#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path
from uuid import uuid4

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parent))

from database import AGENCY_OWNED_COLLECTIONS, Database
from models import (
    AirlineCoverageAssessment,
    AirlineCoverageRemediationPlan,
    AirlineCoverageTarget,
    AirlineKnowledgeGap,
    AirlineServiceCoverageCell,
    AirlineServiceCoverageProfile,
)
from services.airline_service_coverage_gap_service import (
    CAPABILITY_PHASE,
    COVERAGE_COLLECTIONS,
    COVERAGE_DIMENSIONS,
    COVERAGE_STATUSES,
    CRITICAL_GAP_TYPES,
    GAP_TYPES,
    PHASE_LABEL,
    SERVICE_COVERAGE_CATALOG,
    AirlineServiceCoverageGapService,
)
from phase_assertions import assert_application_phase_at_least
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, request


MINIMUM_PHASE = "phase_55_4_airline_service_coverage_gap_management_foundation"
ROOT = Path(__file__).resolve().parents[2]
PLATFORM_BASE = "/api/platform/airline-service-coverage"
AGENCY_AGENT_HEADERS = {"X-Demo-User-Email": "agency.agent@aeroassist.dev"}


def require_text(path: Path, text: str) -> None:
    if text not in path.read_text(encoding="utf-8"):
        raise AssertionError(f"{path.relative_to(ROOT)} missing expected text: {text}")


def reject_text(path: Path, text: str) -> None:
    if text.lower() in path.read_text(encoding="utf-8").lower():
        raise AssertionError(f"{path.relative_to(ROOT)} contains rejected text: {text}")


def assert_no_restricted_material(value: object) -> None:
    restricted = {
        "source_reference_ids",
        "source_reference_counts",
        "gap_ids",
        "profile_id",
        "assessment_id",
        "remediation_plans",
        "internal_notes",
        "remediation_guidance",
        "evidence_assertion_ids",
    }
    if isinstance(value, dict):
        for key, child in value.items():
            if key in restricted:
                raise AssertionError(f"Agency coverage response leaked restricted field {key}")
            assert_no_restricted_material(child)
    elif isinstance(value, list):
        for item in value:
            assert_no_restricted_material(item)


def verify_models_collections_and_indexes() -> None:
    if CAPABILITY_PHASE != MINIMUM_PHASE:
        raise AssertionError(f"Unexpected Phase 55.4 capability provenance: {CAPABILITY_PHASE}")
    assert_application_phase_at_least(PHASE_LABEL, MINIMUM_PHASE, source="Phase 55.4 service")
    expected = {
        "airline_service_coverage_profiles",
        "airline_service_coverage_cells",
        "airline_knowledge_gaps",
        "airline_coverage_targets",
        "airline_coverage_assessments",
        "airline_coverage_remediation_plans",
    }
    if set(COVERAGE_COLLECTIONS) != expected or not expected.issubset(AGENCY_OWNED_COLLECTIONS):
        raise AssertionError("Phase 55.4 tenant-aware collection registration is incomplete.")
    required_statuses = {
        "complete_published_knowledge",
        "partial_knowledge",
        "stale_knowledge",
        "conflicting_knowledge",
        "no_knowledge",
        "policy_without_pricing",
        "pricing_without_policy",
        "rules_without_evidence",
        "evidence_without_normalized_knowledge",
        "knowledge_without_scenario_tests",
        "failed_qa",
        "unpublished_approved_knowledge",
    }
    if set(COVERAGE_STATUSES) != required_statuses:
        raise AssertionError("Coverage status taxonomy is incomplete.")
    if not CRITICAL_GAP_TYPES.issubset(set(GAP_TYPES)):
        raise AssertionError("Critical gap types are not part of the canonical gap taxonomy.")
    for code in ["WCHR", "WCHS", "WCHC", "MEDIF", "POC", "UMNR", "PETC", "AVIH", "SVAN", "ESAN", "EXST", "CBBG"]:
        if code not in {item for family in SERVICE_COVERAGE_CATALOG for item in family.get("service_codes") or []}:
            raise AssertionError(f"Required service coverage code missing: {code}")
    for dimension in ["route_type", "flight_type", "cabin", "fare_bundle", "aircraft_family", "country_scope", "airport_scope", "distribution_channel", "effective_date", "evidence_freshness"]:
        if dimension not in COVERAGE_DIMENSIONS:
            raise AssertionError(f"Coverage dimension missing: {dimension}")

    assessment = AirlineCoverageAssessment(assessment_reference="ACA-MODEL", airline_codes=["LH"], service_families=["petc"])
    profile = AirlineServiceCoverageProfile(coverage_profile_reference="ACP-MODEL", assessment_id=assessment.id, airline_code="LH")
    cell = AirlineServiceCoverageCell(coverage_cell_reference="ACC-MODEL", assessment_id=assessment.id, profile_id=profile.id, airline_code="LH", service_family="petc")
    gap = AirlineKnowledgeGap(gap_reference="AKG-MODEL", assessment_id=assessment.id, profile_id=profile.id, coverage_cell_id=cell.id, airline_code="LH", service_family="petc", gap_type="missing_evidence", title="Missing Evidence", description="Evidence is required.")
    target = AirlineCoverageTarget(target_reference="ACT-MODEL", target_name="Model target", airline_codes=["LH"], service_families=["petc"])
    plan = AirlineCoverageRemediationPlan(remediation_plan_reference="ACR-MODEL", assessment_id=assessment.id, profile_id=profile.id, airline_code="LH", gap_ids=[gap.id])
    if not all(item.id for item in [assessment, profile, cell, gap, target, plan]):
        raise AssertionError("Phase 55.4 models did not preserve their canonical relationships.")

    database_text = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "airline_service_coverage_profiles_assessment_airline_unique",
        "airline_service_coverage_cells_agency_public_ready_lookup",
        "airline_service_coverage_cells_travel_context_lookup",
        "airline_service_coverage_cells_geography_distribution_lookup",
        "airline_knowledge_gaps_cell_type_unique",
        "airline_coverage_targets_scope_lookup",
        "airline_coverage_assessments_target_completed_lookup",
        "airline_coverage_remediation_plans_assessment_airline_unique",
    ]:
        if index_name not in database_text:
            raise AssertionError(f"Mongo index registration missing {index_name}")


