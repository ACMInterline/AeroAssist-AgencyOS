#!/usr/bin/env python3
import asyncio
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS, Database
from models import (
    JourneyCommercialPriceBreakdown,
    JourneyFareBrandChoice,
    JourneyOptionAlternative,
    JourneyOptionComparisonProfile,
    JourneyOptionComparisonResult,
    JourneyOptionComposition,
    JourneyOptionCompositionSnapshot,
    JourneyOptionMetricSnapshot,
    JourneyOptionOfferHandoff,
    JourneyOptionSegmentAssignment,
    JourneyOptionServiceAssessment,
)
from services.canonical_journey_itinerary_service import CanonicalJourneyItineraryService
from services.journey_option_fare_brand_composition_service import (
    ASSIGNMENT_COLLECTION,
    COMPARISON_PROFILE_COLLECTION,
    COMPARISON_RESULT_COLLECTION,
    COMPOSITION_COLLECTION,
    COMPOSITION_COLLECTIONS,
    FARE_CHOICE_COLLECTION,
    HANDOFF_COLLECTION,
    METRIC_COLLECTION,
    OPTION_COLLECTION,
    PHASE_LABEL,
    PRICE_COLLECTION,
    SERVICE_ASSESSMENT_COLLECTION,
    SNAPSHOT_COLLECTION,
    FinalizedCompositionSnapshotError,
    JourneyOptionCompositionError,
    JourneyOptionFareBrandCompositionService,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, request


EXPECTED_PHASE = "phase_56_2_journey_option_fare_brand_composition_workspace_foundation"
ROOT = Path(__file__).resolve().parents[2]
AGENCY_AGENT_HEADERS = {"X-Demo-User-Email": "agency.agent@aeroassist.dev"}


def require_text(path: Path, text: str) -> None:
    if text not in path.read_text(encoding="utf-8"):
        raise AssertionError(f"{path.relative_to(ROOT)} missing expected text: {text}")


def verify_static_contracts() -> None:
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected Phase 56.2 marker: {PHASE_LABEL}")
    expected = {
        COMPOSITION_COLLECTION, OPTION_COLLECTION, ASSIGNMENT_COLLECTION, FARE_CHOICE_COLLECTION, PRICE_COLLECTION,
        METRIC_COLLECTION, SERVICE_ASSESSMENT_COLLECTION, COMPARISON_PROFILE_COLLECTION, COMPARISON_RESULT_COLLECTION,
        SNAPSHOT_COLLECTION, HANDOFF_COLLECTION,
    }
    if set(COMPOSITION_COLLECTIONS) != expected or not expected.issubset(set(AGENCY_OWNED_COLLECTIONS)):
        raise AssertionError("Journey option composition collections are incomplete or not agency-owned.")
    samples = [
        JourneyOptionComposition(agency_id="agency", journey_id="journey", title="Composition"),
        JourneyOptionAlternative(agency_id="agency", composition_id="composition", journey_id="journey", option_code="OPTION-A", display_order=1),
        JourneyOptionSegmentAssignment(agency_id="agency", composition_id="composition", option_id="option", journey_id="journey", source_segment_id="segment", display_order=1),
        JourneyFareBrandChoice(agency_id="agency", composition_id="composition", option_id="option", display_order=1, client_safe_label="Flex"),
        JourneyCommercialPriceBreakdown(agency_id="agency", composition_id="composition", option_id="option", fare_choice_id="fare", currency="EUR"),
        JourneyOptionMetricSnapshot(agency_id="agency", composition_id="composition", option_id="option"),
        JourneyOptionServiceAssessment(agency_id="agency", composition_id="composition", option_id="option", service_code="WCHC"),
        JourneyOptionComparisonProfile(agency_id="agency", composition_id="composition"),
        JourneyOptionComparisonResult(agency_id="agency", composition_id="composition", content_hash="hash"),
        JourneyOptionCompositionSnapshot(agency_id="agency", composition_id="composition", journey_id="journey", snapshot_number=1, content_hash="hash"),
        JourneyOptionOfferHandoff(agency_id="agency", composition_id="composition", snapshot_id="snapshot"),
    ]
    if not all(item.id and item.metadata_only for item in samples):
        raise AssertionError("Journey option composition model defaults are incomplete.")
    if not samples[2].source_segment_remains_canonical or not samples[9].physical_deletion_disabled or not samples[10].provider_execution_disabled:
        raise AssertionError("Canonical-source, snapshot, or provider safety defaults are missing.")

    database_text = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "journey_option_compositions_journey_version_lookup", "journey_option_alternatives_composition_order_lookup",
        "journey_option_segment_assignments_source_lookup", "journey_fare_brand_choices_option_order_lookup",
        "journey_commercial_price_breakdowns_choice_lookup", "journey_option_metric_snapshots_option_lookup",
        "journey_option_service_assessments_service_lookup", "journey_option_comparison_profiles_composition_lookup",
        "journey_option_comparison_results_hash_lookup", "journey_option_composition_snapshots_finalized_lookup",
        "journey_option_offer_handoffs_offer_lookup",
    ]:
        if index_name not in database_text:
            raise AssertionError(f"Missing Mongo index registration: {index_name}")

    service_text = (ROOT / "backend/services/journey_option_fare_brand_composition_service.py").read_text(encoding="utf-8")
    for forbidden in ["requests.get(", "httpx.", "openai", "selenium", "playwright", "backgroundtasks", "celery", "scrape("]:
        if forbidden in service_text.lower():
            raise AssertionError(f"Composition service contains forbidden execution semantics: {forbidden}")
    for required in ["AirlineFareFamilyBrandIntelligenceService", "minimum_connection_time_asserted", "automatic_offer_publication_disabled", "FinalizedCompositionSnapshotError"]:
        if required not in service_text:
            raise AssertionError(f"Composition service missing required contract: {required}")

    require_text(ROOT / "frontend/src/App.jsx", '"/agency/journey-option-composition"')
    require_text(ROOT / "frontend/src/App.jsx", '"/platform/journey-option-compositions"')
    require_text(ROOT / "frontend/src/lib/moduleCatalog.js", "Journey Option Composition")
    require_text(ROOT / "frontend/src/pages/agency/JourneyOptionCompositionWorkspacePage.jsx", "Itinerary option board")
    require_text(ROOT / "frontend/src/pages/agency/JourneyOptionCompositionWorkspacePage.jsx", "No live price, availability")
    require_text(ROOT / "frontend/src/pages/agency/JourneyOptionCompositionWorkspacePage.jsx", "Duplicate fare choice")
    require_text(ROOT / "frontend/src/pages/platform/JourneyOptionCompositionDiagnosticsPage.jsx", "Governance view only")
    require_text(ROOT / "frontend/src/pages/agency/JourneyWorkspacePage.jsx", "Compose itinerary options")
    require_text(ROOT / "frontend/src/pages/agency/OfferWorkspaceMetadataPage.jsx", "Prepare itinerary options")
    require_text(ROOT / "docs/architecture/journey-option-fare-brand-composition-workspace-foundation.md", "3 x 3 Composition Target")


