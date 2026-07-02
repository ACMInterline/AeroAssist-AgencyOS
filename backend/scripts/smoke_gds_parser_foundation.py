#!/usr/bin/env python3
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post


EXPECTED_PHASE = "phase_36_9_service_mechanics_mapping_foundation"


RAW_GDS_TEXT = """RP/SOF1A0980/SOF1A0980 AA/SU 30JUN26/0915Z ABC123
PNR ABC123
1.SMOKE/TRAVELER MR
2 LH1703 Y 13DEC SOFFRA HK1 0600 0725
SSR WCHR LH HK1 SOF FRA /WHEELCHAIR
OSI LH VIP CLIENT
TK 2201234567890
EMD 2209876543210
FARE BASIS YSMOKE
TOTAL EUR 152.00
"""


def require_flag(section: dict, key: str, expected: object = True) -> None:
    if section.get(key) is not expected:
        raise AssertionError(f"Readiness flag {key} expected {expected!r}, got {section.get(key)!r}")


def main() -> int:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")

    openapi = get("/openapi.json")
    paths = openapi.get("paths") or {}
    for path, method in [
        ("/api/agencies/{agency_id}/gds-parser/profiles", "get"),
        ("/api/agencies/{agency_id}/gds-parser/runs", "get"),
        ("/api/agencies/{agency_id}/gds-parser/parse-text", "post"),
        ("/api/agencies/{agency_id}/gds-parser/booking-import-drafts/{draft_id}/parse", "post"),
        ("/api/agencies/{agency_id}/gds-parser/runs/{parser_run_id}", "get"),
        ("/api/agencies/{agency_id}/gds-parser/runs/{parser_run_id}/entities", "get"),
        ("/api/agencies/{agency_id}/gds-parser/corrections", "post"),
        ("/api/agencies/{agency_id}/gds-parser/runs/{parser_run_id}/training-sample", "post"),
        ("/api/platform/gds-parser/profiles", "get"),
        ("/api/platform/gds-parser/profiles/seed-defaults", "post"),
        ("/api/platform/gds-parser/profiles/{profile_id}/versions", "get"),
        ("/api/platform/gds-parser/profiles/{profile_id}/versions", "post"),
        ("/api/platform/gds-parser/profiles/{profile_id}/versions/{version_id}/activate", "post"),
        ("/api/platform/gds-parser/training-samples", "get"),
        ("/api/platform/gds-parser/training-samples/{sample_id}/review", "post"),
        ("/api/platform/gds-parser/evaluations", "post"),
        ("/api/platform/gds-parser/evaluations", "get"),
    ]:
        assert_openapi_path(paths, path, method)

    readiness = get("/api/readiness")
    parser_foundation = readiness.get("gds_parser_foundation") or {}
    for key in [
        "parser_profile_foundation_enabled",
        "parser_version_foundation_enabled",
        "parser_run_foundation_enabled",
        "parsed_entity_foundation_enabled",
        "parse_correction_foundation_enabled",
        "training_sample_foundation_enabled",
        "parser_evaluation_foundation_enabled",
        "agency_gds_parser_ui_enabled",
        "platform_gds_parser_governance_ui_enabled",
        "booking_import_parser_integration_enabled",
        "parser_document_context_enabled",
        "conservative_parser_rules_enabled",
        "manual_review_required_for_low_confidence",
        "explicit_import_required",
        "live_gds_connection_disabled",
        "live_provider_execution_disabled",
        "external_ai_parser_disabled",
    ]:
        require_flag(parser_foundation, key)
    for key in [
        "parser_profile_count",
        "parser_version_count",
        "parser_run_count",
        "parsed_entity_count",
        "parse_correction_count",
        "training_sample_count",
        "parser_evaluation_run_count",
        "low_confidence_parser_run_count",
        "approved_training_sample_count",
    ]:
        if key not in parser_foundation:
            raise AssertionError(f"Readiness missing parser count {key}")
    require_flag(parser_foundation, "readiness_required", False)

    seeded = post("/api/platform/gds-parser/profiles/seed-defaults", {}, OWNER_HEADERS, 201)
    if seeded.get("live_gds_connection_disabled") is not True or seeded.get("external_ai_parser_disabled") is not True:
        raise AssertionError("Parser seed endpoint changed disabled integration flags.")
    profiles = get("/api/platform/gds-parser/profiles", OWNER_HEADERS)["items"]
    if len(profiles) < 4:
        raise AssertionError("Default parser profiles were not seeded.")
    profile = profiles[0]
    versions = get(f"/api/platform/gds-parser/profiles/{profile['id']}/versions", OWNER_HEADERS)["items"]
    if not versions:
        raise AssertionError("Default parser profile did not include a version.")

    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    agency_profiles = get(f"/api/agencies/{agency_id}/gds-parser/profiles", OWNER_HEADERS)["items"]
    if not agency_profiles:
        raise AssertionError("Agency parser profiles endpoint returned no profiles.")

    parse_result = post(
        f"/api/agencies/{agency_id}/gds-parser/parse-text",
        {"raw_text": RAW_GDS_TEXT},
        OWNER_HEADERS,
        201,
    )
    run = parse_result.get("parser_run") or {}
    entities = parse_result.get("entities") or []
    preview = parse_result.get("normalized_preview") or {}
    if not run.get("id") or run.get("parse_status") not in {"parsed", "partial"}:
        raise AssertionError(f"Parser run was not stored as parsed/partial: {run}")
    if not entities:
        raise AssertionError("Parser entities were not stored.")
    for key in ["passengers", "segments", "ssr", "osi", "ticket_numbers", "emd_numbers", "pricing"]:
        if key not in preview:
            raise AssertionError(f"Normalized preview missing {key}")
    if preview.get("record_locator") != "ABC123":
        raise AssertionError(f"Parser did not extract expected locator: {preview}")

    stored_run = get(f"/api/agencies/{agency_id}/gds-parser/runs/{run['id']}", OWNER_HEADERS)["parser_run"]
    stored_entities = get(f"/api/agencies/{agency_id}/gds-parser/runs/{run['id']}/entities", OWNER_HEADERS)["items"]
    if stored_run.get("id") != run["id"] or not stored_entities:
        raise AssertionError("Stored parser run/entities were not readable.")

    low_confidence = post(
        f"/api/agencies/{agency_id}/gds-parser/parse-text",
        {"raw_text": "UNSTRUCTURED NOTE ONLY"},
        OWNER_HEADERS,
        201,
    )["parser_run"]
    if low_confidence.get("parse_status") != "manual_review_required" or not low_confidence.get("warnings_json"):
        raise AssertionError("Ambiguous input did not return manual review warnings.")

    draft = post(
        f"/api/agencies/{agency_id}/booking-import-drafts",
        {"source_type": "cryptic_gds", "raw_text": RAW_GDS_TEXT, "import_context": "new_booking"},
        OWNER_HEADERS,
        201,
    )["draft"]
    parsed_draft = post(
        f"/api/agencies/{agency_id}/gds-parser/booking-import-drafts/{draft['id']}/parse",
        {},
        OWNER_HEADERS,
    )["draft"]
    if not parsed_draft.get("latest_parser_run_id") or not parsed_draft.get("normalized_preview_json", {}).get("segments"):
        raise AssertionError("Booking import draft was not linked to a parser run/preview.")

    correction = post(
        f"/api/agencies/{agency_id}/gds-parser/corrections",
        {
            "parser_run_id": run["id"],
            "parsed_entity_id": stored_entities[0]["id"],
            "correction_type": "accept",
            "entity_type": stored_entities[0]["entity_type"],
            "before_json": stored_entities[0].get("normalized_json") or {},
            "after_json": stored_entities[0].get("normalized_json") or {},
        },
        OWNER_HEADERS,
        201,
    )
    if not correction.get("correction"):
        raise AssertionError("Parser correction was not recorded.")

    sample = post(
        f"/api/agencies/{agency_id}/gds-parser/runs/{run['id']}/training-sample",
        {"sample_title": "Smoke GDS parser sample", "difficulty": "easy", "tags": ["smoke", "phase_36_6"]},
        OWNER_HEADERS,
        201,
    )["sample"]
    if sample.get("parser_run_id") != run["id"]:
        raise AssertionError("Training sample did not link to parser run.")
    reviewed = post(
        f"/api/platform/gds-parser/training-samples/{sample['id']}/review",
        {"sample_status": "approved", "review_notes": "Smoke approved sample."},
        OWNER_HEADERS,
    )["sample"]
    if reviewed.get("sample_status") != "approved":
        raise AssertionError("Training sample was not approved.")

    draft_version = post(
        f"/api/platform/gds-parser/profiles/{profile['id']}/versions",
        {
            "version_label": "v1.1-smoke",
            "rules_json": {"smoke": True, "external_services": False},
            "extraction_schema_json": {"entities": ["passenger", "segment", "ticket", "emd"]},
            "known_limitations_json": [{"code": "smoke_version", "message": "Smoke test draft version."}],
            "change_notes": "Smoke test draft version.",
        },
        OWNER_HEADERS,
        201,
    )["version"]
    activated = post(
        f"/api/platform/gds-parser/profiles/{profile['id']}/versions/{draft_version['id']}/activate",
        {},
        OWNER_HEADERS,
    )["version"]
    if activated.get("status") != "active":
        raise AssertionError("Parser version activation failed.")

    evaluation = post(
        "/api/platform/gds-parser/evaluations",
        {"parser_profile_id": profile["id"], "parser_version_id": draft_version["id"], "sample_ids": [sample["id"]]},
        OWNER_HEADERS,
        201,
    )["evaluation"]
    if evaluation.get("evaluation_status") != "completed" or evaluation.get("sample_count") != 1:
        raise AssertionError(f"Parser evaluation did not complete: {evaluation}")
    if not get("/api/platform/gds-parser/evaluations", OWNER_HEADERS).get("items"):
        raise AssertionError("Parser evaluations list did not include evaluation records.")

    document_context = post(
        f"/api/agencies/{agency_id}/documents/context-preview",
        {"source_context_type": "gds_parser_run", "source_context_id": run["id"]},
        OWNER_HEADERS,
    )["context"]
    if document_context.get("parser_run_summary", {}).get("id") != run["id"]:
        raise AssertionError("Document context did not include parser run summary.")

    readiness_after = get("/api/readiness")
    parser_after = readiness_after.get("gds_parser_foundation") or {}
    if parser_after.get("parser_run_count", 0) < 2 or parser_after.get("training_sample_count", 0) < 1:
        raise AssertionError("Parser readiness counts did not update.")
    for key in ["explicit_import_required", "live_gds_connection_disabled", "live_provider_execution_disabled", "external_ai_parser_disabled"]:
        require_flag(parser_after, key)

    print("GDS parser foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
