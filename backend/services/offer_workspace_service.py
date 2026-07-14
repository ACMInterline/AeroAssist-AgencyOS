from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from database import Database
from models import OfferWorkspaceV2, OfferWorkspaceV2Create, OfferWorkspaceV2Update, new_id
from services.offer_decision_export_delivery_service import actor_from_user, payload_dict


PHASE_LABEL = "phase_55_9_airline_intelligence_scale_release_readiness_foundation"

OFFER_WORKSPACE_COLLECTION = "offer_workspaces_v2"
OFFER_STATUSES = ["draft", "preparing", "review", "ready", "shared", "accepted", "declined", "expired", "archived"]


class OfferWorkspaceService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_platform_offers(
        self,
        *,
        agency_id: str | None = None,
        status: str | None = None,
        validity: date | str | None = None,
        client_id: str | None = None,
        destination: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        assigned_agent: str | None = None,
        trip_workspace_id: str | None = None,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if status:
            filters["offer_status"] = status
        if client_id:
            filters["client_id"] = client_id
        if assigned_agent:
            filters["assigned_agent"] = assigned_agent
        if trip_workspace_id:
            filters["trip_workspace_id"] = trip_workspace_id
        offers = await self.db.collection(OFFER_WORKSPACE_COLLECTION).find_many(filters or None)
        if not include_archived:
            offers = [item for item in offers if not item.get("deleted_at") and item.get("offer_status") != "archived"]
        if validity:
            target = self._parse_date(validity)
            offers = [item for item in offers if self._date_matches(item.get("validity_date"), target)]
        if destination:
            offers = [item for item in offers if self._destination_matches(item, destination)]
        if min_price is not None:
            offers = [item for item in offers if self._price_value(item.get("total_price")) is not None and self._price_value(item.get("total_price")) >= min_price]
        if max_price is not None:
            offers = [item for item in offers if self._price_value(item.get("total_price")) is not None and self._price_value(item.get("total_price")) <= max_price]
        offers.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._platform_projection(item) for item in offers]

    async def list_agency_offers(
        self,
        agency_id: str,
        *,
        status: str | None = None,
        validity: date | str | None = None,
        client_id: str | None = None,
        destination: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        assigned_agent: str | None = None,
        trip_workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        offers = await self.list_platform_offers(
            agency_id=agency_id,
            status=status,
            validity=validity,
            client_id=client_id,
            destination=destination,
            min_price=min_price,
            max_price=max_price,
            assigned_agent=assigned_agent,
            trip_workspace_id=trip_workspace_id,
        )
        return [self._agency_projection(item) for item in offers if item.get("agency_id") == agency_id]

    async def platform_response(
        self,
        *,
        agency_id: str | None = None,
        status: str | None = None,
        validity: date | str | None = None,
        client_id: str | None = None,
        destination: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        assigned_agent: str | None = None,
        trip_workspace_id: str | None = None,
        include_archived: bool = False,
    ) -> dict[str, Any]:
        items = await self.list_platform_offers(
            agency_id=agency_id,
            status=status,
            validity=validity,
            client_id=client_id,
            destination=destination,
            min_price=min_price,
            max_price=max_price,
            assigned_agent=assigned_agent,
            trip_workspace_id=trip_workspace_id,
            include_archived=include_archived,
        )
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "offer_workspace_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Offer workspaces are metadata only. They do not execute bookings, issue tickets, process payments, connect to GDS or NDC, call airline APIs, calculate fares, generate AI itineraries, integrate suppliers, call external APIs, automatically convert bookings, or run background workers.",
            **self.safety_flags(),
        }

    async def agency_response(
        self,
        agency_id: str,
        *,
        status: str | None = None,
        validity: date | str | None = None,
        client_id: str | None = None,
        destination: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        assigned_agent: str | None = None,
        trip_workspace_id: str | None = None,
    ) -> dict[str, Any]:
        items = await self.list_agency_offers(
            agency_id,
            status=status,
            validity=validity,
            client_id=client_id,
            destination=destination,
            min_price=min_price,
            max_price=max_price,
            assigned_agent=assigned_agent,
            trip_workspace_id=trip_workspace_id,
        )
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "offer_workspace_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            "notice": "Offer workspace metadata is read-only for this agency. It does not execute bookings, issue tickets, process payments, connect to GDS or NDC, call airline APIs, calculate fares, generate AI itineraries, integrate suppliers, call external APIs, automatically convert bookings, or run background workers.",
            **self.safety_flags(),
        }

    async def platform_summary(self) -> dict[str, Any]:
        items = await self.list_platform_offers(include_archived=True)
        return {
            "phase": PHASE_LABEL,
            "summary": self.summarize_counts(items),
            "offer_workspace_count": len(items),
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        items = await self.list_agency_offers(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(items),
            "offer_workspace_count": len(items),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def get_platform_offer(self, offer_workspace_id: str) -> dict[str, Any]:
        offer_workspace = await self._require_offer_workspace(offer_workspace_id)
        return await self._platform_projection(offer_workspace)

    async def get_agency_offer(self, agency_id: str, offer_workspace_id: str) -> dict[str, Any]:
        offer_workspace = await self.get_platform_offer(offer_workspace_id)
        if offer_workspace.get("agency_id") != agency_id:
            raise ValueError("Offer workspace metadata was not found for this agency.")
        return self._agency_projection(offer_workspace)

    async def create_offer(
        self,
        payload: OfferWorkspaceV2Create | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        self._validate_status(data.get("offer_status") or "draft")
        offer_workspace = OfferWorkspaceV2(
            id=data.get("id") or new_id(),
            agency_id=data["agency_id"],
            operational_workspace_id=data.get("operational_workspace_id"),
            trip_workspace_id=data.get("trip_workspace_id"),
            offer_reference=data.get("offer_reference") or self._offer_reference(),
            offer_status=data.get("offer_status") or "draft",
            offer_type=data.get("offer_type"),
            client_id=data.get("client_id"),
            passenger_ids=data.get("passenger_ids") or [],
            flight_workspace_ids=data.get("flight_workspace_ids") or [],
            offer_title=data["offer_title"],
            offer_summary=data.get("offer_summary"),
            destination_summary=data.get("destination_summary"),
            itinerary_summary=data.get("itinerary_summary"),
            pricing_summary=data.get("pricing_summary"),
            currency=data.get("currency"),
            total_price=data.get("total_price"),
            taxes_summary=data.get("taxes_summary"),
            fees_summary=data.get("fees_summary"),
            ancillary_summary=data.get("ancillary_summary"),
            baggage_summary=data.get("baggage_summary"),
            seat_summary=data.get("seat_summary"),
            meal_summary=data.get("meal_summary"),
            hotel_summary=data.get("hotel_summary"),
            transfer_summary=data.get("transfer_summary"),
            insurance_summary=data.get("insurance_summary"),
            validity_date=data.get("validity_date"),
            assigned_agent=data.get("assigned_agent"),
            agent_notes=data.get("agent_notes"),
            customer_notes=data.get("customer_notes"),
            internal_notes=data.get("internal_notes"),
            linked_booking_ids=data.get("linked_booking_ids") or [],
            linked_ticket_ids=data.get("linked_ticket_ids") or [],
            linked_document_ids=data.get("linked_document_ids") or [],
            created_by=actor_from_user(user),
            updated_by=actor_from_user(user),
            metadata=data.get("metadata") or {},
        )
        stored = await self.db.collection(OFFER_WORKSPACE_COLLECTION).insert_one(offer_workspace.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "offer_workspace": await self._platform_projection(stored),
            "metadata_only": True,
            "notice": "Offer workspace metadata was saved only. No booking, ticketing, payment, GDS/NDC, airline API, fare calculation, AI itinerary generation, supplier integration, external API, booking conversion, worker, or automation action ran.",
            **self.safety_flags(),
        }

    async def update_offer(
        self,
        offer_workspace_id: str,
        payload: OfferWorkspaceV2Update | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_offer_workspace(offer_workspace_id)
        updates = {key: value for key, value in payload_dict(payload).items() if value is not None}
        if "offer_status" in updates:
            self._validate_status(updates["offer_status"])
        updates.update(
            {
                "updated_at": self._now(),
                "updated_by": actor_from_user(user),
                "metadata_only": True,
                "offer_workspace_metadata_only": True,
            }
        )
        updated = await self.db.collection(OFFER_WORKSPACE_COLLECTION).update_one({"id": existing["id"]}, updates)
        stored = updated or {**existing, **updates}
        return {
            "phase": PHASE_LABEL,
            "offer_workspace": await self._platform_projection(stored),
            "metadata_only": True,
            "notice": "Offer workspace metadata was updated only. No booking, ticketing, payment, GDS/NDC, airline API, fare calculation, AI itinerary generation, supplier integration, external API, booking conversion, worker, or automation action ran.",
            **self.safety_flags(),
        }

    async def delete_offer(self, offer_workspace_id: str, user: dict | None = None) -> dict[str, Any]:
        existing = await self._require_offer_workspace(offer_workspace_id)
        updates = {
            "offer_status": "archived",
            "deleted_at": self._now(),
            "deleted_by": actor_from_user(user),
            "updated_by": actor_from_user(user),
            "metadata_only": True,
            "offer_workspace_metadata_only": True,
            "offer_workspace_archived_metadata_only": True,
        }
        updated = await self.db.collection(OFFER_WORKSPACE_COLLECTION).update_one({"id": existing["id"]}, updates)
        stored = updated or {**existing, **updates}
        return {
            "phase": PHASE_LABEL,
            "offer_workspace": await self._platform_projection(stored),
            "deleted": True,
            "metadata_only": True,
            "notice": "Offer workspace metadata was archived only. No booking, ticketing, payment, GDS/NDC, airline API, fare calculation, AI itinerary generation, supplier integration, external API, booking conversion, worker, or automation ran.",
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        by_status = {status: 0 for status in OFFER_STATUSES}
        by_type: dict[str, int] = {}
        by_currency: dict[str, int] = {}
        by_destination: dict[str, int] = {}
        agency_ids: set[str] = set()
        operational_workspace_ids: set[str] = set()
        trip_workspace_ids: set[str] = set()
        assigned_agents: set[str] = set()
        price_values: list[float] = []
        linked_counts = {
            "passenger_count": 0,
            "flight_workspace_count": 0,
            "linked_booking_count": 0,
            "linked_ticket_count": 0,
            "linked_document_count": 0,
        }
        for item in items:
            status = item.get("offer_status") or "draft"
            by_status[status] = by_status.get(status, 0) + 1
            self._count_value(by_type, item.get("offer_type"))
            self._count_value(by_currency, item.get("currency"))
            self._count_value(by_destination, item.get("destination_summary"))
            if item.get("agency_id"):
                agency_ids.add(item["agency_id"])
            if item.get("operational_workspace_id"):
                operational_workspace_ids.add(item["operational_workspace_id"])
            if item.get("trip_workspace_id"):
                trip_workspace_ids.add(item["trip_workspace_id"])
            if item.get("assigned_agent"):
                assigned_agents.add(item["assigned_agent"])
            price_value = self._price_value(item.get("total_price"))
            if price_value is not None:
                price_values.append(price_value)
            linked_counts["passenger_count"] += len(item.get("passenger_ids") or [])
            linked_counts["flight_workspace_count"] += len(item.get("flight_workspace_ids") or [])
            linked_counts["linked_booking_count"] += len(item.get("linked_booking_ids") or [])
            linked_counts["linked_ticket_count"] += len(item.get("linked_ticket_ids") or [])
            linked_counts["linked_document_count"] += len(item.get("linked_document_ids") or [])
        return {
            "total_count": len(items),
            "by_status": by_status,
            "by_type": by_type,
            "by_currency": by_currency,
            "by_destination": by_destination,
            "agency_count": len(agency_ids),
            "operational_workspace_count": len(operational_workspace_ids),
            "trip_workspace_count": len(trip_workspace_ids),
            "assigned_agent_count": len(assigned_agents),
            "archived_count": by_status.get("archived", 0),
            "min_price": min(price_values) if price_values else None,
            "max_price": max(price_values) if price_values else None,
            **linked_counts,
            "metadata_only": True,
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "statuses": OFFER_STATUSES,
            "supports_status_filter": True,
            "supports_validity_filter": True,
            "supports_client_filter": True,
            "supports_destination_filter": True,
            "supports_price_range_filter": True,
            "supports_assigned_agent_filter": True,
            "supports_trip_workspace_filter": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def _require_offer_workspace(self, offer_workspace_id: str) -> dict[str, Any]:
        offer_workspace = await self.db.collection(OFFER_WORKSPACE_COLLECTION).find_one({"id": offer_workspace_id})
        if not offer_workspace:
            offer_workspace = await self.db.collection(OFFER_WORKSPACE_COLLECTION).find_one({"offer_reference": offer_workspace_id})
        if not offer_workspace:
            raise ValueError("Offer workspace metadata was not found.")
        return offer_workspace

    async def _platform_projection(self, offer_workspace: dict[str, Any]) -> dict[str, Any]:
        projected = dict(offer_workspace)
        projected["offer_display_name"] = self._offer_display_name(projected)
        projected["agency"] = await self._agency_context(projected.get("agency_id"))
        projected["agency_name"] = projected["agency"].get("agency_name")
        projected["operational_workspace"] = await self._operational_workspace_context(projected.get("operational_workspace_id"))
        projected["trip_workspace"] = await self._trip_workspace_context(projected.get("agency_id"), projected.get("trip_workspace_id"))
        projected["client"] = await self._client_context(projected.get("agency_id"), projected.get("client_id"))
        projected["passengers"] = [
            await self._passenger_context(projected.get("agency_id"), passenger_id)
            for passenger_id in projected.get("passenger_ids") or []
        ]
        projected["flight_workspaces"] = [
            await self._flight_workspace_context(projected.get("agency_id"), flight_workspace_id)
            for flight_workspace_id in projected.get("flight_workspace_ids") or []
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
        projected["offer_workspace_metadata_only"] = True
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

    async def _trip_workspace_context(self, agency_id: str | None, trip_workspace_id: str | None) -> dict[str, Any]:
        item = await self._lookup_agency_record("trip_workspaces", agency_id, trip_workspace_id, ["trip_reference"])
        return self._compact_context("trip_workspace_id", trip_workspace_id, item, ["trip_reference", "trip_status", "destination_city"], "trip_status")

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

    def _offer_display_name(self, item: dict[str, Any]) -> str:
        if item.get("offer_title"):
            return str(item["offer_title"])
        return item.get("offer_reference") or item.get("id") or "Offer workspace"

    def _date_matches(self, value: date | str | None, target: date) -> bool:
        if not value:
            return False
        if isinstance(value, date):
            return value == target
        if isinstance(value, str):
            return value[:10] == target.isoformat()
        return False

    def _destination_matches(self, item: dict[str, Any], destination: str) -> bool:
        needle = destination.strip().lower()
        haystack = " ".join(
            str(item.get(key) or "")
            for key in ["destination_summary", "offer_summary", "itinerary_summary", "hotel_summary", "transfer_summary"]
        ).lower()
        return needle in haystack

    def _price_value(self, value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _count_value(self, target: dict[str, int], value: Any) -> None:
        if value:
            target[str(value)] = target.get(str(value), 0) + 1

    def _validate_status(self, value: str) -> None:
        if value not in OFFER_STATUSES:
            raise ValueError("Unsupported offer workspace status.")

    def _parse_date(self, value: date | str | None) -> date:
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            return date.fromisoformat(value[:10])
        raise ValueError("A validity date filter requires an ISO date.")

    def _offer_reference(self) -> str:
        return f"OFW-{new_id()[:8].upper()}"

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _sort_text(self, value: Any) -> str:
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value or "")

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "offer_workspace_metadata_only": True,
            "booking_execution_disabled": True,
            "ticket_issuance_disabled": True,
            "payment_processing_disabled": True,
            "gds_connectivity_disabled": True,
            "ndc_connectivity_disabled": True,
            "airline_apis_disabled": True,
            "airline_api_calls_disabled": True,
            "fare_calculation_engines_disabled": True,
            "fare_calculation_disabled": True,
            "live_pricing_disabled": True,
            "ai_itinerary_generation_disabled": True,
            "supplier_integrations_disabled": True,
            "external_api_calls_disabled": True,
            "automatic_booking_conversion_disabled": True,
            "background_workers_disabled": True,
            "automation_disabled": True,
        }
