#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import (
    FeatureBundleRolloutActor,
    FeatureBundleRolloutEventType,
    FeatureBundleRolloutTimelineEntry,
    FeatureBundleRolloutTimelineEntryCreate,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, request


EXPECTED_PHASE = "phase_50_0_airline_operational_intelligence_engine_architecture_foundation"
ROOT = Path(__file__).resolve().parents[2]
EVENT_TYPES = {
    "plan_created",
    "plan_edited",
    "approval_requested",
    "approval_granted",
    "approval_rejected",
    "schedule_created",
    "schedule_changed",
    "rollout_started",
    "rollout_completed",
    "rollback_planned",
    "note_added",
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
        "feature_bundles_enablement_disabled",
        "feature_bundle_enablement_disabled",
        "agency_permission_changes_disabled",
        "rollout_plan_execution_disabled",
        "rollout_execution_disabled",
        "background_jobs_disabled",
        "background_workers_disabled",
        "scheduled_jobs_disabled",
        "cron_jobs_disabled",
        "automation_disabled",
        "publishing_disabled",
        "provider_calls_disabled",
        "provider_execution_disabled",
        "external_api_calls_disabled",
        "email_sending_disabled",
        "notifications_disabled",
        "notification_sending_disabled",
        "rollout_state_enforcement_disabled",
        "subscription_modification_disabled",
    ]


