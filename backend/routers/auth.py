from datetime import timedelta

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from auth import (
    DEFAULT_INVITATION_EXPIRY_HOURS,
    DEMO_AUTH_ENABLED,
    DEMO_PASSWORD,
    create_session,
    ensure_auth_identity,
    resolve_auth_payload,
    safe_identity,
    token_response,
)
from config import get_settings
from database import Database, get_database
from models import (
    ChangePasswordRequest,
    InvitationAcceptRequest,
    LoginRequest,
    PlatformUser,
    now_utc,
)
from security import hash_password, hash_token, normalize_email, verify_password
from services.seed_service import seed_core_data

router = APIRouter(prefix="/api/auth", tags=["auth"])


def safe_auth_response(payload: dict, raw_token: str | None = None, session: dict | None = None) -> dict:
    response = {"auth": payload}
    if raw_token and session:
        response["session"] = token_response(raw_token, session)
    return response


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


@router.post("/invitations/accept")
async def accept_invitation(
    payload: InvitationAcceptRequest,
    request: Request,
    db: Database = Depends(get_database),
) -> dict:
    token_hash = hash_token(payload.token)
    invitation = await db.collection("invitations").find_one({"token_hash": token_hash})
    if not invitation or invitation.get("status") != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation is invalid.")
    expires_at = invitation["expires_at"]
    if isinstance(expires_at, str):
        from datetime import datetime

        expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    if expires_at <= now_utc():
        await db.collection("invitations").update_one({"id": invitation["id"]}, {"status": "expired"})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation has expired.")

    identity = await db.collection("auth_identities").find_one({"normalized_email": invitation["normalized_email"]})
    if identity:
        identity = await db.collection("auth_identities").update_one(
            {"id": identity["id"]},
            {
                "password_hash": hash_password(payload.password),
                "status": "active",
                "password_reset_required": False,
            },
        )
    else:
        identity = await ensure_auth_identity(
            db,
            invitation["invited_email"],
            payload.password,
            invitation["invitation_type"],
            "active",
        )

    if invitation["invitation_type"] in {"platform_user", "agency_staff"}:
        user = await db.collection("platform_users").find_one({"email": invitation["invited_email"]})
        if user is None:
            user = await db.collection("platform_users").insert_one(
                PlatformUser(
                    email=invitation["invited_email"],
                    full_name=payload.display_name or invitation["invited_email"],
                    status="active",
                ).model_dump(mode="json")
            )
        else:
            await db.collection("platform_users").update_one({"id": user["id"]}, {"status": "active"})
        if invitation.get("agency_id"):
            membership = await db.collection("agency_staff_memberships").find_one(
                {"agency_id": invitation["agency_id"], "user_id": user["id"]}
            )
            if membership:
                await db.collection("agency_staff_memberships").update_one(
                    {"id": membership["id"]},
                    {"status": "active", "joined_at": now_utc()},
                )
    if invitation["invitation_type"] == "client_portal" and invitation.get("agency_id"):
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

    await db.collection("invitations").update_one(
        {"id": invitation["id"]},
        {"status": "accepted", "accepted_at": now_utc()},
    )
    session_bundle = await create_session(db, identity, request)
    return safe_auth_response(await resolve_auth_payload(db, identity), session_bundle["raw_token"], session_bundle["session"])


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
