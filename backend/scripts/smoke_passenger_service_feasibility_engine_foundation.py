#!/usr/bin/env python3
import sys
import time
from pathlib import Path
from urllib.parse import quote

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import PassengerServiceFeasibility, PassengerServiceFeasibilityCreate
from services.passenger_service_feasibility_service import (
    FEASIBILITY_CONFIDENCE_LEVELS,
    FEASIBILITY_OUTCOMES,
    FEASIBILITY_STATUSES,
    FEASIBILITY_TYPES,
    OPERATIONAL_RISK_LEVELS,
    PASSENGER_SERVICE_FEASIBILITY_COLLECTION,
    PHASE_LABEL,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_52_1_reference_data_engine_foundation"
ROOT = Path(__file__).resolve().parents[2]
PLATFORM_BASE = "/api/platform/passenger-service-feasibility"


def run_ref(prefix: str) -> str:
    return f"{prefix}-{int(time.time() * 1000)}"


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
        "no_ai_reasoning",
        "no_llm_prompts",
        "flight_search_disabled",
        "airline_recommendation_ranking_disabled",
        "recommendation_engine_disabled",
        "booking_disabled",
        "ticketing_disabled",
        "provider_integrations_disabled",
        "parser_execution_disabled",
        "pricing_optimisation_disabled",
        "background_workers_disabled",
        "automatic_operational_decisions_disabled",
    ]


def assert_disabled_response(payload: dict) -> None:
    if payload.get("metadata_only") is not True:
        raise AssertionError(f"Payload is not metadata-only: {payload}")
    for flag in disabled_flags():
        if payload.get(flag) is not True:
            raise AssertionError(f"Payload missing disabled flag {flag}: {payload}")


