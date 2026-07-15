#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parent))

from database import AGENCY_OWNED_COLLECTIONS, Database
from models import (
    AirlineIntelligencePopulationWave,
    AirlineIntelligenceReadinessAssessment,
    AirlineIntelligenceReadinessCheck,
    AirlineIntelligenceReadinessProfile,
    AirlineIntelligenceReleaseCandidate,
    AirlineIntelligenceReleaseDecision,
    AirlineIntelligenceReleaseGate,
    AirlineIntelligenceScaleIssue,
)
from services.airline_intelligence_scale_readiness_service import (
    CAPABILITY_PHASE,
    ASSESSMENT_STATUSES,
    ASSESSMENT_TEMPLATES,
    DIMENSION_CONFIG,
    PHASE_LABEL,
    RELEASE_GATE_CONFIG,
    SCALE_READINESS_COLLECTIONS,
    AirlineIntelligenceScaleReadinessError,
    AirlineIntelligenceScaleReadinessService,
)
from phase_assertions import assert_application_phase_at_least
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, request


MINIMUM_PHASE = "phase_55_9_airline_intelligence_scale_release_readiness_foundation"
ROOT = Path(__file__).resolve().parents[2]
PLATFORM_BASE = "/api/platform/airline-intelligence-readiness"
AGENCY_AGENT_HEADERS = {"X-Demo-User-Email": "agency.agent@aeroassist.dev"}


def require_text(path: Path, value: str) -> None:
    if value not in path.read_text(encoding="utf-8"):
        raise AssertionError(f"{path.relative_to(ROOT)} missing expected text: {value}")


def reject_text(path: Path, value: str) -> None:
    if value.lower() in path.read_text(encoding="utf-8").lower():
        raise AssertionError(f"{path.relative_to(ROOT)} contains prohibited execution text: {value}")


def all_passed_overrides() -> dict:
    return {
        item["code"]: {
            "status": "passed",
            "score": 100,
            "observed": f"Isolated {item['code']} signal passed.",
            "source_reference_ids": [f"source-{item['code']}"],
        }
        for item in DIMENSION_CONFIG
    }


def assert_agency_safe(value: object) -> None:
    restricted = {
        "internal_summary",
        "internal_release_notes",
        "source_snapshot",
        "source_reference_ids",
        "gate_ids",
        "decision_ids",
        "issue_ids",
        "metadata",
        "reviewer",
        "review_reason",
        "decision_by",
        "gate_snapshot",
        "blocker_snapshot",
        "assigned_agency_ids",
    }
    if isinstance(value, dict):
        for key, child in value.items():
            if key in restricted:
                raise AssertionError(f"Agency readiness response leaked restricted field {key}")
            assert_agency_safe(child)
    elif isinstance(value, list):
        for child in value:
            assert_agency_safe(child)


