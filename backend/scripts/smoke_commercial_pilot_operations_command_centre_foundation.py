#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from build_phase import CURRENT_BUILD_PHASE
from scripts.phase_assertions import application_phase_is_at_least
from database import AGENCY_OWNED_COLLECTIONS, Database
from fastapi import HTTPException
from routers.agency_operations_command_center import require_read
from services.commercial_pilot_operations_command_centre_service import (
    PHASE_LABEL,
    CommercialPilotOperationsCommandCentreService,
    commercial_pilot_operations_command_centre_readiness_metadata,
)


NOW = datetime(2026, 7, 23, 9, 0, tzinfo=timezone.utc)
MINIMUM_PHASE = PHASE_LABEL


async def insert(database: Database, collection: str, **document) -> None:
    document.setdefault("created_at", NOW - timedelta(hours=2))
    document.setdefault("updated_at", NOW - timedelta(hours=1))
    await database.collection(collection).insert_one(document)


async def verify_service() -> None:
    database = Database()
    service = CommercialPilotOperationsCommandCentreService(database)
    service._now = lambda: NOW
    agency_id = "agency-operations"
    other_agency_id = "agency-other"
    user = {"id": "user-agent", "email": "agent@example.com", "full_name": "Mila Agent"}
    membership = {"agency_id": agency_id, "user_id": user["id"], "agency_role": "agency_agent", "status": "active", "team_codes": ["sofia"]}

    await insert(database, "agencies", id=agency_id, name="Skybridge Travel", timezone="Europe/Sofia")
    await insert(database, "agencies", id=other_agency_id, name="Other Travel", timezone="UTC")
    await insert(database, "agency_staff_memberships", id="membership-agent", **membership)
    await insert(database, "platform_users", id=user["id"], full_name=user["full_name"], email=user["email"])
    resolved_membership = await require_read(database, agency_id, user)
    assert resolved_membership["agency_role"] == "agency_agent"
    try:
        await require_read(database, other_agency_id, user)
    except HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("Cross-agency command-centre read was allowed.")
    await insert(
        database,
        "agency_dashboard_preferences",
        id="preferences",
        agency_id=agency_id,
        preference_key="default",
        preferred_starting_view="my_work",
        visible_operations_sections=["my_work", "queues", "timeline", "alerts", "quick_actions", "recent_activity"],
        default_assignment_filter="my_work",
        default_urgency_filter="all",
    )
    await insert(database, "client_profiles", id="client-1", agency_id=agency_id, display_name="Alex Morgan")
    await insert(database, "passenger_profiles", id="passenger-1", agency_id=agency_id, display_name="Jamie Morgan")
    await insert(
        database,
        "travel_requests",
        id="request-1",
        agency_id=agency_id,
        client_id="client-1",
        primary_passenger_id="passenger-1",
        title="Sofia to Paris assistance request",
        status="new",
        requested_origin="SOF",
        requested_destination="CDG",
    )
    await insert(
        database,
        "operational_work_items",
        id="work-critical",
        agency_id=agency_id,
        work_item_code="WI-001",
        work_item_type="new_request_triage",
        source_entity_type="request",
        source_entity_id="request-1",
        title="Triage assistance request",
        summary="Review passenger assistance needs",
        status="open",
        priority="critical",
        severity="critical",
        queue_code="unassigned",
        assigned_user_id=user["id"],
        due_at=NOW - timedelta(hours=1),
        sla_status="overdue",
    )
    await insert(
        database,
        "operational_work_items",
        id="work-team",
        agency_id=agency_id,
        work_item_code="WI-002",
        work_item_type="waiting_airline",
        source_entity_type="request",
        source_entity_id="request-1",
        title="Follow up airline approval",
        status="waiting",
        priority="high",
        severity="high",
        queue_code="waiting_airline",
        assigned_team_code="sofia",
        due_at=NOW + timedelta(hours=2),
    )
    await insert(
        database,
        "operational_work_items",
        id="cross-tenant-work",
        agency_id=other_agency_id,
        work_item_code="WI-X",
        work_item_type="workflow_blocker",
        source_entity_type="request",
        source_entity_id="other-request",
        title="Other agency private work",
        status="open",
        priority="critical",
        severity="critical",
        queue_code="blocked",
    )
    await insert(
        database,
        "operational_deadlines",
        id="deadline-1",
        agency_id=agency_id,
        deadline_reference="Ticket deadline",
        deadline_type="ticketing_deadline",
        status="overdue",
        breach_state="breached",
        due_at=NOW - timedelta(hours=3),
        explanation="Ticketing review is overdue.",
    )
    await insert(
        database,
        "offer_workspaces_v2",
        id="offer-1",
        agency_id=agency_id,
        offer_reference="OFF-1",
        offer_title="Paris assistance offer",
        offer_status="awaiting_client",
        validity_date=NOW + timedelta(hours=24),
    )
    await insert(
        database,
        "ssr_osi_workspaces",
        id="service-1",
        agency_id=agency_id,
        workspace_status="pending",
        ssr_code="WCHC",
        approval_required=True,
        operational_notes="Airline approval pending.",
    )
    await insert(
        database,
        "document_deliveries",
        id="delivery-1",
        agency_id=agency_id,
        status="ready",
        document_title="Travel documents",
    )
    await insert(
        database,
        "request_tasks",
        id="task-1",
        agency_id=agency_id,
        request_id="request-1",
        title="Call passenger",
        status="open",
        due_at=NOW + timedelta(hours=1),
    )
    await insert(
        database,
        "operational_timelines",
        id="timeline-1",
        agency_id=agency_id,
        event_type="customer_contacted",
        summary="Passenger details reviewed",
        created_by="Mila Agent",
        travel_request_workspace_id="request-1",
        created_at=NOW - timedelta(minutes=30),
    )
    await insert(
        database,
        "audit_events",
        id="audit-1",
        agency_id=agency_id,
        event_type="request.updated",
        entity_type="request",
        entity_id="request-1",
        summary="Request priority updated",
        actor_user_id=user["id"],
        created_at=NOW - timedelta(minutes=15),
    )

    home = await service.agency_home(agency_id, user, membership, due_period="all")
    assert home["agency_id"] == agency_id and home["tenant_scoped"] is True
    assert home["generated_at"] == NOW.isoformat()
    assert home["user_context"]["can_update_work_items"] is True
    priority_ids = [item["id"] for item in home["priorities"]["items"]]
    assert priority_ids == ["work-critical", "work-team"], priority_ids
    assert "cross-tenant-work" not in str(home)
    critical = home["priorities"]["items"][0]
    assert critical["client"] == "Alex Morgan" and critical["passenger"] == "Jamie Morgan"
    assert critical["trip_or_route"] == "SOF to CDG"
    assert critical["actions"][0]["href"] == "/agency/requests/request-1"
    assert [action["key"] for action in critical["actions"]] == ["open", "reassign", "complete"]
    team = home["priorities"]["items"][1]
    assert "assign_self" in [action["key"] for action in team["actions"]]
    assert all(action.get("api_path", "").startswith(f"/api/agencies/{agency_id}/work-queue/") for action in team["actions"] if action.get("api_path"))

    queues = {item["key"]: item for item in home["queues"]}
    assert queues["new_requests"]["count"] >= 1
    assert queues["waiting_airline"]["count"] == 1
    assert queues["waiting_supplier"]["count"] == 0
    assert queues["special_services"]["count"] == 1
    assert queues["documents_to_send"]["count"] == 1
    assert queues["follow_ups"]["count"] == 1
    assert queues["overdue"]["count"] == 1
    assert home["timeline"]["events"] == sorted(home["timeline"]["events"], key=lambda item: (item["timestamp"], item["id"]))
    assert home["timeline"]["previous_date"] == "2026-07-22"
    assert home["timeline"]["next_date"] == "2026-07-24"
    alert_types = {item["alert_type"] for item in home["alerts"]}
    assert {"overdue_deadline", "offer_expiring", "unresolved_service", "document_delivery"}.issubset(alert_types)
    assert {item["key"] for item in home["quick_actions"]} == {"new_request", "new_offer", "new_booking", "new_passenger", "import_pnr", "open_tasks"}
    assert [item["id"] for item in home["recent_activity"]][:2] == ["audit:audit-1", "timeline:timeline-1"]
    assert home["preferences"]["legacy_defaults_applied"] is False
    assert home["result_limits"]["source_records_per_collection"] == 250
    assert home["provider_execution_disabled"] is True and home["automatic_execution_disabled"] is True

    assigned = await service.agency_home(agency_id, user, membership, assignee_id=user["id"], due_period="all")
    assert [item["id"] for item in assigned["priorities"]["items"]] == ["work-critical"]

    readonly = await service.agency_home(agency_id, user, {**membership, "agency_role": "agency_readonly"}, due_period="all")
    assert readonly["user_context"]["can_update_work_items"] is False
    assert all(action["key"] == "open" for item in readonly["priorities"]["items"] for action in item["actions"])
    assert {item["key"] for item in readonly["quick_actions"]} == {"open_tasks"}

    legacy = await service.agency_home(other_agency_id, {"id": "other-user", "full_name": "Other User"}, {"agency_role": "agency_agent", "status": "active"}, due_period="all")
    assert legacy["preferences"]["legacy_defaults_applied"] is True
    assert legacy["preferences"]["preferred_starting_view"] == "my_work"
    assert len(legacy["priorities"]["items"]) == 1

    await insert(database, "agencies", id="agency-empty", name="Empty Agency", timezone="UTC")
    empty = await service.agency_home("agency-empty", {"id": "empty-user", "full_name": "Empty User"}, {"agency_role": "agency_agent", "status": "active"}, due_period="all")
    assert empty["priorities"]["items"] == []
    assert all(queue["count"] == 0 for queue in empty["queues"])
    assert empty["alerts"] == [] and empty["recent_activity"] == []


