from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status

from database import Database, get_database
from services.seed_service import seed_core_data

router = APIRouter(prefix="/api/portal", tags=["portal"])

DEFAULT_PORTAL_EMAIL = "anna.client@example.com"


def brand_snapshot(workspace: dict | None, agency: dict | None) -> dict:
    workspace = workspace or {}
    agency = agency or {}
    return {
        "brand_name": workspace.get("brand_name") or agency.get("name"),
        "logo_url": workspace.get("logo_url"),
        "primary_color": workspace.get("primary_color") or "#2563eb",
        "secondary_color": workspace.get("secondary_color") or "#0f172a",
        "font_family": workspace.get("font_family") or "Inter",
    }


async def portal_context(
    x_demo_role: Optional[str] = Header(default=None),
    x_demo_client_email: Optional[str] = Header(default=None),
    db: Database = Depends(get_database),
) -> dict:
    await seed_core_data(db)
    email = x_demo_client_email or DEFAULT_PORTAL_EMAIL
    mapping = await db.collection("portal_access_mappings").find_one({"user_email": email})
    if not mapping or mapping.get("portal_status") != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Active demo portal account not found.")
    agency = await db.collection("agencies").find_one({"id": mapping["agency_id"]})
    client = await db.collection("client_profiles").find_one({"agency_id": mapping["agency_id"], "id": mapping["client_id"]})
    if not agency or not client or client.get("status") == "archived":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portal client context not found.")
    workspace = await db.collection("agency_workspaces").find_one({"agency_id": mapping["agency_id"]})
    await db.collection("portal_access_mappings").update_one({"id": mapping["id"]}, {"last_login_at": datetime.now(timezone.utc)})
    return {
        "account": mapping,
        "agency": agency,
        "workspace": workspace,
        "client": client,
        "brand": brand_snapshot(workspace, agency),
        "demo_role": x_demo_role or "portal_client",
    }


def safe_client(client: dict) -> dict:
    return {
        "id": client["id"],
        "client_type": client.get("client_type"),
        "display_name": client.get("display_name"),
        "legal_name": client.get("legal_name"),
        "primary_email": client.get("primary_email"),
        "primary_phone": client.get("primary_phone"),
        "country": client.get("country"),
        "city": client.get("city"),
        "preferred_language": client.get("preferred_language"),
        "default_currency": client.get("default_currency"),
        "portal_status": client.get("portal_status"),
        "client_visible_notes": client.get("client_visible_notes"),
        "status": client.get("status"),
    }


def safe_passenger(passenger: dict, relationship: dict | None = None) -> dict:
    return {
        "id": passenger["id"],
        "display_name": passenger.get("display_name"),
        "first_name": passenger.get("first_name"),
        "middle_name": passenger.get("middle_name"),
        "last_name": passenger.get("last_name"),
        "date_of_birth": passenger.get("date_of_birth"),
        "passenger_type": passenger.get("passenger_type"),
        "gender": passenger.get("gender"),
        "nationality": passenger.get("nationality"),
        "residence_country": passenger.get("residence_country"),
        "primary_language": passenger.get("primary_language"),
        "passport_country": passenger.get("passport_country"),
        "passport_expiry": passenger.get("passport_expiry"),
        "known_assistance_needs": passenger.get("known_assistance_needs"),
        "meal_preferences": passenger.get("meal_preferences"),
        "loyalty_numbers": passenger.get("loyalty_numbers", []),
        "relationship": relationship.get("relationship_type") if relationship else None,
    }


async def permitted_relationships(db: Database, ctx: dict) -> list[dict]:
    return [
        item
        for item in await db.collection("client_passenger_relationships").find_many({"agency_id": ctx["account"]["agency_id"], "client_id": ctx["account"]["client_id"], "status": "active"})
        if item.get("can_view")
    ]


