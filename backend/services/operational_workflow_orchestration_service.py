from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import (
    OperationalWorkflowDefinition,
    OperationalWorkflowDefinitionCreate,
    OperationalWorkflowDefinitionUpdate,
    OperationalWorkflowEvent,
    OperationalWorkflowGuard,
    OperationalWorkflowGuardCreate,
    OperationalWorkflowGuardUpdate,
    OperationalWorkflowInstance,
    OperationalWorkflowInstanceStartRequest,
    OperationalWorkflowTransition,
    OperationalWorkflowTransitionRequest,
    OperationalWorkflowWarningAcknowledgementRequest,
    new_id,
)


PHASE_LABEL = "phase_54_8_operations_command_center_foundation"

OPERATIONAL_WORKFLOW_DEFINITIONS_COLLECTION = "operational_workflow_definitions"
OPERATIONAL_WORKFLOW_INSTANCES_COLLECTION = "operational_workflow_instances"
OPERATIONAL_WORKFLOW_TRANSITIONS_COLLECTION = "operational_workflow_transitions"
OPERATIONAL_WORKFLOW_GUARDS_COLLECTION = "operational_workflow_guards"
OPERATIONAL_WORKFLOW_EVENTS_COLLECTION = "operational_workflow_events"

GUARD_RESULTS = ["passed", "warning", "blocked", "manual_review", "unknown"]
TRANSITION_STATUSES = [
    "completed",
    "completed_with_warnings",
    "blocked",
    "warning_acknowledgement_required",
    "manual_review_required",
    "unknown",
]
WORKFLOW_STATUSES = ["active", "completed", "suspended", "archived"]

REQUEST_LIFECYCLE_STATES = [
    "submitted",
    "triage",
    "information_required",
    "planning",
    "offer_preparation",
    "offer_sent",
    "accepted",
    "rejected",
    "converted_to_trip",
    "closed",
]
TRIP_LIFECYCLE_STATES = [
    "planning",
    "offer_in_progress",
    "offer_sent",
    "accepted",
    "booking_in_progress",
    "booked",
    "ticketing_in_progress",
    "ticketed",
    "servicing",
    "disrupted",
    "completed",
    "archived",
]
BOOKING_READINESS_STATES = [
    "not_started",
    "incomplete",
    "blocked",
    "conditionally_ready",
    "ready",
    "booked",
]
SERVICE_FULFILLMENT_STATES = [
    "requested",
    "information_required",
    "policy_review",
    "airline_approval_required",
    "document_required",
    "pricing_required",
    "ready_to_request",
    "requested_from_airline",
    "confirmed",
    "rejected",
    "fulfilled",
    "cancelled",
]

GUARD_TYPES = [
    "required_client_passenger_linkage",
    "segment_precision",
    "accepted_offer",
    "policy_evaluation",
    "blocked_feasibility",
    "required_approval",
    "required_documents",
    "pricing_resolution",
    "booking_readiness",
    "payment_invoice_prerequisites",
    "ticket_emd_readiness",
    "unresolved_critical_pilot_readiness_issue",
    "unresolved_operational_blockers",
    "generic_metadata_check",
]

EXPLICIT_ENTITY_ADAPTERS: dict[str, dict[str, Any]] = {
    "request": {"collection": "travel_request_workspaces", "status_field": "request_status", "status_sync_enabled": False},
    "travel_request": {"collection": "travel_request_workspaces", "status_field": "request_status", "status_sync_enabled": False},
    "trip": {"collection": "trip_workspaces", "status_field": "trip_status", "status_sync_enabled": False},
    "offer": {"collection": "offer_workspaces_v2", "status_field": "offer_status", "status_sync_enabled": False},
    "booking": {"collection": "booking_workspaces", "status_field": "booking_status", "status_sync_enabled": False},
    "ticket": {"collection": "ticket_workspaces", "status_field": "ticket_status", "status_sync_enabled": False},
    "emd": {"collection": "emd_workspaces", "status_field": "emd_status", "status_sync_enabled": False},
    "service": {"collection": "passenger_service_workflows", "status_field": "current_stage", "status_sync_enabled": False},
}

ENTITY_STATUS_STATE_MAPS: dict[str, dict[str, str]] = {
    "request": {
        "new": "submitted",
        "triage": "triage",
        "waiting": "information_required",
        "researching": "planning",
        "quoted": "offer_sent",
        "completed": "closed",
        "archived": "closed",
    },
    "trip": {
        "draft": "planning",
        "planning": "planning",
        "active": "servicing",
        "ready": "ticketed",
        "traveling": "servicing",
        "completed": "completed",
        "archived": "archived",
    },
    "offer": {
        "draft": "offer_preparation",
        "preparing": "offer_preparation",
        "ready": "offer_sent",
        "shared": "offer_sent",
        "accepted": "accepted",
        "declined": "rejected",
        "expired": "rejected",
    },
    "booking": {
        "draft": "not_started",
        "ready_to_book": "ready",
        "booking_in_progress": "incomplete",
        "booked": "booked",
        "blocked": "blocked",
        "cancelled": "blocked",
    },
    "ticket": {
        "draft": "not_started",
        "ready": "ready",
        "issued": "booked",
        "blocked": "blocked",
        "cancelled": "blocked",
    },
    "emd": {
        "draft": "not_started",
        "ready": "ready",
        "issued": "booked",
        "blocked": "blocked",
        "cancelled": "blocked",
    },
    "service": {
        "documents_pending": "document_required",
        "waiting_for_approval": "airline_approval_required",
        "waiting_for_documents": "document_required",
        "ready": "ready_to_request",
        "completed": "fulfilled",
        "blocked": "information_required",
    },
}


def _state_map(states: list[str], terminal_states: set[str] | None = None) -> dict[str, Any]:
    terminal_states = terminal_states or set()
    return {
        state: {
            "label": state.replace("_", " ").title(),
            "terminal": state in terminal_states,
            "metadata_only": True,
        }
        for state in states
    }


