#!/usr/bin/env python3
import json
import os
import sys
import time
import urllib.error
import urllib.request


BASE_URL = os.getenv("AEROASSIST_SMOKE_BASE_URL", "http://localhost:8000")
OWNER_TOKEN = os.getenv("AEROASSIST_SMOKE_OWNER_TOKEN")
OWNER_HEADERS = (
    {"Authorization": f"Bearer {OWNER_TOKEN}"}
    if OWNER_TOKEN
    else {"X-Demo-User-Email": "owner@aeroassist.dev"}
)
EXPECTED_PHASE = "phase_55_8_airline_contact_communication_intelligence_foundation"


def request(
    method: str,
    path: str,
    body: dict | None = None,
    headers: dict | None = None,
    expect: int | None = None,
) -> tuple[int, dict]:
    data = json.dumps(body or {}).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        method=method,
        data=data,
        headers={**(headers or {}), "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
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


def post(
    path: str,
    body: dict | None = None,
    headers: dict | None = None,
    expect: int | None = None,
) -> dict:
    return request("POST", path, body or {}, headers, expect)[1]


def assert_openapi_path(paths: dict, path: str, method: str) -> None:
    if method.lower() not in paths.get(path, {}):
        raise AssertionError(f"OpenAPI missing {method.upper()} {path}")


def builder_payload(email: str) -> dict:
    return {
        "client": {
            "name": "Phase 36.2 Acceptance Client",
            "email": email,
            "phone": "+421900000362",
        },
        "passengers": [
            {
                "request_passenger_key": "pax-1",
                "first_name": "Accepted",
                "last_name": "Traveler",
                "passenger_type": "adult",
            }
        ],
        "trip_type": "one_way",
        "segments": [
            {
                "segment_key": "seg-1",
                "sequence": 1,
                "origin_text": "SOF",
                "destination_text": "FRA",
                "departure_date": "2026-12-12",
                "marketing_airline": "LH",
                "operating_airline": "LH",
                "flight_number": "LH1703",
                "cabin_preference": "economy",
            }
        ],
        "services": [
            {
                "category": "mobility_assistance",
                "service_code": "WCHR",
                "details": {"confirmed_ssr_code": "WCHR", "notes": "Wheelchair for long airport distance."},
                "applies_to_all_passengers": True,
                "applies_to_all_segments": True,
            }
        ],
        "title": "Phase 36.2 offer acceptance smoke",
        "status": "new",
        "priority": "normal",
        "source": "staff_created",
    }


def create_priced_option(agency_id: str, workspace_id: str) -> dict:
    option = post(
        f"/api/agencies/{agency_id}/offer-workspaces/{workspace_id}/options",
        {
            "label": "Accepted LH economy",
            "option_type": "flight",
            "main_airline_code": "LH",
            "provider_name": "manual",
        },
        OWNER_HEADERS,
        201,
    )["option"]
    option_id = option["id"]
    post(
        f"/api/agencies/{agency_id}/offer-options/{option_id}/segments",
        {
            "sequence": 1,
            "marketing_airline_code": "LH",
            "operating_airline_code": "LH",
            "flight_number": "1703",
            "origin_airport": "SOF",
            "destination_airport": "FRA",
            "departure_at": "2026-12-12T06:00:00Z",
            "arrival_at": "2026-12-12T07:25:00Z",
            "aircraft_type": "A320",
            "cabin_class": "economy",
            "booking_class": "Y",
            "fare_basis": "YACCEPT",
        },
        OWNER_HEADERS,
        201,
    )
    post(
        f"/api/agencies/{agency_id}/offer-options/{option_id}/fare-bundles",
        {
            "fare_family_name": "Economy Flex",
            "cabin_class": "economy",
            "booking_class": "Y",
            "included_baggage_json": {"checked_bags": 1},
        },
        OWNER_HEADERS,
        201,
    )
    for line_type, label, amount in [
        ("base_fare", "Base fare", 120.0),
        ("tax", "Airport taxes", 30.0),
        ("service_fee", "Agency service fee", 12.0),
    ]:
        post(
            f"/api/agencies/{agency_id}/offer-options/{option_id}/pricing-lines",
            {"line_type": line_type, "label": label, "amount": amount, "currency": "EUR"},
            OWNER_HEADERS,
            201,
        )
    post(f"/api/agencies/{agency_id}/offer-options/{option_id}/recalculate-pricing", {}, OWNER_HEADERS)
    post(f"/api/agencies/{agency_id}/offer-options/{option_id}/evaluate-rules", {}, OWNER_HEADERS)
    return option


def main() -> int:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")

    openapi = get("/openapi.json")
    paths = openapi.get("paths") or {}
    for path, method in [
        ("/api/agencies/{agency_id}/offer-workspaces/{workspace_id}/options/{option_id}/accept", "post"),
        ("/api/agencies/{agency_id}/offer-workspaces/{workspace_id}/acceptance", "get"),
        ("/api/agencies/{agency_id}/trips/{trip_id}/accepted-offer", "get"),
        ("/api/agencies/{agency_id}/trips/{trip_id}/booking-readiness", "get"),
        ("/api/agencies/{agency_id}/offer-acceptances/{acceptance_id}/booking-readiness/rebuild", "post"),
        ("/api/agencies/{agency_id}/offer-acceptances/{acceptance_id}/cancel", "post"),
    ]:
        assert_openapi_path(paths, path, method)

    readiness = get("/api/readiness")
    offer_builder = readiness.get("offer_builder") or {}
    for key in [
        "offer_acceptance_enabled",
        "accepted_offer_snapshot_enabled",
        "booking_readiness_package_enabled",
        "offer_to_trip_acceptance_enabled",
        "rules_aware_acceptance_enabled",
        "ssr_osi_booking_preview_enabled",
        "agency_acceptance_ui_enabled",
    ]:
        if offer_builder.get(key) is not True:
            raise AssertionError(f"Readiness missing offer acceptance flag: {key}")
    for key in [
        "offer_acceptance_count",
        "trip_accepted_offer_snapshot_count",
        "booking_readiness_package_count",
    ]:
        if key not in offer_builder:
            raise AssertionError(f"Readiness missing offer acceptance count: {key}")

    post("/api/reference/seed", {}, OWNER_HEADERS)
    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    created_request = post(
        f"/api/agencies/{agency_id}/requests/builder",
        builder_payload(f"phase362.{int(time.time())}@example.com"),
        OWNER_HEADERS,
        201,
    )
    request_id = created_request["request"]["id"]
    workspace = post(
        f"/api/agencies/{agency_id}/requests/{request_id}/offer-workspace",
        {},
        OWNER_HEADERS,
        201,
    )["workspace"]
    workspace_id = workspace["id"]
    option = create_priced_option(agency_id, workspace_id)
    option_id = option["id"]

    accepted = post(
        f"/api/agencies/{agency_id}/offer-workspaces/{workspace_id}/options/{option_id}/accept",
        {"acceptance_source": "internal", "provider_target": "manual"},
        OWNER_HEADERS,
        201,
    )
    acceptance = accepted["acceptance"]
    trip_id = acceptance.get("trip_id")
    if not acceptance.get("id") or acceptance.get("status") != "accepted":
        raise AssertionError("Offer acceptance was not created as accepted.")
    if not trip_id:
        raise AssertionError("Accepting a request workspace should create or link a trip.")
    if not accepted.get("trip_snapshot"):
        raise AssertionError("Trip accepted-offer snapshot was not created.")
    readiness_package = accepted.get("booking_readiness") or {}
    if readiness_package.get("status") not in {"draft", "ready", "blocked"}:
        raise AssertionError(f"Unexpected booking readiness status: {readiness_package}")
    if "ssr_json" not in readiness_package or "osi_json" not in readiness_package:
        raise AssertionError("Booking readiness did not include SSR/OSI preview fields.")
    if "warnings_json" not in readiness_package:
        raise AssertionError("Booking readiness did not include warnings.")

    workspace_acceptance = get(
        f"/api/agencies/{agency_id}/offer-workspaces/{workspace_id}/acceptance",
        OWNER_HEADERS,
    )
    if workspace_acceptance.get("acceptance", {}).get("id") != acceptance["id"]:
        raise AssertionError("Workspace acceptance lookup did not return the active acceptance.")
    trip_offer = get(f"/api/agencies/{agency_id}/trips/{trip_id}/accepted-offer", OWNER_HEADERS)
    if trip_offer.get("accepted_offer", {}).get("acceptance_id") != acceptance["id"]:
        raise AssertionError("Trip accepted-offer lookup did not return the acceptance snapshot.")
    trip_readiness = get(f"/api/agencies/{agency_id}/trips/{trip_id}/booking-readiness", OWNER_HEADERS)
    if trip_readiness.get("booking_readiness", {}).get("acceptance_id") != acceptance["id"]:
        raise AssertionError("Trip booking readiness lookup did not return the readiness package.")

    rebuilt = post(
        f"/api/agencies/{agency_id}/offer-acceptances/{acceptance['id']}/booking-readiness/rebuild",
        {},
        OWNER_HEADERS,
    )
    if rebuilt.get("booking_readiness", {}).get("acceptance_id") != acceptance["id"]:
        raise AssertionError("Booking readiness rebuild did not return the acceptance package.")

    clone = post(f"/api/agencies/{agency_id}/offer-options/{option_id}/clone", {}, OWNER_HEADERS, 201)["option"]
    second_acceptance = post(
        f"/api/agencies/{agency_id}/offer-workspaces/{workspace_id}/options/{clone['id']}/accept",
        {"acceptance_source": "manual", "provider_target": "manual"},
        OWNER_HEADERS,
        201,
    )["acceptance"]
    history = (
        get(f"/api/agencies/{agency_id}/offer-workspaces/{workspace_id}/acceptance", OWNER_HEADERS).get("history")
        or []
    )
    previous = [item for item in history if item["id"] == acceptance["id"]]
    if not previous or previous[0].get("status") != "superseded":
        raise AssertionError("Previous accepted offer was not superseded safely.")

    cancelled = post(
        f"/api/agencies/{agency_id}/offer-acceptances/{second_acceptance['id']}/cancel",
        {},
        OWNER_HEADERS,
    )
    if cancelled.get("acceptance", {}).get("status") != "cancelled":
        raise AssertionError("Cancellation did not mark acceptance cancelled.")
    if cancelled.get("booking_readiness", {}).get("status") != "cancelled":
        raise AssertionError("Cancellation did not mark linked readiness package cancelled.")

    print("Offer acceptance and booking readiness smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Offer acceptance and booking readiness smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
