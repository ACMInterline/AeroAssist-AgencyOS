#!/usr/bin/env python3
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import ReferenceDataDomain, ReferenceDataDomainCreate
from services.reference_data_engine_service import (
    GOVERNANCE_STATUSES,
    PHASE_LABEL,
    REFERENCE_DATA_DOMAINS_COLLECTION,
    REVIEW_STATUSES,
    SUPPORTED_REFERENCE_DOMAIN_CODES,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_56_2_journey_option_fare_brand_composition_workspace_foundation"
ROOT = Path(__file__).resolve().parents[2]

REQUIRED_DOMAIN_CODES = {
    "airlines",
    "airports",
    "countries",
    "cities",
    "currencies",
    "aircraft_types",
    "aircraft_families",
    "cabin_classes",
    "seat_types",
    "passenger_types",
    "service_codes",
    "service_families",
    "ssr_codes",
    "osi_templates",
    "rfic_rfisc",
    "pet_species",
    "pet_breeds",
    "breed_risk_flags",
    "container_types",
    "document_types",
    "vaccination_types",
    "mobility_levels",
    "wheelchair_device_types",
    "battery_types",
    "medical_equipment_types",
    "route_types",
    "flight_types",
    "fare_bundles",
    "pricing_units",
    "pricing_categories",
    "formula_components",
    "temperature_zones",
    "seasonal_restriction_types",
    "travel_purposes",
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
        "reference_data_engine_foundation",
        "airline_operational_knowledge_production_ready",
        "provider_integrations_disabled",
        "ai_disabled",
        "live_evaluation_disabled",
        "pricing_calculation_disabled",
        "background_workers_disabled",
        "old_admin_routes_disabled",
        "human_authority_final",
    ]:
        if payload.get(flag) is not True:
            raise AssertionError(f"Payload missing safety flag {flag}: {payload}")


def domain_payload(agency_id: str, reference: str, domain_code: str = "pet_breeds") -> dict:
    return {
        "agency_id": agency_id,
        "domain_reference": reference,
        "domain_code": domain_code,
        "domain_label": "Pet Breeds" if domain_code == "pet_breeds" else "SSR Codes",
        "domain_description": "Phase 52.1 smoke reference domain.",
        "records": [
            {
                "code": "PUG" if domain_code == "pet_breeds" else "WCHR",
                "label": "Pug" if domain_code == "pet_breeds" else "Wheelchair ramp",
                "metadata": {"smoke": True, "phase": "52.1"},
            }
        ],
        "aliases": [
            {
                "alias": "pug dog" if domain_code == "pet_breeds" else "wheelchair assistance",
                "code": "PUG" if domain_code == "pet_breeds" else "WCHR",
            }
        ],
        "normalization_rules": [{"source": "intake", "rule": "lowercase_trim"}],
        "validation_rules": [{"field": "code", "required": True}],
        "import_template_reference": "IMPORT-PHASE-52-1",
        "governance_status": "approved",
        "review_status": "approved",
        "active": True,
        "metadata": {"smoke": True, "human_authority_final": True},
    }


def verify_model_and_collection_registration() -> None:
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Service phase label mismatch: {PHASE_LABEL}")
    if REFERENCE_DATA_DOMAINS_COLLECTION not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("reference_data_domains is not registered as agency-owned metadata.")
    missing_codes = REQUIRED_DOMAIN_CODES - set(SUPPORTED_REFERENCE_DOMAIN_CODES)
    if missing_codes:
        raise AssertionError(f"Supported reference domains missing: {sorted(missing_codes)}")
    if "approved" not in GOVERNANCE_STATUSES or "needs_review" not in REVIEW_STATUSES:
        raise AssertionError("Governance/review statuses are incomplete.")

    create = ReferenceDataDomainCreate(**domain_payload("agency-smoke", "RDE-SMOKE-MODEL"))
    record = ReferenceDataDomain(**create.model_dump(mode="json", exclude_none=True))
    if record.domain_reference != "RDE-SMOKE-MODEL" or not record.records or not record.aliases:
        raise AssertionError("ReferenceDataDomain model did not preserve records and aliases.")
    if record.reference_data_engine_foundation is not True or record.pricing_calculation_disabled is not True:
        raise AssertionError("ReferenceDataDomain model did not preserve metadata-only flags.")

    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for marker in [
        REFERENCE_DATA_DOMAINS_COLLECTION,
        "reference_data_domains_reference_unique",
        "reference_data_domains_agency_domain_lookup",
        "reference_data_domains_domain_code_lookup",
        "reference_data_domains_governance_status_lookup",
        "reference_data_domains_review_status_lookup",
        "reference_data_domains_record_code_lookup",
        "reference_data_domains_alias_lookup",
        "reference_data_domains_archive_lookup",
    ]:
        if marker not in database_py:
            raise AssertionError(f"Database registration missing {marker}.")


def verify_router_ui_docs_registration() -> None:
    openapi = get("/openapi.json", OWNER_HEADERS)
    paths = openapi.get("paths") or {}
    for path, method in [
        ("/api/platform/reference-data-engine", "get"),
        ("/api/platform/reference-data-engine", "post"),
        ("/api/platform/reference-data-engine/summary", "get"),
        ("/api/platform/reference-data-engine/{domain_id}", "get"),
        ("/api/platform/reference-data-engine/{domain_id}", "put"),
        ("/api/platform/reference-data-engine/{domain_id}", "delete"),
        ("/api/agencies/{agency_id}/reference-data-engine", "get"),
        ("/api/agencies/{agency_id}/reference-data-engine", "post"),
        ("/api/agencies/{agency_id}/reference-data-engine/summary", "get"),
        ("/api/agencies/{agency_id}/reference-data-engine/{domain_id}", "get"),
        ("/api/agencies/{agency_id}/reference-data-engine/{domain_id}", "put"),
        ("/api/agencies/{agency_id}/reference-data-engine/{domain_id}", "delete"),
    ]:
        assert_openapi_path(paths, path, method)
    for path in paths:
        if path.startswith("/api/admin") or path.startswith("/admin"):
            raise AssertionError(f"Old admin route must not be registered: {path}")

    for path, text in [
        (ROOT / "frontend/src/App.jsx", "/platform/reference-data-engine"),
        (ROOT / "frontend/src/App.jsx", "/agency/reference-data-engine"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Reference Data Engine"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "reference_data_engine"),
        (ROOT / "frontend/src/pages/platform/ReferenceDataEnginePage.jsx", "Domain Overview"),
        (ROOT / "frontend/src/pages/platform/ReferenceDataEnginePage.jsx", "Normalization Rules"),
        (ROOT / "frontend/src/pages/agency/ReferenceDataEnginePage.jsx", "Production Readiness"),
        (ROOT / "backend/services/saas_subscription_service.py", "reference_data_engine"),
        (ROOT / "backend/services/blueprint_adoption_service.py", "Reference Data Engine"),
        (ROOT / "docs/architecture/reference-data-engine-foundation.md", "Phase 52.1"),
        (ROOT / "docs/architecture/current-model-inventory.md", "reference_data_domains"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/platform/reference-data-engine"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Reference Data Engine"),
        (ROOT / "docs/architecture/airline-operational-intelligence-engine-foundation.md", "reference_data_domains"),
        (ROOT / "docs/architecture/service-parameter-taxonomy-integration-foundation.md", "Reference Data Engine Alignment"),
        (ROOT / "docs/architecture/foundations/AIRLINE_OPERATIONAL_KNOWLEDGE_BLUEPRINT.md", "Phase 52.1"),
        (ROOT / "docs/architecture/foundations/GLOSSARY.md", "Reference Data Engine"),
        (ROOT / "BUILD_PHASES.md", "Implemented Phase 52.1"),
        (ROOT / "README.md", "reference data engine domain records"),
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

    platform_reference = run_ref("RDE-SMOKE-PLATFORM")
    created = post(
        "/api/platform/reference-data-engine",
        domain_payload(agency_id, platform_reference),
        OWNER_HEADERS,
        201,
    )
    assert_safety_flags(created)
    platform_domain = created["reference_data_domain"]
    assert_safety_flags(platform_domain)
    if platform_domain.get("domain_code") != "pet_breeds" or not platform_domain.get("records"):
        raise AssertionError("Platform reference domain did not preserve domain records.")

    listed = get("/api/platform/reference-data-engine?domain_code=pet_breeds&search=pug", OWNER_HEADERS)
    if not any(item.get("domain_reference") == platform_reference for item in listed.get("items", [])):
        raise AssertionError("Platform filtered list did not include created reference domain.")
    summary = get("/api/platform/reference-data-engine/summary", OWNER_HEADERS)
    if summary.get("summary", {}).get("record_count", 0) < 1:
        raise AssertionError("Platform summary did not count reference records.")

    updated = put(
        f"/api/platform/reference-data-engine/{platform_domain['id']}",
        {
            "review_status": "changes_requested",
            "records": platform_domain["records"] + [{"code": "BULLDOG", "label": "Bulldog"}],
            "validation_rules": platform_domain["validation_rules"] + [{"field": "label", "required": True}],
        },
        OWNER_HEADERS,
    )["reference_data_domain"]
    if updated.get("review_status") != "changes_requested" or len(updated.get("records") or []) < 2:
        raise AssertionError("Platform update did not persist review status and records.")

    agency_reference = run_ref("RDE-SMOKE-AGENCY")
    agency_created = post(
        f"/api/agencies/{agency_id}/reference-data-engine",
        domain_payload(agency_id, agency_reference, domain_code="ssr_codes"),
        OWNER_HEADERS,
        201,
    )
    assert_safety_flags(agency_created)
    agency_domain = agency_created["reference_data_domain"]
    if agency_domain.get("agency_id") != agency_id or agency_domain.get("domain_code") != "ssr_codes":
        raise AssertionError("Agency reference domain did not preserve agency scope.")

    agency_list = get(f"/api/agencies/{agency_id}/reference-data-engine?domain_code=ssr_codes&active=true", OWNER_HEADERS)
    if not any(item.get("domain_reference") == agency_reference for item in agency_list.get("items", [])):
        raise AssertionError("Agency filtered list did not include created reference domain.")

    agency_updated = put(
        f"/api/agencies/{agency_id}/reference-data-engine/{agency_domain['id']}",
        {"governance_status": "in_review", "normalization_rules": [{"source": "airline", "rule": "uppercase_code"}]},
        OWNER_HEADERS,
    )["reference_data_domain"]
    if agency_updated.get("governance_status") != "in_review":
        raise AssertionError("Agency update did not persist governance status.")

    archived = request(
        "DELETE",
        f"/api/agencies/{agency_id}/reference-data-engine/{agency_domain['id']}",
        headers=OWNER_HEADERS,
        expect=200,
    )[1]["reference_data_domain"]
    if archived.get("active") is not False or archived.get("governance_status") != "archived":
        raise AssertionError("Agency archive did not persist inactive archived metadata.")

    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("reference_data_engine_foundation") or {}
    for flag in [
        "reference_data_engine_enabled",
        "reference_data_domains_collection_enabled",
        "platform_reference_data_engine_metadata_crud_enabled",
        "agency_reference_data_metadata_crud_enabled",
        "platform_reference_data_engine_ui_enabled",
        "agency_reference_data_ui_enabled",
        "metadata_only",
        "provider_integrations_disabled",
        "ai_disabled",
        "live_evaluation_disabled",
        "pricing_calculation_disabled",
        "background_workers_disabled",
        "old_admin_routes_disabled",
        "human_authority_final",
    ]:
        if section.get(flag) is not True:
            raise AssertionError(f"Readiness missing flag: {flag}")
    if set(section.get("supported_domain_codes") or []) != set(SUPPORTED_REFERENCE_DOMAIN_CODES):
        raise AssertionError("Readiness did not expose supported domain codes.")
    if section.get("reference_data_engine_record_count", 0) < 1:
        raise AssertionError("Readiness did not count persisted reference records.")


def verify_boundaries() -> None:
    openapi = get("/openapi.json", OWNER_HEADERS)
    for path in openapi.get("paths") or {}:
        lowered = path.lower()
        if lowered.startswith("/api/admin") or lowered.startswith("/admin"):
            raise AssertionError(f"Old admin route registered: {path}")
        for marker in ["live-flight-search", "booking-provider", "ticketing-provider", "ai-generate", "background-worker"]:
            if marker in lowered:
                raise AssertionError(f"Forbidden execution route registered: {path}")

    for path in [
        ROOT / "backend/services/reference_data_engine_service.py",
        ROOT / "backend/routers/platform_reference_data_engine.py",
        ROOT / "backend/routers/agency_reference_data_engine.py",
        ROOT / "frontend/src/pages/platform/ReferenceDataEnginePage.jsx",
        ROOT / "frontend/src/pages/agency/ReferenceDataEnginePage.jsx",
    ]:
        for marker in [
            "BackgroundTasks",
            "asyncio.create_task",
            "httpx",
            "requests.",
            "openai",
            "ChatCompletion",
            "provider_client =",
            "def calculate_price",
            "def calculate_pricing",
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
    print("Reference data engine foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Reference data engine foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
