#!/usr/bin/env python3
import sys
import time
from pathlib import Path
from urllib.parse import quote

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import OperationalKnowledgeEvaluation, OperationalKnowledgeEvaluationCreate
from services.operational_knowledge_evaluation_service import (
    EVALUATION_CONFIDENCE_LEVELS,
    EVALUATION_RESULT_VALUES,
    EVALUATION_STATUSES,
    EVALUATION_TYPES,
    OPERATIONAL_KNOWLEDGE_EVALUATION_COLLECTION,
    OPERATIONAL_RESULTS,
    OPERATIONAL_RISK_LEVELS,
    PHASE_LABEL,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_53_0_end_to_end_stabilization_pilot_readiness_foundation"
ROOT = Path(__file__).resolve().parents[2]
PLATFORM_BASE = "/api/platform/operational-evaluations"


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
        "itinerary_recommendation_disabled",
        "booking_disabled",
        "ticketing_disabled",
        "provider_integrations_disabled",
        "parser_execution_disabled",
        "pricing_optimisation_disabled",
        "background_workers_disabled",
        "feasibility_determination_disabled",
        "recommendation_engine_disabled",
    ]


def assert_disabled_response(payload: dict) -> None:
    if payload.get("metadata_only") is not True:
        raise AssertionError(f"Payload is not metadata-only: {payload}")
    for flag in disabled_flags():
        if payload.get(flag) is not True:
            raise AssertionError(f"Payload missing disabled flag {flag}: {payload}")


def evaluation_payload(agency_id: str, reference: str) -> dict:
    return {
        "agency_id": agency_id,
        "evaluation_reference": reference,
        "evaluation_status": "in_review",
        "evaluation_type": "capability_policy_pricing_constraint_procedure",
        "evaluation_version": "50.6.0-smoke",
        "passenger_workspace_id": "PAX-WS-SMOKE-506",
        "passenger_profile_reference": "PSG-SMOKE-506",
        "passenger_need_summary": "Passenger requests PETC with governed source evidence.",
        "travel_request_id": "TR-SMOKE-506",
        "trip_workspace_id": "TRIP-SMOKE-506",
        "booking_workspace_id": "BKG-SMOKE-506",
        "airline_code": "LH",
        "validating_carrier": "LH",
        "operating_carrier": "LH",
        "marketing_carrier": "LH",
        "knowledge_version_ids": ["AKV-SMOKE-506"],
        "capability_matrix_ids": ["ACM-SMOKE-506"],
        "operational_constraint_ids": ["OC-SMOKE-506"],
        "acquisition_ids": ["AKA-SMOKE-506"],
        "evidence_reference_ids": ["EVID-SMOKE-506"],
        "evaluated_service_domains": ["animal_transport"],
        "evaluated_service_families": ["pet_transport"],
        "evaluated_ssrs": ["PETC"],
        "evaluated_osis": ["PET IN CABIN REVIEW REQUIRED"],
        "evaluated_emd_requirements": ["RFIC-C-RFISC-0BT"],
        "evaluation_completed": True,
        "evaluation_confidence": "official",
        "evaluation_reasoning_available": True,
        "capability_result": "pass",
        "capability_reason": "Capability matrix metadata states PETC can be supported under listed aircraft and station conditions.",
        "capability_evidence": [{"evidence_id": "EVID-SMOKE-506", "source": "governed_release", "field": "petc_capability"}],
        "policy_result": "warning",
        "policy_reason": "Policy metadata requires advance carrier review for PETC dimensions.",
        "policy_evidence": [{"evidence_id": "EVID-POLICY-SMOKE-506", "source": "knowledge_acquisition"}],
        "pricing_result": "manual_review",
        "pricing_reason": "Pricing metadata references EMD requirement but does not calculate fare.",
        "pricing_reference": "PRICE-SMOKE-506",
        "constraint_result": "warning",
        "constraint_reason": "Station and aircraft constraints require manual review.",
        "triggered_constraints": ["OC-SMOKE-506"],
        "blocking_constraints": [],
        "warning_constraints": ["ADVANCE_NOTICE_REQUIRED"],
        "operational_procedure_result": "manual_review",
        "operational_procedure_reason": "Station notification and crew awareness metadata apply.",
        "operational_result": "conditional",
        "operational_summary": "PETC appears operationally applicable with manual review and station notification metadata.",
        "operational_notes": "This evaluation stores metadata only and does not execute booking, ticketing, pricing, provider, or communication actions.",
        "required_ssrs": ["PETC"],
        "required_osis": ["PET IN CABIN REVIEW REQUIRED"],
        "required_emds": ["RFIC-C-RFISC-0BT"],
        "required_documents": ["pet_passport"],
        "required_medif": False,
        "required_manual_review": True,
        "required_airline_approval": True,
        "required_station_notification": True,
        "required_crew_notification": True,
        "evaluation_steps": [
            {"step": "read_governed_knowledge", "result": "referenced"},
            {"step": "compare_capability_matrix", "result": "conditional_match"},
            {"step": "collect_required_actions", "result": "metadata_only"},
        ],
        "evaluated_objects": [
            {"object_type": "capability_matrix", "object_id": "ACM-SMOKE-506"},
            {"object_type": "operational_constraint", "object_id": "OC-SMOKE-506"},
        ],
        "evidence_trace": [
            {"evidence_id": "EVID-SMOKE-506", "supports": "capability", "source_collection": "airline_knowledge_acquisitions"},
            {"evidence_id": "EVID-POLICY-SMOKE-506", "supports": "policy", "source_collection": "airline_knowledge_versions"},
        ],
        "structured_explanation": {
            "reason": "PETC metadata applies conditionally.",
            "evidence": ["EVID-SMOKE-506", "EVID-POLICY-SMOKE-506"],
            "capability": "conditional capability match",
            "constraint": "station review warning",
            "procedure": "manual station notification review",
        },
        "operational_risk": "medium",
        "operational_risk_reason": "Station, aircraft, and advance notice conditions must be reviewed by staff.",
        "feasibility_ready": True,
        "recommendation_ready": False,
        "internal_notes": "No AI, LLM, flight search, itinerary recommendation, booking, ticketing, provider integration, parser execution, pricing optimisation, worker, or automation.",
        "metadata": {"smoke": True, "metadata_only": True},
    }