async def build_journey(db: Database, agency_id: str, user: dict) -> tuple[dict, list[dict]]:
    canonical = CanonicalJourneyItineraryService(db)
    journey = (await canonical.create_journey({
        "agency_id": agency_id, "title": "SOF to New York alternatives", "source_entity_type": "travel_request", "source_entity_id": "request-a",
        "origin_airport_code": "SOF", "destination_airport_code": "JFK", "departure_date": "2027-08-01", "passenger_ids": ["passenger-a"],
    }, user, agency_id=agency_id))["journey"]
    segments = []
    route_data = [
        [
            {"source_entity_id": "a-1", "marketing_carrier_code": "LH", "operating_carrier_code": "LH", "marketing_flight_number": "1427", "origin_airport_code": "SOF", "destination_airport_code": "FRA", "departure_utc": "2027-08-01T05:00:00+00:00", "arrival_utc": "2027-08-01T07:00:00+00:00", "departure_local": "2027-08-01T08:00:00+03:00", "arrival_local": "2027-08-01T09:00:00+02:00", "departure_timezone": "Europe/Sofia", "arrival_timezone": "Europe/Berlin", "departure_terminal": "2", "arrival_terminal": "1"},
            {"source_entity_id": "a-2", "marketing_carrier_code": "LH", "operating_carrier_code": "LH", "marketing_flight_number": "400", "origin_airport_code": "FRA", "destination_airport_code": "JFK", "departure_utc": "2027-08-01T22:30:00+00:00", "arrival_utc": "2027-08-02T07:00:00+00:00", "departure_local": "2027-08-02T00:30:00+02:00", "arrival_local": "2027-08-02T03:00:00-04:00", "departure_timezone": "Europe/Berlin", "arrival_timezone": "America/New_York", "departure_terminal": "1", "arrival_terminal": "1"},
        ],
        [
            {"source_entity_id": "b-1", "marketing_carrier_code": "BA", "operating_carrier_code": "BA", "marketing_flight_number": "893", "origin_airport_code": "SOF", "destination_airport_code": "LHR", "departure_utc": "2027-08-01T08:00:00+00:00", "arrival_utc": "2027-08-01T11:00:00+00:00", "departure_local": "2027-08-01T11:00:00+03:00", "arrival_local": "2027-08-01T12:00:00+01:00", "departure_timezone": "Europe/Sofia", "arrival_timezone": "Europe/London", "departure_terminal": "2", "arrival_terminal": "5"},
            {"source_entity_id": "b-2", "marketing_carrier_code": "BA", "operating_carrier_code": "AA", "marketing_flight_number": "1506", "origin_airport_code": "LGW", "destination_airport_code": "JFK", "departure_utc": "2027-08-01T15:00:00+00:00", "arrival_utc": "2027-08-01T23:00:00+00:00", "departure_local": "2027-08-01T16:00:00+01:00", "arrival_local": "2027-08-01T19:00:00-04:00", "departure_timezone": "Europe/London", "arrival_timezone": "America/New_York", "departure_terminal": "N", "arrival_terminal": "8", "codeshare_indicator": True},
        ],
    ]
    for option_index, route in enumerate(route_data, start=1):
        option = (await canonical.create_option(agency_id, journey["id"], {"title": f"Route {option_index}", "source_entity_type": "travel_request", "source_entity_id": "request-a"}, user))["itinerary_option"]
        leg = (await canonical.create_leg(agency_id, journey["id"], {"itinerary_option_id": option["id"], "leg_type": "flight"}, user))["leg"]
        for data in route:
            segment = (await canonical.create_segment(agency_id, journey["id"], {"itinerary_option_id": option["id"], "leg_id": leg["id"], "source_entity_type": "travel_request", **data}, user))["segment"]
            segments.append(segment)
    await canonical.create_service_presentation(agency_id, journey["id"], {
        "service_code": "WCHC", "service_name": "Wheelchair assistance", "passenger_id": "passenger-a",
        "feasibility_status": "unknown", "confirmation_status": "pending", "approval_required": True,
        "SSR_codes": ["WCHC"], "document_required": False,
        "client_safe_summary": "Wheelchair assistance is requested and requires airline confirmation.",
        "internal_summary": "Contact the operating carrier special-assistance desk.",
    }, user)
    return journey, segments


