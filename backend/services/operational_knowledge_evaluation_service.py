from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import (
    OperationalKnowledgeEvaluation,
    OperationalKnowledgeEvaluationCreate,
    OperationalKnowledgeEvaluationUpdate,
    new_id,
)


PHASE_LABEL = "phase_56_3_journey_comparison_client_presentation_foundation"
OPERATIONAL_KNOWLEDGE_EVALUATION_COLLECTION = "operational_knowledge_evaluations"

EVALUATION_STATUSES = ["draft", "in_review", "completed", "blocked", "archived"]
EVALUATION_TYPES = [
    "capability_policy_pricing_constraint_procedure",
    "capability",
    "policy",
    "pricing",
    "constraint",
    "procedure",
    "operational_bundle",
]
EVALUATION_RESULT_VALUES = ["pass", "fail", "warning", "manual_review", "not_applicable", "unknown"]
OPERATIONAL_RESULTS = ["applies", "does_not_apply", "conditional", "blocked", "manual_review", "unknown"]
EVALUATION_CONFIDENCE_LEVELS = ["official", "high", "medium", "low", "unknown"]
OPERATIONAL_RISK_LEVELS = ["low", "medium", "high", "critical", "unknown"]


class OperationalKnowledgeEvaluationError(ValueError):
    pass


