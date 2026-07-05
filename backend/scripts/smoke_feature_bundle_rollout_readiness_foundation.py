#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import FeatureBundleRolloutChecklistItem, FeatureBundleRolloutReadiness
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, request


EXPECTED_PHASE = "phase_40_8_feature_bundle_rollout_risk_register_foundation"
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
    checklist_item = FeatureBundleRolloutChecklistItem(
        item_key="smoke_check",
        label="Smoke check",
        status="warning",
        notes="Metadata-only smoke checklist item.",
    )
    readiness = FeatureBundleRolloutReadiness(
        agency_id="agency-smoke",
        bundle_id="bundle_core_agency",
        assignment_id="assignment-smoke",
        readiness_status="reviewing",
        checklist_items=[checklist_item],
        notes="Metadata-only smoke readiness.",
    )
    dumped = readiness.model_dump(mode="json")
    if dumped.get("metadata_only") is not True:
        raise AssertionError(f"Rollout readiness model is not metadata-only: {dumped}")
    for flag in ["activation_logic_disabled", "feature_access_enforcement_disabled", "billing_disabled", "provider_execution_disabled"]:
        if dumped.get(flag) is not True:
            raise AssertionError(f"Rollout readiness model missing disabled flag {flag}: {dumped}")
    if dumped["checklist_items"][0].get("status") != "warning":
        raise AssertionError(f"Checklist status was not preserved: {dumped}")
    if "agency_feature_bundle_rollout_readiness" not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("Rollout readiness collection is not agency-owned/registered.")
    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "agency_feature_bundle_rollout_readiness_id_unique",
        "agency_feature_bundle_rollout_readiness_assignment_unique",
        "agency_feature_bundle_rollout_readiness_agency_status_lookup",
        "agency_feature_bundle_rollout_readiness_bundle_status_lookup",
        "agency_feature_bundle_rollout_readiness_reviewed_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Rollout readiness index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    expected_methods = {
        "/api/platform/feature-bundle-rollout-readiness": {"get"},
        "/api/platform/feature-bundle-rollout-readiness/summary": {"get"},
        "/api/platform/feature-bundle-rollout-readiness/defaults": {"post"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-readiness": {"get"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-readiness/summary": {"get"},
    }
    for path, methods in expected_methods.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in [
        "/api/agencies/{agency_id}/feature-bundle-rollout-readiness",
        "/api/agencies/{agency_id}/feature-bundle-rollout-readiness/summary",
    ]:
        methods = set(paths.get(path, {}).keys())
        blocked_methods = methods & {"post", "put", "patch", "delete"}
        if blocked_methods:
            raise AssertionError(f"Agency rollout readiness route is not read-only: {path} {sorted(blocked_methods)}")


