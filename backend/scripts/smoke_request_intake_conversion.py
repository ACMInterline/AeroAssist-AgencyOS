#!/usr/bin/env python3
import json
import os
import sys
import time
import urllib.error
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


def post(path: str, body: dict | None = None, headers: dict | None = None, expect: int | None = None) -> dict:
    return request("POST", path, body or {}, headers, expect)[1]


def patch(path: str, body: dict, headers: dict | None = None, expect: int | None = None) -> dict:
    return request("PATCH", path, body, headers, expect)[1]


def assert_safe_public_response(value: object) -> None:
    serialized = json.dumps(value)
    forbidden = ["internal_notes", "assigned_to", "raw_payload", "canonical_payload", "token_hash", "agency_role"]
    leaked = [field for field in forbidden if field in serialized]
    if leaked:
        raise AssertionError(f"Public response leaked internal fields: {leaked}")


def intake_payload(email: str) -> dict:
    return {
        "contact": {
            "name": "Phase 26 Smoke Client",
            "email": email,
            "phone": "+421900000000",
            "privacy_policy_accepted": True,
            "data_processing_consent": True,
        },
        "travel": {
            "origin": "Bratislava",
            "destination": "London",
            "departure_date": "2026-08-01",
            "return_date": "2026-08-15",
            "passenger_count": 2,
            "itinerary_notes": "Wheelchair assistance and planning support requested.",
        },
        "services": {
            "selected_service_categories": ["mobility assistance", "booking planning"],
            "mobility_assistance": True,
            "medical_travel": False,
            "pet_travel": False,
            "child_or_unaccompanied_minor": False,
            "special_baggage": False,
            "documents_or_visa": False,
            "disruption_or_claims": False,
            "booking_or_planning": True,
            "other": False,
        },
        "request_details": "Client needs assistance booking and moving through airports.",
    }


def main() -> int:
    health = get("/api/health")
    if health.get("phase") != "phase_39_5_saas_subscription_entitlement_foundation":
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")
    post("/api/reference/seed", {}, OWNER_HEADERS)
    get("/api/request-intakes", {"Authorization": "Bearer definitely-not-valid"}, 401)

    email = f"phase26.{int(time.time())}@example.com"
    unsafe = intake_payload(email)
    unsafe["status"] = "converted"
    post("/api/public/request-intakes", unsafe, expect=422)
    public_created = post("/api/public/request-intakes", intake_payload(email), expect=201)
    assert_safe_public_response(public_created)
    intake_id = public_created["intake"]["id"]
    if public_created["intake"]["status"] != "received":
        raise AssertionError("Public endpoint did not return safe received status.")

    listed = get("/api/request-intakes", OWNER_HEADERS)
    if not any(item["id"] == intake_id for item in listed["items"]):
        raise AssertionError("Created intake was not visible to staff.")
    detail = get(f"/api/request-intakes/{intake_id}", OWNER_HEADERS)
    if detail["intake"].get("status") != "new":
        raise AssertionError("Intake was not stored as new.")
    if detail["intake"].get("assigned_to") or detail["intake"].get("internal_notes"):
        raise AssertionError("Public endpoint accepted internal fields.")

    triaged = patch(
        f"/api/request-intakes/{intake_id}/triage",
        {"priority": "high", "triage_notes": "Smoke triage note"},
        OWNER_HEADERS,
    )
    if triaged["intake"]["status"] != "triaged" or triaged["intake"]["priority"] != "high":
        raise AssertionError("Triage update failed.")

    converted = post(f"/api/request-intakes/{intake_id}/convert", {}, OWNER_HEADERS)
    request_id = converted["request"]["id"]
    if converted.get("already_converted"):
        raise AssertionError("First conversion should not be marked already converted.")
    if converted["intake"]["converted_request_id"] != request_id:
        raise AssertionError("Converted request was not linked to intake.")

    converted_again = post(f"/api/request-intakes/{intake_id}/convert", {}, OWNER_HEADERS)
    if not converted_again.get("already_converted") or converted_again["request"]["id"] != request_id:
        raise AssertionError("Repeated conversion did not return existing request.")

    request_detail = get(f"/api/agencies/{converted['request']['agency_id']}/requests/{request_id}", OWNER_HEADERS)
    if request_detail["request"].get("source_intake_id") != intake_id:
        raise AssertionError("Operational request does not link back to intake.")
    if len([item for item in get("/api/request-intakes", OWNER_HEADERS)["items"] if item.get("converted_request_id") == request_id]) != 1:
        raise AssertionError("Duplicate converted intake linkage detected.")

    second = post("/api/public/request-intakes", intake_payload(f"phase26.reject.{int(time.time())}@example.com"), expect=201)
    rejected = post(f"/api/request-intakes/{second['intake']['id']}/reject", {"reason": "Smoke rejection"}, OWNER_HEADERS)
    if rejected["intake"]["status"] != "rejected":
        raise AssertionError("Reject action failed.")

    readiness = get("/api/readiness")
    if not readiness.get("ok"):
        raise AssertionError("Readiness is not ok.")
    if "request_intake" not in readiness:
        raise AssertionError("Readiness does not expose request intake summary.")

    print("Request intake conversion smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Request intake conversion smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
