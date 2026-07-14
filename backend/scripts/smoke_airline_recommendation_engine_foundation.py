#!/usr/bin/env python3
import sys
import time
from pathlib import Path
from urllib.parse import quote

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import AirlineRecommendation, AirlineRecommendationCreate
from services.airline_recommendation_engine_service import (
    AIRLINE_RECOMMENDATION_COLLECTION,
    AIRLINE_RECOMMENDATION_LEVELS,
    AIRLINE_RECOMMENDATION_STATUSES,
    PHASE_LABEL,
    RECOMMENDATION_STATUS_VALUES,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_54_6_offer_to_booking_handoff_readiness_foundation"
ROOT = Path(__file__).resolve().parents[2]
PLATFORM_BASE = "/api/platform/airline-recommendations"
AGENCY_BASE_TEMPLATE = "/api/agencies/{agency_id}/airline-recommendations"


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
        "no_live_gds_search",
        "no_ndc_search",
        "flight_search_disabled",
        "booking_disabled",
        "ticketing_disabled",
        "emd_issuance_disabled",
        "provider_integrations_disabled",
        "parser_execution_disabled",
        "no_ai_generation",
        "no_llm_generation",
        "background_workers_disabled",
    ]


def assert_disabled_response(payload: dict) -> None:
    if payload.get("metadata_only") is not True:
        raise AssertionError(f"Payload is not metadata-only: {payload}")
    if payload.get("advisory_only") is not True or payload.get("human_authority_final") is not True:
        raise AssertionError(f"Payload is not advisory/human-reviewed metadata: {payload}")
    for flag in disabled_flags():
        if payload.get(flag) is not True:
            raise AssertionError(f"Payload missing disabled flag {flag}: {payload}")


