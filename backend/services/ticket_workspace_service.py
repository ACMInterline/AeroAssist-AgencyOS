from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from database import Database
from models import (
    TicketDocumentStatus,
    TicketWorkspaceCouponStatus,
    TicketWorkspace,
    TicketWorkspaceCreate,
    TicketWorkspaceStatus,
    TicketWorkspaceUpdate,
    new_id,
)


PHASE_LABEL = "phase_56_3_journey_comparison_client_presentation_foundation"
TICKET_WORKSPACE_COLLECTION = "ticket_workspaces"
TICKET_WORKSPACE_STATUSES = [
    TicketWorkspaceStatus.DRAFT.value,
    TicketWorkspaceStatus.REVIEW.value,
    TicketWorkspaceStatus.READY.value,
    TicketWorkspaceStatus.ARCHIVED.value,
]
TICKET_DOCUMENT_STATUSES = [
    TicketDocumentStatus.DRAFT_METADATA.value,
    TicketDocumentStatus.ISSUED.value,
    TicketDocumentStatus.VOIDED.value,
    TicketDocumentStatus.EXCHANGED.value,
    TicketDocumentStatus.REFUNDED.value,
    TicketDocumentStatus.PARTIALLY_REFUNDED.value,
    TicketDocumentStatus.CANCELLED.value,
    TicketDocumentStatus.UNKNOWN.value,
]
TICKET_COUPON_STATUSES = [
    TicketWorkspaceCouponStatus.OPEN_FOR_USE.value,
    TicketWorkspaceCouponStatus.AIRPORT_CONTROL.value,
    TicketWorkspaceCouponStatus.CHECKED_IN.value,
    TicketWorkspaceCouponStatus.FLOWN.value,
    TicketWorkspaceCouponStatus.CLOSED.value,
    TicketWorkspaceCouponStatus.SUSPENDED.value,
    TicketWorkspaceCouponStatus.VOID.value,
    TicketWorkspaceCouponStatus.EXCHANGED.value,
    TicketWorkspaceCouponStatus.REFUNDED.value,
    TicketWorkspaceCouponStatus.UNKNOWN.value,
]


class TicketWorkspaceError(ValueError):
    pass


