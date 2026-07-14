from __future__ import annotations

from typing import Any

from database import Database
from models import (
    AgencyFeatureFlag,
    AgencyFeatureFlagCreateRequest,
    AgencyFeatureFlagReview,
    AgencyFeatureFlagReviewCreateRequest,
    AgencyFeatureFlagSnapshot,
    AgencyFeatureFlagSnapshotCreateRequest,
    AgencyFeatureFlagUpdateRequest,
    now_utc,
)
from services.offer_decision_export_delivery_service import actor_from_user, enum_value, payload_dict
from services.agency_feature_flag_audit_service import AgencyFeatureFlagAuditService


PHASE_LABEL = "phase_54_7_servicing_after_sales_workflow_foundation"

FLAG_COLLECTION = "agency_feature_flags"
REVIEW_COLLECTION = "agency_feature_flag_reviews"
SNAPSHOT_COLLECTION = "agency_feature_flag_snapshots"

FEATURE_FLAG_STATES = ["enabled", "disabled", "hidden", "beta", "pilot"]


class AgencyFeatureFlagService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def platform_summary(self, agency_id: str | None = None) -> dict[str, Any]:
        flags = await self.list_flags(agency_id=agency_id)
        reviews = await self.list_reviews(agency_id=agency_id)
        snapshots = await self.list_snapshots(agency_id=agency_id)
        agency_ids = {item.get("agency_id") for item in flags + reviews + snapshots if item.get("agency_id")}
        return {
            "phase": PHASE_LABEL,
            "flag_count": len(flags),
            "review_count": len(reviews),
            "snapshot_count": len(snapshots),
            "agency_count": len(agency_ids),
            "state_counts": self._state_counts(flags),
            "platform_review_enabled": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        flags = await self.list_flags(agency_id=agency_id, agency_view=True)
        reviews = await self.list_reviews(agency_id=agency_id, agency_view=True)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "flag_count": len(flags),
            "review_count": len(reviews),
            "state_counts": self._state_counts(flags),
            "read_only": True,
            "payloads_hidden": True,
            "notice": "Feature visibility is informational only. Operational enforcement is not performed.",
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def create_flag(self, payload: AgencyFeatureFlagCreateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        existing = await self.db.collection(FLAG_COLLECTION).find_one(
            {"agency_id": data["agency_id"], "module_key": data["module_key"], "feature_key": data["feature_key"]}
        )
        actor = actor_from_user(user)
        if existing:
            updates = {
                "module_key": data["module_key"],
                "feature_key": data["feature_key"],
                "display_name": data["display_name"],
                "state": data.get("state", "disabled"),
                "visibility_note": data.get("visibility_note"),
                "metadata_only": True,
                "automatic_enforcement_disabled": True,
            }
            updated = await self.db.collection(FLAG_COLLECTION).update_one(
                {"id": existing["id"]},
                updates,
            )
            stored = updated or existing
            previous_state = existing.get("state")
            reason = "feature_flag_visibility_updated"
        else:
            flag = AgencyFeatureFlag(**data)
            stored = await self.db.collection(FLAG_COLLECTION).insert_one(flag.model_dump(mode="json"))
            previous_state = None
            reason = "feature_flag_visibility_created"
        audit_service = AgencyFeatureFlagAuditService(self.db)
        await audit_service.ensure_readiness(agency_id=data["agency_id"], feature_key=data["feature_key"], reviewed_by=actor)
        await audit_service.record_audit(
            agency_id=data["agency_id"],
            feature_key=data["feature_key"],
            previous_state=previous_state,
            proposed_state=stored.get("state") or data.get("state") or "disabled",
            changed_by=actor,
            reason=reason,
            notes=data.get("visibility_note"),
            metadata={
                "module_key": data.get("module_key"),
                "display_name": data.get("display_name"),
                "metadata_only": True,
                "automatic_enforcement_disabled": True,
            },
        )
        return {"flag": self._flag_projection(stored), **self.safety_flags()}

    async def update_flag(self, flag_id: str, payload: AgencyFeatureFlagUpdateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        existing = await self._require_flag(flag_id)
        updates = payload_dict(payload)
        updated = await self.db.collection(FLAG_COLLECTION).update_one({"id": flag_id}, updates)
        stored = updated or existing
        audit_service = AgencyFeatureFlagAuditService(self.db)
        await audit_service.ensure_readiness(
            agency_id=stored["agency_id"],
            feature_key=stored["feature_key"],
            reviewed_by=actor_from_user(user),
        )
        await audit_service.record_audit(
            agency_id=stored["agency_id"],
            feature_key=stored["feature_key"],
            previous_state=existing.get("state"),
            proposed_state=stored.get("state") or existing.get("state") or "disabled",
            changed_by=actor_from_user(user),
            reason="feature_flag_visibility_updated",
            notes=updates.get("visibility_note") or existing.get("visibility_note"),
            metadata={
                "module_key": stored.get("module_key"),
                "display_name": stored.get("display_name"),
                "metadata_only": True,
                "automatic_enforcement_disabled": True,
            },
        )
        return {"flag": self._flag_projection(stored), **self.safety_flags()}

    async def create_review(self, payload: AgencyFeatureFlagReviewCreateRequest | dict[str, Any], user: dict | None = None) -> dict[str, Any]:
        data = payload_dict(payload)
        data["reviewer"] = data.get("reviewer") or actor_from_user(user)
        review = AgencyFeatureFlagReview(**data)
        stored = await self.db.collection(REVIEW_COLLECTION).insert_one(review.model_dump(mode="json"))
        return {"review": self._review_projection(stored), **self.safety_flags()}

    async def create_snapshot(self, payload: AgencyFeatureFlagSnapshotCreateRequest | dict[str, Any]) -> dict[str, Any]:
        data = payload_dict(payload)
        if not data.get("snapshot_date"):
            data["snapshot_date"] = now_utc()
        if not data.get("immutable_json"):
            flags = await self.list_flags(agency_id=data["agency_id"])
            data["immutable_json"] = {"flags": flags, "metadata_only": True}
        snapshot = AgencyFeatureFlagSnapshot(**data)
        stored = await self.db.collection(SNAPSHOT_COLLECTION).insert_one(snapshot.model_dump(mode="json"))
        return {"snapshot": self._snapshot_projection(stored), **self.safety_flags()}

    async def list_flags(
        self,
        *,
        agency_id: str | None = None,
        module_key: str | None = None,
        state: str | None = None,
        agency_view: bool = False,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if module_key:
            filters["module_key"] = module_key
        if state:
            filters["state"] = enum_value(state)
        flags = await self.db.collection(FLAG_COLLECTION).find_many(filters or None)
        flags.sort(key=lambda item: (item.get("module_key") or "", item.get("feature_key") or ""))
        return [self._flag_projection(item, agency_view=agency_view) for item in flags]

    async def list_reviews(self, *, agency_id: str | None = None, agency_view: bool = False) -> list[dict[str, Any]]:
        filters = {"agency_id": agency_id} if agency_id else None
        reviews = await self.db.collection(REVIEW_COLLECTION).find_many(filters)
        reviews.sort(key=lambda item: self._timestamp_sort_value(item.get("created_at")), reverse=True)
        return [self._review_projection(item, agency_view=agency_view) for item in reviews]

    async def list_snapshots(self, *, agency_id: str | None = None, agency_view: bool = False) -> list[dict[str, Any]]:
        filters = {"agency_id": agency_id} if agency_id else None
        snapshots = await self.db.collection(SNAPSHOT_COLLECTION).find_many(filters)
        snapshots.sort(key=lambda item: self._timestamp_sort_value(item.get("snapshot_date") or item.get("created_at")), reverse=True)
        return [self._snapshot_projection(item, agency_view=agency_view) for item in snapshots]

    async def _require_flag(self, flag_id: str) -> dict[str, Any]:
        flag = await self.db.collection(FLAG_COLLECTION).find_one({"id": flag_id})
        if not flag:
            raise ValueError("Agency feature flag not found.")
        return flag

    def _flag_projection(self, flag: dict[str, Any], *, agency_view: bool = False) -> dict[str, Any]:
        projected = dict(flag)
        projected.update(
            {
                "metadata_only": True,
                "automatic_enforcement_disabled": True,
                "operational_enforcement_performed": False,
                "badge": self._state_badge(projected.get("state")),
            }
        )
        if agency_view:
            projected["read_only"] = True
        return projected

    def _review_projection(self, review: dict[str, Any], *, agency_view: bool = False) -> dict[str, Any]:
        projected = dict(review)
        projected["metadata_only"] = True
        if agency_view:
            projected["read_only"] = True
        return projected

    def _snapshot_projection(self, snapshot: dict[str, Any], *, agency_view: bool = False) -> dict[str, Any]:
        projected = dict(snapshot)
        projected.update({"metadata_only": True, "immutable": True})
        if agency_view:
            projected["read_only"] = True
            projected["immutable_json"] = {"metadata_only": True, "payloads_hidden": True}
        return projected

    def _state_counts(self, flags: list[dict[str, Any]]) -> dict[str, int]:
        return {state: len([item for item in flags if item.get("state") == state]) for state in FEATURE_FLAG_STATES}

    def _state_badge(self, state: str | None) -> str:
        return {
            "enabled": "Enabled",
            "disabled": "Disabled",
            "hidden": "Hidden",
            "beta": "Beta",
            "pilot": "Pilot",
        }.get(enum_value(state), "Disabled")

    def _timestamp_sort_value(self, value: Any) -> str:
        if value is None:
            return ""
        return value.isoformat() if hasattr(value, "isoformat") else str(value)

    def safety_flags(self) -> dict[str, bool]:
        return {
            "automatic_enforcement_disabled": True,
            "billing_disabled": True,
            "payments_disabled": True,
            "provider_execution_disabled": True,
            "booking_execution_disabled": True,
            "pnr_mutation_disabled": True,
            "ticketing_disabled": True,
            "emd_issuance_disabled": True,
            "cms_publishing_disabled": True,
            "client_portal_publishing_disabled": True,
            "external_api_calls_disabled": True,
            "external_ai_disabled": True,
            "scraping_disabled": True,
            "automatic_sending_disabled": True,
            "feature_blocking_disabled": True,
            "operational_enforcement_enabled": False,
        }
