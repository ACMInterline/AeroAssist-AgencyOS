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
EXPECTED_PHASE = "phase_39_4_platform_agency_ux_consolidation"


def request(method: str, path: str, body: dict | None = None, headers: dict | None = None, expect: int | None = None) -> tuple[int, dict]:
    data = json.dumps(body or {}).encode("utf-8") if body is not None else None
    req = urllib.request.Request(f"{BASE_URL}{path}", method=method, data=data, headers={**(headers or {}), "Content-Type": "application/json"})
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


def main() -> int:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")
    post("/api/reference/seed", {}, OWNER_HEADERS)
    reference = get("/api/reference/service-catalogue", OWNER_HEADERS)
    if "WCHR" not in {item["service_code"] for item in reference["items"]}:
        raise AssertionError("Reference service catalogue missing WCHR.")
    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    client_id = get(f"/api/agencies/{agency_id}/clients", OWNER_HEADERS)["items"][0]["id"]
    now = int(time.time())
    payload = {
        "client": {"client_id": client_id},
        "passengers": [{"request_passenger_key": "inline-0", "first_name": "Scoped", "last_name": "Traveler", "passenger_type": "adult"}],
        "trip_type": "multi_city",
        "segments": [
            {"segment_key": "1", "sequence": 1, "origin_text": "SOF", "destination_text": "FRA", "departure_date": "2026-08-01"},
            {"segment_key": "2", "sequence": 2, "origin_text": "FRA", "destination_text": "JFK", "departure_date": "2026-08-02"},
        ],
        "services": [
            {
                "category": "mobility_assistance",
                "service_code": "WCHR",
                "service_family_code": "wheelchair_mobility",
                "applies_to_all_passengers": False,
                "passenger_ids": ["inline-0"],
                "applies_to_all_segments": False,
                "segment_ids": ["1"],
                "details": {
                    "assessment_version": "v2_assessment_driven",
                    "functional_assessment": {"needs_wheelchair_for_distance": "yes", "can_walk_short_distances": "yes", "can_climb_aircraft_stairs": "yes"},
                    "suggested_ssr_code": "WCHR",
                    "confirmed_ssr_code": "WCHR",
                    "mobility_level": "wchr",
                },
            },
            {
                "category": "medical_travel",
                "service_code": "POC",
                "service_family_code": "medical_assistance",
                "applies_to_all_passengers": False,
                "passenger_ids": ["inline-0"],
                "applies_to_all_segments": False,
                "segment_ids": ["2"],
                "details": {"ssr_code": "POC", "requires_poc": True, "battery_count": 2, "battery_duration_hours": 8},
            },
        ],
        "pets": [
            {
                "pet_key": "pet-1",
                "request_passenger_key": "inline-0",
                "pet_name": "Milo",
                "species": "dog",
                "breed_free_text": "Mixed",
                "pet_weight_kg": 7,
                "container_weight_kg": 2,
                "combined_weight_kg": 9,
                "requested_transport_mode": "petc",
                "documentation_status": "pending_information",
                "segment_transports": [{"segment_key": "2", "requested_transport_mode": "petc"}],
            }
        ],
        "special_items": [
            {
                "item_key": "item-1",
                "item_category_code": "sports_equipment",
                "item_name": "Foldable bike",
                "description": "Packed sports equipment",
                "quantity": 1,
                "weight_kg": 12,
                "transport_location": "checked_baggage",
                "documentation_status": "pending_information",
                "segment_transports": [{"segment_key": "1", "transport_location": "checked_baggage"}, {"segment_key": "2", "transport_location": "checked_baggage"}],
            }
        ],
        "title": f"Phase 34 scoped request {now}",
        "status": "triage",
        "source": "staff_created",
        "priority": "normal",
    }
    created = post(f"/api/agencies/{agency_id}/requests/builder", payload, OWNER_HEADERS, 201)
    request_id = created["request"]["id"]
    detail = get(f"/api/agencies/{agency_id}/requests/{request_id}", OWNER_HEADERS)
    if len(detail["segments"]) != 2 or len(detail["passengers"]) != 1:
        raise AssertionError("Request did not create expected passengers and segments.")
    if len(detail["passenger_segment_services"]) != 2:
        raise AssertionError(f"Expected two passenger-segment services, got {len(detail['passenger_segment_services'])}.")
    if len(detail["pets"]) != 1 or len(detail["pet_segment_transport"]) != 1:
        raise AssertionError("Pet and pet segment transport rows were not normalized.")
    if len(detail["special_items"]) != 1 or len(detail["special_item_segments"]) != 2:
        raise AssertionError("Special item and segment rows were not normalized.")
    request_root = detail["request"]
    if request_root["pet_count"] != 1 or request_root["special_service_count"] < 4:
        raise AssertionError("Root counters were not updated from normalized records.")
    flags = {item["flag_code"] for item in detail["case_flags"]}
    for flag in ["segment_scoped_services", "medical_review", "document_followup", "pet_transport", "special_items"]:
        if flag not in flags:
            raise AssertionError(f"Missing derived case flag: {flag}")

    before = {key: len(detail[key]) for key in ["passenger_segment_services", "pets", "pet_segment_transport", "special_items", "special_item_segments"]}
    post(f"/api/agencies/{agency_id}/requests/{request_id}/normalize", {}, OWNER_HEADERS)
    after_detail = get(f"/api/agencies/{agency_id}/requests/{request_id}", OWNER_HEADERS)
    after = {key: len(after_detail[key]) for key in before}
    if before != after:
        raise AssertionError(f"Normalization duplicated records: before={before}, after={after}")

    invalid_payload = {**payload, "title": f"Invalid scoped request {now}", "services": [{**payload["services"][0], "applies_to_all_segments": False, "segment_ids": []}]}
    post(f"/api/agencies/{agency_id}/requests/builder", invalid_payload, OWNER_HEADERS, 400)

    public_submission = post(
        "/api/public/request-intakes",
        {
            "contact": {"name": "Phase 34 Public", "email": f"phase34-{now}@example.com", "privacy_policy_accepted": True, "data_processing_consent": True},
            "travel": {"origin": "SOF", "destination": "JFK", "passenger_count": 1},
            "services": {"selected_service_categories": ["mobility assistance"], "mobility_assistance": True},
            "request_details": "Need simplified public mobility assistance intake.",
        },
        expect=201,
    )
    if public_submission["intake"]["status"] != "received":
        raise AssertionError("Public request submission compatibility failed.")

    readiness = get("/api/readiness")
    scoped = readiness.get("segment_scoped_requests") or {}
    for flag in ["segment_scoped_services_enabled", "request_service_normalization_enabled"]:
        if scoped.get(flag) is not True:
            raise AssertionError(f"Readiness missing scoped request flag: {flag}")
    print("Segment-scoped request services smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Segment-scoped request services smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
