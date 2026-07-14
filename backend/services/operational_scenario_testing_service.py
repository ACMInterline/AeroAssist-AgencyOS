from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import OperationalScenarioTest, OperationalScenarioTestCreate, OperationalScenarioTestUpdate


PHASE_LABEL = "phase_54_5_request_to_trip_operational_conversion_foundation"
OPERATIONAL_SCENARIO_TESTS_COLLECTION = "operational_scenario_tests"

SCENARIO_FAMILIES = [
    "petc",
    "avih",
    "svan",
    "exst_passenger_of_size",
    "cbbg",
    "wchc",
    "medif",
    "poc",
    "umnr",
    "musical_instrument",
    "sports_equipment",
    "restricted_equipment",
]

SCENARIO_TEST_STATUSES = ["draft", "ready_for_review", "reviewed", "approved", "needs_update", "archived"]
EXPECTED_RECOMMENDATION_LEVELS = [
    "highly_recommended",
    "recommended",
    "acceptable",
    "use_with_caution",
    "not_recommended",
    "not_applicable",
]


class OperationalScenarioTestingError(ValueError):
    pass


class OperationalScenarioTestingService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def platform_response(self, **filters: Any) -> dict[str, Any]:
        scenarios = await self.list_scenarios(**filters)
        return {
            "phase": PHASE_LABEL,
            "items": scenarios,
            "scenarios": scenarios,
            "summary": await self.summarize_counts(filters.get("agency_id")),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Operational Scenario Testing stores test-case metadata only. It does not run live providers, AI, parser execution, or automated evaluation.",
            **self.safety_flags(),
        }

    async def agency_response(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        scenarios = await self.list_scenarios(agency_id=agency_id, **filters)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": scenarios,
            "scenarios": scenarios,
            "summary": await self.summarize_counts(agency_id),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            "notice": "Agency Scenario Testing is read-only metadata for passenger service examples and expected outcomes.",
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
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def list_scenarios(
        self,
        *,
        agency_id: str | None = None,
        scenario_family: str | None = None,
        test_status: str | None = None,
        airline_code: str | None = None,
        service_code: str | None = None,
        expected_recommendation_level: str | None = None,
        search: str | None = None,
        include_archived: bool = False,
        **_: Any,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if scenario_family:
            filters["scenario_family"] = self._normalize_code(scenario_family)
        if test_status:
            filters["test_status"] = self._normalize_code(test_status)
        if expected_recommendation_level:
            filters["expected_recommendation_level"] = self._normalize_code(expected_recommendation_level)

        items = await self.db.collection(OPERATIONAL_SCENARIO_TESTS_COLLECTION).find_many(filters or None)
        if airline_code:
            normalized_airline = self._normalize_airline(airline_code)
            items = [
                item
                for item in items
                if self._normalize_airline((item.get("airline_context") or {}).get("airline_code")) == normalized_airline
            ]
        if service_code:
            normalized_service = self._normalize_code(service_code)
            items = [
                item
                for item in items
                if normalized_service
                in {self._normalize_code((requirement or {}).get("code")) for requirement in item.get("service_requirements") or []}
            ]
        if not include_archived:
            items = [item for item in items if not item.get("archived") and item.get("test_status") != "archived"]
        items = [
            item
            for item in items
            if self._any_field_matches(
                item,
                [
                    "scenario_reference",
                    "scenario_name",
                    "scenario_family",
                    "passenger_context",
                    "itinerary_context",
                    "airline_context",
                    "service_requirements",
                    "pets",
                    "special_items",
                    "documents",
                    "expected_policy_outcome",
                    "expected_pricing_behavior",
                    "expected_feasibility",
                    "expected_recommendation_level",
                    "expected_required_actions",
                    "evidence_links",
                    "review_notes",
                    "metadata",
                ],
                search,
            )
        ]
        items.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._scenario_projection(item) for item in items]

    async def get_scenario(self, scenario_id: str, agency_id: str | None = None) -> dict[str, Any]:
        item = await self._require_scenario(scenario_id, agency_id=agency_id)
        return await self._scenario_projection(item)

    async def create_scenario(
        self,
        payload: OperationalScenarioTestCreate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        if agency_id:
            data["agency_id"] = agency_id
        data = self._normalize_payload(data)
        data.setdefault("scenario_reference", self._reference("OST"))
        data.setdefault("test_status", "draft")
        data.update(self.safety_flags())
        self._validate_payload(data)
        record = OperationalScenarioTest(**data)
        created = await self.db.collection(OPERATIONAL_SCENARIO_TESTS_COLLECTION).insert_one(record.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "operational_scenario_test": await self._scenario_projection(created),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def update_scenario(
        self,
        scenario_id: str,
        payload: OperationalScenarioTestUpdate,
        user: dict,
    ) -> dict[str, Any]:
        existing = await self._require_scenario(scenario_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        updates = self._normalize_payload(updates)
        updates.update(self.safety_flags())
        self._validate_payload(updates, partial=True)
        updated = await self.db.collection(OPERATIONAL_SCENARIO_TESTS_COLLECTION).update_one({"id": existing["id"]}, updates)
        if not updated:
            raise OperationalScenarioTestingError("Operational scenario test metadata could not be updated.")
        return {
            "phase": PHASE_LABEL,
            "operational_scenario_test": await self._scenario_projection(updated),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def archive_scenario(self, scenario_id: str, user: dict) -> dict[str, Any]:
        existing = await self._require_scenario(scenario_id)
        updates = {
            "test_status": "archived",
            "archived": True,
            "archived_at": self._now(),
            **self.safety_flags(),
        }
        updated = await self.db.collection(OPERATIONAL_SCENARIO_TESTS_COLLECTION).update_one({"id": existing["id"]}, updates)
        if not updated:
            raise OperationalScenarioTestingError("Operational scenario test metadata could not be archived.")
        return {
            "phase": PHASE_LABEL,
            "operational_scenario_test": await self._scenario_projection(updated),
            "archived": True,
            "physical_delete_disabled": True,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def summarize_counts(self, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"agency_id": agency_id} if agency_id else None
        scenarios = await self.db.collection(OPERATIONAL_SCENARIO_TESTS_COLLECTION).find_many(filters)
        active = [item for item in scenarios if not item.get("archived") and item.get("test_status") != "archived"]
        return {
            "operational_scenario_test_count": len(scenarios),
            "active_scenario_test_count": len(active),
            "scenario_family_counts": self._counts(scenarios, "scenario_family", SCENARIO_FAMILIES),
            "test_status_counts": self._counts(scenarios, "test_status", SCENARIO_TEST_STATUSES),
            "expected_recommendation_level_counts": self._counts(
                scenarios,
                "expected_recommendation_level",
                EXPECTED_RECOMMENDATION_LEVELS,
            ),
            "service_requirement_count": sum(len(item.get("service_requirements") or []) for item in scenarios),
            "pet_case_count": len([item for item in scenarios if item.get("pets")]),
            "special_item_case_count": len([item for item in scenarios if item.get("special_items")]),
            "document_count": sum(len(item.get("documents") or []) for item in scenarios),
            "expected_required_action_count": sum(len(item.get("expected_required_actions") or []) for item in scenarios),
            "evidence_link_count": sum(len(item.get("evidence_links") or []) for item in scenarios),
            "supported_scenario_family_count": len(SCENARIO_FAMILIES),
            "supported_test_status_count": len(SCENARIO_TEST_STATUSES),
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "scenario_family": SCENARIO_FAMILIES,
            "test_status": SCENARIO_TEST_STATUSES,
            "expected_recommendation_level": EXPECTED_RECOMMENDATION_LEVELS,
            "airline_code": "airline_context.airline_code metadata match",
            "service_code": "service_requirements.code metadata match",
            "search": "reference, name, family, contexts, expected outcomes, actions, evidence, notes, or metadata",
            "metadata_only": True,
        }

    async def _scenario_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        projected["scenario_display_name"] = " / ".join(
            part for part in [projected.get("scenario_reference"), projected.get("scenario_name"), projected.get("scenario_family")] if part
        )
        projected["scenario_section"] = {
            "scenario_reference": projected.get("scenario_reference"),
            "scenario_name": projected.get("scenario_name"),
            "scenario_family": projected.get("scenario_family"),
            "test_status": projected.get("test_status"),
        }
        projected["passenger_context_section"] = {
            "passenger_context": projected.get("passenger_context") or {},
            "pets": projected.get("pets") or [],
            "special_items": projected.get("special_items") or [],
            "documents": projected.get("documents") or [],
        }
        projected["operational_context_section"] = {
            "itinerary_context": projected.get("itinerary_context") or {},
            "airline_context": projected.get("airline_context") or {},
            "service_requirements": projected.get("service_requirements") or [],
        }
        projected["expected_outcome_section"] = {
            "expected_policy_outcome": projected.get("expected_policy_outcome") or {},
            "expected_pricing_behavior": projected.get("expected_pricing_behavior") or {},
            "expected_feasibility": projected.get("expected_feasibility") or {},
            "expected_recommendation_level": projected.get("expected_recommendation_level"),
            "expected_required_actions": projected.get("expected_required_actions") or [],
        }
        projected["evidence_section"] = {
            "evidence_links": projected.get("evidence_links") or [],
            "evidence_link_count": len(projected.get("evidence_links") or []),
        }
        projected["review_section"] = {
            "review_notes": projected.get("review_notes"),
            "created_at": projected.get("created_at"),
            "updated_at": projected.get("updated_at"),
            "archived": projected.get("archived"),
            "archived_at": projected.get("archived_at"),
        }
        projected["boundary_section"] = self.safety_flags()
        projected.update(self.safety_flags())
        return projected

    async def _require_scenario(self, scenario_id: str, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": scenario_id}
        if agency_id:
            filters["agency_id"] = agency_id
        item = await self.db.collection(OPERATIONAL_SCENARIO_TESTS_COLLECTION).find_one(filters)
        if not item:
            filters = {"scenario_reference": scenario_id}
            if agency_id:
                filters["agency_id"] = agency_id
            item = await self.db.collection(OPERATIONAL_SCENARIO_TESTS_COLLECTION).find_one(filters)
        if not item:
            raise OperationalScenarioTestingError("Operational scenario test metadata not found.")
        return item

    def _normalize_payload(self, data: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(data)
        for field in ["scenario_family", "test_status", "expected_recommendation_level"]:
            if field in normalized and normalized[field] is not None:
                normalized[field] = self._normalize_code(normalized[field])
        if "airline_context" in normalized and isinstance(normalized.get("airline_context"), dict):
            airline_context = dict(normalized["airline_context"])
            if airline_context.get("airline_code") is not None:
                airline_context["airline_code"] = self._normalize_airline(airline_context.get("airline_code"))
            normalized["airline_context"] = airline_context
        return normalized

    def _validate_payload(self, data: dict[str, Any], *, partial: bool = False) -> None:
        self._validate_choice(data, "scenario_family", SCENARIO_FAMILIES)
        self._validate_choice(data, "test_status", SCENARIO_TEST_STATUSES)
        self._validate_choice(data, "expected_recommendation_level", EXPECTED_RECOMMENDATION_LEVELS)
        self._reject_forbidden_metadata(data)
        if not partial:
            for field in ["scenario_name", "scenario_family"]:
                if not data.get(field):
                    raise OperationalScenarioTestingError(f"{field} is required.")

    def _validate_choice(self, data: dict[str, Any], field: str, allowed: list[str]) -> None:
        if field not in data or data.get(field) is None:
            return
        if data[field] not in allowed:
            raise OperationalScenarioTestingError(f"Unsupported {field} metadata value: {data[field]}.")

    def _reject_forbidden_metadata(self, data: dict[str, Any]) -> None:
        forbidden = [
            "live_provider_enabled",
            "provider_client",
            "call_provider",
            "live_gds",
            "live_ndc",
            "ai_prompt",
            "llm_prompt",
            "chatcompletion",
            "background_task",
            "backgroundtasks",
            "auto_evaluate",
            "execute_scenario",
            "run_live_test",
            "booking_provider",
            "ticketing_provider",
        ]
        serialized = str(data).lower()
        for marker in forbidden:
            if marker in serialized:
                raise OperationalScenarioTestingError(f"Forbidden non-metadata implementation marker present: {marker}.")

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "operational_scenario_testing_foundation": True,
            "scenario_execution_disabled": True,
            "live_provider_execution_disabled": True,
            "ai_disabled": True,
            "automated_test_execution_disabled": True,
            "provider_integrations_disabled": True,
            "background_workers_disabled": True,
            "human_authority_final": True,
        }

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
