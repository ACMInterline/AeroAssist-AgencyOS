from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    AuditEvent,
    PassengerMergeAudit,
    PassengerMergeRequest,
    PassengerProfile,
    PassengerProfileCreate,
    PassengerProfileUpdate,
    new_id,
)
from services.tenant_service import assert_agency_access, require_any_agency_role

router = APIRouter(prefix="/api/agencies/{agency_id}", tags=["passengers"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin", "agency_agent"]
MERGE_ROLES = ["agency_owner", "agency_admin"]


def clean_updates(payload) -> dict:
    return payload.model_dump(exclude_unset=True, mode="json")


def includes_search(record: dict, search: Optional[str], fields: list[str]) -> bool:
    if not search:
        return True
    needle = search.lower()
    return any(needle in str(record.get(field) or "").lower() for field in fields)


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


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


async def require_write(db: Database, agency_id: str, user: dict) -> None:
    if user.get("global_role") not in {"platform_owner", "platform_admin"}:
        await require_any_agency_role(db, agency_id, user, WRITE_ROLES)


async def get_passenger_or_404(db: Database, agency_id: str, passenger_id: str) -> dict:
    passenger = await db.collection("passenger_profiles").find_one({"agency_id": agency_id, "id": passenger_id})
    if passenger is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Passenger not found.")
    return passenger


@router.get("/passengers")
async def list_passengers(
    agency_id: str,
    search: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    passenger_type: Optional[str] = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    filters = {"agency_id": agency_id}
    if status_filter:
        filters["status"] = status_filter
    if passenger_type:
        filters["passenger_type"] = passenger_type
    passengers = await db.collection("passenger_profiles").find_many(filters)
    passengers = [
        passenger
        for passenger in passengers
        if includes_search(
            passenger,
            search,
            ["display_name", "first_name", "middle_name", "last_name", "nationality", "residence_country"],
        )
    ]
    return {"items": passengers}


@router.post("/passengers", status_code=status.HTTP_201_CREATED)
async def create_passenger(
    agency_id: str,
    payload: PassengerProfileCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    data = payload.model_dump(mode="json")
    if not data.get("display_name"):
        middle = f" {data['middle_name']}" if data.get("middle_name") else ""
        data["display_name"] = f"{data['first_name']}{middle} {data['last_name']}"
    passenger = PassengerProfile(agency_id=agency_id, **data)
    created = await db.collection("passenger_profiles").insert_one(passenger.model_dump(mode="json"))
    await write_audit(
        db,
        agency_id,
        user["id"],
        "passenger.created",
        "passenger_profile",
        passenger.id,
        f"Created passenger {passenger.display_name}.",
    )
    return {"passenger": created}


@router.get("/passengers/{passenger_id}")
async def get_passenger(
    agency_id: str,
    passenger_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    passenger = await get_passenger_or_404(db, agency_id, passenger_id)
    relationships = await db.collection("client_passenger_relationships").find_many(
        {"agency_id": agency_id, "passenger_id": passenger_id}
    )
    client_ids = {relationship["client_id"] for relationship in relationships}
    clients = [
        client
        for client in await db.collection("client_profiles").find_many({"agency_id": agency_id})
        if client["id"] in client_ids
    ]
    return {"passenger": passenger, "relationships": relationships, "clients": clients}


@router.put("/passengers/{passenger_id}")
async def update_passenger(
    agency_id: str,
    passenger_id: str,
    payload: PassengerProfileUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    await get_passenger_or_404(db, agency_id, passenger_id)
    updates = clean_updates(payload)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided.")
    passenger = await db.collection("passenger_profiles").update_one(
        {"agency_id": agency_id, "id": passenger_id},
        updates,
    )
    await write_audit(
        db,
        agency_id,
        user["id"],
        "passenger.updated",
        "passenger_profile",
        passenger_id,
        "Updated passenger profile.",
        {"fields": sorted(updates.keys())},
    )
    return {"passenger": passenger}


@router.post("/passengers/{passenger_id}/archive")
async def archive_passenger(
    agency_id: str,
    passenger_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    await get_passenger_or_404(db, agency_id, passenger_id)
    passenger = await db.collection("passenger_profiles").update_one(
        {"agency_id": agency_id, "id": passenger_id},
        {"status": "archived"},
    )
    await write_audit(
        db,
        agency_id,
        user["id"],
        "passenger.archived",
        "passenger_profile",
        passenger_id,
        "Archived passenger.",
    )
    return {"passenger": passenger}


@router.post("/passengers/{passenger_id}/restore")
async def restore_passenger(
    agency_id: str,
    passenger_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    passenger = await get_passenger_or_404(db, agency_id, passenger_id)
    if passenger.get("status") == "duplicate_merged":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Merged duplicate passengers cannot be restored.")
    restored = await db.collection("passenger_profiles").update_one(
        {"agency_id": agency_id, "id": passenger_id},
        {"status": "active"},
    )
    await write_audit(
        db,
        agency_id,
        user["id"],
        "passenger.restored",
        "passenger_profile",
        passenger_id,
        "Restored passenger.",
    )
    return {"passenger": restored}


@router.post("/passengers/{passenger_id}/merge")
async def merge_passenger(
    agency_id: str,
    passenger_id: str,
    payload: PassengerMergeRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    if user.get("global_role") not in {"platform_owner", "platform_admin"}:
        await require_any_agency_role(db, agency_id, user, MERGE_ROLES)

    source = await get_passenger_or_404(db, agency_id, passenger_id)
    target = await get_passenger_or_404(db, agency_id, payload.target_passenger_id)
    if source["id"] == target["id"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Source and target passenger must differ.")
    if source.get("status") == "duplicate_merged":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Source passenger is already merged.")

    existing_target_relationships = await db.collection("client_passenger_relationships").find_many(
        {"agency_id": agency_id, "passenger_id": target["id"]}
    )
    target_client_ids = {relationship["client_id"] for relationship in existing_target_relationships}
    source_relationships = await db.collection("client_passenger_relationships").find_many(
        {"agency_id": agency_id, "passenger_id": source["id"]}
    )
    copied_relationship_ids = []
    archived_relationship_ids = []

    for relationship in source_relationships:
        if relationship["client_id"] in target_client_ids:
            updated = await db.collection("client_passenger_relationships").update_one(
                {"agency_id": agency_id, "id": relationship["id"]},
                {"status": "archived", "notes": "Archived during duplicate passenger merge."},
            )
            archived_relationship_ids.append(updated["id"])
            continue
        new_relationship = dict(relationship)
        new_relationship["id"] = new_id()
        new_relationship["passenger_id"] = target["id"]
        new_relationship["notes"] = (new_relationship.get("notes") or "") + " Copied during duplicate passenger merge."
        copied = await db.collection("client_passenger_relationships").insert_one(new_relationship)
        copied_relationship_ids.append(copied["id"])

    merged = await db.collection("passenger_profiles").update_one(
        {"agency_id": agency_id, "id": source["id"]},
        {"status": "duplicate_merged", "merged_into_passenger_id": target["id"]},
    )
    audit = PassengerMergeAudit(
        agency_id=agency_id,
        source_passenger_id=source["id"],
        target_passenger_id=target["id"],
        merged_by_user_id=user["id"],
        reason=payload.reason,
        retained_fields_summary=payload.retained_fields_summary,
    )
    audit_doc = await db.collection("passenger_merge_audits").insert_one(audit.model_dump(mode="json"))
    await write_audit(
        db,
        agency_id,
        user["id"],
        "passenger.merged",
        "passenger_profile",
        source["id"],
        "Merged duplicate passenger profile.",
        {
            "target_passenger_id": target["id"],
            "copied_relationship_ids": copied_relationship_ids,
            "archived_relationship_ids": archived_relationship_ids,
        },
    )
    return {
        "source_passenger": merged,
        "target_passenger": target,
        "merge_audit": audit_doc,
        "summary": {
            "copied_relationship_ids": copied_relationship_ids,
            "archived_relationship_ids": archived_relationship_ids,
            "future_records_should_follow": "merged_into_passenger_id",
        },
    }


@router.get("/passengers/{passenger_id}/clients")
async def list_passenger_clients(
    agency_id: str,
    passenger_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    await get_passenger_or_404(db, agency_id, passenger_id)
    relationships = await db.collection("client_passenger_relationships").find_many(
        {"agency_id": agency_id, "passenger_id": passenger_id}
    )
    client_ids = {relationship["client_id"] for relationship in relationships}
    clients = [
        client
        for client in await db.collection("client_profiles").find_many({"agency_id": agency_id})
        if client["id"] in client_ids
    ]
    return {"relationships": relationships, "clients": clients}
