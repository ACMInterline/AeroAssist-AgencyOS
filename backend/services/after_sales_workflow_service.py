from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import (
    AfterSalesCase,
    AfterSalesCaseCreate,
    AfterSalesCaseItem,
    AfterSalesCaseItemCreate,
    AfterSalesCaseUpdate,
    AfterSalesCommunicationRecord,
    AfterSalesCommunicationRecordCreate,
    AfterSalesDecision,
    AfterSalesDecisionCreate,
    AfterSalesFinancialImpact,
    AfterSalesFinancialImpactCreate,
    AfterSalesResolution,
    AfterSalesResolutionCreate,
    OperationalDeadlineCreate,
    OperationalTaskAutomationRunRequest,
    OperationalTimelineCreate,
    OperationalWorkItemGenerateRequest,
    OperationalWorkflowEvent,
    OperationalWorkflowInstance,
    new_id,
)
from services.agent_work_queue_service import AgentWorkQueueService
from services.operational_sla_deadline_service import OperationalSlaDeadlineService
from services.task_automation_dependency_service import TaskAutomationDependencyService
from services.timeline_workspace_service import OperationalTimelineService


PHASE_LABEL = "phase_55_5_airline_distribution_pss_gds_ndc_capability_intelligence_foundation"

AFTER_SALES_CASES_COLLECTION = "after_sales_cases"
AFTER_SALES_CASE_ITEMS_COLLECTION = "after_sales_case_items"
AFTER_SALES_DECISIONS_COLLECTION = "after_sales_decisions"
AFTER_SALES_FINANCIAL_IMPACTS_COLLECTION = "after_sales_financial_impacts"
AFTER_SALES_RESOLUTIONS_COLLECTION = "after_sales_resolutions"
AFTER_SALES_COMMUNICATION_RECORDS_COLLECTION = "after_sales_communication_records"

CASE_TYPES = [
    "voluntary_change",
    "schedule_change",
    "cancellation",
    "refund",
    "ticket_exchange",
    "emd_exchange_refund",
    "claim",
    "service_amendment",
    "passenger_document_amendment",
    "disruption_irregular_operation",
]
CASE_STATUSES = [
    "opened",
    "assessing",
    "information_required",
    "supplier_contact_required",
    "client_decision_required",
    "quote_preparation",
    "awaiting_approval",
    "processing",
    "partially_resolved",
    "resolved",
    "rejected",
    "cancelled",
    "archived",
]
CASE_PRIORITIES = ["low", "normal", "high", "urgent", "critical"]
CASE_ITEM_TYPES = [
    "trip",
    "booking",
    "ticket",
    "emd",
    "passenger",
    "segment",
    "document",
    "ssr_osi",
    "refund_exchange_case",
    "trip_change_operation",
    "ticket_exchange_operation",
    "emd_exchange_operation",
    "claim",
    "other",
]
DECISION_STATUSES = ["draft", "needs_client_approval", "approved", "rejected", "deferred", "manual_review"]
FINANCIAL_IMPACT_TYPES = [
    "residual_value",
    "penalty",
    "fare_difference",
    "service_fee",
    "refundability",
    "supplier_fee",
    "tax_refund",
    "credit",
    "claim_amount",
    "other",
]
FINANCIAL_ESTIMATE_STATUSES = ["placeholder", "estimated", "manual_review", "pending_supplier", "confirmed_metadata"]
RESOLUTION_STATUSES = ["draft", "proposed", "awaiting_approval", "approved", "resolved", "rejected", "cancelled"]
COMMUNICATION_TYPES = ["internal_note", "client_message", "supplier_message", "airline_message", "document_request", "approval_request", "other"]


class AfterSalesWorkflowError(ValueError):
    pass


