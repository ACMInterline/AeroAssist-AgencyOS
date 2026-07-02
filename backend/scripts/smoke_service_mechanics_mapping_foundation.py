#!/usr/bin/env python3
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, request


EXPECTED_PHASE = "phase_37_3_offer_builder_advisor_consumption_decision_pack_foundation"


def require_flag(section: dict, key: str, expected: object = True) -> None:
    if section.get(key) is not expected:
        raise AssertionError(f"Readiness flag {key} expected {expected!r}, got {section.get(key)!r}")


def require_count(section: dict, key: str) -> None:
    if key not in section:
        raise AssertionError(f"Readiness missing mechanics count {key}")


def main() -> int:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")

    openapi = get("/openapi.json")
    paths = openapi.get("paths") or {}
    for path in paths:
        if path.startswith("/agent") or path.startswith("/admin") or path.startswith("/api/agent") or path.startswith("/api/admin"):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    for path, method in [
        ("/api/platform/service-mechanics/summary", "get"),
        ("/api/platform/service-mechanics/lookup", "post"),
        ("/api/platform/service-mechanics/communication-rules", "get"),
        ("/api/platform/service-mechanics/communication-rules", "post"),
        ("/api/platform/service-mechanics/communication-rules/{record_id}", "patch"),
        ("/api/platform/service-mechanics/ssr-osi-templates", "get"),
        ("/api/platform/service-mechanics/ssr-osi-templates", "post"),
        ("/api/platform/service-mechanics/ssr-osi-templates/{record_id}", "patch"),
        ("/api/platform/service-mechanics/requirements", "get"),
        ("/api/platform/service-mechanics/requirements", "post"),
        ("/api/platform/service-mechanics/requirements/{record_id}", "patch"),
        ("/api/platform/service-mechanics/status-recognition-rules", "get"),
        ("/api/platform/service-mechanics/status-recognition-rules", "post"),
        ("/api/platform/service-mechanics/status-recognition-rules/{record_id}", "patch"),
        ("/api/platform/service-mechanics/rejection-patterns", "get"),
        ("/api/platform/service-mechanics/rejection-patterns", "post"),
        ("/api/platform/service-mechanics/rejection-patterns/{record_id}", "patch"),
        ("/api/platform/service-mechanics/payment-rules", "get"),
        ("/api/platform/service-mechanics/payment-rules", "post"),
        ("/api/platform/service-mechanics/payment-rules/{record_id}", "patch"),
        ("/api/platform/service-mechanics/emd-issuance-rules", "get"),
        ("/api/platform/service-mechanics/emd-issuance-rules", "post"),
        ("/api/platform/service-mechanics/emd-issuance-rules/{record_id}", "patch"),
        ("/api/platform/service-mechanics/rfic-rfisc-mappings", "get"),
        ("/api/platform/service-mechanics/rfic-rfisc-mappings", "post"),
        ("/api/platform/service-mechanics/rfic-rfisc-mappings/{record_id}", "patch"),
        ("/api/platform/service-mechanics/emd-interline-rules", "get"),
        ("/api/platform/service-mechanics/emd-interline-rules", "post"),
        ("/api/platform/service-mechanics/emd-interline-rules/{record_id}", "patch"),
        ("/api/platform/service-mechanics/emd-lifecycle-rules", "get"),
        ("/api/platform/service-mechanics/emd-lifecycle-rules", "post"),
        ("/api/platform/service-mechanics/emd-lifecycle-rules/{record_id}", "patch"),
        ("/api/platform/service-mechanics/candidate-mechanics-links", "get"),
        ("/api/platform/service-mechanics/candidate-mechanics-links", "post"),
        ("/api/platform/service-mechanics/candidate-mechanics-links/{record_id}", "patch"),
        ("/api/agencies/{agency_id}/service-mechanics/summary", "get"),
        ("/api/agencies/{agency_id}/service-mechanics/lookup", "post"),
        ("/api/agencies/{agency_id}/service-mechanics/communication-rules", "get"),
        ("/api/agencies/{agency_id}/service-mechanics/ssr-osi-templates", "get"),
        ("/api/agencies/{agency_id}/service-mechanics/requirements", "get"),
        ("/api/agencies/{agency_id}/service-mechanics/status-recognition-rules", "get"),
        ("/api/agencies/{agency_id}/service-mechanics/rejection-patterns", "get"),
        ("/api/agencies/{agency_id}/service-mechanics/payment-rules", "get"),
        ("/api/agencies/{agency_id}/service-mechanics/emd-issuance-rules", "get"),
        ("/api/agencies/{agency_id}/service-mechanics/rfic-rfisc-mappings", "get"),
        ("/api/agencies/{agency_id}/service-mechanics/emd-interline-rules", "get"),
        ("/api/agencies/{agency_id}/service-mechanics/emd-lifecycle-rules", "get"),
        ("/api/agencies/{agency_id}/service-mechanics/candidate-mechanics-links", "get"),
        ("/api/agencies/{agency_id}/service-mechanics/candidate-mechanics-links", "post"),
    ]:
        assert_openapi_path(paths, path, method)

    readiness = get("/api/readiness")
    mechanics = readiness.get("service_mechanics_mapping_foundation") or {}
    for key in [
        "communication_rules_enabled",
        "ssr_osi_templates_enabled",
        "ssr_osi_requirements_enabled",
        "ssr_status_recognition_enabled",
        "airline_rejection_patterns_enabled",
        "payment_rules_enabled",
        "emd_issuance_rules_enabled",
        "rfic_rfisc_mappings_enabled",
        "emd_interline_rules_enabled",
        "emd_lifecycle_rules_enabled",
        "candidate_mechanics_links_enabled",
        "platform_service_mechanics_ui_enabled",
        "agency_service_mechanics_ui_enabled",
        "deterministic_mechanics_lookup_enabled",
        "communication_payment_separation_enforced",
        "provider_execution_disabled",
        "emd_issuance_disabled",
        "agency_auto_promotion_disabled",
    ]:
        require_flag(mechanics, key)
    require_flag(mechanics, "readiness_required", False)
    for key in [
        "communication_rule_count",
        "ssr_osi_template_count",
        "ssr_osi_requirement_count",
        "status_recognition_rule_count",
        "rejection_pattern_count",
        "payment_rule_count",
        "emd_issuance_rule_count",
        "rfic_rfisc_mapping_count",
        "emd_interline_rule_count",
        "emd_lifecycle_rule_count",
        "candidate_mechanics_link_count",
    ]:
        require_count(mechanics, key)

    communication_rule = post(
        "/api/platform/service-mechanics/communication-rules",
        {
            "airline_code": "LH",
            "domain_code": "mobility",
            "family_code": "wheelchair",
            "variant_code": "wchr",
            "canonical_service_label": "Wheelchair assistance",
            "communication_channel": "gds",
            "gds_system": "amadeus",
            "request_method": "ssr",
            "ssr_code": "WCHR",
            "passenger_association_required": True,
            "segment_association_required": True,
            "airline_confirmation_required": True,
            "notes": "Smoke communication mechanics.",
        },
        OWNER_HEADERS,
        201,
    )["communication_rule"]
    updated_rule = request(
        "PATCH",
        f"/api/platform/service-mechanics/communication-rules/{communication_rule['id']}",
        {"review_status": "confirmed"},
        OWNER_HEADERS,
    )[1]["communication_rule"]
    if updated_rule.get("review_status") != "confirmed":
        raise AssertionError(f"Communication rule update failed: {updated_rule}")

    payment_rule = post(
        "/api/platform/service-mechanics/payment-rules",
        {
            "airline_code": "LH",
            "domain_code": "mobility",
            "family_code": "wheelchair",
            "variant_code": "wchr",
            "payment_required": False,
            "fee_included_in_fare": True,
            "separate_emd_required": False,
            "payment_timing": "not_applicable",
            "passenger_association_required": True,
            "segment_association_required": True,
            "notes": "Smoke payment mechanics.",
        },
        OWNER_HEADERS,
        201,
    )["payment_rule"]
    updated_payment = request(
        "PATCH",
        f"/api/platform/service-mechanics/payment-rules/{payment_rule['id']}",
        {"review_status": "confirmed"},
        OWNER_HEADERS,
    )[1]["payment_rule"]
    if updated_payment.get("review_status") != "confirmed":
        raise AssertionError(f"Payment rule update failed: {updated_payment}")

    template = post(
        "/api/platform/service-mechanics/ssr-osi-templates",
        {
            "communication_rule_id": communication_rule["id"],
            "airline_code": "LH",
            "domain_code": "mobility",
            "family_code": "wheelchair",
            "variant_code": "wchr",
            "gds_system": "amadeus",
            "template_type": "ssr",
            "ssr_code": "WCHR",
            "template_text": "SR WCHR LH HK1 {passenger_ref} {segment_ref}",
            "example_text": "SR WCHR LH HK1 P1 S1",
            "required_fields": ["passenger_ref", "segment_ref"],
        },
        OWNER_HEADERS,
        201,
    )["ssr_osi_template"]
    if template.get("template_type") != "ssr":
        raise AssertionError(f"SSR/OSI template creation failed: {template}")

    rfic_mapping = post(
        "/api/platform/service-mechanics/rfic-rfisc-mappings",
        {
            "airline_code": "LH",
            "domain_code": "mobility",
            "family_code": "wheelchair",
            "variant_code": "wchr",
            "rfic": "C",
            "rfisc": "0W1",
            "service_subcode": "0W1",
            "commercial_name": "Wheelchair service fee placeholder",
            "reason_for_issuance_description": "Smoke RFIC/RFISC mapping only.",
            "emd_type": "emd_a",
        },
        OWNER_HEADERS,
        201,
    )["rfic_rfisc_mapping"]
    if rfic_mapping.get("rfic") != "C" or rfic_mapping.get("rfisc") != "0W1":
        raise AssertionError(f"RFIC/RFISC mapping creation failed: {rfic_mapping}")

    lookup = post(
        "/api/platform/service-mechanics/lookup",
        {"airline_code": "LH", "domain_code": "mobility", "family_code": "wheelchair", "variant_code": "wchr"},
        OWNER_HEADERS,
    )
    if "communication" not in lookup or "payment" not in lookup:
        raise AssertionError(f"Lookup did not separate communication and payment mechanics: {lookup}")
    if not lookup["communication"].get("communication_rules") or not lookup["payment"].get("payment_rules"):
        raise AssertionError(f"Lookup did not return created mechanics: {lookup}")
    if lookup.get("provider_execution_disabled") is not True or lookup.get("emd_issuance_disabled") is not True:
        raise AssertionError(f"Lookup changed execution safeguards: {lookup}")

    empty_lookup = post(
        "/api/platform/service-mechanics/lookup",
        {"airline_code": "ZZ", "domain_code": "other", "family_code": "unknown_review_required"},
        OWNER_HEADERS,
    )
    if not empty_lookup.get("warnings"):
        raise AssertionError(f"Empty lookup should return warnings, not an error: {empty_lookup}")

    link = post(
        "/api/platform/service-mechanics/candidate-mechanics-links",
        {
            "candidate_type": "extracted_communication",
            "candidate_id": "smoke-mechanics-candidate",
            "mechanics_type": "communication_rule",
            "mechanics_record_id": communication_rule["id"],
            "airline_code": "LH",
            "domain_code": "mobility",
            "family_code": "wheelchair",
            "variant_code": "wchr",
            "confidence_score": 0.78,
            "evidence_text": "Policy says request SSR WCHR.",
        },
        OWNER_HEADERS,
        201,
    )["link"]
    if link.get("mechanics_record_id") != communication_rule["id"]:
        raise AssertionError(f"Candidate mechanics link creation failed: {link}")

    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    agency_summary = get(f"/api/agencies/{agency_id}/service-mechanics/summary", OWNER_HEADERS)
    if agency_summary.get("platform_mechanics_read_only") is not True or agency_summary.get("agency_global_mutation_disabled") is not True:
        raise AssertionError(f"Agency mechanics summary did not expose governance boundaries: {agency_summary}")
    agency_lookup = post(
        f"/api/agencies/{agency_id}/service-mechanics/lookup",
        {"airline_code": "LH", "domain_code": "mobility", "family_code": "wheelchair", "variant_code": "wchr"},
        OWNER_HEADERS,
    )
    if not agency_lookup.get("communication", {}).get("communication_rules"):
        raise AssertionError(f"Agency lookup did not read global mechanics: {agency_lookup}")
    blocked_status, _ = request(
        "POST",
        f"/api/agencies/{agency_id}/service-mechanics/communication-rules",
        {
            "airline_code": "LH",
            "domain_code": "mobility",
            "family_code": "wheelchair",
        },
        OWNER_HEADERS,
        405,
    )
    if blocked_status != 405:
        raise AssertionError(f"Agency global mechanics mutation was not blocked: {blocked_status}")

    agency_link = post(
        f"/api/agencies/{agency_id}/service-mechanics/candidate-mechanics-links",
        {
            "candidate_type": "extracted_communication",
            "candidate_id": "agency-smoke-mechanics-candidate",
            "mechanics_type": "communication_rule",
            "mechanics_record_id": communication_rule["id"],
            "airline_code": "LH",
            "domain_code": "mobility",
            "family_code": "wheelchair",
            "variant_code": "wchr",
            "confidence_score": 0.72,
            "evidence_text": "Agency local mechanics suggestion.",
        },
        OWNER_HEADERS,
        201,
    )
    if agency_link.get("link", {}).get("agency_id") != agency_id or agency_link.get("agency_auto_promotion_disabled") is not True:
        raise AssertionError(f"Agency candidate mechanics link was not scoped safely: {agency_link}")

    after = get("/api/readiness")
    mechanics_after = after.get("service_mechanics_mapping_foundation") or {}
    if mechanics_after.get("communication_rule_count", 0) < 1 or mechanics_after.get("payment_rule_count", 0) < 1 or mechanics_after.get("candidate_mechanics_link_count", 0) < 2:
        raise AssertionError(f"Readiness counts did not include created mechanics: {mechanics_after}")

    print("Phase 36.9 service mechanics mapping foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
