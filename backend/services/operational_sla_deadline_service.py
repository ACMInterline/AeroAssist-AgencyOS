from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import Any

from database import Database
from models import (
    OperationalBusinessCalendar,
    OperationalBusinessCalendarCreate,
    OperationalBusinessCalendarUpdate,
    OperationalDeadline,
    OperationalDeadlineActionRequest,
    OperationalDeadlineCreate,
    OperationalDeadlineUpdate,
    OperationalSlaEvent,
    OperationalSlaPolicy,
    OperationalSlaPolicyCreate,
    OperationalSlaPolicyUpdate,
    new_id,
)


PHASE_LABEL = "phase_54_6_offer_to_booking_handoff_readiness_foundation"

OPERATIONAL_SLA_POLICIES_COLLECTION = "operational_sla_policies"
OPERATIONAL_DEADLINES_COLLECTION = "operational_deadlines"
OPERATIONAL_SLA_EVENTS_COLLECTION = "operational_sla_events"
OPERATIONAL_BUSINESS_CALENDARS_COLLECTION = "operational_business_calendars"

SLA_POLICY_SCOPES = ["platform", "agency"]
SLA_POLICY_STATUSES = ["draft", "active", "paused", "archived"]
SLA_DURATION_UNITS = ["minutes", "hours", "days"]
BUSINESS_HOURS_BEHAVIORS = ["calendar_hours", "business_hours"]
DEADLINE_STATUSES = ["open", "due_soon", "overdue", "paused", "extended", "completed", "waived", "archived"]
BREACH_STATES = ["not_breached", "due_soon", "breached", "paused", "completed", "waived"]
SLA_EVENT_TYPES = ["started", "paused", "resumed", "warning", "breached", "extended", "completed", "waived", "recalculated"]
DEADLINE_TYPES = [
    "request_response_sla",
    "offer_preparation_deadline",
    "offer_expiry",
    "ticketing_deadline",
    "airline_approval_deadline",
    "medif_document_deadline",
    "petc_avih_notice_deadline",
    "umnr_notice_deadline",
    "mobility_poc_notice_deadline",
    "payment_deadline",
    "booking_ticketing_deadline",
    "task_deadline",
    "disruption_response_deadline",
    "claim_refund_change_deadline",
]

DEFAULT_SLA_POLICIES: list[dict[str, Any]] = [
    {"deadline_type": "request_response_sla", "entity_type": "request", "duration_value": 4, "duration_unit": "hours", "priority": "normal", "name": "Request response SLA"},
    {"deadline_type": "offer_preparation_deadline", "entity_type": "offer_workspace", "work_item_type": "offer_preparation_required", "duration_value": 1, "duration_unit": "days", "name": "Offer preparation deadline"},
    {"deadline_type": "offer_expiry", "entity_type": "offer_workspace", "work_item_type": "offer_awaiting_response", "duration_value": 3, "duration_unit": "days", "name": "Offer expiry"},
    {"deadline_type": "ticketing_deadline", "entity_type": "booking_workspace", "work_item_type": "booking_awaiting_ticketing", "duration_value": 12, "duration_unit": "hours", "priority": "high", "name": "Ticketing deadline"},
    {"deadline_type": "airline_approval_deadline", "entity_type": "ssr_osi_workspace", "work_item_type": "service_approval_document_requirement", "duration_value": 2, "duration_unit": "days", "name": "Airline approval deadline"},
    {"deadline_type": "medif_document_deadline", "entity_type": "document_workspace", "work_item_type": "document_missing_or_expiring", "duration_value": 3, "duration_unit": "days", "service_family": "MEDIF", "name": "MEDIF/document deadline"},
    {"deadline_type": "petc_avih_notice_deadline", "entity_type": "ssr_osi_workspace", "duration_value": 48, "duration_unit": "hours", "service_family": "PETC_AVIH", "name": "PETC/AVIH notice deadline"},
    {"deadline_type": "umnr_notice_deadline", "entity_type": "ssr_osi_workspace", "duration_value": 48, "duration_unit": "hours", "service_family": "UMNR", "name": "UMNR notice deadline"},
    {"deadline_type": "mobility_poc_notice_deadline", "entity_type": "ssr_osi_workspace", "duration_value": 48, "duration_unit": "hours", "service_family": "MOBILITY_POC", "name": "Mobility/POC notice deadline"},
    {"deadline_type": "payment_deadline", "entity_type": "payment", "duration_value": 24, "duration_unit": "hours", "name": "Payment deadline"},
    {"deadline_type": "booking_ticketing_deadline", "entity_type": "booking_workspace", "duration_value": 24, "duration_unit": "hours", "priority": "high", "name": "Booking/ticketing deadline"},
    {"deadline_type": "task_deadline", "entity_type": "request_task", "work_item_type": "task_deadline", "duration_value": 1, "duration_unit": "days", "name": "Task deadline"},
    {"deadline_type": "disruption_response_deadline", "entity_type": "disruption", "work_item_type": "disruption", "duration_value": 1, "duration_unit": "hours", "priority": "urgent", "name": "Disruption response deadline"},
    {"deadline_type": "claim_refund_change_deadline", "entity_type": "service_case", "work_item_type": "claim_service_case", "duration_value": 5, "duration_unit": "days", "name": "Claim/refund/change deadline"},
]


class OperationalSlaDeadlineError(ValueError):
    pass


