from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from typing import Any

from database import Database
from persistence_query import MAXIMUM_QUERY_LIMIT, PaginationRequest
from persistence_repository import PersistenceRepository
from models import (
    OperationalAssignmentEvent,
    OperationalBulkAssignmentRequest,
    OperationalQueueDefinition,
    OperationalQueueDefinitionCreate,
    OperationalQueueDefinitionUpdate,
    OperationalQueueView,
    OperationalQueueViewCreate,
    OperationalQueueViewUpdate,
    OperationalWorkItem,
    OperationalWorkItemActionRequest,
    OperationalWorkItemCreate,
    OperationalWorkItemGenerateRequest,
    OperationalWorkItemUpdate,
    new_id,
)
from services.operational_collaboration_service import OperationalCollaborationService
from services.authorization_service import agency_permissions
from services.governed_automation_contract import (
    TASK_TYPE_CATALOGUE,
    bounded_safe_snapshot,
    task_type_contract,
)


from build_phase import CURRENT_BUILD_PHASE

PHASE_LABEL = CURRENT_BUILD_PHASE

OPERATIONAL_WORK_ITEMS_COLLECTION = "operational_work_items"
OPERATIONAL_QUEUE_DEFINITIONS_COLLECTION = "operational_queue_definitions"
OPERATIONAL_ASSIGNMENT_EVENTS_COLLECTION = "operational_assignment_events"
OPERATIONAL_QUEUE_VIEWS_COLLECTION = "operational_queue_views"

WORK_ITEM_STATUSES = [
    "open",
    "assigned",
    "in_progress",
    "waiting",
    "blocked",
    "approval_required",
    "completed",
    "cancelled",
    "overdue",
]
WORK_ITEM_PRIORITIES = ["low", "normal", "high", "urgent", "critical"]
WORK_ITEM_SEVERITIES = ["low", "medium", "high", "critical"]
BLOCKER_STATUSES = [
    "not_blocked",
    "blocked",
    "waiting_client",
    "waiting_airline_supplier",
    "waiting_documents",
    "waiting_approval",
    "waiting_payment",
    "manual_review",
]
SLA_STATUSES = ["on_track", "due_soon", "overdue", "breached", "paused", "completed", "unknown"]
ASSIGNMENT_EVENT_TYPES = [
    "created",
    "generated",
    "synchronized",
    "assigned_to_self",
    "assigned",
    "reassigned",
    "unassigned",
    "accepted",
    "released",
    "in_progress",
    "blocked",
    "completed",
    "reopened",
    "bulk_assigned",
    "waiting",
    "cancelled",
    "approval_requested",
    "approval_completed",
    "escalated",
    "blocker_resolved",
    "queue_changed",
]
WORK_ITEM_TYPES = [
    "new_request_triage",
    "incomplete_passenger_data",
    "incomplete_service_data",
    "offer_preparation_required",
    "offer_awaiting_response",
    "accepted_offer_awaiting_booking",
    "booking_awaiting_ticketing",
    "service_approval_document_requirement",
    "policy_gap_manual_review",
    "knowledge_issue",
    "disruption",
    "overdue_task",
    "task_deadline",
    "document_missing_or_expiring",
    "pilot_readiness_blocker",
    "workflow_blocker",
    "claim_service_case",
    "manual",
    "approval_request",
    "reminder",
    "escalation",
    *sorted(TASK_TYPE_CATALOGUE),
]
WORK_ITEM_TRANSITIONS: dict[str, set[str]] = {
    "open": {"assigned", "in_progress", "waiting", "blocked", "approval_required", "completed", "cancelled", "overdue"},
    "assigned": {"in_progress", "waiting", "blocked", "approval_required", "completed", "cancelled", "open", "overdue"},
    "in_progress": {"waiting", "blocked", "approval_required", "completed", "cancelled", "overdue"},
    "waiting": {"open", "assigned", "in_progress", "blocked", "approval_required", "cancelled", "overdue"},
    "blocked": {"open", "assigned", "in_progress", "approval_required", "cancelled", "overdue"},
    "approval_required": {"open", "assigned", "in_progress", "completed", "cancelled", "blocked"},
    "overdue": {"assigned", "in_progress", "waiting", "blocked", "approval_required", "completed", "cancelled"},
    "completed": {"open"},
    "cancelled": {"open"},
}
CANONICAL_QUEUE_CODES = [
    "unassigned",
    "my_work",
    "team_queue",
    "urgent_critical",
    "due_soon",
    "overdue",
    "blocked",
    "waiting_client",
    "waiting_airline_supplier",
    "waiting_documents",
    "waiting_approval",
    "waiting_payment",
    "disruption_queue",
    "service_case_queue",
    "knowledge_gap_queue",
    "workflow_blocker_queue",
]

DEFAULT_QUEUE_DEFINITIONS: list[dict[str, Any]] = [
    {
        "queue_code": "unassigned",
        "name": "Unassigned",
        "description": "Open operational work not assigned to an agent.",
        "filter_json": {"assigned_user_id": None, "active_only": True},
        "sort_json": {"priority": "desc", "sla_status": "asc", "due_at": "asc", "severity": "desc", "created_at": "asc"},
        "assignment_strategy": "manual",
    },
    {
        "queue_code": "my_work",
        "name": "My Work",
        "description": "Work assigned to the current agent.",
        "filter_json": {"assigned_to_current_user": True, "active_only": True},
        "sort_json": {"priority": "desc", "due_at": "asc"},
        "assignment_strategy": "agent_owned",
    },
    {
        "queue_code": "team_queue",
        "name": "Team Queue",
        "description": "Work assigned to a team code.",
        "filter_json": {"assigned_team_code": "selected_team", "active_only": True},
        "sort_json": {"priority": "desc", "sla_status": "asc", "due_at": "asc"},
        "assignment_strategy": "team_manual",
    },
    {
        "queue_code": "urgent_critical",
        "name": "Urgent / Critical",
        "description": "High-pressure work ordered by impact and due date.",
        "filter_json": {"priority": ["urgent", "critical"], "severity": ["high", "critical"], "active_only": True},
        "sort_json": {"priority": "desc", "severity": "desc", "due_at": "asc"},
        "assignment_strategy": "manual",
    },
    {
        "queue_code": "due_soon",
        "name": "Due Soon",
        "description": "Active work with due-soon SLA or due dates.",
        "filter_json": {"sla_status": "due_soon", "active_only": True},
        "sort_json": {"due_at": "asc", "priority": "desc"},
        "assignment_strategy": "manual",
    },
    {
        "queue_code": "overdue",
        "name": "Overdue",
        "description": "Active work whose due date or SLA has passed.",
        "filter_json": {"sla_status": ["overdue", "breached"], "active_only": True},
        "sort_json": {"due_at": "asc", "priority": "desc"},
        "assignment_strategy": "manual",
    },
    {
        "queue_code": "blocked",
        "name": "Blocked",
        "description": "Work requiring blocker review.",
        "filter_json": {"blocker_status": "blocked", "active_only": True},
        "sort_json": {"severity": "desc", "created_at": "asc"},
        "assignment_strategy": "manual",
    },
    {
        "queue_code": "waiting_documents",
        "name": "Waiting Documents",
        "description": "Document-dependent work items.",
        "filter_json": {"blocker_status": "waiting_documents", "active_only": True},
        "sort_json": {"due_at": "asc"},
        "assignment_strategy": "manual",
    },
    {
        "queue_code": "disruption_queue",
        "name": "Disruptions",
        "description": "Disruption and urgent service recovery items.",
        "filter_json": {"work_item_type": "disruption", "active_only": True},
        "sort_json": {"priority": "desc", "due_at": "asc"},
        "assignment_strategy": "manual",
    },
    {
        "queue_code": "knowledge_gap_queue",
        "name": "Knowledge Gaps",
        "description": "Policy gaps, knowledge issues, and manual review items.",
        "filter_json": {"work_item_type": ["policy_gap_manual_review", "knowledge_issue"], "active_only": True},
        "sort_json": {"severity": "desc", "created_at": "asc"},
        "assignment_strategy": "manual",
    },
    {
        "queue_code": "workflow_blocker_queue",
        "name": "Workflow Blockers",
        "description": "Blocked workflow orchestration items.",
        "filter_json": {"work_item_type": "workflow_blocker", "active_only": True},
        "sort_json": {"severity": "desc", "created_at": "asc"},
        "assignment_strategy": "manual",
    },
]


class AgentWorkQueueError(ValueError):
    pass


