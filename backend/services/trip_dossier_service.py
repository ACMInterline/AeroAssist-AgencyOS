from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException, status

from database import Database
from models import (
    AuditEvent,
    RequestTimelineEvent,
    TripDossier,
    TripDossierCreate,
    TripDossierSource,
    TripPassenger,
    TripPassengerType,
    TripSegment,
    TripServiceItem,
    TripTimelineEvent,
)


def _compact(value: Any, limit: int = 1000) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).split())
    return text[:limit] if text else None


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item]
    return []


def _passenger_type(value: Any) -> str:
    normalized = str(value or "").lower()
    if normalized in {"adt", "adult"}:
        return TripPassengerType.ADULT.value
    if normalized in {"chd", "child"}:
        return TripPassengerType.CHILD.value
    if normalized in {"inf", "infant"}:
        return TripPassengerType.INFANT.value
    if normalized in {"youth", "yth"}:
        return TripPassengerType.YOUTH.value
    if normalized in {"senior", "src"}:
        return TripPassengerType.SENIOR.value
    return TripPassengerType.UNKNOWN.value


def _segment_code(*values: Any) -> str:
    for value in values:
        text = _compact(value, 16)
        if text:
            return text.upper()
    return "TBD"


def _date_summary(request: dict, segments: list[dict]) -> str | None:
    dates = [segment.get("departure_date") for segment in segments if segment.get("departure_date")]
    if dates:
        return f"{min(dates)} to {max(dates)}" if len(set(dates)) > 1 else str(dates[0])
    departure = request.get("requested_departure_date") or request.get("first_departure_date")
    return_date = request.get("requested_return_date") or request.get("last_arrival_date")
    if departure and return_date:
        return f"{departure} to {return_date}"
    return str(departure or return_date) if departure or return_date else None


def _trip_title(request: dict) -> str:
    route = _compact(request.get("route_summary"), 80)
    service = _compact(request.get("service_summary"), 80)
    if route and service:
        return f"{route} {service}".replace("→", "-")[:160]
    if route:
        return f"{route} trip".replace("→", "-")[:160]
    if service:
        return f"{service} trip"[:160]
    return f"Trip from Request {request.get('request_reference') or request.get('id')}"


async def write_trip_audit(db: Database, agency_id: str, actor_user_id: Optional[str], event_type: str, trip_id: str, summary: str, metadata: dict | None = None) -> None:
    await db.collection("audit_events").insert_one(
        AuditEvent(
            agency_id=agency_id,
            actor_user_id=actor_user_id,
            event_type=event_type,
            entity_type="trip_dossier",
            entity_id=trip_id,
            summary=summary,
            metadata=metadata or {},
        ).model_dump(mode="json")
    )


async def write_trip_timeline(db: Database, agency_id: str, workspace_id: Optional[str], trip_id: str, actor_user_id: Optional[str], event_type: str, title: str, summary: str | None = None, metadata: dict | None = None) -> None:
    await db.collection("trip_timeline_events").insert_one(
        TripTimelineEvent(
            agency_id=agency_id,
            workspace_id=workspace_id,
            trip_id=trip_id,
            actor_user_id=actor_user_id,
            event_type=event_type,
            title=title,
            summary=summary,
            metadata=metadata or {},
        ).model_dump(mode="json")
    )


async def write_request_timeline(db: Database, agency_id: str, request_id: str, actor_user_id: Optional[str], event_type: str, title: str, summary: str | None = None, metadata: dict | None = None) -> None:
    await db.collection("request_timeline_events").insert_one(
        RequestTimelineEvent(
            agency_id=agency_id,
            request_id=request_id,
            actor_user_id=actor_user_id,
            event_type=event_type,
            title=title,
            summary=summary,
            metadata=metadata or {},
        ).model_dump(mode="json")
    )


async def next_trip_reference(db: Database, agency_id: str) -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    count = await db.collection("trip_dossiers").count({"agency_id": agency_id})
    return f"TRP-{today}-{count + 1:04d}"


async def get_trip_or_404(db: Database, agency_id: str, trip_id: str) -> dict:
    trip = await db.collection("trip_dossiers").find_one({"agency_id": agency_id, "id": trip_id})
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip dossier not found.")
    return trip


