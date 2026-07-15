#!/usr/bin/env python3
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import AGENCY_OWNED_COLLECTIONS
from models import (
    OperationalBusinessCalendar,
    OperationalBusinessCalendarCreate,
    OperationalDeadline,
    OperationalDeadlineCreate,
    OperationalSlaEvent,
    OperationalSlaPolicy,
    OperationalSlaPolicyCreate,
)
from services.operational_sla_deadline_service import (
    BREACH_STATES,
    BUSINESS_HOURS_BEHAVIORS,
    DEADLINE_STATUSES,
    DEADLINE_TYPES,
    DEFAULT_SLA_POLICIES,
    OPERATIONAL_BUSINESS_CALENDARS_COLLECTION,
    OPERATIONAL_DEADLINES_COLLECTION,
    OPERATIONAL_SLA_EVENTS_COLLECTION,
    OPERATIONAL_SLA_POLICIES_COLLECTION,
    PHASE_LABEL,
    SLA_DURATION_UNITS,
    SLA_EVENT_TYPES,
    SLA_POLICY_SCOPES,
    SLA_POLICY_STATUSES,
)
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, request


EXPECTED_PHASE = "phase_56_3_journey_comparison_client_presentation_foundation"
ROOT = Path(__file__).resolve().parents[2]
AGENCY_AGENT_HEADERS = {"X-Demo-User-Email": "agency.agent@aeroassist.dev"}


def run_ref(prefix: str) -> str:
    return f"{prefix}-{int(time.time() * 1000)}"


def utc_iso(delta: timedelta | None = None) -> str:
    value = datetime.now(timezone.utc) + (delta or timedelta())
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_dt(value: str) -> datetime:
    text = str(value)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


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
        "sla_operational_deadline_engine_foundation",
        "deadline_calculation_enabled",
        "business_calendar_calculation_enabled",
        "pause_resume_metadata_enabled",
        "extension_audit_enabled",
        "manual_extensions_preserved",
        "work_queue_integration_enabled",
        "workflow_event_integration_enabled",
        "timeline_history_integration_enabled",
        "agency_isolation_enforced",
        "provider_integrations_disabled",
        "external_api_calls_disabled",
        "ai_disabled",
        "background_workers_disabled",
        "schedulers_disabled",
        "automatic_execution_disabled",
        "automation_disabled",
        "enforcement_disabled",
        "human_authority_final",
    ]:
        if payload.get(flag) is not True:
            raise AssertionError(f"Payload missing SLA safety flag {flag}: {payload}")


