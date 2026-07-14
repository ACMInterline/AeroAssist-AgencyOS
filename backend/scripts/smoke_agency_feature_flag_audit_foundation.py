#!/usr/bin/env python3
import sys
from pathlib import Path
from uuid import uuid4

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import AgencyFeatureFlagAudit, AgencyFeatureFlagReadiness
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, request


EXPECTED_PHASE = "phase_54_6_offer_to_booking_handoff_readiness_foundation"
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
    for model in [AgencyFeatureFlagAudit, AgencyFeatureFlagReadiness]:
        if not hasattr(model, "model_fields"):
            raise AssertionError(f"Model import failed for {model}")
    for collection in ["agency_feature_flag_audits", "agency_feature_flag_readiness"]:
        if collection not in AGENCY_OWNED_COLLECTIONS:
            raise AssertionError(f"Feature flag audit collection not registered: {collection}")


def verify_routes(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    read_only_routes = [
        "/api/platform/feature-flags/audits",
        "/api/platform/feature-flags/readiness",
        "/api/platform/feature-flags/readiness/{feature_key}",
        "/api/agencies/{agency_id}/feature-readiness",
        "/api/agencies/{agency_id}/feature-readiness/{feature_key}",
    ]
    for path in read_only_routes:
        assert_openapi_path(paths, path, "get")
        methods = set(paths.get(path, {}).keys())
        blocked_methods = methods & {"post", "patch", "put", "delete"}
        if blocked_methods:
            raise AssertionError(f"Read-only feature audit route exposes write methods: {path} {sorted(blocked_methods)}")


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
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Feature Flag Audit"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Feature Readiness"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "metadata_only: true"),
        (ROOT / "frontend/src/App.jsx", "/platform/feature-flag-audit"),
        (ROOT / "frontend/src/App.jsx", "/agency/feature-readiness"),
        (ROOT / "frontend/src/pages/platform/FeatureFlagAuditPage.jsx", "Audit History"),
        (ROOT / "frontend/src/pages/agency/FeatureReadinessPage.jsx", "Readiness checklist"),
        (ROOT / "docs/architecture/agency-feature-flag-audit-foundation.md", "Agency Feature Flag Readiness & Audit Foundation"),
        (ROOT / "README.md", "Phase 39.8 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 39.8: Agency Feature Flag Readiness And Audit Foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "Phase 39.8 adds feature flag audit history"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Agency feature flag readiness and audit"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Agency feature flag audit"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/FeatureFlagAuditPage.jsx",
        ROOT / "frontend/src/pages/agency/FeatureReadinessPage.jsx",
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
    section = readiness.get("feature_flag_audit_foundation") or {}
    for flag in [
        "feature_flag_audits_enabled",
        "feature_flag_readiness_enabled",
        "audit_history_enabled",
        "readiness_checklist_enabled",
        "platform_read_only_audit_enabled",
        "agency_read_only_readiness_enabled",
        "metadata_only",
    ]:
        require_flag(section, flag)
    for flag in [
        "automatic_enforcement_disabled",
        "route_blocking_disabled",
        "permission_changes_disabled",
        "subscription_changes_disabled",
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
    require_flag(section, "operational_enforcement_enabled", False)
    require_flag(section, "readiness_required", False)

    openapi = get("/openapi.json")
    verify_routes(openapi.get("paths") or {})
    verify_route_policy()
    verify_frontend_and_docs()

    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires seeded demo agency.")
    agency_id = agencies[0]["id"]
    feature_key = f"audit_smoke_{run_key}"

    created = post(
        "/api/platform/feature-flags/flags",
        {
            "agency_id": agency_id,
            "module_key": "settings",
            "feature_key": feature_key,
            "display_name": "Smoke Audit Feature",
            "state": "pilot",
            "visibility_note": "Metadata-only audit smoke.",
        },
        OWNER_HEADERS,
        201,
    )
    flag_id = created["flag"]["id"]
    patch(
        f"/api/platform/feature-flags/flags/{flag_id}",
        {
            "state": "beta",
            "visibility_note": "Metadata-only audit update.",
        },
        OWNER_HEADERS,
    )

    audit_response = get(f"/api/platform/feature-flags/audits?agency_id={agency_id}&feature_key={feature_key}", OWNER_HEADERS)
    if audit_response.get("phase") != EXPECTED_PHASE or audit_response.get("read_only") is not True:
        raise AssertionError(f"Audit response is not read-only 39.8 metadata: {audit_response}")
    if audit_response.get("audit_count", 0) < 2:
        raise AssertionError(f"Expected create/update audit history, got: {audit_response}")
    latest_audit = audit_response["items"][0]
    if latest_audit.get("proposed_state") != "beta" or latest_audit.get("previous_state") != "pilot":
        raise AssertionError(f"Latest audit state transition incorrect: {latest_audit}")
    for key in ["metadata", "changed_by", "changed_at", "reason", "notes"]:
        if key not in latest_audit:
            raise AssertionError(f"Audit item missing metadata key {key}: {latest_audit}")

    platform_readiness = get(f"/api/platform/feature-flags/readiness/{feature_key}?agency_id={agency_id}", OWNER_HEADERS)
    if platform_readiness.get("phase") != EXPECTED_PHASE or platform_readiness.get("read_only") is not True:
        raise AssertionError(f"Platform readiness response is not read-only 39.8 metadata: {platform_readiness}")
    if platform_readiness.get("readiness_count") != 1:
        raise AssertionError(f"Expected one platform readiness record for smoke feature: {platform_readiness}")
    readiness_item = platform_readiness["items"][0]
    for key in ["documentation_complete", "backend_complete", "api_complete", "ui_complete", "testing_complete", "deployment_ready", "rollout_ready"]:
        if key not in readiness_item:
            raise AssertionError(f"Readiness item missing checklist key {key}: {readiness_item}")
    if readiness_item.get("rollout_ready") is not False:
        raise AssertionError(f"Default readiness should not mark rollout ready: {readiness_item}")

    agency_readiness = get(f"/api/agencies/{agency_id}/feature-readiness/{feature_key}", OWNER_HEADERS)
    if agency_readiness.get("phase") != EXPECTED_PHASE or agency_readiness.get("read_only") is not True:
        raise AssertionError(f"Agency readiness response is not read-only 39.8 metadata: {agency_readiness}")
    if not agency_readiness.get("item") or agency_readiness["item"].get("agency_id") != agency_id:
        raise AssertionError(f"Agency readiness did not scope to requested agency: {agency_readiness}")
    if set(agency_readiness.get("readiness_checklist_keys") or []) != {
        "documentation_complete",
        "backend_complete",
        "api_complete",
        "ui_complete",
        "testing_complete",
        "deployment_ready",
        "rollout_ready",
    }:
        raise AssertionError(f"Unexpected checklist keys: {agency_readiness.get('readiness_checklist_keys')}")
    for flag in ["automatic_enforcement_disabled", "route_blocking_disabled", "subscription_changes_disabled", "billing_disabled", "provider_execution_disabled"]:
        require_flag(agency_readiness, flag)

    request("POST", "/api/platform/feature-flags/audits", {"feature_key": feature_key}, OWNER_HEADERS, 405)
    request("PATCH", f"/api/platform/feature-flags/readiness/{feature_key}", {"rollout_ready": True}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/platform/feature-flags/readiness/{feature_key}", {}, OWNER_HEADERS, 405)
    request("POST", f"/api/agencies/{agency_id}/feature-readiness", {"feature_key": feature_key}, OWNER_HEADERS, 405)
    request("PATCH", f"/api/agencies/{agency_id}/feature-readiness/{feature_key}", {"rollout_ready": True}, OWNER_HEADERS, 405)

    final_readiness = get("/api/readiness")
    final_section = final_readiness.get("feature_flag_audit_foundation") or {}
    if final_section.get("audit_count", 0) < section.get("audit_count", 0) + 2:
        raise AssertionError("Readiness audit count did not reflect feature flag audit history.")
    if final_section.get("readiness_count", 0) < section.get("readiness_count", 0) + 1:
        raise AssertionError("Readiness count did not reflect feature flag readiness metadata.")

    print("Phase 39.8 agency feature flag audit foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Agency feature flag audit foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
