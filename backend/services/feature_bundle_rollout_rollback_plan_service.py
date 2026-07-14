from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import (
    FeatureBundleRolloutRollbackPlan,
    FeatureBundleRolloutRollbackPlanCreate,
    FeatureBundleRolloutRollbackPlanUpdate,
    new_id,
)
from services.agency_feature_flag_bundle_service import AgencyFeatureFlagBundleService
from services.feature_bundle_dependency_service import DEPENDENCY_COLLECTION
from services.feature_bundle_rollout_change_request_service import CHANGE_REQUEST_COLLECTION
from services.feature_bundle_rollout_decision_service import DECISION_COLLECTION
from services.feature_bundle_rollout_issue_service import ISSUE_COLLECTION
from services.feature_bundle_rollout_risk_service import RISK_COLLECTION
from services.offer_decision_export_delivery_service import actor_from_user, payload_dict


PHASE_LABEL = "phase_54_7_servicing_after_sales_workflow_foundation"

ROLLBACK_PLAN_COLLECTION = "feature_bundle_rollout_rollback_plans"
PLAN_COLLECTION = "agency_feature_bundle_rollout_plans"
FEATURE_FLAG_COLLECTION = "agency_feature_flags"
ROLLBACK_TRIGGERS = [
    "manual_review",
    "issue_detected",
    "risk_threshold",
    "dependency_unready",
    "agency_request",
    "schedule_conflict",
    "operational_concern",
    "documentation_gap",
    "future_runtime_signal",
]
ROLLBACK_SCOPES = ["bundle", "feature_flag", "agency", "dependency", "schedule", "readiness", "approval", "operational", "documentation"]
ROLLBACK_STATUSES = ["draft", "under_review", "approved", "rejected", "ready", "deferred", "superseded", "archived"]
ROLLBACK_PRIORITIES = ["low", "medium", "high", "urgent"]


