#!/usr/bin/env python3
import asyncio
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS, Database
from models import (
    JourneyComparisonConnectionProjection,
    JourneyComparisonDimension,
    JourneyComparisonFareBrandProjection,
    JourneyComparisonOptionProjection,
    JourneyComparisonPresentation,
    JourneyComparisonResult,
    JourneyComparisonSegmentProjection,
    JourneyComparisonServiceSuitabilityProjection,
    JourneyPresentationConfiguration,
    JourneyPresentationContentBlock,
    JourneyPresentationHandoff,
    JourneyPresentationReview,
    JourneyPresentationSnapshot,
)
from routers import agency_journey_comparison_presentations, platform_journey_comparison_presentations
from services.journey_comparison_client_presentation_service import (
    CONNECTION_COLLECTION,
    CONTENT_COLLECTION,
    DIMENSION_COLLECTION,
    FARE_COLLECTION,
    HANDOFF_COLLECTION,
    OPTION_COLLECTION,
    PHASE_LABEL,
    PRESENTATION_COLLECTION,
    PRESENTATION_COLLECTIONS,
    RESULT_COLLECTION,
    REVIEW_COLLECTION,
    SEGMENT_COLLECTION,
    SERVICE_COLLECTION,
    SNAPSHOT_COLLECTION,
    FinalizedJourneyPresentationSnapshotError,
    JourneyComparisonClientPresentationService,
    JourneyComparisonPresentationError,
)
from services.journey_option_fare_brand_composition_service import JourneyOptionFareBrandCompositionService
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, request
from smoke_journey_option_fare_brand_composition_workspace_foundation import build_journey, seed_governed_fare


EXPECTED_PHASE = "phase_56_3_journey_comparison_client_presentation_foundation"
ROOT = Path(__file__).resolve().parents[2]
AGENCY_AGENT_HEADERS = {"X-Demo-User-Email": "agency.agent@aeroassist.dev"}


def require_text(path: Path, text: str) -> None:
    if text not in path.read_text(encoding="utf-8"):
        raise AssertionError(f"{path.relative_to(ROOT)} missing expected text: {text}")


def verify_static_contracts() -> None:
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected Phase 56.3 marker: {PHASE_LABEL}")
    if not agency_journey_comparison_presentations.router or not platform_journey_comparison_presentations.router:
        raise AssertionError("Journey comparison routers did not import.")

    expected = set(PRESENTATION_COLLECTIONS)
    if len(expected) != 13 or not expected.issubset(set(AGENCY_OWNED_COLLECTIONS)):
        raise AssertionError("Phase 56.3 collections are incomplete or not agency-owned.")
    models = [
        JourneyComparisonPresentation, JourneyComparisonOptionProjection, JourneyComparisonSegmentProjection,
        JourneyComparisonConnectionProjection, JourneyComparisonFareBrandProjection,
        JourneyComparisonServiceSuitabilityProjection, JourneyComparisonDimension, JourneyComparisonResult,
        JourneyPresentationContentBlock, JourneyPresentationConfiguration, JourneyPresentationSnapshot,
        JourneyPresentationReview, JourneyPresentationHandoff,
    ]
    if any("metadata_only" not in model.model_fields for model in models):
        raise AssertionError("Phase 56.3 model metadata-only defaults are incomplete.")
    if not JourneyComparisonResult.model_fields["automatic_preferred_option_disabled"].default:
        raise AssertionError("Automatic preferred-option selection is not disabled by model default.")
    if not JourneyPresentationSnapshot.model_fields["physical_deletion_disabled"].default:
        raise AssertionError("Presentation snapshot physical deletion is not disabled.")

    database_text = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "journey_comparison_presentations_composition_status_lookup",
        "journey_comparison_option_projections_order_lookup",
        "journey_comparison_segment_projections_order_lookup",
        "journey_comparison_connection_projections_review_lookup",
        "journey_comparison_fare_brand_projections_source_lookup",
        "journey_comparison_service_suitability_status_lookup",
        "journey_comparison_dimensions_code_lookup",
        "journey_comparison_results_hash_lookup",
        "journey_presentation_content_blocks_visibility_lookup",
        "journey_comparison_presentation_configurations_presentation_unique",
        "journey_presentation_snapshots_status_lookup",
        "journey_presentation_reviews_status_lookup",
        "journey_presentation_handoffs_destination_lookup",
    ]:
        if index_name not in database_text:
            raise AssertionError(f"Missing Mongo index registration: {index_name}")

    service_text = (ROOT / "backend/services/journey_comparison_client_presentation_service.py").read_text(encoding="utf-8").lower()
    for forbidden in ["requests.get(", "requests.post(", "httpx.", "openai", "selenium", "playwright", "backgroundtasks", "celery", "scrape("]:
        if forbidden in service_text:
            raise AssertionError(f"Presentation service contains forbidden execution semantics: {forbidden}")
    for required in ["automatic_preferred_option_selection_disabled", "public_share_links_disabled", "external_messaging_disabled", "finalizedjourneypresentationsnapshoterror", "journeyoptionfarebrandcompositionservice"]:
        if required not in service_text:
            raise AssertionError(f"Presentation service missing required contract: {required}")

    require_text(ROOT / "frontend/src/App.jsx", '"/agency/journey-comparison-presentations"')
    require_text(ROOT / "frontend/src/App.jsx", '"/platform/journey-comparison-presentations"')
    require_text(ROOT / "frontend/src/lib/moduleCatalog.js", "Journey Comparison Presentations")
    require_text(ROOT / "frontend/src/pages/agency/JourneyComparisonPresentationWorkspacePage.jsx", "Client-safe preview")
    require_text(ROOT / "frontend/src/pages/agency/JourneyComparisonPresentationWorkspacePage.jsx", "Select explicitly")
    require_text(ROOT / "frontend/src/pages/platform/JourneyComparisonPresentationDiagnosticsPage.jsx", "Governance view only")
    require_text(ROOT / "frontend/src/pages/agency/JourneyWorkspacePage.jsx", "Prepare client comparison")
    require_text(ROOT / "frontend/src/pages/agency/JourneyAuthoringWorkspacePage.jsx", "Prepare client comparison")
    require_text(ROOT / "frontend/src/pages/agency/JourneyOptionCompositionWorkspacePage.jsx", "Prepare client comparison")
    require_text(ROOT / "frontend/src/pages/agency/OfferWorkspaceMetadataPage.jsx", "Prepare client comparison")
    require_text(ROOT / "docs/architecture/journey-comparison-client-presentation-foundation.md", "Preferred Option Governance")


