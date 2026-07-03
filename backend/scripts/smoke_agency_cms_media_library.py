#!/usr/bin/env python3
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request


BASE_URL = os.getenv("AEROASSIST_SMOKE_BASE_URL", "http://localhost:8000")
OWNER_TOKEN = os.getenv("AEROASSIST_SMOKE_OWNER_TOKEN")
OWNER_HEADERS = {"Authorization": f"Bearer {OWNER_TOKEN}"} if OWNER_TOKEN else {"X-Demo-User-Email": "owner@aeroassist.dev"}
ONE_BY_ONE_PNG = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="


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


def delete(path: str, headers: dict | None = None, expect: int | None = None) -> dict:
    return request("DELETE", path, None, headers, expect)[1]


def assert_safe(payload: dict) -> None:
    serialized = json.dumps(payload).lower()
    forbidden = ["file_path", "/users/", "/var/", "data_base64", "<script", "javascript:", "<svg"]
    leaked = [item for item in forbidden if item in serialized]
    if leaked:
        raise AssertionError(f"Media payload leaked unsafe fields: {leaked}")


def main() -> int:
    health = get("/api/health")
    if health.get("phase") != "phase_38_0_offer_decision_export_audit_review_foundation":
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")
    post("/api/reference/seed", {}, OWNER_HEADERS)
    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    slug = f"media-smoke-{int(time.time())}"

    get(f"/api/agencies/{agency_id}/website/media", {"Authorization": "Bearer definitely-not-valid"}, 401)
    post(
        f"/api/agencies/{agency_id}/website/media",
        {"filename": "unsafe.svg", "content_type": "image/svg+xml", "data_base64": base64.b64encode(b"<svg/>").decode("ascii"), "title": "Unsafe", "alt_text": "Unsafe"},
        OWNER_HEADERS,
        400,
    )
    post(
        f"/api/agencies/{agency_id}/website/media",
        {"filename": "bad.png", "content_type": "image/png", "data_base64": base64.b64encode(b"not an image").decode("ascii"), "title": "Bad", "alt_text": "Bad"},
        OWNER_HEADERS,
        400,
    )
    uploaded = post(
        f"/api/agencies/{agency_id}/website/media",
        {
            "filename": "hero.png",
            "content_type": "image/png",
            "data_base64": ONE_BY_ONE_PNG,
            "title": "Hero aircraft assistance",
            "alt_text": "Aircraft assistance desk",
            "caption": "Prepared public-safe CMS image.",
            "usage_context": "hero",
            "asset_type": "image",
            "public_usage_allowed": True,
        },
        OWNER_HEADERS,
        201,
    )["asset"]
    assert_safe(uploaded)
    for variant in ["thumbnail", "card", "hero", "original_safe"]:
        if variant not in uploaded["variants"] or not uploaded["variants"][variant].get("url"):
            raise AssertionError(f"Missing generated media variant: {variant}")

    private_asset = post(
        f"/api/agencies/{agency_id}/website/media",
        {
            "filename": "private.png",
            "content_type": "image/png",
            "data_base64": ONE_BY_ONE_PNG,
            "title": "Private image",
            "alt_text": "Private image",
            "usage_context": "general",
            "asset_type": "image",
            "public_usage_allowed": False,
        },
        OWNER_HEADERS,
        201,
    )["asset"]

    media_list = get(f"/api/agencies/{agency_id}/website/media", OWNER_HEADERS)
    assert_safe(media_list)
    if uploaded["id"] not in [item["id"] for item in media_list["items"]]:
        raise AssertionError("Uploaded media asset missing from media list.")

    updated = put(f"/api/agencies/{agency_id}/website/media/{uploaded['id']}", {"title": "Updated Hero", "alt_text": "Updated aircraft assistance"}, OWNER_HEADERS)["asset"]
    if updated["title"] != "Updated Hero" or updated["alt_text"] != "Updated aircraft assistance":
        raise AssertionError("Media metadata update did not persist.")

    put(f"/api/agencies/{agency_id}/website", {"site_name": "Media Smoke", "slug": slug, "status": "draft", "show_request_cta": True}, OWNER_HEADERS)
    page = post(
        f"/api/agencies/{agency_id}/website/pages",
        {
            "title": "Media",
            "slug": "media",
            "page_type": "custom",
            "sections": [{"section_type": "hero", "heading": "Safe media hero", "body": "Rendered with a CMS media asset.", "image_asset_id": uploaded["id"], "primary_cta_label": "Request", "primary_cta_target": "/request"}],
        },
        OWNER_HEADERS,
        201,
    )["page"]
    put(
        f"/api/agencies/{agency_id}/website/pages/{page['id']}",
        {"sections": [{"section_type": "hero", "heading": "Private media should fail", "image_asset_id": private_asset["id"]}]},
        OWNER_HEADERS,
        400,
    )
    post(f"/api/agencies/{agency_id}/website/pages/{page['id']}/publish", {}, OWNER_HEADERS)
    put(f"/api/agencies/{agency_id}/website", {"status": "active"}, OWNER_HEADERS)
    public_site = get(f"/api/public/websites/{slug}")
    assert_safe(public_site)
    if uploaded["id"] not in public_site.get("media_assets", {}):
        raise AssertionError("Published site did not include referenced public-safe media asset.")
    if private_asset["id"] in public_site.get("media_assets", {}):
        raise AssertionError("Private media asset leaked to public website response.")
    if public_site["media_assets"][uploaded["id"]]["hero_url"] is None:
        raise AssertionError("Public media asset missing hero variant URL.")

    submitted = post(
        f"/api/public/websites/{slug}/request",
        {
            "contact": {"name": "Media Visitor", "email": "media@example.com", "privacy_policy_accepted": True, "data_processing_consent": True},
            "travel": {"origin": "SOF", "destination": "JFK", "passenger_count": 1},
            "services": {"selected_service_categories": ["mobility assistance"], "mobility_assistance": True},
            "request_details": "Need visual-polished website intake.",
        },
        expect=201,
    )
    if submitted["intake"]["status"] != "received":
        raise AssertionError("Public website request did not create intake receipt.")

    post(f"/api/agencies/{agency_id}/website/unpublish", {}, OWNER_HEADERS)
    post(f"/api/agencies/{agency_id}/website/pages/{page['id']}/archive", {}, OWNER_HEADERS)

    archived = delete(f"/api/agencies/{agency_id}/website/media/{uploaded['id']}", OWNER_HEADERS)["asset"]
    if archived["status"] != "archived" or archived["public_usage_allowed"]:
        raise AssertionError("Media archive did not disable public usage.")

    readiness = get("/api/readiness")
    if not readiness["agency_websites"].get("cms_media_library_enabled") or readiness["agency_websites"].get("media_asset_count", 0) < 1:
        raise AssertionError("Readiness does not expose media library counts.")

    print("Agency CMS media library smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Agency CMS media library smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
