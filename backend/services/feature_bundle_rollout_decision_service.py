from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import (
    FeatureBundleRolloutDecision,
    FeatureBundleRolloutDecisionCreate,
    FeatureBundleRolloutDecisionUpdate,
    new_id,
)
from services.agency_feature_flag_bundle_service import AgencyFeatureFlagBundleService
from services.feature_bundle_dependency_service import DEPENDENCY_COLLECTION
from services.feature_bundle_rollout_issue_service import ISSUE_COLLECTION
from services.feature_bundle_rollout_risk_service import RISK_COLLECTION
from services.offer_decision_export_delivery_service import actor_from_user, payload_dict


PHASE_LABEL = "phase_40_12_feature_bundle_rollout_rollback_plan_foundation"

DECISION_COLLECTION = "feature_bundle_rollout_decisions"
PLAN_COLLECTION = "agency_feature_bundle_rollout_plans"
TIMELINE_COLLECTION = "feature_bundle_rollout_timeline_entries"
DECISION_CATEGORIES = [
    "readiness",
    "approval",
    "schedule",
    "dependency",
    "risk",
    "issue",
    "rollout_scope",
    "operational",
    "governance",
]
DECISION_STATUSES = ["draft", "proposed", "accepted", "deferred", "rejected", "superseded", "archived"]