class TicketWorkspaceService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_platform_tickets(
        self,
        *,
        agency_id: str | None = None,
        ticket_status: str | None = None,
        ticket_document_status: str | None = None,
        validating_carrier: str | None = None,
        issue_date: date | str | None = None,
        passenger: str | None = None,
        booking_reference: str | None = None,
        currency: str | None = None,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if ticket_status:
            filters["ticket_status"] = ticket_status
        if ticket_document_status:
            filters["ticket_document_status"] = ticket_document_status
        if validating_carrier:
            filters["validating_carrier"] = validating_carrier
        if passenger:
            filters["passenger_id"] = passenger
        if booking_reference:
            filters["booking_reference"] = booking_reference
        if currency:
            filters["currency"] = currency

        items = await self.db.collection(TICKET_WORKSPACE_COLLECTION).find_many(filters or None)
        if not include_archived:
            items = [
                item
                for item in items
                if not item.get("deleted_at")
                and item.get("ticket_status", TicketWorkspaceStatus.DRAFT.value) != TicketWorkspaceStatus.ARCHIVED.value
            ]
        if issue_date:
            target = self._parse_date(issue_date)
            items = [item for item in items if self._date_matches(item.get("issue_date"), target)]

        items.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._platform_projection(item) for item in items]

    async def list_agency_tickets(
        self,
        agency_id: str,
        *,
        ticket_status: str | None = None,
        ticket_document_status: str | None = None,
        validating_carrier: str | None = None,
        issue_date: date | str | None = None,
        passenger: str | None = None,
        booking_reference: str | None = None,
        currency: str | None = None,
    ) -> list[dict[str, Any]]:
        items = await self.list_platform_tickets(
            agency_id=agency_id,
            ticket_status=ticket_status,
            ticket_document_status=ticket_document_status,
            validating_carrier=validating_carrier,
            issue_date=issue_date,
            passenger=passenger,
            booking_reference=booking_reference,
            currency=currency,
        )
        return [self._agency_projection(item) for item in items if item.get("agency_id") == agency_id]

    async def platform_response(
        self,
        *,
        agency_id: str | None = None,
        ticket_status: str | None = None,
        ticket_document_status: str | None = None,
        validating_carrier: str | None = None,
        issue_date: date | str | None = None,
        passenger: str | None = None,
        booking_reference: str | None = None,
        currency: str | None = None,
        include_archived: bool = False,
    ) -> dict[str, Any]:
        items = await self.list_platform_tickets(
            agency_id=agency_id,
            ticket_status=ticket_status,
            ticket_document_status=ticket_document_status,
            validating_carrier=validating_carrier,
            issue_date=issue_date,
            passenger=passenger,
            booking_reference=booking_reference,
            currency=currency,
            include_archived=include_archived,
        )
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "ticket_workspace_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Ticket workspaces are metadata only. They separate whole-ticket document status from per-coupon travel or usage status and store inert fare construction, pricing unit, fare component, tax, commission, and payment references. They do not issue, reissue, void, refund, exchange, process payments, recalculate fares, connect to GDS or NDC, call airline APIs, validate coupons, run background workers, or integrate external providers.",
            **self.safety_flags(),
        }

    async def agency_response(
        self,
        agency_id: str,
        *,
        ticket_status: str | None = None,
        ticket_document_status: str | None = None,
        validating_carrier: str | None = None,
        issue_date: date | str | None = None,
        passenger: str | None = None,
        booking_reference: str | None = None,
        currency: str | None = None,
    ) -> dict[str, Any]:
        items = await self.list_agency_tickets(
            agency_id,
            ticket_status=ticket_status,
            ticket_document_status=ticket_document_status,
            validating_carrier=validating_carrier,
            issue_date=issue_date,
            passenger=passenger,
            booking_reference=booking_reference,
            currency=currency,
        )
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "ticket_workspace_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            "notice": "Agency ticket workspace views are read-only metadata. Whole-ticket document status, per-coupon status, fare construction, pricing unit, fare component, tax, commission, and payment references are informational only. No issuance, reissue, void, refund, exchange, payment, GDS/NDC, airline API, fare recalculation, coupon validation, worker, or provider action is available.",
            **self.safety_flags(),
        }

    async def platform_summary(self) -> dict[str, Any]:
        items = await self.list_platform_tickets()
        return {
            "phase": PHASE_LABEL,
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        items = await self.list_agency_tickets(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def get_platform_ticket(self, ticket_workspace_id: str) -> dict[str, Any]:
        item = await self._require_ticket(ticket_workspace_id)
        return await self._platform_projection(item)

    async def get_agency_ticket(self, agency_id: str, ticket_workspace_id: str) -> dict[str, Any]:
        item = await self._require_ticket(ticket_workspace_id, agency_id=agency_id)
        return self._agency_projection(await self._platform_projection(item))

    async def create_ticket(self, payload: TicketWorkspaceCreate, user: dict) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        if data.get("ticket_status"):
            self._validate_status(data["ticket_status"])
        if data.get("ticket_document_status"):
            self._validate_document_status(data["ticket_document_status"])
        self._validate_coupon_details(data.get("coupon_details") or [])
        data.setdefault("ticket_reference", self._ticket_reference())
        data["created_by"] = user.get("id")
        data["updated_by"] = user.get("id")
        data.update(self.safety_flags())
        ticket = TicketWorkspace(**data)
        created = await self.db.collection(TICKET_WORKSPACE_COLLECTION).insert_one(ticket.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "ticket_workspace": await self._platform_projection(created),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def update_ticket(self, ticket_workspace_id: str, payload: TicketWorkspaceUpdate, user: dict) -> dict[str, Any]:
        existing = await self._require_ticket(ticket_workspace_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        if updates.get("ticket_status"):
            self._validate_status(updates["ticket_status"])
        if updates.get("ticket_document_status"):
            self._validate_document_status(updates["ticket_document_status"])
        if "coupon_details" in updates:
            self._validate_coupon_details(updates.get("coupon_details") or [])
        updates["updated_by"] = user.get("id")
        updates.update(self.safety_flags())
        updated = await self.db.collection(TICKET_WORKSPACE_COLLECTION).update_one({"id": existing["id"]}, updates)
        if not updated:
            raise TicketWorkspaceError("Ticket workspace metadata could not be updated.")
        return {
            "phase": PHASE_LABEL,
            "ticket_workspace": await self._platform_projection(updated),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def delete_ticket(self, ticket_workspace_id: str, user: dict) -> dict[str, Any]:
        existing = await self._require_ticket(ticket_workspace_id)
        updated = await self.db.collection(TICKET_WORKSPACE_COLLECTION).update_one(
            {"id": existing["id"]},
            {
                "ticket_status": TicketWorkspaceStatus.ARCHIVED.value,
                "deleted_at": self._now(),
                "deleted_by": user.get("id"),
                "updated_by": user.get("id"),
                **self.safety_flags(),
            },
        )
        if not updated:
            raise TicketWorkspaceError("Ticket workspace metadata could not be archived.")
        return {
            "phase": PHASE_LABEL,
            "ticket_workspace": await self._platform_projection(updated),
            "archived": True,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        by_status = {status: 0 for status in TICKET_WORKSPACE_STATUSES}
        by_document_status = {status: 0 for status in TICKET_DOCUMENT_STATUSES}
        by_coupon_status = {status: 0 for status in TICKET_COUPON_STATUSES}
        by_type: dict[str, int] = {}
        by_validating_carrier: dict[str, int] = {}
        by_currency: dict[str, int] = {}
        agency_ids: set[str] = set()
        operational_workspace_ids: set[str] = set()
        trip_workspace_ids: set[str] = set()
        offer_workspace_ids: set[str] = set()
        booking_workspace_ids: set[str] = set()
        passenger_ids: set[str] = set()
        linked_counts = {
            "flight_workspace_count": 0,
            "linked_emd_count": 0,
            "linked_document_count": 0,
            "coupon_detail_count": 0,
            "exchange_reference_count": 0,
            "refund_reference_count": 0,
            "void_reference_count": 0,
            "pricing_unit_count": 0,
            "fare_component_count": 0,
            "tax_breakdown_count": 0,
        }
        fare_amount_total = 0.0
        taxes_amount_total = 0.0
        total_amount_total = 0.0
        fare_calculation_nuc_total = 0.0
        equivalent_fare_paid_total = 0.0
        for item in items:
            status = item.get("ticket_status") or TicketWorkspaceStatus.DRAFT.value
            by_status[status] = by_status.get(status, 0) + 1
            document_status = item.get("ticket_document_status") or TicketDocumentStatus.DRAFT_METADATA.value
            by_document_status[document_status] = by_document_status.get(document_status, 0) + 1
            for coupon in item.get("coupon_details") or []:
                if isinstance(coupon, dict):
                    coupon_status = coupon.get("coupon_status") or TicketWorkspaceCouponStatus.UNKNOWN.value
                    by_coupon_status[coupon_status] = by_coupon_status.get(coupon_status, 0) + 1
            self._count_value(by_type, item.get("ticket_type"))
            self._count_value(by_validating_carrier, item.get("validating_carrier"))
            self._count_value(by_currency, item.get("currency"))
            self._add_if_present(agency_ids, item.get("agency_id"))
            self._add_if_present(operational_workspace_ids, item.get("operational_workspace_id"))
            self._add_if_present(trip_workspace_ids, item.get("trip_workspace_id"))
            self._add_if_present(offer_workspace_ids, item.get("offer_workspace_id"))
            self._add_if_present(booking_workspace_ids, item.get("booking_workspace_id"))
            self._add_if_present(passenger_ids, item.get("passenger_id"))
            linked_counts["flight_workspace_count"] += self._list_count(item.get("flight_workspace_ids"))
            linked_counts["linked_emd_count"] += self._list_count(item.get("linked_emd_ids"))
            linked_counts["linked_document_count"] += self._list_count(item.get("linked_document_ids"))
            linked_counts["coupon_detail_count"] += self._list_count(item.get("coupon_details"))
            linked_counts["exchange_reference_count"] += self._list_count(item.get("exchange_reference_ids"))
            linked_counts["refund_reference_count"] += self._list_count(item.get("refund_reference_ids"))
            linked_counts["void_reference_count"] += self._list_count(item.get("void_reference_ids"))
            linked_counts["pricing_unit_count"] += self._list_count(item.get("pricing_units"))
            linked_counts["fare_component_count"] += self._list_count(item.get("fare_components"))
            linked_counts["tax_breakdown_count"] += self._list_count(item.get("tax_breakdown"))
            fare_amount_total += self._amount(item.get("fare_amount"))
            taxes_amount_total += self._amount(item.get("taxes_amount"))
            total_amount_total += self._amount(item.get("total_amount"))
            fare_calculation_nuc_total += self._amount(item.get("fare_calculation_nuc_total"))
            equivalent_fare_paid_total += self._amount(item.get("equivalent_fare_paid"))
        return {
            "total_count": len(items),
            "by_status": by_status,
            "by_document_status": by_document_status,
            "by_coupon_status": by_coupon_status,
            "by_type": by_type,
            "by_validating_carrier": by_validating_carrier,
            "by_currency": by_currency,
            "agency_count": len(agency_ids),
            "operational_workspace_count": len(operational_workspace_ids),
            "trip_workspace_count": len(trip_workspace_ids),
            "offer_workspace_count": len(offer_workspace_ids),
            "booking_workspace_count": len(booking_workspace_ids),
            "passenger_count": len(passenger_ids),
            "fare_amount_total": fare_amount_total,
            "taxes_amount_total": taxes_amount_total,
            "total_amount_total": total_amount_total,
            "fare_calculation_nuc_total": fare_calculation_nuc_total,
            "equivalent_fare_paid_total": equivalent_fare_paid_total,
            **linked_counts,
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "status": TICKET_WORKSPACE_STATUSES,
            "ticket_document_status": TICKET_DOCUMENT_STATUSES,
            "coupon_status": TICKET_COUPON_STATUSES,
            "validating_carrier": "exact metadata match",
            "issue_date": "ISO date metadata match",
            "passenger": "passenger_id metadata match",
            "booking_reference": "exact metadata match",
            "currency": "exact metadata match",
            "pricing_units": "metadata-only pricing unit list",
            "fare_components": "metadata-only fare component list",
            "tax_breakdown": "metadata-only tax breakdown list",
            "metadata_only": True,
        }

    async def _platform_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        projected["ticket_display_name"] = self._ticket_display_name(projected)
        agency = await self._agency_context(projected.get("agency_id"))
        projected["agency"] = agency
        projected["agency_name"] = agency.get("agency_name")
        projected["operational_workspace"] = await self._operational_workspace_context(projected.get("operational_workspace_id"))
        projected["trip_workspace"] = await self._trip_workspace_context(projected.get("agency_id"), projected.get("trip_workspace_id"))
        projected["offer_workspace"] = await self._offer_workspace_context(projected.get("agency_id"), projected.get("offer_workspace_id"))
        projected["booking_workspace"] = await self._booking_workspace_context(projected.get("agency_id"), projected.get("booking_workspace_id"))
        projected["passenger"] = await self._passenger_context(projected.get("agency_id"), projected.get("passenger_id"))
        projected["flight_workspaces"] = [
            await self._flight_workspace_context(projected.get("agency_id"), flight_workspace_id)
            for flight_workspace_id in projected.get("flight_workspace_ids") or []
        ]
        projected["linked_emds"] = [
            await self._emd_context(projected.get("agency_id"), emd_id)
            for emd_id in projected.get("linked_emd_ids") or []
        ]
        projected["linked_documents"] = [
            await self._document_context(projected.get("agency_id"), document_id)
            for document_id in projected.get("linked_document_ids") or []
        ]
        projected["read_only"] = False
        projected.update(self.safety_flags())
        return projected

    def _agency_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        projected["read_only"] = True
        projected.update(self.safety_flags())
        return projected

    async def _require_ticket(self, ticket_workspace_id: str, *, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": ticket_workspace_id}
        if agency_id:
            filters["agency_id"] = agency_id
        item = await self.db.collection(TICKET_WORKSPACE_COLLECTION).find_one(filters)
        if not item:
            alt_filters = {"ticket_reference": ticket_workspace_id}
            if agency_id:
                alt_filters["agency_id"] = agency_id
            item = await self.db.collection(TICKET_WORKSPACE_COLLECTION).find_one(alt_filters)
        if not item and not agency_id:
            item = await self.db.collection(TICKET_WORKSPACE_COLLECTION).find_one({"ticket_number": ticket_workspace_id})
        if not item:
            raise TicketWorkspaceError("Ticket workspace metadata was not found.")
        return item

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
        item = await self.db.collection("operational_travel_workspaces").find_one({"id": workspace_id})
        if not item:
            item = await self.db.collection("operational_travel_workspaces").find_one({"workspace_reference": workspace_id})
        if not item:
            return {"operational_workspace_id": workspace_id, "workspace_reference": workspace_id, "workspace_title": workspace_id, "metadata_only": True}
        return {
            "operational_workspace_id": item.get("id"),
            "workspace_reference": item.get("workspace_reference"),
            "workspace_title": item.get("workspace_title"),
            "workspace_status": item.get("workspace_status"),
            "metadata_only": True,
        }

    async def _trip_workspace_context(self, agency_id: str | None, trip_workspace_id: str | None) -> dict[str, Any]:
        item = await self._lookup_agency_record("trip_workspaces", agency_id, trip_workspace_id, ["trip_reference"])
        if not item:
            item = await self._lookup_agency_record("trip_dossiers", agency_id, trip_workspace_id, ["trip_reference"])
        return self._compact_context("trip_workspace_id", trip_workspace_id, item, ["trip_reference", "trip_title", "destination_city"], "trip_status")

    async def _offer_workspace_context(self, agency_id: str | None, offer_workspace_id: str | None) -> dict[str, Any]:
        item = await self._lookup_agency_record("offer_workspaces_v2", agency_id, offer_workspace_id, ["offer_reference"])
        if not item:
            item = await self._lookup_agency_record("offer_workspaces", agency_id, offer_workspace_id, ["workspace_reference", "offer_reference"])
        return self._compact_context("offer_workspace_id", offer_workspace_id, item, ["offer_reference", "offer_title", "title"], "offer_status")

    async def _booking_workspace_context(self, agency_id: str | None, booking_workspace_id: str | None) -> dict[str, Any]:
        item = await self._lookup_agency_record("booking_workspaces", agency_id, booking_workspace_id, ["booking_reference", "workspace_number"])
        return self._compact_context("booking_workspace_id", booking_workspace_id, item, ["booking_reference", "workspace_number", "booking_summary", "title"], "booking_status")

    async def _passenger_context(self, agency_id: str | None, passenger_id: str | None) -> dict[str, Any]:
        item = await self._lookup_agency_record("passenger_workspaces", agency_id, passenger_id, ["passenger_reference"])
        if not item:
            item = await self._lookup_agency_record("passengers", agency_id, passenger_id, ["passenger_reference"])
        return self._compact_context("passenger_id", passenger_id, item, ["passenger_reference", "preferred_name", "first_name", "last_name"], "passenger_status")

    async def _flight_workspace_context(self, agency_id: str | None, flight_workspace_id: str | None) -> dict[str, Any]:
        item = await self._lookup_agency_record("flight_workspaces", agency_id, flight_workspace_id, ["flight_reference"])
        return self._compact_context("flight_workspace_id", flight_workspace_id, item, ["flight_reference", "flight_number", "airline_code"], "flight_status")

    async def _emd_context(self, agency_id: str | None, emd_id: str | None) -> dict[str, Any]:
        item = await self._lookup_agency_record("emd_records", agency_id, emd_id, ["emd_number", "document_number"])
        if not item:
            item = await self._lookup_agency_record("emds", agency_id, emd_id, ["emd_number", "document_number"])
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
            "status": item.get(status_key) or item.get("status"),
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

    def _ticket_display_name(self, item: dict[str, Any]) -> str:
        if item.get("ticket_number"):
            return str(item["ticket_number"])
        if item.get("ticket_reference"):
            return str(item["ticket_reference"])
        if item.get("passenger_name"):
            return f"Ticket for {item['passenger_name']}"
        return item.get("id") or "Ticket workspace"

    def _date_matches(self, value: date | str | None, target: date) -> bool:
        if not value:
            return False
        if isinstance(value, date):
            return value == target
        if isinstance(value, str):
            return value[:10] == target.isoformat()
        return False

    def _parse_date(self, value: date | str | None) -> date:
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            return date.fromisoformat(value[:10])
        raise ValueError("An issue date filter requires an ISO date.")

    def _validate_status(self, value: str) -> None:
        if value not in TICKET_WORKSPACE_STATUSES:
            raise TicketWorkspaceError("Unsupported ticket workspace status.")

    def _validate_document_status(self, value: str) -> None:
        if value not in TICKET_DOCUMENT_STATUSES:
            raise TicketWorkspaceError("Unsupported ticket document status.")

    def _validate_coupon_details(self, value: Any) -> None:
        if not isinstance(value, list):
            raise TicketWorkspaceError("Coupon details must be a metadata-only list.")
        for coupon in value:
            if not isinstance(coupon, dict):
                raise TicketWorkspaceError("Coupon detail entries must be metadata-only objects.")
            coupon_status = coupon.get("coupon_status") or TicketWorkspaceCouponStatus.UNKNOWN.value
            if coupon_status not in TICKET_COUPON_STATUSES:
                raise TicketWorkspaceError("Unsupported coupon status.")

    def _ticket_reference(self) -> str:
        return f"TKTW-{new_id()[:8].upper()}"

    def _count_value(self, target: dict[str, int], value: Any) -> None:
        if value:
            target[str(value)] = target.get(str(value), 0) + 1

    def _add_if_present(self, target: set[str], value: Any) -> None:
        if value:
            target.add(str(value))

    def _list_count(self, value: Any) -> int:
        if not value:
            return 0
        if isinstance(value, list):
            return len(value)
        return 1

    def _amount(self, value: Any) -> float:
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

    def _sort_text(self, value: Any) -> str:
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value or "")

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "ticket_workspace_metadata_only": True,
            "ticket_issuance_disabled": True,
            "ticket_reissue_disabled": True,
            "voiding_disabled": True,
            "void_workflow_disabled": True,
            "refunds_disabled": True,
            "refund_workflow_disabled": True,
            "exchanges_disabled": True,
            "exchange_workflow_disabled": True,
            "payment_processing_disabled": True,
            "gds_connectivity_disabled": True,
            "ndc_connectivity_disabled": True,
            "airline_apis_disabled": True,
            "airline_api_calls_disabled": True,
            "fare_calculation_disabled": True,
            "fare_recalculation_disabled": True,
            "automated_ticket_validation_disabled": True,
            "coupon_validation_disabled": True,
            "background_workers_disabled": True,
            "external_integrations_disabled": True,
            "external_api_calls_disabled": True,
            "automation_disabled": True,
        }
