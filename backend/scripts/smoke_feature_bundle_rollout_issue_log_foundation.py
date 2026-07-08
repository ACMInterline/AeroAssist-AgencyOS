#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import (
    FeatureBundleRolloutIssue,
    FeatureBundleRolloutIssueCreate,
    FeatureBundleRolloutIssueSeverity,
    FeatureBundleRolloutIssueStatus,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_42_1_operational_timeline_workspace_foundation"
ROOT = Path(__file__).resolve().parents[2]
ISSUE_SEVERITIES = {"low", "medium", "high", "critical"}
ISSUE_STATUSES = {"open", "in_review", "follow_up", "resolved", "closed", "deleted"}


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
        "feature_bundle_activation_disabled",
        "feature_bundles_enablement_disabled",
        "rollout_blocking_disabled",
        "blocking_enforcement_disabled",
        "notification_sending_disabled",
        "notifications_disabled",
        "external_provider_calls_disabled",
        "provider_calls_disabled",
        "provider_execution_disabled",
        "ai_provider_execution_disabled",
        "ai_execution_disabled",
        "automation_disabled",
        "background_jobs_disabled",
    ]


def forbidden_enabled_flags() -> list[str]:
    return [
        "rollout_execution_enabled",
        "feature_bundle_activation_enabled",
        "rollout_blocking_enabled",
        "blocking_enforcement_enabled",
        "notification_sending_enabled",
        "provider_calls_enabled",
        "provider_execution_enabled",
        "ai_provider_execution_enabled",
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
    create_payload = FeatureBundleRolloutIssueCreate(
        agency_id="agency-smoke",
        bundle_id="bundle-smoke",
        rollout_plan_id="plan-smoke",
        risk_id="risk-smoke",
        dependency_id="dependency-smoke",
        approval_id="approval-smoke",
        title="Checklist item failed smoke",
        description="Metadata-only issue smoke.",
        severity=FeatureBundleRolloutIssueSeverity.HIGH,
        status=FeatureBundleRolloutIssueStatus.IN_REVIEW,
        owner="Platform Ops",
        resolution_notes="Document follow-up.",
        review_notes="No blocking.",
        metadata={"smoke": True},
    )
    issue = FeatureBundleRolloutIssue(**create_payload.model_dump(mode="json", exclude_none=True))
    dumped = issue.model_dump(mode="json")
    if dumped.get("severity") != "high" or dumped.get("status") != "in_review":
        raise AssertionError(f"Issue dimensions were not preserved: {dumped}")
    for flag in [
        "metadata_only",
        "issue_log_metadata_only",
        "rollout_execution_disabled",
        "feature_bundle_activation_disabled",
        "rollout_blocking_disabled",
        "blocking_enforcement_disabled",
        "notification_sending_disabled",
        "external_provider_calls_disabled",
        "ai_provider_execution_disabled",
        "automation_disabled",
    ]:
        if dumped.get(flag) is not True:
            raise AssertionError(f"Issue model missing disabled flag {flag}: {dumped}")
    if "feature_bundle_rollout_issues" not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("Feature bundle rollout issues collection is not agency-owned/registered.")
    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "feature_bundle_rollout_issues_id_unique",
        "feature_bundle_rollout_issues_issue_unique",
        "feature_bundle_rollout_issues_agency_status_lookup",
        "feature_bundle_rollout_issues_bundle_severity_lookup",
        "feature_bundle_rollout_issues_plan_status_lookup",
        "feature_bundle_rollout_issues_risk_lookup",
        "feature_bundle_rollout_issues_dependency_lookup",
        "feature_bundle_rollout_issues_approval_lookup",
        "feature_bundle_rollout_issues_severity_status_lookup",
        "feature_bundle_rollout_issues_created_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Feature bundle rollout issue index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    expected_methods = {
        "/api/platform/feature-bundle-rollout-issues": {"get", "post"},
        "/api/platform/feature-bundle-rollout-issues/summary": {"get"},
        "/api/platform/feature-bundle-rollout-issues/{issue_id}": {"get", "put", "delete"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-issues": {"get"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-issues/summary": {"get"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-issues/{issue_id}": {"get"},
    }
    for path, methods in expected_methods.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in [
        "/api/agencies/{agency_id}/feature-bundle-rollout-issues",
        "/api/agencies/{agency_id}/feature-bundle-rollout-issues/summary",
        "/api/agencies/{agency_id}/feature-bundle-rollout-issues/{issue_id}",
    ]:
        methods = set(paths.get(path, {}).keys())
        blocked_methods = methods & {"post", "put", "patch", "delete"}
        if blocked_methods:
            raise AssertionError(f"Agency feature bundle rollout issue route is not read-only: {path} {sorted(blocked_methods)}")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Feature Bundle Rollout Issues"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Rollout Issues"),
        (ROOT / "frontend/src/App.jsx", "/platform/feature-bundle-rollout-issues"),
        (ROOT / "frontend/src/App.jsx", "/agency/rollout-issues"),
        (ROOT / "frontend/src/pages/platform/FeatureBundleRolloutIssuesPage.jsx", "Feature Bundle Rollout Issues"),
        (ROOT / "frontend/src/pages/platform/FeatureBundleRolloutIssuesPage.jsx", "Metadata-only rollout issue log"),
        (ROOT / "frontend/src/pages/agency/RolloutIssuesPage.jsx", "Rollout Issues"),
        (ROOT / "frontend/src/pages/agency/RolloutIssuesPage.jsx", "Read-only rollout issue metadata"),
        (ROOT / "docs/architecture/feature-bundle-rollout-issue-log-foundation.md", "Feature Bundle Rollout Issue Log Foundation"),
        (ROOT / "README.md", "Phase 40.9 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 40.9: Feature Bundle Rollout Issue Log Foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "Phase 40.9 adds feature bundle rollout issue log metadata"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "Phase 40.9 adds feature bundle rollout issue APIs"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Feature bundle rollout issue log"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Feature bundle rollout issue log"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/FeatureBundleRolloutIssuesPage.jsx",
        ROOT / "frontend/src/pages/agency/RolloutIssuesPage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)
    for path in [
        ROOT / "frontend/src/pages/platform/FeatureBundleRolloutIssuesPage.jsx",
        ROOT / "frontend/src/pages/agency/RolloutIssuesPage.jsx",
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
    section = readiness.get("feature_bundle_rollout_issue_log_foundation") or {}
    for flag in [
        "feature_bundle_rollout_issues_enabled",
        "feature_bundle_rollout_issue_severity_metadata_enabled",
        "feature_bundle_rollout_issue_status_metadata_enabled",
        "platform_issue_metadata_crud_enabled",
        "agency_issue_read_only_enabled",
        "issue_filter_by_agency_enabled",
        "issue_filter_by_bundle_enabled",
        "issue_filter_by_rollout_plan_enabled",
        "issue_filter_by_risk_enabled",
        "issue_filter_by_dependency_enabled",
        "issue_filter_by_approval_enabled",
        "issue_filter_by_severity_enabled",
        "issue_filter_by_status_enabled",
        "metadata_only",
        "issue_log_metadata_only",
        "issue_records_informational_only",
    ]:
        require_flag(section, flag)
    for flag in disabled_flags():
        require_flag(section, flag)
    require_flag(section, "readiness_required", False)
    for count_key in ["issue_count", "issue_status_counts", "issue_severity_counts"]:
        if count_key not in section:
            raise AssertionError(f"Issue readiness missing count: {count_key}")
    if not ISSUE_STATUSES.issubset(set((section.get("issue_status_counts") or {}).keys())):
        raise AssertionError(f"Issue readiness status counts missing statuses: {section}")
    if not ISSUE_SEVERITIES.issubset(set((section.get("issue_severity_counts") or {}).keys())):
        raise AssertionError(f"Issue readiness severity counts missing severities: {section}")
    previous_section = readiness.get("feature_bundle_rollout_risk_register_foundation") or {}
    if previous_section.get("metadata_only") is not True:
        raise AssertionError("Previous risk register section should remain metadata-only.")


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
            "plan_name": "Phase 40.9 smoke issue rollout plan",
            "rollout_stage": "readiness_review",
            "target_start_date": "2027-02-10",
            "target_end_date": "2027-02-20",
            "rollout_owner": "Platform Ops",
            "checklist_summary": {"counts": {"passed": 1, "warning": 1, "blocked": 0}, "metadata_only": True},
            "notes": "Plan metadata for issue smoke.",
        },
        OWNER_HEADERS,
        201,
    )
    rollout_plan_id = (plan_response.get("plan") or {}).get("rollout_plan_id")
    if not rollout_plan_id:
        raise AssertionError(f"Rollout plan was not created for issue smoke: {plan_response}")

    approval_response = post(
        "/api/platform/feature-bundle-rollout-approvals",
        {
            "rollout_plan_id": rollout_plan_id,
            "agency_id": agency_id,
            "status": "submitted",
            "reviewer": "Platform Ops",
            "notes": "Approval metadata for issue smoke.",
        },
        OWNER_HEADERS,
        201,
    )
    approval_id = (approval_response.get("approval") or {}).get("approval_id")
    if not approval_id:
        raise AssertionError(f"Approval was not created for issue smoke: {approval_response}")

    dependency_response = post(
        "/api/platform/feature-bundle-dependencies",
        {
            "agency_id": agency_id,
            "bundle_id": bundle_id,
            "rollout_plan_id": rollout_plan_id,
            "dependency_type": "readiness_checklist",
            "depends_on": {
                "reference_type": "readiness_checklist",
                "reference_id": "readiness-issue-smoke",
                "label": "Readiness checklist issue smoke",
            },
            "status": "warning",
            "notes": "Dependency metadata for issue smoke.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    dependency_id = (dependency_response.get("dependency") or {}).get("dependency_id")
    if not dependency_id:
        raise AssertionError(f"Dependency was not created for issue smoke: {dependency_response}")

    risk_response = post(
        "/api/platform/feature-bundle-rollout-risks",
        {
            "agency_id": agency_id,
            "bundle_id": bundle_id,
            "rollout_plan_id": rollout_plan_id,
            "dependency_id": dependency_id,
            "title": "Documentation gap risk smoke",
            "description": "Risk metadata for issue smoke.",
            "impact": "high",
            "likelihood": "possible",
            "status": "open",
            "mitigation_notes": "Review documentation metadata.",
            "owner": "Platform Ops",
            "review_notes": "No enforcement.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    risk_id = (risk_response.get("risk") or {}).get("risk_id")
    if not risk_id:
        raise AssertionError(f"Risk was not created for issue smoke: {risk_response}")

    created = post(
        "/api/platform/feature-bundle-rollout-issues",
        {
            "agency_id": agency_id,
            "bundle_id": bundle_id,
            "rollout_plan_id": rollout_plan_id,
            "risk_id": risk_id,
            "dependency_id": dependency_id,
            "approval_id": approval_id,
            "title": "Approval comment needs follow-up",
            "description": "Issue metadata only; no activation or blocking.",
            "severity": "high",
            "status": "open",
            "owner": "Platform Ops",
            "resolution_notes": "Assign follow-up owner.",
            "review_notes": "No notification sent.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    if created.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected create phase: {created.get('phase')}")
    assert_disabled_response(created)
    issue = created.get("issue") or {}
    assert_issue_shape(issue)
    issue_id = issue.get("issue_id")
    if not issue_id:
        raise AssertionError(f"Issue id missing: {created}")

    updated = put(
        f"/api/platform/feature-bundle-rollout-issues/{issue_id}",
        {
            "severity": "critical",
            "status": "in_review",
            "resolution_notes": "Resolution is being reviewed as metadata only.",
            "review_notes": "Still no execution.",
            "metadata": {"updated": True, "metadata_only": True},
        },
        OWNER_HEADERS,
    )
    assert_disabled_response(updated)
    updated_issue = updated.get("issue") or {}
    assert_issue_shape(updated_issue)
    if updated_issue.get("severity") != "critical" or updated_issue.get("status") != "in_review":
        raise AssertionError(f"Issue update did not persist metadata: {updated}")

    platform_list = get(f"/api/platform/feature-bundle-rollout-issues?bundle_id={bundle_id}", OWNER_HEADERS)
    assert_disabled_response(platform_list)
    if not any(item.get("issue_id") == issue_id for item in platform_list.get("items") or []):
        raise AssertionError(f"Platform issue list missing created issue: {platform_list}")

    for filter_query in [
        f"rollout_plan_id={rollout_plan_id}",
        f"agency_id={agency_id}",
        f"risk_id={risk_id}",
        f"dependency_id={dependency_id}",
        f"approval_id={approval_id}",
        "severity=critical",
        "status=in_review",
    ]:
        filtered = get(f"/api/platform/feature-bundle-rollout-issues?{filter_query}", OWNER_HEADERS)
        if not any(item.get("issue_id") == issue_id for item in filtered.get("items") or []):
            raise AssertionError(f"Issue filter {filter_query} missing created issue: {filtered}")

    severity_filter = get("/api/platform/feature-bundle-rollout-issues?severity=critical", OWNER_HEADERS)
    if any(item.get("severity") != "critical" for item in severity_filter.get("items") or []):
        raise AssertionError(f"Issue severity filter returned another severity: {severity_filter}")

    platform_summary = get("/api/platform/feature-bundle-rollout-issues/summary", OWNER_HEADERS)
    assert_summary_shape(platform_summary)

    platform_detail = get(f"/api/platform/feature-bundle-rollout-issues/{issue_id}", OWNER_HEADERS)
    assert_disabled_response(platform_detail)
    assert_issue_shape(platform_detail.get("issue") or {})

    agency_list = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-issues?status=in_review", OWNER_HEADERS)
    assert_disabled_response(agency_list)
    if agency_list.get("read_only") is not True:
        raise AssertionError(f"Agency issue list should be read-only: {agency_list}")
    agency_item = next((item for item in agency_list.get("items") or [] if item.get("issue_id") == issue_id), None)
    if not agency_item:
        raise AssertionError(f"Agency issue list missing created issue: {agency_list}")
    assert_issue_shape(agency_item, agency_view=True)

    agency_summary = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-issues/summary", OWNER_HEADERS)
    assert_summary_shape(agency_summary, agency_id=agency_id)
    if agency_summary.get("read_only") is not True:
        raise AssertionError(f"Agency issue summary should be read-only: {agency_summary}")

    agency_detail = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-issues/{issue_id}", OWNER_HEADERS)
    assert_disabled_response(agency_detail)
    if agency_detail.get("read_only") is not True:
        raise AssertionError(f"Agency issue detail should be read-only: {agency_detail}")
    assert_issue_shape(agency_detail.get("issue") or {}, agency_view=True)

    deleted = request("DELETE", f"/api/platform/feature-bundle-rollout-issues/{issue_id}", {}, OWNER_HEADERS)[1]
    assert_disabled_response(deleted)
    if deleted.get("deleted") is not True or (deleted.get("issue") or {}).get("status") != "deleted":
        raise AssertionError(f"Issue delete should be metadata-only soft delete: {deleted}")

    after_delete = get(f"/api/platform/feature-bundle-rollout-issues?bundle_id={bundle_id}", OWNER_HEADERS)
    if any(item.get("issue_id") == issue_id for item in after_delete.get("items") or []):
        raise AssertionError(f"Default issue list should exclude deleted metadata: {after_delete}")
    include_deleted = get(f"/api/platform/feature-bundle-rollout-issues?bundle_id={bundle_id}&include_deleted=true", OWNER_HEADERS)
    if not any(item.get("issue_id") == issue_id for item in include_deleted.get("items") or []):
        raise AssertionError(f"include_deleted should expose metadata-deleted issue: {include_deleted}")

    request("POST", f"/api/agencies/{agency_id}/feature-bundle-rollout-issues", {"title": "blocked"}, OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/feature-bundle-rollout-issues/{issue_id}", {"status": "closed"}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/feature-bundle-rollout-issues/{issue_id}", {}, OWNER_HEADERS, 405)


def assert_issue_shape(issue: dict, *, agency_view: bool = False) -> None:
    for key in [
        "issue_id",
        "title",
        "severity",
        "status",
        "metadata_only",
        "issue_log_metadata_only",
    ]:
        if key not in issue:
            raise AssertionError(f"Issue missing {key}: {issue}")
    if issue.get("severity") not in ISSUE_SEVERITIES:
        raise AssertionError(f"Issue severity is invalid: {issue}")
    if issue.get("status") not in ISSUE_STATUSES:
        raise AssertionError(f"Issue status is invalid: {issue}")
    if agency_view and issue.get("read_only") is not True:
        raise AssertionError(f"Agency issue should be read-only: {issue}")
    assert_disabled_response(issue)


def assert_summary_shape(payload: dict, *, agency_id: str | None = None) -> None:
    if payload.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected summary phase: {payload}")
    if agency_id is not None and payload.get("agency_id") != agency_id:
        raise AssertionError(f"Agency issue summary did not stay agency-scoped: {payload}")
    assert_disabled_response(payload)
    summary = payload.get("summary") or {}
    for key in ["by_status", "by_severity", "total_count"]:
        if key not in summary:
            raise AssertionError(f"Issue summary malformed: {payload}")
    if not ISSUE_STATUSES.issubset(set((summary.get("by_status") or {}).keys())):
        raise AssertionError(f"Issue summary missing statuses: {payload}")
    if not ISSUE_SEVERITIES.issubset(set((summary.get("by_severity") or {}).keys())):
        raise AssertionError(f"Issue summary missing severities: {payload}")


def main() -> int:
    verify_model_and_collection_registration()
    openapi = get("/openapi.json")
    verify_routes(openapi.get("paths") or {})
    verify_frontend_and_docs()
    verify_readiness()
    verify_endpoint_behavior()
    print("Phase 40.9 feature bundle rollout issue log foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
