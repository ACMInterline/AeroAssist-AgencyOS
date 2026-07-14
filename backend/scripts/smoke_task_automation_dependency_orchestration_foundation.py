#!/usr/bin/env python3
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import (
    OperationalTaskAutomationRule,
    OperationalTaskAutomationRuleCreate,
    OperationalTaskAutomationRun,
    OperationalTaskAutomationRunRequest,
    OperationalTaskDependency,
    OperationalTaskDependencyCreate,
    OperationalTaskTemplate,
    OperationalTaskTemplateCreate,
)
from services.task_automation_dependency_service import (
    DEFAULT_AUTOMATION_RULES,
    OPERATIONAL_TASK_AUTOMATION_RULES_COLLECTION,
    OPERATIONAL_TASK_AUTOMATION_RUNS_COLLECTION,
    OPERATIONAL_TASK_DEPENDENCIES_COLLECTION,
    OPERATIONAL_TASK_TEMPLATES_COLLECTION,
    PHASE_LABEL,
    SAFE_TASK_TEMPLATES,
    TASK_AUTOMATION_RULE_STATUSES,
    TASK_AUTOMATION_RUN_STATUSES,
    TASK_AUTOMATION_TRIGGER_EVENTS,
    TASK_DEPENDENCY_STATUSES,
    TASK_DEPENDENCY_TYPES,
    TASK_TEMPLATE_STATUSES,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, put, request
from smoke_operational_workflow_orchestration_foundation import definition_payload


EXPECTED_PHASE = "phase_54_5_request_to_trip_operational_conversion_foundation"
ROOT = Path(__file__).resolve().parents[2]
AGENCY_AGENT_HEADERS = {"X-Demo-User-Email": "agency.agent@aeroassist.dev"}


def run_ref(prefix: str) -> str:
    return f"{prefix}-{int(time.time() * 1000)}"


def utc_iso(delta: timedelta | None = None) -> str:
    value = datetime.now(timezone.utc) + (delta or timedelta())
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def require_text(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8")
    if text not in content:
        raise AssertionError(f"{path.relative_to(ROOT)} missing expected text: {text}")


def reject_text(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8").lower()
    if text.lower() in content:
        raise AssertionError(f"{path.relative_to(ROOT)} contains rejected text: {text}")


def assert_safety_flags(payload: dict) -> None:
    for flag in [
        "metadata_only",
        "task_automation_dependency_orchestration_foundation",
        "existing_tasks_preserved",
        "request_tasks_reused",
        "safe_automatic_task_creation_enabled",
        "idempotent_task_generation_enabled",
        "dependency_blocking_enabled",
        "dependency_unblocking_enabled",
        "work_queue_integration_enabled",
        "sla_due_date_integration_enabled",
        "workflow_event_integration_enabled",
        "audit_run_records_enabled",
        "manual_retry_enabled",
        "arbitrary_code_execution_disabled",
        "provider_integrations_disabled",
        "external_api_calls_disabled",
        "ai_disabled",
        "background_workers_disabled",
        "schedulers_disabled",
        "unbounded_automation_disabled",
        "agency_isolation_enforced",
        "human_authority_final",
    ]:
        if payload.get(flag) is not True:
            raise AssertionError(f"Payload missing task automation safety flag {flag}: {payload}")


def request_builder_payload(reference: str) -> dict:
    return {
        "client": {
            "name": f"Task Automation Smoke Client {reference}",
            "email": f"{reference}@example.com",
            "phone": "+421900054400",
        },
        "passengers": [
            {
                "request_passenger_key": "pax-1",
                "first_name": "Automation",
                "last_name": "Traveler",
                "passenger_type": "adult",
            }
        ],
        "trip_type": "one_way",
        "segments": [
            {
                "segment_key": "seg-1",
                "sequence": 1,
                "origin_text": "SOF",
                "destination_text": "FRA",
                "departure_date": "2026-12-14",
                "marketing_airline": "LH",
                "operating_airline": "LH",
                "flight_number": "LH1703",
                "cabin_preference": "economy",
            }
        ],
        "services": [
            {
                "category": "mobility_assistance",
                "service_code": "WCHR",
                "details": {"notes": "Task automation smoke service requirement."},
                "applies_to_all_passengers": True,
                "applies_to_all_segments": True,
            }
        ],
        "title": "Phase 54.4 task automation request",
        "status": "new",
        "priority": "urgent",
        "source": "staff_created",
    }


def ensure_second_agency(existing_agencies: list[dict]) -> str:
    if len(existing_agencies) > 1:
        return existing_agencies[1]["id"]
    slug = run_ref("task-automation-smoke-agency").lower()
    created = post(
        "/api/agencies",
        {
            "name": "Task Automation Smoke Isolation Agency",
            "slug": slug,
            "legal_name": "Task Automation Smoke Isolation Agency Ltd",
            "status": "active",
            "subscription_status": "trial",
            "default_currency": "EUR",
            "country": "BG",
            "timezone": "UTC",
        },
        OWNER_HEADERS,
        201,
    )
    return created["agency"]["id"]


def create_request(agency_id: str) -> dict:
    reference = run_ref("task-auto-request").lower()
    return post(f"/api/agencies/{agency_id}/requests/builder", request_builder_payload(reference), AGENCY_AGENT_HEADERS, 201)["request"]


def start_workflow_instance(agency_id: str, request_id: str) -> dict:
    workflow_code = run_ref("task_auto_workflow").lower()
    definition = post("/api/platform/operational-workflows/definitions", definition_payload(workflow_code), OWNER_HEADERS, 201)["workflow_definition"]
    put(f"/api/platform/operational-workflows/definitions/{definition['id']}", {"status": "active"}, OWNER_HEADERS)
    return post(
        "/api/platform/operational-workflows/instances/start",
        {
            "agency_id": agency_id,
            "workflow_definition_id": definition["id"],
            "entity_type": "request",
            "entity_id": request_id,
            "context_snapshot_json": {"phase": "54.4 smoke"},
            "metadata": {"smoke": True},
        },
        OWNER_HEADERS,
        201,
    )["workflow_instance"]


def automation_run_payload(agency_id: str, request_id: str, workflow_instance_id: str) -> dict:
    return {
        "agency_id": agency_id,
        "trigger_event": "request_created",
        "source_entity_type": "request",
        "source_entity_id": request_id,
        "request_id": request_id,
        "template_codes": ["triage_request", "obtain_missing_passenger_data"],
        "event_snapshot_json": {
            "source_label": "Phase 54.4 smoke request",
            "request_id": request_id,
            "workflow_instance_id": workflow_instance_id,
        },
    }


def verify_models_and_registration() -> None:
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Service phase label mismatch: {PHASE_LABEL}")
    for collection in [
        OPERATIONAL_TASK_TEMPLATES_COLLECTION,
        OPERATIONAL_TASK_DEPENDENCIES_COLLECTION,
        OPERATIONAL_TASK_AUTOMATION_RULES_COLLECTION,
        OPERATIONAL_TASK_AUTOMATION_RUNS_COLLECTION,
    ]:
        if collection not in AGENCY_OWNED_COLLECTIONS:
            raise AssertionError(f"{collection} is not registered as agency-owned metadata.")
    for value in ["draft", "active", "paused", "archived"]:
        if value not in TASK_TEMPLATE_STATUSES or value not in TASK_AUTOMATION_RULE_STATUSES:
            raise AssertionError(f"Missing task template/rule status: {value}")
    for value in ["finish_to_start", "manual_review", "evidence_required"]:
        if value not in TASK_DEPENDENCY_TYPES:
            raise AssertionError(f"Missing dependency type: {value}")
    for value in ["pending", "blocked", "satisfied", "waived"]:
        if value not in TASK_DEPENDENCY_STATUSES:
            raise AssertionError(f"Missing dependency status: {value}")
    for value in ["completed", "completed_with_warnings", "failed", "skipped"]:
        if value not in TASK_AUTOMATION_RUN_STATUSES:
            raise AssertionError(f"Missing run status: {value}")
    for value in ["request_created", "service_requirement_detected", "offer_needed", "ticket_emd_linked", "manual_retry"]:
        if value not in TASK_AUTOMATION_TRIGGER_EVENTS:
            raise AssertionError(f"Missing trigger event: {value}")
    for template_code in [
        "triage_request",
        "obtain_missing_passenger_data",
        "obtain_passport_document",
        "request_medif",
        "confirm_poc_model_battery",
        "request_wheelchair_dimensions_battery",
        "request_petc_avih_documents",
        "request_airline_approval",
        "prepare_offer",
        "review_pricing_manual_quote",
        "follow_up_client_acceptance",
        "create_booking_readiness_check",
        "ticket_emd_verification",
        "invoice_payment_follow_up",
        "disruption_handling",
        "refund_change_claim_follow_up",
        "final_trip_document_check",
    ]:
        if template_code not in {template["template_code"] for template in SAFE_TASK_TEMPLATES}:
            raise AssertionError(f"Missing safe task template {template_code}.")
    if len(DEFAULT_AUTOMATION_RULES) != len(SAFE_TASK_TEMPLATES):
        raise AssertionError("Default automation rules should map one-to-one to safe templates.")

    template = OperationalTaskTemplate(**OperationalTaskTemplateCreate(template_code="smoke_template", title_pattern="Smoke", trigger_event="request_created").model_dump(mode="json", exclude_none=True))
    dependency = OperationalTaskDependency(agency_id="agency-smoke", predecessor_task_id="task-a", successor_task_id="task-b")
    rule = OperationalTaskAutomationRule(**OperationalTaskAutomationRuleCreate(rule_code="smoke_rule", name="Smoke rule", trigger_event="request_created", generated_template_code="triage_request").model_dump(mode="json", exclude_none=True), deduplication_key_pattern="{agency_id}:{source_entity_id}")
    run_request = OperationalTaskAutomationRunRequest(trigger_event="request_created", source_entity_type="request", source_entity_id="request-smoke")
    run = OperationalTaskAutomationRun(agency_id="agency-smoke", run_reference="TASK-AUTO-SMOKE", trigger_event="request_created", source_entity_type="request", source_entity_id="request-smoke", idempotency_key="smoke")
    for record in [template, dependency, rule, run]:
        dumped = record.model_dump(mode="json")
        if dumped.get("metadata_only") is not True or dumped.get("task_automation_dependency_orchestration_foundation") is not True:
            raise AssertionError(f"Task automation model lost metadata-only flags: {dumped}")
    if run_request.source_entity_type != "request":
        raise AssertionError("Automation run request model did not preserve source entity type.")

    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for marker in [
        "operational_task_templates_agency_code_lookup",
        "operational_task_dependencies_agency_successor_lookup",
        "operational_task_dependencies_source_lookup",
        "operational_task_automation_rules_enabled_status_lookup",
        "operational_task_automation_runs_agency_idempotency_lookup",
    ]:
        if marker not in database_py:
            raise AssertionError(f"Database index registration missing {marker}.")


def verify_router_ui_docs_registration() -> None:
    openapi = get("/openapi.json", OWNER_HEADERS)
    paths = openapi.get("paths") or {}
    for path, method in [
        ("/api/platform/task-automation", "get"),
        ("/api/platform/task-automation/templates", "get"),
        ("/api/platform/task-automation/templates", "post"),
        ("/api/platform/task-automation/templates/{template_id}", "put"),
        ("/api/platform/task-automation/rules", "get"),
        ("/api/platform/task-automation/rules", "post"),
        ("/api/platform/task-automation/rules/{rule_id}", "put"),
        ("/api/platform/task-automation/dependencies", "get"),
        ("/api/platform/task-automation/dependencies", "post"),
        ("/api/platform/task-automation/dependencies/{dependency_id}", "put"),
        ("/api/platform/task-automation/dependencies/{dependency_id}/satisfy", "post"),
        ("/api/platform/task-automation/dependencies/{dependency_id}/waive", "post"),
        ("/api/platform/task-automation/dependencies/evaluate", "post"),
        ("/api/platform/task-automation/runs", "get"),
        ("/api/platform/task-automation/runs", "post"),
        ("/api/platform/task-automation/runs/{run_id}/retry", "post"),
        ("/api/agencies/{agency_id}/task-automation", "get"),
        ("/api/agencies/{agency_id}/task-automation/templates", "get"),
        ("/api/agencies/{agency_id}/task-automation/templates", "post"),
        ("/api/agencies/{agency_id}/task-automation/rules", "get"),
        ("/api/agencies/{agency_id}/task-automation/runs", "get"),
        ("/api/agencies/{agency_id}/task-automation/runs", "post"),
        ("/api/agencies/{agency_id}/task-automation/runs/{run_id}/retry", "post"),
        ("/api/agencies/{agency_id}/task-automation/dependencies", "get"),
        ("/api/agencies/{agency_id}/task-automation/dependencies/{dependency_id}/satisfy", "post"),
        ("/api/agencies/{agency_id}/task-automation/dependencies/{dependency_id}/waive", "post"),
        ("/api/agencies/{agency_id}/task-automation/dependencies/evaluate", "post"),
    ]:
        assert_openapi_path(paths, path, method)
    for path in paths:
        lowered = path.lower()
        if lowered.startswith("/api/admin") or lowered.startswith("/api/agent"):
            raise AssertionError(f"Old API route root must not be registered: {path}")

    for path, text in [
        (ROOT / "frontend/src/App.jsx", "/platform/task-automation"),
        (ROOT / "frontend/src/App.jsx", "/agency/task-automation"),
        (ROOT / "frontend/src/pages/platform/TaskAutomationPage.jsx", "Task Automation"),
        (ROOT / "frontend/src/pages/agency/TaskAutomationPage.jsx", "Dependency Graph"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "task_automation"),
        (ROOT / "backend/services/saas_subscription_service.py", "task_automation"),
        (ROOT / "backend/services/blueprint_adoption_service.py", "Task Automation and Dependency Orchestration"),
        (ROOT / "docs/architecture/task-automation-dependency-orchestration-foundation.md", "Safe Task Creation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "operational_task_templates"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/platform/task-automation"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Task Automation and Dependency Orchestration"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "operational_task_automation_runs"),
        (ROOT / "docs/architecture/passenger-service-operations-principle.md", "Task Automation and Dependency Orchestration"),
        (ROOT / "docs/architecture/foundations/GLOSSARY.md", "Operational Task Automation Run"),
        (ROOT / "BUILD_PHASES.md", "Implemented Phase 54.4"),
        (ROOT / "README.md", "Task Automation and Dependency Orchestration Foundation"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/App.jsx",
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "backend/routers/platform_task_automation.py",
        ROOT / "backend/routers/agency_task_automation.py",
    ]:
        reject_text(path, "/admin/")
        reject_text(path, "/agent/")
    service_text = (ROOT / "backend/services/task_automation_dependency_service.py").read_text(encoding="utf-8").lower()
    for forbidden in ["eval(", "exec(", "subprocess", "backgroundtasks", "requests.get", "httpx", "openai", "send_email", "send_sms", "stripe"]:
        if forbidden in service_text:
            raise AssertionError(f"Task automation service contains forbidden execution semantic: {forbidden}")


def verify_health_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")
    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    for section_name in [
        "operational_workflow_orchestration_foundation",
        "agent_work_queue_assignment_foundation",
        "sla_operational_deadline_engine_foundation",
        "task_automation_dependency_orchestration_foundation",
    ]:
        if section_name not in readiness:
            raise AssertionError(f"Readiness missing section {section_name}.")
    section = readiness.get("task_automation_dependency_orchestration_foundation") or {}
    for key in [
        "task_automation_dependency_orchestration_enabled",
        "operational_task_templates_collection_enabled",
        "operational_task_dependencies_collection_enabled",
        "operational_task_automation_rules_collection_enabled",
        "operational_task_automation_runs_collection_enabled",
        "existing_task_system_preserved",
        "request_tasks_reused",
        "safe_automatic_task_creation_enabled",
        "idempotent_task_generation_enabled",
        "dependency_blocking_enabled",
        "dependency_unblocking_enabled",
        "work_queue_integration_enabled",
        "workflow_event_integration_enabled",
        "sla_due_date_integration_enabled",
        "audit_run_records_enabled",
        "manual_retry_enabled",
        "arbitrary_code_execution_disabled",
        "agency_isolation_enforced",
        "metadata_only",
    ]:
        if section.get(key) is not True:
            raise AssertionError(f"Readiness missing task automation flag: {key}")
    for count_key in [
        "safe_task_template_count",
        "default_task_automation_rule_count",
        "operational_task_template_count",
        "operational_task_dependency_count",
        "operational_task_automation_rule_count",
        "operational_task_automation_run_count",
        "operational_task_automation_run_status_counts",
        "operational_task_dependency_status_counts",
    ]:
        if count_key not in section:
            raise AssertionError(f"Readiness missing task automation count: {count_key}")
    if section.get("safe_task_template_count", 0) < 17:
        raise AssertionError("Readiness did not expose all safe task templates.")


def verify_task_automation_lifecycle(agency_id: str, other_agency_id: str) -> None:
    request("GET", "/api/platform/task-automation", None, AGENCY_AGENT_HEADERS, expect=403)
    platform_dashboard = get(f"/api/platform/task-automation?{urlencode({'agency_id': agency_id})}", OWNER_HEADERS)
    assert_safety_flags(platform_dashboard)
    if "triage_request" not in platform_dashboard.get("safe_template_codes", []):
        raise AssertionError("Platform task automation dashboard missing safe template codes.")

    task_request = create_request(agency_id)
    workflow_instance = start_workflow_instance(agency_id, task_request["id"])
    payload = automation_run_payload(agency_id, task_request["id"], workflow_instance["id"])

    first_run = post(f"/api/agencies/{agency_id}/task-automation/runs", payload, AGENCY_AGENT_HEADERS, 201)
    assert_safety_flags(first_run)
    run = first_run["run"]
    if len(run.get("tasks_created") or []) != 2:
        raise AssertionError(f"Expected two generated tasks, got: {run}")
    if run.get("status") not in {"completed", "completed_with_warnings"}:
        raise AssertionError(f"Unexpected automation run status: {run.get('status')}")

    duplicate = post(f"/api/agencies/{agency_id}/task-automation/runs", payload, AGENCY_AGENT_HEADERS, 201)
    if duplicate.get("idempotent_reused") is not True or duplicate["run"]["id"] != run["id"]:
        raise AssertionError("Duplicate automation run did not reuse idempotent run metadata.")

    dashboard = get(f"/api/agencies/{agency_id}/task-automation?{urlencode({'source_entity_type': 'request', 'source_entity_id': task_request['id']})}", AGENCY_AGENT_HEADERS)
    assert_safety_flags(dashboard)
    dependencies = dashboard.get("dependencies") or []
    if len(dependencies) != 1:
        raise AssertionError(f"Expected one dependency between request-created tasks: {dependencies}")
    dependency = dependencies[0]
    predecessor = dependency.get("predecessor_task") or {}
    successor = dependency.get("successor_task") or {}
    if dependency.get("status") != "pending" or successor.get("status") != "waiting":
        raise AssertionError(f"Dependency should block successor until predecessor completion: {dependency}")
    if not predecessor.get("due_at") or not successor.get("due_at"):
        raise AssertionError("Generated request tasks should carry due_at metadata from template offsets.")

    queue = get(f"/api/agencies/{agency_id}/work-queue?{urlencode({'include_completed': 'true'})}", AGENCY_AGENT_HEADERS)
    queue_items = queue.get("items") or []
    predecessor_item = next((item for item in queue_items if item.get("request_task_id") == predecessor["id"]), None)
    successor_item = next((item for item in queue_items if item.get("request_task_id") == successor["id"]), None)
    if not predecessor_item or not successor_item:
        raise AssertionError("Generated tasks were not synchronized into the agent work queue.")
    if successor_item.get("blocker_status") != "manual_review" or successor_item.get("queue_code") != "waiting_client":
        raise AssertionError(f"Blocked successor did not refresh queue blocker metadata: {successor_item}")

    events = get(f"/api/platform/operational-workflows/instances/{workflow_instance['id']}/events", OWNER_HEADERS).get("events") or []
    if not any(event.get("source_entity_id") == run["id"] and event.get("source_module") == "task_automation_dependency_orchestration" for event in events):
        raise AssertionError("Task automation run did not record workflow-event metadata.")

    post(f"/api/agencies/{agency_id}/requests/{task_request['id']}/tasks/{predecessor['id']}/complete", {}, AGENCY_AGENT_HEADERS)
    evaluated = post(
        f"/api/agencies/{agency_id}/task-automation/dependencies/evaluate?{urlencode({'source_entity_type': 'request', 'source_entity_id': task_request['id']})}",
        {},
        AGENCY_AGENT_HEADERS,
    )
    assert_safety_flags(evaluated)
    released_dependencies = get(
        f"/api/agencies/{agency_id}/task-automation/dependencies?{urlencode({'source_entity_type': 'request', 'source_entity_id': task_request['id']})}",
        AGENCY_AGENT_HEADERS,
    )["dependencies"]
    released = released_dependencies[0]
    if released.get("status") != "satisfied" or released.get("successor_task", {}).get("status") != "open":
        raise AssertionError(f"Dependency should be satisfied and successor released: {released}")

    retry = post(f"/api/agencies/{agency_id}/task-automation/runs/{run['id']}/retry", {"reason": "Smoke safe retry"}, AGENCY_AGENT_HEADERS)
    assert_safety_flags(retry)
    retry_run = retry["run"]
    if retry_run.get("retry_of_run_id") != run["id"]:
        raise AssertionError("Manual safe retry did not preserve retry lineage.")
    if len(retry_run.get("tasks_created") or []) != 0 or len(retry_run.get("tasks_skipped") or []) < 2:
        raise AssertionError(f"Safe retry should skip existing generated tasks: {retry_run}")

    other_dashboard = get(f"/api/agencies/{other_agency_id}/task-automation", OWNER_HEADERS)
    if any(item.get("id") in {run["id"], retry_run["id"]} for item in other_dashboard.get("runs") or []):
        raise AssertionError("Task automation runs leaked across agency boundaries.")
    request("GET", f"/api/agencies/{other_agency_id}/task-automation/runs", None, AGENCY_AGENT_HEADERS, expect=403)


def main() -> None:
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("No demo agency exists for task automation smoke test.")
    agency_id = agencies[0]["id"]
    other_agency_id = ensure_second_agency(agencies)
    verify_models_and_registration()
    verify_router_ui_docs_registration()
    verify_health_readiness()
    verify_task_automation_lifecycle(agency_id, other_agency_id)
    print("task automation dependency orchestration foundation smoke passed")


if __name__ == "__main__":
    main()
