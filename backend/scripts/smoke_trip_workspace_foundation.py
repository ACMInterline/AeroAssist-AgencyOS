#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import TripWorkspace, TripWorkspaceCreate, TripWorkspaceStatus
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_41_7_ticket_workspace_foundation"
ROOT = Path(__file__).resolve().parents[2]
TRIP_STATUSES = {"draft", "planning", "active", "ready", "traveling", "completed", "archived"}


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
        "ticket_issuance_disabled",
        "gds_connectivity_disabled",
        "ndc_connectivity_disabled",
        "airline_apis_disabled",
        "airline_api_calls_disabled",
        "payment_processing_disabled",
        "invoicing_disabled",
        "ai_disabled",
        "background_workers_disabled",
        "automatic_trip_generation_disabled",
        "automatic_itinerary_generation_disabled",
        "itinerary_generation_disabled",
        "external_integrations_disabled",
        "external_api_calls_disabled",
        "automation_disabled",
    ]


def forbidden_enabled_flags() -> list[str]:
    return [
        "booking_execution_enabled",
        "ticket_issuance_enabled",
        "gds_connectivity_enabled",
        "ndc_connectivity_enabled",
        "airline_apis_enabled",
        "airline_api_calls_enabled",
        "payment_processing_enabled",
        "invoicing_enabled",
        "ai_enabled",
        "background_workers_enabled",
        "automatic_trip_generation_enabled",
        "automatic_itinerary_generation_enabled",
        "itinerary_generation_enabled",
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
    create_payload = TripWorkspaceCreate(
        agency_id="agency-smoke",
        operational_workspace_id="workspace-smoke",
        trip_reference="TRW-SMOKE-MODEL",
        trip_status=TripWorkspaceStatus.ACTIVE,
        journey_type="round_trip",
        service_type="flight",
        client_id="client-smoke",
        passenger_ids=["passenger-smoke"],
        flight_workspace_ids=["flight-smoke"],
        travel_request_ids=["request-smoke"],
        offer_ids=["offer-smoke"],
        booking_ids=["booking-smoke"],
        ticket_ids=["ticket-smoke"],
        emd_ids=["emd-smoke"],
        document_ids=["document-smoke"],
        departure_country="BG",
        destination_country="DE",
        departure_city="Sofia",
        destination_city="Frankfurt",
        origin_airport="SOF",
        destination_airport="FRA",
        departure_date="2027-11-10",
        return_date="2027-11-20",
        travel_duration="10 days",
        passenger_count=1,
        itinerary_summary="SOF-FRA-SOF metadata only",
        baggage_summary="1 checked bag",
        service_summary="Flight-only journey",
        operational_priority="high",
        assigned_agent="Taylor Trip",
        assigned_team=["trip-ops"],
        operational_notes="Metadata-only trip workspace smoke.",
        metadata={"smoke": True},
    )
    trip_workspace = TripWorkspace(**create_payload.model_dump(mode="json", exclude_none=True))
    dumped = trip_workspace.model_dump(mode="json")
    if dumped.get("trip_status") != "active" or dumped.get("departure_country") != "BG":
        raise AssertionError(f"Trip workspace dimensions were not preserved: {dumped}")
    for key in ["metadata_only", "trip_workspace_metadata_only", *disabled_flags()]:
        if dumped.get(key) is not True:
            raise AssertionError(f"Trip workspace model missing disabled flag {key}: {dumped}")
    if "trip_workspaces" not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("Trip workspaces collection is not registered.")
    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "trip_workspaces_id_unique",
        "trip_workspaces_reference_unique",
        "trip_workspaces_agency_status_lookup",
        "trip_workspaces_agency_departure_country_lookup",
        "trip_workspaces_agency_destination_country_lookup",
        "trip_workspaces_agency_departure_date_lookup",
        "trip_workspaces_agency_assigned_agent_lookup",
        "trip_workspaces_agency_priority_lookup",
        "trip_workspaces_operational_workspace_lookup",
        "trip_workspaces_status_lookup",
        "trip_workspaces_journey_type_lookup",
        "trip_workspaces_service_type_lookup",
        "trip_workspaces_client_lookup",
        "trip_workspaces_passenger_lookup",
        "trip_workspaces_flight_workspace_lookup",
        "trip_workspaces_travel_request_lookup",
        "trip_workspaces_offer_lookup",
        "trip_workspaces_booking_lookup",
        "trip_workspaces_ticket_lookup",
        "trip_workspaces_emd_lookup",
        "trip_workspaces_document_lookup",
        "trip_workspaces_departure_country_lookup",
        "trip_workspaces_destination_country_lookup",
        "trip_workspaces_departure_date_lookup",
        "trip_workspaces_return_date_lookup",
        "trip_workspaces_created_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Trip workspace index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    expected_methods = {
        "/api/platform/trip-workspaces": {"get", "post"},
        "/api/platform/trip-workspaces/summary": {"get"},
        "/api/platform/trip-workspaces/{trip_workspace_id}": {"get", "put", "delete"},
        "/api/agencies/{agency_id}/trip-workspaces": {"get"},
        "/api/agencies/{agency_id}/trip-workspaces/summary": {"get"},
        "/api/agencies/{agency_id}/trip-workspaces/{trip_workspace_id}": {"get"},
    }
    for path, methods in expected_methods.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in [
        "/api/agencies/{agency_id}/trip-workspaces",
        "/api/agencies/{agency_id}/trip-workspaces/summary",
        "/api/agencies/{agency_id}/trip-workspaces/{trip_workspace_id}",
    ]:
        methods = set(paths.get(path, {}).keys())
        blocked_methods = methods & {"post", "put", "patch", "delete"}
        if blocked_methods:
            raise AssertionError(f"Agency trip workspace route is not read-only: {path} {sorted(blocked_methods)}")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Trip Workspaces"),
        (ROOT / "frontend/src/App.jsx", "/platform/trip-workspaces"),
        (ROOT / "frontend/src/App.jsx", "/agency/trip-workspaces"),
        (ROOT / "frontend/src/pages/platform/TripWorkspacesPage.jsx", "Trip Workspaces"),
        (ROOT / "frontend/src/pages/platform/TripWorkspacesPage.jsx", "No itinerary generation"),
        (ROOT / "frontend/src/pages/platform/TripWorkspacesPage.jsx", "Passenger summary"),
        (ROOT / "frontend/src/pages/platform/TripWorkspacesPage.jsx", "EMDs"),
        (ROOT / "frontend/src/pages/agency/TripWorkspacesPage.jsx", "Trips"),
        (ROOT / "frontend/src/pages/agency/TripWorkspacesPage.jsx", "Read-only trip workspace metadata"),
        (ROOT / "docs/architecture/trip-workspace-foundation.md", "Trip Workspace Foundation"),
        (ROOT / "README.md", "Phase 41.4 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 41.4: Trip Workspace Foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "Phase 41.4 adds trip workspace metadata"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "Phase 41.4 adds trip workspace APIs"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Trip workspaces"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Trip workspaces"),
        (ROOT / "backend/services/blueprint_adoption_service.py", "Trip Workspaces"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/TripWorkspacesPage.jsx",
        ROOT / "frontend/src/pages/agency/TripWorkspacesPage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)
    for path in [
        ROOT / "frontend/src/pages/platform/TripWorkspacesPage.jsx",
        ROOT / "frontend/src/pages/agency/TripWorkspacesPage.jsx",
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
    section = readiness.get("trip_workspace_foundation") or {}
    for flag in [
        "trip_workspaces_enabled",
        "trip_workspace_metadata_enabled",
        "platform_trip_workspace_metadata_crud_enabled",
        "agency_trip_workspace_read_only_enabled",
        "trip_workspace_filter_by_status_enabled",
        "trip_workspace_filter_by_departure_country_enabled",
        "trip_workspace_filter_by_destination_country_enabled",
        "trip_workspace_filter_by_departure_date_enabled",
        "trip_workspace_filter_by_assigned_agent_enabled",
        "trip_workspace_filter_by_priority_enabled",
        "trip_workspace_filter_by_operational_workspace_enabled",
        "trip_reference_metadata_enabled",
        "journey_type_metadata_enabled",
        "service_type_metadata_enabled",
        "client_metadata_enabled",
        "passenger_summary_metadata_enabled",
        "flight_summary_metadata_enabled",
        "linked_request_metadata_enabled",
        "linked_offer_metadata_enabled",
        "linked_booking_metadata_enabled",
        "linked_ticket_metadata_enabled",
        "linked_emd_metadata_enabled",
        "linked_document_metadata_enabled",
        "route_metadata_enabled",
        "travel_date_metadata_enabled",
        "itinerary_summary_metadata_enabled",
        "baggage_summary_metadata_enabled",
        "service_summary_metadata_enabled",
        "assigned_team_metadata_enabled",
        "operational_notes_metadata_enabled",
        "read_only_ui_enabled",
        "metadata_only",
        "trip_workspace_metadata_only",
    ]:
        require_flag(section, flag)
    for flag in disabled_flags():
        require_flag(section, flag)
    require_flag(section, "readiness_required", False)
    for count_key in [
        "trip_workspace_count",
        "trip_workspace_status_counts",
        "trip_workspace_departure_country_count",
        "trip_workspace_destination_country_count",
        "trip_workspace_priority_count",
    ]:
        if count_key not in section:
            raise AssertionError(f"Trip workspace readiness missing count: {count_key}")
    if not TRIP_STATUSES.issubset(set((section.get("trip_workspace_status_counts") or {}).keys())):
        raise AssertionError(f"Trip workspace readiness status counts missing statuses: {section}")
    previous_section = readiness.get("flight_workspace_foundation") or {}
    if previous_section.get("metadata_only") is not True:
        raise AssertionError("Previous flight workspace section should remain metadata-only.")


def verify_endpoint_behavior() -> None:
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires seeded demo agency.")
    agency_id = agencies[0]["id"]

    workspace_created = post(
        "/api/platform/operational-travel-workspaces",
        {
            "agency_id": agency_id,
            "workspace_title": "Phase 41.4 parent operational workspace smoke",
            "workspace_type": "trip",
            "workspace_status": "open",
            "priority": "high",
            "assigned_team": ["trip-ops"],
            "assigned_agent": "Taylor Trip",
            "travel_start_date": "2027-11-10",
            "travel_end_date": "2027-11-20",
            "origin_summary": "SOF",
            "destination_summary": "FRA",
            "service_summary": "Trip workspace parent metadata",
            "operational_notes": "Metadata-only parent workspace for trip smoke.",
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
            "first_name": "Trip",
            "last_name": "Passenger",
            "nationality": "BG",
            "citizenship": "BG",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    passenger_id = (passenger_created.get("passenger_workspace") or {}).get("id") or "passenger-smoke"

    request_created = post(
        "/api/platform/travel-request-workspaces",
        {
            "agency_id": agency_id,
            "operational_workspace_id": operational_workspace_id,
            "request_title": "Phase 41.4 linked request smoke",
            "request_type": "flight",
            "request_status": "open",
            "request_priority": "high",
            "client_id": "client-smoke",
            "primary_passenger_id": passenger_id,
            "requester_name": "Trip Requester",
            "requested_origin": "SOF",
            "requested_destination": "FRA",
            "requested_departure_date": "2027-11-10",
            "requested_return_date": "2027-11-20",
            "passenger_count": 1,
            "assigned_agent": "Taylor Trip",
            "internal_notes": "Metadata-only request for trip smoke.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    request_id = (request_created.get("request_workspace") or {}).get("id") or "request-smoke"

    flight_created = post(
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
            "departure_datetime": "2027-11-10T06:00:00Z",
            "arrival_datetime": "2027-11-10T07:25:00Z",
            "aircraft_type": "A320",
            "cabin_class": "economy",
            "booking_class": "Y",
            "fare_family": "Economy Flex",
            "passenger_ids": [passenger_id],
            "linked_request_ids": [request_id],
            "linked_booking_ids": ["booking-smoke"],
            "linked_document_ids": ["document-smoke"],
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    flight_id = (flight_created.get("flight_workspace") or {}).get("id") or "flight-smoke"

    created = post(
        "/api/platform/trip-workspaces",
        {
            "agency_id": agency_id,
            "operational_workspace_id": operational_workspace_id,
            "trip_status": "active",
            "journey_type": "round_trip",
            "service_type": "flight",
            "client_id": "client-smoke",
            "passenger_ids": [passenger_id],
            "flight_workspace_ids": [flight_id],
            "travel_request_ids": [request_id],
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
            "departure_date": "2027-11-10",
            "return_date": "2027-11-20",
            "travel_duration": "10 days",
            "passenger_count": 1,
            "itinerary_summary": "SOF-FRA-SOF metadata only",
            "baggage_summary": "1 checked bag",
            "service_summary": "Flight-only journey",
            "operational_priority": "high",
            "assigned_agent": "Taylor Trip",
            "assigned_team": ["trip-ops"],
            "operational_notes": "Metadata-only trip workspace smoke.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    if created.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected create phase: {created.get('phase')}")
    assert_disabled_response(created)
    trip_workspace = created.get("trip_workspace") or {}
    assert_trip_shape(trip_workspace)
    trip_workspace_id = trip_workspace.get("id")
    if not trip_workspace_id:
        raise AssertionError(f"Trip workspace id missing: {created}")

    updated = put(
        f"/api/platform/trip-workspaces/{trip_workspace_id}",
        {
            "trip_status": "ready",
            "service_summary": "Flight-only journey metadata reviewed",
            "operational_notes": "Updated metadata only; no itinerary generation.",
            "metadata": {"updated": True, "metadata_only": True},
        },
        OWNER_HEADERS,
    )
    assert_disabled_response(updated)
    updated_trip = updated.get("trip_workspace") or {}
    assert_trip_shape(updated_trip)
    if updated_trip.get("trip_status") != "ready":
        raise AssertionError(f"Trip workspace update did not persist metadata: {updated}")

    for filter_query in [
        f"agency_id={agency_id}",
        "status=ready",
        "departure_country=BG",
        "destination_country=DE",
        "departure_date=2027-11-10",
        "assigned_agent=Taylor%20Trip",
        "priority=high",
        f"operational_workspace_id={operational_workspace_id}",
    ]:
        filtered = get(f"/api/platform/trip-workspaces?{filter_query}", OWNER_HEADERS)
        assert_disabled_response(filtered)
        if not any(item.get("id") == trip_workspace_id for item in filtered.get("items") or []):
            raise AssertionError(f"Trip workspace filter {filter_query} missing created record: {filtered}")

    platform_summary = get("/api/platform/trip-workspaces/summary", OWNER_HEADERS)
    assert_summary_shape(platform_summary)

    platform_detail = get(f"/api/platform/trip-workspaces/{trip_workspace_id}", OWNER_HEADERS)
    assert_disabled_response(platform_detail)
    assert_trip_shape(platform_detail.get("trip_workspace") or {})

    agency_list = get(f"/api/agencies/{agency_id}/trip-workspaces?status=ready&departure_country=BG", OWNER_HEADERS)
    assert_disabled_response(agency_list)
    if agency_list.get("read_only") is not True:
        raise AssertionError(f"Agency trip workspace list should be read-only: {agency_list}")
    agency_item = next((item for item in agency_list.get("items") or [] if item.get("id") == trip_workspace_id), None)
    if not agency_item:
        raise AssertionError(f"Agency trip workspace list missing created record: {agency_list}")
    assert_trip_shape(agency_item, agency_view=True)

    agency_summary = get(f"/api/agencies/{agency_id}/trip-workspaces/summary", OWNER_HEADERS)
    assert_summary_shape(agency_summary, agency_id=agency_id)
    if agency_summary.get("read_only") is not True:
        raise AssertionError(f"Agency trip workspace summary should be read-only: {agency_summary}")

    agency_detail = get(f"/api/agencies/{agency_id}/trip-workspaces/{trip_workspace_id}", OWNER_HEADERS)
    assert_disabled_response(agency_detail)
    if agency_detail.get("read_only") is not True:
        raise AssertionError(f"Agency trip workspace detail should be read-only: {agency_detail}")
    assert_trip_shape(agency_detail.get("trip_workspace") or {}, agency_view=True)

    deleted = request("DELETE", f"/api/platform/trip-workspaces/{trip_workspace_id}", {}, OWNER_HEADERS)[1]
    assert_disabled_response(deleted)
    if deleted.get("deleted") is not True or (deleted.get("trip_workspace") or {}).get("trip_status") != "archived":
        raise AssertionError(f"Trip workspace delete should be metadata-only archive: {deleted}")

    after_delete = get(f"/api/platform/trip-workspaces?agency_id={agency_id}", OWNER_HEADERS)
    if any(item.get("id") == trip_workspace_id for item in after_delete.get("items") or []):
        raise AssertionError(f"Default trip workspace list should exclude archived-delete metadata: {after_delete}")
    include_archived = get(f"/api/platform/trip-workspaces?agency_id={agency_id}&include_archived=true", OWNER_HEADERS)
    if not any(item.get("id") == trip_workspace_id for item in include_archived.get("items") or []):
        raise AssertionError(f"include_archived should expose metadata-archived trip workspace: {include_archived}")

    request("POST", f"/api/agencies/{agency_id}/trip-workspaces", {"trip_status": "active"}, OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/trip-workspaces/{trip_workspace_id}", {"trip_status": "active"}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/trip-workspaces/{trip_workspace_id}", {}, OWNER_HEADERS, 405)


def assert_trip_shape(trip_workspace: dict, *, agency_view: bool = False) -> None:
    for key in [
        "id",
        "agency_id",
        "operational_workspace_id",
        "trip_reference",
        "trip_status",
        "journey_type",
        "service_type",
        "client_id",
        "passenger_ids",
        "flight_workspace_ids",
        "travel_request_ids",
        "offer_ids",
        "booking_ids",
        "ticket_ids",
        "emd_ids",
        "document_ids",
        "departure_country",
        "destination_country",
        "departure_city",
        "destination_city",
        "origin_airport",
        "destination_airport",
        "departure_date",
        "return_date",
        "travel_duration",
        "passenger_count",
        "itinerary_summary",
        "baggage_summary",
        "service_summary",
        "operational_priority",
        "assigned_agent",
        "assigned_team",
        "operational_notes",
        "trip_display_name",
        "operational_workspace",
        "client",
        "passengers",
        "flight_workspaces",
        "travel_requests",
        "offers",
        "bookings",
        "tickets",
        "emds",
        "documents",
    ]:
        if key not in trip_workspace:
            raise AssertionError(f"Trip workspace missing {key}: {trip_workspace}")
    if trip_workspace.get("metadata_only") is not True or trip_workspace.get("trip_workspace_metadata_only") is not True:
        raise AssertionError(f"Trip workspace is not metadata-only: {trip_workspace}")
    if agency_view and trip_workspace.get("read_only") is not True:
        raise AssertionError(f"Agency trip workspace should be read-only: {trip_workspace}")
    for flag in disabled_flags():
        if trip_workspace.get(flag) is not True:
            raise AssertionError(f"Trip workspace missing disabled flag {flag}: {trip_workspace}")
    if not trip_workspace.get("passengers") or not trip_workspace.get("flight_workspaces") or not trip_workspace.get("bookings") or not trip_workspace.get("documents"):
        raise AssertionError(f"Trip workspace linked metadata shape missing references: {trip_workspace}")
    if not trip_workspace.get("operational_workspace"):
        raise AssertionError(f"Trip workspace missing operational workspace context: {trip_workspace}")


def assert_summary_shape(payload: dict, *, agency_id: str | None = None) -> None:
    assert_disabled_response(payload)
    if agency_id and payload.get("agency_id") != agency_id:
        raise AssertionError(f"Agency summary not scoped to agency: {payload}")
    summary = payload.get("summary") or {}
    for key in [
        "total_count",
        "by_status",
        "by_departure_country",
        "by_destination_country",
        "by_priority",
        "agency_count",
        "operational_workspace_count",
        "passenger_count",
        "flight_workspace_count",
        "travel_request_count",
        "offer_count",
        "booking_count",
        "ticket_count",
        "emd_count",
        "document_count",
        "metadata_only",
    ]:
        if key not in summary:
            raise AssertionError(f"Trip workspace summary missing {key}: {payload}")
    if not TRIP_STATUSES.issubset(set((summary.get("by_status") or {}).keys())):
        raise AssertionError(f"Trip workspace summary missing statuses: {payload}")


def main() -> int:
    verify_model_and_collection_registration()
    openapi = get("/openapi.json")
    verify_routes(openapi.get("paths") or {})
    verify_frontend_and_docs()
    verify_readiness()
    verify_endpoint_behavior()
    print("Phase 41.4 trip workspace foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
