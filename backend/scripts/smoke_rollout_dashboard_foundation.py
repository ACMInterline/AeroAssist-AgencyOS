#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import (
    RolloutDashboardCounts,
    RolloutDashboardFilters,
    RolloutDashboardSection,
    RolloutDashboardSnapshot,
    RolloutDashboardSummary,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, request


EXPECTED_PHASE = "phase_50_0_airline_operational_intelligence_engine_architecture_foundation"
ROOT = Path(__file__).resolve().parents[2]
EXPECTED_SECTIONS = {
    "capability_catalog",
    "feature_flags",
    "feature_bundles",
    "assigned_bundles",
    "rollout_readiness",
    "rollout_plans",
}


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


def disabled_flags() -> list[str]:
    return [
        "automation_disabled",
        "rollout_automation_disabled",
        "rollout_execution_disabled",
        "execution_engines_disabled",
        "feature_activation_disabled",
        "permission_enforcement_disabled",
        "feature_access_enforcement_disabled",
        "route_blocking_disabled",
        "billing_disabled",
        "payments_disabled",
        "provider_execution_disabled",
        "external_api_calls_disabled",
        "ai_execution_disabled",
        "scraping_disabled",
        "publishing_disabled",
        "background_workers_disabled",
        "schedulers_disabled",
        "cron_disabled",
        "webhook_execution_disabled",
        "email_sending_disabled",
        "sms_sending_disabled",
    ]


def assert_disabled_response(payload: dict) -> None:
    for flag in disabled_flags():
        if payload.get(flag) is not True:
            raise AssertionError(f"Payload missing disabled flag {flag}: {payload}")
    for flag in [
        "automation_enabled",
        "rollout_execution_enabled",
        "execution_engines_enabled",
        "feature_activation_enabled",
        "permission_enforcement_enabled",
        "feature_access_enforcement_enabled",
        "route_blocking_enabled",
        "billing_enabled",
        "payments_enabled",
        "provider_execution_enabled",
        "external_api_calls_enabled",
        "ai_execution_enabled",
        "scraping_enabled",
        "publishing_enabled",
        "background_workers_enabled",
        "schedulers_enabled",
        "webhook_execution_enabled",
        "email_sending_enabled",
        "sms_sending_enabled",
    ]:
        if payload.get(flag) is True:
            raise AssertionError(f"Payload exposes forbidden enabled flag {flag}: {payload}")