class FeatureBundleRolloutRollbackPlanService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_platform_rollback_plans(
        self,
        *,
        rollout_plan_id: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        scope: str | None = None,
        owner: str | None = None,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if rollout_plan_id:
            filters["rollout_plan_id"] = rollout_plan_id
        if status:
            filters["rollback_status"] = status
        if priority:
            filters["rollback_priority"] = priority
        if scope:
            filters["rollback_scope"] = scope
        if owner:
            filters["rollback_owner"] = owner
        rollback_plans = await self.db.collection(ROLLBACK_PLAN_COLLECTION).find_many(filters or None)
        if not include_archived:
            rollback_plans = [item for item in rollback_plans if not item.get("deleted_at")]
        rollback_plans.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._platform_projection(item) for item in rollback_plans]

    async def list_agency_rollback_plans(
        self,
        agency_id: str,
        *,
        rollout_plan_id: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        scope: str | None = None,
        owner: str | None = None,
    ) -> list[dict[str, Any]]:
        rollback_plans = await self.list_platform_rollback_plans(
            rollout_plan_id=rollout_plan_id,
            status=status,
            priority=priority,
            scope=scope,
            owner=owner,
        )
        return [self._agency_projection(item, agency_id) for item in rollback_plans if item.get("agency_id") == agency_id]

    async def platform_response(
        self,
        *,
        rollout_plan_id: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        scope: str | None = None,
        owner: str | None = None,
        include_archived: bool = False,
    ) -> dict[str, Any]:
        items = await self.list_platform_rollback_plans(
            rollout_plan_id=rollout_plan_id,
            status=status,
            priority=priority,
            scope=scope,
            owner=owner,
            include_archived=include_archived,
        )
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "rollback_plan_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Feature bundle rollout rollback plans are metadata only. They do not execute rollbacks, automate deployments, activate or deactivate features, enforce entitlements, bill, call providers or external APIs, use AI, run workers or schedulers, notify users, send email, execute webhooks, publish, switch runtime behavior, or trigger automation.",
            **self.safety_flags(),
        }

    async def agency_response(
        self,
        agency_id: str,
        *,
        rollout_plan_id: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        scope: str | None = None,
        owner: str | None = None,
    ) -> dict[str, Any]:
        items = await self.list_agency_rollback_plans(
            agency_id,
            rollout_plan_id=rollout_plan_id,
            status=status,
            priority=priority,
            scope=scope,
            owner=owner,
        )
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "rollback_plan_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            "notice": "Feature bundle rollout rollback plan metadata is read-only for this agency. It does not execute rollbacks, activate or deactivate features, enforce access, bill, call providers or external APIs, use AI, notify users, send email, publish, switch runtime behavior, or automate actions.",
            **self.safety_flags(),
        }

    async def platform_summary(self) -> dict[str, Any]:
        items = await self.list_platform_rollback_plans(include_archived=True)
        return {
            "phase": PHASE_LABEL,
            "summary": self.summarize_counts(items),
            "rollback_plan_count": len(items),
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        items = await self.list_agency_rollback_plans(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(items),
            "rollback_plan_count": len(items),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def get_platform_rollback_plan(self, rollback_plan_id: str) -> dict[str, Any]:
        rollback_plan = await self._require_rollback_plan(rollback_plan_id)
        return await self._platform_projection(rollback_plan)

    async def get_agency_rollback_plan(self, agency_id: str, rollback_plan_id: str) -> dict[str, Any]:
        projected = await self.get_platform_rollback_plan(rollback_plan_id)
        if projected.get("agency_id") != agency_id:
            raise ValueError("Feature bundle rollout rollback plan metadata was not found for this agency.")
        return self._agency_projection(projected, agency_id)

    async def create_rollback_plan(
        self,
        payload: FeatureBundleRolloutRollbackPlanCreate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        self._validate_dimension("trigger", data.get("rollback_trigger") or "manual_review", ROLLBACK_TRIGGERS)
        self._validate_dimension("scope", data.get("rollback_scope") or "bundle", ROLLBACK_SCOPES)
        self._validate_dimension("status", data.get("rollback_status") or "draft", ROLLBACK_STATUSES)
        self._validate_dimension("priority", data.get("rollback_priority") or "medium", ROLLBACK_PRIORITIES)
        rollback_plan = FeatureBundleRolloutRollbackPlan(
            id=data.get("id") or new_id(),
            rollout_plan_id=data["rollout_plan_id"],
            rollout_phase=data.get("rollout_phase"),
            rollback_title=data["rollback_title"],
            rollback_summary=data.get("rollback_summary"),
            rollback_reason=data.get("rollback_reason"),
            rollback_trigger=data.get("rollback_trigger") or "manual_review",
            rollback_scope=data.get("rollback_scope") or "bundle",
            rollback_status=data.get("rollback_status") or "draft",
            rollback_owner=data.get("rollback_owner") or actor_from_user(user),
            rollback_priority=data.get("rollback_priority") or "medium",
            affected_bundle_ids=data.get("affected_bundle_ids") or [],
            affected_feature_flag_ids=data.get("affected_feature_flag_ids") or [],
            related_change_request_ids=data.get("related_change_request_ids") or [],
            related_decision_ids=data.get("related_decision_ids") or [],
            related_issue_ids=data.get("related_issue_ids") or [],
            related_risk_ids=data.get("related_risk_ids") or [],
            related_dependency_ids=data.get("related_dependency_ids") or [],
            rollback_steps=data.get("rollback_steps") or [],
            validation_notes=data.get("validation_notes"),
            created_by=actor_from_user(user),
            updated_by=actor_from_user(user),
            metadata=data.get("metadata") or {},
        )
        stored = await self.db.collection(ROLLBACK_PLAN_COLLECTION).insert_one(rollback_plan.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "rollback_plan": await self._platform_projection(stored),
            "metadata_only": True,
            "notice": "Feature bundle rollout rollback plan metadata was saved only. No rollback execution, deployment automation, feature activation or deactivation, entitlement enforcement, billing, provider integration, AI, external API, worker, scheduler, notification, email, webhook, publishing, runtime switch, or automation was triggered.",
            **self.safety_flags(),
        }

    async def update_rollback_plan(
        self,
        rollback_plan_id: str,
        payload: FeatureBundleRolloutRollbackPlanUpdate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_rollback_plan(rollback_plan_id)
        updates = {key: value for key, value in payload_dict(payload).items() if value is not None}
        if "rollback_trigger" in updates:
            self._validate_dimension("trigger", updates["rollback_trigger"], ROLLBACK_TRIGGERS)
        if "rollback_scope" in updates:
            self._validate_dimension("scope", updates["rollback_scope"], ROLLBACK_SCOPES)
        if "rollback_status" in updates:
            self._validate_dimension("status", updates["rollback_status"], ROLLBACK_STATUSES)
        if "rollback_priority" in updates:
            self._validate_dimension("priority", updates["rollback_priority"], ROLLBACK_PRIORITIES)
        updates.update(
            {
                "updated_at": self._now(),
                "updated_by": actor_from_user(user),
                "metadata_only": True,
                "rollback_plan_metadata_only": True,
            }
        )
        updated = await self.db.collection(ROLLBACK_PLAN_COLLECTION).update_one({"id": existing["id"]}, updates)
        stored = updated or {**existing, **updates}
        return {
            "phase": PHASE_LABEL,
            "rollback_plan": await self._platform_projection(stored),
            "metadata_only": True,
            "notice": "Feature bundle rollout rollback plan metadata was updated only. No rollback execution, deployment automation, activation, deactivation, enforcement, billing, provider integration, AI, external API, worker, scheduler, notification, email, webhook, publishing, runtime switching, or automation ran.",
            **self.safety_flags(),
        }

    async def delete_rollback_plan(self, rollback_plan_id: str, user: dict | None = None) -> dict[str, Any]:
        existing = await self._require_rollback_plan(rollback_plan_id)
        updates = {
            "rollback_status": "archived",
            "deleted_at": self._now(),
            "deleted_by": actor_from_user(user),
            "updated_by": actor_from_user(user),
            "metadata_only": True,
            "rollback_plan_metadata_only": True,
            "rollback_plan_deleted_metadata_only": True,
        }
        updated = await self.db.collection(ROLLBACK_PLAN_COLLECTION).update_one({"id": existing["id"]}, updates)
        stored = updated or {**existing, **updates}
        return {
            "phase": PHASE_LABEL,
            "rollback_plan": await self._platform_projection(stored),
            "deleted": True,
            "metadata_only": True,
            "notice": "Feature bundle rollout rollback plan metadata was archived only. No rollback, deployment, feature activation or deactivation, entitlement enforcement, billing, provider call, AI, external API, worker, scheduler, notification, email, webhook, publishing, runtime switch, or automation ran.",
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        by_status = {status: 0 for status in ROLLBACK_STATUSES}
        by_priority = {priority: 0 for priority in ROLLBACK_PRIORITIES}
        by_scope = {scope: 0 for scope in ROLLBACK_SCOPES}
        by_trigger = {trigger: 0 for trigger in ROLLBACK_TRIGGERS}
        rollout_ids: set[str] = set()
        affected_bundle_ids: set[str] = set()
        affected_feature_flag_ids: set[str] = set()
        related_change_request_ids: set[str] = set()
        related_decision_ids: set[str] = set()
        related_issue_ids: set[str] = set()
        related_risk_ids: set[str] = set()
        related_dependency_ids: set[str] = set()
        rollback_step_count = 0
        for item in items:
            status = item.get("rollback_status") or "draft"
            priority = item.get("rollback_priority") or "medium"
            scope = item.get("rollback_scope") or "bundle"
            trigger = item.get("rollback_trigger") or "manual_review"
            by_status[status] = by_status.get(status, 0) + 1
            by_priority[priority] = by_priority.get(priority, 0) + 1
            by_scope[scope] = by_scope.get(scope, 0) + 1
            by_trigger[trigger] = by_trigger.get(trigger, 0) + 1
            if item.get("rollout_plan_id"):
                rollout_ids.add(item["rollout_plan_id"])
            affected_bundle_ids.update(item.get("affected_bundle_ids") or [])
            affected_feature_flag_ids.update(item.get("affected_feature_flag_ids") or [])
            related_change_request_ids.update(item.get("related_change_request_ids") or [])
            related_decision_ids.update(item.get("related_decision_ids") or [])
            related_issue_ids.update(item.get("related_issue_ids") or [])
            related_risk_ids.update(item.get("related_risk_ids") or [])
            related_dependency_ids.update(item.get("related_dependency_ids") or [])
            rollback_step_count += len(item.get("rollback_steps") or [])
        return {
            "total_count": len(items),
            "by_status": by_status,
            "by_priority": by_priority,
            "by_scope": by_scope,
            "by_trigger": by_trigger,
            "rollout_count": len(rollout_ids),
            "affected_bundle_count": len(affected_bundle_ids),
            "affected_feature_flag_count": len(affected_feature_flag_ids),
            "related_change_request_count": len(related_change_request_ids),
            "related_decision_count": len(related_decision_ids),
            "related_issue_count": len(related_issue_ids),
            "related_risk_count": len(related_risk_ids),
            "related_dependency_count": len(related_dependency_ids),
            "rollback_step_count": rollback_step_count,
            "archived_count": by_status.get("archived", 0),
            "metadata_only": True,
            "rollback_execution_disabled": True,
            "feature_deactivation_disabled": True,
            "automation_disabled": True,
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "triggers": ROLLBACK_TRIGGERS,
            "scopes": ROLLBACK_SCOPES,
            "statuses": ROLLBACK_STATUSES,
            "priorities": ROLLBACK_PRIORITIES,
            "supports_rollout_filter": True,
            "supports_status_filter": True,
            "supports_priority_filter": True,
            "supports_scope_filter": True,
            "supports_owner_filter": True,
            "metadata_only": True,
        }

    async def _require_rollback_plan(self, rollback_plan_id: str) -> dict[str, Any]:
        rollback_plan = await self.db.collection(ROLLBACK_PLAN_COLLECTION).find_one({"id": rollback_plan_id})
        if not rollback_plan:
            raise ValueError("Feature bundle rollout rollback plan metadata was not found.")
        return rollback_plan

    async def _platform_projection(self, rollback_plan: dict[str, Any]) -> dict[str, Any]:
        projected = dict(rollback_plan)
        projected["plan"] = await self._plan_context(projected.get("rollout_plan_id"))
        projected["plan_name"] = projected["plan"].get("plan_name")
        projected["agency_id"] = projected["plan"].get("agency_id")
        projected["agency_name"] = projected["plan"].get("agency_name")
        projected["bundle_id"] = projected["plan"].get("bundle_id")
        projected["bundle_name"] = projected["plan"].get("bundle_name")
        projected["bundle_key"] = projected["plan"].get("bundle_key")
        projected["affected_bundles"] = [await self._bundle_context(bundle_id) for bundle_id in projected.get("affected_bundle_ids") or []]
        projected["affected_feature_flags"] = [await self._feature_flag_context(feature_flag_id, projected.get("agency_id")) for feature_flag_id in projected.get("affected_feature_flag_ids") or []]
        projected["related_change_requests"] = [await self._change_request_context(change_request_id) for change_request_id in projected.get("related_change_request_ids") or []]
        projected["related_decisions"] = [await self._decision_context(decision_id) for decision_id in projected.get("related_decision_ids") or []]
        projected["related_dependencies"] = [await self._dependency_context(dependency_id) for dependency_id in projected.get("related_dependency_ids") or []]
        projected["related_risks"] = [await self._risk_context(risk_id) for risk_id in projected.get("related_risk_ids") or []]
        projected["related_issues"] = [await self._issue_context(issue_id) for issue_id in projected.get("related_issue_ids") or []]
        projected["read_only"] = False
        projected["metadata_only"] = True
        projected["rollback_plan_metadata_only"] = True
        projected.update(self.safety_flags())
        return projected

    def _agency_projection(self, item: dict[str, Any], agency_id: str) -> dict[str, Any]:
        projected = dict(item)
        projected["agency_id"] = agency_id
        projected["read_only"] = True
        projected.update(self.safety_flags())
        return projected

    async def _plan_context(self, rollout_plan_id: str | None) -> dict[str, Any]:
        if not rollout_plan_id:
            return {"rollout_plan_id": None, "plan_name": None, "agency_id": None, "metadata_only": True}
        plan = await self.db.collection(PLAN_COLLECTION).find_one({"rollout_plan_id": rollout_plan_id})
        if not plan:
            plan = await self.db.collection(PLAN_COLLECTION).find_one({"id": rollout_plan_id})
        if not plan:
            return {"rollout_plan_id": rollout_plan_id, "plan_name": rollout_plan_id, "agency_id": None, "metadata_only": True}
        agency = await self._agency_context(plan.get("agency_id"))
        bundle = await self._bundle_context(plan.get("bundle_id"))
        return {
            "rollout_plan_id": plan.get("rollout_plan_id"),
            "plan_name": plan.get("plan_name"),
            "rollout_stage": plan.get("rollout_stage"),
            "agency_id": plan.get("agency_id"),
            "agency_name": agency.get("agency_name"),
            "bundle_id": plan.get("bundle_id"),
            "bundle_name": bundle.get("bundle_name"),
            "bundle_key": bundle.get("bundle_key"),
            "metadata_only": True,
        }

    async def _agency_context(self, agency_id: str | None) -> dict[str, Any]:
        if not agency_id:
            return {"agency_id": None, "agency_name": None, "agency_slug": None}
        agency = await self.db.collection("agencies").find_one({"id": agency_id})
        if not agency:
            return {"agency_id": agency_id, "agency_name": agency_id, "agency_slug": None}
        return {
            "agency_id": agency.get("id"),
            "agency_name": agency.get("name"),
            "agency_slug": agency.get("slug"),
        }

    async def _bundle_context(self, bundle_id: str | None) -> dict[str, Any]:
        if not bundle_id:
            return {"bundle_id": None, "bundle_key": None, "bundle_name": None, "metadata_only": True}
        bundle = await AgencyFeatureFlagBundleService(self.db).get_bundle(bundle_id)
        if not bundle:
            return {"bundle_id": bundle_id, "bundle_key": bundle_id, "bundle_name": bundle_id, "metadata_only": True}
        return {
            "bundle_id": bundle.get("bundle_id"),
            "bundle_key": bundle.get("bundle_key"),
            "bundle_name": bundle.get("bundle_name"),
            "category": bundle.get("category"),
            "metadata_only": True,
        }

    async def _feature_flag_context(self, feature_flag_id: str | None, agency_id: str | None) -> dict[str, Any]:
        if not feature_flag_id:
            return {"feature_flag_id": None, "feature_key": None, "metadata_only": True}
        filters = {"id": feature_flag_id}
        if agency_id:
            filters["agency_id"] = agency_id
        flag = await self.db.collection(FEATURE_FLAG_COLLECTION).find_one(filters)
        if not flag:
            filters = {"feature_key": feature_flag_id}
            if agency_id:
                filters["agency_id"] = agency_id
            flag = await self.db.collection(FEATURE_FLAG_COLLECTION).find_one(filters)
        if not flag:
            return {"feature_flag_id": feature_flag_id, "feature_key": feature_flag_id, "label": feature_flag_id, "metadata_only": True}
        return {
            "feature_flag_id": flag.get("id"),
            "feature_key": flag.get("feature_key"),
            "module_key": flag.get("module_key"),
            "state": flag.get("state"),
            "label": flag.get("feature_key") or flag.get("id"),
            "metadata_only": True,
        }

    async def _change_request_context(self, change_request_id: str | None) -> dict[str, Any]:
        if not change_request_id:
            return {"change_request_id": None, "title": None, "metadata_only": True}
        change_request = await self.db.collection(CHANGE_REQUEST_COLLECTION).find_one({"id": change_request_id})
        if not change_request:
            return {"change_request_id": change_request_id, "title": change_request_id, "metadata_only": True}
        return {
            "change_request_id": change_request.get("id"),
            "title": change_request.get("change_title"),
            "status": change_request.get("change_status"),
            "type": change_request.get("change_type"),
            "priority": change_request.get("priority"),
            "metadata_only": True,
        }

    async def _decision_context(self, decision_id: str | None) -> dict[str, Any]:
        if not decision_id:
            return {"decision_id": None, "title": None, "metadata_only": True}
        decision = await self.db.collection(DECISION_COLLECTION).find_one({"id": decision_id})
        if not decision:
            return {"decision_id": decision_id, "title": decision_id, "metadata_only": True}
        return {
            "decision_id": decision.get("id"),
            "title": decision.get("decision_title"),
            "status": decision.get("decision_status"),
            "category": decision.get("decision_category"),
            "metadata_only": True,
        }

    async def _dependency_context(self, dependency_id: str | None) -> dict[str, Any]:
        if not dependency_id:
            return {"dependency_id": None, "label": None, "metadata_only": True}
        dependency = await self.db.collection(DEPENDENCY_COLLECTION).find_one({"dependency_id": dependency_id})
        if not dependency:
            dependency = await self.db.collection(DEPENDENCY_COLLECTION).find_one({"id": dependency_id})
        if not dependency:
            return {"dependency_id": dependency_id, "label": dependency_id, "metadata_only": True}
        depends_on = dependency.get("depends_on") or {}
        return {
            "dependency_id": dependency.get("dependency_id"),
            "dependency_type": dependency.get("dependency_type"),
            "label": depends_on.get("label") or depends_on.get("reference_id") or dependency.get("dependency_id"),
            "status": dependency.get("status"),
            "metadata_only": True,
        }

    async def _risk_context(self, risk_id: str | None) -> dict[str, Any]:
        if not risk_id:
            return {"risk_id": None, "title": None, "metadata_only": True}
        risk = await self.db.collection(RISK_COLLECTION).find_one({"risk_id": risk_id})
        if not risk:
            risk = await self.db.collection(RISK_COLLECTION).find_one({"id": risk_id})
        if not risk:
            return {"risk_id": risk_id, "title": risk_id, "metadata_only": True}
        return {
            "risk_id": risk.get("risk_id"),
            "title": risk.get("title"),
            "impact": risk.get("impact"),
            "likelihood": risk.get("likelihood"),
            "status": risk.get("status"),
            "metadata_only": True,
        }

    async def _issue_context(self, issue_id: str | None) -> dict[str, Any]:
        if not issue_id:
            return {"issue_id": None, "title": None, "metadata_only": True}
        issue = await self.db.collection(ISSUE_COLLECTION).find_one({"issue_id": issue_id})
        if not issue:
            issue = await self.db.collection(ISSUE_COLLECTION).find_one({"id": issue_id})
        if not issue:
            return {"issue_id": issue_id, "title": issue_id, "metadata_only": True}
        return {
            "issue_id": issue.get("issue_id"),
            "title": issue.get("title"),
            "severity": issue.get("severity"),
            "status": issue.get("status"),
            "metadata_only": True,
        }

    def _validate_dimension(self, label: str, value: str, allowed: list[str]) -> None:
        if value not in allowed:
            raise ValueError(f"Unsupported feature bundle rollout rollback plan {label}.")

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _sort_text(self, value: Any) -> str:
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value or "")

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "rollback_plan_metadata_only": True,
            "rollout_execution_disabled": True,
            "rollback_execution_disabled": True,
            "deployment_automation_disabled": True,
            "feature_activation_disabled": True,
            "feature_deactivation_disabled": True,
            "feature_bundle_activation_disabled": True,
            "feature_bundle_deactivation_disabled": True,
            "entitlement_enforcement_disabled": True,
            "billing_disabled": True,
            "provider_integrations_disabled": True,
            "provider_calls_disabled": True,
            "provider_execution_disabled": True,
            "external_api_calls_disabled": True,
            "ai_execution_disabled": True,
            "external_ai_disabled": True,
            "background_workers_disabled": True,
            "schedulers_disabled": True,
            "notification_sending_disabled": True,
            "notifications_disabled": True,
            "email_sending_disabled": True,
            "webhook_execution_disabled": True,
            "publishing_disabled": True,
            "runtime_switching_disabled": True,
            "automation_disabled": True,
        }
