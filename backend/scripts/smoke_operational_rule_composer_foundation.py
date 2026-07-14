#!/usr/bin/env python3
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import OperationalRuleComposerRule, OperationalRuleComposerRuleCreate
from services.operational_rule_composer_service import (
    LIFECYCLE_STATUSES,
    OPERATIONAL_RULE_COMPOSER_RULES_COLLECTION,
    PHASE_LABEL,
    RULE_FAMILIES,
    SEVERITY_LEVELS,
    SUPPORTED_OPERATORS,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_54_6_offer_to_booking_handoff_readiness_foundation"
ROOT = Path(__file__).resolve().parents[2]

REQUIRED_OPERATORS = {
    "=",
    "!=",
    ">",
    ">=",
    "<",
    "<=",
    "in",
    "not_in",
    "contains",
    "exists",
    "not_exists",
    "between",
    "between_month_day",
    "date_before",
    "date_after",
    "route_includes_country",
    "route_crosses_border",
    "outside_range",
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
        "operational_rule_composer_foundation",
        "rule_execution_disabled",
        "live_rule_evaluation_disabled",
        "provider_integrations_disabled",
        "ai_disabled",
        "background_workers_disabled",
        "automatic_decisioning_disabled",
        "human_authority_final",
    ]:
        if payload.get(flag) is not True:
            raise AssertionError(f"Payload missing safety flag {flag}: {payload}")


def rule_payload(agency_id: str, reference: str, rule_family: str = "pets_animals") -> dict:
    is_pet = rule_family == "pets_animals"
    return {
        "agency_id": agency_id,
        "rule_reference": reference,
        "rule_name": "Phase 52.5 Smoke Rule",
        "rule_family": rule_family,
        "service_family": "pets_animals" if is_pet else "passenger_assistance",
        "service_codes": ["PETC"] if is_pet else ["WCHR"],
        "applies_to": {
            "airlines": ["LH"],
            "route_types": ["international"],
            "cabins": ["economy"],
        },
        "conditions": [
            {"field": "pet_weight_kg" if is_pet else "mobility_level", "operator": "<=", "value": 8 if is_pet else 2},
            {"field": "route_countries", "operator": "route_includes_country", "value": "DE"},
        ],
        "any_conditions": [
            {"field": "season_window", "operator": "between_month_day", "value": ["06-01", "09-15"]},
            {"field": "aircraft_family", "operator": "in", "value": ["A320", "A321"]},
        ],
        "result": {
            "outcome": "conditional",
            "required_actions": ["manual_airline_confirmation"],
            "blocks_offer": False,
        },
        "severity": "conditional",
        "client_message": "Airline confirmation is required before travel.",
        "internal_message": "Check pet and summer restrictions before offer.",
        "evidence_links": [{"reference": "EVIDENCE-SMOKE-525", "source": "manual_review"}],
        "governance_links": ["KGV-SMOKE-525"],
        "parameter_taxonomy_links": ["SPT-SMOKE-525"],
        "effective_from": "2026-01-01",
        "effective_to": "2026-12-31",
        "lifecycle_status": "approved",
        "metadata": {"smoke": True, "human_authority_final": True},
    }


def verify_model_and_collection_registration() -> None:
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Service phase label mismatch: {PHASE_LABEL}")
    if OPERATIONAL_RULE_COMPOSER_RULES_COLLECTION not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("operational_rule_composer_rules is not registered as agency-owned metadata.")
    if REQUIRED_OPERATORS - set(SUPPORTED_OPERATORS):
        raise AssertionError(f"Supported operators missing: {sorted(REQUIRED_OPERATORS - set(SUPPORTED_OPERATORS))}")
    if "pets_animals" not in RULE_FAMILIES or "passenger_assistance" not in RULE_FAMILIES:
        raise AssertionError("Rule family metadata is incomplete.")
    if "conditional" not in SEVERITY_LEVELS or "blocking" not in SEVERITY_LEVELS:
        raise AssertionError("Severity metadata is incomplete.")
    if "approved" not in LIFECYCLE_STATUSES or "archived" not in LIFECYCLE_STATUSES:
        raise AssertionError("Lifecycle metadata is incomplete.")

    create = OperationalRuleComposerRuleCreate(**rule_payload("agency-smoke", "ORC-SMOKE-MODEL"))
    record = OperationalRuleComposerRule(**create.model_dump(mode="json", exclude_none=True))
    if record.rule_reference != "ORC-SMOKE-MODEL" or not record.conditions or not record.any_conditions:
        raise AssertionError("OperationalRuleComposerRule model did not preserve condition metadata.")
    if record.operational_rule_composer_foundation is not True or record.rule_execution_disabled is not True:
        raise AssertionError("OperationalRuleComposerRule model did not preserve metadata-only flags.")

    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for marker in [
        OPERATIONAL_RULE_COMPOSER_RULES_COLLECTION,
        "operational_rule_composer_rules_reference_unique",
        "operational_rule_composer_rules_agency_family_lookup",
        "operational_rule_composer_rules_family_lookup",
        "operational_rule_composer_rules_service_family_lookup",
        "operational_rule_composer_rules_service_codes_lookup",
        "operational_rule_composer_rules_lifecycle_lookup",
        "operational_rule_composer_rules_severity_lookup",
        "operational_rule_composer_rules_effective_dates_lookup",
        "operational_rule_composer_rules_condition_operator_lookup",
        "operational_rule_composer_rules_any_condition_operator_lookup",
        "operational_rule_composer_rules_evidence_lookup",
        "operational_rule_composer_rules_governance_lookup",
        "operational_rule_composer_rules_parameter_taxonomy_lookup",
        "operational_rule_composer_rules_archive_lookup",
    ]:
        if marker not in database_py:
            raise AssertionError(f"Database registration missing {marker}.")


def verify_router_ui_docs_registration() -> None:
    openapi = get("/openapi.json", OWNER_HEADERS)
    paths = openapi.get("paths") or {}
    for path, method in [
        ("/api/platform/operational-rule-composer", "get"),
        ("/api/platform/operational-rule-composer", "post"),
        ("/api/platform/operational-rule-composer/summary", "get"),
        ("/api/platform/operational-rule-composer/{rule_id}", "get"),
        ("/api/platform/operational-rule-composer/{rule_id}", "put"),
        ("/api/platform/operational-rule-composer/{rule_id}", "delete"),
        ("/api/agencies/{agency_id}/rule-composer", "get"),
        ("/api/agencies/{agency_id}/rule-composer", "post"),
        ("/api/agencies/{agency_id}/rule-composer/summary", "get"),
        ("/api/agencies/{agency_id}/rule-composer/{rule_id}", "get"),
        ("/api/agencies/{agency_id}/rule-composer/{rule_id}", "put"),
        ("/api/agencies/{agency_id}/rule-composer/{rule_id}", "delete"),
    ]:
        assert_openapi_path(paths, path, method)
    for path in paths:
        if path.startswith("/api/admin") or path.startswith("/admin"):
            raise AssertionError(f"Old admin route must not be registered: {path}")

    for path, text in [
        (ROOT / "frontend/src/App.jsx", "/platform/operational-rule-composer"),
        (ROOT / "frontend/src/App.jsx", "/agency/rule-composer"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Operational Rule Composer"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "operational_rule_composer"),
        (ROOT / "frontend/src/pages/platform/OperationalRuleComposerPage.jsx", "All Conditions"),
        (ROOT / "frontend/src/pages/agency/RuleComposerPage.jsx", "Any Conditions"),
        (ROOT / "backend/services/saas_subscription_service.py", "operational_rule_composer"),
        (ROOT / "backend/services/blueprint_adoption_service.py", "Operational Rule Composer"),
        (ROOT / "docs/architecture/operational-rule-composer-foundation.md", "Phase 52.5"),
        (ROOT / "docs/architecture/current-model-inventory.md", "operational_rule_composer_rules"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/platform/operational-rule-composer"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Operational Rule Composer"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Operational rule composer"),
        (ROOT / "docs/architecture/airline-operational-intelligence-engine-foundation.md", "operational_rule_composer_rules"),
        (ROOT / "docs/architecture/service-parameter-taxonomy-integration-foundation.md", "Operational Rule Composer Alignment"),
        (ROOT / "docs/architecture/reference-data-engine-foundation.md", "Operational Rule Composer Relationship"),
        (ROOT / "docs/architecture/knowledge-import-templates-foundation.md", "Operational Rule Composer preparation"),
        (ROOT / "docs/architecture/visual-policy-editor-foundation.md", "operational rule composer records"),
        (ROOT / "docs/architecture/pricing-formula-builder-foundation.md", "Operational Rule Composer"),
        (ROOT / "docs/architecture/intelligent-offer-builder-integration-foundation.md", "Phase 52.5 Operational Rule Composer"),
        (ROOT / "docs/architecture/foundations/AIRLINE_OPERATIONAL_KNOWLEDGE_BLUEPRINT.md", "Phase 52.5"),
        (ROOT / "docs/architecture/foundations/AEROASSIST_ENGINEERING_PRINCIPLES.md", "Phase 52.5"),
        (ROOT / "docs/architecture/foundations/GLOSSARY.md", "Operational Rule Composer"),
        (ROOT / "BUILD_PHASES.md", "Implemented Phase 52.5"),
        (ROOT / "README.md", "operational rule composer records"),
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

    platform_reference = run_ref("ORC-SMOKE-PLATFORM")
    created = post(
        "/api/platform/operational-rule-composer",
        rule_payload(agency_id, platform_reference),
        OWNER_HEADERS,
        201,
    )
    assert_safety_flags(created)
    platform_rule = created["operational_rule_composer_rule"]
    assert_safety_flags(platform_rule)
    if platform_rule.get("rule_family") != "pets_animals" or len(platform_rule.get("conditions") or []) < 2:
        raise AssertionError("Platform rule did not preserve condition metadata.")
    if platform_rule.get("conditions_section", {}).get("condition_count") < 2:
        raise AssertionError("Platform rule projection did not expose no-code condition section.")

    listed = get(
        "/api/platform/operational-rule-composer?rule_family=pets_animals&service_code=PETC&severity=conditional&operator=route_includes_country&search=summer",
        OWNER_HEADERS,
    )
    if not any(item.get("rule_reference") == platform_reference for item in listed.get("items", [])):
        raise AssertionError("Platform filtered list did not include created operational rule.")
    summary = get("/api/platform/operational-rule-composer/summary", OWNER_HEADERS)
    if summary.get("summary", {}).get("total_condition_count", 0) < 1:
        raise AssertionError("Platform summary did not count rule conditions.")

    updated = put(
        f"/api/platform/operational-rule-composer/{platform_rule['id']}",
        {
            "lifecycle_status": "in_review",
            "severity": "blocking",
            "conditions": platform_rule["conditions"] + [{"field": "temperature_c", "operator": "outside_range", "value": [-5, 30]}],
        },
        OWNER_HEADERS,
    )["operational_rule_composer_rule"]
    if updated.get("lifecycle_status") != "in_review" or updated.get("severity") != "blocking":
        raise AssertionError("Platform update did not persist lifecycle and severity metadata.")
    if "outside_range" not in [condition.get("operator") for condition in updated.get("conditions", [])]:
        raise AssertionError("Platform update did not persist outside_range condition metadata.")

    agency_reference = run_ref("ORC-SMOKE-AGENCY")
    agency_created = post(
        f"/api/agencies/{agency_id}/rule-composer",
        rule_payload(agency_id, agency_reference, rule_family="passenger_assistance"),
        OWNER_HEADERS,
        201,
    )
    assert_safety_flags(agency_created)
    agency_rule = agency_created["operational_rule_composer_rule"]
    if agency_rule.get("agency_id") != agency_id or agency_rule.get("rule_family") != "passenger_assistance":
        raise AssertionError("Agency rule did not preserve agency scope.")

    agency_list = get(
        f"/api/agencies/{agency_id}/rule-composer?rule_family=passenger_assistance&service_code=WCHR&lifecycle_status=approved",
        OWNER_HEADERS,
    )
    if not any(item.get("rule_reference") == agency_reference for item in agency_list.get("items", [])):
        raise AssertionError("Agency filtered list did not include created operational rule.")

    agency_updated = put(
        f"/api/agencies/{agency_id}/rule-composer/{agency_rule['id']}",
        {
            "client_message": "Manual assistance confirmation is required.",
            "internal_message": "Review WCHR handling and connection details.",
            "parameter_taxonomy_links": ["SPT-SMOKE-525", "SPT-WCHR-SMOKE-525"],
        },
        OWNER_HEADERS,
    )["operational_rule_composer_rule"]
    if len(agency_updated.get("parameter_taxonomy_links") or []) < 2:
        raise AssertionError("Agency update did not persist parameter taxonomy links.")
    if not agency_updated.get("client_message") or not agency_updated.get("internal_message"):
        raise AssertionError("Agency update did not persist message metadata.")

    archived = request(
        "DELETE",
        f"/api/agencies/{agency_id}/rule-composer/{agency_rule['id']}",
        headers=OWNER_HEADERS,
        expect=200,
    )[1]["operational_rule_composer_rule"]
    if archived.get("lifecycle_status") != "archived" or archived.get("archived") is not True:
        raise AssertionError("Agency archive did not persist archived metadata.")

    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("operational_rule_composer_foundation") or {}
    for flag in [
        "operational_rule_composer_enabled",
        "operational_rule_composer_rules_collection_enabled",
        "platform_operational_rule_composer_metadata_crud_enabled",
        "agency_rule_composer_metadata_crud_enabled",
        "platform_operational_rule_composer_ui_enabled",
        "agency_rule_composer_ui_enabled",
        "no_code_compound_rules_enabled",
        "applies_to_metadata_enabled",
        "all_conditions_metadata_enabled",
        "any_conditions_metadata_enabled",
        "result_metadata_enabled",
        "severity_metadata_enabled",
        "client_message_metadata_enabled",
        "internal_message_metadata_enabled",
        "evidence_links_metadata_enabled",
        "governance_links_metadata_enabled",
        "parameter_taxonomy_links_metadata_enabled",
        "effective_dates_metadata_enabled",
        "lifecycle_status_metadata_enabled",
        "metadata_only",
        "rule_execution_disabled",
        "live_rule_evaluation_disabled",
        "provider_integrations_disabled",
        "ai_disabled",
        "background_workers_disabled",
        "automatic_decisioning_disabled",
        "human_authority_final",
    ]:
        if section.get(flag) is not True:
            raise AssertionError(f"Readiness missing flag: {flag}")
    if set(section.get("supported_operators") or []) != set(SUPPORTED_OPERATORS):
        raise AssertionError("Readiness did not expose supported operators.")
    if section.get("operational_rule_composer_total_condition_count", 0) < 1:
        raise AssertionError("Readiness did not count persisted rule conditions.")
    if section.get("operational_rule_composer_evidence_link_count", 0) < 1:
        raise AssertionError("Readiness did not count persisted evidence links.")
    if section.get("operational_rule_composer_parameter_taxonomy_link_count", 0) < 1:
        raise AssertionError("Readiness did not count persisted parameter taxonomy links.")


def verify_boundaries() -> None:
    openapi = get("/openapi.json", OWNER_HEADERS)
    for path in openapi.get("paths") or {}:
        lowered = path.lower()
        if lowered.startswith("/api/admin") or lowered.startswith("/admin"):
            raise AssertionError(f"Old admin route registered: {path}")
        if "operational-rule-composer" in lowered or "rule-composer" in lowered:
            for marker in ["execute", "evaluate", "provider", "ai-generate", "background-worker", "automatic-decision"]:
                if marker in lowered:
                    raise AssertionError(f"Forbidden Operational Rule Composer execution route registered: {path}")

    for path in [
        ROOT / "backend/services/operational_rule_composer_service.py",
        ROOT / "backend/routers/platform_operational_rule_composer.py",
        ROOT / "backend/routers/agency_operational_rule_composer.py",
        ROOT / "frontend/src/pages/platform/OperationalRuleComposerPage.jsx",
        ROOT / "frontend/src/pages/agency/RuleComposerPage.jsx",
    ]:
        for marker in [
            "import requests",
            "import httpx",
            "from openai",
            "import openai",
            "BackgroundTasks",
            "asyncio.create_task(",
            "def execute_rule",
            "def evaluate_rule",
            "def run_rule",
            "def apply_rule",
            "rule_engine_executor =",
            "provider_client =",
            "@router.post(\"/api/platform/operational-rule-composer/execute",
            "@router.post(\"/api/platform/operational-rule-composer/evaluate",
            "@router.post(\"/api/agencies/{agency_id}/rule-composer/execute",
            "@router.post(\"/api/agencies/{agency_id}/rule-composer/evaluate",
            "@router.get(\"/admin",
            "@router.post(\"/admin",
            "\"/api/admin",
        ]:
            reject_text(path, marker)


def main() -> int:
    verify_model_and_collection_registration()
    verify_router_ui_docs_registration()
    verify_crud_and_readiness()
    verify_boundaries()
    print("Operational rule composer foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Operational rule composer foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
