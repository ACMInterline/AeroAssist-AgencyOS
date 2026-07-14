from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from database import Database
from models import (
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
    RequestTask,
    new_id,
)


PHASE_LABEL = "phase_54_8_operations_command_center_foundation"

OPERATIONAL_TASK_TEMPLATES_COLLECTION = "operational_task_templates"
OPERATIONAL_TASK_DEPENDENCIES_COLLECTION = "operational_task_dependencies"
OPERATIONAL_TASK_AUTOMATION_RULES_COLLECTION = "operational_task_automation_rules"
OPERATIONAL_TASK_AUTOMATION_RUNS_COLLECTION = "operational_task_automation_runs"

TASK_TEMPLATE_STATUSES = ["draft", "active", "paused", "archived"]
TASK_DEPENDENCY_TYPES = ["finish_to_start", "start_to_start", "manual_review", "evidence_required"]
TASK_DEPENDENCY_STATUSES = ["pending", "blocked", "satisfied", "waived"]
TASK_AUTOMATION_RULE_STATUSES = ["draft", "active", "paused", "archived"]
TASK_AUTOMATION_RUN_STATUSES = ["completed", "completed_with_warnings", "failed", "skipped"]
TASK_AUTOMATION_TRIGGER_EVENTS = [
    "request_created",
    "service_requirement_detected",
    "offer_needed",
    "offer_sent",
    "offer_accepted",
    "booking_ready",
    "ticket_emd_linked",
    "payment_due",
    "disruption_reported",
    "refund_change_claim_opened",
    "after_sales_case_opened",
    "pre_trip_check",
    "manual_retry",
]

SAFE_TASK_TEMPLATES: list[dict[str, Any]] = [
    {
        "template_code": "triage_request",
        "title_pattern": "Triage {source_label}",
        "description_pattern": "Review the new request and identify passenger service requirements.",
        "related_entity_types": ["request", "travel_request_workspace"],
        "trigger_event": "request_created",
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
        "trigger_event": "request_created",
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
        "trigger_event": "request_created",
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
        "trigger_event": "service_requirement_detected",
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
        "trigger_event": "service_requirement_detected",
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
        "trigger_event": "service_requirement_detected",
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
        "trigger_event": "service_requirement_detected",
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
        "trigger_event": "service_requirement_detected",
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
        "trigger_event": "offer_needed",
        "default_priority": "normal",
        "due_offset_days": 1,
        "dependency_template_codes": ["triage_request"],
    },
    {
        "template_code": "review_pricing_manual_quote",
        "title_pattern": "Review pricing or manual quote for {source_label}",
        "description_pattern": "Review pricing metadata and manual quote dependencies before client presentation.",
        "related_entity_types": ["offer_workspace", "pricing_formula_builder"],
        "trigger_event": "offer_needed",
        "default_priority": "normal",
        "due_offset_days": 1,
        "dependency_template_codes": ["prepare_offer"],
    },
    {
        "template_code": "follow_up_client_acceptance",
        "title_pattern": "Follow up client acceptance for {source_label}",
        "description_pattern": "Follow up client acceptance metadata without sending automated messages.",
        "related_entity_types": ["offer_workspace"],
        "trigger_event": "offer_sent",
        "default_priority": "normal",
        "due_offset_days": 2,
        "dependency_template_codes": ["prepare_offer"],
    },
    {
        "template_code": "create_booking_readiness_check",
        "title_pattern": "Create booking readiness check for {source_label}",
        "description_pattern": "Review booking readiness metadata after offer acceptance.",
        "related_entity_types": ["booking_workspace", "offer_workspace"],
        "trigger_event": "offer_accepted",
        "default_priority": "high",
        "due_offset_hours": 12,
        "dependency_template_codes": ["follow_up_client_acceptance"],
    },
    {
        "template_code": "ticket_emd_verification",
        "title_pattern": "Verify ticket and EMD metadata for {source_label}",
        "description_pattern": "Verify ticket, coupon, EMD, RFIC/RFISC, and document metadata after booking.",
        "related_entity_types": ["ticket_workspace", "emd_workspace", "booking_workspace"],
        "trigger_event": "ticket_emd_linked",
        "default_priority": "high",
        "due_offset_hours": 12,
        "dependency_template_codes": ["create_booking_readiness_check"],
    },
    {
        "template_code": "invoice_payment_follow_up",
        "title_pattern": "Follow up invoice or payment metadata for {source_label}",
        "description_pattern": "Review payment/invoice follow-up metadata without payment processing or automated messaging.",
        "related_entity_types": ["booking_workspace", "payment"],
        "trigger_event": "payment_due",
        "default_priority": "high",
        "due_offset_hours": 24,
        "dependency_template_codes": ["create_booking_readiness_check"],
    },
    {
        "template_code": "disruption_handling",
        "title_pattern": "Handle disruption for {source_label}",
        "description_pattern": "Create disruption handling task metadata for human operational review.",
        "related_entity_types": ["disruption", "trip_workspace"],
        "trigger_event": "disruption_reported",
        "default_priority": "urgent",
        "due_offset_hours": 1,
    },
    {
        "template_code": "refund_change_claim_follow_up",
        "title_pattern": "Follow up refund/change/claim for {source_label}",
        "description_pattern": "Track refund, change, or claim follow-up metadata without processing workflow execution.",
        "related_entity_types": ["service_case", "refund_exchange_case"],
        "trigger_event": "refund_change_claim_opened",
        "default_priority": "normal",
        "due_offset_days": 3,
    },
    {
        "template_code": "final_trip_document_check",
        "title_pattern": "Final trip document check for {source_label}",
        "description_pattern": "Confirm final travel document metadata before travel readiness.",
        "related_entity_types": ["trip_workspace", "document_workspace"],
        "trigger_event": "pre_trip_check",
        "default_priority": "high",
        "due_offset_hours": 24,
        "dependency_template_codes": ["ticket_emd_verification", "invoice_payment_follow_up"],
    },
]

