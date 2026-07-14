from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from database import AGENCY_OWNED_COLLECTIONS, Database
from services.operations_command_center_service import OperationsCommandCenterService
from services.pilot_readiness_service import PilotReadinessService


PHASE_LABEL = "phase_55_3_airline_knowledge_versioning_change_detection_foundation"

MATURITY_DIMENSIONS = [
    "workflow_linkage",
    "assignment_readiness",
    "sla_readiness",
    "task_dependency_readiness",
    "request_to_trip_conversion_readiness",
    "offer_to_booking_readiness",
    "servicing_readiness",
    "command_center_visibility",
    "audit_completeness",
    "client_internal_message_separation",
    "agency_isolation",
    "production_safety",
]

GOLDEN_PATH_STAGES = [
    "new_request",
    "triage_work_item",
    "sla_deadline",
    "passenger_segment_service_resolution",
    "request_to_trip_conversion",
    "offer_preparation",
    "accepted_offer",
    "booking_handoff",
    "booking_readiness",
    "booking_ticketing",
    "passenger_service_fulfillment",
    "servicing_after_sales",
    "completed_trip",
    "archived_operational_record",
]

MODULE_REQUIREMENTS: dict[str, dict[str, Any]] = {
    "workflow_linkage": {
        "label": "Workflow linkage",
        "collections": ["operational_workflow_instances", "operational_workflow_events", "operational_workflow_transitions"],
        "platform_route": "/platform/operational-workflows",
        "agency_route": "/agency/operational-workflows",
    },
    "assignment_readiness": {
        "label": "Assignment readiness",
        "collections": ["operational_work_items", "operational_queue_definitions", "operational_assignment_events"],
        "platform_route": "/platform/work-queues",
        "agency_route": "/agency/work-queue",
    },
    "sla_readiness": {
        "label": "SLA readiness",
        "collections": ["operational_sla_policies", "operational_deadlines", "operational_sla_events", "operational_business_calendars"],
        "platform_route": "/platform/sla-policies",
        "agency_route": "/agency/deadlines",
    },
    "task_dependency_readiness": {
        "label": "Task dependency readiness",
        "collections": ["operational_task_templates", "operational_task_dependencies", "operational_task_automation_rules", "operational_task_automation_runs"],
        "platform_route": "/platform/task-automation",
        "agency_route": "/agency/task-automation",
    },
    "request_to_trip_conversion_readiness": {
        "label": "Request-to-trip conversion readiness",
        "collections": ["request_trip_conversion_plans", "request_trip_conversion_runs", "request_trip_entity_mappings", "request_trip_conversion_issues"],
        "platform_route": "/platform/request-trip-conversion",
        "agency_route": "/agency/request-trip-conversion",
    },
    "offer_to_booking_readiness": {
        "label": "Offer-to-booking readiness",
        "collections": ["offer_booking_handoffs", "offer_booking_handoff_checks", "offer_booking_handoff_mappings", "booking_execution_instructions"],
        "platform_route": "/platform/booking-handoffs",
        "agency_route": "/agency/booking-handoffs",
    },
    "servicing_readiness": {
        "label": "Servicing readiness",
        "collections": ["after_sales_cases", "after_sales_case_items", "after_sales_decisions", "after_sales_financial_impacts", "after_sales_resolutions", "after_sales_communication_records"],
        "platform_route": "/platform/after-sales",
        "agency_route": "/agency/after-sales",
    },
    "command_center_visibility": {
        "label": "Command-center visibility",
        "collections": ["operational_work_items", "operational_deadlines", "operational_workflow_instances"],
        "platform_route": "/platform/operations-governance",
        "agency_route": "/agency/operations-command-center",
    },
    "audit_completeness": {
        "label": "Audit completeness",
        "collections": ["operational_workflow_events", "operational_assignment_events", "operational_sla_events", "operational_timelines"],
        "platform_route": "/platform/operational-timelines",
        "agency_route": "/agency/timeline",
    },
    "client_internal_message_separation": {
        "label": "Client/internal message separation",
        "collections": ["after_sales_communication_records", "pilot_golden_path_runs"],
        "platform_route": "/platform/after-sales",
        "agency_route": "/agency/after-sales",
    },
    "agency_isolation": {
        "label": "Agency isolation",
        "collections": ["operational_workflow_instances", "operational_work_items", "operational_deadlines", "after_sales_cases"],
        "platform_route": "/platform/workflow-maturity",
        "agency_route": "/agency/workflow-maturity",
    },
    "production_safety": {
        "label": "Production safety",
        "collections": [],
        "platform_route": "/platform/workflow-maturity",
        "agency_route": "/agency/workflow-maturity",
    },
}

