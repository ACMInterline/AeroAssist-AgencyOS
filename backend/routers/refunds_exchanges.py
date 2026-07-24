from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    AuditEvent,
    BookingTimelineEvent,
    PaymentRecord,
    RefundExchangeCase,
    RefundExchangeCaseCreate,
    RefundExchangeCaseStatus,
    RefundExchangeCaseStatusUpdate,
    RefundExchangeCaseUpdate,
    RefundExchangeFromBookingCreate,
    RefundExchangeFinancialLine,
    RefundExchangeFinancialLineCreate,
    RefundExchangeFinancialLineUpdate,
    RefundExchangeItem,
    RefundExchangeItemCreate,
    RefundExchangeItemType,
    RefundExchangeItemUpdate,
    RefundExchangeMessage,
    RefundExchangeMessageCreate,
    RefundExchangeMessageSenderType,
    RefundExchangeMessageVisibility,
    RefundExchangeTimelineEvent,
    RefundExchangeTimelineVisibility,
    RequestTask,
)
from routers.portal import portal_context
from services.operational_collaboration_service import (
    OperationalCollaborationError,
    OperationalCollaborationService,
)
from services.tenant_service import (
    assert_agency_access,
    assert_portal_projection_safe,
    assert_portal_owns_client_record,
    require_any_agency_role,
)

