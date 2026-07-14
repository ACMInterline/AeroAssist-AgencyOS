#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import (
    EmdWorkspace,
    EmdWorkspaceCouponStatus,
    EmdWorkspaceCreate,
    EmdWorkspaceDocumentStatus,
    EmdWorkspaceStatus,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request
from smoke_booking_workspace_foundation import (
    create_flight_workspace,
    create_offer_workspace,
    create_operational_workspace,
    create_passenger_workspace,
    create_trip_workspace,
)
from smoke_ticket_workspace_foundation import create_booking_workspace


EXPECTED_PHASE = "phase_55_4_airline_service_coverage_gap_management_foundation"
ROOT = Path(__file__).resolve().parents[2]
EMD_STATUSES = {"draft", "review", "ready", "archived"}
EMD_DOCUMENT_STATUSES = {"draft_metadata", "issued", "voided", "exchanged", "refunded", "partially_refunded", "cancelled", "unknown"}
EMD_COUPON_STATUSES = {"open_for_use", "airport_control", "checked_in", "flown", "used", "closed", "suspended", "void", "exchanged", "refunded", "unknown"}


def require_flag(section: dict, key: str, expected: object = True) -> None:
    if section.get(key) is not expected:
        raise AssertionError(f"Readiness flag {key} expected {expected!r}, got {section.get(key)!r}")