async def permitted_passenger_ids(db: Database, ctx: dict) -> set[str]:
    return {item["passenger_id"] for item in await permitted_relationships(db, ctx)}


def safe_request(request: dict) -> dict:
    return {
        "id": request["id"],
        "request_reference": request.get("request_reference"),
        "title": request.get("title"),
        "status": request.get("status"),
        "priority": request.get("priority"),
        "source": request.get("source"),
        "requested_departure_date": request.get("requested_departure_date"),
        "requested_return_date": request.get("requested_return_date"),
        "route_summary": request.get("route_summary"),
        "service_summary": request.get("service_summary"),
        "client_notes": request.get("client_notes"),
        "client_visible_notes": request.get("client_visible_notes"),
        "passenger_count": request.get("passenger_count"),
        "service_count": request.get("service_count"),
    }


def safe_requested_service(service: dict) -> dict:
    return {
        "id": service["id"],
        "passenger_id": service.get("passenger_id"),
        "service_code": service.get("service_code"),
        "service_name": service.get("service_name"),
        "service_category": service.get("service_category"),
        "status": service.get("status"),
        "details": service.get("details"),
        "client_visible_summary": service.get("client_visible_summary"),
        "requires_documents": service.get("requires_documents"),
        "requires_airline_approval": service.get("requires_airline_approval"),
    }


def safe_request_message(message: dict) -> dict:
    return {
        "id": message["id"],
        "sender_type": message.get("sender_type"),
        "message_text": message.get("message_text"),
        "created_at": message.get("created_at"),
    }


def safe_request_task(task: dict) -> dict:
    return {
        "id": task["id"],
        "title": task.get("title"),
        "description": task.get("description"),
        "status": task.get("status"),
        "priority": task.get("priority"),
        "due_at": task.get("due_at"),
        "completed_at": task.get("completed_at"),
    }


def safe_request_timeline_event(event: dict) -> dict:
    return {
        "id": event["id"],
        "event_type": event.get("event_type"),
        "title": event.get("title"),
        "summary": event.get("summary"),
        "created_at": event.get("created_at"),
    }


def safe_offer(offer: dict) -> dict:
    return {
        "id": offer["id"],
        "offer_reference": offer.get("offer_reference"),
        "title": offer.get("title"),
        "status": offer.get("status"),
        "source": offer.get("source"),
        "currency": offer.get("currency"),
        "client_language": offer.get("client_language"),
        "valid_until": offer.get("valid_until"),
        "sent_at": offer.get("sent_at"),
        "client_visible_intro": offer.get("client_visible_intro"),
        "client_visible_terms": offer.get("client_visible_terms"),
        "route_alternative_count": offer.get("route_alternative_count"),
        "fare_option_count": offer.get("fare_option_count"),
        "total_min_amount": offer.get("total_min_amount"),
        "total_max_amount": offer.get("total_max_amount"),
        "recommended_route_alternative_id": offer.get("recommended_route_alternative_id"),
        "recommended_fare_option_id": offer.get("recommended_fare_option_id"),
        "sent_snapshot_available": bool(offer.get("sent_snapshot")),
    }


def safe_offer_passenger(passenger: dict) -> dict:
    return {
        "id": passenger["id"],
        "passenger_id": passenger.get("passenger_id"),
        "role_in_offer": passenger.get("role_in_offer"),
        "is_primary_traveler": passenger.get("is_primary_traveler"),
        "status": passenger.get("status"),
    }


def safe_offer_route(route: dict) -> dict:
    return {
        "id": route["id"],
        "sequence": route.get("sequence"),
        "label": route.get("label"),
        "title": route.get("title"),
        "status": route.get("status"),
        "carrier_summary": route.get("carrier_summary"),
        "route_summary": route.get("route_summary"),
        "schedule_summary": route.get("schedule_summary"),
        "total_travel_time_minutes": route.get("total_travel_time_minutes"),
        "stop_count": route.get("stop_count"),
        "connection_quality": route.get("connection_quality"),
        "service_support_summary": route.get("service_support_summary"),
        "recommendation_label": route.get("recommendation_label"),
        "client_visible_notes": route.get("client_visible_notes"),
    }


