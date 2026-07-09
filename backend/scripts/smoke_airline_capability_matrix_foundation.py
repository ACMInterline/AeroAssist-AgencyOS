#!/usr/bin/env python3
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import AirlineCapabilityMatrixCreate, AirlineCapabilityMatrixRecord
from services.airline_capability_matrix_service import (
    AIRLINE_CAPABILITY_MATRIX_COLLECTION,
    CAPABILITY_OUTCOMES,
    CAPABILITY_REVIEW_STATUSES,
    CAPABILITY_STATUSES,
    CAPABILITY_STATUS_VALUES,
    CONFIDENCE_LEVELS,
    OPERATIONAL_RISK_LEVELS,
    OPERATIONAL_VALIDITY_STATUSES,
    PHASE_LABEL,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_51_2_request_segment_service_precision_foundation"
ROOT = Path(__file__).resolve().parents[2]
PLATFORM_BASE = "/api/platform/airline-capability-matrix"


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
        "live_rule_evaluation_disabled",
        "passenger_feasibility_scoring_disabled",
        "airline_recommendation_ranking_disabled",
        "ai_reasoning_disabled",
        "parser_execution_disabled",
        "pricing_calculation_disabled",
        "provider_integrations_disabled",
        "background_workers_disabled",
        "automatic_publication_disabled",
        "scraping_disabled",
    ]


def assert_disabled_response(payload: dict) -> None:
    if payload.get("metadata_only") is not True:
        raise AssertionError(f"Payload is not metadata-only: {payload}")
    for flag in disabled_flags():
        if payload.get(flag) is not True:
            raise AssertionError(f"Payload missing disabled flag {flag}: {payload}")


