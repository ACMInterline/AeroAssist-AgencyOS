#!/usr/bin/env python3
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import (
    OperationalAssignmentEvent,
    OperationalBulkAssignmentRequest,
    OperationalQueueDefinition,
    OperationalQueueDefinitionCreate,
    OperationalQueueView,
    OperationalQueueViewCreate,
    OperationalWorkItem,
    OperationalWorkItemCreate,
    OperationalWorkItemGenerateRequest,
)
from services.agent_work_queue_service import (
    ASSIGNMENT_EVENT_TYPES,
    BLOCKER_STATUSES,
    CANONICAL_QUEUE_CODES,
    DEFAULT_QUEUE_DEFINITIONS,
    OPERATIONAL_ASSIGNMENT_EVENTS_COLLECTION,
    OPERATIONAL_QUEUE_DEFINITIONS_COLLECTION,
    OPERATIONAL_QUEUE_VIEWS_COLLECTION,
    OPERATIONAL_WORK_ITEMS_COLLECTION,
    PHASE_LABEL,
    SLA_STATUSES,
    WORK_ITEM_PRIORITIES,
    WORK_ITEM_SEVERITIES,
    WORK_ITEM_STATUSES,
    WORK_ITEM_TYPES,
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
        "agent_work_queue_assignment_foundation",
        "canonical_operational_queue",
        "existing_task_system_preserved",
        "reuse_existing_tasks_timelines_workflows_enabled",
        "client_facing_context_hidden",
        "platform_governance_does_not_silently_act_as_agency_staff",
        "agency_isolation_enforced",
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


def request_builder_payload(reference: str) -> dict:
    return {
        "client": {
            "name": f"Queue Smoke Client {reference}",
            "email": f"{reference}@example.com",
            "phone": "+421900054200",
        },
        "passengers": [
            {
                "request_passenger_key": "pax-1",
                "first_name": "Queue",
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
                "departure_date": "2026-12-13",
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
                "details": {"notes": "Queue smoke service requirement."},
                "applies_to_all_passengers": True,
                "applies_to_all_segments": True,
            }
        ],
        "title": "Phase 54.2 work queue request",
        "status": "new",
        "priority": "urgent",
        "source": "staff_created",
    }


def generate_payload(source_entity_id: str, suffix: str = "") -> dict:
    return {
        "work_item_type": "policy_gap_manual_review",
        "source_entity_type": "knowledge_issue",
        "source_entity_id": source_entity_id,
        "title": f"Policy gap requires manual review {suffix}".strip(),
        "summary": "Metadata-only work item generated from a knowledge gap.",
        "priority": "critical",
        "severity": "critical",
        "queue_code": "knowledge_gap_queue",
        "sla_status": "due_soon",
        "blocker_status": "manual_review",
        "generation_reason": "smoke_idempotency",
        "source_snapshot_json": {"source": "smoke", "suffix": suffix},
        "compatibility_mapping_json": {"knowledge_issue_id": source_entity_id},
    }


def create_manual_work_item(agency_id: str, suffix: str, priority: str = "normal", due_at: str | None = None) -> dict:
    response = post(
        f"/api/agencies/{agency_id}/work-queue/work-items",
        {
            "work_item_type": "manual",
            "source_entity_type": "request",
            "source_entity_id": run_ref(f"manual-source-{suffix}"),
            "title": f"Manual queue item {suffix}",
            "summary": "Manual metadata-only work item.",
            "priority": priority,
            "severity": "medium",
            "queue_code": "unassigned",
            "due_at": due_at,
            "internal_context_json": {"internal_note": "hidden from client routes"},
        },
        AGENCY_AGENT_HEADERS,
        201,
    )
    assert_safety_flags(response)
    return response["work_item"]


def assert_item_present(items: list[dict], work_item_id: str, message: str) -> dict:
    item = next((candidate for candidate in items if candidate.get("id") == work_item_id), None)
    if not item:
        raise AssertionError(message)
    return item


def verify_models_and_registration() -> None:
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Service phase label mismatch: {PHASE_LABEL}")
    for collection in [
        OPERATIONAL_WORK_ITEMS_COLLECTION,
        OPERATIONAL_QUEUE_DEFINITIONS_COLLECTION,
        OPERATIONAL_ASSIGNMENT_EVENTS_COLLECTION,
        OPERATIONAL_QUEUE_VIEWS_COLLECTION,
    ]:
        if collection not in AGENCY_OWNED_COLLECTIONS:
            raise AssertionError(f"{collection} is not registered as agency-owned metadata.")
    for value in ["open", "accepted", "in_progress", "blocked", "completed", "reopened"]:
        if value not in WORK_ITEM_STATUSES:
            raise AssertionError(f"Missing work item status: {value}")
    for value in ["critical", "urgent", "high", "normal", "low"]:
        if value not in WORK_ITEM_PRIORITIES:
            raise AssertionError(f"Missing priority: {value}")
    for value in ["critical", "high", "medium", "low"]:
        if value not in WORK_ITEM_SEVERITIES:
            raise AssertionError(f"Missing severity: {value}")
    for value in ["blocked", "waiting_client", "waiting_airline_supplier", "waiting_documents", "waiting_approval", "waiting_payment"]:
        if value not in BLOCKER_STATUSES:
            raise AssertionError(f"Missing blocker status: {value}")
    for value in ["due_soon", "overdue", "breached", "paused", "completed", "unknown"]:
        if value not in SLA_STATUSES:
            raise AssertionError(f"Missing SLA status: {value}")
    for value in ["unassigned", "my_work", "team_queue", "urgent_critical", "overdue", "blocked", "knowledge_gap_queue", "workflow_blocker_queue"]:
        if value not in CANONICAL_QUEUE_CODES:
            raise AssertionError(f"Missing canonical queue: {value}")
    for value in ["assigned_to_self", "assigned", "reassigned", "unassigned", "bulk_assigned", "completed", "reopened"]:
        if value not in ASSIGNMENT_EVENT_TYPES:
            raise AssertionError(f"Missing assignment event type: {value}")
    for value in ["new_request_triage", "booking_awaiting_ticketing", "document_missing_or_expiring", "workflow_blocker", "pilot_readiness_blocker"]:
        if value not in WORK_ITEM_TYPES:
            raise AssertionError(f"Missing work item type: {value}")
    if len(DEFAULT_QUEUE_DEFINITIONS) < 10:
        raise AssertionError("Expected default definitions for the canonical work queues.")

    work_item = OperationalWorkItem(
        agency_id="agency-smoke",
        work_item_code="OWI-MODEL",
        work_item_type="manual",
        source_entity_type="request",
        source_entity_id="request-smoke",
        title="Model smoke",
    )
    created = OperationalWorkItemCreate(
        agency_id="agency-smoke",
        work_item_type="manual",
        source_entity_type="request",
        source_entity_id="request-create",
        title="Create model smoke",
    )
    generated = OperationalWorkItemGenerateRequest(
        work_item_type="workflow_blocker",
        source_entity_type="workflow",
        source_entity_id="workflow-smoke",
        title="Generate model smoke",
    )
    definition = OperationalQueueDefinition(**OperationalQueueDefinitionCreate(queue_code="smoke", name="Smoke").model_dump(mode="json", exclude_none=True))
    view = OperationalQueueView(
        **OperationalQueueViewCreate(agency_id="agency-smoke", view_code="smoke_view", name="Smoke View", queue_code="unassigned").model_dump(mode="json", exclude_none=True)
    )
    event = OperationalAssignmentEvent(agency_id="agency-smoke", work_item_id=work_item.id, event_type="assigned", actor_user_id="user-smoke")
    bulk = OperationalBulkAssignmentRequest(work_item_ids=[work_item.id], to_user_id="user-smoke", reason="model smoke")
    for record in [work_item, definition, view, event]:
        dumped = record.model_dump(mode="json")
        if dumped.get("metadata_only") is not True or dumped.get("agent_work_queue_assignment_foundation") is not True:
            raise AssertionError(f"Queue model lost metadata-only flags: {dumped}")
    if created.work_item_type != "manual" or generated.work_item_type != "workflow_blocker" or bulk.max_items < 1:
        raise AssertionError("Create/generate/bulk queue request models did not preserve fields.")

    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for marker in [
        "operational_work_items_source_fingerprint_unique",
        "operational_work_items_agency_queue_lookup",
        "operational_work_items_request_task_lookup",
        "operational_queue_definitions_agency_code_lookup",
        "operational_assignment_events_history_lookup",
        "operational_queue_views_agency_code_lookup",
    ]:
        if marker not in database_py:
            raise AssertionError(f"Database index registration missing {marker}.")


def verify_router_ui_docs_registration() -> None:
    openapi = get("/openapi.json", OWNER_HEADERS)
    paths = openapi.get("paths") or {}
    for path, method in [
        ("/api/platform/work-queues", "get"),
        ("/api/platform/work-queues/summary", "get"),
        ("/api/platform/work-queues/definitions", "get"),
        ("/api/platform/work-queues/definitions", "post"),
        ("/api/platform/work-queues/definitions/{definition_id}", "put"),
        ("/api/platform/work-queues/views", "get"),
        ("/api/platform/work-queues/views", "post"),
        ("/api/platform/work-queues/work-items", "get"),
        ("/api/platform/work-queues/work-items", "post"),
        ("/api/platform/work-queues/work-items/generate", "post"),
        ("/api/platform/work-queues/work-items/sync", "post"),
        ("/api/platform/work-queues/work-items/{work_item_id}", "get"),
        ("/api/platform/work-queues/work-items/{work_item_id}/events", "get"),
        ("/api/agencies/{agency_id}/work-queue", "get"),
        ("/api/agencies/{agency_id}/work-queue/summary", "get"),
        ("/api/agencies/{agency_id}/work-queue/queue-definitions", "get"),
        ("/api/agencies/{agency_id}/work-queue/views", "get"),
        ("/api/agencies/{agency_id}/work-queue/work-items", "post"),
        ("/api/agencies/{agency_id}/work-queue/work-items/generate", "post"),
        ("/api/agencies/{agency_id}/work-queue/work-items/sync", "post"),
        ("/api/agencies/{agency_id}/work-queue/work-items/bulk-assign", "post"),
        ("/api/agencies/{agency_id}/work-queue/work-items/{work_item_id}/assign-self", "post"),
        ("/api/agencies/{agency_id}/work-queue/work-items/{work_item_id}/assign", "post"),
        ("/api/agencies/{agency_id}/work-queue/work-items/{work_item_id}/reassign", "post"),
        ("/api/agencies/{agency_id}/work-queue/work-items/{work_item_id}/unassign", "post"),
        ("/api/agencies/{agency_id}/work-queue/work-items/{work_item_id}/accept", "post"),
        ("/api/agencies/{agency_id}/work-queue/work-items/{work_item_id}/release", "post"),
        ("/api/agencies/{agency_id}/work-queue/work-items/{work_item_id}/in-progress", "post"),
        ("/api/agencies/{agency_id}/work-queue/work-items/{work_item_id}/block", "post"),
        ("/api/agencies/{agency_id}/work-queue/work-items/{work_item_id}/complete", "post"),
        ("/api/agencies/{agency_id}/work-queue/work-items/{work_item_id}/reopen", "post"),
    ]:
        assert_openapi_path(paths, path, method)
    for path in paths:
        lowered = path.lower()
        if lowered.startswith("/api/admin") or lowered.startswith("/api/agent"):
            raise AssertionError(f"Old API route root must not be registered: {path}")
        if "/api/platform/work-queues/work-items/{work_item_id}/assign" in lowered or "/api/platform/work-queues/work-items/{work_item_id}/complete" in lowered:
            raise AssertionError(f"Platform governance must not silently act as agency staff: {path}")

    for path, text in [
        (ROOT / "frontend/src/App.jsx", "/platform/work-queues"),
        (ROOT / "frontend/src/App.jsx", "/agency/work-queue"),
        (ROOT / "frontend/src/pages/platform/WorkQueueGovernancePage.jsx", "Platform governance only"),
        (ROOT / "frontend/src/pages/agency/AgentWorkQueuePage.jsx", "Bulk assign to me"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Agent Work Queue"),
        (ROOT / "backend/services/saas_subscription_service.py", "work_queue"),
        (ROOT / "backend/services/blueprint_adoption_service.py", "Agent Work Queue and Assignment"),
        (ROOT / "docs/architecture/agent-work-queue-assignment-foundation.md", "canonical operational work queue"),
        (ROOT / "docs/architecture/current-model-inventory.md", "operational_work_items"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/platform/work-queues"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Agent Work Queue and Assignment"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "operational_queue_views"),
        (ROOT / "docs/architecture/passenger-service-operations-principle.md", "Agent Work Queue"),
        (ROOT / "docs/architecture/foundations/GLOSSARY.md", "Agent Work Queue"),
        (ROOT / "BUILD_PHASES.md", "Implemented Phase 54.2"),
        (ROOT / "README.md", "Agent Work Queue and Assignment Foundation"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "frontend/src/App.jsx",
        ROOT / "frontend/src/lib/moduleCatalog.js",
        ROOT / "backend/routers/platform_agent_work_queues.py",
        ROOT / "backend/routers/agency_agent_work_queues.py",
    ]:
        reject_text(path, "/admin/")
        reject_text(path, "/agent/")


def ensure_second_agency(existing_agencies: list[dict]) -> str:
    if len(existing_agencies) > 1:
        return existing_agencies[1]["id"]
    slug = run_ref("queue-smoke-agency").lower()
    created = post(
        "/api/agencies",
        {
            "name": "Queue Smoke Isolation Agency",
            "slug": slug,
            "legal_name": "Queue Smoke Isolation Agency Ltd",
            "status": "active",
            "subscription_status": "trial",
            "default_currency": "EUR",
            "country": "BG",
            "timezone": "Europe/Sofia",
        },
        OWNER_HEADERS,
        201,
    )
    return created["agency"]["id"]


def verify_health_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")
    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("agent_work_queue_assignment_foundation") or {}
    for key in [
        "agent_work_queue_assignment_enabled",
        "operational_work_items_collection_enabled",
        "platform_queue_governance_enabled",
        "agency_work_queue_enabled",
        "assignment_actions_enabled",
        "bulk_safe_assignment_enabled",
        "idempotent_work_item_generation_enabled",
        "workflow_event_integration_enabled",
        "request_task_compatibility_mapping_enabled",
        "timeline_history_integration_enabled",
        "existing_task_system_preserved",
        "client_facing_context_hidden",
        "platform_governance_does_not_silently_act_as_agency_staff",
        "deterministic_queue_ordering_enabled",
        "agency_isolation_enforced",
        "metadata_only",
    ]:
        if section.get(key) is not True:
            raise AssertionError(f"Readiness missing queue foundation flag: {key}")
    for count_key in [
        "operational_work_item_count",
        "operational_queue_definition_count",
        "operational_assignment_event_count",
        "operational_queue_view_count",
        "operational_work_item_status_counts",
        "operational_work_item_priority_counts",
        "operational_assignment_event_type_counts",
    ]:
        if count_key not in section:
            raise AssertionError(f"Readiness missing queue count: {count_key}")
    if section.get("readiness_required") is not False:
        raise AssertionError("Agent work queue foundation should not be deployment-readiness required.")


def verify_queue_lifecycle(agency_id: str, other_agency_id: str) -> tuple[str, str]:
    agent_auth = get("/api/auth/me", AGENCY_AGENT_HEADERS)
    agent_user = agent_auth.get("user") or {}
    if not agent_user.get("id"):
        raise AssertionError("Demo agency agent user was not resolved.")

    request("GET", "/api/platform/work-queues", None, AGENCY_AGENT_HEADERS, expect=403)
    platform_dashboard = get(f"/api/platform/work-queues?{urlencode({'agency_id': agency_id})}", OWNER_HEADERS)
    assert_safety_flags(platform_dashboard)
    if "ordering" not in platform_dashboard or len(platform_dashboard.get("queue_definitions") or []) < 10:
        raise AssertionError("Platform work queue dashboard missing ordering or default definitions.")

    definition = post(
        "/api/platform/work-queues/definitions",
        {
            "agency_id": agency_id,
            "queue_code": run_ref("queue_governance").lower(),
            "name": "Queue Governance Smoke",
            "description": "Metadata-only queue definition.",
            "entity_types": ["request", "booking_workspace"],
            "filter_json": {"priority": ["urgent", "critical"]},
            "sort_json": {"priority": "desc", "due_at": "asc"},
            "assignment_strategy": "manual",
        },
        OWNER_HEADERS,
        201,
    )["queue_definition"]
    updated_definition = put(
        f"/api/platform/work-queues/definitions/{definition['id']}",
        {"description": "Updated queue definition metadata.", "is_active": True},
        OWNER_HEADERS,
    )["queue_definition"]
    if "Updated queue definition" not in (updated_definition.get("description") or ""):
        raise AssertionError("Queue definition update did not persist.")

    queue_view = post(
        f"/api/agencies/{agency_id}/work-queue/views",
        {
            "name": "My urgent work",
            "queue_code": "urgent_critical",
            "owner_scope": "user",
            "owner_user_id": agent_user["id"],
            "column_settings_json": {"columns": ["priority", "due_at", "source"]},
            "sort_json": {"priority": "desc", "due_at": "asc"},
            "visibility": "private",
        },
        AGENCY_AGENT_HEADERS,
        201,
    )["queue_view"]
    if queue_view.get("agency_id") != agency_id:
        raise AssertionError("Agency queue view did not preserve agency scope.")

    manual_item = create_manual_work_item(agency_id, "lifecycle", "high", utc_iso(timedelta(hours=2)))
    generated_once = post(f"/api/agencies/{agency_id}/work-queue/work-items/generate", generate_payload(run_ref("knowledge-source")), AGENCY_AGENT_HEADERS, 201)
    generated_twice = post(
        f"/api/agencies/{agency_id}/work-queue/work-items/generate",
        generate_payload(generated_once["work_item"]["source_entity_id"], "second"),
        AGENCY_AGENT_HEADERS,
        201,
    )
    if generated_twice.get("idempotent_reused") is not True or generated_twice["work_item"]["id"] != generated_once["work_item"]["id"]:
        raise AssertionError("Idempotent work item generation did not reuse existing source metadata.")

    assigned = post(
        f"/api/agencies/{agency_id}/work-queue/work-items/{manual_item['id']}/assign-self",
        {"reason": "Taking ownership in smoke."},
        AGENCY_AGENT_HEADERS,
    )["work_item"]
    if assigned.get("assigned_user_id") != agent_user["id"] or assigned.get("status") != "accepted":
        raise AssertionError(f"Assign to self failed: {assigned}")
    released = post(
        f"/api/agencies/{agency_id}/work-queue/work-items/{manual_item['id']}/release",
        {"reason": "Release for reassignment smoke."},
        AGENCY_AGENT_HEADERS,
    )["work_item"]
    if released.get("assigned_user_id") is not None or released.get("status") != "open":
        raise AssertionError(f"Release failed: {released}")
    reassigned = post(
        f"/api/agencies/{agency_id}/work-queue/work-items/{manual_item['id']}/assign",
        {"to_user_id": agent_user["id"], "reason": "Assign to agent smoke."},
        AGENCY_AGENT_HEADERS,
    )["work_item"]
    if reassigned.get("assigned_user_id") != agent_user["id"]:
        raise AssertionError("Assign action did not set the target user.")
    in_progress = post(
        f"/api/agencies/{agency_id}/work-queue/work-items/{manual_item['id']}/in-progress",
        {"reason": "Start work smoke."},
        AGENCY_AGENT_HEADERS,
    )["work_item"]
    if in_progress.get("status") != "in_progress":
        raise AssertionError("Mark in progress failed.")
    blocked = post(
        f"/api/agencies/{agency_id}/work-queue/work-items/{manual_item['id']}/block",
        {"reason": "Waiting on client evidence.", "blocker_status": "waiting_client"},
        AGENCY_AGENT_HEADERS,
    )["work_item"]
    if blocked.get("status") != "blocked" or blocked.get("blocker_status") != "waiting_client":
        raise AssertionError("Block action failed.")
    completed = post(
        f"/api/agencies/{agency_id}/work-queue/work-items/{manual_item['id']}/complete",
        {"reason": "Completed smoke metadata."},
        AGENCY_AGENT_HEADERS,
    )["work_item"]
    if completed.get("status") != "completed" or completed.get("sla_status") != "completed":
        raise AssertionError("Complete action failed.")
    reopened = post(
        f"/api/agencies/{agency_id}/work-queue/work-items/{manual_item['id']}/reopen",
        {"reason": "Reopen smoke metadata."},
        AGENCY_AGENT_HEADERS,
    )["work_item"]
    if reopened.get("status") != "reopened" or reopened.get("completed_at") is not None:
        raise AssertionError("Reopen action failed.")

    events = get(f"/api/agencies/{agency_id}/work-queue/work-items/{manual_item['id']}/events", AGENCY_AGENT_HEADERS)
    event_types = {event.get("event_type") for event in events.get("events") or []}
    for event_type in ["created", "assigned_to_self", "released", "assigned", "in_progress", "completed", "reopened"]:
        if event_type not in event_types:
            raise AssertionError(f"Assignment history missing {event_type}: {event_types}")

    bulk_one = create_manual_work_item(agency_id, "bulk-one")
    bulk_two = create_manual_work_item(agency_id, "bulk-two")
    bulk = post(
        f"/api/agencies/{agency_id}/work-queue/work-items/bulk-assign",
        {
            "work_item_ids": [bulk_one["id"], bulk_two["id"], manual_item["id"]],
            "to_user_id": agent_user["id"],
            "reason": "Bulk safe assignment smoke.",
            "only_unassigned": True,
            "max_items": 10,
        },
        AGENCY_AGENT_HEADERS,
    )
    if bulk.get("assigned_count") != 2 or bulk.get("skipped_count") < 1:
        raise AssertionError(f"Bulk safe assignment did not assign and skip as expected: {bulk}")

    my_work = get(f"/api/agencies/{agency_id}/work-queue?{urlencode({'queue_code': 'my_work'})}", AGENCY_AGENT_HEADERS)
    assert_item_present(my_work.get("items") or [], bulk_one["id"], "My work queue did not include assigned bulk item.")
    waiting_client = get(f"/api/agencies/{agency_id}/work-queue?{urlencode({'queue_code': 'waiting_client', 'include_completed': 'true'})}", AGENCY_AGENT_HEADERS)
    assert_item_present(waiting_client.get("items") or [], manual_item["id"], "Waiting-client queue did not include blocked lifecycle item.")

    overdue_item = create_manual_work_item(agency_id, "overdue", "urgent", utc_iso(timedelta(days=-1)))
    low_item = create_manual_work_item(agency_id, "low", "low", utc_iso(timedelta(days=5)))
    ordered = get(f"/api/agencies/{agency_id}/work-queue?{urlencode({'include_completed': 'true'})}", AGENCY_AGENT_HEADERS).get("items") or []
    ordered_ids = [item.get("id") for item in ordered]
    if ordered_ids.index(overdue_item["id"]) > ordered_ids.index(low_item["id"]):
        raise AssertionError("Deterministic ordering did not prioritize urgent overdue work ahead of low future work.")
    overdue_queue = get(f"/api/agencies/{agency_id}/work-queue?{urlencode({'queue_code': 'overdue'})}", AGENCY_AGENT_HEADERS)
    assert_item_present(overdue_queue.get("items") or [], overdue_item["id"], "Overdue queue did not include overdue item.")

    other_agency_queue = get(f"/api/agencies/{other_agency_id}/work-queue?{urlencode({'include_completed': 'true'})}", OWNER_HEADERS)
    if any(item.get("id") in {manual_item["id"], overdue_item["id"], generated_once["work_item"]["id"]} for item in other_agency_queue.get("items") or []):
        raise AssertionError("Agency work queue leaked items across agency boundaries.")
    request("GET", f"/api/agencies/{other_agency_id}/work-queue/work-items/{manual_item['id']}", None, AGENCY_AGENT_HEADERS, expect=403)

    platform_item = get(f"/api/platform/work-queues/work-items/{manual_item['id']}", OWNER_HEADERS)["work_item"]
    if platform_item.get("internal_context_json", {}).get("internal_note") != "hidden from client routes":
        raise AssertionError("Platform governance did not preserve internal context metadata.")
    if platform_item.get("client_facing_context_hidden") is not True:
        raise AssertionError("Work item projection did not mark internal context as hidden from client-facing routes.")
    return agent_user["id"], generated_once["work_item"]["id"]


def verify_source_synchronization(agency_id: str, agent_user_id: str) -> None:
    reference = run_ref("queue-request").lower()
    created_request = post(
        f"/api/agencies/{agency_id}/requests/builder",
        request_builder_payload(reference),
        AGENCY_AGENT_HEADERS,
        201,
    )
    request_id = created_request["request"]["id"]
    task = post(
        f"/api/agencies/{agency_id}/requests/{request_id}/tasks",
        {
            "assigned_user_id": agent_user_id,
            "title": "Overdue request task smoke",
            "description": "Request task should synchronize into the canonical work queue.",
            "status": "open",
            "priority": "high",
            "due_at": utc_iso(timedelta(days=-2)),
            "visibility": "internal",
        },
        AGENCY_AGENT_HEADERS,
        201,
    )["task"]

    workflow_code = run_ref("queue_workflow").lower()
    definition = post("/api/platform/operational-workflows/definitions", definition_payload(workflow_code), OWNER_HEADERS, 201)["workflow_definition"]
    put(f"/api/platform/operational-workflows/definitions/{definition['id']}", {"status": "active"}, OWNER_HEADERS)
    started = post(
        "/api/platform/operational-workflows/instances/start",
        {
            "agency_id": agency_id,
            "workflow_definition_id": definition["id"],
            "entity_type": "request",
            "entity_id": request_id,
            "context_snapshot_json": {"phase": "54.2 smoke"},
            "metadata": {"smoke": True},
        },
        OWNER_HEADERS,
        201,
    )["workflow_instance"]

    synced_once = post(f"/api/agencies/{agency_id}/work-queue/work-items/sync", {}, AGENCY_AGENT_HEADERS)
    assert_safety_flags(synced_once)
    synced_twice = post(f"/api/agencies/{agency_id}/work-queue/work-items/sync", {}, AGENCY_AGENT_HEADERS)
    if synced_twice.get("reused_count", 0) < synced_once.get("generated_count", 0):
        raise AssertionError(f"Source synchronization was not idempotent: first={synced_once}, second={synced_twice}")

    items = get(f"/api/agencies/{agency_id}/work-queue?{urlencode({'include_completed': 'true'})}", AGENCY_AGENT_HEADERS).get("items") or []
    task_item = next((item for item in items if item.get("request_task_id") == task["id"]), None)
    if not task_item or task_item.get("work_item_type") not in {"overdue_task", "task_deadline"}:
        raise AssertionError("Request task did not synchronize into a compatible work item.")
    workflow_item = next((item for item in items if item.get("workflow_instance_id") == started["id"]), None)
    if not workflow_item or workflow_item.get("source", {}).get("workflow_instance_id") != started["id"]:
        raise AssertionError("Operational workflow event did not synchronize into a work item.")
    if not any(event.get("event_type") in {"generated", "synchronized"} for event in task_item.get("assignment_events", [])):
        raise AssertionError("Generated work item did not expose compact assignment/history events.")


def verify_blueprint_registration() -> None:
    adoption = get("/api/platform/blueprint/adoption-map", OWNER_HEADERS)
    categories = {item.get("category") for item in adoption.get("items") or []}
    if "Agent Work Queue and Assignment" not in categories:
        raise AssertionError("Blueprint adoption map missing Agent Work Queue and Assignment.")
    route_policy = get("/api/platform/blueprint/route-policy", OWNER_HEADERS)
    mappings = {(item.get("supplementary"), item.get("agencyos")) for item in route_policy.get("route_mappings") or []}
    for mapping in [("/admin/work-queues", "/platform/work-queues"), ("/agent/work-queue", "/agency/work-queue")]:
        if mapping not in mappings:
            raise AssertionError(f"Route policy missing work queue mapping: {mapping}")
    gaps = get("/api/platform/blueprint/gaps", OWNER_HEADERS)
    if not any("Agent work queue and assignment foundation built in Phase 54.2" in item for item in gaps.get("already_built", [])):
        raise AssertionError("Blueprint gaps did not recognize Phase 54.2 as already built.")


def main() -> int:
    verify_models_and_registration()

    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")
    verify_router_ui_docs_registration()

    post("/api/reference/seed", {}, OWNER_HEADERS)
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("Smoke requires at least one seeded agency.")
    agency_id = agencies[0]["id"]
    other_agency_id = ensure_second_agency(agencies)

    verify_health_readiness()
    agent_user_id, _ = verify_queue_lifecycle(agency_id, other_agency_id)
    verify_source_synchronization(agency_id, agent_user_id)
    verify_blueprint_registration()
    verify_health_readiness()

    service_py = (ROOT / "backend/services/agent_work_queue_service.py").read_text(encoding="utf-8")
    for marker in [
        "idempotent_generation",
        "request_task_compatibility_mapping",
        "workflow_event_integration",
        "platform_governance_does_not_silently_act_as_agency_staff",
        "client_facing_context_hidden",
    ]:
        if marker not in service_py:
            raise AssertionError(f"Agent work queue service missing safety/source marker: {marker}")

    print("Agent work queue and assignment foundation smoke passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Agent work queue and assignment foundation smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
