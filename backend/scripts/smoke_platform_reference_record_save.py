#!/usr/bin/env python3
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


BASE_URL = os.getenv("AEROASSIST_SMOKE_BASE_URL", "http://localhost:8000")
OWNER_TOKEN = os.getenv("AEROASSIST_SMOKE_OWNER_TOKEN")
OWNER_HEADERS = {"Authorization": f"Bearer {OWNER_TOKEN}"} if OWNER_TOKEN else {"X-Demo-User-Email": "owner@aeroassist.dev"}
AGENCY_HEADERS = {"X-Demo-User-Email": "agency.agent@aeroassist.dev"}
EXPECTED_PHASE = "phase_37_2_offer_policy_advisor_integration_foundation"
ROOT = Path(__file__).resolve().parents[2]


def smoke_city_code(seed: int) -> str:
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return "Q" + alphabet[(seed // 26) % 26] + alphabet[seed % 26]


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


def main() -> int:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")

    post("/api/reference/seed", {}, OWNER_HEADERS)
    now = int(time.time())
    code = smoke_city_code(now)
    encoded_code = urllib.parse.quote(code)

    created = post(
        "/api/platform/reference/records",
        {
            "domain": "cities",
            "code": code,
            "label": "Smoke Save City",
            "description": "Created by platform reference save smoke.",
            "aliases": ["Smokeopolis"],
            "sort_order": 991,
            "metadata_json": {"country_code": "BG", "data_quality_status": "draft"},
        },
        OWNER_HEADERS,
        201,
    )["record"]
    if created["domain"] != "cities" or created["code"] != code:
        raise AssertionError("Created city record did not preserve the requested domain/code.")

    updated = put(
        f"/api/platform/reference/records/{created['id']}",
        {
            "domain": "cities",
            "label": "Smoke Save City Updated",
            "description": "Updated by platform reference save smoke.",
            "aliases": ["Smokeopolis", "Save City"],
            "sort_order": 992,
            "metadata_json": {"country_code": "BG", "data_quality_status": "verified"},
            "is_active": True,
        },
        OWNER_HEADERS,
    )["record"]
    if updated["domain"] != "cities" or updated["label"] != "Smoke Save City Updated":
        raise AssertionError("Updated city record did not persist in its original domain.")
    if updated.get("metadata_json", {}).get("data_quality_status") != "verified":
        raise AssertionError("Updated city metadata was not persisted.")

    put(f"/api/platform/reference/records/{created['id']}", {"domain": "countries", "label": "Blocked Domain Swap"}, OWNER_HEADERS, 400)

    city_matches = get(f"/api/platform/reference/records?domain=cities&include_inactive=true&q={encoded_code}", OWNER_HEADERS)["items"]
    if len(city_matches) != 1 or city_matches[0]["id"] != created["id"]:
        raise AssertionError("Saved city record was not reloadable from the selected cities domain.")
    country_matches = get(f"/api/platform/reference/records?domain=countries&include_inactive=true&q={encoded_code}", OWNER_HEADERS)["items"]
    if country_matches:
        raise AssertionError("Saved city record leaked into the countries domain response.")

    post(
        "/api/platform/reference/records",
        {"domain": "cities", "code": f"AGENCY_BLOCKED_SAVE_{now}", "label": "Agency Blocked Save"},
        AGENCY_HEADERS,
        403,
    )
    put(f"/api/platform/reference/records/{created['id']}", {"label": "Agency Blocked Update"}, AGENCY_HEADERS, 403)

    post(f"/api/platform/reference/records/{created['id']}/archive", {}, OWNER_HEADERS)

    platform_page = (ROOT / "frontend/src/pages/platform/PlatformReferenceDataPage.jsx").read_text(encoding="utf-8")
    for needle in [
        "savingRecord",
        "recordsLoading",
        "recordError",
        "recordNotice",
        "recordLoadRequestRef",
        "setRecords([])",
        "record.domain !== selectedDomain",
        "type=\"submit\"",
        "Save global record",
        "Saving...",
        "Advanced metadata must be valid JSON.",
        "Global reference record saved.",
        "synchronizedMetadataJson",
        "recordPayload({ ...recordForm, domain: selectedDomain, metadata_json: synchronizedMetadataJson })",
        "selectedDomainRef",
        "selectedDomainRef.current !== domain",
    ]:
        if needle not in platform_page:
            raise AssertionError(f"PlatformReferenceDataPage missing record save/domain consistency marker: {needle}")

    models = (ROOT / "backend/models.py").read_text(encoding="utf-8")
    router = (ROOT / "backend/routers/platform_reference.py").read_text(encoding="utf-8")
    update_model = models.split("class PlatformReferenceRecordUpdate(BaseModel):", 1)[1].split("class ServiceCatalogueRecord", 1)[0]
    if "domain: Optional[str] = None" not in update_model:
        raise AssertionError("PlatformReferenceRecordUpdate must accept domain for selected-domain validation.")
    if "Reference record belongs to" not in router or "updates.pop(\"domain\")" not in router:
        raise AssertionError("Platform reference update endpoint must reject contradictory update domains.")

    print("Platform reference record save smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Platform reference record save smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
