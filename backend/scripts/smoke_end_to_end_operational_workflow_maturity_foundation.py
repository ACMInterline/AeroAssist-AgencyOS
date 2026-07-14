#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parent))

from database import AGENCY_OWNED_COLLECTIONS
from services.operational_workflow_maturity_service import (
    GOLDEN_PATH_STAGES,
    MATURITY_DIMENSIONS,
    PHASE_LABEL,
    TEST_CASE_TEMPLATES,
    OperationalWorkflowMaturityService,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, request


EXPECTED_PHASE = "phase_55_5_airline_distribution_pss_gds_ndc_capability_intelligence_foundation"
ROOT = Path(__file__).resolve().parents[2]
AGENCY_AGENT_HEADERS = {"X-Demo-User-Email": "agency.agent@aeroassist.dev"}


def require_text(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8")
    if text not in content:
        raise AssertionError(f"{path.relative_to(ROOT)} missing expected text: {text}")


def reject_text(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8").lower()
    if text.lower() in content:
        raise AssertionError(f"{path.relative_to(ROOT)} contains rejected text: {text}")


def assert_safety(payload: dict) -> None:
    expected_true = [
        "metadata_only",
        "end_to_end_operational_workflow_maturity_foundation",
        "consolidation_only",
        "parallel_subsystem_disabled",
        "production_record_creation_disabled",
        "automatic_production_seeding_disabled",
        "destructive_reset_disabled",
        "provider_execution_disabled",
        "external_api_calls_disabled",
        "ai_disabled",
        "background_workers_disabled",
        "automatic_booking_disabled",
        "automatic_ticketing_disabled",
        "automatic_emd_issuance_disabled",
        "automatic_financial_commitment_disabled",
        "test_runs_isolated",
        "client_internal_message_separation_enabled",
        "agency_isolation_enforced",
        "human_authority_final",
    ]
    for flag in expected_true:
        if payload.get(flag) is not True:
            raise AssertionError(f"Missing workflow maturity safety flag {flag}: {payload}")
    if payload.get("test_runs_persisted") is not False:
        raise AssertionError(f"Workflow maturity test runs must not persist: {payload}")


def verify_static_contracts() -> None:
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Workflow maturity phase mismatch: {PHASE_LABEL}")
    if len(MATURITY_DIMENSIONS) != 12:
        raise AssertionError(f"Expected 12 maturity dimensions: {MATURITY_DIMENSIONS}")
    if len(GOLDEN_PATH_STAGES) != 14:
        raise AssertionError(f"Unexpected golden-path stage count: {GOLDEN_PATH_STAGES}")
    expected_templates = {
        "standard_request_offer_booking",
        "wchc_multi_segment_request",
        "petc_conditional_approval_documents",
        "medif_poc_case",
        "umnr_connection_restricted",
        "accepted_offer_missing_approval",
        "booking_ready_after_blocker_resolution",
        "ticketed_trip_after_sales_change",
        "disruption_urgent_operations",
        "unknown_knowledge_manual_review",
    }
    if {item["template_code"] for item in TEST_CASE_TEMPLATES} != expected_templates:
        raise AssertionError("Workflow maturity test templates are incomplete.")
    if any("maturity" in collection for collection in AGENCY_OWNED_COLLECTIONS):
        raise AssertionError("Phase 54.9 must not add a parallel maturity collection.")
    assert_safety(OperationalWorkflowMaturityService(None).safety_flags())

    service_path = ROOT / "backend/services/operational_workflow_maturity_service.py"
    for required in [
        "operational_workflow_instances",
        "operational_work_items",
        "operational_deadlines",
        "operational_task_dependencies",
        "request_trip_conversion_runs",
        "offer_booking_handoffs",
        "after_sales_cases",
        "pilot_golden_path_runs",
        "OperationsCommandCenterService",
        "PilotReadinessService",
        "missing_canonical_contract",
        '"critical"',
    ]:
        require_text(service_path, required)
    for forbidden in [
        ".insert_one(",
        ".update_one(",
        ".delete_one(",
        ".delete_many(",
        "requests.get(",
        "requests.post(",
        "httpx.",
        "openai",
        "stripe",
        "send_email",
        "send_sms",
        "backgroundtasks",
        "asyncio.create_task",
    ]:
        reject_text(service_path, forbidden)


def verify_routes_ui_and_docs(paths: dict) -> None:
    expected_routes = {
        "/api/platform/workflow-maturity": {"get"},
        "/api/platform/workflow-maturity/assessment": {"get"},
        "/api/platform/workflow-maturity/test-templates": {"get"},
        "/api/platform/workflow-maturity/test-runs": {"post"},
        "/api/agencies/{agency_id}/workflow-maturity": {"get"},
        "/api/agencies/{agency_id}/workflow-maturity/assessment": {"get"},
        "/api/agencies/{agency_id}/workflow-maturity/test-templates": {"get"},
        "/api/agencies/{agency_id}/workflow-maturity/test-runs": {"post"},
    }
    for path, methods in expected_routes.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")

    checks = [
        (ROOT / "frontend/src/App.jsx", "/platform/workflow-maturity"),
        (ROOT / "frontend/src/App.jsx", "/agency/workflow-maturity"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Workflow Maturity"),
        (ROOT / "backend/services/saas_subscription_service.py", "workflow_maturity"),
        (ROOT / "frontend/src/pages/platform/WorkflowMaturityPage.jsx", "Workflow Maturity"),
        (ROOT / "frontend/src/pages/agency/WorkflowMaturityPage.jsx", "No production seeding"),
        (ROOT / "frontend/src/components/WorkflowMaturityDashboard.jsx", "Run diagnostic"),
        (ROOT / "docs/architecture/end-to-end-operational-workflow-maturity-foundation.md", "End-to-End Operational Workflow Maturity Foundation"),
        (ROOT / "BUILD_PHASES.md", "Phase 54.9: End-to-end operational workflow maturity foundation"),
        (ROOT / "README.md", "Phase 54.9 completes Epic 54"),
        (ROOT / "docs/architecture/current-model-inventory.md", "End-to-End Operational Workflow Maturity aggregate read model"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "Phase 54.9 adds workflow maturity APIs"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "End-to-end operational workflow maturity"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "End-to-End Operational Workflow Maturity"),
        (ROOT / "docs/architecture/foundations/GLOSSARY.md", "Operational Workflow Maturity"),
        (ROOT / "docs/architecture/foundations/AEROASSIST_ENGINEERING_PRINCIPLES.md", "Operational Maturity Diagnostics"),
        (ROOT / "backend/services/blueprint_adoption_service.py", "End-to-End Operational Workflow Maturity"),
    ]
    for path, text in checks:
        require_text(path, text)


def verify_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health}")
    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("end_to_end_operational_workflow_maturity_foundation") or {}
    for flag in [
        "end_to_end_operational_workflow_maturity_enabled",
        "platform_workflow_maturity_enabled",
        "agency_workflow_maturity_enabled",
        "epic_54_consolidation_enabled",
        "phase_53_readiness_patterns_reused",
        "new_parallel_subsystem_disabled",
        "new_maturity_collection_disabled",
        "workflow_linkage_assessment_enabled",
        "assignment_readiness_assessment_enabled",
        "sla_readiness_assessment_enabled",
        "task_dependency_readiness_assessment_enabled",
        "request_to_trip_conversion_readiness_assessment_enabled",
        "offer_to_booking_readiness_assessment_enabled",
        "servicing_readiness_assessment_enabled",
        "command_center_visibility_assessment_enabled",
        "audit_completeness_assessment_enabled",
        "client_internal_message_separation_assessment_enabled",
        "agency_isolation_assessment_enabled",
        "production_safety_assessment_enabled",
        "deterministic_scoring_enabled",
        "critical_blocker_behavior_enabled",
        "golden_path_stage_results_enabled",
        "blocked_and_resumed_flow_enabled",
        "isolated_test_templates_enabled",
        "isolated_test_runs_enabled",
        "automatic_production_seeding_disabled",
        "destructive_reset_disabled",
        "provider_execution_disabled",
        "external_api_calls_disabled",
        "ai_disabled",
        "background_workers_disabled",
        "human_authority_final",
        "metadata_only",
    ]:
        if section.get(flag) is not True:
            raise AssertionError(f"Readiness missing Phase 54.9 flag {flag}: {section}")
    if section.get("test_runs_persisted") is not False or section.get("test_records_become_production_records") is not False:
        raise AssertionError(f"Readiness does not preserve isolated tests: {section}")
    for key in ["maturity_score", "maturity_status", "module_scores", "failing_stage_count", "blocker_count", "operational_coverage"]:
        if key not in section:
            raise AssertionError(f"Readiness missing Phase 54.9 metric {key}: {section}")


def assert_dashboard(payload: dict, agency_id: str | None = None) -> None:
    assert_safety(payload)
    if agency_id and payload.get("agency_id") != agency_id:
        raise AssertionError(f"Agency maturity response escaped scope: {payload.get('agency_id')} != {agency_id}")
    for key in ["maturity_score", "maturity_status", "module_scores", "failing_stages", "golden_path_stages", "test_templates", "golden_path_runs", "blocker_register", "remediation_links", "recent_workflow_errors", "operational_coverage", "command_center_summary"]:
        if key not in payload:
            raise AssertionError(f"Workflow maturity dashboard missing {key}.")
    if len(payload["module_scores"]) != len(MATURITY_DIMENSIONS):
        raise AssertionError("Workflow maturity module scoring is incomplete.")
    if payload["golden_path_stages"] != GOLDEN_PATH_STAGES:
        raise AssertionError("Workflow maturity golden path is not canonical.")
    score = payload["maturity_score"]
    if not isinstance(score, int) or not 0 <= score <= 100:
        raise AssertionError(f"Maturity score is not deterministic integer range: {score}")


def verify_isolated_runs(agency_id: str) -> None:
    before = get(f"/api/agencies/{agency_id}/workflow-maturity", AGENCY_AGENT_HEADERS)
    assert_dashboard(before, agency_id)
    before_counts = (before.get("operational_coverage") or {}).get("record_counts") or {}

    run_results: dict[str, dict] = {}
    for template in TEST_CASE_TEMPLATES:
        result = post(
            f"/api/agencies/{agency_id}/workflow-maturity/test-runs",
            {"template_code": template["template_code"]},
            AGENCY_AGENT_HEADERS,
        )
        assert_safety(result)
        run = result.get("test_run") or {}
        run_results[template["template_code"]] = run
        if run.get("persisted") is not False or run.get("production_record_created") is not False:
            raise AssertionError(f"Diagnostic run escaped isolation: {run}")
        if len(run.get("stage_results") or []) != len(GOLDEN_PATH_STAGES):
            raise AssertionError(f"Diagnostic run stage coverage is incomplete: {run}")
        if run.get("client_internal_message_separated") is not True or not run.get("client_message") or not run.get("internal_trace"):
            raise AssertionError(f"Client/internal message separation is missing: {run}")

    standard = run_results["standard_request_offer_booking"]
    if standard.get("final_status") != "passed" or any(stage.get("status") != "passed" for stage in standard["stage_results"]):
        raise AssertionError(f"Standard golden path did not pass: {standard}")
    if [stage["stage_code"] for stage in standard["stage_results"]] != GOLDEN_PATH_STAGES:
        raise AssertionError("Standard run did not preserve canonical stage ordering.")

    blocked = run_results["accepted_offer_missing_approval"]
    if blocked.get("final_status") != "blocked" or not any(stage.get("stage_code") == "booking_handoff" and stage.get("status") == "blocked" for stage in blocked["stage_results"]):
        raise AssertionError(f"Missing approval did not block booking handoff: {blocked}")

    resumed = run_results["booking_ready_after_blocker_resolution"]
    resumed_stage = next(stage for stage in resumed["stage_results"] if stage["stage_code"] == "booking_handoff")
    if not resumed.get("initial_blocked") or not resumed.get("resumed_after_explicit_resolution") or resumed.get("final_status") != "passed":
        raise AssertionError(f"Blocked/resumed flow is incomplete: {resumed}")
    if len(resumed_stage.get("transition_history") or []) != 2:
        raise AssertionError(f"Blocked/resumed transition audit is incomplete: {resumed_stage}")

    disruption = run_results["disruption_urgent_operations"]
    if disruption.get("work_queue_signal") != "verified" or disruption.get("sla_signal") != "verified" or disruption.get("task_dependency_signal") != "verified" or disruption.get("command_center_visibility") is not True:
        raise AssertionError(f"Disruption integration signals are incomplete: {disruption}")
    if run_results["ticketed_trip_after_sales_change"].get("final_status") != "passed":
        raise AssertionError("After-sales diagnostic did not pass.")
    if run_results["unknown_knowledge_manual_review"].get("final_status") != "manual_review":
        raise AssertionError("Unknown knowledge did not preserve manual review.")

    after = get(f"/api/agencies/{agency_id}/workflow-maturity", AGENCY_AGENT_HEADERS)
    after_counts = (after.get("operational_coverage") or {}).get("record_counts") or {}
    if before_counts != after_counts:
        raise AssertionError(f"Isolated test runs changed production metadata counts: before={before_counts} after={after_counts}")


def verify_live_api(paths: dict) -> None:
    verify_routes_ui_and_docs(paths)
    verify_readiness()
    post("/api/reference/seed", {}, OWNER_HEADERS)
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("No agencies available for workflow maturity smoke.")
    agency_id = agencies[0]["id"]

    platform = get(f"/api/platform/workflow-maturity?agency_id={agency_id}", OWNER_HEADERS)
    assert_dashboard(platform, agency_id)
    if platform.get("platform_governance") is not True:
        raise AssertionError("Platform workflow maturity governance flag is missing.")
    platform_assessment = get(f"/api/platform/workflow-maturity/assessment?agency_id={agency_id}", OWNER_HEADERS)
    assert_safety(platform_assessment)
    templates = get("/api/platform/workflow-maturity/test-templates", OWNER_HEADERS)
    if len(templates.get("items") or []) != 10:
        raise AssertionError(f"Platform workflow maturity templates are incomplete: {templates}")

    verify_isolated_runs(agency_id)
    request("POST", f"/api/agencies/{agency_id}/workflow-maturity/test-runs", {"template_code": "unknown-template"}, AGENCY_AGENT_HEADERS, 400)
    request("GET", "/api/agencies/not-an-agency/workflow-maturity", None, AGENCY_AGENT_HEADERS, 404)
    if len(agencies) > 1:
        other_id = agencies[1]["id"]
        other = get(f"/api/platform/workflow-maturity?agency_id={other_id}", OWNER_HEADERS)
        assert_dashboard(other, other_id)
        if other.get("agency_id") == agency_id:
            raise AssertionError("Platform agency filter returned another agency's scope.")


def main() -> None:
    verify_static_contracts()
    paths = get("/openapi.json").get("paths", {})
    verify_live_api(paths)
    print("Phase 54.9 end-to-end operational workflow maturity foundation smoke passed.")


if __name__ == "__main__":
    main()
