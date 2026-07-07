#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import (
    FeatureBundleRolloutApproval,
    FeatureBundleRolloutApprovalCreate,
    FeatureBundleRolloutApprovalNote,
    FeatureBundleRolloutApprovalSummary,
    FeatureBundleRolloutApprovalTimelineEntry,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_41_1_travel_request_workspace_foundation"
ROOT = Path(__file__).resolve().parents[2]
APPROVAL_STATUSES = {"draft", "submitted", "under_review", "approved", "rejected", "archived"}


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
        "feature_enablement_disabled",
        "feature_activation_disabled",
        "route_blocking_disabled",
        "permission_enforcement_disabled",
        "runtime_gating_disabled",
        "billing_disabled",
        "payments_disabled",
        "stripe_disabled",
        "payment_provider_disabled",
        "provider_execution_disabled",
        "external_api_calls_disabled",
        "authentication_changes_disabled",
        "deployment_automation_disabled",
        "rollout_execution_disabled",
        "background_workers_disabled",
        "cron_disabled",
        "webhook_execution_disabled",
        "email_sending_disabled",
        "sms_sending_disabled",
        "notifications_disabled",
        "ai_execution_disabled",
        "openai_disabled",
        "scraping_disabled",
        "publishing_disabled",
    ]


def forbidden_enabled_flags() -> list[str]:
    return [
        "feature_enablement_enabled",
        "feature_activation_enabled",
        "route_blocking_enabled",
        "permission_enforcement_enabled",
        "runtime_gating_enabled",
        "billing_enabled",
        "payments_enabled",
        "stripe_enabled",
        "payment_provider_enabled",
        "provider_execution_enabled",
        "external_api_calls_enabled",
        "authentication_changes_enabled",
        "deployment_automation_enabled",
        "rollout_execution_enabled",
        "background_workers_enabled",
        "cron_enabled",
        "webhook_execution_enabled",
        "email_sending_enabled",
        "sms_sending_enabled",
        "notifications_enabled",
        "ai_execution_enabled",
        "openai_enabled",
        "scraping_enabled",
        "publishing_enabled",
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
    summary = FeatureBundleRolloutApprovalSummary(
        total_count=2,
        by_status={"submitted": 1, "under_review": 1},
        submitted_count=1,
        under_review_count=1,
    )
    timeline = FeatureBundleRolloutApprovalTimelineEntry(
        approval_id="approval-smoke",
        rollout_plan_id="plan-smoke",
        agency_id="agency-smoke",
        event_type="approval_reviewed",
        status="under_review",
        actor="smoke",
        notes="Metadata-only timeline entry.",
    )
    approval = FeatureBundleRolloutApproval(
        approval_id="approval-smoke",
        rollout_plan_id="plan-smoke",
        agency_id="agency-smoke",
        bundle_id="bundle-smoke",
        status="under_review",
        reviewer="Platform Ops",
        approval_summary=summary,
        timeline=[timeline],
        notes="Metadata-only approval model smoke.",
    )
    note = FeatureBundleRolloutApprovalNote(
        approval_id="approval-smoke",
        rollout_plan_id="plan-smoke",
        agency_id="agency-smoke",
        note_text="Metadata-only approval note.",
        agency_visible=True,
    )
    create_payload = FeatureBundleRolloutApprovalCreate(
        rollout_plan_id="plan-smoke",
        agency_id="agency-smoke",
        status="submitted",
        reviewer="Platform Ops",
    )
    dumped = approval.model_dump(mode="json")
    dumped_note = note.model_dump(mode="json")
    if dumped.get("status") != "under_review":
        raise AssertionError(f"Approval status was not preserved: {dumped}")
    if create_payload.model_dump(mode="json").get("status") != "submitted":
        raise AssertionError("Approval create model did not preserve submitted status.")
    assert_disabled_response(dumped)
    if dumped_note.get("metadata_only") is not True or dumped_note.get("read_only_for_agency") is not True:
        raise AssertionError(f"Approval note model should be metadata-only/read-only for agency: {dumped_note}")
    for collection in ["feature_bundle_rollout_approvals", "feature_bundle_rollout_approval_notes"]:
        if collection not in AGENCY_OWNED_COLLECTIONS:
            raise AssertionError(f"Rollout approval collection is not registered: {collection}")
    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "feature_bundle_rollout_approvals_id_unique",
        "feature_bundle_rollout_approvals_approval_unique",
        "feature_bundle_rollout_approvals_plan_lookup",
        "feature_bundle_rollout_approvals_agency_status_lookup",
        "feature_bundle_rollout_approvals_status_created_lookup",
        "feature_bundle_rollout_approvals_approved_by_created_lookup",
        "feature_bundle_rollout_approvals_created_lookup",
        "feature_bundle_rollout_approval_notes_id_unique",
        "feature_bundle_rollout_approval_notes_note_unique",
        "feature_bundle_rollout_approval_notes_approval_created_lookup",
        "feature_bundle_rollout_approval_notes_plan_created_lookup",
        "feature_bundle_rollout_approval_notes_agency_created_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Rollout approval index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    expected_methods = {
        "/api/platform/feature-bundle-rollout-approvals": {"get", "post"},
        "/api/platform/feature-bundle-rollout-approvals/summary": {"get"},
        "/api/platform/feature-bundle-rollout-approvals/{approval_id}": {"get", "put"},
        "/api/platform/feature-bundle-rollout-approvals/{approval_id}/notes": {"get", "post"},
        "/api/platform/feature-bundle-rollout-approvals/{approval_id}/timeline": {"get"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-approvals": {"get"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-approvals/summary": {"get"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-approvals/{approval_id}": {"get"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-approvals/{approval_id}/notes": {"get"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-approvals/{approval_id}/timeline": {"get"},
    }
    for path, methods in expected_methods.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in [
        "/api/agencies/{agency_id}/feature-bundle-rollout-approvals",
        "/api/agencies/{agency_id}/feature-bundle-rollout-approvals/summary",
        "/api/agencies/{agency_id}/feature-bundle-rollout-approvals/{approval_id}",
        "/api/agencies/{agency_id}/feature-bundle-rollout-approvals/{approval_id}/notes",
        "/api/agencies/{agency_id}/feature-bundle-rollout-approvals/{approval_id}/timeline",
    ]:
        methods = set(paths.get(path, {}).keys())
        blocked_methods = methods & {"post", "put", "patch", "delete"}
        if blocked_methods:
            raise AssertionError(f"Agency rollout approval route is not read-only: {path} {sorted(blocked_methods)}")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Feature Bundle Rollout Approvals"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Rollout Approval"),
        (ROOT / "frontend/src/App.jsx", "/platform/feature-bundle-rollout-approvals"),
        (ROOT / "frontend/src/App.jsx", "/agency/rollout-approval"),
        (ROOT / "frontend/src/pages/platform/FeatureBundleRolloutApprovalsPage.jsx", "Feature Bundle Rollout Approvals"),
        (ROOT / "frontend/src/pages/platform/FeatureBundleRolloutApprovalsPage.jsx", "Approval records are metadata only"),
        (ROOT / "frontend/src/pages/agency/RolloutApprovalPage.jsx", "Rollout Approval"),
        (ROOT / "frontend/src/pages/agency/RolloutApprovalPage.jsx", "Read-only approval metadata"),
        (ROOT / "docs/architecture/feature-bundle-rollout-approval-foundation.md", "Feature Bundle Rollout Approval Foundation"),
        (ROOT / "README.md", "Phase 40.4 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 40.4: Feature Bundle Rollout Approval Foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "Phase 40.4 adds feature bundle rollout approval metadata"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "Phase 40.4 adds feature bundle rollout approval APIs"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Feature bundle rollout approvals"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Feature bundle rollout approvals"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/FeatureBundleRolloutApprovalsPage.jsx",
        ROOT / "frontend/src/pages/agency/RolloutApprovalPage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)
    reject_text(ROOT / "frontend/src/pages/agency/RolloutApprovalPage.jsx", "<button")
    reject_text(ROOT / "frontend/src/pages/agency/RolloutApprovalPage.jsx", "onClick=")


def verify_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")
    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("feature_bundle_rollout_approval_foundation") or {}
    for flag in [
        "feature_bundle_rollout_approvals_enabled",
        "feature_bundle_rollout_approval_notes_enabled",
        "platform_rollout_approval_metadata_crud_enabled",
        "platform_rollout_approval_notes_metadata_enabled",
        "agency_rollout_approval_read_only_enabled",
        "approval_status_metadata_enabled",
        "approval_summary_enabled",
        "approval_timeline_enabled",
        "approval_note_visibility_enabled",
        "metadata_only",
        "read_only_visibility_only",
        "actual_feature_enablement_disabled",
    ]:
        require_flag(section, flag)
    for flag in disabled_flags():
        require_flag(section, flag)
    require_flag(section, "readiness_required", False)
    for count_key in ["approval_count", "approval_note_count", "approval_status_counts"]:
        if count_key not in section:
            raise AssertionError(f"Rollout approval readiness missing count: {count_key}")
    status_counts = section.get("approval_status_counts") or {}
    if not APPROVAL_STATUSES.issubset(set(status_counts.keys())):
        raise AssertionError(f"Approval readiness status counts missing statuses: {section}")
    previous_section = readiness.get("rollout_dashboard_foundation") or {}
    if previous_section.get("metadata_only") is not True or previous_section.get("read_only") is not True:
        raise AssertionError("Previous rollout dashboard section should remain read-only metadata.")


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
            "plan_name": "Phase 40.4 smoke rollout approval plan",
            "rollout_stage": "readiness_review",
            "target_start_date": "2026-09-01",
            "target_end_date": "2026-09-15",
            "rollout_owner": "Platform Ops",
            "checklist_summary": {"counts": {"passed": 2, "warning": 1, "blocked": 0}, "metadata_only": True},
            "notes": "Plan metadata for rollout approval smoke.",
        },
        OWNER_HEADERS,
        201,
    )
    rollout_plan_id = (plan_response.get("plan") or {}).get("rollout_plan_id")
    if not rollout_plan_id:
        raise AssertionError(f"Rollout plan was not created for approval smoke: {plan_response}")

    created = post(
        "/api/platform/feature-bundle-rollout-approvals",
        {
            "rollout_plan_id": rollout_plan_id,
            "agency_id": agency_id,
            "status": "submitted",
            "reviewer": "Platform Ops",
            "notes": "Metadata-only approval smoke note.",
        },
        OWNER_HEADERS,
        201,
    )
    if created.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected create phase: {created.get('phase')}")
    assert_disabled_response(created)
    approval = created.get("approval") or {}
    assert_approval_shape(approval)
    approval_id = approval.get("approval_id")
    if not approval_id:
        raise AssertionError(f"Approval id missing: {created}")
    if approval.get("status") != "submitted":
        raise AssertionError(f"Submitted status was not persisted: {created}")

    updated = put(
        f"/api/platform/feature-bundle-rollout-approvals/{approval_id}",
        {
            "status": "approved",
            "approved_by": "Platform Ops",
            "notes": "Approved as metadata only; no rollout execution.",
        },
        OWNER_HEADERS,
    )
    assert_disabled_response(updated)
    updated_approval = updated.get("approval") or {}
    assert_approval_shape(updated_approval)
    if updated_approval.get("status") != "approved" or not updated_approval.get("approved_at"):
        raise AssertionError(f"Approval update did not persist approved metadata: {updated}")

    visible_note = post(
        f"/api/platform/feature-bundle-rollout-approvals/{approval_id}/notes",
        {"note_text": "Agency-visible approval review note.", "note_type": "review_note", "agency_visible": True},
        OWNER_HEADERS,
        201,
    )
    assert_disabled_response(visible_note)
    if (visible_note.get("note") or {}).get("agency_visible") is not True:
        raise AssertionError(f"Visible approval note malformed: {visible_note}")

    hidden_note = post(
        f"/api/platform/feature-bundle-rollout-approvals/{approval_id}/notes",
        {"note_text": "Internal platform-only approval note.", "note_type": "internal_note", "agency_visible": False},
        OWNER_HEADERS,
        201,
    )
    assert_disabled_response(hidden_note)

    platform_list = get("/api/platform/feature-bundle-rollout-approvals", OWNER_HEADERS)
    assert_disabled_response(platform_list)
    listed = next((item for item in platform_list.get("items") or [] if item.get("approval_id") == approval_id), None)
    if not listed:
        raise AssertionError(f"Platform rollout approval list missing created approval: {platform_list}")
    assert_approval_shape(listed)

    platform_summary = get("/api/platform/feature-bundle-rollout-approvals/summary", OWNER_HEADERS)
    assert_summary_shape(platform_summary)

    platform_detail = get(f"/api/platform/feature-bundle-rollout-approvals/{approval_id}", OWNER_HEADERS)
    assert_disabled_response(platform_detail)
    assert_approval_shape(platform_detail.get("approval") or {})

    platform_notes = get(f"/api/platform/feature-bundle-rollout-approvals/{approval_id}/notes", OWNER_HEADERS)
    assert_notes_shape(platform_notes, approval_id=approval_id, agency_view=False)
    if not any(note.get("agency_visible") is False for note in platform_notes.get("items") or []):
        raise AssertionError(f"Platform notes should include platform-only approval note metadata: {platform_notes}")

    platform_timeline = get(f"/api/platform/feature-bundle-rollout-approvals/{approval_id}/timeline", OWNER_HEADERS)
    assert_timeline_shape(platform_timeline, approval_id=approval_id, agency_view=False)

    agency_list = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-approvals", OWNER_HEADERS)
    assert_disabled_response(agency_list)
    if agency_list.get("read_only") is not True:
        raise AssertionError(f"Agency rollout approval list should be read-only: {agency_list}")
    agency_item = next((item for item in agency_list.get("items") or [] if item.get("approval_id") == approval_id), None)
    if not agency_item:
        raise AssertionError(f"Agency rollout approval list missing created approval: {agency_list}")
    assert_approval_shape(agency_item, agency_view=True)
    if "Internal platform-only approval note." in str(agency_item):
        raise AssertionError(f"Agency approval item leaked platform-only note text: {agency_item}")

    agency_summary = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-approvals/summary", OWNER_HEADERS)
    assert_summary_shape(agency_summary, agency_id=agency_id)
    if agency_summary.get("read_only") is not True:
        raise AssertionError(f"Agency rollout approval summary should be read-only: {agency_summary}")

    agency_detail = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-approvals/{approval_id}", OWNER_HEADERS)
    assert_disabled_response(agency_detail)
    if agency_detail.get("read_only") is not True:
        raise AssertionError(f"Agency rollout approval detail should be read-only: {agency_detail}")
    assert_approval_shape(agency_detail.get("approval") or {}, agency_view=True)
    if "Internal platform-only approval note." in str(agency_detail):
        raise AssertionError(f"Agency approval detail leaked platform-only note text: {agency_detail}")

    agency_notes = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-approvals/{approval_id}/notes", OWNER_HEADERS)
    assert_notes_shape(agency_notes, approval_id=approval_id, agency_view=True)
    if any(note.get("agency_visible") is False for note in agency_notes.get("items") or []):
        raise AssertionError(f"Agency notes should hide platform-only note metadata: {agency_notes}")
    if "Internal platform-only approval note." in str(agency_notes):
        raise AssertionError(f"Agency notes leaked platform-only note text: {agency_notes}")

    agency_timeline = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-approvals/{approval_id}/timeline", OWNER_HEADERS)
    assert_timeline_shape(agency_timeline, approval_id=approval_id, agency_view=True)
    if "Internal platform-only approval note." in str(agency_timeline):
        raise AssertionError(f"Agency timeline leaked platform-only note text: {agency_timeline}")

    request("POST", f"/api/agencies/{agency_id}/feature-bundle-rollout-approvals", {"rollout_plan_id": rollout_plan_id}, OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/feature-bundle-rollout-approvals/{approval_id}", {"status": "rejected"}, OWNER_HEADERS, 405)
    request("POST", f"/api/agencies/{agency_id}/feature-bundle-rollout-approvals/{approval_id}/notes", {"note_text": "blocked"}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/feature-bundle-rollout-approvals/{approval_id}", {}, OWNER_HEADERS, 405)


def assert_approval_shape(approval: dict, *, agency_view: bool = False) -> None:
    for key in [
        "approval_id",
        "rollout_plan_id",
        "agency_id",
        "bundle_id",
        "status",
        "plan_name",
        "rollout_stage",
        "agency_name",
        "bundle_key",
        "bundle_name",
        "timeline",
        "notes_list",
        "note_count",
        "metadata_only",
        "approval_metadata_only",
    ]:
        if key not in approval:
            raise AssertionError(f"Approval missing {key}: {approval}")
    if approval.get("status") not in APPROVAL_STATUSES:
        raise AssertionError(f"Approval status is invalid: {approval}")
    if agency_view and approval.get("payloads_hidden") is not True:
        raise AssertionError(f"Agency approval should hide payloads: {approval}")
    assert_disabled_response(approval)
    if not isinstance(approval.get("timeline"), list) or not isinstance(approval.get("notes_list"), list):
        raise AssertionError(f"Approval timeline/notes should be lists: {approval}")


def assert_summary_shape(payload: dict, *, agency_id: str | None = None) -> None:
    if payload.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected summary phase: {payload}")
    if agency_id is not None and payload.get("agency_id") != agency_id:
        raise AssertionError(f"Agency approval summary did not stay agency-scoped: {payload}")
    assert_disabled_response(payload)
    summary = payload.get("summary") or {}
    if "by_status" not in summary or "total_count" not in summary:
        raise AssertionError(f"Approval summary malformed: {payload}")
    if not APPROVAL_STATUSES.issubset(set((summary.get("by_status") or {}).keys())):
        raise AssertionError(f"Approval summary missing statuses: {payload}")


def assert_notes_shape(payload: dict, *, approval_id: str, agency_view: bool) -> None:
    if payload.get("phase") != EXPECTED_PHASE or payload.get("approval_id") != approval_id:
        raise AssertionError(f"Approval notes response malformed: {payload}")
    if agency_view and payload.get("read_only") is not True:
        raise AssertionError(f"Agency approval notes should be read-only: {payload}")
    assert_disabled_response(payload)
    if not isinstance(payload.get("items"), list) or "note_count" not in payload:
        raise AssertionError(f"Approval notes shape malformed: {payload}")
    for note in payload.get("items") or []:
        for key in ["note_id", "approval_id", "rollout_plan_id", "agency_id", "note_text", "note_type", "metadata_only"]:
            if key not in note:
                raise AssertionError(f"Approval note missing {key}: {note}")
        if note.get("metadata_only") is not True:
            raise AssertionError(f"Approval note should be metadata-only: {note}")


def assert_timeline_shape(payload: dict, *, approval_id: str, agency_view: bool) -> None:
    if payload.get("phase") != EXPECTED_PHASE or payload.get("approval_id") != approval_id:
        raise AssertionError(f"Approval timeline response malformed: {payload}")
    if agency_view and payload.get("read_only") is not True:
        raise AssertionError(f"Agency approval timeline should be read-only: {payload}")
    assert_disabled_response(payload)
    if not isinstance(payload.get("items"), list) or "timeline_count" not in payload:
        raise AssertionError(f"Approval timeline shape malformed: {payload}")
    if not payload.get("items"):
        raise AssertionError(f"Approval timeline should include metadata entries: {payload}")
    for entry in payload.get("items") or []:
        for key in ["timeline_entry_id", "rollout_plan_id", "agency_id", "event_type", "metadata_only", "execution_disabled"]:
            if key not in entry:
                raise AssertionError(f"Approval timeline entry missing {key}: {entry}")
        if entry.get("metadata_only") is not True or entry.get("execution_disabled") is not True:
            raise AssertionError(f"Approval timeline entry should be metadata-only/no execution: {entry}")


def main() -> int:
    verify_model_and_collection_registration()
    verify_readiness()
    openapi = get("/openapi.json")
    paths = openapi.get("paths") or {}
    verify_routes(paths)
    verify_frontend_and_docs()
    verify_endpoint_behavior()
    print("Phase 40.4 feature bundle rollout approval foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Phase 40.4 feature bundle rollout approval foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
