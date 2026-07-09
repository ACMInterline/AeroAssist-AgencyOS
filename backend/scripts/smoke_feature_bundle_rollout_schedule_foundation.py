#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import FeatureBundleRolloutSchedule, FeatureBundleRolloutScheduleCreate
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_52_1_reference_data_engine_foundation"
ROOT = Path(__file__).resolve().parents[2]
SCHEDULE_STATUSES = {"Planned", "Ready", "AwaitingApproval", "Approved", "Deferred", "Cancelled", "CompletedMetadata"}


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
        "rollout_execution_disabled",
        "feature_activation_disabled",
        "entitlement_behavior_disabled",
        "permission_changes_disabled",
        "cron_jobs_disabled",
        "schedulers_disabled",
        "workers_disabled",
        "queues_disabled",
        "timers_disabled",
        "background_execution_disabled",
        "external_api_calls_disabled",
        "ai_execution_disabled",
        "billing_disabled",
        "publishing_disabled",
        "automation_disabled",
    ]


def forbidden_enabled_flags() -> list[str]:
    return [
        "rollout_execution_enabled",
        "feature_activation_enabled",
        "entitlement_behavior_enabled",
        "permission_changes_enabled",
        "cron_jobs_enabled",
        "schedulers_enabled",
        "workers_enabled",
        "queues_enabled",
        "timers_enabled",
        "background_execution_enabled",
        "external_api_calls_enabled",
        "ai_execution_enabled",
        "billing_enabled",
        "publishing_enabled",
        "automation_enabled",
    ]


def assert_disabled_response(payload: dict) -> None:
    if payload.get("metadata_only") is not True:
        raise AssertionError(f"Payload is not metadata-only: {payload}")
    for flag in disabled_flags():
        if payload.get(flag) is not True:
            raise AssertionError(f"Payload missing disabled flag {flag}: {payload}")
    for flag in forbidden_enabled_flags():
        if payload.get(flag) is True:
            raise AssertionError(f"Payload exposes forbidden enabled flag {flag}: {payload}")


