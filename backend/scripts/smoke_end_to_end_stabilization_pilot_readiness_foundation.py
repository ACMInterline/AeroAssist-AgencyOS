#!/usr/bin/env python3
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import (
    PilotGoldenPathCase,
    PilotGoldenPathCaseCreate,
    PilotReadinessAssessment,
    PilotReadinessCheck,
    PilotReadinessIssue,
    PilotReadinessProfile,
    PilotReadinessProfileCreate,
)
from services.pilot_readiness_service import (
    CHECK_FAMILIES,
    CHECK_STATUSES,
    GOLDEN_PATH_CASE_TEMPLATES,
    GOLDEN_PATH_STAGE_CODES,
    ISSUE_STATUSES,
    PHASE_LABEL,
    PILOT_GOLDEN_PATH_CASES_COLLECTION,
    PILOT_GOLDEN_PATH_RUNS_COLLECTION,
    PILOT_READINESS_ASSESSMENTS_COLLECTION,
    PILOT_READINESS_CHECKS_COLLECTION,
    PILOT_READINESS_ISSUES_COLLECTION,
    PILOT_READINESS_PROFILES_COLLECTION,
    READINESS_STATUSES,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_55_8_airline_contact_communication_intelligence_foundation"
ROOT = Path(__file__).resolve().parents[2]


def run_ref(prefix: str) -> str:
    return f"{prefix}-{int(time.time() * 1000)}"


def require_text(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8")
    if text not in content:
        raise AssertionError(f"{path.relative_to(ROOT)} missing expected text: {text}")


def reject_text(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8").lower()
    if text.lower() in content:
        raise AssertionError(f"{path.relative_to(ROOT)} contains rejected text: {text}")


def assert_safety_flags(payload: dict) -> None:
    for flag in [
        "metadata_only",
        "end_to_end_stabilization_pilot_readiness_foundation",
        "production_seed_disabled",
        "production_record_mutation_disabled",
        "automation_disabled",
        "provider_integrations_disabled",
        "ai_disabled",
        "destructive_reset_disabled",
        "human_authority_final",
    ]:
        if payload.get(flag) is not True:
            raise AssertionError(f"Payload missing safety flag {flag}: {payload}")


def profile_payload(agency_id: str, reference: str) -> dict:
    return {
        "agency_id": agency_id,
        "profile_reference": reference,
        "profile_name": "Phase 53.0 Pilot Readiness Smoke",
        "profile_status": "reviewing",
        "pilot_scope": "Smoke test diagnostic scope",
        "target_airline_codes": ["LH"],
        "target_service_families": ["mobility_assistance", "pets_animals"],
        "target_service_codes": ["WCHC", "PETC"],
        "required_reference_domains": ["phase53_missing_domain"],
        "required_modules": ["reference_data_engine", "phase53_missing_module"],
        "minimum_score": 85,
        "owner": "platform_knowledge_editor",
        "notes": "Metadata-only pilot readiness profile.",
        "metadata": {"smoke": True, "human_authority_final": True},
    }


def golden_case_payload(agency_id: str, reference: str, scenario_type: str, family: str) -> dict:
    return {
        "agency_id": agency_id,
        "case_reference": reference,
        "case_name": f"Phase 53.0 {scenario_type} smoke",
        "case_family": family,
        "scenario_type": scenario_type,
        "case_status": "draft",
        "airline_code": "LH",
        "origin": "FRA",
        "destination": "JFK",
        "passenger_context": {"passenger_need": "service review"},
        "itinerary_context": {"route": "FRA-JFK"},
        "service_requirements": [{"service_code": "WCHC", "service_family": "mobility_assistance"}],
        "expected_outcome": {"pilot_review": scenario_type},
        "expected_required_actions": [{"action": "human_review"}],
        "evidence_links": [{"reference": "manual-smoke-evidence", "url": "internal://pilot-readiness-smoke"}],
        "notes": "Golden path smoke metadata only.",
        "metadata": {"smoke": True},
    }


def verify_models_and_collections() -> None:
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Service phase label mismatch: {PHASE_LABEL}")
    for collection in [
        PILOT_READINESS_PROFILES_COLLECTION,
        PILOT_READINESS_ASSESSMENTS_COLLECTION,
        PILOT_READINESS_CHECKS_COLLECTION,
        PILOT_GOLDEN_PATH_CASES_COLLECTION,
        PILOT_GOLDEN_PATH_RUNS_COLLECTION,
        PILOT_READINESS_ISSUES_COLLECTION,
    ]:
        if collection not in AGENCY_OWNED_COLLECTIONS:
            raise AssertionError(f"{collection} is not registered as agency-owned metadata.")
    for value in ["system_health", "reference_data", "knowledge_production", "pilot_operations"]:
        if value not in CHECK_FAMILIES:
            raise AssertionError(f"Missing check family: {value}")
    for value in ["passed", "warning", "blocked", "failed", "skipped", "unknown"]:
        if value not in CHECK_STATUSES:
            raise AssertionError(f"Missing check status: {value}")
    for value in ["pilot_ready", "blocked", "conditionally_ready"]:
        if value not in READINESS_STATUSES:
            raise AssertionError(f"Missing readiness status: {value}")
    for value in ["open", "resolved", "reopened"]:
        if value not in ISSUE_STATUSES:
            raise AssertionError(f"Missing issue status: {value}")

    profile = PilotReadinessProfile(**PilotReadinessProfileCreate(**profile_payload("agency-smoke", "PILOT-PROFILE-MODEL")).model_dump(mode="json", exclude_none=True))
    if profile.profile_reference != "PILOT-PROFILE-MODEL" or profile.metadata_only is not True:
        raise AssertionError("PilotReadinessProfile model did not preserve metadata-only fields.")
    check = PilotReadinessCheck(assessment_id="assessment-smoke", check_reference="CHECK-MODEL", check_code="model_check", check_family="system_health", label="Model check")
    assessment = PilotReadinessAssessment(assessment_reference="ASSESS-MODEL", check_ids=[check.id])
    issue = PilotReadinessIssue(issue_reference="ISSUE-MODEL", issue_family="system_health", title="Model issue")
    case = PilotGoldenPathCase(**PilotGoldenPathCaseCreate(**golden_case_payload("agency-smoke", "CASE-MODEL", "unknown_policy", "unknown_policy")).model_dump(mode="json", exclude_none=True))
    if assessment.deterministic_scoring_enabled is not True or issue.metadata_only is not True or case.sample_template_auto_seed_disabled is not True:
        raise AssertionError("Pilot readiness models did not preserve required safety metadata.")

    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for marker in [
        "pilot_readiness_profiles_reference_unique",
        "pilot_readiness_assessments_reference_unique",
        "pilot_readiness_checks_reference_unique",
        "pilot_golden_path_cases_reference_unique",
        "pilot_golden_path_runs_reference_unique",
        "pilot_readiness_issues_reference_unique",
    ]:
        if marker not in database_py:
            raise AssertionError(f"Database index registration missing {marker}.")


def verify_router_ui_docs_registration() -> None:
    openapi = get("/openapi.json", OWNER_HEADERS)
    paths = openapi.get("paths") or {}
    for path, method in [
        ("/api/platform/pilot-readiness", "get"),
        ("/api/platform/pilot-readiness/summary", "get"),
        ("/api/platform/pilot-readiness/module-readiness", "get"),
        ("/api/platform/pilot-readiness/airline-service-coverage", "get"),
        ("/api/platform/pilot-readiness/sample-cases", "get"),
        ("/api/platform/pilot-readiness/profiles", "get"),
        ("/api/platform/pilot-readiness/profiles", "post"),
        ("/api/platform/pilot-readiness/profiles/{profile_id}", "put"),
        ("/api/platform/pilot-readiness/assessments/run", "post"),
        ("/api/platform/pilot-readiness/golden-path-cases", "post"),
        ("/api/platform/pilot-readiness/golden-path-cases/{case_id}/runs", "post"),
        ("/api/platform/pilot-readiness/issues/{issue_id}/resolve", "post"),
        ("/api/platform/pilot-readiness/issues/{issue_id}/reopen", "post"),
        ("/api/agencies/{agency_id}/pilot-readiness", "get"),
        ("/api/agencies/{agency_id}/pilot-readiness/summary", "get"),
        ("/api/agencies/{agency_id}/pilot-readiness/remediation-checklist", "get"),
        ("/api/agencies/{agency_id}/pilot-readiness/assessments/run", "post"),
        ("/api/agencies/{agency_id}/pilot-readiness/golden-path-cases", "post"),
        ("/api/agencies/{agency_id}/pilot-readiness/golden-path-cases/{case_id}/runs", "post"),
    ]:
        assert_openapi_path(paths, path, method)
    for path in paths:
        lowered = path.lower()
        if lowered.startswith("/api/admin") or lowered.startswith("/api/agent"):
            raise AssertionError(f"Old API route root must not be registered: {path}")
        if "pilot-readiness" in lowered and ("/admin" in lowered or "/agent" in lowered):
            raise AssertionError(f"Pilot readiness route used old root: {path}")

    for path, text in [
        (ROOT / "frontend/src/App.jsx", "/platform/pilot-readiness"),
        (ROOT / "frontend/src/App.jsx", "/agency/pilot-readiness"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Pilot Readiness"),
        (ROOT / "backend/services/saas_subscription_service.py", "pilot_readiness"),
        (ROOT / "backend/services/blueprint_adoption_service.py", "PilotReadinessAssessment"),
        (ROOT / "docs/architecture/end-to-end-stabilization-pilot-readiness-foundation.md", "Deterministic Scoring"),
        (ROOT / "docs/architecture/current-model-inventory.md", "pilot_readiness_profiles"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/platform/pilot-readiness"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Pilot Readiness"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "pilot_readiness_assessments"),
        (ROOT / "docs/architecture/foundations/AIRLINE_OPERATIONAL_KNOWLEDGE_BLUEPRINT.md", "53.0 End-to-End Stabilization"),
        (ROOT / "docs/architecture/foundations/GLOSSARY.md", "Golden Path Run"),
        (ROOT / "BUILD_PHASES.md", "Implemented Phase 53.0"),
        (ROOT / "README.md", "pilot readiness"),
    ]:
        require_text(path, text)


def verify_health_readiness_and_core_workflow() -> tuple[str, str, str]:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")
    readiness = get("/api/readiness")
    section = readiness.get("end_to_end_stabilization_pilot_readiness_foundation") or {}
    for key in [
        "pilot_readiness_enabled",
        "deterministic_readiness_scoring_enabled",
        "critical_blockers_prevent_pilot_ready",
        "golden_path_templates_exposed_without_auto_seed",
        "client_internal_message_separation_enabled",
        "metadata_only",
        "production_seed_disabled",
        "destructive_reset_disabled",
    ]:
        if section.get(key) is not True:
            raise AssertionError(f"Readiness section missing {key}: {section}")

    post("/api/reference/seed", {}, OWNER_HEADERS)
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires at least one seeded agency.")
    agency_id = agencies[0]["id"]
    other_agency_id = agencies[1]["id"] if len(agencies) > 1 else None

    samples = get("/api/platform/pilot-readiness/sample-cases", OWNER_HEADERS)
    assert_safety_flags(samples)
    references = {item.get("case_reference") for item in samples.get("sample_cases") or []}
    for reference in ["GPT-WCHC", "GPT-PETC", "GPT-MEDIF-POC", "GPT-UNKNOWN-POLICY", "GPT-BLOCKED-POLICY", "GPT-PUBLISHED-FEASIBLE"]:
        if reference not in references:
            raise AssertionError(f"Missing golden-path sample template {reference}.")
    if samples.get("auto_seed_disabled") is not True or len(samples.get("sample_cases") or []) < 10:
        raise AssertionError("Sample cases must be exposed without auto-seeding and include at least ten templates.")

    profile_ref = run_ref("PILOT-PROFILE")
    created_profile = post("/api/platform/pilot-readiness/profiles", profile_payload(agency_id, profile_ref), OWNER_HEADERS, 201)
    assert_safety_flags(created_profile)
    profile = created_profile["pilot_readiness_profile"]
    updated_profile = put(
        f"/api/platform/pilot-readiness/profiles/{profile['id']}",
        {"profile_status": "active", "notes": "Updated metadata-only pilot profile."},
        OWNER_HEADERS,
    )["pilot_readiness_profile"]
    if updated_profile.get("profile_status") != "active":
        raise AssertionError("Pilot readiness profile update did not persist metadata.")

    run_one = post("/api/platform/pilot-readiness/assessments/run", {"profile_id": profile["id"]}, OWNER_HEADERS, 201)
    run_two = post("/api/platform/pilot-readiness/assessments/run", {"profile_id": profile["id"]}, OWNER_HEADERS, 201)
    assessment = run_one["pilot_readiness_assessment"]
    assert_safety_flags(assessment)
    if assessment.get("assessment_status") == "pilot_ready":
        raise AssertionError("Critical blockers must prevent pilot_ready.")
    if assessment.get("critical_blocker_count", 0) < 1:
        raise AssertionError("Assessment should include at least one critical blocker.")
    if assessment.get("readiness_score") != run_two["pilot_readiness_assessment"].get("readiness_score"):
        raise AssertionError("Pilot readiness scoring is not deterministic for the same profile.")
    checks = run_one.get("checks") or []
    if not checks or not any(check.get("check_family") == "reference_data" for check in checks):
        raise AssertionError("Assessment did not persist readiness/check metadata.")
    if not any(check.get("status") == "blocked" and check.get("severity") == "critical" for check in checks):
        raise AssertionError("Assessment did not create a critical blocked check.")
    issues = run_one.get("issues") or []
    if not issues:
        raise AssertionError("Assessment blockers/warnings should create issue metadata.")
    issue_id = issues[0]["id"]
    resolved = post(f"/api/platform/pilot-readiness/issues/{issue_id}/resolve", {"resolution_notes": "Smoke resolved metadata issue."}, OWNER_HEADERS)["pilot_readiness_issue"]
    if resolved.get("issue_status") != "resolved":
        raise AssertionError("Issue resolution metadata did not persist.")
    reopened = post(f"/api/platform/pilot-readiness/issues/{issue_id}/reopen", {"reopened_notes": "Smoke reopened metadata issue."}, OWNER_HEADERS)["pilot_readiness_issue"]
    if reopened.get("issue_status") != "reopened":
        raise AssertionError("Issue reopen metadata did not persist.")

    unknown_case = post(
        "/api/platform/pilot-readiness/golden-path-cases",
        golden_case_payload(agency_id, run_ref("PILOT-UNKNOWN"), "unknown_policy", "unknown_policy"),
        OWNER_HEADERS,
        201,
    )["pilot_golden_path_case"]
    unknown_run = post(f"/api/platform/pilot-readiness/golden-path-cases/{unknown_case['id']}/runs", {"notes": "Unknown policy smoke."}, OWNER_HEADERS, 201)["pilot_golden_path_run"]
    if unknown_run.get("run_status") in {"blocked", "failed"}:
        raise AssertionError("Unknown policy golden path should warn, not crash or block.")
    if len(unknown_run.get("stage_results") or []) != len(GOLDEN_PATH_STAGE_CODES):
        raise AssertionError("Golden-path run did not persist all stage results.")
    policy_stage = next((stage for stage in unknown_run["stage_results"] if stage.get("stage_code") == "policy_rule_pricing_ready"), {})
    if policy_stage.get("status") != "warning":
        raise AssertionError(f"Unknown policy should persist a warning policy stage: {policy_stage}")
    if not unknown_run.get("client_internal_message_separated") or not unknown_run.get("client_message") or not unknown_run.get("internal_trace"):
        raise AssertionError("Golden-path run did not separate client and internal diagnostic messages.")

    blocked_case = post(
        "/api/platform/pilot-readiness/golden-path-cases",
        golden_case_payload(agency_id, run_ref("PILOT-BLOCKED"), "blocked_policy", "blocked_policy"),
        OWNER_HEADERS,
        201,
    )["pilot_golden_path_case"]
    blocked_response = post(f"/api/platform/pilot-readiness/golden-path-cases/{blocked_case['id']}/runs", {"notes": "Blocked policy smoke."}, OWNER_HEADERS, 201)
    blocked_run = blocked_response["pilot_golden_path_run"]
    if blocked_run.get("run_status") != "blocked" or blocked_run.get("blocking_stage") != "policy_rule_pricing_ready":
        raise AssertionError(f"Blocked policy run did not preserve blocking stage: {blocked_run}")
    if not any(issue.get("severity") == "critical" for issue in blocked_response.get("issues") or []):
        raise AssertionError("Blocked golden-path run should create a critical issue.")

    agency_case = post(
        f"/api/agencies/{agency_id}/pilot-readiness/golden-path-cases",
        golden_case_payload(agency_id, run_ref("PILOT-AGENCY"), "conditional_policy", "conditional_policy"),
        OWNER_HEADERS,
        201,
    )["pilot_golden_path_case"]
    agency_run = post(f"/api/agencies/{agency_id}/pilot-readiness/golden-path-cases/{agency_case['id']}/runs", {}, OWNER_HEADERS, 201)["pilot_golden_path_run"]
    if agency_run.get("agency_id") != agency_id:
        raise AssertionError("Agency golden-path run did not remain scoped to its agency.")
    agency_assessment = post(
        f"/api/agencies/{agency_id}/pilot-readiness/assessments/run",
        {"airline_code": "LH", "required_modules": ["reference_data_engine"], "required_reference_domains": ["phase53_agency_missing_domain"]},
        OWNER_HEADERS,
        201,
    )["pilot_readiness_assessment"]
    if agency_assessment.get("agency_id") != agency_id:
        raise AssertionError("Agency assessment did not remain scoped to its agency.")
    checklist = get(f"/api/agencies/{agency_id}/pilot-readiness/remediation-checklist", OWNER_HEADERS)
    if "remediation_checklist" not in checklist or "module_readiness" not in checklist:
        raise AssertionError("Agency remediation checklist response shape is incomplete.")
    if other_agency_id:
        request("GET", f"/api/agencies/{other_agency_id}/pilot-readiness/golden-path-cases/{agency_case['id']}", None, OWNER_HEADERS, 404)

    dashboard = get("/api/platform/pilot-readiness", OWNER_HEADERS)
    for key in ["summary", "module_readiness", "airline_service_coverage", "sample_cases", "issues"]:
        if key not in dashboard:
            raise AssertionError(f"Platform dashboard response missing {key}.")
    agency_dashboard = get(f"/api/agencies/{agency_id}/pilot-readiness", OWNER_HEADERS)
    if agency_dashboard.get("agency_id") != agency_id or "module_readiness" not in agency_dashboard:
        raise AssertionError("Agency dashboard response shape is incomplete.")

    return profile["id"], unknown_case["id"], blocked_run["id"]


def verify_metadata_only_boundaries() -> None:
    for path in [
        ROOT / "backend/services/pilot_readiness_service.py",
        ROOT / "backend/routers/platform_pilot_readiness.py",
        ROOT / "backend/routers/agency_pilot_readiness.py",
    ]:
        content = path.read_text(encoding="utf-8").lower()
        for forbidden in [
            "import requests",
            "import httpx",
            "from openai",
            "openai.",
            "openai(",
            "backgroundtasks",
            "asyncio.create_task",
            "stripe",
            "send_email(",
            "send_sms(",
            "scrape(",
            "scraper_client",
            "provider_client",
            "gds_connect(",
            "ndc_connect(",
            "@router.delete",
            "seed-defaults",
            "reset-production",
        ]:
            if forbidden in content:
                raise AssertionError(f"{path.relative_to(ROOT)} contains forbidden implementation marker: {forbidden}")
    for path in [
        ROOT / "backend/services/pilot_readiness_service.py",
        ROOT / "backend/routers/platform_pilot_readiness.py",
        ROOT / "backend/routers/agency_pilot_readiness.py",
        ROOT / "frontend/src/pages/platform/PilotReadinessPage.jsx",
        ROOT / "frontend/src/pages/agency/PilotReadinessPage.jsx",
    ]:
        require_text(path, "metadata")
    reject_text(ROOT / "frontend/src/pages/platform/PilotReadinessPage.jsx", ">Activate<")
    reject_text(ROOT / "frontend/src/pages/agency/PilotReadinessPage.jsx", ">Activate<")


def main() -> None:
    verify_models_and_collections()
    verify_router_ui_docs_registration()
    verify_health_readiness_and_core_workflow()
    verify_metadata_only_boundaries()
    print("Phase 53.0 end-to-end stabilization pilot readiness foundation smoke passed.")


if __name__ == "__main__":
    main()
