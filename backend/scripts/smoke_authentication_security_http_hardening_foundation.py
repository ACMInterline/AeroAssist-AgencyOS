#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import timedelta
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from build_phase import CURRENT_BUILD_PHASE
from config import env_float, env_int, get_settings, validate_config
from database import Database
from http_security import SAFE_SECURITY_EVENT_FIELDS, security_headers
from models import AuthIdentity, AuthSession, now_utc
from phase_assertions import assert_application_phase_at_least
from security import hash_password, hash_token
from services.authentication_security_service import (
    clear_login_failures,
    login_attempt_state,
    record_login_failure,
    validate_auth_token,
)
from smoke_booking_pnr_foundation import BASE_URL


RELEASE_PHASE = "phase_56_5_4_authentication_security_http_hardening_foundation"
MINIMUM_PHASE = RELEASE_PHASE
REQUIRED_SECURITY_HEADERS = {
    "content-security-policy",
    "strict-transport-security",
    "x-frame-options",
    "x-content-type-options",
    "referrer-policy",
    "permissions-policy",
    "cross-origin-resource-policy",
    "cross-origin-opener-policy",
    "cross-origin-embedder-policy",
    "x-request-id",
}


def request(
    method: str,
    path: str,
    body: dict | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict | str, dict[str, str]]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        method=method,
        data=data,
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    try:
        response = urllib.request.urlopen(req, timeout=20)
    except urllib.error.HTTPError as exc:
        response = exc
    with response:
        raw = response.read().decode("utf-8")
        response_headers = {key.lower(): value for key, value in response.headers.items()}
        try:
            payload: dict | str = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = raw
        return response.status, payload, response_headers


async def verify_authentication_state_and_tokens() -> None:
    db = Database()
    settings = get_settings()
    identity = await db.collection("auth_identities").insert_one(
        AuthIdentity(
            email="security-smoke@example.com",
            normalized_email="security-smoke@example.com",
            password_hash=hash_password("not-used-by-smoke"),
            identity_type="platform_user",
            status="active",
        ).model_dump(mode="json")
    )

    state = login_attempt_state(identity, settings=settings)
    if state.locked or state.failed_count:
        raise AssertionError("A new identity unexpectedly started in a locked state.")
    for attempt in range(settings.login_max_attempts):
        identity = await db.collection("auth_identities").find_one({"id": identity["id"]}) or identity
        state = await record_login_failure(db, identity, settings=settings)
        if attempt < settings.login_max_attempts - 1 and state.locked:
            raise AssertionError("Account locked before the configured maximum attempt.")
    if not state.locked or not state.locked_until or state.retry_after_seconds <= 0:
        raise AssertionError("Configured failures did not create a temporary account lock.")
    unlocked_state = login_attempt_state(
        await db.collection("auth_identities").find_one({"id": identity["id"]}) or identity,
        at=state.locked_until + timedelta(seconds=1),
        settings=settings,
    )
    if unlocked_state.locked:
        raise AssertionError("Temporary account lock did not expire deterministically.")
    cleared = await clear_login_failures(db, identity["id"])
    if not cleared or cleared.get("failed_login_count") != 0 or cleared.get("locked_until") is not None:
        raise AssertionError("Successful-login reset did not clear temporary failure metadata.")

    raw_token = "security-smoke-valid-token"
    session = AuthSession(
        identity_id=identity["id"],
        token_hash=hash_token(raw_token),
        expires_at=now_utc() + timedelta(minutes=10),
    )
    await db.collection("auth_sessions").insert_one(session.model_dump(mode="json"))
    valid = await validate_auth_token(db, raw_token, settings=settings)
    if not valid.valid or valid.reason != "valid" or not valid.identity:
        raise AssertionError(f"Valid opaque token was rejected: {valid}")
    if (valid.refresh_metadata or {}).get("execution_enabled") is not False:
        raise AssertionError("Refresh policy metadata unexpectedly enabled token execution.")
    invalid = await validate_auth_token(db, "security-smoke-invalid-token", settings=settings)
    if invalid.valid or invalid.reason != "unknown_token":
        raise AssertionError("Invalid token diagnostics were not explicit.")

    expired_token = "security-smoke-expired-token"
    expired_session = AuthSession(
        identity_id=identity["id"],
        token_hash=hash_token(expired_token),
        issued_at=now_utc() - timedelta(hours=2),
        expires_at=now_utc() - timedelta(seconds=settings.token_clock_skew_seconds + 2),
    )
    await db.collection("auth_sessions").insert_one(expired_session.model_dump(mode="json"))
    expired = await validate_auth_token(db, expired_token, settings=settings)
    if expired.valid or expired.reason != "expired_token":
        raise AssertionError("Expired token was not rejected after bounded clock skew.")


