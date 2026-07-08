from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import (
    FeatureBundleRolloutSchedule,
    FeatureBundleRolloutScheduleCreate,
    FeatureBundleRolloutScheduleUpdate,
    new_id,
)
from services.agency_feature_flag_bundle_service import AgencyFeatureFlagBundleService
from services.offer_decision_export_delivery_service import actor_from_user, payload_dict


PHASE_LABEL = "phase_41_6_booking_workspace_foundation"

SCHEDULE_COLLECTION = "feature_bundle_rollout_schedules"
PLAN_COLLECTION = "agency_feature_bundle_rollout_plans"
APPROVAL_COLLECTION = "feature_bundle_rollout_approvals"
SCHEDULE_STATUSES = ["Planned", "Ready", "AwaitingApproval", "Approved", "Deferred", "Cancelled", "CompletedMetadata"]


class FeatureBundleRolloutScheduleService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_platform_schedules(
        self,
        *,
        agency_id: str | None = None,
        rollout_plan_id: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if rollout_plan_id:
            filters["rollout_plan_id"] = rollout_plan_id
        if status:
            filters["schedule_status"] = status
        schedules = await self.db.collection(SCHEDULE_COLLECTION).find_many(filters or None)
        schedules.sort(key=lambda item: (self._sort_text(item.get("planned_start") or item.get("created_at")), item.get("rollout_name") or ""), reverse=True)
        return [await self._platform_projection(item) for item in schedules]

    async def list_agency_schedules(self, agency_id: str, *, status: str | None = None) -> list[dict[str, Any]]:
        schedules = await self.list_platform_schedules(agency_id=agency_id, status=status)
        return [self._agency_projection(item, agency_id) for item in schedules]

    async def platform_response(
        self,
        *,
        agency_id: str | None = None,
        rollout_plan_id: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        items = await self.list_platform_schedules(agency_id=agency_id, rollout_plan_id=rollout_plan_id, status=status)
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "schedule_count": len(items),
            "summary": self.summarize_counts(items),
            "read_only": False,
            "metadata_only": True,
            "notice": "Rollout schedules are metadata only. They do not start timers, run workers, activate features, change entitlements, change permissions, bill, publish, call external APIs, use AI, or execute rollouts.",
            **self.safety_flags(),
        }

    async def agency_response(self, agency_id: str, *, status: str | None = None) -> dict[str, Any]:
        items = await self.list_agency_schedules(agency_id, status=status)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "schedule_count": len(items),
            "summary": self.summarize_counts(items),
            "read_only": True,
            "metadata_only": True,
            "notice": "Rollout schedule metadata is read-only for this agency. It does not activate features, change access, or execute rollout actions.",
            **self.safety_flags(),
        }

    async def platform_summary(self, *, agency_id: str | None = None) -> dict[str, Any]:
        items = await self.list_platform_schedules(agency_id=agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(items),
            "schedule_count": len(items),
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        items = await self.list_agency_schedules(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(items),
            "schedule_count": len(items),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def get_platform_schedule(self, schedule_id: str) -> dict[str, Any]:
        schedule = await self._require_schedule(schedule_id)
        return await self._platform_projection(schedule)

    async def get_agency_schedule(self, agency_id: str, schedule_id: str) -> dict[str, Any]:
        schedule = await self._require_schedule(schedule_id, agency_id=agency_id)
        return self._agency_projection(await self._platform_projection(schedule), agency_id)

    async def create_schedule(
        self,
        payload: FeatureBundleRolloutScheduleCreate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        plan = await self._require_plan(data.get("rollout_plan_id"))
        if data.get("agency_id") and data.get("agency_id") != plan.get("agency_id"):
            raise ValueError("Schedule agency metadata must match the rollout plan agency.")
        if data.get("bundle_id") and data.get("bundle_id") != plan.get("bundle_id"):
            raise ValueError("Schedule bundle metadata must match the rollout plan bundle.")
        actor = actor_from_user(user)
        schedule = FeatureBundleRolloutSchedule(
            schedule_id=data.get("schedule_id") or new_id(),
            rollout_plan_id=plan["rollout_plan_id"],
            rollout_name=data.get("rollout_name") or plan.get("plan_name") or "Feature bundle rollout",
            bundle_id=plan["bundle_id"],
            agency_id=plan["agency_id"],
            schedule_status=data.get("schedule_status") or "Planned",
            planned_start=data.get("planned_start"),
            planned_finish=data.get("planned_finish"),
            scheduling_notes=data.get("scheduling_notes"),
            created_by=actor,
            updated_by=actor,
            maintenance_window=data.get("maintenance_window"),
            estimated_duration=data.get("estimated_duration"),
            dependency_summary=data.get("dependency_summary") or {},
            checklist_summary=data.get("checklist_summary") or plan.get("checklist_summary") or {},
            approval_summary=await self._approval_summary(plan["rollout_plan_id"], data.get("approval_summary") or {}),
        )
        stored = await self.db.collection(SCHEDULE_COLLECTION).insert_one(schedule.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "schedule": await self._platform_projection(stored),
            "metadata_only": True,
            "notice": "Rollout schedule metadata was saved only. No timer, scheduler, worker, queue, feature activation, entitlement change, permission change, billing, publishing, API call, AI action, or rollout execution was triggered.",
            **self.safety_flags(),
        }

    async def update_schedule(
        self,
        schedule_id: str,
        payload: FeatureBundleRolloutScheduleUpdate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_schedule(schedule_id)
        updates = {key: value for key, value in payload_dict(payload).items() if value is not None}
        updates.update(
            {
                "updated_at": self._now(),
                "updated_by": actor_from_user(user),
                "metadata_only": True,
                "scheduling_metadata_only": True,
            }
        )
        updated = await self.db.collection(SCHEDULE_COLLECTION).update_one({"schedule_id": existing["schedule_id"]}, updates)
        stored = updated or {**existing, **updates}
        return {
            "phase": PHASE_LABEL,
            "schedule": await self._platform_projection(stored),
            "metadata_only": True,
            "notice": "Rollout schedule metadata was updated only. No timer, scheduler, worker, queue, feature activation, entitlement change, permission change, billing, publishing, API call, AI action, or rollout execution was triggered.",
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        counts = {status: 0 for status in SCHEDULE_STATUSES}
        for item in items:
            status = item.get("schedule_status") or "Planned"
            counts[status] = counts.get(status, 0) + 1
        return {
            "total_count": len(items),
            "by_schedule_status": counts,
            "planned_count": counts.get("Planned", 0),
            "ready_count": counts.get("Ready", 0),
            "awaiting_approval_count": counts.get("AwaitingApproval", 0),
            "approved_count": counts.get("Approved", 0),
            "deferred_count": counts.get("Deferred", 0),
            "cancelled_count": counts.get("Cancelled", 0),
            "completed_metadata_count": counts.get("CompletedMetadata", 0),
            "metadata_only": True,
            "execution_disabled": True,
        }

    async def _require_schedule(self, schedule_id: str, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"schedule_id": schedule_id}
        if agency_id:
            filters["agency_id"] = agency_id
        schedule = await self.db.collection(SCHEDULE_COLLECTION).find_one(filters)
        if not schedule:
            filters = {"id": schedule_id}
            if agency_id:
                filters["agency_id"] = agency_id
            schedule = await self.db.collection(SCHEDULE_COLLECTION).find_one(filters)
        if not schedule:
            raise ValueError("Rollout schedule metadata was not found.")
        return schedule

    async def _require_plan(self, rollout_plan_id: str | None, agency_id: str | None = None) -> dict[str, Any]:
        if not rollout_plan_id:
            raise ValueError("rollout_plan_id is required.")
        filters = {"rollout_plan_id": rollout_plan_id}
        if agency_id:
            filters["agency_id"] = agency_id
        plan = await self.db.collection(PLAN_COLLECTION).find_one(filters)
        if not plan:
            filters = {"id": rollout_plan_id}
            if agency_id:
                filters["agency_id"] = agency_id
            plan = await self.db.collection(PLAN_COLLECTION).find_one(filters)
        if not plan:
            raise ValueError("Rollout plan metadata was not found.")
        return plan

    async def _platform_projection(self, schedule: dict[str, Any]) -> dict[str, Any]:
        projected = dict(schedule)
        plan = await self._plan_context(projected.get("rollout_plan_id"))
        projected["plan"] = plan
        projected["plan_name"] = plan.get("plan_name")
        projected["rollout_stage"] = plan.get("rollout_stage")
        projected["target_start_date"] = plan.get("target_start_date")
        projected["target_end_date"] = plan.get("target_end_date")
        projected["rollout_owner"] = plan.get("rollout_owner")
        projected["agency"] = await self._agency_context(projected.get("agency_id"))
        projected["agency_name"] = projected["agency"].get("agency_name")
        projected["bundle"] = await self._bundle_context(projected.get("bundle_id"))
        projected["bundle_key"] = projected["bundle"].get("bundle_key")
        projected["bundle_name"] = projected["bundle"].get("bundle_name")
        projected["approval_summary"] = await self._approval_summary(projected.get("rollout_plan_id"), projected.get("approval_summary") or {})
        projected["read_only"] = False
        projected["metadata_only"] = True
        projected["scheduling_metadata_only"] = True
        projected.update(self.safety_flags())
        return projected

    def _agency_projection(self, item: dict[str, Any], agency_id: str) -> dict[str, Any]:
        projected = dict(item)
        projected["agency_id"] = agency_id
        projected["read_only"] = True
        projected["payloads_hidden"] = True
        projected.update(self.safety_flags())
        return projected

    async def _plan_context(self, rollout_plan_id: str | None) -> dict[str, Any]:
        if not rollout_plan_id:
            return {"rollout_plan_id": None, "metadata_only": True}
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
            "target_start_date": plan.get("target_start_date"),
            "target_end_date": plan.get("target_end_date"),
            "rollout_owner": plan.get("rollout_owner"),
            "readiness_snapshot_id": plan.get("readiness_snapshot_id"),
            "assigned_bundle_id": plan.get("assigned_bundle_id"),
            "checklist_summary": plan.get("checklist_summary") or {},
            "metadata_only": True,
        }

    async def _agency_context(self, agency_id: str | None) -> dict[str, Any]:
        agency = await self.db.collection("agencies").find_one({"id": agency_id})
        if not agency:
            return {"agency_id": agency_id, "agency_name": agency_id, "agency_slug": None}
        return {
            "agency_id": agency.get("id"),
            "agency_name": agency.get("name"),
            "agency_slug": agency.get("slug"),
        }

    async def _bundle_context(self, bundle_id: str | None) -> dict[str, Any]:
        bundle = await AgencyFeatureFlagBundleService(self.db).get_bundle(bundle_id or "")
        if not bundle:
            return {"bundle_id": bundle_id, "bundle_key": bundle_id, "bundle_name": bundle_id, "category": None}
        return {
            "bundle_id": bundle.get("bundle_id"),
            "bundle_key": bundle.get("bundle_key"),
            "bundle_name": bundle.get("bundle_name"),
            "category": bundle.get("category"),
        }

    async def _approval_summary(self, rollout_plan_id: str | None, existing: dict[str, Any]) -> dict[str, Any]:
        approvals = await self.db.collection(APPROVAL_COLLECTION).find_many({"rollout_plan_id": rollout_plan_id}) if rollout_plan_id else []
        status_counts = {status: 0 for status in ["draft", "submitted", "under_review", "approved", "rejected", "archived"]}
        for approval in approvals:
            status = approval.get("status") or "draft"
            status_counts[status] = status_counts.get(status, 0) + 1
        latest = sorted(approvals, key=lambda item: item.get("updated_at") or item.get("created_at") or "", reverse=True)[0] if approvals else {}
        return {
            **(existing or {}),
            "approval_count": len(approvals),
            "by_status": status_counts,
            "latest_status": latest.get("status"),
            "latest_approval_id": latest.get("approval_id"),
            "metadata_only": True,
        }

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _sort_text(self, value: Any) -> str:
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value or "")

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "scheduling_metadata_only": True,
            "rollout_execution_disabled": True,
            "feature_activation_disabled": True,
            "entitlement_behavior_disabled": True,
            "permission_changes_disabled": True,
            "cron_jobs_disabled": True,
            "schedulers_disabled": True,
            "workers_disabled": True,
            "queues_disabled": True,
            "timers_disabled": True,
            "background_execution_disabled": True,
            "external_api_calls_disabled": True,
            "ai_execution_disabled": True,
            "billing_disabled": True,
            "publishing_disabled": True,
            "automation_disabled": True,
        }
