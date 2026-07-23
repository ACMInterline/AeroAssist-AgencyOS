#!/usr/bin/env python3
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


BASE_URL = os.getenv("AEROASSIST_SMOKE_BASE_URL", "http://localhost:8000")
OWNER_TOKEN = os.getenv("AEROASSIST_SMOKE_OWNER_TOKEN")
OWNER_HEADERS = {"Authorization": f"Bearer {OWNER_TOKEN}"} if OWNER_TOKEN else {"X-Demo-User-Email": "owner@aeroassist.dev"}
from phase_assertions import application_phase_is_at_least


MINIMUM_PHASE = "phase_35_0_trip_dossier_foundation"
ROOT = Path(__file__).resolve().parents[2]


def request(method: str, path: str, body: dict | None = None, headers: dict | None = None, expect: int | None = None) -> tuple[int, dict]:
    data = json.dumps(body or {}).encode("utf-8") if body is not None else None
    req = urllib.request.Request(f"{BASE_URL}{path}", method=method, data=data, headers={**(headers or {}), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            payload = response.read().decode("utf-8")
            status = response.status
            result = json.loads(payload) if payload else {}
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8")
        status = exc.code
        result = json.loads(payload) if payload else {}
    if expect is not None and status != expect:
        raise AssertionError(f"{method} {path} expected {expect}, got {status}: {result}")
    if expect is None and status >= 400:
        raise AssertionError(f"{method} {path} failed with {status}: {result}")
    return status, result


def get(path: str, headers: dict | None = None, expect: int | None = None) -> dict:
    return request("GET", path, None, headers, expect)[1]


def require_text(source: str, needles: list[str], label: str) -> None:
    for needle in needles:
        if needle not in source:
            raise AssertionError(f"{label} missing expected text: {needle}")


def reject_text(source: str, needles: list[str], label: str) -> None:
    for needle in needles:
        if needle in source:
            raise AssertionError(f"{label} contains forbidden text: {needle}")


def main() -> int:
    health = get("/api/health")
    if not application_phase_is_at_least(health.get("phase"), MINIMUM_PHASE):
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")

    app = (ROOT / "frontend/src/App.jsx").read_text(encoding="utf-8")
    layout = (ROOT / "frontend/src/layouts/PlatformLayout.jsx").read_text(encoding="utf-8")
    module_catalog = (ROOT / "frontend/src/lib/moduleCatalog.js").read_text(encoding="utf-8")
    platform_catalog = module_catalog.split("export const agencyModuleGroups", 1)[0]
    dashboard = (ROOT / "frontend/src/pages/platform/PlatformDashboardPage.jsx").read_text(encoding="utf-8")
    agencies = (ROOT / "frontend/src/pages/platform/PlatformAgenciesPage.jsx").read_text(encoding="utf-8")
    agency_detail = (ROOT / "frontend/src/pages/platform/PlatformAgencyDetailPage.jsx").read_text(encoding="utf-8")
    airlines = (ROOT / "frontend/src/pages/platform/AirlinesPage.jsx").read_text(encoding="utf-8")
    agency_reference = (ROOT / "frontend/src/pages/agency/ReferenceDataPage.jsx").read_text(encoding="utf-8")

    require_text(app, [
        '"/platform/agencies": PlatformAgenciesPage',
        '"/platform/airlines": AirlinesPage',
        '"/platform/airline-policy-ingestion": AirlinePolicyIngestionPage',
        '"/platform/service-taxonomy": PlatformServiceTaxonomyPage',
        '"/platform/service-mechanics": PlatformServiceMechanicsPage',
        'import PlatformAgenciesPage from "./pages/platform/PlatformAgenciesPage"',
        'import AirlinesPage from "./pages/platform/AirlinesPage"',
        'import AirlinePolicyIngestionPage from "./pages/platform/AirlinePolicyIngestionPage"',
        'import PlatformServiceTaxonomyPage from "./pages/platform/ServiceTaxonomyPage"',
        'import PlatformServiceMechanicsPage from "./pages/platform/ServiceMechanicsPage"',
        "PlatformAgencyDetailPage",
        "AirlineDetailPage",
        "AirlineKnowledgeDetailPage",
    ], "App platform routes")
    require_text(layout, ["Platform Console", "platformModuleGroups", "platformProductNavigation", "productNavigationForRole", "PlatformArea", "PlatformNavItem"], "Platform navigation")
    require_text(platform_catalog, ["Platform Console", "Agencies", "Reference Data", "Airlines / Knowledge", "Policy Ingestion", "Service Taxonomy", "Service Mechanics", 'href: "/platform/agencies"', 'href: "/platform/airlines"', 'href: "/platform/airline-policy-ingestion"', 'href: "/platform/service-taxonomy"', 'href: "/platform/service-mechanics"'], "Platform module catalog")
    reject_text(layout, ["Agency Workspace", 'href="/agency"'], "Platform header")
    reject_text(platform_catalog, ["Agency Workspace", 'href: "/agency"'], "Platform module catalog")
    require_text(dashboard, ['href="/platform/agencies"', "Attention required", "Knowledge readiness", "Pilot status", "System health", "Recent activity", "Quick actions"], "Platform dashboard")
    require_text(agencies, ["Agencies", "Create Agency", "Promise.allSettled", "agencies = state?.agencies || []"], "Platform agencies defensive route")
    require_text(agency_detail, ["Enter workspace", "`/agency?agency_id=${agencyId}`"], "Contextual agency workspace entry")
    require_text(airlines, ["Airline Knowledge", "Promise.allSettled", "airlines = state?.airlines || []", "Platform owners will manage airline policy"], "Platform airlines defensive route")
    reject_text(agency_reference, ["Create global record", "Deactivate", "Upload import batch", "Import / Bulk Upload"], "Agency reference governance")

    summary = get("/api/platform/summary", OWNER_HEADERS)
    counts = summary.get("counts") or {}
    for key in ["agencies", "workspaces", "airlines", "airline_knowledge"]:
        if key not in counts:
            raise AssertionError(f"Platform summary missing count: {key}")
    overview = summary.get("product_overview") or {}
    for key in ["agency_count", "onboarding_attention_count", "legacy_agency_count", "open_operational_request_count", "recent_activity"]:
        if key not in overview:
            raise AssertionError(f"Platform summary missing product overview field: {key}")
    get("/api/agencies", OWNER_HEADERS)
    get("/api/platform/airlines", OWNER_HEADERS)

    print("Platform navigation routes smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Platform navigation routes smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
