#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import (
    FeatureBundleRolloutRollbackPlan,
    FeatureBundleRolloutRollbackPlanCreate,
    FeatureBundleRolloutRollbackPriority,
    FeatureBundleRolloutRollbackScope,
    FeatureBundleRolloutRollbackStatus,
    FeatureBundleRolloutRollbackTrigger,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_42_2_passenger_service_workflow_engine_foundation"
ROOT = Path(__file__).resolve().parents[2]
ROLLBACK_TRIGGERS = {
    "manual_review",
    "issue_detected",
    "risk_threshold",
    "dependency_unready",
    "agency_request",
    "schedule_conflict",
    "operational_concern",
    "documentation_gap",
    "future_runtime_signal",
}
ROLLBACK_SCOPES = {"bundle", "feature_flag", "agency", "dependency", "schedule", "readiness", "approval", "operational", "documentation"}
ROLLBACK_STATUSES = {"draft", "under_review", "approved", "rejected", "ready", "deferred", "superseded", "archived"}
ROLLBACK_PRIORITIES = {"low", "medium", "high", "urgent"}


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
        "rollback_execution_disabled",
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
        "automation_disabled",
    ]


def forbidden_enabled_flags() -> list[str]:
    return [
        "rollout_execution_enabled",
        "rollback_execution_enabled",
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
    create_payload = FeatureBundleRolloutRollbackPlanCreate(
        id="rollback-plan-smoke",
        rollout_plan_id="plan-smoke",
        rollout_phase="approval",
        rollback_title="Rollback review smoke",
        rollback_summary="Rollback plan smoke summary.",
        rollback_reason="Platform wants rollback metadata available before activation.",
        rollback_trigger=FeatureBundleRolloutRollbackTrigger.ISSUE_DETECTED,
        rollback_scope=FeatureBundleRolloutRollbackScope.BUNDLE,
        rollback_status=FeatureBundleRolloutRollbackStatus.UNDER_REVIEW,
        rollback_owner="Platform Ops",
        rollback_priority=FeatureBundleRolloutRollbackPriority.HIGH,
        affected_bundle_ids=["bundle-smoke"],
        affected_feature_flag_ids=["feature-smoke"],
        related_change_request_ids=["change-request-smoke"],
        related_decision_ids=["decision-smoke"],
        related_issue_ids=["issue-smoke"],
        related_risk_ids=["risk-smoke"],
        related_dependency_ids=["dependency-smoke"],
        rollback_steps=["Review metadata", "Confirm owner"],
        validation_notes="Metadata only.",
        metadata={"smoke": True},
    )
    rollback_plan = FeatureBundleRolloutRollbackPlan(**create_payload.model_dump(mode="json", exclude_none=True))
    dumped = rollback_plan.model_dump(mode="json")
    if (
        dumped.get("rollback_trigger") != "issue_detected"
        or dumped.get("rollback_scope") != "bundle"
        or dumped.get("rollback_status") != "under_review"
        or dumped.get("rollback_priority") != "high"
    ):
        raise AssertionError(f"Rollback plan dimensions were not preserved: {dumped}")
    for flag in [
        "metadata_only",
        "rollback_plan_metadata_only",
        "rollout_execution_disabled",
        "rollback_execution_disabled",
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
        "automation_disabled",
    ]:
        if dumped.get(flag) is not True:
            raise AssertionError(f"Rollback plan model missing disabled flag {flag}: {dumped}")
    if "feature_bundle_rollout_rollback_plans" not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("Feature bundle rollout rollback plans collection is not registered.")
    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "feature_bundle_rollout_rollback_plans_id_unique",
        "feature_bundle_rollout_rollback_plans_plan_status_lookup",
        "feature_bundle_rollout_rollback_plans_status_priority_lookup",
        "feature_bundle_rollout_rollback_plans_priority_lookup",
        "feature_bundle_rollout_rollback_plans_scope_lookup",
        "feature_bundle_rollout_rollback_plans_owner_lookup",
        "feature_bundle_rollout_rollback_plans_trigger_lookup",
        "feature_bundle_rollout_rollback_plans_affected_bundle_lookup",
        "feature_bundle_rollout_rollback_plans_affected_feature_flag_lookup",
        "feature_bundle_rollout_rollback_plans_related_change_request_lookup",
        "feature_bundle_rollout_rollback_plans_related_decision_lookup",
        "feature_bundle_rollout_rollback_plans_related_issue_lookup",
        "feature_bundle_rollout_rollback_plans_related_risk_lookup",
        "feature_bundle_rollout_rollback_plans_related_dependency_lookup",
        "feature_bundle_rollout_rollback_plans_created_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Feature bundle rollout rollback plan index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    expected_methods = {
        "/api/platform/feature-bundle-rollout-rollback-plans": {"get", "post"},
        "/api/platform/feature-bundle-rollout-rollback-plans/summary": {"get"},
        "/api/platform/feature-bundle-rollout-rollback-plans/{rollback_plan_id}": {"get", "put", "delete"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-rollback-plans": {"get"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-rollback-plans/summary": {"get"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-rollback-plans/{rollback_plan_id}": {"get"},
    }
    for path, methods in expected_methods.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in [
        "/api/agencies/{agency_id}/feature-bundle-rollout-rollback-plans",
        "/api/agencies/{agency_id}/feature-bundle-rollout-rollback-plans/summary",
        "/api/agencies/{agency_id}/feature-bundle-rollout-rollback-plans/{rollback_plan_id}",
    ]:
        methods = set(paths.get(path, {}).keys())
        blocked_methods = methods & {"post", "put", "patch", "delete"}
        if blocked_methods:
            raise AssertionError(f"Agency feature bundle rollout rollback plan route is not read-only: {path} {sorted(blocked_methods)}")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Feature Bundle Rollout Rollback Plans"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Rollout Rollback Plans"),
        (ROOT / "frontend/src/App.jsx", "/platform/feature-bundle-rollout-rollback-plans"),
        (ROOT / "frontend/src/App.jsx", "/agency/rollout-rollback-plans"),
        (ROOT / "frontend/src/pages/platform/FeatureBundleRolloutRollbackPlansPage.jsx", "Feature Bundle Rollout Rollback Plans"),
        (ROOT / "frontend/src/pages/platform/FeatureBundleRolloutRollbackPlansPage.jsx", "Metadata-only rollout rollback plans"),
        (ROOT / "frontend/src/pages/platform/FeatureBundleRolloutRollbackPlansPage.jsx", "Rollback steps"),
        (ROOT / "frontend/src/pages/agency/RolloutRollbackPlansPage.jsx", "Rollout Rollback Plans"),
        (ROOT / "frontend/src/pages/agency/RolloutRollbackPlansPage.jsx", "Read-only rollout rollback plan metadata"),
        (ROOT / "docs/architecture/feature-bundle-rollout-rollback-plan-foundation.md", "Feature Bundle Rollout Rollback Plan Foundation"),
        (ROOT / "README.md", "Phase 40.12 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 40.12: Feature Bundle Rollout Rollback Plan Foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "Phase 40.12 adds feature bundle rollout rollback plan metadata"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "Phase 40.12 adds feature bundle rollout rollback plan APIs"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Feature bundle rollout rollback plans"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Feature bundle rollout rollback plans"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/FeatureBundleRolloutRollbackPlansPage.jsx",
        ROOT / "frontend/src/pages/agency/RolloutRollbackPlansPage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)
    for path in [
        ROOT / "frontend/src/pages/platform/FeatureBundleRolloutRollbackPlansPage.jsx",
        ROOT / "frontend/src/pages/agency/RolloutRollbackPlansPage.jsx",
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
    section = readiness.get("feature_bundle_rollout_rollback_plan_foundation") or {}
    for flag in [
        "feature_bundle_rollout_rollback_plans_enabled",
        "feature_bundle_rollout_rollback_trigger_metadata_enabled",
        "feature_bundle_rollout_rollback_scope_metadata_enabled",
        "feature_bundle_rollout_rollback_priority_metadata_enabled",
        "feature_bundle_rollout_rollback_status_metadata_enabled",
        "platform_rollback_plan_metadata_crud_enabled",
        "agency_rollback_plan_read_only_enabled",
        "rollback_plan_filter_by_rollout_enabled",
        "rollback_plan_filter_by_status_enabled",
        "rollback_plan_filter_by_priority_enabled",
        "rollback_plan_filter_by_scope_enabled",
        "rollback_plan_filter_by_owner_enabled",
        "rollback_plan_affected_bundle_references_enabled",
        "rollback_plan_affected_feature_flag_references_enabled",
        "rollback_plan_related_change_request_references_enabled",
        "rollback_plan_related_decision_references_enabled",
        "rollback_plan_related_issue_references_enabled",
        "rollback_plan_related_risk_references_enabled",
        "rollback_plan_related_dependency_references_enabled",
        "rollback_steps_metadata_enabled",
        "validation_notes_metadata_enabled",
        "metadata_only",
        "rollback_plan_metadata_only",
        "rollback_plan_records_informational_only",
        "read_only_ui_enabled",
    ]:
        require_flag(section, flag)
    for flag in disabled_flags():
        require_flag(section, flag)
    require_flag(section, "readiness_required", False)
    for count_key in ["rollback_plan_count", "rollback_plan_status_counts", "rollback_plan_priority_counts", "rollback_plan_scope_counts", "rollback_plan_trigger_counts"]:
        if count_key not in section:
            raise AssertionError(f"Rollback plan readiness missing count: {count_key}")
    if not ROLLBACK_STATUSES.issubset(set((section.get("rollback_plan_status_counts") or {}).keys())):
        raise AssertionError(f"Rollback plan readiness status counts missing statuses: {section}")
    if not ROLLBACK_PRIORITIES.issubset(set((section.get("rollback_plan_priority_counts") or {}).keys())):
        raise AssertionError(f"Rollback plan readiness priority counts missing priorities: {section}")
    if not ROLLBACK_SCOPES.issubset(set((section.get("rollback_plan_scope_counts") or {}).keys())):
        raise AssertionError(f"Rollback plan readiness scope counts missing scopes: {section}")
    if not ROLLBACK_TRIGGERS.issubset(set((section.get("rollback_plan_trigger_counts") or {}).keys())):
        raise AssertionError(f"Rollback plan readiness trigger counts missing triggers: {section}")
    previous_section = readiness.get("feature_bundle_rollout_change_request_foundation") or {}
    if previous_section.get("metadata_only") is not True:
        raise AssertionError("Previous change request section should remain metadata-only.")


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
            "plan_name": "Phase 40.12 smoke rollback rollout plan",
            "rollout_stage": "readiness_review",
            "target_start_date": "2027-05-10",
            "target_end_date": "2027-05-20",
            "rollout_owner": "Platform Ops",
            "notes": "Rollback plan smoke metadata only.",
        },
        OWNER_HEADERS,
        201,
    )
    rollout_plan_id = (plan_response.get("plan") or {}).get("rollout_plan_id")
    if not rollout_plan_id:
        raise AssertionError(f"Rollout plan was not created for rollback plan smoke: {plan_response}")

    dependency_id = create_dependency(agency_id, bundle_id, rollout_plan_id)
    risk_id = create_risk(agency_id, bundle_id, rollout_plan_id, dependency_id)
    issue_id = create_issue(agency_id, bundle_id, rollout_plan_id, risk_id, dependency_id)
    decision_id = create_decision(bundle_id, rollout_plan_id, dependency_id, risk_id, issue_id)
    change_request_id = create_change_request(bundle_id, rollout_plan_id, dependency_id, risk_id, issue_id, decision_id)

    created = post(
        "/api/platform/feature-bundle-rollout-rollback-plans",
        {
            "rollout_plan_id": rollout_plan_id,
            "rollout_phase": "approval",
            "rollback_title": "Rollback plan review metadata",
            "rollback_summary": "Rollback plan smoke summary.",
            "rollback_reason": "Platform wants a reviewed rollback metadata path before future activation.",
            "rollback_trigger": "issue_detected",
            "rollback_scope": "bundle",
            "rollback_status": "under_review",
            "rollback_owner": "Platform Ops",
            "rollback_priority": "high",
            "affected_bundle_ids": [bundle_id],
            "affected_feature_flag_ids": ["feature_smoke_key"],
            "related_change_request_ids": [change_request_id],
            "related_decision_ids": [decision_id],
            "related_issue_ids": [issue_id],
            "related_risk_ids": [risk_id],
            "related_dependency_ids": [dependency_id],
            "rollback_steps": ["Review affected bundle metadata", "Confirm rollback owner"],
            "validation_notes": "Rollback plan metadata only; no rollback execution.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    if created.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected create phase: {created.get('phase')}")
    assert_disabled_response(created)
    rollback_plan = created.get("rollback_plan") or {}
    assert_rollback_plan_shape(rollback_plan)
    rollback_plan_id = rollback_plan.get("id")
    if not rollback_plan_id:
        raise AssertionError(f"Rollback plan id missing: {created}")

    updated = put(
        f"/api/platform/feature-bundle-rollout-rollback-plans/{rollback_plan_id}",
        {
            "rollback_status": "ready",
            "rollback_trigger": "dependency_unready",
            "rollback_scope": "feature_flag",
            "rollback_priority": "urgent",
            "rollback_owner": "Platform Ops Updated",
            "rollback_steps": ["Review affected feature flags", "Record validation notes"],
            "validation_notes": "No rollback automation triggered.",
            "metadata": {"updated": True, "metadata_only": True},
        },
        OWNER_HEADERS,
    )
    assert_disabled_response(updated)
    updated_plan = updated.get("rollback_plan") or {}
    assert_rollback_plan_shape(updated_plan)
    if (
        updated_plan.get("rollback_status") != "ready"
        or updated_plan.get("rollback_trigger") != "dependency_unready"
        or updated_plan.get("rollback_scope") != "feature_flag"
        or updated_plan.get("rollback_priority") != "urgent"
        or updated_plan.get("rollback_owner") != "Platform Ops Updated"
    ):
        raise AssertionError(f"Rollback plan update did not persist metadata: {updated}")

    for filter_query in [
        f"rollout_plan_id={rollout_plan_id}",
        "status=ready",
        "priority=urgent",
        "scope=feature_flag",
        "owner=Platform%20Ops%20Updated",
    ]:
        filtered = get(f"/api/platform/feature-bundle-rollout-rollback-plans?{filter_query}", OWNER_HEADERS)
        assert_disabled_response(filtered)
        if not any(item.get("id") == rollback_plan_id for item in filtered.get("items") or []):
            raise AssertionError(f"Rollback plan filter {filter_query} missing created record: {filtered}")

    platform_summary = get("/api/platform/feature-bundle-rollout-rollback-plans/summary", OWNER_HEADERS)
    assert_summary_shape(platform_summary)

    platform_detail = get(f"/api/platform/feature-bundle-rollout-rollback-plans/{rollback_plan_id}", OWNER_HEADERS)
    assert_disabled_response(platform_detail)
    assert_rollback_plan_shape(platform_detail.get("rollback_plan") or {})

    agency_list = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-rollback-plans?status=ready", OWNER_HEADERS)
    assert_disabled_response(agency_list)
    if agency_list.get("read_only") is not True:
        raise AssertionError(f"Agency rollback plan list should be read-only: {agency_list}")
    agency_item = next((item for item in agency_list.get("items") or [] if item.get("id") == rollback_plan_id), None)
    if not agency_item:
        raise AssertionError(f"Agency rollback plan list missing created record: {agency_list}")
    assert_rollback_plan_shape(agency_item, agency_view=True)

    agency_summary = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-rollback-plans/summary", OWNER_HEADERS)
    assert_summary_shape(agency_summary, agency_id=agency_id)
    if agency_summary.get("read_only") is not True:
        raise AssertionError(f"Agency rollback plan summary should be read-only: {agency_summary}")

    agency_detail = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-rollback-plans/{rollback_plan_id}", OWNER_HEADERS)
    assert_disabled_response(agency_detail)
    if agency_detail.get("read_only") is not True:
        raise AssertionError(f"Agency rollback plan detail should be read-only: {agency_detail}")
    assert_rollback_plan_shape(agency_detail.get("rollback_plan") or {}, agency_view=True)

    deleted = request("DELETE", f"/api/platform/feature-bundle-rollout-rollback-plans/{rollback_plan_id}", {}, OWNER_HEADERS)[1]
    assert_disabled_response(deleted)
    if deleted.get("deleted") is not True or (deleted.get("rollback_plan") or {}).get("rollback_status") != "archived":
        raise AssertionError(f"Rollback plan delete should be metadata-only archive: {deleted}")

    after_delete = get(f"/api/platform/feature-bundle-rollout-rollback-plans?rollout_plan_id={rollout_plan_id}", OWNER_HEADERS)
    if any(item.get("id") == rollback_plan_id for item in after_delete.get("items") or []):
        raise AssertionError(f"Default rollback plan list should exclude archived-delete metadata: {after_delete}")
    include_archived = get(f"/api/platform/feature-bundle-rollout-rollback-plans?rollout_plan_id={rollout_plan_id}&include_archived=true", OWNER_HEADERS)
    if not any(item.get("id") == rollback_plan_id for item in include_archived.get("items") or []):
        raise AssertionError(f"include_archived should expose metadata-archived rollback plan: {include_archived}")

    request("POST", f"/api/agencies/{agency_id}/feature-bundle-rollout-rollback-plans", {"rollback_title": "blocked"}, OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/feature-bundle-rollout-rollback-plans/{rollback_plan_id}", {"rollback_status": "rejected"}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/feature-bundle-rollout-rollback-plans/{rollback_plan_id}", {}, OWNER_HEADERS, 405)


def create_dependency(agency_id: str, bundle_id: str, rollout_plan_id: str) -> str:
    response = post(
        "/api/platform/feature-bundle-dependencies",
        {
            "agency_id": agency_id,
            "bundle_id": bundle_id,
            "rollout_plan_id": rollout_plan_id,
            "dependency_type": "readiness_checklist",
            "depends_on": {
                "reference_type": "readiness_checklist",
                "reference_id": "readiness-rollback-plan-smoke",
                "label": "Readiness checklist rollback plan smoke",
            },
            "status": "warning",
            "notes": "Dependency metadata for rollback plan smoke.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    dependency_id = (response.get("dependency") or {}).get("dependency_id")
    if not dependency_id:
        raise AssertionError(f"Dependency was not created for rollback plan smoke: {response}")
    return dependency_id


def create_risk(agency_id: str, bundle_id: str, rollout_plan_id: str, dependency_id: str) -> str:
    response = post(
        "/api/platform/feature-bundle-rollout-risks",
        {
            "agency_id": agency_id,
            "bundle_id": bundle_id,
            "rollout_plan_id": rollout_plan_id,
            "dependency_id": dependency_id,
            "title": "Rollback dependency risk smoke",
            "description": "Risk metadata for rollback plan smoke.",
            "impact": "high",
            "likelihood": "possible",
            "status": "open",
            "mitigation_notes": "Review dependency metadata.",
            "owner": "Platform Ops",
            "review_notes": "No enforcement.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    risk_id = (response.get("risk") or {}).get("risk_id")
    if not risk_id:
        raise AssertionError(f"Risk was not created for rollback plan smoke: {response}")
    return risk_id


def create_issue(agency_id: str, bundle_id: str, rollout_plan_id: str, risk_id: str, dependency_id: str) -> str:
    response = post(
        "/api/platform/feature-bundle-rollout-issues",
        {
            "agency_id": agency_id,
            "bundle_id": bundle_id,
            "rollout_plan_id": rollout_plan_id,
            "risk_id": risk_id,
            "dependency_id": dependency_id,
            "title": "Rollback follow-up issue smoke",
            "description": "Issue metadata for rollback plan smoke.",
            "severity": "high",
            "status": "open",
            "owner": "Platform Ops",
            "resolution_notes": "Record rollback plan rationale.",
            "review_notes": "No notification sent.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    issue_id = (response.get("issue") or {}).get("issue_id")
    if not issue_id:
        raise AssertionError(f"Issue was not created for rollback plan smoke: {response}")
    return issue_id


def create_decision(bundle_id: str, rollout_plan_id: str, dependency_id: str, risk_id: str, issue_id: str) -> str:
    response = post(
        "/api/platform/feature-bundle-rollout-decisions",
        {
            "rollout_plan_id": rollout_plan_id,
            "rollout_phase": "approval",
            "decision_title": "Prepare rollback metadata",
            "decision_summary": "Decision metadata for rollback plan smoke.",
            "decision_reason": "A rollback plan should be recorded for review.",
            "decision_category": "governance",
            "decision_status": "accepted",
            "decision_owner": "Platform Ops",
            "decision_date": "2027-05-04T10:00:00Z",
            "related_bundle_ids": [bundle_id],
            "related_dependency_ids": [dependency_id],
            "related_risk_ids": [risk_id],
            "related_issue_ids": [issue_id],
            "notes": "Decision metadata only; no rollout execution.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    decision_id = (response.get("decision") or {}).get("id")
    if not decision_id:
        raise AssertionError(f"Decision was not created for rollback plan smoke: {response}")
    return decision_id


def create_change_request(bundle_id: str, rollout_plan_id: str, dependency_id: str, risk_id: str, issue_id: str, decision_id: str) -> str:
    response = post(
        "/api/platform/feature-bundle-rollout-change-requests",
        {
            "rollout_plan_id": rollout_plan_id,
            "rollout_phase": "approval",
            "change_title": "Prepare rollback plan metadata",
            "change_summary": "Change request metadata for rollback plan smoke.",
            "change_reason": "Platform asked for rollback plan metadata before future activation.",
            "requested_by": "Platform Ops",
            "requested_date": "2027-05-05T10:00:00Z",
            "change_type": "operational",
            "priority": "high",
            "impact_level": "high",
            "change_status": "requested",
            "affected_bundle_ids": [bundle_id],
            "affected_feature_flag_ids": ["feature_smoke_key"],
            "related_decision_ids": [decision_id],
            "related_issue_ids": [issue_id],
            "related_risk_ids": [risk_id],
            "related_dependency_ids": [dependency_id],
            "review_notes": "Change request metadata only; no rollout execution.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    change_request_id = (response.get("change_request") or {}).get("id")
    if not change_request_id:
        raise AssertionError(f"Change request was not created for rollback plan smoke: {response}")
    return change_request_id


def assert_rollback_plan_shape(rollback_plan: dict, *, agency_view: bool = False) -> None:
    for key in [
        "id",
        "rollout_plan_id",
        "rollback_title",
        "rollback_trigger",
        "rollback_scope",
        "rollback_status",
        "rollback_priority",
        "metadata_only",
        "rollback_plan_metadata_only",
        "affected_bundle_ids",
        "affected_feature_flag_ids",
        "related_change_request_ids",
        "related_decision_ids",
        "related_issue_ids",
        "related_risk_ids",
        "related_dependency_ids",
        "rollback_steps",
        "affected_bundles",
        "affected_feature_flags",
        "related_change_requests",
        "related_decisions",
        "related_issues",
        "related_risks",
        "related_dependencies",
    ]:
        if key not in rollback_plan:
            raise AssertionError(f"Rollback plan response missing {key}: {rollback_plan}")
    if rollback_plan.get("rollback_trigger") not in ROLLBACK_TRIGGERS:
        raise AssertionError(f"Rollback trigger is invalid: {rollback_plan}")
    if rollback_plan.get("rollback_scope") not in ROLLBACK_SCOPES:
        raise AssertionError(f"Rollback scope is invalid: {rollback_plan}")
    if rollback_plan.get("rollback_status") not in ROLLBACK_STATUSES:
        raise AssertionError(f"Rollback status is invalid: {rollback_plan}")
    if rollback_plan.get("rollback_priority") not in ROLLBACK_PRIORITIES:
        raise AssertionError(f"Rollback priority is invalid: {rollback_plan}")
    for key in [
        "affected_bundles",
        "affected_feature_flags",
        "related_change_requests",
        "related_decisions",
        "related_issues",
        "related_risks",
        "related_dependencies",
        "rollback_steps",
    ]:
        if not isinstance(rollback_plan.get(key), list):
            raise AssertionError(f"Rollback plan {key} should be a list: {rollback_plan}")
    for flag in disabled_flags():
        if rollback_plan.get(flag) is not True:
            raise AssertionError(f"Rollback plan missing disabled flag {flag}: {rollback_plan}")
    if agency_view and rollback_plan.get("read_only") is not True:
        raise AssertionError(f"Agency rollback plan projection should be read-only: {rollback_plan}")


def assert_summary_shape(payload: dict, *, agency_id: str | None = None) -> None:
    assert_disabled_response(payload)
    summary = payload.get("summary") or {}
    for key in [
        "by_status",
        "by_priority",
        "by_scope",
        "by_trigger",
        "total_count",
        "affected_bundle_count",
        "affected_feature_flag_count",
        "related_change_request_count",
        "related_decision_count",
        "related_issue_count",
        "related_risk_count",
        "related_dependency_count",
        "rollback_step_count",
    ]:
        if key not in summary:
            raise AssertionError(f"Rollback plan summary missing {key}: {payload}")
    if not ROLLBACK_STATUSES.issubset(set((summary.get("by_status") or {}).keys())):
        raise AssertionError(f"Rollback plan summary missing statuses: {payload}")
    if not ROLLBACK_PRIORITIES.issubset(set((summary.get("by_priority") or {}).keys())):
        raise AssertionError(f"Rollback plan summary missing priorities: {payload}")
    if not ROLLBACK_SCOPES.issubset(set((summary.get("by_scope") or {}).keys())):
        raise AssertionError(f"Rollback plan summary missing scopes: {payload}")
    if not ROLLBACK_TRIGGERS.issubset(set((summary.get("by_trigger") or {}).keys())):
        raise AssertionError(f"Rollback plan summary missing triggers: {payload}")
    if agency_id and payload.get("agency_id") != agency_id:
        raise AssertionError(f"Agency summary should be scoped to {agency_id}: {payload}")


def main() -> int:
    verify_model_and_collection_registration()
    openapi = get("/openapi.json")
    verify_routes(openapi.get("paths") or {})
    verify_frontend_and_docs()
    verify_readiness()
    verify_endpoint_behavior()
    print("Phase 40.12 feature bundle rollout rollback plan foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
