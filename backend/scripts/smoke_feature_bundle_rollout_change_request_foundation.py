#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import (
    FeatureBundleRolloutChangeRequest,
    FeatureBundleRolloutChangeRequestCreate,
    FeatureBundleRolloutChangeRequestImpactLevel,
    FeatureBundleRolloutChangeRequestPriority,
    FeatureBundleRolloutChangeRequestStatus,
    FeatureBundleRolloutChangeRequestType,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_42_1_operational_timeline_workspace_foundation"
ROOT = Path(__file__).resolve().parents[2]
CHANGE_TYPES = {"scope", "schedule", "readiness", "approval", "dependency", "risk", "issue", "decision", "documentation", "operational"}
CHANGE_PRIORITIES = {"low", "medium", "high", "urgent"}
CHANGE_IMPACTS = {"low", "medium", "high", "critical"}
CHANGE_STATUSES = {"draft", "requested", "under_review", "approved", "rejected", "deferred", "superseded", "archived"}


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
        "feature_bundle_activation_disabled",
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
        "deployment_automation_enabled",
        "feature_activation_enabled",
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
    create_payload = FeatureBundleRolloutChangeRequestCreate(
        id="change-request-smoke",
        rollout_plan_id="plan-smoke",
        rollout_phase="approval",
        change_title="Adjust rollout scope smoke",
        change_summary="Change request smoke summary.",
        change_reason="Platform review found agency-facing scope notes to update.",
        requested_by="Platform Ops",
        change_type=FeatureBundleRolloutChangeRequestType.SCOPE,
        priority=FeatureBundleRolloutChangeRequestPriority.HIGH,
        impact_level=FeatureBundleRolloutChangeRequestImpactLevel.CRITICAL,
        change_status=FeatureBundleRolloutChangeRequestStatus.UNDER_REVIEW,
        affected_bundle_ids=["bundle-smoke"],
        affected_feature_flag_ids=["feature-smoke"],
        related_decision_ids=["decision-smoke"],
        related_issue_ids=["issue-smoke"],
        related_risk_ids=["risk-smoke"],
        related_dependency_ids=["dependency-smoke"],
        review_notes="Metadata only.",
        metadata={"smoke": True},
    )
    change_request = FeatureBundleRolloutChangeRequest(**create_payload.model_dump(mode="json", exclude_none=True))
    dumped = change_request.model_dump(mode="json")
    if (
        dumped.get("change_type") != "scope"
        or dumped.get("priority") != "high"
        or dumped.get("impact_level") != "critical"
        or dumped.get("change_status") != "under_review"
    ):
        raise AssertionError(f"Change request dimensions were not preserved: {dumped}")
    for flag in [
        "metadata_only",
        "change_request_metadata_only",
        "rollout_execution_disabled",
        "deployment_automation_disabled",
        "feature_activation_disabled",
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
            raise AssertionError(f"Change request model missing disabled flag {flag}: {dumped}")
    if "feature_bundle_rollout_change_requests" not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("Feature bundle rollout change requests collection is not registered.")
    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "feature_bundle_rollout_change_requests_id_unique",
        "feature_bundle_rollout_change_requests_plan_status_lookup",
        "feature_bundle_rollout_change_requests_status_priority_lookup",
        "feature_bundle_rollout_change_requests_priority_lookup",
        "feature_bundle_rollout_change_requests_impact_lookup",
        "feature_bundle_rollout_change_requests_type_lookup",
        "feature_bundle_rollout_change_requests_affected_bundle_lookup",
        "feature_bundle_rollout_change_requests_affected_feature_flag_lookup",
        "feature_bundle_rollout_change_requests_related_decision_lookup",
        "feature_bundle_rollout_change_requests_related_issue_lookup",
        "feature_bundle_rollout_change_requests_related_risk_lookup",
        "feature_bundle_rollout_change_requests_related_dependency_lookup",
        "feature_bundle_rollout_change_requests_requested_date_lookup",
        "feature_bundle_rollout_change_requests_created_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Feature bundle rollout change request index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    expected_methods = {
        "/api/platform/feature-bundle-rollout-change-requests": {"get", "post"},
        "/api/platform/feature-bundle-rollout-change-requests/summary": {"get"},
        "/api/platform/feature-bundle-rollout-change-requests/{change_request_id}": {"get", "put", "delete"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-change-requests": {"get"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-change-requests/summary": {"get"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-change-requests/{change_request_id}": {"get"},
    }
    for path, methods in expected_methods.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in [
        "/api/agencies/{agency_id}/feature-bundle-rollout-change-requests",
        "/api/agencies/{agency_id}/feature-bundle-rollout-change-requests/summary",
        "/api/agencies/{agency_id}/feature-bundle-rollout-change-requests/{change_request_id}",
    ]:
        methods = set(paths.get(path, {}).keys())
        blocked_methods = methods & {"post", "put", "patch", "delete"}
        if blocked_methods:
            raise AssertionError(f"Agency feature bundle rollout change request route is not read-only: {path} {sorted(blocked_methods)}")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Feature Bundle Rollout Change Requests"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Rollout Change Requests"),
        (ROOT / "frontend/src/App.jsx", "/platform/feature-bundle-rollout-change-requests"),
        (ROOT / "frontend/src/App.jsx", "/agency/rollout-change-requests"),
        (ROOT / "frontend/src/pages/platform/FeatureBundleRolloutChangeRequestsPage.jsx", "Feature Bundle Rollout Change Requests"),
        (ROOT / "frontend/src/pages/platform/FeatureBundleRolloutChangeRequestsPage.jsx", "Metadata-only rollout change requests"),
        (ROOT / "frontend/src/pages/platform/FeatureBundleRolloutChangeRequestsPage.jsx", "Affected bundles"),
        (ROOT / "frontend/src/pages/agency/RolloutChangeRequestsPage.jsx", "Rollout Change Requests"),
        (ROOT / "frontend/src/pages/agency/RolloutChangeRequestsPage.jsx", "Read-only rollout change request metadata"),
        (ROOT / "docs/architecture/feature-bundle-rollout-change-request-foundation.md", "Feature Bundle Rollout Change Request Foundation"),
        (ROOT / "README.md", "Phase 40.11 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 40.11: Feature Bundle Rollout Change Request Foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "Phase 40.11 adds feature bundle rollout change request metadata"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "Phase 40.11 adds feature bundle rollout change request APIs"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Feature bundle rollout change requests"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Feature bundle rollout change requests"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/FeatureBundleRolloutChangeRequestsPage.jsx",
        ROOT / "frontend/src/pages/agency/RolloutChangeRequestsPage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)
    for path in [
        ROOT / "frontend/src/pages/platform/FeatureBundleRolloutChangeRequestsPage.jsx",
        ROOT / "frontend/src/pages/agency/RolloutChangeRequestsPage.jsx",
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
    section = readiness.get("feature_bundle_rollout_change_request_foundation") or {}
    for flag in [
        "feature_bundle_rollout_change_requests_enabled",
        "feature_bundle_rollout_change_request_type_metadata_enabled",
        "feature_bundle_rollout_change_request_priority_metadata_enabled",
        "feature_bundle_rollout_change_request_impact_metadata_enabled",
        "feature_bundle_rollout_change_request_status_metadata_enabled",
        "platform_change_request_metadata_crud_enabled",
        "agency_change_request_read_only_enabled",
        "change_request_filter_by_rollout_enabled",
        "change_request_filter_by_status_enabled",
        "change_request_filter_by_priority_enabled",
        "change_request_filter_by_impact_level_enabled",
        "change_request_filter_by_change_type_enabled",
        "change_request_affected_bundle_references_enabled",
        "change_request_affected_feature_flag_references_enabled",
        "change_request_related_decision_references_enabled",
        "change_request_related_issue_references_enabled",
        "change_request_related_risk_references_enabled",
        "change_request_related_dependency_references_enabled",
        "metadata_only",
        "change_request_metadata_only",
        "change_request_records_informational_only",
        "read_only_ui_enabled",
    ]:
        require_flag(section, flag)
    for flag in disabled_flags():
        require_flag(section, flag)
    require_flag(section, "readiness_required", False)
    for count_key in ["change_request_count", "change_request_status_counts", "change_request_priority_counts", "change_request_impact_counts", "change_request_type_counts"]:
        if count_key not in section:
            raise AssertionError(f"Change request readiness missing count: {count_key}")
    if not CHANGE_STATUSES.issubset(set((section.get("change_request_status_counts") or {}).keys())):
        raise AssertionError(f"Change request readiness status counts missing statuses: {section}")
    if not CHANGE_PRIORITIES.issubset(set((section.get("change_request_priority_counts") or {}).keys())):
        raise AssertionError(f"Change request readiness priority counts missing priorities: {section}")
    if not CHANGE_IMPACTS.issubset(set((section.get("change_request_impact_counts") or {}).keys())):
        raise AssertionError(f"Change request readiness impact counts missing impacts: {section}")
    if not CHANGE_TYPES.issubset(set((section.get("change_request_type_counts") or {}).keys())):
        raise AssertionError(f"Change request readiness type counts missing types: {section}")
    previous_section = readiness.get("feature_bundle_rollout_decision_register_foundation") or {}
    if previous_section.get("metadata_only") is not True:
        raise AssertionError("Previous decision register section should remain metadata-only.")


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
            "plan_name": "Phase 40.11 smoke change request rollout plan",
            "rollout_stage": "readiness_review",
            "target_start_date": "2027-04-10",
            "target_end_date": "2027-04-20",
            "rollout_owner": "Platform Ops",
            "notes": "Change request smoke plan metadata only.",
        },
        OWNER_HEADERS,
        201,
    )
    rollout_plan_id = (plan_response.get("plan") or {}).get("rollout_plan_id")
    if not rollout_plan_id:
        raise AssertionError(f"Rollout plan was not created for change request smoke: {plan_response}")

    dependency_id = create_dependency(agency_id, bundle_id, rollout_plan_id)
    risk_id = create_risk(agency_id, bundle_id, rollout_plan_id, dependency_id)
    issue_id = create_issue(agency_id, bundle_id, rollout_plan_id, risk_id, dependency_id)
    decision_id = create_decision(bundle_id, rollout_plan_id, dependency_id, risk_id, issue_id)

    created = post(
        "/api/platform/feature-bundle-rollout-change-requests",
        {
            "rollout_plan_id": rollout_plan_id,
            "rollout_phase": "approval",
            "change_title": "Adjust agency rollout notes",
            "change_summary": "Change request smoke summary.",
            "change_reason": "Decision review asked for agency-facing rollout notes to be clarified.",
            "requested_by": "Platform Ops",
            "requested_date": "2027-04-05T10:00:00Z",
            "change_type": "schedule",
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
    if created.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected create phase: {created.get('phase')}")
    assert_disabled_response(created)
    change_request = created.get("change_request") or {}
    assert_change_request_shape(change_request)
    change_request_id = change_request.get("id")
    if not change_request_id:
        raise AssertionError(f"Change request id missing: {created}")

    updated = put(
        f"/api/platform/feature-bundle-rollout-change-requests/{change_request_id}",
        {
            "change_status": "under_review",
            "change_type": "scope",
            "priority": "urgent",
            "impact_level": "critical",
            "change_reason": "Reviewed as urgent scope metadata.",
            "review_notes": "No automation triggered.",
            "metadata": {"updated": True, "metadata_only": True},
        },
        OWNER_HEADERS,
    )
    assert_disabled_response(updated)
    updated_change = updated.get("change_request") or {}
    assert_change_request_shape(updated_change)
    if (
        updated_change.get("change_status") != "under_review"
        or updated_change.get("change_type") != "scope"
        or updated_change.get("priority") != "urgent"
        or updated_change.get("impact_level") != "critical"
    ):
        raise AssertionError(f"Change request update did not persist metadata: {updated}")

    for filter_query in [
        f"rollout_plan_id={rollout_plan_id}",
        "status=under_review",
        "priority=urgent",
        "impact_level=critical",
        "change_type=scope",
    ]:
        filtered = get(f"/api/platform/feature-bundle-rollout-change-requests?{filter_query}", OWNER_HEADERS)
        assert_disabled_response(filtered)
        if not any(item.get("id") == change_request_id for item in filtered.get("items") or []):
            raise AssertionError(f"Change request filter {filter_query} missing created record: {filtered}")

    type_filter = get("/api/platform/feature-bundle-rollout-change-requests?change_type=scope", OWNER_HEADERS)
    if any(item.get("change_type") != "scope" for item in type_filter.get("items") or []):
        raise AssertionError(f"Change request type filter returned another type: {type_filter}")

    platform_summary = get("/api/platform/feature-bundle-rollout-change-requests/summary", OWNER_HEADERS)
    assert_summary_shape(platform_summary)

    platform_detail = get(f"/api/platform/feature-bundle-rollout-change-requests/{change_request_id}", OWNER_HEADERS)
    assert_disabled_response(platform_detail)
    assert_change_request_shape(platform_detail.get("change_request") or {})

    agency_list = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-change-requests?status=under_review", OWNER_HEADERS)
    assert_disabled_response(agency_list)
    if agency_list.get("read_only") is not True:
        raise AssertionError(f"Agency change request list should be read-only: {agency_list}")
    agency_item = next((item for item in agency_list.get("items") or [] if item.get("id") == change_request_id), None)
    if not agency_item:
        raise AssertionError(f"Agency change request list missing created record: {agency_list}")
    assert_change_request_shape(agency_item, agency_view=True)

    agency_summary = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-change-requests/summary", OWNER_HEADERS)
    assert_summary_shape(agency_summary, agency_id=agency_id)
    if agency_summary.get("read_only") is not True:
        raise AssertionError(f"Agency change request summary should be read-only: {agency_summary}")

    agency_detail = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-change-requests/{change_request_id}", OWNER_HEADERS)
    assert_disabled_response(agency_detail)
    if agency_detail.get("read_only") is not True:
        raise AssertionError(f"Agency change request detail should be read-only: {agency_detail}")
    assert_change_request_shape(agency_detail.get("change_request") or {}, agency_view=True)

    deleted = request("DELETE", f"/api/platform/feature-bundle-rollout-change-requests/{change_request_id}", {}, OWNER_HEADERS)[1]
    assert_disabled_response(deleted)
    if deleted.get("deleted") is not True or (deleted.get("change_request") or {}).get("change_status") != "archived":
        raise AssertionError(f"Change request delete should be metadata-only archive: {deleted}")

    after_delete = get(f"/api/platform/feature-bundle-rollout-change-requests?rollout_plan_id={rollout_plan_id}", OWNER_HEADERS)
    if any(item.get("id") == change_request_id for item in after_delete.get("items") or []):
        raise AssertionError(f"Default change request list should exclude archived-delete metadata: {after_delete}")
    include_archived = get(f"/api/platform/feature-bundle-rollout-change-requests?rollout_plan_id={rollout_plan_id}&include_archived=true", OWNER_HEADERS)
    if not any(item.get("id") == change_request_id for item in include_archived.get("items") or []):
        raise AssertionError(f"include_archived should expose metadata-archived change request: {include_archived}")

    request("POST", f"/api/agencies/{agency_id}/feature-bundle-rollout-change-requests", {"change_title": "blocked"}, OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/feature-bundle-rollout-change-requests/{change_request_id}", {"change_status": "rejected"}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/feature-bundle-rollout-change-requests/{change_request_id}", {}, OWNER_HEADERS, 405)


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
                "reference_id": "readiness-change-request-smoke",
                "label": "Readiness checklist change request smoke",
            },
            "status": "warning",
            "notes": "Dependency metadata for change request smoke.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    dependency_id = (response.get("dependency") or {}).get("dependency_id")
    if not dependency_id:
        raise AssertionError(f"Dependency was not created for change request smoke: {response}")
    return dependency_id


def create_risk(agency_id: str, bundle_id: str, rollout_plan_id: str, dependency_id: str) -> str:
    response = post(
        "/api/platform/feature-bundle-rollout-risks",
        {
            "agency_id": agency_id,
            "bundle_id": bundle_id,
            "rollout_plan_id": rollout_plan_id,
            "dependency_id": dependency_id,
            "title": "Change request dependency risk smoke",
            "description": "Risk metadata for change request smoke.",
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
        raise AssertionError(f"Risk was not created for change request smoke: {response}")
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
            "title": "Change request follow-up issue smoke",
            "description": "Issue metadata for change request smoke.",
            "severity": "high",
            "status": "open",
            "owner": "Platform Ops",
            "resolution_notes": "Record change request rationale.",
            "review_notes": "No notification sent.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    issue_id = (response.get("issue") or {}).get("issue_id")
    if not issue_id:
        raise AssertionError(f"Issue was not created for change request smoke: {response}")
    return issue_id


def create_decision(bundle_id: str, rollout_plan_id: str, dependency_id: str, risk_id: str, issue_id: str) -> str:
    response = post(
        "/api/platform/feature-bundle-rollout-decisions",
        {
            "rollout_plan_id": rollout_plan_id,
            "rollout_phase": "approval",
            "decision_title": "Request metadata change",
            "decision_summary": "Decision metadata for change request smoke.",
            "decision_reason": "A rollout change request should be recorded for review.",
            "decision_category": "governance",
            "decision_status": "accepted",
            "decision_owner": "Platform Ops",
            "decision_date": "2027-04-04T10:00:00Z",
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
        raise AssertionError(f"Decision was not created for change request smoke: {response}")
    return decision_id


def assert_change_request_shape(change_request: dict, *, agency_view: bool = False) -> None:
    for key in [
        "id",
        "rollout_plan_id",
        "change_title",
        "change_type",
        "priority",
        "impact_level",
        "change_status",
        "metadata_only",
        "change_request_metadata_only",
        "affected_bundle_ids",
        "affected_feature_flag_ids",
        "related_decision_ids",
        "related_issue_ids",
        "related_risk_ids",
        "related_dependency_ids",
        "affected_bundles",
        "affected_feature_flags",
        "related_decisions",
        "related_issues",
        "related_risks",
        "related_dependencies",
    ]:
        if key not in change_request:
            raise AssertionError(f"Change request response missing {key}: {change_request}")
    if change_request.get("change_type") not in CHANGE_TYPES:
        raise AssertionError(f"Change request type is invalid: {change_request}")
    if change_request.get("priority") not in CHANGE_PRIORITIES:
        raise AssertionError(f"Change request priority is invalid: {change_request}")
    if change_request.get("impact_level") not in CHANGE_IMPACTS:
        raise AssertionError(f"Change request impact is invalid: {change_request}")
    if change_request.get("change_status") not in CHANGE_STATUSES:
        raise AssertionError(f"Change request status is invalid: {change_request}")
    for key in ["affected_bundles", "affected_feature_flags", "related_decisions", "related_issues", "related_risks", "related_dependencies"]:
        if not isinstance(change_request.get(key), list):
            raise AssertionError(f"Change request {key} should be a list: {change_request}")
    for flag in disabled_flags():
        if change_request.get(flag) is not True:
            raise AssertionError(f"Change request missing disabled flag {flag}: {change_request}")
    if agency_view and change_request.get("read_only") is not True:
        raise AssertionError(f"Agency change request projection should be read-only: {change_request}")


def assert_summary_shape(payload: dict, *, agency_id: str | None = None) -> None:
    assert_disabled_response(payload)
    summary = payload.get("summary") or {}
    for key in [
        "by_status",
        "by_priority",
        "by_impact_level",
        "by_change_type",
        "total_count",
        "affected_bundle_count",
        "affected_feature_flag_count",
        "related_decision_count",
        "related_issue_count",
        "related_risk_count",
        "related_dependency_count",
    ]:
        if key not in summary:
            raise AssertionError(f"Change request summary missing {key}: {payload}")
    if not CHANGE_STATUSES.issubset(set((summary.get("by_status") or {}).keys())):
        raise AssertionError(f"Change request summary missing statuses: {payload}")
    if not CHANGE_PRIORITIES.issubset(set((summary.get("by_priority") or {}).keys())):
        raise AssertionError(f"Change request summary missing priorities: {payload}")
    if not CHANGE_IMPACTS.issubset(set((summary.get("by_impact_level") or {}).keys())):
        raise AssertionError(f"Change request summary missing impacts: {payload}")
    if not CHANGE_TYPES.issubset(set((summary.get("by_change_type") or {}).keys())):
        raise AssertionError(f"Change request summary missing types: {payload}")
    if agency_id and payload.get("agency_id") != agency_id:
        raise AssertionError(f"Agency summary should be scoped to {agency_id}: {payload}")


def main() -> int:
    verify_model_and_collection_registration()
    openapi = get("/openapi.json")
    verify_routes(openapi.get("paths") or {})
    verify_frontend_and_docs()
    verify_readiness()
    verify_endpoint_behavior()
    print("Phase 40.11 feature bundle rollout change request foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