def recommendation_payload(agency_id: str, reference: str) -> dict:
    return {
        "agency_id": agency_id,
        "recommendation_reference": reference,
        "recommendation_status": "in_review",
        "recommendation_version": "50.8.0-smoke",
        "passenger_workspace_id": "PAX-WS-SMOKE-508",
        "passenger_profile_reference": "PSG-SMOKE-508",
        "passenger_need_summary": "Passenger needs PETC with station handling, document review, and manual approval metadata.",
        "passenger_need_category": "travel_with_pet",
        "travel_request_id": "TR-SMOKE-508",
        "trip_workspace_id": "TRIP-SMOKE-508",
        "itinerary_reference": "ITIN-SMOKE-508",
        "itinerary_summary": "SOF-MUC-FRA itinerary with PETC support and station review metadata.",
        "origin": "SOF",
        "destination": "FRA",
        "travel_date": "2028-07-01",
        "cabin_requested": "Economy",
        "airline_code": "LH",
        "airline_name": "Lufthansa",
        "validating_carrier": "LH",
        "operating_carrier": "LH",
        "marketing_carrier": "LH",
        "feasibility_ids": ["PSF-SMOKE-508"],
        "operational_evaluation_ids": ["OKE-SMOKE-508"],
        "capability_matrix_ids": ["ACM-SMOKE-508"],
        "knowledge_version_ids": ["AKV-SMOKE-508"],
        "evidence_reference_ids": ["EVID-SMOKE-508"],
        "recommendation_rank": 1,
        "recommendation_status_value": "preferred",
        "recommendation_summary": "LH is the preferred advisory option because feasibility, confidence, and handling evidence are strongest.",
        "operational_feasibility_score": 92,
        "operational_confidence_score": 88,
        "operational_risk_score": 24,
        "passenger_comfort_score": 84,
        "operational_complexity_score": 31,
        "ancillary_cost_score": 70,
        "ticket_cost_reference": "TICKET-COST-REF-SMOKE-508",
        "ancillary_cost_reference": "ANC-COST-REF-SMOKE-508",
        "total_cost_reference": "TOTAL-COST-REF-SMOKE-508",
        "recommendation_score": 91,
        "recommendation_level": "highly_recommended",
        "recommendation_reason": "Compared feasible options show LH has stronger station handling evidence and fewer unresolved operational constraints.",
        "recommendation_strengths": ["Official evidence available", "Strong PETC capability metadata", "Clear station handling path"],
        "recommendation_limitations": ["Final airline approval remains human-reviewed", "Ancillary cost reference is metadata only"],
        "recommendation_conditions": ["Confirm PETC approval", "Attach pet passport", "Record station notification"],
        "required_ssrs": ["PETC"],
        "required_osis": ["PET IN CABIN REVIEW REQUIRED"],
        "required_emds": ["RFIC-C-RFISC-0BT"],
        "required_documents": ["pet_passport", "vaccination_certificate"],
        "required_medif": False,
        "required_manual_review": True,
        "required_station_notification": True,
        "required_crew_notification": True,
        "compared_airlines": ["LH", "OS", "TK"],
        "compared_itineraries": ["ITIN-SMOKE-508", "ITIN-ALT-SMOKE-508"],
        "comparison_summary": "LH ranks first among feasible metadata candidates.",
        "comparison_notes": "Rows are advisory comparison metadata only and do not search, book, price, or issue documents.",
        "comparison_matrix": [
            {"category": "Operational Feasibility", "LH": "strong", "OS": "conditional", "TK": "manual_review", "preferred": "LH"},
            {"category": "Operational Confidence", "LH": "official", "OS": "reviewed", "TK": "unknown", "preferred": "LH"},
            {"category": "Passenger Comfort", "LH": "high", "OS": "medium", "TK": "medium", "preferred": "LH"},
            {"category": "Operational Risk", "LH": "low", "OS": "medium", "TK": "high", "preferred": "LH"},
            {"category": "Required Approvals", "LH": "manual", "OS": "manual", "TK": "manual", "preferred": "LH"},
            {"category": "Required Documents", "LH": "pet_passport", "OS": "pet_passport", "TK": "unknown", "preferred": "LH"},
            {"category": "Required SSRs", "LH": "PETC", "OS": "PETC", "TK": "PETC", "preferred": "LH"},
            {"category": "Required EMDs", "LH": "RFIC-C-RFISC-0BT", "OS": "unknown", "TK": "unknown", "preferred": "LH"},
            {"category": "Operational Complexity", "LH": "low", "OS": "medium", "TK": "high", "preferred": "LH"},
            {"category": "Ancillary Cost Reference", "LH": "referenced", "OS": "missing", "TK": "missing", "preferred": "LH"},
            {"category": "Overall Recommendation", "LH": "highly_recommended", "OS": "acceptable", "TK": "use_with_caution", "preferred": "LH"},
        ],
        "recommendation_evidence": [
            {"evidence_id": "EVID-SMOKE-508", "supports": "PETC capability", "source_collection": "airline_knowledge_acquisitions"}
        ],
        "recommendation_trace": [
            {"step": "feasibility_considered", "input": "PSF-SMOKE-508", "result": "conditionally_feasible"},
            {"step": "comparison_recorded", "result": "LH preferred by advisory metadata"},
        ],
        "recommendation_ready": True,
        "internal_notes": "Metadata-only recommendation. No flight search, booking, ticketing, EMD issuance, provider API, parser execution, AI generation, price generation, worker, or automation.",
        "metadata": {"smoke": True, "metadata_only": True},
    }