def _transitions(states: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "transition_code": f"{states[index]}_to_{states[index + 1]}",
            "from_state": states[index],
            "to_state": states[index + 1],
            "label": f"{states[index].replace('_', ' ').title()} to {states[index + 1].replace('_', ' ').title()}",
            "guard_codes": [],
            "metadata_only": True,
        }
        for index in range(len(states) - 1)
    ]


DEFAULT_WORKFLOW_DEFINITIONS: list[dict[str, Any]] = [
    {
        "workflow_code": "request_lifecycle_default",
        "name": "Request Lifecycle",
        "description": "Canonical request lifecycle from submitted through triage, planning, offer, acceptance, conversion, and closure.",
        "entity_type": "request",
        "version": "1.0",
        "status": "active",
        "initial_state": "submitted",
        "terminal_states": ["accepted", "rejected", "converted_to_trip", "closed"],
        "state_definitions_json": _state_map(REQUEST_LIFECYCLE_STATES, {"accepted", "rejected", "converted_to_trip", "closed"}),
        "transition_definitions_json": _transitions(REQUEST_LIFECYCLE_STATES),
        "required_modules_json": ["travel_request_workspaces", "operational_timelines", "passenger_service_workflows"],
        "metadata_only": True,
    },
    {
        "workflow_code": "trip_lifecycle_default",
        "name": "Trip Lifecycle",
        "description": "Canonical trip lifecycle from planning through offer, booking, ticketing, servicing, completion, and archive.",
        "entity_type": "trip",
        "version": "1.0",
        "status": "active",
        "initial_state": "planning",
        "terminal_states": ["completed", "archived"],
        "state_definitions_json": _state_map(TRIP_LIFECYCLE_STATES, {"completed", "archived"}),
        "transition_definitions_json": _transitions(TRIP_LIFECYCLE_STATES),
        "required_modules_json": ["trip_workspaces", "offer_workspaces_v2", "booking_workspaces", "ticket_workspaces", "operational_timelines"],
        "metadata_only": True,
    },
    {
        "workflow_code": "booking_readiness_default",
        "name": "Booking Readiness",
        "description": "Canonical readiness path before a booking mirror reaches booked metadata status.",
        "entity_type": "booking",
        "version": "1.0",
        "status": "active",
        "initial_state": "not_started",
        "terminal_states": ["booked"],
        "state_definitions_json": _state_map(BOOKING_READINESS_STATES, {"booked"}),
        "transition_definitions_json": _transitions(BOOKING_READINESS_STATES),
        "required_modules_json": ["booking_workspaces", "offer_acceptances", "booking_readiness_packages"],
        "metadata_only": True,
    },
    {
        "workflow_code": "service_fulfillment_default",
        "name": "Service Fulfillment",
        "description": "Canonical passenger service fulfillment path from requested through policy, approval, document, pricing, airline request, confirmation, and fulfillment.",
        "entity_type": "service",
        "version": "1.0",
        "status": "active",
        "initial_state": "requested",
        "terminal_states": ["confirmed", "rejected", "fulfilled", "cancelled"],
        "state_definitions_json": _state_map(SERVICE_FULFILLMENT_STATES, {"confirmed", "rejected", "fulfilled", "cancelled"}),
        "transition_definitions_json": _transitions(SERVICE_FULFILLMENT_STATES),
        "required_modules_json": ["passenger_service_workflows", "ssr_osi_workspaces", "document_workspaces", "emd_workspaces"],
        "metadata_only": True,
    },
]


class OperationalWorkflowOrchestrationError(ValueError):
    pass


