#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import BundleReadiness, FeatureFlagBundle, FeatureFlagBundleMember, FeatureFlagBundleReview, FeatureFlagBundleSummary
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, request


EXPECTED_PHASE = "phase_40_13_feature_bundle_rollout_summary_pack_foundation"
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
    member = FeatureFlagBundleMember(module_key="settings", feature_key="feature_bundles", display_name="Feature Bundles")
    readiness = BundleReadiness(documentation_complete=True)
    bundle = FeatureFlagBundle(
        bundle_key="smoke_bundle",
        bundle_name="Smoke Bundle",
        members=[member],
        readiness=readiness,
    )
    summary = FeatureFlagBundleSummary(
        bundle_id=bundle.id,
        bundle_key=bundle.bundle_key,
        bundle_name=bundle.bundle_name,
        flag_count=1,
        readiness=readiness,
    )
    review = FeatureFlagBundleReview(bundle_id=bundle.id, bundle_key=bundle.bundle_key, review_status="draft")
    for model in [member, readiness, bundle, summary, review]:
        if model.model_dump(mode="json").get("metadata_only") is not True:
            raise AssertionError(f"Bundle model is not metadata-only by default: {model}")
    for collection in ["agency_feature_flag_bundles", "agency_feature_flag_bundle_reviews"]:
        if collection not in AGENCY_OWNED_COLLECTIONS:
            raise AssertionError(f"Feature flag bundle collection not registered: {collection}")
    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "agency_feature_flag_bundles_key_lookup",
        "agency_feature_flag_bundles_category_status_lookup",
        "agency_feature_flag_bundle_reviews_key_created_lookup",
        "agency_feature_flag_bundle_reviews_status_created_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Feature flag bundle index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    read_only_routes = [
        "/api/platform/feature-flag-bundles",
        "/api/platform/feature-flag-bundles/{bundle_id}",
        "/api/platform/feature-flag-bundles/{bundle_id}/members",
        "/api/platform/feature-flag-bundles/reviews",
        "/api/agencies/{agency_id}/feature-flag-bundles",
        "/api/agencies/{agency_id}/feature-flag-bundles/{bundle_id}",
    ]
    for path in read_only_routes:
        assert_openapi_path(paths, path, "get")
        methods = set(paths.get(path, {}).keys())
        blocked_methods = methods & {"post", "patch", "put", "delete"}
        if blocked_methods:
            raise AssertionError(f"Read-only feature bundle route exposes write methods: {path} {sorted(blocked_methods)}")