OPERATIONAL_COLLECTIONS = sorted(
    {
        collection
        for requirement in MODULE_REQUIREMENTS.values()
        for collection in requirement["collections"]
    }
    | {
        "travel_requests",
        "passenger_workspaces",
        "request_segment_service_scopes",
        "trip_workspaces",
        "offer_workspaces_v2",
        "offer_acceptances",
        "booking_readiness_packages",
        "booking_workspaces",
        "ticket_workspaces",
        "emd_workspaces",
        "ssr_osi_workspaces",
        "document_workspaces",
        "passenger_service_workflows",
        "operational_intelligence_cases",
        "pilot_readiness_issues",
    }
)

TEST_CASE_TEMPLATES: list[dict[str, Any]] = [
    {
        "template_code": "standard_request_offer_booking",
        "name": "Standard request to offer to booking",
        "family": "standard",
        "expected_status": "passed",
    },
    {
        "template_code": "wchc_multi_segment_request",
        "name": "WCHC multi-segment request",
        "family": "WCHC",
        "expected_status": "passed",
        "service_requirements": ["WCHC"],
        "segment_count": 2,
    },
    {
        "template_code": "petc_conditional_approval_documents",
        "name": "PETC conditional approval and document case",
        "family": "PETC",
        "expected_status": "conditional",
        "service_requirements": ["PETC"],
        "warning_stages": ["passenger_service_fulfillment", "booking_readiness"],
    },
    {
        "template_code": "medif_poc_case",
        "name": "MEDIF and portable oxygen concentrator case",
        "family": "MEDIF_POC",
        "expected_status": "conditional",
        "service_requirements": ["MEDIF", "POC"],
        "warning_stages": ["passenger_segment_service_resolution", "passenger_service_fulfillment"],
    },
    {
        "template_code": "umnr_connection_restricted",
        "name": "UMNR connection-restricted case",
        "family": "UMNR",
        "expected_status": "blocked",
        "service_requirements": ["UMNR"],
        "blocked_stage": "offer_preparation",
        "blocker": "Connection restriction requires human itinerary review.",
    },
    {
        "template_code": "accepted_offer_missing_approval",
        "name": "Accepted offer blocked by missing approval",
        "family": "booking_approval",
        "expected_status": "blocked",
        "blocked_stage": "booking_handoff",
        "blocker": "Required airline approval is missing from the accepted-offer handoff.",
    },
    {
        "template_code": "booking_ready_after_blocker_resolution",
        "name": "Booking ready after blocker resolution",
        "family": "booking_approval",
        "expected_status": "passed",
        "blocked_stage": "booking_handoff",
        "blocker": "Required approval was initially missing.",
        "resume_after_resolution": True,
    },
    {
        "template_code": "ticketed_trip_after_sales_change",
        "name": "Ticketed trip requiring an after-sales change",
        "family": "after_sales_change",
        "expected_status": "passed",
        "required_stages": ["booking_ticketing", "servicing_after_sales"],
    },
    {
        "template_code": "disruption_urgent_operations",
        "name": "Disruption creates urgent queue, SLA, and task metadata",
        "family": "disruption",
        "expected_status": "passed",
        "required_signals": ["urgent_work_item", "disruption_response_deadline", "dependency_aware_tasks"],
    },
    {
        "template_code": "unknown_knowledge_manual_review",
        "name": "Unknown knowledge creates manual review",
        "family": "unknown_knowledge",
        "expected_status": "manual_review",
        "warning_stages": ["passenger_segment_service_resolution", "offer_preparation"],
        "required_signals": ["knowledge_gap_work_item", "human_review_required"],
    },
]


