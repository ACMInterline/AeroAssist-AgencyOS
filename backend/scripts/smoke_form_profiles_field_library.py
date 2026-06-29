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
AGENCY_OWNER_HEADERS = {"X-Demo-User-Email": "agency.owner@aeroassist.dev"}
EXPECTED_PHASE = "phase_36_3_booking_pnr_foundation"


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


def main() -> int:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")

    post("/api/reference/seed", {}, OWNER_HEADERS)
    first = post("/api/form-profiles/field-definitions/bootstrap", {}, OWNER_HEADERS)["bootstrap"]
    second = post("/api/form-profiles/field-definitions/bootstrap", {}, OWNER_HEADERS)["bootstrap"]
    if first["inserted"] + first["updated"] <= 0 or second["updated"] <= 0:
        raise AssertionError("Global field bootstrap was not idempotent.")

    definitions = get("/api/form-profiles/field-definitions", OWNER_HEADERS)["items"]
    by_key = {item["field_key"]: item for item in definitions}
    for key in ["contact.email", "itinerary_segments.origin", "services.service_family", "internal.admin_notes"]:
        if key not in by_key:
            raise AssertionError(f"Missing global field definition: {key}")

    now = int(time.time())
    owner_field = post(
        "/api/form-profiles/field-definitions",
        {
            "field_key": f"smoke.owner_field.{now}",
            "canonical_path": f"agency_custom_fields.smoke_owner_{now}",
            "field_family": "internal_admin",
            "field_type": "text",
            "label": "Smoke Owner Field",
            "required_level": "internal_only",
            "public_safe": False,
            "portal_safe": False,
            "admin_safe": True,
        },
        OWNER_HEADERS,
        201,
    )["field"]
    updated = put(f"/api/form-profiles/field-definitions/{owner_field['id']}", {"label": "Smoke Owner Field Updated"}, OWNER_HEADERS)["field"]
    if updated["label"] != "Smoke Owner Field Updated":
        raise AssertionError("Platform owner could not update global field definition.")
    post(
        "/api/form-profiles/field-definitions",
        {
            "field_key": f"smoke.agency_forbidden.{now}",
            "canonical_path": "agency_custom_fields.nope",
            "field_family": "contact",
            "field_type": "text",
            "label": "Nope",
        },
        AGENCY_OWNER_HEADERS,
        403,
    )

    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    profiles = get(f"/api/agencies/{agency_id}/form-profiles", AGENCY_OWNER_HEADERS)["items"]
    if not any(item["form_context"] == "admin_request" for item in profiles):
        raise AssertionError("Default agency form profiles were not created.")

    profile = post(
        f"/api/agencies/{agency_id}/form-profiles",
        {
            "profile_key": f"smoke_public_{now}",
            "name": "Smoke Public Profile",
            "form_context": "public_request",
            "is_default": False,
        },
        AGENCY_OWNER_HEADERS,
        201,
    )["profile"]

    hidden_optional = put(
        f"/api/agencies/{agency_id}/form-profiles/{profile['id']}/fields",
        {"fields": [{"field_key": "itinerary_segments.notes", "visible": False, "enabled": True, "display_order": 260, "section_key": "itinerary_segment"}]},
        AGENCY_OWNER_HEADERS,
    )
    notes = [item for item in hidden_optional["effective"]["fields"] if item["field_key"] == "itinerary_segments.notes"][0]
    if notes["visible"] is not False:
        raise AssertionError("Optional field could not be hidden.")

    put(
        f"/api/agencies/{agency_id}/form-profiles/{profile['id']}/fields",
        {"fields": [{"field_key": "contact.email", "visible": False, "enabled": True, "display_order": 30, "section_key": "contact"}]},
        AGENCY_OWNER_HEADERS,
        400,
    )
    put(
        f"/api/agencies/{agency_id}/form-profiles/{profile['id']}/fields",
        {"fields": [{"field_key": "internal.admin_notes", "visible": True, "enabled": True, "display_order": 1000, "section_key": "internal_admin"}]},
        AGENCY_OWNER_HEADERS,
        400,
    )

    custom_key = f"custom.smoke_question_{now}"
    custom_result = put(
        f"/api/agencies/{agency_id}/form-profiles/{profile['id']}/fields",
        {
            "fields": [
                {"field_key": "itinerary_segments.notes", "visible": False, "enabled": True, "display_order": 260, "section_key": "itinerary_segment"},
                {"field_key": custom_key, "visible": True, "enabled": True, "required_override": True, "label_override": "Smoke custom question", "display_order": 1200, "section_key": "agency_custom", "custom_field": True, "custom_field_schema_json": {"field_type": "text", "label": "Smoke custom question"}},
            ]
        },
        AGENCY_OWNER_HEADERS,
    )
    custom_fields = [item for item in custom_result["effective"]["fields"] if item.get("custom_field")]
    if not custom_fields or custom_fields[0]["canonical_path"] != f"agency_custom_fields.{custom_key}":
        raise AssertionError("Custom agency field was not accepted into effective profile.")

    effective = get(f"/api/agencies/{agency_id}/form-profiles/{profile['id']}/effective", AGENCY_OWNER_HEADERS)
    if any(item["field_key"] == "internal.admin_notes" and item["visible"] for item in effective["fields"]):
        raise AssertionError("Internal-only field leaked into public effective profile.")

    fallback = get(f"/api/public/form-profiles/effective?agency_id={agency_id}&form_context=portal_request")
    if "fields" not in fallback:
        raise AssertionError("Public effective profile fallback response is malformed.")

    readiness = get("/api/readiness")
    form_profiles = readiness.get("form_profiles") or {}
    for flag in ["global_field_library_enabled", "agency_form_profiles_enabled", "agency_field_menu_enabled"]:
        if form_profiles.get(flag) is not True:
            raise AssertionError(f"Readiness missing form profile flag: {flag}")
    if form_profiles.get("global_field_definition_count", 0) < 20:
        raise AssertionError("Readiness global field definition count is too low.")

    print("Form profiles field library smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Form profiles field library smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