async def seed_governed_fare(db: Database) -> None:
    await db.collection("airline_fare_families").insert_one({
        "id": "family-flex", "airline_id": "airline-lh", "family_code": "FLEX", "family_name": "Economy Flex",
        "fare_family_reference": "AFF-FLEX", "airline_code": "LH", "brand_code": "FLEX", "commercial_name": "Economy Flex",
        "cabin": "economy", "client_safe_label": "Flex", "evidence_link_ids": ["evidence-public", "evidence-restricted"],
        "confidence": "high", "freshness_status": "current", "approval_status": "approved", "publication_status": "published",
        "agency_visibility_status": "all_agencies", "visible_agency_ids": [], "internal_notes": "Restricted platform note",
        "metadata": {"knowledge_version_ids": ["knowledge-version-1"]}, "source_metadata_json": {}, "governance_status": "approved",
        "created_at": "2027-01-01T00:00:00+00:00", "updated_at": "2027-01-01T00:00:00+00:00",
    })
    await db.collection("airline_fare_brand_attributes").insert_one({
        "id": "attribute-change", "attribute_reference": "ATTR-CHANGE", "airline_code": "LH", "fare_family_id": "family-flex",
        "attribute_code": "changeability", "attribute_label": "Changes", "attribute_status": "included", "included": True,
        "client_safe_label": "Changes", "client_safe_value": "Included with conditions", "evidence_link_ids": ["evidence-public"],
        "confidence": "high", "freshness_status": "current", "publication_status": "published", "agency_visibility_status": "all_agencies",
        "created_at": "2027-01-01T00:00:00+00:00", "updated_at": "2027-01-01T00:00:00+00:00",
    })
    await db.collection("airline_baggage_allowance_rules").insert_one({
        "id": "baggage-flex", "baggage_rule_reference": "BAG-FLEX", "airline_code": "LH", "fare_family_id": "family-flex",
        "brand_code": "FLEX", "cabin": "economy", "allowance_status": "supported", "baggage_concept": "piece",
        "cabin_baggage_pieces": 1, "cabin_baggage_weight_kg": 8, "personal_item_included": True,
        "checked_baggage_pieces": 1, "checked_baggage_weight_per_piece_kg": 23, "codeshare_interline_status": "supported",
        "confidence": "high", "freshness_status": "current", "publication_status": "published", "agency_visibility_status": "all_agencies",
        "created_at": "2027-01-01T00:00:00+00:00", "updated_at": "2027-01-01T00:00:00+00:00",
    })
    await db.collection("airline_fare_family_evidence_links").insert_one({
        "id": "evidence-public", "fare_family_evidence_reference": "EVD-PUB", "airline_code": "LH", "target_type": "fare-families", "target_id": "family-flex",
        "evidence_source_id": "source-public", "evidence_status": "approved", "authority_level": "airline_official", "confidence": "high",
        "freshness_status": "current", "accessibility": "agency_visible", "agency_visible": True, "client_visible": True,
        "created_at": "2027-01-01T00:00:00+00:00", "updated_at": "2027-01-01T00:00:00+00:00",
    })
    await db.collection("airline_fare_family_evidence_links").insert_one({
        "id": "evidence-restricted", "fare_family_evidence_reference": "EVD-INT", "airline_code": "LH", "target_type": "fare-families", "target_id": "family-flex",
        "evidence_source_id": "source-internal", "evidence_status": "approved", "authority_level": "internal_observation", "confidence": "medium",
        "freshness_status": "current", "accessibility": "internal_restricted", "agency_visible": False, "client_visible": False,
        "internal_notes": "Never expose", "created_at": "2027-01-01T00:00:00+00:00", "updated_at": "2027-01-01T00:00:00+00:00",
    })


