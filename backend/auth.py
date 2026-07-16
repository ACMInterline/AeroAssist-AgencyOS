from datetime import timedelta
from typing import Callable, Iterable, Optional

from fastapi import Depends, Header, HTTPException, Request, status

from config import get_settings
from database import Database, get_database
from models import AuthIdentity, AuthSession, now_utc
from security import hash_password, hash_token, new_raw_token, normalize_email, verify_password
from http_security import log_security_event
from services.authentication_security_service import token_refresh_metadata, validate_auth_token
from services.seed_service import DEMO_OWNER_EMAIL, seed_core_data
from services.tenant_service import assert_agency_access, require_any_agency_role, require_any_platform_role


SETTINGS = get_settings()
DEMO_AUTH_ENABLED = SETTINGS.demo_auth_enabled
DEMO_PASSWORD = "DemoPass123!"
DEFAULT_TOKEN_EXPIRY_MINUTES = SETTINGS.token_expiry_minutes
DEFAULT_INVITATION_EXPIRY_HOURS = SETTINGS.invitation_expiry_hours

def token_response(raw_token: str, session: dict) -> dict:
    refresh_metadata = token_refresh_metadata(session["expires_at"])
    return {
        "access_token": raw_token,
        "token_type": "bearer",
        "expires_at": session["expires_at"],
        "refresh": refresh_metadata,
    }


def safe_identity(identity: dict | None) -> dict | None:
    if not identity:
        return None
    return {
        key: value
        for key, value in identity.items()
        if key
        not in {
            "password_hash",
            "failed_login_count",
            "first_failed_login_at",
            "last_failed_login_at",
            "locked_until",
        }
    }


async def ensure_auth_identity(
    db: Database,
    email: str,
    password: str,
    identity_type: str,
    status_value: str = "active",
) -> dict:
    normalized = normalize_email(email)
    existing = await db.collection("auth_identities").find_one({"normalized_email": normalized})
    if existing:
        return existing
    identity = AuthIdentity(
        email=email,
        normalized_email=normalized,
        password_hash=hash_password(password),
        identity_type=identity_type,
        status=status_value,
    )
    return await db.collection("auth_identities").insert_one(identity.model_dump(mode="json"))


async def create_session(
    db: Database,
    identity: dict,
    request: Request | None = None,
    minutes: int | None = None,
) -> dict:
    raw_token = new_raw_token()
    issued_at = now_utc()
    lifetime_minutes = DEFAULT_TOKEN_EXPIRY_MINUTES if minutes is None else minutes
    if lifetime_minutes <= 0:
        raise ValueError("Session lifetime must be greater than zero.")
    expires_at = issued_at + timedelta(minutes=lifetime_minutes)
    session = AuthSession(
        identity_id=identity["id"],
        token_hash=hash_token(raw_token),
        issued_at=issued_at,
        expires_at=expires_at,
        user_agent=request.headers.get("user-agent") if request else None,
        ip_address=request.client.host if request and request.client else None,
    )
    created = await db.collection("auth_sessions").insert_one(session.model_dump(mode="json"))
    return {"raw_token": raw_token, "session": created}


async def resolve_auth_payload(db: Database, identity: dict) -> dict:
    platform_user = await db.collection("platform_users").find_one({"email": identity["email"]})
    memberships = []
    portal_account = None
    portal_client = None
    if platform_user:
        memberships = await db.collection("agency_staff_memberships").find_many(
            {"user_id": platform_user["id"], "status": "active"}
        )
    if identity.get("identity_type") == "client_portal":
        portal_account = await db.collection("portal_access_mappings").find_one(
            {"user_email": identity["email"], "portal_status": "active"}
        )
        if portal_account:
            portal_client = await db.collection("client_profiles").find_one(
                {"agency_id": portal_account["agency_id"], "id": portal_account["client_id"]}
            )
    return {
        "identity": safe_identity(identity),
        "user": platform_user,
        "memberships": memberships,
        "portal": {"account": portal_account, "client": portal_client} if portal_account else None,
    }


async def get_current_identity(
    authorization: Optional[str] = Header(default=None),
    x_demo_user_email: Optional[str] = Header(default=None),
    db: Database = Depends(get_database),
) -> dict:
    if get_settings().seed_on_startup:
        await seed_core_data(db)
    if authorization and authorization.lower().startswith("bearer "):
        raw_token = authorization.split(" ", 1)[1].strip()
        result = await validate_auth_token(db, raw_token)
        if not result.valid:
            log_security_event(
                "invalid_token",
                outcome="denied",
                reason=result.reason,
                session_id=(result.session or {}).get("id"),
            )
            detail = {
                "expired_token": "Session expired.",
                "inactive_identity": "Active identity required.",
            }.get(result.reason, "Invalid or revoked session.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=detail,
                headers={"WWW-Authenticate": "Bearer"},
            )
        return result.identity or {}

    if DEMO_AUTH_ENABLED:
        email = x_demo_user_email or DEMO_OWNER_EMAIL
        identity = await db.collection("auth_identities").find_one({"normalized_email": normalize_email(email)})
        if identity:
            return identity
        user = await db.collection("platform_users").find_one({"email": email})
        if user is None or user.get("status") != "active":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Active demo user not found.")
        return await ensure_auth_identity(
            db,
            email=user["email"],
            password=DEMO_PASSWORD,
            identity_type="platform_user" if user.get("global_role") else "agency_staff",
            status_value="active",
        )

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")


async def get_current_user(identity: dict = Depends(get_current_identity), db: Database = Depends(get_database)) -> dict:
    user = await db.collection("platform_users").find_one({"email": identity["email"]})
    if user is None or user.get("status") != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Active staff or platform user required.")
    return user


def require_platform_role(roles: Iterable[str]) -> Callable:
    async def dependency(user: dict = Depends(get_current_user)) -> dict:
        await require_any_platform_role(user, roles)
        return user

    return dependency


def require_agency_role(agency_id_param: str, roles: Iterable[str]) -> Callable:
    async def dependency(
        db: Database = Depends(get_database),
        user: dict = Depends(get_current_user),
        agency_id: str = "",
    ) -> dict:
        target_agency_id = agency_id or agency_id_param
        return await require_any_agency_role(db, target_agency_id, user, roles)

    return dependency


async def get_current_agency_context(
    agency_id: str,
    db: Database = Depends(get_database),
    user: dict = Depends(get_current_user),
) -> dict:
    agency = await assert_agency_access(db, agency_id, user)
    membership = await db.collection("agency_staff_memberships").find_one(
        {"agency_id": agency_id, "user_id": user["id"]}
    )
    return {
        "agency": agency,
        "membership": membership,
        "user": user,
    }
