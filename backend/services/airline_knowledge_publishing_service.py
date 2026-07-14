from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import AirlineKnowledgePublication, AirlineKnowledgePublicationCreate, AirlineKnowledgePublicationUpdate


PHASE_LABEL = "phase_54_8_operations_command_center_foundation"
AIRLINE_KNOWLEDGE_PUBLICATIONS_COLLECTION = "airline_knowledge_publications"

PUBLICATION_STATUSES = [
    "draft",
    "qa_approved",
    "approved",
    "scheduled",
    "published",
    "superseded",
    "rolled_back",
    "archived",
]
RELEASE_CHANNELS = [
    "internal_review",
    "scenario_testing",
    "agency_preview",
    "agency_reference",
    "production_reference",
]
VISIBILITY_STATUSES = ["platform_only", "selected_agencies", "all_agencies", "hidden", "suspended"]


class AirlineKnowledgePublishingError(ValueError):
    pass


class AirlineKnowledgePublishingService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def platform_response(self, **filters: Any) -> dict[str, Any]:
        publications = await self.list_publications(**filters)
        return {
            "phase": PHASE_LABEL,
            "items": publications,
            "publications": publications,
            "summary": await self.summarize_counts(filters.get("agency_id")),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Airline Knowledge Publishing stores controlled publication metadata only. It does not publish automatically or execute recommendations.",
            **self.safety_flags(),
        }

    async def agency_response(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        publications = await self.list_publications(agency_id=agency_id, **filters)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": publications,
            "publications": publications,
            "summary": await self.summarize_counts(agency_id),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Agency Published Knowledge shows visibility and readiness metadata. Human authority remains final.",
            **self.safety_flags(),
        }

    async def platform_summary(self, agency_id: str | None = None) -> dict[str, Any]:
        return {
            "phase": PHASE_LABEL,
            "summary": await self.summarize_counts(agency_id),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": await self.summarize_counts(agency_id),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def list_publications(
        self,
        *,
        agency_id: str | None = None,
        airline_code: str | None = None,
        service_family: str | None = None,
        publication_status: str | None = None,
        release_channel: str | None = None,
        agency_visibility: str | None = None,
        AOIE_ready: bool | None = None,
        search: str | None = None,
        include_archived: bool = False,
        **_: Any,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if publication_status:
            filters["publication_status"] = self._normalize_code(publication_status)
        if release_channel:
            filters["release_channel"] = self._normalize_code(release_channel)
        if AOIE_ready is not None:
            filters["AOIE_ready"] = AOIE_ready

        items = await self.db.collection(AIRLINE_KNOWLEDGE_PUBLICATIONS_COLLECTION).find_many(filters or None)
        if airline_code:
            normalized_airline = self._normalize_airline(airline_code)
            items = [item for item in items if normalized_airline in (item.get("airline_codes") or [])]
        if service_family:
            normalized_family = self._normalize_code(service_family)
            items = [item for item in items if normalized_family in (item.get("service_families") or [])]
        if agency_visibility:
            normalized_visibility = self._normalize_code(agency_visibility)
            items = [
                item
                for item in items
                if self._visibility_status(item.get("agency_visibility")) == normalized_visibility
            ]
        if not include_archived:
            items = [item for item in items if not item.get("archived") and item.get("publication_status") != "archived"]
        items = [
            item
            for item in items
            if self._any_field_matches(
                item,
                [
                    "publication_reference",
                    "publication_name",
                    "airline_codes",
                    "service_families",
                    "included_knowledge_version_ids",
                    "included_policy_cards",
                    "included_pricing_formulas",
                    "included_rules",
                    "qa_review_ids",
                    "publication_status",
                    "release_channel",
                    "rollback_plan",
                    "consumer_readiness",
                    "agency_visibility",
                    "metadata",
                ],
                search,
            )
        ]
        items.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._publication_projection(item) for item in items]

    async def get_publication(self, publication_id: str, agency_id: str | None = None) -> dict[str, Any]:
        item = await self._require_publication(publication_id, agency_id=agency_id)
        return await self._publication_projection(item)

    async def create_publication(
        self,
        payload: AirlineKnowledgePublicationCreate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        if agency_id:
            data["agency_id"] = agency_id
        data = self._normalize_payload(data)
        data.setdefault("publication_reference", self._reference("AKP"))
        data.setdefault("publication_status", "draft")
        data.setdefault("release_channel", "internal_review")
        data.setdefault("AOIE_ready", False)
        data.update(self.safety_flags())
        self._validate_payload(data)
        record = AirlineKnowledgePublication(**data)
        created = await self.db.collection(AIRLINE_KNOWLEDGE_PUBLICATIONS_COLLECTION).insert_one(record.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "airline_knowledge_publication": await self._publication_projection(created),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def update_publication(
        self,
        publication_id: str,
        payload: AirlineKnowledgePublicationUpdate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_publication(publication_id, agency_id=agency_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        if agency_id:
            updates.pop("agency_id", None)
        updates = self._normalize_payload(updates)
        updates.update(self.safety_flags())
        self._validate_payload(updates, partial=True)
        filters = {"id": existing["id"]}
        if agency_id:
            filters["agency_id"] = agency_id
        updated = await self.db.collection(AIRLINE_KNOWLEDGE_PUBLICATIONS_COLLECTION).update_one(filters, updates)
        if not updated:
            raise AirlineKnowledgePublishingError("Airline knowledge publication metadata could not be updated.")
        return {
            "phase": PHASE_LABEL,
            "airline_knowledge_publication": await self._publication_projection(updated),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def archive_publication(self, publication_id: str, user: dict, agency_id: str | None = None) -> dict[str, Any]:
        existing = await self._require_publication(publication_id, agency_id=agency_id)
        updates = {
            "publication_status": "archived",
            "archived": True,
            "archived_at": self._now(),
            **self.safety_flags(),
        }
        filters = {"id": existing["id"]}
        if agency_id:
            filters["agency_id"] = agency_id
        updated = await self.db.collection(AIRLINE_KNOWLEDGE_PUBLICATIONS_COLLECTION).update_one(filters, updates)
        if not updated:
            raise AirlineKnowledgePublishingError("Airline knowledge publication metadata could not be archived.")
        return {
            "phase": PHASE_LABEL,
            "airline_knowledge_publication": await self._publication_projection(updated),
            "archived": True,
            "physical_delete_disabled": True,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def summarize_counts(self, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"agency_id": agency_id} if agency_id else None
        publications = await self.db.collection(AIRLINE_KNOWLEDGE_PUBLICATIONS_COLLECTION).find_many(filters)
        active_publications = [
            item for item in publications if not item.get("archived") and item.get("publication_status") != "archived"
        ]
        knowledge_version_count = sum(len(item.get("included_knowledge_version_ids") or []) for item in publications)
        policy_card_count = sum(len(item.get("included_policy_cards") or []) for item in publications)
        pricing_formula_count = sum(len(item.get("included_pricing_formulas") or []) for item in publications)
        rule_count = sum(len(item.get("included_rules") or []) for item in publications)
        qa_review_count = sum(len(item.get("qa_review_ids") or []) for item in publications)
        return {
            "airline_knowledge_publication_count": len(publications),
            "active_publication_count": len(active_publications),
            "aoie_ready_count": len([item for item in publications if item.get("AOIE_ready") is True]),
            "knowledge_version_count": knowledge_version_count,
            "policy_card_count": policy_card_count,
            "pricing_formula_count": pricing_formula_count,
            "rule_count": rule_count,
            "qa_review_count": qa_review_count,
            "superseded_publication_link_count": sum(len(item.get("supersedes_publication_ids") or []) for item in publications),
            "by_publication_status": self._counts(publications, "publication_status", PUBLICATION_STATUSES),
            "by_release_channel": self._counts(publications, "release_channel", RELEASE_CHANNELS),
            "by_visibility_status": {
                status: len(
                    [
                        item
                        for item in publications
                        if self._visibility_status(item.get("agency_visibility")) == status
                    ]
                )
                for status in VISIBILITY_STATUSES
            },
            "supported_publication_status_count": len(PUBLICATION_STATUSES),
            "supported_release_channel_count": len(RELEASE_CHANNELS),
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "publication_status": PUBLICATION_STATUSES,
            "release_channel": RELEASE_CHANNELS,
            "agency_visibility": VISIBILITY_STATUSES,
            "airline_code": "IATA or internal airline code",
            "service_family": "service family code",
            "AOIE_ready": "true or false",
            "search": "reference, name, airlines, services, included artifacts, QA reviews, readiness, visibility, rollback, or metadata",
            "metadata_only": True,
        }

    async def _publication_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        projected["publication_display_name"] = " / ".join(
            part
            for part in [
                projected.get("publication_reference"),
                projected.get("publication_name"),
                projected.get("publication_status"),
                projected.get("release_channel"),
            ]
            if part
        )
        projected["overview_section"] = {
            "publication_reference": projected.get("publication_reference"),
            "publication_name": projected.get("publication_name"),
            "publication_status": projected.get("publication_status"),
            "release_channel": projected.get("release_channel"),
            "airline_codes": projected.get("airline_codes") or [],
            "service_families": projected.get("service_families") or [],
            "effective_from": projected.get("effective_from"),
            "effective_until": projected.get("effective_until"),
        }
        projected["included_knowledge_section"] = {
            "included_knowledge_version_ids": projected.get("included_knowledge_version_ids") or [],
            "included_policy_cards": projected.get("included_policy_cards") or [],
            "included_pricing_formulas": projected.get("included_pricing_formulas") or [],
            "included_rules": projected.get("included_rules") or [],
            "qa_review_ids": projected.get("qa_review_ids") or [],
        }
        projected["readiness_section"] = {
            "consumer_readiness": projected.get("consumer_readiness") or {},
            "AOIE_ready": projected.get("AOIE_ready") is True,
            "agency_visibility": projected.get("agency_visibility") or {},
            "human_authority_final": True,
        }
        projected["release_control_section"] = {
            "approved_at": projected.get("approved_at"),
            "published_at": projected.get("published_at"),
            "automatic_publication_disabled": True,
            "recommendation_execution_disabled": True,
        }
        projected["supersession_section"] = {
            "supersedes_publication_ids": projected.get("supersedes_publication_ids") or [],
            "rollback_plan": projected.get("rollback_plan") or {},
        }
        projected["lifecycle_section"] = {
            "created_at": projected.get("created_at"),
            "updated_at": projected.get("updated_at"),
            "archived": projected.get("archived"),
            "archived_at": projected.get("archived_at"),
        }
        projected["boundary_section"] = self.safety_flags()
        projected.update(self.safety_flags())
        return projected

    async def _require_publication(self, publication_id: str, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": publication_id}
        if agency_id:
            filters["agency_id"] = agency_id
        item = await self.db.collection(AIRLINE_KNOWLEDGE_PUBLICATIONS_COLLECTION).find_one(filters)
        if not item:
            raise AirlineKnowledgePublishingError("Airline knowledge publication metadata not found.")
        return item

    def _normalize_payload(self, data: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(data)
        for field in ["publication_status", "release_channel"]:
            if field in normalized and normalized[field] is not None:
                normalized[field] = self._normalize_code(normalized[field])
        if "airline_codes" in normalized and normalized["airline_codes"] is not None:
            normalized["airline_codes"] = [self._normalize_airline(value) for value in normalized.get("airline_codes") or []]
        if "service_families" in normalized and normalized["service_families"] is not None:
            normalized["service_families"] = [self._normalize_code(value) for value in normalized.get("service_families") or []]
        if "agency_visibility" in normalized and isinstance(normalized.get("agency_visibility"), dict):
            visibility = dict(normalized["agency_visibility"])
            if visibility.get("visibility_status") is not None:
                visibility["visibility_status"] = self._normalize_code(visibility.get("visibility_status"))
            normalized["agency_visibility"] = visibility
        return normalized

    def _validate_payload(self, data: dict[str, Any], *, partial: bool = False) -> None:
        self._validate_choice(data, "publication_status", PUBLICATION_STATUSES)
        self._validate_choice(data, "release_channel", RELEASE_CHANNELS)
        if "agency_visibility" in data:
            visibility_status = self._visibility_status(data.get("agency_visibility"))
            if visibility_status and visibility_status not in VISIBILITY_STATUSES:
                raise AirlineKnowledgePublishingError(f"Unsupported agency_visibility metadata value: {visibility_status}.")
        self._reject_forbidden_metadata(data)
        if not partial:
            for field in ["publication_name"]:
                if not data.get(field):
                    raise AirlineKnowledgePublishingError(f"{field} is required.")

    def _validate_choice(self, data: dict[str, Any], field: str, allowed: list[str]) -> None:
        if field not in data or data.get(field) is None:
            return
        if data[field] not in allowed:
            raise AirlineKnowledgePublishingError(f"Unsupported {field} metadata value: {data[field]}.")

    def _reject_forbidden_metadata(self, data: dict[str, Any]) -> None:
        forbidden = [
            "auto_" + "publish",
            "publish_" + "now",
            "automatic_" + "publish",
            "automatic_publication_" + "enabled",
            "execute_" + "recommendation",
            "recommendation_execution_" + "enabled",
            "booking_provider",
            "ticketing_provider",
            "emd_issuance_provider",
            "ai_prompt",
            "llm_prompt",
            "chatcompletion",
            "provider_client",
            "background_task",
            "backgroundtasks",
        ]
        serialized = str(data).lower()
        for marker in forbidden:
            if marker in serialized:
                raise AirlineKnowledgePublishingError(f"Forbidden non-metadata implementation marker present: {marker}.")

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "airline_knowledge_publishing_foundation": True,
            "automatic_publication_disabled": True,
            "recommendation_execution_disabled": True,
            "auto_approval_disabled": True,
            "provider_integrations_disabled": True,
            "ai_disabled": True,
            "background_workers_disabled": True,
            "human_authority_final": True,
        }

    def _visibility_status(self, value: Any) -> str:
        if isinstance(value, dict):
            return self._normalize_code(value.get("visibility_status") or value.get("status") or "")
        return self._normalize_code(value)

    def _normalize_code(self, value: Any) -> str:
        return str(value or "").strip().lower().replace(" ", "_").replace("/", "_").replace("-", "_")

    def _normalize_airline(self, value: Any) -> str:
        return str(value or "").strip().upper()

    def _reference(self, prefix: str) -> str:
        return f"{prefix}-{self._now().replace(':', '').replace('-', '').replace('.', '')}"

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _sort_text(self, value: Any) -> str:
        return str(value or "")

    def _counts(self, items: list[dict[str, Any]], field: str, values: list[str]) -> dict[str, int]:
        return {value: len([item for item in items if item.get(field) == value]) for value in values}

    def _any_field_matches(self, item: dict[str, Any], fields: list[str], expected: Any) -> bool:
        if expected in (None, ""):
            return True
        expected_text = str(expected).lower()
        for field in fields:
            value = item.get(field)
            if isinstance(value, list):
                if any(expected_text in str(entry).lower() for entry in value):
                    return True
            elif isinstance(value, dict):
                if expected_text in str(value).lower():
                    return True
            elif value is not None and expected_text in str(value).lower():
                return True
        return False