def verify_models_collections_indexes_and_taxonomies() -> None:
    if CAPABILITY_PHASE != MINIMUM_PHASE:
        raise AssertionError(f"Unexpected Phase 55.9 capability provenance: {CAPABILITY_PHASE}")
    assert_application_phase_at_least(PHASE_LABEL, MINIMUM_PHASE, source="Phase 55.9 service")
    expected_collections = {
        "airline_intelligence_readiness_profiles",
        "airline_intelligence_readiness_assessments",
        "airline_intelligence_readiness_checks",
        "airline_intelligence_release_candidates",
        "airline_intelligence_release_gates",
        "airline_intelligence_release_decisions",
        "airline_intelligence_population_waves",
        "airline_intelligence_scale_issues",
    }
    if set(SCALE_READINESS_COLLECTIONS) != expected_collections:
        raise AssertionError("Phase 55.9 collection constants are incomplete.")
    if not expected_collections.issubset(set(AGENCY_OWNED_COLLECTIONS)):
        raise AssertionError("Phase 55.9 agency-aware collection registration is incomplete.")
    if len(DIMENSION_CONFIG) != 18 or len(RELEASE_GATE_CONFIG) != 11 or len(ASSESSMENT_TEMPLATES) != 10:
        raise AssertionError("Phase 55.9 dimension, gate, or assessment-template taxonomy is incomplete.")
    if not {"blocked", "conditionally_ready", "release_ready", "released", "suspended"}.issubset(set(ASSESSMENT_STATUSES)):
        raise AssertionError("Phase 55.9 assessment statuses are incomplete.")

    profile = AirlineIntelligenceReadinessProfile(profile_reference="AIRP-MODEL", profile_name="Model profile")
    assessment = AirlineIntelligenceReadinessAssessment(assessment_reference="AIRA-MODEL", airline_code="LH")
    check = AirlineIntelligenceReadinessCheck(check_reference="AIRC-MODEL", assessment_id=assessment.id, airline_code="LH", dimension_code="master_profile", label="Master")
    candidate = AirlineIntelligenceReleaseCandidate(candidate_reference="AIRCAND-MODEL", candidate_name="Candidate", airline_code="LH", readiness_assessment_id=assessment.id)
    gate = AirlineIntelligenceReleaseGate(gate_reference="AIRG-MODEL", candidate_id=candidate.id, airline_code="LH", gate_code="qa_passed", label="QA passed")
    decision = AirlineIntelligenceReleaseDecision(decision_reference="AIRD-MODEL", candidate_id=candidate.id, airline_code="LH", decision_status="rejected", decision_reason="Model check", decision_by="owner", prior_candidate_status="needs_review", resulting_candidate_status="blocked")
    wave = AirlineIntelligencePopulationWave(wave_reference="AIRW-MODEL", wave_name="Wave")
    issue = AirlineIntelligenceScaleIssue(issue_reference="AISI-MODEL", title="Issue", description="Model issue")
    if not all(item.id and item.metadata_only for item in [profile, assessment, check, candidate, gate, decision, wave, issue]):
        raise AssertionError("Phase 55.9 model defaults are incomplete.")
    if not profile.automatic_production_seeding_disabled or not candidate.automatic_publication_disabled or not decision.publication_mutation_disabled:
        raise AssertionError("Phase 55.9 safety defaults are incomplete.")

    database_text = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "airline_intelligence_readiness_profiles_reference_unique",
        "airline_intelligence_readiness_assessments_score_lookup",
        "airline_intelligence_readiness_checks_assessment_dimension_lookup",
        "airline_intelligence_release_candidates_assignment_lookup",
        "airline_intelligence_release_gates_critical_lookup",
        "airline_intelligence_release_decisions_candidate_timeline_lookup",
        "airline_intelligence_population_waves_reviewer_due_lookup",
        "airline_intelligence_scale_issues_relationship_lookup",
    ]:
        if index_name not in database_text:
            raise AssertionError(f"Mongo index registration missing {index_name}")


