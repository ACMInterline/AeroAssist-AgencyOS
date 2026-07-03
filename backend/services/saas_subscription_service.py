from __future__ import annotations

from typing import Any

from database import Database
from models import (
    AgencyEntitlementReadiness,
    AgencyEntitlementReadinessCreateRequest,
    AgencySubscriptionAssignment,
    AgencySubscriptionAssignmentCreateRequest,
    AgencySubscriptionAssignmentUpdateRequest,
    AgencySubscriptionReviewNote,
    AgencySubscriptionReviewNoteCreateRequest,
    AgencySubscriptionSnapshot,
    AgencySubscriptionSnapshotCreateRequest,
    SaaSPlanEntitlement,
    SaaSPlanEntitlementCreateRequest,
    SaaSSubscriptionPlan,
    SaaSSubscriptionPlanCreateRequest,
    SaaSSubscriptionPlanUpdateRequest,
    now_utc,
)
from services.offer_decision_export_delivery_service import actor_from_user, enum_value, payload_dict


PHASE_LABEL = "phase_39_5_saas_subscription_entitlement_foundation"

PLAN_COLLECTION = "saas_subscription_plans"
ENTITLEMENT_COLLECTION = "saas_plan_entitlements"
ASSIGNMENT_COLLECTION = "agency_subscription_assignments"
READINESS_COLLECTION = "agency_entitlement_readiness"
NOTE_COLLECTION = "agency_subscription_review_notes"
SNAPSHOT_COLLECTION = "agency_subscription_snapshots"


