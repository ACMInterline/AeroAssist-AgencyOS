from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import (
    FeatureBundleDependency,
    FeatureBundleDependencyCreate,
    FeatureBundleDependencyUpdate,
    new_id,
)
from services.agency_feature_flag_bundle_service import AgencyFeatureFlagBundleService
from services.offer_decision_export_delivery_service import actor_from_user, payload_dict


PHASE_LABEL = "phase_40_9_feature_bundle_rollout_issue_log_foundation"

DEPENDENCY_COLLECTION = "feature_bundle_dependencies"
PLAN_COLLECTION = "agency_feature_bundle_rollout_plans"
DEPENDENCY_TYPES = ["bundle", "capability", "approval", "rollout_plan", "schedule", "readiness_checklist", "other"]
DEPENDENCY_STATUSES = ["informational", "not_reviewed", "satisfied", "warning", "blocked", "deleted"]


class FeatureBundleDependencyService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_platform_dependencies(
        self,
        *,
        agency_id: str | None = None,
        bundle_id: str | None = None,
        rollout_plan_id: str | None = None,
        dependency_type: str | None = None,
        include_deleted: bool = False,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if bundle_id:
            filters["bundle_id"] = bundle_id
        if rollout_plan_id:
            filters["rollout_plan_id"] = rollout_plan_id
        if dependency_type:
            filters["dependency_type"] = dependency_type
        dependencies = await self.db.collection(DEPENDENCY_COLLECTION).find_many(filters or None)
        if not include_deleted:
            dependencies = [item for item in dependencies if item.get("status") != "deleted" and not item.get("deleted_at")]
        dependencies.sort(key=lambda item: (item.get("bundle_id") or "", item.get("dependency_type") or "", item.get("created_at") or ""), reverse=True)
        return [await self._platform_projection(item) for item in dependencies]

    async def list_agency_dependencies(
        self,
        agency_id: str,
        *,
        bundle_id: str | None = None,
        rollout_plan_id: str | None = None,
        dependency_type: str | None = None,
    ) -> list[dict[str, Any]]:
        dependencies = await self.list_platform_dependencies(
            agency_id=agency_id,
            bundle_id=bundle_id,
            rollout_plan_id=rollout_plan_id,
            dependency_type=dependency_type,
        )
        return [self._agency_projection(item, agency_id) for item in dependencies]

    async def platform_response(
        self,
        *,
        agency_id: str | None = None,
        bundle_id: str | None = None,
        rollout_plan_id: str | None = None,
        dependency_type: str | None = None,
        include_deleted: bool = False,
    ) -> dict[str, Any]:
        items = await self.list_platform_dependencies(
            agency_id=agency_id,
            bundle_id=bundle_id,
            rollout_plan_id=rollout_plan_id,
            dependency_type=dependency_type,
            include_deleted=include_deleted,
        )
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "dependency_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Feature bundle dependencies are metadata only. They do not execute rollout plans, schedule jobs, enforce dependencies, block rollouts, activate bundles, modify permissions, send notifications, publish, call providers, or introduce automation.",
            **self.safety_flags(),
        }

    async def agency_response(
        self,
        agency_id: str,
        *,
        bundle_id: str | None = None,
        rollout_plan_id: str | None = None,
        dependency_type: str | None = None,
    ) -> dict[str, Any]:
        items = await self.list_agency_dependencies(
            agency_id,
            bundle_id=bundle_id,
            rollout_plan_id=rollout_plan_id,
            dependency_type=dependency_type,
        )
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "dependency_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            "notice": "Feature bundle dependency metadata is read-only for this agency. It does not enforce rollout state, block rollout activity, or activate features.",
            **self.safety_flags(),
        }

    async def platform_summary(self, *, agency_id: str | None = None) -> dict[str, Any]:
        items = await self.list_platform_dependencies(agency_id=agency_id, include_deleted=True)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(items),
            "dependency_count": len(items),
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        items = await self.list_agency_dependencies(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(items),
            "dependency_count": len(items),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def get_platform_dependency(self, dependency_id: str) -> dict[str, Any]:
        dependency = await self._require_dependency(dependency_id)
        return await self._platform_projection(dependency)

    async def get_agency_dependency(self, agency_id: str, dependency_id: str) -> dict[str, Any]:
        dependency = await self._require_dependency(dependency_id, agency_id=agency_id)
        return self._agency_projection(await self._platform_projection(dependency), agency_id)

    async def create_dependency(
        self,
        payload: FeatureBundleDependencyCreate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        dependency_type = data.get("dependency_type")
        if dependency_type not in DEPENDENCY_TYPES:
            raise ValueError("Unsupported feature bundle dependency type.")
        dependency = FeatureBundleDependency(
            dependency_id=data.get("dependency_id") or new_id(),
            agency_id=data["agency_id"],
            bundle_id=data["bundle_id"],
            rollout_plan_id=data.get("rollout_plan_id"),
            dependency_type=dependency_type,
            depends_on=data["depends_on"],
            status=data.get("status") or "informational",
            notes=data.get("notes"),
            created_by=actor_from_user(user),
            updated_by=actor_from_user(user),
            metadata=data.get("metadata") or {},
        )
        stored = await self.db.collection(DEPENDENCY_COLLECTION).insert_one(dependency.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "dependency": await self._platform_projection(stored),
            "metadata_only": True,
            "notice": "Feature bundle dependency metadata was saved only. No rollout execution, job scheduling, dependency enforcement, rollout blocking, bundle activation, permission change, notification, publishing, provider call, or automation was triggered.",
            **self.safety_flags(),
        }

    async def update_dependency(
        self,
        dependency_id: str,
        payload: FeatureBundleDependencyUpdate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_dependency(dependency_id)
        updates = {key: value for key, value in payload_dict(payload).items() if value is not None}
        if updates.get("dependency_type") and updates["dependency_type"] not in DEPENDENCY_TYPES:
            raise ValueError("Unsupported feature bundle dependency type.")
        if isinstance(updates.get("depends_on"), dict):
            updates["depends_on"] = {
                **updates["depends_on"],
                "metadata_only": True,
                "dependency_enforcement_disabled": True,
            }
        updates.update(
            {
                "updated_at": self._now(),
                "updated_by": actor_from_user(user),
                "metadata_only": True,
                "dependency_metadata_only": True,
            }
        )
        updated = await self.db.collection(DEPENDENCY_COLLECTION).update_one({"dependency_id": existing["dependency_id"]}, updates)
        stored = updated or {**existing, **updates}
        return {
            "phase": PHASE_LABEL,
            "dependency": await self._platform_projection(stored),
            "metadata_only": True,
            "notice": "Feature bundle dependency metadata was updated only. No dependency enforcement, rollout blocking, rollout execution, permission change, notification, provider call, publishing, or automation was triggered.",
            **self.safety_flags(),
        }

    async def delete_dependency(self, dependency_id: str, user: dict | None = None) -> dict[str, Any]:
        existing = await self._require_dependency(dependency_id)
        updates = {
            "status": "deleted",
            "deleted_at": self._now(),
            "deleted_by": actor_from_user(user),
            "updated_by": actor_from_user(user),
            "metadata_only": True,
            "dependency_metadata_only": True,
            "dependency_deleted_metadata_only": True,
        }
        updated = await self.db.collection(DEPENDENCY_COLLECTION).update_one({"dependency_id": existing["dependency_id"]}, updates)
        stored = updated or {**existing, **updates}
        return {
            "phase": PHASE_LABEL,
            "dependency": await self._platform_projection(stored),
            "deleted": True,
            "metadata_only": True,
            "notice": "Feature bundle dependency metadata was marked deleted only. No rollout was blocked, no dependency was enforced, and no rollout or provider action was executed.",
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        by_dependency_type = {dependency_type: 0 for dependency_type in DEPENDENCY_TYPES}
        by_status = {status: 0 for status in DEPENDENCY_STATUSES}
        bundle_ids: set[str] = set()
        plan_ids: set[str] = set()
        agency_ids: set[str] = set()
        for item in items:
            dependency_type = item.get("dependency_type") or "other"
            status = item.get("status") or "informational"
            by_dependency_type[dependency_type] = by_dependency_type.get(dependency_type, 0) + 1
            by_status[status] = by_status.get(status, 0) + 1
            if item.get("bundle_id"):
                bundle_ids.add(item["bundle_id"])
            if item.get("rollout_plan_id"):
                plan_ids.add(item["rollout_plan_id"])
            if item.get("agency_id"):
                agency_ids.add(item["agency_id"])
        return {
            "total_count": len(items),
            "by_dependency_type": by_dependency_type,
            "by_status": by_status,
            "bundle_count": len(bundle_ids),
            "plan_count": len(plan_ids),
            "agency_count": len(agency_ids),
            "deleted_count": by_status.get("deleted", 0),
            "metadata_only": True,
            "execution_disabled": True,
            "enforcement_disabled": True,
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "dependency_types": DEPENDENCY_TYPES,
            "statuses": DEPENDENCY_STATUSES,
            "supports_bundle_filter": True,
            "supports_plan_filter": True,
            "supports_agency_filter": True,
            "supports_dependency_type_filter": True,
            "metadata_only": True,
        }

    async def _require_dependency(self, dependency_id: str, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"dependency_id": dependency_id}
        if agency_id:
            filters["agency_id"] = agency_id
        dependency = await self.db.collection(DEPENDENCY_COLLECTION).find_one(filters)
        if not dependency:
            filters = {"id": dependency_id}
            if agency_id:
                filters["agency_id"] = agency_id
            dependency = await self.db.collection(DEPENDENCY_COLLECTION).find_one(filters)
        if not dependency:
            raise ValueError("Feature bundle dependency metadata was not found.")
        return dependency

    async def _platform_projection(self, dependency: dict[str, Any]) -> dict[str, Any]:
        projected = dict(dependency)
        projected["bundle"] = await self._bundle_context(projected.get("bundle_id"))
        projected["bundle_key"] = projected["bundle"].get("bundle_key")
        projected["bundle_name"] = projected["bundle"].get("bundle_name")
        projected["agency"] = await self._agency_context(projected.get("agency_id"))
        projected["agency_name"] = projected["agency"].get("agency_name")
        projected["plan"] = await self._plan_context(projected.get("rollout_plan_id"))
        projected["plan_name"] = projected["plan"].get("plan_name")
        projected["depends_on_label"] = self._depends_on_label(projected.get("depends_on") or {})
        projected["read_only"] = False
        projected["metadata_only"] = True
        projected["dependency_metadata_only"] = True
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

    def _depends_on_label(self, reference: dict[str, Any]) -> str:
        return reference.get("label") or reference.get("reference_id") or "Dependency reference"

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "dependency_metadata_only": True,
            "rollout_execution_disabled": True,
            "background_jobs_disabled": True,
            "scheduled_jobs_disabled": True,
            "dependency_enforcement_disabled": True,
            "rollout_blocking_disabled": True,
            "feature_bundle_activation_disabled": True,
            "feature_bundles_enablement_disabled": True,
            "permission_modification_disabled": True,
            "notification_sending_disabled": True,
            "notifications_disabled": True,
            "publishing_disabled": True,
            "provider_calls_disabled": True,
            "provider_execution_disabled": True,
            "automation_disabled": True,
        }