def require_text(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8")
    if text not in content:
        raise AssertionError(f"{path.relative_to(ROOT)} missing expected text: {text}")


def reject_text(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8")
    if text in content:
        raise AssertionError(f"{path.relative_to(ROOT)} contains rejected text: {text}")


def disabled_flags() -> list[str]:
    return [
        "emd_issuance_disabled",
        "emd_exchange_disabled",
        "emd_refund_disabled",
        "emd_voiding_disabled",
        "live_gds_ndc_connectivity_disabled",
        "gds_connectivity_disabled",
        "ndc_connectivity_disabled",
        "airline_apis_disabled",
        "airline_api_calls_disabled",
        "payment_processing_disabled",
        "rfic_rfisc_validation_engine_disabled",
        "ssr_osi_transmission_disabled",
        "background_workers_disabled",
        "external_integrations_disabled",
        "external_api_calls_disabled",
        "parallel_duplicate_emd_architecture_disabled",
        "automation_disabled",
    ]


def forbidden_enabled_flags() -> list[str]:
    return [
        "emd_issuance_enabled",
        "emd_exchange_enabled",
        "emd_refund_enabled",
        "emd_voiding_enabled",
        "live_gds_ndc_connectivity_enabled",
        "gds_connectivity_enabled",
        "ndc_connectivity_enabled",
        "airline_apis_enabled",
        "airline_api_calls_enabled",
        "payment_processing_enabled",
        "rfic_rfisc_validation_engine_enabled",
        "ssr_osi_transmission_enabled",
        "background_workers_enabled",
        "external_integrations_enabled",
        "external_api_calls_enabled",
        "parallel_duplicate_emd_architecture_enabled",
        "automation_enabled",
    ]


def assert_disabled_response(payload: dict) -> None:
    if payload.get("metadata_only") is not True:
        raise AssertionError(f"Payload is not metadata-only: {payload}")
    for flag in disabled_flags():
        if payload.get(flag) is not True:
            raise AssertionError(f"Payload missing disabled flag {flag}: {payload}")
    for flag in forbidden_enabled_flags():
        if payload.get(flag) is True:
            raise AssertionError(f"Payload exposes forbidden enabled flag {flag}: {payload}")


def verify_model_and_collection_registration() -> None:
    create_payload = EmdWorkspaceCreate(
        agency_id="agency-smoke",
        operational_workspace_id="workspace-smoke",
        trip_workspace_id="trip-smoke",
        offer_workspace_id="offer-smoke",
        booking_workspace_id="booking-smoke",
        ticket_workspace_id="ticket-smoke",
        emd_reference="EMDW-SMOKE-MODEL",
        emd_status=EmdWorkspaceStatus.READY,
        emd_document_status=EmdWorkspaceDocumentStatus.ISSUED,
        emd_type="ancillary",
        emd_number="2208200000001",
        emd_form_type="electronic",
        emd_a_or_s="EMD-A",
        validating_carrier="LH",
        issuing_agent="Taylor EMD",
        issuing_office="SOF001",
        issue_date="2028-03-05",
        passenger_id="passenger-smoke",
        passenger_name="EMD Passenger",
        booking_reference="BKGW-SMOKE",
        airline_pnr="LHABC1",
        gds_record_locator="GDSABC",
        associated_ticket_number="2201234567890",
        associated_ticket_coupon_numbers=["1"],
        associated_flight_workspace_ids=["flight-smoke"],
        ssr_ids=["ssr-smoke"],
        osi_ids=["osi-smoke"],
        ancillary_service_ids=["ancillary-smoke"],
        rfic="C",
        rfisc="0B5",
        service_reason="Baggage",
        service_description="Extra baggage",
        service_category="baggage",
        service_status="available",
        service_quantity=1,
        service_route_scope="SOF-FRA",
        service_segment_scope="SEG-1",
        emd_coupon_status_summary="Coupon 1 open for use.",
        emd_coupon_details=[
            {
                "coupon_number": "1",
                "coupon_status": EmdWorkspaceCouponStatus.OPEN_FOR_USE,
                "associated_ticket_number": "2201234567890",
                "associated_ticket_coupon_number": "1",
                "flight_workspace_id": "flight-smoke",
                "segment_reference": "SEG-1",
                "origin": "SOF",
                "destination": "FRA",
                "rfic": "C",
                "rfisc": "0B5",
                "service_description": "Extra baggage",
                "service_date": "2028-03-05",
                "not_valid_before": "2028-03-05",
                "not_valid_after": "2028-03-06",
                "amount": 120,
                "currency": "EUR",
                "remarks": "Metadata-only coupon detail.",
            }
        ],
        fare_amount=100,
        taxes_amount=20,
        total_amount=120,
        currency="EUR",
        tax_breakdown=[{"tax_code": "YQ", "amount": 20, "currency": "EUR", "description": "Carrier surcharge metadata."}],
        form_of_payment="card_metadata",
        payment_reference="PAY-EMD-META-1",
        payment_restrictions="Metadata-only payment restriction note.",
        exchange_reference_ids=["exchange-smoke"],
        refund_reference_ids=["refund-smoke"],
        void_reference_ids=["void-smoke"],
        linked_document_ids=["document-smoke"],
        lifecycle_notes="EMD document lifecycle metadata only.",
        operational_notes="Metadata-only EMD notes.",
        metadata={"smoke": True},
    )
    emd_workspace = EmdWorkspace(**create_payload.model_dump(mode="json", exclude_none=True))
    dumped = emd_workspace.model_dump(mode="json")
    if dumped.get("emd_status") != "ready" or dumped.get("emd_number") != "2208200000001":
        raise AssertionError(f"EMD workspace dimensions were not preserved: {dumped}")
    if dumped.get("emd_document_status") != "issued":
        raise AssertionError(f"EMD document status was not preserved: {dumped}")
    if (dumped.get("emd_coupon_details") or [{}])[0].get("coupon_status") != "open_for_use":
        raise AssertionError(f"EMD coupon status metadata was not preserved: {dumped}")
    if dumped.get("rfic") != "C" or dumped.get("rfisc") != "0B5":
        raise AssertionError(f"EMD RFIC/RFISC metadata was not preserved: {dumped}")
    for key in ["metadata_only", "emd_workspace_metadata_only", *disabled_flags()]:
        if dumped.get(key) is not True:
            raise AssertionError(f"EMD workspace model missing disabled flag {key}: {dumped}")
    if "emd_workspaces" not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("EMD workspaces collection is not registered.")
    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "emd_workspaces_id_unique",
        "emd_workspaces_reference_unique",
        "emd_workspaces_agency_status_lookup",
        "emd_workspaces_agency_type_lookup",
        "emd_workspaces_agency_a_or_s_lookup",
        "emd_workspaces_validating_carrier_lookup",
        "emd_workspaces_issue_date_lookup",
        "emd_workspaces_passenger_lookup",
        "emd_workspaces_rfic_lookup",
        "emd_workspaces_rfisc_lookup",
        "emd_workspaces_service_category_lookup",
        "emd_workspaces_operational_workspace_lookup",
        "emd_workspaces_trip_workspace_lookup",
        "emd_workspaces_offer_workspace_lookup",
        "emd_workspaces_booking_workspace_lookup",
        "emd_workspaces_ticket_workspace_lookup",
        "emd_workspaces_status_lookup",
        "emd_workspaces_document_status_lookup",
        "emd_workspaces_coupon_status_lookup",
        "emd_workspaces_emd_number_lookup",
        "emd_workspaces_associated_ticket_lookup",
        "emd_workspaces_flight_workspace_lookup",
        "emd_workspaces_ssr_lookup",
        "emd_workspaces_osi_lookup",
        "emd_workspaces_ancillary_service_lookup",
        "emd_workspaces_exchange_reference_lookup",
        "emd_workspaces_refund_reference_lookup",
        "emd_workspaces_void_reference_lookup",
        "emd_workspaces_document_lookup",
        "emd_workspaces_created_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"EMD workspace index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    expected_methods = {
        "/api/platform/emd-workspaces": {"get", "post"},
        "/api/platform/emd-workspaces/summary": {"get"},
        "/api/platform/emd-workspaces/{emd_workspace_id}": {"get", "put", "delete"},
        "/api/agencies/{agency_id}/emd-workspaces": {"get"},
        "/api/agencies/{agency_id}/emd-workspaces/summary": {"get"},
        "/api/agencies/{agency_id}/emd-workspaces/{emd_workspace_id}": {"get"},
    }
    for path, methods in expected_methods.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in [
        "/api/agencies/{agency_id}/emd-workspaces",
        "/api/agencies/{agency_id}/emd-workspaces/summary",
        "/api/agencies/{agency_id}/emd-workspaces/{emd_workspace_id}",
    ]:
        methods = set(paths.get(path, {}).keys())
        blocked_methods = methods & {"post", "put", "patch", "delete"}
        if blocked_methods:
            raise AssertionError(f"Agency EMD workspace route is not read-only: {path} {sorted(blocked_methods)}")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/lib/moduleCatalog.js", "EMD Workspaces"),
        (ROOT / "frontend/src/App.jsx", "/platform/emd-workspaces"),
        (ROOT / "frontend/src/App.jsx", "/agency/emd-workspaces"),
        (ROOT / "frontend/src/pages/platform/EmdWorkspacesPage.jsx", "EMD Workspaces"),
        (ROOT / "frontend/src/pages/platform/EmdWorkspacesPage.jsx", "No EMD issuance"),
        (ROOT / "frontend/src/pages/platform/EmdWorkspacesPage.jsx", "EMD document"),
        (ROOT / "frontend/src/pages/platform/EmdWorkspacesPage.jsx", "RFIC/RFISC"),
        (ROOT / "frontend/src/pages/platform/EmdWorkspacesPage.jsx", "Associated ticket"),
        (ROOT / "frontend/src/pages/platform/EmdWorkspacesPage.jsx", "Coupon details"),
        (ROOT / "frontend/src/pages/platform/EmdWorkspacesPage.jsx", "Exchange refs"),
        (ROOT / "frontend/src/pages/platform/EmdWorkspacesPage.jsx", "Lifecycle"),
        (ROOT / "frontend/src/pages/agency/EmdWorkspaceMetadataPage.jsx", "EMDs"),
        (ROOT / "frontend/src/pages/agency/EmdWorkspaceMetadataPage.jsx", "Read-only EMD workspace metadata"),
        (ROOT / "frontend/src/pages/agency/EmdWorkspaceMetadataPage.jsx", "No EMD issuance"),
        (ROOT / "frontend/src/pages/agency/EmdWorkspaceMetadataPage.jsx", "EMD document"),
        (ROOT / "frontend/src/pages/agency/EmdWorkspaceMetadataPage.jsx", "RFIC/RFISC"),
        (ROOT / "frontend/src/pages/agency/EmdWorkspaceMetadataPage.jsx", "Coupon details"),
        (ROOT / "frontend/src/pages/agency/EmdWorkspaceMetadataPage.jsx", "Refund refs"),
        (ROOT / "frontend/src/pages/agency/EmdWorkspaceMetadataPage.jsx", "Lifecycle"),
        (ROOT / "docs/architecture/emd-workspace-foundation.md", "EMD Workspace Foundation"),
        (ROOT / "docs/architecture/emd-workspace-foundation.md", "emd_document_status"),
        (ROOT / "docs/architecture/emd-workspace-foundation.md", "emd_coupon_details"),
        (ROOT / "docs/architecture/emd-workspace-foundation.md", "RFIC/RFISC"),
        (ROOT / "README.md", "Phase 41.8 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 41.8: EMD Workspace Foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "Phase 41.8 adds EMD workspace metadata"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "Phase 41.8 adds EMD workspace APIs"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "EMD workspaces"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "EMD workspaces"),
        (ROOT / "backend/services/blueprint_adoption_service.py", "EMD Workspaces"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/EmdWorkspacesPage.jsx",
        ROOT / "frontend/src/pages/agency/EmdWorkspaceMetadataPage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)
    for path in [
        ROOT / "frontend/src/pages/platform/EmdWorkspacesPage.jsx",
        ROOT / "frontend/src/pages/agency/EmdWorkspaceMetadataPage.jsx",
    ]:
        reject_text(path, "<button")
        reject_text(path, "apiPost")
        reject_text(path, "apiPut")


def verify_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")
    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("emd_workspace_foundation") or {}
    for flag in [
        "emd_workspaces_enabled",
        "emd_workspace_metadata_enabled",
        "platform_emd_workspace_metadata_crud_enabled",
        "agency_emd_workspace_read_only_enabled",
        "emd_workspace_filter_by_status_enabled",
        "emd_workspace_filter_by_type_enabled",
        "emd_workspace_filter_by_a_or_s_enabled",
        "emd_workspace_filter_by_validating_carrier_enabled",
        "emd_workspace_filter_by_passenger_enabled",
        "emd_workspace_filter_by_rfic_enabled",
        "emd_workspace_filter_by_rfisc_enabled",
        "emd_workspace_filter_by_service_category_enabled",
        "emd_workspace_filter_by_issue_date_enabled",
        "emd_reference_metadata_enabled",
        "emd_status_metadata_enabled",
        "emd_document_status_metadata_enabled",
        "emd_type_metadata_enabled",
        "emd_number_metadata_enabled",
        "emd_form_type_metadata_enabled",
        "emd_a_or_s_metadata_enabled",
        "validating_carrier_metadata_enabled",
        "issuing_metadata_enabled",
        "passenger_metadata_enabled",
        "booking_reference_metadata_enabled",
        "airline_pnr_metadata_enabled",
        "gds_record_locator_metadata_enabled",
        "associated_ticket_metadata_enabled",
        "associated_ticket_coupon_metadata_enabled",
        "associated_flight_metadata_enabled",
        "ssr_link_metadata_enabled",
        "osi_link_metadata_enabled",
        "ancillary_service_link_metadata_enabled",
        "rfic_metadata_enabled",
        "rfisc_metadata_enabled",
        "service_metadata_enabled",
        "emd_coupon_status_summary_metadata_enabled",
        "emd_coupon_details_metadata_enabled",
        "amount_metadata_enabled",
        "tax_breakdown_metadata_enabled",
        "payment_metadata_enabled",
        "exchange_reference_metadata_enabled",
        "refund_reference_metadata_enabled",
        "void_reference_metadata_enabled",
        "document_link_metadata_enabled",
        "lifecycle_notes_metadata_enabled",
        "operational_notes_metadata_enabled",
        "read_only_ui_enabled",
        "metadata_only",
        "emd_workspace_metadata_only",
    ]:
        require_flag(section, flag)
    for flag in disabled_flags():
        require_flag(section, flag)
    require_flag(section, "readiness_required", False)
    for count_key in [
        "emd_workspace_count",
        "emd_workspace_status_counts",
        "emd_document_status_counts",
        "emd_workspace_validating_carrier_count",
        "emd_workspace_currency_count",
        "emd_workspace_passenger_count",
        "emd_workspace_rfic_count",
        "emd_workspace_rfisc_count",
        "emd_workspace_service_category_count",
        "emd_workspace_booking_reference_count",
        "emd_workspace_operational_workspace_count",
        "emd_workspace_trip_workspace_count",
        "emd_workspace_offer_workspace_count",
        "emd_workspace_booking_workspace_count",
        "emd_workspace_ticket_workspace_count",
        "emd_workspace_coupon_detail_count",
        "emd_workspace_tax_breakdown_count",
        "emd_workspace_associated_ticket_coupon_count",
        "emd_workspace_associated_flight_workspace_count",
        "emd_workspace_ssr_count",
        "emd_workspace_osi_count",
        "emd_workspace_ancillary_service_count",
        "emd_workspace_exchange_reference_count",
        "emd_workspace_refund_reference_count",
        "emd_workspace_void_reference_count",
        "emd_workspace_linked_document_count",
    ]:
        if count_key not in section:
            raise AssertionError(f"EMD workspace readiness missing count: {count_key}")
    if not EMD_STATUSES.issubset(set((section.get("emd_workspace_status_counts") or {}).keys())):
        raise AssertionError(f"EMD workspace readiness status counts missing statuses: {section}")
    if not EMD_DOCUMENT_STATUSES.issubset(set((section.get("emd_document_status_counts") or {}).keys())):
        raise AssertionError(f"EMD workspace readiness document status counts missing statuses: {section}")
    previous_section = readiness.get("ticket_workspace_foundation") or {}
    if previous_section.get("metadata_only") is not True:
        raise AssertionError("Previous ticket workspace section should remain metadata-only.")


def verify_endpoint_behavior() -> None:
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires seeded demo agency.")
    agency_id = agencies[0]["id"]

    operational_workspace_id = create_operational_workspace(agency_id)
    passenger_id = create_passenger_workspace(agency_id, operational_workspace_id)
    flight_id = create_flight_workspace(agency_id, operational_workspace_id, passenger_id)
    trip_workspace_id = create_trip_workspace(agency_id, operational_workspace_id, passenger_id, flight_id)
    offer_workspace_id = create_offer_workspace(agency_id, operational_workspace_id, trip_workspace_id, passenger_id, flight_id)
    booking_workspace = create_booking_workspace(agency_id, operational_workspace_id, trip_workspace_id, offer_workspace_id, passenger_id, flight_id)
    booking_workspace_id = booking_workspace["id"]
    booking_reference = booking_workspace.get("booking_reference")
    ticket_workspace = create_ticket_workspace(
        agency_id,
        operational_workspace_id,
        trip_workspace_id,
        offer_workspace_id,
        booking_workspace_id,
        booking_reference,
        passenger_id,
        flight_id,
    )

    created = post(
        "/api/platform/emd-workspaces",
        emd_payload(
            agency_id,
            operational_workspace_id,
            trip_workspace_id,
            offer_workspace_id,
            booking_workspace_id,
            ticket_workspace["id"],
            booking_reference,
            passenger_id,
            flight_id,
        ),
        OWNER_HEADERS,
        201,
    )
    if created.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected create phase: {created.get('phase')}")
    assert_disabled_response(created)
    emd = created.get("emd_workspace") or {}
    assert_emd_shape(emd)
    emd_workspace_id = emd.get("id")
    if not emd_workspace_id:
        raise AssertionError(f"EMD workspace id missing: {created}")

    updated = put(
        f"/api/platform/emd-workspaces/{emd_workspace_id}",
        {
            "emd_status": "ready",
            "emd_document_status": "partially_refunded",
            "emd_coupon_status_summary": "Coupon 1 remains open for use in metadata only.",
            "lifecycle_notes": "Updated EMD lifecycle metadata only.",
            "operational_notes": "Updated metadata only; no EMD issuance.",
            "metadata": {"updated": True, "metadata_only": True},
        },
        OWNER_HEADERS,
    )
    assert_disabled_response(updated)
    updated_emd = updated.get("emd_workspace") or {}
    assert_emd_shape(updated_emd)
    if updated_emd.get("emd_status") != "ready":
        raise AssertionError(f"EMD workspace update did not persist metadata: {updated}")
    if updated_emd.get("emd_document_status") != "partially_refunded":
        raise AssertionError(f"EMD document status update did not persist metadata: {updated}")

    for filter_query in [
        f"agency_id={agency_id}",
        "status=ready",
        "emd_type=ancillary",
        "emd_a_or_s=EMD-A",
        "validating_carrier=LH",
        f"passenger={passenger_id}",
        "rfic=C",
        "rfisc=0B5",
        "service_category=baggage",
        "issue_date=2028-03-05",
    ]:
        filtered = get(f"/api/platform/emd-workspaces?{filter_query}", OWNER_HEADERS)
        assert_disabled_response(filtered)
        if not any(item.get("id") == emd_workspace_id for item in filtered.get("items") or []):
            raise AssertionError(f"EMD workspace filter {filter_query} missing created record: {filtered}")

    platform_summary = get("/api/platform/emd-workspaces/summary", OWNER_HEADERS)
    assert_summary_shape(platform_summary)

    platform_detail = get(f"/api/platform/emd-workspaces/{emd_workspace_id}", OWNER_HEADERS)
    assert_disabled_response(platform_detail)
    assert_emd_shape(platform_detail.get("emd_workspace") or {})

    agency_list = get(f"/api/agencies/{agency_id}/emd-workspaces?status=ready&emd_type=ancillary&validating_carrier=LH&rfic=C", OWNER_HEADERS)
    assert_disabled_response(agency_list)
    if agency_list.get("read_only") is not True:
        raise AssertionError(f"Agency EMD workspace list should be read-only: {agency_list}")
    agency_item = next((item for item in agency_list.get("items") or [] if item.get("id") == emd_workspace_id), None)
    if not agency_item:
        raise AssertionError(f"Agency EMD workspace list missing created record: {agency_list}")
    assert_emd_shape(agency_item, agency_view=True)

    agency_summary = get(f"/api/agencies/{agency_id}/emd-workspaces/summary", OWNER_HEADERS)
    assert_summary_shape(agency_summary, agency_id=agency_id)
    if agency_summary.get("read_only") is not True:
        raise AssertionError(f"Agency EMD workspace summary should be read-only: {agency_summary}")

    agency_detail = get(f"/api/agencies/{agency_id}/emd-workspaces/{emd_workspace_id}", OWNER_HEADERS)
    assert_disabled_response(agency_detail)
    if agency_detail.get("read_only") is not True:
        raise AssertionError(f"Agency EMD workspace detail should be read-only: {agency_detail}")
    assert_emd_shape(agency_detail.get("emd_workspace") or {}, agency_view=True)

    deleted = request("DELETE", f"/api/platform/emd-workspaces/{emd_workspace_id}", {}, OWNER_HEADERS)[1]
    assert_disabled_response(deleted)
    if deleted.get("archived") is not True or (deleted.get("emd_workspace") or {}).get("emd_status") != "archived":
        raise AssertionError(f"EMD workspace delete should be metadata-only archive: {deleted}")

    after_delete = get(f"/api/platform/emd-workspaces?agency_id={agency_id}", OWNER_HEADERS)
    if any(item.get("id") == emd_workspace_id for item in after_delete.get("items") or []):
        raise AssertionError(f"Default EMD workspace list should exclude archived-delete metadata: {after_delete}")
    include_archived = get(f"/api/platform/emd-workspaces?agency_id={agency_id}&include_archived=true", OWNER_HEADERS)
    if not any(item.get("id") == emd_workspace_id for item in include_archived.get("items") or []):
        raise AssertionError(f"include_archived should expose metadata-archived EMD workspace: {include_archived}")

    request("POST", f"/api/agencies/{agency_id}/emd-workspaces", {"emd_number": "blocked"}, OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/emd-workspaces/{emd_workspace_id}", {"emd_status": "ready"}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/emd-workspaces/{emd_workspace_id}", {}, OWNER_HEADERS, 405)


def create_ticket_workspace(
    agency_id: str,
    operational_workspace_id: str,
    trip_workspace_id: str,
    offer_workspace_id: str,
    booking_workspace_id: str,
    booking_reference: str,
    passenger_id: str,
    flight_id: str,
) -> dict:
    created = post(
        "/api/platform/ticket-workspaces",
        {
            "agency_id": agency_id,
            "operational_workspace_id": operational_workspace_id,
            "trip_workspace_id": trip_workspace_id,
            "offer_workspace_id": offer_workspace_id,
            "booking_workspace_id": booking_workspace_id,
            "ticket_status": "ready",
            "ticket_document_status": "issued",
            "ticket_type": "eticket",
            "ticket_number": "2201234567890",
            "validating_carrier": "LH",
            "issue_date": "2028-03-05",
            "passenger_id": passenger_id,
            "passenger_name": "EMD Linked Passenger",
            "flight_workspace_ids": [flight_id],
            "booking_reference": booking_reference,
            "airline_pnr": "LHABC1",
            "gds_record_locator": "GDSABC",
            "coupon_status_summary": "Coupon 1 open for use.",
            "coupon_details": [
                {
                    "coupon_number": "1",
                    "flight_workspace_id": flight_id,
                    "segment_reference": "SEG-1",
                    "origin": "SOF",
                    "destination": "FRA",
                    "coupon_status": "open_for_use",
                    "fare_basis": "YFLEX",
                }
            ],
            "operational_notes": "Metadata-only ticket for EMD workspace smoke.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    ticket_workspace = created.get("ticket_workspace") or {}
    if not ticket_workspace.get("id"):
        raise AssertionError(f"Ticket workspace id missing for EMD smoke: {created}")
    return ticket_workspace


def emd_payload(
    agency_id: str,
    operational_workspace_id: str,
    trip_workspace_id: str,
    offer_workspace_id: str,
    booking_workspace_id: str,
    ticket_workspace_id: str,
    booking_reference: str,
    passenger_id: str,
    flight_id: str,
) -> dict:
    return {
        "agency_id": agency_id,
        "operational_workspace_id": operational_workspace_id,
        "trip_workspace_id": trip_workspace_id,
        "offer_workspace_id": offer_workspace_id,
        "booking_workspace_id": booking_workspace_id,
        "ticket_workspace_id": ticket_workspace_id,
        "emd_status": "draft",
        "emd_document_status": "issued",
        "emd_type": "ancillary",
        "emd_number": "2208200000001",
        "emd_form_type": "electronic",
        "emd_a_or_s": "EMD-A",
        "validating_carrier": "LH",
        "issuing_agent": "Taylor EMD",
        "issuing_office": "SOF001",
        "issue_date": "2028-03-05",
        "passenger_id": passenger_id,
        "passenger_name": "EMD Passenger",
        "booking_reference": booking_reference,
        "airline_pnr": "LHABC1",
        "gds_record_locator": "GDSABC",
        "associated_ticket_number": "2201234567890",
        "associated_ticket_coupon_numbers": ["1"],
        "associated_flight_workspace_ids": [flight_id],
        "ssr_ids": ["ssr-smoke"],
        "osi_ids": ["osi-smoke"],
        "ancillary_service_ids": ["ancillary-smoke"],
        "rfic": "C",
        "rfisc": "0B5",
        "service_reason": "Baggage",
        "service_description": "Extra baggage",
        "service_category": "baggage",
        "service_status": "available",
        "service_quantity": 1,
        "service_route_scope": "SOF-FRA",
        "service_segment_scope": "SEG-1",
        "emd_coupon_status_summary": "Coupon 1 open for use.",
        "emd_coupon_details": [
            {
                "coupon_number": "1",
                "coupon_status": "open_for_use",
                "associated_ticket_number": "2201234567890",
                "associated_ticket_coupon_number": "1",
                "flight_workspace_id": flight_id,
                "segment_reference": "SEG-1",
                "origin": "SOF",
                "destination": "FRA",
                "rfic": "C",
                "rfisc": "0B5",
                "service_description": "Extra baggage",
                "service_date": "2028-03-05",
                "not_valid_before": "2028-03-05",
                "not_valid_after": "2028-03-06",
                "amount": 120,
                "currency": "EUR",
                "remarks": "Metadata-only coupon detail.",
            }
        ],
        "fare_amount": 100,
        "taxes_amount": 20,
        "total_amount": 120,
        "currency": "EUR",
        "tax_breakdown": [{"tax_code": "YQ", "amount": 20, "currency": "EUR", "description": "Carrier surcharge metadata."}],
        "form_of_payment": "card_metadata",
        "payment_reference": "PAY-EMD-META-1",
        "payment_restrictions": "Metadata-only payment restriction note.",
        "exchange_reference_ids": ["exchange-smoke"],
        "refund_reference_ids": ["refund-smoke"],
        "void_reference_ids": ["void-smoke"],
        "linked_document_ids": ["document-smoke"],
        "lifecycle_notes": "EMD document lifecycle metadata only.",
        "operational_notes": "Metadata-only EMD notes.",
        "metadata": {"smoke": True, "metadata_only": True},
    }


def assert_summary_shape(payload: dict, agency_id: str | None = None) -> None:
    assert_disabled_response(payload)
    if agency_id and payload.get("agency_id") != agency_id:
        raise AssertionError(f"Agency summary should preserve agency_id: {payload}")
    summary = payload.get("summary") or {}
    for key in [
        "total_count",
        "by_status",
        "by_document_status",
        "by_coupon_status",
        "by_type",
        "by_a_or_s",
        "by_validating_carrier",
        "by_rfic",
        "by_rfisc",
        "by_service_category",
        "agency_count",
        "passenger_count",
        "associated_ticket_coupon_count",
        "associated_flight_workspace_count",
        "ssr_count",
        "osi_count",
        "ancillary_service_count",
        "emd_coupon_detail_count",
        "tax_breakdown_count",
        "exchange_reference_count",
        "refund_reference_count",
        "void_reference_count",
        "linked_document_count",
        "fare_amount_total",
        "taxes_amount_total",
        "total_amount_total",
    ]:
        if key not in summary:
            raise AssertionError(f"EMD workspace summary missing {key}: {payload}")
    if not EMD_STATUSES.issubset(set((summary.get("by_status") or {}).keys())):
        raise AssertionError(f"EMD workspace summary missing status buckets: {summary}")
    if not EMD_DOCUMENT_STATUSES.issubset(set((summary.get("by_document_status") or {}).keys())):
        raise AssertionError(f"EMD workspace summary missing document status buckets: {summary}")
    if not EMD_COUPON_STATUSES.issubset(set((summary.get("by_coupon_status") or {}).keys())):
        raise AssertionError(f"EMD workspace summary missing coupon status buckets: {summary}")


def assert_emd_shape(emd: dict, agency_view: bool = False) -> None:
    required_keys = [
        "id",
        "agency_id",
        "operational_workspace_id",
        "trip_workspace_id",
        "offer_workspace_id",
        "booking_workspace_id",
        "ticket_workspace_id",
        "emd_reference",
        "emd_status",
        "emd_document_status",
        "emd_type",
        "emd_number",
        "emd_form_type",
        "emd_a_or_s",
        "validating_carrier",
        "issuing_agent",
        "issuing_office",
        "issue_date",
        "passenger_id",
        "passenger_name",
        "booking_reference",
        "airline_pnr",
        "gds_record_locator",
        "associated_ticket_number",
        "associated_ticket_coupon_numbers",
        "associated_flight_workspace_ids",
        "ssr_ids",
        "osi_ids",
        "ancillary_service_ids",
        "rfic",
        "rfisc",
        "service_reason",
        "service_description",
        "service_category",
        "service_status",
        "service_quantity",
        "service_route_scope",
        "service_segment_scope",
        "emd_coupon_status_summary",
        "emd_coupon_details",
        "fare_amount",
        "taxes_amount",
        "total_amount",
        "currency",
        "tax_breakdown",
        "form_of_payment",
        "payment_reference",
        "payment_restrictions",
        "exchange_reference_ids",
        "refund_reference_ids",
        "void_reference_ids",
        "linked_document_ids",
        "lifecycle_notes",
        "operational_notes",
        "emd_display_name",
        "agency",
        "metadata_only",
        "emd_workspace_metadata_only",
    ]
    for key in required_keys:
        if key not in emd:
            raise AssertionError(f"EMD workspace missing {key}: {emd}")
    coupon = (emd.get("emd_coupon_details") or [{}])[0]
    for key in ["coupon_status", "associated_ticket_number", "associated_ticket_coupon_number", "rfic", "rfisc", "service_description"]:
        if key not in coupon:
            raise AssertionError(f"EMD coupon detail missing {key}: {emd}")
    if agency_view and emd.get("read_only") is not True:
        raise AssertionError(f"Agency EMD workspace item should be read-only: {emd}")
    for flag in disabled_flags():
        if emd.get(flag) is not True:
            raise AssertionError(f"EMD workspace missing disabled flag {flag}: {emd}")


def verify_blueprint_gap_summary() -> None:
    gaps = get("/api/platform/blueprint/gaps", OWNER_HEADERS)
    if not any("EMD workspace foundation built in Phase 41.8" in item for item in gaps.get("already_built", [])):
        raise AssertionError(f"Blueprint gap summary did not recognize EMD workspace foundation: {gaps}")
    if "Phase 50.9" not in gaps.get("next_intelligence_phase", ""):
        raise AssertionError(f"Blueprint gap summary did not preserve next intelligence phase: {gaps}")
    if "Phase 42.2" not in gaps.get("next_operational_phase", ""):
        raise AssertionError(f"Blueprint gap summary did not preserve next operational phase: {gaps}")
    adoption = get("/api/platform/blueprint/adoption-map", OWNER_HEADERS)
    if not any(item.get("category") == "EMD Workspaces" for item in adoption.get("items") or []):
        raise AssertionError(f"Blueprint adoption map missing EMD Workspaces: {adoption}")


def main() -> None:
    verify_model_and_collection_registration()
    openapi = get("/openapi.json")
    verify_routes(openapi.get("paths", {}))
    verify_frontend_and_docs()
    verify_readiness()
    verify_endpoint_behavior()
    verify_blueprint_gap_summary()
    print("EMD workspace foundation smoke passed.")


if __name__ == "__main__":
    main()
