#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import os
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import timedelta
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

os.environ["APP_ENV"] = "development"
os.environ["AEROASSIST_DB_MODE"] = "memory"
os.environ["DEMO_AUTH_ENABLED"] = "false"
os.environ["SEED_ON_STARTUP"] = "false"
os.environ["SEED_ENDPOINT_ENABLED"] = "false"
os.environ["LOG_LEVEL"] = "CRITICAL"

import uvicorn

from build_phase import CURRENT_BUILD_PHASE
from database import database
from models import AuthIdentity, AuthSession, now_utc
from phase_assertions import assert_application_phase_at_least
from security import hash_password, hash_token
from server import app


MINIMUM_PHASE = "phase_56_5_4_authentication_security_http_hardening_foundation"
PASSWORD = "audit-isolation-smoke-password"
AGENCY_ONE = "audit-smoke-agency-one"
AGENCY_TWO = "audit-smoke-agency-two"
SENSITIVE_VALUES = {
    "audit-super-secret",
    "audit-provider-payload",
    "audit-private-document",
    "audit-bearer-token",
}


async def seed_fixture() -> dict[str, str]:
    await database.collection("agencies").insert_one(
        {"id": AGENCY_ONE, "name": "Audit Smoke One", "slug": AGENCY_ONE, "status": "active"}
    )
    await database.collection("agencies").insert_one(
        {"id": AGENCY_TWO, "name": "Audit Smoke Two", "slug": AGENCY_TWO, "status": "active"}
    )

    tokens: dict[str, str] = {}
    users = (
        ("platform_owner", "audit.owner@example.com", "platform_user", "platform_owner", None),
        ("platform_admin", "audit.admin@example.com", "platform_user", "platform_admin", None),
        ("platform_support", "audit.support@example.com", "platform_user", "platform_support", None),
        ("agency_owner", "audit.agency.owner@example.com", "agency_staff", None, "agency_owner"),
        ("agency_readonly", "audit.agency.readonly@example.com", "agency_staff", None, "agency_readonly"),
        ("portal", "audit.portal@example.com", "client_portal", None, None),
    )
    for key, email, identity_type, global_role, agency_role in users:
        identity = AuthIdentity(
            email=email,
            normalized_email=email,
            password_hash=hash_password(PASSWORD),
            identity_type=identity_type,
            status="active",
        )
        identity_record = await database.collection("auth_identities").insert_one(identity.model_dump(mode="json"))
        if identity_type != "client_portal":
            user_id = f"audit-smoke-user-{key}"
            await database.collection("platform_users").insert_one(
                {
                    "id": user_id,
                    "email": email,
                    "full_name": key.replace("_", " ").title(),
                    "global_role": global_role,
                    "status": "active",
                }
            )
            if agency_role:
                await database.collection("agency_staff_memberships").insert_one(
                    {
                        "id": f"audit-smoke-membership-{key}",
                        "agency_id": AGENCY_ONE,
                        "user_id": user_id,
                        "agency_role": agency_role,
                        "status": "active",
                    }
                )
        raw_token = f"audit-smoke-token-{key}"
        session = AuthSession(
            identity_id=identity_record["id"],
            token_hash=hash_token(raw_token),
            expires_at=now_utc() + timedelta(minutes=30),
        )
        await database.collection("auth_sessions").insert_one(session.model_dump(mode="json"))
        tokens[key] = raw_token

    await database.collection("audit_events").insert_one(
        {
            "id": "audit-smoke-event-sensitive",
            "agency_id": AGENCY_ONE,
            "actor_user_id": "audit-smoke-user-agency_owner",
            "event_type": "request.reviewed",
            "entity_type": "request",
            "entity_id": "request-one",
            "summary": "Reviewed request for private.audit@example.com.",
            "metadata": {
                "status": "reviewed",
                "password": "audit-super-secret",
                "provider_payload": {"response": "audit-provider-payload"},
                "private_document": {"content": "audit-private-document"},
                "nested": {"authorization": "Bearer audit-bearer-token"},
            },
            "created_at": now_utc(),
        }
    )
    await database.collection("audit_events").insert_one(
        {
            "id": "audit-smoke-event-one",
            "agency_id": AGENCY_ONE,
            "actor_user_id": "audit-smoke-user-agency_owner",
            "event_type": "request.created",
            "entity_type": "request",
            "entity_id": "request-two",
            "summary": "Created request.",
            "metadata": {"status": "created"},
            "created_at": now_utc() - timedelta(seconds=1),
        }
    )
    await database.collection("audit_events").insert_one(
        {
            "id": "audit-smoke-event-two",
            "agency_id": AGENCY_TWO,
            "actor_user_id": "audit-smoke-user-platform_admin",
            "event_type": "agency.updated",
            "entity_type": "agency",
            "entity_id": AGENCY_TWO,
            "summary": "Updated second agency.",
            "metadata": {"status": "active"},
            "created_at": now_utc() - timedelta(seconds=2),
        }
    )
    return tokens


