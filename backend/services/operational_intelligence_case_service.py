from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import (
    OperationalIntelligenceCase,
    OperationalIntelligenceCaseCreate,
    OperationalIntelligenceCaseUpdate,
)


PHASE_LABEL = "phase_55_2_airline_policy_evidence_source_governance_foundation"
OPERATIONAL_INTELLIGENCE_CASES_COLLECTION = "operational_intelligence_cases"

OPERATIONAL_INTELLIGENCE_CASE_STATUSES = ["draft", "assembling", "in_review", "ready", "blocked", "archived"]
OPERATIONAL_INTELLIGENCE_OVERALL_STATUSES = ["ready", "conditional", "blocked", "needs_review", "unknown"]
PIPELINE_READY_FIELDS = [
    "acquisition_ready",
    "normalisation_ready",
    "constraints_ready",
    "governance_ready",
    "capability_matrix_ready",
    "evaluation_ready",
    "feasibility_ready",
    "recommendation_ready",
    "offer_intelligence_ready",
]
PIPELINE_LINK_FIELDS = [
    "knowledge_acquisition_ids",
    "normalisation_ids",
    "operational_constraint_ids",
    "knowledge_version_ids",
    "knowledge_release_ids",
    "capability_matrix_ids",
    "operational_evaluation_ids",
    "feasibility_ids",
    "recommendation_ids",
    "intelligent_offer_package_ids",
]


class OperationalIntelligenceCaseError(ValueError):
    pass


