#!/usr/bin/env python3
from uuid import uuid4

from smoke_ancillary_pricing_exception_foundation import main as pricing_smoke_main
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, request
from smoke_service_mechanics_mapping_foundation import main as mechanics_smoke_main


from phase_assertions import application_phase_is_at_least


MINIMUM_PHASE = "phase_37_1_policy_comparison_service_advisor_foundation"
AGENCY_AGENT_HEADERS = {"X-Demo-User-Email": "agency.agent@aeroassist.dev"}
AGENCY_READONLY_HEADERS = {"X-Demo-User-Email": "agency.readonly@aeroassist.dev"}


def require_flag(section: dict, key: str, expected: object = True) -> None:
    if section.get(key) is not expected:
        raise AssertionError(f"Readiness flag {key} expected {expected!r}, got {section.get(key)!r}")


def require_count(section: dict, key: str) -> None:
    if key not in section:
        raise AssertionError(f"Readiness missing policy comparison count {key}")


def seed_airline_facts(airline_code: str, domain_code: str, family_code: str, variant_code: str, amount: float, run_key: str) -> dict:
    communication_rule = post(
        "/api/platform/service-mechanics/communication-rules",
        {
            "airline_code": airline_code,
            "domain_code": domain_code,
            "family_code": family_code,
            "variant_code": variant_code,
            "canonical_service_label": f"{airline_code} smoke assistance",
            "communication_channel": "gds",
            "gds_system": "amadeus",
            "request_method": "ssr",
            "ssr_code": "WCHR",
            "airline_confirmation_required": airline_code == "ZX",
            "manual_contact_required": airline_code == "QY",
            "ndc_supported": True,
            "gds_supported": True,
            "notes": f"Smoke comparison communication {run_key}.",
        },
        OWNER_HEADERS,
        201,
    )["communication_rule"]
    payment_rule = post(
        "/api/platform/service-mechanics/payment-rules",
        {
            "airline_code": airline_code,
            "domain_code": domain_code,
            "family_code": family_code,
            "variant_code": variant_code,
            "payment_required": amount > 0,
            "fee_included_in_fare": amount == 0,
            "separate_emd_required": airline_code == "QY",
            "payment_timing": "before_ticketing" if amount > 0 else "not_applicable",
            "notes": f"Smoke comparison payment {run_key}.",
        },
        OWNER_HEADERS,
        201,
    )["payment_rule"]
    rfic_mapping = post(
        "/api/platform/service-mechanics/rfic-rfisc-mappings",
        {
            "airline_code": airline_code,
            "domain_code": domain_code,
            "family_code": family_code,
            "variant_code": variant_code,
            "rfic": "C",
            "rfisc": f"{airline_code}1",
            "commercial_name": f"{airline_code} wheelchair service",
            "emd_type": "emd_a" if airline_code == "QY" else "not_required",
        },
        OWNER_HEADERS,
        201,
    )["rfic_rfisc_mapping"]
    pricing_rule = post(
        "/api/platform/ancillary-pricing/pricing-rules",
        {
            "airline_code": airline_code,
            "domain_code": domain_code,
            "family_code": family_code,
            "variant_code": variant_code,
            "pricing_rule_name": f"{airline_code} smoke comparison pricing {run_key}",
            "pricing_status": "active",
            "review_status": "confirmed",
            "optional_service": True,
            "separate_fee_required": amount > 0,
            "emd_required": airline_code == "QY",
        },
        OWNER_HEADERS,
        201,
    )["pricing_rule"]
    component = post(
        "/api/platform/ancillary-pricing/price-components",
        {
            "pricing_rule_id": pricing_rule["id"],
            "component_type": "service_fee",
            "amount": amount,
            "currency": "EUR",
            "amount_type": "fixed",
            "applies_per": "passenger",
            "sequence": 10,
        },
        OWNER_HEADERS,
        201,
    )["price_component"]
    exception_rule = post(
        "/api/platform/ancillary-pricing/exception-rules",
        {
            "airline_code": airline_code,
            "domain_code": domain_code,
            "family_code": family_code,
            "variant_code": variant_code,
            "exception_name": f"{airline_code} smoke advisor review {run_key}",
            "exception_type": "manual_contact_required" if airline_code == "QY" else "route_restriction",
            "severity": "warning" if airline_code == "QY" else "advisory",
            "outcome": "manual_review",
            "condition_json": {},
            "explanation": f"{airline_code} smoke comparison metadata only.",
            "pricing_rule_id": pricing_rule["id"],
        },
        OWNER_HEADERS,
        201,
    )["exception_rule"]
    return {
        "communication_rule": communication_rule,
        "payment_rule": payment_rule,
        "rfic_mapping": rfic_mapping,
        "pricing_rule": pricing_rule,
        "component": component,
        "exception_rule": exception_rule,
    }


