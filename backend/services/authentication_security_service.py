from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from config import AppSettings, get_settings
from database import Database
from models import now_utc
from security import hash_token


ACTIVE_IDENTITY_STATUSES = {"active", "email_unverified"}


def as_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class LoginAttemptState:
    locked: bool
    failed_count: int
    retry_after_seconds: int
    backoff_seconds: float
    locked_until: datetime | None = None


@dataclass(frozen=True)
class TokenValidationResult:
    valid: bool
    reason: str
    diagnostic: str
    session: dict[str, Any] | None = None
    identity: dict[str, Any] | None = None
    refresh_metadata: dict[str, Any] | None = None


def login_attempt_state(
    identity: dict[str, Any],
    *,
    at: datetime | None = None,
    settings: AppSettings | None = None,
) -> LoginAttemptState:
    settings = settings or get_settings()
    at = as_utc(at) or now_utc()
    locked_until = as_utc(identity.get("locked_until"))
    if settings.login_throttle_enabled and locked_until and locked_until > at:
        retry_after = max(1, int((locked_until - at).total_seconds()))
        return LoginAttemptState(True, int(identity.get("failed_login_count") or 0), retry_after, 0.0, locked_until)

    failed_count = 0 if locked_until and locked_until <= at else int(identity.get("failed_login_count") or 0)
    last_failed_at = as_utc(identity.get("last_failed_login_at"))
    if last_failed_at and at - last_failed_at >= timedelta(seconds=settings.login_failure_reset_seconds):
        failed_count = 0
    return LoginAttemptState(False, failed_count, 0, 0.0, None)


def failure_backoff_seconds(failed_count: int, settings: AppSettings | None = None) -> float:
    settings = settings or get_settings()
    if not settings.login_throttle_enabled or settings.login_backoff_base_seconds <= 0:
        return 0.0
    exponent = max(0, min(failed_count - 1, 20))
    return min(settings.login_backoff_base_seconds * (2**exponent), settings.login_backoff_max_seconds)


async def record_login_failure(
    db: Database,
    identity: dict[str, Any],
    *,
    at: datetime | None = None,
    settings: AppSettings | None = None,
) -> LoginAttemptState:
    settings = settings or get_settings()
    at = as_utc(at) or now_utc()
    current = login_attempt_state(identity, at=at, settings=settings)
    failed_count = current.failed_count + 1
    first_failed_at = as_utc(identity.get("first_failed_login_at")) if current.failed_count else at
    locked = settings.login_throttle_enabled and failed_count >= settings.login_max_attempts
    locked_until = at + timedelta(seconds=settings.login_lock_duration_seconds) if locked else None
    updates = {
        "failed_login_count": failed_count,
        "first_failed_login_at": first_failed_at or at,
        "last_failed_login_at": at,
        "locked_until": locked_until,
    }
    await db.collection("auth_identities").update_one({"id": identity["id"]}, updates)
    retry_after = max(1, settings.login_lock_duration_seconds) if locked else 0
    return LoginAttemptState(
        locked=locked,
        failed_count=failed_count,
        retry_after_seconds=retry_after,
        backoff_seconds=0.0 if locked else failure_backoff_seconds(failed_count, settings),
        locked_until=locked_until,
    )


async def clear_login_failures(db: Database, identity_id: str) -> dict[str, Any] | None:
    return await db.collection("auth_identities").update_one(
        {"id": identity_id},
        {
            "failed_login_count": 0,
            "first_failed_login_at": None,
            "last_failed_login_at": None,
            "locked_until": None,
            "last_login_at": now_utc(),
        },
    )


def token_refresh_metadata(expires_at: Any, settings: AppSettings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    parsed_expires_at = as_utc(expires_at)
    eligible = bool(
        settings.token_refresh_policy == "manual_metadata"
        and parsed_expires_at
        and now_utc() >= parsed_expires_at - timedelta(minutes=settings.token_refresh_window_minutes)
    )
    return {
        "policy": settings.token_refresh_policy,
        "execution_enabled": False,
        "window_minutes": settings.token_refresh_window_minutes,
        "eligible": eligible,
        "expires_at": parsed_expires_at or expires_at,
    }


async def validate_auth_token(
    db: Database,
    raw_token: str,
    *,
    at: datetime | None = None,
    settings: AppSettings | None = None,
    update_last_seen: bool = True,
) -> TokenValidationResult:
    settings = settings or get_settings()
    at = as_utc(at) or now_utc()
    if not raw_token or len(raw_token) > 4096:
        return TokenValidationResult(False, "malformed_token", "Bearer token is missing or malformed.")

    session = await db.collection("auth_sessions").find_one({"token_hash": hash_token(raw_token)})
    if not session:
        return TokenValidationResult(False, "unknown_token", "No session matched the supplied token.")
    if session.get("status") != "active":
        return TokenValidationResult(False, "inactive_session", "The session is not active.", session=session)

    expires_at = as_utc(session.get("expires_at"))
    issued_at = as_utc(session.get("issued_at"))
    skew = timedelta(seconds=settings.token_clock_skew_seconds)
    if expires_at is None:
        return TokenValidationResult(False, "invalid_expiration", "The session expiration value is invalid.", session=session)
    if issued_at and issued_at > at + skew:
        return TokenValidationResult(False, "issued_in_future", "The session issue time exceeds clock-skew tolerance.", session=session)
    if expires_at <= at - skew:
        await db.collection("auth_sessions").update_one({"id": session["id"]}, {"status": "expired"})
        return TokenValidationResult(False, "expired_token", "The session has expired.", session=session)

    identity = await db.collection("auth_identities").find_one({"id": session.get("identity_id")})
    if not identity or identity.get("status") not in ACTIVE_IDENTITY_STATUSES:
        return TokenValidationResult(False, "inactive_identity", "The session identity is not active.", session=session)

    if update_last_seen:
        await db.collection("auth_sessions").update_one({"id": session["id"]}, {"last_seen_at": at})
    refresh = token_refresh_metadata(expires_at, settings)
    if settings.token_refresh_policy == "manual_metadata":
        window_start = expires_at - timedelta(minutes=settings.token_refresh_window_minutes)
        refresh["eligible"] = at >= window_start
    return TokenValidationResult(
        True,
        "valid",
        "Token is valid.",
        session=session,
        identity=identity,
        refresh_metadata=refresh,
    )
