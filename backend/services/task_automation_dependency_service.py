from __future__ import annotations

from datetime import datetime, timedelta, timezone
from time import monotonic
from typing import Any

from database import Database
from models import (
    AuditEvent,
    OperationalApprovalDecisionRequest,
    OperationalApprovalRequestCreate,
    OperationalAutomationDryRunRequest,
    OperationalAutomationProcessRequest,
    OperationalReminderProcessRequest,
    OperationalAutomationRuleLifecycleRequest,
    OperationalTaskAutomationRule,
    OperationalTaskAutomationRuleCreate,
    OperationalTaskAutomationRuleUpdate,
    OperationalTaskAutomationRun,
    OperationalTaskAutomationRunRequest,
    OperationalTaskDependency,
    OperationalTaskDependencyActionRequest,
    OperationalTaskDependencyCreate,
    OperationalTaskDependencyUpdate,
    OperationalTaskTemplate,
    OperationalTaskTemplateCreate,
    OperationalTaskTemplateUpdate,
    new_id,
)
from build_phase import CURRENT_BUILD_PHASE
from services.agent_work_queue_service import (
    WORK_ITEM_STATUSES,
    WORK_ITEM_TYPES,
    AgentWorkQueueError,
    AgentWorkQueueService,
)
from services.governed_automation_contract import (
    ACTION_SAFETY_CLASS,
    CANONICAL_AUTOMATION_EVENTS,
    MAX_CHAINED_ACTIONS,
    MAX_RECURSION_DEPTH,
    TASK_TYPE_CATALOGUE,
    GovernedAutomationContractError,
    action_safety_class,
    bounded_safe_snapshot,
    canonical_event_type,
    evaluate_conditions,
    normalized_actions,
    task_type_contract,
    validate_rule_contract,
)
from services.operational_collaboration_service import OperationalCollaborationService
from services.operational_sla_deadline_service import OperationalSlaDeadlineService
from services.authorization_service import agency_permissions

PHASE_LABEL = CURRENT_BUILD_PHASE

OPERATIONAL_TASK_TEMPLATES_COLLECTION = "operational_task_templates"
OPERATIONAL_TASK_DEPENDENCIES_COLLECTION = "operational_task_dependencies"
OPERATIONAL_TASK_AUTOMATION_RULES_COLLECTION = "operational_task_automation_rules"
OPERATIONAL_TASK_AUTOMATION_RUNS_COLLECTION = "operational_task_automation_runs"

TASK_TEMPLATE_STATUSES = [
    "draft",
    "active",
    "inactive",
    "paused",
    "superseded",
    "archived",
]
TASK_DEPENDENCY_TYPES = [
    "mandatory",
    "advisory",
    "finish_to_start",
    "start_to_start",
    "manual_review",
    "evidence_required",
]
TASK_DEPENDENCY_STATUSES = ["pending", "blocked", "satisfied", "waived"]
TASK_AUTOMATION_RULE_STATUSES = ["draft", "active", "inactive", "superseded", "archived"]
TASK_AUTOMATION_RUN_STATUSES = [
    "processing",
    "completed",
    "completed_with_warnings",
    "failed",
    "skipped",
    "manual_review",
]
TASK_AUTOMATION_TRIGGER_EVENTS = list(CANONICAL_AUTOMATION_EVENTS)
MAX_PROCESS_BATCH = 50
EXECUTION_LOCK_MINUTES = 5

SAFE_TASK_TEMPLATES: list[dict[str, Any]] = [
    {
        "template_code": "triage_request",
        "title_pattern": "Triage {source_label}",
        "description_pattern": "Review the new request and identify passenger service requirements.",
        "related_entity_types": ["request", "travel_request_workspace"],
        "trigger_event": "request.created",
        "default_priority": "urgent",
        "due_offset_hours": 4,
        "assigned_team_strategy": "triage",
        "completion_conditions": [{"field": "request_status", "expected": "triaged"}],
    },
    {
        "template_code": "obtain_missing_passenger_data",
        "title_pattern": "Obtain missing passenger data for {source_label}",
        "description_pattern": "Collect missing passenger identity, contact, assistance, or travel-profile metadata.",
        "related_entity_types": ["request", "passenger_workspace"],
        "trigger_event": "request.created",
        "default_priority": "high",
        "due_offset_hours": 12,
        "assigned_team_strategy": "operations",
        "dependency_template_codes": ["triage_request"],
    },
    {
        "template_code": "obtain_passport_document",
        "title_pattern": "Obtain passport or required document for {source_label}",
        "description_pattern": "Request passport, visa, medical, consent, or authority document metadata as required.",
        "related_entity_types": ["document_workspace", "request"],
        "trigger_event": "request.created",
        "default_priority": "high",
        "due_offset_days": 1,
        "assigned_team_strategy": "documents",
        "dependency_template_codes": ["triage_request"],
    },
    {
        "template_code": "request_medif",
        "title_pattern": "Request MEDIF for {source_label}",
        "description_pattern": "Coordinate medical information form metadata with the passenger and airline.",
        "related_entity_types": ["ssr_osi_workspace", "document_workspace"],
        "trigger_event": "trip.service_added",
        "default_priority": "high",
        "due_offset_days": 2,
        "required_capability": "MEDIF",
        "dependency_template_codes": ["obtain_missing_passenger_data"],
    },
    {
        "template_code": "confirm_poc_model_battery",
        "title_pattern": "Confirm POC model and battery details for {source_label}",
        "description_pattern": "Record portable oxygen concentrator model, battery duration, and airline review metadata.",
        "related_entity_types": ["ssr_osi_workspace"],
        "trigger_event": "trip.service_added",
        "default_priority": "high",
        "due_offset_days": 2,
        "required_capability": "POC",
        "dependency_template_codes": ["obtain_missing_passenger_data"],
    },
    {
        "template_code": "request_wheelchair_dimensions_battery",
        "title_pattern": "Request wheelchair dimensions and battery information for {source_label}",
        "description_pattern": "Collect mobility aid dimensions, weight, battery type, and handling metadata.",
        "related_entity_types": ["ssr_osi_workspace"],
        "trigger_event": "trip.service_added",
        "default_priority": "high",
        "due_offset_days": 2,
        "required_capability": "mobility_assistance",
        "dependency_template_codes": ["obtain_missing_passenger_data"],
    },
    {
        "template_code": "request_petc_avih_documents",
        "title_pattern": "Request PETC/AVIH documents for {source_label}",
        "description_pattern": "Collect pet transport documents, container details, and veterinary metadata.",
        "related_entity_types": ["ssr_osi_workspace", "document_workspace"],
        "trigger_event": "trip.service_added",
        "default_priority": "high",
        "due_offset_days": 2,
        "required_capability": "PETC_AVIH",
        "dependency_template_codes": ["obtain_missing_passenger_data"],
    },
    {
        "template_code": "request_airline_approval",
        "title_pattern": "Request airline approval for {source_label}",
        "description_pattern": "Prepare airline approval metadata for special service handling.",
        "related_entity_types": ["ssr_osi_workspace"],
        "trigger_event": "trip.service_added",
        "default_priority": "high",
        "due_offset_days": 2,
        "assigned_team_strategy": "airline_liaison",
        "dependency_template_codes": ["request_medif", "request_petc_avih_documents", "confirm_poc_model_battery", "request_wheelchair_dimensions_battery"],
    },
    {
        "template_code": "prepare_offer",
        "title_pattern": "Prepare offer for {source_label}",
        "description_pattern": "Prepare human-reviewed offer metadata after requirements are understood.",
        "related_entity_types": ["offer_workspace", "request"],
        "trigger_event": "offer.created",
        "default_priority": "normal",
        "due_offset_days": 1,
        "dependency_template_codes": ["triage_request"],
    },
    {
        "template_code": "review_pricing_manual_quote",
        "title_pattern": "Review pricing or manual quote for {source_label}",
        "description_pattern": "Review pricing metadata and manual quote dependencies before client presentation.",
        "related_entity_types": ["offer_workspace", "pricing_formula_builder"],
        "trigger_event": "offer.created",
        "default_priority": "normal",
        "due_offset_days": 1,
        "dependency_template_codes": ["prepare_offer"],
    },
    {
        "template_code": "follow_up_client_acceptance",
        "title_pattern": "Follow up client acceptance for {source_label}",
        "description_pattern": "Follow up client acceptance metadata without sending automated messages.",
        "related_entity_types": ["offer_workspace"],
        "trigger_event": "offer.delivered",
        "default_priority": "normal",
        "due_offset_days": 2,
        "dependency_template_codes": ["prepare_offer"],
    },
    {
        "template_code": "create_booking_readiness_check",
        "title_pattern": "Create booking readiness check for {source_label}",
        "description_pattern": "Review booking readiness metadata after offer acceptance.",
        "related_entity_types": ["booking_workspace", "offer_workspace"],
        "trigger_event": "offer.accepted",
        "default_priority": "high",
        "due_offset_hours": 12,
        "dependency_template_codes": ["follow_up_client_acceptance"],
    },
    {
        "template_code": "ticket_emd_verification",
        "title_pattern": "Verify ticket and EMD metadata for {source_label}",
        "description_pattern": "Verify ticket, coupon, EMD, RFIC/RFISC, and document metadata after booking.",
        "related_entity_types": ["ticket_workspace", "emd_workspace", "booking_workspace"],
        "trigger_event": "ticket.recorded",
        "default_priority": "high",
        "due_offset_hours": 12,
        "dependency_template_codes": ["create_booking_readiness_check"],
    },
    {
        "template_code": "invoice_payment_follow_up",
        "title_pattern": "Follow up invoice or payment metadata for {source_label}",
        "description_pattern": "Review payment/invoice follow-up metadata without payment processing or automated messaging.",
        "related_entity_types": ["booking_workspace", "payment"],
        "trigger_event": "invoice.due_soon",
        "default_priority": "high",
        "due_offset_hours": 24,
        "dependency_template_codes": ["create_booking_readiness_check"],
    },
    {
        "template_code": "disruption_handling",
        "title_pattern": "Handle disruption for {source_label}",
        "description_pattern": "Create disruption handling task metadata for human operational review.",
        "related_entity_types": ["disruption", "trip_workspace"],
        "trigger_event": "booking.blocked",
        "default_priority": "urgent",
        "due_offset_hours": 1,
    },
    {
        "template_code": "refund_change_claim_follow_up",
        "title_pattern": "Follow up refund/change/claim for {source_label}",
        "description_pattern": "Track refund, change, or claim follow-up metadata without processing workflow execution.",
        "related_entity_types": ["service_case", "refund_exchange_case"],
        "trigger_event": "refund.requested",
        "default_priority": "normal",
        "due_offset_days": 3,
    },
    {
        "template_code": "final_trip_document_check",
        "title_pattern": "Final trip document check for {source_label}",
        "description_pattern": "Confirm final travel document metadata before travel readiness.",
        "related_entity_types": ["trip_workspace", "document_workspace"],
        "trigger_event": "trip.document_required",
        "default_priority": "high",
        "due_offset_hours": 24,
        "dependency_template_codes": ["ticket_emd_verification", "invoice_payment_follow_up"],
    },
]

SAFE_TASK_TEMPLATES.extend(
    [
        {
            "template_code": "qualify_new_request",
            "title_pattern": "Qualify {source_label}",
            "description_pattern": "Review the new request and confirm its operational requirements.",
            "related_entity_types": ["request"],
            "trigger_event": "request.created",
            "default_priority": "high",
            "due_offset_hours": 4,
        },
        {
            "template_code": "review_missing_passenger_information",
            "title_pattern": "Review missing passenger information for {source_label}",
            "description_pattern": "Resolve missing passenger information before downstream work.",
            "related_entity_types": ["request"],
            "trigger_event": "request.missing_information",
            "default_priority": "high",
            "due_offset_hours": 8,
        },
        {
            "template_code": "follow_up_delivered_offer",
            "title_pattern": "Follow up delivered Offer for {source_label}",
            "description_pattern": "Review the delivered Offer and record the next internal follow-up.",
            "related_entity_types": ["offer"],
            "trigger_event": "offer.delivered",
            "default_priority": "normal",
            "due_offset_days": 2,
        },
        {
            "template_code": "review_offer_expiry",
            "title_pattern": "Review expiring Offer for {source_label}",
            "description_pattern": "Review Offer expiry evidence and decide the next human action.",
            "related_entity_types": ["offer"],
            "trigger_event": "offer.ready",
            "default_priority": "high",
            "due_offset_hours": 24,
        },
        {
            "template_code": "prepare_booking_from_accepted_offer",
            "title_pattern": "Prepare Booking for {source_label}",
            "description_pattern": "Review the accepted Offer snapshot and prepare the Booking handoff.",
            "related_entity_types": ["offer", "booking"],
            "trigger_event": "offer.accepted",
            "default_priority": "high",
            "due_offset_hours": 12,
        },
        {
            "template_code": "review_confirmed_trip_service",
            "title_pattern": "Review passenger service for {source_label}",
            "description_pattern": "Review special-service evidence on the confirmed Trip.",
            "related_entity_types": ["trip"],
            "trigger_event": "trip.service_added",
            "default_priority": "high",
            "due_offset_hours": 12,
        },
        {
            "template_code": "review_booking_blocker",
            "title_pattern": "Review Booking blocker for {source_label}",
            "description_pattern": "Resolve the Booking blocker through a human operational review.",
            "related_entity_types": ["booking"],
            "trigger_event": "booking.blocked",
            "default_priority": "urgent",
            "due_offset_hours": 2,
        },
        {
            "template_code": "verify_ticketing_deadline",
            "title_pattern": "Verify ticketing deadline for {source_label}",
            "description_pattern": "Review recorded ticketing-deadline evidence.",
            "related_entity_types": ["ticket", "booking"],
            "trigger_event": "ticket.deadline_approaching",
            "default_priority": "urgent",
            "due_offset_hours": 1,
        },
        {
            "template_code": "review_uploaded_document",
            "title_pattern": "Review uploaded document for {source_label}",
            "description_pattern": "Review the uploaded document through the canonical Document workspace.",
            "related_entity_types": ["document"],
            "trigger_event": "document.uploaded",
            "default_priority": "normal",
            "due_offset_hours": 12,
        },
        {
            "template_code": "respond_to_client_reply",
            "title_pattern": "Respond to client for {source_label}",
            "description_pattern": "Review the client reply and prepare a human response.",
            "related_entity_types": ["communication"],
            "trigger_event": "client_reply_received",
            "default_priority": "normal",
            "due_offset_hours": 4,
        },
        {
            "template_code": "respond_to_passenger_reply",
            "title_pattern": "Respond to passenger for {source_label}",
            "description_pattern": "Review the passenger reply and prepare a human response.",
            "related_entity_types": ["communication"],
            "trigger_event": "passenger_reply_received",
            "default_priority": "normal",
            "due_offset_hours": 4,
        },
        {
            "template_code": "review_supplier_reply",
            "title_pattern": "Review supplier reply for {source_label}",
            "description_pattern": "Review the supplier reply without sending an automatic response.",
            "related_entity_types": ["communication"],
            "trigger_event": "supplier_reply_received",
            "default_priority": "high",
            "due_offset_hours": 4,
        },
        {
            "template_code": "review_invoice_due",
            "title_pattern": "Review Invoice due date for {source_label}",
            "description_pattern": "Review the approaching Invoice due date internally.",
            "related_entity_types": ["invoice"],
            "trigger_event": "invoice.due_soon",
            "default_priority": "high",
            "due_offset_hours": 4,
        },
        {
            "template_code": "review_unallocated_payment",
            "title_pattern": "Investigate unallocated Payment for {source_label}",
            "description_pattern": "Review allocation evidence without posting a Payment.",
            "related_entity_types": ["payment"],
            "trigger_event": "payment.unallocated",
            "default_priority": "high",
            "due_offset_hours": 8,
        },
        {
            "template_code": "review_missing_supplier_cost",
            "title_pattern": "Review missing Supplier Cost for {source_label}",
            "description_pattern": "Review missing Supplier Cost evidence with finance permissions.",
            "related_entity_types": ["supplier_cost"],
            "trigger_event": "supplier_cost.missing",
            "default_priority": "high",
            "due_offset_hours": 8,
        },
        {
            "template_code": "review_refund_request",
            "title_pattern": "Review Refund request for {source_label}",
            "description_pattern": "Review Refund evidence without executing a refund.",
            "related_entity_types": ["refund"],
            "trigger_event": "refund.requested",
            "default_priority": "high",
            "due_offset_hours": 8,
        },
        {
            "template_code": "review_exchange_request",
            "title_pattern": "Review Exchange request for {source_label}",
            "description_pattern": "Review Exchange evidence without confirming an exchange.",
            "related_entity_types": ["exchange"],
            "trigger_event": "exchange.requested",
            "default_priority": "high",
            "due_offset_hours": 8,
        },
    ]
)

