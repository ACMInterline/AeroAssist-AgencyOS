#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import FlightWorkspace, FlightWorkspaceCreate, FlightWorkspaceStatus
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_54_5_request_to_trip_operational_conversion_foundation"
ROOT = Path(__file__).resolve().parents[2]
FLIGHT_STATUSES = {"draft", "active", "schedule_review", "ready", "flown", "archived"}


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
        "live_flight_search_disabled",
        "flight_search_disabled",
        "gds_connectivity_disabled",
        "ndc_connectivity_disabled",
        "airline_apis_disabled",
        "airline_api_calls_disabled",
        "payment_disabled",
        "payment_processing_disabled",
        "ticket_issuance_disabled",
        "schedule_synchronization_disabled",
        "external_api_calls_disabled",
        "ai_disabled",
        "background_workers_disabled",
        "automatic_route_generation_disabled",
        "flight_validation_disabled",
        "airline_lookups_disabled",
        "live_schedule_updates_disabled",
        "automation_disabled",
    ]


def forbidden_enabled_flags() -> list[str]:
    return [
        "booking_execution_enabled",
        "live_flight_search_enabled",
        "flight_search_enabled",
        "gds_connectivity_enabled",
        "ndc_connectivity_enabled",
        "airline_apis_enabled",
        "airline_api_calls_enabled",
        "payment_enabled",
        "payment_processing_enabled",
        "ticket_issuance_enabled",
        "schedule_synchronization_enabled",
        "external_api_calls_enabled",
        "ai_enabled",
        "background_workers_enabled",
        "automatic_route_generation_enabled",
        "flight_validation_enabled",
        "airline_lookups_enabled",
        "live_schedule_updates_enabled",
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
    create_payload = FlightWorkspaceCreate(
        agency_id="agency-smoke",
        operational_workspace_id="workspace-smoke",
        flight_reference="FLW-SMOKE-MODEL",
        flight_status=FlightWorkspaceStatus.ACTIVE,
        flight_type="scheduled",
        travel_direction="outbound",
        airline_code="LH",
        airline_name="Lufthansa",
        marketing_carrier="LH",
        operating_carrier="LH",
        flight_number="1703",
        operating_flight_number="1703",
        departure_airport="SOF",
        arrival_airport="FRA",
        departure_terminal="2",
        arrival_terminal="1",
        departure_datetime="2027-10-10T06:00:00Z",
        arrival_datetime="2027-10-10T07:25:00Z",
        aircraft_type="A320",
        cabin_class="economy",
        booking_class="Y",
        fare_family="Economy Flex",
        baggage_summary="1 checked bag",
        connection_summary="Nonstop",
        stopover_summary="None",
        elapsed_travel_time="1h 25m",
        operating_days=["monday"],
        passenger_ids=["passenger-smoke"],
        linked_request_ids=["request-smoke"],
        linked_trip_ids=["trip-smoke"],
        linked_offer_ids=["offer-smoke"],
        linked_booking_ids=["booking-smoke"],
        linked_ticket_ids=["ticket-smoke"],
        linked_document_ids=["document-smoke"],
        operational_notes="Metadata-only flight workspace smoke.",
        metadata={"smoke": True},
    )
    flight_workspace = FlightWorkspace(**create_payload.model_dump(mode="json", exclude_none=True))
    dumped = flight_workspace.model_dump(mode="json")
    if dumped.get("flight_status") != "active" or dumped.get("airline_code") != "LH":
        raise AssertionError(f"Flight workspace dimensions were not preserved: {dumped}")
    for key in ["metadata_only", "flight_workspace_metadata_only", *disabled_flags()]:
        if dumped.get(key) is not True:
            raise AssertionError(f"Flight workspace model missing disabled flag {key}: {dumped}")
    if "flight_workspaces" not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("Flight workspaces collection is not registered.")
    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "flight_workspaces_id_unique",
        "flight_workspaces_reference_unique",
        "flight_workspaces_agency_status_lookup",
        "flight_workspaces_agency_airline_lookup",
        "flight_workspaces_agency_departure_lookup",
        "flight_workspaces_agency_arrival_lookup",
        "flight_workspaces_operational_workspace_lookup",
        "flight_workspaces_status_lookup",
        "flight_workspaces_type_lookup",
        "flight_workspaces_airline_code_lookup",
        "flight_workspaces_departure_airport_lookup",
        "flight_workspaces_arrival_airport_lookup",
        "flight_workspaces_departure_datetime_lookup",
        "flight_workspaces_arrival_datetime_lookup",
        "flight_workspaces_cabin_class_lookup",
        "flight_workspaces_booking_class_lookup",
        "flight_workspaces_passenger_lookup",
        "flight_workspaces_request_lookup",
        "flight_workspaces_trip_lookup",
        "flight_workspaces_offer_lookup",
        "flight_workspaces_booking_lookup",
        "flight_workspaces_ticket_lookup",
        "flight_workspaces_document_lookup",
        "flight_workspaces_created_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Flight workspace index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    expected_methods = {
        "/api/platform/flight-workspaces": {"get", "post"},
        "/api/platform/flight-workspaces/summary": {"get"},
        "/api/platform/flight-workspaces/{flight_workspace_id}": {"get", "put", "delete"},
        "/api/agencies/{agency_id}/flight-workspaces": {"get"},
        "/api/agencies/{agency_id}/flight-workspaces/summary": {"get"},
        "/api/agencies/{agency_id}/flight-workspaces/{flight_workspace_id}": {"get"},
    }
    for path, methods in expected_methods.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in [
        "/api/agencies/{agency_id}/flight-workspaces",
        "/api/agencies/{agency_id}/flight-workspaces/summary",
        "/api/agencies/{agency_id}/flight-workspaces/{flight_workspace_id}",
    ]:
        methods = set(paths.get(path, {}).keys())
        blocked_methods = methods & {"post", "put", "patch", "delete"}
        if blocked_methods:
            raise AssertionError(f"Agency flight workspace route is not read-only: {path} {sorted(blocked_methods)}")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Flight Workspaces"),
        (ROOT / "frontend/src/App.jsx", "/platform/flight-workspaces"),
        (ROOT / "frontend/src/App.jsx", "/agency/flight-workspaces"),
        (ROOT / "frontend/src/pages/platform/FlightWorkspacesPage.jsx", "Flight Workspaces"),
        (ROOT / "frontend/src/pages/platform/FlightWorkspacesPage.jsx", "No live search"),
        (ROOT / "frontend/src/pages/platform/FlightWorkspacesPage.jsx", "Marketing carrier"),
        (ROOT / "frontend/src/pages/agency/FlightWorkspacesPage.jsx", "Flights"),
        (ROOT / "frontend/src/pages/agency/FlightWorkspacesPage.jsx", "Read-only flight workspace metadata"),
        (ROOT / "docs/architecture/flight-workspace-foundation.md", "Flight Workspace Foundation"),
        (ROOT / "README.md", "Phase 41.3 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 41.3: Flight Workspace Foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "Phase 41.3 adds flight workspace metadata"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "Phase 41.3 adds flight workspace APIs"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Flight workspaces"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Flight workspaces"),
        (ROOT / "backend/services/blueprint_adoption_service.py", "Flight Workspaces"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/FlightWorkspacesPage.jsx",
        ROOT / "frontend/src/pages/agency/FlightWorkspacesPage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)
    for path in [
        ROOT / "frontend/src/pages/platform/FlightWorkspacesPage.jsx",
        ROOT / "frontend/src/pages/agency/FlightWorkspacesPage.jsx",
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
    section = readiness.get("flight_workspace_foundation") or {}
    for flag in [
        "flight_workspaces_enabled",
        "flight_workspace_metadata_enabled",
        "platform_flight_workspace_metadata_crud_enabled",
        "agency_flight_workspace_read_only_enabled",
        "flight_workspace_filter_by_status_enabled",
        "flight_workspace_filter_by_airline_enabled",
        "flight_workspace_filter_by_departure_airport_enabled",
        "flight_workspace_filter_by_arrival_airport_enabled",
        "flight_workspace_filter_by_departure_date_enabled",
        "flight_workspace_filter_by_cabin_enabled",
        "flight_workspace_filter_by_booking_class_enabled",
        "flight_workspace_filter_by_operational_workspace_enabled",
        "flight_reference_metadata_enabled",
        "airline_metadata_enabled",
        "marketing_carrier_metadata_enabled",
        "operating_carrier_metadata_enabled",
        "flight_number_metadata_enabled",
        "departure_airport_metadata_enabled",
        "arrival_airport_metadata_enabled",
        "terminal_metadata_enabled",
        "schedule_metadata_enabled",
        "aircraft_metadata_enabled",
        "cabin_class_metadata_enabled",
        "booking_class_metadata_enabled",
        "fare_family_metadata_enabled",
        "baggage_summary_metadata_enabled",
        "connection_summary_metadata_enabled",
        "stopover_summary_metadata_enabled",
        "passenger_link_metadata_enabled",
        "linked_request_metadata_enabled",
        "linked_trip_metadata_enabled",
        "linked_offer_metadata_enabled",
        "linked_booking_metadata_enabled",
        "linked_ticket_metadata_enabled",
        "linked_document_metadata_enabled",
        "operational_notes_metadata_enabled",
        "read_only_ui_enabled",
        "metadata_only",
        "flight_workspace_metadata_only",
    ]:
        require_flag(section, flag)
    for flag in disabled_flags():
        require_flag(section, flag)
    require_flag(section, "readiness_required", False)
    for count_key in [
        "flight_workspace_count",
        "flight_workspace_status_counts",
        "flight_workspace_airline_count",
        "flight_workspace_departure_airport_count",
        "flight_workspace_arrival_airport_count",
        "flight_workspace_cabin_count",
    ]:
        if count_key not in section:
            raise AssertionError(f"Flight workspace readiness missing count: {count_key}")
    if not FLIGHT_STATUSES.issubset(set((section.get("flight_workspace_status_counts") or {}).keys())):
        raise AssertionError(f"Flight workspace readiness status counts missing statuses: {section}")
    previous_section = readiness.get("passenger_workspace_foundation") or {}
    if previous_section.get("metadata_only") is not True:
        raise AssertionError("Previous passenger workspace section should remain metadata-only.")


def verify_endpoint_behavior() -> None:
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires seeded demo agency.")
    agency_id = agencies[0]["id"]

    workspace_created = post(
        "/api/platform/operational-travel-workspaces",
        {
            "agency_id": agency_id,
            "workspace_title": "Phase 41.3 parent operational workspace smoke",
            "workspace_type": "trip",
            "workspace_status": "open",
            "priority": "high",
            "assigned_team": ["flight-ops"],
            "assigned_agent": "Flynn Flight",
            "travel_start_date": "2027-10-10",
            "travel_end_date": "2027-10-20",
            "origin_summary": "SOF",
            "destination_summary": "FRA",
            "service_summary": "Flight workspace parent metadata",
            "operational_notes": "Metadata-only parent workspace for flight smoke.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    operational_workspace_id = (workspace_created.get("workspace") or {}).get("id")
    if not operational_workspace_id:
        raise AssertionError(f"Parent operational workspace id missing: {workspace_created}")

    passenger_created = post(
        "/api/platform/passenger-workspaces",
        {
            "agency_id": agency_id,
            "operational_workspace_id": operational_workspace_id,
            "passenger_status": "active",
            "first_name": "Flight",
            "last_name": "Passenger",
            "nationality": "BG",
            "citizenship": "BG",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    passenger_id = (passenger_created.get("passenger_workspace") or {}).get("id") or "passenger-smoke"

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
            "departure_terminal": "2",
            "arrival_terminal": "1",
            "departure_datetime": "2027-10-10T06:00:00Z",
            "arrival_datetime": "2027-10-10T07:25:00Z",
            "aircraft_type": "A320",
            "cabin_class": "economy",
            "booking_class": "Y",
            "fare_family": "Economy Flex",
            "baggage_summary": "1 checked bag",
            "connection_summary": "Nonstop",
            "stopover_summary": "None",
            "elapsed_travel_time": "1h 25m",
            "operating_days": ["monday"],
            "passenger_ids": [passenger_id],
            "linked_request_ids": ["request-smoke"],
            "linked_trip_ids": ["trip-smoke"],
            "linked_offer_ids": ["offer-smoke"],
            "linked_booking_ids": ["booking-smoke"],
            "linked_ticket_ids": ["ticket-smoke"],
            "linked_document_ids": ["document-smoke"],
            "operational_notes": "Metadata-only flight workspace smoke.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    if created.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected create phase: {created.get('phase')}")
    assert_disabled_response(created)
    flight_workspace = created.get("flight_workspace") or {}
    assert_flight_shape(flight_workspace)
    flight_workspace_id = flight_workspace.get("id")
    if not flight_workspace_id:
        raise AssertionError(f"Flight workspace id missing: {created}")

    updated = put(
        f"/api/platform/flight-workspaces/{flight_workspace_id}",
        {
            "flight_status": "ready",
            "connection_summary": "Nonstop metadata reviewed",
            "operational_notes": "Updated metadata only; no schedule sync or airline lookup.",
            "metadata": {"updated": True, "metadata_only": True},
        },
        OWNER_HEADERS,
    )
    assert_disabled_response(updated)
    updated_flight = updated.get("flight_workspace") or {}
    assert_flight_shape(updated_flight)
    if updated_flight.get("flight_status") != "ready":
        raise AssertionError(f"Flight workspace update did not persist metadata: {updated}")

    for filter_query in [
        f"agency_id={agency_id}",
        "status=ready",
        "airline=LH",
        "departure_airport=SOF",
        "arrival_airport=FRA",
        "departure_date=2027-10-10",
        "cabin=economy",
        "booking_class=Y",
        f"operational_workspace_id={operational_workspace_id}",
    ]:
        filtered = get(f"/api/platform/flight-workspaces?{filter_query}", OWNER_HEADERS)
        assert_disabled_response(filtered)
        if not any(item.get("id") == flight_workspace_id for item in filtered.get("items") or []):
            raise AssertionError(f"Flight workspace filter {filter_query} missing created record: {filtered}")

    platform_summary = get("/api/platform/flight-workspaces/summary", OWNER_HEADERS)
    assert_summary_shape(platform_summary)

    platform_detail = get(f"/api/platform/flight-workspaces/{flight_workspace_id}", OWNER_HEADERS)
    assert_disabled_response(platform_detail)
    assert_flight_shape(platform_detail.get("flight_workspace") or {})

    agency_list = get(f"/api/agencies/{agency_id}/flight-workspaces?status=ready&airline=LH", OWNER_HEADERS)
    assert_disabled_response(agency_list)
    if agency_list.get("read_only") is not True:
        raise AssertionError(f"Agency flight workspace list should be read-only: {agency_list}")
    agency_item = next((item for item in agency_list.get("items") or [] if item.get("id") == flight_workspace_id), None)
    if not agency_item:
        raise AssertionError(f"Agency flight workspace list missing created record: {agency_list}")
    assert_flight_shape(agency_item, agency_view=True)

    agency_summary = get(f"/api/agencies/{agency_id}/flight-workspaces/summary", OWNER_HEADERS)
    assert_summary_shape(agency_summary, agency_id=agency_id)
    if agency_summary.get("read_only") is not True:
        raise AssertionError(f"Agency flight workspace summary should be read-only: {agency_summary}")

    agency_detail = get(f"/api/agencies/{agency_id}/flight-workspaces/{flight_workspace_id}", OWNER_HEADERS)
    assert_disabled_response(agency_detail)
    if agency_detail.get("read_only") is not True:
        raise AssertionError(f"Agency flight workspace detail should be read-only: {agency_detail}")
    assert_flight_shape(agency_detail.get("flight_workspace") or {}, agency_view=True)

    deleted = request("DELETE", f"/api/platform/flight-workspaces/{flight_workspace_id}", {}, OWNER_HEADERS)[1]
    assert_disabled_response(deleted)
    if deleted.get("deleted") is not True or (deleted.get("flight_workspace") or {}).get("flight_status") != "archived":
        raise AssertionError(f"Flight workspace delete should be metadata-only archive: {deleted}")

    after_delete = get(f"/api/platform/flight-workspaces?agency_id={agency_id}", OWNER_HEADERS)
    if any(item.get("id") == flight_workspace_id for item in after_delete.get("items") or []):
        raise AssertionError(f"Default flight workspace list should exclude archived-delete metadata: {after_delete}")
    include_archived = get(f"/api/platform/flight-workspaces?agency_id={agency_id}&include_archived=true", OWNER_HEADERS)
    if not any(item.get("id") == flight_workspace_id for item in include_archived.get("items") or []):
        raise AssertionError(f"include_archived should expose metadata-archived flight workspace: {include_archived}")

    request("POST", f"/api/agencies/{agency_id}/flight-workspaces", {"flight_number": "Blocked"}, OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/flight-workspaces/{flight_workspace_id}", {"flight_status": "active"}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/flight-workspaces/{flight_workspace_id}", {}, OWNER_HEADERS, 405)


def assert_flight_shape(flight_workspace: dict, *, agency_view: bool = False) -> None:
    for key in [
        "id",
        "agency_id",
        "operational_workspace_id",
        "flight_reference",
        "flight_status",
        "flight_type",
        "travel_direction",
        "airline_code",
        "airline_name",
        "marketing_carrier",
        "operating_carrier",
        "flight_number",
        "operating_flight_number",
        "departure_airport",
        "arrival_airport",
        "departure_terminal",
        "arrival_terminal",
        "departure_datetime",
        "arrival_datetime",
        "aircraft_type",
        "cabin_class",
        "booking_class",
        "fare_family",
        "baggage_summary",
        "connection_summary",
        "stopover_summary",
        "elapsed_travel_time",
        "operating_days",
        "passenger_ids",
        "linked_request_ids",
        "linked_trip_ids",
        "linked_offer_ids",
        "linked_booking_ids",
        "linked_ticket_ids",
        "linked_document_ids",
        "operational_notes",
        "flight_designator",
        "operational_workspace",
        "passengers",
        "linked_requests",
        "linked_trips",
        "linked_offers",
        "linked_bookings",
        "linked_tickets",
        "linked_documents",
    ]:
        if key not in flight_workspace:
            raise AssertionError(f"Flight workspace missing {key}: {flight_workspace}")
    if flight_workspace.get("metadata_only") is not True or flight_workspace.get("flight_workspace_metadata_only") is not True:
        raise AssertionError(f"Flight workspace is not metadata-only: {flight_workspace}")
    if agency_view and flight_workspace.get("read_only") is not True:
        raise AssertionError(f"Agency flight workspace should be read-only: {flight_workspace}")
    for flag in disabled_flags():
        if flight_workspace.get(flag) is not True:
            raise AssertionError(f"Flight workspace missing disabled flag {flag}: {flight_workspace}")
    if not flight_workspace.get("passengers") or not flight_workspace.get("linked_bookings") or not flight_workspace.get("linked_documents"):
        raise AssertionError(f"Flight workspace linked metadata shape missing references: {flight_workspace}")
    if not flight_workspace.get("operational_workspace"):
        raise AssertionError(f"Flight workspace missing operational workspace context: {flight_workspace}")


def assert_summary_shape(payload: dict, *, agency_id: str | None = None) -> None:
    assert_disabled_response(payload)
    if agency_id and payload.get("agency_id") != agency_id:
        raise AssertionError(f"Agency summary not scoped to agency: {payload}")
    summary = payload.get("summary") or {}
    for key in [
        "total_count",
        "by_status",
        "by_airline_code",
        "by_departure_airport",
        "by_arrival_airport",
        "by_cabin_class",
        "by_booking_class",
        "agency_count",
        "operational_workspace_count",
        "passenger_count",
        "linked_request_count",
        "linked_trip_count",
        "linked_offer_count",
        "linked_booking_count",
        "linked_ticket_count",
        "linked_document_count",
        "metadata_only",
    ]:
        if key not in summary:
            raise AssertionError(f"Flight workspace summary missing {key}: {payload}")
    if not FLIGHT_STATUSES.issubset(set((summary.get("by_status") or {}).keys())):
        raise AssertionError(f"Flight workspace summary missing statuses: {payload}")


def main() -> int:
    verify_model_and_collection_registration()
    openapi = get("/openapi.json")
    verify_routes(openapi.get("paths") or {})
    verify_frontend_and_docs()
    verify_readiness()
    verify_endpoint_behavior()
    print("Phase 41.3 flight workspace foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