def feasibility_payload(agency_id: str, reference: str) -> dict:
    return {
        "agency_id": agency_id,
        "feasibility_reference": reference,
        "feasibility_status": "in_review",
        "feasibility_type": "passenger_service",
        "feasibility_version": "50.7.0-smoke",
        "passenger_workspace_id": "PAX-WS-SMOKE-507",
        "passenger_profile_reference": "PSG-SMOKE-507",
        "passenger_need_summary": "Passenger requests PETC with conditional station handling and document review.",
        "passenger_need_category": "travel_with_pet",
        "passenger_type": "adult",
        "passenger_age": 34,
        "passenger_requirements": [
            {"requirement": "PETC", "category": "animal_transport", "notes": "Small pet in cabin."},
            {"requirement": "pet_passport", "category": "document"},
        ],
        "travel_request_id": "TR-SMOKE-507",
        "trip_workspace_id": "TRIP-SMOKE-507",
        "flight_workspace_ids": ["FLT-SMOKE-507"],
        "booking_workspace_id": "BKG-SMOKE-507",
        "itinerary_summary": "SOF-MUC-FRA with PETC handling review.",
        "origin": "SOF",
        "destination": "FRA",
        "transit_points": ["MUC"],
        "travel_date": "2028-07-01",
        "cabin_requested": "Economy",
        "airline_code": "LH",
        "airline_name": "Lufthansa",
        "validating_carrier": "LH",
        "operating_carrier": "LH",
        "marketing_carrier": "LH",
        "operational_evaluation_ids": ["OKE-SMOKE-507"],
        "capability_matrix_ids": ["ACM-SMOKE-507"],
        "knowledge_version_ids": ["AKV-SMOKE-507"],
        "constraint_ids": ["OC-SMOKE-507"],
        "evidence_reference_ids": ["EVID-SMOKE-507"],
        "feasibility_outcome": "conditionally_feasible",
        "feasibility_confidence": "official",
        "feasibility_summary": "PETC appears feasible with station review, document review, and manual approval metadata.",
        "feasibility_reason": "Operational Evaluation Results indicate capability and policy metadata are conditionally satisfied.",
        "feasibility_blocking_reasons": [],
        "feasibility_warning_reasons": ["Station handling confirmation is not yet recorded."],
        "feasibility_conditions": ["Advance airline approval required", "Pet passport required"],
        "satisfied_requirements": ["adult_passenger_identity"],
        "conditionally_satisfied_requirements": ["PETC", "station_handling"],
        "unsatisfied_requirements": [],
        "unknown_requirements": ["final_station_handling_confirmation"],
        "required_ssrs": ["PETC"],
        "required_osis": ["PET IN CABIN REVIEW REQUIRED"],
        "required_emds": ["RFIC-C-RFISC-0BT"],
        "required_documents": ["pet_passport", "vaccination_certificate"],
        "required_medif": False,
        "required_airline_approval": True,
        "required_station_notification": True,
        "required_crew_notification": True,
        "required_manual_review": True,
        "required_follow_up_tasks": ["Confirm station handling", "Attach pet passport"],
        "operational_risk_level": "medium",
        "operational_risk_summary": "Service can proceed only with manual operational review.",
        "operational_risk_reasons": ["Station handling metadata is conditional", "Document verification is pending"],
        "adm_risk_relevance": "low",
        "disruption_risk_relevance": "medium",
        "service_failure_risk_relevance": "medium",
        "evidence_trace": [
            {"evidence_id": "EVID-SMOKE-507", "supports": "capability", "source_collection": "airline_knowledge_acquisitions"}
        ],
        "evaluation_trace": [
            {"evaluation_id": "OKE-SMOKE-507", "result": "conditional", "source_collection": "operational_knowledge_evaluations"}
        ],
        "decision_trace": [
            {"decision": "human_review_required", "reason": "Feasibility is advisory and not final authority."}
        ],
        "data_confidence_level": "official",
        "evidence_confidence_level": "official",
        "operational_validation_confidence": "medium",
        "confidence_reason": "Evidence is official, but station handling still requires human review.",
        "feasibility_ready": True,
        "recommendation_ready": False,
        "internal_notes": "Metadata-only feasibility. No recommendation, ranking, flight search, booking, ticketing, provider integration, AI, LLM, parser, pricing optimisation, worker, or automatic decision.",
        "agent_notes": "Human authority remains final.",
        "metadata": {"smoke": True, "metadata_only": True},
    }


def verify_model_and_collection_registration() -> None:
    if PASSENGER_SERVICE_FEASIBILITY_COLLECTION not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("passenger_service_feasibilities is not registered as agency-owned metadata.")
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Service phase label mismatch: {PHASE_LABEL}")

    payload = feasibility_payload("agency-smoke", "PSF-SMOKE-MODEL")
    create_model = PassengerServiceFeasibilityCreate(**payload)
    record = PassengerServiceFeasibility(**create_model.model_dump(mode="json", exclude_none=True))
    if record.feasibility_reference != "PSF-SMOKE-MODEL":
        raise AssertionError("Passenger service feasibility model did not preserve reference metadata.")
    if record.feasibility_outcome != "conditionally_feasible" or record.feasibility_confidence != "official":
        raise AssertionError("Passenger service feasibility model did not preserve non-Boolean outcome metadata.")
    if not record.operational_evaluation_ids or not record.required_ssrs or not record.evidence_trace:
        raise AssertionError("Passenger service feasibility model did not preserve links, actions, and trace metadata.")
    if record.metadata_only is not True or record.no_ai_reasoning is not True or record.recommendation_engine_disabled is not True:
        raise AssertionError("Passenger service feasibility model is not metadata-only.")

    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "passenger_service_feasibilities_id_unique",
        "passenger_service_feasibilities_reference_unique",
        "passenger_service_feasibilities_agency_status_lookup",
        "passenger_service_feasibilities_airline_lookup",
        "passenger_service_feasibilities_operational_evaluation_lookup",
        "passenger_service_feasibilities_outcome_lookup",
        "passenger_service_feasibilities_required_ssr_lookup",
        "passenger_service_feasibilities_risk_lookup",
        "passenger_service_feasibilities_future_readiness_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Database index registration missing {index_name}.")

    for value in ["fully_feasible", "conditionally_feasible", "operational_review_required", "operationally_blocked", "unknown"]:
        if value not in FEASIBILITY_OUTCOMES:
            raise AssertionError(f"Missing feasibility outcome {value}.")
    for value in ["draft", "in_review", "completed", "blocked", "archived"]:
        if value not in FEASIBILITY_STATUSES:
            raise AssertionError(f"Missing feasibility status {value}.")
    if "passenger_service" not in FEASIBILITY_TYPES or "official" not in FEASIBILITY_CONFIDENCE_LEVELS or "medium" not in OPERATIONAL_RISK_LEVELS:
        raise AssertionError("Feasibility constants are incomplete.")


