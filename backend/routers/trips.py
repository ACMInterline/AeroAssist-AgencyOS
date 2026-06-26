from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import TripDossierCreate, TripDossierUpdate
from services.tenant_service import assert_agency_access, require_any_agency_role
from services.trip_dossier_service import (
    create_manual_trip,
    create_trip_from_request,
    get_trip_or_404,
    link_request_to_trip,
    rebuild_trip_summary,
    unlink_request_from_trip,
    write_trip_audit,
    write_trip_timeline,
)

router = APIRouter(prefix="/api/agencies/{agency_id}/trips", tags=["trips"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin", "agency_agent"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


async def require_write(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin"}:
        await require_any_agency_role(db, agency_id, user, WRITE_ROLES)


def clean_updates(payload: Any) -> dict:
    return payload.model_dump(exclude_unset=True, mode="json")


def matches_search(record: dict, search: Optional[str], client: dict | None = None) -> bool:
    if not search:
        return True
    needle = search.lower()
    fields = [
        record.get("trip_reference"),
        record.get("trip_title"),
        record.get("route_summary"),
        record.get("service_summary"),
        client.get("display_name") if client else None,
    ]
    return any(needle in str(value or "").lower() for value in fields)


async def trip_detail_payload(db: Database, agency_id: str, trip: dict) -> dict:
    linked_requests = []
    for request_id in trip.get("linked_request_ids", []):
        request = await db.collection("travel_requests").find_one({"agency_id": agency_id, "id": request_id})
        if request:
            linked_requests.append(request)
    client = None
    if trip.get("primary_client_id"):
        client = await db.collection("client_profiles").find_one({"agency_id": agency_id, "id": trip["primary_client_id"]})
    return {
        "trip": trip,
        "client": client,
        "linked_requests": linked_requests,
        "passengers": await db.collection("trip_passengers").find_many({"agency_id": agency_id, "trip_id": trip["id"]}),
        "segments": await db.collection("trip_segments").find_many({"agency_id": agency_id, "trip_id": trip["id"]}),
        "services": await db.collection("trip_service_items").find_many({"agency_id": agency_id, "trip_id": trip["id"]}),
        "timeline": await db.collection("trip_timeline_events").find_many({"agency_id": agency_id, "trip_id": trip["id"]}),
    }


@router.get("")
async def list_trips(
    agency_id: str,
    search: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    trip_type: Optional[str] = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    filters = {"agency_id": agency_id}
    if status_filter:
        filters["trip_status"] = status_filter
    if trip_type:
        filters["trip_type"] = trip_type
    trips = await db.collection("trip_dossiers").find_many(filters)
    clients = {client["id"]: client for client in await db.collection("client_profiles").find_many({"agency_id": agency_id})}
    items = []
    for trip in trips:
        client = clients.get(trip.get("primary_client_id"))
        if matches_search(trip, search, client):
            items.append({**trip, "client": client, "linked_request_count": len(trip.get("linked_request_ids", []))})
    items.sort(key=lambda item: str(item.get("updated_at") or ""), reverse=True)
    return {"items": items}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_trip(
    agency_id: str,
    payload: TripDossierCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    created = await create_manual_trip(db, agency_id, payload, user["id"])
    return {"trip": created}


@router.get("/{trip_id}")
async def get_trip(agency_id: str, trip_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    trip = await get_trip_or_404(db, agency_id, trip_id)
    return await trip_detail_payload(db, agency_id, trip)


@router.put("/{trip_id}")
async def update_trip(agency_id: str, trip_id: str, payload: TripDossierUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    trip = await get_trip_or_404(db, agency_id, trip_id)
    updates = clean_updates(payload)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided.")
    updates["updated_by_user_id"] = user["id"]
    updated = await db.collection("trip_dossiers").update_one({"agency_id": agency_id, "id": trip_id}, updates)
    await write_trip_audit(db, agency_id, user["id"], "trip_dossier_updated", trip_id, "Updated trip dossier.", {"fields": sorted(updates.keys())})
    await write_trip_timeline(db, agency_id, trip.get("workspace_id"), trip_id, user["id"], "trip_dossier_updated", "Trip dossier updated", ", ".join(sorted(updates.keys())))
    return {"trip": updated}


@router.post("/{trip_id}/archive")
async def archive_trip(agency_id: str, trip_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    trip = await get_trip_or_404(db, agency_id, trip_id)
    updated = await db.collection("trip_dossiers").update_one(
        {"agency_id": agency_id, "id": trip_id},
        {"trip_status": "archived", "archived_at": datetime.now(timezone.utc), "updated_by_user_id": user["id"]},
    )
    await write_trip_audit(db, agency_id, user["id"], "trip_dossier_archived", trip_id, f"Archived trip {trip.get('trip_reference')}.")
    await write_trip_timeline(db, agency_id, trip.get("workspace_id"), trip_id, user["id"], "trip_dossier_archived", "Trip dossier archived")
    return {"trip": updated}


@router.post("/from-request/{request_id}", status_code=status.HTTP_201_CREATED)
async def create_from_request(agency_id: str, request_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    trip = await create_trip_from_request(db, agency_id, request_id, user["id"])
    return {"trip": trip}


@router.post("/{trip_id}/link-request/{request_id}")
async def link_request(agency_id: str, trip_id: str, request_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    trip = await link_request_to_trip(db, agency_id, trip_id, request_id, user["id"])
    return {"trip": trip}


@router.post("/{trip_id}/unlink-request/{request_id}")
async def unlink_request(agency_id: str, trip_id: str, request_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    trip = await unlink_request_from_trip(db, agency_id, trip_id, request_id, user["id"])
    return {"trip": trip}


@router.post("/{trip_id}/rebuild-summary")
async def rebuild_summary(agency_id: str, trip_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    trip = await rebuild_trip_summary(db, agency_id, trip_id, user["id"])
    return {"trip": trip}
