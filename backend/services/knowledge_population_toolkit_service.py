from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import KnowledgePopulationToolkit, KnowledgePopulationToolkitCreate, KnowledgePopulationToolkitUpdate


PHASE_LABEL = "phase_54_2_agent_work_queue_assignment_foundation"
KNOWLEDGE_POPULATION_TOOLKITS_COLLECTION = "knowledge_population_toolkits"

POPULATION_STATUSES = [
    "draft",
    "onboarding",
    "reference_readiness",
    "template_readiness",
    "content_population",
    "qa_review",
    "publishing_readiness",
    "scenario_review",
    "ready",
    "blocked",
    "archived",
]

TOOLKIT_READINESS_STATUSES = ["not_started", "in_progress", "ready", "needs_review", "blocked", "not_applicable"]


class KnowledgePopulationToolkitError(ValueError):
    pass


class KnowledgePopulationToolkitService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def platform_response(self, **filters: Any) -> dict[str, Any]:
        toolkits = await self.list_toolkits(**filters)
        return {
            "phase": PHASE_LABEL,
            "items": toolkits,
            "toolkits": toolkits,
            "summary": await self.summarize_counts(filters.get("agency_id")),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Knowledge Population Toolkit stores readiness, coverage, progress, and next-action metadata only. It does not scrape, auto-import, call providers, run AI, or execute population jobs.",
            **self.safety_flags(),
        }

    async def agency_response(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        toolkits = await self.list_toolkits(agency_id=agency_id, **filters)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": toolkits,
            "toolkits": toolkits,
            "summary": await self.summarize_counts(agency_id),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            "notice": "Agency Knowledge Population Toolkit is read-only metadata for airline knowledge population readiness and coverage.",
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

    async def list_toolkits(
        self,
        *,
        agency_id: str | None = None,
        airline_code: str | None = None,
        population_status: str | None = None,
        QA_status: str | None = None,
        publishing_status: str | None = None,
        scenario_test_status: str | None = None,
        owner: str | None = None,
        search: str | None = None,
        include_archived: bool = False,
        **_: Any,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if airline_code:
            filters["airline_code"] = self._normalize_airline(airline_code)
        if population_status:
            filters["population_status"] = self._normalize_code(population_status)
        if QA_status:
            filters["QA_status"] = self._normalize_code(QA_status)
        if publishing_status:
            filters["publishing_status"] = self._normalize_code(publishing_status)
        if scenario_test_status:
            filters["scenario_test_status"] = self._normalize_code(scenario_test_status)
        if owner:
            filters["owner"] = owner

        items = await self.db.collection(KNOWLEDGE_POPULATION_TOOLKITS_COLLECTION).find_many(filters or None)
        if not include_archived:
            items = [item for item in items if not item.get("archived") and item.get("population_status") != "archived"]
        items = [
            item
            for item in items
            if self._any_field_matches(
                item,
                [
                    "toolkit_reference",
                    "airline_code",
                    "population_status",
                    "coverage_summary",
                    "service_family_coverage",
                    "evidence_coverage",
                    "pricing_coverage",
                    "capability_coverage",
                    "QA_status",
                    "publishing_status",
                    "scenario_test_status",
                    "missing_domains",
                    "blockers",
                    "warnings",
                    "next_actions",
                    "owner",
                    "due_dates",
                    "notes",
                    "metadata",
                ],
                search,
            )
        ]
        items.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._toolkit_projection(item) for item in items]

    async def get_toolkit(self, toolkit_id: str, agency_id: str | None = None) -> dict[str, Any]:
        item = await self._require_toolkit(toolkit_id, agency_id=agency_id)
        return await self._toolkit_projection(item)

    async def create_toolkit(
        self,
        payload: KnowledgePopulationToolkitCreate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        if agency_id:
            data["agency_id"] = agency_id
        data = self._normalize_payload(data)
        data.setdefault("toolkit_reference", self._reference("KPT"))
        data.setdefault("population_status", "draft")
        data.update(self.safety_flags())
        self._validate_payload(data)
        record = KnowledgePopulationToolkit(**data)
        created = await self.db.collection(KNOWLEDGE_POPULATION_TOOLKITS_COLLECTION).insert_one(record.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "knowledge_population_toolkit": await self._toolkit_projection(created),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def update_toolkit(
        self,
        toolkit_id: str,
        payload: KnowledgePopulationToolkitUpdate,
        user: dict,
    ) -> dict[str, Any]:
        existing = await self._require_toolkit(toolkit_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        updates = self._normalize_payload(updates)
        updates.update(self.safety_flags())
        self._validate_payload(updates, partial=True)
        updated = await self.db.collection(KNOWLEDGE_POPULATION_TOOLKITS_COLLECTION).update_one({"id": existing["id"]}, updates)
        if not updated:
            raise KnowledgePopulationToolkitError("Knowledge population toolkit metadata could not be updated.")
        return {
            "phase": PHASE_LABEL,
            "knowledge_population_toolkit": await self._toolkit_projection(updated),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def archive_toolkit(self, toolkit_id: str, user: dict) -> dict[str, Any]:
        existing = await self._require_toolkit(toolkit_id)
        updates = {
            "population_status": "archived",
            "archived": True,
            "archived_at": self._now(),
            **self.safety_flags(),
        }
        updated = await self.db.collection(KNOWLEDGE_POPULATION_TOOLKITS_COLLECTION).update_one({"id": existing["id"]}, updates)
        if not updated:
            raise KnowledgePopulationToolkitError("Knowledge population toolkit metadata could not be archived.")
        return {
            "phase": PHASE_LABEL,
            "knowledge_population_toolkit": await self._toolkit_projection(updated),
            "archived": True,
            "physical_delete_disabled": True,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def summarize_counts(self, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"agency_id": agency_id} if agency_id else None
        toolkits = await self.db.collection(KNOWLEDGE_POPULATION_TOOLKITS_COLLECTION).find_many(filters)
        active = [item for item in toolkits if not item.get("archived") and item.get("population_status") != "archived"]
        return {
            "knowledge_population_toolkit_count": len(toolkits),
            "active_toolkit_count": len(active),
            "population_status_counts": self._counts(toolkits, "population_status", POPULATION_STATUSES),
            "QA_status_counts": self._counts(toolkits, "QA_status", TOOLKIT_READINESS_STATUSES),
            "publishing_status_counts": self._counts(toolkits, "publishing_status", TOOLKIT_READINESS_STATUSES),
            "scenario_test_status_counts": self._counts(toolkits, "scenario_test_status", TOOLKIT_READINESS_STATUSES),
            "service_family_coverage_count": sum(len(item.get("service_family_coverage") or []) for item in toolkits),
            "missing_domain_count": sum(len(item.get("missing_domains") or []) for item in toolkits),
            "blocker_count": sum(len(item.get("blockers") or []) for item in toolkits),
            "warning_count": sum(len(item.get("warnings") or []) for item in toolkits),
            "next_action_count": sum(len(item.get("next_actions") or []) for item in toolkits),
            "due_date_count": sum(len(item.get("due_dates") or []) for item in toolkits),
            "supported_population_status_count": len(POPULATION_STATUSES),
            "supported_readiness_status_count": len(TOOLKIT_READINESS_STATUSES),
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "airline_code": "IATA airline code metadata match",
            "population_status": POPULATION_STATUSES,
            "QA_status": TOOLKIT_READINESS_STATUSES,
            "publishing_status": TOOLKIT_READINESS_STATUSES,
            "scenario_test_status": TOOLKIT_READINESS_STATUSES,
            "owner": "metadata owner exact match",
            "search": "reference, airline, coverage, readiness, blockers, warnings, next actions, owner, due dates, notes, or metadata",
            "metadata_only": True,
        }

    async def _toolkit_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        projected["toolkit_display_name"] = " / ".join(
            part for part in [projected.get("toolkit_reference"), projected.get("airline_code"), projected.get("population_status")] if part
        )
        projected["toolkit_section"] = {
            "toolkit_reference": projected.get("toolkit_reference"),
            "airline_code": projected.get("airline_code"),
            "population_status": projected.get("population_status"),
            "owner": projected.get("owner"),
        }
        projected["readiness_section"] = {
            "airline_onboarding_checklist": projected.get("airline_onboarding_checklist") or [],
            "reference_readiness": projected.get("reference_readiness") or {},
            "import_template_readiness": projected.get("import_template_readiness") or {},
            "policy_editor_readiness": projected.get("policy_editor_readiness") or {},
            "pricing_builder_readiness": projected.get("pricing_builder_readiness") or {},
            "rule_composer_readiness": projected.get("rule_composer_readiness") or {},
            "qa_readiness": projected.get("qa_readiness") or {},
            "publishing_readiness": projected.get("publishing_readiness") or {},
            "scenario_test_readiness": projected.get("scenario_test_readiness") or {},
        }
        projected["coverage_section"] = {
            "coverage_summary": projected.get("coverage_summary") or {},
            "service_family_coverage": projected.get("service_family_coverage") or [],
            "evidence_coverage": projected.get("evidence_coverage") or {},
            "pricing_coverage": projected.get("pricing_coverage") or {},
            "capability_coverage": projected.get("capability_coverage") or {},
            "population_progress": projected.get("population_progress") or {},
            "missing_domains": projected.get("missing_domains") or [],
        }
        projected["quality_release_section"] = {
            "QA_status": projected.get("QA_status"),
            "publishing_status": projected.get("publishing_status"),
            "scenario_test_status": projected.get("scenario_test_status"),
        }
        projected["actions_section"] = {
            "blockers": projected.get("blockers") or [],
            "warnings": projected.get("warnings") or [],
            "next_actions": projected.get("next_actions") or [],
            "due_dates": projected.get("due_dates") or [],
            "notes": projected.get("notes"),
        }
        projected["review_section"] = {
            "created_at": projected.get("created_at"),
            "updated_at": projected.get("updated_at"),
            "archived": projected.get("archived"),
            "archived_at": projected.get("archived_at"),
        }
        projected["boundary_section"] = self.safety_flags()
        projected.update(self.safety_flags())
        return projected

    async def _require_toolkit(self, toolkit_id: str, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": toolkit_id}
        if agency_id:
            filters["agency_id"] = agency_id
        item = await self.db.collection(KNOWLEDGE_POPULATION_TOOLKITS_COLLECTION).find_one(filters)
        if not item:
            filters = {"toolkit_reference": toolkit_id}
            if agency_id:
                filters["agency_id"] = agency_id
            item = await self.db.collection(KNOWLEDGE_POPULATION_TOOLKITS_COLLECTION).find_one(filters)
        if not item:
            raise KnowledgePopulationToolkitError("Knowledge population toolkit metadata not found.")
        return item

    def _normalize_payload(self, data: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(data)
        for field in ["population_status", "QA_status", "publishing_status", "scenario_test_status"]:
            if field in normalized and normalized[field] is not None:
                normalized[field] = self._normalize_code(normalized[field])
        if "airline_code" in normalized and normalized.get("airline_code") is not None:
            normalized["airline_code"] = self._normalize_airline(normalized.get("airline_code"))
        return normalized

    def _validate_payload(self, data: dict[str, Any], *, partial: bool = False) -> None:
        self._validate_choice(data, "population_status", POPULATION_STATUSES)
        self._validate_choice(data, "QA_status", TOOLKIT_READINESS_STATUSES)
        self._validate_choice(data, "publishing_status", TOOLKIT_READINESS_STATUSES)
        self._validate_choice(data, "scenario_test_status", TOOLKIT_READINESS_STATUSES)
        self._reject_forbidden_metadata(data)
        if not partial and not data.get("airline_code"):
            raise KnowledgePopulationToolkitError("airline_code is required.")

    def _validate_choice(self, data: dict[str, Any], field: str, allowed: list[str]) -> None:
        if field not in data or data.get(field) is None:
            return
        if data[field] not in allowed:
            raise KnowledgePopulationToolkitError(f"Unsupported {field} metadata value: {data[field]}.")

    def _reject_forbidden_metadata(self, data: dict[str, Any]) -> None:
        forbidden = [
            "scrape_enabled",
            "crawler_enabled",
            "auto_import_enabled",
            "automatic_import_enabled",
            "provider_client",
            "call_provider",
            "ai_prompt",
            "llm_prompt",
            "chatcompletion",
            "background_task",
            "backgroundtasks",
            "import_runner",
            "execute_population",
            "run_population_job",
        ]
        serialized = str(data).lower()
        for marker in forbidden:
            if marker in serialized:
                raise KnowledgePopulationToolkitError(f"Forbidden non-metadata implementation marker present: {marker}.")

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "knowledge_population_toolkit_foundation": True,
            "scraping_disabled": True,
            "auto_import_disabled": True,
            "ai_disabled": True,
            "provider_integrations_disabled": True,
            "background_workers_disabled": True,
            "population_execution_disabled": True,
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
