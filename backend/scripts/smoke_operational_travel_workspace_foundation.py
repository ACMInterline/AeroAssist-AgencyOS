#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import (
    OperationalTravelWorkspace,
    OperationalTravelWorkspaceCreate,
    OperationalTravelWorkspacePriority,
    OperationalTravelWorkspaceStatus,
    OperationalTravelWorkspaceType,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_55_6_interline_codeshare_operating_carrier_intelligence_foundation"
ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_TYPES = {"general", "request", "trip", "offer", "booking", "ticketing", "documents", "disruption", "service_case"}
WORKSPACE_STATUSES = {"draft", "open", "active", "waiting", "review", "completed", "archived"}
WORKSPACE_PRIORITIES = {"low", "medium", "high", "urgent"}


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
    create_payload = OperationalTravelWorkspaceCreate(
        agency_id="agency-smoke",
        workspace_reference="OTW-SMOKE-MODEL",
        workspace_title="Operational workspace smoke",
        workspace_type=OperationalTravelWorkspaceType.TRIP,
        workspace_status=OperationalTravelWorkspaceStatus.OPEN,
        primary_client_id="client-smoke",
        primary_passenger_id="passenger-smoke",
        linked_request_ids=["request-smoke"],
        linked_trip_ids=["trip-smoke"],
        linked_offer_ids=["offer-smoke"],
        linked_booking_ids=["booking-smoke"],
        linked_ticket_ids=["ticket-smoke"],
        linked_document_ids=["document-smoke"],
        priority=OperationalTravelWorkspacePriority.HIGH,
        assigned_team=["operations"],
        assigned_agent="Avery Agent",
        travel_start_date="2027-07-10",
        travel_end_date="2027-07-20",
        origin_summary="SOF",
        destination_summary="JFK",
        service_summary="Round trip service support",
        operational_notes="Metadata-only workspace smoke.",
        metadata={"smoke": True},
    )
    workspace = OperationalTravelWorkspace(**create_payload.model_dump(mode="json", exclude_none=True))
    dumped = workspace.model_dump(mode="json")
    if dumped.get("workspace_type") != "trip" or dumped.get("workspace_status") != "open" or dumped.get("priority") != "high":
        raise AssertionError(f"Workspace dimensions were not preserved: {dumped}")
    for key in ["metadata_only", "operational_workspace_metadata_only", *disabled_flags()]:
        if dumped.get(key) is not True:
            raise AssertionError(f"Operational workspace model missing disabled flag {key}: {dumped}")
    if "operational_travel_workspaces" not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("Operational travel workspaces collection is not registered.")
    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "operational_travel_workspaces_id_unique",
        "operational_travel_workspaces_reference_unique",
        "operational_travel_workspaces_agency_status_lookup",
        "operational_travel_workspaces_agency_type_lookup",
        "operational_travel_workspaces_agency_priority_lookup",
        "operational_travel_workspaces_status_priority_lookup",
        "operational_travel_workspaces_type_lookup",
        "operational_travel_workspaces_assigned_agent_lookup",
        "operational_travel_workspaces_travel_dates_lookup",
        "operational_travel_workspaces_primary_client_lookup",
        "operational_travel_workspaces_primary_passenger_lookup",
        "operational_travel_workspaces_request_lookup",
        "operational_travel_workspaces_trip_lookup",
        "operational_travel_workspaces_offer_lookup",
        "operational_travel_workspaces_booking_lookup",
        "operational_travel_workspaces_ticket_lookup",
        "operational_travel_workspaces_document_lookup",
        "operational_travel_workspaces_created_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Operational travel workspace index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    expected_methods = {
        "/api/platform/operational-travel-workspaces": {"get", "post"},
        "/api/platform/operational-travel-workspaces/summary": {"get"},
        "/api/platform/operational-travel-workspaces/{workspace_id}": {"get", "put", "delete"},
        "/api/agencies/{agency_id}/operational-travel-workspaces": {"get"},
        "/api/agencies/{agency_id}/operational-travel-workspaces/summary": {"get"},
        "/api/agencies/{agency_id}/operational-travel-workspaces/{workspace_id}": {"get"},
    }
    for path, methods in expected_methods.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in [
        "/api/agencies/{agency_id}/operational-travel-workspaces",
        "/api/agencies/{agency_id}/operational-travel-workspaces/summary",
        "/api/agencies/{agency_id}/operational-travel-workspaces/{workspace_id}",
    ]:
        methods = set(paths.get(path, {}).keys())
        blocked_methods = methods & {"post", "put", "patch", "delete"}
        if blocked_methods:
            raise AssertionError(f"Agency operational travel workspace route is not read-only: {path} {sorted(blocked_methods)}")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Operational Travel Workspaces"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Travel Workspaces"),
        (ROOT / "frontend/src/App.jsx", "/platform/operational-travel-workspaces"),
        (ROOT / "frontend/src/App.jsx", "/agency/travel-workspaces"),
        (ROOT / "frontend/src/pages/platform/OperationalTravelWorkspacesPage.jsx", "Operational Travel Workspaces"),
        (ROOT / "frontend/src/pages/platform/OperationalTravelWorkspacesPage.jsx", "No provider actions"),
        (ROOT / "frontend/src/pages/platform/OperationalTravelWorkspacesPage.jsx", "Linked records"),
        (ROOT / "frontend/src/pages/agency/TravelWorkspacesPage.jsx", "Travel Workspaces"),
        (ROOT / "frontend/src/pages/agency/TravelWorkspacesPage.jsx", "Read-only operational travel workspace metadata"),
        (ROOT / "docs/architecture/operational-travel-workspace-foundation.md", "Operational Travel Workspace Foundation"),
        (ROOT / "README.md", "Phase 41.0 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 41.0: Operational Travel Workspace Foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "Phase 41.0 adds operational travel workspace metadata"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "Phase 41.0 adds operational travel workspace APIs"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Operational travel workspaces"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Operational travel workspaces"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/OperationalTravelWorkspacesPage.jsx",
        ROOT / "frontend/src/pages/agency/TravelWorkspacesPage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)
    for path in [
        ROOT / "frontend/src/pages/platform/OperationalTravelWorkspacesPage.jsx",
        ROOT / "frontend/src/pages/agency/TravelWorkspacesPage.jsx",
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
    section = readiness.get("operational_travel_workspace_foundation") or {}
    for flag in [
        "operational_travel_workspaces_enabled",
        "operational_travel_workspace_metadata_enabled",
        "platform_operational_travel_workspace_metadata_crud_enabled",
        "agency_operational_travel_workspace_read_only_enabled",
        "workspace_filter_by_agency_enabled",
        "workspace_filter_by_status_enabled",
        "workspace_filter_by_type_enabled",
        "workspace_filter_by_priority_enabled",
        "workspace_filter_by_assigned_agent_enabled",
        "workspace_filter_by_travel_date_enabled",
        "primary_client_metadata_enabled",
        "primary_passenger_metadata_enabled",
        "linked_request_metadata_enabled",
        "linked_trip_metadata_enabled",
        "linked_offer_metadata_enabled",
        "linked_booking_metadata_enabled",
        "linked_ticket_metadata_enabled",
        "linked_document_metadata_enabled",
        "origin_summary_metadata_enabled",
        "destination_summary_metadata_enabled",
        "service_summary_metadata_enabled",
        "operational_notes_metadata_enabled",
        "assigned_team_metadata_enabled",
        "read_only_ui_enabled",
        "metadata_only",
        "operational_workspace_metadata_only",
    ]:
        require_flag(section, flag)
    for flag in disabled_flags():
        require_flag(section, flag)
    require_flag(section, "readiness_required", False)
    for count_key in ["workspace_count", "workspace_status_counts", "workspace_type_counts", "workspace_priority_counts"]:
        if count_key not in section:
            raise AssertionError(f"Operational workspace readiness missing count: {count_key}")
    if not WORKSPACE_STATUSES.issubset(set((section.get("workspace_status_counts") or {}).keys())):
        raise AssertionError(f"Operational workspace readiness status counts missing statuses: {section}")
    if not WORKSPACE_TYPES.issubset(set((section.get("workspace_type_counts") or {}).keys())):
        raise AssertionError(f"Operational workspace readiness type counts missing types: {section}")
    if not WORKSPACE_PRIORITIES.issubset(set((section.get("workspace_priority_counts") or {}).keys())):
        raise AssertionError(f"Operational workspace readiness priority counts missing priorities: {section}")
    previous_section = readiness.get("feature_bundle_rollout_summary_pack_foundation") or {}
    if previous_section.get("metadata_only") is not True:
        raise AssertionError("Previous summary pack section should remain metadata-only.")


def verify_endpoint_behavior() -> None:
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires seeded demo agency.")
    agency_id = agencies[0]["id"]

    created = post(
        "/api/platform/operational-travel-workspaces",
        {
            "agency_id": agency_id,
            "workspace_title": "Phase 41.0 operational workspace smoke",
            "workspace_type": "trip",
            "workspace_status": "open",
            "primary_client_id": "client-smoke",
            "primary_passenger_id": "passenger-smoke",
            "linked_request_ids": ["request-smoke"],
            "linked_trip_ids": ["trip-smoke"],
            "linked_offer_ids": ["offer-smoke"],
            "linked_booking_ids": ["booking-smoke"],
            "linked_ticket_ids": ["ticket-smoke"],
            "linked_document_ids": ["document-smoke"],
            "priority": "high",
            "assigned_team": ["operations", "after-hours"],
            "assigned_agent": "Avery Agent",
            "travel_start_date": "2027-07-10",
            "travel_end_date": "2027-07-20",
            "origin_summary": "SOF",
            "destination_summary": "JFK",
            "service_summary": "Round trip service support",
            "operational_notes": "Metadata-only operational travel workspace smoke.",
            "metadata": {"smoke": True, "metadata_only": True},
        },
        OWNER_HEADERS,
        201,
    )
    if created.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected create phase: {created.get('phase')}")
    assert_disabled_response(created)
    workspace = created.get("workspace") or {}
    assert_workspace_shape(workspace)
    workspace_id = workspace.get("id")
    if not workspace_id:
        raise AssertionError(f"Workspace id missing: {created}")

    updated = put(
        f"/api/platform/operational-travel-workspaces/{workspace_id}",
        {
            "workspace_status": "active",
            "priority": "urgent",
            "assigned_agent": "Jordan Agent",
            "operational_notes": "Updated metadata only; no booking or ticketing action.",
            "metadata": {"updated": True, "metadata_only": True},
        },
        OWNER_HEADERS,
    )
    assert_disabled_response(updated)
    updated_workspace = updated.get("workspace") or {}
    assert_workspace_shape(updated_workspace)
    if updated_workspace.get("workspace_status") != "active" or updated_workspace.get("priority") != "urgent":
        raise AssertionError(f"Workspace update did not persist metadata: {updated}")

    for filter_query in [
        f"agency_id={agency_id}",
        "status=active",
        "workspace_type=trip",
        "priority=urgent",
        "assigned_agent=Jordan+Agent",
        "travel_date=2027-07-15",
    ]:
        filtered = get(f"/api/platform/operational-travel-workspaces?{filter_query}", OWNER_HEADERS)
        assert_disabled_response(filtered)
        if not any(item.get("id") == workspace_id for item in filtered.get("items") or []):
            raise AssertionError(f"Operational workspace filter {filter_query} missing created record: {filtered}")

    platform_summary = get("/api/platform/operational-travel-workspaces/summary", OWNER_HEADERS)
    assert_summary_shape(platform_summary)

    platform_detail = get(f"/api/platform/operational-travel-workspaces/{workspace_id}", OWNER_HEADERS)
    assert_disabled_response(platform_detail)
    assert_workspace_shape(platform_detail.get("workspace") or {})

    agency_list = get(f"/api/agencies/{agency_id}/operational-travel-workspaces?status=active&priority=urgent", OWNER_HEADERS)
    assert_disabled_response(agency_list)
    if agency_list.get("read_only") is not True:
        raise AssertionError(f"Agency workspace list should be read-only: {agency_list}")
    agency_item = next((item for item in agency_list.get("items") or [] if item.get("id") == workspace_id), None)
    if not agency_item:
        raise AssertionError(f"Agency workspace list missing created record: {agency_list}")
    assert_workspace_shape(agency_item, agency_view=True)

    agency_summary = get(f"/api/agencies/{agency_id}/operational-travel-workspaces/summary", OWNER_HEADERS)
    assert_summary_shape(agency_summary, agency_id=agency_id)
    if agency_summary.get("read_only") is not True:
        raise AssertionError(f"Agency workspace summary should be read-only: {agency_summary}")

    agency_detail = get(f"/api/agencies/{agency_id}/operational-travel-workspaces/{workspace_id}", OWNER_HEADERS)
    assert_disabled_response(agency_detail)
    if agency_detail.get("read_only") is not True:
        raise AssertionError(f"Agency workspace detail should be read-only: {agency_detail}")
    assert_workspace_shape(agency_detail.get("workspace") or {}, agency_view=True)

    deleted = request("DELETE", f"/api/platform/operational-travel-workspaces/{workspace_id}", {}, OWNER_HEADERS)[1]
    assert_disabled_response(deleted)
    if deleted.get("deleted") is not True or (deleted.get("workspace") or {}).get("workspace_status") != "archived":
        raise AssertionError(f"Workspace delete should be metadata-only archive: {deleted}")

    after_delete = get(f"/api/platform/operational-travel-workspaces?agency_id={agency_id}", OWNER_HEADERS)
    if any(item.get("id") == workspace_id for item in after_delete.get("items") or []):
        raise AssertionError(f"Default workspace list should exclude archived-delete metadata: {after_delete}")
    include_archived = get(f"/api/platform/operational-travel-workspaces?agency_id={agency_id}&include_archived=true", OWNER_HEADERS)
    if not any(item.get("id") == workspace_id for item in include_archived.get("items") or []):
        raise AssertionError(f"include_archived should expose metadata-archived workspace: {include_archived}")

    request("POST", f"/api/agencies/{agency_id}/operational-travel-workspaces", {"workspace_title": "blocked"}, OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/operational-travel-workspaces/{workspace_id}", {"workspace_status": "open"}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/operational-travel-workspaces/{workspace_id}", {}, OWNER_HEADERS, 405)


def assert_workspace_shape(workspace: dict, *, agency_view: bool = False) -> None:
    for key in [
        "id",
        "agency_id",
        "workspace_reference",
        "workspace_title",
        "workspace_type",
        "workspace_status",
        "primary_client_id",
        "primary_passenger_id",
        "linked_request_ids",
        "linked_trip_ids",
        "linked_offer_ids",
        "linked_booking_ids",
        "linked_ticket_ids",
        "linked_document_ids",
        "priority",
        "assigned_team",
        "assigned_agent",
        "travel_start_date",
        "travel_end_date",
        "origin_summary",
        "destination_summary",
        "service_summary",
        "operational_notes",
        "primary_client",
        "primary_passenger",
        "linked_requests",
        "linked_trips",
        "linked_offers",
        "linked_bookings",
        "linked_tickets",
        "linked_documents",
    ]:
        if key not in workspace:
            raise AssertionError(f"Workspace missing {key}: {workspace}")
    if workspace.get("metadata_only") is not True or workspace.get("operational_workspace_metadata_only") is not True:
        raise AssertionError(f"Workspace is not metadata-only: {workspace}")
    if agency_view and workspace.get("read_only") is not True:
        raise AssertionError(f"Agency workspace should be read-only: {workspace}")
    for flag in disabled_flags():
        if workspace.get(flag) is not True:
            raise AssertionError(f"Workspace missing disabled flag {flag}: {workspace}")
    if not workspace.get("linked_requests") or not workspace.get("linked_bookings") or not workspace.get("linked_documents"):
        raise AssertionError(f"Workspace linked metadata shape missing references: {workspace}")


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
        "linked_request_count",
        "linked_trip_count",
        "linked_offer_count",
        "linked_booking_count",
        "linked_ticket_count",
        "linked_document_count",
        "metadata_only",
    ]:
        if key not in summary:
            raise AssertionError(f"Workspace summary missing {key}: {payload}")
    if not WORKSPACE_STATUSES.issubset(set((summary.get("by_status") or {}).keys())):
        raise AssertionError(f"Workspace summary missing statuses: {payload}")
    if not WORKSPACE_TYPES.issubset(set((summary.get("by_type") or {}).keys())):
        raise AssertionError(f"Workspace summary missing types: {payload}")
    if not WORKSPACE_PRIORITIES.issubset(set((summary.get("by_priority") or {}).keys())):
        raise AssertionError(f"Workspace summary missing priorities: {payload}")


def main() -> int:
    verify_model_and_collection_registration()
    openapi = get("/openapi.json")
    verify_routes(openapi.get("paths") or {})
    verify_frontend_and_docs()
    verify_readiness()
    verify_endpoint_behavior()
    print("Phase 41.0 operational travel workspace foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
