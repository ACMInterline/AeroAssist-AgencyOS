from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from database import Database


PHASE_LABEL = "phase_54_8_operations_command_center_foundation"

VIEW_TYPES = ["dashboard", "queue", "kanban", "calendar", "timeline", "exceptions", "workload"]

OPEN_WORK_STATUSES = {"open", "accepted", "in_progress", "waiting", "blocked", "reopened"}
CLOSED_WORK_STATUSES = {"completed", "cancelled", "resolved", "rejected", "archived"}
OPEN_AFTER_SALES_STATUSES = {
    "opened",
    "assessing",
    "information_required",
    "supplier_contact_required",
    "client_decision_required",
    "quote_preparation",
    "awaiting_approval",
    "processing",
    "partially_resolved",
}
REQUEST_TRIAGE_STATUSES = {"new", "submitted", "received", "triage", "awaiting_triage", "draft_metadata"}
OFFER_ACTION_STATUSES = {"draft", "preparing", "under_review", "sent", "awaiting_client", "awaiting_response", "needs_review"}
BOOKING_TICKETING_STATUSES = {"booking_created", "confirmed", "ready_to_ticket", "awaiting_ticketing", "ticketing_pending"}
MANUAL_REVIEW_WORK_TYPES = {"policy_gap_manual_review", "knowledge_issue", "workflow_blocker"}


