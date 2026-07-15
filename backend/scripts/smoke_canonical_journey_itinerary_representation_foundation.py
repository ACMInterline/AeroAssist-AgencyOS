#!/usr/bin/env python3
import asyncio
import copy
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS, Database
from models import (
    JourneyConnectionRepresentation,
    JourneyFareBrandPresentation,
    JourneyItineraryOption,
    JourneyLegRepresentation,
    JourneyPresentationConfiguration,
    JourneyRepresentation,
    JourneySegmentRepresentation,
    JourneyServicePresentation,
    JourneySnapshot,
)
from services.canonical_journey_itinerary_service import (
    CAPABILITY_PHASE,
    PHASE_LABEL,
    CONNECTION_COLLECTION,
    FARE_BRAND_COLLECTION,
    JOURNEY_COLLECTION,
    JOURNEY_COLLECTIONS,
    LEG_COLLECTION,
    OPTION_COLLECTION,
    PRESENTATION_COLLECTION,
    SEGMENT_COLLECTION,
    SERVICE_COLLECTION,
    SNAPSHOT_COLLECTION,
    CanonicalJourneyError,
    CanonicalJourneyItineraryService,
    FinalizedJourneySnapshotError,
)
from phase_assertions import assert_application_phase_at_least
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


MINIMUM_PHASE = "phase_56_0_canonical_journey_itinerary_representation_foundation"
ROOT = Path(__file__).resolve().parents[2]
AGENCY_AGENT_HEADERS = {"X-Demo-User-Email": "agency.agent@aeroassist.dev"}


def require_text(path: Path, text: str) -> None:
    if text not in path.read_text(encoding="utf-8"):
        raise AssertionError(f"{path.relative_to(ROOT)} missing expected text: {text}")


