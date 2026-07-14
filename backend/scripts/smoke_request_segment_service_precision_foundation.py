#!/usr/bin/env python3
import sys
import time
from pathlib import Path
from urllib.parse import quote

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import RequestSegmentServiceScope, RequestSegmentServiceScopeCreate
from services.request_segment_service_precision_service import (
    KNOWLEDGE_LINK_FIELDS,
    OPERATIONAL_FLAG_FIELDS,
    PHASE_LABEL,
    REQUEST_SEGMENT_SERVICE_READINESS_STATUSES,
    REQUEST_SEGMENT_SERVICE_REQUESTED_STATUSES,
    REQUEST_SEGMENT_SERVICE_SCOPE_STATUSES,
    REQUEST_SEGMENT_SERVICE_SCOPES_COLLECTION,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_55_2_airline_policy_evidence_source_governance_foundation"
ROOT = Path(__file__).resolve().parents[2]
PLATFORM_BASE = "/api/platform/request-segment-services"
AGENCY_BASE_TEMPLATE = "/api/agencies/{agency_id}/request-segment-services"


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
        "request_segment_service_precision_foundation",
        "request_intake_segment_first",
        "passenger_segment_service_scope",
        "pets_segment_scoped",
        "special_items_segment_scoped",
        "request_remains_intake",
        "trip_remains_operational_dossier",
        "never_use_travel_request_id_as_trip_id",
        "trip_conversion_metadata_only",
        "policy_evaluation_disabled",
        "pricing_calculation_disabled",
        "booking_disabled",
        "ticketing_disabled",
        "emd_issuance_disabled",
        "provider_integrations_disabled",
        "no_ai_generation",
        "no_llm_generation",
        "background_workers_disabled",
        "human_authority_final",
    ]


def assert_disabled_response(payload: dict) -> None:
    for flag in disabled_flags():
        if payload.get(flag) is not True:
            raise AssertionError(f"Payload missing disabled flag {flag}: {payload}")


def scope_payload(agency_id: str, reference: str) -> dict:
    return {
        "agency_id": agency_id,
        "scope_reference": reference,
        "scope_status": "needs_review",
        "scope_version": "51.2.0-smoke",
        "travel_request_id": "TR-SMOKE-512",
        "request_reference": "REQ-SMOKE-512",
        "source_entry_path": "/agency/requests/new",
        "submission_channel": "staff_console",
        "client_id": "CLIENT-SMOKE-512",
        "contact_summary": "Primary contact confirmed pet and instrument needs.",
        "request_passenger_reference": "RPSG-SMOKE-512",
        "passenger_workspace_id": "PAX-WS-SMOKE-512",
        "passenger_id": "PAX-SMOKE-512",
        "passenger_link_mode": "existing",
        "passenger_snapshot": {"display_name": "Phase 51.2 Traveler", "type": "adult"},
        "beneficiary_type": "traveler",
        "request_segment_reference": "RSEG-SMOKE-512-1",
        "segment_order": 1,
        "origin": "SOF",
        "destination": "FRA",
        "departure_date": "2028-07-01",
        "arrival_date": "2028-07-01",
        "preferred_airline": "LH",
        "cabin_requested": "Economy",
        "segment_scope_type": "single_segment",
        "service_family": "pets_animals",
        "service_code": "PETC",
        "ssr_code": "PETC",
        "service_catalogue_reference": "SVC-PETC",
        "selected_service_key": "pet_in_cabin",
        "service_details": {"approval_required": True, "source": "intake"},
        "requested_status": "requested",
        "pet_reference": "PET-SMOKE-512",
        "pet_id": "PET-ID-SMOKE-512",
        "pet_transport_mode": "petc",
        "species": "dog",
        "breed": "Pug",
        "snub_nosed_flag": True,
        "pet_weight_kg": 8.2,
        "container_dimensions": {"length": 55, "width": 40, "height": 23, "unit": "cm"},
        "pet_document_status": "missing_vaccination_certificate",
        "special_item_reference": "ITEM-SMOKE-512",
        "special_item_id": "ITEM-ID-SMOKE-512",
        "item_category": "musical_instrument",
        "transport_location": "extra_seat",
        "item_weight_kg": 7.5,
        "item_dimensions": {"length": 80, "width": 25, "height": 18, "unit": "cm"},
        "battery_type": "none",
        "documentation_status": "not_required",
        "requires_airline_policy_review": True,
        "requires_medical_review": True,
        "requires_document_followup": True,
        "requires_airline_approval": True,
        "requires_manual_review": True,
        "requires_pricing_review": True,
        "service_parameter_taxonomy_ids": ["SPT-SMOKE-511"],
        "operational_constraint_ids": ["OCE-SMOKE-512"],
        "capability_matrix_ids": ["ACM-SMOKE-512"],
        "operational_evaluation_ids": ["OKE-SMOKE-512"],
        "feasibility_ids": ["PSF-SMOKE-512"],
        "recommendation_ids": ["ARE-SMOKE-512"],
        "readiness_status": "needs_review",
        "missing_fields": ["pet_container_height_confirmation"],
        "missing_documents": ["vaccination_certificate"],
        "readiness_warnings": ["Snub-nosed breed requires airline-specific review."],
        "readiness_blockers": ["Vaccination certificate missing."],
        "linked_trip_id": "TRIP-SMOKE-512",
        "converted_to_trip": True,
        "converted_at": "2026-07-09T00:00:00+00:00",
        "trip_segment_ids": ["TRIP-SEG-SMOKE-512-1"],
        "carried_forward_to_trip": True,
        "request_snapshot": {"request_reference": "REQ-SMOKE-512", "segment_first": True},
        "decision_trace": [{"step": "intake_scope_created", "authority": "human_agent"}],
        "operational_notes": "Metadata-only segment service scope for smoke coverage.",
        "internal_notes": "No policy evaluation, pricing calculation, booking, ticketing, provider, AI, or worker execution.",
        "metadata": {"smoke": True, "phase": "51.2"},
    }


