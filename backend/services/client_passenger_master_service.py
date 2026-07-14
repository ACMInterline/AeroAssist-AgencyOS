from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import (
    ClientMasterRecord,
    ClientMasterRecordCreate,
    ClientMasterRecordUpdate,
    ClientPassengerMasterLink,
    ClientPassengerMasterLinkCreate,
    ClientPortalAccessProfile,
    ClientPortalAccessProfileCreate,
    PassengerKnownDocument,
    PassengerKnownDocumentCreate,
    PassengerMasterRecord,
    PassengerMasterRecordCreate,
    PassengerMasterRecordUpdate,
    PassengerOperationalPreference,
    PassengerOperationalPreferenceCreate,
    PassengerServiceHistoryCreate,
    PassengerServiceHistoryRecord,
)


PHASE_LABEL = "phase_54_9_end_to_end_operational_workflow_maturity_foundation"

CLIENT_MASTER_RECORDS_COLLECTION = "client_master_records"
PASSENGER_MASTER_RECORDS_COLLECTION = "passenger_master_records"
CLIENT_PASSENGER_LINKS_COLLECTION = "client_passenger_links"
PASSENGER_SERVICE_HISTORY_COLLECTION = "passenger_service_history"
PASSENGER_OPERATIONAL_PREFERENCES_COLLECTION = "passenger_operational_preferences"
PASSENGER_KNOWN_DOCUMENTS_COLLECTION = "passenger_known_documents"
CLIENT_PORTAL_ACCESS_PROFILES_COLLECTION = "client_portal_access_profiles"

MASTER_COLLECTIONS = [
    CLIENT_MASTER_RECORDS_COLLECTION,
    PASSENGER_MASTER_RECORDS_COLLECTION,
    CLIENT_PASSENGER_LINKS_COLLECTION,
    PASSENGER_SERVICE_HISTORY_COLLECTION,
    PASSENGER_OPERATIONAL_PREFERENCES_COLLECTION,
    PASSENGER_KNOWN_DOCUMENTS_COLLECTION,
    CLIENT_PORTAL_ACCESS_PROFILES_COLLECTION,
]

CLIENT_MASTER_STATUSES = ["active", "in_review", "needs_review", "merged", "archived"]
PASSENGER_MASTER_STATUSES = ["active", "in_review", "needs_review", "merged", "archived"]
CLIENT_PASSENGER_LINK_STATUSES = ["active", "inactive", "archived"]
PASSENGER_HISTORY_STATUSES = ["active", "superseded", "archived"]
PASSENGER_PREFERENCE_STATUSES = ["active", "needs_review", "archived"]
PASSENGER_DOCUMENT_STATUSES = ["active", "needs_review", "expired", "archived"]
CLIENT_PORTAL_ACCESS_STATUSES = ["no_portal_access", "invited", "active", "suspended", "archived"]

CLIENT_LINK_FIELDS = [
    "linked_passenger_ids",
    "request_ids",
    "trip_ids",
    "offer_ids",
    "invoice_ids",
    "communication_ids",
    "document_ids",
]
PASSENGER_HISTORY_LINK_FIELDS = [
    "service_history_ids",
    "document_ids",
    "trip_ids",
    "booking_ids",
    "ticket_ids",
    "emd_ids",
    "operational_evaluation_ids",
    "feasibility_ids",
    "recommendation_ids",
]


class ClientPassengerMasterError(ValueError):
    pass