def verify_previous_phase_smoke_compatibility(paths: dict) -> None:
    for path, method in [
        ("/api/platform/feature-flag-bundles", "get"),
        ("/api/platform/feature-bundle-assignments", "get"),
        ("/api/platform/agencies/{agency_id}/bundle-assignments", "post"),
        ("/api/agencies/{agency_id}/feature-bundle-assignments", "get"),
        ("/api/agencies/{agency_id}/feature-bundle-assignment-history", "get"),
    ]:
        assert_openapi_path(paths, path, method)
    readiness = get("/api/readiness")
    for section_name in ["feature_flag_bundle_foundation", "feature_bundle_assignment_foundation"]:
        section = readiness.get(section_name) or {}
        if not section.get("metadata_only"):
            raise AssertionError(f"Previous phase readiness section missing or not metadata-only: {section_name}")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Feature Bundle Rollout Readiness"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Bundle Rollout Readiness"),
        (ROOT / "frontend/src/App.jsx", "/platform/feature-bundle-rollout-readiness"),
        (ROOT / "frontend/src/App.jsx", "/agency/bundle-rollout-readiness"),
        (ROOT / "frontend/src/pages/platform/FeatureBundleRolloutReadinessPage.jsx", "Feature Bundle Rollout Readiness"),
        (ROOT / "frontend/src/pages/platform/FeatureBundleRolloutReadinessPage.jsx", "does not activate, deactivate, allow, or block features"),
        (ROOT / "frontend/src/pages/agency/BundleRolloutReadinessPage.jsx", "Bundle Rollout Readiness"),
        (ROOT / "frontend/src/pages/agency/BundleRolloutReadinessPage.jsx", "does not activate or block features"),
        (ROOT / "docs/architecture/feature-bundle-rollout-readiness-foundation.md", "Feature Bundle Rollout Readiness Foundation"),
        (ROOT / "README.md", "Phase 40.1 Feature Bundle Rollout Readiness"),
        (ROOT / "BUILD_PHASES.md", "Phase 40.1: Feature Bundle Rollout Readiness Foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "Phase 40.1 adds feature bundle rollout readiness metadata"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "Phase 40.1 adds feature bundle rollout readiness APIs"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Feature bundle rollout readiness"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Feature bundle rollout readiness"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/FeatureBundleRolloutReadinessPage.jsx",
        ROOT / "frontend/src/pages/agency/BundleRolloutReadinessPage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)


def verify_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")
    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("feature_bundle_rollout_readiness_foundation") or {}
    for flag in [
        "feature_bundle_rollout_readiness_enabled",
        "feature_bundle_rollout_checklist_enabled",
        "default_readiness_views_enabled",
        "platform_rollout_readiness_review_enabled",
        "agency_rollout_readiness_read_only_enabled",
        "readiness_status_summary_enabled",
        "metadata_only",
    ]:
        require_flag(section, flag)
    for flag in [
        "activation_logic_disabled",
        "feature_activation_disabled",
        "feature_deactivation_disabled",
        "feature_access_enforcement_disabled",
        "route_blocking_disabled",
        "permission_changes_disabled",
        "entitlement_enforcement_disabled",
        "entitlement_evaluation_disabled",
        "billing_disabled",
        "payments_disabled",
        "email_sending_disabled",
        "sms_sending_disabled",
        "notifications_disabled",
        "provider_execution_disabled",
        "external_api_calls_disabled",
        "scraping_disabled",
        "publishing_disabled",
        "background_workers_disabled",
        "cron_disabled",
    ]:
        require_flag(section, flag)
    require_flag(section, "readiness_required", False)
    if "readiness_status_counts" not in section:
        raise AssertionError(f"Rollout readiness status counts missing: {section}")


def verify_endpoint_behavior() -> None:
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires seeded demo agency.")
    agency_id = agencies[0]["id"]
    bundles = get("/api/platform/feature-flag-bundles", OWNER_HEADERS).get("items") or []
    if not bundles:
        raise AssertionError("Smoke requires feature flag bundle metadata.")
    bundle_id = next((item["bundle_id"] for item in bundles if item.get("bundle_key") == "core_agency"), bundles[0]["bundle_id"])

    created = post(
        f"/api/platform/agencies/{agency_id}/bundle-assignments",
        {
            "bundle_id": bundle_id,
            "effective_date": "2026-07-05",
            "status": "assigned",
            "review_status": "pending_review",
            "notes": "Metadata-only rollout readiness smoke assignment.",
        },
        OWNER_HEADERS,
        201,
    )
    assignment_id = (created.get("assignment") or {}).get("assignment_id")
    if not assignment_id:
        raise AssertionError(f"Assignment was not created for rollout readiness smoke: {created}")

    platform_before_defaults = get("/api/platform/feature-bundle-rollout-readiness", OWNER_HEADERS)
    if platform_before_defaults.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Platform rollout readiness phase mismatch: {platform_before_defaults}")
    for flag in ["metadata_only", "feature_activation_disabled", "feature_access_enforcement_disabled", "billing_disabled", "provider_execution_disabled"]:
        require_flag(platform_before_defaults, flag)
    default_view = next((item for item in platform_before_defaults.get("items") or [] if item.get("assignment_id") == assignment_id), None)
    if not default_view or default_view.get("stored_record") is not False:
        raise AssertionError(f"Default rollout readiness view missing for assignment: {platform_before_defaults}")
    assert_readiness_shape(default_view)

    defaults = post("/api/platform/feature-bundle-rollout-readiness/defaults", {}, OWNER_HEADERS, 201)
    if defaults.get("metadata_only") is not True or defaults.get("created_count", 0) < 1:
        raise AssertionError(f"Default readiness record creation failed: {defaults}")

    platform_readiness = get("/api/platform/feature-bundle-rollout-readiness", OWNER_HEADERS)
    stored_view = next((item for item in platform_readiness.get("items") or [] if item.get("assignment_id") == assignment_id), None)
    if not stored_view or stored_view.get("stored_record") is not True:
        raise AssertionError(f"Stored rollout readiness view missing for assignment: {platform_readiness}")
    assert_readiness_shape(stored_view)
    if stored_view.get("readiness_status") not in {"draft", "reviewing", "ready", "blocked"}:
        raise AssertionError(f"Unexpected readiness status: {stored_view}")

    platform_summary = get("/api/platform/feature-bundle-rollout-readiness/summary", OWNER_HEADERS)
    if "by_readiness_status" not in (platform_summary.get("summary") or {}):
        raise AssertionError(f"Platform readiness summary malformed: {platform_summary}")

    agency_readiness = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-readiness", OWNER_HEADERS)
    if agency_readiness.get("read_only") is not True or agency_readiness.get("metadata_only") is not True:
        raise AssertionError(f"Agency rollout readiness should be read-only metadata: {agency_readiness}")
    agency_view = next((item for item in agency_readiness.get("items") or [] if item.get("assignment_id") == assignment_id), None)
    if not agency_view:
        raise AssertionError(f"Agency rollout readiness missing created assignment: {agency_readiness}")
    if agency_view.get("payloads_hidden") is not True:
        raise AssertionError(f"Agency rollout readiness should hide payload details: {agency_view}")
    assert_readiness_shape(agency_view)

    agency_summary = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-readiness/summary", OWNER_HEADERS)
    if agency_summary.get("read_only") is not True or "by_readiness_status" not in (agency_summary.get("summary") or {}):
        raise AssertionError(f"Agency readiness summary malformed: {agency_summary}")

    request("POST", f"/api/agencies/{agency_id}/feature-bundle-rollout-readiness", {"readiness_status": "ready"}, OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/feature-bundle-rollout-readiness", {"readiness_status": "ready"}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/feature-bundle-rollout-readiness", {}, OWNER_HEADERS, 405)


def assert_readiness_shape(item: dict) -> None:
    for key in ["agency_id", "bundle_id", "assignment_id", "readiness_status", "checklist_items", "checklist_counts", "warnings", "blockers"]:
        if key not in item:
            raise AssertionError(f"Readiness item missing {key}: {item}")
    if not item.get("checklist_items"):
        raise AssertionError(f"Readiness checklist metadata missing: {item}")
    for checklist_item in item["checklist_items"]:
        for key in ["item_key", "label", "status", "notes"]:
            if key not in checklist_item:
                raise AssertionError(f"Checklist item missing {key}: {checklist_item}")


def main() -> int:
    verify_model_and_collection_registration()
    verify_readiness()
    openapi = get("/openapi.json")
    paths = openapi.get("paths") or {}
    verify_routes(paths)
    verify_previous_phase_smoke_compatibility(paths)
    verify_frontend_and_docs()
    verify_endpoint_behavior()
    print("Phase 40.1 feature bundle rollout readiness foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Phase 40.1 feature bundle rollout readiness foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