def verify_model_and_collection_registration() -> None:
    if REQUEST_SEGMENT_SERVICE_SCOPES_COLLECTION not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("request_segment_service_scopes is not registered as agency-owned metadata.")
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Service phase label mismatch: {PHASE_LABEL}")

    payload = scope_payload("agency-smoke", "RSS-SMOKE-MODEL")
    create_model = RequestSegmentServiceScopeCreate(**payload)
    record = RequestSegmentServiceScope(**create_model.model_dump(mode="json", exclude_none=True))
    if record.scope_reference != "RSS-SMOKE-MODEL":
        raise AssertionError("Request segment service scope model did not preserve reference metadata.")
    for field in [
        "request_passenger_reference",
        "request_segment_reference",
        "service_family",
        "ssr_code",
        "pet_reference",
        "special_item_reference",
        "readiness_status",
        "linked_trip_id",
        "decision_trace",
    ]:
        if not getattr(record, field):
            raise AssertionError(f"Request segment service scope model did not preserve {field}.")
    if record.metadata_only is not True or record.policy_evaluation_disabled is not True:
        raise AssertionError("Request segment service scope model is not metadata-only.")
    if record.linked_trip_id == record.travel_request_id:
        raise AssertionError("Request segment service scope reused travel_request_id as linked_trip_id.")

    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "request_segment_service_scopes_id_unique",
        "request_segment_service_scopes_reference_unique",
        "request_segment_service_scopes_agency_status_lookup",
        "request_segment_service_scopes_travel_request_lookup",
        "request_segment_service_scopes_request_passenger_lookup",
        "request_segment_service_scopes_request_segment_lookup",
        "request_segment_service_scopes_service_family_lookup",
        "request_segment_service_scopes_ssr_lookup",
        "request_segment_service_scopes_pet_transport_lookup",
        "request_segment_service_scopes_item_category_lookup",
        "request_segment_service_scopes_readiness_lookup",
        "request_segment_service_scopes_taxonomy_lookup",
        "request_segment_service_scopes_recommendation_lookup",
        "request_segment_service_scopes_linked_trip_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Database index registration missing {index_name}.")

    for value in ["draft", "captured", "needs_review", "ready", "converted", "archived"]:
        if value not in REQUEST_SEGMENT_SERVICE_SCOPE_STATUSES:
            raise AssertionError(f"Missing scope status {value}.")
    for value in ["missing_information", "needs_review", "blocked", "ready_for_agent_review", "ready_for_trip_conversion", "converted", "unknown"]:
        if value not in REQUEST_SEGMENT_SERVICE_READINESS_STATUSES:
            raise AssertionError(f"Missing readiness status {value}.")
    for value in ["requested", "pending_information", "confirmed_by_client", "cancelled", "carried_forward", "unknown"]:
        if value not in REQUEST_SEGMENT_SERVICE_REQUESTED_STATUSES:
            raise AssertionError(f"Missing requested status {value}.")


