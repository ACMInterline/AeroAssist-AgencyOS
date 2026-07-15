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


def mobility_details(code: str = "WCHS", override: str | None = None, override_reason: str | None = None) -> dict:
    assessments = {
        "WCHR": {
            "can_walk_short_distances": "yes",
            "can_climb_aircraft_stairs": "yes",
            "needs_wheelchair_for_distance": "yes",
        },
        "WCHS": {
            "can_walk_short_distances": "yes",
            "can_climb_aircraft_stairs": "no",
            "needs_wheelchair_to_aircraft_door": "yes",
        },
        "WCHC": {
            "can_walk_short_distances": "no",
            "can_transfer_independently_to_aircraft_seat": "no",
            "needs_assistance_into_aircraft_seat": "yes",
            "needs_aisle_chair": "yes",
        },
    }
    reasons = {
        "WCHR": "Passenger can walk/use stairs but needs wheelchair for airport distance.",
        "WCHS": "Passenger can walk short distances but cannot use stairs.",
        "WCHC": "Passenger cannot walk or needs seat/aisle-chair assistance.",
    }
    confirmed = override or code
    details = {
        "assessment_version": "v2_assessment_driven",
        "passenger_context_tags": ["prm", "temporary_injury"],
        "passenger_context_notes": "Operational context only.",
        "functional_assessment": assessments[code],
        "suggested_ssr_code": code,
        "suggested_ssr_reason": reasons[code],
        "recommendation_confidence": "high",
        "confirmed_ssr_code": confirmed,
        "own_mobility_device": "electric_wheelchair_powerchair",
        "own_device_details": {
            "device_type": "electric_wheelchair_powerchair",
            "brand_model": "Example Powerchair",
            "weight_kg": "34",
            "length_cm": "100",
            "width_cm": "62",
            "height_cm": "88",
            "foldable_or_collapsible": "no",
        },
        "battery_details": {
            "battery_type": "lithium_ion",
            "battery_removable": "yes",
            "battery_watt_hours": "280",
            "battery_documentation_available": "yes",
        },
    }
    if override_reason:
        details["override_reason"] = override_reason
    return details


def builder_payload(email: str, mobility_code: str = "WCHS", override: str | None = None, override_reason: str | None = None) -> dict:
    return {
        "client": {
            "name": "Phase 27 Builder Client",
            "email": email,
            "phone": "+421900000027",
            "organization": "Builder Smoke Ltd",
            "notes": "Inline client created by smoke.",
        },
        "passengers": [
            {
                "first_name": "Builder",
                "last_name": "Traveler",
                "date_of_birth": "1985-05-05",
                "passenger_type": "adult",
                "mobility_notes": "Needs wheelchair assistance.",
            },
            {
                "display_name": "Minor Traveler",
                "passenger_type": "unaccompanied_minor",
                "notes": "UM support required.",
            },
        ],
        "trip_type": "round_trip",
        "origin": "Bratislava",
        "destination": "London",
        "departure_date": "2026-09-10",
        "return_date": "2026-09-20",
        "route_notes": "Prefer direct routing if available.",
        "segments": [
            {
                "sequence": 1,
                "origin_text": "BTS",
                "destination_text": "LHR",
                "departure_date": "2026-09-10",
                "departure_time_window": "morning",
                "marketing_airline": "BA",
                "operating_airline": "BA",
                "flight_number": "BA001",
                "cabin_preference": "economy",
            }
        ],
        "services": [
            {
                "category": "mobility_assistance",
                "details": mobility_details(mobility_code, override, override_reason),
                "applies_to_all_passengers": True,
                "applies_to_all_segments": True,
                "notes": "Coordinate assistance manually.",
            },
            {
                "category": "unaccompanied_minor",
                "details": {
                    "child_age": "11",
                    "escort_needed": True,
                    "handover_contact": "Parent A",
                    "pickup_contact": "Parent B",
                    "airline_um_service_required": True,
                },
                "applies_to_all_passengers": True,
                "applies_to_all_segments": True,
            },
        ],
        "status": "new",
        "priority": "high",
        "source": "staff_created",
        "internal_notes": "Builder smoke internal notes.",
        "client_visible_notes": "Request received for staff review.",
    }


def public_intake_payload(email: str) -> dict:
    return {
        "contact": {"name": "Builder Intake Client", "email": email, "privacy_policy_accepted": True, "data_processing_consent": True},
        "travel": {"origin": "Vienna", "destination": "Paris", "departure_date": "2026-10-01", "passenger_count": 2, "itinerary_notes": "Need airport support."},
        "services": {"selected_service_categories": ["airport assistance"], "booking_or_planning": True},
        "request_details": "Airport assistance and planning.",
    }