def request(base_url: str, path: str, token: str | None = None) -> tuple[int, dict]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    req = urllib.request.Request(f"{base_url}{path}", headers=headers)
    try:
        response = urllib.request.urlopen(req, timeout=10)
    except urllib.error.HTTPError as exc:
        response = exc
    with response:
        raw = response.read().decode("utf-8")
        return response.status, json.loads(raw) if raw else {}


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_server(base_url: str) -> None:
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        try:
            status_code, _ = request(base_url, "/api/health")
            if status_code == 200:
                return
        except (OSError, urllib.error.URLError):
            time.sleep(0.05)
    raise AssertionError("Disposable audit isolation server did not become ready.")


def assert_status(base_url: str, path: str, expected: int, token: str | None = None) -> dict:
    actual, payload = request(base_url, path, token)
    if actual != expected:
        raise AssertionError(f"{path} returned {actual}, expected {expected}: {payload}")
    return payload


async def verify_source_truth_preserved() -> None:
    stored = await database.collection("audit_events").find_one({"id": "audit-smoke-event-sensitive"})
    if (stored or {}).get("metadata", {}).get("password") != "audit-super-secret":
        raise AssertionError("Read projection mutated persisted audit source truth.")


def verify_access_matrix(base_url: str, tokens: dict[str, str]) -> None:
    assert_status(base_url, "/api/audit-events", 401)
    assert_status(base_url, "/api/audit-events", 403, tokens["portal"])
    assert_status(base_url, "/api/audit-events", 403, tokens["agency_owner"])
    assert_status(base_url, "/api/audit-events", 403, tokens["platform_support"])

    legacy = assert_status(base_url, "/api/audit-events?limit=1", 200, tokens["platform_owner"])
    if legacy.get("canonical_route") != "/api/platform/audit-events" or legacy.get("deprecated") is not True:
        raise AssertionError("Legacy audit route did not identify its protected canonical replacement.")

    assert_status(base_url, "/api/platform/audit-events", 403, tokens["platform_support"])
    assert_status(base_url, "/api/platform/audit-events", 200, tokens["platform_admin"])
    platform = assert_status(base_url, "/api/platform/audit-events?limit=2", 200, tokens["platform_owner"])
    if len(platform.get("items") or []) != 2 or (platform.get("pagination") or {}).get("has_more") is not True:
        raise AssertionError(f"Platform audit pagination is not bounded: {platform}")

    agency_path = f"/api/agencies/{AGENCY_ONE}/audit-events"
    assert_status(base_url, agency_path, 403, tokens["portal"])
    assert_status(base_url, agency_path, 403, tokens["agency_readonly"])
    assert_status(base_url, f"/api/agencies/{AGENCY_TWO}/audit-events", 403, tokens["agency_owner"])
    agency = assert_status(base_url, f"{agency_path}?event_type=request.reviewed", 200, tokens["agency_owner"])
    if agency.get("scope") != "agency" or agency.get("agency_id") != AGENCY_ONE:
        raise AssertionError(f"Agency audit response did not preserve tenant scope: {agency}")
    if not agency.get("items") or any(item.get("agency_id") != AGENCY_ONE for item in agency["items"]):
        raise AssertionError(f"Agency audit response leaked cross-tenant records: {agency}")

    serialized = json.dumps(agency, sort_keys=True)
    if any(value in serialized for value in SENSITIVE_VALUES):
        raise AssertionError(f"Audit projection leaked restricted metadata: {serialized}")
    if "[REDACTED]" not in serialized:
        raise AssertionError("Audit projection did not visibly redact restricted metadata.")


def main() -> int:
    assert_application_phase_at_least(CURRENT_BUILD_PHASE, MINIMUM_PHASE, source="canonical build phase")
    tokens = asyncio.run(seed_fixture())
    port = free_port()
    base_url = f"http://127.0.0.1:{port}"
    uvicorn_server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="critical", lifespan="off")
    )
    thread = threading.Thread(target=uvicorn_server.run, daemon=True)
    thread.start()
    try:
        wait_for_server(base_url)
        verify_access_matrix(base_url, tokens)
        asyncio.run(verify_source_truth_preserved())
    finally:
        uvicorn_server.should_exit = True
        thread.join(timeout=10)
    if thread.is_alive():
        raise AssertionError("Disposable audit isolation server did not stop.")
    print("Audit event isolation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
