#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import (
    FeatureBundleRolloutSummaryPack,
    FeatureBundleRolloutSummaryPackAudience,
    FeatureBundleRolloutSummaryPackCreate,
    FeatureBundleRolloutSummaryPackStatus,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request
from smoke_feature_bundle_rollout_rollback_plan_foundation import (
    create_change_request,
    create_decision,
    create_dependency,
    create_issue,
    create_risk,
)


EXPECTED_PHASE = "phase_41_7_ticket_workspace_foundation"
ROOT = Path(__file__).resolve().parents[2]
PACK_STATUSES = {"draft", "assembled", "reviewing", "ready", "archived"}
PACK_AUDIENCES = {"platform", "agency", "operations", "compliance", "executive"}


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
        "deployment_automation_disabled",
        "feature_activation_disabled",
        "feature_deactivation_disabled",
        "feature_bundle_activation_disabled",
        "feature_bundle_deactivation_disabled",
        "entitlement_enforcement_disabled",
        "billing_disabled",
        "provider_integrations_disabled",
        "provider_calls_disabled",
        "provider_execution_disabled",
        "external_api_calls_disabled",
        "ai_execution_disabled",
        "external_ai_disabled",
        "background_workers_disabled",
        "schedulers_disabled",
        "notification_sending_disabled",
        "notifications_disabled",
        "email_sending_disabled",
        "webhook_execution_disabled",
        "publishing_disabled",
        "runtime_switching_disabled",
        "pdf_generation_disabled",
        "file_export_disabled",
        "automation_disabled",
    ]