class OperationsCommandCenterService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "operations_command_center_foundation": True,
            "aggregation_only": True,
            "duplicate_operational_data_disabled": True,
            "read_only_dashboard": True,
            "uncontrolled_drag_and_drop_disabled": True,
            "kanban_moves_require_workflow_transitions": True,
            "kanban_guard_enforcement_enabled": True,
            "provider_execution_disabled": True,
            "external_api_calls_disabled": True,
            "background_workers_disabled": True,
            "ai_disabled": True,
            "status_mutation_disabled": True,
            "human_authority_final": True,
        }

    async def platform_dashboard(self, agency_id: str | None = None) -> dict[str, Any]:
        records = await self._load_records(agency_id=agency_id)
        return self._dashboard(records, agency_id=agency_id, platform=True)

    async def agency_command_center(self, agency_id: str) -> dict[str, Any]:
        records = await self._load_records(agency_id=agency_id)
        return self._dashboard(records, agency_id=agency_id, platform=False)

    async def summary(self, agency_id: str | None = None) -> dict[str, Any]:
        return (await self.platform_dashboard(agency_id=agency_id)).get("kpis") or {}

    async def operational_feed(self, agency_id: str | None = None, limit: int = 100, platform: bool | None = None) -> list[dict[str, Any]]:
        records = await self._load_records(agency_id=agency_id)
        return self._feed(records, platform=(agency_id is None if platform is None else platform))[:limit]

    async def calendar_events(self, agency_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        records = await self._load_records(agency_id=agency_id)
        return self._calendar(records)[:limit]

    async def kanban_lanes(self, agency_id: str | None = None, platform: bool = False) -> list[dict[str, Any]]:
        records = await self._load_records(agency_id=agency_id)
        return self._kanban(records, platform=platform)

    async def team_workload(self, agency_id: str | None = None) -> list[dict[str, Any]]:
        records = await self._load_records(agency_id=agency_id)
        return self._workload(records)

    def _dashboard(self, records: dict[str, list[dict[str, Any]]], agency_id: str | None, platform: bool) -> dict[str, Any]:
        kpis = self._kpis(records)
        feed = self._feed(records, platform=platform)
        calendar = self._calendar(records)
        kanban = self._kanban(records, platform=platform)
        workload = self._workload(records)
        exceptions = [item for item in feed if item.get("severity") in {"critical", "high"} or item.get("status") in {"blocked", "overdue", "breached"}]
        timeline = self._timeline(records)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "platform_read_only_governance": platform,
            "view_types": VIEW_TYPES,
            "kpis": kpis,
            "dashboard": {"kpis": kpis, "top_feed": feed[:20], "exceptions": exceptions[:20], "metadata_only": True},
            "queue": feed[:100],
            "kanban": {"lanes": kanban, "guard_enforcement": True, "uncontrolled_drag_and_drop_disabled": True, "metadata_only": True},
            "calendar": {"events": calendar[:100], "metadata_only": True},
            "timeline": {"events": timeline[:100], "metadata_only": True},
            "exceptions": exceptions[:100],
            "workload": workload,
            "safe_action_links": self._safe_action_links(agency_id=agency_id, platform=platform),
            **self.safety_flags(),
        }

    async def _load_records(self, agency_id: str | None = None) -> dict[str, list[dict[str, Any]]]:
        filters = {"agency_id": agency_id} if agency_id else None
        names = {
            "work_items": "operational_work_items",
            "deadlines": "operational_deadlines",
            "workflow_instances": "operational_workflow_instances",
            "workflow_events": "operational_workflow_events",
            "request_intakes": "request_intakes",
            "travel_requests": "travel_requests",
            "offer_workspaces": "offer_workspaces_v2",
            "offer_acceptances": "offer_acceptances",
            "booking_handoffs": "offer_booking_handoffs",
            "booking_workspaces": "booking_workspaces",
            "ticket_workspaces": "ticket_workspaces",
            "emd_workspaces": "emd_workspaces",
            "ssr_osi_workspaces": "ssr_osi_workspaces",
            "document_workspaces": "document_workspaces",
            "trip_workspaces": "trip_workspaces",
            "flight_workspaces": "flight_workspaces",
            "after_sales_cases": "after_sales_cases",
            "operational_intelligence_cases": "operational_intelligence_cases",
            "pilot_readiness_issues": "pilot_readiness_issues",
            "request_tasks": "request_tasks",
            "invoices": "invoices",
            "payments": "payments",
        }
        return {key: await self.db.collection(collection).find_many(filters) for key, collection in names.items()}

    def _kpis(self, records: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        now = self._now()
        work_items = records["work_items"]
        deadlines = records["deadlines"]
        workflows = records["workflow_instances"]
        after_sales = records["after_sales_cases"]
        documents = records["document_workspaces"]
        ssr_osi = records["ssr_osi_workspaces"]
        trips = records["trip_workspaces"]
        flights = records["flight_workspaces"]
        open_work = [item for item in work_items if self._norm(item.get("status")) in OPEN_WORK_STATUSES]
        deadline_due_soon = [item for item in deadlines if self._norm(item.get("status")) == "due_soon" or self._norm(item.get("breach_state")) == "due_soon"]
        deadline_overdue = [item for item in deadlines if self._norm(item.get("status")) in {"overdue", "breached"} or self._norm(item.get("breach_state")) == "breached"]
        workflow_blockers = sum(len(item.get("active_blockers_json") or []) for item in workflows)
        request_triage = [
            item
            for item in records["request_intakes"] + records["travel_requests"]
            if self._norm(item.get("status") or item.get("request_status")) in REQUEST_TRIAGE_STATUSES
        ]
        offers_awaiting_action = [
            item for item in records["offer_workspaces"] if self._norm(item.get("offer_status") or item.get("status")) in OFFER_ACTION_STATUSES
        ]
        accepted_awaiting_booking = [
            item
            for item in records["booking_handoffs"]
            if self._norm(item.get("handoff_status")) in {"ready", "conditional", "handed_off"} and not item.get("booking_workspace_id")
        ]
        bookings_awaiting_ticketing = [
            item
            for item in records["booking_workspaces"]
            if self._norm(item.get("booking_status") or item.get("status")) in BOOKING_TICKETING_STATUSES or not (item.get("ticket_ids") or item.get("linked_ticket_ids"))
        ]
        service_approval_documents = [
            item for item in ssr_osi if item.get("approval_required") and self._norm(item.get("approval_status")) not in {"approved", "not_required", "waived"}
        ] + [
            item for item in documents if item.get("required_for_travel") and self._norm(item.get("verification_status")) not in {"verified", "waived", "not_required"}
        ]
        departure_buckets = self._departure_buckets(trips, flights, now)
        open_after_sales = [item for item in after_sales if self._norm(item.get("case_status")) in OPEN_AFTER_SALES_STATUSES]
        disrupted = [item for item in open_after_sales if self._norm(item.get("case_type")) == "disruption_irregular_operation"] + [
            item for item in work_items if self._norm(item.get("work_item_type")) == "disruption"
        ]
        knowledge_manual_review = [
            item for item in work_items if self._norm(item.get("work_item_type")) in MANUAL_REVIEW_WORK_TYPES or self._norm(item.get("blocker_status")) == "manual_review"
        ] + [
            item for item in records["operational_intelligence_cases"] if self._norm(item.get("case_status") or item.get("overall_status")) not in CLOSED_WORK_STATUSES
        ]
        payment_invoice_blockers = [
            item for item in work_items if self._norm(item.get("blocker_status")) == "waiting_payment"
        ] + [
            item for item in records["invoices"] + records["payments"] if self._norm(item.get("status") or item.get("payment_status")) in {"due", "overdue", "blocked", "pending"}
        ]
        pilot_issues = [
            item for item in records["pilot_readiness_issues"] if self._norm(item.get("issue_status")) in {"open", "in_review", "reopened"}
        ]
        return {
            "current_operational_workload": len(open_work),
            "unassigned_work": len([item for item in open_work if not item.get("assigned_user_id")]),
            "due_soon": len(deadline_due_soon) + len([item for item in open_work if self._norm(item.get("sla_status")) == "due_soon"]),
            "overdue": len(deadline_overdue) + len([item for item in open_work if self._norm(item.get("sla_status")) in {"overdue", "breached"}]),
            "critical_blockers": len([item for item in open_work if self._norm(item.get("severity")) == "critical" or self._norm(item.get("blocker_status")) == "blocked"]) + workflow_blockers,
            "requests_awaiting_triage": len(request_triage),
            "offers_awaiting_action": len(offers_awaiting_action),
            "accepted_offers_awaiting_booking": len(accepted_awaiting_booking),
            "bookings_awaiting_ticketing": len(bookings_awaiting_ticketing),
            "service_approvals_documents": len(service_approval_documents),
            "departures_next_24_hours": departure_buckets["24h"],
            "departures_next_48_hours": departure_buckets["48h"],
            "departures_next_72_hours": departure_buckets["72h"],
            "disrupted_trips": len(disrupted),
            "after_sales_cases": len(open_after_sales),
            "unresolved_knowledge_manual_review": len(knowledge_manual_review),
            "payment_invoice_blockers": len(payment_invoice_blockers),
            "pilot_readiness_issues": len(pilot_issues),
            "team_workload_units": len(open_work),
        }

    def _feed(self, records: dict[str, list[dict[str, Any]]], *, platform: bool) -> list[dict[str, Any]]:
        feed: list[dict[str, Any]] = []
        for item in records["work_items"]:
            if self._norm(item.get("status")) in OPEN_WORK_STATUSES:
                feed.append(
                    self._feed_item(
                        source="work_item",
                        item=item,
                        title=item.get("title") or item.get("work_item_code") or "Work item",
                        summary=item.get("summary"),
                        status=item.get("status"),
                        priority=item.get("priority"),
                        severity=item.get("severity"),
                        due_at=item.get("due_at"),
                        href="/platform/work-queues" if platform else "/agency/work-queue",
                    )
                )
        for item in records["deadlines"]:
            if self._norm(item.get("status")) not in {"completed", "waived", "cancelled"}:
                feed.append(
                    self._feed_item(
                        source="deadline",
                        item=item,
                        title=item.get("deadline_reference") or item.get("deadline_type") or "Operational deadline",
                        summary=item.get("explanation"),
                        status=item.get("status"),
                        priority=item.get("priority"),
                        severity="high" if self._norm(item.get("breach_state")) == "breached" else "medium",
                        due_at=item.get("due_at") or item.get("calculated_due_at"),
                        href="/platform/sla-policies" if platform else "/agency/deadlines",
                    )
                )
        for item in records["booking_handoffs"]:
            if self._norm(item.get("handoff_status")) in {"blocked", "conditional", "ready", "handed_off"} and not item.get("booking_workspace_id"):
                feed.append(
                    self._feed_item(
                        source="accepted_offer_awaiting_booking",
                        item=item,
                        title=item.get("handoff_reference") or "Booking handoff",
                        summary="Accepted offer handoff requires booking follow-up.",
                        status=item.get("handoff_status"),
                        priority="high" if self._norm(item.get("handoff_status")) == "blocked" else "normal",
                        severity="high" if self._norm(item.get("handoff_status")) == "blocked" else "medium",
                        href="/platform/booking-handoffs" if platform else "/agency/booking-handoffs",
                    )
                )
        for item in records["after_sales_cases"]:
            if self._norm(item.get("case_status")) in OPEN_AFTER_SALES_STATUSES:
                feed.append(
                    self._feed_item(
                        source="after_sales_case",
                        item=item,
                        title=item.get("case_title") or item.get("case_reference") or "After-sales case",
                        summary=item.get("case_summary"),
                        status=item.get("case_status"),
                        priority=item.get("case_priority"),
                        severity="high" if self._norm(item.get("case_priority")) in {"urgent", "critical"} else "medium",
                        href="/platform/after-sales" if platform else "/agency/after-sales",
                    )
                )
        for item in records["pilot_readiness_issues"]:
            if self._norm(item.get("issue_status")) in {"open", "in_review", "reopened"}:
                feed.append(
                    self._feed_item(
                        source="pilot_readiness_issue",
                        item=item,
                        title=item.get("title") or item.get("issue_code") or "Pilot readiness issue",
                        summary=item.get("description") or item.get("summary"),
                        status=item.get("issue_status"),
                        priority=item.get("priority") or "normal",
                        severity=item.get("severity") or "medium",
                        href="/platform/pilot-readiness" if platform else "/agency/pilot-readiness",
                    )
                )
        feed.sort(key=lambda item: (-item["urgency_score"], str(item.get("due_at") or ""), str(item.get("created_at") or "")))
        return feed

    def _calendar(self, records: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        for item in records["deadlines"]:
            due_at = item.get("due_at") or item.get("calculated_due_at")
            if due_at:
                events.append(
                    {
                        "id": f"deadline:{item.get('id')}",
                        "event_type": "deadline",
                        "title": item.get("deadline_reference") or item.get("deadline_type") or "Operational deadline",
                        "start": due_at,
                        "status": item.get("status"),
                        "source_entity_type": item.get("source_entity_type"),
                        "source_entity_id": item.get("source_entity_id"),
                        "metadata_only": True,
                    }
                )
        for collection_key, event_type, date_fields in [
            ("trip_workspaces", "trip_departure", ["departure_date", "travel_start_date"]),
            ("flight_workspaces", "flight_departure", ["departure_datetime"]),
        ]:
            for item in records[collection_key]:
                start = next((item.get(field) for field in date_fields if item.get(field)), None)
                if start:
                    events.append(
                        {
                            "id": f"{event_type}:{item.get('id')}",
                            "event_type": event_type,
                            "title": item.get("trip_reference") or item.get("flight_reference") or event_type.replace("_", " "),
                            "start": start,
                            "status": item.get("trip_status") or item.get("flight_status") or item.get("status"),
                            "source_entity_type": collection_key.rstrip("s"),
                            "source_entity_id": item.get("id"),
                            "metadata_only": True,
                        }
                    )
        events.sort(key=lambda item: str(item.get("start") or ""))
        return events

    def _kanban(self, records: dict[str, list[dict[str, Any]]], *, platform: bool = False) -> list[dict[str, Any]]:
        lanes: dict[str, dict[str, Any]] = {}
        for workflow in records["workflow_instances"]:
            state = self._norm(workflow.get("current_state") or "unknown")
            if state not in lanes:
                lanes[state] = {
                    "lane_key": state,
                    "title": self._label(state),
                    "count": 0,
                    "cards": [],
                    "kanban_moves_require_workflow_transitions": True,
                    "uncontrolled_drag_and_drop_disabled": True,
                    "metadata_only": True,
                }
            lanes[state]["cards"].append(
                {
                    "id": workflow.get("id"),
                    "entity_type": workflow.get("entity_type"),
                    "entity_id": workflow.get("entity_id"),
                    "workflow_status": workflow.get("workflow_status"),
                    "active_blocker_count": len(workflow.get("active_blockers_json") or []),
                    "active_warning_count": len(workflow.get("active_warnings_json") or []),
                    "transition_route_required": f"{'/platform' if platform else '/agency'}/operational-workflows?workflow_instance_id={workflow.get('id')}",
                    "guard_enforcement_required": True,
                    "metadata_only": True,
                }
            )
        for lane in lanes.values():
            lane["count"] = len(lane["cards"])
            lane["cards"] = lane["cards"][:25]
        return sorted(lanes.values(), key=lambda lane: lane["title"])

    def _workload(self, records: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        buckets: dict[str, dict[str, Any]] = {}
        for item in records["work_items"]:
            if self._norm(item.get("status")) not in OPEN_WORK_STATUSES:
                continue
            key = item.get("assigned_user_id") or item.get("assigned_team_code") or "unassigned"
            bucket = buckets.setdefault(
                key,
                {
                    "owner_key": key,
                    "assigned_user_id": item.get("assigned_user_id"),
                    "assigned_team_code": item.get("assigned_team_code"),
                    "open_count": 0,
                    "critical_count": 0,
                    "due_soon_count": 0,
                    "overdue_count": 0,
                    "blocked_count": 0,
                    "metadata_only": True,
                },
            )
            bucket["open_count"] += 1
            if self._norm(item.get("severity")) == "critical":
                bucket["critical_count"] += 1
            if self._norm(item.get("sla_status")) == "due_soon":
                bucket["due_soon_count"] += 1
            if self._norm(item.get("sla_status")) in {"overdue", "breached"}:
                bucket["overdue_count"] += 1
            if self._norm(item.get("blocker_status")) == "blocked":
                bucket["blocked_count"] += 1
        return sorted(buckets.values(), key=lambda item: (-item["critical_count"], -item["overdue_count"], -item["open_count"], item["owner_key"]))

    def _timeline(self, records: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        entries = []
        for item in records["workflow_events"]:
            entries.append(
                {
                    "id": item.get("id"),
                    "event_type": item.get("event_type"),
                    "title": item.get("event_code") or item.get("event_type"),
                    "timestamp": item.get("occurred_at") or item.get("created_at"),
                    "source_entity_type": item.get("source_entity_type"),
                    "source_entity_id": item.get("source_entity_id"),
                    "metadata_only": True,
                }
            )
        entries.sort(key=lambda item: str(item.get("timestamp") or ""), reverse=True)
        return entries

    def _feed_item(
        self,
        *,
        source: str,
        item: dict[str, Any],
        title: str,
        summary: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        severity: str | None = None,
        due_at: Any = None,
        href: str,
    ) -> dict[str, Any]:
        return {
            "id": f"{source}:{item.get('id')}",
            "source": source,
            "source_entity_id": item.get("id"),
            "agency_id": item.get("agency_id"),
            "title": title,
            "summary": summary,
            "status": status,
            "priority": priority or "normal",
            "severity": severity or "medium",
            "due_at": due_at,
            "created_at": item.get("created_at"),
            "urgency_score": self._urgency_score(priority=priority, severity=severity, status=status, due_at=due_at),
            "safe_action_link": href,
            "metadata_only": True,
        }

    def _urgency_score(self, priority: str | None, severity: str | None, status: str | None, due_at: Any) -> int:
        priority_score = {"critical": 50, "urgent": 40, "high": 30, "normal": 15, "low": 5}.get(self._norm(priority), 10)
        severity_score = {"critical": 40, "high": 25, "medium": 10, "low": 3}.get(self._norm(severity), 5)
        status_score = {"blocked": 40, "overdue": 35, "breached": 35, "due_soon": 20, "waiting": 10}.get(self._norm(status), 0)
        due_score = 0
        parsed = self._parse_dt(due_at)
        if parsed:
            now = self._now()
            if parsed < now:
                due_score = 35
            elif parsed <= now + timedelta(hours=24):
                due_score = 20
            elif parsed <= now + timedelta(hours=72):
                due_score = 10
        return priority_score + severity_score + status_score + due_score

    def _departure_buckets(self, trips: list[dict[str, Any]], flights: list[dict[str, Any]], now: datetime) -> dict[str, int]:
        departures = []
        for item in trips:
            departures.append(self._parse_dt(item.get("departure_date") or item.get("travel_start_date")))
        for item in flights:
            departures.append(self._parse_dt(item.get("departure_datetime")))
        departures = [value for value in departures if value and value >= now]
        return {
            "24h": len([value for value in departures if value <= now + timedelta(hours=24)]),
            "48h": len([value for value in departures if value <= now + timedelta(hours=48)]),
            "72h": len([value for value in departures if value <= now + timedelta(hours=72)]),
        }

    def _safe_action_links(self, agency_id: str | None, platform: bool) -> list[dict[str, str]]:
        base = "/platform" if platform else "/agency"
        return [
            {"label": "Work queue", "href": f"{base}/work-queues" if platform else f"{base}/work-queue"},
            {"label": "Deadlines", "href": f"{base}/sla-policies" if platform else f"{base}/deadlines"},
            {"label": "Operational workflows", "href": f"{base}/operational-workflows"},
            {"label": "Booking handoffs", "href": f"{base}/booking-handoffs"},
            {"label": "After-sales", "href": f"{base}/after-sales"},
            {"label": "Pilot readiness", "href": f"{base}/pilot-readiness"},
        ]

    def _parse_dt(self, value: Any) -> datetime | None:
        if not value:
            return None
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        text = str(value)
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            try:
                return datetime.fromisoformat(f"{text}T00:00:00+00:00")
            except ValueError:
                return None

    def _norm(self, value: Any) -> str:
        return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")

    def _label(self, value: Any) -> str:
        return self._norm(value).replace("_", " ").title()

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)