def verify_route_policy() -> None:
    route_policy = get("/api/platform/blueprint/route-policy", OWNER_HEADERS)
    if route_policy.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected route policy phase: {route_policy.get('phase')}")
    canonical_roots = {item.get("root") for item in route_policy.get("canonical_routes") or []}
    rejected_roots = {item.get("root") for item in route_policy.get("rejected_routes") or []}
    for root in ["/platform/*", "/agency/*", "/api/platform/*", "/api/agencies/{agency_id}/*"]:
        if root not in canonical_roots:
            raise AssertionError(f"Canonical route root missing: {root}")
    for root in ["/agent/*", "/admin/*"]:
        if root not in rejected_roots:
            raise AssertionError(f"Rejected route root missing: {root}")
    if route_policy.get("aliases_added") is not False:
        raise AssertionError("Route policy should not add admin/agent aliases.")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Feature Flag Bundles"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Feature Bundles"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "metadata_only: true"),
        (ROOT / "frontend/src/App.jsx", "/platform/feature-flag-bundles"),
        (ROOT / "frontend/src/App.jsx", "/agency/feature-bundles"),
        (ROOT / "frontend/src/pages/platform/FeatureFlagBundlesPage.jsx", "Feature Flag Bundles"),
        (ROOT / "frontend/src/pages/agency/FeatureBundlesPage.jsx", "Available Feature Bundles"),
        (ROOT / "docs/architecture/agency-feature-flag-bundle-foundation.md", "Agency Feature Flag Bundle Foundation"),
        (ROOT / "README.md", "Phase 39.9 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 39.9: Feature Flag Bundles Foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "Phase 39.9 adds reusable feature flag bundle metadata"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "Phase 39.9 adds read-only feature flag bundle APIs"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Feature flag bundles"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Feature flag bundles"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/FeatureFlagBundlesPage.jsx",
        ROOT / "frontend/src/pages/agency/FeatureBundlesPage.jsx",
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
    section = readiness.get("feature_flag_bundle_foundation") or {}
    for flag in [
        "feature_flag_bundles_enabled",
        "feature_flag_bundle_reviews_enabled",
        "feature_flag_bundle_members_enabled",
        "bundle_readiness_enabled",
        "platform_bundle_read_only_enabled",
        "agency_bundle_read_only_enabled",
        "metadata_only",
    ]:
        require_flag(section, flag)
    for flag in [
        "runtime_feature_enforcement_disabled",
        "entitlement_checks_disabled",
        "billing_disabled",
        "execution_logic_disabled",
        "module_hiding_disabled",
        "permission_decisions_disabled",
        "publishing_disabled",
        "rollout_disabled",
        "percentage_deployments_disabled",
        "provider_integrations_disabled",
        "external_ai_disabled",
        "scraping_disabled",
        "background_workers_disabled",
        "notifications_disabled",
        "email_sending_disabled",
        "api_integrations_disabled",
        "external_api_calls_disabled",
    ]:
        require_flag(section, flag)
    require_flag(section, "readiness_required", False)
    if section.get("default_bundle_count", 0) < 10:
        raise AssertionError(f"Expected default bundle metadata count, got {section.get('default_bundle_count')}")


def verify_endpoint_behavior() -> None:
    platform_bundles = get("/api/platform/feature-flag-bundles", OWNER_HEADERS)
    if platform_bundles.get("phase") != EXPECTED_PHASE or platform_bundles.get("read_only") is not True:
        raise AssertionError(f"Platform bundle response is not read-only 39.9 metadata: {platform_bundles}")
    for flag in ["metadata_only", "runtime_feature_enforcement_disabled", "entitlement_checks_disabled", "billing_disabled", "rollout_disabled", "provider_integrations_disabled", "background_workers_disabled", "notifications_disabled"]:
        require_flag(platform_bundles, flag)
    if platform_bundles.get("bundle_count", 0) < 10:
        raise AssertionError(f"Expected default platform bundles, got: {platform_bundles}")
    bundle_keys = {item.get("bundle_key") for item in platform_bundles.get("items") or []}
    for bundle_key in ["core_agency", "crm", "ticketing", "booking", "airline_intelligence", "gds", "finance", "premium_operations", "beta_features", "internal_testing"]:
        if bundle_key not in bundle_keys:
            raise AssertionError(f"Default bundle missing: {bundle_key}")
    first_bundle = platform_bundles["items"][0]
    bundle_id = first_bundle["bundle_id"]
    detail = get(f"/api/platform/feature-flag-bundles/{bundle_id}", OWNER_HEADERS)
    if not detail.get("bundle") or detail["bundle"].get("metadata_only") is not True:
        raise AssertionError(f"Platform bundle detail missing metadata: {detail}")
    members = get(f"/api/platform/feature-flag-bundles/{bundle_id}/members", OWNER_HEADERS)
    if members.get("member_count", 0) < 1 or members.get("read_only") is not True:
        raise AssertionError(f"Platform bundle members missing: {members}")
    reviews = get("/api/platform/feature-flag-bundles/reviews", OWNER_HEADERS)
    if reviews.get("phase") != EXPECTED_PHASE or reviews.get("read_only") is not True:
        raise AssertionError(f"Platform bundle reviews response is not read-only: {reviews}")

    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires seeded demo agency.")
    agency_id = agencies[0]["id"]
    agency_bundles = get(f"/api/agencies/{agency_id}/feature-flag-bundles", OWNER_HEADERS)
    if agency_bundles.get("phase") != EXPECTED_PHASE or agency_bundles.get("agency_id") != agency_id:
        raise AssertionError(f"Agency bundle response is not scoped to agency: {agency_bundles}")
    if agency_bundles.get("read_only") is not True or agency_bundles.get("metadata_only") is not True:
        raise AssertionError(f"Agency bundle response should be read-only metadata: {agency_bundles}")
    agency_keys = {item.get("bundle_key") for item in agency_bundles.get("items") or []}
    if "internal_testing" in agency_keys:
        raise AssertionError("Internal testing bundle should not be agency-visible by default.")
    if "core_agency" not in agency_keys:
        raise AssertionError(f"Agency bundle defaults missing core agency: {agency_bundles}")
    agency_bundle_id = (agency_bundles.get("items") or [])[0]["bundle_id"]
    agency_detail = get(f"/api/agencies/{agency_id}/feature-flag-bundles/{agency_bundle_id}", OWNER_HEADERS)
    if not agency_detail.get("bundle") or agency_detail["bundle"].get("agency_id") != agency_id:
        raise AssertionError(f"Agency bundle detail missing agency scoped metadata: {agency_detail}")
    if agency_detail["bundle"].get("payloads_hidden") is not True:
        raise AssertionError(f"Agency bundle detail should hide payloads: {agency_detail}")

    request("POST", "/api/platform/feature-flag-bundles", {"bundle_key": "blocked"}, OWNER_HEADERS, 405)
    request("PATCH", f"/api/platform/feature-flag-bundles/{bundle_id}", {"review_status": "approved"}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/platform/feature-flag-bundles/{bundle_id}", {}, OWNER_HEADERS, 405)
    request("POST", f"/api/agencies/{agency_id}/feature-flag-bundles", {"bundle_key": "blocked"}, OWNER_HEADERS, 405)
    request("PATCH", f"/api/agencies/{agency_id}/feature-flag-bundles/{agency_bundle_id}", {"review_status": "approved"}, OWNER_HEADERS, 405)


def main() -> int:
    verify_model_and_collection_registration()
    verify_readiness()
    openapi = get("/openapi.json")
    verify_routes(openapi.get("paths") or {})
    verify_route_policy()
    verify_frontend_and_docs()
    verify_endpoint_behavior()
    print("Phase 39.9 agency feature flag bundle foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Phase 39.9 agency feature flag bundle foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
