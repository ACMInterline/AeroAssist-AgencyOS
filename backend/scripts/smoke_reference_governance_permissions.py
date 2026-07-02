#!/usr/bin/env python3
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


BASE_URL = os.getenv("AEROASSIST_SMOKE_BASE_URL", "http://localhost:8000")
OWNER_TOKEN = os.getenv("AEROASSIST_SMOKE_OWNER_TOKEN")
OWNER_HEADERS = {"Authorization": f"Bearer {OWNER_TOKEN}"} if OWNER_TOKEN else {"X-Demo-User-Email": "owner@aeroassist.dev"}
AGENCY_ADMIN_HEADERS = {"X-Demo-User-Email": "agency.owner@aeroassist.dev"}
AGENCY_AGENT_HEADERS = {"X-Demo-User-Email": "agency.agent@aeroassist.dev"}
PORTAL_HEADERS = {"X-Demo-User-Email": "anna.client@example.com"}
EXPECTED_PHASE = "phase_37_6_offer_decision_export_preview_foundation"
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


def post(path: str, body: dict | None = None, headers: dict | None = None, expect: int | None = None) -> dict:
    return request("POST", path, body or {}, headers, expect)[1]


def put(path: str, body: dict | None = None, headers: dict | None = None, expect: int | None = None) -> dict:
    return request("PUT", path, body or {}, headers, expect)[1]


def patch(path: str, body: dict | None = None, headers: dict | None = None, expect: int | None = None) -> dict:
    return request("PATCH", path, body or {}, headers, expect)[1]


def assert_absent(text: str, needles: list[str], label: str) -> None:
    for needle in needles:
        if needle in text:
            raise AssertionError(f"{label} still contains forbidden agency management text: {needle}")


def main() -> int:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")

    post("/api/reference/seed", {}, OWNER_HEADERS)
    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    now = int(time.time())

    code = f"gov_perm_{now}"
    record = post(
        "/api/platform/reference/records",
        {"domain": "contact_channels", "code": code, "label": "Governance Permission Smoke"},
        OWNER_HEADERS,
        201,
    )["record"]
    updated = put(f"/api/platform/reference/records/{record['id']}", {"label": "Governance Permission Smoke Updated"}, OWNER_HEADERS)["record"]
    if updated["label"] != "Governance Permission Smoke Updated":
        raise AssertionError("Platform owner could not update a global reference record.")
    archived = post(f"/api/platform/reference/records/{record['id']}/archive", {}, OWNER_HEADERS)["record"]
    if archived.get("is_active") is not False:
        raise AssertionError("Platform owner could not archive a global reference record.")

    get("/api/platform/reference/import-batches", OWNER_HEADERS)
    get("/api/platform/reference/enrichment/templates", OWNER_HEADERS)
    post("/api/platform/reference/enrichment/dry-run", {"domain": "countries", "csv_text": "code,label\nZZ,Smoke"}, OWNER_HEADERS)

    for headers in [AGENCY_ADMIN_HEADERS, AGENCY_AGENT_HEADERS]:
        post("/api/reference/contact_channels", {"code": f"blocked_{now}", "label": "Blocked", "scope": "global"}, headers, 403)
        put(f"/api/reference/contact_channels/{record['id']}", {"label": "Blocked", "scope": "global"}, headers, 403)
        patch(f"/api/reference/contact_channels/{record['id']}/deactivate", {}, headers, 403)
        post("/api/reference/import-batches", {"scope": "global", "domain": "contact_channels", "filename": "blocked.csv", "csv_text": "domain,code,label\ncontact_channels,BLOCKED,Blocked"}, headers, 403)
        get("/api/platform/reference/enrichment/templates", headers, 403)
        post("/api/platform/reference/enrichment/import", {"domain": "countries", "csv_text": "code,label\nZZ,Blocked"}, headers, 403)
        get("/api/reference/contact_channels", headers)
        get("/api/reference/contact_channels?include_inactive=true", headers, 403)

    suggestion = post(
        "/api/reference/suggestions",
        {
            "submitting_agency_id": agency_id,
            "domain": "contact_channels",
            "suggested_code": f"agency_suggestion_{now}",
            "suggested_label": "Agency Governance Suggestion",
            "suggestion_type": "new_record",
            "source_context": "manual_reference_page",
            "evidence_note": "Smoke test agency suggestion.",
        },
        AGENCY_AGENT_HEADERS,
        201,
    )["suggestion"]
    reviewed = post(f"/api/platform/reference/suggestions/{suggestion['id']}/request-info", {"reviewer_note": "Need source."}, OWNER_HEADERS)["suggestion"]
    if reviewed["status"] != "needs_more_information":
        raise AssertionError("Platform owner could not review agency suggestion.")
    post(f"/api/platform/reference/suggestions/{suggestion['id']}/reject", {"reviewer_note": "Rejected by smoke."}, AGENCY_AGENT_HEADERS, 403)

    post("/api/reference/contact_channels", {"code": f"portal_blocked_{now}", "label": "Portal Blocked", "scope": "global"}, PORTAL_HEADERS, 403)
    post("/api/platform/reference/records", {"domain": "contact_channels", "code": f"portal_platform_blocked_{now}", "label": "Portal Blocked"}, PORTAL_HEADERS, 403)

    agency_page = (ROOT / "frontend/src/pages/agency/ReferenceDataPage.jsx").read_text(encoding="utf-8")
    platform_page = (ROOT / "frontend/src/pages/platform/PlatformReferenceDataPage.jsx").read_text(encoding="utf-8")
    assert_absent(
        agency_page,
        [
            "Create global record",
            "Update global record",
            "Deactivate",
            "Upload import batch",
            "Import / Bulk Upload",
            "Global reference record updated",
            "Global reference record created",
            "activateReferenceRecord",
            "createReferenceRecord",
            "updateReferenceRecord",
        ],
        "/agency/reference",
    )
    for needle in ["Global Reference Data", "Service Catalogue", "Suggestions", "Suggest correction", "Suggest new record"]:
        if needle not in agency_page:
            raise AssertionError(f"/agency/reference missing expected consume/suggest UI text: {needle}")
    for needle in ["Create Record", "Archive", "Bulk Import", "Enrichment Packs", "Agency Suggestion Review Queue"]:
        if needle not in platform_page:
            raise AssertionError(f"/platform/reference missing expected management UI text: {needle}")

    readiness = get("/api/readiness")
    reference_data = readiness.get("reference_data") or {}
    platform_console = readiness.get("platform_reference_console") or {}
    for flag in ["reference_governance_permissions_enforced", "agency_reference_mutation_blocked", "agency_reference_consume_suggest_only"]:
        if reference_data.get(flag) is not True:
            raise AssertionError(f"Readiness missing reference governance flag: {flag}")
    if platform_console.get("platform_reference_management_enabled") is not True:
        raise AssertionError("Readiness missing platform reference management flag.")

    print("Reference governance permissions smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Reference governance permissions smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
