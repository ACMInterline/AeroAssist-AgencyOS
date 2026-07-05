from __future__ import annotations

from typing import Any

from database import Database
from models import (
    AgencyFeatureBundleAssignment,
    AgencyFeatureBundleAssignmentCreate,
    AgencyFeatureBundleAssignmentHistory,
    AgencyFeatureBundleAssignmentUpdate,
    new_id,
    now_utc,
)
from services.agency_feature_flag_bundle_service import AgencyFeatureFlagBundleService
from services.offer_decision_export_delivery_service import actor_from_user, payload_dict


PHASE_LABEL = "phase_40_1_feature_bundle_rollout_readiness_foundation"

ASSIGNMENT_COLLECTION = "agency_feature_bundle_assignments"
HISTORY_COLLECTION = "agency_feature_bundle_assignment_history"


class AgencyFeatureBundleAssignmentService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_assignments(self, *, agency_id: str | None = None, status: str | None = None, agency_view: bool = False) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if status:
            filters["status"] = status
        assignments = await self.db.collection(ASSIGNMENT_COLLECTION).find_many(filters or None)
        assignments.sort(key=lambda item: (item.get("agency_id") or "", self._timestamp_sort_value(item.get("updated_at"))), reverse=True)
        return [await self._assignment_projection(item, agency_view=agency_view) for item in assignments]

    async def list_history(
        self,
        *,
        agency_id: str | None = None,
        assignment_id: str | None = None,
        agency_view: bool = False,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if assignment_id:
            filters["assignment_id"] = assignment_id
        history = await self.db.collection(HISTORY_COLLECTION).find_many(filters or None)
        history.sort(key=lambda item: self._timestamp_sort_value(item.get("changed_at") or item.get("created_at")), reverse=True)
        return [await self._history_projection(item, agency_view=agency_view) for item in history]

    async def platform_assignments_response(self, *, agency_id: str | None = None) -> dict[str, Any]:
        assignments = await self.list_assignments(agency_id=agency_id)
        history = await self.list_history(agency_id=agency_id)
        return {
            "phase": PHASE_LABEL,
            "items": assignments,
            "history": history,
            "assignment_count": len(assignments),
            "history_count": len(history),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_assignments_response(self, agency_id: str) -> dict[str, Any]:
        assignments = await self.list_assignments(agency_id=agency_id, agency_view=True)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": assignments,
            "assignment_count": len(assignments),
            "notice": "Feature bundle assignments are informational only and do not activate features.",
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_history_response(self, agency_id: str) -> dict[str, Any]:
        history = await self.list_history(agency_id=agency_id, agency_view=True)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": history,
            "history_count": len(history),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def create_assignment(
        self,
        agency_id: str,
        payload: AgencyFeatureBundleAssignmentCreate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        data["agency_id"] = agency_id
        await self._require_bundle(data.get("bundle_id"))
        actor = actor_from_user(user)
        assignment = AgencyFeatureBundleAssignment(
            assignment_id=data.get("assignment_id") or new_id(),
            agency_id=agency_id,
            bundle_id=data["bundle_id"],
            assigned_by=data.get("assigned_by") or actor,
            assigned_at=data.get("assigned_at") or now_utc(),
            effective_date=data.get("effective_date"),
            expiration_date=data.get("expiration_date"),
            status=data.get("status") or "assigned",
            notes=data.get("notes"),
            review_status=data.get("review_status") or "pending_review",
            metadata_only=True,
            activation_logic_disabled=True,
            entitlement_enforcement_disabled=True,
            billing_disabled=True,
        )
        stored = await self.db.collection(ASSIGNMENT_COLLECTION).insert_one(assignment.model_dump(mode="json"))
        await self._record_history(stored, "created", actor)
        return {
            "phase": PHASE_LABEL,
            "assignment": await self._assignment_projection(stored),
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def update_assignment(
        self,
        assignment_id: str,
        payload: AgencyFeatureBundleAssignmentUpdate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_assignment(assignment_id)
        updates = {key: value for key, value in payload_dict(payload).items() if value is not None}
        if "bundle_id" in updates:
            await self._require_bundle(updates["bundle_id"])
        updates.update(
            {
                "metadata_only": True,
                "activation_logic_disabled": True,
                "entitlement_enforcement_disabled": True,
                "billing_disabled": True,
            }
        )
        updated = await self.db.collection(ASSIGNMENT_COLLECTION).update_one({"assignment_id": assignment_id}, updates)
        stored = updated or {**existing, **updates}
        await self._record_history(stored, "updated", actor_from_user(user))
        return {
            "phase": PHASE_LABEL,
            "assignment": await self._assignment_projection(stored),
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def inactive_assignment(self, assignment_id: str, user: dict | None = None) -> dict[str, Any]:
        existing = await self._require_assignment(assignment_id)
        updates = {
            "status": "inactive",
            "review_status": "inactive",
            "notes": existing.get("notes") or "Assignment marked inactive as metadata only.",
            "metadata_only": True,
            "activation_logic_disabled": True,
            "entitlement_enforcement_disabled": True,
            "billing_disabled": True,
        }
        updated = await self.db.collection(ASSIGNMENT_COLLECTION).update_one({"assignment_id": assignment_id}, updates)
        stored = updated or {**existing, **updates}
        await self._record_history(stored, "inactivated", actor_from_user(user))
        return {
            "phase": PHASE_LABEL,
            "assignment": await self._assignment_projection(stored),
            "deleted": False,
            "inactive": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def _require_assignment(self, assignment_id: str) -> dict[str, Any]:
        assignment = await self.db.collection(ASSIGNMENT_COLLECTION).find_one({"assignment_id": assignment_id})
        if not assignment:
            assignment = await self.db.collection(ASSIGNMENT_COLLECTION).find_one({"id": assignment_id})
        if not assignment:
            raise ValueError("Feature bundle assignment metadata was not found.")
        return assignment

    async def _require_bundle(self, bundle_id: str | None) -> dict[str, Any]:
        if not bundle_id:
            raise ValueError("bundle_id is required.")
        bundle = await AgencyFeatureFlagBundleService(self.db).get_bundle(bundle_id)
        if not bundle:
            raise ValueError("Feature flag bundle metadata was not found.")
        return bundle

    async def _record_history(self, assignment: dict[str, Any], history_event: str, changed_by: str | None) -> dict[str, Any]:
        history = AgencyFeatureBundleAssignmentHistory(
            assignment_id=assignment["assignment_id"],
            agency_id=assignment["agency_id"],
            bundle_id=assignment["bundle_id"],
            assigned_by=assignment.get("assigned_by"),
            assigned_at=assignment.get("assigned_at"),
            effective_date=assignment.get("effective_date"),
            expiration_date=assignment.get("expiration_date"),
            status=assignment.get("status") or "assigned",
            notes=assignment.get("notes"),
            review_status=assignment.get("review_status") or "pending_review",
            history_event=history_event,
            changed_by=changed_by,
            changed_at=now_utc(),
            metadata_only=True,
            activation_logic_disabled=True,
        )
        return await self.db.collection(HISTORY_COLLECTION).insert_one(history.model_dump(mode="json"))

    async def _assignment_projection(self, assignment: dict[str, Any], *, agency_view: bool = False) -> dict[str, Any]:
        projected = dict(assignment)
        bundle = await AgencyFeatureFlagBundleService(self.db).get_bundle(projected.get("bundle_id") or "")
        projected["bundle"] = {
            "bundle_id": bundle.get("bundle_id"),
            "bundle_key": bundle.get("bundle_key"),
            "bundle_name": bundle.get("bundle_name"),
            "description": bundle.get("description"),
        } if bundle else None
        projected["bundle_name"] = projected.get("bundle", {}).get("bundle_name") if projected.get("bundle") else projected.get("bundle_id")
        projected["read_only"] = agency_view
        projected.update(self.safety_flags())
        if agency_view:
            projected["payloads_hidden"] = True
        return projected

    async def _history_projection(self, history: dict[str, Any], *, agency_view: bool = False) -> dict[str, Any]:
        projected = dict(history)
        bundle = await AgencyFeatureFlagBundleService(self.db).get_bundle(projected.get("bundle_id") or "")
        projected["bundle_name"] = bundle.get("bundle_name") if bundle else projected.get("bundle_id")
        projected["read_only"] = True
        projected.update(self.safety_flags())
        if agency_view:
            projected["payloads_hidden"] = True
        return projected

    def _timestamp_sort_value(self, value: Any) -> str:
        if value is None:
            return ""
        return value.isoformat() if hasattr(value, "isoformat") else str(value)

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "no_activation_logic_enabled": True,
            "feature_activation_disabled": True,
            "runtime_execution_disabled": True,
            "feature_flag_execution_disabled": True,
            "entitlement_enforcement_disabled": True,
            "entitlement_evaluation_disabled": True,
            "billing_disabled": True,
            "payments_disabled": True,
            "stripe_disabled": True,
            "licensing_disabled": True,
            "permission_changes_disabled": True,
            "provider_calls_disabled": True,
            "external_ai_disabled": True,
            "background_workers_disabled": True,
            "cron_disabled": True,
        }