def verify_http_contract() -> None:
    request_id = "security-smoke-request-0001"
    status_code, health, headers = request("GET", "/api/health", headers={"X-Request-ID": request_id})
    if status_code != 200 or not isinstance(health, dict):
        raise AssertionError(f"Health phase mismatch: {health}")
    assert_application_phase_at_least(health.get("phase"), MINIMUM_PHASE, source="health")
    missing = REQUIRED_SECURITY_HEADERS - set(headers)
    if missing:
        raise AssertionError(f"Security headers are missing: {sorted(missing)}")
    if headers.get("x-request-id") != request_id:
        raise AssertionError("A valid caller correlation ID was not echoed.")
    if "default-src 'self'" not in headers.get("content-security-policy", ""):
        raise AssertionError("CSP does not establish a same-origin default.")

    for path in ("/docs", "/openapi.json"):
        page_status, _, page_headers = request("GET", path)
        if page_status != 200 or "content-security-policy" not in page_headers:
            raise AssertionError(f"FastAPI documentation surface is not CSP-compatible: {path}")

    failed_status, failed_body, _ = request(
        "POST",
        "/api/auth/login",
        {"email": "owner@aeroassist.dev", "password": "incorrect-security-smoke-password"},
    )
    if failed_status != 401 or not isinstance(failed_body, dict) or (failed_body.get("error") or {}).get("code") != "authentication_required":
        raise AssertionError(f"Failed login did not return the safe authentication error contract: {failed_body}")
    login_status, login_body, _ = request(
        "POST",
        "/api/auth/login",
        {"email": "owner@aeroassist.dev", "password": "DemoPass123!"},
    )
    session_payload = login_body.get("session") if isinstance(login_body, dict) else None
    if login_status != 200 or not session_payload or not session_payload.get("access_token"):
        raise AssertionError(f"Existing login contract failed after a throttled attempt: {login_body}")
    if (session_payload.get("refresh") or {}).get("execution_enabled") is not False:
        raise AssertionError("Login response did not expose metadata-only refresh policy.")
    me_status, me_body, _ = request(
        "GET",
        "/api/auth/me",
        headers={"Authorization": f"Bearer {session_payload['access_token']}"},
    )
    if me_status != 200 or not isinstance(me_body, dict):
        raise AssertionError(f"New token validation helper rejected an existing session token: {me_body}")
    serialized_me = json.dumps(me_body)
    if any(field in serialized_me for field in ("password_hash", "failed_login_count", "locked_until")):
        raise AssertionError("Authentication response exposed login security metadata.")

    error_status, error_body, error_headers = request("GET", "/api/security-smoke-not-found")
    if error_status != 404 or not isinstance(error_body, dict):
        raise AssertionError(f"Unexpected not-found response: {error_status} {error_body}")
    error = error_body.get("error") or {}
    if error.get("code") != "not_found" or not error.get("request_id") or "traceback" in json.dumps(error_body).lower():
        raise AssertionError(f"Error response is not safe and structured: {error_body}")
    if error_headers.get("x-request-id") != error.get("request_id"):
        raise AssertionError("Error response correlation ID is inconsistent.")

    token_status, token_body, _ = request(
        "GET", "/api/auth/me", headers={"Authorization": "Bearer definitely-invalid-token"}
    )
    if token_status != 401 or not isinstance(token_body, dict) or (token_body.get("error") or {}).get("code") != "authentication_required":
        raise AssertionError(f"Invalid bearer token did not return a safe JSON diagnostic: {token_body}")

    allowed_origin = get_settings().cors_allowed_origins[0]
    cors_status, _, cors_headers = request(
        "OPTIONS",
        "/api/health",
        headers={"Origin": allowed_origin, "Access-Control-Request-Method": "GET"},
    )
    if cors_status != 200 or cors_headers.get("access-control-allow-origin") != allowed_origin:
        raise AssertionError(f"Configured development CORS origin was not allowed: {cors_headers}")
    _, _, rejected_headers = request(
        "OPTIONS",
        "/api/health",
        headers={"Origin": "https://untrusted.example", "Access-Control-Request-Method": "GET"},
    )
    if "access-control-allow-origin" in rejected_headers:
        raise AssertionError("Unconfigured CORS origin received an allow-origin header.")

    readiness_status, readiness, _ = request("GET", "/api/readiness")
    if readiness_status != 200 or not isinstance(readiness, dict):
        raise AssertionError(f"Readiness failed: {readiness}")
    assert_application_phase_at_least(readiness.get("phase"), MINIMUM_PHASE, source="readiness")
    section = readiness.get("authentication_security_http_hardening_foundation") or {}
    for key in (
        "authentication_hardening",
        "http_security",
        "cors_validation",
        "security_logging",
        "request_correlation",
        "token_validation",
    ):
        if section.get(key) is not True:
            raise AssertionError(f"Security readiness flag is missing: {key}")
    if section.get("permanent_account_locking") is not False or section.get("runtime_filesystem_scanning") is not False:
        raise AssertionError("Security readiness safety flags are incorrect.")


