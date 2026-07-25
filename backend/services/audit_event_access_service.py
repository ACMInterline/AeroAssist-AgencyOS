from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from database import Database
from observability import REDACTED, redact_sensitive
from persistence_query import PaginationRequest
from persistence_repository import PersistenceRepository


AUDIT_EVENTS_COLLECTION = "audit_events"
PLATFORM_AUDIT_READ_ROLES = ("platform_owner", "platform_admin")
AGENCY_AUDIT_READ_ROLES = ("agency_owner", "agency_admin")

_RESTRICTED_METADATA_FRAGMENTS = (
    "attachment",
    "authorization",
    "card",
    "content",
    "cookie",
    "credential",
    "document",
    "file",
    "internal_note",
    "medical",
    "passport",
    "password",
    "payment",
    "private",
    "provider",
    "raw_payload",
    "secret",
    "token",
)
_MAX_METADATA_DEPTH = 5
_MAX_METADATA_ITEMS = 50


class AuditEventAccessService:
    def __init__(self, db: Database) -> None:
        self.repository = PersistenceRepository(db)

    async def list_platform_events(
        self,
        *,
        agency_id: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        event_type: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        page = await self.repository.find_platform_records(
            collection_name=AUDIT_EVENTS_COLLECTION,
            agency_id=agency_id,
            filters=_filters(entity_type=entity_type, entity_id=entity_id, event_type=event_type),
            sort_field="created_at",
            sort_direction="desc",
            pagination=PaginationRequest.build(limit=limit, cursor=cursor),
        )
        return {
            "items": [safe_audit_event(item) for item in page.items],
            "pagination": page.pagination.as_dict(),
            "scope": "platform",
            "read_only": True,
        }

    async def list_agency_events(
        self,
        agency_id: str,
        *,
        entity_type: str | None = None,
        entity_id: str | None = None,
        event_type: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        page = await self.repository.find_agency_records(
            collection_name=AUDIT_EVENTS_COLLECTION,
            agency_id=agency_id,
            filters=_filters(entity_type=entity_type, entity_id=entity_id, event_type=event_type),
            sort_field="created_at",
            sort_direction="desc",
            pagination=PaginationRequest.build(limit=limit, cursor=cursor),
        )
        return {
            "items": [safe_audit_event(item) for item in page.items],
            "pagination": page.pagination.as_dict(),
            "scope": "agency",
            "agency_id": agency_id,
            "read_only": True,
        }


def safe_audit_event(record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": record.get("id"),
        "agency_id": record.get("agency_id"),
        "actor_user_id": record.get("actor_user_id"),
        "event_type": record.get("event_type"),
        "entity_type": record.get("entity_type"),
        "entity_id": record.get("entity_id"),
        "summary": redact_sensitive(record.get("summary")),
        "metadata": _safe_metadata(record.get("metadata")),
        "created_at": record.get("created_at"),
    }


def _filters(*, entity_type: str | None, entity_id: str | None, event_type: str | None) -> dict[str, Any]:
    return {
        key: value
        for key, value in {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "event_type": event_type,
        }.items()
        if value is not None
    }


def _safe_metadata(value: Any, *, key: str | None = None, depth: int = 0) -> Any:
    if key is not None and any(fragment in key.strip().lower() for fragment in _RESTRICTED_METADATA_FRAGMENTS):
        return REDACTED
    if depth >= _MAX_METADATA_DEPTH:
        return REDACTED
    if isinstance(value, Mapping):
        return {
            str(item_key): _safe_metadata(item_value, key=str(item_key), depth=depth + 1)
            for item_key, item_value in list(value.items())[:_MAX_METADATA_ITEMS]
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_safe_metadata(item, depth=depth + 1) for item in list(value)[:_MAX_METADATA_ITEMS]]
    return redact_sensitive(value, key=key)
