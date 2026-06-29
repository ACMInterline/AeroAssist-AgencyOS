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
EXPECTED_PHASE = "phase_36_4_6_standalone_change_exchange_foundation"


def request(method: str, path: str, body: dict | None = None, headers: dict | None = None, expect: int | None = None) -> tuple[int, dict]:
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


def post(path: str, body: dict | None = None, headers: dict | None = None, expect: int | None = None) -> dict:
    return request("POST", path, body or {}, headers, expect)[1]


def put(path: str, body: dict | None = None, headers: dict | None = None, expect: int | None = None) -> dict:
    return request("PUT", path, body or {}, headers, expect)[1]


def assert_openapi_path(paths: dict, path: str, method: str) -> None:
    if method.lower() not in paths.get(path, {}):
        raise AssertionError(f"OpenAPI missing {method.upper()} {path}")


def builder_payload(email: str) -> dict:
    return {
        "client": {"name": "Phase 36.1 Offer Client", "email": email, "phone": "+421900000361"},
        "passengers": [{"request_passenger_key": "pax-1", "first_name": "Offer", "last_name": "Traveler", "passenger_type": "adult"}],
        "trip_type": "one_way",
        "segments": [
            {
                "segment_key": "seg-1",
                "sequence": 1,
                "origin_text": "SOF",
                "destination_text": "FRA",
                "departure_date": "2026-11-15",
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
                "details": {"confirmed_ssr_code": "WCHR", "notes": "Wheelchair for airport distance."},
                "applies_to_all_passengers": True,
                "applies_to_all_segments": True,
            }
        ],
        "title": "Phase 36.1 offer builder smoke",
        "status": "new",
        "priority": "normal",
        "source": "staff_created",
    }


