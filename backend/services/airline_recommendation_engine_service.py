from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import AirlineRecommendation, AirlineRecommendationCreate, AirlineRecommendationUpdate, new_id


PHASE_LABEL = "phase_55_3_airline_knowledge_versioning_change_detection_foundation"
AIRLINE_RECOMMENDATION_COLLECTION = "airline_recommendations"

AIRLINE_RECOMMENDATION_STATUSES = ["draft", "in_review", "ready", "archived"]
RECOMMENDATION_STATUS_VALUES = ["candidate", "preferred", "backup", "use_with_caution", "not_recommended"]
AIRLINE_RECOMMENDATION_LEVELS = [
    "highly_recommended",
    "recommended",
    "acceptable",
    "use_with_caution",
    "not_recommended",
]
SCORE_FIELDS = [
    "operational_feasibility_score",
    "operational_confidence_score",
    "operational_risk_score",
    "passenger_comfort_score",
    "operational_complexity_score",
    "ancillary_cost_score",
    "recommendation_score",
]


class AirlineRecommendationError(ValueError):
    pass


class AirlineRecommendationService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def platform_response(self, **filters: Any) -> dict[str, Any]:
        recommendations = await self.list_platform_recommendations(**filters)
        return {
            "phase": PHASE_LABEL,
            "items": recommendations,
            "recommendations": recommendations,
            "summary": self.summarize_counts(recommendations),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Airline Recommendations are advisory metadata. Recommendation is not feasibility, booking, provider search, pricing generation, or final authority.",
            **self.safety_flags(),
        }

    async def agency_response(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        recommendations = await self.list_agency_recommendations(agency_id, **filters)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": recommendations,
            "recommendations": recommendations,
            "summary": self.summarize_counts(recommendations),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            "notice": "Agency Recommendations are read-only advisory metadata. They do not search, book, ticket, call providers, or generate prices.",
            **self.safety_flags(),
        }

    async def platform_summary(self) -> dict[str, Any]:
        recommendations = await self.list_platform_recommendations()
        return {
            "phase": PHASE_LABEL,
            "summary": self.summarize_counts(recommendations),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        recommendations = await self.list_agency_recommendations(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(recommendations),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def list_platform_recommendations(
        self,
        *,
        agency_id: str | None = None,
        recommendation_status: str | None = None,
        airline: str | None = None,
        recommendation_level: str | None = None,
        operational_score: float | None = None,
        risk: float | None = None,
        passenger_need_category: str | None = None,
        cabin: str | None = None,
        destination: str | None = None,
        travel_date: str | None = None,
        include_archived: bool = False,
        **_: Any,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if recommendation_status:
            filters["recommendation_status"] = recommendation_status
        if recommendation_level:
            filters["recommendation_level"] = recommendation_level
        if passenger_need_category:
            filters["passenger_need_category"] = passenger_need_category
        if travel_date:
            filters["travel_date"] = travel_date

        items = await self.db.collection(AIRLINE_RECOMMENDATION_COLLECTION).find_many(filters or None)
        if not include_archived:
            items = [item for item in items if not item.get("archived") and item.get("recommendation_status") != "archived"]
        items = [
            item
            for item in items
            if self._any_field_matches(item, ["airline_code", "airline_name", "validating_carrier", "operating_carrier", "marketing_carrier"], airline)
            and self._any_field_matches(item, ["cabin_requested"], cabin)
            and self._any_field_matches(item, ["destination"], destination)
            and self._score_at_least(item.get("operational_feasibility_score"), operational_score)
            and self._score_at_most(item.get("operational_risk_score"), risk)
        ]
        items.sort(
            key=lambda item: (
                item.get("recommendation_rank") if item.get("recommendation_rank") is not None else 999999,
                -float(item.get("recommendation_score") or 0),
                self._sort_text(item.get("updated_at") or item.get("created_at")),
            )
        )
        return [await self._recommendation_projection(item, read_only=False) for item in items]

    async def list_agency_recommendations(self, agency_id: str, **filters: Any) -> list[dict[str, Any]]:
        items = await self.list_platform_recommendations(agency_id=agency_id, **filters)
        return [self._agency_projection(item) for item in items if item.get("agency_id") == agency_id]

    async def get_platform_recommendation(self, recommendation_id: str) -> dict[str, Any]:
        item = await self._require_recommendation(recommendation_id)
        return await self._recommendation_projection(item, read_only=False)

    async def get_agency_recommendation(self, agency_id: str, recommendation_id: str) -> dict[str, Any]:
        item = await self._require_recommendation(recommendation_id, agency_id=agency_id)
        return self._agency_projection(await self._recommendation_projection(item, read_only=True))

    async def create_recommendation(self, payload: AirlineRecommendationCreate, user: dict) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        data.setdefault("recommendation_reference", self._recommendation_reference())
        data.setdefault("recommendation_status", "draft")
        self._validate_payload(data)
        data.setdefault("created_by", user.get("id"))
        data["updated_by"] = user.get("id")
        data.update(self.safety_flags())
        record = AirlineRecommendation(**data)
        created = await self.db.collection(AIRLINE_RECOMMENDATION_COLLECTION).insert_one(record.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "airline_recommendation": await self._recommendation_projection(created, read_only=False),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def update_recommendation(self, recommendation_id: str, payload: AirlineRecommendationUpdate, user: dict) -> dict[str, Any]:
        existing = await self._require_recommendation(recommendation_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        self._validate_payload(updates, partial=True)
        updates["updated_by"] = user.get("id")
        updates.update(self.safety_flags())
        updated = await self.db.collection(AIRLINE_RECOMMENDATION_COLLECTION).update_one({"id": existing["id"]}, updates)
        if not updated:
            raise AirlineRecommendationError("Airline recommendation metadata could not be updated.")
        return {
            "phase": PHASE_LABEL,
            "airline_recommendation": await self._recommendation_projection(updated, read_only=False),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def archive_recommendation(self, recommendation_id: str, user: dict) -> dict[str, Any]:
        existing = await self._require_recommendation(recommendation_id)
        now = self._now()
        updated = await self.db.collection(AIRLINE_RECOMMENDATION_COLLECTION).update_one(
            {"id": existing["id"]},
            {
                "recommendation_status": "archived",
                "archived": True,
                "archived_at": now,
                "updated_by": user.get("id"),
                **self.safety_flags(),
            },
        )
        if not updated:
            raise AirlineRecommendationError("Airline recommendation metadata could not be archived.")
        return {
            "phase": PHASE_LABEL,
            "airline_recommendation": await self._recommendation_projection(updated, read_only=False),
            "archived": True,
            "physical_delete_disabled": True,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "recommendation_count": len(items),
            "by_recommendation_status": self._counts(items, "recommendation_status", AIRLINE_RECOMMENDATION_STATUSES),
            "by_recommendation_level": self._counts(items, "recommendation_level", AIRLINE_RECOMMENDATION_LEVELS),
            "by_recommendation_status_value": self._counts(items, "recommendation_status_value", RECOMMENDATION_STATUS_VALUES),
            "recommendation_ready_count": len([item for item in items if item.get("recommendation_ready")]),
            "feasibility_reference_count": sum(len(item.get("feasibility_ids") or []) for item in items),
            "comparison_matrix_count": sum(len(item.get("comparison_matrix") or []) for item in items),
            "recommendation_evidence_count": sum(len(item.get("recommendation_evidence") or []) for item in items),
            "recommendation_trace_count": sum(len(item.get("recommendation_trace") or []) for item in items),
            "required_action_count": sum(
                len(item.get("required_ssrs") or [])
                + len(item.get("required_osis") or [])
                + len(item.get("required_emds") or [])
                + len(item.get("required_documents") or [])
                + int(bool(item.get("required_medif")))
                + int(bool(item.get("required_manual_review")))
                + int(bool(item.get("required_station_notification")))
                + int(bool(item.get("required_crew_notification")))
                for item in items
            ),
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "agency_id": "agency_id exact metadata match",
            "recommendation_status": AIRLINE_RECOMMENDATION_STATUSES,
            "airline": "airline_code, airline_name, validating_carrier, operating_carrier, or marketing_carrier metadata match",
            "recommendation_level": AIRLINE_RECOMMENDATION_LEVELS,
            "operational_score": "minimum operational_feasibility_score metadata threshold",
            "risk": "maximum operational_risk_score metadata threshold",
            "passenger_need_category": "passenger_need_category exact metadata match",
            "cabin": "cabin_requested metadata match",
            "destination": "destination metadata match",
            "travel_date": "travel_date exact metadata match",
            "metadata_only": True,
        }

    async def _recommendation_projection(self, item: dict[str, Any], *, read_only: bool) -> dict[str, Any]:
        projected = dict(item)
        projected["recommendation_display_name"] = projected.get("recommendation_reference") or projected.get("id")
        projected["input_reference_summary"] = self._input_reference_summary(projected)
        projected["score_summary"] = self._score_summary(projected)
        projected["action_summary"] = self._action_summary(projected)
        projected["comparison_metadata_summary"] = self._comparison_metadata_summary(projected)
        projected["evidence_summary"] = self._evidence_summary(projected)
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

    async def _require_recommendation(self, recommendation_id: str, *, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": recommendation_id}
        if agency_id:
            filters["agency_id"] = agency_id
        item = await self.db.collection(AIRLINE_RECOMMENDATION_COLLECTION).find_one(filters)
        if not item:
            filters = {"recommendation_reference": recommendation_id}
            if agency_id:
                filters["agency_id"] = agency_id
            item = await self.db.collection(AIRLINE_RECOMMENDATION_COLLECTION).find_one(filters)
        if not item:
            raise AirlineRecommendationError("Airline recommendation metadata was not found.")
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
        if data.get("recommendation_status") and data["recommendation_status"] not in AIRLINE_RECOMMENDATION_STATUSES:
            raise AirlineRecommendationError("Recommendation status must be known metadata.")
        if data.get("recommendation_status_value") and data["recommendation_status_value"] not in RECOMMENDATION_STATUS_VALUES:
            raise AirlineRecommendationError("Recommendation status value must be known metadata.")
        if data.get("recommendation_level") and data["recommendation_level"] not in AIRLINE_RECOMMENDATION_LEVELS:
            raise AirlineRecommendationError("Recommendation level must be supported metadata.")
        for field in SCORE_FIELDS:
            if data.get(field) is not None:
                score = float(data[field])
                if score < 0 or score > 100:
                    raise AirlineRecommendationError(f"{field} must be a metadata score between 0 and 100.")
        if data.get("recommendation_ready") and not data.get("feasibility_ids"):
            raise AirlineRecommendationError("Recommendation-ready metadata must reference Passenger Service Feasibility records.")
        if data.get("recommendation_status") == "ready" and not (data.get("recommendation_evidence") or data.get("recommendation_trace")):
            raise AirlineRecommendationError("Ready recommendation metadata must include evidence or trace metadata.")
        if not partial and not data.get("recommendation_reference"):
            raise AirlineRecommendationError("Recommendation reference is required for recommendation metadata.")

    def _input_reference_summary(self, item: dict[str, Any]) -> dict[str, int]:
        return {
            "feasibilities": len(item.get("feasibility_ids") or []),
            "operational_evaluations": len(item.get("operational_evaluation_ids") or []),
            "capability_matrix_records": len(item.get("capability_matrix_ids") or []),
            "knowledge_versions": len(item.get("knowledge_version_ids") or []),
            "evidence_references": len(item.get("evidence_reference_ids") or []),
        }

    def _score_summary(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            field: item.get(field)
            for field in SCORE_FIELDS
        }

    def _action_summary(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "required_ssrs": len(item.get("required_ssrs") or []),
            "required_osis": len(item.get("required_osis") or []),
            "required_emds": len(item.get("required_emds") or []),
            "required_documents": len(item.get("required_documents") or []),
            "required_medif": bool(item.get("required_medif")),
            "required_manual_review": bool(item.get("required_manual_review")),
            "required_station_notification": bool(item.get("required_station_notification")),
            "required_crew_notification": bool(item.get("required_crew_notification")),
        }

    def _comparison_metadata_summary(self, item: dict[str, Any]) -> dict[str, int]:
        return {
            "compared_airlines": len(item.get("compared_airlines") or []),
            "compared_itineraries": len(item.get("compared_itineraries") or []),
            "comparison_rows": len(item.get("comparison_matrix") or []),
        }

    def _evidence_summary(self, item: dict[str, Any]) -> dict[str, int]:
        return {
            "recommendation_evidence": len(item.get("recommendation_evidence") or []),
            "recommendation_trace": len(item.get("recommendation_trace") or []),
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

    def _score_at_least(self, candidate: Any, value: float | None) -> bool:
        if value is None:
            return True
        if candidate is None:
            return False
        return float(candidate) >= float(value)

    def _score_at_most(self, candidate: Any, value: float | None) -> bool:
        if value is None:
            return True
        if candidate is None:
            return False
        return float(candidate) <= float(value)

    def _sort_text(self, value: Any) -> str:
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value or "")

    def _recommendation_reference(self) -> str:
        return f"ARE-{new_id()[:8].upper()}"

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "airline_recommendation_engine_foundation": True,
            "recommendation_is_not_feasibility": True,
            "consumes_passenger_service_feasibility": True,
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
        }