def verify_model_and_collection_registration() -> None:
    if OPERATIONAL_KNOWLEDGE_EVALUATION_COLLECTION not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("operational_knowledge_evaluations is not registered as agency-owned metadata.")
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Service phase label mismatch: {PHASE_LABEL}")

    payload = evaluation_payload("agency-smoke", "OKE-SMOKE-MODEL")
    create_model = OperationalKnowledgeEvaluationCreate(**payload)
    record = OperationalKnowledgeEvaluation(**create_model.model_dump(mode="json", exclude_none=True))
    if record.evaluation_reference != "OKE-SMOKE-MODEL":
        raise AssertionError("Operational evaluation model did not preserve reference metadata.")
    if record.capability_result != "pass" or record.policy_result != "warning" or record.pricing_result != "manual_review":
        raise AssertionError("Operational evaluation model did not preserve evaluation result metadata.")
    if not record.evidence_trace or not record.structured_explanation:
        raise AssertionError("Operational evaluation model did not preserve explanation or evidence metadata.")
    if record.metadata_only is not True or record.no_ai_reasoning is not True or record.recommendation_engine_disabled is not True:
        raise AssertionError("Operational evaluation model is not metadata-only.")

    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "operational_knowledge_evaluations_id_unique",
        "operational_knowledge_evaluations_reference_unique",
        "operational_knowledge_evaluations_agency_status_lookup",
        "operational_knowledge_evaluations_airline_lookup",
        "operational_knowledge_evaluations_knowledge_version_lookup",
        "operational_knowledge_evaluations_capability_matrix_lookup",
        "operational_knowledge_evaluations_constraint_lookup",
        "operational_knowledge_evaluations_acquisition_lookup",
        "operational_knowledge_evaluations_evidence_lookup",
        "operational_knowledge_evaluations_service_domain_lookup",
        "operational_knowledge_evaluations_ssr_lookup",
        "operational_knowledge_evaluations_capability_result_lookup",
        "operational_knowledge_evaluations_policy_result_lookup",
        "operational_knowledge_evaluations_pricing_result_lookup",
        "operational_knowledge_evaluations_constraint_result_lookup",
        "operational_knowledge_evaluations_operational_result_lookup",
        "operational_knowledge_evaluations_required_review_approval_lookup",
        "operational_knowledge_evaluations_future_readiness_lookup",
        "operational_knowledge_evaluations_archive_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Operational knowledge evaluation index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    expected_methods = {
        "/api/platform/operational-evaluations": {"get", "post"},
        "/api/platform/operational-evaluations/summary": {"get"},
        "/api/platform/operational-evaluations/{evaluation_id}": {"get", "put", "delete"},
        "/api/agencies/{agency_id}/operational-evaluations": {"get"},
        "/api/agencies/{agency_id}/operational-evaluations/summary": {"get"},
        "/api/agencies/{agency_id}/operational-evaluations/{evaluation_id}": {"get"},
    }
    for path, methods in expected_methods.items():
        for method in methods:
            assert_openapi_path(paths, path, method)

    for path in [
        "/api/agencies/{agency_id}/operational-evaluations",
        "/api/agencies/{agency_id}/operational-evaluations/summary",
        "/api/agencies/{agency_id}/operational-evaluations/{evaluation_id}",
    ]:
        blocked_methods = set(paths.get(path, {}).keys()) & {"post", "put", "patch", "delete"}
        if blocked_methods:
            raise AssertionError(f"Agency operational evaluation route is not read-only: {path} {sorted(blocked_methods)}")

    forbidden_route_terms = [
        "recommend",
        "flight-search",
        "book",
        "ticket",
        "provider",
        "execute",
        "ai",
        "llm",
    ]
    for path in paths:
        if "operational-evaluations" in path and any(term in path for term in forbidden_route_terms):
            raise AssertionError(f"Forbidden operational evaluation execution route should not exist: {path}")
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/App.jsx", "/platform/operational-evaluations"),
        (ROOT / "frontend/src/App.jsx", "/agency/operational-evaluations"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Operational Knowledge Evaluations"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Operational Evaluations"),
        (ROOT / "frontend/src/pages/platform/OperationalEvaluationsPage.jsx", "Evaluation Overview"),
        (ROOT / "frontend/src/pages/platform/OperationalEvaluationsPage.jsx", "Capability Evaluation"),
        (ROOT / "frontend/src/pages/platform/OperationalEvaluationsPage.jsx", "Policy Evaluation"),
        (ROOT / "frontend/src/pages/platform/OperationalEvaluationsPage.jsx", "Pricing Evaluation"),
        (ROOT / "frontend/src/pages/platform/OperationalEvaluationsPage.jsx", "Constraint Evaluation"),
        (ROOT / "frontend/src/pages/platform/OperationalEvaluationsPage.jsx", "Procedure Evaluation"),
        (ROOT / "frontend/src/pages/platform/OperationalEvaluationsPage.jsx", "Required Operational Actions"),
        (ROOT / "frontend/src/pages/platform/OperationalEvaluationsPage.jsx", "Evidence Trace"),
        (ROOT / "frontend/src/pages/platform/OperationalEvaluationsPage.jsx", "Evaluation is not recommendation"),
        (ROOT / "frontend/src/pages/agency/OperationalEvaluationsPage.jsx", "Read-only operational knowledge evaluation metadata"),
        (ROOT / "frontend/src/pages/agency/OperationalEvaluationsPage.jsx", "Evaluation is not recommendation"),
        (ROOT / "docs/architecture/operational-knowledge-evaluation-engine-foundation.md", "Evaluation Is Not Recommendation"),
        (ROOT / "docs/architecture/operational-knowledge-evaluation-engine-foundation.md", "Evaluation determines what operationally applies"),
        (ROOT / "docs/architecture/current-model-inventory.md", "operational_knowledge_evaluations"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/api/platform/operational-evaluations"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/api/agencies/{agency_id}/operational-evaluations"),
        (ROOT / "docs/architecture/airline-operational-intelligence-engine-foundation.md", "50.6 Operational Knowledge Evaluation Engine Foundation"),
        (ROOT / "docs/architecture/airline-operational-capability-matrix-foundation.md", "Phase 50.6 consumes the matrix"),
        (ROOT / "docs/architecture/foundations/AIRLINE_OPERATIONAL_KNOWLEDGE_BLUEPRINT.md", "50.6 Operational Knowledge Evaluation Engine"),
        (ROOT / "README.md", "Phase 50.6 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 50.6: Operational Knowledge Evaluation Engine Foundation"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Operational knowledge evaluation"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Operational Knowledge Evaluations"),
    ]:
        require_text(path, text)

    for path, text in [
        (ROOT / "frontend/src/pages/platform/OperationalEvaluationsPage.jsx", "apiPost"),
        (ROOT / "frontend/src/pages/platform/OperationalEvaluationsPage.jsx", "apiPut"),
        (ROOT / "frontend/src/pages/platform/OperationalEvaluationsPage.jsx", "apiDelete"),
        (ROOT / "frontend/src/pages/agency/OperationalEvaluationsPage.jsx", "apiPost"),
        (ROOT / "frontend/src/pages/agency/OperationalEvaluationsPage.jsx", "apiPut"),
        (ROOT / "frontend/src/pages/agency/OperationalEvaluationsPage.jsx", "apiDelete"),
    ]:
        reject_text(path, text)