def verify_router_and_ui_registration() -> None:
    openapi = get("/openapi.json", OWNER_HEADERS)
    paths = openapi.get("paths", {})
    for path, method in [
        (PLATFORM_BASE, "get"),
        (PLATFORM_BASE, "post"),
        (f"{PLATFORM_BASE}/summary", "get"),
        (f"{PLATFORM_BASE}/{{feasibility_id}}", "get"),
        (f"{PLATFORM_BASE}/{{feasibility_id}}", "put"),
        (f"{PLATFORM_BASE}/{{feasibility_id}}", "delete"),
        ("/api/agencies/{agency_id}/passenger-service-feasibility", "get"),
        ("/api/agencies/{agency_id}/passenger-service-feasibility/summary", "get"),
        ("/api/agencies/{agency_id}/passenger-service-feasibility/{feasibility_id}", "get"),
    ]:
        assert_openapi_path(paths, path, method)

    for path in paths:
        if "passenger-service-feasibility" in path:
            for forbidden in ["recommendations", "ranking", "flight-search", "bookings/live", "tickets/issue", "providers", "execute"]:
                if forbidden in path:
                    raise AssertionError(f"Forbidden execution route exposed for feasibility: {path}")

    for path, text in [
        (ROOT / "frontend/src/App.jsx", "/platform/passenger-service-feasibility"),
        (ROOT / "frontend/src/App.jsx", "/agency/service-feasibility"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Passenger Service Feasibility"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Service Feasibility"),
        (ROOT / "frontend/src/pages/platform/PassengerServiceFeasibilityPage.jsx", "Feasibility is not Boolean"),
        (ROOT / "frontend/src/pages/agency/ServiceFeasibilityPage.jsx", "Read-only advisory feasibility metadata"),
        (ROOT / "docs/architecture/passenger-service-feasibility-engine-foundation.md", "Feasibility is not Boolean"),
        (ROOT / "docs/architecture/passenger-service-feasibility-engine-foundation.md", "Phase 50.8 consumes feasibility metadata for advisory Airline Recommendation records"),
        (ROOT / "docs/architecture/current-model-inventory.md", "passenger_service_feasibilities"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/api/platform/passenger-service-feasibility"),
        (ROOT / "docs/architecture/airline-operational-intelligence-engine-foundation.md", "Passenger Service Feasibility Engine"),
        (ROOT / "docs/architecture/foundations/AIRLINE_OPERATIONAL_KNOWLEDGE_BLUEPRINT.md", "Phase 50.7 implements"),
        (ROOT / "docs/architecture/foundations/AEROASSIST_ENGINEERING_PRINCIPLES.md", "Passenger Service Feasibility is non-Boolean advisory metadata"),
        (ROOT / "docs/architecture/foundations/GLOSSARY.md", "Passenger Service Feasibility"),
    ]:
        require_text(path, text)

    for path in [
        ROOT / "frontend/src/pages/platform/PassengerServiceFeasibilityPage.jsx",
        ROOT / "frontend/src/pages/agency/ServiceFeasibilityPage.jsx",
    ]:
        reject_text(path, "apiPost")
        reject_text(path, "apiPut")
        reject_text(path, "apiDelete")
        for forbidden in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, forbidden)


