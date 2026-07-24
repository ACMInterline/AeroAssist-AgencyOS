from __future__ import annotations

import inspect
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable

from database import Database
from services.operational_collaboration_service import (
    ATTACHMENT_COLLECTION,
    MESSAGE_COLLECTION,
    NOTIFICATION_COLLECTION,
    PARTICIPANT_COLLECTION,
    THREAD_COLLECTION,
    TIMELINE_COLLECTION,
    OperationalCollaborationError,
    OperationalCollaborationService,
)


ROOT = Path(__file__).resolve().parents[2]
AGENCY_ID = "collaboration-smoke-agency"
OTHER_AGENCY_ID = "collaboration-smoke-other-agency"
USER_ID = "collaboration-smoke-user"
IDENTITY_ID = "collaboration-smoke-staff-identity"
CLIENT_ID = "collaboration-smoke-client"
CLIENT_IDENTITY_ID = "collaboration-smoke-client-identity"
PASSENGER_ID = "collaboration-smoke-passenger"
PASSENGER_IDENTITY_ID = "collaboration-smoke-passenger-identity"
REQUEST_ID = "collaboration-smoke-request"
TRIP_ID = "collaboration-smoke-trip"
BOOKING_ID = "collaboration-smoke-booking"
DOCUMENT_ID = "collaboration-smoke-document"


@dataclass
class SmokeContext:
    db: Database
    service: OperationalCollaborationService
    actor: dict[str, Any]
    client_ctx: dict[str, Any]
    passenger_ctx: dict[str, Any]
    checks: list[str]

    def check(self, name: str, condition: bool, message: str) -> None:
        if not condition:
            raise AssertionError(f"{name}: {message}")
        self.checks.append(name)


async def insert(
    db: Database, collection: str, record: dict[str, Any]
) -> dict[str, Any]:
    return await db.collection(collection).insert_one(record)


async def expect_error(
    operation: Callable[[], Awaitable[Any]], code: str
) -> OperationalCollaborationError:
    try:
        await operation()
    except OperationalCollaborationError as exc:
        if exc.code != code:
            raise AssertionError(
                f"Expected {code}, received {exc.code}: {exc}"
            ) from exc
        return exc
    raise AssertionError(f"Expected OperationalCollaborationError {code}.")


def parsed_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