async def verify_public_projection() -> None:
    from server import public_readiness_payload

    projection = await public_readiness_payload()
    if projection.get("readiness_mode") != "public_summary" or not projection.get("inventory"):
        raise AssertionError(f"Public readiness projection is incomplete: {projection}")
    for restricted_key in ("config", "storage", "delivery", "smtp_secret_refs"):
        if restricted_key in projection:
            raise AssertionError(f"Public readiness exposed restricted implementation detail: {restricted_key}")


def verify_static_configuration() -> None:
    assert_application_phase_at_least(CURRENT_BUILD_PHASE, MINIMUM_PHASE, source="canonical build phase")
    os.environ["AEROASSIST_SECURITY_SMOKE_INT"] = "17"
    os.environ["AEROASSIST_SECURITY_SMOKE_FLOAT"] = "0.25"
    try:
        if env_int("AEROASSIST_SECURITY_SMOKE_INT", 1) != 17:
            raise AssertionError("Explicit integer security configuration was not parsed.")
        if env_float("AEROASSIST_SECURITY_SMOKE_FLOAT", 1.0) != 0.25:
            raise AssertionError("Explicit decimal security configuration was not parsed.")
    finally:
        os.environ.pop("AEROASSIST_SECURITY_SMOKE_INT", None)
        os.environ.pop("AEROASSIST_SECURITY_SMOKE_FLOAT", None)
    settings = get_settings()
    config = validate_config(settings, include_storage=False)
    if not config.get("ok"):
        raise AssertionError(f"Security configuration validation failed: {config}")
    configured_headers = {key.lower() for key in security_headers(settings)}
    if REQUIRED_SECURITY_HEADERS - {"x-request-id"} - configured_headers:
        raise AssertionError("Configured HTTP security header set is incomplete.")
    forbidden_log_fields = {"password", "token", "email", "passport", "payment", "medical"}
    if forbidden_log_fields.intersection(SAFE_SECURITY_EVENT_FIELDS):
        raise AssertionError("Structured security logging allowlist contains sensitive fields.")
    server_text = (BACKEND / "server.py").read_text(encoding="utf-8")
    if any(pattern in server_text for pattern in (".glob(", ".rglob(", "os.walk(")):
        raise AssertionError("Server readiness performs runtime filesystem scanning.")
    production_smoke_text = (ROOT / "deploy" / "hostinger" / "scripts" / "smoke_production.sh").read_text(encoding="utf-8")
    if "@example.invalid" in production_smoke_text or "401|403" in production_smoke_text:
        raise AssertionError("Production login smoke permits an invalid email schema or ambiguous rejection status.")
    for token in ('@example.com', '-d "$login_payload"', '  401)'):
        if token not in production_smoke_text:
            raise AssertionError(f"Production login smoke is missing the valid safe-probe contract {token!r}.")


def main() -> None:
    verify_static_configuration()
    asyncio.run(verify_authentication_state_and_tokens())
    verify_http_contract()
    asyncio.run(verify_public_projection())
    print("Phase 56.5.4 authentication, security, and HTTP hardening foundation smoke passed.")


if __name__ == "__main__":
    main()
