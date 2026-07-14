#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import (
    TicketDocumentStatus,
    TicketWorkspace,
    TicketWorkspaceCouponStatus,
    TicketWorkspaceCreate,
    TicketWorkspaceStatus,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request
from smoke_booking_workspace_foundation import (
    create_flight_workspace,
    create_offer_workspace,
    create_operational_workspace,
    create_passenger_workspace,
    create_trip_workspace,
)


EXPECTED_PHASE = "phase_55_4_airline_service_coverage_gap_management_foundation"
ROOT = Path(__file__).resolve().parents[2]
TICKET_STATUSES = {"draft", "review", "ready", "archived"}
TICKET_DOCUMENT_STATUSES = {"draft_metadata", "issued", "voided", "exchanged", "refunded", "partially_refunded", "cancelled", "unknown"}
TICKET_COUPON_STATUSES = {"open_for_use", "airport_control", "checked_in", "flown", "closed", "suspended", "void", "exchanged", "refunded", "unknown"}


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
        "ticket_issuance_disabled",
        "ticket_reissue_disabled",
        "voiding_disabled",
        "void_workflow_disabled",
        "refunds_disabled",
        "refund_workflow_disabled",
        "exchanges_disabled",
        "exchange_workflow_disabled",
        "payment_processing_disabled",
        "gds_connectivity_disabled",
        "ndc_connectivity_disabled",
        "airline_apis_disabled",
        "airline_api_calls_disabled",
        "fare_calculation_disabled",
        "fare_recalculation_disabled",
        "automated_ticket_validation_disabled",
        "coupon_validation_disabled",
        "background_workers_disabled",
        "external_integrations_disabled",
        "external_api_calls_disabled",
        "automation_disabled",
    ]