def forbidden_enabled_flags() -> list[str]:
    return [
        "feature_bundles_enablement_enabled",
        "feature_bundle_enablement_enabled",
        "agency_permission_changes_enabled",
        "rollout_plan_execution_enabled",
        "rollout_execution_enabled",
        "background_jobs_enabled",
        "scheduled_jobs_enabled",
        "automation_enabled",
        "publishing_enabled",
        "provider_calls_enabled",
        "email_sending_enabled",
        "notifications_enabled",
        "rollout_state_enforcement_enabled",
        "subscription_modification_enabled",
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
    actor = FeatureBundleRolloutActor(
        actor_id="platform-smoke",
        actor_type="platform_user",
        display_name="Platform Smoke",
        email="owner@aeroassist.dev",
        role="platform_owner",
    )
    payload = FeatureBundleRolloutTimelineEntryCreate(
        rollout_plan_id="plan-smoke",
        agency_id="agency-smoke",
        bundle_id="bundle-smoke",
        event_type=FeatureBundleRolloutEventType.SCHEDULE_CHANGED,
        event_label="Schedule changed",
        actor=actor,
        occurred_at="2026-11-02T10:00:00Z",
        description="Metadata-only schedule change.",
        source="smoke",
        metadata={"smoke": True},
    )
    entry = FeatureBundleRolloutTimelineEntry(
        **{
            **payload.model_dump(mode="json", exclude_none=True),
            "agency_id": "agency-smoke",
            "bundle_id": "bundle-smoke",
        }
    )
    dumped = entry.model_dump(mode="json")
    if dumped.get("event_type") != "schedule_changed":
        raise AssertionError(f"Timeline event type was not preserved: {dumped}")
    if dumped.get("metadata_only") is not True or dumped.get("timeline_metadata_only") is not True:
        raise AssertionError(f"Timeline model should be metadata-only: {dumped}")
    for flag in [
        "feature_bundle_enablement_disabled",
        "agency_permission_changes_disabled",
        "rollout_plan_execution_disabled",
        "background_jobs_disabled",
        "provider_calls_disabled",
        "email_sending_disabled",
        "notification_sending_disabled",
        "rollout_state_enforcement_disabled",
        "subscription_modification_disabled",
        "automation_disabled",
        "publishing_disabled",
    ]:
        if dumped.get(flag) is not True:
            raise AssertionError(f"Timeline model missing disabled flag {flag}: {dumped}")
    if "feature_bundle_rollout_timeline_entries" not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("Rollout timeline collection is not agency-owned/registered.")
    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "feature_bundle_rollout_timeline_entries_id_unique",
        "feature_bundle_rollout_timeline_entries_entry_unique",
        "feature_bundle_rollout_timeline_entries_plan_occurred_lookup",
        "feature_bundle_rollout_timeline_entries_agency_occurred_lookup",
        "feature_bundle_rollout_timeline_entries_bundle_event_lookup",
        "feature_bundle_rollout_timeline_entries_event_occurred_lookup",
        "feature_bundle_rollout_timeline_entries_created_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Rollout timeline index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    expected_methods = {
        "/api/platform/feature-bundle-rollout-timeline": {"get", "post"},
        "/api/platform/feature-bundle-rollout-timeline/summary": {"get"},
        "/api/platform/feature-bundle-rollout-timeline/{timeline_entry_id}": {"get"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-timeline": {"get"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-timeline/summary": {"get"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-timeline/{timeline_entry_id}": {"get"},
    }
    for path, methods in expected_methods.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in [
        "/api/agencies/{agency_id}/feature-bundle-rollout-timeline",
        "/api/agencies/{agency_id}/feature-bundle-rollout-timeline/summary",
        "/api/agencies/{agency_id}/feature-bundle-rollout-timeline/{timeline_entry_id}",
    ]:
        methods = set(paths.get(path, {}).keys())
        blocked_methods = methods & {"post", "put", "patch", "delete"}
        if blocked_methods:
            raise AssertionError(f"Agency rollout timeline route is not read-only: {path} {sorted(blocked_methods)}")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Feature Bundle Rollout Timeline"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Rollout Timeline"),
        (ROOT / "frontend/src/App.jsx", "/platform/feature-bundle-rollout-timeline"),
        (ROOT / "frontend/src/App.jsx", "/agency/rollout-timeline"),
        (ROOT / "frontend/src/pages/platform/FeatureBundleRolloutTimelinePage.jsx", "Feature Bundle Rollout Timeline"),
        (ROOT / "frontend/src/pages/platform/FeatureBundleRolloutTimelinePage.jsx", "Read-only rollout history metadata"),
        (ROOT / "frontend/src/pages/agency/RolloutTimelinePage.jsx", "Rollout Timeline"),
        (ROOT / "frontend/src/pages/agency/RolloutTimelinePage.jsx", "Read-only rollout timeline metadata"),
        (ROOT / "docs/architecture/feature-bundle-rollout-timeline-foundation.md", "Feature Bundle Rollout Timeline Foundation"),
        (ROOT / "README.md", "Phase 40.6 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 40.6: Feature Bundle Rollout Timeline Foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "Phase 40.6 adds feature bundle rollout timeline metadata"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "Phase 40.6 adds feature bundle rollout timeline APIs"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Feature bundle rollout timeline"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Feature bundle rollout timeline"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/FeatureBundleRolloutTimelinePage.jsx",
        ROOT / "frontend/src/pages/agency/RolloutTimelinePage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)
    reject_text(ROOT / "frontend/src/pages/agency/RolloutTimelinePage.jsx", "<button")
    reject_text(ROOT / "frontend/src/pages/agency/RolloutTimelinePage.jsx", "onClick=")
    reject_text(ROOT / "frontend/src/pages/platform/FeatureBundleRolloutTimelinePage.jsx", "apiPost")
    reject_text(ROOT / "frontend/src/pages/platform/FeatureBundleRolloutTimelinePage.jsx", "apiPut")


def verify_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")
    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("feature_bundle_rollout_timeline_foundation") or {}
    for flag in [
        "feature_bundle_rollout_timeline_entries_enabled",
        "feature_bundle_rollout_actor_metadata_enabled",
        "feature_bundle_rollout_event_type_metadata_enabled",
        "platform_rollout_timeline_metadata_create_enabled",
        "platform_rollout_timeline_read_enabled",
        "agency_rollout_timeline_read_only_enabled",
        "timeline_filter_by_plan_enabled",
        "timeline_filter_by_agency_enabled",
        "timeline_filter_by_bundle_enabled",
        "timeline_filter_by_event_type_enabled",
        "timeline_filter_by_date_enabled",
        "newest_first_enabled",
        "metadata_only",
        "historical_timeline_only",
    ]:
        require_flag(section, flag)
    for flag in disabled_flags():
        require_flag(section, flag)
    require_flag(section, "readiness_required", False)
    for count_key in ["timeline_entry_count", "timeline_event_type_counts"]:
        if count_key not in section:
            raise AssertionError(f"Rollout timeline readiness missing count: {count_key}")
    if not EVENT_TYPES.issubset(set((section.get("timeline_event_type_counts") or {}).keys())):
        raise AssertionError(f"Rollout timeline readiness event type counts missing events: {section}")
    previous_section = readiness.get("feature_bundle_rollout_schedule_foundation") or {}
    if previous_section.get("metadata_only") is not True:
        raise AssertionError("Previous rollout schedule section should remain metadata-only.")


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
            "plan_name": "Phase 40.6 smoke rollout timeline plan",
            "rollout_stage": "scheduled",
            "target_start_date": "2026-11-01",
            "target_end_date": "2026-11-15",
            "rollout_owner": "Platform Ops",
            "checklist_summary": {"counts": {"passed": 4, "warning": 0, "blocked": 0}, "metadata_only": True},
            "notes": "Plan metadata for rollout timeline smoke.",
        },
        OWNER_HEADERS,
        201,
    )
    rollout_plan_id = (plan_response.get("plan") or {}).get("rollout_plan_id")
    if not rollout_plan_id:
        raise AssertionError(f"Rollout plan was not created for timeline smoke: {plan_response}")

    created_plan_event = create_timeline_entry(
        rollout_plan_id,
        agency_id,
        bundle_id,
        "plan_created",
        "2026-11-01T09:00:00Z",
        "Plan created as metadata only.",
    )
    created_schedule_event = create_timeline_entry(
        rollout_plan_id,
        agency_id,
        bundle_id,
        "schedule_changed",
        "2026-11-02T10:00:00Z",
        "Schedule changed as metadata only.",
    )
    plan_entry_id = (created_plan_event.get("entry") or {}).get("timeline_entry_id")
    schedule_entry_id = (created_schedule_event.get("entry") or {}).get("timeline_entry_id")
    if not plan_entry_id or not schedule_entry_id:
        raise AssertionError(f"Timeline entry ids missing: {created_plan_event} {created_schedule_event}")

    platform_list = get(f"/api/platform/feature-bundle-rollout-timeline?rollout_plan_id={rollout_plan_id}", OWNER_HEADERS)
    assert_disabled_response(platform_list)
    if platform_list.get("newest_first") is not True:
        raise AssertionError(f"Timeline list should be newest-first: {platform_list}")
    items = platform_list.get("items") or []
    if [item.get("timeline_entry_id") for item in items[:2]] != [schedule_entry_id, plan_entry_id]:
        raise AssertionError(f"Timeline list is not newest-first for created entries: {items[:2]}")
    for item in items[:2]:
        assert_entry_shape(item)

    event_filter = get(f"/api/platform/feature-bundle-rollout-timeline?event_type=plan_created&rollout_plan_id={rollout_plan_id}", OWNER_HEADERS)
    if not any(item.get("timeline_entry_id") == plan_entry_id for item in event_filter.get("items") or []):
        raise AssertionError(f"Event-type filter did not return plan_created entry: {event_filter}")
    if any(item.get("event_type") != "plan_created" for item in event_filter.get("items") or []):
        raise AssertionError(f"Event-type filter returned another event type: {event_filter}")

    date_filter = get(f"/api/platform/feature-bundle-rollout-timeline?rollout_plan_id={rollout_plan_id}&date_from=2026-11-02&date_to=2026-11-02", OWNER_HEADERS)
    date_ids = {item.get("timeline_entry_id") for item in date_filter.get("items") or []}
    if schedule_entry_id not in date_ids or plan_entry_id in date_ids:
        raise AssertionError(f"Date filter did not isolate expected entry: {date_filter}")

    platform_summary = get("/api/platform/feature-bundle-rollout-timeline/summary", OWNER_HEADERS)
    assert_summary_shape(platform_summary)

    platform_detail = get(f"/api/platform/feature-bundle-rollout-timeline/{schedule_entry_id}", OWNER_HEADERS)
    assert_disabled_response(platform_detail)
    assert_entry_shape(platform_detail.get("entry") or {})

    agency_list = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-timeline?event_type=schedule_changed", OWNER_HEADERS)
    assert_disabled_response(agency_list)
    if agency_list.get("read_only") is not True:
        raise AssertionError(f"Agency timeline list should be read-only: {agency_list}")
    agency_item = next((item for item in agency_list.get("items") or [] if item.get("timeline_entry_id") == schedule_entry_id), None)
    if not agency_item:
        raise AssertionError(f"Agency timeline list missing created entry: {agency_list}")
    assert_entry_shape(agency_item, agency_view=True)

    agency_summary = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-timeline/summary", OWNER_HEADERS)
    assert_summary_shape(agency_summary, agency_id=agency_id)
    if agency_summary.get("read_only") is not True:
        raise AssertionError(f"Agency timeline summary should be read-only: {agency_summary}")

    agency_detail = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-timeline/{schedule_entry_id}", OWNER_HEADERS)
    assert_disabled_response(agency_detail)
    if agency_detail.get("read_only") is not True:
        raise AssertionError(f"Agency timeline detail should be read-only: {agency_detail}")
    assert_entry_shape(agency_detail.get("entry") or {}, agency_view=True)

    request("POST", f"/api/agencies/{agency_id}/feature-bundle-rollout-timeline", {"rollout_plan_id": rollout_plan_id}, OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/feature-bundle-rollout-timeline/{schedule_entry_id}", {"description": "blocked"}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/feature-bundle-rollout-timeline/{schedule_entry_id}", {}, OWNER_HEADERS, 405)


