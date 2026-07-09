from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import PassengerServiceWorkflow, PassengerServiceWorkflowCreate, PassengerServiceWorkflowUpdate, new_id


PHASE_LABEL = "phase_52_3_visual_policy_editor_foundation"
PASSENGER_SERVICE_WORKFLOW_COLLECTION = "passenger_service_workflows"

WORKFLOW_STAGES = [
    "passenger_registered",
    "requirements_collected",
    "service_requirements_analysed",
    "airline_evaluation",
    "offer_preparation",
    "offer_accepted",
    "booking_ready",
    "booking_completed",
    "ticket_ready",
    "ticket_completed",
    "emd_required",
    "emd_completed",
    "documents_pending",
    "documents_complete",
    "travel_ready",
    "travel_completed",
    "case_closed",
]

READINESS_STATES = [
    "ready",
    "waiting_for_customer",
    "waiting_for_airline",
    "waiting_for_documents",
    "waiting_for_payment",
    "waiting_for_approval",
    "waiting_for_emd",
    "blocked",
    "completed",
]


class PassengerServiceWorkflowError(ValueError):
    pass


class PassengerServiceWorkflowService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_platform_workflows(
        self,
        *,
        agency_id: str | None = None,
        stage: str | None = None,
        readiness: str | None = None,
        passenger: str | None = None,
        airline: str | None = None,
        priority: str | None = None,
        assigned_agent: str | None = None,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if stage:
            filters["current_stage"] = stage
        if readiness:
            filters["readiness_status"] = readiness
        if priority:
            filters["workflow_priority"] = priority
        if airline:
            filters["related_airline"] = airline
        if assigned_agent:
            filters["responsible_agent"] = assigned_agent

        items = await self.db.collection(PASSENGER_SERVICE_WORKFLOW_COLLECTION).find_many(filters or None)
        if not include_archived:
            items = [
                item
                for item in items
                if not item.get("deleted_at") and item.get("workflow_status") != "archived"
            ]
        items = self._filter_exact(items, passenger, ["passenger_workspace_id"])
        items.sort(key=lambda item: self._sort_text(item.get("last_updated") or item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._platform_projection(item) for item in items]

    async def list_agency_workflows(
        self,
        agency_id: str,
        *,
        stage: str | None = None,
        readiness: str | None = None,
        passenger: str | None = None,
        airline: str | None = None,
        priority: str | None = None,
        assigned_agent: str | None = None,
    ) -> list[dict[str, Any]]:
        items = await self.list_platform_workflows(
            agency_id=agency_id,
            stage=stage,
            readiness=readiness,
            passenger=passenger,
            airline=airline,
            priority=priority,
            assigned_agent=assigned_agent,
        )
        return [self._agency_projection(item) for item in items if item.get("agency_id") == agency_id]

    async def platform_response(self, **filters: Any) -> dict[str, Any]:
        items = await self.list_platform_workflows(**filters)
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "passenger_service_workflow_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Passenger Service Workflows are metadata-only coordination records. They do not execute workflows, make AI decisions, run workers, call airline/GDS/NDC APIs, approve, ticket, issue EMDs, or send messages.",
            **self.safety_flags(),
        }

    async def agency_response(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        items = await self.list_agency_workflows(agency_id, **filters)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "passenger_service_workflow_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            "notice": "Agency Workflow Engine is read-only coordination metadata. No workflow automation, AI decisions, approvals, ticketing, EMD issuance, messaging, workers, or provider integrations run here.",
            **self.safety_flags(),
        }

    async def platform_summary(self) -> dict[str, Any]:
        items = await self.list_platform_workflows()
        return {
            "phase": PHASE_LABEL,
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        items = await self.list_agency_workflows(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def get_platform_workflow(self, workflow_id: str) -> dict[str, Any]:
        item = await self._require_workflow(workflow_id)
        return await self._platform_projection(item)

    async def get_agency_workflow(self, agency_id: str, workflow_id: str) -> dict[str, Any]:
        item = await self._require_workflow(workflow_id, agency_id=agency_id)
        return self._agency_projection(await self._platform_projection(item))

    async def create_workflow(self, payload: PassengerServiceWorkflowCreate, user: dict) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        self._validate_payload(data)
        data.setdefault("workflow_reference", self._workflow_reference())
        data.setdefault("workflow_status", "draft_metadata")
        data.setdefault("workflow_version", "1.0")
        data.setdefault("last_updated", self._now())
        data["updated_by"] = user.get("id")
        data.update(self.safety_flags())
        workflow = PassengerServiceWorkflow(**data)
        created = await self.db.collection(PASSENGER_SERVICE_WORKFLOW_COLLECTION).insert_one(workflow.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "passenger_service_workflow": await self._platform_projection(created),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def update_workflow(self, workflow_id: str, payload: PassengerServiceWorkflowUpdate, user: dict) -> dict[str, Any]:
        existing = await self._require_workflow(workflow_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        self._validate_payload(updates, partial=True)
        updates["last_updated"] = self._now()
        updates["updated_by"] = user.get("id")
        updates.update(self.safety_flags())
        updated = await self.db.collection(PASSENGER_SERVICE_WORKFLOW_COLLECTION).update_one({"id": existing["id"]}, updates)
        if not updated:
            raise PassengerServiceWorkflowError("Passenger service workflow metadata could not be updated.")
        return {
            "phase": PHASE_LABEL,
            "passenger_service_workflow": await self._platform_projection(updated),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def delete_workflow(self, workflow_id: str, user: dict) -> dict[str, Any]:
        existing = await self._require_workflow(workflow_id)
        updated = await self.db.collection(PASSENGER_SERVICE_WORKFLOW_COLLECTION).update_one(
            {"id": existing["id"]},
            {
                "workflow_status": "archived",
                "deleted_at": self._now(),
                "deleted_by": user.get("id"),
                "updated_by": user.get("id"),
                "last_updated": self._now(),
                **self.safety_flags(),
            },
        )
        if not updated:
            raise PassengerServiceWorkflowError("Passenger service workflow metadata could not be archived.")
        return {
            "phase": PHASE_LABEL,
            "passenger_service_workflow": await self._platform_projection(updated),
            "archived": True,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        by_stage: dict[str, int] = {stage: 0 for stage in WORKFLOW_STAGES}
        by_readiness: dict[str, int] = {state: 0 for state in READINESS_STATES}
        by_status: dict[str, int] = {}
        by_type: dict[str, int] = {}
        by_priority: dict[str, int] = {}
        linked_counts = {
            "passenger_workspace_count": 0,
            "travel_request_workspace_count": 0,
            "trip_workspace_count": 0,
            "booking_workspace_count": 0,
            "ticket_workspace_count": 0,
            "emd_workspace_count": 0,
            "ssr_osi_workspace_count": 0,
            "document_workspace_count": 0,
            "timeline_workspace_count": 0,
            "blocking_requirement_count": 0,
            "completed_requirement_count": 0,
            "recommendation_pack_count": 0,
        }
        for item in items:
            self._count_value(by_stage, item.get("current_stage"))
            self._count_value(by_readiness, item.get("readiness_status"))
            self._count_value(by_status, item.get("workflow_status"))
            self._count_value(by_type, item.get("workflow_type"))
            self._count_value(by_priority, item.get("workflow_priority"))
            linked_counts["passenger_workspace_count"] += 1 if item.get("passenger_workspace_id") else 0
            linked_counts["travel_request_workspace_count"] += 1 if item.get("travel_request_workspace_id") else 0
            linked_counts["trip_workspace_count"] += 1 if item.get("trip_workspace_id") else 0
            linked_counts["booking_workspace_count"] += 1 if item.get("booking_workspace_id") else 0
            linked_counts["ticket_workspace_count"] += 1 if item.get("ticket_workspace_id") else 0
            linked_counts["emd_workspace_count"] += 1 if item.get("emd_workspace_id") else 0
            linked_counts["ssr_osi_workspace_count"] += 1 if item.get("ssr_osi_workspace_id") else 0
            linked_counts["document_workspace_count"] += 1 if item.get("document_workspace_id") else 0
            linked_counts["timeline_workspace_count"] += 1 if item.get("timeline_workspace_id") else 0
            linked_counts["blocking_requirement_count"] += self._list_count(item.get("blocking_requirements"))
            linked_counts["completed_requirement_count"] += self._list_count(item.get("completed_requirements"))
            linked_counts["recommendation_pack_count"] += 1 if item.get("recommendation_pack_reference") else 0
        return {
            "total_count": len(items),
            "by_stage": by_stage,
            "by_readiness": by_readiness,
            "by_status": by_status,
            "by_type": by_type,
            "by_priority": by_priority,
            **linked_counts,
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "stage": WORKFLOW_STAGES,
            "readiness": READINESS_STATES,
            "passenger": "passenger_workspace_id exact metadata match",
            "airline": "related_airline exact metadata match",
            "priority": "workflow_priority exact metadata match",
            "assigned_agent": "responsible_agent exact metadata match",
            "metadata_only": True,
        }

    async def _platform_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        projected["workflow_display_name"] = self._workflow_display_name(projected)
        agency = await self._agency_context(projected.get("agency_id"))
        projected["agency"] = agency
        projected["agency_name"] = agency.get("agency_name")
        projected["read_only"] = False
        projected.update(self.safety_flags())
        return projected

    def _agency_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        projected["read_only"] = True
        projected.update(self.safety_flags())
        return projected

    async def _require_workflow(self, workflow_id: str, *, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": workflow_id}
        if agency_id:
            filters["agency_id"] = agency_id
        item = await self.db.collection(PASSENGER_SERVICE_WORKFLOW_COLLECTION).find_one(filters)
        if not item:
            alt_filters = {"workflow_reference": workflow_id}
            if agency_id:
                alt_filters["agency_id"] = agency_id
            item = await self.db.collection(PASSENGER_SERVICE_WORKFLOW_COLLECTION).find_one(alt_filters)
        if not item:
            raise PassengerServiceWorkflowError("Passenger service workflow metadata was not found.")
        return item

    async def _agency_context(self, agency_id: str | None) -> dict[str, Any]:
        if not agency_id:
            return {"agency_id": None, "agency_name": None, "agency_slug": None, "metadata_only": True}
        agency = await self.db.collection("agencies").find_one({"id": agency_id})
        if not agency:
            return {"agency_id": agency_id, "agency_name": agency_id, "agency_slug": None, "metadata_only": True}
        return {
            "agency_id": agency.get("id"),
            "agency_name": agency.get("name"),
            "agency_slug": agency.get("slug"),
            "metadata_only": True,
        }

    def _validate_payload(self, data: dict[str, Any], *, partial: bool = False) -> None:
        if not partial and not data.get("agency_id"):
            raise PassengerServiceWorkflowError("Agency id is required for passenger service workflow metadata.")
        for key in ["current_stage", "next_stage", "previous_stage"]:
            if data.get(key) and data[key] not in WORKFLOW_STAGES:
                raise PassengerServiceWorkflowError(f"{key} must be a known passenger service workflow stage.")
        if data.get("readiness_status") and data["readiness_status"] not in READINESS_STATES:
            raise PassengerServiceWorkflowError("Readiness status must be a known passenger service workflow readiness state.")

    def _filter_exact(self, items: list[dict[str, Any]], value: str | None, keys: list[str]) -> list[dict[str, Any]]:
        if not value:
            return items
        value_key = value.lower()
        return [
            item
            for item in items
            if value_key in {str(item.get(key) or "").lower() for key in keys}
        ]

    def _workflow_display_name(self, item: dict[str, Any]) -> str:
        if item.get("workflow_reference"):
            return str(item["workflow_reference"])
        if item.get("current_stage"):
            return str(item["current_stage"])
        return item.get("id") or "Passenger service workflow"

    def _workflow_reference(self) -> str:
        return f"PSW-{new_id()[:8].upper()}"

    def _count_value(self, target: dict[str, int], value: Any) -> None:
        if value:
            target[str(value)] = target.get(str(value), 0) + 1

    def _list_count(self, value: Any) -> int:
        if not value:
            return 0
        if isinstance(value, list):
            return len(value)
        return 1

    def _sort_text(self, value: Any) -> str:
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value or "")

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "workflow_engine_metadata_only": True,
            "automatic_workflow_execution_disabled": True,
            "ai_decision_making_disabled": True,
            "background_workers_disabled": True,
            "airline_apis_disabled": True,
            "gds_connectivity_disabled": True,
            "ndc_connectivity_disabled": True,
            "automatic_approvals_disabled": True,
            "automatic_ticketing_disabled": True,
            "automatic_emd_issuance_disabled": True,
            "automatic_messaging_disabled": True,
            "provider_integrations_disabled": True,
            "automation_disabled": True,
        }
