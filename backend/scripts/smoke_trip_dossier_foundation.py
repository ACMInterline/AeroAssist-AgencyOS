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
READONLY_HEADERS = {"X-Demo-User-Email": "agency.readonly@aeroassist.dev"}
PORTAL_HEADERS = {"X-Demo-User-Email": "anna.client@example.com"}
EXPECTED_PHASE = "phase_35_trip_dossier_foundation"


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


def put(path: str, body: dict | None = None, headers: dict | None = None, expect: int | None = None) -> dict:
    return request("PUT", path, body or {}, headers, expect)[1]


def create_request(agency_id: str, client_id: str, title: str, suffix: str) -> dict:
    payload = {
        "client": {"client_id": client_id},
        "passengers": [{"request_passenger_key": f"pax-{suffix}", "first_name": "Trip", "last_name": f"Traveler {suffix}", "passenger_type": "adult"}],
        "trip_type": "multi_city",
        "segments": [
            {"segment_key": "1", "sequence": 1, "origin_text": "SOF", "destination_text": "CDG", "departure_date": "2026-09-01", "flight_number": "AF123"},
            {"segment_key": "2", "sequence": 2, "origin_text": "CDG", "destination_text": "JFK", "departure_date": "2026-09-02"},
        ],
        "services": [
            {
                "category": "mobility_assistance",
                "service_code": "WCHR",
                "service_family_code": "wheelchair_mobility",
                "applies_to_all_passengers": False,
                "passenger_ids": [f"pax-{suffix}"],
                "applies_to_all_segments": False,
                "segment_ids": ["1"],
                "details": {
                    "assessment_version": "v2_assessment_driven",
                    "functional_assessment": {"needs_wheelchair_for_distance": "yes", "can_walk_short_distances": "yes", "can_climb_aircraft_stairs": "yes"},
                    "suggested_ssr_code": "WCHR",
                    "confirmed_ssr_code": "WCHR",
                },
            }
        ],
        "pets": [{"pet_key": f"pet-{suffix}", "request_passenger_key": f"pax-{suffix}", "pet_name": "Milo", "species": "dog"}],
        "special_items": [{"item_key": f"item-{suffix}", "item_category_code": "sports_equipment", "description": "Packed bicycle"}],
        "title": title,
        "status": "triage",
        "source": "staff_created",
        "priority": "normal",
    }
    return post(f"/api/agencies/{agency_id}/requests/builder", payload, OWNER_HEADERS, 201)