def verify_model_and_collection_registration() -> None:
    counts = RolloutDashboardCounts(
        total_count=3,
        by_status={"ready": 1, "blocked": 1},
        by_stage={"draft": 1},
        warning_count=1,
        blocker_count=1,
    )
    section = RolloutDashboardSection(
        section_key="rollout_plans",
        title="Rollout Plans",
        description="Smoke dashboard section.",
        count=3,
        counts=counts,
        statuses={"draft": 1},
        route="/platform/feature-bundle-rollout-plans",
    )
    filters = RolloutDashboardFilters(
        agency_id="agency-smoke",
        bundle_id="bundle-smoke",
        readiness_status="reviewing",
        rollout_stage="draft",
    )
    summary = RolloutDashboardSummary(agency_id="agency-smoke", sections=[section], counts=counts, filters=filters)
    snapshot = RolloutDashboardSnapshot(
        agency_id="agency-smoke",
        filters=filters,
        sections=[section],
        counts=counts,
        captured_by="smoke",
    )
    dumped_summary = summary.model_dump(mode="json")
    dumped_snapshot = snapshot.model_dump(mode="json")
    if dumped_summary.get("read_only") is not True or dumped_summary.get("metadata_only") is not True:
        raise AssertionError(f"Dashboard summary model is not read-only metadata: {dumped_summary}")
    if dumped_snapshot.get("metadata_only") is not True or dumped_snapshot.get("read_only") is not True:
        raise AssertionError(f"Dashboard snapshot model is not read-only metadata: {dumped_snapshot}")
    for flag in [
        "automation_disabled",
        "rollout_execution_disabled",
        "feature_activation_disabled",
        "billing_disabled",
        "provider_execution_disabled",
    ]:
        if dumped_snapshot.get(flag) is not True:
            raise AssertionError(f"Dashboard snapshot model missing disabled flag {flag}: {dumped_snapshot}")
    if dumped_summary["sections"][0].get("section_key") != "rollout_plans":
        raise AssertionError(f"Dashboard section key was not preserved: {dumped_summary}")
    for collection in ["rollout_dashboard_views", "rollout_dashboard_snapshots"]:
        if collection not in AGENCY_OWNED_COLLECTIONS:
            raise AssertionError(f"Rollout dashboard collection is not registered: {collection}")
    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "rollout_dashboard_views_id_unique",
        "rollout_dashboard_views_agency_lookup",
        "rollout_dashboard_views_view_agency_lookup",
        "rollout_dashboard_snapshots_id_unique",
        "rollout_dashboard_snapshots_snapshot_unique",
        "rollout_dashboard_snapshots_agency_captured_lookup",
        "rollout_dashboard_snapshots_source_captured_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Rollout dashboard index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    expected_methods = {
        "/api/platform/rollout-dashboard": {"get"},
        "/api/platform/rollout-dashboard/summary": {"get"},
        "/api/platform/rollout-dashboard/snapshots": {"get"},
        "/api/platform/rollout-dashboard/filters": {"get"},
        "/api/agencies/{agency_id}/rollout-dashboard": {"get"},
        "/api/agencies/{agency_id}/rollout-dashboard/summary": {"get"},
        "/api/agencies/{agency_id}/rollout-dashboard/snapshots": {"get"},
    }
    for path, methods in expected_methods.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
        blocked_methods = set(paths.get(path, {}).keys()) & {"post", "put", "patch", "delete"}
        if blocked_methods:
            raise AssertionError(f"Rollout dashboard route is not read-only: {path} {sorted(blocked_methods)}")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Rollout Dashboard"),
        (ROOT / "frontend/src/App.jsx", "/platform/rollout-dashboard"),
        (ROOT / "frontend/src/App.jsx", "/agency/rollout-dashboard"),
        (ROOT / "frontend/src/pages/platform/RolloutDashboardPage.jsx", "Rollout Dashboard"),
        (ROOT / "frontend/src/pages/platform/RolloutDashboardPage.jsx", "No activation, automation, billing, publishing, provider execution, AI, route blocking, email, or SMS occurs."),
        (ROOT / "frontend/src/pages/agency/RolloutDashboardPage.jsx", "Rollout Dashboard"),
        (ROOT / "frontend/src/pages/agency/RolloutDashboardPage.jsx", "does not activate features, enforce access, bill, publish, send, schedule, execute providers, use AI, or block routes"),
        (ROOT / "docs/architecture/rollout-dashboard-foundation.md", "Rollout Dashboard Foundation"),
        (ROOT / "README.md", "Phase 40.3 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 40.3: Agency Capability Rollout Dashboard Foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "Phase 40.3 adds read-only rollout dashboard metadata aggregation"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "Phase 40.3 adds read-only rollout dashboard APIs"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Rollout dashboard"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Rollout dashboard"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/RolloutDashboardPage.jsx",
        ROOT / "frontend/src/pages/agency/RolloutDashboardPage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)
    for path in [
        ROOT / "frontend/src/pages/platform/RolloutDashboardPage.jsx",
        ROOT / "frontend/src/pages/agency/RolloutDashboardPage.jsx",
    ]:
        reject_text(path, "<button")
        reject_text(path, "onClick=")


def verify_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")
    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("rollout_dashboard_foundation") or {}
    for flag in [
        "rollout_dashboard_enabled",
        "platform_rollout_dashboard_enabled",
        "agency_rollout_dashboard_enabled",
        "rollout_dashboard_summary_enabled",
        "rollout_dashboard_filters_enabled",
        "rollout_dashboard_snapshots_read_only_enabled",
        "capability_catalog_section_enabled",
        "feature_flags_section_enabled",
        "feature_bundles_section_enabled",
        "assigned_bundles_section_enabled",
        "rollout_readiness_section_enabled",
        "rollout_plans_section_enabled",
        "metadata_only",
        "read_only",
    ]:
        require_flag(section, flag)
    for flag in disabled_flags():
        require_flag(section, flag)
    require_flag(section, "readiness_required", False)
    if section.get("dashboard_section_count") != len(EXPECTED_SECTIONS):
        raise AssertionError(f"Unexpected dashboard section count: {section}")
    for count_key in ["rollout_dashboard_view_count", "rollout_dashboard_snapshot_count"]:
        if count_key not in section:
            raise AssertionError(f"Rollout dashboard readiness missing count: {count_key}")
    previous_section = readiness.get("feature_bundle_rollout_plan_foundation") or {}
    if previous_section.get("metadata_only") is not True:
        raise AssertionError("Previous rollout plan section should remain metadata-only.")


def verify_endpoint_behavior() -> None:
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires seeded demo agency.")
    agency_id = agencies[0]["id"]

    platform_dashboard = get("/api/platform/rollout-dashboard", OWNER_HEADERS)
    assert_dashboard_response(platform_dashboard, agency_id=None)

    platform_summary = get("/api/platform/rollout-dashboard/summary", OWNER_HEADERS)
    assert_summary_response(platform_summary)

    filters = get("/api/platform/rollout-dashboard/filters", OWNER_HEADERS)
    if filters.get("metadata_only") is not True or filters.get("read_only") is not True:
        raise AssertionError(f"Platform dashboard filters should be read-only metadata: {filters}")
    assert_disabled_response(filters)
    filter_payload = filters.get("filters") or {}
    for key in ["agencies", "bundle_ids", "feature_states", "readiness_statuses", "rollout_stages", "sections"]:
        if key not in filter_payload:
            raise AssertionError(f"Platform dashboard filters missing {key}: {filters}")
    if set(filter_payload.get("sections") or []) != EXPECTED_SECTIONS:
        raise AssertionError(f"Dashboard filter sections mismatch: {filters}")

    platform_snapshots = get("/api/platform/rollout-dashboard/snapshots", OWNER_HEADERS)
    assert_snapshot_response(platform_snapshots)

    agency_dashboard = get(f"/api/agencies/{agency_id}/rollout-dashboard", OWNER_HEADERS)
    assert_dashboard_response(agency_dashboard, agency_id=agency_id)

    agency_summary = get(f"/api/agencies/{agency_id}/rollout-dashboard/summary", OWNER_HEADERS)
    assert_summary_response(agency_summary, agency_id=agency_id)

    agency_snapshots = get(f"/api/agencies/{agency_id}/rollout-dashboard/snapshots", OWNER_HEADERS)
    assert_snapshot_response(agency_snapshots, agency_id=agency_id)

    request("POST", "/api/platform/rollout-dashboard", {}, OWNER_HEADERS, 405)
    request("PUT", "/api/platform/rollout-dashboard", {}, OWNER_HEADERS, 405)
    request("DELETE", "/api/platform/rollout-dashboard", {}, OWNER_HEADERS, 405)
    request("POST", f"/api/agencies/{agency_id}/rollout-dashboard", {}, OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/rollout-dashboard", {}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/rollout-dashboard", {}, OWNER_HEADERS, 405)


def assert_dashboard_response(payload: dict, *, agency_id: str | None) -> None:
    if payload.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected dashboard phase: {payload}")
    if agency_id is not None and payload.get("agency_id") != agency_id:
        raise AssertionError(f"Agency dashboard did not stay agency-scoped: {payload}")
    if payload.get("read_only") is not True or payload.get("metadata_only") is not True:
        raise AssertionError(f"Dashboard response should be read-only metadata: {payload}")
    assert_disabled_response(payload)
    sections = payload.get("sections") or []
    if {section.get("section_key") for section in sections} != EXPECTED_SECTIONS:
        raise AssertionError(f"Dashboard sections mismatch: {payload}")
    for section in sections:
        assert_section_shape(section)
    counts = payload.get("counts") or {}
    if "total_count" not in counts or "by_status" not in counts:
        raise AssertionError(f"Dashboard counts malformed: {payload}")
    summary = payload.get("summary") or {}
    if "sections" not in summary or "counts" not in summary or "generated_at" not in summary:
        raise AssertionError(f"Dashboard summary malformed: {payload}")


def assert_summary_response(payload: dict, *, agency_id: str | None = None) -> None:
    if payload.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected dashboard summary phase: {payload}")
    if agency_id is not None and payload.get("agency_id") != agency_id:
        raise AssertionError(f"Agency dashboard summary did not stay agency-scoped: {payload}")
    if payload.get("section_count") != len(EXPECTED_SECTIONS):
        raise AssertionError(f"Dashboard summary section count mismatch: {payload}")
    if payload.get("read_only") is not True or payload.get("metadata_only") is not True:
        raise AssertionError(f"Dashboard summary should be read-only metadata: {payload}")
    assert_disabled_response(payload)
    summary = payload.get("summary") or {}
    counts = payload.get("counts") or {}
    if "sections" not in summary or "counts" not in summary or "total_count" not in counts:
        raise AssertionError(f"Dashboard summary shape malformed: {payload}")


def assert_snapshot_response(payload: dict, *, agency_id: str | None = None) -> None:
    if payload.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected dashboard snapshot phase: {payload}")
    if agency_id is not None and payload.get("agency_id") != agency_id:
        raise AssertionError(f"Agency dashboard snapshots did not stay agency-scoped: {payload}")
    if payload.get("read_only") is not True or payload.get("metadata_only") is not True:
        raise AssertionError(f"Dashboard snapshots should be read-only metadata: {payload}")
    assert_disabled_response(payload)
    if not isinstance(payload.get("items"), list) or "snapshot_count" not in payload:
        raise AssertionError(f"Dashboard snapshot shape malformed: {payload}")
    for item in payload.get("items") or []:
        if item.get("metadata_only") is not True or item.get("read_only") is not True:
            raise AssertionError(f"Dashboard snapshot item should be read-only metadata: {item}")
        if agency_id is not None and item.get("agency_id") != agency_id:
            raise AssertionError(f"Agency dashboard snapshot leaked another agency: {item}")


def assert_section_shape(section: dict) -> None:
    for key in ["section_key", "title", "count", "counts", "statuses", "last_updated", "read_only", "metadata_only"]:
        if key not in section:
            raise AssertionError(f"Dashboard section missing {key}: {section}")
    if section.get("read_only") is not True or section.get("metadata_only") is not True:
        raise AssertionError(f"Dashboard section is not read-only metadata: {section}")
    counts = section.get("counts") or {}
    for key in ["total_count", "by_status", "warning_count", "blocker_count", "metadata_only"]:
        if key not in counts:
            raise AssertionError(f"Dashboard section counts missing {key}: {section}")


def main() -> int:
    verify_model_and_collection_registration()
    verify_readiness()
    openapi = get("/openapi.json")
    paths = openapi.get("paths") or {}
    verify_routes(paths)
    verify_frontend_and_docs()
    verify_endpoint_behavior()
    print("Phase 40.3 rollout dashboard foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Phase 40.3 rollout dashboard foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
