from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import AirlineKnowledgeNormalisation, AirlineKnowledgeNormalisationCreate, AirlineKnowledgeNormalisationUpdate, new_id


PHASE_LABEL = "phase_50_5_airline_operational_capability_matrix_foundation"
AIRLINE_KNOWLEDGE_NORMALISATION_COLLECTION = "airline_knowledge_normalisations"

NORMALISATION_STATUSES = [
    "draft",
    "captured",
    "in_review",
    "approved",
    "rejected",
    "superseded",
    "archived",
]

NORMALISATION_TYPES = [
    "animal_taxonomy",
    "aircraft_taxonomy",
    "cabin_taxonomy",
    "service_taxonomy",
    "unit_normalisation",
    "terminology_alias",
    "ssr_mapping",
    "rfic_rfisc_mapping",
    "commercial_term_mapping",
    "operational_term_mapping",
]

REVIEW_STATUSES = [
    "not_started",
    "in_review",
    "needs_clarification",
    "reviewed",
    "rejected",
]

APPROVAL_STATUSES = [
    "not_requested",
    "pending",
    "approved",
    "rejected",
]


class AirlineKnowledgeNormalisationError(ValueError):
    pass


class AirlineKnowledgeNormalisationService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_platform_normalisations(
        self,
        *,
        agency_id: str | None = None,
        normalisation_status: str | None = None,
        normalisation_type: str | None = None,
        canonical_code: str | None = None,
        taxonomy_domain: str | None = None,
        taxonomy_family: str | None = None,
        taxonomy_variant: str | None = None,
        airline: str | None = None,
        ssr_code: str | None = None,
        rfic: str | None = None,
        rfisc: str | None = None,
        review_status: str | None = None,
        approval_status: str | None = None,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if normalisation_status:
            filters["normalisation_status"] = normalisation_status
        if normalisation_type:
            filters["normalisation_type"] = normalisation_type
        if canonical_code:
            filters["canonical_code"] = canonical_code
        if taxonomy_domain:
            filters["taxonomy_domain"] = taxonomy_domain
        if taxonomy_family:
            filters["taxonomy_family"] = taxonomy_family
        if taxonomy_variant:
            filters["taxonomy_variant"] = taxonomy_variant
        if review_status:
            filters["review_status"] = review_status
        if approval_status:
            filters["approval_status"] = approval_status

        items = await self.db.collection(AIRLINE_KNOWLEDGE_NORMALISATION_COLLECTION).find_many(filters or None)
        if not include_archived:
            items = [
                item
                for item in items
                if not item.get("deleted_at") and item.get("normalisation_status") != "archived"
            ]
        items = self._filter_list_value(items, "airline_codes", airline)
        items = self._filter_list_value(items, "ssr_codes", ssr_code)
        items = self._filter_list_value(items, "rfic_codes", rfic)
        items = self._filter_list_value(items, "rfisc_codes", rfisc)
        items.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._platform_projection(item) for item in items]

    async def list_agency_normalisations(self, agency_id: str, **filters: Any) -> list[dict[str, Any]]:
        items = await self.list_platform_normalisations(agency_id=agency_id, **filters)
        return [self._agency_projection(item) for item in items if item.get("agency_id") == agency_id]

    async def platform_response(self, **filters: Any) -> dict[str, Any]:
        items = await self.list_platform_normalisations(**filters)
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "airline_knowledge_normalisation_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Airline Knowledge Normalisation stores canonical operational vocabulary metadata only. It does not evaluate rules, parse with AI, recommend, score feasibility, calculate pricing, scrape, run workers, or call providers.",
            **self.safety_flags(),
        }

    async def agency_response(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        items = await self.list_agency_normalisations(agency_id, **filters)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "airline_knowledge_normalisation_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            "notice": "Agency Knowledge Normalisation is read-only canonical vocabulary metadata. It does not evaluate rules, parse with AI, recommend, score feasibility, calculate pricing, scrape, run workers, or call providers.",
            **self.safety_flags(),
        }

    async def platform_summary(self) -> dict[str, Any]:
        items = await self.list_platform_normalisations()
        return {
            "phase": PHASE_LABEL,
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        items = await self.list_agency_normalisations(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def get_platform_normalisation(self, normalisation_id: str) -> dict[str, Any]:
        item = await self._require_normalisation(normalisation_id)
        return await self._platform_projection(item)

    async def get_agency_normalisation(self, agency_id: str, normalisation_id: str) -> dict[str, Any]:
        item = await self._require_normalisation(normalisation_id, agency_id=agency_id)
        return self._agency_projection(await self._platform_projection(item))

    async def create_normalisation(self, payload: AirlineKnowledgeNormalisationCreate, user: dict) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        self._validate_payload(data)
        data.setdefault("normalisation_reference", self._normalisation_reference())
        data.setdefault("normalisation_status", "draft")
        data.setdefault("review_status", "not_started")
        data.setdefault("approval_status", "not_requested")
        data.setdefault("created_by", user.get("id"))
        data["updated_by"] = user.get("id")
        data.update(self.safety_flags())
        normalisation = AirlineKnowledgeNormalisation(**data)
        created = await self.db.collection(AIRLINE_KNOWLEDGE_NORMALISATION_COLLECTION).insert_one(normalisation.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "airline_knowledge_normalisation": await self._platform_projection(created),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def update_normalisation(self, normalisation_id: str, payload: AirlineKnowledgeNormalisationUpdate, user: dict) -> dict[str, Any]:
        existing = await self._require_normalisation(normalisation_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        self._validate_payload(updates, partial=True)
        updates["updated_by"] = user.get("id")
        updates.update(self.safety_flags())
        updated = await self.db.collection(AIRLINE_KNOWLEDGE_NORMALISATION_COLLECTION).update_one({"id": existing["id"]}, updates)
        if not updated:
            raise AirlineKnowledgeNormalisationError("Airline knowledge normalisation metadata could not be updated.")
        return {
            "phase": PHASE_LABEL,
            "airline_knowledge_normalisation": await self._platform_projection(updated),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def delete_normalisation(self, normalisation_id: str, user: dict) -> dict[str, Any]:
        existing = await self._require_normalisation(normalisation_id)
        updated = await self.db.collection(AIRLINE_KNOWLEDGE_NORMALISATION_COLLECTION).update_one(
            {"id": existing["id"]},
            {
                "normalisation_status": "archived",
                "deleted_at": self._now(),
                "deleted_by": user.get("id"),
                "updated_by": user.get("id"),
                **self.safety_flags(),
            },
        )
        if not updated:
            raise AirlineKnowledgeNormalisationError("Airline knowledge normalisation metadata could not be archived.")
        return {
            "phase": PHASE_LABEL,
            "airline_knowledge_normalisation": await self._platform_projection(updated),
            "archived": True,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        by_status = {status: 0 for status in NORMALISATION_STATUSES}
        by_type = {item_type: 0 for item_type in NORMALISATION_TYPES}
        by_review_status = {status: 0 for status in REVIEW_STATUSES}
        by_approval_status = {status: 0 for status in APPROVAL_STATUSES}
        by_taxonomy_domain: dict[str, int] = {}
        by_airline: dict[str, int] = {}
        hierarchy_count = 0
        alias_count = 0
        applicability_count = 0
        animal_taxonomy_count = 0
        aircraft_cabin_taxonomy_count = 0
        service_taxonomy_count = 0
        unit_normalisation_count = 0
        knowledge_link_count = 0
        for item in items:
            self._count_value(by_status, item.get("normalisation_status"))
            self._count_value(by_type, item.get("normalisation_type"))
            self._count_value(by_review_status, item.get("review_status"))
            self._count_value(by_approval_status, item.get("approval_status"))
            self._count_value(by_taxonomy_domain, item.get("taxonomy_domain"))
            for airline in item.get("airline_codes") or []:
                self._count_value(by_airline, airline)
            hierarchy_count += 1 if item.get("hierarchy_path") or item.get("parent_canonical_id") else 0
            alias_count += sum(self._list_count(item.get(field)) for field in ["aliases", "abbreviations", "airline_specific_terms", "gds_terms", "commercial_terms", "operational_terms"])
            applicability_count += sum(self._list_count(item.get(field)) for field in ["airline_codes", "country_codes", "airport_codes", "aircraft_types", "cabin_codes", "service_codes", "ssr_codes", "rfic_codes", "rfisc_codes"])
            animal_taxonomy_count += 1 if item.get("species") or item.get("breed") or item.get("animal_notes") else 0
            aircraft_cabin_taxonomy_count += 1 if item.get("aircraft_family") or item.get("cabin_family") or item.get("cabin_name") else 0
            service_taxonomy_count += 1 if item.get("service_domain") or item.get("service_family") or item.get("related_ssr_code") else 0
            unit_normalisation_count += 1 if item.get("unit_type") or item.get("canonical_unit") else 0
            knowledge_link_count += sum(self._list_count(item.get(field)) for field in ["acquisition_ids", "constraint_ids", "evidence_reference_ids", "policy_reference_ids", "pricing_reference_ids", "capability_reference_ids"])
        return {
            "total_count": len(items),
            "by_normalisation_status": by_status,
            "by_normalisation_type": by_type,
            "by_review_status": by_review_status,
            "by_approval_status": by_approval_status,
            "by_taxonomy_domain": by_taxonomy_domain,
            "by_airline": by_airline,
            "hierarchy_count": hierarchy_count,
            "alias_count": alias_count,
            "applicability_count": applicability_count,
            "animal_taxonomy_count": animal_taxonomy_count,
            "aircraft_cabin_taxonomy_count": aircraft_cabin_taxonomy_count,
            "service_taxonomy_count": service_taxonomy_count,
            "unit_normalisation_count": unit_normalisation_count,
            "knowledge_link_count": knowledge_link_count,
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "agency_id": "agency_id exact metadata match",
            "normalisation_status": NORMALISATION_STATUSES,
            "normalisation_type": NORMALISATION_TYPES,
            "canonical_code": "canonical_code exact metadata match",
            "taxonomy_domain": "taxonomy_domain exact metadata match",
            "taxonomy_family": "taxonomy_family exact metadata match",
            "taxonomy_variant": "taxonomy_variant exact metadata match",
            "airline": "airline_codes membership metadata match",
            "ssr_code": "ssr_codes membership metadata match",
            "rfic": "rfic_codes membership metadata match",
            "rfisc": "rfisc_codes membership metadata match",
            "review_status": REVIEW_STATUSES,
            "approval_status": APPROVAL_STATUSES,
            "metadata_only": True,
        }

    async def _platform_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        projected["normalisation_display_name"] = self._display_name(projected)
        agency = await self._agency_context(projected.get("agency_id"))
        projected["agency"] = agency
        projected["agency_name"] = agency.get("agency_name")
        projected["read_only"] = False
        projected.update(self.safety_flags())
        return projected

    def _agency_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        projected["read_only"] = True
        projected.update(self.safety_flags())
        return projected

    async def _require_normalisation(self, normalisation_id: str, *, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": normalisation_id}
        if agency_id:
            filters["agency_id"] = agency_id
        item = await self.db.collection(AIRLINE_KNOWLEDGE_NORMALISATION_COLLECTION).find_one(filters)
        if not item:
            alt_filters = {"normalisation_reference": normalisation_id}
            if agency_id:
                alt_filters["agency_id"] = agency_id
            item = await self.db.collection(AIRLINE_KNOWLEDGE_NORMALISATION_COLLECTION).find_one(alt_filters)
        if not item:
            raise AirlineKnowledgeNormalisationError("Airline knowledge normalisation metadata was not found.")
        return item

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

    def _validate_payload(self, data: dict[str, Any], *, partial: bool = False) -> None:
        if data.get("normalisation_status") and data["normalisation_status"] not in NORMALISATION_STATUSES:
            raise AirlineKnowledgeNormalisationError("Normalisation status must be a known metadata status.")
        if data.get("normalisation_type") and data["normalisation_type"] not in NORMALISATION_TYPES:
            raise AirlineKnowledgeNormalisationError("Normalisation type must be a known metadata type.")
        if data.get("review_status") and data["review_status"] not in REVIEW_STATUSES:
            raise AirlineKnowledgeNormalisationError("Review status must be a known metadata status.")
        if data.get("approval_status") and data["approval_status"] not in APPROVAL_STATUSES:
            raise AirlineKnowledgeNormalisationError("Approval status must be a known metadata status.")
        if not partial and not (data.get("canonical_code") or data.get("canonical_name")):
            raise AirlineKnowledgeNormalisationError("Canonical code or canonical name is required for normalisation metadata.")

    def _filter_list_value(self, items: list[dict[str, Any]], field: str, value: str | None) -> list[dict[str, Any]]:
        if not value:
            return items
        normalized = value.lower()
        return [
            item
            for item in items
            if normalized in {str(candidate).lower() for candidate in (item.get(field) or [])}
        ]

    def _display_name(self, item: dict[str, Any]) -> str:
        if item.get("canonical_name"):
            return str(item["canonical_name"])
        if item.get("canonical_code"):
            return str(item["canonical_code"])
        if item.get("normalisation_reference"):
            return str(item["normalisation_reference"])
        return item.get("id") or "Airline knowledge normalisation"

    def _normalisation_reference(self) -> str:
        return f"AKN-{new_id()[:8].upper()}"

    def _count_value(self, target: dict[str, int], value: Any) -> None:
        if value:
            target[str(value)] = target.get(str(value), 0) + 1

    def _list_count(self, value: Any) -> int:
        if not value:
            return 0
        if isinstance(value, list):
            return len(value)
        return 1

    def _sort_text(self, value: Any) -> str:
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value or "")

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "normalisation_foundation": True,
            "canonical_vocabulary_foundation": True,
            "live_evaluation_disabled": True,
            "ai_parsing_disabled": True,
            "recommendation_engine_disabled": True,
            "feasibility_scoring_disabled": True,
            "pricing_calculation_disabled": True,
            "scraping_disabled": True,
            "background_workers_disabled": True,
            "provider_integrations_disabled": True,
        }
