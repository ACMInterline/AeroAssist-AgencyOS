from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status

from auth import DEMO_AUTH_ENABLED, get_current_agency_context, get_current_user, require_platform_role
from config import get_settings
from database import Database, get_database
from models import (
    Agency,
    AgencyCreate,
    AgencyStaffCreate,
    AgencyStaffMembership,
    AgencyUpdate,
    AgencyWorkspace,
    AgencyWorkspaceUpdate,
    AuditEvent,
    Invitation,
    PortalActionProcessSubmit,
    PlatformUser,
    StaffInvitationCreate,
    now_utc,
)
from security import hash_token, new_raw_token, normalize_email
from services.tenant_service import require_any_agency_role

router = APIRouter(prefix="/api/agencies", tags=["agencies"])


def clean_updates(payload: AgencyUpdate | AgencyWorkspaceUpdate) -> dict:
    return payload.model_dump(exclude_unset=True, mode="json")


async def write_audit(
    db: Database,
    event_type: str,
    entity_type: str,
    entity_id: str,
    summary: str,
    actor_user_id: str | None = None,
    agency_id: str | None = None,
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


@router.get("")
async def list_agencies(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    if user.get("global_role") in {"platform_owner", "platform_admin", "platform_support"}:
        agencies = await db.collection("agencies").find_many()
    else:
        memberships = await db.collection("agency_staff_memberships").find_many({"user_id": user["id"], "status": "active"})
        agency_ids = {membership["agency_id"] for membership in memberships}
        agencies = [
            agency
            for agency in await db.collection("agencies").find_many()
            if agency["id"] in agency_ids
        ]
    return {"items": agencies}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_agency(
    payload: AgencyCreate,
    user: dict = Depends(require_platform_role(["platform_owner", "platform_admin"])),
    db: Database = Depends(get_database),
) -> dict:
    existing = await db.collection("agencies").find_one({"slug": payload.slug})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Agency slug already exists.")

    agency = Agency(**payload.model_dump(mode="json"))
    agency_doc = await db.collection("agencies").insert_one(agency.model_dump(mode="json"))
    workspace = AgencyWorkspace(agency_id=agency.id, brand_name=agency.name)
    workspace_doc = await db.collection("agency_workspaces").insert_one(workspace.model_dump(mode="json"))
    await write_audit(
        db,
        event_type="agency.created",
        entity_type="agency",
        entity_id=agency.id,
        summary=f"Created agency {agency.name}.",
        actor_user_id=user["id"],
        agency_id=agency.id,
    )
    return {"agency": agency_doc, "settings": workspace_doc}


@router.get("/{agency_id}")
async def get_agency(context: dict = Depends(get_current_agency_context)) -> dict:
    return {"agency": context["agency"], "membership": context["membership"]}


@router.put("/{agency_id}")
async def update_agency(
    agency_id: str,
    payload: AgencyUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    if user.get("global_role") not in {"platform_owner", "platform_admin"}:
        await require_any_agency_role(db, agency_id, user, ["agency_owner", "agency_admin"])

    updates = clean_updates(payload)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided.")

    agency = await db.collection("agencies").update_one({"id": agency_id}, updates)
    if agency is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found.")
    await write_audit(
        db,
        event_type="agency.updated",
        entity_type="agency",
        entity_id=agency_id,
        summary="Updated agency profile.",
        actor_user_id=user["id"],
        agency_id=agency_id,
        metadata={"fields": sorted(updates.keys())},
    )
    return {"agency": agency}


@router.get("/{agency_id}/settings")
async def get_settings(context: dict = Depends(get_current_agency_context), db: Database = Depends(get_database)) -> dict:
    settings = await db.collection("agency_workspaces").find_one({"agency_id": context["agency"]["id"]})
    if settings is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency settings not found.")
    return {"settings": settings}


@router.put("/{agency_id}/settings")
async def update_settings(
    agency_id: str,
    payload: AgencyWorkspaceUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_any_agency_role(db, agency_id, user, ["agency_owner", "agency_admin"])
    updates = clean_updates(payload)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided.")

    settings = await db.collection("agency_workspaces").update_one({"agency_id": agency_id}, updates)
    if settings is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency settings not found.")
    await write_audit(
        db,
        event_type="agency.settings_updated",
        entity_type="agency_workspace",
        entity_id=settings["id"],
        summary="Updated agency workspace settings.",
        actor_user_id=user["id"],
        agency_id=agency_id,
        metadata={"fields": sorted(updates.keys())},
    )
    return {"settings": settings}


@router.get("/{agency_id}/staff")
async def list_staff(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_any_agency_role(
        db,
        agency_id,
        user,
        ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"],
    )
    memberships = await db.collection("agency_staff_memberships").find_many({"agency_id": agency_id})
    users_by_id = {
        staff_user["id"]: staff_user
        for staff_user in await db.collection("platform_users").find_many()
    }
    return {
        "items": [
            {"membership": membership, "user": users_by_id.get(membership["user_id"])}
            for membership in memberships
        ]
    }


@router.post("/{agency_id}/staff/invitations", status_code=status.HTTP_201_CREATED)
async def create_staff_invitation(
    agency_id: str,
    payload: StaffInvitationCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_any_agency_role(db, agency_id, user, ["agency_owner", "agency_admin"])
    agency = await db.collection("agencies").find_one({"id": agency_id})
    if agency is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found.")

    staff_user = await db.collection("platform_users").find_one({"email": payload.email})
    if staff_user is None:
        staff_user = await db.collection("platform_users").insert_one(
            PlatformUser(email=payload.email, full_name=payload.full_name, status="invited").model_dump(mode="json")
        )

    membership = await db.collection("agency_staff_memberships").find_one(
        {"agency_id": agency_id, "user_id": staff_user["id"]}
    )
    if membership is None:
        membership = await db.collection("agency_staff_memberships").insert_one(
            AgencyStaffMembership(
                agency_id=agency_id,
                user_id=staff_user["id"],
                agency_role=payload.agency_role,
                status="invited",
            ).model_dump(mode="json")
        )

    raw_token = new_raw_token()
    invitation = Invitation(
        agency_id=agency_id,
        invited_email=payload.email,
        normalized_email=normalize_email(payload.email),
        invitation_type="agency_staff",
        target_role=payload.agency_role,
        target_user_id=staff_user["id"],
        invited_by_user_id=user["id"],
        token_hash=hash_token(raw_token),
        expires_at=now_utc() + timedelta(hours=get_settings().invitation_expiry_hours),
    )
    invitation_doc = await db.collection("invitations").insert_one(invitation.model_dump(mode="json"))
    response = {"invitation": {key: value for key, value in invitation_doc.items() if key != "token_hash"}, "membership": membership}
    if DEMO_AUTH_ENABLED and not get_settings().is_production:
        response["dev_invitation_token"] = raw_token
        response["dev_invitation_link"] = f"/login?invite={raw_token}"
    return response


@router.post("/{agency_id}/staff", status_code=status.HTTP_201_CREATED)
async def create_staff(
    agency_id: str,
    payload: AgencyStaffCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_any_agency_role(db, agency_id, user, ["agency_owner", "agency_admin"])
    agency = await db.collection("agencies").find_one({"id": agency_id})
    if agency is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found.")

    staff_user = await db.collection("platform_users").find_one({"email": payload.email})
    if staff_user is None:
        staff_user_model = PlatformUser(
            email=payload.email,
            full_name=payload.full_name,
            status=payload.status,
        )
        staff_user = await db.collection("platform_users").insert_one(staff_user_model.model_dump(mode="json"))

    existing = await db.collection("agency_staff_memberships").find_one(
        {"agency_id": agency_id, "user_id": staff_user["id"]}
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Staff membership already exists.")

    membership = AgencyStaffMembership(
        agency_id=agency_id,
        user_id=staff_user["id"],
        agency_role=payload.agency_role,
        status=payload.status,
        joined_at=staff_user["created_at"] if payload.status == "active" else None,
    )
    membership_doc = await db.collection("agency_staff_memberships").insert_one(membership.model_dump(mode="json"))
    await write_audit(
        db,
        event_type="agency.staff_created",
        entity_type="agency_staff_membership",
        entity_id=membership.id,
        summary=f"Added {payload.full_name} to agency staff.",
        actor_user_id=user["id"],
        agency_id=agency_id,
    )
    return {"membership": membership_doc, "user": staff_user}


@router.get("/{agency_id}/portal-actions")
async def list_portal_actions(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_any_agency_role(
        db,
        agency_id,
        user,
        ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"],
    )
    actions = await db.collection("portal_action_events").find_many({"agency_id": agency_id})
    clients_by_id = {
        client["id"]: client
        for client in await db.collection("client_profiles").find_many({"agency_id": agency_id})
    }
    return {
        "items": [
            {
                "action": action,
                "client": clients_by_id.get(action.get("client_id")),
            }
            for action in actions
        ]
    }


@router.post("/{agency_id}/portal-actions/{action_id}/process")
async def process_portal_action(
    agency_id: str,
    action_id: str,
    payload: PortalActionProcessSubmit | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_any_agency_role(db, agency_id, user, ["agency_owner", "agency_admin", "agency_agent"])
    payload = payload or PortalActionProcessSubmit()
    if payload.status not in {"processed", "cancelled", "archived"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Portal action can only be marked processed, cancelled, or archived.")
    action = await db.collection("portal_action_events").update_one(
        {"agency_id": agency_id, "id": action_id},
        {"status": payload.status},
    )
    if action is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portal action not found.")
    await write_audit(
        db,
        event_type="portal_action.processed",
        entity_type="portal_action_event",
        entity_id=action_id,
        summary=f"Marked portal action {payload.status}.",
        actor_user_id=user["id"],
        agency_id=agency_id,
    )
    return {"action": action}
