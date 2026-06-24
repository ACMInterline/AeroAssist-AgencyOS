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
EXPECTED_PHASE = "phase_34_1_global_field_library_agency_form_profiles"


def request(method: str, path: str, body: dict | None = None, headers: dict | None = None, expect: int | None = None) -> tuple[int, dict]:
    data = json.dumps(body or {}).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        method=method,
        data=data,
        headers={**(headers or {}), "Content-Type": "application/json"},
    )
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


def patch(path: str, body: dict | None = None, headers: dict | None = None, expect: int | None = None) -> dict:
    return request("PATCH", path, body or {}, headers, expect)[1]


def assert_safe(payload: dict) -> None:
    serialized = json.dumps(payload).lower()
    leaked = [item for item in ["token_hash", "password_hash", "smtp_password", "/users/"] if item in serialized]
    if leaked:
        raise AssertionError(f"Reference payload leaked unsafe fields: {leaked}")


def main() -> int:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")

    first_bootstrap = post("/api/reference/bootstrap", {}, OWNER_HEADERS)["bootstrap"]
    second_bootstrap = post("/api/reference/bootstrap", {}, OWNER_HEADERS)["bootstrap"]
    if first_bootstrap["reference_records"]["inserted"] + first_bootstrap["reference_records"]["updated"] <= 0:
        raise AssertionError("Reference bootstrap did not process records.")
    if second_bootstrap["reference_records"]["updated"] <= 0:
        raise AssertionError("Reference bootstrap was not idempotent on second run.")

    domains = get("/api/reference/domains", OWNER_HEADERS)
    assert_safe(domains)
    domain_names = {item["domain"] for item in domains["domains"]}
    for required_domain in ["passenger_types", "mobility_levels", "special_item_categories"]:
        if required_domain not in domain_names:
            raise AssertionError(f"Missing reference domain: {required_domain}")

    passengers = get("/api/reference/passenger_types", OWNER_HEADERS)
    if "adult" not in {item["code"] for item in passengers["items"]}:
        raise AssertionError("Passenger type bootstrap missing adult.")

    search = get("/api/reference/passenger_types/search?q=ADT", OWNER_HEADERS)
    if not search["items"]:
        raise AssertionError("Reference search did not match aliases.")

    get("/api/reference/not_a_domain", OWNER_HEADERS, 400)

    service_catalogue = get("/api/reference/service-catalogue", OWNER_HEADERS)
    assert_safe(service_catalogue)
    service_codes = {item["service_code"] for item in service_catalogue["items"]}
    for service_code in ["WCHR", "WCHS", "WCHC", "MEDA", "PETC", "AVIH", "UMNR"]:
        if service_code not in service_codes:
            raise AssertionError(f"Missing service catalogue record: {service_code}")
    families = get("/api/reference/service-catalogue/families", OWNER_HEADERS)
    if "wheelchair_mobility" not in {item["code"] for item in families["families"]}:
        raise AssertionError("Service catalogue families missing wheelchair mobility.")
    if not get("/api/reference/service-catalogue/search?q=oxygen", OWNER_HEADERS)["items"]:
        raise AssertionError("Service catalogue search did not find oxygen service.")

    smoke_code = f"smoke_chat_{int(time.time())}"
    created = post(
        "/api/reference/contact_channels",
        {"code": smoke_code, "label": "Smoke Chat", "aliases": ["smoke channel"], "sort_order": 999, "scope": "global"},
        OWNER_HEADERS,
        201,
    )["record"]
    if created["code"] != smoke_code:
        raise AssertionError("Reference create returned the wrong code.")
    patch(f"/api/reference/contact_channels/{created['id']}/deactivate", {}, OWNER_HEADERS)
    active_contacts = get("/api/reference/contact_channels", OWNER_HEADERS)
    if smoke_code in {item["code"] for item in active_contacts["items"]}:
        raise AssertionError("Inactive reference record leaked into active-only list.")
    inactive_contacts = get("/api/reference/contact_channels?include_inactive=true", OWNER_HEADERS)
    if smoke_code not in {item["code"] for item in inactive_contacts["items"]}:
        raise AssertionError("Inactive reference record missing from include_inactive list.")

    readiness = get("/api/readiness")
    reference_data = readiness.get("reference_data") or {}
    for flag in ["reference_data_enabled", "service_catalogue_enabled", "reference_bootstrap_available"]:
        if reference_data.get(flag) is not True:
            raise AssertionError(f"Readiness missing reference flag: {flag}")
    if reference_data.get("reference_domain_count", 0) < 20:
        raise AssertionError("Readiness reference domain count is too low.")

    print("Reference data core smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Reference data core smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