def verify_metadata_only_code() -> None:
    implementation_paths = [
        ROOT / "backend/services/passenger_service_feasibility_service.py",
        ROOT / "backend/routers/platform_passenger_service_feasibility.py",
        ROOT / "backend/routers/agency_passenger_service_feasibility.py",
        ROOT / "frontend/src/pages/platform/PassengerServiceFeasibilityPage.jsx",
        ROOT / "frontend/src/pages/agency/ServiceFeasibilityPage.jsx",
    ]
    forbidden_terms = [
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
        "BeautifulSoup",
        "crawl(",
        "scrape(",
        "flight_search(",
        "search_flights(",
        "rank_airlines(",
        "recommend_airline(",
        "recommend_itinerary(",
        "create_booking(",
        "issue_ticket(",
        "provider_client",
        "execute_parser(",
        "optimise_pricing(",
        "optimize_pricing(",
        "llm_prompt(",
        "ChatCompletion",
    ]
    for path in implementation_paths:
        content = path.read_text(encoding="utf-8")
        for term in forbidden_terms:
            if term in content:
                raise AssertionError(f"{path.relative_to(ROOT)} contains forbidden execution term {term}.")


def verify_blueprint_adoption() -> None:
    adoption = get("/api/platform/blueprint/adoption-map", OWNER_HEADERS)
    categories = {item.get("category") for item in adoption.get("items") or []}
    if "Passenger Service Feasibility" not in categories:
        raise AssertionError(f"Blueprint adoption map missing Passenger Service Feasibility category: {categories}")

    route_policy = get("/api/platform/blueprint/route-policy", OWNER_HEADERS)
    mappings = route_policy.get("route_mappings") or []
    expected_pairs = {
        ("/admin/passenger-service-feasibility", "/platform/passenger-service-feasibility"),
        ("/agent/service-feasibility", "/agency/service-feasibility"),
    }
    actual_pairs = {(item.get("supplementary"), item.get("agencyos")) for item in mappings}
    missing = expected_pairs - actual_pairs
    if missing:
        raise AssertionError(f"Route policy missing feasibility canonical mappings: {missing}")

    gaps = get("/api/platform/blueprint/gaps", OWNER_HEADERS)
    if "Passenger service feasibility engine foundation built in Phase 50.7" not in gaps.get("already_built", []):
        raise AssertionError(f"Gap summary missing Phase 50.7 feasibility marker: {gaps}")
    if "Phase 50.9" not in gaps.get("next_intelligence_phase", ""):
        raise AssertionError(f"Gap summary missing Phase 50.9 next intelligence phase: {gaps}")

    next_phases = get("/api/platform/blueprint/next-phases", OWNER_HEADERS)
    if not next_phases.get("items") or next_phases["items"][0].get("phase") != "Phase 50.9":
        raise AssertionError(f"Next recommendations did not start with Phase 50.9: {next_phases}")


def assert_created_record(record: dict, reference: str, agency_id: str) -> None:
    if record.get("feasibility_reference") != reference:
        raise AssertionError(f"Unexpected feasibility reference: {record}")
    if record.get("agency_id") != agency_id:
        raise AssertionError(f"Unexpected agency scope: {record}")
    if record.get("feasibility_outcome") != "conditionally_feasible":
        raise AssertionError(f"Non-Boolean feasibility outcome was not preserved: {record}")
    for field in [
        "operational_evaluation_ids",
        "capability_matrix_ids",
        "knowledge_version_ids",
        "constraint_ids",
        "evidence_reference_ids",
        "passenger_requirements",
        "satisfied_requirements",
        "conditionally_satisfied_requirements",
        "unknown_requirements",
        "required_ssrs",
        "required_osis",
        "required_emds",
        "required_documents",
        "required_follow_up_tasks",
        "operational_risk_reasons",
        "evidence_trace",
        "evaluation_trace",
        "decision_trace",
    ]:
        if not record.get(field):
            raise AssertionError(f"Passenger service feasibility record missing metadata dimension {field}: {record}")
    for summary_field in ["evaluation_link_summary", "requirement_summary", "action_summary", "risk_summary", "confidence_summary"]:
        if not record.get(summary_field):
            raise AssertionError(f"Passenger service feasibility projection missing {summary_field}: {record}")
    if record.get("required_airline_approval") is not True or record.get("required_manual_review") is not True:
        raise AssertionError(f"Required action metadata was not preserved: {record}")
    if record.get("feasibility_is_not_boolean") is not True or record.get("human_authority_final") is not True:
        raise AssertionError(f"Advisory feasibility flags were not preserved: {record}")
    assert_disabled_response(record)