class AgentWorkQueueService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def platform_dashboard(self, **filters: Any) -> dict[str, Any]:
        items = await self.list_work_items(**filters)
        definitions = await self.list_queue_definitions(agency_id=filters.get("agency_id"), include_defaults=True)
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "queue_definitions": definitions,
            "queue_views": await self.list_queue_views(agency_id=filters.get("agency_id")),
            "summary": self.summarize_counts(items),
            "queue_summary": self.queue_summary(items),
            "ordering": self.ordering_metadata(),
            "generation_rules": self.generation_rules(),
            "platform_governance_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_dashboard(self, agency_id: str, user: dict, **filters: Any) -> dict[str, Any]:
        filters["agency_id"] = agency_id
        items = await self.list_work_items(current_user_id=user.get("id"), **filters)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "queue_definitions": await self.list_queue_definitions(agency_id=agency_id, include_defaults=True),
            "queue_views": await self.list_queue_views(agency_id=agency_id, owner_user_id=user.get("id")),
            "summary": self.summarize_counts(items),
            "queue_summary": self.queue_summary(items),
            "ordering": self.ordering_metadata(),
            "generation_rules": self.generation_rules(),
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def list_work_items(
        self,
        *,
        agency_id: str | None = None,
        queue_code: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        severity: str | None = None,
        work_item_type: str | None = None,
        source_entity_type: str | None = None,
        source_entity_id: str | None = None,
        assigned_user_id: str | None = None,
        assigned_team_code: str | None = None,
        blocker_status: str | None = None,
        sla_status: str | None = None,
        include_completed: bool = False,
        current_user_id: str | None = None,
        **_: Any,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if status:
            filters["status"] = self._norm(status)
        if priority:
            filters["priority"] = self._norm(priority)
        if severity:
            filters["severity"] = self._norm(severity)
        if work_item_type:
            filters["work_item_type"] = self._norm(work_item_type)
        if source_entity_type:
            filters["source_entity_type"] = self._norm(source_entity_type)
        if source_entity_id:
            filters["source_entity_id"] = source_entity_id
        if assigned_user_id:
            filters["assigned_user_id"] = assigned_user_id
        if assigned_team_code:
            filters["assigned_team_code"] = self._norm(assigned_team_code)
        if blocker_status:
            filters["blocker_status"] = self._norm(blocker_status)
        if sla_status:
            filters["sla_status"] = self._norm(sla_status)

        repository = PersistenceRepository(self.db)
        query = {
            "collection_name": OPERATIONAL_WORK_ITEMS_COLLECTION,
            "filters": filters or None,
            "sort_field": "due_at",
            "sort_direction": "asc",
            "pagination": PaginationRequest.build(limit=MAXIMUM_QUERY_LIMIT),
        }
        page = await (
            repository.find_agency_records(agency_id=agency_id, **query)
            if agency_id
            else repository.find_platform_records(**query)
        )
        items = page.items
        if not include_completed:
            items = [item for item in items if item.get("status") not in {"completed", "cancelled"}]
        if queue_code:
            items = [item for item in items if self._queue_matches(item, queue_code, current_user_id=current_user_id)]
        items.sort(key=self._ordering_key)
        return [await self._work_item_projection(item) for item in items]

    async def get_work_item(self, work_item_id: str, agency_id: str | None = None) -> dict[str, Any]:
        return await self._work_item_projection(await self._require_work_item(work_item_id, agency_id=agency_id))

    async def create_work_item(
        self,
        payload: OperationalWorkItemCreate | dict[str, Any],
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        data = self._payload(payload)
        if agency_id:
            data["agency_id"] = agency_id
        self._validate_work_item_payload(data)
        data.setdefault("work_item_code", self._work_item_code())
        data.setdefault("source_fingerprint", self._fingerprint(data))
        if data.get("assigned_user_id"):
            await self._validate_assignee(
                data["agency_id"],
                data["assigned_user_id"],
                data["work_item_type"],
            )
            data["status"] = "assigned" if data.get("status") == "open" else data.get("status")
        data.setdefault("primary_entity_type", data["source_entity_type"])
        data.setdefault("primary_entity_id", data["source_entity_id"])
        data.setdefault(
            "entity_references",
            [
                {
                    "entity_type": data["source_entity_type"],
                    "entity_id": data["source_entity_id"],
                }
            ],
        )
        data["created_by"] = user.get("id")
        data["updated_by"] = user.get("id")
        data["version"] = 1
        data["internal_context_json"] = bounded_safe_snapshot(
            data.get("internal_context_json") or {}, max_depth=4
        )
        data["metadata"] = bounded_safe_snapshot(
            data.get("metadata") or {}, max_depth=3
        )
        record = OperationalWorkItem(**data).model_dump(mode="json")
        created = await self.db.collection(OPERATIONAL_WORK_ITEMS_COLLECTION).insert_one(record)
        await self._record_event(created, "created", user, reason="Work item created.", payload={"source": self._source_ref(created)})
        return {"phase": PHASE_LABEL, "work_item": await self._work_item_projection(created), "metadata_only": True, **self.safety_flags()}

    async def update_work_item(
        self,
        work_item_id: str,
        payload: OperationalWorkItemUpdate | dict[str, Any],
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_work_item(work_item_id, agency_id=agency_id)
        updates = self._payload(payload, exclude_unset=True)
        if not updates:
            raise AgentWorkQueueError("No work item metadata updates were provided.")
        expected_version = updates.pop("expected_version", None)
        self._check_expected_version(existing, expected_version)
        allowed_fields = {
            "title",
            "description",
            "summary",
            "priority",
            "severity",
            "due_at",
            "reminder_at",
            "escalation_at",
            "sla_status",
            "client_impact",
            "checklist",
            "metadata",
        }
        unsupported = sorted(set(updates) - allowed_fields)
        if unsupported:
            raise AgentWorkQueueError(
                "Assignment, queue, status, source, and ownership changes must "
                "use a governed work-item action."
            )
        merged = {**existing, **updates}
        self._validate_work_item_payload(merged, partial=True)
        if "metadata" in updates:
            updates["metadata"] = bounded_safe_snapshot(
                updates.get("metadata") or {}, max_depth=3
            )
        updates["updated_by"] = user.get("id")
        updates["version"] = int(existing.get("version") or 1) + 1
        version_filter = {"id": existing["id"]}
        if "version" in existing:
            version_filter["version"] = existing["version"]
        updated = await self.db.collection(OPERATIONAL_WORK_ITEMS_COLLECTION).update_one(
            version_filter, updates
        )
        if not updated:
            raise AgentWorkQueueError("Work item version conflict.")
        await self._record_event(updated, "synchronized", user, reason="Work item metadata updated.", payload={"updated_fields": sorted(updates)})
        return {"phase": PHASE_LABEL, "work_item": await self._work_item_projection(updated), "metadata_only": True, **self.safety_flags()}

    async def generate_work_item(
        self,
        payload: OperationalWorkItemGenerateRequest | dict[str, Any],
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        data = self._payload(payload)
        if agency_id:
            data["agency_id"] = agency_id
        self._validate_work_item_payload(data)
        data.setdefault("status", "open")
        data.setdefault("work_item_code", self._work_item_code())
        data.setdefault("primary_entity_type", data["source_entity_type"])
        data.setdefault("primary_entity_id", data["source_entity_id"])
        data.setdefault(
            "entity_references",
            [
                {
                    "entity_type": data["source_entity_type"],
                    "entity_id": data["source_entity_id"],
                }
            ],
        )
        if data.get("assigned_user_id"):
            await self._validate_assignee(
                data["agency_id"],
                data["assigned_user_id"],
                data["work_item_type"],
            )
            if data["status"] == "open":
                data["status"] = "assigned"
        source_snapshot = bounded_safe_snapshot(
            data.pop("source_snapshot_json", {}), max_depth=3
        )
        generation_reason = data.pop("generation_reason", None)
        data["internal_context_json"] = {
            **(data.get("internal_context_json") or {}),
            "source_snapshot_json": source_snapshot,
            "generation_reason": generation_reason,
            "idempotent_generation": True,
        }
        data.setdefault("source_fingerprint", self._fingerprint(data))
        existing = await self.db.collection(OPERATIONAL_WORK_ITEMS_COLLECTION).find_one({"source_fingerprint": data["source_fingerprint"]})
        if existing:
            updates = {
                "summary": data.get("summary") or existing.get("summary"),
                "priority": self._norm(data.get("priority") or existing.get("priority") or "normal"),
                "severity": self._norm(data.get("severity") or existing.get("severity") or "medium"),
                "queue_code": self._norm(data.get("queue_code") or existing.get("queue_code") or "unassigned"),
                "sla_status": self._norm(data.get("sla_status")) if data.get("sla_status") else existing.get("sla_status"),
                "blocker_status": self._norm(data.get("blocker_status") or existing.get("blocker_status") or "not_blocked"),
                "internal_context_json": {**(existing.get("internal_context_json") or {}), **(data.get("internal_context_json") or {})},
                "compatibility_mapping_json": {**(existing.get("compatibility_mapping_json") or {}), **(data.get("compatibility_mapping_json") or {})},
                "updated_by": user.get("id"),
                "version": int(existing.get("version") or 1) + 1,
            }
            version_filter = {"id": existing["id"]}
            if "version" in existing:
                version_filter["version"] = existing["version"]
            updated = await self.db.collection(OPERATIONAL_WORK_ITEMS_COLLECTION).update_one(
                version_filter, updates
            )
            await self._record_event(updated or existing, "synchronized", user, reason="Idempotent work-item generation reused existing record.", payload={"source_fingerprint": data["source_fingerprint"]})
            return {
                "phase": PHASE_LABEL,
                "work_item": await self._work_item_projection(updated or existing),
                "idempotent_reused": True,
                "metadata_only": True,
                **self.safety_flags(),
            }
        data["created_by"] = user.get("id")
        data["updated_by"] = user.get("id")
        data["version"] = 1
        data["metadata"] = bounded_safe_snapshot(
            data.get("metadata") or {}, max_depth=3
        )
        record = OperationalWorkItem(**data).model_dump(mode="json")
        created = await self.db.collection(OPERATIONAL_WORK_ITEMS_COLLECTION).insert_one(record)
        await self._record_event(created, "generated", user, reason=generation_reason or "Work item generated from source metadata.", payload={"source_fingerprint": data["source_fingerprint"]})
        return {
            "phase": PHASE_LABEL,
            "work_item": await self._work_item_projection(created),
            "idempotent_reused": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def sync_sources(self, agency_id: str, user: dict) -> dict[str, Any]:
        generated: list[dict[str, Any]] = []
        generated.extend(await self._sync_workflow_events(agency_id, user))
        generated.extend(await self._sync_workflow_blockers(agency_id, user))
        generated.extend(await self._sync_request_tasks(agency_id, user))
        generated.extend(await self._sync_travel_requests(agency_id, user))
        generated.extend(await self._sync_request_workspaces(agency_id, user))
        generated.extend(await self._sync_offer_workspaces(agency_id, user))
        generated.extend(await self._sync_booking_workspaces(agency_id, user))
        generated.extend(await self._sync_document_workspaces(agency_id, user))
        generated.extend(await self._sync_pilot_readiness_issues(agency_id, user))
        reused = len([item for item in generated if item.get("idempotent_reused")])
        created = len(generated) - reused
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "created_count": created,
            "reused_count": reused,
            "generated_count": len(generated),
            "generated": generated,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def apply_action(
        self,
        work_item_id: str,
        action: str,
        payload: OperationalWorkItemActionRequest | dict[str, Any],
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        item = await self._require_work_item(work_item_id, agency_id=agency_id)
        data = self._payload(payload)
        action = self._norm(action)
        self._check_expected_version(item, data.get("expected_version"))
        now = self._now()
        updates: dict[str, Any] = {"updated_by": user.get("id")}
        event_type = action
        target_status: str | None = None

        if action == "assign_self":
            await self._validate_assignee(
                item["agency_id"], user.get("id"), item["work_item_type"]
            )
            updates["assigned_user_id"] = user.get("id")
            updates["status"] = "assigned"
            updates["accepted_at"] = now
            updates["accepted_by_user_id"] = user.get("id")
            updates["assignment_explanation"] = (
                "Eligible Agency member claimed the work item."
            )
            target_status = "assigned"
            event_type = "assigned_to_self"
        elif action in {"assign", "reassign"}:
            if not data.get("to_user_id") and not data.get("to_team_code"):
                raise AgentWorkQueueError("Assignment requires to_user_id or to_team_code metadata.")
            if data.get("to_user_id"):
                await self._validate_assignee(
                    item["agency_id"],
                    data["to_user_id"],
                    item["work_item_type"],
                )
            updates["assigned_user_id"] = data.get("to_user_id")
            updates["assigned_team_code"] = self._norm(data.get("to_team_code")) if data.get("to_team_code") else item.get("assigned_team_code")
            updates["assignment_explanation"] = (
                data.get("reason") or "Manual governed assignment."
            )
            if item.get("status") in {"open", "reopened"}:
                updates["status"] = "assigned"
                target_status = "assigned"
            event_type = "reassigned" if item.get("assigned_user_id") or action == "reassign" else "assigned"
        elif action == "unassign":
            updates["assigned_user_id"] = None
            updates["assigned_team_code"] = None
            updates["status"] = "open"
            updates["assignment_explanation"] = data.get("reason") or "Work item returned to the unassigned queue."
            target_status = "open"
            event_type = "unassigned"
        elif action == "accept":
            await self._validate_assignee(
                item["agency_id"],
                item.get("assigned_user_id") or user.get("id"),
                item["work_item_type"],
            )
            updates["assigned_user_id"] = item.get("assigned_user_id") or user.get("id")
            updates["status"] = "assigned"
            updates["accepted_at"] = now
            updates["accepted_by_user_id"] = user.get("id")
            target_status = "assigned"
            event_type = "accepted"
        elif action == "release":
            updates["assigned_user_id"] = None
            updates["status"] = "open"
            updates["released_at"] = now
            target_status = "open"
            event_type = "released"
        elif action in {"in_progress", "mark_in_progress", "start"}:
            updates["status"] = "in_progress"
            updates["started_at"] = item.get("started_at") or now
            target_status = "in_progress"
            event_type = "in_progress"
        elif action == "wait":
            if not str(data.get("reason") or "").strip():
                raise AgentWorkQueueError("Waiting requires an operational reason.")
            updates["status"] = "waiting"
            updates["blocker_status"] = self._norm(
                data.get("blocker_status") or "manual_review"
            )
            updates["blocked_reason"] = data["reason"]
            target_status = "waiting"
            event_type = "waiting"
        elif action == "block":
            if not str(data.get("reason") or "").strip():
                raise AgentWorkQueueError("Blocking requires an operational reason.")
            updates["status"] = "blocked"
            updates["blocker_status"] = self._norm(data.get("blocker_status") or "blocked")
            updates["blocked_at"] = now
            updates["blocked_reason"] = data.get("reason")
            updates["blockers"] = [
                *(item.get("blockers") or []),
                {
                    "blocker_type": updates["blocker_status"],
                    "reason": data["reason"],
                    "source": "manual",
                    "created_by": user.get("id"),
                    "created_at": now,
                    "resolved": False,
                },
            ]
            target_status = "blocked"
            event_type = "blocked"
        elif action == "resolve_blocker":
            if not str(data.get("reason") or "").strip():
                raise AgentWorkQueueError("Resolving a blocker requires a reason.")
            updates["blockers"] = [
                (
                    blocker
                    if blocker.get("resolved")
                    else {
                        **blocker,
                        "resolved": True,
                        "resolved_at": now,
                        "resolved_by": user.get("id"),
                        "resolution_reason": data["reason"],
                    }
                )
                for blocker in item.get("blockers") or []
            ]
            updates["blocker_status"] = "not_blocked"
            updates["blocked_reason"] = None
            updates["status"] = "assigned" if item.get("assigned_user_id") else "open"
            target_status = updates["status"]
            event_type = "blocker_resolved"
        elif action == "request_approval":
            if not data.get("approval_type") or not data.get("required_permission"):
                raise AgentWorkQueueError(
                    "Approval request requires approval_type and required_permission."
                )
            updates.update(
                {
                    "status": "approval_required",
                    "blocker_status": "waiting_approval",
                    "approval_required": True,
                    "approval_type": self._norm(data["approval_type"]),
                    "approval_status": "requested",
                    "approval_required_permission": data["required_permission"],
                    "approval_requested_by": user.get("id"),
                    "approval_requested_at": now,
                    "approval_evidence_snapshot": data.get("evidence_snapshot") or {},
                    "human_confirmation_required": True,
                }
            )
            target_status = "approval_required"
            event_type = "approval_requested"
        elif action == "complete":
            await self._assert_completion_allowed(item, user, data)
            updates["status"] = "completed"
            updates["completed_at"] = now
            updates["completed_by"] = user.get("id")
            updates["completion_evidence"] = data.get("completion_evidence") or {}
            updates["sla_status"] = "completed"
            target_status = "completed"
            event_type = "completed"
        elif action == "reopen":
            updates["status"] = "open"
            updates["completed_at"] = None
            updates["completed_by"] = None
            updates["reopened_at"] = now
            target_status = "open"
            event_type = "reopened"
        elif action == "cancel":
            if not str(data.get("reason") or "").strip():
                raise AgentWorkQueueError("Cancellation requires a reason.")
            updates.update(
                {
                    "status": "cancelled",
                    "cancelled_at": now,
                    "cancelled_by": user.get("id"),
                    "cancellation_reason": data["reason"],
                }
            )
            target_status = "cancelled"
            event_type = "cancelled"
        elif action == "escalate":
            if not str(data.get("reason") or "").strip():
                raise AgentWorkQueueError("Escalation requires an operational reason.")
            priority_order = ["low", "normal", "high", "urgent", "critical"]
            current = self._norm(item.get("priority") or "normal")
            index = min(priority_order.index(current) + 1, len(priority_order) - 1)
            updates["priority"] = priority_order[index]
            updates["escalation_at"] = now
            updates["queue_code"] = "urgent_critical"
            updates["queue_key"] = "urgent_critical"
            event_type = "escalated"
        elif action == "place_in_queue":
            queue_code = self._norm(
                data.get("queue_code")
                or (data.get("metadata") or {}).get("queue_code")
            )
            if queue_code not in CANONICAL_QUEUE_CODES:
                raise AgentWorkQueueError("A canonical queue_code is required.")
            updates["queue_code"] = queue_code
            updates["queue_key"] = queue_code
            event_type = "queue_changed"
        else:
            raise AgentWorkQueueError(f"Unsupported work queue action metadata: {action}.")

        if data.get("due_at"):
            if not str(data.get("reason") or "").strip():
                raise AgentWorkQueueError(
                    "Changing a work-item deadline requires a reason."
                )
            updates["due_at"] = data["due_at"]
        if data.get("internal_context_json"):
            updates["internal_context_json"] = {**(item.get("internal_context_json") or {}), **data["internal_context_json"]}
        if target_status:
            self._assert_transition(item.get("status") or "open", target_status)
        updates["version"] = int(item.get("version") or 1) + 1
        version_filter = {"id": item["id"]}
        if "version" in item:
            version_filter["version"] = item["version"]
        updated = await self.db.collection(OPERATIONAL_WORK_ITEMS_COLLECTION).update_one(version_filter, updates, allow_agency_update=True)
        if not updated:
            raise AgentWorkQueueError("Work item version conflict.")
        await self._record_event(
            updated,
            event_type,
            user,
            reason=data.get("reason"),
            from_user_id=item.get("assigned_user_id"),
            to_user_id=updates.get("assigned_user_id"),
            from_team_code=item.get("assigned_team_code"),
            to_team_code=updates.get("assigned_team_code"),
            payload={"action": action, "previous_status": item.get("status"), "next_status": updated.get("status"), "metadata": data.get("metadata") or {}},
        )
        if event_type == "completed":
            from services.task_automation_dependency_service import (
                TaskAutomationDependencyService,
            )

            await TaskAutomationDependencyService(self.db).evaluate_dependencies(
                item["agency_id"], user
            )
        return {"phase": PHASE_LABEL, "work_item": await self._work_item_projection(updated), "action": event_type, "metadata_only": True, **self.safety_flags()}

    async def synchronize_dependency_state(
        self,
        work_item_id: str,
        *,
        agency_id: str,
        blocked: bool,
        dependency_ids: list[str],
        dependency_blockers: list[dict[str, Any]],
        user: dict,
    ) -> dict[str, Any]:
        item = await self._require_work_item(work_item_id, agency_id=agency_id)
        now = self._now()
        existing_blockers = item.get("blockers") or []
        non_dependency_blockers = [
            blocker
            for blocker in existing_blockers
            if blocker.get("blocker_type") != "mandatory_dependency"
        ]
        if blocked:
            if item.get("status") in {
                "completed",
                "cancelled",
                "approval_required",
            }:
                return item
            normalized_dependency_blockers = sorted(
                dependency_blockers,
                key=lambda blocker: (
                    str(blocker.get("dependency_id") or ""),
                    str(blocker.get("predecessor_task_id") or ""),
                ),
            )
            updates = {
                "status": "blocked",
                "blocker_status": "blocked",
                "dependency_ids": sorted(set(dependency_ids)),
                "blockers": [
                    *non_dependency_blockers,
                    *normalized_dependency_blockers,
                ],
                "blocked_at": item.get("blocked_at") or now,
                "blocked_reason": (
                    "Mandatory work-item dependency is incomplete."
                ),
                "version": int(item.get("version") or 1) + 1,
                "updated_by": user.get("id"),
            }
            event_type = "dependency_blocked"
            reason = updates["blocked_reason"]
        else:
            resolved_dependency_blockers = [
                (
                    blocker
                    if blocker.get("resolved")
                    else {
                        **blocker,
                        "resolved": True,
                        "resolved_at": now,
                        "resolved_by": user.get("id"),
                        "resolution_reason": (
                            "Mandatory predecessor completion satisfied the "
                            "dependency."
                        ),
                    }
                )
                for blocker in existing_blockers
                if blocker.get("blocker_type") == "mandatory_dependency"
            ]
            active_non_dependency = [
                blocker
                for blocker in non_dependency_blockers
                if not blocker.get("resolved")
            ]
            remains_blocked = bool(active_non_dependency)
            updates = {
                "status": (
                    "blocked"
                    if remains_blocked
                    else (
                        "assigned"
                        if item.get("assigned_user_id")
                        else "open"
                    )
                ),
                "blocker_status": (
                    item.get("blocker_status") or "blocked"
                    if remains_blocked
                    else "not_blocked"
                ),
                "blockers": [
                    *non_dependency_blockers,
                    *resolved_dependency_blockers,
                ],
                "blocked_reason": (
                    item.get("blocked_reason") if remains_blocked else None
                ),
                "version": int(item.get("version") or 1) + 1,
                "updated_by": user.get("id"),
            }
            event_type = "dependency_satisfied"
            reason = (
                "Mandatory predecessor completion satisfied the dependency."
            )
        target_status = updates["status"]
        self._assert_transition(item.get("status") or "open", target_status)
        updated = await self.db.collection(
            OPERATIONAL_WORK_ITEMS_COLLECTION
        ).update_one(
            {
                "agency_id": agency_id,
                "id": item["id"],
                "version": item.get("version", 1),
            },
            updates,
            allow_agency_update=True,
        )
        if not updated:
            raise AgentWorkQueueError("Work item version conflict.")
        await self._record_event(
            updated,
            event_type,
            user,
            reason=reason,
            payload={
                "dependency_ids": sorted(set(dependency_ids)),
                "previous_status": item.get("status"),
                "next_status": updated.get("status"),
            },
        )
        return updated

    async def record_approval_decision(
        self,
        work_item_id: str,
        *,
        agency_id: str,
        decision: str,
        reason: str,
        evidence_snapshot: dict[str, Any],
        user: dict,
        expected_version: int | None = None,
    ) -> dict[str, Any]:
        item = await self._require_work_item(work_item_id, agency_id=agency_id)
        self._check_expected_version(item, expected_version)
        now = self._now()
        target_status = (
            "completed" if decision in {"approved", "rejected"} else "cancelled"
        )
        self._assert_transition(item.get("status") or "approval_required", target_status)
        decision_evidence = bounded_safe_snapshot(evidence_snapshot)
        updates = {
            "approval_status": decision,
            "approval_decision": decision,
            "approval_decision_reason": reason,
            "approval_decided_by": user.get("id"),
            "approval_decided_at": now,
            "approval_evidence_snapshot": {
                **(item.get("approval_evidence_snapshot") or {}),
                "decision_evidence": decision_evidence,
            },
            "status": target_status,
            "blocker_status": "not_blocked",
            "completed_at": (
                now if decision in {"approved", "rejected"} else None
            ),
            "completed_by": (
                user.get("id")
                if decision in {"approved", "rejected"}
                else None
            ),
            "completion_evidence": {
                "approval_decision": decision,
                "decision_evidence": decision_evidence,
            },
            "version": int(item.get("version") or 1) + 1,
            "updated_by": user.get("id"),
        }
        updated = await self.db.collection(
            OPERATIONAL_WORK_ITEMS_COLLECTION
        ).update_one(
            {
                "agency_id": agency_id,
                "id": item["id"],
                "version": item.get("version", 1),
            },
            updates,
            allow_agency_update=True,
        )
        if not updated:
            raise AgentWorkQueueError("Approval version conflict.")
        await self._record_event(
            updated,
            "approval_completed",
            user,
            reason=reason,
            payload={
                "decision": decision,
                "previous_status": item.get("status"),
                "next_status": target_status,
                "underlying_action_executed": False,
            },
        )
        return updated

    async def route_assignment(
        self,
        work_item_id: str,
        *,
        strategy: str,
        user: dict,
        agency_id: str,
        fixed_user_id: str | None = None,
        fixed_team_code: str | None = None,
        parent_owner_user_id: str | None = None,
        reason: str,
        expected_version: int | None = None,
    ) -> dict[str, Any]:
        item = await self._require_work_item(work_item_id, agency_id=agency_id)
        self._check_expected_version(item, expected_version)
        strategy = self._norm(strategy)
        if strategy not in {
            "fixed_user",
            "fixed_team",
            "least_open_eligible",
            "round_robin",
            "retain_current_owner",
            "parent_entity_owner",
            "manual_assignment_required",
        }:
            raise AgentWorkQueueError("Unsupported governed assignment strategy.")
        if not str(reason or "").strip():
            raise AgentWorkQueueError("Assignment routing requires an explanation.")

        target_user_id: str | None = None
        target_team_code: str | None = None
        explanation = reason.strip()
        if strategy == "fixed_user":
            target_user_id = fixed_user_id
        elif strategy == "fixed_team":
            target_team_code = self._norm(fixed_team_code)
            if not target_team_code:
                raise AgentWorkQueueError("Fixed-team routing requires a team code.")
        elif strategy == "retain_current_owner":
            target_user_id = item.get("assigned_user_id")
            target_team_code = item.get("assigned_team_code")
        elif strategy == "parent_entity_owner":
            target_user_id = parent_owner_user_id
        elif strategy == "manual_assignment_required":
            return await self.apply_action(
                work_item_id,
                "place_in_queue",
                {
                    "queue_code": "unassigned",
                    "reason": explanation,
                    "expected_version": expected_version,
                    "metadata": {
                        "assignment_strategy": strategy,
                        "assignment_unresolved": True,
                    },
                },
                user,
                agency_id=agency_id,
            )
        else:
            eligible = await self._eligible_assignees(
                agency_id, item["work_item_type"]
            )
            if not eligible:
                return await self.apply_action(
                    work_item_id,
                    "place_in_queue",
                    {
                        "queue_code": "unassigned",
                        "reason": explanation,
                        "expected_version": expected_version,
                        "metadata": {
                            "assignment_strategy": strategy,
                            "assignment_unresolved": True,
                        },
                    },
                    user,
                    agency_id=agency_id,
                )
            if strategy == "least_open_eligible":
                active_items = await self.db.collection(
                    OPERATIONAL_WORK_ITEMS_COLLECTION
                ).find_many(
                    {"agency_id": agency_id},
                    sort=[("id", 1)],
                    limit=MAXIMUM_QUERY_LIMIT,
                )
                active_items = [
                    work
                    for work in active_items
                    if work.get("id") != item["id"]
                    and work.get("status") not in {"completed", "cancelled"}
                ]
                loads = {
                    member["user_id"]: len(
                        [
                            work
                            for work in active_items
                            if work.get("assigned_user_id") == member["user_id"]
                        ]
                    )
                    for member in eligible
                }
                target_user_id = min(loads, key=lambda member_id: (loads[member_id], member_id))
                explanation = (
                    f"{explanation} Least-open routing selected {target_user_id} "
                    f"from {len(eligible)} eligible members at load {loads[target_user_id]}."
                )
            else:
                ordered_ids = sorted(member["user_id"] for member in eligible)
                seed = int(
                    sha256(
                        f"{agency_id}:{item['id']}:{item.get('source_fingerprint') or ''}".encode(
                            "utf-8"
                        )
                    ).hexdigest()[:12],
                    16,
                )
                target_user_id = ordered_ids[seed % len(ordered_ids)]
                explanation = (
                    f"{explanation} Deterministic round-robin routing selected "
                    f"{target_user_id} from {len(ordered_ids)} eligible members."
                )

        if target_user_id:
            await self._validate_assignee(
                agency_id, target_user_id, item["work_item_type"]
            )
        if not target_user_id and not target_team_code:
            return await self.apply_action(
                work_item_id,
                "place_in_queue",
                {
                    "queue_code": "unassigned",
                    "reason": explanation,
                    "expected_version": expected_version,
                    "metadata": {
                        "assignment_strategy": strategy,
                        "assignment_unresolved": True,
                    },
                },
                user,
                agency_id=agency_id,
            )
        result = await self.apply_action(
            work_item_id,
            "assign" if not item.get("assigned_user_id") else "reassign",
            {
                "to_user_id": target_user_id,
                "to_team_code": target_team_code,
                "reason": explanation,
                "expected_version": expected_version,
                "metadata": {
                    "assignment_strategy": strategy,
                    "deterministic_routing": True,
                },
            },
            user,
            agency_id=agency_id,
        )
        result["assignment_strategy"] = strategy
        result["assignment_explanation"] = explanation
        return result

    async def bulk_assign(
        self,
        payload: OperationalBulkAssignmentRequest | dict[str, Any],
        user: dict,
        agency_id: str,
    ) -> dict[str, Any]:
        data = self._payload(payload)
        request_model = OperationalBulkAssignmentRequest(**data)
        if not request_model.to_user_id and not request_model.to_team_code:
            raise AgentWorkQueueError("Bulk assignment requires a user or team target.")
        if request_model.to_user_id:
            membership = await self.db.collection("agency_staff_memberships").find_one(
                {
                    "agency_id": agency_id,
                    "user_id": request_model.to_user_id,
                    "status": "active",
                }
            )
            if not membership:
                raise AgentWorkQueueError(
                    "Bulk assignment target must be an active member of this Agency."
                )
        updated_items: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        for work_item_id in request_model.work_item_ids[: request_model.max_items]:
            try:
                item = await self._require_work_item(work_item_id, agency_id=agency_id)
            except AgentWorkQueueError:
                skipped.append({"work_item_id": work_item_id, "reason": "not_found"})
                continue
            if item.get("status") in {"completed", "cancelled"}:
                skipped.append({"work_item_id": work_item_id, "reason": "not_active"})
                continue
            if request_model.only_unassigned and item.get("assigned_user_id"):
                skipped.append({"work_item_id": work_item_id, "reason": "already_assigned"})
                continue
            if request_model.to_user_id:
                try:
                    await self._validate_assignee(
                        agency_id,
                        request_model.to_user_id,
                        item["work_item_type"],
                    )
                except AgentWorkQueueError:
                    skipped.append(
                        {
                            "work_item_id": work_item_id,
                            "reason": "assignee_not_eligible",
                        }
                    )
                    continue
            updates = {
                "assigned_user_id": request_model.to_user_id,
                "assigned_team_code": self._norm(request_model.to_team_code) if request_model.to_team_code else item.get("assigned_team_code"),
                "status": "assigned"
                if item.get("status") in {"open", "reopened", "accepted"}
                else item.get("status"),
                "assignment_explanation": request_model.reason,
                "version": int(item.get("version") or 1) + 1,
                "updated_by": user.get("id"),
            }
            version_filter = {"id": item["id"]}
            if "version" in item:
                version_filter["version"] = item["version"]
            updated = await self.db.collection(OPERATIONAL_WORK_ITEMS_COLLECTION).update_one(version_filter, updates, allow_agency_update=True)
            if updated:
                await self._record_event(
                    updated,
                    "bulk_assigned",
                    user,
                    reason=request_model.reason,
                    from_user_id=item.get("assigned_user_id"),
                    to_user_id=updated.get("assigned_user_id"),
                    from_team_code=item.get("assigned_team_code"),
                    to_team_code=updated.get("assigned_team_code"),
                    payload={"bulk_assignment": True, "metadata": request_model.metadata},
                )
                updated_items.append(await self._work_item_projection(updated))
        return {
            "phase": PHASE_LABEL,
            "assigned_count": len(updated_items),
            "skipped_count": len(skipped),
            "items": updated_items,
            "skipped": skipped,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def list_assignment_events(self, work_item_id: str, agency_id: str | None = None) -> list[dict[str, Any]]:
        filters = {"work_item_id": work_item_id}
        if agency_id:
            filters["agency_id"] = agency_id
        events = await self.db.collection(OPERATIONAL_ASSIGNMENT_EVENTS_COLLECTION).find_many(filters)
        events.sort(key=lambda item: self._sort_text(item.get("created_at")))
        return events

    async def list_queue_definitions(self, agency_id: str | None = None, include_defaults: bool = True) -> list[dict[str, Any]]:
        filters = {"agency_id": agency_id} if agency_id else None
        definitions = await self.db.collection(OPERATIONAL_QUEUE_DEFINITIONS_COLLECTION).find_many(filters)
        if include_defaults:
            existing_codes = {item.get("queue_code") for item in definitions}
            for definition in DEFAULT_QUEUE_DEFINITIONS:
                if definition["queue_code"] not in existing_codes:
                    definitions.append(
                        {
                            "id": f"default-{definition['queue_code']}",
                            "agency_id": agency_id,
                            "is_default": True,
                            "is_active": True,
                            "metadata_only": True,
                            "agent_work_queue_assignment_foundation": True,
                            **definition,
                        }
                    )
        definitions.sort(key=lambda item: str(item.get("queue_code") or ""))
        return definitions

    async def create_queue_definition(
        self,
        payload: OperationalQueueDefinitionCreate | dict[str, Any],
        user: dict,
        *,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        data = self._payload(payload)
        if agency_id:
            data["agency_id"] = agency_id
        data["queue_code"] = self._norm(data["queue_code"])
        data["assignment_strategy"] = self._norm(data.get("assignment_strategy") or "manual")
        data["created_by"] = user.get("id")
        data["updated_by"] = user.get("id")
        definition = OperationalQueueDefinition(**data)
        created = await self.db.collection(OPERATIONAL_QUEUE_DEFINITIONS_COLLECTION).insert_one(definition.model_dump(mode="json"))
        return {"phase": PHASE_LABEL, "queue_definition": created, "metadata_only": True, **self.safety_flags()}

    async def update_queue_definition(
        self,
        definition_id: str,
        payload: OperationalQueueDefinitionUpdate | dict[str, Any],
        user: dict,
        *,
        agency_id: str | None = None,
        platform_scope_only: bool = False,
    ) -> dict[str, Any]:
        filters: dict[str, Any] = {"id": definition_id}
        if agency_id:
            filters["agency_id"] = agency_id
        elif platform_scope_only:
            filters["agency_id"] = None
        existing = await self.db.collection(
            OPERATIONAL_QUEUE_DEFINITIONS_COLLECTION
        ).find_one(filters)
        if not existing:
            raise AgentWorkQueueError("Queue definition metadata was not found.")
        updates = self._payload(payload, exclude_unset=True)
        if set(updates) & {"agency_id", "queue_code"}:
            raise AgentWorkQueueError(
                "Queue Agency scope and stable queue code are immutable."
            )
        if "assignment_strategy" in updates:
            updates["assignment_strategy"] = self._norm(updates["assignment_strategy"])
        updates["updated_by"] = user.get("id")
        updated = await self.db.collection(
            OPERATIONAL_QUEUE_DEFINITIONS_COLLECTION
        ).update_one(filters, updates)
        if not updated:
            raise AgentWorkQueueError("Queue definition metadata could not be updated.")
        return {"phase": PHASE_LABEL, "queue_definition": updated, "metadata_only": True, **self.safety_flags()}

    async def list_queue_views(self, agency_id: str | None = None, owner_user_id: str | None = None) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        views = await self.db.collection(OPERATIONAL_QUEUE_VIEWS_COLLECTION).find_many(filters or None)
        if owner_user_id:
            views = [item for item in views if item.get("owner_scope") in {"agency", "team", "platform"} or item.get("owner_user_id") == owner_user_id]
        views.sort(key=lambda item: (not bool(item.get("is_default")), str(item.get("name") or "")))
        return views

    async def create_queue_view(self, payload: OperationalQueueViewCreate | dict[str, Any], user: dict, agency_id: str | None = None) -> dict[str, Any]:
        data = self._payload(payload)
        if agency_id:
            data["agency_id"] = agency_id
        data.setdefault("view_code", self._queue_view_code(data.get("name") or "queue_view"))
        data["view_code"] = self._norm(data["view_code"])
        data["created_by"] = user.get("id")
        data["updated_by"] = user.get("id")
        view = OperationalQueueView(**data)
        created = await self.db.collection(OPERATIONAL_QUEUE_VIEWS_COLLECTION).insert_one(view.model_dump(mode="json"))
        return {"phase": PHASE_LABEL, "queue_view": created, "metadata_only": True, **self.safety_flags()}

    async def update_queue_view(self, view_id: str, payload: OperationalQueueViewUpdate | dict[str, Any], user: dict, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": view_id}
        if agency_id:
            filters["agency_id"] = agency_id
        existing = await self.db.collection(OPERATIONAL_QUEUE_VIEWS_COLLECTION).find_one(filters)
        if not existing:
            raise AgentWorkQueueError("Queue view metadata was not found.")
        updates = self._payload(payload, exclude_unset=True)
        if "view_code" in updates:
            updates["view_code"] = self._norm(updates["view_code"])
        updates["updated_by"] = user.get("id")
        updated = await self.db.collection(OPERATIONAL_QUEUE_VIEWS_COLLECTION).update_one({"id": existing["id"]}, updates)
        if not updated:
            raise AgentWorkQueueError("Queue view metadata could not be updated.")
        return {"phase": PHASE_LABEL, "queue_view": updated, "metadata_only": True, **self.safety_flags()}

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "work_item_count": len(items),
            "unassigned_count": len([item for item in items if not item.get("assigned_user_id")]),
            "blocked_count": len([item for item in items if item.get("status") == "blocked" or item.get("blocker_status") == "blocked"]),
            "due_soon_count": len([item for item in items if self._computed_sla_status(item) == "due_soon"]),
            "overdue_count": len([item for item in items if self._computed_sla_status(item) in {"overdue", "breached"}]),
            "completed_count": len([item for item in items if item.get("status") == "completed"]),
            "status_counts": self._counts(items, "status", WORK_ITEM_STATUSES),
            "priority_counts": self._counts(items, "priority", WORK_ITEM_PRIORITIES),
            "severity_counts": self._counts(items, "severity", WORK_ITEM_SEVERITIES),
            "type_counts": self._counts(items, "work_item_type", WORK_ITEM_TYPES),
            "queue_counts": self._counts(items, "queue_code", CANONICAL_QUEUE_CODES),
        }

    def queue_summary(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "queue_code": queue_code,
                "label": self._label(queue_code),
                "count": len([item for item in items if self._queue_matches(item, queue_code)]),
                "metadata_only": True,
            }
            for queue_code in CANONICAL_QUEUE_CODES
        ]

    def ordering_metadata(self) -> dict[str, Any]:
        return {
            "priority_order": ["critical", "urgent", "high", "normal", "low"],
            "sla_order": ["breached", "overdue", "due_soon", "paused", "on_track", "unknown"],
            "due_date_order": "oldest_due_at_first",
            "severity_order": ["critical", "high", "medium", "low"],
            "created_order": "oldest_created_at_first",
            "deterministic_queue_ordering_enabled": True,
        }

    def generation_rules(self) -> list[dict[str, Any]]:
        return [
            {"source": "workflow_started", "work_item_type": "new_request_triage", "idempotent": True},
            {"source": "workflow_active_blockers", "work_item_type": "workflow_blocker", "idempotent": True},
            {"source": "request_tasks", "work_item_type": "task_deadline", "idempotent": True},
            {"source": "travel_requests_new", "work_item_type": "new_request_triage", "idempotent": True},
            {"source": "offer_preparation", "work_item_type": "offer_preparation_required", "idempotent": True},
            {"source": "accepted_offer_awaiting_booking", "work_item_type": "accepted_offer_awaiting_booking", "idempotent": True},
            {"source": "booking_awaiting_ticketing", "work_item_type": "booking_awaiting_ticketing", "idempotent": True},
            {"source": "documents_required_missing_expired", "work_item_type": "document_missing_or_expiring", "idempotent": True},
            {"source": "pilot_readiness_issues", "work_item_type": "pilot_readiness_blocker", "idempotent": True},
        ]

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "agent_work_queue_assignment_foundation": True,
            "canonical_operational_queue": True,
            "canonical_operational_work_item_owner": True,
            "legacy_request_tasks_projection_only": True,
            "existing_task_system_preserved": True,
            "reuse_existing_tasks_timelines_workflows_enabled": True,
            "client_facing_context_hidden": True,
            "platform_governance_does_not_silently_act_as_agency_staff": True,
            "agency_isolation_enforced": True,
            "provider_integrations_disabled": True,
            "external_api_calls_disabled": True,
            "ai_disabled": True,
            "background_workers_disabled": True,
            "automatic_execution_disabled": True,
            "automation_disabled": True,
            "external_execution_disabled": True,
            "governed_internal_automation_enabled": True,
            "class_c_business_execution_disabled": True,
            "human_authority_final": True,
        }

    async def _sync_workflow_events(self, agency_id: str, user: dict) -> list[dict[str, Any]]:
        events = await self.db.collection("operational_workflow_events").find_many({"agency_id": agency_id})
        generated = []
        for event in events:
            event_type = self._norm(event.get("event_type") or "")
            if event_type not in {"workflow_started", "transition_blocked", "workflow_warning", "workflow_manual_review"}:
                continue
            source_type = self._norm(event.get("source_entity_type") or "workflow")
            source_id = event.get("source_entity_id") or event.get("workflow_instance_id")
            work_item_type = "new_request_triage" if event_type == "workflow_started" and source_type in {"request", "travel_request"} else "workflow_blocker"
            response = await self.generate_work_item(
                {
                    "agency_id": agency_id,
                    "work_item_type": work_item_type,
                    "source_entity_type": source_type,
                    "source_entity_id": source_id,
                    "workflow_instance_id": event.get("workflow_instance_id"),
                    "workflow_event_id": event.get("id"),
                    "title": f"{self._label(source_type)} workflow review",
                    "summary": f"Workflow event {event_type} needs queue visibility.",
                    "priority": "normal" if work_item_type == "new_request_triage" else "high",
                    "severity": "medium" if work_item_type == "new_request_triage" else "high",
                    "queue_code": "unassigned" if work_item_type == "new_request_triage" else "workflow_blocker_queue",
                    "blocker_status": "not_blocked" if work_item_type == "new_request_triage" else "blocked",
                    "generation_reason": "workflow_event_integration",
                    "source_snapshot_json": event,
                    "compatibility_mapping_json": {"operational_workflow_event_id": event.get("id")},
                },
                user,
                agency_id=agency_id,
            )
            generated.append(response)
        return generated

    async def _sync_workflow_blockers(self, agency_id: str, user: dict) -> list[dict[str, Any]]:
        instances = await self.db.collection("operational_workflow_instances").find_many({"agency_id": agency_id})
        generated = []
        for instance in instances:
            blockers = instance.get("active_blockers_json") or []
            warnings = instance.get("active_warnings_json") or []
            if not blockers and not warnings:
                continue
            response = await self.generate_work_item(
                {
                    "agency_id": agency_id,
                    "work_item_type": "workflow_blocker" if blockers else "policy_gap_manual_review",
                    "source_entity_type": self._norm(instance.get("entity_type") or "workflow"),
                    "source_entity_id": instance.get("entity_id") or instance.get("id"),
                    "workflow_instance_id": instance.get("id"),
                    "title": f"{self._label(instance.get('entity_type') or 'workflow')} workflow blocker",
                    "summary": "Workflow orchestration has blockers or warnings requiring human review.",
                    "priority": "high",
                    "severity": "high" if blockers else "medium",
                    "queue_code": "workflow_blocker_queue",
                    "blocker_status": "blocked" if blockers else "manual_review",
                    "generation_reason": "workflow_blocker_integration",
                    "source_snapshot_json": {"active_blockers_json": blockers, "active_warnings_json": warnings},
                    "compatibility_mapping_json": {"operational_workflow_instance_id": instance.get("id")},
                },
                user,
                agency_id=agency_id,
            )
            generated.append(response)
        return generated

    async def _sync_request_tasks(self, agency_id: str, user: dict) -> list[dict[str, Any]]:
        tasks = await self.db.collection("request_tasks").find_many({"agency_id": agency_id})
        generated = []
        for task in tasks:
            if task.get("status") in {"done", "cancelled"}:
                continue
            overdue = self._parse_dt(task.get("due_at")) and self._parse_dt(task.get("due_at")) < self._now()
            response = await self.generate_work_item(
                {
                    "agency_id": agency_id,
                    "work_item_type": "overdue_task" if overdue else "task_deadline",
                    "source_entity_type": "request_task",
                    "source_entity_id": task.get("id"),
                    "request_task_id": task.get("id"),
                    "title": task.get("title") or "Request task",
                    "summary": task.get("description"),
                    "status": "open",
                    "priority": self._norm(task.get("priority") or "normal"),
                    "severity": "high" if overdue else "medium",
                    "queue_code": "overdue" if overdue else "unassigned",
                    "assigned_user_id": task.get("assigned_user_id"),
                    "due_at": task.get("due_at"),
                    "sla_status": "overdue" if overdue else None,
                    "blocker_status": "not_blocked",
                    "generation_reason": "request_task_compatibility_mapping",
                    "source_snapshot_json": task,
                    "compatibility_mapping_json": {"request_task_id": task.get("id"), "request_id": task.get("request_id")},
                },
                user,
                agency_id=agency_id,
            )
            generated.append(response)
        return generated

    async def _sync_travel_requests(self, agency_id: str, user: dict) -> list[dict[str, Any]]:
        requests = await self.db.collection("travel_requests").find_many({"agency_id": agency_id})
        generated = []
        for request in requests:
            status = self._norm(request.get("status") or "")
            if status not in {"new", "triage", "information_required"}:
                continue
            response = await self.generate_work_item(
                {
                    "agency_id": agency_id,
                    "work_item_type": "new_request_triage" if status == "new" else "incomplete_passenger_data",
                    "source_entity_type": "request",
                    "source_entity_id": request.get("id"),
                    "title": request.get("title") or request.get("request_reference") or "Travel request",
                    "summary": request.get("service_summary") or request.get("route_summary"),
                    "priority": self._norm(request.get("priority") or "normal"),
                    "severity": "medium",
                    "queue_code": "unassigned",
                    "assigned_user_id": request.get("assigned_user_id"),
                    "client_impact": request.get("client_visible_notes"),
                    "generation_reason": "travel_request_triage",
                    "source_snapshot_json": request,
                    "compatibility_mapping_json": {"travel_request_id": request.get("id")},
                },
                user,
                agency_id=agency_id,
            )
            generated.append(response)
        return generated

    async def _sync_request_workspaces(self, agency_id: str, user: dict) -> list[dict[str, Any]]:
        requests = await self.db.collection("travel_request_workspaces").find_many({"agency_id": agency_id})
        generated = []
        for request in requests:
            status = self._norm(request.get("request_status") or "")
            if status not in {"new", "triage", "open", "waiting"}:
                continue
            response = await self.generate_work_item(
                {
                    "agency_id": agency_id,
                    "work_item_type": "new_request_triage" if status in {"new", "triage"} else "incomplete_service_data",
                    "source_entity_type": "travel_request_workspace",
                    "source_entity_id": request.get("id"),
                    "title": request.get("request_title") or request.get("request_reference") or "Travel request workspace",
                    "summary": request.get("service_summary") or request.get("special_service_notes"),
                    "priority": self._norm(request.get("request_priority") or "normal"),
                    "severity": "medium",
                    "queue_code": "waiting_client" if status == "waiting" else "unassigned",
                    "assigned_user_id": request.get("assigned_agent"),
                    "due_at": request.get("deadline"),
                    "blocker_status": "waiting_client" if status == "waiting" else "not_blocked",
                    "generation_reason": "travel_request_workspace_status",
                    "source_snapshot_json": request,
                    "compatibility_mapping_json": {"travel_request_workspace_id": request.get("id")},
                },
                user,
                agency_id=agency_id,
            )
            generated.append(response)
        return generated

    async def _sync_offer_workspaces(self, agency_id: str, user: dict) -> list[dict[str, Any]]:
        offers = await self.db.collection("offer_workspaces_v2").find_many({"agency_id": agency_id})
        generated = []
        for offer in offers:
            status = self._norm(offer.get("offer_status") or "")
            if status not in {"draft", "new", "preparing", "accepted", "awaiting_response"}:
                continue
            work_item_type = "offer_preparation_required"
            queue_code = "unassigned"
            if status == "accepted":
                work_item_type = "accepted_offer_awaiting_booking"
                queue_code = "service_case_queue"
            elif status == "awaiting_response":
                work_item_type = "offer_awaiting_response"
                queue_code = "waiting_client"
            response = await self.generate_work_item(
                {
                    "agency_id": agency_id,
                    "work_item_type": work_item_type,
                    "source_entity_type": "offer_workspace",
                    "source_entity_id": offer.get("id"),
                    "title": offer.get("offer_title") or offer.get("offer_reference") or "Offer workspace",
                    "summary": offer.get("offer_summary") or offer.get("itinerary_summary"),
                    "priority": "normal",
                    "severity": "medium",
                    "queue_code": queue_code,
                    "due_at": offer.get("validity_date"),
                    "blocker_status": "waiting_client" if status == "awaiting_response" else "not_blocked",
                    "generation_reason": "offer_workspace_status",
                    "source_snapshot_json": offer,
                    "compatibility_mapping_json": {"offer_workspace_id": offer.get("id")},
                },
                user,
                agency_id=agency_id,
            )
            generated.append(response)
        return generated

    async def _sync_booking_workspaces(self, agency_id: str, user: dict) -> list[dict[str, Any]]:
        bookings = await self.db.collection("booking_workspaces").find_many({"agency_id": agency_id})
        generated = []
        for booking in bookings:
            status = self._norm(booking.get("booking_status") or "")
            if status not in {"booked", "ticketing", "ready_to_ticket", "pending_ticketing"}:
                continue
            if booking.get("ticket_ids"):
                continue
            response = await self.generate_work_item(
                {
                    "agency_id": agency_id,
                    "work_item_type": "booking_awaiting_ticketing",
                    "source_entity_type": "booking_workspace",
                    "source_entity_id": booking.get("id"),
                    "title": booking.get("booking_reference") or "Booking awaiting ticketing",
                    "summary": booking.get("booking_summary") or booking.get("operational_notes"),
                    "priority": "high",
                    "severity": "high",
                    "queue_code": "urgent_critical",
                    "assigned_user_id": booking.get("booking_owner"),
                    "due_at": booking.get("booking_deadline"),
                    "generation_reason": "booking_awaiting_ticketing",
                    "source_snapshot_json": booking,
                    "compatibility_mapping_json": {"booking_workspace_id": booking.get("id")},
                },
                user,
                agency_id=agency_id,
            )
            generated.append(response)
        return generated

    async def _sync_document_workspaces(self, agency_id: str, user: dict) -> list[dict[str, Any]]:
        documents = await self.db.collection("document_workspaces").find_many({"agency_id": agency_id})
        generated = []
        for document in documents:
            status = self._norm(document.get("document_status") or "")
            if status not in {"required", "requested", "rejected", "expired"} and not document.get("required_for_travel"):
                continue
            response = await self.generate_work_item(
                {
                    "agency_id": agency_id,
                    "work_item_type": "document_missing_or_expiring",
                    "source_entity_type": "document_workspace",
                    "source_entity_id": document.get("id"),
                    "title": document.get("document_title") or document.get("document_reference") or "Document requirement",
                    "summary": document.get("missing_reason") or document.get("rejection_reason") or document.get("document_description"),
                    "priority": "high" if document.get("required_for_travel") else "normal",
                    "severity": "high" if status in {"rejected", "expired"} else "medium",
                    "queue_code": "waiting_documents",
                    "due_at": document.get("requirement_deadline"),
                    "blocker_status": "waiting_documents",
                    "generation_reason": "document_requirement",
                    "source_snapshot_json": document,
                    "compatibility_mapping_json": {"document_workspace_id": document.get("id")},
                },
                user,
                agency_id=agency_id,
            )
            generated.append(response)
        return generated

    async def _sync_pilot_readiness_issues(self, agency_id: str, user: dict) -> list[dict[str, Any]]:
        issues = await self.db.collection("pilot_readiness_issues").find_many({"agency_id": agency_id})
        generated = []
        for issue in issues:
            if self._norm(issue.get("issue_status") or "") not in {"open", "in_review", "reopened"}:
                continue
            severity = self._norm(issue.get("severity") or "medium")
            response = await self.generate_work_item(
                {
                    "agency_id": agency_id,
                    "work_item_type": "pilot_readiness_blocker" if severity in {"critical", "high"} else "knowledge_issue",
                    "source_entity_type": "pilot_readiness_issue",
                    "source_entity_id": issue.get("id"),
                    "title": issue.get("title") or issue.get("issue_reference") or "Pilot readiness issue",
                    "summary": issue.get("description") or issue.get("review_notes"),
                    "priority": "critical" if severity == "critical" else "high",
                    "severity": severity,
                    "queue_code": "knowledge_gap_queue",
                    "blocker_status": "blocked" if severity == "critical" else "manual_review",
                    "generation_reason": "pilot_readiness_issue",
                    "source_snapshot_json": issue,
                    "compatibility_mapping_json": {"pilot_readiness_issue_id": issue.get("id")},
                },
                user,
                agency_id=agency_id,
            )
            generated.append(response)
        return generated

    async def _work_item_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = bounded_safe_snapshot(item, max_depth=6)
        for field in (
            "id",
            "agency_id",
            "work_item_code",
            "work_item_type",
            "source_entity_type",
            "source_entity_id",
            "primary_entity_type",
            "primary_entity_id",
            "workflow_instance_id",
            "workflow_event_id",
            "request_task_id",
            "timeline_entry_id",
            "source_timeline_entry_id",
            "source_automation_rule_id",
            "source_automation_execution_id",
            "title",
            "summary",
            "description",
            "status",
            "priority",
            "severity",
            "queue_code",
            "queue_key",
            "assigned_user_id",
            "assigned_team_code",
            "assignment_explanation",
            "due_at",
            "reminder_at",
            "escalation_at",
            "sla_status",
            "blocker_status",
            "approval_required",
            "approval_type",
            "approval_status",
            "approval_required_permission",
            "started_at",
            "completed_at",
            "cancelled_at",
            "version",
            "reconciliation_status",
        ):
            if field in item:
                projected[field] = item.get(field)
        projected["sla_status"] = self._computed_sla_status(projected)
        projected["queue_labels"] = [self._label(queue) for queue in CANONICAL_QUEUE_CODES if self._queue_matches(projected, queue)]
        projected["source"] = self._source_ref(projected)
        projected["source_route"] = self._source_route(projected)
        projected["assignment_events"] = (await self.list_assignment_events(projected["id"], agency_id=projected.get("agency_id")))[-5:]
        projected["dependencies"] = await self.db.collection(
            "operational_task_dependencies"
        ).find_many(
            {
                "agency_id": projected.get("agency_id"),
                "successor_task_id": projected["id"],
            },
            sort=[("created_at", 1), ("id", 1)],
            limit=50,
        )
        projected["dependants"] = await self.db.collection(
            "operational_task_dependencies"
        ).find_many(
            {
                "agency_id": projected.get("agency_id"),
                "predecessor_task_id": projected["id"],
            },
            sort=[("created_at", 1), ("id", 1)],
            limit=50,
        )
        source_execution_id = projected.get("source_automation_execution_id")
        projected["latest_automation_explanation"] = (
            await self.db.collection("operational_task_automation_runs").find_one(
                {
                    "agency_id": projected.get("agency_id"),
                    "id": source_execution_id,
                }
            )
            if source_execution_id
            else None
        )
        projected["next_recommended_safe_action"] = self._next_safe_action(projected)
        projected["client_facing_context_hidden"] = True
        projected.update(self.safety_flags())
        return projected

    async def _record_event(
        self,
        item: dict[str, Any],
        event_type: str,
        user: dict,
        *,
        reason: str | None = None,
        from_user_id: str | None = None,
        to_user_id: str | None = None,
        from_team_code: str | None = None,
        to_team_code: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        event = OperationalAssignmentEvent(
            agency_id=item["agency_id"],
            work_item_id=item["id"],
            event_type=self._norm(event_type),
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            from_team_code=from_team_code,
            to_team_code=to_team_code,
            reason=reason,
            actor_user_id=user.get("id"),
            payload_json=bounded_safe_snapshot(payload or {}, max_depth=4),
        )
        created = await self.db.collection(
            OPERATIONAL_ASSIGNMENT_EVENTS_COLLECTION
        ).insert_one(event.model_dump(mode="json"))
        timeline_event_type = (
            "assignment"
            if event_type
            in {
                "assigned",
                "assigned_to_self",
                "reassigned",
                "unassigned",
                "accepted",
                "released",
            }
            else "status_transition"
        )
        await OperationalCollaborationService(self.db).record_business_event(
            agency_id=item["agency_id"],
            entity_type="task",
            entity_id=item["id"],
            event_type=timeline_event_type,
            event_subtype=self._norm(event_type),
            summary=f"Work item {self._norm(event_type).replace('_', ' ')}.",
            actor={
                **user,
                "actor_type": "agency",
                "identity_id": user.get("identity_id") or user.get("id"),
            },
            visibility="internal",
            details={
                "work_item_code": item.get("work_item_code"),
                "source_entity_type": item.get("source_entity_type"),
                "source_entity_id": item.get("source_entity_id"),
                "reason": reason,
                "from_user_id": from_user_id,
                "to_user_id": to_user_id,
                "from_team_code": from_team_code,
                "to_team_code": to_team_code,
            },
            parent_entity_type=item.get("source_entity_type"),
            parent_entity_id=item.get("source_entity_id"),
            idempotency_key=f"assignment-event:{created['id']}",
            source_collection=OPERATIONAL_ASSIGNMENT_EVENTS_COLLECTION,
            source_record_id=created["id"],
        )
        return created

    async def _require_work_item(self, work_item_id: str, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": work_item_id}
        if agency_id:
            filters["agency_id"] = agency_id
        item = await self.db.collection(OPERATIONAL_WORK_ITEMS_COLLECTION).find_one(filters)
        if not item:
            alt_filters = {"work_item_code": work_item_id}
            if agency_id:
                alt_filters["agency_id"] = agency_id
            item = await self.db.collection(OPERATIONAL_WORK_ITEMS_COLLECTION).find_one(alt_filters)
        if not item:
            raise AgentWorkQueueError("Work item metadata was not found.")
        return item

    def _check_expected_version(
        self, item: dict[str, Any], expected_version: int | None
    ) -> None:
        if expected_version is not None and int(expected_version) != int(
            item.get("version") or 1
        ):
            raise AgentWorkQueueError("Work item version conflict.")

    def _assert_transition(self, current: str, target: str) -> None:
        current = self._norm(current)
        target = self._norm(target)
        current = {"accepted": "assigned", "reopened": "open"}.get(
            current, current
        )
        target = {"accepted": "assigned", "reopened": "open"}.get(
            target, target
        )
        if current == target:
            return
        if target not in WORK_ITEM_TRANSITIONS.get(current, set()):
            raise AgentWorkQueueError(
                f"Invalid work-item transition from {current} to {target}."
            )

    async def _validate_assignee(
        self, agency_id: str, user_id: str | None, work_item_type: str
    ) -> dict[str, Any]:
        if not user_id:
            raise AgentWorkQueueError("Assignment target user is required.")
        membership = await self.db.collection("agency_staff_memberships").find_one(
            {"agency_id": agency_id, "user_id": user_id, "status": "active"}
        )
        if not membership:
            raise AgentWorkQueueError(
                "Assignment target must be an active member of this Agency."
            )
        required_permission = task_type_contract(work_item_type)[
            "required_permission"
        ]
        permissions = agency_permissions(membership.get("agency_role"))
        if required_permission and required_permission not in permissions:
            raise AgentWorkQueueError(
                "Assignment target does not hold the required Agency permission."
            )
        return membership

    async def _eligible_assignees(
        self, agency_id: str, work_item_type: str
    ) -> list[dict[str, Any]]:
        memberships = await self.db.collection(
            "agency_staff_memberships"
        ).find_many(
            {"agency_id": agency_id, "status": "active"},
            sort=[("user_id", 1), ("id", 1)],
            limit=200,
        )
        required_permission = task_type_contract(work_item_type)[
            "required_permission"
        ]
        eligible = [
            membership
            for membership in memberships
            if membership.get("user_id")
            and (
                not required_permission
                or required_permission
                in agency_permissions(membership.get("agency_role"))
            )
        ]
        eligible.sort(key=lambda membership: str(membership.get("user_id") or ""))
        return eligible

    async def _assert_completion_allowed(
        self, item: dict[str, Any], user: dict, data: dict[str, Any]
    ) -> None:
        dependencies = await self.db.collection(
            "operational_task_dependencies"
        ).find_many(
            {
                "agency_id": item["agency_id"],
                "successor_task_id": item["id"],
            },
            sort=[("created_at", 1), ("id", 1)],
            limit=100,
        )
        unsatisfied = [
            dependency
            for dependency in dependencies
            if dependency.get("dependency_type") != "advisory"
            and dependency.get("status") not in {"satisfied", "waived"}
        ]
        if unsatisfied:
            raise AgentWorkQueueError(
                "Mandatory work-item dependencies must be satisfied before completion."
            )
        if item.get("blocker_status") not in {None, "", "not_blocked"} or any(
            not blocker.get("resolved") for blocker in item.get("blockers") or []
        ):
            raise AgentWorkQueueError(
                "Active work-item blockers must be resolved before completion."
            )
        if item.get("human_confirmation_required") or item.get(
            "execution_safety_class"
        ) == "C":
            if item.get("approval_status") != "approved":
                raise AgentWorkQueueError(
                    "Class C work requires an approved internal approval before "
                    "completion."
                )
        evidence = data.get("completion_evidence") or {}
        if not evidence:
            raise AgentWorkQueueError(
                "Manual work-item completion requires bounded completion evidence."
            )
        if not user.get("id"):
            raise AgentWorkQueueError("Completion actor is required.")

    def _next_safe_action(self, item: dict[str, Any]) -> str | None:
        status = self._norm(item.get("status") or "open")
        if status in {"completed", "cancelled"}:
            return "reopen"
        if status == "approval_required":
            return "review_approval"
        if status == "blocked":
            return "resolve_blocker"
        if status == "waiting":
            return "resume"
        if not item.get("assigned_user_id"):
            return "claim"
        if status in {"open", "assigned", "accepted", "reopened", "overdue"}:
            return "start"
        if status == "in_progress":
            return "complete"
        return None

    def _queue_matches(self, item: dict[str, Any], queue_code: str, *, current_user_id: str | None = None) -> bool:
        queue = self._norm(queue_code)
        if item.get("status") in {"completed", "cancelled"} and queue not in {"completed"}:
            return False
        computed_sla = self._computed_sla_status(item)
        if queue == "unassigned":
            return not item.get("assigned_user_id")
        if queue == "my_work":
            return bool(current_user_id) and item.get("assigned_user_id") == current_user_id
        if queue == "team_queue":
            return bool(item.get("assigned_team_code"))
        if queue == "urgent_critical":
            return item.get("priority") in {"urgent", "critical"} or item.get("severity") == "critical"
        if queue == "due_soon":
            return computed_sla == "due_soon"
        if queue == "overdue":
            return computed_sla in {"overdue", "breached"}
        if queue == "blocked":
            return item.get("status") == "blocked" or item.get("blocker_status") == "blocked"
        if queue in {"waiting_client", "waiting_airline_supplier", "waiting_documents", "waiting_approval", "waiting_payment"}:
            return item.get("blocker_status") == queue
        if queue == "disruption_queue":
            return item.get("work_item_type") == "disruption"
        if queue == "service_case_queue":
            return item.get("work_item_type") in {"claim_service_case", "accepted_offer_awaiting_booking", "service_approval_document_requirement"}
        if queue == "knowledge_gap_queue":
            return item.get("work_item_type") in {"policy_gap_manual_review", "knowledge_issue", "pilot_readiness_blocker"}
        if queue == "workflow_blocker_queue":
            return item.get("work_item_type") == "workflow_blocker"
        return item.get("queue_code") == queue

    def _computed_sla_status(self, item: dict[str, Any]) -> str:
        explicit = self._norm(item.get("sla_status") or "")
        if explicit in {"breached", "overdue", "due_soon", "paused", "completed"}:
            return explicit
        if item.get("status") == "completed":
            return "completed"
        due_at = self._parse_dt(item.get("due_at"))
        if not due_at:
            return explicit or "unknown"
        now = self._now()
        if due_at < now:
            return "overdue"
        if (due_at - now).total_seconds() <= 24 * 60 * 60:
            return "due_soon"
        return explicit or "on_track"

    def _ordering_key(self, item: dict[str, Any]) -> tuple[Any, ...]:
        priority_rank = {"critical": 0, "urgent": 1, "high": 2, "normal": 3, "medium": 3, "low": 4}
        sla_rank = {"breached": 0, "overdue": 0, "due_soon": 1, "paused": 2, "on_track": 3, "unknown": 4, "": 4, None: 4}
        severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        due_at = self._parse_dt(item.get("due_at")) or datetime.max.replace(tzinfo=timezone.utc)
        created_at = self._parse_dt(item.get("created_at")) or datetime.max.replace(tzinfo=timezone.utc)
        return (
            1 if item.get("status") in {"completed", "cancelled"} else 0,
            priority_rank.get(self._norm(item.get("priority") or "normal"), 5),
            sla_rank.get(self._computed_sla_status(item), 4),
            due_at,
            severity_rank.get(self._norm(item.get("severity") or "medium"), 4),
            created_at,
        )

    def _fingerprint(self, data: dict[str, Any]) -> str:
        parts = [
            data.get("agency_id"),
            self._norm(data.get("work_item_type") or ""),
            self._norm(data.get("source_entity_type") or ""),
            data.get("source_entity_id"),
            data.get("workflow_instance_id") or "",
            data.get("workflow_event_id") or "",
            data.get("request_task_id") or "",
            data.get("source_timeline_entry_id") or "",
            data.get("source_automation_rule_id") or "",
            data.get("source_automation_execution_id") or "",
        ]
        return "::".join(str(part or "") for part in parts)

    def _validate_work_item_payload(self, data: dict[str, Any], *, partial: bool = False) -> None:
        if not partial:
            for field in ["agency_id", "work_item_type", "source_entity_type", "source_entity_id", "title"]:
                if not data.get(field):
                    raise AgentWorkQueueError(f"{field} is required for work item metadata.")
        for field, allowed in [
            ("status", WORK_ITEM_STATUSES),
            ("priority", WORK_ITEM_PRIORITIES + ["medium"]),
            ("severity", WORK_ITEM_SEVERITIES),
            ("blocker_status", BLOCKER_STATUSES),
            ("sla_status", SLA_STATUSES),
        ]:
            if data.get(field):
                value = self._norm(data[field])
                if value not in allowed:
                    raise AgentWorkQueueError(f"Unsupported {field} metadata value: {value}.")
                data[field] = value
        if data.get("work_item_type"):
            data["work_item_type"] = self._norm(data["work_item_type"])
            if not partial and data["work_item_type"] not in WORK_ITEM_TYPES:
                raise AgentWorkQueueError(
                    f"Unsupported canonical work_item_type: {data['work_item_type']}."
                )
        if data.get("source_entity_type"):
            data["source_entity_type"] = self._norm(data["source_entity_type"])
        if data.get("queue_code"):
            data["queue_code"] = self._norm(data["queue_code"])
        if data.get("assigned_team_code"):
            data["assigned_team_code"] = self._norm(data["assigned_team_code"])
        if data.get("due_at"):
            parsed_due_at = self._parse_dt(data["due_at"])
            if parsed_due_at:
                data["due_at"] = parsed_due_at
        if data.get("execution_safety_class") not in {None, "A", "B", "C"}:
            raise AgentWorkQueueError(
                "Work-item execution_safety_class must be A, B, or C."
            )

    def _source_ref(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "source_entity_type": item.get("source_entity_type"),
            "source_entity_id": item.get("source_entity_id"),
            "workflow_instance_id": item.get("workflow_instance_id"),
            "workflow_event_id": item.get("workflow_event_id"),
            "request_task_id": item.get("request_task_id"),
            "timeline_entry_id": item.get("timeline_entry_id"),
            "metadata_only": True,
        }

    def _source_route(self, item: dict[str, Any]) -> str | None:
        source_type = self._norm(item.get("source_entity_type") or "")
        source_id = item.get("source_entity_id")
        if not source_id:
            return None
        route_map = {
            "request": f"/agency/requests/{source_id}",
            "travel_request": f"/agency/requests/{source_id}",
            "travel_request_workspace": "/agency/travel-requests",
            "trip": f"/agency/trips/{source_id}",
            "trip_workspace": "/agency/trip-workspaces",
            "offer": f"/agency/offers/{source_id}",
            "offer_workspace": "/agency/offer-workspaces",
            "booking": f"/agency/bookings/{source_id}",
            "booking_workspace": "/agency/booking-workspaces",
            "ticket": f"/agency/tickets-emds/{source_id}",
            "ticket_workspace": "/agency/ticket-workspaces",
            "emd": f"/agency/tickets-emds/{source_id}",
            "emd_workspace": "/agency/emd-workspaces",
            "document_workspace": "/agency/document-workspaces",
            "request_task": item.get("compatibility_mapping_json", {}).get("request_id") and f"/agency/requests/{item['compatibility_mapping_json']['request_id']}",
            "pilot_readiness_issue": "/agency/pilot-readiness",
            "workflow": "/agency/operational-workflows",
        }
        return route_map.get(source_type)

    def _payload(self, payload: Any, *, exclude_unset: bool = False) -> dict[str, Any]:
        if hasattr(payload, "model_dump"):
            return payload.model_dump(mode="json", exclude_unset=exclude_unset, exclude_none=True)
        return dict(payload or {})

    def _counts(self, items: list[dict[str, Any]], field: str, known_values: list[str]) -> dict[str, int]:
        counts = {value: 0 for value in known_values}
        for item in items:
            value = self._norm(item.get(field) or "unknown")
            counts[value] = counts.get(value, 0) + 1
        return counts

    def _work_item_code(self) -> str:
        return f"OWI-{self._now().strftime('%Y%m%d%H%M%S%f')}-{new_id()[:8]}"

    def _queue_view_code(self, name: str) -> str:
        return f"queue_view_{self._norm(name)}_{new_id()[:8]}"

    def _norm(self, value: Any) -> str:
        return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")

    def _label(self, value: Any) -> str:
        return str(value or "unset").replace("_", " ").title()

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _parse_dt(self, value: Any) -> datetime | None:
        if not value:
            return None
        try:
            if isinstance(value, datetime):
                parsed = value
            else:
                text = str(value)
                if len(text) == 10 and text.count("-") == 2:
                    text = f"{text}T23:59:59+00:00"
                parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed

    def _sort_text(self, value: Any) -> str:
        return str(value or "")
