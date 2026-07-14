#!/usr/bin/env python3
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import KnowledgeImportTemplate, KnowledgeImportTemplateCreate
from services.knowledge_import_template_service import (
    FOUNDATION_PHASE_LABEL,
    IMPORT_SCOPES,
    KNOWLEDGE_IMPORT_TEMPLATES_COLLECTION,
    PHASE_LABEL,
    TEMPLATE_TYPES,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_55_9_airline_intelligence_scale_release_readiness_foundation"
EXPECTED_FOUNDATION_PHASE = "phase_52_2_knowledge_import_templates_foundation"
ROOT = Path(__file__).resolve().parents[2]

REQUIRED_TEMPLATE_TYPES = {
    "airline_manual",
    "operational_bulletin",
    "policy_update",
    "capability_table",
    "pricing_table",
    "service_parameter_table",
    "reference_data_table",
    "evidence_pack",
    "exception_rule_pack",
}


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
        "knowledge_import_templates_foundation",
        "parsing_execution_disabled",
        "scraping_disabled",
        "ai_disabled",
        "background_workers_disabled",
        "provider_integrations_disabled",
        "human_authority_final",
    ]:
        if payload.get(flag) is not True:
            raise AssertionError(f"Payload missing safety flag {flag}: {payload}")


def template_payload(agency_id: str, reference: str, template_type: str = "service_parameter_table") -> dict:
    target_collection = "service_parameter_taxonomies" if template_type == "service_parameter_table" else "reference_data_domains"
    target_domain = "service_parameters" if template_type == "service_parameter_table" else "reference_data"
    return {
        "agency_id": agency_id,
        "template_reference": reference,
        "template_name": "Phase 52.2 Smoke Template",
        "template_type": template_type,
        "template_version": "1.0",
        "target_knowledge_domain": target_domain,
        "target_collections": [target_collection],
        "required_columns": [
            {"name": "airline", "type": "string", "required": True},
            {"name": "service_code", "type": "string", "required": True},
        ],
        "optional_columns": [{"name": "notes", "type": "string"}],
        "validation_rules": [{"field": "service_code", "rule": "required"}],
        "mapping_rules": [{"source_column": "service_code", "target_field": "service_codes"}],
        "sample_rows": [{"airline": "LH", "service_code": "PETC", "notes": "Manual review required"}],
        "accepted_file_types": ["csv", "xlsx"],
        "import_scope": "platform_governed",
        "review_required": True,
        "governance_links": ["KGV-SMOKE-522"],
        "metadata": {"smoke": True, "human_authority_final": True},
    }


def verify_model_and_collection_registration() -> None:
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Active service phase label mismatch: {PHASE_LABEL}")
    if FOUNDATION_PHASE_LABEL != EXPECTED_FOUNDATION_PHASE:
        raise AssertionError(f"Foundation phase label mismatch: {FOUNDATION_PHASE_LABEL}")
    if KNOWLEDGE_IMPORT_TEMPLATES_COLLECTION not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("knowledge_import_templates is not registered as agency-owned metadata.")
    missing_types = REQUIRED_TEMPLATE_TYPES - set(TEMPLATE_TYPES)
    if missing_types:
        raise AssertionError(f"Supported template types missing: {sorted(missing_types)}")
    if "platform_governed" not in IMPORT_SCOPES or "scenario_testing" not in IMPORT_SCOPES:
        raise AssertionError("Import scopes are incomplete.")

    create = KnowledgeImportTemplateCreate(**template_payload("agency-smoke", "KIT-SMOKE-MODEL"))
    record = KnowledgeImportTemplate(**create.model_dump(mode="json", exclude_none=True))
    if record.template_reference != "KIT-SMOKE-MODEL" or not record.required_columns or not record.mapping_rules:
        raise AssertionError("KnowledgeImportTemplate model did not preserve template metadata.")
    if record.knowledge_import_templates_foundation is not True or record.parsing_execution_disabled is not True:
        raise AssertionError("KnowledgeImportTemplate model did not preserve metadata-only flags.")

    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for marker in [
        KNOWLEDGE_IMPORT_TEMPLATES_COLLECTION,
        "knowledge_import_templates_reference_unique",
        "knowledge_import_templates_agency_type_lookup",
        "knowledge_import_templates_type_lookup",
        "knowledge_import_templates_target_domain_lookup",
        "knowledge_import_templates_target_collection_lookup",
        "knowledge_import_templates_import_scope_lookup",
        "knowledge_import_templates_review_required_lookup",
        "knowledge_import_templates_file_types_lookup",
        "knowledge_import_templates_required_column_lookup",
        "knowledge_import_templates_governance_lookup",
        "knowledge_import_templates_archive_lookup",
    ]:
        if marker not in database_py:
            raise AssertionError(f"Database registration missing {marker}.")