class OperationalSlaDeadlineService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def platform_dashboard(self, **filters: Any) -> dict[str, Any]:
        deadlines = await self.list_deadlines(**filters)
        return {
            "phase": PHASE_LABEL,
            "deadlines": deadlines,
            "policies": await self.list_policies(agency_id=filters.get("agency_id"), include_defaults=True),
            "business_calendars": await self.list_business_calendars(agency_id=filters.get("agency_id"), include_defaults=True),
            "summary": self.summarize_deadlines(deadlines),
            "deadline_types": DEADLINE_TYPES,
            "metadata_only": True,
            "platform_governance_enabled": True,
            **self.safety_flags(),
        }

    async def agency_dashboard(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        filters["agency_id"] = agency_id
        deadlines = await self.list_deadlines(**filters)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "deadlines": deadlines,
            "policies": await self.list_policies(agency_id=agency_id, include_defaults=True),
            "business_calendars": await self.list_business_calendars(agency_id=agency_id, include_defaults=True),
            "summary": self.summarize_deadlines(deadlines),
            "deadline_types": DEADLINE_TYPES,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def list_policies(self, agency_id: str | None = None, include_defaults: bool = True, **filters: Any) -> list[dict[str, Any]]:
        query: dict[str, Any] = {}
        if agency_id:
            query["agency_id"] = agency_id
        for field in ["scope", "policy_code", "entity_type", "work_item_type", "deadline_type", "priority", "service_family", "status"]:
            if filters.get(field):
                query[field] = self._norm(filters[field])
        policies = await self.db.collection(OPERATIONAL_SLA_POLICIES_COLLECTION).find_many(query or None)
        if include_defaults:
            existing_codes = {policy.get("policy_code") for policy in policies}
            for policy in DEFAULT_SLA_POLICIES:
                policy_code = f"default_{policy['deadline_type']}"
                if policy_code in existing_codes:
                    continue
                if filters.get("deadline_type") and self._norm(filters["deadline_type"]) != policy["deadline_type"]:
                    continue
                policies.append(self._default_policy(policy, agency_id=agency_id))
        policies.sort(key=lambda item: (0 if item.get("agency_id") else 1, str(item.get("policy_code") or "")))
        return policies

    async def create_policy(self, payload: OperationalSlaPolicyCreate | dict[str, Any], user: dict) -> dict[str, Any]:
        data = self._payload(payload)
        self._normalize_policy(data)
        if not data.get("policy_code"):
            data["policy_code"] = self._policy_code(data["deadline_type"], data.get("priority"))
        if not data.get("scope"):
            data["scope"] = "agency" if data.get("agency_id") else "platform"
        data["created_by"] = user.get("id")
        data["updated_by"] = user.get("id")
        policy = OperationalSlaPolicy(**data)
        created = await self.db.collection(OPERATIONAL_SLA_POLICIES_COLLECTION).insert_one(policy.model_dump(mode="json"))
        return {"phase": PHASE_LABEL, "policy": created, "metadata_only": True, **self.safety_flags()}

    async def update_policy(self, policy_id: str, payload: OperationalSlaPolicyUpdate | dict[str, Any], user: dict) -> dict[str, Any]:
        existing = await self.db.collection(OPERATIONAL_SLA_POLICIES_COLLECTION).find_one({"id": policy_id})
        if not existing:
            raise OperationalSlaDeadlineError("SLA policy metadata was not found.")
        updates = self._payload(payload, exclude_unset=True)
        if not updates:
            raise OperationalSlaDeadlineError("No SLA policy metadata updates were provided.")
        merged = {**existing, **updates}
        self._normalize_policy(merged, partial=True)
        for field in ["scope", "policy_code", "entity_type", "work_item_type", "deadline_type", "priority", "service_family", "duration_unit", "business_hours_behavior", "status"]:
            if field in updates and updates[field] is not None:
                updates[field] = self._norm(updates[field])
        updates["updated_by"] = user.get("id")
        updated = await self.db.collection(OPERATIONAL_SLA_POLICIES_COLLECTION).update_one({"id": policy_id}, updates)
        if not updated:
            raise OperationalSlaDeadlineError("SLA policy metadata could not be updated.")
        return {"phase": PHASE_LABEL, "policy": updated, "metadata_only": True, **self.safety_flags()}

    async def list_business_calendars(self, agency_id: str | None = None, include_defaults: bool = True, **filters: Any) -> list[dict[str, Any]]:
        query: dict[str, Any] = {}
        if agency_id:
            query["agency_id"] = agency_id
        for field in ["calendar_code", "status", "timezone"]:
            if filters.get(field):
                query[field] = filters[field] if field == "timezone" else self._norm(filters[field])
        calendars = await self.db.collection(OPERATIONAL_BUSINESS_CALENDARS_COLLECTION).find_many(query or None)
        if include_defaults and not any(calendar.get("calendar_code") == "default_business_calendar" for calendar in calendars):
            calendars.append(self._default_calendar(agency_id=agency_id))
        calendars.sort(key=lambda item: (0 if item.get("agency_id") else 1, str(item.get("calendar_code") or "")))
        return calendars

    async def create_business_calendar(self, payload: OperationalBusinessCalendarCreate | dict[str, Any], user: dict) -> dict[str, Any]:
        data = self._payload(payload)
        if not data.get("calendar_code"):
            data["calendar_code"] = self._calendar_code(data.get("name") or "business_calendar")
        self._normalize_calendar(data)
        data["created_by"] = user.get("id")
        data["updated_by"] = user.get("id")
        calendar = OperationalBusinessCalendar(**data)
        created = await self.db.collection(OPERATIONAL_BUSINESS_CALENDARS_COLLECTION).insert_one(calendar.model_dump(mode="json"))
        return {"phase": PHASE_LABEL, "business_calendar": created, "metadata_only": True, **self.safety_flags()}

    async def update_business_calendar(self, calendar_id: str, payload: OperationalBusinessCalendarUpdate | dict[str, Any], user: dict) -> dict[str, Any]:
        existing = await self.db.collection(OPERATIONAL_BUSINESS_CALENDARS_COLLECTION).find_one({"id": calendar_id})
        if not existing:
            raise OperationalSlaDeadlineError("Business calendar metadata was not found.")
        updates = self._payload(payload, exclude_unset=True)
        if not updates:
            raise OperationalSlaDeadlineError("No business calendar metadata updates were provided.")
        merged = {**existing, **updates}
        self._normalize_calendar(merged, partial=True)
        if "calendar_code" in updates and updates["calendar_code"]:
            updates["calendar_code"] = self._norm(updates["calendar_code"])
        if "status" in updates and updates["status"]:
            updates["status"] = self._norm(updates["status"])
        updates["updated_by"] = user.get("id")
        updated = await self.db.collection(OPERATIONAL_BUSINESS_CALENDARS_COLLECTION).update_one({"id": calendar_id}, updates)
        if not updated:
            raise OperationalSlaDeadlineError("Business calendar metadata could not be updated.")
        return {"phase": PHASE_LABEL, "business_calendar": updated, "metadata_only": True, **self.safety_flags()}

    async def list_deadlines(
        self,
        *,
        agency_id: str | None = None,
        status: str | None = None,
        breach_state: str | None = None,
        deadline_type: str | None = None,
        priority: str | None = None,
        service_family: str | None = None,
        source_entity_type: str | None = None,
        source_entity_id: str | None = None,
        workflow_instance_id: str | None = None,
        work_item_id: str | None = None,
        include_completed: bool = False,
        due_before: str | datetime | None = None,
        due_after: str | datetime | None = None,
        **_: Any,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        for field, value in [
            ("status", status),
            ("breach_state", breach_state),
            ("deadline_type", deadline_type),
            ("priority", priority),
            ("service_family", service_family),
            ("source_entity_type", source_entity_type),
            ("source_entity_id", source_entity_id),
            ("workflow_instance_id", workflow_instance_id),
            ("work_item_id", work_item_id),
        ]:
            if value:
                filters[field] = self._norm(value) if field not in {"source_entity_id", "workflow_instance_id", "work_item_id"} else value
        records = await self.db.collection(OPERATIONAL_DEADLINES_COLLECTION).find_many(filters or None)
        if not include_completed:
            records = [record for record in records if record.get("status") not in {"completed", "waived", "archived"}]
        if due_before:
            cutoff = self._parse_dt(due_before)
            records = [record for record in records if cutoff and self._parse_dt(record.get("due_at")) and self._parse_dt(record.get("due_at")) <= cutoff]
        if due_after:
            cutoff = self._parse_dt(due_after)
            records = [record for record in records if cutoff and self._parse_dt(record.get("due_at")) and self._parse_dt(record.get("due_at")) >= cutoff]
        projected = [await self._deadline_projection(record) for record in records]
        projected.sort(key=self._deadline_ordering_key)
        return projected

    async def get_deadline(self, deadline_id: str, agency_id: str | None = None) -> dict[str, Any]:
        return await self._deadline_projection(await self._require_deadline(deadline_id, agency_id=agency_id))

    async def create_deadline(
        self,
        payload: OperationalDeadlineCreate | dict[str, Any],
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        data = self._payload(payload)
        if agency_id:
            data["agency_id"] = agency_id
        self._validate_deadline_payload(data)
        if not data.get("deadline_reference"):
            data["deadline_reference"] = self._deadline_reference(data["deadline_type"])
        started_at = self._parse_dt(data.get("started_at")) or self._now()
        policy = await self.match_policy(data)
        calendar = await self._calendar_for_policy(policy, agency_id=data.get("agency_id"))
        provided_due_at = self._parse_dt(data.get("due_at"))
        if provided_due_at:
            due_at = provided_due_at
            calculation_snapshot = {
                "provided_due_at": True,
                "manual_due_date_source": "create_deadline_payload",
                "policy": policy,
                "calendar": calendar,
            }
            explanation = f"Deadline was recorded with a provided due date of {self._display_dt(due_at)}. Policy metadata is retained for future recalculation."
        else:
            due_at = self.calculate_due_at(started_at, policy, calendar)
            calculation_snapshot = self._calculation_snapshot(started_at, due_at, policy, calendar)
            explanation = self.explain_calculation(started_at, due_at, policy, calendar)
        status, breach_state = self._computed_status(due_at, data.get("status") or "open")
        record = OperationalDeadline(
            **{
                **data,
                "started_at": started_at,
                "policy_id": policy.get("id"),
                "policy_code": policy.get("policy_code"),
                "original_due_at": due_at,
                "calculated_due_at": due_at,
                "due_at": due_at,
                "status": status,
                "breach_state": breach_state,
                "explanation": explanation,
                "calculation_snapshot_json": calculation_snapshot,
                "escalation_suggestions": self.escalation_suggestions(due_at, policy, status=status, breach_state=breach_state),
                "created_by": user.get("id"),
                "updated_by": user.get("id"),
            }
        )
        created = await self.db.collection(OPERATIONAL_DEADLINES_COLLECTION).insert_one(record.model_dump(mode="json"))
        await self._record_event(created, "started", user, reason="SLA deadline metadata created.", payload={"policy_code": policy.get("policy_code")})
        await self._sync_work_queue_deadline(created, user)
        await self._emit_workflow_event(created, "started", user)
        await self._emit_timeline_event(created, "started", user)
        return {"phase": PHASE_LABEL, "deadline": await self._deadline_projection(created), "metadata_only": True, **self.safety_flags()}

    async def update_deadline(
        self,
        deadline_id: str,
        payload: OperationalDeadlineUpdate | dict[str, Any],
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_deadline(deadline_id, agency_id=agency_id)
        updates = self._payload(payload, exclude_unset=True)
        if not updates:
            raise OperationalSlaDeadlineError("No deadline metadata updates were provided.")
        if "deadline_type" in updates and updates["deadline_type"]:
            updates["deadline_type"] = self._norm(updates["deadline_type"])
        for field in ["status", "breach_state", "priority", "service_family", "source_entity_type"]:
            if field in updates and updates[field] is not None:
                updates[field] = self._norm(updates[field])
        if "due_at" in updates and updates["due_at"]:
            due_at = self._parse_dt(updates["due_at"])
            updates["due_at"] = due_at
            updates["manual_extension_approved"] = True
            updates["extended_at"] = self._now()
            updates["extension_reason"] = "Manual deadline metadata update."
            status_value, breach_value = self._computed_status(due_at, updates.get("status") or existing.get("status") or "open")
            updates["status"] = status_value
            updates["breach_state"] = breach_value
        updates["updated_by"] = user.get("id")
        updated = await self.db.collection(OPERATIONAL_DEADLINES_COLLECTION).update_one({"id": existing["id"]}, updates)
        if not updated:
            raise OperationalSlaDeadlineError("Deadline metadata could not be updated.")
        await self._record_event(updated, "recalculated" if "due_at" in updates else "warning", user, reason="Deadline metadata updated.", payload={"updated_fields": sorted(updates)})
        await self._sync_work_queue_deadline(updated, user)
        return {"phase": PHASE_LABEL, "deadline": await self._deadline_projection(updated), "metadata_only": True, **self.safety_flags()}

    async def apply_action(
        self,
        deadline_id: str,
        action: str,
        payload: OperationalDeadlineActionRequest | dict[str, Any],
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        deadline = await self._require_deadline(deadline_id, agency_id=agency_id)
        data = self._payload(payload)
        action = self._norm(action)
        now = self._now()
        updates: dict[str, Any] = {"updated_by": user.get("id")}
        event_type = action
        reason = data.get("reason")

        if action == "pause":
            if deadline.get("status") != "paused":
                updates.update({"status": "paused", "breach_state": "paused", "paused_at": now})
            event_type = "paused"
        elif action == "resume":
            paused_at = self._parse_dt(deadline.get("paused_at"))
            paused_minutes = 0
            if paused_at:
                paused_minutes = max(0, int((now - paused_at).total_seconds() // 60))
            due_at = self._parse_dt(deadline.get("due_at")) or now
            new_due_at = due_at + timedelta(minutes=paused_minutes)
            status_value, breach_value = self._computed_status(new_due_at, "open")
            updates.update(
                {
                    "status": status_value,
                    "breach_state": breach_value,
                    "paused_at": None,
                    "paused_duration_minutes": int(deadline.get("paused_duration_minutes") or 0) + paused_minutes,
                    "due_at": new_due_at,
                    "explanation": f"Deadline resumed after {paused_minutes} paused minutes. The due date was shifted to preserve the pause interval.",
                }
            )
            event_type = "resumed"
        elif action == "extend":
            due_at = self._parse_dt(data.get("due_at"))
            if not due_at:
                raise OperationalSlaDeadlineError("Extension requires a due_at value.")
            status_value, breach_value = self._computed_status(due_at, "extended")
            updates.update(
                {
                    "due_at": due_at,
                    "status": status_value if status_value in {"due_soon", "overdue"} else "extended",
                    "breach_state": breach_value,
                    "extended_at": now,
                    "extension_reason": reason,
                    "manual_extension_approved": True,
                    "explanation": reason or f"Deadline manually extended to {self._display_dt(due_at)}.",
                }
            )
            event_type = "extended"
        elif action == "complete":
            updates.update({"status": "completed", "breach_state": "completed", "completed_at": now})
            event_type = "completed"
        elif action == "waive":
            updates.update({"status": "waived", "breach_state": "waived", "waived_at": now, "explanation": reason or "Deadline waived by human review."})
            event_type = "waived"
        elif action == "recalculate":
            if deadline.get("manual_extension_approved") and not data.get("force_recalculate"):
                await self._record_event(
                    deadline,
                    "recalculated",
                    user,
                    reason=reason or "Manual extension preserved; recalculation was skipped.",
                    payload={"manual_extension_preserved": True},
                )
                return {"phase": PHASE_LABEL, "deadline": await self._deadline_projection(deadline), "manual_extension_preserved": True, "metadata_only": True, **self.safety_flags()}
            policy = await self.match_policy(deadline)
            calendar = await self._calendar_for_policy(policy, agency_id=deadline.get("agency_id"))
            started_at = self._parse_dt(deadline.get("started_at")) or now
            due_at = self.calculate_due_at(started_at, policy, calendar)
            status_value, breach_value = self._computed_status(due_at, "open")
            updates.update(
                {
                    "policy_id": policy.get("id"),
                    "policy_code": policy.get("policy_code"),
                    "calculated_due_at": due_at,
                    "due_at": due_at,
                    "status": status_value,
                    "breach_state": breach_value,
                    "explanation": self.explain_calculation(started_at, due_at, policy, calendar),
                    "calculation_snapshot_json": self._calculation_snapshot(started_at, due_at, policy, calendar),
                    "manual_extension_approved": False,
                }
            )
            event_type = "recalculated"
        else:
            raise OperationalSlaDeadlineError(f"Unsupported SLA deadline action metadata: {action}.")

        updated = await self.db.collection(OPERATIONAL_DEADLINES_COLLECTION).update_one({"id": deadline["id"]}, updates)
        if not updated:
            raise OperationalSlaDeadlineError("SLA deadline action could not be recorded.")
        await self._record_event(updated, event_type, user, reason=reason, from_status=deadline.get("status"), to_status=updates.get("status"), payload={"action": action, "metadata": data.get("metadata") or {}})
        await self._sync_work_queue_deadline(updated, user)
        await self._emit_workflow_event(updated, event_type, user)
        await self._emit_timeline_event(updated, event_type, user)
        return {"phase": PHASE_LABEL, "deadline": await self._deadline_projection(updated), "action": event_type, "metadata_only": True, **self.safety_flags()}

    async def monitor_deadlines(self, agency_id: str | None = None, user: dict | None = None) -> dict[str, Any]:
        records = await self.db.collection(OPERATIONAL_DEADLINES_COLLECTION).find_many({"agency_id": agency_id} if agency_id else None)
        changed: list[dict[str, Any]] = []
        actor = user or {"id": "system_metadata_monitor"}
        for record in records:
            if record.get("status") in {"paused", "completed", "waived", "archived"}:
                continue
            due_at = self._parse_dt(record.get("due_at"))
            if not due_at:
                continue
            status_value, breach_value = self._computed_status(due_at, record.get("status") or "open")
            if status_value == record.get("status") and breach_value == record.get("breach_state"):
                continue
            updated = await self.db.collection(OPERATIONAL_DEADLINES_COLLECTION).update_one(
                {"id": record["id"]},
                {"status": status_value, "breach_state": breach_value, "updated_by": actor.get("id")},
            )
            if updated:
                event_type = "breached" if breach_value == "breached" else "warning"
                await self._record_event(updated, event_type, actor, reason="SLA deadline monitoring metadata refresh.", payload={"previous_status": record.get("status")})
                await self._sync_work_queue_deadline(updated, actor)
                changed.append(await self._deadline_projection(updated))
        return {"phase": PHASE_LABEL, "updated_count": len(changed), "deadlines": changed, "metadata_only": True, **self.safety_flags()}

    async def list_events(self, deadline_id: str, agency_id: str | None = None) -> list[dict[str, Any]]:
        filters = {"deadline_id": deadline_id}
        if agency_id:
            filters["agency_id"] = agency_id
        events = await self.db.collection(OPERATIONAL_SLA_EVENTS_COLLECTION).find_many(filters)
        events.sort(key=lambda item: self._sort_text(item.get("created_at")))
        return events

    async def match_policy(self, source: dict[str, Any]) -> dict[str, Any]:
        source_deadline_type = self._norm(source.get("deadline_type") or "")
        source_policy_id = source.get("policy_id")
        source_policy_code = self._norm(source.get("policy_code") or "")
        agency_id = source.get("agency_id")
        if source_policy_id:
            policy = await self.db.collection(OPERATIONAL_SLA_POLICIES_COLLECTION).find_one({"id": source_policy_id})
            if policy and (not policy.get("agency_id") or not agency_id or policy.get("agency_id") == agency_id):
                return policy
        if source_policy_code:
            candidates = await self.db.collection(OPERATIONAL_SLA_POLICIES_COLLECTION).find_many({"policy_code": source_policy_code})
            policy = self._best_policy(candidates, source)
            if policy:
                return policy
        persisted = await self.db.collection(OPERATIONAL_SLA_POLICIES_COLLECTION).find_many({"status": "active"})
        policy = self._best_policy(persisted, source)
        if policy:
            return policy
        for default in DEFAULT_SLA_POLICIES:
            if default["deadline_type"] == source_deadline_type:
                return self._default_policy(default, agency_id=agency_id)
        raise OperationalSlaDeadlineError(f"No SLA policy metadata matched deadline type {source_deadline_type}.")

    def calculate_due_at(self, started_at: datetime, policy: dict[str, Any], calendar: dict[str, Any] | None = None) -> datetime:
        duration = self._duration(policy)
        if self._norm(policy.get("business_hours_behavior") or "calendar_hours") != "business_hours":
            return started_at + duration
        calendar = calendar or self._default_calendar(agency_id=policy.get("agency_id"))
        timezone_name = calendar.get("timezone") or policy.get("timezone") or "UTC"
        tz = self._zone(timezone_name)
        current = self._to_zone(started_at, tz)
        remaining_minutes = int(duration.total_seconds() // 60)
        if remaining_minutes <= 0:
            return current
        current = self._next_business_instant(current, calendar, tz)
        while remaining_minutes > 0:
            window_start, window_end = self._working_window(current, calendar, tz)
            if current < window_start:
                current = window_start
            available_minutes = max(0, int((window_end - current).total_seconds() // 60))
            if available_minutes <= 0:
                current = self._next_business_instant(current + timedelta(days=1), calendar, tz)
                continue
            step = min(remaining_minutes, available_minutes)
            current += timedelta(minutes=step)
            remaining_minutes -= step
            if remaining_minutes > 0:
                current = self._next_business_instant(current + timedelta(minutes=1), calendar, tz)
        return current.astimezone(timezone.utc)

    def explain_calculation(self, started_at: datetime, due_at: datetime, policy: dict[str, Any], calendar: dict[str, Any] | None = None) -> str:
        behavior = self._norm(policy.get("business_hours_behavior") or "calendar_hours")
        duration_value = policy.get("duration_value")
        duration_unit = policy.get("duration_unit")
        basis = "business hours" if behavior == "business_hours" else "calendar time"
        calendar_label = (calendar or {}).get("calendar_code") or "default calendar"
        return (
            f"{self._label(policy.get('deadline_type'))} uses policy {policy.get('policy_code')} "
            f"with {duration_value} {duration_unit} measured in {basis}. Start {self._display_dt(started_at)}; "
            f"due {self._display_dt(due_at)} using {calendar_label}. This is advisory metadata only."
        )

    def escalation_suggestions(self, due_at: datetime, policy: dict[str, Any], *, status: str, breach_state: str) -> list[dict[str, Any]]:
        suggestions: list[dict[str, Any]] = []
        thresholds = policy.get("escalation_thresholds_json") or []
        if not thresholds:
            thresholds = [{"minutes_before_due": 60, "suggestion": "Review owner and queue assignment before due time."}]
        for threshold in thresholds:
            suggestions.append(
                {
                    "threshold": threshold,
                    "due_at": due_at,
                    "status": status,
                    "breach_state": breach_state,
                    "suggested_action": threshold.get("suggestion") or threshold.get("action") or "Escalate to the responsible operational owner for human review.",
                    "metadata_only": True,
                }
            )
        if breach_state == "breached":
            suggestions.append({"suggested_action": "Review breach reason, update timeline notes, and assign urgent work item.", "metadata_only": True})
        return suggestions

    def summarize_deadlines(self, deadlines: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "deadline_count": len(deadlines),
            "due_soon_count": len([item for item in deadlines if item.get("status") == "due_soon" or item.get("breach_state") == "due_soon"]),
            "overdue_count": len([item for item in deadlines if item.get("status") == "overdue" or item.get("breach_state") == "breached"]),
            "paused_count": len([item for item in deadlines if item.get("status") == "paused"]),
            "completed_count": len([item for item in deadlines if item.get("status") == "completed"]),
            "waived_count": len([item for item in deadlines if item.get("status") == "waived"]),
            "by_status": self._counts(deadlines, "status", DEADLINE_STATUSES),
            "by_breach_state": self._counts(deadlines, "breach_state", BREACH_STATES),
            "by_deadline_type": self._counts(deadlines, "deadline_type", DEADLINE_TYPES),
            "by_priority": self._counts(deadlines, "priority", ["critical", "urgent", "high", "normal", "low"]),
        }

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "sla_operational_deadline_engine_foundation": True,
            "deadline_calculation_enabled": True,
            "business_calendar_calculation_enabled": True,
            "pause_resume_metadata_enabled": True,
            "extension_audit_enabled": True,
            "manual_extensions_preserved": True,
            "work_queue_integration_enabled": True,
            "workflow_event_integration_enabled": True,
            "timeline_history_integration_enabled": True,
            "agency_isolation_enforced": True,
            "provider_integrations_disabled": True,
            "external_api_calls_disabled": True,
            "ai_disabled": True,
            "background_workers_disabled": True,
            "schedulers_disabled": True,
            "automatic_execution_disabled": True,
            "automation_disabled": True,
            "enforcement_disabled": True,
            "human_authority_final": True,
        }

    async def _deadline_projection(self, record: dict[str, Any]) -> dict[str, Any]:
        projected = dict(record)
        if projected.get("status") not in {"paused", "completed", "waived", "archived"}:
            due_at = self._parse_dt(projected.get("due_at"))
            if due_at:
                projected["computed_status"], projected["computed_breach_state"] = self._computed_status(due_at, projected.get("status") or "open")
                if projected.get("status") in {"open", "due_soon", "overdue"}:
                    projected["status"] = projected["computed_status"]
                    projected["breach_state"] = projected["computed_breach_state"]
        projected["sla_status"] = self._queue_sla_status(projected)
        projected["events"] = (await self.list_events(projected["id"], agency_id=projected.get("agency_id")))[-8:]
        projected["escalation_suggestions"] = projected.get("escalation_suggestions") or self.escalation_suggestions(
            self._parse_dt(projected.get("due_at")) or self._now(),
            projected.get("calculation_snapshot_json", {}).get("policy") or {},
            status=projected.get("status") or "open",
            breach_state=projected.get("breach_state") or "not_breached",
        )
        projected.update(self.safety_flags())
        return projected

    async def _require_deadline(self, deadline_id: str, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": deadline_id}
        if agency_id:
            filters["agency_id"] = agency_id
        deadline = await self.db.collection(OPERATIONAL_DEADLINES_COLLECTION).find_one(filters)
        if not deadline:
            alt_filters = {"deadline_reference": deadline_id}
            if agency_id:
                alt_filters["agency_id"] = agency_id
            deadline = await self.db.collection(OPERATIONAL_DEADLINES_COLLECTION).find_one(alt_filters)
        if not deadline:
            raise OperationalSlaDeadlineError("SLA deadline metadata was not found.")
        return deadline

    async def _record_event(
        self,
        deadline: dict[str, Any],
        event_type: str,
        user: dict,
        *,
        reason: str | None = None,
        from_status: str | None = None,
        to_status: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        event = OperationalSlaEvent(
            agency_id=deadline["agency_id"],
            deadline_id=deadline["id"],
            event_type=self._norm(event_type),
            from_status=from_status,
            to_status=to_status,
            reason=reason,
            actor_user_id=user.get("id"),
            payload_json=payload or {},
        )
        return await self.db.collection(OPERATIONAL_SLA_EVENTS_COLLECTION).insert_one(event.model_dump(mode="json"))

    async def _sync_work_queue_deadline(self, deadline: dict[str, Any], user: dict) -> None:
        try:
            from services.agent_work_queue_service import AgentWorkQueueService, OPERATIONAL_WORK_ITEMS_COLLECTION
        except ImportError:
            return
        service = AgentWorkQueueService(self.db)
        sla_status = self._queue_sla_status(deadline)
        if deadline.get("work_item_id"):
            work_item = await self.db.collection(OPERATIONAL_WORK_ITEMS_COLLECTION).find_one({"id": deadline["work_item_id"], "agency_id": deadline["agency_id"]})
            if work_item:
                context = {
                    **(work_item.get("internal_context_json") or {}),
                    "sla_deadline_id": deadline.get("id"),
                    "sla_deadline_reference": deadline.get("deadline_reference"),
                    "sla_deadline_type": deadline.get("deadline_type"),
                    "sla_explanation": deadline.get("explanation"),
                }
                await self.db.collection(OPERATIONAL_WORK_ITEMS_COLLECTION).update_one(
                    {"id": work_item["id"]},
                    {"due_at": deadline.get("due_at"), "sla_status": sla_status, "internal_context_json": context, "updated_by": user.get("id")},
                )
            return
        await service.generate_work_item(
            {
                "agency_id": deadline["agency_id"],
                "work_item_type": self._work_item_type_for_deadline(deadline),
                "source_entity_type": deadline.get("source_entity_type") or "deadline",
                "source_entity_id": deadline.get("source_entity_id") or deadline["id"],
                "workflow_instance_id": deadline.get("workflow_instance_id"),
                "workflow_event_id": deadline.get("workflow_event_id"),
                "request_task_id": deadline.get("request_task_id"),
                "timeline_entry_id": deadline.get("timeline_entry_id"),
                "title": f"{self._label(deadline.get('deadline_type'))} deadline",
                "summary": deadline.get("explanation"),
                "priority": deadline.get("priority") or "normal",
                "severity": "high" if sla_status in {"overdue", "breached"} else "medium",
                "queue_code": self._queue_code_for_deadline(deadline),
                "due_at": deadline.get("due_at"),
                "sla_status": sla_status,
                "blocker_status": self._blocker_for_deadline(deadline),
                "generation_reason": "sla_operational_deadline_integration",
                "source_snapshot_json": deadline,
                "compatibility_mapping_json": {"operational_deadline_id": deadline.get("id")},
            },
            user,
            agency_id=deadline["agency_id"],
        )

    async def _emit_workflow_event(self, deadline: dict[str, Any], event_type: str, user: dict) -> None:
        if not deadline.get("workflow_instance_id"):
            return
        await self.db.collection("operational_workflow_events").insert_one(
            {
                "id": new_id(),
                "agency_id": deadline["agency_id"],
                "workflow_instance_id": deadline.get("workflow_instance_id"),
                "event_code": f"sla_deadline_{self._norm(event_type)}",
                "event_type": f"sla_deadline_{self._norm(event_type)}",
                "event_status": "recorded",
                "source_module": "sla_operational_deadline_engine",
                "source_entity_type": "operational_deadline",
                "source_entity_id": deadline["id"],
                "payload_json": {"deadline_reference": deadline.get("deadline_reference"), "deadline_type": deadline.get("deadline_type"), "status": deadline.get("status")},
                "occurred_at": self._now(),
                "created_at": self._now(),
                "updated_at": self._now(),
                "created_by": user.get("id"),
                "metadata_only": True,
            }
        )

    async def _emit_timeline_event(self, deadline: dict[str, Any], event_type: str, user: dict) -> None:
        await self.db.collection("operational_timelines").insert_one(
            {
                "id": new_id(),
                "agency_id": deadline["agency_id"],
                "timeline_reference": f"SLA-{(deadline.get('deadline_reference') or deadline['id'])[-12:]}-{self._norm(event_type)}",
                "created_at": self._now(),
                "updated_at": self._now(),
                "created_by": user.get("id"),
                "event_type": f"SLA deadline {self._label(event_type)}",
                "event_category": "sla_deadline",
                "event_source": "sla_operational_deadline_engine",
                "event_status": "recorded",
                "event_priority": deadline.get("priority") or "normal",
                "operational_stage": "deadline_monitoring",
                "operational_result": deadline.get("status"),
                "summary": deadline.get("explanation"),
                "operational_notes": "Metadata-only SLA/deadline timeline entry. No messaging, provider calls, or automation occurred.",
                "internal_only": True,
                "passenger_visible": False,
                "airline_visible": False,
                "attachment_ids": [],
                "metadata_only": True,
                "operational_deadline_id": deadline["id"],
            }
        )

    async def _calendar_for_policy(self, policy: dict[str, Any], agency_id: str | None = None) -> dict[str, Any]:
        if policy.get("calendar_id"):
            calendar = await self.db.collection(OPERATIONAL_BUSINESS_CALENDARS_COLLECTION).find_one({"id": policy["calendar_id"]})
            if calendar and (not calendar.get("agency_id") or not agency_id or calendar.get("agency_id") == agency_id):
                return calendar
        calendars = await self.list_business_calendars(agency_id=agency_id, include_defaults=True, status="active")
        return calendars[0] if calendars else self._default_calendar(agency_id=agency_id)

    def _best_policy(self, candidates: list[dict[str, Any]], source: dict[str, Any]) -> dict[str, Any] | None:
        agency_id = source.get("agency_id")
        deadline_type = self._norm(source.get("deadline_type") or "")
        entity_type = self._norm(source.get("source_entity_type") or source.get("entity_type") or "")
        work_item_type = self._norm(source.get("work_item_type") or "")
        priority = self._norm(source.get("priority") or "")
        service_family = self._norm(source.get("service_family") or "")
        now = self._now()
        scored: list[tuple[int, dict[str, Any]]] = []
        for policy in candidates:
            if policy.get("status") and policy.get("status") != "active":
                continue
            if policy.get("agency_id") and policy.get("agency_id") != agency_id:
                continue
            if policy.get("deadline_type") and self._norm(policy.get("deadline_type")) != deadline_type:
                continue
            effective_from = self._parse_dt(policy.get("effective_from"))
            effective_to = self._parse_dt(policy.get("effective_to"))
            if effective_from and effective_from > now:
                continue
            if effective_to and effective_to < now:
                continue
            score = 0
            if policy.get("agency_id") == agency_id:
                score += 100
            if self._norm(policy.get("entity_type") or "") == entity_type:
                score += 20
            if policy.get("work_item_type") and self._norm(policy["work_item_type"]) == work_item_type:
                score += 15
            elif not policy.get("work_item_type"):
                score += 2
            if policy.get("priority") and self._norm(policy["priority"]) == priority:
                score += 10
            elif not policy.get("priority"):
                score += 1
            if policy.get("service_family") and self._norm(policy["service_family"]) == service_family:
                score += 10
            elif not policy.get("service_family"):
                score += 1
            scored.append((score, policy))
        scored.sort(key=lambda item: item[0], reverse=True)
        return scored[0][1] if scored else None

    def _validate_deadline_payload(self, data: dict[str, Any]) -> None:
        for field in ["agency_id", "source_entity_type", "source_entity_id", "deadline_type"]:
            if not data.get(field):
                raise OperationalSlaDeadlineError(f"{field} is required for SLA deadline metadata.")
        data["deadline_type"] = self._norm(data["deadline_type"])
        if data["deadline_type"] not in DEADLINE_TYPES:
            raise OperationalSlaDeadlineError(f"Unsupported deadline type metadata: {data['deadline_type']}.")
        data["source_entity_type"] = self._norm(data["source_entity_type"])
        data["priority"] = self._norm(data.get("priority") or "normal")
        if data.get("service_family"):
            data["service_family"] = self._norm(data["service_family"])
        if data.get("status"):
            data["status"] = self._norm(data["status"])
            if data["status"] not in DEADLINE_STATUSES:
                raise OperationalSlaDeadlineError(f"Unsupported deadline status metadata: {data['status']}.")

    def _normalize_policy(self, data: dict[str, Any], *, partial: bool = False) -> None:
        if not partial:
            for field in ["name", "entity_type", "deadline_type"]:
                if not data.get(field):
                    raise OperationalSlaDeadlineError(f"{field} is required for SLA policy metadata.")
        for field in ["scope", "policy_code", "entity_type", "work_item_type", "deadline_type", "priority", "service_family", "duration_unit", "business_hours_behavior", "status"]:
            if data.get(field):
                data[field] = self._norm(data[field])
        if data.get("scope") and data["scope"] not in SLA_POLICY_SCOPES:
            raise OperationalSlaDeadlineError(f"Unsupported SLA policy scope metadata: {data['scope']}.")
        if data.get("deadline_type") and data["deadline_type"] not in DEADLINE_TYPES:
            raise OperationalSlaDeadlineError(f"Unsupported deadline type metadata: {data['deadline_type']}.")
        if data.get("duration_unit") and data["duration_unit"] not in SLA_DURATION_UNITS:
            raise OperationalSlaDeadlineError(f"Unsupported duration unit metadata: {data['duration_unit']}.")
        if data.get("business_hours_behavior") and data["business_hours_behavior"] not in BUSINESS_HOURS_BEHAVIORS:
            raise OperationalSlaDeadlineError(f"Unsupported business-hours behavior metadata: {data['business_hours_behavior']}.")
        if data.get("status") and data["status"] not in SLA_POLICY_STATUSES:
            raise OperationalSlaDeadlineError(f"Unsupported SLA policy status metadata: {data['status']}.")
        if int(data.get("duration_value") or 0) <= 0:
            raise OperationalSlaDeadlineError("SLA duration must be greater than zero.")

    def _normalize_calendar(self, data: dict[str, Any], *, partial: bool = False) -> None:
        if not partial:
            for field in ["name", "calendar_code"]:
                if not data.get(field):
                    raise OperationalSlaDeadlineError(f"{field} is required for business calendar metadata.")
        if data.get("calendar_code"):
            data["calendar_code"] = self._norm(data["calendar_code"])
        if data.get("status"):
            data["status"] = self._norm(data["status"])
        self._zone(data.get("timezone") or "UTC")
        for day in data.get("working_days") or []:
            if not isinstance(day, int) or day < 0 or day > 6:
                raise OperationalSlaDeadlineError("Business calendar working_days must use integers 0-6.")
        hours = data.get("working_hours_json") or {}
        if hours:
            self._parse_time(hours.get("start", "09:00"))
            self._parse_time(hours.get("end", "17:00"))

    def _computed_status(self, due_at: datetime, current_status: str = "open") -> tuple[str, str]:
        normalized = self._norm(current_status)
        if normalized in {"paused", "completed", "waived", "archived"}:
            return normalized, {"paused": "paused", "completed": "completed", "waived": "waived", "archived": "not_breached"}[normalized]
        now = self._now()
        if due_at < now:
            return "overdue", "breached"
        if (due_at - now).total_seconds() <= 24 * 60 * 60:
            return "due_soon", "due_soon"
        return "open" if normalized not in {"extended"} else "extended", "not_breached"

    def _queue_sla_status(self, deadline: dict[str, Any]) -> str:
        status = self._norm(deadline.get("status") or "")
        breach_state = self._norm(deadline.get("breach_state") or "")
        if status == "completed" or breach_state == "completed":
            return "completed"
        if status == "paused" or breach_state == "paused":
            return "paused"
        if status == "overdue" or breach_state == "breached":
            return "breached"
        if status == "due_soon" or breach_state == "due_soon":
            return "due_soon"
        return "on_track"

    def _work_item_type_for_deadline(self, deadline: dict[str, Any]) -> str:
        mapping = {
            "request_response_sla": "new_request_triage",
            "offer_preparation_deadline": "offer_preparation_required",
            "offer_expiry": "offer_awaiting_response",
            "ticketing_deadline": "booking_awaiting_ticketing",
            "airline_approval_deadline": "service_approval_document_requirement",
            "medif_document_deadline": "document_missing_or_expiring",
            "payment_deadline": "task_deadline",
            "booking_ticketing_deadline": "booking_awaiting_ticketing",
            "task_deadline": "task_deadline",
            "disruption_response_deadline": "disruption",
            "claim_refund_change_deadline": "claim_service_case",
        }
        return mapping.get(self._norm(deadline.get("deadline_type") or ""), "task_deadline")

    def _queue_code_for_deadline(self, deadline: dict[str, Any]) -> str:
        sla_status = self._queue_sla_status(deadline)
        if sla_status == "due_soon":
            return "due_soon"
        if sla_status in {"overdue", "breached"}:
            return "overdue"
        deadline_type = self._norm(deadline.get("deadline_type") or "")
        if "document" in deadline_type or "medif" in deadline_type:
            return "waiting_documents"
        if "approval" in deadline_type:
            return "waiting_approval"
        if "payment" in deadline_type:
            return "waiting_payment"
        if "disruption" in deadline_type:
            return "disruption_queue"
        return "unassigned"

    def _blocker_for_deadline(self, deadline: dict[str, Any]) -> str:
        deadline_type = self._norm(deadline.get("deadline_type") or "")
        if "document" in deadline_type or "medif" in deadline_type:
            return "waiting_documents"
        if "approval" in deadline_type:
            return "waiting_approval"
        if "payment" in deadline_type:
            return "waiting_payment"
        return "not_blocked"

    def _calculation_snapshot(self, started_at: datetime, due_at: datetime, policy: dict[str, Any], calendar: dict[str, Any] | None) -> dict[str, Any]:
        return {
            "started_at": started_at,
            "due_at": due_at,
            "policy": policy,
            "calendar": calendar or {},
            "duration": {"value": policy.get("duration_value"), "unit": policy.get("duration_unit")},
            "business_hours_behavior": policy.get("business_hours_behavior"),
            "manual_extension_preservation_enabled": True,
            "metadata_only": True,
        }

    def _duration(self, policy: dict[str, Any]) -> timedelta:
        value = int(policy.get("duration_value") or 1)
        unit = self._norm(policy.get("duration_unit") or "hours")
        if unit == "minutes":
            return timedelta(minutes=value)
        if unit == "days":
            return timedelta(days=value)
        return timedelta(hours=value)

    def _default_policy(self, policy: dict[str, Any], agency_id: str | None = None) -> dict[str, Any]:
        deadline_type = policy["deadline_type"]
        return {
            "id": f"default-{deadline_type}",
            "agency_id": agency_id,
            "scope": "agency" if agency_id else "platform",
            "policy_code": f"default_{deadline_type}",
            "name": policy.get("name") or self._label(deadline_type),
            "entity_type": policy.get("entity_type") or "manual",
            "work_item_type": policy.get("work_item_type"),
            "deadline_type": deadline_type,
            "priority": policy.get("priority"),
            "service_family": policy.get("service_family"),
            "route_context_json": {},
            "flight_context_json": {},
            "duration_value": policy.get("duration_value") or 1,
            "duration_unit": policy.get("duration_unit") or "hours",
            "business_hours_behavior": policy.get("business_hours_behavior") or "calendar_hours",
            "calendar_id": None,
            "pause_conditions": ["waiting_client", "waiting_airline_supplier", "waiting_documents", "waiting_approval", "waiting_payment"],
            "escalation_thresholds_json": [{"minutes_before_due": 60, "suggestion": "Review owner and queue assignment before due time."}],
            "status": "active",
            "effective_from": None,
            "effective_to": None,
            "timezone": "UTC",
            "metadata_only": True,
            "is_default": True,
            "sla_operational_deadline_engine_foundation": True,
        }

    def _default_calendar(self, agency_id: str | None = None) -> dict[str, Any]:
        return {
            "id": "default-business-calendar",
            "agency_id": agency_id,
            "calendar_code": "default_business_calendar",
            "name": "Default Business Calendar",
            "timezone": "UTC",
            "working_days": [0, 1, 2, 3, 4],
            "working_hours_json": {"start": "09:00", "end": "17:00"},
            "holidays": [],
            "exceptions": [],
            "status": "active",
            "metadata_only": True,
            "is_default": True,
            "sla_operational_deadline_engine_foundation": True,
        }

    def _next_business_instant(self, value: datetime, calendar: dict[str, Any], tz: ZoneInfo) -> datetime:
        current = self._to_zone(value, tz)
        for _ in range(366):
            if self._is_working_day(current, calendar):
                window_start, window_end = self._working_window(current, calendar, tz)
                if current < window_start:
                    return window_start
                if window_start <= current < window_end:
                    return current
            next_day = current.date() + timedelta(days=1)
            current = datetime.combine(next_day, self._parse_time((calendar.get("working_hours_json") or {}).get("start", "09:00")), tzinfo=tz)
        raise OperationalSlaDeadlineError("Business calendar could not find a working instant within one year.")

    def _working_window(self, value: datetime, calendar: dict[str, Any], tz: ZoneInfo) -> tuple[datetime, datetime]:
        hours = calendar.get("working_hours_json") or {}
        start = self._parse_time(hours.get("start", "09:00"))
        end = self._parse_time(hours.get("end", "17:00"))
        return (
            datetime.combine(value.date(), start, tzinfo=tz),
            datetime.combine(value.date(), end, tzinfo=tz),
        )

    def _is_working_day(self, value: datetime, calendar: dict[str, Any]) -> bool:
        date_text = value.date().isoformat()
        for exception in calendar.get("exceptions") or []:
            if exception.get("date") == date_text and exception.get("closed") is True:
                return False
        if date_text in set(calendar.get("holidays") or []):
            return False
        return value.weekday() in set(calendar.get("working_days") or [0, 1, 2, 3, 4])

    def _parse_time(self, value: str | None) -> time:
        if not value:
            value = "09:00"
        try:
            hour, minute = str(value).split(":", 1)
            return time(int(hour), int(minute[:2]))
        except (ValueError, TypeError) as exc:
            raise OperationalSlaDeadlineError(f"Invalid business calendar time metadata: {value}.") from exc

    def _zone(self, timezone_name: str) -> ZoneInfo:
        try:
            return ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError as exc:
            raise OperationalSlaDeadlineError(f"Unsupported business calendar timezone metadata: {timezone_name}.") from exc

    def _to_zone(self, value: datetime, tz: ZoneInfo) -> datetime:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(tz)

    def _deadline_ordering_key(self, item: dict[str, Any]) -> tuple[Any, ...]:
        status_rank = {"overdue": 0, "due_soon": 1, "paused": 2, "open": 3, "extended": 4, "completed": 5, "waived": 6, "archived": 7}
        priority_rank = {"critical": 0, "urgent": 1, "high": 2, "normal": 3, "low": 4}
        due_at = self._parse_dt(item.get("due_at")) or datetime.max.replace(tzinfo=timezone.utc)
        return (status_rank.get(item.get("status"), 9), priority_rank.get(item.get("priority"), 5), due_at, self._sort_text(item.get("created_at")))

    def _policy_code(self, deadline_type: str, priority: str | None = None) -> str:
        suffix = f"_{self._norm(priority)}" if priority else ""
        return f"sla_{self._norm(deadline_type)}{suffix}"

    def _calendar_code(self, name: str) -> str:
        return f"calendar_{self._norm(name)}_{new_id()[:8]}"

    def _deadline_reference(self, deadline_type: str) -> str:
        return f"SLA-{self._norm(deadline_type).upper().replace('_', '-')}-{new_id()[:8].upper()}"

    def _counts(self, records: list[dict[str, Any]], field: str, values: list[str]) -> dict[str, int]:
        counts = {value: 0 for value in values}
        for record in records:
            value = self._norm(record.get(field) or "unset")
            counts[value] = counts.get(value, 0) + 1
        return counts

    def _payload(self, payload: Any, *, exclude_unset: bool = False) -> dict[str, Any]:
        if hasattr(payload, "model_dump"):
            return payload.model_dump(mode="json", exclude_unset=exclude_unset, exclude_none=True)
        return dict(payload or {})

    def _parse_dt(self, value: Any) -> datetime | None:
        if not value:
            return None
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        text = str(value)
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)

    def _display_dt(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _sort_text(self, value: Any) -> str:
        return "" if value is None else str(value)

    def _label(self, value: Any) -> str:
        return str(value or "").replace("_", " ").replace("-", " ").strip().title() or "Unset"

    def _norm(self, value: Any) -> str:
        return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")