router = APIRouter(prefix="/api/agencies/{agency_id}", tags=["refund_exchanges"])
portal_router = APIRouter(prefix="/api/portal", tags=["portal_refund_exchanges"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant"]
CLIENT_VISIBLE_STATUS_CHANGES = {
    RefundExchangeCaseStatus.CLIENT_REQUESTED,
    RefundExchangeCaseStatus.WAITING_FOR_CLIENT,
    RefundExchangeCaseStatus.PROCESSING_EXTERNALLY,
    RefundExchangeCaseStatus.APPROVED,
    RefundExchangeCaseStatus.COMPLETED,
    RefundExchangeCaseStatus.REJECTED,
    RefundExchangeCaseStatus.CANCELLED,
}


def clean_updates(payload: Any) -> dict:
    return payload.model_dump(exclude_unset=True, mode="json")


def matches_search(record: dict, search: Optional[str]) -> bool:
    if not search:
        return True
    needle = search.lower()
    fields = [
        "case_reference",
        "client_reason_text",
        "internal_summary",
        "client_visible_summary",
        "supplier_reference",
    ]
    return any(needle in str(record.get(field, "")).lower() for field in fields)


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


async def require_write(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin"}:
        await require_any_agency_role(db, agency_id, user, WRITE_ROLES)


async def write_audit(
    db: Database,
    agency_id: str,
    actor_user_id: str,
    event_type: str,
    entity_type: str,
    entity_id: str,
    summary: str,
    metadata: dict | None = None,
) -> None:
    event = AuditEvent(
        agency_id=agency_id,
        actor_user_id=actor_user_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        summary=summary,
        metadata=metadata or {},
    )
    await db.collection("audit_events").insert_one(event.model_dump(mode="json"))


async def write_booking_timeline(
    db: Database,
    agency_id: str,
    booking_id: str | None,
    actor_user_id: str | None,
    event_type: str,
    title: str,
    summary: str | None = None,
    metadata: dict | None = None,
) -> None:
    if not booking_id:
        return
    await OperationalCollaborationService(db).record_compatibility_event(
        agency_id=agency_id,
        entity_type="booking",
        entity_id=booking_id,
        source_event_type=event_type,
        summary=summary or title,
        actor_user_id=actor_user_id,
        visibility="internal",
        details={"title": title, **(metadata or {})},
        source_collection="booking_timeline_events",
    )


async def write_case_timeline(
    db: Database,
    agency_id: str,
    case_id: str,
    actor_user_id: str | None,
    event_type: str,
    title: str,
    summary: str | None = None,
    visibility: RefundExchangeTimelineVisibility | str = RefundExchangeTimelineVisibility.INTERNAL,
    metadata: dict | None = None,
) -> None:
    collaboration = OperationalCollaborationService(db)
    visibility_value = (
        visibility.value if isinstance(visibility, RefundExchangeTimelineVisibility) else visibility
    )
    await collaboration.record_business_event(
        agency_id=agency_id,
        entity_type="after_sales_case",
        entity_id=case_id,
        event_type=event_type,
        event_subtype="refund_exchange_case_event",
        summary=summary or title,
        actor={
            "id": actor_user_id,
            "identity_id": actor_user_id,
            "actor_type": "agency" if actor_user_id else "system",
        },
        visibility="client" if visibility_value == "client_visible" else "internal",
        details={"title": title, **(metadata or {})},
        source_collection="refund_exchange_cases",
        source_record_id=case_id,
    )


async def next_reference(db: Database, agency_id: str) -> str:
    count = await db.collection("refund_exchange_cases").count({"agency_id": agency_id})
    return f"REC-{count + 1:05d}"


async def get_case_or_404(db: Database, agency_id: str, case_id: str) -> dict:
    case = await db.collection("refund_exchange_cases").find_one({"agency_id": agency_id, "id": case_id})
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Refund/exchange case not found.")
    return case


async def get_client_or_404(db: Database, agency_id: str, client_id: str) -> dict:
    client = await db.collection("client_profiles").find_one({"agency_id": agency_id, "id": client_id})
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")
    return client


async def get_booking_or_404(db: Database, agency_id: str, booking_id: str) -> dict:
    booking = await db.collection("bookings").find_one({"agency_id": agency_id, "id": booking_id})
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found.")
    return booking


async def get_request_or_404(db: Database, agency_id: str, request_id: str) -> dict:
    request = await db.collection("travel_requests").find_one({"agency_id": agency_id, "id": request_id})
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.")
    return request


async def get_offer_or_404(db: Database, agency_id: str, offer_id: str) -> dict:
    offer = await db.collection("offers").find_one({"agency_id": agency_id, "id": offer_id})
    if offer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found.")
    return offer


async def get_case_item_or_404(db: Database, agency_id: str, case_id: str, item_id: str) -> dict:
    item = await db.collection("refund_exchange_items").find_one({"agency_id": agency_id, "case_id": case_id, "id": item_id})
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case item not found.")
    return item


async def get_case_line_or_404(db: Database, agency_id: str, case_id: str, line_id: str) -> dict:
    line = await db.collection("refund_exchange_financial_lines").find_one({"agency_id": agency_id, "case_id": case_id, "id": line_id})
    if line is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Financial line not found.")
    return line


async def validate_case_links(db: Database, agency_id: str, case: dict) -> None:
    await get_client_or_404(db, agency_id, case["client_id"])
    if case.get("booking_id"):
        booking = await get_booking_or_404(db, agency_id, case["booking_id"])
        if booking["client_id"] != case["client_id"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Booking must belong to the selected client.")
    if case.get("request_id"):
        request = await get_request_or_404(db, agency_id, case["request_id"])
        if request["client_id"] != case["client_id"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request must belong to the selected client.")
    if case.get("offer_id"):
        offer = await get_offer_or_404(db, agency_id, case["offer_id"])
        if offer["client_id"] != case["client_id"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Offer must belong to the selected client.")


async def validate_item_link(db: Database, agency_id: str, case: dict, item_payload: dict) -> None:
    item_type = RefundExchangeItemType(item_payload["item_type"])
    case_booking_id = case.get("booking_id")
    case_client_id = case.get("client_id")

    if item_type == RefundExchangeItemType.TICKET:
        ticket_id = item_payload.get("ticket_id")
        if not ticket_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ticket_id is required for ticket items.")
        ticket = await db.collection("ticket_records").find_one({"agency_id": agency_id, "id": ticket_id})
        if not ticket:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticket not found.")
        if case_booking_id and ticket.get("booking_id") != case_booking_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticket must belong to the same booking as the case.")
        if not case_booking_id and case_client_id:
            ticket_booking = await db.collection("bookings").find_one({"agency_id": agency_id, "id": ticket["booking_id"]})
            if ticket_booking and ticket_booking.get("client_id") != case_client_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticket must belong to the selected client.")
        if case_client_id and ticket.get("passenger_id"):
            passenger = await db.collection("passenger_profiles").find_one({"agency_id": agency_id, "id": ticket["passenger_id"]})
            if passenger is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ticket passenger reference.")

    elif item_type == RefundExchangeItemType.EMD:
        emd_id = item_payload.get("emd_id")
        if not emd_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="emd_id is required for EMD items.")
        emd = await db.collection("emd_records").find_one({"agency_id": agency_id, "id": emd_id})
        if not emd:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="EMD not found.")
        if case_booking_id and emd.get("booking_id") != case_booking_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="EMD must belong to the same booking as the case.")
        if not case_booking_id and case_client_id:
            emd_booking = await db.collection("bookings").find_one({"agency_id": agency_id, "id": emd["booking_id"]})
            if emd_booking and emd_booking.get("client_id") != case_client_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="EMD must belong to the selected client.")

    elif item_type == RefundExchangeItemType.INVOICE:
        invoice_id = item_payload.get("invoice_id")
        if not invoice_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invoice_id is required for invoice items.")
        invoice = await db.collection("invoices").find_one({"agency_id": agency_id, "id": invoice_id})
        if not invoice:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invoice not found.")
        if invoice["client_id"] != case_client_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invoice must belong to the selected client.")
        if case_booking_id and invoice.get("booking_id") and invoice["booking_id"] != case_booking_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invoice must belong to the same booking as the case.")

    elif item_type == RefundExchangeItemType.PAYMENT:
        payment_id = item_payload.get("payment_id")
        if not payment_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="payment_id is required for payment items.")
        payment = await db.collection("payment_records").find_one({"agency_id": agency_id, "id": payment_id})
        if not payment:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment not found.")
        payment_record = PaymentRecord.model_validate(payment)
        if payment_record.client_id != case_client_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment must belong to the selected client.")
        if case_booking_id and payment_record.booking_id and payment_record.booking_id != case_booking_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment must belong to the same booking as the case.")

    elif item_type == RefundExchangeItemType.BOOKING_SEGMENT:
        segment_id = item_payload.get("booking_segment_id") or item_payload.get("item_id")
        if not segment_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="booking_segment_id is required for segment items.")
        segment = await db.collection("booking_segments").find_one({"agency_id": agency_id, "id": segment_id})
        if not segment:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Booking segment not found.")
        if not case_booking_id or segment.get("booking_id") != case_booking_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Booking segment must belong to the same booking as the case.")

    elif item_type == RefundExchangeItemType.PASSENGER:
        passenger_id = item_payload.get("passenger_id")
        if not passenger_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="passenger_id is required for passenger items.")
        passenger = await db.collection("passenger_profiles").find_one({"agency_id": agency_id, "id": passenger_id})
        if not passenger:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passenger not found.")
        if case_booking_id:
            booking_passenger = await db.collection("booking_passengers").find_one(
                {"agency_id": agency_id, "booking_id": case_booking_id, "passenger_id": passenger_id}
            )
            if not booking_passenger:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passenger must belong to the same booking as the case.")
        elif case_client_id:
            relationship = await db.collection("client_passenger_relationships").find_one(
                {"agency_id": agency_id, "client_id": case_client_id, "passenger_id": passenger_id, "status": "active"}
            )
            if not relationship:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passenger must belong to the selected client.")