async def seed() -> SmokeContext:
    db = Database()
    for agency_id in (AGENCY_ID, OTHER_AGENCY_ID):
        await insert(
            db,
            "agencies",
            {
                "id": agency_id,
                "name": agency_id.replace("-", " ").title(),
                "slug": agency_id,
                "status": "active",
            },
        )
    await insert(
        db,
        "platform_users",
        {
            "id": USER_ID,
            "identity_id": IDENTITY_ID,
            "email": "collaboration.agent@example.test",
            "full_name": "Collaboration Agent",
            "status": "active",
        },
    )
    await insert(
        db,
        "agency_staff_memberships",
        {
            "id": "collaboration-smoke-membership",
            "agency_id": AGENCY_ID,
            "user_id": USER_ID,
            "identity_id": IDENTITY_ID,
            "agency_role": "agency_agent",
            "status": "active",
        },
    )
    await insert(
        db,
        "client_profiles",
        {
            "id": CLIENT_ID,
            "agency_id": AGENCY_ID,
            "display_name": "Avery Client",
            "status": "active",
        },
    )
    await insert(
        db,
        "passenger_profiles",
        {
            "id": PASSENGER_ID,
            "agency_id": AGENCY_ID,
            "client_id": CLIENT_ID,
            "display_name": "Parker Passenger",
            "status": "active",
        },
    )
    await insert(
        db,
        "travel_requests",
        {
            "id": REQUEST_ID,
            "agency_id": AGENCY_ID,
            "client_id": CLIENT_ID,
            "passenger_ids": [PASSENGER_ID],
            "request_reference": "REQ-COLLAB-001",
            "status": "open",
        },
    )
    await insert(
        db,
        "trip_dossiers",
        {
            "id": TRIP_ID,
            "agency_id": AGENCY_ID,
            "client_id": CLIENT_ID,
            "passenger_ids": [PASSENGER_ID],
            "trip_reference": "TRP-COLLAB-001",
            "status": "active",
        },
    )
    await insert(
        db,
        "booking_records",
        {
            "id": BOOKING_ID,
            "agency_id": AGENCY_ID,
            "client_id": CLIENT_ID,
            "trip_id": TRIP_ID,
            "booking_reference": "BKG-COLLAB-001",
            "status": "confirmed",
        },
    )
    await insert(
        db,
        "document_workspaces",
        {
            "id": DOCUMENT_ID,
            "agency_id": AGENCY_ID,
            "passenger_workspace_id": PASSENGER_ID,
            "booking_workspace_id": BOOKING_ID,
            "document_reference": "DOC-COLLAB-001",
            "document_title": "Travel approval",
            "document_status": "verified",
        },
    )
    await insert(
        db,
        "portal_access_mappings",
        {
            "id": "collaboration-smoke-client-mapping",
            "agency_id": AGENCY_ID,
            "auth_identity_id": CLIENT_IDENTITY_ID,
            "subject_type": "client",
            "client_profile_id": CLIENT_ID,
            "status": "active",
        },
    )
    await insert(
        db,
        "portal_access_mappings",
        {
            "id": "collaboration-smoke-passenger-mapping",
            "agency_id": AGENCY_ID,
            "auth_identity_id": PASSENGER_IDENTITY_ID,
            "subject_type": "passenger",
            "passenger_profile_id": PASSENGER_ID,
            "status": "active",
        },
    )
    actor = {
        "id": USER_ID,
        "identity_id": IDENTITY_ID,
        "actor_type": "agency",
        "display_name": "Collaboration Agent",
        "full_name": "Collaboration Agent",
    }
    client_ctx = {
        "account": {
            "id": "collaboration-smoke-client-account",
            "agency_id": AGENCY_ID,
            "client_profile_id": CLIENT_ID,
        },
        "identity": {"id": CLIENT_IDENTITY_ID},
        "subject_type": "client",
        "client": {"id": CLIENT_ID, "display_name": "Avery Client"},
        "agency": {"id": AGENCY_ID, "name": "Collaboration Smoke Agency"},
    }
    passenger_ctx = {
        "account": {
            "id": "collaboration-smoke-passenger-account",
            "agency_id": AGENCY_ID,
            "passenger_profile_id": PASSENGER_ID,
        },
        "identity": {"id": PASSENGER_IDENTITY_ID},
        "subject_type": "passenger",
        "passenger": {
            "id": PASSENGER_ID,
            "display_name": "Parker Passenger",
        },
        "agency": {"id": AGENCY_ID, "name": "Collaboration Smoke Agency"},
    }
    return SmokeContext(
        db=db,
        service=OperationalCollaborationService(db),
        actor=actor,
        client_ctx=client_ctx,
        passenger_ctx=passenger_ctx,
        checks=[],
    )


async def canonical_thread(ctx: SmokeContext) -> dict[str, Any]:
    return await ctx.service.create_thread(
        AGENCY_ID,
        {
            "idempotency_key": "canonical-multi-entity-thread",
            "subject": "Request to booking operations",
            "entity_references": [
                {
                    "entity_type": "request",
                    "entity_id": REQUEST_ID,
                    "label": "Request REQ-COLLAB-001",
                },
                {
                    "entity_type": "trip",
                    "entity_id": TRIP_ID,
                    "label": "Trip TRP-COLLAB-001",
                },
                {
                    "entity_type": "booking",
                    "entity_id": BOOKING_ID,
                    "label": "Booking BKG-COLLAB-001",
                },
            ],
            "participants": [
                {
                    "participant_type": "supplier",
                    "supplier_reference": "SUPPLIER-COLLAB-001",
                    "display_name": "Manual Supplier Desk",
                    "participant_role": "supplier_support",
                    "visibility": ["supplier"],
                }
            ],
            "visibility": [
                "internal",
                "agency",
                "client",
                "passenger",
                "supplier",
            ],
        },
        ctx.actor,
    )


