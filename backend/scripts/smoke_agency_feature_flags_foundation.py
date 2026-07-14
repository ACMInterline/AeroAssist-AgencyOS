#!/usr/bin/env python3
import sys
from pathlib import Path
from uuid import uuid4

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import AgencyFeatureFlag, AgencyFeatureFlagReview, AgencyFeatureFlagSnapshot
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, request


EXPECTED_PHASE = "phase_55_7_airline_fare_family_rbd_baggage_brand_intelligence_foundation"
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


def patch(path: str, body: dict | None = None, headers: dict | None = None, expect: int | None = None) -> dict:
    return request("PATCH", path, body or {}, headers, expect)[1]


def verify_model_and_collection_registration() -> None:
    for model in [AgencyFeatureFlag, AgencyFeatureFlagReview, AgencyFeatureFlagSnapshot]:
        if not hasattr(model, "model_fields"):
            raise AssertionError(f"Model import failed for {model}")
    for collection in ["agency_feature_flags", "agency_feature_flag_reviews", "agency_feature_flag_snapshots"]:
        if collection not in AGENCY_OWNED_COLLECTIONS:
            raise AssertionError(f"Feature flag collection not registered: {collection}")


def verify_routes(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
        if "feature-flags" in path and any(
            token in path
            for token in [
                "billing",
                "payment",
                "invoice",
                "settle",
                "stripe",
                "charge",
                "enforce",
                "block",
                "execute",
                "book",
                "pnr",
                "ticket",
                "emd",
                "publish",
                "scrape",
                "send",
            ]
        ):
            raise AssertionError(f"Execution or billing feature flag route introduced: {path}")
    for path, method in [
        ("/api/platform/feature-flags/summary", "get"),
        ("/api/platform/feature-flags/flags", "get"),
        ("/api/platform/feature-flags/flags", "post"),
        ("/api/platform/feature-flags/flags/{flag_id}", "patch"),
        ("/api/platform/feature-flags/reviews", "get"),
        ("/api/platform/feature-flags/reviews", "post"),
        ("/api/platform/feature-flags/snapshots", "get"),
        ("/api/platform/feature-flags/snapshots", "post"),
        ("/api/agencies/{agency_id}/feature-flags/summary", "get"),
        ("/api/agencies/{agency_id}/feature-flags/flags", "get"),
        ("/api/agencies/{agency_id}/feature-flags/reviews", "get"),
    ]:
        assert_openapi_path(paths, path, method)


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
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Feature Availability"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "featureFlagLabels"),
        (ROOT / "frontend/src/pages/platform/FeatureFlagsPage.jsx", "Feature visibility is informational only. Operational enforcement is not performed."),
        (ROOT / "frontend/src/pages/agency/FeatureAvailabilityPage.jsx", "Feature visibility is informational only. Operational enforcement is not performed."),
        (ROOT / "frontend/src/App.jsx", "/platform/feature-flags"),
        (ROOT / "frontend/src/App.jsx", "/agency/feature-availability"),
        (ROOT / "docs/architecture/agency-feature-flags-foundation.md", "Agency Feature Flags Foundation"),
        (ROOT / "README.md", "Phase 39.7 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 39.7: Agency Feature Flags Foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "Phase 39.7 adds agency feature flag metadata"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Agency feature flags"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Agency feature flags"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/FeatureFlagsPage.jsx",
        ROOT / "frontend/src/pages/agency/FeatureAvailabilityPage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)


def main() -> int:
    verify_model_and_collection_registration()
    run_key = uuid4().hex[:10]

    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")

    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("agency_feature_flags_foundation") or {}
    for flag in [
        "feature_flags_enabled",
        "review_notes_enabled",
        "snapshots_enabled",
        "platform_review_enabled",
        "agency_read_only_visibility_enabled",
    ]:
        require_flag(section, flag)
    for flag in [
        "automatic_enforcement_disabled",
        "billing_disabled",
        "payments_disabled",
        "provider_execution_disabled",
        "booking_execution_disabled",
        "pnr_mutation_disabled",
        "ticketing_disabled",
        "emd_issuance_disabled",
        "cms_publishing_disabled",
        "client_portal_publishing_disabled",
        "external_api_calls_disabled",
        "external_ai_disabled",
        "scraping_disabled",
        "automatic_sending_disabled",
        "feature_blocking_disabled",
    ]:
        require_flag(section, flag)
    for flag in ["automatic_enforcement_enabled", "billing_enabled", "payments_enabled", "provider_execution_enabled"]:
        require_flag(section, flag, False)
    require_flag(section, "readiness_required", False)

    openapi = get("/openapi.json")
    verify_routes(openapi.get("paths") or {})
    verify_route_policy()
    verify_frontend_and_docs()

    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires seeded demo agency.")
    agency_id = agencies[0]["id"]
    feature_key = f"smoke_feature_{run_key}"

    created = post(
        "/api/platform/feature-flags/flags",
        {
            "agency_id": agency_id,
            "module_key": "requests",
            "feature_key": feature_key,
            "display_name": "Smoke Feature Visibility",
            "state": "beta",
            "visibility_note": "Metadata-only smoke feature flag. No operational enforcement is performed.",
        },
        OWNER_HEADERS,
        201,
    )
    flag = created.get("flag") or {}
    if flag.get("state") != "beta" or flag.get("badge") != "Beta":
        raise AssertionError(f"Feature flag was not created as beta metadata: {flag}")
    for safety_flag in ["automatic_enforcement_disabled", "billing_disabled", "provider_execution_disabled", "feature_blocking_disabled"]:
        require_flag(created, safety_flag)

    updated = patch(
        f"/api/platform/feature-flags/flags/{flag['id']}",
        {
            "state": "pilot",
            "visibility_note": "Pilot visibility metadata only.",
        },
        OWNER_HEADERS,
    )
    if (updated.get("flag") or {}).get("state") != "pilot":
        raise AssertionError(f"Feature flag update did not preserve metadata-only pilot state: {updated}")

    review = post(
        "/api/platform/feature-flags/reviews",
        {
            "agency_id": agency_id,
            "notes": "Smoke review note for feature visibility metadata only.",
        },
        OWNER_HEADERS,
        201,
    )
    if (review.get("review") or {}).get("metadata_only") is not True:
        raise AssertionError(f"Review note is not metadata-only: {review}")

    snapshot = post(
        "/api/platform/feature-flags/snapshots",
        {
            "agency_id": agency_id,
            "immutable_json": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    if (snapshot.get("snapshot") or {}).get("immutable") is not True:
        raise AssertionError(f"Snapshot is not immutable metadata: {snapshot}")

    platform_summary = get("/api/platform/feature-flags/summary", OWNER_HEADERS)
    if platform_summary.get("phase") != EXPECTED_PHASE or platform_summary.get("metadata_only") is not True:
        raise AssertionError(f"Platform summary is not metadata-only 39.7 data: {platform_summary}")
    if (platform_summary.get("state_counts") or {}).get("pilot", 0) < 1:
        raise AssertionError(f"Platform summary did not count pilot flag: {platform_summary}")

    agency_summary = get(f"/api/agencies/{agency_id}/feature-flags/summary", OWNER_HEADERS)
    if agency_summary.get("phase") != EXPECTED_PHASE or agency_summary.get("read_only") is not True:
        raise AssertionError(f"Agency summary is not read-only metadata: {agency_summary}")
    for safety_flag in ["automatic_enforcement_disabled", "billing_disabled", "provider_execution_disabled", "feature_blocking_disabled"]:
        require_flag(agency_summary, safety_flag)

    agency_flags = get(f"/api/agencies/{agency_id}/feature-flags/flags", OWNER_HEADERS)
    smoke_item = next((item for item in agency_flags.get("items") or [] if item.get("feature_key") == feature_key), None)
    if not smoke_item or smoke_item.get("read_only") is not True or smoke_item.get("state") != "pilot":
        raise AssertionError(f"Agency read-only flags did not include pilot smoke flag: {agency_flags}")
    agency_reviews = get(f"/api/agencies/{agency_id}/feature-flags/reviews", OWNER_HEADERS)
    if agency_reviews.get("read_only") is not True:
        raise AssertionError(f"Agency reviews endpoint should be read-only: {agency_reviews}")
    request("POST", f"/api/agencies/{agency_id}/feature-flags/flags", {"state": "enabled"}, OWNER_HEADERS, 405)

    final_readiness = get("/api/readiness")
    final_section = final_readiness.get("agency_feature_flags_foundation") or {}
    if final_section.get("flag_count", 0) < section.get("flag_count", 0) + 1:
        raise AssertionError("Readiness flag count did not reflect feature flag metadata creation.")
    print("Phase 39.7 agency feature flags foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Agency feature flags foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
