#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import (
    FeatureBundleRolloutRisk,
    FeatureBundleRolloutRiskCreate,
    FeatureBundleRolloutRiskImpact,
    FeatureBundleRolloutRiskLikelihood,
    FeatureBundleRolloutRiskStatus,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_56_2_journey_option_fare_brand_composition_workspace_foundation"
ROOT = Path(__file__).resolve().parents[2]
RISK_IMPACTS = {"low", "medium", "high", "critical"}
RISK_LIKELIHOODS = {"rare", "unlikely", "possible", "likely", "almost_certain"}
RISK_STATUSES = {"open", "reviewing", "mitigating", "mitigated", "accepted", "closed", "deleted"}


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
        "risk_decision_enforcement_disabled",
        "risk_enforcement_disabled",
        "risk_blocking_disabled",
        "rollout_blocking_disabled",
        "feature_bundle_activation_disabled",
        "feature_bundles_enablement_disabled",
        "notification_sending_disabled",
        "notifications_disabled",
        "external_provider_calls_disabled",
        "provider_calls_disabled",
        "provider_execution_disabled",
        "automation_disabled",
        "background_jobs_disabled",
    ]


def forbidden_enabled_flags() -> list[str]:
    return [
        "rollout_execution_enabled",
        "risk_decision_enforcement_enabled",
        "risk_enforcement_enabled",
        "risk_blocking_enabled",
        "rollout_blocking_enabled",
        "feature_bundle_activation_enabled",
        "notification_sending_enabled",
        "provider_calls_enabled",
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
    create_payload = FeatureBundleRolloutRiskCreate(
        agency_id="agency-smoke",
        bundle_id="bundle-smoke",
        rollout_plan_id="plan-smoke",
        dependency_id="dependency-smoke",
        title="Missing approval smoke",
        description="Metadata-only risk smoke.",
        impact=FeatureBundleRolloutRiskImpact.HIGH,
        likelihood=FeatureBundleRolloutRiskLikelihood.LIKELY,
        status=FeatureBundleRolloutRiskStatus.REVIEWING,
        mitigation_notes="Review approval metadata.",
        owner="Platform Ops",
        review_notes="No enforcement.",
        metadata={"smoke": True},
    )
    risk = FeatureBundleRolloutRisk(**create_payload.model_dump(mode="json", exclude_none=True))
    dumped = risk.model_dump(mode="json")
    if dumped.get("impact") != "high" or dumped.get("likelihood") != "likely" or dumped.get("status") != "reviewing":
        raise AssertionError(f"Risk dimensions were not preserved: {dumped}")
    for flag in [
        "metadata_only",
        "risk_register_metadata_only",
        "rollout_execution_disabled",
        "risk_decision_enforcement_disabled",
        "risk_blocking_disabled",
        "feature_bundle_activation_disabled",
        "notification_sending_disabled",
        "external_provider_calls_disabled",
        "automation_disabled",
    ]:
        if dumped.get(flag) is not True:
            raise AssertionError(f"Risk model missing disabled flag {flag}: {dumped}")
    if "feature_bundle_rollout_risks" not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("Feature bundle rollout risks collection is not agency-owned/registered.")
    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "feature_bundle_rollout_risks_id_unique",
        "feature_bundle_rollout_risks_risk_unique",
        "feature_bundle_rollout_risks_agency_status_lookup",
        "feature_bundle_rollout_risks_bundle_status_lookup",
        "feature_bundle_rollout_risks_plan_status_lookup",
        "feature_bundle_rollout_risks_dependency_lookup",
        "feature_bundle_rollout_risks_impact_likelihood_lookup",
        "feature_bundle_rollout_risks_created_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Feature bundle rollout risk index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    expected_methods = {
        "/api/platform/feature-bundle-rollout-risks": {"get", "post"},
        "/api/platform/feature-bundle-rollout-risks/summary": {"get"},
        "/api/platform/feature-bundle-rollout-risks/{risk_id}": {"get", "put", "delete"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-risks": {"get"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-risks/summary": {"get"},
        "/api/agencies/{agency_id}/feature-bundle-rollout-risks/{risk_id}": {"get"},
    }
    for path, methods in expected_methods.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in [
        "/api/agencies/{agency_id}/feature-bundle-rollout-risks",
        "/api/agencies/{agency_id}/feature-bundle-rollout-risks/summary",
        "/api/agencies/{agency_id}/feature-bundle-rollout-risks/{risk_id}",
    ]:
        methods = set(paths.get(path, {}).keys())
        blocked_methods = methods & {"post", "put", "patch", "delete"}
        if blocked_methods:
            raise AssertionError(f"Agency feature bundle rollout risk route is not read-only: {path} {sorted(blocked_methods)}")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Feature Bundle Rollout Risks"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Rollout Risks"),
        (ROOT / "frontend/src/App.jsx", "/platform/feature-bundle-rollout-risks"),
        (ROOT / "frontend/src/App.jsx", "/agency/rollout-risks"),
        (ROOT / "frontend/src/pages/platform/FeatureBundleRolloutRisksPage.jsx", "Feature Bundle Rollout Risks"),
        (ROOT / "frontend/src/pages/platform/FeatureBundleRolloutRisksPage.jsx", "Metadata-only rollout risk register"),
        (ROOT / "frontend/src/pages/agency/RolloutRisksPage.jsx", "Rollout Risks"),
        (ROOT / "frontend/src/pages/agency/RolloutRisksPage.jsx", "Read-only rollout risk metadata"),
        (ROOT / "docs/architecture/feature-bundle-rollout-risk-register-foundation.md", "Feature Bundle Rollout Risk Register Foundation"),
        (ROOT / "README.md", "Phase 40.8 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 40.8: Feature Bundle Rollout Risk Register Foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "Phase 40.8 adds feature bundle rollout risk register metadata"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "Phase 40.8 adds feature bundle rollout risk APIs"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Feature bundle rollout risk register"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Feature bundle rollout risk register"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/FeatureBundleRolloutRisksPage.jsx",
        ROOT / "frontend/src/pages/agency/RolloutRisksPage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)
    for path in [
        ROOT / "frontend/src/pages/platform/FeatureBundleRolloutRisksPage.jsx",
        ROOT / "frontend/src/pages/agency/RolloutRisksPage.jsx",
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
    section = readiness.get("feature_bundle_rollout_risk_register_foundation") or {}
    for flag in [
        "feature_bundle_rollout_risks_enabled",
        "feature_bundle_rollout_risk_impact_metadata_enabled",
        "feature_bundle_rollout_risk_likelihood_metadata_enabled",
        "feature_bundle_rollout_risk_status_metadata_enabled",
        "platform_risk_metadata_crud_enabled",
        "agency_risk_read_only_enabled",
        "risk_filter_by_agency_enabled",
        "risk_filter_by_bundle_enabled",
        "risk_filter_by_rollout_plan_enabled",
        "risk_filter_by_status_enabled",
        "risk_filter_by_impact_enabled",
        "risk_filter_by_likelihood_enabled",
        "metadata_only",
        "risk_register_metadata_only",
        "risk_decisions_informational_only",
    ]:
        require_flag(section, flag)
    for flag in disabled_flags():
        require_flag(section, flag)
    require_flag(section, "readiness_required", False)
    for count_key in ["risk_count", "risk_status_counts", "risk_impact_counts", "risk_likelihood_counts"]:
        if count_key not in section:
            raise AssertionError(f"Risk readiness missing count: {count_key}")
    if not RISK_STATUSES.issubset(set((section.get("risk_status_counts") or {}).keys())):
        raise AssertionError(f"Risk readiness status counts missing statuses: {section}")
    if not RISK_IMPACTS.issubset(set((section.get("risk_impact_counts") or {}).keys())):
        raise AssertionError(f"Risk readiness impact counts missing impacts: {section}")
    if not RISK_LIKELIHOODS.issubset(set((section.get("risk_likelihood_counts") or {}).keys())):
        raise AssertionError(f"Risk readiness likelihood counts missing likelihoods: {section}")
    previous_section = readiness.get("feature_bundle_dependency_foundation") or {}
    if previous_section.get("metadata_only") is not True:
        raise AssertionError("Previous dependency section should remain metadata-only.")


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
            "plan_name": "Phase 40.8 smoke risk rollout plan",
            "rollout_stage": "readiness_review",
            "target_start_date": "2027-01-10",
            "target_end_date": "2027-01-20",
            "rollout_owner": "Platform Ops",
            "checklist_summary": {"counts": {"passed": 2, "warning": 1, "blocked": 0}, "metadata_only": True},
            "notes": "Plan metadata for risk smoke.",
        },
        OWNER_HEADERS,
        201,
    )
    rollout_plan_id = (plan_response.get("plan") or {}).get("rollout_plan_id")
    if not rollout_plan_id:
        raise AssertionError(f"Rollout plan was not created for risk smoke: {plan_response}")

    dependency_response = post(
        "/api/platform/feature-bundle-dependencies",
        {
            "agency_id": agency_id,
            "bundle_id": bundle_id,
            "rollout_plan_id": rollout_plan_id,
            "dependency_type": "approval",
            "depends_on": {
                "reference_type": "approval",
                "reference_id": "approval-risk-smoke",
                "label": "Approval dependency smoke",
            },
            "status": "warning",
            "notes": "Dependency metadata for risk smoke.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    dependency_id = (dependency_response.get("dependency") or {}).get("dependency_id")
    if not dependency_id:
        raise AssertionError(f"Dependency was not created for risk smoke: {dependency_response}")

    created = post(
        "/api/platform/feature-bundle-rollout-risks",
        {
            "agency_id": agency_id,
            "bundle_id": bundle_id,
            "rollout_plan_id": rollout_plan_id,
            "dependency_id": dependency_id,
            "title": "Missing approval risk smoke",
            "description": "Approval dependency may need human review.",
            "impact": "high",
            "likelihood": "likely",
            "status": "open",
            "mitigation_notes": "Review approval metadata before future activation.",
            "owner": "Platform Ops",
            "review_notes": "Metadata only. No enforcement.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    if created.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected create phase: {created.get('phase')}")
    assert_disabled_response(created)
    risk = created.get("risk") or {}
    assert_risk_shape(risk)
    risk_id = risk.get("risk_id")
    if not risk_id:
        raise AssertionError(f"Risk id missing: {created}")

    updated = put(
        f"/api/platform/feature-bundle-rollout-risks/{risk_id}",
        {
            "impact": "critical",
            "likelihood": "possible",
            "status": "reviewing",
            "mitigation_notes": "Confirm owner review notes.",
            "review_notes": "Updated metadata only.",
            "metadata": {"updated": True, "metadata_only": True},
        },
        OWNER_HEADERS,
    )
    assert_disabled_response(updated)
    updated_risk = updated.get("risk") or {}
    assert_risk_shape(updated_risk)
    if updated_risk.get("impact") != "critical" or updated_risk.get("status") != "reviewing":
        raise AssertionError(f"Risk update did not persist metadata: {updated}")

    platform_list = get(f"/api/platform/feature-bundle-rollout-risks?bundle_id={bundle_id}", OWNER_HEADERS)
    assert_disabled_response(platform_list)
    if not any(item.get("risk_id") == risk_id for item in platform_list.get("items") or []):
        raise AssertionError(f"Platform risk list missing created risk: {platform_list}")

    for filter_query in [
        f"rollout_plan_id={rollout_plan_id}",
        f"agency_id={agency_id}",
        "status=reviewing",
        "impact=critical",
        "likelihood=possible",
    ]:
        filtered = get(f"/api/platform/feature-bundle-rollout-risks?{filter_query}", OWNER_HEADERS)
        if not any(item.get("risk_id") == risk_id for item in filtered.get("items") or []):
            raise AssertionError(f"Risk filter {filter_query} missing created risk: {filtered}")

    status_filter = get("/api/platform/feature-bundle-rollout-risks?status=reviewing", OWNER_HEADERS)
    if any(item.get("status") != "reviewing" for item in status_filter.get("items") or []):
        raise AssertionError(f"Risk status filter returned another status: {status_filter}")

    platform_summary = get("/api/platform/feature-bundle-rollout-risks/summary", OWNER_HEADERS)
    assert_summary_shape(platform_summary)

    platform_detail = get(f"/api/platform/feature-bundle-rollout-risks/{risk_id}", OWNER_HEADERS)
    assert_disabled_response(platform_detail)
    assert_risk_shape(platform_detail.get("risk") or {})

    agency_list = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-risks?status=reviewing", OWNER_HEADERS)
    assert_disabled_response(agency_list)
    if agency_list.get("read_only") is not True:
        raise AssertionError(f"Agency risk list should be read-only: {agency_list}")
    agency_item = next((item for item in agency_list.get("items") or [] if item.get("risk_id") == risk_id), None)
    if not agency_item:
        raise AssertionError(f"Agency risk list missing created risk: {agency_list}")
    assert_risk_shape(agency_item, agency_view=True)

    agency_summary = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-risks/summary", OWNER_HEADERS)
    assert_summary_shape(agency_summary, agency_id=agency_id)
    if agency_summary.get("read_only") is not True:
        raise AssertionError(f"Agency risk summary should be read-only: {agency_summary}")

    agency_detail = get(f"/api/agencies/{agency_id}/feature-bundle-rollout-risks/{risk_id}", OWNER_HEADERS)
    assert_disabled_response(agency_detail)
    if agency_detail.get("read_only") is not True:
        raise AssertionError(f"Agency risk detail should be read-only: {agency_detail}")
    assert_risk_shape(agency_detail.get("risk") or {}, agency_view=True)

    deleted = request("DELETE", f"/api/platform/feature-bundle-rollout-risks/{risk_id}", {}, OWNER_HEADERS)[1]
    assert_disabled_response(deleted)
    if deleted.get("deleted") is not True or (deleted.get("risk") or {}).get("status") != "deleted":
        raise AssertionError(f"Risk delete should be metadata-only soft delete: {deleted}")

    after_delete = get(f"/api/platform/feature-bundle-rollout-risks?bundle_id={bundle_id}", OWNER_HEADERS)
    if any(item.get("risk_id") == risk_id for item in after_delete.get("items") or []):
        raise AssertionError(f"Default risk list should exclude deleted metadata: {after_delete}")
    include_deleted = get(f"/api/platform/feature-bundle-rollout-risks?bundle_id={bundle_id}&include_deleted=true", OWNER_HEADERS)
    if not any(item.get("risk_id") == risk_id for item in include_deleted.get("items") or []):
        raise AssertionError(f"include_deleted should expose metadata-deleted risk: {include_deleted}")

    request("POST", f"/api/agencies/{agency_id}/feature-bundle-rollout-risks", {"title": "blocked"}, OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/feature-bundle-rollout-risks/{risk_id}", {"status": "closed"}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/feature-bundle-rollout-risks/{risk_id}", {}, OWNER_HEADERS, 405)


def assert_risk_shape(risk: dict, *, agency_view: bool = False) -> None:
    for key in [
        "risk_id",
        "title",
        "impact",
        "likelihood",
        "status",
        "metadata_only",
        "risk_register_metadata_only",
    ]:
        if key not in risk:
            raise AssertionError(f"Risk missing {key}: {risk}")
    if risk.get("impact") not in RISK_IMPACTS:
        raise AssertionError(f"Risk impact is invalid: {risk}")
    if risk.get("likelihood") not in RISK_LIKELIHOODS:
        raise AssertionError(f"Risk likelihood is invalid: {risk}")
    if risk.get("status") not in RISK_STATUSES:
        raise AssertionError(f"Risk status is invalid: {risk}")
    if agency_view and risk.get("read_only") is not True:
        raise AssertionError(f"Agency risk should be read-only: {risk}")
    assert_disabled_response(risk)


def assert_summary_shape(payload: dict, *, agency_id: str | None = None) -> None:
    if payload.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected summary phase: {payload}")
    if agency_id is not None and payload.get("agency_id") != agency_id:
        raise AssertionError(f"Agency risk summary did not stay agency-scoped: {payload}")
    assert_disabled_response(payload)
    summary = payload.get("summary") or {}
    for key in ["by_status", "by_impact", "by_likelihood", "total_count"]:
        if key not in summary:
            raise AssertionError(f"Risk summary malformed: {payload}")
    if not RISK_STATUSES.issubset(set((summary.get("by_status") or {}).keys())):
        raise AssertionError(f"Risk summary missing statuses: {payload}")
    if not RISK_IMPACTS.issubset(set((summary.get("by_impact") or {}).keys())):
        raise AssertionError(f"Risk summary missing impacts: {payload}")
    if not RISK_LIKELIHOODS.issubset(set((summary.get("by_likelihood") or {}).keys())):
        raise AssertionError(f"Risk summary missing likelihoods: {payload}")


def main() -> int:
    verify_model_and_collection_registration()
    openapi = get("/openapi.json")
    verify_routes(openapi.get("paths") or {})
    verify_frontend_and_docs()
    verify_readiness()
    verify_endpoint_behavior()
    print("Phase 40.8 feature bundle rollout risk register foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