def verify_static_contracts() -> None:
    if CAPABILITY_PHASE != MINIMUM_PHASE:
        raise AssertionError(f"Unexpected Phase 56.0 capability provenance: {CAPABILITY_PHASE}")
    assert_application_phase_at_least(PHASE_LABEL, MINIMUM_PHASE, source="Phase 56.0 service")
    expected_collections = {
        JOURNEY_COLLECTION,
        OPTION_COLLECTION,
        LEG_COLLECTION,
        SEGMENT_COLLECTION,
        CONNECTION_COLLECTION,
        FARE_BRAND_COLLECTION,
        SERVICE_COLLECTION,
        PRESENTATION_COLLECTION,
        SNAPSHOT_COLLECTION,
    }
    if set(JOURNEY_COLLECTIONS) != expected_collections:
        raise AssertionError("Journey collection constants are incomplete.")
    if not expected_collections.issubset(set(AGENCY_OWNED_COLLECTIONS)):
        raise AssertionError("Journey collections are not registered as agency-owned.")

    samples = [
        JourneyRepresentation(agency_id="agency", journey_reference="JNY-MODEL", title="Model", source_entity_type="manual_entry", source_entity_id="source"),
        JourneyItineraryOption(agency_id="agency", journey_id="journey", option_number=1, option_code="OPT-01", title="Option", source_entity_type="manual_entry", source_entity_id="source"),
        JourneyLegRepresentation(agency_id="agency", journey_id="journey", itinerary_option_id="option", leg_number=1),
        JourneySegmentRepresentation(agency_id="agency", journey_id="journey", itinerary_option_id="option", segment_number=1, source_entity_type="trip_segment", source_entity_id="trip"),
        JourneyConnectionRepresentation(agency_id="agency", journey_id="journey", itinerary_option_id="option", inbound_segment_id="one", outbound_segment_id="two"),
        JourneyFareBrandPresentation(agency_id="agency", journey_id="journey", itinerary_option_id="option", brand_name="Flex"),
        JourneyServicePresentation(agency_id="agency", journey_id="journey", service_code="WCHC", service_name="Wheelchair"),
        JourneyPresentationConfiguration(agency_id="agency", journey_id="journey"),
        JourneySnapshot(agency_id="agency", journey_id="journey", version_number=1, source_entity_type="trip", source_entity_id="trip", content_hash="hash"),
    ]
    if not all(item.id and item.metadata_only for item in samples):
        raise AssertionError("Journey model defaults are incomplete.")
    if not samples[3].source_segment_remains_canonical or not samples[-1].physical_deletion_disabled:
        raise AssertionError("Journey source-truth or snapshot safety defaults are incomplete.")

    database_text = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "journey_representations_source_lookup",
        "journey_itinerary_options_chronology_lookup",
        "journey_leg_representations_chronology_lookup",
        "journey_segment_representations_chronology_lookup",
        "journey_segment_representations_source_lookup",
        "journey_connection_representations_segment_pair_lookup",
        "journey_fare_brand_presentations_option_lookup",
        "journey_service_presentations_scope_lookup",
        "journey_presentation_configurations_journey_unique",
        "journey_snapshots_version_unique",
        "journey_snapshots_hash_lookup",
        "journey_snapshots_finalization_lookup",
    ]:
        if index_name not in database_text:
            raise AssertionError(f"Mongo index registration missing {index_name}")

    paths = get("/openapi.json").get("paths") or {}
    expected_routes = [
        ("/api/platform/journey-engine", "get"),
        ("/api/platform/journey-engine/summary", "get"),
        ("/api/platform/journey-engine/filters", "get"),
        ("/api/platform/journey-engine/journeys", "get"),
        ("/api/platform/journey-engine/journeys/{journey_id}", "get"),
        ("/api/platform/journey-engine/journeys/{journey_id}/snapshots", "get"),
        ("/api/agencies/{agency_id}/journeys", "get"),
        ("/api/agencies/{agency_id}/journeys", "post"),
        ("/api/agencies/{agency_id}/journeys/summary", "get"),
        ("/api/agencies/{agency_id}/journeys/{journey_id}", "get"),
        ("/api/agencies/{agency_id}/journeys/{journey_id}", "put"),
        ("/api/agencies/{agency_id}/journeys/{journey_id}/options", "post"),
        ("/api/agencies/{agency_id}/journeys/{journey_id}/legs", "post"),
        ("/api/agencies/{agency_id}/journeys/{journey_id}/segments", "post"),
        ("/api/agencies/{agency_id}/journeys/{journey_id}/connections", "post"),
        ("/api/agencies/{agency_id}/journeys/{journey_id}/fare-brands", "post"),
        ("/api/agencies/{agency_id}/journeys/{journey_id}/services", "post"),
        ("/api/agencies/{agency_id}/journeys/{journey_id}/presentation", "put"),
        ("/api/agencies/{agency_id}/journeys/{journey_id}/snapshots", "post"),
        ("/api/agencies/{agency_id}/journeys/{journey_id}/snapshots", "get"),
        ("/api/agencies/{agency_id}/journeys/from-trip/{trip_id}", "post"),
        ("/api/agencies/{agency_id}/journeys/from-offer/{offer_id}", "post"),
        ("/api/agencies/{agency_id}/journeys/from-booking/{booking_id}", "post"),
        ("/api/agencies/{agency_id}/journeys/from-ticket/{ticket_id}", "post"),
        ("/api/agencies/{agency_id}/journeys/from-emd/{emd_id}", "post"),
    ]
    for path, method in expected_routes:
        assert_openapi_path(paths, path, method)
    if any(path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")) for path in paths):
        raise AssertionError("Non-canonical route root is present.")

    for path, text in [
        (ROOT / "frontend/src/App.jsx", "/platform/journey-engine"),
        (ROOT / "frontend/src/App.jsx", "/agency/journeys"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Journey Engine"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Journeys"),
        (ROOT / "frontend/src/pages/platform/JourneyEnginePage.jsx", "canonical journey projections"),
        (ROOT / "frontend/src/pages/agency/JourneyWorkspacePage.jsx", "Create Journey Representation"),
        (ROOT / "frontend/src/pages/agency/JourneyWorkspacePage.jsx", "Create immutable snapshot"),
        (ROOT / "frontend/src/pages/agency/TripWorkspacesPage.jsx", "Open Journey View"),
        (ROOT / "frontend/src/pages/agency/OfferWorkspaceMetadataPage.jsx", "Open Journey View"),
        (ROOT / "frontend/src/pages/agency/BookingWorkspaceMetadataPage.jsx", "Open Journey View"),
        (ROOT / "frontend/src/pages/agency/TicketWorkspaceMetadataPage.jsx", "View Journey Snapshot"),
        (ROOT / "frontend/src/pages/agency/EmdWorkspaceMetadataPage.jsx", "Open Journey View"),
        (ROOT / "docs/architecture/canonical-journey-itinerary-representation-foundation.md", "Source-Truth Boundary"),
        (ROOT / "docs/architecture/current-model-inventory.md", "JourneySegmentRepresentation"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/api/agencies/{agency_id}/journeys"),
        (ROOT / "README.md", "Phase 56.0 Canonical Journey"),
        (ROOT / "BUILD_PHASES.md", "Implemented Phase 56.0"),
    ]:
        require_text(path, text)

    service_text = (ROOT / "backend/services/canonical_journey_itinerary_service.py").read_text(encoding="utf-8").lower()
    for rejected in ["import requests", "urllib.request", "openai", "backgroundtasks", "send_email", "send_sms", "stripe", "selenium", "playwright"]:
        if rejected in service_text:
            raise AssertionError(f"Forbidden execution semantic found in Journey service: {rejected}")


async def verify_service_behavior() -> None:
    db = Database()
    service = CanonicalJourneyItineraryService(db)
    user = {"id": "journey-agent", "email": "agent@example.com"}

    created = await service.create_journey({
        "agency_id": "agency-a",
        "title": "SOF to JFK service journey",
        "journey_type": "one_way",
        "source_entity_type": "manual_entry",
        "source_entity_id": "manual-source",
        "passenger_ids": ["passenger-a"],
        "metadata": {"private_source_location": "must-not-leak"},
    }, user, agency_id="agency-a")
    journey = created["journey"]
    if journey.get("data_completeness_status") != "incomplete" or not journey.get("manual_review_required"):
        raise AssertionError("Unknown journey data did not create an incomplete manual-review state.")
    option = (await service.create_option("agency-a", journey["id"], {"title": "LH via FRA", "source_provenance": {"provenance_type": "itinerary_text_parser", "data_state": "imported", "verified": False}}, user))["itinerary_option"]
    leg = (await service.create_leg("agency-a", journey["id"], {"itinerary_option_id": option["id"], "presentation_label": "Outbound"}, user))["leg"]
    first = (await service.create_segment("agency-a", journey["id"], {
        "itinerary_option_id": option["id"], "leg_id": leg["id"], "source_entity_type": "structured_import", "source_entity_id": "manual-source", "source_segment_id": "source-segment-1", "segment_number": 1,
        "marketing_carrier_code": "LH", "operating_carrier_code": "LH", "marketing_flight_number": "1703", "origin_airport_code": "SOF", "destination_airport_code": "FRA", "departure_utc": "2026-09-01T06:00:00Z", "arrival_utc": "2026-09-01T08:00:00Z",
        "source_provenance": {"provenance_type": "structured_import", "data_state": "imported", "verified": False},
    }, user))["segment"]
    second = (await service.create_segment("agency-a", journey["id"], {
        "itinerary_option_id": option["id"], "leg_id": leg["id"], "source_entity_type": "structured_import", "source_entity_id": "manual-source", "source_segment_id": "source-segment-2", "segment_number": 2,
        "marketing_carrier_code": "LH", "operating_carrier_code": "UA", "marketing_flight_number": "400", "origin_airport_code": "FRA", "destination_airport_code": "JFK", "departure_utc": "2026-09-01T09:30:00Z", "arrival_utc": "2026-09-01T17:00:00Z",
    }, user))["segment"]
    connection = (await service.create_connection("agency-a", journey["id"], {"itinerary_option_id": option["id"], "inbound_segment_id": first["id"], "outbound_segment_id": second["id"]}, user))["connection"]
    if connection.get("connection_minutes") != 90 or connection.get("airport_change_required"):
        raise AssertionError(f"Deterministic connection calculation failed: {connection}")
    if not second.get("codeshare_indicator") or second.get("source_segment_remains_canonical") is not True:
        raise AssertionError("Codeshare or canonical-source projection metadata is missing.")

    await service.create_fare_brand("agency-a", journey["id"], {"itinerary_option_id": option["id"], "brand_name": "Economy Flex", "currency": "EUR", "total_price": 520.0, "baggage_summary": "One checked bag", "data_status": "normalized"}, user)
    await service.create_service_presentation("agency-a", journey["id"], {"itinerary_option_id": option["id"], "passenger_id": "passenger-a", "segment_id": first["id"], "service_code": "WCHC", "service_name": "Wheelchair to cabin seat", "approval_required": True, "document_required": False, "client_safe_summary": "Wheelchair assistance requested.", "internal_summary": "Internal operational handling instruction."}, user)
    await service.set_presentation("agency-a", journey["id"], {"client_safe_mode": True, "show_internal_information": True}, user)
    complete = await service.get_complete_journey("agency-a", journey["id"])
    if len(complete["fare_brands"]) != 1 or len(complete["services"]) != 1 or complete["presentation"].get("show_internal_information") is not False:
        raise AssertionError("Fare, service, or presentation configuration attachment failed.")
    refreshed_leg = complete["legs"][0]
    if refreshed_leg.get("elapsed_minutes") != 660 or refreshed_leg.get("connection_ids") != [connection["id"]]:
        raise AssertionError("Leg chronology or connection aggregation failed.")
    summary = await service.summary(agency_id="agency-a")
    if summary.get("journey_leg_count") != 1 or summary.get("fare_brand_presentation_count") != 1 or summary.get("service_presentation_count") != 1:
        raise AssertionError("Journey readiness summary is missing leg, fare-brand, or service counts.")
    client_safe = await service.get_complete_journey("agency-a", journey["id"], client_safe=True)
    if "internal_summary" in str(client_safe) or "must-not-leak" in str(client_safe) or client_safe["presentation"].get("show_internal_information") is not False:
        raise AssertionError("Client-safe Journey projection leaked restricted internal data.")

    snapshot = (await service.create_snapshot("agency-a", journey["id"], {"snapshot_type": "journey_updated", "finalize": True}, user))["snapshot"]
    if not snapshot.get("immutable") or not snapshot.get("finalized_at") or len(snapshot.get("content_hash") or "") != 64:
        raise AssertionError("Immutable Journey snapshot creation failed.")
    try:
        await service.update_snapshot("agency-a", journey["id"], snapshot["id"], {"metadata": {"illegal": True}}, user)
    except FinalizedJourneySnapshotError:
        pass
    else:
        raise AssertionError("Finalized Journey snapshot mutation was not rejected.")
    try:
        await service.get_complete_journey("agency-b", journey["id"])
    except CanonicalJourneyError:
        pass
    else:
        raise AssertionError("Journey service leaked data across agencies.")
    archived = (await service.archive_journey("agency-a", journey["id"], user))["journey"]
    if archived.get("status") != "archived" or not await service.list_snapshots("agency-a", journey["id"]):
        raise AssertionError("Non-destructive Journey archival failed.")

    await db.collection("trip_dossiers").insert_one({"id": "trip-source", "agency_id": "agency-a", "trip_reference": "TRIP-SOURCE", "trip_title": "Canonical trip source", "trip_type": "return", "primary_client_id": "client-a"})
    await db.collection("trip_segments").insert_one({"id": "trip-segment-1", "agency_id": "agency-a", "trip_id": "trip-source", "segment_order": 1, "origin_airport_code": "SOF", "destination_airport_code": "FRA", "departure_date": "2026-10-01", "departure_time": "08:00", "arrival_date": "2026-10-01", "arrival_time": "09:30", "marketing_airline_code": "LH", "operating_airline_code": "LH"})
    trip_before = copy.deepcopy(await db.collection("trip_dossiers").find_one({"id": "trip-source"}))
    trip_projection = await service.project_from_trip("agency-a", "trip-source", user)
    if trip_projection["segments"][0].get("source_segment_id") != "trip-segment-1" or await db.collection("trip_dossiers").find_one({"id": "trip-source"}) != trip_before:
        raise AssertionError("Trip projection lost source provenance or mutated canonical Trip truth.")

    await db.collection("offer_workspaces").insert_one({"id": "offer-source", "agency_id": "agency-a", "title": "Canonical offer source", "status": "accepted", "currency": "EUR"})
    await db.collection("offer_options").insert_one({"id": "offer-option-source", "agency_id": "agency-a", "workspace_id": "offer-source", "label": "Accepted option", "status": "recommended"})
    await db.collection("offer_builder_segments").insert_one({"id": "offer-segment-source", "agency_id": "agency-a", "option_id": "offer-option-source", "sequence": 1, "marketing_airline_code": "LH", "origin_airport": "SOF", "destination_airport": "FRA", "departure_at": "2026-11-01T06:00:00Z", "arrival_at": "2026-11-01T08:00:00Z"})
    await db.collection("offer_acceptances").insert_one({
        "id": "offer-acceptance-source",
        "agency_id": "agency-a",
        "workspace_id": "offer-source",
        "option_id": "offer-option-source",
        "status": "accepted",
        "accepted_at": "2026-08-01T10:00:00Z",
        "accepted_routing_snapshot_json": {"segments": [{"id": "accepted-segment-source", "sequence": 1, "marketing_airline_code": "LH", "origin_airport": "SOF", "destination_airport": "MUC", "departure_at": "2026-11-01T06:00:00Z", "arrival_at": "2026-11-01T08:00:00Z"}]},
        "accepted_pricing_snapshot_json": {"lines": [{"id": "accepted-price-source", "amount": 240, "currency": "EUR"}]},
        "accepted_fare_bundle_snapshot_json": {"items": [{"id": "accepted-fare-source", "fare_family_name": "Economy Flex"}]},
        "accepted_services_snapshot_json": [{"service_code": "WCHR", "service_name": "Ramp wheelchair assistance"}],
    })
    offer_before = copy.deepcopy(await db.collection("offer_workspaces").find_one({"id": "offer-source"}))
    acceptance_before = copy.deepcopy(await db.collection("offer_acceptances").find_one({"id": "offer-acceptance-source"}))
    offer_projection = await service.project_from_offer("agency-a", "offer-source", user)
    if len(offer_projection["segments"]) != 1 or offer_projection["segments"][0].get("source_segment_id") != "accepted-segment-source":
        raise AssertionError("Offer projection did not reuse the frozen accepted routing snapshot.")
    if offer_projection["journey"].get("metadata", {}).get("accepted_offer_snapshot_reused") is not True:
        raise AssertionError("Offer projection did not retain accepted-snapshot lineage.")
    if await db.collection("offer_workspaces").find_one({"id": "offer-source"}) != offer_before or await db.collection("offer_acceptances").find_one({"id": "offer-acceptance-source"}) != acceptance_before:
        raise AssertionError("Offer projection mutated canonical Offer or accepted-snapshot truth.")

    booking_source = {"id": "booking-source", "agency_id": "agency-a", "workspace_number": "BW-SOURCE", "title": "Booking source", "passenger_ids": ["passenger-a"], "ticket_ids": ["ticket-reference"], "emd_ids": ["emd-reference"], "segments_snapshot_json": [{"id": "booking-segment-source", "origin_airport": "SOF", "destination_airport": "MUC", "departure_at": "2026-12-01T06:00:00Z", "arrival_at": "2026-12-01T08:00:00Z"}]}
    await db.collection("booking_workspaces").insert_one(booking_source)
    booking_before = copy.deepcopy(await db.collection("booking_workspaces").find_one({"id": "booking-source"}))
    booking_projection = await service.project_from_booking("agency-a", "booking-source", user)
    if booking_projection["segments"][0].get("source_segment_id") != "booking-segment-source" or booking_projection["source_references"].get("ticket_reference_ids") != ["ticket-reference"]:
        raise AssertionError("Booking projection or ticket reference projection failed.")
    if await db.collection("booking_workspaces").find_one({"id": "booking-source"}) != booking_before:
        raise AssertionError("Booking projection mutated frozen source metadata.")


def ensure_second_agency(agencies: list[dict]) -> str:
    if len(agencies) > 1:
        return agencies[1]["id"]
    slug = f"journey-isolation-{int(time.time() * 1000)}"
    return post("/api/agencies", {"name": "Journey Isolation Agency", "slug": slug, "legal_name": "Journey Isolation Agency Ltd", "status": "active", "subscription_status": "trial", "default_currency": "EUR", "country": "BG", "timezone": "UTC"}, OWNER_HEADERS, 201)["agency"]["id"]


def verify_live_api() -> None:
    health = get("/api/health")
    assert_application_phase_at_least(health.get("phase"), MINIMUM_PHASE, source="health")
    readiness = get("/api/readiness")
    section = readiness.get("canonical_journey_itinerary_representation_foundation") or {}
    for key in [
        "canonical_journey_itinerary_representation_enabled",
        "canonical_operational_entities_reused",
        "duplicate_operational_entities_disabled",
        "journey_segment_projection_enabled",
        "immutable_journey_snapshots_enabled",
        "finalized_snapshot_mutation_disabled",
        "agency_isolation_enabled",
        "client_safe_projection_enabled",
        "live_availability_disabled",
        "live_pricing_disabled",
        "provider_connectivity_disabled",
        "external_api_calls_disabled",
        "automatic_publication_disabled",
        "metadata_only",
    ]:
        if section.get(key) is not True:
            raise AssertionError(f"Journey readiness flag {key} is not enabled/disabled as expected: {section.get(key)}")
    for key in ["journey_count", "itinerary_option_count", "journey_leg_count", "journey_segment_count", "connection_count", "fare_brand_presentation_count", "service_presentation_count", "snapshot_count", "finalized_snapshot_count", "incomplete_journey_count", "manual_review_journey_count"]:
        if not isinstance(section.get(key), int):
            raise AssertionError(f"Journey readiness counter {key} is missing: {section.get(key)}")

    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires the seeded demo agency.")
    agency_id = agencies[0]["id"]
    other_agency_id = ensure_second_agency(agencies)
    journey = post(f"/api/agencies/{agency_id}/journeys", {"title": "Live API Journey", "source_entity_type": "manual_entry", "source_entity_id": f"live-{int(time.time() * 1000)}", "passenger_ids": ["passenger-live"]}, OWNER_HEADERS, 201)["journey"]
    option = post(f"/api/agencies/{agency_id}/journeys/{journey['id']}/options", {"title": "Live option"}, OWNER_HEADERS, 201)["itinerary_option"]
    leg = post(f"/api/agencies/{agency_id}/journeys/{journey['id']}/legs", {"itinerary_option_id": option["id"], "presentation_label": "Outbound"}, OWNER_HEADERS, 201)["leg"]
    first = post(f"/api/agencies/{agency_id}/journeys/{journey['id']}/segments", {"itinerary_option_id": option["id"], "leg_id": leg["id"], "source_entity_type": "manual_entry", "source_entity_id": journey["source_entity_id"], "source_segment_id": "live-1", "origin_airport_code": "SOF", "destination_airport_code": "FRA", "departure_utc": "2026-09-01T06:00:00Z", "arrival_utc": "2026-09-01T08:00:00Z"}, OWNER_HEADERS, 201)["segment"]
    second = post(f"/api/agencies/{agency_id}/journeys/{journey['id']}/segments", {"itinerary_option_id": option["id"], "leg_id": leg["id"], "source_entity_type": "manual_entry", "source_entity_id": journey["source_entity_id"], "source_segment_id": "live-2", "origin_airport_code": "FRA", "destination_airport_code": "JFK", "departure_utc": "2026-09-01T09:30:00Z", "arrival_utc": "2026-09-01T17:00:00Z"}, OWNER_HEADERS, 201)["segment"]
    connection = post(f"/api/agencies/{agency_id}/journeys/{journey['id']}/connections", {"itinerary_option_id": option["id"], "inbound_segment_id": first["id"], "outbound_segment_id": second["id"]}, OWNER_HEADERS, 201)["connection"]
    if connection.get("connection_minutes") != 90:
        raise AssertionError("Live Journey API connection calculation was not deterministic.")
    post(f"/api/agencies/{agency_id}/journeys/{journey['id']}/fare-brands", {"itinerary_option_id": option["id"], "brand_name": "Flex", "data_status": "normalized"}, OWNER_HEADERS, 201)
    post(f"/api/agencies/{agency_id}/journeys/{journey['id']}/services", {"itinerary_option_id": option["id"], "service_code": "WCHC", "service_name": "Wheelchair"}, OWNER_HEADERS, 201)
    put(f"/api/agencies/{agency_id}/journeys/{journey['id']}/presentation", {"client_safe_mode": True, "show_internal_information": True}, OWNER_HEADERS, 200)
    snapshot = post(f"/api/agencies/{agency_id}/journeys/{journey['id']}/snapshots", {"snapshot_type": "journey_updated", "finalize": True}, OWNER_HEADERS, 201)["snapshot"]
    request("PUT", f"/api/agencies/{agency_id}/journeys/{journey['id']}/snapshots/{snapshot['id']}", {"metadata": {"illegal": True}}, OWNER_HEADERS, expect=409)
    detail = get(f"/api/agencies/{agency_id}/journeys/{journey['id']}?client_safe=true", OWNER_HEADERS)
    if "internal_summary" in str(detail) or detail.get("duplicate_segment_source_of_truth_disabled") is not True:
        raise AssertionError("Live client-safe projection or source-truth safety flag failed.")
    post(f"/api/agencies/{agency_id}/journeys/{journey['id']}/archive", {}, OWNER_HEADERS, 200)
    snapshots = get(f"/api/agencies/{agency_id}/journeys/{journey['id']}/snapshots", OWNER_HEADERS)
    if snapshots.get("count") != 1:
        raise AssertionError("Non-destructive archive did not preserve the finalized snapshot.")

    request("GET", "/api/platform/journey-engine", None, AGENCY_AGENT_HEADERS, expect=403)
    request("GET", f"/api/agencies/{other_agency_id}/journeys", None, AGENCY_AGENT_HEADERS, expect=403)


def main() -> None:
    verify_static_contracts()
    asyncio.run(verify_service_behavior())
    verify_live_api()
    print("Phase 56.0 canonical journey and itinerary representation smoke passed.")


if __name__ == "__main__":
    main()