def main() -> int:
    run_key = uuid4().hex[:10]
    domain_code = f"smoke_policy_comparison_{run_key}"
    family_code = f"advisor_wheelchair_{run_key}"
    variant_code = f"wchr_{run_key}"
    airline_codes = ["ZX", "QY"]

    health = get("/api/health")
    if not application_phase_is_at_least(health.get("phase"), MINIMUM_PHASE):
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")

    openapi = get("/openapi.json")
    paths = openapi.get("paths") or {}
    for path in paths:
        if path.startswith("/agent") or path.startswith("/admin") or path.startswith("/api/agent") or path.startswith("/api/admin"):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    for path, method in [
        ("/api/platform/policy-comparison/summary", "get"),
        ("/api/platform/policy-comparison/profiles", "get"),
        ("/api/platform/policy-comparison/profiles", "post"),
        ("/api/platform/policy-comparison/profiles/{profile_id}", "patch"),
        ("/api/platform/policy-comparison/build-profile", "post"),
        ("/api/platform/policy-comparison/compare", "post"),
        ("/api/platform/policy-comparison/snapshots", "get"),
        ("/api/platform/policy-comparison/snapshots", "post"),
        ("/api/platform/policy-comparison/comparison-rows", "get"),
        ("/api/platform/policy-comparison/advisor-scenarios", "get"),
        ("/api/platform/policy-comparison/advisor-scenarios", "post"),
        ("/api/platform/policy-comparison/advisor-evaluate", "post"),
        ("/api/platform/policy-comparison/advisor-results", "get"),
        ("/api/platform/policy-comparison/saved-views", "get"),
        ("/api/platform/policy-comparison/saved-views", "post"),
        ("/api/platform/policy-comparison/saved-views/{view_id}", "patch"),
        ("/api/agencies/{agency_id}/policy-comparison/summary", "get"),
        ("/api/agencies/{agency_id}/policy-comparison/profiles", "get"),
        ("/api/agencies/{agency_id}/policy-comparison/compare", "post"),
        ("/api/agencies/{agency_id}/policy-comparison/snapshots", "get"),
        ("/api/agencies/{agency_id}/policy-comparison/snapshots", "post"),
        ("/api/agencies/{agency_id}/policy-comparison/comparison-rows", "get"),
        ("/api/agencies/{agency_id}/policy-comparison/advisor-scenarios", "get"),
        ("/api/agencies/{agency_id}/policy-comparison/advisor-scenarios", "post"),
        ("/api/agencies/{agency_id}/policy-comparison/advisor-evaluate", "post"),
        ("/api/agencies/{agency_id}/policy-comparison/advisor-results", "get"),
        ("/api/agencies/{agency_id}/policy-comparison/saved-views", "get"),
        ("/api/agencies/{agency_id}/policy-comparison/saved-views", "post"),
    ]:
        assert_openapi_path(paths, path, method)

    readiness = get("/api/readiness")
    comparison_readiness = readiness.get("policy_comparison_service_advisor_foundation") or {}
    for key in [
        "comparison_profiles_enabled",
        "comparison_snapshots_enabled",
        "comparison_rows_enabled",
        "advisor_scenarios_enabled",
        "advisor_results_enabled",
        "saved_views_enabled",
        "platform_policy_comparison_ui_enabled",
        "agency_policy_comparison_ui_enabled",
        "agency_airline_service_advisor_ui_enabled",
        "deterministic_service_advisor_enabled",
        "operational_complexity_scoring_enabled",
        "recommendations_disabled",
        "provider_execution_disabled",
        "emd_issuance_disabled",
        "payment_invoice_settlement_disabled",
        "agency_global_mutation_blocked",
    ]:
        require_flag(comparison_readiness, key)
    require_flag(comparison_readiness, "readiness_required", False)
    for key in [
        "comparison_profile_count",
        "comparison_snapshot_count",
        "comparison_row_count",
        "advisor_scenario_count",
        "advisor_result_count",
        "saved_view_count",
    ]:
        require_count(comparison_readiness, key)

    for airline_code, amount in [("ZX", 35.0), ("QY", 55.0)]:
        seed_airline_facts(airline_code, domain_code, family_code, variant_code, amount, run_key)

    manual_profile = post(
        "/api/platform/policy-comparison/profiles",
        {
            "airline_code": "ZX",
            "domain_code": domain_code,
            "family_code": family_code,
            "variant_code": variant_code,
            "display_name": f"ZX manual smoke profile {run_key}",
            "commercial_names": ["ZX wheelchair service"],
            "review_status": "suggested",
        },
        OWNER_HEADERS,
        201,
    )["comparison_profile"]
    updated_profile = request(
        "PATCH",
        f"/api/platform/policy-comparison/profiles/{manual_profile['id']}",
        {"review_status": "confirmed"},
        OWNER_HEADERS,
    )[1]["comparison_profile"]
    if updated_profile.get("review_status") != "confirmed":
        raise AssertionError(f"Profile update failed: {updated_profile}")

    built_profile = post(
        "/api/platform/policy-comparison/build-profile",
        {
            "airline_code": "QY",
            "domain_code": domain_code,
            "family_code": family_code,
            "variant_code": variant_code,
            "display_name": f"QY built smoke profile {run_key}",
            "review_status": "suggested",
        },
        OWNER_HEADERS,
        201,
    )["comparison_profile"]
    if not built_profile.get("pricing_summary_json", {}).get("estimated_price_available"):
        raise AssertionError(f"Built profile did not consume pricing metadata: {built_profile}")

    profiles = get("/api/platform/policy-comparison/profiles", OWNER_HEADERS)["items"]
    if manual_profile["id"] not in {item["id"] for item in profiles} or built_profile["id"] not in {item["id"] for item in profiles}:
        raise AssertionError("Platform profile list did not include created profiles.")

    compare_payload = {
        "snapshot_name": f"Smoke two-airline comparison {run_key}",
        "airline_codes": airline_codes,
        "domain_code": domain_code,
        "family_code": family_code,
        "variant_code": variant_code,
        "route_context_json": {"direct_vs_connecting": "direct", "origin_airport": "SOF", "destination_airport": "FRA"},
        "passenger_context_json": {"passenger_type": "adult", "passenger_age": 34},
        "service_context_json": {"service_code": "WCHR"},
        "generated_from": "manual",
    }
    comparison = post("/api/platform/policy-comparison/compare", compare_payload, OWNER_HEADERS, 201)
    rows = comparison.get("rows") or []
    if len(rows) != 2 or {row.get("airline_code") for row in rows} != set(airline_codes):
        raise AssertionError(f"Platform comparison did not return two airline rows: {comparison}")
    if comparison.get("recommendations_disabled") is not True or comparison.get("provider_execution_disabled") is not True:
        raise AssertionError(f"Comparison changed safety boundaries: {comparison}")

    row_items = get(f"/api/platform/policy-comparison/comparison-rows?snapshot_id={comparison['snapshot']['id']}", OWNER_HEADERS)["items"]
    if len(row_items) < 2:
        raise AssertionError(f"Comparison rows were not persisted: {row_items}")

    scenario = post(
        "/api/platform/policy-comparison/advisor-scenarios",
        {
            "scenario_name": f"Platform advisor scenario {run_key}",
            "airline_codes": airline_codes,
            "domain_code": domain_code,
            "family_code": family_code,
            "variant_code": variant_code,
            "passenger_age": 34,
            "passenger_type": "adult",
            "route_type": "international",
            "direct_vs_connecting": "direct",
            "origin_airport": "SOF",
            "destination_airport": "FRA",
            "origin_country": "BG",
            "destination_country": "DE",
            "requested_service_context_json": {"service_code": "WCHR"},
        },
        OWNER_HEADERS,
        201,
    )["advisor_scenario"]
    advisor = post(
        "/api/platform/policy-comparison/advisor-evaluate",
        {"scenario_id": scenario["id"], **{key: scenario[key] for key in ["scenario_name", "airline_codes", "domain_code", "family_code", "variant_code"]}},
        OWNER_HEADERS,
        201,
    )
    if advisor["result"].get("result_status") not in {"evaluated", "manual_review", "blocked"}:
        raise AssertionError(f"Unexpected advisor status: {advisor}")
    if advisor.get("recommendations_disabled") is not True or advisor.get("payment_invoice_settlement_disabled") is not True:
        raise AssertionError(f"Advisor changed safety boundaries: {advisor}")

    saved_view = post(
        "/api/platform/policy-comparison/saved-views",
        {
            "view_name": f"Platform smoke view {run_key}",
            "airline_codes": airline_codes,
            "domain_code": domain_code,
            "family_code": family_code,
            "variant_code": variant_code,
            "visible_columns": ["airline", "pricing", "complexity"],
            "is_global": True,
        },
        OWNER_HEADERS,
        201,
    )["saved_view"]
    patched_view = request(
        "PATCH",
        f"/api/platform/policy-comparison/saved-views/{saved_view['id']}",
        {"status": "active"},
        OWNER_HEADERS,
    )[1]["saved_view"]
    if patched_view.get("id") != saved_view["id"]:
        raise AssertionError(f"Saved view patch failed: {patched_view}")

    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    agency_summary = get(f"/api/agencies/{agency_id}/policy-comparison/summary", AGENCY_AGENT_HEADERS)
    if agency_summary.get("platform_profiles_read_only") is not True or agency_summary.get("agency_global_mutation_blocked") is not True:
        raise AssertionError(f"Agency summary did not expose governance boundaries: {agency_summary}")

    agency_compare = post(
        f"/api/agencies/{agency_id}/policy-comparison/compare",
        compare_payload,
        AGENCY_AGENT_HEADERS,
        201,
    )
    if len(agency_compare.get("rows") or []) != 2:
        raise AssertionError(f"Agency comparison failed: {agency_compare}")

    blocked_status, _ = request(
        "PATCH",
        f"/api/agencies/{agency_id}/policy-comparison/profiles/{manual_profile['id']}",
        {"review_status": "corrected"},
        AGENCY_AGENT_HEADERS,
        expect=404,
    )
    if blocked_status != 404:
        raise AssertionError(f"Agency global profile mutation was not blocked: {blocked_status}")

    agency_advisor = post(
        f"/api/agencies/{agency_id}/policy-comparison/advisor-evaluate",
        {
            "scenario_name": f"Agency advisor scenario {run_key}",
            "airline_codes": airline_codes,
            "domain_code": domain_code,
            "family_code": family_code,
            "variant_code": variant_code,
            "passenger_age": 34,
            "passenger_type": "adult",
            "route_type": "international",
            "direct_vs_connecting": "direct",
            "requested_service_context_json": {"service_code": "WCHR"},
        },
        AGENCY_AGENT_HEADERS,
        201,
    )
    if agency_advisor.get("recommendations_disabled") is not True or agency_advisor.get("emd_issuance_disabled") is not True:
        raise AssertionError(f"Agency advisor changed safety boundaries: {agency_advisor}")

    agency_view = post(
        f"/api/agencies/{agency_id}/policy-comparison/saved-views",
        {
            "view_name": f"Agency smoke view {run_key}",
            "airline_codes": airline_codes,
            "domain_code": domain_code,
            "family_code": family_code,
            "variant_code": variant_code,
            "visible_columns": ["airline", "complexity"],
        },
        AGENCY_AGENT_HEADERS,
        201,
    )["saved_view"]
    if agency_view.get("agency_id") != agency_id or agency_view.get("is_global") is not False:
        raise AssertionError(f"Agency saved view was not scoped locally: {agency_view}")

    readonly_status, _ = request(
        "POST",
        f"/api/agencies/{agency_id}/policy-comparison/saved-views",
        {
            "view_name": f"Readonly forbidden view {run_key}",
            "airline_codes": airline_codes,
            "domain_code": domain_code,
            "family_code": family_code,
            "variant_code": variant_code,
            "visible_columns": ["airline"],
        },
        AGENCY_READONLY_HEADERS,
        expect=403,
    )
    if readonly_status != 403:
        raise AssertionError(
            f"Agency read-only policy comparison write was not denied: {readonly_status}"
        )

    comparison_after = get("/api/readiness").get("policy_comparison_service_advisor_foundation") or {}
    for key in ["comparison_profile_count", "comparison_snapshot_count", "comparison_row_count", "advisor_scenario_count", "advisor_result_count", "saved_view_count"]:
        if comparison_after.get(key, 0) < 1:
            raise AssertionError(f"Readiness count {key} did not include created records: {comparison_after}")

    pricing_smoke_main()
    mechanics_smoke_main()

    print("Policy comparison service advisor foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
