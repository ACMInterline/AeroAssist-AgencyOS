#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import (
    FeatureBundleRolloutDecision,
    FeatureBundleRolloutDecisionCategory,
    FeatureBundleRolloutDecisionCreate,
    FeatureBundleRolloutDecisionStatus,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_50_5_airline_operational_capability_matrix_foundation"
ROOT = Path(__file__).resolve().parents[2]
DECISION_CATEGORIES = {"readiness", "approval", "schedule", "dependency", "risk", "issue", "rollout_scope", "operational", "governance"}
DECISION_STATUSES = {"draft", "proposed", "accepted", "deferred", "rejected", "superseded", "archived"}


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
    create_payload = FeatureBundleRolloutDecisionCreate(
        id="decision-smoke",
        rollout_plan_id="plan-smoke",
        rollout_phase="approval",
        decision_title="Proceed with reviewed metadata",
        decision_summary="Decision register smoke summary.",
        decision_reason="Readiness and approval metadata were reviewed.",
        decision_category=FeatureBundleRolloutDecisionCategory.GOVERNANCE,
        decision_status=FeatureBundleRolloutDecisionStatus.ACCEPTED,
        decision_owner="Platform Ops",
        related_bundle_ids=["bundle-smoke"],
        related_dependency_ids=["dependency-smoke"],
        related_risk_ids=["risk-smoke"],
        related_issue_ids=["issue-smoke"],
        timeline_reference_ids=["timeline-smoke"],
        notes="Metadata only.",
        metadata={"smoke": True},
    )
    decision = FeatureBundleRolloutDecision(**create_payload.model_dump(mode="json", exclude_none=True))
    dumped = decision.model_dump(mode="json")
    if dumped.get("decision_category") != "governance" or dumped.get("decision_status") != "accepted":
        raise AssertionError(f"Decision dimensions were not preserved: {dumped}")
    for flag in [
        "metadata_only",
        "decision_register_metadata_only",
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
            raise AssertionError(f"Decision model missing disabled flag {flag}: {dumped}")
    if "feature_bundle_rollout_decisions" not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("Feature bundle rollout decisions collection is not registered.")
    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "feature_bundle_rollout_decisions_id_unique",
        "feature_bundle_rollout_decisions_plan_status_lookup",
        "feature_bundle_rollout_decisions_category_status_lookup",
        "feature_bundle_rollout_decisions_owner_lookup",
        "feature_bundle_rollout_decisions_decision_date_lookup",
        "feature_bundle_rollout_decisions_related_bundle_lookup",
        "feature_bundle_rollout_decisions_related_dependency_lookup",
        "feature_bundle_rollout_decisions_related_risk_lookup",
        "feature_bundle_rollout_decisions_related_issue_lookup",
        "feature_bundle_rollout_decisions_created_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Feature bundle rollout decision index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    expected_methods = {
        "/api/platform/feature-bundle-rollout-decisions": {"get", "post"},
        "/api/platform/feature-bundle-rollout-decisions/summary": {"get"},
        "/api/platform/feature-bundle-rollout-decisions/{decision_id}": {"get", "put", "delete"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-decisions": {"get"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-decisions/summary": {"get"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-decisions/{decision_id}": {"get"},
    }
    for path, methods in expected_methods.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in [
        "/api/agencies/{agency_id}/feature-bundle-rollout-decisions",
        "/api/agencies/{agency_id}/feature-bundle-rollout-decisions/summary",
        "/api/agencies/{agency_id}/feature-bundle-rollout-decisions/{decision_id}",
    ]:
        methods = set(paths.get(path, {}).keys())
        blocked_methods = methods & {"post", "put", "patch", "delete"}
        if blocked_methods:
            raise AssertionError(f"Agency feature bundle rollout decision route is not read-only: {path} {sorted(blocked_methods)}")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Feature Bundle Rollout Decisions"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Rollout Decisions"),
        (ROOT / "frontend/src/App.jsx", "/platform/feature-bundle-rollout-decisions"),
        (ROOT / "frontend/src/App.jsx", "/agency/rollout-decisions"),
        (ROOT / "frontend/src/pages/platform/FeatureBundleRolloutDecisionsPage.jsx", "Feature Bundle Rollout Decisions"),
        (ROOT / "frontend/src/pages/platform/FeatureBundleRolloutDecisionsPage.jsx", "Metadata-only decision register"),
        (ROOT / "frontend/src/pages/platform/FeatureBundleRolloutDecisionsPage.jsx", "Timeline references"),
        (ROOT / "frontend/src/pages/agency/RolloutDecisionsPage.jsx", "Rollout Decisions"),
        (ROOT / "frontend/src/pages/agency/RolloutDecisionsPage.jsx", "Read-only rollout decision metadata"),
        (ROOT / "docs/architecture/feature-bundle-rollout-decision-register-foundation.md", "Feature Bundle Rollout Decision Register Foundation"),
        (ROOT / "README.md", "Phase 40.10 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 40.10: Feature Bundle Rollout Decision Register Foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "Phase 40.10 adds feature bundle rollout decision register metadata"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "Phase 40.10 adds feature bundle rollout decision APIs"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Feature bundle rollout decision register"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Feature bundle rollout decision register"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/FeatureBundleRolloutDecisionsPage.jsx",
        ROOT / "frontend/src/pages/agency/RolloutDecisionsPage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)
    for path in [
        ROOT / "frontend/src/pages/platform/FeatureBundleRolloutDecisionsPage.jsx",
        ROOT / "frontend/src/pages/agency/RolloutDecisionsPage.jsx",
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
    section = readiness.get("feature_bundle_rollout_decision_register_foundation") or {}
    for flag in [
        "feature_bundle_rollout_decisions_enabled",
        "feature_bundle_rollout_decision_category_metadata_enabled",
        "feature_bundle_rollout_decision_status_metadata_enabled",
        "platform_decision_metadata_crud_enabled",
        "agency_decision_read_only_enabled",
        "decision_filter_by_rollout_enabled",
        "decision_filter_by_category_enabled",
        "decision_filter_by_owner_enabled",
        "decision_filter_by_status_enabled",
        "decision_related_bundle_references_enabled",
        "decision_related_dependency_references_enabled",
        "decision_related_risk_references_enabled",
        "decision_related_issue_references_enabled",
        "decision_timeline_references_enabled",
        "metadata_only",
        "decision_register_metadata_only",
        "decision_records_informational_only",
        "read_only_ui_enabled",
    ]:
        require_flag(section, flag)
    for flag in disabled_flags():
        require_flag(section, flag)
    require_flag(section, "readiness_required", False)
    for count_key in ["decision_count", "decision_status_counts", "decision_category_counts"]:
        if count_key not in section:
            raise AssertionError(f"Decision readiness missing count: {count_key}")
    if not DECISION_STATUSES.issubset(set((section.get("decision_status_counts") or {}).keys())):
        raise AssertionError(f"Decision readiness status counts missing statuses: {section}")
    if not DECISION_CATEGORIES.issubset(set((section.get("decision_category_counts") or {}).keys())):
        raise AssertionError(f"Decision readiness category counts missing categories: {section}")
    previous_section = readiness.get("feature_bundle_rollout_issue_log_foundation") or {}
    if previous_section.get("metadata_only") is not True:
        raise AssertionError("Previous issue log section should remain metadata-only.")


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
            "plan_name": "Phase 40.10 smoke decision rollout plan",
            "rollout_stage": "readiness_review",
            "target_start_date": "2027-03-10",
            "target_end_date": "2027-03-20",
            "rollout_owner": "Platform Ops",
            "notes": "Decision smoke plan metadata only.",
        },
        OWNER_HEADERS,
        201,
    )
    rollout_plan_id = (plan_response.get("plan") or {}).get("rollout_plan_id")
    if not rollout_plan_id:
        raise AssertionError(f"Rollout plan was not created for decision smoke: {plan_response}")

    dependency_id = create_dependency(agency_id, bundle_id, rollout_plan_id)
    risk_id = create_risk(agency_id, bundle_id, rollout_plan_id, dependency_id)
    issue_id = create_issue(agency_id, bundle_id, rollout_plan_id, risk_id, dependency_id)
    timeline_entry_id = create_timeline_entry(agency_id, bundle_id, rollout_plan_id)

    created = post(
        "/api/platform/feature-bundle-rollout-decisions",
        {
            "rollout_plan_id": rollout_plan_id,
            "rollout_phase": "approval",
            "decision_title": "Proceed after metadata review",
            "decision_summary": "Decision register smoke summary.",
            "decision_reason": "Readiness, risk, issue, and dependency metadata were reviewed.",
            "decision_category": "governance",
            "decision_status": "proposed",
            "decision_owner": "Platform Ops",
            "decision_date": "2027-03-05T10:00:00Z",
            "related_bundle_ids": [bundle_id],
            "related_dependency_ids": [dependency_id],
            "related_risk_ids": [risk_id],
            "related_issue_ids": [issue_id],
            "timeline_reference_ids": [timeline_entry_id],
            "notes": "Decision metadata only; no rollout execution.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    if created.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected create phase: {created.get('phase')}")
    assert_disabled_response(created)
    decision = created.get("decision") or {}
    assert_decision_shape(decision)
    decision_id = decision.get("id")
    if not decision_id:
        raise AssertionError(f"Decision id missing: {created}")

    updated = put(
        f"/api/platform/feature-bundle-rollout-decisions/{decision_id}",
        {
            "decision_status": "accepted",
            "decision_category": "operational",
            "decision_reason": "Accepted after metadata-only review.",
            "notes": "No automation triggered.",
            "metadata": {"updated": True, "metadata_only": True},
        },
        OWNER_HEADERS,
    )
    assert_disabled_response(updated)
    updated_decision = updated.get("decision") or {}
    assert_decision_shape(updated_decision)
    if updated_decision.get("decision_status") != "accepted" or updated_decision.get("decision_category") != "operational":
        raise AssertionError(f"Decision update did not persist metadata: {updated}")

    for filter_query in [
        f"rollout_plan_id={rollout_plan_id}",
        "category=operational",
        "owner=Platform%20Ops",
        "status=accepted",
    ]:
        filtered = get(f"/api/platform/feature-bundle-rollout-decisions?{filter_query}", OWNER_HEADERS)
        assert_disabled_response(filtered)
        if not any(item.get("id") == decision_id for item in filtered.get("items") or []):
            raise AssertionError(f"Decision filter {filter_query} missing created decision: {filtered}")

    category_filter = get("/api/platform/feature-bundle-rollout-decisions?category=operational", OWNER_HEADERS)
    if any(item.get("decision_category") != "operational" for item in category_filter.get("items") or []):
        raise AssertionError(f"Decision category filter returned another category: {category_filter}")

    platform_summary = get("/api/platform/feature-bundle-rollout-decisions/summary", OWNER_HEADERS)
    assert_summary_shape(platform_summary)

    platform_detail = get(f"/api/platform/feature-bundle-rollout-decisions/{decision_id}", OWNER_HEADERS)
    assert_disabled_response(platform_detail)
    assert_decision_shape(platform_detail.get("decision") or {})

    agency_list = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-decisions?status=accepted", OWNER_HEADERS)
    assert_disabled_response(agency_list)
    if agency_list.get("read_only") is not True:
        raise AssertionError(f"Agency decision list should be read-only: {agency_list}")
    agency_item = next((item for item in agency_list.get("items") or [] if item.get("id") == decision_id), None)
    if not agency_item:
        raise AssertionError(f"Agency decision list missing created decision: {agency_list}")
    assert_decision_shape(agency_item, agency_view=True)

    agency_summary = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-decisions/summary", OWNER_HEADERS)
    assert_summary_shape(agency_summary, agency_id=agency_id)
    if agency_summary.get("read_only") is not True:
        raise AssertionError(f"Agency decision summary should be read-only: {agency_summary}")

    agency_detail = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-decisions/{decision_id}", OWNER_HEADERS)
    assert_disabled_response(agency_detail)
    if agency_detail.get("read_only") is not True:
        raise AssertionError(f"Agency decision detail should be read-only: {agency_detail}")
    assert_decision_shape(agency_detail.get("decision") or {}, agency_view=True)

    deleted = request("DELETE", f"/api/platform/feature-bundle-rollout-decisions/{decision_id}", {}, OWNER_HEADERS)[1]
    assert_disabled_response(deleted)
    if deleted.get("deleted") is not True or (deleted.get("decision") or {}).get("decision_status") != "archived":
        raise AssertionError(f"Decision delete should be metadata-only archive: {deleted}")

    after_delete = get(f"/api/platform/feature-bundle-rollout-decisions?rollout_plan_id={rollout_plan_id}", OWNER_HEADERS)
    if any(item.get("id") == decision_id for item in after_delete.get("items") or []):
        raise AssertionError(f"Default decision list should exclude archived-delete metadata: {after_delete}")
    include_archived = get(f"/api/platform/feature-bundle-rollout-decisions?rollout_plan_id={rollout_plan_id}&include_archived=true", OWNER_HEADERS)
    if not any(item.get("id") == decision_id for item in include_archived.get("items") or []):
        raise AssertionError(f"include_archived should expose metadata-archived decision: {include_archived}")

    request("POST", f"/api/agencies/{agency_id}/feature-bundle-rollout-decisions", {"decision_title": "blocked"}, OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/feature-bundle-rollout-decisions/{decision_id}", {"decision_status": "rejected"}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/feature-bundle-rollout-decisions/{decision_id}", {}, OWNER_HEADERS, 405)


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
                "reference_id": "readiness-decision-smoke",
                "label": "Readiness checklist decision smoke",
            },
            "status": "warning",
            "notes": "Dependency metadata for decision smoke.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    dependency_id = (response.get("dependency") or {}).get("dependency_id")
    if not dependency_id:
        raise AssertionError(f"Dependency was not created for decision smoke: {response}")
    return dependency_id


def create_risk(agency_id: str, bundle_id: str, rollout_plan_id: str, dependency_id: str) -> str:
    response = post(
        "/api/platform/feature-bundle-rollout-risks",
        {
            "agency_id": agency_id,
            "bundle_id": bundle_id,
            "rollout_plan_id": rollout_plan_id,
            "dependency_id": dependency_id,
            "title": "Decision dependency risk smoke",
            "description": "Risk metadata for decision smoke.",
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
        raise AssertionError(f"Risk was not created for decision smoke: {response}")
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
            "title": "Decision follow-up issue smoke",
            "description": "Issue metadata for decision smoke.",
            "severity": "high",
            "status": "open",
            "owner": "Platform Ops",
            "resolution_notes": "Record decision rationale.",
            "review_notes": "No notification sent.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    issue_id = (response.get("issue") or {}).get("issue_id")
    if not issue_id:
        raise AssertionError(f"Issue was not created for decision smoke: {response}")
    return issue_id


def create_timeline_entry(agency_id: str, bundle_id: str, rollout_plan_id: str) -> str:
    response = post(
        "/api/platform/feature-bundle-rollout-timeline",
        {
            "rollout_plan_id": rollout_plan_id,
            "agency_id": agency_id,
            "bundle_id": bundle_id,
            "event_type": "approval_requested",
            "occurred_at": "2027-03-04T10:00:00Z",
            "description": "Decision smoke timeline reference.",
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
    entry_id = (response.get("entry") or {}).get("timeline_entry_id")
    if not entry_id:
        raise AssertionError(f"Timeline entry was not created for decision smoke: {response}")
    return entry_id


def assert_decision_shape(decision: dict, *, agency_view: bool = False) -> None:
    for key in [
        "id",
        "rollout_plan_id",
        "decision_title",
        "decision_category",
        "decision_status",
        "metadata_only",
        "decision_register_metadata_only",
        "related_bundle_ids",
        "related_dependency_ids",
        "related_risk_ids",
        "related_issue_ids",
        "timeline_reference_ids",
        "related_bundles",
        "related_dependencies",
        "related_risks",
        "related_issues",
        "timeline_references",
    ]:
        if key not in decision:
            raise AssertionError(f"Decision response missing {key}: {decision}")
    if decision.get("decision_category") not in DECISION_CATEGORIES:
        raise AssertionError(f"Decision category is invalid: {decision}")
    if decision.get("decision_status") not in DECISION_STATUSES:
        raise AssertionError(f"Decision status is invalid: {decision}")
    if not isinstance(decision.get("related_bundles"), list):
        raise AssertionError(f"Decision related bundles should be a list: {decision}")
    if not isinstance(decision.get("timeline_references"), list):
        raise AssertionError(f"Decision timeline references should be a list: {decision}")
    for flag in disabled_flags():
        if decision.get(flag) is not True:
            raise AssertionError(f"Decision missing disabled flag {flag}: {decision}")
    if agency_view and decision.get("read_only") is not True:
        raise AssertionError(f"Agency decision projection should be read-only: {decision}")


def assert_summary_shape(payload: dict, *, agency_id: str | None = None) -> None:
    assert_disabled_response(payload)
    summary = payload.get("summary") or {}
    for key in ["by_status", "by_category", "total_count", "related_bundle_count", "related_dependency_count", "related_risk_count", "related_issue_count"]:
        if key not in summary:
            raise AssertionError(f"Decision summary missing {key}: {payload}")
    if not DECISION_STATUSES.issubset(set((summary.get("by_status") or {}).keys())):
        raise AssertionError(f"Decision summary missing statuses: {payload}")
    if not DECISION_CATEGORIES.issubset(set((summary.get("by_category") or {}).keys())):
        raise AssertionError(f"Decision summary missing categories: {payload}")
    if agency_id and payload.get("agency_id") != agency_id:
        raise AssertionError(f"Agency summary should be scoped to {agency_id}: {payload}")


def main() -> int:
    verify_model_and_collection_registration()
    openapi = get("/openapi.json")
    verify_routes(openapi.get("paths") or {})
    verify_frontend_and_docs()
    verify_readiness()
    verify_endpoint_behavior()
    print("Phase 40.10 feature bundle rollout decision register foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
