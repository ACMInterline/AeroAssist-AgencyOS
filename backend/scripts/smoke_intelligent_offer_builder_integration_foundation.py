#!/usr/bin/env python3
import sys
import time
from pathlib import Path
from urllib.parse import quote

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import IntelligentOfferBuilderPackage, IntelligentOfferBuilderPackageCreate
from services.intelligent_offer_builder_service import (
    INTELLIGENT_OFFER_BUILDER_COLLECTION,
    INTELLIGENT_OFFER_CLIENT_VISIBILITY_STATUSES,
    INTELLIGENT_OFFER_PACKAGE_STATUSES,
    INTELLIGENT_OFFER_READINESS_STATUSES,
    PHASE_LABEL,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_54_8_operations_command_center_foundation"
ROOT = Path(__file__).resolve().parents[2]
PLATFORM_BASE = "/api/platform/intelligent-offer-builder"
AGENCY_BASE_TEMPLATE = "/api/agencies/{agency_id}/offer-intelligence"


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
        "no_live_gds_search",
        "no_ndc_search",
        "flight_search_disabled",
        "booking_disabled",
        "ticketing_disabled",
        "emd_issuance_disabled",
        "provider_integrations_disabled",
        "parser_execution_disabled",
        "no_ai_generation",
        "no_llm_generation",
        "background_workers_disabled",
        "automatic_sending_disabled",
    ]


def assert_disabled_response(payload: dict) -> None:
    if payload.get("metadata_only") is not True:
        raise AssertionError(f"Payload is not metadata-only: {payload}")
    if payload.get("advisory_only") is not True or payload.get("human_authority_final") is not True:
        raise AssertionError(f"Payload is not advisory/human-reviewed metadata: {payload}")
    if payload.get("offer_builder_should_not_invent_intelligence") is not True:
        raise AssertionError(f"Payload does not preserve consumer-only offer builder boundary: {payload}")
    for flag in disabled_flags():
        if payload.get(flag) is not True:
            raise AssertionError(f"Payload missing disabled flag {flag}: {payload}")


