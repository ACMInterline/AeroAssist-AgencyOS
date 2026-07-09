from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from database import Database
from models import (
    OperationalTravelWorkspace,
    OperationalTravelWorkspaceCreate,
    OperationalTravelWorkspaceUpdate,
    new_id,
)
from services.offer_decision_export_delivery_service import actor_from_user, payload_dict


PHASE_LABEL = "phase_50_9_intelligent_offer_builder_integration_foundation"

WORKSPACE_COLLECTION = "operational_travel_workspaces"
WORKSPACE_TYPES = ["general", "request", "trip", "offer", "booking", "ticketing", "documents", "disruption", "service_case"]
WORKSPACE_STATUSES = ["draft", "open", "active", "waiting", "review", "completed", "archived"]
WORKSPACE_PRIORITIES = ["low", "medium", "high", "urgent"]


class OperationalTravelWorkspaceService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_platform_workspaces(
        self,
        *,
        agency_id: str | None = None,
        status: str | None = None,
        workspace_type: str | None = None,
        priority: str | None = None,
        assigned_agent: str | None = None,
        travel_date: date | str | None = None,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if status:
            filters["workspace_status"] = status
        if workspace_type:
            filters["workspace_type"] = workspace_type
        if priority:
            filters["priority"] = priority
        if assigned_agent:
            filters["assigned_agent"] = assigned_agent
        workspaces = await self.db.collection(WORKSPACE_COLLECTION).find_many(filters or None)
        if not include_archived:
            workspaces = [item for item in workspaces if not item.get("deleted_at") and item.get("workspace_status") != "archived"]
        if travel_date:
            workspaces = [item for item in workspaces if self._matches_travel_date(item, travel_date)]
        workspaces.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._platform_projection(item) for item in workspaces]

    async def list_agency_workspaces(
        self,
        agency_id: str,
        *,
        status: str | None = None,
        workspace_type: str | None = None,
        priority: str | None = None,
        assigned_agent: str | None = None,
        travel_date: date | str | None = None,
    ) -> list[dict[str, Any]]:
        workspaces = await self.list_platform_workspaces(
            agency_id=agency_id,
            status=status,
            workspace_type=workspace_type,
            priority=priority,
            assigned_agent=assigned_agent,
            travel_date=travel_date,
        )
        return [self._agency_projection(item) for item in workspaces if item.get("agency_id") == agency_id]

    async def platform_response(
        self,
        *,
        agency_id: str | None = None,
        status: str | None = None,
        workspace_type: str | None = None,
        priority: str | None = None,
        assigned_agent: str | None = None,
        travel_date: date | str | None = None,
        include_archived: bool = False,
    ) -> dict[str, Any]:
        items = await self.list_platform_workspaces(
            agency_id=agency_id,
            status=status,
            workspace_type=workspace_type,
            priority=priority,
            assigned_agent=assigned_agent,
            travel_date=travel_date,
            include_archived=include_archived,
        )
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "workspace_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Operational travel workspaces are metadata only. They do not execute bookings, issue tickets, connect to live GDS or NDC, process payments, send email or SMS, run AI automation, call external APIs, integrate suppliers, call live airlines, run background workers, or automate operational actions.",
            **self.safety_flags(),
        }

    async def agency_response(
        self,
        agency_id: str,
        *,
        status: str | None = None,
        workspace_type: str | None = None,
        priority: str | None = None,
        assigned_agent: str | None = None,
        travel_date: date | str | None = None,
    ) -> dict[str, Any]:
        items = await self.list_agency_workspaces(
            agency_id,
            status=status,
            workspace_type=workspace_type,
            priority=priority,
            assigned_agent=assigned_agent,
            travel_date=travel_date,
        )
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "workspace_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            "notice": "Operational travel workspace metadata is read-only for this agency. It does not execute bookings, issue tickets, connect to live GDS or NDC, process payments, send email or SMS, run AI automation, call external APIs, integrate suppliers, call live airlines, run background workers, or automate operational actions.",
            **self.safety_flags(),
        }

    async def platform_summary(self) -> dict[str, Any]:
        items = await self.list_platform_workspaces(include_archived=True)
        return {
            "phase": PHASE_LABEL,
            "summary": self.summarize_counts(items),
            "workspace_count": len(items),
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        items = await self.list_agency_workspaces(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(items),
            "workspace_count": len(items),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def get_platform_workspace(self, workspace_id: str) -> dict[str, Any]:
        workspace = await self._require_workspace(workspace_id)
        return await self._platform_projection(workspace)

    async def get_agency_workspace(self, agency_id: str, workspace_id: str) -> dict[str, Any]:
        workspace = await self.get_platform_workspace(workspace_id)
        if workspace.get("agency_id") != agency_id:
            raise ValueError("Operational travel workspace metadata was not found for this agency.")
        return self._agency_projection(workspace)

    async def create_workspace(
        self,
        payload: OperationalTravelWorkspaceCreate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        self._validate_dimension("type", data.get("workspace_type") or "general", WORKSPACE_TYPES)
        self._validate_dimension("status", data.get("workspace_status") or "open", WORKSPACE_STATUSES)
        self._validate_dimension("priority", data.get("priority") or "medium", WORKSPACE_PRIORITIES)
        workspace = OperationalTravelWorkspace(
            id=data.get("id") or new_id(),
            agency_id=data["agency_id"],
            workspace_reference=data.get("workspace_reference") or self._workspace_reference(),
            workspace_title=data["workspace_title"],
            workspace_type=data.get("workspace_type") or "general",
            workspace_status=data.get("workspace_status") or "open",
            primary_client_id=data.get("primary_client_id"),
            primary_passenger_id=data.get("primary_passenger_id"),
            linked_request_ids=data.get("linked_request_ids") or [],
            linked_trip_ids=data.get("linked_trip_ids") or [],
            linked_offer_ids=data.get("linked_offer_ids") or [],
            linked_booking_ids=data.get("linked_booking_ids") or [],
            linked_ticket_ids=data.get("linked_ticket_ids") or [],
            linked_document_ids=data.get("linked_document_ids") or [],
            priority=data.get("priority") or "medium",
            assigned_team=data.get("assigned_team") or [],
            assigned_agent=data.get("assigned_agent"),
            travel_start_date=data.get("travel_start_date"),
            travel_end_date=data.get("travel_end_date"),
            origin_summary=data.get("origin_summary"),
            destination_summary=data.get("destination_summary"),
            service_summary=data.get("service_summary"),
            operational_notes=data.get("operational_notes"),
            created_by=actor_from_user(user),
            updated_by=actor_from_user(user),
            metadata=data.get("metadata") or {},
        )
        stored = await self.db.collection(WORKSPACE_COLLECTION).insert_one(workspace.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "workspace": await self._platform_projection(stored),
            "metadata_only": True,
            "notice": "Operational travel workspace metadata was saved only. No booking execution, ticket issuance, live GDS/NDC connectivity, payment processing, email, SMS, AI automation, external API, supplier integration, live airline call, background worker, or automation was triggered.",
            **self.safety_flags(),
        }

    async def update_workspace(
        self,
        workspace_id: str,
        payload: OperationalTravelWorkspaceUpdate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_workspace(workspace_id)
        updates = {key: value for key, value in payload_dict(payload).items() if value is not None}
        if "workspace_type" in updates:
            self._validate_dimension("type", updates["workspace_type"], WORKSPACE_TYPES)
        if "workspace_status" in updates:
            self._validate_dimension("status", updates["workspace_status"], WORKSPACE_STATUSES)
        if "priority" in updates:
            self._validate_dimension("priority", updates["priority"], WORKSPACE_PRIORITIES)
        updates.update(
            {
                "updated_at": self._now(),
                "updated_by": actor_from_user(user),
                "metadata_only": True,
                "operational_workspace_metadata_only": True,
            }
        )
        updated = await self.db.collection(WORKSPACE_COLLECTION).update_one({"id": existing["id"]}, updates)
        stored = updated or {**existing, **updates}
        return {
            "phase": PHASE_LABEL,
            "workspace": await self._platform_projection(stored),
            "metadata_only": True,
            "notice": "Operational travel workspace metadata was updated only. No booking, ticketing, provider, payment, messaging, AI, external API, supplier, airline, worker, or automation action ran.",
            **self.safety_flags(),
        }

    async def delete_workspace(self, workspace_id: str, user: dict | None = None) -> dict[str, Any]:
        existing = await self._require_workspace(workspace_id)
        updates = {
            "workspace_status": "archived",
            "deleted_at": self._now(),
            "deleted_by": actor_from_user(user),
            "updated_by": actor_from_user(user),
            "metadata_only": True,
            "operational_workspace_metadata_only": True,
            "workspace_archived_metadata_only": True,
        }
        updated = await self.db.collection(WORKSPACE_COLLECTION).update_one({"id": existing["id"]}, updates)
        stored = updated or {**existing, **updates}
        return {
            "phase": PHASE_LABEL,
            "workspace": await self._platform_projection(stored),
            "deleted": True,
            "metadata_only": True,
            "notice": "Operational travel workspace metadata was archived only. No booking execution, ticket issuance, live GDS/NDC connectivity, payment processing, email, SMS, AI automation, external API, supplier integration, live airline call, background worker, or automation ran.",
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        by_status = {status: 0 for status in WORKSPACE_STATUSES}
        by_type = {workspace_type: 0 for workspace_type in WORKSPACE_TYPES}
        by_priority = {priority: 0 for priority in WORKSPACE_PRIORITIES}
        agency_ids: set[str] = set()
        assigned_agents: set[str] = set()
        linked_counts = {
            "linked_request_count": 0,
            "linked_trip_count": 0,
            "linked_offer_count": 0,
            "linked_booking_count": 0,
            "linked_ticket_count": 0,
            "linked_document_count": 0,
        }
        for item in items:
            status = item.get("workspace_status") or "open"
            workspace_type = item.get("workspace_type") or "general"
            priority = item.get("priority") or "medium"
            by_status[status] = by_status.get(status, 0) + 1
            by_type[workspace_type] = by_type.get(workspace_type, 0) + 1
            by_priority[priority] = by_priority.get(priority, 0) + 1
            if item.get("agency_id"):
                agency_ids.add(item["agency_id"])
            if item.get("assigned_agent"):
                assigned_agents.add(item["assigned_agent"])
            linked_counts["linked_request_count"] += len(item.get("linked_request_ids") or [])
            linked_counts["linked_trip_count"] += len(item.get("linked_trip_ids") or [])
            linked_counts["linked_offer_count"] += len(item.get("linked_offer_ids") or [])
            linked_counts["linked_booking_count"] += len(item.get("linked_booking_ids") or [])
            linked_counts["linked_ticket_count"] += len(item.get("linked_ticket_ids") or [])
            linked_counts["linked_document_count"] += len(item.get("linked_document_ids") or [])
        return {
            "total_count": len(items),
            "by_status": by_status,
            "by_type": by_type,
            "by_priority": by_priority,
            "agency_count": len(agency_ids),
            "assigned_agent_count": len(assigned_agents),
            "archived_count": by_status.get("archived", 0),
            "urgent_count": by_priority.get("urgent", 0),
            **linked_counts,
            "metadata_only": True,
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "statuses": WORKSPACE_STATUSES,
            "types": WORKSPACE_TYPES,
            "priorities": WORKSPACE_PRIORITIES,
            "supports_agency_filter": True,
            "supports_status_filter": True,
            "supports_type_filter": True,
            "supports_priority_filter": True,
            "supports_assigned_agent_filter": True,
            "supports_travel_date_filter": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def _require_workspace(self, workspace_id: str) -> dict[str, Any]:
        workspace = await self.db.collection(WORKSPACE_COLLECTION).find_one({"id": workspace_id})
        if not workspace:
            workspace = await self.db.collection(WORKSPACE_COLLECTION).find_one({"workspace_reference": workspace_id})
        if not workspace:
            raise ValueError("Operational travel workspace metadata was not found.")
        return workspace

    async def _platform_projection(self, workspace: dict[str, Any]) -> dict[str, Any]:
        projected = dict(workspace)
        projected["agency"] = await self._agency_context(projected.get("agency_id"))
        projected["agency_name"] = projected["agency"].get("agency_name")
        projected["primary_client"] = await self._client_context(projected.get("agency_id"), projected.get("primary_client_id"))
        projected["primary_passenger"] = await self._passenger_context(projected.get("agency_id"), projected.get("primary_passenger_id"))
        projected["linked_requests"] = [
            await self._request_context(projected.get("agency_id"), request_id)
            for request_id in projected.get("linked_request_ids") or []
        ]
        projected["linked_trips"] = [
            await self._trip_context(projected.get("agency_id"), trip_id)
            for trip_id in projected.get("linked_trip_ids") or []
        ]
        projected["linked_offers"] = [
            await self._offer_context(projected.get("agency_id"), offer_id)
            for offer_id in projected.get("linked_offer_ids") or []
        ]
        projected["linked_bookings"] = [
            await self._booking_context(projected.get("agency_id"), booking_id)
            for booking_id in projected.get("linked_booking_ids") or []
        ]
        projected["linked_tickets"] = [
            await self._ticket_context(projected.get("agency_id"), ticket_id)
            for ticket_id in projected.get("linked_ticket_ids") or []
        ]
        projected["linked_documents"] = [
            await self._document_context(projected.get("agency_id"), document_id)
            for document_id in projected.get("linked_document_ids") or []
        ]
        projected["read_only"] = False
        projected["metadata_only"] = True
        projected["operational_workspace_metadata_only"] = True
        projected.update(self.safety_flags())
        return projected

    def _agency_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        projected["read_only"] = True
        projected.update(self.safety_flags())
        return projected

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

    async def _client_context(self, agency_id: str | None, client_id: str | None) -> dict[str, Any]:
        if not client_id:
            return {"client_id": None, "display_name": None, "metadata_only": True}
        client = await self._lookup_agency_record("client_profiles", agency_id, client_id)
        return {
            "client_id": client.get("id") if client else client_id,
            "display_name": self._first_present(client, ["display_name", "name", "full_name", "company_name"]) if client else client_id,
            "primary_email": client.get("primary_email") if client else None,
            "metadata_only": True,
        }

    async def _passenger_context(self, agency_id: str | None, passenger_id: str | None) -> dict[str, Any]:
        if not passenger_id:
            return {"passenger_id": None, "display_name": None, "metadata_only": True}
        passenger = await self._lookup_agency_record("passenger_profiles", agency_id, passenger_id)
        return {
            "passenger_id": passenger.get("id") if passenger else passenger_id,
            "display_name": self._first_present(passenger, ["display_name", "full_name", "name"]) if passenger else passenger_id,
            "metadata_only": True,
        }

    async def _request_context(self, agency_id: str | None, request_id: str | None) -> dict[str, Any]:
        item = await self._lookup_agency_record("travel_requests", agency_id, request_id)
        return self._compact_context("request_id", request_id, item, ["request_reference", "title", "purpose", "request_purpose"], "status")

    async def _trip_context(self, agency_id: str | None, trip_id: str | None) -> dict[str, Any]:
        item = await self._lookup_agency_record("trip_dossiers", agency_id, trip_id)
        return self._compact_context("trip_id", trip_id, item, ["trip_reference", "title", "trip_name"], "status")

    async def _offer_context(self, agency_id: str | None, offer_id: str | None) -> dict[str, Any]:
        item = await self._lookup_agency_record("offer_workspaces", agency_id, offer_id)
        if not item:
            item = await self._lookup_agency_record("offers", agency_id, offer_id)
        return self._compact_context("offer_id", offer_id, item, ["workspace_reference", "offer_reference", "title", "offer_title"], "status")

    async def _booking_context(self, agency_id: str | None, booking_id: str | None) -> dict[str, Any]:
        item = await self._lookup_agency_record("booking_workspaces", agency_id, booking_id)
        if not item:
            item = await self._lookup_agency_record("booking_records", agency_id, booking_id)
        if not item:
            item = await self._lookup_agency_record("bookings", agency_id, booking_id)
        return self._compact_context("booking_id", booking_id, item, ["workspace_number", "booking_reference", "pnr_locator", "title"], "status")

    async def _ticket_context(self, agency_id: str | None, ticket_id: str | None) -> dict[str, Any]:
        item = await self._lookup_agency_record("ticket_records", agency_id, ticket_id)
        return self._compact_context("ticket_id", ticket_id, item, ["ticket_number", "title", "record_reference"], "issue_status")

    async def _document_context(self, agency_id: str | None, document_id: str | None) -> dict[str, Any]:
        item = await self._lookup_agency_record("rendered_documents", agency_id, document_id)
        if not item:
            item = await self._lookup_agency_record("document_packages", agency_id, document_id)
        return self._compact_context("document_id", document_id, item, ["title", "document_title", "filename", "package_title"], "status")

    async def _lookup_agency_record(self, collection: str, agency_id: str | None, record_id: str | None) -> dict[str, Any] | None:
        if not record_id:
            return None
        filters = {"id": record_id}
        if agency_id:
            filters["agency_id"] = agency_id
        item = await self.db.collection(collection).find_one(filters)
        if item:
            return item
        if agency_id:
            return await self.db.collection(collection).find_one({"agency_id": agency_id, "workspace_reference": record_id})
        return None

    def _compact_context(
        self,
        id_key: str,
        fallback_id: str | None,
        item: dict[str, Any] | None,
        label_keys: list[str],
        status_key: str,
    ) -> dict[str, Any]:
        if not fallback_id:
            return {id_key: None, "label": None, "status": None, "metadata_only": True}
        if not item:
            return {id_key: fallback_id, "label": fallback_id, "status": None, "metadata_only": True}
        return {
            id_key: item.get("id") or fallback_id,
            "label": self._first_present(item, label_keys) or fallback_id,
            "status": item.get(status_key),
            "metadata_only": True,
        }

    def _first_present(self, item: dict[str, Any] | None, keys: list[str]) -> Any:
        if not item:
            return None
        for key in keys:
            if item.get(key):
                return item[key]
        return None

    def _validate_dimension(self, label: str, value: str, allowed: list[str]) -> None:
        if value not in allowed:
            raise ValueError(f"Unsupported operational travel workspace {label}.")

    def _matches_travel_date(self, item: dict[str, Any], travel_date: date | str) -> bool:
        target = self._parse_date(travel_date)
        start = self._parse_optional_date(item.get("travel_start_date"))
        end = self._parse_optional_date(item.get("travel_end_date"))
        if start and end:
            return start <= target <= end
        if start:
            return start == target
        if end:
            return end == target
        return False

    def _parse_date(self, value: date | str | None) -> date:
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            return date.fromisoformat(value[:10])
        raise ValueError("A travel date filter requires an ISO date.")

    def _parse_optional_date(self, value: date | str | None) -> date | None:
        if value is None:
            return None
        return self._parse_date(value)

    def _workspace_reference(self) -> str:
        return f"OTW-{new_id()[:8].upper()}"

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _sort_text(self, value: Any) -> str:
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value or "")

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "operational_workspace_metadata_only": True,
            "booking_execution_disabled": True,
            "ticket_issuance_disabled": True,
            "gds_live_connectivity_disabled": True,
            "ndc_connectivity_disabled": True,
            "payment_processing_disabled": True,
            "email_sending_disabled": True,
            "sms_sending_disabled": True,
            "ai_automation_disabled": True,
            "external_api_calls_disabled": True,
            "supplier_integrations_disabled": True,
            "live_airline_calls_disabled": True,
            "background_workers_disabled": True,
            "automation_disabled": True,
        }