def source_records(agency_id: str, airline_code: str, visible: bool = True) -> dict[str, list[dict]]:
    suffix = airline_code.lower()
    visibility = {"visibility_status": "selected_agencies", "agency_ids": [agency_id]} if visible else {"visibility_status": "platform_only"}
    return {
        "visual_policy_editor_cards": [{"id": f"policy-{suffix}", "agency_id": agency_id, "card_reference": f"POL-{airline_code}", "airline": airline_code, "policy_family": "PETC", "service_family": "pets_animals", "service_codes": ["PETC"], "status": "approved", "effective_from": "2026-01-01", "effective_to": "2027-12-31", "required_documents": [{"type": "pet_passport"}], "approval_requirements": [{"type": "airline"}], "client_messages": [{"message": "Confirmation required"}], "evidence_links": [{"reference": f"ASSERT-{airline_code}"}]}],
        "pricing_formula_builders": [{"id": f"price-{suffix}", "agency_id": agency_id, "formula_reference": f"PRICE-{airline_code}", "airline": airline_code, "service_family": "pets_animals", "service_codes": ["PETC"], "formula_status": "approved", "route_type": "international", "flight_type": "mediumhaul", "fare_bundle": "standard", "effective_from": "2026-01-01", "evidence_links": [{"reference": f"ASSERT-{airline_code}"}]}],
        "operational_rule_composer_rules": [{"id": f"rule-{suffix}", "agency_id": agency_id, "rule_reference": f"RULE-{airline_code}", "rule_family": "pets_animals", "service_family": "pets_animals", "service_codes": ["PETC"], "applies_to": {"airlines": [airline_code]}, "lifecycle_status": "approved", "effective_from": "2026-01-01", "client_message": "Confirmation required", "internal_message": "Verify carrier and documents", "evidence_links": [{"reference": f"ASSERT-{airline_code}"}]}],
        "airline_knowledge_normalisations": [{"id": f"norm-{suffix}", "agency_id": agency_id, "normalisation_reference": f"NORM-{airline_code}", "airline_codes": [airline_code], "service_family": "pet_transport", "service_codes": ["PETC"]}],
        "airline_capability_matrix": [{"id": f"cap-{suffix}", "agency_id": agency_id, "capability_reference": f"CAP-{airline_code}", "airline_code": airline_code, "operating_carrier": airline_code, "marketing_carrier": airline_code, "service_family": "pet_transport", "service_variant": "pet_in_cabin", "ssr_code": "PETC", "capability_confidence": "official", "document_required": True, "approval_required": True, "effective_from": "2026-01-01"}],
        "airline_evidence_sources": [{"id": f"source-{suffix}", "agency_id": agency_id, "canonical_airline_id": airline_code, "source_reference": f"SOURCE-{airline_code}", "source_type": "airline_public_website", "title": f"{airline_code} PETC policy", "review_due_date": "2027-07-01", "confidence": "official_source", "evidence_status": "approved", "accessibility": "agency_visible"}],
        "airline_evidence_assertions": [{"id": f"assert-{suffix}", "agency_id": agency_id, "canonical_airline_id": airline_code, "source_id": f"source-{suffix}", "assertion_reference": f"ASSERT-{airline_code}", "assertion_type": "policy_limit", "assertion_key": "petc.total_weight_limit", "service_family": "PETC", "distribution_channel": "agency_gds", "effective_from": "2026-01-01", "confidence": "official_source", "evidence_status": "approved", "accessibility": "agency_visible"}],
        "airline_evidence_freshness_assessments": [{"id": f"fresh-{suffix}", "agency_id": agency_id, "source_id": f"source-{suffix}", "assertion_id": f"assert-{suffix}", "freshness_status": "current", "explanation": "Source is current."}],
        "knowledge_quality_assurance_reviews": [{"id": f"qa-{suffix}", "agency_id": agency_id, "review_reference": f"QA-{airline_code}", "target_type": "visual_policy_card", "target_id": f"policy-{suffix}", "airline_code": airline_code, "service_family": "pets_animals", "service_code": "PETC", "qa_status": "resolved", "severity": "low", "approval_recommendation": "ready_for_human_approval", "issues": []}],
        "airline_knowledge_publications": [{"id": f"pub-{suffix}", "agency_id": agency_id, "publication_reference": f"PUB-{airline_code}", "publication_name": f"{airline_code} PETC", "airline_codes": [airline_code], "service_families": ["pets_animals"], "publication_status": "published", "release_channel": "agency_reference", "effective_from": "2026-01-01", "effective_until": "2027-12-31", "AOIE_ready": True, "agency_visibility": visibility}],
        "operational_scenario_tests": [{"id": f"scenario-{suffix}", "agency_id": agency_id, "scenario_reference": f"SCENARIO-{airline_code}", "scenario_name": f"{airline_code} PETC", "scenario_family": "PETC", "airline_context": {"airline_code": airline_code}, "service_requirements": [{"code": "PETC"}], "test_status": "approved"}],
        "airline_distribution_summaries": [{"id": f"dist-{suffix}", "canonical_airline_id": airline_code, "distribution_reference": f"DIST-{airline_code}", "distribution_channels": ["agency_gds"]}],
    }