class ClientPassengerMasterService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def platform_clients_response(self, **filters: Any) -> dict[str, Any]:
        clients = await self.list_client_records(**filters)
        return {
            "phase": PHASE_LABEL,
            "items": clients,
            "clients": clients,
            "summary": await self.summarize_counts(filters.get("agency_id")),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Client Master stores commercial-owner metadata only. It does not add CRM sales pipelines, marketing automation, provider integrations, booking, ticketing, payments, AI/LLM logic, or workers.",
            **self.safety_flags(),
        }

    async def agency_clients_response(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        clients = await self.list_client_records(agency_id=agency_id, **filters)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": clients,
            "clients": clients,
            "summary": await self.summarize_counts(agency_id),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def platform_passengers_response(self, **filters: Any) -> dict[str, Any]:
        passengers = await self.list_passenger_records(**filters)
        return {
            "phase": PHASE_LABEL,
            "items": passengers,
            "passengers": passengers,
            "summary": await self.summarize_counts(filters.get("agency_id")),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Passenger Master stores reusable operational identity and history metadata only. Human authority remains final.",
            **self.safety_flags(),
        }

    async def agency_passengers_response(self, agency_id: str, **filters: Any) -> dict[str, Any]:
        passengers = await self.list_passenger_records(agency_id=agency_id, **filters)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": passengers,
            "passengers": passengers,
            "summary": await self.summarize_counts(agency_id),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def platform_summary(self, agency_id: str | None = None) -> dict[str, Any]:
        return {
            "phase": PHASE_LABEL,
            "summary": await self.summarize_counts(agency_id),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": await self.summarize_counts(agency_id),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def list_client_records(
        self,
        *,
        agency_id: str | None = None,
        search: str | None = None,
        status: str | None = None,
        portal_status: str | None = None,
        passenger: str | None = None,
        include_archived: bool = False,
        **_: Any,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if status:
            filters["client_status"] = status
        if portal_status:
            filters["portal_status"] = portal_status

        items = await self.db.collection(CLIENT_MASTER_RECORDS_COLLECTION).find_many(filters or None)
        if not include_archived:
            items = [item for item in items if not item.get("archived") and item.get("client_status") != "archived"]
        items = [
            item
            for item in items
            if self._any_field_matches(item, ["client_master_reference", "profile", "contacts", "client_overview"], search)
            and self._any_field_matches(item, ["linked_passenger_ids", "relationship_graph"], passenger)
        ]
        items.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._client_projection(item) for item in items]

    async def list_passenger_records(
        self,
        *,
        agency_id: str | None = None,
        search: str | None = None,
        status: str | None = None,
        service: str | None = None,
        include_archived: bool = False,
        **_: Any,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if status:
            filters["passenger_status"] = status

        items = await self.db.collection(PASSENGER_MASTER_RECORDS_COLLECTION).find_many(filters or None)
        if not include_archived:
            items = [item for item in items if not item.get("archived") and item.get("passenger_status") != "archived"]
        items = [
            item
            for item in items
            if self._any_field_matches(item, ["passenger_master_reference", "operational_profile", "passenger_overview"], search)
            and self._passenger_service_matches(item, service)
        ]
        items.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._passenger_projection(item) for item in items]

    async def get_client_record(self, record_id: str, agency_id: str | None = None) -> dict[str, Any]:
        item = await self._require_record(CLIENT_MASTER_RECORDS_COLLECTION, record_id, agency_id=agency_id)
        return await self._client_projection(item)

    async def get_passenger_record(self, record_id: str, agency_id: str | None = None) -> dict[str, Any]:
        item = await self._require_record(PASSENGER_MASTER_RECORDS_COLLECTION, record_id, agency_id=agency_id)
        return await self._passenger_projection(item)

    async def create_client_record(
        self,
        payload: ClientMasterRecordCreate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        if agency_id:
            data["agency_id"] = agency_id
        data.setdefault("client_master_reference", self._reference("CLM"))
        data.setdefault("client_status", "active")
        data.setdefault("created_by", user.get("id"))
        self._validate_client_payload(data)
        data.update(self.safety_flags())
        record = ClientMasterRecord(**data)
        created = await self.db.collection(CLIENT_MASTER_RECORDS_COLLECTION).insert_one(record.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "client_master_record": await self._client_projection(created),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def update_client_record(
        self,
        record_id: str,
        payload: ClientMasterRecordUpdate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_record(CLIENT_MASTER_RECORDS_COLLECTION, record_id, agency_id=agency_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        if agency_id:
            updates.pop("agency_id", None)
        self._validate_client_payload(updates, partial=True)
        updates.update(self.safety_flags())
        updated = await self._update_record(CLIENT_MASTER_RECORDS_COLLECTION, existing["id"], updates, agency_id=agency_id)
        return {
            "phase": PHASE_LABEL,
            "client_master_record": await self._client_projection(updated),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def archive_client_record(self, record_id: str, user: dict, agency_id: str | None = None) -> dict[str, Any]:
        existing = await self._require_record(CLIENT_MASTER_RECORDS_COLLECTION, record_id, agency_id=agency_id)
        updated = await self._update_record(
            CLIENT_MASTER_RECORDS_COLLECTION,
            existing["id"],
            {"client_status": "archived", "archived": True, "archived_at": self._now(), **self.safety_flags()},
            agency_id=agency_id,
        )
        return {
            "phase": PHASE_LABEL,
            "client_master_record": await self._client_projection(updated),
            "archived": True,
            "physical_delete_disabled": True,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def create_passenger_record(
        self,
        payload: PassengerMasterRecordCreate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        if agency_id:
            data["agency_id"] = agency_id
        data.setdefault("passenger_master_reference", self._reference("PXM"))
        data.setdefault("passenger_status", "active")
        data.setdefault("created_by", user.get("id"))
        self._validate_passenger_payload(data)
        data.update(self.safety_flags())
        record = PassengerMasterRecord(**data)
        created = await self.db.collection(PASSENGER_MASTER_RECORDS_COLLECTION).insert_one(record.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "passenger_master_record": await self._passenger_projection(created),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def update_passenger_record(
        self,
        record_id: str,
        payload: PassengerMasterRecordUpdate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_record(PASSENGER_MASTER_RECORDS_COLLECTION, record_id, agency_id=agency_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        if agency_id:
            updates.pop("agency_id", None)
        self._validate_passenger_payload(updates, partial=True)
        updates.update(self.safety_flags())
        updated = await self._update_record(PASSENGER_MASTER_RECORDS_COLLECTION, existing["id"], updates, agency_id=agency_id)
        return {
            "phase": PHASE_LABEL,
            "passenger_master_record": await self._passenger_projection(updated),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def archive_passenger_record(self, record_id: str, user: dict, agency_id: str | None = None) -> dict[str, Any]:
        existing = await self._require_record(PASSENGER_MASTER_RECORDS_COLLECTION, record_id, agency_id=agency_id)
        updated = await self._update_record(
            PASSENGER_MASTER_RECORDS_COLLECTION,
            existing["id"],
            {"passenger_status": "archived", "archived": True, "archived_at": self._now(), **self.safety_flags()},
            agency_id=agency_id,
        )
        return {
            "phase": PHASE_LABEL,
            "passenger_master_record": await self._passenger_projection(updated),
            "archived": True,
            "physical_delete_disabled": True,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def create_link(
        self,
        payload: ClientPassengerMasterLinkCreate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        if agency_id:
            data["agency_id"] = agency_id
        data.setdefault("link_reference", self._reference("CPL"))
        data.setdefault("link_status", "active")
        self._validate_choice(data, "link_status", CLIENT_PASSENGER_LINK_STATUSES)
        data.update(self.safety_flags())
        record = ClientPassengerMasterLink(**data)
        created = await self.db.collection(CLIENT_PASSENGER_LINKS_COLLECTION).insert_one(record.model_dump(mode="json"))
        return self._child_response("client_passenger_link", created)

    async def create_service_history(
        self,
        payload: PassengerServiceHistoryCreate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        if agency_id:
            data["agency_id"] = agency_id
        data.setdefault("history_reference", self._reference("PSH"))
        data.setdefault("history_status", "active")
        self._validate_choice(data, "history_status", PASSENGER_HISTORY_STATUSES)
        data.update(self._history_flags())
        record = PassengerServiceHistoryRecord(**data)
        created = await self.db.collection(PASSENGER_SERVICE_HISTORY_COLLECTION).insert_one(record.model_dump(mode="json"))
        return self._child_response("passenger_service_history", created)

    async def create_operational_preference(
        self,
        payload: PassengerOperationalPreferenceCreate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        if agency_id:
            data["agency_id"] = agency_id
        data.setdefault("preference_reference", self._reference("POP"))
        data.setdefault("preference_status", "active")
        self._validate_choice(data, "preference_status", PASSENGER_PREFERENCE_STATUSES)
        data.update(self._history_flags())
        record = PassengerOperationalPreference(**data)
        created = await self.db.collection(PASSENGER_OPERATIONAL_PREFERENCES_COLLECTION).insert_one(record.model_dump(mode="json"))
        return self._child_response("passenger_operational_preference", created)

    async def create_known_document(
        self,
        payload: PassengerKnownDocumentCreate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        if agency_id:
            data["agency_id"] = agency_id
        data.setdefault("document_reference", self._reference("PKD"))
        data.setdefault("document_status", "active")
        self._validate_choice(data, "document_status", PASSENGER_DOCUMENT_STATUSES)
        data.update(self._history_flags())
        record = PassengerKnownDocument(**data)
        created = await self.db.collection(PASSENGER_KNOWN_DOCUMENTS_COLLECTION).insert_one(record.model_dump(mode="json"))
        return self._child_response("passenger_known_document", created)

    async def create_portal_access_profile(
        self,
        payload: ClientPortalAccessProfileCreate,
        user: dict,
        agency_id: str | None = None,
    ) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        if agency_id:
            data["agency_id"] = agency_id
        data.setdefault("portal_access_reference", self._reference("CPA"))
        data.setdefault("portal_status", "no_portal_access")
        self._validate_choice(data, "portal_status", CLIENT_PORTAL_ACCESS_STATUSES)
        data.update(self._portal_flags())
        record = ClientPortalAccessProfile(**data)
        created = await self.db.collection(CLIENT_PORTAL_ACCESS_PROFILES_COLLECTION).insert_one(record.model_dump(mode="json"))
        return self._child_response("client_portal_access_profile", created)

    async def summarize_counts(self, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"agency_id": agency_id} if agency_id else None
        clients = await self.db.collection(CLIENT_MASTER_RECORDS_COLLECTION).find_many(filters)
        passengers = await self.db.collection(PASSENGER_MASTER_RECORDS_COLLECTION).find_many(filters)
        links = await self.db.collection(CLIENT_PASSENGER_LINKS_COLLECTION).find_many(filters)
        history = await self.db.collection(PASSENGER_SERVICE_HISTORY_COLLECTION).find_many(filters)
        preferences = await self.db.collection(PASSENGER_OPERATIONAL_PREFERENCES_COLLECTION).find_many(filters)
        documents = await self.db.collection(PASSENGER_KNOWN_DOCUMENTS_COLLECTION).find_many(filters)
        portal_profiles = await self.db.collection(CLIENT_PORTAL_ACCESS_PROFILES_COLLECTION).find_many(filters)
        return {
            "client_master_record_count": len(clients),
            "passenger_master_record_count": len(passengers),
            "client_passenger_link_count": len(links),
            "passenger_service_history_count": len(history),
            "passenger_operational_preference_count": len(preferences),
            "passenger_known_document_count": len(documents),
            "client_portal_access_profile_count": len(portal_profiles),
            "by_client_status": self._counts(clients, "client_status", CLIENT_MASTER_STATUSES),
            "by_passenger_status": self._counts(passengers, "passenger_status", PASSENGER_MASTER_STATUSES),
            "by_portal_status": self._counts(portal_profiles + clients, "portal_status", CLIENT_PORTAL_ACCESS_STATUSES),
            "relationship_link_count": len(links),
            "reusable_history_reference_count": sum(len(item.get(field) or []) for item in passengers for field in PASSENGER_HISTORY_LINK_FIELDS) + len(history),
            "known_document_reference_count": sum(len(item.get("document_ids") or []) for item in passengers) + len(documents),
            "preferred_airline_count": sum(len(item.get("preferred_airlines") or []) for item in passengers + preferences),
            "preferred_cabin_count": sum(len(item.get("preferred_cabins") or []) for item in passengers + preferences),
            "preferred_seat_count": sum(len(item.get("preferred_seats") or []) for item in passengers + preferences),
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "search": "reference, overview, profile, contacts, or operational profile metadata match",
            "status": "client_status or passenger_status exact metadata match",
            "portal_status": CLIENT_PORTAL_ACCESS_STATUSES,
            "passenger": "linked passenger id or relationship graph metadata match",
            "service": "passenger service history, service family, service code, or SSR code metadata match",
            "metadata_only": True,
        }

    async def _client_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        projected["client_display_name"] = self._display_name(projected, "client_master_reference", "profile")
        projected["client_overview_section"] = {
            "client_master_reference": projected.get("client_master_reference"),
            "client_status": projected.get("client_status"),
            "commercial_owner_type": projected.get("commercial_owner_type"),
            "profile": projected.get("profile") or {},
            "client_overview": projected.get("client_overview") or {},
        }
        projected["passenger_overview_section"] = {
            "linked_passenger_ids": projected.get("linked_passenger_ids") or [],
            "linked_passenger_count": len(projected.get("linked_passenger_ids") or []),
        }
        projected["service_history_section"] = {
            "reusable_passenger_history": True,
            "linked_passenger_ids": projected.get("linked_passenger_ids") or [],
        }
        projected["known_operational_profile_section"] = {
            "client_is_commercial_owner": True,
            "operational_identity_is_passenger": True,
        }
        projected["known_preferences_section"] = {"permissions": projected.get("permissions") or {}}
        projected["portal_access_section"] = {
            "portal_status": projected.get("portal_status"),
            "permissions": projected.get("permissions") or {},
        }
        projected["relationship_graph_section"] = {
            "relationship_graph": projected.get("relationship_graph") or [],
            "many_to_many_relationships_supported": True,
        }
        projected["link_summary"] = {field: len(projected.get(field) or []) for field in CLIENT_LINK_FIELDS}
        projected.update(self.safety_flags())
        return projected

    async def _passenger_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        projected["passenger_display_name"] = self._display_name(projected, "passenger_master_reference", "operational_profile")
        projected["client_overview_section"] = {
            "commercial_owners": projected.get("relationship_graph") or [],
            "client_is_commercial_owner": True,
        }
        projected["passenger_overview_section"] = {
            "passenger_master_reference": projected.get("passenger_master_reference"),
            "passenger_status": projected.get("passenger_status"),
            "operational_profile": projected.get("operational_profile") or {},
            "passenger_overview": projected.get("passenger_overview") or {},
        }
        projected["service_history_section"] = {
            "service_history_ids": projected.get("service_history_ids") or [],
            "trip_ids": projected.get("trip_ids") or [],
            "booking_ids": projected.get("booking_ids") or [],
            "ticket_ids": projected.get("ticket_ids") or [],
            "emd_ids": projected.get("emd_ids") or [],
            "operational_evaluation_ids": projected.get("operational_evaluation_ids") or [],
            "feasibility_ids": projected.get("feasibility_ids") or [],
            "recommendation_ids": projected.get("recommendation_ids") or [],
            "passenger_history_reusable": True,
        }
        projected["known_operational_profile_section"] = {
            "operational_profile": projected.get("operational_profile") or {},
            "mobility_profile": projected.get("mobility_profile") or {},
            "medical_profile": projected.get("medical_profile") or {},
            "pets": projected.get("pets") or [],
            "special_items": projected.get("special_items") or [],
            "document_ids": projected.get("document_ids") or [],
        }
        projected["known_preferences_section"] = {
            "preferred_airlines": projected.get("preferred_airlines") or [],
            "preferred_cabins": projected.get("preferred_cabins") or [],
            "preferred_seats": projected.get("preferred_seats") or [],
        }
        projected["portal_access_section"] = {"passenger_portal_visibility_is_client_controlled": True}
        projected["relationship_graph_section"] = {
            "relationship_graph": projected.get("relationship_graph") or [],
            "many_to_many_relationships_supported": True,
        }
        projected["history_link_summary"] = {field: len(projected.get(field) or []) for field in PASSENGER_HISTORY_LINK_FIELDS}
        projected.update(self.safety_flags())
        return projected

    async def _require_record(self, collection: str, record_id: str, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": record_id}
        if agency_id:
            filters["agency_id"] = agency_id
        item = await self.db.collection(collection).find_one(filters)
        if not item:
            raise ClientPassengerMasterError("Client/passenger master metadata not found.")
        return item

    async def _update_record(self, collection: str, record_id: str, updates: dict[str, Any], agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": record_id}
        if agency_id:
            filters["agency_id"] = agency_id
        updated = await self.db.collection(collection).update_one(filters, updates)
        if not updated:
            raise ClientPassengerMasterError("Client/passenger master metadata could not be updated.")
        return updated

    def _child_response(self, key: str, created: dict[str, Any]) -> dict[str, Any]:
        return {
            "phase": PHASE_LABEL,
            key: created,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    def _validate_client_payload(self, data: dict[str, Any], *, partial: bool = False) -> None:
        self._validate_choice(data, "client_status", CLIENT_MASTER_STATUSES)
        self._validate_choice(data, "portal_status", CLIENT_PORTAL_ACCESS_STATUSES)
        self._reject_forbidden_metadata(data)

    def _validate_passenger_payload(self, data: dict[str, Any], *, partial: bool = False) -> None:
        self._validate_choice(data, "passenger_status", PASSENGER_MASTER_STATUSES)
        self._reject_forbidden_metadata(data)

    def _validate_choice(self, data: dict[str, Any], field: str, allowed: list[str]) -> None:
        if field not in data or data.get(field) is None:
            return
        if data[field] not in allowed:
            raise ClientPassengerMasterError(f"Unsupported {field} metadata value: {data[field]}.")

    def _reject_forbidden_metadata(self, data: dict[str, Any]) -> None:
        forbidden = ["sales_pipeline_stage", "marketing_campaign", "provider_payload", "llm_prompt", "ai_prompt", "payment_processor"]
        serialized = str(data).lower()
        for marker in forbidden:
            if marker in serialized:
                raise ClientPassengerMasterError(f"Forbidden non-metadata implementation marker present: {marker}.")

    def _passenger_service_matches(self, item: dict[str, Any], expected: str | None) -> bool:
        if expected in (None, ""):
            return True
        return self._any_field_matches(
            item,
            ["service_history_ids", "operational_profile", "mobility_profile", "medical_profile", "pets", "special_items", "passenger_overview"],
            expected,
        )

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "client_passenger_master_foundation": True,
            "client_is_commercial_owner": True,
            "passenger_is_operational_identity": True,
            "many_to_many_relationships_supported": True,
            "passenger_history_reusable": True,
            "crm_sales_pipeline_disabled": True,
            "marketing_automation_disabled": True,
            "provider_integrations_disabled": True,
            "ai_llm_disabled": True,
            "booking_disabled": True,
            "ticketing_disabled": True,
            "payment_gateway_disabled": True,
            "background_workers_disabled": True,
            "human_authority_final": True,
        }

    def _history_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "client_passenger_master_foundation": True,
            "passenger_is_operational_identity": True,
            "passenger_history_reusable": True,
            "human_authority_final": True,
        }

    def _portal_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "client_passenger_master_foundation": True,
            "client_is_commercial_owner": True,
            "automatic_client_sending_disabled": True,
            "human_authority_final": True,
        }

    def _reference(self, prefix: str) -> str:
        return f"{prefix}-{self._now().replace(':', '').replace('-', '').replace('.', '')}"

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _sort_text(self, value: Any) -> str:
        return str(value or "")

    def _counts(self, items: list[dict[str, Any]], field: str, values: list[str]) -> dict[str, int]:
        return {value: len([item for item in items if item.get(field) == value]) for value in values}

    def _display_name(self, item: dict[str, Any], reference_field: str, profile_field: str) -> str:
        profile = item.get(profile_field) or {}
        if isinstance(profile, dict):
            for key in ["display_name", "name", "legal_name", "full_name"]:
                if profile.get(key):
                    return str(profile[key])
        return str(item.get(reference_field) or item.get("id") or "Master record")

    def _any_field_matches(self, item: dict[str, Any], fields: list[str], expected: Any) -> bool:
        if expected in (None, ""):
            return True
        expected_text = str(expected).lower()
        for field in fields:
            value = item.get(field)
            if isinstance(value, list):
                if any(expected_text in str(entry).lower() for entry in value):
                    return True
            elif isinstance(value, dict):
                if expected_text in str(value).lower():
                    return True
            elif value is not None and expected_text in str(value).lower():
                return True
        return False
