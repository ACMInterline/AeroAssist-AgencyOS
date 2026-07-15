#!/usr/bin/env python3
import asyncio
import copy
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS, Database
from models import (
    JourneyAuthoringApplication,
    JourneyAuthoringCorrection,
    JourneyAuthoringSession,
    JourneyAuthoringTemplate,
    JourneyAuthoringValidation,
    JourneyFieldProvenance,
    JourneyImportSource,
    JourneySegmentDraft,
)
from services.canonical_journey_itinerary_service import CanonicalJourneyItineraryService
from services.journey_segment_authoring_service import (
    APPLICATION_COLLECTION,
    AUTHORING_COLLECTIONS,
    CORRECTION_COLLECTION,
    DRAFT_COLLECTION,
    PHASE_LABEL,
    PROVENANCE_COLLECTION,
    SESSION_COLLECTION,
    SOURCE_COLLECTION,
    TEMPLATE_COLLECTION,
    VALIDATION_COLLECTION,
    FinalizedJourneyMutationError,
    JourneyAuthoringError,
    JourneySegmentAuthoringService,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_56_3_journey_comparison_client_presentation_foundation"
ROOT = Path(__file__).resolve().parents[2]
AGENCY_AGENT_HEADERS = {"X-Demo-User-Email": "agency.agent@aeroassist.dev"}


def require_text(path: Path, text: str) -> None:
    if text not in path.read_text(encoding="utf-8"):
        raise AssertionError(f"{path.relative_to(ROOT)} missing expected text: {text}")


def verify_static_contracts() -> None:
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected Phase 56.1 marker: {PHASE_LABEL}")
    expected_collections = {
        SESSION_COLLECTION, SOURCE_COLLECTION, DRAFT_COLLECTION, PROVENANCE_COLLECTION,
        CORRECTION_COLLECTION, VALIDATION_COLLECTION, APPLICATION_COLLECTION, TEMPLATE_COLLECTION,
    }
    if set(AUTHORING_COLLECTIONS) != expected_collections or not expected_collections.issubset(set(AGENCY_OWNED_COLLECTIONS)):
        raise AssertionError("Journey authoring collections are incomplete or not agency-owned.")
    samples = [
        JourneyAuthoringSession(agency_id="agency", title="Session"),
        JourneyImportSource(agency_id="agency", authoring_session_id="session", source_type="manual", source_hash="hash"),
        JourneySegmentDraft(agency_id="agency", authoring_session_id="session", sequence=1),
        JourneyFieldProvenance(agency_id="agency", authoring_session_id="session", segment_draft_id="segment", field_name="origin", source_type="manual"),
        JourneyAuthoringCorrection(agency_id="agency", authoring_session_id="session", correction_type="manual_override"),
        JourneyAuthoringValidation(agency_id="agency", authoring_session_id="session", validation_code="test", severity="info", category="test", message="Test"),
        JourneyAuthoringApplication(agency_id="agency", authoring_session_id="session", journey_id="journey", application_mode="create_new_journey", result_hash="hash"),
        JourneyAuthoringTemplate(agency_id="agency", name="Template"),
    ]
    if not all(item.id and item.metadata_only for item in samples):
        raise AssertionError("Journey authoring model defaults are incomplete.")
    if samples[1].immutable_raw_source is not True or samples[6].automatic_publication_disabled is not True:
        raise AssertionError("Raw-source or publication safety defaults are missing.")

    database_text = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "journey_authoring_sessions_agency_status_lookup",
        "journey_import_sources_hash_lookup",
        "journey_segment_drafts_session_sequence_lookup",
        "journey_field_provenance_field_lookup",
        "journey_authoring_corrections_session_lookup",
        "journey_authoring_validations_session_lookup",
        "journey_authoring_applications_target_lookup",
        "journey_authoring_templates_agency_lookup",
    ]:
        if index_name not in database_text:
            raise AssertionError(f"Missing Mongo index registration: {index_name}")

    service_text = (ROOT / "backend/services/journey_segment_authoring_service.py").read_text(encoding="utf-8")
    for forbidden in ["requests.get(", "httpx.", "openai", "selenium", "playwright", "backgroundtasks", "celery", "scrape("]:
        if forbidden in service_text.lower():
            raise AssertionError(f"Journey authoring service contains forbidden execution semantics: {forbidden}")
    for required in ["GdsParserService", "CanonicalJourneyItineraryService", "ZoneInfo", "minimum_connection_time_asserted", "automatic_publication_disabled"]:
        if required not in service_text:
            raise AssertionError(f"Journey authoring service missing required safety/integration contract: {required}")

    require_text(ROOT / "frontend/src/App.jsx", '"/agency/journey-authoring"')
    require_text(ROOT / "frontend/src/App.jsx", '"/platform/journey-authoring"')
    require_text(ROOT / "frontend/src/lib/moduleCatalog.js", "Journey Authoring")
    require_text(ROOT / "frontend/src/pages/agency/JourneyAuthoringWorkspacePage.jsx", "Parse into editable drafts")
    require_text(ROOT / "frontend/src/pages/agency/JourneyAuthoringWorkspacePage.jsx", "Apply to canonical Journey")
    require_text(ROOT / "frontend/src/pages/platform/JourneyAuthoringDiagnosticsPage.jsx", "Platform users cannot edit")
    require_text(ROOT / "frontend/src/pages/agency/BookingImportsPage.jsx", "Import into Journey")
    require_text(ROOT / "frontend/src/pages/agency/GdsParserPage.jsx", "Create option from parsed itinerary")
    require_text(ROOT / "docs/architecture/journey-segment-authoring-intelligent-import-workspace-foundation.md", "Source-Of-Truth Boundary")


