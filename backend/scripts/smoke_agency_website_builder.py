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


def put(path: str, body: dict, headers: dict | None = None, expect: int | None = None) -> dict:
    return request("PUT", path, body, headers, expect)[1]


def assert_no_custom_code(payload: dict) -> None:
    serialized = json.dumps(payload).lower()
    forbidden = ["<script", "javascript:", "<iframe", "custom_css", "custom_js", "token_hash"]
    leaked = [item for item in forbidden if item in serialized]
    if leaked:
        raise AssertionError(f"Website payload leaked unsafe/custom-code fields: {leaked}")


def main() -> int:
    health = get("/api/health")
    if health.get("phase") != "phase_29_agency_website_builder_cms_foundation":
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")
    post("/api/reference/seed", {}, OWNER_HEADERS)
    agencies = get("/api/agencies", OWNER_HEADERS)["items"]
    if not agencies:
        raise AssertionError("No agency available for website smoke.")
    agency_id = agencies[0]["id"]
    slug = f"phase29-{int(time.time())}"

    get(f"/api/agencies/{agency_id}/website", {"Authorization": "Bearer definitely-not-valid"}, 401)
    initial = get(f"/api/agencies/{agency_id}/website", OWNER_HEADERS)
    assert_no_custom_code(initial)
    if "settings" not in initial:
        raise AssertionError("Website settings response missing settings.")

    put(
        f"/api/agencies/{agency_id}/website",
        {"site_name": "Phase 29 Travel", "slug": slug, "tagline": "<script>alert(1)</script>"},
        OWNER_HEADERS,
        400,
    )

    settings = put(
        f"/api/agencies/{agency_id}/website",
        {
            "site_name": "Phase 29 Travel",
            "slug": slug,
            "tagline": "Accessible travel support for real clients.",
            "status": "draft",
            "seo_title": "Phase 29 Travel",
            "seo_description": "CMS smoke test website.",
            "contact_email": "hello@example.com",
            "contact_phone": "+421900290000",
            "show_request_cta": True,
        },
        OWNER_HEADERS,
    )
    if settings["settings"]["slug"] != slug:
        raise AssertionError("Website settings slug did not persist.")

    put(f"/api/agencies/{agency_id}/website", {"status": "active"}, OWNER_HEADERS, 400)

    unsafe_page = {
        "title": "Unsafe",
        "slug": "unsafe",
        "page_type": "custom",
        "sections": [{"section_type": "text", "heading": "Unsafe", "body": "javascript:alert(1)"}],
    }
    post(f"/api/agencies/{agency_id}/website/pages", unsafe_page, OWNER_HEADERS, 400)

    page = post(
        f"/api/agencies/{agency_id}/website/pages",
        {
            "title": "Home",
            "slug": "home",
            "page_type": "home",
            "sections": [
                {
                    "section_type": "hero",
                    "eyebrow": "Travel assistance",
                    "heading": "Travel support without the chaos",
                    "body": "Our team coordinates planning, mobility assistance, documents, and follow-up.",
                    "cta_label": "Request assistance",
                    "cta_href": "/",
                    "items": ["Mobility assistance", "Document guidance", "Manual agency review"],
                }
            ],
        },
        OWNER_HEADERS,
        201,
    )["page"]
    published = post(f"/api/agencies/{agency_id}/website/pages/{page['id']}/publish", {}, OWNER_HEADERS)
    if published["page"]["status"] != "published":
        raise AssertionError("Page was not published.")

    active = put(f"/api/agencies/{agency_id}/website", {"status": "active"}, OWNER_HEADERS)
    if active["settings"]["status"] != "active":
        raise AssertionError("Website was not activated.")

    public = get(f"/api/public/websites/{slug}")
    assert_no_custom_code(public)
    if public["settings"]["slug"] != slug or not public["pages"]:
        raise AssertionError("Public website did not expose published page safely.")

    readiness = get("/api/readiness")
    if "agency_websites" not in readiness or readiness["agency_websites"].get("readiness_required") is not False:
        raise AssertionError("Readiness does not expose optional website summary.")

    print("Agency website builder smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Agency website builder smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
