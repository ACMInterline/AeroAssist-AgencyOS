#!/usr/bin/env python3
import json
import os
import sys
import time
import urllib.error
import urllib.request


BASE_URL = os.getenv("AEROASSIST_SMOKE_BASE_URL", "http://localhost:8000")
OWNER_TOKEN = os.getenv("AEROASSIST_SMOKE_OWNER_TOKEN")
OWNER_HEADERS = {"Authorization": f"Bearer {OWNER_TOKEN}"} if OWNER_TOKEN else {"X-Demo-User-Email": "owner@aeroassist.dev"}
AGENCY_HEADERS = {"X-Demo-User-Email": "agency.agent@aeroassist.dev"}
EXPECTED_PHASE = "phase_36_7_airline_policy_ingestion_foundation"


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


def enrichment_csv(code: str, iso3: str = "TST", airports: str = "TSA,TSB,TSC", capital_iata: str = "TSA") -> str:
    return "\n".join(
        [
            "code,label,iso2_code,iso3_code,continent,region,capital_city,capital_iata_code,major_airport_1,major_airport_2,major_airport_3,official_language_1,currency_name,currency_iso_code,national_carrier_name,national_carrier_iata_code,data_quality_status,source_notes",
            f"{code},Testland,{code[:2].upper()},{iso3},Test Continent,Test Region,Test City,{capital_iata},{','.join(airports.split(',')[:1])},{','.join(airports.split(',')[1:2])},{','.join(airports.split(',')[2:3])},Testish,Test credit,TST,Test Air,T1,draft,Smoke enrichment import",
        ]
    )


