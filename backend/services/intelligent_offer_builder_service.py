from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import (
    IntelligentOfferBuilderPackage,
    IntelligentOfferBuilderPackageCreate,
    IntelligentOfferBuilderPackageUpdate,
)
from services.airline_fare_family_brand_intelligence_service import AirlineFareFamilyBrandIntelligenceService


PHASE_LABEL = "phase_56_2_journey_option_fare_brand_composition_workspace_foundation"
INTELLIGENT_OFFER_BUILDER_COLLECTION = "intelligent_offer_builder_packages"

INTELLIGENT_OFFER_PACKAGE_STATUSES = ["draft", "in_review", "ready", "approved", "archived"]
INTELLIGENT_OFFER_READINESS_STATUSES = ["ready", "conditional", "blocked", "needs_review", "unknown"]
INTELLIGENT_OFFER_CLIENT_VISIBILITY_STATUSES = ["internal", "agent_review", "client_ready", "client_visible", "hidden"]
RECOMMENDATION_LEVELS = ["highly_recommended", "recommended", "acceptable", "use_with_caution", "not_recommended"]
OPERATIONAL_RISK_LEVELS = ["low", "medium", "high", "critical", "unknown"]


class IntelligentOfferBuilderError(ValueError):
    pass


class IntelligentOfferBuilderService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def platform_response(self, **filters: Any) -> dict[str, Any]:
        packages = await self.list_platform_packages(**filters)
        return {
            "phase": PHASE_LABEL,
            "items": packages,
            "packages": packages,
            "summary": self.summarize_counts(packages),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Intelligent Offer Builder consumes approved operational intelligence and prepares explainable offer-intelligence metadata. It does not search, book, ticket, issue EMDs, call providers, generate AI output, or send offers.",
            **self.safety_flags(),
        }

    async def agency_response(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        packages = await self.list_agency_packages(agency_id, **filters)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": packages,
            "packages": packages,
            "summary": self.summarize_counts(packages),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Offer Intelligence packages are agency-scoped metadata for human-reviewed offer presentation support. Automatic offer sending, booking, ticketing, EMD issuance, live search, provider execution, and AI generation stay disabled.",
            **self.safety_flags(),
        }

    async def platform_summary(self) -> dict[str, Any]:
        packages = await self.list_platform_packages()
        return {
            "phase": PHASE_LABEL,
            "summary": self.summarize_counts(packages),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        packages = await self.list_agency_packages(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(packages),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def list_platform_packages(
        self,
        *,
        agency_id: str | None = None,
        package_status: str | None = None,
        airline: str | None = None,
        recommendation_level: str | None = None,
        readiness_status: str | None = None,
        operational_risk: str | None = None,
        passenger_need: str | None = None,
        destination: str | None = None,
        travel_date: str | None = None,
        offer_workspace: str | None = None,
        client_visibility_status: str | None = None,
        include_archived: bool = False,
        **_: Any,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if package_status:
            filters["package_status"] = package_status
        if readiness_status:
            filters["readiness_status"] = readiness_status
        if travel_date:
            filters["travel_date"] = travel_date
        if client_visibility_status:
            filters["client_visibility_status"] = client_visibility_status
        if offer_workspace:
            filters["offer_workspace_id"] = offer_workspace

        items = await self.db.collection(INTELLIGENT_OFFER_BUILDER_COLLECTION).find_many(filters or None)
        if not include_archived:
            items = [item for item in items if not item.get("archived") and item.get("package_status") != "archived"]
        items = [
            item
            for item in items
            if self._any_field_matches(item, ["recommended_airlines"], airline)
            and self._any_field_matches(item, ["recommendation_levels"], recommendation_level)
            and self._any_field_matches(item, ["operational_risk_level", "internal_risk_notes"], operational_risk)
            and self._any_field_matches(item, ["passenger_need_summary", "passenger_requirements"], passenger_need)
            and self._any_field_matches(item, ["destination"], destination)
        ]
        items.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._package_projection(item, read_only=False) for item in items]

    async def list_agency_packages(self, agency_id: str, **filters: Any) -> list[dict[str, Any]]:
        items = await self.list_platform_packages(agency_id=agency_id, **filters)
        return [await self._package_projection(item, read_only=False) for item in items if item.get("agency_id") == agency_id]

    async def get_platform_package(self, package_id: str) -> dict[str, Any]:
        item = await self._require_package(package_id)
        return await self._package_projection(item, read_only=False)

    async def get_agency_package(self, agency_id: str, package_id: str) -> dict[str, Any]:
        item = await self._require_package(package_id, agency_id=agency_id)
        return await self._package_projection(item, read_only=False)

    async def create_package(self, payload: IntelligentOfferBuilderPackageCreate, user: dict, agency_id: str | None = None) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        if agency_id:
            data["agency_id"] = agency_id
        data.setdefault("offer_intelligence_reference", self._package_reference())
        data.setdefault("package_status", "draft")
        self._validate_payload(data)
        data.setdefault("created_by", user.get("id"))
        data.update(self.safety_flags())
        record = IntelligentOfferBuilderPackage(**data)
        created = await self.db.collection(INTELLIGENT_OFFER_BUILDER_COLLECTION).insert_one(record.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "intelligent_offer_builder_package": await self._package_projection(created, read_only=False),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def update_package(
        self,
        package_id: str,
        payload: IntelligentOfferBuilderPackageUpdate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_package(package_id, agency_id=agency_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        if agency_id:
            updates.pop("agency_id", None)
        self._validate_payload(updates, partial=True)
        updates.update(self.safety_flags())
        filters = {"id": existing["id"]}
        if agency_id:
            filters["agency_id"] = agency_id
        updated = await self.db.collection(INTELLIGENT_OFFER_BUILDER_COLLECTION).update_one(filters, updates)
        if not updated:
            raise IntelligentOfferBuilderError("Offer intelligence package metadata could not be updated.")
        return {
            "phase": PHASE_LABEL,
            "intelligent_offer_builder_package": await self._package_projection(updated, read_only=False),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def archive_package(self, package_id: str, user: dict, agency_id: str | None = None) -> dict[str, Any]:
        existing = await self._require_package(package_id, agency_id=agency_id)
        updates = {
            "package_status": "archived",
            "archived": True,
            "archived_at": self._now(),
            **self.safety_flags(),
        }
        filters = {"id": existing["id"]}
        if agency_id:
            filters["agency_id"] = agency_id
        updated = await self.db.collection(INTELLIGENT_OFFER_BUILDER_COLLECTION).update_one(filters, updates)
        if not updated:
            raise IntelligentOfferBuilderError("Offer intelligence package metadata could not be archived.")
        return {
            "phase": PHASE_LABEL,
            "intelligent_offer_builder_package": await self._package_projection(updated, read_only=False),
            "archived": True,
            "physical_delete_disabled": True,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "package_count": len(items),
            "by_package_status": self._counts(items, "package_status", INTELLIGENT_OFFER_PACKAGE_STATUSES),
            "by_readiness_status": self._counts(items, "readiness_status", INTELLIGENT_OFFER_READINESS_STATUSES),
            "by_client_visibility_status": self._counts(items, "client_visibility_status", INTELLIGENT_OFFER_CLIENT_VISIBILITY_STATUSES),
            "decision_pack_ready_count": len([item for item in items if item.get("decision_pack_ready")]),
            "prepared_for_offer_builder_count": len([item for item in items if item.get("prepared_for_offer_builder")]),
            "approved_for_client_presentation_count": len([item for item in items if item.get("approved_for_client_presentation")]),
            "recommendation_reference_count": sum(len(item.get("recommendation_ids") or []) for item in items),
            "feasibility_reference_count": sum(len(item.get("feasibility_ids") or []) for item in items),
            "operational_evaluation_reference_count": sum(len(item.get("operational_evaluation_ids") or []) for item in items),
            "capability_matrix_reference_count": sum(len(item.get("capability_matrix_ids") or []) for item in items),
            "evidence_reference_count": sum(len(item.get("evidence_reference_ids") or []) for item in items),
            "required_action_count": sum(self._required_action_count(item) for item in items),
            "client_explanation_count": len(
                [
                    item
                    for item in items
                    if item.get("client_explanation_summary")
                    or item.get("client_visible_reasons")
                    or item.get("client_visible_conditions")
                ]
            ),
            "internal_trace_count": sum(
                len(item.get("internal_evidence_trace") or []) + len(item.get("internal_decision_trace") or [])
                for item in items
            ),
            "decision_pack_section_count": sum(len(item.get("decision_pack_sections") or []) for item in items),
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "agency_id": "agency_id exact metadata match",
            "package_status": INTELLIGENT_OFFER_PACKAGE_STATUSES,
            "airline": "recommended_airlines metadata match",
            "recommendation_level": RECOMMENDATION_LEVELS,
            "readiness_status": INTELLIGENT_OFFER_READINESS_STATUSES,
            "operational_risk": OPERATIONAL_RISK_LEVELS,
            "passenger_need": "passenger_need_summary or passenger_requirements metadata match",
            "destination": "destination metadata match",
            "travel_date": "travel_date exact metadata match",
            "offer_workspace": "offer_workspace_id exact metadata match",
            "client_visibility_status": INTELLIGENT_OFFER_CLIENT_VISIBILITY_STATUSES,
            "metadata_only": True,
        }

    async def _package_projection(self, item: dict[str, Any], *, read_only: bool) -> dict[str, Any]:
        projected = dict(item)
        projected["package_display_name"] = projected.get("offer_intelligence_reference") or projected.get("id")
        projected["input_reference_summary"] = self._input_reference_summary(projected)
        projected["recommended_option_summary"] = self._recommended_option_summary(projected)
        projected["readiness_metadata_summary"] = self._readiness_summary(projected)
        projected["required_action_summary"] = self._action_summary(projected)
        projected["explanation_summary"] = self._explanation_summary(projected)
        projected["decision_pack_metadata_summary"] = self._decision_pack_summary(projected)
        projected["fare_brand_intelligence"] = await AirlineFareFamilyBrandIntelligenceService(
            self.db
        ).offer_builder_package_attributes(projected)
        projected["read_only"] = read_only
        projected.update(self.safety_flags())
        return projected

    async def _require_package(self, package_id: str, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": package_id}
        if agency_id:
            filters["agency_id"] = agency_id
        item = await self.db.collection(INTELLIGENT_OFFER_BUILDER_COLLECTION).find_one(filters)
        if not item:
            raise IntelligentOfferBuilderError("Offer intelligence package metadata not found.")
        return item

    def _validate_payload(self, data: dict[str, Any], *, partial: bool = False) -> None:
        self._validate_choice(data, "package_status", INTELLIGENT_OFFER_PACKAGE_STATUSES, partial)
        self._validate_choice(data, "readiness_status", INTELLIGENT_OFFER_READINESS_STATUSES, partial)
        self._validate_choice(data, "client_visibility_status", INTELLIGENT_OFFER_CLIENT_VISIBILITY_STATUSES, partial)
        self._validate_choice(data, "operational_risk_level", OPERATIONAL_RISK_LEVELS, partial)
        if "recommendation_levels" in data:
            unknown_levels = [level for level in data.get("recommendation_levels") or [] if level not in RECOMMENDATION_LEVELS]
            if unknown_levels:
                raise IntelligentOfferBuilderError(f"Unsupported recommendation level metadata: {', '.join(unknown_levels)}.")

    def _validate_choice(self, data: dict[str, Any], field: str, allowed: list[str], partial: bool) -> None:
        if field not in data:
            return
        value = data.get(field)
        if value is None:
            return
        if value not in allowed:
            raise IntelligentOfferBuilderError(f"Unsupported {field} metadata value: {value}.")

    def _input_reference_summary(self, item: dict[str, Any]) -> dict[str, int]:
        return {
            "recommendations": len(item.get("recommendation_ids") or []),
            "feasibilities": len(item.get("feasibility_ids") or []),
            "operational_evaluations": len(item.get("operational_evaluation_ids") or []),
            "capability_matrix_records": len(item.get("capability_matrix_ids") or []),
            "knowledge_versions": len(item.get("knowledge_version_ids") or []),
            "evidence_references": len(item.get("evidence_reference_ids") or []),
        }

    def _recommended_option_summary(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "airline_count": len(item.get("recommended_airlines") or []),
            "itinerary_count": len(item.get("recommended_itineraries") or []),
            "ranking_count": len(item.get("recommendation_rankings") or []),
            "score_count": len(item.get("recommendation_scores") or []),
            "levels": item.get("recommendation_levels") or [],
            "reason_count": len(item.get("recommendation_reasons") or []),
        }

    def _readiness_summary(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "readiness_status": item.get("readiness_status"),
            "blocker_count": len(item.get("readiness_blockers") or []),
            "warning_count": len(item.get("readiness_warnings") or []),
            "condition_count": len(item.get("readiness_conditions") or []),
            "operational_risk_level": item.get("operational_risk_level"),
        }

    def _action_summary(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "required_action_count": self._required_action_count(item),
            "required_ssr_count": len(item.get("required_ssrs") or []),
            "required_osi_count": len(item.get("required_osis") or []),
            "required_emd_count": len(item.get("required_emds") or []),
            "required_document_count": len(item.get("required_documents") or []),
            "manual_review_required": bool(item.get("required_manual_review")),
            "airline_approval_required": bool(item.get("required_airline_approval")),
        }

    def _required_action_count(self, item: dict[str, Any]) -> int:
        return (
            len(item.get("required_ssrs") or [])
            + len(item.get("required_osis") or [])
            + len(item.get("required_emds") or [])
            + len(item.get("required_documents") or [])
            + len(item.get("required_follow_up_tasks") or [])
            + int(bool(item.get("required_medif")))
            + int(bool(item.get("required_manual_review")))
            + int(bool(item.get("required_airline_approval")))
            + int(bool(item.get("required_station_notification")))
            + int(bool(item.get("required_crew_notification")))
        )

    def _explanation_summary(self, item: dict[str, Any]) -> dict[str, int]:
        return {
            "client_visible_reason_count": len(item.get("client_visible_reasons") or []),
            "client_visible_limitation_count": len(item.get("client_visible_limitations") or []),
            "client_visible_condition_count": len(item.get("client_visible_conditions") or []),
            "client_visible_document_count": len(item.get("client_visible_documents") or []),
            "internal_evidence_trace_count": len(item.get("internal_evidence_trace") or []),
            "internal_decision_trace_count": len(item.get("internal_decision_trace") or []),
        }

    def _decision_pack_summary(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "decision_pack_ready": bool(item.get("decision_pack_ready")),
            "decision_pack_reference": item.get("decision_pack_reference"),
            "section_count": len(item.get("decision_pack_sections") or []),
            "evidence_count": len(item.get("decision_pack_evidence") or []),
        }

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "intelligent_offer_builder_integration_foundation": True,
            "offer_builder_should_not_invent_intelligence": True,
            "consumes_passenger_service_feasibility": True,
            "consumes_airline_recommendations": True,
            "consumes_operational_evaluations": True,
            "consumes_capability_matrix": True,
            "consumes_knowledge_governance_evidence": True,
            "consumes_fare_brand_intelligence": True,
            "advisory_only": True,
            "human_authority_final": True,
            "no_live_gds_search": True,
            "no_ndc_search": True,
            "flight_search_disabled": True,
            "booking_disabled": True,
            "ticketing_disabled": True,
            "emd_issuance_disabled": True,
            "provider_integrations_disabled": True,
            "parser_execution_disabled": True,
            "no_ai_generation": True,
            "no_llm_generation": True,
            "background_workers_disabled": True,
            "automatic_sending_disabled": True,
        }

    def _package_reference(self) -> str:
        return f"IOB-{self._now().replace(':', '').replace('-', '').replace('.', '')}"

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
