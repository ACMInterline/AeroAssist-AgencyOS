from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import (
    AirlineKnowledgeRelease,
    AirlineKnowledgeReleaseCreate,
    AirlineKnowledgeReleaseUpdate,
    AirlineKnowledgeVersion,
    AirlineKnowledgeVersionCreate,
    AirlineKnowledgeVersionUpdate,
    new_id,
)


PHASE_LABEL = "phase_56_2_journey_option_fare_brand_composition_workspace_foundation"
AIRLINE_KNOWLEDGE_VERSION_COLLECTION = "airline_knowledge_versions"
AIRLINE_KNOWLEDGE_RELEASE_COLLECTION = "airline_knowledge_releases"

KNOWLEDGE_LIFECYCLE_STATUSES = [
    "draft",
    "under_review",
    "approved",
    "published",
    "effective",
    "superseded",
    "archived",
    "historical_audit",
]

RELEASE_STATUSES = [
    "draft",
    "under_review",
    "approved",
    "published",
    "effective",
    "superseded",
    "archived",
]

REVIEW_STATUSES = [
    "not_started",
    "under_review",
    "changes_requested",
    "reviewed",
    "rejected",
]

APPROVAL_STATUSES = [
    "not_requested",
    "pending",
    "approved",
    "rejected",
]

KNOWLEDGE_SCOPES = [
    "evidence",
    "policy",
    "pricing",
    "capability",
    "operational_constraints",
    "operational_procedures",
]

CHANGE_TYPES = [
    "new",
    "correction",
    "policy_update",
    "pricing_update",
    "capability_update",
    "constraint_update",
    "procedure_update",
    "supersession",
    "rollback_metadata",
]


class AirlineKnowledgeGovernanceError(ValueError):
    pass


