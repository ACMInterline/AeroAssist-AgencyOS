#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import (
    SsrOsiApprovalStatus,
    SsrOsiNeedCategory,
    SsrOsiOperationalStatus,
    SsrOsiReadinessStatus,
    SsrOsiWorkspace,
    SsrOsiWorkspaceCreate,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_55_8_airline_contact_communication_intelligence_foundation"
ROOT = Path(__file__).resolve().parents[2]
AOIE_PATH = "Passenger Need -> SSR / OSI Workspace -> Airline Knowledge -> Capability Matrix -> Operational Feasibility -> Offer Builder"

NEED_CATEGORIES = {
    "mobility",
    "medical",
    "visual_impairment",
    "hearing_impairment",
    "cognitive",
    "unaccompanied_minor",
    "infant",
    "pet",
    "assistance_animal",
    "sports_equipment",
    "musical_instrument",
    "oversized_baggage",
    "dangerous_goods",
    "religious",
    "dietary",
    "seating",
    "security",
    "immigration",
    "documentation",
    "vip",
    "disruption",
    "other",
}
READINESS_STATUSES = {
    "ready",
    "pending",
    "awaiting_airline",
    "awaiting_documents",
    "awaiting_payment",
    "awaiting_emd",
    "awaiting_medif",
    "awaiting_customer",
    "blocked",
}
APPROVAL_STATUSES = {"not_required", "pending", "approved", "rejected", "expired"}
OPERATIONAL_STATUSES = {"draft", "review", "ready", "archived"}


def require_flag(section: dict, key: str, expected: object = True) -> None:
    if section.get(key) is not expected:
        raise AssertionError(f"Readiness flag {key} expected {expected!r}, got {section.get(key)!r}")


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
        "live_ssr_transmission_disabled",
        "live_osi_transmission_disabled",
        "gds_connectivity_disabled",
        "ndc_connectivity_disabled",
        "airline_apis_disabled",
        "ai_recommendation_disabled",
        "automatic_airline_approval_disabled",
        "automatic_emd_issuance_disabled",
        "background_workers_disabled",
        "provider_integrations_disabled",
        "external_api_calls_disabled",
        "automation_disabled",
    ]


def forbidden_enabled_flags() -> list[str]:
    return [
        "live_ssr_transmission_enabled",
        "live_osi_transmission_enabled",
        "gds_connectivity_enabled",
        "ndc_connectivity_enabled",
        "airline_apis_enabled",
        "ai_recommendation_enabled",
        "automatic_airline_approval_enabled",
        "automatic_emd_issuance_enabled",
        "background_workers_enabled",
        "provider_integrations_enabled",
        "external_api_calls_enabled",
        "automation_enabled",
    ]


def assert_disabled_response(payload: dict) -> None:
    if payload.get("metadata_only") is not True:
        raise AssertionError(f"Payload is not metadata-only: {payload}")
    for flag in disabled_flags():
        if payload.get(flag) is not True:
            raise AssertionError(f"Payload missing disabled flag {flag}: {payload}")
    for flag in forbidden_enabled_flags():
        if payload.get(flag) is True:
            raise AssertionError(f"Payload exposes forbidden enabled flag {flag}: {payload}")