def ensure_second_agency(existing_agencies: list[dict]) -> str:
    if len(existing_agencies) > 1:
        return existing_agencies[1]["id"]
    slug = run_ref("sla-smoke-agency").lower()
    created = post(
        "/api/agencies",
        {
            "name": "SLA Smoke Isolation Agency",
            "slug": slug,
            "legal_name": "SLA Smoke Isolation Agency Ltd",
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


def create_manual_work_item(agency_id: str, source_entity_id: str) -> dict:
    response = post(
        f"/api/agencies/{agency_id}/work-queue/work-items",
        {
            "work_item_type": "new_request_triage",
            "source_entity_type": "request",
            "source_entity_id": source_entity_id,
            "title": "SLA linked request response",
            "summary": "Manual queue item used by the SLA smoke test.",
            "priority": "urgent",
            "severity": "high",
            "queue_code": "unassigned",
        },
        AGENCY_AGENT_HEADERS,
        201,
    )
    return response["work_item"]


def verify_models_and_registration() -> None:
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Service phase label mismatch: {PHASE_LABEL}")
    for collection in [
        OPERATIONAL_SLA_POLICIES_COLLECTION,
        OPERATIONAL_DEADLINES_COLLECTION,
        OPERATIONAL_SLA_EVENTS_COLLECTION,
        OPERATIONAL_BUSINESS_CALENDARS_COLLECTION,
    ]:
        if collection not in AGENCY_OWNED_COLLECTIONS:
            raise AssertionError(f"{collection} is not registered as agency-owned metadata.")
    for value in ["platform", "agency"]:
        if value not in SLA_POLICY_SCOPES:
            raise AssertionError(f"Missing SLA policy scope: {value}")
    for value in ["draft", "active", "archived"]:
        if value not in SLA_POLICY_STATUSES:
            raise AssertionError(f"Missing SLA policy status: {value}")
    for value in ["minutes", "hours", "days"]:
        if value not in SLA_DURATION_UNITS:
            raise AssertionError(f"Missing SLA duration unit: {value}")
    for value in ["calendar_hours", "business_hours"]:
        if value not in BUSINESS_HOURS_BEHAVIORS:
            raise AssertionError(f"Missing business-hours behavior: {value}")
    for value in ["open", "due_soon", "overdue", "paused", "extended", "completed", "waived"]:
        if value not in DEADLINE_STATUSES:
            raise AssertionError(f"Missing deadline status: {value}")
    for value in ["not_breached", "due_soon", "breached", "paused", "completed", "waived"]:
        if value not in BREACH_STATES:
            raise AssertionError(f"Missing breach state: {value}")
    for value in ["started", "paused", "resumed", "warning", "breached", "extended", "completed", "waived", "recalculated"]:
        if value not in SLA_EVENT_TYPES:
            raise AssertionError(f"Missing SLA event type: {value}")
    for value in ["request_response_sla", "offer_preparation_deadline", "ticketing_deadline", "medif_document_deadline", "disruption_response_deadline", "claim_refund_change_deadline"]:
        if value not in DEADLINE_TYPES:
            raise AssertionError(f"Missing deadline type: {value}")
    if len(DEFAULT_SLA_POLICIES) < 12:
        raise AssertionError("Expected default SLA policies for the operational deadline families.")

    due_at = datetime(2026, 7, 14, 11, 0, tzinfo=timezone.utc)
    calendar = OperationalBusinessCalendar(calendar_code="smoke_calendar", name="Smoke Calendar")
    policy = OperationalSlaPolicy(
        policy_code="smoke_policy",
        name="Smoke Policy",
        entity_type="request",
        deadline_type="request_response_sla",
    )
    deadline = OperationalDeadline(
        agency_id="agency-smoke",
        deadline_reference="SLA-SMOKE",
        source_entity_type="request",
        source_entity_id="request-smoke",
        deadline_type="request_response_sla",
        original_due_at=due_at,
        calculated_due_at=due_at,
        due_at=due_at,
        explanation="Smoke explanation.",
    )
    event = OperationalSlaEvent(agency_id="agency-smoke", deadline_id=deadline.id, event_type="started")
    policy_create = OperationalSlaPolicyCreate(name="Create Smoke", entity_type="request", deadline_type="request_response_sla")
    calendar_create = OperationalBusinessCalendarCreate(name="Create Smoke Calendar")
    deadline_create = OperationalDeadlineCreate(source_entity_type="request", source_entity_id="request-create", deadline_type="request_response_sla")
    for record in [calendar, policy, deadline, event]:
        dumped = record.model_dump(mode="json")
        if dumped.get("metadata_only") is not True or dumped.get("sla_operational_deadline_engine_foundation") is not True:
            raise AssertionError(f"SLA model lost metadata-only flags: {dumped}")
    if policy_create.deadline_type != "request_response_sla" or calendar_create.timezone != "UTC" or deadline_create.deadline_type != "request_response_sla":
        raise AssertionError("SLA create models did not preserve expected fields.")

    database_py = (ROOT / "backend/database.py").read_text(encoding="utf-8")
    for marker in [
        "operational_sla_policies_agency_code_lookup",
        "operational_deadlines_agency_due_at_lookup",
        "operational_deadlines_work_item_lookup",
        "operational_sla_events_deadline_history_lookup",
        "operational_business_calendars_agency_code_lookup",
    ]:
        if marker not in database_py:
            raise AssertionError(f"Database index registration missing {marker}.")


def verify_router_ui_docs_registration() -> None:
    openapi = get("/openapi.json", OWNER_HEADERS)
    paths = openapi.get("paths") or {}
    for path, method in [
        ("/api/platform/sla-policies", "get"),
        ("/api/platform/sla-policies/summary", "get"),
        ("/api/platform/sla-policies/policies", "get"),
        ("/api/platform/sla-policies/policies", "post"),
        ("/api/platform/sla-policies/policies/{policy_id}", "put"),
        ("/api/platform/sla-policies/business-calendars", "get"),
        ("/api/platform/sla-policies/business-calendars", "post"),
        ("/api/platform/sla-policies/business-calendars/{calendar_id}", "put"),
        ("/api/platform/sla-policies/deadlines", "get"),
        ("/api/platform/sla-policies/deadlines", "post"),
        ("/api/platform/sla-policies/deadlines/monitor", "post"),
        ("/api/platform/sla-policies/deadlines/{deadline_id}", "get"),
        ("/api/platform/sla-policies/deadlines/{deadline_id}/events", "get"),
        ("/api/platform/sla-policies/deadlines/{deadline_id}/pause", "post"),
        ("/api/platform/sla-policies/deadlines/{deadline_id}/resume", "post"),
        ("/api/platform/sla-policies/deadlines/{deadline_id}/extend", "post"),
        ("/api/platform/sla-policies/deadlines/{deadline_id}/complete", "post"),
        ("/api/platform/sla-policies/deadlines/{deadline_id}/waive", "post"),
        ("/api/platform/sla-policies/deadlines/{deadline_id}/recalculate", "post"),
        ("/api/agencies/{agency_id}/deadlines", "get"),
        ("/api/agencies/{agency_id}/deadlines/summary", "get"),
        ("/api/agencies/{agency_id}/deadlines/policies", "get"),
        ("/api/agencies/{agency_id}/deadlines/business-calendars", "get"),
        ("/api/agencies/{agency_id}/deadlines/items", "get"),
        ("/api/agencies/{agency_id}/deadlines/items", "post"),
        ("/api/agencies/{agency_id}/deadlines/monitor", "post"),
        ("/api/agencies/{agency_id}/deadlines/{deadline_id}", "get"),
        ("/api/agencies/{agency_id}/deadlines/{deadline_id}/events", "get"),
        ("/api/agencies/{agency_id}/deadlines/{deadline_id}/pause", "post"),
        ("/api/agencies/{agency_id}/deadlines/{deadline_id}/resume", "post"),
        ("/api/agencies/{agency_id}/deadlines/{deadline_id}/extend", "post"),
        ("/api/agencies/{agency_id}/deadlines/{deadline_id}/complete", "post"),
        ("/api/agencies/{agency_id}/deadlines/{deadline_id}/waive", "post"),
        ("/api/agencies/{agency_id}/deadlines/{deadline_id}/recalculate", "post"),
    ]:
        assert_openapi_path(paths, path, method)
    for path in paths:
        lowered = path.lower()
        if lowered.startswith("/api/admin") or lowered.startswith("/api/agent"):
            raise AssertionError(f"Old API route root must not be registered: {path}")

    for path, text in [
        (ROOT / "frontend/src/App.jsx", "/platform/sla-policies"),
        (ROOT / "frontend/src/App.jsx", "/agency/deadlines"),
        (ROOT / "frontend/src/pages/platform/SlaPoliciesPage.jsx", "No automation"),
        (ROOT / "frontend/src/pages/agency/DeadlinesPage.jsx", "Extension due date/time"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "SLA Policies"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Deadlines"),
        (ROOT / "backend/services/saas_subscription_service.py", "deadlines"),
        (ROOT / "backend/services/blueprint_adoption_service.py", "SLA and Operational Deadline Engine"),
        (ROOT / "docs/architecture/sla-operational-deadline-engine-foundation.md", "Manual extensions are preserved"),
        (ROOT / "docs/architecture/current-model-inventory.md", "operational_sla_policies"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "/platform/sla-policies"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "SLA and Operational Deadline Engine"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "operational_business_calendars"),
        (ROOT / "docs/architecture/passenger-service-operations-principle.md", "SLA and Operational Deadline Engine"),
        (ROOT / "docs/architecture/foundations/GLOSSARY.md", "Operational SLA Policy"),
        (ROOT / "BUILD_PHASES.md", "Implemented Phase 54.3"),
        (ROOT / "README.md", "SLA and Operational Deadline Engine Foundation"),
    ]:
        require_text(path, text)
    for path in [
        ROOT / "backend/services/operational_sla_deadline_service.py",
        ROOT / "backend/routers/platform_operational_sla_deadlines.py",
        ROOT / "backend/routers/agency_operational_sla_deadlines.py",
        ROOT / "frontend/src/App.jsx",
    ]:
        reject_text(path, "/admin/")
        reject_text(path, "/agent/")
    service_text = (ROOT / "backend/services/operational_sla_deadline_service.py").read_text(encoding="utf-8").lower()
    for forbidden in ["requests.get", "requests.post", "httpx.", "stripe", "openai", "send_email", "send_sms"]:
        if forbidden in service_text:
            raise AssertionError(f"SLA service contains forbidden execution/provider semantic: {forbidden}")


def verify_health_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")
    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("sla_operational_deadline_engine_foundation") or {}
    for key in [
        "sla_operational_deadline_engine_enabled",
        "operational_sla_policies_collection_enabled",
        "operational_deadlines_collection_enabled",
        "operational_sla_events_collection_enabled",
        "operational_business_calendars_collection_enabled",
        "deadline_calculation_enabled",
        "business_calendar_calculation_enabled",
        "pause_resume_metadata_enabled",
        "extension_audit_enabled",
        "manual_extensions_preserved",
        "due_soon_detection_enabled",
        "breach_detection_enabled",
        "work_queue_integration_enabled",
        "workflow_event_integration_enabled",
        "timeline_history_integration_enabled",
        "agency_isolation_enforced",
        "metadata_only",
        "provider_integrations_disabled",
        "external_api_calls_disabled",
        "ai_disabled",
        "background_workers_disabled",
        "schedulers_disabled",
        "automatic_execution_disabled",
        "automation_disabled",
        "enforcement_disabled",
        "human_authority_final",
    ]:
        if section.get(key) is not True:
            raise AssertionError(f"Readiness missing SLA foundation flag: {key}")
    for count_key in [
        "operational_sla_policy_count",
        "operational_deadline_count",
        "operational_sla_event_count",
        "operational_business_calendar_count",
        "operational_deadline_status_counts",
        "operational_deadline_breach_counts",
        "operational_deadline_type_counts",
        "operational_sla_event_type_counts",
    ]:
        if count_key not in section:
            raise AssertionError(f"Readiness missing SLA count: {count_key}")
    if "request_response_sla" not in section.get("deadline_types", []):
        raise AssertionError("Readiness missing deadline type list.")
    if section.get("readiness_required") is not False:
        raise AssertionError("SLA deadline foundation should not be deployment-readiness required.")
    for previous_section in ["operational_workflow_orchestration_foundation", "agent_work_queue_assignment_foundation"]:
        if not readiness.get(previous_section):
            raise AssertionError(f"Readiness missing regression dependency section {previous_section}.")


def verify_deadline_lifecycle(agency_id: str, other_agency_id: str) -> None:
    request("GET", "/api/platform/sla-policies", None, AGENCY_AGENT_HEADERS, expect=403)

    calendar = post(
        "/api/platform/sla-policies/business-calendars",
        {
            "agency_id": agency_id,
            "calendar_code": run_ref("sla_calendar").lower().replace("-", "_"),
            "name": "SLA Smoke Business Calendar",
            "timezone": "UTC",
            "working_days": [0, 1, 2, 3, 4],
            "working_hours_json": {"start": "09:00", "end": "17:00"},
            "holidays": [],
            "exceptions": [],
            "status": "active",
        },
        OWNER_HEADERS,
        201,
    )["business_calendar"]

    policy = post(
        "/api/platform/sla-policies/policies",
        {
            "agency_id": agency_id,
            "scope": "agency",
            "policy_code": run_ref("request_response_sla").lower().replace("-", "_"),
            "name": "Request response smoke SLA",
            "entity_type": "request",
            "work_item_type": "new_request_triage",
            "deadline_type": "request_response_sla",
            "priority": "urgent",
            "duration_value": 4,
            "duration_unit": "hours",
            "business_hours_behavior": "business_hours",
            "calendar_id": calendar["id"],
            "pause_conditions": ["waiting_client", "waiting_airline_supplier"],
            "escalation_thresholds_json": [{"minutes_before_due": 60, "suggestion": "Escalate to queue owner for smoke review."}],
            "status": "active",
        },
        OWNER_HEADERS,
        201,
    )["policy"]
    if policy.get("calendar_id") != calendar["id"]:
        raise AssertionError("SLA policy did not preserve business calendar link.")

    source_entity_id = run_ref("sla-request")
    work_item = create_manual_work_item(agency_id, source_entity_id)
    created = post(
        f"/api/agencies/{agency_id}/deadlines/items",
        {
            "source_entity_type": "request",
            "source_entity_id": source_entity_id,
            "work_item_id": work_item["id"],
            "deadline_type": "request_response_sla",
            "priority": "urgent",
            "started_at": "2026-07-13T15:00:00Z",
            "source_snapshot_json": {"source": "sla_smoke"},
        },
        AGENCY_AGENT_HEADERS,
        201,
    )
    assert_safety_flags(created)
    deadline = created["deadline"]
    calculated = parse_dt(deadline["calculated_due_at"])
    if calculated != datetime(2026, 7, 14, 11, 0, tzinfo=timezone.utc):
        raise AssertionError(f"Business-hours calculation was not deterministic: {deadline['calculated_due_at']}")
    if "business hours" not in (deadline.get("explanation") or ""):
        raise AssertionError("Deadline explanation did not mention business-hours calculation.")

    linked_item = get(f"/api/agencies/{agency_id}/work-queue/work-items/{work_item['id']}", AGENCY_AGENT_HEADERS)["work_item"]
    if not linked_item.get("due_at") or linked_item.get("sla_status") not in {"on_track", "due_soon", "overdue", "breached", "paused", "completed"}:
        raise AssertionError(f"Work queue integration did not update linked item SLA metadata: {linked_item}")
    if (linked_item.get("internal_context_json") or {}).get("sla_deadline_id") != deadline["id"]:
        raise AssertionError("Work queue item missing SLA deadline context.")

    paused = post(f"/api/agencies/{agency_id}/deadlines/{deadline['id']}/pause", {"reason": "Waiting for airline response."}, AGENCY_AGENT_HEADERS)["deadline"]
    if paused.get("status") != "paused" or paused.get("breach_state") != "paused":
        raise AssertionError(f"Pause action failed: {paused}")
    resumed = post(f"/api/agencies/{agency_id}/deadlines/{deadline['id']}/resume", {"reason": "Airline response received."}, AGENCY_AGENT_HEADERS)["deadline"]
    if resumed.get("status") == "paused" or resumed.get("paused_at") is not None:
        raise AssertionError(f"Resume action failed: {resumed}")

    extension_due = utc_iso(timedelta(days=4))
    extended = post(
        f"/api/agencies/{agency_id}/deadlines/{deadline['id']}/extend",
        {"reason": "Human-approved extension for smoke.", "due_at": extension_due},
        AGENCY_AGENT_HEADERS,
    )["deadline"]
    if extended.get("manual_extension_approved") is not True:
        raise AssertionError("Manual extension metadata was not recorded.")
    if parse_dt(extended["original_due_at"]) != datetime(2026, 7, 14, 11, 0, tzinfo=timezone.utc):
        raise AssertionError("Original due date was not preserved after extension.")
    recalculated = post(
        f"/api/agencies/{agency_id}/deadlines/{deadline['id']}/recalculate",
        {"reason": "Do not override manual extension."},
        AGENCY_AGENT_HEADERS,
    )
    if recalculated.get("manual_extension_preserved") is not True:
        raise AssertionError("Manual extension was not preserved by safe recalculation.")

    events = get(f"/api/agencies/{agency_id}/deadlines/{deadline['id']}/events", AGENCY_AGENT_HEADERS).get("events") or []
    event_types = {event.get("event_type") for event in events}
    for event_type in ["started", "paused", "resumed", "extended", "recalculated"]:
        if event_type not in event_types:
            raise AssertionError(f"SLA event history missing {event_type}: {event_types}")

    breached = post(
        f"/api/agencies/{agency_id}/deadlines/items",
        {
            "source_entity_type": "request_task",
            "source_entity_id": run_ref("breach-task"),
            "deadline_type": "task_deadline",
            "priority": "high",
            "started_at": utc_iso(timedelta(days=-2)),
            "due_at": utc_iso(timedelta(days=-1)),
        },
        AGENCY_AGENT_HEADERS,
        201,
    )["deadline"]
    if breached.get("status") != "overdue" or breached.get("breach_state") != "breached":
        raise AssertionError(f"Breach detection failed: {breached}")
    monitor = post(f"/api/agencies/{agency_id}/deadlines/monitor", {}, AGENCY_AGENT_HEADERS)
    assert_safety_flags(monitor)

    platform_dashboard = get(f"/api/platform/sla-policies?{urlencode({'agency_id': agency_id, 'include_completed': 'true'})}", OWNER_HEADERS)
    assert_safety_flags(platform_dashboard)
    if platform_dashboard.get("summary", {}).get("overdue_count", 0) < 1:
        raise AssertionError("Platform SLA dashboard did not expose overdue metadata.")

    agency_dashboard = get(f"/api/agencies/{agency_id}/deadlines?{urlencode({'include_completed': 'true'})}", AGENCY_AGENT_HEADERS)
    assert_safety_flags(agency_dashboard)
    if not agency_dashboard.get("policies") or not agency_dashboard.get("business_calendars"):
        raise AssertionError("Agency deadline dashboard missing policy/calendar metadata.")

    other_deadline = post(
        f"/api/agencies/{other_agency_id}/deadlines/items",
        {
            "source_entity_type": "request",
            "source_entity_id": run_ref("other-agency-request"),
            "deadline_type": "request_response_sla",
            "priority": "normal",
            "started_at": utc_iso(),
        },
        OWNER_HEADERS,
        201,
    )["deadline"]
    request("GET", f"/api/agencies/{other_agency_id}/deadlines/{other_deadline['id']}", None, AGENCY_AGENT_HEADERS, expect=403)


def main() -> int:
    verify_models_and_registration()
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected phase label: {health.get('phase')}")
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("No demo agencies available for SLA smoke.")
    agency_id = agencies[0]["id"]
    other_agency_id = ensure_second_agency(agencies)
    verify_router_ui_docs_registration()
    verify_health_readiness()
    verify_deadline_lifecycle(agency_id, other_agency_id)
    verify_health_readiness()
    print("Phase 54.3 SLA and operational deadline engine foundation smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