def verify_metadata_only_implementation() -> None:
    checked_files = [
        ROOT / "backend/services/operational_knowledge_evaluation_service.py",
        ROOT / "backend/routers/platform_operational_evaluations.py",
        ROOT / "backend/routers/agency_operational_evaluations.py",
        ROOT / "frontend/src/pages/platform/OperationalEvaluationsPage.jsx",
        ROOT / "frontend/src/pages/agency/OperationalEvaluationsPage.jsx",
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
        "recommend_itinerary(",
        "recommend_airline(",
        "score_feasibility(",
        "determine_feasibility(",
        "create_booking(",
        "issue_ticket(",
        "provider_client",
        "execute_parser(",
        "optimise_pricing(",
        "optimize_pricing(",
        "llm_prompt(",
        "ChatCompletion",
    ]
    for path in checked_files:
        content = path.read_text(encoding="utf-8")
        for term in forbidden_terms:
            if term in content:
                raise AssertionError(f"Forbidden implementation term {term!r} found in {path.relative_to(ROOT)}")


def verify_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase label: {health.get('phase')}")

    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase label: {readiness.get('phase')}")
    evaluation = readiness.get("operational_knowledge_evaluation_engine_foundation") or {}
    for key in [
        "operational_knowledge_evaluation_engine_enabled",
        "operational_knowledge_evaluations_collection_enabled",
        "platform_operational_evaluations_metadata_crud_enabled",
        "agency_operational_evaluations_read_only_enabled",
        "platform_operational_evaluations_ui_enabled",
        "agency_operational_evaluations_ui_enabled",
        "evaluation_is_deterministic",
        "evaluation_is_explainable",
        "evaluation_always_references_evidence",
        "evaluation_is_not_recommendation",
        "evaluation_does_not_determine_passenger_feasibility",
        "knowledge_acquisition_consumer",
        "knowledge_normalisation_consumer",
        "operational_constraints_consumer",
        "knowledge_governance_consumer",
        "capability_matrix_consumer",
        "structured_explanation_metadata_enabled",
        "capability_evaluation_metadata_enabled",
        "policy_evaluation_metadata_enabled",
        "pricing_evaluation_metadata_enabled",
        "constraint_evaluation_metadata_enabled",
        "procedure_evaluation_metadata_enabled",
        "operational_action_metadata_enabled",
        "evidence_trace_metadata_enabled",
        "future_50_7_feasibility_consumer_only",
        "future_50_8_recommendation_consumer_only",
        "future_50_9_offer_builder_consumer_only",
        *disabled_flags(),
    ]:
        if evaluation.get(key) is not True:
            raise AssertionError(f"Readiness missing operational evaluation flag {key}: {evaluation}")
    if evaluation.get("readiness_required") is not False:
        raise AssertionError("Operational evaluation foundation should not be deployment-readiness required.")
    if evaluation.get("evaluation_statuses") != EVALUATION_STATUSES:
        raise AssertionError("Readiness did not expose evaluation statuses.")
    if evaluation.get("evaluation_types") != EVALUATION_TYPES:
        raise AssertionError("Readiness did not expose evaluation types.")
    if evaluation.get("evaluation_result_values") != EVALUATION_RESULT_VALUES:
        raise AssertionError("Readiness did not expose evaluation result values.")
    if evaluation.get("operational_results") != OPERATIONAL_RESULTS:
        raise AssertionError("Readiness did not expose operational results.")
    if evaluation.get("evaluation_confidence_levels") != EVALUATION_CONFIDENCE_LEVELS:
        raise AssertionError("Readiness did not expose evaluation confidence levels.")
    if evaluation.get("operational_risk_levels") != OPERATIONAL_RISK_LEVELS:
        raise AssertionError("Readiness did not expose operational risk levels.")
    for key in [
        "operational_knowledge_evaluation_count",
        "operational_knowledge_evaluation_status_counts",
        "operational_knowledge_evaluation_type_counts",
        "operational_knowledge_evaluation_confidence_counts",
        "operational_knowledge_evaluation_capability_result_counts",
        "operational_knowledge_evaluation_policy_result_counts",
        "operational_knowledge_evaluation_pricing_result_counts",
        "operational_knowledge_evaluation_constraint_result_counts",
        "operational_knowledge_evaluation_procedure_result_counts",
        "operational_knowledge_evaluation_operational_result_counts",
        "operational_knowledge_evaluation_risk_counts",
        "operational_knowledge_evaluation_completed_count",
        "operational_knowledge_evaluation_source_reference_count",
        "operational_knowledge_evaluation_evidence_trace_count",
        "operational_knowledge_evaluation_required_action_count",
        "operational_knowledge_evaluation_feasibility_ready_count",
        "operational_knowledge_evaluation_recommendation_ready_count",
    ]:
        if key not in evaluation:
            raise AssertionError(f"Readiness missing operational evaluation count {key}: {evaluation}")


