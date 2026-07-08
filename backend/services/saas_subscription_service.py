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


PHASE_LABEL = "phase_41_9_ssr_osi_operational_workspace_foundation"

PLAN_COLLECTION = "saas_subscription_plans"
ENTITLEMENT_COLLECTION = "saas_plan_entitlements"
ASSIGNMENT_COLLECTION = "agency_subscription_assignments"
READINESS_COLLECTION = "agency_entitlement_readiness"
NOTE_COLLECTION = "agency_subscription_review_notes"
SNAPSHOT_COLLECTION = "agency_subscription_snapshots"

VISIBILITY_STATUSES = {"included", "limited", "not_included", "review_required", "unknown"}

AGENCY_MODULE_VISIBILITY_CATALOG: list[dict[str, Any]] = [
    {"key": "dashboard", "label": "Dashboard", "href": "/agency", "aliases": ["workspace_core", "dashboard"]},
    {"key": "requests", "label": "Requests", "href": "/agency/requests", "aliases": ["requests", "request_builder", "daily_work"]},
    {"key": "request_intakes", "label": "Intakes", "href": "/agency/request-intakes", "aliases": ["intakes", "request_intakes", "daily_work"]},
    {"key": "gds_parser", "label": "GDS Parser", "href": "/agency/gds-parser", "aliases": ["gds_parser", "gds"]},
    {"key": "crm", "label": "Clients & Passengers", "href": "/agency/clients", "aliases": ["crm", "clients", "passengers"]},
    {"key": "client_portal", "label": "Portal Actions", "href": "/agency/portal-actions", "aliases": ["client_portal", "portal_actions"]},
    {"key": "trips", "label": "Trips", "href": "/agency/trips", "aliases": ["trips", "trip_dossier"]},
    {"key": "offers", "label": "Offers", "href": "/agency/offers", "aliases": ["offers", "offer_builder"]},
    {"key": "booking_workspaces", "label": "Booking Workspaces", "href": "/agency/booking-workspaces", "aliases": ["booking_workspaces", "booking_foundation"]},
    {"key": "booking_imports", "label": "Booking Imports", "href": "/agency/booking-imports", "aliases": ["booking_imports", "gds_imports"]},
    {"key": "tickets_emds", "label": "Tickets & EMDs", "href": "/agency/tickets-emds", "aliases": ["tickets_emds", "ticketing", "emd_issuance"]},
    {"key": "refunds_exchanges", "label": "Refunds & Exchanges", "href": "/agency/refunds-exchanges", "aliases": ["refunds_exchanges", "service_cases"]},
    {"key": "cms", "label": "Website / CMS", "href": "/agency/website", "aliases": ["cms", "website", "website_cms"]},
    {"key": "cms_media", "label": "CMS Media", "href": "/agency/website/media", "aliases": ["cms_media", "media_library", "cms"]},
    {"key": "airline_intelligence", "label": "Airline Intelligence", "href": "/agency/airline-policy-library", "aliases": ["airline_intelligence", "policies", "service_mechanics", "service_taxonomy"]},
    {"key": "airline_coverage", "label": "Airline Coverage", "href": "/agency/airline-intelligence-coverage", "aliases": ["airline_coverage", "data_pack_coverage", "airline_intelligence"]},
    {"key": "knowledge_versions", "label": "Knowledge Versions", "href": "/agency/airline-intelligence-knowledge-versions", "aliases": ["knowledge_versions", "airline_intelligence"]},
    {"key": "airline_intelligence_consumption", "label": "Airline Intelligence Usage", "href": "/agency/airline-intelligence-consumption", "aliases": ["airline_intelligence_consumption", "usage_readiness", "airline_intelligence"]},
    {"key": "service_taxonomy", "label": "Service Taxonomy", "href": "/agency/service-taxonomy", "aliases": ["service_taxonomy", "airline_intelligence"]},
    {"key": "service_mechanics", "label": "Service Mechanics", "href": "/agency/service-mechanics", "aliases": ["service_mechanics", "airline_intelligence"]},
    {"key": "ancillary_pricing", "label": "Ancillary Pricing", "href": "/agency/ancillary-pricing", "aliases": ["ancillary_pricing", "airline_intelligence"]},
    {"key": "policy_comparison", "label": "Policy Comparison", "href": "/agency/policy-comparison", "aliases": ["policy_comparison", "airline_intelligence"]},
    {"key": "airline_service_advisor", "label": "Service Advisor", "href": "/agency/airline-service-advisor", "aliases": ["airline_service_advisor", "policy_advisor", "airline_intelligence"]},
    {"key": "offer_policy_advisor", "label": "Offer Advisor", "href": "/agency/offer-policy-advisor", "aliases": ["offer_policy_advisor", "offer_builder"]},
    {"key": "documents", "label": "Documents", "href": "/agency/documents", "aliases": ["documents", "document_foundation"]},
    {"key": "offer_decision_evidence", "label": "Offer Decision Evidence", "href": "/agency/offer-decision-packs", "aliases": ["offer_decision_evidence", "decision_packs", "documents"]},
    {"key": "offer_exports", "label": "Decision Exports", "href": "/agency/offer-decision-exports", "aliases": ["offer_exports", "export_previews", "documents"]},
    {"key": "manual_delivery", "label": "Manual Delivery", "href": "/agency/offer-decision-export-deliveries", "aliases": ["manual_delivery", "export_handoffs", "documents"]},
    {"key": "settings", "label": "Settings", "href": "/agency/settings", "aliases": ["settings", "workspace_core"]},
    {"key": "subscription", "label": "My Subscription", "href": "/agency/saas-subscription", "aliases": ["subscription", "saas_subscription", "workspace_core"]},
    {"key": "reference_data", "label": "Reference Data", "href": "/agency/reference", "aliases": ["reference_data", "reference"]},
    {"key": "form_profiles", "label": "Form Profiles", "href": "/agency/settings/forms", "aliases": ["form_profiles", "settings"]},
]


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
            "entitlement_visibility_enabled": True,
            "read_only_guardrail_ui_enabled": True,
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
            "entitlement_visibility_enabled": True,
            "read_only_guardrail_ui_enabled": True,
            **self.safety_flags(),
        }

    async def agency_module_visibility(self, agency_id: str) -> dict[str, Any]:
        assignments = await self.db.collection(ASSIGNMENT_COLLECTION).find_many({"agency_id": agency_id})
        readiness = await self.db.collection(READINESS_COLLECTION).find_many({"agency_id": agency_id})
        plan_ids = {item.get("plan_id") for item in assignments if item.get("plan_id")}
        plans = [item for item in await self.db.collection(PLAN_COLLECTION).find_many() if item.get("id") in plan_ids]
        entitlements = [item for item in await self.db.collection(ENTITLEMENT_COLLECTION).find_many() if item.get("plan_id") in plan_ids]
        modules = [
            self._module_visibility(module, assignments, plans, entitlements, readiness)
            for module in AGENCY_MODULE_VISIBILITY_CATALOG
        ]
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "modules": modules,
            "visibility_by_key": {item["key"]: item for item in modules},
            "status_counts": self._status_counts(modules),
            "assignment_count": len(assignments),
            "readiness_count": len(readiness),
            "informational_only": True,
            "read_only": True,
            "payloads_hidden": True,
            "notice": "Subscription visibility is informational only and does not automatically enforce access.",
            **self.ui_guardrail_flags(),
        }

    async def platform_entitlement_visibility(self, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"agency_id": agency_id} if agency_id else None
        assignments = await self.db.collection(ASSIGNMENT_COLLECTION).find_many(filters)
        assigned_agency_ids = {item.get("agency_id") for item in assignments if item.get("agency_id")}
        if agency_id:
            agency_ids = {agency_id}
        else:
            agencies = await self.db.collection("agencies").find_many()
            agency_ids = assigned_agency_ids | {item.get("id") for item in agencies if item.get("id")}
        agency_names = {
            item.get("id"): item.get("name") or item.get("legal_name") or item.get("id")
            for item in await self.db.collection("agencies").find_many()
        }
        items: list[dict[str, Any]] = []
        for current_agency_id in sorted(agency_ids):
            visibility = await self.agency_module_visibility(current_agency_id)
            agency_assignments = [item for item in assignments if item.get("agency_id") == current_agency_id]
            if not agency_assignments:
                agency_assignments = await self.db.collection(ASSIGNMENT_COLLECTION).find_many({"agency_id": current_agency_id})
            latest_assignment = self._latest_assignment(agency_assignments)
            items.append(
                {
                    "agency_id": current_agency_id,
                    "agency_name": agency_names.get(current_agency_id) or current_agency_id,
                    "assignment_id": latest_assignment.get("id") if latest_assignment else None,
                    "plan_id": latest_assignment.get("plan_id") if latest_assignment else None,
                    "assignment_status": latest_assignment.get("assignment_status") if latest_assignment else "unknown",
                    "manual_review_required": bool(latest_assignment and latest_assignment.get("manual_review_required")),
                    "status_counts": visibility["status_counts"],
                    "modules": visibility["modules"],
                    "notice": visibility["notice"],
                    "metadata_only": True,
                    "read_only": True,
                    "automatic_access_enforcement_disabled": True,
                }
            )
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "agency_count": len(items),
            "informational_only": True,
            "read_only": True,
            "owner_review_metadata_only": True,
            **self.ui_guardrail_flags(),
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

    def _latest_assignment(self, assignments: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not assignments:
            return None
        return sorted(
            assignments,
            key=lambda item: self._timestamp_sort_value(item.get("updated_at") or item.get("created_at")),
            reverse=True,
        )[0]

    def _module_visibility(
        self,
        module: dict[str, Any],
        assignments: list[dict[str, Any]],
        plans: list[dict[str, Any]],
        entitlements: list[dict[str, Any]],
        readiness: list[dict[str, Any]],
    ) -> dict[str, Any]:
        aliases = {module["key"], *(module.get("aliases") or [])}
        plan_by_id = {item.get("id"): item for item in plans}
        active_assignments = [
            item
            for item in assignments
            if enum_value(item.get("assignment_status")) not in {"cancelled", "expired"}
        ]
        matching_readiness = [
            item
            for item in readiness
            if enum_value(item.get("entitlement_key")) in aliases
            or enum_value(item.get("entitlement_scope")) in aliases
        ]
        matching_entitlements = [
            item
            for item in entitlements
            if enum_value(item.get("entitlement_key")) in aliases
            or any(self._flag_enabled(item.get("visibility_flags"), alias) for alias in aliases)
        ]
        included_by_assignment = any(
            self._module_list_includes(item.get("included_modules"), aliases)
            or any(self._flag_enabled(item.get("visibility_flags"), alias) for alias in aliases)
            for item in active_assignments
        )
        included_by_plan = any(
            self._module_list_includes(plan_by_id.get(item.get("plan_id"), {}).get("included_modules"), aliases)
            or any(self._flag_enabled(plan_by_id.get(item.get("plan_id"), {}).get("visibility_flags"), alias) for alias in aliases)
            for item in active_assignments
        )
        included_by_entitlement = any(item.get("included", True) is True for item in matching_entitlements)
        explicitly_not_included = any(item.get("included") is False for item in matching_entitlements)
        has_assignment = bool(assignments)
        included = included_by_assignment or included_by_plan or included_by_entitlement
        review_required = any(item.get("manual_review_required") for item in active_assignments + matching_readiness + matching_entitlements)
        review_required = review_required or any(enum_value(item.get("assignment_status")) == "review" for item in active_assignments)
        readiness_statuses = {enum_value(item.get("status")) for item in matching_readiness if item.get("status")}
        if "needs_review" in readiness_statuses:
            review_required = True

        if not has_assignment:
            status = "unknown"
            reason = "No subscription assignment metadata is available for this agency."
        elif review_required:
            status = "review_required"
            reason = "Platform review metadata is present for this entitlement."
        elif included and ("not_ready" in readiness_statuses or "blocked" in readiness_statuses):
            status = "limited"
            reason = "The entitlement is assigned, but readiness metadata indicates a limited or blocked state."
        elif included:
            status = "included"
            reason = "The current subscription metadata includes this module."
        elif explicitly_not_included or has_assignment:
            status = "not_included"
            reason = "The current subscription metadata does not include this module."
        else:
            status = "unknown"
            reason = "Subscription metadata does not describe this module yet."

        if status not in VISIBILITY_STATUSES:
            status = "unknown"
        return {
            "key": module["key"],
            "label": module["label"],
            "href": module.get("href"),
            "status": status,
            "badge": self._visibility_badge(status),
            "reason": reason,
            "matching_entitlement_count": len(matching_entitlements),
            "matching_readiness_count": len(matching_readiness),
            "included": status == "included",
            "limited": status == "limited",
            "review_required": status == "review_required",
            "not_included": status == "not_included",
            "unknown": status == "unknown",
            "informational_only": True,
            "automatic_access_enforcement_disabled": True,
        }

    def _module_list_includes(self, values: list[str] | None, aliases: set[str]) -> bool:
        normalized_values = {enum_value(value) for value in values or []}
        return bool(normalized_values & aliases)

    def _flag_enabled(self, flags: dict[str, Any] | None, key: str) -> bool:
        return bool((flags or {}).get(key))

    def _visibility_badge(self, status: str) -> str:
        return {
            "included": "Included",
            "limited": "Limited",
            "not_included": "Not included",
            "review_required": "Review required",
            "unknown": "Unknown",
        }.get(status, "Unknown")

    def _status_counts(self, modules: list[dict[str, Any]]) -> dict[str, int]:
        return {status: len([item for item in modules if item.get("status") == status]) for status in sorted(VISIBILITY_STATUSES)}

    def ui_guardrail_flags(self) -> dict[str, bool]:
        return {
            "entitlement_visibility_enabled": True,
            "agency_navigation_badges_enabled": True,
            "platform_entitlement_review_enabled": True,
            "read_only_guardrail_ui_enabled": True,
            "automatic_enforcement_disabled": True,
            "billing_disabled": True,
            "payment_invoice_settlement_disabled": True,
            "provider_execution_disabled": True,
            "booking_execution_disabled": True,
            "pnr_mutation_disabled": True,
            "ticketing_disabled": True,
            "emd_issuance_disabled": True,
            "external_api_calls_disabled": True,
            "external_ai_disabled": True,
            "scraping_disabled": True,
            "automatic_sending_disabled": True,
        }

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