def verify_router_and_ui_registration() -> None:
    openapi = get("/openapi.json", OWNER_HEADERS)
    paths = openapi.get("paths", {})
    for path, method in [
        (PLATFORM_BASE, "get"),
        (PLATFORM_BASE, "post"),
        (f"{PLATFORM_BASE}/summary", "get"),
        (f"{PLATFORM_BASE}/{{scope_id}}", "get"),
        (f"{PLATFORM_BASE}/{{scope_id}}", "put"),
        (f"{PLATFORM_BASE}/{{scope_id}}", "delete"),
        ("/api/agencies/{agency_id}/request-segment-services", "get"),
        ("/api/agencies/{agency_id}/request-segment-services", "post"),
        ("/api/agencies/{agency_id}/request-segment-services/summary", "get"),
        ("/api/agencies/{agency_id}/request-segment-services/{scope_id}", "get"),
        ("/api/agencies/{agency_id}/request-segment-services/{scope_id}", "put"),
        ("/api/agencies/{agency_id}/request-segment-services/{scope_id}", "delete"),
    ]:
        assert_openapi_path(paths, path, method)

    for path in paths:
        if "request-segment-services" in path:
            for forbidden in ["/admin", "/agent", "live-search", "book", "ticket", "providers", "ai-generate", "worker"]:
                if forbidden in path:
                    raise AssertionError(f"Forbidden route exposed for request segment services: {path}")

    for path, text in [
        (ROOT / "frontend/src/App.jsx", "/platform/request-segment-services"),
        (ROOT / "frontend/src/App.jsx", "/agency/request-segment-services"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Request Segment Services"),
        (ROOT / "frontend/src/pages/platform/RequestSegmentServicesPage.jsx", "Scope Overview"),
        (ROOT / "frontend/src/pages/platform/RequestSegmentServicesPage.jsx", "Passenger Context"),
        (ROOT / "frontend/src/pages/platform/RequestSegmentServicesPage.jsx", "Special Item Context"),
        (ROOT / "frontend/src/pages/platform/RequestSegmentServicesPage.jsx", "Conversion Metadata"),
        (ROOT / "frontend/src/pages/agency/RequestSegmentServicesPage.jsx", "Trace / Notes"),
        (ROOT / "docs/architecture/request-segment-service-precision-foundation.md", "Phase 51.2 does not add policy or pricing evaluation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "request_segment_service_scopes"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/api/platform/request-segment-services"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Request intake segment-service precision"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Request Segment Services"),
        (ROOT / "docs/architecture/passenger-service-operations-principle.md", "segment-first intake"),
        (ROOT / "docs/architecture/foundations/GLOSSARY.md", "Request Segment Service Scope"),
    ]:
        require_text(path, text)

    for path in [
        ROOT / "frontend/src/pages/platform/RequestSegmentServicesPage.jsx",
        ROOT / "frontend/src/pages/agency/RequestSegmentServicesPage.jsx",
    ]:
        reject_text(path, "apiPost")
        reject_text(path, "apiPut")
        reject_text(path, "apiDelete")
        for forbidden in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, forbidden)


