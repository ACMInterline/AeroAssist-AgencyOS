#!/usr/bin/env python3
from pathlib import Path
from uuid import uuid4

import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import (
    AgencyEntitlementReadiness,
    AgencySubscriptionAssignment,
    AgencySubscriptionReviewNote,
    AgencySubscriptionSnapshot,
    SaaSPlanEntitlement,
    SaaSSubscriptionPlan,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, request


EXPECTED_PHASE = "phase_50_0_airline_operational_intelligence_engine_architecture_foundation"
ROOT = Path(__file__).resolve().parents[2]


def require_flag(section: dict, key: str, expected: object = True) -> None:
    if section.get(key) is not expected:
        raise AssertionError(f"Readiness flag {key} expected {expected!r}, got {section.get(key)!r}")


def require_count(section: dict, key: str) -> None:
    if not isinstance(section.get(key), int):
        raise AssertionError(f"Readiness count {key} missing or not an int: {section.get(key)!r}")


def patch(path: str, body: dict | None = None, headers: dict | None = None, expect: int | None = None) -> dict:
    return request("PATCH", path, body or {}, headers, expect)[1]


def require_text(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8")
    if text not in content:
        raise AssertionError(f"{path.relative_to(ROOT)} missing expected text: {text}")


def reject_text(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8")
    if text in content:
        raise AssertionError(f"{path.relative_to(ROOT)} contains rejected text: {text}")


def verify_model_and_collection_registration() -> None:
    for model in [
        SaaSSubscriptionPlan,
        SaaSPlanEntitlement,
        AgencySubscriptionAssignment,
        AgencyEntitlementReadiness,
        AgencySubscriptionReviewNote,
        AgencySubscriptionSnapshot,
    ]:
        if not hasattr(model, "model_fields"):
            raise AssertionError(f"Model import failed for {model}")
    for collection in [
        "saas_subscription_plans",
        "saas_plan_entitlements",
        "agency_subscription_assignments",
        "agency_entitlement_readiness",
        "agency_subscription_review_notes",
        "agency_subscription_snapshots",
    ]:
        if collection not in AGENCY_OWNED_COLLECTIONS:
            raise AssertionError(f"Collection not registered for Mongo index setup: {collection}")


def verify_routes(paths: dict) -> None:
    for path in paths:
        if path.startswith("/agent") or path.startswith("/admin") or path.startswith("/api/agent") or path.startswith("/api/admin"):
            raise AssertionError(f"Non-canonical route introduced: {path}")
        if "saas-subscriptions" in path and any(
            token in path
            for token in [
                "billing",
                "payment",
                "invoice",
                "settle",
                "stripe",
                "card",
                "bank",
                "tax",
                "charge",
                "enforce-access",
                "disable-access",
                "publish",
                "recommend",
                "execute",
                "book",
                "pnr",
                "ticket",
                "emd",
                "scrape",
                "send",
            ]
        ):
            raise AssertionError(f"Execution or billing route introduced: {path}")

    for path, method in [
        ("/api/platform/saas-subscriptions/summary", "get"),
        ("/api/platform/saas-subscriptions/plans", "get"),
        ("/api/platform/saas-subscriptions/plans", "post"),
        ("/api/platform/saas-subscriptions/plans/{plan_id}", "patch"),
        ("/api/platform/saas-subscriptions/entitlements", "get"),
        ("/api/platform/saas-subscriptions/entitlements", "post"),
        ("/api/platform/saas-subscriptions/assignments", "get"),
        ("/api/platform/saas-subscriptions/assignments", "post"),
        ("/api/platform/saas-subscriptions/assignments/{assignment_id}", "patch"),
        ("/api/platform/saas-subscriptions/readiness", "get"),
        ("/api/platform/saas-subscriptions/readiness", "post"),
        ("/api/platform/saas-subscriptions/notes", "get"),
        ("/api/platform/saas-subscriptions/notes", "post"),
        ("/api/platform/saas-subscriptions/snapshots", "get"),
        ("/api/platform/saas-subscriptions/snapshots", "post"),
        ("/api/agencies/{agency_id}/saas-subscriptions/summary", "get"),
        ("/api/agencies/{agency_id}/saas-subscriptions/assignments", "get"),
        ("/api/agencies/{agency_id}/saas-subscriptions/readiness", "get"),
        ("/api/agencies/{agency_id}/saas-subscriptions/notes", "get"),
        ("/api/agencies/{agency_id}/saas-subscriptions/snapshots", "get"),
    ]:
        assert_openapi_path(paths, path, method)


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Subscriptions & Entitlements"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "My Subscription"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "/platform/saas-subscriptions"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "/agency/saas-subscription"),
        (ROOT / "frontend/src/pages/platform/SaaSSubscriptionsPage.jsx", "No billing"),
        (ROOT / "frontend/src/pages/agency/SaaSSubscriptionPage.jsx", "Agency read-only"),
        (ROOT / "frontend/src/App.jsx", "/platform/saas-subscriptions"),
        (ROOT / "frontend/src/App.jsx", "/agency/saas-subscription"),
        (ROOT / "docs/architecture/saas-subscription-entitlement-foundation.md", "SaaS Subscription"),
        (ROOT / "README.md", "Phase 39.5 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 39.5: SaaS Subscription"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/SaaSSubscriptionsPage.jsx",
        ROOT / "frontend/src/pages/agency/SaaSSubscriptionPage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)


def main() -> int:
    verify_model_and_collection_registration()
    run_key = uuid4().hex[:10]

    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")

    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("saas_subscription_entitlement_foundation") or {}
    for flag in [
        "plans_enabled",
        "plan_entitlements_enabled",
        "agency_subscription_assignments_enabled",
        "entitlement_readiness_enabled",
        "subscription_review_notes_enabled",
        "immutable_subscription_snapshots_enabled",
        "platform_subscription_ui_enabled",
        "agency_subscription_visibility_ui_enabled",
        "metadata_only_subscription_enabled",
        "billing_disabled",
        "payment_disabled",
        "invoice_disabled",
        "settlement_disabled",
        "automatic_access_enforcement_disabled",
        "cms_publishing_disabled",
        "client_portal_publishing_disabled",
        "recommendation_disabled",
        "provider_execution_disabled",
        "booking_execution_disabled",
        "pnr_mutation_disabled",
        "ticketing_disabled",
        "emd_issuance_disabled",
        "scraping_disabled",
        "external_api_calls_disabled",
        "external_ai_disabled",
        "automatic_sending_disabled",
    ]:
        require_flag(section, flag)
    require_flag(section, "readiness_required", False)
    for count_key in ["plan_count", "entitlement_count", "assignment_count", "readiness_count", "note_count", "snapshot_count"]:
        require_count(section, count_key)

    openapi = get("/openapi.json")
    verify_routes(openapi.get("paths") or {})
    verify_frontend_and_docs()

    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires seeded demo agency.")
    agency_id = agencies[0]["id"]
    plan = post(
        "/api/platform/saas-subscriptions/plans",
        {
            "plan_name": f"Smoke Entitlement Plan {run_key}",
            "plan_code": f"smoke_{run_key}",
            "tier": "growth",
            "status": "active",
            "description": "Metadata-only smoke plan. No billing, charging, invoices, settlement, or automatic access enforcement.",
            "included_modules": ["crm", "offers"],
            "included_airline_intelligence_domains": ["policies", "service_mechanics"],
            "included_data_pack_channels": ["reviewed"],
            "visibility_flags": {"crm": True, "offer_builder": True, "airline_intelligence": True},
        },
        OWNER_HEADERS,
        201,
    )["plan"]
    entitlement = post(
        "/api/platform/saas-subscriptions/entitlements",
        {
            "plan_id": plan["id"],
            "entitlement_scope": "module",
            "entitlement_key": f"offer_builder_{run_key}",
            "label": "Offer builder",
            "description": "Metadata-only module entitlement.",
            "visibility_flags": {"offer_builder": True},
        },
        OWNER_HEADERS,
        201,
    )["entitlement"]
    assignment = post(
        "/api/platform/saas-subscriptions/assignments",
        {
            "agency_id": agency_id,
            "plan_id": plan["id"],
            "assignment_status": "review",
            "manual_review_required": True,
            "visibility_flags": {"crm": True, "offer_builder": True},
        },
        OWNER_HEADERS,
        201,
    )["assignment"]
    updated_assignment = patch(
        f"/api/platform/saas-subscriptions/assignments/{assignment['id']}",
        {"assignment_status": "active", "manual_review_required": False},
        OWNER_HEADERS,
    )["assignment"]
    if updated_assignment.get("assignment_status") != "active":
        raise AssertionError(f"Assignment update failed: {updated_assignment}")
    readiness_record = post(
        "/api/platform/saas-subscriptions/readiness",
        {
            "agency_id": agency_id,
            "assignment_id": assignment["id"],
            "plan_id": plan["id"],
            "entitlement_scope": "module",
            "entitlement_key": entitlement["entitlement_key"],
            "status": "ready",
            "crm_ready": True,
            "offer_builder_ready": True,
            "airline_intelligence_ready": True,
            "plain_language_summary": "Smoke entitlement is ready for metadata-only visibility.",
        },
        OWNER_HEADERS,
        201,
    )["readiness"]
    note = post(
        "/api/platform/saas-subscriptions/notes",
        {
            "agency_id": agency_id,
            "assignment_id": assignment["id"],
            "plan_id": plan["id"],
            "note_type": "agency_visible",
            "note": "Smoke note visible to agency. Billing and access enforcement remain disabled.",
            "visible_to_agency": True,
        },
        OWNER_HEADERS,
        201,
    )["note"]
    snapshot = post(
        "/api/platform/saas-subscriptions/snapshots",
        {
            "agency_id": agency_id,
            "assignment_id": assignment["id"],
            "plan_id": plan["id"],
            "snapshot_type": "manual",
            "snapshot_json": {"plain_language_summary": "Smoke immutable subscription snapshot."},
        },
        OWNER_HEADERS,
        201,
    )["snapshot"]

    platform_summary = get("/api/platform/saas-subscriptions/summary", OWNER_HEADERS)
    if platform_summary.get("plan_count", 0) < 1 or platform_summary.get("assignment_count", 0) < 1:
        raise AssertionError(f"Platform summary missing created records: {platform_summary}")
    agency_summary = get(f"/api/agencies/{agency_id}/saas-subscriptions/summary", OWNER_HEADERS)
    if agency_summary.get("read_only") is not True or agency_summary.get("billing_disabled") is not True:
        raise AssertionError(f"Agency summary is not read-only/safe: {agency_summary}")
    agency_assignments = get(f"/api/agencies/{agency_id}/saas-subscriptions/assignments", OWNER_HEADERS)["items"]
    agency_readiness = get(f"/api/agencies/{agency_id}/saas-subscriptions/readiness", OWNER_HEADERS)["items"]
    agency_notes = get(f"/api/agencies/{agency_id}/saas-subscriptions/notes", OWNER_HEADERS)["items"]
    agency_snapshots = get(f"/api/agencies/{agency_id}/saas-subscriptions/snapshots", OWNER_HEADERS)["items"]
    if assignment["id"] not in {item["id"] for item in agency_assignments}:
        raise AssertionError("Agency read-only assignment view missing created assignment.")
    if readiness_record["id"] not in {item["id"] for item in agency_readiness}:
        raise AssertionError("Agency read-only readiness view missing created readiness.")
    if note["id"] not in {item["id"] for item in agency_notes}:
        raise AssertionError("Agency read-only notes view missing visible note.")
    if snapshot["id"] not in {item["id"] for item in agency_snapshots}:
        raise AssertionError("Agency read-only snapshots view missing created snapshot.")

    for method, path in [
        ("POST", f"/api/agencies/{agency_id}/saas-subscriptions/assignments"),
        ("PATCH", f"/api/agencies/{agency_id}/saas-subscriptions/readiness"),
        ("POST", f"/api/agencies/{agency_id}/saas-subscriptions/notes"),
    ]:
        request(method, path, {}, OWNER_HEADERS, expect=405)

    final_readiness = get("/api/readiness")
    final_section = final_readiness.get("saas_subscription_entitlement_foundation") or {}
    if final_section.get("plan_count", 0) < section.get("plan_count", 0) + 1:
        raise AssertionError(f"Readiness plan count did not advance: {final_section}")
    print("SaaS subscription entitlement foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