async def verify_service_behavior() -> None:
    db = Database()
    service = JourneySegmentAuthoringService(db)
    canonical = CanonicalJourneyItineraryService(db)
    user = {"id": "agent-a", "email": "agent-a@example.test"}

    session = (await service.create_authoring_session("agency-a", {"title": "SOF to New York options"}, user))["session"]
    if session.get("status") != "draft" or session.get("agency_id") != "agency-a":
        raise AssertionError("Authoring-session creation failed.")
    try:
        await service.get_authoring_session("agency-b", session["id"])
    except JourneyAuthoringError:
        pass
    else:
        raise AssertionError("Journey authoring leaked a session across agencies.")

    raw_text = "LH 441 15JUL FRA JFK 1010 1305\nUNRESOLVED FREE TEXT MUST REMAIN"
    imported = await service.import_raw_text("agency-a", session["id"], {"raw_text": raw_text, "source_type": "gds_cryptic", "source_label": "Agent paste", "default_year": 2027}, user)
    source = await db.collection(SOURCE_COLLECTION).find_one({"id": imported["source"]["id"]})
    if source.get("raw_text") != raw_text or len(source.get("source_hash") or "") != 64 or not source.get("immutable_raw_source"):
        raise AssertionError("Raw-text preservation or source hashing failed.")
    if "UNRESOLVED FREE TEXT MUST REMAIN" not in str((await db.collection(SOURCE_COLLECTION).find_one({"id": source["id"]})).get("raw_payload")):
        raise AssertionError("Unparsed source text was silently discarded.")
    if not imported.get("existing_gds_parser_reused") or not imported.get("created_segments"):
        raise AssertionError("Pasted-text parser adapter did not create normalized drafts.")

    imported_segment = imported["created_segments"][0]
    updated = (await service.update_segment_draft("agency-a", session["id"], imported_segment["id"], {"operating_carrier_code": "LH", "departure_timezone": "Europe/Berlin", "arrival_timezone": "America/New_York", "reason": "Agent confirmed carrier and timezones"}, user))["segment"]
    if updated.get("scheduled_duration_minutes") != 535:
        raise AssertionError(f"Timezone-aware duration calculation failed: {updated.get('scheduled_duration_minutes')}")
    provenance = await service.list_field_provenance("agency-a", session["id"])
    corrections = await service.list_corrections("agency-a", session["id"])
    if not any(item.get("value_status") == "agent_overridden" for item in provenance) or not corrections:
        raise AssertionError("Manual correction or field provenance history failed.")

    await db.collection("global_reference_records").insert_one({"id": "airport-fra", "domain": "airports", "code": "FRA", "label": "Frankfurt Airport", "metadata_json": {"city": "Frankfurt", "country": "DE", "timezone": "Europe/Berlin"}})
    await db.collection("global_reference_records").insert_one({"id": "airport-jfk", "domain": "airports", "code": "JFK", "label": "John F. Kennedy International Airport", "metadata_json": {"city": "New York", "country": "US", "timezone": "America/New_York"}})
    await db.collection("global_reference_records").insert_one({"id": "airline-lh", "domain": "airlines", "code": "LH", "label": "Lufthansa", "metadata_json": {}})
    enriched = await service.enrich_session_from_internal_reference_data("agency-a", session["id"], user)
    if not enriched.get("count") or enriched.get("external_lookup_performed") is not False:
        raise AssertionError("Governed internal airport/airline enrichment failed.")
    enriched_segment = await db.collection(DRAFT_COLLECTION).find_one({"id": imported_segment["id"]})
    if enriched_segment.get("departure_airport_name") != "Frankfurt Airport" or enriched_segment.get("marketing_carrier_name") != "Lufthansa":
        raise AssertionError("Internal reference fields were not applied.")

    second = (await service.create_manual_segment_draft("agency-a", session["id"], {
        "marketing_carrier_code": "UA", "marketing_flight_number": "900", "operating_carrier_code": "UA",
        "departure_airport_code": "JFK", "arrival_airport_code": "LAX",
        "departure_local_datetime": "2027-07-15T16:30:00", "arrival_local_datetime": "2027-07-15T19:20:00",
        "departure_timezone": "America/New_York", "arrival_timezone": "America/Los_Angeles", "cabin": "economy", "booking_class": "Y",
    }, user))["segment"]
    validation = await service.validate_session("agency-a", session["id"])
    if validation["summary"]["blocking"]:
        raise AssertionError(f"Valid valid-timezone itinerary was unexpectedly blocked: {validation['items']}")
    recalculated = await service.recalculate_session("agency-a", session["id"])
    if not recalculated.get("connections") or recalculated["connections"][0].get("connection_minutes") != 205:
        raise AssertionError("Connection duration calculation failed.")

    overnight_session = (await service.create_authoring_session("agency-a", {"title": "Overnight validation"}, user))["session"]
    overnight = (await service.create_manual_segment_draft("agency-a", overnight_session["id"], {
        "marketing_carrier_code": "BA", "marketing_flight_number": "117", "operating_carrier_code": "BA",
        "departure_airport_code": "LHR", "arrival_airport_code": "JFK",
        "departure_local_datetime": "2027-09-20T20:00:00", "arrival_local_datetime": "2027-09-21T23:00:00",
        "departure_timezone": "Europe/London", "arrival_timezone": "America/New_York",
    }, user))["segment"]
    if not overnight.get("overnight_indicator") or overnight.get("arrival_day_offset") != 1:
        raise AssertionError("Overnight/local-date change detection failed.")
    duplicate = (await service.create_manual_segment_draft("agency-a", overnight_session["id"], {
        "marketing_carrier_code": "BA", "marketing_flight_number": "117", "operating_carrier_code": "AA",
        "departure_airport_code": "LHR", "arrival_airport_code": "JFK",
        "departure_local_datetime": "2027-09-20T20:00:00", "arrival_local_datetime": "2027-09-21T23:00:00",
        "departure_timezone": "Europe/London", "arrival_timezone": "America/New_York",
    }, user))["segment"]
    findings = (await service.validate_session("agency-a", overnight_session["id"]))["items"]
    codes = {item.get("validation_code") for item in findings}
    if not {"duplicate_segment", "negative_connection", "segment_overlap", "codeshare_review"}.issubset(codes):
        raise AssertionError(f"Duplicate, chronology, or carrier validation failed: {codes}")

    gap_session = (await service.create_authoring_session("agency-a", {"title": "Surface gap"}, user))["session"]
    gap_one = (await service.create_manual_segment_draft("agency-a", gap_session["id"], {
        "marketing_carrier_code": "LH", "marketing_flight_number": "100", "operating_carrier_code": "LH",
        "departure_airport_code": "SOF", "arrival_airport_code": "FRA",
        "departure_local_datetime": "2027-10-01T08:00:00", "arrival_local_datetime": "2027-10-01T09:30:00",
        "departure_timezone": "Europe/Sofia", "arrival_timezone": "Europe/Berlin",
    }, user))["segment"]
    gap_two = (await service.create_manual_segment_draft("agency-a", gap_session["id"], {
        "marketing_carrier_code": "LH", "marketing_flight_number": "400", "operating_carrier_code": "LH",
        "departure_airport_code": "MUC", "arrival_airport_code": "JFK",
        "departure_local_datetime": "2027-10-01T12:00:00", "arrival_local_datetime": "2027-10-01T15:00:00",
        "departure_timezone": "Europe/Berlin", "arrival_timezone": "America/New_York",
    }, user))["segment"]
    gap_codes = {item["validation_code"] for item in (await service.validate_session("agency-a", gap_session["id"]))["items"]}
    if "surface_discontinuity" not in gap_codes or "airport_change" not in gap_codes:
        raise AssertionError("Surface-gap or airport-change validation failed.")

    bulk = await service.bulk_update_segment_drafts("agency-a", gap_session["id"], [gap_one["id"], gap_two["id"]], {"cabin": "business", "booking_class": "C"}, user)
    if any(item.get("cabin") != "business" for item in bulk["items"]):
        raise AssertionError("Bulk segment update failed.")
    reordered = await service.reorder_segment_drafts("agency-a", gap_session["id"], [gap_two["id"], gap_one["id"]], user)
    if reordered["items"][0]["id"] != gap_two["id"]:
        raise AssertionError("Segment reordering failed.")
    await service.archive_segment_draft("agency-a", gap_session["id"], gap_one["id"], user)
    restored = (await service.restore_segment_draft("agency-a", gap_session["id"], gap_one["id"], user))["segment"]
    if not restored.get("active") or restored.get("archived_at"):
        raise AssertionError("Segment draft archive/restore failed.")

    parser_run_id = "parser-run-mocked"
    await db.collection("gds_parser_runs").insert_one({
        "id": parser_run_id,
        "agency_id": "agency-a",
        "input_excerpt": "1 BA 117 Y 20SEP LHRJFK HK1 0820 1105",
        "parser_profile_id": "profile-mocked",
        "normalized_preview_json": {"segments": [{"sequence": 1, "marketing_airline_code": "BA", "flight_number": "117", "booking_class": "Y", "departure_date": "2027-09-20", "departure_time": "0820", "arrival_date": "2027-09-20", "arrival_time": "1105", "origin_airport_code": "LHR", "destination_airport_code": "JFK", "raw_line": "1 BA 117 Y 20SEP LHRJFK HK1 0820 1105", "confidence": 0.91}]},
    })
    parser_session = (await service.create_authoring_session("agency-a", {"title": "Parser import"}, user))["session"]
    parser_import = await service.import_parser_run("agency-a", parser_session["id"], parser_run_id, user)
    if not parser_import.get("existing_gds_parser_reused") or not parser_import.get("created_segments"):
        raise AssertionError("Existing parser-run integration failed.")

    await db.collection("booking_import_drafts").insert_one({
        "id": "booking-draft-a", "agency_id": "agency-a", "raw_text": "AF006 18AUG CDG JFK 13:30 15:45",
        "normalized_preview_json": {"segments": [{"sequence": 1, "marketing_airline_code": "AF", "flight_number": "006", "departure_date": "2027-08-18", "departure_time": "1330", "arrival_date": "2027-08-18", "arrival_time": "1545", "origin_airport_code": "CDG", "destination_airport_code": "JFK", "raw_line": "AF006 18AUG CDG JFK 13:30 15:45"}]},
    })
    booking_session = (await service.create_authoring_session("agency-a", {"title": "Booking import"}, user))["session"]
    booking_import = await service.import_booking_import_draft("agency-a", booking_session["id"], "booking-draft-a", user)
    if not booking_import.get("booking_import_draft_reused") or not booking_import.get("created_segments"):
        raise AssertionError("Booking Import Draft integration failed.")

    apply_session = (await service.create_authoring_session("agency-a", {"title": "Application source"}, user))["session"]
    first = (await service.create_manual_segment_draft("agency-a", apply_session["id"], {
        "marketing_carrier_code": "LH", "marketing_flight_number": "1426", "operating_carrier_code": "LH",
        "departure_airport_code": "SOF", "arrival_airport_code": "FRA",
        "departure_local_datetime": "2027-11-03T06:00:00", "arrival_local_datetime": "2027-11-03T07:30:00",
        "departure_timezone": "Europe/Sofia", "arrival_timezone": "Europe/Berlin", "cabin": "economy", "booking_class": "Y",
    }, user))["segment"]
    await service.create_manual_segment_draft("agency-a", apply_session["id"], {
        "marketing_carrier_code": "LH", "marketing_flight_number": "400", "operating_carrier_code": "LH",
        "departure_airport_code": "FRA", "arrival_airport_code": "JFK",
        "departure_local_datetime": "2027-11-03T10:00:00", "arrival_local_datetime": "2027-11-03T13:00:00",
        "departure_timezone": "Europe/Berlin", "arrival_timezone": "America/New_York", "cabin": "economy", "booking_class": "Y",
    }, user)
    preview = await service.preview_application("agency-a", apply_session["id"], {"application_mode": "create_new_journey"})
    if preview.get("blocking") or preview.get("segment_count") != 2 or not preview.get("source_references_retained"):
        raise AssertionError(f"Application preview failed: {preview}")
    applied = await service.apply_session_to_journey("agency-a", apply_session["id"], {"application_mode": "create_new_journey"}, user)
    if not applied.get("application") or len(applied.get("journey", {}).get("segments") or []) != 2 or applied.get("automatic_publication") is not False:
        raise AssertionError("Application to new canonical Journey failed.")
    if not await db.collection(APPLICATION_COLLECTION).find_one({"id": applied["application"]["id"]}):
        raise AssertionError("Journey application trace was not retained.")

    editable_journey = (await canonical.create_journey({"agency_id": "agency-a", "title": "Editable target", "source_entity_type": "manual_entry", "source_entity_id": "editable-target"}, user, agency_id="agency-a"))["journey"]
    existing_apply = await service.apply_session_to_journey("agency-a", apply_session["id"], {"application_mode": "create_new_option", "journey_id": editable_journey["id"]}, user)
    if existing_apply["application"].get("journey_id") != editable_journey["id"]:
        raise AssertionError("Application to an existing editable Journey failed.")

    immutable_journey = (await canonical.create_journey({"agency_id": "agency-a", "title": "Finalized target", "source_entity_type": "manual_entry", "source_entity_id": "immutable-target"}, user, agency_id="agency-a"))["journey"]
    await canonical.create_snapshot("agency-a", immutable_journey["id"], {"finalize": True}, user)
    try:
        await service.apply_session_to_journey("agency-a", apply_session["id"], {"application_mode": "create_new_option", "journey_id": immutable_journey["id"]}, user)
    except FinalizedJourneyMutationError:
        pass
    else:
        raise AssertionError("Finalized Journey target mutation was not rejected.")

    dashboard = await service.dashboard()
    if dashboard.get("summary", {}).get("application_count", 0) < 2 or dashboard.get("platform_diagnostics_enabled") is not True:
        raise AssertionError("Platform authoring diagnostics summary failed.")
    safe_detail = await service.get_authoring_session("agency-a", session["id"])
    if any("restricted_metadata" in item for item in safe_detail.get("sources") or []):
        raise AssertionError("Agency-safe source response leaked restricted source metadata.")
    flags = service.safety_flags()
    for key in ["external_api_calls_disabled", "scraping_disabled", "provider_execution_disabled", "automatic_publication_disabled", "background_workers_disabled", "ai_disabled"]:
        if flags.get(key) is not True:
            raise AssertionError(f"Safety flag is missing: {key}")
    if first.get("source_provenance", {}).get("source_type") != "manual":
        raise AssertionError("Manual draft provenance was not retained.")