def verify_router_ui_docs_registration() -> None:
    openapi = get("/openapi.json", OWNER_HEADERS)
    paths = openapi.get("paths") or {}
    for path, method in [
        ("/api/platform/knowledge-import-templates", "get"),
        ("/api/platform/knowledge-import-templates", "post"),
        ("/api/platform/knowledge-import-templates/summary", "get"),
        ("/api/platform/knowledge-import-templates/{template_id}", "get"),
        ("/api/platform/knowledge-import-templates/{template_id}", "put"),
        ("/api/platform/knowledge-import-templates/{template_id}", "delete"),
        ("/api/agencies/{agency_id}/knowledge-import-templates", "get"),
        ("/api/agencies/{agency_id}/knowledge-import-templates", "post"),
        ("/api/agencies/{agency_id}/knowledge-import-templates/summary", "get"),
        ("/api/agencies/{agency_id}/knowledge-import-templates/{template_id}", "get"),
        ("/api/agencies/{agency_id}/knowledge-import-templates/{template_id}", "put"),
        ("/api/agencies/{agency_id}/knowledge-import-templates/{template_id}", "delete"),
    ]:
        assert_openapi_path(paths, path, method)
    for path in paths:
        if path.startswith("/api/admin") or path.startswith("/admin"):
            raise AssertionError(f"Old admin route must not be registered: {path}")

    for path, text in [
        (ROOT / "frontend/src/App.jsx", "/platform/knowledge-import-templates"),
        (ROOT / "frontend/src/App.jsx", "/agency/import-templates"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Knowledge Import Templates"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "knowledge_import_templates"),
        (ROOT / "frontend/src/pages/platform/KnowledgeImportTemplatesPage.jsx", "Template Overview"),
        (ROOT / "frontend/src/pages/agency/ImportTemplatesPage.jsx", "Validation Rules"),
        (ROOT / "backend/services/saas_subscription_service.py", "knowledge_import_templates"),
        (ROOT / "backend/services/blueprint_adoption_service.py", "Knowledge Import Templates"),
        (ROOT / "docs/architecture/knowledge-import-templates-foundation.md", "Phase 52.2"),
        (ROOT / "docs/architecture/current-model-inventory.md", "knowledge_import_templates"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/platform/knowledge-import-templates"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Knowledge Import Templates"),
        (ROOT / "docs/architecture/airline-operational-intelligence-engine-foundation.md", "knowledge_import_templates"),
        (ROOT / "docs/architecture/service-parameter-taxonomy-integration-foundation.md", "Knowledge Import Templates Alignment"),
        (ROOT / "docs/architecture/reference-data-engine-foundation.md", "Knowledge Import Template Relationship"),
        (ROOT / "docs/architecture/visual-policy-editor-foundation.md", "knowledge import template records"),
        (ROOT / "docs/architecture/foundations/AIRLINE_OPERATIONAL_KNOWLEDGE_BLUEPRINT.md", "Phase 52.2"),
        (ROOT / "docs/architecture/foundations/AEROASSIST_ENGINEERING_PRINCIPLES.md", "Phase 52.2"),
        (ROOT / "docs/architecture/foundations/GLOSSARY.md", "Knowledge Import Templates"),
        (ROOT / "BUILD_PHASES.md", "Implemented Phase 52.2"),
        (ROOT / "README.md", "knowledge import template records"),
    ]:
        require_text(path, text)


def verify_crud_and_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")

    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires at least one seeded agency.")
    agency_id = agencies[0]["id"]

    platform_reference = run_ref("KIT-SMOKE-PLATFORM")
    created = post(
        "/api/platform/knowledge-import-templates",
        template_payload(agency_id, platform_reference),
        OWNER_HEADERS,
        201,
    )
    assert_safety_flags(created)
    if created.get("foundation_phase") != EXPECTED_FOUNDATION_PHASE:
        raise AssertionError("Platform create response did not expose Phase 52.2 foundation marker.")
    platform_template = created["knowledge_import_template"]
    assert_safety_flags(platform_template)
    if platform_template.get("template_type") != "service_parameter_table" or not platform_template.get("required_columns"):
        raise AssertionError("Platform template did not preserve type and required column metadata.")

    listed = get(
        "/api/platform/knowledge-import-templates?template_type=service_parameter_table&target_collection=service_parameter_taxonomies&accepted_file_type=csv&search=PETC",
        OWNER_HEADERS,
    )
    if not any(item.get("template_reference") == platform_reference for item in listed.get("items", [])):
        raise AssertionError("Platform filtered list did not include created template.")
    summary = get("/api/platform/knowledge-import-templates/summary", OWNER_HEADERS)
    if summary.get("summary", {}).get("mapping_rule_count", 0) < 1:
        raise AssertionError("Platform summary did not count mapping rules.")

    updated = put(
        f"/api/platform/knowledge-import-templates/{platform_template['id']}",
        {
            "template_version": "1.1",
            "optional_columns": platform_template["optional_columns"] + [{"name": "evidence_url", "type": "string"}],
            "validation_rules": platform_template["validation_rules"] + [{"field": "airline", "rule": "iata_or_name"}],
        },
        OWNER_HEADERS,
    )["knowledge_import_template"]
    if updated.get("template_version") != "1.1" or len(updated.get("validation_rules") or []) < 2:
        raise AssertionError("Platform update did not persist template version and validation rules.")

    agency_reference = run_ref("KIT-SMOKE-AGENCY")
    agency_payload = template_payload(agency_id, agency_reference, template_type="reference_data_table")
    agency_payload["import_scope"] = "agency_scoped"
    agency_created = post(
        f"/api/agencies/{agency_id}/knowledge-import-templates",
        agency_payload,
        OWNER_HEADERS,
        201,
    )
    assert_safety_flags(agency_created)
    agency_template = agency_created["knowledge_import_template"]
    if agency_template.get("agency_id") != agency_id or agency_template.get("template_type") != "reference_data_table":
        raise AssertionError("Agency template did not preserve agency scope.")

    agency_list = get(
        f"/api/agencies/{agency_id}/knowledge-import-templates?template_type=reference_data_table&import_scope=agency_scoped&review_required=true",
        OWNER_HEADERS,
    )
    if not any(item.get("template_reference") == agency_reference for item in agency_list.get("items", [])):
        raise AssertionError("Agency filtered list did not include created template.")

    agency_updated = put(
        f"/api/agencies/{agency_id}/knowledge-import-templates/{agency_template['id']}",
        {"review_required": False, "governance_links": ["KGV-SMOKE-522", "REL-SMOKE-522"]},
        OWNER_HEADERS,
    )["knowledge_import_template"]
    if agency_updated.get("review_required") is not False or len(agency_updated.get("governance_links") or []) < 2:
        raise AssertionError("Agency update did not persist review and governance metadata.")

    archived = request(
        "DELETE",
        f"/api/agencies/{agency_id}/knowledge-import-templates/{agency_template['id']}",
        headers=OWNER_HEADERS,
        expect=200,
    )[1]["knowledge_import_template"]
    if archived.get("archived") is not True:
        raise AssertionError("Agency archive did not persist archived metadata.")

    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("knowledge_import_templates_foundation") or {}
    if section.get("foundation_phase") != EXPECTED_FOUNDATION_PHASE:
        raise AssertionError("Readiness did not expose Phase 52.2 foundation marker.")
    for flag in [
        "knowledge_import_templates_enabled",
        "knowledge_import_templates_collection_enabled",
        "platform_knowledge_import_templates_metadata_crud_enabled",
        "agency_import_templates_metadata_crud_enabled",
        "platform_knowledge_import_templates_ui_enabled",
        "agency_import_templates_ui_enabled",
        "metadata_only",
        "parsing_execution_disabled",
        "scraping_disabled",
        "ai_disabled",
        "background_workers_disabled",
        "provider_integrations_disabled",
        "human_authority_final",
    ]:
        if section.get(flag) is not True:
            raise AssertionError(f"Readiness missing flag: {flag}")
    if set(section.get("template_types") or []) != set(TEMPLATE_TYPES):
        raise AssertionError("Readiness did not expose supported template types.")
    if section.get("knowledge_import_template_mapping_rule_count", 0) < 1:
        raise AssertionError("Readiness did not count persisted mapping rules.")


def verify_boundaries() -> None:
    openapi = get("/openapi.json", OWNER_HEADERS)
    for path in openapi.get("paths") or {}:
        lowered = path.lower()
        if lowered.startswith("/api/admin") or lowered.startswith("/admin"):
            raise AssertionError(f"Old admin route registered: {path}")
        if "knowledge-import-templates" in lowered:
            for marker in ["parse", "scrape", "execute-import", "run-import", "provider", "ai-generate", "background-worker"]:
                if marker in lowered:
                    raise AssertionError(f"Forbidden import-template execution route registered: {path}")

    for path in [
        ROOT / "backend/services/knowledge_import_template_service.py",
        ROOT / "backend/routers/platform_knowledge_import_templates.py",
        ROOT / "backend/routers/agency_knowledge_import_templates.py",
        ROOT / "frontend/src/pages/platform/KnowledgeImportTemplatesPage.jsx",
        ROOT / "frontend/src/pages/agency/ImportTemplatesPage.jsx",
    ]:
        for marker in [
            "import requests",
            "import httpx",
            "from openai",
            "import openai",
            "BackgroundTasks",
            "asyncio.create_task(",
            "def parse_",
            "def scrape",
            "def execute_import",
            "def run_import",
            "@router.post(\"/api/platform/knowledge-import-templates/import",
            "@router.post(\"/api/agencies/{agency_id}/knowledge-import-templates/import",
        ]:
            reject_text(path, marker)


def main() -> int:
    verify_model_and_collection_registration()
    verify_router_ui_docs_registration()
    verify_crud_and_readiness()
    verify_boundaries()
    print("Knowledge import templates foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Knowledge import templates foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