def safe_client_case_item(item: dict) -> dict:
    return {
        "id": item["id"],
        "item_type": item.get("item_type"),
        "description": item.get("description"),
        "status": item.get("status"),
        "estimated_amount": item.get("estimated_amount"),
        "final_amount": item.get("final_amount"),
        "currency": item.get("currency"),
        "client_visible_notes": item.get("client_visible_notes"),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
    }


def safe_client_case_line(line: dict) -> dict:
    return {
        "id": line["id"],
        "line_type": line.get("line_type"),
        "description": line.get("description"),
        "amount": line.get("amount"),
        "currency": line.get("currency"),
        "direction": line.get("direction"),
        "supplier_pass_through": line.get("supplier_pass_through"),
        "created_at": line.get("created_at"),
    }


def safe_client_case_timeline(event: dict) -> dict:
    return {
        "id": event["id"],
        "event_type": event.get("event_type"),
        "title": event.get("title"),
        "summary": event.get("summary"),
        "created_at": event.get("created_at"),
    }


def safe_client_case_message(message: dict) -> dict:
    return {
        "id": message["id"],
        "sender_type": message.get("sender_type"),
        "message_text": message.get("message_text"),
        "created_at": message.get("created_at"),
    }


def safe_client_case(case: dict) -> dict:
    return {
        "id": case["id"],
        "case_reference": case.get("case_reference"),
        "case_type": case.get("case_type"),
        "status": case.get("status"),
        "priority": case.get("priority"),
        "reason_category": case.get("reason_category"),
        "client_reason_text": case.get("client_reason_text"),
        "client_visible_summary": case.get("client_visible_summary"),
        "supplier_reference": case.get("supplier_reference"),
        "estimated_refund_amount": case.get("estimated_refund_amount"),
        "estimated_penalty_amount": case.get("estimated_penalty_amount"),
        "estimated_exchange_difference_amount": case.get("estimated_exchange_difference_amount"),
        "estimated_agency_fee_amount": case.get("estimated_agency_fee_amount"),
        "estimated_total_due_from_client": case.get("estimated_total_due_from_client"),
        "estimated_total_due_to_client": case.get("estimated_total_due_to_client"),
        "final_refund_amount": case.get("final_refund_amount"),
        "final_penalty_amount": case.get("final_penalty_amount"),
        "final_exchange_difference_amount": case.get("final_exchange_difference_amount"),
        "final_agency_fee_amount": case.get("final_agency_fee_amount"),
        "final_total_due_from_client": case.get("final_total_due_from_client"),
        "final_total_due_to_client": case.get("final_total_due_to_client"),
        "currency": case.get("currency"),
        "expected_supplier_response_at": case.get("expected_supplier_response_at"),
        "deadline_at": case.get("deadline_at"),
        "booking_id": case.get("booking_id"),
        "created_at": case.get("created_at"),
        "updated_at": case.get("updated_at"),
    }


def _as_sort_value(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value) if value is not None else ""


async def canonical_case_messages(
    db: Database, agency_id: str, case_id: str
) -> list[dict[str, Any]]:
    collaboration = OperationalCollaborationService(db)
    threads = await collaboration.list_threads(
        agency_id,
        entity_type="after_sales_case",
        entity_id=case_id,
        visibility={"internal", "agency", "client"},
        limit=200,
    )
    canonical: list[dict[str, Any]] = []
    for thread in threads:
        detail = await collaboration.thread_detail(
            agency_id,
            thread["id"],
            visibility={"internal", "agency", "client"},
        )
        canonical.extend(
            {
                **message,
                "case_id": case_id,
                "sender_user_id": message.get("sender_identity_id"),
                "sender_type": "client"
                if message.get("sender_type") == "client_portal"
                else "staff"
                if message.get("sender_type") == "agency"
                else "system",
                "visibility": "client_visible"
                if message.get("visibility") == "client"
                else "internal",
                "message_text": message.get("plain_text"),
                "canonical_thread_id": thread["id"],
                "canonical_message_id": message["id"],
            }
            for message in detail.get("messages") or []
            if message.get("message_type") == "refund_exchange_message"
        )
    legacy = await db.collection("refund_exchange_messages").find_many(
        {"agency_id": agency_id, "case_id": case_id},
        sort=[("created_at", -1), ("id", -1)],
        limit=200,
    )
    items = legacy + canonical
    items.sort(key=lambda item: _as_sort_value(item.get("created_at")), reverse=True)
    return items


