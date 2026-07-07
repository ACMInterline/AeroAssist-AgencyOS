#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import AgencyFeatureBundleAssignment, AgencyFeatureBundleAssignmentCreate, AgencyFeatureBundleAssignmentHistory
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_41_2_passenger_workspace_foundation"
ROOT = Path(__file__).resolve().parents[2]


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


def verify_model_and_collection_registration() -> None:
    create_payload = AgencyFeatureBundleAssignmentCreate(
        agency_id="agency-smoke",
        bundle_id="bundle_core_agency",
        effective_date="2026-07-04",
        expiration_date="2026-12-31",
        notes="Metadata-only smoke assignment.",
    )
    assignment = AgencyFeatureBundleAssignment(
        agency_id="agency-smoke",
        bundle_id=create_payload.bundle_id,
        notes=create_payload.notes,
    )
    history = AgencyFeatureBundleAssignmentHistory(
        assignment_id=assignment.assignment_id,
        agency_id=assignment.agency_id,
        bundle_id=assignment.bundle_id,
        status=assignment.status,
        review_status=assignment.review_status,
    )
    for model in [assignment, history]:
        dumped = model.model_dump(mode="json")
        if dumped.get("metadata_only") is not True:
            raise AssertionError(f"Feature bundle assignment model is not metadata-only: {dumped}")
        if dumped.get("activation_logic_disabled") is not True:
            raise AssertionError(f"Feature bundle assignment model does not disable activation logic: {dumped}")
    if create_payload.bundle_id != "bundle_core_agency":
        raise AssertionError("Create model failed to preserve bundle_id.")
    for collection in ["agency_feature_bundle_assignments", "agency_feature_bundle_assignment_history"]:
        if collection not in AGENCY_OWNED_COLLECTIONS:
            raise AssertionError(f"Feature bundle assignment collection not registered: {collection}")
    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "agency_feature_bundle_assignments_assignment_unique",
        "agency_feature_bundle_assignments_agency_status_lookup",
        "agency_feature_bundle_assignments_agency_bundle_lookup",
        "agency_feature_bundle_assignment_history_assignment_changed_lookup",
        "agency_feature_bundle_assignment_history_agency_changed_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Feature bundle assignment index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    expected_methods = {
        "/api/platform/feature-bundle-assignments": {"get"},
        "/api/platform/agencies/{agency_id}/bundle-assignments": {"get", "post"},
        "/api/platform/bundle-assignments/{assignment_id}": {"put", "delete"},
        "/api/agencies/{agency_id}/feature-bundle-assignments": {"get"},
        "/api/agencies/{agency_id}/feature-bundle-assignment-history": {"get"},
    }
    for path, methods in expected_methods.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
        exposed = set(paths.get(path, {}).keys())
        unexpected = exposed - methods
        if unexpected:
            raise AssertionError(f"Feature bundle assignment route exposes unexpected methods: {path} {sorted(unexpected)}")