def verify_model_and_collection_registration() -> None:
    if AIRLINE_RECOMMENDATION_COLLECTION not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("airline_recommendations is not registered as agency-owned metadata.")
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Service phase label mismatch: {PHASE_LABEL}")

    payload = recommendation_payload("agency-smoke", "ARE-SMOKE-MODEL")
    create_model = AirlineRecommendationCreate(**payload)
    record = AirlineRecommendation(**create_model.model_dump(mode="json", exclude_none=True))
    if record.recommendation_reference != "ARE-SMOKE-MODEL":
        raise AssertionError("Airline recommendation model did not preserve reference metadata.")
    if record.recommendation_level != "highly_recommended" or record.recommendation_score != 91:
        raise AssertionError("Airline recommendation model did not preserve scoring metadata.")
    if not record.feasibility_ids or not record.comparison_matrix or not record.recommendation_evidence or not record.recommendation_trace:
        raise AssertionError("Airline recommendation model did not preserve inputs, comparison, evidence, and trace metadata.")
    if record.metadata_only is not True or record.booking_disabled is not True or record.provider_integrations_disabled is not True:
        raise AssertionError("Airline recommendation model is not metadata-only.")

    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "airline_recommendations_id_unique",
        "airline_recommendations_reference_unique",
        "airline_recommendations_agency_status_lookup",
        "airline_recommendations_airline_lookup",
        "airline_recommendations_feasibility_lookup",
        "airline_recommendations_operational_evaluation_lookup",
        "airline_recommendations_capability_matrix_lookup",
        "airline_recommendations_level_lookup",
        "airline_recommendations_score_lookup",
        "airline_recommendations_risk_score_lookup",
        "airline_recommendations_compared_airlines_lookup",
        "airline_recommendations_ready_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Database index registration missing {index_name}.")

    for value in ["draft", "in_review", "ready", "archived"]:
        if value not in AIRLINE_RECOMMENDATION_STATUSES:
            raise AssertionError(f"Missing recommendation status {value}.")
    for value in ["candidate", "preferred", "backup", "use_with_caution", "not_recommended"]:
        if value not in RECOMMENDATION_STATUS_VALUES:
            raise AssertionError(f"Missing recommendation status value {value}.")
    for value in ["highly_recommended", "recommended", "acceptable", "use_with_caution", "not_recommended"]:
        if value not in AIRLINE_RECOMMENDATION_LEVELS:
            raise AssertionError(f"Missing recommendation level {value}.")


def verify_router_and_ui_registration() -> None:
    openapi = get("/openapi.json", OWNER_HEADERS)
    paths = openapi.get("paths", {})
    for path, method in [
        (PLATFORM_BASE, "get"),
        (PLATFORM_BASE, "post"),
        (f"{PLATFORM_BASE}/summary", "get"),
        (f"{PLATFORM_BASE}/{{recommendation_id}}", "get"),
        (f"{PLATFORM_BASE}/{{recommendation_id}}", "put"),
        (f"{PLATFORM_BASE}/{{recommendation_id}}", "delete"),
        ("/api/agencies/{agency_id}/airline-recommendations", "get"),
        ("/api/agencies/{agency_id}/airline-recommendations/summary", "get"),
        ("/api/agencies/{agency_id}/airline-recommendations/{recommendation_id}", "get"),
    ]:
        assert_openapi_path(paths, path, method)

    for path in paths:
        if "airline-recommendations" in path:
            for forbidden in ["flight-search", "bookings/live", "tickets/issue", "emds/issue", "providers", "execute", "ai-generate"]:
                if forbidden in path:
                    raise AssertionError(f"Forbidden execution route exposed for recommendation engine: {path}")

    for path, text in [
        (ROOT / "frontend/src/App.jsx", "/platform/airline-recommendations"),
        (ROOT / "frontend/src/App.jsx", "/agency/recommendations"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Airline Recommendations"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Recommendations"),
        (ROOT / "frontend/src/pages/platform/AirlineRecommendationsPage.jsx", "Recommendation Dashboard"),
        (ROOT / "frontend/src/pages/platform/AirlineRecommendationsPage.jsx", "Comparison Matrix"),
        (ROOT / "frontend/src/pages/platform/AirlineRecommendationsPage.jsx", "Recommendation Explanation"),
        (ROOT / "frontend/src/pages/agency/RecommendationsPage.jsx", "Read-only advisory recommendation metadata"),
        (ROOT / "docs/architecture/airline-recommendation-engine-foundation.md", "Recommendation is not feasibility"),
        (ROOT / "docs/architecture/airline-recommendation-engine-foundation.md", "does not implement live GDS search"),
        (ROOT / "docs/architecture/current-model-inventory.md", "airline_recommendations"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/api/platform/airline-recommendations"),
        (ROOT / "docs/architecture/airline-operational-intelligence-engine-foundation.md", "Phase 50.8 adds the `airline_recommendations` collection"),
        (ROOT / "docs/architecture/passenger-service-feasibility-engine-foundation.md", "Phase 50.8 consumes feasibility metadata"),
        (ROOT / "docs/architecture/foundations/AIRLINE_OPERATIONAL_KNOWLEDGE_BLUEPRINT.md", "Phase 50.8 implements"),
        (ROOT / "docs/architecture/foundations/AEROASSIST_ENGINEERING_PRINCIPLES.md", "Airline Recommendation is advisory preference metadata"),
        (ROOT / "docs/architecture/foundations/GLOSSARY.md", "An advisory output that suggests airline or itinerary options"),
    ]:
        require_text(path, text)

    for path in [
        ROOT / "frontend/src/pages/platform/AirlineRecommendationsPage.jsx",
        ROOT / "frontend/src/pages/agency/RecommendationsPage.jsx",
    ]:
        reject_text(path, "apiPost")
        reject_text(path, "apiPut")
        reject_text(path, "apiDelete")
        for forbidden in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, forbidden)