DEFAULT_AUTOMATION_RULES: list[dict[str, Any]] = [
    {
        "rule_code": f"default_{template['template_code']}",
        "rule_key": f"default_{template['template_code']}",
        "name": template["title_pattern"].replace("{source_label}", "event"),
        "description": template.get("description_pattern"),
        "trigger_event": canonical_event_type(template["trigger_event"]),
        "trigger_event_types": [canonical_event_type(template["trigger_event"])],
        "trigger_entity_types": list(template.get("related_entity_types") or []),
        "conditions_json": {},
        "actions": [
            {
                "action_type": "create_work_item",
                "parameters": {"template_code": template["template_code"]},
                "safety_class": "A",
            }
        ],
        "generated_template_code": template["template_code"],
        "deduplication_key_pattern": "{agency_id}:{source_entity_type}:{source_entity_id}:{template_code}",
        "priority": 100,
        "execution_safety_class": "A",
        "dry_run_supported": True,
        "enabled": False,
        "status": "draft",
        "published_at": None,
        "reconciliation_status": "default_pack_not_activated",
    }
    for template in SAFE_TASK_TEMPLATES
]

for _template in SAFE_TASK_TEMPLATES:
    _template["trigger_event"] = canonical_event_type(_template["trigger_event"])
    _template["status"] = "draft"


class TaskAutomationDependencyError(ValueError):
    pass