async def verify_service_behavior() -> None:
    db = Database()
    service = AirlineIntelligenceScaleReadinessService(db)
    user = {"id": "platform-owner", "email": "owner@aeroassist.dev"}
    agency_id = "agency-ready"
    other_agency_id = "agency-other"

    await db.collection("airline_profiles").insert_one({"id": "airline-jp", "airline_code": "JP", "airline_name": "Join Proof"})
    await db.collection("airline_master_profiles").insert_one({"id": "master-jp", "canonical_airline_id": "airline-jp", "review_status": "approved"})
    await db.collection("airline_identity_aliases").insert_one({"id": "alias-jp", "canonical_airline_id": "airline-jp", "normalized_alias": "JOIN PROOF"})
    await db.collection("airline_evidence_assertions").insert_one({"id": "assertion-jp", "airline_code": "JP", "source_id": "source-jp"})
    await db.collection("airline_evidence_conflicts").insert_one({"id": "conflict-jp", "assertion_ids": ["assertion-jp"], "status": "unresolved"})
    await db.collection("airline_evidence_freshness_assessments").insert_one({"id": "freshness-jp", "assertion_id": "assertion-jp", "freshness_status": "current"})
    await db.collection("airline_knowledge_versions").insert_one({"id": "version-jp", "airline_codes": ["JP"], "version_status": "approved"})
    await db.collection("airline_intelligence_agency_consumption_profiles").insert_one({"id": "assignment-jp", "agency_id": agency_id, "knowledge_version_id": "version-jp", "status": "visible", "visible_to_agency": True})
    await db.collection("airline_intelligence_agency_usage_readiness").insert_one({"id": "consumption-jp", "agency_id": agency_id, "profile_id": "assignment-jp", "status": "ready"})
    linked = await service._source_records("JP", agency_id)
    if not linked["master_profiles"] or not linked["aliases"] or not linked["conflicts"] or not linked["freshness"] or not linked["assignments"] or not linked["consumption"]:
        raise AssertionError("Canonical-id, assertion-id, or knowledge-version source joins are incomplete.")

    profile = (await service.create_profile({
        "profile_name": "PETC WCHC UMNR release profile",
        "profile_status": "needs_review",
        "airline_codes": ["LH"],
        "required_service_families": ["PETC", "WCHC", "UMNR"],
        "minimum_readiness_score": 85,
    }, user))["profile"]
    ready = await service.run_assessment({
        "profile_id": profile["id"],
        "airline_code": "LH",
        "required_service_families": ["PETC", "WCHC", "UMNR"],
        "template_code": "fully_ready_petc_wchc_umnr",
        "signal_overrides": all_passed_overrides(),
    }, user)
    if ready["assessment"].get("assessment_status") != "release_ready" or ready["assessment"].get("readiness_score") != 100:
        raise AssertionError("Deterministic fully-ready assessment did not score 100/release_ready.")
    if len(ready.get("checks") or []) != 18 or ready.get("issues"):
        raise AssertionError("Fully-ready assessment did not produce exactly 18 passed checks.")

    publication = await db.collection("airline_knowledge_publications").insert_one({
        "id": "publication-ready",
        "publication_reference": "PUB-READY",
        "publication_name": "Published LH knowledge",
        "airline_codes": ["LH"],
        "publication_status": "published",
        "AOIE_ready": True,
    })
    candidate_response = await service.create_release_candidate({
        "readiness_assessment_id": ready["assessment"]["id"],
        "candidate_name": "LH controlled release",
        "publication_id": publication["id"],
        "knowledge_version_id": "version-ready",
        "version_snapshot_id": "snapshot-ready",
        "release_reference": "release-2026-07",
        "service_family_scope": ["PETC", "WCHC", "UMNR"],
        "assigned_agency_ids": [agency_id],
        "usable_modules": ["offer_builder", "operational_advisor"],
        "effective_from": "2026-07-15",
        "rollback_reference": "rollback-ready",
        "client_facing_summary": "Published PETC, WCHC, and UMNR coverage is available for review.",
        "internal_release_notes": "Confirm evidence and applicability before operational advice.",
    }, user)
    candidate = candidate_response["candidate"]
    gates = candidate_response["gates"]
    if candidate.get("candidate_status") != "release_ready" or len(gates) != 11 or any(item.get("gate_status") != "passed" for item in gates):
        raise AssertionError("Fully-ready release candidate did not pass all deterministic gates.")

    released = await service.decide_release(candidate["id"], {"decision_status": "released", "decision_reason": "All critical gates reviewed and passed."}, user)
    if released["candidate"].get("candidate_status") != "released" or released.get("publication_mutated") is not False:
        raise AssertionError("Human release decision did not preserve metadata-only behavior.")
    unchanged_publication = await db.collection("airline_knowledge_publications").find_one({"id": publication["id"]})
    if unchanged_publication != publication:
        raise AssertionError("Release decision mutated the canonical publication record.")
    decisions = await db.collection("airline_intelligence_release_decisions").find_many({"candidate_id": candidate["id"]})
    if len(decisions) != 1 or len(decisions[0].get("gate_snapshot") or []) != 11 or decisions[0].get("rollback_reference") != "rollback-ready":
        raise AssertionError("Release decision audit did not preserve gates and rollback reference.")

    agency = await service.agency_dashboard(agency_id)
    if len(agency.get("released_coverage") or []) != 1 or agency["released_coverage"][0].get("assigned_release_version") != "release-2026-07":
        raise AssertionError("Assigned release was not visible in the agency-safe readiness view.")
    if (await service.agency_dashboard(other_agency_id)).get("released_coverage"):
        raise AssertionError("Released airline intelligence leaked across agencies.")
    assert_agency_safe(agency)

    blocked_overrides = all_passed_overrides()
    blocked_overrides["evidence_coverage"] = {"status": "blocked", "score": 90, "observed": "Evidence minimum is missing."}
    blocked = await service.run_assessment({"airline_code": "XX", "signal_overrides": blocked_overrides, "template_code": "missing_evidence"}, user)
    if blocked["assessment"].get("assessment_status") != "blocked" or blocked["assessment"].get("readiness_score", 0) < 90:
        raise AssertionError("Critical blocker did not override a high aggregate readiness score.")
    blocked_candidate = await service.create_release_candidate({
        "readiness_assessment_id": blocked["assessment"]["id"],
        "version_snapshot_id": "snapshot-blocked",
        "assigned_agency_ids": [agency_id],
        "usable_modules": ["offer_builder"],
        "effective_from": "2026-07-15",
        "rollback_reference": "rollback-blocked",
        "client_facing_summary": "Client summary.",
        "internal_release_notes": "Internal review instruction.",
    }, user)
    if blocked_candidate["candidate"].get("candidate_status") != "blocked" or not any(item.get("gate_code") == "evidence_minimum_met" and item.get("gate_status") == "blocked" for item in blocked_candidate["gates"]):
        raise AssertionError("Critical evidence gate did not block release candidate creation.")
    try:
        await service.decide_release(blocked_candidate["candidate"]["id"], {"decision_status": "released", "decision_reason": "Unsafe attempt."}, user)
    except AirlineIntelligenceScaleReadinessError:
        pass
    else:
        raise AssertionError("Release decision bypassed an unresolved critical gate.")

    conditional_overrides = all_passed_overrides()
    conditional_overrides["fare_brand_baggage"] = {"status": "warning", "score": 60, "observed": "Fare-brand metadata is incomplete."}
    conditional = await service.run_assessment({"airline_code": "BA", "signal_overrides": conditional_overrides, "template_code": "incomplete_fare_brand"}, user)
    if conditional["assessment"].get("assessment_status") != "conditionally_ready":
        raise AssertionError("Noncritical incomplete fare-brand metadata did not produce conditional readiness.")

    wave = (await service.create_population_wave({
        "wave_name": "Multi-airline wave",
        "wave_status": "planning",
        "airline_codes": ["LH", "BA", "XX"],
        "service_family_targets": ["PETC", "WCHC", "UMNR"],
        "responsible_reviewer": "platform-owner",
        "due_date": "2026-08-31",
        "release_candidate_ids": [candidate["id"], blocked_candidate["candidate"]["id"]],
    }, user))["population_wave"]
    completed = await service.update_population_wave(wave["id"], {"wave_status": "complete", "completion_percentage": 100, "readiness_score": 83}, user)
    if completed.get("release_candidates_automatically_published") is not False:
        raise AssertionError("Population-wave completion implied automatic publication.")
    still_blocked = await db.collection("airline_intelligence_release_candidates").find_one({"id": blocked_candidate["candidate"]["id"]})
    if still_blocked.get("candidate_status") != "blocked":
        raise AssertionError("Population-wave completion changed a blocked candidate.")

    coverage = await service.coverage()
    if coverage.get("readiness_assessment_count") != 3 or coverage.get("release_candidate_count") != 2 or coverage.get("population_wave_count") != 1:
        raise AssertionError(f"Phase 55.9 coverage counters are incorrect: {coverage}")


