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
    req = urllib.request.Request(f"{BASE_URL}{path}", method=method, data=data, headers={**(headers or {}), "Content-Type": "application/json"})
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


def assert_openapi_path(paths: dict, path: str, method: str) -> None:
    if method.lower() not in paths.get(path, {}):
        raise AssertionError(f"OpenAPI missing {method.upper()} {path}")


def main() -> int:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")

    openapi = get("/openapi.json")
    paths = openapi.get("paths") or {}
    for path, method in [
        ("/api/agencies/{agency_id}/booking-workspaces/manual", "post"),
        ("/api/agencies/{agency_id}/tickets/manual", "post"),
        ("/api/agencies/{agency_id}/emds/manual", "post"),
        ("/api/agencies/{agency_id}/booking-import-drafts", "get"),
        ("/api/agencies/{agency_id}/booking-import-drafts", "post"),
        ("/api/agencies/{agency_id}/booking-import-drafts/{draft_id}", "get"),
        ("/api/agencies/{agency_id}/booking-import-drafts/{draft_id}/parse", "post"),
        ("/api/agencies/{agency_id}/booking-import-drafts/{draft_id}/import-as-booking", "post"),
        ("/api/agencies/{agency_id}/trips/{trip_id}/change-operations", "get"),
        ("/api/agencies/{agency_id}/trips/{trip_id}/change-operations", "post"),
        ("/api/agencies/{agency_id}/trip-change-operations/{operation_id}/create-change-booking", "post"),
        ("/api/agencies/{agency_id}/ticket-exchange-operations", "post"),
        ("/api/agencies/{agency_id}/ticket-exchange-operations/{operation_id}/mirror-new-ticket", "post"),
        ("/api/agencies/{agency_id}/emd-exchange-operations", "post"),
        ("/api/agencies/{agency_id}/emd-exchange-operations/{operation_id}/mirror-new-emd", "post"),
    ]:
        assert_openapi_path(paths, path, method)
    if any(path.startswith("/api/agent") or path.startswith("/api/admin") for path in paths):
        raise AssertionError("/agent or /admin API roots were introduced.")

    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError("Readiness did not expose the phase 36.4.6 label.")
    booking = readiness.get("booking_foundation") or {}
    ticket_emd = readiness.get("ticket_emd_foundation") or {}
    change = readiness.get("change_exchange_foundation") or {}
    blueprint = readiness.get("blueprint_sync") or {}
    for key in [
        "manual_booking_workspace_enabled",
        "structured_manual_booking_form_enabled",
        "structured_import_preview_enabled",
        "raw_json_advanced_fallback_enabled",
        "standalone_booking_record_enabled",
        "booking_import_draft_enabled",
        "booking_import_parser_stub_enabled",
        "existing_trip_change_booking_enabled",
        "provider_execution_disabled",
    ]:
        if booking.get(key) is not True:
            raise AssertionError(f"Readiness missing booking flag: {key}")
    for key in [
        "manual_ticket_creation_enabled",
        "structured_manual_ticket_form_enabled",
        "standalone_ticket_creation_enabled",
        "manual_emd_creation_enabled",
        "structured_manual_emd_form_enabled",
        "raw_json_advanced_fallback_enabled",
        "standalone_emd_creation_enabled",
        "ticket_emd_import_association_ready",
        "ticket_exchange_operation_foundation_enabled",
        "emd_exchange_operation_foundation_enabled",
        "exchange_reissue_mirror_enabled",
        "provider_ticketing_disabled",
        "provider_emd_issuance_disabled",
    ]:
        if ticket_emd.get(key) is not True:
            raise AssertionError(f"Readiness missing ticket/EMD flag: {key}")
    for key in [
        "trip_change_operation_foundation_enabled",
        "ticket_exchange_operation_foundation_enabled",
        "emd_exchange_operation_foundation_enabled",
        "existing_trip_change_booking_enabled",
        "request_offer_change_linkage_ready",
        "provider_exchange_execution_disabled",
        "provider_refund_execution_disabled",
        "provider_void_execution_disabled",
    ]:
        if change.get(key) is not True:
            raise AssertionError(f"Readiness missing change/exchange flag: {key}")
    for key in [
        "standalone_booking_ticket_emd_workflow_recognized",
        "gds_confirmation_import_foundation_enabled",
        "existing_trip_change_exchange_workflow_recognized",
    ]:
        if blueprint.get(key) is not True:
            raise AssertionError(f"Blueprint sync missing workflow flag: {key}")

    post("/api/reference/seed", {}, OWNER_HEADERS)
    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    trip = post(
        f"/api/agencies/{agency_id}/trips",
        {"trip_title": f"Phase 36.4.6 servicing trip {int(time.time())}", "trip_status": "draft", "trip_type": "one_way"},
        OWNER_HEADERS,
        201,
    )["trip"]
    segments = [
        {
            "id": "seg-1",
            "sequence": 1,
            "coupon_number": 1,
            "marketing_airline_code": "LH",
            "operating_airline_code": "LH",
            "flight_number": "1703",
            "origin_airport_code": "SOF",
            "destination_airport_code": "FRA",
            "departure_date": "2026-12-13",
            "departure_datetime": "2026-12-13T08:30:00",
            "cabin": "economy",
            "booking_class": "Y",
            "rbd": "Y",
            "status_code": "HK",
        }
    ]
    passengers = [{"id": "pax-1", "first_name": "Manual", "last_name": "Traveler", "display_name": "Manual Traveler"}]
    pricing = {"summary": {"currency": "EUR", "base_fare_amount": 100, "taxes_amount": 25, "fees_amount": 0, "total_amount": 125}}
    services = {
        "items": [
            {
                "service_category": "mobility assistance",
                "service_label": "Wheelchair assistance",
                "passenger_reference": "pax-1",
                "segment_reference": "seg-1",
                "quantity": 1,
                "service_catalogue_id": "manual-wchr",
            }
        ]
    }

    manual_booking = post(
        f"/api/agencies/{agency_id}/booking-workspaces/manual",
        {
            "trip_id": trip["id"],
            "title": "Standalone manual booking smoke",
            "provider_target": "manual",
            "pnr_locator": "MNL123",
            "passengers_json": passengers,
            "segments_json": segments,
            "pricing_json": pricing,
            "ssr_json": [{"ssr_code": "WCHR", "airline_code": "LH", "passenger_reference": "pax-1", "segment_reference": "seg-1", "free_text": "WHEELCHAIR"}],
            "osi_json": [{"airline_code": "LH", "text": "VIP PASSENGER", "passenger_reference": "pax-1"}],
            "services_json": services,
            "create_draft_record": True,
            "source_context": "standalone_manual",
        },
        OWNER_HEADERS,
        201,
    )
    workspace = manual_booking["booking_workspace"]
    record = manual_booking["booking_record"]
    if workspace.get("booking_readiness_package_id") is not None or workspace.get("source_context") != "standalone_manual":
        raise AssertionError("Manual booking workspace did not preserve standalone context.")
    if not record or record.get("pnr_locator") != "MNL123":
        raise AssertionError("Manual booking did not create a draft booking record.")

    ticket = post(
        f"/api/agencies/{agency_id}/tickets/manual",
        {
            "booking_record_id": record["id"],
            "trip_id": trip["id"],
            "passenger_id": "pax-1",
            "passenger_snapshot_json": passengers[0],
            "ticket_number": "2201111111111",
            "validating_carrier": "LH",
            "segments_snapshot_json": segments,
            "pricing_snapshot_json": pricing,
            "base_fare_amount": 100,
            "taxes_amount": 25,
            "total_amount": 125,
            "currency": "EUR",
            "source_context": "standalone_manual",
        },
        OWNER_HEADERS,
        201,
    )["ticket"]
    standalone_ticket = post(
        f"/api/agencies/{agency_id}/tickets/manual",
        {
            "trip_id": trip["id"],
            "passenger_id": "standalone-pax",
            "ticket_number": "2202222222222",
            "segments_snapshot_json": segments,
            "source_context": "standalone_manual",
        },
        OWNER_HEADERS,
        201,
    )["ticket"]
    if standalone_ticket.get("booking_record_id"):
        raise AssertionError("Standalone manual ticket unexpectedly required a booking record.")

    emd = post(
        f"/api/agencies/{agency_id}/emds/manual",
        {
            "booking_record_id": record["id"],
            "ticket_record_id": ticket["id"],
            "trip_id": trip["id"],
            "passenger_id": "pax-1",
            "emd_number": "2203333333333",
            "service_key": "WCHR",
            "service_catalogue_id": "manual-wchr",
            "service_label": "Wheelchair assistance",
            "service_category": "mobility assistance",
            "linked_service_snapshot_json": {
                "service_key": "WCHR",
                "service_label": "Wheelchair assistance",
                "service_category": "mobility assistance",
                "emd_coupons": [
                    {
                        "coupon_number": 1,
                        "rfic": "E",
                        "rfisc": "0B5",
                        "service_description": "Wheelchair assistance",
                        "status": "draft",
                        "related_segment_reference": "seg-1",
                    }
                ],
            },
            "linked_segment_ids": ["seg-1"],
            "amount": 0,
            "taxes_amount": 0,
            "total_amount": 0,
            "currency": "EUR",
            "source_context": "standalone_manual",
        },
        OWNER_HEADERS,
        201,
    )["emd"]
    standalone_emd = post(
        f"/api/agencies/{agency_id}/emds/manual",
        {
            "trip_id": trip["id"],
            "passenger_id": "standalone-pax",
            "emd_number": "2204444444444",
            "service_key": "BAG",
            "service_label": "Bag service",
            "source_context": "standalone_manual",
        },
        OWNER_HEADERS,
        201,
    )["emd"]
    if standalone_emd.get("booking_record_id"):
        raise AssertionError("Standalone manual EMD unexpectedly required a booking record.")

    raw_import = "\n".join(
        [
            "PNR ABC123",
            "1.SMITH/JOHN",
            "LH1703 Y 13DEC SOFFRA",
            "SSR WCHR LH HK1 SOFFRA",
            "OSI LH VIP PASSENGER",
            "TKT 2201234567890",
            "EMD 2200987654321",
        ]
    )
    draft = post(
        f"/api/agencies/{agency_id}/booking-import-drafts",
        {"source_type": "cryptic_gds", "raw_text": raw_import, "linked_trip_id": trip["id"], "import_context": "new_booking"},
        OWNER_HEADERS,
        201,
    )["draft"]
    parsed = post(f"/api/agencies/{agency_id}/booking-import-drafts/{draft['id']}/parse", {}, OWNER_HEADERS)["draft"]
    if not parsed.get("parsed_json", {}).get("record_locator"):
        raise AssertionError("Booking import parser did not extract a locator.")
    imported = post(
        f"/api/agencies/{agency_id}/booking-import-drafts/{draft['id']}/import-as-booking",
        {"create_draft_record": True, "create_ticket_mirrors": True, "create_emd_mirrors": True},
        OWNER_HEADERS,
    )
    if not imported.get("booking_workspace") or not imported.get("booking_record"):
        raise AssertionError("Import draft did not create a booking workspace and record.")
    if not imported.get("ticket_record_ids") or not imported.get("emd_record_ids"):
        raise AssertionError("Import draft did not create confirmed ticket/EMD mirrors from parsed numbers.")

    change_op = post(
        f"/api/agencies/{agency_id}/trips/{trip['id']}/change-operations",
        {
            "operation_type": "itinerary_change",
            "reason": "Smoke itinerary change",
            "source_booking_workspace_id": workspace["id"],
            "source_booking_record_id": record["id"],
            "change_summary_json": {
                "summary_text": "Structured smoke change",
                "proposed_change_notes": "Move outbound flight later",
                "internal_notes": "No provider execution",
            },
        },
        OWNER_HEADERS,
        201,
    )["operation"]
    change_booking = post(
        f"/api/agencies/{agency_id}/trip-change-operations/{change_op['id']}/create-change-booking",
        {"source_context": "existing_trip_change", "title": "Revised booking mirror", "create_draft_record": True, "segments_json": segments},
        OWNER_HEADERS,
        201,
    )
    if change_booking["operation"].get("status") != "mirrored" or change_booking["booking_workspace"].get("source_context") != "existing_trip_change":
        raise AssertionError("Trip change operation did not create a revised booking mirror.")

    ticket_exchange = post(
        f"/api/agencies/{agency_id}/ticket-exchange-operations",
        {"trip_id": trip["id"], "booking_record_id": record["id"], "original_ticket_record_id": ticket["id"], "operation_type": "exchange", "reason": "Smoke exchange"},
        OWNER_HEADERS,
        201,
    )["operation"]
    mirrored_ticket = post(
        f"/api/agencies/{agency_id}/ticket-exchange-operations/{ticket_exchange['id']}/mirror-new-ticket",
        {"ticket_number": "2205555555555", "segments_snapshot_json": segments, "source_context": "exchange_reissue"},
        OWNER_HEADERS,
        201,
    )
    if mirrored_ticket["operation"].get("status") != "mirrored" or mirrored_ticket["ticket"].get("original_ticket_record_id") != ticket["id"]:
        raise AssertionError("Ticket exchange did not create a linked new ticket mirror.")

    emd_exchange = post(
        f"/api/agencies/{agency_id}/emd-exchange-operations",
        {"trip_id": trip["id"], "booking_record_id": record["id"], "original_emd_record_id": emd["id"], "operation_type": "exchange", "reason": "Smoke EMD exchange"},
        OWNER_HEADERS,
        201,
    )["operation"]
    mirrored_emd = post(
        f"/api/agencies/{agency_id}/emd-exchange-operations/{emd_exchange['id']}/mirror-new-emd",
        {"emd_number": "2206666666666", "service_key": "WCHR", "service_label": "Wheelchair assistance", "source_context": "exchange_reissue"},
        OWNER_HEADERS,
        201,
    )
    if mirrored_emd["operation"].get("status") != "mirrored" or mirrored_emd["emd"].get("original_emd_record_id") != emd["id"]:
        raise AssertionError("EMD exchange did not create a linked new EMD mirror.")

    updated_readiness = get("/api/readiness")
    counts = updated_readiness.get("change_exchange_foundation") or {}
    for key in ["booking_import_draft_count", "trip_change_operation_count", "ticket_exchange_operation_count", "emd_exchange_operation_count"]:
        if key not in counts:
            raise AssertionError(f"Readiness missing count: {key}")

    print("Standalone booking, import, and change/exchange foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Standalone/change/exchange foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
