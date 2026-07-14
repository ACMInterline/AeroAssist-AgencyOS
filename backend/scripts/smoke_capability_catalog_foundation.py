#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import CapabilityCatalogEntry
from services.capability_catalog_service import DEFAULT_CAPABILITY_CATALOG
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get


EXPECTED_PHASE = "phase_55_6_interline_codeshare_operating_carrier_intelligence_foundation"
ROOT = Path(__file__).resolve().parents[2]


def require_flag(section: dict, key: str, expected: object = True) -> None:
    if section.get(key) is not expected:
        raise AssertionError(f"Readiness flag {key} expected {expected!r}, got {section.get(key)!r}")


def require_text(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8")
    if text not in content:
        raise AssertionError(f"{path.relative_to(ROOT)} missing expected text: {text}")


def reject_text(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8")
    if text in content:
        raise AssertionError(f"{path.relative_to(ROOT)} contains rejected text: {text}")


def verify_model_and_collection_registration() -> None:
    entry = CapabilityCatalogEntry(
        code="smoke_capability",
        name="Smoke Capability",
        required_feature_flags=["smoke_flag"],
        required_bundles=["smoke_bundle"],
        dependencies=["dashboard"],
        ui_routes=["/agency/capabilities"],
        documentation_links=["docs/architecture/capability-catalog-foundation.md"],
    )
    dumped = entry.model_dump(mode="json")
    if dumped.get("metadata_only") is not True:
        raise AssertionError(f"Capability catalog model is not metadata-only: {dumped}")
    if dumped.get("execution_logic_disabled") is not True:
        raise AssertionError(f"Capability catalog model should disable execution logic: {dumped}")
    if dumped.get("entitlement_enforcement_disabled") is not True:
        raise AssertionError(f"Capability catalog model should disable entitlement enforcement: {dumped}")
    if "capability_catalog" in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("Capability catalog should remain platform-scoped, not agency-owned.")
    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "capability_catalog_id_unique",
        "capability_catalog_code_unique",
        "capability_catalog_category_lookup",
        "capability_catalog_module_lookup",
        "capability_catalog_status_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Capability catalog index missing: {index_name}")
    if len(DEFAULT_CAPABILITY_CATALOG) < 20:
        raise AssertionError(f"Expected default capability catalog metadata, got {len(DEFAULT_CAPABILITY_CATALOG)} entries.")


def verify_routes(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    read_only_routes = [
        "/api/platform/capabilities",
        "/api/platform/capabilities/{code}",
        "/api/platform/capabilities/categories",
        "/api/platform/capabilities/modules",
        "/api/agencies/{agency_id}/capabilities",
        "/api/agencies/{agency_id}/capabilities/available",
        "/api/agencies/{agency_id}/capabilities/unavailable",
        "/api/system/readiness",
    ]
    for path in read_only_routes:
        assert_openapi_path(paths, path, "get")
        methods = set(paths.get(path, {}).keys())
        blocked_methods = methods & {"post", "patch", "put", "delete"}
        if blocked_methods:
            raise AssertionError(f"Read-only capability route exposes write methods: {path} {sorted(blocked_methods)}")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Capability Catalog"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Available Capabilities"),
        (ROOT / "frontend/src/App.jsx", "/platform/capabilities"),
        (ROOT / "frontend/src/App.jsx", "/agency/capabilities"),
        (ROOT / "frontend/src/pages/platform/CapabilityCatalogPage.jsx", "Platform Capability Catalog"),
        (ROOT / "frontend/src/pages/platform/CapabilityCatalogPage.jsx", "Dependency view"),
        (ROOT / "frontend/src/pages/agency/CapabilitiesPage.jsx", "Available Capabilities"),
        (ROOT / "docs/architecture/capability-catalog-foundation.md", "Capability Catalog Foundation"),
        (ROOT / "README.md", "Phase 40.1 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 40.1: Capability Catalog Foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "Phase 40.1 adds capability catalog metadata"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "Phase 40.1 adds read-only capability catalog APIs"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Capability catalog"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Capability catalog"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/CapabilityCatalogPage.jsx",
        ROOT / "frontend/src/pages/agency/CapabilitiesPage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)


def verify_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")
    readiness = get("/api/readiness")
    system_readiness = get("/api/system/readiness")
    for payload in [readiness, system_readiness]:
        if payload.get("phase") != EXPECTED_PHASE:
            raise AssertionError(f"Unexpected readiness phase: {payload.get('phase')}")
    section = readiness.get("capability_catalog_foundation") or {}
    for flag in [
        "capability_catalog_enabled",
        "platform_capability_catalog_enabled",
        "agency_capability_visibility_enabled",
        "category_listing_enabled",
        "module_listing_enabled",
        "search_filter_metadata_enabled",
        "flag_references_enabled",
        "bundle_references_enabled",
        "dependency_view_enabled",
        "documentation_links_enabled",
        "availability_informational_only",
        "metadata_only",
        "read_only",
        "no_execution_logic",
    ]:
        require_flag(section, flag)
    for flag in [
        "runtime_feature_enforcement_disabled",
        "entitlement_checks_disabled",
        "entitlement_enforcement_disabled",
        "billing_disabled",
        "payments_disabled",
        "subscription_charging_disabled",
        "route_blocking_disabled",
        "permission_changes_disabled",
        "provider_execution_disabled",
        "publishing_disabled",
        "external_services_disabled",
        "external_api_calls_disabled",
        "external_ai_disabled",
        "background_workers_disabled",
        "cron_disabled",
    ]:
        require_flag(section, flag)
    require_flag(section, "readiness_required", False)
    if section.get("default_capability_count", 0) < 20:
        raise AssertionError(f"Expected default capability metadata count, got {section.get('default_capability_count')}")


def verify_endpoint_behavior() -> None:
    platform_capabilities = get("/api/platform/capabilities", OWNER_HEADERS)
    if platform_capabilities.get("phase") != EXPECTED_PHASE or platform_capabilities.get("read_only") is not True:
        raise AssertionError(f"Platform capability response is not read-only metadata: {platform_capabilities}")
    for flag in ["metadata_only", "runtime_feature_enforcement_disabled", "entitlement_checks_disabled", "route_blocking_disabled", "billing_disabled", "provider_execution_disabled", "external_services_disabled"]:
        require_flag(platform_capabilities, flag)
    items = platform_capabilities.get("items") or []
    if not any(item.get("code") == "capability_catalog" for item in items):
        raise AssertionError("Default capability catalog entry missing.")
    if platform_capabilities.get("capability_count", 0) < 20:
        raise AssertionError(f"Expected default capability catalog items, got {platform_capabilities.get('capability_count')}")

    categories = get("/api/platform/capabilities/categories", OWNER_HEADERS)
    category_names = {item.get("category") for item in categories.get("items") or []}
    if not {"core", "feature_governance"}.issubset(category_names):
        raise AssertionError(f"Expected capability categories missing: {categories}")
    modules = get("/api/platform/capabilities/modules", OWNER_HEADERS)
    module_names = {item.get("module") for item in modules.get("items") or []}
    if "settings" not in module_names or "booking" not in module_names:
        raise AssertionError(f"Expected capability modules missing: {modules}")

    detail = get("/api/platform/capabilities/capability_catalog", OWNER_HEADERS)
    capability = detail.get("capability") or {}
    if capability.get("code") != "capability_catalog" or capability.get("metadata_only") is not True:
        raise AssertionError(f"Capability detail malformed: {detail}")

    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires seeded demo agency.")
    agency_id = agencies[0]["id"]
    agency_capabilities = get(f"/api/agencies/{agency_id}/capabilities", OWNER_HEADERS)
    if agency_capabilities.get("read_only") is not True or agency_capabilities.get("metadata_only") is not True:
        raise AssertionError(f"Agency capability response should be read-only metadata: {agency_capabilities}")
    if "availability_counts" not in agency_capabilities:
        raise AssertionError(f"Agency capability response missing availability counts: {agency_capabilities}")
    for path in [
        f"/api/agencies/{agency_id}/capabilities/available",
        f"/api/agencies/{agency_id}/capabilities/unavailable",
    ]:
        response = get(path, OWNER_HEADERS)
        if response.get("phase") != EXPECTED_PHASE or response.get("read_only") is not True:
            raise AssertionError(f"Agency capability filtered endpoint malformed: {path} {response}")

    summary = get("/api/platform/summary", OWNER_HEADERS)
    if "capability_catalog" not in (summary.get("counts") or {}):
        raise AssertionError("Platform summary missing capability_catalog count.")


def main() -> int:
    verify_model_and_collection_registration()
    openapi = get("/openapi.json")
    verify_routes(openapi.get("paths") or {})
    verify_frontend_and_docs()
    verify_readiness()
    verify_endpoint_behavior()
    print("Phase 40.1 capability catalog foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Phase 40.1 capability catalog foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
