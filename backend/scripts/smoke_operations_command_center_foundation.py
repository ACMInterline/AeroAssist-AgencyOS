#!/usr/bin/env python3
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parent))

from database import AGENCY_OWNED_COLLECTIONS
from services.operations_command_center_service import PHASE_LABEL, VIEW_TYPES, OperationsCommandCenterService
from smoke_booking_pnr_foundation import OWNER_HEADERS, assert_openapi_path, get, post, request


EXPECTED_PHASE = "phase_56_0_canonical_journey_itinerary_representation_foundation"
ROOT = Path(__file__).resolve().parents[2]
AGENCY_AGENT_HEADERS = {"X-Demo-User-Email": "agency.agent@aeroassist.dev"}


def ref(prefix: str) -> str:
    return f"{prefix}-{int(time.time() * 1000)}"


def require_text(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8")
    if text not in content:
        raise AssertionError(f"{path.relative_to(ROOT)} missing expected text: {text}")


def reject_text(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8").lower()
    if text.lower() in content:
        raise AssertionError(f"{path.relative_to(ROOT)} contains rejected text: {text}")


def assert_flags(payload: dict) -> None:
    for flag in [
        "metadata_only",
        "operations_command_center_foundation",
        "aggregation_only",
        "duplicate_operational_data_disabled",
        "read_only_dashboard",
        "uncontrolled_drag_and_drop_disabled",
        "kanban_moves_require_workflow_transitions",
        "kanban_guard_enforcement_enabled",
        "provider_execution_disabled",
        "external_api_calls_disabled",
        "background_workers_disabled",
        "ai_disabled",
        "status_mutation_disabled",
        "human_authority_final",
    ]:
        if payload.get(flag) is not True:
            raise AssertionError(f"Missing command center safety flag {flag}: {payload}")


def assert_no_forbidden_execution_text() -> None:
    service_path = ROOT / "backend/services/operations_command_center_service.py"
    for forbidden in [
        "requests.get(",
        "requests.post(",
        "httpx.",
        "urllib.request",
        "openai",
        "stripe",
        "send_email",
        "send_sms",
        "BackgroundTasks",
        "asyncio.create_task",
        ".insert_one(",
        ".update_one(",
        ".delete_one(",
        ".delete_many(",
    ]:
        reject_text(service_path, forbidden)


def verify_static_contracts() -> None:
    if PHASE_LABEL != EXPECTED_PHASE:
        raise AssertionError(f"Command center service PHASE_LABEL mismatch: {PHASE_LABEL}")
    for view in ["dashboard", "queue", "kanban", "calendar", "timeline", "exceptions", "workload"]:
        if view not in VIEW_TYPES:
            raise AssertionError(f"Missing command-center view type: {view}")
    if any(collection == "operations_command_center" or collection == "operations_command_centers" for collection in AGENCY_OWNED_COLLECTIONS):
        raise AssertionError("Command center must not register a duplicate operational collection.")
    flags = OperationsCommandCenterService(None).safety_flags()
    assert_flags(flags)
    assert_no_forbidden_execution_text()
    for source_collection in [
        "operational_work_items",
        "operational_deadlines",
        "operational_workflow_instances",
        "operational_workflow_events",
        "request_intakes",
        "offer_workspaces_v2",
        "offer_booking_handoffs",
        "booking_workspaces",
        "ticket_workspaces",
        "emd_workspaces",
        "ssr_osi_workspaces",
        "document_workspaces",
        "trip_workspaces",
        "flight_workspaces",
        "after_sales_cases",
        "operational_intelligence_cases",
        "pilot_readiness_issues",
        "request_tasks",
    ]:
        require_text(ROOT / "backend/services/operations_command_center_service.py", source_collection)


def verify_routes_and_docs(paths: dict) -> None:
    for path in paths:
        if path.startswith(("/admin", "/agent", "/api/admin", "/api/agent")):
            raise AssertionError(f"Non-canonical API route introduced: {path}")
    expected = {
        "/api/platform/operations-governance": {"get"},
        "/api/platform/operations-governance/summary": {"get"},
        "/api/platform/operations-governance/feed": {"get"},
        "/api/platform/operations-governance/calendar": {"get"},
        "/api/platform/operations-governance/kanban": {"get"},
        "/api/platform/operations-governance/workload": {"get"},
        "/api/agencies/{agency_id}/operations-command-center": {"get"},
        "/api/agencies/{agency_id}/operations-command-center/summary": {"get"},
        "/api/agencies/{agency_id}/operations-command-center/feed": {"get"},
        "/api/agencies/{agency_id}/operations-command-center/calendar": {"get"},
        "/api/agencies/{agency_id}/operations-command-center/kanban": {"get"},
        "/api/agencies/{agency_id}/operations-command-center/workload": {"get"},
    }
    for path, methods in expected.items():
        for method in methods:
            assert_openapi_path(paths, path, method)
        disallowed = set(paths.get(path, {}).keys()) & {"post", "put", "patch", "delete"}
        if disallowed:
            raise AssertionError(f"Command center route should be read-only: {path} {disallowed}")
    if "/api/agencies/{agency_id}/operations-command-center/kanban/move" in paths:
        raise AssertionError("Command center must not expose uncontrolled kanban move endpoints.")
    for path, text in [
        (ROOT / "frontend/src/App.jsx", "/agency/operations-command-center"),
        (ROOT / "frontend/src/App.jsx", "/platform/operations-governance"),
        (ROOT / "frontend/src/lib/moduleCatalog.js", "Operations Command Center"),
        (ROOT / "frontend/src/pages/agency/OperationsCommandCenterPage.jsx", "uncontrolled drag-and-drop is disabled"),
        (ROOT / "frontend/src/pages/platform/OperationsGovernancePage.jsx", "Read-only platform command center"),
        (ROOT / "backend/services/saas_subscription_service.py", "operations_command_center"),
        (ROOT / "docs/architecture/operations-command-center-foundation.md", "Operations Command Center Foundation"),
        (ROOT / "README.md", "Operations Command Center Foundation"),
        (ROOT / "BUILD_PHASES.md", "Phase 54.8: Operations command center foundation"),
        (ROOT / "docs/architecture/current-model-inventory.md", "Operations Command Center aggregate read model"),
        (ROOT / "docs/architecture/canonical-route-policy.md", "Phase 54.8 adds operations command center APIs"),
        (ROOT / "docs/architecture/agencyos-blueprint-alignment-gap-map.md", "Operations command center"),
        (ROOT / "docs/architecture/supplementary-blueprint-adoption-map.md", "Operations Command Center"),
        (ROOT / "docs/architecture/passenger-service-operations-principle.md", "Operations Command Center"),
        (ROOT / "backend/services/blueprint_adoption_service.py", "Operations Command Center"),
    ]:
        require_text(path, text)


def verify_readiness() -> None:
    health = get("/api/health")
    if health.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected health phase: {health.get('phase')}")
    readiness = get("/api/readiness")
    if readiness.get("phase") != EXPECTED_PHASE:
        raise AssertionError(f"Unexpected readiness phase: {readiness.get('phase')}")
    section = readiness.get("operations_command_center_foundation") or {}
    for flag in [
        "operations_command_center_enabled",
        "agency_operations_command_center_enabled",
        "platform_operations_governance_enabled",
        "aggregation_only",
        "duplicate_operational_data_disabled",
        "current_operational_workload_enabled",
        "unassigned_work_enabled",
        "overdue_due_soon_enabled",
        "critical_blockers_enabled",
        "requests_awaiting_triage_enabled",
        "offers_awaiting_action_enabled",
        "accepted_offers_awaiting_booking_enabled",
        "bookings_awaiting_ticketing_enabled",
        "service_approvals_documents_enabled",
        "departure_horizon_enabled",
        "disrupted_trips_enabled",
        "after_sales_cases_enabled",
        "knowledge_manual_review_enabled",
        "payment_invoice_blockers_enabled",
        "pilot_readiness_issues_enabled",
        "team_workload_enabled",
        "dashboard_view_enabled",
        "queue_view_enabled",
        "kanban_view_enabled",
        "calendar_view_enabled",
        "timeline_view_enabled",
        "exception_list_enabled",
        "agent_team_workload_view_enabled",
        "urgency_ranked_feed_enabled",
        "calendar_generation_enabled",
        "kanban_lanes_from_workflow_state_enabled",
        "kanban_moves_require_workflow_transitions",
        "kanban_guard_enforcement_enabled",
        "uncontrolled_drag_and_drop_disabled",
        "safe_action_links_enabled",
        "queue_integration_enabled",
        "sla_integration_enabled",
        "workflow_integration_enabled",
        "after_sales_integration_enabled",
        "agency_isolation_enforced",
        "metadata_only",
        "read_only_dashboard",
        "provider_execution_disabled",
        "external_api_calls_disabled",
        "background_workers_disabled",
        "ai_disabled",
        "status_mutation_disabled",
        "human_authority_final",
    ]:
        if section.get(flag) is not True:
            raise AssertionError(f"Readiness missing command center flag {flag}: {section}")
    for key in ["view_types", "kpis", "feed_count", "calendar_event_count", "kanban_lane_count", "workload_bucket_count", "exception_count"]:
        if key not in section:
            raise AssertionError(f"Readiness missing command-center key {key}: {section}")


def agency_ids() -> list[str]:
    post("/api/reference/seed", {}, OWNER_HEADERS)
    agencies = get("/api/agencies", OWNER_HEADERS).get("items") or []
    if not agencies:
        raise AssertionError("No agencies available after seed.")
    return [agency["id"] for agency in agencies]


def after_sales_payload() -> dict:
    token = ref("OCC")
    return {
        "case_type": "disruption_irregular_operation",
        "case_priority": "critical",
        "case_title": f"Command center disruption smoke {token}",
        "case_summary": "Metadata-only case used to verify command-center aggregation.",
        "trip_workspace_id": f"trip-{token}",
        "booking_workspace_id": f"booking-{token}",
        "ticket_workspace_ids": [f"ticket-{token}"],
        "emd_workspace_ids": [f"emd-{token}"],
        "passenger_workspace_ids": [f"passenger-{token}"],
        "document_workspace_ids": [f"document-{token}"],
        "ssr_osi_workspace_ids": [f"ssr-{token}"],
        "affected_segment_refs": ["seg-1"],
        "supplier_communication_required": True,
        "client_approval_required": True,
        "generated_advice_json": {"advice_status": "draft_metadata", "no_sending": True},
        "internal_message_json": {"summary": "Internal command center smoke note."},
        "client_message_json": {"summary": "Client-facing draft metadata only."},
        "financial_estimate_json": {"estimate_status": "placeholder", "no_commitment": True},
        "idempotency_key": f"smoke:operations-command-center:{token}",
    }


def assert_dashboard_shape(payload: dict) -> None:
    assert_flags(payload)
    for view in ["dashboard", "queue", "kanban", "calendar", "timeline", "exceptions", "workload"]:
        if view not in payload:
            raise AssertionError(f"Command center missing {view}: {payload}")
    for kpi in [
        "current_operational_workload",
        "unassigned_work",
        "due_soon",
        "overdue",
        "critical_blockers",
        "requests_awaiting_triage",
        "offers_awaiting_action",
        "accepted_offers_awaiting_booking",
        "bookings_awaiting_ticketing",
        "service_approvals_documents",
        "departures_next_24_hours",
        "departures_next_48_hours",
        "departures_next_72_hours",
        "disrupted_trips",
        "after_sales_cases",
        "unresolved_knowledge_manual_review",
        "payment_invoice_blockers",
        "pilot_readiness_issues",
        "team_workload_units",
    ]:
        if kpi not in (payload.get("kpis") or {}):
            raise AssertionError(f"Command center missing KPI {kpi}: {payload.get('kpis')}")
    if payload.get("kanban", {}).get("guard_enforcement") is not True:
        raise AssertionError(f"Kanban guard enforcement missing: {payload.get('kanban')}")
    if payload.get("kanban", {}).get("uncontrolled_drag_and_drop_disabled") is not True:
        raise AssertionError(f"Kanban drag-drop guard missing: {payload.get('kanban')}")


def verify_live_api(paths: dict) -> None:
    verify_routes_and_docs(paths)
    verify_readiness()
    primary_agency_id = agency_ids()[0]
    created = post(f"/api/agencies/{primary_agency_id}/after-sales", after_sales_payload(), AGENCY_AGENT_HEADERS, 201)
    case = created.get("case") or {}
    if not case.get("workflow_instance_id") or not case.get("work_item_ids") or not case.get("deadline_ids") or not case.get("timeline_entry_ids"):
        raise AssertionError(f"After-sales seed did not produce workflow/queue/SLA/timeline metadata: {case}")

    agency_dashboard = get(f"/api/agencies/{primary_agency_id}/operations-command-center", AGENCY_AGENT_HEADERS)
    assert_dashboard_shape(agency_dashboard)
    if agency_dashboard.get("platform_read_only_governance") is not False:
        raise AssertionError(f"Agency command center should not be platform governance: {agency_dashboard}")
    if (agency_dashboard.get("kpis") or {}).get("after_sales_cases", 0) < 1:
        raise AssertionError(f"Agency command center did not aggregate after-sales cases: {agency_dashboard.get('kpis')}")
    if not agency_dashboard.get("queue"):
        raise AssertionError(f"Agency command center queue is empty after seeded work: {agency_dashboard}")
    if not (agency_dashboard.get("kanban", {}).get("lanes") or []):
        raise AssertionError(f"Agency command center kanban is empty after seeded workflow: {agency_dashboard.get('kanban')}")
    if not (agency_dashboard.get("calendar", {}).get("events") or []):
        raise AssertionError(f"Agency command center calendar is empty after seeded deadline: {agency_dashboard.get('calendar')}")
    if not (agency_dashboard.get("timeline", {}).get("events") or []):
        raise AssertionError(f"Agency command center timeline is empty after seeded workflow event: {agency_dashboard.get('timeline')}")
    first_lane = agency_dashboard["kanban"]["lanes"][0]
    first_card = first_lane["cards"][0]
    if first_card.get("guard_enforcement_required") is not True or not str(first_card.get("transition_route_required", "")).startswith("/agency/operational-workflows"):
        raise AssertionError(f"Agency kanban card did not require workflow guard route: {first_card}")

    for suffix, key in [
        ("summary", "summary"),
        ("feed", "items"),
        ("calendar", "events"),
        ("kanban", "lanes"),
        ("workload", "items"),
    ]:
        response = get(f"/api/agencies/{primary_agency_id}/operations-command-center/{suffix}", AGENCY_AGENT_HEADERS)
        assert_flags(response)
        if key not in response:
            raise AssertionError(f"Agency command center sub-endpoint missing {key}: {suffix} {response}")

    platform_dashboard = get(f"/api/platform/operations-governance?agency_id={primary_agency_id}", OWNER_HEADERS)
    assert_dashboard_shape(platform_dashboard)
    if platform_dashboard.get("platform_read_only_governance") is not True:
        raise AssertionError(f"Platform operations governance flag missing: {platform_dashboard}")
    platform_kanban = get(f"/api/platform/operations-governance/kanban?agency_id={primary_agency_id}", OWNER_HEADERS)
    if not platform_kanban.get("platform_read_only_governance") or not platform_kanban.get("guard_enforcement"):
        raise AssertionError(f"Platform kanban governance flags missing: {platform_kanban}")
    if platform_kanban.get("lanes"):
        card = platform_kanban["lanes"][0]["cards"][0]
        if not str(card.get("transition_route_required", "")).startswith("/platform/operational-workflows"):
            raise AssertionError(f"Platform kanban card should link to platform workflows: {card}")
    platform_summary = get("/api/platform/operations-governance/summary", OWNER_HEADERS)
    assert_flags(platform_summary)
    request("POST", "/api/platform/operations-governance", {}, OWNER_HEADERS, 405)
    request("POST", f"/api/agencies/{primary_agency_id}/operations-command-center", {}, AGENCY_AGENT_HEADERS, 405)
    request("GET", "/api/agencies/not-an-agency/operations-command-center", None, AGENCY_AGENT_HEADERS, 404)


def main() -> None:
    verify_static_contracts()
    paths = get("/openapi.json").get("paths", {})
    verify_live_api(paths)
    print("Phase 54.8 operations command center foundation smoke passed.")


if __name__ == "__main__":
    main()
