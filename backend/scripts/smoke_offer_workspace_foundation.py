#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import OfferWorkspaceV2, OfferWorkspaceV2Create, OfferWorkspaceV2Status
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_52_1_reference_data_engine_foundation"
ROOT = Path(__file__).resolve().parents[2]
OFFER_STATUSES = {"draft", "preparing", "review", "ready", "shared", "accepted", "declined", "expired", "archived"}


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
        "payment_processing_disabled",
        "gds_connectivity_disabled",
        "ndc_connectivity_disabled",
        "airline_apis_disabled",
        "airline_api_calls_disabled",
        "fare_calculation_engines_disabled",
        "fare_calculation_disabled",
        "live_pricing_disabled",
        "ai_itinerary_generation_disabled",
        "supplier_integrations_disabled",
        "external_api_calls_disabled",
        "automatic_booking_conversion_disabled",
        "background_workers_disabled",
        "automation_disabled",
    ]


def forbidden_enabled_flags() -> list[str]:
    return [
        "booking_execution_enabled",
        "ticket_issuance_enabled",
        "payment_processing_enabled",
        "gds_connectivity_enabled",
        "ndc_connectivity_enabled",
        "airline_apis_enabled",
        "airline_api_calls_enabled",
        "fare_calculation_engines_enabled",
        "fare_calculation_enabled",
        "live_pricing_enabled",
        "ai_itinerary_generation_enabled",
        "supplier_integrations_enabled",
        "external_api_calls_enabled",
        "automatic_booking_conversion_enabled",
        "background_workers_enabled",
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
    create_payload = OfferWorkspaceV2Create(
        agency_id="agency-smoke",
        operational_workspace_id="workspace-smoke",
        trip_workspace_id="trip-smoke",
        offer_reference="OFW-SMOKE-MODEL",
        offer_status=OfferWorkspaceV2Status.PREPARING,
        offer_type="flight_package",
        client_id="client-smoke",
        passenger_ids=["passenger-smoke"],
        flight_workspace_ids=["flight-smoke"],
        offer_title="Phase 41.5 offer smoke model",
        offer_summary="Metadata-only offer model smoke.",
        destination_summary="Frankfurt",
        itinerary_summary="SOF-FRA-SOF",
        pricing_summary="Manual price summary only.",
        currency="EUR",
        total_price=1180.5,
        taxes_summary="Taxes metadata.",
        fees_summary="Fees metadata.",
        ancillary_summary="Ancillary metadata.",
        baggage_summary="One checked bag.",
        seat_summary="Standard seats.",
        meal_summary="Standard meals.",
        hotel_summary="No hotel.",
        transfer_summary="No transfer.",
        insurance_summary="Insurance declined.",
        validity_date="2027-12-10",
        assigned_agent="Taylor Offer",
        agent_notes="Agent notes metadata only.",
        customer_notes="Customer notes metadata only.",
        internal_notes="Internal notes metadata only.",
        linked_booking_ids=["booking-smoke"],
        linked_ticket_ids=["ticket-smoke"],
        linked_document_ids=["document-smoke"],
        metadata={"smoke": True},
    )
    offer_workspace = OfferWorkspaceV2(**create_payload.model_dump(mode="json", exclude_none=True))
    dumped = offer_workspace.model_dump(mode="json")
    if dumped.get("offer_status") != "preparing" or dumped.get("currency") != "EUR" or dumped.get("total_price") != 1180.5:
        raise AssertionError(f"Offer workspace dimensions were not preserved: {dumped}")
    for key in ["metadata_only", "offer_workspace_metadata_only", *disabled_flags()]:
        if dumped.get(key) is not True:
            raise AssertionError(f"Offer workspace model missing disabled flag {key}: {dumped}")
    if "offer_workspaces_v2" not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("Offer workspace v2 collection is not registered.")
    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "offer_workspaces_v2_id_unique",
        "offer_workspaces_v2_reference_unique",
        "offer_workspaces_v2_agency_status_lookup",
        "offer_workspaces_v2_agency_validity_lookup",
        "offer_workspaces_v2_agency_client_lookup",
        "offer_workspaces_v2_agency_destination_lookup",
        "offer_workspaces_v2_agency_assigned_agent_lookup",
        "offer_workspaces_v2_agency_price_lookup",
        "offer_workspaces_v2_operational_workspace_lookup",
        "offer_workspaces_v2_trip_workspace_lookup",
        "offer_workspaces_v2_status_lookup",
        "offer_workspaces_v2_type_lookup",
        "offer_workspaces_v2_client_lookup",
        "offer_workspaces_v2_passenger_lookup",
        "offer_workspaces_v2_flight_workspace_lookup",
        "offer_workspaces_v2_currency_lookup",
        "offer_workspaces_v2_total_price_lookup",
        "offer_workspaces_v2_validity_lookup",
        "offer_workspaces_v2_assigned_agent_lookup",
        "offer_workspaces_v2_booking_lookup",
        "offer_workspaces_v2_ticket_lookup",
        "offer_workspaces_v2_document_lookup",
        "offer_workspaces_v2_created_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Offer workspace v2 index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    expected_methods = {
        "/api/platform/offer-workspaces": {"get", "post"},
        "/api/platform/offer-workspaces/summary": {"get"},
        "/api/platform/offer-workspaces/{offer_workspace_id}": {"get", "put", "delete"},
        "/api/agencies/{agency_id}/offer-workspaces-v2": {"get"},
        "/api/agencies/{agency_id}/offer-workspaces-v2/summary": {"get"},
        "/api/agencies/{agency_id}/offer-workspaces-v2/{offer_workspace_id}": {"get"},
    }
    for path, methods in expected_methods.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in [
        "/api/agencies/{agency_id}/offer-workspaces-v2",
        "/api/agencies/{agency_id}/offer-workspaces-v2/summary",
        "/api/agencies/{agency_id}/offer-workspaces-v2/{offer_workspace_id}",
    ]:
        methods = set(paths.get(path, {}).keys())
        blocked_methods = methods & {"post", "put", "patch", "delete"}
        if blocked_methods:
            raise AssertionError(f"Agency offer workspace route is not read-only: {path} {sorted(blocked_methods)}")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Offer Workspaces"),
        (ROOT / "frontend/src/App.jsx", "/platform/offer-workspaces"),
        (ROOT / "frontend/src/App.jsx", "/agency/offer-workspaces"),
        (ROOT / "frontend/src/pages/platform/OfferWorkspacesPage.jsx", "Offer Workspaces"),
        (ROOT / "frontend/src/pages/platform/OfferWorkspacesPage.jsx", "No fare calculations"),
        (ROOT / "frontend/src/pages/platform/OfferWorkspacesPage.jsx", "Pricing summary"),
        (ROOT / "frontend/src/pages/agency/OfferWorkspaceMetadataPage.jsx", "Offers"),
        (ROOT / "frontend/src/pages/agency/OfferWorkspaceMetadataPage.jsx", "Read-only offer workspace metadata"),
        (ROOT / "frontend/src/pages/agency/OfferWorkspaceMetadataPage.jsx", "No live pricing"),
        (ROOT / "docs/architecture/offer-workspace-foundation.md", "Offer Workspace Foundation"),
        (ROOT / "README.md", "Phase 41.5 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 41.5: Offer Workspace Foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "Phase 41.5 adds offer workspace metadata"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "Phase 41.5 adds offer workspace APIs"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Offer workspaces"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Offer workspaces"),
        (ROOT / "backend/services/blueprint_adoption_service.py", "Offer Workspaces"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/OfferWorkspacesPage.jsx",
        ROOT / "frontend/src/pages/agency/OfferWorkspaceMetadataPage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)
    for path in [
        ROOT / "frontend/src/pages/platform/OfferWorkspacesPage.jsx",
        ROOT / "frontend/src/pages/agency/OfferWorkspaceMetadataPage.jsx",
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
    section = readiness.get("offer_workspace_foundation") or {}
    for flag in [
        "offer_workspaces_enabled",
        "offer_workspace_metadata_enabled",
        "platform_offer_workspace_metadata_crud_enabled",
        "agency_offer_workspace_read_only_enabled",
        "offer_workspace_filter_by_status_enabled",
        "offer_workspace_filter_by_validity_enabled",
        "offer_workspace_filter_by_client_enabled",
        "offer_workspace_filter_by_destination_enabled",
        "offer_workspace_filter_by_price_range_enabled",
        "offer_workspace_filter_by_assigned_agent_enabled",
        "offer_workspace_filter_by_trip_workspace_enabled",
        "offer_reference_metadata_enabled",
        "offer_status_metadata_enabled",
        "offer_type_metadata_enabled",
        "client_metadata_enabled",
        "passenger_summary_metadata_enabled",
        "flight_summary_metadata_enabled",
        "trip_summary_metadata_enabled",
        "pricing_summary_metadata_enabled",
        "taxes_metadata_enabled",
        "fees_metadata_enabled",
        "ancillary_metadata_enabled",
        "baggage_metadata_enabled",
        "seat_metadata_enabled",
        "meal_metadata_enabled",
        "hotel_metadata_enabled",
        "transfer_metadata_enabled",
        "insurance_metadata_enabled",
        "validity_metadata_enabled",
        "linked_booking_metadata_enabled",
        "linked_ticket_metadata_enabled",
        "linked_document_metadata_enabled",
        "agent_notes_metadata_enabled",
        "customer_notes_metadata_enabled",
        "internal_notes_metadata_enabled",
        "read_only_ui_enabled",
        "metadata_only",
        "offer_workspace_metadata_only",
    ]:
        require_flag(section, flag)
    for flag in disabled_flags():
        require_flag(section, flag)
    require_flag(section, "readiness_required", False)
    for count_key in [
        "offer_workspace_count",
        "offer_workspace_status_counts",
        "offer_workspace_type_count",
        "offer_workspace_currency_count",
        "offer_workspace_destination_count",
        "offer_workspace_assigned_agent_count",
    ]:
        if count_key not in section:
            raise AssertionError(f"Offer workspace readiness missing count: {count_key}")
    if not OFFER_STATUSES.issubset(set((section.get("offer_workspace_status_counts") or {}).keys())):
        raise AssertionError(f"Offer workspace readiness status counts missing statuses: {section}")
    previous_section = readiness.get("trip_workspace_foundation") or {}
    if previous_section.get("metadata_only") is not True:
        raise AssertionError("Previous trip workspace section should remain metadata-only.")


def verify_endpoint_behavior() -> None:
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires seeded demo agency.")
    agency_id = agencies[0]["id"]

    workspace_created = post(
        "/api/platform/operational-travel-workspaces",
        {
            "agency_id": agency_id,
            "workspace_title": "Phase 41.5 parent operational workspace smoke",
            "workspace_type": "offer",
            "workspace_status": "open",
            "priority": "high",
            "assigned_team": ["offer-ops"],
            "assigned_agent": "Taylor Offer",
            "travel_start_date": "2027-12-01",
            "travel_end_date": "2027-12-12",
            "origin_summary": "SOF",
            "destination_summary": "FRA",
            "service_summary": "Offer workspace parent metadata",
            "operational_notes": "Metadata-only parent workspace for offer smoke.",
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
            "first_name": "Offer",
            "last_name": "Passenger",
            "nationality": "BG",
            "citizenship": "BG",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    passenger_id = (passenger_created.get("passenger_workspace") or {}).get("id") or "passenger-smoke"

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
            "departure_datetime": "2027-12-01T06:00:00Z",
            "arrival_datetime": "2027-12-01T07:25:00Z",
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
    flight_id = (flight_created.get("flight_workspace") or {}).get("id") or "flight-smoke"

    trip_created = post(
        "/api/platform/trip-workspaces",
        {
            "agency_id": agency_id,
            "operational_workspace_id": operational_workspace_id,
            "trip_status": "ready",
            "journey_type": "round_trip",
            "service_type": "flight",
            "client_id": "client-offer-smoke",
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
            "departure_date": "2027-12-01",
            "return_date": "2027-12-12",
            "travel_duration": "11 days",
            "passenger_count": 1,
            "itinerary_summary": "SOF-FRA-SOF metadata only",
            "baggage_summary": "1 checked bag",
            "service_summary": "Flight-only journey",
            "operational_priority": "high",
            "assigned_agent": "Taylor Offer",
            "assigned_team": ["offer-ops"],
            "operational_notes": "Metadata-only trip workspace for offer smoke.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    trip_workspace_id = (trip_created.get("trip_workspace") or {}).get("id")
    if not trip_workspace_id:
        raise AssertionError(f"Trip workspace id missing: {trip_created}")

    created = post(
        "/api/platform/offer-workspaces",
        {
            "agency_id": agency_id,
            "operational_workspace_id": operational_workspace_id,
            "trip_workspace_id": trip_workspace_id,
            "offer_status": "preparing",
            "offer_type": "flight_package",
            "client_id": "client-offer-smoke",
            "passenger_ids": [passenger_id],
            "flight_workspace_ids": [flight_id],
            "offer_title": "Phase 41.5 offer smoke",
            "offer_summary": "Metadata-only offer proposal for SOF to FRA.",
            "destination_summary": "Frankfurt",
            "itinerary_summary": "SOF-FRA-SOF offer metadata only.",
            "pricing_summary": "Manual price summary only.",
            "currency": "EUR",
            "total_price": 1180.5,
            "taxes_summary": "Taxes metadata only.",
            "fees_summary": "Fees metadata only.",
            "ancillary_summary": "Ancillary metadata only.",
            "baggage_summary": "1 checked bag.",
            "seat_summary": "Standard seats.",
            "meal_summary": "Standard meals.",
            "hotel_summary": "No hotel included.",
            "transfer_summary": "No transfer included.",
            "insurance_summary": "Insurance declined.",
            "validity_date": "2027-12-10",
            "assigned_agent": "Taylor Offer",
            "agent_notes": "Agent notes metadata only.",
            "customer_notes": "Customer notes metadata only.",
            "internal_notes": "Internal notes metadata only.",
            "linked_booking_ids": ["booking-smoke"],
            "linked_ticket_ids": ["ticket-smoke"],
            "linked_document_ids": ["document-smoke"],
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    if created.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected create phase: {created.get('phase')}")
    assert_disabled_response(created)
    offer_workspace = created.get("offer_workspace") or {}
    assert_offer_shape(offer_workspace)
    offer_workspace_id = offer_workspace.get("id")
    if not offer_workspace_id:
        raise AssertionError(f"Offer workspace id missing: {created}")

    updated = put(
        f"/api/platform/offer-workspaces/{offer_workspace_id}",
        {
            "offer_status": "ready",
            "pricing_summary": "Manual price summary reviewed; still metadata only.",
            "internal_notes": "Updated metadata only; no fare calculation.",
            "metadata": {"updated": True, "metadata_only": True},
        },
        OWNER_HEADERS,
    )
    assert_disabled_response(updated)
    updated_offer = updated.get("offer_workspace") or {}
    assert_offer_shape(updated_offer)
    if updated_offer.get("offer_status") != "ready":
        raise AssertionError(f"Offer workspace update did not persist metadata: {updated}")

    for filter_query in [
        f"agency_id={agency_id}",
        "status=ready",
        "validity=2027-12-10",
        "client_id=client-offer-smoke",
        "destination=Frankfurt",
        "min_price=1000",
        "max_price=1200",
        "assigned_agent=Taylor%20Offer",
        f"trip_workspace_id={trip_workspace_id}",
    ]:
        filtered = get(f"/api/platform/offer-workspaces?{filter_query}", OWNER_HEADERS)
        assert_disabled_response(filtered)
        if not any(item.get("id") == offer_workspace_id for item in filtered.get("items") or []):
            raise AssertionError(f"Offer workspace filter {filter_query} missing created record: {filtered}")

    platform_summary = get("/api/platform/offer-workspaces/summary", OWNER_HEADERS)
    assert_summary_shape(platform_summary)

    platform_detail = get(f"/api/platform/offer-workspaces/{offer_workspace_id}", OWNER_HEADERS)
    assert_disabled_response(platform_detail)
    assert_offer_shape(platform_detail.get("offer_workspace") or {})

    agency_list = get(f"/api/agencies/{agency_id}/offer-workspaces-v2?status=ready&destination=Frankfurt", OWNER_HEADERS)
    assert_disabled_response(agency_list)
    if agency_list.get("read_only") is not True:
        raise AssertionError(f"Agency offer workspace list should be read-only: {agency_list}")
    agency_item = next((item for item in agency_list.get("items") or [] if item.get("id") == offer_workspace_id), None)
    if not agency_item:
        raise AssertionError(f"Agency offer workspace list missing created record: {agency_list}")
    assert_offer_shape(agency_item, agency_view=True)

    agency_summary = get(f"/api/agencies/{agency_id}/offer-workspaces-v2/summary", OWNER_HEADERS)
    assert_summary_shape(agency_summary, agency_id=agency_id)
    if agency_summary.get("read_only") is not True:
        raise AssertionError(f"Agency offer workspace summary should be read-only: {agency_summary}")

    agency_detail = get(f"/api/agencies/{agency_id}/offer-workspaces-v2/{offer_workspace_id}", OWNER_HEADERS)
    assert_disabled_response(agency_detail)
    if agency_detail.get("read_only") is not True:
        raise AssertionError(f"Agency offer workspace detail should be read-only: {agency_detail}")
    assert_offer_shape(agency_detail.get("offer_workspace") or {}, agency_view=True)

    deleted = request("DELETE", f"/api/platform/offer-workspaces/{offer_workspace_id}", {}, OWNER_HEADERS)[1]
    assert_disabled_response(deleted)
    if deleted.get("deleted") is not True or (deleted.get("offer_workspace") or {}).get("offer_status") != "archived":
        raise AssertionError(f"Offer workspace delete should be metadata-only archive: {deleted}")

    after_delete = get(f"/api/platform/offer-workspaces?agency_id={agency_id}", OWNER_HEADERS)
    if any(item.get("id") == offer_workspace_id for item in after_delete.get("items") or []):
        raise AssertionError(f"Default offer workspace list should exclude archived-delete metadata: {after_delete}")
    include_archived = get(f"/api/platform/offer-workspaces?agency_id={agency_id}&include_archived=true", OWNER_HEADERS)
    if not any(item.get("id") == offer_workspace_id for item in include_archived.get("items") or []):
        raise AssertionError(f"include_archived should expose metadata-archived offer workspace: {include_archived}")

    request("POST", f"/api/agencies/{agency_id}/offer-workspaces-v2", {"offer_title": "blocked"}, OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/offer-workspaces-v2/{offer_workspace_id}", {"offer_status": "ready"}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/offer-workspaces-v2/{offer_workspace_id}", {}, OWNER_HEADERS, 405)


def assert_offer_shape(offer_workspace: dict, *, agency_view: bool = False) -> None:
    for key in [
        "id",
        "agency_id",
        "operational_workspace_id",
        "trip_workspace_id",
        "offer_reference",
        "offer_status",
        "offer_type",
        "client_id",
        "passenger_ids",
        "flight_workspace_ids",
        "offer_title",
        "offer_summary",
        "destination_summary",
        "itinerary_summary",
        "pricing_summary",
        "currency",
        "total_price",
        "taxes_summary",
        "fees_summary",
        "ancillary_summary",
        "baggage_summary",
        "seat_summary",
        "meal_summary",
        "hotel_summary",
        "transfer_summary",
        "insurance_summary",
        "validity_date",
        "assigned_agent",
        "agent_notes",
        "customer_notes",
        "internal_notes",
        "linked_booking_ids",
        "linked_ticket_ids",
        "linked_document_ids",
        "offer_display_name",
        "agency",
        "operational_workspace",
        "trip_workspace",
        "client",
        "passengers",
        "flight_workspaces",
        "linked_bookings",
        "linked_tickets",
        "linked_documents",
    ]:
        if key not in offer_workspace:
            raise AssertionError(f"Offer workspace missing {key}: {offer_workspace}")
    if offer_workspace.get("metadata_only") is not True or offer_workspace.get("offer_workspace_metadata_only") is not True:
        raise AssertionError(f"Offer workspace is not metadata-only: {offer_workspace}")
    if agency_view and offer_workspace.get("read_only") is not True:
        raise AssertionError(f"Agency offer workspace should be read-only: {offer_workspace}")
    for flag in disabled_flags():
        if offer_workspace.get(flag) is not True:
            raise AssertionError(f"Offer workspace missing disabled flag {flag}: {offer_workspace}")
    if not offer_workspace.get("passengers") or not offer_workspace.get("flight_workspaces"):
        raise AssertionError(f"Offer workspace linked passenger/flight metadata missing references: {offer_workspace}")
    if not offer_workspace.get("linked_bookings") or not offer_workspace.get("linked_tickets") or not offer_workspace.get("linked_documents"):
        raise AssertionError(f"Offer workspace linked booking/ticket/document metadata missing references: {offer_workspace}")
    if not offer_workspace.get("operational_workspace") or not offer_workspace.get("trip_workspace"):
        raise AssertionError(f"Offer workspace missing operational/trip context: {offer_workspace}")


def assert_summary_shape(payload: dict, *, agency_id: str | None = None) -> None:
    assert_disabled_response(payload)
    if agency_id and payload.get("agency_id") != agency_id:
        raise AssertionError(f"Agency summary not scoped to agency: {payload}")
    summary = payload.get("summary") or {}
    for key in [
        "total_count",
        "by_status",
        "by_type",
        "by_currency",
        "by_destination",
        "agency_count",
        "operational_workspace_count",
        "trip_workspace_count",
        "assigned_agent_count",
        "passenger_count",
        "flight_workspace_count",
        "linked_booking_count",
        "linked_ticket_count",
        "linked_document_count",
        "metadata_only",
    ]:
        if key not in summary:
            raise AssertionError(f"Offer workspace summary missing {key}: {payload}")
    if not OFFER_STATUSES.issubset(set((summary.get("by_status") or {}).keys())):
        raise AssertionError(f"Offer workspace summary missing statuses: {payload}")


def main() -> int:
    verify_model_and_collection_registration()
    openapi = get("/openapi.json")
    verify_routes(openapi.get("paths") or {})
    verify_frontend_and_docs()
    verify_readiness()
    verify_endpoint_behavior()
    print("Phase 41.5 offer workspace foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