async def insert_records(db: Database, records: dict[str, list[dict]]) -> None:
    for collection, items in records.items():
        for item in items:
            await db.collection(collection).insert_one(item)


async def verify_deterministic_assessment_and_integrations() -> None:
    db = Database()
    agency_id = "agency-coverage-smoke"
    await insert_records(db, source_records(agency_id, "LH"))
    await insert_records(db, source_records(agency_id, "AF"))
    await db.collection("knowledge_population_toolkits").insert_one({"id": "toolkit-lh", "agency_id": agency_id, "toolkit_reference": "TOOLKIT-LH", "airline_code": "LH", "population_status": "content_population"})
    service = AirlineServiceCoverageGapService(db)
    result = await service.create_assessment(
        {
            "assessment_reference": "ACA-READY-SMOKE",
            "agency_id": agency_id,
            "airline_codes": ["LH", "AF"],
            "service_families": ["PETC"],
            "coverage_dimensions": [{"route_type": "international", "flight_type": "mediumhaul", "fare_bundle": "standard", "distribution_channel": "agency_gds"}],
        },
        {"id": "platform-owner", "email": "owner@aeroassist.dev"},
    )
    if len(result["cells"]) != 2 or not all(item.get("operational_ready") for item in result["cells"]):
        raise AssertionError(f"Complete published coverage did not become operationally ready: {result['cells']}")
    if any(item.get("coverage_status") != "complete_published_knowledge" for item in result["cells"]):
        raise AssertionError("Ready coverage cells have an incorrect coverage status.")
    if result["assessment"].get("integration_summary", {}).get("knowledge_population_toolkit_records_updated") != 1:
        raise AssertionError("Coverage assessment did not synchronize the existing population toolkit.")
    toolkit = await db.collection("knowledge_population_toolkits").find_one({"id": "toolkit-lh"})
    if (toolkit.get("coverage_summary") or {}).get("coverage_assessment_id") != result["assessment"]["id"]:
        raise AssertionError("Population toolkit did not retain the deterministic assessment linkage.")

    global_scope = await service.create_assessment(
        {"assessment_reference": "ACA-GLOBAL-ISOLATION-SMOKE", "airline_codes": ["LH"], "service_families": ["AVIH"]},
        {"id": "platform-owner"},
    )
    if any(cell.get("policy_present") or cell.get("evidence_present") for cell in global_scope["cells"]):
        raise AssertionError("A global coverage assessment mixed agency-owned knowledge into platform-global scope.")

    no_knowledge = await service.create_assessment(
        {"assessment_reference": "ACA-GAPS-SMOKE", "agency_id": agency_id, "airline_codes": ["ZZ"], "service_families": ["WCHC"]},
        {"id": "platform-owner"},
    )
    gap_cell = no_knowledge["cells"][0]
    if gap_cell.get("operational_ready") is not False or not gap_cell.get("critical_gap_types") or gap_cell.get("operational_usability_score", 100) >= 50:
        raise AssertionError("Critical knowledge gaps did not enforce the readiness guard.")
    if not no_knowledge.get("remediation_plans") or not no_knowledge["remediation_plans"][0].get("remediation_actions"):
        raise AssertionError("Critical gaps did not produce a deterministic remediation plan.")

    await db.collection("airline_evidence_sources").insert_one({"id": "source-stale", "agency_id": agency_id, "canonical_airline_id": "BA", "source_reference": "SOURCE-STALE", "source_type": "airline_public_website", "title": "Stale PETC", "review_due_date": "2020-01-01", "confidence": "medium", "evidence_status": "approved"})
    await db.collection("airline_evidence_assertions").insert_one({"id": "assert-stale", "agency_id": agency_id, "canonical_airline_id": "BA", "source_id": "source-stale", "assertion_reference": "ASSERT-STALE", "assertion_type": "policy", "assertion_key": "petc.notice", "service_family": "PETC", "confidence": "medium", "evidence_status": "approved"})
    await db.collection("airline_evidence_freshness_assessments").insert_one({"id": "fresh-stale", "agency_id": agency_id, "source_id": "source-stale", "assertion_id": "assert-stale", "freshness_status": "stale", "explanation": "Review overdue."})
    stale = await service.create_assessment({"assessment_reference": "ACA-STALE-SMOKE", "agency_id": agency_id, "airline_codes": ["BA"], "service_families": ["PETC"]}, {"id": "platform-owner"})
    if stale["cells"][0].get("coverage_status") != "stale_knowledge" or "stale_evidence" not in stale["cells"][0].get("critical_gap_types", []):
        raise AssertionError("Stale evidence did not produce stale coverage and a critical gap.")

    await db.collection("airline_evidence_conflicts").insert_one({"id": "conflict-stale", "agency_id": agency_id, "canonical_airline_id": "BA", "conflict_reference": "CONFLICT-BA", "conflict_type": "different_limits", "assertion_key": "petc.notice", "assertion_ids": ["assert-stale"], "status": "unresolved", "source_truth_preserved": True})
    conflict = await service.create_assessment({"assessment_reference": "ACA-CONFLICT-SMOKE", "agency_id": agency_id, "airline_codes": ["BA"], "service_families": ["PETC"]}, {"id": "platform-owner"})
    if conflict["cells"][0].get("coverage_status") != "conflicting_knowledge" or "unresolved_conflict" not in conflict["cells"][0].get("critical_gap_types", []):
        raise AssertionError("Unresolved evidence conflict did not block operational readiness.")

    agency_view = await service.agency_response(agency_id, airline_code="LH", service_family="petc")
    if len(agency_view.get("usable_cells") or []) != 1 or "AF" not in {item.get("airline_code") for item in agency_view.get("alternative_airline_hints") or []}:
        raise AssertionError(f"Agency published coverage or alternative-airline hints are incomplete: {agency_view}")
    assert_no_restricted_material(agency_view)
    foreign_view = await service.agency_response("foreign-agency", airline_code="LH", service_family="petc")
    if foreign_view.get("cells"):
        raise AssertionError("Agency-scoped published coverage leaked to another agency.")