class OperationalIntelligenceCaseService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def platform_response(self, **filters: Any) -> dict[str, Any]:
        cases = await self.list_platform_cases(**filters)
        return {
            "phase": PHASE_LABEL,
            "items": cases,
            "cases": cases,
            "summary": self.summarize_counts(cases),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Operational Intelligence Cases consolidate Chapter 50 metadata from passenger need through offer-intelligence package. They add no new intelligence and do not search, book, ticket, issue EMDs, call providers, generate AI output, run workers, or send offers.",
            **self.safety_flags(),
        }

    async def agency_response(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        cases = await self.list_agency_cases(agency_id, **filters)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": cases,
            "cases": cases,
            "summary": self.summarize_counts(cases),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Intelligence Cases are agency-scoped metadata views of the Chapter 50 operational intelligence chain. Human authority remains final.",
            **self.safety_flags(),
        }

    async def platform_summary(self) -> dict[str, Any]:
        cases = await self.list_platform_cases()
        return {
            "phase": PHASE_LABEL,
            "summary": self.summarize_counts(cases),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        cases = await self.list_agency_cases(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(cases),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def list_platform_cases(
        self,
        *,
        agency_id: str | None = None,
        case_status: str | None = None,
        overall_case_status: str | None = None,
        airline: str | None = None,
        passenger_need: str | None = None,
        travel_request: str | None = None,
        trip_workspace: str | None = None,
        ready_for_agent_review: bool | None = None,
        ready_for_offer_builder: bool | None = None,
        ready_for_client_presentation: bool | None = None,
        include_archived: bool = False,
        **_: Any,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if case_status:
            filters["case_status"] = case_status
        if overall_case_status:
            filters["overall_case_status"] = overall_case_status
        if travel_request:
            filters["travel_request_id"] = travel_request
        if trip_workspace:
            filters["trip_workspace_id"] = trip_workspace
        if ready_for_agent_review is not None:
            filters["ready_for_agent_review"] = ready_for_agent_review
        if ready_for_offer_builder is not None:
            filters["ready_for_offer_builder"] = ready_for_offer_builder
        if ready_for_client_presentation is not None:
            filters["ready_for_client_presentation"] = ready_for_client_presentation

        items = await self.db.collection(OPERATIONAL_INTELLIGENCE_CASES_COLLECTION).find_many(filters or None)
        if not include_archived:
            items = [item for item in items if not item.get("archived") and item.get("case_status") != "archived"]
        items = [
            item
            for item in items
            if self._any_field_matches(item, ["recommended_airlines", "blocked_airlines", "conditional_airlines"], airline)
            and self._any_field_matches(item, ["passenger_need_summary", "passenger_requirements"], passenger_need)
        ]
        items.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._case_projection(item, read_only=False) for item in items]

    async def list_agency_cases(self, agency_id: str, **filters: Any) -> list[dict[str, Any]]:
        items = await self.list_platform_cases(agency_id=agency_id, **filters)
        return [await self._case_projection(item, read_only=False) for item in items if item.get("agency_id") == agency_id]

    async def get_platform_case(self, case_id: str) -> dict[str, Any]:
        item = await self._require_case(case_id)
        return await self._case_projection(item, read_only=False)

    async def get_agency_case(self, agency_id: str, case_id: str) -> dict[str, Any]:
        item = await self._require_case(case_id, agency_id=agency_id)
        return await self._case_projection(item, read_only=False)

    async def create_case(self, payload: OperationalIntelligenceCaseCreate, user: dict, agency_id: str | None = None) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        if agency_id:
            data["agency_id"] = agency_id
        data.setdefault("case_reference", self._case_reference())
        data.setdefault("case_status", "draft")
        self._validate_payload(data)
        data.setdefault("created_by", user.get("id"))
        data.update(self.safety_flags())
        record = OperationalIntelligenceCase(**data)
        created = await self.db.collection(OPERATIONAL_INTELLIGENCE_CASES_COLLECTION).insert_one(record.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "operational_intelligence_case": await self._case_projection(created, read_only=False),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def update_case(
        self,
        case_id: str,
        payload: OperationalIntelligenceCaseUpdate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_case(case_id, agency_id=agency_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        if agency_id:
            updates.pop("agency_id", None)
        self._validate_payload(updates, partial=True)
        updates.update(self.safety_flags())
        filters = {"id": existing["id"]}
        if agency_id:
            filters["agency_id"] = agency_id
        updated = await self.db.collection(OPERATIONAL_INTELLIGENCE_CASES_COLLECTION).update_one(filters, updates)
        if not updated:
            raise OperationalIntelligenceCaseError("Operational intelligence case metadata could not be updated.")
        return {
            "phase": PHASE_LABEL,
            "operational_intelligence_case": await self._case_projection(updated, read_only=False),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def archive_case(self, case_id: str, user: dict, agency_id: str | None = None) -> dict[str, Any]:
        existing = await self._require_case(case_id, agency_id=agency_id)
        updates = {
            "case_status": "archived",
            "archived": True,
            "archived_at": self._now(),
            **self.safety_flags(),
        }
        filters = {"id": existing["id"]}
        if agency_id:
            filters["agency_id"] = agency_id
        updated = await self.db.collection(OPERATIONAL_INTELLIGENCE_CASES_COLLECTION).update_one(filters, updates)
        if not updated:
            raise OperationalIntelligenceCaseError("Operational intelligence case metadata could not be archived.")
        return {
            "phase": PHASE_LABEL,
            "operational_intelligence_case": await self._case_projection(updated, read_only=False),
            "archived": True,
            "physical_delete_disabled": True,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "case_count": len(items),
            "by_case_status": self._counts(items, "case_status", OPERATIONAL_INTELLIGENCE_CASE_STATUSES),
            "by_overall_case_status": self._counts(items, "overall_case_status", OPERATIONAL_INTELLIGENCE_OVERALL_STATUSES),
            "ready_for_agent_review_count": len([item for item in items if item.get("ready_for_agent_review")]),
            "ready_for_offer_builder_count": len([item for item in items if item.get("ready_for_offer_builder")]),
            "ready_for_client_presentation_count": len([item for item in items if item.get("ready_for_client_presentation")]),
            "pipeline_ready_counts": {field: len([item for item in items if item.get(field)]) for field in PIPELINE_READY_FIELDS},
            "pipeline_link_counts": {
                field: sum(len(item.get(field) or []) for item in items)
                for field in PIPELINE_LINK_FIELDS
            },
            "recommended_airline_count": sum(len(item.get("recommended_airlines") or []) for item in items),
            "blocked_airline_count": sum(len(item.get("blocked_airlines") or []) for item in items),
            "conditional_airline_count": sum(len(item.get("conditional_airlines") or []) for item in items),
            "required_action_count": sum(len(item.get("required_actions_summary") or []) for item in items),
            "missing_pipeline_item_count": sum(len(item.get("missing_pipeline_items") or []) for item in items),
            "blocking_pipeline_item_count": sum(len(item.get("blocking_pipeline_items") or []) for item in items),
            "trace_entry_count": sum(
                len(item.get("evidence_trace") or [])
                + len(item.get("decision_trace") or [])
                + len(item.get("knowledge_trace") or [])
                + len(item.get("operational_trace") or [])
                for item in items
            ),
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "agency_id": "agency_id exact metadata match",
            "case_status": OPERATIONAL_INTELLIGENCE_CASE_STATUSES,
            "overall_case_status": OPERATIONAL_INTELLIGENCE_OVERALL_STATUSES,
            "airline": "recommended_airlines, blocked_airlines, or conditional_airlines metadata match",
            "passenger_need": "passenger_need_summary or passenger_requirements metadata match",
            "travel_request": "travel_request_id exact metadata match",
            "trip_workspace": "trip_workspace_id exact metadata match",
            "ready_for_agent_review": "boolean metadata match",
            "ready_for_offer_builder": "boolean metadata match",
            "ready_for_client_presentation": "boolean metadata match",
            "metadata_only": True,
        }

    async def _case_projection(self, item: dict[str, Any], *, read_only: bool) -> dict[str, Any]:
        projected = dict(item)
        projected["case_display_name"] = projected.get("case_reference") or projected.get("id")
        projected["pipeline_link_summary"] = self._pipeline_link_summary(projected)
        projected["pipeline_status_summary"] = self._pipeline_status_summary(projected)
        projected["decision_summary_metadata"] = self._decision_summary(projected)
        projected["trace_summary"] = self._trace_summary(projected)
        projected["readiness_metadata_summary"] = self._readiness_summary(projected)
        projected["read_only"] = read_only
        projected.update(self.safety_flags())
        return projected

    async def _require_case(self, case_id: str, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": case_id}
        if agency_id:
            filters["agency_id"] = agency_id
        item = await self.db.collection(OPERATIONAL_INTELLIGENCE_CASES_COLLECTION).find_one(filters)
        if not item:
            raise OperationalIntelligenceCaseError("Operational intelligence case metadata not found.")
        return item

    def _validate_payload(self, data: dict[str, Any], *, partial: bool = False) -> None:
        self._validate_choice(data, "case_status", OPERATIONAL_INTELLIGENCE_CASE_STATUSES, partial)
        self._validate_choice(data, "overall_case_status", OPERATIONAL_INTELLIGENCE_OVERALL_STATUSES, partial)

    def _validate_choice(self, data: dict[str, Any], field: str, allowed: list[str], partial: bool) -> None:
        if field not in data:
            return
        value = data.get(field)
        if value is None:
            return
        if value not in allowed:
            raise OperationalIntelligenceCaseError(f"Unsupported {field} metadata value: {value}.")

    def _pipeline_link_summary(self, item: dict[str, Any]) -> dict[str, int]:
        return {field: len(item.get(field) or []) for field in PIPELINE_LINK_FIELDS}

    def _pipeline_status_summary(self, item: dict[str, Any]) -> dict[str, Any]:
        ready = {field: bool(item.get(field)) for field in PIPELINE_READY_FIELDS}
        return {
            **ready,
            "ready_stage_count": len([value for value in ready.values() if value]),
            "total_stage_count": len(PIPELINE_READY_FIELDS),
        }

    def _decision_summary(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "overall_case_status": item.get("overall_case_status"),
            "recommended_airline_count": len(item.get("recommended_airlines") or []),
            "blocked_airline_count": len(item.get("blocked_airlines") or []),
            "conditional_airline_count": len(item.get("conditional_airlines") or []),
            "required_action_count": len(item.get("required_actions_summary") or []),
        }

    def _trace_summary(self, item: dict[str, Any]) -> dict[str, int]:
        return {
            "evidence_trace_count": len(item.get("evidence_trace") or []),
            "decision_trace_count": len(item.get("decision_trace") or []),
            "knowledge_trace_count": len(item.get("knowledge_trace") or []),
            "operational_trace_count": len(item.get("operational_trace") or []),
        }

    def _readiness_summary(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "ready_for_agent_review": bool(item.get("ready_for_agent_review")),
            "ready_for_offer_builder": bool(item.get("ready_for_offer_builder")),
            "ready_for_client_presentation": bool(item.get("ready_for_client_presentation")),
            "missing_pipeline_item_count": len(item.get("missing_pipeline_items") or []),
            "blocking_pipeline_item_count": len(item.get("blocking_pipeline_items") or []),
        }

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "operational_intelligence_pipeline_consolidation_foundation": True,
            "chapter_50_pipeline_consolidated": True,
            "no_new_intelligence_added": True,
            "scenario_testing_preparation": True,
            "real_airline_data_population_preparation": True,
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

    def _case_reference(self) -> str:
        return f"OIC-{self._now().replace(':', '').replace('-', '').replace('.', '')}"

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