def capability_payload(agency_id: str, reference: str) -> dict:
    return {
        "agency_id": agency_id,
        "capability_reference": reference,
        "capability_status": "under_review",
        "capability_version": "50.5.0-smoke",
        "capability_name": "Phase 50.5 PETC capability metadata",
        "capability_description": "Metadata-only operational capability record for PETC handling.",
        "airline_code": "LH",
        "airline_name": "Lufthansa",
        "validating_carrier": "LH",
        "operating_carrier": "LH",
        "marketing_carrier": "LH",
        "knowledge_version_ids": ["AKV-SMOKE-505"],
        "knowledge_release_ids": ["AKR-SMOKE-505"],
        "acquisition_ids": ["AKA-SMOKE-505"],
        "normalisation_ids": ["AKN-SMOKE-505"],
        "constraint_ids": ["OC-SMOKE-505"],
        "evidence_reference_ids": ["EVID-SMOKE-505"],
        "service_domain": "animal_transport",
        "service_family": "pet_transport",
        "service_variant": "pet_in_cabin",
        "passenger_need_category": "travel_with_pet",
        "ssr_code": "PETC",
        "osi_relevance": "pet-in-cabin operational note",
        "rfic": "C",
        "rfisc": "0BT",
        "emd_relevance": "associated_optional_service_metadata",
        "document_relevance": "pet_passport_metadata",
        "capability_type": "animal_transport",
        "capability_status_value": "conditional",
        "capability_outcome": "conditional_delivery",
        "capability_reason": "Capability depends on aircraft, cabin, station, and carrier dimensions.",
        "capability_confidence": "official",
        "capability_source_type": "governed_knowledge_release",
        "capability_review_status": "under_review",
        "operational_validity_status": "valid",
        "operational_validity_confidence": "high",
        "aircraft_applicability": ["A320", "A321"],
        "aircraft_family": "A320 Family",
        "aircraft_subtype": "A320neo",
        "aircraft_configuration": "single_aisle",
        "cabin_applicability": ["Economy", "Premium Economy"],
        "cabin_family": "Economy",
        "cabin_name": "Economy Classic",
        "seat_type": "standard",
        "seat_map_relevance": "under_seat_space",
        "adjacent_seat_available": True,
        "adjacent_seat_required": False,
        "fixed_armrests": False,
        "movable_armrests": True,
        "bulkhead_restriction": "not_allowed_for_petc",
        "exit_row_restriction": "not_allowed_for_petc",
        "under_seat_space_available": True,
        "under_seat_space_notes": "Carrier must fit under seat.",
        "accessible_lavatory_available": False,
        "onboard_wheelchair_capability": "not_relevant",
        "cabin_notes": "Cabin metadata only.",
        "airport_applicability": ["FRA", "SOF", "CDG"],
        "station_applicability": ["FRA-Station"],
        "origin_airport_applicability": ["SOF"],
        "destination_airport_applicability": ["FRA"],
        "transit_airport_applicability": ["CDG"],
        "ground_handling_capability": "station_review_required",
        "airport_handling_required": True,
        "station_notification_required": True,
        "airport_restriction_notes": "Station capability metadata only.",
        "route_applicability": ["SOF-FRA"],
        "origin_country_applicability": ["BG"],
        "destination_country_applicability": ["DE"],
        "transit_country_applicability": ["FR"],
        "seasonal_applicability": ["summer_2028"],
        "date_range_applicability": [{"start": "2028-05-01", "end": "2029-05-01"}],
        "event_based_applicability": ["heat_embargo_review"],
        "embargo_applicability": ["temperature_embargo"],
        "weather_temperature_relevance": "temperature_sensitive",
        "interline_allowed": False,
        "codeshare_allowed": False,
        "operating_carrier_control_required": True,
        "validating_carrier_control_required": True,
        "marketing_carrier_restriction_notes": "Operating carrier confirmation metadata.",
        "animal_transport_applicable": True,
        "petc_capability": "conditional",
        "avih_capability": "restricted",
        "species_applicability": ["cat", "dog"],
        "breed_applicability": ["non_brachycephalic"],
        "brachycephalic_capability": "restricted",
        "carrier_dimension_capability": "55x40x23cm",
        "carrier_weight_capability": "8kg_with_container",
        "pet_under_seat_capability": "required",
        "pet_on_adjacent_extra_seat_capability": "not_allowed",
        "animal_transport_notes": "No airline call or validation is performed.",
        "extra_seat_applicable": True,
        "extra_seat_available": True,
        "extra_seat_reason": "comfort",
        "passenger_of_size_capability": "manual_review",
        "comfort_extra_seat_capability": "conditional",
        "cbbg_capability": "manual_review",
        "musical_instrument_extra_seat_capability": "conditional",
        "medical_extra_seat_capability": "manual_review",
        "adjacent_extra_seat_capability": "conditional",
        "extra_seat_cabin_restriction_notes": "Cabin metadata only.",
        "extra_seat_refund_capability_notes": "Pricing and refund metadata are not evaluated.",
        "wheelchair_capability": "available",
        "wchr_capability": "available",
        "wchs_capability": "available",
        "wchc_capability": "manual_review",
        "medif_capability": "manual_review",
        "oxygen_capability": "manual_review",
        "stretcher_capability": "restricted",
        "medical_equipment_capability": "conditional",
        "reduced_mobility_notes": "Medical/accessibility metadata only.",
        "approval_required": True,
        "document_required": True,
        "emd_required": True,
        "ssr_required": True,
        "osi_required": True,
        "medif_required": False,
        "advance_notice_required": True,
        "advance_notice_hours": 48,
        "crew_notification_required": True,
        "operational_procedure_required": True,
        "manual_review_required": True,
        "operational_risk_level": "medium",
        "operational_risk_reason": "Station and weather conditions affect delivery.",
        "data_confidence_level": "high",
        "evidence_confidence_level": "official",
        "last_operational_confirmation_date": "2028-05-15T09:00:00Z",
        "operational_confirmation_source": "governed_release_metadata",
        "effective_from": "2028-05-01T00:00:00Z",
        "effective_until": "2029-05-01T00:00:00Z",
        "superseded_by_capability_id": None,
        "supersedes_capability_ids": ["ACM-SUPERSEDED-SMOKE"],
        "operational_notes": "Capability inventory metadata only.",
        "internal_notes": "No evaluation, scoring, ranking, AI reasoning, parser execution, pricing calculation, provider integration, scraping, worker, or publication action.",
        "metadata": {"smoke": True, "metadata_only": True},
    }


