#!/usr/bin/env python3
from pathlib import Path
import subprocess

from smoke_booking_pnr_foundation import get


EXPECTED_PHASE = "phase_40_0_feature_bundle_assignment_foundation"
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


def verify_route_policy() -> None:
    openapi = get("/openapi.json")
    for path in openapi.get("paths") or {}:
        if path.startswith("/agent") or path.startswith("/admin") or path.startswith("/api/agent") or path.startswith("/api/admin"):
            raise AssertionError(f"Non-canonical route introduced: {path}")

    route_policy = get("/api/platform/blueprint/route-policy")
    if route_policy.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected route policy phase: {route_policy.get('phase')}")
    canonical_roots = {item.get("root") for item in route_policy.get("canonical_routes") or []}
    rejected_roots = {item.get("root") for item in route_policy.get("rejected_routes") or []}
    for root in ["/platform/*", "/agency/*", "/api/platform/*", "/api/agencies/{agency_id}/*"]:
        if root not in canonical_roots:
            raise AssertionError(f"Canonical route root missing from route policy: {root}")
    for root in ["/agent/*", "/admin/*"]:
        if root not in rejected_roots:
            raise AssertionError(f"Rejected route root missing from route policy: {root}")
    if route_policy.get("aliases_added") is not False:
        raise AssertionError("Route aliases should remain disabled.")


def verify_frontend_source() -> None:
    catalog = ROOT / "frontend/src/lib/moduleCatalog.js"
    platform_layout = ROOT / "frontend/src/layouts/PlatformLayout.jsx"
    agency_layout = ROOT / "frontend/src/layouts/AgencyLayout.jsx"
    platform_dashboard = ROOT / "frontend/src/pages/platform/PlatformDashboardPage.jsx"
    agency_dashboard = ROOT / "frontend/src/pages/agency/AgencyDashboardPage.jsx"
    app = ROOT / "frontend/src/App.jsx"

    for text in [
        "SaaS & Agencies",
        "Airline Intelligence Governance",
        "Agency Website/CMS Governance",
        "CRM / Client Portal Governance",
        "Offer & Document Governance",
        "System Readiness",
        "Daily Work",
        "Clients & Passengers",
        "Requests, Offers & Trips",
        "Website/CMS",
        "Airline Intelligence Visibility",
        "Documents & Delivery",
        "Settings",
        "Platform only",
        "Agency read-only",
        "Metadata only",
        "No publishing yet",
    ]:
        require_text(catalog, text)

    for path, text in [
        (platform_layout, "Platform Console"),
        (platform_layout, "Platform Console modules"),
        (platform_layout, "platformModuleGroups"),
        (agency_layout, "Agency Workspace"),
        (agency_layout, "agencyModuleGroups"),
        (platform_dashboard, "Platform Console"),
        (platform_dashboard, "platformModuleGroups"),
        (agency_dashboard, "Agency Workspace"),
        (agency_dashboard, "agencyModuleGroups"),
    ]:
        require_text(path, text)

    for path in [catalog, platform_layout, agency_layout, platform_dashboard, agency_dashboard, app]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)


def verify_frontend_build() -> None:
    result = subprocess.run(
        ["npm", "run", "build", "--prefix", "frontend"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(f"Frontend build failed in smoke:\n{result.stdout}\n{result.stderr}")


def main() -> int:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")

    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("platform_agency_ux_consolidation") or {}
    for flag in [
        "platform_console_labels_enabled",
        "agency_workspace_labels_enabled",
        "owner_agency_separation_enabled",
        "plain_language_navigation_enabled",
        "canonical_routes_preserved",
        "admin_agent_routes_rejected",
        "metadata_only_ui_enabled",
        "operational_execution_disabled",
        "cms_publishing_disabled",
        "client_portal_publishing_disabled",
        "recommendation_disabled",
        "booking_execution_disabled",
        "pnr_mutation_disabled",
        "ticketing_disabled",
        "emd_issuance_disabled",
        "payment_invoice_settlement_disabled",
        "provider_execution_disabled",
        "scraping_disabled",
        "external_api_calls_disabled",
        "external_ai_disabled",
        "automatic_sending_disabled",
    ]:
        require_flag(section, flag)
    require_flag(section, "readiness_required", False)

    verify_route_policy()
    verify_frontend_source()
    verify_frontend_build()
    print("Phase 39.4 platform/agency UX consolidation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