def verify_blueprint_adoption() -> None:
    adoption = get("/api/platform/blueprint/adoption-map", OWNER_HEADERS)
    categories = {item.get("category") for item in adoption.get("items", [])}
    if "Operational Knowledge Evaluations" not in categories:
        raise AssertionError("Blueprint adoption map missing Operational Knowledge Evaluations.")

    route_policy = get("/api/platform/blueprint/route-policy", OWNER_HEADERS)
    mappings = route_policy.get("route_mappings") or []
    expected_pairs = {
        ("/admin/operational-evaluations", "/platform/operational-evaluations"),
        ("/agent/operational-evaluations", "/agency/operational-evaluations"),
    }
    actual_pairs = {(item.get("supplementary"), item.get("agencyos")) for item in mappings}
    missing = expected_pairs - actual_pairs
    if missing:
        raise AssertionError(f"Route policy missing operational evaluation canonical mappings: {missing}")

    gaps = get("/api/platform/blueprint/gaps", OWNER_HEADERS)
    if "Operational knowledge evaluation engine foundation built in Phase 50.6" not in gaps.get("already_built", []):
        raise AssertionError(f"Gap summary missing Phase 50.6 operational evaluation marker: {gaps}")
    if "Phase 50.9" not in gaps.get("next_intelligence_phase", ""):
        raise AssertionError(f"Gap summary missing Phase 50.9 next intelligence phase: {gaps}")

    next_phases = get("/api/platform/blueprint/next-phases", OWNER_HEADERS)
    if not next_phases.get("items") or next_phases["items"][0].get("phase") != "Phase 50.9":
        raise AssertionError(f"Next recommendations did not start with Phase 50.9: {next_phases}")