def safe_offer_segment(segment: dict) -> dict:
    return {
        "id": segment["id"],
        "route_alternative_id": segment.get("route_alternative_id"),
        "sequence": segment.get("sequence"),
        "marketing_airline_code": segment.get("marketing_airline_code"),
        "marketing_airline_name": segment.get("marketing_airline_name"),
        "operating_airline_code": segment.get("operating_airline_code"),
        "operating_airline_name": segment.get("operating_airline_name"),
        "flight_number": segment.get("flight_number"),
        "origin_airport_code": segment.get("origin_airport_code"),
        "origin_city": segment.get("origin_city"),
        "destination_airport_code": segment.get("destination_airport_code"),
        "destination_city": segment.get("destination_city"),
        "departure_datetime": segment.get("departure_datetime"),
        "arrival_datetime": segment.get("arrival_datetime"),
        "aircraft_type": segment.get("aircraft_type"),
        "cabin": segment.get("cabin"),
        "booking_class": segment.get("booking_class"),
        "fare_basis": segment.get("fare_basis"),
        "segment_status": segment.get("segment_status"),
        "baggage_summary": segment.get("baggage_summary"),
    }


def safe_offer_fare_option(fare: dict) -> dict:
    return {
        "id": fare["id"],
        "route_alternative_id": fare.get("route_alternative_id"),
        "sequence": fare.get("sequence"),
        "label": fare.get("label"),
        "branded_fare_name": fare.get("branded_fare_name"),
        "fare_family_code": fare.get("fare_family_code"),
        "status": fare.get("status"),
        "currency": fare.get("currency"),
        "base_fare_amount": fare.get("base_fare_amount"),
        "taxes_amount": fare.get("taxes_amount"),
        "airline_fees_amount": fare.get("airline_fees_amount"),
        "agency_service_fee_amount": fare.get("agency_service_fee_amount"),
        "total_amount": fare.get("total_amount"),
        "refundable_status": fare.get("refundable_status"),
        "changeability_status": fare.get("changeability_status"),
        "baggage_summary": fare.get("baggage_summary"),
        "seat_selection_summary": fare.get("seat_selection_summary"),
        "meal_summary": fare.get("meal_summary"),
        "special_service_summary": fare.get("special_service_summary"),
        "client_visible_notes": fare.get("client_visible_notes"),
        "is_recommended": fare.get("is_recommended"),
    }


def safe_offer_price_line(line: dict) -> dict:
    return {
        "id": line["id"],
        "route_alternative_id": line.get("route_alternative_id"),
        "fare_option_id": line.get("fare_option_id"),
        "line_type": line.get("line_type"),
        "description": line.get("description"),
        "service_code": line.get("service_code"),
        "passenger_id": line.get("passenger_id"),
        "quantity": line.get("quantity"),
        "unit_amount": line.get("unit_amount"),
        "total_amount": line.get("total_amount"),
        "currency": line.get("currency"),
        "supplier_pass_through": line.get("supplier_pass_through"),
    }


def safe_offer_service_check(check: dict) -> dict:
    return {
        "id": check["id"],
        "route_alternative_id": check.get("route_alternative_id"),
        "fare_option_id": check.get("fare_option_id"),
        "passenger_id": check.get("passenger_id"),
        "service_code": check.get("service_code"),
        "service_name": check.get("service_name"),
        "support_status": check.get("support_status"),
        "client_visible_summary": check.get("client_visible_summary"),
        "requires_documents": check.get("requires_documents"),
        "requires_airline_confirmation": check.get("requires_airline_confirmation"),
        "estimated_fee_amount": check.get("estimated_fee_amount"),
        "currency": check.get("currency"),
        "status": check.get("status"),
    }