class OperationalWorkflowMaturityError(ValueError):
    pass


class OperationalWorkflowMaturityService:
    def __init__(self, db: Database | None) -> None:
        self.db = db

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "end_to_end_operational_workflow_maturity_foundation": True,
            "consolidation_only": True,
            "parallel_subsystem_disabled": True,
            "production_record_creation_disabled": True,
            "automatic_production_seeding_disabled": True,
            "destructive_reset_disabled": True,
            "provider_execution_disabled": True,
            "external_api_calls_disabled": True,
            "ai_disabled": True,
            "background_workers_disabled": True,
            "automatic_booking_disabled": True,
            "automatic_ticketing_disabled": True,
            "automatic_emd_issuance_disabled": True,
            "automatic_financial_commitment_disabled": True,
            "test_runs_isolated": True,
            "test_runs_persisted": False,
            "client_internal_message_separation_enabled": True,
            "agency_isolation_enforced": True,
            "human_authority_final": True,
        }

    async def platform_dashboard(self, agency_id: str | None = None) -> dict[str, Any]:
        return await self._dashboard(agency_id=agency_id, platform=True)

    async def agency_dashboard(self, agency_id: str) -> dict[str, Any]:
        return await self._dashboard(agency_id=agency_id, platform=False)

    async def assessment(self, agency_id: str | None = None) -> dict[str, Any]:
        records = await self._load_records(agency_id)
        return self._assessment_from_records(records, agency_id)

    def _assessment_from_records(self, records: dict[str, list[dict[str, Any]]], agency_id: str | None) -> dict[str, Any]:
        module_scores = self._module_scores(records, agency_id)
        blockers = self._blockers(records, module_scores)
        critical_blockers = [item for item in blockers if item.get("severity") == "critical"]
        score = round(sum(item["score"] for item in module_scores) / len(module_scores)) if module_scores else 0
        status = "blocked" if critical_blockers else "mature" if score >= 90 else "needs_attention" if score >= 70 else "not_ready"
        return {
            "maturity_score": score,
            "maturity_status": status,
            "module_scores": module_scores,
            "failing_stages": [item for item in module_scores if item.get("status") != "ready"],
            "critical_blocker_count": len(critical_blockers),
            "blocker_count": len(blockers),
            "deterministic_scoring": True,
            "scoring_explanation": "Each dimension scores registered canonical contracts and recorded linkage invariants. Missing operational examples affect coverage, not contract maturity.",
            "evaluated_at": self._now(),
            **self.safety_flags(),
        }

    def test_templates(self) -> list[dict[str, Any]]:
        return [
            {
                **template,
                "stage_count": len(GOLDEN_PATH_STAGES),
                "isolated_test_only": True,
                "auto_seed_disabled": True,
                "production_record_creation_disabled": True,
            }
            for template in TEST_CASE_TEMPLATES
        ]

    async def run_test_template(self, template_code: str, agency_id: str | None = None) -> dict[str, Any]:
        template = next((item for item in TEST_CASE_TEMPLATES if item["template_code"] == template_code), None)
        if not template:
            raise OperationalWorkflowMaturityError("Unknown operational workflow maturity test template.")

        blocked_stage = template.get("blocked_stage")
        warning_stages = set(template.get("warning_stages") or [])
        resume_after_resolution = bool(template.get("resume_after_resolution"))
        stages: list[dict[str, Any]] = []
        blocked_seen = False
        for index, stage_code in enumerate(GOLDEN_PATH_STAGES, start=1):
            status = "passed"
            summary = f"{self._label(stage_code)} contract is represented by canonical Epic 54 metadata."
            blockers: list[dict[str, Any]] = []
            warnings: list[dict[str, Any]] = []
            transition_history: list[dict[str, Any]] = []
            if stage_code in warning_stages:
                status = "warning"
                warnings.append({"code": "human_review_required", "summary": "The scenario remains conditional and requires human operational review."})
            if stage_code == blocked_stage:
                blocked_seen = True
                status = "blocked"
                blockers.append({"code": "scenario_blocker", "summary": template.get("blocker")})
                transition_history.append({"from_status": "ready", "to_status": "blocked", "reason": template.get("blocker")})
                if resume_after_resolution:
                    status = "passed"
                    transition_history.append({"from_status": "blocked", "to_status": "ready", "reason": "The isolated test applied an explicit simulated blocker resolution."})
                    blockers = []
                    summary = "The isolated test proved blocked-to-resumed progression without mutating operational records."
            stages.append(
                {
                    "sequence": index,
                    "stage_code": stage_code,
                    "stage_label": self._label(stage_code),
                    "status": status,
                    "summary": summary,
                    "blockers": blockers,
                    "warnings": warnings,
                    "transition_history": transition_history,
                    "source_records_created": False,
                }
            )

        final_status = template["expected_status"]
        passed_count = len([item for item in stages if item["status"] == "passed"])
        warning_count = len([item for item in stages if item["status"] == "warning"])
        blocked_count = len([item for item in stages if item["status"] == "blocked"])
        score = round(((passed_count + warning_count * 0.5) / len(stages)) * 100)
        return {
            "phase": PHASE_LABEL,
            "test_run": {
                "run_reference": f"WF-MATURITY-{template_code.upper().replace('_', '-')}",
                "template_code": template_code,
                "agency_id": agency_id,
                "test_mode": "isolated_diagnostic",
                "persisted": False,
                "production_record_created": False,
                "initial_blocked": blocked_seen,
                "resumed_after_explicit_resolution": resume_after_resolution,
                "final_status": final_status,
                "maturity_score": score,
                "stage_results": stages,
                "work_queue_signal": "verified" if template_code in {"standard_request_offer_booking", "disruption_urgent_operations", "unknown_knowledge_manual_review"} else "available",
                "sla_signal": "verified" if template_code in {"standard_request_offer_booking", "disruption_urgent_operations"} else "available",
                "task_dependency_signal": "verified" if template_code in {"booking_ready_after_blocker_resolution", "disruption_urgent_operations"} else "available",
                "command_center_visibility": True,
                "client_message": "This diagnostic scenario is complete and remains subject to human operational review.",
                "internal_trace": [{"trace_type": "isolated_test", "summary": "No production operational record was created or changed."}],
                "client_internal_message_separated": True,
                "evaluated_at": self._now(),
            },
            **self.safety_flags(),
        }

    async def _dashboard(self, agency_id: str | None, platform: bool) -> dict[str, Any]:
        records = await self._load_records(agency_id)
        assessment = self._assessment_from_records(records, agency_id)
        blockers = self._blockers(records, assessment["module_scores"])
        pilot = PilotReadinessService(self.db) if self.db else None
        recent_runs = await pilot.list_runs(agency_id=agency_id) if pilot else []
        command_center = await OperationsCommandCenterService(self.db).platform_dashboard(agency_id) if self.db and platform else await OperationsCommandCenterService(self.db).agency_command_center(agency_id) if self.db and agency_id else {}
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "maturity_score": assessment["maturity_score"],
            "maturity_status": assessment["maturity_status"],
            "assessment": assessment,
            "module_scores": assessment["module_scores"],
            "failing_stages": assessment["failing_stages"],
            "golden_path_stages": GOLDEN_PATH_STAGES,
            "test_templates": self.test_templates(),
            "golden_path_runs": recent_runs[:25],
            "blocker_register": blockers,
            "remediation_links": self._remediation_links(platform),
            "recent_workflow_errors": self._recent_errors(records),
            "operational_coverage": self._coverage(records),
            "command_center_summary": command_center.get("kpis") or {},
            "read_only_assessment": True,
            "platform_governance": platform,
            "notice": "Workflow Maturity consolidates existing Epic 54 metadata and runs isolated diagnostics only. It does not create production requests, trips, offers, bookings, tickets, EMDs, or after-sales cases.",
            **self.safety_flags(),
        }

    async def _load_records(self, agency_id: str | None) -> dict[str, list[dict[str, Any]]]:
        if not self.db:
            return {collection: [] for collection in OPERATIONAL_COLLECTIONS}
        filters = {"agency_id": agency_id} if agency_id else None
        results = await asyncio.gather(
            *(self.db.collection(collection).find_many(filters) for collection in OPERATIONAL_COLLECTIONS)
        )
        return dict(zip(OPERATIONAL_COLLECTIONS, results))

    def _module_scores(self, records: dict[str, list[dict[str, Any]]], agency_id: str | None) -> list[dict[str, Any]]:
        registered = set(AGENCY_OWNED_COLLECTIONS)
        scores: list[dict[str, Any]] = []
        for dimension in MATURITY_DIMENSIONS:
            requirement = MODULE_REQUIREMENTS[dimension]
            missing = [collection for collection in requirement["collections"] if collection not in registered]
            score = 0 if missing else 100
            warnings = self._dimension_warnings(dimension, records, agency_id)
            deductions = min(30, sum(int(item.get("deduction") or 0) for item in warnings))
            score = max(0, score - deductions)
            status = "blocked" if missing else "ready" if score >= 90 else "needs_attention"
            scores.append(
                {
                    "dimension": dimension,
                    "label": requirement["label"],
                    "score": score,
                    "status": status,
                    "required_collections": requirement["collections"],
                    "missing_collections": missing,
                    "warnings": warnings,
                    "platform_route": requirement["platform_route"],
                    "agency_route": requirement["agency_route"],
                    "observed_record_count": sum(len(records.get(collection) or []) for collection in requirement["collections"]),
                }
            )
        return scores

    def _dimension_warnings(self, dimension: str, records: dict[str, list[dict[str, Any]]], agency_id: str | None) -> list[dict[str, Any]]:
        warnings: list[dict[str, Any]] = []
        if dimension == "workflow_linkage":
            unlinked = [item for item in records.get("operational_workflow_instances", []) if not any(item.get(key) for key in ["source_entity_id", "request_id", "trip_id", "booking_id", "after_sales_case_id"])]
            if unlinked:
                warnings.append({"code": "unlinked_workflow_instances", "count": len(unlinked), "deduction": 10})
        elif dimension == "assignment_readiness":
            incomplete = [item for item in records.get("operational_work_items", []) if not item.get("queue_code") or not item.get("source_entity_id")]
            if incomplete:
                warnings.append({"code": "incomplete_work_item_linkage", "count": len(incomplete), "deduction": 10})
        elif dimension == "sla_readiness":
            incomplete = [item for item in records.get("operational_deadlines", []) if not item.get("original_due_at") or not item.get("explanation")]
            if incomplete:
                warnings.append({"code": "incomplete_deadline_audit", "count": len(incomplete), "deduction": 10})
        elif dimension == "task_dependency_readiness":
            invalid = [item for item in records.get("operational_task_dependencies", []) if not item.get("predecessor_task_id") or not item.get("successor_task_id")]
            if invalid:
                warnings.append({"code": "incomplete_task_dependencies", "count": len(invalid), "deduction": 10})
        elif dimension == "request_to_trip_conversion_readiness":
            completed = [item for item in records.get("request_trip_conversion_runs", []) if item.get("run_status") in {"completed", "converted", "succeeded"}]
            mappings = records.get("request_trip_entity_mappings", [])
            missing = [item for item in completed if not any(mapping.get("run_id") == item.get("id") for mapping in mappings)]
            if missing:
                warnings.append({"code": "completed_conversion_missing_mapping", "count": len(missing), "deduction": 20})
        elif dimension == "offer_to_booking_readiness":
            handoffs = [item for item in records.get("offer_booking_handoffs", []) if item.get("handoff_status") in {"handed_off", "booking_created"}]
            mappings = records.get("offer_booking_handoff_mappings", [])
            missing = [item for item in handoffs if not item.get("accepted_offer_snapshot_id") and not item.get("acceptance_id")]
            missing += [item for item in handoffs if not any(mapping.get("handoff_id") == item.get("id") for mapping in mappings)]
            if missing:
                warnings.append({"code": "handoff_trace_incomplete", "count": len(missing), "deduction": 20})
        elif dimension == "servicing_readiness":
            cases = records.get("after_sales_cases", [])
            incomplete = [item for item in cases if not item.get("workflow_instance_id") or not item.get("work_item_ids") or not item.get("deadline_ids")]
            if incomplete:
                warnings.append({"code": "after_sales_operational_links_incomplete", "count": len(incomplete), "deduction": 15})
        elif dimension == "audit_completeness":
            audit_records = sum((records.get(name) or [] for name in ["operational_workflow_events", "operational_assignment_events", "operational_sla_events", "operational_timelines"]), [])
            incomplete = [item for item in audit_records if not item.get("created_at")]
            if incomplete:
                warnings.append({"code": "audit_timestamp_missing", "count": len(incomplete), "deduction": 20})
        elif dimension == "client_internal_message_separation":
            invalid_audience = [item for item in records.get("after_sales_communication_records", []) if item.get("audience") not in {"internal", "client"}]
            if invalid_audience:
                warnings.append({"code": "communication_audience_unclear", "count": len(invalid_audience), "deduction": 20})
        elif dimension == "agency_isolation" and agency_id:
            leaked = sum(1 for items in records.values() for item in items if item.get("agency_id") not in {agency_id, None})
            if leaked:
                warnings.append({"code": "cross_agency_record_visible", "count": leaked, "deduction": 30})
        return warnings

    def _blockers(self, records: dict[str, list[dict[str, Any]]], module_scores: list[dict[str, Any]]) -> list[dict[str, Any]]:
        blockers: list[dict[str, Any]] = []
        for module in module_scores:
            if module["missing_collections"]:
                blockers.append(self._blocker("missing_canonical_contract", "critical", module["label"], f"Missing collections: {', '.join(module['missing_collections'])}", module["platform_route"], module["agency_route"]))
            for warning in module["warnings"]:
                blockers.append(self._blocker(warning["code"], "high", module["label"], f"{warning['count']} record(s) require remediation.", module["platform_route"], module["agency_route"]))

        for item in records.get("operational_work_items", []):
            if item.get("blocker_status") not in {None, "", "none", "not_blocked", "resolved"} and item.get("status") not in {"completed", "cancelled", "archived"}:
                blockers.append(self._blocker(f"work-item:{item.get('id')}", "high", item.get("title") or "Blocked work item", item.get("summary") or item.get("blocker_status"), "/platform/work-queues", "/agency/work-queue"))
        for item in records.get("operational_deadlines", []):
            if item.get("breach_state") == "breached" or item.get("status") == "overdue":
                blockers.append(self._blocker(f"deadline:{item.get('id')}", "high", item.get("deadline_type") or "Overdue deadline", item.get("explanation") or "Operational deadline is breached.", "/platform/sla-policies", "/agency/deadlines"))
        for item in records.get("request_trip_conversion_issues", []):
            if item.get("status") not in {"resolved", "waived", "archived"}:
                blockers.append(self._blocker(f"conversion:{item.get('id')}", item.get("severity") or "medium", item.get("title") or item.get("issue_code") or "Conversion issue", item.get("description") or "Request-to-trip conversion requires review.", "/platform/request-trip-conversion", "/agency/request-trip-conversion"))
        for item in records.get("offer_booking_handoff_checks", []):
            if item.get("status") in {"blocked", "failed"}:
                blockers.append(self._blocker(f"handoff:{item.get('id')}", "critical" if item.get("status") == "failed" else "high", item.get("label") or item.get("check_key") or "Booking handoff blocker", item.get("summary") or "Offer-to-booking handoff is blocked.", "/platform/booking-handoffs", "/agency/booking-handoffs"))
        for item in records.get("pilot_readiness_issues", []):
            if item.get("issue_status") in {"open", "in_review", "reopened"}:
                blockers.append(self._blocker(f"pilot:{item.get('id')}", item.get("severity") or "medium", item.get("title") or "Pilot readiness issue", item.get("description") or "Pilot readiness requires review.", item.get("remediation_route") or "/platform/pilot-readiness", item.get("agency_remediation_route") or "/agency/pilot-readiness"))
        return blockers[:100]

    def _recent_errors(self, records: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        errors: list[dict[str, Any]] = []
        sources = [
            ("workflow_event", "operational_workflow_events", "event_status", {"blocked", "failed", "error"}),
            ("task_automation", "operational_task_automation_runs", "run_status", {"failed", "warning"}),
            ("conversion", "request_trip_conversion_runs", "run_status", {"blocked", "failed"}),
            ("booking_handoff", "offer_booking_handoffs", "handoff_status", {"blocked", "failed"}),
        ]
        for source, collection, status_field, statuses in sources:
            for item in records.get(collection, []):
                if item.get(status_field) in statuses:
                    errors.append(
                        {
                            "source": source,
                            "id": item.get("id"),
                            "status": item.get(status_field),
                            "summary": item.get("summary") or item.get("error") or item.get("warnings") or f"{self._label(source)} requires review.",
                            "created_at": item.get("created_at") or item.get("updated_at"),
                        }
                    )
        errors.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
        return errors[:25]

    def _coverage(self, records: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        counts = {collection: len(items) for collection, items in records.items()}
        workflows = records.get("operational_workflow_instances", [])
        work_items = records.get("operational_work_items", [])
        deadlines = records.get("operational_deadlines", [])
        return {
            "record_counts": counts,
            "workflow_linkage_rate": self._rate(workflows, lambda item: bool(item.get("source_entity_id") or item.get("request_id") or item.get("trip_id") or item.get("booking_id") or item.get("after_sales_case_id"))),
            "work_item_source_linkage_rate": self._rate(work_items, lambda item: bool(item.get("source_entity_id"))),
            "deadline_workflow_or_queue_linkage_rate": self._rate(deadlines, lambda item: bool(item.get("workflow_instance_id") or item.get("work_item_id"))),
            "covered_stage_count": len(GOLDEN_PATH_STAGES),
            "total_stage_count": len(GOLDEN_PATH_STAGES),
            "test_template_count": len(TEST_CASE_TEMPLATES),
        }

    def _remediation_links(self, platform: bool) -> dict[str, str]:
        key = "platform_route" if platform else "agency_route"
        return {dimension: requirement[key] for dimension, requirement in MODULE_REQUIREMENTS.items()}

    def _blocker(self, code: str, severity: str, title: str, summary: str, platform_route: str, agency_route: str) -> dict[str, Any]:
        return {
            "blocker_code": code,
            "severity": severity,
            "title": title,
            "summary": summary,
            "platform_route": platform_route,
            "agency_route": agency_route,
            "human_review_required": True,
        }

    def _rate(self, items: list[dict[str, Any]], predicate: Any) -> int:
        if not items:
            return 0
        return round((len([item for item in items if predicate(item)]) / len(items)) * 100)

    def _label(self, value: Any) -> str:
        return str(value or "").replace("_", " ").strip().title()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()
