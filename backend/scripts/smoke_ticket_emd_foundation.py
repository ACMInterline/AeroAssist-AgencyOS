#!/usr/bin/env python3
import sys
import time

from smoke_booking_pnr_foundation import (
    OWNER_HEADERS,
    builder_payload,
    create_priced_option,
    flatten_service_snapshot,
    get,
    post,
    put,
)


EXPECTED_PHASE = "phase_39_4_platform_agency_ux_consolidation"


def assert_openapi_path(paths: dict, path: str, method: str) -> None:
    if method.lower() not in paths.get(path, {}):
        raise AssertionError(f"OpenAPI missing {method.upper()} {path}")


def service_key(service: dict) -> str | None:
    snapshot = service.get("service_catalogue_snapshot_json") or {}
    return service.get("service_key") or service.get("service_code") or snapshot.get("service_key") or snapshot.get("service_code")


def create_booking_record() -> tuple[str, dict, dict, dict]:
    post("/api/reference/seed", {}, OWNER_HEADERS)
    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    created_request = post(
        f"/api/agencies/{agency_id}/requests/builder",
        builder_payload(f"phase364.{int(time.time())}@example.com"),
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
    readiness = accepted.get("booking_readiness") or {}
    booking = post(
        f"/api/agencies/{agency_id}/booking-workspaces/from-readiness",
        {"booking_readiness_package_id": readiness["id"], "create_draft_record": True},
        OWNER_HEADERS,
        201,
    )
    return agency_id, readiness, booking["booking_workspace"], booking["booking_record"]


def main() -> int:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")

    openapi = get("/openapi.json")
    paths = openapi.get("paths") or {}
    for path, method in [
        ("/api/agencies/{agency_id}/tickets", "get"),
        ("/api/agencies/{agency_id}/tickets/from-booking-record", "post"),
        ("/api/agencies/{agency_id}/tickets/{ticket_record_id}", "get"),
        ("/api/agencies/{agency_id}/tickets/{ticket_record_id}", "put"),
        ("/api/agencies/{agency_id}/emds", "get"),
        ("/api/agencies/{agency_id}/emds/from-booking-service", "post"),
        ("/api/agencies/{agency_id}/emds/{emd_record_id}", "get"),
        ("/api/agencies/{agency_id}/emds/{emd_record_id}", "put"),
        ("/api/agencies/{agency_id}/booking-records/{booking_record_id}/ticket-emd-readiness", "get"),
    ]:
        assert_openapi_path(paths, path, method)

    readiness = get("/api/readiness")
    ticket_emd = readiness.get("ticket_emd_foundation") or {}
    for flag in [
        "ticket_record_foundation_enabled",
        "ticket_coupon_foundation_enabled",
        "emd_record_foundation_enabled",
        "emd_coupon_foundation_enabled",
        "ticket_from_booking_enabled",
        "emd_from_booking_service_enabled",
        "ticket_emd_readiness_enabled",
        "manual_ticket_mirror_enabled",
        "manual_emd_mirror_enabled",
        "service_catalogue_emd_mapping_enabled",
        "provider_ticketing_disabled",
        "provider_emd_issuance_disabled",
        "agency_ticket_emd_ui_enabled",
    ]:
        if ticket_emd.get(flag) is not True:
            raise AssertionError(f"Readiness missing ticket/EMD flag: {flag}")
    for key in [
        "ticket_record_count",
        "ticket_coupon_count",
        "emd_record_count",
        "emd_coupon_count",
        "ticket_draft_count",
        "ticket_issued_count",
        "emd_draft_count",
        "emd_issued_count",
    ]:
        if key not in ticket_emd:
            raise AssertionError(f"Readiness missing ticket/EMD count: {key}")
    if ticket_emd.get("readiness_required") is not False:
        raise AssertionError("Ticket/EMD foundation should not be deployment-readiness required.")

    agency_id, booking_readiness, booking_workspace, booking_record = create_booking_record()
    services = flatten_service_snapshot(booking_readiness.get("services_snapshot_json") or {})
    selected_service = services[0] if services else {}
    selected_service_key = service_key(selected_service) or "WCHR"

    ticket_created = post(
        f"/api/agencies/{agency_id}/tickets/from-booking-record",
        {"booking_record_id": booking_record["id"], "create_coupons": True},
        OWNER_HEADERS,
        201,
    )
    ticket = ticket_created.get("ticket") or {}
    coupons = ticket_created.get("coupons") or []
    if not ticket.get("id") or ticket.get("booking_record_id") != booking_record["id"]:
        raise AssertionError("Ticket mirror was not created from booking record.")
    if ticket.get("issue_status") != "draft" or ticket.get("issuing_provider") != "manual":
        raise AssertionError(f"Ticket mirror has unexpected status/provider: {ticket}")
    if not coupons:
        raise AssertionError("Ticket coupons were not created.")
    if ticket_created.get("provider_execution_disabled") is not True:
        raise AssertionError("Ticket detail did not disable provider execution.")

    ticket_detail = get(f"/api/agencies/{agency_id}/tickets/{ticket['id']}", OWNER_HEADERS)
    if ticket_detail.get("booking_workspace_summary", {}).get("id") != booking_workspace["id"]:
        raise AssertionError("Ticket detail did not include booking workspace summary.")
    if not ticket_detail.get("timeline"):
        raise AssertionError("Ticket detail did not include timeline.")

    updated_ticket = put(
        f"/api/agencies/{agency_id}/tickets/{ticket['id']}",
        {
            "ticket_number": "2201234567890",
            "validating_carrier": "LH",
            "issue_status": "issued",
            "currency": "EUR",
            "base_fare_amount": 120,
            "taxes_amount": 30,
            "total_amount": 150,
            "internal_notes": "Manual ticket mirror smoke update.",
        },
        OWNER_HEADERS,
    )
    if updated_ticket.get("ticket", {}).get("ticket_number") != "2201234567890":
        raise AssertionError("Ticket manual update did not persist ticket number.")

    emd_created = post(
        f"/api/agencies/{agency_id}/emds/from-booking-service",
        {
            "booking_record_id": booking_record["id"],
            "service_key": selected_service_key,
            "ticket_record_id": ticket["id"],
            "create_coupons": True,
        },
        OWNER_HEADERS,
        201,
    )
    emd = emd_created.get("emd") or {}
    emd_coupons = emd_created.get("coupons") or []
    if not emd.get("id") or emd.get("booking_record_id") != booking_record["id"]:
        raise AssertionError("EMD mirror was not created from booking service.")
    if emd.get("issue_status") != "draft":
        raise AssertionError(f"EMD mirror has unexpected status: {emd}")
    if emd.get("service_key") != selected_service_key:
        raise AssertionError("EMD mirror did not preserve selected service key.")
    if not emd_coupons:
        raise AssertionError("EMD coupons were not created.")
    if emd_created.get("provider_execution_disabled") is not True:
        raise AssertionError("EMD detail did not disable provider execution.")

    emd_detail = get(f"/api/agencies/{agency_id}/emds/{emd['id']}", OWNER_HEADERS)
    if emd_detail.get("service_mapping", {}).get("service_key") != selected_service_key:
        raise AssertionError("EMD detail did not return service mapping.")
    if emd_detail.get("booking_record_summary", {}).get("id") != booking_record["id"]:
        raise AssertionError("EMD detail did not include booking record summary.")

    updated_emd = put(
        f"/api/agencies/{agency_id}/emds/{emd['id']}",
        {
            "emd_number": "2209876543210",
            "emd_type": "emd_a",
            "reason_for_issuance_code": "C",
            "reason_for_issuance_subcode": "0B5",
            "issue_status": "issued",
            "currency": "EUR",
            "amount": 25,
            "taxes_amount": 0,
            "total_amount": 25,
            "internal_notes": "Manual EMD mirror smoke update.",
        },
        OWNER_HEADERS,
    )
    if updated_emd.get("emd", {}).get("emd_number") != "2209876543210":
        raise AssertionError("EMD manual update did not persist EMD number.")

    summary = get(
        f"/api/agencies/{agency_id}/booking-records/{booking_record['id']}/ticket-emd-readiness",
        OWNER_HEADERS,
    )
    if summary.get("ticket_count", 0) < 1 or summary.get("emd_count", 0) < 1:
        raise AssertionError("Ticket/EMD readiness summary did not count created mirrors.")
    if summary.get("provider_execution_disabled") is not True:
        raise AssertionError("Ticket/EMD readiness did not disable provider execution.")

    listed_tickets = get(f"/api/agencies/{agency_id}/tickets?booking_record_id={booking_record['id']}", OWNER_HEADERS)
    listed_emds = get(f"/api/agencies/{agency_id}/emds?booking_record_id={booking_record['id']}", OWNER_HEADERS)
    if not any(item["id"] == ticket["id"] for item in listed_tickets.get("items", [])):
        raise AssertionError("Ticket list did not include created ticket.")
    if not any(item["id"] == emd["id"] for item in listed_emds.get("items", [])):
        raise AssertionError("EMD list did not include created EMD.")

    final_readiness = get("/api/readiness")
    final_ticket_emd = final_readiness.get("ticket_emd_foundation") or {}
    if final_ticket_emd.get("provider_ticketing_disabled") is not True or final_ticket_emd.get("provider_emd_issuance_disabled") is not True:
        raise AssertionError("Provider execution flags changed unexpectedly.")

    print("Ticket and EMD foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Ticket and EMD foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
