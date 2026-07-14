#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import (
    TravelRequestWorkspace,
    TravelRequestWorkspaceCreate,
    TravelRequestWorkspacePriority,
    TravelRequestWorkspaceStatus,
    TravelRequestWorkspaceType,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_55_2_airline_policy_evidence_source_governance_foundation"
ROOT = Path(__file__).resolve().parents[2]
REQUEST_TYPES = {"general", "flight", "hotel", "package", "multi_city", "group", "corporate", "leisure", "disruption", "service"}
REQUEST_STATUSES = {"draft", "new", "triage", "open", "researching", "waiting", "quoted", "completed", "archived"}
REQUEST_PRIORITIES = {"low", "medium", "high", "urgent"}


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
        "booking_execution_disabled",
        "ticket_issuance_disabled",
        "gds_live_connectivity_disabled",
        "ndc_connectivity_disabled",
        "payment_processing_disabled",
        "email_sending_disabled",
        "sms_sending_disabled",
        "ai_automation_disabled",
        "external_api_calls_disabled",
        "supplier_integrations_disabled",
        "live_airline_calls_disabled",
        "background_workers_disabled",
        "automatic_trip_creation_disabled",
        "automatic_offer_creation_disabled",
        "automation_disabled",
    ]


def forbidden_enabled_flags() -> list[str]:
    return [
        "booking_execution_enabled",
        "ticket_issuance_enabled",
        "gds_live_connectivity_enabled",
        "ndc_connectivity_enabled",
        "payment_processing_enabled",
        "email_sending_enabled",
        "sms_sending_enabled",
        "ai_automation_enabled",
        "external_api_calls_enabled",
        "supplier_integrations_enabled",
        "live_airline_calls_enabled",
        "background_workers_enabled",
        "automatic_trip_creation_enabled",
        "automatic_offer_creation_enabled",
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
    create_payload = TravelRequestWorkspaceCreate(
        agency_id="agency-smoke",
        operational_workspace_id="workspace-smoke",
        request_reference="TRW-SMOKE-MODEL",
        request_title="Travel request workspace smoke",
        request_type=TravelRequestWorkspaceType.FLIGHT,
        request_status=TravelRequestWorkspaceStatus.OPEN,
        request_priority=TravelRequestWorkspacePriority.HIGH,
        client_id="client-smoke",
        primary_passenger_id="passenger-smoke",
        requester_name="Request Owner",
        requester_email="requester@example.com",
        requester_phone="+359888000000",
        requested_service_categories=["flight", "mobility_assistance"],
        requested_origin="SOF",
        requested_destination="JFK",
        requested_departure_date="2027-08-10",
        requested_return_date="2027-08-20",
        passenger_count=2,
        passenger_type_summary="1 adult, 1 child",
        flexibility_notes="Flexible by one day.",
        special_service_notes="Wheelchair assistance requested.",
        budget_notes="Prefer refundable fares.",
        deadline="2027-07-31",
        assigned_agent="Avery Agent",
        internal_notes="Metadata-only request workspace smoke.",
        linked_trip_ids=["trip-smoke"],
        linked_offer_ids=["offer-smoke"],
        linked_document_ids=["document-smoke"],
        metadata={"smoke": True},
    )
    request_workspace = TravelRequestWorkspace(**create_payload.model_dump(mode="json", exclude_none=True))
    dumped = request_workspace.model_dump(mode="json")
    if dumped.get("request_type") != "flight" or dumped.get("request_status") != "open" or dumped.get("request_priority") != "high":
        raise AssertionError(f"Request workspace dimensions were not preserved: {dumped}")
    for key in ["metadata_only", "travel_request_workspace_metadata_only", *disabled_flags()]:
        if dumped.get(key) is not True:
            raise AssertionError(f"Travel request workspace model missing disabled flag {key}: {dumped}")
    if "travel_request_workspaces" not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("Travel request workspaces collection is not registered.")
    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "travel_request_workspaces_id_unique",
        "travel_request_workspaces_reference_unique",
        "travel_request_workspaces_agency_status_lookup",
        "travel_request_workspaces_agency_type_lookup",
        "travel_request_workspaces_agency_priority_lookup",
        "travel_request_workspaces_operational_workspace_lookup",
        "travel_request_workspaces_status_priority_lookup",
        "travel_request_workspaces_type_lookup",
        "travel_request_workspaces_assigned_agent_lookup",
        "travel_request_workspaces_departure_date_lookup",
        "travel_request_workspaces_deadline_lookup",
        "travel_request_workspaces_client_lookup",
        "travel_request_workspaces_primary_passenger_lookup",
        "travel_request_workspaces_trip_lookup",
        "travel_request_workspaces_offer_lookup",
        "travel_request_workspaces_document_lookup",
        "travel_request_workspaces_created_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Travel request workspace index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    expected_methods = {
        "/api/platform/travel-request-workspaces": {"get", "post"},
        "/api/platform/travel-request-workspaces/summary": {"get"},
        "/api/platform/travel-request-workspaces/{request_workspace_id}": {"get", "put", "delete"},
        "/api/agencies/{agency_id}/travel-request-workspaces": {"get"},
        "/api/agencies/{agency_id}/travel-request-workspaces/summary": {"get"},
        "/api/agencies/{agency_id}/travel-request-workspaces/{request_workspace_id}": {"get"},
    }
    for path, methods in expected_methods.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in [
        "/api/agencies/{agency_id}/travel-request-workspaces",
        "/api/agencies/{agency_id}/travel-request-workspaces/summary",
        "/api/agencies/{agency_id}/travel-request-workspaces/{request_workspace_id}",
    ]:
        methods = set(paths.get(path, {}).keys())
        blocked_methods = methods & {"post", "put", "patch", "delete"}
        if blocked_methods:
            raise AssertionError(f"Agency travel request workspace route is not read-only: {path} {sorted(blocked_methods)}")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Travel Request Workspaces"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Travel Requests"),
        (ROOT / "frontend/src/App.jsx", "/platform/travel-request-workspaces"),
        (ROOT / "frontend/src/App.jsx", "/agency/travel-requests"),
        (ROOT / "frontend/src/pages/platform/TravelRequestWorkspacesPage.jsx", "Travel Request Workspaces"),
        (ROOT / "frontend/src/pages/platform/TravelRequestWorkspacesPage.jsx", "No trip or offer automation"),
        (ROOT / "frontend/src/pages/platform/TravelRequestWorkspacesPage.jsx", "Linked records"),
        (ROOT / "frontend/src/pages/agency/TravelRequestsPage.jsx", "Travel Requests"),
        (ROOT / "frontend/src/pages/agency/TravelRequestsPage.jsx", "Read-only travel request workspace metadata"),
        (ROOT / "docs/architecture/travel-request-workspace-foundation.md", "Travel Request Workspace Foundation"),
        (ROOT / "README.md", "Phase 41.1 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 41.1: Travel Request Workspace Foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "Phase 41.1 adds travel request workspace metadata"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "Phase 41.1 adds travel request workspace APIs"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Travel request workspaces"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Travel request workspaces"),
        (ROOT / "backend/services/blueprint_adoption_service.py", "Travel Request Workspaces"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/TravelRequestWorkspacesPage.jsx",
        ROOT / "frontend/src/pages/agency/TravelRequestsPage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)
    for path in [
        ROOT / "frontend/src/pages/platform/TravelRequestWorkspacesPage.jsx",
        ROOT / "frontend/src/pages/agency/TravelRequestsPage.jsx",
    ]:
        reject_text(path, "<button")
        reject_text(path, "apiPost")
        reject_text(path, "apiPut")


def verify_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")
    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("travel_request_workspace_foundation") or {}
    for flag in [
        "travel_request_workspaces_enabled",
        "travel_request_workspace_metadata_enabled",
        "platform_travel_request_workspace_metadata_crud_enabled",
        "agency_travel_request_workspace_read_only_enabled",
        "request_workspace_filter_by_agency_enabled",
        "request_workspace_filter_by_status_enabled",
        "request_workspace_filter_by_type_enabled",
        "request_workspace_filter_by_priority_enabled",
        "request_workspace_filter_by_assigned_agent_enabled",
        "request_workspace_filter_by_departure_date_enabled",
        "request_workspace_filter_by_operational_workspace_enabled",
        "operational_workspace_link_metadata_enabled",
        "requester_metadata_enabled",
        "client_passenger_metadata_enabled",
        "requested_route_metadata_enabled",
        "requested_dates_metadata_enabled",
        "passenger_summary_metadata_enabled",
        "requested_services_metadata_enabled",
        "special_service_notes_metadata_enabled",
        "budget_notes_metadata_enabled",
        "deadline_metadata_enabled",
        "linked_trip_metadata_enabled",
        "linked_offer_metadata_enabled",
        "linked_document_metadata_enabled",
        "internal_notes_metadata_enabled",
        "read_only_ui_enabled",
        "metadata_only",
        "travel_request_workspace_metadata_only",
    ]:
        require_flag(section, flag)
    for flag in disabled_flags():
        require_flag(section, flag)
    require_flag(section, "readiness_required", False)
    for count_key in ["request_workspace_count", "request_workspace_status_counts", "request_workspace_type_counts", "request_workspace_priority_counts"]:
        if count_key not in section:
            raise AssertionError(f"Travel request workspace readiness missing count: {count_key}")
    if not REQUEST_STATUSES.issubset(set((section.get("request_workspace_status_counts") or {}).keys())):
        raise AssertionError(f"Travel request workspace readiness status counts missing statuses: {section}")
    if not REQUEST_TYPES.issubset(set((section.get("request_workspace_type_counts") or {}).keys())):
        raise AssertionError(f"Travel request workspace readiness type counts missing types: {section}")
    if not REQUEST_PRIORITIES.issubset(set((section.get("request_workspace_priority_counts") or {}).keys())):
        raise AssertionError(f"Travel request workspace readiness priority counts missing priorities: {section}")
    previous_section = readiness.get("operational_travel_workspace_foundation") or {}
    if previous_section.get("metadata_only") is not True:
        raise AssertionError("Previous operational travel workspace section should remain metadata-only.")


def verify_endpoint_behavior() -> None:
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires seeded demo agency.")
    agency_id = agencies[0]["id"]

    workspace_created = post(
        "/api/platform/operational-travel-workspaces",
        {
            "agency_id": agency_id,
            "workspace_title": "Phase 41.1 parent operational workspace smoke",
            "workspace_type": "request",
            "workspace_status": "open",
            "priority": "high",
            "assigned_team": ["requests"],
            "assigned_agent": "Avery Agent",
            "travel_start_date": "2027-08-10",
            "travel_end_date": "2027-08-20",
            "origin_summary": "SOF",
            "destination_summary": "JFK",
            "service_summary": "Request workspace parent metadata",
            "operational_notes": "Metadata-only parent workspace for travel request smoke.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    operational_workspace_id = (workspace_created.get("workspace") or {}).get("id")
    if not operational_workspace_id:
        raise AssertionError(f"Parent operational workspace id missing: {workspace_created}")

    created = post(
        "/api/platform/travel-request-workspaces",
        {
            "agency_id": agency_id,
            "operational_workspace_id": operational_workspace_id,
            "request_title": "Phase 41.1 travel request workspace smoke",
            "request_type": "flight",
            "request_status": "open",
            "request_priority": "high",
            "client_id": "client-smoke",
            "primary_passenger_id": "passenger-smoke",
            "requester_name": "Request Owner",
            "requester_email": "requester@example.com",
            "requester_phone": "+359888000000",
            "requested_service_categories": ["flight", "mobility_assistance"],
            "requested_origin": "SOF",
            "requested_destination": "JFK",
            "requested_departure_date": "2027-08-10",
            "requested_return_date": "2027-08-20",
            "passenger_count": 2,
            "passenger_type_summary": "1 adult, 1 child",
            "flexibility_notes": "Flexible by one day.",
            "special_service_notes": "Wheelchair assistance requested.",
            "budget_notes": "Prefer refundable fares.",
            "deadline": "2027-07-31",
            "assigned_agent": "Avery Agent",
            "internal_notes": "Metadata-only request workspace smoke.",
            "linked_trip_ids": ["trip-smoke"],
            "linked_offer_ids": ["offer-smoke"],
            "linked_document_ids": ["document-smoke"],
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    if created.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected create phase: {created.get('phase')}")
    assert_disabled_response(created)
    request_workspace = created.get("request_workspace") or {}
    assert_request_shape(request_workspace)
    request_workspace_id = request_workspace.get("id")
    if not request_workspace_id:
        raise AssertionError(f"Travel request workspace id missing: {created}")

    updated = put(
        f"/api/platform/travel-request-workspaces/{request_workspace_id}",
        {
            "request_status": "researching",
            "request_priority": "urgent",
            "assigned_agent": "Jordan Agent",
            "internal_notes": "Updated metadata only; no trip conversion or offer creation.",
            "metadata": {"updated": True, "metadata_only": True},
        },
        OWNER_HEADERS,
    )
    assert_disabled_response(updated)
    updated_request = updated.get("request_workspace") or {}
    assert_request_shape(updated_request)
    if updated_request.get("request_status") != "researching" or updated_request.get("request_priority") != "urgent":
        raise AssertionError(f"Request workspace update did not persist metadata: {updated}")

    for filter_query in [
        f"agency_id={agency_id}",
        "status=researching",
        "request_type=flight",
        "priority=urgent",
        "assigned_agent=Jordan+Agent",
        "departure_date=2027-08-10",
        f"operational_workspace_id={operational_workspace_id}",
    ]:
        filtered = get(f"/api/platform/travel-request-workspaces?{filter_query}", OWNER_HEADERS)
        assert_disabled_response(filtered)
        if not any(item.get("id") == request_workspace_id for item in filtered.get("items") or []):
            raise AssertionError(f"Travel request workspace filter {filter_query} missing created record: {filtered}")

    platform_summary = get("/api/platform/travel-request-workspaces/summary", OWNER_HEADERS)
    assert_summary_shape(platform_summary)

    platform_detail = get(f"/api/platform/travel-request-workspaces/{request_workspace_id}", OWNER_HEADERS)
    assert_disabled_response(platform_detail)
    assert_request_shape(platform_detail.get("request_workspace") or {})

    agency_list = get(f"/api/agencies/{agency_id}/travel-request-workspaces?status=researching&priority=urgent", OWNER_HEADERS)
    assert_disabled_response(agency_list)
    if agency_list.get("read_only") is not True:
        raise AssertionError(f"Agency request workspace list should be read-only: {agency_list}")
    agency_item = next((item for item in agency_list.get("items") or [] if item.get("id") == request_workspace_id), None)
    if not agency_item:
        raise AssertionError(f"Agency request workspace list missing created record: {agency_list}")
    assert_request_shape(agency_item, agency_view=True)

    agency_summary = get(f"/api/agencies/{agency_id}/travel-request-workspaces/summary", OWNER_HEADERS)
    assert_summary_shape(agency_summary, agency_id=agency_id)
    if agency_summary.get("read_only") is not True:
        raise AssertionError(f"Agency request workspace summary should be read-only: {agency_summary}")

    agency_detail = get(f"/api/agencies/{agency_id}/travel-request-workspaces/{request_workspace_id}", OWNER_HEADERS)
    assert_disabled_response(agency_detail)
    if agency_detail.get("read_only") is not True:
        raise AssertionError(f"Agency request workspace detail should be read-only: {agency_detail}")
    assert_request_shape(agency_detail.get("request_workspace") or {}, agency_view=True)

    deleted = request("DELETE", f"/api/platform/travel-request-workspaces/{request_workspace_id}", {}, OWNER_HEADERS)[1]
    assert_disabled_response(deleted)
    if deleted.get("deleted") is not True or (deleted.get("request_workspace") or {}).get("request_status") != "archived":
        raise AssertionError(f"Travel request workspace delete should be metadata-only archive: {deleted}")

    after_delete = get(f"/api/platform/travel-request-workspaces?agency_id={agency_id}", OWNER_HEADERS)
    if any(item.get("id") == request_workspace_id for item in after_delete.get("items") or []):
        raise AssertionError(f"Default request workspace list should exclude archived-delete metadata: {after_delete}")
    include_archived = get(f"/api/platform/travel-request-workspaces?agency_id={agency_id}&include_archived=true", OWNER_HEADERS)
    if not any(item.get("id") == request_workspace_id for item in include_archived.get("items") or []):
        raise AssertionError(f"include_archived should expose metadata-archived request workspace: {include_archived}")

    request("POST", f"/api/agencies/{agency_id}/travel-request-workspaces", {"request_title": "blocked"}, OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/travel-request-workspaces/{request_workspace_id}", {"request_status": "open"}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/travel-request-workspaces/{request_workspace_id}", {}, OWNER_HEADERS, 405)


def assert_request_shape(request_workspace: dict, *, agency_view: bool = False) -> None:
    for key in [
        "id",
        "agency_id",
        "operational_workspace_id",
        "request_reference",
        "request_title",
        "request_type",
        "request_status",
        "request_priority",
        "client_id",
        "primary_passenger_id",
        "requester_name",
        "requester_email",
        "requester_phone",
        "requested_service_categories",
        "requested_origin",
        "requested_destination",
        "requested_departure_date",
        "requested_return_date",
        "passenger_count",
        "passenger_type_summary",
        "flexibility_notes",
        "special_service_notes",
        "budget_notes",
        "deadline",
        "assigned_agent",
        "internal_notes",
        "linked_trip_ids",
        "linked_offer_ids",
        "linked_document_ids",
        "operational_workspace",
        "client",
        "primary_passenger",
        "linked_trips",
        "linked_offers",
        "linked_documents",
    ]:
        if key not in request_workspace:
            raise AssertionError(f"Travel request workspace missing {key}: {request_workspace}")
    if request_workspace.get("metadata_only") is not True or request_workspace.get("travel_request_workspace_metadata_only") is not True:
        raise AssertionError(f"Travel request workspace is not metadata-only: {request_workspace}")
    if agency_view and request_workspace.get("read_only") is not True:
        raise AssertionError(f"Agency travel request workspace should be read-only: {request_workspace}")
    for flag in disabled_flags():
        if request_workspace.get(flag) is not True:
            raise AssertionError(f"Travel request workspace missing disabled flag {flag}: {request_workspace}")
    if not request_workspace.get("linked_trips") or not request_workspace.get("linked_offers") or not request_workspace.get("linked_documents"):
        raise AssertionError(f"Travel request workspace linked metadata shape missing references: {request_workspace}")
    if not request_workspace.get("operational_workspace"):
        raise AssertionError(f"Travel request workspace missing operational workspace context: {request_workspace}")


def assert_summary_shape(payload: dict, *, agency_id: str | None = None) -> None:
    assert_disabled_response(payload)
    if agency_id and payload.get("agency_id") != agency_id:
        raise AssertionError(f"Agency summary not scoped to agency: {payload}")
    summary = payload.get("summary") or {}
    for key in [
        "total_count",
        "by_status",
        "by_type",
        "by_priority",
        "agency_count",
        "assigned_agent_count",
        "operational_workspace_count",
        "passenger_count_total",
        "linked_trip_count",
        "linked_offer_count",
        "linked_document_count",
        "metadata_only",
    ]:
        if key not in summary:
            raise AssertionError(f"Travel request workspace summary missing {key}: {payload}")
    if not REQUEST_STATUSES.issubset(set((summary.get("by_status") or {}).keys())):
        raise AssertionError(f"Travel request workspace summary missing statuses: {payload}")
    if not REQUEST_TYPES.issubset(set((summary.get("by_type") or {}).keys())):
        raise AssertionError(f"Travel request workspace summary missing types: {payload}")
    if not REQUEST_PRIORITIES.issubset(set((summary.get("by_priority") or {}).keys())):
        raise AssertionError(f"Travel request workspace summary missing priorities: {payload}")


def main() -> int:
    verify_model_and_collection_registration()
    openapi = get("/openapi.json")
    verify_routes(openapi.get("paths") or {})
    verify_frontend_and_docs()
    verify_readiness()
    verify_endpoint_behavior()
    print("Phase 41.1 travel request workspace foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