def forbidden_enabled_flags() -> list[str]:
    return [
        "ticket_issuance_enabled",
        "ticket_reissue_enabled",
        "voiding_enabled",
        "void_workflow_enabled",
        "refunds_enabled",
        "refund_workflow_enabled",
        "exchanges_enabled",
        "exchange_workflow_enabled",
        "payment_processing_enabled",
        "gds_connectivity_enabled",
        "ndc_connectivity_enabled",
        "airline_apis_enabled",
        "airline_api_calls_enabled",
        "fare_calculation_enabled",
        "fare_recalculation_enabled",
        "automated_ticket_validation_enabled",
        "coupon_validation_enabled",
        "background_workers_enabled",
        "external_integrations_enabled",
        "external_api_calls_enabled",
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
    create_payload = TicketWorkspaceCreate(
        agency_id="agency-smoke",
        operational_workspace_id="workspace-smoke",
        trip_workspace_id="trip-smoke",
        offer_workspace_id="offer-smoke",
        booking_workspace_id="booking-smoke",
        ticket_reference="TKTW-SMOKE-MODEL",
        ticket_status=TicketWorkspaceStatus.READY,
        ticket_document_status=TicketDocumentStatus.ISSUED,
        ticket_type="eticket",
        ticket_number="2201234567890",
        validating_carrier="LH",
        issuing_agent="Taylor Ticket",
        issuing_office="SOF001",
        issue_date="2028-02-05",
        passenger_id="passenger-smoke",
        passenger_name="Ticket Passenger",
        flight_workspace_ids=["flight-smoke"],
        booking_reference="BKGW-SMOKE",
        airline_pnr="LHABC1",
        gds_record_locator="GDSABC",
        fare_basis_summary="YFLEX",
        fare_amount=1000,
        taxes_amount=150,
        total_amount=1150,
        currency="EUR",
        fare_calculation_line="SOF LH FRA Q10.00 900.00NUC910.00END ROE0.9234",
        fare_calculation_currency="NUC",
        fare_calculation_nuc_total=910,
        fare_calculation_roe=0.9234,
        equivalent_fare_paid=840,
        equivalent_fare_currency="EUR",
        form_of_payment="card_metadata",
        payment_reference="PAY-META-1",
        payment_restrictions="Metadata-only payment restriction note.",
        commission_summary="Commission metadata only.",
        tax_breakdown=[
            {"tax_code": "YQ", "amount": 90, "currency": "EUR", "description": "Carrier surcharge metadata."},
            {"tax_code": "RA", "amount": 60, "currency": "EUR", "description": "Airport tax metadata."},
        ],
        fare_construction_notes="Fare construction metadata for later exchange review.",
        pricing_units=[
            {
                "pricing_unit_reference": "PU-1",
                "pricing_unit_type": "one_way",
                "origin": "SOF",
                "destination": "FRA",
                "fare_component_references": ["FC-1"],
                "nuc_amount": 910,
                "currency": "NUC",
                "notes": "Pricing unit metadata only.",
            }
        ],
        fare_components=[
            {
                "fare_component_reference": "FC-1",
                "origin": "SOF",
                "destination": "FRA",
                "carrier": "LH",
                "fare_basis": "YFLEX",
                "booking_class": "Y",
                "nuc_amount": 910,
                "mileage_or_routing_note": "MPM metadata only.",
                "rule_reference": "RULE-1",
                "notes": "Fare component metadata only.",
            }
        ],
        coupon_summary="Two coupons metadata only.",
        coupon_status_summary="Coupon 1 open for use; coupon 2 unknown.",
        coupon_details=[
            {
                "coupon_number": "1",
                "flight_workspace_id": "flight-smoke",
                "segment_reference": "SEG-1",
                "origin": "SOF",
                "destination": "FRA",
                "marketing_carrier": "LH",
                "operating_carrier": "LH",
                "fare_basis": "YFLEX",
                "fare_component_reference": "FC-1",
                "pricing_unit_reference": "PU-1",
                "coupon_status": TicketWorkspaceCouponStatus.OPEN_FOR_USE,
                "not_valid_before": "2028-02-05",
                "not_valid_after": "2028-02-06",
                "baggage_summary": "One checked bag.",
                "remarks": "Metadata-only coupon detail.",
            }
        ],
        baggage_summary="One checked bag.",
        endorsement_summary="Non-endorsable metadata only.",
        restrictions_summary="Manual restrictions metadata.",
        exchange_reference_ids=["exchange-smoke"],
        refund_reference_ids=["refund-smoke"],
        void_reference_ids=["void-smoke"],
        linked_emd_ids=["emd-smoke"],
        linked_document_ids=["document-smoke"],
        lifecycle_notes="Ticket document lifecycle metadata only.",
        operational_notes="Metadata-only ticket notes.",
        metadata={"smoke": True},
    )
    ticket_workspace = TicketWorkspace(**create_payload.model_dump(mode="json", exclude_none=True))
    dumped = ticket_workspace.model_dump(mode="json")
    if dumped.get("ticket_status") != "ready" or dumped.get("ticket_number") != "2201234567890":
        raise AssertionError(f"Ticket workspace dimensions were not preserved: {dumped}")
    if dumped.get("ticket_document_status") != "issued":
        raise AssertionError(f"Ticket document status was not preserved: {dumped}")
    if (dumped.get("coupon_details") or [{}])[0].get("coupon_status") != "open_for_use":
        raise AssertionError(f"Ticket coupon status metadata was not preserved: {dumped}")
    if (dumped.get("coupon_details") or [{}])[0].get("fare_component_reference") != "FC-1":
        raise AssertionError(f"Coupon fare component metadata was not preserved: {dumped}")
    if (dumped.get("pricing_units") or [{}])[0].get("pricing_unit_reference") != "PU-1":
        raise AssertionError(f"Pricing unit metadata was not preserved: {dumped}")
    if (dumped.get("fare_components") or [{}])[0].get("fare_component_reference") != "FC-1":
        raise AssertionError(f"Fare component metadata was not preserved: {dumped}")
    if dumped.get("fare_calculation_nuc_total") != 910:
        raise AssertionError(f"Fare calculation metadata was not preserved: {dumped}")
    for key in ["metadata_only", "ticket_workspace_metadata_only", *disabled_flags()]:
        if dumped.get(key) is not True:
            raise AssertionError(f"Ticket workspace model missing disabled flag {key}: {dumped}")
    if "ticket_workspaces" not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("Ticket workspaces collection is not registered.")
    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "ticket_workspaces_id_unique",
        "ticket_workspaces_reference_unique",
        "ticket_workspaces_agency_status_lookup",
        "ticket_workspaces_validating_carrier_lookup",
        "ticket_workspaces_issue_date_lookup",
        "ticket_workspaces_passenger_lookup",
        "ticket_workspaces_booking_reference_lookup",
        "ticket_workspaces_currency_lookup",
        "ticket_workspaces_operational_workspace_lookup",
        "ticket_workspaces_trip_workspace_lookup",
        "ticket_workspaces_offer_workspace_lookup",
        "ticket_workspaces_booking_workspace_lookup",
        "ticket_workspaces_status_lookup",
        "ticket_workspaces_document_status_lookup",
        "ticket_workspaces_coupon_status_lookup",
        "ticket_workspaces_coupon_fare_basis_lookup",
        "ticket_workspaces_type_lookup",
        "ticket_workspaces_ticket_number_lookup",
        "ticket_workspaces_fare_calculation_currency_lookup",
        "ticket_workspaces_equivalent_fare_currency_lookup",
        "ticket_workspaces_form_of_payment_lookup",
        "ticket_workspaces_pricing_unit_reference_lookup",
        "ticket_workspaces_fare_component_reference_lookup",
        "ticket_workspaces_airline_pnr_lookup",
        "ticket_workspaces_gds_locator_lookup",
        "ticket_workspaces_flight_workspace_lookup",
        "ticket_workspaces_emd_lookup",
        "ticket_workspaces_document_lookup",
        "ticket_workspaces_exchange_reference_lookup",
        "ticket_workspaces_refund_reference_lookup",
        "ticket_workspaces_void_reference_lookup",
        "ticket_workspaces_created_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Ticket workspace index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    expected_methods = {
        "/api/platform/ticket-workspaces": {"get", "post"},
        "/api/platform/ticket-workspaces/summary": {"get"},
        "/api/platform/ticket-workspaces/{ticket_workspace_id}": {"get", "put", "delete"},
        "/api/agencies/{agency_id}/ticket-workspaces": {"get"},
        "/api/agencies/{agency_id}/ticket-workspaces/summary": {"get"},
        "/api/agencies/{agency_id}/ticket-workspaces/{ticket_workspace_id}": {"get"},
    }
    for path, methods in expected_methods.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in [
        "/api/agencies/{agency_id}/ticket-workspaces",
        "/api/agencies/{agency_id}/ticket-workspaces/summary",
        "/api/agencies/{agency_id}/ticket-workspaces/{ticket_workspace_id}",
    ]:
        methods = set(paths.get(path, {}).keys())
        blocked_methods = methods & {"post", "put", "patch", "delete"}
        if blocked_methods:
            raise AssertionError(f"Agency ticket workspace route is not read-only: {path} {sorted(blocked_methods)}")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Ticket Workspaces"),
        (ROOT / "frontend/src/App.jsx", "/platform/ticket-workspaces"),
        (ROOT / "frontend/src/App.jsx", "/agency/ticket-workspaces"),
        (ROOT / "frontend/src/pages/platform/TicketWorkspacesPage.jsx", "Ticket Workspaces"),
        (ROOT / "frontend/src/pages/platform/TicketWorkspacesPage.jsx", "No issuance"),
        (ROOT / "frontend/src/pages/platform/TicketWorkspacesPage.jsx", "Ticket document"),
        (ROOT / "frontend/src/pages/platform/TicketWorkspacesPage.jsx", "Coupon details"),
        (ROOT / "frontend/src/pages/platform/TicketWorkspacesPage.jsx", "Coupon-level fare basis"),
        (ROOT / "frontend/src/pages/platform/TicketWorkspacesPage.jsx", "Fare calculation line"),
        (ROOT / "frontend/src/pages/platform/TicketWorkspacesPage.jsx", "NUC total"),
        (ROOT / "frontend/src/pages/platform/TicketWorkspacesPage.jsx", "Equivalent fare paid"),
        (ROOT / "frontend/src/pages/platform/TicketWorkspacesPage.jsx", "Form of payment"),
        (ROOT / "frontend/src/pages/platform/TicketWorkspacesPage.jsx", "Tax breakdown"),
        (ROOT / "frontend/src/pages/platform/TicketWorkspacesPage.jsx", "Pricing units"),
        (ROOT / "frontend/src/pages/platform/TicketWorkspacesPage.jsx", "Fare components"),
        (ROOT / "frontend/src/pages/platform/TicketWorkspacesPage.jsx", "Exchange refs"),
        (ROOT / "frontend/src/pages/platform/TicketWorkspacesPage.jsx", "Lifecycle"),
        (ROOT / "frontend/src/pages/platform/TicketWorkspacesPage.jsx", "Validating carrier"),
        (ROOT / "frontend/src/pages/agency/TicketWorkspaceMetadataPage.jsx", "Tickets"),
        (ROOT / "frontend/src/pages/agency/TicketWorkspaceMetadataPage.jsx", "Read-only ticket workspace metadata"),
        (ROOT / "frontend/src/pages/agency/TicketWorkspaceMetadataPage.jsx", "No ticket issuance"),
        (ROOT / "frontend/src/pages/agency/TicketWorkspaceMetadataPage.jsx", "Ticket document"),
        (ROOT / "frontend/src/pages/agency/TicketWorkspaceMetadataPage.jsx", "Coupon details"),
        (ROOT / "frontend/src/pages/agency/TicketWorkspaceMetadataPage.jsx", "Coupon-level fare basis"),
        (ROOT / "frontend/src/pages/agency/TicketWorkspaceMetadataPage.jsx", "Fare calculation line"),
        (ROOT / "frontend/src/pages/agency/TicketWorkspaceMetadataPage.jsx", "Tax breakdown"),
        (ROOT / "frontend/src/pages/agency/TicketWorkspaceMetadataPage.jsx", "Pricing units"),
        (ROOT / "frontend/src/pages/agency/TicketWorkspaceMetadataPage.jsx", "Fare components"),
        (ROOT / "frontend/src/pages/agency/TicketWorkspaceMetadataPage.jsx", "Refund refs"),
        (ROOT / "frontend/src/pages/agency/TicketWorkspaceMetadataPage.jsx", "Lifecycle"),
        (ROOT / "docs/architecture/ticket-workspace-foundation.md", "Ticket Workspace Foundation"),
        (ROOT / "docs/architecture/ticket-workspace-foundation.md", "ticket_document_status"),
        (ROOT / "docs/architecture/ticket-workspace-foundation.md", "coupon_details"),
        (ROOT / "docs/architecture/ticket-workspace-foundation.md", "whole-ticket document status"),
        (ROOT / "docs/architecture/ticket-workspace-foundation.md", "fare_calculation_line"),
        (ROOT / "docs/architecture/ticket-workspace-foundation.md", "pricing_units"),
        (ROOT / "docs/architecture/ticket-workspace-foundation.md", "fare_components"),
        (ROOT / "README.md", "Phase 41.7 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 41.7: Ticket Workspace Foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "Phase 41.7 adds ticket workspace metadata"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "Phase 41.7 adds ticket workspace APIs"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Ticket workspaces"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Ticket workspaces"),
        (ROOT / "backend/services/blueprint_adoption_service.py", "Ticket Workspaces"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/TicketWorkspacesPage.jsx",
        ROOT / "frontend/src/pages/agency/TicketWorkspaceMetadataPage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)
    for path in [
        ROOT / "frontend/src/pages/platform/TicketWorkspacesPage.jsx",
        ROOT / "frontend/src/pages/agency/TicketWorkspaceMetadataPage.jsx",
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
    section = readiness.get("ticket_workspace_foundation") or {}
    for flag in [
        "ticket_workspaces_enabled",
        "ticket_workspace_metadata_enabled",
        "platform_ticket_workspace_metadata_crud_enabled",
        "agency_ticket_workspace_read_only_enabled",
        "ticket_workspace_filter_by_status_enabled",
        "ticket_workspace_filter_by_document_status_enabled",
        "ticket_workspace_filter_by_validating_carrier_enabled",
        "ticket_workspace_filter_by_issue_date_enabled",
        "ticket_workspace_filter_by_passenger_enabled",
        "ticket_workspace_filter_by_booking_reference_enabled",
        "ticket_workspace_filter_by_currency_enabled",
        "ticket_reference_metadata_enabled",
        "ticket_status_metadata_enabled",
        "ticket_document_status_metadata_enabled",
        "ticket_type_metadata_enabled",
        "ticket_number_metadata_enabled",
        "validating_carrier_metadata_enabled",
        "issuing_agent_metadata_enabled",
        "issuing_office_metadata_enabled",
        "issue_date_metadata_enabled",
        "passenger_metadata_enabled",
        "flight_summary_metadata_enabled",
        "booking_reference_metadata_enabled",
        "airline_pnr_metadata_enabled",
        "gds_record_locator_metadata_enabled",
        "fare_basis_metadata_enabled",
        "fare_amount_metadata_enabled",
        "taxes_amount_metadata_enabled",
        "total_amount_metadata_enabled",
        "fare_calculation_line_metadata_enabled",
        "fare_calculation_currency_metadata_enabled",
        "fare_calculation_nuc_total_metadata_enabled",
        "fare_calculation_roe_metadata_enabled",
        "equivalent_fare_metadata_enabled",
        "form_of_payment_metadata_enabled",
        "payment_reference_metadata_enabled",
        "payment_restrictions_metadata_enabled",
        "commission_summary_metadata_enabled",
        "tax_breakdown_metadata_enabled",
        "fare_construction_notes_metadata_enabled",
        "pricing_units_metadata_enabled",
        "fare_components_metadata_enabled",
        "coupon_summary_metadata_enabled",
        "coupon_status_summary_metadata_enabled",
        "coupon_details_metadata_enabled",
        "baggage_summary_metadata_enabled",
        "endorsement_summary_metadata_enabled",
        "restrictions_summary_metadata_enabled",
        "exchange_reference_metadata_enabled",
        "refund_reference_metadata_enabled",
        "void_reference_metadata_enabled",
        "emd_link_metadata_enabled",
        "document_link_metadata_enabled",
        "lifecycle_notes_metadata_enabled",
        "operational_notes_metadata_enabled",
        "read_only_ui_enabled",
        "metadata_only",
        "ticket_workspace_metadata_only",
    ]:
        require_flag(section, flag)
    for flag in disabled_flags():
        require_flag(section, flag)
    require_flag(section, "readiness_required", False)
    for count_key in [
        "ticket_workspace_count",
        "ticket_workspace_status_counts",
        "ticket_document_status_counts",
        "ticket_workspace_validating_carrier_count",
        "ticket_workspace_currency_count",
        "ticket_workspace_passenger_count",
        "ticket_workspace_booking_reference_count",
        "ticket_workspace_operational_workspace_count",
        "ticket_workspace_trip_workspace_count",
        "ticket_workspace_offer_workspace_count",
        "ticket_workspace_booking_workspace_count",
        "ticket_workspace_coupon_detail_count",
        "ticket_workspace_pricing_unit_count",
        "ticket_workspace_fare_component_count",
        "ticket_workspace_tax_breakdown_count",
        "ticket_workspace_exchange_reference_count",
        "ticket_workspace_refund_reference_count",
        "ticket_workspace_void_reference_count",
    ]:
        if count_key not in section:
            raise AssertionError(f"Ticket workspace readiness missing count: {count_key}")
    if not TICKET_STATUSES.issubset(set((section.get("ticket_workspace_status_counts") or {}).keys())):
        raise AssertionError(f"Ticket workspace readiness status counts missing statuses: {section}")
    if not TICKET_DOCUMENT_STATUSES.issubset(set((section.get("ticket_document_status_counts") or {}).keys())):
        raise AssertionError(f"Ticket workspace readiness document status counts missing statuses: {section}")
    previous_section = readiness.get("booking_workspace_foundation") or {}
    if previous_section.get("metadata_only") is not True:
        raise AssertionError("Previous booking workspace section should remain metadata-only.")


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

    created = post(
        "/api/platform/ticket-workspaces",
        {
            "agency_id": agency_id,
            "operational_workspace_id": operational_workspace_id,
            "trip_workspace_id": trip_workspace_id,
            "offer_workspace_id": offer_workspace_id,
            "booking_workspace_id": booking_workspace_id,
            "ticket_status": "draft",
            "ticket_type": "eticket",
            "ticket_number": "2201234567890",
            "validating_carrier": "LH",
            "issuing_agent": "Taylor Ticket",
            "issuing_office": "SOF001",
            "issue_date": "2028-02-05",
            "passenger_id": passenger_id,
            "passenger_name": "Ticket Passenger",
            "flight_workspace_ids": [flight_id],
            "booking_reference": booking_reference,
            "airline_pnr": "LHABC1",
            "gds_record_locator": "GDSABC",
            "ticket_document_status": "issued",
            "fare_basis_summary": "YFLEX",
            "fare_amount": 1000,
            "taxes_amount": 150,
            "total_amount": 1150,
            "currency": "EUR",
            "fare_calculation_line": "SOF LH FRA Q10.00 900.00NUC910.00END ROE0.9234",
            "fare_calculation_currency": "NUC",
            "fare_calculation_nuc_total": 910,
            "fare_calculation_roe": 0.9234,
            "equivalent_fare_paid": 840,
            "equivalent_fare_currency": "EUR",
            "form_of_payment": "card_metadata",
            "payment_reference": "PAY-META-1",
            "payment_restrictions": "Metadata-only payment restriction note.",
            "commission_summary": "Commission metadata only.",
            "tax_breakdown": [
                {"tax_code": "YQ", "amount": 90, "currency": "EUR", "description": "Carrier surcharge metadata."},
                {"tax_code": "RA", "amount": 60, "currency": "EUR", "description": "Airport tax metadata."},
            ],
            "fare_construction_notes": "Fare construction metadata for later exchange review.",
            "pricing_units": [
                {
                    "pricing_unit_reference": "PU-1",
                    "pricing_unit_type": "one_way",
                    "origin": "SOF",
                    "destination": "FRA",
                    "fare_component_references": ["FC-1"],
                    "nuc_amount": 910,
                    "currency": "NUC",
                    "notes": "Pricing unit metadata only.",
                }
            ],
            "fare_components": [
                {
                    "fare_component_reference": "FC-1",
                    "origin": "SOF",
                    "destination": "FRA",
                    "carrier": "LH",
                    "fare_basis": "YFLEX",
                    "booking_class": "Y",
                    "nuc_amount": 910,
                    "mileage_or_routing_note": "MPM metadata only.",
                    "rule_reference": "RULE-1",
                    "notes": "Fare component metadata only.",
                }
            ],
            "coupon_summary": "Two coupons metadata only.",
            "coupon_status_summary": "Coupon 1 open for use; coupon 2 unknown.",
            "coupon_details": [
                {
                    "coupon_number": "1",
                    "flight_workspace_id": flight_id,
                    "segment_reference": "SEG-1",
                    "origin": "SOF",
                    "destination": "FRA",
                    "marketing_carrier": "LH",
                    "operating_carrier": "LH",
                    "fare_basis": "YFLEX",
                    "fare_component_reference": "FC-1",
                    "pricing_unit_reference": "PU-1",
                    "coupon_status": "open_for_use",
                    "not_valid_before": "2028-02-05",
                    "not_valid_after": "2028-02-06",
                    "baggage_summary": "One checked bag.",
                    "remarks": "Metadata-only coupon detail.",
                }
            ],
            "baggage_summary": "One checked bag.",
            "endorsement_summary": "Non-endorsable metadata only.",
            "restrictions_summary": "Manual restrictions metadata.",
            "exchange_reference_ids": ["exchange-smoke"],
            "refund_reference_ids": ["refund-smoke"],
            "void_reference_ids": ["void-smoke"],
            "linked_emd_ids": ["emd-smoke"],
            "linked_document_ids": ["document-smoke"],
            "lifecycle_notes": "Ticket document lifecycle metadata only.",
            "operational_notes": "Metadata-only ticket notes.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    if created.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected create phase: {created.get('phase')}")
    assert_disabled_response(created)
    ticket = created.get("ticket_workspace") or {}
    assert_ticket_shape(ticket)
    ticket_workspace_id = ticket.get("id")
    if not ticket_workspace_id:
        raise AssertionError(f"Ticket workspace id missing: {created}")

    updated = put(
        f"/api/platform/ticket-workspaces/{ticket_workspace_id}",
        {
            "ticket_status": "ready",
            "ticket_document_status": "partially_refunded",
            "coupon_status_summary": "Coupon 1 remains open for use in metadata only.",
            "fare_calculation_roe": 0.924,
            "fare_construction_notes": "Updated fare construction metadata only.",
            "operational_notes": "Updated metadata only; no ticket issuance.",
            "lifecycle_notes": "Updated lifecycle metadata only.",
            "metadata": {"updated": True, "metadata_only": True},
        },
        OWNER_HEADERS,
    )
    assert_disabled_response(updated)
    updated_ticket = updated.get("ticket_workspace") or {}
    assert_ticket_shape(updated_ticket)
    if updated_ticket.get("ticket_status") != "ready":
        raise AssertionError(f"Ticket workspace update did not persist metadata: {updated}")
    if updated_ticket.get("ticket_document_status") != "partially_refunded":
        raise AssertionError(f"Ticket document status update did not persist metadata: {updated}")
    if updated_ticket.get("fare_calculation_roe") != 0.924:
        raise AssertionError(f"Ticket fare calculation metadata update did not persist: {updated}")

    for filter_query in [
        f"agency_id={agency_id}",
        "status=ready",
        "document_status=partially_refunded",
        "validating_carrier=LH",
        "issue_date=2028-02-05",
        f"passenger={passenger_id}",
        f"booking_reference={booking_reference}",
        "currency=EUR",
    ]:
        filtered = get(f"/api/platform/ticket-workspaces?{filter_query}", OWNER_HEADERS)
        assert_disabled_response(filtered)
        if not any(item.get("id") == ticket_workspace_id for item in filtered.get("items") or []):
            raise AssertionError(f"Ticket workspace filter {filter_query} missing created record: {filtered}")

    platform_summary = get("/api/platform/ticket-workspaces/summary", OWNER_HEADERS)
    assert_summary_shape(platform_summary)

    platform_detail = get(f"/api/platform/ticket-workspaces/{ticket_workspace_id}", OWNER_HEADERS)
    assert_disabled_response(platform_detail)
    assert_ticket_shape(platform_detail.get("ticket_workspace") or {})

    agency_list = get(f"/api/agencies/{agency_id}/ticket-workspaces?status=ready&document_status=partially_refunded&validating_carrier=LH", OWNER_HEADERS)
    assert_disabled_response(agency_list)
    if agency_list.get("read_only") is not True:
        raise AssertionError(f"Agency ticket workspace list should be read-only: {agency_list}")
    agency_item = next((item for item in agency_list.get("items") or [] if item.get("id") == ticket_workspace_id), None)
    if not agency_item:
        raise AssertionError(f"Agency ticket workspace list missing created record: {agency_list}")
    assert_ticket_shape(agency_item, agency_view=True)

    agency_summary = get(f"/api/agencies/{agency_id}/ticket-workspaces/summary", OWNER_HEADERS)
    assert_summary_shape(agency_summary, agency_id=agency_id)
    if agency_summary.get("read_only") is not True:
        raise AssertionError(f"Agency ticket workspace summary should be read-only: {agency_summary}")

    agency_detail = get(f"/api/agencies/{agency_id}/ticket-workspaces/{ticket_workspace_id}", OWNER_HEADERS)
    assert_disabled_response(agency_detail)
    if agency_detail.get("read_only") is not True:
        raise AssertionError(f"Agency ticket workspace detail should be read-only: {agency_detail}")
    assert_ticket_shape(agency_detail.get("ticket_workspace") or {}, agency_view=True)

    deleted = request("DELETE", f"/api/platform/ticket-workspaces/{ticket_workspace_id}", {}, OWNER_HEADERS)[1]
    assert_disabled_response(deleted)
    if deleted.get("archived") is not True or (deleted.get("ticket_workspace") or {}).get("ticket_status") != "archived":
        raise AssertionError(f"Ticket workspace delete should be metadata-only archive: {deleted}")

    after_delete = get(f"/api/platform/ticket-workspaces?agency_id={agency_id}", OWNER_HEADERS)
    if any(item.get("id") == ticket_workspace_id for item in after_delete.get("items") or []):
        raise AssertionError(f"Default ticket workspace list should exclude archived-delete metadata: {after_delete}")
    include_archived = get(f"/api/platform/ticket-workspaces?agency_id={agency_id}&include_archived=true", OWNER_HEADERS)
    if not any(item.get("id") == ticket_workspace_id for item in include_archived.get("items") or []):
        raise AssertionError(f"include_archived should expose metadata-archived ticket workspace: {include_archived}")

    request("POST", f"/api/agencies/{agency_id}/ticket-workspaces", {"ticket_number": "blocked"}, OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/ticket-workspaces/{ticket_workspace_id}", {"ticket_status": "ready"}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/ticket-workspaces/{ticket_workspace_id}", {}, OWNER_HEADERS, 405)


def create_booking_workspace(
    agency_id: str,
    operational_workspace_id: str,
    trip_workspace_id: str,
    offer_workspace_id: str,
    passenger_id: str,
    flight_id: str,
) -> dict:
    created = post(
        "/api/platform/booking-workspaces",
        {
            "agency_id": agency_id,
            "operational_workspace_id": operational_workspace_id,
            "trip_workspace_id": trip_workspace_id,
            "offer_workspace_id": offer_workspace_id,
            "booking_status": "ready_to_book",
            "booking_type": "flight_booking",
            "booking_source": "manual_metadata",
            "booking_owner": "Taylor Ticket",
            "airline_pnr": "LHABC1",
            "gds_record_locator": "GDSABC",
            "supplier_reference": "SUP-TICKET-1",
            "booking_created_date": "2028-02-01",
            "booking_deadline": "2028-02-20",
            "passenger_ids": [passenger_id],
            "flight_workspace_ids": [flight_id],
            "ticket_ids": ["ticket-smoke"],
            "emd_ids": ["emd-smoke"],
            "document_ids": ["document-smoke"],
            "payment_summary": "Payment metadata only.",
            "booking_summary": "Metadata-only booking for ticket workspace smoke.",
            "operational_notes": "Metadata-only booking notes for ticket workspace smoke.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    booking_workspace = created.get("booking_workspace") or {}
    if not booking_workspace.get("id"):
        raise AssertionError(f"Booking workspace id missing for ticket smoke: {created}")
    return booking_workspace


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
        "by_validating_carrier",
        "by_currency",
        "agency_count",
        "operational_workspace_count",
        "trip_workspace_count",
        "offer_workspace_count",
        "booking_workspace_count",
        "passenger_count",
        "flight_workspace_count",
        "linked_emd_count",
        "linked_document_count",
        "coupon_detail_count",
        "pricing_unit_count",
        "fare_component_count",
        "tax_breakdown_count",
        "exchange_reference_count",
        "refund_reference_count",
        "void_reference_count",
        "fare_amount_total",
        "taxes_amount_total",
        "total_amount_total",
        "fare_calculation_nuc_total",
        "equivalent_fare_paid_total",
    ]:
        if key not in summary:
            raise AssertionError(f"Ticket workspace summary missing {key}: {payload}")
    if not TICKET_STATUSES.issubset(set((summary.get("by_status") or {}).keys())):
        raise AssertionError(f"Ticket workspace summary missing status buckets: {summary}")
    if not TICKET_DOCUMENT_STATUSES.issubset(set((summary.get("by_document_status") or {}).keys())):
        raise AssertionError(f"Ticket workspace summary missing document status buckets: {summary}")
    if not TICKET_COUPON_STATUSES.issubset(set((summary.get("by_coupon_status") or {}).keys())):
        raise AssertionError(f"Ticket workspace summary missing coupon status buckets: {summary}")


def assert_ticket_shape(ticket: dict, agency_view: bool = False) -> None:
    required_keys = [
        "id",
        "agency_id",
        "operational_workspace_id",
        "trip_workspace_id",
        "offer_workspace_id",
        "booking_workspace_id",
        "ticket_reference",
        "ticket_status",
        "ticket_document_status",
        "ticket_type",
        "ticket_number",
        "validating_carrier",
        "issuing_agent",
        "issuing_office",
        "issue_date",
        "passenger_id",
        "passenger_name",
        "flight_workspace_ids",
        "booking_reference",
        "airline_pnr",
        "gds_record_locator",
        "fare_basis_summary",
        "fare_amount",
        "taxes_amount",
        "total_amount",
        "currency",
        "fare_calculation_line",
        "fare_calculation_currency",
        "fare_calculation_nuc_total",
        "fare_calculation_roe",
        "equivalent_fare_paid",
        "equivalent_fare_currency",
        "form_of_payment",
        "payment_reference",
        "payment_restrictions",
        "commission_summary",
        "tax_breakdown",
        "fare_construction_notes",
        "pricing_units",
        "fare_components",
        "coupon_summary",
        "coupon_status_summary",
        "coupon_details",
        "baggage_summary",
        "endorsement_summary",
        "restrictions_summary",
        "exchange_reference_ids",
        "refund_reference_ids",
        "void_reference_ids",
        "linked_emd_ids",
        "linked_document_ids",
        "lifecycle_notes",
        "operational_notes",
        "ticket_display_name",
        "agency",
        "operational_workspace",
        "trip_workspace",
        "offer_workspace",
        "booking_workspace",
        "passenger",
        "flight_workspaces",
        "linked_emds",
        "linked_documents",
        "metadata_only",
        "ticket_workspace_metadata_only",
    ]
    for key in required_keys:
        if key not in ticket:
            raise AssertionError(f"Ticket workspace missing {key}: {ticket}")
    coupon = (ticket.get("coupon_details") or [{}])[0]
    for key in ["marketing_carrier", "operating_carrier", "fare_basis", "fare_component_reference", "pricing_unit_reference"]:
        if key not in coupon:
            raise AssertionError(f"Ticket coupon detail missing {key}: {ticket}")
    pricing_unit = (ticket.get("pricing_units") or [{}])[0]
    for key in ["pricing_unit_reference", "pricing_unit_type", "fare_component_references", "nuc_amount"]:
        if key not in pricing_unit:
            raise AssertionError(f"Ticket pricing unit missing {key}: {ticket}")
    fare_component = (ticket.get("fare_components") or [{}])[0]
    for key in ["fare_component_reference", "fare_basis", "booking_class", "nuc_amount", "rule_reference"]:
        if key not in fare_component:
            raise AssertionError(f"Ticket fare component missing {key}: {ticket}")
    if agency_view and ticket.get("read_only") is not True:
        raise AssertionError(f"Agency ticket workspace item should be read-only: {ticket}")
    for flag in disabled_flags():
        if ticket.get(flag) is not True:
            raise AssertionError(f"Ticket workspace missing disabled flag {flag}: {ticket}")


def main() -> None:
    verify_model_and_collection_registration()
    openapi = get("/openapi.json")
    verify_routes(openapi.get("paths", {}))
    verify_frontend_and_docs()
    verify_readiness()
    verify_endpoint_behavior()
    print("Feature bundle ticket workspace foundation smoke passed.")


if __name__ == "__main__":
    main()
