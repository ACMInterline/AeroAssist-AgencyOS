from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Iterable

from database import Database
from models import (
    AuditEvent,
    CommunicationAttachment,
    CommunicationAttachmentCreate,
    CommunicationEntityReference,
    CommunicationMessage,
    CommunicationMessageCreate,
    CommunicationMessageEdit,
    CommunicationParticipant,
    CommunicationParticipantCreate,
    CommunicationThread,
    CommunicationThreadCreate,
    NotificationProjection,
    OperationalTimeline,
    OperationalTimelineCreate,
    new_id,
)
from persistence_query import PaginationRequest
from persistence_repository import PersistenceRepository


TIMELINE_COLLECTION = "operational_timelines"
THREAD_COLLECTION = "communication_threads"
MESSAGE_COLLECTION = "communication_messages"
PARTICIPANT_COLLECTION = "communication_participants"
ATTACHMENT_COLLECTION = "communication_attachments"
NOTIFICATION_COLLECTION = "operational_notification_projections"
AUDIT_COLLECTION = "audit_events"

MAX_LIST_LIMIT = 200
MAX_SEARCH_LIMIT = 100

CANONICAL_EVENT_TYPES = {
    "request_created",
    "offer_created",
    "offer_revised",
    "offer_delivered",
    "offer_accepted",
    "offer_declined",
    "trip_confirmed",
    "booking_prepared",
    "booking_confirmed",
    "ticket_imported",
    "emd_imported",
    "invoice_issued",
    "payment_received",
    "refund_recorded",
    "exchange_recorded",
    "supplier_cost_confirmed",
    "portal_login",
    "portal_approval",
    "document_uploaded",
    "document_delivered",
    "communication_sent",
    "communication_received",
    "manual_note",
    "assignment",
    "status_transition",
    "timeline_correction",
    "timeline_superseded",
}

VISIBILITY_VALUES = {
    "internal",
    "agency",
    "client",
    "passenger",
    "supplier",
    "platform",
    "system",
}

PARTICIPANT_TYPES = {
    "platform",
    "agency",
    "client_portal",
    "passenger_portal",
    "supplier",
    "airline",
    "system",
}

ENTITY_COLLECTIONS: dict[str, tuple[str, ...]] = {
    "client": ("client_profiles",),
    "passenger": ("passenger_profiles", "passenger_workspaces"),
    "request": ("travel_requests", "travel_request_workspaces"),
    "offer": ("offer_workspaces", "offer_workspaces_v2", "offers"),
    "accepted_offer": ("trip_accepted_offer_snapshots",),
    "trip": ("trip_dossiers", "trip_workspaces"),
    "booking": ("booking_records", "booking_workspaces", "bookings"),
    "booking_workspace": ("booking_workspaces",),
    "ticket": ("ticket_records", "ticket_workspaces"),
    "emd": ("emd_records", "emd_workspaces"),
    "passenger_service": ("passenger_service_requests", "ssr_osi_workspaces"),
    "document": ("document_workspaces", "rendered_documents", "documents"),
    "invoice": ("invoices",),
    "payment": ("payment_records",),
    "supplier_cost": ("supplier_costs",),
    "refund": ("refund_ledger_entries",),
    "exchange": ("exchange_ledger_entries",),
    "after_sales_case": ("after_sales_cases", "refund_exchange_cases"),
    "task": ("operational_work_items", "request_tasks"),
}

LEGACY_COMMUNICATION_STRUCTURES: tuple[dict[str, str], ...] = (
    {
        "structure": "request_messages",
        "classification": "compatibility",
        "canonical_adapter": "request message API",
    },
    {
        "structure": "after_sales_communication_records",
        "classification": "compatibility",
        "canonical_adapter": "after-sales communication API",
    },
    {
        "structure": "refund_exchange_messages",
        "classification": "compatibility",
        "canonical_adapter": "refund/exchange message API",
    },
    {
        "structure": "journey_offer_client_questions",
        "classification": "compatibility",
        "canonical_adapter": "offer delivery question API",
    },
    {
        "structure": "airline_supplier_interactions",
        "classification": "projection",
        "canonical_adapter": "supplier interaction evidence",
    },
)

LEGACY_TIMELINE_STRUCTURES: tuple[dict[str, str], ...] = (
    {"structure": "operational_timelines", "classification": "canonical"},
    {"structure": "request_timeline_events", "classification": "compatibility"},
    {"structure": "offer_timeline_events", "classification": "compatibility"},
    {"structure": "trip_timeline_events", "classification": "compatibility"},
    {"structure": "booking_timeline_events", "classification": "compatibility"},
    {"structure": "ticket_emd_timeline_events", "classification": "compatibility"},
    {"structure": "document_timeline_events", "classification": "compatibility"},
    {"structure": "refund_exchange_timeline_events", "classification": "compatibility"},
    {"structure": "audit_events", "classification": "audit"},
)


class OperationalCollaborationError(ValueError):
    def __init__(self, message: str, code: str = "INVALID_COLLABORATION_REQUEST") -> None:
        super().__init__(message)
        self.code = code