def verify_model_and_collection_registration() -> None:
    if AIRLINE_CAPABILITY_MATRIX_COLLECTION not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("airline_capability_matrix is not registered as agency-owned metadata.")
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Service phase label mismatch: {PHASE_LABEL}")

    payload = capability_payload("agency-smoke", "ACM-SMOKE-MODEL")
    create_model = AirlineCapabilityMatrixCreate(**payload)
    record = AirlineCapabilityMatrixRecord(**create_model.model_dump(mode="json", exclude_none=True))
    if record.capability_reference != "ACM-SMOKE-MODEL":
        raise AssertionError("Capability matrix model did not preserve reference metadata.")
    if record.capability_status_value != "conditional" or record.capability_outcome != "conditional_delivery":
        raise AssertionError("Capability matrix model did not preserve capability outcome metadata.")
    if record.aircraft_family != "A320 Family" or "FRA" not in record.airport_applicability:
        raise AssertionError("Capability matrix model did not preserve operational dimensions.")
    if record.metadata_only is not True or record.passenger_feasibility_scoring_disabled is not True:
        raise AssertionError("Capability matrix model is not metadata-only.")

    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "airline_capability_matrix_id_unique",
        "airline_capability_matrix_reference_unique",
        "airline_capability_matrix_agency_status_lookup",
        "airline_capability_matrix_airline_lookup",
        "airline_capability_matrix_knowledge_version_lookup",
        "airline_capability_matrix_service_lookup",
        "airline_capability_matrix_ssr_rfic_lookup",
        "airline_capability_matrix_capability_type_status_lookup",
        "airline_capability_matrix_aircraft_lookup",
        "airline_capability_matrix_cabin_lookup",
        "airline_capability_matrix_airport_lookup",
        "airline_capability_matrix_route_lookup",
        "airline_capability_matrix_animal_transport_lookup",
        "airline_capability_matrix_extra_seat_lookup",
        "airline_capability_matrix_medical_accessibility_lookup",
        "airline_capability_matrix_requirements_lookup",
        "airline_capability_matrix_risk_lookup",
        "airline_capability_matrix_effective_window_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Airline capability matrix index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    expected_methods = {
        "/api/platform/airline-capability-matrix": {"get", "post"},
        "/api/platform/airline-capability-matrix/summary": {"get"},
        "/api/platform/airline-capability-matrix/{capability_id}": {"get", "put", "delete"},
        "/api/agencies/{agency_id}/airline-capability-matrix": {"get"},
        "/api/agencies/{agency_id}/airline-capability-matrix/summary": {"get"},
        "/api/agencies/{agency_id}/airline-capability-matrix/{capability_id}": {"get"},
    }
    for path, methods in expected_methods.items():
        for method in methods:
            assert_openapi_path(paths, path, method)

    for path in [
        "/api/agencies/{agency_id}/airline-capability-matrix",
        "/api/agencies/{agency_id}/airline-capability-matrix/summary",
        "/api/agencies/{agency_id}/airline-capability-matrix/{capability_id}",
    ]:
        blocked_methods = set(paths.get(path, {}).keys()) & {"post", "put", "patch", "delete"}
        if blocked_methods:
            raise AssertionError(f"Agency capability matrix route is not read-only: {path} {sorted(blocked_methods)}")

    for path in paths:
        if "airline-capability-matrix" in path and any(term in path for term in ["evaluate", "execute", "score", "rank", "pricing", "publish"]):
            raise AssertionError(f"Execution route should not exist for capability matrix: {path}")
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/App.jsx", "/platform/airline-capability-matrix"),
        (ROOT / "frontend/src/App.jsx", "/agency/capability-matrix"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Airline Capability Matrix"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Capability Matrix"),
        (ROOT / "frontend/src/pages/platform/AirlineCapabilityMatrixPage.jsx", "Capability is different from policy"),
        (ROOT / "frontend/src/pages/platform/AirlineCapabilityMatrixPage.jsx", "Knowledge Governance Links"),
        (ROOT / "frontend/src/pages/platform/AirlineCapabilityMatrixPage.jsx", "Aircraft / Cabin Capability"),
        (ROOT / "frontend/src/pages/platform/AirlineCapabilityMatrixPage.jsx", "Airport / Station Capability"),
        (ROOT / "frontend/src/pages/platform/AirlineCapabilityMatrixPage.jsx", "Route / Country / Season Capability"),
        (ROOT / "frontend/src/pages/platform/AirlineCapabilityMatrixPage.jsx", "Animal Transport Capability"),
        (ROOT / "frontend/src/pages/platform/AirlineCapabilityMatrixPage.jsx", "Extra Seat / EXST Capability"),
        (ROOT / "frontend/src/pages/platform/AirlineCapabilityMatrixPage.jsx", "Medical / Accessibility Capability"),
        (ROOT / "frontend/src/pages/platform/AirlineCapabilityMatrixPage.jsx", "Operational Requirements"),
        (ROOT / "frontend/src/pages/agency/CapabilityMatrixPage.jsx", "Read-only metadata inventory"),
        (ROOT / "docs/architecture/airline-operational-capability-matrix-foundation.md", "Capability is different from Policy"),
        (ROOT / "docs/architecture/airline-operational-capability-matrix-foundation.md", "Phase 50.6 consumes the matrix"),
        (ROOT / "docs/architecture/airline-operational-capability-matrix-foundation.md", "Phase 50.7 consumes Operational Evaluation Results"),
        (ROOT / "docs/architecture/current-model-inventory.md", "airline_capability_matrix"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/api/platform/airline-capability-matrix"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/api/agencies/{agency_id}/airline-capability-matrix"),
        (ROOT / "docs/architecture/airline-operational-intelligence-engine-foundation.md", "Phase 50.5"),
        (ROOT / "docs/architecture/airline-knowledge-acquisition-workspace-foundation.md", "Phase 50.5"),
        (ROOT / "docs/architecture/operational-constraint-engine-foundation.md", "Phase 50.5"),
        (ROOT / "docs/architecture/airline-knowledge-normalisation-foundation.md", "Phase 50.5"),
        (ROOT / "docs/architecture/airline-operational-knowledge-governance-foundation.md", "Phase 50.5 Consumer"),
        (ROOT / "docs/architecture/passenger-service-operations-principle.md", "Phase 50.5"),
        (ROOT / "docs/architecture/foundations/AIRLINE_OPERATIONAL_KNOWLEDGE_BLUEPRINT.md", "50.5 Airline Operational Capability Matrix"),
        (ROOT / "docs/architecture/foundations/AEROASSIST_ENGINEERING_PRINCIPLES.md", "Capability Matrix"),
        (ROOT / "docs/architecture/foundations/GLOSSARY.md", "Capability Matrix"),
        (ROOT / "README.md", "Phase 50.5"),
        (ROOT / "BUILD_PHASES.md", "Phase 50.5"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Airline Operational Capability Matrix Foundation"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Airline Capability Matrix"),
    ]:
        require_text(path, text)

    for path, text in [
        (ROOT / "frontend/src/pages/platform/AirlineCapabilityMatrixPage.jsx", "apiPost"),
        (ROOT / "frontend/src/pages/platform/AirlineCapabilityMatrixPage.jsx", "apiPut"),
        (ROOT / "frontend/src/pages/platform/AirlineCapabilityMatrixPage.jsx", "apiDelete"),
        (ROOT / "frontend/src/pages/agency/CapabilityMatrixPage.jsx", "apiPost"),
        (ROOT / "frontend/src/pages/agency/CapabilityMatrixPage.jsx", "apiPut"),
        (ROOT / "frontend/src/pages/agency/CapabilityMatrixPage.jsx", "apiDelete"),
    ]:
        reject_text(path, text)


