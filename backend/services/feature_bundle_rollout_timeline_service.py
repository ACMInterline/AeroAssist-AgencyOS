from __future__ import annotations

from datetime import datetime, time, timezone
from typing import Any

from database import Database
from models import (
    FeatureBundleRolloutActor,
    FeatureBundleRolloutTimelineEntry,
    FeatureBundleRolloutTimelineEntryCreate,
    new_id,
)
from services.agency_feature_flag_bundle_service import AgencyFeatureFlagBundleService
from services.offer_decision_export_delivery_service import payload_dict


PHASE_LABEL = "phase_54_7_servicing_after_sales_workflow_foundation"

TIMELINE_COLLECTION = "feature_bundle_rollout_timeline_entries"
PLAN_COLLECTION = "agency_feature_bundle_rollout_plans"
TIMELINE_EVENT_TYPES = [
    "plan_created",
    "plan_edited",
    "approval_requested",
    "approval_granted",
    "approval_rejected",
    "schedule_created",
    "schedule_changed",
    "rollout_started",
    "rollout_completed",
    "rollback_planned",
    "note_added",
]
EVENT_LABELS = {
    "plan_created": "Plan created",
    "plan_edited": "Plan edited",
    "approval_requested": "Approval requested",
    "approval_granted": "Approval granted",
    "approval_rejected": "Approval rejected",
    "schedule_created": "Schedule created",
    "schedule_changed": "Schedule changed",
    "rollout_started": "Rollout started",
    "rollout_completed": "Rollout completed",
    "rollback_planned": "Rollback planned",
    "note_added": "Note added",
}


