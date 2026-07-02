#!/usr/bin/env python3
from uuid import uuid4

from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, request


EXPECTED_PHASE = "phase_37_3_offer_builder_advisor_consumption_decision_pack_foundation"


def require_flag(section: dict, key: str, expected: object = True) -> None:
    if section.get(key) is not expected:
        raise AssertionError(f"Readiness flag {key} expected {expected!r}, got {section.get(key)!r}")


def require_count(section: dict, key: str) -> None:
    if key not in section:
        raise AssertionError(f"Readiness missing ancillary pricing count {key}")


def main() -> int:
    run_key = uuid4().hex[:10]
    airline_code = "ZX"
    domain_code = f"smoke_mobility_{run_key}"
    family_code = f"wheelchair_{run_key}"
    variant_code = f"wchr_{run_key}"
    service_identity = {
        "airline_code": airline_code,
        "domain_code": domain_code,
        "family_code": family_code,
        "variant_code": variant_code,
    }

    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")

    openapi = get("/openapi.json")
    paths = openapi.get("paths") or {}
    for path in paths:
        if path.startswith("/agent") or path.startswith("/admin") or path.startswith("/api/agent") or path.startswith("/api/admin"):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    for path, method in [
        ("/api/platform/ancillary-pricing/summary", "get"),
        ("/api/platform/ancillary-pricing/lookup", "post"),
        ("/api/platform/ancillary-pricing/evaluate", "post"),
        ("/api/platform/ancillary-pricing/pricing-rules", "get"),
        ("/api/platform/ancillary-pricing/pricing-rules", "post"),
        ("/api/platform/ancillary-pricing/pricing-rules/{record_id}", "patch"),
        ("/api/platform/ancillary-pricing/price-components", "get"),
        ("/api/platform/ancillary-pricing/price-components", "post"),
        ("/api/platform/ancillary-pricing/price-components/{record_id}", "patch"),
        ("/api/platform/ancillary-pricing/applicability", "get"),
        ("/api/platform/ancillary-pricing/applicability", "post"),
        ("/api/platform/ancillary-pricing/applicability/{record_id}", "patch"),
        ("/api/platform/ancillary-pricing/pricing-matrices", "get"),
        ("/api/platform/ancillary-pricing/pricing-matrices", "post"),
        ("/api/platform/ancillary-pricing/pricing-matrices/{record_id}", "patch"),
        ("/api/platform/ancillary-pricing/pricing-matrix-rows", "get"),
        ("/api/platform/ancillary-pricing/pricing-matrix-rows", "post"),
        ("/api/platform/ancillary-pricing/pricing-matrix-rows/{record_id}", "patch"),
        ("/api/platform/ancillary-pricing/exception-rules", "get"),
        ("/api/platform/ancillary-pricing/exception-rules", "post"),
        ("/api/platform/ancillary-pricing/exception-rules/{record_id}", "patch"),
        ("/api/platform/ancillary-pricing/quote-scenarios", "get"),
        ("/api/platform/ancillary-pricing/quote-scenarios", "post"),
        ("/api/platform/ancillary-pricing/quote-results", "get"),
        ("/api/platform/ancillary-pricing/candidate-pricing-links", "get"),
        ("/api/platform/ancillary-pricing/candidate-pricing-links", "post"),
        ("/api/platform/ancillary-pricing/candidate-pricing-links/{record_id}", "patch"),
        ("/api/agencies/{agency_id}/ancillary-pricing/summary", "get"),
        ("/api/agencies/{agency_id}/ancillary-pricing/lookup", "post"),
        ("/api/agencies/{agency_id}/ancillary-pricing/evaluate", "post"),
        ("/api/agencies/{agency_id}/ancillary-pricing/pricing-rules", "get"),
        ("/api/agencies/{agency_id}/ancillary-pricing/price-components", "get"),
        ("/api/agencies/{agency_id}/ancillary-pricing/applicability", "get"),
        ("/api/agencies/{agency_id}/ancillary-pricing/pricing-matrices", "get"),
        ("/api/agencies/{agency_id}/ancillary-pricing/pricing-matrix-rows", "get"),
        ("/api/agencies/{agency_id}/ancillary-pricing/exception-rules", "get"),
        ("/api/agencies/{agency_id}/ancillary-pricing/quote-scenarios", "get"),
        ("/api/agencies/{agency_id}/ancillary-pricing/quote-scenarios", "post"),
        ("/api/agencies/{agency_id}/ancillary-pricing/quote-results", "get"),
        ("/api/agencies/{agency_id}/ancillary-pricing/candidate-pricing-links", "get"),
        ("/api/agencies/{agency_id}/ancillary-pricing/candidate-pricing-links", "post"),
    ]:
        assert_openapi_path(paths, path, method)

    readiness = get("/api/readiness")
    pricing = readiness.get("ancillary_pricing_exception_foundation") or {}
    for key in [
        "pricing_rules_enabled",
        "price_components_enabled",
        "pricing_applicability_enabled",
        "pricing_matrices_enabled",
        "pricing_matrix_rows_enabled",
        "service_exception_rules_enabled",
        "quote_scenarios_enabled",
        "quote_results_enabled",
        "candidate_pricing_links_enabled",
        "platform_ancillary_pricing_ui_enabled",
        "agency_ancillary_pricing_ui_enabled",
        "deterministic_quote_evaluation_enabled",
        "exception_engine_expansion_enabled",
        "pricing_mechanics_reference_enabled",
        "invoice_payment_settlement_disabled",
        "emd_issuance_disabled",
        "provider_execution_disabled",
        "agency_auto_promotion_disabled",
    ]:
        require_flag(pricing, key)
    require_flag(pricing, "readiness_required", False)
    for key in [
        "pricing_rule_count",
        "price_component_count",
        "pricing_applicability_count",
        "pricing_matrix_count",
        "pricing_matrix_row_count",
        "service_exception_rule_count",
        "quote_scenario_count",
        "quote_result_count",
        "candidate_pricing_link_count",
    ]:
        require_count(pricing, key)

    pricing_rule = post(
        "/api/platform/ancillary-pricing/pricing-rules",
        {
            **service_identity,
            "pricing_rule_name": f"Smoke ZX WCHR ancillary pricing {run_key}",
            "pricing_status": "active",
            "review_status": "suggested",
            "mandatory_service": False,
            "optional_service": True,
            "fee_included_in_fare": False,
            "separate_fee_required": True,
            "emd_required": False,
            "notes": "Smoke pricing rule only.",
        },
        OWNER_HEADERS,
        201,
    )["pricing_rule"]
    updated_rule = request(
        "PATCH",
        f"/api/platform/ancillary-pricing/pricing-rules/{pricing_rule['id']}",
        {"review_status": "confirmed"},
        OWNER_HEADERS,
    )[1]["pricing_rule"]
    if updated_rule.get("review_status") != "confirmed":
        raise AssertionError(f"Pricing rule update failed: {updated_rule}")

    component = post(
        "/api/platform/ancillary-pricing/price-components",
        {
            "pricing_rule_id": pricing_rule["id"],
            "component_type": "service_fee",
            "amount": 35.0,
            "currency": "EUR",
            "amount_type": "fixed",
            "applies_per": "passenger",
            "roundtrip_doubling_rule": False,
            "sequence": 10,
        },
        OWNER_HEADERS,
        201,
    )["price_component"]
    if component.get("pricing_rule_id") != pricing_rule["id"]:
        raise AssertionError(f"Price component creation failed: {component}")

    applicability = post(
        "/api/platform/ancillary-pricing/applicability",
        {
            "pricing_rule_id": pricing_rule["id"],
            "dimension_code": "direct_vs_connecting",
            "operator": "equals",
            "value": "direct",
            "applies_as": "condition",
        },
        OWNER_HEADERS,
        201,
    )["applicability"]
    if applicability.get("pricing_rule_id") != pricing_rule["id"]:
        raise AssertionError(f"Applicability creation failed: {applicability}")

    exception_rule = post(
        "/api/platform/ancillary-pricing/exception-rules",
        {
            **service_identity,
            "exception_name": "Smoke direct route review note",
            "exception_type": "route_restriction",
            "severity": "advisory",
            "outcome": "manual_review",
            "condition_json": {"direct_vs_connecting": "direct"},
            "explanation": "Smoke advisory exception for deterministic quote testing.",
            "pricing_rule_id": pricing_rule["id"],
        },
        OWNER_HEADERS,
        201,
    )["exception_rule"]
    if exception_rule.get("pricing_rule_id") != pricing_rule["id"]:
        raise AssertionError(f"Exception rule creation failed: {exception_rule}")

    lookup = post(
        "/api/platform/ancillary-pricing/lookup",
        service_identity,
        OWNER_HEADERS,
    )
    if "pricing" not in lookup or "exceptions" not in lookup:
        raise AssertionError(f"Lookup did not return pricing and exceptions separately: {lookup}")
    lookup_pricing_ids = {item["id"] for item in lookup["pricing"].get("pricing_rules") or []}
    lookup_exception_ids = {item["id"] for item in lookup["exceptions"].get("exception_rules") or []}
    if pricing_rule["id"] not in lookup_pricing_ids or exception_rule["id"] not in lookup_exception_ids:
        raise AssertionError(f"Lookup did not return created pricing/exception records: {lookup}")

    quote_payload = {
        **service_identity,
        "scenario_name": f"Smoke direct WCHR quote {run_key}",
        "passenger_age": 34,
        "passenger_type": "adult",
        "route_type": "international",
        "direct_vs_connecting": "direct",
        "origin_airport": "SOF",
        "destination_airport": "FRA",
        "origin_country": "BG",
        "destination_country": "DE",
        "cabin": "economy",
        "segment_count": 1,
        "direction_count": 1,
        "currency": "EUR",
    }
    quote = post("/api/platform/ancillary-pricing/evaluate", quote_payload, OWNER_HEADERS)
    result = quote.get("result") or {}
    if result.get("evaluation_status") not in {"priced", "manual_review"}:
        raise AssertionError(f"Unexpected quote status: {quote}")
    if result.get("pricing_rule_ids") != [pricing_rule["id"]]:
        raise AssertionError(f"Quote did not isolate current smoke pricing rule: {quote}")
    if result.get("estimated_amount") != 35.0:
        raise AssertionError(f"Quote did not sum fixed component: {quote}")
    if "pricing" not in quote or "exceptions" not in quote:
        raise AssertionError(f"Quote did not separate pricing and exceptions: {quote}")
    if quote.get("invoice_payment_settlement_disabled") is not True or quote.get("emd_issuance_disabled") is not True or quote.get("provider_execution_disabled") is not True:
        raise AssertionError(f"Quote changed safety boundaries: {quote}")

    link = post(
        "/api/platform/ancillary-pricing/candidate-pricing-links",
        {
            "candidate_type": "extracted_price",
            "candidate_id": f"smoke-pricing-candidate-{run_key}",
            "pricing_record_type": "pricing_rule",
            "pricing_record_id": pricing_rule["id"],
            **service_identity,
            "confidence_score": 0.82,
            "evidence_text": "Policy states WCHR fee is EUR 35.",
        },
        OWNER_HEADERS,
        201,
    )["link"]
    if link.get("pricing_record_id") != pricing_rule["id"]:
        raise AssertionError(f"Candidate pricing link creation failed: {link}")

    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    agency_summary = get(f"/api/agencies/{agency_id}/ancillary-pricing/summary", OWNER_HEADERS)
    if agency_summary.get("platform_pricing_read_only") is not True or agency_summary.get("agency_global_mutation_disabled") is not True:
        raise AssertionError(f"Agency pricing summary did not expose governance boundaries: {agency_summary}")
    agency_lookup = post(
        f"/api/agencies/{agency_id}/ancillary-pricing/lookup",
        service_identity,
        OWNER_HEADERS,
    )
    agency_pricing_ids = {item["id"] for item in agency_lookup["pricing"].get("pricing_rules") or []}
    if pricing_rule["id"] not in agency_pricing_ids:
        raise AssertionError(f"Agency lookup did not read global pricing records: {agency_lookup}")
    agency_quote = post(f"/api/agencies/{agency_id}/ancillary-pricing/evaluate", quote_payload, OWNER_HEADERS)
    if agency_quote.get("agency_auto_promotion_disabled") is not True or agency_quote.get("provider_execution_disabled") is not True:
        raise AssertionError(f"Agency quote changed safety boundaries: {agency_quote}")

    blocked_status, _ = request(
        "POST",
        f"/api/agencies/{agency_id}/ancillary-pricing/pricing-rules",
        {
            **service_identity,
            "pricing_rule_name": "Agency blocked global mutation",
        },
        OWNER_HEADERS,
        expect=405,
    )
    if blocked_status != 405:
        raise AssertionError(f"Agency pricing mutation was not blocked: {blocked_status}")

    agency_link = post(
        f"/api/agencies/{agency_id}/ancillary-pricing/candidate-pricing-links",
        {
            "candidate_type": "extracted_price",
            "candidate_id": f"agency-smoke-pricing-candidate-{run_key}",
            "pricing_record_type": "pricing_rule",
            "pricing_record_id": pricing_rule["id"],
            **service_identity,
            "confidence_score": 0.66,
            "evidence_text": "Agency local pricing evidence.",
        },
        OWNER_HEADERS,
        201,
    )["link"]
    if agency_link.get("agency_id") != agency_id:
        raise AssertionError(f"Agency pricing link was not scoped safely: {agency_link}")

    pricing_after = get("/api/readiness").get("ancillary_pricing_exception_foundation") or {}
    for key in ["pricing_rule_count", "price_component_count", "pricing_applicability_count", "service_exception_rule_count", "quote_result_count", "candidate_pricing_link_count"]:
        if pricing_after.get(key, 0) < 1:
            raise AssertionError(f"Readiness count {key} did not include created pricing records: {pricing_after}")

    print("Ancillary pricing exception foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
