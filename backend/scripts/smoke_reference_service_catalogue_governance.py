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
EXPECTED_PHASE = "phase_39_5_saas_subscription_entitlement_foundation"

REQUIRED_DOMAINS = {
    "countries",
    "cities",
    "airports",
    "airlines",
    "currencies",
    "languages",
    "service_catalogue",
    "service_categories",
    "ssr_osi_codes",
    "document_types",
    "pet_species",
    "pet_breeds",
    "special_item_categories",
    "aircraft_types",
    "airline_alliances",
    "payment_methods",
    "tax_types",
}

REQUIRED_IMPORT_TEMPLATES = {
    "countries",
    "cities",
    "airports",
    "airlines",
    "currencies",
    "languages",
    "service_catalogue",
    "service_categories",
    "ssr_osi_codes",
    "document_types",
    "pet_species",
    "pet_breeds",
    "special_item_categories",
    "aircraft_types",
}

READINESS_FLAGS = [
    "reference_domain_usage_map_enabled",
    "reference_health_action_required_enabled",
    "domain_aware_import_templates_enabled",
    "enrichment_packs_defined_enabled",
    "service_catalogue_editable_enabled",
    "service_catalogue_operational_mapping_enabled",
    "service_catalogue_request_integration_enabled",
    "service_catalogue_rules_services_integration_enabled",
    "service_catalogue_offer_builder_integration_enabled",
    "service_catalogue_acceptance_booking_readiness_integration_enabled",
    "agency_service_catalogue_consume_enabled",
]