def main() -> int:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")

    openapi = get("/openapi.json")
    paths = openapi.get("paths") or {}
    for path, method in [
        ("/api/agencies/{agency_id}/offer-workspaces", "get"),
        ("/api/agencies/{agency_id}/offer-workspaces", "post"),
        ("/api/agencies/{agency_id}/offer-workspaces/{workspace_id}", "get"),
        ("/api/agencies/{agency_id}/requests/{request_id}/offer-workspace", "post"),
        ("/api/agencies/{agency_id}/trips/{trip_id}/offer-workspace", "post"),
        ("/api/agencies/{agency_id}/offer-workspaces/{workspace_id}/options", "post"),
        ("/api/agencies/{agency_id}/offer-options/{option_id}/evaluate-rules", "post"),
        ("/api/agencies/{agency_id}/offer-options/{option_id}/recalculate-pricing", "post"),
        ("/api/agencies/{agency_id}/offer-workspaces/{workspace_id}/comparison", "get"),
        ("/api/agencies/{agency_id}/offer-workspaces/{workspace_id}/comparison/snapshot", "post"),
        ("/api/agencies/{agency_id}/offer-workspaces/{workspace_id}/recommend", "post"),
    ]:
        assert_openapi_path(paths, path, method)

    post("/api/reference/seed", {}, OWNER_HEADERS)
    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    created_request = post(
        f"/api/agencies/{agency_id}/requests/builder",
        builder_payload(f"phase361.{int(time.time())}@example.com"),
        OWNER_HEADERS,
        201,
    )
    request_id = created_request["request"]["id"]
    trip = post(f"/api/agencies/{agency_id}/trips/from-request/{request_id}", {}, OWNER_HEADERS, 201)["trip"]

    request_workspace = post(f"/api/agencies/{agency_id}/requests/{request_id}/offer-workspace", {}, OWNER_HEADERS, 201)["workspace"]
    trip_workspace = post(f"/api/agencies/{agency_id}/trips/{trip['id']}/offer-workspace", {}, OWNER_HEADERS, 201)["workspace"]
    if request_workspace["id"] != trip_workspace["id"]:
        raise AssertionError("Request and trip workspace entry points should converge on the same workspace.")
    workspace_id = request_workspace["id"]

    workspace_list = get(f"/api/agencies/{agency_id}/offer-workspaces?request_id={request_id}", OWNER_HEADERS)["items"]
    if workspace_id not in {item["id"] for item in workspace_list}:
        raise AssertionError("Created offer workspace was not returned by request filter.")

    option = post(
        f"/api/agencies/{agency_id}/offer-workspaces/{workspace_id}/options",
        {"label": "Recommended LH economy", "option_type": "flight", "main_airline_code": "LH", "provider_name": "manual"},
        OWNER_HEADERS,
        201,
    )["option"]
    option_id = option["id"]
    updated = put(f"/api/agencies/{agency_id}/offer-options/{option_id}", {"internal_notes": "Smoke option update."}, OWNER_HEADERS)["option"]
    if updated.get("internal_notes") != "Smoke option update.":
        raise AssertionError("Offer option update did not persist.")

    segment = post(
        f"/api/agencies/{agency_id}/offer-options/{option_id}/segments",
        {
            "sequence": 1,
            "marketing_airline_code": "LH",
            "operating_airline_code": "LH",
            "flight_number": "1703",
            "origin_airport": "SOF",
            "destination_airport": "FRA",
            "departure_at": "2026-11-15T06:00:00Z",
            "arrival_at": "2026-11-15T07:25:00Z",
            "aircraft_type": "A320",
            "cabin_class": "economy",
            "booking_class": "Y",
            "fare_basis": "YSMOKE",
        },
        OWNER_HEADERS,
        201,
    )["segment"]
    if segment["origin_airport"] != "SOF":
        raise AssertionError("Offer segment was not created.")

    fare_bundle = post(
        f"/api/agencies/{agency_id}/offer-options/{option_id}/fare-bundles",
        {
            "fare_family_name": "Economy Flex",
            "cabin_class": "economy",
            "booking_class": "Y",
            "included_baggage_json": {"checked_bags": 1},
            "change_rules_json": {"changes": "permitted_with_fee"},
            "refund_rules_json": {"refunds": "partially_refundable"},
        },
        OWNER_HEADERS,
        201,
    )["fare_bundle"]
    if fare_bundle["fare_family_name"] != "Economy Flex":
        raise AssertionError("Fare bundle was not created.")

    for line_type, label, amount in [
        ("base_fare", "Base fare", 100.0),
        ("tax", "Airport taxes", 25.0),
        ("service_fee", "Agency service fee", 10.0),
        ("commission", "Commission", -5.0),
    ]:
        post(
            f"/api/agencies/{agency_id}/offer-options/{option_id}/pricing-lines",
            {"line_type": line_type, "label": label, "amount": amount, "currency": "EUR"},
            OWNER_HEADERS,
            201,
        )
    pricing = post(f"/api/agencies/{agency_id}/offer-options/{option_id}/recalculate-pricing", {}, OWNER_HEADERS)
    if pricing["pricing_summary"]["total_amount"] != 130.0:
        raise AssertionError(f"Unexpected pricing total: {pricing['pricing_summary']}")

    evaluation = post(f"/api/agencies/{agency_id}/offer-options/{option_id}/evaluate-rules", {}, OWNER_HEADERS)
    if "rules_summary" not in evaluation or "service_feasibility" not in evaluation:
        raise AssertionError("Rule evaluation response missing structured summaries.")
    if evaluation["rules_summary"].get("evaluation_count", 0) < 1:
        raise AssertionError("Rule evaluation did not evaluate any segment/service pair.")

    comparison = get(f"/api/agencies/{agency_id}/offer-workspaces/{workspace_id}/comparison", OWNER_HEADERS)["matrix"]
    if comparison.get("option_count") != 1 or not comparison.get("rows") or not comparison.get("columns"):
        raise AssertionError("Comparison matrix did not include option rows and columns.")
    if not any(row.get("key") == "total" for row in comparison["rows"]):
        raise AssertionError("Comparison matrix missing pricing total row.")

    snapshot = post(f"/api/agencies/{agency_id}/offer-workspaces/{workspace_id}/comparison/snapshot", {}, OWNER_HEADERS, 201)["snapshot"]
    if snapshot.get("workspace_id") != workspace_id:
        raise AssertionError("Comparison snapshot did not persist workspace id.")

    recommendation = post(
        f"/api/agencies/{agency_id}/offer-workspaces/{workspace_id}/recommend",
        {"option_id": option_id, "tag": "Best balance", "rank": 1},
        OWNER_HEADERS,
    )["option"]
    if recommendation.get("status") != "recommended" or recommendation.get("recommendation_tag") != "Best balance":
        raise AssertionError("Offer recommendation did not persist.")

    clone = post(f"/api/agencies/{agency_id}/offer-options/{option_id}/clone", {}, OWNER_HEADERS, 201)["option"]
    if clone["id"] == option_id or clone.get("status") != "draft":
        raise AssertionError("Offer option clone did not create a draft copy.")

    detail = get(f"/api/agencies/{agency_id}/offer-workspaces/{workspace_id}", OWNER_HEADERS)
    if len(detail.get("options") or []) < 2 or not detail.get("segments") or not detail.get("pricing_lines"):
        raise AssertionError("Workspace detail did not include option child records.")

    readiness = get("/api/readiness")
    offer_builder = readiness.get("offer_builder") or {}
    for key in [
        "offer_workspace_foundation_enabled",
        "rule_aware_offer_options_enabled",
        "internal_comparison_matrix_enabled",
        "workspace_request_entrypoint_enabled",
        "workspace_trip_entrypoint_enabled",
        "rule_evaluation_in_offer_builder_enabled",
        "pricing_recalculation_enabled",
        "recommendation_flagging_enabled",
    ]:
        if offer_builder.get(key) is not True:
            raise AssertionError(f"Readiness missing offer-builder flag: {key}")
    for key in ["offer_workspace_count", "offer_option_count", "offer_segment_count", "offer_pricing_line_count", "offer_comparison_snapshot_count"]:
        if key not in offer_builder:
            raise AssertionError(f"Readiness missing offer-builder count: {key}")

    print("Offer builder foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Offer builder foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