def verify_registration() -> None:
    assert application_phase_is_at_least(CURRENT_BUILD_PHASE, MINIMUM_PHASE)
    metadata = commercial_pilot_operations_command_centre_readiness_metadata()
    for key in [
        "agency_operations_home_enabled",
        "existing_command_center_reused",
        "canonical_agency_home_route_enabled",
        "legacy_command_center_route_preserved",
        "bounded_tenant_aggregation_enabled",
        "deterministic_ordering_enabled",
        "agency_isolation_enforced",
        "existing_work_queue_actions_reused",
    ]:
        assert metadata[key] is True, key
    assert metadata["new_operational_collection_created"] is False
    assert metadata["automatic_execution_enabled"] is False
    assert metadata["provider_connectivity_enabled"] is False
    assert not any("command_centre" in name or "command_center" in name for name in AGENCY_OWNED_COLLECTIONS)

    expected = {
        ROOT / "backend/routers/agency_operations_command_center.py": [
            'prefix="/api/agencies/{agency_id}/operations-command-center"',
            "CommercialPilotOperationsCommandCentreService",
            "Query(default=50, ge=1, le=50)",
        ],
        ROOT / "backend/server.py": ["commercial_pilot_operations_command_centre_foundation"],
        ROOT / "frontend/src/App.jsx": ['"/agency": OperationsCommandCenterPage', '"/agency/operations-command-center": OperationsCommandCenterPage'],
        ROOT / "frontend/src/lib/moduleCatalog.js": ["Operations Command Centre", 'href: "/agency"'],
        ROOT / "frontend/src/pages/agency/OperationsCommandCenterPage.jsx": ["Here’s what needs attention.", "OperationsWorkList", "OperationsQueues"],
        ROOT / "frontend/src/components/operations/OperationsWorkList.jsx": ["My Work Today", "reassign"],
        ROOT / "frontend/src/components/operations/OperationsTimelineActivity.jsx": ["Today’s Timeline", "Recent Activity"],
        ROOT / "frontend/src/lib/agency.js": ["onboarding.required", "/agency/onboarding?agency_id="],
        ROOT / "docs/architecture/commercial-pilot-operations-command-centre-foundation.md": ["Operations Command Centre", "Phase 58.1"],
    }
    for path, needles in expected.items():
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            assert needle in text, f"Missing {needle!r} in {path.relative_to(ROOT)}"

    service_text = (ROOT / "backend/services/commercial_pilot_operations_command_centre_service.py").read_text(encoding="utf-8").lower()
    for forbidden in ["requests.get(", "requests.post(", "httpx.", "openai", "stripe", "backgroundtasks", ".insert_one(", ".update_one(", ".delete_one("]:
        assert forbidden not in service_text, forbidden


async def main() -> None:
    verify_registration()
    await verify_service()
    print("Commercial pilot operations command centre foundation smoke passed.")


if __name__ == "__main__":
    asyncio.run(main())