def verify_model_and_collection_registration() -> None:
    create_payload = FeatureBundleRolloutScheduleCreate(
        rollout_plan_id="plan-smoke",
        rollout_name="Smoke rollout schedule",
        agency_id="agency-smoke",
        bundle_id="bundle-smoke",
        schedule_status="AwaitingApproval",
        planned_start="2026-10-01T09:00:00Z",
        planned_finish="2026-10-01T11:00:00Z",
        maintenance_window="Sunday morning",
        estimated_duration="2 hours",
        dependency_summary={"dependencies": ["approval"]},
        checklist_summary={"counts": {"passed": 2}},
        approval_summary={"latest_status": "approved"},
        scheduling_notes="Metadata-only schedule smoke.",
    )
    schedule = FeatureBundleRolloutSchedule(
        **{
            **create_payload.model_dump(mode="json", exclude_none=True),
            "bundle_id": "bundle-smoke",
            "agency_id": "agency-smoke",
        }
    )
    dumped = schedule.model_dump(mode="json")
    if dumped.get("schedule_status") != "AwaitingApproval":
        raise AssertionError(f"Schedule status was not preserved: {dumped}")
    if dumped.get("metadata_only") is not True or dumped.get("scheduling_metadata_only") is not True:
        raise AssertionError(f"Schedule model should be metadata-only: {dumped}")
    assert_disabled_response(dumped)
    if "feature_bundle_rollout_schedules" not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("Rollout schedule collection is not agency-owned/registered.")
    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "feature_bundle_rollout_schedules_id_unique",
        "feature_bundle_rollout_schedules_schedule_unique",
        "feature_bundle_rollout_schedules_plan_lookup",
        "feature_bundle_rollout_schedules_agency_status_lookup",
        "feature_bundle_rollout_schedules_bundle_status_lookup",
        "feature_bundle_rollout_schedules_planned_start_lookup",
        "feature_bundle_rollout_schedules_created_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Rollout schedule index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    expected_methods = {
        "/api/platform/feature-bundle-rollout-schedule": {"get", "post"},
        "/api/platform/feature-bundle-rollout-schedule/summary": {"get"},
        "/api/platform/feature-bundle-rollout-schedule/{schedule_id}": {"get", "put"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-schedule": {"get"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-schedule/summary": {"get"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-schedule/{schedule_id}": {"get"},
    }
    for path, methods in expected_methods.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in [
        "/api/agencies/{agency_id}/feature-bundle-rollout-schedule",
        "/api/agencies/{agency_id}/feature-bundle-rollout-schedule/summary",
        "/api/agencies/{agency_id}/feature-bundle-rollout-schedule/{schedule_id}",
    ]:
        methods = set(paths.get(path, {}).keys())
        blocked_methods = methods & {"post", "put", "patch", "delete"}
        if blocked_methods:
            raise AssertionError(f"Agency rollout schedule route is not read-only: {path} {sorted(blocked_methods)}")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Feature Bundle Rollout Schedule"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Rollout Schedule"),
        (ROOT / "frontend/src/App.jsx", "/platform/feature-bundle-rollout-schedule"),
        (ROOT / "frontend/src/App.jsx", "/agency/rollout-schedule"),
        (ROOT / "frontend/src/pages/platform/FeatureBundleRolloutSchedulePage.jsx", "Feature Bundle Rollout Schedule"),
        (ROOT / "frontend/src/pages/platform/FeatureBundleRolloutSchedulePage.jsx", "Schedule records are metadata only"),
        (ROOT / "frontend/src/pages/agency/RolloutSchedulePage.jsx", "Rollout Schedule"),
        (ROOT / "frontend/src/pages/agency/RolloutSchedulePage.jsx", "Read-only rollout schedule metadata"),
        (ROOT / "docs/architecture/feature-bundle-rollout-schedule-foundation.md", "Feature Bundle Rollout Schedule Foundation"),
        (ROOT / "README.md", "Phase 40.5 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 40.5: Feature Bundle Rollout Schedule Foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "Phase 40.5 adds feature bundle rollout schedule metadata"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "Phase 40.5 adds feature bundle rollout schedule APIs"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Feature bundle rollout schedule"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Feature bundle rollout schedule"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/FeatureBundleRolloutSchedulePage.jsx",
        ROOT / "frontend/src/pages/agency/RolloutSchedulePage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)
    reject_text(ROOT / "frontend/src/pages/agency/RolloutSchedulePage.jsx", "<button")
    reject_text(ROOT / "frontend/src/pages/agency/RolloutSchedulePage.jsx", "onClick=")


def verify_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")
    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("feature_bundle_rollout_schedule_foundation") or {}
    for flag in [
        "feature_bundle_rollout_schedules_enabled",
        "platform_rollout_schedule_metadata_crud_enabled",
        "agency_rollout_schedule_read_only_enabled",
        "schedule_status_metadata_enabled",
        "planned_window_metadata_enabled",
        "maintenance_window_metadata_enabled",
        "estimated_duration_metadata_enabled",
        "dependency_summary_metadata_enabled",
        "checklist_summary_metadata_enabled",
        "approval_summary_metadata_enabled",
        "metadata_only",
        "read_only_planning",
        "actual_rollout_execution_disabled",
    ]:
        require_flag(section, flag)
    for flag in disabled_flags():
        require_flag(section, flag)
    require_flag(section, "readiness_required", False)
    for count_key in ["schedule_count", "schedule_status_counts"]:
        if count_key not in section:
            raise AssertionError(f"Rollout schedule readiness missing count: {count_key}")
    if not SCHEDULE_STATUSES.issubset(set((section.get("schedule_status_counts") or {}).keys())):
        raise AssertionError(f"Rollout schedule readiness status counts missing statuses: {section}")
    previous_section = readiness.get("feature_bundle_rollout_approval_foundation") or {}
    if previous_section.get("metadata_only") is not True:
        raise AssertionError("Previous rollout approval section should remain metadata-only.")


def verify_endpoint_behavior() -> None:
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires seeded demo agency.")
    agency_id = agencies[0]["id"]
    bundles = get("/api/platform/feature-flag-bundles", OWNER_HEADERS).get("items") or []
    if not bundles:
        raise AssertionError("Smoke requires feature flag bundle metadata.")
    bundle_id = next((item["bundle_id"] for item in bundles if item.get("bundle_key") == "core_agency"), bundles[0]["bundle_id"])

    plan_response = post(
        "/api/platform/feature-bundle-rollout-plans",
        {
            "agency_id": agency_id,
            "bundle_id": bundle_id,
            "plan_name": "Phase 40.5 smoke rollout schedule plan",
            "rollout_stage": "scheduled",
            "target_start_date": "2026-10-01",
            "target_end_date": "2026-10-15",
            "rollout_owner": "Platform Ops",
            "checklist_summary": {"counts": {"passed": 3, "warning": 0, "blocked": 0}, "metadata_only": True},
            "notes": "Plan metadata for rollout schedule smoke.",
        },
        OWNER_HEADERS,
        201,
    )
    rollout_plan_id = (plan_response.get("plan") or {}).get("rollout_plan_id")
    if not rollout_plan_id:
        raise AssertionError(f"Rollout plan was not created for schedule smoke: {plan_response}")

    approval_response = post(
        "/api/platform/feature-bundle-rollout-approvals",
        {
            "rollout_plan_id": rollout_plan_id,
            "agency_id": agency_id,
            "status": "approved",
            "reviewer": "Platform Ops",
            "notes": "Approved as metadata only for schedule smoke.",
        },
        OWNER_HEADERS,
        201,
    )
    approval_id = (approval_response.get("approval") or {}).get("approval_id")
    if not approval_id:
        raise AssertionError(f"Approval was not created for schedule smoke: {approval_response}")

    created = post(
        "/api/platform/feature-bundle-rollout-schedule",
        {
            "rollout_plan_id": rollout_plan_id,
            "agency_id": agency_id,
            "bundle_id": bundle_id,
            "rollout_name": "Phase 40.5 metadata-only rollout schedule",
            "schedule_status": "AwaitingApproval",
            "planned_start": "2026-10-05T09:00:00Z",
            "planned_finish": "2026-10-05T11:00:00Z",
            "maintenance_window": "Sunday morning",
            "estimated_duration": "2 hours",
            "dependency_summary": {"approval_id": approval_id, "notes": "Approval metadata exists."},
            "scheduling_notes": "Metadata-only schedule. No timers or rollout execution.",
        },
        OWNER_HEADERS,
        201,
    )
    if created.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected create phase: {created.get('phase')}")
    assert_disabled_response(created)
    schedule = created.get("schedule") or {}
    assert_schedule_shape(schedule)
    schedule_id = schedule.get("schedule_id")
    if not schedule_id:
        raise AssertionError(f"Schedule id missing: {created}")
    if (schedule.get("approval_summary") or {}).get("latest_status") != "approved":
        raise AssertionError(f"Schedule did not include approval summary metadata: {created}")

    updated = put(
        f"/api/platform/feature-bundle-rollout-schedule/{schedule_id}",
        {
            "schedule_status": "Approved",
            "scheduling_notes": "Approved schedule metadata only; no rollout execution.",
            "estimated_duration": "2 hours",
        },
        OWNER_HEADERS,
    )
    assert_disabled_response(updated)
    updated_schedule = updated.get("schedule") or {}
    assert_schedule_shape(updated_schedule)
    if updated_schedule.get("schedule_status") != "Approved":
        raise AssertionError(f"Schedule update did not persist status metadata: {updated}")

    platform_list = get("/api/platform/feature-bundle-rollout-schedule", OWNER_HEADERS)
    assert_disabled_response(platform_list)
    listed = next((item for item in platform_list.get("items") or [] if item.get("schedule_id") == schedule_id), None)
    if not listed:
        raise AssertionError(f"Platform schedule list missing created schedule: {platform_list}")
    assert_schedule_shape(listed)

    platform_summary = get("/api/platform/feature-bundle-rollout-schedule/summary", OWNER_HEADERS)
    assert_summary_shape(platform_summary)

    platform_detail = get(f"/api/platform/feature-bundle-rollout-schedule/{schedule_id}", OWNER_HEADERS)
    assert_disabled_response(platform_detail)
    assert_schedule_shape(platform_detail.get("schedule") or {})

    agency_list = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-schedule", OWNER_HEADERS)
    assert_disabled_response(agency_list)
    if agency_list.get("read_only") is not True:
        raise AssertionError(f"Agency schedule list should be read-only: {agency_list}")
    agency_item = next((item for item in agency_list.get("items") or [] if item.get("schedule_id") == schedule_id), None)
    if not agency_item:
        raise AssertionError(f"Agency schedule list missing created schedule: {agency_list}")
    assert_schedule_shape(agency_item, agency_view=True)

    agency_summary = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-schedule/summary", OWNER_HEADERS)
    assert_summary_shape(agency_summary, agency_id=agency_id)
    if agency_summary.get("read_only") is not True:
        raise AssertionError(f"Agency schedule summary should be read-only: {agency_summary}")

    agency_detail = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-schedule/{schedule_id}", OWNER_HEADERS)
    assert_disabled_response(agency_detail)
    if agency_detail.get("read_only") is not True:
        raise AssertionError(f"Agency schedule detail should be read-only: {agency_detail}")
    assert_schedule_shape(agency_detail.get("schedule") or {}, agency_view=True)

    request("POST", f"/api/agencies/{agency_id}/feature-bundle-rollout-schedule", {"rollout_plan_id": rollout_plan_id}, OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/feature-bundle-rollout-schedule/{schedule_id}", {"schedule_status": "Cancelled"}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/feature-bundle-rollout-schedule/{schedule_id}", {}, OWNER_HEADERS, 405)


def assert_schedule_shape(schedule: dict, *, agency_view: bool = False) -> None:
    for key in [
        "schedule_id",
        "rollout_plan_id",
        "rollout_name",
        "bundle_id",
        "agency_id",
        "schedule_status",
        "planned_start",
        "planned_finish",
        "maintenance_window",
        "estimated_duration",
        "dependency_summary",
        "checklist_summary",
        "approval_summary",
        "scheduling_notes",
        "plan_name",
        "agency_name",
        "bundle_key",
        "bundle_name",
        "metadata_only",
        "scheduling_metadata_only",
    ]:
        if key not in schedule:
            raise AssertionError(f"Schedule missing {key}: {schedule}")
    if schedule.get("schedule_status") not in SCHEDULE_STATUSES:
        raise AssertionError(f"Schedule status is invalid: {schedule}")
    if agency_view and schedule.get("payloads_hidden") is not True:
        raise AssertionError(f"Agency schedule should hide payloads: {schedule}")
    assert_disabled_response(schedule)


def assert_summary_shape(payload: dict, *, agency_id: str | None = None) -> None:
    if payload.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected summary phase: {payload}")
    if agency_id is not None and payload.get("agency_id") != agency_id:
        raise AssertionError(f"Agency schedule summary did not stay agency-scoped: {payload}")
    assert_disabled_response(payload)
    summary = payload.get("summary") or {}
    if "by_schedule_status" not in summary or "total_count" not in summary:
        raise AssertionError(f"Schedule summary malformed: {payload}")
    if not SCHEDULE_STATUSES.issubset(set((summary.get("by_schedule_status") or {}).keys())):
        raise AssertionError(f"Schedule summary missing statuses: {payload}")


def main() -> int:
    verify_model_and_collection_registration()
    verify_readiness()
    openapi = get("/openapi.json")
    paths = openapi.get("paths") or {}
    verify_routes(paths)
    verify_frontend_and_docs()
    verify_endpoint_behavior()
    print("Phase 40.5 feature bundle rollout schedule foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Phase 40.5 feature bundle rollout schedule foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