def main() -> int:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")

    post("/api/reference/seed", {}, OWNER_HEADERS)
    templates = get("/api/platform/reference/enrichment/templates", OWNER_HEADERS)["items"]
    if "countries_enriched" not in {item["template_name"] for item in templates}:
        raise AssertionError("Countries enrichment template missing.")
    template = get("/api/platform/reference/enrichment/template/countries_enriched", OWNER_HEADERS)
    if "iso3_code" not in template.get("csv_text", ""):
        raise AssertionError("Countries template is missing enriched headers.")
    get("/api/platform/reference/enrichment/templates", AGENCY_HEADERS, 403)
    post("/api/platform/reference/enrichment/dry-run", {"domain": "countries", "csv_text": template["csv_text"]}, AGENCY_HEADERS, 403)

    now = int(time.time())
    letter = chr(65 + (now % 26))
    second_letter = chr(65 + ((now // 26) % 26))
    code = f"X{letter}"
    dry = post(
        "/api/platform/reference/enrichment/dry-run",
        {"domain": "countries", "csv_text": enrichment_csv(code), "update_mode": "insert_only", "dry_run": True},
        OWNER_HEADERS,
    )["report"]
    if dry["failed"] != 0 or dry["inserted"] != 1:
        raise AssertionError(f"Country dry run did not validate as expected: {dry}")
    if get(f"/api/platform/reference/records?domain=countries&q={code}", OWNER_HEADERS)["items"]:
        raise AssertionError("Dry-run country import inserted data.")

    bad_iso = post("/api/platform/reference/enrichment/dry-run", {"domain": "countries", "csv_text": enrichment_csv(f"I{str(now)[-5:]}", "XX")}, OWNER_HEADERS)["report"]
    if bad_iso["failed"] < 1:
        raise AssertionError("Invalid ISO3 was not rejected.")
    bad_airport = post("/api/platform/reference/enrichment/dry-run", {"domain": "countries", "csv_text": enrichment_csv(f"A{str(now)[-5:]}", "AIR", "BAD,TSB,TSC", "12")}, OWNER_HEADERS)["report"]
    if bad_airport["failed"] < 1:
        raise AssertionError("Invalid airport IATA was not rejected.")
    too_many = post(
        "/api/platform/reference/enrichment/dry-run",
        {
            "domain": "countries",
            "csv_text": "\n".join(
                [
                    "code,label,iso2_code,iso3_code,continent,capital_city,capital_iata_code,major_airports,data_quality_status",
                    f"M{str(now)[-5:]},Many Airports,MM,MMM,Test,City,AAA,\"AAA,BBB,CCC,DDD\",draft",
                ]
            ),
        },
        OWNER_HEADERS,
    )["report"]
    if too_many["failed"] < 1:
        raise AssertionError("More than 3 major airports was not rejected.")

    committed = post(
        "/api/platform/reference/enrichment/import",
        {"domain": "countries", "csv_text": enrichment_csv(code), "update_mode": "insert_only", "dry_run": False},
        OWNER_HEADERS,
    )["report"]
    if committed["inserted"] != 1:
        raise AssertionError("Committed country import did not insert.")
    repeated = post(
        "/api/platform/reference/enrichment/import",
        {"domain": "countries", "csv_text": enrichment_csv(code), "update_mode": "insert_only", "dry_run": False},
        OWNER_HEADERS,
    )["report"]
    if repeated["skipped"] != 1:
        raise AssertionError("Repeated insert_only import did not skip existing record.")

    verified_code = f"Y{second_letter}"
    post(
        "/api/platform/reference/records",
        {
            "domain": "countries",
            "code": verified_code,
            "label": "Verifiedland",
            "metadata_json": {"iso2_code": "VV", "iso3_code": "VFD", "capital_iata_code": "VFA", "data_quality_status": "verified"},
        },
        OWNER_HEADERS,
        201,
    )
    post("/api/platform/reference/enrichment/import", {"domain": "countries", "csv_text": enrichment_csv(verified_code, "NEW"), "update_mode": "update_missing_only", "dry_run": False}, OWNER_HEADERS)
    verified = get(f"/api/platform/reference/records?domain=countries&q={verified_code}", OWNER_HEADERS)["items"][0]
    if verified["metadata_json"].get("iso3_code") != "VFD":
        raise AssertionError("update_missing_only overwrote verified country data.")

    airport_code = f"Q{letter}{second_letter}"
    airport_csv = "\n".join(
        [
            "code,label,iata_code,icao_code,city,country_iso2,country_iso3,country_code,timezone,latitude,longitude,airport_type,is_major_airport,aliases,data_quality_status,source_notes",
            f"{airport_code},Smoke Airport,{airport_code},QAAA,Smoke City,{code[:2].upper()},TST,{code},UTC,1.1,2.2,international,true,Smoke Field,draft,Smoke enrichment",
        ]
    )
    airline_code = f"Z{letter}"
    airline_csv = "\n".join(
        [
            "code,label,iata_code,icao_code,country_iso2,country_iso3,country_code,airline_type,is_national_carrier,active,aliases,data_quality_status,source_notes",
            f"{airline_code},Smoke Air,{airline_code},ZZA,{code[:2].upper()},TST,{code},scheduled,true,true,Smoke Airways,draft,Smoke enrichment",
        ]
    )
    currency_csv = "code,label,currency_iso_code,currency_name,numeric_code,minor_unit,symbol,aliases,data_quality_status,source_notes\nXTS,Test Credit,XTS,Test Credit,999,2,¤,Test money,draft,Smoke enrichment"
    language_csv = "code,label,iso639_1,iso639_2,name,native_name,aliases,data_quality_status,source_notes\nzz,Testish,zz,zzz,Testish,Testish,Test language,draft,Smoke enrichment"
    for domain, csv_text in [("airports", airport_csv), ("airlines", airline_csv), ("currencies", currency_csv), ("languages", language_csv)]:
        report = post("/api/platform/reference/enrichment/import", {"domain": domain, "csv_text": csv_text, "update_mode": "insert_only", "dry_run": False}, OWNER_HEADERS)["report"]
        if report["inserted"] != 1:
            raise AssertionError(f"{domain} enrichment import did not insert.")

    readiness = get("/api/readiness")
    console = readiness.get("platform_reference_console") or {}
    for flag in ["reference_enrichment_import_enabled", "reference_enrichment_templates_enabled"]:
        if console.get(flag) is not True:
            raise AssertionError(f"Readiness missing enrichment flag: {flag}")
    for count in ["enriched_airport_record_count", "enriched_airline_record_count", "enriched_currency_record_count", "enriched_language_record_count"]:
        if console.get(count, 0) < 1:
            raise AssertionError(f"Readiness missing enrichment count: {count}")

    get("/api/platform/reference/domains", OWNER_HEADERS)
    agency_domains = get("/api/reference/domains", AGENCY_HEADERS)
    if not agency_domains.get("domains"):
        raise AssertionError("Agency reference view cannot consume domains.")

    print("Reference enrichment imports smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Reference enrichment imports smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