async def get_request_or_404(db: Database, agency_id: str, request_id: str) -> dict:
    request = await db.collection("travel_requests").find_one({"agency_id": agency_id, "id": request_id})
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.")
    return request


async def create_manual_trip(db: Database, agency_id: str, payload: TripDossierCreate, actor_user_id: str) -> dict:
    trip = TripDossier(
        agency_id=agency_id,
        created_by_user_id=actor_user_id,
        updated_by_user_id=actor_user_id,
        trip_reference=await next_trip_reference(db, agency_id),
        **payload.model_dump(mode="json"),
    )
    created = await db.collection("trip_dossiers").insert_one(trip.model_dump(mode="json"))
    await write_trip_audit(db, agency_id, actor_user_id, "trip_dossier_created", created["id"], f"Created trip dossier {created['trip_reference']}.")
    await write_trip_timeline(db, agency_id, created.get("workspace_id"), created["id"], actor_user_id, "trip_dossier_created", "Trip dossier created", created.get("trip_title"))
    return created


async def create_trip_from_request(db: Database, agency_id: str, request_id: str, actor_user_id: str) -> dict:
    request = await get_request_or_404(db, agency_id, request_id)
    if request.get("trip_id"):
        existing = await db.collection("trip_dossiers").find_one({"agency_id": agency_id, "id": request["trip_id"]})
        if existing:
            await copy_request_to_trip(db, agency_id, existing["id"], request_id, actor_user_id)
            return await rebuild_trip_summary(db, agency_id, existing["id"], actor_user_id)
    existing = await db.collection("trip_dossiers").find_one({"agency_id": agency_id, "primary_request_id": request_id})
    if existing:
        await link_request_to_trip(db, agency_id, existing["id"], request_id, actor_user_id)
        return await rebuild_trip_summary(db, agency_id, existing["id"], actor_user_id)

    segments = await db.collection("request_segments").find_many({"agency_id": agency_id, "request_id": request_id, "status": "active"})
    pets = await db.collection("request_pets").find_many({"agency_id": agency_id, "request_id": request_id, "status": "active"})
    items = await db.collection("request_special_items").find_many({"agency_id": agency_id, "request_id": request_id, "status": "active"})
    summary_notes = []
    if not segments:
        summary_notes.append("Request has no normalized itinerary segments yet.")
    if request.get("passenger_count", 0) == 0:
        summary_notes.append("Request has no normalized passengers yet.")
    if pets:
        summary_notes.append(f"Pet travel summary only: {len(pets)} pet record(s) remain request-level in this phase.")
    if items:
        summary_notes.append(f"Special item summary only: {len(items)} item record(s) remain request-level in this phase.")
    trip = TripDossier(
        agency_id=agency_id,
        workspace_id=request.get("workspace_id"),
        primary_client_id=request.get("client_id"),
        primary_request_id=request_id,
        linked_request_ids=[request_id],
        trip_reference=await next_trip_reference(db, agency_id),
        trip_title=_trip_title(request),
        trip_status="planning",
        trip_type=request.get("trip_type") or "unknown",
        route_summary=request.get("route_summary"),
        date_summary=_date_summary(request, segments),
        service_summary=request.get("service_summary"),
        operational_summary=request.get("title"),
        internal_notes=" ".join(summary_notes) or request.get("internal_notes"),
        client_visible_notes=request.get("client_visible_notes"),
        source=TripDossierSource.REQUEST_CONVERSION.value,
        raw_source_payloads=[{"request_id": request_id, "request_reference": request.get("request_reference")}],
        created_by_user_id=actor_user_id,
        updated_by_user_id=actor_user_id,
    )
    created = await db.collection("trip_dossiers").insert_one(trip.model_dump(mode="json"))
    await db.collection("travel_requests").update_one({"agency_id": agency_id, "id": request_id}, {"trip_id": created["id"]})
    await copy_request_to_trip(db, agency_id, created["id"], request_id, actor_user_id)
    await write_trip_audit(db, agency_id, actor_user_id, "trip_created_from_request", created["id"], f"Created trip {created['trip_reference']} from request {request.get('request_reference')}.", {"request_id": request_id})
    await write_trip_timeline(db, agency_id, created.get("workspace_id"), created["id"], actor_user_id, "trip_created_from_request", "Trip created from request", request.get("request_reference"), {"request_id": request_id})
    await write_request_timeline(db, agency_id, request_id, actor_user_id, "trip_created_from_request", "Trip dossier created", created["trip_reference"], {"trip_id": created["id"]})
    return await rebuild_trip_summary(db, agency_id, created["id"], actor_user_id)