class FeatureBundleRolloutTimelineService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_platform_entries(
        self,
        *,
        agency_id: str | None = None,
        rollout_plan_id: str | None = None,
        bundle_id: str | None = None,
        event_type: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if rollout_plan_id:
            filters["rollout_plan_id"] = rollout_plan_id
        if bundle_id:
            filters["bundle_id"] = bundle_id
        if event_type:
            filters["event_type"] = event_type
        entries = await self.db.collection(TIMELINE_COLLECTION).find_many(filters or None)
        entries = [entry for entry in entries if self._matches_date_filter(entry, date_from=date_from, date_to=date_to)]
        entries.sort(key=lambda item: (self._date_sort_key(item.get("occurred_at")), item.get("created_at") or ""), reverse=True)
        return [await self._platform_projection(item) for item in entries]

    async def list_agency_entries(
        self,
        agency_id: str,
        *,
        rollout_plan_id: str | None = None,
        bundle_id: str | None = None,
        event_type: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict[str, Any]]:
        entries = await self.list_platform_entries(
            agency_id=agency_id,
            rollout_plan_id=rollout_plan_id,
            bundle_id=bundle_id,
            event_type=event_type,
            date_from=date_from,
            date_to=date_to,
        )
        return [self._agency_projection(item, agency_id) for item in entries]

    async def platform_response(
        self,
        *,
        agency_id: str | None = None,
        rollout_plan_id: str | None = None,
        bundle_id: str | None = None,
        event_type: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict[str, Any]:
        items = await self.list_platform_entries(
            agency_id=agency_id,
            rollout_plan_id=rollout_plan_id,
            bundle_id=bundle_id,
            event_type=event_type,
            date_from=date_from,
            date_to=date_to,
        )
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "timeline_entry_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "newest_first": True,
            "read_only": False,
            "metadata_only": True,
            "notice": "Rollout timeline entries are metadata-only history records. They do not enable bundles, change permissions, execute rollout plans, schedule jobs, publish, call providers, send email or notifications, enforce rollout state, modify subscriptions, or introduce automation.",
            **self.safety_flags(),
        }

    async def agency_response(
        self,
        agency_id: str,
        *,
        rollout_plan_id: str | None = None,
        bundle_id: str | None = None,
        event_type: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict[str, Any]:
        items = await self.list_agency_entries(
            agency_id,
            rollout_plan_id=rollout_plan_id,
            bundle_id=bundle_id,
            event_type=event_type,
            date_from=date_from,
            date_to=date_to,
        )
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "timeline_entry_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "newest_first": True,
            "read_only": True,
            "metadata_only": True,
            "notice": "Rollout timeline metadata is read-only for this agency. It does not activate features, change access, or execute rollout actions.",
            **self.safety_flags(),
        }

    async def platform_summary(self, *, agency_id: str | None = None) -> dict[str, Any]:
        items = await self.list_platform_entries(agency_id=agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(items),
            "timeline_entry_count": len(items),
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        items = await self.list_agency_entries(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(items),
            "timeline_entry_count": len(items),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def get_platform_entry(self, timeline_entry_id: str) -> dict[str, Any]:
        entry = await self._require_entry(timeline_entry_id)
        return await self._platform_projection(entry)

    async def get_agency_entry(self, agency_id: str, timeline_entry_id: str) -> dict[str, Any]:
        entry = await self._require_entry(timeline_entry_id, agency_id=agency_id)
        return self._agency_projection(await self._platform_projection(entry), agency_id)

    async def create_entry(
        self,
        payload: FeatureBundleRolloutTimelineEntryCreate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        plan = await self._require_plan(data.get("rollout_plan_id"))
        if data.get("agency_id") and data.get("agency_id") != plan.get("agency_id"):
            raise ValueError("Timeline agency metadata must match the rollout plan agency.")
        if data.get("bundle_id") and data.get("bundle_id") != plan.get("bundle_id"):
            raise ValueError("Timeline bundle metadata must match the rollout plan bundle.")
        event_type = data.get("event_type")
        if event_type not in TIMELINE_EVENT_TYPES:
            raise ValueError("Unsupported rollout timeline event type.")
        actor = self._actor_payload(data.get("actor"), user)
        event_label = data.get("event_label") or EVENT_LABELS.get(event_type) or event_type
        entry = FeatureBundleRolloutTimelineEntry(
            timeline_entry_id=data.get("timeline_entry_id") or new_id(),
            rollout_plan_id=plan["rollout_plan_id"],
            agency_id=plan["agency_id"],
            bundle_id=plan.get("bundle_id"),
            event_type=event_type,
            event_label=event_label,
            actor=actor,
            occurred_at=data.get("occurred_at") or self._now(),
            description=data.get("description") or event_label,
            source=data.get("source") or "platform_metadata",
            related_schedule_id=data.get("related_schedule_id"),
            related_approval_id=data.get("related_approval_id"),
            related_assignment_id=data.get("related_assignment_id") or plan.get("assigned_bundle_id"),
            metadata=data.get("metadata") or {},
        )
        stored = await self.db.collection(TIMELINE_COLLECTION).insert_one(entry.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "entry": await self._platform_projection(stored),
            "metadata_only": True,
            "notice": "Rollout timeline metadata was saved only. No bundle enablement, permission change, rollout execution, scheduling job, publishing, provider call, email, notification, rollout-state enforcement, subscription change, or automation was triggered.",
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        by_event_type = {event_type: 0 for event_type in TIMELINE_EVENT_TYPES}
        plan_ids: set[str] = set()
        agency_ids: set[str] = set()
        bundle_ids: set[str] = set()
        latest: str | None = None
        for item in items:
            event_type = item.get("event_type") or "note_added"
            by_event_type[event_type] = by_event_type.get(event_type, 0) + 1
            if item.get("rollout_plan_id"):
                plan_ids.add(item["rollout_plan_id"])
            if item.get("agency_id"):
                agency_ids.add(item["agency_id"])
            if item.get("bundle_id"):
                bundle_ids.add(item["bundle_id"])
            occurred_at = item.get("occurred_at")
            if occurred_at and (latest is None or str(occurred_at) > latest):
                latest = str(occurred_at)
        return {
            "total_count": len(items),
            "by_event_type": by_event_type,
            "plan_count": len(plan_ids),
            "agency_count": len(agency_ids),
            "bundle_count": len(bundle_ids),
            "latest_occurred_at": latest,
            "metadata_only": True,
            "execution_disabled": True,
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "event_types": TIMELINE_EVENT_TYPES,
            "supports_plan_filter": True,
            "supports_agency_filter": True,
            "supports_bundle_filter": True,
            "supports_event_type_filter": True,
            "supports_date_filter": True,
            "metadata_only": True,
        }

    async def _require_entry(self, timeline_entry_id: str, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"timeline_entry_id": timeline_entry_id}
        if agency_id:
            filters["agency_id"] = agency_id
        entry = await self.db.collection(TIMELINE_COLLECTION).find_one(filters)
        if not entry:
            filters = {"id": timeline_entry_id}
            if agency_id:
                filters["agency_id"] = agency_id
            entry = await self.db.collection(TIMELINE_COLLECTION).find_one(filters)
        if not entry:
            raise ValueError("Rollout timeline metadata entry was not found.")
        return entry

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

    async def _platform_projection(self, entry: dict[str, Any]) -> dict[str, Any]:
        projected = dict(entry)
        projected["event_label"] = projected.get("event_label") or EVENT_LABELS.get(projected.get("event_type")) or projected.get("event_type")
        projected["plan"] = await self._plan_context(projected.get("rollout_plan_id"))
        projected["plan_name"] = projected["plan"].get("plan_name")
        projected["rollout_stage"] = projected["plan"].get("rollout_stage")
        projected["agency"] = await self._agency_context(projected.get("agency_id"))
        projected["agency_name"] = projected["agency"].get("agency_name")
        projected["bundle"] = await self._bundle_context(projected.get("bundle_id"))
        projected["bundle_key"] = projected["bundle"].get("bundle_key")
        projected["bundle_name"] = projected["bundle"].get("bundle_name")
        projected["newest_first"] = True
        projected["read_only"] = False
        projected["metadata_only"] = True
        projected["timeline_metadata_only"] = True
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
            "target_start_date": plan.get("target_start_date"),
            "target_end_date": plan.get("target_end_date"),
            "rollout_owner": plan.get("rollout_owner"),
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

    def _actor_payload(self, actor: dict[str, Any] | None, user: dict | None) -> FeatureBundleRolloutActor:
        if actor:
            return FeatureBundleRolloutActor(**actor)
        user = user or {}
        actor_type = "platform_user" if user.get("global_role") else "agency_user"
        return FeatureBundleRolloutActor(
            actor_id=user.get("id"),
            actor_type=actor_type,
            display_name=user.get("full_name") or user.get("email") or user.get("id"),
            email=user.get("email"),
            role=user.get("global_role") or user.get("role"),
        )

    def _matches_date_filter(self, entry: dict[str, Any], *, date_from: str | None, date_to: str | None) -> bool:
        occurred_at = self._parse_datetime(entry.get("occurred_at"))
        if not occurred_at:
            return False
        start = self._parse_datetime(date_from)
        end = self._parse_datetime(date_to, end_of_day=True)
        if start and occurred_at < start:
            return False
        if end and occurred_at > end:
            return False
        return True

    def _parse_datetime(self, value: Any, *, end_of_day: bool = False) -> datetime | None:
        if not value:
            return None
        if isinstance(value, datetime):
            parsed = value
        else:
            text = str(value)
            if text.endswith("Z"):
                text = text[:-1] + "+00:00"
            if len(text) == 10 and text.count("-") == 2:
                parsed = datetime.combine(datetime.fromisoformat(text).date(), time.max if end_of_day else time.min)
            else:
                parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _date_sort_key(self, value: Any) -> str:
        parsed = self._parse_datetime(value)
        return parsed.isoformat() if parsed else ""

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "timeline_metadata_only": True,
            "feature_bundles_enablement_disabled": True,
            "feature_bundle_enablement_disabled": True,
            "agency_permission_changes_disabled": True,
            "rollout_plan_execution_disabled": True,
            "rollout_execution_disabled": True,
            "background_jobs_disabled": True,
            "background_workers_disabled": True,
            "scheduled_jobs_disabled": True,
            "cron_jobs_disabled": True,
            "automation_disabled": True,
            "publishing_disabled": True,
            "provider_calls_disabled": True,
            "provider_execution_disabled": True,
            "external_api_calls_disabled": True,
            "email_sending_disabled": True,
            "notifications_disabled": True,
            "notification_sending_disabled": True,
            "rollout_state_enforcement_disabled": True,
            "subscription_modification_disabled": True,
        }