def verify_routes_ui_docs_and_readiness(paths: dict) -> None:
    expected = {
        "/api/platform/airline-intelligence-readiness": {"get"},
        "/api/platform/airline-intelligence-readiness/summary": {"get"},
        "/api/platform/airline-intelligence-readiness/filters": {"get"},
        "/api/platform/airline-intelligence-readiness/assessment-templates": {"get"},
        "/api/platform/airline-intelligence-readiness/profiles": {"post"},
        "/api/platform/airline-intelligence-readiness/profiles/{profile_id}": {"put"},
        "/api/platform/airline-intelligence-readiness/assessments": {"get"},
        "/api/platform/airline-intelligence-readiness/assessments/run": {"post"},
        "/api/platform/airline-intelligence-readiness/release-candidates": {"get", "post"},
        "/api/platform/airline-intelligence-readiness/release-candidates/{candidate_id}": {"get"},
        "/api/platform/airline-intelligence-readiness/release-candidates/{candidate_id}/evaluate-gates": {"post"},
        "/api/platform/airline-intelligence-readiness/release-candidates/{candidate_id}/decisions": {"post"},
        "/api/platform/airline-intelligence-readiness/population-waves": {"get", "post"},
        "/api/platform/airline-intelligence-readiness/population-waves/{wave_id}": {"put"},
        "/api/platform/airline-intelligence-readiness/issues": {"get"},
        "/api/platform/airline-intelligence-readiness/issues/{issue_id}": {"put"},
        "/api/agencies/{agency_id}/airline-intelligence-readiness": {"get"},
        "/api/agencies/{agency_id}/airline-intelligence-readiness/summary": {"get"},
        "/api/agencies/{agency_id}/airline-intelligence-readiness/released": {"get"},
        "/api/agencies/{agency_id}/airline-intelligence-readiness/released/{candidate_id}": {"get"},
    }
    for path, methods in expected.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in [
        "/api/agencies/{agency_id}/airline-intelligence-readiness",
        "/api/agencies/{agency_id}/airline-intelligence-readiness/released",
        "/api/agencies/{agency_id}/airline-intelligence-readiness/released/{candidate_id}",
    ]:
        if set(paths.get(path, {})) & {"post", "put", "patch", "delete"}:
            raise AssertionError("Agency airline intelligence readiness routes expose mutation.")

    checks = [
        ("frontend/src/App.jsx", "/platform/airline-intelligence-readiness"),
        ("frontend/src/App.jsx", "/agency/airline-intelligence-readiness"),
        ("frontend/src/lib/moduleCatalog.js", "Airline Intelligence Readiness"),
        ("frontend/src/pages/platform/AirlineIntelligenceReadinessPage.jsx", "Airline readiness matrix"),
        ("frontend/src/pages/agency/AirlineIntelligenceReadinessPage.jsx", "Assigned released coverage"),
        ("docs/architecture/airline-intelligence-scale-release-readiness-foundation.md", "11 deterministic gates"),
        ("BUILD_PHASES.md", "Implemented Phase 55.9"),
        ("README.md", "Phase 55.9 Airline Intelligence Scale and Release Readiness"),
        ("docs/architecture/current-model-inventory.md", "AirlineIntelligenceReleaseCandidate"),
        ("docs/architecture/canonical-route-policy.md", "/api/platform/airline-intelligence-readiness"),
        ("docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Phase 55.9 Alignment"),
        ("docs/architecture/supplementary-blueprint-adoption-map.md", "Phase 55.9 Airline Intelligence Scale and Release Readiness"),
        ("docs/architecture/foundations/AIRLINE_OPERATIONAL_KNOWLEDGE_BLUEPRINT.md", "Epic 55 Scale and Release Readiness"),
        ("docs/architecture/foundations/GLOSSARY.md", "Release Gate"),
        ("docs/architecture/foundations/AEROASSIST_ENGINEERING_PRINCIPLES.md", "Critical gates must override aggregate scores"),
    ]
    for relative, value in checks:
        require_text(ROOT / relative, value)

    health = get("/api/health")
    readiness = get("/api/readiness")
    assert_application_phase_at_least(health.get("phase"), MINIMUM_PHASE, source="health")
    assert_application_phase_at_least(readiness.get("phase"), MINIMUM_PHASE, source="readiness")
    section = readiness.get("airline_intelligence_scale_release_readiness_foundation") or {}
    for key in [
        "airline_intelligence_scale_release_readiness_enabled",
        "epic_55_canonical_sources_reused",
        "eighteen_readiness_dimensions_enabled",
        "eleven_deterministic_release_gates_enabled",
        "critical_blocker_guard_enabled",
        "decision_audit_enabled",
        "population_wave_tracking_enabled",
        "agency_release_assignment_enabled",
        "rollback_reference_gate_enabled",
        "client_internal_message_separation_enabled",
        "agency_released_read_only_projection_enabled",
        "draft_governance_agency_visibility_disabled",
        "automatic_publication_disabled",
        "automatic_production_seeding_disabled",
        "metadata_only",
    ]:
        if section.get(key) is not True:
            raise AssertionError(f"Readiness missing Phase 55.9 flag {key}: {section}")
    for key in ["readiness_profile_count", "readiness_assessment_count", "readiness_check_count", "release_candidate_count", "release_gate_count", "release_decision_count", "population_wave_count", "scale_issue_count"]:
        if key not in section:
            raise AssertionError(f"Readiness missing Phase 55.9 counter {key}")


