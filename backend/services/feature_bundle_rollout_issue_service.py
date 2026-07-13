from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import (
    FeatureBundleRolloutIssue,
    FeatureBundleRolloutIssueCreate,
    FeatureBundleRolloutIssueUpdate,
    new_id,
)
from services.agency_feature_flag_bundle_service import AgencyFeatureFlagBundleService
from services.feature_bundle_dependency_service import DEPENDENCY_COLLECTION
from services.feature_bundle_rollout_risk_service import RISK_COLLECTION
from services.offer_decision_export_delivery_service import actor_from_user, payload_dict


PHASE_LABEL = "phase_54_3_sla_operational_deadline_engine_foundation"

ISSUE_COLLECTION = "feature_bundle_rollout_issues"
PLAN_COLLECTION = "agency_feature_bundle_rollout_plans"
APPROVAL_COLLECTION = "feature_bundle_rollout_approvals"
ISSUE_SEVERITIES = ["low", "medium", "high", "critical"]
ISSUE_STATUSES = ["open", "in_review", "follow_up", "resolved", "closed", "deleted"]


class FeatureBundleRolloutIssueService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_platform_issues(
        self,
        *,
        agency_id: str | None = None,
        bundle_id: str | None = None,
        rollout_plan_id: str | None = None,
        risk_id: str | None = None,
        dependency_id: str | None = None,
        approval_id: str | None = None,
        severity: str | None = None,
        status: str | None = None,
        include_deleted: bool = False,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if bundle_id:
            filters["bundle_id"] = bundle_id
        if rollout_plan_id:
            filters["rollout_plan_id"] = rollout_plan_id
        if risk_id:
            filters["risk_id"] = risk_id
        if dependency_id:
            filters["dependency_id"] = dependency_id
        if approval_id:
            filters["approval_id"] = approval_id
        if severity:
            filters["severity"] = severity
        if status:
            filters["status"] = status
        issues = await self.db.collection(ISSUE_COLLECTION).find_many(filters or None)
        if not include_deleted:
            issues = [item for item in issues if item.get("status") != "deleted" and not item.get("deleted_at")]
        issues.sort(key=lambda item: item.get("created_at") or "", reverse=True)
        return [await self._platform_projection(item) for item in issues]

    async def list_agency_issues(
        self,
        agency_id: str,
        *,
        bundle_id: str | None = None,
        rollout_plan_id: str | None = None,
        risk_id: str | None = None,
        dependency_id: str | None = None,
        approval_id: str | None = None,
        severity: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        issues = await self.list_platform_issues(
            agency_id=agency_id,
            bundle_id=bundle_id,
            rollout_plan_id=rollout_plan_id,
            risk_id=risk_id,
            dependency_id=dependency_id,
            approval_id=approval_id,
            severity=severity,
            status=status,
        )
        return [self._agency_projection(item, agency_id) for item in issues]

    async def platform_response(
        self,
        *,
        agency_id: str | None = None,
        bundle_id: str | None = None,
        rollout_plan_id: str | None = None,
        risk_id: str | None = None,
        dependency_id: str | None = None,
        approval_id: str | None = None,
        severity: str | None = None,
        status: str | None = None,
        include_deleted: bool = False,
    ) -> dict[str, Any]:
        items = await self.list_platform_issues(
            agency_id=agency_id,
            bundle_id=bundle_id,
            rollout_plan_id=rollout_plan_id,
            risk_id=risk_id,
            dependency_id=dependency_id,
            approval_id=approval_id,
            severity=severity,
            status=status,
            include_deleted=include_deleted,
        )
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "issue_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Feature bundle rollout issues are metadata only. They do not execute rollouts, activate bundles, enforce blocking, send notifications, call external providers, or add AI/provider execution.",
            **self.safety_flags(),
        }

    async def agency_response(
        self,
        agency_id: str,
        *,
        bundle_id: str | None = None,
        rollout_plan_id: str | None = None,
        risk_id: str | None = None,
        dependency_id: str | None = None,
        approval_id: str | None = None,
        severity: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        items = await self.list_agency_issues(
            agency_id,
            bundle_id=bundle_id,
            rollout_plan_id=rollout_plan_id,
            risk_id=risk_id,
            dependency_id=dependency_id,
            approval_id=approval_id,
            severity=severity,
            status=status,
        )
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "issue_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            "notice": "Feature bundle rollout issue metadata is read-only for this agency. It does not execute rollouts, activate bundles, enforce blocking, send notifications, call providers, or execute AI/provider logic.",
            **self.safety_flags(),
        }

    async def platform_summary(self, *, agency_id: str | None = None) -> dict[str, Any]:
        items = await self.list_platform_issues(agency_id=agency_id, include_deleted=True)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(items),
            "issue_count": len(items),
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        items = await self.list_agency_issues(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(items),
            "issue_count": len(items),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def get_platform_issue(self, issue_id: str) -> dict[str, Any]:
        issue = await self._require_issue(issue_id)
        return await self._platform_projection(issue)

    async def get_agency_issue(self, agency_id: str, issue_id: str) -> dict[str, Any]:
        issue = await self._require_issue(issue_id, agency_id=agency_id)
        return self._agency_projection(await self._platform_projection(issue), agency_id)

    async def create_issue(
        self,
        payload: FeatureBundleRolloutIssueCreate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        self._validate_dimension("severity", data.get("severity") or "medium", ISSUE_SEVERITIES)
        self._validate_dimension("status", data.get("status") or "open", ISSUE_STATUSES)
        issue = FeatureBundleRolloutIssue(
            issue_id=data.get("issue_id") or new_id(),
            agency_id=data.get("agency_id"),
            bundle_id=data.get("bundle_id"),
            rollout_plan_id=data.get("rollout_plan_id"),
            risk_id=data.get("risk_id"),
            dependency_id=data.get("dependency_id"),
            approval_id=data.get("approval_id"),
            title=data["title"],
            description=data.get("description"),
            severity=data.get("severity") or "medium",
            status=data.get("status") or "open",
            owner=data.get("owner"),
            resolution_notes=data.get("resolution_notes"),
            review_notes=data.get("review_notes"),
            created_by=actor_from_user(user),
            updated_by=actor_from_user(user),
            metadata=data.get("metadata") or {},
        )
        stored = await self.db.collection(ISSUE_COLLECTION).insert_one(issue.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "issue": await self._platform_projection(stored),
            "metadata_only": True,
            "notice": "Feature bundle rollout issue metadata was saved only. No rollout execution, bundle activation, blocking enforcement, notification, provider call, or AI/provider execution was triggered.",
            **self.safety_flags(),
        }

    async def update_issue(
        self,
        issue_id: str,
        payload: FeatureBundleRolloutIssueUpdate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_issue(issue_id)
        updates = {key: value for key, value in payload_dict(payload).items() if value is not None}
        if "severity" in updates:
            self._validate_dimension("severity", updates["severity"], ISSUE_SEVERITIES)
        if "status" in updates:
            self._validate_dimension("status", updates["status"], ISSUE_STATUSES)
        updates.update(
            {
                "updated_at": self._now(),
                "updated_by": actor_from_user(user),
                "metadata_only": True,
                "issue_log_metadata_only": True,
            }
        )
        updated = await self.db.collection(ISSUE_COLLECTION).update_one({"issue_id": existing["issue_id"]}, updates)
        stored = updated or {**existing, **updates}
        return {
            "phase": PHASE_LABEL,
            "issue": await self._platform_projection(stored),
            "metadata_only": True,
            "notice": "Feature bundle rollout issue metadata was updated only. No rollout execution, activation, blocking enforcement, notification, provider call, or AI/provider execution was triggered.",
            **self.safety_flags(),
        }

    async def delete_issue(self, issue_id: str, user: dict | None = None) -> dict[str, Any]:
        existing = await self._require_issue(issue_id)
        updates = {
            "status": "deleted",
            "deleted_at": self._now(),
            "deleted_by": actor_from_user(user),
            "updated_by": actor_from_user(user),
            "metadata_only": True,
            "issue_log_metadata_only": True,
            "issue_deleted_metadata_only": True,
        }
        updated = await self.db.collection(ISSUE_COLLECTION).update_one({"issue_id": existing["issue_id"]}, updates)
        stored = updated or {**existing, **updates}
        return {
            "phase": PHASE_LABEL,
            "issue": await self._platform_projection(stored),
            "deleted": True,
            "metadata_only": True,
            "notice": "Feature bundle rollout issue metadata was marked deleted only. No rollout was executed, no bundle was activated, no blocking was enforced, and no provider or AI action ran.",
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        by_status = {status: 0 for status in ISSUE_STATUSES}
        by_severity = {severity: 0 for severity in ISSUE_SEVERITIES}
        agency_ids: set[str] = set()
        bundle_ids: set[str] = set()
        plan_ids: set[str] = set()
        risk_ids: set[str] = set()
        dependency_ids: set[str] = set()
        approval_ids: set[str] = set()
        for item in items:
            status = item.get("status") or "open"
            severity = item.get("severity") or "medium"
            by_status[status] = by_status.get(status, 0) + 1
            by_severity[severity] = by_severity.get(severity, 0) + 1
            if item.get("agency_id"):
                agency_ids.add(item["agency_id"])
            if item.get("bundle_id"):
                bundle_ids.add(item["bundle_id"])
            if item.get("rollout_plan_id"):
                plan_ids.add(item["rollout_plan_id"])
            if item.get("risk_id"):
                risk_ids.add(item["risk_id"])
            if item.get("dependency_id"):
                dependency_ids.add(item["dependency_id"])
            if item.get("approval_id"):
                approval_ids.add(item["approval_id"])
        return {
            "total_count": len(items),
            "by_status": by_status,
            "by_severity": by_severity,
            "agency_count": len(agency_ids),
            "bundle_count": len(bundle_ids),
            "plan_count": len(plan_ids),
            "risk_count": len(risk_ids),
            "dependency_count": len(dependency_ids),
            "approval_count": len(approval_ids),
            "deleted_count": by_status.get("deleted", 0),
            "metadata_only": True,
            "execution_disabled": True,
            "blocking_disabled": True,
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "severities": ISSUE_SEVERITIES,
            "statuses": ISSUE_STATUSES,
            "supports_agency_filter": True,
            "supports_bundle_filter": True,
            "supports_rollout_plan_filter": True,
            "supports_risk_filter": True,
            "supports_dependency_filter": True,
            "supports_approval_filter": True,
            "supports_severity_filter": True,
            "supports_status_filter": True,
            "metadata_only": True,
        }

    async def _require_issue(self, issue_id: str, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"issue_id": issue_id}
        if agency_id:
            filters["agency_id"] = agency_id
        issue = await self.db.collection(ISSUE_COLLECTION).find_one(filters)
        if not issue:
            filters = {"id": issue_id}
            if agency_id:
                filters["agency_id"] = agency_id
            issue = await self.db.collection(ISSUE_COLLECTION).find_one(filters)
        if not issue:
            raise ValueError("Feature bundle rollout issue metadata was not found.")
        return issue

    async def _platform_projection(self, issue: dict[str, Any]) -> dict[str, Any]:
        projected = dict(issue)
        projected["agency"] = await self._agency_context(projected.get("agency_id"))
        projected["agency_name"] = projected["agency"].get("agency_name")
        projected["bundle"] = await self._bundle_context(projected.get("bundle_id"))
        projected["bundle_key"] = projected["bundle"].get("bundle_key")
        projected["bundle_name"] = projected["bundle"].get("bundle_name")
        projected["plan"] = await self._plan_context(projected.get("rollout_plan_id"))
        projected["plan_name"] = projected["plan"].get("plan_name")
        projected["risk"] = await self._risk_context(projected.get("risk_id"))
        projected["risk_title"] = projected["risk"].get("risk_title")
        projected["dependency"] = await self._dependency_context(projected.get("dependency_id"))
        projected["dependency_label"] = projected["dependency"].get("dependency_label")
        projected["approval"] = await self._approval_context(projected.get("approval_id"))
        projected["approval_status"] = projected["approval"].get("status")
        projected["read_only"] = False
        projected["metadata_only"] = True
        projected["issue_log_metadata_only"] = True
        projected.update(self.safety_flags())
        return projected

    def _agency_projection(self, item: dict[str, Any], agency_id: str) -> dict[str, Any]:
        projected = dict(item)
        projected["agency_id"] = agency_id
        projected["read_only"] = True
        projected.update(self.safety_flags())
        return projected

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
            return {"bundle_id": None, "bundle_key": None, "bundle_name": None, "category": None}
        bundle = await AgencyFeatureFlagBundleService(self.db).get_bundle(bundle_id)
        if not bundle:
            return {"bundle_id": bundle_id, "bundle_key": bundle_id, "bundle_name": bundle_id, "category": None}
        return {
            "bundle_id": bundle.get("bundle_id"),
            "bundle_key": bundle.get("bundle_key"),
            "bundle_name": bundle.get("bundle_name"),
            "category": bundle.get("category"),
        }

    async def _plan_context(self, rollout_plan_id: str | None) -> dict[str, Any]:
        if not rollout_plan_id:
            return {"rollout_plan_id": None, "plan_name": None, "metadata_only": True}
        plan = await self.db.collection(PLAN_COLLECTION).find_one({"rollout_plan_id": rollout_plan_id})
        if not plan:
            plan = await self.db.collection(PLAN_COLLECTION).find_one({"id": rollout_plan_id})
        if not plan:
            return {"rollout_plan_id": rollout_plan_id, "plan_name": rollout_plan_id, "metadata_only": True}
        return {
            "rollout_plan_id": plan.get("rollout_plan_id"),
            "plan_name": plan.get("plan_name"),
            "agency_id": plan.get("agency_id"),
            "bundle_id": plan.get("bundle_id"),
            "rollout_stage": plan.get("rollout_stage"),
            "metadata_only": True,
        }

    async def _risk_context(self, risk_id: str | None) -> dict[str, Any]:
        if not risk_id:
            return {"risk_id": None, "risk_title": None, "metadata_only": True}
        risk = await self.db.collection(RISK_COLLECTION).find_one({"risk_id": risk_id})
        if not risk:
            risk = await self.db.collection(RISK_COLLECTION).find_one({"id": risk_id})
        if not risk:
            return {"risk_id": risk_id, "risk_title": risk_id, "metadata_only": True}
        return {
            "risk_id": risk.get("risk_id"),
            "risk_title": risk.get("title"),
            "impact": risk.get("impact"),
            "likelihood": risk.get("likelihood"),
            "status": risk.get("status"),
            "metadata_only": True,
        }

    async def _dependency_context(self, dependency_id: str | None) -> dict[str, Any]:
        if not dependency_id:
            return {"dependency_id": None, "dependency_label": None, "metadata_only": True}
        dependency = await self.db.collection(DEPENDENCY_COLLECTION).find_one({"dependency_id": dependency_id})
        if not dependency:
            dependency = await self.db.collection(DEPENDENCY_COLLECTION).find_one({"id": dependency_id})
        if not dependency:
            return {"dependency_id": dependency_id, "dependency_label": dependency_id, "metadata_only": True}
        depends_on = dependency.get("depends_on") or {}
        return {
            "dependency_id": dependency.get("dependency_id"),
            "dependency_type": dependency.get("dependency_type"),
            "dependency_label": depends_on.get("label") or depends_on.get("reference_id") or dependency.get("dependency_id"),
            "status": dependency.get("status"),
            "metadata_only": True,
        }

    async def _approval_context(self, approval_id: str | None) -> dict[str, Any]:
        if not approval_id:
            return {"approval_id": None, "status": None, "metadata_only": True}
        approval = await self.db.collection(APPROVAL_COLLECTION).find_one({"approval_id": approval_id})
        if not approval:
            approval = await self.db.collection(APPROVAL_COLLECTION).find_one({"id": approval_id})
        if not approval:
            return {"approval_id": approval_id, "status": None, "metadata_only": True}
        return {
            "approval_id": approval.get("approval_id"),
            "rollout_plan_id": approval.get("rollout_plan_id"),
            "status": approval.get("status"),
            "approved_by": approval.get("approved_by"),
            "metadata_only": True,
        }

    def _validate_dimension(self, label: str, value: str, allowed: list[str]) -> None:
        if value not in allowed:
            raise ValueError(f"Unsupported feature bundle rollout issue {label}.")

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "issue_log_metadata_only": True,
            "rollout_execution_disabled": True,
            "feature_bundle_activation_disabled": True,
            "feature_bundles_enablement_disabled": True,
            "rollout_blocking_disabled": True,
            "blocking_enforcement_disabled": True,
            "notification_sending_disabled": True,
            "notifications_disabled": True,
            "external_provider_calls_disabled": True,
            "provider_calls_disabled": True,
            "provider_execution_disabled": True,
            "ai_provider_execution_disabled": True,
            "ai_execution_disabled": True,
            "automation_disabled": True,
            "background_jobs_disabled": True,
        }
