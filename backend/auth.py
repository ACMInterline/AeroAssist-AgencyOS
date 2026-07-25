from datetime import timedelta
from typing import Callable, Iterable, Optional

from fastapi import Depends, Header, HTTPException, Request, status

from config import get_settings
from database import Database, get_database
from models import AuthIdentity, AuthSession, now_utc
from security import hash_password, hash_token, new_raw_token, normalize_email, verify_password
from http_security import log_security_event
from services.authentication_security_service import token_refresh_metadata, validate_auth_token
from services.authorization_service import (
    active_memberships,
    agency_permissions,
    authorize_staff_request,
    platform_permissions,
    portal_permissions,
    resolve_staff_user,
    safe_membership,
    safe_platform_user,
)
from services.portal_identity_link_service import (
    PortalIdentityLinkError,
    UNLINKED_PORTAL_MESSAGE,
    resolve_portal_identity_context,
    safe_portal_mapping,
    safe_portal_subject,
)
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
        key: identity.get(key)
        for key in (
            "id",
            "email",
            "identity_type",
            "status",
            "last_login_at",
            "created_at",
            "updated_at",
        )
        if key in identity
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
    staff_identity = identity.get("identity_type") in {"platform_user", "agency_staff"}
    platform_user = await resolve_staff_user(db, identity) if staff_identity else None
    if platform_user and platform_user.get("status") != "active":
        platform_user = None
    memberships = (
        await active_memberships(db, platform_user, identity)
        if platform_user and staff_identity
        else []
    )
    portal_context = None
    portal_link_error = None
    if identity.get("identity_type") in {"client_portal", "passenger_portal"}:
        try:
            portal_context = await resolve_portal_identity_context(
                db,
                identity["id"],
                required=False,
            )
        except PortalIdentityLinkError:
            portal_link_error = "Portal access requires operator review."
    platform_access = None
    if platform_user and platform_user.get("global_role"):
        platform_access = {
            "user_id": platform_user["id"],
            "role": platform_user.get("global_role"),
            "permissions": sorted(platform_permissions(platform_user.get("global_role"))),
        }
    agency_access = [
        {
            "membership": safe_membership(membership),
            "permissions": sorted(agency_permissions(membership.get("agency_role"))),
        }
        for membership in memberships
    ]
    portal_access = (
        {
            "linked": True,
            "mapping": safe_portal_mapping(portal_context["mapping"]),
            "subject_type": portal_context["subject_type"],
            "subject": safe_portal_subject(
                portal_context["subject_type"],
                portal_context["subject"],
            ),
            "permissions": sorted(portal_permissions(identity.get("identity_type"))),
        }
        if portal_context
        else {
            "linked": False,
            "mapping": None,
            "subject_type": None,
            "subject": None,
            "permissions": sorted(portal_permissions(identity.get("identity_type"))),
            "message": portal_link_error or UNLINKED_PORTAL_MESSAGE,
        }
        if identity.get("identity_type") in {"client_portal", "passenger_portal"}
        else None
    )
    return {
        "identity": safe_identity(identity),
        "authorization": {
            "identity_type": identity.get("identity_type"),
            "platform": platform_access,
            "agency_memberships": agency_access,
            "portal": portal_access,
        },
        # Compatibility keys remain projections of the canonical contract.
        "user": safe_platform_user(platform_user),
        "memberships": [safe_membership(item) for item in memberships],
        "portal": (
            {
                "account": safe_portal_mapping(portal_context["mapping"]),
                "client": (
                    safe_portal_subject("client", portal_context["client"])
                    if portal_context.get("client")
                    else None
                ),
                "passenger": (
                    safe_portal_subject("passenger", portal_context["passenger"])
                    if portal_context.get("passenger")
                    else None
                ),
                "subject_type": portal_context["subject_type"],
            }
            if portal_context
            else None
        ),
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


async def get_current_user(
    request: Request,
    identity: dict = Depends(get_current_identity),
    db: Database = Depends(get_database),
) -> dict:
    if identity.get("identity_type") in {"client_portal", "passenger_portal"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff or Platform identity required.",
        )
    user = await resolve_staff_user(db, identity)
    if user is None or user.get("status") != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Active staff or platform user required.")
    return await authorize_staff_request(request, db, identity, user)


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