def verify_routes_ui_docs_and_readiness(paths: dict) -> None:
    expected = {
        "/api/platform/airline-service-coverage": {"get"},
        "/api/platform/airline-service-coverage/summary": {"get"},
        "/api/platform/airline-service-coverage/targets": {"get", "post"},
        "/api/platform/airline-service-coverage/targets/{target_id}": {"put"},
        "/api/platform/airline-service-coverage/assessments": {"get", "post"},
        "/api/platform/airline-service-coverage/assessments/{assessment_id}": {"get"},
        "/api/platform/airline-service-coverage/gaps": {"get"},
        "/api/platform/airline-service-coverage/gaps/{gap_id}": {"put"},
        "/api/platform/airline-service-coverage/remediation-plans": {"get", "post"},
        "/api/platform/airline-service-coverage/remediation-plans/{plan_id}": {"put"},
        "/api/agencies/{agency_id}/airline-service-coverage": {"get"},
        "/api/agencies/{agency_id}/airline-service-coverage/summary": {"get"},
    }
    for path, methods in expected.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in ["/api/agencies/{agency_id}/airline-service-coverage", "/api/agencies/{agency_id}/airline-service-coverage/summary"]:
        if set(paths.get(path, {})) & {"post", "put", "patch", "delete"}:
            raise AssertionError(f"Agency service coverage route is not read-only: {path}")

    checks = [
        ("frontend/src/App.jsx", "/platform/airline-service-coverage"),
        ("frontend/src/App.jsx", "/agency/airline-service-coverage"),
        ("frontend/src/lib/moduleCatalog.js", "Airline Service Coverage"),
        ("frontend/src/pages/platform/AirlineServiceCoveragePage.jsx", "Airline × service matrix"),
        ("frontend/src/pages/platform/AirlineServiceCoveragePage.jsx", "Priority gap register"),
        ("frontend/src/pages/agency/AirlineServiceCoveragePage.jsx", "Usable published coverage"),
        ("frontend/src/pages/agency/AirlineServiceCoveragePage.jsx", "Alternative airline hints"),
        ("docs/architecture/airline-service-coverage-gap-management-foundation.md", "Critical gaps cap operational usability below readiness"),
        ("BUILD_PHASES.md", "Implemented Phase 55.4"),
        ("README.md", "Phase 55.4 Airline Service Coverage And Knowledge Gap Management"),
        ("docs/architecture/current-model-inventory.md", "airline_service_coverage_cells"),
        ("docs/architecture/canonical-route-policy.md", "/api/platform/airline-service-coverage"),
        ("docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Phase 55.4 Alignment"),
        ("docs/architecture/supplementary-blueprint-adoption-map.md", "Phase 55.4 Airline Service Coverage"),
        ("backend/services/blueprint_adoption_service.py", "Airline Service Coverage And Knowledge Gap Management"),
        ("backend/services/pilot_readiness_service.py", "coverage_cell_count"),
        ("backend/services/saas_subscription_service.py", "airline_service_coverage"),
    ]
    for relative, text in checks:
        require_text(ROOT / relative, text)

    health = get("/api/health")
    readiness = get("/api/readiness")
    assert_application_phase_at_least(health.get("phase"), MINIMUM_PHASE, source="health")
    assert_application_phase_at_least(readiness.get("phase"), MINIMUM_PHASE, source="readiness")
    section = readiness.get("airline_service_coverage_gap_management_foundation") or {}
    for key in [
        "airline_service_coverage_gap_management_enabled",
        "airline_service_matrix_enabled",
        "deterministic_completeness_scoring_enabled",
        "deterministic_operational_usability_scoring_enabled",
        "critical_gap_operational_ready_guard_enabled",
        "stale_evidence_gap_detection_enabled",
        "unresolved_conflict_gap_detection_enabled",
        "knowledge_population_toolkit_integration_enabled",
        "pilot_readiness_integration_enabled",
        "agency_published_coverage_read_only",
        "unpublished_draft_agency_visibility_disabled",
        "metadata_only",
    ]:
        if section.get(key) is not True:
            raise AssertionError(f"Readiness missing Phase 55.4 flag {key}: {section}")
    for key in ["coverage_profile_count", "coverage_cell_count", "coverage_assessment_count", "knowledge_gap_count", "critical_knowledge_gap_count", "operational_ready_coverage_cell_count", "remediation_plan_count"]:
        if key not in section:
            raise AssertionError(f"Readiness missing Phase 55.4 counter {key}")