def verify_filter(path: str, feasibility_id: str) -> None:
    response = get(path, OWNER_HEADERS)
    assert_disabled_response(response)
    item_ids = {item.get("id") for item in response.get("items", [])}
    if feasibility_id not in item_ids:
        raise AssertionError(f"Filter did not return passenger service feasibility {feasibility_id}: {path} -> {response}")


def verify_endpoints() -> None:
    post("/api/reference/seed", {}, OWNER_HEADERS)
    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    reference = run_ref("PSF-SMOKE")
    created_response = post(PLATFORM_BASE, feasibility_payload(agency_id, reference), OWNER_HEADERS, expect=201)
    assert_disabled_response(created_response)
    created = created_response.get("passenger_service_feasibility") or {}
    feasibility_id = created.get("id")
    if not feasibility_id:
        raise AssertionError(f"Create response missing passenger service feasibility: {created_response}")
    assert_created_record(created, reference, agency_id)

    updated_response = put(
        f"{PLATFORM_BASE}/{quote(feasibility_id)}",
        {
            "feasibility_status": "completed",
            "feasibility_confidence": "high",
            "recommendation_ready": True,
            "evidence_trace": created.get("evidence_trace"),
            "agent_notes": "Human reviewed metadata; still advisory only.",
        },
        OWNER_HEADERS,
    )
    assert_disabled_response(updated_response)
    updated = updated_response.get("passenger_service_feasibility") or {}
    if updated.get("feasibility_status") != "completed" or updated.get("feasibility_confidence") != "high":
        raise AssertionError(f"Update did not preserve completed/high metadata: {updated_response}")

    detail = get(f"{PLATFORM_BASE}/{quote(feasibility_id)}", OWNER_HEADERS)
    assert_created_record(detail.get("passenger_service_feasibility") or {}, reference, agency_id)
    summary = get(f"{PLATFORM_BASE}/summary", OWNER_HEADERS)
    assert_disabled_response(summary)
    if not summary.get("summary", {}).get("feasibility_count"):
        raise AssertionError(f"Platform feasibility summary missing counts: {summary}")

    filter_paths = [
        f"{PLATFORM_BASE}?agency_id={quote(agency_id)}",
        f"{PLATFORM_BASE}?feasibility_status=completed",
        f"{PLATFORM_BASE}?feasibility_type=passenger_service",
        f"{PLATFORM_BASE}?airline=LH",
        f"{PLATFORM_BASE}?feasibility_outcome=conditionally_feasible",
        f"{PLATFORM_BASE}?confidence_level=high",
        f"{PLATFORM_BASE}?operational_risk=medium",
        f"{PLATFORM_BASE}?passenger_need_category=travel_with_pet",
        f"{PLATFORM_BASE}?ssr_code=PETC",
        f"{PLATFORM_BASE}?travel_date=2028-07-01",
        f"{PLATFORM_BASE}?cabin=Economy",
        f"{PLATFORM_BASE}?destination=FRA",
        f"{PLATFORM_BASE}?recommendation_ready=true",
    ]
    for path in filter_paths:
        verify_filter(path, feasibility_id)

    agency_base = f"/api/agencies/{agency_id}/passenger-service-feasibility"
    agency_response = get(f"{agency_base}?airline=LH&feasibility_outcome=conditionally_feasible", OWNER_HEADERS)
    assert_disabled_response(agency_response)
    if agency_response.get("read_only") is not True:
        raise AssertionError(f"Agency feasibility response was not read-only: {agency_response}")
    agency_ids = {item.get("id") for item in agency_response.get("items", [])}
    if feasibility_id not in agency_ids:
        raise AssertionError(f"Agency feasibility list missing created metadata: {agency_response}")
    agency_detail = get(f"{agency_base}/{quote(feasibility_id)}", OWNER_HEADERS)
    assert_disabled_response(agency_detail)
    if agency_detail.get("read_only") is not True:
        raise AssertionError(f"Agency feasibility detail was not read-only: {agency_detail}")
    get(f"{agency_base}/summary", OWNER_HEADERS)
    request("POST", agency_base, feasibility_payload(agency_id, run_ref("PSF-AGENCY-WRITE")), OWNER_HEADERS, expect=405)
    request("PUT", f"{agency_base}/{quote(feasibility_id)}", {"feasibility_status": "blocked"}, OWNER_HEADERS, expect=405)
    request("DELETE", f"{agency_base}/{quote(feasibility_id)}", None, OWNER_HEADERS, expect=405)

    archived = request("DELETE", f"{PLATFORM_BASE}/{quote(feasibility_id)}", None, OWNER_HEADERS, expect=200)[1]
    assert_disabled_response(archived)
    if archived.get("archived") is not True or archived.get("physical_delete_disabled") is not True:
        raise AssertionError(f"Archive did not remain metadata-only soft delete: {archived}")