def verify_metadata_only_implementation() -> None:
    checked_files = [
        ROOT / "backend/services/airline_capability_matrix_service.py",
        ROOT / "backend/routers/platform_airline_capability_matrix.py",
        ROOT / "backend/routers/agency_airline_capability_matrix.py",
        ROOT / "frontend/src/pages/platform/AirlineCapabilityMatrixPage.jsx",
        ROOT / "frontend/src/pages/agency/CapabilityMatrixPage.jsx",
    ]
    forbidden_terms = [
        "BackgroundTasks",
        "httpx",
        "requests.",
        "urllib.",
        "openai",
        "AsyncClient",
        "Scheduler",
        "schedule.",
        "scrapy",
        "selenium",
        "BeautifulSoup",
        "crawl(",
        "scrape(",
        "evaluate_rules(",
        "run_evaluation(",
        "score_feasibility(",
        "rank_airlines(",
        "recommend_airline(",
        "execute_parser(",
        "calculate_price(",
        "provider_client",
        "publish_capability(",
    ]
    for path in checked_files:
        content = path.read_text(encoding="utf-8")
        for term in forbidden_terms:
            if term in content:
                raise AssertionError(f"Forbidden implementation term {term!r} found in {path.relative_to(ROOT)}")


def verify_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase label: {health.get('phase')}")

    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase label: {readiness.get('phase')}")
    matrix = readiness.get("airline_operational_capability_matrix_foundation") or {}
    for key in [
        "airline_operational_capability_matrix_enabled",
        "airline_capability_matrix_collection_enabled",
        "platform_airline_capability_matrix_metadata_crud_enabled",
        "agency_airline_capability_matrix_read_only_enabled",
        "platform_airline_capability_matrix_ui_enabled",
        "agency_capability_matrix_ui_enabled",
        "capability_is_distinct_from_policy",
        "knowledge_governance_links_enabled",
        "airline_service_capability_metadata_enabled",
        "aircraft_cabin_capability_metadata_enabled",
        "airport_station_capability_metadata_enabled",
        "route_country_season_capability_metadata_enabled",
        "interline_codeshare_capability_metadata_enabled",
        "animal_transport_capability_metadata_enabled",
        "extra_seat_capability_metadata_enabled",
        "medical_accessibility_capability_metadata_enabled",
        "operational_requirements_metadata_enabled",
        "risk_confidence_metadata_enabled",
        "lifecycle_metadata_enabled",
        "future_50_6_rule_evaluation_consumer_only",
        "future_50_7_feasibility_consumer_only",
        *disabled_flags(),
    ]:
        if matrix.get(key) is not True:
            raise AssertionError(f"Readiness missing capability matrix flag {key}: {matrix}")
    if matrix.get("readiness_required") is not False:
        raise AssertionError("Capability matrix foundation should not be deployment-readiness required.")
    if matrix.get("capability_statuses") != CAPABILITY_STATUSES:
        raise AssertionError("Readiness did not expose capability statuses.")
    if matrix.get("capability_status_values") != CAPABILITY_STATUS_VALUES:
        raise AssertionError("Readiness did not expose capability status values.")
    if matrix.get("capability_outcomes") != CAPABILITY_OUTCOMES:
        raise AssertionError("Readiness did not expose capability outcomes.")
    if matrix.get("capability_review_statuses") != CAPABILITY_REVIEW_STATUSES:
        raise AssertionError("Readiness did not expose capability review statuses.")
    if matrix.get("operational_validity_statuses") != OPERATIONAL_VALIDITY_STATUSES:
        raise AssertionError("Readiness did not expose operational validity statuses.")
    if matrix.get("confidence_levels") != CONFIDENCE_LEVELS:
        raise AssertionError("Readiness did not expose confidence levels.")
    if matrix.get("operational_risk_levels") != OPERATIONAL_RISK_LEVELS:
        raise AssertionError("Readiness did not expose operational risk levels.")
    for key in [
        "airline_capability_matrix_count",
        "airline_capability_matrix_status_counts",
        "airline_capability_matrix_status_value_counts",
        "airline_capability_matrix_outcome_counts",
        "airline_capability_matrix_review_status_counts",
        "airline_capability_matrix_validity_status_counts",
        "airline_capability_matrix_risk_counts",
        "airline_capability_matrix_confidence_counts",
        "airline_capability_matrix_airline_count",
        "airline_capability_matrix_service_domain_count",
        "airline_capability_matrix_governance_link_count",
        "airline_capability_matrix_aircraft_cabin_count",
        "airline_capability_matrix_airport_station_count",
        "airline_capability_matrix_route_country_season_count",
        "airline_capability_matrix_animal_transport_count",
        "airline_capability_matrix_extra_seat_count",
        "airline_capability_matrix_medical_accessibility_count",
        "airline_capability_matrix_manual_review_required_count",
    ]:
        if key not in matrix:
            raise AssertionError(f"Readiness missing capability matrix count {key}: {matrix}")