async def verify_service_behavior() -> None:
    db = Database()
    service = JourneyOptionFareBrandCompositionService(db)
    user = {"id": "agent-a", "email": "agent-a@example.test"}
    journey, segments = await build_journey(db, "agency-a", user)
    await seed_governed_fare(db)

    detail = await service.create_from_journey("agency-a", journey["id"], {"request_id": "request-a"}, user)
    composition = detail["composition"]
    options = detail["options"]
    if len(options) != 2 or len(detail["segment_assignments"]) != 4:
        raise AssertionError("Composition creation did not project canonical options and segment references.")
    try:
        await service.get_composition("agency-b", composition["id"])
    except JourneyOptionCompositionError:
        pass
    else:
        raise AssertionError("Composition leaked across agencies.")

    first, second = options
    first_metric = await service._latest_metric("agency-a", composition["id"], first["id"])
    second_metric = await service._latest_metric("agency-a", composition["id"], second["id"])
    if not first_metric.get("overnight_indicator") or not first_metric.get("date_change_indicator"):
        raise AssertionError("Overnight or date-change detection failed.")
    if not second_metric.get("airport_change_indicator") or not second_metric.get("interline_indicator") or not second_metric.get("codeshare_indicator"):
        raise AssertionError("Airport-change, interline, or codeshare metric detection failed.")
    if first_metric.get("shortest_connection_minutes") != 930 or first_metric.get("minimum_connection_time_asserted"):
        raise AssertionError("Deterministic connection calculation or MCT boundary failed.")

    try:
        await service.assign_segments("agency-a", composition["id"], first["id"], {"segment_ids": [segments[0]["id"]]}, user)
    except JourneyOptionCompositionError:
        pass
    else:
        raise AssertionError("Duplicate active segment assignment was not rejected.")

    cloned = (await service.clone_option("agency-a", composition["id"], first["id"], {"client_safe_label": "Option C"}, user))["option"]
    active = await service._active_options("agency-a", composition["id"])
    reordered = await service.reorder_options("agency-a", composition["id"], [cloned["id"], second["id"], first["id"]], user)
    if reordered["items"][0]["id"] != cloned["id"]:
        raise AssertionError("Option cloning or ordering failed.")

    imported = (await service.import_fare_brand("agency-a", composition["id"], first["id"], {"fare_family_id": "family-flex", "booking_class": "Y"}, user))["fare_brand_choice"]
    if imported.get("manual_entry") or imported.get("baggage_summary") != "personal item included; 1 cabin bag up to 8 kg; 1 checked bag up to 23 kg each":
        raise AssertionError("Governed fare-brand or baggage import failed.")
    if imported.get("evidence_refs") != ["evidence-public"] or "evidence-restricted" in str(imported):
        raise AssertionError("Restricted fare-brand evidence was not sanitized.")
    manual = (await service.create_manual_fare_brand("agency-a", composition["id"], first["id"], {"client_safe_label": "Manual Light", "baggage_summary": "Unknown"}, user))["fare_brand_choice"]
    if not manual.get("manual_entry") or manual.get("uncertainty_status") != "requires_review":
        raise AssertionError("Manual fare choice did not preserve review-required uncertainty.")
    ordered_fares = await service.reorder_fare_brands("agency-a", composition["id"], first["id"], [manual["id"], imported["id"]], user)
    if ordered_fares["items"][0]["id"] != manual["id"]:
        raise AssertionError("Fare-brand ordering failed.")
    duplicated = (await service.duplicate_fare_brand("agency-a", composition["id"], first["id"], imported["id"], {"client_safe_label": "Flex copy"}, user))["fare_brand_choice"]
    if duplicated["id"] == imported["id"] or duplicated.get("source_provenance", {}).get("cloned_from_fare_choice_id") != imported["id"]:
        raise AssertionError("Fare-brand duplication did not preserve source provenance.")
    await service.archive_fare_brand("agency-a", composition["id"], first["id"], duplicated["id"], user)
    restored = (await service.restore_fare_brand("agency-a", composition["id"], first["id"], duplicated["id"], user))["fare_brand_choice"]
    if restored.get("archived_at"):
        raise AssertionError("Fare-brand archive or restore failed.")

    priced = await service.set_price_breakdown("agency-a", composition["id"], first["id"], imported["id"], {
        "currency": "EUR", "base_amount": 500, "tax_amount": 120, "ancillary_amount": 25, "service_fee": 30,
        "ticketing_fee": 10, "assistance_fee": 15, "markup_amount": 20, "discount_amount": 20, "total_selling_amount": 700,
        "source_type": "agency_manual", "source_ref": "quote-a", "validity_until": "2027-07-31T18:00:00+00:00",
    }, user)
    if priced["price_breakdown"].get("total_selling_amount") != 700 or not priced.get("arithmetic_valid"):
        raise AssertionError("Price arithmetic validation failed.")
    try:
        await service.set_price_breakdown("agency-a", composition["id"], first["id"], manual["id"], {"currency": "EUR", "base_amount": 100, "tax_amount": 10, "total_selling_amount": 999}, user)
    except JourneyOptionCompositionError:
        pass
    else:
        raise AssertionError("Invalid commercial total was accepted.")
    try:
        await service.set_price_breakdown("agency-a", composition["id"], first["id"], imported["id"], {"currency": "USD", "base_amount": 500, "tax_amount": 120, "total_selling_amount": 620}, user)
    except JourneyOptionCompositionError:
        pass
    else:
        raise AssertionError("Currency change without conversion metadata was accepted.")

    assessments = await service.project_service_assessments("agency-a", composition["id"], user)
    if not assessments["items"] or not all(item.get("advisory_only") for item in assessments["items"]):
        raise AssertionError("Passenger service advisory projection failed.")
    if not any(item.get("feasibility_status") == "unknown" and item.get("airline_confirmation_required") for item in assessments["items"]):
        raise AssertionError("Unknown/manual-review service handling failed.")

    comparison = (await service.generate_comparison("agency-a", composition["id"]))["comparison_result"]
    if not comparison.get("structured_rows") or not comparison.get("human_readable_rows") or not comparison.get("unsupported_recommendation_disabled"):
        raise AssertionError("Deterministic comparison generation failed.")
    if "baggage" not in comparison.get("unknown_dimensions", []):
        raise AssertionError("Unknown baggage state was not retained in comparison output.")
    preferred = await service.select_preferred_option("agency-a", composition["id"], {"option_id": first["id"], "fare_choice_id": imported["id"], "internal_decision_notes": "Agent review", "client_rationale": "Best timing for this passenger."}, user)
    if preferred["composition"].get("preferred_option_id") != first["id"] or preferred.get("automatic_recommendation") is not False:
        raise AssertionError("Explicit preferred-option selection failed.")

    snapshot = (await service.create_snapshot("agency-a", composition["id"], {"finalize": True}, user))["snapshot"]
    if not snapshot.get("finalized") or len(snapshot.get("content_hash") or "") != 64:
        raise AssertionError("Immutable composition snapshot creation failed.")
    try:
        await service.update_snapshot("agency-a", composition["id"], snapshot["id"], {"metadata": {"changed": True}})
    except FinalizedCompositionSnapshotError:
        pass
    else:
        raise AssertionError("Finalized composition snapshot mutation was not rejected.")

    await db.collection("offer_workspaces_v2").insert_one({"id": "offer-a", "agency_id": "agency-a", "offer_reference": "OFF-A", "offer_title": "Draft offer", "offer_status": "draft", "created_at": "2027-01-01T00:00:00+00:00", "updated_at": "2027-01-01T00:00:00+00:00"})
    preview = await service.preview_offer_handoff("agency-a", composition["id"], {"snapshot_id": snapshot["id"], "offer_workspace_id": "offer-a"})
    if not preview.get("can_apply") or preview.get("automatic_action_performed") is not False or "book" not in preview["preview"]["prohibited_actions"]:
        raise AssertionError("Offer handoff preview boundary failed.")
    handoff = await service.apply_offer_handoff("agency-a", composition["id"], {"snapshot_id": snapshot["id"], "offer_workspace_id": "offer-a"}, user)
    if handoff.get("offer_records_mutated") is not False or handoff["offer_handoff"].get("created_records") or handoff.get("provider_execution_performed") is not False:
        raise AssertionError("Explicit handoff trace performed an out-of-scope action.")

    safe = await service.get_composition("agency-a", composition["id"], client_safe=True)
    if "internal_decision_notes" in str(safe) or "internal_agent_notes" in str(safe) or "Never expose" in str(safe):
        raise AssertionError("Client-safe projection leaked internal composition content.")
    dashboard = await service.dashboard()
    if dashboard.get("summary", {}).get("composition_count") != 1 or not dashboard.get("platform_diagnostics_read_only"):
        raise AssertionError("Platform composition diagnostics failed.")
    flags = service.safety_flags()
    for key in ["live_pricing_disabled", "live_availability_disabled", "provider_connectivity_disabled", "external_api_calls_disabled", "scraping_disabled", "ai_disabled", "background_workers_disabled", "automatic_offer_publication_disabled"]:
        if flags.get(key) is not True:
            raise AssertionError(f"Safety flag is missing: {key}")


