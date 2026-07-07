from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import (
    FeatureBundleRolloutApproval,
    FeatureBundleRolloutApprovalCreate,
    FeatureBundleRolloutApprovalNote,
    FeatureBundleRolloutApprovalNoteCreate,
    FeatureBundleRolloutApprovalSummary,
    FeatureBundleRolloutApprovalTimelineEntry,
    FeatureBundleRolloutApprovalUpdate,
    new_id,
)
from services.agency_feature_flag_bundle_service import AgencyFeatureFlagBundleService
from services.offer_decision_export_delivery_service import actor_from_user, payload_dict


PHASE_LABEL = "phase_40_12_feature_bundle_rollout_rollback_plan_foundation"

APPROVAL_COLLECTION = "feature_bundle_rollout_approvals"
NOTE_COLLECTION = "feature_bundle_rollout_approval_notes"
PLAN_COLLECTION = "agency_feature_bundle_rollout_plans"
APPROVAL_STATUSES = ["draft", "submitted", "under_review", "approved", "rejected", "archived"]


class FeatureBundleRolloutApprovalService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_platform_approvals(
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
            filters["status"] = status
        approvals = await self.db.collection(APPROVAL_COLLECTION).find_many(filters or None)
        approvals.sort(key=lambda item: (item.get("created_at") or "", item.get("rollout_plan_id") or ""), reverse=True)
        return [await self._platform_projection(item) for item in approvals]

    async def list_agency_approvals(self, agency_id: str, *, status: str | None = None) -> list[dict[str, Any]]:
        approvals = await self.list_platform_approvals(agency_id=agency_id, status=status)
        return [self._agency_projection(item, agency_id) for item in approvals]

    async def platform_response(
        self,
        *,
        agency_id: str | None = None,
        rollout_plan_id: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        items = await self.list_platform_approvals(agency_id=agency_id, rollout_plan_id=rollout_plan_id, status=status)
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "approval_count": len(items),
            "summary": self.summarize_counts(items).model_dump(mode="json"),
            "read_only": False,
            "metadata_only": True,
            "notice": "Rollout approvals are metadata only. They do not enable features, enforce permissions, gate runtime access, bill, deploy, send, publish, or execute rollouts.",
            **self.safety_flags(),
        }

    async def agency_response(self, agency_id: str, *, status: str | None = None) -> dict[str, Any]:
        items = await self.list_agency_approvals(agency_id, status=status)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "approval_count": len(items),
            "summary": self.summarize_counts(items).model_dump(mode="json"),
            "read_only": True,
            "metadata_only": True,
            "notice": "Rollout approval metadata is read-only for this agency. It does not activate features or change access.",
            **self.safety_flags(),
        }

    async def platform_summary(self, *, agency_id: str | None = None) -> dict[str, Any]:
        items = await self.list_platform_approvals(agency_id=agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(items).model_dump(mode="json"),
            "approval_count": len(items),
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        items = await self.list_agency_approvals(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(items).model_dump(mode="json"),
            "approval_count": len(items),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def get_platform_approval(self, approval_id: str) -> dict[str, Any]:
        approval = await self._require_approval(approval_id)
        return await self._platform_projection(approval)

    async def get_agency_approval(self, agency_id: str, approval_id: str) -> dict[str, Any]:
        approval = await self._require_approval(approval_id, agency_id=agency_id)
        return self._agency_projection(await self._platform_projection(approval), agency_id)

    async def create_approval(
        self,
        payload: FeatureBundleRolloutApprovalCreate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        plan = await self._require_plan(data.get("rollout_plan_id"))
        if data.get("agency_id") and data.get("agency_id") != plan.get("agency_id"):
            raise ValueError("Approval agency metadata must match the rollout plan agency.")
        actor = actor_from_user(user)
        now = self._now()
        status = data.get("status") or "draft"
        data = self._stamp_status_fields(data, status=status, actor=actor, timestamp=now)
        approval = FeatureBundleRolloutApproval(
            approval_id=data.get("approval_id") or new_id(),
            rollout_plan_id=plan["rollout_plan_id"],
            agency_id=plan["agency_id"],
            bundle_id=plan.get("bundle_id"),
            status=status,
            reviewer=data.get("reviewer"),
            submitted_by=data.get("submitted_by"),
            submitted_at=data.get("submitted_at"),
            reviewed_by=data.get("reviewed_by"),
            reviewed_at=data.get("reviewed_at"),
            approved_by=data.get("approved_by"),
            approved_at=data.get("approved_at"),
            rejected_by=data.get("rejected_by"),
            rejected_at=data.get("rejected_at"),
            archived_at=data.get("archived_at"),
            notes=data.get("notes"),
            created_by=actor,
            updated_by=actor,
            approval_summary=self.summarize_counts([]),
            timeline=[
                FeatureBundleRolloutApprovalTimelineEntry(
                    rollout_plan_id=plan["rollout_plan_id"],
                    agency_id=plan["agency_id"],
                    event_type="approval_created",
                    status=status,
                    actor=actor,
                    occurred_at=now,
                    notes="Approval metadata record created.",
                )
            ],
        )
        stored = await self.db.collection(APPROVAL_COLLECTION).insert_one(approval.model_dump(mode="json"))
        if data.get("notes"):
            await self.create_note(stored["approval_id"], {"note_text": data["notes"], "note_type": "initial_review_note"}, user)
            stored = await self._require_approval(stored["approval_id"])
        return {
            "phase": PHASE_LABEL,
            "approval": await self._platform_projection(stored),
            "metadata_only": True,
            "notice": "Rollout approval metadata was saved only. No feature enablement, gating, billing, deployment, notification, or rollout action was triggered.",
            **self.safety_flags(),
        }

    async def update_approval(
        self,
        approval_id: str,
        payload: FeatureBundleRolloutApprovalUpdate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_approval(approval_id)
        updates = {key: value for key, value in payload_dict(payload).items() if value is not None}
        actor = actor_from_user(user)
        now = self._now()
        status = updates.get("status") or existing.get("status") or "draft"
        updates = self._stamp_status_fields(updates, status=status, actor=actor, timestamp=now)
        updates.update(
            {
                "metadata_only": True,
                "approval_metadata_only": True,
                "updated_by": actor,
            }
        )
        timeline = list(existing.get("timeline") or [])
        if "status" in updates and updates.get("status") != existing.get("status"):
            timeline.append(
                FeatureBundleRolloutApprovalTimelineEntry(
                    approval_id=existing.get("approval_id"),
                    rollout_plan_id=existing["rollout_plan_id"],
                    agency_id=existing["agency_id"],
                    event_type="approval_status_updated",
                    status=updates["status"],
                    actor=actor,
                    occurred_at=now,
                    notes=f"Approval status recorded as {updates['status']}.",
                ).model_dump(mode="json")
            )
        if "notes" in updates and updates.get("notes") and updates.get("notes") != existing.get("notes"):
            timeline.append(
                FeatureBundleRolloutApprovalTimelineEntry(
                    approval_id=existing.get("approval_id"),
                    rollout_plan_id=existing["rollout_plan_id"],
                    agency_id=existing["agency_id"],
                    event_type="approval_notes_updated",
                    status=status,
                    actor=actor,
                    occurred_at=now,
                    notes="Approval notes metadata updated.",
                ).model_dump(mode="json")
            )
        updates["timeline"] = timeline
        updated = await self.db.collection(APPROVAL_COLLECTION).update_one({"approval_id": existing.get("approval_id")}, updates)
        stored = updated or {**existing, **updates}
        return {
            "phase": PHASE_LABEL,
            "approval": await self._platform_projection(stored),
            "metadata_only": True,
            "notice": "Rollout approval metadata was updated only. No feature enablement, gating, billing, deployment, notification, or rollout action was triggered.",
            **self.safety_flags(),
        }

    async def list_notes(self, approval_id: str, *, agency_id: str | None = None) -> list[dict[str, Any]]:
        approval = await self._require_approval(approval_id, agency_id=agency_id)
        notes = await self.db.collection(NOTE_COLLECTION).find_many({"approval_id": approval["approval_id"]})
        if agency_id:
            notes = [note for note in notes if note.get("agency_visible", True)]
        notes.sort(key=lambda item: item.get("created_at") or "")
        return [self._note_projection(note, agency_view=agency_id is not None) for note in notes]

    async def notes_response(self, approval_id: str, *, agency_id: str | None = None) -> dict[str, Any]:
        notes = await self.list_notes(approval_id, agency_id=agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "approval_id": approval_id,
            "items": notes,
            "note_count": len(notes),
            "read_only": agency_id is not None,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def create_note(
        self,
        approval_id: str,
        payload: FeatureBundleRolloutApprovalNoteCreate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        approval = await self._require_approval(approval_id)
        data = payload_dict(payload)
        if not data.get("note_text"):
            raise ValueError("note_text is required.")
        actor = actor_from_user(user)
        agency_visible = bool(data.get("agency_visible", True))
        note = FeatureBundleRolloutApprovalNote(
            approval_id=approval["approval_id"],
            rollout_plan_id=approval["rollout_plan_id"],
            agency_id=approval["agency_id"],
            note_text=data["note_text"],
            note_type=data.get("note_type") or "review_note",
            agency_visible=agency_visible,
            author=actor,
        )
        stored = await self.db.collection(NOTE_COLLECTION).insert_one(note.model_dump(mode="json"))
        timeline = list(approval.get("timeline") or [])
        timeline.append(
            FeatureBundleRolloutApprovalTimelineEntry(
                approval_id=approval.get("approval_id"),
                rollout_plan_id=approval["rollout_plan_id"],
                agency_id=approval["agency_id"],
                event_type="approval_note_added",
                status=approval.get("status"),
                actor=actor,
                occurred_at=self._now(),
                notes=data["note_text"] if agency_visible else "Internal approval note metadata added.",
            ).model_dump(mode="json")
        )
        await self.db.collection(APPROVAL_COLLECTION).update_one({"approval_id": approval["approval_id"]}, {"timeline": timeline, "updated_by": actor})
        return {
            "phase": PHASE_LABEL,
            "note": self._note_projection(stored, agency_view=False),
            "metadata_only": True,
            "notice": "Rollout approval note metadata was saved only. No notification or rollout action was triggered.",
            **self.safety_flags(),
        }

    async def timeline_response(self, approval_id: str, *, agency_id: str | None = None) -> dict[str, Any]:
        approval = await self._require_approval(approval_id, agency_id=agency_id)
        timeline = await self._timeline_entries(approval, agency_view=agency_id is not None)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "approval_id": approval["approval_id"],
            "items": timeline,
            "timeline_count": len(timeline),
            "read_only": agency_id is not None,
            "metadata_only": True,
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> FeatureBundleRolloutApprovalSummary:
        counts = {status: 0 for status in APPROVAL_STATUSES}
        for item in items:
            status = item.get("status") or "draft"
            counts[status] = counts.get(status, 0) + 1
        return FeatureBundleRolloutApprovalSummary(
            total_count=len(items),
            by_status=counts,
            draft_count=counts.get("draft", 0),
            submitted_count=counts.get("submitted", 0),
            under_review_count=counts.get("under_review", 0),
            approved_count=counts.get("approved", 0),
            rejected_count=counts.get("rejected", 0),
            archived_count=counts.get("archived", 0),
            metadata_only=True,
            read_only=True,
        )

    async def _require_approval(self, approval_id: str, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"approval_id": approval_id}
        if agency_id:
            filters["agency_id"] = agency_id
        approval = await self.db.collection(APPROVAL_COLLECTION).find_one(filters)
        if not approval:
            filters = {"id": approval_id}
            if agency_id:
                filters["agency_id"] = agency_id
            approval = await self.db.collection(APPROVAL_COLLECTION).find_one(filters)
        if not approval:
            raise ValueError("Rollout approval metadata was not found.")
        return approval

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

    async def _platform_projection(self, approval: dict[str, Any]) -> dict[str, Any]:
        projected = dict(approval)
        plan = await self._plan_context(projected.get("rollout_plan_id"))
        projected["plan"] = plan
        projected["plan_name"] = plan.get("plan_name")
        projected["rollout_stage"] = plan.get("rollout_stage")
        projected["target_start_date"] = plan.get("target_start_date")
        projected["target_end_date"] = plan.get("target_end_date")
        projected["rollout_owner"] = plan.get("rollout_owner")
        projected["agency"] = await self._agency_context(projected.get("agency_id"))
        projected["agency_name"] = projected["agency"].get("agency_name")
        projected["bundle"] = await self._bundle_context(projected.get("bundle_id") or plan.get("bundle_id"))
        projected["bundle_key"] = projected["bundle"].get("bundle_key")
        projected["bundle_name"] = projected["bundle"].get("bundle_name")
        projected["notes_list"] = await self.list_notes(projected["approval_id"])
        projected["note_count"] = len(projected["notes_list"])
        projected["timeline"] = await self._timeline_entries(projected, agency_view=False)
        projected["read_only"] = False
        projected["metadata_only"] = True
        projected.update(self.safety_flags())
        return projected

    def _agency_projection(self, item: dict[str, Any], agency_id: str) -> dict[str, Any]:
        projected = dict(item)
        projected["agency_id"] = agency_id
        projected["read_only"] = True
        projected["payloads_hidden"] = True
        projected["notes_list"] = [note for note in projected.get("notes_list", []) if note.get("agency_visible", True)]
        visible_note_texts = {note.get("note_text") for note in projected["notes_list"]}
        projected["timeline"] = [
            entry for entry in projected.get("timeline", [])
            if entry.get("event_type") not in {"approval_note_added", "approval_note_visible"}
            or entry.get("notes") in visible_note_texts
        ]
        projected.update(self.safety_flags())
        return projected

    async def _timeline_entries(self, approval: dict[str, Any], *, agency_view: bool) -> list[dict[str, Any]]:
        entries = [dict(item) for item in approval.get("timeline") or []]
        if agency_view:
            entries = [entry for entry in entries if entry.get("event_type") != "approval_note_added"]
        notes = await self.list_notes(approval["approval_id"], agency_id=approval["agency_id"] if agency_view else None)
        for note in notes:
            entries.append(
                FeatureBundleRolloutApprovalTimelineEntry(
                    approval_id=approval["approval_id"],
                    rollout_plan_id=approval["rollout_plan_id"],
                    agency_id=approval["agency_id"],
                    event_type="approval_note_visible",
                    status=approval.get("status"),
                    actor=note.get("author"),
                    occurred_at=note.get("created_at"),
                    notes=note.get("note_text"),
                ).model_dump(mode="json")
            )
        entries.sort(key=lambda item: self._sort_timestamp(item.get("occurred_at") or item.get("created_at")))
        for item in entries:
            item["metadata_only"] = True
            item["execution_disabled"] = True
        return entries

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

    def _note_projection(self, note: dict[str, Any], *, agency_view: bool) -> dict[str, Any]:
        projected = dict(note)
        projected["read_only"] = agency_view
        projected["metadata_only"] = True
        projected["payloads_hidden"] = agency_view and not projected.get("agency_visible", True)
        projected["execution_disabled"] = True
        return projected

    def _stamp_status_fields(
        self,
        data: dict[str, Any],
        *,
        status: str,
        actor: str | None,
        timestamp: datetime,
    ) -> dict[str, Any]:
        stamped = dict(data)
        stamped["status"] = status
        if status == "submitted":
            stamped.setdefault("submitted_by", actor)
            stamped.setdefault("submitted_at", timestamp)
        if status == "under_review":
            stamped.setdefault("reviewed_by", actor)
            stamped.setdefault("reviewed_at", timestamp)
        if status == "approved":
            stamped.setdefault("approved_by", actor)
            stamped.setdefault("approved_at", timestamp)
        if status == "rejected":
            stamped.setdefault("rejected_by", actor)
            stamped.setdefault("rejected_at", timestamp)
        if status == "archived":
            stamped.setdefault("archived_at", timestamp)
        return stamped

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _sort_timestamp(self, value: Any) -> str:
        if value is None:
            return ""
        return value.isoformat() if hasattr(value, "isoformat") else str(value)

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "approval_metadata_only": True,
            "feature_enablement_disabled": True,
            "feature_activation_disabled": True,
            "route_blocking_disabled": True,
            "permission_enforcement_disabled": True,
            "runtime_gating_disabled": True,
            "billing_disabled": True,
            "payments_disabled": True,
            "stripe_disabled": True,
            "payment_provider_disabled": True,
            "provider_execution_disabled": True,
            "external_api_calls_disabled": True,
            "authentication_changes_disabled": True,
            "deployment_automation_disabled": True,
            "rollout_execution_disabled": True,
            "background_workers_disabled": True,
            "cron_disabled": True,
            "webhook_execution_disabled": True,
            "email_sending_disabled": True,
            "sms_sending_disabled": True,
            "notifications_disabled": True,
            "ai_execution_disabled": True,
            "openai_disabled": True,
            "scraping_disabled": True,
            "publishing_disabled": True,
        }
