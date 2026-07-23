from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from build_phase import CURRENT_BUILD_PHASE
from database import Database
from services.operations_command_center_service import (
    CLOSED_WORK_STATUSES,
    OFFER_ACTION_STATUSES,
    OPEN_WORK_STATUSES,
    REQUEST_TRIAGE_STATUSES,
    OperationsCommandCenterService,
)


PHASE_LABEL = CURRENT_BUILD_PHASE
RECORD_LIMIT = 250
RESULT_LIMIT = 50
SECTION_KEYS = ["my_work", "queues", "timeline", "alerts", "quick_actions", "recent_activity"]
WRITE_ROLES = {"agency_owner", "agency_admin", "agency_agent"}

QUEUE_DEFINITIONS = [
    ("new_requests", "New Requests"),
    ("offers_awaiting_action", "Offers Awaiting Action"),
    ("waiting_client", "Waiting for Client"),
    ("waiting_airline", "Waiting for Airline"),
    ("waiting_supplier", "Waiting for Supplier"),
    ("awaiting_approval", "Awaiting Approval"),
    ("ready_booking", "Ready for Booking"),
    ("ready_ticketing", "Ready for Ticketing"),
    ("special_services", "Special Services"),
    ("documents_to_send", "Documents to Send"),
    ("follow_ups", "Follow-ups"),
    ("overdue", "Overdue"),
]


def commercial_pilot_operations_command_centre_readiness_metadata() -> dict[str, Any]:
    return {
        "agency_operations_home_enabled": True,
        "existing_command_center_reused": True,
        "canonical_agency_home_route_enabled": True,
        "legacy_command_center_route_preserved": True,
        "my_work_today_enabled": True,
        "operational_queues_enabled": True,
        "today_timeline_enabled": True,
        "actionable_alerts_enabled": True,
        "permission_aware_quick_actions_enabled": True,
        "recent_activity_enabled": True,
        "onboarding_preferences_consumed": True,
        "bounded_tenant_aggregation_enabled": True,
        "deterministic_ordering_enabled": True,
        "agency_isolation_enforced": True,
        "existing_work_queue_actions_reused": True,
        "new_operational_collection_created": False,
        "automatic_execution_enabled": False,
        "provider_connectivity_enabled": False,
        "readiness_required": False,
    }