class FeatureBundleRolloutDecisionService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_platform_decisions(
        self,
        *,
        rollout_plan_id: str | None = None,
        category: str | None = None,
        owner: str | None = None,
        status: str | None = None,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if rollout_plan_id:
            filters["rollout_plan_id"] = rollout_plan_id
        if category:
            filters["decision_category"] = category
        if owner:
            filters["decision_owner"] = owner
        if status:
            filters["decision_status"] = status
        decisions = await self.db.collection(DECISION_COLLECTION).find_many(filters or None)
        if not include_archived:
            decisions = [item for item in decisions if not item.get("deleted_at")]
        decisions.sort(key=lambda item: item.get("decision_date") or item.get("created_at") or "", reverse=True)
        return [await self._platform_projection(item) for item in decisions]

    async def list_agency_decisions(
        self,
        agency_id: str,
        *,
        rollout_plan_id: str | None = None,
        category: str | None = None,
        owner: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        decisions = await self.list_platform_decisions(
            rollout_plan_id=rollout_plan_id,
            category=category,
            owner=owner,
            status=status,
        )
        return [self._agency_projection(item, agency_id) for item in decisions if item.get("agency_id") == agency_id]

    async def platform_response(
        self,
        *,
        rollout_plan_id: str | None = None,
        category: str | None = None,
        owner: str | None = None,
        status: str | None = None,
        include_archived: bool = False,
    ) -> dict[str, Any]:
        items = await self.list_platform_decisions(
            rollout_plan_id=rollout_plan_id,
            category=category,
            owner=owner,
            status=status,
            include_archived=include_archived,
        )
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "decision_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Feature bundle rollout decisions are metadata only. They do not execute rollouts, deploy, activate features, enforce entitlements, bill, call providers or external APIs, use AI, schedule work, notify users, publish, switch runtime behavior, or trigger automation.",
            **self.safety_flags(),
        }

    async def agency_response(
        self,
        agency_id: str,
        *,
        rollout_plan_id: str | None = None,
        category: str | None = None,
        owner: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        items = await self.list_agency_decisions(
            agency_id,
            rollout_plan_id=rollout_plan_id,
            category=category,
            owner=owner,
            status=status,
        )
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "decision_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            "notice": "Feature bundle rollout decision metadata is read-only for this agency. It does not execute rollouts, activate features, enforce access, bill, call providers or external APIs, use AI, notify users, publish, switch runtime behavior, or automate actions.",
            **self.safety_flags(),
        }

    async def platform_summary(self) -> dict[str, Any]:
        items = await self.list_platform_decisions(include_archived=True)
        return {
            "phase": PHASE_LABEL,
            "summary": self.summarize_counts(items),
            "decision_count": len(items),
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        items = await self.list_agency_decisions(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(items),
            "decision_count": len(items),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def get_platform_decision(self, decision_id: str) -> dict[str, Any]:
        decision = await self._require_decision(decision_id)
        return await self._platform_projection(decision)

    async def get_agency_decision(self, agency_id: str, decision_id: str) -> dict[str, Any]:
        projected = await self.get_platform_decision(decision_id)
        if projected.get("agency_id") != agency_id:
            raise ValueError("Feature bundle rollout decision metadata was not found for this agency.")
        return self._agency_projection(projected, agency_id)

    async def create_decision(
        self,
        payload: FeatureBundleRolloutDecisionCreate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        self._validate_dimension("category", data.get("decision_category") or "operational", DECISION_CATEGORIES)
        self._validate_dimension("status", data.get("decision_status") or "draft", DECISION_STATUSES)
        decision = FeatureBundleRolloutDecision(
            id=data.get("id") or new_id(),
            rollout_plan_id=data["rollout_plan_id"],
            rollout_phase=data.get("rollout_phase"),
            decision_title=data["decision_title"],
            decision_summary=data.get("decision_summary"),
            decision_reason=data.get("decision_reason"),
            decision_category=data.get("decision_category") or "operational",
            decision_status=data.get("decision_status") or "draft",
            decision_owner=data.get("decision_owner"),
            decision_date=data.get("decision_date") or self._now(),
            related_bundle_ids=data.get("related_bundle_ids") or [],
            related_dependency_ids=data.get("related_dependency_ids") or [],
            related_risk_ids=data.get("related_risk_ids") or [],
            related_issue_ids=data.get("related_issue_ids") or [],
            timeline_reference_ids=data.get("timeline_reference_ids") or [],
            notes=data.get("notes"),
            created_by=actor_from_user(user),
            updated_by=actor_from_user(user),
            metadata=data.get("metadata") or {},
        )
        stored = await self.db.collection(DECISION_COLLECTION).insert_one(decision.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "decision": await self._platform_projection(stored),
            "metadata_only": True,
            "notice": "Feature bundle rollout decision metadata was saved only. No rollout execution, deployment automation, feature activation, entitlement enforcement, billing, provider integration, AI, external API, scheduler, notification, webhook, publishing, runtime switch, or automation was triggered.",
            **self.safety_flags(),
        }

    async def update_decision(
        self,
        decision_id: str,
        payload: FeatureBundleRolloutDecisionUpdate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_decision(decision_id)
        updates = {key: value for key, value in payload_dict(payload).items() if value is not None}
        if "decision_category" in updates:
            self._validate_dimension("category", updates["decision_category"], DECISION_CATEGORIES)
        if "decision_status" in updates:
            self._validate_dimension("status", updates["decision_status"], DECISION_STATUSES)
        updates.update(
            {
                "updated_at": self._now(),
                "updated_by": actor_from_user(user),
                "metadata_only": True,
                "decision_register_metadata_only": True,
            }
        )
        updated = await self.db.collection(DECISION_COLLECTION).update_one({"id": existing["id"]}, updates)
        stored = updated or {**existing, **updates}
        return {
            "phase": PHASE_LABEL,
            "decision": await self._platform_projection(stored),
            "metadata_only": True,
            "notice": "Feature bundle rollout decision metadata was updated only. No rollout execution, deployment automation, activation, enforcement, billing, provider integration, AI, external API, scheduler, notification, webhook, publishing, runtime switching, or automation ran.",
            **self.safety_flags(),
        }

    async def delete_decision(self, decision_id: str, user: dict | None = None) -> dict[str, Any]:
        existing = await self._require_decision(decision_id)
        updates = {
            "decision_status": "archived",
            "deleted_at": self._now(),
            "deleted_by": actor_from_user(user),
            "updated_by": actor_from_user(user),
            "metadata_only": True,
            "decision_register_metadata_only": True,
            "decision_deleted_metadata_only": True,
        }
        updated = await self.db.collection(DECISION_COLLECTION).update_one({"id": existing["id"]}, updates)
        stored = updated or {**existing, **updates}
        return {
            "phase": PHASE_LABEL,
            "decision": await self._platform_projection(stored),
            "deleted": True,
            "metadata_only": True,
            "notice": "Feature bundle rollout decision metadata was archived only. No rollout, deployment, feature activation, entitlement enforcement, billing, provider call, AI, external API, scheduler, notification, webhook, publishing, runtime switch, or automation ran.",
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        by_status = {status: 0 for status in DECISION_STATUSES}
        by_category = {category: 0 for category in DECISION_CATEGORIES}
        owner_ids: set[str] = set()
        rollout_ids: set[str] = set()
        related_bundle_ids: set[str] = set()
        related_dependency_ids: set[str] = set()
        related_risk_ids: set[str] = set()
        related_issue_ids: set[str] = set()
        for item in items:
            status = item.get("decision_status") or "draft"
            category = item.get("decision_category") or "operational"
            by_status[status] = by_status.get(status, 0) + 1
            by_category[category] = by_category.get(category, 0) + 1
            if item.get("decision_owner"):
                owner_ids.add(item["decision_owner"])
            if item.get("rollout_plan_id"):
                rollout_ids.add(item["rollout_plan_id"])
            related_bundle_ids.update(item.get("related_bundle_ids") or [])
            related_dependency_ids.update(item.get("related_dependency_ids") or [])
            related_risk_ids.update(item.get("related_risk_ids") or [])
            related_issue_ids.update(item.get("related_issue_ids") or [])
        return {
            "total_count": len(items),
            "by_status": by_status,
            "by_category": by_category,
            "owner_count": len(owner_ids),
            "rollout_count": len(rollout_ids),
            "related_bundle_count": len(related_bundle_ids),
            "related_dependency_count": len(related_dependency_ids),
            "related_risk_count": len(related_risk_ids),
            "related_issue_count": len(related_issue_ids),
            "archived_count": by_status.get("archived", 0),
            "metadata_only": True,
            "execution_disabled": True,
            "automation_disabled": True,
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "categories": DECISION_CATEGORIES,
            "statuses": DECISION_STATUSES,
            "supports_rollout_filter": True,
            "supports_category_filter": True,
            "supports_owner_filter": True,
            "supports_status_filter": True,
            "metadata_only": True,
        }

    async def _require_decision(self, decision_id: str) -> dict[str, Any]:
        decision = await self.db.collection(DECISION_COLLECTION).find_one({"id": decision_id})
        if not decision:
            raise ValueError("Feature bundle rollout decision metadata was not found.")
        return decision

    async def _platform_projection(self, decision: dict[str, Any]) -> dict[str, Any]:
        projected = dict(decision)
        projected["plan"] = await self._plan_context(projected.get("rollout_plan_id"))
        projected["plan_name"] = projected["plan"].get("plan_name")
        projected["agency_id"] = projected["plan"].get("agency_id")
        projected["agency_name"] = projected["plan"].get("agency_name")
        projected["bundle_id"] = projected["plan"].get("bundle_id")
        projected["bundle_name"] = projected["plan"].get("bundle_name")
        projected["bundle_key"] = projected["plan"].get("bundle_key")
        projected["related_bundles"] = [await self._bundle_context(bundle_id) for bundle_id in projected.get("related_bundle_ids") or []]
        projected["related_dependencies"] = [await self._dependency_context(dependency_id) for dependency_id in projected.get("related_dependency_ids") or []]
        projected["related_risks"] = [await self._risk_context(risk_id) for risk_id in projected.get("related_risk_ids") or []]
        projected["related_issues"] = [await self._issue_context(issue_id) for issue_id in projected.get("related_issue_ids") or []]
        projected["timeline_references"] = [await self._timeline_context(entry_id) for entry_id in projected.get("timeline_reference_ids") or []]
        projected["read_only"] = False
        projected["metadata_only"] = True
        projected["decision_register_metadata_only"] = True
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

    async def _timeline_context(self, entry_id: str | None) -> dict[str, Any]:
        if not entry_id:
            return {"entry_id": None, "label": None, "metadata_only": True}
        entry = await self.db.collection(TIMELINE_COLLECTION).find_one({"timeline_entry_id": entry_id})
        if not entry:
            entry = await self.db.collection(TIMELINE_COLLECTION).find_one({"entry_id": entry_id})
        if not entry:
            entry = await self.db.collection(TIMELINE_COLLECTION).find_one({"id": entry_id})
        if not entry:
            return {"entry_id": entry_id, "label": entry_id, "metadata_only": True}
        return {
            "entry_id": entry.get("timeline_entry_id") or entry.get("entry_id"),
            "event_type": entry.get("event_type"),
            "description": entry.get("description"),
            "occurred_at": entry.get("occurred_at"),
            "metadata_only": True,
        }

    def _validate_dimension(self, label: str, value: str, allowed: list[str]) -> None:
        if value not in allowed:
            raise ValueError(f"Unsupported feature bundle rollout decision {label}.")

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "decision_register_metadata_only": True,
            "rollout_execution_disabled": True,
            "deployment_automation_disabled": True,
            "feature_activation_disabled": True,
            "feature_bundle_activation_disabled": True,
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