def package_payload(agency_id: str, reference: str) -> dict:
    return {
        "agency_id": agency_id,
        "offer_intelligence_reference": reference,
        "package_status": "in_review",
        "package_version": "50.9.0-smoke",
        "passenger_workspace_id": "PAX-WS-SMOKE-509",
        "passenger_profile_reference": "PSG-SMOKE-509",
        "passenger_need_summary": "Passenger needs PETC with document review, station handling, and manual approval metadata.",
        "passenger_requirements": [{"type": "pet_in_cabin", "ssr": "PETC", "evidence_required": True}],
        "travel_request_id": "TR-SMOKE-509",
        "trip_workspace_id": "TRIP-SMOKE-509",
        "flight_workspace_ids": ["FLT-WS-SMOKE-509"],
        "itinerary_summary": "SOF-MUC-FRA itinerary with PETC support metadata.",
        "origin": "SOF",
        "destination": "FRA",
        "transit_points": ["MUC"],
        "travel_date": "2028-07-01",
        "cabin_requested": "Economy",
        "offer_workspace_id": "OFF-WS-SMOKE-509",
        "offer_reference": "OFFER-SMOKE-509",
        "offer_option_ids": ["OPT-SMOKE-509-A", "OPT-SMOKE-509-B"],
        "offer_status": "draft",
        "client_visibility_status": "agent_review",
        "recommendation_ids": ["ARE-SMOKE-508"],
        "feasibility_ids": ["PSF-SMOKE-507"],
        "operational_evaluation_ids": ["OKE-SMOKE-506"],
        "capability_matrix_ids": ["ACM-SMOKE-505"],
        "knowledge_version_ids": ["AKV-SMOKE-504"],
        "evidence_reference_ids": ["EVID-SMOKE-504"],
        "recommended_airlines": ["LH"],
        "recommended_itineraries": ["ITIN-SMOKE-509"],
        "recommendation_rankings": [{"rank": 1, "airline": "LH", "itinerary": "ITIN-SMOKE-509"}],
        "recommendation_scores": [{"airline": "LH", "score": 91}],
        "recommendation_levels": ["highly_recommended"],
        "recommendation_reasons": ["Strong PETC feasibility and station handling evidence."],
        "readiness_status": "conditional",
        "readiness_summary": "Ready for agent review after PETC approval and document check.",
        "readiness_blockers": ["Airline approval must be recorded before client presentation."],
        "readiness_warnings": ["Ancillary cost reference remains non-binding metadata."],
        "readiness_conditions": ["Confirm pet passport", "Record station notification"],
        "operational_risk_level": "medium",
        "required_ssrs": ["PETC"],
        "required_osis": ["PET IN CABIN REVIEW REQUIRED"],
        "required_emds": ["RFIC-C-RFISC-0BT"],
        "required_documents": ["pet_passport", "vaccination_certificate"],
        "required_medif": False,
        "required_airline_approval": True,
        "required_station_notification": True,
        "required_crew_notification": True,
        "required_manual_review": True,
        "required_follow_up_tasks": ["Confirm PETC approval", "Attach pet documentation"],
        "ticket_cost_reference": "TICKET-COST-REF-SMOKE-509",
        "ancillary_cost_reference": "ANC-COST-REF-SMOKE-509",
        "total_cost_reference": "TOTAL-COST-REF-SMOKE-509",
        "pricing_notes": "Pricing references are metadata only and do not calculate fares.",
        "refund_condition_references": ["REFUND-COND-SMOKE-509"],
        "exchange_condition_references": ["EXCHANGE-COND-SMOKE-509"],
        "client_explanation_summary": "LH is currently the strongest reviewed option, subject to PETC approval and documents.",
        "client_visible_reasons": ["Reviewed PETC capability metadata", "Clear station handling path"],
        "client_visible_limitations": ["Airline approval remains required"],
        "client_visible_conditions": ["Provide pet passport", "Await airline PETC confirmation"],
        "client_visible_documents": ["pet_passport", "vaccination_certificate"],
        "client_visible_price_notes": ["Ancillary cost reference is not a live quote"],
        "internal_operational_reasoning": "Package consumes approved recommendation, feasibility, evaluation, capability, and evidence metadata only.",
        "internal_risk_notes": "Medium risk until airline approval is recorded.",
        "internal_evidence_trace": [{"evidence_id": "EVID-SMOKE-504", "supports": "PETC capability"}],
        "internal_decision_trace": [{"step": "recommendation_consumed", "input": "ARE-SMOKE-508"}],
        "decision_pack_ready": True,
        "decision_pack_reference": "ODP-SMOKE-509",
        "decision_pack_summary": "Decision support metadata for human offer review.",
        "decision_pack_sections": [{"title": "Recommendation", "source": "ARE-SMOKE-508"}],
        "decision_pack_evidence": [{"evidence_id": "EVID-SMOKE-504", "source": "knowledge_governance"}],
        "prepared_for_offer_builder": True,
        "reviewed_by_agent": True,
        "approved_for_client_presentation": False,
        "internal_notes": "No live search, booking, ticketing, EMD issuance, provider call, parser execution, AI generation, worker, or automatic sending.",
        "agent_notes": "Human review required before client presentation.",
        "metadata": {"smoke": True, "metadata_only": True},
    }


