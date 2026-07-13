#!/usr/bin/env python3
import sys
import time
from pathlib import Path
from urllib.parse import quote

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import ServiceParameterTaxonomy, ServiceParameterTaxonomyCreate
from services.service_parameter_taxonomy_service import (
    AMOUNT_TYPES,
    DEFAULT_SERVICE_PARAMETER_TAXONOMY_TEMPLATES,
    EVALUATION_STATUS_OPTIONS,
    PASSENGER_ASSISTANCE_PARAMETER_FIELDS,
    PETS_ANIMALS_PARAMETER_FIELDS,
    PHASE_LABEL,
    PRICING_CATEGORIES,
    PRICING_FARE_BUNDLES,
    PRICING_FLIGHT_TYPES,
    PRICING_ROUTE_TYPES,
    PRICING_UNITS,
    PRICING_WAY_VALUES,
    ROUTE_AIRCRAFT_CABIN_PARAMETER_FIELDS,
    SERVICE_PARAMETER_TAXONOMIES_COLLECTION,
    SERVICE_PARAMETER_TAXONOMY_STATUSES,
    SPECIAL_ITEM_PARAMETER_FIELDS,
    SUPPORT_STATUS_OPTIONS,
    TAXONOMY_APPROVAL_STATUSES,
    TAXONOMY_REVIEW_STATUSES,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_54_4_task_automation_dependency_orchestration_foundation"
ROOT = Path(__file__).resolve().parents[2]
PLATFORM_BASE = "/api/platform/service-parameter-taxonomies"
AGENCY_BASE_TEMPLATE = "/api/agencies/{agency_id}/service-parameter-taxonomies"


def run_ref(prefix: str) -> str:
    return f"{prefix}-{int(time.time() * 1000)}"


def require_text(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8")
    if text not in content:
        raise AssertionError(f"{path.relative_to(ROOT)} missing expected text: {text}")


def reject_text(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8")
    if text in content:
        raise AssertionError(f"{path.relative_to(ROOT)} contains rejected text: {text}")


def disabled_flags() -> list[str]:
    return [
        "metadata_only",
        "service_parameter_taxonomy_integration_foundation",
        "measurable_service_parameters_enabled",
        "current_architecture_integrated",
        "parameter_taxonomies_reusable",
        "policy_pricing_capability_constraints_procedures_separate",
        "standalone_policy_engine_disabled",
        "legacy_pricing_engine_disabled",
        "pocketbase_logic_disabled",
        "duplicate_operational_models_disabled",
        "live_rule_evaluation_disabled",
        "live_pricing_calculation_disabled",
        "recommendation_execution_disabled",
        "provider_integrations_disabled",
        "no_ai_generation",
        "no_llm_generation",
        "background_workers_disabled",
        "booking_disabled",
        "ticketing_disabled",
        "emd_issuance_disabled",
        "human_authority_final",
    ]


def assert_disabled_response(payload: dict) -> None:
    for flag in disabled_flags():
        if payload.get(flag) is not True:
            raise AssertionError(f"Payload missing disabled flag {flag}: {payload}")


def parameter(name: str, value_type: str = "string", required: bool = False, **metadata: object) -> dict:
    return {"name": name, "value_type": value_type, "required": required, **metadata}


def taxonomy_payload(agency_id: str, reference: str) -> dict:
    return {
        "agency_id": agency_id,
        "taxonomy_reference": reference,
        "taxonomy_status": "in_review",
        "taxonomy_version": "51.1.0-smoke",
        "taxonomy_name": "PETC WCHC EXST Service Parameter Smoke",
        "taxonomy_description": "Metadata-only measurable parameters for passenger assistance, pets, special items, route context, pricing references, and governance.",
        "policy_family": "special_service_policy",
        "service_family": "cross_service_operational_parameters",
        "service_codes": ["PETC", "AVIH", "WCHC", "EXST", "CBBG"],
        "beneficiary_type": "passenger",
        "parameter_domain": "airline_operational_intelligence",
        "parameter_group": "cross_service",
        "parameter_scope": "airline_service_policy_metadata",
        "support_status_options": SUPPORT_STATUS_OPTIONS,
        "evaluation_status_options": EVALUATION_STATUS_OPTIONS,
        "restriction_status_options": ["none", "conditional", "restricted", "blocked", "manual_review", "unknown"],
        "approval_status_options": ["not_required", "required", "requested", "approved", "rejected", "manual_review", "unknown"],
        "wheelchair_mobility_parameters": [parameter("wheelchair_service_code", "enum", True, values=["WCHR", "WCHS", "WCHC", "WCOB", "MAAS"])],
        "mobility_level_parameters": [parameter("mobility_level", "enum", True, values=["ramp", "stairs", "cabin_seat"])],
        "wheelchair_device_parameters": [parameter("wheelchair_type", "enum", False, values=["manual", "electric"])],
        "battery_type_parameters": [parameter("battery_type", "enum", False, values=["dry_cell", "gel_cell", "lithium"])],
        "device_weight_dimension_parameters": [parameter("device_dimensions_cm", "dimension_set", False)],
        "airport_assistance_parameters": [parameter("airport_assistance_required", "boolean", False)],
        "onboard_assistance_parameters": [parameter("onboard_aisle_chair", "boolean", False)],
        "medical_support_parameters": [parameter("medical_clearance_required", "boolean", False)],
        "medif_parameters": [parameter("medif_required", "boolean", False)],
        "fit_to_fly_parameters": [parameter("fit_to_fly_document", "document", False)],
        "stretcher_parameters": [parameter("stretcher_required", "boolean", False)],
        "oxygen_poc_parameters": [parameter("poc_model", "string", False)],
        "battery_duration_parameters": [parameter("battery_duration_minutes", "integer", False)],
        "umnr_age_parameters": [parameter("minor_age", "integer", False)],
        "umnr_route_parameters": [parameter("umnr_route_allowed", "boolean", False)],
        "guardian_parameters": [parameter("guardian_contact_required", "boolean", False)],
        "extra_seat_parameters": [parameter("extra_seat_reason", "enum", False, values=["comfort", "medical", "cbbg", "passenger_of_size"])],
        "passenger_of_size_parameters": [parameter("passenger_of_size_review", "boolean", False)],
        "cbbg_parameters": [parameter("cbbg_item_type", "string", False)],
        "adjacent_seat_parameters": [parameter("adjacent_seat_required", "boolean", False)],
        "cabin_restriction_parameters": [parameter("cabin_restriction", "string", False)],
        "extra_seat_refund_parameters": [parameter("refund_condition", "string", False)],
        "petc_parameters": [parameter("pet_in_cabin_allowed", "boolean", True)],
        "avih_parameters": [parameter("animal_in_hold_allowed", "boolean", False)],
        "svan_parameters": [parameter("service_animal_accepted", "boolean", False)],
        "esan_parameters": [parameter("emotional_support_animal_accepted", "boolean", False)],
        "species_parameters": [parameter("species", "enum", True, values=["dog", "cat"])],
        "breed_parameters": [parameter("breed", "string", False)],
        "breed_risk_flag_parameters": [parameter("brachycephalic_or_restricted_breed", "boolean", False)],
        "animal_age_parameters": [parameter("animal_age_months", "integer", False)],
        "animal_weight_parameters": [parameter("animal_weight_kg", "decimal", True)],
        "container_dimension_parameters": [parameter("container_dimensions_cm", "dimension_set", True)],
        "container_type_parameters": [parameter("container_type", "enum", False, values=["soft", "hard"])],
        "pet_under_seat_parameters": [parameter("under_seat_fit_required", "boolean", False)],
        "pet_on_adjacent_extra_seat_parameters": [parameter("pet_on_adjacent_extra_seat_allowed", "boolean", False)],
        "animal_purpose_parameters": [parameter("animal_purpose", "enum", False, values=["pet", "service_animal", "emotional_support"])],
        "temperature_parameters": [parameter("temperature_embargo_threshold", "range", False)],
        "seasonal_restriction_parameters": [parameter("seasonal_restriction", "string", False)],
        "animal_document_parameters": [parameter("animal_document_type", "document", False)],
        "sports_equipment_parameters": [parameter("sports_equipment_type", "enum", False, values=["BIKE", "SKI", "GOLF", "SURF", "DIVE"])],
        "musical_instrument_parameters": [parameter("musical_instrument_type", "string", False)],
        "fragile_valuable_parameters": [parameter("declared_fragile_or_valuable", "boolean", False)],
        "restricted_equipment_parameters": [parameter("restricted_equipment_type", "string", False)],
        "special_baggage_parameters": [parameter("special_baggage_category", "string", False)],
        "item_type_parameters": [parameter("item_type", "string", False)],
        "item_weight_dimension_parameters": [parameter("item_weight_dimensions", "weight_dimension_set", False)],
        "packaging_parameters": [parameter("packaging_required", "string", False)],
        "declared_value_parameters": [parameter("declared_value", "money", False)],
        "permit_document_parameters": [parameter("permit_document", "document", False)],
        "route_type_parameters": [parameter("route_type", "enum", False, values=PRICING_ROUTE_TYPES)],
        "flight_type_parameters": [parameter("flight_type", "enum", False, values=PRICING_FLIGHT_TYPES)],
        "airport_parameters": [parameter("airport_code", "iata_code", False)],
        "country_parameters": [parameter("country_code", "iso_country_code", False)],
        "aircraft_type_parameters": [parameter("aircraft_type", "string", False)],
        "aircraft_family_parameters": [parameter("aircraft_family", "string", False)],
        "cabin_parameters": [parameter("cabin", "string", False)],
        "seat_type_parameters": [parameter("seat_type", "string", False)],
        "fixed_armrest_parameters": [parameter("fixed_armrest", "boolean", False)],
        "under_seat_space_parameters": [parameter("under_seat_space_cm", "dimension_set", False)],
        "accessible_lavatory_parameters": [parameter("accessible_lavatory", "boolean", False)],
        "pricing_units": PRICING_UNITS,
        "pricing_way_values": PRICING_WAY_VALUES,
        "pricing_route_types": PRICING_ROUTE_TYPES,
        "pricing_flight_types": PRICING_FLIGHT_TYPES,
        "pricing_fare_bundles": PRICING_FARE_BUNDLES,
        "pricing_categories": PRICING_CATEGORIES,
        "amount_types": AMOUNT_TYPES,
        "pricing_basis_parameters": [parameter("pricing_basis", "string", False)],
        "pricing_formula_components": [parameter("formula_component", "string", False)],
        "pricing_applicability_parameters": [parameter("pricing_applicability", "string", False)],
        "refund_condition_parameters": [parameter("refund_condition", "string", False)],
        "exchange_condition_parameters": [parameter("exchange_condition", "string", False)],
        "required_reference_collections": [
            "airline_knowledge_acquisitions",
            "operational_constraints",
            "airline_capability_matrix",
            "operational_intelligence_cases",
        ],
        "required_reference_values": [
            {"collection": "airline_capability_matrix", "field": "service_codes", "values": ["PETC", "WCHC", "EXST"]},
            {"collection": "operational_constraints", "field": "condition_operator", "values": ["equals", "range"]},
        ],
        "missing_reference_notes": "Reference values are metadata only until real airline data population.",
        "acquisition_ids": ["AKA-SMOKE-511"],
        "normalisation_ids": ["AKN-SMOKE-511"],
        "constraint_ids": ["OCE-SMOKE-511"],
        "knowledge_version_ids": ["AKV-SMOKE-511"],
        "capability_matrix_ids": ["ACM-SMOKE-511"],
        "operational_evaluation_ids": ["OKE-SMOKE-511"],
        "feasibility_ids": ["PSF-SMOKE-511"],
        "recommendation_ids": ["ARE-SMOKE-511"],
        "intelligent_offer_package_ids": ["IOB-SMOKE-511"],
        "operational_intelligence_case_ids": ["OIC-SMOKE-511"],
        "review_status": "in_review",
        "approval_status": "pending",
        "reviewer": "taxonomy-reviewer",
        "review_notes": "Smoke taxonomy is under human review.",
        "approved_by": "taxonomy-approver",
        "approved_at": "2026-07-09T00:00:00+00:00",
        "internal_notes": "Metadata-only taxonomy. No rule evaluation, pricing calculation, recommendation execution, provider call, AI generation, worker, booking, ticketing, or EMD issuance.",
        "metadata": {"smoke": True, "metadata_only": True},
    }


def verify_model_and_collection_registration() -> None:
    if SERVICE_PARAMETER_TAXONOMIES_COLLECTION not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("service_parameter_taxonomies is not registered as agency-owned metadata.")
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Service phase label mismatch: {PHASE_LABEL}")

    payload = taxonomy_payload("agency-smoke", "SPT-SMOKE-MODEL")
    create_model = ServiceParameterTaxonomyCreate(**payload)
    record = ServiceParameterTaxonomy(**create_model.model_dump(mode="json", exclude_none=True))
    if record.taxonomy_reference != "SPT-SMOKE-MODEL":
        raise AssertionError("Service parameter taxonomy model did not preserve reference metadata.")
    for field in [
        "wheelchair_mobility_parameters",
        "petc_parameters",
        "sports_equipment_parameters",
        "route_type_parameters",
        "pricing_units",
        "required_reference_collections",
        "acquisition_ids",
        "operational_intelligence_case_ids",
    ]:
        if not getattr(record, field):
            raise AssertionError(f"Service parameter taxonomy model did not preserve {field}.")
    if record.metadata_only is not True or record.live_rule_evaluation_disabled is not True:
        raise AssertionError("Service parameter taxonomy model is not metadata-only.")

    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "service_parameter_taxonomies_id_unique",
        "service_parameter_taxonomies_reference_unique",
        "service_parameter_taxonomies_agency_status_lookup",
        "service_parameter_taxonomies_service_code_lookup",
        "service_parameter_taxonomies_parameter_group_lookup",
        "service_parameter_taxonomies_review_status_lookup",
        "service_parameter_taxonomies_approval_status_lookup",
        "service_parameter_taxonomies_acquisition_lookup",
        "service_parameter_taxonomies_operational_case_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Database index registration missing {index_name}.")

    for value in ["draft", "active", "in_review", "approved", "deprecated", "archived"]:
        if value not in SERVICE_PARAMETER_TAXONOMY_STATUSES:
            raise AssertionError(f"Missing taxonomy status {value}.")
    for value in ["not_reviewed", "in_review", "changes_requested", "reviewed", "approved", "rejected"]:
        if value not in TAXONOMY_REVIEW_STATUSES:
            raise AssertionError(f"Missing review status {value}.")
    for value in ["not_submitted", "pending", "approved", "rejected", "expired"]:
        if value not in TAXONOMY_APPROVAL_STATUSES:
            raise AssertionError(f"Missing approval status {value}.")

    required_templates = {
        "wheelchair_mobility": {"WCHR", "WCHS", "WCHC", "WCOB", "MAAS"},
        "medical_support": {"MEDA", "MEDIF", "STCR"},
        "oxygen_poc": {"OXYG", "POC"},
        "umnr": {"UMNR", "YP"},
        "extra_seat": {"EXST", "CBBG"},
        "pet_transport": {"PETC", "AVIH"},
        "service_animal": {"SVAN"},
        "emotional_support_animal": {"ESAN"},
        "sports_equipment": {"SPEQ", "BIKE", "SKI", "GOLF", "SURF", "DIVE"},
        "musical_instruments": {"MUSI", "CBBG", "EXST"},
        "fragile_valuable": {"FRAGILE", "VALUABLE", "CBBG", "EXST"},
        "restricted_equipment": {"WEAP"},
        "pricing": set(),
    }
    templates_by_group = {template["parameter_group"]: set(template.get("service_codes") or []) for template in DEFAULT_SERVICE_PARAMETER_TAXONOMY_TEMPLATES}
    for group, codes in required_templates.items():
        if group not in templates_by_group:
            raise AssertionError(f"Missing default parameter template group {group}.")
        if codes and not codes.issubset(templates_by_group[group]):
            raise AssertionError(f"Template group {group} missing codes {codes - templates_by_group[group]}.")


def verify_router_and_ui_registration() -> None:
    openapi = get("/openapi.json", OWNER_HEADERS)
    paths = openapi.get("paths", {})
    for path, method in [
        (PLATFORM_BASE, "get"),
        (PLATFORM_BASE, "post"),
        (f"{PLATFORM_BASE}/summary", "get"),
        (f"{PLATFORM_BASE}/{{taxonomy_id}}", "get"),
        (f"{PLATFORM_BASE}/{{taxonomy_id}}", "put"),
        (f"{PLATFORM_BASE}/{{taxonomy_id}}", "delete"),
        ("/api/agencies/{agency_id}/service-parameter-taxonomies", "get"),
        ("/api/agencies/{agency_id}/service-parameter-taxonomies", "post"),
        ("/api/agencies/{agency_id}/service-parameter-taxonomies/summary", "get"),
        ("/api/agencies/{agency_id}/service-parameter-taxonomies/{taxonomy_id}", "get"),
        ("/api/agencies/{agency_id}/service-parameter-taxonomies/{taxonomy_id}", "put"),
        ("/api/agencies/{agency_id}/service-parameter-taxonomies/{taxonomy_id}", "delete"),
    ]:
        assert_openapi_path(paths, path, method)

    for path in paths:
        if "service-parameter-taxonomies" in path:
            for forbidden in ["/admin", "/agent", "evaluate", "price-calculate", "recommendation-execute", "providers", "ai-generate", "worker"]:
                if forbidden in path:
                    raise AssertionError(f"Forbidden route exposed for service parameter taxonomies: {path}")

    for path, text in [
        (ROOT / "frontend/src/App.jsx", "/platform/service-parameter-taxonomies"),
        (ROOT / "frontend/src/App.jsx", "/agency/service-parameter-taxonomies"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Service Parameter Taxonomies"),
        (ROOT / "frontend/src/pages/platform/ServiceParameterTaxonomiesPage.jsx", "Taxonomy Overview"),
        (ROOT / "frontend/src/pages/platform/ServiceParameterTaxonomiesPage.jsx", "Passenger Assistance Parameters"),
        (ROOT / "frontend/src/pages/platform/ServiceParameterTaxonomiesPage.jsx", "Pets / Animals Parameters"),
        (ROOT / "frontend/src/pages/platform/ServiceParameterTaxonomiesPage.jsx", "Pricing Parameters"),
        (ROOT / "frontend/src/pages/agency/ServiceParameterTaxonomiesPage.jsx", "Knowledge Graph Links"),
        (ROOT / "docs/architecture/service-parameter-taxonomy-integration-foundation.md", "Phase 51.1 does not copy"),
        (ROOT / "docs/architecture/current-model-inventory.md", "service_parameter_taxonomies"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/api/platform/service-parameter-taxonomies"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Service parameter taxonomy integration"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Service Parameter Taxonomies"),
        (ROOT / "docs/architecture/foundations/GLOSSARY.md", "Service Parameter Taxonomy"),
    ]:
        require_text(path, text)

    for path in [
        ROOT / "frontend/src/pages/platform/ServiceParameterTaxonomiesPage.jsx",
        ROOT / "frontend/src/pages/agency/ServiceParameterTaxonomiesPage.jsx",
    ]:
        reject_text(path, "apiPost")
        reject_text(path, "apiPut")
        reject_text(path, "apiDelete")
        for forbidden in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, forbidden)


def verify_metadata_only_code() -> None:
    implementation_paths = [
        ROOT / "backend/services/service_parameter_taxonomy_service.py",
        ROOT / "backend/routers/platform_service_parameter_taxonomies.py",
        ROOT / "backend/routers/agency_service_parameter_taxonomies.py",
        ROOT / "frontend/src/pages/platform/ServiceParameterTaxonomiesPage.jsx",
        ROOT / "frontend/src/pages/agency/ServiceParameterTaxonomiesPage.jsx",
    ]
    forbidden_terms = [
        "BackgroundTasks",
        "httpx",
        "requests.",
        "urllib.",
        "openai",
        "ChatCompletion",
        "airlinePolicyEngine.js",
        "pricingEngine.js",
        "PocketBase",
        "airline_policies",
        "policy_evaluations",
        "live_search",
        "issue_ticket",
        "issue_emd",
        "send_to_client",
    ]
    for path in implementation_paths:
        content = path.read_text(encoding="utf-8")
        for term in forbidden_terms:
            if term in content:
                raise AssertionError(f"{path.relative_to(ROOT)} contains forbidden execution term {term}.")


def assert_created_record(record: dict, reference: str, agency_id: str) -> None:
    if record.get("taxonomy_reference") != reference:
        raise AssertionError(f"Unexpected taxonomy reference: {record}")
    if record.get("agency_id") != agency_id:
        raise AssertionError(f"Unexpected agency scope: {record}")
    for field in PASSENGER_ASSISTANCE_PARAMETER_FIELDS:
        if not record.get(field):
            raise AssertionError(f"Passenger assistance parameter field did not persist: {field}")
    for field in PETS_ANIMALS_PARAMETER_FIELDS:
        if not record.get(field):
            raise AssertionError(f"Pets / animals parameter field did not persist: {field}")
    for field in SPECIAL_ITEM_PARAMETER_FIELDS:
        if not record.get(field):
            raise AssertionError(f"Special item parameter field did not persist: {field}")
    for field in ROUTE_AIRCRAFT_CABIN_PARAMETER_FIELDS:
        if not record.get(field):
            raise AssertionError(f"Route / aircraft / cabin parameter field did not persist: {field}")
    for field in [
        "pricing_units",
        "pricing_way_values",
        "pricing_route_types",
        "pricing_flight_types",
        "pricing_fare_bundles",
        "pricing_categories",
        "amount_types",
        "pricing_basis_parameters",
        "pricing_formula_components",
        "pricing_applicability_parameters",
        "refund_condition_parameters",
        "exchange_condition_parameters",
        "required_reference_collections",
        "required_reference_values",
        "acquisition_ids",
        "normalisation_ids",
        "constraint_ids",
        "knowledge_version_ids",
        "capability_matrix_ids",
        "operational_evaluation_ids",
        "feasibility_ids",
        "recommendation_ids",
        "intelligent_offer_package_ids",
        "operational_intelligence_case_ids",
    ]:
        if not record.get(field):
            raise AssertionError(f"Created taxonomy missing {field}: {record}")
    for summary_field in ["parameter_summary", "vocabulary_summary", "knowledge_graph_link_summary", "governance_summary"]:
        if not isinstance(record.get(summary_field), dict):
            raise AssertionError(f"Projection missing {summary_field}: {record}")
    if not record.get("template_matches"):
        raise AssertionError(f"Projection did not match any default templates: {record}")
    assert_disabled_response(record)


def find_record(payload: dict, reference: str) -> dict:
    for item in payload.get("items") or payload.get("taxonomies") or []:
        if item.get("taxonomy_reference") == reference:
            return item
    raise AssertionError(f"Service parameter taxonomy {reference} not found in payload: {payload}")


def verify_taxonomy_crud_and_filters() -> None:
    post("/api/reference/seed", {}, OWNER_HEADERS)
    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    reference = run_ref("SPT-SMOKE-511")
    payload = taxonomy_payload(agency_id, reference)

    created_response = post(PLATFORM_BASE, payload, OWNER_HEADERS, 201)
    assert_disabled_response(created_response)
    created = created_response.get("service_parameter_taxonomy") or {}
    taxonomy_id = created.get("id")
    if not taxonomy_id:
        raise AssertionError(f"Create response missing taxonomy id: {created_response}")
    assert_created_record(created, reference, agency_id)

    quoted_id = quote(taxonomy_id)
    detail = get(f"{PLATFORM_BASE}/{quoted_id}", OWNER_HEADERS)
    assert_created_record(detail.get("service_parameter_taxonomy") or {}, reference, agency_id)

    updated = put(
        f"{PLATFORM_BASE}/{quoted_id}",
        {
            "taxonomy_status": "approved",
            "review_status": "approved",
            "approval_status": "approved",
            "review_notes": "Smoke taxonomy approved as metadata-only.",
            "pricing_formula_components": [parameter("formula_component", "string", False), parameter("manual_quote_component", "string", False)],
        },
        OWNER_HEADERS,
    )
    updated_record = updated.get("service_parameter_taxonomy") or {}
    if updated_record.get("taxonomy_status") != "approved" or updated_record.get("approval_status") != "approved":
        raise AssertionError(f"Update did not preserve service parameter taxonomy metadata: {updated_record}")
    assert_disabled_response(updated_record)

    query_checks = [
        f"?agency_id={quote(agency_id)}",
        "?taxonomy_status=approved",
        "?policy_family=special_service_policy",
        "?service_family=cross_service_operational_parameters",
        "?service_code=PETC",
        "?parameter_domain=airline_operational_intelligence",
        "?parameter_group=cross_service",
        "?parameter_scope=airline_service_policy_metadata",
        "?review_status=approved",
        "?approval_status=approved",
    ]
    for query in query_checks:
        result = get(f"{PLATFORM_BASE}{query}", OWNER_HEADERS)
        assert_disabled_response(result)
        assert_created_record(find_record(result, reference), reference, agency_id)

    summary = get(f"{PLATFORM_BASE}/summary", OWNER_HEADERS)
    assert_disabled_response(summary)
    for key in [
        "taxonomy_count",
        "by_taxonomy_status",
        "by_review_status",
        "by_approval_status",
        "service_code_count",
        "passenger_assistance_parameter_count",
        "pets_animals_parameter_count",
        "special_item_parameter_count",
        "route_aircraft_cabin_parameter_count",
        "pricing_parameter_count",
        "reference_requirement_count",
        "knowledge_graph_link_count",
        "template_count",
    ]:
        if key not in (summary.get("summary") or {}):
            raise AssertionError(f"Platform summary missing taxonomy count {key}: {summary}")

    agency_base = AGENCY_BASE_TEMPLATE.format(agency_id=quote(agency_id))
    agency_list = get(f"{agency_base}?service_code=PETC&approval_status=approved", OWNER_HEADERS)
    assert_disabled_response(agency_list)
    assert_created_record(find_record(agency_list, reference), reference, agency_id)

    agency_detail = get(f"{agency_base}/{quoted_id}", OWNER_HEADERS)
    assert_disabled_response(agency_detail)
    assert_created_record(agency_detail.get("service_parameter_taxonomy") or {}, reference, agency_id)

    agency_summary = get(f"{agency_base}/summary", OWNER_HEADERS)
    assert_disabled_response(agency_summary)

    agency_reference = run_ref("SPT-AGENCY-SMOKE-511")
    agency_created = post(agency_base, taxonomy_payload(agency_id, agency_reference), OWNER_HEADERS, 201)
    agency_created_record = agency_created.get("service_parameter_taxonomy") or {}
    agency_taxonomy_id = agency_created_record.get("id")
    if not agency_taxonomy_id:
        raise AssertionError(f"Agency create response missing taxonomy id: {agency_created}")
    assert_created_record(agency_created_record, agency_reference, agency_id)
    agency_updated = put(
        f"{agency_base}/{quote(agency_taxonomy_id)}",
        {"taxonomy_status": "approved", "review_status": "approved", "approval_status": "approved"},
        OWNER_HEADERS,
    )
    if (agency_updated.get("service_parameter_taxonomy") or {}).get("taxonomy_status") != "approved":
        raise AssertionError(f"Agency update did not preserve taxonomy status: {agency_updated}")
    agency_archived = request("DELETE", f"{agency_base}/{quote(agency_taxonomy_id)}", None, OWNER_HEADERS)[1]
    if agency_archived.get("archived") is not True:
        raise AssertionError(f"Agency archive did not soft-archive taxonomy metadata: {agency_archived}")

    archived = request("DELETE", f"{PLATFORM_BASE}/{quoted_id}", None, OWNER_HEADERS)[1]
    if archived.get("archived") is not True:
        raise AssertionError(f"Platform archive did not soft-archive taxonomy metadata: {archived}")
    assert_disabled_response(archived)


def verify_readiness_and_blueprint() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected active phase label: {health.get('phase')}")

    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Readiness phase mismatch: {readiness.get('phase')}")
    section = readiness.get("service_parameter_taxonomy_integration_foundation") or {}
    required_flags = [
        "service_parameter_taxonomy_integration_enabled",
        "service_parameter_taxonomies_collection_enabled",
        "platform_service_parameter_taxonomies_metadata_crud_enabled",
        "agency_service_parameter_taxonomies_metadata_crud_enabled",
        "platform_service_parameter_taxonomies_ui_enabled",
        "agency_service_parameter_taxonomies_ui_enabled",
        "measurable_service_parameters_enabled",
        "parameter_taxonomies_reusable",
        "passenger_assistance_parameters_enabled",
        "pets_animals_parameters_enabled",
        "special_items_baggage_parameters_enabled",
        "route_aircraft_cabin_parameters_enabled",
        "pricing_parameters_enabled",
        "reference_requirements_enabled",
        "knowledge_graph_links_enabled",
        "governance_metadata_enabled",
        "live_rule_evaluation_disabled",
        "live_pricing_calculation_disabled",
        "provider_integrations_disabled",
        "background_workers_disabled",
    ]
    for flag in required_flags:
        if section.get(flag) is not True:
            raise AssertionError(f"Readiness section missing {flag}: {section}")

    adoption = get("/api/platform/blueprint/adoption-map", OWNER_HEADERS)
    if adoption.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Adoption phase mismatch: {adoption.get('phase')}")
    if "ServiceParameterTaxonomy" not in str(adoption):
        raise AssertionError(f"Adoption map missing ServiceParameterTaxonomy: {adoption}")

    route_policy = get("/api/platform/blueprint/route-policy", OWNER_HEADERS)
    if route_policy.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Route policy phase mismatch: {route_policy.get('phase')}")
    mappings = route_policy.get("route_mappings") or []
    expected_mappings = [
        ("/admin/service-parameter-taxonomies", "/platform/service-parameter-taxonomies"),
        ("/agent/service-parameter-taxonomies", "/agency/service-parameter-taxonomies"),
    ]
    for supplementary, agencyos in expected_mappings:
        if not any(item.get("supplementary") == supplementary and item.get("agencyos") == agencyos for item in mappings):
            raise AssertionError(f"Route policy missing taxonomy mapping {supplementary} -> {agencyos}: {route_policy}")

    gaps = get("/api/platform/blueprint/gaps", OWNER_HEADERS)
    if "Service parameter taxonomy integration foundation built in Phase 51.1" not in str(gaps):
        raise AssertionError(f"Gap summary missing Phase 51.1 built marker: {gaps}")


def main() -> None:
    verify_model_and_collection_registration()
    verify_router_and_ui_registration()
    verify_metadata_only_code()
    verify_taxonomy_crud_and_filters()
    verify_readiness_and_blueprint()
    print("Phase 51.1 service parameter taxonomy integration smoke passed.")


if __name__ == "__main__":
    main()