def verify_blueprint_adoption() -> None:
    adoption = get("/api/platform/blueprint/adoption-map", OWNER_HEADERS)
    categories = {item.get("category") for item in adoption.get("items", [])}
    if "Airline Capability Matrix" not in categories:
        raise AssertionError("Blueprint adoption map missing Airline Capability Matrix.")

    route_policy = get("/api/platform/blueprint/route-policy", OWNER_HEADERS)
    mappings = route_policy.get("route_mappings") or []
    expected_pairs = {
        ("/admin/airline-capability-matrix", "/platform/airline-capability-matrix"),
        ("/agent/capability-matrix", "/agency/capability-matrix"),
    }
    actual_pairs = {(item.get("supplementary"), item.get("agencyos")) for item in mappings}
    missing = expected_pairs - actual_pairs
    if missing:
        raise AssertionError(f"Route policy missing capability matrix canonical mappings: {missing}")

    gaps = get("/api/platform/blueprint/gaps", OWNER_HEADERS)
    if "Airline operational capability matrix foundation built in Phase 50.5" not in gaps.get("already_built", []):
        raise AssertionError(f"Gap summary missing Phase 50.5 capability matrix marker: {gaps}")
    if "Phase 50.9" not in gaps.get("next_intelligence_phase", ""):
        raise AssertionError(f"Gap summary missing Phase 50.9 next intelligence phase: {gaps}")

    next_phases = get("/api/platform/blueprint/next-phases", OWNER_HEADERS)
    if not next_phases.get("items") or next_phases["items"][0].get("phase") != "Phase 50.9":
        raise AssertionError(f"Next recommendations did not start with Phase 50.9: {next_phases}")