def verify_model_and_collection_registration() -> None:
    if INTELLIGENT_OFFER_BUILDER_COLLECTION not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("intelligent_offer_builder_packages is not registered as agency-owned metadata.")
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Service phase label mismatch: {PHASE_LABEL}")

    payload = package_payload("agency-smoke", "IOB-SMOKE-MODEL")
    create_model = IntelligentOfferBuilderPackageCreate(**payload)
    record = IntelligentOfferBuilderPackage(**create_model.model_dump(mode="json", exclude_none=True))
    if record.offer_intelligence_reference != "IOB-SMOKE-MODEL":
        raise AssertionError("Offer intelligence model did not preserve reference metadata.")
    if not record.recommendation_ids or not record.feasibility_ids or not record.operational_evaluation_ids:
        raise AssertionError("Offer intelligence model did not preserve intelligence input links.")
    if not record.required_ssrs or not record.client_visible_reasons or not record.internal_evidence_trace:
        raise AssertionError("Offer intelligence model did not preserve required action and explanation metadata.")
    if record.metadata_only is not True or record.booking_disabled is not True or record.automatic_sending_disabled is not True:
        raise AssertionError("Offer intelligence model is not metadata-only.")

    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "intelligent_offer_builder_packages_id_unique",
        "intelligent_offer_builder_packages_reference_unique",
        "intelligent_offer_builder_packages_agency_status_lookup",
        "intelligent_offer_builder_packages_recommendation_lookup",
        "intelligent_offer_builder_packages_feasibility_lookup",
        "intelligent_offer_builder_packages_operational_evaluation_lookup",
        "intelligent_offer_builder_packages_capability_matrix_lookup",
        "intelligent_offer_builder_packages_evidence_lookup",
        "intelligent_offer_builder_packages_required_ssr_lookup",
        "intelligent_offer_builder_packages_decision_pack_ready_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Database index registration missing {index_name}.")

    for value in ["draft", "in_review", "ready", "approved", "archived"]:
        if value not in INTELLIGENT_OFFER_PACKAGE_STATUSES:
            raise AssertionError(f"Missing package status {value}.")
    for value in ["ready", "conditional", "blocked", "needs_review", "unknown"]:
        if value not in INTELLIGENT_OFFER_READINESS_STATUSES:
            raise AssertionError(f"Missing readiness status {value}.")
    for value in ["internal", "agent_review", "client_ready", "client_visible", "hidden"]:
        if value not in INTELLIGENT_OFFER_CLIENT_VISIBILITY_STATUSES:
            raise AssertionError(f"Missing client visibility status {value}.")


def verify_router_and_ui_registration() -> None:
    openapi = get("/openapi.json", OWNER_HEADERS)
    paths = openapi.get("paths", {})
    for path, method in [
        (PLATFORM_BASE, "get"),
        (PLATFORM_BASE, "post"),
        (f"{PLATFORM_BASE}/summary", "get"),
        (f"{PLATFORM_BASE}/{{package_id}}", "get"),
        (f"{PLATFORM_BASE}/{{package_id}}", "put"),
        (f"{PLATFORM_BASE}/{{package_id}}", "delete"),
        ("/api/agencies/{agency_id}/offer-intelligence", "get"),
        ("/api/agencies/{agency_id}/offer-intelligence", "post"),
        ("/api/agencies/{agency_id}/offer-intelligence/summary", "get"),
        ("/api/agencies/{agency_id}/offer-intelligence/{package_id}", "get"),
        ("/api/agencies/{agency_id}/offer-intelligence/{package_id}", "put"),
        ("/api/agencies/{agency_id}/offer-intelligence/{package_id}", "delete"),
    ]:
        assert_openapi_path(paths, path, method)

    for path in paths:
        if "intelligent-offer-builder" in path or "offer-intelligence" in path:
            for forbidden in ["flight-search", "bookings/live", "tickets/issue", "emds/issue", "providers", "execute", "ai-generate", "send"]:
                if forbidden in path:
                    raise AssertionError(f"Forbidden execution route exposed for offer intelligence: {path}")

    for path, text in [
        (ROOT / "frontend/src/App.jsx", "/platform/intelligent-offer-builder"),
        (ROOT / "frontend/src/App.jsx", "/agency/offer-intelligence"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Intelligent Offer Builder"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Offer Intelligence"),
        (ROOT / "frontend/src/pages/platform/IntelligentOfferBuilderPage.jsx", "Package Overview"),
        (ROOT / "frontend/src/pages/platform/IntelligentOfferBuilderPage.jsx", "Decision Pack"),
        (ROOT / "frontend/src/pages/agency/OfferIntelligencePage.jsx", "Offer Intelligence Packages"),
        (ROOT / "docs/architecture/intelligent-offer-builder-integration-foundation.md", "Offer Builder should not invent intelligence"),
        (ROOT / "docs/architecture/current-model-inventory.md", "intelligent_offer_builder_packages"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/api/platform/intelligent-offer-builder"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Intelligent offer builder integration"),
        (ROOT / "docs/architecture/foundations/GLOSSARY.md", "Offer Intelligence Package"),
    ]:
        require_text(path, text)

    for path in [
        ROOT / "frontend/src/pages/platform/IntelligentOfferBuilderPage.jsx",
        ROOT / "frontend/src/pages/agency/OfferIntelligencePage.jsx",
    ]:
        reject_text(path, "apiPost")
        reject_text(path, "apiPut")
        reject_text(path, "apiDelete")
        for forbidden in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, forbidden)