def main() -> int:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")
    post("/api/reference/seed", {}, OWNER_HEADERS)
    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    client_id = get(f"/api/agencies/{agency_id}/clients", OWNER_HEADERS)["items"][0]["id"]

    manual = post(
        f"/api/agencies/{agency_id}/trips",
        {"trip_title": f"Manual phase 35 trip {int(time.time())}", "trip_status": "draft", "trip_type": "unknown"},
        OWNER_HEADERS,
        201,
    )["trip"]
    if not manual["trip_reference"].startswith("TRP-"):
        raise AssertionError("Manual trip did not generate a trip reference.")
    post(f"/api/agencies/{agency_id}/trips", {"trip_title": "Readonly should fail"}, READONLY_HEADERS, 403)
    get(f"/api/agencies/{agency_id}/trips", READONLY_HEADERS)

    created = create_request(agency_id, client_id, f"Phase 35 source request {int(time.time())}", "a")
    request_id = created["request"]["id"]
    request_before = get(f"/api/agencies/{agency_id}/requests/{request_id}", OWNER_HEADERS)
    trip = post(f"/api/agencies/{agency_id}/trips/from-request/{request_id}", {}, OWNER_HEADERS, 201)["trip"]
    if trip["id"] == request_id:
        raise AssertionError("Trip id must not equal request id.")
    if trip["primary_request_id"] != request_id or request_id not in trip["linked_request_ids"]:
        raise AssertionError("Trip missing primary or linked request id.")
    if not trip["trip_reference"].startswith("TRP-"):
        raise AssertionError("Converted trip reference was not generated.")

    detail = get(f"/api/agencies/{agency_id}/trips/{trip['id']}", OWNER_HEADERS)
    if len(detail["passengers"]) != 1:
        raise AssertionError("Normalized request passengers were not copied.")
    if len(detail["segments"]) != 2:
        raise AssertionError("Normalized request segments were not copied.")
    if len(detail["services"]) != 1:
        raise AssertionError("Normalized request service scopes were not copied.")
    counts = (len(detail["passengers"]), len(detail["segments"]), len(detail["services"]))

    duplicate = post(f"/api/agencies/{agency_id}/trips/from-request/{request_id}", {}, OWNER_HEADERS, 201)["trip"]
    duplicate_detail = get(f"/api/agencies/{agency_id}/trips/{duplicate['id']}", OWNER_HEADERS)
    duplicate_counts = (len(duplicate_detail["passengers"]), len(duplicate_detail["segments"]), len(duplicate_detail["services"]))
    if duplicate["id"] != trip["id"] or duplicate_counts != counts:
        raise AssertionError("Idempotent create-from-request duplicated trip child records.")

    request_after = get(f"/api/agencies/{agency_id}/requests/{request_id}", OWNER_HEADERS)
    if request_after["request"]["id"] != request_before["request"]["id"] or not request_after.get("linked_trip"):
        raise AssertionError("Request was mutated destructively or did not expose linked trip.")
    if len(request_after["segments"]) != len(request_before["segments"]):
        raise AssertionError("Request segments changed during trip conversion.")

    second = create_request(agency_id, client_id, f"Phase 35 additional request {int(time.time())}", "b")
    second_id = second["request"]["id"]
    linked = post(f"/api/agencies/{agency_id}/trips/{trip['id']}/link-request/{second_id}", {}, OWNER_HEADERS)["trip"]
    if second_id not in linked["linked_request_ids"]:
        raise AssertionError("Additional request was not linked.")
    unlinked = post(f"/api/agencies/{agency_id}/trips/{trip['id']}/unlink-request/{second_id}", {}, OWNER_HEADERS)["trip"]
    if second_id in unlinked["linked_request_ids"]:
        raise AssertionError("Request unlink did not remove linked request id.")

    rebuilt = post(f"/api/agencies/{agency_id}/trips/{trip['id']}/rebuild-summary", {}, OWNER_HEADERS)["trip"]
    if rebuilt["passenger_count"] < 1 or rebuilt["segment_count"] < 2 or rebuilt["service_count"] < 1:
        raise AssertionError("Rebuild summary did not persist counts.")
    updated = put(f"/api/agencies/{agency_id}/trips/{trip['id']}", {"trip_status": "quoted", "trip_type": "complex", "internal_notes": "Smoke update"}, OWNER_HEADERS)["trip"]
    if updated["trip_status"] != "quoted" or updated["trip_type"] != "complex":
        raise AssertionError("Trip update did not persist editable fields.")
    archived = post(f"/api/agencies/{agency_id}/trips/{trip['id']}/archive", {}, OWNER_HEADERS)["trip"]
    if archived["trip_status"] != "archived" or not archived.get("archived_at"):
        raise AssertionError("Trip archive did not persist archive state.")

    readiness = get("/api/readiness")
    dossier = readiness.get("trip_dossiers") or {}
    for key in [
        "trip_dossier_foundation_enabled",
        "request_to_trip_conversion_enabled",
        "trip_linking_enabled",
        "trip_passenger_copy_enabled",
        "trip_segment_copy_enabled",
        "trip_service_scope_copy_enabled",
    ]:
        if dossier.get(key) is not True:
            raise AssertionError(f"Readiness missing trip flag: {key}")
    for key in ["trip_dossier_count", "linked_trip_request_count", "trip_passenger_count", "trip_segment_count", "trip_service_item_count"]:
        if key not in dossier:
            raise AssertionError(f"Readiness missing trip count: {key}")

    get(f"/api/agencies/{agency_id}/trips", PORTAL_HEADERS, 403)
    print("Trip dossier foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Trip dossier foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