def safe_booking(booking: dict) -> dict:
    return {
        "id": booking["id"],
        "booking_reference": booking.get("booking_reference"),
        "request_id": booking.get("request_id"),
        "offer_id": booking.get("offer_id"),
        "status": booking.get("status"),
        "pnr": booking.get("pnr"),
        "validating_airline_code": booking.get("validating_airline_code"),
        "booking_channel": booking.get("booking_channel"),
        "currency": booking.get("currency"),
        "total_amount": booking.get("total_amount"),
        "amount_paid": booking.get("amount_paid"),
        "amount_due": booking.get("amount_due"),
        "client_visible_notes": booking.get("client_visible_notes"),
        "booking_snapshot_available": bool(booking.get("booking_snapshot")),
    }


def safe_booking_passenger(passenger: dict) -> dict:
    return {
        "id": passenger["id"],
        "passenger_id": passenger.get("passenger_id"),
        "snapshot_display_name": passenger.get("snapshot_display_name"),
        "snapshot_date_of_birth": passenger.get("snapshot_date_of_birth"),
        "snapshot_passenger_type": passenger.get("snapshot_passenger_type"),
        "is_primary_traveler": passenger.get("is_primary_traveler"),
        "ticket_status": passenger.get("ticket_status"),
    }


def safe_booking_segment(segment: dict) -> dict:
    return {
        "id": segment["id"],
        "sequence": segment.get("sequence"),
        "marketing_airline_code": segment.get("marketing_airline_code"),
        "marketing_airline_name": segment.get("marketing_airline_name"),
        "operating_airline_code": segment.get("operating_airline_code"),
        "operating_airline_name": segment.get("operating_airline_name"),
        "flight_number": segment.get("flight_number"),
        "origin_airport_code": segment.get("origin_airport_code"),
        "origin_city": segment.get("origin_city"),
        "destination_airport_code": segment.get("destination_airport_code"),
        "destination_city": segment.get("destination_city"),
        "departure_datetime": segment.get("departure_datetime"),
        "arrival_datetime": segment.get("arrival_datetime"),
        "aircraft_type": segment.get("aircraft_type"),
        "cabin": segment.get("cabin"),
        "booking_class": segment.get("booking_class"),
        "fare_basis": segment.get("fare_basis"),
        "segment_status": segment.get("segment_status"),
        "baggage_summary": segment.get("baggage_summary"),
    }


def safe_ticket(ticket: dict) -> dict:
    return {
        "id": ticket["id"],
        "passenger_id": ticket.get("passenger_id"),
        "booking_passenger_id": ticket.get("booking_passenger_id"),
        "ticket_number": ticket.get("ticket_number"),
        "validating_airline_code": ticket.get("validating_airline_code"),
        "issue_date": ticket.get("issue_date"),
        "status": ticket.get("status"),
        "base_fare_amount": ticket.get("base_fare_amount"),
        "taxes_amount": ticket.get("taxes_amount"),
        "total_amount": ticket.get("total_amount"),
        "currency": ticket.get("currency"),
        "fare_basis": ticket.get("fare_basis"),
        "coupon_summary": ticket.get("coupon_summary"),
        "client_visible_notes": ticket.get("client_visible_notes"),
    }


def safe_emd(emd: dict) -> dict:
    return {
        "id": emd["id"],
        "passenger_id": emd.get("passenger_id"),
        "booking_passenger_id": emd.get("booking_passenger_id"),
        "ticket_id": emd.get("ticket_id"),
        "service_code": emd.get("service_code"),
        "service_name": emd.get("service_name"),
        "emd_number": emd.get("emd_number"),
        "emd_type": emd.get("emd_type"),
        "rfic_code": emd.get("rfic_code"),
        "rfisc_code": emd.get("rfisc_code"),
        "reason_for_issuance": emd.get("reason_for_issuance"),
        "issue_date": emd.get("issue_date"),
        "status": emd.get("status"),
        "amount": emd.get("amount"),
        "currency": emd.get("currency"),
        "associated_segment_ids": emd.get("associated_segment_ids", []),
        "client_visible_notes": emd.get("client_visible_notes"),
    }


