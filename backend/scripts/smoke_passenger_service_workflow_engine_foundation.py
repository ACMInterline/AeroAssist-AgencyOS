#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import PassengerServiceWorkflow, PassengerServiceWorkflowCreate
from services.passenger_service_workflow_service import READINESS_STATES, WORKFLOW_STAGES
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_54_2_agent_work_queue_assignment_foundation"
ROOT = Path(__file__).resolve().parents[2]
EXPECTED_STAGES = {
    "passenger_registered",
    "requirements_collected",
    "service_requirements_analysed",
    "airline_evaluation",
    "offer_preparation",
    "offer_accepted",
    "booking_ready",
    "booking_completed",
    "ticket_ready",
    "ticket_completed",
    "emd_required",
    "emd_completed",
    "documents_pending",
    "documents_complete",
    "travel_ready",
    "travel_completed",
    "case_closed",
}
EXPECTED_READINESS = {
    "ready",
    "waiting_for_customer",
    "waiting_for_airline",
    "waiting_for_documents",
    "waiting_for_payment",
    "waiting_for_approval",
    "waiting_for_emd",
    "blocked",
    "completed",
}


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
        "automatic_workflow_execution_disabled",
        "ai_decision_making_disabled",
        "background_workers_disabled",
        "airline_apis_disabled",
        "gds_connectivity_disabled",
        "ndc_connectivity_disabled",
        "automatic_approvals_disabled",
        "automatic_ticketing_disabled",
        "automatic_emd_issuance_disabled",
        "automatic_messaging_disabled",
        "provider_integrations_disabled",
        "automation_disabled",
    ]