class TaskAutomationDependencyService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def platform_dashboard(self, **filters: Any) -> dict[str, Any]:
        runs = await self.list_runs(**filters)
        dependencies = await self.list_dependencies(agency_id=filters.get("agency_id"))
        templates = await self.list_templates(agency_id=filters.get("agency_id"), include_defaults=True)
        rules = await self.list_rules(agency_id=filters.get("agency_id"), include_defaults=True)
        return {
            "phase": PHASE_LABEL,
            "templates": templates,
            "rules": rules,
            "runs": runs,
            "dependencies": dependencies,
            "summary": self.summarize(runs, dependencies),
            "safe_template_codes": [template["template_code"] for template in SAFE_TASK_TEMPLATES],
            "event_catalogue": list(CANONICAL_AUTOMATION_EVENTS),
            "action_catalogue": self.action_catalogue(),
            "task_type_catalogue": [
                task_type_contract(task_type) for task_type in sorted(TASK_TYPE_CATALOGUE)
            ],
            "metadata_only": True,
            "platform_governance_enabled": True,
            **self.safety_flags(),
        }

    async def agency_dashboard(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        scoped_filters = {key: value for key, value in filters.items() if key != "agency_id"}
        runs = await self.list_runs(agency_id=agency_id, **scoped_filters)
        dependencies = await self.list_dependencies(agency_id=agency_id, **scoped_filters)
        templates = await self.list_templates(agency_id=agency_id, include_defaults=True)
        rules = await self.list_rules(agency_id=agency_id, include_defaults=True)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "templates": templates,
            "rules": rules,
            "runs": runs,
            "dependencies": dependencies,
            "ready_tasks": await self.ready_tasks(agency_id),
            "blocked_tasks": await self.blocked_tasks(agency_id),
            "summary": self.summarize(runs, dependencies),
            "safe_template_codes": [template["template_code"] for template in SAFE_TASK_TEMPLATES],
            "event_catalogue": list(CANONICAL_AUTOMATION_EVENTS),
            "action_catalogue": self.action_catalogue(),
            "task_type_catalogue": [
                task_type_contract(task_type) for task_type in sorted(TASK_TYPE_CATALOGUE)
            ],
            "approvals": await self.list_approvals(agency_id),
            "operational_metrics": await self.operational_metrics(agency_id),
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def list_templates(self, agency_id: str | None = None, include_defaults: bool = True, **filters: Any) -> list[dict[str, Any]]:
        query: dict[str, Any] = {}
        for field in ["template_code", "trigger_event", "status", "required_capability"]:
            if filters.get(field):
                query[field] = (
                    canonical_event_type(filters[field])
                    if field == "trigger_event"
                    else self._norm(filters[field])
                )
        templates = await self.db.collection(OPERATIONAL_TASK_TEMPLATES_COLLECTION).find_many(query or None)
        if agency_id:
            templates = [
                item for item in templates if item.get("agency_id") in {None, agency_id}
            ]
        if include_defaults:
            existing_codes = {item.get("template_code") for item in templates}
            for template in SAFE_TASK_TEMPLATES:
                if template["template_code"] in existing_codes:
                    continue
                if filters.get("trigger_event") and canonical_event_type(filters["trigger_event"]) != template["trigger_event"]:
                    continue
                templates.append(self._default_template(template, agency_id=agency_id))
        templates.sort(key=lambda item: str(item.get("template_code") or ""))
        return templates

    async def create_template(self, payload: OperationalTaskTemplateCreate | dict[str, Any], user: dict) -> dict[str, Any]:
        data = self._payload(payload)
        if not data.get("template_code"):
            data["template_code"] = self._code(data.get("title_pattern") or "task_template")
        self._normalize_template(data)
        data["created_by"] = user.get("id")
        data["updated_by"] = user.get("id")
        data["trigger_event"] = canonical_event_type(data["trigger_event"])
        data.setdefault("status", "draft")
        created = await self.db.collection(OPERATIONAL_TASK_TEMPLATES_COLLECTION).insert_one(OperationalTaskTemplate(**data).model_dump(mode="json"))
        return {"phase": PHASE_LABEL, "template": created, "metadata_only": True, **self.safety_flags()}

    async def update_template(self, template_id: str, payload: OperationalTaskTemplateUpdate | dict[str, Any], user: dict, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": template_id}
        if agency_id:
            filters["agency_id"] = agency_id
        existing = await self.db.collection(OPERATIONAL_TASK_TEMPLATES_COLLECTION).find_one(filters)
        if not existing:
            raise TaskAutomationDependencyError("Task template metadata was not found.")
        updates = self._payload(payload, exclude_unset=True)
        if not updates:
            raise TaskAutomationDependencyError("No task template metadata updates were provided.")
        if set(updates) & {"agency_id", "scope", "template_code"}:
            raise TaskAutomationDependencyError(
                "Task template Agency scope and stable template code are immutable."
            )
        merged = {**existing, **updates}
        self._normalize_template(merged, partial=True)
        for field in ["scope", "template_code", "trigger_event", "default_priority", "assigned_role_strategy", "assigned_team_strategy", "required_capability", "status"]:
            if field in updates and updates[field] is not None:
                updates[field] = self._norm(updates[field])
        updates["updated_by"] = user.get("id")
        updated = await self.db.collection(OPERATIONAL_TASK_TEMPLATES_COLLECTION).update_one({"id": existing["id"]}, updates)
        return {"phase": PHASE_LABEL, "template": updated, "metadata_only": True, **self.safety_flags()}

    async def list_rules(self, agency_id: str | None = None, include_defaults: bool = True, **filters: Any) -> list[dict[str, Any]]:
        query: dict[str, Any] = {}
        for field in ["rule_code", "rule_key", "generated_template_code", "status"]:
            if filters.get(field):
                query[field] = self._norm(filters[field])
        if filters.get("trigger_event"):
            query["trigger_event"] = canonical_event_type(filters["trigger_event"])
        if "enabled" in filters and filters["enabled"] is not None:
            query["enabled"] = bool(filters["enabled"])
        rules = await self.db.collection(OPERATIONAL_TASK_AUTOMATION_RULES_COLLECTION).find_many(query or None)
        if agency_id:
            rules = [item for item in rules if item.get("agency_id") in {None, agency_id}]
        if include_defaults:
            existing_codes = {item.get("rule_key") or item.get("rule_code") for item in rules}
            for rule in DEFAULT_AUTOMATION_RULES:
                if rule["rule_key"] in existing_codes:
                    continue
                if filters.get("trigger_event") and canonical_event_type(filters["trigger_event"]) != rule["trigger_event"]:
                    continue
                rules.append(self._default_rule(rule, agency_id=agency_id))
        rules.sort(
            key=lambda item: (
                int(item.get("priority") or 100),
                str(item.get("rule_key") or item.get("rule_code") or ""),
                -int(item.get("version") or 1),
                str(item.get("id") or ""),
            )
        )
        return rules

    async def create_rule(self, payload: OperationalTaskAutomationRuleCreate | dict[str, Any], user: dict) -> dict[str, Any]:
        data = self._payload(payload)
        data["agency_id"] = data.get("agency_id") or None
        data["scope"] = "agency" if data["agency_id"] else "platform"
        data["platform_scope"] = not bool(data["agency_id"])
        rule_key = self._stable_code(
            data.get("rule_key")
            or data.get("rule_code")
            or data.get("name")
            or data.get("generated_template_code")
            or "task_rule"
        )
        data["rule_key"] = rule_key
        prior_versions = await self.db.collection(
            OPERATIONAL_TASK_AUTOMATION_RULES_COLLECTION
        ).find_many(self._rule_scope_filter(data["agency_id"], rule_key))
        data["version"] = max(
            [int(item.get("version") or 1) for item in prior_versions] or [0]
        ) + 1
        data["rule_code"] = (
            rule_key if data["version"] == 1 else f"{rule_key}_v{data['version']}"
        )
        if not data.get("deduplication_key_pattern"):
            data["deduplication_key_pattern"] = (
                "{agency_id}:{source_timeline_entry_id}:{rule_id}:{action_index}"
            )
        data["status"] = "draft"
        data["enabled"] = False
        data["published_at"] = None
        data["published_by"] = None
        data["reconciliation_status"] = "canonical"
        self._normalize_rule(data)
        data["created_by"] = user.get("id")
        data["updated_by"] = user.get("id")
        created = await self.db.collection(OPERATIONAL_TASK_AUTOMATION_RULES_COLLECTION).insert_one(OperationalTaskAutomationRule(**data).model_dump(mode="json"))
        await self._audit(
            agency_id=created.get("agency_id"),
            actor_user_id=user.get("id"),
            event_type="automation.rule_created",
            entity_id=created["id"],
            summary=f"Automation rule {rule_key} version {created['version']} created as draft.",
            metadata={"rule_key": rule_key, "version": created["version"]},
        )
        return {"phase": PHASE_LABEL, "rule": created, "metadata_only": True, **self.safety_flags()}

    async def update_rule(self, rule_id: str, payload: OperationalTaskAutomationRuleUpdate | dict[str, Any], user: dict, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": rule_id}
        if agency_id:
            filters["agency_id"] = agency_id
        existing = await self.db.collection(OPERATIONAL_TASK_AUTOMATION_RULES_COLLECTION).find_one(filters)
        if not existing:
            raise TaskAutomationDependencyError("Task automation rule metadata was not found.")
        updates = self._payload(payload, exclude_unset=True)
        if not updates:
            raise TaskAutomationDependencyError("No task automation rule metadata updates were provided.")
        allowed_fields = {
            "name",
            "description",
            "trigger_event",
            "trigger_event_types",
            "trigger_entity_types",
            "conditions_json",
            "actions",
            "generated_template_code",
            "deduplication_key_pattern",
            "priority",
            "effective_from",
            "effective_to",
            "execution_safety_class",
            "dry_run_supported",
            "expected_version",
            "audit_metadata",
            "metadata",
        }
        unsupported = sorted(set(updates) - allowed_fields)
        if unsupported:
            raise TaskAutomationDependencyError(
                "Rule tenant scope, stable key, lifecycle state, and ownership "
                "are immutable outside governed lifecycle actions."
            )
        expected_version = updates.pop("expected_version", None)
        if expected_version is not None and int(expected_version) != int(existing.get("version") or 1):
            raise TaskAutomationDependencyError("Automation rule version conflict.")
        merged = {**existing, **updates}
        merged.pop("id", None)
        merged.pop("created_at", None)
        merged.pop("updated_at", None)
        prior_versions = await self.db.collection(
            OPERATIONAL_TASK_AUTOMATION_RULES_COLLECTION
        ).find_many(
            self._rule_scope_filter(
                existing.get("agency_id"),
                existing.get("rule_key") or existing.get("rule_code"),
            )
        )
        merged["version"] = max(
            [int(item.get("version") or 1) for item in prior_versions] or [0]
        ) + 1
        merged["rule_code"] = f"{existing.get('rule_key') or existing.get('rule_code')}_v{merged['version']}"
        merged["status"] = "draft"
        merged["enabled"] = False
        merged["published_at"] = None
        merged["published_by"] = None
        merged["superseded_at"] = None
        merged["superseded_by_rule_id"] = None
        merged["created_by"] = user.get("id")
        merged["updated_by"] = user.get("id")
        self._normalize_rule(merged)
        versioned = await self.db.collection(
            OPERATIONAL_TASK_AUTOMATION_RULES_COLLECTION
        ).insert_one(OperationalTaskAutomationRule(**merged).model_dump(mode="json"))
        await self._audit(
            agency_id=versioned.get("agency_id"),
            actor_user_id=user.get("id"),
            event_type="automation.rule_version_created",
            entity_id=versioned["id"],
            summary=f"Automation rule {versioned['rule_key']} version {versioned['version']} created as draft.",
            metadata={"previous_rule_id": existing["id"]},
        )
        return {
            "phase": PHASE_LABEL,
            "rule": versioned,
            "previous_rule": existing,
            "material_change_created_new_version": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def publish_rule(
        self,
        rule_id: str,
        payload: OperationalAutomationRuleLifecycleRequest | dict[str, Any],
        user: dict,
        *,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        rule = await self._require_rule(rule_id, agency_id=agency_id)
        data = self._payload(payload)
        if rule.get("status") != "draft":
            raise TaskAutomationDependencyError("Only draft rule versions may be published.")
        self._check_expected_version(rule, data.get("expected_version"))
        self._normalize_rule(dict(rule))
        active = await self._active_rule_versions(
            rule.get("agency_id"), rule.get("rule_key") or rule.get("rule_code")
        )
        if active:
            raise TaskAutomationDependencyError(
                "An active published rule with this rule_key already exists. "
                "Use explicit supersede to preserve history."
            )
        now = self._now()
        updated = await self.db.collection(
            OPERATIONAL_TASK_AUTOMATION_RULES_COLLECTION
        ).update_one(
            {"id": rule["id"], "version": rule.get("version", 1)},
            {
                "status": "active",
                "enabled": True,
                "published_at": now,
                "published_by": user.get("id"),
                "updated_by": user.get("id"),
                "audit_metadata": {
                    **(rule.get("audit_metadata") or {}),
                    "publish_reason": data.get("reason"),
                },
            },
        )
        if not updated:
            raise TaskAutomationDependencyError("Automation rule version conflict.")
        await self._audit_rule_lifecycle(updated, user, "published", data.get("reason"))
        return {"phase": PHASE_LABEL, "rule": updated, "metadata_only": True, **self.safety_flags()}

    async def deactivate_rule(
        self,
        rule_id: str,
        payload: OperationalAutomationRuleLifecycleRequest | dict[str, Any],
        user: dict,
        *,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        rule = await self._require_rule(rule_id, agency_id=agency_id)
        data = self._payload(payload)
        self._check_expected_version(rule, data.get("expected_version"))
        if rule.get("status") not in {"active", "draft"}:
            raise TaskAutomationDependencyError("Only active or draft rules may be deactivated.")
        updated = await self.db.collection(
            OPERATIONAL_TASK_AUTOMATION_RULES_COLLECTION
        ).update_one(
            {"id": rule["id"], "version": rule.get("version", 1)},
            {
                "status": "inactive",
                "enabled": False,
                "updated_by": user.get("id"),
                "audit_metadata": {
                    **(rule.get("audit_metadata") or {}),
                    "deactivation_reason": data.get("reason"),
                },
            },
        )
        if not updated:
            raise TaskAutomationDependencyError("Automation rule version conflict.")
        await self._audit_rule_lifecycle(updated, user, "deactivated", data.get("reason"))
        return {"phase": PHASE_LABEL, "rule": updated, "metadata_only": True, **self.safety_flags()}

    async def supersede_rule(
        self,
        rule_id: str,
        payload: OperationalAutomationRuleLifecycleRequest | dict[str, Any],
        user: dict,
        *,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        replacement = await self._require_rule(rule_id, agency_id=agency_id)
        data = self._payload(payload)
        if replacement.get("status") != "draft":
            raise TaskAutomationDependencyError("Replacement rule must be a draft version.")
        self._check_expected_version(replacement, data.get("expected_version"))
        active = await self._active_rule_versions(
            replacement.get("agency_id"),
            replacement.get("rule_key") or replacement.get("rule_code"),
        )
        if len(active) != 1:
            raise TaskAutomationDependencyError(
                "Explicit supersede requires exactly one active published predecessor."
            )
        predecessor = active[0]
        now = self._now()
        predecessor_update = await self.db.collection(
            OPERATIONAL_TASK_AUTOMATION_RULES_COLLECTION
        ).update_one(
            {
                "id": predecessor["id"],
                "status": "active",
                "enabled": True,
            },
            {
                "status": "superseded",
                "enabled": False,
                "superseded_at": now,
                "superseded_by_rule_id": replacement["id"],
                "updated_by": user.get("id"),
            },
        )
        if not predecessor_update:
            raise TaskAutomationDependencyError(
                "Active predecessor changed before supersession could be recorded."
            )
        updated = await self.db.collection(
            OPERATIONAL_TASK_AUTOMATION_RULES_COLLECTION
        ).update_one(
            {
                "id": replacement["id"],
                "status": "draft",
                "version": replacement.get("version", 1),
            },
            {
                "status": "active",
                "enabled": True,
                "published_at": now,
                "published_by": user.get("id"),
                "updated_by": user.get("id"),
                "audit_metadata": {
                    **(replacement.get("audit_metadata") or {}),
                    "supersede_reason": data.get("reason"),
                    "superseded_rule_id": predecessor["id"],
                },
            },
        )
        if not updated:
            restored = await self.db.collection(
                OPERATIONAL_TASK_AUTOMATION_RULES_COLLECTION
            ).update_one(
                {
                    "id": predecessor["id"],
                    "status": "superseded",
                    "superseded_by_rule_id": replacement["id"],
                },
                {
                    "status": "active",
                    "enabled": True,
                    "superseded_at": None,
                    "superseded_by_rule_id": None,
                    "updated_by": user.get("id"),
                },
            )
            if not restored:
                raise TaskAutomationDependencyError(
                    "Rule supersession failed and predecessor restoration "
                    "requires manual review."
                )
            raise TaskAutomationDependencyError(
                "Replacement rule changed during supersession; the active "
                "predecessor was restored."
            )
        await self._audit_rule_lifecycle(updated or replacement, user, "superseded", data.get("reason"))
        return {
            "phase": PHASE_LABEL,
            "rule": updated,
            "superseded_rule_id": predecessor["id"],
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def list_dependencies(
        self,
        agency_id: str | None = None,
        status: str | None = None,
        predecessor_task_id: str | None = None,
        successor_task_id: str | None = None,
        source_entity_type: str | None = None,
        source_entity_id: str | None = None,
        **_: Any,
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {}
        if agency_id:
            query["agency_id"] = agency_id
        if status:
            query["status"] = self._norm(status)
        if predecessor_task_id:
            query["predecessor_task_id"] = predecessor_task_id
        if successor_task_id:
            query["successor_task_id"] = successor_task_id
        if source_entity_type:
            query["source_entity_type"] = self._norm(source_entity_type)
        if source_entity_id:
            query["source_entity_id"] = source_entity_id
        dependencies = await self.db.collection(OPERATIONAL_TASK_DEPENDENCIES_COLLECTION).find_many(query or None)
        dependencies.sort(key=lambda item: self._sort_text(item.get("created_at")))
        return [await self._dependency_projection(item) for item in dependencies]

    async def create_dependency(self, payload: OperationalTaskDependencyCreate | dict[str, Any], user: dict, agency_id: str | None = None) -> dict[str, Any]:
        data = self._payload(payload)
        if agency_id:
            data["agency_id"] = agency_id
        self._normalize_dependency(data)
        if data["predecessor_task_id"] == data["successor_task_id"]:
            raise TaskAutomationDependencyError("A work item cannot depend on itself.")
        predecessor = await self._require_work_item(
            data["predecessor_task_id"], data["agency_id"]
        )
        successor = await self._require_work_item(
            data["successor_task_id"], data["agency_id"]
        )
        if predecessor.get("agency_id") != successor.get("agency_id"):
            raise TaskAutomationDependencyError(
                "Task dependencies must remain inside one Agency."
            )
        if await self._dependency_would_cycle(
            data["agency_id"],
            data["predecessor_task_id"],
            data["successor_task_id"],
        ):
            raise TaskAutomationDependencyError("Task dependency cycle detected.")
        existing = await self.db.collection(
            OPERATIONAL_TASK_DEPENDENCIES_COLLECTION
        ).find_one(
            {
                "agency_id": data["agency_id"],
                "predecessor_task_id": data["predecessor_task_id"],
                "successor_task_id": data["successor_task_id"],
                "dependency_type": data.get("dependency_type") or "mandatory",
            }
        )
        if existing:
            return {
                "phase": PHASE_LABEL,
                "dependency": await self._dependency_projection(existing),
                "idempotent_reused": True,
                "metadata_only": True,
                **self.safety_flags(),
            }
        data["created_by"] = user.get("id")
        data["updated_by"] = user.get("id")
        created = await self.db.collection(OPERATIONAL_TASK_DEPENDENCIES_COLLECTION).insert_one(OperationalTaskDependency(**data).model_dump(mode="json"))
        await self.evaluate_dependencies(data["agency_id"], user, successor_task_id=created["successor_task_id"])
        await self._audit(
            agency_id=data["agency_id"],
            actor_user_id=user.get("id"),
            event_type="automation.dependency_created",
            entity_id=created["id"],
            summary="Canonical work-item dependency created.",
            metadata={
                "predecessor_task_id": predecessor["id"],
                "successor_task_id": successor["id"],
                "dependency_type": created.get("dependency_type"),
            },
        )
        await self._timeline(
            agency_id=data["agency_id"],
            entity_type="task",
            entity_id=successor["id"],
            event_type="task.dependency_added",
            summary="A work-item dependency was added.",
            actor=user,
            idempotency_key=f"task-dependency-created:{created['id']}",
            details={"dependency_id": created["id"]},
        )
        return {"phase": PHASE_LABEL, "dependency": await self._dependency_projection(created), "idempotent_reused": False, "metadata_only": True, **self.safety_flags()}

    async def update_dependency(self, dependency_id: str, payload: OperationalTaskDependencyUpdate | dict[str, Any], user: dict, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": dependency_id}
        if agency_id:
            filters["agency_id"] = agency_id
        existing = await self.db.collection(OPERATIONAL_TASK_DEPENDENCIES_COLLECTION).find_one(filters)
        if not existing:
            raise TaskAutomationDependencyError("Task dependency metadata was not found.")
        updates = self._payload(payload, exclude_unset=True)
        if not updates:
            raise TaskAutomationDependencyError("No task dependency metadata updates were provided.")
        if set(updates) - {"dependency_type", "status", "satisfied_at", "blocked_reason", "metadata"}:
            raise TaskAutomationDependencyError(
                "Task dependency ownership and task references are immutable."
            )
        if "dependency_type" in updates and updates["dependency_type"]:
            updates["dependency_type"] = self._norm(updates["dependency_type"])
        if "status" in updates and updates["status"]:
            updates["status"] = self._norm(updates["status"])
            if updates["status"] == "satisfied" and not updates.get("satisfied_at"):
                updates["satisfied_at"] = self._now()
        updates["updated_by"] = user.get("id")
        updated = await self.db.collection(OPERATIONAL_TASK_DEPENDENCIES_COLLECTION).update_one({"id": existing["id"]}, updates)
        if updated:
            await self.evaluate_dependencies(updated["agency_id"], user, successor_task_id=updated["successor_task_id"])
        return {"phase": PHASE_LABEL, "dependency": await self._dependency_projection(updated or existing), "metadata_only": True, **self.safety_flags()}

    async def satisfy_dependency(self, dependency_id: str, payload: OperationalTaskDependencyActionRequest | dict[str, Any], user: dict, agency_id: str | None = None) -> dict[str, Any]:
        data = self._payload(payload)
        result = await self.update_dependency(
            dependency_id,
            {
                "status": "satisfied",
                "satisfied_at": self._now(),
                "blocked_reason": data.get("reason"),
                "metadata": {
                    **(data.get("metadata") or {}),
                    "satisfied_by": user.get("id"),
                    "satisfied_reason": data.get("reason"),
                },
            },
            user,
            agency_id=agency_id,
        )
        return result

    async def waive_dependency(self, dependency_id: str, payload: OperationalTaskDependencyActionRequest | dict[str, Any], user: dict, agency_id: str | None = None) -> dict[str, Any]:
        data = self._payload(payload)
        if not str(data.get("reason") or "").strip():
            raise TaskAutomationDependencyError(
                "Waiving a dependency requires an actor reason."
            )
        return await self.update_dependency(
            dependency_id,
            {
                "status": "waived",
                "blocked_reason": data["reason"],
                "metadata": {
                    **(data.get("metadata") or {}),
                    "waived_by": user.get("id"),
                    "waived_at": self._now(),
                },
            },
            user,
            agency_id=agency_id,
        )

    async def list_runs(self, agency_id: str | None = None, trigger_event: str | None = None, status: str | None = None, source_entity_type: str | None = None, source_entity_id: str | None = None, **_: Any) -> list[dict[str, Any]]:
        query: dict[str, Any] = {}
        if agency_id:
            query["agency_id"] = agency_id
        if trigger_event:
            query["trigger_event"] = self._norm(trigger_event)
        if status:
            query["status"] = self._norm(status)
        if source_entity_type:
            query["source_entity_type"] = self._norm(source_entity_type)
        if source_entity_id:
            query["source_entity_id"] = source_entity_id
        runs = await self.db.collection(OPERATIONAL_TASK_AUTOMATION_RUNS_COLLECTION).find_many(query or None)
        runs.sort(key=lambda item: self._sort_text(item.get("created_at")), reverse=True)
        return runs

    async def run_automation(self, payload: OperationalTaskAutomationRunRequest | dict[str, Any], user: dict, agency_id: str | None = None) -> dict[str, Any]:
        started = monotonic()
        data = self._payload(payload)
        if agency_id:
            data["agency_id"] = agency_id
        self._validate_run_request(data)
        if data.get("dry_run"):
            raise TaskAutomationDependencyError(
                "Execution dry runs must use the rule dry-run or bounded "
                "timeline preview route; those paths perform zero writes."
            )
        data["trigger_event"] = canonical_event_type(data["trigger_event"])
        data["source_entity_type"] = self._norm(data["source_entity_type"])
        source_timeline = await self._resolve_source_timeline(data, user)
        data["source_timeline_entry_id"] = source_timeline["id"]
        if source_timeline.get("agency_id") != data["agency_id"]:
            raise TaskAutomationDependencyError(
                "Automation source timeline entry belongs to another Agency."
            )
        source_event = canonical_event_type(source_timeline.get("event_type"))
        if source_event != data["trigger_event"]:
            raise TaskAutomationDependencyError(
                "Automation trigger must match the exact source timeline event."
            )
        base_idempotency_key = (
            data.get("idempotency_key") or self._idempotency_key(data)
        )
        retry_count = int((data.get("metadata") or {}).get("retry_count") or 0)
        idempotency_key = (
            f"{base_idempotency_key}:retry:{data.get('retry_of_run_id')}:{retry_count}"
            if data.get("retry_of_run_id")
            else base_idempotency_key
        )
        existing = await self.db.collection(
            OPERATIONAL_TASK_AUTOMATION_RUNS_COLLECTION
        ).find_one(
            {
                "agency_id": data["agency_id"],
                "idempotency_key": idempotency_key,
            }
        )
        if existing:
            return {
                "phase": PHASE_LABEL,
                "run": existing,
                "idempotent_reused": True,
                "metadata_only": True,
                **self.safety_flags(),
            }

        run_id = new_id()
        run_reference = self._run_reference(data["trigger_event"])
        lock_token = new_id()
        safe_event_snapshot = bounded_safe_snapshot(
            data.get("event_snapshot_json") or {}
        )
        reservation = OperationalTaskAutomationRun(
            id=run_id,
            agency_id=data["agency_id"],
            run_reference=run_reference,
            trigger_event=data["trigger_event"],
            source_entity_type=data["source_entity_type"],
            source_entity_id=data["source_entity_id"],
            source_timeline_entry_id=source_timeline["id"],
            idempotency_key=idempotency_key,
            event_snapshot_json=safe_event_snapshot,
            status="processing",
            lock_token=lock_token,
            locked_until=self._now() + timedelta(minutes=EXECUTION_LOCK_MINUTES),
            retry_count=retry_count,
            recursion_depth=int(data.get("recursion_depth") or 0),
            chained_action_count=int(data.get("chained_action_count") or 0),
            retry_of_run_id=data.get("retry_of_run_id"),
            created_by=user.get("id"),
            updated_by=user.get("id"),
            metadata=bounded_safe_snapshot(data.get("metadata") or {}),
        )
        try:
            await self.db.collection(
                OPERATIONAL_TASK_AUTOMATION_RUNS_COLLECTION
            ).insert_one(reservation.model_dump(mode="json"))
        except Exception:
            concurrent = await self.db.collection(
                OPERATIONAL_TASK_AUTOMATION_RUNS_COLLECTION
            ).find_one(
                {
                    "agency_id": data["agency_id"],
                    "idempotency_key": idempotency_key,
                }
            )
            if concurrent:
                return {
                    "phase": PHASE_LABEL,
                    "run": concurrent,
                    "idempotent_reused": True,
                    "metadata_only": True,
                    **self.safety_flags(),
                }
            raise

        templates = await self.list_templates(
            agency_id=data["agency_id"],
            include_defaults=True,
            trigger_event=data["trigger_event"],
        )
        templates_by_code = {template["template_code"]: template for template in templates}
        requested_codes = set(data.get("template_codes") or [])
        rules = await self.list_rules(
            agency_id=data["agency_id"],
            include_defaults=False,
            trigger_event=data["trigger_event"],
            enabled=True,
            status="active",
        )
        now = self._now()
        rules = [
            rule
            for rule in rules
            if rule.get("published_at")
            and (not self._parse_dt(rule.get("effective_from")) or self._parse_dt(rule.get("effective_from")) <= now)
            and (not self._parse_dt(rule.get("effective_to")) or self._parse_dt(rule.get("effective_to")) >= now)
        ]
        if requested_codes:
            rules = [rule for rule in rules if rule.get("generated_template_code") in requested_codes]

        matched_rules: list[dict[str, Any]] = []
        evaluation_trace: list[dict[str, Any]] = []
        actions_attempted: list[dict[str, Any]] = []
        actions_completed: list[dict[str, Any]] = []
        actions_skipped: list[dict[str, Any]] = []
        tasks_created: list[dict[str, Any]] = []
        tasks_skipped: list[dict[str, Any]] = []
        dependencies_created: list[dict[str, Any]] = []
        approvals_created: list[str] = []
        timeline_entries_created: list[str] = []
        warnings: list[str] = []
        errors: list[str] = []
        tasks_by_template: dict[str, dict[str, Any]] = {}
        context = self._evaluation_context(data, source_timeline)
        for rule in rules:
            try:
                normalized_rule = validate_rule_contract(dict(rule))
                matched, trace = evaluate_conditions(
                    normalized_rule.get("conditions_json") or {},
                    context,
                    evaluation_time=self._parse_dt(source_timeline.get("event_time")),
                )
            except GovernedAutomationContractError as exc:
                errors.append(f"Rule {rule.get('rule_code')} is invalid: {exc}")
                continue
            for item in trace:
                evaluation_trace.append(
                    {
                        "rule_id": rule["id"],
                        "rule_key": rule.get("rule_key") or rule.get("rule_code"),
                        "rule_version": rule.get("version") or 1,
                        **item,
                    }
                )
            if not matched:
                continue
            matched_rules.append(
                {
                    "rule_id": rule["id"],
                    "rule_code": rule.get("rule_code"),
                    "rule_key": rule.get("rule_key") or rule.get("rule_code"),
                    "rule_version": rule.get("version") or 1,
                    "metadata_only": True,
                }
            )
            for action_index, action in enumerate(normalized_actions(normalized_rule)):
                if len(actions_attempted) >= MAX_CHAINED_ACTIONS:
                    errors.append(
                        f"Chained action limit of {MAX_CHAINED_ACTIONS} was reached."
                    )
                    break
                attempted = {
                    "rule_id": rule["id"],
                    "rule_version": rule.get("version") or 1,
                    "action_index": action_index,
                    "action_type": action["action_type"],
                    "safety_class": action["safety_class"],
                }
                actions_attempted.append(attempted)
                try:
                    outcome = await self._execute_governed_action(
                        data=data,
                        source_timeline=source_timeline,
                        rule=normalized_rule,
                        action=action,
                        action_index=action_index,
                        execution_id=run_id,
                        user=user,
                        templates_by_code=templates_by_code,
                    )
                except (TaskAutomationDependencyError, GovernedAutomationContractError) as exc:
                    errors.append(
                        f"Rule {rule.get('rule_code')} action {action_index} failed: {exc}"
                    )
                    actions_skipped.append({**attempted, "reason": str(exc)})
                    continue
                actions_completed.append({**attempted, **outcome.get("trace", {})})
                work_item = outcome.get("work_item")
                if work_item:
                    task_ref = {
                        "template_code": outcome.get("template_code"),
                        "task_id": work_item["id"],
                        "title": work_item.get("title"),
                        "status": work_item.get("status"),
                        "due_at": work_item.get("due_at"),
                        "deduplication_key": work_item.get("source_fingerprint"),
                    }
                    if outcome.get("idempotent_reused"):
                        tasks_skipped.append({**task_ref, "reason": "deduplicated"})
                    else:
                        tasks_created.append(task_ref)
                    if outcome.get("template_code"):
                        tasks_by_template[outcome["template_code"]] = work_item
                if outcome.get("approval_id"):
                    approvals_created.append(outcome["approval_id"])
                if outcome.get("timeline_entry_id"):
                    timeline_entries_created.append(outcome["timeline_entry_id"])

        run_status = "completed"
        if errors:
            run_status = "failed" if not actions_completed else "completed_with_warnings"
        elif warnings:
            run_status = "completed_with_warnings"
        if not matched_rules:
            run_status = "skipped"
            warnings.append("No enabled task automation rules matched the event snapshot.")

        run = OperationalTaskAutomationRun(
            id=run_id,
            agency_id=data["agency_id"],
            run_reference=run_reference,
            trigger_event=data["trigger_event"],
            source_entity_type=data["source_entity_type"],
            source_entity_id=data["source_entity_id"],
            source_timeline_entry_id=source_timeline["id"],
            idempotency_key=idempotency_key,
            event_snapshot_json=safe_event_snapshot,
            rules_matched=matched_rules,
            evaluation_trace=evaluation_trace,
            actions_attempted=actions_attempted,
            actions_completed=actions_completed,
            actions_skipped=actions_skipped,
            tasks_created=tasks_created,
            tasks_skipped=tasks_skipped,
            approvals_created=sorted(set(approvals_created)),
            timeline_entries_created=sorted(set(timeline_entries_created)),
            warnings=warnings,
            errors=errors,
            failure_reason="; ".join(errors)[:500] if errors else None,
            status=run_status,
            execution_safety_class=self._max_safety_class(actions_attempted),
            idempotency_result="created",
            duration_ms=max(0, int((monotonic() - started) * 1000)),
            retry_count=retry_count,
            recursion_depth=int(data.get("recursion_depth") or 0),
            chained_action_count=len(actions_attempted),
            dry_run=False,
            retry_of_run_id=data.get("retry_of_run_id"),
            created_by=user.get("id"),
            updated_by=user.get("id"),
            lock_token=None,
            locked_until=None,
            metadata=bounded_safe_snapshot(data.get("metadata") or {}),
        )
        run_updates = run.model_dump(mode="json")
        for immutable_field in {"id", "created_at", "updated_at"}:
            run_updates.pop(immutable_field, None)
        created_run = await self.db.collection(
            OPERATIONAL_TASK_AUTOMATION_RUNS_COLLECTION
        ).update_one(
            {"id": run_id, "lock_token": lock_token},
            run_updates,
        )
        if not created_run:
            raise TaskAutomationDependencyError(
                "Automation execution lock was lost; manual review is required."
            )

        dependencies_created = await self._create_run_dependencies(data, created_run["id"], tasks_by_template, user)
        if dependencies_created:
            created_run = await self.db.collection(OPERATIONAL_TASK_AUTOMATION_RUNS_COLLECTION).update_one(
                {"id": created_run["id"]},
                {"dependencies_created": dependencies_created, "updated_by": user.get("id")},
            ) or created_run
            await self.evaluate_dependencies(data["agency_id"], user, source_entity_type=data["source_entity_type"], source_entity_id=data["source_entity_id"])
        await self._record_workflow_event(data, created_run)
        completion_timeline = await self._timeline(
            agency_id=data["agency_id"],
            entity_type=data["source_entity_type"],
            entity_id=data["source_entity_id"],
            event_type="automation.execution_completed",
            summary=f"Governed automation execution finished with status {run_status}.",
            actor=user,
            idempotency_key=f"automation-run-completed:{created_run['id']}",
            details={
                "source_timeline_entry_id": source_timeline["id"],
                "automation_execution_id": created_run["id"],
                "matched_rule_count": len(matched_rules),
                "created_work_item_ids": [
                    item["task_id"] for item in tasks_created if item.get("task_id")
                ],
                "created_approval_ids": sorted(set(approvals_created)),
                "safety_class": created_run.get("execution_safety_class"),
            },
        )
        timeline_entries_created.append(completion_timeline["id"])
        created_run = await self.db.collection(
            OPERATIONAL_TASK_AUTOMATION_RUNS_COLLECTION
        ).update_one(
            {"id": created_run["id"]},
            {
                "timeline_entries_created": sorted(set(timeline_entries_created)),
                "duration_ms": max(0, int((monotonic() - started) * 1000)),
            },
        ) or created_run

        return {"phase": PHASE_LABEL, "run": created_run, "idempotent_reused": False, "metadata_only": True, **self.safety_flags()}

    async def retry_run(self, run_id: str, payload: OperationalTaskDependencyActionRequest | dict[str, Any], user: dict, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": run_id}
        if agency_id:
            filters["agency_id"] = agency_id
        existing = await self.db.collection(OPERATIONAL_TASK_AUTOMATION_RUNS_COLLECTION).find_one(filters)
        if not existing:
            raise TaskAutomationDependencyError("Task automation run metadata was not found.")
        request = {
            "agency_id": existing["agency_id"],
            "trigger_event": existing["trigger_event"],
            "source_entity_type": existing["source_entity_type"],
            "source_entity_id": existing["source_entity_id"],
            "source_timeline_entry_id": existing.get("source_timeline_entry_id"),
            "request_id": (existing.get("event_snapshot_json") or {}).get("request_id") or existing["source_entity_id"],
            "event_snapshot_json": existing.get("event_snapshot_json") or {},
            "template_codes": [rule.get("template_code") for rule in existing.get("rules_matched") or [] if rule.get("template_code")],
            "retry_of_run_id": existing["id"],
            "idempotency_key": existing.get("idempotency_key"),
            "metadata": {
                "manual_retry": True,
                "retry_count": int(existing.get("retry_count") or 0) + 1,
                **(self._payload(payload).get("metadata") or {}),
            },
        }
        if request["metadata"]["retry_count"] > 3:
            await self.db.collection(
                OPERATIONAL_TASK_AUTOMATION_RUNS_COLLECTION
            ).update_one(
                {"id": existing["id"]},
                {
                    "status": "manual_review",
                    "failure_reason": "Bounded retry limit reached.",
                    "updated_by": user.get("id"),
                },
            )
            raise TaskAutomationDependencyError(
                "Automation retry limit reached; manual review is required."
            )
        return await self.run_automation(request, user, agency_id=existing["agency_id"])

    async def evaluate_dependencies(self, agency_id: str, user: dict, successor_task_id: str | None = None, source_entity_type: str | None = None, source_entity_id: str | None = None) -> dict[str, Any]:
        dependencies = await self.list_dependencies(agency_id=agency_id, successor_task_id=successor_task_id, source_entity_type=source_entity_type, source_entity_id=source_entity_id)
        updated_dependencies: list[dict[str, Any]] = []
        affected_successors = {dependency["successor_task_id"] for dependency in dependencies}
        for dependency in dependencies:
            predecessor = await self.db.collection("operational_work_items").find_one({"agency_id": agency_id, "id": dependency["predecessor_task_id"]})
            if dependency.get("status") in {"satisfied", "waived"}:
                continue
            if predecessor and predecessor.get("status") == "completed":
                updated = await self.db.collection(OPERATIONAL_TASK_DEPENDENCIES_COLLECTION).update_one(
                    {"id": dependency["id"]},
                    {"status": "satisfied", "satisfied_at": self._now(), "updated_by": user.get("id")},
                )
                if updated:
                    updated_dependencies.append(await self._dependency_projection(updated))
        ready: list[dict[str, Any]] = []
        blocked: list[dict[str, Any]] = []
        for task_id in affected_successors:
            task = await self.db.collection("operational_work_items").find_one({"agency_id": agency_id, "id": task_id})
            if not task:
                continue
            task_dependencies = await self.db.collection(OPERATIONAL_TASK_DEPENDENCIES_COLLECTION).find_many({"agency_id": agency_id, "successor_task_id": task_id})
            unsatisfied = [
                dep
                for dep in task_dependencies
                if dep.get("status") not in {"satisfied", "waived"}
                and dep.get("dependency_type") != "advisory"
            ]
            if unsatisfied:
                dependency_ids = sorted(dep["id"] for dep in unsatisfied)
                blockers = [
                    {
                        "blocker_type": "mandatory_dependency",
                        "dependency_id": dep["id"],
                        "predecessor_task_id": dep["predecessor_task_id"],
                        "reason": dep.get("blocked_reason")
                        or "Mandatory predecessor is incomplete.",
                        "resolved": False,
                    }
                    for dep in unsatisfied
                ]
                if task.get("status") not in {"completed", "cancelled", "approval_required"}:
                    task = await AgentWorkQueueService(
                        self.db
                    ).synchronize_dependency_state(
                        task_id,
                        agency_id=agency_id,
                        blocked=True,
                        dependency_ids=dependency_ids,
                        dependency_blockers=blockers,
                        user=user,
                    )
                blocked.append(task)
            else:
                if task.get("status") == "blocked" and task.get("blocker_status") == "blocked":
                    task = await AgentWorkQueueService(
                        self.db
                    ).synchronize_dependency_state(
                        task_id,
                        agency_id=agency_id,
                        blocked=False,
                        dependency_ids=[],
                        dependency_blockers=[],
                        user=user,
                    )
                ready.append(task)
        return {"phase": PHASE_LABEL, "updated_dependencies": updated_dependencies, "ready_tasks": ready, "blocked_tasks": blocked, "metadata_only": True, **self.safety_flags()}

    async def ready_tasks(self, agency_id: str) -> list[dict[str, Any]]:
        tasks = await self.db.collection("operational_work_items").find_many({"agency_id": agency_id})
        return [
            task
            for task in tasks
            if task.get("status") in {"open", "assigned", "in_progress"}
            and task.get("blocker_status") == "not_blocked"
        ]

    async def blocked_tasks(self, agency_id: str) -> list[dict[str, Any]]:
        tasks = await self.db.collection("operational_work_items").find_many({"agency_id": agency_id})
        return [
            task
            for task in tasks
            if task.get("status") in {"blocked", "waiting", "approval_required"}
            or task.get("blocker_status") != "not_blocked"
        ]

    async def dry_run_rule(
        self,
        rule_id: str,
        payload: OperationalAutomationDryRunRequest | dict[str, Any],
        user: dict,
        *,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        rule = await self._require_rule(rule_id, agency_id=agency_id)
        data = self._payload(payload)
        source_timeline = None
        if data.get("source_timeline_entry_id"):
            filters = {"id": data["source_timeline_entry_id"]}
            if agency_id:
                filters["agency_id"] = agency_id
            source_timeline = await self.db.collection(
                "operational_timelines"
            ).find_one(filters)
            if not source_timeline:
                raise TaskAutomationDependencyError(
                    "Dry-run source timeline entry was not found in this Agency."
                )
        event_type = canonical_event_type(
            (source_timeline or {}).get("event_type")
            or rule.get("trigger_event")
            or (rule.get("trigger_event_types") or [""])[0]
        )
        source_type = self._norm(
            (source_timeline or {}).get("entity_type")
            or (rule.get("trigger_entity_types") or ["source"])[0]
        )
        source_id = (
            (source_timeline or {}).get("entity_id")
            or "safe-dry-run-fixture"
        )
        execution_data = {
            "agency_id": agency_id or rule.get("agency_id") or "platform-safe-fixture",
            "trigger_event": event_type,
            "source_entity_type": source_type,
            "source_entity_id": source_id,
            "event_snapshot_json": data.get("event_snapshot_json") or {},
        }
        context = self._evaluation_context(
            execution_data,
            source_timeline
            or {
                "id": "safe-dry-run-fixture",
                "agency_id": execution_data["agency_id"],
                "event_type": event_type,
                "entity_type": source_type,
                "entity_id": source_id,
                "event_time": self._now(),
            },
        )
        try:
            normalized = validate_rule_contract(dict(rule))
            matched, trace = evaluate_conditions(
                normalized.get("conditions_json") or {}, context
            )
            actions = [
                {
                    "action_type": item["action_type"],
                    "safety_class": item["safety_class"],
                    "would_execute_internal_action": item["safety_class"] in {"A", "B"},
                    "would_create_approval_only": item["safety_class"] == "C",
                }
                for item in normalized_actions(normalized)
            ]
        except GovernedAutomationContractError as exc:
            raise TaskAutomationDependencyError(str(exc)) from exc
        return {
            "phase": PHASE_LABEL,
            "rule_id": rule["id"],
            "rule_key": rule.get("rule_key") or rule.get("rule_code"),
            "rule_version": rule.get("version") or 1,
            "matched": matched,
            "evaluation_trace": trace,
            "planned_actions": actions if matched else [],
            "writes_performed": 0,
            "dry_run": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def process_timeline_events(
        self,
        payload: OperationalAutomationProcessRequest | dict[str, Any],
        user: dict,
        *,
        agency_id: str,
    ) -> dict[str, Any]:
        data = self._payload(payload)
        stale_lock_recovery = await self.recover_stale_execution_locks(
            agency_id, user
        )
        limit = min(max(int(data.get("batch_limit") or 25), 1), MAX_PROCESS_BATCH)
        requested_ids = list(dict.fromkeys(data.get("timeline_entry_ids") or []))[:limit]
        if requested_ids:
            candidates = []
            for entry_id in requested_ids:
                entry = await self.db.collection("operational_timelines").find_one(
                    {"agency_id": agency_id, "id": entry_id}
                )
                if not entry:
                    raise TaskAutomationDependencyError(
                        "Timeline processing selection contains an unknown or "
                        "cross-Agency entry."
                    )
                candidates.append(entry)
        else:
            candidates = await self.db.collection(
                "operational_timelines"
            ).find_many(
                {"agency_id": agency_id},
                sort=[("event_time", 1), ("id", 1)],
                limit=limit,
            )

        processed: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        for entry in candidates:
            event_type = canonical_event_type(entry.get("event_type"))
            if event_type not in CANONICAL_AUTOMATION_EVENTS:
                skipped.append(
                    {"timeline_entry_id": entry["id"], "reason": "event_not_allowlisted"}
                )
                continue
            if data.get("dry_run"):
                matching_rules = await self.list_rules(
                    agency_id=agency_id,
                    include_defaults=False,
                    trigger_event=event_type,
                    status="active",
                    enabled=True,
                )
                processed.append(
                    {
                        "timeline_entry_id": entry["id"],
                        "dry_run": True,
                        "matching_rule_ids": [
                            rule["id"] for rule in matching_rules if rule.get("published_at")
                        ],
                    }
                )
                continue
            result = await self.run_automation(
                {
                    "agency_id": agency_id,
                    "trigger_event": event_type,
                    "source_entity_type": entry.get("entity_type") or "source",
                    "source_entity_id": entry.get("entity_id") or entry["id"],
                    "source_timeline_entry_id": entry["id"],
                    "event_snapshot_json": entry.get("details") or {},
                    "recursion_depth": int(
                        (entry.get("details") or {}).get("recursion_depth") or 0
                    ),
                    "chained_action_count": int(
                        (entry.get("details") or {}).get("chained_action_count") or 0
                    ),
                },
                user,
                agency_id=agency_id,
            )
            processed.append(
                {
                    "timeline_entry_id": entry["id"],
                    "run_id": result["run"]["id"],
                    "idempotent_reused": result.get("idempotent_reused", False),
                }
            )
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "batch_limit": limit,
            "processed_count": len(processed),
            "skipped_count": len(skipped),
            "processed": processed,
            "skipped": skipped,
            "stale_lock_recovery": stale_lock_recovery,
            "persistent_scheduler_enabled": False,
            "bounded_manual_processing_enabled": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def recover_stale_execution_locks(
        self, agency_id: str, user: dict
    ) -> dict[str, Any]:
        processing = await self.db.collection(
            OPERATIONAL_TASK_AUTOMATION_RUNS_COLLECTION
        ).find_many(
            {"agency_id": agency_id, "status": "processing"},
            sort=[("locked_until", 1), ("id", 1)],
            limit=MAX_PROCESS_BATCH,
        )
        now = self._now()
        recovered: list[str] = []
        for run in processing:
            locked_until = self._parse_dt(run.get("locked_until"))
            if not locked_until or locked_until > now:
                continue
            updated = await self.db.collection(
                OPERATIONAL_TASK_AUTOMATION_RUNS_COLLECTION
            ).update_one(
                {
                    "id": run["id"],
                    "lock_token": run.get("lock_token"),
                    "status": "processing",
                },
                {
                    "status": "manual_review",
                    "failure_reason": (
                        "The bounded execution lock expired before completion."
                    ),
                    "lock_token": None,
                    "locked_until": None,
                    "updated_by": user.get("id"),
                },
            )
            if updated:
                recovered.append(updated["id"])
        return {
            "recovered_count": len(recovered),
            "recovered_run_ids": recovered,
            "batch_limit": MAX_PROCESS_BATCH,
            "recovery_action": "manual_review",
        }

    async def process_reminders_and_escalations(
        self,
        payload: OperationalReminderProcessRequest | dict[str, Any],
        user: dict,
        *,
        agency_id: str,
    ) -> dict[str, Any]:
        data = self._payload(payload)
        limit = min(max(int(data.get("batch_limit") or 50), 1), MAX_PROCESS_BATCH)
        monitor = await OperationalSlaDeadlineService(self.db).monitor_deadlines(
            agency_id, user
        )
        deadlines = await self.db.collection(
            "operational_deadlines"
        ).find_many(
            {"agency_id": agency_id},
            sort=[("due_at", 1), ("id", 1)],
            limit=limit,
        )
        projected: list[dict[str, Any]] = []
        deduplicated: list[str] = []
        escalated_work_item_ids: list[str] = []
        now = self._now()
        queue_service = AgentWorkQueueService(self.db)
        for deadline in deadlines[:limit]:
            if deadline.get("status") in {
                "paused",
                "completed",
                "waived",
                "archived",
            }:
                continue
            due_at = self._parse_dt(deadline.get("due_at"))
            if not due_at:
                continue
            remaining_seconds = (due_at - now).total_seconds()
            if remaining_seconds <= 0:
                level = "critical"
                event_type = "deadline_reached"
            elif remaining_seconds <= 60 * 60:
                level = "urgent"
                event_type = "reminder"
            elif remaining_seconds <= 24 * 60 * 60:
                level = "attention"
                event_type = "reminder"
            else:
                continue
            idempotency_key = (
                f"deadline-projection:{deadline['id']}:"
                f"{deadline.get('due_at')}:{level}"
            )
            existing = await self.db.collection(
                "operational_timelines"
            ).find_one(
                {
                    "agency_id": agency_id,
                    "idempotency_key": idempotency_key,
                }
            )
            if existing:
                deduplicated.append(deadline["id"])
                continue
            timeline = await OperationalCollaborationService(
                self.db
            ).record_business_event(
                agency_id=agency_id,
                entity_type=deadline.get("source_entity_type") or "deadline",
                entity_id=deadline.get("source_entity_id") or deadline["id"],
                event_type=event_type,
                event_subtype=f"deadline_{level}",
                summary=(
                    f"{self._label(deadline.get('deadline_type'))} is "
                    f"{'overdue' if level == 'critical' else 'approaching'}."
                ),
                actor={
                    **user,
                    "actor_type": "agency",
                    "identity_id": user.get("identity_id") or user.get("id"),
                },
                visibility="internal",
                details={
                    "operational_deadline_id": deadline["id"],
                    "work_item_id": deadline.get("work_item_id"),
                    "escalation_level": level,
                    "policy_code": deadline.get("policy_code"),
                    "policy_version": deadline.get("policy_version") or 1,
                    "due_at": deadline.get("due_at"),
                    "external_delivery": False,
                    "projection_only": True,
                },
                idempotency_key=idempotency_key,
                event_source="governed_automation",
                source_collection="operational_deadlines",
                source_record_id=deadline["id"],
            )
            projected.append(
                {
                    "deadline_id": deadline["id"],
                    "timeline_entry_id": timeline["id"],
                    "level": level,
                }
            )
            if deadline.get("work_item_id") and level in {"urgent", "critical"}:
                try:
                    result = await queue_service.apply_action(
                        deadline["work_item_id"],
                        "escalate",
                        {
                            "reason": (
                                f"Deadline {deadline.get('deadline_reference')} "
                                f"reached {level} escalation under policy "
                                f"{deadline.get('policy_code')} version "
                                f"{deadline.get('policy_version') or 1}."
                            ),
                            "metadata": {
                                "deadline_id": deadline["id"],
                                "rule_version": deadline.get("policy_version") or 1,
                            },
                        },
                        user,
                        agency_id=agency_id,
                    )
                    escalated_work_item_ids.append(result["work_item"]["id"])
                except AgentWorkQueueError as exc:
                    projected[-1]["escalation_warning"] = str(exc)[:300]
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "bounded_record_limit": limit,
            "deadline_monitor": monitor,
            "projection_count": len(projected),
            "deduplicated_count": len(deduplicated),
            "projections": projected,
            "escalated_work_item_ids": sorted(set(escalated_work_item_ids)),
            "external_delivery": False,
            "persistent_scheduler_enabled": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def list_approvals(
        self,
        agency_id: str,
        *,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {
            "agency_id": agency_id,
            "work_item_type": "approval_request",
        }
        if status:
            filters["approval_status"] = self._norm(status)
        approvals = await self.db.collection("operational_work_items").find_many(
            filters
        )
        approvals.sort(
            key=lambda item: (
                self._sort_text(item.get("approval_requested_at")),
                self._sort_text(item.get("id")),
            ),
            reverse=True,
        )
        return approvals

    async def create_approval(
        self,
        payload: OperationalApprovalRequestCreate | dict[str, Any],
        user: dict,
        agency_id: str,
    ) -> dict[str, Any]:
        data = self._payload(payload)
        required = [
            "approval_type",
            "title",
            "source_entity_type",
            "source_entity_id",
            "required_permission",
        ]
        missing = [field for field in required if not data.get(field)]
        if missing:
            raise TaskAutomationDependencyError(
                f"Approval request is missing: {', '.join(missing)}."
            )
        source_timeline_id = data.get("source_timeline_entry_id")
        if source_timeline_id:
            source = await self.db.collection("operational_timelines").find_one(
                {"agency_id": agency_id, "id": source_timeline_id}
            )
            if not source:
                raise TaskAutomationDependencyError(
                    "Approval source timeline entry was not found in this Agency."
                )
        result = await AgentWorkQueueService(self.db).generate_work_item(
            {
                "agency_id": agency_id,
                "work_item_type": "approval_request",
                "source_entity_type": self._norm(data["source_entity_type"]),
                "source_entity_id": data["source_entity_id"],
                "primary_entity_type": self._norm(data["source_entity_type"]),
                "primary_entity_id": data["source_entity_id"],
                "entity_references": [
                    {
                        "entity_type": self._norm(data["source_entity_type"]),
                        "entity_id": data["source_entity_id"],
                    }
                ],
                "source_timeline_entry_id": source_timeline_id,
                "timeline_entry_id": source_timeline_id,
                "title": data["title"],
                "description": data.get("summary"),
                "summary": data.get("summary"),
                "status": "approval_required",
                "priority": "high",
                "severity": "high",
                "queue_code": "waiting_approval",
                "queue_key": "waiting_approval",
                "assigned_user_id": data.get("assigned_approver_id"),
                "blocker_status": "waiting_approval",
                "approval_required": True,
                "approval_type": self._norm(data["approval_type"]),
                "approval_status": "assigned"
                if data.get("assigned_approver_id")
                else "requested",
                "approval_required_permission": data["required_permission"],
                "approval_requested_by": user.get("id"),
                "approval_requested_at": self._now(),
                "approval_evidence_snapshot": bounded_safe_snapshot(
                    data.get("evidence_snapshot") or {}
                ),
                "execution_safety_class": "C",
                "external_action_required": True,
                "human_confirmation_required": True,
                "source_fingerprint": (
                    f"{agency_id}::approval::{source_timeline_id or 'manual'}::"
                    f"{self._norm(data['approval_type'])}::{data['source_entity_id']}"
                ),
                "generation_reason": "governed_class_c_approval_request",
                "source_snapshot_json": {
                    "source_timeline_entry_id": source_timeline_id,
                    "underlying_action_executed": False,
                },
            },
            user,
            agency_id=agency_id,
        )
        approval = result["work_item"]
        await self._timeline(
            agency_id=agency_id,
            entity_type=data["source_entity_type"],
            entity_id=data["source_entity_id"],
            event_type="approval.requested",
            summary=f"Internal approval requested: {data['title']}.",
            actor=user,
            idempotency_key=f"approval-requested:{approval['id']}",
            details={
                "approval_work_item_id": approval["id"],
                "approval_type": approval.get("approval_type"),
                "required_permission": approval.get("approval_required_permission"),
                "underlying_action_executed": False,
            },
        )
        return {
            "phase": PHASE_LABEL,
            "approval": approval,
            "idempotent_reused": result.get("idempotent_reused", False),
            "underlying_action_executed": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def decide_approval(
        self,
        approval_id: str,
        payload: OperationalApprovalDecisionRequest | dict[str, Any],
        user: dict,
        agency_id: str,
    ) -> dict[str, Any]:
        data = self._payload(payload)
        decision = self._norm(data.get("decision"))
        if decision not in {"approved", "rejected", "cancelled"}:
            raise TaskAutomationDependencyError(
                "Approval decision must be approved, rejected, or cancelled."
            )
        approval = await self._require_work_item(approval_id, agency_id)
        if approval.get("work_item_type") != "approval_request":
            raise TaskAutomationDependencyError(
                "The selected work item is not an approval request."
            )
        if approval.get("approval_status") in {
            "approved",
            "rejected",
            "cancelled",
            "expired",
        }:
            if approval.get("approval_status") == decision:
                return {
                    "phase": PHASE_LABEL,
                    "approval": approval,
                    "idempotent_reused": True,
                    "underlying_action_executed": False,
                    "metadata_only": True,
                    **self.safety_flags(),
                }
            raise TaskAutomationDependencyError(
                "Approval decision is immutable once recorded."
            )
        if approval.get("approval_requested_by") == user.get("id"):
            raise TaskAutomationDependencyError(
                "Approval requester and decision maker must be different users."
            )
        membership = await self.db.collection("agency_staff_memberships").find_one(
            {
                "agency_id": agency_id,
                "user_id": user.get("id"),
                "status": "active",
            }
        )
        if not membership:
            raise TaskAutomationDependencyError(
                "Active Agency membership is required to decide an approval."
            )
        required_permission = approval.get("approval_required_permission")
        permissions = agency_permissions(membership.get("agency_role"))
        if required_permission and required_permission not in permissions:
            raise TaskAutomationDependencyError(
                "The approver does not hold the required Agency permission."
            )
        expected_version = data.get("expected_version")
        self._check_expected_version(approval, expected_version)
        try:
            updated = await AgentWorkQueueService(
                self.db
            ).record_approval_decision(
                approval["id"],
                agency_id=agency_id,
                decision=decision,
                reason=data["reason"],
                evidence_snapshot=data.get("evidence_snapshot") or {},
                user=user,
                expected_version=expected_version,
            )
        except AgentWorkQueueError as exc:
            raise TaskAutomationDependencyError(str(exc)) from exc
        await self._timeline(
            agency_id=agency_id,
            entity_type=approval["source_entity_type"],
            entity_id=approval["source_entity_id"],
            event_type="approval.completed",
            summary=f"Internal approval was {decision}.",
            actor=user,
            idempotency_key=f"approval-decision:{approval['id']}:{decision}",
            details={
                "approval_work_item_id": approval["id"],
                "decision": decision,
                "underlying_action_executed": False,
            },
        )
        return {
            "phase": PHASE_LABEL,
            "approval": updated,
            "idempotent_reused": False,
            "underlying_action_executed": False,
            "canonical_execution_service_still_required": decision == "approved",
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def operational_metrics(self, agency_id: str) -> dict[str, Any]:
        work_items = await self.db.collection("operational_work_items").find_many(
            {"agency_id": agency_id},
            sort=[("created_at", 1), ("id", 1)],
            limit=500,
        )
        runs = await self.db.collection(
            OPERATIONAL_TASK_AUTOMATION_RUNS_COLLECTION
        ).find_many(
            {"agency_id": agency_id},
            sort=[("created_at", 1), ("id", 1)],
            limit=500,
        )
        dependencies = await self.db.collection(
            OPERATIONAL_TASK_DEPENDENCIES_COLLECTION
        ).find_many(
            {"agency_id": agency_id},
            sort=[("created_at", 1), ("id", 1)],
            limit=500,
        )
        completion_seconds: list[float] = []
        approval_seconds: list[float] = []
        for item in work_items:
            created = self._parse_dt(item.get("created_at"))
            completed = self._parse_dt(item.get("completed_at"))
            if created and completed:
                completion_seconds.append(max(0, (completed - created).total_seconds()))
            requested = self._parse_dt(item.get("approval_requested_at"))
            decided = self._parse_dt(item.get("approval_decided_at"))
            if requested and decided:
                approval_seconds.append(max(0, (decided - requested).total_seconds()))
        return {
            "bounded_record_limit": 500,
            "open_work_count": len(
                [
                    item
                    for item in work_items
                    if item.get("status") not in {"completed", "cancelled"}
                ]
            ),
            "unassigned_work_count": len(
                [
                    item
                    for item in work_items
                    if not item.get("assigned_user_id")
                    and item.get("status") not in {"completed", "cancelled"}
                ]
            ),
            "blocked_work_count": len(
                [item for item in work_items if item.get("status") == "blocked"]
            ),
            "reopened_work_count": len(
                [item for item in work_items if item.get("reopened_at")]
            ),
            "average_completion_minutes": round(
                sum(completion_seconds) / len(completion_seconds) / 60, 2
            )
            if completion_seconds
            else None,
            "average_approval_turnaround_minutes": round(
                sum(approval_seconds) / len(approval_seconds) / 60, 2
            )
            if approval_seconds
            else None,
            "automation_success_count": len(
                [run for run in runs if run.get("status") == "completed"]
            ),
            "automation_failure_count": len(
                [run for run in runs if run.get("status") == "failed"]
            ),
            "pending_dependency_count": len(
                [
                    item
                    for item in dependencies
                    if item.get("status") in {"pending", "blocked"}
                ]
            ),
            "personal_ranking_disabled": True,
            "predictive_ai_disabled": True,
            "supplier_cost_margin_metrics_excluded": True,
        }

    async def migration_analysis(
        self, *, maximum_records_per_collection: int = 5000
    ) -> dict[str, Any]:
        limit = min(max(int(maximum_records_per_collection), 1), 10000)
        collections = {
            name: await self.db.collection(name).find_many(
                sort=[("id", 1)],
                limit=limit,
            )
            for name in (
                "request_tasks",
                "operational_work_items",
                "operational_workflow_instances",
                "operational_deadlines",
                "operational_task_dependencies",
                "operational_notification_projections",
                "operational_task_automation_rules",
                "operational_task_automation_runs",
                "operational_queue_definitions",
                "agency_staff_memberships",
                "operational_timelines",
            )
        }
        issues: list[dict[str, Any]] = []

        def add(
            category: str,
            record: dict[str, Any],
            *,
            domain: str,
            reason: str,
            candidate: dict[str, Any] | None = None,
            ambiguous: bool = False,
        ) -> None:
            issues.append(
                {
                    "category": category,
                    "agency_id": record.get("agency_id") or "missing",
                    "domain": domain,
                    "record_id": record.get("id"),
                    "reason": reason,
                    "candidate_mapping": candidate,
                    "manual_review_required": ambiguous,
                }
            )

        active_statuses = {
            "open",
            "assigned",
            "accepted",
            "in_progress",
            "waiting",
            "blocked",
            "approval_required",
            "reopened",
            "overdue",
        }
        canonical_items = collections["operational_work_items"]
        canonical_by_id = {
            (item.get("agency_id"), item.get("id")): item
            for item in canonical_items
        }
        active_groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
        membership_keys = {
            (item.get("agency_id"), item.get("user_id"))
            for item in collections["agency_staff_memberships"]
            if item.get("status") == "active"
        }
        for item in canonical_items:
            if not item.get("agency_id"):
                add(
                    "task_missing_agency",
                    item,
                    domain="work_item",
                    reason="Canonical work item has no Agency owner.",
                    ambiguous=True,
                )
            if item.get("status") not in WORK_ITEM_STATUSES:
                add(
                    "invalid_task_status",
                    item,
                    domain="work_item",
                    reason=f"Unknown status {item.get('status')}.",
                    ambiguous=True,
                )
            if not (
                item.get("source_timeline_entry_id")
                or (
                    item.get("source_entity_type")
                    and item.get("source_entity_id")
                )
            ):
                add(
                    "task_missing_entity_lineage",
                    item,
                    domain="work_item",
                    reason="No timeline or source-entity lineage is recorded.",
                    ambiguous=True,
                )
            assignee = item.get("assigned_user_id")
            if assignee and (item.get("agency_id"), assignee) not in membership_keys:
                add(
                    "task_assigned_to_inactive_user",
                    item,
                    domain="assignment",
                    reason="Assignee does not have an active Agency membership.",
                    candidate={"queue_code": "unassigned"},
                )
            due_at = self._parse_dt(item.get("due_at"))
            if item.get("due_at") and not due_at:
                add(
                    "invalid_task_deadline",
                    item,
                    domain="deadline",
                    reason="Work-item due_at cannot be parsed.",
                    ambiguous=True,
                )
            if (
                due_at
                and due_at < self._now()
                and item.get("status") in active_statuses
                and item.get("sla_status") not in {"overdue", "breached"}
            ):
                add(
                    "overdue_task_without_evidence",
                    item,
                    domain="deadline",
                    reason="Past-due work lacks overdue or breach evidence.",
                    candidate={"sla_status": "overdue"},
                )
            if (
                item.get("status") == "completed"
                and not item.get("completion_evidence")
            ):
                add(
                    "completed_work_without_evidence",
                    item,
                    domain="work_item",
                    reason="Completed work lacks bounded completion evidence.",
                    ambiguous=True,
                )
            if (
                item.get("work_item_type") == "approval_request"
                and not (
                    item.get("source_timeline_entry_id")
                    or item.get("source_entity_id")
                )
            ):
                add(
                    "approval_without_source_work",
                    item,
                    domain="approval",
                    reason="Approval has no source timeline or entity linkage.",
                    ambiguous=True,
                )
            if item.get("work_item_type") not in WORK_ITEM_TYPES:
                add(
                    "legacy_task_type",
                    item,
                    domain="work_item",
                    reason=f"Task type {item.get('work_item_type')} is not canonical.",
                    candidate={"work_item_type": "manual"},
                    ambiguous=True,
                )
            if item.get("status") in active_statuses:
                key = (
                    item.get("agency_id"),
                    item.get("work_item_type"),
                    item.get("source_entity_type"),
                    item.get("source_entity_id"),
                    item.get("source_automation_rule_id"),
                )
                active_groups.setdefault(key, []).append(item)
        for grouped in active_groups.values():
            if len(grouped) > 1:
                for item in sorted(grouped, key=lambda value: str(value.get("id"))):
                    add(
                        "duplicate_active_task",
                        item,
                        domain="work_item",
                        reason="Multiple active canonical work items share one source and type.",
                        ambiguous=True,
                    )

        for legacy in collections["request_tasks"]:
            candidate = next(
                (
                    item
                    for item in canonical_items
                    if item.get("agency_id") == legacy.get("agency_id")
                    and (
                        item.get("request_task_id") == legacy.get("id")
                        or item.get("source_entity_id") == legacy.get("id")
                    )
                ),
                None,
            )
            add(
                "legacy_request_task",
                legacy,
                domain="compatibility",
                reason="Legacy request task remains historical compatibility data.",
                candidate={"operational_work_item_id": candidate.get("id")}
                if candidate
                else None,
                ambiguous=not bool(candidate),
            )

        for workflow in collections["operational_workflow_instances"]:
            linked = [
                item
                for item in canonical_items
                if item.get("agency_id") == workflow.get("agency_id")
                and item.get("workflow_instance_id") == workflow.get("id")
            ]
            if not linked:
                add(
                    "workflow_without_canonical_work_item",
                    workflow,
                    domain="workflow",
                    reason="Workflow instance has no canonical work-item projection.",
                    candidate={"source": "workflow_instance"},
                )

        for deadline in collections["operational_deadlines"]:
            if deadline.get("work_item_id") and (
                deadline.get("agency_id"),
                deadline.get("work_item_id"),
            ) not in canonical_by_id:
                add(
                    "orphan_deadline",
                    deadline,
                    domain="deadline",
                    reason="Deadline references an absent canonical work item.",
                    ambiguous=True,
                )
            if deadline.get("source_entity_id") and not deadline.get(
                "source_entity_type"
            ):
                add(
                    "orphan_deadline",
                    deadline,
                    domain="deadline",
                    reason="Deadline source entity type is missing.",
                    ambiguous=True,
                )

        dependencies = collections["operational_task_dependencies"]
        adjacency: dict[tuple[str, str], set[str]] = {}
        for dependency in dependencies:
            predecessor = canonical_by_id.get(
                (dependency.get("agency_id"), dependency.get("predecessor_task_id"))
            )
            successor = canonical_by_id.get(
                (dependency.get("agency_id"), dependency.get("successor_task_id"))
            )
            if not predecessor or not successor:
                add(
                    "cross_agency_or_orphan_dependency",
                    dependency,
                    domain="dependency",
                    reason="Dependency source or target is absent from the same Agency.",
                    ambiguous=True,
                )
                continue
            key = (dependency["agency_id"], dependency["predecessor_task_id"])
            adjacency.setdefault(key, set()).add(dependency["successor_task_id"])

        for agency_id, start in sorted(adjacency):
            stack: list[tuple[str, tuple[str, ...]]] = [(start, (start,))]
            while stack:
                node, path = stack.pop()
                for target in sorted(adjacency.get((agency_id, node), set())):
                    if target in path:
                        add(
                            "dependency_cycle",
                            {"id": f"{agency_id}:{start}", "agency_id": agency_id},
                            domain="dependency",
                            reason=" -> ".join((*path, target)),
                            ambiguous=True,
                        )
                        stack = []
                        break
                    if len(path) < 100:
                        stack.append((target, (*path, target)))

        projection_groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
        for projection in collections["operational_notification_projections"]:
            key = (
                projection.get("agency_id"),
                projection.get("projection_key"),
            )
            projection_groups.setdefault(key, []).append(projection)
        for grouped in projection_groups.values():
            if grouped[0].get("projection_key") and len(grouped) > 1:
                for projection in grouped:
                    add(
                        "duplicate_notification_projection",
                        projection,
                        domain="notification",
                        reason="Projection key is duplicated.",
                        ambiguous=True,
                    )

        active_rule_groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
        for rule in collections["operational_task_automation_rules"]:
            if rule.get("status") == "active" and rule.get("enabled"):
                key = (
                    rule.get("agency_id"),
                    rule.get("rule_key") or rule.get("rule_code"),
                )
                active_rule_groups.setdefault(key, []).append(rule)
        for grouped in active_rule_groups.values():
            if len(grouped) > 1:
                for rule in grouped:
                    add(
                        "conflicting_active_rule_key",
                        rule,
                        domain="automation_rule",
                        reason="More than one active rule version shares an effective scope.",
                        ambiguous=True,
                    )

        valid_assignment_strategies = {
            "manual",
            "agent_owned",
            "team_manual",
            "fixed_user",
            "fixed_team",
            "least_open_eligible",
            "round_robin",
            "retain_current_owner",
            "parent_entity_owner",
            "manual_assignment_required",
        }
        for definition in collections["operational_queue_definitions"]:
            if self._norm(
                definition.get("assignment_strategy") or "manual"
            ) not in valid_assignment_strategies:
                add(
                    "legacy_assignment_rule",
                    definition,
                    domain="assignment",
                    reason="Queue assignment strategy is not governed.",
                    candidate={"assignment_strategy": "manual_assignment_required"},
                    ambiguous=True,
                )

        timeline_keys = {
            (item.get("agency_id"), item.get("id"))
            for item in collections["operational_timelines"]
        }
        for run in collections["operational_task_automation_runs"]:
            if (
                run.get("agency_id"),
                run.get("source_timeline_entry_id"),
            ) not in timeline_keys:
                add(
                    "automation_run_without_source_timeline",
                    run,
                    domain="automation_run",
                    reason="Automation run has no exact canonical source timeline entry.",
                    ambiguous=True,
                )

        by_agency: dict[str, int] = {}
        by_domain: dict[str, int] = {}
        by_category: dict[str, int] = {}
        for issue in issues:
            by_agency[issue["agency_id"]] = by_agency.get(issue["agency_id"], 0) + 1
            by_domain[issue["domain"]] = by_domain.get(issue["domain"], 0) + 1
            by_category[issue["category"]] = (
                by_category.get(issue["category"], 0) + 1
            )
        return {
            "analysis": "governed_automation_orchestration_migration",
            "maximum_records_per_collection": limit,
            "records_inspected": {
                name: len(records) for name, records in collections.items()
            },
            "counts_by_agency": dict(sorted(by_agency.items())),
            "counts_by_domain": dict(sorted(by_domain.items())),
            "counts_by_category": dict(sorted(by_category.items())),
            "deterministic_candidate_mappings": [
                issue
                for issue in issues
                if issue.get("candidate_mapping")
                and not issue.get("manual_review_required")
            ],
            "ambiguous_cases": [
                issue for issue in issues if issue.get("manual_review_required")
            ],
            "manual_review_cases": len(
                [issue for issue in issues if issue.get("manual_review_required")]
            ),
            "issues": sorted(
                issues,
                key=lambda issue: (
                    issue["agency_id"],
                    issue["domain"],
                    issue["category"],
                    str(issue.get("record_id") or ""),
                ),
            ),
            "writes_performed": 0,
            "write_mode_available": False,
            "production_data_accessed": False,
        }

    def summarize(self, runs: list[dict[str, Any]], dependencies: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "run_count": len(runs),
            "dependency_count": len(dependencies),
            "blocked_dependency_count": len([item for item in dependencies if item.get("status") in {"pending", "blocked"}]),
            "satisfied_dependency_count": len([item for item in dependencies if item.get("status") == "satisfied"]),
            "failed_run_count": len([item for item in runs if item.get("status") == "failed"]),
            "created_task_count": sum(len(item.get("tasks_created") or []) for item in runs),
            "skipped_task_count": sum(len(item.get("tasks_skipped") or []) for item in runs),
            "run_status_counts": self._counts(runs, "status", TASK_AUTOMATION_RUN_STATUSES),
            "dependency_status_counts": self._counts(dependencies, "status", TASK_DEPENDENCY_STATUSES),
        }

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "task_automation_dependency_orchestration_foundation": True,
            "existing_tasks_preserved": True,
            "operational_work_item_is_sole_task_owner": True,
            "legacy_request_tasks_projection_only": True,
            "safe_automatic_task_creation_enabled": True,
            "idempotent_task_generation_enabled": True,
            "dependency_blocking_enabled": True,
            "dependency_unblocking_enabled": True,
            "work_queue_integration_enabled": True,
            "sla_due_date_integration_enabled": True,
            "workflow_event_integration_enabled": True,
            "audit_run_records_enabled": True,
            "manual_retry_enabled": True,
            "arbitrary_code_execution_disabled": True,
            "provider_integrations_disabled": True,
            "external_api_calls_disabled": True,
            "ai_disabled": True,
            "background_workers_disabled": True,
            "schedulers_disabled": True,
            "bounded_manual_processing_enabled": True,
            "unbounded_automation_disabled": True,
            "agency_isolation_enforced": True,
            "class_c_execution_disabled": True,
            "class_d_actions_rejected": True,
            "default_automation_pack_disabled": True,
            "human_authority_final": True,
        }

    def action_catalogue(self) -> list[dict[str, Any]]:
        return [
            {
                "action_type": action_type,
                "safety_class": safety_class,
                "automatic_execution": safety_class in {"A", "B"},
                "creates_approval_only": safety_class == "C",
                "external_execution": False,
            }
            for action_type, safety_class in sorted(ACTION_SAFETY_CLASS.items())
        ]

    async def _execute_governed_action(
        self,
        *,
        data: dict[str, Any],
        source_timeline: dict[str, Any],
        rule: dict[str, Any],
        action: dict[str, Any],
        action_index: int,
        execution_id: str,
        user: dict,
        templates_by_code: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        action_type = action["action_type"]
        safety_class = action_safety_class(action_type)
        parameters = action.get("parameters") or {}
        if safety_class == "D":
            raise TaskAutomationDependencyError(
                f"Class D action is prohibited: {action_type}."
            )
        if safety_class == "C":
            approval = await self.create_approval(
                {
                    "approval_type": action_type,
                    "title": f"Approval required: {action_type.replace('_', ' ')}",
                    "summary": (
                        "Automation identified a Class C action. No business action "
                        "has been executed."
                    ),
                    "source_entity_type": data["source_entity_type"],
                    "source_entity_id": data["source_entity_id"],
                    "source_timeline_entry_id": source_timeline["id"],
                    "required_permission": self._approval_permission(action_type),
                    "evidence_snapshot": {
                        "rule_id": rule["id"],
                        "rule_version": rule.get("version") or 1,
                        "automation_execution_id": execution_id,
                        "action_type": action_type,
                    },
                },
                user,
                data["agency_id"],
            )
            return {
                "approval_id": approval["approval"]["id"],
                "work_item": approval["approval"],
                "trace": {
                    "result": "approval_required",
                    "underlying_action_executed": False,
                },
            }

        if action_type in {
            "create_work_item",
            "request_document",
            "request_missing_information",
            "create_supplier_follow_up",
            "create_client_follow_up",
            "create_accounting_review",
            "create_policy_review",
            "create_manual_booking_review",
        }:
            template_code = parameters.get("template_code") or rule.get(
                "generated_template_code"
            )
            template = templates_by_code.get(template_code) if template_code else None
            result = await self._create_canonical_work_item(
                data=data,
                source_timeline=source_timeline,
                rule=rule,
                action_type=action_type,
                action_index=action_index,
                execution_id=execution_id,
                parameters=parameters,
                template=template,
                user=user,
            )
            return {
                **result,
                "template_code": template_code,
                "trace": {
                    "result": "work_item_reused"
                    if result.get("idempotent_reused")
                    else "work_item_created",
                    "work_item_id": result["work_item"]["id"],
                },
            }

        if action_type == "create_approval_request":
            approval = await self.create_approval(
                {
                    "approval_type": parameters.get("approval_type") or "manual_review",
                    "title": parameters.get("title") or "Operational approval required",
                    "summary": parameters.get("summary"),
                    "source_entity_type": data["source_entity_type"],
                    "source_entity_id": data["source_entity_id"],
                    "source_timeline_entry_id": source_timeline["id"],
                    "required_permission": parameters.get("required_permission")
                    or "edit_tasks",
                    "evidence_snapshot": {
                        "rule_id": rule["id"],
                        "rule_version": rule.get("version") or 1,
                        "automation_execution_id": execution_id,
                    },
                },
                user,
                data["agency_id"],
            )
            return {
                "approval_id": approval["approval"]["id"],
                "work_item": approval["approval"],
                "trace": {
                    "result": "approval_request_created",
                    "underlying_action_executed": False,
                },
            }

        if action_type in {
            "create_internal_timeline_entry",
            "create_internal_note",
            "create_notification_projection",
        }:
            event = await self._timeline(
                agency_id=data["agency_id"],
                entity_type=data["source_entity_type"],
                entity_id=data["source_entity_id"],
                event_type=parameters.get("event_type")
                or (
                    "automation.notification_projected"
                    if action_type == "create_notification_projection"
                    else "automation.internal_note"
                ),
                summary=parameters.get("summary")
                or parameters.get("title")
                or "Governed automation recorded internal operational evidence.",
                actor=user,
                idempotency_key=(
                    f"automation-action:{source_timeline['id']}:{rule['id']}:"
                    f"{rule.get('version', 1)}:{action_index}"
                ),
                details={
                    "source_timeline_entry_id": source_timeline["id"],
                    "source_automation_rule_id": rule["id"],
                    "source_automation_execution_id": execution_id,
                    "recipient_user_id": parameters.get("recipient_user_id"),
                },
            )
            return {
                "timeline_entry_id": event["id"],
                "trace": {"result": "timeline_evidence_created"},
            }

        work_item_id = parameters.get("work_item_id")
        if not work_item_id:
            raise TaskAutomationDependencyError(
                f"Action {action_type} requires an existing canonical work_item_id."
            )
        queue_service = AgentWorkQueueService(self.db)
        if action_type in {"assign_work_item", "place_in_queue"}:
            result = await queue_service.apply_action(
                work_item_id,
                "assign" if action_type == "assign_work_item" else "place_in_queue",
                {
                    "to_user_id": parameters.get("to_user_id"),
                    "to_team_code": parameters.get("to_team_code"),
                    "queue_code": parameters.get("queue_code"),
                    "reason": "Governed automation rule action.",
                    "expected_version": parameters.get("expected_version"),
                    "metadata": {"source_automation_execution_id": execution_id},
                },
                user,
                agency_id=data["agency_id"],
            )
        elif action_type == "update_work_item_priority":
            result = await queue_service.update_work_item(
                work_item_id,
                {
                    "priority": parameters.get("priority") or "normal",
                    "expected_version": parameters.get("expected_version"),
                },
                user,
                agency_id=data["agency_id"],
            )
        elif action_type == "set_work_item_deadline":
            item = await queue_service.get_work_item(
                work_item_id, agency_id=data["agency_id"]
            )
            deadline_result = await OperationalSlaDeadlineService(
                self.db
            ).create_deadline(
                {
                    "agency_id": data["agency_id"],
                    "source_entity_type": item["source_entity_type"],
                    "source_entity_id": item["source_entity_id"],
                    "work_item_id": item["id"],
                    "timeline_entry_id": source_timeline["id"],
                    "deadline_type": parameters.get("deadline_type")
                    or "task_deadline",
                    "priority": item.get("priority") or "normal",
                    "due_at": parameters.get("due_at"),
                    "source_snapshot_json": {
                        "automation_rule_id": rule["id"],
                        "automation_rule_version": rule.get("version") or 1,
                    },
                },
                user,
                agency_id=data["agency_id"],
            )
            return {
                "trace": {
                    "result": "deadline_created",
                    "deadline_id": deadline_result["deadline"]["id"],
                }
            }
        elif action_type == "add_work_item_dependency":
            dependency = await self.create_dependency(
                {
                    "agency_id": data["agency_id"],
                    "predecessor_task_id": parameters.get("predecessor_task_id"),
                    "successor_task_id": work_item_id,
                    "dependency_type": parameters.get("dependency_type")
                    or "mandatory",
                    "source_entity_type": data["source_entity_type"],
                    "source_entity_id": data["source_entity_id"],
                    "automation_run_id": execution_id,
                },
                user,
                agency_id=data["agency_id"],
            )
            return {
                "trace": {
                    "result": "dependency_created",
                    "dependency_id": dependency["dependency"]["id"],
                }
            }
        else:
            action_map = {
                "escalate_work_item": "escalate",
                "reopen_work_item": "reopen",
                "close_work_item_when_conditions_met": "complete",
                "add_readiness_blocker": "block",
                "clear_resolved_readiness_blocker": "resolve_blocker",
            }
            mapped_action = action_map.get(action_type)
            if not mapped_action:
                raise TaskAutomationDependencyError(
                    f"Action {action_type} has no governed internal adapter."
                )
            result = await queue_service.apply_action(
                work_item_id,
                mapped_action,
                {
                    "reason": "Governed automation rule action.",
                    "expected_version": parameters.get("expected_version"),
                    "completion_evidence": parameters.get("completion_evidence") or {},
                    "metadata": {"source_automation_execution_id": execution_id},
                },
                user,
                agency_id=data["agency_id"],
            )
        return {
            "work_item": result.get("work_item"),
            "trace": {
                "result": "canonical_work_item_updated",
                "work_item_id": work_item_id,
            },
        }

    async def _create_canonical_work_item(
        self,
        *,
        data: dict[str, Any],
        source_timeline: dict[str, Any],
        rule: dict[str, Any],
        action_type: str,
        action_index: int,
        execution_id: str,
        parameters: dict[str, Any],
        template: dict[str, Any] | None,
        user: dict,
    ) -> dict[str, Any]:
        source_label = (
            (data.get("event_snapshot_json") or {}).get("source_label")
            or (data.get("event_snapshot_json") or {}).get("title")
            or data["source_entity_id"]
        )
        template = template or {
            "template_code": parameters.get("task_type") or action_type,
            "title_pattern": parameters.get("title")
            or action_type.replace("_", " ").title(),
            "description_pattern": parameters.get("description"),
            "default_priority": parameters.get("priority") or "normal",
        }
        task_type = parameters.get("task_type") or self._task_type_for_action(
            action_type, template.get("template_code")
        )
        contract = task_type_contract(task_type)
        due_at = parameters.get("due_at") or self._due_at(template)
        title = self._render_pattern(
            template.get("title_pattern") or task_type,
            data,
            template,
            source_label=source_label,
        )
        description = self._render_pattern(
            template.get("description_pattern") or "",
            data,
            template,
            source_label=source_label,
        ) or None
        fingerprint = (
            f"{data['agency_id']}::{source_timeline['id']}::{rule['id']}::"
            f"{rule.get('version', 1)}::{action_index}"
        )
        result = await AgentWorkQueueService(self.db).generate_work_item(
            {
                "agency_id": data["agency_id"],
                "work_item_type": task_type,
                "source_entity_type": data["source_entity_type"],
                "source_entity_id": data["source_entity_id"],
                "primary_entity_type": data["source_entity_type"],
                "primary_entity_id": data["source_entity_id"],
                "entity_references": [
                    {
                        "entity_type": data["source_entity_type"],
                        "entity_id": data["source_entity_id"],
                    }
                ],
                "workflow_instance_id": (
                    data.get("event_snapshot_json") or {}
                ).get("workflow_instance_id"),
                "timeline_entry_id": source_timeline["id"],
                "source_timeline_entry_id": source_timeline["id"],
                "source_automation_rule_id": rule["id"],
                "source_automation_execution_id": execution_id,
                "title": title,
                "description": description,
                "summary": description,
                "priority": parameters.get("priority")
                or template.get("default_priority")
                or contract["default_priority"],
                "severity": parameters.get("severity") or "medium",
                "queue_code": parameters.get("queue_code") or "unassigned",
                "queue_key": parameters.get("queue_code") or "unassigned",
                "assigned_team_code": parameters.get("assigned_team_code")
                or template.get("assigned_team_strategy"),
                "assignment_explanation": (
                    "Created by governed rule; unresolved user assignment remains "
                    "in the canonical queue."
                ),
                "due_at": due_at,
                "blocker_status": "not_blocked",
                "approval_required": contract["human_confirmation_required"],
                "approval_status": "requested"
                if contract["human_confirmation_required"]
                else None,
                "approval_required_permission": contract["required_permission"],
                "execution_safety_class": action_safety_class(action_type),
                "external_action_required": contract[
                    "external_action_required"
                ],
                "human_confirmation_required": contract[
                    "human_confirmation_required"
                ],
                "source_fingerprint": fingerprint,
                "generation_reason": "governed_automation_rule",
                "source_snapshot_json": {
                    "source_timeline_entry_id": source_timeline["id"],
                    "source_automation_rule_id": rule["id"],
                    "source_automation_rule_version": rule.get("version") or 1,
                },
                "compatibility_mapping_json": {
                    "legacy_request_task_created": False,
                    "template_code": template.get("template_code"),
                },
            },
            user,
            agency_id=data["agency_id"],
        )
        return {
            "work_item": result["work_item"],
            "idempotent_reused": result.get("idempotent_reused", False),
        }

    async def _create_run_dependencies(self, data: dict[str, Any], run_id: str, tasks_by_template: dict[str, dict[str, Any]], user: dict) -> list[dict[str, Any]]:
        created: list[dict[str, Any]] = []
        templates = await self.list_templates(agency_id=data["agency_id"], include_defaults=True, trigger_event=data["trigger_event"])
        for template in templates:
            successor = tasks_by_template.get(template["template_code"])
            if not successor:
                continue
            for predecessor_code in template.get("dependency_template_codes") or []:
                predecessor = tasks_by_template.get(predecessor_code)
                if not predecessor:
                    continue
                existing = await self.db.collection(OPERATIONAL_TASK_DEPENDENCIES_COLLECTION).find_one(
                    {
                        "agency_id": data["agency_id"],
                        "predecessor_task_id": predecessor["id"],
                        "successor_task_id": successor["id"],
                    }
                )
                if existing:
                    created.append(existing)
                    continue
                dependency = OperationalTaskDependency(
                    agency_id=data["agency_id"],
                    predecessor_task_id=predecessor["id"],
                    successor_task_id=successor["id"],
                    predecessor_template_code=predecessor_code,
                    successor_template_code=template["template_code"],
                    dependency_type="finish_to_start",
                    status="pending",
                    blocked_reason="Successor task waits for predecessor completion metadata.",
                    automation_run_id=run_id,
                    source_entity_type=data["source_entity_type"],
                    source_entity_id=data["source_entity_id"],
                    created_by=user.get("id"),
                    updated_by=user.get("id"),
                )
                inserted = await self.db.collection(OPERATIONAL_TASK_DEPENDENCIES_COLLECTION).insert_one(dependency.model_dump(mode="json"))
                created.append(inserted)
        return created

    async def _record_workflow_event(self, data: dict[str, Any], run: dict[str, Any]) -> None:
        workflow_instance_id = (data.get("event_snapshot_json") or {}).get("workflow_instance_id")
        if not workflow_instance_id:
            return
        await self.db.collection("operational_workflow_events").insert_one(
            {
                "id": new_id(),
                "agency_id": data["agency_id"],
                "workflow_instance_id": workflow_instance_id,
                "event_type": "task_automation",
                "event_code": "task_automation_run_recorded",
                "event_status": run.get("status") or "recorded",
                "source_module": "task_automation_dependency_orchestration",
                "source_entity_type": "operational_task_automation_run",
                "source_entity_id": run["id"],
                "payload_json": {
                    "trigger_event": data.get("trigger_event"),
                    "source_entity_type": data.get("source_entity_type"),
                    "source_entity_id": data.get("source_entity_id"),
                    "tasks_created": run.get("tasks_created") or [],
                    "tasks_skipped": run.get("tasks_skipped") or [],
                    "dependencies_created": run.get("dependencies_created") or [],
                    "metadata_only": True,
                },
                "occurred_at": self._now(),
                "metadata": {"phase": PHASE_LABEL, "metadata_only": True},
                "metadata_only": True,
                "operational_workflow_orchestration_foundation": True,
                "immutable_history": True,
            }
        )

    async def _dependency_projection(self, dependency: dict[str, Any]) -> dict[str, Any]:
        projected = dict(dependency)
        projected["predecessor_task"] = await self.db.collection("operational_work_items").find_one({"agency_id": dependency["agency_id"], "id": dependency["predecessor_task_id"]})
        projected["successor_task"] = await self.db.collection("operational_work_items").find_one({"agency_id": dependency["agency_id"], "id": dependency["successor_task_id"]})
        projected.update(self.safety_flags())
        return projected

    def _default_template(self, template: dict[str, Any], agency_id: str | None = None) -> dict[str, Any]:
        return {
            "id": f"default-{template['template_code']}",
            "agency_id": agency_id,
            "scope": "agency" if agency_id else "platform",
            "status": "active",
            "metadata_only": True,
            "is_default": True,
            "task_automation_dependency_orchestration_foundation": True,
            **template,
        }

    def _default_rule(self, rule: dict[str, Any], agency_id: str | None = None) -> dict[str, Any]:
        return {
            "id": f"default-{rule['rule_code']}",
            "agency_id": agency_id,
            "scope": "agency" if agency_id else "platform",
            "metadata_only": True,
            "is_default": True,
            "task_automation_dependency_orchestration_foundation": True,
            **rule,
        }

    def _normalize_template(self, data: dict[str, Any], *, partial: bool = False) -> None:
        if not partial:
            for field in ["template_code", "title_pattern", "trigger_event"]:
                if not data.get(field):
                    raise TaskAutomationDependencyError(f"{field} is required for task template metadata.")
        for field in ["scope", "template_code", "default_priority", "assigned_role_strategy", "assigned_team_strategy", "required_capability", "status"]:
            if data.get(field):
                data[field] = self._norm(data[field])
        if data.get("trigger_event"):
            data["trigger_event"] = canonical_event_type(data["trigger_event"])
        if data.get("status") and data["status"] not in TASK_TEMPLATE_STATUSES:
            raise TaskAutomationDependencyError(f"Unsupported task template status metadata: {data['status']}.")
        if data.get("trigger_event") and data["trigger_event"] not in TASK_AUTOMATION_TRIGGER_EVENTS:
            raise TaskAutomationDependencyError(f"Unsupported task trigger metadata: {data['trigger_event']}.")

    def _normalize_rule(self, data: dict[str, Any], *, partial: bool = False) -> None:
        if not partial:
            for field in ["rule_code", "name", "deduplication_key_pattern"]:
                if not data.get(field):
                    raise TaskAutomationDependencyError(f"{field} is required for task automation rule metadata.")
        for field in ["scope", "rule_code", "rule_key", "generated_template_code", "status"]:
            if data.get(field):
                data[field] = self._norm(data[field])
        if data.get("trigger_event"):
            data["trigger_event"] = canonical_event_type(data["trigger_event"])
        if data.get("status") and data["status"] not in TASK_AUTOMATION_RULE_STATUSES:
            raise TaskAutomationDependencyError(f"Unsupported task automation rule status metadata: {data['status']}.")
        try:
            validate_rule_contract(data)
        except GovernedAutomationContractError as exc:
            raise TaskAutomationDependencyError(str(exc)) from exc

    def _normalize_dependency(self, data: dict[str, Any]) -> None:
        for field in ["agency_id", "predecessor_task_id", "successor_task_id"]:
            if not data.get(field):
                raise TaskAutomationDependencyError(f"{field} is required for task dependency metadata.")
        data.setdefault("dependency_type", "mandatory")
        data.setdefault("status", "pending")
        if data.get("dependency_type"):
            data["dependency_type"] = self._norm(data["dependency_type"])
        if data.get("status"):
            data["status"] = self._norm(data["status"])
        if data.get("dependency_type") not in TASK_DEPENDENCY_TYPES:
            raise TaskAutomationDependencyError(f"Unsupported dependency type metadata: {data.get('dependency_type')}.")
        if data.get("status") not in TASK_DEPENDENCY_STATUSES:
            raise TaskAutomationDependencyError(f"Unsupported dependency status metadata: {data.get('status')}.")

    def _validate_run_request(self, data: dict[str, Any]) -> None:
        for field in ["agency_id", "trigger_event", "source_entity_type", "source_entity_id"]:
            if not data.get(field):
                raise TaskAutomationDependencyError(f"{field} is required for task automation run metadata.")
        if canonical_event_type(data["trigger_event"]) not in TASK_AUTOMATION_TRIGGER_EVENTS:
            raise TaskAutomationDependencyError(f"Unsupported task automation trigger metadata: {data['trigger_event']}.")
        if int(data.get("recursion_depth") or 0) > MAX_RECURSION_DEPTH:
            raise TaskAutomationDependencyError(
                f"Automation recursion depth exceeds {MAX_RECURSION_DEPTH}."
            )
        if int(data.get("chained_action_count") or 0) > MAX_CHAINED_ACTIONS:
            raise TaskAutomationDependencyError(
                f"Automation chain length exceeds {MAX_CHAINED_ACTIONS}."
            )
        if data.get("dry_run"):
            raise TaskAutomationDependencyError(
                "Use the dedicated dry-run route; execution runs always record evidence."
            )

    def _due_at(self, template: dict[str, Any]) -> datetime | None:
        minutes = int(template.get("due_offset_minutes") or 0)
        hours = int(template.get("due_offset_hours") or 0)
        days = int(template.get("due_offset_days") or 0)
        if not any([minutes, hours, days]):
            return None
        return self._now() + timedelta(days=days, hours=hours, minutes=minutes)

    def _idempotency_key(self, data: dict[str, Any]) -> str:
        return (
            f"{data['agency_id']}:{data.get('source_timeline_entry_id')}:"
            f"{canonical_event_type(data['trigger_event'])}"
        )

    def _render_pattern(self, pattern: str, data: dict[str, Any], template: dict[str, Any], *, source_label: str | None = None) -> str:
        values = {
            "agency_id": data.get("agency_id", ""),
            "source_entity_type": data.get("source_entity_type", ""),
            "source_entity_id": data.get("source_entity_id", ""),
            "template_code": template.get("template_code", ""),
            "trigger_event": data.get("trigger_event", ""),
            "source_label": source_label or data.get("source_entity_id", ""),
        }
        rendered = pattern
        for key, value in values.items():
            rendered = rendered.replace("{" + key + "}", str(value))
        return rendered

    def _run_reference(self, trigger_event: str) -> str:
        return f"TASK-AUTO-{self._norm(trigger_event).upper().replace('_', '-')}-{new_id()[:8].upper()}"

    def _code(self, value: str) -> str:
        return f"{self._norm(value)[:48]}_{new_id()[:8]}"

    def _stable_code(self, value: str) -> str:
        return self._norm(value)[:64] or "automation_rule"

    async def _resolve_source_timeline(
        self, data: dict[str, Any], user: dict
    ) -> dict[str, Any]:
        source_timeline_id = data.get("source_timeline_entry_id")
        if source_timeline_id:
            record = await self.db.collection("operational_timelines").find_one(
                {"agency_id": data["agency_id"], "id": source_timeline_id}
            )
            if not record:
                raise TaskAutomationDependencyError(
                    "Automation source timeline entry was not found in this Agency."
                )
            return record
        event_key = (
            f"automation-source:{data['agency_id']}:{data['trigger_event']}:"
            f"{data['source_entity_type']}:{data['source_entity_id']}:"
            f"{data.get('idempotency_key') or 'canonical'}"
        )
        return await OperationalCollaborationService(self.db).record_business_event(
            agency_id=data["agency_id"],
            entity_type=data["source_entity_type"],
            entity_id=data["source_entity_id"],
            event_type=data["trigger_event"],
            summary=f"Canonical automation trigger: {data['trigger_event']}.",
            actor=user,
            visibility="internal",
            details=bounded_safe_snapshot(data.get("event_snapshot_json") or {}),
            idempotency_key=event_key,
            event_source="governed_automation_adapter",
            source_collection=data.get("metadata", {}).get("source_collection"),
            source_record_id=data["source_entity_id"],
        )

    def _evaluation_context(
        self, data: dict[str, Any], source_timeline: dict[str, Any]
    ) -> dict[str, Any]:
        snapshot = bounded_safe_snapshot(data.get("event_snapshot_json") or {})
        context: dict[str, Any] = {
            "event": {
                "event_type": canonical_event_type(source_timeline.get("event_type")),
                "event_subtype": source_timeline.get("event_subtype"),
                "event_time": source_timeline.get("event_time")
                or source_timeline.get("created_at"),
                "entity_type": source_timeline.get("entity_type"),
                "entity_id": source_timeline.get("entity_id"),
                "priority": source_timeline.get("event_priority"),
                "status": source_timeline.get("event_status"),
                "visibility": source_timeline.get("visibility"),
            },
            "source": {
                "entity_type": data["source_entity_type"],
                "entity_id": data["source_entity_id"],
                "source_type": data["source_entity_type"],
                "source_id": data["source_entity_id"],
            },
        }
        if isinstance(snapshot, dict):
            for root in [
                "request",
                "offer",
                "trip",
                "booking",
                "ticket",
                "emd",
                "invoice",
                "document",
                "communication",
                "work",
            ]:
                if isinstance(snapshot.get(root), dict):
                    context[root] = snapshot[root]
            source_root = data["source_entity_type"].split("_")[0]
            if source_root in {
                "request",
                "offer",
                "trip",
                "booking",
                "ticket",
                "emd",
                "invoice",
                "document",
                "communication",
                "work",
            }:
                context.setdefault(source_root, snapshot)
        return context

    async def _timeline(
        self,
        *,
        agency_id: str,
        entity_type: str,
        entity_id: str,
        event_type: str,
        summary: str,
        actor: dict[str, Any],
        idempotency_key: str,
        details: dict[str, Any],
    ) -> dict[str, Any]:
        return await OperationalCollaborationService(self.db).record_business_event(
            agency_id=agency_id,
            entity_type=self._norm(entity_type),
            entity_id=entity_id,
            event_type=event_type,
            summary=summary,
            actor=actor,
            visibility="internal",
            details=bounded_safe_snapshot(details),
            idempotency_key=idempotency_key,
            event_source="governed_automation",
        )

    async def _audit(
        self,
        *,
        agency_id: str | None,
        actor_user_id: str | None,
        event_type: str,
        entity_id: str,
        summary: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        record = AuditEvent(
            agency_id=agency_id,
            actor_user_id=actor_user_id,
            event_type=event_type,
            entity_type="operational_automation",
            entity_id=entity_id,
            summary=summary,
            metadata=bounded_safe_snapshot(metadata),
        )
        return await self.db.collection("audit_events").insert_one(
            record.model_dump(mode="json")
        )

    def _rule_scope_filter(
        self, agency_id: str | None, rule_key: str
    ) -> dict[str, Any]:
        return {
            "agency_id": agency_id,
            "rule_key": rule_key,
        }

    async def _require_rule(
        self, rule_id: str, *, agency_id: str | None = None
    ) -> dict[str, Any]:
        filters: dict[str, Any] = {"id": rule_id}
        if agency_id:
            filters["agency_id"] = agency_id
        rule = await self.db.collection(
            OPERATIONAL_TASK_AUTOMATION_RULES_COLLECTION
        ).find_one(filters)
        if not rule:
            raise TaskAutomationDependencyError(
                "Task automation rule metadata was not found."
            )
        return rule

    async def _require_work_item(
        self, work_item_id: str, agency_id: str
    ) -> dict[str, Any]:
        item = await self.db.collection("operational_work_items").find_one(
            {"agency_id": agency_id, "id": work_item_id}
        )
        if not item:
            raise TaskAutomationDependencyError(
                "Canonical work item was not found in this Agency."
            )
        return item

    def _check_expected_version(
        self, record: dict[str, Any], expected_version: int | None
    ) -> None:
        if expected_version is not None and int(expected_version) != int(
            record.get("version") or 1
        ):
            raise TaskAutomationDependencyError("Version conflict.")

    async def _active_rule_versions(
        self, agency_id: str | None, rule_key: str
    ) -> list[dict[str, Any]]:
        return await self.db.collection(
            OPERATIONAL_TASK_AUTOMATION_RULES_COLLECTION
        ).find_many(
            {
                "agency_id": agency_id,
                "rule_key": rule_key,
                "status": "active",
                "enabled": True,
            }
        )

    async def _audit_rule_lifecycle(
        self,
        rule: dict[str, Any],
        user: dict,
        action: str,
        reason: str | None,
    ) -> None:
        await self._audit(
            agency_id=rule.get("agency_id"),
            actor_user_id=user.get("id"),
            event_type=f"automation.rule_{action}",
            entity_id=rule["id"],
            summary=(
                f"Automation rule {rule.get('rule_key') or rule.get('rule_code')} "
                f"version {rule.get('version', 1)} was {action}."
            ),
            metadata={"reason": reason},
        )

    async def _dependency_would_cycle(
        self, agency_id: str, predecessor_id: str, successor_id: str
    ) -> bool:
        dependencies = await self.db.collection(
            OPERATIONAL_TASK_DEPENDENCIES_COLLECTION
        ).find_many(
            {"agency_id": agency_id},
            sort=[
                ("predecessor_task_id", 1),
                ("successor_task_id", 1),
                ("id", 1),
            ],
            limit=500,
        )
        graph: dict[str, set[str]] = {}
        for dependency in dependencies:
            graph.setdefault(dependency["predecessor_task_id"], set()).add(
                dependency["successor_task_id"]
            )
        graph.setdefault(predecessor_id, set()).add(successor_id)
        stack = [successor_id]
        visited: set[str] = set()
        while stack:
            current = stack.pop()
            if current == predecessor_id:
                return True
            if current in visited:
                continue
            visited.add(current)
            stack.extend(sorted(graph.get(current, set()), reverse=True))
            if len(visited) > 500:
                raise TaskAutomationDependencyError(
                    "Dependency graph exceeds the bounded validation limit."
                )
        return False

    def _task_type_for_action(
        self, action_type: str, template_code: str | None
    ) -> str:
        template_map = {
            "triage_request": "qualify_request",
            "obtain_missing_passenger_data": "request_missing_information",
            "obtain_passport_document": "collect_documents",
            "request_medif": "review_special_service",
            "confirm_poc_model_battery": "review_special_service",
            "request_wheelchair_dimensions_battery": "review_special_service",
            "request_petc_avih_documents": "review_pet_request",
            "request_airline_approval": "complete_approval",
            "prepare_offer": "prepare_offer",
            "review_pricing_manual_quote": "review_offer",
            "follow_up_client_acceptance": "follow_up_offer",
            "create_booking_readiness_check": "prepare_booking",
            "ticket_emd_verification": "verify_coupon_status",
            "invoice_payment_follow_up": "investigate_unallocated_payment",
            "disruption_handling": "resolve_booking_failure",
            "refund_change_claim_follow_up": "review_refund",
            "final_trip_document_check": "prepare_client_documents",
        }
        action_map = {
            "request_document": "collect_documents",
            "request_missing_information": "request_missing_information",
            "create_supplier_follow_up": "respond_to_supplier",
            "create_client_follow_up": "respond_to_client",
            "create_accounting_review": "investigate_unallocated_payment",
            "create_policy_review": "review_service_requirements",
            "create_manual_booking_review": "prepare_booking",
        }
        return action_map.get(action_type) or template_map.get(
            template_code or "", template_code or "manual"
        )

    def _approval_permission(self, action_type: str) -> str:
        mapping = {
            "deliver_offer": "edit_offers",
            "revise_offer": "edit_offers",
            "accept_offer": "edit_offers",
            "decline_offer": "edit_offers",
            "confirm_trip": "edit_trips",
            "cancel_trip": "edit_trips",
            "record_booking_result": "edit_bookings",
            "modify_ticket_emd_truth": "edit_tickets_emds",
            "issue_invoice": "edit_commercial_ledger",
            "allocate_payment": "edit_commercial_ledger",
            "issue_credit_note": "edit_commercial_ledger",
            "post_refund": "edit_finance",
            "confirm_exchange": "edit_finance",
            "publish_portal_record": "edit_documents",
            "publish_client_document": "edit_documents",
            "send_external_communication": "edit_tasks",
            "change_external_lifecycle_status": "edit_tasks",
        }
        return mapping.get(action_type, "edit_tasks")

    def _max_safety_class(
        self, actions: list[dict[str, Any]]
    ) -> str:
        ranks = {"A": 1, "B": 2, "C": 3, "D": 4}
        return max(
            (str(item.get("safety_class") or "A") for item in actions),
            key=lambda value: ranks.get(value, 1),
            default="A",
        )

    def _parse_dt(self, value: Any) -> datetime | None:
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return None
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)

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

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _sort_text(self, value: Any) -> str:
        return "" if value is None else str(value)

    def _label(self, value: Any) -> str:
        return (
            str(value or "").replace("_", " ").replace("-", " ").strip().title()
            or "Operational Deadline"
        )

    def _norm(self, value: Any) -> str:
        return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")