class SaaSSubscriptionService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def platform_summary(self) -> dict[str, Any]:
        plans = await self.list_plans()
        entitlements = await self.list_entitlements()
        assignments = await self.list_assignments()
        readiness = await self.list_readiness()
        notes = await self.list_notes()
        snapshots = await self.list_snapshots()
        return {
            "phase": PHASE_LABEL,
            "plan_count": len(plans),
            "entitlement_count": len(entitlements),
            "assignment_count": len(assignments),
            "readiness_count": len(readiness),
            "note_count": len(notes),
            "snapshot_count": len(snapshots),
            "active_assignment_count": len([item for item in assignments if item.get("assignment_status") == "active"]),
            "manual_review_assignment_count": len([item for item in assignments if item.get("manual_review_required")]),
            "platform_subscription_ui_enabled": True,
            "agency_subscription_visibility_ui_enabled": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        assignments = await self.list_assignments(agency_id=agency_id, agency_view=True)
        readiness = await self.list_readiness(agency_id=agency_id, agency_view=True)
        notes = await self.list_notes(agency_id=agency_id, visible_to_agency=True, agency_view=True)
        snapshots = await self.list_snapshots(agency_id=agency_id, agency_view=True)
        return {
            "phase": PHASE_LABEL,
            "assignment_count": len(assignments),
            "readiness_count": len(readiness),
            "note_count": len(notes),
            "snapshot_count": len(snapshots),
            "active_assignment_count": len([item for item in assignments if item.get("assignment_status") == "active"]),
            "manual_review_required": any(item.get("manual_review_required") for item in assignments + readiness),
            "plain_language_overview": "Your subscription view shows which modules and airline intelligence coverage are assigned to your agency. It is read-only and does not bill, charge, invoice, enforce access, publish, recommend, book, ticket, or issue EMDs.",
            "read_only": True,
            "payloads_hidden": True,
            **self.safety_flags(),
        }

    async def create_plan(self, payload: SaaSSubscriptionPlanCreateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        existing = await self.db.collection(PLAN_COLLECTION).find_one({"plan_code": data["plan_code"]})
        if existing:
            raise ValueError("Subscription plan code already exists.")
        data["created_by"] = data.get("created_by") or actor_from_user(user)
        plan = SaaSSubscriptionPlan(**data)
        stored = await self.db.collection(PLAN_COLLECTION).insert_one(plan.model_dump(mode="json"))
        await self._create_snapshot(None, None, stored["id"], "plan_created", stored.get("created_by"), {"plan": stored})
        return {"plan": stored, **self.safety_flags()}

    async def update_plan(self, plan_id: str, payload: SaaSSubscriptionPlanUpdateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        await self._require_plan(plan_id)
        updates = payload_dict(payload)
        updates["updated_by"] = updates.get("updated_by") or actor_from_user(user)
        updated = await self.db.collection(PLAN_COLLECTION).update_one({"id": plan_id}, updates)
        await self._create_snapshot(None, None, plan_id, "plan_updated", updates["updated_by"], {"plan": updated})
        return {"plan": updated, **self.safety_flags()}

    async def create_entitlement(self, payload: SaaSPlanEntitlementCreateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        await self._require_plan(data["plan_id"])
        entitlement = SaaSPlanEntitlement(**data)
        stored = await self.db.collection(ENTITLEMENT_COLLECTION).insert_one(entitlement.model_dump(mode="json"))
        await self._create_snapshot(None, None, data["plan_id"], "entitlement_created", actor_from_user(user), {"entitlement": stored})
        return {"entitlement": stored, **self.safety_flags()}

    async def create_assignment(self, payload: AgencySubscriptionAssignmentCreateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        plan = await self._require_plan(data["plan_id"])
        data["included_modules"] = data.get("included_modules") or plan.get("included_modules") or []
        data["included_airline_intelligence_domains"] = data.get("included_airline_intelligence_domains") or plan.get("included_airline_intelligence_domains") or []
        data["included_data_pack_channels"] = data.get("included_data_pack_channels") or plan.get("included_data_pack_channels") or []
        data["assigned_by"] = data.get("assigned_by") or actor_from_user(user)
        assignment = AgencySubscriptionAssignment(
            **data,
        )
        stored = await self.db.collection(ASSIGNMENT_COLLECTION).insert_one(assignment.model_dump(mode="json"))
        await self._create_snapshot(stored["agency_id"], stored["id"], stored["plan_id"], "assignment_created", stored.get("assigned_by"), {"assignment": stored})
        return {"assignment": self._assignment_projection(stored), **self.safety_flags()}

    async def update_assignment(self, assignment_id: str, payload: AgencySubscriptionAssignmentUpdateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        assignment = await self._require_assignment(assignment_id)
        updates = payload_dict(payload)
        updates["updated_by"] = updates.get("updated_by") or actor_from_user(user)
        updated = await self.db.collection(ASSIGNMENT_COLLECTION).update_one({"id": assignment_id}, updates)
        result = updated or assignment
        await self._create_snapshot(result["agency_id"], result["id"], result["plan_id"], "assignment_updated", updates["updated_by"], {"assignment": result})
        return {"assignment": self._assignment_projection(result), **self.safety_flags()}

    async def create_readiness(self, payload: AgencyEntitlementReadinessCreateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        if data.get("assignment_id"):
            await self._require_assignment(data["assignment_id"])
        if data.get("plan_id"):
            await self._require_plan(data["plan_id"])
        data["calculated_by"] = data.get("calculated_by") or actor_from_user(user)
        data["calculated_at"] = now_utc()
        readiness = AgencyEntitlementReadiness(
            **data,
        )
        stored = await self.db.collection(READINESS_COLLECTION).insert_one(readiness.model_dump(mode="json"))
        await self._create_snapshot(stored["agency_id"], stored.get("assignment_id"), stored.get("plan_id"), "readiness_recalculated", stored.get("calculated_by"), {"readiness": stored})
        return {"readiness": stored, **self.safety_flags()}

    async def create_note(self, payload: AgencySubscriptionReviewNoteCreateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        if data.get("assignment_id"):
            await self._require_assignment(data["assignment_id"])
        if data.get("plan_id"):
            await self._require_plan(data["plan_id"])
        data["created_by"] = data.get("created_by") or actor_from_user(user)
        note = AgencySubscriptionReviewNote(**data)
        stored = await self.db.collection(NOTE_COLLECTION).insert_one(note.model_dump(mode="json"))
        await self._create_snapshot(stored["agency_id"], stored.get("assignment_id"), stored.get("plan_id"), "note_created", stored.get("created_by"), {"note_id": stored["id"], "visible_to_agency": stored.get("visible_to_agency")})
        return {"note": stored, **self.safety_flags()}

    async def create_snapshot(self, payload: AgencySubscriptionSnapshotCreateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        if data.get("assignment_id"):
            await self._require_assignment(data["assignment_id"])
        if data.get("plan_id"):
            await self._require_plan(data["plan_id"])
        snapshot = await self._create_snapshot(
            data.get("agency_id"),
            data.get("assignment_id"),
            data.get("plan_id"),
            data.get("snapshot_type") or "manual",
            data.get("created_by") or actor_from_user(user),
            data.get("snapshot_json") or {},
        )
        return {"snapshot": snapshot, **self.safety_flags()}

    async def list_plans(self, *, status: str | None = None, agency_view: bool = False) -> list[dict[str, Any]]:
        filters = {"status": status} if status else None
        plans = await self.db.collection(PLAN_COLLECTION).find_many(filters)
        plans.sort(key=lambda item: (item.get("tier") or "", item.get("plan_name") or ""))
        return [self._plan_projection(item, agency_view=agency_view) for item in plans]

    async def list_entitlements(self, *, plan_id: str | None = None, agency_view: bool = False) -> list[dict[str, Any]]:
        filters = {"plan_id": plan_id} if plan_id else None
        entitlements = await self.db.collection(ENTITLEMENT_COLLECTION).find_many(filters)
        entitlements.sort(key=lambda item: (item.get("entitlement_scope") or "", item.get("entitlement_key") or ""))
        return [self._entitlement_projection(item, agency_view=agency_view) for item in entitlements]

    async def list_assignments(self, *, agency_id: str | None = None, agency_view: bool = False) -> list[dict[str, Any]]:
        filters = {"agency_id": agency_id} if agency_id else None
        assignments = await self.db.collection(ASSIGNMENT_COLLECTION).find_many(filters)
        assignments.sort(key=lambda item: self._timestamp_sort_value(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [self._assignment_projection(item, agency_view=agency_view) for item in assignments]

    async def list_readiness(self, *, agency_id: str | None = None, assignment_id: str | None = None, agency_view: bool = False) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if assignment_id:
            filters["assignment_id"] = assignment_id
        readiness = await self.db.collection(READINESS_COLLECTION).find_many(filters or None)
        readiness.sort(key=lambda item: (item.get("status") or "", item.get("entitlement_key") or ""))
        return [self._readiness_projection(item, agency_view=agency_view) for item in readiness]

    async def list_notes(self, *, agency_id: str | None = None, assignment_id: str | None = None, visible_to_agency: bool | None = None, agency_view: bool = False) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if assignment_id:
            filters["assignment_id"] = assignment_id
        if visible_to_agency is not None:
            filters["visible_to_agency"] = visible_to_agency
        notes = await self.db.collection(NOTE_COLLECTION).find_many(filters or None)
        notes.sort(key=lambda item: self._timestamp_sort_value(item.get("created_at")), reverse=True)
        return [self._note_projection(item, agency_view=agency_view) for item in notes if not agency_view or item.get("visible_to_agency")]

    async def list_snapshots(self, *, agency_id: str | None = None, assignment_id: str | None = None, agency_view: bool = False) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if assignment_id:
            filters["assignment_id"] = assignment_id
        snapshots = await self.db.collection(SNAPSHOT_COLLECTION).find_many(filters or None)
        snapshots.sort(key=lambda item: self._timestamp_sort_value(item.get("created_at")), reverse=True)
        return [self._snapshot_projection(item, agency_view=agency_view) for item in snapshots]

    async def _require_plan(self, plan_id: str) -> dict[str, Any]:
        plan = await self.db.collection(PLAN_COLLECTION).find_one({"id": plan_id})
        if not plan:
            raise ValueError("SaaS subscription plan not found.")
        return plan

    async def _require_assignment(self, assignment_id: str) -> dict[str, Any]:
        assignment = await self.db.collection(ASSIGNMENT_COLLECTION).find_one({"id": assignment_id})
        if not assignment:
            raise ValueError("Agency subscription assignment not found.")
        return assignment

    async def _create_snapshot(self, agency_id: str | None, assignment_id: str | None, plan_id: str | None, snapshot_type: str, actor: str | None, payload: dict[str, Any]) -> dict[str, Any]:
        snapshot = AgencySubscriptionSnapshot(
            agency_id=agency_id,
            assignment_id=assignment_id,
            plan_id=plan_id,
            snapshot_type=enum_value(snapshot_type),
            snapshot_json={"metadata_only": True, **(payload or {})},
            created_by=actor,
        )
        return await self.db.collection(SNAPSHOT_COLLECTION).insert_one(snapshot.model_dump(mode="json"))

    def _plan_projection(self, plan: dict[str, Any], *, agency_view: bool = False) -> dict[str, Any]:
        projected = dict(plan)
        projected.update({"metadata_only": True, "billing_disabled": True, "payment_disabled": True})
        if agency_view:
            projected.pop("created_by", None)
            projected.pop("updated_by", None)
        return projected

    def _entitlement_projection(self, entitlement: dict[str, Any], *, agency_view: bool = False) -> dict[str, Any]:
        projected = dict(entitlement)
        projected["metadata_only"] = True
        if agency_view:
            projected.pop("manual_review_required", None)
        return projected

    def _assignment_projection(self, assignment: dict[str, Any], *, agency_view: bool = False) -> dict[str, Any]:
        projected = dict(assignment)
        projected.update({"metadata_only": True, "automatic_access_enforcement_disabled": True})
        if agency_view:
            projected.pop("assigned_by", None)
            projected.pop("updated_by", None)
        return projected

    def _readiness_projection(self, readiness: dict[str, Any], *, agency_view: bool = False) -> dict[str, Any]:
        projected = dict(readiness)
        projected.update({"metadata_only": True, "automatic_access_enforcement_disabled": True})
        if agency_view:
            projected.pop("calculated_by", None)
        return projected

    def _note_projection(self, note: dict[str, Any], *, agency_view: bool = False) -> dict[str, Any]:
        projected = dict(note)
        projected["metadata_only"] = True
        if agency_view:
            projected.pop("created_by", None)
            projected.pop("visible_to_agency", None)
        return projected

    def _snapshot_projection(self, snapshot: dict[str, Any], *, agency_view: bool = False) -> dict[str, Any]:
        projected = dict(snapshot)
        projected.update({"immutable": True, "metadata_only": True})
        if agency_view:
            projected.pop("created_by", None)
            payload = projected.get("snapshot_json") or {}
            projected["plain_language_summary"] = payload.get("plain_language_summary") or payload.get("summary") or "Subscription metadata snapshot."
            projected["snapshot_json"] = {"metadata_only": True, "payloads_hidden": True}
        return projected

    def _timestamp_sort_value(self, value: Any) -> str:
        if value is None:
            return ""
        return value.isoformat() if hasattr(value, "isoformat") else str(value)

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only_subscription_enabled": True,
            "billing_disabled": True,
            "payment_disabled": True,
            "invoice_disabled": True,
            "settlement_disabled": True,
            "automatic_access_enforcement_disabled": True,
            "cms_publishing_disabled": True,
            "client_portal_publishing_disabled": True,
            "recommendation_disabled": True,
            "provider_execution_disabled": True,
            "booking_execution_disabled": True,
            "pnr_mutation_disabled": True,
            "ticketing_disabled": True,
            "emd_issuance_disabled": True,
            "scraping_disabled": True,
            "external_api_calls_disabled": True,
            "external_ai_disabled": True,
            "automatic_sending_disabled": True,
        }