def forbidden_enabled_flags() -> list[str]:
    return [
        "automatic_workflow_execution_enabled",
        "ai_decision_making_enabled",
        "background_workers_enabled",
        "airline_apis_enabled",
        "gds_connectivity_enabled",
        "ndc_connectivity_enabled",
        "automatic_approvals_enabled",
        "automatic_ticketing_enabled",
        "automatic_emd_issuance_enabled",
        "automatic_messaging_enabled",
        "provider_integrations_enabled",
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


def workflow_payload(
    agency_id: str,
    reference: str = "PSW-SMOKE-001",
    *,
    current_stage: str = "documents_pending",
    readiness_status: str = "waiting_for_documents",
) -> dict:
    return {
        "agency_id": agency_id,
        "workflow_reference": reference,
        "workflow_status": "draft_metadata",
        "workflow_type": "ssr_osi_service_case",
        "workflow_version": "1.0",
        "passenger_workspace_id": "workflow-passenger-smoke",
        "travel_request_workspace_id": "workflow-request-smoke",
        "trip_workspace_id": "workflow-trip-smoke",
        "booking_workspace_id": "workflow-booking-smoke",
        "ticket_workspace_id": "workflow-ticket-smoke",
        "emd_workspace_id": "workflow-emd-smoke",
        "ssr_osi_workspace_id": "workflow-ssr-smoke",
        "document_workspace_id": "workflow-document-smoke",
        "timeline_workspace_id": "workflow-timeline-smoke",
        "current_stage": current_stage,
        "next_stage": "travel_ready",
        "previous_stage": "emd_completed",
        "readiness_status": readiness_status,
        "blocking_requirements": ["medical_certificate"],
        "completed_requirements": ["passenger_registered", "requirements_collected", "emd_completed"],
        "responsible_team": "Passenger services",
        "responsible_agent": "Workflow Agent",
        "related_airline": "LH",
        "workflow_priority": "high",
        "started_at": "2028-07-01T10:00:00Z",
        "last_updated": "2028-07-01T12:00:00Z",
        "recommendation_pack_reference": "aoie-pack-smoke",
        "operational_notes": "Metadata-only workflow coordination. No execution, AI decision, worker, airline API, GDS/NDC, approval automation, ticketing, EMD issuance, or messaging.",
        "metadata": {"smoke": True, "metadata_only": True},
    }


def verify_model_and_collection_registration() -> None:
    if set(WORKFLOW_STAGES) != EXPECTED_STAGES:
        raise AssertionError("Passenger service workflow stage definitions changed unexpectedly.")
    if set(READINESS_STATES) != EXPECTED_READINESS:
        raise AssertionError("Passenger service workflow readiness definitions changed unexpectedly.")

    create_payload = PassengerServiceWorkflowCreate(**workflow_payload("agency-smoke", "PSW-SMOKE-MODEL"))
    workflow = PassengerServiceWorkflow(**create_payload.model_dump(mode="json", exclude_none=True))
    if workflow.current_stage != "documents_pending" or workflow.readiness_status != "waiting_for_documents":
        raise AssertionError("Passenger service workflow model did not preserve stage/readiness metadata.")
    if workflow.ticket_workspace_id != "workflow-ticket-smoke" or workflow.timeline_workspace_id != "workflow-timeline-smoke":
        raise AssertionError("Passenger service workflow relationship fields were not preserved.")
    if workflow.metadata_only is not True or workflow.automatic_workflow_execution_disabled is not True:
        raise AssertionError("Passenger service workflow model is not metadata-only.")
    if "passenger_service_workflows" not in AGENCY_OWNED_COLLECTIONS:
        raise AssertionError("Passenger service workflows collection is not registered as agency-owned metadata.")

    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for index_name in [
        "passenger_service_workflows_id_unique",
        "passenger_service_workflows_reference_unique",
        "passenger_service_workflows_agency_stage_lookup",
        "passenger_service_workflows_agency_readiness_lookup",
        "passenger_service_workflows_agency_status_lookup",
        "passenger_service_workflows_agency_priority_lookup",
        "passenger_service_workflows_agency_airline_lookup",
        "passenger_service_workflows_agency_agent_lookup",
        "passenger_service_workflows_passenger_workspace_lookup",
        "passenger_service_workflows_travel_request_workspace_lookup",
        "passenger_service_workflows_trip_workspace_lookup",
        "passenger_service_workflows_booking_workspace_lookup",
        "passenger_service_workflows_ticket_workspace_lookup",
        "passenger_service_workflows_emd_workspace_lookup",
        "passenger_service_workflows_ssr_osi_workspace_lookup",
        "passenger_service_workflows_document_workspace_lookup",
        "passenger_service_workflows_timeline_workspace_lookup",
        "passenger_service_workflows_recommendation_pack_lookup",
    ]:
        if index_name not in database_py:
            raise AssertionError(f"Passenger service workflow index missing: {index_name}")


def verify_routes(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
    expected_methods = {
        "/api/platform/passenger-service-workflows": {"get", "post"},
        "/api/platform/passenger-service-workflows/summary": {"get"},
        "/api/platform/passenger-service-workflows/{workflow_id}": {"get", "put", "delete"},
        "/api/agencies/{agency_id}/passenger-service-workflows": {"get"},
        "/api/agencies/{agency_id}/passenger-service-workflows/summary": {"get"},
        "/api/agencies/{agency_id}/passenger-service-workflows/{workflow_id}": {"get"},
    }
    for path, methods in expected_methods.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
    for path in [
        "/api/agencies/{agency_id}/passenger-service-workflows",
        "/api/agencies/{agency_id}/passenger-service-workflows/summary",
        "/api/agencies/{agency_id}/passenger-service-workflows/{workflow_id}",
    ]:
        blocked_methods = set(paths.get(path, {}).keys()) & {"post", "put", "patch", "delete"}
        if blocked_methods:
            raise AssertionError(f"Agency passenger service workflow route is not read-only: {path} {sorted(blocked_methods)}")


def verify_frontend_and_docs() -> None:
    for path, text in [
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Passenger Service Workflows"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Workflow Engine"),
        (ROOT / "frontend/src/App.jsx", "/platform/passenger-service-workflows"),
        (ROOT / "frontend/src/App.jsx", "/agency/workflow-engine"),
        (ROOT / "frontend/src/pages/platform/PassengerServiceWorkflowsPage.jsx", "Passenger Service Workflows"),
        (ROOT / "frontend/src/pages/platform/PassengerServiceWorkflowsPage.jsx", "No automation"),
        (ROOT / "frontend/src/pages/platform/PassengerServiceWorkflowsPage.jsx", "No AI decisions"),
        (ROOT / "frontend/src/pages/agency/WorkflowEnginePage.jsx", "Workflow Engine"),
        (ROOT / "frontend/src/pages/agency/WorkflowEnginePage.jsx", "Read-only passenger service workflow metadata"),
        (ROOT / "docs/architecture/passenger-service-workflow-engine-foundation.md", "Passenger Service Workflow Engine Foundation"),
        (ROOT / "docs/architecture/passenger-service-workflow-engine-foundation.md", "Passenger -> Service Requirement -> Operational Workspaces -> Timeline -> Future AOIE -> Operational Execution"),
        (ROOT / "README.md", "Phase 42.2 Includes"),
        (ROOT / "BUILD_PHASES.md", "Phase 42.2: Passenger Service Workflow Engine Foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "passenger_service_workflows"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/api/platform/passenger-service-workflows"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Passenger service workflows"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Passenger service workflows"),
        (ROOT / "docs/architecture/passenger-service-operations-principle.md", "Phase 42.2 adds the Passenger Service Workflow Engine"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "frontend/src/pages/platform/PassengerServiceWorkflowsPage.jsx",
        ROOT / "frontend/src/pages/agency/WorkflowEnginePage.jsx",
        ROOT / "frontend/src/App.jsx",
    ]:
        for text in ['"/admin', '"/agent', '"/api/admin', '"/api/agent']:
            reject_text(path, text)
    for path in [
        ROOT / "frontend/src/pages/platform/PassengerServiceWorkflowsPage.jsx",
        ROOT / "frontend/src/pages/agency/WorkflowEnginePage.jsx",
    ]:
        reject_text(path, "<button")
        reject_text(path, "apiPost")
        reject_text(path, "apiPut")


def verify_blueprint_adoption() -> None:
    adoption = get("/api/platform/blueprint/adoption-map", OWNER_HEADERS)
    categories = {item.get("category") for item in adoption.get("items") or []}
    if "Passenger Service Workflows" not in categories:
        raise AssertionError(f"Blueprint adoption map missing Passenger Service Workflows category: {categories}")
    gaps = get("/api/platform/blueprint/gaps", OWNER_HEADERS)
    if not any("Passenger service workflow engine foundation built in Phase 42.2" in item for item in gaps.get("already_built", [])):
        raise AssertionError(f"Blueprint gaps missing Passenger Service Workflow foundation marker: {gaps}")
    if "Phase 42.2" not in gaps.get("next_operational_phase", ""):
        raise AssertionError(f"Blueprint gaps missing Phase 42.2 operational marker: {gaps}")
    chapter_41 = gaps.get("chapter_41_operational_workspaces") or []
    if "Passenger service workflows" not in chapter_41:
        raise AssertionError(f"Chapter 41/42 operational map missing Passenger service workflows: {gaps}")
    next_phases = get("/api/platform/blueprint/next-phases", OWNER_HEADERS)
    if not any(item.get("phase") == "Phase 42.2" for item in next_phases.get("items", [])):
        raise AssertionError(f"Next recommendations missing Phase 42.2: {next_phases}")


def verify_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")
    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("passenger_service_workflow_engine_foundation") or {}
    for flag in [
        "passenger_service_workflows_enabled",
        "workflow_engine_metadata_enabled",
        "platform_passenger_service_workflow_metadata_crud_enabled",
        "agency_passenger_service_workflow_read_only_enabled",
        "platform_passenger_service_workflows_ui_enabled",
        "agency_workflow_engine_ui_enabled",
        "workflow_stage_definitions_enabled",
        "workflow_readiness_state_definitions_enabled",
        "filter_by_workflow_stage_enabled",
        "filter_by_readiness_enabled",
        "filter_by_passenger_enabled",
        "filter_by_airline_enabled",
        "filter_by_priority_enabled",
        "filter_by_assigned_agent_enabled",
        "passenger_workspace_link_enabled",
        "travel_request_workspace_link_enabled",
        "trip_workspace_link_enabled",
        "booking_workspace_link_enabled",
        "ticket_workspace_link_enabled",
        "emd_workspace_link_enabled",
        "ssr_osi_workspace_link_enabled",
        "document_workspace_link_enabled",
        "timeline_workspace_link_enabled",
        "future_aoie_reference_metadata_enabled",
        "blocking_requirements_metadata_enabled",
        "completed_requirements_metadata_enabled",
        "responsible_team_metadata_enabled",
        "responsible_agent_metadata_enabled",
        "metadata_only",
        "workflow_engine_metadata_only",
    ]:
        require_flag(section, flag)
    for flag in disabled_flags():
        require_flag(section, flag)
    require_flag(section, "readiness_required", False)
    for count_key in [
        "passenger_service_workflow_count",
        "passenger_service_workflow_stage_counts",
        "passenger_service_workflow_readiness_counts",
        "passenger_service_workflow_status_count",
        "passenger_service_workflow_type_count",
        "passenger_service_workflow_priority_count",
        "passenger_service_workflow_airline_count",
        "passenger_service_workflow_assigned_agent_count",
        "passenger_service_workflow_passenger_workspace_count",
        "passenger_service_workflow_travel_request_workspace_count",
        "passenger_service_workflow_trip_workspace_count",
        "passenger_service_workflow_booking_workspace_count",
        "passenger_service_workflow_ticket_workspace_count",
        "passenger_service_workflow_emd_workspace_count",
        "passenger_service_workflow_ssr_osi_workspace_count",
        "passenger_service_workflow_document_workspace_count",
        "passenger_service_workflow_timeline_workspace_count",
        "passenger_service_workflow_blocking_requirement_count",
        "passenger_service_workflow_completed_requirement_count",
        "passenger_service_workflow_recommendation_pack_count",
    ]:
        if count_key not in section:
            raise AssertionError(f"Passenger service workflow readiness missing count: {count_key}")
    if not EXPECTED_STAGES.issubset(set((section.get("passenger_service_workflow_stage_counts") or {}).keys())):
        raise AssertionError(f"Passenger service workflow readiness missing stages: {section}")
    if not EXPECTED_READINESS.issubset(set((section.get("passenger_service_workflow_readiness_counts") or {}).keys())):
        raise AssertionError(f"Passenger service workflow readiness missing readiness states: {section}")
    previous_section = readiness.get("operational_timeline_workspace_foundation") or {}
    if previous_section.get("metadata_only") is not True:
        raise AssertionError("Operational timeline workspace section should remain metadata-only.")


def verify_no_forbidden_implementation() -> None:
    checked_files = [
        ROOT / "backend/services/passenger_service_workflow_service.py",
        ROOT / "backend/routers/platform_passenger_service_workflows.py",
        ROOT / "backend/routers/agency_passenger_service_workflows.py",
        ROOT / "frontend/src/pages/platform/PassengerServiceWorkflowsPage.jsx",
        ROOT / "frontend/src/pages/agency/WorkflowEnginePage.jsx",
    ]
    forbidden_terms = [
        "BackgroundTasks",
        "execute_workflow",
        "run_workflow",
        "send_email",
        "send_sms",
        "issue_ticket",
        "issue_emd",
        "gds_client",
        "ndc_client",
        "airline_api_client",
        "approve_service",
        "openai",
        "requests.post",
        "httpx.",
        "schedule_job",
        "celery",
    ]
    for path in checked_files:
        content = path.read_text(encoding="utf-8").lower()
        for term in forbidden_terms:
            if term.lower() in content:
                raise AssertionError(f"{path.relative_to(ROOT)} contains forbidden implementation term: {term}")


def verify_endpoint_behavior() -> None:
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires seeded demo agency.")
    agency_id = agencies[0]["id"]

    created = post("/api/platform/passenger-service-workflows", workflow_payload(agency_id), OWNER_HEADERS, 201)
    assert_disabled_response(created)
    workflow = created.get("passenger_service_workflow") or {}
    assert_workflow_shape(workflow)
    workflow_id = workflow.get("id")
    if not workflow_id:
        raise AssertionError(f"Passenger service workflow id missing: {created}")

    updated = put(
        f"/api/platform/passenger-service-workflows/{workflow_id}",
        {
            "current_stage": "documents_complete",
            "previous_stage": "documents_pending",
            "next_stage": "travel_ready",
            "readiness_status": "ready",
            "blocking_requirements": [],
            "completed_requirements": ["passenger_registered", "requirements_collected", "emd_completed", "documents_complete"],
            "operational_notes": "Updated metadata only; no workflow execution.",
            "metadata": {"updated": True, "metadata_only": True},
        },
        OWNER_HEADERS,
    )
    assert_disabled_response(updated)
    updated_workflow = updated.get("passenger_service_workflow") or {}
    assert_workflow_shape(updated_workflow)
    if updated_workflow.get("current_stage") != "documents_complete" or updated_workflow.get("readiness_status") != "ready":
        raise AssertionError(f"Passenger service workflow update did not persist metadata: {updated}")

    for filter_query in [
        f"agency_id={agency_id}",
        "stage=documents_complete",
        "readiness=ready",
        "passenger=workflow-passenger-smoke",
        "airline=LH",
        "priority=high",
        "assigned_agent=Workflow%20Agent",
    ]:
        filtered = get(f"/api/platform/passenger-service-workflows?{filter_query}", OWNER_HEADERS)
        assert_disabled_response(filtered)
        if not any(item.get("id") == workflow_id for item in filtered.get("items") or []):
            raise AssertionError(f"Passenger service workflow filter {filter_query} missing created record: {filtered}")

    platform_summary = get("/api/platform/passenger-service-workflows/summary", OWNER_HEADERS)
    assert_summary_shape(platform_summary)

    platform_detail = get(f"/api/platform/passenger-service-workflows/{workflow_id}", OWNER_HEADERS)
    assert_disabled_response(platform_detail)
    assert_workflow_shape(platform_detail.get("passenger_service_workflow") or {})

    agency_list = get(
        f"/api/agencies/{agency_id}/passenger-service-workflows?stage=documents_complete&readiness=ready&passenger=workflow-passenger-smoke&airline=LH&priority=high&assigned_agent=Workflow%20Agent",
        OWNER_HEADERS,
    )
    assert_disabled_response(agency_list)
    if agency_list.get("read_only") is not True:
        raise AssertionError(f"Agency passenger service workflow list should be read-only: {agency_list}")
    agency_item = next((item for item in agency_list.get("items") or [] if item.get("id") == workflow_id), None)
    if not agency_item:
        raise AssertionError(f"Agency passenger service workflow list missing created record: {agency_list}")
    assert_workflow_shape(agency_item, agency_view=True)

    agency_summary = get(f"/api/agencies/{agency_id}/passenger-service-workflows/summary", OWNER_HEADERS)
    assert_summary_shape(agency_summary, agency_id=agency_id)
    if agency_summary.get("read_only") is not True:
        raise AssertionError(f"Agency passenger service workflow summary should be read-only: {agency_summary}")

    agency_detail = get(f"/api/agencies/{agency_id}/passenger-service-workflows/{workflow_id}", OWNER_HEADERS)
    assert_disabled_response(agency_detail)
    if agency_detail.get("read_only") is not True:
        raise AssertionError(f"Agency passenger service workflow detail should be read-only: {agency_detail}")
    assert_workflow_shape(agency_detail.get("passenger_service_workflow") or {}, agency_view=True)

    deleted = request("DELETE", f"/api/platform/passenger-service-workflows/{workflow_id}", {}, OWNER_HEADERS)[1]
    assert_disabled_response(deleted)
    if deleted.get("archived") is not True or (deleted.get("passenger_service_workflow") or {}).get("workflow_status") != "archived":
        raise AssertionError(f"Passenger service workflow delete should be metadata-only archive: {deleted}")

    after_delete = get(f"/api/platform/passenger-service-workflows?agency_id={agency_id}&passenger=workflow-passenger-smoke", OWNER_HEADERS)
    if any(item.get("id") == workflow_id for item in after_delete.get("items") or []):
        raise AssertionError(f"Default workflow list should exclude archived metadata: {after_delete}")
    include_archived = get(
        f"/api/platform/passenger-service-workflows?agency_id={agency_id}&passenger=workflow-passenger-smoke&include_archived=true",
        OWNER_HEADERS,
    )
    if not any(item.get("id") == workflow_id for item in include_archived.get("items") or []):
        raise AssertionError(f"include_archived should expose archived passenger service workflow: {include_archived}")

    request("POST", f"/api/agencies/{agency_id}/passenger-service-workflows", {"current_stage": "travel_ready"}, OWNER_HEADERS, 405)
    request("PUT", f"/api/agencies/{agency_id}/passenger-service-workflows/{workflow_id}", {"readiness_status": "ready"}, OWNER_HEADERS, 405)
    request("DELETE", f"/api/agencies/{agency_id}/passenger-service-workflows/{workflow_id}", {}, OWNER_HEADERS, 405)


def assert_workflow_shape(workflow: dict, *, agency_view: bool = False) -> None:
    for key in [
        "id",
        "agency_id",
        "workflow_reference",
        "workflow_status",
        "workflow_type",
        "workflow_version",
        "passenger_workspace_id",
        "travel_request_workspace_id",
        "trip_workspace_id",
        "booking_workspace_id",
        "ticket_workspace_id",
        "emd_workspace_id",
        "ssr_osi_workspace_id",
        "document_workspace_id",
        "timeline_workspace_id",
        "current_stage",
        "next_stage",
        "previous_stage",
        "readiness_status",
        "blocking_requirements",
        "completed_requirements",
        "responsible_team",
        "responsible_agent",
        "related_airline",
        "workflow_priority",
        "started_at",
        "last_updated",
        "recommendation_pack_reference",
        "operational_notes",
        "workflow_display_name",
        "metadata_only",
        "workflow_engine_metadata_only",
    ]:
        if key not in workflow:
            raise AssertionError(f"Passenger service workflow missing {key}: {workflow}")
    if workflow.get("ticket_workspace_id") != "workflow-ticket-smoke":
        raise AssertionError(f"Ticket workspace link missing: {workflow}")
    if workflow.get("emd_workspace_id") != "workflow-emd-smoke":
        raise AssertionError(f"EMD workspace link missing: {workflow}")
    if workflow.get("ssr_osi_workspace_id") != "workflow-ssr-smoke":
        raise AssertionError(f"SSR / OSI workspace link missing: {workflow}")
    if workflow.get("document_workspace_id") != "workflow-document-smoke":
        raise AssertionError(f"Document workspace link missing: {workflow}")
    if workflow.get("timeline_workspace_id") != "workflow-timeline-smoke":
        raise AssertionError(f"Timeline workspace link missing: {workflow}")
    if workflow.get("recommendation_pack_reference") != "aoie-pack-smoke":
        raise AssertionError(f"AOIE recommendation-pack reference missing: {workflow}")
    if agency_view and workflow.get("read_only") is not True:
        raise AssertionError(f"Agency workflow item should be read-only: {workflow}")
    for flag in disabled_flags():
        if workflow.get(flag) is not True:
            raise AssertionError(f"Passenger service workflow missing disabled flag {flag}: {workflow}")
    if workflow.get("metadata_only") is not True:
        raise AssertionError(f"Passenger service workflow should be metadata-only: {workflow}")


def assert_summary_shape(payload: dict, *, agency_id: str | None = None) -> None:
    assert_disabled_response(payload)
    if agency_id and payload.get("agency_id") != agency_id:
        raise AssertionError(f"Agency summary has wrong agency id: {payload}")
    summary = payload.get("summary") or {}
    for key in [
        "total_count",
        "by_stage",
        "by_readiness",
        "by_status",
        "by_type",
        "by_priority",
        "ticket_workspace_count",
        "emd_workspace_count",
        "ssr_osi_workspace_count",
        "document_workspace_count",
        "timeline_workspace_count",
        "blocking_requirement_count",
        "completed_requirement_count",
        "recommendation_pack_count",
    ]:
        if key not in summary:
            raise AssertionError(f"Passenger service workflow summary missing {key}: {payload}")
    if not EXPECTED_STAGES.issubset(set((summary.get("by_stage") or {}).keys())):
        raise AssertionError(f"Passenger service workflow summary missing stages: {payload}")
    if not EXPECTED_READINESS.issubset(set((summary.get("by_readiness") or {}).keys())):
        raise AssertionError(f"Passenger service workflow summary missing readiness states: {payload}")


def main() -> int:
    verify_model_and_collection_registration()
    openapi = get("/openapi.json")
    verify_routes(openapi.get("paths", {}))
    verify_no_forbidden_implementation()
    verify_frontend_and_docs()
    verify_readiness()
    verify_blueprint_adoption()
    verify_endpoint_behavior()
    print("Phase 42.2 passenger service workflow engine foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