def verify_live_routes() -> None:
    post("/api/reference/seed", {}, OWNER_HEADERS)
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Phase 55.9 smoke requires a seeded agency.")
    agency_id = agencies[0]["id"]
    dashboard = get(PLATFORM_BASE, OWNER_HEADERS)
    assert_application_phase_at_least(dashboard.get("phase"), MINIMUM_PHASE, source="platform readiness endpoint")
    if len(dashboard.get("assessment_templates") or []) != 10:
        raise AssertionError("Platform airline intelligence readiness endpoint is incomplete.")
    assessment = post(f"{PLATFORM_BASE}/assessments/run", {
        "airline_code": "ZZ",
        "signal_overrides": all_passed_overrides(),
    }, OWNER_HEADERS, 201)["assessment"]
    candidate = post(f"{PLATFORM_BASE}/release-candidates", {
        "readiness_assessment_id": assessment["id"],
        "version_snapshot_id": "live-snapshot",
        "release_reference": "live-release",
        "assigned_agency_ids": [agency_id],
        "usable_modules": ["operational_advisor"],
        "effective_from": "2026-07-15",
        "rollback_reference": "live-rollback",
        "client_facing_summary": "Released coverage is available for agency review.",
        "internal_release_notes": "Internal applicability confirmation remains required.",
    }, OWNER_HEADERS, 201)["candidate"]
    post(f"{PLATFORM_BASE}/release-candidates/{candidate['id']}/decisions", {"decision_status": "released", "decision_reason": "Smoke release gate audit."}, OWNER_HEADERS, 201)
    agency = get(f"/api/agencies/{agency_id}/airline-intelligence-readiness", OWNER_HEADERS)
    if not any(item.get("id") == candidate["id"] for item in agency.get("released_coverage") or []):
        raise AssertionError("Agency route omitted its assigned released candidate.")
    assert_agency_safe(agency)
    request("GET", PLATFORM_BASE, None, AGENCY_AGENT_HEADERS, 403)
    request("POST", f"/api/agencies/{agency_id}/airline-intelligence-readiness", {}, OWNER_HEADERS, 405)
    if len(agencies) > 1:
        foreign = get(f"/api/agencies/{agencies[1]['id']}/airline-intelligence-readiness", OWNER_HEADERS)
        if any(item.get("id") == candidate["id"] for item in foreign.get("released_coverage") or []):
            raise AssertionError("Live agency readiness route leaked a release assignment.")


def verify_safety() -> None:
    flags = AirlineIntelligenceScaleReadinessService(None).safety_flags()  # type: ignore[arg-type]
    if any(value is not True for value in flags.values()):
        raise AssertionError(f"Scale-readiness safety flag is disabled: {flags}")
    service_path = ROOT / "backend/services/airline_intelligence_scale_readiness_service.py"
    for forbidden in [
        "requests.get(",
        "requests.post(",
        "httpx.",
        "openai",
        "backgroundtasks",
        "asyncio.create_task",
        ".delete_one(",
        ".delete_many(",
        "publish_release(",
        "seed_production(",
        "provider.execute(",
    ]:
        reject_text(service_path, forbidden)


def main() -> int:
    verify_models_collections_indexes_and_taxonomies()
    verify_safety()
    asyncio.run(verify_service_behavior())
    paths = get("/openapi.json").get("paths") or {}
    verify_routes_ui_docs_and_readiness(paths)
    verify_live_routes()
    print("Phase 55.9 airline intelligence scale and release readiness foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
