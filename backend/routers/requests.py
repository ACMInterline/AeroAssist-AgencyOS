from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    AuditEvent,
    ClientPassengerRelationship,
    ClientProfile,
    OperationalRequestBuilderCreate,
    RequestMessage,
    RequestMessageCreate,
    RequestPassenger,
    RequestPassengerCreate,
    RequestPassengerIdentityConfirm,
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
    TravelRequestUpdate,
    RequestV4Payload,
    RequestV4Update,
)
from services.request_passenger_identity_service import (
    confirm_request_passenger_identity,
    unresolved_request_passenger,
)
from services.request_normalization_service import normalize_request_children
from services.request_v4_service import (
    builder_payload_to_v4,
    create_request_v4,
    project_canonical_request,
    request_detail_v4,
    update_request_v4,
)
from services.service_catalogue_service import find_service_catalogue_record, service_catalogue_snapshot
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
    await require_any_agency_role(db, agency_id, user, READ_ROLES)


async def require_write(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
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


def reject_independent_v4_child_write(request: dict) -> None:
    if request.get("request_version") == 4:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Request V4 structure is aggregate-owned. Update the canonical request instead of writing a child projection independently.",
        )


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
    pet_count = await db.collection("request_pets").count({"agency_id": agency_id, "request_id": request_id, "status": "active"})
    item_count = await db.collection("request_special_items").count({"agency_id": agency_id, "request_id": request_id, "status": "active"})
    return await db.collection("travel_requests").update_one(
        {"agency_id": agency_id, "id": request_id},
        {"passenger_count": passenger_count, "service_count": service_count, "pet_count": pet_count, "special_service_count": service_count + pet_count + item_count},
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
    if not payload.passenger_id:
        display_name = compact_text(payload.display_name, 160)
        first_name = compact_text(payload.first_name, 80)
        last_name = compact_text(payload.last_name, 80)
        if not display_name:
            display_name = " ".join(
                part for part in [first_name, last_name] if part
            )
        return {
            "passenger": {
                "id": None,
                "display_name": display_name or f"Unresolved traveler {index + 1}",
                "date_of_birth": payload.date_of_birth,
                "passenger_type": PASSENGER_TYPE_MAP.get(payload.passenger_type, "ADT"),
            },
            "relationship": None,
        }
    passenger = await get_passenger_or_404(db, agency_id, payload.passenger_id)
    if passenger.get("status") in {"archived", "duplicate_merged", "quarantined"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Archived, merged, or quarantined passengers cannot be linked to a request.",
        )
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
        if not service.applies_to_all_segments and not service.segment_ids:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Service rows require at least one exact segment.")
        if not service.applies_to_all_passengers and not service.passenger_ids:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Service rows require at least one exact passenger.")
        if service.category == "mobility_assistance" and service.details.get("assessment_version") == "v2_assessment_driven":
            suggested = service.details.get("suggested_ssr_code")
            confirmed = service.details.get("confirmed_ssr_code")
            if suggested and confirmed and confirmed != suggested and not service.details.get("override_reason"):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mobility SSR override reason is required when confirmed code differs from suggested code.")
    canonical_payload = await builder_payload_to_v4(db, agency_id, payload)
    return await create_request_v4(db, agency_id, canonical_payload, user["id"])


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
    trips = {trip["id"]: trip for trip in await db.collection("trip_dossiers").find_many({"agency_id": agency_id})}
    items.sort(key=lambda item: str(item.get("updated_at") or ""), reverse=True)
    return {"items": [{**item, "client": clients.get(item["client_id"]), "linked_trip": trips.get(item.get("trip_id"))} for item in items]}


@router.post("/requests", status_code=status.HTTP_201_CREATED)
async def create_request(
    agency_id: str,
    payload: RequestV4Payload,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    return await create_request_v4(db, agency_id, payload, user["id"])


@router.get("/requests/{request_id}")
async def get_request(agency_id: str, request_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    request = await get_request_or_404(db, agency_id, request_id)
    return await request_detail_v4(db, request)


@router.post("/requests/{request_id}/normalize")
async def normalize_request(
    agency_id: str,
    request_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    request = await get_request_or_404(db, agency_id, request_id)
    if request.get("request_version") == 4:
        payload = RequestV4Payload.model_validate(request.get("canonical_payload") or {})
        counts = await project_canonical_request(db, request, payload)
        updated = await db.collection("travel_requests").update_one(
            {"agency_id": agency_id, "id": request_id},
            {
                "canonical_projection_status": "current",
                "canonical_projection_warnings": [],
                "passenger_count": counts["passenger_count"],
                "service_count": counts["service_count"],
                "pet_count": counts["pet_count"],
                "special_service_count": counts["service_count"] + counts["pet_count"] + counts["special_item_count"],
            },
        )
        await write_timeline(db, agency_id, request_id, user["id"], "request.v4_projection_rebuilt", "Request compatibility details rebuilt")
        return {"request": updated, "projection": counts, "request_version": 4}
    result = await normalize_request_children(db, agency_id, request_id, actor_user_id=user["id"])
    await write_timeline(db, agency_id, request_id, user["id"], "request.normalized", "Request normalized", "Segment-scoped services, pets, special items, and flags updated.")
    return result


@router.put("/requests/{request_id}")
async def update_request(agency_id: str, request_id: str, payload: TravelRequestUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    existing_request = await get_request_or_404(db, agency_id, request_id)
    if existing_request.get("request_version") == 4:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Use PATCH with the canonical Request V4 aggregate to edit this request.",
        )
    updates = clean_updates(payload)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided.")
    if updates.get("status") in {"closed", "cancelled"}:
        updates["closed_at"] = datetime.now(timezone.utc)
    updated = await db.collection("travel_requests").update_one({"agency_id": agency_id, "id": request_id}, updates)
    await write_audit(db, agency_id, user["id"], "request.updated", "travel_request", request_id, "Updated request.", {"fields": sorted(updates.keys())})
    await write_timeline(db, agency_id, request_id, user["id"], "request.updated", "Request updated", ", ".join(sorted(updates.keys())))
    return {"request": updated}


@router.patch("/requests/{request_id}")
async def patch_request_v4(
    agency_id: str,
    request_id: str,
    payload: RequestV4Update,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    return await update_request_v4(db, agency_id, request_id, payload, user["id"])


@router.post("/requests/{request_id}/archive")
async def archive_request(agency_id: str, request_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    request = await get_request_or_404(db, agency_id, request_id)
    updates = {"status": "archived"}
    if request.get("request_version") == 4:
        canonical = RequestV4Payload.model_validate(request.get("canonical_payload") or {})
        canonical.admin_metadata.status = "archived"
        updates["canonical_payload"] = canonical.model_dump(mode="json")
    updated = await db.collection("travel_requests").update_one({"agency_id": agency_id, "id": request_id}, updates)
    await write_audit(db, agency_id, user["id"], "request.archived", "travel_request", request_id, "Archived request.")
    await write_timeline(db, agency_id, request_id, user["id"], "request.archived", "Request archived")
    return {"request": updated}


@router.post("/requests/{request_id}/restore")
async def restore_request(agency_id: str, request_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    request = await get_request_or_404(db, agency_id, request_id)
    updates = {"status": "triage", "closed_at": None}
    if request.get("request_version") == 4:
        canonical = RequestV4Payload.model_validate(request.get("canonical_payload") or {})
        canonical.admin_metadata.status = "triage"
        updates["canonical_payload"] = canonical.model_dump(mode="json")
    updated = await db.collection("travel_requests").update_one({"agency_id": agency_id, "id": request_id}, updates)
    await write_audit(db, agency_id, user["id"], "request.restored", "travel_request", request_id, "Restored request.")
    await write_timeline(db, agency_id, request_id, user["id"], "request.restored", "Request restored")
    return {"request": updated}


@router.post("/requests/{request_id}/status")
async def change_status(agency_id: str, request_id: str, payload: RequestStatusUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    request = await get_request_or_404(db, agency_id, request_id)
    updates = {"status": payload.status}
    if request.get("request_version") == 4:
        canonical = RequestV4Payload.model_validate(request.get("canonical_payload") or {})
        canonical.admin_metadata.status = getattr(payload.status, "value", payload.status)
        updates["canonical_payload"] = canonical.model_dump(mode="json")
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
    reject_independent_v4_child_write(request)
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
    request = await get_request_or_404(db, agency_id, request_id)
    reject_independent_v4_child_write(request)
    updates = clean_updates(payload)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided.")
    item = await db.collection("request_passengers").update_one({"agency_id": agency_id, "request_id": request_id, "id": request_passenger_id}, updates)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request passenger not found.")
    await write_timeline(db, agency_id, request_id, user["id"], "request.passenger_updated", "Request passenger updated")
    return {"request_passenger": item}


@router.post("/requests/{request_id}/passengers/{request_passenger_id}/confirm-identity")
async def confirm_request_passenger(
    agency_id: str,
    request_id: str,
    request_passenger_id: str,
    payload: RequestPassengerIdentityConfirm,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    return await confirm_request_passenger_identity(
        db,
        agency_id,
        request_id,
        request_passenger_id,
        payload,
        user["id"],
    )


@router.post("/requests/{request_id}/passengers/{request_passenger_id}/archive")
async def archive_request_passenger(agency_id: str, request_id: str, request_passenger_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    request = await get_request_or_404(db, agency_id, request_id)
    reject_independent_v4_child_write(request)
    item = await db.collection("request_passengers").update_one({"agency_id": agency_id, "request_id": request_id, "id": request_passenger_id}, {"status": "archived"})
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request passenger not found.")
    request = await update_counts(db, agency_id, request_id)
    await write_timeline(db, agency_id, request_id, user["id"], "request.passenger_archived", "Request passenger archived")
    return {"request_passenger": item, "request": request}


async def create_child(db: Database, agency_id: str, request_id: str, user: dict, model, collection_name: str, payload, event_type: str, title: str) -> dict:
    await require_write(db, agency_id, user)
    request = await get_request_or_404(db, agency_id, request_id)
    reject_independent_v4_child_write(request)
    data = payload.model_dump(mode="json")
    if collection_name == "requested_services":
        record = await find_service_catalogue_record(db, data.get("service_key") or data.get("service_code"))
        snapshot = service_catalogue_snapshot(record)
        if snapshot:
            data["service_catalogue_id"] = data.get("service_catalogue_id") or snapshot.get("service_catalogue_id")
            data["service_key"] = data.get("service_key") or snapshot.get("service_key")
            data["service_catalogue_snapshot_json"] = data.get("service_catalogue_snapshot_json") or snapshot
            data["service_name"] = data.get("service_name") or snapshot.get("label")
            data["service_category"] = data.get("service_category") or snapshot.get("category")
    item = model(agency_id=agency_id, request_id=request_id, **data)
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
        request = await get_request_or_404(db, agency_id, request_id)
        reject_independent_v4_child_write(request)
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
        request = await get_request_or_404(db, agency_id, request_id)
        reject_independent_v4_child_write(request)
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
