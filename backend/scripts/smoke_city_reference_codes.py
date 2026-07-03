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
AGENCY_HEADERS = {"X-Demo-User-Email": "agency.agent@aeroassist.dev"}
EXPECTED_PHASE = "phase_37_8_offer_decision_export_manual_delivery_handoff_foundation"
ROOT = Path(__file__).resolve().parents[2]
EXPECTED_CITY_CODES = {"SOF": "SOFIA", "NYC": "NEW_YORK", "LON": "LONDON"}
LEGACY_CITY_CODES = set(EXPECTED_CITY_CODES.values())


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


def main() -> int:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")

    first_seed = post("/api/reference/seed", {}, OWNER_HEADERS)
    second_bootstrap = post("/api/reference/bootstrap", {}, OWNER_HEADERS)["bootstrap"]
    migration = second_bootstrap.get("city_code_migration") or {}
    if migration.get("airport_city_codes_updated"):
        raise AssertionError("City code migration was not idempotent after reference seed.")

    cities = get("/api/platform/reference/records?domain=cities&include_inactive=true", OWNER_HEADERS)["items"]
    active_cities = {item["code"]: item for item in cities if item.get("is_active", True)}
    missing = set(EXPECTED_CITY_CODES) - set(active_cities)
    if missing:
        raise AssertionError(f"Missing canonical city code(s): {sorted(missing)}")
    active_legacy = LEGACY_CITY_CODES.intersection(active_cities)
    if active_legacy:
        raise AssertionError(f"Legacy slug city code(s) still active: {sorted(active_legacy)}")
    for code, legacy_alias in EXPECTED_CITY_CODES.items():
        aliases = set(active_cities[code].get("aliases") or [])
        if legacy_alias not in aliases:
            raise AssertionError(f"{code} did not preserve legacy alias {legacy_alias}.")
        metadata = active_cities[code].get("metadata_json") or {}
        if metadata.get("record_type") != "city":
            raise AssertionError(f"{code} metadata did not identify the record as a city.")
        if metadata.get("iata_city_code") != code:
            raise AssertionError(f"{code} metadata did not mirror the canonical city code.")
        if metadata.get("city_name") != active_cities[code].get("label"):
            raise AssertionError(f"{code} metadata did not mirror the city label.")
        if legacy_alias not in set(metadata.get("legacy_codes") or []):
            raise AssertionError(f"{code} metadata did not preserve legacy code {legacy_alias}.")
        if not metadata.get("country_code"):
            raise AssertionError(f"{code} metadata did not preserve country_code.")

    airports = get("/api/platform/reference/records?domain=airports&include_inactive=true", OWNER_HEADERS)["items"]
    airport_city_codes = {item.get("metadata_json", {}).get("city_code") for item in airports}
    if LEGACY_CITY_CODES.intersection(airport_city_codes):
        raise AssertionError("Airport records still point to legacy city slug codes.")

    post("/api/platform/reference/records", {"domain": "cities", "code": "BAD", "label": "Agency Blocked"}, AGENCY_HEADERS, 403)
    post(
        "/api/platform/reference/records",
        {"domain": "cities", "code": "LON", "label": "Contradictory City", "metadata_json": {"iata_city_code": "SOF"}},
        OWNER_HEADERS,
        409,
    )
    post(
        "/api/platform/reference/records",
        {"domain": "cities", "code": "ZZZ", "label": "Contradictory City", "metadata_json": {"iata_city_code": "SOF"}},
        OWNER_HEADERS,
        400,
    )

    reference_service = (ROOT / "backend/services/reference_data_service.py").read_text(encoding="utf-8")
    platform_page = (ROOT / "frontend/src/pages/platform/PlatformReferenceDataPage.jsx").read_text(encoding="utf-8")
    for needle in ['"code": "SOF"', '"code": "NYC"', '"code": "LON"', '"SOFIA"', '"NEW_YORK"', '"LONDON"', "normalize_city_reference_codes"]:
        if needle not in reference_service:
            raise AssertionError(f"Reference seed/migration missing marker: {needle}")
    for needle in ["IATA City Code", "IATA Airport Code", "Airline Code", "buildMetadataFromRecordForm", "mergeMetadataIntoRecordForm", "domainSpecificMetadataKeys"]:
        if needle not in platform_page:
            raise AssertionError(f"Platform console missing domain-specific code label: {needle}")

    print(f"City reference codes smoke passed. Seed bootstrap keys: {sorted(first_seed.get('reference_bootstrap', {}).keys())}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"City reference codes smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
