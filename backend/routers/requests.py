from datetime import date, datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    AuditEvent,
    ClientPassengerRelationship,
    ClientProfile,
    OperationalRequestBuilderCreate,
    PassengerProfile,
    RequestMessage,
    RequestMessageCreate,
    RequestPassenger,
    RequestPassengerCreate,
    RequestPassengerUpdate,
    RequestSegment,
    RequestSegmentCreate,
    RequestSegmentUpdate,
    RequestStatusUpdate,
    RequestTask,
    RequestTaskCreate,
    RequestTaskUpdate,
    RequestTimelineEvent,
    RequestedService,
    RequestedServiceCreate,
    RequestedServiceUpdate,
    TravelRequest,
    TravelRequestCreate,
    TravelRequestUpdate,
)
from services.tenant_service import assert_agency_access, require_any_agency_role

router = APIRouter(prefix="/api/agencies/{agency_id}", tags=["requests"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin", "agency_agent"]


def clean_updates(payload: Any) -> dict:
    return payload.model_dump(exclude_unset=True, mode="json")


def matches_search(record: dict, search: Optional[str]) -> bool:
    if not search:
        return True
    needle = search.lower()
    fields = ["request_reference", "title", "route_summary", "service_summary", "client_notes", "internal_notes"]
    return any(needle in str(record.get(field) or "").lower() for field in fields)


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


async def require_write(db: Database, agency_id: str, user: dict) -> None:
    if user.get("global_role") not in {"platform_owner", "platform_admin"}:
        await require_any_agency_role(db, agency_id, user, WRITE_ROLES)


async def write_audit(db: Database, agency_id: str, actor_user_id: str, event_type: str, entity_type: str, entity_id: str, summary: str, metadata: dict | None = None) -> None:
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


async def write_timeline(db: Database, agency_id: str, request_id: str, actor_user_id: str | None, event_type: str, title: str, summary: str | None = None, visibility: str = "internal", metadata: dict | None = None) -> dict:
    event = RequestTimelineEvent(
        agency_id=agency_id,
        request_id=request_id,
        actor_user_id=actor_user_id,
        event_type=event_type,
        title=title,
        summary=summary,
        visibility=visibility,
        metadata=metadata or {},
    )
    return await db.collection("request_timeline_events").insert_one(event.model_dump(mode="json"))


async def get_request_or_404(db: Database, agency_id: str, request_id: str) -> dict:
    request = await db.collection("travel_requests").find_one({"agency_id": agency_id, "id": request_id})
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.")
    return request


async def get_client_or_404(db: Database, agency_id: str, client_id: str) -> dict:
    client = await db.collection("client_profiles").find_one({"agency_id": agency_id, "id": client_id})
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")
    return client


async def get_passenger_or_404(db: Database, agency_id: str, passenger_id: str) -> dict:
    passenger = await db.collection("passenger_profiles").find_one({"agency_id": agency_id, "id": passenger_id})
    if passenger is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Passenger not found.")
    return passenger


async def update_counts(db: Database, agency_id: str, request_id: str) -> dict:
    passenger_count = await db.collection("request_passengers").count({"agency_id": agency_id, "request_id": request_id, "status": "active"})
    services = await db.collection("requested_services").find_many({"agency_id": agency_id, "request_id": request_id})
    service_count = len([service for service in services if service.get("status") != "cancelled"])
    return await db.collection("travel_requests").update_one(
        {"agency_id": agency_id, "id": request_id},
        {"passenger_count": passenger_count, "service_count": service_count},
    )


async def next_reference(db: Database, agency_id: str) -> str:
    count = await db.collection("travel_requests").count({"agency_id": agency_id})
    return f"REQ-{count + 1:05d}"


def compact_text(value: Any, limit: int = 1000) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).split())
    return text[:limit] if text else None


PASSENGER_TYPE_MAP = {
    "adult": "ADT",
    "child": "CHD",
    "infant": "INF",
    "senior": "SRC",
    "unaccompanied_minor": "UMNR",
    "ADT": "ADT",
    "CHD": "CHD",
    "INF": "INF",
    "SRC": "SRC",
    "UMNR": "UMNR",
}


