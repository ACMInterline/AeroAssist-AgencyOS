import os
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import DEMO_AUTH_ENABLED, get_current_user
from database import Database, get_database
from models import (
    AuditEvent,
    ClientPassengerRelationship,
    ClientPassengerRelationshipCreate,
    ClientPassengerRelationshipUpdate,
    ClientPortalInvitationCreate,
    ClientProfile,
    ClientProfileCreate,
    ClientProfileUpdate,
    Invitation,
    PortalAccessMapping,
    now_utc,
)
from security import hash_token, new_raw_token, normalize_email
from services.tenant_service import assert_agency_access, require_any_agency_role

router = APIRouter(prefix="/api/agencies/{agency_id}", tags=["clients"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin", "agency_agent"]


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


async def get_relationship_or_404(db: Database, agency_id: str, relationship_id: str) -> dict:
    relationship = await db.collection("client_passenger_relationships").find_one(
        {"agency_id": agency_id, "id": relationship_id}
    )
    if relationship is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relationship not found.")
    return relationship


@router.get("/clients")
async def list_clients(
    agency_id: str,
    search: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    client_type: Optional[str] = None,
    portal_status: Optional[str] = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    filters = {"agency_id": agency_id}
    if status_filter:
        filters["status"] = status_filter
    if client_type:
        filters["client_type"] = client_type
    if portal_status:
        filters["portal_status"] = portal_status
    clients = await db.collection("client_profiles").find_many(filters)
    clients = [
        client
        for client in clients
        if includes_search(client, search, ["display_name", "legal_name", "primary_email", "primary_phone", "city"])
    ]
    return {"items": clients}


@router.post("/clients", status_code=status.HTTP_201_CREATED)
async def create_client(
    agency_id: str,
    payload: ClientProfileCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    client = ClientProfile(agency_id=agency_id, **payload.model_dump(mode="json"))
    created = await db.collection("client_profiles").insert_one(client.model_dump(mode="json"))
    await write_audit(
        db,
        agency_id,
        user["id"],
        "client.created",
        "client_profile",
        client.id,
        f"Created client {client.display_name}.",
    )
    return {"client": created}


@router.get("/clients/{client_id}")
async def get_client(
    agency_id: str,
    client_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    client = await get_client_or_404(db, agency_id, client_id)
    relationships = await db.collection("client_passenger_relationships").find_many(
        {"agency_id": agency_id, "client_id": client_id}
    )
    passenger_ids = {relationship["passenger_id"] for relationship in relationships}
    passengers = [
        passenger
        for passenger in await db.collection("passenger_profiles").find_many({"agency_id": agency_id})
        if passenger["id"] in passenger_ids
    ]
    return {"client": client, "relationships": relationships, "passengers": passengers}


@router.put("/clients/{client_id}")
async def update_client(
    agency_id: str,
    client_id: str,
    payload: ClientProfileUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    await get_client_or_404(db, agency_id, client_id)
    updates = clean_updates(payload)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided.")
    client = await db.collection("client_profiles").update_one({"agency_id": agency_id, "id": client_id}, updates)
    await write_audit(
        db,
        agency_id,
        user["id"],
        "client.updated",
        "client_profile",
        client_id,
        "Updated client profile.",
        {"fields": sorted(updates.keys())},
    )
    return {"client": client}


@router.post("/clients/{client_id}/archive")
async def archive_client(
    agency_id: str,
    client_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    await get_client_or_404(db, agency_id, client_id)
    client = await db.collection("client_profiles").update_one(
        {"agency_id": agency_id, "id": client_id},
        {"status": "archived", "portal_status": "archived"},
    )
    await write_audit(db, agency_id, user["id"], "client.archived", "client_profile", client_id, "Archived client.")
    return {"client": client}


@router.post("/clients/{client_id}/restore")
async def restore_client(
    agency_id: str,
    client_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    await get_client_or_404(db, agency_id, client_id)
    client = await db.collection("client_profiles").update_one(
        {"agency_id": agency_id, "id": client_id},
        {"status": "active", "portal_status": "no_portal_access"},
    )
    await write_audit(db, agency_id, user["id"], "client.restored", "client_profile", client_id, "Restored client.")
    return {"client": client}


@router.post("/clients/{client_id}/portal-invitation", status_code=status.HTTP_201_CREATED)
async def create_client_portal_invitation(
    agency_id: str,
    client_id: str,
    payload: ClientPortalInvitationCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    client = await get_client_or_404(db, agency_id, client_id)
    invited_email = payload.email or client.get("primary_email")
    if not invited_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Client portal invitation requires an email.")
    display_name = payload.display_name or client.get("display_name") or invited_email

    mapping = await db.collection("portal_access_mappings").find_one({"agency_id": agency_id, "client_id": client_id})
    if mapping is None:
        mapping = await db.collection("portal_access_mappings").insert_one(
            PortalAccessMapping(
                agency_id=agency_id,
                client_id=client_id,
                user_email=invited_email,
                portal_status="invited",
                display_name=display_name,
            ).model_dump(mode="json")
        )
    else:
        mapping = await db.collection("portal_access_mappings").update_one(
            {"id": mapping["id"]},
            {"user_email": invited_email, "portal_status": "invited", "display_name": display_name},
        )

    client = await db.collection("client_profiles").update_one(
        {"agency_id": agency_id, "id": client_id},
        {"portal_status": "invited"},
    )
    raw_token = new_raw_token()
    invitation = Invitation(
        agency_id=agency_id,
        invited_email=invited_email,
        normalized_email=normalize_email(invited_email),
        invitation_type="client_portal",
        target_client_id=client_id,
        invited_by_user_id=user["id"],
        token_hash=hash_token(raw_token),
        expires_at=now_utc() + timedelta(hours=int(os.getenv("INVITATION_EXPIRY_HOURS", "72"))),
    )
    invitation_doc = await db.collection("invitations").insert_one(invitation.model_dump(mode="json"))
    await write_audit(
        db,
        agency_id,
        user["id"],
        "client.portal_invited",
        "client_profile",
        client_id,
        "Created client portal invitation.",
    )
    response = {
        "client": client,
        "portal_mapping": mapping,
        "invitation": {key: value for key, value in invitation_doc.items() if key != "token_hash"},
    }
    if DEMO_AUTH_ENABLED or os.getenv("AEROASSIST_DB_MODE", "memory") == "memory":
        response["dev_invitation_token"] = raw_token
        response["dev_invitation_link"] = f"/login?invite={raw_token}"
    return response


@router.get("/client-passenger-relationships")
async def list_relationships(
    agency_id: str,
    status_filter: Optional[str] = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    filters = {"agency_id": agency_id}
    if status_filter:
        filters["status"] = status_filter
    return {"items": await db.collection("client_passenger_relationships").find_many(filters)}


@router.post("/client-passenger-relationships", status_code=status.HTTP_201_CREATED)
async def create_relationship(
    agency_id: str,
    payload: ClientPassengerRelationshipCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    await get_client_or_404(db, agency_id, payload.client_id)
    await get_passenger_or_404(db, agency_id, payload.passenger_id)
    existing = await db.collection("client_passenger_relationships").find_one(
        {"agency_id": agency_id, "client_id": payload.client_id, "passenger_id": payload.passenger_id}
    )
    if existing and existing.get("status") != "archived":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Active relationship already exists.")
    relationship = ClientPassengerRelationship(agency_id=agency_id, **payload.model_dump(mode="json"))
    created = await db.collection("client_passenger_relationships").insert_one(relationship.model_dump(mode="json"))
    await write_audit(
        db,
        agency_id,
        user["id"],
        "relationship.created",
        "client_passenger_relationship",
        relationship.id,
        "Linked client and passenger.",
        {"client_id": payload.client_id, "passenger_id": payload.passenger_id},
    )
    return {"relationship": created}


@router.put("/client-passenger-relationships/{relationship_id}")
async def update_relationship(
    agency_id: str,
    relationship_id: str,
    payload: ClientPassengerRelationshipUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    await get_relationship_or_404(db, agency_id, relationship_id)
    updates = clean_updates(payload)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided.")
    relationship = await db.collection("client_passenger_relationships").update_one(
        {"agency_id": agency_id, "id": relationship_id},
        updates,
    )
    await write_audit(
        db,
        agency_id,
        user["id"],
        "relationship.updated",
        "client_passenger_relationship",
        relationship_id,
        "Updated client/passenger relationship.",
        {"fields": sorted(updates.keys())},
    )
    return {"relationship": relationship}


@router.post("/client-passenger-relationships/{relationship_id}/archive")
async def archive_relationship(
    agency_id: str,
    relationship_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    await get_relationship_or_404(db, agency_id, relationship_id)
    relationship = await db.collection("client_passenger_relationships").update_one(
        {"agency_id": agency_id, "id": relationship_id},
        {"status": "archived"},
    )
    await write_audit(
        db,
        agency_id,
        user["id"],
        "relationship.archived",
        "client_passenger_relationship",
        relationship_id,
        "Archived client/passenger relationship.",
    )
    return {"relationship": relationship}


@router.get("/clients/{client_id}/passengers")
async def list_client_passengers(
    agency_id: str,
    client_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    await get_client_or_404(db, agency_id, client_id)
    relationships = await db.collection("client_passenger_relationships").find_many(
        {"agency_id": agency_id, "client_id": client_id}
    )
    passenger_ids = {relationship["passenger_id"] for relationship in relationships}
    passengers = [
        passenger
        for passenger in await db.collection("passenger_profiles").find_many({"agency_id": agency_id})
        if passenger["id"] in passenger_ids
    ]
    return {"relationships": relationships, "passengers": passengers}