async def link_request_to_trip(db: Database, agency_id: str, trip_id: str, request_id: str, actor_user_id: str) -> dict:
    trip = await get_trip_or_404(db, agency_id, trip_id)
    request = await get_request_or_404(db, agency_id, request_id)
    linked_trip_id = request.get("trip_id")
    if linked_trip_id and linked_trip_id != trip_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Request is already linked to another trip dossier.")
    linked_ids = list(dict.fromkeys([*trip.get("linked_request_ids", []), request_id]))
    updates = {"linked_request_ids": linked_ids, "updated_by_user_id": actor_user_id}
    if not trip.get("primary_request_id"):
        updates["primary_request_id"] = request_id
    if not trip.get("primary_client_id") and request.get("client_id"):
        updates["primary_client_id"] = request["client_id"]
    await db.collection("trip_dossiers").update_one({"agency_id": agency_id, "id": trip_id}, updates)
    await db.collection("travel_requests").update_one({"agency_id": agency_id, "id": request_id}, {"trip_id": trip_id})
    await copy_request_to_trip(db, agency_id, trip_id, request_id, actor_user_id)
    await write_trip_audit(db, agency_id, actor_user_id, "request_linked_to_trip", trip_id, f"Linked request {request.get('request_reference')} to trip.", {"request_id": request_id})
    await write_trip_timeline(db, agency_id, trip.get("workspace_id"), trip_id, actor_user_id, "request_linked_to_trip", "Request linked", request.get("request_reference"), {"request_id": request_id})
    await write_request_timeline(db, agency_id, request_id, actor_user_id, "request_linked_to_trip", "Linked to trip dossier", trip.get("trip_reference"), {"trip_id": trip_id})
    return await rebuild_trip_summary(db, agency_id, trip_id, actor_user_id)


async def unlink_request_from_trip(db: Database, agency_id: str, trip_id: str, request_id: str, actor_user_id: str) -> dict:
    trip = await get_trip_or_404(db, agency_id, trip_id)
    await get_request_or_404(db, agency_id, request_id)
    linked_ids = [item for item in trip.get("linked_request_ids", []) if item != request_id]
    updates: dict[str, Any] = {"linked_request_ids": linked_ids, "updated_by_user_id": actor_user_id}
    if trip.get("primary_request_id") == request_id:
        updates["primary_request_id"] = linked_ids[0] if linked_ids else None
    await db.collection("trip_dossiers").update_one({"agency_id": agency_id, "id": trip_id}, updates)
    request = await db.collection("travel_requests").find_one({"agency_id": agency_id, "id": request_id})
    if request and request.get("trip_id") == trip_id:
        await db.collection("travel_requests").update_one({"agency_id": agency_id, "id": request_id}, {"trip_id": None})
    await write_trip_audit(db, agency_id, actor_user_id, "request_unlinked_from_trip", trip_id, "Unlinked request from trip.", {"request_id": request_id})
    await write_trip_timeline(db, agency_id, trip.get("workspace_id"), trip_id, actor_user_id, "request_unlinked_from_trip", "Request unlinked", None, {"request_id": request_id})
    await write_request_timeline(db, agency_id, request_id, actor_user_id, "request_unlinked_from_trip", "Unlinked from trip dossier", trip.get("trip_reference"), {"trip_id": trip_id})
    return await rebuild_trip_summary(db, agency_id, trip_id, actor_user_id)