def ensure_second_agency(agencies: list[dict]) -> str:
    if len(agencies) > 1:
        return agencies[1]["id"]
    slug = f"journey-authoring-isolation-{int(time.time() * 1000)}"
    return post("/api/agencies", {"name": "Journey Authoring Isolation", "slug": slug, "legal_name": "Journey Authoring Isolation Ltd", "status": "active", "subscription_status": "trial", "default_currency": "EUR", "country": "BG", "timezone": "UTC"}, OWNER_HEADERS, 201)["agency"]["id"]


def verify_live_api() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")
    readiness = get("/api/readiness")
    section = readiness.get("journey_segment_authoring_intelligent_import_workspace_foundation") or {}
    for key in [
        "journey_segment_authoring_enabled", "authoring_sessions_collection_enabled", "raw_source_preservation_enabled",
        "field_provenance_enabled", "deterministic_duration_calculation_enabled", "timezone_aware_calculation_enabled",
        "finalized_journey_snapshot_mutation_disabled", "agency_isolation_enabled", "platform_diagnostics_enabled",
        "live_schedule_lookup_disabled", "external_api_calls_disabled", "scraping_disabled", "provider_connectivity_disabled",
        "automatic_publication_disabled", "background_workers_disabled", "ai_disabled", "metadata_only",
    ]:
        if section.get(key) is not True:
            raise AssertionError(f"Journey authoring readiness flag missing: {key}={section.get(key)}")
    for key in [
        "authoring_session_count", "active_authoring_session_count", "requires_review_session_count", "import_source_count",
        "segment_draft_count", "unresolved_segment_count", "confirmed_segment_count", "validation_count",
        "blocking_validation_count", "correction_count", "application_count", "parser_linked_session_count",
        "booking_import_linked_session_count",
    ]:
        if not isinstance(section.get(key), int):
            raise AssertionError(f"Journey authoring readiness counter missing: {key}")
    if section.get("readiness_required") is not False:
        raise AssertionError("Journey authoring readiness must remain diagnostic-only.")

    paths = get("/openapi.json").get("paths") or {}
    for path, method in [
        ("/api/agencies/{agency_id}/journey-authoring", "get"),
        ("/api/agencies/{agency_id}/journey-authoring", "post"),
        ("/api/agencies/{agency_id}/journey-authoring/{session_id}/import-text", "post"),
        ("/api/agencies/{agency_id}/journey-authoring/{session_id}/segments/reorder", "post"),
        ("/api/agencies/{agency_id}/journey-authoring/{session_id}/validate", "post"),
        ("/api/agencies/{agency_id}/journey-authoring/{session_id}/preview-application", "post"),
        ("/api/agencies/{agency_id}/journey-authoring/{session_id}/apply-to-journey", "post"),
        ("/api/platform/journey-authoring", "get"),
        ("/api/platform/journey-authoring/sessions/{session_id}", "get"),
        ("/api/platform/journey-authoring/validation-codes", "get"),
    ]:
        assert_openapi_path(paths, path, method)

    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires the seeded demo agency.")
    agency_id = agencies[0]["id"]
    other_agency_id = ensure_second_agency(agencies)
    session = post(f"/api/agencies/{agency_id}/journey-authoring", {"title": f"Live authoring {int(time.time())}"}, OWNER_HEADERS, 201)["session"]
    segment = post(f"/api/agencies/{agency_id}/journey-authoring/{session['id']}/segments", {
        "marketing_carrier_code": "LH", "marketing_flight_number": "400", "operating_carrier_code": "LH",
        "departure_airport_code": "FRA", "arrival_airport_code": "JFK",
        "departure_local_datetime": "2027-12-01T10:00:00", "arrival_local_datetime": "2027-12-01T13:00:00",
        "departure_timezone": "Europe/Berlin", "arrival_timezone": "America/New_York",
    }, OWNER_HEADERS, 201)["segment"]
    put(f"/api/agencies/{agency_id}/journey-authoring/{session['id']}/segments/{segment['id']}", {"cabin": "economy", "booking_class": "Y", "reason": "Live smoke correction"}, OWNER_HEADERS, 200)
    validated = post(f"/api/agencies/{agency_id}/journey-authoring/{session['id']}/validate", {}, OWNER_HEADERS, 200)
    if validated.get("summary", {}).get("blocking"):
        raise AssertionError(f"Live Journey authoring validation unexpectedly blocked: {validated}")
    preview = post(f"/api/agencies/{agency_id}/journey-authoring/{session['id']}/preview-application", {"application_mode": "create_new_journey"}, OWNER_HEADERS, 200)
    if preview.get("blocking") or preview.get("segment_count") != 1:
        raise AssertionError("Live Journey application preview failed.")
    applied = post(f"/api/agencies/{agency_id}/journey-authoring/{session['id']}/apply-to-journey", {"application_mode": "create_new_journey"}, OWNER_HEADERS, 200)
    if not applied.get("application") or applied.get("automatic_publication") is not False:
        raise AssertionError("Live explicit Journey application failed.")
    if get("/api/platform/journey-authoring", OWNER_HEADERS).get("platform_diagnostics_enabled") is not True:
        raise AssertionError("Platform Journey authoring diagnostics failed.")
    request("GET", "/api/platform/journey-authoring", None, AGENCY_AGENT_HEADERS, expect=403)
    request("GET", f"/api/agencies/{other_agency_id}/journey-authoring", None, AGENCY_AGENT_HEADERS, expect=403)


def main() -> None:
    verify_static_contracts()
    asyncio.run(verify_service_behavior())
    verify_live_api()
    print("Phase 56.1 journey segment authoring and intelligent import workspace smoke passed.")


if __name__ == "__main__":
    main()
