from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from database import Database
from persistence_query import MAXIMUM_QUERY_LIMIT, PaginationRequest
from persistence_repository import PersistenceRepository
from models import (
    AuditEvent,
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
from services.operational_collaboration_service import (
    OperationalCollaborationError,
    OperationalCollaborationService,
)


from build_phase import CURRENT_BUILD_PHASE

PHASE_LABEL = CURRENT_BUILD_PHASE

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
    "passenger_service",
    "segment",
    "document",
    "ssr_osi",
    "accepted_offer",
    "invoice",
    "invoice_line_item",
    "payment",
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
    "agency_fee",
    "refund",
    "commission_adjustment",
    "tax_adjustment",
    "unknown",
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
        self.collaboration = OperationalCollaborationService(db)

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

    async def link_options(self, agency_id: str) -> dict[str, Any]:
        collections = {
            "trips": "trip_workspaces",
            "bookings": "booking_workspaces",
            "passengers": "passenger_workspaces",
            "passenger_services": "passenger_service_requests",
            "segments": "trip_segments",
            "accepted_offer_snapshots": "trip_accepted_offer_snapshots",
            "ticket_workspaces": "ticket_workspaces",
            "emd_workspaces": "emd_workspaces",
            "invoices": "invoices",
            "invoice_lines": "invoice_line_items",
            "payments": "payment_records",
            "tickets": "ticket_records",
            "emds": "emd_records",
        }
        records = await asyncio.gather(
            *(self._selector_records(agency_id, collection) for collection in collections.values())
        )
        items = {
            key: [self._selector_option(key, record) for record in group]
            for (key, _), group in zip(collections.items(), records)
        }
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "selector_count": sum(len(group) for group in items.values()),
            "canonical_entities_only": True,
            "labels_preferred_over_ids": True,
            "context_preview_enabled": True,
            "warnings_before_linking_enabled": True,
            "immutable_reference_snapshots_enabled": True,
            **self.safety_flags(),
        }

    async def create_case(self, payload: AfterSalesCaseCreate | dict[str, Any], user: dict, agency_id: str | None = None) -> dict[str, Any]:
        data = self._payload(payload)
        if agency_id:
            data["agency_id"] = agency_id
        self._validate_case(data)
        link_validation = await self._validate_canonical_links(data)
        data["canonical_reference_snapshot_json"] = link_validation["snapshot"]
        data["link_validation_warnings"] = link_validation["warnings"]
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
        if financial:
            await self._record_financial_transition(updated, financial, user)
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
            "affected_financial_records": await self._affected_financial_summary(case),
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
        data = self._payload(payload)
        correlation_id = data.get("correlation_id") or self._financial_correlation_id(case, data)
        existing = await self.db.collection(AFTER_SALES_FINANCIAL_IMPACTS_COLLECTION).find_one(
            {"agency_id": case["agency_id"], "case_id": case["id"], "correlation_id": correlation_id}
        )
        if existing:
            return {
                "phase": PHASE_LABEL,
                "financial_impact": existing,
                "idempotent_reused": True,
                **self.safety_flags(),
            }
        data["correlation_id"] = correlation_id
        impact = await self._create_financial_impact(case, data, user)
        await self._refresh_case_child_links(case["id"], user)
        await self._record_financial_transition(case, impact, user)
        return {"phase": PHASE_LABEL, "financial_impact": impact, **self.safety_flags()}

    async def _record_financial_transition(self, case: dict[str, Any], impact: dict[str, Any], user: dict) -> None:
        evidence = self._transition_evidence(
            case,
            user,
            "financial_records",
            ",".join(impact.get("invoice_ids") or impact.get("payment_record_ids") or [impact["id"]]),
            "after_sales_financial_impact",
            impact["id"],
            impact.get("correlation_id") or f"after-sales:{case['id']}:financial-impact:{impact['id']}",
            impact.get("reconciliation_state") or "unreconciled",
            impact.get("unresolved_mismatches_json") or [],
        )
        await self._record_case_timeline(
            case,
            "after_sales_financial_impact_recorded",
            "Affected financial records and impact snapshots recorded.",
            user,
            evidence,
        )
        audit = AuditEvent(
            agency_id=case["agency_id"],
            actor_user_id=user.get("id"),
            event_type="after_sales.financial_impact_recorded",
            entity_type="after_sales_case",
            entity_id=case["id"],
            summary="After-sales financial linkage and impact metadata recorded.",
            metadata=evidence,
        )
        await self.db.collection("audit_events").insert_one(audit.model_dump(mode="json"))
        if case.get("workflow_instance_id"):
            workflow_event = OperationalWorkflowEvent(
                agency_id=case["agency_id"],
                workflow_instance_id=case["workflow_instance_id"],
                event_type="after_sales_financial_impact_recorded",
                event_code=f"after_sales_financial_impact:{impact['id']}",
                source_module="after_sales_workflow",
                source_entity_type="after_sales_financial_impact",
                source_entity_id=impact["id"],
                payload_json=evidence,
                metadata={"metadata_only": True},
            )
            await self.db.collection("operational_workflow_events").insert_one(workflow_event.model_dump(mode="json"))
        await self.work_queue.generate_work_item(
            OperationalWorkItemGenerateRequest(
                agency_id=case["agency_id"],
                work_item_type=self._work_item_type(case),
                source_entity_type="after_sales_case",
                source_entity_id=case["id"],
                workflow_instance_id=case.get("workflow_instance_id"),
                title=case.get("case_title") or "After-sales case",
                summary=f"Financial reconciliation state: {impact.get('reconciliation_state') or 'unreconciled'}.",
                priority=case.get("case_priority") or "normal",
                severity="high" if impact.get("unresolved_mismatches_json") else "medium",
                queue_code=self._queue_code(case),
                blocker_status="manual_review" if impact.get("manual_unreconciled") or impact.get("unresolved_mismatches_json") else self._blocker_status(case),
                generation_reason="after_sales_financial_linkage",
                source_snapshot_json=evidence,
                compatibility_mapping_json={"after_sales_case_id": case["id"], "financial_impact_id": impact["id"]},
            ),
            user,
            agency_id=case["agency_id"],
        )

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
        legacy = await self._list_child(
            AFTER_SALES_COMMUNICATION_RECORDS_COLLECTION,
            agency_id=agency_id,
            case_id=case_id,
            field="communication_type",
            value=communication_type,
            limit=limit,
        )
        if not agency_id:
            return legacy
        threads = await self.collaboration.list_threads(
            agency_id,
            entity_type="after_sales_case",
            entity_id=case_id,
            limit=limit,
        )
        canonical: list[dict[str, Any]] = []
        for thread in threads:
            detail = await self.collaboration.thread_detail(agency_id, thread["id"])
            for message in detail.get("messages") or []:
                if communication_type and message.get("message_type") != communication_type:
                    continue
                canonical.append(
                    {
                        **message,
                        "case_id": case_id
                        or next(
                            (
                                item.get("entity_id")
                                for item in thread.get("entity_references") or []
                                if item.get("entity_type") == "after_sales_case"
                            ),
                            None,
                        ),
                        "communication_reference": f"CANON-{message['id'][-12:].upper()}",
                        "communication_type": message.get("message_type"),
                        "direction": "internal"
                        if message.get("visibility") == "internal"
                        else "outbound",
                        "audience": message.get("visibility"),
                        "channel": "canonical_record",
                        "sender": message.get("sender_display"),
                        "summary": message.get("plain_text"),
                        "internal_message": message.get("plain_text")
                        if message.get("visibility") == "internal"
                        else None,
                        "client_message": message.get("plain_text")
                        if message.get("visibility") == "client"
                        else None,
                        "document_ids": message.get("attachment_ids") or [],
                        "timeline_entry_id": message.get("linked_timeline_entry_id"),
                        "sent_externally": False,
                        "canonical_thread_id": thread["id"],
                        "canonical_message_id": message["id"],
                    }
                )
        items = legacy + canonical
        items.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
        return items[:limit]

    async def _selector_records(self, agency_id: str, collection_name: str) -> list[dict[str, Any]]:
        page = await PersistenceRepository(self.db).find_agency_records(
            collection_name=collection_name,
            agency_id=agency_id,
            pagination=PaginationRequest.build(limit=MAXIMUM_QUERY_LIMIT),
        )
        return page.items

    def _selector_option(self, group: str, record: dict[str, Any]) -> dict[str, Any]:
        labels = {
            "trips": self._join_label(
                record.get("trip_reference") or "Trip",
                self._route_label(record),
                record.get("departure_date"),
            ),
            "bookings": self._join_label(
                record.get("booking_reference") or record.get("airline_pnr") or "Booking",
                record.get("booking_status") or record.get("status"),
                record.get("airline_pnr"),
            ),
            "passengers": self._join_label(
                " ".join(value for value in [record.get("first_name"), record.get("last_name")] if value)
                or record.get("preferred_name")
                or "Passenger",
                record.get("passenger_reference"),
                record.get("passenger_status"),
            ),
            "passenger_services": self._join_label(
                record.get("service_label") or record.get("service_type") or "Passenger service",
                record.get("service_key") or record.get("ssr_code"),
                record.get("fulfilment_result") or record.get("status"),
            ),
            "segments": self._join_label(
                self._route_label(record) or "Trip segment",
                record.get("flight_number"),
                record.get("departure_date"),
            ),
            "accepted_offer_snapshots": self._join_label(
                "Accepted offer snapshot",
                (record.get("confirmed_fare_bundle_json") or {}).get("name"),
                self._money_label(
                    (record.get("confirmed_pricing_json") or {}).get("total_amount"),
                    (record.get("confirmed_pricing_json") or {}).get("currency"),
                ),
                record.get("created_at"),
            ),
            "ticket_workspaces": self._join_label(
                record.get("ticket_number") or record.get("ticket_reference") or "Ticket workspace",
                record.get("passenger_name"),
                record.get("ticket_document_status") or record.get("ticket_status"),
            ),
            "emd_workspaces": self._join_label(
                record.get("emd_number") or record.get("emd_reference") or "EMD workspace",
                record.get("service_description") or record.get("service_category"),
                record.get("emd_document_status") or record.get("emd_status"),
            ),
            "invoices": self._join_label(
                record.get("invoice_number") or "Invoice",
                self._money_label(record.get("total") or record.get("total_amount"), record.get("currency")),
                record.get("status"),
            ),
            "invoice_lines": self._join_label(
                record.get("description") or record.get("line_item_type") or "Invoice line",
                self._money_label(
                    record.get("amount") or record.get("line_total") or record.get("total_amount"),
                    record.get("currency"),
                ),
            ),
            "payments": self._join_label(
                record.get("external_reference") or record.get("payment_reference") or "Payment",
                self._money_label(record.get("amount"), record.get("currency")),
                record.get("status"),
            ),
            "tickets": self._join_label(
                record.get("ticket_number") or record.get("ticket_reference") or "Ticket record",
                (record.get("passenger_snapshot_json") or {}).get("display_name") or record.get("passenger_name"),
                record.get("reconciliation_status") or record.get("issue_status") or record.get("status"),
            ),
            "emds": self._join_label(
                record.get("emd_number") or record.get("emd_reference") or "EMD record",
                record.get("service_label") or record.get("service_name") or record.get("service_code"),
                record.get("issue_status") or record.get("status"),
            ),
        }
        status_value = (
            record.get("reconciliation_status")
            or record.get("fulfilment_result")
            or record.get("booking_status")
            or record.get("trip_status")
            or record.get("ticket_document_status")
            or record.get("emd_document_status")
            or record.get("status")
            or record.get("issue_status")
            or "unknown"
        )
        warning_states = {"unknown", "unreconciled", "mismatch", "manual_review", "draft", "failed", "blocked"}
        warnings = []
        if self._norm(status_value) in warning_states:
            warnings.append(f"Current state is {self._label(status_value)}; review before linking.")
        if group == "accepted_offer_snapshots":
            warnings.append("This immutable accepted-offer snapshot will be referenced without modification.")
        context = {
            key: record.get(key)
            for key in [
                "trip_id", "trip_workspace_id", "booking_id", "booking_workspace_id", "booking_record_id",
                "passenger_id", "client_id", "request_id", "invoice_id", "workspace_id", "acceptance_id",
                "accepted_offer_snapshot_id", "trip_accepted_offer_snapshot_id",
            ]
            if record.get(key)
        }
        return {
            "id": record["id"],
            "label": labels.get(group) or "Operational record",
            "status": status_value,
            "context": context,
            "context_preview": self._join_label(
                self._route_label(record),
                record.get("booking_reference"),
                record.get("airline_pnr"),
                record.get("passenger_name"),
            ),
            "warnings": warnings,
            "immutable_reference": group == "accepted_offer_snapshots",
        }

    async def _validate_canonical_links(self, data: dict[str, Any]) -> dict[str, Any]:
        agency_id = data["agency_id"]
        list_fields = {
            "ticket_workspace_ids": "ticket_workspaces",
            "emd_workspace_ids": "emd_workspaces",
            "passenger_workspace_ids": "passenger_workspaces",
            "passenger_service_request_ids": "passenger_service_requests",
            "document_workspace_ids": "document_workspaces",
            "ssr_osi_workspace_ids": "ssr_osi_workspaces",
            "invoice_ids": "invoices",
            "invoice_line_item_ids": "invoice_line_items",
            "payment_record_ids": "payment_records",
            "ticket_record_ids": "ticket_records",
            "emd_record_ids": "emd_records",
            "affected_segment_refs": "trip_segments",
        }
        single_fields = {
            "operational_workspace_id": "operational_travel_workspaces",
            "travel_request_workspace_id": "travel_request_workspaces",
            "trip_workspace_id": "trip_workspaces",
            "booking_workspace_id": "booking_workspaces",
            "accepted_offer_snapshot_id": "trip_accepted_offer_snapshots",
        }
        warnings: list[dict[str, Any]] = []
        references: dict[str, list[dict[str, Any]]] = {}

        for field, collection in list_fields.items():
            original = [value for value in data.get(field) or [] if value]
            values = self._present(original)
            data[field] = values
            if len(values) != len(original):
                warnings.append({"code": "duplicate_reference_removed", "field": field, "severity": "warning"})
            references[field] = []
            for entity_id in values:
                references[field].append(await self._require_agency_entity(collection, entity_id, agency_id, field))

        for field, collection in single_fields.items():
            references[field] = []
            if data.get(field):
                references[field].append(
                    await self._require_agency_entity(collection, data[field], agency_id, field)
                )

        trip = self._first_reference(references, "trip_workspace_id")
        booking = self._first_reference(references, "booking_workspace_id")
        snapshot = self._first_reference(references, "accepted_offer_snapshot_id")
        trip_ids = self._record_ids(
            trip,
            "id", "trip_id", "linked_trip_id",
            metadata_keys=("canonical_trip_id",),
        )
        booking_ids = self._record_ids(booking, "id", "booking_id", "booking_record_id")

        if trip and booking:
            self._require_context_overlap(
                "Booking workspace",
                trip_ids,
                self._record_ids(booking, "trip_workspace_id", "trip_id"),
                "trip",
            )
        for passenger in references["passenger_workspace_ids"]:
            if trip:
                trip_passenger_ids = self._record_ids(trip, "passenger_ids")
                if trip_passenger_ids and passenger["id"] not in trip_passenger_ids:
                    raise AfterSalesWorkflowError("Passenger does not belong to the selected trip context.")
            if booking:
                booking_passenger_ids = self._record_ids(booking, "passenger_ids")
                if booking_passenger_ids and passenger["id"] not in booking_passenger_ids:
                    raise AfterSalesWorkflowError("Passenger does not belong to the selected booking context.")
        if trip and snapshot:
            self._require_context_overlap(
                "Accepted-offer snapshot", trip_ids, self._record_ids(snapshot, "trip_id"), "trip"
            )
        if booking and snapshot:
            snapshot_ids = self._record_ids(
                booking, "accepted_offer_snapshot_id", "trip_accepted_offer_snapshot_id"
            )
            if snapshot_ids and snapshot["id"] not in snapshot_ids:
                raise AfterSalesWorkflowError("Accepted-offer snapshot does not belong to the selected booking context.")

        for record in references["invoice_line_item_ids"]:
            if not references["invoice_ids"]:
                raise AfterSalesWorkflowError("Select the invoice that owns the selected invoice line.")
            if record.get("invoice_id") not in {item["id"] for item in references["invoice_ids"]}:
                raise AfterSalesWorkflowError("Selected invoice line does not belong to the selected invoice.")
        for record in references["payment_record_ids"]:
            if not references["invoice_ids"]:
                raise AfterSalesWorkflowError("Select the invoice that owns the selected payment.")
            if record.get("invoice_id") not in {item["id"] for item in references["invoice_ids"]}:
                raise AfterSalesWorkflowError("Selected payment does not belong to the selected invoice.")

        for label, field in [
            ("Invoice", "invoice_ids"),
            ("Ticket workspace", "ticket_workspace_ids"),
            ("EMD workspace", "emd_workspace_ids"),
            ("Ticket", "ticket_record_ids"),
            ("EMD", "emd_record_ids"),
            ("Passenger service", "passenger_service_request_ids"),
        ]:
            for record in references[field]:
                if trip:
                    self._require_context_overlap(
                        label, trip_ids, self._record_ids(record, "trip_workspace_id", "trip_id"), "trip"
                    )
                if booking:
                    self._require_context_overlap(
                        label,
                        booking_ids,
                        self._record_ids(record, "booking_workspace_id", "booking_record_id", "booking_id"),
                        "booking",
                    )
                selected_passenger_ids = {item["id"] for item in references["passenger_workspace_ids"]}
                if selected_passenger_ids and record.get("passenger_id") and record["passenger_id"] not in selected_passenger_ids:
                    raise AfterSalesWorkflowError(f"{label} belongs to a different passenger context.")
        for segment in references["affected_segment_refs"]:
            if trip:
                self._require_context_overlap(
                    "Trip segment", trip_ids, self._record_ids(segment, "trip_id", "workspace_id"), "trip"
                )

        if booking:
            canonical_booking_reference = booking.get("booking_reference") or booking.get("airline_pnr")
            if data.get("booking_reference") and canonical_booking_reference and data["booking_reference"] != canonical_booking_reference:
                raise AfterSalesWorkflowError("Booking reference does not match the selected booking workspace.")
            data["booking_reference"] = canonical_booking_reference or data.get("booking_reference")

        snapshot_payload = {
            field: [self._reference_snapshot(record) for record in records]
            for field, records in references.items()
            if records
        }
        return {
            "snapshot": {
                "captured_at": self._now().isoformat(),
                "agency_id": agency_id,
                "immutable_reference_evidence": True,
                "references": snapshot_payload,
            },
            "warnings": warnings,
        }

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

        for ticket_id in data.get("ticket_record_ids") or []:
            record = await self.db.collection("ticket_records").find_one(
                {"id": ticket_id, "agency_id": data["agency_id"]}
            )
            if record:
                linked.append({"item_type": "ticket", "source_entity_type": "ticket_record", "source_entity_id": ticket_id, "snapshot": self._compact_snapshot(record)})
                coupon_snapshots.append(
                    {
                        "ticket_record_id": ticket_id,
                        "ticket_status": record.get("issue_status") or record.get("status"),
                        "reconciliation_status": record.get("reconciliation_status") or "unknown",
                        "coupon_details": record.get("coupons_json") or [],
                    }
                )

        for emd_id in data.get("emd_record_ids") or []:
            record = await self.db.collection("emd_records").find_one(
                {"id": emd_id, "agency_id": data["agency_id"]}
            )
            if record:
                linked.append({"item_type": "emd", "source_entity_type": "emd_record", "source_entity_id": emd_id, "snapshot": self._compact_snapshot(record)})
                coupon_snapshots.append(
                    {
                        "emd_record_id": emd_id,
                        "emd_status": record.get("issue_status") or record.get("status"),
                        "service_code": record.get("service_code"),
                        "associated_segment_ids": record.get("associated_segment_ids") or [],
                    }
                )

        list_links = [
            ("passenger_workspaces", "passenger_workspace", "passenger_workspace_ids", "passenger"),
            ("passenger_service_requests", "passenger_service_request", "passenger_service_request_ids", "passenger_service"),
            ("document_workspaces", "document_workspace", "document_workspace_ids", "document"),
            ("ssr_osi_workspaces", "ssr_osi_workspace", "ssr_osi_workspace_ids", "ssr_osi"),
            ("invoices", "invoice", "invoice_ids", "invoice"),
            ("invoice_line_items", "invoice_line_item", "invoice_line_item_ids", "invoice_line_item"),
            ("payment_records", "payment_record", "payment_record_ids", "payment"),
        ]
        for collection, entity_type, field, item_type in list_links:
            for entity_id in data.get(field) or []:
                record = await self.db.collection(collection).find_one({"id": entity_id, "agency_id": data["agency_id"]})
                if record:
                    linked.append({"item_type": item_type, "source_entity_type": entity_type, "source_entity_id": entity_id, "snapshot": self._compact_snapshot(record)})
                else:
                    warnings.append({"code": f"linked_{entity_type}_not_found", "entity_type": entity_type, "entity_id": entity_id, "severity": "warning"})

        if data.get("accepted_offer_snapshot_id"):
            snapshot = await self.db.collection("trip_accepted_offer_snapshots").find_one(
                {"id": data["accepted_offer_snapshot_id"], "agency_id": data["agency_id"]}
            )
            if snapshot:
                linked.append(
                    {
                        "item_type": "accepted_offer",
                        "source_entity_type": "trip_accepted_offer_snapshot",
                        "source_entity_id": snapshot["id"],
                        "snapshot": self._reference_snapshot(snapshot),
                    }
                )

        for segment_ref in data.get("affected_segment_refs") or []:
            segment = await self.db.collection("trip_segments").find_one(
                {"id": segment_ref, "agency_id": data["agency_id"]}
            )
            if segment:
                linked.append({"item_type": "segment", "source_entity_type": "trip_segment", "source_entity_id": segment_ref, "snapshot": self._compact_snapshot(segment)})

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
                "passenger_service_request_ids": data.get("passenger_service_request_ids") or [],
                "document_workspace_ids": data.get("document_workspace_ids") or [],
                "ssr_osi_workspace_ids": data.get("ssr_osi_workspace_ids") or [],
                "invoice_ids": data.get("invoice_ids") or [],
                "invoice_line_item_ids": data.get("invoice_line_item_ids") or [],
                "payment_record_ids": data.get("payment_record_ids") or [],
                "ticket_record_ids": data.get("ticket_record_ids") or [],
                "emd_record_ids": data.get("emd_record_ids") or [],
                "accepted_offer_snapshot_id": data.get("accepted_offer_snapshot_id"),
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
            "invoice_ids": data.get("invoice_ids") or [],
            "invoice_line_item_ids": data.get("invoice_line_item_ids") or [],
            "payment_record_ids": data.get("payment_record_ids") or [],
            "ticket_record_ids": data.get("ticket_record_ids") or [],
            "emd_record_ids": data.get("emd_record_ids") or [],
            "accepted_offer_snapshot_id": data.get("accepted_offer_snapshot_id"),
            "booking_reference": data.get("booking_reference"),
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
        data["amount_category"] = self._norm(data.get("amount_category") or data["impact_type"] or "unknown")
        data["estimate_status"] = self._norm(data.get("estimate_status") or "placeholder")
        if data["impact_type"] not in FINANCIAL_IMPACT_TYPES:
            raise AfterSalesWorkflowError(f"Unsupported after-sales financial impact type metadata: {data['impact_type']}.")
        if data["estimate_status"] not in FINANCIAL_ESTIMATE_STATUSES:
            raise AfterSalesWorkflowError(f"Unsupported after-sales financial estimate status metadata: {data['estimate_status']}.")
        allowed_categories = {
            "fare_difference", "penalty", "agency_fee", "supplier_fee", "refund", "credit",
            "residual_value", "commission_adjustment", "tax_adjustment", "unknown", "service_fee",
            "refundability", "tax_refund", "claim_amount", "other",
        }
        if data["amount_category"] not in allowed_categories:
            raise AfterSalesWorkflowError(f"Unsupported after-sales amount category: {data['amount_category']}.")
        bundle = await self._resolve_financial_records(case, data)
        linked = bool(bundle["records"])
        data["invoice_ids"] = bundle["invoice_ids"]
        data["invoice_line_item_ids"] = bundle["invoice_line_item_ids"]
        data["payment_record_ids"] = bundle["payment_record_ids"]
        data["ticket_record_ids"] = bundle["ticket_record_ids"]
        data["emd_record_ids"] = bundle["emd_record_ids"]
        data["accepted_offer_snapshot_id"] = bundle["accepted_offer_snapshot_id"]
        data["booking_reference"] = data.get("booking_reference") or case.get("booking_reference")
        data["original_financial_snapshot_json"] = data.get("original_financial_snapshot_json") or {
            "records": bundle["records"], "captured_at": self._now().isoformat(), "immutable_source_snapshot": True
        }
        data["proposed_financial_impact_snapshot_json"] = data.get("proposed_financial_impact_snapshot_json") or {
            key: data.get(key)
            for key in ["amount_category", "amount", "currency", "direction", "residual_value", "penalty_amount", "fare_difference_amount", "service_fee_amount", "refundable_amount", "supplier_fee_amount"]
            if data.get(key) is not None
        }
        data["linked_financial_records"] = linked
        data["manual_unreconciled"] = not linked
        data["correlation_id"] = data.get("correlation_id") or self._financial_correlation_id(case, data)
        if data.get("final_reconciled_financial_snapshot_json") and data.get("reconciliation_state") != "reconciled":
            raise AfterSalesWorkflowError("A final reconciled snapshot requires reconciliation_state=reconciled.")
        if data.get("settlement_state") == "settled" and not linked:
            raise AfterSalesWorkflowError("An unlinked manual estimate cannot be recorded as settled.")
        if data.get("settlement_state") == "settled" and data.get("estimate_status") in {"placeholder", "manual_review"}:
            raise AfterSalesWorkflowError("A manual estimate cannot claim financial settlement.")
        if data.get("reconciliation_state") == "reconciled":
            if not linked:
                raise AfterSalesWorkflowError("A manual unlinked estimate cannot be recorded as reconciled.")
            if not data.get("final_reconciled_financial_snapshot_json"):
                raise AfterSalesWorkflowError("Reconciled financial impact requires a final reviewed snapshot.")
            if data.get("unresolved_mismatches_json"):
                raise AfterSalesWorkflowError("Reconciled financial impact cannot retain unresolved mismatches.")
            data["reconciled_at"] = data.get("reconciled_at") or self._now()
            data["reconciled_by"] = user.get("id")
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
        audience = self._norm(data.get("audience") or "internal")
        visibility = (
            "client"
            if audience == "client"
            else "supplier"
            if audience in {"supplier", "airline"}
            or data["communication_type"] in {"supplier_message", "airline_message"}
            else "internal"
        )
        participant_payloads: list[dict[str, Any]] = []
        thread_visibility = ["internal", visibility]
        if visibility == "client" and case.get("client_id"):
            mapping = await self.db.collection("portal_access_mappings").find_one(
                {
                    "agency_id": case["agency_id"],
                    "client_profile_id": case["client_id"],
                    "subject_type": "client",
                    "status": "active",
                }
            )
            if mapping:
                client = await self.db.collection("client_profiles").find_one(
                    {"agency_id": case["agency_id"], "id": case["client_id"]}
                )
                participant_payloads.append(
                    {
                        "participant_type": "client_portal",
                        "identity_id": mapping.get("auth_identity_id"),
                        "portal_account_id": mapping.get("id"),
                        "client_id": case["client_id"],
                        "display_name": (client or {}).get("display_name")
                        or "Client Portal",
                        "visibility": ["client"],
                    }
                )
        if visibility == "supplier":
            participant_payloads.append(
                {
                    "participant_type": "supplier",
                    "supplier_reference": data.get("supplier_reference")
                    or "manual_supplier",
                    "display_name": data.get("recipient")
                    or data.get("supplier_reference")
                    or "Supplier",
                    "visibility": ["supplier"],
                    "permissions": ["read"],
                }
            )
        actor = {
            **user,
            "actor_type": "agency",
            "identity_id": user.get("identity_id") or user.get("id"),
            "display_name": user.get("full_name")
            or user.get("email")
            or "Agency user",
        }
        try:
            thread_detail = await self.collaboration.ensure_entity_thread(
                agency_id=case["agency_id"],
                entity_type="after_sales_case",
                entity_id=case["id"],
                subject=case.get("case_title")
                or f"After-sales {case.get('case_reference') or case['id']}",
                actor=actor,
                visibility=list(dict.fromkeys(thread_visibility)),
                participants=participant_payloads,
                context_key=f"after_sales_{visibility}",
            )
            message_text = (
                data.get("internal_message")
                if visibility == "internal"
                else data.get("client_message")
                if visibility == "client"
                else data.get("summary")
            ) or data.get("summary") or data["communication_type"].replace("_", " ")
            message = await self.collaboration.post_message(
                case["agency_id"],
                thread_detail["thread"]["id"],
                {
                    "message_type": data["communication_type"],
                    "plain_text": message_text,
                    "visibility": visibility,
                    "delivery_status": "recorded"
                    if visibility == "internal"
                    else "not_sent",
                    "metadata": {
                        "compatibility_route": "after_sales_communication_records",
                        "supplier_reference": data.get("supplier_reference"),
                        "external_delivery": False,
                    },
                },
                actor,
            )
        except OperationalCollaborationError as exc:
            raise AfterSalesWorkflowError(str(exc)) from exc
        return {
            **message,
            "agency_id": case["agency_id"],
            "case_id": case["id"],
            "communication_reference": data["communication_reference"],
            "communication_type": data["communication_type"],
            "direction": data.get("direction") or "internal",
            "audience": audience,
            "channel": data.get("channel") or "canonical_record",
            "sender": data.get("sender") or message.get("sender_display"),
            "recipient": data.get("recipient"),
            "subject": data.get("subject"),
            "summary": data.get("summary") or message_text,
            "internal_message": data.get("internal_message"),
            "client_message": data.get("client_message"),
            "supplier_reference": data.get("supplier_reference"),
            "document_ids": data.get("document_ids") or [],
            "timeline_entry_id": message.get("linked_timeline_entry_id"),
            "sent_externally": False,
            "canonical_thread_id": thread_detail["thread"]["id"],
            "canonical_message_id": message["id"],
        }

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
                "invoice_ids": self._present((case.get("invoice_ids") or []) + [item_id for impact in impacts for item_id in (impact.get("invoice_ids") or [])]),
                "invoice_line_item_ids": self._present((case.get("invoice_line_item_ids") or []) + [item_id for impact in impacts for item_id in (impact.get("invoice_line_item_ids") or [])]),
                "payment_record_ids": self._present((case.get("payment_record_ids") or []) + [item_id for impact in impacts for item_id in (impact.get("payment_record_ids") or [])]),
                "ticket_record_ids": self._present((case.get("ticket_record_ids") or []) + [item_id for impact in impacts for item_id in (impact.get("ticket_record_ids") or [])]),
                "emd_record_ids": self._present((case.get("emd_record_ids") or []) + [item_id for impact in impacts for item_id in (impact.get("emd_record_ids") or [])]),
                "updated_by": user.get("id"),
            },
        )

    async def _record_case_timeline(self, case: dict[str, Any], event_type: str, summary: str, user: dict, evidence: dict[str, Any] | None = None) -> None:
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
                metadata={"after_sales_case_id": case["id"], "phase": PHASE_LABEL, "metadata_only": True, **(evidence or {})},
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

    async def _resolve_financial_records(self, case: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
        agency_id = case["agency_id"]
        id_groups = {
            "invoice_ids": ("invoices", data.get("invoice_ids") or case.get("invoice_ids") or []),
            "invoice_line_item_ids": ("invoice_line_items", data.get("invoice_line_item_ids") or case.get("invoice_line_item_ids") or []),
            "payment_record_ids": ("payment_records", data.get("payment_record_ids") or case.get("payment_record_ids") or []),
            "ticket_record_ids": ("ticket_records", data.get("ticket_record_ids") or case.get("ticket_record_ids") or []),
            "emd_record_ids": ("emd_records", data.get("emd_record_ids") or case.get("emd_record_ids") or []),
        }
        accepted_snapshot_id = data.get("accepted_offer_snapshot_id") or case.get("accepted_offer_snapshot_id")
        if not accepted_snapshot_id and not any(self._present(ids) for _, ids in id_groups.values()):
            return {
                **{field: [] for field in id_groups},
                "accepted_offer_snapshot_id": None,
                "records": [],
            }
        valid_trip_ids = {
            value
            for value in [
                case.get("source_entity_id") if case.get("source_entity_type") in {"trip", "trip_dossier"} else None,
                (case.get("source_snapshot_json") or {}).get("trip_id"),
            ]
            if value
        }
        if case.get("trip_workspace_id"):
            trip_workspace = await self.db.collection("trip_workspaces").find_one(
                {"agency_id": agency_id, "id": case["trip_workspace_id"]}
            )
            if not trip_workspace:
                raise AfterSalesWorkflowError("After-sales trip workspace was not found for this agency.")
            for value in [
                trip_workspace.get("trip_id"),
                trip_workspace.get("linked_trip_id"),
                (trip_workspace.get("metadata") or {}).get("canonical_trip_id"),
            ]:
                if value:
                    valid_trip_ids.add(value)
        resolved: dict[str, list[str]] = {key: [] for key in id_groups}
        records: list[dict[str, Any]] = []
        raw: dict[tuple[str, str], dict[str, Any]] = {}
        for field, (collection, ids) in id_groups.items():
            for entity_id in self._present(ids):
                record = await self.db.collection(collection).find_one({"agency_id": agency_id, "id": entity_id})
                if not record:
                    raise AfterSalesWorkflowError(f"Referenced {collection} record {entity_id} was not found for this agency.")
                resolved[field].append(entity_id)
                raw[(collection, entity_id)] = record
                records.append({"entity_type": collection, "snapshot": self._financial_snapshot(record)})

        invoice_ids = set(resolved["invoice_ids"])
        for line_id in resolved["invoice_line_item_ids"]:
            line = raw[("invoice_line_items", line_id)]
            if not invoice_ids:
                raise AfterSalesWorkflowError("Select the invoice that owns the selected invoice line item.")
            if line.get("invoice_id") not in invoice_ids:
                raise AfterSalesWorkflowError("Invoice line item does not belong to a selected invoice.")
        for payment_id in resolved["payment_record_ids"]:
            payment = raw[("payment_records", payment_id)]
            if not invoice_ids:
                raise AfterSalesWorkflowError("Select the invoice that owns the selected payment record.")
            if payment.get("invoice_id") not in invoice_ids:
                raise AfterSalesWorkflowError("Payment record does not belong to a selected invoice.")
        for collection, field in [("ticket_records", "ticket_record_ids"), ("emd_records", "emd_record_ids")]:
            for entity_id in resolved[field]:
                record = raw[(collection, entity_id)]
                if valid_trip_ids and record.get("trip_id") and record.get("trip_id") not in valid_trip_ids:
                    raise AfterSalesWorkflowError(f"Referenced {collection} record belongs to a different trip context.")
                if case.get("booking_workspace_id") and record.get("booking_workspace_id") and record.get("booking_workspace_id") != case["booking_workspace_id"]:
                    raise AfterSalesWorkflowError(f"Referenced {collection} record belongs to a different booking context.")

        if accepted_snapshot_id:
            snapshot = await self.db.collection("trip_accepted_offer_snapshots").find_one({"agency_id": agency_id, "id": accepted_snapshot_id})
            if not snapshot:
                raise AfterSalesWorkflowError("Accepted-offer snapshot was not found for this agency.")
            if valid_trip_ids and snapshot.get("trip_id") and snapshot.get("trip_id") not in valid_trip_ids:
                raise AfterSalesWorkflowError("Accepted-offer snapshot belongs to a different trip context.")
            records.append({"entity_type": "trip_accepted_offer_snapshot", "snapshot": self._financial_snapshot(snapshot)})
        return {**resolved, "accepted_offer_snapshot_id": accepted_snapshot_id, "records": records}

    async def _affected_financial_summary(self, case: dict[str, Any]) -> dict[str, Any]:
        bundle = await self._resolve_financial_records(case, case)
        return {
            "invoice_ids": bundle["invoice_ids"],
            "invoice_line_item_ids": bundle["invoice_line_item_ids"],
            "payment_record_ids": bundle["payment_record_ids"],
            "ticket_record_ids": bundle["ticket_record_ids"],
            "emd_record_ids": bundle["emd_record_ids"],
            "accepted_offer_snapshot_id": bundle["accepted_offer_snapshot_id"],
            "booking_reference": case.get("booking_reference"),
            "records": bundle["records"],
            "read_only": True,
        }

    def _financial_snapshot(self, record: dict[str, Any]) -> dict[str, Any]:
        keys = [
            "id", "invoice_id", "invoice_number", "booking_id", "offer_id", "ticket_id", "emd_id",
            "ticket_number", "emd_number", "status", "issue_status", "reconciliation_status", "line_type",
            "description", "currency", "subtotal_amount", "tax_amount", "total_amount", "paid_amount",
            "due_amount", "amount", "external_reference", "created_at", "updated_at",
        ]
        return {key: record.get(key) for key in keys if key in record}

    def _transition_evidence(
        self,
        case: dict[str, Any],
        user: dict,
        source_type: str,
        source_id: str,
        target_type: str,
        target_id: str,
        correlation_id: str,
        result: str,
        warnings: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "agency_id": case["agency_id"],
            "actor_user_id": user.get("id"),
            "source_entity_type": source_type,
            "source_entity_id": source_id,
            "target_entity_type": target_type,
            "target_entity_id": target_id,
            "correlation_id": correlation_id,
            "occurred_at": self._now().isoformat(),
            "result": result,
            "warnings": warnings,
            "internal_only": True,
            "client_visible_summary": (case.get("client_message_json") or {}).get("summary"),
            "financial_commitment_performed": False,
            "metadata_only": True,
        }

    def _financial_correlation_id(self, case: dict[str, Any], data: dict[str, Any]) -> str:
        linked_ids = self._present(
            [
                *(data.get("invoice_ids") or []),
                *(data.get("payment_record_ids") or []),
                *(data.get("ticket_record_ids") or []),
                *(data.get("emd_record_ids") or []),
            ]
        )
        scope = ",".join(linked_ids or ["manual"])
        category = self._norm(data.get("amount_category") or data.get("impact_type") or "unknown")
        return f"after-sales:{case['id']}:finance:{category}:{scope}"

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

    async def _require_agency_entity(
        self, collection: str, entity_id: str, agency_id: str, field: str
    ) -> dict[str, Any]:
        record = await self.db.collection(collection).find_one({"agency_id": agency_id, "id": entity_id})
        if not record:
            raise AfterSalesWorkflowError(
                f"Selected {field.replace('_', ' ')} record was not found for this agency."
            )
        return record

    def _first_reference(
        self, references: dict[str, list[dict[str, Any]]], field: str
    ) -> dict[str, Any] | None:
        return (references.get(field) or [None])[0]

    def _record_ids(
        self,
        record: dict[str, Any] | None,
        *fields: str,
        metadata_keys: tuple[str, ...] = (),
    ) -> set[str]:
        if not record:
            return set()
        values: set[str] = set()
        for field in fields:
            value = record.get(field)
            if isinstance(value, list):
                values.update(str(item) for item in value if item)
            elif value:
                values.add(str(value))
        metadata = record.get("metadata") or {}
        values.update(str(metadata[key]) for key in metadata_keys if metadata.get(key))
        return values

    def _require_context_overlap(
        self, label: str, expected: set[str], actual: set[str], context_name: str
    ) -> None:
        if expected and actual and expected.isdisjoint(actual):
            raise AfterSalesWorkflowError(
                f"{label} belongs to a different {context_name} context."
            )

    def _reference_snapshot(self, record: dict[str, Any]) -> dict[str, Any]:
        return {
            **self._compact_snapshot(record),
            "trip_id": record.get("trip_id"),
            "trip_workspace_id": record.get("trip_workspace_id"),
            "booking_id": record.get("booking_id"),
            "booking_workspace_id": record.get("booking_workspace_id"),
            "booking_record_id": record.get("booking_record_id"),
            "passenger_id": record.get("passenger_id"),
            "invoice_id": record.get("invoice_id"),
            "acceptance_id": record.get("acceptance_id"),
            "immutable_reference": True,
        }

    def _join_label(self, *values: Any) -> str:
        return " · ".join(str(value) for value in values if value is not None and value != "")

    def _route_label(self, record: dict[str, Any]) -> str | None:
        origin = record.get("origin_airport_code") or record.get("origin_airport") or record.get("departure_city")
        destination = record.get("destination_airport_code") or record.get("destination_airport") or record.get("destination_city")
        return f"{origin} to {destination}" if origin and destination else None

    def _money_label(self, amount: Any, currency: Any) -> str | None:
        if amount is None or amount == "":
            return None
        return self._join_label(currency, amount)

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
            "invoice_number",
            "external_reference",
            "ticket_number",
            "emd_number",
            "service_label",
            "service_type",
            "fulfilment_result",
            "reconciliation_status",
            "invoice_id",
            "amount",
            "currency",
            "description",
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
