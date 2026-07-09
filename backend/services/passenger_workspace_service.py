from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from database import Database
from models import PassengerWorkspace, PassengerWorkspaceCreate, PassengerWorkspaceUpdate, new_id
from services.offer_decision_export_delivery_service import actor_from_user, payload_dict


PHASE_LABEL = "phase_51_3_client_passenger_master_workspace_foundation"

PASSENGER_WORKSPACE_COLLECTION = "passenger_workspaces"
PASSENGER_STATUSES = ["draft", "active", "incomplete", "review", "ready", "archived"]


class PassengerWorkspaceService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_platform_passengers(
        self,
        *,
        agency_id: str | None = None,
        status: str | None = None,
        nationality: str | None = None,
        citizenship: str | None = None,
        assistance_profile: str | None = None,
        travel_date: date | str | None = None,
        operational_workspace_id: str | None = None,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if status:
            filters["passenger_status"] = status
        if nationality:
            filters["nationality"] = nationality
        if citizenship:
            filters["citizenship"] = citizenship
        if operational_workspace_id:
            filters["operational_workspace_id"] = operational_workspace_id
        passengers = await self.db.collection(PASSENGER_WORKSPACE_COLLECTION).find_many(filters or None)
        if not include_archived:
            passengers = [item for item in passengers if not item.get("deleted_at") and item.get("passenger_status") != "archived"]
        if assistance_profile:
            passengers = [item for item in passengers if self._profile_matches(item.get("assistance_profile"), assistance_profile)]
        if travel_date:
            target = self._parse_date(travel_date)
            filtered: list[dict[str, Any]] = []
            for item in passengers:
                if await self._workspace_matches_travel_date(item.get("operational_workspace_id"), target):
                    filtered.append(item)
            passengers = filtered
        passengers.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._platform_projection(item) for item in passengers]

    async def list_agency_passengers(
        self,
        agency_id: str,
        *,
        status: str | None = None,
        nationality: str | None = None,
        citizenship: str | None = None,
        assistance_profile: str | None = None,
        travel_date: date | str | None = None,
        operational_workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        passengers = await self.list_platform_passengers(
            agency_id=agency_id,
            status=status,
            nationality=nationality,
            citizenship=citizenship,
            assistance_profile=assistance_profile,
            travel_date=travel_date,
            operational_workspace_id=operational_workspace_id,
        )
        return [self._agency_projection(item) for item in passengers if item.get("agency_id") == agency_id]

    async def platform_response(
        self,
        *,
        agency_id: str | None = None,
        status: str | None = None,
        nationality: str | None = None,
        citizenship: str | None = None,
        assistance_profile: str | None = None,
        travel_date: date | str | None = None,
        operational_workspace_id: str | None = None,
        include_archived: bool = False,
    ) -> dict[str, Any]:
        items = await self.list_platform_passengers(
            agency_id=agency_id,
            status=status,
            nationality=nationality,
            citizenship=citizenship,
            assistance_profile=assistance_profile,
            travel_date=travel_date,
            operational_workspace_id=operational_workspace_id,
            include_archived=include_archived,
        )
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "passenger_workspace_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Passenger workspaces are metadata only. They do not execute bookings, issue tickets, connect to GDS or NDC, process payments, integrate suppliers, use AI, send email or SMS, run background workers, call external APIs, automatically match profiles, automatically validate documents, or communicate with airlines.",
            **self.safety_flags(),
        }

    async def agency_response(
        self,
        agency_id: str,
        *,
        status: str | None = None,
        nationality: str | None = None,
        citizenship: str | None = None,
        assistance_profile: str | None = None,
        travel_date: date | str | None = None,
        operational_workspace_id: str | None = None,
    ) -> dict[str, Any]:
        items = await self.list_agency_passengers(
            agency_id,
            status=status,
            nationality=nationality,
            citizenship=citizenship,
            assistance_profile=assistance_profile,
            travel_date=travel_date,
            operational_workspace_id=operational_workspace_id,
        )
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "passenger_workspace_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            "notice": "Passenger workspace metadata is read-only for this agency. It does not execute bookings, issue tickets, connect to GDS or NDC, process payments, integrate suppliers, use AI, send email or SMS, run background workers, call external APIs, automatically match profiles, automatically validate documents, or communicate with airlines.",
            **self.safety_flags(),
        }

    async def platform_summary(self) -> dict[str, Any]:
        items = await self.list_platform_passengers(include_archived=True)
        return {
            "phase": PHASE_LABEL,
            "summary": self.summarize_counts(items),
            "passenger_workspace_count": len(items),
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        items = await self.list_agency_passengers(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(items),
            "passenger_workspace_count": len(items),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def get_platform_passenger(self, passenger_workspace_id: str) -> dict[str, Any]:
        passenger_workspace = await self._require_passenger_workspace(passenger_workspace_id)
        return await self._platform_projection(passenger_workspace)

    async def get_agency_passenger(self, agency_id: str, passenger_workspace_id: str) -> dict[str, Any]:
        passenger_workspace = await self.get_platform_passenger(passenger_workspace_id)
        if passenger_workspace.get("agency_id") != agency_id:
            raise ValueError("Passenger workspace metadata was not found for this agency.")
        return self._agency_projection(passenger_workspace)

    async def create_passenger(
        self,
        payload: PassengerWorkspaceCreate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = payload_dict(payload)
        self._validate_status(data.get("passenger_status") or "active")
        passenger_workspace = PassengerWorkspace(
            id=data.get("id") or new_id(),
            agency_id=data["agency_id"],
            operational_workspace_id=data.get("operational_workspace_id"),
            passenger_reference=data.get("passenger_reference") or self._passenger_reference(),
            passenger_status=data.get("passenger_status") or "active",
            title=data.get("title"),
            first_name=data.get("first_name"),
            middle_name=data.get("middle_name"),
            last_name=data.get("last_name"),
            preferred_name=data.get("preferred_name"),
            gender=data.get("gender"),
            date_of_birth=data.get("date_of_birth"),
            nationality=data.get("nationality"),
            citizenship=data.get("citizenship"),
            passport_number=data.get("passport_number"),
            passport_expiry=data.get("passport_expiry"),
            passport_country=data.get("passport_country"),
            identity_document_type=data.get("identity_document_type"),
            loyalty_programs=data.get("loyalty_programs") or [],
            frequent_flyer_numbers=data.get("frequent_flyer_numbers") or [],
            known_traveler_numbers=data.get("known_traveler_numbers") or [],
            emergency_contact=data.get("emergency_contact") or {},
            mobility_profile=data.get("mobility_profile") or {},
            medical_profile=data.get("medical_profile") or {},
            dietary_profile=data.get("dietary_profile") or {},
            assistance_profile=data.get("assistance_profile") or {},
            baggage_profile=data.get("baggage_profile") or {},
            seating_preferences=data.get("seating_preferences") or {},
            language_preferences=data.get("language_preferences") or [],
            contact_email=data.get("contact_email"),
            contact_phone=data.get("contact_phone"),
            linked_request_ids=data.get("linked_request_ids") or [],
            linked_trip_ids=data.get("linked_trip_ids") or [],
            linked_offer_ids=data.get("linked_offer_ids") or [],
            linked_booking_ids=data.get("linked_booking_ids") or [],
            linked_ticket_ids=data.get("linked_ticket_ids") or [],
            linked_document_ids=data.get("linked_document_ids") or [],
            internal_notes=data.get("internal_notes"),
            created_by=actor_from_user(user),
            updated_by=actor_from_user(user),
            metadata=data.get("metadata") or {},
        )
        stored = await self.db.collection(PASSENGER_WORKSPACE_COLLECTION).insert_one(passenger_workspace.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "passenger_workspace": await self._platform_projection(stored),
            "metadata_only": True,
            "notice": "Passenger workspace metadata was saved only. No booking, ticketing, GDS/NDC, payment, supplier, AI, email, SMS, background worker, external API, profile matching, document validation, airline communication, or automation action ran.",
            **self.safety_flags(),
        }

    async def update_passenger(
        self,
        passenger_workspace_id: str,
        payload: PassengerWorkspaceUpdate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_passenger_workspace(passenger_workspace_id)
        updates = {key: value for key, value in payload_dict(payload).items() if value is not None}
        if "passenger_status" in updates:
            self._validate_status(updates["passenger_status"])
        updates.update(
            {
                "updated_at": self._now(),
                "updated_by": actor_from_user(user),
                "metadata_only": True,
                "passenger_workspace_metadata_only": True,
            }
        )
        updated = await self.db.collection(PASSENGER_WORKSPACE_COLLECTION).update_one({"id": existing["id"]}, updates)
        stored = updated or {**existing, **updates}
        return {
            "phase": PHASE_LABEL,
            "passenger_workspace": await self._platform_projection(stored),
            "metadata_only": True,
            "notice": "Passenger workspace metadata was updated only. No booking, ticketing, validation, matching, provider, payment, messaging, AI, external API, worker, airline communication, or automation action ran.",
            **self.safety_flags(),
        }

    async def delete_passenger(self, passenger_workspace_id: str, user: dict | None = None) -> dict[str, Any]:
        existing = await self._require_passenger_workspace(passenger_workspace_id)
        updates = {
            "passenger_status": "archived",
            "deleted_at": self._now(),
            "deleted_by": actor_from_user(user),
            "updated_by": actor_from_user(user),
            "metadata_only": True,
            "passenger_workspace_metadata_only": True,
            "passenger_workspace_archived_metadata_only": True,
        }
        updated = await self.db.collection(PASSENGER_WORKSPACE_COLLECTION).update_one({"id": existing["id"]}, updates)
        stored = updated or {**existing, **updates}
        return {
            "phase": PHASE_LABEL,
            "passenger_workspace": await self._platform_projection(stored),
            "deleted": True,
            "metadata_only": True,
            "notice": "Passenger workspace metadata was archived only. No booking, ticketing, GDS/NDC, payment, supplier, AI, email, SMS, background worker, external API, profile matching, document validation, airline communication, or automation ran.",
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        by_status = {status: 0 for status in PASSENGER_STATUSES}
        by_nationality: dict[str, int] = {}
        by_citizenship: dict[str, int] = {}
        agency_ids: set[str] = set()
        operational_workspace_ids: set[str] = set()
        linked_counts = {
            "linked_request_count": 0,
            "linked_trip_count": 0,
            "linked_offer_count": 0,
            "linked_booking_count": 0,
            "linked_ticket_count": 0,
            "linked_document_count": 0,
        }
        assistance_profile_count = 0
        for item in items:
            status = item.get("passenger_status") or "active"
            by_status[status] = by_status.get(status, 0) + 1
            if item.get("nationality"):
                by_nationality[item["nationality"]] = by_nationality.get(item["nationality"], 0) + 1
            if item.get("citizenship"):
                by_citizenship[item["citizenship"]] = by_citizenship.get(item["citizenship"], 0) + 1
            if item.get("agency_id"):
                agency_ids.add(item["agency_id"])
            if item.get("operational_workspace_id"):
                operational_workspace_ids.add(item["operational_workspace_id"])
            if item.get("assistance_profile"):
                assistance_profile_count += 1
            linked_counts["linked_request_count"] += len(item.get("linked_request_ids") or [])
            linked_counts["linked_trip_count"] += len(item.get("linked_trip_ids") or [])
            linked_counts["linked_offer_count"] += len(item.get("linked_offer_ids") or [])
            linked_counts["linked_booking_count"] += len(item.get("linked_booking_ids") or [])
            linked_counts["linked_ticket_count"] += len(item.get("linked_ticket_ids") or [])
            linked_counts["linked_document_count"] += len(item.get("linked_document_ids") or [])
        return {
            "total_count": len(items),
            "by_status": by_status,
            "by_nationality": by_nationality,
            "by_citizenship": by_citizenship,
            "agency_count": len(agency_ids),
            "operational_workspace_count": len(operational_workspace_ids),
            "assistance_profile_count": assistance_profile_count,
            "archived_count": by_status.get("archived", 0),
            **linked_counts,
            "metadata_only": True,
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "statuses": PASSENGER_STATUSES,
            "supports_status_filter": True,
            "supports_nationality_filter": True,
            "supports_citizenship_filter": True,
            "supports_assistance_profile_filter": True,
            "supports_travel_date_filter": True,
            "supports_operational_workspace_filter": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def _require_passenger_workspace(self, passenger_workspace_id: str) -> dict[str, Any]:
        passenger_workspace = await self.db.collection(PASSENGER_WORKSPACE_COLLECTION).find_one({"id": passenger_workspace_id})
        if not passenger_workspace:
            passenger_workspace = await self.db.collection(PASSENGER_WORKSPACE_COLLECTION).find_one({"passenger_reference": passenger_workspace_id})
        if not passenger_workspace:
            raise ValueError("Passenger workspace metadata was not found.")
        return passenger_workspace

    async def _platform_projection(self, passenger_workspace: dict[str, Any]) -> dict[str, Any]:
        projected = dict(passenger_workspace)
        projected["display_name"] = self._display_name(projected)
        projected["agency"] = await self._agency_context(projected.get("agency_id"))
        projected["agency_name"] = projected["agency"].get("agency_name")
        projected["operational_workspace"] = await self._operational_workspace_context(projected.get("operational_workspace_id"))
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
        projected["passenger_workspace_metadata_only"] = True
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
            "label": self._first_present(item, label_keys) or fallback_id,
            "status": item.get(status_key),
            "metadata_only": True,
        }

    async def _workspace_matches_travel_date(self, workspace_id: str | None, target: date) -> bool:
        if not workspace_id:
            return False
        workspace = await self.db.collection("operational_travel_workspaces").find_one({"id": workspace_id})
        if not workspace:
            workspace = await self.db.collection("operational_travel_workspaces").find_one({"workspace_reference": workspace_id})
        if not workspace:
            return False
        start = self._parse_optional_date(workspace.get("travel_start_date"))
        end = self._parse_optional_date(workspace.get("travel_end_date")) or start
        if not start:
            return False
        return start <= target <= (end or start)

    def _profile_matches(self, profile: Any, expected: str) -> bool:
        expected_text = expected.lower()
        if isinstance(profile, dict):
            profile_values = [str(value).lower() for value in profile.values()]
            profile_values.extend(str(key).lower() for key in profile.keys())
            return any(expected_text in value for value in profile_values)
        return expected_text in str(profile or "").lower()

    def _display_name(self, item: dict[str, Any]) -> str:
        preferred = item.get("preferred_name")
        parts = [item.get("title"), item.get("first_name"), item.get("middle_name"), item.get("last_name")]
        name = " ".join(str(part).strip() for part in parts if part)
        return preferred or name or item.get("passenger_reference") or item.get("id") or "Passenger"

    def _first_present(self, item: dict[str, Any] | None, keys: list[str]) -> Any:
        if not item:
            return None
        for key in keys:
            if item.get(key):
                return item[key]
        return None

    def _validate_status(self, value: str) -> None:
        if value not in PASSENGER_STATUSES:
            raise ValueError("Unsupported passenger workspace status.")

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

    def _passenger_reference(self) -> str:
        return f"PXW-{new_id()[:8].upper()}"

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _sort_text(self, value: Any) -> str:
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value or "")

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "passenger_workspace_metadata_only": True,
            "booking_execution_disabled": True,
            "ticket_issuance_disabled": True,
            "gds_connectivity_disabled": True,
            "gds_live_connectivity_disabled": True,
            "ndc_connectivity_disabled": True,
            "payment_processing_disabled": True,
            "supplier_integrations_disabled": True,
            "ai_disabled": True,
            "ai_automation_disabled": True,
            "email_disabled": True,
            "email_sending_disabled": True,
            "sms_disabled": True,
            "sms_sending_disabled": True,
            "background_workers_disabled": True,
            "external_api_calls_disabled": True,
            "automatic_profile_matching_disabled": True,
            "automatic_document_validation_disabled": True,
            "document_validation_disabled": True,
            "airline_communication_disabled": True,
            "automation_disabled": True,
        }
