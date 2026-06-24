from datetime import date, datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException, status

from database import Database
from models import (
    AuditEvent,
    ClientPassengerRelationship,
    ClientProfile,
    PassengerProfile,
    RequestIntake,
    RequestPassenger,
    RequestSegment,
    RequestTimelineEvent,
    RequestedService,
    TravelRequest,
)


SERVICE_LABELS = {
    "mobility_assistance": "Mobility assistance",
    "medical_travel": "Medical travel",
    "pet_travel": "Pet travel",
    "child_or_unaccompanied_minor": "Child / unaccompanied minor",
    "special_baggage": "Special baggage",
    "documents_or_visa": "Documents / visa",
    "disruption_or_claims": "Disruption / claims",
    "booking_or_planning": "Booking / planning",
    "other": "Other assistance",
}


async def write_audit(
    db: Database,
    agency_id: Optional[str],
    actor_user_id: Optional[str],
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


async def write_timeline(
    db: Database,
    agency_id: str,
    request_id: str,
    actor_user_id: Optional[str],
    event_type: str,
    title: str,
    summary: Optional[str] = None,
    metadata: dict | None = None,
) -> None:
    event = RequestTimelineEvent(
        agency_id=agency_id,
        request_id=request_id,
        actor_user_id=actor_user_id,
        event_type=event_type,
        title=title,
        summary=summary,
        visibility="internal",
        metadata=metadata or {},
    )
    await db.collection("request_timeline_events").insert_one(event.model_dump(mode="json"))


async def default_agency_context(db: Database) -> dict:
    agencies = await db.collection("agencies").find_many()
    active_agencies = [agency for agency in agencies if agency.get("status") != "archived"]
    if len(active_agencies) != 1:
        return {"agency_id": None, "workspace_id": None}
    agency = active_agencies[0]
    workspaces = await db.collection("agency_workspaces").find_many({"agency_id": agency["id"]})
    active_workspaces = [workspace for workspace in workspaces if workspace.get("status") == "active"]
    return {"agency_id": agency["id"], "workspace_id": active_workspaces[0]["id"] if len(active_workspaces) == 1 else None}


async def next_intake_reference(db: Database) -> str:
    count = await db.collection("request_intakes").count()
    return f"INT-{count + 1:05d}"


async def create_intake(
    db: Database,
    *,
    source: str,
    contact: dict,
    travel: dict,
    services: dict,
    request_details: Optional[str] = None,
    agency_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
    priority: str = "normal",
    assigned_to: Optional[str] = None,
    triage_notes: Optional[str] = None,
    internal_notes: Optional[str] = None,
    client_visible_notes: Optional[str] = None,
    raw_payload: Optional[dict] = None,
    actor_user_id: Optional[str] = None,
) -> dict:
    if not agency_id:
        default_context = await default_agency_context(db)
        agency_id = default_context["agency_id"]
        workspace_id = workspace_id or default_context["workspace_id"]
    canonical_payload = {
        "contact": contact,
        "travel": travel,
        "services": services,
        "request_details": request_details,
    }
    intake = RequestIntake(
        agency_id=agency_id,
        workspace_id=workspace_id,
        reference_code=await next_intake_reference(db),
        source=source,
        contact_snapshot=contact,
        travel_summary=travel,
        service_summary=services,
        canonical_payload=canonical_payload,
        raw_payload=raw_payload or canonical_payload,
        priority=priority,
        assigned_to=assigned_to,
        triage_notes=triage_notes,
        internal_notes=internal_notes,
        client_visible_notes=client_visible_notes,
    )
    created = await db.collection("request_intakes").insert_one(intake.model_dump(mode="json"))
    await write_audit(db, agency_id, actor_user_id, "intake_created", "request_intake", created["id"], "Created request intake.", {"reference_code": created["reference_code"], "source": source})
    return created


async def next_request_reference(db: Database, agency_id: str) -> str:
    count = await db.collection("travel_requests").count({"agency_id": agency_id})
    return f"REQ-{count + 1:05d}"


def compact_text(value: Any, limit: int = 1000) -> Optional[str]:
    if value is None:
        return None
    text = " ".join(str(value).split())
    return text[:limit] if text else None


def service_names(service_summary: dict) -> list[str]:
    selected = [compact_text(item, 80) for item in service_summary.get("selected_service_categories", [])]
    selected = [item for item in selected if item]
    flags = [label for key, label in SERVICE_LABELS.items() if service_summary.get(key)]
    names = list(dict.fromkeys([*selected, *flags]))
    other_details = compact_text(service_summary.get("other_details"), 240)
    if other_details and "Other assistance" not in names:
        names.append("Other assistance")
    return names


def normalize_intake_payload(intake: dict) -> dict:
    contact = intake.get("contact_snapshot") or {}
    travel = intake.get("travel_summary") or {}
    services = intake.get("service_summary") or {}
    route_parts = [compact_text(travel.get("origin"), 120), compact_text(travel.get("destination"), 120)]
    route_summary = " → ".join([part for part in route_parts if part])
    service_list = service_names(services)
    return {
        "client": {
            "display_name": compact_text(contact.get("name"), 160),
            "email": contact.get("email"),
            "phone": compact_text(contact.get("phone"), 80),
            "organization": compact_text(contact.get("organization"), 160),
            "marketing_consent": bool(contact.get("marketing_consent")),
            "data_processing_consent": bool(contact.get("data_processing_consent") or contact.get("privacy_policy_accepted")),
        },
        "travel": {
            "route_summary": route_summary or compact_text(travel.get("itinerary_notes"), 240),
            "origin": compact_text(travel.get("origin"), 120),
            "destination": compact_text(travel.get("destination"), 120),
            "departure_date": travel.get("departure_date"),
            "return_date": travel.get("return_date"),
            "passenger_count": max(int(travel.get("passenger_count") or 1), 1),
            "itinerary_notes": compact_text(travel.get("itinerary_notes"), 2000),
        },
        "services": service_list,
        "request_details": compact_text((intake.get("canonical_payload") or {}).get("request_details"), 3000),
    }


def validate_conversion(intake: dict, normalized: dict) -> None:
    if not intake.get("agency_id"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assign intake to an agency before conversion.")
    client = normalized["client"]
    if not client.get("display_name"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Client name is required before conversion.")
    travel = normalized["travel"]
    if not (travel.get("route_summary") or travel.get("itinerary_notes")):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Route summary or travel details are required before conversion.")
    if not (normalized["services"] or normalized.get("request_details")):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one service category or request detail is required before conversion.")


async def find_or_create_client(db: Database, intake: dict, normalized: dict, actor_user_id: str) -> dict:
    agency_id = intake["agency_id"]
    client_data = normalized["client"]
    email = client_data.get("email") or f"intake-{intake['id']}@client.aeroassist.local"
    existing = await db.collection("client_profiles").find_one({"agency_id": agency_id, "primary_email": email})
    if existing:
        return existing
    client = ClientProfile(
        agency_id=agency_id,
        display_name=client_data["display_name"],
        legal_name=client_data.get("organization"),
        primary_email=email,
        primary_phone=client_data.get("phone"),
        marketing_consent=client_data.get("marketing_consent", False),
        data_processing_consent=client_data.get("data_processing_consent", False),
        internal_notes=f"Created from request intake {intake['reference_code']}.",
    )
    created = await db.collection("client_profiles").insert_one(client.model_dump(mode="json"))
    await write_audit(db, agency_id, actor_user_id, "client.created_from_intake", "client_profile", created["id"], "Created client from request intake.", {"intake_id": intake["id"]})
    return created


async def convert_intake(db: Database, intake_id: str, actor_user_id: str) -> dict:
    intake = await db.collection("request_intakes").find_one({"id": intake_id})
    if not intake:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request intake not found.")
    if intake.get("converted_request_id"):
        request = await db.collection("travel_requests").find_one({"id": intake["converted_request_id"]})
        return {"intake": intake, "request": request, "already_converted": True}
    if intake.get("status") in {"rejected", "duplicate", "archived"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Cannot convert intake with status {intake.get('status')}.")

    normalized = normalize_intake_payload(intake)
    validate_conversion(intake, normalized)
    await db.collection("request_intakes").update_one({"id": intake_id}, {"normalized_payload": normalized})
    client = await find_or_create_client(db, intake, normalized, actor_user_id)
    travel = normalized["travel"]
    services = normalized["services"]
    title = f"{normalized['client']['display_name']} request"
    if travel.get("route_summary"):
        title = f"{normalized['client']['display_name']} · {travel['route_summary']}"
    notes = "\n\n".join([item for item in [travel.get("itinerary_notes"), normalized.get("request_details"), intake.get("internal_notes")] if item])
    request = TravelRequest(
        agency_id=intake["agency_id"],
        client_id=client["id"],
        created_by_user_id=actor_user_id,
        request_reference=await next_request_reference(db, intake["agency_id"]),
        title=title[:180],
        status="triage",
        priority=intake.get("priority") or "normal",
        source=intake.get("source") if intake.get("source") in {"client_portal", "staff_created", "imported", "internal", "public_website"} else "website_form",
        requested_departure_date=travel.get("departure_date"),
        requested_return_date=travel.get("return_date"),
        trip_type="round_trip" if travel.get("return_date") else "unknown",
        route_summary=travel.get("route_summary"),
        service_summary="; ".join(services) if services else normalized.get("request_details"),
        passenger_count=travel.get("passenger_count", 1),
        service_count=len(services),
        client_notes=normalized.get("request_details"),
        internal_notes=notes or None,
        client_visible_notes=intake.get("client_visible_notes") or "Received by AeroAssist. Staff review is required before any offer or booking action.",
        assigned_user_id=intake.get("assigned_to"),
        source_intake_id=intake["id"],
        intake_payload_snapshot={
            "reference_code": intake.get("reference_code"),
            "contact_snapshot": intake.get("contact_snapshot"),
            "travel_summary": intake.get("travel_summary"),
            "service_summary": intake.get("service_summary"),
            "canonical_payload": intake.get("canonical_payload"),
            "raw_payload": intake.get("raw_payload"),
        },
    )
    created_request = await db.collection("travel_requests").insert_one(request.model_dump(mode="json"))

    request_passengers = []
    for index in range(travel.get("passenger_count", 1)):
        passenger = PassengerProfile(
            agency_id=intake["agency_id"],
            first_name=f"Passenger {index + 1}",
            last_name="Details pending",
            display_name=f"Passenger {index + 1} details pending",
            date_of_birth=date(1900, 1, 1),
            passenger_type="ADT",
            travel_document_notes="Created as a placeholder from request intake conversion.",
        )
        passenger_doc = await db.collection("passenger_profiles").insert_one(passenger.model_dump(mode="json"))
        relationship = ClientPassengerRelationship(
            agency_id=intake["agency_id"],
            client_id=client["id"],
            passenger_id=passenger_doc["id"],
            relationship_type="self" if index == 0 else "other",
            can_request_travel=True,
            notes=f"Placeholder created from intake {intake.get('reference_code')}.",
        )
        relationship_doc = await db.collection("client_passenger_relationships").insert_one(relationship.model_dump(mode="json"))
        request_passenger = RequestPassenger(
            agency_id=intake["agency_id"],
            request_id=created_request["id"],
            passenger_id=passenger_doc["id"],
            client_passenger_relationship_id=relationship_doc["id"],
            role_in_request="traveler",
            is_primary_traveler=index == 0,
            service_needs_summary=normalized.get("request_details"),
            snapshot_display_name=passenger_doc["display_name"],
            snapshot_date_of_birth=passenger_doc["date_of_birth"],
            snapshot_passenger_type=passenger_doc["passenger_type"],
        )
        request_passengers.append(await db.collection("request_passengers").insert_one(request_passenger.model_dump(mode="json")))

    request_segment_ids = []
    if travel.get("origin") and travel.get("destination"):
        segment = RequestSegment(
            agency_id=intake["agency_id"],
            request_id=created_request["id"],
            sequence=1,
            origin_text=travel["origin"],
            destination_text=travel["destination"],
            departure_date=travel.get("departure_date"),
            notes=travel.get("itinerary_notes"),
        )
        segment_doc = await db.collection("request_segments").insert_one(segment.model_dump(mode="json"))
        request_segment_ids.append(segment_doc["id"])

    for service_name in services:
        service = RequestedService(
            agency_id=intake["agency_id"],
            request_id=created_request["id"],
            service_code=service_name.upper().replace(" ", "_").replace("/", "_")[:32],
            service_name=service_name,
            service_category="intake",
            details=normalized.get("request_details"),
            detail_payload={
                "source": "request_intake",
                "intake_reference": intake.get("reference_code"),
                "request_details": normalized.get("request_details"),
            },
            passenger_ids=[item["passenger_id"] for item in request_passengers],
            segment_ids=request_segment_ids,
            applies_to_all_passengers=True,
            applies_to_all_segments=True,
            client_visible_summary=service_name,
        )
        await db.collection("requested_services").insert_one(service.model_dump(mode="json"))

    created_request = await db.collection("travel_requests").update_one(
        {"agency_id": intake["agency_id"], "id": created_request["id"]},
        {"passenger_count": len(request_passengers), "service_count": len(services)},
    )

    converted_at = datetime.now(timezone.utc)
    updated_intake = await db.collection("request_intakes").update_one(
        {"id": intake_id},
        {
            "status": "converted",
            "normalized_payload": normalized,
            "converted_request_id": created_request["id"],
            "converted_at": converted_at,
            "converted_by": actor_user_id,
        },
    )
    await write_audit(db, intake["agency_id"], actor_user_id, "intake_converted", "request_intake", intake_id, "Converted intake to operational request.", {"request_id": created_request["id"]})
    await write_audit(db, intake["agency_id"], actor_user_id, "request.created_from_intake", "travel_request", created_request["id"], "Created operational request from intake.", {"intake_id": intake_id})
    await write_timeline(db, intake["agency_id"], created_request["id"], actor_user_id, "intake_converted", "Request created from intake", intake.get("reference_code"), {"intake_id": intake_id})
    return {"intake": updated_intake, "request": created_request, "already_converted": False}