def verify_metadata_only_code() -> None:
    implementation_paths = [
        ROOT / "backend/services/request_segment_service_precision_service.py",
        ROOT / "backend/routers/platform_request_segment_services.py",
        ROOT / "backend/routers/agency_request_segment_services.py",
        ROOT / "frontend/src/pages/platform/RequestSegmentServicesPage.jsx",
        ROOT / "frontend/src/pages/agency/RequestSegmentServicesPage.jsx",
    ]
    forbidden_terms = [
        "BackgroundTasks",
        "asyncio.create_task",
        "httpx",
        "requests.",
        "urllib.",
        "openai",
        "ChatCompletion",
        "PocketBase",
        "airline_policies",
        "policy_evaluations",
        "live_flight_search",
        "flight_search(",
        "book_flight",
        "create_booking",
        "issue_ticket",
        "issue_emd",
        "provider_client",
        "send_to_client",
    ]
    for path in implementation_paths:
        content = path.read_text(encoding="utf-8")
        for term in forbidden_terms:
            if term in content:
                raise AssertionError(f"{path.relative_to(ROOT)} contains forbidden execution term {term}.")


def assert_created_scope(record: dict, reference: str, agency_id: str) -> None:
    if record.get("scope_reference") != reference:
        raise AssertionError(f"Unexpected scope reference: {record}")
    if record.get("agency_id") != agency_id:
        raise AssertionError(f"Unexpected agency scope: {record}")
    for field in [
        "travel_request_id",
        "request_reference",
        "request_passenger_reference",
        "passenger_workspace_id",
        "passenger_id",
        "passenger_snapshot",
        "request_segment_reference",
        "segment_order",
        "origin",
        "destination",
        "service_family",
        "service_code",
        "ssr_code",
        "service_details",
        "pet_reference",
        "pet_id",
        "pet_transport_mode",
        "species",
        "breed",
        "container_dimensions",
        "special_item_reference",
        "special_item_id",
        "item_category",
        "item_dimensions",
        "service_parameter_taxonomy_ids",
        "operational_constraint_ids",
        "capability_matrix_ids",
        "operational_evaluation_ids",
        "feasibility_ids",
        "recommendation_ids",
        "missing_fields",
        "readiness_warnings",
        "linked_trip_id",
        "trip_segment_ids",
        "request_snapshot",
        "decision_trace",
        "operational_notes",
    ]:
        if not record.get(field):
            raise AssertionError(f"Created scope missing {field}: {record}")
    for field in ["missing_documents", "readiness_blockers"]:
        if field not in record:
            raise AssertionError(f"Created scope missing readiness field {field}: {record}")
    for flag in OPERATIONAL_FLAG_FIELDS:
        if record.get(flag) is not True and flag != "requires_document_followup":
            raise AssertionError(f"Created scope missing operational flag {flag}: {record}")
    for summary_field in ["passenger_segment_service_summary", "operational_flag_summary", "knowledge_link_summary", "readiness_summary", "conversion_summary"]:
        if not isinstance(record.get(summary_field), dict):
            raise AssertionError(f"Projection missing {summary_field}: {record}")
    if record.get("linked_trip_id") == record.get("travel_request_id"):
        raise AssertionError(f"linked_trip_id reused travel_request_id: {record}")
    assert_disabled_response(record)


def find_record(payload: dict, reference: str) -> dict:
    for item in payload.get("items") or payload.get("scopes") or []:
        if item.get("scope_reference") == reference:
            return item
    raise AssertionError(f"Request segment service scope {reference} not found in payload: {payload}")


