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
from services.tenant_service import assert_agency_access, require_any_agency_role

router = APIRouter(prefix="/api/agencies/{agency_id}", tags=["bookings"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant"]


def clean_updates(payload: Any) -> dict:
    return payload.model_dump(exclude_unset=True, mode="json")


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


async def require_write(db: Database, agency_id: str, user: dict) -> None:
    if user.get("global_role") not in {"platform_owner", "platform_admin"}:
        await require_any_agency_role(db, agency_id, user, WRITE_ROLES)


async def write_audit(db: Database, agency_id: str, actor_user_id: str, event_type: str, entity_type: str, entity_id: str, summary: str, metadata: dict | None = None) -> None:
    event = AuditEvent(agency_id=agency_id, actor_user_id=actor_user_id, event_type=event_type, entity_type=entity_type, entity_id=entity_id, summary=summary, metadata=metadata or {})
    await db.collection("audit_events").insert_one(event.model_dump(mode="json"))


async def write_booking_timeline(db: Database, agency_id: str, booking_id: str, actor_user_id: str | None, event_type: str, title: str, summary: str | None = None, visibility: str = "internal", metadata: dict | None = None) -> None:
    event = BookingTimelineEvent(agency_id=agency_id, booking_id=booking_id, actor_user_id=actor_user_id, event_type=event_type, title=title, summary=summary, visibility=visibility, metadata=metadata or {})
    await db.collection("booking_timeline_events").insert_one(event.model_dump(mode="json"))


async def write_offer_timeline(db: Database, agency_id: str, offer_id: str, actor_user_id: str | None, event_type: str, title: str, summary: str | None = None, metadata: dict | None = None) -> None:
    event = OfferTimelineEvent(agency_id=agency_id, offer_id=offer_id, actor_user_id=actor_user_id, event_type=event_type, title=title, summary=summary, visibility="internal", metadata=metadata or {})
    await db.collection("offer_timeline_events").insert_one(event.model_dump(mode="json"))


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


async def recalc_booking_from_invoices(db: Database, agency_id: str, booking_id: str) -> None:
    invoices = await db.collection("invoices").find_many({"agency_id": agency_id, "booking_id": booking_id})
    active = [invoice for invoice in invoices if invoice.get("status") not in {"voided", "cancelled", "archived"}]
    total = sum(float(invoice.get("total_amount") or 0) for invoice in active)
    paid = sum(float(invoice.get("paid_amount") or 0) for invoice in active)
    due = max(total - paid, 0)
    updates = {"total_amount": total, "amount_paid": paid, "amount_due": due}
    await db.collection("bookings").update_one({"agency_id": agency_id, "id": booking_id}, updates)


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
        "timeline": await db.collection("booking_timeline_events").find_many({"agency_id": agency_id, "booking_id": booking_id}),
    }


def selected_or_first(items: list[dict], selected_id: str | None, preferred_key: str | None = None) -> dict | None:
    if selected_id:
        return next((item for item in items if item["id"] == selected_id), None)
    if preferred_key:
        preferred = next((item for item in items if item.get(preferred_key)), None)
        if preferred:
            return preferred
    return items[0] if items else None


async def copy_offer_to_booking(db: Database, agency_id: str, booking: dict, offer: dict, payload: CreateBookingFromOffer) -> None:
    offer_passengers = await db.collection("offer_passengers").find_many({"agency_id": agency_id, "offer_id": offer["id"], "status": "active"})
    routes = await db.collection("offer_route_alternatives").find_many({"agency_id": agency_id, "offer_id": offer["id"]})
    fares = await db.collection("offer_fare_options").find_many({"agency_id": agency_id, "offer_id": offer["id"]})
    selected_fare = next((fare for fare in fares if fare["id"] == payload.selected_fare_option_id), None) if payload.selected_fare_option_id else None
    if payload.selected_fare_option_id and not selected_fare:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected fare option does not belong to the offer.")
    inferred_route_id = payload.selected_route_alternative_id or selected_fare.get("route_alternative_id") if selected_fare else payload.selected_route_alternative_id
    selected_route = selected_or_first(routes, inferred_route_id, "is_recommended")
    if inferred_route_id and not selected_route:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected route does not belong to the offer.")
    route_fares = [fare for fare in fares if not selected_route or fare.get("route_alternative_id") == selected_route["id"]]
    selected_fare = selected_fare or selected_or_first(route_fares, None, "is_recommended")
    if selected_fare and selected_route and selected_fare.get("route_alternative_id") != selected_route["id"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected fare option does not belong to the selected offer route.")

    for offer_passenger in offer_passengers:
        passenger = BookingPassenger(
            agency_id=agency_id,
            booking_id=booking["id"],
            passenger_id=offer_passenger.get("passenger_id"),
            offer_passenger_id=offer_passenger["id"],
            snapshot_display_name=offer_passenger["snapshot_display_name"],
            snapshot_date_of_birth=offer_passenger.get("snapshot_date_of_birth"),
            snapshot_passenger_type=offer_passenger.get("snapshot_passenger_type") or "ADT",
            is_primary_traveler=offer_passenger.get("is_primary_traveler", False),
        )
        await db.collection("booking_passengers").insert_one(passenger.model_dump(mode="json"))

    offer_segments = await db.collection("offer_segments").find_many({"agency_id": agency_id, "offer_id": offer["id"], "route_alternative_id": selected_route["id"]}) if selected_route else []
    copied_segments = []
    for offer_segment in offer_segments:
        segment = BookingSegment(
            agency_id=agency_id,
            booking_id=booking["id"],
            offer_segment_id=offer_segment["id"],
            sequence=offer_segment["sequence"],
            marketing_airline_code=offer_segment["marketing_airline_code"],
            marketing_airline_name=offer_segment.get("marketing_airline_name"),
            operating_airline_code=offer_segment.get("operating_airline_code"),
            operating_airline_name=offer_segment.get("operating_airline_name"),
            flight_number=offer_segment.get("flight_number"),
            origin_airport_code=offer_segment["origin_airport_code"],
            origin_city=offer_segment.get("origin_city"),
            destination_airport_code=offer_segment["destination_airport_code"],
            destination_city=offer_segment.get("destination_city"),
            departure_datetime=offer_segment.get("departure_datetime"),
            arrival_datetime=offer_segment.get("arrival_datetime"),
            aircraft_type=offer_segment.get("aircraft_type"),
            cabin=offer_segment.get("cabin"),
            booking_class=offer_segment.get("booking_class"),
            fare_basis=offer_segment.get("fare_basis"),
            segment_status="booked",
            baggage_summary=offer_segment.get("baggage_summary"),
            notes=offer_segment.get("notes"),
        )
        copied_segments.append(await db.collection("booking_segments").insert_one(segment.model_dump(mode="json")))

    price_lines = await db.collection("offer_price_lines").find_many({"agency_id": agency_id, "offer_id": offer["id"], "fare_option_id": selected_fare["id"], "status": "active"}) if selected_fare else []
    service_checks = await db.collection("offer_service_checks").find_many({"agency_id": agency_id, "offer_id": offer["id"], "status": "active"})
    snapshot = {
        "source": "offer",
        "offer_reference": offer["offer_reference"],
        "offer_id": offer["id"],
        "selected_route": selected_route,
        "selected_fare_option": selected_fare,
        "passengers": offer_passengers,
        "segments": offer_segments,
        "price_lines": price_lines,
        "service_checks": service_checks,
        "snapshotted_at": datetime.now(timezone.utc).isoformat(),
    }
    updates = {
        "selected_route_alternative_id": selected_route["id"] if selected_route else None,
        "selected_fare_option_id": selected_fare["id"] if selected_fare else None,
        "booking_snapshot": snapshot,
        "total_amount": float(selected_fare.get("total_amount") or 0) if selected_fare else 0,
        "amount_due": float(selected_fare.get("total_amount") or 0) if selected_fare else 0,
    }
    await db.collection("bookings").update_one({"agency_id": agency_id, "id": booking["id"]}, updates)


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
    await get_client_or_404(db, agency_id, payload.client_id)
    if payload.request_id and not await db.collection("travel_requests").find_one({"agency_id": agency_id, "id": payload.request_id, "client_id": payload.client_id}):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request must belong to the selected client.")
    if payload.offer_id and not await db.collection("offers").find_one({"agency_id": agency_id, "id": payload.offer_id, "client_id": payload.client_id}):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Offer must belong to the selected client.")
    booking = Booking(agency_id=agency_id, booking_reference=await next_reference(db, agency_id), created_by_user_id=user["id"], **payload.model_dump(mode="json"))
    created = await db.collection("bookings").insert_one(booking.model_dump(mode="json"))
    await write_booking_timeline(db, agency_id, booking.id, user["id"], "booking.created", "Booking tracking record created", "Manual tracking only. Reservation is handled externally.")
    await write_audit(db, agency_id, user["id"], "booking.created", "booking", booking.id, f"Created booking {booking.booking_reference}.")
    return {"booking": created}


@router.post("/offers/{offer_id}/create-booking", status_code=status.HTTP_201_CREATED)
async def create_booking_from_offer(agency_id: str, offer_id: str, payload: CreateBookingFromOffer, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    offer = await get_offer_or_404(db, agency_id, offer_id)
    booking = Booking(
        agency_id=agency_id,
        booking_reference=await next_reference(db, agency_id),
        client_id=offer["client_id"],
        request_id=offer.get("request_id"),
        offer_id=offer_id,
        created_by_user_id=user["id"],
        assigned_user_id=payload.assigned_user_id or offer.get("assigned_user_id"),
        status=payload.status,
        pnr=payload.pnr,
        booking_channel=payload.booking_channel,
        currency=offer.get("currency") or "EUR",
        internal_notes=payload.internal_notes,
    )
    created = await db.collection("bookings").insert_one(booking.model_dump(mode="json"))
    await copy_offer_to_booking(db, agency_id, created, offer, payload)
    if payload.accept_offer:
        await db.collection("offers").update_one({"agency_id": agency_id, "id": offer_id}, {"status": "accepted", "accepted_at": datetime.now(timezone.utc)})
    await write_booking_timeline(db, agency_id, booking.id, user["id"], "booking.created_from_offer", "Booking created from offer", offer["offer_reference"], metadata={"offer_id": offer_id})
    await write_offer_timeline(db, agency_id, offer_id, user["id"], "offer.booking_created", "Booking created", booking.booking_reference, {"booking_id": booking.id})
    await write_audit(db, agency_id, user["id"], "booking.created_from_offer", "booking", booking.id, "Created booking from offer.", {"offer_id": offer_id})
    return await booking_detail(db, agency_id, booking.id)


@router.get("/bookings/{booking_id}")
async def get_booking(agency_id: str, booking_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    return await booking_detail(db, agency_id, booking_id)


@router.put("/bookings/{booking_id}")
async def update_booking(agency_id: str, booking_id: str, payload: BookingUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_booking_or_404(db, agency_id, booking_id)
    updates = clean_updates(payload)
    if updates.get("status") == "ticketed":
        updates["ticketed_at"] = datetime.now(timezone.utc)
    if updates.get("status") == "cancelled":
        updates["cancelled_at"] = datetime.now(timezone.utc)
    updated = await db.collection("bookings").update_one({"agency_id": agency_id, "id": booking_id}, updates)
    await write_booking_timeline(db, agency_id, booking_id, user["id"], "booking.updated", "Booking updated")
    return {"booking": updated}


@router.post("/bookings/{booking_id}/archive")
async def archive_booking(agency_id: str, booking_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    updated = await db.collection("bookings").update_one({"agency_id": agency_id, "id": booking_id}, {"status": "archived"})
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found.")
    await write_booking_timeline(db, agency_id, booking_id, user["id"], "booking.archived", "Booking archived")
    return {"booking": updated}


@router.post("/bookings/{booking_id}/cancel")
async def cancel_booking(agency_id: str, booking_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    updated = await db.collection("bookings").update_one({"agency_id": agency_id, "id": booking_id}, {"status": "cancelled", "cancelled_at": datetime.now(timezone.utc)})
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found.")
    await write_booking_timeline(db, agency_id, booking_id, user["id"], "booking.cancelled", "Booking cancelled", "External cancellation should be documented separately.")
    return {"booking": updated}


@router.get("/bookings/{booking_id}/timeline")
async def list_booking_timeline(agency_id: str, booking_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    await get_booking_or_404(db, agency_id, booking_id)
    items = await db.collection("booking_timeline_events").find_many({"agency_id": agency_id, "booking_id": booking_id})
    items.sort(key=lambda item: item.get("created_at", ""))
    return {"items": items}


@router.get("/bookings/{booking_id}/passengers")
async def list_booking_passengers(agency_id: str, booking_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    await get_booking_or_404(db, agency_id, booking_id)
    return {"items": await db.collection("booking_passengers").find_many({"agency_id": agency_id, "booking_id": booking_id})}


@router.post("/bookings/{booking_id}/passengers", status_code=status.HTTP_201_CREATED)
async def create_booking_passenger(agency_id: str, booking_id: str, payload: BookingPassengerCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_booking_or_404(db, agency_id, booking_id)
    passenger = await get_passenger_snapshot(db, agency_id, payload.passenger_id)
    if not payload.snapshot_display_name and not passenger:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide a passenger profile or snapshot display name.")
    model = BookingPassenger(
        agency_id=agency_id,
        booking_id=booking_id,
        passenger_id=payload.passenger_id,
        offer_passenger_id=payload.offer_passenger_id,
        snapshot_display_name=payload.snapshot_display_name or passenger["display_name"],
        snapshot_date_of_birth=payload.snapshot_date_of_birth or passenger.get("date_of_birth"),
        snapshot_passenger_type=payload.snapshot_passenger_type or passenger.get("passenger_type", "ADT"),
        is_primary_traveler=payload.is_primary_traveler,
        ticket_status=payload.ticket_status,
    )
    created = await db.collection("booking_passengers").insert_one(model.model_dump(mode="json"))
    await write_booking_timeline(db, agency_id, booking_id, user["id"], "booking.passenger_added", "Passenger added", model.snapshot_display_name)
    return {"passenger": created}


@router.put("/bookings/{booking_id}/passengers/{booking_passenger_id}")
async def update_booking_passenger(agency_id: str, booking_id: str, booking_passenger_id: str, payload: BookingPassengerUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    updated = await db.collection("booking_passengers").update_one({"agency_id": agency_id, "booking_id": booking_id, "id": booking_passenger_id}, clean_updates(payload))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking passenger not found.")
    await write_booking_timeline(db, agency_id, booking_id, user["id"], "booking.passenger_updated", "Passenger tracking updated", updated["snapshot_display_name"])
    return {"passenger": updated}


@router.get("/bookings/{booking_id}/segments")
async def list_booking_segments(agency_id: str, booking_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    await get_booking_or_404(db, agency_id, booking_id)
    return {"items": await db.collection("booking_segments").find_many({"agency_id": agency_id, "booking_id": booking_id})}


@router.post("/bookings/{booking_id}/segments", status_code=status.HTTP_201_CREATED)
async def create_booking_segment(agency_id: str, booking_id: str, payload: BookingSegmentCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_booking_or_404(db, agency_id, booking_id)
    model = BookingSegment(agency_id=agency_id, booking_id=booking_id, **payload.model_dump(mode="json"))
    created = await db.collection("booking_segments").insert_one(model.model_dump(mode="json"))
    await write_booking_timeline(db, agency_id, booking_id, user["id"], "booking.segment_added", "Segment added", f"{model.origin_airport_code}-{model.destination_airport_code}")
    return {"segment": created}


@router.put("/bookings/{booking_id}/segments/{segment_id}")
async def update_booking_segment(agency_id: str, booking_id: str, segment_id: str, payload: BookingSegmentUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    updated = await db.collection("booking_segments").update_one({"agency_id": agency_id, "booking_id": booking_id, "id": segment_id}, clean_updates(payload))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking segment not found.")
    await write_booking_timeline(db, agency_id, booking_id, user["id"], "booking.segment_updated", "Segment updated", f"{updated['origin_airport_code']}-{updated['destination_airport_code']}")
    return {"segment": updated}


@router.get("/bookings/{booking_id}/tickets")
async def list_tickets(agency_id: str, booking_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    await get_booking_or_404(db, agency_id, booking_id)
    return {"items": await db.collection("ticket_records").find_many({"agency_id": agency_id, "booking_id": booking_id})}


@router.post("/bookings/{booking_id}/tickets", status_code=status.HTTP_201_CREATED)
async def create_ticket(agency_id: str, booking_id: str, payload: TicketRecordCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_booking_or_404(db, agency_id, booking_id)
    total = payload.total_amount if payload.total_amount is not None else payload.base_fare_amount + payload.taxes_amount
    model = TicketRecord(agency_id=agency_id, booking_id=booking_id, total_amount=total, **payload.model_dump(exclude={"total_amount"}, mode="json"))
    created = await db.collection("ticket_records").insert_one(model.model_dump(mode="json"))
    if payload.booking_passenger_id:
        await db.collection("booking_passengers").update_one({"agency_id": agency_id, "booking_id": booking_id, "id": payload.booking_passenger_id}, {"ticket_status": "issued" if payload.status == "issued" else "pending"})
    await write_booking_timeline(db, agency_id, booking_id, user["id"], "booking.ticket_recorded", "Ticket recorded", model.ticket_number)
    return {"ticket": created}


@router.put("/bookings/{booking_id}/tickets/{ticket_id}")
async def update_ticket(agency_id: str, booking_id: str, ticket_id: str, payload: TicketRecordUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    updates = clean_updates(payload)
    if "total_amount" not in updates and ("base_fare_amount" in updates or "taxes_amount" in updates):
        current = await db.collection("ticket_records").find_one({"agency_id": agency_id, "booking_id": booking_id, "id": ticket_id})
        if current:
            updates["total_amount"] = float(updates.get("base_fare_amount", current.get("base_fare_amount") or 0)) + float(updates.get("taxes_amount", current.get("taxes_amount") or 0))
    updated = await db.collection("ticket_records").update_one({"agency_id": agency_id, "booking_id": booking_id, "id": ticket_id}, updates)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")
    await write_booking_timeline(db, agency_id, booking_id, user["id"], "booking.ticket_updated", "Ticket updated", updated["ticket_number"])
    return {"ticket": updated}


@router.post("/bookings/{booking_id}/tickets/{ticket_id}/void")
async def void_ticket(agency_id: str, booking_id: str, ticket_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    updated = await db.collection("ticket_records").update_one({"agency_id": agency_id, "booking_id": booking_id, "id": ticket_id}, {"status": "voided"})
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")
    await write_booking_timeline(db, agency_id, booking_id, user["id"], "booking.ticket_voided", "Ticket voided", updated["ticket_number"])
    return {"ticket": updated}


@router.get("/bookings/{booking_id}/emds")
async def list_emds(agency_id: str, booking_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    await get_booking_or_404(db, agency_id, booking_id)
    return {"items": await db.collection("emd_records").find_many({"agency_id": agency_id, "booking_id": booking_id})}


@router.post("/bookings/{booking_id}/emds", status_code=status.HTTP_201_CREATED)
async def create_emd(agency_id: str, booking_id: str, payload: EMDRecordCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_booking_or_404(db, agency_id, booking_id)
    if payload.ticket_id and not await db.collection("ticket_records").find_one({"agency_id": agency_id, "booking_id": booking_id, "id": payload.ticket_id}):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticket must belong to this booking.")
    model = EMDRecord(agency_id=agency_id, booking_id=booking_id, **payload.model_dump(mode="json"))
    created = await db.collection("emd_records").insert_one(model.model_dump(mode="json"))
    await write_booking_timeline(db, agency_id, booking_id, user["id"], "booking.emd_recorded", "EMD recorded", model.emd_number)
    return {"emd": created}


@router.put("/bookings/{booking_id}/emds/{emd_id}")
async def update_emd(agency_id: str, booking_id: str, emd_id: str, payload: EMDRecordUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    updated = await db.collection("emd_records").update_one({"agency_id": agency_id, "booking_id": booking_id, "id": emd_id}, clean_updates(payload))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="EMD not found.")
    await write_booking_timeline(db, agency_id, booking_id, user["id"], "booking.emd_updated", "EMD updated", updated["emd_number"])
    return {"emd": updated}


@router.post("/bookings/{booking_id}/emds/{emd_id}/void")
async def void_emd(agency_id: str, booking_id: str, emd_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    updated = await db.collection("emd_records").update_one({"agency_id": agency_id, "booking_id": booking_id, "id": emd_id}, {"status": "voided"})
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="EMD not found.")
    await write_booking_timeline(db, agency_id, booking_id, user["id"], "booking.emd_voided", "EMD voided", updated["emd_number"])
    return {"emd": updated}