def forbidden_enabled_flags() -> list[str]:
    return [
        "rollout_execution_enabled",
        "deployment_automation_enabled",
        "feature_activation_enabled",
        "feature_deactivation_enabled",
        "feature_bundle_activation_enabled",
        "feature_bundle_deactivation_enabled",
        "entitlement_enforcement_enabled",
        "billing_enabled",
        "provider_integrations_enabled",
        "provider_calls_enabled",
        "ai_execution_enabled",
        "external_api_calls_enabled",
        "background_workers_enabled",
        "schedulers_enabled",
        "notifications_enabled",
        "email_sending_enabled",
        "webhook_execution_enabled",
        "publishing_enabled",
        "runtime_switching_enabled",
        "pdf_generation_enabled",
        "file_export_enabled",
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
    create_payload = FeatureBundleRolloutSummaryPackCreate(
        id="summary-pack-smoke",
        rollout_plan_id="plan-smoke",
        pack_title="Summary pack smoke",
        pack_summary="Summary pack metadata smoke.",
        pack_status=FeatureBundleRolloutSummaryPackStatus.ASSEMBLED,
        generated_for_audience=FeatureBundleRolloutSummaryPackAudience.AGENCY,
        covered_bundle_ids=["bundle-smoke"],
        readiness_reference_ids=["readiness-smoke"],
        approval_reference_ids=["approval-smoke"],
        schedule_reference_ids=["schedule-smoke"],
        timeline_reference_ids=["timeline-smoke"],
        dependency_reference_ids=["dependency-smoke"],
        risk_reference_ids=["risk-smoke"],
        issue_reference_ids=["issue-smoke"],
        decision_reference_ids=["decision-smoke"],
        change_request_reference_ids=["change-request-smoke"],
        rollback_plan_reference_ids=["rollback-plan-smoke"],
        evidence_notes="Evidence metadata only.",
        compliance_notes="Compliance metadata only.",
        metadata={"smoke": True},
    )
    pack = FeatureBundleRolloutSummaryPack(**create_payload.model_dump(mode="json", exclude_none=True))
    dumped = pack.model_dump(mode="json")
    if dumped.get("pack_status") != "assembled" or dumped.get("generated_for_audience") != "agency":
        raise AssertionError(f"Summary pack dimensions were not preserved: {dumped}")
    for key in [
        "metadata_only",
        "summary_pack_metadata_only",
        "rollout_execution_disabled",
        "deployment_automation_disabled",
        "feature_activation_disabled",
        "feature_deactivation_disabled",
        "feature_bundle_activation_disabled",
        "feature_bundle_deactivation_disabled",
        "entitlement_enforcement_disabled",
        "billing_disabled",
        "provider_integrations_disabled",
        "external_api_calls_disabled",
        "ai_execution_disabled",
        "background_workers_disabled",
        "schedulers_disabled",
        "notification_sending_disabled",
        "email_sending_disabled",
        "webhook_execution_disabled",
        "publishing_disabled",
        "runtime_switching_disabled",
        "pdf_generation_disabled",
        "file_export_disabled",
        "automation_disabled",
    ]:
        if dumped.get(key) is not True:
            raise AssertionError(f"Summary pack model missing disabled flag {key}: {dumped}")
    if "feature_bundle_rollout_summary_packs" not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("Feature bundle rollout summary packs collection is not registered.")
    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "feature_bundle_rollout_summary_packs_id_unique",
        "feature_bundle_rollout_summary_packs_plan_status_lookup",
        "feature_bundle_rollout_summary_packs_status_audience_lookup",
        "feature_bundle_rollout_summary_packs_audience_lookup",
        "feature_bundle_rollout_summary_packs_bundle_lookup",
        "feature_bundle_rollout_summary_packs_readiness_lookup",
        "feature_bundle_rollout_summary_packs_approval_lookup",
        "feature_bundle_rollout_summary_packs_schedule_lookup",
        "feature_bundle_rollout_summary_packs_timeline_lookup",
        "feature_bundle_rollout_summary_packs_dependency_lookup",
        "feature_bundle_rollout_summary_packs_risk_lookup",
        "feature_bundle_rollout_summary_packs_issue_lookup",
        "feature_bundle_rollout_summary_packs_decision_lookup",
        "feature_bundle_rollout_summary_packs_change_request_lookup",
        "feature_bundle_rollout_summary_packs_rollback_plan_lookup",
        "feature_bundle_rollout_summary_packs_created_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Feature bundle rollout summary pack index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    expected_methods = {
        "/api/platform/feature-bundle-rollout-summary-packs": {"get", "post"},
        "/api/platform/feature-bundle-rollout-summary-packs/summary": {"get"},
        "/api/platform/feature-bundle-rollout-summary-packs/{pack_id}": {"get", "put", "delete"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-summary-packs": {"get"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-summary-packs/summary": {"get"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-summary-packs/{pack_id}": {"get"},
    }
    for path, methods in expected_methods.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in [
        "/api/agencies/{agency_id}/feature-bundle-rollout-summary-packs",
        "/api/agencies/{agency_id}/feature-bundle-rollout-summary-packs/summary",
        "/api/agencies/{agency_id}/feature-bundle-rollout-summary-packs/{pack_id}",
    ]:
        methods = set(paths.get(path, {}).keys())
        blocked_methods = methods & {"post", "put", "patch", "delete"}
        if blocked_methods:
            raise AssertionError(f"Agency feature bundle rollout summary pack route is not read-only: {path} {sorted(blocked_methods)}")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Feature Bundle Rollout Summary Packs"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Rollout Summary Packs"),
        (ROOT / "frontend/src/App.jsx", "/platform/feature-bundle-rollout-summary-packs"),
        (ROOT / "frontend/src/App.jsx", "/agency/rollout-summary-packs"),
        (ROOT / "frontend/src/pages/platform/FeatureBundleRolloutSummaryPacksPage.jsx", "Feature Bundle Rollout Summary Packs"),
        (ROOT / "frontend/src/pages/platform/FeatureBundleRolloutSummaryPacksPage.jsx", "No PDF or export"),
        (ROOT / "frontend/src/pages/platform/FeatureBundleRolloutSummaryPacksPage.jsx", "Evidence references"),
        (ROOT / "frontend/src/pages/agency/RolloutSummaryPacksPage.jsx", "Rollout Summary Packs"),
        (ROOT / "frontend/src/pages/agency/RolloutSummaryPacksPage.jsx", "Read-only rollout summary evidence-pack metadata"),
        (ROOT / "docs/architecture/feature-bundle-rollout-summary-pack-foundation.md", "Feature Bundle Rollout Summary Pack Foundation"),
        (ROOT / "README.md", "Phase 40.13 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 40.13: Feature Bundle Rollout Summary Pack Foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "Phase 40.13 adds feature bundle rollout summary pack metadata"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "Phase 40.13 adds feature bundle rollout summary pack APIs"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Feature bundle rollout summary packs"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Feature bundle rollout summary packs"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/FeatureBundleRolloutSummaryPacksPage.jsx",
        ROOT / "frontend/src/pages/agency/RolloutSummaryPacksPage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)
    for path in [
        ROOT / "frontend/src/pages/platform/FeatureBundleRolloutSummaryPacksPage.jsx",
        ROOT / "frontend/src/pages/agency/RolloutSummaryPacksPage.jsx",
    ]:
        reject_text(path, "<button")
        reject_text(path, "apiPost")
        reject_text(path, "apiPut")


def verify_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")
    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("feature_bundle_rollout_summary_pack_foundation") or {}
    for flag in [
        "feature_bundle_rollout_summary_packs_enabled",
        "feature_bundle_rollout_summary_pack_status_metadata_enabled",
        "feature_bundle_rollout_summary_pack_audience_metadata_enabled",
        "platform_summary_pack_metadata_crud_enabled",
        "agency_summary_pack_read_only_enabled",
        "summary_pack_filter_by_rollout_enabled",
        "summary_pack_filter_by_status_enabled",
        "summary_pack_filter_by_audience_enabled",
        "summary_pack_filter_by_bundle_enabled",
        "summary_pack_covered_bundle_references_enabled",
        "summary_pack_readiness_references_enabled",
        "summary_pack_approval_references_enabled",
        "summary_pack_schedule_references_enabled",
        "summary_pack_timeline_references_enabled",
        "summary_pack_dependency_references_enabled",
        "summary_pack_risk_references_enabled",
        "summary_pack_issue_references_enabled",
        "summary_pack_decision_references_enabled",
        "summary_pack_change_request_references_enabled",
        "summary_pack_rollback_plan_references_enabled",
        "evidence_notes_metadata_enabled",
        "compliance_notes_metadata_enabled",
        "metadata_only",
        "summary_pack_metadata_only",
        "summary_pack_records_informational_only",
        "read_only_ui_enabled",
    ]:
        require_flag(section, flag)
    for flag in disabled_flags():
        require_flag(section, flag)
    require_flag(section, "readiness_required", False)
    for count_key in ["summary_pack_count", "summary_pack_status_counts", "summary_pack_audience_counts"]:
        if count_key not in section:
            raise AssertionError(f"Summary pack readiness missing count: {count_key}")
    if not PACK_STATUSES.issubset(set((section.get("summary_pack_status_counts") or {}).keys())):
        raise AssertionError(f"Summary pack readiness status counts missing statuses: {section}")
    if not PACK_AUDIENCES.issubset(set((section.get("summary_pack_audience_counts") or {}).keys())):
        raise AssertionError(f"Summary pack readiness audience counts missing audiences: {section}")
    previous_section = readiness.get("feature_bundle_rollout_rollback_plan_foundation") or {}
    if previous_section.get("metadata_only") is not True:
        raise AssertionError("Previous rollback plan section should remain metadata-only.")


def verify_endpoint_behavior() -> None:
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires seeded demo agency.")
    agency_id = agencies[0]["id"]
    bundles = get("/api/platform/feature-flag-bundles", OWNER_HEADERS).get("items") or []
    if not bundles:
        raise AssertionError("Smoke requires feature flag bundle metadata.")
    bundle_id = next((item["bundle_id"] for item in bundles if item.get("bundle_key") == "core_agency"), bundles[0]["bundle_id"])

    rollout_plan_id = create_rollout_plan(agency_id, bundle_id)
    readiness_id = create_readiness_reference(agency_id, bundle_id)
    approval_id = create_approval(agency_id, rollout_plan_id)
    schedule_id = create_schedule(agency_id, bundle_id, rollout_plan_id, approval_id)
    timeline_entry_id = create_timeline_entry(agency_id, bundle_id, rollout_plan_id)
    dependency_id = create_dependency(agency_id, bundle_id, rollout_plan_id)
    risk_id = create_risk(agency_id, bundle_id, rollout_plan_id, dependency_id)
    issue_id = create_issue(agency_id, bundle_id, rollout_plan_id, risk_id, dependency_id)
    decision_id = create_decision(bundle_id, rollout_plan_id, dependency_id, risk_id, issue_id)
    change_request_id = create_change_request(bundle_id, rollout_plan_id, dependency_id, risk_id, issue_id, decision_id)
    rollback_plan_id = create_rollback_plan(bundle_id, rollout_plan_id, dependency_id, risk_id, issue_id, decision_id, change_request_id)

    created = post(
        "/api/platform/feature-bundle-rollout-summary-packs",
        {
            "rollout_plan_id": rollout_plan_id,
            "pack_title": "Summary evidence pack metadata",
            "pack_summary": "Summary pack smoke record for metadata-only rollout evidence.",
            "pack_status": "assembled",
            "generated_for_audience": "agency",
            "covered_bundle_ids": [bundle_id],
            "readiness_reference_ids": [readiness_id],
            "approval_reference_ids": [approval_id],
            "schedule_reference_ids": [schedule_id],
            "timeline_reference_ids": [timeline_entry_id],
            "dependency_reference_ids": [dependency_id],
            "risk_reference_ids": [risk_id],
            "issue_reference_ids": [issue_id],
            "decision_reference_ids": [decision_id],
            "change_request_reference_ids": [change_request_id],
            "rollback_plan_reference_ids": [rollback_plan_id],
            "evidence_notes": "Evidence notes are metadata only. No PDF generation.",
            "compliance_notes": "Compliance notes are metadata only. No file export.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    if created.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected create phase: {created.get('phase')}")
    assert_disabled_response(created)
    summary_pack = created.get("summary_pack") or {}
    assert_summary_pack_shape(summary_pack)
    pack_id = summary_pack.get("id")
    if not pack_id:
        raise AssertionError(f"Summary pack id missing: {created}")

    updated = put(
        f"/api/platform/feature-bundle-rollout-summary-packs/{pack_id}",
        {
            "pack_status": "ready",
            "generated_for_audience": "compliance",
            "evidence_notes": "Evidence notes updated; still no PDF generation.",
            "compliance_notes": "Compliance notes updated; still no export.",
            "metadata": {"updated": True, "metadata_only": True},
        },
        OWNER_HEADERS,
    )
    assert_disabled_response(updated)
    updated_pack = updated.get("summary_pack") or {}
    assert_summary_pack_shape(updated_pack)
    if updated_pack.get("pack_status") != "ready" or updated_pack.get("generated_for_audience") != "compliance":
        raise AssertionError(f"Summary pack update did not persist metadata: {updated}")

    for filter_query in [
        f"rollout_plan_id={rollout_plan_id}",
        "status=ready",
        "audience=compliance",
        f"bundle_id={bundle_id}",
    ]:
        filtered = get(f"/api/platform/feature-bundle-rollout-summary-packs?{filter_query}", OWNER_HEADERS)
        assert_disabled_response(filtered)
        if not any(item.get("id") == pack_id for item in filtered.get("items") or []):
            raise AssertionError(f"Summary pack filter {filter_query} missing created record: {filtered}")

    platform_summary = get("/api/platform/feature-bundle-rollout-summary-packs/summary", OWNER_HEADERS)
    assert_summary_shape(platform_summary)

    platform_detail = get(f"/api/platform/feature-bundle-rollout-summary-packs/{pack_id}", OWNER_HEADERS)
    assert_disabled_response(platform_detail)
    assert_summary_pack_shape(platform_detail.get("summary_pack") or {})

    agency_list = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-summary-packs?status=ready", OWNER_HEADERS)
    assert_disabled_response(agency_list)
    if agency_list.get("read_only") is not True:
        raise AssertionError(f"Agency summary pack list should be read-only: {agency_list}")
    agency_item = next((item for item in agency_list.get("items") or [] if item.get("id") == pack_id), None)
    if not agency_item:
        raise AssertionError(f"Agency summary pack list missing created record: {agency_list}")
    assert_summary_pack_shape(agency_item, agency_view=True)

    agency_summary = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-summary-packs/summary", OWNER_HEADERS)
    assert_summary_shape(agency_summary, agency_id=agency_id)
    if agency_summary.get("read_only") is not True:
        raise AssertionError(f"Agency summary pack summary should be read-only: {agency_summary}")

    agency_detail = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-summary-packs/{pack_id}", OWNER_HEADERS)
    assert_disabled_response(agency_detail)
    if agency_detail.get("read_only") is not True:
        raise AssertionError(f"Agency summary pack detail should be read-only: {agency_detail}")
    assert_summary_pack_shape(agency_detail.get("summary_pack") or {}, agency_view=True)

    deleted = request("DELETE", f"/api/platform/feature-bundle-rollout-summary-packs/{pack_id}", {}, OWNER_HEADERS)[1]
    assert_disabled_response(deleted)
    if deleted.get("deleted") is not True or (deleted.get("summary_pack") or {}).get("pack_status") != "archived":
        raise AssertionError(f"Summary pack delete should be metadata-only archive: {deleted}")

    after_delete = get(f"/api/platform/feature-bundle-rollout-summary-packs?rollout_plan_id={rollout_plan_id}", OWNER_HEADERS)
    if any(item.get("id") == pack_id for item in after_delete.get("items") or []):
        raise AssertionError(f"Default summary pack list should exclude archived-delete metadata: {after_delete}")
    include_archived = get(f"/api/platform/feature-bundle-rollout-summary-packs?rollout_plan_id={rollout_plan_id}&include_archived=true", OWNER_HEADERS)
    if not any(item.get("id") == pack_id for item in include_archived.get("items") or []):
        raise AssertionError(f"include_archived should expose metadata-archived summary pack: {include_archived}")

    request("POST", f"/api/agencies/{agency_id}/feature-bundle-rollout-summary-packs", {"pack_title": "blocked"}, OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/feature-bundle-rollout-summary-packs/{pack_id}", {"pack_status": "draft"}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/feature-bundle-rollout-summary-packs/{pack_id}", {}, OWNER_HEADERS, 405)


def create_rollout_plan(agency_id: str, bundle_id: str) -> str:
    response = post(
        "/api/platform/feature-bundle-rollout-plans",
        {
            "agency_id": agency_id,
            "bundle_id": bundle_id,
            "plan_name": "Phase 40.13 smoke summary pack rollout plan",
            "rollout_stage": "readiness_review",
            "target_start_date": "2027-06-10",
            "target_end_date": "2027-06-20",
            "rollout_owner": "Platform Ops",
            "checklist_summary": {"counts": {"passed": 3, "warning": 1, "blocked": 0}, "metadata_only": True},
            "notes": "Summary pack smoke rollout plan metadata only.",
        },
        OWNER_HEADERS,
        201,
    )
    rollout_plan_id = (response.get("plan") or {}).get("rollout_plan_id")
    if not rollout_plan_id:
        raise AssertionError(f"Rollout plan was not created for summary pack smoke: {response}")
    return rollout_plan_id


def create_readiness_reference(agency_id: str, bundle_id: str) -> str:
    assignment = post(
        f"/api/platform/agencies/{agency_id}/bundle-assignments",
        {
            "bundle_id": bundle_id,
            "effective_date": "2027-06-01",
            "status": "assigned",
            "review_status": "pending_review",
            "notes": "Summary pack smoke readiness assignment.",
        },
        OWNER_HEADERS,
        201,
    )
    assignment_id = (assignment.get("assignment") or {}).get("assignment_id")
    if not assignment_id:
        raise AssertionError(f"Assignment was not created for summary pack smoke: {assignment}")
    post("/api/platform/feature-bundle-rollout-readiness/defaults", {}, OWNER_HEADERS, 201)
    readiness = get("/api/platform/feature-bundle-rollout-readiness", OWNER_HEADERS)
    item = next((entry for entry in readiness.get("items") or [] if entry.get("assignment_id") == assignment_id), None)
    if not item:
        raise AssertionError(f"Readiness record was not created for summary pack smoke: {readiness}")
    return item.get("id") or assignment_id


def create_approval(agency_id: str, rollout_plan_id: str) -> str:
    response = post(
        "/api/platform/feature-bundle-rollout-approvals",
        {
            "rollout_plan_id": rollout_plan_id,
            "agency_id": agency_id,
            "status": "approved",
            "reviewer": "Platform Ops",
            "notes": "Approval metadata for summary pack smoke.",
        },
        OWNER_HEADERS,
        201,
    )
    approval_id = (response.get("approval") or {}).get("approval_id")
    if not approval_id:
        raise AssertionError(f"Approval was not created for summary pack smoke: {response}")
    return approval_id


def create_schedule(agency_id: str, bundle_id: str, rollout_plan_id: str, approval_id: str) -> str:
    response = post(
        "/api/platform/feature-bundle-rollout-schedule",
        {
            "rollout_plan_id": rollout_plan_id,
            "agency_id": agency_id,
            "bundle_id": bundle_id,
            "rollout_name": "Phase 40.13 summary pack schedule metadata",
            "schedule_status": "Approved",
            "planned_start": "2027-06-12T09:00:00Z",
            "planned_finish": "2027-06-12T11:00:00Z",
            "maintenance_window": "Sunday morning",
            "estimated_duration": "2 hours",
            "dependency_summary": {"approval_id": approval_id, "notes": "Approval metadata exists."},
            "scheduling_notes": "Schedule metadata only. No timers or rollout execution.",
        },
        OWNER_HEADERS,
        201,
    )
    schedule_id = (response.get("schedule") or {}).get("schedule_id")
    if not schedule_id:
        raise AssertionError(f"Schedule was not created for summary pack smoke: {response}")
    return schedule_id


def create_timeline_entry(agency_id: str, bundle_id: str, rollout_plan_id: str) -> str:
    response = post(
        "/api/platform/feature-bundle-rollout-timeline",
        {
            "rollout_plan_id": rollout_plan_id,
            "agency_id": agency_id,
            "bundle_id": bundle_id,
            "event_type": "plan_edited",
            "occurred_at": "2027-06-11T10:00:00Z",
            "description": "Summary pack smoke timeline entry metadata only.",
            "source": "smoke",
            "actor": {
                "actor_id": "platform-summary-smoke",
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
    timeline_entry_id = (response.get("entry") or {}).get("timeline_entry_id")
    if not timeline_entry_id:
        raise AssertionError(f"Timeline entry was not created for summary pack smoke: {response}")
    return timeline_entry_id


def create_rollback_plan(
    bundle_id: str,
    rollout_plan_id: str,
    dependency_id: str,
    risk_id: str,
    issue_id: str,
    decision_id: str,
    change_request_id: str,
) -> str:
    response = post(
        "/api/platform/feature-bundle-rollout-rollback-plans",
        {
            "rollout_plan_id": rollout_plan_id,
            "rollout_phase": "summary_pack",
            "rollback_title": "Summary pack rollback metadata",
            "rollback_summary": "Rollback plan reference for summary pack smoke.",
            "rollback_reason": "Summary pack needs a rollback plan reference.",
            "rollback_trigger": "manual_review",
            "rollback_scope": "bundle",
            "rollback_status": "ready",
            "rollback_owner": "Platform Ops",
            "rollback_priority": "medium",
            "affected_bundle_ids": [bundle_id],
            "affected_feature_flag_ids": ["feature_summary_smoke"],
            "related_change_request_ids": [change_request_id],
            "related_decision_ids": [decision_id],
            "related_issue_ids": [issue_id],
            "related_risk_ids": [risk_id],
            "related_dependency_ids": [dependency_id],
            "rollback_steps": ["Review summary pack metadata"],
            "validation_notes": "Rollback plan metadata only; no rollback execution.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    rollback_plan_id = (response.get("rollback_plan") or {}).get("id")
    if not rollback_plan_id:
        raise AssertionError(f"Rollback plan was not created for summary pack smoke: {response}")
    return rollback_plan_id


def assert_summary_pack_shape(pack: dict, *, agency_view: bool = False) -> None:
    for key in [
        "id",
        "rollout_plan_id",
        "pack_title",
        "pack_status",
        "generated_for_audience",
        "covered_bundle_ids",
        "readiness_reference_ids",
        "approval_reference_ids",
        "schedule_reference_ids",
        "timeline_reference_ids",
        "dependency_reference_ids",
        "risk_reference_ids",
        "issue_reference_ids",
        "decision_reference_ids",
        "change_request_reference_ids",
        "rollback_plan_reference_ids",
        "evidence_notes",
        "compliance_notes",
        "covered_bundles",
        "readiness_references",
        "approval_references",
        "schedule_references",
        "timeline_references",
        "dependency_references",
        "risk_references",
        "issue_references",
        "decision_references",
        "change_request_references",
        "rollback_plan_references",
        "metadata_only",
        "summary_pack_metadata_only",
    ]:
        if key not in pack:
            raise AssertionError(f"Summary pack response missing {key}: {pack}")
    if pack.get("pack_status") not in PACK_STATUSES:
        raise AssertionError(f"Summary pack status is invalid: {pack}")
    if pack.get("generated_for_audience") not in PACK_AUDIENCES:
        raise AssertionError(f"Summary pack audience is invalid: {pack}")
    for key in [
        "covered_bundles",
        "readiness_references",
        "approval_references",
        "schedule_references",
        "timeline_references",
        "dependency_references",
        "risk_references",
        "issue_references",
        "decision_references",
        "change_request_references",
        "rollback_plan_references",
    ]:
        if not isinstance(pack.get(key), list):
            raise AssertionError(f"Summary pack {key} should be a list: {pack}")
    for flag in disabled_flags():
        if pack.get(flag) is not True:
            raise AssertionError(f"Summary pack missing disabled flag {flag}: {pack}")
    if agency_view and pack.get("read_only") is not True:
        raise AssertionError(f"Agency summary pack projection should be read-only: {pack}")


def assert_summary_shape(payload: dict, *, agency_id: str | None = None) -> None:
    assert_disabled_response(payload)
    summary = payload.get("summary") or {}
    for key in [
        "by_status",
        "by_audience",
        "total_count",
        "rollout_count",
        "covered_bundle_count",
        "readiness_reference_count",
        "approval_reference_count",
        "schedule_reference_count",
        "timeline_reference_count",
        "dependency_reference_count",
        "risk_reference_count",
        "issue_reference_count",
        "decision_reference_count",
        "change_request_reference_count",
        "rollback_plan_reference_count",
        "archived_count",
        "pdf_generation_disabled",
        "file_export_disabled",
        "automation_disabled",
    ]:
        if key not in summary:
            raise AssertionError(f"Summary pack summary missing {key}: {payload}")
    if not PACK_STATUSES.issubset(set((summary.get("by_status") or {}).keys())):
        raise AssertionError(f"Summary pack summary missing statuses: {payload}")
    if not PACK_AUDIENCES.issubset(set((summary.get("by_audience") or {}).keys())):
        raise AssertionError(f"Summary pack summary missing audiences: {payload}")
    if agency_id and payload.get("agency_id") != agency_id:
        raise AssertionError(f"Agency summary should be scoped to {agency_id}: {payload}")


def main() -> int:
    verify_model_and_collection_registration()
    openapi = get("/openapi.json")
    verify_routes(openapi.get("paths") or {})
    verify_frontend_and_docs()
    verify_readiness()
    verify_endpoint_behavior()
    print("Phase 40.13 feature bundle rollout summary pack foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Phase 40.13 feature bundle rollout summary pack foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
