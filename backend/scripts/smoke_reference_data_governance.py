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
EXPECTED_PHASE = "phase_37_2_offer_policy_advisor_integration_foundation"


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


def patch(path: str, body: dict | None = None, headers: dict | None = None, expect: int | None = None) -> dict:
    return request("PATCH", path, body or {}, headers, expect)[1]


def main() -> int:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")

    post("/api/reference/bootstrap", {}, OWNER_HEADERS)
    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    now = int(time.time())

    owner_code = f"governed_owner_{now}"
    owner_record = post("/api/reference/contact_channels", {"code": owner_code, "label": "Governed Owner Channel", "scope": "global"}, OWNER_HEADERS, 201)["record"]
    if owner_record["code"] != owner_code:
        raise AssertionError("Platform owner global create returned the wrong record.")

    post("/api/reference/contact_channels", {"code": f"agency_direct_{now}", "label": "Should Fail", "scope": "global"}, AGENCY_HEADERS, 403)

    suggestion_code = f"agency_suggested_{now}"
    suggestion = post(
        "/api/reference/suggestions",
        {
            "submitting_agency_id": agency_id,
            "domain": "contact_channels",
            "suggested_code": suggestion_code,
            "suggested_label": "Agency Suggested Channel",
            "suggestion_type": "new_record",
            "source_context": "manual_reference_page",
            "evidence_note": "Used by a real agency workflow.",
        },
        AGENCY_HEADERS,
        201,
    )["suggestion"]
    if suggestion["status"] != "pending_review":
        raise AssertionError("Suggestion was not created as pending_review.")

    approved = patch(f"/api/reference/suggestions/{suggestion['id']}/approve", {"reviewer_note": "Approved by smoke."}, OWNER_HEADERS)["record"]
    if approved["code"] != suggestion_code:
        raise AssertionError("Approved suggestion did not promote the expected global record.")
    if suggestion_code not in {item["code"] for item in get("/api/reference/contact_channels", OWNER_HEADERS)["items"]}:
        raise AssertionError("Approved suggestion is not available in active global lookup.")

    rejected_code = f"agency_rejected_{now}"
    rejected_suggestion = post(
        "/api/reference/suggestions",
        {
            "submitting_agency_id": agency_id,
            "domain": "contact_channels",
            "suggested_code": rejected_code,
            "suggested_label": "Rejected Channel",
            "suggestion_type": "new_record",
            "source_context": "manual_reference_page",
        },
        AGENCY_HEADERS,
        201,
    )["suggestion"]
    patch(f"/api/reference/suggestions/{rejected_suggestion['id']}/reject", {"reviewer_note": "Rejected by smoke."}, OWNER_HEADERS)
    if rejected_code in {item["code"] for item in get("/api/reference/contact_channels", OWNER_HEADERS)["items"]}:
        raise AssertionError("Rejected suggestion leaked into global lookup.")

    duplicate_csv = "\n".join(
        [
            "domain,code,label,description,aliases,sort_order,is_active,metadata_json",
            f"contact_channels,bulk_dup_{now},Bulk Duplicate One,,alias one,910,true,{{}}",
            f"contact_channels,bulk_dup_{now},Bulk Duplicate Two,,alias two,911,true,{{}}",
        ]
    )
    duplicate_batch = post("/api/reference/import-batches", {"scope": "global", "domain": "contact_channels", "filename": "duplicate.csv", "csv_text": duplicate_csv}, OWNER_HEADERS, 201)["batch"]
    if duplicate_batch["invalid_rows"] != 1 or "bulk_dup" not in json.dumps(duplicate_batch.get("error_report_json", {})):
        raise AssertionError("Duplicate import rows were not reported safely.")

    import_code = f"bulk_idempotent_{now}"
    clean_csv = "\n".join(
        [
            "domain,code,label,description,aliases,sort_order,is_active,metadata_json",
            f"contact_channels,{import_code},Bulk Idempotent,,bulk alias,920,true,{{}}",
        ]
    )
    first_batch = post("/api/reference/import-batches", {"scope": "global", "domain": "contact_channels", "filename": "clean.csv", "csv_text": clean_csv}, OWNER_HEADERS, 201)["batch"]
    second_batch = post("/api/reference/import-batches", {"scope": "global", "domain": "contact_channels", "filename": "clean.csv", "csv_text": clean_csv}, OWNER_HEADERS, 201)["batch"]
    if first_batch["inserted_count"] != 1 or second_batch["updated_count"] != 1:
        raise AssertionError("Repeated import was not idempotent.")

    inactive_code = f"inactive_governed_{now}"
    inactive = post("/api/reference/contact_channels", {"code": inactive_code, "label": "Inactive Governed", "scope": "global"}, OWNER_HEADERS, 201)["record"]
    patch(f"/api/reference/contact_channels/{inactive['id']}/deactivate", {}, OWNER_HEADERS)
    if inactive_code in {item["code"] for item in get("/api/reference/contact_channels", OWNER_HEADERS)["items"]}:
        raise AssertionError("Inactive reference record leaked into active lookup.")

    if not get("/api/reference/service-catalogue", OWNER_HEADERS)["items"]:
        raise AssertionError("Service catalogue is no longer accessible.")

    readiness = get("/api/readiness")
    reference_data = readiness.get("reference_data") or {}
    for flag in ["global_reference_governance_enabled", "reference_suggestion_queue_enabled", "reference_bulk_import_enabled"]:
        if reference_data.get(flag) is not True:
            raise AssertionError(f"Readiness missing governance flag: {flag}")
    if reference_data.get("reference_import_batch_count", 0) < 3:
        raise AssertionError("Readiness did not count import batches.")

    print("Reference data governance smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Reference data governance smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