async def canonical_case_timeline(
    db: Database, agency_id: str, case_id: str
) -> list[dict[str, Any]]:
    collaboration = OperationalCollaborationService(db)
    canonical = [
        {
            **event,
            "case_id": case_id,
            "actor_user_id": event.get("actor_id"),
            "title": (event.get("details") or {}).get("title")
            or event.get("summary"),
            "visibility": "client_visible"
            if event.get("visibility") == "client"
            else "internal",
            "canonical_timeline_entry_id": event["id"],
        }
        for event in await collaboration.list_timeline(
            agency_id=agency_id,
            entity_type="after_sales_case",
            entity_id=case_id,
            visibility={"internal", "agency", "client"},
            limit=200,
        )
    ]
    legacy = await db.collection("refund_exchange_timeline_events").find_many(
        {"agency_id": agency_id, "case_id": case_id},
        sort=[("created_at", -1), ("id", -1)],
        limit=200,
    )
    items = legacy + canonical
    items.sort(key=lambda item: _as_sort_value(item.get("created_at")), reverse=True)
    return items


@router.get("/refund-exchange-cases")
async def list_cases(
    agency_id: str,
    search: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    case_type: Optional[str] = None,
    priority: Optional[str] = None,
    client_id: Optional[str] = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    filters = {"agency_id": agency_id}
    if status_filter:
        filters["status"] = status_filter
    if case_type:
        filters["case_type"] = case_type
    if priority:
        filters["priority"] = priority
    if client_id:
        filters["client_id"] = client_id
    cases = [item for item in await db.collection("refund_exchange_cases").find_many(filters) if matches_search(item, search)]

    clients = {item["id"]: item for item in await db.collection("client_profiles").find_many({"agency_id": agency_id})}
    bookings = {item["id"]: item for item in await db.collection("bookings").find_many({"agency_id": agency_id})}
    cases.sort(key=lambda item: _as_sort_value(item.get("updated_at")), reverse=True)
    return {
        "items": [
            {**case, "client": clients.get(case["client_id"]), "booking": bookings.get(case.get("booking_id"))}
            for case in cases
        ]
    }


@router.post("/refund-exchange-cases", status_code=status.HTTP_201_CREATED)
async def create_case(
    agency_id: str,
    payload: RefundExchangeCaseCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    case_payload = payload.model_dump(mode="json")
    await validate_case_links(db, agency_id, case_payload)

    case = RefundExchangeCase(
        agency_id=agency_id,
        case_reference=await next_reference(db, agency_id),
        created_by_user_id=user["id"],
        **case_payload,
    )
    created = await db.collection("refund_exchange_cases").insert_one(case.model_dump(mode="json"))
    await write_case_timeline(
        db=db,
        agency_id=agency_id,
        case_id=created["id"],
        actor_user_id=user["id"],
        event_type="case.created",
        title="Case created",
        summary=f"Created refund/exchange case {created['case_reference']}.",
        visibility=RefundExchangeTimelineVisibility.INTERNAL,
        metadata={"case_reference": created.get("case_reference"), "case_type": created.get("case_type")},
    )
    await write_booking_timeline(
        db,
        agency_id,
        created.get("booking_id"),
        user["id"],
        "refund_exchange.case_created",
        "Refund/exchange case created",
        created["case_reference"],
    )
    await write_audit(
        db=db,
        agency_id=agency_id,
        actor_user_id=user["id"],
        event_type="refund_exchange_case.created",
        entity_type="refund_exchange_case",
        entity_id=created["id"],
        summary=f"Created refund/exchange case {created['case_reference']}.",
        metadata={"case_type": created.get("case_type"), "client_id": created["client_id"]},
    )
    return {"case": created}


@router.get("/refund-exchange-cases/{case_id}")
async def get_case(
    agency_id: str,
    case_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    case = await get_case_or_404(db, agency_id, case_id)
    return {
        "case": case,
        "client": await get_client_or_404(db, agency_id, case["client_id"]),
        "booking": await db.collection("bookings").find_one({"agency_id": agency_id, "id": case.get("booking_id")}),
        "items": await db.collection("refund_exchange_items").find_many({"agency_id": agency_id, "case_id": case_id}),
        "financial_lines": await db.collection("refund_exchange_financial_lines").find_many({"agency_id": agency_id, "case_id": case_id}),
        "messages": await canonical_case_messages(db, agency_id, case_id),
        "timeline": await canonical_case_timeline(db, agency_id, case_id),
    }


@router.put("/refund-exchange-cases/{case_id}")
async def update_case(
    agency_id: str,
    case_id: str,
    payload: RefundExchangeCaseUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    case = await get_case_or_404(db, agency_id, case_id)
    updates = clean_updates(payload)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided.")
    candidate = {**case, **updates}
    await validate_case_links(db, agency_id, candidate)
    updated = await db.collection("refund_exchange_cases").update_one({"agency_id": agency_id, "id": case_id}, updates)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Refund/exchange case not found.")
    await write_case_timeline(
        db=db,
        agency_id=agency_id,
        case_id=case_id,
        actor_user_id=user["id"],
        event_type="case.updated",
        title="Case updated",
        summary="Case updated",
        visibility=RefundExchangeTimelineVisibility.INTERNAL,
        metadata={"fields": sorted(updates.keys())},
    )
    await write_audit(
        db=db,
        agency_id=agency_id,
        actor_user_id=user["id"],
        event_type="refund_exchange_case.updated",
        entity_type="refund_exchange_case",
        entity_id=case_id,
        summary="Refund/exchange case updated.",
        metadata={"fields": sorted(updates.keys())},
    )
    return {"case": updated}


@router.post("/refund-exchange-cases/{case_id}/status")
async def update_case_status(
    agency_id: str,
    case_id: str,
    payload: RefundExchangeCaseStatusUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    case = await get_case_or_404(db, agency_id, case_id)
    updates: dict[str, Any] = {"status": payload.status}
    now = datetime.now(timezone.utc)
    if payload.status == RefundExchangeCaseStatus.COMPLETED:
        updates["completed_at"] = now
        updates["cancelled_at"] = None
    elif payload.status == RefundExchangeCaseStatus.CANCELLED:
        updates["cancelled_at"] = now
        updates["completed_at"] = None
    else:
        updates["completed_at"] = None
        updates["cancelled_at"] = None

    updated = await db.collection("refund_exchange_cases").update_one({"agency_id": agency_id, "id": case_id}, updates)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Refund/exchange case not found.")
    await write_case_timeline(
        db=db,
        agency_id=agency_id,
        case_id=case_id,
        actor_user_id=user["id"],
        event_type="case.status_changed",
        title=f"Status changed to {payload.status}",
        summary=f"Case status changed from {case.get('status')} to {payload.status}.",
        visibility=RefundExchangeTimelineVisibility.INTERNAL,
        metadata={"from": case.get("status"), "to": payload.status},
    )
    await write_audit(
        db=db,
        agency_id=agency_id,
        actor_user_id=user["id"],
        event_type="refund_exchange_case.status_changed",
        entity_type="refund_exchange_case",
        entity_id=case_id,
        summary=f"Changed case status from {case.get('status')} to {payload.status}.",
        metadata={"from": case.get("status"), "to": payload.status},
    )
    return {"case": updated}


@router.post("/refund-exchange-cases/{case_id}/archive")
async def archive_case(
    agency_id: str,
    case_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    updated = await db.collection("refund_exchange_cases").update_one({"agency_id": agency_id, "id": case_id}, {"status": "archived"})
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Refund/exchange case not found.")
    await write_case_timeline(
        db=db,
        agency_id=agency_id,
        case_id=case_id,
        actor_user_id=user["id"],
        event_type="case.archived",
        title="Case archived",
        summary=f"Case archived: {updated.get('case_reference', case_id)}.",
        visibility=RefundExchangeTimelineVisibility.INTERNAL,
    )
    await write_audit(
        db=db,
        agency_id=agency_id,
        actor_user_id=user["id"],
        event_type="refund_exchange_case.archived",
        entity_type="refund_exchange_case",
        entity_id=case_id,
        summary="Refund/exchange case archived.",
    )
    return {"case": updated}


@router.post("/bookings/{booking_id}/create-refund-exchange-case", status_code=status.HTTP_201_CREATED)
async def create_case_from_booking(
    agency_id: str,
    booking_id: str,
    payload: RefundExchangeFromBookingCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    booking = await get_booking_or_404(db, agency_id, booking_id)
    payload_data = payload.model_dump(mode="json")

    case_payload = {
        "agency_id": agency_id,
        "case_reference": await next_reference(db, agency_id),
        "client_id": booking["client_id"],
        "booking_id": booking_id,
        "request_id": booking.get("request_id"),
        "offer_id": booking.get("offer_id"),
        "created_by_user_id": user["id"],
        "case_type": payload_data["case_type"],
        "status": payload_data["status"],
        "priority": payload_data["priority"],
        "reason_category": payload_data["reason_category"],
        "client_reason_text": payload_data.get("client_reason_text"),
        "internal_summary": payload_data.get("internal_summary"),
        "client_visible_summary": payload_data.get("client_visible_summary"),
        "supplier_reference": payload_data.get("supplier_reference"),
        "expected_supplier_response_at": payload_data.get("expected_supplier_response_at"),
        "deadline_at": payload_data.get("deadline_at"),
        "estimated_refund_amount": payload_data.get("estimated_refund_amount"),
        "estimated_penalty_amount": payload_data.get("estimated_penalty_amount"),
        "estimated_exchange_difference_amount": payload_data.get("estimated_exchange_difference_amount"),
        "estimated_agency_fee_amount": payload_data.get("estimated_agency_fee_amount"),
        "estimated_total_due_from_client": payload_data.get("estimated_total_due_from_client"),
        "estimated_total_due_to_client": payload_data.get("estimated_total_due_to_client"),
        "currency": payload_data["currency"],
        "client_visible": payload_data.get("client_visible", True),
    }
    await validate_case_links(db, agency_id, case_payload)

    case = RefundExchangeCase(**case_payload)
    created_case = await db.collection("refund_exchange_cases").insert_one(case.model_dump(mode="json"))

    for ticket_id in payload.link_ticket_ids:
        item_payload = {"item_type": RefundExchangeItemType.TICKET.value, "ticket_id": ticket_id}
        await validate_item_link(db, agency_id, created_case, item_payload)
        ticket = await db.collection("ticket_records").find_one({"agency_id": agency_id, "id": ticket_id})
        item = RefundExchangeItem(
            agency_id=agency_id,
            case_id=created_case["id"],
            item_type="ticket",
            ticket_id=ticket_id,
            passenger_id=ticket.get("passenger_id"),
            description=f"Ticket {ticket['ticket_number']}",
            currency=created_case["currency"],
        )
        await db.collection("refund_exchange_items").insert_one(item.model_dump(mode="json"))

    for emd_id in payload.link_emd_ids:
        item_payload = {"item_type": RefundExchangeItemType.EMD.value, "emd_id": emd_id}
        await validate_item_link(db, agency_id, created_case, item_payload)
        emd = await db.collection("emd_records").find_one({"agency_id": agency_id, "id": emd_id})
        await db.collection("refund_exchange_items").insert_one(
            RefundExchangeItem(
                agency_id=agency_id,
                case_id=created_case["id"],
                item_type="emd",
                emd_id=emd_id,
                description=f"EMD {emd.get('emd_number') or emd_id}",
                currency=created_case["currency"],
            ).model_dump(mode="json")
        )

    for invoice_id in payload.link_invoice_ids:
        item_payload = {"item_type": RefundExchangeItemType.INVOICE.value, "invoice_id": invoice_id}
        await validate_item_link(db, agency_id, created_case, item_payload)
        invoice = await db.collection("invoices").find_one({"agency_id": agency_id, "id": invoice_id})
        await db.collection("refund_exchange_items").insert_one(
            RefundExchangeItem(
                agency_id=agency_id,
                case_id=created_case["id"],
                item_type="invoice",
                invoice_id=invoice_id,
                description=f"Invoice {invoice['invoice_number']}",
                currency=created_case["currency"],
            ).model_dump(mode="json")
        )

    for payment_id in payload.link_payment_ids:
        item_payload = {"item_type": RefundExchangeItemType.PAYMENT.value, "payment_id": payment_id}
        await validate_item_link(db, agency_id, created_case, item_payload)
        payment = await db.collection("payment_records").find_one({"agency_id": agency_id, "id": payment_id})
        await db.collection("refund_exchange_items").insert_one(
            RefundExchangeItem(
                agency_id=agency_id,
                case_id=created_case["id"],
                item_type="payment",
                payment_id=payment_id,
                description=f"Payment {payment.get('external_reference') or payment_id}",
                currency=created_case["currency"],
            ).model_dump(mode="json")
        )

    for passenger_id in payload.link_passenger_ids:
        item_payload = {"item_type": RefundExchangeItemType.PASSENGER.value, "passenger_id": passenger_id}
        await validate_item_link(db, agency_id, created_case, item_payload)
        passenger = await db.collection("passenger_profiles").find_one({"agency_id": agency_id, "id": passenger_id})
        await db.collection("refund_exchange_items").insert_one(
            RefundExchangeItem(
                agency_id=agency_id,
                case_id=created_case["id"],
                item_type="passenger",
                passenger_id=passenger_id,
                description=passenger["display_name"],
                currency=created_case["currency"],
            ).model_dump(mode="json")
        )

    await write_booking_timeline(
        db,
        agency_id,
        booking_id,
        user["id"],
        "refund_exchange.case_created",
        "Refund/exchange case created from booking",
        created_case["case_reference"],
    )
    await write_case_timeline(
        db=db,
        agency_id=agency_id,
        case_id=created_case["id"],
        actor_user_id=user["id"],
        event_type="case.created_from_booking",
        title="Case created from booking",
        summary=f"Created from booking {booking['booking_reference']}.",
        visibility=RefundExchangeTimelineVisibility.INTERNAL,
        metadata={"booking_id": booking_id},
    )
    if booking.get("request_id"):
        await db.collection("request_tasks").insert_one(
            RequestTask(
                agency_id=agency_id,
                request_id=booking["request_id"],
                title="Review refund/exchange case",
                description=f"Review case {created_case['case_reference']} from booking {booking['booking_reference']}.",
                status="open",
                assigned_user_id=user["id"],
            ).model_dump(mode="json")
        )
    await write_audit(
        db=db,
        agency_id=agency_id,
        actor_user_id=user["id"],
        event_type="refund_exchange_case.created_from_booking",
        entity_type="refund_exchange_case",
        entity_id=created_case["id"],
        summary=f"Created case {created_case['case_reference']} from booking.",
        metadata={"booking_id": booking_id},
    )
    return {"case": created_case}


@router.get("/refund-exchange-cases/{case_id}/items")
async def list_case_items(
    agency_id: str,
    case_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    await get_case_or_404(db, agency_id, case_id)
    items = await db.collection("refund_exchange_items").find_many({"agency_id": agency_id, "case_id": case_id})
    items.sort(key=lambda item: _as_sort_value(item.get("updated_at")), reverse=True)
    return {"items": items}


@router.post("/refund-exchange-cases/{case_id}/items", status_code=status.HTTP_201_CREATED)
async def create_case_item(
    agency_id: str,
    case_id: str,
    payload: RefundExchangeItemCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    case = await get_case_or_404(db, agency_id, case_id)
    payload_data = payload.model_dump(mode="json")
    await validate_item_link(db, agency_id, case, payload_data)
    item = RefundExchangeItem(agency_id=agency_id, case_id=case_id, **payload_data)
    created = await db.collection("refund_exchange_items").insert_one(item.model_dump(mode="json"))
    await write_case_timeline(
        db=db,
        agency_id=agency_id,
        case_id=case_id,
        actor_user_id=user["id"],
        event_type="item.added",
        title="Item added",
        summary=created.get("description"),
        visibility=RefundExchangeTimelineVisibility.INTERNAL,
    )
    await write_audit(
        db=db,
        agency_id=agency_id,
        actor_user_id=user["id"],
        event_type="refund_exchange_item.created",
        entity_type="refund_exchange_item",
        entity_id=created["id"],
        summary="Refund/exchange item added.",
    )
    return {"item": created}


@router.put("/refund-exchange-cases/{case_id}/items/{item_id}")
async def update_case_item(
    agency_id: str,
    case_id: str,
    item_id: str,
    payload: RefundExchangeItemUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    case = await get_case_or_404(db, agency_id, case_id)
    current = await get_case_item_or_404(db, agency_id, case_id, item_id)
    updates = clean_updates(payload)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided.")
    candidate = {**current, **updates}
    await validate_item_link(db, agency_id, case, candidate)
    updated = await db.collection("refund_exchange_items").update_one({"agency_id": agency_id, "case_id": case_id, "id": item_id}, updates)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case item not found.")
    await write_case_timeline(
        db=db,
        agency_id=agency_id,
        case_id=case_id,
        actor_user_id=user["id"],
        event_type="item.updated",
        title="Item updated",
        summary=f"Item {item_id} updated.",
        visibility=RefundExchangeTimelineVisibility.INTERNAL,
    )
    await write_audit(
        db=db,
        agency_id=agency_id,
        actor_user_id=user["id"],
        event_type="refund_exchange_item.updated",
        entity_type="refund_exchange_item",
        entity_id=item_id,
        summary="Refund/exchange item updated.",
        metadata={"fields": sorted(updates.keys())},
    )
    return {"item": updated}


@router.get("/refund-exchange-cases/{case_id}/financial-lines")
async def list_case_financial_lines(
    agency_id: str,
    case_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    await get_case_or_404(db, agency_id, case_id)
    lines = await db.collection("refund_exchange_financial_lines").find_many({"agency_id": agency_id, "case_id": case_id})
    lines.sort(key=lambda item: _as_sort_value(item.get("updated_at")), reverse=True)
    return {"items": lines}


@router.post("/refund-exchange-cases/{case_id}/financial-lines", status_code=status.HTTP_201_CREATED)
async def create_financial_line(
    agency_id: str,
    case_id: str,
    payload: RefundExchangeFinancialLineCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    await get_case_or_404(db, agency_id, case_id)
    line = RefundExchangeFinancialLine(agency_id=agency_id, case_id=case_id, **payload.model_dump(mode="json"))
    created = await db.collection("refund_exchange_financial_lines").insert_one(line.model_dump(mode="json"))
    await write_case_timeline(
        db=db,
        agency_id=agency_id,
        case_id=case_id,
        actor_user_id=user["id"],
        event_type="financial_line.added",
        title="Financial line added",
        summary=created.get("description"),
        visibility=RefundExchangeTimelineVisibility.INTERNAL,
    )
    await write_audit(
        db=db,
        agency_id=agency_id,
        actor_user_id=user["id"],
        event_type="refund_exchange_financial_line.created",
        entity_type="refund_exchange_financial_line",
        entity_id=created["id"],
        summary="Financial line added.",
    )
    return {"financial_line": created}


@router.put("/refund-exchange-cases/{case_id}/financial-lines/{line_id}")
async def update_financial_line(
    agency_id: str,
    case_id: str,
    line_id: str,
    payload: RefundExchangeFinancialLineUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    await get_case_or_404(db, agency_id, case_id)
    await get_case_line_or_404(db, agency_id, case_id, line_id)
    updates = clean_updates(payload)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided.")
    updated = await db.collection("refund_exchange_financial_lines").update_one({"agency_id": agency_id, "case_id": case_id, "id": line_id}, updates)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Financial line not found.")
    await write_case_timeline(
        db=db,
        agency_id=agency_id,
        case_id=case_id,
        actor_user_id=user["id"],
        event_type="financial_line.updated",
        title="Financial line updated",
        summary=f"Line {line_id} updated.",
        visibility=RefundExchangeTimelineVisibility.INTERNAL,
    )
    await write_audit(
        db=db,
        agency_id=agency_id,
        actor_user_id=user["id"],
        event_type="refund_exchange_financial_line.updated",
        entity_type="refund_exchange_financial_line",
        entity_id=line_id,
        summary="Financial line updated.",
        metadata={"fields": sorted(updates.keys())},
    )
    return {"financial_line": updated}


@router.get("/refund-exchange-cases/{case_id}/messages")
async def list_case_messages(
    agency_id: str,
    case_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    await get_case_or_404(db, agency_id, case_id)
    messages = await canonical_case_messages(db, agency_id, case_id)
    messages.sort(key=lambda item: _as_sort_value(item.get("created_at")), reverse=True)
    return {"items": messages}


@router.post("/refund-exchange-cases/{case_id}/messages", status_code=status.HTTP_201_CREATED)
async def create_case_message(
    agency_id: str,
    case_id: str,
    payload: RefundExchangeMessageCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    await get_case_or_404(db, agency_id, case_id)
    payload_data = payload.model_dump(mode="json")
    if payload_data.get("sender_type") == RefundExchangeMessageSenderType.CLIENT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Use portal endpoint only for client-visible messages.")
    case = await get_case_or_404(db, agency_id, case_id)
    collaboration = OperationalCollaborationService(db)
    canonical_visibility = (
        "client"
        if payload_data.get("visibility")
        == RefundExchangeMessageVisibility.CLIENT_VISIBLE
        else "internal"
    )
    participants: list[dict[str, Any]] = []
    thread_visibility = ["internal", canonical_visibility]
    if canonical_visibility == "client":
        mapping = await db.collection("portal_access_mappings").find_one(
            {
                "agency_id": agency_id,
                "client_profile_id": case["client_id"],
                "subject_type": "client",
                "status": "active",
            }
        )
        if mapping:
            client = await db.collection("client_profiles").find_one(
                {"agency_id": agency_id, "id": case["client_id"]}
            )
            participants.append(
                {
                    "participant_type": "client_portal",
                    "identity_id": mapping.get("auth_identity_id"),
                    "portal_account_id": mapping.get("id"),
                    "client_id": case["client_id"],
                    "display_name": (client or {}).get("display_name")
                    or "Client Portal",
                    "visibility": ["client"],
                }
            )
    actor = {
        **user,
        "actor_type": "agency",
        "identity_id": user.get("identity_id") or user.get("id"),
        "display_name": user.get("full_name") or user.get("email") or "Agency user",
    }
    try:
        thread_detail = await collaboration.ensure_entity_thread(
            agency_id=agency_id,
            entity_type="after_sales_case",
            entity_id=case_id,
            subject=f"Refund or exchange {case.get('case_reference') or case_id}",
            actor=actor,
            visibility=list(dict.fromkeys(thread_visibility)),
            participants=participants,
            context_key=f"refund_exchange_{canonical_visibility}",
        )
        canonical_message = await collaboration.post_message(
            agency_id,
            thread_detail["thread"]["id"],
            {
                "message_type": "refund_exchange_message",
                "plain_text": payload_data["message_text"],
                "visibility": canonical_visibility,
                "delivery_status": "not_sent"
                if canonical_visibility == "client"
                else "recorded",
                "metadata": {
                    "compatibility_route": "refund_exchange_messages",
                    "external_delivery": False,
                },
            },
            actor,
        )
    except OperationalCollaborationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc
    created = {
        **canonical_message,
        "agency_id": agency_id,
        "case_id": case_id,
        "sender_user_id": user["id"],
        "sender_type": payload_data.get("sender_type"),
        "visibility": payload_data.get("visibility"),
        "message_text": canonical_message.get("plain_text"),
        "canonical_thread_id": thread_detail["thread"]["id"],
        "canonical_message_id": canonical_message["id"],
    }
    await write_audit(
        db=db,
        agency_id=agency_id,
        actor_user_id=user["id"],
        event_type="refund_exchange_message.created",
        entity_type="refund_exchange_message",
        entity_id=created["id"],
        summary="Case message added.",
    )
    return {"message": created}


@router.get("/refund-exchange-cases/{case_id}/timeline")
async def list_case_timeline(
    agency_id: str,
    case_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    await get_case_or_404(db, agency_id, case_id)
    events = await canonical_case_timeline(db, agency_id, case_id)
    events.sort(key=lambda item: _as_sort_value(item.get("created_at")), reverse=True)
    return {"items": events}


@portal_router.get("/refund-exchange-cases")
async def list_portal_cases(
    ctx: dict = Depends(portal_context),
    db: Database = Depends(get_database),
) -> dict:
    agency_id = ctx["account"]["agency_id"]
    client_id = ctx["account"]["client_id"]
    cases = await db.collection("refund_exchange_cases").find_many({"agency_id": agency_id, "client_id": client_id, "client_visible": True})
    bookings = {
        item["id"]: item
        for item in await db.collection("bookings").find_many({"agency_id": agency_id})
    }
    payload = [
        {
            **safe_client_case(item),
            "booking": (
                {
                    "id": bookings[item.get("booking_id")]["id"],
                    "booking_reference": bookings[item.get("booking_id")].get("booking_reference"),
                }
                if item.get("booking_id") and item.get("booking_id") in bookings
                else None
            ),
        }
        for item in sorted(cases, key=lambda item: _as_sort_value(item.get("updated_at")), reverse=True)
    ]
    assert_portal_projection_safe(payload)
    return {"items": payload, "count": len(payload)}


@portal_router.get("/refund-exchange-cases/{case_id}")
async def get_portal_case(
    case_id: str,
    ctx: dict = Depends(portal_context),
    db: Database = Depends(get_database),
) -> dict:
    case = await assert_portal_owns_client_record(db, ctx, "refund_exchange_cases", case_id, "Case not found.")
    if not case.get("client_visible"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")

    agency_id = ctx["account"]["agency_id"]
    booking = await db.collection("bookings").find_one({"agency_id": agency_id, "id": case.get("booking_id")})
    payload = {
        **safe_client_case(case),
        "booking": {"id": booking["id"], "booking_reference": booking["booking_reference"]} if booking else None,
        "items": [
            safe_client_case_item(item)
            for item in await db.collection("refund_exchange_items").find_many({"agency_id": agency_id, "case_id": case_id})
            if item.get("client_visible_notes") is not None or item.get("item_type") in {"passenger", "other"}
        ],
        "financial_lines": [
            safe_client_case_line(item)
            for item in await db.collection("refund_exchange_financial_lines").find_many({"agency_id": agency_id, "case_id": case_id, "client_visible": True})
        ],
        "messages": [
            safe_client_case_message(item)
            for item in await canonical_case_messages(db, agency_id, case_id)
            if item.get("visibility")
            == RefundExchangeMessageVisibility.CLIENT_VISIBLE
        ],
        "timeline": [
            safe_client_case_timeline(item)
            for item in await canonical_case_timeline(db, agency_id, case_id)
            if item.get("visibility")
            == RefundExchangeTimelineVisibility.CLIENT_VISIBLE
        ],
    }
    assert_portal_projection_safe(payload)
    return payload
