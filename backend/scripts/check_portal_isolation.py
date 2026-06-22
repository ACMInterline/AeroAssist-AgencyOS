#!/usr/bin/env python3
import json
import os
import sys
import urllib.error
import urllib.request


BASE_URL = os.getenv("AEROASSIST_SMOKE_BASE_URL", "http://localhost:8000")
OWNER_HEADERS = {"X-Demo-User-Email": "owner@aeroassist.dev"}
PORTAL_A = {"X-Demo-Role": "portal_client", "X-Demo-Client-Email": "anna.client@example.com"}
PORTAL_B = {"X-Demo-Role": "portal_client", "X-Demo-Client-Email": "travel@orbitex.example.com"}
FORBIDDEN_STRINGS = [
    "internal_notes",
    "reconciliation_notes",
    "airline_knowledge",
    "medical_notes_internal",
    "travel_document_notes",
    "passport_number",
    "sent_snapshot",
    "booking_snapshot",
    "source_snapshot",
]


def request(method: str, path: str, headers: dict | None = None, expected_status: int = 200) -> dict | None:
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        method=method,
        headers={**(headers or {}), "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            body = response.read().decode("utf-8")
            if response.status != expected_status:
                raise AssertionError(f"{method} {path} returned {response.status}, expected {expected_status}")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        if exc.code == expected_status:
            return None
        detail = exc.read().decode("utf-8")
        raise AssertionError(f"{method} {path} failed with {exc.code}: {detail}") from exc


def get(path: str, headers: dict | None = None, expected_status: int = 200) -> dict | None:
    return request("GET", path, headers, expected_status)


def assert_no_internal_fields(payload: dict | None, path: str) -> None:
    text = json.dumps(payload or {}, sort_keys=True)
    leaked = [field for field in FORBIDDEN_STRINGS if field in text]
    if leaked:
        raise AssertionError(f"{path} leaked internal field names: {leaked}")


def first_id(payload: dict, key: str = "items") -> str | None:
    items = payload.get(key, [])
    return items[0]["id"] if items else None


def main() -> int:
    request("POST", "/api/reference/seed", OWNER_HEADERS)

    portal_paths = [
        "/api/portal/me",
        "/api/portal/dashboard",
        "/api/portal/profile",
        "/api/portal/passengers",
        "/api/portal/requests",
        "/api/portal/offers",
        "/api/portal/bookings",
        "/api/portal/documents",
        "/api/portal/invoices",
        "/api/portal/payments",
    ]
    for headers in (PORTAL_A, PORTAL_B):
        for path in portal_paths:
            assert_no_internal_fields(get(path, headers), path)

    anna_passenger_id = first_id(get("/api/portal/passengers", PORTAL_A))
    company_passenger_id = first_id(get("/api/portal/passengers", PORTAL_B))
    if anna_passenger_id and company_passenger_id:
        get(f"/api/portal/passengers/{company_passenger_id}", PORTAL_A, expected_status=404)
        get(f"/api/portal/passengers/{anna_passenger_id}", PORTAL_B, expected_status=404)

    cross_detail_paths = [
        ("/api/portal/requests", "/api/portal/requests/{}"),
        ("/api/portal/offers", "/api/portal/offers/{}"),
        ("/api/portal/bookings", "/api/portal/bookings/{}"),
        ("/api/portal/documents", "/api/portal/documents/{}"),
        ("/api/portal/invoices", "/api/portal/invoices/{}"),
    ]
    for list_path, detail_template in cross_detail_paths:
        b_id = first_id(get(list_path, PORTAL_B))
        if b_id:
            get(detail_template.format(b_id), PORTAL_A, expected_status=404)

    print("Portal isolation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Portal isolation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