def assert_created_record(record: dict, reference: str, agency_id: str) -> None:
    if record.get("capability_reference") != reference:
        raise AssertionError(f"Unexpected capability reference: {record}")
    if record.get("agency_id") != agency_id:
        raise AssertionError(f"Unexpected agency scope: {record}")
    for field in [
        "knowledge_version_ids",
        "knowledge_release_ids",
        "acquisition_ids",
        "normalisation_ids",
        "constraint_ids",
        "evidence_reference_ids",
        "aircraft_applicability",
        "cabin_applicability",
        "airport_applicability",
        "route_applicability",
        "seasonal_applicability",
        "date_range_applicability",
        "species_applicability",
        "breed_applicability",
    ]:
        if not record.get(field):
            raise AssertionError(f"Capability record missing metadata dimension {field}: {record}")
    if record.get("capability_status_value") != "conditional":
        raise AssertionError(f"Capability status value was not preserved: {record}")
    if record.get("capability_outcome") != "conditional_delivery":
        raise AssertionError(f"Capability outcome was not preserved: {record}")
    if not record.get("knowledge_governance_summary") or not record.get("operational_dimension_summary"):
        raise AssertionError(f"Capability projection missing summaries: {record}")
    assert_disabled_response(record)


def verify_filter(path: str, capability_id: str) -> None:
    response = get(path, OWNER_HEADERS)
    assert_disabled_response(response)
    item_ids = {item.get("id") for item in response.get("items", [])}
    if capability_id not in item_ids:
        raise AssertionError(f"Filter did not return capability {capability_id}: {path} -> {response}")