def verify_metadata_only_code() -> None:
    implementation_paths = [
        ROOT / "backend/services/airline_recommendation_engine_service.py",
        ROOT / "backend/routers/platform_airline_recommendations.py",
        ROOT / "backend/routers/agency_airline_recommendations.py",
        ROOT / "frontend/src/pages/platform/AirlineRecommendationsPage.jsx",
        ROOT / "frontend/src/pages/agency/RecommendationsPage.jsx",
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
        "create_booking(",
        "issue_ticket(",
        "issue_emd(",
        "provider_client",
        "execute_parser(",
        "generate_price(",
        "calculate_fare(",
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
    if "Airline Recommendations" not in categories:
        raise AssertionError(f"Blueprint adoption map missing Airline Recommendations category: {categories}")

    route_policy = get("/api/platform/blueprint/route-policy", OWNER_HEADERS)
    mappings = route_policy.get("route_mappings") or []
    expected_pairs = {
        ("/admin/airline-recommendations", "/platform/airline-recommendations"),
        ("/agent/recommendations", "/agency/recommendations"),
    }
    actual_pairs = {(item.get("supplementary"), item.get("agencyos")) for item in mappings}
    missing = expected_pairs - actual_pairs
    if missing:
        raise AssertionError(f"Route policy missing airline recommendation canonical mappings: {missing}")

    gaps = get("/api/platform/blueprint/gaps", OWNER_HEADERS)
    if "Airline recommendation engine foundation built in Phase 50.8" not in gaps.get("already_built", []):
        raise AssertionError(f"Gap summary missing Phase 50.8 recommendation marker: {gaps}")
    if "Phase 50.9" not in gaps.get("next_intelligence_phase", ""):
        raise AssertionError(f"Gap summary missing Phase 50.9 next intelligence phase: {gaps}")

    next_phases = get("/api/platform/blueprint/next-phases", OWNER_HEADERS)
    if not next_phases.get("items") or next_phases["items"][0].get("phase") != "Phase 50.9":
        raise AssertionError(f"Next recommendations did not start with Phase 50.9: {next_phases}")


def assert_created_record(record: dict, reference: str, agency_id: str) -> None:
    if record.get("recommendation_reference") != reference:
        raise AssertionError(f"Unexpected recommendation reference: {record}")
    if record.get("agency_id") != agency_id:
        raise AssertionError(f"Unexpected agency scope: {record}")
    if record.get("recommendation_level") != "highly_recommended" or record.get("recommendation_score") < 90:
        raise AssertionError(f"Recommendation scoring metadata was not preserved: {record}")
    for field in [
        "feasibility_ids",
        "operational_evaluation_ids",
        "capability_matrix_ids",
        "knowledge_version_ids",
        "evidence_reference_ids",
        "comparison_matrix",
        "recommendation_evidence",
        "recommendation_trace",
        "required_ssrs",
        "required_emds",
        "required_documents",
    ]:
        if not record.get(field):
            raise AssertionError(f"Created recommendation missing {field}: {record}")
    if record.get("recommendation_is_not_feasibility") is not True or record.get("consumes_passenger_service_feasibility") is not True:
        raise AssertionError(f"Recommendation/feasibility separation flags missing: {record}")
    for summary_field in ["input_reference_summary", "score_summary", "action_summary", "comparison_metadata_summary", "evidence_summary"]:
        if not isinstance(record.get(summary_field), dict):
            raise AssertionError(f"Projection missing {summary_field}: {record}")
    if record["comparison_metadata_summary"].get("comparison_rows", 0) < 11:
        raise AssertionError(f"Comparison matrix summary did not count structured categories: {record}")
    assert_disabled_response(record)


def find_record(payload: dict, reference: str) -> dict:
    for item in payload.get("items") or payload.get("recommendations") or []:
        if item.get("recommendation_reference") == reference:
            return item
    raise AssertionError(f"Recommendation {reference} not found in payload: {payload}")


def verify_recommendation_crud_and_filters() -> None:
    post("/api/reference/seed", {}, OWNER_HEADERS)
    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    reference = run_ref("ARE-SMOKE-508")
    payload = recommendation_payload(agency_id, reference)

    created_response = post(PLATFORM_BASE, payload, OWNER_HEADERS, 201)
    assert_disabled_response(created_response)
    created = created_response.get("airline_recommendation") or {}
    recommendation_id = created.get("id")
    if not recommendation_id:
        raise AssertionError(f"Create response missing recommendation id: {created_response}")
    assert_created_record(created, reference, agency_id)

    quoted_id = quote(recommendation_id)
    detail = get(f"{PLATFORM_BASE}/{quoted_id}", OWNER_HEADERS)
    assert_created_record(detail.get("airline_recommendation") or {}, reference, agency_id)

    updated = put(
        f"{PLATFORM_BASE}/{quoted_id}",
        {
            "recommendation_status": "ready",
            "recommendation_score": 93,
            "recommendation_trace": [
                {"step": "ready_review", "result": "ready metadata reviewed for advisory comparison"}
            ],
            "internal_notes": "Updated by smoke as metadata-only advisory recommendation.",
        },
        OWNER_HEADERS,
    )
    updated_record = updated.get("airline_recommendation") or {}
    if updated_record.get("recommendation_status") != "ready" or updated_record.get("recommendation_score") != 93:
        raise AssertionError(f"Update did not preserve ready recommendation metadata: {updated_record}")
    assert_disabled_response(updated_record)

    query_checks = [
        f"?agency_id={quote(agency_id)}",
        "?recommendation_status=ready",
        "?airline=LH",
        "?recommendation_level=highly_recommended",
        "?operational_score=90",
        "?risk=25",
        "?passenger_need_category=travel_with_pet",
        "?cabin=Economy",
        "?destination=FRA",
        "?travel_date=2028-07-01",
    ]
    for query in query_checks:
        result = get(f"{PLATFORM_BASE}{query}", OWNER_HEADERS)
        assert_disabled_response(result)
        assert_created_record(find_record(result, reference), reference, agency_id)

    summary = get(f"{PLATFORM_BASE}/summary", OWNER_HEADERS)
    assert_disabled_response(summary)
    for key in [
        "recommendation_count",
        "by_recommendation_status",
        "by_recommendation_level",
        "recommendation_ready_count",
        "feasibility_reference_count",
        "comparison_matrix_count",
        "recommendation_evidence_count",
        "recommendation_trace_count",
        "required_action_count",
    ]:
        if key not in (summary.get("summary") or {}):
            raise AssertionError(f"Platform summary missing recommendation count {key}: {summary}")

    agency_base = AGENCY_BASE_TEMPLATE.format(agency_id=quote(agency_id))
    agency_list = get(f"{agency_base}?airline=LH&recommendation_level=highly_recommended", OWNER_HEADERS)
    assert_disabled_response(agency_list)
    if agency_list.get("read_only") is not True:
        raise AssertionError(f"Agency recommendation list is not read-only: {agency_list}")
    agency_record = find_record(agency_list, reference)
    assert_created_record(agency_record, reference, agency_id)
    if agency_record.get("read_only") is not True:
        raise AssertionError(f"Agency recommendation item is not read-only: {agency_record}")

    agency_detail = get(f"{agency_base}/{quoted_id}", OWNER_HEADERS)
    assert_disabled_response(agency_detail)
    assert_created_record(agency_detail.get("airline_recommendation") or {}, reference, agency_id)

    agency_summary = get(f"{agency_base}/summary", OWNER_HEADERS)
    assert_disabled_response(agency_summary)
    if agency_summary.get("read_only") is not True:
        raise AssertionError(f"Agency summary is not read-only: {agency_summary}")

    post(agency_base, payload, OWNER_HEADERS, 405)
    put(f"{agency_base}/{quoted_id}", {"recommendation_status": "archived"}, OWNER_HEADERS, 405)
    request("DELETE", f"{agency_base}/{quoted_id}", None, OWNER_HEADERS, 405)

    archived = request("DELETE", f"{PLATFORM_BASE}/{quoted_id}", None, OWNER_HEADERS)[1]
    if archived.get("archived") is not True:
        raise AssertionError(f"Platform archive did not soft-archive recommendation metadata: {archived}")
    assert_disabled_response(archived)


def verify_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected active phase label: {health.get('phase')}")

    readiness = get("/api/readiness")
    section = readiness.get("airline_recommendation_engine_foundation") or {}
    for flag in [
        "airline_recommendation_engine_enabled",
        "airline_recommendations_collection_enabled",
        "platform_airline_recommendation_metadata_crud_enabled",
        "agency_airline_recommendation_read_only_enabled",
        "platform_airline_recommendations_ui_enabled",
        "agency_recommendations_ui_enabled",
        "consumes_passenger_service_feasibility",
        "recommendation_is_not_feasibility",
        "recommendation_compares_feasible_airlines",
        "recommendation_is_advisory",
        "human_authority_final",
        "recommendation_dashboard_metadata_enabled",
        "comparison_matrix_metadata_enabled",
        "recommendation_card_metadata_enabled",
        "operational_scores_metadata_enabled",
        "commercial_scores_metadata_enabled",
        "required_action_metadata_enabled",
        "recommendation_explanation_metadata_enabled",
        "recommendation_evidence_metadata_enabled",
        "future_50_9_offer_builder_consumer_only",
        "metadata_only",
        "advisory_only",
        "no_live_gds_search",
        "no_ndc_search",
        "flight_search_disabled",
        "booking_disabled",
        "ticketing_disabled",
        "emd_issuance_disabled",
        "provider_integrations_disabled",
        "parser_execution_disabled",
        "no_ai_generation",
        "no_llm_generation",
        "background_workers_disabled",
    ]:
        if section.get(flag) is not True:
            raise AssertionError(f"Readiness missing recommendation flag {flag}: {section}")
    for key in [
        "airline_recommendation_count",
        "airline_recommendation_status_counts",
        "airline_recommendation_level_counts",
        "airline_recommendation_status_value_counts",
        "airline_recommendation_ready_count",
        "airline_recommendation_feasibility_reference_count",
        "airline_recommendation_comparison_matrix_count",
        "airline_recommendation_evidence_count",
        "airline_recommendation_trace_count",
        "airline_recommendation_required_action_count",
    ]:
        if key not in section:
            raise AssertionError(f"Readiness missing recommendation count {key}: {section}")
    if section.get("recommendation_statuses") != AIRLINE_RECOMMENDATION_STATUSES:
        raise AssertionError(f"Readiness statuses mismatch: {section}")
    if section.get("recommendation_status_values") != RECOMMENDATION_STATUS_VALUES:
        raise AssertionError(f"Readiness status values mismatch: {section}")
    if section.get("recommendation_levels") != AIRLINE_RECOMMENDATION_LEVELS:
        raise AssertionError(f"Readiness levels mismatch: {section}")
    if section.get("readiness_required") is not False:
        raise AssertionError("Airline recommendation foundation should not be deployment-readiness required.")


def main() -> int:
    verify_model_and_collection_registration()
    verify_router_and_ui_registration()
    verify_metadata_only_code()
    verify_blueprint_adoption()
    verify_recommendation_crud_and_filters()
    verify_readiness()
    print("Phase 50.8 airline recommendation engine smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