def verify_metadata_only_code() -> None:
    implementation_paths = [
        ROOT / "backend/services/intelligent_offer_builder_service.py",
        ROOT / "backend/routers/platform_intelligent_offer_builder.py",
        ROOT / "backend/routers/agency_intelligent_offer_builder.py",
        ROOT / "frontend/src/pages/platform/IntelligentOfferBuilderPage.jsx",
        ROOT / "frontend/src/pages/agency/OfferIntelligencePage.jsx",
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
        "flight_search(",
        "search_flights(",
        "create_booking(",
        "issue_ticket(",
        "issue_emd(",
        "provider_client",
        "execute_parser(",
        "generate_price(",
        "calculate_fare(",
        "llm_prompt(",
        "ChatCompletion",
    ]
    for path in implementation_paths:
        content = path.read_text(encoding="utf-8")
        for term in forbidden_terms:
            if term in content:
                raise AssertionError(f"{path.relative_to(ROOT)} contains forbidden execution term {term}.")


def assert_created_record(record: dict, reference: str, agency_id: str) -> None:
    if record.get("offer_intelligence_reference") != reference:
        raise AssertionError(f"Unexpected offer intelligence reference: {record}")
    if record.get("agency_id") != agency_id:
        raise AssertionError(f"Unexpected agency scope: {record}")
    for field in [
        "recommendation_ids",
        "feasibility_ids",
        "operational_evaluation_ids",
        "capability_matrix_ids",
        "knowledge_version_ids",
        "evidence_reference_ids",
        "required_ssrs",
        "required_emds",
        "required_documents",
        "client_visible_reasons",
        "internal_evidence_trace",
        "internal_decision_trace",
        "decision_pack_sections",
        "decision_pack_evidence",
    ]:
        if not record.get(field):
            raise AssertionError(f"Created package missing {field}: {record}")
    if record.get("prepared_for_offer_builder") is not True or record.get("reviewed_by_agent") is not True:
        raise AssertionError(f"Lifecycle metadata was not preserved: {record}")
    for summary_field in [
        "input_reference_summary",
        "recommended_option_summary",
        "readiness_metadata_summary",
        "required_action_summary",
        "explanation_summary",
        "decision_pack_metadata_summary",
    ]:
        if not isinstance(record.get(summary_field), dict):
            raise AssertionError(f"Projection missing {summary_field}: {record}")
    assert_disabled_response(record)


def find_record(payload: dict, reference: str) -> dict:
    for item in payload.get("items") or payload.get("packages") or []:
        if item.get("offer_intelligence_reference") == reference:
            return item
    raise AssertionError(f"Offer intelligence package {reference} not found in payload: {payload}")