def verify_model_and_collection_registration() -> None:
    if {item.value for item in SsrOsiNeedCategory} != NEED_CATEGORIES:
        raise AssertionError("SSR / OSI need category enum values changed unexpectedly.")
    if {item.value for item in SsrOsiReadinessStatus} != READINESS_STATUSES:
        raise AssertionError("SSR / OSI readiness enum values changed unexpectedly.")
    if {item.value for item in SsrOsiApprovalStatus} != APPROVAL_STATUSES:
        raise AssertionError("SSR / OSI approval enum values changed unexpectedly.")
    if {item.value for item in SsrOsiOperationalStatus} != OPERATIONAL_STATUSES:
        raise AssertionError("SSR / OSI operational enum values changed unexpectedly.")

    create_payload = SsrOsiWorkspaceCreate(
        agency_id="agency-smoke",
        operational_workspace_id="operational-smoke",
        passenger_workspace_id="passenger-smoke",
        travel_request_workspace_id="request-smoke",
        trip_workspace_id="trip-smoke",
        booking_workspace_id="booking-smoke",
        ticket_workspace_id="ticket-smoke",
        emd_workspace_id="emd-smoke",
        workspace_reference="SSROSI-SMOKE-MODEL",
        operational_status=SsrOsiOperationalStatus.READY,
        operational_priority="high",
        need_category=SsrOsiNeedCategory.MOBILITY,
        need_subcategory="wheelchair",
        need_description="Passenger needs wheelchair assistance between gates.",
        passenger_statement="Long distances are difficult.",
        service_family="assistance",
        service_type="wheelchair",
        ancillary_category="assistance",
        operational_category="airport_assistance",
        medical_category="mobility",
        mobility_category="WCHR",
        ssr_code="WCHR",
        ssr_description="Wheelchair ramp assistance metadata.",
        ssr_status="requested",
        ssr_confirmation_status="pending",
        osi_required=True,
        osi_text="OSI LH PASSENGER REQUESTS GATE DISTANCE SUPPORT",
        osi_status="draft",
        airline_code="LH",
        validating_carrier="LH",
        operating_carrier="LH",
        approval_required=True,
        approval_status=SsrOsiApprovalStatus.PENDING,
        approval_reference="APR-SSR-SMOKE",
        approval_deadline="2028-04-01",
        departure_station="SOF",
        connection_station="FRA",
        arrival_station="JFK",
        handling_company="Airport Assist",
        station_status="pending",
        emd_required=True,
        emd_workspace_ids=["emd-smoke"],
        rfic="C",
        rfisc="0B5",
        document_requirements=["MEDIF"],
        medif_required=True,
        medif_workspace_id="medif-smoke",
        medical_certificate_required=True,
        customs_documents_required=False,
        visa_documents_required=True,
        task_ids=["task-smoke"],
        timeline_ids=["timeline-smoke"],
        communication_ids=["communication-smoke"],
        readiness_status=SsrOsiReadinessStatus.AWAITING_AIRLINE,
        missing_requirements=["airline approval"],
        unresolved_items=["MEDIF review"],
        flight_workspace_ids=["flight-smoke"],
        linked_document_ids=["document-smoke"],
        agent_notes="Agent metadata only.",
        passenger_notes="Passenger service note metadata.",
        airline_notes="Airline handling note metadata.",
        internal_notes="Internal operational metadata only.",
        metadata={"smoke": True},
    )
    workspace = SsrOsiWorkspace(**create_payload.model_dump(mode="json", exclude_none=True))
    dumped = workspace.model_dump(mode="json")
    if dumped.get("need_category") != "mobility" or dumped.get("ssr_code") != "WCHR":
        raise AssertionError(f"SSR / OSI workspace dimensions were not preserved: {dumped}")
    if dumped.get("readiness_status") != "awaiting_airline" or dumped.get("approval_status") != "pending":
        raise AssertionError(f"SSR / OSI readiness or approval metadata was not preserved: {dumped}")
    for key in ["metadata_only", "ssr_osi_workspace_metadata_only", *disabled_flags()]:
        if dumped.get(key) is not True:
            raise AssertionError(f"SSR / OSI model missing disabled flag {key}: {dumped}")
    if "ssr_osi_workspaces" not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("SSR / OSI workspaces collection is not registered.")
    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "ssr_osi_workspaces_id_unique",
        "ssr_osi_workspaces_reference_unique",
        "ssr_osi_workspaces_agency_need_category_lookup",
        "ssr_osi_workspaces_agency_airline_lookup",
        "ssr_osi_workspaces_agency_approval_status_lookup",
        "ssr_osi_workspaces_agency_readiness_status_lookup",
        "ssr_osi_workspaces_agency_passenger_lookup",
        "ssr_osi_workspaces_agency_priority_lookup",
        "ssr_osi_workspaces_agency_rfic_lookup",
        "ssr_osi_workspaces_agency_rfisc_lookup",
        "ssr_osi_workspaces_status_lookup",
        "ssr_osi_workspaces_operational_workspace_lookup",
        "ssr_osi_workspaces_travel_request_workspace_lookup",
        "ssr_osi_workspaces_trip_workspace_lookup",
        "ssr_osi_workspaces_booking_workspace_lookup",
        "ssr_osi_workspaces_ticket_workspace_lookup",
        "ssr_osi_workspaces_emd_workspace_lookup",
        "ssr_osi_workspaces_flight_workspace_lookup",
        "ssr_osi_workspaces_emd_links_lookup",
        "ssr_osi_workspaces_document_lookup",
        "ssr_osi_workspaces_created_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"SSR / OSI workspace index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    expected_methods = {
        "/api/platform/ssr-osi-workspaces": {"get", "post"},
        "/api/platform/ssr-osi-workspaces/summary": {"get"},
        "/api/platform/ssr-osi-workspaces/{workspace_id}": {"get", "put", "delete"},
        "/api/agencies/{agency_id}/ssr-osi-workspaces": {"get"},
        "/api/agencies/{agency_id}/ssr-osi-workspaces/summary": {"get"},
        "/api/agencies/{agency_id}/ssr-osi-workspaces/{workspace_id}": {"get"},
    }
    for path, methods in expected_methods.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in [
        "/api/agencies/{agency_id}/ssr-osi-workspaces",
        "/api/agencies/{agency_id}/ssr-osi-workspaces/summary",
        "/api/agencies/{agency_id}/ssr-osi-workspaces/{workspace_id}",
    ]:
        methods = set(paths.get(path, {}).keys())
        blocked_methods = methods & {"post", "put", "patch", "delete"}
        if blocked_methods:
            raise AssertionError(f"Agency SSR / OSI workspace route is not read-only: {path} {sorted(blocked_methods)}")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/lib/moduleCatalog.js", "SSR / OSI Operations"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Passenger Services"),
        (ROOT / "frontend/src/App.jsx", "/platform/ssr-osi-workspaces"),
        (ROOT / "frontend/src/App.jsx", "/agency/passenger-services"),
        (ROOT / "frontend/src/pages/platform/SsrOsiWorkspacesPage.jsx", "SSR / OSI Operations"),
        (ROOT / "frontend/src/pages/platform/SsrOsiWorkspacesPage.jsx", "without live transmission"),
        (ROOT / "frontend/src/pages/platform/SsrOsiWorkspacesPage.jsx", "Missing"),
        (ROOT / "frontend/src/pages/agency/PassengerServicesPage.jsx", "Passenger Services"),
        (ROOT / "frontend/src/pages/agency/PassengerServicesPage.jsx", "Read-only SSR / OSI operational workspace metadata"),
        (ROOT / "docs/architecture/ssr-osi-operational-workspace-foundation.md", "SSR / OSI Operational Workspace Foundation"),
        (ROOT / "docs/architecture/ssr-osi-operational-workspace-foundation.md", AOIE_PATH),
        (ROOT / "docs/architecture/passenger-service-operations-principle.md", AOIE_PATH),
        (ROOT / "README.md", "Phase 41.9 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 41.9: SSR / OSI Operational Workspace Foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "ssr_osi_workspaces"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/api/platform/ssr-osi-workspaces"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "SSR / OSI operational workspace"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "SSR / OSI operational workspaces"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/SsrOsiWorkspacesPage.jsx",
        ROOT / "frontend/src/pages/agency/PassengerServicesPage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)
    for path in [
        ROOT / "frontend/src/pages/platform/SsrOsiWorkspacesPage.jsx",
        ROOT / "frontend/src/pages/agency/PassengerServicesPage.jsx",
    ]:
        reject_text(path, "<button")
        reject_text(path, "apiPost")
        reject_text(path, "apiPut")


def verify_blueprint_adoption() -> None:
    adoption = get("/api/platform/blueprint/adoption-map", OWNER_HEADERS)
    categories = {item.get("category") for item in adoption.get("items") or []}
    if "SSR / OSI Operational Workspaces" not in categories:
        raise AssertionError(f"Blueprint adoption map missing SSR / OSI category: {categories}")
    gaps = get("/api/platform/blueprint/gaps", OWNER_HEADERS)
    already_built = " ".join(gaps.get("already_built") or [])
    if "Phase 41.9" not in already_built or "SSR / OSI" not in already_built:
        raise AssertionError(f"Blueprint gaps missing SSR / OSI foundation marker: {gaps}")
    chapter_41 = gaps.get("chapter_41_operational_workspaces") or []
    if "SSR / OSI operational workspaces" not in chapter_41:
        raise AssertionError(f"Chapter 41 map missing SSR / OSI workspace: {gaps}")


def verify_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")
    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("ssr_osi_operational_workspace_foundation") or {}
    for flag in [
        "ssr_osi_workspaces_enabled",
        "ssr_osi_workspace_metadata_enabled",
        "platform_ssr_osi_workspace_metadata_crud_enabled",
        "agency_ssr_osi_workspace_read_only_enabled",
        "passenger_services_ui_enabled",
        "ssr_osi_operations_ui_enabled",
        "filter_by_need_category_enabled",
        "filter_by_airline_enabled",
        "filter_by_approval_status_enabled",
        "filter_by_readiness_enabled",
        "filter_by_passenger_enabled",
        "filter_by_priority_enabled",
        "filter_by_rfic_enabled",
        "filter_by_rfisc_enabled",
        "passenger_need_metadata_enabled",
        "service_classification_metadata_enabled",
        "ssr_metadata_enabled",
        "osi_metadata_enabled",
        "airline_handling_metadata_enabled",
        "airport_handling_metadata_enabled",
        "emd_reference_metadata_enabled",
        "document_requirement_metadata_enabled",
        "medif_metadata_enabled",
        "operational_fulfilment_metadata_enabled",
        "readiness_metadata_enabled",
        "relationship_metadata_enabled",
        "aoie_operational_input_enabled",
        "metadata_only",
        "ssr_osi_workspace_metadata_only",
    ]:
        require_flag(section, flag)
    for flag in disabled_flags():
        require_flag(section, flag)
    require_flag(section, "readiness_required", False)
    if section.get("aoie_input_path") != AOIE_PATH:
        raise AssertionError(f"SSR / OSI readiness missing AOIE input path: {section}")
    for count_key in [
        "ssr_osi_workspace_count",
        "ssr_osi_operational_status_counts",
        "ssr_osi_readiness_status_counts",
        "ssr_osi_approval_status_counts",
        "ssr_osi_need_category_counts",
        "ssr_osi_airline_count",
        "ssr_osi_passenger_count",
        "ssr_osi_rfic_count",
        "ssr_osi_rfisc_count",
        "ssr_osi_emd_required_count",
        "ssr_osi_medif_required_count",
        "ssr_osi_approval_required_count",
        "ssr_osi_missing_requirement_count",
        "ssr_osi_unresolved_item_count",
        "ssr_osi_document_requirement_count",
        "ssr_osi_task_count",
        "ssr_osi_timeline_count",
        "ssr_osi_communication_count",
        "ssr_osi_flight_workspace_count",
        "ssr_osi_linked_document_count",
    ]:
        if count_key not in section:
            raise AssertionError(f"SSR / OSI readiness missing count: {count_key}")
    if not OPERATIONAL_STATUSES.issubset(set((section.get("ssr_osi_operational_status_counts") or {}).keys())):
        raise AssertionError(f"SSR / OSI readiness status counts missing statuses: {section}")
    if not READINESS_STATUSES.issubset(set((section.get("ssr_osi_readiness_status_counts") or {}).keys())):
        raise AssertionError(f"SSR / OSI readiness counts missing readiness statuses: {section}")
    if not APPROVAL_STATUSES.issubset(set((section.get("ssr_osi_approval_status_counts") or {}).keys())):
        raise AssertionError(f"SSR / OSI readiness counts missing approval statuses: {section}")
    if not NEED_CATEGORIES.issubset(set((section.get("ssr_osi_need_category_counts") or {}).keys())):
        raise AssertionError(f"SSR / OSI readiness counts missing need categories: {section}")
    previous_section = readiness.get("emd_workspace_foundation") or {}
    if previous_section.get("metadata_only") is not True:
        raise AssertionError("Previous EMD workspace section should remain metadata-only.")


def verify_endpoint_behavior() -> None:
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires seeded demo agency.")
    agency_id = agencies[0]["id"]

    created = post(
        "/api/platform/ssr-osi-workspaces",
        {
            "agency_id": agency_id,
            "operational_workspace_id": "operational-smoke",
            "passenger_workspace_id": "passenger-smoke",
            "travel_request_workspace_id": "request-smoke",
            "trip_workspace_id": "trip-smoke",
            "booking_workspace_id": "booking-smoke",
            "ticket_workspace_id": "ticket-smoke",
            "emd_workspace_id": "emd-smoke",
            "workspace_reference": "SSROSI-SMOKE-ENDPOINT",
            "operational_status": "review",
            "operational_priority": "high",
            "need_category": "mobility",
            "need_subcategory": "wheelchair",
            "need_description": "Passenger needs wheelchair assistance between gates.",
            "passenger_statement": "Long distances are difficult.",
            "service_family": "assistance",
            "service_type": "wheelchair",
            "ancillary_category": "assistance",
            "operational_category": "airport_assistance",
            "medical_category": "mobility",
            "mobility_category": "WCHR",
            "ssr_code": "WCHR",
            "ssr_description": "Wheelchair ramp assistance metadata.",
            "ssr_status": "requested",
            "ssr_confirmation_status": "pending",
            "osi_required": True,
            "osi_text": "OSI LH PASSENGER REQUESTS GATE DISTANCE SUPPORT",
            "osi_status": "draft",
            "airline_code": "LH",
            "validating_carrier": "LH",
            "operating_carrier": "LH",
            "approval_required": True,
            "approval_status": "pending",
            "approval_reference": "APR-SSR-ENDPOINT",
            "approval_deadline": "2028-04-01",
            "departure_station": "SOF",
            "connection_station": "FRA",
            "arrival_station": "JFK",
            "handling_company": "Airport Assist",
            "station_status": "pending",
            "emd_required": True,
            "emd_workspace_ids": ["emd-smoke"],
            "rfic": "C",
            "rfisc": "0B5",
            "document_requirements": ["MEDIF", "medical certificate"],
            "medif_required": True,
            "medif_workspace_id": "medif-smoke",
            "medical_certificate_required": True,
            "veterinary_documents_required": False,
            "customs_documents_required": False,
            "visa_documents_required": True,
            "task_ids": ["task-smoke"],
            "timeline_ids": ["timeline-smoke"],
            "communication_ids": ["communication-smoke"],
            "readiness_status": "awaiting_airline",
            "missing_requirements": ["airline approval"],
            "unresolved_items": ["MEDIF review"],
            "flight_workspace_ids": ["flight-smoke"],
            "linked_document_ids": ["document-smoke"],
            "agent_notes": "Agent metadata only.",
            "passenger_notes": "Passenger service note metadata.",
            "airline_notes": "Airline handling note metadata.",
            "internal_notes": "Internal operational metadata only.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    if created.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected create phase: {created.get('phase')}")
    assert_disabled_response(created)
    workspace = created.get("ssr_osi_workspace") or {}
    assert_workspace_shape(workspace)
    workspace_id = workspace.get("id")
    if not workspace_id:
        raise AssertionError(f"SSR / OSI workspace id missing: {created}")

    updated = put(
        f"/api/platform/ssr-osi-workspaces/{workspace_id}",
        {
            "operational_status": "ready",
            "readiness_status": "ready",
            "approval_status": "approved",
            "missing_requirements": [],
            "unresolved_items": [],
            "agent_notes": "Updated metadata only; no SSR/OSI transmission.",
            "metadata": {"updated": True, "metadata_only": True},
        },
        OWNER_HEADERS,
    )
    assert_disabled_response(updated)
    updated_workspace = updated.get("ssr_osi_workspace") or {}
    assert_workspace_shape(updated_workspace)
    if updated_workspace.get("readiness_status") != "ready" or updated_workspace.get("approval_status") != "approved":
        raise AssertionError(f"SSR / OSI workspace update did not persist metadata: {updated}")

    for filter_query in [
        f"agency_id={agency_id}",
        "need_category=mobility",
        "airline=LH",
        "approval_status=approved",
        "readiness_status=ready",
        "passenger=passenger-smoke",
        "priority=high",
        "rfic=C",
        "rfisc=0B5",
    ]:
        filtered = get(f"/api/platform/ssr-osi-workspaces?{filter_query}", OWNER_HEADERS)
        assert_disabled_response(filtered)
        if filtered.get("aoie_input") != AOIE_PATH:
            raise AssertionError(f"SSR / OSI list missing AOIE path: {filtered}")
        if not any(item.get("id") == workspace_id for item in filtered.get("items") or []):
            raise AssertionError(f"SSR / OSI filter {filter_query} missing created record: {filtered}")

    platform_summary = get("/api/platform/ssr-osi-workspaces/summary", OWNER_HEADERS)
    assert_summary_shape(platform_summary)

    platform_detail = get(f"/api/platform/ssr-osi-workspaces/{workspace_id}", OWNER_HEADERS)
    assert_disabled_response(platform_detail)
    assert_workspace_shape(platform_detail.get("ssr_osi_workspace") or {})

    agency_list = get(
        f"/api/agencies/{agency_id}/ssr-osi-workspaces?need_category=mobility&airline=LH&approval_status=approved&readiness_status=ready&passenger=passenger-smoke&priority=high&rfic=C&rfisc=0B5",
        OWNER_HEADERS,
    )
    assert_disabled_response(agency_list)
    if agency_list.get("read_only") is not True:
        raise AssertionError(f"Agency SSR / OSI list should be read-only: {agency_list}")
    if agency_list.get("aoie_input") != AOIE_PATH:
        raise AssertionError(f"Agency SSR / OSI list missing AOIE path: {agency_list}")
    agency_item = next((item for item in agency_list.get("items") or [] if item.get("id") == workspace_id), None)
    if not agency_item:
        raise AssertionError(f"Agency SSR / OSI list missing created record: {agency_list}")
    assert_workspace_shape(agency_item, agency_view=True)

    agency_summary = get(f"/api/agencies/{agency_id}/ssr-osi-workspaces/summary", OWNER_HEADERS)
    assert_summary_shape(agency_summary, agency_id=agency_id)
    if agency_summary.get("read_only") is not True:
        raise AssertionError(f"Agency SSR / OSI summary should be read-only: {agency_summary}")

    agency_detail = get(f"/api/agencies/{agency_id}/ssr-osi-workspaces/{workspace_id}", OWNER_HEADERS)
    assert_disabled_response(agency_detail)
    if agency_detail.get("read_only") is not True:
        raise AssertionError(f"Agency SSR / OSI detail should be read-only: {agency_detail}")
    assert_workspace_shape(agency_detail.get("ssr_osi_workspace") or {}, agency_view=True)

    deleted = request("DELETE", f"/api/platform/ssr-osi-workspaces/{workspace_id}", {}, OWNER_HEADERS)[1]
    assert_disabled_response(deleted)
    if deleted.get("archived") is not True or (deleted.get("ssr_osi_workspace") or {}).get("operational_status") != "archived":
        raise AssertionError(f"SSR / OSI delete should be metadata-only archive: {deleted}")

    after_delete = get(f"/api/platform/ssr-osi-workspaces?agency_id={agency_id}", OWNER_HEADERS)
    if any(item.get("id") == workspace_id for item in after_delete.get("items") or []):
        raise AssertionError(f"Default SSR / OSI list should exclude archived metadata: {after_delete}")
    include_archived = get(f"/api/platform/ssr-osi-workspaces?agency_id={agency_id}&include_archived=true", OWNER_HEADERS)
    if not any(item.get("id") == workspace_id for item in include_archived.get("items") or []):
        raise AssertionError(f"include_archived should expose metadata-archived SSR / OSI workspace: {include_archived}")

    request("POST", f"/api/agencies/{agency_id}/ssr-osi-workspaces", {"need_category": "mobility"}, OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/ssr-osi-workspaces/{workspace_id}", {"readiness_status": "ready"}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/ssr-osi-workspaces/{workspace_id}", {}, OWNER_HEADERS, 405)


def assert_workspace_shape(workspace: dict, *, agency_view: bool = False) -> None:
    for key in [
        "id",
        "agency_id",
        "operational_workspace_id",
        "passenger_workspace_id",
        "travel_request_workspace_id",
        "trip_workspace_id",
        "booking_workspace_id",
        "ticket_workspace_id",
        "emd_workspace_id",
        "workspace_reference",
        "operational_status",
        "operational_priority",
        "need_category",
        "need_subcategory",
        "need_description",
        "passenger_statement",
        "service_family",
        "service_type",
        "ancillary_category",
        "operational_category",
        "medical_category",
        "mobility_category",
        "ssr_code",
        "ssr_description",
        "ssr_status",
        "ssr_confirmation_status",
        "osi_required",
        "osi_text",
        "osi_status",
        "airline_code",
        "validating_carrier",
        "operating_carrier",
        "approval_required",
        "approval_status",
        "approval_reference",
        "approval_deadline",
        "departure_station",
        "connection_station",
        "arrival_station",
        "handling_company",
        "station_status",
        "emd_required",
        "emd_workspace_ids",
        "rfic",
        "rfisc",
        "document_requirements",
        "medif_required",
        "medif_workspace_id",
        "medical_certificate_required",
        "veterinary_documents_required",
        "customs_documents_required",
        "visa_documents_required",
        "task_ids",
        "timeline_ids",
        "communication_ids",
        "readiness_status",
        "missing_requirements",
        "unresolved_items",
        "flight_workspace_ids",
        "linked_document_ids",
        "agent_notes",
        "passenger_notes",
        "airline_notes",
        "internal_notes",
        "aoie_operational_input",
    ]:
        if key not in workspace:
            raise AssertionError(f"SSR / OSI workspace missing {key}: {workspace}")
    if workspace.get("metadata_only") is not True or workspace.get("ssr_osi_workspace_metadata_only") is not True:
        raise AssertionError(f"SSR / OSI workspace is not metadata-only: {workspace}")
    if agency_view and workspace.get("read_only") is not True:
        raise AssertionError(f"Agency SSR / OSI workspace should be read-only: {workspace}")
    for flag in disabled_flags():
        if workspace.get(flag) is not True:
            raise AssertionError(f"SSR / OSI workspace missing disabled flag {flag}: {workspace}")


def assert_summary_shape(payload: dict, *, agency_id: str | None = None) -> None:
    assert_disabled_response(payload)
    if agency_id and payload.get("agency_id") != agency_id:
        raise AssertionError(f"Agency summary not scoped to agency: {payload}")
    summary = payload.get("summary") or {}
    for key in [
        "total_count",
        "by_operational_status",
        "by_readiness_status",
        "by_approval_status",
        "by_need_category",
        "by_airline",
        "by_rfic",
        "by_rfisc",
        "agency_count",
        "passenger_count",
        "emd_workspace_link_count",
        "document_requirement_count",
        "missing_requirement_count",
        "unresolved_item_count",
        "task_count",
        "timeline_count",
        "communication_count",
        "flight_workspace_count",
        "linked_document_count",
        "metadata_only",
    ]:
        if key not in summary:
            raise AssertionError(f"SSR / OSI summary missing {key}: {payload}")
    if not OPERATIONAL_STATUSES.issubset(set((summary.get("by_operational_status") or {}).keys())):
        raise AssertionError(f"SSR / OSI summary missing operational statuses: {payload}")
    if not READINESS_STATUSES.issubset(set((summary.get("by_readiness_status") or {}).keys())):
        raise AssertionError(f"SSR / OSI summary missing readiness statuses: {payload}")
    if not APPROVAL_STATUSES.issubset(set((summary.get("by_approval_status") or {}).keys())):
        raise AssertionError(f"SSR / OSI summary missing approval statuses: {payload}")
    if not NEED_CATEGORIES.issubset(set((summary.get("by_need_category") or {}).keys())):
        raise AssertionError(f"SSR / OSI summary missing need categories: {payload}")


def main() -> int:
    verify_model_and_collection_registration()
    openapi = get("/openapi.json")
    verify_routes(openapi.get("paths") or {})
    verify_frontend_and_docs()
    verify_blueprint_adoption()
    verify_readiness()
    verify_endpoint_behavior()
    print("Phase 41.9 SSR / OSI operational workspace foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
