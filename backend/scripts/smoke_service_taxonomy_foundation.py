#!/usr/bin/env python3
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, request


EXPECTED_PHASE = "phase_39_3_airline_intelligence_agency_consumption_bridge"

SAMPLE_POLICY_TEXT = """General:
Kids Solo applies to children aged 5 to 14 years. UMT applies to unaccompanied teenagers on selected flights.

How to book:
Request SSR UMNR at least 24 hours before departure. PETC, WCHC, and MEDA examples must remain taxonomy-only mapping signals.

Pricing:
Service fee EUR 75 per passenger.
"""


def require_flag(section: dict, key: str, expected: object = True) -> None:
    if section.get(key) is not expected:
        raise AssertionError(f"Readiness flag {key} expected {expected!r}, got {section.get(key)!r}")


def require_count(section: dict, key: str) -> None:
    if key not in section:
        raise AssertionError(f"Readiness missing taxonomy count {key}")


def assert_mapping(text: str, expected_domain: str, expected_family: str, expected_variant: str | None = None, airline_code: str | None = None) -> dict:
    result = post(
        "/api/platform/service-taxonomy/map-candidate",
        {"text": text, "airline_code": airline_code},
        OWNER_HEADERS,
    )
    if result.get("domain_code") != expected_domain or result.get("family_code") != expected_family:
        raise AssertionError(f"{text} mapped unexpectedly: {result}")
    if expected_variant and result.get("variant_code") != expected_variant:
        raise AssertionError(f"{text} variant mapped unexpectedly: {result}")
    if result.get("external_ai_taxonomy_mapping_disabled") is not True:
        raise AssertionError("Taxonomy mapper changed external AI safeguard.")
    return result


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
        ("/api/platform/service-taxonomy/summary", "get"),
        ("/api/platform/service-taxonomy/seed-baseline", "post"),
        ("/api/platform/service-taxonomy/domains", "get"),
        ("/api/platform/service-taxonomy/domains", "post"),
        ("/api/platform/service-taxonomy/domains/{domain_id}", "patch"),
        ("/api/platform/service-taxonomy/families", "get"),
        ("/api/platform/service-taxonomy/families", "post"),
        ("/api/platform/service-taxonomy/families/{family_id}", "patch"),
        ("/api/platform/service-taxonomy/variants", "get"),
        ("/api/platform/service-taxonomy/variants", "post"),
        ("/api/platform/service-taxonomy/variants/{variant_id}", "patch"),
        ("/api/platform/service-taxonomy/aliases", "get"),
        ("/api/platform/service-taxonomy/aliases", "post"),
        ("/api/platform/service-taxonomy/aliases/{alias_id}", "patch"),
        ("/api/platform/service-taxonomy/applicability-dimensions", "get"),
        ("/api/platform/service-taxonomy/outcome-types", "get"),
        ("/api/platform/service-taxonomy/mapping-rules", "get"),
        ("/api/platform/service-taxonomy/mapping-rules", "post"),
        ("/api/platform/service-taxonomy/mapping-rules/{rule_id}", "patch"),
        ("/api/platform/service-taxonomy/map-candidate", "post"),
        ("/api/platform/service-taxonomy/candidate-links", "get"),
        ("/api/platform/service-taxonomy/candidate-links", "post"),
        ("/api/platform/service-taxonomy/candidate-links/{link_id}", "patch"),
        ("/api/platform/service-taxonomy/review-corrections", "get"),
        ("/api/platform/service-taxonomy/review-corrections", "post"),
        ("/api/agencies/{agency_id}/service-taxonomy/summary", "get"),
        ("/api/agencies/{agency_id}/service-taxonomy/domains", "get"),
        ("/api/agencies/{agency_id}/service-taxonomy/families", "get"),
        ("/api/agencies/{agency_id}/service-taxonomy/variants", "get"),
        ("/api/agencies/{agency_id}/service-taxonomy/aliases", "get"),
        ("/api/agencies/{agency_id}/service-taxonomy/applicability-dimensions", "get"),
        ("/api/agencies/{agency_id}/service-taxonomy/outcome-types", "get"),
        ("/api/agencies/{agency_id}/service-taxonomy/mapping-rules", "get"),
        ("/api/agencies/{agency_id}/service-taxonomy/map-candidate", "post"),
        ("/api/agencies/{agency_id}/service-taxonomy/candidate-links", "get"),
        ("/api/agencies/{agency_id}/service-taxonomy/candidate-links", "post"),
        ("/api/agencies/{agency_id}/service-taxonomy/candidate-links/{link_id}", "patch"),
        ("/api/agencies/{agency_id}/service-taxonomy/review-corrections", "get"),
        ("/api/agencies/{agency_id}/service-taxonomy/review-corrections", "post"),
    ]:
        assert_openapi_path(paths, path, method)

    readiness = get("/api/readiness")
    taxonomy = readiness.get("service_taxonomy_foundation") or {}
    for key in [
        "taxonomy_domains_enabled",
        "taxonomy_families_enabled",
        "taxonomy_variants_enabled",
        "airline_service_aliases_enabled",
        "applicability_dimensions_enabled",
        "outcome_types_enabled",
        "mapping_rules_enabled",
        "policy_candidate_taxonomy_links_enabled",
        "taxonomy_review_corrections_enabled",
        "platform_service_taxonomy_ui_enabled",
        "agency_service_taxonomy_ui_enabled",
        "deterministic_taxonomy_mapping_enabled",
        "external_ai_taxonomy_mapping_disabled",
        "agency_auto_promotion_disabled",
        "taxonomy_seeding_enabled",
    ]:
        require_flag(taxonomy, key)
    require_flag(taxonomy, "readiness_required", False)
    for key in [
        "domain_count",
        "family_count",
        "variant_count",
        "alias_count",
        "applicability_dimension_count",
        "outcome_type_count",
        "mapping_rule_count",
        "candidate_link_count",
        "review_correction_count",
    ]:
        require_count(taxonomy, key)

    first_seed = post("/api/platform/service-taxonomy/seed-baseline", {}, OWNER_HEADERS, 201)
    second_seed = post("/api/platform/service-taxonomy/seed-baseline", {}, OWNER_HEADERS, 201)
    if second_seed.get("created") != {
        "domains": 0,
        "families": 0,
        "variants": 0,
        "aliases": 0,
        "applicability_dimensions": 0,
        "outcome_types": 0,
        "mapping_rules": 0,
    }:
        raise AssertionError(f"Baseline seed was not idempotent: {first_seed} / {second_seed}")
    summary = get("/api/platform/service-taxonomy/summary", OWNER_HEADERS)
    for key in ["domain_count", "family_count", "variant_count", "alias_count", "mapping_rule_count"]:
        if summary.get(key, 0) <= 0:
            raise AssertionError(f"Seed did not populate {key}: {summary}")

    assert_mapping("Kids Solo", "children", "unaccompanied_minor", "kids_solo", "AF")
    assert_mapping("UMT", "children", "unaccompanied_minor", "unaccompanied_teenager", "AF")
    assert_mapping("PETC", "pets_animals", "pet_in_cabin", "petc")
    assert_mapping("WCHC", "mobility", "wheelchair", "wchc")
    assert_mapping("MEDA", "medical", "medical_clearance", "meda")

    rule = post(
        "/api/platform/service-taxonomy/mapping-rules",
        {
            "rule_name": "Smoke contains young traveler",
            "match_type": "contains",
            "match_value": "young traveler",
            "domain_code": "children",
            "family_code": "young_passenger",
            "variant_code": None,
            "confidence_score": 0.78,
            "priority": 40,
            "notes": "Smoke deterministic taxonomy mapping rule.",
        },
        OWNER_HEADERS,
        201,
    )["mapping_rule"]
    updated_rule = request(
        "PATCH",
        f"/api/platform/service-taxonomy/mapping-rules/{rule['id']}",
        {"priority": 35, "status": "active"},
        OWNER_HEADERS,
    )[1]["mapping_rule"]
    if updated_rule.get("priority") != 35:
        raise AssertionError(f"Platform mapping rule update failed: {updated_rule}")

    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    agency_summary = get(f"/api/agencies/{agency_id}/service-taxonomy/summary", OWNER_HEADERS)
    if agency_summary.get("platform_taxonomy_read_only") is not True or agency_summary.get("agency_global_mutation_disabled") is not True:
        raise AssertionError(f"Agency taxonomy summary did not expose governance boundaries: {agency_summary}")
    agency_domains = get(f"/api/agencies/{agency_id}/service-taxonomy/domains", OWNER_HEADERS)
    if not agency_domains.get("items") or agency_domains.get("read_only") is not True:
        raise AssertionError("Agency could not read global taxonomy domains.")
    agency_map = post(
        f"/api/agencies/{agency_id}/service-taxonomy/map-candidate",
        {"text": "SSR WCHC assistance required", "airline_code": "LH"},
        OWNER_HEADERS,
    )
    if agency_map.get("variant_code") != "wchc":
        raise AssertionError(f"Agency candidate mapping failed: {agency_map}")
    blocked_status, _ = request(
        "POST",
        f"/api/agencies/{agency_id}/service-taxonomy/domains",
        {"code": "agency_forbidden", "name": "Agency Forbidden"},
        OWNER_HEADERS,
        405,
    )
    if blocked_status != 405:
        raise AssertionError(f"Agency global domain mutation was not blocked: {blocked_status}")

    agency_source = post(
        f"/api/agencies/{agency_id}/airline-policy/sources",
        {
            "airline_iata_code": "AF",
            "airline_name_snapshot": "Air France",
            "service_domain": "special_services",
            "service_family": "unaccompanied_minor",
            "source_title": "Taxonomy smoke policy",
            "source_type": "pasted_text",
            "raw_text": SAMPLE_POLICY_TEXT,
        },
        OWNER_HEADERS,
        201,
    )["policy_source"]
    extracted = post(
        f"/api/agencies/{agency_id}/airline-policy/sources/{agency_source['id']}/extract",
        {"service_domain": "special_services", "service_family": "unaccompanied_minor"},
        OWNER_HEADERS,
        201,
    )
    rule_candidate = (extracted.get("candidates") or {}).get("rules", [])[0]
    link_result = post(
        f"/api/agencies/{agency_id}/service-taxonomy/candidate-links",
        {
            "policy_source_id": agency_source["id"],
            "extraction_run_id": extracted["extraction_run"]["id"],
            "candidate_type": "extracted_rule",
            "candidate_id": rule_candidate["id"],
            "airline_code": "AF",
            "evidence_text": rule_candidate.get("source_excerpt") or "Kids Solo",
        },
        OWNER_HEADERS,
        201,
    )
    link = link_result.get("link") or {}
    if link.get("candidate_type") != "extracted_rule" or link.get("agency_id") != agency_id:
        raise AssertionError(f"Agency candidate taxonomy link did not preserve Phase 36.7 reference/scope: {link_result}")
    if link_result.get("agency_auto_promotion_disabled") is not True:
        raise AssertionError("Candidate link changed agency auto-promotion safeguard.")

    correction = post(
        f"/api/agencies/{agency_id}/service-taxonomy/review-corrections",
        {
            "policy_candidate_taxonomy_link_id": link["id"],
            "candidate_type": "extracted_rule",
            "candidate_id": rule_candidate["id"],
            "previous_domain_code": link.get("domain_code"),
            "previous_family_code": link.get("family_code"),
            "previous_variant_code": link.get("variant_code"),
            "corrected_domain_code": "children",
            "corrected_family_code": "unaccompanied_minor",
            "corrected_variant_code": "kids_solo",
            "correction_reason": "Smoke agency-local taxonomy correction.",
            "promotion_requested": True,
        },
        OWNER_HEADERS,
        201,
    )
    if correction.get("promotion_status") != "pending_review" or correction.get("agency_auto_promotion_disabled") is not True:
        raise AssertionError(f"Agency correction did not remain pending review: {correction}")

    after = get("/api/readiness")
    taxonomy_after = after.get("service_taxonomy_foundation") or {}
    if taxonomy_after.get("candidate_link_count", 0) < 1 or taxonomy_after.get("review_correction_count", 0) < 1:
        raise AssertionError(f"Readiness counts did not include taxonomy link/correction: {taxonomy_after}")

    print("Phase 36.8 service taxonomy foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