class OperationalWorkflowOrchestrationService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def platform_dashboard(self, **filters: Any) -> dict[str, Any]:
        definitions = await self.list_definitions(entity_type=filters.get("entity_type"), status=filters.get("status"), include_defaults=True)
        instances = await self.list_instances(
            agency_id=filters.get("agency_id"),
            entity_type=filters.get("entity_type"),
            workflow_status=filters.get("workflow_status"),
            current_state=filters.get("current_state"),
        )
        return {
            "phase": PHASE_LABEL,
            "definitions": definitions,
            "instances": instances,
            "guards": await self.list_guards(workflow_definition_id=filters.get("workflow_definition_id")),
            "summary": await self.summary(agency_id=filters.get("agency_id")),
            "state_transition_maps": self.state_transition_maps(),
            "diagnostics": await self.diagnostics(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Operational Workflow Orchestration coordinates workflow-state metadata and guarded transitions around existing workspaces. It does not replace workspace services, execute providers, run automation, or mutate entity statuses without explicit adapters.",
            **self.safety_flags(),
        }

    async def agency_dashboard(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        instances = await self.list_instances(
            agency_id=agency_id,
            entity_type=filters.get("entity_type"),
            workflow_status=filters.get("workflow_status"),
            current_state=filters.get("current_state"),
            entity_id=filters.get("entity_id"),
        )
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "instances": [self._agency_instance_projection(item) for item in instances],
            "summary": await self.summary(agency_id=agency_id),
            "state_transition_maps": self.state_transition_maps(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Agency workflow orchestration stores and transitions orchestration metadata only. It does not create bookings, issue tickets or EMDs, call providers, run AI, send messages, schedule jobs, or mutate linked workspace statuses.",
            **self.safety_flags(),
        }

    async def list_definitions(
        self,
        *,
        entity_type: str | None = None,
        status: str | None = None,
        include_defaults: bool = False,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if entity_type:
            filters["entity_type"] = self._norm(entity_type)
        if status:
            filters["status"] = self._norm(status)
        definitions = await self.db.collection(OPERATIONAL_WORKFLOW_DEFINITIONS_COLLECTION).find_many(filters or None)
        if include_defaults:
            stored_keys = {(item.get("workflow_code"), item.get("version")) for item in definitions}
            definitions.extend(
                {
                    **definition,
                    "id": f"default:{definition['workflow_code']}:{definition['version']}",
                    "default_definition": True,
                    **self.safety_flags(),
                }
                for definition in DEFAULT_WORKFLOW_DEFINITIONS
                if (definition["workflow_code"], definition["version"]) not in stored_keys
                and (not entity_type or definition["entity_type"] == self._norm(entity_type))
                and (not status or definition["status"] == self._norm(status))
            )
        definitions.sort(key=lambda item: (str(item.get("entity_type") or ""), str(item.get("workflow_code") or ""), str(item.get("version") or "")))
        return [self._definition_projection(item) for item in definitions]

    async def get_definition(self, definition_id: str) -> dict[str, Any]:
        return self._definition_projection(await self._require_definition(definition_id))

    async def create_definition(self, payload: OperationalWorkflowDefinitionCreate, user: dict) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        data["workflow_code"] = self._norm(data["workflow_code"])
        data["entity_type"] = self._norm(data["entity_type"])
        data["status"] = self._norm(data.get("status") or "draft")
        data["created_by"] = user.get("id")
        data["updated_by"] = user.get("id")
        self._validate_definition(data)
        definition = OperationalWorkflowDefinition(**data)
        record = definition.model_dump(mode="json")
        record.update(self.safety_flags())
        created = await self.db.collection(OPERATIONAL_WORKFLOW_DEFINITIONS_COLLECTION).insert_one(record)
        return {"phase": PHASE_LABEL, "workflow_definition": self._definition_projection(created), "metadata_only": True, **self.safety_flags()}

    async def update_definition(self, definition_id: str, payload: OperationalWorkflowDefinitionUpdate, user: dict) -> dict[str, Any]:
        existing = await self._require_definition(definition_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        if "workflow_code" in updates:
            updates["workflow_code"] = self._norm(updates["workflow_code"])
        if "entity_type" in updates:
            updates["entity_type"] = self._norm(updates["entity_type"])
        if "status" in updates:
            updates["status"] = self._norm(updates["status"])
        merged = {**existing, **updates}
        self._validate_definition(merged)
        updates["updated_by"] = user.get("id")
        updates.update(self.safety_flags())
        updated = await self.db.collection(OPERATIONAL_WORKFLOW_DEFINITIONS_COLLECTION).update_one({"id": existing["id"]}, updates)
        if not updated:
            raise OperationalWorkflowOrchestrationError("Workflow definition metadata could not be updated.")
        return {"phase": PHASE_LABEL, "workflow_definition": self._definition_projection(updated), "metadata_only": True, **self.safety_flags()}

    async def create_definition_version(
        self,
        definition_id: str,
        payload: OperationalWorkflowDefinitionUpdate,
        user: dict,
    ) -> dict[str, Any]:
        existing = await self._require_definition(definition_id)
        overrides = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        excluded_keys = {"id", "_id", "created_at", "updated_at", "created_by", "updated_by", "state_count", "transition_count"}
        excluded_keys.update(self.safety_flags().keys())
        next_data = {
            key: value
            for key, value in existing.items()
            if key not in excluded_keys
        }
        next_data.update(overrides)
        next_data["version"] = overrides.get("version") or self._next_version(str(existing.get("version") or "1.0"))
        next_data["status"] = self._norm(next_data.get("status") or "draft")
        next_data["created_by"] = user.get("id")
        next_data["updated_by"] = user.get("id")
        self._validate_definition(next_data)
        versioned = OperationalWorkflowDefinition(**next_data)
        record = versioned.model_dump(mode="json")
        record.update(self.safety_flags())
        created = await self.db.collection(OPERATIONAL_WORKFLOW_DEFINITIONS_COLLECTION).insert_one(record)
        await self._record_event(
            agency_id=next_data.get("metadata", {}).get("agency_id") or "platform",
            workflow_instance_id="definition-versioning",
            event_type="definition_version_created",
            event_code=f"{next_data['workflow_code']}:{next_data['version']}",
            event_status="recorded",
            source_module="operational_workflow_orchestration",
            source_entity_type="workflow_definition",
            source_entity_id=created["id"],
            payload={"previous_definition_id": existing["id"], "new_definition_id": created["id"]},
        )
        return {"phase": PHASE_LABEL, "workflow_definition": self._definition_projection(created), "version_created": True, "metadata_only": True, **self.safety_flags()}

    async def list_guards(
        self,
        *,
        workflow_definition_id: str | None = None,
        transition_code: str | None = None,
        guard_type: str | None = None,
        is_active: bool | None = None,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if workflow_definition_id:
            filters["workflow_definition_id"] = workflow_definition_id
        if transition_code:
            filters["transition_code"] = self._norm(transition_code)
        if guard_type:
            filters["guard_type"] = self._norm(guard_type)
        if is_active is not None:
            filters["is_active"] = is_active
        guards = await self.db.collection(OPERATIONAL_WORKFLOW_GUARDS_COLLECTION).find_many(filters or None)
        guards.sort(key=lambda item: (str(item.get("transition_code") or ""), str(item.get("guard_code") or "")))
        return [self._guard_projection(item) for item in guards]

    async def get_guard(self, guard_id: str) -> dict[str, Any]:
        return self._guard_projection(await self._require_guard(guard_id))

    async def create_guard(self, payload: OperationalWorkflowGuardCreate, user: dict) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        data["guard_code"] = self._norm(data["guard_code"])
        data["transition_code"] = self._norm(data["transition_code"])
        data["guard_type"] = self._norm(data["guard_type"])
        data["severity"] = self._norm(data.get("severity") or "warning")
        data["evaluation_mode"] = self._norm(data.get("evaluation_mode") or "metadata")
        data["created_by"] = user.get("id")
        data["updated_by"] = user.get("id")
        self._validate_guard(data)
        guard = OperationalWorkflowGuard(**data)
        record = guard.model_dump(mode="json")
        record.update(self.safety_flags())
        created = await self.db.collection(OPERATIONAL_WORKFLOW_GUARDS_COLLECTION).insert_one(record)
        return {"phase": PHASE_LABEL, "workflow_guard": self._guard_projection(created), "metadata_only": True, **self.safety_flags()}

    async def update_guard(self, guard_id: str, payload: OperationalWorkflowGuardUpdate, user: dict) -> dict[str, Any]:
        existing = await self._require_guard(guard_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        for key in ["guard_code", "transition_code", "guard_type", "severity", "evaluation_mode"]:
            if key in updates:
                updates[key] = self._norm(updates[key])
        merged = {**existing, **updates}
        self._validate_guard(merged)
        updates["updated_by"] = user.get("id")
        updates.update(self.safety_flags())
        updated = await self.db.collection(OPERATIONAL_WORKFLOW_GUARDS_COLLECTION).update_one({"id": existing["id"]}, updates)
        if not updated:
            raise OperationalWorkflowOrchestrationError("Workflow guard metadata could not be updated.")
        return {"phase": PHASE_LABEL, "workflow_guard": self._guard_projection(updated), "metadata_only": True, **self.safety_flags()}

    async def list_instances(
        self,
        *,
        agency_id: str | None = None,
        workflow_definition_id: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        workflow_status: str | None = None,
        current_state: str | None = None,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if workflow_definition_id:
            filters["workflow_definition_id"] = workflow_definition_id
        if entity_type:
            filters["entity_type"] = self._norm(entity_type)
        if entity_id:
            filters["entity_id"] = entity_id
        if workflow_status:
            filters["workflow_status"] = self._norm(workflow_status)
        if current_state:
            filters["current_state"] = self._norm(current_state)
        instances = await self.db.collection(OPERATIONAL_WORKFLOW_INSTANCES_COLLECTION).find_many(filters or None)
        instances.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._instance_projection(item) for item in instances]

    async def get_instance(self, instance_id: str, agency_id: str | None = None) -> dict[str, Any]:
        return await self._instance_projection(await self._require_instance(instance_id, agency_id=agency_id))

    async def start_instance(
        self,
        payload: OperationalWorkflowInstanceStartRequest,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        if agency_id:
            data["agency_id"] = agency_id
        if not data.get("agency_id"):
            raise OperationalWorkflowOrchestrationError("Agency id is required to start workflow orchestration metadata.")
        definition = await self._require_definition(data["workflow_definition_id"])
        data["entity_type"] = self._norm(data["entity_type"])
        if data["entity_type"] != definition.get("entity_type"):
            raise OperationalWorkflowOrchestrationError("Workflow definition entity type does not match the requested entity type.")
        data.setdefault("current_state", definition.get("initial_state"))
        data.setdefault("started_at", self._now())
        data.setdefault("workflow_status", "active")
        data["workflow_status"] = self._norm(data["workflow_status"])
        data["created_by"] = user.get("id")
        data["updated_by"] = user.get("id")
        instance = OperationalWorkflowInstance(**data)
        record = instance.model_dump(mode="json")
        record.update(self.safety_flags())
        created = await self.db.collection(OPERATIONAL_WORKFLOW_INSTANCES_COLLECTION).insert_one(record)
        await self._record_event(
            agency_id=created["agency_id"],
            workflow_instance_id=created["id"],
            event_type="workflow_started",
            event_code="workflow_started",
            event_status="recorded",
            source_module="operational_workflow_orchestration",
            source_entity_type=created["entity_type"],
            source_entity_id=created["entity_id"],
            payload={"current_state": created["current_state"], "definition_id": created["workflow_definition_id"]},
        )
        return {"phase": PHASE_LABEL, "workflow_instance": await self._instance_projection(created), "metadata_only": True, **self.safety_flags()}

    async def available_transitions(self, instance_id: str, agency_id: str | None = None) -> dict[str, Any]:
        instance = await self._require_instance(instance_id, agency_id=agency_id)
        definition = await self._require_definition(instance["workflow_definition_id"])
        transitions = []
        for transition in self._definition_transitions(definition):
            if transition.get("from_state") != instance.get("current_state"):
                continue
            guard_results = await self.evaluate_transition_guards(instance, definition, transition)
            transitions.append(
                {
                    **transition,
                    "availability_status": self._availability_status(guard_results),
                    "guard_results": guard_results,
                    "remediation_guidance": self._remediation_from_results(guard_results),
                    "metadata_only": True,
                }
            )
        return {
            "phase": PHASE_LABEL,
            "workflow_instance_id": instance_id,
            "current_state": instance.get("current_state"),
            "available_transitions": transitions,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def execute_transition(
        self,
        instance_id: str,
        payload: OperationalWorkflowTransitionRequest,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        instance = await self._require_instance(instance_id, agency_id=agency_id)
        definition = await self._require_definition(instance["workflow_definition_id"])
        transition = self._require_transition_definition(definition, payload.transition_code, instance.get("current_state"))
        guard_results = await self.evaluate_transition_guards(instance, definition, transition, payload.input_snapshot_json)
        blocked = [item for item in guard_results if item["status"] == "blocked"]
        warnings = [item for item in guard_results if item["status"] in {"warning", "manual_review", "unknown"}]
        now = self._now()
        transition_status = "completed"
        should_update_state = True

        if blocked:
            transition_status = "blocked"
            should_update_state = False
        elif warnings and not self._warnings_acknowledged(warnings, payload):
            transition_status = "manual_review_required" if any(item["status"] in {"manual_review", "unknown"} for item in warnings) else "warning_acknowledgement_required"
            should_update_state = False
        elif warnings:
            transition_status = "completed_with_warnings"

        transition_record = OperationalWorkflowTransition(
            agency_id=instance["agency_id"],
            workflow_instance_id=instance["id"],
            transition_code=self._norm(payload.transition_code),
            from_state=instance["current_state"],
            to_state=transition["to_state"],
            transition_status=transition_status,
            requested_by=user.get("id"),
            approved_by=payload.approved_by,
            reason=payload.reason,
            input_snapshot_json=payload.input_snapshot_json,
            result_snapshot_json={
                "guard_results": guard_results,
                "entity_status_sync_disabled": True,
                "explicit_adapter": self.adapter_for(instance.get("entity_type")),
                "metadata_only": True,
            },
            blocker_snapshot_json=blocked,
            warning_snapshot_json=warnings,
            executed_at=now,
            metadata=payload.metadata,
        )
        stored_transition = await self.db.collection(OPERATIONAL_WORKFLOW_TRANSITIONS_COLLECTION).insert_one(transition_record.model_dump(mode="json"))

        updates: dict[str, Any] = {
            "active_blockers_json": blocked,
            "active_warnings_json": warnings,
            "updated_by": user.get("id"),
            **self.safety_flags(),
        }
        if should_update_state:
            updates["previous_state"] = instance["current_state"]
            updates["current_state"] = transition["to_state"]
            if transition["to_state"] in (definition.get("terminal_states") or []):
                updates["workflow_status"] = "completed"
                updates["completed_at"] = now
        updated_instance = await self.db.collection(OPERATIONAL_WORKFLOW_INSTANCES_COLLECTION).update_one({"id": instance["id"]}, updates)
        await self._record_event(
            agency_id=instance["agency_id"],
            workflow_instance_id=instance["id"],
            event_type="workflow_transition",
            event_code=self._norm(payload.transition_code),
            event_status=transition_status,
            source_module="operational_workflow_orchestration",
            source_entity_type=instance["entity_type"],
            source_entity_id=instance["entity_id"],
            payload={
                "from_state": instance["current_state"],
                "to_state": transition["to_state"],
                "transition_id": stored_transition["id"],
                "guard_results": guard_results,
                "state_updated": should_update_state,
                "metadata_only": True,
            },
        )
        return {
            "phase": PHASE_LABEL,
            "transition": stored_transition,
            "workflow_instance": await self._instance_projection(updated_instance or instance),
            "guard_results": guard_results,
            "transition_status": transition_status,
            "state_updated": should_update_state,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def acknowledge_warnings(
        self,
        instance_id: str,
        payload: OperationalWorkflowWarningAcknowledgementRequest,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        instance = await self._require_instance(instance_id, agency_id=agency_id)
        warning_codes = set(payload.warning_codes or [])
        active_warnings = instance.get("active_warnings_json") or []
        acknowledged = [
            warning
            for warning in active_warnings
            if not warning_codes or warning.get("guard_code") in warning_codes or warning.get("guard_type") in warning_codes
        ]
        remaining = [
            warning
            for warning in active_warnings
            if warning not in acknowledged
        ]
        acknowledgement = {
            "acknowledged_warning_codes": [item.get("guard_code") or item.get("guard_type") for item in acknowledged],
            "acknowledged_by": payload.acknowledged_by or user.get("id"),
            "acknowledged_at": self._now().isoformat(),
            "acknowledgement_notes": payload.acknowledgement_notes,
            "metadata": payload.metadata,
            "metadata_only": True,
        }
        acknowledgements = list(instance.get("warning_acknowledgements_json") or [])
        acknowledgements.append(acknowledgement)
        updated = await self.db.collection(OPERATIONAL_WORKFLOW_INSTANCES_COLLECTION).update_one(
            {"id": instance["id"]},
            {
                "active_warnings_json": remaining,
                "warning_acknowledgements_json": acknowledgements,
                "updated_by": user.get("id"),
                **self.safety_flags(),
            },
        )
        await self._record_event(
            agency_id=instance["agency_id"],
            workflow_instance_id=instance["id"],
            event_type="workflow_warning_acknowledged",
            event_code="warning_acknowledged",
            event_status="recorded",
            source_module="operational_workflow_orchestration",
            source_entity_type=instance["entity_type"],
            source_entity_id=instance["entity_id"],
            payload=acknowledgement,
        )
        return {
            "phase": PHASE_LABEL,
            "workflow_instance": await self._instance_projection(updated or instance),
            "acknowledgement": acknowledgement,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def list_transitions(self, instance_id: str, agency_id: str | None = None) -> list[dict[str, Any]]:
        instance = await self._require_instance(instance_id, agency_id=agency_id)
        transitions = await self.db.collection(OPERATIONAL_WORKFLOW_TRANSITIONS_COLLECTION).find_many({"workflow_instance_id": instance["id"]})
        transitions.sort(key=lambda item: self._sort_text(item.get("created_at")), reverse=True)
        return [{**item, "immutable_history": True, "metadata_only": True, **self.safety_flags()} for item in transitions]

    async def list_events(self, instance_id: str, agency_id: str | None = None) -> list[dict[str, Any]]:
        instance = await self._require_instance(instance_id, agency_id=agency_id)
        events = await self.db.collection(OPERATIONAL_WORKFLOW_EVENTS_COLLECTION).find_many({"workflow_instance_id": instance["id"]})
        events.sort(key=lambda item: self._sort_text(item.get("occurred_at")), reverse=True)
        return [{**item, "immutable_history": True, "metadata_only": True, **self.safety_flags()} for item in events]

    async def entity_summary(self, agency_id: str | None, entity_type: str, entity_id: str) -> dict[str, Any]:
        instances = await self.list_instances(agency_id=agency_id, entity_type=entity_type, entity_id=entity_id)
        primary = instances[0] if instances else None
        available = await self.available_transitions(primary["id"], agency_id=agency_id) if primary else {"available_transitions": []}
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "entity_type": self._norm(entity_type),
            "entity_id": entity_id,
            "workflow_instance": primary,
            "available_transitions": available.get("available_transitions", []),
            "workflow_count": len(instances),
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def summary(self, agency_id: str | None = None) -> dict[str, Any]:
        definitions = await self.list_definitions(include_defaults=False)
        instances = await self.list_instances(agency_id=agency_id)
        guards = await self.list_guards()
        transitions = await self.db.collection(OPERATIONAL_WORKFLOW_TRANSITIONS_COLLECTION).find_many({"agency_id": agency_id} if agency_id else None)
        events = await self.db.collection(OPERATIONAL_WORKFLOW_EVENTS_COLLECTION).find_many({"agency_id": agency_id} if agency_id else None)
        return {
            "definition_count": len(definitions),
            "default_definition_count": len(DEFAULT_WORKFLOW_DEFINITIONS),
            "instance_count": len(instances),
            "guard_count": len(guards),
            "transition_count": len(transitions),
            "event_count": len(events),
            "by_entity_type": self._counts(instances, "entity_type"),
            "by_current_state": self._counts(instances, "current_state"),
            "by_workflow_status": self._counts(instances, "workflow_status"),
            "by_transition_status": self._counts(transitions, "transition_status"),
            "active_blocker_count": sum(len(item.get("active_blockers_json") or []) for item in instances),
            "active_warning_count": sum(len(item.get("active_warnings_json") or []) for item in instances),
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def diagnostics(self) -> dict[str, Any]:
        return {
            "phase": PHASE_LABEL,
            "adapters": EXPLICIT_ENTITY_ADAPTERS,
            "guard_results": GUARD_RESULTS,
            "guard_types": GUARD_TYPES,
            "transition_statuses": TRANSITION_STATUSES,
            "workflow_statuses": WORKFLOW_STATUSES,
            "entity_status_state_maps": ENTITY_STATUS_STATE_MAPS,
            "default_workflow_definitions": DEFAULT_WORKFLOW_DEFINITIONS,
            "metadata_only": True,
            **self.safety_flags(),
        }

    def state_transition_maps(self) -> dict[str, Any]:
        return {
            definition["workflow_code"]: {
                "entity_type": definition["entity_type"],
                "initial_state": definition["initial_state"],
                "terminal_states": definition["terminal_states"],
                "states": list((definition["state_definitions_json"] or {}).keys()),
                "transitions": definition["transition_definitions_json"],
                "metadata_only": True,
            }
            for definition in DEFAULT_WORKFLOW_DEFINITIONS
        }

    def adapter_for(self, entity_type: str | None) -> dict[str, Any]:
        adapter = EXPLICIT_ENTITY_ADAPTERS.get(self._norm(entity_type or ""))
        return dict(adapter or {"status_sync_enabled": False, "known_adapter": False})

    def map_entity_status(self, entity_type: str, status: str | None) -> dict[str, Any]:
        entity_key = self._norm(entity_type)
        status_key = self._norm(status or "")
        state = ENTITY_STATUS_STATE_MAPS.get(entity_key, {}).get(status_key)
        return {
            "entity_type": entity_key,
            "source_status": status,
            "mapped_workflow_state": state or "unknown",
            "mapping_status": "mapped" if state else "unknown",
            "does_not_overwrite_entity_status": True,
            "metadata_only": True,
        }

    async def evaluate_transition_guards(
        self,
        instance: dict[str, Any],
        definition: dict[str, Any],
        transition: dict[str, Any],
        input_snapshot: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        context = {
            **(instance.get("context_snapshot_json") or {}),
            **(input_snapshot or {}),
        }
        guard_codes = set(transition.get("guard_codes") or [])
        guards = await self.list_guards(workflow_definition_id=definition["id"], transition_code=transition["transition_code"], is_active=True)
        if guard_codes:
            guards = [guard for guard in guards if guard.get("guard_code") in guard_codes]
        return [self._evaluate_guard(guard, context) for guard in guards]

    def _evaluate_guard(self, guard: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        guard_type = self._norm(guard.get("guard_type") or "generic_metadata_check")
        condition = guard.get("condition_json") or {}
        if condition.get("force_status"):
            status = self._guard_status(condition["force_status"])
        elif self._is_unknown(condition, guard, context):
            status = "unknown"
        else:
            status = self._evaluate_guard_type(guard_type, condition, context)
        return {
            "guard_id": guard.get("id"),
            "guard_code": guard.get("guard_code"),
            "guard_type": guard_type,
            "severity": guard.get("severity"),
            "status": status,
            "failure_message_internal": None if status == "passed" else guard.get("failure_message_internal"),
            "failure_message_client": None if status == "passed" else guard.get("failure_message_client"),
            "remediation_guidance": None if status == "passed" else guard.get("remediation_guidance"),
            "evaluation_mode": guard.get("evaluation_mode"),
            "unknown_data_safe": status != "error",
            "metadata_only": True,
        }

    def _evaluate_guard_type(self, guard_type: str, condition: dict[str, Any], context: dict[str, Any]) -> str:
        if guard_type == "required_client_passenger_linkage":
            has_client = any(context.get(key) for key in ["client_id", "primary_client_id", "client_master_record_id"])
            has_passenger = any(context.get(key) for key in ["passenger_id", "primary_passenger_id", "passenger_workspace_id"])
            return "passed" if has_client and has_passenger else self._missing_status(condition, default="manual_review")
        if guard_type == "segment_precision":
            value = context.get("segment_precision_status") or context.get("segment_precision")
            if value in {True, "complete", "precise", "passed"}:
                return "passed"
            return "blocked" if value in {False, "blocked", "failed"} else self._missing_status(condition, default="warning")
        if guard_type == "accepted_offer":
            if context.get("accepted_offer_id") or context.get("offer_accepted") is True or context.get("offer_status") == "accepted":
                return "passed"
            return "blocked"
        if guard_type == "policy_evaluation":
            value = context.get("policy_evaluation_status") or context.get("policy_status")
            if value in {"passed", "reviewed", "supported", "allowed"}:
                return "passed"
            if value in {"blocked", "not_supported", "failed"}:
                return "blocked"
            return self._missing_status(condition, default="unknown")
        if guard_type == "blocked_feasibility":
            value = context.get("feasibility_status") or context.get("feasibility_outcome")
            if value in {"blocked", "not_feasible", "not_supported"}:
                return "blocked"
            return "passed" if value else self._missing_status(condition, default="unknown")
        if guard_type == "required_approval":
            if context.get("approval_required") is False:
                return "passed"
            return "passed" if context.get("approval_status") in {"approved", "received", "not_required", "waived"} else "blocked"
        if guard_type == "required_documents":
            if context.get("documents_unknown") is True:
                return "unknown"
            missing = context.get("missing_documents") or []
            missing_count = context.get("required_documents_missing_count") or len(missing)
            return "blocked" if missing_count else "passed"
        if guard_type == "pricing_resolution":
            value = context.get("pricing_status") or context.get("pricing_resolution_status")
            if value in {"resolved", "passed", "not_required", "waived"} or context.get("pricing_resolved") is True:
                return "passed"
            return "blocked" if value in {"blocked", "failed"} else self._missing_status(condition, default="warning")
        if guard_type == "booking_readiness":
            value = context.get("booking_readiness_status") or context.get("booking_status")
            if value in {"ready", "booked", "ready_to_book"} or context.get("booking_ready") is True:
                return "passed"
            return "blocked" if value in {"blocked", "failed"} else self._missing_status(condition, default="warning")
        if guard_type == "payment_invoice_prerequisites":
            value = context.get("payment_status") or context.get("invoice_status")
            if value in {"completed", "paid", "waived", "not_required"}:
                return "passed"
            return "blocked" if value in {"failed", "overdue", "blocked"} else self._missing_status(condition, default="warning")
        if guard_type == "ticket_emd_readiness":
            value = context.get("ticket_emd_readiness_status") or context.get("ticket_status") or context.get("emd_status")
            if value in {"ready", "issued", "not_required", "completed"}:
                return "passed"
            return "blocked" if value in {"blocked", "failed"} else self._missing_status(condition, default="warning")
        if guard_type == "unresolved_critical_pilot_readiness_issue":
            count = int(context.get("critical_pilot_readiness_issue_count") or 0)
            return "blocked" if count > 0 else "passed"
        if guard_type == "unresolved_operational_blockers":
            blockers = context.get("operational_blockers") or context.get("active_blockers") or []
            count = int(context.get("active_operational_blocker_count") or len(blockers))
            return "blocked" if count > 0 else "passed"
        context_key = condition.get("context_key")
        if context_key:
            expected = condition.get("expected_value")
            if expected is not None:
                return "passed" if context.get(context_key) == expected else self._missing_status(condition, default="manual_review")
            return "passed" if context.get(context_key) not in {None, "", []} else self._missing_status(condition, default="manual_review")
        return "unknown"

    def _is_unknown(self, condition: dict[str, Any], guard: dict[str, Any], context: dict[str, Any]) -> bool:
        unknown_fields = set(context.get("unknown_fields") or [])
        return bool(
            condition.get("unknown") is True
            or guard.get("guard_code") in unknown_fields
            or guard.get("guard_type") in unknown_fields
        )

    def _missing_status(self, condition: dict[str, Any], default: str) -> str:
        return self._guard_status(condition.get("missing_status") or default)

    def _guard_status(self, value: Any) -> str:
        text = self._norm(str(value or "unknown"))
        return text if text in GUARD_RESULTS else "unknown"

    def _availability_status(self, guard_results: list[dict[str, Any]]) -> str:
        if any(item["status"] == "blocked" for item in guard_results):
            return "blocked"
        if any(item["status"] in {"manual_review", "unknown"} for item in guard_results):
            return "manual_review_required"
        if any(item["status"] == "warning" for item in guard_results):
            return "warning_acknowledgement_required"
        return "available"

    def _warnings_acknowledged(self, warnings: list[dict[str, Any]], payload: OperationalWorkflowTransitionRequest) -> bool:
        if payload.acknowledge_warnings:
            return True
        acknowledged = set(payload.acknowledged_warning_codes or [])
        required = {item.get("guard_code") or item.get("guard_type") for item in warnings}
        return required.issubset(acknowledged)

    def _remediation_from_results(self, guard_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "guard_code": item.get("guard_code"),
                "status": item.get("status"),
                "severity": item.get("severity"),
                "message": item.get("failure_message_internal"),
                "guidance": item.get("remediation_guidance"),
            }
            for item in guard_results
            if item.get("status") != "passed"
        ]

    def _require_transition_definition(self, definition: dict[str, Any], transition_code: str, current_state: str | None) -> dict[str, Any]:
        code = self._norm(transition_code)
        for transition in self._definition_transitions(definition):
            if transition.get("transition_code") == code and transition.get("from_state") == current_state:
                return transition
        raise OperationalWorkflowOrchestrationError("Transition is not available from the current workflow state.")

    def _definition_transitions(self, definition: dict[str, Any]) -> list[dict[str, Any]]:
        transitions = definition.get("transition_definitions_json") or []
        return [
            {
                **transition,
                "transition_code": self._norm(transition.get("transition_code") or ""),
                "from_state": self._norm(transition.get("from_state") or ""),
                "to_state": self._norm(transition.get("to_state") or ""),
                "guard_codes": [self._norm(item) for item in (transition.get("guard_codes") or [])],
            }
            for transition in transitions
        ]

    async def _require_definition(self, definition_id: str) -> dict[str, Any]:
        item = await self.db.collection(OPERATIONAL_WORKFLOW_DEFINITIONS_COLLECTION).find_one({"id": definition_id})
        if not item:
            item = await self.db.collection(OPERATIONAL_WORKFLOW_DEFINITIONS_COLLECTION).find_one({"workflow_code": self._norm(definition_id)})
        if not item:
            raise OperationalWorkflowOrchestrationError("Operational workflow definition metadata was not found.")
        return item

    async def _require_instance(self, instance_id: str, *, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": instance_id}
        if agency_id:
            filters["agency_id"] = agency_id
        item = await self.db.collection(OPERATIONAL_WORKFLOW_INSTANCES_COLLECTION).find_one(filters)
        if not item:
            raise OperationalWorkflowOrchestrationError("Operational workflow instance metadata was not found.")
        return item

    async def _require_guard(self, guard_id: str) -> dict[str, Any]:
        item = await self.db.collection(OPERATIONAL_WORKFLOW_GUARDS_COLLECTION).find_one({"id": guard_id})
        if not item:
            item = await self.db.collection(OPERATIONAL_WORKFLOW_GUARDS_COLLECTION).find_one({"guard_code": self._norm(guard_id)})
        if not item:
            raise OperationalWorkflowOrchestrationError("Operational workflow guard metadata was not found.")
        return item

    async def _instance_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        definition = None
        try:
            definition = await self._require_definition(item["workflow_definition_id"])
        except OperationalWorkflowOrchestrationError:
            definition = None
        projected = {
            **item,
            "definition": self._definition_projection(definition) if definition else None,
            "adapter": self.adapter_for(item.get("entity_type")),
            "display_name": f"{item.get('entity_type')} {item.get('entity_id')} - {item.get('current_state')}",
            "read_only": False,
            **self.safety_flags(),
        }
        return projected

    def _agency_instance_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        return {**item, "read_only": False, **self.safety_flags()}

    def _definition_projection(self, item: dict[str, Any] | None) -> dict[str, Any]:
        if not item:
            return {}
        return {
            **item,
            "state_count": len((item.get("state_definitions_json") or {}).keys()),
            "transition_count": len(item.get("transition_definitions_json") or []),
            "metadata_only": True,
            **self.safety_flags(),
        }

    def _guard_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        return {**item, "metadata_only": True, **self.safety_flags()}

    async def _record_event(
        self,
        *,
        agency_id: str,
        workflow_instance_id: str,
        event_type: str,
        event_code: str,
        event_status: str,
        source_module: str,
        source_entity_type: str,
        source_entity_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        event = OperationalWorkflowEvent(
            agency_id=agency_id,
            workflow_instance_id=workflow_instance_id,
            event_type=event_type,
            event_code=event_code,
            event_status=event_status,
            source_module=source_module,
            source_entity_type=source_entity_type,
            source_entity_id=source_entity_id,
            payload_json={**payload, "metadata_only": True},
            occurred_at=self._now(),
        )
        return await self.db.collection(OPERATIONAL_WORKFLOW_EVENTS_COLLECTION).insert_one(event.model_dump(mode="json"))

    def _validate_definition(self, data: dict[str, Any]) -> None:
        if not data.get("workflow_code") or not data.get("entity_type") or not data.get("initial_state"):
            raise OperationalWorkflowOrchestrationError("Workflow code, entity type, and initial state are required.")
        states = set((data.get("state_definitions_json") or {}).keys())
        if data["initial_state"] not in states:
            raise OperationalWorkflowOrchestrationError("Initial state must exist in state definitions.")
        for terminal in data.get("terminal_states") or []:
            if terminal not in states:
                raise OperationalWorkflowOrchestrationError("Terminal states must exist in state definitions.")
        for transition in data.get("transition_definitions_json") or []:
            if not transition.get("transition_code") or transition.get("from_state") not in states or transition.get("to_state") not in states:
                raise OperationalWorkflowOrchestrationError("Each transition must have a code and valid from/to states.")

    def _validate_guard(self, data: dict[str, Any]) -> None:
        if data.get("guard_type") not in GUARD_TYPES:
            raise OperationalWorkflowOrchestrationError("Guard type is not supported by the orchestration foundation.")
        if data.get("severity") not in {"info", "warning", "medium", "high", "critical", "blocker"}:
            raise OperationalWorkflowOrchestrationError("Guard severity is not supported.")
        if not data.get("failure_message_internal"):
            raise OperationalWorkflowOrchestrationError("Internal failure message is required for guard metadata.")

    def _next_version(self, current: str) -> str:
        parts = current.split(".")
        try:
            parts[-1] = str(int(parts[-1]) + 1)
            return ".".join(parts)
        except ValueError:
            return f"{current}.1"

    def _counts(self, items: list[dict[str, Any]], key: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in items:
            value = item.get(key) or "unset"
            counts[str(value)] = counts.get(str(value), 0) + 1
        return counts

    def _sort_text(self, value: Any) -> str:
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value or "")

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _norm(self, value: Any) -> str:
        return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "operational_workflow_orchestration_foundation": True,
            "shared_workflow_state_layer_enabled": True,
            "guarded_transition_metadata_enabled": True,
            "immutable_transition_history_enabled": True,
            "workflow_events_metadata_enabled": True,
            "explicit_entity_adapters_enabled": True,
            "entity_status_sync_disabled_by_default": True,
            "unrestricted_dynamic_mutation_disabled": True,
            "existing_workspace_services_preserved": True,
            "booking_execution_disabled": True,
            "ticket_issuance_disabled": True,
            "emd_issuance_disabled": True,
            "provider_integrations_disabled": True,
            "external_api_calls_disabled": True,
            "ai_disabled": True,
            "background_workers_disabled": True,
            "schedulers_disabled": True,
            "automatic_execution_disabled": True,
            "automation_disabled": True,
            "destructive_reset_disabled": True,
            "human_authority_final": True,
        }