class AfterSalesWorkflowService:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.work_queue = AgentWorkQueueService(db)
        self.deadlines = OperationalSlaDeadlineService(db)
        self.task_automation = TaskAutomationDependencyService(db)
        self.timelines = OperationalTimelineService(db)

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "servicing_after_sales_workflow_foundation": True,
            "existing_change_exchange_foundation_reused": True,
            "ticket_workspace_reused": True,
            "emd_workspace_reused": True,
            "claim_case_metadata_supported": True,
            "communication_records_metadata_only": True,
            "internal_client_message_separation_enabled": True,
            "task_sla_queue_workflow_integration_enabled": True,
            "ticket_mutation_disabled": True,
            "emd_mutation_disabled": True,
            "financial_commitment_disabled": True,
            "provider_execution_disabled": True,
            "external_api_calls_disabled": True,
            "background_workers_disabled": True,
            "ai_disabled": True,
            "human_authority_final": True,
        }

    async def platform_dashboard(self, **filters: Any) -> dict[str, Any]:
        cases = await self.list_cases(**filters)
        return {
            "phase": PHASE_LABEL,
            "summary": await self.summary(**filters),
            "items": cases[:75],
            "recent_items": await self.list_case_items(agency_id=filters.get("agency_id"), limit=50),
            "recent_decisions": await self.list_decisions(agency_id=filters.get("agency_id"), limit=50),
            "recent_financial_impacts": await self.list_financial_impacts(agency_id=filters.get("agency_id"), limit=50),
            "recent_resolutions": await self.list_resolutions(agency_id=filters.get("agency_id"), limit=50),
            "recent_communications": await self.list_communications(agency_id=filters.get("agency_id"), limit=50),
            "platform_read_only_diagnostics": True,
            **self.safety_flags(),
        }

    async def agency_dashboard(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        scoped = {key: value for key, value in filters.items() if key != "agency_id"}
        cases = await self.list_cases(agency_id=agency_id, **scoped)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": await self.summary(agency_id=agency_id, **scoped),
            "items": cases,
            "recent_items": await self.list_case_items(agency_id=agency_id, limit=50),
            "recent_decisions": await self.list_decisions(agency_id=agency_id, limit=50),
            "recent_financial_impacts": await self.list_financial_impacts(agency_id=agency_id, limit=50),
            "recent_resolutions": await self.list_resolutions(agency_id=agency_id, limit=50),
            "recent_communications": await self.list_communications(agency_id=agency_id, limit=50),
            **self.safety_flags(),
        }

    async def create_case(self, payload: AfterSalesCaseCreate | dict[str, Any], user: dict, agency_id: str | None = None) -> dict[str, Any]:
        data = self._payload(payload)
        if agency_id:
            data["agency_id"] = agency_id
        self._validate_case(data)
        data.setdefault("case_reference", self._reference("ASC"))
        data["idempotency_key"] = data.get("idempotency_key") or self._idempotency_key(data)
        existing = await self.db.collection(AFTER_SALES_CASES_COLLECTION).find_one({"agency_id": data["agency_id"], "idempotency_key": data["idempotency_key"]})
        if existing:
            return {
                "phase": PHASE_LABEL,
                "case": await self.get_case(existing["id"], agency_id=data["agency_id"]),
                "idempotent_reused": True,
                **self.safety_flags(),
            }

        context = await self._resolve_context(data)
        opened_at = self._now()
        case = AfterSalesCase(
            **{
                **data,
                "case_status": self._norm(data.get("case_status") or "opened"),
                "case_priority": self._norm(data.get("case_priority") or "normal"),
                "impact_scope_json": context["impact_scope_json"],
                "coupon_status_snapshot_json": context["coupon_status_snapshot_json"],
                "approval_status": "awaiting_client" if data.get("client_approval_required") else "not_required",
                "opened_at": opened_at,
                "created_by": user.get("id"),
                "updated_by": user.get("id"),
            }
        )
        created = await self.db.collection(AFTER_SALES_CASES_COLLECTION).insert_one(case.model_dump(mode="json"))
        items = await self._store_initial_items(created, context, user)
        financial = await self._store_initial_financial_impact(created, data, user)
        decision = await self._store_initial_decision(created, data, user)
        communication = await self._store_initial_communication(created, data, user)
        resolution = await self._store_initial_resolution(created, user)
        integrations = await self._emit_integrations(created, items, user)
        updated = await self.db.collection(AFTER_SALES_CASES_COLLECTION).update_one(
            {"id": created["id"]},
            {
                "item_count": len(items),
                "decision_count": 1 if decision else 0,
                "financial_impact_count": 1 if financial else 0,
                "resolution_count": 1 if resolution else 0,
                "communication_count": 1 if communication else 0,
                "decision_ids": [decision["id"]] if decision else [],
                "financial_impact_ids": [financial["id"]] if financial else [],
                "resolution_ids": [resolution["id"]] if resolution else [],
                "communication_ids": [communication["id"]] if communication else [],
                "workflow_instance_id": integrations.get("workflow_instance_id"),
                "timeline_entry_ids": self._present([integrations.get("timeline_entry_id")]),
                "task_ids": integrations.get("task_ids") or [],
                "deadline_ids": self._present([integrations.get("deadline_id")]),
                "work_item_ids": self._present([integrations.get("work_item_id")]),
                "integration_snapshot_json": integrations,
                "updated_by": user.get("id"),
                **self.safety_flags(),
            },
        ) or created
        return {
            "phase": PHASE_LABEL,
            "case": await self.get_case(updated["id"], agency_id=updated["agency_id"]),
            "items": items,
            "decision": decision,
            "financial_impact": financial,
            "resolution": resolution,
            "communication": communication,
            "integrations": integrations,
            "idempotent_reused": False,
            **self.safety_flags(),
        }

    async def update_case(self, case_id: str, payload: AfterSalesCaseUpdate | dict[str, Any], user: dict, agency_id: str | None = None) -> dict[str, Any]:
        existing = await self._require_case(case_id, agency_id=agency_id)
        updates = self._payload(payload, exclude_unset=True)
        if not updates:
            raise AfterSalesWorkflowError("No after-sales case metadata updates were provided.")
        if updates.get("case_status"):
            updates["case_status"] = self._norm(updates["case_status"])
            if updates["case_status"] not in CASE_STATUSES:
                raise AfterSalesWorkflowError(f"Unsupported after-sales case status metadata: {updates['case_status']}.")
            if updates["case_status"] in {"resolved", "rejected", "cancelled", "archived"}:
                updates.setdefault("resolved_at", self._now())
        if updates.get("case_priority"):
            updates["case_priority"] = self._norm(updates["case_priority"])
            if updates["case_priority"] not in CASE_PRIORITIES:
                raise AfterSalesWorkflowError(f"Unsupported after-sales case priority metadata: {updates['case_priority']}.")
        if "client_approval_required" in updates and "approval_status" not in updates:
            updates["approval_status"] = "awaiting_client" if updates["client_approval_required"] else "not_required"
        updates["updated_by"] = user.get("id")
        updated = await self.db.collection(AFTER_SALES_CASES_COLLECTION).update_one({"id": existing["id"]}, updates)
        if not updated:
            raise AfterSalesWorkflowError("After-sales case metadata could not be updated.")
        await self._record_case_timeline(updated, "after_sales_case_updated", "After-sales case metadata updated.", user)
        return {"phase": PHASE_LABEL, "case": await self.get_case(updated["id"], agency_id=updated["agency_id"]), **self.safety_flags()}

    async def get_case(self, case_id: str, agency_id: str | None = None) -> dict[str, Any]:
        case = await self._require_case(case_id, agency_id=agency_id)
        return {
            **case,
            "items": await self.list_case_items(agency_id=case["agency_id"], case_id=case["id"]),
            "decisions": await self.list_decisions(agency_id=case["agency_id"], case_id=case["id"]),
            "financial_impacts": await self.list_financial_impacts(agency_id=case["agency_id"], case_id=case["id"]),
            "resolutions": await self.list_resolutions(agency_id=case["agency_id"], case_id=case["id"]),
            "communications": await self.list_communications(agency_id=case["agency_id"], case_id=case["id"]),
            **self.safety_flags(),
        }

    async def list_cases(
        self,
        agency_id: str | None = None,
        case_status: str | None = None,
        case_type: str | None = None,
        case_priority: str | None = None,
        trip_workspace_id: str | None = None,
        booking_workspace_id: str | None = None,
        ticket_workspace_id: str | None = None,
        emd_workspace_id: str | None = None,
        assigned_agent: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if case_status:
            filters["case_status"] = self._norm(case_status)
        if case_type:
            filters["case_type"] = self._norm(case_type)
        if case_priority:
            filters["case_priority"] = self._norm(case_priority)
        if trip_workspace_id:
            filters["trip_workspace_id"] = trip_workspace_id
        if booking_workspace_id:
            filters["booking_workspace_id"] = booking_workspace_id
        if assigned_agent:
            filters["assigned_agent"] = assigned_agent
        records = await self.db.collection(AFTER_SALES_CASES_COLLECTION).find_many(filters)
        if ticket_workspace_id:
            records = [record for record in records if ticket_workspace_id in (record.get("ticket_workspace_ids") or [])]
        if emd_workspace_id:
            records = [record for record in records if emd_workspace_id in (record.get("emd_workspace_ids") or [])]
        records.sort(key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""), reverse=True)
        return [{**record, **self.safety_flags()} for record in records[:limit]]

    async def summary(self, agency_id: str | None = None, **filters: Any) -> dict[str, Any]:
        cases = await self.list_cases(agency_id=agency_id, limit=1000, **{key: value for key, value in filters.items() if key in {"case_status", "case_type", "case_priority", "trip_workspace_id", "booking_workspace_id", "ticket_workspace_id", "emd_workspace_id", "assigned_agent"}})
        return {
            "case_count": len(cases),
            "by_status": self._counts(cases, "case_status", CASE_STATUSES),
            "by_type": self._counts(cases, "case_type", CASE_TYPES),
            "by_priority": self._counts(cases, "case_priority", CASE_PRIORITIES),
            "requires_supplier_communication_count": len([case for case in cases if case.get("supplier_communication_required")]),
            "requires_client_approval_count": len([case for case in cases if case.get("client_approval_required")]),
            "open_case_count": len([case for case in cases if case.get("case_status") not in {"resolved", "rejected", "cancelled", "archived"}]),
            "metadata_only": True,
        }

    async def create_case_item(self, case_id: str, payload: AfterSalesCaseItemCreate | dict[str, Any], user: dict, agency_id: str | None = None) -> dict[str, Any]:
        case = await self._require_case(case_id, agency_id=agency_id)
        item = await self._create_item(case, self._payload(payload), user)
        await self._refresh_case_child_links(case["id"], user)
        return {"phase": PHASE_LABEL, "item": item, **self.safety_flags()}

    async def create_decision(self, case_id: str, payload: AfterSalesDecisionCreate | dict[str, Any], user: dict, agency_id: str | None = None) -> dict[str, Any]:
        case = await self._require_case(case_id, agency_id=agency_id)
        decision = await self._create_decision(case, self._payload(payload), user)
        await self._refresh_case_child_links(case["id"], user)
        await self._record_case_timeline(case, "after_sales_decision_recorded", decision.get("decision_summary") or "After-sales decision metadata recorded.", user)
        return {"phase": PHASE_LABEL, "decision": decision, **self.safety_flags()}

    async def create_financial_impact(self, case_id: str, payload: AfterSalesFinancialImpactCreate | dict[str, Any], user: dict, agency_id: str | None = None) -> dict[str, Any]:
        case = await self._require_case(case_id, agency_id=agency_id)
        impact = await self._create_financial_impact(case, self._payload(payload), user)
        await self._refresh_case_child_links(case["id"], user)
        return {"phase": PHASE_LABEL, "financial_impact": impact, **self.safety_flags()}

    async def create_resolution(self, case_id: str, payload: AfterSalesResolutionCreate | dict[str, Any], user: dict, agency_id: str | None = None) -> dict[str, Any]:
        case = await self._require_case(case_id, agency_id=agency_id)
        data = self._payload(payload)
        self._guard_resolution_mutation(data)
        resolution = await self._create_resolution(case, data, user)
        await self._refresh_case_child_links(case["id"], user)
        await self._record_case_timeline(case, "after_sales_resolution_recorded", resolution.get("resolution_summary") or "After-sales resolution metadata recorded.", user)
        return {"phase": PHASE_LABEL, "resolution": resolution, **self.safety_flags()}

    async def create_communication(self, case_id: str, payload: AfterSalesCommunicationRecordCreate | dict[str, Any], user: dict, agency_id: str | None = None) -> dict[str, Any]:
        case = await self._require_case(case_id, agency_id=agency_id)
        data = self._payload(payload)
        if data.get("sent_externally"):
            raise AfterSalesWorkflowError("After-sales communication records are metadata-only; external sending is disabled.")
        communication = await self._create_communication(case, data, user)
        await self._refresh_case_child_links(case["id"], user)
        await self._record_case_timeline(case, "after_sales_communication_recorded", communication.get("summary") or "After-sales communication metadata recorded.", user)
        return {"phase": PHASE_LABEL, "communication": communication, **self.safety_flags()}

    async def list_case_items(self, agency_id: str | None = None, case_id: str | None = None, item_type: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        return await self._list_child(AFTER_SALES_CASE_ITEMS_COLLECTION, agency_id=agency_id, case_id=case_id, field="item_type", value=item_type, limit=limit)

    async def list_decisions(self, agency_id: str | None = None, case_id: str | None = None, decision_status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        return await self._list_child(AFTER_SALES_DECISIONS_COLLECTION, agency_id=agency_id, case_id=case_id, field="decision_status", value=decision_status, limit=limit)

    async def list_financial_impacts(self, agency_id: str | None = None, case_id: str | None = None, impact_type: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        return await self._list_child(AFTER_SALES_FINANCIAL_IMPACTS_COLLECTION, agency_id=agency_id, case_id=case_id, field="impact_type", value=impact_type, limit=limit)

    async def list_resolutions(self, agency_id: str | None = None, case_id: str | None = None, resolution_status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        return await self._list_child(AFTER_SALES_RESOLUTIONS_COLLECTION, agency_id=agency_id, case_id=case_id, field="resolution_status", value=resolution_status, limit=limit)

    async def list_communications(self, agency_id: str | None = None, case_id: str | None = None, communication_type: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        return await self._list_child(AFTER_SALES_COMMUNICATION_RECORDS_COLLECTION, agency_id=agency_id, case_id=case_id, field="communication_type", value=communication_type, limit=limit)

    async def _resolve_context(self, data: dict[str, Any]) -> dict[str, Any]:
        linked: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        coupon_snapshots: list[dict[str, Any]] = []

        async def collect(collection: str, entity_type: str, entity_id: str | None, item_type: str, id_field: str | None = None) -> None:
            if not entity_id:
                return
            record = await self.db.collection(collection).find_one({"id": entity_id, "agency_id": data["agency_id"]})
            if record:
                linked.append({"item_type": item_type, "source_entity_type": entity_type, "source_entity_id": entity_id, "snapshot": self._compact_snapshot(record)})
            else:
                warnings.append({"code": "linked_record_not_found", "entity_type": entity_type, "entity_id": entity_id, "severity": "warning"})
            if id_field:
                return

        await collect("trip_workspaces", "trip_workspace", data.get("trip_workspace_id"), "trip")
        await collect("booking_workspaces", "booking_workspace", data.get("booking_workspace_id"), "booking")
        await collect("refund_exchange_cases", "refund_exchange_case", data.get("refund_exchange_case_id"), "refund_exchange_case")
        await collect("trip_change_operations", "trip_change_operation", data.get("trip_change_operation_id"), "trip_change_operation")
        await collect("ticket_exchange_operations", "ticket_exchange_operation", data.get("ticket_exchange_operation_id"), "ticket_exchange_operation")
        await collect("emd_exchange_operations", "emd_exchange_operation", data.get("emd_exchange_operation_id"), "emd_exchange_operation")

        for ticket_id in data.get("ticket_workspace_ids") or []:
            record = await self.db.collection("ticket_workspaces").find_one({"id": ticket_id, "agency_id": data["agency_id"]})
            if record:
                linked.append({"item_type": "ticket", "source_entity_type": "ticket_workspace", "source_entity_id": ticket_id, "snapshot": self._compact_snapshot(record)})
                coupon_snapshots.append(
                    {
                        "ticket_workspace_id": ticket_id,
                        "ticket_document_status": record.get("ticket_document_status") or record.get("ticket_status"),
                        "coupon_status_summary": record.get("coupon_status_summary"),
                        "coupon_details": record.get("coupon_details") or [],
                    }
                )
            else:
                warnings.append({"code": "linked_ticket_workspace_not_found", "entity_type": "ticket_workspace", "entity_id": ticket_id, "severity": "warning"})

        for emd_id in data.get("emd_workspace_ids") or []:
            record = await self.db.collection("emd_workspaces").find_one({"id": emd_id, "agency_id": data["agency_id"]})
            if record:
                linked.append({"item_type": "emd", "source_entity_type": "emd_workspace", "source_entity_id": emd_id, "snapshot": self._compact_snapshot(record)})
                coupon_snapshots.append(
                    {
                        "emd_workspace_id": emd_id,
                        "document_status": record.get("emd_document_status") or record.get("emd_status"),
                        "coupon_status_summary": record.get("coupon_status_summary") or record.get("emd_coupon_status_summary"),
                        "coupon_details": record.get("coupon_details") or record.get("emd_coupon_details") or [],
                    }
                )
            else:
                warnings.append({"code": "linked_emd_workspace_not_found", "entity_type": "emd_workspace", "entity_id": emd_id, "severity": "warning"})

        list_links = [
            ("passenger_workspaces", "passenger_workspace", "passenger_workspace_ids", "passenger"),
            ("document_workspaces", "document_workspace", "document_workspace_ids", "document"),
            ("ssr_osi_workspaces", "ssr_osi_workspace", "ssr_osi_workspace_ids", "ssr_osi"),
        ]
        for collection, entity_type, field, item_type in list_links:
            for entity_id in data.get(field) or []:
                record = await self.db.collection(collection).find_one({"id": entity_id, "agency_id": data["agency_id"]})
                if record:
                    linked.append({"item_type": item_type, "source_entity_type": entity_type, "source_entity_id": entity_id, "snapshot": self._compact_snapshot(record)})
                else:
                    warnings.append({"code": f"linked_{entity_type}_not_found", "entity_type": entity_type, "entity_id": entity_id, "severity": "warning"})

        for segment_ref in data.get("affected_segment_refs") or []:
            linked.append({"item_type": "segment", "source_entity_type": "segment_reference", "source_entity_id": segment_ref, "snapshot": {"segment_reference": segment_ref}})

        return {
            "linked_records": linked,
            "impact_scope_json": {
                "linked_record_count": len(linked),
                "warnings": warnings,
                "trip_workspace_id": data.get("trip_workspace_id"),
                "booking_workspace_id": data.get("booking_workspace_id"),
                "ticket_workspace_ids": data.get("ticket_workspace_ids") or [],
                "emd_workspace_ids": data.get("emd_workspace_ids") or [],
                "passenger_workspace_ids": data.get("passenger_workspace_ids") or [],
                "document_workspace_ids": data.get("document_workspace_ids") or [],
                "ssr_osi_workspace_ids": data.get("ssr_osi_workspace_ids") or [],
                "affected_segment_refs": data.get("affected_segment_refs") or [],
                "metadata_only": True,
            },
            "coupon_status_snapshot_json": {"coupon_status_aware": True, "snapshots": coupon_snapshots, "metadata_only": True},
        }

    async def _store_initial_items(self, case: dict[str, Any], context: dict[str, Any], user: dict) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for item in context.get("linked_records") or []:
            payload = {
                "item_type": item["item_type"],
                "source_entity_type": item["source_entity_type"],
                "source_entity_id": item["source_entity_id"],
                "impact_type": "case_scope",
                "impact_status": "linked",
                "impact_summary": f"{self._label(item['item_type'])} linked to after-sales case metadata.",
                "snapshot_json": item.get("snapshot") or {},
            }
            items.append(await self._create_item(case, payload, user))
        if not items:
            items.append(
                await self._create_item(
                    case,
                    {
                        "item_type": "other",
                        "source_entity_type": "after_sales_case",
                        "source_entity_id": case["id"],
                        "impact_type": "manual_review",
                        "impact_status": "warning",
                        "impact_summary": "No affected operational records were linked; manual impact scoping is required.",
                        "snapshot_json": {"manual_review_required": True, "metadata_only": True},
                    },
                    user,
                )
            )
        return items

    async def _store_initial_financial_impact(self, case: dict[str, Any], data: dict[str, Any], user: dict) -> dict[str, Any]:
        payload = {
            "impact_type": "refundability" if data.get("refundability_summary") else "other",
            "estimate_status": "placeholder",
            "direction": "neutral",
            "calculation_basis": "Manual after-sales review placeholder; no fare recalculation or financial commitment is performed.",
            "placeholder_notes": self._join_notes(
                [
                    data.get("residual_value_summary"),
                    data.get("penalty_summary"),
                    data.get("fare_difference_summary"),
                    data.get("service_fee_summary"),
                    data.get("refundability_summary"),
                ]
            ),
            "metadata": {"financial_estimate_json": data.get("financial_estimate_json") or {}},
        }
        return await self._create_financial_impact(case, payload, user)

    async def _store_initial_decision(self, case: dict[str, Any], data: dict[str, Any], user: dict) -> dict[str, Any]:
        payload = {
            "decision_type": "client_approval" if data.get("client_approval_required") else "manual_review",
            "decision_status": "needs_client_approval" if data.get("client_approval_required") else "manual_review",
            "decision_summary": "Client approval is required before any future authorized after-sales action." if data.get("client_approval_required") else "Manual after-sales review decision placeholder.",
            "decision_reason": data.get("case_summary"),
            "requires_client_approval": bool(data.get("client_approval_required")),
            "client_approval_status": "awaiting_client" if data.get("client_approval_required") else "not_required",
            "approval_guard_json": {
                "no_automatic_financial_commitment": True,
                "no_ticket_or_emd_mutation": True,
                "explicit_authorized_action_required_for_future_execution": True,
                "metadata_only": True,
            },
        }
        return await self._create_decision(case, payload, user)

    async def _store_initial_communication(self, case: dict[str, Any], data: dict[str, Any], user: dict) -> dict[str, Any] | None:
        if not data.get("internal_message_json") and not data.get("client_message_json") and not data.get("supplier_communication_required"):
            return None
        payload = {
            "communication_type": "client_message" if data.get("client_message_json") else "internal_note",
            "direction": "outbound" if data.get("client_message_json") else "internal",
            "audience": "client" if data.get("client_message_json") else "internal",
            "channel": "metadata",
            "summary": "After-sales communication metadata placeholder.",
            "internal_message": str(data.get("internal_message_json") or "") or None,
            "client_message": str(data.get("client_message_json") or "") or None,
            "metadata": {"supplier_communication_required": bool(data.get("supplier_communication_required"))},
        }
        return await self._create_communication(case, payload, user)

    async def _store_initial_resolution(self, case: dict[str, Any], user: dict) -> dict[str, Any]:
        return await self._create_resolution(
            case,
            {
                "resolution_type": "manual_resolution",
                "resolution_status": "draft",
                "resolution_summary": "Resolution placeholder only. Ticket, EMD, and financial mutations are disabled in Phase 54.7.",
                "outcome_json": {"metadata_only": True, "future_authorized_action_required": True},
            },
            user,
        )

    async def _emit_integrations(self, case: dict[str, Any], items: list[dict[str, Any]], user: dict) -> dict[str, Any]:
        integrations: dict[str, Any] = {"metadata_only": True}
        workflow = OperationalWorkflowInstance(
            agency_id=case["agency_id"],
            workflow_definition_id="after_sales_servicing_metadata_workflow",
            entity_type="after_sales_case",
            entity_id=case["id"],
            current_state=case.get("case_status") or "opened",
            workflow_status="active",
            context_snapshot_json=self._integration_snapshot(case, items),
            active_blockers_json=self._active_blockers(case),
            active_warnings_json=(case.get("impact_scope_json") or {}).get("warnings") or [],
            started_at=self._now(),
            created_by=user.get("id"),
            updated_by=user.get("id"),
            metadata={"phase": PHASE_LABEL, "metadata_only": True},
        )
        workflow_created = await self.db.collection("operational_workflow_instances").insert_one(workflow.model_dump(mode="json"))
        integrations["workflow_instance_id"] = workflow_created["id"]
        workflow_event = OperationalWorkflowEvent(
            agency_id=case["agency_id"],
            workflow_instance_id=workflow_created["id"],
            event_type="after_sales_case_opened",
            event_code=f"after_sales_case_opened:{case['id']}",
            source_module="after_sales_workflow",
            source_entity_type="after_sales_case",
            source_entity_id=case["id"],
            payload_json=self._integration_snapshot(case, items),
            metadata={"phase": PHASE_LABEL, "metadata_only": True},
        )
        event_created = await self.db.collection("operational_workflow_events").insert_one(workflow_event.model_dump(mode="json"))
        integrations["workflow_event_id"] = event_created["id"]

        work_item = await self.work_queue.generate_work_item(
            OperationalWorkItemGenerateRequest(
                agency_id=case["agency_id"],
                work_item_type=self._work_item_type(case),
                source_entity_type="after_sales_case",
                source_entity_id=case["id"],
                workflow_instance_id=workflow_created["id"],
                workflow_event_id=event_created["id"],
                title=case.get("case_title") or "After-sales case",
                summary=case.get("case_summary") or "After-sales case requires human servicing review.",
                priority=case.get("case_priority") or "normal",
                severity="high" if case.get("case_priority") in {"urgent", "critical"} else "medium",
                queue_code=self._queue_code(case),
                blocker_status=self._blocker_status(case),
                generation_reason="after_sales_case_opened",
                source_snapshot_json=self._integration_snapshot(case, items),
                compatibility_mapping_json={"after_sales_case_id": case["id"], "workflow_instance_id": workflow_created["id"]},
                metadata={"phase": PHASE_LABEL, "metadata_only": True},
            ),
            user,
            agency_id=case["agency_id"],
        )
        integrations["work_item_id"] = (work_item.get("work_item") or {}).get("id")

        deadline_type = "disruption_response_deadline" if case.get("case_type") == "disruption_irregular_operation" else "claim_refund_change_deadline"
        deadline = await self.deadlines.create_deadline(
            OperationalDeadlineCreate(
                agency_id=case["agency_id"],
                source_entity_type="after_sales_case",
                source_entity_id=case["id"],
                workflow_instance_id=workflow_created["id"],
                workflow_event_id=event_created["id"],
                work_item_id=integrations.get("work_item_id"),
                deadline_type=deadline_type,
                priority=case.get("case_priority") or "normal",
                started_at=self._now(),
                source_snapshot_json=self._integration_snapshot(case, items),
                metadata={"phase": PHASE_LABEL, "metadata_only": True},
            ),
            user,
            agency_id=case["agency_id"],
        )
        integrations["deadline_id"] = (deadline.get("deadline") or {}).get("id")

        task_run = await self.task_automation.run_automation(
            OperationalTaskAutomationRunRequest(
                agency_id=case["agency_id"],
                trigger_event="after_sales_case_opened",
                source_entity_type="after_sales_case",
                source_entity_id=case["id"],
                idempotency_key=f"after-sales:{case['id']}:case-opened",
                event_snapshot_json={
                    "source_label": case.get("case_title"),
                    "case_type": case.get("case_type"),
                    "priority": case.get("case_priority"),
                    "metadata_only": True,
                },
                metadata={"phase": PHASE_LABEL, "metadata_only": True},
            ),
            user,
            agency_id=case["agency_id"],
        )
        integrations["task_automation_run_id"] = (task_run.get("run") or {}).get("id")
        integrations["task_ids"] = [task.get("task_id") for task in ((task_run.get("run") or {}).get("tasks_created") or []) if task.get("task_id")]

        timeline = await self.timelines.create_entry(
            OperationalTimelineCreate(
                agency_id=case["agency_id"],
                timeline_reference=self._reference("ASTL"),
                created_by=user.get("id"),
                passenger_workspace_id=(case.get("passenger_workspace_ids") or [None])[0],
                trip_workspace_id=case.get("trip_workspace_id"),
                booking_workspace_id=case.get("booking_workspace_id"),
                ticket_workspace_id=(case.get("ticket_workspace_ids") or [None])[0],
                emd_workspace_id=(case.get("emd_workspace_ids") or [None])[0],
                document_workspace_id=(case.get("document_workspace_ids") or [None])[0],
                event_type="after_sales_case_opened",
                event_category="servicing_after_sales",
                event_source="after_sales_workflow",
                event_status="recorded",
                event_priority=case.get("case_priority") or "normal",
                operational_stage="servicing_after_sales",
                operational_result=case.get("case_status") or "opened",
                summary=case.get("case_summary") or case.get("case_title"),
                internal_only=True,
                passenger_visible=False,
                airline_visible=False,
                operational_notes="Metadata-only after-sales timeline entry; no external messages were sent.",
                metadata={"after_sales_case_id": case["id"], "phase": PHASE_LABEL, "metadata_only": True},
            ),
            user,
        )
        integrations["timeline_entry_id"] = (timeline.get("timeline_entry") or {}).get("id")
        return integrations

    async def _create_item(self, case: dict[str, Any], payload: dict[str, Any], user: dict) -> dict[str, Any]:
        data = {**payload}
        data["item_type"] = self._norm(data.get("item_type") or "other")
        if data["item_type"] not in CASE_ITEM_TYPES:
            raise AfterSalesWorkflowError(f"Unsupported after-sales item type metadata: {data['item_type']}.")
        item = AfterSalesCaseItem(
            agency_id=case["agency_id"],
            case_id=case["id"],
            case_reference=case.get("case_reference"),
            created_by=user.get("id"),
            updated_by=user.get("id"),
            **data,
        )
        return await self.db.collection(AFTER_SALES_CASE_ITEMS_COLLECTION).insert_one(item.model_dump(mode="json"))

    async def _create_decision(self, case: dict[str, Any], payload: dict[str, Any], user: dict) -> dict[str, Any]:
        data = {**payload}
        data.setdefault("decision_reference", self._reference("ASD"))
        data["decision_status"] = self._norm(data.get("decision_status") or "draft")
        if data["decision_status"] not in DECISION_STATUSES:
            raise AfterSalesWorkflowError(f"Unsupported after-sales decision status metadata: {data['decision_status']}.")
        data["approval_guard_json"] = {
            "no_automatic_financial_commitment": True,
            "no_ticket_or_emd_mutation": True,
            "explicit_authorized_action_required_for_future_execution": True,
            "metadata_only": True,
            **(data.get("approval_guard_json") or {}),
        }
        decision = AfterSalesDecision(
            agency_id=case["agency_id"],
            case_id=case["id"],
            created_by=user.get("id"),
            updated_by=user.get("id"),
            **data,
        )
        return await self.db.collection(AFTER_SALES_DECISIONS_COLLECTION).insert_one(decision.model_dump(mode="json"))

    async def _create_financial_impact(self, case: dict[str, Any], payload: dict[str, Any], user: dict) -> dict[str, Any]:
        data = {**payload}
        data.setdefault("impact_reference", self._reference("ASF"))
        data["impact_type"] = self._norm(data.get("impact_type") or "other")
        data["estimate_status"] = self._norm(data.get("estimate_status") or "placeholder")
        if data["impact_type"] not in FINANCIAL_IMPACT_TYPES:
            raise AfterSalesWorkflowError(f"Unsupported after-sales financial impact type metadata: {data['impact_type']}.")
        if data["estimate_status"] not in FINANCIAL_ESTIMATE_STATUSES:
            raise AfterSalesWorkflowError(f"Unsupported after-sales financial estimate status metadata: {data['estimate_status']}.")
        impact = AfterSalesFinancialImpact(
            agency_id=case["agency_id"],
            case_id=case["id"],
            created_by=user.get("id"),
            updated_by=user.get("id"),
            **data,
        )
        return await self.db.collection(AFTER_SALES_FINANCIAL_IMPACTS_COLLECTION).insert_one(impact.model_dump(mode="json"))

    async def _create_resolution(self, case: dict[str, Any], payload: dict[str, Any], user: dict) -> dict[str, Any]:
        data = {**payload}
        self._guard_resolution_mutation(data)
        data.setdefault("resolution_reference", self._reference("ASR"))
        data["resolution_status"] = self._norm(data.get("resolution_status") or "draft")
        if data["resolution_status"] not in RESOLUTION_STATUSES:
            raise AfterSalesWorkflowError(f"Unsupported after-sales resolution status metadata: {data['resolution_status']}.")
        resolution = AfterSalesResolution(
            agency_id=case["agency_id"],
            case_id=case["id"],
            created_by=user.get("id"),
            updated_by=user.get("id"),
            **data,
        )
        return await self.db.collection(AFTER_SALES_RESOLUTIONS_COLLECTION).insert_one(resolution.model_dump(mode="json"))

    async def _create_communication(self, case: dict[str, Any], payload: dict[str, Any], user: dict) -> dict[str, Any]:
        data = {**payload}
        if data.get("sent_externally"):
            raise AfterSalesWorkflowError("After-sales communication records are metadata-only; external sending is disabled.")
        data.setdefault("communication_reference", self._reference("ASCMM"))
        data["communication_type"] = self._norm(data.get("communication_type") or "internal_note")
        if data["communication_type"] not in COMMUNICATION_TYPES:
            raise AfterSalesWorkflowError(f"Unsupported after-sales communication type metadata: {data['communication_type']}.")
        communication = AfterSalesCommunicationRecord(
            agency_id=case["agency_id"],
            case_id=case["id"],
            created_by=user.get("id"),
            updated_by=user.get("id"),
            **data,
        )
        return await self.db.collection(AFTER_SALES_COMMUNICATION_RECORDS_COLLECTION).insert_one(communication.model_dump(mode="json"))

    async def _refresh_case_child_links(self, case_id: str, user: dict) -> None:
        case = await self._require_case(case_id)
        items = await self.list_case_items(agency_id=case["agency_id"], case_id=case_id, limit=1000)
        decisions = await self.list_decisions(agency_id=case["agency_id"], case_id=case_id, limit=1000)
        impacts = await self.list_financial_impacts(agency_id=case["agency_id"], case_id=case_id, limit=1000)
        resolutions = await self.list_resolutions(agency_id=case["agency_id"], case_id=case_id, limit=1000)
        communications = await self.list_communications(agency_id=case["agency_id"], case_id=case_id, limit=1000)
        await self.db.collection(AFTER_SALES_CASES_COLLECTION).update_one(
            {"id": case_id},
            {
                "item_count": len(items),
                "decision_count": len(decisions),
                "financial_impact_count": len(impacts),
                "resolution_count": len(resolutions),
                "communication_count": len(communications),
                "decision_ids": [item["id"] for item in decisions],
                "financial_impact_ids": [item["id"] for item in impacts],
                "resolution_ids": [item["id"] for item in resolutions],
                "communication_ids": [item["id"] for item in communications],
                "updated_by": user.get("id"),
            },
        )

    async def _record_case_timeline(self, case: dict[str, Any], event_type: str, summary: str, user: dict) -> None:
        timeline = await self.timelines.create_entry(
            OperationalTimelineCreate(
                agency_id=case["agency_id"],
                timeline_reference=self._reference("ASTL"),
                created_by=user.get("id"),
                passenger_workspace_id=(case.get("passenger_workspace_ids") or [None])[0],
                trip_workspace_id=case.get("trip_workspace_id"),
                booking_workspace_id=case.get("booking_workspace_id"),
                ticket_workspace_id=(case.get("ticket_workspace_ids") or [None])[0],
                emd_workspace_id=(case.get("emd_workspace_ids") or [None])[0],
                document_workspace_id=(case.get("document_workspace_ids") or [None])[0],
                event_type=event_type,
                event_category="servicing_after_sales",
                event_source="after_sales_workflow",
                event_status="recorded",
                event_priority=case.get("case_priority") or "normal",
                summary=summary,
                internal_only=True,
                operational_notes="Metadata-only after-sales timeline entry.",
                metadata={"after_sales_case_id": case["id"], "phase": PHASE_LABEL, "metadata_only": True},
            ),
            user,
        )
        timeline_id = (timeline.get("timeline_entry") or {}).get("id")
        if timeline_id:
            existing = await self._require_case(case["id"], agency_id=case["agency_id"])
            ids = self._present((existing.get("timeline_entry_ids") or []) + [timeline_id])
            await self.db.collection(AFTER_SALES_CASES_COLLECTION).update_one({"id": case["id"]}, {"timeline_entry_ids": ids, "updated_by": user.get("id")})

    async def _list_child(self, collection: str, agency_id: str | None = None, case_id: str | None = None, field: str | None = None, value: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if case_id:
            filters["case_id"] = case_id
        if field and value:
            filters[field] = self._norm(value)
        records = await self.db.collection(collection).find_many(filters)
        records.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
        return [{**record, **self.safety_flags()} for record in records[:limit]]

    async def _require_case(self, case_id: str, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": case_id}
        if agency_id:
            filters["agency_id"] = agency_id
        case = await self.db.collection(AFTER_SALES_CASES_COLLECTION).find_one(filters)
        if not case:
            raise AfterSalesWorkflowError("After-sales case metadata was not found.")
        return case

    def _validate_case(self, data: dict[str, Any]) -> None:
        for field in ["agency_id", "case_type", "case_title"]:
            if not data.get(field):
                raise AfterSalesWorkflowError(f"{field} is required for after-sales case metadata.")
        data["case_type"] = self._norm(data["case_type"])
        data["case_status"] = self._norm(data.get("case_status") or "opened")
        data["case_priority"] = self._norm(data.get("case_priority") or "normal")
        if data["case_type"] not in CASE_TYPES:
            raise AfterSalesWorkflowError(f"Unsupported after-sales case type metadata: {data['case_type']}.")
        if data["case_status"] not in CASE_STATUSES:
            raise AfterSalesWorkflowError(f"Unsupported after-sales case status metadata: {data['case_status']}.")
        if data["case_priority"] not in CASE_PRIORITIES:
            raise AfterSalesWorkflowError(f"Unsupported after-sales case priority metadata: {data['case_priority']}.")

    def _guard_resolution_mutation(self, data: dict[str, Any]) -> None:
        forbidden = [
            "ticket_mutation_authorized",
            "ticket_mutation_performed",
            "emd_mutation_authorized",
            "emd_mutation_performed",
            "financial_commitment_authorized",
            "financial_commitment_performed",
        ]
        requested = [field for field in forbidden if data.get(field)]
        if requested:
            raise AfterSalesWorkflowError(
                "Phase 54.7 records resolution metadata only; ticket/EMD mutation and financial commitment flags cannot be set true."
            )

    def _integration_snapshot(self, case: dict[str, Any], items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "after_sales_case_id": case.get("id"),
            "case_reference": case.get("case_reference"),
            "case_type": case.get("case_type"),
            "case_status": case.get("case_status"),
            "case_priority": case.get("case_priority"),
            "item_count": len(items),
            "client_approval_required": case.get("client_approval_required"),
            "supplier_communication_required": case.get("supplier_communication_required"),
            "impact_scope_json": case.get("impact_scope_json") or {},
            "coupon_status_snapshot_json": case.get("coupon_status_snapshot_json") or {},
            "metadata_only": True,
            "ticket_mutation_disabled": True,
            "financial_commitment_disabled": True,
        }

    def _active_blockers(self, case: dict[str, Any]) -> list[dict[str, Any]]:
        blockers: list[dict[str, Any]] = []
        if case.get("client_approval_required"):
            blockers.append({"code": "client_approval_required", "severity": "warning", "message": "Client approval is required before any future servicing action."})
        if case.get("supplier_communication_required"):
            blockers.append({"code": "supplier_contact_required", "severity": "warning", "message": "Supplier or airline contact is required for after-sales review."})
        return blockers

    def _work_item_type(self, case: dict[str, Any]) -> str:
        if case.get("case_type") == "disruption_irregular_operation":
            return "disruption"
        if case.get("case_type") in {"claim", "refund", "ticket_exchange", "emd_exchange_refund"}:
            return "claim_service_case"
        return "manual"

    def _queue_code(self, case: dict[str, Any]) -> str:
        if case.get("case_type") == "disruption_irregular_operation":
            return "disruption_queue"
        if case.get("client_approval_required"):
            return "waiting_approval"
        if case.get("supplier_communication_required"):
            return "waiting_airline_supplier"
        return "service_case_queue"

    def _blocker_status(self, case: dict[str, Any]) -> str:
        if case.get("client_approval_required"):
            return "waiting_approval"
        if case.get("supplier_communication_required"):
            return "waiting_airline_supplier"
        return "manual_review"

    def _idempotency_key(self, data: dict[str, Any]) -> str:
        source = data.get("source_entity_id") or data.get("booking_workspace_id") or data.get("trip_workspace_id") or data.get("case_title")
        return f"{data['agency_id']}:{self._norm(data['case_type'])}:{source}"

    def _reference(self, prefix: str) -> str:
        return f"{prefix}-{new_id()[:8].upper()}"

    def _compact_snapshot(self, record: dict[str, Any]) -> dict[str, Any]:
        keys = [
            "id",
            "agency_id",
            "workspace_reference",
            "trip_reference",
            "booking_reference",
            "ticket_reference",
            "emd_reference",
            "passenger_reference",
            "document_reference",
            "case_reference",
            "status",
            "trip_status",
            "booking_status",
            "ticket_status",
            "ticket_document_status",
            "emd_status",
            "emd_document_status",
            "coupon_status_summary",
            "passenger_name",
            "airline_pnr",
            "gds_record_locator",
            "created_at",
            "updated_at",
        ]
        return {key: record.get(key) for key in keys if key in record}

    def _payload(self, payload: Any, *, exclude_unset: bool = False) -> dict[str, Any]:
        if hasattr(payload, "model_dump"):
            return payload.model_dump(mode="json", exclude_none=True, exclude_unset=exclude_unset)
        return {key: value for key, value in dict(payload or {}).items() if value is not None}

    def _counts(self, records: list[dict[str, Any]], field: str, allowed: list[str]) -> dict[str, int]:
        return {value: len([record for record in records if record.get(field) == value]) for value in allowed}

    def _present(self, values: list[str | None]) -> list[str]:
        seen: list[str] = []
        for value in values:
            if value and value not in seen:
                seen.append(value)
        return seen

    def _join_notes(self, values: list[str | None]) -> str | None:
        notes = [value for value in values if value]
        return " | ".join(notes) if notes else None

    def _label(self, value: str) -> str:
        return self._norm(value).replace("_", " ").title()

    def _norm(self, value: Any) -> str:
        return str(value or "").strip().lower().replace(" ", "_").replace("/", "_").replace("-", "_")

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)
