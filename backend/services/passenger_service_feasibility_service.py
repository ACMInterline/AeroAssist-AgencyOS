from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import (
    PassengerServiceFeasibility,
    PassengerServiceFeasibilityCreate,
    PassengerServiceFeasibilityUpdate,
    new_id,
)


PHASE_LABEL = "phase_55_8_airline_contact_communication_intelligence_foundation"
PASSENGER_SERVICE_FEASIBILITY_COLLECTION = "passenger_service_feasibilities"

FEASIBILITY_STATUSES = ["draft", "in_review", "completed", "blocked", "archived"]
FEASIBILITY_TYPES = [
    "passenger_service",
    "airline_service",
    "itinerary_service",
    "special_service",
    "operational_bundle",
]
FEASIBILITY_OUTCOMES = [
    "fully_feasible",
    "conditionally_feasible",
    "operational_review_required",
    "operationally_blocked",
    "unknown",
]
FEASIBILITY_CONFIDENCE_LEVELS = ["official", "high", "medium", "low", "unknown"]
OPERATIONAL_RISK_LEVELS = ["low", "medium", "high", "critical", "unknown"]


class PassengerServiceFeasibilityError(ValueError):
    pass


class PassengerServiceFeasibilityService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def platform_response(self, **filters: Any) -> dict[str, Any]:
        feasibilities = await self.list_platform_feasibilities(**filters)
        return {
            "phase": PHASE_LABEL,
            "items": feasibilities,
            "feasibilities": feasibilities,
            "summary": self.summarize_counts(feasibilities),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Passenger Service Feasibility records are advisory metadata. Feasibility is not Boolean, not recommendation, and human authority remains final.",
            **self.safety_flags(),
        }

    async def agency_response(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        feasibilities = await self.list_agency_feasibilities(agency_id, **filters)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": feasibilities,
            "feasibilities": feasibilities,
            "summary": self.summarize_counts(feasibilities),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            "notice": "Agency Service Feasibility records are read-only advisory metadata. They do not rank or recommend airlines.",
            **self.safety_flags(),
        }

    async def platform_summary(self) -> dict[str, Any]:
        feasibilities = await self.list_platform_feasibilities()
        return {
            "phase": PHASE_LABEL,
            "summary": self.summarize_counts(feasibilities),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        feasibilities = await self.list_agency_feasibilities(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(feasibilities),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def list_platform_feasibilities(
        self,
        *,
        agency_id: str | None = None,
        feasibility_status: str | None = None,
        feasibility_type: str | None = None,
        airline: str | None = None,
        feasibility_outcome: str | None = None,
        confidence_level: str | None = None,
        operational_risk: str | None = None,
        passenger_need_category: str | None = None,
        ssr_code: str | None = None,
        travel_date: str | None = None,
        cabin: str | None = None,
        destination: str | None = None,
        recommendation_ready: bool | None = None,
        include_archived: bool = False,
        **_: Any,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if feasibility_status:
            filters["feasibility_status"] = feasibility_status
        if feasibility_type:
            filters["feasibility_type"] = feasibility_type
        if feasibility_outcome:
            filters["feasibility_outcome"] = feasibility_outcome
        if travel_date:
            filters["travel_date"] = travel_date
        if passenger_need_category:
            filters["passenger_need_category"] = passenger_need_category

        items = await self.db.collection(PASSENGER_SERVICE_FEASIBILITY_COLLECTION).find_many(filters or None)
        if not include_archived:
            items = [item for item in items if not item.get("archived") and item.get("feasibility_status") != "archived"]
        items = [
            item
            for item in items
            if self._any_field_matches(item, ["airline_code", "airline_name", "validating_carrier", "operating_carrier", "marketing_carrier"], airline)
            and self._any_field_matches(item, ["feasibility_confidence", "data_confidence_level", "evidence_confidence_level", "operational_validation_confidence"], confidence_level)
            and self._any_field_matches(item, ["operational_risk_level"], operational_risk)
            and self._any_field_matches(item, ["required_ssrs"], ssr_code)
            and self._any_field_matches(item, ["cabin_requested"], cabin)
            and self._any_field_matches(item, ["destination"], destination)
            and self._bool_matches(item.get("recommendation_ready"), recommendation_ready)
        ]
        items.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._feasibility_projection(item, read_only=False) for item in items]

    async def list_agency_feasibilities(self, agency_id: str, **filters: Any) -> list[dict[str, Any]]:
        items = await self.list_platform_feasibilities(agency_id=agency_id, **filters)
        return [self._agency_projection(item) for item in items if item.get("agency_id") == agency_id]

    async def get_platform_feasibility(self, feasibility_id: str) -> dict[str, Any]:
        item = await self._require_feasibility(feasibility_id)
        return await self._feasibility_projection(item, read_only=False)

    async def get_agency_feasibility(self, agency_id: str, feasibility_id: str) -> dict[str, Any]:
        item = await self._require_feasibility(feasibility_id, agency_id=agency_id)
        return self._agency_projection(await self._feasibility_projection(item, read_only=True))

    async def create_feasibility(self, payload: PassengerServiceFeasibilityCreate, user: dict) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        data.setdefault("feasibility_reference", self._feasibility_reference())
        data.setdefault("feasibility_status", "draft")
        self._validate_payload(data)
        data.setdefault("created_by", user.get("id"))
        data["updated_by"] = user.get("id")
        data.update(self.safety_flags())
        record = PassengerServiceFeasibility(**data)
        created = await self.db.collection(PASSENGER_SERVICE_FEASIBILITY_COLLECTION).insert_one(record.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "passenger_service_feasibility": await self._feasibility_projection(created, read_only=False),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def update_feasibility(self, feasibility_id: str, payload: PassengerServiceFeasibilityUpdate, user: dict) -> dict[str, Any]:
        existing = await self._require_feasibility(feasibility_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        self._validate_payload(updates, partial=True)
        updates["updated_by"] = user.get("id")
        updates.update(self.safety_flags())
        updated = await self.db.collection(PASSENGER_SERVICE_FEASIBILITY_COLLECTION).update_one({"id": existing["id"]}, updates)
        if not updated:
            raise PassengerServiceFeasibilityError("Passenger service feasibility metadata could not be updated.")
        return {
            "phase": PHASE_LABEL,
            "passenger_service_feasibility": await self._feasibility_projection(updated, read_only=False),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def archive_feasibility(self, feasibility_id: str, user: dict) -> dict[str, Any]:
        existing = await self._require_feasibility(feasibility_id)
        now = self._now()
        updated = await self.db.collection(PASSENGER_SERVICE_FEASIBILITY_COLLECTION).update_one(
            {"id": existing["id"]},
            {
                "feasibility_status": "archived",
                "archived": True,
                "archived_at": now,
                "updated_by": user.get("id"),
                **self.safety_flags(),
            },
        )
        if not updated:
            raise PassengerServiceFeasibilityError("Passenger service feasibility metadata could not be archived.")
        return {
            "phase": PHASE_LABEL,
            "passenger_service_feasibility": await self._feasibility_projection(updated, read_only=False),
            "archived": True,
            "physical_delete_disabled": True,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "feasibility_count": len(items),
            "by_feasibility_status": self._counts(items, "feasibility_status", FEASIBILITY_STATUSES),
            "by_feasibility_type": self._counts(items, "feasibility_type", FEASIBILITY_TYPES),
            "by_feasibility_outcome": self._counts(items, "feasibility_outcome", FEASIBILITY_OUTCOMES),
            "by_feasibility_confidence": self._counts(items, "feasibility_confidence", FEASIBILITY_CONFIDENCE_LEVELS),
            "by_operational_risk": self._counts(items, "operational_risk_level", OPERATIONAL_RISK_LEVELS),
            "evidence_trace_count": sum(len(item.get("evidence_trace") or []) for item in items),
            "evaluation_trace_count": sum(len(item.get("evaluation_trace") or []) for item in items),
            "decision_trace_count": sum(len(item.get("decision_trace") or []) for item in items),
            "operational_evaluation_reference_count": sum(len(item.get("operational_evaluation_ids") or []) for item in items),
            "required_action_count": sum(
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
                for item in items
            ),
            "recommendation_ready_count": len([item for item in items if item.get("recommendation_ready")]),
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "agency_id": "agency_id exact metadata match",
            "feasibility_status": FEASIBILITY_STATUSES,
            "feasibility_type": FEASIBILITY_TYPES,
            "airline": "airline_code, airline_name, validating_carrier, operating_carrier, or marketing_carrier metadata match",
            "feasibility_outcome": FEASIBILITY_OUTCOMES,
            "confidence_level": FEASIBILITY_CONFIDENCE_LEVELS,
            "operational_risk": OPERATIONAL_RISK_LEVELS,
            "passenger_need_category": "passenger_need_category exact metadata match",
            "ssr_code": "required_ssrs metadata match",
            "travel_date": "travel_date exact metadata match",
            "cabin": "cabin_requested metadata match",
            "destination": "destination metadata match",
            "recommendation_ready": "metadata boolean",
            "metadata_only": True,
        }

    async def _feasibility_projection(self, item: dict[str, Any], *, read_only: bool) -> dict[str, Any]:
        projected = dict(item)
        projected["feasibility_display_name"] = projected.get("feasibility_reference") or projected.get("id")
        projected["evaluation_link_summary"] = self._evaluation_link_summary(projected)
        projected["requirement_summary"] = self._requirement_summary(projected)
        projected["action_summary"] = self._action_summary(projected)
        projected["risk_summary"] = self._risk_summary(projected)
        projected["confidence_summary"] = self._confidence_summary(projected)
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

    async def _require_feasibility(self, feasibility_id: str, *, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": feasibility_id}
        if agency_id:
            filters["agency_id"] = agency_id
        item = await self.db.collection(PASSENGER_SERVICE_FEASIBILITY_COLLECTION).find_one(filters)
        if not item:
            filters = {"feasibility_reference": feasibility_id}
            if agency_id:
                filters["agency_id"] = agency_id
            item = await self.db.collection(PASSENGER_SERVICE_FEASIBILITY_COLLECTION).find_one(filters)
        if not item:
            raise PassengerServiceFeasibilityError("Passenger service feasibility metadata was not found.")
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
        if data.get("feasibility_status") and data["feasibility_status"] not in FEASIBILITY_STATUSES:
            raise PassengerServiceFeasibilityError("Feasibility status must be known metadata.")
        if data.get("feasibility_type") and data["feasibility_type"] not in FEASIBILITY_TYPES:
            raise PassengerServiceFeasibilityError("Feasibility type must be known metadata.")
        if data.get("feasibility_outcome") and data["feasibility_outcome"] not in FEASIBILITY_OUTCOMES:
            raise PassengerServiceFeasibilityError("Feasibility outcome must be non-Boolean known metadata.")
        for field in ["feasibility_confidence", "data_confidence_level", "evidence_confidence_level", "operational_validation_confidence"]:
            if data.get(field) and data[field] not in FEASIBILITY_CONFIDENCE_LEVELS:
                raise PassengerServiceFeasibilityError(f"{field} must be a known confidence metadata value.")
        if data.get("operational_risk_level") and data["operational_risk_level"] not in OPERATIONAL_RISK_LEVELS:
            raise PassengerServiceFeasibilityError("Operational risk level must be known metadata.")
        if data.get("feasibility_ready") and not data.get("operational_evaluation_ids"):
            raise PassengerServiceFeasibilityError("Feasibility-ready metadata must reference Operational Evaluation Results.")
        has_trace = bool(data.get("evidence_trace") or data.get("evaluation_trace") or data.get("decision_trace"))
        if data.get("feasibility_status") == "completed" and not has_trace:
            raise PassengerServiceFeasibilityError("Completed feasibility metadata must include evidence, evaluation, or decision trace metadata.")
        if not partial and not data.get("feasibility_reference"):
            raise PassengerServiceFeasibilityError("Feasibility reference is required for feasibility metadata.")

    def _evaluation_link_summary(self, item: dict[str, Any]) -> dict[str, int]:
        return {
            "operational_evaluations": len(item.get("operational_evaluation_ids") or []),
            "capability_matrix_records": len(item.get("capability_matrix_ids") or []),
            "knowledge_versions": len(item.get("knowledge_version_ids") or []),
            "constraints": len(item.get("constraint_ids") or []),
            "evidence_references": len(item.get("evidence_reference_ids") or []),
        }

    def _requirement_summary(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "satisfied": len(item.get("satisfied_requirements") or []),
            "conditional": len(item.get("conditionally_satisfied_requirements") or []),
            "unsatisfied": len(item.get("unsatisfied_requirements") or []),
            "unknown": len(item.get("unknown_requirements") or []),
            "feasibility_is_not_boolean": True,
        }

    def _action_summary(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "required_ssrs": len(item.get("required_ssrs") or []),
            "required_osis": len(item.get("required_osis") or []),
            "required_emds": len(item.get("required_emds") or []),
            "required_documents": len(item.get("required_documents") or []),
            "required_medif": bool(item.get("required_medif")),
            "required_airline_approval": bool(item.get("required_airline_approval")),
            "required_station_notification": bool(item.get("required_station_notification")),
            "required_crew_notification": bool(item.get("required_crew_notification")),
            "required_manual_review": bool(item.get("required_manual_review")),
            "required_follow_up_tasks": len(item.get("required_follow_up_tasks") or []),
        }

    def _risk_summary(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "operational_risk_level": item.get("operational_risk_level"),
            "risk_reasons": len(item.get("operational_risk_reasons") or []),
            "adm_risk_relevance": item.get("adm_risk_relevance"),
            "disruption_risk_relevance": item.get("disruption_risk_relevance"),
            "service_failure_risk_relevance": item.get("service_failure_risk_relevance"),
        }

    def _confidence_summary(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "feasibility_confidence": item.get("feasibility_confidence"),
            "data_confidence_level": item.get("data_confidence_level"),
            "evidence_confidence_level": item.get("evidence_confidence_level"),
            "operational_validation_confidence": item.get("operational_validation_confidence"),
            "confidence_reason": item.get("confidence_reason"),
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

    def _feasibility_reference(self) -> str:
        return f"PSF-{new_id()[:8].upper()}"

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "passenger_service_feasibility_foundation": True,
            "feasibility_is_not_boolean": True,
            "explainable_feasibility": True,
            "evidence_linked": True,
            "advisory_only": True,
            "human_authority_final": True,
            "consumes_operational_evaluation_results": True,
            "no_ai_reasoning": True,
            "no_llm_prompts": True,
            "flight_search_disabled": True,
            "airline_recommendation_ranking_disabled": True,
            "recommendation_engine_disabled": True,
            "booking_disabled": True,
            "ticketing_disabled": True,
            "provider_integrations_disabled": True,
            "parser_execution_disabled": True,
            "pricing_optimisation_disabled": True,
            "background_workers_disabled": True,
            "automatic_operational_decisions_disabled": True,
        }
