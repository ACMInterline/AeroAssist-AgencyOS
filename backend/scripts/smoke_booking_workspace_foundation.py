#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import BookingWorkspace, BookingWorkspaceMetadataCreate, BookingWorkspaceStatus
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_54_6_offer_to_booking_handoff_readiness_foundation"
ROOT = Path(__file__).resolve().parents[2]
BOOKING_STATUSES = {"draft", "ready_to_book", "booking_in_progress", "booked", "blocked", "cancelled"}


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
        "booking_execution_disabled",
        "live_booking_creation_disabled",
        "ticket_issuance_disabled",
        "gds_connectivity_disabled",
        "ndc_connectivity_disabled",
        "airline_apis_disabled",
        "airline_api_calls_disabled",
        "payment_processing_disabled",
        "fare_calculation_disabled",
        "ai_disabled",
        "background_workers_disabled",
        "automatic_booking_confirmation_disabled",
        "automatic_ticket_generation_disabled",
        "external_integrations_disabled",
        "external_api_calls_disabled",
        "automation_disabled",
    ]


def forbidden_enabled_flags() -> list[str]:
    return [
        "booking_execution_enabled",
        "live_booking_creation_enabled",
        "ticket_issuance_enabled",
        "gds_connectivity_enabled",
        "ndc_connectivity_enabled",
        "airline_apis_enabled",
        "airline_api_calls_enabled",
        "payment_processing_enabled",
        "fare_calculation_enabled",
        "ai_enabled",
        "background_workers_enabled",
        "automatic_booking_confirmation_enabled",
        "automatic_ticket_generation_enabled",
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
    create_payload = BookingWorkspaceMetadataCreate(
        agency_id="agency-smoke",
        operational_workspace_id="workspace-smoke",
        trip_workspace_id="trip-smoke",
        offer_workspace_id="offer-smoke",
        booking_reference="BKGW-SMOKE-MODEL",
        booking_status=BookingWorkspaceStatus.READY_TO_BOOK,
        booking_type="flight_booking",
        booking_source="manual_metadata",
        booking_owner="Taylor Booking",
        airline_pnr="LHABC1",
        gds_record_locator="GDSABC",
        supplier_reference="SUP-BOOK-1",
        booking_created_date="2028-01-05",
        booking_deadline="2028-01-20",
        passenger_ids=["passenger-smoke"],
        flight_workspace_ids=["flight-smoke"],
        ticket_ids=["ticket-smoke"],
        emd_ids=["emd-smoke"],
        ssr_ids=["ssr-smoke"],
        osi_ids=["osi-smoke"],
        document_ids=["document-smoke"],
        timeline_ids=["timeline-smoke"],
        communication_ids=["communication-smoke"],
        payment_summary="Payment metadata only.",
        booking_summary="Booking summary metadata only.",
        operational_notes="Operational notes metadata only.",
        metadata={"smoke": True},
    )
    booking_workspace = BookingWorkspace(
        **create_payload.model_dump(mode="json", exclude_none=True),
        workspace_number=create_payload.booking_reference,
        title="Phase 41.6 booking smoke model",
        status=BookingWorkspaceStatus.READY_TO_BOOK,
    )
    dumped = booking_workspace.model_dump(mode="json")
    if dumped.get("booking_status") != "ready_to_book" or dumped.get("airline_pnr") != "LHABC1":
        raise AssertionError(f"Booking workspace dimensions were not preserved: {dumped}")
    for key in ["metadata_only", "booking_workspace_metadata_only", *disabled_flags()]:
        if dumped.get(key) is not True:
            raise AssertionError(f"Booking workspace model missing disabled flag {key}: {dumped}")
    if "booking_workspaces" not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("Booking workspaces collection is not registered.")
    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "booking_workspaces_operational_workspace_lookup",
        "booking_workspaces_trip_workspace_lookup",
        "booking_workspaces_offer_workspace_lookup",
        "booking_workspaces_reference_lookup",
        "booking_workspaces_booking_status_lookup",
        "booking_workspaces_booking_owner_lookup",
        "booking_workspaces_airline_pnr_lookup",
        "booking_workspaces_gds_locator_lookup",
        "booking_workspaces_supplier_reference_lookup",
        "booking_workspaces_booking_created_date_lookup",
        "booking_workspaces_booking_deadline_lookup",
        "booking_workspaces_flight_workspace_lookup",
        "booking_workspaces_ticket_lookup",
        "booking_workspaces_emd_lookup",
        "booking_workspaces_ssr_lookup",
        "booking_workspaces_osi_lookup",
        "booking_workspaces_document_lookup",
        "booking_workspaces_timeline_lookup",
        "booking_workspaces_communication_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Booking workspace index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    expected_methods = {
        "/api/platform/booking-workspaces": {"get", "post"},
        "/api/platform/booking-workspaces/summary": {"get"},
        "/api/platform/booking-workspaces/{booking_workspace_id}": {"get", "put", "delete"},
        "/api/agencies/{agency_id}/booking-workspaces": {"get"},
        "/api/agencies/{agency_id}/booking-workspaces/summary": {"get"},
        "/api/agencies/{agency_id}/booking-workspaces/{booking_workspace_id}": {"get"},
    }
    for path, methods in expected_methods.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in [
        "/api/agencies/{agency_id}/booking-workspaces",
        "/api/agencies/{agency_id}/booking-workspaces/summary",
        "/api/agencies/{agency_id}/booking-workspaces/{booking_workspace_id}",
    ]:
        methods = set(paths.get(path, {}).keys())
        blocked_methods = methods & {"post", "put", "patch", "delete"}
        if blocked_methods:
            raise AssertionError(f"Agency booking workspace metadata route is not read-only: {path} {sorted(blocked_methods)}")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Booking Workspaces"),
        (ROOT / "frontend/src/App.jsx", "/platform/booking-workspaces"),
        (ROOT / "frontend/src/App.jsx", "/agency/booking-workspaces"),
        (ROOT / "frontend/src/pages/platform/BookingWorkspacesPage.jsx", "Booking Workspaces"),
        (ROOT / "frontend/src/pages/platform/BookingWorkspacesPage.jsx", "No GDS or NDC"),
        (ROOT / "frontend/src/pages/platform/BookingWorkspacesPage.jsx", "Airline PNR"),
        (ROOT / "frontend/src/pages/agency/BookingWorkspaceMetadataPage.jsx", "Bookings"),
        (ROOT / "frontend/src/pages/agency/BookingWorkspaceMetadataPage.jsx", "Read-only booking workspace metadata"),
        (ROOT / "frontend/src/pages/agency/BookingWorkspaceMetadataPage.jsx", "No ticket issuance"),
        (ROOT / "docs/architecture/booking-workspace-foundation.md", "Booking Workspace Foundation"),
        (ROOT / "README.md", "Phase 41.6 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 41.6: Booking Workspace Foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "Phase 41.6 adds booking workspace metadata"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "Phase 41.6 adds booking workspace APIs"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Booking workspaces"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Booking workspaces"),
        (ROOT / "backend/services/blueprint_adoption_service.py", "Booking Workspaces"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/BookingWorkspacesPage.jsx",
        ROOT / "frontend/src/pages/agency/BookingWorkspaceMetadataPage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)
    for path in [
        ROOT / "frontend/src/pages/platform/BookingWorkspacesPage.jsx",
        ROOT / "frontend/src/pages/agency/BookingWorkspaceMetadataPage.jsx",
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
    section = readiness.get("booking_workspace_foundation") or {}
    for flag in [
        "booking_workspaces_enabled",
        "booking_workspace_metadata_enabled",
        "platform_booking_workspace_metadata_crud_enabled",
        "agency_booking_workspace_read_only_enabled",
        "booking_workspace_filter_by_status_enabled",
        "booking_workspace_filter_by_owner_enabled",
        "booking_workspace_filter_by_airline_enabled",
        "booking_workspace_filter_by_supplier_enabled",
        "booking_workspace_filter_by_booking_date_enabled",
        "booking_reference_metadata_enabled",
        "booking_status_metadata_enabled",
        "booking_type_metadata_enabled",
        "booking_source_metadata_enabled",
        "booking_owner_metadata_enabled",
        "airline_pnr_metadata_enabled",
        "gds_record_locator_metadata_enabled",
        "supplier_reference_metadata_enabled",
        "passenger_summary_metadata_enabled",
        "flight_summary_metadata_enabled",
        "trip_summary_metadata_enabled",
        "offer_summary_metadata_enabled",
        "ticket_link_metadata_enabled",
        "emd_link_metadata_enabled",
        "ssr_link_metadata_enabled",
        "osi_link_metadata_enabled",
        "document_link_metadata_enabled",
        "timeline_link_metadata_enabled",
        "communication_link_metadata_enabled",
        "payment_summary_metadata_enabled",
        "booking_summary_metadata_enabled",
        "operational_notes_metadata_enabled",
        "read_only_ui_enabled",
        "metadata_only",
        "booking_workspace_metadata_only",
    ]:
        require_flag(section, flag)
    for flag in disabled_flags():
        require_flag(section, flag)
    require_flag(section, "readiness_required", False)
    for count_key in [
        "booking_workspace_count",
        "booking_workspace_status_counts",
        "booking_workspace_owner_count",
        "booking_workspace_supplier_count",
        "booking_workspace_airline_count",
        "booking_workspace_operational_workspace_count",
        "booking_workspace_trip_workspace_count",
        "booking_workspace_offer_workspace_count",
    ]:
        if count_key not in section:
            raise AssertionError(f"Booking workspace readiness missing count: {count_key}")
    if not BOOKING_STATUSES.issubset(set((section.get("booking_workspace_status_counts") or {}).keys())):
        raise AssertionError(f"Booking workspace readiness status counts missing statuses: {section}")
    previous_section = readiness.get("offer_workspace_foundation") or {}
    if previous_section.get("metadata_only") is not True:
        raise AssertionError("Previous offer workspace section should remain metadata-only.")


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

    created = post(
        "/api/platform/booking-workspaces",
        {
            "agency_id": agency_id,
            "operational_workspace_id": operational_workspace_id,
            "trip_workspace_id": trip_workspace_id,
            "offer_workspace_id": offer_workspace_id,
            "booking_status": "draft",
            "booking_type": "flight_booking",
            "booking_source": "manual_metadata",
            "booking_owner": "Taylor Booking",
            "airline_pnr": "LHABC1",
            "gds_record_locator": "GDSABC",
            "supplier_reference": "SUP-BOOK-1",
            "booking_created_date": "2028-01-05",
            "booking_deadline": "2028-01-20",
            "passenger_ids": [passenger_id],
            "flight_workspace_ids": [flight_id],
            "ticket_ids": ["ticket-smoke"],
            "emd_ids": ["emd-smoke"],
            "ssr_ids": ["ssr-smoke"],
            "osi_ids": ["osi-smoke"],
            "document_ids": ["document-smoke"],
            "timeline_ids": ["timeline-smoke"],
            "communication_ids": ["communication-smoke"],
            "payment_summary": "Payment metadata only.",
            "booking_summary": "Metadata-only LH booking workspace.",
            "operational_notes": "Metadata-only booking notes.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    if created.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected create phase: {created.get('phase')}")
    assert_disabled_response(created)
    booking_workspace = created.get("booking_workspace") or {}
    assert_booking_shape(booking_workspace)
    booking_workspace_id = booking_workspace.get("id")
    if not booking_workspace_id:
        raise AssertionError(f"Booking workspace id missing: {created}")

    updated = put(
        f"/api/platform/booking-workspaces/{booking_workspace_id}",
        {
            "booking_status": "ready_to_book",
            "booking_summary": "Metadata-only LH booking workspace reviewed.",
            "operational_notes": "Updated metadata only; no booking confirmation.",
            "metadata": {"updated": True, "metadata_only": True},
        },
        OWNER_HEADERS,
    )
    assert_disabled_response(updated)
    updated_booking = updated.get("booking_workspace") or {}
    assert_booking_shape(updated_booking)
    if updated_booking.get("booking_status") != "ready_to_book":
        raise AssertionError(f"Booking workspace update did not persist metadata: {updated}")

    for filter_query in [
        f"agency_id={agency_id}",
        "status=ready_to_book",
        "booking_owner=Taylor%20Booking",
        "airline=LHABC1",
        "supplier=SUP-BOOK-1",
        "booking_date=2028-01-05",
    ]:
        filtered = get(f"/api/platform/booking-workspaces?{filter_query}", OWNER_HEADERS)
        assert_disabled_response(filtered)
        if not any(item.get("id") == booking_workspace_id for item in filtered.get("items") or []):
            raise AssertionError(f"Booking workspace filter {filter_query} missing created record: {filtered}")

    platform_summary = get("/api/platform/booking-workspaces/summary", OWNER_HEADERS)
    assert_summary_shape(platform_summary)

    platform_detail = get(f"/api/platform/booking-workspaces/{booking_workspace_id}", OWNER_HEADERS)
    assert_disabled_response(platform_detail)
    assert_booking_shape(platform_detail.get("booking_workspace") or {})

    agency_list = get(f"/api/agencies/{agency_id}/booking-workspaces?status=ready_to_book&airline=LHABC1", OWNER_HEADERS)
    assert_disabled_response(agency_list)
    if agency_list.get("read_only") is not True:
        raise AssertionError(f"Agency booking workspace list should be read-only: {agency_list}")
    agency_item = next((item for item in agency_list.get("items") or [] if item.get("id") == booking_workspace_id), None)
    if not agency_item:
        raise AssertionError(f"Agency booking workspace list missing created record: {agency_list}")
    assert_booking_shape(agency_item, agency_view=True)

    agency_summary = get(f"/api/agencies/{agency_id}/booking-workspaces/summary", OWNER_HEADERS)
    assert_summary_shape(agency_summary, agency_id=agency_id)
    if agency_summary.get("read_only") is not True:
        raise AssertionError(f"Agency booking workspace summary should be read-only: {agency_summary}")

    agency_detail = get(f"/api/agencies/{agency_id}/booking-workspaces/{booking_workspace_id}", OWNER_HEADERS)
    assert_disabled_response(agency_detail)
    if agency_detail.get("read_only") is not True:
        raise AssertionError(f"Agency booking workspace detail should be read-only: {agency_detail}")
    assert_booking_shape(agency_detail.get("booking_workspace") or {}, agency_view=True)

    deleted = request("DELETE", f"/api/platform/booking-workspaces/{booking_workspace_id}", {}, OWNER_HEADERS)[1]
    assert_disabled_response(deleted)
    if deleted.get("deleted") is not True or (deleted.get("booking_workspace") or {}).get("booking_status") != "cancelled":
        raise AssertionError(f"Booking workspace delete should be metadata-only archive: {deleted}")

    after_delete = get(f"/api/platform/booking-workspaces?agency_id={agency_id}", OWNER_HEADERS)
    if any(item.get("id") == booking_workspace_id for item in after_delete.get("items") or []):
        raise AssertionError(f"Default booking workspace list should exclude archived-delete metadata: {after_delete}")
    include_archived = get(f"/api/platform/booking-workspaces?agency_id={agency_id}&include_archived=true", OWNER_HEADERS)
    if not any(item.get("id") == booking_workspace_id for item in include_archived.get("items") or []):
        raise AssertionError(f"include_archived should expose metadata-archived booking workspace: {include_archived}")

    request("POST", f"/api/agencies/{agency_id}/booking-workspaces", {"booking_summary": "blocked"}, OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/booking-workspaces/{booking_workspace_id}", {"booking_status": "ready_to_book"}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/booking-workspaces/{booking_workspace_id}", {}, OWNER_HEADERS, 405)


def create_operational_workspace(agency_id: str) -> str:
    created = post(
        "/api/platform/operational-travel-workspaces",
        {
            "agency_id": agency_id,
            "workspace_title": "Phase 41.6 parent operational workspace smoke",
            "workspace_type": "booking",
            "workspace_status": "open",
            "priority": "high",
            "assigned_team": ["booking-ops"],
            "assigned_agent": "Taylor Booking",
            "travel_start_date": "2028-01-05",
            "travel_end_date": "2028-01-20",
            "origin_summary": "SOF",
            "destination_summary": "FRA",
            "service_summary": "Booking workspace parent metadata",
            "operational_notes": "Metadata-only parent workspace for booking smoke.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    workspace_id = (created.get("workspace") or {}).get("id")
    if not workspace_id:
        raise AssertionError(f"Parent operational workspace id missing: {created}")
    return workspace_id


def create_passenger_workspace(agency_id: str, operational_workspace_id: str) -> str:
    created = post(
        "/api/platform/passenger-workspaces",
        {
            "agency_id": agency_id,
            "operational_workspace_id": operational_workspace_id,
            "passenger_status": "active",
            "first_name": "Booking",
            "last_name": "Passenger",
            "nationality": "BG",
            "citizenship": "BG",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    return (created.get("passenger_workspace") or {}).get("id") or "passenger-smoke"


def create_flight_workspace(agency_id: str, operational_workspace_id: str, passenger_id: str) -> str:
    created = post(
        "/api/platform/flight-workspaces",
        {
            "agency_id": agency_id,
            "operational_workspace_id": operational_workspace_id,
            "flight_status": "active",
            "flight_type": "scheduled",
            "travel_direction": "outbound",
            "airline_code": "LH",
            "airline_name": "Lufthansa",
            "marketing_carrier": "LH",
            "operating_carrier": "LH",
            "flight_number": "1703",
            "operating_flight_number": "1703",
            "departure_airport": "SOF",
            "arrival_airport": "FRA",
            "departure_datetime": "2028-01-05T06:00:00Z",
            "arrival_datetime": "2028-01-05T07:25:00Z",
            "aircraft_type": "A320",
            "cabin_class": "economy",
            "booking_class": "Y",
            "fare_family": "Economy Flex",
            "passenger_ids": [passenger_id],
            "linked_booking_ids": ["booking-smoke"],
            "linked_document_ids": ["document-smoke"],
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    return (created.get("flight_workspace") or {}).get("id") or "flight-smoke"


def create_trip_workspace(agency_id: str, operational_workspace_id: str, passenger_id: str, flight_id: str) -> str:
    created = post(
        "/api/platform/trip-workspaces",
        {
            "agency_id": agency_id,
            "operational_workspace_id": operational_workspace_id,
            "trip_status": "ready",
            "journey_type": "round_trip",
            "service_type": "flight",
            "client_id": "client-booking-smoke",
            "passenger_ids": [passenger_id],
            "flight_workspace_ids": [flight_id],
            "offer_ids": ["offer-smoke"],
            "booking_ids": ["booking-smoke"],
            "ticket_ids": ["ticket-smoke"],
            "emd_ids": ["emd-smoke"],
            "document_ids": ["document-smoke"],
            "departure_country": "BG",
            "destination_country": "DE",
            "departure_city": "Sofia",
            "destination_city": "Frankfurt",
            "origin_airport": "SOF",
            "destination_airport": "FRA",
            "departure_date": "2028-01-05",
            "return_date": "2028-01-20",
            "travel_duration": "15 days",
            "passenger_count": 1,
            "itinerary_summary": "SOF-FRA-SOF metadata only",
            "baggage_summary": "1 checked bag",
            "service_summary": "Flight-only journey",
            "operational_priority": "high",
            "assigned_agent": "Taylor Booking",
            "assigned_team": ["booking-ops"],
            "operational_notes": "Metadata-only trip workspace for booking smoke.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    trip_workspace_id = (created.get("trip_workspace") or {}).get("id")
    if not trip_workspace_id:
        raise AssertionError(f"Trip workspace id missing: {created}")
    return trip_workspace_id


def create_offer_workspace(
    agency_id: str,
    operational_workspace_id: str,
    trip_workspace_id: str,
    passenger_id: str,
    flight_id: str,
) -> str:
    created = post(
        "/api/platform/offer-workspaces",
        {
            "agency_id": agency_id,
            "operational_workspace_id": operational_workspace_id,
            "trip_workspace_id": trip_workspace_id,
            "offer_status": "ready",
            "offer_type": "flight_package",
            "client_id": "client-booking-smoke",
            "passenger_ids": [passenger_id],
            "flight_workspace_ids": [flight_id],
            "offer_title": "Phase 41.6 linked offer smoke",
            "offer_summary": "Metadata-only offer linked to booking smoke.",
            "destination_summary": "Frankfurt",
            "itinerary_summary": "SOF-FRA-SOF offer metadata only.",
            "pricing_summary": "Manual price summary only.",
            "currency": "EUR",
            "total_price": 1250.0,
            "taxes_summary": "Taxes metadata only.",
            "fees_summary": "Fees metadata only.",
            "ancillary_summary": "Ancillary metadata only.",
            "baggage_summary": "1 checked bag.",
            "seat_summary": "Standard seats.",
            "meal_summary": "Standard meals.",
            "validity_date": "2028-01-10",
            "assigned_agent": "Taylor Booking",
            "linked_booking_ids": ["booking-smoke"],
            "linked_ticket_ids": ["ticket-smoke"],
            "linked_document_ids": ["document-smoke"],
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    offer_workspace_id = (created.get("offer_workspace") or {}).get("id")
    if not offer_workspace_id:
        raise AssertionError(f"Offer workspace id missing: {created}")
    return offer_workspace_id


def assert_booking_shape(booking_workspace: dict, *, agency_view: bool = False) -> None:
    for key in [
        "id",
        "agency_id",
        "operational_workspace_id",
        "trip_workspace_id",
        "offer_workspace_id",
        "booking_reference",
        "booking_status",
        "booking_type",
        "booking_source",
        "booking_owner",
        "airline_pnr",
        "gds_record_locator",
        "supplier_reference",
        "booking_created_date",
        "booking_deadline",
        "passenger_ids",
        "flight_workspace_ids",
        "ticket_ids",
        "emd_ids",
        "ssr_ids",
        "osi_ids",
        "document_ids",
        "timeline_ids",
        "communication_ids",
        "payment_summary",
        "booking_summary",
        "operational_notes",
        "agency",
        "operational_workspace",
        "trip_workspace",
        "offer_workspace",
        "passengers",
        "flight_workspaces",
        "tickets",
        "emds",
        "ssrs",
        "osis",
        "documents",
        "timeline",
        "communications",
        "booking_display_name",
    ]:
        if key not in booking_workspace:
            raise AssertionError(f"Booking workspace missing {key}: {booking_workspace}")
    if booking_workspace.get("metadata_only") is not True or booking_workspace.get("booking_workspace_metadata_only") is not True:
        raise AssertionError(f"Booking workspace should be metadata-only: {booking_workspace}")
    for flag in disabled_flags():
        if booking_workspace.get(flag) is not True:
            raise AssertionError(f"Booking workspace missing disabled flag {flag}: {booking_workspace}")
    if agency_view and booking_workspace.get("read_only") is not True:
        raise AssertionError(f"Agency booking workspace should be read-only: {booking_workspace}")
    if not booking_workspace.get("passengers") or not booking_workspace.get("flight_workspaces"):
        raise AssertionError(f"Booking workspace missing linked passenger/flight context: {booking_workspace}")
    for linked_key in ["tickets", "emds", "ssrs", "osis", "documents", "timeline", "communications"]:
        if not booking_workspace.get(linked_key):
            raise AssertionError(f"Booking workspace missing linked {linked_key}: {booking_workspace}")


def assert_summary_shape(payload: dict, *, agency_id: str | None = None) -> None:
    assert_disabled_response(payload)
    summary = payload.get("summary") or {}
    for key in [
        "total_count",
        "by_status",
        "by_type",
        "by_source",
        "by_supplier",
        "agency_count",
        "booking_owner_count",
        "airline_count",
        "operational_workspace_count",
        "trip_workspace_count",
        "offer_workspace_count",
        "passenger_count",
        "flight_workspace_count",
        "ticket_count",
        "emd_count",
        "ssr_count",
        "osi_count",
        "document_count",
        "timeline_count",
        "communication_count",
        "metadata_only",
    ]:
        if key not in summary:
            raise AssertionError(f"Booking workspace summary missing {key}: {payload}")
    if not BOOKING_STATUSES.issubset(set((summary.get("by_status") or {}).keys())):
        raise AssertionError(f"Booking workspace summary missing statuses: {summary}")
    if agency_id and payload.get("agency_id") != agency_id:
        raise AssertionError(f"Agency summary should be scoped to {agency_id}: {payload}")


def main() -> int:
    verify_model_and_collection_registration()
    openapi = get("/openapi.json")
    verify_routes(openapi.get("paths") or {})
    verify_frontend_and_docs()
    verify_readiness()
    verify_endpoint_behavior()
    print("Phase 41.6 booking workspace foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Phase 41.6 booking workspace foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