async def copy_request_to_trip(db: Database, agency_id: str, trip_id: str, request_id: str, actor_user_id: str) -> dict:
    trip = await get_trip_or_404(db, agency_id, trip_id)
    passengers = await db.collection("request_passengers").find_many({"agency_id": agency_id, "request_id": request_id, "status": "active"})
    segments = await db.collection("request_segments").find_many({"agency_id": agency_id, "request_id": request_id, "status": "active"})
    passenger_map: dict[str, str] = {}
    segment_map: dict[str, str] = {}

    for index, passenger in enumerate(passengers, start=1):
        existing = await db.collection("trip_passengers").find_one({"agency_id": agency_id, "trip_id": trip_id, "source_request_passenger_id": passenger["id"]})
        if existing:
            passenger_map[passenger["id"]] = existing["id"]
            continue
        item = TripPassenger(
            agency_id=agency_id,
            workspace_id=trip.get("workspace_id"),
            trip_id=trip_id,
            source_request_passenger_id=passenger["id"],
            passenger_profile_id=passenger.get("passenger_id"),
            display_name=passenger.get("snapshot_display_name") or "Passenger",
            passenger_type=_passenger_type(passenger.get("snapshot_passenger_type")),
            date_of_birth=passenger.get("snapshot_date_of_birth"),
            assistance_summary=_compact(passenger.get("service_needs_summary"), 500),
            sort_order=index,
        )
        created = await db.collection("trip_passengers").insert_one(item.model_dump(mode="json"))
        passenger_map[passenger["id"]] = created["id"]
        await write_trip_timeline(db, agency_id, trip.get("workspace_id"), trip_id, actor_user_id, "trip_passenger_copied", "Passenger copied from request", created["display_name"], {"source_request_passenger_id": passenger["id"]})

    for index, segment in enumerate(sorted(segments, key=lambda row: row.get("sequence") or 0), start=1):
        existing = await db.collection("trip_segments").find_one({"agency_id": agency_id, "trip_id": trip_id, "source_request_segment_id": segment["id"]})
        if existing:
            segment_map[segment["id"]] = existing["id"]
            continue
        item = TripSegment(
            agency_id=agency_id,
            workspace_id=trip.get("workspace_id"),
            trip_id=trip_id,
            source_request_segment_id=segment["id"],
            segment_order=segment.get("sequence") or index,
            origin_airport_code=_segment_code(segment.get("origin_airport_code"), segment.get("origin_text")),
            destination_airport_code=_segment_code(segment.get("destination_airport_code"), segment.get("destination_text")),
            departure_date=segment.get("departure_date"),
            departure_time=segment.get("departure_time_window"),
            arrival_date=segment.get("arrival_date"),
            arrival_time=segment.get("arrival_time_window"),
            marketing_airline_code=segment.get("preferred_airline_code") or segment.get("marketing_airline"),
            operating_airline_code=segment.get("operating_airline"),
            flight_number=segment.get("preferred_flight_number"),
            cabin=segment.get("cabin_preference"),
        )
        created = await db.collection("trip_segments").insert_one(item.model_dump(mode="json"))
        segment_map[segment["id"]] = created["id"]
        await write_trip_timeline(db, agency_id, trip.get("workspace_id"), trip_id, actor_user_id, "trip_segment_copied", "Segment copied from request", f"{created['origin_airport_code']} to {created['destination_airport_code']}", {"source_request_segment_id": segment["id"]})

    scoped_services = await db.collection("request_passenger_segment_services").find_many({"agency_id": agency_id, "request_id": request_id})
    requested_services = await db.collection("requested_services").find_many({"agency_id": agency_id, "request_id": request_id})
    if scoped_services:
        for service in scoped_services:
            existing = await db.collection("trip_service_items").find_one({"agency_id": agency_id, "trip_id": trip_id, "source_passenger_segment_service_id": service["id"]})
            if existing:
                continue
            item = TripServiceItem(
                agency_id=agency_id,
                workspace_id=trip.get("workspace_id"),
                trip_id=trip_id,
                source_request_service_id=service.get("requested_service_id"),
                source_passenger_segment_service_id=service["id"],
                service_catalogue_id=service.get("service_catalogue_id"),
                service_key=service.get("service_key"),
                service_catalogue_snapshot_json=service.get("service_catalogue_snapshot_json") or {},
                service_code=service.get("service_code") or "SERVICE",
                service_label=service.get("service_label") or service.get("service_code") or "Service",
                service_catalogue_category=(service.get("service_catalogue_snapshot_json") or {}).get("category"),
                service_family_code=service.get("service_family_code"),
                passenger_ids=[passenger_map[service["request_passenger_id"]]] if service.get("request_passenger_id") in passenger_map else [],
                segment_ids=[segment_map[service["request_segment_id"]]] if service.get("request_segment_id") in segment_map else [],
                status=service.get("applicability_status") if service.get("applicability_status") in {"requested", "checking", "quoted", "confirmed", "rejected", "cancelled", "fulfilled"} else "requested",
                notes=_compact(service.get("notes"), 1000),
            )
            created = await db.collection("trip_service_items").insert_one(item.model_dump(mode="json"))
            await write_trip_timeline(db, agency_id, trip.get("workspace_id"), trip_id, actor_user_id, "trip_service_item_copied", "Service scope copied from request", created["service_label"], {"source_passenger_segment_service_id": service["id"]})
    else:
        for service in requested_services:
            existing = await db.collection("trip_service_items").find_one({"agency_id": agency_id, "trip_id": trip_id, "source_request_service_id": service["id"]})
            if existing:
                continue
            item = TripServiceItem(
                agency_id=agency_id,
                workspace_id=trip.get("workspace_id"),
                trip_id=trip_id,
                source_request_service_id=service["id"],
                service_catalogue_id=service.get("service_catalogue_id"),
                service_key=service.get("service_key"),
                service_catalogue_snapshot_json=service.get("service_catalogue_snapshot_json") or {},
                service_code=service.get("service_code") or "SERVICE",
                service_label=service.get("service_name") or service.get("client_visible_summary") or service.get("service_code") or "Service",
                service_catalogue_category=(service.get("service_catalogue_snapshot_json") or {}).get("category"),
                service_family_code=service.get("service_family_code") or service.get("service_category"),
                passenger_ids=[passenger_map[item] for item in _as_list(service.get("passenger_ids")) if item in passenger_map],
                segment_ids=[segment_map[item] for item in _as_list(service.get("segment_ids")) if item in segment_map],
                status=service.get("status") if service.get("status") in {"requested", "checking", "quoted", "confirmed", "rejected", "cancelled", "fulfilled"} else "requested",
                notes=_compact(service.get("details") or service.get("internal_notes"), 1000),
            )
            created = await db.collection("trip_service_items").insert_one(item.model_dump(mode="json"))
            await write_trip_timeline(db, agency_id, trip.get("workspace_id"), trip_id, actor_user_id, "trip_service_item_copied", "Service copied from request", created["service_label"], {"source_request_service_id": service["id"]})
    return {"passengers": passenger_map, "segments": segment_map}