async def run_timeline_case() -> list[str]:
    ctx = await seed()
    before = datetime.now(timezone.utc)
    first = await ctx.service.record_business_event(
        agency_id=AGENCY_ID,
        entity_type="request",
        entity_id=REQUEST_ID,
        event_type="request_created",
        summary="Request created.",
        actor=ctx.actor,
        visibility="internal",
        idempotency_key="timeline-request-created",
        details={"submitted_event_time": "1900-01-01T00:00:00Z"},
    )
    after = datetime.now(timezone.utc)
    duplicate = await ctx.service.record_business_event(
        agency_id=AGENCY_ID,
        entity_type="request",
        entity_id=REQUEST_ID,
        event_type="request_created",
        summary="Request created.",
        actor=ctx.actor,
        visibility="internal",
        idempotency_key="timeline-request-created",
    )
    ctx.check(
        "timeline_server_timestamp",
        before <= parsed_datetime(first["event_time"]) <= after,
        "Timeline time was not assigned by the server.",
    )
    ctx.check(
        "timeline_deterministic_idempotency",
        first["id"] == duplicate["id"]
        and await ctx.db.collection(TIMELINE_COLLECTION).count(
            {"agency_id": AGENCY_ID, "idempotency_key": "timeline-request-created"}
        )
        == 1,
        "An idempotent business event created duplicate history.",
    )
    original_snapshot = dict(
        await ctx.service.require_timeline_entry(first["id"], AGENCY_ID)
    )
    correction = await ctx.service.append_correction(
        first["id"],
        {"operational_notes": "Corrected by append-only evidence."},
        ctx.actor,
    )
    original_after = await ctx.service.require_timeline_entry(first["id"], AGENCY_ID)
    ctx.check(
        "timeline_original_immutable",
        original_snapshot == original_after
        and correction.get("supersedes_entry_id") == first["id"]
        and correction.get("event_type") == "timeline_correction",
        "Correction rewrote or failed to link the original timeline entry.",
    )
    source = inspect.getsource(OperationalCollaborationService)
    ctx.check(
        "timeline_deletion_absent",
        "delete_one(" not in source and "delete_many(" not in source,
        "The canonical collaboration service exposes destructive deletion.",
    )
    ctx.check(
        "timeline_safety_flags",
        ctx.service.safety_flags()["timeline_append_only"]
        and ctx.service.safety_flags()["timeline_immutable_business_history"],
        "Append-only safety flags are incomplete.",
    )
    return ctx.checks


