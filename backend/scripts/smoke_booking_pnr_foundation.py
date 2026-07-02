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
EXPECTED_PHASE = "phase_37_6_offer_decision_export_preview_foundation"


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


def put(
    path: str,
    body: dict | None = None,
    headers: dict | None = None,
    expect: int | None = None,
) -> dict:
    return request("PUT", path, body or {}, headers, expect)[1]


def assert_openapi_path(paths: dict, path: str, method: str) -> None:
    if method.lower() not in paths.get(path, {}):
        raise AssertionError(f"OpenAPI missing {method.upper()} {path}")


def builder_payload(email: str) -> dict:
    return {
        "client": {
            "name": "Phase 36.3 Booking Client",
            "email": email,
            "phone": "+421900000363",
        },
        "passengers": [
            {
                "request_passenger_key": "pax-1",
                "first_name": "Booking",
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
                "departure_date": "2026-12-13",
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
        "title": "Phase 36.3 booking workspace smoke",
        "status": "new",
        "priority": "normal",
        "source": "staff_created",
    }


def create_priced_option(agency_id: str, workspace_id: str) -> dict:
    option = post(
        f"/api/agencies/{agency_id}/offer-workspaces/{workspace_id}/options",
        {
            "label": "Booking LH economy",
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
            "departure_at": "2026-12-13T06:00:00Z",
            "arrival_at": "2026-12-13T07:25:00Z",
            "aircraft_type": "A320",
            "cabin_class": "economy",
            "booking_class": "Y",
            "fare_basis": "YBOOKING",
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


def flatten_service_snapshot(snapshot: dict) -> list[dict]:
    items: list[dict] = []
    for value in (snapshot or {}).values():
        if isinstance(value, list):
            items.extend([item for item in value if isinstance(item, dict)])
    return items


def main() -> int:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")

    openapi = get("/openapi.json")
    paths = openapi.get("paths") or {}
    for path, method in [
        ("/api/agencies/{agency_id}/booking-workspaces", "get"),
        ("/api/agencies/{agency_id}/booking-readiness-packages", "get"),
        ("/api/agencies/{agency_id}/booking-workspaces/from-readiness", "post"),
        ("/api/agencies/{agency_id}/booking-workspaces/{booking_workspace_id}", "get"),
        ("/api/agencies/{agency_id}/booking-workspaces/{booking_workspace_id}/status", "post"),
        ("/api/agencies/{agency_id}/booking-workspaces/{booking_workspace_id}/rebuild-record", "post"),
        ("/api/agencies/{agency_id}/booking-workspaces/{booking_workspace_id}/cancel", "post"),
        ("/api/agencies/{agency_id}/booking-records/{booking_record_id}", "put"),
    ]:
        assert_openapi_path(paths, path, method)

    readiness = get("/api/readiness")
    booking_foundation = readiness.get("booking_foundation") or {}
    for key in [
        "booking_workspace_foundation_enabled",
        "booking_from_readiness_enabled",
        "booking_record_mirror_enabled",
        "booking_timeline_enabled",
        "manual_pnr_mirror_enabled",
        "provider_execution_disabled",
        "service_catalogue_booking_snapshot_enabled",
        "trip_booking_workspace_link_enabled",
        "agency_booking_workspace_ui_enabled",
    ]:
        if booking_foundation.get(key) is not True:
            raise AssertionError(f"Readiness missing booking foundation flag: {key}")
    for key in [
        "booking_workspace_count",
        "booking_record_count",
        "booking_timeline_event_count",
        "booking_workspace_ready_count",
        "booking_workspace_blocked_count",
        "booking_workspace_cancelled_count",
    ]:
        if key not in booking_foundation:
            raise AssertionError(f"Readiness missing booking foundation count: {key}")
    if booking_foundation.get("readiness_required") is not False:
        raise AssertionError("Booking foundation should not be deployment-readiness required.")

    post("/api/reference/seed", {}, OWNER_HEADERS)
    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    created_request = post(
        f"/api/agencies/{agency_id}/requests/builder",
        builder_payload(f"phase363.{int(time.time())}@example.com"),
        OWNER_HEADERS,
        201,
    )
    request_id = created_request["request"]["id"]
    offer_workspace = post(
        f"/api/agencies/{agency_id}/requests/{request_id}/offer-workspace",
        {},
        OWNER_HEADERS,
        201,
    )["workspace"]
    option = create_priced_option(agency_id, offer_workspace["id"])
    accepted = post(
        f"/api/agencies/{agency_id}/offer-workspaces/{offer_workspace['id']}/options/{option['id']}/accept",
        {"acceptance_source": "internal", "provider_target": "manual"},
        OWNER_HEADERS,
        201,
    )
    readiness_package = accepted.get("booking_readiness") or {}
    if readiness_package.get("status") not in {"ready", "draft", "blocked"}:
        raise AssertionError(f"Unexpected readiness status: {readiness_package}")
    service_items = flatten_service_snapshot(readiness_package.get("services_snapshot_json") or {})
    if not service_items:
        raise AssertionError("Booking readiness did not preserve service snapshot items.")
    if not any(item.get("service_catalogue_snapshot_json") or item.get("service_catalogue_id") or item.get("service_code") for item in service_items):
        raise AssertionError("Service snapshot did not preserve catalogue or service mapping fields.")

    eligible_before = get(f"/api/agencies/{agency_id}/booking-readiness-packages", OWNER_HEADERS)
    before_item = next((item for item in eligible_before.get("items", []) if item["id"] == readiness_package["id"]), None)
    if before_item is None:
        raise AssertionError("Eligible booking readiness list did not include the accepted package.")
    if before_item.get("booking_workspace_already_exists") is not False:
        raise AssertionError("Eligible booking readiness package was incorrectly marked as already created.")
    if not before_item.get("trip_summary") or not before_item.get("accepted_offer_summary") or not before_item.get("workspace_summary"):
        raise AssertionError("Eligible booking readiness package did not include required summaries.")

    created = post(
        f"/api/agencies/{agency_id}/booking-workspaces/from-readiness",
        {
            "booking_readiness_package_id": readiness_package["id"],
            "create_draft_record": True,
        },
        OWNER_HEADERS,
        201,
    )
    workspace = created.get("booking_workspace") or {}
    record = created.get("booking_record") or {}
    if not workspace.get("id") or not workspace.get("workspace_number", "").startswith("BKG-"):
        raise AssertionError(f"Booking workspace was not created with a workspace number: {workspace}")
    if workspace.get("booking_readiness_package_id") != readiness_package["id"]:
        raise AssertionError("Booking workspace did not link to readiness package.")
    if workspace.get("status") not in {"ready_to_book", "draft", "blocked"}:
        raise AssertionError(f"Unexpected booking workspace status: {workspace.get('status')}")
    if not record.get("id") or record.get("booking_workspace_id") != workspace["id"]:
        raise AssertionError("Draft booking record mirror was not created and linked.")
    if record.get("provider_status") != "draft" or record.get("booking_status") != "draft":
        raise AssertionError(f"Draft booking record has unexpected status: {record}")
    mirror = record.get("internal_pnr_mirror_json") or {}
    if mirror.get("provider_execution_disabled") is not True:
        raise AssertionError("Internal PNR mirror did not explicitly disable provider execution.")
    if workspace.get("services_snapshot_json") != readiness_package.get("services_snapshot_json"):
        raise AssertionError("Workspace services snapshot drifted from readiness package.")
    if record.get("services_json") != readiness_package.get("services_snapshot_json"):
        raise AssertionError("Booking record services snapshot drifted from readiness package.")

    duplicate = post(
        f"/api/agencies/{agency_id}/booking-workspaces/from-readiness",
        {"booking_readiness_package_id": readiness_package["id"]},
        OWNER_HEADERS,
        201,
    )
    if duplicate.get("booking_workspace", {}).get("id") != workspace["id"]:
        raise AssertionError("Duplicate create did not reuse the active booking workspace.")
    if not any(item.get("code") == "existing_booking_workspace_reused" for item in duplicate.get("warnings", [])):
        raise AssertionError("Duplicate create did not return reuse warning.")

    eligible_after = get(f"/api/agencies/{agency_id}/booking-readiness-packages", OWNER_HEADERS)
    after_item = next((item for item in eligible_after.get("items", []) if item["id"] == readiness_package["id"]), None)
    if after_item is None or after_item.get("booking_workspace_id") != workspace["id"]:
        raise AssertionError("Eligible booking readiness list did not expose the existing booking workspace.")
    if after_item.get("booking_workspace_already_exists") is not True or after_item.get("can_create_booking_workspace") is not False:
        raise AssertionError("Eligible booking readiness list did not mark the package as open-only after creation.")

    listed = get(
        f"/api/agencies/{agency_id}/booking-workspaces?trip_id={accepted['acceptance']['trip_id']}",
        OWNER_HEADERS,
    )
    if not any(item["id"] == workspace["id"] for item in listed.get("items", [])):
        raise AssertionError("Booking workspace list did not include created workspace.")

    detail = get(f"/api/agencies/{agency_id}/booking-workspaces/{workspace['id']}", OWNER_HEADERS)
    if not detail.get("timeline"):
        raise AssertionError("Booking workspace detail did not include timeline events.")
    if detail.get("readiness_summary", {}).get("id") != readiness_package["id"]:
        raise AssertionError("Booking workspace detail did not include readiness summary.")

    moved = post(
        f"/api/agencies/{agency_id}/booking-workspaces/{workspace['id']}/status",
        {"status": "booking_in_progress"},
        OWNER_HEADERS,
    )
    if moved.get("booking_workspace", {}).get("status") != "booking_in_progress":
        raise AssertionError("Booking workspace status update failed.")

    updated = put(
        f"/api/agencies/{agency_id}/booking-records/{record['id']}",
        {
            "pnr_locator": "ABC123",
            "provider_status": "held",
            "booking_status": "draft",
            "internal_notes": "Manual smoke PNR mirror.",
        },
        OWNER_HEADERS,
    )
    updated_record = updated.get("booking_record") or {}
    if updated_record.get("pnr_locator") != "ABC123" or updated_record.get("provider_status") != "held":
        raise AssertionError("Manual PNR record update failed.")

    rebuilt = post(
        f"/api/agencies/{agency_id}/booking-workspaces/{workspace['id']}/rebuild-record",
        {},
        OWNER_HEADERS,
    )
    if rebuilt.get("booking_record", {}).get("id") != record["id"]:
        raise AssertionError("Booking record rebuild did not preserve the draft record.")
    if rebuilt.get("booking_record", {}).get("internal_pnr_mirror_json", {}).get("provider_execution_disabled") is not True:
        raise AssertionError("Rebuilt booking record mirror did not keep provider execution disabled.")

    cancelled = post(
        f"/api/agencies/{agency_id}/booking-workspaces/{workspace['id']}/cancel",
        {},
        OWNER_HEADERS,
    )
    if cancelled.get("booking_workspace", {}).get("status") != "cancelled":
        raise AssertionError("Booking workspace cancel did not mark workspace cancelled.")
    if cancelled.get("booking_record", {}).get("booking_status") != "cancelled":
        raise AssertionError("Booking workspace cancel did not mark draft record cancelled.")

    final_readiness = get("/api/readiness")
    final_booking = final_readiness.get("booking_foundation") or {}
    if final_booking.get("booking_workspace_count", 0) < 1 or final_booking.get("booking_record_count", 0) < 1:
        raise AssertionError("Readiness counts did not include booking workspace and record.")
    if final_booking.get("provider_execution_disabled") is not True:
        raise AssertionError("Provider execution flag changed unexpectedly.")

    print("Booking PNR foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Booking PNR foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