def safe_invoice(invoice: dict) -> dict:
    return {
        "id": invoice["id"],
        "invoice_number": invoice.get("invoice_number"),
        "booking_id": invoice.get("booking_id"),
        "offer_id": invoice.get("offer_id"),
        "status": invoice.get("status"),
        "currency": invoice.get("currency"),
        "subtotal_amount": invoice.get("subtotal_amount"),
        "tax_amount": invoice.get("tax_amount"),
        "total_amount": invoice.get("total_amount"),
        "paid_amount": invoice.get("paid_amount"),
        "due_amount": invoice.get("due_amount"),
        "issue_date": invoice.get("issue_date"),
        "due_date": invoice.get("due_date"),
        "client_visible_notes": invoice.get("client_visible_notes"),
        "issued_at": invoice.get("issued_at"),
        "paid_at": invoice.get("paid_at"),
    }


def safe_payment(payment: dict) -> dict:
    return {
        "id": payment["id"],
        "invoice_id": payment.get("invoice_id"),
        "booking_id": payment.get("booking_id"),
        "status": payment.get("status"),
        "method": payment.get("method"),
        "amount": payment.get("amount"),
        "currency": payment.get("currency"),
        "received_at": payment.get("received_at"),
        "external_reference": payment.get("external_reference"),
    }


def safe_invoice_line_item(line: dict) -> dict:
    return {
        "id": line["id"],
        "booking_id": line.get("booking_id"),
        "ticket_id": line.get("ticket_id"),
        "emd_id": line.get("emd_id"),
        "line_type": line.get("line_type"),
        "description": line.get("description"),
        "service_code": line.get("service_code"),
        "quantity": line.get("quantity"),
        "unit_amount": line.get("unit_amount"),
        "total_amount": line.get("total_amount"),
        "currency": line.get("currency"),
        "supplier_pass_through": line.get("supplier_pass_through"),
        "status": line.get("status"),
    }


def safe_document(document: dict, include_html: bool = False) -> dict:
    result = {
        "id": document["id"],
        "document_type": document.get("document_type"),
        "source_entity_type": document.get("source_entity_type"),
        "source_entity_id": document.get("source_entity_id"),
        "title": document.get("title"),
        "status": document.get("status"),
        "language": document.get("language"),
        "brand_snapshot": document.get("brand_snapshot"),
        "rendered_at": document.get("rendered_at"),
        "client_visible": document.get("client_visible"),
    }
    if include_html:
        result["rendered_html"] = document.get("rendered_html")
    return result


async def visible_request_or_404(db: Database, ctx: dict, request_id: str) -> dict:
    request = await db.collection("travel_requests").find_one({"agency_id": ctx["account"]["agency_id"], "client_id": ctx["account"]["client_id"], "id": request_id})
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portal request not found.")
    return request


async def visible_offer_or_404(db: Database, ctx: dict, offer_id: str) -> dict:
    offer = await db.collection("offers").find_one({"agency_id": ctx["account"]["agency_id"], "client_id": ctx["account"]["client_id"], "id": offer_id})
    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portal offer not found.")
    return offer


async def visible_booking_or_404(db: Database, ctx: dict, booking_id: str) -> dict:
    booking = await db.collection("bookings").find_one({"agency_id": ctx["account"]["agency_id"], "client_id": ctx["account"]["client_id"], "id": booking_id})
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portal booking not found.")
    return booking


