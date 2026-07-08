from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import OperationalTimeline, OperationalTimelineCreate, OperationalTimelineUpdate, new_id


PHASE_LABEL = "phase_50_4_airline_operational_knowledge_governance_foundation"
OPERATIONAL_TIMELINE_COLLECTION = "operational_timelines"

TIMELINE_EVENT_TYPES = [
    "passenger_created",
    "passenger_updated",
    "travel_request_received",
    "offer_created",
    "offer_accepted",
    "booking_created",
    "ticket_linked",
    "emd_linked",
    "ssr_created",
    "ssr_confirmed",
    "osi_added",
    "medif_requested",
    "medif_received",
    "document_uploaded",
    "document_verified",
    "approval_requested",
    "approval_received",
    "approval_rejected",
    "airport_handling_confirmed",
    "customer_contacted",
    "airline_contacted",
    "internal_note",
    "task_completed",
    "reminder",
    "deadline_reached",
    "other",
]

COMMUNICATION_TYPES = [
    "email",
    "phone",
    "chat",
    "letter",
    "meeting",
    "internal_note",
    "airline_message",
    "airport_message",
    "customer_message",
    "other",
]


class OperationalTimelineError(ValueError):
    pass


class OperationalTimelineService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_platform_entries(
        self,
        *,
        agency_id: str | None = None,
        passenger: str | None = None,
        booking: str | None = None,
        ticket: str | None = None,
        emd: str | None = None,
        ssr: str | None = None,
        airline: str | None = None,
        communication_type: str | None = None,
        event_type: str | None = None,
        priority: str | None = None,
        status: str | None = None,
        date: str | None = None,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if communication_type:
            filters["communication_type"] = communication_type
        if event_type:
            filters["event_type"] = event_type
        if priority:
            filters["event_priority"] = priority
        if status:
            filters["event_status"] = status

        items = await self.db.collection(OPERATIONAL_TIMELINE_COLLECTION).find_many(filters or None)
        if not include_archived:
            items = [
                item
                for item in items
                if not item.get("deleted_at") and item.get("event_status") != "archived"
            ]
        items = self._filter_exact(items, passenger, ["passenger_workspace_id"])
        items = self._filter_exact(items, booking, ["booking_workspace_id"])
        items = self._filter_exact(items, ticket, ["ticket_workspace_id"])
        items = self._filter_exact(items, emd, ["emd_workspace_id"])
        items = self._filter_exact(items, ssr, ["ssr_osi_workspace_id"])
        items = self._filter_exact(items, airline, ["related_airline"])
        if date:
            items = [
                item
                for item in items
                if self._date_text(item.get("created_at")) == date
                or self._date_text(item.get("due_date")) == date
                or self._date_text(item.get("completed_date")) == date
            ]
        items.sort(key=lambda item: self._sort_text(item.get("created_at")))
        return [await self._platform_projection(item) for item in items]

    async def list_agency_entries(
        self,
        agency_id: str,
        *,
        passenger: str | None = None,
        booking: str | None = None,
        ticket: str | None = None,
        emd: str | None = None,
        ssr: str | None = None,
        airline: str | None = None,
        communication_type: str | None = None,
        event_type: str | None = None,
        priority: str | None = None,
        status: str | None = None,
        date: str | None = None,
    ) -> list[dict[str, Any]]:
        items = await self.list_platform_entries(
            agency_id=agency_id,
            passenger=passenger,
            booking=booking,
            ticket=ticket,
            emd=emd,
            ssr=ssr,
            airline=airline,
            communication_type=communication_type,
            event_type=event_type,
            priority=priority,
            status=status,
            date=date,
        )
        return [self._agency_projection(item) for item in items if item.get("agency_id") == agency_id]

    async def platform_response(self, **filters: Any) -> dict[str, Any]:
        items = await self.list_platform_entries(**filters)
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "operational_timeline_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "chronological_order": "ascending_created_at",
            "read_only": False,
            "metadata_only": True,
            "notice": "Operational Timelines are metadata-only history and communication records. They do not send email, SMS, WhatsApp, Teams, Slack, live airline messages, live customer messages, AI summaries, background jobs, or provider integrations.",
            **self.safety_flags(),
        }

    async def agency_response(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        items = await self.list_agency_entries(agency_id, **filters)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "operational_timeline_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "chronological_order": "ascending_created_at",
            "read_only": True,
            "metadata_only": True,
            "notice": "Agency Timeline is read-only operational history metadata. Messaging, AI summarization, workers, and provider integrations are disabled.",
            **self.safety_flags(),
        }

    async def platform_summary(self) -> dict[str, Any]:
        items = await self.list_platform_entries()
        return {
            "phase": PHASE_LABEL,
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        items = await self.list_agency_entries(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def get_platform_entry(self, entry_id: str) -> dict[str, Any]:
        item = await self._require_entry(entry_id)
        return await self._platform_projection(item)

    async def get_agency_entry(self, agency_id: str, entry_id: str) -> dict[str, Any]:
        item = await self._require_entry(entry_id, agency_id=agency_id)
        return self._agency_projection(await self._platform_projection(item))

    async def create_entry(self, payload: OperationalTimelineCreate, user: dict) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        self._validate_payload(data)
        data.setdefault("timeline_reference", self._timeline_reference())
        data.setdefault("created_by", user.get("id"))
        data["updated_by"] = user.get("id")
        data.update(self.safety_flags())
        entry = OperationalTimeline(**data)
        created = await self.db.collection(OPERATIONAL_TIMELINE_COLLECTION).insert_one(entry.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "timeline_entry": await self._platform_projection(created),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def update_entry(self, entry_id: str, payload: OperationalTimelineUpdate, user: dict) -> dict[str, Any]:
        existing = await self._require_entry(entry_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        self._validate_payload(updates, partial=True)
        updates["updated_by"] = user.get("id")
        updates.update(self.safety_flags())
        updated = await self.db.collection(OPERATIONAL_TIMELINE_COLLECTION).update_one({"id": existing["id"]}, updates)
        if not updated:
            raise OperationalTimelineError("Operational timeline metadata could not be updated.")
        return {
            "phase": PHASE_LABEL,
            "timeline_entry": await self._platform_projection(updated),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def delete_entry(self, entry_id: str, user: dict) -> dict[str, Any]:
        existing = await self._require_entry(entry_id)
        updated = await self.db.collection(OPERATIONAL_TIMELINE_COLLECTION).update_one(
            {"id": existing["id"]},
            {
                "event_status": "archived",
                "deleted_at": self._now(),
                "deleted_by": user.get("id"),
                "updated_by": user.get("id"),
                **self.safety_flags(),
            },
        )
        if not updated:
            raise OperationalTimelineError("Operational timeline metadata could not be archived.")
        return {
            "phase": PHASE_LABEL,
            "timeline_entry": await self._platform_projection(updated),
            "archived": True,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        by_event_type: dict[str, int] = {event_type: 0 for event_type in TIMELINE_EVENT_TYPES}
        by_communication_type: dict[str, int] = {communication_type: 0 for communication_type in COMMUNICATION_TYPES}
        by_status: dict[str, int] = {}
        by_priority: dict[str, int] = {}
        by_category: dict[str, int] = {}
        linked_counts = {
            "passenger_workspace_count": 0,
            "travel_request_workspace_count": 0,
            "trip_workspace_count": 0,
            "booking_workspace_count": 0,
            "ticket_workspace_count": 0,
            "emd_workspace_count": 0,
            "ssr_osi_workspace_count": 0,
            "document_workspace_count": 0,
            "attachment_count": 0,
            "approval_reference_count": 0,
            "reminder_required_count": 0,
            "passenger_visible_count": 0,
            "airline_visible_count": 0,
            "internal_only_count": 0,
        }
        for item in items:
            self._count_value(by_event_type, item.get("event_type") or "other")
            self._count_value(by_communication_type, item.get("communication_type") or "other")
            self._count_value(by_status, item.get("event_status"))
            self._count_value(by_priority, item.get("event_priority"))
            self._count_value(by_category, item.get("event_category"))
            linked_counts["passenger_workspace_count"] += 1 if item.get("passenger_workspace_id") else 0
            linked_counts["travel_request_workspace_count"] += 1 if item.get("travel_request_workspace_id") else 0
            linked_counts["trip_workspace_count"] += 1 if item.get("trip_workspace_id") else 0
            linked_counts["booking_workspace_count"] += 1 if item.get("booking_workspace_id") else 0
            linked_counts["ticket_workspace_count"] += 1 if item.get("ticket_workspace_id") else 0
            linked_counts["emd_workspace_count"] += 1 if item.get("emd_workspace_id") else 0
            linked_counts["ssr_osi_workspace_count"] += 1 if item.get("ssr_osi_workspace_id") else 0
            linked_counts["document_workspace_count"] += 1 if item.get("document_workspace_id") else 0
            linked_counts["attachment_count"] += self._list_count(item.get("attachment_ids"))
            linked_counts["approval_reference_count"] += 1 if item.get("approval_reference") else 0
            linked_counts["reminder_required_count"] += 1 if item.get("reminder_required") else 0
            linked_counts["passenger_visible_count"] += 1 if item.get("passenger_visible") else 0
            linked_counts["airline_visible_count"] += 1 if item.get("airline_visible") else 0
            linked_counts["internal_only_count"] += 1 if item.get("internal_only") else 0
        return {
            "total_count": len(items),
            "by_event_type": by_event_type,
            "by_communication_type": by_communication_type,
            "by_status": by_status,
            "by_priority": by_priority,
            "by_category": by_category,
            **linked_counts,
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "passenger": "passenger_workspace_id exact metadata match",
            "booking": "booking_workspace_id exact metadata match",
            "ticket": "ticket_workspace_id exact metadata match",
            "emd": "emd_workspace_id exact metadata match",
            "ssr": "ssr_osi_workspace_id exact metadata match",
            "airline": "related_airline exact metadata match",
            "communication_type": COMMUNICATION_TYPES,
            "event_type": TIMELINE_EVENT_TYPES,
            "priority": "event_priority exact metadata match",
            "status": "event_status exact metadata match",
            "date": "created_at, due_date, or completed_date YYYY-MM-DD metadata match",
            "metadata_only": True,
        }

    async def _platform_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        projected["timeline_display_name"] = self._timeline_display_name(projected)
        agency = await self._agency_context(projected.get("agency_id"))
        projected["agency"] = agency
        projected["agency_name"] = agency.get("agency_name")
        projected["read_only"] = False
        projected.update(self.safety_flags())
        return projected

    def _agency_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        projected["read_only"] = True
        projected.update(self.safety_flags())
        return projected

    async def _require_entry(self, entry_id: str, *, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": entry_id}
        if agency_id:
            filters["agency_id"] = agency_id
        item = await self.db.collection(OPERATIONAL_TIMELINE_COLLECTION).find_one(filters)
        if not item:
            alt_filters = {"timeline_reference": entry_id}
            if agency_id:
                alt_filters["agency_id"] = agency_id
            item = await self.db.collection(OPERATIONAL_TIMELINE_COLLECTION).find_one(alt_filters)
        if not item:
            raise OperationalTimelineError("Operational timeline metadata was not found.")
        return item

    async def _agency_context(self, agency_id: str | None) -> dict[str, Any]:
        if not agency_id:
            return {"agency_id": None, "agency_name": None, "agency_slug": None, "metadata_only": True}
        agency = await self.db.collection("agencies").find_one({"id": agency_id})
        if not agency:
            return {"agency_id": agency_id, "agency_name": agency_id, "agency_slug": None, "metadata_only": True}
        return {
            "agency_id": agency.get("id"),
            "agency_name": agency.get("name"),
            "agency_slug": agency.get("slug"),
            "metadata_only": True,
        }

    def _validate_payload(self, data: dict[str, Any], *, partial: bool = False) -> None:
        if not partial and not data.get("agency_id"):
            raise OperationalTimelineError("Agency id is required for operational timeline metadata.")
        if not partial and not data.get("event_type"):
            raise OperationalTimelineError("Event type is required for operational timeline metadata.")

    def _filter_exact(self, items: list[dict[str, Any]], value: str | None, keys: list[str]) -> list[dict[str, Any]]:
        if not value:
            return items
        value_key = value.lower()
        return [
            item
            for item in items
            if value_key in {str(item.get(key) or "").lower() for key in keys}
        ]

    def _timeline_display_name(self, item: dict[str, Any]) -> str:
        if item.get("subject"):
            return str(item["subject"])
        if item.get("summary"):
            return str(item["summary"])
        if item.get("timeline_reference"):
            return str(item["timeline_reference"])
        return item.get("id") or "Operational timeline entry"

    def _timeline_reference(self) -> str:
        return f"TL-{new_id()[:8].upper()}"

    def _count_value(self, target: dict[str, int], value: Any) -> None:
        if value:
            target[str(value)] = target.get(str(value), 0) + 1

    def _list_count(self, value: Any) -> int:
        if not value:
            return 0
        if isinstance(value, list):
            return len(value)
        return 1

    def _sort_text(self, value: Any) -> str:
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value or "")

    def _date_text(self, value: Any) -> str:
        if not value:
            return ""
        if hasattr(value, "isoformat"):
            return value.isoformat()[:10]
        return str(value)[:10]

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "timeline_workspace_metadata_only": True,
            "email_sending_disabled": True,
            "sms_sending_disabled": True,
            "whatsapp_disabled": True,
            "teams_disabled": True,
            "slack_disabled": True,
            "live_airline_messaging_disabled": True,
            "live_customer_messaging_disabled": True,
            "ai_summarization_disabled": True,
            "background_workers_disabled": True,
            "provider_integrations_disabled": True,
            "automation_disabled": True,
        }