def verify_scope_crud_and_filters() -> None:
    post("/api/reference/seed", {}, OWNER_HEADERS)
    agency_id = get("/api/agencies", OWNER_HEADERS)["items"][0]["id"]
    reference = run_ref("RSS-SMOKE-512")
    payload = scope_payload(agency_id, reference)

    created_response = post(PLATFORM_BASE, payload, OWNER_HEADERS, 201)
    assert_disabled_response(created_response)
    created = created_response.get("request_segment_service_scope") or {}
    scope_id = created.get("id")
    if not scope_id:
        raise AssertionError(f"Create response missing scope id: {created_response}")
    assert_created_scope(created, reference, agency_id)

    quoted_id = quote(scope_id)
    detail = get(f"{PLATFORM_BASE}/{quoted_id}", OWNER_HEADERS)
    assert_created_scope(detail.get("request_segment_service_scope") or {}, reference, agency_id)

    updated = put(
        f"{PLATFORM_BASE}/{quoted_id}",
        {
            "scope_status": "ready",
            "readiness_status": "ready_for_trip_conversion",
            "requires_document_followup": False,
            "missing_documents": [],
            "readiness_blockers": [],
            "requested_status": "confirmed_by_client",
        },
        OWNER_HEADERS,
    )
    updated_record = updated.get("request_segment_service_scope") or {}
    if updated_record.get("readiness_status") != "ready_for_trip_conversion" or updated_record.get("requires_document_followup") is not False:
        raise AssertionError(f"Update did not preserve request segment service metadata: {updated_record}")
    assert_disabled_response(updated_record)

    query_checks = [
        f"?agency_id={quote(agency_id)}",
        "?request=TR-SMOKE-512",
        "?passenger=PAX-SMOKE-512",
        "?segment=SOF",
        "?service_family=pets_animals",
        "?ssr_code=PETC",
        "?pet_transport_mode=petc",
        "?item_category=musical_instrument",
        "?readiness_status=ready_for_trip_conversion",
        "?requires_policy_review=true",
        "?requires_document_followup=false",
    ]
    for query in query_checks:
        result = get(f"{PLATFORM_BASE}{query}", OWNER_HEADERS)
        assert_disabled_response(result)
        found = find_record(result, reference)
        if query == "?requires_document_followup=false" and found.get("requires_document_followup") is not False:
            raise AssertionError(f"Document follow-up false filter returned wrong scope: {found}")

    summary = get(f"{PLATFORM_BASE}/summary", OWNER_HEADERS)
    assert_disabled_response(summary)
    for key in [
        "scope_count",
        "by_scope_status",
        "by_readiness_status",
        "by_requested_status",
        "policy_review_count",
        "document_followup_count",
        "pet_transport_scope_count",
        "special_item_scope_count",
        "converted_to_trip_count",
        "knowledge_link_count",
        "missing_field_count",
        "readiness_warning_count",
    ]:
        if key not in (summary.get("summary") or {}):
            raise AssertionError(f"Platform summary missing scope count {key}: {summary}")

    agency_base = AGENCY_BASE_TEMPLATE.format(agency_id=quote(agency_id))
    agency_list = get(f"{agency_base}?service_family=pets_animals&ssr_code=PETC", OWNER_HEADERS)
    assert_disabled_response(agency_list)
    assert_created_scope(find_record(agency_list, reference), reference, agency_id)

    agency_detail = get(f"{agency_base}/{quoted_id}", OWNER_HEADERS)
    assert_disabled_response(agency_detail)
    assert_created_scope(agency_detail.get("request_segment_service_scope") or {}, reference, agency_id)

    agency_summary = get(f"{agency_base}/summary", OWNER_HEADERS)
    assert_disabled_response(agency_summary)

    agency_reference = run_ref("RSS-AGENCY-SMOKE-512")
    agency_created = post(agency_base, scope_payload(agency_id, agency_reference), OWNER_HEADERS, 201)
    agency_created_record = agency_created.get("request_segment_service_scope") or {}
    agency_scope_id = agency_created_record.get("id")
    if not agency_scope_id:
        raise AssertionError(f"Agency create response missing scope id: {agency_created}")
    assert_created_scope(agency_created_record, agency_reference, agency_id)
    agency_updated = put(
        f"{agency_base}/{quote(agency_scope_id)}",
        {"scope_status": "ready", "readiness_status": "ready_for_agent_review"},
        OWNER_HEADERS,
    )
    if (agency_updated.get("request_segment_service_scope") or {}).get("scope_status") != "ready":
        raise AssertionError(f"Agency update did not preserve scope status: {agency_updated}")
    agency_archived = request("DELETE", f"{agency_base}/{quote(agency_scope_id)}", None, OWNER_HEADERS)[1]
    if agency_archived.get("archived") is not True:
        raise AssertionError(f"Agency archive did not soft-archive request segment service metadata: {agency_archived}")

    archived = request("DELETE", f"{PLATFORM_BASE}/{quoted_id}", None, OWNER_HEADERS)[1]
    if archived.get("archived") is not True:
        raise AssertionError(f"Platform archive did not soft-archive request segment service metadata: {archived}")
    assert_disabled_response(archived)