class CommercialPilotOperationsCommandCentreService(OperationsCommandCenterService):
    def __init__(self, db: Database) -> None:
        super().__init__(db)

    def safety_flags(self) -> dict[str, bool]:
        return {
            **super().safety_flags(),
            "commercial_pilot_operations_command_centre_foundation": True,
            "automatic_execution_disabled": True,
            "ticket_issuance_disabled": True,
            "payment_execution_disabled": True,
        }

    async def agency_home(
        self,
        agency_id: str,
        user: dict[str, Any],
        membership: dict[str, Any] | None,
        *,
        assignment: str | None = None,
        urgency: str | None = None,
        work_type: str | None = None,
        assignee_id: str | None = None,
        due_period: str | None = None,
        selected_date: str | None = None,
        limit: int = RESULT_LIMIT,
    ) -> dict[str, Any]:
        records = await self._load_records(agency_id=agency_id, include_agency_home_sources=True)
        records.update(await self._load_home_records(agency_id))
        legacy = self._dashboard(records, agency_id=agency_id, platform=False)
        preferences = self._preferences(records.get("dashboard_preferences", []))
        role = self._role(user, membership)
        user_context = {
            "user_id": user.get("id"),
            "display_name": user.get("full_name") or user.get("name") or user.get("email") or "Current user",
            "agency_role": role,
            "team_codes": self._team_codes(membership),
            "can_update_work_items": role in WRITE_ROLES,
        }
        selected_filters = {
            "assignment": self._choice(assignment, {"my_work", "team", "unassigned", "all"}, preferences["default_assignment_filter"]),
            "urgency": self._choice(urgency, {"all", "critical", "urgent", "high", "normal", "low"}, preferences["default_urgency_filter"]),
            "work_type": self._norm(work_type) or "all",
            "assignee_id": str(assignee_id or "all"),
            "due_period": self._choice(due_period, {"today", "overdue", "next_3_days", "all"}, "today"),
        }
        staff = await self._staff_options(agency_id, records.get("staff_memberships", []))
        priorities = self._priorities(records, user_context, staff, selected_filters)[: max(1, min(limit, RESULT_LIMIT))]
        timeline = self._today_timeline(records, selected_date, records.get("agency", []))
        response = {
            **legacy,
            "phase": PHASE_LABEL,
            "generated_at": self._now().isoformat(),
            "agency_id": agency_id,
            "user_context": user_context,
            "preferences": preferences,
            "priorities": {
                "title": "My Work Today",
                "items": priorities,
                "displayed_count": len(priorities),
                "sort": ["urgency", "deadline", "created_at", "id"],
            },
            "queues": self._queues(records),
            "timeline": timeline,
            "alerts": self._alerts(records),
            "quick_actions": self._quick_actions(role),
            "recent_activity": self._recent_activity(records, staff),
            "filter_metadata": self._filter_metadata(records, staff, selected_filters),
            "result_limits": {"source_records_per_collection": RECORD_LIMIT, "priorities": RESULT_LIMIT, "queue_items": 10, "alerts": 30, "recent_activity": 20},
            "commercial_pilot_operations_command_centre_foundation": True,
            "tenant_scoped": True,
            "empty_state_supported": True,
        }
        return response

    async def _load_home_records(self, agency_id: str) -> dict[str, list[dict[str, Any]]]:
        agency = await self.db.collection("agencies").find_one({"id": agency_id})
        return {"agency": [agency] if agency else []}

    async def _staff_options(self, agency_id: str, memberships: list[dict[str, Any]]) -> list[dict[str, str]]:
        options: list[dict[str, str]] = []
        for membership in memberships:
            if membership.get("status") != "active" or not membership.get("user_id"):
                continue
            user_id = str(membership["user_id"])
            user = await self.db.collection("platform_users").find_one({"id": user_id})
            label = (user or {}).get("full_name") or (user or {}).get("name") or membership.get("display_name") or "Agency team member"
            options.append({"value": user_id, "label": str(label), "role": str(membership.get("agency_role") or "")})
        return sorted(options, key=lambda item: (item["label"].lower(), item["value"]))

    def _preferences(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        item = next((record for record in records if record.get("preference_key", "default") == "default"), {})
        visible = [value for value in item.get("visible_operations_sections", SECTION_KEYS) if value in SECTION_KEYS]
        return {
            "preferred_starting_view": self._choice(item.get("preferred_starting_view"), set(SECTION_KEYS), "my_work"),
            "visible_sections": visible or SECTION_KEYS,
            "default_assignment_filter": self._choice(item.get("default_assignment_filter"), {"my_work", "team", "unassigned", "all"}, "my_work"),
            "default_urgency_filter": self._choice(item.get("default_urgency_filter"), {"all", "critical", "urgent", "high", "normal", "low"}, "all"),
            "legacy_defaults_applied": not bool(item),
        }

    def _priorities(
        self,
        records: dict[str, list[dict[str, Any]]],
        user_context: dict[str, Any],
        staff: list[dict[str, str]],
        filters: dict[str, str],
    ) -> list[dict[str, Any]]:
        staff_labels = {item["value"]: item["label"] for item in staff}
        items = []
        for work_item in records["work_items"]:
            if self._norm(work_item.get("status")) not in OPEN_WORK_STATUSES:
                continue
            assigned_user_id = work_item.get("assigned_user_id")
            team_code = self._norm(work_item.get("assigned_team_code"))
            current_teams = set(user_context.get("team_codes") or [])
            assignment = filters["assignment"]
            if assignment == "my_work" and assigned_user_id not in {None, user_context.get("user_id")} and team_code not in current_teams:
                continue
            if assignment == "team" and (not team_code or team_code not in current_teams):
                continue
            if assignment == "unassigned" and (assigned_user_id or team_code):
                continue
            enriched = self._enrich_work_item(work_item, records, staff_labels, user_context)
            if filters["urgency"] != "all" and enriched["urgency"] != filters["urgency"]:
                continue
            if filters["work_type"] != "all" and self._norm(enriched["work_type"]) != filters["work_type"]:
                continue
            if filters["assignee_id"] != "all" and str(enriched.get("assigned_user_id") or "unassigned") != filters["assignee_id"]:
                continue
            if not self._due_period_matches(enriched.get("deadline"), filters["due_period"]):
                continue
            items.append(enriched)
        items.sort(key=lambda item: (-item["urgency_score"], self._date_sort(item.get("deadline")), self._date_sort(item.get("created_at")), item["id"]))
        return items

    def _enrich_work_item(
        self,
        item: dict[str, Any],
        records: dict[str, list[dict[str, Any]]],
        staff_labels: dict[str, str],
        user_context: dict[str, Any],
    ) -> dict[str, Any]:
        context = item.get("internal_context_json") or {}
        source = self._source_record(item, records)
        client_id = item.get("client_id") or context.get("client_id") or source.get("client_id")
        passenger_id = item.get("passenger_id") or context.get("passenger_id") or source.get("passenger_id") or source.get("primary_passenger_id")
        client = self._by_id(records.get("clients", []), client_id)
        passenger = self._by_id(records.get("passengers", []) + records.get("passenger_workspaces", []), passenger_id)
        route = self._route_label(source, context)
        due_at = item.get("due_at")
        urgency_score = self._urgency_score(item.get("priority"), item.get("severity"), item.get("sla_status") or item.get("status"), due_at)
        urgency = self._urgency_label(urgency_score, due_at, item)
        assigned_user_id = item.get("assigned_user_id")
        can_write = bool(user_context.get("can_update_work_items"))
        actions = [{"key": "open", "label": "Open", "href": self._entity_href(item.get("source_entity_type"), item.get("source_entity_id"))}]
        api_base = f"/api/agencies/{item.get('agency_id')}/work-queue/work-items/{item.get('id')}"
        if can_write and assigned_user_id != user_context.get("user_id"):
            actions.append({"key": "assign_self", "label": "Assign to me", "method": "POST", "api_path": f"{api_base}/assign-self"})
        if can_write:
            actions.append({"key": "reassign", "label": "Reassign", "method": "POST", "api_path": f"{api_base}/reassign", "requires_assignee": True})
            actions.append({"key": "complete", "label": "Complete", "method": "POST", "api_path": f"{api_base}/complete", "confirmation_required": True})
        return {
            "id": str(item.get("id")),
            "work_item_code": item.get("work_item_code"),
            "work_type": item.get("work_item_type") or "operational_work",
            "client": self._person_label(client, "Client not linked"),
            "passenger": self._passenger_label(passenger, source),
            "trip_or_route": route or "Route not linked",
            "reason": item.get("summary") or item.get("title") or "Operational follow-up required",
            "next_action": self._next_action(item),
            "deadline": due_at,
            "urgency": urgency,
            "urgency_score": urgency_score,
            "consultant": staff_labels.get(str(assigned_user_id)) if assigned_user_id else (self._label(item.get("assigned_team_code")) if item.get("assigned_team_code") else "Unassigned"),
            "assigned_user_id": assigned_user_id,
            "assigned_team_code": item.get("assigned_team_code"),
            "source_type": item.get("source_entity_type"),
            "source_label": self._label(item.get("source_entity_type") or "Work item"),
            "source_id": item.get("source_entity_id"),
            "status": item.get("status"),
            "created_at": item.get("created_at"),
            "actions": actions,
        }

    def _queues(self, records: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        buckets: dict[str, list[dict[str, Any]]] = {key: [] for key, _ in QUEUE_DEFINITIONS}
        for item in records["work_items"]:
            if self._norm(item.get("status")) not in OPEN_WORK_STATUSES:
                continue
            queue_key = self._work_item_queue(item)
            if queue_key in buckets:
                buckets[queue_key].append(self._queue_item("work_item", item, item.get("title") or "Operational work", self._entity_href(item.get("source_entity_type"), item.get("source_entity_id"))))
            if self._is_overdue(item.get("due_at")) or self._norm(item.get("sla_status")) in {"overdue", "breached"}:
                buckets["overdue"].append(self._queue_item("work_item", item, item.get("title") or "Overdue work", "/agency/work-queue"))
        for item in records["request_intakes"] + records["travel_requests"]:
            if self._norm(item.get("status") or item.get("request_status")) in REQUEST_TRIAGE_STATUSES:
                buckets["new_requests"].append(self._queue_item("request", item, item.get("request_title") or item.get("title") or item.get("request_reference") or "New request", self._entity_href("request", item.get("id"))))
        for item in records["offer_workspaces"]:
            if self._norm(item.get("offer_status") or item.get("status")) in OFFER_ACTION_STATUSES:
                buckets["offers_awaiting_action"].append(self._queue_item("offer", item, item.get("offer_title") or item.get("offer_reference") or "Offer awaiting action", self._entity_href("offer", item.get("id"))))
        for item in records["booking_handoffs"]:
            if self._norm(item.get("handoff_status")) in {"ready", "conditional", "handed_off"} and not item.get("booking_workspace_id"):
                buckets["ready_booking"].append(self._queue_item("booking_handoff", item, item.get("handoff_reference") or "Booking handoff ready", "/agency/booking-handoffs"))
        for item in records["booking_workspaces"]:
            if self._norm(item.get("booking_status") or item.get("status")) in {"confirmed", "ready_to_ticket", "awaiting_ticketing", "ticketing_pending"} and not (item.get("ticket_ids") or item.get("linked_ticket_ids")):
                buckets["ready_ticketing"].append(self._queue_item("booking", item, item.get("booking_reference") or "Booking ready for ticketing", self._entity_href("booking", item.get("id"))))
        for item in records["ssr_osi_workspaces"]:
            if self._norm(item.get("workspace_status") or item.get("status")) not in CLOSED_WORK_STATUSES:
                buckets["special_services"].append(self._queue_item("passenger_service", item, item.get("service_name") or item.get("ssr_code") or "Passenger service", "/agency/passenger-services"))
        for item in records["document_deliveries"]:
            if self._norm(item.get("status") or item.get("delivery_status")) in {"draft", "pending", "ready", "failed", "not_sent"}:
                buckets["documents_to_send"].append(self._queue_item("document", item, item.get("document_title") or item.get("file_name") or "Document pending delivery", "/agency/documents"))
        for item in records["request_tasks"]:
            if self._norm(item.get("status")) not in {"done", "completed", "cancelled", "archived"}:
                buckets["follow_ups"].append(self._queue_item("follow_up", item, item.get("title") or item.get("task_type") or "Follow-up", self._entity_href("request", item.get("request_id"))))
                if self._is_overdue(item.get("due_at") or item.get("deadline")):
                    buckets["overdue"].append(self._queue_item("follow_up", item, item.get("title") or "Overdue follow-up", self._entity_href("request", item.get("request_id"))))
        output = []
        for key, label in QUEUE_DEFINITIONS:
            items = self._dedupe_sorted(buckets[key])
            output.append({"key": key, "label": label, "count": len(items), "items": items[:10], "href": self._queue_href(key)})
        return output

    def _today_timeline(self, records: dict[str, list[dict[str, Any]]], selected_date: str | None, agencies: list[dict[str, Any]]) -> dict[str, Any]:
        agency = agencies[0] if agencies else {}
        timezone_name = agency.get("timezone") or "UTC"
        zone = self._zone(timezone_name)
        today = self._now().astimezone(zone).date()
        chosen = self._parse_date(selected_date) or today
        events: list[dict[str, Any]] = []
        sources = [
            (records["work_items"], "due_at", "task", "/agency/work-queue"),
            (records["deadlines"], "due_at", "deadline", "/agency/deadlines"),
            (records["request_tasks"], "due_at", "follow_up", "/agency/requests"),
            (records["offer_workspaces"], "validity_date", "offer_expiry", "/agency/offers"),
            (records["document_workspaces"], "requirement_deadline", "document", "/agency/documents"),
            (records["trip_workspaces"], "departure_date", "departure", "/agency/trips"),
            (records["flight_workspaces"], "departure_datetime", "flight", "/agency/trips"),
        ]
        for items, field, event_type, href in sources:
            for item in items:
                timestamp = item.get(field) or (item.get("calculated_due_at") if event_type == "deadline" else None)
                parsed = self._parse_dt(timestamp)
                if parsed and parsed.astimezone(zone).date() == chosen:
                    events.append({
                        "id": f"{event_type}:{item.get('id')}",
                        "event_type": event_type,
                        "label": self._timeline_label(event_type, item),
                        "timestamp": parsed.isoformat(),
                        "time_label": parsed.astimezone(zone).strftime("%H:%M"),
                        "status": item.get("status") or item.get("offer_status") or item.get("trip_status") or item.get("flight_status"),
                        "href": href,
                    })
        events.sort(key=lambda item: (item["timestamp"], item["id"]))
        return {
            "selected_date": chosen.isoformat(),
            "today": today.isoformat(),
            "previous_date": (chosen - timedelta(days=1)).isoformat(),
            "next_date": (chosen + timedelta(days=1)).isoformat(),
            "timezone": timezone_name,
            "events": events[:RESULT_LIMIT],
        }

    def _alerts(self, records: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []
        for item in records["deadlines"]:
            due_at = item.get("due_at") or item.get("calculated_due_at")
            if self._is_overdue(due_at) or self._norm(item.get("status")) in {"overdue", "breached"}:
                alerts.append(self._alert("overdue_deadline", "Deadline overdue", item.get("explanation") or "An operational deadline has passed.", "Open the deadline and decide the next action.", due_at, "/agency/deadlines", "critical", item))
            elif "ticket" in self._norm(item.get("deadline_type")) and self._is_due_within(due_at, timedelta(hours=24)):
                alerts.append(self._alert("ticketing_deadline", "Ticketing deadline approaching", item.get("explanation") or "A ticketing deadline is due within 24 hours.", "Open the deadline and review ticketing readiness.", due_at, "/agency/deadlines", "urgent", item))
        for item in records["travel_requests"]:
            missing = [field for field in ["client_id", "primary_passenger_id"] if not item.get(field)]
            if missing:
                alerts.append(self._alert("missing_passenger_data", "Passenger details incomplete", "This request is missing linked client or passenger details.", "Open the request and complete the traveller details.", item.get("deadline"), self._entity_href("request", item.get("id")), "high", item))
        for item in records["ssr_osi_workspaces"]:
            status = self._norm(item.get("workspace_status") or item.get("status"))
            if status not in CLOSED_WORK_STATUSES and (item.get("approval_required") or status in {"blocked", "pending", "waiting"}):
                alerts.append(self._alert("unresolved_service", "Passenger service needs attention", item.get("service_summary") or item.get("operational_notes") or "A passenger service requirement remains unresolved.", "Open Passenger Services and review the requirement.", item.get("service_deadline"), "/agency/passenger-services", "high", item))
        for item in records["document_deliveries"]:
            if self._norm(item.get("status") or item.get("delivery_status")) in {"pending", "ready", "failed", "not_sent"}:
                alerts.append(self._alert("document_delivery", "Document pending delivery", "A prepared document has not been delivered.", "Open Documents and review delivery readiness.", item.get("delivery_deadline"), "/agency/documents", "normal", item))
        for item in records["offer_workspaces"]:
            valid_until = item.get("validity_date")
            parsed = self._parse_dt(valid_until)
            if parsed and self._now() <= parsed <= self._now() + timedelta(hours=48):
                alerts.append(self._alert("offer_expiring", "Offer expires soon", item.get("offer_title") or "An active offer is nearing expiry.", "Open the offer and follow up with the client.", valid_until, self._entity_href("offer", item.get("id")), "urgent", item))
        for item in records["booking_handoffs"] + records["booking_readiness_packages"]:
            status = self._norm(item.get("handoff_status") or item.get("readiness_status") or item.get("status"))
            if status in {"blocked", "conditional", "incomplete", "not_ready"}:
                alerts.append(self._alert("booking_readiness", "Booking readiness incomplete", "Booking cannot proceed cleanly until readiness issues are reviewed.", "Open the booking handoff and resolve its blockers.", item.get("deadline"), "/agency/booking-handoffs", "high", item))
        for item in records["invoices"] + records["payments"]:
            status = self._norm(item.get("status") or item.get("payment_status"))
            if status in {"blocked", "overdue", "due", "failed"}:
                alerts.append(self._alert("payment_blocker", "Payment needs attention", "A payment or invoice state is blocking operational progress.", "Open Finance and review the payment record.", item.get("due_date") or item.get("due_at"), "/agency/invoices", "high", item))
        alerts = self._dedupe_sorted(alerts)
        return alerts[:30]

    def _quick_actions(self, role: str) -> list[dict[str, Any]]:
        can_write = role in WRITE_ROLES
        items = [
            ("new_request", "New Request", "/agency/requests/new", can_write),
            ("new_offer", "New Offer", "/agency/offers/new", can_write),
            ("new_booking", "New Booking", "/agency/bookings/new", can_write),
            ("new_passenger", "New Passenger", "/agency/passengers", can_write),
            ("import_pnr", "Import PNR", "/agency/booking-imports", can_write),
            ("open_tasks", "Open Tasks", "/agency/work-queue", True),
        ]
        return [{"key": key, "label": label, "href": href} for key, label, href, allowed in items if allowed]

    def _recent_activity(self, records: dict[str, list[dict[str, Any]]], staff: list[dict[str, str]]) -> list[dict[str, Any]]:
        staff_labels = {item["value"]: item["label"] for item in staff}
        activities = []
        for item in records["operational_timelines"]:
            actor = item.get("created_by") or item.get("sender")
            activities.append({
                "id": f"timeline:{item.get('id')}",
                "label": item.get("summary") or self._activity_label(item.get("event_type") or "Operational update"),
                "timestamp": item.get("created_at") or item.get("occurred_at"),
                "actor": staff_labels.get(str(actor), actor or "Agency team"),
                "href": self._entity_href(self._timeline_source_type(item), self._timeline_source_id(item)),
            })
        for item in records["audit_events"]:
            actor = item.get("actor_user_id")
            activities.append({
                "id": f"audit:{item.get('id')}",
                "label": item.get("summary") or self._activity_label(item.get("event_type") or "Record updated"),
                "timestamp": item.get("created_at"),
                "actor": staff_labels.get(str(actor), "Agency team"),
                "href": self._entity_href(item.get("entity_type"), item.get("entity_id")),
            })
        activities.sort(key=lambda item: (self._date_sort(item.get("timestamp")), item["id"]), reverse=True)
        return activities[:20]

    def _activity_label(self, value: Any) -> str:
        return str(value or "Operational update").replace(".", " ").replace("_", " ").replace("-", " ").title()

    def _filter_metadata(self, records: dict[str, list[dict[str, Any]]], staff: list[dict[str, str]], selected: dict[str, str]) -> dict[str, Any]:
        work_types = sorted({self._norm(item.get("work_item_type")) for item in records["work_items"] if item.get("work_item_type")})
        return {
            "selected": selected,
            "assignment_options": [{"value": value, "label": label} for value, label in [("my_work", "My work"), ("team", "My team"), ("unassigned", "Unassigned"), ("all", "All work")]],
            "urgency_options": [{"value": value, "label": self._label(value)} for value in ["all", "critical", "urgent", "high", "normal", "low"]],
            "work_type_options": [{"value": "all", "label": "All work types"}] + [{"value": value, "label": self._label(value)} for value in work_types],
            "due_options": [{"value": value, "label": label} for value, label in [("today", "Due today"), ("overdue", "Overdue"), ("next_3_days", "Next 3 days"), ("all", "Any due date")]],
            "assignee_options": [{"value": "all", "label": "Any consultant"}, {"value": "unassigned", "label": "Unassigned"}] + staff,
            "assignees": staff,
        }

    def _source_record(self, item: dict[str, Any], records: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        source_id = item.get("source_entity_id")
        for key in ["travel_requests", "request_intakes", "trip_workspaces", "offer_workspaces", "booking_workspaces", "ticket_workspaces", "emd_workspaces", "ssr_osi_workspaces", "document_workspaces"]:
            match = self._by_id(records.get(key, []), source_id)
            if match:
                return match
        return {}

    def _work_item_queue(self, item: dict[str, Any]) -> str:
        values = " ".join(self._norm(item.get(field)) for field in ["queue_code", "work_item_type", "status", "blocker_status"])
        if "waiting_client" in values:
            return "waiting_client"
        if any(value in values for value in ["waiting_airline", "waiting_supplier"]):
            return "waiting_airline" if "waiting_airline" in values else "waiting_supplier"
        if "approval" in values:
            return "awaiting_approval"
        if "ticket" in values:
            return "ready_ticketing"
        if "booking" in values:
            return "ready_booking"
        if any(value in values for value in ["service", "ssr", "osi", "medif", "petc", "avih"]):
            return "special_services"
        if "document" in values:
            return "documents_to_send"
        if any(value in values for value in ["request", "triage"]):
            return "new_requests"
        if "offer" in values:
            return "offers_awaiting_action"
        return "follow_ups"

    def _queue_item(self, source: str, item: dict[str, Any], label: str, href: str) -> dict[str, Any]:
        due_at = item.get("due_at") or item.get("deadline") or item.get("validity_date")
        score = self._urgency_score(item.get("priority"), item.get("severity"), item.get("status"), due_at)
        return {"id": f"{source}:{item.get('id')}", "label": label, "status": item.get("status") or item.get("offer_status") or item.get("request_status"), "deadline": due_at, "urgency_score": score, "href": href}

    def _alert(self, key: str, title: str, why: str, next_action: str, deadline: Any, href: str, urgency: str, item: dict[str, Any]) -> dict[str, Any]:
        score = {"critical": 130, "urgent": 110, "high": 90, "normal": 60}.get(urgency, 40)
        return {"id": f"{key}:{item.get('id')}", "alert_type": key, "what": title, "why": why, "next_action": next_action, "deadline": deadline, "href": href, "urgency": urgency, "urgency_score": score}

    def _dedupe_sorted(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        unique = {item["id"]: item for item in items}
        return sorted(unique.values(), key=lambda item: (-int(item.get("urgency_score") or 0), self._date_sort(item.get("deadline")), item["id"]))

    def _route_label(self, source: dict[str, Any], context: dict[str, Any]) -> str | None:
        origin = source.get("requested_origin") or source.get("departure_city") or source.get("origin_airport") or context.get("origin")
        destination = source.get("requested_destination") or source.get("destination_city") or source.get("destination_airport") or context.get("destination")
        if origin and destination:
            return f"{origin} to {destination}"
        return source.get("trip_reference") or source.get("request_reference") or context.get("route_summary")

    def _next_action(self, item: dict[str, Any]) -> str:
        value = " ".join(self._norm(item.get(field)) for field in ["work_item_type", "queue_code", "blocker_status", "status"])
        mappings = [
            ("waiting_client", "Contact the client"),
            ("waiting_airline", "Contact the airline"),
            ("waiting_supplier", "Contact the supplier"),
            ("waiting_document", "Review missing documents"),
            ("approval", "Review approval requirements"),
            ("payment", "Review payment status"),
            ("offer", "Prepare or review the offer"),
            ("booking", "Review booking readiness"),
            ("ticket", "Review ticketing readiness"),
            ("triage", "Triage the request"),
        ]
        return next((label for needle, label in mappings if needle in value), "Open and review")

    def _entity_href(self, entity_type: Any, entity_id: Any) -> str:
        kind = self._norm(entity_type)
        identifier = str(entity_id or "")
        if kind in {"request", "travel_request", "request_intake"}:
            return f"/agency/requests/{identifier}" if identifier else "/agency/requests"
        if kind in {"trip", "trip_workspace"}:
            return f"/agency/trips/{identifier}" if identifier else "/agency/trips"
        if kind in {"offer", "offer_workspace", "accepted_offer"}:
            return f"/agency/offers/{identifier}" if identifier else "/agency/offers"
        if kind in {"booking", "booking_workspace"}:
            return f"/agency/bookings/{identifier}" if identifier else "/agency/bookings"
        if kind in {"ticket", "ticket_workspace"}:
            return f"/agency/tickets/{identifier}" if identifier else "/agency/tickets-emds"
        if kind in {"emd", "emd_workspace"}:
            return f"/agency/emds/{identifier}" if identifier else "/agency/tickets-emds"
        if kind in {"passenger", "passenger_workspace"}:
            return f"/agency/passengers/{identifier}" if identifier else "/agency/passengers"
        if kind in {"document", "document_workspace"}:
            return f"/agency/documents/{identifier}" if identifier else "/agency/documents"
        if kind in {"ssr", "osi", "ssr_osi_workspace", "passenger_service"}:
            return "/agency/passenger-services"
        return "/agency/work-queue"

    def _queue_href(self, key: str) -> str:
        mapping = {
            "new_requests": "/agency/requests",
            "offers_awaiting_action": "/agency/offers",
            "ready_booking": "/agency/booking-handoffs",
            "ready_ticketing": "/agency/bookings",
            "special_services": "/agency/passenger-services",
            "documents_to_send": "/agency/documents",
            "overdue": "/agency/deadlines",
        }
        return mapping.get(key, "/agency/work-queue")

    def _timeline_label(self, event_type: str, item: dict[str, Any]) -> str:
        return item.get("title") or item.get("deadline_reference") or item.get("offer_title") or item.get("document_title") or item.get("trip_reference") or item.get("flight_reference") or self._label(event_type)

    def _timeline_source_type(self, item: dict[str, Any]) -> Any:
        for field, label in [("travel_request_workspace_id", "request"), ("trip_workspace_id", "trip"), ("booking_workspace_id", "booking"), ("ticket_workspace_id", "ticket"), ("emd_workspace_id", "emd"), ("document_workspace_id", "document"), ("passenger_workspace_id", "passenger")]:
            if item.get(field):
                return label
        return item.get("source_entity_type")

    def _timeline_source_id(self, item: dict[str, Any]) -> Any:
        for field in ["travel_request_workspace_id", "trip_workspace_id", "booking_workspace_id", "ticket_workspace_id", "emd_workspace_id", "document_workspace_id", "passenger_workspace_id", "source_entity_id"]:
            if item.get(field):
                return item[field]
        return None

    def _person_label(self, item: dict[str, Any], fallback: str) -> str:
        if not item:
            return fallback
        return str(item.get("display_name") or item.get("full_name") or item.get("preferred_name") or " ".join(filter(None, [item.get("first_name"), item.get("last_name")])) or item.get("name") or fallback)

    def _passenger_label(self, passenger: dict[str, Any], source: dict[str, Any]) -> str:
        if passenger:
            return self._person_label(passenger, "Passenger not linked")
        count = source.get("passenger_count") or len(source.get("passenger_ids") or [])
        if count:
            return f"{count} passenger" if str(count) == "1" else f"{count} passengers"
        return "Passenger not linked"

    def _role(self, user: dict[str, Any], membership: dict[str, Any] | None) -> str:
        if membership and membership.get("agency_role"):
            return str(membership["agency_role"])
        if user.get("global_role") in {"platform_owner", "platform_admin", "platform_support"}:
            return "platform_read_only"
        return "agency_readonly"

    def _team_codes(self, membership: dict[str, Any] | None) -> list[str]:
        if not membership:
            return []
        values = membership.get("team_codes") or ([membership.get("team_code")] if membership.get("team_code") else [])
        return sorted({self._norm(value) for value in values if value})

    def _due_period_matches(self, value: Any, period: str) -> bool:
        if period == "all":
            return True
        parsed = self._parse_dt(value)
        if not parsed:
            return period == "today"
        today = self._now().date()
        if period == "overdue":
            return parsed < self._now()
        if period == "next_3_days":
            return today <= parsed.date() <= today + timedelta(days=3)
        return parsed.date() == today

    def _urgency_label(self, score: int, due_at: Any, item: dict[str, Any]) -> str:
        if self._is_overdue(due_at) or self._norm(item.get("severity")) == "critical":
            return "critical"
        if score >= 95:
            return "urgent"
        if score >= 65:
            return "high"
        if score >= 35:
            return "normal"
        return "low"

    def _is_overdue(self, value: Any) -> bool:
        parsed = self._parse_dt(value)
        return bool(parsed and parsed < self._now())

    def _is_due_within(self, value: Any, window: timedelta) -> bool:
        parsed = self._parse_dt(value)
        return bool(parsed and self._now() <= parsed <= self._now() + window)

    def _by_id(self, records: list[dict[str, Any]], record_id: Any) -> dict[str, Any]:
        return next((item for item in records if record_id and str(item.get("id")) == str(record_id)), {})

    def _choice(self, value: Any, allowed: set[str], fallback: str) -> str:
        normalized = self._norm(value)
        return normalized if normalized in allowed else fallback

    def _parse_date(self, value: str | None) -> date | None:
        try:
            return date.fromisoformat(value) if value else None
        except ValueError:
            return None

    def _zone(self, value: str) -> ZoneInfo:
        try:
            return ZoneInfo(value)
        except ZoneInfoNotFoundError:
            return ZoneInfo("UTC")

    def _date_sort(self, value: Any) -> str:
        parsed = self._parse_dt(value)
        return parsed.isoformat() if parsed else "9999-12-31T23:59:59+00:00"
