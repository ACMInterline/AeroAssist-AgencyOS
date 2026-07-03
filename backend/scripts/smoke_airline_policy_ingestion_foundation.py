#!/usr/bin/env python3
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post


EXPECTED_PHASE = "phase_39_1_airline_intelligence_data_pack_review_foundation"


SAMPLE_POLICY_TEXT = """General:
UMNR / Kids Solo applies to children aged 5 to 14 years. Young passengers aged 15 to 17 may request assistance.

How to book:
Request SSR UMNR at least 24 hours before departure. Use GDS entry SSR UMNR AF HK1 CHILD AGE 10. OSI AF GUARDIAN CONTACT REQUIRED. NDC not available for this service.

Pricing:
Mandatory UMNR service fee EUR 75 per passenger per direction on direct flights. Connecting itineraries may be EUR 150 and require manual review.

EMD / payment:
EMD is required. Use EMD-A where available. RFIC E / RFISC 0B5 may apply. ICW ticket is required. Non-refundable after departure.

Exceptions:
No overnight connection or airport change is permitted. Train or bus segments are forbidden. Partner airline operated flights require manual review.

Changes/refunds:
Changes require airline confirmation and any refund must be manually reviewed.
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
        ("/api/platform/airline-policy/sources", "get"),
        ("/api/platform/airline-policy/sources", "post"),
        ("/api/platform/airline-policy/sources/{policy_source_id}", "get"),
        ("/api/platform/airline-policy/sources/{policy_source_id}/detect-sections", "post"),
        ("/api/platform/airline-policy/sources/{policy_source_id}/extract", "post"),
        ("/api/platform/airline-policy/sources/{policy_source_id}/candidates", "get"),
        ("/api/platform/airline-policy/extraction-runs", "get"),
        ("/api/platform/airline-policy/extraction-runs/{extraction_run_id}", "get"),
        ("/api/platform/airline-policy/review-corrections", "post"),
        ("/api/platform/airline-policy/promote-candidate", "post"),
        ("/api/platform/airline-policy/sources/{policy_source_id}/promote-accepted", "post"),
        ("/api/platform/airline-policy/approved-knowledge", "get"),
        ("/api/agencies/{agency_id}/airline-policy/library", "get"),
        ("/api/agencies/{agency_id}/airline-policy/sources", "get"),
        ("/api/agencies/{agency_id}/airline-policy/sources", "post"),
        ("/api/agencies/{agency_id}/airline-policy/sources/{policy_source_id}", "get"),
        ("/api/agencies/{agency_id}/airline-policy/sources/{policy_source_id}/detect-sections", "post"),
        ("/api/agencies/{agency_id}/airline-policy/sources/{policy_source_id}/extract", "post"),
        ("/api/agencies/{agency_id}/airline-policy/sources/{policy_source_id}/candidates", "get"),
        ("/api/agencies/{agency_id}/airline-policy/review-corrections", "post"),
        ("/api/agencies/{agency_id}/airline-policy/sources/{policy_source_id}/submit-for-platform-review", "post"),
    ]:
        assert_openapi_path(paths, path, method)

    readiness = get("/api/readiness")
    policy_foundation = readiness.get("airline_policy_ingestion_foundation") or {}
    for key in [
        "policy_source_foundation_enabled",
        "policy_section_detection_enabled",
        "policy_extraction_run_enabled",
        "extracted_rule_candidates_enabled",
        "extracted_price_candidates_enabled",
        "extracted_communication_candidates_enabled",
        "extracted_emd_rule_candidates_enabled",
        "extracted_exception_candidates_enabled",
        "review_correction_foundation_enabled",
        "approved_knowledge_foundation_enabled",
        "platform_policy_ingestion_ui_enabled",
        "agency_policy_library_ui_enabled",
        "document_policy_summary_context_enabled",
        "deterministic_extraction_enabled",
        "external_ai_policy_extraction_disabled",
        "auto_promotion_disabled",
        "platform_review_required_for_global_knowledge",
    ]:
        require_flag(policy_foundation, key)
    require_flag(policy_foundation, "readiness_required", False)
    for count_key in [
        "policy_source_count",
        "policy_section_count",
        "policy_extraction_run_count",
        "extracted_rule_candidate_count",
        "extracted_price_candidate_count",
        "extracted_communication_candidate_count",
        "extracted_emd_rule_candidate_count",
        "extracted_exception_candidate_count",
        "policy_review_correction_count",
        "approved_knowledge_record_count",
        "pending_policy_source_count",
        "approved_policy_source_count",
        "rejected_policy_source_count",
    ]:
        if count_key not in policy_foundation:
            raise AssertionError(f"Readiness missing policy count {count_key}")

    created = post(
        "/api/platform/airline-policy/sources",
        {
            "airline_iata_code": "AF",
            "airline_name_snapshot": "Air France",
            "service_domain": "special_services",
            "service_family": "unaccompanied_minor",
            "source_type": "pasted_text",
            "source_title": "Smoke UMNR policy",
            "raw_text": SAMPLE_POLICY_TEXT,
            "language": "en",
        },
        OWNER_HEADERS,
        201,
    )
    platform_source = created.get("policy_source") or {}
    if not platform_source.get("id") or platform_source.get("scope") != "platform":
        raise AssertionError(f"Platform policy source was not created: {created}")
    if created.get("external_ai_policy_extraction_disabled") is not True or created.get("auto_promotion_disabled") is not True:
        raise AssertionError("Policy source creation changed extraction/promotion safeguards.")

    sections = post(f"/api/platform/airline-policy/sources/{platform_source['id']}/detect-sections", {}, OWNER_HEADERS)
    if sections.get("created_count", 0) < 4:
        raise AssertionError(f"Section detection did not create representative sections: {sections}")

    extracted = post(
        f"/api/platform/airline-policy/sources/{platform_source['id']}/extract",
        {"service_domain": "special_services", "service_family": "unaccompanied_minor"},
        OWNER_HEADERS,
        201,
    )
    run = extracted.get("extraction_run") or {}
    candidates = extracted.get("candidates") or {}
    if run.get("extraction_status") not in {"extracted", "partial", "manual_review_required"}:
        raise AssertionError(f"Unexpected extraction status: {run}")
    if not candidates.get("rules") or not candidates.get("prices") or not candidates.get("communication_rules") or not candidates.get("emd_rules") or not candidates.get("exceptions"):
        raise AssertionError(f"Extraction did not create all candidate groups: {candidates}")
    if extracted.get("external_ai_policy_extraction_disabled") is not True or extracted.get("auto_promotion_disabled") is not True:
        raise AssertionError("Policy extraction changed disabled AI/auto-promotion safeguards.")

    listed_candidates = get(f"/api/platform/airline-policy/sources/{platform_source['id']}/candidates", OWNER_HEADERS)
    first_rule = (listed_candidates.get("rules") or [])[0]
    correction = post(
        "/api/platform/airline-policy/review-corrections",
        {
            "policy_source_id": platform_source["id"],
            "extraction_run_id": run["id"],
            "target_type": "rule",
            "target_id": first_rule["id"],
            "correction_type": "accept",
            "before_json": first_rule.get("normalized_action_json") or {},
            "after_json": first_rule.get("normalized_action_json") or {},
            "correction_reason": "Smoke review accepted deterministic candidate.",
        },
        OWNER_HEADERS,
        201,
    )
    if not correction.get("correction") or correction.get("auto_promotion_disabled") is not True:
        raise AssertionError("Review correction was not recorded with safeguards.")

    promoted = post(
        "/api/platform/airline-policy/promote-candidate",
        {
            "policy_source_id": platform_source["id"],
            "extraction_run_id": run["id"],
            "target_type": "rule",
            "target_id": first_rule["id"],
            "knowledge_type": "applicability_rule",
        },
        OWNER_HEADERS,
        201,
    )
    if not promoted.get("approved_knowledge") or promoted.get("auto_promotion_disabled") is not True:
        raise AssertionError(f"Accepted candidate was not explicitly promoted: {promoted}")
    approved = get("/api/platform/airline-policy/approved-knowledge", OWNER_HEADERS).get("items") or []
    if not any(item.get("id") == promoted["approved_knowledge"]["id"] for item in approved):
        raise AssertionError("Approved knowledge list did not include promoted record.")

    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    library_before = get(f"/api/agencies/{agency_id}/airline-policy/library", OWNER_HEADERS)
    if not library_before.get("platform_knowledge_read_only") or not library_before.get("approved_knowledge"):
        raise AssertionError("Agency policy library did not expose read-only approved platform knowledge.")

    agency_created = post(
        f"/api/agencies/{agency_id}/airline-policy/sources",
        {
            "airline_iata_code": "KL",
            "airline_name_snapshot": "KLM",
            "service_domain": "special_services",
            "service_family": "unaccompanied_minor",
            "source_title": "Agency local UMNR note",
            "source_type": "pasted_text",
            "raw_text": SAMPLE_POLICY_TEXT.replace("AF", "KL"),
        },
        OWNER_HEADERS,
        201,
    )["policy_source"]
    if agency_created.get("scope") != "agency" or agency_created.get("agency_id") != agency_id:
        raise AssertionError("Agency local policy source did not preserve agency scope.")
    agency_extract = post(
        f"/api/agencies/{agency_id}/airline-policy/sources/{agency_created['id']}/extract",
        {"service_domain": "special_services", "service_family": "unaccompanied_minor"},
        OWNER_HEADERS,
        201,
    )
    agency_run = agency_extract.get("extraction_run") or {}
    if not agency_run.get("id") or not agency_extract.get("candidates", {}).get("rules"):
        raise AssertionError("Agency local policy extraction did not create candidates.")
    approved_count_before_submit = len(get("/api/platform/airline-policy/approved-knowledge", OWNER_HEADERS).get("items") or [])
    submitted = post(
        f"/api/agencies/{agency_id}/airline-policy/sources/{agency_created['id']}/submit-for-platform-review",
        {},
        OWNER_HEADERS,
    )
    approved_count_after_submit = len(get("/api/platform/airline-policy/approved-knowledge", OWNER_HEADERS).get("items") or [])
    if submitted.get("global_knowledge_created") is not False or approved_count_after_submit != approved_count_before_submit:
        raise AssertionError("Agency submit-for-review created global knowledge automatically.")

    document_context = post(
        f"/api/agencies/{agency_id}/documents/context-preview",
        {"source_context_type": "airline_policy_extraction_run", "source_context_id": agency_run["id"]},
        OWNER_HEADERS,
    )["context"]
    if document_context.get("policy_extraction_summary", {}).get("id") != agency_run["id"]:
        raise AssertionError("Document context did not include policy extraction summary.")
    if not document_context.get("policy_candidates", {}).get("rules"):
        raise AssertionError("Document context did not include policy candidates.")

    readiness_after = get("/api/readiness").get("airline_policy_ingestion_foundation") or {}
    if readiness_after.get("policy_source_count", 0) < 2 or readiness_after.get("approved_knowledge_record_count", 0) < 1:
        raise AssertionError("Policy readiness counts did not update after smoke workflow.")
    for key in ["external_ai_policy_extraction_disabled", "auto_promotion_disabled", "platform_review_required_for_global_knowledge"]:
        require_flag(readiness_after, key)

    print("Airline policy ingestion foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
