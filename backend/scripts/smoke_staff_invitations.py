#!/usr/bin/env python3
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


BASE_URL = os.getenv("AEROASSIST_SMOKE_BASE_URL", "http://localhost:8000")
OWNER_TOKEN = os.getenv("AEROASSIST_SMOKE_OWNER_TOKEN")
OWNER_HEADERS = {"Authorization": f"Bearer {OWNER_TOKEN}"} if OWNER_TOKEN else {"X-Demo-User-Email": "owner@aeroassist.dev"}


def request(method: str, path: str, body: dict | None = None, headers: dict | None = None, expect: int | None = None) -> tuple[int, dict]:
    data = json.dumps(body or {}).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        method=method,
        data=data,
        headers={**(headers or {}), "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            payload = response.read().decode("utf-8")
            status = response.status
            result = json.loads(payload) if payload else {}
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8")
        status = exc.code
        result = json.loads(payload) if payload else {}
    if expect is not None and status != expect:
        raise AssertionError(f"{method} {path} expected {expect}, got {status}: {result}")
    if expect is None and status >= 400:
        raise AssertionError(f"{method} {path} failed with {status}: {result}")
    return status, result


def get(path: str, headers: dict | None = None, expect: int | None = None) -> dict:
    return request("GET", path, None, headers, expect)[1]


def post(path: str, body: dict, headers: dict | None = None, expect: int | None = None) -> dict:
    return request("POST", path, body, headers, expect)[1]


def assert_no_token_fields(value: object) -> None:
    serialized = json.dumps(value)
    forbidden = ["token_hash", "one_time_token", "dev_invitation_token"]
    leaked = [field for field in forbidden if field in serialized]
    if leaked:
        raise AssertionError(f"Unsafe token fields leaked: {leaked}")


def main() -> int:
    get("/api/health")
    post("/api/reference/seed", {}, OWNER_HEADERS)
    agencies = get("/api/agencies", OWNER_HEADERS)["items"]
    if not agencies:
        raise AssertionError("No agency available for invitation smoke.")
    agency_id = agencies[0]["id"]
    workspaces = get(f"/api/agencies/{agency_id}/workspaces", OWNER_HEADERS)["items"]
    workspace_id = workspaces[0]["id"] if workspaces else None
    email = f"staff.invite.{int(time.time())}@example.com"
    body = {
        "email": email,
        "invited_name": "Staff Invite Smoke",
        "agency_role": "agency_agent",
        "workspace_id": workspace_id,
    }

    created = post(f"/api/agencies/{agency_id}/staff/invitations", body, OWNER_HEADERS, 201)
    raw_token = created.get("one_time_token")
    if not raw_token or not created.get("accept_url"):
        raise AssertionError("Create response must include one-time token and accept_url.")
    if "token_hash" in json.dumps(created):
        raise AssertionError("Create response leaked token_hash.")

    invitations = get(f"/api/agencies/{agency_id}/staff/invitations", OWNER_HEADERS)["items"]
    assert_no_token_fields(invitations)
    if not any(item["id"] == created["invitation"]["id"] for item in invitations):
        raise AssertionError("Created invitation not found in list.")

    post(f"/api/agencies/{agency_id}/staff/invitations", body, OWNER_HEADERS, 409)
    post(
        f"/api/agencies/{agency_id}/staff/invitations",
        {**body, "email": f"owner.{email}", "agency_role": "agency_owner"},
        OWNER_HEADERS,
        400,
    )
    get("/api/auth/invitations/validate?token=not-real", expect=400)
    validated = get(f"/api/auth/invitations/validate?token={urllib.parse.quote(raw_token)}")
    assert_no_token_fields(validated)
    if validated["invitation"]["invited_email"] != email:
        raise AssertionError("Validate response returned wrong invited email.")

    post(f"/api/agencies/{agency_id}/staff/invitations/{created['invitation']['id']}/revoke", {}, OWNER_HEADERS)
    post("/api/auth/invitations/accept", {"token": raw_token, "email": email, "password": "SmokePass123!"}, expect=400)

    accepted_invite = post(
        f"/api/agencies/{agency_id}/staff/invitations",
        {**body, "email": f"accepted.{email}"},
        OWNER_HEADERS,
        201,
    )
    accepted_token = accepted_invite["one_time_token"]
    accepted_email = accepted_invite["invitation"]["invited_email"]
    accepted = post(
        "/api/auth/invitations/accept",
        {"token": accepted_token, "email": accepted_email, "password": "SmokePass123!", "display_name": "Accepted Smoke"},
    )
    if accepted["invitation"]["status"] != "accepted":
        raise AssertionError("Invitation was not marked accepted.")
    post(
        "/api/auth/invitations/accept",
        {"token": accepted_token, "email": accepted_email, "password": "SmokePass123!"},
        expect=400,
    )

    staff = get(f"/api/agencies/{agency_id}/staff", OWNER_HEADERS)["items"]
    memberships = [item for item in staff if item.get("user", {}).get("email") == accepted_email]
    if len(memberships) != 1 or memberships[0]["membership"]["status"] != "active":
        raise AssertionError("Accepted invitation did not create exactly one active membership.")

    audit_events = get("/api/audit-events").get("items", [])
    audit_serialized = json.dumps(audit_events)
    if raw_token in audit_serialized or accepted_token in audit_serialized or "token_hash" in audit_serialized:
        raise AssertionError("Audit events leaked invitation token material.")

    print("Staff invitation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Staff invitation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
