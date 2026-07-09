#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from models import AirlineOperationalIntelligenceArchitecture
from services.airline_operational_intelligence_service import (
    ARCHITECTURE_COLLECTION,
    ARCHITECTURE_REFERENCE,
    FUTURE_AOIE_PHASES,
    LINKED_EXISTING_FOUNDATIONS,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, request


EXPECTED_PHASE = "phase_51_3_client_passenger_master_workspace_foundation"
ROOT = Path(__file__).resolve().parents[2]
PLATFORM_BASE = "/api/platform/airline-operational-intelligence"


def require_text(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8")
    if text not in content:
        raise AssertionError(f"{path.relative_to(ROOT)} missing expected text: {text}")


def verify_model_and_collection_registration() -> None:
    model = AirlineOperationalIntelligenceArchitecture(
        id=ARCHITECTURE_REFERENCE,
        architecture_reference=ARCHITECTURE_REFERENCE,
        architecture_version="50.0",
        principle="Passenger -> Need -> Service Requirement -> Airline Capability -> Operational Feasibility -> Pricing / Conditions -> Recommendation -> Fulfilment",
        purpose="Architecture smoke record",
        operational_platform_scope="What is happening.",
        intelligence_engine_scope="What is possible, allowed, priced, risky, and recommended.",
        knowledge_acquisition_scope="Manual acquisition metadata.",
        knowledge_normalisation_scope="Normalisation metadata.",
        knowledge_versioning_scope="Version metadata.",
        knowledge_approval_scope="Human approval metadata.",
        operational_feasibility_scope="Feasibility metadata.",
        airline_recommendation_scope="Future recommendation metadata only.",
        offer_optimisation_scope="Future offer optimisation metadata only.",
        excluded_scope=["AI generation", "airline scraping", "background workers"],
        linked_existing_foundations=LINKED_EXISTING_FOUNDATIONS,
        linked_future_phases=FUTURE_AOIE_PHASES,
    )
    dumped = model.model_dump(mode="json")
    if dumped.get("architecture_status") != "foundation" or dumped.get("metadata_only") is not True:
        raise AssertionError(f"AOIE model did not preserve metadata-only status: {dumped}")
    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    if ARCHITECTURE_COLLECTION not in database_py:
        raise AssertionError("AOIE architecture collection is not registered.")
    for index_name in [
        "airline_operational_intelligence_architecture_id_unique",
        "airline_operational_intelligence_architecture_reference_unique",
        "airline_operational_intelligence_architecture_status_lookup",
        "airline_operational_intelligence_architecture_version_lookup",
        "airline_operational_intelligence_architecture_created_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"AOIE architecture index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    expected = {
        "/api/platform/airline-operational-intelligence": {"get"},
        "/api/platform/airline-operational-intelligence/summary": {"get"},
        "/api/platform/airline-operational-intelligence/architecture": {"get"},
        "/api/agencies/{agency_id}/airline-operational-intelligence": {"get"},
        "/api/agencies/{agency_id}/airline-operational-intelligence/summary": {"get"},
        "/api/agencies/{agency_id}/airline-operational-intelligence/architecture": {"get"},
    }
    for path, methods in expected.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
        blocked = set(paths.get(path, {}).keys()) & {"post", "put", "patch", "delete"}
        if blocked:
            raise AssertionError(f"AOIE route is not read-only: {path} {sorted(blocked)}")
    for path in paths:
        if "airline-operational-intelligence" not in path:
            continue
        forbidden_path_terms = ["ai-execution", "ai-generation", "scrape", "crawler", "worker", "booking-execution", "ticket-issuance", "emd-issuance"]
        if any(term in path for term in forbidden_path_terms):
            raise AssertionError(f"Forbidden AOIE execution-like route exists in OpenAPI: {path}")


def verify_no_execution_code() -> None:
    source_files = [
        ROOT / "backend/services/airline_operational_intelligence_service.py",
        ROOT / "backend/routers/platform_airline_operational_intelligence.py",
        ROOT / "backend/routers/agency_airline_operational_intelligence.py",
    ]
    forbidden_code_terms = [
        "BackgroundTasks",
        "httpx",
        "requests.",
        "urllib.",
        "openai",
        "AsyncClient",
        "Scheduler",
        "schedule.",
        "scrapy",
        "selenium",
    ]
    for source_file in source_files:
        content = source_file.read_text(encoding="utf-8")
        for term in forbidden_code_terms:
            if term in content:
                raise AssertionError(f"AOIE source contains forbidden execution/integration code term {term}: {source_file.relative_to(ROOT)}")


def verify_endpoint_payload(payload: dict, agency_view: bool = False) -> None:
    if payload.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected AOIE phase: {payload}")
    if payload.get("metadata_only") is not True or payload.get("architecture_only") is not True:
        raise AssertionError(f"AOIE payload is not architecture-only metadata: {payload}")
    if agency_view and payload.get("read_only") is not True:
        raise AssertionError(f"Agency AOIE payload should be read-only: {payload}")
    for flag in [
        "ai_generation_disabled",
        "airline_scraping_disabled",
        "automatic_web_crawling_disabled",
        "live_airline_apis_disabled",
        "provider_integrations_disabled",
        "pricing_engine_execution_disabled",
        "itinerary_search_disabled",
        "booking_execution_disabled",
        "ticket_issuance_disabled",
        "emd_issuance_disabled",
        "recommendation_automation_disabled",
        "background_workers_disabled",
        "automation_disabled",
        "external_api_calls_disabled",
    ]:
        if payload.get(flag) is not True:
            raise AssertionError(f"AOIE payload missing disabled flag {flag}: {payload}")
    architecture = payload.get("architecture") or {}
    if architecture.get("architecture_reference") != ARCHITECTURE_REFERENCE:
        raise AssertionError(f"AOIE architecture seed missing: {architecture}")
    if "Passenger -> Need" not in architecture.get("principle", ""):
        raise AssertionError(f"AOIE principle missing: {architecture}")
    for foundation in LINKED_EXISTING_FOUNDATIONS:
        if foundation not in (architecture.get("linked_existing_foundations") or []):
            raise AssertionError(f"AOIE missing linked foundation {foundation}: {architecture}")
    for phase in FUTURE_AOIE_PHASES:
        if phase not in (architecture.get("linked_future_phases") or []):
            raise AssertionError(f"AOIE missing future phase {phase}: {architecture}")
    section_keys = {section.get("key") for section in payload.get("sections") or []}
    for key in [
        "passenger_service_operations_principle",
        "operational_platform_vs_intelligence_engine",
        "knowledge_acquisition",
        "knowledge_normalisation",
        "versioning_and_human_approval",
        "airline_capability_matrix",
        "passenger_service_feasibility",
        "airline_itinerary_recommendation",
        "total_journey_cost_comparison",
        "future_offer_builder_integration",
        "excluded_scope",
    ]:
        if key not in section_keys:
            raise AssertionError(f"AOIE payload missing section {key}: {payload}")


def verify_api_behavior() -> None:
    platform_payload = get(PLATFORM_BASE, OWNER_HEADERS)
    verify_endpoint_payload(platform_payload)
    summary = get(f"{PLATFORM_BASE}/summary", OWNER_HEADERS)
    if summary.get("architecture_record_count", 0) < 1 or summary.get("future_aoie_phase_count") != len(FUTURE_AOIE_PHASES):
        raise AssertionError(f"AOIE summary shape invalid: {summary}")
    architecture_payload = get(f"{PLATFORM_BASE}/architecture", OWNER_HEADERS)
    if (architecture_payload.get("architecture") or {}).get("architecture_reference") != ARCHITECTURE_REFERENCE:
        raise AssertionError(f"AOIE architecture endpoint did not return seeded record: {architecture_payload}")
    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    agency_payload = get(f"/api/agencies/{agency_id}/airline-operational-intelligence", OWNER_HEADERS)
    verify_endpoint_payload(agency_payload, agency_view=True)
    request("POST", f"/api/agencies/{agency_id}/airline-operational-intelligence", {}, OWNER_HEADERS, 405)
    request("POST", PLATFORM_BASE, {}, OWNER_HEADERS, 405)


def verify_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health}")
    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("airline_operational_intelligence_engine_architecture_foundation") or {}
    for key in [
        "airline_operational_intelligence_engine_enabled",
        "aoie_architecture_foundation_enabled",
        "passenger_service_operations_principle_enabled",
        "architecture_record_seeded",
        "platform_airline_operational_intelligence_ui_enabled",
        "agency_operational_intelligence_ui_enabled",
        "chapter_50_intelligence_track_enabled",
        "chapter_41_operational_workspaces_preserved",
        "feeds_chapter_41_42_operational_workspaces",
        "ai_generation_disabled",
        "airline_scraping_disabled",
        "automatic_web_crawling_disabled",
        "live_airline_apis_disabled",
        "provider_integrations_disabled",
        "pricing_engine_execution_disabled",
        "itinerary_search_disabled",
        "booking_execution_disabled",
        "ticket_issuance_disabled",
        "emd_issuance_disabled",
        "recommendation_automation_disabled",
        "background_workers_disabled",
        "external_api_calls_disabled",
    ]:
        if section.get(key) is not True:
            raise AssertionError(f"AOIE readiness missing flag {key}: {section}")
    if section.get("readiness_required") is not False:
        raise AssertionError("AOIE readiness should not be deployment-readiness required.")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/App.jsx", "/platform/airline-operational-intelligence"),
        (ROOT / "frontend/src/App.jsx", "/agency/operational-intelligence"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Airline Operational Intelligence"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Operational Intelligence"),
        (ROOT / "frontend/src/pages/platform/AirlineOperationalIntelligencePage.jsx", "Architecture only"),
        (ROOT / "frontend/src/pages/agency/OperationalIntelligencePage.jsx", "Read-only AOIE architecture metadata"),
        (ROOT / "docs/architecture/airline-operational-intelligence-engine-foundation.md", "Phase 50.0"),
        (ROOT / "docs/architecture/passenger-service-operations-principle.md", "Passenger -> Need"),
        (ROOT / "BUILD_PHASES.md", "Phase 50.0: Airline Operational Intelligence Engine Architecture Foundation"),
        (ROOT / "README.md", "Phase 50.0 Airline Operational Intelligence Engine architecture foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "airline_operational_intelligence_architecture"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/api/platform/airline-operational-intelligence"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "AOIE Chapter 50"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Phase 50.2 - Operational Constraint Engine Foundation"),
    ]:
        require_text(path, text)


def verify_blueprint_recommendations() -> None:
    adoption = get("/api/platform/blueprint/adoption-map", OWNER_HEADERS)
    if not any(item.get("category") == "Airline Operational Intelligence Engine" for item in adoption.get("items") or []):
        raise AssertionError("Blueprint adoption map missing AOIE category.")
    gaps = get("/api/platform/blueprint/gaps", OWNER_HEADERS)
    if "Phase 50.9" not in gaps.get("next_intelligence_phase", ""):
        raise AssertionError(f"Gap summary missing Phase 50.9 next intelligence phase: {gaps}")
    if "Phase 42.2" not in gaps.get("next_operational_phase", ""):
        raise AssertionError(f"Gap summary missing next operational phase: {gaps}")
    if not any("EMD workspace foundation built in Phase 41.8" in item for item in gaps.get("already_built", [])):
        raise AssertionError("Chapter 41 EMD workspace foundation was not preserved.")
    if not any("Phase 50.9" in item for item in gaps.get("chapter_50_intelligence_track", [])):
        raise AssertionError("Chapter 50 AOIE roadmap is missing.")
    next_phases = get("/api/platform/blueprint/next-phases", OWNER_HEADERS)
    if next_phases["items"][0].get("phase") != "Phase 50.9":
        raise AssertionError(f"Next recommendations did not start with Phase 50.9: {next_phases}")
    if not any(item.get("phase") == "Phase 42.2" for item in next_phases.get("items", [])):
        raise AssertionError(f"Next recommendations did not preserve Phase 42.2: {next_phases}")


def main() -> int:
    verify_model_and_collection_registration()
    openapi = get("/openapi.json")
    verify_routes(openapi.get("paths", {}))
    verify_no_execution_code()
    verify_api_behavior()
    verify_readiness()
    verify_frontend_and_docs()
    verify_blueprint_recommendations()
    print("Phase 50.0 airline operational intelligence engine architecture foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"AOIE architecture foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
