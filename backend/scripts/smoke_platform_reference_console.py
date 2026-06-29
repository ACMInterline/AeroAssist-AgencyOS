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
AGENCY_HEADERS = {"X-Demo-User-Email": "agency.agent@aeroassist.dev"}
EXPECTED_PHASE = "phase_36_4_6_standalone_change_exchange_foundation"
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


def valid_country_metadata(suffix: str) -> dict:
    return {
        "iso2_code": "XZ",
        "iso3_code": "XZZ",
        "continent": "Smoke",
        "capital_city": f"Smoke City {suffix}",
        "capital_iata_code": "XZA",
        "major_airports": ["XZA", "XZB", "XZC"],
        "official_languages": ["Smokeish", "English"],
        "currency_name": "Smoke credit",
        "currency_iso_code": "XZD",
        "population_estimate": 123456,
        "population_estimate_year": 2026,
        "national_carrier": {"name": "Smoke Air", "iata_code": "X1"},
        "major_airlines": [
            {"name": "Smoke Air", "iata_code": "X1"},
            {"name": "Test Wings", "iata_code": "T2"},
        ],
        "travel_notes": "Smoke-test record only.",
        "data_quality_status": "draft",
        "source_notes": "Created by smoke_platform_reference_console.py",
    }


def main() -> int:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")

    post("/api/reference/seed", {}, OWNER_HEADERS)
    domains = get("/api/platform/reference/domains", OWNER_HEADERS)["items"]
    if "countries" not in {item["domain"] for item in domains}:
        raise AssertionError("Platform reference domains did not include countries.")
    expected_domains = ["countries", "cities", "airports", "airlines", "currencies", "languages"]
    for domain in expected_domains:
        records = get(f"/api/platform/reference/records?domain={domain}&include_inactive=true", OWNER_HEADERS)["items"]
        if not records:
            raise AssertionError(f"Platform records endpoint returned no records for {domain}.")
    cities = get("/api/platform/reference/records?domain=cities&include_inactive=true", OWNER_HEADERS)["items"]
    city_codes = {item.get("code") for item in cities if item.get("is_active", True)}
    if not {"SOF", "NYC", "LON"}.issubset(city_codes):
        raise AssertionError("Cities records endpoint did not return canonical IATA city codes.")
    if {"SOFIA", "NEW_YORK", "LONDON"}.intersection(city_codes):
        raise AssertionError("Cities records endpoint returned legacy slug city codes as active records.")

    platform_page = (ROOT / "frontend/src/pages/platform/PlatformReferenceDataPage.jsx").read_text(encoding="utf-8")
    for needle in ["Open records", "Edit metadata", "selectedDomainHasCountrySchema", "Global Records:", "Status / Governance", "IATA City Code"]:
        if needle not in platform_page:
            raise AssertionError(f"PlatformReferenceDataPage missing domain navigation/table behavior marker: {needle}")
    agency_page = (ROOT / "frontend/src/pages/agency/ReferenceDataPage.jsx").read_text(encoding="utf-8")
    for forbidden in ["Create global record", "Edit", "Deactivate", "Upload import batch", "Import / Bulk Upload"]:
        if forbidden in agency_page:
            raise AssertionError(f"Agency reference page regressed into management UI: {forbidden}")

    now = int(time.time())
    code = f"smoke_country_{now}"
    record = post(
        "/api/platform/reference/records",
        {"domain": "countries", "code": code, "label": "Smoke Country", "metadata_json": valid_country_metadata(str(now))},
        OWNER_HEADERS,
        201,
    )["record"]
    updated = put(
        f"/api/platform/reference/records/{record['id']}",
        {"label": "Smoke Country Verified", "metadata_json": {**valid_country_metadata(str(now)), "data_quality_status": "verified"}},
        OWNER_HEADERS,
    )["record"]
    if updated["metadata_json"].get("reviewed_by_user_id") is None:
        raise AssertionError("Verified country metadata did not capture reviewer information.")

    post(
        "/api/platform/reference/records",
        {"domain": "countries", "code": f"agency_forbidden_{now}", "label": "Forbidden", "metadata_json": valid_country_metadata("forbidden")},
        AGENCY_HEADERS,
        403,
    )
    post("/api/platform/reference/records", {"domain": "countries", "code": f"bad_iso3_{now}", "label": "Bad ISO3", "metadata_json": {**valid_country_metadata("bad"), "iso3_code": "XX"}}, OWNER_HEADERS, 400)
    post("/api/platform/reference/records", {"domain": "countries", "code": f"bad_airport_{now}", "label": "Bad Airport", "metadata_json": {**valid_country_metadata("bad"), "capital_iata_code": "12"}}, OWNER_HEADERS, 400)
    post("/api/platform/reference/records", {"domain": "countries", "code": f"too_many_airports_{now}", "label": "Too Many Airports", "metadata_json": {**valid_country_metadata("bad"), "major_airports": ["AAA", "BBB", "CCC", "DDD"]}}, OWNER_HEADERS, 400)

    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    suggestion_code = f"suggested_country_{now}"
    suggestion = post(
        "/api/reference/suggestions",
        {
            "submitting_agency_id": agency_id,
            "domain": "countries",
            "suggested_code": suggestion_code,
            "suggested_label": "Suggested Smoke Country",
            "suggested_metadata_json": valid_country_metadata("suggestion"),
            "suggestion_type": "new_record",
            "source_context": "manual_reference_page",
        },
        AGENCY_HEADERS,
        201,
    )["suggestion"]
    approved = post(f"/api/platform/reference/suggestions/{suggestion['id']}/approve", {"reviewer_note": "Approved by platform smoke."}, OWNER_HEADERS)["record"]
    if approved["code"] != suggestion_code:
        raise AssertionError("Platform approval did not promote the suggested country record.")

    blocked_suggestion = post(
        "/api/reference/suggestions",
        {
            "submitting_agency_id": agency_id,
            "domain": "countries",
            "suggested_code": f"blocked_country_{now}",
            "suggested_label": "Blocked Smoke Country",
            "suggested_metadata_json": valid_country_metadata("blocked"),
            "suggestion_type": "new_record",
            "source_context": "manual_reference_page",
        },
        AGENCY_HEADERS,
        201,
    )["suggestion"]
    post(f"/api/platform/reference/suggestions/{blocked_suggestion['id']}/approve", {"reviewer_note": "Should fail."}, AGENCY_HEADERS, 403)

    dry_code = f"dry_import_country_{now}"
    import_code = f"commit_import_country_{now}"
    dry_csv = "\n".join(
        [
            "domain,code,label,iso2_code,iso3_code,continent,capital_city,capital_iata_code,major_airports,official_languages,currency_name,currency_iso_code,national_carrier_name,national_carrier_iata_code,data_quality_status",
            f"countries,{dry_code},Dry Import Country,XZ,XZZ,Smoke,Dry City,XZA,\"XZA,XZB\",Smokeish,Smoke credit,XZD,Smoke Air,X1,draft",
        ]
    )
    dry_batch = post("/api/platform/reference/import", {"scope": "global", "domain": "countries", "filename": "dry.csv", "csv_text": dry_csv, "dry_run": True}, OWNER_HEADERS, 201)["batch"]
    if dry_batch["inserted_count"] != 0 or get(f"/api/platform/reference/records?domain=countries&q={dry_code}", OWNER_HEADERS)["items"]:
        raise AssertionError("Dry-run import inserted records.")

    commit_csv = dry_csv.replace(dry_code, import_code).replace("Dry Import Country", "Committed Import Country")
    first_commit = post("/api/platform/reference/import", {"scope": "global", "domain": "countries", "filename": "commit.csv", "csv_text": commit_csv, "dry_run": False}, OWNER_HEADERS, 201)["batch"]
    second_commit = post("/api/platform/reference/import", {"scope": "global", "domain": "countries", "filename": "commit.csv", "csv_text": commit_csv, "dry_run": False}, OWNER_HEADERS, 201)["batch"]
    if first_commit["inserted_count"] != 1 or second_commit["updated_count"] != 1:
        raise AssertionError("Committed platform import was not a safe upsert.")

    csv_export = get("/api/platform/reference/export?export_type=domain&domain=countries&format=csv", OWNER_HEADERS)
    json_export = get("/api/platform/reference/export?export_type=domain&domain=countries&format=json", OWNER_HEADERS)
    if import_code not in csv_export.get("content", "") or import_code not in json_export.get("content", ""):
        raise AssertionError("Platform export did not include committed country record.")

    readiness = get("/api/readiness")
    console = readiness.get("platform_reference_console") or {}
    for flag in [
        "platform_reference_console_enabled",
        "enriched_country_schema_enabled",
        "platform_reference_import_enabled",
        "platform_reference_export_enabled",
        "platform_reference_suggestion_review_enabled",
        "reference_record_card_enabled",
    ]:
        if console.get(flag) is not True:
            raise AssertionError(f"Readiness missing platform reference flag: {flag}")
    if console.get("country_record_count", 0) < 1 or console.get("enriched_country_record_count", 0) < 1:
        raise AssertionError("Readiness did not count enriched countries.")

    print("Platform reference console smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Platform reference console smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