async def run_communication_case() -> list[str]:
    ctx = await seed()
    detail = await canonical_thread(ctx)
    thread = detail["thread"]
    participant_types = {
        item["participant_type"] for item in detail["participants"]
    }
    ctx.check(
        "thread_multi_entity_lineage",
        len(thread["entity_references"]) == 3
        and {item["entity_type"] for item in thread["entity_references"]}
        == {"request", "trip", "booking"},
        "The canonical thread did not preserve all business references.",
    )
    ctx.check(
        "thread_participants",
        {"agency", "client_portal", "passenger_portal", "supplier"}.issubset(
            participant_types
        ),
        "Expected governed participants were not linked to the thread.",
    )
    internal = await ctx.service.post_message(
        AGENCY_ID,
        thread["id"],
        {
            "idempotency_key": "internal-note-001",
            "message_type": "internal_note",
            "plain_text": "Margin review remains internal.",
            "visibility": "internal",
        },
        ctx.actor,
    )
    client_message = await ctx.service.post_message(
        AGENCY_ID,
        thread["id"],
        {
            "idempotency_key": "client-message-001",
            "plain_text": "Your booking is ready for review.",
            "visibility": "client",
            "delivery_status": "not_sent",
        },
        ctx.actor,
    )
    repeated = await ctx.service.post_message(
        AGENCY_ID,
        thread["id"],
        {
            "idempotency_key": "client-message-001",
            "plain_text": "Your booking is ready for review.",
            "visibility": "client",
            "delivery_status": "not_sent",
        },
        ctx.actor,
    )
    await expect_error(
        lambda: ctx.service.post_message(
            AGENCY_ID,
            thread["id"],
            {
                "idempotency_key": "client-message-001",
                "plain_text": "Different content.",
                "visibility": "client",
            },
            ctx.actor,
        ),
        "IDEMPOTENCY_CONFLICT",
    )
    edited = await ctx.service.edit_message(
        AGENCY_ID,
        client_message["id"],
        {
            "plain_text": "Your booking is ready for your review.",
            "reason": "Clarified wording.",
        },
        ctx.actor,
    )
    ctx.check(
        "message_edit_history",
        len(edited["edit_history"]) == 1
        and edited["edit_history"][0]["plain_text"]
        == "Your booking is ready for review."
        and edited["deletion_prohibited"],
        "Message edit history did not preserve the prior content.",
    )
    ctx.check(
        "message_idempotency",
        repeated["id"] == client_message["id"]
        and await ctx.db.collection(MESSAGE_COLLECTION).count(
            {"agency_id": AGENCY_ID}
        )
        == 2,
        "Message idempotency did not preserve a single posted message.",
    )
    timeline = await ctx.db.collection(TIMELINE_COLLECTION).find_one(
        {"agency_id": AGENCY_ID, "id": internal["linked_timeline_entry_id"]}
    )
    audit = await ctx.db.collection("audit_events").find_one(
        {"agency_id": AGENCY_ID, "id": internal["linked_audit_event_id"]}
    )
    ctx.check(
        "message_timeline_audit_linkage",
        bool(timeline)
        and bool(audit)
        and timeline.get("linked_communication_thread_id") == thread["id"]
        and timeline.get("linked_communication_message_id") == internal["id"],
        "Message, timeline, and audit evidence were not linked.",
    )
    ctx.check(
        "canonical_collection_ownership",
        all(
            [
            await ctx.db.collection(name).count({"agency_id": AGENCY_ID}) > 0
            for name in (
                THREAD_COLLECTION,
                MESSAGE_COLLECTION,
                PARTICIPANT_COLLECTION,
                TIMELINE_COLLECTION,
            )
            ]
        ),
        "A canonical collaboration collection was not populated.",
    )
    return ctx.checks


async def run_portal_case() -> list[str]:
    ctx = await seed()
    detail = await canonical_thread(ctx)
    thread_id = detail["thread"]["id"]
    await ctx.service.post_message(
        AGENCY_ID,
        thread_id,
        {
            "message_type": "internal_note",
            "plain_text": "Supplier cost: EUR 220.",
            "visibility": "internal",
        },
        ctx.actor,
    )
    await ctx.service.post_message(
        AGENCY_ID,
        thread_id,
        {
            "plain_text": "Client-visible operational update.",
            "visibility": "client",
            "delivery_status": "not_sent",
        },
        ctx.actor,
    )
    await ctx.service.post_message(
        AGENCY_ID,
        thread_id,
        {
            "plain_text": "Passenger-visible operational update.",
            "visibility": "passenger",
            "delivery_status": "not_sent",
        },
        ctx.actor,
    )
    client_detail = await ctx.service.portal_thread_detail(
        ctx.client_ctx, thread_id
    )
    passenger_detail = await ctx.service.portal_thread_detail(
        ctx.passenger_ctx, thread_id
    )
    ctx.check(
        "portal_internal_note_isolation",
        {item["plain_text"] for item in client_detail["messages"]}
        == {"Client-visible operational update."}
        and {item["plain_text"] for item in passenger_detail["messages"]}
        == {"Passenger-visible operational update."},
        "Portal projections crossed client/passenger visibility or leaked an internal note.",
    )
    reply = await ctx.service.portal_post_message(
        ctx.client_ctx,
        thread_id,
        {
            "idempotency_key": "portal-client-reply",
            "plain_text": "Please proceed.",
        },
    )
    ctx.check(
        "portal_reply_lineage",
        reply["sender_type"] == "client_portal"
        and reply["visibility"] == "client"
        and reply["delivery_status"] == "received"
        and bool(reply["linked_timeline_entry_id"])
        and bool(reply["linked_audit_event_id"]),
        "Portal reply did not produce governed communication evidence.",
    )
    wrong_ctx = {
        **ctx.client_ctx,
        "account": {
            **ctx.client_ctx["account"],
            "agency_id": OTHER_AGENCY_ID,
        },
    }
    ctx.check(
        "portal_cross_tenant_isolation",
        await ctx.service.portal_threads(wrong_ctx) == [],
        "A Portal context could discover another Agency's threads.",
    )
    await expect_error(
        lambda: ctx.service.portal_post_message(
            ctx.passenger_ctx,
            thread_id,
            {
                "plain_text": "Invalid client visibility.",
                "visibility": "client",
            },
        ),
        "PORTAL_VISIBILITY_MISMATCH",
    )
    return ctx.checks