def verify_endpoints() -> None:
    post("/api/reference/seed", {}, OWNER_HEADERS)
    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    reference = run_ref("ACM-SMOKE")
    created = post(PLATFORM_BASE, capability_payload(agency_id, reference), OWNER_HEADERS, 201)
    assert_disabled_response(created)
    record = created.get("airline_capability_matrix_record") or {}
    capability_id = record.get("id")
    if not capability_id:
        raise AssertionError(f"Created capability matrix response missing id: {created}")
    assert_created_record(record, reference, agency_id)

    updated = put(
        f"{PLATFORM_BASE}/{capability_id}",
        {
            "capability_status": "active",
            "capability_status_value": "available",
            "capability_outcome": "can_deliver",
            "capability_review_status": "reviewed",
            "operational_validity_status": "valid",
            "manual_review_required": False,
            "operational_notes": "Reviewed metadata only.",
        },
        OWNER_HEADERS,
    )
    assert_disabled_response(updated)
    updated_record = updated.get("airline_capability_matrix_record") or {}
    if updated_record.get("capability_status") != "active":
        raise AssertionError(f"Update did not persist active status: {updated}")
    if updated_record.get("capability_outcome") != "can_deliver":
        raise AssertionError(f"Update did not persist capability outcome: {updated}")

    for query in [
        f"agency_id={agency_id}",
        "airline=LH",
        "service_domain=animal_transport",
        "service_family=pet_transport",
        "ssr_code=PETC",
        "rfic=C",
        "rfisc=0BT",
        "aircraft_family=A320%20Family",
        "cabin=Economy",
        "airport=FRA",
        "route=SOF-FRA",
        "country=DE",
        "season=summer_2028",
        "capability_status=active",
        "operational_risk=medium",
        "confidence_level=official",
        "effective_date=2028-06-01",
    ]:
        verify_filter(f"{PLATFORM_BASE}?{query}", capability_id)

    platform_summary = get(f"{PLATFORM_BASE}/summary", OWNER_HEADERS)
    assert_disabled_response(platform_summary)
    if "by_capability_status" not in platform_summary.get("summary", {}):
        raise AssertionError(f"Platform summary missing capability status counts: {platform_summary}")

    platform_detail = get(f"{PLATFORM_BASE}/{reference}", OWNER_HEADERS)
    assert_disabled_response(platform_detail)
    if platform_detail.get("airline_capability_matrix_record", {}).get("id") != capability_id:
        raise AssertionError(f"Platform detail lookup by reference failed: {platform_detail}")

    agency_base = f"/api/agencies/{agency_id}/airline-capability-matrix"
    for query in [
        "airline=LH",
        "service_domain=animal_transport",
        "service_family=pet_transport",
        "ssr_code=PETC",
        "rfic=C",
        "rfisc=0BT",
        "aircraft_family=A320%20Family",
        "cabin=Economy",
        "airport=FRA",
        "route=SOF-FRA",
        "country=DE",
        "season=summer_2028",
        "capability_status=active",
        "operational_risk=medium",
        "confidence_level=official",
        "effective_date=2028-06-01",
    ]:
        verify_filter(f"{agency_base}?{query}", capability_id)

    agency_list = get(agency_base, OWNER_HEADERS)
    assert_disabled_response(agency_list)
    if agency_list.get("read_only") is not True:
        raise AssertionError(f"Agency list is not marked read-only: {agency_list}")
    agency_items = [item for item in agency_list.get("items", []) if item.get("id") == capability_id]
    if not agency_items or agency_items[0].get("read_only") is not True:
        raise AssertionError(f"Agency item is not read-only: {agency_list}")

    agency_summary = get(f"{agency_base}/summary", OWNER_HEADERS)
    assert_disabled_response(agency_summary)
    if agency_summary.get("read_only") is not True:
        raise AssertionError(f"Agency summary is not read-only: {agency_summary}")

    agency_detail = get(f"{agency_base}/{capability_id}", OWNER_HEADERS)
    assert_disabled_response(agency_detail)
    if agency_detail.get("airline_capability_matrix_record", {}).get("read_only") is not True:
        raise AssertionError(f"Agency detail is not read-only: {agency_detail}")

    request("POST", agency_base, capability_payload(agency_id, run_ref("ACM-BLOCKED")), OWNER_HEADERS, 405)
    request("PUT", f"{agency_base}/{capability_id}", {"capability_status": "archived"}, OWNER_HEADERS, 405)
    request("DELETE", f"{agency_base}/{capability_id}", None, OWNER_HEADERS, 405)

    deleted = request("DELETE", f"{PLATFORM_BASE}/{capability_id}", None, OWNER_HEADERS)[1]
    assert_disabled_response(deleted)
    if deleted.get("archived") is not True or deleted.get("physical_delete_disabled") is not True:
        raise AssertionError(f"Platform delete should soft-archive metadata only: {deleted}")
    archived = deleted.get("airline_capability_matrix_record") or {}
    if archived.get("capability_status") != "archived" or not archived.get("deleted_at"):
        raise AssertionError(f"Soft archive did not mark archived metadata: {deleted}")


def main() -> int:
    verify_model_and_collection_registration()
    verify_metadata_only_implementation()
    verify_frontend_and_docs()

    openapi = get("/openapi.json")
    verify_routes(openapi.get("paths") or {})
    verify_readiness()
    verify_blueprint_adoption()
    verify_endpoints()

    print("Phase 50.5 airline operational capability matrix foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