class AirlineKnowledgeGovernanceService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def platform_response(self, **filters: Any) -> dict[str, Any]:
        versions = await self.list_platform_versions(**filters)
        releases = await self.list_platform_releases(**filters)
        return {
            "phase": PHASE_LABEL,
            "versions": versions,
            "releases": releases,
            "summary": self.summarize_counts(versions, releases),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Airline Knowledge Governance stores version and release metadata only. It does not evaluate rules, reason with AI, execute parsers, recommend, calculate pricing, call providers, run workers, or automatically publish.",
            **self.safety_flags(),
        }

    async def agency_response(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        versions = await self.list_agency_versions(agency_id, **filters)
        releases = await self.list_agency_releases(agency_id, **filters)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "versions": versions,
            "releases": releases,
            "summary": self.summarize_counts(versions, releases),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            "notice": "Agency Knowledge Governance is read-only lifecycle metadata. It does not evaluate rules, reason with AI, execute parsers, recommend, calculate pricing, call providers, run workers, or automatically publish.",
            **self.safety_flags(),
        }

    async def platform_summary(self) -> dict[str, Any]:
        versions = await self.list_platform_versions()
        releases = await self.list_platform_releases()
        return {
            "phase": PHASE_LABEL,
            "summary": self.summarize_counts(versions, releases),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        versions = await self.list_agency_versions(agency_id)
        releases = await self.list_agency_releases(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(versions, releases),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def list_platform_versions(
        self,
        *,
        agency_id: str | None = None,
        lifecycle_status: str | None = None,
        review_status: str | None = None,
        approval_status: str | None = None,
        publication_channel: str | None = None,
        publication_scope: str | None = None,
        knowledge_scope: str | None = None,
        change_type: str | None = None,
        include_archived: bool = False,
        **_: Any,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if lifecycle_status:
            filters["lifecycle_status"] = lifecycle_status
        if review_status:
            filters["review_status"] = review_status
        if approval_status:
            filters["approval_status"] = approval_status
        if publication_channel:
            filters["publication_channel"] = publication_channel
        if publication_scope:
            filters["publication_scope"] = publication_scope
        if change_type:
            filters["change_type"] = change_type

        items = await self.db.collection(AIRLINE_KNOWLEDGE_VERSION_COLLECTION).find_many(filters or None)
        if not include_archived:
            items = [item for item in items if not item.get("deleted_at") and item.get("lifecycle_status") != "archived"]
        items = self._filter_list_value(items, "knowledge_scope", knowledge_scope)
        items.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._version_projection(item, read_only=False) for item in items]

    async def list_agency_versions(self, agency_id: str, **filters: Any) -> list[dict[str, Any]]:
        items = await self.list_platform_versions(agency_id=agency_id, **filters)
        return [self._agency_projection(item) for item in items if item.get("agency_id") == agency_id]

    async def list_platform_releases(
        self,
        *,
        agency_id: str | None = None,
        release_status: str | None = None,
        airline_code: str | None = None,
        country: str | None = None,
        service_domain: str | None = None,
        include_archived: bool = False,
        **_: Any,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if release_status:
            filters["release_status"] = release_status

        items = await self.db.collection(AIRLINE_KNOWLEDGE_RELEASE_COLLECTION).find_many(filters or None)
        if not include_archived:
            items = [item for item in items if not item.get("deleted_at") and item.get("release_status") != "archived"]
        items = self._filter_list_value(items, "airline_codes", airline_code)
        items = self._filter_list_value(items, "countries", country)
        items = self._filter_list_value(items, "service_domains", service_domain)
        items.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._release_projection(item, read_only=False) for item in items]

    async def list_agency_releases(self, agency_id: str, **filters: Any) -> list[dict[str, Any]]:
        items = await self.list_platform_releases(agency_id=agency_id, **filters)
        return [self._agency_projection(item) for item in items if item.get("agency_id") == agency_id]

    async def get_platform_version(self, version_id: str) -> dict[str, Any]:
        item = await self._require_version(version_id)
        return await self._version_projection(item, read_only=False)

    async def get_agency_version(self, agency_id: str, version_id: str) -> dict[str, Any]:
        item = await self._require_version(version_id, agency_id=agency_id)
        return self._agency_projection(await self._version_projection(item, read_only=True))

    async def get_platform_release(self, release_id: str) -> dict[str, Any]:
        item = await self._require_release(release_id)
        return await self._release_projection(item, read_only=False)

    async def get_agency_release(self, agency_id: str, release_id: str) -> dict[str, Any]:
        item = await self._require_release(release_id, agency_id=agency_id)
        return self._agency_projection(await self._release_projection(item, read_only=True))

    async def create_version(self, payload: AirlineKnowledgeVersionCreate, user: dict) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        self._validate_version_payload(data)
        data.setdefault("knowledge_version_reference", self._version_reference())
        data.setdefault("lifecycle_status", "draft")
        data.setdefault("review_status", "not_started")
        data.setdefault("approval_status", "not_requested")
        data.setdefault("draft_created_at", self._now())
        data.setdefault("author", user.get("id"))
        data.setdefault("created_by", user.get("id"))
        data["updated_by"] = user.get("id")
        data.update(self.safety_flags())
        record = AirlineKnowledgeVersion(**data)
        created = await self.db.collection(AIRLINE_KNOWLEDGE_VERSION_COLLECTION).insert_one(record.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "airline_knowledge_version": await self._version_projection(created, read_only=False),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def update_version(self, version_id: str, payload: AirlineKnowledgeVersionUpdate, user: dict) -> dict[str, Any]:
        existing = await self._require_version(version_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        self._validate_version_payload(updates, partial=True)
        updates["updated_by"] = user.get("id")
        updates.update(self.safety_flags())
        updated = await self.db.collection(AIRLINE_KNOWLEDGE_VERSION_COLLECTION).update_one({"id": existing["id"]}, updates)
        if not updated:
            raise AirlineKnowledgeGovernanceError("Airline knowledge version metadata could not be updated.")
        return {
            "phase": PHASE_LABEL,
            "airline_knowledge_version": await self._version_projection(updated, read_only=False),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def archive_version(self, version_id: str, user: dict) -> dict[str, Any]:
        existing = await self._require_version(version_id)
        updated = await self.db.collection(AIRLINE_KNOWLEDGE_VERSION_COLLECTION).update_one(
            {"id": existing["id"]},
            {
                "lifecycle_status": "archived",
                "archived_at": self._now(),
                "deleted_at": self._now(),
                "deleted_by": user.get("id"),
                "updated_by": user.get("id"),
                **self.safety_flags(),
            },
        )
        if not updated:
            raise AirlineKnowledgeGovernanceError("Airline knowledge version metadata could not be archived.")
        return {
            "phase": PHASE_LABEL,
            "airline_knowledge_version": await self._version_projection(updated, read_only=False),
            "archived": True,
            "physical_delete_disabled": True,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def create_release(self, payload: AirlineKnowledgeReleaseCreate, user: dict) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        self._validate_release_payload(data)
        data.setdefault("release_reference", self._release_reference())
        data.setdefault("release_status", "draft")
        data.setdefault("release_author", user.get("id"))
        data["updated_by"] = user.get("id")
        data.update(self.safety_flags())
        record = AirlineKnowledgeRelease(**data)
        created = await self.db.collection(AIRLINE_KNOWLEDGE_RELEASE_COLLECTION).insert_one(record.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "airline_knowledge_release": await self._release_projection(created, read_only=False),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def update_release(self, release_id: str, payload: AirlineKnowledgeReleaseUpdate, user: dict) -> dict[str, Any]:
        existing = await self._require_release(release_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        self._validate_release_payload(updates, partial=True)
        updates["updated_by"] = user.get("id")
        updates.update(self.safety_flags())
        updated = await self.db.collection(AIRLINE_KNOWLEDGE_RELEASE_COLLECTION).update_one({"id": existing["id"]}, updates)
        if not updated:
            raise AirlineKnowledgeGovernanceError("Airline knowledge release metadata could not be updated.")
        return {
            "phase": PHASE_LABEL,
            "airline_knowledge_release": await self._release_projection(updated, read_only=False),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def archive_release(self, release_id: str, user: dict) -> dict[str, Any]:
        existing = await self._require_release(release_id)
        updated = await self.db.collection(AIRLINE_KNOWLEDGE_RELEASE_COLLECTION).update_one(
            {"id": existing["id"]},
            {
                "release_status": "archived",
                "deleted_at": self._now(),
                "deleted_by": user.get("id"),
                "updated_by": user.get("id"),
                **self.safety_flags(),
            },
        )
        if not updated:
            raise AirlineKnowledgeGovernanceError("Airline knowledge release metadata could not be archived.")
        return {
            "phase": PHASE_LABEL,
            "airline_knowledge_release": await self._release_projection(updated, read_only=False),
            "archived": True,
            "physical_delete_disabled": True,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    def summarize_counts(self, versions: list[dict[str, Any]], releases: list[dict[str, Any]]) -> dict[str, Any]:
        by_lifecycle_status = {status: 0 for status in KNOWLEDGE_LIFECYCLE_STATUSES}
        by_review_status = {status: 0 for status in REVIEW_STATUSES}
        by_approval_status = {status: 0 for status in APPROVAL_STATUSES}
        by_release_status = {status: 0 for status in RELEASE_STATUSES}
        by_knowledge_scope = {scope: 0 for scope in KNOWLEDGE_SCOPES}
        by_change_type = {change_type: 0 for change_type in CHANGE_TYPES}
        for item in versions:
            self._count_value(by_lifecycle_status, item.get("lifecycle_status"))
            self._count_value(by_review_status, item.get("review_status"))
            self._count_value(by_approval_status, item.get("approval_status"))
            self._count_value(by_change_type, item.get("change_type"))
            for scope in item.get("knowledge_scope") or []:
                self._count_value(by_knowledge_scope, scope)
        for release in releases:
            self._count_value(by_release_status, release.get("release_status"))
        return {
            "version_count": len(versions),
            "release_count": len(releases),
            "by_lifecycle_status": by_lifecycle_status,
            "by_review_status": by_review_status,
            "by_approval_status": by_approval_status,
            "by_release_status": by_release_status,
            "by_knowledge_scope": by_knowledge_scope,
            "by_change_type": by_change_type,
            "review_queue_count": len([item for item in versions if item.get("lifecycle_status") == "under_review" or item.get("review_status") == "under_review"]),
            "approval_queue_count": len([item for item in versions if item.get("approval_status") == "pending"]),
            "publication_queue_count": len([item for item in versions if item.get("lifecycle_status") == "approved"]),
            "published_count": len([item for item in versions if item.get("lifecycle_status") == "published"]),
            "effective_count": len([item for item in versions if item.get("lifecycle_status") == "effective"]),
            "superseded_count": len([item for item in versions if item.get("lifecycle_status") == "superseded" or item.get("supersedes_version_ids")]),
            "archived_count": len([item for item in versions if item.get("lifecycle_status") == "archived"]),
            "historical_version_count": len([item for item in versions if item.get("lifecycle_status") == "historical_audit" or item.get("historical_lookup_tags")]),
            "version_comparison_count": len([item for item in versions if self._has_comparison_metadata(item)]),
            "rollback_metadata_count": len([item for item in versions if item.get("rollback_to_version_id") or item.get("rollback_from_version_id")]),
            "release_evaluation_ready_count": len([item for item in releases if item.get("evaluation_ready")]),
            "release_recommendation_ready_count": len([item for item in releases if item.get("recommendation_ready")]),
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "agency_id": "agency_id exact metadata match",
            "lifecycle_status": KNOWLEDGE_LIFECYCLE_STATUSES,
            "release_status": RELEASE_STATUSES,
            "review_status": REVIEW_STATUSES,
            "approval_status": APPROVAL_STATUSES,
            "publication_channel": "publication_channel exact metadata match",
            "publication_scope": "publication_scope exact metadata match",
            "knowledge_scope": KNOWLEDGE_SCOPES,
            "change_type": CHANGE_TYPES,
            "airline_code": "release airline_codes membership metadata match",
            "country": "release countries membership metadata match",
            "service_domain": "release service_domains membership metadata match",
            "metadata_only": True,
        }

    async def _version_projection(self, item: dict[str, Any], *, read_only: bool) -> dict[str, Any]:
        projected = dict(item)
        projected["version_display_name"] = self._version_display_name(projected)
        projected["governed_knowledge_summary"] = self._knowledge_summary(projected)
        projected["version_comparison"] = self._version_comparison(projected)
        projected["lifecycle_timeline"] = self._lifecycle_timeline(projected)
        projected["agency"] = await self._agency_context(projected.get("agency_id"))
        projected["agency_name"] = projected["agency"].get("agency_name")
        projected["read_only"] = read_only
        projected.update(self.safety_flags())
        return projected

    async def _release_projection(self, item: dict[str, Any], *, read_only: bool) -> dict[str, Any]:
        projected = dict(item)
        projected["release_display_name"] = projected.get("release_name") or projected.get("release_reference") or projected.get("id")
        projected["included_version_count"] = len(projected.get("included_version_ids") or [])
        projected["agency"] = await self._agency_context(projected.get("agency_id"))
        projected["agency_name"] = projected["agency"].get("agency_name")
        projected["read_only"] = read_only
        projected.update(self.safety_flags())
        return projected

    def _agency_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        projected["read_only"] = True
        projected.update(self.safety_flags())
        return projected

    async def _require_version(self, version_id: str, *, agency_id: str | None = None) -> dict[str, Any]:
        item = await self._find_by_id_or_reference(
            AIRLINE_KNOWLEDGE_VERSION_COLLECTION,
            version_id,
            "knowledge_version_reference",
            agency_id=agency_id,
        )
        if not item:
            raise AirlineKnowledgeGovernanceError("Airline knowledge version metadata was not found.")
        return item

    async def _require_release(self, release_id: str, *, agency_id: str | None = None) -> dict[str, Any]:
        item = await self._find_by_id_or_reference(
            AIRLINE_KNOWLEDGE_RELEASE_COLLECTION,
            release_id,
            "release_reference",
            agency_id=agency_id,
        )
        if not item:
            raise AirlineKnowledgeGovernanceError("Airline knowledge release metadata was not found.")
        return item

    async def _find_by_id_or_reference(self, collection: str, value: str, reference_field: str, *, agency_id: str | None = None) -> dict[str, Any] | None:
        filters = {"id": value}
        if agency_id:
            filters["agency_id"] = agency_id
        item = await self.db.collection(collection).find_one(filters)
        if item:
            return item
        filters = {reference_field: value}
        if agency_id:
            filters["agency_id"] = agency_id
        return await self.db.collection(collection).find_one(filters)

    async def _agency_context(self, agency_id: str | None) -> dict[str, Any]:
        if not agency_id:
            return {"agency_id": None, "agency_name": None, "agency_slug": None, "metadata_only": True}
        agency = await self.db.collection("agencies").find_one({"id": agency_id})
        if not agency:
            return {"agency_id": agency_id, "agency_name": agency_id, "agency_slug": None, "metadata_only": True}
        return {
            "agency_id": agency.get("id"),
            "agency_name": agency.get("name"),
            "agency_slug": agency.get("slug"),
            "metadata_only": True,
        }

    def _validate_version_payload(self, data: dict[str, Any], *, partial: bool = False) -> None:
        if data.get("lifecycle_status") and data["lifecycle_status"] not in KNOWLEDGE_LIFECYCLE_STATUSES:
            raise AirlineKnowledgeGovernanceError("Lifecycle status must be a known governance status.")
        if data.get("review_status") and data["review_status"] not in REVIEW_STATUSES:
            raise AirlineKnowledgeGovernanceError("Review status must be a known governance status.")
        if data.get("approval_status") and data["approval_status"] not in APPROVAL_STATUSES:
            raise AirlineKnowledgeGovernanceError("Approval status must be a known governance status.")
        if data.get("change_type") and data["change_type"] not in CHANGE_TYPES:
            raise AirlineKnowledgeGovernanceError("Change type must be a known governance metadata type.")
        unknown_scopes = set(data.get("knowledge_scope") or []) - set(KNOWLEDGE_SCOPES)
        if unknown_scopes:
            raise AirlineKnowledgeGovernanceError(f"Unknown knowledge scope metadata: {sorted(unknown_scopes)}.")
        if not partial and not (data.get("version_label") or data.get("semantic_version") or data.get("knowledge_version_reference")):
            raise AirlineKnowledgeGovernanceError("Version label, semantic version, or reference is required for governance metadata.")

    def _validate_release_payload(self, data: dict[str, Any], *, partial: bool = False) -> None:
        if data.get("release_status") and data["release_status"] not in RELEASE_STATUSES:
            raise AirlineKnowledgeGovernanceError("Release status must be a known governance status.")
        if not partial and not (data.get("release_name") or data.get("release_reference")):
            raise AirlineKnowledgeGovernanceError("Release name or reference is required for release metadata.")

    def _version_comparison(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "version_a": item.get("comparison_base_version_id") or item.get("previous_version_id"),
            "version_b": item.get("comparison_target_version_id") or item.get("id"),
            "added": item.get("added_objects") or [],
            "modified": item.get("modified_objects") or [],
            "removed": item.get("removed_objects") or [],
            "changed_effective_dates": item.get("changed_effective_dates") or [],
            "changed_pricing": item.get("changed_pricing") or [],
            "changed_capability": item.get("changed_capability") or [],
            "changed_operational_constraints": item.get("changed_operational_constraints") or [],
            "changed_procedures": item.get("changed_procedures") or [],
            "metadata_only": True,
        }

    def _lifecycle_timeline(self, item: dict[str, Any]) -> list[dict[str, Any]]:
        fields = [
            ("draft", "draft_created_at"),
            ("review", "submitted_for_review_at"),
            ("reviewed", "reviewed_at"),
            ("approved", "approved_at"),
            ("published", "published_at"),
            ("effective_from", "effective_from"),
            ("effective_until", "effective_until"),
            ("superseded", "superseded_at"),
            ("archived", "archived_at"),
        ]
        return [
            {"stage": stage, "timestamp": item.get(field), "metadata_only": True}
            for stage, field in fields
            if item.get(field)
        ]

    def _knowledge_summary(self, item: dict[str, Any]) -> dict[str, int]:
        return {
            "evidence": len(item.get("evidence_ids") or []),
            "policy": len(item.get("policy_ids") or []),
            "pricing": len(item.get("pricing_ids") or []),
            "capability": len(item.get("capability_ids") or []),
            "operational_constraints": len(item.get("constraint_ids") or []),
            "operational_procedures": len(item.get("procedure_ids") or []),
        }

    def _has_comparison_metadata(self, item: dict[str, Any]) -> bool:
        comparison_fields = [
            "comparison_base_version_id",
            "comparison_target_version_id",
            "added_objects",
            "modified_objects",
            "removed_objects",
            "changed_effective_dates",
            "changed_pricing",
            "changed_capability",
            "changed_operational_constraints",
            "changed_procedures",
        ]
        return any(bool(item.get(field)) for field in comparison_fields)

    def _filter_list_value(self, items: list[dict[str, Any]], field: str, value: str | None) -> list[dict[str, Any]]:
        if not value:
            return items
        normalized = value.lower()
        return [
            item
            for item in items
            if normalized in {str(candidate).lower() for candidate in (item.get(field) or [])}
        ]

    def _version_display_name(self, item: dict[str, Any]) -> str:
        if item.get("version_label"):
            return str(item["version_label"])
        if item.get("semantic_version"):
            return str(item["semantic_version"])
        if item.get("knowledge_version_reference"):
            return str(item["knowledge_version_reference"])
        return item.get("id") or "Airline knowledge version"

    def _version_reference(self) -> str:
        return f"AKV-{new_id()[:8].upper()}"

    def _release_reference(self) -> str:
        return f"AKR-{new_id()[:8].upper()}"

    def _count_value(self, target: dict[str, int], value: Any) -> None:
        if value:
            target[str(value)] = target.get(str(value), 0) + 1

    def _sort_text(self, value: Any) -> str:
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value or "")

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "governance_foundation": True,
            "version_control_foundation": True,
            "live_rule_evaluation_disabled": True,
            "ai_reasoning_disabled": True,
            "parser_execution_disabled": True,
            "recommendation_engine_disabled": True,
            "pricing_calculation_disabled": True,
            "provider_integrations_disabled": True,
            "background_workers_disabled": True,
            "automatic_publication_disabled": True,
        }
