from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from database import Database
from models import FlightWorkspace, FlightWorkspaceCreate, FlightWorkspaceUpdate, new_id
from services.offer_decision_export_delivery_service import actor_from_user, payload_dict


PHASE_LABEL = "phase_50_9_intelligent_offer_builder_integration_foundation"

FLIGHT_WORKSPACE_COLLECTION = "flight_workspaces"
FLIGHT_STATUSES = ["draft", "active", "schedule_review", "ready", "flown", "archived"]


class FlightWorkspaceService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_platform_flights(
        self,
        *,
        agency_id: str | None = None,
        status: str | None = None,
        airline: str | None = None,
        departure_airport: str | None = None,
        arrival_airport: str | None = None,
        departure_date: date | str | None = None,
        cabin: str | None = None,
        booking_class: str | None = None,
        operational_workspace_id: str | None = None,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if status:
            filters["flight_status"] = status
        if departure_airport:
            filters["departure_airport"] = departure_airport
        if arrival_airport:
            filters["arrival_airport"] = arrival_airport
        if cabin:
            filters["cabin_class"] = cabin
        if booking_class:
            filters["booking_class"] = booking_class
        if operational_workspace_id:
            filters["operational_workspace_id"] = operational_workspace_id
        flights = await self.db.collection(FLIGHT_WORKSPACE_COLLECTION).find_many(filters or None)
        if not include_archived:
            flights = [item for item in flights if not item.get("deleted_at") and item.get("flight_status") != "archived"]
        if airline:
            flights = [item for item in flights if self._airline_matches(item, airline)]
        if departure_date:
            target = self._parse_date(departure_date)
            flights = [item for item in flights if self._datetime_matches_date(item.get("departure_datetime"), target)]
        flights.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._platform_projection(item) for item in flights]

    async def list_agency_flights(
        self,
        agency_id: str,
        *,
        status: str | None = None,
        airline: str | None = None,
        departure_airport: str | None = None,
        arrival_airport: str | None = None,
        departure_date: date | str | None = None,
        cabin: str | None = None,
        booking_class: str | None = None,
        operational_workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        flights = await self.list_platform_flights(
            agency_id=agency_id,
            status=status,
            airline=airline,
            departure_airport=departure_airport,
            arrival_airport=arrival_airport,
            departure_date=departure_date,
            cabin=cabin,
            booking_class=booking_class,
            operational_workspace_id=operational_workspace_id,
        )
        return [self._agency_projection(item) for item in flights if item.get("agency_id") == agency_id]

    async def platform_response(
        self,
        *,
        agency_id: str | None = None,
        status: str | None = None,
        airline: str | None = None,
        departure_airport: str | None = None,
        arrival_airport: str | None = None,
        departure_date: date | str | None = None,
        cabin: str | None = None,
        booking_class: str | None = None,
        operational_workspace_id: str | None = None,
        include_archived: bool = False,
    ) -> dict[str, Any]:
        items = await self.list_platform_flights(
            agency_id=agency_id,
            status=status,
            airline=airline,
            departure_airport=departure_airport,
            arrival_airport=arrival_airport,
            departure_date=departure_date,
            cabin=cabin,
            booking_class=booking_class,
            operational_workspace_id=operational_workspace_id,
            include_archived=include_archived,
        )
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "flight_workspace_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Flight workspaces are metadata only. They do not execute bookings, run live flight search, connect to GDS or NDC, call airline APIs, process payments, issue tickets, synchronize schedules, call external APIs, use AI, run background workers, automatically generate routes, validate flights, look up airlines, or update live schedules.",
            **self.safety_flags(),
        }

    async def agency_response(
        self,
        agency_id: str,
        *,
        status: str | None = None,
        airline: str | None = None,
        departure_airport: str | None = None,
        arrival_airport: str | None = None,
        departure_date: date | str | None = None,
        cabin: str | None = None,
        booking_class: str | None = None,
        operational_workspace_id: str | None = None,
    ) -> dict[str, Any]:
        items = await self.list_agency_flights(
            agency_id,
            status=status,
            airline=airline,
            departure_airport=departure_airport,
            arrival_airport=arrival_airport,
            departure_date=departure_date,
            cabin=cabin,
            booking_class=booking_class,
            operational_workspace_id=operational_workspace_id,
        )
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "flight_workspace_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            "notice": "Flight workspace metadata is read-only for this agency. It does not execute bookings, run live flight search, connect to GDS or NDC, call airline APIs, process payments, issue tickets, synchronize schedules, call external APIs, use AI, run background workers, automatically generate routes, validate flights, look up airlines, or update live schedules.",
            **self.safety_flags(),
        }

    async def platform_summary(self) -> dict[str, Any]:
        items = await self.list_platform_flights(include_archived=True)
        return {
            "phase": PHASE_LABEL,
            "summary": self.summarize_counts(items),
            "flight_workspace_count": len(items),
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        items = await self.list_agency_flights(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(items),
            "flight_workspace_count": len(items),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def get_platform_flight(self, flight_workspace_id: str) -> dict[str, Any]:
        flight_workspace = await self._require_flight_workspace(flight_workspace_id)
        return await self._platform_projection(flight_workspace)

    async def get_agency_flight(self, agency_id: str, flight_workspace_id: str) -> dict[str, Any]:
        flight_workspace = await self.get_platform_flight(flight_workspace_id)
        if flight_workspace.get("agency_id") != agency_id:
            raise ValueError("Flight workspace metadata was not found for this agency.")
        return self._agency_projection(flight_workspace)

    async def create_flight(
        self,
        payload: FlightWorkspaceCreate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        self._validate_status(data.get("flight_status") or "active")
        flight_workspace = FlightWorkspace(
            id=data.get("id") or new_id(),
            agency_id=data["agency_id"],
            operational_workspace_id=data.get("operational_workspace_id"),
            flight_reference=data.get("flight_reference") or self._flight_reference(),
            flight_status=data.get("flight_status") or "active",
            flight_type=data.get("flight_type"),
            travel_direction=data.get("travel_direction"),
            airline_code=data.get("airline_code"),
            airline_name=data.get("airline_name"),
            marketing_carrier=data.get("marketing_carrier"),
            operating_carrier=data.get("operating_carrier"),
            flight_number=data.get("flight_number"),
            operating_flight_number=data.get("operating_flight_number"),
            departure_airport=data.get("departure_airport"),
            arrival_airport=data.get("arrival_airport"),
            departure_terminal=data.get("departure_terminal"),
            arrival_terminal=data.get("arrival_terminal"),
            departure_datetime=data.get("departure_datetime"),
            arrival_datetime=data.get("arrival_datetime"),
            aircraft_type=data.get("aircraft_type"),
            cabin_class=data.get("cabin_class"),
            booking_class=data.get("booking_class"),
            fare_family=data.get("fare_family"),
            baggage_summary=data.get("baggage_summary"),
            connection_summary=data.get("connection_summary"),
            stopover_summary=data.get("stopover_summary"),
            elapsed_travel_time=data.get("elapsed_travel_time"),
            operating_days=data.get("operating_days") or [],
            passenger_ids=data.get("passenger_ids") or [],
            linked_request_ids=data.get("linked_request_ids") or [],
            linked_trip_ids=data.get("linked_trip_ids") or [],
            linked_offer_ids=data.get("linked_offer_ids") or [],
            linked_booking_ids=data.get("linked_booking_ids") or [],
            linked_ticket_ids=data.get("linked_ticket_ids") or [],
            linked_document_ids=data.get("linked_document_ids") or [],
            operational_notes=data.get("operational_notes"),
            created_by=actor_from_user(user),
            updated_by=actor_from_user(user),
            metadata=data.get("metadata") or {},
        )
        stored = await self.db.collection(FLIGHT_WORKSPACE_COLLECTION).insert_one(flight_workspace.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "flight_workspace": await self._platform_projection(stored),
            "metadata_only": True,
            "notice": "Flight workspace metadata was saved only. No booking, live search, GDS/NDC, airline API, payment, ticketing, schedule synchronization, external API, AI, worker, route generation, validation, airline lookup, live schedule update, or automation action ran.",
            **self.safety_flags(),
        }

    async def update_flight(
        self,
        flight_workspace_id: str,
        payload: FlightWorkspaceUpdate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_flight_workspace(flight_workspace_id)
        updates = {key: value for key, value in payload_dict(payload).items() if value is not None}
        if "flight_status" in updates:
            self._validate_status(updates["flight_status"])
        updates.update(
            {
                "updated_at": self._now(),
                "updated_by": actor_from_user(user),
                "metadata_only": True,
                "flight_workspace_metadata_only": True,
            }
        )
        updated = await self.db.collection(FLIGHT_WORKSPACE_COLLECTION).update_one({"id": existing["id"]}, updates)
        stored = updated or {**existing, **updates}
        return {
            "phase": PHASE_LABEL,
            "flight_workspace": await self._platform_projection(stored),
            "metadata_only": True,
            "notice": "Flight workspace metadata was updated only. No booking, live search, schedule sync, provider, payment, ticketing, AI, external API, validation, lookup, worker, route generation, or automation action ran.",
            **self.safety_flags(),
        }

    async def delete_flight(self, flight_workspace_id: str, user: dict | None = None) -> dict[str, Any]:
        existing = await self._require_flight_workspace(flight_workspace_id)
        updates = {
            "flight_status": "archived",
            "deleted_at": self._now(),
            "deleted_by": actor_from_user(user),
            "updated_by": actor_from_user(user),
            "metadata_only": True,
            "flight_workspace_metadata_only": True,
            "flight_workspace_archived_metadata_only": True,
        }
        updated = await self.db.collection(FLIGHT_WORKSPACE_COLLECTION).update_one({"id": existing["id"]}, updates)
        stored = updated or {**existing, **updates}
        return {
            "phase": PHASE_LABEL,
            "flight_workspace": await self._platform_projection(stored),
            "deleted": True,
            "metadata_only": True,
            "notice": "Flight workspace metadata was archived only. No booking, live search, GDS/NDC, airline API, payment, ticketing, schedule sync, external API, AI, worker, route generation, validation, live update, or automation ran.",
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        by_status = {status: 0 for status in FLIGHT_STATUSES}
        by_airline_code: dict[str, int] = {}
        by_departure_airport: dict[str, int] = {}
        by_arrival_airport: dict[str, int] = {}
        by_cabin_class: dict[str, int] = {}
        by_booking_class: dict[str, int] = {}
        agency_ids: set[str] = set()
        operational_workspace_ids: set[str] = set()
        linked_counts = {
            "passenger_count": 0,
            "linked_request_count": 0,
            "linked_trip_count": 0,
            "linked_offer_count": 0,
            "linked_booking_count": 0,
            "linked_ticket_count": 0,
            "linked_document_count": 0,
        }
        for item in items:
            status = item.get("flight_status") or "active"
            by_status[status] = by_status.get(status, 0) + 1
            self._count_value(by_airline_code, item.get("airline_code"))
            self._count_value(by_departure_airport, item.get("departure_airport"))
            self._count_value(by_arrival_airport, item.get("arrival_airport"))
            self._count_value(by_cabin_class, item.get("cabin_class"))
            self._count_value(by_booking_class, item.get("booking_class"))
            if item.get("agency_id"):
                agency_ids.add(item["agency_id"])
            if item.get("operational_workspace_id"):
                operational_workspace_ids.add(item["operational_workspace_id"])
            linked_counts["passenger_count"] += len(item.get("passenger_ids") or [])
            linked_counts["linked_request_count"] += len(item.get("linked_request_ids") or [])
            linked_counts["linked_trip_count"] += len(item.get("linked_trip_ids") or [])
            linked_counts["linked_offer_count"] += len(item.get("linked_offer_ids") or [])
            linked_counts["linked_booking_count"] += len(item.get("linked_booking_ids") or [])
            linked_counts["linked_ticket_count"] += len(item.get("linked_ticket_ids") or [])
            linked_counts["linked_document_count"] += len(item.get("linked_document_ids") or [])
        return {
            "total_count": len(items),
            "by_status": by_status,
            "by_airline_code": by_airline_code,
            "by_departure_airport": by_departure_airport,
            "by_arrival_airport": by_arrival_airport,
            "by_cabin_class": by_cabin_class,
            "by_booking_class": by_booking_class,
            "agency_count": len(agency_ids),
            "operational_workspace_count": len(operational_workspace_ids),
            "archived_count": by_status.get("archived", 0),
            **linked_counts,
            "metadata_only": True,
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "statuses": FLIGHT_STATUSES,
            "supports_airline_filter": True,
            "supports_departure_airport_filter": True,
            "supports_arrival_airport_filter": True,
            "supports_departure_date_filter": True,
            "supports_cabin_filter": True,
            "supports_booking_class_filter": True,
            "supports_operational_workspace_filter": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def _require_flight_workspace(self, flight_workspace_id: str) -> dict[str, Any]:
        flight_workspace = await self.db.collection(FLIGHT_WORKSPACE_COLLECTION).find_one({"id": flight_workspace_id})
        if not flight_workspace:
            flight_workspace = await self.db.collection(FLIGHT_WORKSPACE_COLLECTION).find_one({"flight_reference": flight_workspace_id})
        if not flight_workspace:
            raise ValueError("Flight workspace metadata was not found.")
        return flight_workspace

    async def _platform_projection(self, flight_workspace: dict[str, Any]) -> dict[str, Any]:
        projected = dict(flight_workspace)
        projected["flight_designator"] = self._flight_designator(projected)
        projected["agency"] = await self._agency_context(projected.get("agency_id"))
        projected["agency_name"] = projected["agency"].get("agency_name")
        projected["operational_workspace"] = await self._operational_workspace_context(projected.get("operational_workspace_id"))
        projected["passengers"] = [
            await self._passenger_context(projected.get("agency_id"), passenger_id)
            for passenger_id in projected.get("passenger_ids") or []
        ]
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
        projected["flight_workspace_metadata_only"] = True
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

    async def _passenger_context(self, agency_id: str | None, passenger_id: str | None) -> dict[str, Any]:
        item = await self._lookup_agency_record("passenger_workspaces", agency_id, passenger_id, ["passenger_reference"])
        if not item:
            item = await self._lookup_agency_record("passengers", agency_id, passenger_id, ["passenger_reference"])
        return self._compact_context("passenger_id", passenger_id, item, ["passenger_reference", "preferred_name", "first_name", "last_name"], "passenger_status")

    async def _request_context(self, agency_id: str | None, request_id: str | None) -> dict[str, Any]:
        item = await self._lookup_agency_record("travel_request_workspaces", agency_id, request_id, ["request_reference"])
        if not item:
            item = await self._lookup_agency_record("travel_requests", agency_id, request_id, ["request_reference"])
        return self._compact_context("request_id", request_id, item, ["request_reference", "request_title", "title"], "request_status")

    async def _trip_context(self, agency_id: str | None, trip_id: str | None) -> dict[str, Any]:
        item = await self._lookup_agency_record("trip_dossiers", agency_id, trip_id, ["trip_reference"])
        return self._compact_context("trip_id", trip_id, item, ["trip_reference", "title", "trip_name"], "status")

    async def _offer_context(self, agency_id: str | None, offer_id: str | None) -> dict[str, Any]:
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

    def _airline_matches(self, item: dict[str, Any], expected: str) -> bool:
        expected_text = expected.lower()
        values = [
            item.get("airline_code"),
            item.get("airline_name"),
            item.get("marketing_carrier"),
            item.get("operating_carrier"),
        ]
        return any(expected_text in str(value or "").lower() for value in values)

    def _datetime_matches_date(self, value: datetime | str | None, target: date) -> bool:
        if not value:
            return False
        if isinstance(value, datetime):
            return value.date() == target
        if isinstance(value, str):
            return value[:10] == target.isoformat()
        return False

    def _flight_designator(self, item: dict[str, Any]) -> str:
        carrier = item.get("marketing_carrier") or item.get("airline_code") or item.get("operating_carrier")
        flight_number = item.get("flight_number") or item.get("operating_flight_number")
        if carrier and flight_number:
            return f"{carrier}{flight_number}"
        return item.get("flight_reference") or item.get("id") or "Flight"

    def _count_value(self, target: dict[str, int], value: Any) -> None:
        if value:
            target[str(value)] = target.get(str(value), 0) + 1

    def _validate_status(self, value: str) -> None:
        if value not in FLIGHT_STATUSES:
            raise ValueError("Unsupported flight workspace status.")

    def _parse_date(self, value: date | str | None) -> date:
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            return date.fromisoformat(value[:10])
        raise ValueError("A departure date filter requires an ISO date.")

    def _flight_reference(self) -> str:
        return f"FLW-{new_id()[:8].upper()}"

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _sort_text(self, value: Any) -> str:
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value or "")

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "flight_workspace_metadata_only": True,
            "booking_execution_disabled": True,
            "live_flight_search_disabled": True,
            "flight_search_disabled": True,
            "gds_connectivity_disabled": True,
            "ndc_connectivity_disabled": True,
            "airline_apis_disabled": True,
            "airline_api_calls_disabled": True,
            "payment_disabled": True,
            "payment_processing_disabled": True,
            "ticket_issuance_disabled": True,
            "schedule_synchronization_disabled": True,
            "external_api_calls_disabled": True,
            "ai_disabled": True,
            "background_workers_disabled": True,
            "automatic_route_generation_disabled": True,
            "flight_validation_disabled": True,
            "airline_lookups_disabled": True,
            "live_schedule_updates_disabled": True,
            "automation_disabled": True,
        }