def restricted_key_found(value: object) -> bool:
    restricted = {
        "internal_title", "internal_notes", "internal_summary", "internal_operational_text",
        "internal_connection_text", "internal_operational_summary", "internal_text", "source_provenance",
        "source_references", "source_hash", "internal_payload", "snapshot_payload", "calculation_trace",
        "evidence_refs", "knowledge_version_refs", "restricted_contacts", "source_urls", "source_locations",
        "supplier_cost", "margin", "internal_cost",
    }
    if isinstance(value, dict):
        return any(key in restricted or key.startswith("internal_") or restricted_key_found(item) for key, item in value.items())
    if isinstance(value, list):
        return any(restricted_key_found(item) for item in value)
    return False


async def verify_service_behavior() -> None:
    db = Database()
    user = {"id": "agent-a", "email": "agent-a@example.test"}
    journey, _ = await build_journey(db, "agency-a", user)
    await seed_governed_fare(db)
    composition_service = JourneyOptionFareBrandCompositionService(db)
    source = await composition_service.create_from_journey("agency-a", journey["id"], {"request_id": "request-a"}, user)
    composition = source["composition"]
    first, second = source["options"]

    governed = (await composition_service.import_fare_brand("agency-a", composition["id"], first["id"], {"fare_family_id": "family-flex", "booking_class": "Y"}, user))["fare_brand_choice"]
    manual = (await composition_service.create_manual_fare_brand("agency-a", composition["id"], second["id"], {
        "client_safe_label": "Comfort", "baggage_summary": "2 checked bags up to 23 kg each",
        "changeability": "included", "refundability": "conditional", "internal_agent_notes": "CLIENT-LEAK-SENTINEL",
    }, user))["fare_brand_choice"]
    await composition_service.set_price_breakdown("agency-a", composition["id"], first["id"], governed["id"], {
        "currency": "EUR", "base_amount": 500, "tax_amount": 100, "total_selling_amount": 600,
    }, user)
    await composition_service.set_price_breakdown("agency-a", composition["id"], second["id"], manual["id"], {
        "currency": "EUR", "base_amount": 620, "tax_amount": 100, "total_selling_amount": 720,
    }, user)
    await composition_service.project_service_assessments("agency-a", composition["id"], user)

    service = JourneyComparisonClientPresentationService(db)
    detail = await service.create_from_composition("agency-a", composition["id"], {
        "internal_notes": "CLIENT-LEAK-SENTINEL", "client_intro_text": "Choose the itinerary that suits your journey.",
    }, user)
    presentation = detail["presentation"]
    if len(detail["options"]) != 2 or len(detail["segments"]) != 4 or len(detail["connections"]) != 2:
        raise AssertionError("Option, segment, or connection projection generation failed.")
    if len(detail["fare_brands"]) != 2 or len(detail["service_suitability"]) != 2:
        raise AssertionError("Fare-brand or special-service suitability projection failed.")
    try:
        await service.get_presentation("agency-b", presentation["id"])
    except JourneyComparisonPresentationError:
        pass
    else:
        raise AssertionError("Presentation leaked across agencies.")

    option_by_source = {item["composition_option_id"]: item for item in detail["options"]}
    first_projection = option_by_source[first["id"]]
    second_projection = option_by_source[second["id"]]
    if first_projection.get("total_elapsed_minutes") != 1560 or first_projection.get("total_connection_minutes") != 930:
        raise AssertionError("Deterministic elapsed or connection duration calculation failed.")
    if not first_projection.get("overnight_connection_count") or not second_projection.get("airport_change_count"):
        raise AssertionError("Overnight or airport-change comparison metadata failed.")
    if not all(item.get("minimum_connection_status") == "not_assessed" and item.get("manual_review_required") for item in detail["connections"]):
        raise AssertionError("Unknown MCT state was not preserved for manual review.")

    comparison = detail["comparison_results"][0]
    if comparison.get("lowest_price_option_id") != first_projection["id"] or comparison.get("preferred_option_id"):
        raise AssertionError("Deterministic price leader or no-automatic-preference boundary failed.")
    fare_by_option = {item["option_projection_id"]: item for item in detail["fare_brands"]}
    if fare_by_option[first_projection["id"]].get("price_difference_from_lowest") != 0 or fare_by_option[second_projection["id"]].get("price_difference_from_lowest") != 120:
        raise AssertionError("Deterministic fare price difference failed.")
    if "checked bag" not in fare_by_option[first_projection["id"]].get("baggage_summary", ""):
        raise AssertionError("Baggage comparison projection failed.")
    if fare_by_option[second_projection["id"]].get("change_summary") != "included" or fare_by_option[second_projection["id"]].get("refund_summary") != "conditional":
        raise AssertionError("Change/refund comparison projection failed.")
    if not comparison.get("unresolved_unknowns") or not comparison.get("manual_review_required"):
        raise AssertionError("Unknown/manual-review states were lost.")
    if not any(item.get("confirmation_requirement") == "airline_confirmation_required" for item in detail["service_suitability"]):
        raise AssertionError("Airline confirmation state was not projected.")

    client = await service.preview_client("agency-a", presentation["id"])
    internal = await service.preview_internal("agency-a", presentation["id"])
    if restricted_key_found(client["client_safe_payload"]) or "CLIENT-LEAK-SENTINEL" in str(client["client_safe_payload"]):
        raise AssertionError("Client preview leaked internal or restricted content.")
    if "CLIENT-LEAK-SENTINEL" not in str(internal["internal_payload"]):
        raise AssertionError("Authorized internal preview omitted internal review context.")
    if client["client_safe_payload"].get("public_share_link") is not None or client["client_safe_payload"].get("published") is not False:
        raise AssertionError("Client preview implied a public link or publication.")

    selected = await service.select_preferred_option("agency-a", presentation["id"], {
        "option_id": second_projection["id"], "reason": "Agent reviewed assistance, timing, and baggage trade-offs.",
    }, user)
    if selected["presentation"].get("preferred_option_id") != second_projection["id"] or selected.get("automatic_selection") is not False:
        raise AssertionError("Explicit preferred-option selection failed.")

    snapshot = (await service.create_snapshot("agency-a", presentation["id"], {"finalize": True}, user))["snapshot"]
    if not snapshot.get("finalized") or len(snapshot.get("source_hash") or "") != 64:
        raise AssertionError("Immutable presentation snapshot creation failed.")
    try:
        await service.update_snapshot("agency-a", presentation["id"], snapshot["id"], {"snapshot_status": "draft"})
    except FinalizedJourneyPresentationSnapshotError:
        pass
    else:
        raise AssertionError("Finalized presentation snapshot mutation was not rejected.")

    review = (await service.create_review("agency-a", presentation["id"], {
        "snapshot_id": snapshot["id"], "review_status": "in_review", "review_notes": "Check all client copy.",
    }, user))["review"]
    completed = (await service.update_review("agency-a", presentation["id"], review["id"], {
        "review_status": "approved", "client_content_approved": True, "pricing_approved": True,
        "schedule_approved": True, "service_assessment_approved": True, "warnings_acknowledged": True,
    }, user))["review"]
    if completed.get("review_status") != "approved" or not completed.get("completed_at"):
        raise AssertionError("Explicit review completion failed.")

    await db.collection("offer_workspaces_v2").insert_one({
        "id": "offer-a", "agency_id": "agency-a", "offer_reference": "OFF-A", "offer_title": "Draft offer",
        "offer_status": "draft", "accepted_snapshot_id": "accepted-snapshot-immutable", "created_at": "2027-01-01T00:00:00+00:00",
        "updated_at": "2027-01-01T00:00:00+00:00",
    })
    before = await db.collection("offer_workspaces_v2").find_one({"id": "offer-a"})
    preview = await service.preview_handoff("agency-a", presentation["id"], {
        "snapshot_id": snapshot["id"], "destination_type": "offer_workspace", "destination_id": "offer-a",
    })
    if not preview.get("can_apply") or preview.get("automatic_action_performed") is not False or "publish" not in preview["preview"]["prohibited_actions"]:
        raise AssertionError("Metadata-only handoff preview boundary failed.")
    applied = await service.apply_handoff("agency-a", presentation["id"], {
        "snapshot_id": snapshot["id"], "destination_type": "offer_workspace", "destination_id": "offer-a",
    }, user)
    after = await db.collection("offer_workspaces_v2").find_one({"id": "offer-a"})
    if before != after or applied.get("destination_mutated") is not False or applied.get("offer_published") is not False or applied.get("provider_execution_performed") is not False:
        raise AssertionError("Handoff mutated an Offer or performed execution.")
    document_preview = await service.preview_handoff("agency-a", presentation["id"], {
        "snapshot_id": snapshot["id"], "destination_type": "document_workspace",
    })
    if document_preview["preview"].get("document_type_suggestion") != "itinerary_comparison":
        raise AssertionError("Document handoff preparation metadata failed.")

    summary = await service.summarize_readiness("agency-a")
    for key in ["presentation_count", "option_projection_count", "segment_projection_count", "connection_projection_count", "fare_brand_projection_count", "service_suitability_projection_count", "comparison_result_count", "snapshot_count", "review_count", "handoff_count", "blocking_warning_count", "manual_review_count", "unknown_value_count"]:
        if not isinstance(summary.get(key), int):
            raise AssertionError(f"Readiness counter missing: {key}")
    for key, value in service.safety_flags().items():
        if value is not True:
            raise AssertionError(f"Safety flag is not enabled: {key}")