SERVICE_LABELS = {
    "mobility_assistance": "Mobility assistance",
    "medical_travel": "Medical travel",
    "pet_travel": "Pet travel",
    "unaccompanied_minor": "Unaccompanied minor",
    "child_travel_support": "Child travel support",
    "special_baggage": "Special baggage",
    "sports_equipment": "Sports equipment",
    "documents_visa": "Documents / visa",
    "booking_planning": "Booking / planning",
    "disruption_support": "Disruption support",
    "refund_exchange": "Refund / exchange",
    "claims_support": "Claims support",
    "airport_assistance": "Airport assistance",
    "other": "Other assistance",
}


async def create_inline_client(db: Database, agency_id: str, payload) -> dict:
    if payload.client_id:
        return await get_client_or_404(db, agency_id, payload.client_id)
    name = compact_text(payload.name, 160)
    phone = compact_text(payload.phone, 80)
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Client name is required.")
    if not payload.email and not phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Client email or phone is required.")
    email = payload.email or f"client-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}@client.aeroassist.local"
    existing = await db.collection("client_profiles").find_one({"agency_id": agency_id, "primary_email": email})
    if existing:
        return existing
    client = ClientProfile(
        agency_id=agency_id,
        display_name=name,
        legal_name=compact_text(payload.organization, 160),
        primary_email=email,
        primary_phone=phone,
        internal_notes=compact_text(payload.notes, 2000),
    )
    return await db.collection("client_profiles").insert_one(client.model_dump(mode="json"))


async def create_inline_passenger(db: Database, agency_id: str, client_id: str, payload, index: int) -> dict:
    if payload.passenger_id:
        passenger = await get_passenger_or_404(db, agency_id, payload.passenger_id)
    else:
        display_name = compact_text(payload.display_name, 160)
        first_name = compact_text(payload.first_name, 80)
        last_name = compact_text(payload.last_name, 80)
        if not display_name and not first_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passenger first name or display name is required.")
        if not display_name:
            display_name = " ".join([part for part in [first_name, last_name] if part])
        passenger = PassengerProfile(
            agency_id=agency_id,
            first_name=first_name or display_name.split(" ", 1)[0],
            last_name=last_name or "Unknown",
            display_name=display_name,
            date_of_birth=payload.date_of_birth or date(1900, 1, 1),
            passenger_type=PASSENGER_TYPE_MAP.get(payload.passenger_type, "OTHER"),
            known_assistance_needs=compact_text(payload.mobility_notes or payload.notes, 2000),
            medical_notes_internal=compact_text(payload.medical_notes, 2000),
            travel_document_notes=compact_text(payload.notes, 2000),
        )
        passenger = await db.collection("passenger_profiles").insert_one(passenger.model_dump(mode="json"))
    relationship = await db.collection("client_passenger_relationships").find_one({"agency_id": agency_id, "client_id": client_id, "passenger_id": passenger["id"]})
    if not relationship:
        relationship = await db.collection("client_passenger_relationships").insert_one(
            ClientPassengerRelationship(
                agency_id=agency_id,
                client_id=client_id,
                passenger_id=passenger["id"],
                relationship_type="self" if index == 0 else "other",
                can_request_travel=True,
                notes="Created from Operational Request Builder V1.",
            ).model_dump(mode="json")
        )
    return {"passenger": passenger, "relationship": relationship}


def route_summary_from_payload(payload: OperationalRequestBuilderCreate) -> str | None:
    if payload.origin and payload.destination:
        return f"{payload.origin} → {payload.destination}"
    first_segment = payload.segments[0] if payload.segments else None
    if first_segment:
        return f"{first_segment.origin_text} → {first_segment.destination_text}"
    return compact_text(payload.route_notes, 240)


def generated_request_title(client: dict, route_summary: str | None, service_summary: str | None) -> str:
    parts = [client.get("display_name") or "Client request"]
    if route_summary:
        parts.append(route_summary)
    elif service_summary:
        parts.append(service_summary)
    return " · ".join(parts)[:180]