def verify_package_crud_and_filters() -> None:
    post("/api/reference/seed", {}, OWNER_HEADERS)
    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    reference = run_ref("IOB-SMOKE-509")
    payload = package_payload(agency_id, reference)

    created_response = post(PLATFORM_BASE, payload, OWNER_HEADERS, 201)
    assert_disabled_response(created_response)
    created = created_response.get("intelligent_offer_builder_package") or {}
    package_id = created.get("id")
    if not package_id:
        raise AssertionError(f"Create response missing package id: {created_response}")
    assert_created_record(created, reference, agency_id)

    quoted_id = quote(package_id)
    detail = get(f"{PLATFORM_BASE}/{quoted_id}", OWNER_HEADERS)
    assert_created_record(detail.get("intelligent_offer_builder_package") or {}, reference, agency_id)

    updated = put(
        f"{PLATFORM_BASE}/{quoted_id}",
        {
            "package_status": "ready",
            "client_visibility_status": "client_ready",
            "approved_for_client_presentation": True,
            "internal_decision_trace": [
                {"step": "client_ready_review", "result": "package metadata approved for client presentation"}
            ],
            "agent_notes": "Updated by smoke as metadata-only offer intelligence.",
        },
        OWNER_HEADERS,
    )
    updated_record = updated.get("intelligent_offer_builder_package") or {}
    if updated_record.get("package_status") != "ready" or updated_record.get("client_visibility_status") != "client_ready":
        raise AssertionError(f"Update did not preserve offer intelligence metadata: {updated_record}")
    assert_disabled_response(updated_record)

    query_checks = [
        f"?agency_id={quote(agency_id)}",
        "?package_status=ready",
        "?airline=LH",
        "?recommendation_level=highly_recommended",
        "?readiness_status=conditional",
        "?operational_risk=medium",
        "?passenger_need=PETC",
        "?destination=FRA",
        "?travel_date=2028-07-01",
        "?offer_workspace=OFF-WS-SMOKE-509",
        "?client_visibility_status=client_ready",
    ]
    for query in query_checks:
        result = get(f"{PLATFORM_BASE}{query}", OWNER_HEADERS)
        assert_disabled_response(result)
        assert_created_record(find_record(result, reference), reference, agency_id)

    summary = get(f"{PLATFORM_BASE}/summary", OWNER_HEADERS)
    assert_disabled_response(summary)
    for key in [
        "package_count",
        "by_package_status",
        "by_readiness_status",
        "by_client_visibility_status",
        "decision_pack_ready_count",
        "recommendation_reference_count",
        "feasibility_reference_count",
        "operational_evaluation_reference_count",
        "required_action_count",
        "client_explanation_count",
        "internal_trace_count",
        "decision_pack_section_count",
    ]:
        if key not in (summary.get("summary") or {}):
            raise AssertionError(f"Platform summary missing offer intelligence count {key}: {summary}")

    agency_base = AGENCY_BASE_TEMPLATE.format(agency_id=quote(agency_id))
    agency_list = get(f"{agency_base}?airline=LH&recommendation_level=highly_recommended", OWNER_HEADERS)
    assert_disabled_response(agency_list)
    assert_created_record(find_record(agency_list, reference), reference, agency_id)

    agency_detail = get(f"{agency_base}/{quoted_id}", OWNER_HEADERS)
    assert_disabled_response(agency_detail)
    assert_created_record(agency_detail.get("intelligent_offer_builder_package") or {}, reference, agency_id)

    agency_summary = get(f"{agency_base}/summary", OWNER_HEADERS)
    assert_disabled_response(agency_summary)

    agency_reference = run_ref("IOB-AGENCY-SMOKE-509")
    agency_created = post(agency_base, package_payload(agency_id, agency_reference), OWNER_HEADERS, 201)
    agency_created_record = agency_created.get("intelligent_offer_builder_package") or {}
    agency_package_id = agency_created_record.get("id")
    if not agency_package_id:
        raise AssertionError(f"Agency create response missing package id: {agency_created}")
    assert_created_record(agency_created_record, agency_reference, agency_id)
    agency_updated = put(
        f"{agency_base}/{quote(agency_package_id)}",
        {"package_status": "approved", "approved_for_client_presentation": True},
        OWNER_HEADERS,
    )
    if (agency_updated.get("intelligent_offer_builder_package") or {}).get("package_status") != "approved":
        raise AssertionError(f"Agency update did not preserve package status: {agency_updated}")
    agency_archived = request("DELETE", f"{agency_base}/{quote(agency_package_id)}", None, OWNER_HEADERS)[1]
    if agency_archived.get("archived") is not True:
        raise AssertionError(f"Agency archive did not soft-archive package metadata: {agency_archived}")

    archived = request("DELETE", f"{PLATFORM_BASE}/{quoted_id}", None, OWNER_HEADERS)[1]
    if archived.get("archived") is not True:
        raise AssertionError(f"Platform archive did not soft-archive package metadata: {archived}")
    assert_disabled_response(archived)


