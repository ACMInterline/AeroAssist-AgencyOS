from __future__ import annotations

import base64
import binascii
from copy import deepcopy
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from database import Database
from models import (
    AuditEvent,
    DocumentStorageRecord,
    RequestV4Payload,
    RequestV4Update,
    new_id,
    now_utc,
)
from services.file_storage_service import (
    compute_checksum,
    resolve_storage_key,
    save_export_bytes,
)
from services.offer_delivery_client_interaction_service import (
    JourneyOfferDeliveryError,
    OfferDeliveryClientInteractionService,
)
from services.operational_collaboration_service import OperationalCollaborationService
from services.request_v4_service import update_request_v4


MAX_PORTAL_ITEMS = 500
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
PORTAL_UPLOAD_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
}
PORTAL_UPLOAD_EXTENSIONS = {
    "application/pdf": {".pdf"},
    "image/jpeg": {".jpeg", ".jpg"},
    "image/png": {".png"},
}
PORTAL_UPLOAD_DOCUMENT_STATUSES = {
    "required",
    "requested",
    "rejected",
    "expired",
}
SAFE_REQUEST_EDIT_STATUSES = {"draft"}
SAFE_REQUEST_CANCEL_STATUSES = {"draft", "new"}
FINANCE_INTERNAL_TOKENS = {
    "supplier",
    "margin",
    "commission",
    "cost",
    "markup",
    "provider",
    "credential",
    "secret",
    "raw",
    "internal",
}


class PortalProjectionError(ValueError):
    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