def assert_created_record(record: dict, reference: str, agency_id: str) -> None:
    if record.get("evaluation_reference") != reference:
        raise AssertionError(f"Unexpected evaluation reference: {record}")
    if record.get("agency_id") != agency_id:
        raise AssertionError(f"Unexpected agency scope: {record}")
    for field in [
        "knowledge_version_ids",
        "capability_matrix_ids",
        "operational_constraint_ids",
        "acquisition_ids",
        "evidence_reference_ids",
        "evaluated_service_domains",
        "evaluated_service_families",
        "evaluated_ssrs",
        "capability_evidence",
        "policy_evidence",
        "evaluation_steps",
        "evaluated_objects",
        "evidence_trace",
        "structured_explanation",
    ]:
        if not record.get(field):
            raise AssertionError(f"Operational evaluation record missing metadata dimension {field}: {record}")
    if record.get("capability_result") != "pass" or record.get("policy_result") != "warning":
        raise AssertionError(f"Evaluation result metadata was not preserved: {record}")
    if not record.get("source_summary") or not record.get("scope_summary") or not record.get("action_summary"):
        raise AssertionError(f"Operational evaluation projection missing summaries: {record}")
    assert_disabled_response(record)


def verify_filter(path: str, evaluation_id: str) -> None:
    response = get(path, OWNER_HEADERS)
    assert_disabled_response(response)
    item_ids = {item.get("id") for item in response.get("items", [])}
    if evaluation_id not in item_ids:
        raise AssertionError(f"Filter did not return operational evaluation {evaluation_id}: {path} -> {response}")