def request(method: str, path: str, body: dict | None = None, headers: dict | None = None, expect: int | None = None, allow_error: bool = False) -> tuple[int, dict]:
    data = json.dumps(body or {}).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        method=method,
        data=data,
        headers={**(headers or {}), "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            payload = response.read().decode("utf-8")
            status = response.status
            result = json.loads(payload) if payload else {}
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8")
        status = exc.code
        result = json.loads(payload) if payload else {}
    if expect is not None and status != expect:
        raise AssertionError(f"{method} {path} expected {expect}, got {status}: {result}")
    if expect is None and status >= 400 and not allow_error:
        raise AssertionError(f"{method} {path} failed with {status}: {result}")
    return status, result


def get(path: str, headers: dict | None = None, expect: int | None = None) -> dict:
    return request("GET", path, None, headers, expect)[1]


def post(path: str, body: dict | None = None, headers: dict | None = None, expect: int | None = None) -> dict:
    return request("POST", path, body or {}, headers, expect)[1]


def put(path: str, body: dict | None = None, headers: dict | None = None, expect: int | None = None) -> dict:
    return request("PUT", path, body or {}, headers, expect)[1]


def assert_openapi_path(paths: dict, path: str, method: str) -> None:
    if method.lower() not in paths.get(path, {}):
        raise AssertionError(f"OpenAPI missing {method.upper()} {path}")


def main() -> int:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")

    openapi = get("/openapi.json")
    paths = openapi.get("paths") or {}
    for path, method in [
        ("/api/platform/reference/domain-usage", "get"),
        ("/api/platform/reference/domain-usage/{domain_key}", "get"),
        ("/api/platform/reference/health", "get"),
        ("/api/platform/reference/records/action-required", "get"),
        ("/api/platform/reference/import/templates", "get"),
        ("/api/platform/reference/import/templates/{domain_key}", "get"),
        ("/api/platform/reference/import/preview", "post"),
        ("/api/platform/reference/import/apply", "post"),
        ("/api/platform/reference/enrichment-packs", "get"),
        ("/api/platform/reference/enrichment-packs/{pack_id}", "get"),
        ("/api/platform/reference/enrichment-packs/{pack_id}/preview", "post"),
        ("/api/platform/reference/enrichment-packs/{pack_id}/apply", "post"),
        ("/api/platform/service-catalogue", "get"),
        ("/api/platform/service-catalogue", "post"),
        ("/api/platform/service-catalogue/{service_id}", "get"),
        ("/api/platform/service-catalogue/{service_id}", "put"),
        ("/api/platform/service-catalogue/{service_id}/archive", "post"),
        ("/api/platform/service-catalogue/reorder", "post"),
    ]:
        assert_openapi_path(paths, path, method)

    post("/api/reference/seed", {}, OWNER_HEADERS)

    readiness = get("/api/readiness")
    reference_data = readiness.get("reference_data") or {}
    for flag in READINESS_FLAGS:
        if reference_data.get(flag) is not True:
            raise AssertionError(f"Readiness missing Phase 36.2.5 flag: {flag}")
    for count_key in [
        "reference_domain_usage_count",
        "import_template_count",
        "enrichment_pack_count",
        "service_catalogue_record_count",
        "service_catalogue_active_count",
        "reference_action_required_count",
    ]:
        if reference_data.get(count_key, -1) < 0:
            raise AssertionError(f"Readiness count missing or invalid: {count_key}")
    if reference_data.get("readiness_required") is not False:
        raise AssertionError("Reference governance should not be deployment-readiness required.")

    usage = get("/api/platform/reference/domain-usage", OWNER_HEADERS)["items"]
    usage_by_domain = {item["domain_key"]: item for item in usage}
    missing_domains = REQUIRED_DOMAINS - set(usage_by_domain)
    if missing_domains:
        raise AssertionError(f"Domain usage missing required domains: {sorted(missing_domains)}")
    for domain in REQUIRED_DOMAINS:
        item = usage_by_domain[domain]
        for key in ["primary_consumers", "used_in_workflows", "required_metadata_fields", "health_checks"]:
            if not item.get(key):
                raise AssertionError(f"Domain usage {domain} missing {key}")
    service_usage = get("/api/platform/reference/domain-usage/service_catalogue", OWNER_HEADERS)["domain"]
    if "booking_readiness" not in service_usage.get("used_in_workflows", []):
        raise AssertionError("Service catalogue usage did not include booking readiness workflow.")

    reference_health = get("/api/platform/reference/health", OWNER_HEADERS)
    if reference_health.get("important_records_replaced") is not True:
        raise AssertionError("Reference health did not explicitly replace unexplained Important Records.")
    expected_sections = {
        "missing_required_metadata",
        "used_by_active_workflows",
        "recently_imported_or_updated",
        "needs_review",
        "pinned_records",
        "high_risk_operational_domains",
    }
    health_section_keys = {section.get("key") for section in reference_health.get("sections") or []}
    if expected_sections - health_section_keys:
        raise AssertionError("Reference health missing expected sections.")

    action_required = get("/api/platform/reference/records/action-required", OWNER_HEADERS)["items"]
    for item in action_required[:20]:
        for key in ["domain", "record_id", "reason", "severity", "consumer_impact", "recommended_action"]:
            if key not in item:
                raise AssertionError(f"Action-required item missing {key}: {item}")

    templates = get("/api/platform/reference/import/templates", OWNER_HEADERS)["items"]
    template_domains = {item["domain_key"] for item in templates}
    missing_templates = REQUIRED_IMPORT_TEMPLATES - template_domains
    if missing_templates:
        raise AssertionError(f"Import templates missing domains: {sorted(missing_templates)}")
    service_template = get("/api/platform/reference/import/templates/service_catalogue", OWNER_HEADERS)["template"]
    if "service_key" not in service_template.get("required_columns", []):
        raise AssertionError("Service catalogue import template missing service_key.")

    now = int(time.time())
    imported_service_key = f"SMKIMP{now}"
    service_csv = "\n".join(
        [
            "service_key,label,category,ssr_code,rules_category,emd_applicability,required_documents_json",
            f'{imported_service_key},Smoke Imported Service,smoke_services,SMK,OTHER,optional,"[{{""code"":""smoke_doc"",""label"":""Smoke document""}}]"',
        ]
    )
    service_preview = post(
        "/api/platform/reference/import/preview",
        {"domain": "service_catalogue", "filename": "service.csv", "csv_text": service_csv, "mode": "upsert"},
        OWNER_HEADERS,
    )
    if service_preview.get("summary", {}).get("created") != 1:
        raise AssertionError(f"Service catalogue preview did not show one create: {service_preview}")
    service_apply = post(
        "/api/platform/reference/import/apply",
        {"domain": "service_catalogue", "filename": "service.csv", "csv_text": service_csv, "mode": "upsert"},
        OWNER_HEADERS,
    )
    if service_apply.get("summary", {}).get("created") != 1:
        raise AssertionError(f"Service catalogue import did not create one record: {service_apply}")

    airport_preview = post(
        "/api/platform/reference/import/preview",
        {
            "domain": "airports",
            "filename": "airports.csv",
            "csv_text": f"code,label,city_code,country_code,timezone\nX{now % 100:02d},Smoke Airport,SMK,ZZ,UTC",
            "mode": "upsert",
        },
        OWNER_HEADERS,
    )
    if airport_preview.get("summary", {}).get("created") != 1:
        raise AssertionError("Airport import preview did not report one create.")

    packs = get("/api/platform/reference/enrichment-packs", OWNER_HEADERS)["items"]
    pack_keys = {item.get("pack_key") for item in packs}
    for pack_key in ["airport_timezone_city_country_pack", "service_catalogue_ssr_emd_mapping_pack", "document_type_compliance_pack"]:
        if pack_key not in pack_keys:
            raise AssertionError(f"Missing default enrichment pack: {pack_key}")
    pack = get("/api/platform/reference/enrichment-packs/service_catalogue_ssr_emd_mapping_pack", OWNER_HEADERS)["pack"]
    for key in ["target_domain", "fields_added_or_updated", "workflow_impact", "validation_rules_json"]:
        if not pack.get(key):
            raise AssertionError(f"Enrichment pack missing {key}: {pack}")

    platform_key = f"SMKCRUD{now}"
    created = post(
        "/api/platform/service-catalogue",
        {
            "service_key": platform_key,
            "label": "Smoke CRUD Service",
            "category": "smoke_services",
            "ssr_code": "SMK",
            "rules_category": "OTHER",
            "request_form_enabled": True,
            "exception_engine_enabled": True,
            "booking_preview_enabled": True,
            "offer_feasibility_enabled": True,
            "acceptance_snapshot_enabled": True,
            "booking_readiness_enabled": True,
            "emd_applicability": "optional",
            "required_documents_json": [{"code": "smoke_doc", "label": "Smoke document"}],
        },
        OWNER_HEADERS,
        201,
    )["service"]
    if created.get("operational_mappings", {}).get("acceptance_booking_readiness", {}).get("booking_readiness_enabled") is not True:
        raise AssertionError("Created service did not expose booking readiness operational mapping.")
    updated = put(
        f"/api/platform/service-catalogue/{created['id']}",
        {"label": "Smoke CRUD Service Updated", "offer_pricing_enabled": True, "fee_expected": True},
        OWNER_HEADERS,
    )["service"]
    if updated.get("label") != "Smoke CRUD Service Updated" or updated.get("offer_pricing_enabled") is not True:
        raise AssertionError("Service catalogue update did not persist operational fields.")

    agency_catalogue = get("/api/reference/service-catalogue", AGENCY_HEADERS)["items"]
    agency_service = next((item for item in agency_catalogue if item.get("service_key") == platform_key), None)
    if not agency_service:
        raise AssertionError("Agency consume API did not include active platform service catalogue record.")
    for mapping_key in ["request", "rules_services", "ssr_osi", "offer", "acceptance_booking_readiness", "documents"]:
        if mapping_key not in agency_service.get("operational_mappings", {}):
            raise AssertionError(f"Agency service record missing operational mapping: {mapping_key}")

    status_code, _ = request(
        "POST",
        "/api/reference/service-catalogue",
        {"service_key": f"AGENCYBLOCK{now}", "label": "Agency Blocked", "category": "smoke_services"},
        AGENCY_HEADERS,
        allow_error=True,
    )
    if status_code not in {400, 403, 405, 422}:
        raise AssertionError(f"Agency service catalogue mutation should be blocked, got {status_code}.")

    archived = post(f"/api/platform/service-catalogue/{created['id']}/archive", {}, OWNER_HEADERS)["service"]
    if archived.get("status") != "archived" or archived.get("active") is not False:
        raise AssertionError("Service catalogue archive did not mark the service archived.")

    print("Reference service catalogue governance smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Reference service catalogue governance smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