def verify_readiness_and_blueprint() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected active phase label: {health.get('phase')}")

    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Readiness phase mismatch: {readiness.get('phase')}")
    section = readiness.get("request_segment_service_precision_foundation") or {}
    required_flags = [
        "request_segment_service_precision_enabled",
        "request_segment_service_scopes_collection_enabled",
        "platform_request_segment_services_metadata_crud_enabled",
        "agency_request_segment_services_metadata_crud_enabled",
        "platform_request_segment_services_ui_enabled",
        "agency_request_segment_services_ui_enabled",
        "segment_first_intake_enabled",
        "service_scope_requires_passenger_segment_service_context",
        "pets_segment_scoped",
        "special_items_segment_scoped",
        "request_remains_intake",
        "trip_remains_operational_dossier",
        "never_use_travel_request_id_as_trip_id",
        "policy_evaluation_disabled",
        "pricing_calculation_disabled",
        "booking_disabled",
        "provider_integrations_disabled",
        "no_ai_generation",
        "background_workers_disabled",
    ]
    for flag in required_flags:
        if section.get(flag) is not True:
            raise AssertionError(f"Readiness section missing {flag}: {section}")
    for key in [
        "request_segment_service_scope_count",
        "request_segment_service_scope_status_counts",
        "request_segment_service_readiness_status_counts",
        "request_segment_service_operational_flag_counts",
        "request_segment_service_knowledge_link_counts",
        "request_segment_service_pet_scope_count",
        "request_segment_service_special_item_scope_count",
        "request_segment_service_decision_trace_count",
    ]:
        if key not in section:
            raise AssertionError(f"Readiness section missing count {key}: {section}")

    adoption = get("/api/platform/blueprint/adoption-map", OWNER_HEADERS)
    if adoption.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Adoption phase mismatch: {adoption.get('phase')}")
    if "RequestSegmentServiceScope" not in str(adoption):
        raise AssertionError(f"Adoption map missing RequestSegmentServiceScope: {adoption}")

    route_policy = get("/api/platform/blueprint/route-policy", OWNER_HEADERS)
    if route_policy.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Route policy phase mismatch: {route_policy.get('phase')}")
    mappings = route_policy.get("route_mappings") or []
    expected_mappings = [
        ("/admin/request-segment-services", "/platform/request-segment-services"),
        ("/agent/request-segment-services", "/agency/request-segment-services"),
    ]
    for supplementary, agencyos in expected_mappings:
        if not any(item.get("supplementary") == supplementary and item.get("agencyos") == agencyos for item in mappings):
            raise AssertionError(f"Route policy missing request segment service mapping {supplementary} -> {agencyos}: {route_policy}")

    gaps = get("/api/platform/blueprint/gaps", OWNER_HEADERS)
    if "Request intake segment-service precision foundation built in Phase 51.2" not in str(gaps):
        raise AssertionError(f"Gap summary missing Phase 51.2 built marker: {gaps}")

    for field in KNOWLEDGE_LINK_FIELDS:
        if field not in str(adoption) and field not in str(readiness):
            raise AssertionError(f"Knowledge link field {field} missing from blueprint/readiness metadata.")


def main() -> None:
    verify_model_and_collection_registration()
    verify_router_and_ui_registration()
    verify_metadata_only_code()
    verify_scope_crud_and_filters()
    verify_readiness_and_blueprint()
    print("Phase 51.2 request segment service precision smoke passed.")


if __name__ == "__main__":
    main()