def ensure_second_agency(agencies: list[dict]) -> str:
    if len(agencies) > 1:
        return agencies[1]["id"]
    slug = f"journey-presentation-isolation-{int(time.time() * 1000)}"
    return post("/api/agencies", {"name": "Journey Presentation Isolation", "slug": slug, "legal_name": "Journey Presentation Isolation Ltd", "status": "active", "subscription_status": "trial", "default_currency": "EUR", "country": "BG", "timezone": "UTC"}, OWNER_HEADERS, 201)["agency"]["id"]


def verify_live_api() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}; expected {EXPECTED_PHASE}")
    readiness = get("/api/readiness")
    section = readiness.get("journey_comparison_client_presentation_foundation") or {}
    for key in JourneyComparisonClientPresentationService(Database()).safety_flags():
        if section.get(key) is not True:
            raise AssertionError(f"Presentation readiness flag missing: {key}={section.get(key)}")
    for key in [
        "presentation_count", "active_presentation_count", "review_required_presentation_count", "option_projection_count",
        "segment_projection_count", "connection_projection_count", "fare_brand_projection_count",
        "service_suitability_projection_count", "comparison_result_count", "preferred_option_selection_count",
        "content_block_count", "snapshot_count", "finalized_snapshot_count", "review_count", "approved_review_count",
        "handoff_count", "blocking_warning_count", "manual_review_count", "unknown_value_count",
    ]:
        if not isinstance(section.get(key), int):
            raise AssertionError(f"Presentation readiness counter missing: {key}")
    if section.get("readiness_required") is not False:
        raise AssertionError("Presentation readiness must remain diagnostic-only.")

    paths = get("/openapi.json").get("paths") or {}
    route_contract = [
        ("/api/agencies/{agency_id}/journey-comparison-presentations", "get"),
        ("/api/agencies/{agency_id}/journey-comparison-presentations", "post"),
        ("/api/agencies/{agency_id}/journey-comparison-presentations/from-composition/{composition_id}", "post"),
        ("/api/agencies/{agency_id}/journey-comparison-presentations/{presentation_id}/generate", "post"),
        ("/api/agencies/{agency_id}/journey-comparison-presentations/{presentation_id}/options", "get"),
        ("/api/agencies/{agency_id}/journey-comparison-presentations/{presentation_id}/comparison", "get"),
        ("/api/agencies/{agency_id}/journey-comparison-presentations/{presentation_id}/configuration", "put"),
        ("/api/agencies/{agency_id}/journey-comparison-presentations/{presentation_id}/preferred-option", "put"),
        ("/api/agencies/{agency_id}/journey-comparison-presentations/{presentation_id}/preview/client", "get"),
        ("/api/agencies/{agency_id}/journey-comparison-presentations/{presentation_id}/snapshots", "post"),
        ("/api/agencies/{agency_id}/journey-comparison-presentations/{presentation_id}/reviews", "post"),
        ("/api/agencies/{agency_id}/journey-comparison-presentations/{presentation_id}/handoff/preview", "post"),
        ("/api/agencies/{agency_id}/journey-comparison-presentations/{presentation_id}/handoff/apply", "post"),
        ("/api/platform/journey-comparison-presentations", "get"),
        ("/api/platform/journey-comparison-presentations/comparison-dimensions", "get"),
        ("/api/platform/journey-comparison-presentations/validation-codes", "get"),
        ("/api/platform/journey-comparison-presentations/presentations/{presentation_id}", "get"),
    ]
    for path, method in route_contract:
        assert_openapi_path(paths, path, method)

    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires the seeded demo agency.")
    agency_id = agencies[0]["id"]
    other_agency_id = ensure_second_agency(agencies)
    marker = int(time.time() * 1000)
    journey = post(f"/api/agencies/{agency_id}/journeys", {
        "title": f"Live presentation {marker}", "source_entity_type": "manual_entry", "source_entity_id": f"presentation-{marker}",
    }, OWNER_HEADERS, 201)["journey"]
    option = post(f"/api/agencies/{agency_id}/journeys/{journey['id']}/options", {
        "title": "Live route", "source_entity_type": "manual_entry", "source_entity_id": journey["id"],
    }, OWNER_HEADERS, 201)["itinerary_option"]
    for index, values in enumerate([
        {"origin_airport_code": "SOF", "destination_airport_code": "FRA", "departure_utc": "2027-12-01T06:00:00+00:00", "arrival_utc": "2027-12-01T08:00:00+00:00"},
        {"origin_airport_code": "FRA", "destination_airport_code": "JFK", "departure_utc": "2027-12-01T10:00:00+00:00", "arrival_utc": "2027-12-01T18:00:00+00:00"},
    ], start=1):
        post(f"/api/agencies/{agency_id}/journeys/{journey['id']}/segments", {
            "itinerary_option_id": option["id"], "source_entity_type": "manual_entry", "source_entity_id": f"live-{marker}-{index}",
            "marketing_carrier_code": "LH", "operating_carrier_code": "LH", "marketing_flight_number": str(400 + index), **values,
        }, OWNER_HEADERS, 201)
    composition = post(f"/api/agencies/{agency_id}/journey-option-compositions/from-journey/{journey['id']}", {}, OWNER_HEADERS, 201)["composition"]
    created = post(f"/api/agencies/{agency_id}/journey-comparison-presentations/from-composition/{composition['id']}", {}, OWNER_HEADERS, 201)
    presentation = created["presentation"]
    if len(created.get("options") or []) != 1 or len(created.get("segments") or []) != 2 or len(created.get("connections") or []) != 1:
        raise AssertionError("Live presentation generation failed.")
    client = get(f"/api/agencies/{agency_id}/journey-comparison-presentations/{presentation['id']}/preview/client", OWNER_HEADERS)
    if client.get("restricted_content_removed") is not True or client.get("client_safe_payload", {}).get("public_share_link") is not None:
        raise AssertionError("Live client-safe preview boundary failed.")
    platform = get("/api/platform/journey-comparison-presentations", OWNER_HEADERS)
    if platform.get("platform_diagnostics_read_only") is not True:
        raise AssertionError("Platform presentation diagnostics are not read-only.")
    request("GET", "/api/platform/journey-comparison-presentations", None, AGENCY_AGENT_HEADERS, expect=403)
    request("GET", f"/api/agencies/{other_agency_id}/journey-comparison-presentations", None, AGENCY_AGENT_HEADERS, expect=403)


def main() -> None:
    verify_static_contracts()
    asyncio.run(verify_service_behavior())
    verify_live_api()
    print("Phase 56.3 journey comparison and client presentation smoke passed.")


if __name__ == "__main__":
    main()