class OperationalCollaborationService:
    """Canonical, provider-free operational timeline and communication owner."""

    def __init__(self, db: Database) -> None:
        self.db = db

    async def append_timeline(
        self,
        payload: OperationalTimelineCreate | dict[str, Any],
        actor: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        data = self._payload(payload)
        agency_id = self._required_text(data.get("agency_id"), "Agency id is required.")
        event_type = self._required_text(data.get("event_type"), "Event type is required.")
        idempotency_key = self._clean_optional(data.get("idempotency_key"))
        if idempotency_key:
            existing = await self.db.collection(TIMELINE_COLLECTION).find_one(
                {"agency_id": agency_id, "idempotency_key": idempotency_key}
            )
            if existing:
                return existing

        now = self._now()
        actor = actor or {}
        actor_type = self._actor_type(actor, data.get("actor_type"))
        actor_id = (
            self._clean_optional(data.get("actor_id"))
            or self._clean_optional(actor.get("identity_id"))
            or self._clean_optional(actor.get("id"))
        )
        actor_display = (
            self._clean_optional(data.get("actor_display"))
            or self._clean_optional(actor.get("full_name"))
            or self._clean_optional(actor.get("display_name"))
            or actor_type.replace("_", " ").title()
        )
        visibility = self._canonical_visibility(data)
        entity_type, entity_id = self._derive_entity(data)
        entry_id = (
            self._stable_id("otl", agency_id, idempotency_key)
            if idempotency_key
            else self._clean_optional(data.get("id")) or new_id()
        )
        data.update(
            {
                "id": entry_id,
                "timeline_reference": data.get("timeline_reference")
                or f"OTL-{entry_id[-12:].upper()}",
                "entity_type": entity_type,
                "entity_id": entity_id,
                "event_type": event_type,
                "event_time": now,
                "actor_type": actor_type,
                "actor_id": actor_id,
                "actor_display": actor_display,
                "visibility": visibility,
                "created_by": data.get("created_by") or actor_id,
                "created_at": now,
                "updated_at": now,
                "ordering_key": f"{now.isoformat()}|{entry_id}",
                "append_only": True,
                "immutable_business_history": True,
                "metadata_only": True,
                "timeline_workspace_metadata_only": True,
            }
        )
        data.pop("updated_by", None)
        data.pop("deleted_at", None)
        data.pop("deleted_by", None)
        entry = OperationalTimeline(**data)
        created = await self.db.collection(TIMELINE_COLLECTION).insert_one(
            entry.model_dump(mode="json")
        )
        await self._project_notification(created)
        return created

    async def record_business_event(
        self,
        *,
        agency_id: str,
        entity_type: str,
        entity_id: str,
        event_type: str,
        summary: str,
        actor: dict[str, Any] | None = None,
        visibility: str = "internal",
        details: dict[str, Any] | None = None,
        parent_entity_type: str | None = None,
        parent_entity_id: str | None = None,
        linked_audit_event_id: str | None = None,
        linked_communication_thread_id: str | None = None,
        linked_communication_message_id: str | None = None,
        attachment_ids: list[str] | None = None,
        event_subtype: str | None = None,
        idempotency_key: str | None = None,
        event_source: str | None = None,
        source_collection: str | None = None,
        source_record_id: str | None = None,
    ) -> dict[str, Any]:
        links = self._canonical_links(entity_type, entity_id)
        return await self.append_timeline(
            {
                "agency_id": agency_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "parent_entity_type": parent_entity_type,
                "parent_entity_id": parent_entity_id,
                "event_type": event_type,
                "event_subtype": event_subtype,
                "event_category": self._event_category(event_type),
                "event_source": event_source
                or source_collection
                or "canonical_operational_collaboration",
                "event_status": "recorded",
                "summary": summary,
                "details": details or {},
                "visibility": visibility,
                "internal_only": visibility in {"internal", "agency", "system"},
                "passenger_visible": visibility == "passenger",
                "airline_visible": visibility == "supplier",
                "linked_audit_event_id": linked_audit_event_id,
                "linked_communication_thread_id": linked_communication_thread_id,
                "linked_communication_message_id": linked_communication_message_id,
                "attachment_ids": attachment_ids or [],
                "idempotency_key": idempotency_key,
                "source_collection": source_collection,
                "source_record_id": source_record_id,
                **links,
            },
            actor,
        )

    async def record_compatibility_event(
        self,
        *,
        agency_id: str,
        entity_type: str,
        entity_id: str,
        source_event_type: str,
        summary: str,
        actor_user_id: str | None = None,
        actor_type: str | None = None,
        visibility: str = "internal",
        details: dict[str, Any] | None = None,
        source_collection: str | None = None,
        source_record_id: str | None = None,
        linked_audit_event_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Append a legacy module event without extending the canonical catalog."""

        return await self.record_business_event(
            agency_id=agency_id,
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=self._canonical_event_type(
                source_event_type, entity_type=entity_type
            ),
            event_subtype=source_event_type,
            summary=summary,
            actor={
                "id": actor_user_id,
                "identity_id": actor_user_id,
                "actor_type": actor_type
                or ("agency" if actor_user_id else "system"),
            },
            visibility=visibility,
            details={"source_event_type": source_event_type, **(details or {})},
            source_collection=source_collection,
            source_record_id=source_record_id or entity_id,
            linked_audit_event_id=linked_audit_event_id,
            idempotency_key=idempotency_key,
        )

    async def append_correction(
        self,
        entry_id: str,
        changes: dict[str, Any],
        actor: dict[str, Any],
        *,
        archive: bool = False,
    ) -> dict[str, Any]:
        original = await self.require_timeline_entry(entry_id)
        event_type = "timeline_superseded" if archive else "timeline_correction"
        details = {
            "requested_projection_changes": changes,
            "original_entry_id": original["id"],
            "original_event_type": original.get("event_type"),
            "append_only": True,
        }
        compatible_changes = {
            key: value
            for key, value in changes.items()
            if key
            in {
                "event_status",
                "event_priority",
                "operational_stage",
                "operational_result",
                "approval_status",
                "due_date",
                "completed_date",
                "reminder_required",
                "operational_notes",
                "metadata",
            }
        }
        inherited_fields = {
            key: original.get(key)
            for key in {
                "passenger_workspace_id",
                "travel_request_workspace_id",
                "trip_workspace_id",
                "booking_workspace_id",
                "ticket_workspace_id",
                "emd_workspace_id",
                "ssr_osi_workspace_id",
                "document_workspace_id",
                "related_airline",
                "related_airport",
                "communication_type",
                "communication_direction",
                "communication_channel",
                "sender",
                "recipient",
                "subject",
                "attachment_ids",
                "approval_reference",
                "linked_communication_thread_id",
                "linked_communication_message_id",
                "linked_audit_event_id",
                "linked_document_id",
                "linked_finance_record",
                "linked_booking",
                "linked_ticket",
                "linked_emd",
                "linked_request",
                "linked_offer",
                "linked_trip",
            }
            if original.get(key) is not None
        }
        return await self.append_timeline(
            {
                "agency_id": original["agency_id"],
                "entity_type": original.get("entity_type") or "timeline_entry",
                "entity_id": original.get("entity_id") or original["id"],
                "parent_entity_type": original.get("parent_entity_type"),
                "parent_entity_id": original.get("parent_entity_id"),
                "event_type": event_type,
                "event_subtype": original.get("event_type"),
                "event_category": "timeline_governance",
                "event_source": "operational_timeline_compatibility_adapter",
                **inherited_fields,
                **compatible_changes,
                "event_status": "archived"
                if archive
                else compatible_changes.get("event_status") or "recorded",
                "summary": (
                    "Timeline entry superseded by append-only evidence."
                    if archive
                    else "Timeline correction appended; original evidence was preserved."
                ),
                "details": details,
                "visibility": original.get("visibility") or "internal",
                "internal_only": original.get("internal_only", True),
                "passenger_visible": original.get("passenger_visible", False),
                "airline_visible": original.get("airline_visible", False),
                "supersedes_entry_id": original["id"],
                "idempotency_key": (
                    f"timeline:{original['id']}:{event_type}:"
                    f"{self._content_hash(changes)}"
                ),
            },
            actor,
        )

    async def require_timeline_entry(
        self, entry_id: str, agency_id: str | None = None
    ) -> dict[str, Any]:
        filters: dict[str, Any] = {"id": entry_id}
        if agency_id:
            filters["agency_id"] = agency_id
        entry = await self.db.collection(TIMELINE_COLLECTION).find_one(filters)
        if not entry:
            raise OperationalCollaborationError(
                "Operational timeline entry was not found.", "TIMELINE_NOT_FOUND"
            )
        return entry

    async def list_timeline(
        self,
        *,
        agency_id: str,
        entity_type: str | None = None,
        entity_id: str | None = None,
        visibility: Iterable[str] | None = None,
        event_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {"agency_id": agency_id}
        if entity_type:
            filters["entity_type"] = entity_type
        if entity_id:
            filters["entity_id"] = entity_id
        if event_type:
            filters["event_type"] = event_type
        items = await self.db.collection(TIMELINE_COLLECTION).find_many(
            filters,
            sort=[("event_time", 1), ("created_at", 1), ("id", 1)],
            limit=self._bounded_limit(limit),
        )
        allowed = set(visibility or VISIBILITY_VALUES)
        return [
            self._timeline_projection(item)
            for item in items
            if self._canonical_visibility(item) in allowed
        ]

    async def create_thread(
        self,
        agency_id: str,
        payload: CommunicationThreadCreate | dict[str, Any],
        actor: dict[str, Any],
    ) -> dict[str, Any]:
        data = self._payload(payload)
        subject = self._required_text(data.get("subject"), "Thread subject is required.")
        idempotency_key = self._clean_optional(data.get("idempotency_key"))
        if idempotency_key:
            thread_id = self._stable_id("cth", agency_id, idempotency_key)
            existing = await self.db.collection(THREAD_COLLECTION).find_one(
                {"agency_id": agency_id, "id": thread_id}
            )
            if existing:
                return await self.thread_detail(agency_id, thread_id)
        else:
            thread_id = new_id()

        references = [
            CommunicationEntityReference(**item).model_dump(mode="json")
            for item in data.get("entity_references") or []
        ]
        if not references:
            raise OperationalCollaborationError(
                "At least one business entity reference is required.",
                "ENTITY_REFERENCE_REQUIRED",
            )
        for reference in references:
            await self.validate_entity_reference(agency_id, reference)

        visibility = self._visibility_list(data.get("visibility"))
        now = self._now()
        thread = CommunicationThread(
            id=thread_id,
            agency_id=agency_id,
            thread_reference=f"COM-{thread_id[-12:].upper()}",
            subject=subject,
            status="open",
            entity_references=references,
            visibility=visibility,
            created_by_actor_type=self._actor_type(actor),
            created_by_actor_id=actor.get("identity_id") or actor.get("id"),
            metadata={
                **(data.get("metadata") or {}),
                "idempotency_key": idempotency_key,
            },
            created_at=now,
            updated_at=now,
        )
        created = await self.db.collection(THREAD_COLLECTION).insert_one(
            thread.model_dump(mode="json")
        )

        participant_payloads = list(data.get("participants") or [])
        participant_payloads.extend(
            await self._linked_portal_participant_payloads(
                agency_id, references, visibility
            )
        )
        participant_payloads = self._deduplicate_participant_payloads(
            participant_payloads
        )
        if not self._actor_participant_present(participant_payloads, actor):
            participant_payloads.insert(0, self._actor_participant_payload(actor))
        participant_ids: list[str] = []
        for participant_payload in participant_payloads:
            participant = await self._create_participant(
                agency_id, thread_id, participant_payload, actor
            )
            participant_ids.append(participant["id"])
        created = (
            await self.db.collection(THREAD_COLLECTION).update_one(
                {"agency_id": agency_id, "id": thread_id},
                {"participant_ids": participant_ids},
            )
            or created
        )

        audit = await self._audit(
            agency_id=agency_id,
            actor=actor,
            event_type="communication.thread_created",
            entity_type="communication_thread",
            entity_id=thread_id,
            summary="Communication thread created.",
            metadata={
                "entity_references": references,
                "participant_count": len(participant_ids),
                "visibility": visibility,
            },
        )
        primary = references[0]
        await self.record_business_event(
            agency_id=agency_id,
            entity_type=primary["entity_type"],
            entity_id=primary["entity_id"],
            event_type="status_transition",
            event_subtype="communication_thread_created",
            summary=f"Communication thread opened: {subject}",
            actor=actor,
            visibility=self._timeline_visibility_for_thread(visibility),
            linked_audit_event_id=audit["id"],
            linked_communication_thread_id=thread_id,
            idempotency_key=f"communication-thread-created:{thread_id}",
            source_collection=THREAD_COLLECTION,
            source_record_id=thread_id,
        )
        return await self.thread_detail(agency_id, thread_id)

    async def ensure_entity_thread(
        self,
        *,
        agency_id: str,
        entity_type: str,
        entity_id: str,
        subject: str,
        actor: dict[str, Any],
        visibility: list[str] | None = None,
        participants: list[dict[str, Any]] | None = None,
        context_key: str = "default",
    ) -> dict[str, Any]:
        return await self.create_thread(
            agency_id,
            {
                "idempotency_key": (
                    f"entity-thread:{entity_type}:{entity_id}:{context_key}"
                ),
                "subject": subject,
                "entity_references": [
                    {"entity_type": entity_type, "entity_id": entity_id}
                ],
                "participants": participants or [],
                "visibility": visibility or ["internal"],
                "metadata": {"context_key": context_key},
            },
            actor,
        )

    async def thread_detail(
        self, agency_id: str, thread_id: str, *, visibility: Iterable[str] | None = None
    ) -> dict[str, Any]:
        thread = await self.require_thread(agency_id, thread_id)
        allowed = set(visibility or VISIBILITY_VALUES)
        participants = await self.db.collection(PARTICIPANT_COLLECTION).find_many(
            {"agency_id": agency_id, "thread_id": thread_id},
            sort=[("created_at", 1), ("id", 1)],
            limit=MAX_LIST_LIMIT,
        )
        messages = await self.db.collection(MESSAGE_COLLECTION).find_many(
            {"agency_id": agency_id, "thread_id": thread_id},
            sort=[("created_at", 1), ("id", 1)],
            limit=MAX_LIST_LIMIT,
        )
        attachments = await self.db.collection(ATTACHMENT_COLLECTION).find_many(
            {"agency_id": agency_id, "thread_id": thread_id},
            sort=[("created_at", 1), ("id", 1)],
            limit=MAX_LIST_LIMIT,
        )
        return {
            "thread": thread,
            "participants": [
                self._participant_projection(item)
                for item in participants
                if allowed.intersection(set(item.get("visibility") or []))
            ],
            "messages": [
                self._message_projection(item)
                for item in messages
                if self._canonical_visibility(item) in allowed
            ],
            "attachments": [
                item
                for item in attachments
                if self._canonical_visibility(item) in allowed
            ],
        }

    async def list_threads(
        self,
        agency_id: str,
        *,
        entity_type: str | None = None,
        entity_id: str | None = None,
        status: str | None = None,
        visibility: Iterable[str] | None = None,
        participant_ids: set[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {"agency_id": agency_id}
        if status:
            filters["status"] = status
        items = await self.db.collection(THREAD_COLLECTION).find_many(
            filters,
            sort=[("updated_at", -1), ("id", -1)],
            limit=self._bounded_limit(limit),
        )
        allowed = set(visibility or VISIBILITY_VALUES)
        projected: list[dict[str, Any]] = []
        for item in items:
            refs = item.get("entity_references") or []
            if entity_type and not any(
                ref.get("entity_type") == entity_type for ref in refs
            ):
                continue
            if entity_id and not any(ref.get("entity_id") == entity_id for ref in refs):
                continue
            if participant_ids is not None and not participant_ids.intersection(
                set(item.get("participant_ids") or [])
            ):
                continue
            if not allowed.intersection(set(item.get("visibility") or [])):
                continue
            projected.append(item)
        return projected

    async def require_thread(self, agency_id: str, thread_id: str) -> dict[str, Any]:
        thread = await self.db.collection(THREAD_COLLECTION).find_one(
            {"agency_id": agency_id, "id": thread_id}
        )
        if not thread:
            raise OperationalCollaborationError(
                "Communication thread was not found.", "THREAD_NOT_FOUND"
            )
        return thread

    async def post_message(
        self,
        agency_id: str,
        thread_id: str,
        payload: CommunicationMessageCreate | dict[str, Any],
        actor: dict[str, Any],
    ) -> dict[str, Any]:
        thread = await self.require_thread(agency_id, thread_id)
        if thread.get("status") != "open":
            raise OperationalCollaborationError(
                "Messages can only be posted to an open thread.", "THREAD_CLOSED"
            )
        data = self._payload(payload)
        plain_text = self._required_text(
            data.get("plain_text"), "Message text is required."
        )
        idempotency_key = self._clean_optional(data.get("idempotency_key"))
        message_id = (
            self._stable_id("cmsg", agency_id, idempotency_key)
            if idempotency_key
            else new_id()
        )
        existing = await self.db.collection(MESSAGE_COLLECTION).find_one(
            {"agency_id": agency_id, "id": message_id}
        )
        if existing:
            if existing.get("plain_text") != plain_text:
                raise OperationalCollaborationError(
                    "The idempotency key already belongs to different message content.",
                    "IDEMPOTENCY_CONFLICT",
                )
            return existing

        sender = await self._resolve_sender_participant(
            agency_id, thread_id, data.get("sender_participant_id"), actor
        )
        visibility = self._required_visibility(data.get("visibility") or "internal")
        self._assert_message_visibility(sender, visibility, thread)
        recipient_ids = list(dict.fromkeys(data.get("recipient_participant_ids") or []))
        await self._validate_recipients(agency_id, thread_id, recipient_ids)
        attachment_ids = list(dict.fromkeys(data.get("attachment_ids") or []))
        await self._validate_attachments(agency_id, thread_id, attachment_ids)
        delivery_status = str(data.get("delivery_status") or "recorded")
        if sender.get("participant_type") in {"agency", "platform"} and delivery_status not in {
            "recorded",
            "not_sent",
        }:
            raise OperationalCollaborationError(
                "External delivery cannot be asserted without provider evidence.",
                "DELIVERY_STATUS_NOT_ALLOWED",
            )
        if sender.get("participant_type") in {"client_portal", "passenger_portal"}:
            delivery_status = "received"

        audit_id = new_id()
        timeline_idempotency = f"communication-message:{message_id}"
        message = CommunicationMessage(
            id=message_id,
            agency_id=agency_id,
            thread_id=thread_id,
            sender_participant_id=sender["id"],
            sender_type=sender["participant_type"],
            sender_identity_id=sender.get("identity_id"),
            sender_display=sender.get("display_name") or "Participant",
            recipient_participant_ids=recipient_ids,
            message_type=data.get("message_type") or "message",
            plain_text=plain_text,
            rich_text=data.get("rich_text"),
            attachment_ids=attachment_ids,
            delivery_status=delivery_status,
            visibility=visibility,
            linked_audit_event_id=audit_id,
            source_collection=(data.get("metadata") or {}).get("source_collection"),
            source_record_id=(data.get("metadata") or {}).get("source_record_id"),
            metadata={
                **(data.get("metadata") or {}),
                "idempotency_key": idempotency_key,
                "provider_execution": False,
            },
        )
        created = await self.db.collection(MESSAGE_COLLECTION).insert_one(
            message.model_dump(mode="json")
        )
        audit = AuditEvent(
            id=audit_id,
            agency_id=agency_id,
            actor_user_id=actor.get("id"),
            event_type="communication.message_posted",
            entity_type="communication_message",
            entity_id=message_id,
            summary="Communication message recorded.",
            metadata={
                "thread_id": thread_id,
                "message_type": created.get("message_type"),
                "visibility": visibility,
                "attachment_count": len(attachment_ids),
                "content_hash": self._content_hash(
                    {"plain_text": plain_text, "rich_text": data.get("rich_text")}
                ),
                "provider_execution": False,
            },
        )
        await self.db.collection(AUDIT_COLLECTION).insert_one(audit.model_dump(mode="json"))
        primary = (thread.get("entity_references") or [{}])[0]
        timeline = await self.record_business_event(
            agency_id=agency_id,
            entity_type=primary.get("entity_type") or "communication_thread",
            entity_id=primary.get("entity_id") or thread_id,
            event_type=(
                "communication_received"
                if sender.get("participant_type") in {"client_portal", "passenger_portal"}
                else "manual_note"
                if created.get("message_type") == "internal_note"
                else "communication_sent"
            ),
            summary=self._message_summary(created),
            actor=actor,
            visibility=visibility,
            details={
                "message_type": created.get("message_type"),
                "delivery_status": delivery_status,
                "participant_type": sender.get("participant_type"),
            },
            linked_audit_event_id=audit_id,
            linked_communication_thread_id=thread_id,
            linked_communication_message_id=message_id,
            attachment_ids=attachment_ids,
            idempotency_key=timeline_idempotency,
            source_collection=MESSAGE_COLLECTION,
            source_record_id=message_id,
        )
        created = (
            await self.db.collection(MESSAGE_COLLECTION).update_one(
                {"agency_id": agency_id, "id": message_id},
                {"linked_timeline_entry_id": timeline["id"]},
            )
            or created
        )
        await self.db.collection(THREAD_COLLECTION).update_one(
            {"agency_id": agency_id, "id": thread_id},
            {
                "last_message_at": created.get("created_at"),
                "message_count": int(thread.get("message_count") or 0) + 1,
            },
        )
        return self._message_projection(created)

    async def edit_message(
        self,
        agency_id: str,
        message_id: str,
        payload: CommunicationMessageEdit | dict[str, Any],
        actor: dict[str, Any],
    ) -> dict[str, Any]:
        message = await self.db.collection(MESSAGE_COLLECTION).find_one(
            {"agency_id": agency_id, "id": message_id}
        )
        if not message:
            raise OperationalCollaborationError(
                "Communication message was not found.", "MESSAGE_NOT_FOUND"
            )
        data = self._payload(payload)
        plain_text = self._required_text(
            data.get("plain_text"), "Edited message text is required."
        )
        reason = self._required_text(data.get("reason"), "Edit reason is required.")
        if (
            self._actor_type(actor) in {"client_portal", "passenger_portal"}
            and message.get("sender_identity_id") != actor.get("identity_id")
        ):
            raise OperationalCollaborationError(
                "Portal users can edit only their own messages.", "MESSAGE_EDIT_FORBIDDEN"
            )
        now = self._now()
        history = list(message.get("edit_history") or [])
        history.append(
            {
                "plain_text": message.get("plain_text"),
                "rich_text": message.get("rich_text"),
                "edited_at": now,
                "edited_by_actor_id": actor.get("identity_id") or actor.get("id"),
                "reason": reason,
                "content_hash": self._content_hash(
                    {
                        "plain_text": message.get("plain_text"),
                        "rich_text": message.get("rich_text"),
                    }
                ),
            }
        )
        updated = await self.db.collection(MESSAGE_COLLECTION).update_one(
            {"agency_id": agency_id, "id": message_id},
            {
                "plain_text": plain_text,
                "rich_text": data.get("rich_text"),
                "edited_at": now,
                "edited_by_actor_id": actor.get("identity_id") or actor.get("id"),
                "edit_history": history,
            },
        )
        audit = await self._audit(
            agency_id=agency_id,
            actor=actor,
            event_type="communication.message_edited",
            entity_type="communication_message",
            entity_id=message_id,
            summary="Communication message edited with preserved history.",
            metadata={"thread_id": message["thread_id"], "reason": reason},
        )
        thread = await self.require_thread(agency_id, message["thread_id"])
        primary = (thread.get("entity_references") or [{}])[0]
        await self.record_business_event(
            agency_id=agency_id,
            entity_type=primary.get("entity_type") or "communication_thread",
            entity_id=primary.get("entity_id") or message["thread_id"],
            event_type="status_transition",
            event_subtype="communication_message_edited",
            summary="Communication message edit recorded; prior content was preserved.",
            actor=actor,
            visibility=message.get("visibility") or "internal",
            details={"message_id": message_id, "reason": reason},
            linked_audit_event_id=audit["id"],
            linked_communication_thread_id=message["thread_id"],
            linked_communication_message_id=message_id,
            idempotency_key=f"communication-message-edit:{message_id}:{len(history)}",
        )
        return self._message_projection(updated or message)

    async def register_attachment(
        self,
        agency_id: str,
        thread_id: str,
        payload: CommunicationAttachmentCreate | dict[str, Any],
        actor: dict[str, Any],
    ) -> dict[str, Any]:
        thread = await self.require_thread(agency_id, thread_id)
        data = self._payload(payload)
        reference_type = self._required_text(
            data.get("reference_type"), "Attachment reference type is required."
        )
        reference_id = self._required_text(
            data.get("reference_id"), "Attachment reference id is required."
        )
        await self.validate_attachment_reference(
            agency_id, reference_type, reference_id, data.get("document_id")
        )
        visibility = self._required_visibility(data.get("visibility") or "internal")
        if visibility not in set(thread.get("visibility") or []):
            raise OperationalCollaborationError(
                "Attachment visibility is outside the thread visibility contract.",
                "THREAD_VISIBILITY_MISMATCH",
            )
        if data.get("message_id"):
            message = await self.db.collection(MESSAGE_COLLECTION).find_one(
                {
                    "agency_id": agency_id,
                    "thread_id": thread_id,
                    "id": data["message_id"],
                }
            )
            if not message:
                raise OperationalCollaborationError(
                    "Attachment message does not belong to the thread.",
                    "ATTACHMENT_MESSAGE_MISMATCH",
                )
        natural_filters = {
            "agency_id": agency_id,
            "thread_id": thread_id,
            "message_id": data.get("message_id"),
            "reference_type": reference_type,
            "reference_id": reference_id,
        }
        existing = await self.db.collection(ATTACHMENT_COLLECTION).find_one(
            natural_filters
        )
        if existing:
            return existing
        attachment_id = self._stable_id(
            "catt",
            agency_id,
            (
                f"{thread_id}:{data.get('message_id') or ''}:"
                f"{reference_type}:{reference_id}"
            ),
        )
        attachment = CommunicationAttachment(
            id=attachment_id,
            agency_id=agency_id,
            thread_id=thread_id,
            message_id=data.get("message_id"),
            document_id=data.get("document_id"),
            reference_type=reference_type,
            reference_id=reference_id,
            title=self._required_text(data.get("title"), "Attachment title is required."),
            media_type=data.get("media_type"),
            checksum=data.get("checksum"),
            visibility=visibility,
            created_by_actor_type=self._actor_type(actor),
            created_by_actor_id=actor.get("identity_id") or actor.get("id"),
            metadata=data.get("metadata") or {},
        )
        created = await self.db.collection(ATTACHMENT_COLLECTION).insert_one(
            attachment.model_dump(mode="json")
        )
        await self._audit(
            agency_id=agency_id,
            actor=actor,
            event_type="communication.attachment_registered",
            entity_type="communication_attachment",
            entity_id=created["id"],
            summary="Immutable communication attachment reference registered.",
            metadata={
                "thread_id": thread_id,
                "reference_type": reference_type,
                "reference_id": reference_id,
                "binary_duplicated": False,
            },
        )
        return created

    async def close_thread(
        self,
        agency_id: str,
        thread_id: str,
        actor: dict[str, Any],
        reason: str,
    ) -> dict[str, Any]:
        thread = await self.require_thread(agency_id, thread_id)
        if thread.get("status") == "archived":
            raise OperationalCollaborationError(
                "Archived communication threads cannot be changed.", "THREAD_ARCHIVED"
            )
        now = self._now()
        updated = await self.db.collection(THREAD_COLLECTION).update_one(
            {"agency_id": agency_id, "id": thread_id},
            {
                "status": "closed",
                "closed_at": now,
                "closed_by_actor_id": actor.get("identity_id") or actor.get("id"),
                "metadata": {**(thread.get("metadata") or {}), "close_reason": reason},
            },
        )
        primary = (thread.get("entity_references") or [{}])[0]
        await self.record_business_event(
            agency_id=agency_id,
            entity_type=primary.get("entity_type") or "communication_thread",
            entity_id=primary.get("entity_id") or thread_id,
            event_type="status_transition",
            summary="Communication thread closed.",
            actor=actor,
            visibility=self._timeline_visibility_for_thread(
                thread.get("visibility") or ["internal"]
            ),
            details={"thread_id": thread_id, "reason": reason},
            linked_communication_thread_id=thread_id,
            idempotency_key=f"communication-thread-closed:{thread_id}",
        )
        return updated or thread

    async def entity_activity(
        self,
        agency_id: str,
        entity_type: str,
        entity_id: str,
        *,
        visibility: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        await self.validate_entity_reference(
            agency_id, {"entity_type": entity_type, "entity_id": entity_id}
        )
        allowed = set(visibility or {"internal", "agency", "client", "passenger", "supplier", "system"})
        timeline = await self.list_timeline(
            agency_id=agency_id,
            entity_type=entity_type,
            entity_id=entity_id,
            visibility=allowed,
            limit=MAX_LIST_LIMIT,
        )
        threads = await self.list_threads(
            agency_id,
            entity_type=entity_type,
            entity_id=entity_id,
            visibility=allowed,
            limit=MAX_LIST_LIMIT,
        )
        thread_details = [
            await self.thread_detail(agency_id, thread["id"], visibility=allowed)
            for thread in threads
        ]
        messages = [
            message
            for detail in thread_details
            for message in detail.get("messages") or []
        ]
        attachments = [
            attachment
            for detail in thread_details
            for attachment in detail.get("attachments") or []
        ]
        documents = [
            item
            for item in attachments
            if item.get("document_id") or item.get("reference_type") == "document"
        ]
        return {
            "entity": {"entity_type": entity_type, "entity_id": entity_id},
            "timeline": timeline,
            "threads": threads,
            "messages": messages,
            "attachments": attachments,
            "documents": documents,
            "activity_summary": {
                "timeline_count": len(timeline),
                "thread_count": len(threads),
                "message_count": len(messages),
                "internal_note_count": len(
                    [
                        item
                        for item in messages
                        if item.get("message_type") == "internal_note"
                        and item.get("visibility") == "internal"
                    ]
                ),
                "attachment_count": len(attachments),
                "document_count": len(documents),
                "last_activity_at": self._last_activity_at(timeline, messages),
            },
            **self.safety_flags(),
        }

    async def search(
        self,
        agency_id: str,
        query: str,
        *,
        visibility: Iterable[str] | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        needle = self._required_text(query, "Search text is required.").lower()
        bounded = min(self._bounded_limit(limit), MAX_SEARCH_LIMIT)
        allowed = set(visibility or VISIBILITY_VALUES)
        timelines = await self.db.collection(TIMELINE_COLLECTION).find_many(
            {"agency_id": agency_id},
            sort=[("event_time", -1), ("id", -1)],
            limit=MAX_LIST_LIMIT,
        )
        messages = await self.db.collection(MESSAGE_COLLECTION).find_many(
            {"agency_id": agency_id},
            sort=[("created_at", -1), ("id", -1)],
            limit=MAX_LIST_LIMIT,
        )
        participants = await self.db.collection(PARTICIPANT_COLLECTION).find_many(
            {"agency_id": agency_id},
            sort=[("created_at", -1), ("id", -1)],
            limit=MAX_LIST_LIMIT,
        )
        attachments = await self.db.collection(ATTACHMENT_COLLECTION).find_many(
            {"agency_id": agency_id},
            sort=[("created_at", -1), ("id", -1)],
            limit=MAX_LIST_LIMIT,
        )
        results: list[dict[str, Any]] = []
        for item_type, records, fields in [
            (
                "timeline",
                timelines,
                ("summary", "event_type", "actor_display", "entity_type", "entity_id"),
            ),
            ("message", messages, ("plain_text", "sender_display", "message_type")),
            (
                "participant",
                participants,
                ("display_name", "participant_role", "supplier_reference", "airline_code"),
            ),
            ("attachment", attachments, ("title", "reference_type", "reference_id")),
        ]:
            for item in records:
                if item_type != "participant" and self._canonical_visibility(item) not in allowed:
                    continue
                if item_type == "participant" and not allowed.intersection(
                    set(item.get("visibility") or [])
                ):
                    continue
                if needle not in " ".join(str(item.get(field) or "") for field in fields).lower():
                    continue
                results.append(
                    {
                        "result_type": item_type,
                        "id": item.get("id"),
                        "thread_id": item.get("thread_id"),
                        "entity_type": item.get("entity_type"),
                        "entity_id": item.get("entity_id"),
                        "label": self._search_label(item_type, item),
                        "created_at": item.get("event_time") or item.get("created_at"),
                    }
                )
        results.sort(
            key=lambda item: (str(item.get("created_at") or ""), str(item.get("id") or "")),
            reverse=True,
        )
        return {
            "query": query,
            "items": results[:bounded],
            "count": min(len(results), bounded),
            "bounded": True,
            "permission_filtered": True,
        }

    async def list_notifications(
        self,
        agency_id: str,
        *,
        visibility: Iterable[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        allowed = set(visibility or VISIBILITY_VALUES)
        items = await self.db.collection(NOTIFICATION_COLLECTION).find_many(
            {"agency_id": agency_id},
            sort=[("created_at", -1), ("id", -1)],
            limit=self._bounded_limit(limit),
        )
        return [
            item for item in items if self._canonical_visibility(item) in allowed
        ]

    async def rebuild_notification_projections(
        self, agency_id: str
    ) -> dict[str, Any]:
        before = await self.db.collection(NOTIFICATION_COLLECTION).count(
            {"agency_id": agency_id}
        )
        entries = await self.db.collection(TIMELINE_COLLECTION).find_many(
            {"agency_id": agency_id},
            sort=[("event_time", 1), ("id", 1)],
            limit=MAX_LIST_LIMIT,
        )
        for entry in entries:
            await self._project_notification(entry)
        after = await self.db.collection(NOTIFICATION_COLLECTION).count(
            {"agency_id": agency_id}
        )
        return {
            "agency_id": agency_id,
            "timeline_entries_reviewed": len(entries),
            "projections_created": max(0, after - before),
            "projection_count": after,
            "business_truth_mutated": False,
            "regenerated_from_timeline": True,
        }

    async def portal_threads(
        self,
        ctx: dict[str, Any],
        *,
        entity_type: str | None = None,
        entity_id: str | None = None,
    ) -> list[dict[str, Any]]:
        agency_id = ctx["account"]["agency_id"]
        participants = await self._portal_participants(ctx)
        participant_ids = {item["id"] for item in participants}
        visibility = self.portal_visibility(ctx)
        threads = await self.list_threads(
            agency_id,
            entity_type=entity_type,
            entity_id=entity_id,
            visibility=visibility,
            participant_ids=participant_ids,
            limit=MAX_LIST_LIMIT,
        )
        visible: list[dict[str, Any]] = []
        for thread in threads:
            if await self._portal_can_access_thread_entities(ctx, thread):
                visible.append(self._portal_thread_summary(thread))
        return visible

    async def portal_thread_detail(
        self, ctx: dict[str, Any], thread_id: str
    ) -> dict[str, Any]:
        threads = await self.portal_threads(ctx)
        if thread_id not in {item["id"] for item in threads}:
            raise OperationalCollaborationError(
                "Portal communication thread was not found.", "THREAD_NOT_FOUND"
            )
        detail = await self.thread_detail(
            ctx["account"]["agency_id"],
            thread_id,
            visibility=self.portal_visibility(ctx),
        )
        return self._portal_thread_projection(detail)

    async def portal_post_message(
        self,
        ctx: dict[str, Any],
        thread_id: str,
        payload: CommunicationMessageCreate | dict[str, Any],
    ) -> dict[str, Any]:
        await self.portal_thread_detail(ctx, thread_id)
        data = self._payload(payload)
        expected_visibility = (
            "passenger" if ctx.get("subject_type") == "passenger" else "client"
        )
        if data.get("visibility") and str(data["visibility"]) != expected_visibility:
            raise OperationalCollaborationError(
                "Portal message visibility does not match the linked Portal subject.",
                "PORTAL_VISIBILITY_MISMATCH",
            )
        data["visibility"] = expected_visibility
        data["delivery_status"] = "received"
        actor = self.portal_actor(ctx)
        return await self.post_message(
            ctx["account"]["agency_id"], thread_id, data, actor
        )

    async def validate_entity_reference(
        self, agency_id: str, reference: dict[str, Any]
    ) -> dict[str, Any]:
        entity_type = self._required_text(
            reference.get("entity_type"), "Entity type is required."
        )
        entity_id = self._required_text(reference.get("entity_id"), "Entity id is required.")
        collections = ENTITY_COLLECTIONS.get(entity_type)
        if not collections:
            raise OperationalCollaborationError(
                f"Unsupported communication entity type: {entity_type}.",
                "UNSUPPORTED_ENTITY_TYPE",
            )
        for collection_name in collections:
            record = await self.db.collection(collection_name).find_one(
                {"agency_id": agency_id, "id": entity_id}
            )
            if record:
                return record
        raise OperationalCollaborationError(
            "Referenced business entity was not found in this Agency.",
            "ENTITY_REFERENCE_NOT_FOUND",
        )

    async def validate_attachment_reference(
        self,
        agency_id: str,
        reference_type: str,
        reference_id: str,
        document_id: str | None = None,
    ) -> dict[str, Any]:
        entity_type = "document" if document_id or reference_type == "document" else reference_type
        entity_id = document_id or reference_id
        return await self.validate_entity_reference(
            agency_id, {"entity_type": entity_type, "entity_id": entity_id}
        )

    def portal_visibility(self, ctx: dict[str, Any]) -> set[str]:
        return (
            {"passenger"}
            if ctx.get("subject_type") == "passenger"
            else {"client"}
        )

    def portal_actor(self, ctx: dict[str, Any]) -> dict[str, Any]:
        identity = ctx.get("identity") or {}
        account = ctx.get("account") or {}
        subject_type = ctx.get("subject_type")
        subject = ctx.get("passenger") if subject_type == "passenger" else ctx.get("client")
        return {
            "id": account.get("id"),
            "identity_id": identity.get("id"),
            "actor_type": (
                "passenger_portal" if subject_type == "passenger" else "client_portal"
            ),
            "display_name": (subject or {}).get("display_name")
            or (subject or {}).get("preferred_name")
            or "Portal user",
            "portal_account_id": account.get("id"),
            "client_id": account.get("client_profile_id") or account.get("client_id"),
            "passenger_id": account.get("passenger_profile_id"),
        }

    async def migration_analysis(
        self, maximum_records_per_collection: int = 5000
    ) -> dict[str, Any]:
        limit = max(1, min(int(maximum_records_per_collection), 10000))
        communication_counts: list[dict[str, Any]] = []
        for item in LEGACY_COMMUNICATION_STRUCTURES:
            collection = item["structure"]
            communication_counts.append(
                {
                    **item,
                    "record_count": await self.db.collection(collection).count(),
                }
            )
        timeline_counts: list[dict[str, Any]] = []
        for item in LEGACY_TIMELINE_STRUCTURES:
            collection = item["structure"]
            timeline_counts.append(
                {
                    **item,
                    "record_count": await self.db.collection(collection).count(),
                }
            )
        orphan_notes = await self._orphan_count(
            "request_messages", "travel_requests", "request_id", limit
        )
        orphan_after_sales = await self._orphan_count(
            "after_sales_communication_records", "after_sales_cases", "case_id", limit
        )
        duplicate_threads = await self._duplicate_thread_candidates(limit)
        duplicate_attachments = await self._duplicate_attachment_candidates(limit)
        timeline_duplicates = await self._timeline_duplicate_candidates(limit)
        missing_entity_links = await self._missing_entity_link_candidates(limit)
        missing_attachment_links = await self._missing_attachment_link_candidates(
            limit
        )
        legacy_note_fields = await self._legacy_note_field_counts(limit)
        return {
            "mode": "dry_run",
            "write_mode_available": False,
            "writes_performed": 0,
            "maximum_records_per_collection": limit,
            "communication_structures": communication_counts,
            "timeline_structures": timeline_counts,
            "orphan_notes": {
                "request_messages": orphan_notes,
                "after_sales_communications": orphan_after_sales,
            },
            "duplicate_thread_candidates": duplicate_threads,
            "duplicate_attachment_candidates": duplicate_attachments,
            "timeline_duplicate_candidates": timeline_duplicates,
            "missing_entity_link_candidates": missing_entity_links,
            "missing_attachment_link_candidates": missing_attachment_links,
            "legacy_note_field_counts": legacy_note_fields,
            "manual_review_required": any(
                [
                    orphan_notes,
                    orphan_after_sales,
                    duplicate_threads,
                    duplicate_attachments,
                    timeline_duplicates,
                    missing_entity_links,
                    missing_attachment_links,
                    any(legacy_note_fields.values()),
                ]
            ),
        }

    def safety_flags(self) -> dict[str, bool]:
        return {
            "canonical_operational_timeline": True,
            "canonical_communication_threads": True,
            "timeline_append_only": True,
            "timeline_immutable_business_history": True,
            "message_deletion_prohibited": True,
            "message_edit_history_preserved": True,
            "attachments_reference_only": True,
            "notification_projection_only": True,
            "external_email_disabled": True,
            "external_sms_disabled": True,
            "external_chat_disabled": True,
            "provider_integrations_disabled": True,
            "background_delivery_disabled": True,
        }

    async def _create_participant(
        self,
        agency_id: str,
        thread_id: str,
        payload: CommunicationParticipantCreate | dict[str, Any],
        actor: dict[str, Any],
    ) -> dict[str, Any]:
        data = self._payload(payload)
        participant_type = str(data.get("participant_type") or "")
        if participant_type not in PARTICIPANT_TYPES:
            raise OperationalCollaborationError(
                f"Unsupported participant type: {participant_type}.",
                "UNSUPPORTED_PARTICIPANT_TYPE",
            )
        await self._validate_participant_scope(agency_id, data)
        natural_key = "|".join(
            [
                participant_type,
                str(data.get("identity_id") or ""),
                str(data.get("portal_account_id") or ""),
                str(data.get("client_id") or ""),
                str(data.get("passenger_id") or ""),
                str(data.get("supplier_reference") or ""),
                str(data.get("airline_code") or ""),
            ]
        )
        participant_id = self._stable_id(
            "cpt", agency_id, f"{thread_id}:{natural_key}"
        )
        existing = await self.db.collection(PARTICIPANT_COLLECTION).find_one(
            {"agency_id": agency_id, "id": participant_id}
        )
        if existing:
            return existing
        visibility = self._visibility_list(
            data.get("visibility") or self._default_participant_visibility(participant_type)
        )
        participant = CommunicationParticipant(
            id=participant_id,
            agency_id=agency_id,
            thread_id=thread_id,
            participant_type=participant_type,
            identity_id=data.get("identity_id"),
            portal_account_id=data.get("portal_account_id"),
            client_id=data.get("client_id"),
            passenger_id=data.get("passenger_id"),
            supplier_reference=data.get("supplier_reference"),
            airline_code=data.get("airline_code"),
            display_name=self._required_text(
                data.get("display_name"), "Participant display name is required."
            ),
            participant_role=data.get("participant_role"),
            permissions=list(data.get("permissions") or self._default_permissions(participant_type)),
            visibility=visibility,
            created_by_actor_id=actor.get("identity_id") or actor.get("id"),
        )
        return await self.db.collection(PARTICIPANT_COLLECTION).insert_one(
            participant.model_dump(mode="json")
        )

    async def _linked_portal_participant_payloads(
        self,
        agency_id: str,
        references: list[dict[str, Any]],
        visibility: list[str],
    ) -> list[dict[str, Any]]:
        client_ids: set[str] = set()
        passenger_ids: set[str] = set()
        for reference in references:
            entity_type = reference["entity_type"]
            entity_id = reference["entity_id"]
            record = await self.validate_entity_reference(agency_id, reference)
            if entity_type == "client":
                client_ids.add(entity_id)
            if entity_type == "passenger":
                passenger_ids.add(entity_id)
            linked_client = (
                record.get("client_id")
                or record.get("primary_client_id")
                or record.get("client_profile_id")
            )
            if linked_client:
                client_ids.add(str(linked_client))
            passenger_ids.update(
                str(value)
                for value in (
                    list(record.get("passenger_ids") or [])
                    + [record.get("passenger_id")]
                )
                if value
            )
            if entity_type == "request":
                request_passengers = await self.db.collection(
                    "request_passengers"
                ).find_many(
                    {"agency_id": agency_id, "request_id": entity_id, "status": "active"},
                    sort=[("created_at", 1), ("id", 1)],
                    limit=MAX_LIST_LIMIT,
                )
                passenger_ids.update(
                    str(item["passenger_id"])
                    for item in request_passengers
                    if item.get("passenger_id")
                )
            if entity_type == "trip":
                trip_passengers = await self.db.collection(
                    "trip_passengers"
                ).find_many(
                    {"agency_id": agency_id, "trip_id": entity_id},
                    sort=[("created_at", 1), ("id", 1)],
                    limit=MAX_LIST_LIMIT,
                )
                passenger_ids.update(
                    str(item["passenger_id"])
                    for item in trip_passengers
                    if item.get("passenger_id")
                )

        payloads: list[dict[str, Any]] = []
        if "client" in visibility:
            for client_id in sorted(client_ids):
                mapping = await self.db.collection(
                    "portal_access_mappings"
                ).find_one(
                    {
                        "agency_id": agency_id,
                        "subject_type": "client",
                        "client_profile_id": client_id,
                        "status": "active",
                    }
                )
                if not mapping:
                    continue
                client = await self.db.collection("client_profiles").find_one(
                    {"agency_id": agency_id, "id": client_id}
                )
                payloads.append(
                    {
                        "participant_type": "client_portal",
                        "identity_id": mapping.get("auth_identity_id"),
                        "portal_account_id": mapping.get("id"),
                        "client_id": client_id,
                        "display_name": (client or {}).get("display_name")
                        or "Client Portal",
                        "visibility": ["client"],
                    }
                )
        if "passenger" in visibility:
            for passenger_id in sorted(passenger_ids):
                mapping = await self.db.collection(
                    "portal_access_mappings"
                ).find_one(
                    {
                        "agency_id": agency_id,
                        "subject_type": "passenger",
                        "passenger_profile_id": passenger_id,
                        "status": "active",
                    }
                )
                if not mapping:
                    continue
                passenger = await self.db.collection(
                    "passenger_profiles"
                ).find_one({"agency_id": agency_id, "id": passenger_id})
                payloads.append(
                    {
                        "participant_type": "passenger_portal",
                        "identity_id": mapping.get("auth_identity_id"),
                        "portal_account_id": mapping.get("id"),
                        "passenger_id": passenger_id,
                        "display_name": (passenger or {}).get("display_name")
                        or (passenger or {}).get("preferred_name")
                        or "Passenger Portal",
                        "visibility": ["passenger"],
                    }
                )
        return payloads

    def _deduplicate_participant_payloads(
        self, payloads: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        unique: list[dict[str, Any]] = []
        seen: set[tuple[Any, ...]] = set()
        for payload in payloads:
            key = (
                payload.get("participant_type"),
                payload.get("identity_id"),
                payload.get("portal_account_id"),
                payload.get("client_id"),
                payload.get("passenger_id"),
                payload.get("supplier_reference"),
                payload.get("airline_code"),
            )
            if key in seen:
                continue
            seen.add(key)
            unique.append(payload)
        return unique

    async def _validate_participant_scope(
        self, agency_id: str, data: dict[str, Any]
    ) -> None:
        participant_type = str(data.get("participant_type") or "")
        if participant_type in {"client_portal", "passenger_portal"}:
            identity_id = self._required_text(
                data.get("identity_id"), "Portal participant identity is required."
            )
            filters: dict[str, Any] = {
                "agency_id": agency_id,
                "auth_identity_id": identity_id,
                "status": "active",
            }
            if participant_type == "client_portal":
                client_id = self._required_text(
                    data.get("client_id"), "Client Portal participant client is required."
                )
                mapping = await self.db.collection("portal_access_mappings").find_one(
                    filters
                )
                if not mapping or (
                    mapping.get("client_profile_id") or mapping.get("client_id")
                ) != client_id:
                    raise OperationalCollaborationError(
                        "Client Portal participant is not actively mapped in this Agency.",
                        "PORTAL_PARTICIPANT_INVALID",
                    )
            else:
                passenger_id = self._required_text(
                    data.get("passenger_id"),
                    "Passenger Portal participant passenger is required.",
                )
                mapping = await self.db.collection("portal_access_mappings").find_one(
                    filters
                )
                if not mapping or mapping.get("passenger_profile_id") != passenger_id:
                    raise OperationalCollaborationError(
                        "Passenger Portal participant is not actively mapped in this Agency.",
                        "PORTAL_PARTICIPANT_INVALID",
                    )
        if participant_type == "agency":
            identity_id = data.get("identity_id")
            if identity_id:
                membership = await self.db.collection(
                    "agency_staff_memberships"
                ).find_one(
                    {
                        "agency_id": agency_id,
                        "identity_id": identity_id,
                        "status": "active",
                    }
                )
                if not membership:
                    membership = await self.db.collection(
                        "agency_staff_memberships"
                    ).find_one(
                        {
                            "agency_id": agency_id,
                            "user_id": identity_id,
                            "status": "active",
                        }
                    )
                if not membership:
                    raise OperationalCollaborationError(
                        "Agency participant requires an active Agency membership.",
                        "AGENCY_PARTICIPANT_INVALID",
                    )

    async def _resolve_sender_participant(
        self,
        agency_id: str,
        thread_id: str,
        participant_id: str | None,
        actor: dict[str, Any],
    ) -> dict[str, Any]:
        if participant_id:
            participant = await self.db.collection(PARTICIPANT_COLLECTION).find_one(
                {
                    "agency_id": agency_id,
                    "thread_id": thread_id,
                    "id": participant_id,
                    "status": "active",
                }
            )
            if not participant:
                raise OperationalCollaborationError(
                    "Sender participant does not belong to this thread.",
                    "SENDER_PARTICIPANT_MISMATCH",
                )
            self._assert_actor_matches_participant(actor, participant)
            return participant
        actor_type = self._actor_type(actor)
        page = await PersistenceRepository(self.db).find_agency_records(
            collection_name=PARTICIPANT_COLLECTION,
            agency_id=agency_id,
            filters={
                "thread_id": thread_id,
                "participant_type": actor_type,
                "status": "active",
            },
            sort_field="created_at",
            sort_direction="asc",
            pagination=PaginationRequest.build(limit=MAX_LIST_LIMIT),
        )
        participants = page.items
        for participant in participants:
            try:
                self._assert_actor_matches_participant(actor, participant)
                return participant
            except OperationalCollaborationError:
                continue
        raise OperationalCollaborationError(
            "The authenticated actor is not a participant in this thread.",
            "THREAD_PARTICIPATION_REQUIRED",
        )

    def _assert_actor_matches_participant(
        self, actor: dict[str, Any], participant: dict[str, Any]
    ) -> None:
        actor_type = self._actor_type(actor)
        if participant.get("participant_type") != actor_type:
            raise OperationalCollaborationError(
                "Sender participant type does not match the authenticated actor.",
                "SENDER_PARTICIPANT_MISMATCH",
            )
        if actor_type in {"client_portal", "passenger_portal"}:
            if participant.get("identity_id") != actor.get("identity_id"):
                raise OperationalCollaborationError(
                    "Portal sender identity does not match the thread participant.",
                    "SENDER_PARTICIPANT_MISMATCH",
                )
        elif actor_type == "agency":
            actor_identity = actor.get("identity_id")
            actor_user = actor.get("id")
            if participant.get("identity_id") not in {actor_identity, actor_user}:
                raise OperationalCollaborationError(
                    "Agency sender identity does not match the thread participant.",
                    "SENDER_PARTICIPANT_MISMATCH",
                )

    async def _validate_recipients(
        self, agency_id: str, thread_id: str, recipient_ids: list[str]
    ) -> None:
        for recipient_id in recipient_ids:
            participant = await self.db.collection(PARTICIPANT_COLLECTION).find_one(
                {
                    "agency_id": agency_id,
                    "thread_id": thread_id,
                    "id": recipient_id,
                    "status": "active",
                }
            )
            if not participant:
                raise OperationalCollaborationError(
                    "A recipient does not belong to this communication thread.",
                    "RECIPIENT_PARTICIPANT_MISMATCH",
                )

    async def _validate_attachments(
        self, agency_id: str, thread_id: str, attachment_ids: list[str]
    ) -> None:
        for attachment_id in attachment_ids:
            attachment = await self.db.collection(ATTACHMENT_COLLECTION).find_one(
                {
                    "agency_id": agency_id,
                    "thread_id": thread_id,
                    "id": attachment_id,
                }
            )
            if not attachment:
                raise OperationalCollaborationError(
                    "An attachment does not belong to this communication thread.",
                    "ATTACHMENT_THREAD_MISMATCH",
                )

    def _assert_message_visibility(
        self,
        sender: dict[str, Any],
        visibility: str,
        thread: dict[str, Any],
    ) -> None:
        participant_type = sender.get("participant_type")
        allowed_by_actor = {
            "agency": {"internal", "agency", "client", "passenger", "supplier"},
            "platform": {"platform"},
            "client_portal": {"client"},
            "passenger_portal": {"passenger"},
            "supplier": {"supplier"},
            "airline": {"supplier"},
            "system": {"system", "internal"},
        }.get(participant_type, set())
        if visibility not in allowed_by_actor:
            raise OperationalCollaborationError(
                "Message visibility is not permitted for this participant.",
                "MESSAGE_VISIBILITY_FORBIDDEN",
            )
        if visibility not in set(thread.get("visibility") or []):
            raise OperationalCollaborationError(
                "Message visibility is outside the thread visibility contract.",
                "THREAD_VISIBILITY_MISMATCH",
            )

    async def _portal_participants(self, ctx: dict[str, Any]) -> list[dict[str, Any]]:
        actor = self.portal_actor(ctx)
        filters = {
            "agency_id": ctx["account"]["agency_id"],
            "participant_type": actor["actor_type"],
            "identity_id": actor["identity_id"],
            "status": "active",
        }
        page = await PersistenceRepository(self.db).find_agency_records(
            collection_name=PARTICIPANT_COLLECTION,
            agency_id=ctx["account"]["agency_id"],
            filters={key: value for key, value in filters.items() if key != "agency_id"},
            sort_field="created_at",
            sort_direction="asc",
            pagination=PaginationRequest.build(limit=MAX_LIST_LIMIT),
        )
        return page.items

    async def _portal_can_access_thread_entities(
        self, ctx: dict[str, Any], thread: dict[str, Any]
    ) -> bool:
        agency_id = ctx["account"]["agency_id"]
        subject_type = ctx.get("subject_type")
        client_id = ctx["account"].get("client_profile_id") or ctx["account"].get(
            "client_id"
        )
        passenger_id = ctx["account"].get("passenger_profile_id")
        for reference in thread.get("entity_references") or []:
            entity_type = reference.get("entity_type")
            entity_id = reference.get("entity_id")
            for collection_name in ENTITY_COLLECTIONS.get(entity_type, ()):
                record = await self.db.collection(collection_name).find_one(
                    {"agency_id": agency_id, "id": entity_id}
                )
                if not record:
                    continue
                if subject_type == "passenger":
                    if entity_type == "passenger" and entity_id == passenger_id:
                        return True
                    linked_passengers = set(
                        (record.get("passenger_ids") or [])
                        + [record.get("passenger_id")]
                    )
                    if passenger_id in linked_passengers:
                        return True
                    if entity_type == "request":
                        request_passenger = await self.db.collection(
                            "request_passengers"
                        ).find_one(
                            {
                                "agency_id": agency_id,
                                "request_id": entity_id,
                                "passenger_id": passenger_id,
                                "status": "active",
                            }
                        )
                        if request_passenger:
                            return True
                    if entity_type == "trip":
                        trip_passenger = await self.db.collection(
                            "trip_passengers"
                        ).find_one(
                            {
                                "agency_id": agency_id,
                                "trip_id": entity_id,
                                "passenger_id": passenger_id,
                            }
                        )
                        if trip_passenger:
                            return True
                    continue
                if entity_type == "client" and entity_id == client_id:
                    return True
                linked_client_id = (
                    record.get("client_id")
                    or record.get("primary_client_id")
                    or record.get("client_profile_id")
                )
                if linked_client_id == client_id:
                    return True
        return False

    async def _project_notification(self, timeline: dict[str, Any]) -> None:
        notification_type = self._notification_type(timeline)
        if not notification_type:
            return
        projection_key = f"timeline:{timeline['id']}:{notification_type}"
        projection_id = self._stable_id(
            "ntf", timeline["agency_id"], projection_key
        )
        existing = await self.db.collection(NOTIFICATION_COLLECTION).find_one(
            {"agency_id": timeline["agency_id"], "id": projection_id}
        )
        if existing:
            return
        projection = NotificationProjection(
            id=projection_id,
            agency_id=timeline["agency_id"],
            timeline_entry_id=timeline["id"],
            notification_type=notification_type,
            status="unread",
            title=timeline.get("summary") or timeline.get("event_type") or "Activity",
            summary=timeline.get("summary"),
            visibility=self._canonical_visibility(timeline),
            projection_key=projection_key,
            source_event_type=timeline.get("event_type") or "other",
            metadata={
                "entity_type": timeline.get("entity_type"),
                "entity_id": timeline.get("entity_id"),
                "regenerable": True,
            },
        )
        await self.db.collection(NOTIFICATION_COLLECTION).insert_one(
            projection.model_dump(mode="json")
        )

    async def _audit(
        self,
        *,
        agency_id: str,
        actor: dict[str, Any],
        event_type: str,
        entity_type: str,
        entity_id: str,
        summary: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        event = AuditEvent(
            agency_id=agency_id,
            actor_user_id=actor.get("id"),
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            summary=summary,
            metadata={
                **metadata,
                "actor_identity_id": actor.get("identity_id"),
                "actor_type": self._actor_type(actor),
            },
        )
        return await self.db.collection(AUDIT_COLLECTION).insert_one(
            event.model_dump(mode="json")
        )

    async def _orphan_count(
        self,
        source_collection: str,
        target_collection: str,
        source_field: str,
        limit: int,
    ) -> int:
        records = await self.db.collection(source_collection).find_many(
            {}, sort=[("created_at", 1), ("id", 1)], limit=limit
        )
        count = 0
        for record in records:
            target_id = record.get(source_field)
            if not target_id:
                count += 1
                continue
            target = await self.db.collection(target_collection).find_one(
                {"agency_id": record.get("agency_id"), "id": target_id}
            )
            if not target:
                count += 1
        return count

    async def _duplicate_thread_candidates(self, limit: int) -> int:
        threads = await self.db.collection(THREAD_COLLECTION).find_many(
            {}, sort=[("created_at", 1), ("id", 1)], limit=limit
        )
        seen: set[str] = set()
        duplicates = 0
        for thread in threads:
            refs = "|".join(
                sorted(
                    f"{item.get('entity_type')}:{item.get('entity_id')}"
                    for item in thread.get("entity_references") or []
                )
            )
            key = f"{thread.get('agency_id')}|{refs}|{str(thread.get('subject') or '').lower()}"
            if key in seen:
                duplicates += 1
            seen.add(key)
        return duplicates

    async def _duplicate_attachment_candidates(self, limit: int) -> int:
        attachments = await self.db.collection(ATTACHMENT_COLLECTION).find_many(
            {}, sort=[("created_at", 1), ("id", 1)], limit=limit
        )
        seen: set[str] = set()
        duplicates = 0
        for item in attachments:
            key = (
                f"{item.get('agency_id')}|{item.get('thread_id')}|"
                f"{item.get('reference_type')}|{item.get('reference_id')}"
            )
            if key in seen:
                duplicates += 1
            seen.add(key)
        return duplicates

    async def _timeline_duplicate_candidates(self, limit: int) -> int:
        entries = await self.db.collection(TIMELINE_COLLECTION).find_many(
            {}, sort=[("event_time", 1), ("id", 1)], limit=limit
        )
        seen: set[str] = set()
        duplicates = 0
        for item in entries:
            key = item.get("idempotency_key")
            if not key:
                continue
            scoped = f"{item.get('agency_id')}|{key}"
            if scoped in seen:
                duplicates += 1
            seen.add(scoped)
        return duplicates

    async def _missing_entity_link_candidates(self, limit: int) -> int:
        missing = 0
        threads = await self.db.collection(THREAD_COLLECTION).find_many(
            {}, sort=[("created_at", 1), ("id", 1)], limit=limit
        )
        for thread in threads:
            references = thread.get("entity_references") or []
            if not references:
                missing += 1
                continue
            for reference in references:
                try:
                    await self.validate_entity_reference(
                        str(thread.get("agency_id") or ""), reference
                    )
                except OperationalCollaborationError:
                    missing += 1
        entries = await self.db.collection(TIMELINE_COLLECTION).find_many(
            {}, sort=[("event_time", 1), ("id", 1)], limit=limit
        )
        missing += len(
            [
                item
                for item in entries
                if not item.get("entity_type") or not item.get("entity_id")
            ]
        )
        return missing

    async def _missing_attachment_link_candidates(self, limit: int) -> int:
        missing = 0
        attachments = await self.db.collection(ATTACHMENT_COLLECTION).find_many(
            {}, sort=[("created_at", 1), ("id", 1)], limit=limit
        )
        for attachment in attachments:
            try:
                await self.validate_attachment_reference(
                    str(attachment.get("agency_id") or ""),
                    str(attachment.get("reference_type") or ""),
                    str(attachment.get("reference_id") or ""),
                    attachment.get("document_id"),
                )
            except OperationalCollaborationError:
                missing += 1
        return missing

    async def _legacy_note_field_counts(self, limit: int) -> dict[str, int]:
        sources = {
            "travel_requests.internal_notes": ("travel_requests", "internal_notes"),
            "trip_dossiers.internal_notes": ("trip_dossiers", "internal_notes"),
            "booking_records.internal_notes": ("booking_records", "internal_notes"),
            "ticket_records.internal_notes": ("ticket_records", "internal_notes"),
            "emd_records.internal_notes": ("emd_records", "internal_notes"),
            "invoices.internal_notes": ("invoices", "internal_notes"),
            "documents.internal_notes": ("documents", "internal_notes"),
        }
        counts: dict[str, int] = {}
        for label, (collection, field) in sources.items():
            records = await self.db.collection(collection).find_many(
                {}, sort=[("created_at", 1), ("id", 1)], limit=limit
            )
            counts[label] = len(
                [item for item in records if str(item.get(field) or "").strip()]
            )
        return counts

    def _payload(self, payload: Any) -> dict[str, Any]:
        if hasattr(payload, "model_dump"):
            return payload.model_dump(mode="json", exclude_none=True)
        return {key: value for key, value in dict(payload).items() if value is not None}

    def _actor_type(
        self, actor: dict[str, Any], requested: str | None = None
    ) -> str:
        value = str(
            requested
            or actor.get("actor_type")
            or (
                "platform"
                if actor.get("global_role")
                else "agency"
                if actor.get("id")
                else "system"
            )
        )
        return value if value in PARTICIPANT_TYPES else "system"

    def _actor_participant_present(
        self, participants: list[dict[str, Any]], actor: dict[str, Any]
    ) -> bool:
        actor_type = self._actor_type(actor)
        actor_identity = actor.get("identity_id") or actor.get("id")
        return any(
            item.get("participant_type") == actor_type
            and (
                actor_type in {"supplier", "airline", "system"}
                or item.get("identity_id") == actor_identity
            )
            for item in participants
        )

    def _actor_participant_payload(
        self, actor: dict[str, Any]
    ) -> dict[str, Any]:
        actor_type = self._actor_type(actor)
        return {
            "participant_type": actor_type,
            "identity_id": actor.get("identity_id") or actor.get("id"),
            "portal_account_id": actor.get("portal_account_id"),
            "client_id": actor.get("client_id"),
            "passenger_id": actor.get("passenger_id"),
            "display_name": actor.get("full_name")
            or actor.get("display_name")
            or actor_type.replace("_", " ").title(),
            "participant_role": actor.get("agency_role") or actor.get("global_role"),
            "permissions": self._default_permissions(actor_type),
            "visibility": self._default_participant_visibility(actor_type),
        }

    def _default_permissions(self, participant_type: str) -> list[str]:
        return {
            "agency": ["read", "post", "edit_own", "close"],
            "platform": ["read"],
            "client_portal": ["read", "post", "edit_own"],
            "passenger_portal": ["read", "post", "edit_own"],
            "supplier": ["read", "post"],
            "airline": ["read", "post"],
            "system": ["append_event"],
        }.get(participant_type, ["read"])

    def _default_participant_visibility(self, participant_type: str) -> list[str]:
        return {
            "agency": ["internal", "agency", "client", "passenger", "supplier"],
            "platform": ["platform"],
            "client_portal": ["client"],
            "passenger_portal": ["passenger"],
            "supplier": ["supplier"],
            "airline": ["supplier"],
            "system": ["system", "internal"],
        }.get(participant_type, ["internal"])

    def _visibility_list(self, values: Any) -> list[str]:
        normalized = [
            self._required_visibility(item)
            for item in (values if isinstance(values, list) else [values or "internal"])
        ]
        return list(dict.fromkeys(normalized))

    def _required_visibility(self, value: Any) -> str:
        visibility = str(value or "internal")
        legacy = {
            "client_visible": "client",
            "passenger_visible": "passenger",
            "airline_visible": "supplier",
        }
        visibility = legacy.get(visibility, visibility)
        if visibility not in VISIBILITY_VALUES:
            raise OperationalCollaborationError(
                f"Unsupported communication visibility: {visibility}.",
                "UNSUPPORTED_VISIBILITY",
            )
        return visibility

    def _canonical_visibility(self, item: dict[str, Any]) -> str:
        if item.get("visibility"):
            value = item["visibility"]
            if isinstance(value, list):
                return str(value[0]) if value else "internal"
            return self._required_visibility(value)
        if item.get("passenger_visible"):
            return "passenger"
        if item.get("airline_visible"):
            return "supplier"
        return "internal"

    def _derive_entity(self, data: dict[str, Any]) -> tuple[str | None, str | None]:
        if data.get("entity_type") and data.get("entity_id"):
            return str(data["entity_type"]), str(data["entity_id"])
        candidates = [
            ("request", data.get("linked_request") or data.get("travel_request_workspace_id")),
            ("trip", data.get("linked_trip") or data.get("trip_workspace_id")),
            ("booking", data.get("linked_booking") or data.get("booking_workspace_id")),
            ("ticket", data.get("linked_ticket") or data.get("ticket_workspace_id")),
            ("emd", data.get("linked_emd") or data.get("emd_workspace_id")),
            ("document", data.get("linked_document_id") or data.get("document_workspace_id")),
            ("passenger", data.get("passenger_workspace_id")),
        ]
        return next(((kind, value) for kind, value in candidates if value), (None, None))

    def _canonical_links(self, entity_type: str, entity_id: str) -> dict[str, str]:
        field = {
            "request": "linked_request",
            "offer": "linked_offer",
            "trip": "linked_trip",
            "booking": "linked_booking",
            "booking_workspace": "linked_booking",
            "ticket": "linked_ticket",
            "emd": "linked_emd",
            "document": "linked_document_id",
            "invoice": "linked_finance_record",
            "payment": "linked_finance_record",
            "supplier_cost": "linked_finance_record",
            "refund": "linked_finance_record",
            "exchange": "linked_finance_record",
        }.get(entity_type)
        return {field: entity_id} if field else {}

    def _event_category(self, event_type: str) -> str:
        if event_type.startswith("communication") or event_type == "manual_note":
            return "communication"
        if event_type.startswith(("invoice", "payment", "refund", "exchange", "supplier_cost")):
            return "finance"
        if event_type.startswith("document"):
            return "document"
        if event_type.startswith("portal"):
            return "portal"
        return "operations"

    def _canonical_event_type(
        self, source_event_type: str, *, entity_type: str | None = None
    ) -> str:
        value = str(source_event_type or "").lower().replace("-", "_")
        normalized = value.replace(".", "_")
        exact = {
            "request_created": "request_created",
            "offer_created": "offer_created",
            "offer_revised": "offer_revised",
            "offer_delivered": "offer_delivered",
            "offer_sent": "offer_delivered",
            "offer_accepted": "offer_accepted",
            "offer_declined": "offer_declined",
            "trip_confirmed": "trip_confirmed",
            "booking_prepared": "booking_prepared",
            "booking_confirmed": "booking_confirmed",
            "ticket_imported": "ticket_imported",
            "emd_imported": "emd_imported",
            "invoice_issued": "invoice_issued",
            "payment_received": "payment_received",
            "refund_recorded": "refund_recorded",
            "exchange_recorded": "exchange_recorded",
            "supplier_cost_confirmed": "supplier_cost_confirmed",
            "portal_login": "portal_login",
            "portal_approval": "portal_approval",
            "document_uploaded": "document_uploaded",
            "document_delivered": "document_delivered",
            "communication_sent": "communication_sent",
            "communication_received": "communication_received",
            "manual_note": "manual_note",
            "assignment": "assignment",
        }
        if normalized in exact:
            return exact[normalized]
        if "offer" in normalized:
            if "accept" in normalized:
                return "offer_accepted"
            if "declin" in normalized or "reject" in normalized:
                return "offer_declined"
            if "deliver" in normalized or "sent" in normalized:
                return "offer_delivered"
            if "creat" in normalized:
                return "offer_created"
            if "updat" in normalized or "revis" in normalized:
                return "offer_revised"
        if entity_type == "request" and "creat" in normalized:
            return "request_created"
        if entity_type == "trip" and "confirm" in normalized:
            return "trip_confirmed"
        if entity_type in {"booking", "booking_workspace"}:
            if "confirm" in normalized or "booked" in normalized:
                return "booking_confirmed"
            if "creat" in normalized or "prepar" in normalized:
                return "booking_prepared"
        if entity_type == "ticket" and (
            "import" in normalized or "external_result" in normalized
        ):
            return "ticket_imported"
        if entity_type == "emd" and (
            "import" in normalized or "external_result" in normalized
        ):
            return "emd_imported"
        if entity_type == "document":
            if "deliver" in normalized or "sent" in normalized:
                return "document_delivered"
            if "upload" in normalized or "render" in normalized:
                return "document_uploaded"
        if "assign" in normalized:
            return "assignment"
        if "message" in normalized or "communication" in normalized:
            return (
                "communication_received"
                if "receiv" in normalized or "portal" in normalized
                else "communication_sent"
            )
        return "status_transition"

    def _notification_type(self, timeline: dict[str, Any]) -> str | None:
        event_type = str(timeline.get("event_type") or "")
        status = str(timeline.get("event_status") or "")
        priority = str(timeline.get("event_priority") or "")
        if status == "failed":
            return "failed"
        if event_type in {"approval_requested", "portal_approval"}:
            return "approval_required"
        if event_type in {"deadline_reached", "reminder"}:
            return "deadline"
        if priority in {"urgent", "critical"}:
            return "warning"
        if event_type in {
            "communication_received",
            "document_uploaded",
            "payment_received",
        }:
            return "action_required"
        return None

    def _timeline_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        projected["visibility"] = self._canonical_visibility(projected)
        projected["event_time"] = projected.get("event_time") or projected.get(
            "created_at"
        )
        projected["ordering_key"] = projected.get("ordering_key") or (
            f"{projected.get('event_time') or projected.get('created_at')}|"
            f"{projected.get('id')}"
        )
        projected["append_only"] = True
        projected["immutable_business_history"] = True
        return projected

    def _participant_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            key: value
            for key, value in item.items()
            if key
            not in {
                "permissions",
                "metadata",
            }
        } | {"permissions": list(item.get("permissions") or [])}

    def _message_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        projected["visibility"] = self._canonical_visibility(projected)
        projected["deletion_prohibited"] = True
        return projected

    def _portal_thread_summary(self, thread: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": thread.get("id"),
            "thread_reference": thread.get("thread_reference"),
            "subject": thread.get("subject"),
            "status": thread.get("status"),
            "entity_references": list(thread.get("entity_references") or []),
            "last_message_at": thread.get("last_message_at"),
            "message_count": int(thread.get("message_count") or 0),
            "created_at": thread.get("created_at"),
            "updated_at": thread.get("updated_at"),
            "closed_at": thread.get("closed_at"),
        }

    def _portal_thread_projection(
        self, detail: dict[str, Any]
    ) -> dict[str, Any]:
        return {
            "thread": self._portal_thread_summary(detail["thread"]),
            "participants": [
                {
                    "id": item.get("id"),
                    "participant_type": item.get("participant_type"),
                    "display_name": item.get("display_name"),
                }
                for item in detail.get("participants") or []
            ],
            "messages": [
                {
                    "id": item.get("id"),
                    "thread_id": item.get("thread_id"),
                    "sender_type": item.get("sender_type"),
                    "sender_display": item.get("sender_display"),
                    "message_type": item.get("message_type"),
                    "plain_text": item.get("plain_text"),
                    "rich_text": item.get("rich_text"),
                    "attachment_ids": list(item.get("attachment_ids") or []),
                    "delivery_status": item.get("delivery_status"),
                    "visibility": item.get("visibility"),
                    "edited_at": item.get("edited_at"),
                    "edit_history": [
                        {
                            "plain_text": version.get("plain_text"),
                            "rich_text": version.get("rich_text"),
                            "edited_at": version.get("edited_at"),
                        }
                        for version in item.get("edit_history") or []
                    ],
                    "created_at": item.get("created_at"),
                    "deletion_prohibited": True,
                }
                for item in detail.get("messages") or []
            ],
            "attachments": [
                {
                    "id": item.get("id"),
                    "thread_id": item.get("thread_id"),
                    "message_id": item.get("message_id"),
                    "document_id": item.get("document_id"),
                    "reference_type": item.get("reference_type"),
                    "reference_id": item.get("reference_id"),
                    "title": item.get("title"),
                    "media_type": item.get("media_type"),
                    "visibility": item.get("visibility"),
                    "created_at": item.get("created_at"),
                    "immutable": True,
                    "binary_duplicated": False,
                }
                for item in detail.get("attachments") or []
            ],
        }

    def _timeline_visibility_for_thread(self, values: list[str]) -> str:
        for value in ["client", "passenger", "supplier", "agency", "internal"]:
            if value in values:
                return value
        return "internal"

    def _message_summary(self, message: dict[str, Any]) -> str:
        if message.get("message_type") == "internal_note":
            return "Internal note recorded."
        if message.get("visibility") == "supplier":
            return "Supplier communication recorded."
        if message.get("visibility") in {"client", "passenger"}:
            return "Portal communication recorded."
        return "Operational communication recorded."

    def _search_label(self, item_type: str, item: dict[str, Any]) -> str:
        if item_type == "timeline":
            return str(item.get("summary") or item.get("event_type") or "Timeline entry")
        if item_type == "message":
            return str(item.get("plain_text") or "")[:160]
        if item_type == "participant":
            return str(item.get("display_name") or "Participant")
        return str(item.get("title") or item.get("reference_id") or "Attachment")

    def _last_activity_at(
        self, timeline: list[dict[str, Any]], messages: list[dict[str, Any]]
    ) -> Any:
        values = [
            item.get("event_time") or item.get("created_at")
            for item in timeline
        ] + [item.get("created_at") for item in messages]
        values = [value for value in values if value]
        return max(values, key=lambda value: str(value)) if values else None

    def _stable_id(self, prefix: str, agency_id: str, key: str | None) -> str:
        digest = hashlib.sha256(
            f"{agency_id}|{key or ''}".encode("utf-8")
        ).hexdigest()[:28]
        return f"{prefix}_{digest}"

    def _content_hash(self, value: Any) -> str:
        return hashlib.sha256(
            repr(self._stable_value(value)).encode("utf-8")
        ).hexdigest()

    def _stable_value(self, value: Any) -> Any:
        if isinstance(value, dict):
            return tuple(
                (key, self._stable_value(item))
                for key, item in sorted(value.items())
            )
        if isinstance(value, list):
            return tuple(self._stable_value(item) for item in value)
        return value

    def _required_text(self, value: Any, message: str) -> str:
        cleaned = str(value or "").strip()
        if not cleaned:
            raise OperationalCollaborationError(message)
        return cleaned

    def _clean_optional(self, value: Any) -> str | None:
        cleaned = str(value or "").strip()
        return cleaned or None

    def _bounded_limit(self, value: int) -> int:
        return max(1, min(int(value or 100), MAX_LIST_LIMIT))

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)


def operational_collaboration_readiness_metadata() -> dict[str, Any]:
    return {
        "canonical_operational_timeline_enabled": True,
        "canonical_communication_threads_enabled": True,
        "canonical_communication_messages_enabled": True,
        "canonical_participants_enabled": True,
        "canonical_attachment_references_enabled": True,
        "notification_projections_enabled": True,
        "timeline_collection_reused": TIMELINE_COLLECTION,
        "append_only_timeline_enabled": True,
        "immutable_ordering_enabled": True,
        "server_timestamping_enabled": True,
        "message_edit_history_enabled": True,
        "message_deletion_disabled": True,
        "portal_subject_isolation_enabled": True,
        "agency_isolation_enabled": True,
        "supplier_communication_manual_only": True,
        "external_delivery_disabled": True,
        "dry_run_migration_analysis_enabled": True,
        "write_migration_disabled": True,
        "readiness_required": False,
    }
