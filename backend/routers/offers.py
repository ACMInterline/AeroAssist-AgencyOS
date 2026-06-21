from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    AuditEvent,
    CreateOfferFromRequest,
    Offer,
    OfferCreate,
    OfferFareOption,
    OfferFareOptionCreate,
    OfferFareOptionUpdate,
    OfferPassenger,
    OfferPassengerCreate,
    OfferPassengerUpdate,
    OfferPriceLine,
    OfferPriceLineCreate,
    OfferPriceLineUpdate,
    OfferRouteAlternative,
    OfferRouteAlternativeCreate,
    OfferRouteAlternativeUpdate,
    OfferSegment,
    OfferSegmentCreate,
    OfferSegmentUpdate,
    OfferServiceCheck,
    OfferServiceCheckCreate,
    OfferServiceCheckUpdate,
    OfferTimelineEvent,
    OfferUpdate,
    RequestTimelineEvent,
)
from services.tenant_service import assert_agency_access, require_any_agency_role

router = APIRouter(prefix="/api/agencies/{agency_id}", tags=["offers"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin", "agency_agent"]


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


async def write_offer_timeline(db: Database, agency_id: str, offer_id: str, actor_user_id: str | None, event_type: str, title: str, summary: str | None = None, visibility: str = "internal", metadata: dict | None = None) -> None:
    event = OfferTimelineEvent(agency_id=agency_id, offer_id=offer_id, actor_user_id=actor_user_id, event_type=event_type, title=title, summary=summary, visibility=visibility, metadata=metadata or {})
    await db.collection("offer_timeline_events").insert_one(event.model_dump(mode="json"))


async def write_request_timeline(db: Database, agency_id: str, request_id: str, actor_user_id: str | None, event_type: str, title: str, summary: str | None = None) -> None:
    event = RequestTimelineEvent(agency_id=agency_id, request_id=request_id, actor_user_id=actor_user_id, event_type=event_type, title=title, summary=summary, visibility="internal")
    await db.collection("request_timeline_events").insert_one(event.model_dump(mode="json"))


async def get_client_or_404(db: Database, agency_id: str, client_id: str) -> dict:
    client = await db.collection("client_profiles").find_one({"agency_id": agency_id, "id": client_id})
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")
    return client


async def get_passenger_or_404(db: Database, agency_id: str, passenger_id: str) -> dict:
    passenger = await db.collection("passenger_profiles").find_one({"agency_id": agency_id, "id": passenger_id})
    if not passenger:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Passenger not found.")
    return passenger


async def get_offer_or_404(db: Database, agency_id: str, offer_id: str) -> dict:
    offer = await db.collection("offers").find_one({"agency_id": agency_id, "id": offer_id})
    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found.")
    return offer


async def get_route_or_404(db: Database, agency_id: str, offer_id: str, route_id: str) -> dict:
    route = await db.collection("offer_route_alternatives").find_one({"agency_id": agency_id, "offer_id": offer_id, "id": route_id})
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route alternative not found.")
    return route


async def get_fare_or_404(db: Database, agency_id: str, offer_id: str, fare_option_id: str) -> dict:
    fare = await db.collection("offer_fare_options").find_one({"agency_id": agency_id, "offer_id": offer_id, "id": fare_option_id})
    if not fare:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fare option not found.")
    return fare


async def next_reference(db: Database, agency_id: str) -> str:
    count = await db.collection("offers").count({"agency_id": agency_id})
    return f"OFF-{count + 1:05d}"


async def recalc_offer(db: Database, agency_id: str, offer_id: str) -> dict:
    routes = [r for r in await db.collection("offer_route_alternatives").find_many({"agency_id": agency_id, "offer_id": offer_id}) if r.get("status") != "withdrawn"]
    fares = [f for f in await db.collection("offer_fare_options").find_many({"agency_id": agency_id, "offer_id": offer_id}) if f.get("status") != "withdrawn"]
    totals = [float(f.get("total_amount") or 0) for f in fares if f.get("status") != "unavailable"]
    updates = {
        "route_alternative_count": len(routes),
        "fare_option_count": len(fares),
        "total_min_amount": min(totals) if totals else None,
        "total_max_amount": max(totals) if totals else None,
    }
    return await db.collection("offers").update_one({"agency_id": agency_id, "id": offer_id}, updates)


async def offer_detail(db: Database, agency_id: str, offer_id: str) -> dict:
    offer = await get_offer_or_404(db, agency_id, offer_id)
    return {
        "offer": offer,
        "client": await get_client_or_404(db, agency_id, offer["client_id"]),
        "passengers": await db.collection("offer_passengers").find_many({"agency_id": agency_id, "offer_id": offer_id, "status": "active"}),
        "routes": await db.collection("offer_route_alternatives").find_many({"agency_id": agency_id, "offer_id": offer_id}),
        "segments": await db.collection("offer_segments").find_many({"agency_id": agency_id, "offer_id": offer_id}),
        "fare_options": await db.collection("offer_fare_options").find_many({"agency_id": agency_id, "offer_id": offer_id}),
        "price_lines": await db.collection("offer_price_lines").find_many({"agency_id": agency_id, "offer_id": offer_id, "status": "active"}),
        "service_checks": await db.collection("offer_service_checks").find_many({"agency_id": agency_id, "offer_id": offer_id, "status": "active"}),
        "timeline": await db.collection("offer_timeline_events").find_many({"agency_id": agency_id, "offer_id": offer_id}),
    }


@router.get("/offers")
async def list_offers(agency_id: str, search: Optional[str] = Query(default=None), status_filter: Optional[str] = Query(default=None, alias="status"), source: Optional[str] = None, client_id: Optional[str] = None, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    filters = {"agency_id": agency_id}
    if status_filter:
        filters["status"] = status_filter
    if source:
        filters["source"] = source
    if client_id:
        filters["client_id"] = client_id
    items = await db.collection("offers").find_many(filters)
    if search:
        needle = search.lower()
        items = [item for item in items if any(needle in str(item.get(field) or "").lower() for field in ["offer_reference", "title", "client_visible_intro", "internal_notes"])]
    clients = {c["id"]: c for c in await db.collection("client_profiles").find_many({"agency_id": agency_id})}
    items.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    return {"items": [{**item, "client": clients.get(item["client_id"])} for item in items]}


@router.post("/offers", status_code=status.HTTP_201_CREATED)
async def create_offer(agency_id: str, payload: OfferCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_client_or_404(db, agency_id, payload.client_id)
    if payload.request_id:
        request = await db.collection("travel_requests").find_one({"agency_id": agency_id, "id": payload.request_id})
        if not request or request["client_id"] != payload.client_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request must belong to the selected client.")
    offer = Offer(agency_id=agency_id, offer_reference=await next_reference(db, agency_id), created_by_user_id=user["id"], **payload.model_dump(mode="json"))
    created = await db.collection("offers").insert_one(offer.model_dump(mode="json"))
    await write_audit(db, agency_id, user["id"], "offer.created", "offer", offer.id, f"Created offer {offer.offer_reference}.")
    await write_offer_timeline(db, agency_id, offer.id, user["id"], "offer.created", "Offer created", offer.title)
    return {"offer": created}


@router.post("/requests/{request_id}/create-offer", status_code=status.HTTP_201_CREATED)
async def create_offer_from_request(agency_id: str, request_id: str, payload: CreateOfferFromRequest, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    request = await db.collection("travel_requests").find_one({"agency_id": agency_id, "id": request_id})
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.")
    offer = Offer(
        agency_id=agency_id,
        offer_reference=await next_reference(db, agency_id),
        client_id=request["client_id"],
        request_id=request_id,
        created_by_user_id=user["id"],
        assigned_user_id=request.get("assigned_user_id"),
        title=payload.title or f"Offer for {request['title']}",
        source="request",
        currency=payload.currency,
        client_language=payload.client_language,
        valid_until=payload.valid_until,
        client_visible_intro=payload.client_visible_intro or request.get("client_visible_notes"),
        client_visible_terms=payload.client_visible_terms,
    )
    created = await db.collection("offers").insert_one(offer.model_dump(mode="json"))
    for request_passenger in await db.collection("request_passengers").find_many({"agency_id": agency_id, "request_id": request_id, "status": "active"}):
        passenger = OfferPassenger(
            agency_id=agency_id,
            offer_id=offer.id,
            passenger_id=request_passenger.get("passenger_id"),
            request_passenger_id=request_passenger["id"],
            snapshot_display_name=request_passenger["snapshot_display_name"],
            snapshot_date_of_birth=request_passenger["snapshot_date_of_birth"],
            snapshot_passenger_type=request_passenger["snapshot_passenger_type"],
            role_in_offer=request_passenger.get("role_in_request", "traveler"),
            is_primary_traveler=request_passenger.get("is_primary_traveler", False),
        )
        await db.collection("offer_passengers").insert_one(passenger.model_dump(mode="json"))
    await write_offer_timeline(db, agency_id, offer.id, user["id"], "offer.created_from_request", "Offer created from request", request["request_reference"])
    await write_request_timeline(db, agency_id, request_id, user["id"], "request.offer_created", "Offer created", offer.offer_reference)
    await write_audit(db, agency_id, user["id"], "offer.created_from_request", "offer", offer.id, "Created offer from request.", {"request_id": request_id})
    return {"offer": created}


@router.get("/offers/{offer_id}")
async def get_offer(agency_id: str, offer_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    return await offer_detail(db, agency_id, offer_id)


@router.put("/offers/{offer_id}")
async def update_offer(agency_id: str, offer_id: str, payload: OfferUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_offer_or_404(db, agency_id, offer_id)
    updates = clean_updates(payload)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided.")
    offer = await db.collection("offers").update_one({"agency_id": agency_id, "id": offer_id}, updates)
    await write_offer_timeline(db, agency_id, offer_id, user["id"], "offer.updated", "Offer updated", ", ".join(sorted(updates.keys())))
    return {"offer": offer}


@router.post("/offers/{offer_id}/archive")
async def archive_offer(agency_id: str, offer_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    offer = await db.collection("offers").update_one({"agency_id": agency_id, "id": offer_id}, {"status": "archived"})
    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found.")
    await write_offer_timeline(db, agency_id, offer_id, user["id"], "offer.archived", "Offer archived")
    return {"offer": offer}


@router.post("/offers/{offer_id}/restore")
async def restore_offer(agency_id: str, offer_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    offer = await db.collection("offers").update_one({"agency_id": agency_id, "id": offer_id}, {"status": "draft"})
    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found.")
    await write_offer_timeline(db, agency_id, offer_id, user["id"], "offer.restored", "Offer restored")
    return {"offer": offer}


@router.post("/offers/{offer_id}/send")
async def send_offer(agency_id: str, offer_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    detail = await offer_detail(db, agency_id, offer_id)
    routes = [r for r in detail["routes"] if r.get("status") != "withdrawn"]
    fares = [f for f in detail["fare_options"] if f.get("status") not in {"withdrawn", "unavailable"}]
    if not routes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one route alternative is required before sending.")
    if not fares:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one fare option is required before sending.")
    sent_at = datetime.now(timezone.utc)
    snapshot = {
        "snapshot_reason": "offer_sent",
        "created_at": sent_at.isoformat(),
        "offer": detail["offer"],
        "client": detail["client"],
        "passengers": detail["passengers"],
        "route_alternatives": detail["routes"],
        "segments": detail["segments"],
        "fare_options": detail["fare_options"],
        "price_lines": detail["price_lines"],
        "service_checks": detail["service_checks"],
        "totals": {"min": detail["offer"].get("total_min_amount"), "max": detail["offer"].get("total_max_amount")},
    }
    offer = await db.collection("offers").update_one({"agency_id": agency_id, "id": offer_id}, {"status": "sent", "sent_at": sent_at, "snapshot_at_send": sent_at, "sent_snapshot": snapshot})
    await write_offer_timeline(db, agency_id, offer_id, user["id"], "offer.sent", "Offer sent", "Send marks offer as sent and snapshots current content.", "client_visible")
    await write_audit(db, agency_id, user["id"], "offer.sent", "offer", offer_id, "Sent offer and created snapshot.")
    if offer.get("request_id"):
        await db.collection("travel_requests").update_one({"agency_id": agency_id, "id": offer["request_id"]}, {"status": "offer_created"})
        await write_request_timeline(db, agency_id, offer["request_id"], user["id"], "request.offer_sent", "Offer sent", offer["offer_reference"])
    return {"offer": offer, "snapshot": snapshot}


@router.get("/offers/{offer_id}/passengers")
async def list_offer_passengers(agency_id: str, offer_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    await get_offer_or_404(db, agency_id, offer_id)
    return {"items": await db.collection("offer_passengers").find_many({"agency_id": agency_id, "offer_id": offer_id, "status": "active"})}


@router.post("/offers/{offer_id}/passengers", status_code=status.HTTP_201_CREATED)
async def add_offer_passenger(agency_id: str, offer_id: str, payload: OfferPassengerCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_offer_or_404(db, agency_id, offer_id)
    passenger = await get_passenger_or_404(db, agency_id, payload.passenger_id)
    item = OfferPassenger(agency_id=agency_id, offer_id=offer_id, snapshot_display_name=passenger["display_name"], snapshot_date_of_birth=passenger["date_of_birth"], snapshot_passenger_type=passenger["passenger_type"], **payload.model_dump(mode="json"))
    created = await db.collection("offer_passengers").insert_one(item.model_dump(mode="json"))
    await write_offer_timeline(db, agency_id, offer_id, user["id"], "offer.passenger_added", "Passenger added", passenger["display_name"])
    return {"offer_passenger": created}


@router.put("/offers/{offer_id}/passengers/{offer_passenger_id}")
async def update_offer_passenger(agency_id: str, offer_id: str, offer_passenger_id: str, payload: OfferPassengerUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    item = await db.collection("offer_passengers").update_one({"agency_id": agency_id, "offer_id": offer_id, "id": offer_passenger_id}, clean_updates(payload))
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer passenger not found.")
    return {"offer_passenger": item}


@router.post("/offers/{offer_id}/passengers/{offer_passenger_id}/archive")
async def archive_offer_passenger(agency_id: str, offer_id: str, offer_passenger_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    item = await db.collection("offer_passengers").update_one({"agency_id": agency_id, "offer_id": offer_id, "id": offer_passenger_id}, {"status": "archived"})
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer passenger not found.")
    return {"offer_passenger": item}


@router.get("/offers/{offer_id}/route-alternatives")
async def list_routes(agency_id: str, offer_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    await get_offer_or_404(db, agency_id, offer_id)
    return {"items": await db.collection("offer_route_alternatives").find_many({"agency_id": agency_id, "offer_id": offer_id})}


@router.post("/offers/{offer_id}/route-alternatives", status_code=status.HTTP_201_CREATED)
async def create_route(agency_id: str, offer_id: str, payload: OfferRouteAlternativeCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_offer_or_404(db, agency_id, offer_id)
    active = [r for r in await db.collection("offer_route_alternatives").find_many({"agency_id": agency_id, "offer_id": offer_id}) if r.get("status") != "withdrawn"]
    if len(active) >= 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An offer can have at most 3 route alternatives.")
    route = OfferRouteAlternative(agency_id=agency_id, offer_id=offer_id, **payload.model_dump(mode="json"))
    created = await db.collection("offer_route_alternatives").insert_one(route.model_dump(mode="json"))
    offer = await recalc_offer(db, agency_id, offer_id)
    await write_offer_timeline(db, agency_id, offer_id, user["id"], "offer.route_created", "Route alternative added", route.title)
    return {"route_alternative": created, "offer": offer}


@router.put("/offers/{offer_id}/route-alternatives/{route_id}")
async def update_route(agency_id: str, offer_id: str, route_id: str, payload: OfferRouteAlternativeUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    route = await db.collection("offer_route_alternatives").update_one({"agency_id": agency_id, "offer_id": offer_id, "id": route_id}, clean_updates(payload))
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route alternative not found.")
    offer = await recalc_offer(db, agency_id, offer_id)
    return {"route_alternative": route, "offer": offer}


@router.post("/offers/{offer_id}/route-alternatives/{route_id}/archive")
async def archive_route(agency_id: str, offer_id: str, route_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    route = await db.collection("offer_route_alternatives").update_one({"agency_id": agency_id, "offer_id": offer_id, "id": route_id}, {"status": "withdrawn"})
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route alternative not found.")
    offer = await recalc_offer(db, agency_id, offer_id)
    return {"route_alternative": route, "offer": offer}


@router.get("/offers/{offer_id}/route-alternatives/{route_id}/segments")
async def list_segments(agency_id: str, offer_id: str, route_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    await get_route_or_404(db, agency_id, offer_id, route_id)
    return {"items": await db.collection("offer_segments").find_many({"agency_id": agency_id, "offer_id": offer_id, "route_alternative_id": route_id})}


@router.post("/offers/{offer_id}/route-alternatives/{route_id}/segments", status_code=status.HTTP_201_CREATED)
async def create_segment(agency_id: str, offer_id: str, route_id: str, payload: OfferSegmentCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_route_or_404(db, agency_id, offer_id, route_id)
    segment = OfferSegment(agency_id=agency_id, offer_id=offer_id, route_alternative_id=route_id, **payload.model_dump(mode="json"))
    created = await db.collection("offer_segments").insert_one(segment.model_dump(mode="json"))
    return {"segment": created}


@router.put("/offers/{offer_id}/route-alternatives/{route_id}/segments/{segment_id}")
async def update_segment(agency_id: str, offer_id: str, route_id: str, segment_id: str, payload: OfferSegmentUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    segment = await db.collection("offer_segments").update_one({"agency_id": agency_id, "offer_id": offer_id, "route_alternative_id": route_id, "id": segment_id}, clean_updates(payload))
    if not segment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Segment not found.")
    return {"segment": segment}


@router.post("/offers/{offer_id}/route-alternatives/{route_id}/segments/{segment_id}/archive")
async def archive_segment(agency_id: str, offer_id: str, route_id: str, segment_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    segment = await db.collection("offer_segments").update_one({"agency_id": agency_id, "offer_id": offer_id, "route_alternative_id": route_id, "id": segment_id}, {"segment_status": "info_only"})
    if not segment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Segment not found.")
    return {"segment": segment}


@router.get("/offers/{offer_id}/route-alternatives/{route_id}/fare-options")
async def list_fares(agency_id: str, offer_id: str, route_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    await get_route_or_404(db, agency_id, offer_id, route_id)
    return {"items": await db.collection("offer_fare_options").find_many({"agency_id": agency_id, "offer_id": offer_id, "route_alternative_id": route_id})}


@router.post("/offers/{offer_id}/route-alternatives/{route_id}/fare-options", status_code=status.HTTP_201_CREATED)
async def create_fare(agency_id: str, offer_id: str, route_id: str, payload: OfferFareOptionCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_route_or_404(db, agency_id, offer_id, route_id)
    active = [f for f in await db.collection("offer_fare_options").find_many({"agency_id": agency_id, "offer_id": offer_id, "route_alternative_id": route_id}) if f.get("status") != "withdrawn"]
    if len(active) >= 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A route alternative can have at most 3 fare options.")
    data = payload.model_dump(mode="json")
    if not data.get("total_amount"):
        data["total_amount"] = float(data.get("base_fare_amount") or 0) + float(data.get("taxes_amount") or 0) + float(data.get("airline_fees_amount") or 0) + float(data.get("agency_service_fee_amount") or 0)
    fare = OfferFareOption(agency_id=agency_id, offer_id=offer_id, route_alternative_id=route_id, **data)
    created = await db.collection("offer_fare_options").insert_one(fare.model_dump(mode="json"))
    offer = await recalc_offer(db, agency_id, offer_id)
    return {"fare_option": created, "offer": offer}


@router.put("/offers/{offer_id}/route-alternatives/{route_id}/fare-options/{fare_option_id}")
async def update_fare(agency_id: str, offer_id: str, route_id: str, fare_option_id: str, payload: OfferFareOptionUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    updates = clean_updates(payload)
    fare = await db.collection("offer_fare_options").update_one({"agency_id": agency_id, "offer_id": offer_id, "route_alternative_id": route_id, "id": fare_option_id}, updates)
    if not fare:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fare option not found.")
    offer = await recalc_offer(db, agency_id, offer_id)
    return {"fare_option": fare, "offer": offer}


@router.post("/offers/{offer_id}/route-alternatives/{route_id}/fare-options/{fare_option_id}/archive")
async def archive_fare(agency_id: str, offer_id: str, route_id: str, fare_option_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    fare = await db.collection("offer_fare_options").update_one({"agency_id": agency_id, "offer_id": offer_id, "route_alternative_id": route_id, "id": fare_option_id}, {"status": "withdrawn"})
    if not fare:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fare option not found.")
    offer = await recalc_offer(db, agency_id, offer_id)
    return {"fare_option": fare, "offer": offer}


@router.get("/offers/{offer_id}/fare-options/{fare_option_id}/price-lines")
async def list_price_lines(agency_id: str, offer_id: str, fare_option_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    await get_fare_or_404(db, agency_id, offer_id, fare_option_id)
    return {"items": await db.collection("offer_price_lines").find_many({"agency_id": agency_id, "offer_id": offer_id, "fare_option_id": fare_option_id, "status": "active"})}


@router.post("/offers/{offer_id}/fare-options/{fare_option_id}/price-lines", status_code=status.HTTP_201_CREATED)
async def create_price_line(agency_id: str, offer_id: str, fare_option_id: str, payload: OfferPriceLineCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    fare = await get_fare_or_404(db, agency_id, offer_id, fare_option_id)
    data = payload.model_dump(mode="json")
    if data.get("total_amount") is None:
        data["total_amount"] = float(data.get("quantity") or 1) * float(data.get("unit_amount") or 0)
    line = OfferPriceLine(agency_id=agency_id, offer_id=offer_id, route_alternative_id=fare["route_alternative_id"], fare_option_id=fare_option_id, **data)
    created = await db.collection("offer_price_lines").insert_one(line.model_dump(mode="json"))
    return {"price_line": created}


@router.put("/offers/{offer_id}/fare-options/{fare_option_id}/price-lines/{line_id}")
async def update_price_line(agency_id: str, offer_id: str, fare_option_id: str, line_id: str, payload: OfferPriceLineUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    line = await db.collection("offer_price_lines").update_one({"agency_id": agency_id, "offer_id": offer_id, "fare_option_id": fare_option_id, "id": line_id}, clean_updates(payload))
    if not line:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Price line not found.")
    return {"price_line": line}


@router.post("/offers/{offer_id}/fare-options/{fare_option_id}/price-lines/{line_id}/archive")
async def archive_price_line(agency_id: str, offer_id: str, fare_option_id: str, line_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    line = await db.collection("offer_price_lines").update_one({"agency_id": agency_id, "offer_id": offer_id, "fare_option_id": fare_option_id, "id": line_id}, {"status": "archived"})
    if not line:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Price line not found.")
    return {"price_line": line}


@router.get("/offers/{offer_id}/service-checks")
async def list_service_checks(agency_id: str, offer_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    await get_offer_or_404(db, agency_id, offer_id)
    return {"items": await db.collection("offer_service_checks").find_many({"agency_id": agency_id, "offer_id": offer_id, "status": "active"})}


@router.post("/offers/{offer_id}/service-checks", status_code=status.HTTP_201_CREATED)
async def create_service_check(agency_id: str, offer_id: str, payload: OfferServiceCheckCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_offer_or_404(db, agency_id, offer_id)
    item = OfferServiceCheck(agency_id=agency_id, offer_id=offer_id, **payload.model_dump(mode="json"))
    created = await db.collection("offer_service_checks").insert_one(item.model_dump(mode="json"))
    return {"service_check": created}


@router.put("/offers/{offer_id}/service-checks/{check_id}")
async def update_service_check(agency_id: str, offer_id: str, check_id: str, payload: OfferServiceCheckUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    item = await db.collection("offer_service_checks").update_one({"agency_id": agency_id, "offer_id": offer_id, "id": check_id}, clean_updates(payload))
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service check not found.")
    return {"service_check": item}


@router.post("/offers/{offer_id}/service-checks/{check_id}/archive")
async def archive_service_check(agency_id: str, offer_id: str, check_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    item = await db.collection("offer_service_checks").update_one({"agency_id": agency_id, "offer_id": offer_id, "id": check_id}, {"status": "archived"})
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service check not found.")
    return {"service_check": item}


@router.get("/offers/{offer_id}/timeline")
async def offer_timeline(agency_id: str, offer_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    await get_offer_or_404(db, agency_id, offer_id)
    return {"items": await db.collection("offer_timeline_events").find_many({"agency_id": agency_id, "offer_id": offer_id})}
