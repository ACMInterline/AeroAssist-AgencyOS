#!/usr/bin/env python3
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


BASE_URL = os.getenv("AEROASSIST_SMOKE_BASE_URL", "http://localhost:8000")
OWNER_TOKEN = os.getenv("AEROASSIST_SMOKE_OWNER_TOKEN")
OWNER_HEADERS = {"Authorization": f"Bearer {OWNER_TOKEN}"} if OWNER_TOKEN else {"X-Demo-User-Email": "owner@aeroassist.dev"}


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


def assert_safe(value: object) -> None:
    serialized = json.dumps(value)
    forbidden = ["/var/", "/opt/", ".local/", "smtp_password_secret_ref\": \"env:", "token_hash"]
    leaked = [item for item in forbidden if item in serialized]
    if leaked:
        raise AssertionError(f"Unsafe response detail leaked: {leaked}")


def main() -> int:
    health = get("/api/health")
    if health.get("phase") != "phase_39_2_airline_intelligence_knowledge_versioning_foundation":
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")
    readiness = get("/api/readiness")
    if not readiness.get("ok"):
        raise AssertionError("Readiness is not ok.")

    post("/api/reference/seed", {}, OWNER_HEADERS)
    agencies = get("/api/agencies", OWNER_HEADERS)["items"]
    if not agencies:
        raise AssertionError("No agency available for storage lifecycle smoke.")
    agency_id = agencies[0]["id"]
    encoded_agency = urllib.parse.quote(agency_id)

    summary = get(f"/api/documents/storage/summary?agency_id={encoded_agency}", OWNER_HEADERS)
    health = get(f"/api/documents/storage/health?agency_id={encoded_agency}", OWNER_HEADERS)
    providers = get(f"/api/documents/delivery-providers?agency_id={encoded_agency}", OWNER_HEADERS)
    provider_readiness = get(f"/api/documents/delivery-providers/readiness?agency_id={encoded_agency}", OWNER_HEADERS)
    records = get(f"/api/documents/storage?agency_id={encoded_agency}", OWNER_HEADERS)

    for response in [summary, health, providers, provider_readiness, records]:
        assert_safe(response)

    manual = next((item for item in providers["items"] if item["provider_type"] == "manual"), None)
    if not manual or not manual.get("enabled") or manual.get("mode") != "manual":
        raise AssertionError("Manual provider is not enabled.")
    if provider_readiness["readiness"].get("automatic_delivery_enabled"):
        raise AssertionError("Automatic delivery should be disabled.")
    if provider_readiness["readiness"].get("public_links_enabled"):
        raise AssertionError("Public links should be disabled.")

    items = records.get("items", [])
    if items:
        record = items[0]
        archived = post(f"/api/documents/storage/{record['id']}/archive", {}, OWNER_HEADERS)
        assert_safe(archived)
        if archived["record"]["storage_status"] != "archived":
            raise AssertionError("Archive action did not mark record archived.")
        missing = post(f"/api/documents/storage/{record['id']}/mark-missing", {}, OWNER_HEADERS)
        assert_safe(missing)
        if missing["record"]["storage_status"] != "missing":
            raise AssertionError("Mark-missing action did not mark record missing.")

    print("Document storage lifecycle smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Document storage lifecycle smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