async def visible_invoice_or_404(db: Database, ctx: dict, invoice_id: str) -> dict:
    invoice = await db.collection("invoices").find_one({"agency_id": ctx["account"]["agency_id"], "client_id": ctx["account"]["client_id"], "id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portal invoice not found.")
    return invoice


@router.get("/me")
async def me(ctx: dict = Depends(portal_context)) -> dict:
    return {
        "portal_account": ctx["account"],
        "agency": ctx["agency"],
        "client": safe_client(ctx["client"]),
        "brand": ctx["brand"],
        "workspace": {
            "brand_name": ctx["brand"].get("brand_name"),
            "logo_url": ctx["brand"].get("logo_url"),
            "primary_color": ctx["brand"].get("primary_color"),
            "secondary_color": ctx["brand"].get("secondary_color"),
            "font_family": ctx["brand"].get("font_family"),
        },
        "demo_notice": "Read-only portal preview. Development-only demo mapping.",
    }


@router.get("/dashboard")
async def dashboard(ctx: dict = Depends(portal_context), db: Database = Depends(get_database)) -> dict:
    agency_id = ctx["account"]["agency_id"]
    client_id = ctx["account"]["client_id"]
    requests = [safe_request(item) for item in await db.collection("travel_requests").find_many({"agency_id": agency_id, "client_id": client_id})]
    offers = [safe_offer(item) for item in await db.collection("offers").find_many({"agency_id": agency_id, "client_id": client_id})]
    bookings = [safe_booking(item) for item in await db.collection("bookings").find_many({"agency_id": agency_id, "client_id": client_id})]
    documents = [safe_document(item) for item in await db.collection("rendered_documents").find_many({"agency_id": agency_id, "client_id": client_id, "client_visible": True})]
    invoices = [safe_invoice(item) for item in await db.collection("invoices").find_many({"agency_id": agency_id, "client_id": client_id})]
    payments = []
    for invoice in invoices:
        payments.extend([safe_payment(item) for item in await db.collection("payment_records").find_many({"agency_id": agency_id, "invoice_id": invoice["id"]})])
    return {
        "counts": {
            "requests": len(requests),
            "offers": len(offers),
            "bookings": len(bookings),
            "documents": len(documents),
            "invoices": len(invoices),
            "payments": len(payments),
        },
        "latest": {
            "requests": requests[:5],
            "offers": offers[:5],
            "bookings": bookings[:5],
            "documents": documents[:5],
            "invoices": invoices[:5],
            "payments": payments[:5],
        },
    }


@router.get("/profile")
async def profile(ctx: dict = Depends(portal_context)) -> dict:
    return {"client": safe_client(ctx["client"]), "portal_account": ctx["account"], "brand": ctx["brand"]}


@router.get("/passengers")
async def passengers(ctx: dict = Depends(portal_context), db: Database = Depends(get_database)) -> dict:
    relationships = await permitted_relationships(db, ctx)
    passengers_by_id = {item["id"]: item for item in await db.collection("passenger_profiles").find_many({"agency_id": ctx["account"]["agency_id"]})}
    return {"items": [safe_passenger(passengers_by_id[item["passenger_id"]], item) for item in relationships if item["passenger_id"] in passengers_by_id and passengers_by_id[item["passenger_id"]].get("status") != "archived"]}


@router.get("/passengers/{passenger_id}")
async def passenger_detail(passenger_id: str, ctx: dict = Depends(portal_context), db: Database = Depends(get_database)) -> dict:
    relationships = {item["passenger_id"]: item for item in await permitted_relationships(db, ctx)}
    if passenger_id not in relationships:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portal passenger not found.")
    passenger = await db.collection("passenger_profiles").find_one({"agency_id": ctx["account"]["agency_id"], "id": passenger_id})
    if not passenger or passenger.get("status") == "archived":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portal passenger not found.")
    return {"passenger": safe_passenger(passenger, relationships[passenger_id])}


@router.get("/requests")
async def requests(ctx: dict = Depends(portal_context), db: Database = Depends(get_database)) -> dict:
    items = await db.collection("travel_requests").find_many({"agency_id": ctx["account"]["agency_id"], "client_id": ctx["account"]["client_id"]})
    return {"items": [safe_request(item) for item in items]}


@router.get("/requests/{request_id}")
async def request_detail(request_id: str, ctx: dict = Depends(portal_context), db: Database = Depends(get_database)) -> dict:
    request = await visible_request_or_404(db, ctx, request_id)
    permitted = await permitted_passenger_ids(db, ctx)
    passengers = [item for item in await db.collection("request_passengers").find_many({"agency_id": ctx["account"]["agency_id"], "request_id": request_id, "status": "active"}) if item.get("passenger_id") in permitted]
    services = [safe_requested_service(item) for item in await db.collection("requested_services").find_many({"agency_id": ctx["account"]["agency_id"], "request_id": request_id})]
    messages = [safe_request_message(item) for item in await db.collection("request_messages").find_many({"agency_id": ctx["account"]["agency_id"], "request_id": request_id}) if item.get("visibility") == "client_visible"]
    tasks = [safe_request_task(item) for item in await db.collection("request_tasks").find_many({"agency_id": ctx["account"]["agency_id"], "request_id": request_id}) if item.get("visibility") == "client_visible"]
    timeline = [safe_request_timeline_event(item) for item in await db.collection("request_timeline_events").find_many({"agency_id": ctx["account"]["agency_id"], "request_id": request_id}) if item.get("visibility") == "client_visible"]
    return {"request": safe_request(request), "passengers": passengers, "services": services, "messages": messages, "tasks": tasks, "timeline": timeline}


@router.get("/offers")
async def offers(ctx: dict = Depends(portal_context), db: Database = Depends(get_database)) -> dict:
    items = await db.collection("offers").find_many({"agency_id": ctx["account"]["agency_id"], "client_id": ctx["account"]["client_id"]})
    return {"items": [safe_offer(item) for item in items]}


@router.get("/offers/{offer_id}")
async def offer_detail(offer_id: str, ctx: dict = Depends(portal_context), db: Database = Depends(get_database)) -> dict:
    offer = await visible_offer_or_404(db, ctx, offer_id)
    permitted = await permitted_passenger_ids(db, ctx)
    passengers = [safe_offer_passenger(item) for item in await db.collection("offer_passengers").find_many({"agency_id": ctx["account"]["agency_id"], "offer_id": offer_id, "status": "active"}) if not item.get("passenger_id") or item.get("passenger_id") in permitted]
    routes = [safe_offer_route(item) for item in await db.collection("offer_route_alternatives").find_many({"agency_id": ctx["account"]["agency_id"], "offer_id": offer_id})]
    segments = [safe_offer_segment(item) for item in await db.collection("offer_segments").find_many({"agency_id": ctx["account"]["agency_id"], "offer_id": offer_id})]
    fares = [safe_offer_fare_option(item) for item in await db.collection("offer_fare_options").find_many({"agency_id": ctx["account"]["agency_id"], "offer_id": offer_id})]
    price_lines = [safe_offer_price_line(item) for item in await db.collection("offer_price_lines").find_many({"agency_id": ctx["account"]["agency_id"], "offer_id": offer_id, "status": "active"}) if item.get("client_visible", True)]
    service_checks = [safe_offer_service_check(item) for item in await db.collection("offer_service_checks").find_many({"agency_id": ctx["account"]["agency_id"], "offer_id": offer_id, "status": "active"})]
    return {"offer": safe_offer(offer), "passengers": passengers, "routes": routes, "segments": segments, "fare_options": fares, "price_lines": price_lines, "service_checks": service_checks}


@router.get("/bookings")
async def bookings(ctx: dict = Depends(portal_context), db: Database = Depends(get_database)) -> dict:
    items = await db.collection("bookings").find_many({"agency_id": ctx["account"]["agency_id"], "client_id": ctx["account"]["client_id"]})
    return {"items": [safe_booking(item) for item in items]}


@router.get("/bookings/{booking_id}")
async def booking_detail(booking_id: str, ctx: dict = Depends(portal_context), db: Database = Depends(get_database)) -> dict:
    booking = await visible_booking_or_404(db, ctx, booking_id)
    permitted = await permitted_passenger_ids(db, ctx)
    passengers = [safe_booking_passenger(item) for item in await db.collection("booking_passengers").find_many({"agency_id": ctx["account"]["agency_id"], "booking_id": booking_id}) if not item.get("passenger_id") or item.get("passenger_id") in permitted]
    segments = [safe_booking_segment(item) for item in await db.collection("booking_segments").find_many({"agency_id": ctx["account"]["agency_id"], "booking_id": booking_id})]
    tickets = [safe_ticket(item) for item in await db.collection("ticket_records").find_many({"agency_id": ctx["account"]["agency_id"], "booking_id": booking_id}) if not item.get("passenger_id") or item.get("passenger_id") in permitted]
    emds = [safe_emd(item) for item in await db.collection("emd_records").find_many({"agency_id": ctx["account"]["agency_id"], "booking_id": booking_id}) if not item.get("passenger_id") or item.get("passenger_id") in permitted]
    return {"booking": safe_booking(booking), "passengers": passengers, "segments": segments, "tickets": tickets, "emds": emds}


@router.get("/documents")
async def documents(ctx: dict = Depends(portal_context), db: Database = Depends(get_database)) -> dict:
    items = await db.collection("rendered_documents").find_many({"agency_id": ctx["account"]["agency_id"], "client_id": ctx["account"]["client_id"], "client_visible": True})
    return {"items": [safe_document(item) for item in items if item.get("status") != "archived"]}


@router.get("/documents/{document_id}")
async def document_detail(document_id: str, ctx: dict = Depends(portal_context), db: Database = Depends(get_database)) -> dict:
    document = await db.collection("rendered_documents").find_one({"agency_id": ctx["account"]["agency_id"], "client_id": ctx["account"]["client_id"], "client_visible": True, "id": document_id})
    if not document or document.get("status") == "archived":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portal document not found.")
    return {"document": safe_document(document, include_html=True)}


@router.get("/invoices")
async def invoices(ctx: dict = Depends(portal_context), db: Database = Depends(get_database)) -> dict:
    items = await db.collection("invoices").find_many({"agency_id": ctx["account"]["agency_id"], "client_id": ctx["account"]["client_id"]})
    return {"items": [safe_invoice(item) for item in items]}


@router.get("/invoices/{invoice_id}")
async def invoice_detail(invoice_id: str, ctx: dict = Depends(portal_context), db: Database = Depends(get_database)) -> dict:
    invoice = await visible_invoice_or_404(db, ctx, invoice_id)
    lines = [safe_invoice_line_item(item) for item in await db.collection("invoice_line_items").find_many({"agency_id": ctx["account"]["agency_id"], "invoice_id": invoice_id}) if item.get("client_visible", True)]
    payments = [safe_payment(item) for item in await db.collection("payment_records").find_many({"agency_id": ctx["account"]["agency_id"], "invoice_id": invoice_id})]
    return {"invoice": safe_invoice(invoice), "line_items": lines, "payments": payments}


@router.get("/payments")
async def payments(ctx: dict = Depends(portal_context), db: Database = Depends(get_database)) -> dict:
    invoices = await db.collection("invoices").find_many({"agency_id": ctx["account"]["agency_id"], "client_id": ctx["account"]["client_id"]})
    invoice_ids = {item["id"] for item in invoices}
    items = await db.collection("payment_records").find_many({"agency_id": ctx["account"]["agency_id"]})
    return {"items": [safe_payment(item) for item in items if item.get("invoice_id") in invoice_ids]}