def verify_readiness_and_blueprint() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected active phase label: {health.get('phase')}")

    readiness = get("/api/readiness")
    section = readiness.get("intelligent_offer_builder_integration_foundation") or {}
    for flag in [
        "intelligent_offer_builder_integration_enabled",
        "intelligent_offer_builder_packages_collection_enabled",
        "platform_intelligent_offer_builder_metadata_crud_enabled",
        "agency_offer_intelligence_metadata_crud_enabled",
        "platform_intelligent_offer_builder_ui_enabled",
        "agency_offer_intelligence_ui_enabled",
        "offer_builder_should_not_invent_intelligence",
        "consumes_passenger_service_feasibility",
        "consumes_airline_recommendations",
        "consumes_operational_evaluations",
        "consumes_capability_matrix",
        "consumes_knowledge_governance_evidence",
        "metadata_only",
        "advisory_only",
        "human_authority_final",
        "no_live_gds_search",
        "no_ndc_search",
        "flight_search_disabled",
        "booking_disabled",
        "ticketing_disabled",
        "emd_issuance_disabled",
        "provider_integrations_disabled",
        "parser_execution_disabled",
        "no_ai_generation",
        "no_llm_generation",
        "background_workers_disabled",
        "automatic_sending_disabled",
    ]:
        if section.get(flag) is not True:
            raise AssertionError(f"Readiness missing offer intelligence flag {flag}: {section}")
    for key in [
        "intelligent_offer_builder_package_count",
        "intelligent_offer_builder_package_status_counts",
        "intelligent_offer_builder_readiness_status_counts",
        "intelligent_offer_builder_client_visibility_status_counts",
        "intelligent_offer_builder_recommendation_reference_count",
        "intelligent_offer_builder_feasibility_reference_count",
        "intelligent_offer_builder_required_action_count",
        "intelligent_offer_builder_client_explanation_count",
        "intelligent_offer_builder_internal_trace_count",
        "intelligent_offer_builder_decision_pack_ready_count",
    ]:
        if key not in section:
            raise AssertionError(f"Readiness missing offer intelligence count {key}: {section}")

    adoption = get("/api/platform/blueprint/adoption-map", OWNER_HEADERS)
    categories = {item.get("category") for item in adoption.get("items") or []}
    if "Intelligent Offer Builder" not in categories:
        raise AssertionError(f"Blueprint adoption map missing Intelligent Offer Builder category: {categories}")

    route_policy = get("/api/platform/blueprint/route-policy", OWNER_HEADERS)
    mappings = route_policy.get("route_mappings") or []
    expected_pairs = {
        ("/admin/intelligent-offer-builder", "/platform/intelligent-offer-builder"),
        ("/agent/offer-intelligence", "/agency/offer-intelligence"),
    }
    actual_pairs = {(item.get("supplementary"), item.get("agencyos")) for item in mappings}
    missing = expected_pairs - actual_pairs
    if missing:
        raise AssertionError(f"Route policy missing intelligent offer builder canonical mappings: {missing}")

    gaps = get("/api/platform/blueprint/gaps", OWNER_HEADERS)
    if "Intelligent offer builder integration foundation built in Phase 50.9" not in gaps.get("already_built", []):
        raise AssertionError(f"Gap summary missing Phase 50.9 intelligent offer builder marker: {gaps}")


def main() -> int:
    verify_model_and_collection_registration()
    verify_router_and_ui_registration()
    verify_metadata_only_code()
    verify_package_crud_and_filters()
    verify_readiness_and_blueprint()
    print("Phase 50.9 intelligent offer builder integration smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