def create_timeline_entry(rollout_plan_id: str, agency_id: str, bundle_id: str, event_type: str, occurred_at: str, description: str) -> dict:
    created = post(
        "/api/platform/feature-bundle-rollout-timeline",
        {
            "rollout_plan_id": rollout_plan_id,
            "agency_id": agency_id,
            "bundle_id": bundle_id,
            "event_type": event_type,
            "occurred_at": occurred_at,
            "description": description,
            "source": "smoke",
            "actor": {
                "actor_id": "platform-smoke",
                "actor_type": "platform_user",
                "display_name": "Platform Smoke",
                "email": "owner@aeroassist.dev",
                "role": "platform_owner",
            },
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    if created.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected create phase: {created.get('phase')}")
    assert_disabled_response(created)
    assert_entry_shape(created.get("entry") or {})
    return created


def assert_entry_shape(entry: dict, *, agency_view: bool = False) -> None:
    for key in [
        "timeline_entry_id",
        "rollout_plan_id",
        "agency_id",
        "bundle_id",
        "event_type",
        "event_label",
        "actor",
        "occurred_at",
        "description",
        "source",
        "metadata",
        "plan_name",
        "agency_name",
        "bundle_key",
        "bundle_name",
        "metadata_only",
        "timeline_metadata_only",
    ]:
        if key not in entry:
            raise AssertionError(f"Timeline entry missing {key}: {entry}")
    if entry.get("event_type") not in EVENT_TYPES:
        raise AssertionError(f"Timeline event type is invalid: {entry}")
    if not isinstance(entry.get("actor"), dict) or entry["actor"].get("metadata_only") is not True:
        raise AssertionError(f"Timeline actor metadata missing: {entry}")
    if agency_view and entry.get("read_only") is not True:
        raise AssertionError(f"Agency timeline entry should be read-only: {entry}")
    assert_disabled_response(entry)


def assert_summary_shape(payload: dict, *, agency_id: str | None = None) -> None:
    if payload.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected summary phase: {payload}")
    if agency_id is not None and payload.get("agency_id") != agency_id:
        raise AssertionError(f"Agency timeline summary did not stay agency-scoped: {payload}")
    assert_disabled_response(payload)
    summary = payload.get("summary") or {}
    if "by_event_type" not in summary or "total_count" not in summary:
        raise AssertionError(f"Timeline summary malformed: {payload}")
    if not EVENT_TYPES.issubset(set((summary.get("by_event_type") or {}).keys())):
        raise AssertionError(f"Timeline summary missing event types: {payload}")


def main() -> int:
    verify_model_and_collection_registration()
    verify_readiness()
    openapi = get("/openapi.json")
    paths = openapi.get("paths") or {}
    verify_routes(paths)
    verify_frontend_and_docs()
    verify_endpoint_behavior()
    print("Phase 40.6 feature bundle rollout timeline foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Phase 40.6 feature bundle rollout timeline foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