def verify_route_policy() -> None:
    route_policy = get("/api/platform/blueprint/route-policy", OWNER_HEADERS)
    if route_policy.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected route policy phase: {route_policy.get('phase')}")
    canonical_roots = {item.get("root") for item in route_policy.get("canonical_routes") or []}
    rejected_roots = {item.get("root") for item in route_policy.get("rejected_routes") or []}
    for root in ["/platform/*", "/agency/*", "/api/platform/*", "/api/agencies/{agency_id}/*"]:
        if root not in canonical_roots:
            raise AssertionError(f"Canonical route root missing: {root}")
    for root in ["/agent/*", "/admin/*"]:
        if root not in rejected_roots:
            raise AssertionError(f"Rejected route root missing: {root}")
    if route_policy.get("aliases_added") is not False:
        raise AssertionError("Route policy should not add admin/agent aliases.")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Feature Bundle Assignments"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Assigned Bundles"),
        (ROOT / "frontend/src/App.jsx", "/platform/feature-bundle-assignments"),
        (ROOT / "frontend/src/App.jsx", "/agency/assigned-bundles"),
        (ROOT / "frontend/src/pages/platform/FeatureBundleAssignmentsPage.jsx", "Feature Bundle Assignments"),
        (ROOT / "frontend/src/pages/platform/FeatureBundleAssignmentsPage.jsx", "History drawer"),
        (ROOT / "frontend/src/pages/agency/AssignedBundlesPage.jsx", "Assigned Bundles"),
        (ROOT / "docs/architecture/feature-bundle-assignment-foundation.md", "Feature Bundle Assignment Foundation"),
        (ROOT / "README.md", "Phase 40.0 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 40.0: Agency Feature Bundle Assignment Foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "Phase 40.0 adds agency feature bundle assignment metadata"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "Phase 40.0 adds feature bundle assignment APIs"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Feature bundle assignments"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Feature bundle assignments"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/FeatureBundleAssignmentsPage.jsx",
        ROOT / "frontend/src/pages/agency/AssignedBundlesPage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)


def verify_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")
    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("feature_bundle_assignment_foundation") or {}
    for flag in [
        "feature_bundle_assignments_enabled",
        "feature_bundle_assignment_history_enabled",
        "platform_assignment_metadata_crud_enabled",
        "agency_read_only_assignment_visibility_enabled",
        "delete_marks_inactive_enabled",
        "history_preserved_enabled",
        "metadata_only",
        "no_activation_logic_enabled",
    ]:
        require_flag(section, flag)
    for flag in [
        "feature_activation_disabled",
        "runtime_execution_disabled",
        "feature_flag_execution_disabled",
        "entitlement_enforcement_disabled",
        "entitlement_evaluation_disabled",
        "billing_disabled",
        "payments_disabled",
        "stripe_disabled",
        "licensing_disabled",
        "permission_changes_disabled",
        "provider_calls_disabled",
        "external_ai_disabled",
        "background_workers_disabled",
        "cron_disabled",
    ]:
        require_flag(section, flag)
    require_flag(section, "readiness_required", False)


def verify_endpoint_behavior() -> None:
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires seeded demo agency.")
    agency_id = agencies[0]["id"]
    bundles = get("/api/platform/feature-flag-bundles", OWNER_HEADERS).get("items") or []
    if not bundles:
        raise AssertionError("Smoke requires feature flag bundle metadata.")
    bundle_id = next((item["bundle_id"] for item in bundles if item.get("bundle_key") == "core_agency"), bundles[0]["bundle_id"])

    created = post(
        f"/api/platform/agencies/{agency_id}/bundle-assignments",
        {
            "bundle_id": bundle_id,
            "effective_date": "2026-07-04",
            "expiration_date": "2026-12-31",
            "status": "assigned",
            "review_status": "pending_review",
            "notes": "Metadata-only feature bundle assignment smoke.",
        },
        OWNER_HEADERS,
        201,
    )
    if created.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected create phase: {created.get('phase')}")
    for flag in ["metadata_only", "no_activation_logic_enabled", "feature_activation_disabled", "entitlement_evaluation_disabled", "billing_disabled", "provider_calls_disabled", "background_workers_disabled"]:
        require_flag(created, flag)
    assignment = created.get("assignment") or {}
    assignment_id = assignment.get("assignment_id")
    if not assignment_id or assignment.get("agency_id") != agency_id or assignment.get("bundle_id") != bundle_id:
        raise AssertionError(f"Created assignment metadata is malformed: {created}")

    platform_all = get("/api/platform/feature-bundle-assignments", OWNER_HEADERS)
    if not any(item.get("assignment_id") == assignment_id for item in platform_all.get("items") or []):
        raise AssertionError(f"Platform assignment list missing created assignment: {platform_all}")
    if platform_all.get("history_count", 0) < 1:
        raise AssertionError(f"Platform assignment list should include history metadata: {platform_all}")
    platform_agency = get(f"/api/platform/agencies/{agency_id}/bundle-assignments", OWNER_HEADERS)
    if not any(item.get("assignment_id") == assignment_id for item in platform_agency.get("items") or []):
        raise AssertionError(f"Platform agency assignment list missing created assignment: {platform_agency}")

    updated = put(
        f"/api/platform/bundle-assignments/{assignment_id}",
        {
            "status": "review",
            "review_status": "reviewed",
            "notes": "Reviewed assignment metadata; no activation performed.",
        },
        OWNER_HEADERS,
    )
    if updated.get("assignment", {}).get("review_status") != "reviewed":
        raise AssertionError(f"Assignment update did not persist review metadata: {updated}")

    agency_assignments = get(f"/api/agencies/{agency_id}/feature-bundle-assignments", OWNER_HEADERS)
    if agency_assignments.get("read_only") is not True or agency_assignments.get("metadata_only") is not True:
        raise AssertionError(f"Agency assignment response should be read-only metadata: {agency_assignments}")
    agency_assignment = next((item for item in agency_assignments.get("items") or [] if item.get("assignment_id") == assignment_id), None)
    if not agency_assignment:
        raise AssertionError(f"Agency read-only assignments missing created assignment: {agency_assignments}")
    if agency_assignment.get("payloads_hidden") is not True:
        raise AssertionError(f"Agency assignment should hide payloads: {agency_assignment}")

    deleted = request("DELETE", f"/api/platform/bundle-assignments/{assignment_id}", {}, OWNER_HEADERS, 200)[1]
    if deleted.get("deleted") is not False or deleted.get("inactive") is not True:
        raise AssertionError(f"DELETE should mark assignment inactive without deletion: {deleted}")
    if deleted.get("assignment", {}).get("status") != "inactive":
        raise AssertionError(f"Assignment was not marked inactive: {deleted}")

    agency_history = get(f"/api/agencies/{agency_id}/feature-bundle-assignment-history", OWNER_HEADERS)
    events = [item.get("history_event") for item in agency_history.get("items") or [] if item.get("assignment_id") == assignment_id]
    for event in ["created", "updated", "inactivated"]:
        if event not in events:
            raise AssertionError(f"Assignment history missing {event}: {agency_history}")
    if agency_history.get("read_only") is not True or agency_history.get("metadata_only") is not True:
        raise AssertionError(f"Agency history response should be read-only metadata: {agency_history}")

    request("POST", "/api/platform/feature-bundle-assignments", {"bundle_id": bundle_id}, OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/feature-bundle-assignments", {"status": "assigned"}, OWNER_HEADERS, 405)
    request("POST", f"/api/agencies/{agency_id}/feature-bundle-assignments", {"bundle_id": bundle_id}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/feature-bundle-assignments", {}, OWNER_HEADERS, 405)


def main() -> int:
    verify_model_and_collection_registration()
    verify_readiness()
    openapi = get("/openapi.json")
    verify_routes(openapi.get("paths") or {})
    verify_route_policy()
    verify_frontend_and_docs()
    verify_endpoint_behavior()
    print("Phase 40.0 feature bundle assignment foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Phase 40.0 feature bundle assignment foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