def verify_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")
    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("passenger_service_feasibility_engine_foundation") or {}
    for flag in [
        "passenger_service_feasibility_engine_enabled",
        "passenger_service_feasibilities_collection_enabled",
        "platform_passenger_service_feasibility_metadata_crud_enabled",
        "agency_passenger_service_feasibility_read_only_enabled",
        "platform_passenger_service_feasibility_ui_enabled",
        "agency_service_feasibility_ui_enabled",
        "consumes_operational_evaluation_results",
        "feasibility_is_not_boolean",
        "feasibility_is_explainable",
        "feasibility_is_evidence_linked",
        "feasibility_is_advisory",
        "human_authority_final",
        "feasibility_is_not_recommendation",
        "recommendation_engine_consumer_phase_50_8_enabled",
        "metadata_only",
        "advisory_only",
        "no_ai_reasoning",
        "no_llm_prompts",
        "flight_search_disabled",
        "airline_recommendation_ranking_disabled",
        "recommendation_engine_disabled",
        "booking_disabled",
        "ticketing_disabled",
        "provider_integrations_disabled",
        "parser_execution_disabled",
        "pricing_optimisation_disabled",
        "background_workers_disabled",
        "automatic_operational_decisions_disabled",
    ]:
        if section.get(flag) is not True:
            raise AssertionError(f"Readiness section missing enabled/disabled flag {flag}: {section}")
    for list_name, expected_values in [
        ("feasibility_statuses", FEASIBILITY_STATUSES),
        ("feasibility_types", FEASIBILITY_TYPES),
        ("feasibility_outcomes", FEASIBILITY_OUTCOMES),
        ("feasibility_confidence_levels", FEASIBILITY_CONFIDENCE_LEVELS),
        ("operational_risk_levels", OPERATIONAL_RISK_LEVELS),
    ]:
        if set(section.get(list_name) or []) != set(expected_values):
            raise AssertionError(f"Readiness section missing constants {list_name}: {section}")


def main() -> int:
    verify_model_and_collection_registration()
    verify_router_and_ui_registration()
    verify_metadata_only_code()
    verify_blueprint_adoption()
    verify_endpoints()
    verify_readiness()
    print("Passenger service feasibility engine foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