async def rebuild_trip_summary(db: Database, agency_id: str, trip_id: str, actor_user_id: Optional[str] = None) -> dict:
    trip = await get_trip_or_404(db, agency_id, trip_id)
    passengers = await db.collection("trip_passengers").find_many({"agency_id": agency_id, "trip_id": trip_id})
    segments = await db.collection("trip_segments").find_many({"agency_id": agency_id, "trip_id": trip_id})
    services = await db.collection("trip_service_items").find_many({"agency_id": agency_id, "trip_id": trip_id})
    ordered_segments = sorted(segments, key=lambda row: row.get("segment_order") or 0)
    route_summary = " / ".join([f"{item.get('origin_airport_code')}-{item.get('destination_airport_code')}" for item in ordered_segments]) or trip.get("route_summary")
    dates = [item.get("departure_date") for item in ordered_segments if item.get("departure_date")]
    date_summary = (f"{min(dates)} to {max(dates)}" if len(set(dates)) > 1 else str(dates[0])) if dates else trip.get("date_summary")
    service_labels = list(dict.fromkeys([item.get("service_label") or item.get("service_code") for item in services if item.get("service_label") or item.get("service_code")]))
    service_summary = "; ".join(service_labels[:6]) if service_labels else trip.get("service_summary")
    updated = await db.collection("trip_dossiers").update_one(
        {"agency_id": agency_id, "id": trip_id},
        {
            "passenger_count": len(passengers),
            "segment_count": len(segments),
            "service_count": len(services),
            "route_summary": route_summary,
            "date_summary": date_summary,
            "service_summary": service_summary,
            "updated_by_user_id": actor_user_id,
        },
    )
    await write_trip_audit(db, agency_id, actor_user_id, "trip_summary_rebuilt", trip_id, "Rebuilt trip summary counts.", {"passengers": len(passengers), "segments": len(segments), "services": len(services)})
    await write_trip_timeline(db, agency_id, trip.get("workspace_id"), trip_id, actor_user_id, "trip_summary_rebuilt", "Trip summary rebuilt", f"{len(passengers)} passengers, {len(segments)} segments, {len(services)} services")
    return updated or trip
