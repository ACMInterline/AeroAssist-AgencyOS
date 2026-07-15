from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import OperationalConstraint, OperationalConstraintCreate, OperationalConstraintUpdate, new_id


PHASE_LABEL = "phase_56_1_journey_segment_authoring_intelligent_import_workspace_foundation"
OPERATIONAL_CONSTRAINT_COLLECTION = "operational_constraints"

CONSTRAINT_STATUSES = [
    "draft",
    "captured",
    "in_review",
    "approved",
    "rejected",
    "superseded",
    "archived",
]

CONDITION_OPERATORS = [
    "equals",
    "not_equals",
    "contains",
    "not_contains",
    "greater_than",
    "less_than",
    "greater_than_or_equal",
    "less_than_or_equal",
    "in",
    "not_in",
    "between",
    "exists",
    "not_exists",
]

OUTCOME_TYPES = [
    "allowed",
    "not_allowed",
    "approval_required",
    "document_required",
    "emd_required",
    "manual_review_required",
    "embargo",
    "restriction_applies",
    "pricing_rule_applies",
    "refund_condition_applies",
    "capability_available",
    "capability_unavailable",
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


class OperationalConstraintEngineError(ValueError):
    pass


class OperationalConstraintEngineService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_platform_constraints(
        self,
        *,
        agency_id: str | None = None,
        acquisition_id: str | None = None,
        airline: str | None = None,
        service_domain: str | None = None,
        service_family: str | None = None,
        ssr_code: str | None = None,
        rfic: str | None = None,
        rfisc: str | None = None,
        constraint_status: str | None = None,
        outcome_type: str | None = None,
        review_status: str | None = None,
        approval_status: str | None = None,
        evaluation_ready: bool | None = None,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if acquisition_id:
            filters["acquisition_id"] = acquisition_id
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
        if constraint_status:
            filters["constraint_status"] = constraint_status
        if outcome_type:
            filters["outcome_type"] = outcome_type
        if review_status:
            filters["review_status"] = review_status
        if approval_status:
            filters["approval_status"] = approval_status
        if evaluation_ready is not None:
            filters["evaluation_ready"] = evaluation_ready

        items = await self.db.collection(OPERATIONAL_CONSTRAINT_COLLECTION).find_many(filters or None)
        if not include_archived:
            items = [
                item
                for item in items
                if not item.get("deleted_at") and item.get("constraint_status") != "archived"
            ]
        items = self._filter_airline(items, airline)
        items.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._platform_projection(item) for item in items]

    async def list_agency_constraints(self, agency_id: str, **filters: Any) -> list[dict[str, Any]]:
        items = await self.list_platform_constraints(agency_id=agency_id, **filters)
        return [self._agency_projection(item) for item in items if item.get("agency_id") == agency_id]

    async def platform_response(self, **filters: Any) -> dict[str, Any]:
        items = await self.list_platform_constraints(**filters)
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "operational_constraint_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Operational Constraints define the future AOIE constraint language as metadata only. Phase 50.2 does not run live rule execution, AI reasoning, recommendations, feasibility scoring, pricing calculation, parser execution, scraping, workers, or providers.",
            **self.safety_flags(),
        }

    async def agency_response(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        items = await self.list_agency_constraints(agency_id, **filters)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "operational_constraint_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            "notice": "Agency Operational Constraints are read-only metadata. They are not evaluated and do not trigger feasibility, recommendations, pricing, parsing, providers, workers, or automation.",
            **self.safety_flags(),
        }

    async def platform_summary(self) -> dict[str, Any]:
        items = await self.list_platform_constraints()
        return {
            "phase": PHASE_LABEL,
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        items = await self.list_agency_constraints(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def get_platform_constraint(self, constraint_id: str) -> dict[str, Any]:
        item = await self._require_constraint(constraint_id)
        return await self._platform_projection(item)

    async def get_agency_constraint(self, agency_id: str, constraint_id: str) -> dict[str, Any]:
        item = await self._require_constraint(constraint_id, agency_id=agency_id)
        return self._agency_projection(await self._platform_projection(item))

    async def create_constraint(self, payload: OperationalConstraintCreate, user: dict) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        self._validate_payload(data)
        data.setdefault("constraint_reference", self._constraint_reference())
        data.setdefault("constraint_status", "draft")
        data.setdefault("constraint_version", "1.0")
        data.setdefault("condition_logic", "all")
        data.setdefault("review_status", "not_started")
        data.setdefault("approval_status", "not_requested")
        data.setdefault("created_by", user.get("id"))
        data["updated_by"] = user.get("id")
        data.update(self.safety_flags())
        constraint = OperationalConstraint(**data)
        created = await self.db.collection(OPERATIONAL_CONSTRAINT_COLLECTION).insert_one(constraint.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "operational_constraint": await self._platform_projection(created),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def update_constraint(self, constraint_id: str, payload: OperationalConstraintUpdate, user: dict) -> dict[str, Any]:
        existing = await self._require_constraint(constraint_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        self._validate_payload(updates, partial=True)
        updates["updated_by"] = user.get("id")
        updates.update(self.safety_flags())
        updated = await self.db.collection(OPERATIONAL_CONSTRAINT_COLLECTION).update_one({"id": existing["id"]}, updates)
        if not updated:
            raise OperationalConstraintEngineError("Operational constraint metadata could not be updated.")
        return {
            "phase": PHASE_LABEL,
            "operational_constraint": await self._platform_projection(updated),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def delete_constraint(self, constraint_id: str, user: dict) -> dict[str, Any]:
        existing = await self._require_constraint(constraint_id)
        updated = await self.db.collection(OPERATIONAL_CONSTRAINT_COLLECTION).update_one(
            {"id": existing["id"]},
            {
                "constraint_status": "archived",
                "deleted_at": self._now(),
                "deleted_by": user.get("id"),
                "updated_by": user.get("id"),
                **self.safety_flags(),
            },
        )
        if not updated:
            raise OperationalConstraintEngineError("Operational constraint metadata could not be archived.")
        return {
            "phase": PHASE_LABEL,
            "operational_constraint": await self._platform_projection(updated),
            "archived": True,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        by_status = {status: 0 for status in CONSTRAINT_STATUSES}
        by_outcome_type = {outcome: 0 for outcome in OUTCOME_TYPES}
        by_review_status = {status: 0 for status in REVIEW_STATUSES}
        by_approval_status = {status: 0 for status in APPROVAL_STATUSES}
        by_airline: dict[str, int] = {}
        by_service_domain: dict[str, int] = {}
        condition_count = 0
        condition_group_count = 0
        evidence_link_count = 0
        operational_link_count = 0
        evaluation_ready_count = 0
        for item in items:
            self._count_value(by_status, item.get("constraint_status"))
            self._count_value(by_outcome_type, item.get("outcome_type"))
            self._count_value(by_review_status, item.get("review_status"))
            self._count_value(by_approval_status, item.get("approval_status"))
            self._count_value(by_airline, item.get("airline_code"))
            self._count_value(by_service_domain, item.get("service_domain"))
            condition_count += self._list_count(item.get("conditions"))
            condition_groups = item.get("condition_groups") or []
            condition_group_count += self._list_count(condition_groups)
            condition_count += sum(self._list_count(group.get("conditions")) for group in condition_groups if isinstance(group, dict))
            evidence_link_count += self._list_count(item.get("evidence_reference_ids"))
            operational_link_count += self._list_count(item.get("ssr_osi_workspace_ids"))
            operational_link_count += self._list_count(item.get("emd_workspace_ids"))
            operational_link_count += self._list_count(item.get("document_workspace_ids"))
            operational_link_count += self._list_count(item.get("workflow_ids"))
            operational_link_count += self._list_count(item.get("timeline_ids"))
            evaluation_ready_count += 1 if item.get("evaluation_ready") else 0
        return {
            "total_count": len(items),
            "by_constraint_status": by_status,
            "by_outcome_type": by_outcome_type,
            "by_review_status": by_review_status,
            "by_approval_status": by_approval_status,
            "by_airline": by_airline,
            "by_service_domain": by_service_domain,
            "condition_count": condition_count,
            "condition_group_count": condition_group_count,
            "evidence_link_count": evidence_link_count,
            "operational_link_count": operational_link_count,
            "evaluation_ready_count": evaluation_ready_count,
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "agency_id": "agency_id exact metadata match",
            "acquisition_id": "acquisition_id exact metadata match",
            "airline": "airline_code exact metadata match",
            "service_domain": "service_domain exact metadata match",
            "service_family": "service_family exact metadata match",
            "ssr_code": "ssr_code exact metadata match",
            "rfic": "rfic exact metadata match",
            "rfisc": "rfisc exact metadata match",
            "constraint_status": CONSTRAINT_STATUSES,
            "outcome_type": OUTCOME_TYPES,
            "condition_operator": CONDITION_OPERATORS,
            "review_status": REVIEW_STATUSES,
            "approval_status": APPROVAL_STATUSES,
            "evaluation_ready": "true or false metadata flag; no evaluation runs",
            "metadata_only": True,
        }

    async def _platform_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        projected["constraint_display_name"] = self._display_name(projected)
        projected["supported_condition_operators"] = CONDITION_OPERATORS
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

    async def _require_constraint(self, constraint_id: str, *, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": constraint_id}
        if agency_id:
            filters["agency_id"] = agency_id
        item = await self.db.collection(OPERATIONAL_CONSTRAINT_COLLECTION).find_one(filters)
        if not item:
            alt_filters = {"constraint_reference": constraint_id}
            if agency_id:
                alt_filters["agency_id"] = agency_id
            item = await self.db.collection(OPERATIONAL_CONSTRAINT_COLLECTION).find_one(alt_filters)
        if not item:
            raise OperationalConstraintEngineError("Operational constraint metadata was not found.")
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
        if data.get("constraint_status") and data["constraint_status"] not in CONSTRAINT_STATUSES:
            raise OperationalConstraintEngineError("Constraint status must be a known metadata status.")
        if data.get("outcome_type") and data["outcome_type"] not in OUTCOME_TYPES:
            raise OperationalConstraintEngineError("Outcome type must be a known operational constraint outcome.")
        if data.get("review_status") and data["review_status"] not in REVIEW_STATUSES:
            raise OperationalConstraintEngineError("Review status must be a known metadata status.")
        if data.get("approval_status") and data["approval_status"] not in APPROVAL_STATUSES:
            raise OperationalConstraintEngineError("Approval status must be a known metadata status.")
        self._validate_conditions(data.get("conditions") or [])
        for group in data.get("condition_groups") or []:
            if isinstance(group, dict):
                self._validate_conditions(group.get("conditions") or [])
        if not partial and not (data.get("conditions") or data.get("condition_groups")):
            raise OperationalConstraintEngineError("At least one condition or condition group is required for constraint metadata.")

    def _validate_conditions(self, conditions: list[Any]) -> None:
        for condition in conditions:
            if not isinstance(condition, dict):
                continue
            operator = condition.get("condition_operator")
            if operator and operator not in CONDITION_OPERATORS:
                raise OperationalConstraintEngineError("Condition operator must be supported by the metadata language.")

    def _filter_airline(self, items: list[dict[str, Any]], airline: str | None) -> list[dict[str, Any]]:
        if not airline:
            return items
        value = airline.lower()
        return [item for item in items if str(item.get("airline_code") or "").lower() == value]

    def _display_name(self, item: dict[str, Any]) -> str:
        if item.get("constraint_name"):
            return str(item["constraint_name"])
        if item.get("constraint_reference"):
            return str(item["constraint_reference"])
        return item.get("id") or "Operational constraint"

    def _constraint_reference(self) -> str:
        return f"OC-{new_id()[:8].upper()}"

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
            "constraint_language_foundation": True,
            "live_rule_execution_disabled": True,
            "ai_reasoning_disabled": True,
            "recommendation_engine_disabled": True,
            "feasibility_scoring_disabled": True,
            "pricing_calculation_disabled": True,
            "parser_execution_disabled": True,
            "scraping_disabled": True,
            "background_workers_disabled": True,
            "provider_integrations_disabled": True,
            "evaluation_endpoint_disabled": True,
        }
