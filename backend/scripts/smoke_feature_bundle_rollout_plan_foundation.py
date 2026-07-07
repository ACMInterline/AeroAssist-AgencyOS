#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import FeatureBundleRolloutPlan, FeatureBundleRolloutPlanCreate
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_40_12_feature_bundle_rollout_rollback_plan_foundation"
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
    create_payload = FeatureBundleRolloutPlanCreate(
        agency_id="agency-smoke",
        bundle_id="bundle_core_agency",
        plan_name="Smoke rollout plan",
        rollout_stage="readiness_review",
        target_start_date="2026-08-01",
        target_end_date="2026-08-15",
        rollout_owner="Platform Ops",
        checklist_summary={"counts": {"passed": 3, "warning": 1, "blocked": 0}},
        readiness_snapshot_id="readiness-smoke",
        assigned_bundle_id="assignment-smoke",
        notes="Metadata-only rollout plan smoke.",
    )
    plan = FeatureBundleRolloutPlan(**create_payload.model_dump(mode="json", exclude_none=True))
    dumped = plan.model_dump(mode="json")
    if dumped.get("metadata_only") is not True:
        raise AssertionError(f"Rollout plan model is not metadata-only: {dumped}")
    for flag in [
        "rollout_execution_disabled",
        "feature_activation_disabled",
        "feature_access_enforcement_disabled",
        "billing_disabled",
        "provider_execution_disabled",
    ]:
        if dumped.get(flag) is not True:
            raise AssertionError(f"Rollout plan model missing disabled flag {flag}: {dumped}")
    if dumped.get("rollout_stage") != "readiness_review":
        raise AssertionError(f"Rollout stage was not preserved: {dumped}")
    if "agency_feature_bundle_rollout_plans" not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("Rollout plan collection is not agency-owned/registered.")
    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "agency_feature_bundle_rollout_plans_id_unique",
        "agency_feature_bundle_rollout_plans_plan_unique",
        "agency_feature_bundle_rollout_plans_agency_stage_lookup",
        "agency_feature_bundle_rollout_plans_agency_bundle_lookup",
        "agency_feature_bundle_rollout_plans_readiness_lookup",
        "agency_feature_bundle_rollout_plans_target_start_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Rollout plan index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    expected_methods = {
        "/api/platform/feature-bundle-rollout-plans": {"get", "post"},
        "/api/platform/feature-bundle-rollout-plans/summary": {"get"},
        "/api/platform/feature-bundle-rollout-plans/{rollout_plan_id}": {"get", "put"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-plans": {"get"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-plans/summary": {"get"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-plans/{rollout_plan_id}": {"get"},
    }
    for path, methods in expected_methods.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in [
        "/api/agencies/{agency_id}/feature-bundle-rollout-plans",
        "/api/agencies/{agency_id}/feature-bundle-rollout-plans/summary",
        "/api/agencies/{agency_id}/feature-bundle-rollout-plans/{rollout_plan_id}",
    ]:
        methods = set(paths.get(path, {}).keys())
        blocked_methods = methods & {"post", "put", "patch", "delete"}
        if blocked_methods:
            raise AssertionError(f"Agency rollout plan route is not read-only: {path} {sorted(blocked_methods)}")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Feature Bundle Rollout Plans"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Rollout Plans"),
        (ROOT / "frontend/src/App.jsx", "/platform/feature-bundle-rollout-plans"),
        (ROOT / "frontend/src/App.jsx", "/agency/rollout-plans"),
        (ROOT / "frontend/src/pages/platform/FeatureBundleRolloutPlansPage.jsx", "Feature Bundle Rollout Plans"),
        (ROOT / "frontend/src/pages/platform/FeatureBundleRolloutPlansPage.jsx", "do not activate, publish, send, bill, enforce access, block routes, or execute rollout actions"),
        (ROOT / "frontend/src/pages/agency/RolloutPlansPage.jsx", "Rollout Plans"),
        (ROOT / "frontend/src/pages/agency/RolloutPlansPage.jsx", "does not activate, publish, send, bill, enforce access, or block features"),
        (ROOT / "docs/architecture/feature-bundle-rollout-plan-foundation.md", "Feature Bundle Rollout Plan Foundation"),
        (ROOT / "README.md", "Phase 40.2 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 40.2: Feature Bundle Rollout Plan Foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "Phase 40.2 adds feature bundle rollout plan metadata"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "Phase 40.2 adds feature bundle rollout plan APIs"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Feature bundle rollout plans"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Feature bundle rollout plans"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/FeatureBundleRolloutPlansPage.jsx",
        ROOT / "frontend/src/pages/agency/RolloutPlansPage.jsx",
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
    section = readiness.get("feature_bundle_rollout_plan_foundation") or {}
    for flag in [
        "feature_bundle_rollout_plans_enabled",
        "platform_rollout_plan_metadata_crud_enabled",
        "agency_rollout_plan_read_only_enabled",
        "rollout_stage_metadata_enabled",
        "target_window_metadata_enabled",
        "readiness_snapshot_reference_enabled",
        "assigned_bundle_reference_enabled",
        "checklist_summary_metadata_enabled",
        "metadata_only",
    ]:
        require_flag(section, flag)
    for flag in disabled_flags():
        require_flag(section, flag)
    require_flag(section, "readiness_required", False)
    if "rollout_stage_counts" not in section:
        raise AssertionError(f"Rollout plan stage counts missing: {section}")
    previous_section = readiness.get("feature_bundle_rollout_readiness_foundation") or {}
    if previous_section.get("metadata_only") is not True:
        raise AssertionError("Previous rollout readiness section should remain metadata-only.")


def verify_endpoint_behavior() -> None:
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires seeded demo agency.")
    agency_id = agencies[0]["id"]
    bundles = get("/api/platform/feature-flag-bundles", OWNER_HEADERS).get("items") or []
    if not bundles:
        raise AssertionError("Smoke requires feature flag bundle metadata.")
    bundle_id = next((item["bundle_id"] for item in bundles if item.get("bundle_key") == "core_agency"), bundles[0]["bundle_id"])

    created_assignment = post(
        f"/api/platform/agencies/{agency_id}/bundle-assignments",
        {
            "bundle_id": bundle_id,
            "effective_date": "2026-08-01",
            "status": "assigned",
            "review_status": "reviewed",
            "notes": "Metadata-only rollout plan smoke assignment.",
        },
        OWNER_HEADERS,
        201,
    )
    assignment_id = (created_assignment.get("assignment") or {}).get("assignment_id")
    if not assignment_id:
        raise AssertionError(f"Assignment was not created for rollout plan smoke: {created_assignment}")

    post("/api/platform/feature-bundle-rollout-readiness/defaults", {}, OWNER_HEADERS, 201)
    readiness_response = get("/api/platform/feature-bundle-rollout-readiness", OWNER_HEADERS)
    readiness_item = next((item for item in readiness_response.get("items") or [] if item.get("assignment_id") == assignment_id), None)
    if not readiness_item:
        raise AssertionError(f"Readiness metadata missing for rollout plan smoke assignment: {readiness_response}")
    assert_readiness_summary_source(readiness_item)

    create_payload = {
        "agency_id": agency_id,
        "bundle_id": bundle_id,
        "plan_name": "Phase 40.2 smoke rollout plan",
        "rollout_stage": "readiness_review",
        "target_start_date": "2026-08-10",
        "target_end_date": "2026-08-20",
        "rollout_owner": "Platform Ops",
        "checklist_summary": {
            "counts": readiness_item.get("checklist_counts") or {},
            "warning_count": (readiness_item.get("checklist_counts") or {}).get("warning", 0),
            "blocker_count": (readiness_item.get("checklist_counts") or {}).get("blocked", 0),
            "readiness_status": readiness_item.get("readiness_status"),
            "metadata_only": True,
        },
        "readiness_snapshot_id": readiness_item.get("id"),
        "assigned_bundle_id": assignment_id,
        "notes": "Metadata-only plan smoke. No rollout execution.",
    }
    created_plan = post("/api/platform/feature-bundle-rollout-plans", create_payload, OWNER_HEADERS, 201)
    if created_plan.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected create phase: {created_plan.get('phase')}")
    assert_disabled_response(created_plan)
    plan = created_plan.get("plan") or {}
    assert_plan_shape(plan)
    rollout_plan_id = plan.get("rollout_plan_id")
    if not rollout_plan_id:
        raise AssertionError(f"Rollout plan id missing: {created_plan}")

    platform_list = get("/api/platform/feature-bundle-rollout-plans", OWNER_HEADERS)
    assert_disabled_response(platform_list)
    listed_plan = next((item for item in platform_list.get("items") or [] if item.get("rollout_plan_id") == rollout_plan_id), None)
    if not listed_plan:
        raise AssertionError(f"Platform rollout plan list missing created plan: {platform_list}")
    assert_plan_shape(listed_plan)

    platform_summary = get("/api/platform/feature-bundle-rollout-plans/summary", OWNER_HEADERS)
    if "by_rollout_stage" not in (platform_summary.get("summary") or {}):
        raise AssertionError(f"Platform rollout plan summary malformed: {platform_summary}")

    platform_detail = get(f"/api/platform/feature-bundle-rollout-plans/{rollout_plan_id}", OWNER_HEADERS)
    if (platform_detail.get("plan") or {}).get("rollout_plan_id") != rollout_plan_id:
        raise AssertionError(f"Platform rollout plan detail malformed: {platform_detail}")

    updated = put(
        f"/api/platform/feature-bundle-rollout-plans/{rollout_plan_id}",
        {
            "rollout_stage": "scheduled",
            "notes": "Scheduled stage recorded as metadata only; no rollout execution.",
        },
        OWNER_HEADERS,
    )
    updated_plan = updated.get("plan") or {}
    if updated_plan.get("rollout_stage") != "scheduled":
        raise AssertionError(f"Rollout plan update did not persist stage metadata: {updated}")
    assert_disabled_response(updated)

    agency_list = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-plans", OWNER_HEADERS)
    if agency_list.get("read_only") is not True or agency_list.get("metadata_only") is not True:
        raise AssertionError(f"Agency rollout plan response should be read-only metadata: {agency_list}")
    agency_plan = next((item for item in agency_list.get("items") or [] if item.get("rollout_plan_id") == rollout_plan_id), None)
    if not agency_plan:
        raise AssertionError(f"Agency rollout plan list missing created plan: {agency_list}")
    if agency_plan.get("payloads_hidden") is not True:
        raise AssertionError(f"Agency rollout plan should hide payloads: {agency_plan}")
    assert_plan_shape(agency_plan)

    agency_detail = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-plans/{rollout_plan_id}", OWNER_HEADERS)
    if agency_detail.get("read_only") is not True or (agency_detail.get("plan") or {}).get("rollout_plan_id") != rollout_plan_id:
        raise AssertionError(f"Agency rollout plan detail malformed: {agency_detail}")
    agency_summary = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-plans/summary", OWNER_HEADERS)
    if agency_summary.get("read_only") is not True or "by_rollout_stage" not in (agency_summary.get("summary") or {}):
        raise AssertionError(f"Agency rollout plan summary malformed: {agency_summary}")

    request("POST", f"/api/agencies/{agency_id}/feature-bundle-rollout-plans", {"plan_name": "Blocked"}, OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/feature-bundle-rollout-plans/{rollout_plan_id}", {"rollout_stage": "paused"}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/feature-bundle-rollout-plans/{rollout_plan_id}", {}, OWNER_HEADERS, 405)


def assert_readiness_summary_source(item: dict) -> None:
    if not item.get("checklist_counts"):
        raise AssertionError(f"Readiness checklist counts missing: {item}")
    if "id" not in item or "assignment_id" not in item:
        raise AssertionError(f"Readiness summary source malformed: {item}")


def assert_plan_shape(plan: dict) -> None:
    for key in [
        "rollout_plan_id",
        "agency_id",
        "bundle_id",
        "plan_name",
        "rollout_stage",
        "target_start_date",
        "target_end_date",
        "rollout_owner",
        "checklist_summary",
        "metadata_only",
        "warnings",
        "blockers",
    ]:
        if key not in plan:
            raise AssertionError(f"Rollout plan missing {key}: {plan}")
    if "counts" not in (plan.get("checklist_summary") or {}):
        raise AssertionError(f"Rollout plan checklist summary missing counts: {plan}")
    assert_disabled_response(plan)


def assert_disabled_response(payload: dict) -> None:
    for flag in disabled_flags():
        if payload.get(flag) is not True:
            raise AssertionError(f"Payload missing disabled flag {flag}: {payload}")
    for flag in [
        "rollout_execution_enabled",
        "feature_activation_enabled",
        "feature_access_enforcement_enabled",
        "route_blocking_enabled",
        "billing_enabled",
        "payments_enabled",
        "provider_execution_enabled",
        "external_api_calls_enabled",
        "ai_execution_enabled",
        "scraping_enabled",
        "publishing_enabled",
        "email_sending_enabled",
        "sms_sending_enabled",
    ]:
        if payload.get(flag) is True:
            raise AssertionError(f"Payload exposes forbidden enabled flag {flag}: {payload}")


def disabled_flags() -> list[str]:
    return [
        "rollout_execution_disabled",
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
        "external_services_disabled",
        "ai_execution_disabled",
        "scraping_disabled",
        "publishing_disabled",
        "background_workers_disabled",
        "cron_disabled",
    ]


def main() -> int:
    verify_model_and_collection_registration()
    verify_readiness()
    openapi = get("/openapi.json")
    paths = openapi.get("paths") or {}
    verify_routes(paths)
    verify_frontend_and_docs()
    verify_endpoint_behavior()
    print("Phase 40.2 feature bundle rollout plan foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Phase 40.2 feature bundle rollout plan foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