def verify_live_routes() -> None:
    post("/api/reference/seed", {}, OWNER_HEADERS)
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Phase 55.4 smoke requires a seeded agency.")
    agency_id = agencies[0]["id"]
    token = uuid4().hex[:8].upper()
    airline_code = f"X{token[:2]}"
    target = post(
        f"{PLATFORM_BASE}/targets",
        {"target_reference": f"ACT-{token}", "target_name": "Smoke coverage target", "agency_id": agency_id, "airline_codes": [airline_code], "service_families": ["WCHC"]},
        OWNER_HEADERS,
        201,
    )["target"]
    assessment_response = post(
        f"{PLATFORM_BASE}/assessments",
        {"assessment_reference": f"ACA-{token}", "target_id": target["id"], "sync_population_toolkit": False},
        OWNER_HEADERS,
        201,
    )
    assessment = assessment_response["assessment"]
    cells = assessment_response.get("cells") or []
    if not cells or any(cell.get("operational_ready") is not False for cell in cells) or any(not cell.get("critical_gap_types") for cell in cells):
        raise AssertionError("Live critical-gap assessment did not remain non-ready.")
    detail = get(f"{PLATFORM_BASE}/assessments/{assessment['id']}", OWNER_HEADERS)
    if not detail.get("gaps") or not detail.get("remediation_plans"):
        raise AssertionError("Live assessment detail omitted gaps or remediation planning.")
    filtered = get(f"{PLATFORM_BASE}?assessment_id={assessment['id']}&critical=true", OWNER_HEADERS)
    if filtered.get("summary", {}).get("critical_gap_count", 0) < 1:
        raise AssertionError("Platform matrix filtering omitted critical knowledge gaps.")

    agency_view = get(f"/api/agencies/{agency_id}/airline-service-coverage?airline_code={airline_code}&service_family=wheelchair_assistance", OWNER_HEADERS)
    if agency_view.get("read_only") is not True or agency_view.get("cells") or not agency_view.get("warnings"):
        raise AssertionError(f"Agency unpublished coverage suppression is incorrect: {agency_view}")
    assert_no_restricted_material(agency_view)
    request("POST", f"/api/agencies/{agency_id}/airline-service-coverage", {}, OWNER_HEADERS, 405)
    request("GET", PLATFORM_BASE, None, AGENCY_AGENT_HEADERS, 403)
    if len(agencies) > 1:
        request(
            "GET",
            f"/api/agencies/{agencies[1]['id']}/airline-service-coverage?airline_code={airline_code}",
            None,
            OWNER_HEADERS,
            403,
        )


def verify_safety() -> None:
    service = AirlineServiceCoverageGapService(None)  # type: ignore[arg-type]
    for key, value in service.safety_flags().items():
        if value is not True:
            raise AssertionError(f"Coverage safety flag is disabled: {key}")
    service_path = ROOT / "backend/services/airline_service_coverage_gap_service.py"
    for forbidden in ["requests.get(", "requests.post(", "httpx.", "openai", "backgroundtasks", "asyncio.create_task", ".delete_one(", ".delete_many(", "seed_core_data", "publish_knowledge(", "execute_recommendation("]:
        reject_text(service_path, forbidden)


def main() -> int:
    verify_models_collections_and_indexes()
    verify_safety()
    asyncio.run(verify_deterministic_assessment_and_integrations())
    paths = get("/openapi.json").get("paths") or {}
    verify_routes_ui_docs_and_readiness(paths)
    verify_live_routes()
    print("Phase 55.4 airline service coverage and knowledge gap management foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