def _value(item: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if item.get(key) not in (None, ""):
            return item[key]
    return None


def _tokens(values: Any) -> set[str]:
    if not values:
        return set()
    if not isinstance(values, list):
        values = [values]
    return {str(value) for value in values if value not in (None, "")}


def _enum_value(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


def _safe_nested(value: Any) -> Any:
    if isinstance(value, list):
        return [_safe_nested(item) for item in value]
    if not isinstance(value, dict):
        return value
    safe: dict[str, Any] = {}
    for key, item in value.items():
        normalized = str(key).lower()
        if normalized in {
            "agency_id",
            "metadata",
            "internal_notes",
            "provider_payload_json",
            "provider_response_json",
            "raw_source_payloads",
            "source_evidence_json",
        }:
            continue
        if any(token in normalized for token in FINANCE_INTERNAL_TOKENS):
            continue
        safe[str(key)] = _safe_nested(item)
    return safe


def _safe_warning(value: Any) -> dict[str, Any]:
    item = value if isinstance(value, dict) else {"summary": str(value)}
    summary = _value(
        item,
        "client_message",
        "client_safe_summary",
        "client_visible_summary",
    )
    if not summary and item.get("client_visible") is True:
        summary = _value(item, "summary", "message", "title")
    return {
        "code": _value(item, "code", "warning_code", "type"),
        "severity": _value(item, "severity", "level") or "warning",
        "summary": summary or "Agency review is required.",
    }


def _created_sort(item: dict[str, Any]) -> str:
    return str(
        _value(
            item,
            "event_time",
            "last_message_at",
            "recorded_at",
            "created_at",
            "updated_at",
        )
        or ""
    )


class PortalProjectionService:
    """Read projections and governed portal actions over canonical Product Kernel records."""

    def __init__(self, db: Database):
        self.db = db
        self._scope_cache: dict[str, Any] | None = None

    @staticmethod
    def agency_id(ctx: dict[str, Any]) -> str:
        return str(ctx["account"]["agency_id"])

    @staticmethod
    def client_id(ctx: dict[str, Any]) -> str | None:
        return _value(ctx["account"], "client_profile_id", "client_id")

    @staticmethod
    def passenger_id(ctx: dict[str, Any]) -> str | None:
        return ctx["account"].get("passenger_profile_id")

    @staticmethod
    def actor_id(ctx: dict[str, Any]) -> str:
        return str(
            (ctx.get("identity") or {}).get("id")
            or ctx["account"].get("auth_identity_id")
            or ctx["account"]["id"]
        )

    async def scope(self, ctx: dict[str, Any]) -> dict[str, Any]:
        if self._scope_cache is not None:
            return self._scope_cache

        agency_id = self.agency_id(ctx)
        subject_type = ctx.get("subject_type")
        client_id = self.client_id(ctx)
        passenger_id = self.passenger_id(ctx)
        passenger_ids: set[str] = set()
        request_ids: set[str] = set()
        trip_ids: set[str] = set()

        if subject_type == "client":
            if not client_id:
                raise PortalProjectionError(
                    "PORTAL_CLIENT_LINK_REQUIRED",
                    "The portal account is not linked to a Client profile.",
                    403,
                )
            relationships = await self.db.collection(
                "client_passenger_relationships"
            ).find_many(
                {
                    "agency_id": agency_id,
                    "client_id": client_id,
                    "status": "active",
                    "can_view": True,
                },
                sort=[("id", 1)],
                limit=MAX_PORTAL_ITEMS,
            )
            passenger_ids = {
                str(item["passenger_id"])
                for item in relationships
                if item.get("passenger_id")
            }
            requests = await self.db.collection("travel_requests").find_many(
                {"agency_id": agency_id, "client_id": client_id},
                sort=[("id", 1)],
                limit=MAX_PORTAL_ITEMS,
            )
            request_ids = {str(item["id"]) for item in requests}
            trips = await self.db.collection("trip_dossiers").find_many(
                {"agency_id": agency_id},
                sort=[("id", 1)],
                limit=MAX_PORTAL_ITEMS,
            )
            trip_ids = {
                str(item["id"])
                for item in trips
                if item.get("primary_client_id") == client_id
                or bool(_tokens(item.get("linked_request_ids")).intersection(request_ids))
                or item.get("primary_request_id") in request_ids
            }
        else:
            if not passenger_id:
                raise PortalProjectionError(
                    "PORTAL_PASSENGER_LINK_REQUIRED",
                    "The portal account is not linked to a Passenger profile.",
                    403,
                )
            passenger_ids = {str(passenger_id)}
            request_passengers = await self.db.collection(
                "request_passengers"
            ).find_many(
                {"agency_id": agency_id},
                sort=[("id", 1)],
                limit=MAX_PORTAL_ITEMS,
            )
            request_ids = {
                str(item["request_id"])
                for item in request_passengers
                if _value(item, "passenger_profile_id", "passenger_id") == passenger_id
                and item.get("status") not in {"archived", "removed"}
            }
            trip_passengers = await self.db.collection("trip_passengers").find_many(
                {"agency_id": agency_id},
                sort=[("id", 1)],
                limit=MAX_PORTAL_ITEMS,
            )
            trip_ids = {
                str(item["trip_id"])
                for item in trip_passengers
                if _value(item, "passenger_profile_id", "passenger_id") == passenger_id
            }

        offers = await self.db.collection("offer_workspaces").find_many(
            {"agency_id": agency_id},
            sort=[("id", 1)],
            limit=MAX_PORTAL_ITEMS,
        )
        offer_ids = {
            str(item["id"])
            for item in offers
            if (
                subject_type == "client"
                and (
                    item.get("client_profile_id") == client_id
                    or item.get("request_id") in request_ids
                    or item.get("trip_id") in trip_ids
                )
            )
            or (
                subject_type == "passenger"
                and (
                    item.get("request_id") in request_ids
                    or item.get("trip_id") in trip_ids
                )
            )
        }

        booking_rows = await self.db.collection("booking_records").find_many(
            {"agency_id": agency_id},
            sort=[("id", 1)],
            limit=MAX_PORTAL_ITEMS,
        )
        booking_ids = {
            str(item["id"])
            for item in booking_rows
            if (
                subject_type == "client"
                and (
                    item.get("client_id") == client_id
                    or item.get("request_id") in request_ids
                    or item.get("trip_id") in trip_ids
                )
            )
            or (
                subject_type == "passenger"
                and (
                    passenger_id in _tokens(item.get("passenger_ids"))
                    or any(
                        _value(row, "passenger_profile_id", "passenger_id")
                        == passenger_id
                        for row in item.get("passengers_json") or []
                        if isinstance(row, dict)
                    )
                    or item.get("trip_id") in trip_ids
                )
            )
        }
        booking_workspace_ids = {
            str(item["booking_workspace_id"])
            for item in booking_rows
            if item.get("id") in booking_ids and item.get("booking_workspace_id")
        }

        ticket_rows = await self.db.collection("ticket_records").find_many(
            {"agency_id": agency_id},
            sort=[("id", 1)],
            limit=MAX_PORTAL_ITEMS,
        )
        ticket_ids = {
            str(item["id"])
            for item in ticket_rows
            if (
                subject_type == "passenger"
                and _value(
                    item,
                    "passenger_profile_id",
                    "passenger_id",
                )
                == passenger_id
            )
            or (
                subject_type == "client"
                and (
                    not _value(
                        item,
                        "passenger_profile_id",
                        "passenger_id",
                    )
                    or _value(
                        item,
                        "passenger_profile_id",
                        "passenger_id",
                    )
                    in passenger_ids
                )
                and (
                    item.get("booking_record_id") in booking_ids
                    or item.get("booking_workspace_id") in booking_workspace_ids
                    or item.get("trip_id") in trip_ids
                    or item.get("client_id") == client_id
                )
            )
        }

        emd_rows = await self.db.collection("emd_records").find_many(
            {"agency_id": agency_id},
            sort=[("id", 1)],
            limit=MAX_PORTAL_ITEMS,
        )
        emd_ids = {
            str(item["id"])
            for item in emd_rows
            if (
                subject_type == "passenger"
                and _value(
                    item,
                    "passenger_profile_id",
                    "passenger_id",
                )
                == passenger_id
            )
            or (
                subject_type == "client"
                and (
                    not _value(
                        item,
                        "passenger_profile_id",
                        "passenger_id",
                    )
                    or _value(
                        item,
                        "passenger_profile_id",
                        "passenger_id",
                    )
                    in passenger_ids
                )
                and (
                    item.get("booking_record_id") in booking_ids
                    or item.get("booking_workspace_id") in booking_workspace_ids
                    or item.get("trip_id") in trip_ids
                    or item.get("ticket_record_id") in ticket_ids
                    or item.get("client_id") == client_id
                )
            )
        }

        self._scope_cache = {
            "agency_id": agency_id,
            "subject_type": subject_type,
            "client_id": client_id,
            "passenger_id": passenger_id,
            "passenger_ids": passenger_ids,
            "request_ids": request_ids,
            "trip_ids": trip_ids,
            "offer_ids": offer_ids,
            "booking_ids": booking_ids,
            "booking_workspace_ids": booking_workspace_ids,
            "ticket_ids": ticket_ids,
            "emd_ids": emd_ids,
        }
        return self._scope_cache

    async def list_trips(self, ctx: dict[str, Any]) -> list[dict[str, Any]]:
        scope = await self.scope(ctx)
        rows = await self.db.collection("trip_dossiers").find_many(
            {"agency_id": scope["agency_id"]},
            sort=[("updated_at", -1), ("id", -1)],
            limit=MAX_PORTAL_ITEMS,
        )
        result = [
            self._trip_summary(item)
            for item in rows
            if item.get("id") in scope["trip_ids"]
        ]
        for item in result:
            segments = await self.db.collection("trip_segments").find_many(
                {"agency_id": scope["agency_id"], "trip_id": item["id"]},
                sort=[("segment_order", 1), ("id", 1)],
                limit=100,
            )
            item["next_departure"] = next(
                (
                    segment.get("departure_date")
                    for segment in segments
                    if segment.get("departure_date")
                ),
                None,
            )
        return result

    async def trip_detail(
        self, ctx: dict[str, Any], trip_id: str
    ) -> dict[str, Any]:
        scope = await self.scope(ctx)
        if trip_id not in scope["trip_ids"]:
            raise PortalProjectionError(
                "TRIP_NOT_FOUND", "Trip was not found in this portal account.", 404
            )
        trip = await self.db.collection("trip_dossiers").find_one(
            {"agency_id": scope["agency_id"], "id": trip_id}
        )
        if not trip:
            raise PortalProjectionError("TRIP_NOT_FOUND", "Trip was not found.", 404)
        passengers = await self.db.collection("trip_passengers").find_many(
            {"agency_id": scope["agency_id"], "trip_id": trip_id},
            sort=[("sort_order", 1), ("id", 1)],
            limit=100,
        )
        passengers = [
            self._trip_passenger(item)
            for item in passengers
            if not item.get("passenger_profile_id")
            or item.get("passenger_profile_id") in scope["passenger_ids"]
        ]
        segments = [
            self._trip_segment(item)
            for item in await self.db.collection("trip_segments").find_many(
                {"agency_id": scope["agency_id"], "trip_id": trip_id},
                sort=[("segment_order", 1), ("id", 1)],
                limit=100,
            )
        ]
        services = [
            self._trip_service(item)
            for item in await self.db.collection("trip_service_items").find_many(
                {"agency_id": scope["agency_id"], "trip_id": trip_id},
                sort=[("created_at", 1), ("id", 1)],
                limit=200,
            )
            if not item.get("passenger_ids")
            or bool(_tokens(item.get("passenger_ids")).intersection(scope["passenger_ids"]))
        ]
        bookings = [
            self._booking_summary(item)
            for item in await self.db.collection("booking_records").find_many(
                {"agency_id": scope["agency_id"], "trip_id": trip_id},
                sort=[("created_at", -1), ("id", -1)],
                limit=100,
            )
            if item.get("id") in scope["booking_ids"]
        ]
        tickets = [
            self._ticket_summary(item)
            for item in await self.db.collection("ticket_records").find_many(
                {"agency_id": scope["agency_id"], "trip_id": trip_id},
                sort=[("created_at", -1), ("id", -1)],
                limit=100,
            )
            if item.get("id") in scope["ticket_ids"]
        ]
        emds = [
            self._emd_summary(item)
            for item in await self.db.collection("emd_records").find_many(
                {"agency_id": scope["agency_id"], "trip_id": trip_id},
                sort=[("created_at", -1), ("id", -1)],
                limit=100,
            )
            if item.get("id") in scope["emd_ids"]
        ]
        accepted_offer = None
        snapshot_id = trip.get("accepted_offer_snapshot_id")
        if snapshot_id:
            snapshot = await self.db.collection(
                "trip_accepted_offer_snapshots"
            ).find_one(
                {
                    "agency_id": scope["agency_id"],
                    "id": snapshot_id,
                    "trip_id": trip_id,
                }
            )
            if snapshot:
                accepted_offer = self._accepted_snapshot(snapshot)
        documents = await self.list_documents(ctx, trip_id=trip_id)
        timeline = await self.timeline(ctx, entity_type="trip", entity_id=trip_id)
        threads = await self._threads(ctx, entity_type="trip", entity_id=trip_id)
        passenger_view = scope["subject_type"] == "passenger"
        accepted_offer_projection = accepted_offer
        if passenger_view and accepted_offer:
            accepted_offer_projection = {
                "id": accepted_offer.get("id"),
                "accepted_at": accepted_offer.get("accepted_at"),
                "immutable": True,
            }
        pets = (accepted_offer or {}).get("pets") or []
        special_items = (accepted_offer or {}).get("special_items") or []
        if passenger_view:
            pets = self._subject_rows(pets, scope["passenger_ids"], require_link=True)
            special_items = self._subject_rows(
                special_items,
                scope["passenger_ids"],
                require_link=True,
            )
        return {
            "trip": self._trip_summary(trip),
            "passengers": passengers,
            "segments": segments,
            "services": services,
            "pets": pets,
            "special_items": special_items,
            "accepted_offer": accepted_offer_projection,
            "bookings": bookings,
            "tickets": tickets,
            "emds": emds,
            "documents": documents,
            "timeline": timeline,
            "communications": threads,
            "read_only": True,
        }

    async def list_bookings(self, ctx: dict[str, Any]) -> list[dict[str, Any]]:
        scope = await self.scope(ctx)
        rows = await self.db.collection("booking_records").find_many(
            {"agency_id": scope["agency_id"]},
            sort=[("updated_at", -1), ("id", -1)],
            limit=MAX_PORTAL_ITEMS,
        )
        return [
            self._booking_summary(item)
            for item in rows
            if item.get("id") in scope["booking_ids"]
        ]

    async def booking_detail(
        self, ctx: dict[str, Any], booking_id: str
    ) -> dict[str, Any]:
        scope = await self.scope(ctx)
        if booking_id not in scope["booking_ids"]:
            raise PortalProjectionError(
                "BOOKING_NOT_FOUND",
                "Booking was not found in this portal account.",
                404,
            )
        booking = await self.db.collection("booking_records").find_one(
            {"agency_id": scope["agency_id"], "id": booking_id}
        )
        if not booking:
            raise PortalProjectionError(
                "BOOKING_NOT_FOUND", "Booking was not found.", 404
            )
        tickets = [
            self._ticket_summary(item)
            for item in await self.db.collection("ticket_records").find_many(
                {"agency_id": scope["agency_id"], "booking_record_id": booking_id},
                sort=[("created_at", -1), ("id", -1)],
                limit=100,
            )
            if item.get("id") in scope["ticket_ids"]
        ]
        emds = [
            self._emd_summary(item)
            for item in await self.db.collection("emd_records").find_many(
                {"agency_id": scope["agency_id"], "booking_record_id": booking_id},
                sort=[("created_at", -1), ("id", -1)],
                limit=100,
            )
            if item.get("id") in scope["emd_ids"]
        ]
        return {
            "booking": {
                **self._booking_summary(booking),
                "airline_locators": [
                    _safe_nested(item)
                    for item in booking.get("airline_locators_json") or []
                ],
                "passengers": [
                    _safe_nested(item)
                    for item in self._subject_rows(
                        booking.get("passengers_json") or [],
                        scope["passenger_ids"],
                        require_link=scope["subject_type"] == "passenger",
                    )
                ],
                "segments": [
                    _safe_nested(item) for item in booking.get("segments_json") or []
                ],
                "services": _safe_nested(
                    self._subject_rows(
                        booking.get("services_json") or {},
                        scope["passenger_ids"],
                        require_link=scope["subject_type"] == "passenger",
                    )
                ),
                "pets": _safe_nested(
                    self._subject_rows(
                        booking.get("pets_json") or {},
                        scope["passenger_ids"],
                        require_link=scope["subject_type"] == "passenger",
                    )
                ),
                "special_items": _safe_nested(
                    self._subject_rows(
                        booking.get("special_items_json") or {},
                        scope["passenger_ids"],
                        require_link=scope["subject_type"] == "passenger",
                    )
                ),
                "warnings": [
                    _safe_warning(item)
                    for item in booking.get("warnings_json") or []
                ],
            },
            "tickets": tickets,
            "emds": emds,
            "documents": await self.list_documents(ctx, booking_id=booking_id),
            "timeline": await self.timeline(
                ctx, entity_type="booking", entity_id=booking_id
            ),
            "communications": await self._threads(
                ctx, entity_type="booking", entity_id=booking_id
            ),
            "read_only": True,
        }

    async def list_tickets(self, ctx: dict[str, Any]) -> list[dict[str, Any]]:
        scope = await self.scope(ctx)
        rows = await self.db.collection("ticket_records").find_many(
            {"agency_id": scope["agency_id"]},
            sort=[("issue_date", -1), ("created_at", -1), ("id", -1)],
            limit=MAX_PORTAL_ITEMS,
        )
        return [
            self._ticket_summary(item)
            for item in rows
            if item.get("id") in scope["ticket_ids"]
        ]

    async def ticket_detail(
        self, ctx: dict[str, Any], ticket_id: str
    ) -> dict[str, Any]:
        scope = await self.scope(ctx)
        if ticket_id not in scope["ticket_ids"]:
            raise PortalProjectionError(
                "TICKET_NOT_FOUND", "Ticket was not found in this portal account.", 404
            )
        ticket = await self.db.collection("ticket_records").find_one(
            {"agency_id": scope["agency_id"], "id": ticket_id}
        )
        if not ticket:
            raise PortalProjectionError("TICKET_NOT_FOUND", "Ticket was not found.", 404)
        coupons = await self.db.collection("ticket_coupons").find_many(
            {"agency_id": scope["agency_id"], "ticket_record_id": ticket_id},
            sort=[("coupon_number", 1), ("id", 1)],
            limit=100,
        )
        refund_rows = await self.db.collection("refund_ledger_entries").find_many(
            {"agency_id": scope["agency_id"], "ticket_id": ticket_id},
            sort=[("recorded_at", -1), ("id", -1)],
            limit=100,
        )
        exchange_rows = await self.db.collection("exchange_ledger_entries").find_many(
            {"agency_id": scope["agency_id"], "ticket_id": ticket_id},
            sort=[("created_at", -1), ("id", -1)],
            limit=100,
        )
        return {
            "ticket": {
                **self._ticket_summary(ticket),
                "passenger": _safe_nested(ticket.get("passenger_snapshot_json") or {}),
                "segments": _safe_nested(ticket.get("segments_snapshot_json") or []),
                "baggage": _safe_nested(
                    (ticket.get("fare_bundle_snapshot_json") or {}).get("baggage")
                    or {}
                ),
                "warnings": [
                    _safe_warning(item) for item in ticket.get("warnings_json") or []
                ],
            },
            "coupons": [self._ticket_coupon(item) for item in coupons],
            "refunds": [self._refund_summary(item) for item in refund_rows],
            "exchanges": [self._exchange_summary(item) for item in exchange_rows],
            "documents": await self.list_documents(ctx, ticket_id=ticket_id),
            "timeline": await self.timeline(
                ctx, entity_type="ticket", entity_id=ticket_id
            ),
            "read_only": True,
        }

    async def list_emds(self, ctx: dict[str, Any]) -> list[dict[str, Any]]:
        scope = await self.scope(ctx)
        rows = await self.db.collection("emd_records").find_many(
            {"agency_id": scope["agency_id"]},
            sort=[("issue_date", -1), ("created_at", -1), ("id", -1)],
            limit=MAX_PORTAL_ITEMS,
        )
        return [
            self._emd_summary(item)
            for item in rows
            if item.get("id") in scope["emd_ids"]
        ]

    async def emd_detail(
        self, ctx: dict[str, Any], emd_id: str
    ) -> dict[str, Any]:
        scope = await self.scope(ctx)
        if emd_id not in scope["emd_ids"]:
            raise PortalProjectionError(
                "EMD_NOT_FOUND", "EMD was not found in this portal account.", 404
            )
        emd = await self.db.collection("emd_records").find_one(
            {"agency_id": scope["agency_id"], "id": emd_id}
        )
        if not emd:
            raise PortalProjectionError("EMD_NOT_FOUND", "EMD was not found.", 404)
        coupons = await self.db.collection("emd_coupons").find_many(
            {"agency_id": scope["agency_id"], "emd_record_id": emd_id},
            sort=[("coupon_number", 1), ("id", 1)],
            limit=100,
        )
        refund_rows = await self.db.collection("refund_ledger_entries").find_many(
            {"agency_id": scope["agency_id"], "emd_id": emd_id},
            sort=[("recorded_at", -1), ("id", -1)],
            limit=100,
        )
        exchange_rows = await self.db.collection("exchange_ledger_entries").find_many(
            {"agency_id": scope["agency_id"], "emd_id": emd_id},
            sort=[("created_at", -1), ("id", -1)],
            limit=100,
        )
        return {
            "emd": {
                **self._emd_summary(emd),
                "passenger": _safe_nested(emd.get("passenger_snapshot_json") or {}),
                "service": _safe_nested(
                    emd.get("linked_service_snapshot_json") or {}
                ),
                "warnings": [
                    _safe_warning(item) for item in emd.get("warnings_json") or []
                ],
            },
            "coupons": [self._emd_coupon(item) for item in coupons],
            "refunds": [self._refund_summary(item) for item in refund_rows],
            "exchanges": [self._exchange_summary(item) for item in exchange_rows],
            "documents": await self.list_documents(ctx, emd_id=emd_id),
            "timeline": await self.timeline(ctx, entity_type="emd", entity_id=emd_id),
            "read_only": True,
        }

    async def list_documents(
        self,
        ctx: dict[str, Any],
        *,
        trip_id: str | None = None,
        booking_id: str | None = None,
        ticket_id: str | None = None,
        emd_id: str | None = None,
    ) -> list[dict[str, Any]]:
        scope = await self.scope(ctx)
        visible_ids = await self._visible_document_ids(scope)
        rows = await self.db.collection("document_workspaces").find_many(
            {"agency_id": scope["agency_id"]},
            sort=[("updated_at", -1), ("id", -1)],
            limit=MAX_PORTAL_ITEMS,
        )
        valid_booking_links: set[str] | None = None
        if booking_id:
            booking = await self.db.collection("booking_records").find_one(
                {
                    "agency_id": scope["agency_id"],
                    "id": booking_id,
                }
            )
            valid_booking_links = {booking_id}
            if booking and booking.get("booking_workspace_id"):
                valid_booking_links.add(str(booking["booking_workspace_id"]))
        result = []
        for item in rows:
            if item.get("id") not in visible_ids:
                continue
            if trip_id and item.get("trip_workspace_id") != trip_id:
                continue
            if valid_booking_links is not None and item.get(
                "booking_workspace_id"
            ) not in valid_booking_links:
                continue
            if ticket_id and item.get("ticket_workspace_id") != ticket_id:
                continue
            if emd_id and item.get("emd_workspace_id") != emd_id:
                continue
            result.append(self._document_summary(item))
        return result

    async def document_detail(
        self, ctx: dict[str, Any], document_id: str
    ) -> dict[str, Any]:
        scope = await self.scope(ctx)
        visible_ids = await self._visible_document_ids(scope)
        if document_id not in visible_ids:
            raise PortalProjectionError(
                "DOCUMENT_NOT_FOUND",
                "Document was not found in this portal account.",
                404,
            )
        document = await self.db.collection("document_workspaces").find_one(
            {"agency_id": scope["agency_id"], "id": document_id}
        )
        if not document:
            raise PortalProjectionError(
                "DOCUMENT_NOT_FOUND", "Document was not found.", 404
            )
        versions = await self._document_versions(scope["agency_id"], document)
        return {
            "document": self._document_summary(document),
            "versions": versions,
            "upload_allowed": await self._document_upload_allowed(ctx, document),
            "download_available": bool(versions or document.get("rendered_document_ids")),
            "timeline": await self.timeline(
                ctx, entity_type="document", entity_id=document_id
            ),
            "immutable_history": True,
        }

    async def upload_document(
        self, ctx: dict[str, Any], document_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        scope = await self.scope(ctx)
        visible_ids = await self._visible_document_ids(scope)
        if document_id not in visible_ids:
            raise PortalProjectionError(
                "DOCUMENT_NOT_FOUND",
                "Document was not found in this portal account.",
                404,
            )
        document = await self.db.collection("document_workspaces").find_one(
            {"agency_id": scope["agency_id"], "id": document_id}
        )
        if not document or not await self._document_upload_allowed(ctx, document):
            raise PortalProjectionError(
                "DOCUMENT_UPLOAD_NOT_REQUESTED",
                "The agency has not requested an upload for this document.",
                403,
            )
        filename = Path(str(payload.get("file_name") or "")).name
        content_type = str(payload.get("content_type") or "").lower()
        encoded = str(payload.get("content_base64") or "")
        if not filename or filename in {".", ".."}:
            raise PortalProjectionError(
                "DOCUMENT_FILENAME_REQUIRED", "Choose a file with a valid name."
            )
        if content_type not in PORTAL_UPLOAD_CONTENT_TYPES:
            raise PortalProjectionError(
                "DOCUMENT_TYPE_NOT_ALLOWED",
                "Only PDF, JPEG, and PNG documents can be uploaded.",
            )
        if Path(filename).suffix.lower() not in PORTAL_UPLOAD_EXTENSIONS[content_type]:
            raise PortalProjectionError(
                "DOCUMENT_TYPE_MISMATCH",
                "The file extension does not match the selected document type.",
            )
        try:
            data = base64.b64decode(encoded.encode("ascii"), validate=True)
        except (binascii.Error, UnicodeEncodeError) as exc:
            raise PortalProjectionError(
                "DOCUMENT_CONTENT_INVALID", "The uploaded document is invalid."
            ) from exc
        if not data or len(data) > MAX_UPLOAD_BYTES:
            raise PortalProjectionError(
                "DOCUMENT_SIZE_INVALID",
                "The document must be between 1 byte and 5 MB.",
            )
        versions = await self._document_versions(scope["agency_id"], document)
        version_number = len(versions) + 1
        storage = save_export_bytes(
            scope["agency_id"],
            f"portal-{document_id}",
            filename,
            content_type,
            data,
        )
        storage_record = DocumentStorageRecord(
            agency_id=scope["agency_id"],
            related_entity_type="document_workspace",
            related_entity_id=document_id,
            document_type=str(document.get("document_type") or "other"),
            filename_original=filename,
            filename_stored=Path(storage["storage_key"]).name,
            storage_key=storage["storage_key"],
            storage_backend="local_filesystem",
            storage_status="active",
            content_type=content_type,
            size_bytes=len(data),
            checksum_sha256=storage["checksum_sha256"],
            created_by_user_id=self.actor_id(ctx),
            created_by_email=(ctx.get("identity") or {}).get("email"),
            delivery_allowed=False,
            public_access_allowed=False,
            audit_metadata={
                "portal_upload": True,
                "portal_mapping_id": ctx["account"]["id"],
                "version_number": version_number,
            },
        )
        created = await self.db.collection("document_storage_records").insert_one(
            storage_record.model_dump(mode="json")
        )
        await self.db.collection("document_workspaces").update_one(
            {
                "agency_id": scope["agency_id"],
                "id": document_id,
                "customer_visible": True,
                "internal_only": False,
            },
            {
                "storage_reference": created["id"],
                "file_name": filename,
                "file_type": content_type,
                "file_size": len(data),
                "received_status": "received",
                "document_status": "received",
                "updated_by": self.actor_id(ctx),
            },
        )
        await self._audit(
            ctx,
            "portal.document_uploaded",
            "document_workspace",
            document_id,
            "Portal user uploaded a requested document version.",
            {
                "storage_record_id": created["id"],
                "version_number": version_number,
                "content_type": content_type,
                "size_bytes": len(data),
            },
        )
        await self._timeline_event(
            ctx,
            "document",
            document_id,
            "document_uploaded",
            f"{filename} was uploaded for agency review.",
            idempotency_key=f"portal-document-upload:{created['id']}",
        )
        return await self.document_detail(ctx, document_id)

    async def document_download(
        self, ctx: dict[str, Any], document_id: str, version_id: str | None = None
    ) -> dict[str, Any]:
        detail = await self.document_detail(ctx, document_id)
        scope = await self.scope(ctx)
        document = await self.db.collection("document_workspaces").find_one(
            {"agency_id": scope["agency_id"], "id": document_id}
        )
        records = await self.db.collection("document_storage_records").find_many(
            {
                "agency_id": scope["agency_id"],
                "related_entity_type": "document_workspace",
                "related_entity_id": document_id,
            },
            sort=[("created_at", -1), ("id", -1)],
            limit=100,
        )
        record = (
            next((item for item in records if item.get("id") == version_id), None)
            if version_id
            else (records[0] if records else None)
        )
        if record:
            storage_key = record.get("storage_key")
            if not storage_key:
                raise PortalProjectionError(
                    "DOCUMENT_FILE_UNAVAILABLE",
                    "This document file is not available.",
                    404,
                )
            path = resolve_storage_key(storage_key)
            if not path.is_file():
                raise PortalProjectionError(
                    "DOCUMENT_FILE_UNAVAILABLE",
                    "This document file is not available.",
                    404,
                )
            data = path.read_bytes()
            checksum = record.get("checksum_sha256")
            if checksum and compute_checksum(data) != checksum:
                raise PortalProjectionError(
                    "DOCUMENT_CHECKSUM_FAILED",
                    "Document integrity verification failed.",
                    409,
                )
            return {
                "content": data,
                "file_name": record.get("filename_original")
                or detail["document"].get("title")
                or "document",
                "content_type": record.get("content_type")
                or "application/octet-stream",
            }
        for rendered_id in (document or {}).get("rendered_document_ids") or []:
            exports = await self.db.collection("document_exports").find_many(
                {
                    "agency_id": scope["agency_id"],
                    "rendered_document_id": rendered_id,
                    "status": "generated",
                    "client_visible": True,
                },
                sort=[("generated_at", -1), ("id", -1)],
                limit=20,
            )
            if not exports:
                continue
            export = exports[0]
            storage_key = export.get("storage_key")
            if not storage_key:
                continue
            path = resolve_storage_key(storage_key)
            if not path.is_file():
                continue
            data = path.read_bytes()
            if export.get("checksum_sha256") and compute_checksum(data) != export.get(
                "checksum_sha256"
            ):
                raise PortalProjectionError(
                    "DOCUMENT_CHECKSUM_FAILED",
                    "Document integrity verification failed.",
                    409,
                )
            return {
                "content": data,
                "file_name": export.get("filename") or "document",
                "content_type": export.get("content_type")
                or "application/octet-stream",
            }
        raise PortalProjectionError(
            "DOCUMENT_FILE_UNAVAILABLE", "This document file is not available.", 404
        )

    async def timeline(
        self,
        ctx: dict[str, Any],
        *,
        entity_type: str | None = None,
        entity_id: str | None = None,
    ) -> list[dict[str, Any]]:
        scope = await self.scope(ctx)
        visibility = "passenger" if scope["subject_type"] == "passenger" else "client"
        rows = await self.db.collection("operational_timelines").find_many(
            {"agency_id": scope["agency_id"]},
            sort=[("event_time", -1), ("id", -1)],
            limit=MAX_PORTAL_ITEMS,
        )
        result = []
        for item in rows:
            item_visibility = _enum_value(item.get("visibility"))
            if item_visibility != visibility:
                continue
            if not self._timeline_in_scope(scope, item):
                continue
            normalized_type = self._entity_type(item.get("entity_type"))
            if entity_type and normalized_type != self._entity_type(entity_type):
                continue
            if entity_id and item.get("entity_id") != entity_id:
                continue
            result.append(
                {
                    "id": item["id"],
                    "event_type": item.get("event_type"),
                    "category": item.get("event_category"),
                    "status": item.get("event_status"),
                    "priority": item.get("event_priority"),
                    "summary": item.get("summary")
                    or str(item.get("event_type") or "Activity").replace("_", " "),
                    "actor": item.get("actor_display"),
                    "entity_type": normalized_type,
                    "entity_id": item.get("entity_id"),
                    "approval_reference": item.get("approval_reference"),
                    "approval_status": item.get("approval_status"),
                    "due_date": item.get("due_date"),
                    "completed_date": item.get("completed_date"),
                    "timeline_link": f"/portal/timeline?event={item['id']}",
                    "occurred_at": item.get("event_time") or item.get("created_at"),
                    "append_only": True,
                }
            )
        return result

    async def notifications(self, ctx: dict[str, Any]) -> list[dict[str, Any]]:
        scope = await self.scope(ctx)
        timeline = await self.timeline(ctx)
        timeline_by_id = {item["id"]: item for item in timeline}
        visibility = "passenger" if scope["subject_type"] == "passenger" else "client"
        rows = await self.db.collection(
            "operational_notification_projections"
        ).find_many(
            {"agency_id": scope["agency_id"]},
            sort=[("created_at", -1), ("id", -1)],
            limit=MAX_PORTAL_ITEMS,
        )
        return [
            {
                "id": item["id"],
                "type": item.get("notification_type"),
                "status": item.get("status"),
                "title": item.get("title"),
                "summary": item.get("summary"),
                "due_at": item.get("due_at"),
                "timeline_entry_id": item.get("timeline_entry_id"),
                "timeline_link": f"/portal/timeline?event={item.get('timeline_entry_id')}",
                "created_at": item.get("created_at"),
            }
            for item in rows
            if _enum_value(item.get("visibility")) == visibility
            and item.get("timeline_entry_id") in timeline_by_id
        ]

    async def finance(self, ctx: dict[str, Any]) -> dict[str, Any]:
        scope = await self.scope(ctx)
        if scope["subject_type"] != "client":
            raise PortalProjectionError(
                "CLIENT_FINANCE_SCOPE_REQUIRED",
                "Financial records are available only to the linked Client account.",
                403,
            )
        invoices = await self.db.collection("invoices").find_many(
            {
                "agency_id": scope["agency_id"],
                "client_id": scope["client_id"],
            },
            sort=[("created_at", -1), ("id", -1)],
            limit=MAX_PORTAL_ITEMS,
        )
        invoice_ids = {item["id"] for item in invoices}
        line_rows = await self.db.collection("invoice_line_items").find_many(
            {"agency_id": scope["agency_id"]},
            sort=[("created_at", 1), ("id", 1)],
            limit=MAX_PORTAL_ITEMS,
        )
        payments = await self.db.collection("payment_records").find_many(
            {"agency_id": scope["agency_id"]},
            sort=[("received_at", -1), ("created_at", -1), ("id", -1)],
            limit=MAX_PORTAL_ITEMS,
        )
        credits = await self.db.collection("credit_notes").find_many(
            {
                "agency_id": scope["agency_id"],
                "client_id": scope["client_id"],
            },
            sort=[("created_at", -1), ("id", -1)],
            limit=MAX_PORTAL_ITEMS,
        )
        refunds = await self.db.collection("refund_ledger_entries").find_many(
            {"agency_id": scope["agency_id"]},
            sort=[("recorded_at", -1), ("id", -1)],
            limit=MAX_PORTAL_ITEMS,
        )
        invoice_result = []
        for invoice in invoices:
            invoice_result.append(
                {
                    **self._invoice_summary(invoice),
                    "lines": [
                        self._invoice_line(item)
                        for item in line_rows
                        if item.get("invoice_id") == invoice["id"]
                    ],
                }
            )
        payment_result = [
            self._payment_summary(item)
            for item in payments
            if item.get("invoice_id") in invoice_ids
            or item.get("client_id") == scope["client_id"]
        ]
        credit_result = [self._credit_summary(item) for item in credits]
        refund_result = [
            self._refund_summary(item)
            for item in refunds
            if item.get("client_id") == scope["client_id"]
            or item.get("booking_id") in scope["booking_ids"]
            or item.get("ticket_id") in scope["ticket_ids"]
            or item.get("emd_id") in scope["emd_ids"]
        ]
        outstanding = sum(
            float(item.get("due_amount") or 0)
            for item in invoices
            if item.get("status") not in {"paid", "credited", "cancelled", "voided"}
        )
        return {
            "summary": {
                "currency": self._single_currency(
                    [item.get("currency") for item in invoices]
                ),
                "outstanding_balance": round(outstanding, 2),
                "invoice_count": len(invoices),
                "payment_count": len(payment_result),
                "travel_credit_total": round(
                    sum(
                        float(item.get("total_amount") or 0)
                        for item in credits
                        if item.get("status") == "issued"
                    ),
                    2,
                ),
                "refund_total": round(
                    sum(float(item.get("amount") or 0) for item in refund_result),
                    2,
                ),
            },
            "invoices": invoice_result,
            "payments": payment_result,
            "credits": credit_result,
            "refunds": refund_result,
            "payment_execution_enabled": False,
        }

    async def approvals(self, ctx: dict[str, Any]) -> list[dict[str, Any]]:
        scope = await self.scope(ctx)
        timeline = await self.timeline(ctx)
        result = [
            {
                "id": item["id"],
                "approval_type": item.get("event_type"),
                "reference": item.get("approval_reference"),
                "status": item.get("approval_status") or item.get("status"),
                "summary": item.get("summary"),
                "occurred_at": item.get("occurred_at"),
                "timeline_entry_id": item["id"],
            }
            for item in timeline
            if item.get("approval_reference")
            or item.get("approval_status")
            or item.get("event_type") in {"approval_requested", "portal_approval"}
        ]
        acceptances = await self.db.collection("offer_acceptances").find_many(
            {"agency_id": scope["agency_id"]},
            sort=[("accepted_at", -1), ("created_at", -1), ("id", -1)],
            limit=MAX_PORTAL_ITEMS,
        )
        for item in acceptances:
            if (
                item.get("workspace_id") not in scope["offer_ids"]
                and item.get("request_id") not in scope["request_ids"]
                and item.get("trip_id") not in scope["trip_ids"]
            ):
                continue
            result.append(
                {
                    "id": item["id"],
                    "approval_type": "offer_acceptance",
                    "reference": item.get("accepted_snapshot_id"),
                    "status": item.get("status"),
                    "summary": _safe_nested(
                        item.get("client_visible_summary_json") or {}
                    ),
                    "occurred_at": item.get("accepted_at") or item.get("created_at"),
                    "timeline_entry_id": None,
                }
            )
        result.sort(key=_created_sort, reverse=True)
        return result

    async def update_profile(
        self, ctx: dict[str, Any], payload: dict[str, Any]
    ) -> dict[str, Any]:
        scope = await self.scope(ctx)
        if scope["subject_type"] == "client":
            allowed = {
                "display_name",
                "legal_name",
                "primary_phone",
                "country",
                "city",
                "address_line_1",
                "address_line_2",
                "postal_code",
                "preferred_language",
                "default_currency",
                "marketing_consent",
                "data_processing_consent",
            }
            collection = "client_profiles"
            record_id = scope["client_id"]
        else:
            allowed = {
                "middle_name",
                "display_name",
                "gender",
                "nationality",
                "residence_country",
                "primary_language",
                "passport_country",
                "passport_expiry",
                "known_assistance_needs",
                "meal_preferences",
                "seating_preferences",
                "baggage_preferences",
                "emergency_contact",
                "loyalty_numbers",
            }
            collection = "passenger_profiles"
            record_id = scope["passenger_id"]
        updates = {
            key: value
            for key, value in payload.items()
            if key in allowed
        }
        if not updates:
            raise PortalProjectionError(
                "PROFILE_UPDATE_EMPTY", "No editable profile fields were provided."
            )
        updated = await self.db.collection(collection).update_one(
            {
                "agency_id": scope["agency_id"],
                "id": record_id,
                "status": {"$ne": "archived"},
            },
            updates,
        )
        if not updated:
            raise PortalProjectionError(
                "PROFILE_NOT_FOUND", "The linked profile is unavailable.", 404
            )
        await self._audit(
            ctx,
            "portal.profile_updated",
            "client" if scope["subject_type"] == "client" else "passenger",
            str(record_id),
            "Portal user updated governed Product Kernel profile fields.",
            {"updated_fields": sorted(updates)},
        )
        await self._timeline_event(
            ctx,
            "client" if scope["subject_type"] == "client" else "passenger",
            str(record_id),
            "profile_updated",
            "Travel profile details were updated.",
            idempotency_key=f"portal-profile-update:{new_id()}",
        )
        return self._profile_projection(scope["subject_type"], updated)

    async def update_request_draft(
        self, ctx: dict[str, Any], request_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        scope = await self.scope(ctx)
        if scope["subject_type"] != "client" or request_id not in scope["request_ids"]:
            raise PortalProjectionError(
                "REQUEST_NOT_FOUND",
                "Request was not found in this portal account.",
                404,
            )
        request = await self.db.collection("travel_requests").find_one(
            {"agency_id": scope["agency_id"], "id": request_id}
        )
        if not request or request.get("status") not in SAFE_REQUEST_EDIT_STATUSES:
            raise PortalProjectionError(
                "REQUEST_NOT_EDITABLE",
                "Only a draft request can be edited in the portal.",
                409,
            )
        if request.get("request_version") != 4:
            raise PortalProjectionError(
                "REQUEST_RECONCILIATION_REQUIRED",
                "This historical request must be reconciled before portal editing.",
                409,
            )
        canonical = RequestV4Payload.model_validate(
            deepcopy(request.get("canonical_payload") or {})
        )
        data = canonical.model_dump(mode="json")
        if payload.get("title") is not None:
            data["trip"]["trip_label"] = str(payload["title"]).strip()
        if payload.get("client_notes") is not None:
            data["request_level_notes"] = str(payload["client_notes"]).strip()
        if not data["trip"]["trip_label"]:
            raise PortalProjectionError(
                "REQUEST_TITLE_REQUIRED", "Request title is required."
            )
        updated = await update_request_v4(
            self.db,
            scope["agency_id"],
            request_id,
            RequestV4Update(
                canonical_payload=RequestV4Payload.model_validate(data)
            ),
            self.actor_id(ctx),
        )
        return self._request_summary(updated["request"] if "request" in updated else updated)

    async def cancel_request(
        self, ctx: dict[str, Any], request_id: str, reason: str
    ) -> dict[str, Any]:
        scope = await self.scope(ctx)
        if scope["subject_type"] != "client" or request_id not in scope["request_ids"]:
            raise PortalProjectionError(
                "REQUEST_NOT_FOUND",
                "Request was not found in this portal account.",
                404,
            )
        request = await self.db.collection("travel_requests").find_one(
            {"agency_id": scope["agency_id"], "id": request_id}
        )
        if not request or request.get("status") not in SAFE_REQUEST_CANCEL_STATUSES:
            raise PortalProjectionError(
                "REQUEST_CANCELLATION_NOT_ALLOWED",
                "This request is already being processed and cannot be cancelled in the portal.",
                409,
            )
        if request.get("request_version") != 4:
            raise PortalProjectionError(
                "REQUEST_RECONCILIATION_REQUIRED",
                "This historical request must be reconciled before portal cancellation.",
                409,
            )
        canonical = RequestV4Payload.model_validate(
            deepcopy(request.get("canonical_payload") or {})
        )
        data = canonical.model_dump(mode="json")
        data["admin_metadata"]["status"] = "cancelled"
        data["request_level_notes"] = "\n".join(
            value
            for value in [
                str(data.get("request_level_notes") or "").strip(),
                f"Cancellation requested: {reason.strip()}",
            ]
            if value
        )
        updated = await update_request_v4(
            self.db,
            scope["agency_id"],
            request_id,
            RequestV4Update(
                canonical_payload=RequestV4Payload.model_validate(data)
            ),
            self.actor_id(ctx),
        )
        cancelled = await self.db.collection("travel_requests").find_one(
            {
                "agency_id": scope["agency_id"],
                "id": request_id,
                "status": "cancelled",
            }
        )
        if not cancelled:
            raise PortalProjectionError(
                "REQUEST_CANCELLATION_CONFLICT",
                "The request changed before cancellation could be recorded.",
                409,
            )
        cancelled = await self.db.collection("travel_requests").update_one(
            {
                "agency_id": scope["agency_id"],
                "id": request_id,
                "status": "cancelled",
            },
            {"closed_at": now_utc()},
        ) or cancelled
        await self._audit(
            ctx,
            "portal.request_cancelled",
            "request",
            request_id,
            "Client cancelled an unprocessed request.",
            {"reason": reason.strip()},
        )
        await self._timeline_event(
            ctx,
            "request",
            request_id,
            "request_cancelled",
            "The client cancelled this request before processing.",
            idempotency_key=f"portal-request-cancel:{request_id}",
        )
        request_result = updated["request"] if "request" in updated else cancelled
        return self._request_summary({**request_result, **cancelled})

    async def dashboard(self, ctx: dict[str, Any]) -> dict[str, Any]:
        scope = await self.scope(ctx)
        trips = await self.list_trips(ctx)
        bookings = await self.list_bookings(ctx)
        tickets = await self.list_tickets(ctx)
        documents = await self.list_documents(ctx)
        timeline = await self.timeline(ctx)
        notifications = await self.notifications(ctx)
        threads = await self._threads(ctx)
        services = await self._visible_services(scope)
        actions = [
            item
            for item in notifications
            if item.get("type")
            in {"action_required", "approval_required", "deadline", "warning", "failed"}
        ]
        actions.extend(await self._portal_actions(scope))
        offer_deliveries = []
        if scope["subject_type"] == "client":
            try:
                delivery_result = await OfferDeliveryClientInteractionService(
                    self.db
                ).portal_list(ctx)
                offer_deliveries = delivery_result.get("items") or []
            except JourneyOfferDeliveryError:
                actions.append(
                    {
                        "id": "offer-delivery-linkage-review",
                        "type": "warning",
                        "title": "A travel option needs agency review",
                        "summary": (
                            "A released travel option could not be linked safely. "
                            "Your travel agency has been asked to review it."
                        ),
                        "href": "/portal/travel-options",
                    }
                )
        finance = (
            await self.finance(ctx)
            if scope["subject_type"] == "client"
            else {
                "summary": {
                    "outstanding_balance": 0,
                    "travel_credit_total": 0,
                },
                "invoices": [],
                "payments": [],
                "credits": [],
                "refunds": [],
            }
        )
        upcoming = [
            item
            for item in trips
            if item.get("status") not in {"completed", "cancelled", "archived"}
        ]
        upcoming.sort(key=lambda item: str(item.get("next_departure") or "9999"))
        pending_offers = [
            item
            for item in offer_deliveries
            if item.get("status")
            not in {"accepted", "declined", "expired", "revoked", "archived"}
        ]
        return {
            "subject_type": scope["subject_type"],
            "counts": {
                "upcoming_trips": len(upcoming),
                "pending_offers": len(pending_offers),
                "action_required": len(actions),
                "documents": len(documents),
                "communications": len(threads),
                "notifications": len(notifications),
                "bookings": len(bookings),
                "tickets": len(tickets),
                "service_requests": len(services),
            },
            "upcoming_trips": upcoming[:5],
            "pending_offers": pending_offers[:5],
            "action_required": actions[:8],
            "outstanding_payments": finance["summary"],
            "recent_communications": threads[:5],
            "recent_documents": documents[:5],
            "recent_timeline": timeline[:8],
            "travel_credits": finance.get("credits", [])[:5],
            "service_requests": services[:8],
            "notifications": notifications[:8],
            "bookings": bookings[:5],
            "tickets": tickets[:5],
            "travel_profile": self._profile_projection(
                scope["subject_type"],
                ctx["passenger"]
                if scope["subject_type"] == "passenger"
                else ctx["client"],
            ),
        }

    async def migration_analysis(
        self, agency_id: str | None = None
    ) -> dict[str, Any]:
        filters = {"agency_id": agency_id} if agency_id else None
        mappings = await self.db.collection("portal_access_mappings").find_many(
            filters,
            sort=[("id", 1)],
            limit=MAX_PORTAL_ITEMS,
        )
        identities = {
            item["id"]: item
            for item in await self.db.collection("auth_identities").find_many(
                None,
                sort=[("id", 1)],
                limit=MAX_PORTAL_ITEMS,
            )
        }
        legacy_users = [
            item
            for item in mappings
            if item.get("linkage_version") == "legacy_email"
            or not item.get("auth_identity_id")
        ]
        missing_identity = [
            item["id"]
            for item in mappings
            if item.get("auth_identity_id")
            and item.get("auth_identity_id") not in identities
        ]
        active_by_identity: dict[str, list[str]] = {}
        active_by_subject: dict[str, list[str]] = {}
        missing_subject_links = []
        for item in mappings:
            if (item.get("status") or item.get("portal_status")) != "active":
                continue
            identity_id = item.get("auth_identity_id")
            if identity_id:
                active_by_identity.setdefault(str(identity_id), []).append(item["id"])
            subject_type = item.get("subject_type")
            subject_id = (
                _value(item, "client_profile_id", "client_id")
                if subject_type == "client"
                else item.get("passenger_profile_id")
            )
            if subject_type and subject_id:
                active_by_subject.setdefault(
                    f"{subject_type}:{subject_id}", []
                ).append(item["id"])
            else:
                missing_subject_links.append(item["id"])
        historical_counts = {}
        for collection in [
            "portal_action_events",
            "document_acknowledgements",
            "journey_offer_client_decisions",
            "journey_offer_client_interactions",
        ]:
            historical_counts[collection] = await self.db.collection(collection).count(
                filters
            )
        return {
            "dry_run": True,
            "writes_performed": 0,
            "agency_filter": agency_id,
            "mapping_count": len(mappings),
            "legacy_mapping_ids": [item["id"] for item in legacy_users],
            "missing_identity_mapping_ids": missing_identity,
            "missing_subject_mapping_ids": missing_subject_links,
            "duplicate_active_identity_mappings": {
                key: values
                for key, values in active_by_identity.items()
                if len(values) > 1
            },
            "duplicate_active_subject_mappings": {
                key: values
                for key, values in active_by_subject.items()
                if len(values) > 1
            },
            "historical_portal_record_counts": historical_counts,
            "write_mode_available": False,
        }

    async def _visible_document_ids(self, scope: dict[str, Any]) -> set[str]:
        rows = await self.db.collection("document_workspaces").find_many(
            {"agency_id": scope["agency_id"]},
            sort=[("id", 1)],
            limit=MAX_PORTAL_ITEMS,
        )
        visible = set()
        for item in rows:
            if not item.get("customer_visible") or item.get("internal_only"):
                continue
            passenger_link = _value(
                item,
                "passenger_profile_id",
                "passenger_id",
            )
            if passenger_link and passenger_link not in scope["passenger_ids"]:
                continue
            linked = (
                passenger_link in scope["passenger_ids"]
                or item.get("travel_request_workspace_id") in scope["request_ids"]
                or item.get("trip_workspace_id") in scope["trip_ids"]
                or item.get("booking_workspace_id")
                in scope["booking_ids"] | scope["booking_workspace_ids"]
                or item.get("ticket_workspace_id") in scope["ticket_ids"]
                or item.get("emd_workspace_id") in scope["emd_ids"]
            )
            if linked:
                visible.add(str(item["id"]))
        return visible

    @staticmethod
    def _subject_rows(
        value: Any,
        passenger_ids: set[str],
        *,
        require_link: bool,
    ) -> Any:
        if isinstance(value, list):
            result = []
            for item in value:
                if not isinstance(item, dict):
                    if not require_link:
                        result.append(item)
                    continue
                linked = _tokens(
                    _value(
                        item,
                        "passenger_profile_ids",
                        "passenger_ids",
                        "passenger_profile_id",
                        "passenger_id",
                    )
                )
                if linked:
                    if linked.intersection(passenger_ids):
                        result.append(item)
                elif not require_link:
                    result.append(item)
            return result
        if isinstance(value, dict):
            linked = _tokens(
                _value(
                    value,
                    "passenger_profile_ids",
                    "passenger_ids",
                    "passenger_profile_id",
                    "passenger_id",
                )
            )
            if linked:
                return value if linked.intersection(passenger_ids) else {}
            if require_link:
                return {}
            return value
        return value if not require_link else []

    async def _document_upload_allowed(
        self, ctx: dict[str, Any], document: dict[str, Any]
    ) -> bool:
        status_value = str(document.get("document_status") or "")
        explicitly_requested = (
            status_value in PORTAL_UPLOAD_DOCUMENT_STATUSES
            or document.get("received_status") in {"requested", "missing"}
        )
        if not explicitly_requested:
            return False
        scope = await self.scope(ctx)
        passenger_id = document.get("passenger_id")
        if scope["subject_type"] == "passenger":
            return passenger_id == scope["passenger_id"]
        if not passenger_id:
            return True
        relationship = await self.db.collection(
            "client_passenger_relationships"
        ).find_one(
            {
                "agency_id": scope["agency_id"],
                "client_id": scope["client_id"],
                "passenger_id": passenger_id,
                "status": "active",
                "can_upload_documents": True,
            }
        )
        return bool(relationship)

    async def _document_versions(
        self, agency_id: str, document: dict[str, Any]
    ) -> list[dict[str, Any]]:
        records = await self.db.collection("document_storage_records").find_many(
            {
                "agency_id": agency_id,
                "related_entity_type": "document_workspace",
                "related_entity_id": document["id"],
            },
            sort=[("created_at", -1), ("id", -1)],
            limit=100,
        )
        result = []
        for index, item in enumerate(reversed(records), start=1):
            result.append(
                {
                    "id": item["id"],
                    "version": (item.get("audit_metadata") or {}).get(
                        "version_number", index
                    ),
                    "file_name": item.get("filename_original"),
                    "content_type": item.get("content_type"),
                    "size_bytes": item.get("size_bytes"),
                    "status": item.get("storage_status"),
                    "uploaded_at": item.get("created_at"),
                    "immutable": True,
                }
            )
        result.reverse()
        return result

    async def _visible_services(
        self, scope: dict[str, Any]
    ) -> list[dict[str, Any]]:
        rows = await self.db.collection("trip_service_items").find_many(
            {"agency_id": scope["agency_id"]},
            sort=[("updated_at", -1), ("id", -1)],
            limit=MAX_PORTAL_ITEMS,
        )
        return [
            self._trip_service(item)
            for item in rows
            if item.get("trip_id") in scope["trip_ids"]
            and (
                not item.get("passenger_ids")
                or bool(
                    _tokens(item.get("passenger_ids")).intersection(
                        scope["passenger_ids"]
                    )
                )
            )
        ]

    async def _portal_actions(
        self, scope: dict[str, Any]
    ) -> list[dict[str, Any]]:
        if scope["subject_type"] != "client":
            return []
        rows = await self.db.collection("portal_action_events").find_many(
            {
                "agency_id": scope["agency_id"],
                "client_id": scope["client_id"],
            },
            sort=[("created_at", -1), ("id", -1)],
            limit=MAX_PORTAL_ITEMS,
        )
        return [
            {
                "id": item["id"],
                "type": item.get("action_type"),
                "status": item.get("status"),
                "summary": item.get("summary"),
                "source_type": item.get("source_entity_type"),
                "source_id": item.get("source_entity_id"),
                "created_at": item.get("created_at"),
            }
            for item in rows
            if item.get("status") in {"received", "staff_review_required"}
        ]

    async def _threads(
        self,
        ctx: dict[str, Any],
        *,
        entity_type: str | None = None,
        entity_id: str | None = None,
    ) -> list[dict[str, Any]]:
        rows = await OperationalCollaborationService(self.db).portal_threads(
            ctx,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        rows.sort(key=_created_sort, reverse=True)
        return rows

    async def _audit(
        self,
        ctx: dict[str, Any],
        event_type: str,
        entity_type: str,
        entity_id: str,
        summary: str,
        details: dict[str, Any],
    ) -> None:
        await self.db.collection("audit_events").insert_one(
            AuditEvent(
                agency_id=self.agency_id(ctx),
                actor_user_id=self.actor_id(ctx),
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                summary=summary,
                metadata={
                    "portal_mapping_id": ctx["account"]["id"],
                    "portal_subject_type": ctx.get("subject_type"),
                    **details,
                },
            ).model_dump(mode="json")
        )

    async def _timeline_event(
        self,
        ctx: dict[str, Any],
        entity_type: str,
        entity_id: str,
        event_type: str,
        summary: str,
        *,
        idempotency_key: str,
    ) -> None:
        collaboration = OperationalCollaborationService(self.db)
        await collaboration.record_business_event(
            agency_id=self.agency_id(ctx),
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type,
            summary=summary,
            actor=collaboration.portal_actor(ctx),
            visibility="passenger"
            if ctx.get("subject_type") == "passenger"
            else "client",
            details={"portal_mapping_id": ctx["account"]["id"]},
            idempotency_key=idempotency_key,
            source_collection="portal_access_mappings",
            source_record_id=ctx["account"]["id"],
        )

    def _timeline_in_scope(
        self, scope: dict[str, Any], item: dict[str, Any]
    ) -> bool:
        entity_type = self._entity_type(item.get("entity_type"))
        entity_id = item.get("entity_id")
        allowed = {
            "client": {scope["client_id"]} if scope["client_id"] else set(),
            "passenger": scope["passenger_ids"],
            "request": scope["request_ids"],
            "offer": scope["offer_ids"],
            "trip": scope["trip_ids"],
            "booking": scope["booking_ids"] | scope["booking_workspace_ids"],
            "ticket": scope["ticket_ids"],
            "emd": scope["emd_ids"],
        }
        if entity_type in allowed and entity_id in allowed[entity_type]:
            return True
        linked_fields = {
            "linked_request": scope["request_ids"],
            "linked_offer": scope["offer_ids"],
            "linked_trip": scope["trip_ids"],
            "linked_booking": scope["booking_ids"] | scope["booking_workspace_ids"],
            "linked_ticket": scope["ticket_ids"],
            "linked_emd": scope["emd_ids"],
        }
        return any(item.get(field) in values for field, values in linked_fields.items())

    @staticmethod
    def _entity_type(value: Any) -> str:
        normalized = str(value or "").lower()
        aliases = {
            "travel_request": "request",
            "request_workspace": "request",
            "offer_workspace": "offer",
            "accepted_offer": "offer",
            "trip_dossier": "trip",
            "trip_workspace": "trip",
            "booking_record": "booking",
            "booking_workspace": "booking",
            "ticket_record": "ticket",
            "ticket_workspace": "ticket",
            "emd_record": "emd",
            "emd_workspace": "emd",
            "document_workspace": "document",
        }
        return aliases.get(normalized, normalized)

    @staticmethod
    def _trip_summary(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": item["id"],
            "trip_reference": item.get("trip_reference"),
            "title": item.get("trip_title"),
            "status": item.get("trip_status"),
            "type": item.get("trip_type"),
            "route_summary": item.get("route_summary"),
            "date_summary": item.get("date_summary"),
            "service_summary": item.get("service_summary"),
            "passenger_count": item.get("passenger_count"),
            "segment_count": item.get("segment_count"),
            "service_count": item.get("service_count"),
            "client_notes": item.get("client_visible_notes"),
            "updated_at": item.get("updated_at"),
        }

    @staticmethod
    def _trip_passenger(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": item["id"],
            "passenger_profile_id": item.get("passenger_profile_id"),
            "display_name": item.get("display_name"),
            "passenger_type": item.get("passenger_type"),
            "nationality": item.get("nationality"),
            "document_summary": item.get("document_summary"),
            "assistance_summary": item.get("assistance_summary"),
            "service_summary": item.get("service_summary"),
        }

    @staticmethod
    def _trip_segment(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": item["id"],
            "order": item.get("segment_order"),
            "origin": item.get("origin_airport_code"),
            "destination": item.get("destination_airport_code"),
            "departure_date": item.get("departure_date"),
            "departure_time": item.get("departure_time"),
            "arrival_date": item.get("arrival_date"),
            "arrival_time": item.get("arrival_time"),
            "marketing_airline": item.get("marketing_airline_code"),
            "operating_airline": item.get("operating_airline_code"),
            "flight_number": item.get("flight_number"),
            "cabin": item.get("cabin"),
            "booking_class": item.get("booking_class"),
            "status": item.get("segment_status"),
        }

    @staticmethod
    def _trip_service(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": item["id"],
            "trip_id": item.get("trip_id"),
            "service_code": item.get("service_code"),
            "service_label": item.get("service_label"),
            "service_family": item.get("service_family_code"),
            "passenger_ids": item.get("passenger_ids") or [],
            "segment_ids": item.get("segment_ids") or [],
            "status": item.get("status"),
        }

    @staticmethod
    def _accepted_snapshot(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": item["id"],
            "offer_version": item.get("offer_version"),
            "option_version": item.get("option_version"),
            "passengers": _safe_nested(item.get("confirmed_passengers_json") or []),
            "segments": _safe_nested(item.get("confirmed_segments_json") or []),
            "fare_bundle": _safe_nested(item.get("confirmed_fare_bundle_json") or {}),
            "pricing": _safe_nested(item.get("confirmed_pricing_json") or {}),
            "services": _safe_nested(item.get("confirmed_services_json") or {}),
            "pets": _safe_nested(item.get("confirmed_pets_json") or {}),
            "special_items": _safe_nested(
                item.get("confirmed_special_items_json") or {}
            ),
            "baggage": _safe_nested(item.get("baggage_snapshot_json") or {}),
            "total": _safe_nested(item.get("total_snapshot_json") or {}),
            "currency": item.get("currency"),
            "terms": _safe_nested(item.get("terms_snapshot_json") or {}),
            "accepted_at": item.get("created_at"),
            "immutable": True,
        }

    @staticmethod
    def _booking_summary(item: dict[str, Any]) -> dict[str, Any]:
        carriers = []
        for row in item.get("segments_json") or []:
            if not isinstance(row, dict):
                continue
            carrier = _value(
                row,
                "marketing_carrier",
                "marketing_airline_code",
                "airline_code",
            )
            if carrier and carrier not in carriers:
                carriers.append(carrier)
        return {
            "id": item["id"],
            "booking_reference": item.get("pnr_locator")
            or item.get("booking_workspace_id"),
            "record_locator": item.get("pnr_locator"),
            "status": item.get("booking_status"),
            "trip_id": item.get("trip_id"),
            "request_id": item.get("request_id"),
            "airlines": carriers,
            "confirmation_timestamp": item.get("confirmation_timestamp"),
            "warnings": [
                _safe_warning(value) for value in item.get("warnings_json") or []
            ],
            "updated_at": item.get("updated_at"),
        }

    @staticmethod
    def _ticket_summary(item: dict[str, Any]) -> dict[str, Any]:
        passenger = item.get("passenger_snapshot_json") or {}
        return {
            "id": item["id"],
            "booking_id": item.get("booking_record_id"),
            "trip_id": item.get("trip_id"),
            "passenger_id": item.get("passenger_id"),
            "passenger_name": _value(passenger, "display_name", "name"),
            "ticket_number": item.get("ticket_number"),
            "validating_carrier": _value(
                item, "validating_carrier", "validating_airline_code"
            ),
            "issue_date": item.get("issue_date"),
            "status": _value(item, "issue_status", "status"),
            "currency": item.get("currency"),
            "total_amount": item.get("total_amount"),
            "coupon_summary": item.get("coupon_summary"),
            "client_notes": item.get("client_visible_notes"),
        }

    @staticmethod
    def _ticket_coupon(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": item["id"],
            "coupon_number": item.get("coupon_number"),
            "status": item.get("coupon_status"),
            "origin": item.get("origin_airport_code"),
            "destination": item.get("destination_airport_code"),
            "marketing_carrier": item.get("marketing_carrier"),
            "operating_carrier": item.get("operating_carrier"),
            "flight_number": item.get("flight_number"),
            "departure_at": item.get("departure_at"),
            "arrival_at": item.get("arrival_at"),
            "cabin": item.get("cabin"),
            "booking_class": item.get("rbd"),
            "fare_basis": item.get("fare_basis"),
        }

    @staticmethod
    def _emd_summary(item: dict[str, Any]) -> dict[str, Any]:
        passenger = item.get("passenger_snapshot_json") or {}
        return {
            "id": item["id"],
            "booking_id": item.get("booking_record_id"),
            "trip_id": item.get("trip_id"),
            "ticket_id": item.get("ticket_record_id"),
            "passenger_id": item.get("passenger_id"),
            "passenger_name": _value(passenger, "display_name", "name"),
            "emd_number": item.get("emd_number"),
            "type": item.get("emd_type"),
            "status": _value(item, "issue_status", "status"),
            "service_code": _value(
                item, "service_code", "service_key", "rfisc_code"
            ),
            "service_name": _value(
                item, "service_name", "service_label", "reason_for_issuance"
            ),
            "rfic": _value(item, "rfic_code", "reason_for_issuance_code"),
            "rfisc": _value(item, "rfisc_code", "reason_for_issuance_subcode"),
            "issue_date": item.get("issue_date"),
            "currency": item.get("currency"),
            "total_amount": _value(item, "total_amount", "amount"),
            "client_notes": item.get("client_visible_notes"),
        }

    @staticmethod
    def _emd_coupon(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": item["id"],
            "coupon_number": item.get("coupon_number"),
            "status": item.get("coupon_status"),
            "service_key": item.get("service_key"),
            "service_label": item.get("service_label"),
            "service_category": item.get("service_category"),
            "segment_id": item.get("segment_id"),
            "ticket_coupon_id": item.get("ticket_coupon_id"),
        }

    @staticmethod
    def _document_summary(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": item["id"],
            "document_reference": item.get("document_reference"),
            "title": item.get("document_title")
            or item.get("document_description")
            or str(item.get("document_type") or "Document").replace("_", " ").title(),
            "description": item.get("document_description"),
            "type": item.get("document_type"),
            "category": item.get("document_category"),
            "status": item.get("document_status"),
            "passenger_id": item.get("passenger_id"),
            "passenger_name": item.get("passenger_name"),
            "required_for_travel": item.get("required_for_travel"),
            "required_by_airline": item.get("required_by_airline"),
            "required_by_airport": item.get("required_by_airport"),
            "required_by_authority": item.get("required_by_authority"),
            "deadline": item.get("requirement_deadline"),
            "received_status": item.get("received_status"),
            "verification_status": item.get("verification_status"),
            "valid_from": item.get("validity_start_date"),
            "valid_until": item.get("validity_end_date"),
            "language": item.get("language"),
            "file_name": item.get("file_name"),
            "file_type": item.get("file_type"),
            "file_size": item.get("file_size"),
            "rejection_reason": item.get("rejection_reason"),
            "updated_at": item.get("updated_at"),
        }

    @staticmethod
    def _request_summary(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": item["id"],
            "request_reference": item.get("request_reference"),
            "title": item.get("title"),
            "status": item.get("status"),
            "priority": item.get("priority"),
            "requested_departure_date": item.get("requested_departure_date"),
            "requested_return_date": item.get("requested_return_date"),
            "route_summary": item.get("route_summary"),
            "service_summary": item.get("service_summary"),
            "client_notes": item.get("client_notes"),
            "client_visible_notes": item.get("client_visible_notes"),
            "passenger_count": item.get("passenger_count"),
            "service_count": item.get("service_count"),
            "editable": item.get("status") in SAFE_REQUEST_EDIT_STATUSES,
            "cancellable": item.get("status") in SAFE_REQUEST_CANCEL_STATUSES,
            "updated_at": item.get("updated_at"),
        }

    @staticmethod
    def _profile_projection(subject_type: str, item: dict[str, Any]) -> dict[str, Any]:
        if subject_type == "client":
            fields = [
                "id",
                "display_name",
                "legal_name",
                "primary_email",
                "primary_phone",
                "country",
                "city",
                "address_line_1",
                "address_line_2",
                "postal_code",
                "preferred_language",
                "default_currency",
                "marketing_consent",
                "data_processing_consent",
                "status",
            ]
        else:
            fields = [
                "id",
                "first_name",
                "middle_name",
                "last_name",
                "display_name",
                "date_of_birth",
                "passenger_type",
                "gender",
                "nationality",
                "residence_country",
                "primary_language",
                "passport_country",
                "passport_expiry",
                "known_assistance_needs",
                "meal_preferences",
                "seating_preferences",
                "baggage_preferences",
                "emergency_contact",
                "loyalty_numbers",
                "status",
            ]
        return {field: item.get(field) for field in fields}

    @staticmethod
    def _invoice_summary(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": item["id"],
            "invoice_number": item.get("invoice_number"),
            "trip_id": item.get("trip_id"),
            "booking_id": item.get("booking_id"),
            "status": item.get("status"),
            "currency": item.get("currency"),
            "subtotal_amount": item.get("subtotal_amount"),
            "tax_amount": item.get("tax_amount"),
            "total_amount": item.get("total_amount"),
            "paid_amount": item.get("paid_amount"),
            "due_amount": item.get("due_amount"),
            "issue_date": item.get("issue_date"),
            "due_date": item.get("due_date"),
            "client_notes": item.get("client_visible_notes"),
            "issued_at": item.get("issued_at"),
            "paid_at": item.get("paid_at"),
        }

    @staticmethod
    def _invoice_line(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": item["id"],
            "type": item.get("line_type"),
            "description": item.get("description"),
            "service_code": item.get("service_code"),
            "quantity": item.get("quantity"),
            "unit_amount": item.get("unit_amount"),
            "total_amount": item.get("total_amount"),
            "currency": item.get("currency"),
            "status": item.get("status"),
        }

    @staticmethod
    def _payment_summary(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": item["id"],
            "invoice_id": item.get("invoice_id"),
            "booking_id": item.get("booking_id"),
            "status": item.get("status"),
            "method": item.get("method"),
            "amount": item.get("amount"),
            "currency": item.get("currency"),
            "received_at": item.get("received_at"),
        }

    @staticmethod
    def _credit_summary(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": item["id"],
            "credit_note_number": item.get("credit_note_number"),
            "invoice_id": item.get("invoice_id"),
            "trip_id": item.get("trip_id"),
            "booking_id": item.get("booking_id"),
            "status": item.get("status"),
            "reason": item.get("reason"),
            "amount": item.get("total_amount"),
            "currency": item.get("currency"),
            "issued_at": item.get("issued_at"),
        }

    @staticmethod
    def _refund_summary(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": item["id"],
            "reference": item.get("refund_reference"),
            "booking_id": item.get("booking_id"),
            "ticket_id": item.get("ticket_id"),
            "emd_id": item.get("emd_id"),
            "amount": item.get("amount"),
            "currency": item.get("currency"),
            "reason": item.get("reason"),
            "status": item.get("status"),
            "recorded_at": item.get("recorded_at"),
        }

    @staticmethod
    def _exchange_summary(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": item["id"],
            "reference": _value(
                item, "exchange_reference", "operation_reference", "reference"
            ),
            "booking_id": item.get("booking_id"),
            "ticket_id": item.get("ticket_id"),
            "emd_id": item.get("emd_id"),
            "status": item.get("status"),
            "currency": item.get("currency"),
            "amount": _value(
                item, "total_amount", "additional_collection_amount", "amount"
            ),
            "created_at": item.get("created_at"),
        }

    @staticmethod
    def _single_currency(values: list[Any]) -> str | None:
        currencies = sorted({str(value) for value in values if value})
        return currencies[0] if len(currencies) == 1 else None
