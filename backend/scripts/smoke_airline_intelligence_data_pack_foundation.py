#!/usr/bin/env python3
from uuid import uuid4

from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, request


EXPECTED_PHASE = "phase_39_2_airline_intelligence_knowledge_versioning_foundation"


def patch(path: str, body: dict | None = None, headers: dict | None = None, expect: int | None = None) -> dict:
    return request("PATCH", path, body or {}, headers, expect)[1]


def require_flag(section: dict, key: str, expected: object = True) -> None:
    if section.get(key) is not expected:
        raise AssertionError(f"Readiness flag {key} expected {expected!r}, got {section.get(key)!r}")


def ids(items: list[dict]) -> set[str]:
    return {item["id"] for item in items}


def main() -> int:
    run_key = uuid4().hex[:10]
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")

    openapi = get("/openapi.json")
    paths = openapi.get("paths") or {}
    for path in paths:
        if path.startswith("/agent") or path.startswith("/admin") or path.startswith("/api/agent") or path.startswith("/api/admin"):
            raise AssertionError(f"Non-canonical route introduced: {path}")
        normalized_path = path.rstrip("/")
        if "airline-intelligence-data-packs" in path and (
            normalized_path.endswith("/ai")
            or any(
                token in path
                for token in [
                    "/scrape",
                    "/external",
                    "/ai/",
                    "/promote",
                    "/recommend",
                    "/execute",
                    "/book",
                    "/pnr",
                    "/ticket",
                    "/emd",
                    "/pay",
                    "/invoice",
                    "/settle",
                    "/send",
                    "/publish",
                    "public-link",
                ]
            )
        ):
            raise AssertionError(f"Airline data pack execution route introduced: {path}")

    for path, method in [
        ("/api/platform/airline-intelligence-data-packs/summary", "get"),
        ("/api/platform/airline-intelligence-data-packs/packs", "get"),
        ("/api/platform/airline-intelligence-data-packs/packs", "post"),
        ("/api/platform/airline-intelligence-data-packs/packs/{pack_id}", "get"),
        ("/api/platform/airline-intelligence-data-packs/packs/{pack_id}", "patch"),
        ("/api/platform/airline-intelligence-data-packs/packs/{pack_id}/items", "get"),
        ("/api/platform/airline-intelligence-data-packs/packs/{pack_id}/items", "post"),
        ("/api/platform/airline-intelligence-data-packs/items/{item_id}", "patch"),
        ("/api/platform/airline-intelligence-data-packs/packs/{pack_id}/validate", "post"),
        ("/api/platform/airline-intelligence-data-packs/packs/{pack_id}/dry-run-json", "post"),
        ("/api/platform/airline-intelligence-data-packs/packs/{pack_id}/dry-run-csv", "post"),
        ("/api/platform/airline-intelligence-data-packs/packs/{pack_id}/validation-issues", "get"),
        ("/api/platform/airline-intelligence-data-packs/validation-issues/{issue_id}/acknowledge", "patch"),
        ("/api/platform/airline-intelligence-data-packs/packs/{pack_id}/review-notes", "get"),
        ("/api/platform/airline-intelligence-data-packs/packs/{pack_id}/review-notes", "post"),
        ("/api/platform/airline-intelligence-data-packs/coverage-snapshots", "post"),
        ("/api/platform/airline-intelligence-data-packs/coverage-snapshots", "get"),
        ("/api/agencies/{agency_id}/airline-intelligence-data-packs/summary", "get"),
        ("/api/agencies/{agency_id}/airline-intelligence-data-packs/coverage", "get"),
        ("/api/agencies/{agency_id}/airline-intelligence-data-packs/packs", "get"),
        ("/api/agencies/{agency_id}/airline-intelligence-data-packs/packs/{pack_id}", "get"),
        ("/api/agencies/{agency_id}/airline-intelligence-data-packs/packs/{pack_id}/items", "get"),
    ]:
        assert_openapi_path(paths, path, method)

    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("airline_intelligence_data_pack_foundation") or {}
    for key in [
        "data_packs_enabled",
        "data_pack_items_enabled",
        "data_pack_validation_enabled",
        "data_pack_dry_runs_enabled",
        "data_pack_review_notes_enabled",
        "coverage_snapshots_enabled",
        "platform_data_pack_ui_enabled",
        "agency_coverage_ui_enabled",
        "agency_read_only_consumption_enabled",
        "crm_alignment_metadata_enabled",
        "cms_alignment_metadata_enabled",
        "client_portal_alignment_metadata_enabled",
        "offer_builder_alignment_metadata_enabled",
        "metadata_only_staging_enabled",
        "automatic_promotion_disabled",
        "scraping_disabled",
        "external_ai_disabled",
        "external_api_calls_disabled",
        "provider_execution_disabled",
        "booking_execution_disabled",
        "pnr_mutation_disabled",
        "ticketing_disabled",
        "emd_issuance_disabled",
        "payment_invoice_settlement_disabled",
        "public_client_portal_disabled",
        "public_cms_publishing_disabled",
        "automatic_sending_disabled",
    ]:
        require_flag(section, key)
    for key in [
        "data_pack_count",
        "data_pack_item_count",
        "validation_issue_count",
        "import_run_count",
        "review_note_count",
        "coverage_snapshot_count",
        "packs_needing_review_count",
        "approved_pack_count",
        "demo_pack_count",
        "agency_display_safe_pack_count",
        "cms_display_safe_pack_count",
        "client_portal_safe_pack_count",
        "offer_builder_safe_pack_count",
    ]:
        if key not in section:
            raise AssertionError(f"Readiness missing airline data pack count {key}")

    platform_base = "/api/platform/airline-intelligence-data-packs"
    pack_response = post(
        f"{platform_base}/packs",
        {
            "name": f"Smoke airline data pack {run_key}",
            "slug": f"smoke-airline-data-pack-{run_key}",
            "description": "Demo/sample airline data pack for smoke validation.",
            "pack_type": "starter_pack",
            "airline_codes": [f"Z{run_key[0].upper()}"],
            "source_type": "demo_sample",
            "source_reference": f"Smoke demo source {run_key}",
            "version_label": "smoke-v1",
            "is_demo_data": True,
            "is_operationally_verified": False,
            "safe_for_agency_internal_crm": False,
            "safe_for_agency_display": False,
            "safe_for_cms_display": False,
            "safe_for_client_portal_later": False,
            "safe_for_offer_builder": False,
            "verification_status": "needs_review",
            "confidence_score": 0.42,
            "human_summary": "Demo/sample airline data staged for platform review only.",
            "operator_guidance": "Needs verification before any agency-facing use.",
        },
        OWNER_HEADERS,
        201,
    )
    pack = pack_response["pack"]
    if pack.get("is_demo_data") is not True or pack.get("is_operationally_verified") is not False:
        raise AssertionError(f"Smoke pack demo/verification flags wrong: {pack}")
    for key in ["automatic_promotion_disabled", "external_ai_disabled", "scraping_disabled", "external_api_calls_disabled"]:
        if pack_response.get(key) is not True:
            raise AssertionError(f"Platform pack response missing safety flag {key}: {pack_response}")

    item_response = post(
        f"{platform_base}/packs/{pack['id']}/items",
        {
            "airline_iata_code": "ZZ",
            "target_domain": "airline_profile",
            "display_name": "Smoke sample airline profile",
            "plain_language_summary": "Demo profile coverage staged for review only.",
            "proposed_action": "review_only",
            "payload": {"airline_name": "Smoke Sample Air", "country": "Demo"},
            "source_reference": f"Smoke item source {run_key}",
            "is_demo_data": True,
            "is_operationally_verified": False,
            "safe_for_agency_internal_crm": False,
            "safe_for_agency_display": False,
            "safe_for_cms_display": False,
            "safe_for_client_portal_later": False,
            "safe_for_offer_builder": False,
        },
        OWNER_HEADERS,
        201,
    )
    item = item_response["item"]
    if item.get("pack_id") != pack["id"] or item.get("payload", {}).get("airline_name") != "Smoke Sample Air":
        raise AssertionError(f"Data pack item not staged correctly: {item}")

    bad_item = post(
        f"{platform_base}/packs/{pack['id']}/items",
        {
            "display_name": "Smoke missing airline code",
            "plain_language_summary": "",
            "proposed_action": "review_only",
            "payload": {},
            "is_demo_data": True,
            "is_operationally_verified": False,
        },
        OWNER_HEADERS,
        201,
    )["item"]

    validation = post(f"{platform_base}/packs/{pack['id']}/validate", {}, OWNER_HEADERS)
    if bad_item["id"] not in {issue.get("item_id") for issue in validation.get("issues", []) if issue.get("severity") == "error"}:
        raise AssertionError(f"Validation did not flag bad staged item: {validation}")
    if "Needs verification" not in validation.get("plain_language_summary", ""):
        raise AssertionError(f"Validation summary was not plain-language: {validation}")

    json_run = post(
        f"{platform_base}/packs/{pack['id']}/dry-run-json",
        {
            "inline_json": '[{"airline_iata_code":"ZZ","target_domain":"routes","display_name":"Smoke route coverage","plain_language_summary":"Demo route coverage for review only.","source_reference":"Smoke JSON","payload":{"routes":["ZZ100"]},"is_demo_data":true,"is_operationally_verified":false}]'
        },
        OWNER_HEADERS,
        201,
    )
    if json_run.get("import_run", {}).get("source_format") != "json" or not json_run.get("items"):
        raise AssertionError(f"JSON dry run did not stage items: {json_run}")

    csv_run = post(
        f"{platform_base}/packs/{pack['id']}/dry-run-csv",
        {
            "inline_csv": "airline_iata_code,target_domain,display_name,plain_language_summary,source_reference,is_demo_data,is_operationally_verified\nZZ,fare_families,Smoke fare family,Demo fare family coverage,Smoke CSV,true,false"
        },
        OWNER_HEADERS,
        201,
    )
    if csv_run.get("import_run", {}).get("source_format") != "csv" or not csv_run.get("items"):
        raise AssertionError(f"CSV dry run did not stage items: {csv_run}")

    issues = get(f"{platform_base}/packs/{pack['id']}/validation-issues", OWNER_HEADERS)["items"]
    if not issues:
        raise AssertionError("Validation issues endpoint did not return issues.")
    acknowledged = patch(
        f"{platform_base}/validation-issues/{issues[0]['id']}/acknowledge",
        {"status": "acknowledged", "resolved_by": "smoke"},
        OWNER_HEADERS,
    )["issue"]
    if acknowledged.get("status") != "acknowledged":
        raise AssertionError(f"Validation issue acknowledgement failed: {acknowledged}")

    note = post(
        f"{platform_base}/packs/{pack['id']}/review-notes",
        {"note_type": "verification", "note": f"Smoke review note {run_key}"},
        OWNER_HEADERS,
        201,
    )["review_note"]
    if note.get("note_type") != "verification":
        raise AssertionError(f"Review note creation failed: {note}")

    snapshot = post(
        f"{platform_base}/coverage-snapshots",
        {"snapshot_label": f"Smoke coverage {run_key}"},
        OWNER_HEADERS,
        201,
    )["coverage_snapshot"]
    if snapshot.get("airlines_with_profiles", 0) < 1:
        raise AssertionError(f"Coverage snapshot did not include staged profile coverage: {snapshot}")

    platform_summary = get(f"{platform_base}/summary", OWNER_HEADERS)
    if platform_summary.get("data_pack_count", 0) < 1 or platform_summary.get("automatic_promotion_disabled") is not True:
        raise AssertionError(f"Platform summary missing data pack/safety state: {platform_summary}")
    if pack["id"] not in ids(get(f"{platform_base}/packs", OWNER_HEADERS)["items"]):
        raise AssertionError("Platform pack list did not include created pack.")
    detail = get(f"{platform_base}/packs/{pack['id']}", OWNER_HEADERS)
    if item["id"] not in ids(detail.get("items", [])):
        raise AssertionError("Platform pack detail did not include staged item.")

    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    agency_base = f"/api/agencies/{agency_id}/airline-intelligence-data-packs"
    agency_summary = get(f"{agency_base}/summary", OWNER_HEADERS)
    if agency_summary.get("read_only") is not True or agency_summary.get("agency_read_only_consumption_enabled") is not True:
        raise AssertionError(f"Agency data pack summary is not read-only: {agency_summary}")
    agency_coverage = get(f"{agency_base}/coverage", OWNER_HEADERS)
    if agency_coverage.get("read_only") is not True:
        raise AssertionError(f"Agency coverage endpoint is not read-only: {agency_coverage}")
    agency_packs = get(f"{agency_base}/packs", OWNER_HEADERS)["items"]
    if pack["id"] not in ids(agency_packs):
        raise AssertionError("Agency read-only pack list did not include created pack.")
    agency_detail = get(f"{agency_base}/packs/{pack['id']}", OWNER_HEADERS)
    if agency_detail.get("payloads_hidden") is not True:
        raise AssertionError(f"Agency pack detail did not hide payloads: {agency_detail}")
    agency_items = get(f"{agency_base}/packs/{pack['id']}/items", OWNER_HEADERS)["items"]
    if not agency_items or any("payload" in agency_item or "normalized_payload" in agency_item for agency_item in agency_items):
        raise AssertionError(f"Agency read-only items exposed raw payloads: {agency_items}")
    request("POST", f"{agency_base}/packs", {"name": "Agency mutation blocked"}, OWNER_HEADERS, 405)
    request("PATCH", f"{agency_base}/packs/{pack['id']}", {"verification_status": "approved"}, OWNER_HEADERS, 405)

    readiness_after = get("/api/readiness")
    section_after = readiness_after.get("airline_intelligence_data_pack_foundation") or {}
    for key in ["data_pack_count", "data_pack_item_count", "import_run_count", "review_note_count", "coverage_snapshot_count"]:
        if section_after.get(key, 0) < 1:
            raise AssertionError(f"Readiness data pack count did not increment for {key}: {section_after}")

    print("Airline intelligence data pack foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
