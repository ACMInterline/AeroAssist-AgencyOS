from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from config import get_settings


IMMUTABLE_UPDATE_FIELDS = {"id", "_id", "agency_id", "created_at"}


def sanitize_updates(updates: Dict[str, Any]) -> Dict[str, Any]:
    return {
        key: value
        for key, value in serialize_document(updates).items()
        if key not in IMMUTABLE_UPDATE_FIELDS
    }


def serialize_document(document: Dict[str, Any]) -> Dict[str, Any]:
    clean = deepcopy(document)
    clean.pop("_id", None)
    return clean


def matches_filter(document: Dict[str, Any], filters: Optional[Dict[str, Any]]) -> bool:
    if not filters:
        return True
    return all(document.get(key) == value for key, value in filters.items())


class InMemoryCollection:
    def __init__(self) -> None:
        self.documents: Dict[str, Dict[str, Any]] = {}

    async def find_many(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        return [
            serialize_document(document)
            for document in self.documents.values()
            if matches_filter(document, filters)
        ]

    async def find_one(self, filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for document in self.documents.values():
            if matches_filter(document, filters):
                return serialize_document(document)
        return None

    async def insert_one(self, document: Dict[str, Any]) -> Dict[str, Any]:
        clean = serialize_document(document)
        self.documents[clean["id"]] = clean
        return serialize_document(clean)

    async def update_one(self, filters: Dict[str, Any], updates: Dict[str, Any], allow_agency_update: bool = False) -> Optional[Dict[str, Any]]:
        updates = serialize_document(updates) if allow_agency_update else sanitize_updates(updates)
        if allow_agency_update:
            updates = {key: value for key, value in updates.items() if key not in {"id", "_id", "created_at"}}
        for document_id, document in self.documents.items():
            if matches_filter(document, filters):
                updated = serialize_document(document)
                updated.update(updates)
                updated["updated_at"] = datetime.now(timezone.utc)
                self.documents[document_id] = updated
                return serialize_document(updated)
        return None

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        return len(await self.find_many(filters))


class MongoCollection:
    def __init__(self, collection: Any) -> None:
        self.collection = collection

    async def find_many(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        cursor = self.collection.find(filters or {})
        return [serialize_document(document) async for document in cursor]

    async def find_one(self, filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        document = await self.collection.find_one(filters)
        return serialize_document(document) if document else None

    async def insert_one(self, document: Dict[str, Any]) -> Dict[str, Any]:
        clean = serialize_document(document)
        await self.collection.insert_one(clean)
        return serialize_document(clean)

    async def update_one(self, filters: Dict[str, Any], updates: Dict[str, Any], allow_agency_update: bool = False) -> Optional[Dict[str, Any]]:
        from pymongo import ReturnDocument

        updates = serialize_document(updates) if allow_agency_update else sanitize_updates(updates)
        if allow_agency_update:
            updates = {key: value for key, value in updates.items() if key not in {"id", "_id", "created_at"}}
        updates["updated_at"] = datetime.now(timezone.utc)
        result = await self.collection.find_one_and_update(
            filters,
            {"$set": updates},
            return_document=ReturnDocument.AFTER,
        )
        return serialize_document(result) if result else None

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        return await self.collection.count_documents(filters or {})


class Database:
    def __init__(self) -> None:
        settings = get_settings()
        self.mode = settings.db_mode
        self.mongodb_url = settings.mongodb_url
        self.mongodb_database = settings.mongodb_database
        self._memory_collections: Dict[str, InMemoryCollection] = {}
        self._mongo_database: Optional[Any] = None
        self._mongo_client: Optional[Any] = None

    async def connect(self) -> None:
        if self.mode != "mongo":
            return

        from motor.motor_asyncio import AsyncIOMotorClient

        client = AsyncIOMotorClient(self.mongodb_url)
        self._mongo_client = client
        self._mongo_database = client[self.mongodb_database]
        await ensure_mongo_indexes(self._mongo_database)

    async def readiness(self) -> Dict[str, Any]:
        if self.mode != "mongo":
            return {"ok": True, "mode": self.mode, "diagnostic": "In-memory database is available."}
        if self._mongo_client is None or self._mongo_database is None:
            return {"ok": False, "mode": self.mode, "diagnostic": "MongoDB is not connected."}
        try:
            await self._mongo_client.admin.command("ping")
        except Exception as exc:
            return {"ok": False, "mode": self.mode, "diagnostic": f"MongoDB ping failed: {exc.__class__.__name__}"}
        return {"ok": True, "mode": self.mode, "database": self.mongodb_database, "diagnostic": "MongoDB ping succeeded."}

    def collection(self, name: str) -> InMemoryCollection | MongoCollection:
        if self.mode == "mongo":
            if self._mongo_database is None:
                raise RuntimeError("MongoDB mode is enabled but database is not connected.")
            return MongoCollection(self._mongo_database[name])

        if name not in self._memory_collections:
            self._memory_collections[name] = InMemoryCollection()
        return self._memory_collections[name]


database = Database()


async def get_database() -> Database:
    return database


AGENCY_OWNED_COLLECTIONS = [
    "agency_staff_memberships",
    "agency_workspaces",
    "agency_branding_settings",
    "agency_branding_assets",
    "client_profiles",
    "request_intakes",
    "portal_access_mappings",
    "passenger_profiles",
    "client_passenger_relationships",
    "travel_requests",
    "request_passengers",
    "request_segments",
    "requested_services",
    "request_messages",
    "request_tasks",
    "request_timeline_events",
    "offers",
    "offer_passengers",
    "offer_route_alternatives",
    "offer_segments",
    "offer_fare_options",
    "offer_price_lines",
    "offer_service_checks",
    "offer_timeline_events",
    "bookings",
    "booking_passengers",
    "booking_segments",
    "ticket_records",
    "emd_records",
    "invoices",
    "invoice_line_items",
    "payment_records",
    "booking_timeline_events",
    "refund_exchange_cases",
    "refund_exchange_items",
    "refund_exchange_financial_lines",
    "refund_exchange_messages",
    "refund_exchange_timeline_events",
    "agency_airline_overrides",
    "document_templates",
    "rendered_documents",
    "document_exports",
    "document_deliveries",
    "document_delivery_attempts",
    "document_storage_records",
    "agency_email_settings",
    "document_timeline_events",
    "portal_action_events",
    "document_acknowledgements",
    "audit_events",
]


async def ensure_mongo_indexes(mongo_database: Any) -> None:
    from pymongo import ASCENDING

    for collection_name in AGENCY_OWNED_COLLECTIONS:
        collection = mongo_database[collection_name]
        await collection.create_index([("id", ASCENDING)], unique=True)
        await collection.create_index([("agency_id", ASCENDING)])

    unique_indexes = {
        "platform_users": [[("email", ASCENDING)]],
        "agencies": [[("slug", ASCENDING)], [("id", ASCENDING)]],
        "global_reference_records": [[("domain", ASCENDING), ("key", ASCENDING)], [("id", ASCENDING)]],
        "airline_profiles": [[("airline_code", ASCENDING)], [("id", ASCENDING)]],
        "agency_staff_memberships": [[("agency_id", ASCENDING), ("user_id", ASCENDING)]],
        "portal_access_mappings": [[("agency_id", ASCENDING), ("user_email", ASCENDING)]],
        "auth_identities": [[("normalized_email", ASCENDING)], [("id", ASCENDING)]],
        "auth_sessions": [[("token_hash", ASCENDING)], [("id", ASCENDING)]],
        "invitations": [[("token_hash", ASCENDING)], [("id", ASCENDING)]],
    }
    for collection_name, index_specs in unique_indexes.items():
        for spec in index_specs:
            await mongo_database[collection_name].create_index(spec, unique=True)

    compound_indexes = {
        "client_profiles": [[("agency_id", ASCENDING), ("primary_email", ASCENDING)]],
        "invitations": [
            [("agency_id", ASCENDING), ("workspace_id", ASCENDING), ("normalized_email", ASCENDING), ("target_role", ASCENDING), ("status", ASCENDING)],
            [("agency_id", ASCENDING), ("status", ASCENDING)],
        ],
        "passenger_profiles": [[("agency_id", ASCENDING), ("display_name", ASCENDING)]],
        "client_passenger_relationships": [
            [("agency_id", ASCENDING), ("client_id", ASCENDING)],
            [("agency_id", ASCENDING), ("passenger_id", ASCENDING)],
            [("agency_id", ASCENDING), ("client_id", ASCENDING), ("passenger_id", ASCENDING)],
        ],
        "travel_requests": [[("agency_id", ASCENDING), ("client_id", ASCENDING)]],
        "offers": [[("agency_id", ASCENDING), ("client_id", ASCENDING)], [("agency_id", ASCENDING), ("request_id", ASCENDING)]],
        "bookings": [[("agency_id", ASCENDING), ("client_id", ASCENDING)], [("agency_id", ASCENDING), ("offer_id", ASCENDING)]],
        "invoices": [[("agency_id", ASCENDING), ("client_id", ASCENDING)], [("agency_id", ASCENDING), ("booking_id", ASCENDING)]],
        "payment_records": [[("agency_id", ASCENDING), ("invoice_id", ASCENDING)], [("agency_id", ASCENDING), ("client_id", ASCENDING)]],
        "refund_exchange_cases": [
            [("agency_id", ASCENDING), ("client_id", ASCENDING)],
            [("agency_id", ASCENDING), ("status", ASCENDING)],
            [("agency_id", ASCENDING), ("case_type", ASCENDING)],
            [("agency_id", ASCENDING), ("updated_at", ASCENDING)],
        ],
        "refund_exchange_items": [[("agency_id", ASCENDING), ("case_id", ASCENDING)], [("agency_id", ASCENDING), ("item_type", ASCENDING)]],
        "refund_exchange_financial_lines": [[("agency_id", ASCENDING), ("case_id", ASCENDING)], [("agency_id", ASCENDING), ("line_type", ASCENDING)]],
        "refund_exchange_messages": [[("agency_id", ASCENDING), ("case_id", ASCENDING)], [("agency_id", ASCENDING), ("visibility", ASCENDING)]],
        "refund_exchange_timeline_events": [[("agency_id", ASCENDING), ("case_id", ASCENDING)], [("agency_id", ASCENDING), ("event_type", ASCENDING)]],
        "rendered_documents": [
            [("agency_id", ASCENDING), ("client_id", ASCENDING)],
            [("agency_id", ASCENDING), ("source_entity_type", ASCENDING), ("source_entity_id", ASCENDING)],
        ],
        "document_exports": [
            [("agency_id", ASCENDING), ("rendered_document_id", ASCENDING)],
            [("agency_id", ASCENDING), ("client_visible", ASCENDING)],
            [("agency_id", ASCENDING), ("retention_expires_at", ASCENDING)],
        ],
        "document_deliveries": [
            [("agency_id", ASCENDING), ("rendered_document_id", ASCENDING)],
            [("agency_id", ASCENDING), ("status", ASCENDING)],
            [("agency_id", ASCENDING), ("retry_status", ASCENDING)],
        ],
        "document_delivery_attempts": [
            [("agency_id", ASCENDING), ("delivery_id", ASCENDING)],
            [("agency_id", ASCENDING), ("rendered_document_id", ASCENDING)],
        ],
        "document_storage_records": [
            [("agency_id", ASCENDING), ("related_entity_type", ASCENDING), ("related_entity_id", ASCENDING)],
            [("agency_id", ASCENDING), ("storage_status", ASCENDING)],
            [("agency_id", ASCENDING), ("document_type", ASCENDING)],
            [("agency_id", ASCENDING), ("storage_backend", ASCENDING)],
        ],
        "agency_email_settings": [[("agency_id", ASCENDING), ("status", ASCENDING)]],
        "portal_action_events": [[("agency_id", ASCENDING), ("client_id", ASCENDING)], [("agency_id", ASCENDING), ("status", ASCENDING)]],
        "document_acknowledgements": [[("agency_id", ASCENDING), ("rendered_document_id", ASCENDING), ("client_id", ASCENDING)]],
        "audit_events": [[("agency_id", ASCENDING), ("entity_type", ASCENDING), ("entity_id", ASCENDING)]],
        "airline_knowledge_items": [[("airline_id", ASCENDING)], [("review_status", ASCENDING)]],
        "airline_procedures": [[("airline_id", ASCENDING)]],
        "airline_emd_rule_notes": [[("airline_id", ASCENDING)]],
        "airline_knowledge_sources": [[("airline_id", ASCENDING)]],
        "agency_airline_overrides": [[("agency_id", ASCENDING), ("airline_id", ASCENDING)]],
    }
    for collection_name, index_specs in compound_indexes.items():
        for spec in index_specs:
            await mongo_database[collection_name].create_index(spec)
