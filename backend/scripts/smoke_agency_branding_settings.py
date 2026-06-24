#!/usr/bin/env python3
import base64
import json
import os
import sys
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


def assert_no_storage_path(payload: dict) -> None:
    serialized = json.dumps(payload)
    forbidden = ["file_path", "/var/", "/opt/", "/Users/", "data_base64", "token_hash", "<svg"]
    leaked = [value for value in forbidden if value in serialized]
    if leaked:
        raise AssertionError(f"Branding response leaked unsafe storage/raw fields: {leaked}")


def main() -> int:
    health = get("/api/health")
    if health.get("phase") != "phase_30_1_branding_logo_asset_settings_stabilization":
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")
    post("/api/reference/seed", {}, OWNER_HEADERS)
    agencies = get("/api/agencies", OWNER_HEADERS)["items"]
    if not agencies:
        raise AssertionError("No agency available for branding smoke.")
    agency_id = agencies[0]["id"]

    get(f"/api/agencies/{agency_id}/branding", {"Authorization": "Bearer definitely-not-valid"}, 401)
    initial = get(f"/api/agencies/{agency_id}/branding", OWNER_HEADERS)
    assert_no_storage_path(initial)
    if len(initial["design_options"]["fonts"]) < 10 or "quicksand" not in initial["design_options"]["fonts"]:
        raise AssertionError("Expected controlled font options including Quicksand.")
    if len(initial["design_options"]["palettes"]) < 10:
        raise AssertionError("Expected at least 10 controlled palettes.")

    put(f"/api/agencies/{agency_id}/branding", {"font_family_key": "comic_sans"}, OWNER_HEADERS, 422)
    put(f"/api/agencies/{agency_id}/branding", {"custom_css": "body{display:none}"}, OWNER_HEADERS, 422)
    put(f"/api/agencies/{agency_id}/branding", {"color_palette_key": "javascript:alert(1)"}, OWNER_HEADERS, 422)

    updated = put(
        f"/api/agencies/{agency_id}/branding",
        {
            "brand_name": "AeroAssist Smoke Agency",
            "font_family_key": "quicksand",
            "corner_radius_key": "soft",
            "density_key": "spacious",
            "theme_mode": "system",
            "color_palette_key": "midnight_navy",
            "field_style_key": "filled",
            "button_style_key": "soft",
            "calendar_style_key": "native_polished",
            "card_style_key": "raised",
            "logo_fit_mode": "contain",
            "preferred_logo_usage": "horizontal",
            "logo_public_usage_allowed": True,
        },
        OWNER_HEADERS,
    )
    assert_no_storage_path(updated)
    if updated["branding"]["font_family_key"] != "quicksand" or "Quicksand" not in updated["computed_theme"]["font_stack"]:
        raise AssertionError("Updated font choice was not persisted or computed.")

    post(
        f"/api/agencies/{agency_id}/branding/logo",
        {"filename": "unsafe.svg", "content_type": "image/svg+xml", "data_base64": base64.b64encode(b"<svg/>").decode("ascii")},
        OWNER_HEADERS,
        400,
    )
    post(
        f"/api/agencies/{agency_id}/branding/logo",
        {"filename": "logo.txt", "content_type": "image/png", "data_base64": ONE_BY_ONE_PNG},
        OWNER_HEADERS,
        400,
    )
    post(
        f"/api/agencies/{agency_id}/branding/logo",
        {"filename": "logo.png", "content_type": "image/png", "data_base64": base64.b64encode(b"not an image").decode("ascii")},
        OWNER_HEADERS,
        400,
    )
    logo = post(
        f"/api/agencies/{agency_id}/branding/logo",
        {"filename": "logo.png", "content_type": "image/png", "data_base64": ONE_BY_ONE_PNG},
        OWNER_HEADERS,
    )
    assert_no_storage_path(logo)
    variants = logo["branding"]["logo_assets"]["variants"]
    if not logo["logo_configured"] or not logo["branding"]["logo_url"].startswith("data:image/png;base64,"):
        raise AssertionError("Safe logo upload did not configure a controlled logo reference.")
    for variant in ["original", "square", "compact", "horizontal", "favicon"]:
        if variant not in variants:
            raise AssertionError(f"Missing generated logo variant: {variant}")
    if variants["original"].get("url") or variants["original"].get("public_usage_allowed"):
        raise AssertionError("Original logo asset should not be public-safe in API responses.")
    if variants["horizontal"].get("width_px") != 512 or variants["horizontal"].get("height_px") != 160:
        raise AssertionError("Horizontal logo variant dimensions are incorrect.")

    regen = post(f"/api/agencies/{agency_id}/branding/logo/regenerate", {}, OWNER_HEADERS)
    assert_no_storage_path(regen)
    if "horizontal" not in regen["branding"]["logo_assets"]["variants"]:
        raise AssertionError("Logo regeneration did not return generated variants.")

    slug = f"branding-smoke-{agency_id[-6:].lower()}"
    put(
        f"/api/agencies/{agency_id}/website",
        {"site_name": "Branding Smoke", "slug": slug, "tagline": "Public branding smoke.", "status": "draft"},
        OWNER_HEADERS,
    )
    page = post(
        f"/api/agencies/{agency_id}/website/pages",
        {
            "title": "Branding",
            "slug": "branding",
            "page_type": "custom",
            "sections": [{"section_type": "hero", "heading": "Branding smoke", "body": "Published page for public-safe branding."}],
        },
        OWNER_HEADERS,
        201,
    )["page"]
    post(f"/api/agencies/{agency_id}/website/pages/{page['id']}/publish", {}, OWNER_HEADERS)
    put(f"/api/agencies/{agency_id}/website", {"status": "active"}, OWNER_HEADERS)
    public_branding = get(f"/api/agencies/{agency_id}/branding/public")
    assert_no_storage_path(public_branding)
    if not public_branding["branding"]["logo_url"] or "original" in json.dumps(public_branding["branding"].get("logo_assets", {}).get("public_header", {})):
        raise AssertionError("Public-safe branding endpoint did not expose the safe header logo only.")
    public_site = get(f"/api/public/websites/{slug}")
    if not public_site["branding"].get("logo_url"):
        raise AssertionError("Public website did not expose safe logo branding.")
    post(f"/api/agencies/{agency_id}/website/unpublish", {}, OWNER_HEADERS)
    post(f"/api/agencies/{agency_id}/website/pages/{page['id']}/archive", {}, OWNER_HEADERS)

    removed = delete(f"/api/agencies/{agency_id}/branding/logo", OWNER_HEADERS)
    if removed["logo_configured"] or removed["branding"].get("logo_url"):
        raise AssertionError("Logo remove did not clear branding logo.")
    if removed["branding"]["public_branding"].get("logo_url"):
        raise AssertionError("Logo remove leaked an old public branding logo.")

    reset = post(f"/api/agencies/{agency_id}/branding/reset", {}, OWNER_HEADERS)
    if reset["branding"]["font_family_key"] != "inter" or reset["branding"]["color_palette_key"] != "aero_blue":
        raise AssertionError("Theme reset did not restore defaults.")

    readiness = get("/api/readiness")
    if not readiness.get("ok") or "agency_branding" not in readiness:
        raise AssertionError("Readiness does not expose optional branding summary.")
    if readiness["agency_branding"].get("readiness_required") is not False:
        raise AssertionError("Branding should not be required for readiness.")

    print("Agency branding settings smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Agency branding settings smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
