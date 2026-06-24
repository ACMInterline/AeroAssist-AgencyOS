from datetime import timedelta

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status

from auth import (
    DEFAULT_INVITATION_EXPIRY_HOURS,
    DEMO_AUTH_ENABLED,
    DEMO_PASSWORD,
    create_session,
    ensure_auth_identity,
    get_current_identity,
    resolve_auth_payload,
    safe_identity,
    token_response,
)
from config import get_settings
from database import Database, get_database
from models import (
    AgencyStaffMembership,
    AuditEvent,
    ChangePasswordRequest,
    InvitationAcceptRequest,
    LoginRequest,
    PlatformUser,
    now_utc,
)
from security import hash_password, hash_token, normalize_email, verify_password
from services.seed_service import seed_core_data

router = APIRouter(prefix="/api/auth", tags=["auth"])


def parse_dt(value: object):
    if isinstance(value, str):
        from datetime import datetime

        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return value


def safe_auth_response(payload: dict, raw_token: str | None = None, session: dict | None = None) -> dict:
    response = {"auth": payload}
    if raw_token and session:
        response["session"] = token_response(raw_token, session)
    return response


def safe_invitation_record(invitation: dict) -> dict:
    return {key: value for key, value in invitation.items() if key != "token_hash"}


async def write_auth_audit(
    db: Database,
    event_type: str,
    entity_type: str,
    entity_id: str,
    summary: str,
    agency_id: str | None = None,
    actor_user_id: str | None = None,
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


async def find_pending_invitation_by_token(db: Database, token: str) -> dict:
    invitation = await db.collection("invitations").find_one({"token_hash": hash_token(token)})
    if not invitation or invitation.get("status") != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation is invalid.")
    expires_at = parse_dt(invitation["expires_at"])
    if expires_at <= now_utc():
        await db.collection("invitations").update_one({"id": invitation["id"]}, {"status": "expired"})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation has expired.")
    return invitation


@router.get("/me")
async def read_me(
    authorization: str | None = Header(default=None),
    x_demo_user_email: str | None = Header(default=None),
    db: Database = Depends(get_database),
) -> dict:
    from auth import get_current_identity

    identity = await get_current_identity(authorization, x_demo_user_email, db)
    payload = await resolve_auth_payload(db, identity)
    payload["demo_auth_enabled"] = DEMO_AUTH_ENABLED
    return payload


@router.post("/login")
async def login(payload: LoginRequest, request: Request, db: Database = Depends(get_database)) -> dict:
    if get_settings().seed_on_startup:
        await seed_core_data(db)
    normalized = normalize_email(payload.email)
    identity = await db.collection("auth_identities").find_one({"normalized_email": normalized})
    if not identity or not verify_password(payload.password, identity.get("password_hash", "")):
        if identity:
            await db.collection("auth_identities").update_one(
                {"id": identity["id"]},
                {"failed_login_count": identity.get("failed_login_count", 0) + 1},
            )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
    if identity.get("status") in {"suspended", "archived", "invited"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account cannot log in.")

    updated_identity = await db.collection("auth_identities").update_one(
        {"id": identity["id"]},
        {"last_login_at": now_utc(), "failed_login_count": 0},
    )
    session_bundle = await create_session(db, updated_identity or identity, request)
    payload_out = await resolve_auth_payload(db, updated_identity or identity)
    return safe_auth_response(payload_out, session_bundle["raw_token"], session_bundle["session"])


@router.post("/logout")
async def logout(authorization: str | None = Header(default=None), db: Database = Depends(get_database)) -> dict:
    if authorization and authorization.lower().startswith("bearer "):
        raw_token = authorization.split(" ", 1)[1].strip()
        await db.collection("auth_sessions").update_one(
            {"token_hash": hash_token(raw_token), "status": "active"},
            {"status": "revoked"},
        )
    return {"ok": True}


@router.post("/demo-login")
async def demo_login(payload: LoginRequest, request: Request, db: Database = Depends(get_database)) -> dict:
    if not DEMO_AUTH_ENABLED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demo auth is disabled.")
    if get_settings().seed_on_startup:
        await seed_core_data(db)
    identity = await db.collection("auth_identities").find_one({"normalized_email": normalize_email(payload.email)})
    if identity is None:
        user = await db.collection("platform_users").find_one({"email": payload.email})
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demo user not found.")
        identity = await ensure_auth_identity(
            db,
            user["email"],
            payload.password or DEMO_PASSWORD,
            "platform_user" if user.get("global_role") else "agency_staff",
        )
    session_bundle = await create_session(db, identity, request)
    return safe_auth_response(await resolve_auth_payload(db, identity), session_bundle["raw_token"], session_bundle["session"])


@router.get("/invitations/validate")
async def validate_invitation(token: str = Query(...), db: Database = Depends(get_database)) -> dict:
    invitation = await find_pending_invitation_by_token(db, token)
    if invitation.get("invitation_type") != "agency_staff":
        return {
            "ok": True,
            "invitation": {
                "invitation_type": invitation.get("invitation_type"),
                "invited_email": invitation.get("invited_email"),
                "target_role": invitation.get("target_role"),
                "expires_at": invitation.get("expires_at"),
                "status": invitation.get("status"),
            },
        }

    agency = await db.collection("agencies").find_one({"id": invitation.get("agency_id")})
    workspace = None
    if invitation.get("workspace_id"):
        workspace = await db.collection("agency_workspaces").find_one(
            {"agency_id": invitation.get("agency_id"), "id": invitation.get("workspace_id")}
        )
    return {
        "ok": True,
        "invitation": {
            "invitation_type": "agency_staff",
            "invited_email": invitation.get("invited_email"),
            "invited_name": invitation.get("invited_name"),
            "target_role": invitation.get("target_role"),
            "expires_at": invitation.get("expires_at"),
            "status": invitation.get("status"),
        },
        "agency": {"name": agency.get("name"), "slug": agency.get("slug")} if agency else None,
        "workspace": {"name": workspace.get("name") or workspace.get("brand_name")} if workspace else None,
    }


@router.post("/invitations/accept")
async def accept_invitation(
    payload: InvitationAcceptRequest,
    request: Request,
    authorization: str | None = Header(default=None),
    db: Database = Depends(get_database),
) -> dict:
    invitation = await find_pending_invitation_by_token(db, payload.token)
    if payload.email and normalize_email(str(payload.email)) != invitation["normalized_email"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invitation email does not match.")

    identity = await db.collection("auth_identities").find_one({"normalized_email": invitation["normalized_email"]})
    authenticated_identity = None
    if authorization:
        authenticated_identity = await get_current_identity(authorization, None, db)
        if normalize_email(authenticated_identity["email"]) != invitation["normalized_email"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Authenticated email does not match invitation.")

    if identity and identity.get("status") == "active":
        if authenticated_identity is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This account already exists. Sign in before accepting the invitation.")
    elif identity:
        identity = await db.collection("auth_identities").update_one(
            {"id": identity["id"]},
            {"password_hash": hash_password(payload.password), "status": "active", "password_reset_required": False},
        )
    else:
        identity = await ensure_auth_identity(
            db,
            invitation["invited_email"],
            payload.password,
            invitation["invitation_type"],
            "active",
        )

    user = None
    if invitation["invitation_type"] in {"platform_user", "agency_staff"}:
        user = await db.collection("platform_users").find_one({"email": invitation["invited_email"]})
        if user is None:
            user = await db.collection("platform_users").insert_one(
                PlatformUser(
                    email=invitation["invited_email"],
                    full_name=payload.display_name or invitation.get("invited_name") or invitation["invited_email"],
                    status="active",
                ).model_dump(mode="json")
            )
        else:
            user = await db.collection("platform_users").update_one(
                {"id": user["id"]},
                {"status": "active", "full_name": user.get("full_name") or payload.display_name or invitation.get("invited_name") or invitation["invited_email"]},
            )
        if invitation.get("agency_id"):
            if invitation.get("workspace_id"):
                workspace = await db.collection("agency_workspaces").find_one(
                    {"agency_id": invitation["agency_id"], "id": invitation["workspace_id"]}
                )
                if workspace is None:
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invitation workspace is no longer available.")
            membership = await db.collection("agency_staff_memberships").find_one(
                {"agency_id": invitation["agency_id"], "user_id": user["id"]}
            )
            if membership:
                membership = await db.collection("agency_staff_memberships").update_one(
                    {"id": membership["id"]},
                    {
                        "status": "active",
                        "agency_role": invitation.get("target_role") or membership.get("agency_role"),
                        "workspace_id": invitation.get("workspace_id"),
                        "identity_id": identity["id"],
                        "email": invitation["invited_email"],
                        "normalized_email": invitation["normalized_email"],
                        "joined_at": now_utc(),
                        "created_from_invitation_id": invitation["id"],
                    },
                )
            else:
                membership_model = AgencyStaffMembership(
                    agency_id=invitation["agency_id"],
                    workspace_id=invitation.get("workspace_id"),
                    user_id=user["id"],
                    identity_id=identity["id"],
                    email=invitation["invited_email"],
                    normalized_email=invitation["normalized_email"],
                    agency_role=invitation.get("target_role") or "agency_agent",
                    status="active",
                    joined_at=now_utc(),
                    created_from_invitation_id=invitation["id"],
                )
                membership = await db.collection("agency_staff_memberships").insert_one(membership_model.model_dump(mode="json"))
            await write_auth_audit(
                db,
                event_type="membership_created_from_invitation",
                entity_type="agency_staff_membership",
                entity_id=membership["id"],
                summary=f"Activated staff membership for {invitation['invited_email']}.",
                agency_id=invitation.get("agency_id"),
                actor_user_id=user["id"],
                metadata={"invitation_id": invitation["id"], "workspace_id": invitation.get("workspace_id"), "agency_role": invitation.get("target_role")},
            )
    elif invitation["invitation_type"] == "client_portal" and invitation.get("agency_id"):
        mapping = await db.collection("portal_access_mappings").find_one(
            {"agency_id": invitation["agency_id"], "client_id": invitation["target_client_id"]}
        )
        if mapping:
            await db.collection("portal_access_mappings").update_one(
                {"id": mapping["id"]},
                {"portal_status": "active", "user_email": invitation["invited_email"], "display_name": payload.display_name or mapping["display_name"]},
            )
        await db.collection("client_profiles").update_one(
            {"agency_id": invitation["agency_id"], "id": invitation["target_client_id"]},
            {"portal_status": "active"},
        )

    accepted = await db.collection("invitations").update_one(
        {"id": invitation["id"], "status": "pending"},
        {
            "status": "accepted",
            "accepted_at": now_utc(),
            "accepted_by_identity_id": identity["id"],
            "accepted_by_user_id": user["id"] if user else None,
        },
    )
    if accepted is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invitation was already used.")
    await write_auth_audit(
        db,
        event_type="invitation_accepted",
        entity_type="invitation",
        entity_id=invitation["id"],
        summary=f"Accepted invitation for {invitation['invited_email']}.",
        agency_id=invitation.get("agency_id"),
        actor_user_id=user["id"] if user else None,
        metadata={"invitation_type": invitation.get("invitation_type"), "workspace_id": invitation.get("workspace_id"), "target_role": invitation.get("target_role")},
    )
    session_bundle = await create_session(db, identity, request)
    return {
        **safe_auth_response(await resolve_auth_payload(db, identity), session_bundle["raw_token"], session_bundle["session"]),
        "invitation": safe_invitation_record(accepted),
    }


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    authorization: str | None = Header(default=None),
    db: Database = Depends(get_database),
) -> dict:
    from auth import get_current_identity

    identity = await get_current_identity(authorization, None, db)
    if payload.current_password and not verify_password(payload.current_password, identity.get("password_hash", "")):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Current password is incorrect.")
    updated = await db.collection("auth_identities").update_one(
        {"id": identity["id"]},
        {"password_hash": hash_password(payload.new_password), "password_reset_required": False},
    )
    return {"identity": safe_identity(updated)}


def invitation_expiry() -> object:
    return now_utc() + timedelta(hours=DEFAULT_INVITATION_EXPIRY_HOURS)