def verify_endpoints() -> None:
    post("/api/reference/seed", {}, OWNER_HEADERS)
    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    reference = run_ref("OKE-SMOKE")
    created = post(PLATFORM_BASE, evaluation_payload(agency_id, reference), OWNER_HEADERS, 201)
    assert_disabled_response(created)
    record = created.get("operational_knowledge_evaluation") or {}
    evaluation_id = record.get("id")
    if not evaluation_id:
        raise AssertionError(f"Created operational evaluation response missing id: {created}")
    assert_created_record(record, reference, agency_id)

    updated = put(
        f"{PLATFORM_BASE}/{evaluation_id}",
        {
            "evaluation_status": "completed",
            "evaluation_confidence": "high",
            "operational_result": "conditional",
            "operational_risk": "medium",
            "internal_notes": "Reviewed metadata only. No feasibility or recommendation decision.",
        },
        OWNER_HEADERS,
    )
    assert_disabled_response(updated)
    updated_record = updated.get("operational_knowledge_evaluation") or {}
    if updated_record.get("evaluation_status") != "completed":
        raise AssertionError(f"Update did not persist completed status: {updated}")
    if updated_record.get("evaluation_confidence") != "high":
        raise AssertionError(f"Update did not persist confidence metadata: {updated}")

    for query in [
        f"agency_id={quote(agency_id)}",
        "evaluation_status=completed",
        "evaluation_type=capability_policy_pricing_constraint_procedure",
        "airline=LH",
        "passenger=PSG-SMOKE-506",
        "travel_request_id=TR-SMOKE-506",
        "trip_workspace_id=TRIP-SMOKE-506",
        "booking_workspace_id=BKG-SMOKE-506",
        "service_domain=animal_transport",
        "service_family=pet_transport",
        "ssr_code=PETC",
        "capability_result=pass",
        "policy_result=warning",
        "pricing_result=manual_review",
        "constraint_result=warning",
        "operational_result=conditional",
        "operational_risk=medium",
        "confidence=high",
        "evaluation_completed=true",
    ]:
        verify_filter(f"{PLATFORM_BASE}?{query}", evaluation_id)

    platform_summary = get(f"{PLATFORM_BASE}/summary", OWNER_HEADERS)
    assert_disabled_response(platform_summary)
    if "by_capability_result" not in platform_summary.get("summary", {}):
        raise AssertionError(f"Platform summary missing capability evaluation counts: {platform_summary}")

    platform_detail = get(f"{PLATFORM_BASE}/{reference}", OWNER_HEADERS)
    assert_disabled_response(platform_detail)
    if platform_detail.get("operational_knowledge_evaluation", {}).get("id") != evaluation_id:
        raise AssertionError(f"Platform detail lookup by reference failed: {platform_detail}")

    agency_base = f"/api/agencies/{agency_id}/operational-evaluations"
    for query in [
        "evaluation_status=completed",
        "airline=LH",
        "passenger=PSG-SMOKE-506",
        "service_domain=animal_transport",
        "service_family=pet_transport",
        "ssr_code=PETC",
        "capability_result=pass",
        "policy_result=warning",
        "pricing_result=manual_review",
        "constraint_result=warning",
        "operational_result=conditional",
        "operational_risk=medium",
        "confidence=high",
        "evaluation_completed=true",
    ]:
        verify_filter(f"{agency_base}?{query}", evaluation_id)

    agency_list = get(agency_base, OWNER_HEADERS)
    assert_disabled_response(agency_list)
    if agency_list.get("read_only") is not True:
        raise AssertionError(f"Agency list is not marked read-only: {agency_list}")
    agency_items = [item for item in agency_list.get("items", []) if item.get("id") == evaluation_id]
    if not agency_items or agency_items[0].get("read_only") is not True:
        raise AssertionError(f"Agency item is not read-only: {agency_list}")

    agency_summary = get(f"{agency_base}/summary", OWNER_HEADERS)
    assert_disabled_response(agency_summary)
    if agency_summary.get("read_only") is not True:
        raise AssertionError(f"Agency summary is not read-only: {agency_summary}")

    agency_detail = get(f"{agency_base}/{evaluation_id}", OWNER_HEADERS)
    assert_disabled_response(agency_detail)
    if agency_detail.get("operational_knowledge_evaluation", {}).get("read_only") is not True:
        raise AssertionError(f"Agency detail is not read-only: {agency_detail}")

    request("POST", agency_base, evaluation_payload(agency_id, run_ref("OKE-BLOCKED")), OWNER_HEADERS, 405)
    request("PUT", f"{agency_base}/{evaluation_id}", {"evaluation_status": "archived"}, OWNER_HEADERS, 405)
    request("DELETE", f"{agency_base}/{evaluation_id}", None, OWNER_HEADERS, 405)

    deleted = request("DELETE", f"{PLATFORM_BASE}/{evaluation_id}", None, OWNER_HEADERS)[1]
    assert_disabled_response(deleted)
    if deleted.get("archived") is not True or deleted.get("physical_delete_disabled") is not True:
        raise AssertionError(f"Platform delete should soft-archive metadata only: {deleted}")
    archived = deleted.get("operational_knowledge_evaluation") or {}
    if archived.get("evaluation_status") != "archived" or archived.get("archived") is not True:
        raise AssertionError(f"Soft archive did not mark archived metadata: {deleted}")


def main() -> int:
    verify_model_and_collection_registration()
    verify_metadata_only_implementation()
    verify_frontend_and_docs()

    openapi = get("/openapi.json")
    verify_routes(openapi.get("paths") or {})
    verify_readiness()
    verify_blueprint_adoption()
    verify_endpoints()

    print("Phase 50.6 operational knowledge evaluation engine foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
