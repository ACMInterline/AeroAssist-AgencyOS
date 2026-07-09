from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import AirlineKnowledgeAcquisition, AirlineKnowledgeAcquisitionCreate, AirlineKnowledgeAcquisitionUpdate, new_id


PHASE_LABEL = "phase_51_3_client_passenger_master_workspace_foundation"
AIRLINE_KNOWLEDGE_ACQUISITION_COLLECTION = "airline_knowledge_acquisitions"

ACQUISITION_STATUSES = [
    "draft",
    "captured",
    "awaiting_review",
    "reviewed",
    "approved",
    "rejected",
    "superseded",
    "archived",
]

SOURCE_TYPES = [
    "airline_website",
    "airline_pdf",
    "airline_manual",
    "email_from_airline",
    "gds_help_page",
    "tariff_note",
    "agency_contract",
    "internal_note",
    "other",
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

FUTURE_AOIE_FEEDS = [
    "50.2 Operational Constraint Engine",
    "50.3 Airline Operational Knowledge Normalisation",
    "50.4 Knowledge Governance & Version Control",
    "50.5 Airline Operational Capability Matrix",
    "50.6 Operational Knowledge Evaluation Engine",
    "50.7 Passenger Service Feasibility Engine",
    "50.8 Airline & Itinerary Recommendation Engine",
    "50.9 Offer Builder Intelligence Integration",
]

KNOWLEDGE_GRAPH_PILLARS = [
    "evidence",
    "policy",
    "pricing",
    "capability",
    "operational_constraints",
]

PRICING_MODELS = [
    "flat_fee",
    "route_fee",
    "cabin_fee",
    "passenger_type_fee",
    "weight_based",
    "dimension_based",
    "fare_based",
    "percentage",
    "manual_quotation",
    "airfare_only",
    "airfare_excluding_taxes",
    "airfare_including_airline_fees",
    "airfare_minus_discount",
    "route_specific",
    "cabin_specific",
]

EXTRA_SEAT_TYPES = [
    "passenger_of_size",
    "personal_comfort",
    "cbbg",
    "musical_instrument",
    "medical",
]


class AirlineKnowledgeAcquisitionError(ValueError):
    pass


class AirlineKnowledgeAcquisitionService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_platform_acquisitions(
        self,
        *,
        agency_id: str | None = None,
        airline: str | None = None,
        service_domain: str | None = None,
        service_family: str | None = None,
        ssr_code: str | None = None,
        rfic: str | None = None,
        rfisc: str | None = None,
        source_type: str | None = None,
        review_status: str | None = None,
        approval_status: str | None = None,
        effective_date: str | None = None,
        official_source_flag: bool | None = None,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if service_domain:
            filters["service_domain"] = service_domain
        if service_family:
            filters["service_family"] = service_family
        if ssr_code:
            filters["ssr_code"] = ssr_code
        if rfic:
            filters["rfic"] = rfic
        if rfisc:
            filters["rfisc"] = rfisc
        if source_type:
            filters["source_type"] = source_type
        if review_status:
            filters["review_status"] = review_status
        if approval_status:
            filters["approval_status"] = approval_status
        if official_source_flag is not None:
            filters["official_source_flag"] = official_source_flag

        items = await self.db.collection(AIRLINE_KNOWLEDGE_ACQUISITION_COLLECTION).find_many(filters or None)
        if not include_archived:
            items = [
                item
                for item in items
                if not item.get("deleted_at") and item.get("acquisition_status") != "archived"
            ]
        items = self._filter_airline(items, airline)
        items = self._filter_effective_date(items, effective_date)
        items.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._platform_projection(item) for item in items]

    async def list_agency_acquisitions(
        self,
        agency_id: str,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        items = await self.list_platform_acquisitions(agency_id=agency_id, **filters)
        return [self._agency_projection(item) for item in items if item.get("agency_id") == agency_id]

    async def platform_response(self, **filters: Any) -> dict[str, Any]:
        items = await self.list_platform_acquisitions(**filters)
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "airline_knowledge_acquisition_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "future_aoie_feeds": FUTURE_AOIE_FEEDS,
            "read_only": False,
            "metadata_only": True,
            "notice": "Airline Knowledge Acquisition stores Airline Operational Knowledge Graph metadata across evidence, policy, pricing, capability, and operational constraints. It does not parse with AI, extract automatically, scrape, crawl, automate airline websites, call providers or live airline APIs, recommend, assess feasibility, price, or run workers.",
            **self.safety_flags(),
        }

    async def agency_response(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        items = await self.list_agency_acquisitions(agency_id, **filters)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "airline_knowledge_acquisition_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "future_aoie_feeds": FUTURE_AOIE_FEEDS,
            "read_only": True,
            "metadata_only": True,
            "notice": "Agency Knowledge Acquisition is read-only Airline Operational Knowledge Graph metadata. No parser, AI interpretation, scraping, crawler, provider call, recommendation, feasibility, pricing, or worker runs here.",
            **self.safety_flags(),
        }

    async def platform_summary(self) -> dict[str, Any]:
        items = await self.list_platform_acquisitions()
        return {
            "phase": PHASE_LABEL,
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "future_aoie_feeds": FUTURE_AOIE_FEEDS,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        items = await self.list_agency_acquisitions(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "future_aoie_feeds": FUTURE_AOIE_FEEDS,
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def get_platform_acquisition(self, acquisition_id: str) -> dict[str, Any]:
        item = await self._require_acquisition(acquisition_id)
        return await self._platform_projection(item)

    async def get_agency_acquisition(self, agency_id: str, acquisition_id: str) -> dict[str, Any]:
        item = await self._require_acquisition(acquisition_id, agency_id=agency_id)
        return self._agency_projection(await self._platform_projection(item))

    async def create_acquisition(self, payload: AirlineKnowledgeAcquisitionCreate, user: dict) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        self._validate_payload(data)
        data.setdefault("acquisition_reference", self._acquisition_reference())
        data.setdefault("acquisition_status", "draft")
        data.setdefault("acquisition_version", "1.0")
        data.setdefault("source_type", "other")
        data.setdefault("review_status", "not_started")
        data.setdefault("approval_status", "not_requested")
        data.setdefault("created_by", user.get("id"))
        data["updated_by"] = user.get("id")
        self._prepare_knowledge_graph_defaults(data)
        data.update(self.safety_flags())
        acquisition = AirlineKnowledgeAcquisition(**data)
        created = await self.db.collection(AIRLINE_KNOWLEDGE_ACQUISITION_COLLECTION).insert_one(acquisition.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "airline_knowledge_acquisition": await self._platform_projection(created),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def update_acquisition(self, acquisition_id: str, payload: AirlineKnowledgeAcquisitionUpdate, user: dict) -> dict[str, Any]:
        existing = await self._require_acquisition(acquisition_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        self._validate_payload(updates, partial=True)
        updates["updated_by"] = user.get("id")
        updates.update(self.safety_flags())
        updated = await self.db.collection(AIRLINE_KNOWLEDGE_ACQUISITION_COLLECTION).update_one({"id": existing["id"]}, updates)
        if not updated:
            raise AirlineKnowledgeAcquisitionError("Airline knowledge acquisition metadata could not be updated.")
        return {
            "phase": PHASE_LABEL,
            "airline_knowledge_acquisition": await self._platform_projection(updated),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def delete_acquisition(self, acquisition_id: str, user: dict) -> dict[str, Any]:
        existing = await self._require_acquisition(acquisition_id)
        updated = await self.db.collection(AIRLINE_KNOWLEDGE_ACQUISITION_COLLECTION).update_one(
            {"id": existing["id"]},
            {
                "acquisition_status": "archived",
                "deleted_at": self._now(),
                "deleted_by": user.get("id"),
                "updated_by": user.get("id"),
                **self.safety_flags(),
            },
        )
        if not updated:
            raise AirlineKnowledgeAcquisitionError("Airline knowledge acquisition metadata could not be archived.")
        return {
            "phase": PHASE_LABEL,
            "airline_knowledge_acquisition": await self._platform_projection(updated),
            "archived": True,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        by_acquisition_status = {status: 0 for status in ACQUISITION_STATUSES}
        by_source_type = {source_type: 0 for source_type in SOURCE_TYPES}
        by_review_status = {status: 0 for status in REVIEW_STATUSES}
        by_approval_status = {status: 0 for status in APPROVAL_STATUSES}
        by_service_domain: dict[str, int] = {}
        by_service_family: dict[str, int] = {}
        by_airline: dict[str, int] = {}
        official_source_count = 0
        raw_source_text_count = 0
        version_link_count = 0
        future_aoie_link_count = 0
        operational_link_count = 0
        policy_count = 0
        pricing_count = 0
        capability_count = 0
        operational_constraint_count = 0
        animal_transport_count = 0
        extra_seat_count = 0
        cabin_capability_count = 0
        operational_procedure_count = 0
        for item in items:
            self._count_value(by_acquisition_status, item.get("acquisition_status"))
            self._count_value(by_source_type, item.get("source_type"))
            self._count_value(by_review_status, item.get("review_status"))
            self._count_value(by_approval_status, item.get("approval_status"))
            self._count_value(by_service_domain, item.get("service_domain"))
            self._count_value(by_service_family, item.get("service_family"))
            self._count_value(by_airline, item.get("airline_code") or item.get("airline_name"))
            official_source_count += 1 if item.get("official_source_flag") else 0
            raw_source_text_count += 1 if item.get("raw_source_text") else 0
            version_link_count += 1 if item.get("previous_acquisition_id") else 0
            version_link_count += self._list_count(item.get("supersedes_acquisition_ids"))
            future_aoie_link_count += self._list_count(item.get("parser_run_ids"))
            future_aoie_link_count += self._list_count(item.get("normalized_rule_ids"))
            future_aoie_link_count += self._list_count(item.get("knowledge_version_ids"))
            future_aoie_link_count += self._list_count(item.get("capability_matrix_ids"))
            operational_link_count += self._list_count(item.get("ssr_osi_workspace_ids"))
            operational_link_count += self._list_count(item.get("emd_workspace_ids"))
            operational_link_count += self._list_count(item.get("ticket_workspace_ids"))
            operational_link_count += self._list_count(item.get("document_workspace_ids"))
            policy_count += 1 if self._metadata_object_has_content(item.get("policy")) else 0
            pricing_count += 1 if self._metadata_object_has_content(item.get("pricing")) else 0
            capability_count += self._list_count(item.get("capabilities"))
            animal_transport = item.get("animal_transport") or {}
            animal_transport_count += 1 if self._metadata_object_has_content(animal_transport) else 0
            extra_seat = item.get("extra_seat") or []
            cabin_capabilities = item.get("cabin_capabilities") or []
            extra_seat_count += self._list_count(extra_seat)
            cabin_capability_count += self._list_count(cabin_capabilities)
            operational_constraint_count += self._list_count(item.get("operational_constraints"))
            operational_constraint_count += self._list_count(animal_transport.get("constraints") if isinstance(animal_transport, dict) else None)
            operational_constraint_count += sum(self._list_count(entry.get("operational_constraints")) for entry in extra_seat if isinstance(entry, dict))
            operational_constraint_count += sum(self._list_count(entry.get("constraints")) for entry in cabin_capabilities if isinstance(entry, dict))
            operational_procedure_count += self._list_count(item.get("operational_procedures"))
        return {
            "total_count": len(items),
            "by_acquisition_status": by_acquisition_status,
            "by_source_type": by_source_type,
            "by_review_status": by_review_status,
            "by_approval_status": by_approval_status,
            "by_service_domain": by_service_domain,
            "by_service_family": by_service_family,
            "by_airline": by_airline,
            "official_source_count": official_source_count,
            "raw_source_text_count": raw_source_text_count,
            "version_link_count": version_link_count,
            "future_aoie_link_count": future_aoie_link_count,
            "operational_link_count": operational_link_count,
            "knowledge_graph_pillars": KNOWLEDGE_GRAPH_PILLARS,
            "policy_count": policy_count,
            "pricing_count": pricing_count,
            "capability_count": capability_count,
            "operational_constraint_count": operational_constraint_count,
            "animal_transport_count": animal_transport_count,
            "extra_seat_count": extra_seat_count,
            "cabin_capability_count": cabin_capability_count,
            "operational_procedure_count": operational_procedure_count,
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "airline": "airline_code, airline_name, validating_carrier, or operating_carrier exact metadata match",
            "service_domain": "service_domain exact metadata match",
            "service_family": "service_family exact metadata match",
            "ssr_code": "ssr_code exact metadata match",
            "rfic": "rfic exact metadata match",
            "rfisc": "rfisc exact metadata match",
            "source_type": SOURCE_TYPES,
            "review_status": REVIEW_STATUSES,
            "approval_status": APPROVAL_STATUSES,
            "effective_date": "source_effective_date exact YYYY-MM-DD metadata match",
            "official_source_flag": "true or false",
            "knowledge_graph_pillars": KNOWLEDGE_GRAPH_PILLARS,
            "pricing_models": PRICING_MODELS,
            "extra_seat_types": EXTRA_SEAT_TYPES,
            "operational_constraint_shape": ["condition", "operator", "value", "outcome", "reason", "notes"],
            "metadata_only": True,
        }

    async def _platform_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        self._prepare_knowledge_graph_defaults(projected)
        projected["acquisition_display_name"] = self._display_name(projected)
        projected["future_aoie_feeds"] = FUTURE_AOIE_FEEDS
        projected["operational_knowledge_graph_pillars"] = KNOWLEDGE_GRAPH_PILLARS
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

    async def _require_acquisition(self, acquisition_id: str, *, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": acquisition_id}
        if agency_id:
            filters["agency_id"] = agency_id
        item = await self.db.collection(AIRLINE_KNOWLEDGE_ACQUISITION_COLLECTION).find_one(filters)
        if not item:
            alt_filters = {"acquisition_reference": acquisition_id}
            if agency_id:
                alt_filters["agency_id"] = agency_id
            item = await self.db.collection(AIRLINE_KNOWLEDGE_ACQUISITION_COLLECTION).find_one(alt_filters)
        if not item:
            raise AirlineKnowledgeAcquisitionError("Airline knowledge acquisition metadata was not found.")
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
        if data.get("acquisition_status") and data["acquisition_status"] not in ACQUISITION_STATUSES:
            raise AirlineKnowledgeAcquisitionError("Acquisition status must be a known acquisition metadata status.")
        if data.get("source_type") and data["source_type"] not in SOURCE_TYPES:
            raise AirlineKnowledgeAcquisitionError("Source type must be a known acquisition source type.")
        if data.get("review_status") and data["review_status"] not in REVIEW_STATUSES:
            raise AirlineKnowledgeAcquisitionError("Review status must be a known acquisition review status.")
        if data.get("approval_status") and data["approval_status"] not in APPROVAL_STATUSES:
            raise AirlineKnowledgeAcquisitionError("Approval status must be a known acquisition approval status.")
        if not partial and not (data.get("raw_source_text") or data.get("source_excerpt") or data.get("source_notes")):
            raise AirlineKnowledgeAcquisitionError("At least one source evidence text field is required for acquisition metadata.")

    def _prepare_knowledge_graph_defaults(self, data: dict[str, Any]) -> None:
        data.setdefault("knowledge_graph_pillars", list(KNOWLEDGE_GRAPH_PILLARS))
        if not self._metadata_object_has_content(data.get("evidence")):
            data["evidence"] = self._evidence_from_source(data)
        data.setdefault("policy", {})
        data.setdefault("pricing", {})
        data.setdefault("capabilities", [])
        data.setdefault("operational_constraints", [])
        data.setdefault("animal_transport", {})
        data.setdefault("extra_seat", [])
        data.setdefault("cabin_capabilities", [])
        data.setdefault("operational_procedures", [])

    def _evidence_from_source(self, data: dict[str, Any]) -> dict[str, Any]:
        return {
            "official_source": "official" if data.get("official_source_flag") else None,
            "source_title": data.get("source_title"),
            "source_type": data.get("source_type"),
            "source_url": data.get("source_url"),
            "publication_date": data.get("source_publication_date"),
            "effective_date": data.get("source_effective_date"),
            "retrieved_date": data.get("source_retrieved_date"),
            "original_text": data.get("raw_source_text"),
            "source_confidence": data.get("source_confidence"),
            "human_reviewer": data.get("reviewer"),
            "version": data.get("acquisition_version"),
            "source_hash": data.get("source_hash"),
            "attachment_ids": data.get("source_attachment_ids") or [],
            "notes": data.get("source_notes"),
        }

    def _filter_airline(self, items: list[dict[str, Any]], airline: str | None) -> list[dict[str, Any]]:
        if not airline:
            return items
        value = airline.lower()
        keys = ["airline_code", "airline_name", "validating_carrier", "operating_carrier"]
        return [
            item
            for item in items
            if value in {str(item.get(key) or "").lower() for key in keys}
        ]

    def _filter_effective_date(self, items: list[dict[str, Any]], effective_date: str | None) -> list[dict[str, Any]]:
        if not effective_date:
            return items
        return [
            item
            for item in items
            if str(item.get("source_effective_date") or "")[:10] == effective_date
        ]

    def _display_name(self, item: dict[str, Any]) -> str:
        if item.get("source_title"):
            return str(item["source_title"])
        if item.get("acquisition_reference"):
            return str(item["acquisition_reference"])
        return item.get("id") or "Airline knowledge acquisition"

    def _acquisition_reference(self) -> str:
        return f"AKA-{new_id()[:8].upper()}"

    def _count_value(self, target: dict[str, int], value: Any) -> None:
        if value:
            target[str(value)] = target.get(str(value), 0) + 1

    def _list_count(self, value: Any) -> int:
        if not value:
            return 0
        if isinstance(value, list):
            return len(value)
        return 1

    def _metadata_object_has_content(self, value: Any) -> bool:
        if not value:
            return False
        if isinstance(value, dict):
            for item in value.values():
                if isinstance(item, (dict, list)):
                    if self._metadata_object_has_content(item):
                        return True
                elif item not in (None, "", False):
                    return True
            return False
        if isinstance(value, list):
            return any(self._metadata_object_has_content(item) for item in value)
        return True

    def _sort_text(self, value: Any) -> str:
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value or "")

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "evidence_intake_only": True,
            "operational_knowledge_graph_foundation": True,
            "policy_pricing_capability_constraints_separated": True,
            "ai_parsing_disabled": True,
            "automatic_extraction_disabled": True,
            "web_scraping_disabled": True,
            "web_crawling_disabled": True,
            "airline_website_automation_disabled": True,
            "provider_integrations_disabled": True,
            "live_airline_apis_disabled": True,
            "recommendation_engine_disabled": True,
            "feasibility_engine_disabled": True,
            "pricing_calculation_engine_disabled": True,
            "background_workers_disabled": True,
            "parser_execution_disabled": True,
            "automation_disabled": True,
        }