async def run_supplier_case() -> list[str]:
    ctx = await seed()
    detail = await canonical_thread(ctx)
    thread = detail["thread"]
    supplier = next(
        item
        for item in detail["participants"]
        if item["participant_type"] == "supplier"
    )
    supplier_actor = {
        "id": "manual-supplier-evidence",
        "actor_type": "supplier",
        "display_name": "Manual Supplier Desk",
    }
    recorded = await ctx.service.post_message(
        AGENCY_ID,
        thread["id"],
        {
            "sender_participant_id": supplier["id"],
            "plain_text": "Seat request noted for manual follow-up.",
            "visibility": "supplier",
            "delivery_status": "recorded",
        },
        supplier_actor,
    )
    await expect_error(
        lambda: ctx.service.post_message(
            AGENCY_ID,
            thread["id"],
            {
                "sender_participant_id": supplier["id"],
                "plain_text": "Attempted internal message.",
                "visibility": "internal",
            },
            supplier_actor,
        ),
        "MESSAGE_VISIBILITY_FORBIDDEN",
    )
    ctx.check(
        "supplier_manual_only",
        recorded["visibility"] == "supplier"
        and recorded["delivery_status"] == "recorded"
        and recorded["metadata"].get("provider_execution") is False
        and ctx.service.safety_flags()["provider_integrations_disabled"],
        "Supplier communication implied provider execution.",
    )
    search = await ctx.service.search(
        AGENCY_ID,
        "seat request",
        visibility={"supplier"},
        limit=10,
    )
    internal_search = await ctx.service.search(
        AGENCY_ID,
        "seat request",
        visibility={"internal"},
        limit=10,
    )
    ctx.check(
        "supplier_search_isolation",
        search["count"] == 1
        and search["items"][0]["result_type"] == "message"
        and internal_search["count"] == 0
        and search["bounded"]
        and search["permission_filtered"],
        "Search did not enforce supplier visibility.",
    )
    return ctx.checks