def main() -> int:
    health = get("/api/health")
    if health.get("phase") != "phase_56_3_journey_comparison_client_presentation_foundation":
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")
    post("/api/reference/seed", {}, OWNER_HEADERS)
    agencies = get("/api/agencies", OWNER_HEADERS)["items"]
    if not agencies:
        raise AssertionError("No agency available for builder smoke.")
    agency_id = agencies[0]["id"]
    post(f"/api/agencies/{agency_id}/requests/builder", builder_payload("unauth@example.com"), {"Authorization": "Bearer definitely-not-valid"}, 401)

    post(
        f"/api/agencies/{agency_id}/requests/builder",
        builder_payload(f"phase27.override.{int(time.time())}@example.com", "WCHR", "WCHC"),
        OWNER_HEADERS,
        400,
    )

    created = post(f"/api/agencies/{agency_id}/requests/builder", builder_payload(f"phase27.{int(time.time())}@example.com"), OWNER_HEADERS, 201)
    request_id = created["request"]["id"]
    if created["request"]["passenger_count"] != 2:
        raise AssertionError("Passenger count did not match builder passengers.")
    if created["request"]["service_count"] != 2:
        raise AssertionError("Service count did not match selected services.")
    detail = get(f"/api/agencies/{agency_id}/requests/{request_id}", OWNER_HEADERS)
    if len(detail["passengers"]) != 2 or len(detail["segments"]) != 1 or len(detail["services"]) != 2:
        raise AssertionError("Request detail did not preserve structured builder records.")
    if detail["request"].get("trip_type") != "round_trip":
        raise AssertionError("Trip type was not stored.")
    if not detail["services"][0].get("detail_payload"):
        raise AssertionError("Service detail payload was not stored.")
    mobility_payload = detail["services"][0]["detail_payload"]
    if mobility_payload.get("suggested_ssr_code") != "WCHS" or mobility_payload.get("confirmed_ssr_code") != "WCHS":
        raise AssertionError("Assessment-driven WCHS recommendation payload was not stored.")
    if mobility_payload.get("own_mobility_device") != "electric_wheelchair_powerchair":
        raise AssertionError("Own mobility device payload was not stored.")
    if mobility_payload.get("battery_details", {}).get("battery_type") != "lithium_ion":
        raise AssertionError("Electric mobility device battery details were not stored.")

    for code in ["WCHR", "WCHC"]:
        result = post(f"/api/agencies/{agency_id}/requests/builder", builder_payload(f"phase27.{code.lower()}.{int(time.time())}@example.com", code), OWNER_HEADERS, 201)
        detail_for_code = get(f"/api/agencies/{agency_id}/requests/{result['request']['id']}", OWNER_HEADERS)
        stored = detail_for_code["services"][0]["detail_payload"]
        if stored.get("suggested_ssr_code") != code or stored.get("confirmed_ssr_code") != code:
            raise AssertionError(f"{code} assessment recommendation was not preserved.")
    if not detail["services"][0].get("passenger_ids") or not detail["services"][0].get("segment_ids"):
        raise AssertionError("Service passenger/segment relationships were not stored.")

    intake = post("/api/public/request-intakes", public_intake_payload(f"phase27.intake.{int(time.time())}@example.com"), expect=201)
    request("PATCH", f"/api/request-intakes/{intake['intake']['id']}/triage", {"agency_id": agency_id}, OWNER_HEADERS)
    converted = post(f"/api/request-intakes/{intake['intake']['id']}/convert", {}, OWNER_HEADERS)
    converted_detail = get(f"/api/agencies/{converted['request']['agency_id']}/requests/{converted['request']['id']}", OWNER_HEADERS)
    if converted_detail["request"].get("source_intake_id") != intake["intake"]["id"]:
        raise AssertionError("Converted request did not link to source intake.")
    if converted_detail["request"].get("passenger_count") < 1 or not converted_detail["services"]:
        raise AssertionError("Intake conversion did not create structured passenger/service records.")
    converted_mobility = next((service for service in converted_detail["services"] if "mobility" in service.get("service_name", "").lower()), None)
    if converted_mobility and converted_mobility["detail_payload"].get("confirmed_ssr_code") != "manual_review":
        raise AssertionError("Intake mobility conversion did not create manual-review assessment payload.")

    print("Operational request builder smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Operational request builder smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
