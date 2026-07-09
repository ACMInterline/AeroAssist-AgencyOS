#!/usr/bin/env python3
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import PricingFormulaBuilder, PricingFormulaBuilderCreate
from services.pricing_formula_builder_service import (
    AMOUNT_TYPES,
    CLIENT_VISIBILITY_OPTIONS,
    FORMULA_STATUSES,
    PHASE_LABEL,
    PRICING_CATEGORIES,
    PRICING_FARE_BUNDLES,
    PRICING_FLIGHT_TYPES,
    PRICING_FORMULA_BUILDERS_COLLECTION,
    PRICING_ROUTE_TYPES,
    PRICING_UNITS,
    PRICING_WAY_VALUES,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_52_6_knowledge_quality_assurance_foundation"
ROOT = Path(__file__).resolve().parents[2]

REQUIRED_AMOUNT_TYPES = {"fixed", "range", "percentage", "manual_quote", "formula", "included", "not_applicable"}
REQUIRED_PRICING_CATEGORIES = {
    "transport_core",
    "ancillary_airline",
    "ancillary_non_airline",
    "documentation",
    "service_coordination",
    "compliance_review",
    "manual_handling",
    "premium_support",
    "after_sales_change",
    "refund_processing",
    "claim_processing",
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
        "pricing_formula_builder_foundation",
        "live_price_calculation_disabled",
        "payment_integrations_disabled",
        "provider_integrations_disabled",
        "ai_disabled",
        "background_workers_disabled",
        "automatic_client_sending_disabled",
        "human_authority_final",
    ]:
        if payload.get(flag) is not True:
            raise AssertionError(f"Payload missing safety flag {flag}: {payload}")


def formula_payload(agency_id: str, reference: str, pricing_category: str = "ancillary_airline") -> dict:
    return {
        "agency_id": agency_id,
        "formula_reference": reference,
        "formula_name": "Phase 52.4 Smoke Formula",
        "formula_status": "approved",
        "airline": "LH",
        "service_family": "pets_animals",
        "service_codes": ["PETC"],
        "pricing_unit": "pet_per_segment",
        "way": "one_way",
        "route_type": "international",
        "flight_type": "mediumhaul",
        "fare_bundle": "standard",
        "pricing_category": pricing_category,
        "amount_type": "formula",
        "currency": "EUR",
        "base_amount": 75.0,
        "amount_range": {"min": 50, "max": 150},
        "formula_components": [
            {"component": "base_amount", "source": "manual_table", "value": 75},
            {"component": "segment_count", "source": "itinerary_metadata"},
        ],
        "multipliers": [{"name": "longhaul_adjustment", "factor": 1.25, "applies_when": "flight_type=longhaul"}],
        "applicability": {
            "cabins": ["economy"],
            "routes": ["BG-DE"],
            "requires_policy_confirmation": True,
        },
        "manual_confirmation_required": True,
        "client_visibility": "agent_visible",
        "refund_exchange_condition_references": ["REX-SMOKE-524"],
        "evidence_links": [{"reference": "EVIDENCE-SMOKE-524", "source": "manual_review"}],
        "governance_links": ["KGV-SMOKE-524"],
        "service_parameter_taxonomy_links": ["SPT-SMOKE-524"],
        "visual_policy_editor_links": ["VPE-SMOKE-524"],
        "internal_notes": "Metadata-only pricing formula smoke.",
        "client_notes": "Price requires manual confirmation.",
        "metadata": {"smoke": True, "human_authority_final": True},
    }


def verify_model_and_collection_registration() -> None:
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Service phase label mismatch: {PHASE_LABEL}")
    if PRICING_FORMULA_BUILDERS_COLLECTION not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("pricing_formula_builders is not registered as agency-owned metadata.")
    if REQUIRED_AMOUNT_TYPES - set(AMOUNT_TYPES):
        raise AssertionError(f"Amount types missing: {sorted(REQUIRED_AMOUNT_TYPES - set(AMOUNT_TYPES))}")
    if REQUIRED_PRICING_CATEGORIES - set(PRICING_CATEGORIES):
        raise AssertionError(f"Pricing categories missing: {sorted(REQUIRED_PRICING_CATEGORIES - set(PRICING_CATEGORIES))}")
    if "pet_per_segment" not in PRICING_UNITS or "one_way" not in PRICING_WAY_VALUES:
        raise AssertionError("Pricing unit/way metadata is incomplete.")
    if "international" not in PRICING_ROUTE_TYPES or "mediumhaul" not in PRICING_FLIGHT_TYPES:
        raise AssertionError("Route/flight type metadata is incomplete.")
    if "standard" not in PRICING_FARE_BUNDLES or "approved" not in FORMULA_STATUSES:
        raise AssertionError("Fare bundle/status metadata is incomplete.")
    if "agent_visible" not in CLIENT_VISIBILITY_OPTIONS:
        raise AssertionError("Client visibility metadata is incomplete.")

    create = PricingFormulaBuilderCreate(**formula_payload("agency-smoke", "PFB-SMOKE-MODEL"))
    record = PricingFormulaBuilder(**create.model_dump(mode="json", exclude_none=True))
    if record.formula_reference != "PFB-SMOKE-MODEL" or not record.formula_components or not record.refund_exchange_condition_references:
        raise AssertionError("PricingFormulaBuilder model did not preserve formula metadata.")
    if record.pricing_formula_builder_foundation is not True or record.live_price_calculation_disabled is not True:
        raise AssertionError("PricingFormulaBuilder model did not preserve metadata-only flags.")

    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for marker in [
        PRICING_FORMULA_BUILDERS_COLLECTION,
        "pricing_formula_builders_reference_unique",
        "pricing_formula_builders_agency_airline_lookup",
        "pricing_formula_builders_status_lookup",
        "pricing_formula_builders_service_codes_lookup",
        "pricing_formula_builders_pricing_unit_lookup",
        "pricing_formula_builders_way_lookup",
        "pricing_formula_builders_route_type_lookup",
        "pricing_formula_builders_flight_type_lookup",
        "pricing_formula_builders_fare_bundle_lookup",
        "pricing_formula_builders_category_lookup",
        "pricing_formula_builders_amount_type_lookup",
        "pricing_formula_builders_client_visibility_lookup",
        "pricing_formula_builders_refund_exchange_lookup",
        "pricing_formula_builders_archive_lookup",
    ]:
        if marker not in database_py:
            raise AssertionError(f"Database registration missing {marker}.")


def verify_router_ui_docs_registration() -> None:
    openapi = get("/openapi.json", OWNER_HEADERS)
    paths = openapi.get("paths") or {}
    for path, method in [
        ("/api/platform/pricing-formula-builder", "get"),
        ("/api/platform/pricing-formula-builder", "post"),
        ("/api/platform/pricing-formula-builder/summary", "get"),
        ("/api/platform/pricing-formula-builder/{formula_id}", "get"),
        ("/api/platform/pricing-formula-builder/{formula_id}", "put"),
        ("/api/platform/pricing-formula-builder/{formula_id}", "delete"),
        ("/api/agencies/{agency_id}/pricing-formula-builder", "get"),
        ("/api/agencies/{agency_id}/pricing-formula-builder", "post"),
        ("/api/agencies/{agency_id}/pricing-formula-builder/summary", "get"),
        ("/api/agencies/{agency_id}/pricing-formula-builder/{formula_id}", "get"),
        ("/api/agencies/{agency_id}/pricing-formula-builder/{formula_id}", "put"),
        ("/api/agencies/{agency_id}/pricing-formula-builder/{formula_id}", "delete"),
    ]:
        assert_openapi_path(paths, path, method)
    for path in paths:
        if path.startswith("/api/admin") or path.startswith("/admin"):
            raise AssertionError(f"Old admin route must not be registered: {path}")

    for path, text in [
        (ROOT / "frontend/src/App.jsx", "/platform/pricing-formula-builder"),
        (ROOT / "frontend/src/App.jsx", "/agency/pricing-formula-builder"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Pricing Formula Builder"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "pricing_formula_builder"),
        (ROOT / "frontend/src/pages/platform/PricingFormulaBuilderPage.jsx", "Formula Components"),
        (ROOT / "frontend/src/pages/agency/PricingFormulaBuilderPage.jsx", "Refund / Exchange Conditions"),
        (ROOT / "backend/services/saas_subscription_service.py", "pricing_formula_builder"),
        (ROOT / "backend/services/blueprint_adoption_service.py", "Pricing Formula Builder"),
        (ROOT / "docs/architecture/pricing-formula-builder-foundation.md", "Phase 52.4"),
        (ROOT / "docs/architecture/current-model-inventory.md", "pricing_formula_builders"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/platform/pricing-formula-builder"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Pricing Formula Builder"),
        (ROOT / "docs/architecture/airline-operational-intelligence-engine-foundation.md", "pricing_formula_builders"),
        (ROOT / "docs/architecture/service-parameter-taxonomy-integration-foundation.md", "Pricing Formula Builder Alignment"),
        (ROOT / "docs/architecture/reference-data-engine-foundation.md", "Pricing Formula Builder Relationship"),
        (ROOT / "docs/architecture/knowledge-import-templates-foundation.md", "Pricing Formula Builder preparation"),
        (ROOT / "docs/architecture/visual-policy-editor-foundation.md", "pricing formula builder records"),
        (ROOT / "docs/architecture/intelligent-offer-builder-integration-foundation.md", "Phase 52.4 Pricing Formula Builder"),
        (ROOT / "docs/architecture/foundations/AIRLINE_OPERATIONAL_KNOWLEDGE_BLUEPRINT.md", "Phase 52.4"),
        (ROOT / "docs/architecture/foundations/AEROASSIST_ENGINEERING_PRINCIPLES.md", "Phase 52.4"),
        (ROOT / "docs/architecture/foundations/GLOSSARY.md", "Pricing Formula Builder"),
        (ROOT / "BUILD_PHASES.md", "Implemented Phase 52.4"),
        (ROOT / "README.md", "pricing formula builder records"),
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

    platform_reference = run_ref("PFB-SMOKE-PLATFORM")
    created = post(
        "/api/platform/pricing-formula-builder",
        formula_payload(agency_id, platform_reference),
        OWNER_HEADERS,
        201,
    )
    assert_safety_flags(created)
    platform_formula = created["pricing_formula_builder"]
    assert_safety_flags(platform_formula)
    if platform_formula.get("amount_type") != "formula" or not platform_formula.get("formula_components"):
        raise AssertionError("Platform pricing formula did not preserve formula component metadata.")

    listed = get(
        "/api/platform/pricing-formula-builder?airline=LH&service_code=PETC&pricing_unit=pet_per_segment&pricing_category=ancillary_airline&amount_type=formula&currency=EUR&search=manual",
        OWNER_HEADERS,
    )
    if not any(item.get("formula_reference") == platform_reference for item in listed.get("items", [])):
        raise AssertionError("Platform filtered list did not include created pricing formula.")
    summary = get("/api/platform/pricing-formula-builder/summary", OWNER_HEADERS)
    if summary.get("summary", {}).get("formula_component_count", 0) < 1:
        raise AssertionError("Platform summary did not count formula components.")

    updated = put(
        f"/api/platform/pricing-formula-builder/{platform_formula['id']}",
        {
            "formula_status": "in_review",
            "client_visibility": "client_visible",
            "multipliers": platform_formula["multipliers"] + [{"name": "manual_review_modifier", "factor": 1.0}],
        },
        OWNER_HEADERS,
    )["pricing_formula_builder"]
    if updated.get("formula_status") != "in_review" or updated.get("client_visibility") != "client_visible":
        raise AssertionError("Platform update did not persist status and visibility metadata.")

    agency_reference = run_ref("PFB-SMOKE-AGENCY")
    agency_payload = formula_payload(agency_id, agency_reference, pricing_category="service_coordination")
    agency_payload["amount_type"] = "fixed"
    agency_payload["formula_components"] = [{"component": "coordination_fee", "source": "manual_policy", "value": 35}]
    agency_created = post(
        f"/api/agencies/{agency_id}/pricing-formula-builder",
        agency_payload,
        OWNER_HEADERS,
        201,
    )
    assert_safety_flags(agency_created)
    agency_formula = agency_created["pricing_formula_builder"]
    if agency_formula.get("agency_id") != agency_id or agency_formula.get("pricing_category") != "service_coordination":
        raise AssertionError("Agency pricing formula did not preserve agency scope.")

    agency_list = get(
        f"/api/agencies/{agency_id}/pricing-formula-builder?pricing_category=service_coordination&amount_type=fixed&manual_confirmation_required=true",
        OWNER_HEADERS,
    )
    if not any(item.get("formula_reference") == agency_reference for item in agency_list.get("items", [])):
        raise AssertionError("Agency filtered list did not include created pricing formula.")

    agency_updated = put(
        f"/api/agencies/{agency_id}/pricing-formula-builder/{agency_formula['id']}",
        {"manual_confirmation_required": False, "refund_exchange_condition_references": ["REX-SMOKE-524", "REFUND-SMOKE-524"]},
        OWNER_HEADERS,
    )["pricing_formula_builder"]
    if agency_updated.get("manual_confirmation_required") is not False or len(agency_updated.get("refund_exchange_condition_references") or []) < 2:
        raise AssertionError("Agency update did not persist manual confirmation/refund metadata.")

    archived = request(
        "DELETE",
        f"/api/agencies/{agency_id}/pricing-formula-builder/{agency_formula['id']}",
        headers=OWNER_HEADERS,
        expect=200,
    )[1]["pricing_formula_builder"]
    if archived.get("formula_status") != "archived" or archived.get("archived") is not True:
        raise AssertionError("Agency archive did not persist archived metadata.")

    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("pricing_formula_builder_foundation") or {}
    for flag in [
        "pricing_formula_builder_enabled",
        "pricing_formula_builders_collection_enabled",
        "platform_pricing_formula_builder_metadata_crud_enabled",
        "agency_pricing_formula_builder_metadata_crud_enabled",
        "platform_pricing_formula_builder_ui_enabled",
        "agency_pricing_formula_builder_ui_enabled",
        "formula_components_metadata_enabled",
        "multipliers_metadata_enabled",
        "applicability_metadata_enabled",
        "manual_confirmation_metadata_enabled",
        "client_visibility_metadata_enabled",
        "refund_exchange_condition_reference_metadata_enabled",
        "metadata_only",
        "live_price_calculation_disabled",
        "payment_integrations_disabled",
        "provider_integrations_disabled",
        "ai_disabled",
        "background_workers_disabled",
        "automatic_client_sending_disabled",
        "human_authority_final",
    ]:
        if section.get(flag) is not True:
            raise AssertionError(f"Readiness missing flag: {flag}")
    if set(section.get("amount_types") or []) != set(AMOUNT_TYPES):
        raise AssertionError("Readiness did not expose supported amount types.")
    if set(section.get("pricing_categories") or []) != set(PRICING_CATEGORIES):
        raise AssertionError("Readiness did not expose supported pricing categories.")
    if section.get("pricing_formula_builder_component_count", 0) < 1:
        raise AssertionError("Readiness did not count persisted formula components.")
    if section.get("pricing_formula_builder_refund_exchange_reference_count", 0) < 1:
        raise AssertionError("Readiness did not count refund/exchange condition references.")


def verify_boundaries() -> None:
    openapi = get("/openapi.json", OWNER_HEADERS)
    for path in openapi.get("paths") or {}:
        lowered = path.lower()
        if lowered.startswith("/api/admin") or lowered.startswith("/admin"):
            raise AssertionError(f"Old admin route registered: {path}")
        if "pricing-formula-builder" in lowered:
            for marker in ["calculate", "execute", "payment", "provider", "ai-generate", "background-worker", "send-client"]:
                if marker in lowered:
                    raise AssertionError(f"Forbidden pricing formula execution route registered: {path}")

    for path in [
        ROOT / "backend/services/pricing_formula_builder_service.py",
        ROOT / "backend/routers/platform_pricing_formula_builder.py",
        ROOT / "backend/routers/agency_pricing_formula_builder.py",
        ROOT / "frontend/src/pages/platform/PricingFormulaBuilderPage.jsx",
        ROOT / "frontend/src/pages/agency/PricingFormulaBuilderPage.jsx",
    ]:
        for marker in [
            "import requests",
            "import httpx",
            "from openai",
            "import openai",
            "BackgroundTasks",
            "asyncio.create_task(",
            "def calculate_live_price",
            "def calculate_price",
            "def execute_formula",
            "def collect_payment",
            "payment_gateway =",
            "provider_client =",
            "@router.post(\"/api/platform/pricing-formula-builder/calculate",
            "@router.post(\"/api/agencies/{agency_id}/pricing-formula-builder/calculate",
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
    print("Pricing formula builder foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Pricing formula builder foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
