from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from database import Database
from models import (
    TravelRequestWorkspace,
    TravelRequestWorkspaceCreate,
    TravelRequestWorkspaceUpdate,
    new_id,
)
from services.offer_decision_export_delivery_service import actor_from_user, payload_dict


PHASE_LABEL = "phase_42_1_operational_timeline_workspace_foundation"

REQUEST_WORKSPACE_COLLECTION = "travel_request_workspaces"
REQUEST_TYPES = ["general", "flight", "hotel", "package", "multi_city", "group", "corporate", "leisure", "disruption", "service"]
REQUEST_STATUSES = ["draft", "new", "triage", "open", "researching", "waiting", "quoted", "completed", "archived"]
REQUEST_PRIORITIES = ["low", "medium", "high", "urgent"]


class TravelRequestWorkspaceService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_platform_requests(
        self,
        *,
        agency_id: str | None = None,
        status: str | None = None,
        request_type: str | None = None,
        priority: str | None = None,
        assigned_agent: str | None = None,
        departure_date: date | str | None = None,
        operational_workspace_id: str | None = None,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if status:
            filters["request_status"] = status
        if request_type:
            filters["request_type"] = request_type
        if priority:
            filters["request_priority"] = priority
        if assigned_agent:
            filters["assigned_agent"] = assigned_agent
        if operational_workspace_id:
            filters["operational_workspace_id"] = operational_workspace_id
        requests = await self.db.collection(REQUEST_WORKSPACE_COLLECTION).find_many(filters or None)
        if not include_archived:
            requests = [item for item in requests if not item.get("deleted_at") and item.get("request_status") != "archived"]
        if departure_date:
            target = self._parse_date(departure_date)
            requests = [item for item in requests if self._parse_optional_date(item.get("requested_departure_date")) == target]
        requests.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._platform_projection(item) for item in requests]

    async def list_agency_requests(
        self,
        agency_id: str,
        *,
        status: str | None = None,
        request_type: str | None = None,
        priority: str | None = None,
        assigned_agent: str | None = None,
        departure_date: date | str | None = None,
        operational_workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        requests = await self.list_platform_requests(
            agency_id=agency_id,
            status=status,
            request_type=request_type,
            priority=priority,
            assigned_agent=assigned_agent,
            departure_date=departure_date,
            operational_workspace_id=operational_workspace_id,
        )
        return [self._agency_projection(item) for item in requests if item.get("agency_id") == agency_id]

    async def platform_response(
        self,
        *,
        agency_id: str | None = None,
        status: str | None = None,
        request_type: str | None = None,
        priority: str | None = None,
        assigned_agent: str | None = None,
        departure_date: date | str | None = None,
        operational_workspace_id: str | None = None,
        include_archived: bool = False,
    ) -> dict[str, Any]:
        items = await self.list_platform_requests(
            agency_id=agency_id,
            status=status,
            request_type=request_type,
            priority=priority,
            assigned_agent=assigned_agent,
            departure_date=departure_date,
            operational_workspace_id=operational_workspace_id,
            include_archived=include_archived,
        )
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "request_workspace_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Travel request workspaces are metadata only. They do not execute bookings, issue tickets, connect to live GDS or NDC, process payments, send email or SMS, run AI automation, call external APIs, integrate suppliers, call live airlines, run background workers, automatically convert requests to trips, or automatically create offers.",
            **self.safety_flags(),
        }

    async def agency_response(
        self,
        agency_id: str,
        *,
        status: str | None = None,
        request_type: str | None = None,
        priority: str | None = None,
        assigned_agent: str | None = None,
        departure_date: date | str | None = None,
        operational_workspace_id: str | None = None,
    ) -> dict[str, Any]:
        items = await self.list_agency_requests(
            agency_id,
            status=status,
            request_type=request_type,
            priority=priority,
            assigned_agent=assigned_agent,
            departure_date=departure_date,
            operational_workspace_id=operational_workspace_id,
        )
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "request_workspace_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            "notice": "Travel request workspace metadata is read-only for this agency. It does not execute bookings, issue tickets, connect to live GDS or NDC, process payments, send email or SMS, run AI automation, call external APIs, integrate suppliers, call live airlines, run background workers, automatically convert requests to trips, or automatically create offers.",
            **self.safety_flags(),
        }

    async def platform_summary(self) -> dict[str, Any]:
        items = await self.list_platform_requests(include_archived=True)
        return {
            "phase": PHASE_LABEL,
            "summary": self.summarize_counts(items),
            "request_workspace_count": len(items),
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        items = await self.list_agency_requests(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(items),
            "request_workspace_count": len(items),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def get_platform_request(self, request_workspace_id: str) -> dict[str, Any]:
        request_workspace = await self._require_request_workspace(request_workspace_id)
        return await self._platform_projection(request_workspace)

    async def get_agency_request(self, agency_id: str, request_workspace_id: str) -> dict[str, Any]:
        request_workspace = await self.get_platform_request(request_workspace_id)
        if request_workspace.get("agency_id") != agency_id:
            raise ValueError("Travel request workspace metadata was not found for this agency.")
        return self._agency_projection(request_workspace)

    async def create_request(
        self,
        payload: TravelRequestWorkspaceCreate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        self._validate_dimension("type", data.get("request_type") or "general", REQUEST_TYPES)
        self._validate_dimension("status", data.get("request_status") or "new", REQUEST_STATUSES)
        self._validate_dimension("priority", data.get("request_priority") or "medium", REQUEST_PRIORITIES)
        request_workspace = TravelRequestWorkspace(
            id=data.get("id") or new_id(),
            agency_id=data["agency_id"],
            operational_workspace_id=data["operational_workspace_id"],
            request_reference=data.get("request_reference") or self._request_reference(),
            request_title=data["request_title"],
            request_type=data.get("request_type") or "general",
            request_status=data.get("request_status") or "new",
            request_priority=data.get("request_priority") or "medium",
            client_id=data.get("client_id"),
            primary_passenger_id=data.get("primary_passenger_id"),
            requester_name=data.get("requester_name"),
            requester_email=data.get("requester_email"),
            requester_phone=data.get("requester_phone"),
            requested_service_categories=data.get("requested_service_categories") or [],
            requested_origin=data.get("requested_origin"),
            requested_destination=data.get("requested_destination"),
            requested_departure_date=data.get("requested_departure_date"),
            requested_return_date=data.get("requested_return_date"),
            passenger_count=data.get("passenger_count") or 1,
            passenger_type_summary=data.get("passenger_type_summary"),
            flexibility_notes=data.get("flexibility_notes"),
            special_service_notes=data.get("special_service_notes"),
            budget_notes=data.get("budget_notes"),
            deadline=data.get("deadline"),
            assigned_agent=data.get("assigned_agent"),
            internal_notes=data.get("internal_notes"),
            linked_trip_ids=data.get("linked_trip_ids") or [],
            linked_offer_ids=data.get("linked_offer_ids") or [],
            linked_document_ids=data.get("linked_document_ids") or [],
            created_by=actor_from_user(user),
            updated_by=actor_from_user(user),
            metadata=data.get("metadata") or {},
        )
        stored = await self.db.collection(REQUEST_WORKSPACE_COLLECTION).insert_one(request_workspace.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "request_workspace": await self._platform_projection(stored),
            "metadata_only": True,
            "notice": "Travel request workspace metadata was saved only. No booking execution, ticket issuance, live GDS/NDC connectivity, payment processing, email, SMS, AI automation, external API, supplier integration, live airline call, background worker, trip conversion, offer creation, or automation was triggered.",
            **self.safety_flags(),
        }

    async def update_request(
        self,
        request_workspace_id: str,
        payload: TravelRequestWorkspaceUpdate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_request_workspace(request_workspace_id)
        updates = {key: value for key, value in payload_dict(payload).items() if value is not None}
        if "request_type" in updates:
            self._validate_dimension("type", updates["request_type"], REQUEST_TYPES)
        if "request_status" in updates:
            self._validate_dimension("status", updates["request_status"], REQUEST_STATUSES)
        if "request_priority" in updates:
            self._validate_dimension("priority", updates["request_priority"], REQUEST_PRIORITIES)
        updates.update(
            {
                "updated_at": self._now(),
                "updated_by": actor_from_user(user),
                "metadata_only": True,
                "travel_request_workspace_metadata_only": True,
            }
        )
        updated = await self.db.collection(REQUEST_WORKSPACE_COLLECTION).update_one({"id": existing["id"]}, updates)
        stored = updated or {**existing, **updates}
        return {
            "phase": PHASE_LABEL,
            "request_workspace": await self._platform_projection(stored),
            "metadata_only": True,
            "notice": "Travel request workspace metadata was updated only. No booking, ticketing, provider, payment, messaging, AI, external API, supplier, airline, worker, trip conversion, offer creation, or automation action ran.",
            **self.safety_flags(),
        }

    async def delete_request(self, request_workspace_id: str, user: dict | None = None) -> dict[str, Any]:
        existing = await self._require_request_workspace(request_workspace_id)
        updates = {
            "request_status": "archived",
            "deleted_at": self._now(),
            "deleted_by": actor_from_user(user),
            "updated_by": actor_from_user(user),
            "metadata_only": True,
            "travel_request_workspace_metadata_only": True,
            "request_workspace_archived_metadata_only": True,
        }
        updated = await self.db.collection(REQUEST_WORKSPACE_COLLECTION).update_one({"id": existing["id"]}, updates)
        stored = updated or {**existing, **updates}
        return {
            "phase": PHASE_LABEL,
            "request_workspace": await self._platform_projection(stored),
            "deleted": True,
            "metadata_only": True,
            "notice": "Travel request workspace metadata was archived only. No booking execution, ticket issuance, live GDS/NDC connectivity, payment processing, email, SMS, AI automation, external API, supplier integration, live airline call, background worker, trip conversion, offer creation, or automation ran.",
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        by_status = {status: 0 for status in REQUEST_STATUSES}
        by_type = {request_type: 0 for request_type in REQUEST_TYPES}
        by_priority = {priority: 0 for priority in REQUEST_PRIORITIES}
        agency_ids: set[str] = set()
        assigned_agents: set[str] = set()
        operational_workspace_ids: set[str] = set()
        passenger_total = 0
        linked_counts = {
            "linked_trip_count": 0,
            "linked_offer_count": 0,
            "linked_document_count": 0,
        }
        for item in items:
            status = item.get("request_status") or "new"
            request_type = item.get("request_type") or "general"
            priority = item.get("request_priority") or "medium"
            by_status[status] = by_status.get(status, 0) + 1
            by_type[request_type] = by_type.get(request_type, 0) + 1
            by_priority[priority] = by_priority.get(priority, 0) + 1
            if item.get("agency_id"):
                agency_ids.add(item["agency_id"])
            if item.get("assigned_agent"):
                assigned_agents.add(item["assigned_agent"])
            if item.get("operational_workspace_id"):
                operational_workspace_ids.add(item["operational_workspace_id"])
            passenger_total += int(item.get("passenger_count") or 0)
            linked_counts["linked_trip_count"] += len(item.get("linked_trip_ids") or [])
            linked_counts["linked_offer_count"] += len(item.get("linked_offer_ids") or [])
            linked_counts["linked_document_count"] += len(item.get("linked_document_ids") or [])
        return {
            "total_count": len(items),
            "by_status": by_status,
            "by_type": by_type,
            "by_priority": by_priority,
            "agency_count": len(agency_ids),
            "assigned_agent_count": len(assigned_agents),
            "operational_workspace_count": len(operational_workspace_ids),
            "passenger_count_total": passenger_total,
            "archived_count": by_status.get("archived", 0),
            "urgent_count": by_priority.get("urgent", 0),
            **linked_counts,
            "metadata_only": True,
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "statuses": REQUEST_STATUSES,
            "types": REQUEST_TYPES,
            "priorities": REQUEST_PRIORITIES,
            "supports_agency_filter": True,
            "supports_status_filter": True,
            "supports_type_filter": True,
            "supports_priority_filter": True,
            "supports_assigned_agent_filter": True,
            "supports_departure_date_filter": True,
            "supports_operational_workspace_filter": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def _require_request_workspace(self, request_workspace_id: str) -> dict[str, Any]:
        request_workspace = await self.db.collection(REQUEST_WORKSPACE_COLLECTION).find_one({"id": request_workspace_id})
        if not request_workspace:
            request_workspace = await self.db.collection(REQUEST_WORKSPACE_COLLECTION).find_one({"request_reference": request_workspace_id})
        if not request_workspace:
            raise ValueError("Travel request workspace metadata was not found.")
        return request_workspace

    async def _platform_projection(self, request_workspace: dict[str, Any]) -> dict[str, Any]:
        projected = dict(request_workspace)
        projected["agency"] = await self._agency_context(projected.get("agency_id"))
        projected["agency_name"] = projected["agency"].get("agency_name")
        projected["operational_workspace"] = await self._operational_workspace_context(projected.get("operational_workspace_id"))
        projected["client"] = await self._client_context(projected.get("agency_id"), projected.get("client_id"))
        projected["primary_passenger"] = await self._passenger_context(projected.get("agency_id"), projected.get("primary_passenger_id"))
        projected["linked_trips"] = [
            await self._trip_context(projected.get("agency_id"), trip_id)
            for trip_id in projected.get("linked_trip_ids") or []
        ]
        projected["linked_offers"] = [
            await self._offer_context(projected.get("agency_id"), offer_id)
            for offer_id in projected.get("linked_offer_ids") or []
        ]
        projected["linked_documents"] = [
            await self._document_context(projected.get("agency_id"), document_id)
            for document_id in projected.get("linked_document_ids") or []
        ]
        projected["read_only"] = False
        projected["metadata_only"] = True
        projected["travel_request_workspace_metadata_only"] = True
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

    async def _operational_workspace_context(self, workspace_id: str | None) -> dict[str, Any]:
        if not workspace_id:
            return {"operational_workspace_id": None, "workspace_reference": None, "workspace_title": None, "metadata_only": True}
        workspace = await self.db.collection("operational_travel_workspaces").find_one({"id": workspace_id})
        if not workspace:
            workspace = await self.db.collection("operational_travel_workspaces").find_one({"workspace_reference": workspace_id})
        if not workspace:
            return {"operational_workspace_id": workspace_id, "workspace_reference": workspace_id, "workspace_title": workspace_id, "metadata_only": True}
        return {
            "operational_workspace_id": workspace.get("id"),
            "workspace_reference": workspace.get("workspace_reference"),
            "workspace_title": workspace.get("workspace_title"),
            "workspace_type": workspace.get("workspace_type"),
            "workspace_status": workspace.get("workspace_status"),
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

    async def _trip_context(self, agency_id: str | None, trip_id: str | None) -> dict[str, Any]:
        item = await self._lookup_agency_record("trip_dossiers", agency_id, trip_id)
        return self._compact_context("trip_id", trip_id, item, ["trip_reference", "title", "trip_name"], "status")

    async def _offer_context(self, agency_id: str | None, offer_id: str | None) -> dict[str, Any]:
        item = await self._lookup_agency_record("offer_workspaces", agency_id, offer_id)
        if not item:
            item = await self._lookup_agency_record("offers", agency_id, offer_id)
        return self._compact_context("offer_id", offer_id, item, ["workspace_reference", "offer_reference", "title", "offer_title"], "status")

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
            raise ValueError(f"Unsupported travel request workspace {label}.")

    def _parse_date(self, value: date | str | None) -> date:
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            return date.fromisoformat(value[:10])
        raise ValueError("A departure date filter requires an ISO date.")

    def _parse_optional_date(self, value: date | str | None) -> date | None:
        if value is None:
            return None
        return self._parse_date(value)

    def _request_reference(self) -> str:
        return f"TRW-{new_id()[:8].upper()}"

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _sort_text(self, value: Any) -> str:
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value or "")

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "travel_request_workspace_metadata_only": True,
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
            "automatic_trip_creation_disabled": True,
            "automatic_offer_creation_disabled": True,
            "automation_disabled": True,
        }
