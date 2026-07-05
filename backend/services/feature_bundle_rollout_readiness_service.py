from __future__ import annotations

from typing import Any

from database import Database
from models import (
    FeatureBundleRolloutChecklistItem,
    FeatureBundleRolloutReadiness,
    now_utc,
)
from services.agency_feature_flag_bundle_service import AgencyFeatureFlagBundleService
from services.offer_decision_export_delivery_service import actor_from_user


PHASE_LABEL = "phase_40_8_feature_bundle_rollout_risk_register_foundation"

READINESS_COLLECTION = "agency_feature_bundle_rollout_readiness"
ASSIGNMENT_COLLECTION = "agency_feature_bundle_assignments"
READINESS_STATUSES = ["draft", "reviewing", "ready", "blocked"]
CHECKLIST_STATUSES = ["pending", "passed", "warning", "blocked"]


class FeatureBundleRolloutReadinessService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_platform_readiness(
        self,
        *,
        agency_id: str | None = None,
        readiness_status: str | None = None,
        include_defaults: bool = True,
    ) -> list[dict[str, Any]]:
        items = await self._merged_readiness(agency_id=agency_id, include_defaults=include_defaults)
        if readiness_status:
            items = [item for item in items if item.get("readiness_status") == readiness_status]
        items.sort(key=lambda item: (item.get("agency_name") or "", item.get("bundle_name") or "", item.get("assignment_id") or ""))
        return [self._platform_projection(item) for item in items]

    async def list_agency_readiness(self, agency_id: str, *, readiness_status: str | None = None) -> list[dict[str, Any]]:
        items = await self.list_platform_readiness(agency_id=agency_id, readiness_status=readiness_status)
        return [self._agency_projection(item, agency_id) for item in items]

    async def platform_response(self, *, agency_id: str | None = None, readiness_status: str | None = None) -> dict[str, Any]:
        items = await self.list_platform_readiness(agency_id=agency_id, readiness_status=readiness_status)
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "readiness_count": len(items),
            "summary": self.summarize_counts(items),
            "read_only": False,
            "metadata_only": True,
            "notice": "Rollout readiness is metadata only. It does not activate, deactivate, allow, or block features.",
            **self.safety_flags(),
        }

    async def agency_response(self, agency_id: str, *, readiness_status: str | None = None) -> dict[str, Any]:
        items = await self.list_agency_readiness(agency_id, readiness_status=readiness_status)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "readiness_count": len(items),
            "summary": self.summarize_counts(items),
            "read_only": True,
            "metadata_only": True,
            "notice": "Bundle rollout readiness is read-only metadata for this agency. It does not activate or block features.",
            **self.safety_flags(),
        }

    async def platform_summary(self, *, agency_id: str | None = None) -> dict[str, Any]:
        items = await self.list_platform_readiness(agency_id=agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(items),
            "readiness_count": len(items),
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        items = await self.list_agency_readiness(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(items),
            "readiness_count": len(items),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def create_default_readiness_records(
        self,
        *,
        agency_id: str | None = None,
        user: dict | None = None,
    ) -> dict[str, Any]:
        assignments = await self._assignments(agency_id=agency_id)
        existing = await self.db.collection(READINESS_COLLECTION).find_many({"agency_id": agency_id} if agency_id else None)
        existing_assignment_ids = {item.get("assignment_id") for item in existing}
        created: list[dict[str, Any]] = []
        actor = actor_from_user(user)
        for assignment in assignments:
            assignment_id = assignment.get("assignment_id") or assignment.get("id")
            if not assignment_id or assignment_id in existing_assignment_ids:
                continue
            checklist = await self._default_checklist(assignment)
            readiness = FeatureBundleRolloutReadiness(
                agency_id=assignment.get("agency_id") or "",
                bundle_id=assignment.get("bundle_id") or "",
                assignment_id=assignment_id,
                readiness_status=self._derive_status(checklist, assignment),
                checklist_items=[FeatureBundleRolloutChecklistItem(**item) for item in checklist],
                notes="Default rollout readiness metadata generated from the assigned feature bundle record.",
                reviewed_by=actor,
                reviewed_at=now_utc(),
                metadata_only=True,
                activation_logic_disabled=True,
                feature_access_enforcement_disabled=True,
                billing_disabled=True,
                provider_execution_disabled=True,
            )
            stored = await self.db.collection(READINESS_COLLECTION).insert_one(readiness.model_dump(mode="json"))
            created.append(await self._record_projection(stored))
            existing_assignment_ids.add(assignment_id)
        return {
            "phase": PHASE_LABEL,
            "created_count": len(created),
            "items": [self._platform_projection(item) for item in created],
            "metadata_only": True,
            "notice": "Default readiness records were created as metadata only. No feature activation or access enforcement was performed.",
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        readiness_counts = {status: 0 for status in READINESS_STATUSES}
        checklist_counts = {status: 0 for status in CHECKLIST_STATUSES}
        warning_count = 0
        blocker_count = 0
        for item in items:
            status = item.get("readiness_status") or "draft"
            readiness_counts[status] = readiness_counts.get(status, 0) + 1
            counts = item.get("checklist_counts") or self._checklist_counts(item.get("checklist_items") or [])
            for checklist_status in CHECKLIST_STATUSES:
                checklist_counts[checklist_status] = checklist_counts.get(checklist_status, 0) + counts.get(checklist_status, 0)
            warning_count += len(item.get("warnings") or [])
            blocker_count += len(item.get("blockers") or [])
        return {
            "by_readiness_status": readiness_counts,
            "by_checklist_status": checklist_counts,
            "warning_count": warning_count,
            "blocker_count": blocker_count,
            "metadata_only": True,
        }

    async def _merged_readiness(self, *, agency_id: str | None = None, include_defaults: bool = True) -> list[dict[str, Any]]:
        filters = {"agency_id": agency_id} if agency_id else None
        stored = await self.db.collection(READINESS_COLLECTION).find_many(filters)
        items = [await self._record_projection(item) for item in stored]
        if not include_defaults:
            return items

        existing_assignment_ids = {item.get("assignment_id") for item in items}
        for assignment in await self._assignments(agency_id=agency_id):
            assignment_id = assignment.get("assignment_id") or assignment.get("id")
            if not assignment_id or assignment_id in existing_assignment_ids:
                continue
            items.append(await self._default_projection(assignment))
        return items

    async def _assignments(self, *, agency_id: str | None = None) -> list[dict[str, Any]]:
        filters = {"agency_id": agency_id} if agency_id else None
        return await self.db.collection(ASSIGNMENT_COLLECTION).find_many(filters)

    async def _default_projection(self, assignment: dict[str, Any]) -> dict[str, Any]:
        checklist = await self._default_checklist(assignment)
        projected = {
            "id": f"default_rollout_readiness_{assignment.get('assignment_id') or assignment.get('id')}",
            "agency_id": assignment.get("agency_id"),
            "bundle_id": assignment.get("bundle_id"),
            "assignment_id": assignment.get("assignment_id") or assignment.get("id"),
            "readiness_status": self._derive_status(checklist, assignment),
            "checklist_items": checklist,
            "notes": "Default rollout readiness view generated from assignment metadata.",
            "reviewed_by": None,
            "reviewed_at": None,
            "created_at": assignment.get("created_at"),
            "updated_at": assignment.get("updated_at"),
            "default_view": True,
            "stored_record": False,
            "metadata_only": True,
            "activation_logic_disabled": True,
            "feature_access_enforcement_disabled": True,
            "billing_disabled": True,
            "provider_execution_disabled": True,
        }
        return await self._add_context(projected, assignment)

    async def _record_projection(self, record: dict[str, Any]) -> dict[str, Any]:
        assignment = await self.db.collection(ASSIGNMENT_COLLECTION).find_one({"assignment_id": record.get("assignment_id")})
        projected = dict(record)
        projected["default_view"] = False
        projected["stored_record"] = True
        projected["metadata_only"] = True
        projected["activation_logic_disabled"] = True
        projected["feature_access_enforcement_disabled"] = True
        projected["billing_disabled"] = True
        projected["provider_execution_disabled"] = True
        return await self._add_context(projected, assignment or {})

    async def _add_context(self, projected: dict[str, Any], assignment: dict[str, Any]) -> dict[str, Any]:
        agency = await self.db.collection("agencies").find_one({"id": projected.get("agency_id")})
        bundle = await AgencyFeatureFlagBundleService(self.db).get_bundle(projected.get("bundle_id") or "")
        projected["agency"] = {
            "agency_id": agency.get("id"),
            "agency_name": agency.get("name"),
            "agency_slug": agency.get("slug"),
        } if agency else {"agency_id": projected.get("agency_id"), "agency_name": projected.get("agency_id"), "agency_slug": None}
        projected["agency_name"] = projected["agency"].get("agency_name")
        projected["bundle"] = {
            "bundle_id": bundle.get("bundle_id"),
            "bundle_key": bundle.get("bundle_key"),
            "bundle_name": bundle.get("bundle_name"),
            "category": bundle.get("category"),
        } if bundle else {
            "bundle_id": projected.get("bundle_id"),
            "bundle_key": projected.get("bundle_id"),
            "bundle_name": projected.get("bundle_id"),
            "category": None,
        }
        projected["bundle_name"] = projected["bundle"].get("bundle_name")
        projected["bundle_key"] = projected["bundle"].get("bundle_key")
        projected["assignment"] = {
            "assignment_id": projected.get("assignment_id"),
            "status": assignment.get("status"),
            "review_status": assignment.get("review_status"),
            "effective_date": assignment.get("effective_date"),
            "expiration_date": assignment.get("expiration_date"),
            "notes": assignment.get("notes"),
            "metadata_only": True,
        }
        projected["checklist_counts"] = self._checklist_counts(projected.get("checklist_items") or [])
        projected["warnings"] = self._checklist_labels(projected.get("checklist_items") or [], "warning")
        projected["blockers"] = self._checklist_labels(projected.get("checklist_items") or [], "blocked")
        projected.update(self.safety_flags())
        return projected

    async def _default_checklist(self, assignment: dict[str, Any]) -> list[dict[str, Any]]:
        bundle = await AgencyFeatureFlagBundleService(self.db).get_bundle(assignment.get("bundle_id") or "")
        assignment_review_status = assignment.get("review_status") or "pending_review"
        assignment_status = assignment.get("status") or "assigned"
        checklist = [
            {
                "item_key": "assignment_metadata",
                "label": "Assignment metadata",
                "status": "passed" if assignment.get("agency_id") and assignment.get("bundle_id") else "blocked",
                "notes": "Agency, bundle, and assignment identifiers are present." if assignment.get("agency_id") and assignment.get("bundle_id") else "Assignment metadata is incomplete.",
                "metadata_only": True,
            },
            {
                "item_key": "bundle_metadata",
                "label": "Bundle metadata",
                "status": "passed" if bundle else "blocked",
                "notes": "Feature bundle metadata was found." if bundle else "The referenced bundle metadata could not be found.",
                "metadata_only": True,
            },
            {
                "item_key": "assignment_review",
                "label": "Assignment review",
                "status": "passed" if assignment_review_status in {"reviewed", "approved"} else "warning",
                "notes": f"Assignment review status is {assignment_review_status}.",
                "metadata_only": True,
            },
            {
                "item_key": "assignment_status",
                "label": "Assignment status",
                "status": "blocked" if assignment_status == "inactive" else "warning" if assignment_status == "paused" else "passed",
                "notes": f"Assignment status is {assignment_status}; this is informational only.",
                "metadata_only": True,
            },
            {
                "item_key": "launch_window_metadata",
                "label": "Launch window metadata",
                "status": "passed" if assignment.get("effective_date") else "warning",
                "notes": "Effective date is recorded." if assignment.get("effective_date") else "No future effective date is recorded yet.",
                "metadata_only": True,
            },
            {
                "item_key": "rollout_boundary",
                "label": "Rollout safety boundary",
                "status": "passed",
                "notes": "Readiness metadata does not activate, deactivate, allow, or block features.",
                "metadata_only": True,
            },
        ]
        return checklist

    def _derive_status(self, checklist: list[dict[str, Any]], assignment: dict[str, Any]) -> str:
        statuses = {item.get("status") for item in checklist}
        if "blocked" in statuses or assignment.get("status") == "inactive":
            return "blocked"
        if "warning" in statuses or "pending" in statuses:
            return "reviewing"
        return "ready"

    def _checklist_counts(self, checklist: list[dict[str, Any]]) -> dict[str, int]:
        counts = {status: 0 for status in CHECKLIST_STATUSES}
        for item in checklist:
            status = item.get("status") or "pending"
            counts[status] = counts.get(status, 0) + 1
        return counts

    def _checklist_labels(self, checklist: list[dict[str, Any]], status: str) -> list[dict[str, Any]]:
        return [
            {
                "item_key": item.get("item_key"),
                "label": item.get("label"),
                "notes": item.get("notes"),
            }
            for item in checklist
            if item.get("status") == status
        ]

    def _platform_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
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

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "activation_logic_disabled": True,
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
            "scraping_disabled": True,
            "publishing_disabled": True,
            "background_workers_disabled": True,
            "cron_disabled": True,
        }