DEFAULT_AUTOMATION_RULES: list[dict[str, Any]] = [
    {
        "rule_code": f"default_{template['template_code']}",
        "name": template["title_pattern"].replace("{source_label}", "event"),
        "trigger_event": template["trigger_event"],
        "conditions_json": {},
        "generated_template_code": template["template_code"],
        "deduplication_key_pattern": "{agency_id}:{source_entity_type}:{source_entity_id}:{template_code}",
        "enabled": True,
        "status": "active",
    }
    for template in SAFE_TASK_TEMPLATES
]


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
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def list_templates(self, agency_id: str | None = None, include_defaults: bool = True, **filters: Any) -> list[dict[str, Any]]:
        query: dict[str, Any] = {}
        if agency_id:
            query["agency_id"] = agency_id
        for field in ["template_code", "trigger_event", "status", "required_capability"]:
            if filters.get(field):
                query[field] = self._norm(filters[field])
        templates = await self.db.collection(OPERATIONAL_TASK_TEMPLATES_COLLECTION).find_many(query or None)
        if include_defaults:
            existing_codes = {item.get("template_code") for item in templates}
            for template in SAFE_TASK_TEMPLATES:
                if template["template_code"] in existing_codes:
                    continue
                if filters.get("trigger_event") and self._norm(filters["trigger_event"]) != template["trigger_event"]:
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
        if agency_id:
            query["agency_id"] = agency_id
        for field in ["rule_code", "trigger_event", "generated_template_code", "status"]:
            if filters.get(field):
                query[field] = self._norm(filters[field])
        if "enabled" in filters and filters["enabled"] is not None:
            query["enabled"] = bool(filters["enabled"])
        rules = await self.db.collection(OPERATIONAL_TASK_AUTOMATION_RULES_COLLECTION).find_many(query or None)
        if include_defaults:
            existing_codes = {item.get("rule_code") for item in rules}
            for rule in DEFAULT_AUTOMATION_RULES:
                if rule["rule_code"] in existing_codes:
                    continue
                if filters.get("trigger_event") and self._norm(filters["trigger_event"]) != rule["trigger_event"]:
                    continue
                rules.append(self._default_rule(rule, agency_id=agency_id))
        rules.sort(key=lambda item: str(item.get("rule_code") or ""))
        return rules

    async def create_rule(self, payload: OperationalTaskAutomationRuleCreate | dict[str, Any], user: dict) -> dict[str, Any]:
        data = self._payload(payload)
        if not data.get("rule_code"):
            data["rule_code"] = self._code(data.get("name") or data.get("generated_template_code") or "task_rule")
        if not data.get("deduplication_key_pattern"):
            data["deduplication_key_pattern"] = "{agency_id}:{source_entity_type}:{source_entity_id}:{template_code}"
        self._normalize_rule(data)
        data["created_by"] = user.get("id")
        data["updated_by"] = user.get("id")
        created = await self.db.collection(OPERATIONAL_TASK_AUTOMATION_RULES_COLLECTION).insert_one(OperationalTaskAutomationRule(**data).model_dump(mode="json"))
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
        merged = {**existing, **updates}
        self._normalize_rule(merged, partial=True)
        for field in ["scope", "rule_code", "trigger_event", "generated_template_code", "status"]:
            if field in updates and updates[field] is not None:
                updates[field] = self._norm(updates[field])
        updates["updated_by"] = user.get("id")
        updated = await self.db.collection(OPERATIONAL_TASK_AUTOMATION_RULES_COLLECTION).update_one({"id": existing["id"]}, updates)
        return {"phase": PHASE_LABEL, "rule": updated, "metadata_only": True, **self.safety_flags()}

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
        data["created_by"] = user.get("id")
        data["updated_by"] = user.get("id")
        created = await self.db.collection(OPERATIONAL_TASK_DEPENDENCIES_COLLECTION).insert_one(OperationalTaskDependency(**data).model_dump(mode="json"))
        await self.evaluate_dependencies(data["agency_id"], user, successor_task_id=created["successor_task_id"])
        return {"phase": PHASE_LABEL, "dependency": await self._dependency_projection(created), "metadata_only": True, **self.safety_flags()}

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
        return await self.update_dependency(dependency_id, {"status": "satisfied", "satisfied_at": self._now(), "metadata": self._payload(payload).get("metadata") or {}}, user, agency_id=agency_id)

    async def waive_dependency(self, dependency_id: str, payload: OperationalTaskDependencyActionRequest | dict[str, Any], user: dict, agency_id: str | None = None) -> dict[str, Any]:
        data = self._payload(payload)
        return await self.update_dependency(dependency_id, {"status": "waived", "blocked_reason": data.get("reason"), "metadata": data.get("metadata") or {}}, user, agency_id=agency_id)

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
        data = self._payload(payload)
        if agency_id:
            data["agency_id"] = agency_id
        self._validate_run_request(data)
        data["trigger_event"] = self._norm(data["trigger_event"])
        data["source_entity_type"] = self._norm(data["source_entity_type"])
        idempotency_key = data.get("idempotency_key") or self._idempotency_key(data)
        existing = await self.db.collection(OPERATIONAL_TASK_AUTOMATION_RUNS_COLLECTION).find_one({"agency_id": data["agency_id"], "idempotency_key": idempotency_key})
        if existing and not data.get("retry_of_run_id"):
            return {"phase": PHASE_LABEL, "run": existing, "idempotent_reused": True, "metadata_only": True, **self.safety_flags()}

        templates = await self.list_templates(agency_id=data["agency_id"], include_defaults=True, trigger_event=data["trigger_event"])
        templates_by_code = {template["template_code"]: template for template in templates}
        requested_codes = set(data.get("template_codes") or [])
        rules = await self.list_rules(agency_id=data["agency_id"], include_defaults=True, trigger_event=data["trigger_event"], enabled=True)
        if requested_codes:
            rules = [rule for rule in rules if rule.get("generated_template_code") in requested_codes]

        matched_rules: list[dict[str, Any]] = []
        tasks_created: list[dict[str, Any]] = []
        tasks_skipped: list[dict[str, Any]] = []
        dependencies_created: list[dict[str, Any]] = []
        warnings: list[str] = []
        errors: list[str] = []
        tasks_by_template: dict[str, dict[str, Any]] = {}
        source_label = data.get("event_snapshot_json", {}).get("source_label") or data.get("event_snapshot_json", {}).get("title") or data["source_entity_id"]
        request_id = data.get("request_id") or data["source_entity_id"]

        for rule in rules:
            template_code = rule.get("generated_template_code")
            template = templates_by_code.get(template_code)
            if not template:
                warnings.append(f"Rule {rule.get('rule_code')} references missing template {template_code}.")
                continue
            if not self._conditions_match(rule.get("conditions_json") or {}, data.get("event_snapshot_json") or {}):
                continue
            matched_rules.append({"rule_code": rule.get("rule_code"), "template_code": template_code, "metadata_only": True})
            dedupe_key = self._render_pattern(rule.get("deduplication_key_pattern") or "{agency_id}:{source_entity_type}:{source_entity_id}:{template_code}", data, template)
            existing_task = await self._existing_generated_task(data["agency_id"], dedupe_key)
            if existing_task:
                tasks_skipped.append({"template_code": template_code, "task_id": existing_task["id"], "reason": "deduplicated", "deduplication_key": dedupe_key})
                tasks_by_template[template_code] = existing_task
                continue
            task = await self._create_request_task_from_template(data, template, source_label, request_id, dedupe_key, user)
            tasks_created.append({"template_code": template_code, "task_id": task["id"], "title": task["title"], "status": task["status"], "due_at": task.get("due_at"), "deduplication_key": dedupe_key})
            tasks_by_template[template_code] = task
            await self._sync_generated_task(task, template, data, user)

        run_status = "completed"
        if errors:
            run_status = "failed"
        elif warnings:
            run_status = "completed_with_warnings"
        if not matched_rules:
            run_status = "skipped"
            warnings.append("No enabled task automation rules matched the event snapshot.")

        run = OperationalTaskAutomationRun(
            agency_id=data["agency_id"],
            run_reference=self._run_reference(data["trigger_event"]),
            trigger_event=data["trigger_event"],
            source_entity_type=data["source_entity_type"],
            source_entity_id=data["source_entity_id"],
            idempotency_key=idempotency_key if not data.get("retry_of_run_id") else f"{idempotency_key}:retry:{new_id()[:8]}",
            event_snapshot_json=data.get("event_snapshot_json") or {},
            rules_matched=matched_rules,
            tasks_created=tasks_created,
            tasks_skipped=tasks_skipped,
            warnings=warnings,
            errors=errors,
            status=run_status,
            retry_of_run_id=data.get("retry_of_run_id"),
            created_by=user.get("id"),
            updated_by=user.get("id"),
            metadata=data.get("metadata") or {},
        )
        created_run = await self.db.collection(OPERATIONAL_TASK_AUTOMATION_RUNS_COLLECTION).insert_one(run.model_dump(mode="json"))

        dependencies_created = await self._create_run_dependencies(data, created_run["id"], tasks_by_template, user)
        if dependencies_created:
            created_run = await self.db.collection(OPERATIONAL_TASK_AUTOMATION_RUNS_COLLECTION).update_one(
                {"id": created_run["id"]},
                {"dependencies_created": dependencies_created, "updated_by": user.get("id")},
            ) or created_run
            await self.evaluate_dependencies(data["agency_id"], user, source_entity_type=data["source_entity_type"], source_entity_id=data["source_entity_id"])
        await self._record_workflow_event(data, created_run)

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
            "request_id": (existing.get("event_snapshot_json") or {}).get("request_id") or existing["source_entity_id"],
            "event_snapshot_json": existing.get("event_snapshot_json") or {},
            "template_codes": [rule.get("template_code") for rule in existing.get("rules_matched") or [] if rule.get("template_code")],
            "retry_of_run_id": existing["id"],
            "idempotency_key": existing.get("idempotency_key"),
            "metadata": {"manual_retry": True, **(self._payload(payload).get("metadata") or {})},
        }
        return await self.run_automation(request, user, agency_id=existing["agency_id"])

    async def evaluate_dependencies(self, agency_id: str, user: dict, successor_task_id: str | None = None, source_entity_type: str | None = None, source_entity_id: str | None = None) -> dict[str, Any]:
        dependencies = await self.list_dependencies(agency_id=agency_id, successor_task_id=successor_task_id, source_entity_type=source_entity_type, source_entity_id=source_entity_id)
        updated_dependencies: list[dict[str, Any]] = []
        affected_successors = {dependency["successor_task_id"] for dependency in dependencies}
        for dependency in dependencies:
            predecessor = await self.db.collection("request_tasks").find_one({"agency_id": agency_id, "id": dependency["predecessor_task_id"]})
            if dependency.get("status") in {"satisfied", "waived"}:
                continue
            if predecessor and predecessor.get("status") == "done":
                updated = await self.db.collection(OPERATIONAL_TASK_DEPENDENCIES_COLLECTION).update_one(
                    {"id": dependency["id"]},
                    {"status": "satisfied", "satisfied_at": self._now(), "updated_by": user.get("id")},
                )
                if updated:
                    updated_dependencies.append(await self._dependency_projection(updated))
        ready: list[dict[str, Any]] = []
        blocked: list[dict[str, Any]] = []
        for task_id in affected_successors:
            task = await self.db.collection("request_tasks").find_one({"agency_id": agency_id, "id": task_id})
            if not task:
                continue
            task_dependencies = await self.db.collection(OPERATIONAL_TASK_DEPENDENCIES_COLLECTION).find_many({"agency_id": agency_id, "successor_task_id": task_id})
            unsatisfied = [dep for dep in task_dependencies if dep.get("status") not in {"satisfied", "waived"}]
            if unsatisfied:
                if task.get("status") == "open":
                    task = await self.db.collection("request_tasks").update_one({"id": task_id}, {"status": "waiting"})
                    await self._sync_generated_task(
                        task,
                        {"template_code": "dependency_blocked"},
                        {
                            "agency_id": agency_id,
                            "source_entity_type": task.get("request_id") and "request" or "request_task",
                            "source_entity_id": task.get("request_id") or task_id,
                        },
                        user,
                    )
                blocked.append(task)
            else:
                if task.get("status") == "waiting":
                    task = await self.db.collection("request_tasks").update_one({"id": task_id}, {"status": "open"})
                    await self._sync_generated_task(task, {"template_code": "dependency_released"}, {"agency_id": agency_id, "source_entity_type": task.get("request_id") and "request" or "request_task", "source_entity_id": task.get("request_id") or task_id}, user)
                ready.append(task)
        return {"phase": PHASE_LABEL, "updated_dependencies": updated_dependencies, "ready_tasks": ready, "blocked_tasks": blocked, "metadata_only": True, **self.safety_flags()}

    async def ready_tasks(self, agency_id: str) -> list[dict[str, Any]]:
        tasks = await self.db.collection("request_tasks").find_many({"agency_id": agency_id})
        return [task for task in tasks if task.get("status") in {"open", "in_progress"}]

    async def blocked_tasks(self, agency_id: str) -> list[dict[str, Any]]:
        tasks = await self.db.collection("request_tasks").find_many({"agency_id": agency_id})
        return [task for task in tasks if task.get("status") == "waiting"]

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
            "request_tasks_reused": True,
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
            "unbounded_automation_disabled": True,
            "agency_isolation_enforced": True,
            "human_authority_final": True,
        }

    async def _create_request_task_from_template(self, data: dict[str, Any], template: dict[str, Any], source_label: str, request_id: str, dedupe_key: str, user: dict) -> dict[str, Any]:
        due_at = self._due_at(template)
        title = self._render_pattern(template.get("title_pattern") or template["template_code"], data, template, source_label=source_label)
        description = self._render_pattern(template.get("description_pattern") or "", data, template, source_label=source_label) or None
        task = RequestTask(
            agency_id=data["agency_id"],
            request_id=request_id,
            assigned_user_id=data.get("event_snapshot_json", {}).get("assigned_user_id"),
            title=title,
            description=description,
            status="open",
            priority=self._norm(template.get("default_priority") or "normal"),
            due_at=due_at,
            visibility="internal",
        )
        created = await self.db.collection("request_tasks").insert_one(task.model_dump(mode="json"))
        created["automation_template_code"] = template["template_code"]
        created["automation_deduplication_key"] = dedupe_key
        return created

    async def _sync_generated_task(self, task: dict[str, Any], template: dict[str, Any], data: dict[str, Any], user: dict) -> None:
        try:
            from services.agent_work_queue_service import AgentWorkQueueService
        except ImportError:
            return
        queue_code = "waiting_client" if task.get("status") == "waiting" else "unassigned"
        await AgentWorkQueueService(self.db).generate_work_item(
            {
                "agency_id": task["agency_id"],
                "work_item_type": "task_deadline",
                "source_entity_type": "request_task",
                "source_entity_id": task["id"],
                "request_task_id": task["id"],
                "title": task.get("title") or "Generated task",
                "summary": task.get("description"),
                "priority": task.get("priority") or "normal",
                "severity": "medium",
                "queue_code": queue_code,
                "due_at": task.get("due_at"),
                "sla_status": None,
                "blocker_status": "manual_review" if task.get("status") == "waiting" else "not_blocked",
                "generation_reason": "task_automation_dependency_orchestration",
                "source_snapshot_json": task,
                "compatibility_mapping_json": {
                    "request_task_id": task["id"],
                    "request_id": task.get("request_id"),
                    "automation_template_code": template.get("template_code"),
                    "source_entity_type": data.get("source_entity_type"),
                    "source_entity_id": data.get("source_entity_id"),
                },
            },
            user,
            agency_id=task["agency_id"],
        )

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

    async def _existing_generated_task(self, agency_id: str, dedupe_key: str) -> dict[str, Any] | None:
        runs = await self.db.collection(OPERATIONAL_TASK_AUTOMATION_RUNS_COLLECTION).find_many({"agency_id": agency_id})
        for run in runs:
            for task_ref in (run.get("tasks_created") or []) + (run.get("tasks_skipped") or []):
                if task_ref.get("deduplication_key") == dedupe_key and task_ref.get("task_id"):
                    task = await self.db.collection("request_tasks").find_one({"agency_id": agency_id, "id": task_ref["task_id"]})
                    if task:
                        return task
        return None

    async def _dependency_projection(self, dependency: dict[str, Any]) -> dict[str, Any]:
        projected = dict(dependency)
        projected["predecessor_task"] = await self.db.collection("request_tasks").find_one({"agency_id": dependency["agency_id"], "id": dependency["predecessor_task_id"]})
        projected["successor_task"] = await self.db.collection("request_tasks").find_one({"agency_id": dependency["agency_id"], "id": dependency["successor_task_id"]})
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
        for field in ["scope", "template_code", "trigger_event", "default_priority", "assigned_role_strategy", "assigned_team_strategy", "required_capability", "status"]:
            if data.get(field):
                data[field] = self._norm(data[field])
        if data.get("status") and data["status"] not in TASK_TEMPLATE_STATUSES:
            raise TaskAutomationDependencyError(f"Unsupported task template status metadata: {data['status']}.")
        if data.get("trigger_event") and data["trigger_event"] not in TASK_AUTOMATION_TRIGGER_EVENTS:
            raise TaskAutomationDependencyError(f"Unsupported task trigger metadata: {data['trigger_event']}.")

    def _normalize_rule(self, data: dict[str, Any], *, partial: bool = False) -> None:
        if not partial:
            for field in ["rule_code", "name", "trigger_event", "generated_template_code", "deduplication_key_pattern"]:
                if not data.get(field):
                    raise TaskAutomationDependencyError(f"{field} is required for task automation rule metadata.")
        for field in ["scope", "rule_code", "trigger_event", "generated_template_code", "status"]:
            if data.get(field):
                data[field] = self._norm(data[field])
        if data.get("status") and data["status"] not in TASK_AUTOMATION_RULE_STATUSES:
            raise TaskAutomationDependencyError(f"Unsupported task automation rule status metadata: {data['status']}.")

    def _normalize_dependency(self, data: dict[str, Any]) -> None:
        for field in ["agency_id", "predecessor_task_id", "successor_task_id"]:
            if not data.get(field):
                raise TaskAutomationDependencyError(f"{field} is required for task dependency metadata.")
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
        if self._norm(data["trigger_event"]) not in TASK_AUTOMATION_TRIGGER_EVENTS:
            raise TaskAutomationDependencyError(f"Unsupported task automation trigger metadata: {data['trigger_event']}.")

    def _conditions_match(self, conditions: dict[str, Any], event_snapshot: dict[str, Any]) -> bool:
        for field, expected in conditions.items():
            if field == "all":
                if not all(self._conditions_match(item, event_snapshot) for item in expected or []):
                    return False
                continue
            if field == "any":
                if not any(self._conditions_match(item, event_snapshot) for item in expected or []):
                    return False
                continue
            actual = event_snapshot.get(field)
            if isinstance(expected, list):
                if actual not in expected:
                    return False
            elif actual != expected:
                return False
        return True

    def _due_at(self, template: dict[str, Any]) -> datetime | None:
        minutes = int(template.get("due_offset_minutes") or 0)
        hours = int(template.get("due_offset_hours") or 0)
        days = int(template.get("due_offset_days") or 0)
        if not any([minutes, hours, days]):
            return None
        return self._now() + timedelta(days=days, hours=hours, minutes=minutes)

    def _idempotency_key(self, data: dict[str, Any]) -> str:
        template_part = ",".join(sorted(data.get("template_codes") or [])) or "all"
        return f"{data['agency_id']}:{self._norm(data['trigger_event'])}:{self._norm(data['source_entity_type'])}:{data['source_entity_id']}:{template_part}"

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

    def _norm(self, value: Any) -> str:
        return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")
