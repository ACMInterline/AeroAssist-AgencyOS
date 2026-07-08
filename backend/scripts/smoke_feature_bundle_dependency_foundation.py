#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import (
    FeatureBundleDependency,
    FeatureBundleDependencyCreate,
    FeatureBundleDependencyReference,
    FeatureBundleDependencyType,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_50_4_airline_operational_knowledge_governance_foundation"
ROOT = Path(__file__).resolve().parents[2]
DEPENDENCY_TYPES = {"bundle", "capability", "approval", "rollout_plan", "schedule", "readiness_checklist", "other"}


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
        "background_jobs_disabled",
        "scheduled_jobs_disabled",
        "dependency_enforcement_disabled",
        "rollout_blocking_disabled",
        "feature_bundle_activation_disabled",
        "feature_bundles_enablement_disabled",
        "permission_modification_disabled",
        "notification_sending_disabled",
        "notifications_disabled",
        "publishing_disabled",
        "provider_calls_disabled",
        "provider_execution_disabled",
        "automation_disabled",
    ]


def forbidden_enabled_flags() -> list[str]:
    return [
        "rollout_execution_enabled",
        "background_jobs_enabled",
        "dependency_enforcement_enabled",
        "rollout_blocking_enabled",
        "feature_bundle_activation_enabled",
        "permission_modification_enabled",
        "notification_sending_enabled",
        "publishing_enabled",
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
    reference = FeatureBundleDependencyReference(
        reference_type=FeatureBundleDependencyType.CAPABILITY,
        reference_id="capability-smoke",
        label="Capability smoke",
        capability_key="capability_smoke",
    )
    create_payload = FeatureBundleDependencyCreate(
        agency_id="agency-smoke",
        bundle_id="bundle-smoke",
        rollout_plan_id="plan-smoke",
        dependency_type=FeatureBundleDependencyType.CAPABILITY,
        depends_on=reference,
        status="warning",
        notes="Metadata-only dependency smoke.",
        metadata={"smoke": True},
    )
    dependency = FeatureBundleDependency(**create_payload.model_dump(mode="json", exclude_none=True))
    dumped = dependency.model_dump(mode="json")
    if dumped.get("dependency_type") != "capability":
        raise AssertionError(f"Dependency type was not preserved: {dumped}")
    if dumped.get("depends_on", {}).get("reference_type") != "capability":
        raise AssertionError(f"Dependency reference was not preserved: {dumped}")
    for flag in [
        "metadata_only",
        "dependency_metadata_only",
        "dependency_enforcement_disabled",
        "rollout_execution_disabled",
        "background_jobs_disabled",
        "rollout_blocking_disabled",
        "feature_bundle_activation_disabled",
        "permission_modification_disabled",
        "notification_sending_disabled",
        "publishing_disabled",
        "provider_calls_disabled",
        "automation_disabled",
    ]:
        if dumped.get(flag) is not True:
            raise AssertionError(f"Dependency model missing disabled flag {flag}: {dumped}")
    if "feature_bundle_dependencies" not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("Feature bundle dependencies collection is not agency-owned/registered.")
    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "feature_bundle_dependencies_id_unique",
        "feature_bundle_dependencies_dependency_unique",
        "feature_bundle_dependencies_agency_bundle_lookup",
        "feature_bundle_dependencies_plan_type_lookup",
        "feature_bundle_dependencies_bundle_type_lookup",
        "feature_bundle_dependencies_agency_type_lookup",
        "feature_bundle_dependencies_reference_lookup",
        "feature_bundle_dependencies_created_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Feature bundle dependency index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    expected_methods = {
        "/api/platform/feature-bundle-dependencies": {"get", "post"},
        "/api/platform/feature-bundle-dependencies/summary": {"get"},
        "/api/platform/feature-bundle-dependencies/{dependency_id}": {"get", "put", "delete"},
        "/api/agencies/{agency_id}/feature-bundle-dependencies": {"get"},
        "/api/agencies/{agency_id}/feature-bundle-dependencies/summary": {"get"},
        "/api/agencies/{agency_id}/feature-bundle-dependencies/{dependency_id}": {"get"},
    }
    for path, methods in expected_methods.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in [
        "/api/agencies/{agency_id}/feature-bundle-dependencies",
        "/api/agencies/{agency_id}/feature-bundle-dependencies/summary",
        "/api/agencies/{agency_id}/feature-bundle-dependencies/{dependency_id}",
    ]:
        methods = set(paths.get(path, {}).keys())
        blocked_methods = methods & {"post", "put", "patch", "delete"}
        if blocked_methods:
            raise AssertionError(f"Agency feature bundle dependency route is not read-only: {path} {sorted(blocked_methods)}")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Feature Bundle Dependencies"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Bundle Dependencies"),
        (ROOT / "frontend/src/App.jsx", "/platform/feature-bundle-dependencies"),
        (ROOT / "frontend/src/App.jsx", "/agency/bundle-dependencies"),
        (ROOT / "frontend/src/pages/platform/FeatureBundleDependenciesPage.jsx", "Feature Bundle Dependencies"),
        (ROOT / "frontend/src/pages/platform/FeatureBundleDependenciesPage.jsx", "Read-only dependency metadata"),
        (ROOT / "frontend/src/pages/agency/BundleDependenciesPage.jsx", "Bundle Dependencies"),
        (ROOT / "frontend/src/pages/agency/BundleDependenciesPage.jsx", "Read-only dependency metadata"),
        (ROOT / "docs/architecture/feature-bundle-dependency-foundation.md", "Feature Bundle Dependency Foundation"),
        (ROOT / "README.md", "Phase 40.7 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 40.7: Feature Bundle Rollout Dependency Foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "Phase 40.7 adds feature bundle dependency metadata"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "Phase 40.7 adds feature bundle dependency APIs"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Feature bundle dependencies"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Feature bundle dependencies"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/FeatureBundleDependenciesPage.jsx",
        ROOT / "frontend/src/pages/agency/BundleDependenciesPage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)
    for path in [
        ROOT / "frontend/src/pages/platform/FeatureBundleDependenciesPage.jsx",
        ROOT / "frontend/src/pages/agency/BundleDependenciesPage.jsx",
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
    section = readiness.get("feature_bundle_dependency_foundation") or {}
    for flag in [
        "feature_bundle_dependencies_enabled",
        "feature_bundle_dependency_reference_metadata_enabled",
        "feature_bundle_dependency_type_metadata_enabled",
        "platform_dependency_metadata_crud_enabled",
        "agency_dependency_read_only_enabled",
        "bundle_dependency_filter_enabled",
        "plan_dependency_filter_enabled",
        "agency_dependency_filter_enabled",
        "dependency_type_filter_enabled",
        "metadata_only",
        "dependency_metadata_only",
        "dependency_informational_only",
    ]:
        require_flag(section, flag)
    for flag in disabled_flags():
        require_flag(section, flag)
    require_flag(section, "readiness_required", False)
    for count_key in ["dependency_count", "dependency_type_counts"]:
        if count_key not in section:
            raise AssertionError(f"Dependency readiness missing count: {count_key}")
    if not DEPENDENCY_TYPES.issubset(set((section.get("dependency_type_counts") or {}).keys())):
        raise AssertionError(f"Dependency readiness type counts missing dependency types: {section}")
    previous_section = readiness.get("feature_bundle_rollout_timeline_foundation") or {}
    if previous_section.get("metadata_only") is not True:
        raise AssertionError("Previous rollout timeline section should remain metadata-only.")


def verify_endpoint_behavior() -> None:
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires seeded demo agency.")
    agency_id = agencies[0]["id"]
    bundles = get("/api/platform/feature-flag-bundles", OWNER_HEADERS).get("items") or []
    if len(bundles) < 1:
        raise AssertionError("Smoke requires feature flag bundle metadata.")
    bundle_id = next((item["bundle_id"] for item in bundles if item.get("bundle_key") == "core_agency"), bundles[0]["bundle_id"])
    depends_on_bundle_id = next((item["bundle_id"] for item in bundles if item["bundle_id"] != bundle_id), bundle_id)

    plan_response = post(
        "/api/platform/feature-bundle-rollout-plans",
        {
            "agency_id": agency_id,
            "bundle_id": bundle_id,
            "plan_name": "Phase 40.7 smoke dependency rollout plan",
            "rollout_stage": "readiness_review",
            "target_start_date": "2026-12-01",
            "target_end_date": "2026-12-15",
            "rollout_owner": "Platform Ops",
            "checklist_summary": {"counts": {"passed": 2, "warning": 1, "blocked": 0}, "metadata_only": True},
            "notes": "Plan metadata for dependency smoke.",
        },
        OWNER_HEADERS,
        201,
    )
    rollout_plan_id = (plan_response.get("plan") or {}).get("rollout_plan_id")
    if not rollout_plan_id:
        raise AssertionError(f"Rollout plan was not created for dependency smoke: {plan_response}")

    created = post(
        "/api/platform/feature-bundle-dependencies",
        {
            "agency_id": agency_id,
            "bundle_id": bundle_id,
            "rollout_plan_id": rollout_plan_id,
            "dependency_type": "bundle",
            "depends_on": {
                "reference_type": "bundle",
                "reference_id": depends_on_bundle_id,
                "bundle_id": depends_on_bundle_id,
                "label": "Core bundle dependency",
                "metadata": {"metadata_only": True},
            },
            "status": "informational",
            "notes": "Bundle dependency metadata only; no enforcement.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    if created.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected create phase: {created.get('phase')}")
    assert_disabled_response(created)
    dependency = created.get("dependency") or {}
    assert_dependency_shape(dependency)
    dependency_id = dependency.get("dependency_id")
    if not dependency_id:
        raise AssertionError(f"Dependency id missing: {created}")

    updated = put(
        f"/api/platform/feature-bundle-dependencies/{dependency_id}",
        {
            "dependency_type": "capability",
            "depends_on": {
                "reference_type": "capability",
                "reference_id": "capability_catalog_smoke",
                "capability_key": "capability_catalog_smoke",
                "label": "Capability catalog smoke",
            },
            "status": "warning",
            "notes": "Updated dependency metadata only; still no enforcement.",
            "metadata": {"updated": True, "metadata_only": True},
        },
        OWNER_HEADERS,
    )
    assert_disabled_response(updated)
    updated_dependency = updated.get("dependency") or {}
    assert_dependency_shape(updated_dependency)
    if updated_dependency.get("dependency_type") != "capability" or updated_dependency.get("status") != "warning":
        raise AssertionError(f"Dependency update did not persist metadata: {updated}")

    platform_list = get(f"/api/platform/feature-bundle-dependencies?bundle_id={bundle_id}", OWNER_HEADERS)
    assert_disabled_response(platform_list)
    if not any(item.get("dependency_id") == dependency_id for item in platform_list.get("items") or []):
        raise AssertionError(f"Platform dependency list missing created dependency: {platform_list}")

    plan_filter = get(f"/api/platform/feature-bundle-dependencies?rollout_plan_id={rollout_plan_id}", OWNER_HEADERS)
    if not any(item.get("dependency_id") == dependency_id for item in plan_filter.get("items") or []):
        raise AssertionError(f"Plan filter missing dependency: {plan_filter}")

    agency_filter = get(f"/api/platform/feature-bundle-dependencies?agency_id={agency_id}", OWNER_HEADERS)
    if not any(item.get("dependency_id") == dependency_id for item in agency_filter.get("items") or []):
        raise AssertionError(f"Agency filter missing dependency: {agency_filter}")

    type_filter = get(f"/api/platform/feature-bundle-dependencies?dependency_type=capability&bundle_id={bundle_id}", OWNER_HEADERS)
    if not any(item.get("dependency_id") == dependency_id for item in type_filter.get("items") or []):
        raise AssertionError(f"Dependency type filter missing dependency: {type_filter}")
    if any(item.get("dependency_type") != "capability" for item in type_filter.get("items") or []):
        raise AssertionError(f"Dependency type filter returned another dependency type: {type_filter}")

    platform_summary = get("/api/platform/feature-bundle-dependencies/summary", OWNER_HEADERS)
    assert_summary_shape(platform_summary)

    platform_detail = get(f"/api/platform/feature-bundle-dependencies/{dependency_id}", OWNER_HEADERS)
    assert_disabled_response(platform_detail)
    assert_dependency_shape(platform_detail.get("dependency") or {})

    agency_list = get(f"/api/agencies/{agency_id}/feature-bundle-dependencies?dependency_type=capability", OWNER_HEADERS)
    assert_disabled_response(agency_list)
    if agency_list.get("read_only") is not True:
        raise AssertionError(f"Agency dependency list should be read-only: {agency_list}")
    agency_item = next((item for item in agency_list.get("items") or [] if item.get("dependency_id") == dependency_id), None)
    if not agency_item:
        raise AssertionError(f"Agency dependency list missing created dependency: {agency_list}")
    assert_dependency_shape(agency_item, agency_view=True)

    agency_summary = get(f"/api/agencies/{agency_id}/feature-bundle-dependencies/summary", OWNER_HEADERS)
    assert_summary_shape(agency_summary, agency_id=agency_id)
    if agency_summary.get("read_only") is not True:
        raise AssertionError(f"Agency dependency summary should be read-only: {agency_summary}")

    agency_detail = get(f"/api/agencies/{agency_id}/feature-bundle-dependencies/{dependency_id}", OWNER_HEADERS)
    assert_disabled_response(agency_detail)
    if agency_detail.get("read_only") is not True:
        raise AssertionError(f"Agency dependency detail should be read-only: {agency_detail}")
    assert_dependency_shape(agency_detail.get("dependency") or {}, agency_view=True)

    deleted = request("DELETE", f"/api/platform/feature-bundle-dependencies/{dependency_id}", {}, OWNER_HEADERS)[1]
    assert_disabled_response(deleted)
    if deleted.get("deleted") is not True or (deleted.get("dependency") or {}).get("status") != "deleted":
        raise AssertionError(f"Dependency delete should be metadata-only soft delete: {deleted}")

    after_delete = get(f"/api/platform/feature-bundle-dependencies?bundle_id={bundle_id}", OWNER_HEADERS)
    if any(item.get("dependency_id") == dependency_id for item in after_delete.get("items") or []):
        raise AssertionError(f"Default dependency list should exclude deleted metadata: {after_delete}")
    include_deleted = get(f"/api/platform/feature-bundle-dependencies?bundle_id={bundle_id}&include_deleted=true", OWNER_HEADERS)
    if not any(item.get("dependency_id") == dependency_id for item in include_deleted.get("items") or []):
        raise AssertionError(f"include_deleted should expose metadata-deleted dependency: {include_deleted}")

    request("POST", f"/api/agencies/{agency_id}/feature-bundle-dependencies", {"bundle_id": bundle_id}, OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/feature-bundle-dependencies/{dependency_id}", {"status": "satisfied"}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/feature-bundle-dependencies/{dependency_id}", {}, OWNER_HEADERS, 405)


def assert_dependency_shape(dependency: dict, *, agency_view: bool = False) -> None:
    for key in [
        "dependency_id",
        "agency_id",
        "bundle_id",
        "dependency_type",
        "depends_on",
        "depends_on_label",
        "status",
        "notes",
        "bundle_name",
        "agency_name",
        "metadata_only",
        "dependency_metadata_only",
    ]:
        if key not in dependency:
            raise AssertionError(f"Dependency missing {key}: {dependency}")
    if dependency.get("dependency_type") not in DEPENDENCY_TYPES:
        raise AssertionError(f"Dependency type is invalid: {dependency}")
    if not isinstance(dependency.get("depends_on"), dict) or dependency["depends_on"].get("metadata_only") is not True:
        raise AssertionError(f"Dependency reference metadata missing: {dependency}")
    if agency_view and dependency.get("read_only") is not True:
        raise AssertionError(f"Agency dependency should be read-only: {dependency}")
    assert_disabled_response(dependency)


def assert_summary_shape(payload: dict, *, agency_id: str | None = None) -> None:
    if payload.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected summary phase: {payload}")
    if agency_id is not None and payload.get("agency_id") != agency_id:
        raise AssertionError(f"Agency dependency summary did not stay agency-scoped: {payload}")
    assert_disabled_response(payload)
    summary = payload.get("summary") or {}
    if "by_dependency_type" not in summary or "total_count" not in summary:
        raise AssertionError(f"Dependency summary malformed: {payload}")
    if not DEPENDENCY_TYPES.issubset(set((summary.get("by_dependency_type") or {}).keys())):
        raise AssertionError(f"Dependency summary missing dependency types: {payload}")


def main() -> int:
    verify_model_and_collection_registration()
    verify_readiness()
    openapi = get("/openapi.json")
    paths = openapi.get("paths") or {}
    verify_routes(paths)
    verify_frontend_and_docs()
    verify_endpoint_behavior()
    print("Phase 40.7 feature bundle dependency foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Phase 40.7 feature bundle dependency foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
