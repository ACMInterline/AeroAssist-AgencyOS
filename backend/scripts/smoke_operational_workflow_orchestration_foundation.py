#!/usr/bin/env python3
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import (
    OperationalWorkflowDefinition,
    OperationalWorkflowDefinitionCreate,
    OperationalWorkflowEvent,
    OperationalWorkflowGuard,
    OperationalWorkflowGuardCreate,
    OperationalWorkflowInstance,
    OperationalWorkflowTransition,
)
from services.operational_workflow_orchestration_service import (
    BOOKING_READINESS_STATES,
    DEFAULT_WORKFLOW_DEFINITIONS,
    GUARD_RESULTS,
    GUARD_TYPES,
    OPERATIONAL_WORKFLOW_DEFINITIONS_COLLECTION,
    OPERATIONAL_WORKFLOW_EVENTS_COLLECTION,
    OPERATIONAL_WORKFLOW_GUARDS_COLLECTION,
    OPERATIONAL_WORKFLOW_INSTANCES_COLLECTION,
    OPERATIONAL_WORKFLOW_TRANSITIONS_COLLECTION,
    PHASE_LABEL,
    REQUEST_LIFECYCLE_STATES,
    SERVICE_FULFILLMENT_STATES,
    TRANSITION_STATUSES,
    TRIP_LIFECYCLE_STATES,
    WORKFLOW_STATUSES,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request


EXPECTED_PHASE = "phase_54_7_servicing_after_sales_workflow_foundation"
ROOT = Path(__file__).resolve().parents[2]
AGENCY_AGENT_HEADERS = {"X-Demo-User-Email": "agency.agent@aeroassist.dev"}


def run_ref(prefix: str) -> str:
    return f"{prefix}-{int(time.time() * 1000)}"


def require_text(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8")
    if text not in content:
        raise AssertionError(f"{path.relative_to(ROOT)} missing expected text: {text}")


def assert_safety_flags(payload: dict) -> None:
    for flag in [
        "metadata_only",
        "operational_workflow_orchestration_foundation",
        "entity_status_sync_disabled_by_default",
        "unrestricted_dynamic_mutation_disabled",
        "existing_workspace_services_preserved",
        "provider_integrations_disabled",
        "external_api_calls_disabled",
        "ai_disabled",
        "background_workers_disabled",
        "automatic_execution_disabled",
        "automation_disabled",
        "human_authority_final",
    ]:
        if payload.get(flag) is not True:
            raise AssertionError(f"Payload missing safety flag {flag}: {payload}")


def definition_payload(reference: str) -> dict:
    return {
        "workflow_code": reference,
        "name": "Phase 54.1 Workflow Smoke",
        "description": "Metadata-only orchestration smoke definition.",
        "entity_type": "request",
        "version": "1.0",
        "status": "draft",
        "initial_state": "submitted",
        "terminal_states": ["planning"],
        "state_definitions_json": {
            "submitted": {"label": "Submitted"},
            "triage": {"label": "Triage"},
            "information_required": {"label": "Information Required"},
            "planning": {"label": "Planning", "terminal": True},
        },
        "transition_definitions_json": [
            {
                "transition_code": "submitted_to_triage",
                "from_state": "submitted",
                "to_state": "triage",
                "label": "Submitted to triage",
                "metadata_only": True,
            },
            {
                "transition_code": "triage_to_planning",
                "from_state": "triage",
                "to_state": "planning",
                "label": "Triage to planning",
                "metadata_only": True,
            },
            {
                "transition_code": "triage_to_information_required",
                "from_state": "triage",
                "to_state": "information_required",
                "label": "Triage to information required",
                "metadata_only": True,
            },
        ],
        "required_modules_json": ["travel_request_workspaces", "operational_timelines", "passenger_service_workflows"],
        "metadata": {"smoke": True},
    }


def guard_payload(definition_id: str, guard_code: str, transition_code: str, guard_type: str, condition: dict, severity: str = "warning") -> dict:
    return {
        "workflow_definition_id": definition_id,
        "guard_code": guard_code,
        "transition_code": transition_code,
        "guard_type": guard_type,
        "severity": severity,
        "evaluation_mode": "metadata",
        "condition_json": condition,
        "failure_message_internal": f"{guard_code} requires human review.",
        "failure_message_client": f"{guard_code} needs review.",
        "remediation_guidance": "Review the linked operational workspace before continuing.",
        "is_active": True,
        "metadata": {"smoke": True},
    }


def verify_models_and_registration() -> None:
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Service phase label mismatch: {PHASE_LABEL}")
    for collection in [
        OPERATIONAL_WORKFLOW_DEFINITIONS_COLLECTION,
        OPERATIONAL_WORKFLOW_INSTANCES_COLLECTION,
        OPERATIONAL_WORKFLOW_TRANSITIONS_COLLECTION,
        OPERATIONAL_WORKFLOW_GUARDS_COLLECTION,
        OPERATIONAL_WORKFLOW_EVENTS_COLLECTION,
    ]:
        if collection not in AGENCY_OWNED_COLLECTIONS:
            raise AssertionError(f"{collection} is not registered as agency-owned metadata.")
    for value in ["passed", "warning", "blocked", "manual_review", "unknown"]:
        if value not in GUARD_RESULTS:
            raise AssertionError(f"Missing guard result: {value}")
    for value in ["completed", "blocked", "warning_acknowledgement_required", "manual_review_required"]:
        if value not in TRANSITION_STATUSES:
            raise AssertionError(f"Missing transition status: {value}")
    for value in ["active", "completed", "suspended", "archived"]:
        if value not in WORKFLOW_STATUSES:
            raise AssertionError(f"Missing workflow status: {value}")
    for value in [
        "required_client_passenger_linkage",
        "segment_precision",
        "accepted_offer",
        "policy_evaluation",
        "required_documents",
        "unresolved_operational_blockers",
    ]:
        if value not in GUARD_TYPES:
            raise AssertionError(f"Missing guard type: {value}")
    if "submitted" not in REQUEST_LIFECYCLE_STATES or "booked" not in BOOKING_READINESS_STATES:
        raise AssertionError("Default request or booking states are incomplete.")
    if "servicing" not in TRIP_LIFECYCLE_STATES or "fulfilled" not in SERVICE_FULFILLMENT_STATES:
        raise AssertionError("Default trip or service states are incomplete.")
    if len(DEFAULT_WORKFLOW_DEFINITIONS) < 4:
        raise AssertionError("Expected default workflow definitions for request, trip, booking, and service.")

    created_definition = OperationalWorkflowDefinitionCreate(**definition_payload("workflow-model-smoke"))
    definition = OperationalWorkflowDefinition(**created_definition.model_dump(mode="json", exclude_none=True))
    guard = OperationalWorkflowGuard(**guard_payload(definition.id, "model_guard", "submitted_to_triage", "segment_precision", {"missing_status": "warning"}))
    instance = OperationalWorkflowInstance(agency_id="agency-smoke", workflow_definition_id=definition.id, entity_type="request", entity_id="request-smoke", current_state="submitted")
    transition = OperationalWorkflowTransition(agency_id="agency-smoke", workflow_instance_id=instance.id, transition_code="submitted_to_triage", from_state="submitted", to_state="triage")
    event = OperationalWorkflowEvent(agency_id="agency-smoke", workflow_instance_id=instance.id, event_type="workflow_started", event_code="workflow_started")
    for record in [definition, guard, instance, transition, event]:
        dumped = record.model_dump(mode="json")
        if dumped.get("metadata_only") is not True or dumped.get("operational_workflow_orchestration_foundation") is not True:
            raise AssertionError(f"Operational workflow model lost metadata-only flags: {dumped}")

    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for marker in [
        "operational_workflow_definitions_code_version_unique",
        "operational_workflow_instances_agency_entity_lookup",
        "operational_workflow_transitions_instance_history_lookup",
        "operational_workflow_guards_definition_transition_lookup",
        "operational_workflow_events_instance_history_lookup",
    ]:
        if marker not in database_py:
            raise AssertionError(f"Database index registration missing {marker}.")


def verify_router_ui_docs_registration() -> None:
    openapi = get("/openapi.json", OWNER_HEADERS)
    paths = openapi.get("paths") or {}
    for path, method in [
        ("/api/platform/operational-workflows", "get"),
        ("/api/platform/operational-workflows/summary", "get"),
        ("/api/platform/operational-workflows/diagnostics", "get"),
        ("/api/platform/operational-workflows/state-transition-maps", "get"),
        ("/api/platform/operational-workflows/definitions", "get"),
        ("/api/platform/operational-workflows/definitions", "post"),
        ("/api/platform/operational-workflows/definitions/{definition_id}", "get"),
        ("/api/platform/operational-workflows/definitions/{definition_id}", "put"),
        ("/api/platform/operational-workflows/definitions/{definition_id}/versions", "post"),
        ("/api/platform/operational-workflows/guards", "get"),
        ("/api/platform/operational-workflows/guards", "post"),
        ("/api/platform/operational-workflows/guards/{guard_id}", "put"),
        ("/api/platform/operational-workflows/instances", "get"),
        ("/api/platform/operational-workflows/instances/start", "post"),
        ("/api/platform/operational-workflows/instances/{instance_id}", "get"),
        ("/api/platform/operational-workflows/instances/{instance_id}/available-transitions", "get"),
        ("/api/platform/operational-workflows/instances/{instance_id}/execute-transition", "post"),
        ("/api/platform/operational-workflows/instances/{instance_id}/acknowledge-warning", "post"),
        ("/api/platform/operational-workflows/instances/{instance_id}/transitions", "get"),
        ("/api/platform/operational-workflows/instances/{instance_id}/events", "get"),
        ("/api/platform/operational-workflows/entities/{entity_type}/{entity_id}/summary", "get"),
        ("/api/agencies/{agency_id}/operational-workflows", "get"),
        ("/api/agencies/{agency_id}/operational-workflows/summary", "get"),
        ("/api/agencies/{agency_id}/operational-workflows/instances/start", "post"),
        ("/api/agencies/{agency_id}/operational-workflows/instances/{instance_id}", "get"),
        ("/api/agencies/{agency_id}/operational-workflows/instances/{instance_id}/available-transitions", "get"),
        ("/api/agencies/{agency_id}/operational-workflows/instances/{instance_id}/execute-transition", "post"),
        ("/api/agencies/{agency_id}/operational-workflows/instances/{instance_id}/acknowledge-warning", "post"),
        ("/api/agencies/{agency_id}/operational-workflows/instances/{instance_id}/transitions", "get"),
        ("/api/agencies/{agency_id}/operational-workflows/instances/{instance_id}/events", "get"),
        ("/api/agencies/{agency_id}/operational-workflows/instances/{instance_id}/blockers", "get"),
        ("/api/agencies/{agency_id}/operational-workflows/instances/{instance_id}/warnings", "get"),
        ("/api/agencies/{agency_id}/operational-workflows/entities/{entity_type}/{entity_id}/summary", "get"),
    ]:
        assert_openapi_path(paths, path, method)
    for path in paths:
        lowered = path.lower()
        if lowered.startswith(("/api/admin", "/api/agent", "/admin", "/agent")):
            raise AssertionError(f"Non-canonical route introduced: {path}")
        if "operational-workflows" in lowered:
            for marker in ["/execute-provider", "/send", "/ai", "/scheduler", "/worker", "/book", "/ticket", "/issue-emd"]:
                if marker in lowered:
                    raise AssertionError(f"Forbidden workflow execution route registered: {path}")

    for path, text in [
        (ROOT / "frontend/src/App.jsx", "/platform/operational-workflows"),
        (ROOT / "frontend/src/App.jsx", "/agency/operational-workflows"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Operational Workflows"),
        (ROOT / "frontend/src/pages/platform/OperationalWorkflowsPage.jsx", "Workflow Definitions"),
        (ROOT / "frontend/src/pages/agency/OperationalWorkflowsPage.jsx", "Available next actions"),
        (ROOT / "frontend/src/pages/agency/TravelRequestsPage.jsx", "/agency/operational-workflows"),
        (ROOT / "frontend/src/pages/agency/TripWorkspacesPage.jsx", "/agency/operational-workflows"),
        (ROOT / "frontend/src/pages/agency/OfferWorkspaceMetadataPage.jsx", "/agency/operational-workflows"),
        (ROOT / "frontend/src/pages/agency/BookingWorkspaceMetadataPage.jsx", "/agency/operational-workflows"),
        (ROOT / "frontend/src/pages/agency/WorkflowEnginePage.jsx", "/agency/operational-workflows"),
        (ROOT / "frontend/src/pages/agency/TimelinePage.jsx", "/agency/operational-workflows"),
        (ROOT / "backend/services/saas_subscription_service.py", "operational_workflows"),
        (ROOT / "backend/services/blueprint_adoption_service.py", "Operational Workflow Orchestration"),
        (ROOT / "docs/architecture/operational-workflow-orchestration-foundation.md", "Phase 54.1"),
        (ROOT / "docs/architecture/current-model-inventory.md", "operational_workflow_definitions"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/api/platform/operational-workflows"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Operational Workflow Orchestration"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Operational workflow orchestration"),
        (ROOT / "docs/architecture/passenger-service-operations-principle.md", "Operational Workflow Orchestration"),
        (ROOT / "docs/architecture/foundations/GLOSSARY.md", "Operational Workflow Orchestration"),
        (ROOT / "BUILD_PHASES.md", "Implemented Phase 54.1"),
        (ROOT / "README.md", "Operational Workflow Orchestration Foundation"),
    ]:
        require_text(path, text)


def find_transition(transitions: list[dict], code: str) -> dict:
    for transition in transitions:
        if transition.get("transition_code") == code:
            return transition
    raise AssertionError(f"Transition {code} was not returned: {transitions}")


def verify_workflow_endpoints() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")
    readiness = get("/api/readiness")
    section = readiness.get("operational_workflow_orchestration_foundation") or {}
    for key in [
        "operational_workflow_orchestration_enabled",
        "metadata_only",
        "entity_status_sync_disabled_by_default",
        "unrestricted_dynamic_mutation_disabled",
        "platform_operational_workflow_definition_metadata_crud_enabled",
        "platform_operational_workflow_guard_metadata_crud_enabled",
        "agency_operational_workflow_instance_metadata_enabled",
        "agency_operational_workflow_transition_metadata_enabled",
        "provider_integrations_disabled",
        "external_api_calls_disabled",
        "ai_disabled",
        "background_workers_disabled",
        "automatic_execution_disabled",
        "automation_disabled",
    ]:
        if section.get(key) is not True:
            raise AssertionError(f"Readiness section missing {key}: {section}")

    post("/api/reference/seed", {}, OWNER_HEADERS)
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires at least one seeded agency.")
    agency_id = agencies[0]["id"]
    other_agency_id = agencies[1]["id"] if len(agencies) > 1 else None

    request("GET", "/api/platform/operational-workflows", None, AGENCY_AGENT_HEADERS, expect=403)

    dashboard = get("/api/platform/operational-workflows", OWNER_HEADERS)
    assert_safety_flags(dashboard)
    if "definitions" not in dashboard or "summary" not in dashboard:
        raise AssertionError("Platform workflow dashboard missing definitions or summary.")
    diagnostics = get("/api/platform/operational-workflows/diagnostics", OWNER_HEADERS)
    assert_safety_flags(diagnostics)
    if diagnostics.get("adapters", {}).get("booking", {}).get("status_sync_enabled") is not False:
        raise AssertionError("Explicit adapters must keep entity status sync disabled by default.")
    maps = get("/api/platform/operational-workflows/state-transition-maps", OWNER_HEADERS)
    if "request_lifecycle_default" not in maps.get("state_transition_maps", {}):
        raise AssertionError("Default request lifecycle map was not exposed.")

    workflow_code = run_ref("workflow_smoke").lower()
    created = post("/api/platform/operational-workflows/definitions", definition_payload(workflow_code), OWNER_HEADERS, 201)
    assert_safety_flags(created)
    definition = created["workflow_definition"]
    definition_id = definition["id"]
    if definition.get("state_count") != 4 or definition.get("transition_count") != 3:
        raise AssertionError(f"Definition projection missing state/transition counts: {definition}")

    updated = put(
        f"/api/platform/operational-workflows/definitions/{definition_id}",
        {"status": "active", "description": "Updated metadata-only orchestration smoke definition."},
        OWNER_HEADERS,
    )
    if updated["workflow_definition"].get("status") != "active":
        raise AssertionError("Definition status update did not persist.")
    versioned = post(
        f"/api/platform/operational-workflows/definitions/{definition_id}/versions",
        {"version": "1.1", "status": "draft", "name": "Phase 54.1 Workflow Smoke v1.1"},
        OWNER_HEADERS,
        201,
    )
    if versioned.get("version_created") is not True or versioned["workflow_definition"].get("version") != "1.1":
        raise AssertionError(f"Definition versioning failed: {versioned}")

    warning_guard = post(
        "/api/platform/operational-workflows/guards",
        guard_payload(definition_id, f"{workflow_code}_segment_warning", "submitted_to_triage", "segment_precision", {"missing_status": "warning"}),
        OWNER_HEADERS,
        201,
    )["workflow_guard"]
    blocked_guard = post(
        "/api/platform/operational-workflows/guards",
        guard_payload(definition_id, f"{workflow_code}_accepted_offer", "triage_to_planning", "accepted_offer", {}, "blocker"),
        OWNER_HEADERS,
        201,
    )["workflow_guard"]
    unknown_guard = post(
        "/api/platform/operational-workflows/guards",
        guard_payload(definition_id, f"{workflow_code}_unknown", "triage_to_information_required", "generic_metadata_check", {"unknown": True}, "warning"),
        OWNER_HEADERS,
        201,
    )["workflow_guard"]
    for guard in [warning_guard, blocked_guard, unknown_guard]:
        assert_safety_flags(guard)

    entity_id = run_ref("request-smoke")
    started = post(
        "/api/platform/operational-workflows/instances/start",
        {
            "agency_id": agency_id,
            "workflow_definition_id": definition_id,
            "entity_type": "request",
            "entity_id": entity_id,
            "context_snapshot_json": {"client_id": "client-smoke", "passenger_id": "passenger-smoke"},
            "metadata": {"smoke": True},
        },
        OWNER_HEADERS,
        201,
    )
    assert_safety_flags(started)
    instance = started["workflow_instance"]
    instance_id = instance["id"]
    if instance.get("current_state") != "submitted":
        raise AssertionError(f"Started workflow at wrong state: {instance}")

    agency_dashboard = get(f"/api/agencies/{agency_id}/operational-workflows", OWNER_HEADERS)
    assert_safety_flags(agency_dashboard)
    if not any(item.get("id") == instance_id for item in agency_dashboard.get("instances", [])):
        raise AssertionError("Agency dashboard did not include its own workflow instance.")
    if other_agency_id:
        other_dashboard = get(f"/api/agencies/{other_agency_id}/operational-workflows", OWNER_HEADERS)
        if any(item.get("id") == instance_id for item in other_dashboard.get("instances", [])):
            raise AssertionError("Workflow instance leaked into another agency dashboard.")

    available = get(f"/api/agencies/{agency_id}/operational-workflows/instances/{instance_id}/available-transitions", OWNER_HEADERS)
    warning_transition = find_transition(available.get("available_transitions") or [], "submitted_to_triage")
    if warning_transition.get("availability_status") != "warning_acknowledgement_required":
        raise AssertionError(f"Warning transition was not flagged for acknowledgement: {warning_transition}")

    no_ack = post(
        f"/api/agencies/{agency_id}/operational-workflows/instances/{instance_id}/execute-transition",
        {"transition_code": "submitted_to_triage", "reason": "Smoke warning without acknowledgement."},
        OWNER_HEADERS,
    )
    if no_ack.get("transition_status") != "warning_acknowledgement_required" or no_ack.get("state_updated") is not False:
        raise AssertionError(f"Warning transition without acknowledgement should not update state: {no_ack}")
    warnings = get(f"/api/agencies/{agency_id}/operational-workflows/instances/{instance_id}/warnings", OWNER_HEADERS)
    if not warnings.get("warnings"):
        raise AssertionError("Warning endpoint did not expose active warnings.")
    ack = post(
        f"/api/agencies/{agency_id}/operational-workflows/instances/{instance_id}/acknowledge-warning",
        {"warning_codes": [warning_guard["guard_code"]], "acknowledgement_notes": "Smoke acknowledgement."},
        OWNER_HEADERS,
    )
    if not ack.get("acknowledgement", {}).get("acknowledged_warning_codes"):
        raise AssertionError(f"Warning acknowledgement was not recorded: {ack}")

    with_ack = post(
        f"/api/agencies/{agency_id}/operational-workflows/instances/{instance_id}/execute-transition",
        {"transition_code": "submitted_to_triage", "reason": "Smoke warning acknowledged.", "acknowledge_warnings": True},
        OWNER_HEADERS,
    )
    if with_ack.get("transition_status") != "completed_with_warnings" or with_ack.get("state_updated") is not True:
        raise AssertionError(f"Acknowledged warning transition should update state: {with_ack}")
    if with_ack["workflow_instance"].get("current_state") != "triage":
        raise AssertionError("Workflow instance did not move to triage after acknowledged warning.")

    available_triage = get(f"/api/platform/operational-workflows/instances/{instance_id}/available-transitions", OWNER_HEADERS)
    blocked_transition = find_transition(available_triage.get("available_transitions") or [], "triage_to_planning")
    unknown_transition = find_transition(available_triage.get("available_transitions") or [], "triage_to_information_required")
    if blocked_transition.get("availability_status") != "blocked":
        raise AssertionError(f"Blocked transition was not blocked: {blocked_transition}")
    if unknown_transition.get("availability_status") != "manual_review_required":
        raise AssertionError(f"Unknown transition was not manual review: {unknown_transition}")

    blocked = post(
        f"/api/agencies/{agency_id}/operational-workflows/instances/{instance_id}/execute-transition",
        {"transition_code": "triage_to_planning", "reason": "Smoke blocked transition."},
        OWNER_HEADERS,
    )
    if blocked.get("transition_status") != "blocked" or blocked.get("state_updated") is not False:
        raise AssertionError(f"Blocked transition should be rejected safely: {blocked}")
    blockers = get(f"/api/agencies/{agency_id}/operational-workflows/instances/{instance_id}/blockers", OWNER_HEADERS)
    if not blockers.get("blockers"):
        raise AssertionError("Blocker endpoint did not expose active blockers after blocked transition.")

    unknown = post(
        f"/api/agencies/{agency_id}/operational-workflows/instances/{instance_id}/execute-transition",
        {"transition_code": "triage_to_information_required", "reason": "Smoke unknown guard handling."},
        OWNER_HEADERS,
    )
    if unknown.get("transition_status") != "manual_review_required" or unknown.get("state_updated") is not False:
        raise AssertionError(f"Unknown guard should require manual review without state update: {unknown}")
    if not any(item.get("status") == "unknown" for item in unknown.get("guard_results") or []):
        raise AssertionError(f"Unknown guard result was not preserved: {unknown}")

    history = get(f"/api/platform/operational-workflows/instances/{instance_id}/transitions", OWNER_HEADERS)
    transitions = history.get("transitions") or []
    if len(transitions) < 4 or history.get("immutable_history") is not True:
        raise AssertionError(f"Immutable transition history was not recorded: {history}")
    if not all(item.get("immutable_history") is True for item in transitions):
        raise AssertionError("Transition records did not preserve immutable_history flags.")
    events = get(f"/api/agencies/{agency_id}/operational-workflows/instances/{instance_id}/events", OWNER_HEADERS)
    if len(events.get("events") or []) < 4:
        raise AssertionError(f"Workflow events were not recorded: {events}")

    entity_summary = get(f"/api/agencies/{agency_id}/operational-workflows/entities/request/{entity_id}/summary", OWNER_HEADERS)
    if entity_summary.get("workflow_count") < 1 or entity_summary.get("entity_status_sync_disabled_by_default") is not True:
        raise AssertionError(f"Entity summary did not expose workflow metadata: {entity_summary}")
    platform_summary = get(f"/api/platform/operational-workflows/summary?agency_id={agency_id}", OWNER_HEADERS)
    if platform_summary.get("summary", {}).get("instance_count", 0) < 1:
        raise AssertionError(f"Platform workflow summary did not count instances: {platform_summary}")


def verify_production_safety_text() -> None:
    service_text = (ROOT / "backend/services/operational_workflow_orchestration_service.py").read_text(encoding="utf-8").lower()
    for required in [
        "entity_status_sync_disabled_by_default",
        "unrestricted_dynamic_mutation_disabled",
        "existing_workspace_services_preserved",
        "provider_integrations_disabled",
        "automatic_execution_disabled",
    ]:
        if required not in service_text:
            raise AssertionError(f"Operational workflow service missing safety marker: {required}")
    for path in [
        ROOT / "docs/architecture/operational-workflow-orchestration-foundation.md",
        ROOT / "frontend/src/pages/platform/OperationalWorkflowsPage.jsx",
        ROOT / "frontend/src/pages/agency/OperationalWorkflowsPage.jsx",
    ]:
        content = path.read_text(encoding="utf-8").lower()
        for text in ["metadata-only", "does not", "status"]:
            if text not in content:
                raise AssertionError(f"{path.relative_to(ROOT)} missing safety language: {text}")


def main() -> int:
    verify_models_and_registration()
    verify_router_ui_docs_registration()
    verify_workflow_endpoints()
    verify_production_safety_text()
    print("Phase 54.1 operational workflow orchestration foundation smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