def ensure_second_agency(agencies: list[dict]) -> str:
    if len(agencies) > 1:
        return agencies[1]["id"]
    slug = f"journey-composition-isolation-{int(time.time() * 1000)}"
    return post("/api/agencies", {"name": "Journey Composition Isolation", "slug": slug, "legal_name": "Journey Composition Isolation Ltd", "status": "active", "subscription_status": "trial", "default_currency": "EUR", "country": "BG", "timezone": "UTC"}, OWNER_HEADERS, 201)["agency"]["id"]


def verify_live_api() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")
    readiness = get("/api/readiness")
    section = readiness.get("journey_option_fare_brand_composition_workspace_foundation") or {}
    for key in [
        "journey_option_fare_brand_composition_enabled", "option_compositions_collection_enabled", "itinerary_alternatives_enabled",
        "segment_assignment_projection_enabled", "fare_brand_choice_composition_enabled", "manual_fare_brand_entry_enabled",
        "governed_fare_brand_import_enabled", "commercial_price_breakdown_enabled", "deterministic_price_arithmetic_validation_enabled",
        "deterministic_journey_metrics_enabled", "special_service_assessment_projection_enabled", "client_internal_content_separation_enabled",
        "immutable_composition_snapshots_enabled", "finalized_snapshot_mutation_disabled", "offer_handoff_preview_enabled",
        "explicit_offer_handoff_enabled", "automatic_offer_publication_disabled", "live_pricing_disabled", "live_availability_disabled",
        "provider_connectivity_disabled", "external_api_calls_disabled", "scraping_disabled", "ai_disabled", "background_workers_disabled", "metadata_only",
    ]:
        if section.get(key) is not True:
            raise AssertionError(f"Composition readiness flag missing: {key}={section.get(key)}")
    for key in [
        "composition_count", "active_composition_count", "incomplete_composition_count", "review_required_composition_count",
        "itinerary_option_count", "fare_brand_choice_count", "manual_fare_brand_choice_count", "imported_fare_brand_choice_count",
        "price_breakdown_count", "service_assessment_count", "blocking_warning_count", "comparison_result_count",
        "snapshot_count", "finalized_snapshot_count", "offer_handoff_count",
    ]:
        if not isinstance(section.get(key), int):
            raise AssertionError(f"Composition readiness counter missing: {key}")
    if section.get("readiness_required") is not False:
        raise AssertionError("Composition readiness must remain diagnostic-only.")

    paths = get("/openapi.json").get("paths") or {}
    for path, method in [
        ("/api/agencies/{agency_id}/journey-option-compositions", "get"),
        ("/api/agencies/{agency_id}/journey-option-compositions", "post"),
        ("/api/agencies/{agency_id}/journey-option-compositions/from-journey/{journey_id}", "post"),
        ("/api/agencies/{agency_id}/journey-option-compositions/{composition_id}/options", "post"),
        ("/api/agencies/{agency_id}/journey-option-compositions/{composition_id}/options/{option_id}/segments", "post"),
        ("/api/agencies/{agency_id}/journey-option-compositions/{composition_id}/options/{option_id}/fare-brands/import", "post"),
        ("/api/agencies/{agency_id}/journey-option-compositions/{composition_id}/options/{option_id}/fare-brands/{fare_choice_id}/clone", "post"),
        ("/api/agencies/{agency_id}/journey-option-compositions/{composition_id}/compare", "post"),
        ("/api/agencies/{agency_id}/journey-option-compositions/{composition_id}/snapshots", "post"),
        ("/api/agencies/{agency_id}/journey-option-compositions/{composition_id}/offer-handoff/preview", "post"),
        ("/api/platform/journey-option-compositions", "get"),
        ("/api/platform/journey-option-compositions/comparison-dimensions", "get"),
        ("/api/platform/journey-option-compositions/validation-codes", "get"),
    ]:
        assert_openapi_path(paths, path, method)

    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires the seeded demo agency.")
    agency_id = agencies[0]["id"]
    other_agency_id = ensure_second_agency(agencies)
    journey = post(f"/api/agencies/{agency_id}/journeys", {"title": f"Live composition {int(time.time())}", "source_entity_type": "manual_entry", "source_entity_id": f"composition-{int(time.time())}"}, OWNER_HEADERS, 201)["journey"]
    option = post(f"/api/agencies/{agency_id}/journeys/{journey['id']}/options", {"title": "Live route", "source_entity_type": "manual_entry", "source_entity_id": journey["id"]}, OWNER_HEADERS, 201)["itinerary_option"]
    segment = post(f"/api/agencies/{agency_id}/journeys/{journey['id']}/segments", {
        "itinerary_option_id": option["id"], "source_entity_type": "manual_entry", "source_entity_id": "live-segment",
        "marketing_carrier_code": "LH", "operating_carrier_code": "LH", "marketing_flight_number": "400",
        "origin_airport_code": "FRA", "destination_airport_code": "JFK",
        "departure_utc": "2027-12-01T10:00:00+00:00", "arrival_utc": "2027-12-01T18:00:00+00:00",
    }, OWNER_HEADERS, 201)["segment"]
    composition = post(f"/api/agencies/{agency_id}/journey-option-compositions/from-journey/{journey['id']}", {}, OWNER_HEADERS, 201)["composition"]
    detail = get(f"/api/agencies/{agency_id}/journey-option-compositions/{composition['id']}", OWNER_HEADERS)
    if not detail.get("options") or not detail.get("segment_assignments") or detail["segment_assignments"][0].get("source_segment_id") != segment["id"]:
        raise AssertionError("Live composition creation or canonical segment assignment failed.")
    if get("/api/platform/journey-option-compositions", OWNER_HEADERS).get("platform_diagnostics_read_only") is not True:
        raise AssertionError("Platform composition diagnostics failed.")
    request("GET", "/api/platform/journey-option-compositions", None, AGENCY_AGENT_HEADERS, expect=403)
    request("GET", f"/api/agencies/{other_agency_id}/journey-option-compositions", None, AGENCY_AGENT_HEADERS, expect=403)


def main() -> None:
    verify_static_contracts()
    asyncio.run(verify_service_behavior())
    verify_live_api()
    print("Phase 56.2 journey option and fare brand composition workspace smoke passed.")


if __name__ == "__main__":
    main()