class OperationalKnowledgeEvaluationService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def platform_response(self, **filters: Any) -> dict[str, Any]:
        evaluations = await self.list_platform_evaluations(**filters)
        return {
            "phase": PHASE_LABEL,
            "items": evaluations,
            "evaluations": evaluations,
            "summary": self.summarize_counts(evaluations),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Operational Knowledge Evaluations store deterministic, explainable metadata about what operational knowledge applies. They do not determine passenger feasibility, recommend airlines or itineraries, use AI or LLM prompts, search flights, book, ticket, execute parsers, optimise pricing, call providers, or run workers.",
            **self.safety_flags(),
        }

    async def agency_response(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        evaluations = await self.list_agency_evaluations(agency_id, **filters)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": evaluations,
            "evaluations": evaluations,
            "summary": self.summarize_counts(evaluations),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            "notice": "Agency Operational Evaluations are read-only metadata. Evaluation is not recommendation and does not decide passenger feasibility.",
            **self.safety_flags(),
        }

    async def platform_summary(self) -> dict[str, Any]:
        evaluations = await self.list_platform_evaluations()
        return {
            "phase": PHASE_LABEL,
            "summary": self.summarize_counts(evaluations),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        evaluations = await self.list_agency_evaluations(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(evaluations),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def list_platform_evaluations(
        self,
        *,
        agency_id: str | None = None,
        evaluation_status: str | None = None,
        evaluation_type: str | None = None,
        airline: str | None = None,
        passenger: str | None = None,
        travel_request_id: str | None = None,
        trip_workspace_id: str | None = None,
        booking_workspace_id: str | None = None,
        service_domain: str | None = None,
        service_family: str | None = None,
        ssr_code: str | None = None,
        capability_result: str | None = None,
        policy_result: str | None = None,
        pricing_result: str | None = None,
        constraint_result: str | None = None,
        operational_result: str | None = None,
        operational_risk: str | None = None,
        confidence: str | None = None,
        evaluation_completed: bool | None = None,
        include_archived: bool = False,
        **_: Any,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if evaluation_status:
            filters["evaluation_status"] = evaluation_status
        if evaluation_type:
            filters["evaluation_type"] = evaluation_type
        if travel_request_id:
            filters["travel_request_id"] = travel_request_id
        if trip_workspace_id:
            filters["trip_workspace_id"] = trip_workspace_id
        if booking_workspace_id:
            filters["booking_workspace_id"] = booking_workspace_id

        items = await self.db.collection(OPERATIONAL_KNOWLEDGE_EVALUATION_COLLECTION).find_many(filters or None)
        if not include_archived:
            items = [item for item in items if not item.get("archived") and item.get("evaluation_status") != "archived"]
        items = [
            item
            for item in items
            if self._any_field_matches(item, ["airline_code", "validating_carrier", "operating_carrier", "marketing_carrier"], airline)
            and self._any_field_matches(item, ["passenger_workspace_id", "passenger_profile_reference", "passenger_need_summary"], passenger)
            and self._any_field_matches(item, ["evaluated_service_domains"], service_domain)
            and self._any_field_matches(item, ["evaluated_service_families"], service_family)
            and self._any_field_matches(item, ["evaluated_ssrs"], ssr_code)
            and self._any_field_matches(item, ["capability_result"], capability_result)
            and self._any_field_matches(item, ["policy_result"], policy_result)
            and self._any_field_matches(item, ["pricing_result"], pricing_result)
            and self._any_field_matches(item, ["constraint_result"], constraint_result)
            and self._any_field_matches(item, ["operational_result"], operational_result)
            and self._any_field_matches(item, ["operational_risk"], operational_risk)
            and self._any_field_matches(item, ["evaluation_confidence"], confidence)
            and self._bool_matches(item.get("evaluation_completed"), evaluation_completed)
        ]
        items.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._evaluation_projection(item, read_only=False) for item in items]

    async def list_agency_evaluations(self, agency_id: str, **filters: Any) -> list[dict[str, Any]]:
        items = await self.list_platform_evaluations(agency_id=agency_id, **filters)
        return [self._agency_projection(item) for item in items if item.get("agency_id") == agency_id]

    async def get_platform_evaluation(self, evaluation_id: str) -> dict[str, Any]:
        item = await self._require_evaluation(evaluation_id)
        return await self._evaluation_projection(item, read_only=False)

    async def get_agency_evaluation(self, agency_id: str, evaluation_id: str) -> dict[str, Any]:
        item = await self._require_evaluation(evaluation_id, agency_id=agency_id)
        return self._agency_projection(await self._evaluation_projection(item, read_only=True))

    async def create_evaluation(self, payload: OperationalKnowledgeEvaluationCreate, user: dict) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        data.setdefault("evaluation_reference", self._evaluation_reference())
        data.setdefault("evaluation_status", "draft")
        self._validate_payload(data)
        data.setdefault("created_by", user.get("id"))
        data["updated_by"] = user.get("id")
        data.update(self.safety_flags())
        record = OperationalKnowledgeEvaluation(**data)
        created = await self.db.collection(OPERATIONAL_KNOWLEDGE_EVALUATION_COLLECTION).insert_one(record.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "operational_knowledge_evaluation": await self._evaluation_projection(created, read_only=False),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def update_evaluation(self, evaluation_id: str, payload: OperationalKnowledgeEvaluationUpdate, user: dict) -> dict[str, Any]:
        existing = await self._require_evaluation(evaluation_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        self._validate_payload(updates, partial=True)
        updates["updated_by"] = user.get("id")
        updates.update(self.safety_flags())
        updated = await self.db.collection(OPERATIONAL_KNOWLEDGE_EVALUATION_COLLECTION).update_one({"id": existing["id"]}, updates)
        if not updated:
            raise OperationalKnowledgeEvaluationError("Operational knowledge evaluation metadata could not be updated.")
        return {
            "phase": PHASE_LABEL,
            "operational_knowledge_evaluation": await self._evaluation_projection(updated, read_only=False),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def archive_evaluation(self, evaluation_id: str, user: dict) -> dict[str, Any]:
        existing = await self._require_evaluation(evaluation_id)
        now = self._now()
        updated = await self.db.collection(OPERATIONAL_KNOWLEDGE_EVALUATION_COLLECTION).update_one(
            {"id": existing["id"]},
            {
                "evaluation_status": "archived",
                "archived": True,
                "archived_at": now,
                "updated_by": user.get("id"),
                **self.safety_flags(),
            },
        )
        if not updated:
            raise OperationalKnowledgeEvaluationError("Operational knowledge evaluation metadata could not be archived.")
        return {
            "phase": PHASE_LABEL,
            "operational_knowledge_evaluation": await self._evaluation_projection(updated, read_only=False),
            "archived": True,
            "physical_delete_disabled": True,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "evaluation_count": len(items),
            "by_evaluation_status": self._counts(items, "evaluation_status", EVALUATION_STATUSES),
            "by_evaluation_type": self._counts(items, "evaluation_type", EVALUATION_TYPES),
            "by_capability_result": self._counts(items, "capability_result", EVALUATION_RESULT_VALUES),
            "by_policy_result": self._counts(items, "policy_result", EVALUATION_RESULT_VALUES),
            "by_pricing_result": self._counts(items, "pricing_result", EVALUATION_RESULT_VALUES),
            "by_constraint_result": self._counts(items, "constraint_result", EVALUATION_RESULT_VALUES),
            "by_procedure_result": self._counts(items, "operational_procedure_result", EVALUATION_RESULT_VALUES),
            "by_operational_result": self._counts(items, "operational_result", OPERATIONAL_RESULTS),
            "by_operational_risk": self._counts(items, "operational_risk", OPERATIONAL_RISK_LEVELS),
            "by_evaluation_confidence": self._counts(items, "evaluation_confidence", EVALUATION_CONFIDENCE_LEVELS),
            "completed_count": len([item for item in items if item.get("evaluation_completed")]),
            "evidence_trace_count": sum(len(item.get("evidence_trace") or []) for item in items),
            "source_reference_count": sum(
                len(item.get("knowledge_version_ids") or [])
                + len(item.get("capability_matrix_ids") or [])
                + len(item.get("operational_constraint_ids") or [])
                + len(item.get("acquisition_ids") or [])
                + len(item.get("evidence_reference_ids") or [])
                for item in items
            ),
            "required_action_count": sum(
                len(item.get("required_ssrs") or [])
                + len(item.get("required_osis") or [])
                + len(item.get("required_emds") or [])
                + len(item.get("required_documents") or [])
                + int(bool(item.get("required_medif")))
                + int(bool(item.get("required_manual_review")))
                + int(bool(item.get("required_airline_approval")))
                + int(bool(item.get("required_station_notification")))
                + int(bool(item.get("required_crew_notification")))
                for item in items
            ),
            "feasibility_ready_count": len([item for item in items if item.get("feasibility_ready")]),
            "recommendation_ready_count": len([item for item in items if item.get("recommendation_ready")]),
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "agency_id": "agency_id exact metadata match",
            "evaluation_status": EVALUATION_STATUSES,
            "evaluation_type": EVALUATION_TYPES,
            "airline": "airline_code, validating_carrier, operating_carrier, or marketing_carrier metadata match",
            "passenger": "passenger workspace, profile reference, or need-summary metadata match",
            "travel_request_id": "travel_request_id exact metadata match",
            "trip_workspace_id": "trip_workspace_id exact metadata match",
            "booking_workspace_id": "booking_workspace_id exact metadata match",
            "service_domain": "evaluated_service_domains metadata match",
            "service_family": "evaluated_service_families metadata match",
            "ssr_code": "evaluated_ssrs metadata match",
            "capability_result": EVALUATION_RESULT_VALUES,
            "policy_result": EVALUATION_RESULT_VALUES,
            "pricing_result": EVALUATION_RESULT_VALUES,
            "constraint_result": EVALUATION_RESULT_VALUES,
            "operational_result": OPERATIONAL_RESULTS,
            "operational_risk": OPERATIONAL_RISK_LEVELS,
            "confidence": EVALUATION_CONFIDENCE_LEVELS,
            "evaluation_completed": "metadata boolean",
            "metadata_only": True,
        }

    async def _evaluation_projection(self, item: dict[str, Any], *, read_only: bool) -> dict[str, Any]:
        projected = dict(item)
        projected["evaluation_display_name"] = projected.get("evaluation_reference") or projected.get("id")
        projected["source_summary"] = self._source_summary(projected)
        projected["scope_summary"] = self._scope_summary(projected)
        projected["action_summary"] = self._action_summary(projected)
        projected["explanation_sections"] = self._explanation_sections(projected)
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

    async def _require_evaluation(self, evaluation_id: str, *, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": evaluation_id}
        if agency_id:
            filters["agency_id"] = agency_id
        item = await self.db.collection(OPERATIONAL_KNOWLEDGE_EVALUATION_COLLECTION).find_one(filters)
        if not item:
            filters = {"evaluation_reference": evaluation_id}
            if agency_id:
                filters["agency_id"] = agency_id
            item = await self.db.collection(OPERATIONAL_KNOWLEDGE_EVALUATION_COLLECTION).find_one(filters)
        if not item:
            raise OperationalKnowledgeEvaluationError("Operational knowledge evaluation metadata was not found.")
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
        if data.get("evaluation_status") and data["evaluation_status"] not in EVALUATION_STATUSES:
            raise OperationalKnowledgeEvaluationError("Evaluation status must be known metadata.")
        if data.get("evaluation_type") and data["evaluation_type"] not in EVALUATION_TYPES:
            raise OperationalKnowledgeEvaluationError("Evaluation type must be known metadata.")
        for field in [
            "capability_result",
            "policy_result",
            "pricing_result",
            "constraint_result",
            "operational_procedure_result",
        ]:
            if data.get(field) and data[field] not in EVALUATION_RESULT_VALUES:
                raise OperationalKnowledgeEvaluationError(f"{field} must be a known evaluation result metadata value.")
        if data.get("operational_result") and data["operational_result"] not in OPERATIONAL_RESULTS:
            raise OperationalKnowledgeEvaluationError("Operational result must be known metadata.")
        if data.get("evaluation_confidence") and data["evaluation_confidence"] not in EVALUATION_CONFIDENCE_LEVELS:
            raise OperationalKnowledgeEvaluationError("Evaluation confidence must be known metadata.")
        if data.get("operational_risk") and data["operational_risk"] not in OPERATIONAL_RISK_LEVELS:
            raise OperationalKnowledgeEvaluationError("Operational risk must be known metadata.")
        has_evidence = bool(
            data.get("evidence_reference_ids")
            or data.get("evidence_trace")
            or data.get("capability_evidence")
            or data.get("policy_evidence")
        )
        if data.get("evaluation_completed") and not has_evidence:
            raise OperationalKnowledgeEvaluationError("Completed evaluation metadata must reference evidence.")
        if not partial and not data.get("evaluation_reference"):
            raise OperationalKnowledgeEvaluationError("Evaluation reference is required for evaluation metadata.")

    def _source_summary(self, item: dict[str, Any]) -> dict[str, int]:
        return {
            "knowledge_versions": len(item.get("knowledge_version_ids") or []),
            "capability_matrix_records": len(item.get("capability_matrix_ids") or []),
            "operational_constraints": len(item.get("operational_constraint_ids") or []),
            "acquisitions": len(item.get("acquisition_ids") or []),
            "evidence_references": len(item.get("evidence_reference_ids") or []),
        }

    def _scope_summary(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "service_domains": item.get("evaluated_service_domains") or [],
            "service_families": item.get("evaluated_service_families") or [],
            "ssrs": item.get("evaluated_ssrs") or [],
            "osis": len(item.get("evaluated_osis") or []),
            "emd_requirements": len(item.get("evaluated_emd_requirements") or []),
            "metadata_only": True,
        }

    def _action_summary(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "required_ssrs": len(item.get("required_ssrs") or []),
            "required_osis": len(item.get("required_osis") or []),
            "required_emds": len(item.get("required_emds") or []),
            "required_documents": len(item.get("required_documents") or []),
            "required_medif": bool(item.get("required_medif")),
            "required_manual_review": bool(item.get("required_manual_review")),
            "required_airline_approval": bool(item.get("required_airline_approval")),
            "required_station_notification": bool(item.get("required_station_notification")),
            "required_crew_notification": bool(item.get("required_crew_notification")),
        }

    def _explanation_sections(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "reason": item.get("operational_summary") or item.get("capability_reason") or item.get("policy_reason"),
            "evidence": item.get("evidence_trace") or item.get("evidence_reference_ids") or [],
            "capability": {"result": item.get("capability_result"), "reason": item.get("capability_reason"), "evidence": item.get("capability_evidence") or []},
            "policy": {"result": item.get("policy_result"), "reason": item.get("policy_reason"), "evidence": item.get("policy_evidence") or []},
            "pricing": {"result": item.get("pricing_result"), "reason": item.get("pricing_reason"), "reference": item.get("pricing_reference")},
            "constraint": {
                "result": item.get("constraint_result"),
                "reason": item.get("constraint_reason"),
                "triggered": item.get("triggered_constraints") or [],
                "blocking": item.get("blocking_constraints") or [],
                "warning": item.get("warning_constraints") or [],
            },
            "procedure": {"result": item.get("operational_procedure_result"), "reason": item.get("operational_procedure_reason")},
            "metadata_only": True,
        }

    def _counts(self, items: list[dict[str, Any]], field: str, known: list[str]) -> dict[str, int]:
        counts = {value: 0 for value in known}
        for item in items:
            value = item.get(field)
            if value:
                counts[str(value)] = counts.get(str(value), 0) + 1
        return counts

    def _any_field_matches(self, item: dict[str, Any], fields: list[str], value: str | None) -> bool:
        if not value:
            return True
        return any(self._value_matches(item.get(field), value) for field in fields)

    def _value_matches(self, candidate: Any, value: str) -> bool:
        normalized = value.lower()
        if isinstance(candidate, list):
            return normalized in {str(item).lower() for item in candidate}
        if candidate is None:
            return False
        return normalized == str(candidate).lower()

    def _bool_matches(self, candidate: Any, value: bool | None) -> bool:
        if value is None:
            return True
        return bool(candidate) is value

    def _sort_text(self, value: Any) -> str:
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value or "")

    def _evaluation_reference(self) -> str:
        return f"OKE-{new_id()[:8].upper()}"

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "operational_knowledge_evaluation_foundation": True,
            "deterministic_evaluation": True,
            "explainable_evaluation": True,
            "evidence_required": True,
            "no_ai_reasoning": True,
            "no_llm_prompts": True,
            "flight_search_disabled": True,
            "itinerary_recommendation_disabled": True,
            "booking_disabled": True,
            "ticketing_disabled": True,
            "provider_integrations_disabled": True,
            "parser_execution_disabled": True,
            "pricing_optimisation_disabled": True,
            "background_workers_disabled": True,
            "feasibility_determination_disabled": True,
            "recommendation_engine_disabled": True,
        }
