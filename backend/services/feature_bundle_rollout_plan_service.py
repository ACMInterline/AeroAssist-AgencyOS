from __future__ import annotations

from typing import Any

from database import Database
from models import (
    FeatureBundleRolloutPlan,
    FeatureBundleRolloutPlanCreate,
    FeatureBundleRolloutPlanUpdate,
    new_id,
)
from services.agency_feature_flag_bundle_service import AgencyFeatureFlagBundleService
from services.offer_decision_export_delivery_service import actor_from_user, payload_dict


PHASE_LABEL = "phase_40_2_feature_bundle_rollout_plan_foundation"

PLAN_COLLECTION = "agency_feature_bundle_rollout_plans"
READINESS_COLLECTION = "agency_feature_bundle_rollout_readiness"
ASSIGNMENT_COLLECTION = "agency_feature_bundle_assignments"
PLAN_STAGES = ["draft", "readiness_review", "scheduled", "paused", "archived"]
CHECKLIST_STATUSES = ["pending", "passed", "warning", "blocked"]


class FeatureBundleRolloutPlanService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_platform_plans(
        self,
        *,
        agency_id: str | None = None,
        rollout_stage: str | None = None,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if rollout_stage:
            filters["rollout_stage"] = rollout_stage
        plans = await self.db.collection(PLAN_COLLECTION).find_many(filters or None)
        plans.sort(key=lambda item: (item.get("target_start_date") or "", item.get("agency_id") or "", item.get("plan_name") or ""))
        return [await self._platform_projection(item) for item in plans]

    async def list_agency_plans(self, agency_id: str, *, rollout_stage: str | None = None) -> list[dict[str, Any]]:
        plans = await self.list_platform_plans(agency_id=agency_id, rollout_stage=rollout_stage)
        return [self._agency_projection(item, agency_id) for item in plans]

    async def get_platform_plan(self, rollout_plan_id: str) -> dict[str, Any]:
        plan = await self._require_plan(rollout_plan_id)
        return await self._platform_projection(plan)

    async def get_agency_plan(self, agency_id: str, rollout_plan_id: str) -> dict[str, Any]:
        plan = await self._require_plan(rollout_plan_id, agency_id=agency_id)
        return self._agency_projection(await self._platform_projection(plan), agency_id)

    async def platform_response(
        self,
        *,
        agency_id: str | None = None,
        rollout_stage: str | None = None,
    ) -> dict[str, Any]:
        items = await self.list_platform_plans(agency_id=agency_id, rollout_stage=rollout_stage)
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "plan_count": len(items),
            "summary": self.summarize_counts(items),
            "read_only": False,
            "metadata_only": True,
            "notice": "Rollout plans are metadata only. They do not activate, publish, send, bill, enforce access, block routes, or execute rollout actions.",
            **self.safety_flags(),
        }

    async def agency_response(self, agency_id: str, *, rollout_stage: str | None = None) -> dict[str, Any]:
        items = await self.list_agency_plans(agency_id, rollout_stage=rollout_stage)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "plan_count": len(items),
            "summary": self.summarize_counts(items),
            "read_only": True,
            "metadata_only": True,
            "notice": "Rollout plans are read-only metadata for this agency. They do not activate or block features.",
            **self.safety_flags(),
        }

    async def platform_summary(self, *, agency_id: str | None = None) -> dict[str, Any]:
        items = await self.list_platform_plans(agency_id=agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(items),
            "plan_count": len(items),
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        items = await self.list_agency_plans(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(items),
            "plan_count": len(items),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def create_plan(
        self,
        payload: FeatureBundleRolloutPlanCreate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        await self._require_agency(data.get("agency_id"))
        await self._require_bundle(data.get("bundle_id"))
        assignment = await self._optional_assignment(
            data.get("assigned_bundle_id"),
            agency_id=data.get("agency_id"),
            bundle_id=data.get("bundle_id"),
        )
        readiness = await self._optional_readiness(
            data.get("readiness_snapshot_id"),
            agency_id=data.get("agency_id"),
            bundle_id=data.get("bundle_id"),
        )
        checklist_summary = self._normalize_checklist_summary(data.get("checklist_summary") or {}, readiness)
        plan = FeatureBundleRolloutPlan(
            rollout_plan_id=data.get("rollout_plan_id") or new_id(),
            agency_id=data["agency_id"],
            bundle_id=data["bundle_id"],
            plan_name=data["plan_name"],
            rollout_stage=data.get("rollout_stage") or "draft",
            target_start_date=data.get("target_start_date"),
            target_end_date=data.get("target_end_date"),
            rollout_owner=data.get("rollout_owner") or actor_from_user(user),
            checklist_summary=checklist_summary,
            readiness_snapshot_id=readiness.get("id") if readiness else data.get("readiness_snapshot_id"),
            assigned_bundle_id=(assignment or {}).get("assignment_id") or data.get("assigned_bundle_id"),
            notes=data.get("notes"),
            metadata_only=True,
            rollout_execution_disabled=True,
            feature_activation_disabled=True,
            feature_access_enforcement_disabled=True,
            billing_disabled=True,
            provider_execution_disabled=True,
        )
        stored = await self.db.collection(PLAN_COLLECTION).insert_one(plan.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "plan": await self._platform_projection(stored),
            "metadata_only": True,
            "notice": "Rollout plan metadata was saved only. No rollout action was triggered.",
            **self.safety_flags(),
        }

    async def update_plan(
        self,
        rollout_plan_id: str,
        payload: FeatureBundleRolloutPlanUpdate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_plan(rollout_plan_id)
        updates = {key: value for key, value in payload_dict(payload).items() if value is not None}
        if "bundle_id" in updates:
            await self._require_bundle(updates["bundle_id"])
        target_bundle_id = updates.get("bundle_id") or existing.get("bundle_id")
        assignment = await self._optional_assignment(
            updates.get("assigned_bundle_id", existing.get("assigned_bundle_id")),
            agency_id=existing.get("agency_id"),
            bundle_id=target_bundle_id,
        )
        readiness = await self._optional_readiness(
            updates.get("readiness_snapshot_id", existing.get("readiness_snapshot_id")),
            agency_id=existing.get("agency_id"),
            bundle_id=target_bundle_id,
        )
        if "checklist_summary" in updates:
            updates["checklist_summary"] = self._normalize_checklist_summary(updates.get("checklist_summary") or {}, readiness)
        elif readiness:
            updates["checklist_summary"] = self._normalize_checklist_summary(existing.get("checklist_summary") or {}, readiness)
        if assignment and "assigned_bundle_id" in updates:
            updates["assigned_bundle_id"] = assignment.get("assignment_id")
        updates.update(
            {
                "metadata_only": True,
                "rollout_execution_disabled": True,
                "feature_activation_disabled": True,
                "feature_access_enforcement_disabled": True,
                "billing_disabled": True,
                "provider_execution_disabled": True,
                "updated_by": actor_from_user(user),
            }
        )
        updated = await self.db.collection(PLAN_COLLECTION).update_one({"rollout_plan_id": existing.get("rollout_plan_id")}, updates)
        stored = updated or {**existing, **updates}
        return {
            "phase": PHASE_LABEL,
            "plan": await self._platform_projection(stored),
            "metadata_only": True,
            "notice": "Rollout plan metadata was updated only. No rollout action was triggered.",
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        stage_counts = {stage: 0 for stage in PLAN_STAGES}
        warning_count = 0
        blocker_count = 0
        scheduled_count = 0
        for item in items:
            stage = item.get("rollout_stage") or "draft"
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
            summary = item.get("checklist_summary") or {}
            warning_count += self._summary_count(summary, "warning")
            blocker_count += self._summary_count(summary, "blocked")
            if item.get("target_start_date"):
                scheduled_count += 1
        return {
            "by_rollout_stage": stage_counts,
            "warning_count": warning_count,
            "blocker_count": blocker_count,
            "target_window_count": scheduled_count,
            "metadata_only": True,
        }

    async def _require_plan(self, rollout_plan_id: str, agency_id: str | None = None) -> dict[str, Any]:
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
            raise ValueError("Feature bundle rollout plan metadata was not found.")
        return plan

    async def _require_agency(self, agency_id: str | None) -> dict[str, Any]:
        if not agency_id:
            raise ValueError("agency_id is required.")
        agency = await self.db.collection("agencies").find_one({"id": agency_id})
        if not agency:
            raise ValueError("Agency metadata was not found.")
        return agency

    async def _require_bundle(self, bundle_id: str | None) -> dict[str, Any]:
        if not bundle_id:
            raise ValueError("bundle_id is required.")
        bundle = await AgencyFeatureFlagBundleService(self.db).get_bundle(bundle_id)
        if not bundle:
            raise ValueError("Feature flag bundle metadata was not found.")
        return bundle

    async def _optional_assignment(
        self,
        assigned_bundle_id: str | None,
        *,
        agency_id: str | None,
        bundle_id: str | None,
    ) -> dict[str, Any] | None:
        if not assigned_bundle_id:
            return None
        assignment = await self.db.collection(ASSIGNMENT_COLLECTION).find_one({"assignment_id": assigned_bundle_id})
        if not assignment:
            assignment = await self.db.collection(ASSIGNMENT_COLLECTION).find_one({"id": assigned_bundle_id})
        if not assignment:
            raise ValueError("Assigned bundle metadata was not found.")
        if agency_id and assignment.get("agency_id") != agency_id:
            raise ValueError("Assigned bundle metadata does not belong to the selected agency.")
        if bundle_id and assignment.get("bundle_id") != bundle_id:
            raise ValueError("Assigned bundle metadata does not match the selected bundle.")
        return assignment

    async def _optional_readiness(
        self,
        readiness_snapshot_id: str | None,
        *,
        agency_id: str | None,
        bundle_id: str | None,
    ) -> dict[str, Any] | None:
        if not readiness_snapshot_id:
            return None
        readiness = await self.db.collection(READINESS_COLLECTION).find_one({"id": readiness_snapshot_id})
        if not readiness:
            readiness = await self.db.collection(READINESS_COLLECTION).find_one({"assignment_id": readiness_snapshot_id})
        if readiness:
            if agency_id and readiness.get("agency_id") != agency_id:
                raise ValueError("Readiness snapshot metadata does not belong to the selected agency.")
            if bundle_id and readiness.get("bundle_id") != bundle_id:
                raise ValueError("Readiness snapshot metadata does not match the selected bundle.")
        return readiness

    async def _platform_projection(self, plan: dict[str, Any]) -> dict[str, Any]:
        projected = dict(plan)
        projected["checklist_summary"] = self._normalize_checklist_summary(projected.get("checklist_summary") or {})
        projected["agency"] = await self._agency_context(projected.get("agency_id"))
        projected["agency_name"] = projected["agency"].get("agency_name")
        projected["bundle"] = await self._bundle_context(projected.get("bundle_id"))
        projected["bundle_key"] = projected["bundle"].get("bundle_key")
        projected["bundle_name"] = projected["bundle"].get("bundle_name")
        projected["assignment"] = await self._assignment_context(projected.get("assigned_bundle_id"))
        projected["readiness_snapshot"] = await self._readiness_context(projected.get("readiness_snapshot_id"))
        projected["warnings"] = self._summary_count(projected["checklist_summary"], "warning")
        projected["blockers"] = self._summary_count(projected["checklist_summary"], "blocked")
        projected["read_only"] = False
        projected.update(self.safety_flags())
        return projected

    def _agency_projection(self, item: dict[str, Any], agency_id: str) -> dict[str, Any]:
        projected = dict(item)
        projected["agency_id"] = agency_id
        projected["read_only"] = True
        projected["payloads_hidden"] = True
        projected.update(self.safety_flags())
        return projected

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

    async def _assignment_context(self, assigned_bundle_id: str | None) -> dict[str, Any] | None:
        if not assigned_bundle_id:
            return None
        assignment = await self.db.collection(ASSIGNMENT_COLLECTION).find_one({"assignment_id": assigned_bundle_id})
        if not assignment:
            assignment = await self.db.collection(ASSIGNMENT_COLLECTION).find_one({"id": assigned_bundle_id})
        if not assignment:
            return {
                "assignment_id": assigned_bundle_id,
                "status": "unknown",
                "review_status": "unknown",
                "metadata_only": True,
            }
        return {
            "assignment_id": assignment.get("assignment_id"),
            "status": assignment.get("status"),
            "review_status": assignment.get("review_status"),
            "effective_date": assignment.get("effective_date"),
            "expiration_date": assignment.get("expiration_date"),
            "metadata_only": True,
        }

    async def _readiness_context(self, readiness_snapshot_id: str | None) -> dict[str, Any] | None:
        if not readiness_snapshot_id:
            return None
        readiness = await self.db.collection(READINESS_COLLECTION).find_one({"id": readiness_snapshot_id})
        if not readiness:
            readiness = await self.db.collection(READINESS_COLLECTION).find_one({"assignment_id": readiness_snapshot_id})
        if not readiness:
            return {
                "readiness_snapshot_id": readiness_snapshot_id,
                "readiness_status": "unknown",
                "checklist_counts": self._checklist_counts([]),
                "metadata_only": True,
            }
        return {
            "readiness_snapshot_id": readiness.get("id"),
            "assignment_id": readiness.get("assignment_id"),
            "readiness_status": readiness.get("readiness_status"),
            "checklist_counts": self._checklist_counts(readiness.get("checklist_items") or []),
            "metadata_only": True,
        }

    def _normalize_checklist_summary(self, summary: dict[str, Any], readiness: dict[str, Any] | None = None) -> dict[str, Any]:
        normalized = dict(summary or {})
        counts = dict(normalized.get("counts") or {})
        if readiness:
            counts = self._checklist_counts(readiness.get("checklist_items") or [])
            normalized["readiness_status"] = readiness.get("readiness_status")
            normalized["readiness_snapshot_id"] = readiness.get("id")
        for status in CHECKLIST_STATUSES:
            counts[status] = int(counts.get(status) or 0)
        normalized["counts"] = counts
        normalized["warning_count"] = int(normalized.get("warning_count") or counts.get("warning") or 0)
        normalized["blocker_count"] = int(normalized.get("blocker_count") or counts.get("blocked") or 0)
        normalized["metadata_only"] = True
        return normalized

    def _checklist_counts(self, checklist: list[dict[str, Any]]) -> dict[str, int]:
        counts = {status: 0 for status in CHECKLIST_STATUSES}
        for item in checklist:
            status = item.get("status") or "pending"
            counts[status] = counts.get(status, 0) + 1
        return counts

    def _summary_count(self, summary: dict[str, Any], status: str) -> int:
        counts = summary.get("counts") or {}
        explicit_key = "blocker_count" if status == "blocked" else f"{status}_count"
        return int(summary.get(explicit_key) or counts.get(status) or 0)

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "rollout_execution_disabled": True,
            "feature_activation_disabled": True,
            "feature_deactivation_disabled": True,
            "feature_access_enforcement_disabled": True,
            "route_blocking_disabled": True,
            "permission_changes_disabled": True,
            "entitlement_enforcement_disabled": True,
            "entitlement_evaluation_disabled": True,
            "billing_disabled": True,
            "payments_disabled": True,
            "email_sending_disabled": True,
            "sms_sending_disabled": True,
            "notifications_disabled": True,
            "provider_execution_disabled": True,
            "external_api_calls_disabled": True,
            "external_services_disabled": True,
            "ai_execution_disabled": True,
            "scraping_disabled": True,
            "publishing_disabled": True,
            "background_workers_disabled": True,
            "cron_disabled": True,
        }
