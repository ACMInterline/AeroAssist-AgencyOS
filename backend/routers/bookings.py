from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    AuditEvent,
    Booking,
    BookingCreate,
    BookingPassenger,
    BookingPassengerCreate,
    BookingPassengerUpdate,
    BookingSegment,
    BookingSegmentCreate,
    BookingSegmentUpdate,
    BookingTimelineEvent,
    BookingUpdate,
    CreateBookingFromOffer,
    EMDRecord,
    EMDRecordCreate,
    EMDRecordUpdate,
    OfferTimelineEvent,
    TicketRecord,
    TicketRecordCreate,
    TicketRecordUpdate,
)
from services.authorization_service import require_permission
from services.operational_collaboration_service import OperationalCollaborationService
from services.tenant_service import assert_agency_access, require_any_agency_role

router = APIRouter(prefix="/api/agencies/{agency_id}", tags=["bookings"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant"]


def clean_updates(payload: Any) -> dict:
    return payload.model_dump(exclude_unset=True, mode="json")


def legacy_booking_write_conflict() -> None:
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=(
            "Legacy Booking routes are read-only compatibility projections. "
            "Use Booking Handoff and BookingWorkspace to prepare work, then "
            "record the governed external result in BookingRecord."
        ),
    )


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    await require_any_agency_role(db, agency_id, user, READ_ROLES)
    require_permission(user, "view_bookings")


async def require_write(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    await require_any_agency_role(db, agency_id, user, WRITE_ROLES)
    require_permission(user, "edit_bookings")


async def write_audit(db: Database, agency_id: str, actor_user_id: str, event_type: str, entity_type: str, entity_id: str, summary: str, metadata: dict | None = None) -> None:
    event = AuditEvent(agency_id=agency_id, actor_user_id=actor_user_id, event_type=event_type, entity_type=entity_type, entity_id=entity_id, summary=summary, metadata=metadata or {})
    await db.collection("audit_events").insert_one(event.model_dump(mode="json"))


async def write_booking_timeline(db: Database, agency_id: str, booking_id: str, actor_user_id: str | None, event_type: str, title: str, summary: str | None = None, visibility: str = "internal", metadata: dict | None = None) -> None:
    await OperationalCollaborationService(db).record_compatibility_event(
        agency_id=agency_id,
        entity_type="booking",
        entity_id=booking_id,
        source_event_type=event_type,
        summary=summary or title,
        actor_user_id=actor_user_id,
        visibility="client" if visibility == "client_visible" else "internal",
        details={"title": title, **(metadata or {})},
        source_collection="booking_timeline_events",
    )


async def write_offer_timeline(db: Database, agency_id: str, offer_id: str, actor_user_id: str | None, event_type: str, title: str, summary: str | None = None, metadata: dict | None = None) -> None:
    await OperationalCollaborationService(db).record_compatibility_event(
        agency_id=agency_id,
        entity_type="offer",
        entity_id=offer_id,
        source_event_type=event_type,
        summary=summary or title,
        actor_user_id=actor_user_id,
        visibility="internal",
        details={"title": title, **(metadata or {})},
        source_collection="offer_timeline_events",
    )


async def next_reference(db: Database, agency_id: str) -> str:
    count = await db.collection("bookings").count({"agency_id": agency_id})
    return f"BKG-{count + 1:05d}"


async def get_client_or_404(db: Database, agency_id: str, client_id: str) -> dict:
    client = await db.collection("client_profiles").find_one({"agency_id": agency_id, "id": client_id})
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")
    return client


async def get_booking_or_404(db: Database, agency_id: str, booking_id: str) -> dict:
    booking = await db.collection("bookings").find_one({"agency_id": agency_id, "id": booking_id})
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found.")
    return booking


async def get_offer_or_404(db: Database, agency_id: str, offer_id: str) -> dict:
    offer = await db.collection("offers").find_one({"agency_id": agency_id, "id": offer_id})
    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found.")
    return offer


async def get_passenger_snapshot(db: Database, agency_id: str, passenger_id: str | None) -> dict | None:
    if not passenger_id:
        return None
    passenger = await db.collection("passenger_profiles").find_one({"agency_id": agency_id, "id": passenger_id})
    if not passenger:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Passenger not found.")
    return passenger


async def booking_timeline_items(
    db: Database, agency_id: str, booking_id: str
) -> list[dict[str, Any]]:
    legacy = await db.collection("booking_timeline_events").find_many(
        {"agency_id": agency_id, "booking_id": booking_id},
        sort=[("created_at", 1), ("id", 1)],
        limit=200,
    )
    canonical = await OperationalCollaborationService(db).list_timeline(
        agency_id=agency_id,
        entity_type="booking",
        entity_id=booking_id,
        visibility={"internal", "agency", "client"},
        limit=200,
    )
    items = legacy + [
        {
            **item,
            "booking_id": booking_id,
            "actor_user_id": item.get("actor_id"),
            "title": (item.get("details") or {}).get("title")
            or item.get("summary")
            or item.get("event_type"),
            "visibility": "client_visible"
            if item.get("visibility") == "client"
            else "internal",
            "metadata": item.get("details") or {},
            "created_at": item.get("event_time") or item.get("created_at"),
            "canonical_timeline_entry_id": item.get("id"),
        }
        for item in canonical
    ]
    items.sort(key=lambda item: str(item.get("created_at") or ""))
    return items


async def booking_detail(db: Database, agency_id: str, booking_id: str) -> dict:
    booking = await get_booking_or_404(db, agency_id, booking_id)
    invoices = await db.collection("invoices").find_many({"agency_id": agency_id, "booking_id": booking_id})
    payments = []
    for invoice in invoices:
        payments.extend(await db.collection("payment_records").find_many({"agency_id": agency_id, "invoice_id": invoice["id"]}))
    return {
        "booking": booking,
        "client": await get_client_or_404(db, agency_id, booking["client_id"]),
        "passengers": await db.collection("booking_passengers").find_many({"agency_id": agency_id, "booking_id": booking_id}),
        "segments": await db.collection("booking_segments").find_many({"agency_id": agency_id, "booking_id": booking_id}),
        "tickets": await db.collection("ticket_records").find_many({"agency_id": agency_id, "booking_id": booking_id}),
        "emds": await db.collection("emd_records").find_many({"agency_id": agency_id, "booking_id": booking_id}),
        "invoices": invoices,
        "payments": payments,
        "timeline": await booking_timeline_items(db, agency_id, booking_id),
    }


@router.get("/bookings")
async def list_bookings(agency_id: str, search: Optional[str] = Query(default=None), status_filter: Optional[str] = Query(default=None, alias="status"), channel: Optional[str] = None, client_id: Optional[str] = None, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    filters = {"agency_id": agency_id}
    if status_filter:
        filters["status"] = status_filter
    if channel:
        filters["booking_channel"] = channel
    if client_id:
        filters["client_id"] = client_id
    items = await db.collection("bookings").find_many(filters)
    clients = {client["id"]: client for client in await db.collection("client_profiles").find_many({"agency_id": agency_id})}
    if search:
        needle = search.lower()
        items = [item for item in items if any(needle in str(item.get(field) or "").lower() for field in ["booking_reference", "pnr", "internal_notes", "client_visible_notes"]) or needle in clients.get(item["client_id"], {}).get("display_name", "").lower()]
    items.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    return {"items": [{**item, "client": clients.get(item["client_id"])} for item in items]}


@router.post("/bookings", status_code=status.HTTP_201_CREATED)
async def create_booking(agency_id: str, payload: BookingCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    legacy_booking_write_conflict()


@router.post("/offers/{offer_id}/create-booking", status_code=status.HTTP_201_CREATED)
async def create_booking_from_offer(agency_id: str, offer_id: str, payload: CreateBookingFromOffer, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    legacy_booking_write_conflict()


@router.get("/bookings/{booking_id}")
async def get_booking(agency_id: str, booking_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    return await booking_detail(db, agency_id, booking_id)


@router.put("/bookings/{booking_id}")
async def update_booking(agency_id: str, booking_id: str, payload: BookingUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_booking_or_404(db, agency_id, booking_id)
    legacy_booking_write_conflict()


@router.post("/bookings/{booking_id}/archive")
async def archive_booking(agency_id: str, booking_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_booking_or_404(db, agency_id, booking_id)
    legacy_booking_write_conflict()


@router.post("/bookings/{booking_id}/cancel")
async def cancel_booking(agency_id: str, booking_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_booking_or_404(db, agency_id, booking_id)
    legacy_booking_write_conflict()


@router.get("/bookings/{booking_id}/timeline")
async def list_booking_timeline(agency_id: str, booking_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    await get_booking_or_404(db, agency_id, booking_id)
    return {"items": await booking_timeline_items(db, agency_id, booking_id)}


@router.get("/bookings/{booking_id}/passengers")
async def list_booking_passengers(agency_id: str, booking_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    await get_booking_or_404(db, agency_id, booking_id)
    return {"items": await db.collection("booking_passengers").find_many({"agency_id": agency_id, "booking_id": booking_id})}


@router.post("/bookings/{booking_id}/passengers", status_code=status.HTTP_201_CREATED)
async def create_booking_passenger(agency_id: str, booking_id: str, payload: BookingPassengerCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_booking_or_404(db, agency_id, booking_id)
    legacy_booking_write_conflict()


@router.put("/bookings/{booking_id}/passengers/{booking_passenger_id}")
async def update_booking_passenger(agency_id: str, booking_id: str, booking_passenger_id: str, payload: BookingPassengerUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_booking_or_404(db, agency_id, booking_id)
    legacy_booking_write_conflict()


@router.get("/bookings/{booking_id}/segments")
async def list_booking_segments(agency_id: str, booking_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    await get_booking_or_404(db, agency_id, booking_id)
    return {"items": await db.collection("booking_segments").find_many({"agency_id": agency_id, "booking_id": booking_id})}


@router.post("/bookings/{booking_id}/segments", status_code=status.HTTP_201_CREATED)
async def create_booking_segment(agency_id: str, booking_id: str, payload: BookingSegmentCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_booking_or_404(db, agency_id, booking_id)
    legacy_booking_write_conflict()


@router.put("/bookings/{booking_id}/segments/{segment_id}")
async def update_booking_segment(agency_id: str, booking_id: str, segment_id: str, payload: BookingSegmentUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_booking_or_404(db, agency_id, booking_id)
    legacy_booking_write_conflict()


@router.get("/bookings/{booking_id}/tickets")
async def list_tickets(agency_id: str, booking_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    await get_booking_or_404(db, agency_id, booking_id)
    return {"items": await db.collection("ticket_records").find_many({"agency_id": agency_id, "booking_id": booking_id})}


@router.post("/bookings/{booking_id}/tickets", status_code=status.HTTP_201_CREATED)
async def create_ticket(agency_id: str, booking_id: str, payload: TicketRecordCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_booking_or_404(db, agency_id, booking_id)
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="This compatibility Booking route is read-only for Ticket truth. Use the canonical Ticket route with a confirmed BookingRecord or governed standalone import evidence.",
    )


@router.put("/bookings/{booking_id}/tickets/{ticket_id}")
async def update_ticket(agency_id: str, booking_id: str, ticket_id: str, payload: TicketRecordUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_booking_or_404(db, agency_id, booking_id)
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="This compatibility Booking route cannot overwrite canonical TicketRecord truth.",
    )


@router.post("/bookings/{booking_id}/tickets/{ticket_id}/void")
async def void_ticket(agency_id: str, booking_id: str, ticket_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_booking_or_404(db, agency_id, booking_id)
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Ticket voiding is not available through the compatibility Booking route.",
    )


@router.get("/bookings/{booking_id}/emds")
async def list_emds(agency_id: str, booking_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    await get_booking_or_404(db, agency_id, booking_id)
    return {"items": await db.collection("emd_records").find_many({"agency_id": agency_id, "booking_id": booking_id})}


@router.post("/bookings/{booking_id}/emds", status_code=status.HTTP_201_CREATED)
async def create_emd(agency_id: str, booking_id: str, payload: EMDRecordCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_booking_or_404(db, agency_id, booking_id)
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="This compatibility Booking route is read-only for EMD truth. Use the canonical EMD route with a confirmed BookingRecord or governed standalone import evidence.",
    )


@router.put("/bookings/{booking_id}/emds/{emd_id}")
async def update_emd(agency_id: str, booking_id: str, emd_id: str, payload: EMDRecordUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_booking_or_404(db, agency_id, booking_id)
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="This compatibility Booking route cannot overwrite canonical EMDRecord truth.",
    )


@router.post("/bookings/{booking_id}/emds/{emd_id}/void")
async def void_emd(agency_id: str, booking_id: str, emd_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_booking_or_404(db, agency_id, booking_id)
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="EMD voiding is not available through the compatibility Booking route.",
    )
