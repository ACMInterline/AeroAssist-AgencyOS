#!/usr/bin/env python3
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import KnowledgePopulationToolkit, KnowledgePopulationToolkitCreate
from services.knowledge_population_toolkit_service import (
    KNOWLEDGE_POPULATION_TOOLKITS_COLLECTION,
    PHASE_LABEL,
    POPULATION_STATUSES,
    TOOLKIT_READINESS_STATUSES,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_55_2_airline_policy_evidence_source_governance_foundation"
ROOT = Path(__file__).resolve().parents[2]


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


def assert_safety_flags(payload: dict) -> None:
    for flag in [
        "metadata_only",
        "knowledge_population_toolkit_foundation",
        "scraping_disabled",
        "auto_import_disabled",
        "ai_disabled",
        "provider_integrations_disabled",
        "background_workers_disabled",
        "population_execution_disabled",
        "human_authority_final",
    ]:
        if payload.get(flag) is not True:
            raise AssertionError(f"Payload missing safety flag {flag}: {payload}")


def toolkit_payload(agency_id: str, reference: str, status: str = "content_population") -> dict:
    return {
        "agency_id": agency_id,
        "toolkit_reference": reference,
        "airline_code": "LH",
        "population_status": status,
        "airline_onboarding_checklist": [
            {"item_key": "airline_profile", "label": "Airline profile metadata", "status": "ready"},
            {"item_key": "service_families", "label": "Core service families identified", "status": "in_progress"},
        ],
        "reference_readiness": {"status": "ready", "domains": ["airlines", "airports", "service_codes"]},
        "import_template_readiness": {"status": "ready", "template_ids": ["KIT-SMOKE-529"]},
        "policy_editor_readiness": {"status": "in_progress", "policy_cards": 4},
        "pricing_builder_readiness": {"status": "needs_review", "pricing_formulas": 2},
        "rule_composer_readiness": {"status": "in_progress", "rules": 3},
        "qa_readiness": {"status": "needs_review", "reviews": 1},
        "publishing_readiness": {"status": "not_started", "publication_ids": []},
        "scenario_test_readiness": {"status": "in_progress", "scenario_ids": ["OST-SMOKE-529"]},
        "coverage_summary": {"overall_percent": 58, "ready_domains": 3, "remaining_domains": 2},
        "service_family_coverage": [
            {"service_family": "pets_animals", "coverage_percent": 75},
            {"service_family": "passenger_assistance", "coverage_percent": 40},
        ],
        "evidence_coverage": {"evidence_items": 8, "missing_evidence": 2},
        "pricing_coverage": {"priced_service_families": ["pets_animals"], "missing_pricing": ["wheelchair_assistance"]},
        "capability_coverage": {"capability_records": 5, "missing_capability_domains": ["medical_clearance"]},
        "QA_status": "needs_review",
        "publishing_status": "not_started",
        "scenario_test_status": "in_progress",
        "population_progress": {"completed_steps": 6, "total_steps": 12},
        "missing_domains": ["medical_clearance", "restricted_equipment"],
        "blockers": [{"blocker_key": "missing_medif_policy", "label": "MEDIF policy still missing"}],
        "warnings": [{"warning_key": "pricing_partial", "label": "Pricing coverage is partial"}],
        "next_actions": [{"action_key": "add_wchc_policy", "label": "Add WCHC policy card"}],
        "owner": "platform_knowledge_editor",
        "due_dates": [{"item_key": "qa_review", "due_date": "2026-08-15"}],
        "notes": "Metadata-only knowledge population readiness tracker.",
        "metadata": {"smoke": True, "human_authority_final": True},
    }


def verify_model_and_collection_registration() -> None:
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Service phase label mismatch: {PHASE_LABEL}")
    if KNOWLEDGE_POPULATION_TOOLKITS_COLLECTION not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("knowledge_population_toolkits is not registered as agency-owned metadata.")
    for value in ["draft", "content_population", "qa_review", "ready", "blocked", "archived"]:
        if value not in POPULATION_STATUSES:
            raise AssertionError(f"Missing population status: {value}")
    for value in ["not_started", "in_progress", "ready", "needs_review", "blocked"]:
        if value not in TOOLKIT_READINESS_STATUSES:
            raise AssertionError(f"Missing toolkit readiness status: {value}")

    create = KnowledgePopulationToolkitCreate(**toolkit_payload("agency-smoke", "KPT-SMOKE-MODEL"))
    record = KnowledgePopulationToolkit(**create.model_dump(mode="json", exclude_none=True))
    if record.toolkit_reference != "KPT-SMOKE-MODEL" or not record.service_family_coverage:
        raise AssertionError("KnowledgePopulationToolkit model did not preserve coverage metadata.")
    if record.knowledge_population_toolkit_foundation is not True or record.auto_import_disabled is not True:
        raise AssertionError("KnowledgePopulationToolkit model did not preserve metadata-only flags.")

    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for marker in [
        KNOWLEDGE_POPULATION_TOOLKITS_COLLECTION,
        "knowledge_population_toolkits_reference_unique",
        "knowledge_population_toolkits_agency_status_lookup",
        "knowledge_population_toolkits_airline_lookup",
        "knowledge_population_toolkits_population_status_lookup",
        "knowledge_population_toolkits_qa_status_lookup",
        "knowledge_population_toolkits_publishing_status_lookup",
        "knowledge_population_toolkits_scenario_test_status_lookup",
        "knowledge_population_toolkits_owner_lookup",
        "knowledge_population_toolkits_missing_domain_lookup",
        "knowledge_population_toolkits_service_family_lookup",
        "knowledge_population_toolkits_archive_lookup",
    ]:
        if marker not in database_py:
            raise AssertionError(f"Database registration missing {marker}.")


def verify_router_ui_docs_registration() -> None:
    openapi = get("/openapi.json", OWNER_HEADERS)
    paths = openapi.get("paths") or {}
    for path, method in [
        ("/api/platform/knowledge-population-toolkit", "get"),
        ("/api/platform/knowledge-population-toolkit", "post"),
        ("/api/platform/knowledge-population-toolkit/summary", "get"),
        ("/api/platform/knowledge-population-toolkit/{toolkit_id}", "get"),
        ("/api/platform/knowledge-population-toolkit/{toolkit_id}", "put"),
        ("/api/platform/knowledge-population-toolkit/{toolkit_id}", "delete"),
        ("/api/agencies/{agency_id}/knowledge-population-toolkit", "get"),
        ("/api/agencies/{agency_id}/knowledge-population-toolkit/summary", "get"),
        ("/api/agencies/{agency_id}/knowledge-population-toolkit/{toolkit_id}", "get"),
    ]:
        assert_openapi_path(paths, path, method)
    for path, method in [
        ("/api/agencies/{agency_id}/knowledge-population-toolkit", "post"),
        ("/api/agencies/{agency_id}/knowledge-population-toolkit/{toolkit_id}", "put"),
        ("/api/agencies/{agency_id}/knowledge-population-toolkit/{toolkit_id}", "delete"),
    ]:
        if method in paths.get(path, {}):
            raise AssertionError(f"Agency Knowledge Population Toolkit must remain read-only: {method.upper()} {path}")
    for path in paths:
        lowered = path.lower()
        if lowered.startswith("/api/admin") or lowered.startswith("/admin"):
            raise AssertionError(f"Old admin route must not be registered: {path}")
        if "knowledge-population-toolkit" in lowered:
            for marker in ["/scrape", "/auto-import", "/run-import", "/execute", "/provider", "/ai"]:
                if marker in lowered:
                    raise AssertionError(f"Forbidden population execution route registered: {path}")

    for path, text in [
        (ROOT / "frontend/src/App.jsx", "/platform/knowledge-population-toolkit"),
        (ROOT / "frontend/src/App.jsx", "/agency/knowledge-population-toolkit"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Knowledge Population Toolkit"),
        (ROOT / "frontend/src/pages/platform/KnowledgePopulationToolkitPage.jsx", "Population Toolkit Records"),
        (ROOT / "frontend/src/pages/agency/KnowledgePopulationToolkitPage.jsx", "Read-only airline knowledge population readiness"),
        (ROOT / "backend/services/saas_subscription_service.py", "knowledge_population_toolkit"),
        (ROOT / "backend/services/blueprint_adoption_service.py", "Knowledge Population Toolkit"),
        (ROOT / "docs/architecture/knowledge-population-toolkit-foundation.md", "Phase 52.9"),
        (ROOT / "docs/architecture/current-model-inventory.md", "knowledge_population_toolkits"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/api/platform/knowledge-population-toolkit"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Knowledge Population Toolkit"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Knowledge population toolkit"),
        (ROOT / "docs/architecture/foundations/AIRLINE_OPERATIONAL_KNOWLEDGE_BLUEPRINT.md", "Phase 52.9"),
        (ROOT / "docs/architecture/foundations/AEROASSIST_ENGINEERING_PRINCIPLES.md", "Phase 52.9"),
        (ROOT / "docs/architecture/foundations/GLOSSARY.md", "Knowledge Population Toolkit"),
        (ROOT / "BUILD_PHASES.md", "Implemented Phase 52.9"),
        (ROOT / "README.md", "knowledge population toolkit records"),
    ]:
        require_text(path, text)


def verify_crud_read_only_and_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")

    post("/api/reference/seed", {}, OWNER_HEADERS)
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires at least one seeded agency.")
    agency_id = agencies[0]["id"]

    reference = run_ref("KPT-SMOKE")
    created = post(
        "/api/platform/knowledge-population-toolkit",
        toolkit_payload(agency_id, reference),
        OWNER_HEADERS,
        201,
    )
    assert_safety_flags(created)
    toolkit = created["knowledge_population_toolkit"]
    assert_safety_flags(toolkit)
    if toolkit.get("airline_code") != "LH" or toolkit.get("population_status") != "content_population":
        raise AssertionError("Toolkit creation did not normalize airline or population status metadata.")
    for field in [
        "airline_onboarding_checklist",
        "reference_readiness",
        "import_template_readiness",
        "policy_editor_readiness",
        "pricing_builder_readiness",
        "rule_composer_readiness",
        "qa_readiness",
        "publishing_readiness",
        "scenario_test_readiness",
        "coverage_summary",
        "service_family_coverage",
        "evidence_coverage",
        "pricing_coverage",
        "capability_coverage",
        "population_progress",
        "missing_domains",
        "blockers",
        "warnings",
        "next_actions",
        "due_dates",
    ]:
        if not toolkit.get(field):
            raise AssertionError(f"Toolkit missing persisted field {field}.")
    for section in [
        "toolkit_section",
        "readiness_section",
        "coverage_section",
        "quality_release_section",
        "actions_section",
        "review_section",
        "boundary_section",
    ]:
        if section not in toolkit:
            raise AssertionError(f"Projected toolkit missing section {section}.")

    filtered = get(
        "/api/platform/knowledge-population-toolkit?airline_code=LH&population_status=content_population&QA_status=needs_review&publishing_status=not_started&scenario_test_status=in_progress&owner=platform_knowledge_editor&search=medical_clearance",
        OWNER_HEADERS,
    )
    if not any(item.get("toolkit_reference") == reference for item in filtered.get("items", [])):
        raise AssertionError("Platform Knowledge Population Toolkit filters did not return created metadata.")

    summary = get("/api/platform/knowledge-population-toolkit/summary", OWNER_HEADERS).get("summary") or {}
    if summary.get("knowledge_population_toolkit_count", 0) < 1:
        raise AssertionError("Platform Knowledge Population Toolkit summary did not count records.")
    if summary.get("service_family_coverage_count", 0) < 1 or summary.get("next_action_count", 0) < 1:
        raise AssertionError("Platform Knowledge Population Toolkit summary did not count coverage/action metadata.")

    detail = get(f"/api/platform/knowledge-population-toolkit/{toolkit['id']}", OWNER_HEADERS)["knowledge_population_toolkit"]
    if detail.get("toolkit_reference") != reference:
        raise AssertionError("Platform Knowledge Population Toolkit detail did not return created metadata.")

    updated = put(
        f"/api/platform/knowledge-population-toolkit/{toolkit['id']}",
        {"population_status": "qa_review", "QA_status": "ready", "notes": "Human reviewer confirmed toolkit metadata shape."},
        OWNER_HEADERS,
    )["knowledge_population_toolkit"]
    if updated.get("population_status") != "qa_review" or updated.get("QA_status") != "ready":
        raise AssertionError("Platform Knowledge Population Toolkit update did not persist review metadata.")

    agency_list = get(
        f"/api/agencies/{agency_id}/knowledge-population-toolkit?airline_code=LH&population_status=qa_review&QA_status=ready&publishing_status=not_started&scenario_test_status=in_progress&owner=platform_knowledge_editor",
        OWNER_HEADERS,
    )
    if agency_list.get("read_only") is not True:
        raise AssertionError("Agency Knowledge Population Toolkit response must be read-only.")
    if not any(item.get("toolkit_reference") == reference for item in agency_list.get("items", [])):
        raise AssertionError("Agency Knowledge Population Toolkit filters did not return agency-scoped metadata.")

    agency_detail = get(
        f"/api/agencies/{agency_id}/knowledge-population-toolkit/{toolkit['id']}",
        OWNER_HEADERS,
    )
    if agency_detail.get("read_only") is not True:
        raise AssertionError("Agency Knowledge Population Toolkit detail must be read-only.")
    if agency_detail.get("knowledge_population_toolkit", {}).get("agency_id") != agency_id:
        raise AssertionError("Agency Knowledge Population Toolkit detail leaked or lost agency scope.")

    agency_summary = get(f"/api/agencies/{agency_id}/knowledge-population-toolkit/summary", OWNER_HEADERS)
    if agency_summary.get("read_only") is not True:
        raise AssertionError("Agency Knowledge Population Toolkit summary must be read-only.")

    request("POST", f"/api/agencies/{agency_id}/knowledge-population-toolkit", toolkit_payload(agency_id, "KPT-AGENCY-FORBIDDEN"), OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/knowledge-population-toolkit/{toolkit['id']}", {"population_status": "ready"}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/knowledge-population-toolkit/{toolkit['id']}", None, OWNER_HEADERS, 405)

    readiness = get("/api/readiness", OWNER_HEADERS)
    section = readiness.get("knowledge_population_toolkit_foundation") or {}
    for flag in [
        "knowledge_population_toolkit_enabled",
        "knowledge_population_toolkits_collection_enabled",
        "platform_knowledge_population_toolkit_metadata_crud_enabled",
        "agency_knowledge_population_toolkit_read_only_enabled",
        "scraping_disabled",
        "auto_import_disabled",
        "ai_disabled",
        "provider_integrations_disabled",
        "background_workers_disabled",
        "population_execution_disabled",
        "human_authority_final",
    ]:
        if section.get(flag) is not True:
            raise AssertionError(f"Readiness missing flag: {flag}")
    if section.get("knowledge_population_service_family_coverage_count", 0) < 1:
        raise AssertionError("Readiness did not count toolkit service family coverage.")
    if section.get("knowledge_population_next_action_count", 0) < 1:
        raise AssertionError("Readiness did not count toolkit next actions.")
    if section.get("knowledge_population_supported_status_count", 0) < len(POPULATION_STATUSES):
        raise AssertionError("Readiness did not expose supported population statuses.")

    archived = request(
        "DELETE",
        f"/api/platform/knowledge-population-toolkit/{toolkit['id']}",
        None,
        OWNER_HEADERS,
        200,
    )[1]
    if archived.get("archived") is not True:
        raise AssertionError("Platform Knowledge Population Toolkit archive did not return archived metadata.")


def verify_boundaries() -> None:
    openapi = get("/openapi.json", OWNER_HEADERS)
    for path in openapi.get("paths") or {}:
        lowered = path.lower()
        if lowered.startswith("/api/admin") or lowered.startswith("/admin"):
            raise AssertionError(f"Old admin route registered: {path}")
        if "knowledge-population-toolkit" in lowered:
            for marker in ["/scrape", "/auto-import", "/run-import", "/execute", "/provider", "/ai"]:
                if marker in lowered:
                    raise AssertionError(f"Forbidden Knowledge Population Toolkit execution route registered: {path}")

    for path in [
        ROOT / "backend/services/knowledge_population_toolkit_service.py",
        ROOT / "backend/routers/platform_knowledge_population_toolkit.py",
        ROOT / "backend/routers/agency_knowledge_population_toolkit.py",
        ROOT / "frontend/src/pages/platform/KnowledgePopulationToolkitPage.jsx",
        ROOT / "frontend/src/pages/agency/KnowledgePopulationToolkitPage.jsx",
    ]:
        for marker in [
            "import requests",
            "import httpx",
            "from openai",
            "import openai",
            "BackgroundTasks",
            "asyncio.create_task(",
            "provider_client =",
            "@router.post(\"/api/platform/knowledge-population-toolkit/scrape",
            "@router.post(\"/api/platform/knowledge-population-toolkit/import",
            "@router.post(\"/api/platform/knowledge-population-toolkit/execute",
            "@router.post(\"/api/agencies/{agency_id}/knowledge-population-toolkit",
            "@router.put(\"/api/agencies/{agency_id}/knowledge-population-toolkit",
            "@router.delete(\"/api/agencies/{agency_id}/knowledge-population-toolkit",
            "@router.get(\"/admin",
            "@router.post(\"/admin",
            "\"/api/admin",
        ]:
            reject_text(path, marker)


def main() -> int:
    verify_model_and_collection_registration()
    verify_router_ui_docs_registration()
    verify_crud_read_only_and_readiness()
    verify_boundaries()
    print("Knowledge population toolkit foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Knowledge population toolkit foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
