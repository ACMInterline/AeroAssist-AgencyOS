from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from database import Database
from models import TripWorkspace, TripWorkspaceCreate, TripWorkspaceUpdate, new_id
from services.offer_decision_export_delivery_service import actor_from_user, payload_dict


PHASE_LABEL = "phase_54_7_servicing_after_sales_workflow_foundation"

TRIP_WORKSPACE_COLLECTION = "trip_workspaces"
TRIP_STATUSES = ["draft", "planning", "active", "ready", "traveling", "completed", "archived"]


class TripWorkspaceService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_platform_trips(
        self,
        *,
        agency_id: str | None = None,
        status: str | None = None,
        departure_country: str | None = None,
        destination_country: str | None = None,
        departure_date: date | str | None = None,
        assigned_agent: str | None = None,
        priority: str | None = None,
        operational_workspace_id: str | None = None,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if status:
            filters["trip_status"] = status
        if departure_country:
            filters["departure_country"] = departure_country
        if destination_country:
            filters["destination_country"] = destination_country
        if assigned_agent:
            filters["assigned_agent"] = assigned_agent
        if priority:
            filters["operational_priority"] = priority
        if operational_workspace_id:
            filters["operational_workspace_id"] = operational_workspace_id
        trips = await self.db.collection(TRIP_WORKSPACE_COLLECTION).find_many(filters or None)
        if not include_archived:
            trips = [item for item in trips if not item.get("deleted_at") and item.get("trip_status") != "archived"]
        if departure_date:
            target = self._parse_date(departure_date)
            trips = [item for item in trips if self._date_matches(item.get("departure_date"), target)]
        trips.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._platform_projection(item) for item in trips]

    async def list_agency_trips(
        self,
        agency_id: str,
        *,
        status: str | None = None,
        departure_country: str | None = None,
        destination_country: str | None = None,
        departure_date: date | str | None = None,
        assigned_agent: str | None = None,
        priority: str | None = None,
        operational_workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        trips = await self.list_platform_trips(
            agency_id=agency_id,
            status=status,
            departure_country=departure_country,
            destination_country=destination_country,
            departure_date=departure_date,
            assigned_agent=assigned_agent,
            priority=priority,
            operational_workspace_id=operational_workspace_id,
        )
        return [self._agency_projection(item) for item in trips if item.get("agency_id") == agency_id]

    async def platform_response(
        self,
        *,
        agency_id: str | None = None,
        status: str | None = None,
        departure_country: str | None = None,
        destination_country: str | None = None,
        departure_date: date | str | None = None,
        assigned_agent: str | None = None,
        priority: str | None = None,
        operational_workspace_id: str | None = None,
        include_archived: bool = False,
    ) -> dict[str, Any]:
        items = await self.list_platform_trips(
            agency_id=agency_id,
            status=status,
            departure_country=departure_country,
            destination_country=destination_country,
            departure_date=departure_date,
            assigned_agent=assigned_agent,
            priority=priority,
            operational_workspace_id=operational_workspace_id,
            include_archived=include_archived,
        )
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "trip_workspace_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Trip workspaces are metadata only. They do not execute bookings, issue tickets, connect to GDS or NDC, call airline APIs, process payments, create invoices, use AI, run background workers, automatically generate trips, automatically generate itineraries, call external integrations, or automate journey operations.",
            **self.safety_flags(),
        }

    async def agency_response(
        self,
        agency_id: str,
        *,
        status: str | None = None,
        departure_country: str | None = None,
        destination_country: str | None = None,
        departure_date: date | str | None = None,
        assigned_agent: str | None = None,
        priority: str | None = None,
        operational_workspace_id: str | None = None,
    ) -> dict[str, Any]:
        items = await self.list_agency_trips(
            agency_id,
            status=status,
            departure_country=departure_country,
            destination_country=destination_country,
            departure_date=departure_date,
            assigned_agent=assigned_agent,
            priority=priority,
            operational_workspace_id=operational_workspace_id,
        )
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "trip_workspace_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            "notice": "Trip workspace metadata is read-only for this agency. It does not execute bookings, issue tickets, connect to GDS or NDC, call airline APIs, process payments, create invoices, use AI, run background workers, automatically generate trips, automatically generate itineraries, call external integrations, or automate journey operations.",
            **self.safety_flags(),
        }

    async def platform_summary(self) -> dict[str, Any]:
        items = await self.list_platform_trips(include_archived=True)
        return {
            "phase": PHASE_LABEL,
            "summary": self.summarize_counts(items),
            "trip_workspace_count": len(items),
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        items = await self.list_agency_trips(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(items),
            "trip_workspace_count": len(items),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def get_platform_trip(self, trip_workspace_id: str) -> dict[str, Any]:
        trip_workspace = await self._require_trip_workspace(trip_workspace_id)
        return await self._platform_projection(trip_workspace)

    async def get_agency_trip(self, agency_id: str, trip_workspace_id: str) -> dict[str, Any]:
        trip_workspace = await self.get_platform_trip(trip_workspace_id)
        if trip_workspace.get("agency_id") != agency_id:
            raise ValueError("Trip workspace metadata was not found for this agency.")
        return self._agency_projection(trip_workspace)

    async def create_trip(
        self,
        payload: TripWorkspaceCreate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        self._validate_status(data.get("trip_status") or "active")
        trip_workspace = TripWorkspace(
            id=data.get("id") or new_id(),
            agency_id=data["agency_id"],
            operational_workspace_id=data.get("operational_workspace_id"),
            trip_reference=data.get("trip_reference") or self._trip_reference(),
            trip_status=data.get("trip_status") or "active",
            journey_type=data.get("journey_type"),
            service_type=data.get("service_type"),
            client_id=data.get("client_id"),
            passenger_ids=data.get("passenger_ids") or [],
            flight_workspace_ids=data.get("flight_workspace_ids") or [],
            travel_request_ids=data.get("travel_request_ids") or [],
            offer_ids=data.get("offer_ids") or [],
            booking_ids=data.get("booking_ids") or [],
            ticket_ids=data.get("ticket_ids") or [],
            emd_ids=data.get("emd_ids") or [],
            document_ids=data.get("document_ids") or [],
            departure_country=data.get("departure_country"),
            destination_country=data.get("destination_country"),
            departure_city=data.get("departure_city"),
            destination_city=data.get("destination_city"),
            origin_airport=data.get("origin_airport"),
            destination_airport=data.get("destination_airport"),
            departure_date=data.get("departure_date"),
            return_date=data.get("return_date"),
            travel_duration=data.get("travel_duration"),
            passenger_count=data.get("passenger_count"),
            itinerary_summary=data.get("itinerary_summary"),
            baggage_summary=data.get("baggage_summary"),
            service_summary=data.get("service_summary"),
            operational_priority=data.get("operational_priority"),
            assigned_agent=data.get("assigned_agent"),
            assigned_team=data.get("assigned_team") or [],
            operational_notes=data.get("operational_notes"),
            created_by=actor_from_user(user),
            updated_by=actor_from_user(user),
            metadata=data.get("metadata") or {},
        )
        stored = await self.db.collection(TRIP_WORKSPACE_COLLECTION).insert_one(trip_workspace.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "trip_workspace": await self._platform_projection(stored),
            "metadata_only": True,
            "notice": "Trip workspace metadata was saved only. No booking, ticketing, GDS/NDC, airline API, payment, invoicing, AI, worker, trip generation, itinerary generation, external integration, or automation action ran.",
            **self.safety_flags(),
        }

    async def update_trip(
        self,
        trip_workspace_id: str,
        payload: TripWorkspaceUpdate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_trip_workspace(trip_workspace_id)
        updates = {key: value for key, value in payload_dict(payload).items() if value is not None}
        if "trip_status" in updates:
            self._validate_status(updates["trip_status"])
        updates.update(
            {
                "updated_at": self._now(),
                "updated_by": actor_from_user(user),
                "metadata_only": True,
                "trip_workspace_metadata_only": True,
            }
        )
        updated = await self.db.collection(TRIP_WORKSPACE_COLLECTION).update_one({"id": existing["id"]}, updates)
        stored = updated or {**existing, **updates}
        return {
            "phase": PHASE_LABEL,
            "trip_workspace": await self._platform_projection(stored),
            "metadata_only": True,
            "notice": "Trip workspace metadata was updated only. No booking, ticketing, GDS/NDC, airline API, payment, invoicing, AI, worker, trip generation, itinerary generation, integration, or automation action ran.",
            **self.safety_flags(),
        }

    async def delete_trip(self, trip_workspace_id: str, user: dict | None = None) -> dict[str, Any]:
        existing = await self._require_trip_workspace(trip_workspace_id)
        updates = {
            "trip_status": "archived",
            "deleted_at": self._now(),
            "deleted_by": actor_from_user(user),
            "updated_by": actor_from_user(user),
            "metadata_only": True,
            "trip_workspace_metadata_only": True,
            "trip_workspace_archived_metadata_only": True,
        }
        updated = await self.db.collection(TRIP_WORKSPACE_COLLECTION).update_one({"id": existing["id"]}, updates)
        stored = updated or {**existing, **updates}
        return {
            "phase": PHASE_LABEL,
            "trip_workspace": await self._platform_projection(stored),
            "deleted": True,
            "metadata_only": True,
            "notice": "Trip workspace metadata was archived only. No booking, ticketing, GDS/NDC, airline API, payment, invoicing, AI, worker, trip generation, itinerary generation, external integration, or automation ran.",
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        by_status = {status: 0 for status in TRIP_STATUSES}
        by_departure_country: dict[str, int] = {}
        by_destination_country: dict[str, int] = {}
        by_priority: dict[str, int] = {}
        agency_ids: set[str] = set()
        operational_workspace_ids: set[str] = set()
        linked_counts = {
            "passenger_count": 0,
            "flight_workspace_count": 0,
            "travel_request_count": 0,
            "offer_count": 0,
            "booking_count": 0,
            "ticket_count": 0,
            "emd_count": 0,
            "document_count": 0,
        }
        for item in items:
            status = item.get("trip_status") or "active"
            by_status[status] = by_status.get(status, 0) + 1
            self._count_value(by_departure_country, item.get("departure_country"))
            self._count_value(by_destination_country, item.get("destination_country"))
            self._count_value(by_priority, item.get("operational_priority"))
            if item.get("agency_id"):
                agency_ids.add(item["agency_id"])
            if item.get("operational_workspace_id"):
                operational_workspace_ids.add(item["operational_workspace_id"])
            linked_counts["passenger_count"] += item.get("passenger_count") or len(item.get("passenger_ids") or [])
            linked_counts["flight_workspace_count"] += len(item.get("flight_workspace_ids") or [])
            linked_counts["travel_request_count"] += len(item.get("travel_request_ids") or [])
            linked_counts["offer_count"] += len(item.get("offer_ids") or [])
            linked_counts["booking_count"] += len(item.get("booking_ids") or [])
            linked_counts["ticket_count"] += len(item.get("ticket_ids") or [])
            linked_counts["emd_count"] += len(item.get("emd_ids") or [])
            linked_counts["document_count"] += len(item.get("document_ids") or [])
        return {
            "total_count": len(items),
            "by_status": by_status,
            "by_departure_country": by_departure_country,
            "by_destination_country": by_destination_country,
            "by_priority": by_priority,
            "agency_count": len(agency_ids),
            "operational_workspace_count": len(operational_workspace_ids),
            "archived_count": by_status.get("archived", 0),
            **linked_counts,
            "metadata_only": True,
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "statuses": TRIP_STATUSES,
            "supports_status_filter": True,
            "supports_departure_country_filter": True,
            "supports_destination_country_filter": True,
            "supports_departure_date_filter": True,
            "supports_assigned_agent_filter": True,
            "supports_priority_filter": True,
            "supports_operational_workspace_filter": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def _require_trip_workspace(self, trip_workspace_id: str) -> dict[str, Any]:
        trip_workspace = await self.db.collection(TRIP_WORKSPACE_COLLECTION).find_one({"id": trip_workspace_id})
        if not trip_workspace:
            trip_workspace = await self.db.collection(TRIP_WORKSPACE_COLLECTION).find_one({"trip_reference": trip_workspace_id})
        if not trip_workspace:
            raise ValueError("Trip workspace metadata was not found.")
        return trip_workspace

    async def _platform_projection(self, trip_workspace: dict[str, Any]) -> dict[str, Any]:
        projected = dict(trip_workspace)
        projected["trip_display_name"] = self._trip_display_name(projected)
        projected["agency"] = await self._agency_context(projected.get("agency_id"))
        projected["agency_name"] = projected["agency"].get("agency_name")
        projected["operational_workspace"] = await self._operational_workspace_context(projected.get("operational_workspace_id"))
        projected["client"] = await self._client_context(projected.get("agency_id"), projected.get("client_id"))
        projected["passengers"] = [
            await self._passenger_context(projected.get("agency_id"), passenger_id)
            for passenger_id in projected.get("passenger_ids") or []
        ]
        projected["flight_workspaces"] = [
            await self._flight_workspace_context(projected.get("agency_id"), flight_workspace_id)
            for flight_workspace_id in projected.get("flight_workspace_ids") or []
        ]
        projected["travel_requests"] = [
            await self._request_context(projected.get("agency_id"), request_id)
            for request_id in projected.get("travel_request_ids") or []
        ]
        projected["offers"] = [
            await self._offer_context(projected.get("agency_id"), offer_id)
            for offer_id in projected.get("offer_ids") or []
        ]
        projected["bookings"] = [
            await self._booking_context(projected.get("agency_id"), booking_id)
            for booking_id in projected.get("booking_ids") or []
        ]
        projected["tickets"] = [
            await self._ticket_context(projected.get("agency_id"), ticket_id)
            for ticket_id in projected.get("ticket_ids") or []
        ]
        projected["emds"] = [
            await self._emd_context(projected.get("agency_id"), emd_id)
            for emd_id in projected.get("emd_ids") or []
        ]
        projected["documents"] = [
            await self._document_context(projected.get("agency_id"), document_id)
            for document_id in projected.get("document_ids") or []
        ]
        projected["read_only"] = False
        projected["metadata_only"] = True
        projected["trip_workspace_metadata_only"] = True
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
            "travel_start_date": workspace.get("travel_start_date"),
            "travel_end_date": workspace.get("travel_end_date"),
            "metadata_only": True,
        }

    async def _client_context(self, agency_id: str | None, client_id: str | None) -> dict[str, Any]:
        item = await self._lookup_agency_record("client_profiles", agency_id, client_id, ["client_reference", "email"])
        if not item:
            item = await self._lookup_agency_record("clients", agency_id, client_id, ["client_reference", "email"])
        return self._compact_context("client_id", client_id, item, ["name", "full_name", "email", "client_reference"], "status")

    async def _passenger_context(self, agency_id: str | None, passenger_id: str | None) -> dict[str, Any]:
        item = await self._lookup_agency_record("passenger_workspaces", agency_id, passenger_id, ["passenger_reference"])
        if not item:
            item = await self._lookup_agency_record("passengers", agency_id, passenger_id, ["passenger_reference"])
        return self._compact_context("passenger_id", passenger_id, item, ["passenger_reference", "preferred_name", "first_name", "last_name"], "passenger_status")

    async def _flight_workspace_context(self, agency_id: str | None, flight_workspace_id: str | None) -> dict[str, Any]:
        item = await self._lookup_agency_record("flight_workspaces", agency_id, flight_workspace_id, ["flight_reference"])
        return self._compact_context("flight_workspace_id", flight_workspace_id, item, ["flight_reference", "flight_number", "airline_code"], "flight_status")

    async def _request_context(self, agency_id: str | None, request_id: str | None) -> dict[str, Any]:
        item = await self._lookup_agency_record("travel_request_workspaces", agency_id, request_id, ["request_reference"])
        if not item:
            item = await self._lookup_agency_record("travel_requests", agency_id, request_id, ["request_reference"])
        return self._compact_context("request_id", request_id, item, ["request_reference", "request_title", "title"], "request_status")

    async def _offer_context(self, agency_id: str | None, offer_id: str | None) -> dict[str, Any]:
        item = await self._lookup_agency_record("offer_workspaces_v2", agency_id, offer_id, ["offer_reference"])
        if not item:
            item = await self._lookup_agency_record("offer_workspaces", agency_id, offer_id, ["workspace_reference", "offer_reference"])
        if not item:
            item = await self._lookup_agency_record("offers", agency_id, offer_id, ["offer_reference"])
        return self._compact_context("offer_id", offer_id, item, ["workspace_reference", "offer_reference", "title", "offer_title"], "status")

    async def _booking_context(self, agency_id: str | None, booking_id: str | None) -> dict[str, Any]:
        item = await self._lookup_agency_record("booking_workspaces", agency_id, booking_id, ["workspace_reference", "booking_reference"])
        if not item:
            item = await self._lookup_agency_record("booking_records", agency_id, booking_id, ["booking_reference", "record_locator"])
        if not item:
            item = await self._lookup_agency_record("bookings", agency_id, booking_id, ["booking_reference", "record_locator"])
        return self._compact_context("booking_id", booking_id, item, ["workspace_reference", "booking_reference", "record_locator", "title"], "status")

    async def _ticket_context(self, agency_id: str | None, ticket_id: str | None) -> dict[str, Any]:
        item = await self._lookup_agency_record("ticket_records", agency_id, ticket_id, ["ticket_number"])
        return self._compact_context("ticket_id", ticket_id, item, ["ticket_number", "document_number", "title"], "status")

    async def _emd_context(self, agency_id: str | None, emd_id: str | None) -> dict[str, Any]:
        item = await self._lookup_agency_record("emd_records", agency_id, emd_id, ["emd_number"])
        return self._compact_context("emd_id", emd_id, item, ["emd_number", "document_number", "title"], "status")

    async def _document_context(self, agency_id: str | None, document_id: str | None) -> dict[str, Any]:
        item = await self._lookup_agency_record("rendered_documents", agency_id, document_id, ["document_reference"])
        if not item:
            item = await self._lookup_agency_record("document_packages", agency_id, document_id, ["package_reference"])
        return self._compact_context("document_id", document_id, item, ["title", "document_title", "filename", "package_title"], "status")

    async def _lookup_agency_record(
        self,
        collection: str,
        agency_id: str | None,
        record_id: str | None,
        alternate_keys: list[str] | None = None,
    ) -> dict[str, Any] | None:
        if not record_id:
            return None
        filters = {"id": record_id}
        if agency_id:
            filters["agency_id"] = agency_id
        item = await self.db.collection(collection).find_one(filters)
        if item:
            return item
        for key in alternate_keys or []:
            alt_filters = {key: record_id}
            if agency_id:
                alt_filters["agency_id"] = agency_id
            item = await self.db.collection(collection).find_one(alt_filters)
            if item:
                return item
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
            "label": self._label_from_item(item, label_keys) or fallback_id,
            "status": item.get(status_key),
            "metadata_only": True,
        }

    def _label_from_item(self, item: dict[str, Any], keys: list[str]) -> str | None:
        for key in keys:
            if item.get(key):
                if key in {"first_name", "last_name"}:
                    name = " ".join(str(item.get(part) or "").strip() for part in ["first_name", "last_name"]).strip()
                    return name or str(item[key])
                return str(item[key])
        return None

    def _trip_display_name(self, item: dict[str, Any]) -> str:
        route = " - ".join(part for part in [item.get("origin_airport") or item.get("departure_city"), item.get("destination_airport") or item.get("destination_city")] if part)
        if route:
            return f"{item.get('trip_reference') or item.get('id')}: {route}"
        return item.get("trip_reference") or item.get("id") or "Trip"

    def _date_matches(self, value: date | str | None, target: date) -> bool:
        if not value:
            return False
        if isinstance(value, date):
            return value == target
        if isinstance(value, str):
            return value[:10] == target.isoformat()
        return False

    def _count_value(self, target: dict[str, int], value: Any) -> None:
        if value:
            target[str(value)] = target.get(str(value), 0) + 1

    def _validate_status(self, value: str) -> None:
        if value not in TRIP_STATUSES:
            raise ValueError("Unsupported trip workspace status.")

    def _parse_date(self, value: date | str | None) -> date:
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            return date.fromisoformat(value[:10])
        raise ValueError("A departure date filter requires an ISO date.")

    def _trip_reference(self) -> str:
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
            "trip_workspace_metadata_only": True,
            "booking_execution_disabled": True,
            "ticket_issuance_disabled": True,
            "gds_connectivity_disabled": True,
            "ndc_connectivity_disabled": True,
            "airline_apis_disabled": True,
            "airline_api_calls_disabled": True,
            "payment_processing_disabled": True,
            "invoicing_disabled": True,
            "ai_disabled": True,
            "background_workers_disabled": True,
            "automatic_trip_generation_disabled": True,
            "automatic_itinerary_generation_disabled": True,
            "itinerary_generation_disabled": True,
            "external_integrations_disabled": True,
            "external_api_calls_disabled": True,
            "automation_disabled": True,
        }
