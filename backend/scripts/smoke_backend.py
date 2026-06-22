#!/usr/bin/env python3
import json
import os
import sys
import urllib.error
import urllib.request


BASE_URL = os.getenv("AEROASSIST_SMOKE_BASE_URL", "http://localhost:8000")
OWNER_HEADERS = {"X-Demo-User-Email": "owner@aeroassist.dev"}


def request(method: str, path: str, headers: dict | None = None) -> dict:
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        method=method,
        headers={**(headers or {}), "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8")
        raise AssertionError(f"{method} {path} failed with {exc.code}: {detail}") from exc


def get(path: str, headers: dict | None = None) -> dict:
    return request("GET", path, headers)


def post(path: str, headers: dict | None = None) -> dict:
    return request("POST", path, headers)


def assert_count_stable(before: dict, after: dict) -> None:
    before_counts = before["counts"]
    after_counts = after["counts"]
    changed = {
        key: (before_counts.get(key), after_counts.get(key))
        for key in sorted(before_counts)
        if before_counts.get(key) != after_counts.get(key)
    }
    if changed:
        raise AssertionError(f"Seed idempotency changed counts: {changed}")


def main() -> int:
    get("/api/health")
    post("/api/reference/seed", OWNER_HEADERS)
    before = get("/api/platform/summary", OWNER_HEADERS)
    post("/api/reference/seed", OWNER_HEADERS)
    after = get("/api/platform/summary", OWNER_HEADERS)
    assert_count_stable(before, after)

    agencies = get("/api/agencies", OWNER_HEADERS)["items"]
    if not agencies:
        raise AssertionError("No agencies returned after seed.")
    agency_id = agencies[0]["id"]

    module_paths = [
        f"/api/agencies/{agency_id}",
        f"/api/agencies/{agency_id}/settings",
        f"/api/agencies/{agency_id}/staff",
        f"/api/agencies/{agency_id}/clients",
        f"/api/agencies/{agency_id}/passengers",
        f"/api/agencies/{agency_id}/client-passenger-relationships",
        f"/api/agencies/{agency_id}/requests",
        f"/api/agencies/{agency_id}/offers",
        f"/api/agencies/{agency_id}/bookings",
        f"/api/agencies/{agency_id}/invoices",
        f"/api/agencies/{agency_id}/payments",
        f"/api/agencies/{agency_id}/airline-intelligence/search",
        f"/api/agencies/{agency_id}/document-templates",
        f"/api/agencies/{agency_id}/documents",
    ]
    for path in module_paths:
        get(path, OWNER_HEADERS)

    detail_collections = [
        ("clients", f"/api/agencies/{agency_id}/clients"),
        ("passengers", f"/api/agencies/{agency_id}/passengers"),
        ("requests", f"/api/agencies/{agency_id}/requests"),
        ("offers", f"/api/agencies/{agency_id}/offers"),
        ("bookings", f"/api/agencies/{agency_id}/bookings"),
        ("invoices", f"/api/agencies/{agency_id}/invoices"),
        ("documents", f"/api/agencies/{agency_id}/documents"),
    ]
    for label, list_path in detail_collections:
        items = get(list_path, OWNER_HEADERS).get("items", [])
        if items:
            get(f"{list_path}/{items[0]['id']}", OWNER_HEADERS)

    print("Backend smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Backend smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
