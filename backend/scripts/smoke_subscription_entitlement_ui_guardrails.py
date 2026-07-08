#!/usr/bin/env python3
from pathlib import Path
from uuid import uuid4

from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post


EXPECTED_PHASE = "phase_41_7_ticket_workspace_foundation"
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


def verify_routes(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    for path, method in [
        ("/api/platform/saas-subscriptions/entitlement-visibility", "get"),
        ("/api/agencies/{agency_id}/saas-subscriptions/module-visibility", "get"),
        ("/api/platform/saas-subscriptions/summary", "get"),
        ("/api/agencies/{agency_id}/saas-subscriptions/summary", "get"),
    ]:
        assert_openapi_path(paths, path, method)


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
        (ROOT / "frontend/src/lib/moduleCatalog.js", "entitlementVisibilityLabels"),
        (ROOT / "frontend/src/layouts/AgencyLayout.jsx", "Subscription visibility is informational only"),
        (ROOT / "frontend/src/pages/agency/AgencyDashboardPage.jsx", "summarizeEntitlementVisibility"),
        (ROOT / "frontend/src/pages/platform/SaaSSubscriptionsPage.jsx", "Agency entitlement review visibility"),
        (ROOT / "docs/architecture/subscription-entitlement-ui-guardrails.md", "Subscription Entitlement UI Guardrails"),
        (ROOT / "README.md", "Phase 39.6 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 39.6: Subscription Entitlement UI Guardrails"),
        (ROOT / "docs/architecture/current-model-inventory.md", "Phase 39.6 adds no new persistent collections"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Subscription entitlement UI guardrails"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Subscription entitlement UI guardrails"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/layouts/AgencyLayout.jsx",
        ROOT / "frontend/src/pages/agency/AgencyDashboardPage.jsx",
        ROOT / "frontend/src/pages/platform/SaaSSubscriptionsPage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)


def main() -> int:
    run_key = uuid4().hex[:10]

    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")

    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("subscription_entitlement_ui_guardrails") or {}
    for flag in [
        "entitlement_visibility_enabled",
        "agency_navigation_badges_enabled",
        "platform_entitlement_review_enabled",
        "read_only_guardrail_ui_enabled",
    ]:
        require_flag(section, flag)
    for flag in [
        "automatic_enforcement_disabled",
        "billing_disabled",
        "payment_invoice_settlement_disabled",
        "provider_execution_disabled",
        "booking_execution_disabled",
        "pnr_mutation_disabled",
        "ticketing_disabled",
        "emd_issuance_disabled",
        "external_api_calls_disabled",
        "external_ai_disabled",
        "scraping_disabled",
        "automatic_sending_disabled",
    ]:
        require_flag(section, flag)
    require_flag(section, "readiness_required", False)
    for status in ["included", "limited", "not_included", "review_required", "unknown"]:
        if status not in (section.get("visibility_statuses") or []):
            raise AssertionError(f"Readiness visibility statuses missing {status}: {section}")

    openapi = get("/openapi.json")
    verify_routes(openapi.get("paths") or {})
    verify_route_policy()
    verify_frontend_and_docs()

    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires seeded demo agency.")
    agency_id = agencies[0]["id"]

    plan = post(
        "/api/platform/saas-subscriptions/plans",
        {
            "plan_name": f"Smoke Guardrail Plan {run_key}",
            "plan_code": f"guardrail_{run_key}",
            "tier": "professional",
            "status": "active",
            "description": "Metadata-only entitlement visibility smoke plan.",
            "included_modules": ["requests", "crm", "client_portal"],
            "visibility_flags": {"requests": True, "crm": True, "client_portal": True},
        },
        OWNER_HEADERS,
        201,
    )["plan"]
    for entitlement_key, included in [("requests", True), ("crm", True), ("client_portal", True), ("cms", False)]:
        post(
            "/api/platform/saas-subscriptions/entitlements",
            {
                "plan_id": plan["id"],
                "entitlement_scope": "module",
                "entitlement_key": entitlement_key,
                "label": entitlement_key.replace("_", " ").title(),
                "description": "Metadata-only entitlement visibility smoke.",
                "included": included,
            },
            OWNER_HEADERS,
            201,
        )
    assignment = post(
        "/api/platform/saas-subscriptions/assignments",
        {
            "agency_id": agency_id,
            "plan_id": plan["id"],
            "assignment_status": "active",
            "included_modules": ["requests", "crm", "client_portal"],
            "visibility_flags": {"requests": True, "crm": True, "client_portal": True},
        },
        OWNER_HEADERS,
        201,
    )["assignment"]
    for entitlement_key, status, manual_review_required in [
        ("requests", "ready", False),
        ("crm", "not_ready", False),
        ("client_portal", "needs_review", True),
    ]:
        post(
            "/api/platform/saas-subscriptions/readiness",
            {
                "agency_id": agency_id,
                "assignment_id": assignment["id"],
                "plan_id": plan["id"],
                "entitlement_scope": "module",
                "entitlement_key": entitlement_key,
                "status": status,
                "manual_review_required": manual_review_required,
                "plain_language_summary": "Smoke visibility metadata only.",
            },
            OWNER_HEADERS,
            201,
        )

    agency_visibility = get(f"/api/agencies/{agency_id}/saas-subscriptions/module-visibility", OWNER_HEADERS)
    if agency_visibility.get("phase") != EXPECTED_PHASE or agency_visibility.get("read_only") is not True:
        raise AssertionError(f"Agency visibility response is not read-only 39.6 metadata: {agency_visibility}")
    by_key = agency_visibility.get("visibility_by_key") or {}
    expected_statuses = {
        "requests": "included",
        "crm": "limited",
        "client_portal": "review_required",
        "cms": "not_included",
    }
    for key, expected in expected_statuses.items():
        actual = (by_key.get(key) or {}).get("status")
        if actual != expected:
            raise AssertionError(f"Expected {key} visibility {expected}, got {actual}: {by_key.get(key)}")
    for flag in ["automatic_enforcement_disabled", "billing_disabled", "payment_invoice_settlement_disabled", "provider_execution_disabled"]:
        require_flag(agency_visibility, flag)

    platform_visibility = get("/api/platform/saas-subscriptions/entitlement-visibility", OWNER_HEADERS)
    if platform_visibility.get("phase") != EXPECTED_PHASE or platform_visibility.get("owner_review_metadata_only") is not True:
        raise AssertionError(f"Platform visibility response is not owner-review metadata: {platform_visibility}")
    agency_item = next((item for item in platform_visibility.get("items") or [] if item.get("agency_id") == agency_id), None)
    if not agency_item:
        raise AssertionError("Platform visibility did not include smoke agency.")
    if agency_item.get("status_counts", {}).get("review_required", 0) < 1:
        raise AssertionError(f"Platform visibility did not surface review-required metadata: {agency_item}")

    final_readiness = get("/api/readiness")
    final_section = final_readiness.get("subscription_entitlement_ui_guardrails") or {}
    if final_section.get("assignment_count", 0) < section.get("assignment_count", 0) + 1:
        raise AssertionError(f"Guardrail readiness assignment count did not advance: {final_section}")

    print("Subscription entitlement UI guardrails smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
