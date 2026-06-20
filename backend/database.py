import os
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


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

    async def update_one(self, filters: Dict[str, Any], updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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

    async def update_one(self, filters: Dict[str, Any], updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        updates = serialize_document(updates)
        updates["updated_at"] = datetime.now(timezone.utc)
        result = await self.collection.find_one_and_update(
            filters,
            {"$set": updates},
            return_document=True,
        )
        return serialize_document(result) if result else None

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        return await self.collection.count_documents(filters or {})


class Database:
    def __init__(self) -> None:
        self.mode = os.getenv("AEROASSIST_DB_MODE", "memory")
        self._memory_collections: Dict[str, InMemoryCollection] = {}
        self._mongo_database: Optional[Any] = None

    async def connect(self) -> None:
        if self.mode != "mongo":
            return

        from motor.motor_asyncio import AsyncIOMotorClient

        mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        database_name = os.getenv("MONGODB_DATABASE", "aeroassist_agencyos")
        client = AsyncIOMotorClient(mongo_url)
        self._mongo_database = client[database_name]

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