async def run_ordering_case() -> list[str]:
    ctx = await seed()
    fixed = datetime(2026, 7, 24, 12, 0, tzinfo=timezone.utc)
    ctx.service._now = lambda: fixed  # type: ignore[method-assign]
    created = []
    for key in ("ordering-c", "ordering-a", "ordering-b"):
        created.append(
            await ctx.service.record_business_event(
                agency_id=AGENCY_ID,
                entity_type="request",
                entity_id=REQUEST_ID,
                event_type="status_transition",
                summary=key,
                actor=ctx.actor,
                visibility="internal",
                idempotency_key=key,
            )
        )
    ordered = await ctx.service.list_timeline(
        agency_id=AGENCY_ID,
        entity_type="request",
        entity_id=REQUEST_ID,
        visibility={"internal"},
        limit=20,
    )
    expected_ids = sorted(item["id"] for item in created)
    ctx.check(
        "timeline_total_order",
        [item["id"] for item in ordered] == expected_ids
        and all(parsed_datetime(item["event_time"]) == fixed for item in ordered),
        "Equal-time timeline entries did not use deterministic ID ordering.",
    )
    warning = await ctx.service.record_business_event(
        agency_id=AGENCY_ID,
        entity_type="request",
        entity_id=REQUEST_ID,
        event_type="communication_received",
        summary="Client response requires action.",
        actor=ctx.actor,
        visibility="internal",
        idempotency_key="notification-source",
    )
    before_timeline = await ctx.db.collection(TIMELINE_COLLECTION).count(
        {"agency_id": AGENCY_ID}
    )
    first_rebuild = await ctx.service.rebuild_notification_projections(AGENCY_ID)
    second_rebuild = await ctx.service.rebuild_notification_projections(AGENCY_ID)
    after_timeline = await ctx.db.collection(TIMELINE_COLLECTION).count(
        {"agency_id": AGENCY_ID}
    )
    projection = await ctx.db.collection(NOTIFICATION_COLLECTION).find_one(
        {"agency_id": AGENCY_ID, "timeline_entry_id": warning["id"]}
    )
    ctx.check(
        "notification_projection_regeneration",
        bool(projection)
        and projection["business_truth"] is False
        and first_rebuild["business_truth_mutated"] is False
        and second_rebuild["projections_created"] == 0
        and before_timeline == after_timeline,
        "Notification regeneration mutated timeline truth or duplicated projections.",
    )
    thread = await canonical_thread(ctx)
    attachment = await ctx.service.register_attachment(
        AGENCY_ID,
        thread["thread"]["id"],
        {
            "document_id": DOCUMENT_ID,
            "reference_type": "document",
            "reference_id": DOCUMENT_ID,
            "title": "Travel approval",
            "media_type": "application/pdf",
            "checksum": "sha256:collaboration-smoke",
            "visibility": "client",
        },
        ctx.actor,
    )
    repeated = await ctx.service.register_attachment(
        AGENCY_ID,
        thread["thread"]["id"],
        {
            "document_id": DOCUMENT_ID,
            "reference_type": "document",
            "reference_id": DOCUMENT_ID,
            "title": "Travel approval",
            "media_type": "application/pdf",
            "checksum": "sha256:collaboration-smoke",
            "visibility": "client",
        },
        ctx.actor,
    )
    ctx.check(
        "attachment_immutable_reference",
        attachment["id"] == repeated["id"]
        and attachment["immutable"] is True
        and attachment["binary_duplicated"] is False
        and await ctx.db.collection(ATTACHMENT_COLLECTION).count(
            {"agency_id": AGENCY_ID}
        )
        == 1,
        "Attachment registration duplicated binary or reference evidence.",
    )
    before_counts = {
        name: await ctx.db.collection(name).count()
        for name in (
            "request_messages",
            "after_sales_communication_records",
            THREAD_COLLECTION,
            MESSAGE_COLLECTION,
            TIMELINE_COLLECTION,
        )
    }
    analysis = await ctx.service.migration_analysis(100)
    after_counts = {
        name: await ctx.db.collection(name).count()
        for name in before_counts
    }
    ctx.check(
        "migration_analysis_read_only",
        analysis["mode"] == "dry_run"
        and analysis["write_mode_available"] is False
        and analysis["writes_performed"] == 0
        and before_counts == after_counts,
        "Migration analysis changed persistence or exposed write mode.",
    )
    return ctx.checks


CASES: dict[str, Callable[[], Awaitable[list[str]]]] = {
    "timeline": run_timeline_case,
    "communication": run_communication_case,
    "portal": run_portal_case,
    "supplier": run_supplier_case,
    "ordering": run_ordering_case,
}


async def run_case(name: str) -> list[str]:
    return await CASES[name]()