def service_code_for(category: str) -> str:
    return category.upper()[:32]


@router.post("/requests/builder", status_code=status.HTTP_201_CREATED)
async def create_request_from_builder(
    agency_id: str,
    payload: OperationalRequestBuilderCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    for service in payload.services:
        if service.category == "mobility_assistance" and service.details.get("assessment_version") == "v2_assessment_driven":
            suggested = service.details.get("suggested_ssr_code")
            confirmed = service.details.get("confirmed_ssr_code")
            if suggested and confirmed and confirmed != suggested and not service.details.get("override_reason"):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mobility SSR override reason is required when confirmed code differs from suggested code.")
    client = await create_inline_client(db, agency_id, payload.client)
    route_summary = route_summary_from_payload(payload)
    service_labels = [SERVICE_LABELS.get(service.category, service.category.replace("_", " ")) for service in payload.services]
    service_summary = "; ".join(service_labels) if service_labels else None
    request = TravelRequest(
        agency_id=agency_id,
        client_id=client["id"],
        created_by_user_id=user["id"],
        request_reference=await next_reference(db, agency_id),
        title=compact_text(payload.title, 180) or generated_request_title(client, route_summary, service_summary),
        status=payload.status,
        priority=payload.priority,
        source=payload.source,
        trip_type=payload.trip_type,
        requested_departure_date=payload.departure_date or (payload.segments[0].departure_date if payload.segments else None),
        requested_return_date=payload.return_date,
        route_summary=route_summary,
        service_summary=service_summary,
        urgency_reason=None,
        client_notes=compact_text(payload.route_notes, 2000),
        internal_notes=compact_text(payload.internal_notes, 4000),
        client_visible_notes=compact_text(payload.client_visible_notes, 2000),
        builder_payload_snapshot=payload.model_dump(mode="json"),
    )
    created_request = await db.collection("travel_requests").insert_one(request.model_dump(mode="json"))

    request_passengers = []
    passenger_id_map: dict[str, str] = {}
    for index, passenger_payload in enumerate(payload.passengers):
        resolved = await create_inline_passenger(db, agency_id, client["id"], passenger_payload, index)
        passenger = resolved["passenger"]
        relationship = resolved["relationship"]
        passenger_id_map[passenger_payload.passenger_id or f"inline-{index}"] = passenger["id"]
        request_passenger = RequestPassenger(
            agency_id=agency_id,
            request_id=created_request["id"],
            passenger_id=passenger["id"],
            client_passenger_relationship_id=relationship["id"],
            role_in_request="traveler",
            is_primary_traveler=index == 0,
            service_needs_summary=compact_text(passenger_payload.mobility_notes or passenger_payload.medical_notes or passenger_payload.notes, 1000),
            snapshot_display_name=passenger["display_name"],
            snapshot_date_of_birth=passenger["date_of_birth"],
            snapshot_passenger_type=passenger["passenger_type"],
        )
        request_passengers.append(await db.collection("request_passengers").insert_one(request_passenger.model_dump(mode="json")))

    request_segments = []
    segment_id_map: dict[str, str] = {}
    segments = payload.segments or (
        [
            {
                "sequence": 1,
                "origin_text": payload.origin,
                "destination_text": payload.destination,
                "departure_date": payload.departure_date,
                "notes": payload.route_notes,
            }
        ]
        if payload.origin and payload.destination
        else []
    )
    for index, segment_payload in enumerate(segments):
        segment_data = segment_payload if isinstance(segment_payload, dict) else segment_payload.model_dump(mode="json")
        segment = RequestSegment(
            agency_id=agency_id,
            request_id=created_request["id"],
            sequence=segment_data.get("sequence") or index + 1,
            origin_text=segment_data["origin_text"],
            destination_text=segment_data["destination_text"],
            departure_date=segment_data.get("departure_date"),
            departure_time_window=segment_data.get("departure_time_window"),
            arrival_date=segment_data.get("arrival_date"),
            arrival_time_window=segment_data.get("arrival_time_window"),
            marketing_airline=segment_data.get("marketing_airline"),
            operating_airline=segment_data.get("operating_airline"),
            preferred_airline_code=segment_data.get("marketing_airline"),
            preferred_flight_number=segment_data.get("flight_number"),
            cabin_preference=segment_data.get("cabin_preference"),
            notes=segment_data.get("notes"),
        )
        created_segment = await db.collection("request_segments").insert_one(segment.model_dump(mode="json"))
        request_segments.append(created_segment)
        segment_id_map[str(segment_data.get("sequence") or index + 1)] = created_segment["id"]

    requested_services = []
    all_passenger_ids = [item["passenger_id"] for item in request_passengers]
    all_segment_ids = [item["id"] for item in request_segments]
    for service_payload in payload.services:
        passenger_ids = service_payload.passenger_ids or (all_passenger_ids if service_payload.applies_to_all_passengers else [])
        segment_ids = service_payload.segment_ids or (all_segment_ids if service_payload.applies_to_all_segments else [])
        label = SERVICE_LABELS.get(service_payload.category, service_payload.category.replace("_", " "))
        service = RequestedService(
            agency_id=agency_id,
            request_id=created_request["id"],
            service_code=service_code_for(service_payload.category),
            service_name=label,
            service_category=service_payload.category,
            details=compact_text(service_payload.notes, 2000),
            detail_payload=service_payload.details,
            passenger_ids=passenger_ids,
            segment_ids=segment_ids,
            applies_to_all_passengers=service_payload.applies_to_all_passengers,
            applies_to_all_segments=service_payload.applies_to_all_segments,
            client_visible_summary=label,
        )
        requested_services.append(await db.collection("requested_services").insert_one(service.model_dump(mode="json")))

    updated_request = await update_counts(db, agency_id, created_request["id"])
    await write_audit(db, agency_id, user["id"], "request.builder_created", "travel_request", created_request["id"], f"Created structured request {created_request['request_reference']}.", {"passengers": len(request_passengers), "segments": len(request_segments), "services": len(requested_services)})
    await write_timeline(db, agency_id, created_request["id"], user["id"], "request.builder_created", "Operational request builder completed", service_summary)
    return {
        "request": updated_request,
        "client": client,
        "passengers": request_passengers,
        "segments": request_segments,
        "services": requested_services,
    }


@router.get("/requests")
async def list_requests(
    agency_id: str,
    search: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    priority: Optional[str] = None,
    source: Optional[str] = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    filters = {"agency_id": agency_id}
    if status_filter:
        filters["status"] = status_filter
    if priority:
        filters["priority"] = priority
    if source:
        filters["source"] = source
    items = [item for item in await db.collection("travel_requests").find_many(filters) if matches_search(item, search)]
    clients = {client["id"]: client for client in await db.collection("client_profiles").find_many({"agency_id": agency_id})}
    items.sort(key=lambda item: str(item.get("updated_at") or ""), reverse=True)
    return {"items": [{**item, "client": clients.get(item["client_id"])} for item in items]}


@router.post("/requests", status_code=status.HTTP_201_CREATED)
async def create_request(
    agency_id: str,
    payload: TravelRequestCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    await get_client_or_404(db, agency_id, payload.client_id)
    request = TravelRequest(
        agency_id=agency_id,
        created_by_user_id=user["id"],
        request_reference=await next_reference(db, agency_id),
        **payload.model_dump(mode="json"),
    )
    created = await db.collection("travel_requests").insert_one(request.model_dump(mode="json"))
    await write_audit(db, agency_id, user["id"], "request.created", "travel_request", request.id, f"Created request {request.request_reference}.")
    await write_timeline(db, agency_id, request.id, user["id"], "request.created", "Request created", request.title)
    return {"request": created}


@router.get("/requests/{request_id}")
async def get_request(agency_id: str, request_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    request = await get_request_or_404(db, agency_id, request_id)
    client = await get_client_or_404(db, agency_id, request["client_id"])
    return {
        "request": request,
        "client": client,
        "passengers": await db.collection("request_passengers").find_many({"agency_id": agency_id, "request_id": request_id, "status": "active"}),
        "segments": await db.collection("request_segments").find_many({"agency_id": agency_id, "request_id": request_id, "status": "active"}),
        "services": await db.collection("requested_services").find_many({"agency_id": agency_id, "request_id": request_id}),
        "messages": await db.collection("request_messages").find_many({"agency_id": agency_id, "request_id": request_id}),
        "tasks": await db.collection("request_tasks").find_many({"agency_id": agency_id, "request_id": request_id}),
        "timeline": await db.collection("request_timeline_events").find_many({"agency_id": agency_id, "request_id": request_id}),
    }


@router.put("/requests/{request_id}")
async def update_request(agency_id: str, request_id: str, payload: TravelRequestUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_request_or_404(db, agency_id, request_id)
    updates = clean_updates(payload)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided.")
    if updates.get("status") in {"closed", "cancelled"}:
        updates["closed_at"] = datetime.now(timezone.utc)
    updated = await db.collection("travel_requests").update_one({"agency_id": agency_id, "id": request_id}, updates)
    await write_audit(db, agency_id, user["id"], "request.updated", "travel_request", request_id, "Updated request.", {"fields": sorted(updates.keys())})
    await write_timeline(db, agency_id, request_id, user["id"], "request.updated", "Request updated", ", ".join(sorted(updates.keys())))
    return {"request": updated}


@router.post("/requests/{request_id}/archive")
async def archive_request(agency_id: str, request_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_request_or_404(db, agency_id, request_id)
    updated = await db.collection("travel_requests").update_one({"agency_id": agency_id, "id": request_id}, {"status": "archived"})
    await write_audit(db, agency_id, user["id"], "request.archived", "travel_request", request_id, "Archived request.")
    await write_timeline(db, agency_id, request_id, user["id"], "request.archived", "Request archived")
    return {"request": updated}


@router.post("/requests/{request_id}/restore")
async def restore_request(agency_id: str, request_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_request_or_404(db, agency_id, request_id)
    updated = await db.collection("travel_requests").update_one({"agency_id": agency_id, "id": request_id}, {"status": "triage", "closed_at": None})
    await write_audit(db, agency_id, user["id"], "request.restored", "travel_request", request_id, "Restored request.")
    await write_timeline(db, agency_id, request_id, user["id"], "request.restored", "Request restored")
    return {"request": updated}


@router.post("/requests/{request_id}/status")
async def change_status(agency_id: str, request_id: str, payload: RequestStatusUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_request_or_404(db, agency_id, request_id)
    updates = {"status": payload.status}
    if payload.status in {"closed", "cancelled"}:
        updates["closed_at"] = datetime.now(timezone.utc)
    updated = await db.collection("travel_requests").update_one({"agency_id": agency_id, "id": request_id}, updates)
    await write_audit(db, agency_id, user["id"], "request.status_changed", "travel_request", request_id, f"Changed request status to {payload.status}.")
    await write_timeline(db, agency_id, request_id, user["id"], "request.status_changed", "Request status changed", payload.summary or str(payload.status), "client_visible")
    return {"request": updated}


@router.get("/requests/{request_id}/passengers")
async def list_request_passengers(agency_id: str, request_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    await get_request_or_404(db, agency_id, request_id)
    return {"items": await db.collection("request_passengers").find_many({"agency_id": agency_id, "request_id": request_id, "status": "active"})}


@router.post("/requests/{request_id}/passengers", status_code=status.HTTP_201_CREATED)
async def add_request_passenger(agency_id: str, request_id: str, payload: RequestPassengerCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    request = await get_request_or_404(db, agency_id, request_id)
    passenger = await get_passenger_or_404(db, agency_id, payload.passenger_id)
    if payload.client_passenger_relationship_id:
        relationship = await db.collection("client_passenger_relationships").find_one({"agency_id": agency_id, "id": payload.client_passenger_relationship_id})
        if not relationship or relationship["client_id"] != request["client_id"] or relationship["passenger_id"] != payload.passenger_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Relationship must connect request client and passenger.")
    existing = await db.collection("request_passengers").find_one({"agency_id": agency_id, "request_id": request_id, "passenger_id": payload.passenger_id, "status": "active"})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Passenger already linked to request.")
    item = RequestPassenger(
        agency_id=agency_id,
        request_id=request_id,
        snapshot_display_name=passenger["display_name"],
        snapshot_date_of_birth=passenger["date_of_birth"],
        snapshot_passenger_type=passenger["passenger_type"],
        **payload.model_dump(mode="json"),
    )
    created = await db.collection("request_passengers").insert_one(item.model_dump(mode="json"))
    request = await update_counts(db, agency_id, request_id)
    await write_audit(db, agency_id, user["id"], "request.passenger_added", "request_passenger", item.id, "Added passenger to request.")
    await write_timeline(db, agency_id, request_id, user["id"], "request.passenger_added", "Passenger added", passenger["display_name"])
    return {"request_passenger": created, "request": request}


@router.put("/requests/{request_id}/passengers/{request_passenger_id}")
async def update_request_passenger(agency_id: str, request_id: str, request_passenger_id: str, payload: RequestPassengerUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_request_or_404(db, agency_id, request_id)
    updates = clean_updates(payload)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided.")
    item = await db.collection("request_passengers").update_one({"agency_id": agency_id, "request_id": request_id, "id": request_passenger_id}, updates)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request passenger not found.")
    await write_timeline(db, agency_id, request_id, user["id"], "request.passenger_updated", "Request passenger updated")
    return {"request_passenger": item}


@router.post("/requests/{request_id}/passengers/{request_passenger_id}/archive")
async def archive_request_passenger(agency_id: str, request_id: str, request_passenger_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    item = await db.collection("request_passengers").update_one({"agency_id": agency_id, "request_id": request_id, "id": request_passenger_id}, {"status": "archived"})
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request passenger not found.")
    request = await update_counts(db, agency_id, request_id)
    await write_timeline(db, agency_id, request_id, user["id"], "request.passenger_archived", "Request passenger archived")
    return {"request_passenger": item, "request": request}


async def create_child(db: Database, agency_id: str, request_id: str, user: dict, model, collection_name: str, payload, event_type: str, title: str) -> dict:
    await require_write(db, agency_id, user)
    await get_request_or_404(db, agency_id, request_id)
    item = model(agency_id=agency_id, request_id=request_id, **payload.model_dump(mode="json"))
    created = await db.collection(collection_name).insert_one(item.model_dump(mode="json"))
    request = await update_counts(db, agency_id, request_id) if collection_name == "requested_services" else None
    await write_timeline(db, agency_id, request_id, user["id"], event_type, title)
    await write_audit(db, agency_id, user["id"], event_type, collection_name, item.id, title)
    return {"item": created, "request": request}


def child_routes(path: str, collection_name: str, model, create_model, update_model, label: str):
    @router.get(path)
    async def list_items(agency_id: str, request_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
        await require_read(db, agency_id, user)
        await get_request_or_404(db, agency_id, request_id)
        items = await db.collection(collection_name).find_many({"agency_id": agency_id, "request_id": request_id})
        if collection_name == "request_segments":
            items = [item for item in items if item.get("status") != "archived"]
            items.sort(key=lambda item: item.get("sequence", 0))
        return {"items": items}

    @router.post(path, status_code=status.HTTP_201_CREATED)
    async def create_item(agency_id: str, request_id: str, payload: create_model, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
        if collection_name == "requested_services" and payload.passenger_id:
            await get_passenger_or_404(db, agency_id, payload.passenger_id)
        result = await create_child(db, agency_id, request_id, user, model, collection_name, payload, f"request.{label}_created", f"Request {label} added")
        return {label: result["item"], "request": result["request"]}

    @router.put(f"{path}/{{item_id}}")
    async def update_item(agency_id: str, request_id: str, item_id: str, payload: update_model, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
        await require_write(db, agency_id, user)
        updates = clean_updates(payload)
        if not updates:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided.")
        item = await db.collection(collection_name).update_one({"agency_id": agency_id, "request_id": request_id, "id": item_id}, updates)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Request {label} not found.")
        request = await update_counts(db, agency_id, request_id) if collection_name == "requested_services" else None
        await write_timeline(db, agency_id, request_id, user["id"], f"request.{label}_updated", f"Request {label} updated")
        return {label: item, "request": request}

    @router.post(f"{path}/{{item_id}}/archive")
    async def archive_item(agency_id: str, request_id: str, item_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
        await require_write(db, agency_id, user)
        updates = {"status": "archived"} if collection_name == "request_segments" else {"status": "cancelled"}
        item = await db.collection(collection_name).update_one({"agency_id": agency_id, "request_id": request_id, "id": item_id}, updates)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Request {label} not found.")
        request = await update_counts(db, agency_id, request_id) if collection_name == "requested_services" else None
        await write_timeline(db, agency_id, request_id, user["id"], f"request.{label}_archived", f"Request {label} archived")
        return {label: item, "request": request}


child_routes("/requests/{request_id}/segments", "request_segments", RequestSegment, RequestSegmentCreate, RequestSegmentUpdate, "segment")
child_routes("/requests/{request_id}/services", "requested_services", RequestedService, RequestedServiceCreate, RequestedServiceUpdate, "service")


@router.get("/requests/{request_id}/messages")
async def list_messages(agency_id: str, request_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    await get_request_or_404(db, agency_id, request_id)
    return {"items": await db.collection("request_messages").find_many({"agency_id": agency_id, "request_id": request_id})}


@router.post("/requests/{request_id}/messages", status_code=status.HTTP_201_CREATED)
async def create_message(agency_id: str, request_id: str, payload: RequestMessageCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_request_or_404(db, agency_id, request_id)
    message = RequestMessage(agency_id=agency_id, request_id=request_id, sender_user_id=user["id"], **payload.model_dump(mode="json"))
    created = await db.collection("request_messages").insert_one(message.model_dump(mode="json"))
    await write_timeline(db, agency_id, request_id, user["id"], "request.message_added", "Message added", payload.message_text[:140], payload.visibility)
    return {"message": created}


@router.get("/requests/{request_id}/tasks")
async def list_tasks(agency_id: str, request_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    await get_request_or_404(db, agency_id, request_id)
    return {"items": await db.collection("request_tasks").find_many({"agency_id": agency_id, "request_id": request_id})}


@router.post("/requests/{request_id}/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(agency_id: str, request_id: str, payload: RequestTaskCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_request_or_404(db, agency_id, request_id)
    task = RequestTask(agency_id=agency_id, request_id=request_id, **payload.model_dump(mode="json"))
    created = await db.collection("request_tasks").insert_one(task.model_dump(mode="json"))
    await write_timeline(db, agency_id, request_id, user["id"], "request.task_created", "Task created", payload.title)
    return {"task": created}


@router.put("/requests/{request_id}/tasks/{task_id}")
async def update_task(agency_id: str, request_id: str, task_id: str, payload: RequestTaskUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    updates = clean_updates(payload)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided.")
    if updates.get("status") == "done":
        updates["completed_at"] = datetime.now(timezone.utc)
    task = await db.collection("request_tasks").update_one({"agency_id": agency_id, "request_id": request_id, "id": task_id}, updates)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    await write_timeline(db, agency_id, request_id, user["id"], "request.task_updated", "Task updated", task["title"])
    return {"task": task}


@router.post("/requests/{request_id}/tasks/{task_id}/complete")
async def complete_task(agency_id: str, request_id: str, task_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    task = await db.collection("request_tasks").update_one({"agency_id": agency_id, "request_id": request_id, "id": task_id}, {"status": "done", "completed_at": datetime.now(timezone.utc)})
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    await write_timeline(db, agency_id, request_id, user["id"], "request.task_completed", "Task completed", task["title"])
    return {"task": task}


@router.get("/requests/{request_id}/timeline")
async def list_timeline(agency_id: str, request_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    await get_request_or_404(db, agency_id, request_id)
    items = await db.collection("request_timeline_events").find_many({"agency_id": agency_id, "request_id": request_id})
    items.sort(key=lambda item: item.get("created_at", ""))
    return {"items": items}
