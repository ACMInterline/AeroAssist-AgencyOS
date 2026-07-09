from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from database import Database
from models import (
    EmdWorkspace,
    EmdWorkspaceCouponStatus,
    EmdWorkspaceCreate,
    EmdWorkspaceDocumentStatus,
    EmdWorkspaceStatus,
    EmdWorkspaceUpdate,
    new_id,
)


PHASE_LABEL = "phase_51_0_operational_intelligence_pipeline_consolidation_foundation"
EMD_WORKSPACE_COLLECTION = "emd_workspaces"
EMD_WORKSPACE_STATUSES = [
    EmdWorkspaceStatus.DRAFT.value,
    EmdWorkspaceStatus.REVIEW.value,
    EmdWorkspaceStatus.READY.value,
    EmdWorkspaceStatus.ARCHIVED.value,
]
EMD_DOCUMENT_STATUSES = [
    EmdWorkspaceDocumentStatus.DRAFT_METADATA.value,
    EmdWorkspaceDocumentStatus.ISSUED.value,
    EmdWorkspaceDocumentStatus.VOIDED.value,
    EmdWorkspaceDocumentStatus.EXCHANGED.value,
    EmdWorkspaceDocumentStatus.REFUNDED.value,
    EmdWorkspaceDocumentStatus.PARTIALLY_REFUNDED.value,
    EmdWorkspaceDocumentStatus.CANCELLED.value,
    EmdWorkspaceDocumentStatus.UNKNOWN.value,
]
EMD_COUPON_STATUSES = [
    EmdWorkspaceCouponStatus.OPEN_FOR_USE.value,
    EmdWorkspaceCouponStatus.AIRPORT_CONTROL.value,
    EmdWorkspaceCouponStatus.CHECKED_IN.value,
    EmdWorkspaceCouponStatus.FLOWN.value,
    EmdWorkspaceCouponStatus.USED.value,
    EmdWorkspaceCouponStatus.CLOSED.value,
    EmdWorkspaceCouponStatus.SUSPENDED.value,
    EmdWorkspaceCouponStatus.VOID.value,
    EmdWorkspaceCouponStatus.EXCHANGED.value,
    EmdWorkspaceCouponStatus.REFUNDED.value,
    EmdWorkspaceCouponStatus.UNKNOWN.value,
]


class EmdWorkspaceError(ValueError):
    pass


class EmdWorkspaceService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_platform_emds(
        self,
        *,
        agency_id: str | None = None,
        emd_status: str | None = None,
        emd_type: str | None = None,
        emd_a_or_s: str | None = None,
        validating_carrier: str | None = None,
        passenger: str | None = None,
        rfic: str | None = None,
        rfisc: str | None = None,
        service_category: str | None = None,
        issue_date: date | str | None = None,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if emd_status:
            filters["emd_status"] = emd_status
        if emd_type:
            filters["emd_type"] = emd_type
        if emd_a_or_s:
            filters["emd_a_or_s"] = emd_a_or_s
        if validating_carrier:
            filters["validating_carrier"] = validating_carrier
        if passenger:
            filters["passenger_id"] = passenger
        if rfic:
            filters["rfic"] = rfic
        if rfisc:
            filters["rfisc"] = rfisc
        if service_category:
            filters["service_category"] = service_category

        items = await self.db.collection(EMD_WORKSPACE_COLLECTION).find_many(filters or None)
        if not include_archived:
            items = [
                item
                for item in items
                if not item.get("deleted_at")
                and item.get("emd_status", EmdWorkspaceStatus.DRAFT.value) != EmdWorkspaceStatus.ARCHIVED.value
            ]
        if issue_date:
            target = self._parse_date(issue_date)
            items = [item for item in items if self._date_matches(item.get("issue_date"), target)]

        items.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._platform_projection(item) for item in items]

    async def list_agency_emds(
        self,
        agency_id: str,
        *,
        emd_status: str | None = None,
        emd_type: str | None = None,
        emd_a_or_s: str | None = None,
        validating_carrier: str | None = None,
        passenger: str | None = None,
        rfic: str | None = None,
        rfisc: str | None = None,
        service_category: str | None = None,
        issue_date: date | str | None = None,
    ) -> list[dict[str, Any]]:
        items = await self.list_platform_emds(
            agency_id=agency_id,
            emd_status=emd_status,
            emd_type=emd_type,
            emd_a_or_s=emd_a_or_s,
            validating_carrier=validating_carrier,
            passenger=passenger,
            rfic=rfic,
            rfisc=rfisc,
            service_category=service_category,
            issue_date=issue_date,
        )
        return [self._agency_projection(item) for item in items if item.get("agency_id") == agency_id]

    async def platform_response(
        self,
        *,
        agency_id: str | None = None,
        emd_status: str | None = None,
        emd_type: str | None = None,
        emd_a_or_s: str | None = None,
        validating_carrier: str | None = None,
        passenger: str | None = None,
        rfic: str | None = None,
        rfisc: str | None = None,
        service_category: str | None = None,
        issue_date: date | str | None = None,
        include_archived: bool = False,
    ) -> dict[str, Any]:
        items = await self.list_platform_emds(
            agency_id=agency_id,
            emd_status=emd_status,
            emd_type=emd_type,
            emd_a_or_s=emd_a_or_s,
            validating_carrier=validating_carrier,
            passenger=passenger,
            rfic=rfic,
            rfisc=rfisc,
            service_category=service_category,
            issue_date=issue_date,
            include_archived=include_archived,
        )
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "emd_workspace_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "EMD workspaces are metadata only. They link operational EMD records to tickets, coupons, flights, SSR/OSI references, RFIC/RFISC mechanics, service metadata, and payment notes without EMD issuance, exchange, refund, voiding, validation engines, provider calls, or duplicate EMD architecture.",
            **self.safety_flags(),
        }

    async def agency_response(
        self,
        agency_id: str,
        *,
        emd_status: str | None = None,
        emd_type: str | None = None,
        emd_a_or_s: str | None = None,
        validating_carrier: str | None = None,
        passenger: str | None = None,
        rfic: str | None = None,
        rfisc: str | None = None,
        service_category: str | None = None,
        issue_date: date | str | None = None,
    ) -> dict[str, Any]:
        items = await self.list_agency_emds(
            agency_id,
            emd_status=emd_status,
            emd_type=emd_type,
            emd_a_or_s=emd_a_or_s,
            validating_carrier=validating_carrier,
            passenger=passenger,
            rfic=rfic,
            rfisc=rfisc,
            service_category=service_category,
            issue_date=issue_date,
        )
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "emd_workspace_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            "notice": "Agency EMD workspace views are read-only metadata. No EMD issuance, exchange, refund, voiding, RFIC/RFISC validation, SSR/OSI transmission, payment processing, provider call, or automation is available.",
            **self.safety_flags(),
        }

    async def platform_summary(self) -> dict[str, Any]:
        items = await self.list_platform_emds()
        return {
            "phase": PHASE_LABEL,
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        items = await self.list_agency_emds(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def get_platform_emd(self, emd_workspace_id: str) -> dict[str, Any]:
        item = await self._require_emd(emd_workspace_id)
        return await self._platform_projection(item)

    async def get_agency_emd(self, agency_id: str, emd_workspace_id: str) -> dict[str, Any]:
        item = await self._require_emd(emd_workspace_id, agency_id=agency_id)
        return self._agency_projection(await self._platform_projection(item))

    async def create_emd(self, payload: EmdWorkspaceCreate, user: dict) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        if data.get("emd_status"):
            self._validate_status(data["emd_status"])
        if data.get("emd_document_status"):
            self._validate_document_status(data["emd_document_status"])
        self._validate_coupon_details(data.get("emd_coupon_details") or [])
        data.setdefault("emd_reference", self._emd_reference())
        data["created_by"] = user.get("id")
        data["updated_by"] = user.get("id")
        data.update(self.safety_flags())
        emd = EmdWorkspace(**data)
        created = await self.db.collection(EMD_WORKSPACE_COLLECTION).insert_one(emd.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "emd_workspace": await self._platform_projection(created),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def update_emd(self, emd_workspace_id: str, payload: EmdWorkspaceUpdate, user: dict) -> dict[str, Any]:
        existing = await self._require_emd(emd_workspace_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        if updates.get("emd_status"):
            self._validate_status(updates["emd_status"])
        if updates.get("emd_document_status"):
            self._validate_document_status(updates["emd_document_status"])
        if "emd_coupon_details" in updates:
            self._validate_coupon_details(updates.get("emd_coupon_details") or [])
        updates["updated_by"] = user.get("id")
        updates.update(self.safety_flags())
        updated = await self.db.collection(EMD_WORKSPACE_COLLECTION).update_one({"id": existing["id"]}, updates)
        if not updated:
            raise EmdWorkspaceError("EMD workspace metadata could not be updated.")
        return {
            "phase": PHASE_LABEL,
            "emd_workspace": await self._platform_projection(updated),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def delete_emd(self, emd_workspace_id: str, user: dict) -> dict[str, Any]:
        existing = await self._require_emd(emd_workspace_id)
        updated = await self.db.collection(EMD_WORKSPACE_COLLECTION).update_one(
            {"id": existing["id"]},
            {
                "emd_status": EmdWorkspaceStatus.ARCHIVED.value,
                "deleted_at": self._now(),
                "deleted_by": user.get("id"),
                "updated_by": user.get("id"),
                **self.safety_flags(),
            },
        )
        if not updated:
            raise EmdWorkspaceError("EMD workspace metadata could not be archived.")
        return {
            "phase": PHASE_LABEL,
            "emd_workspace": await self._platform_projection(updated),
            "archived": True,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        by_status = {status: 0 for status in EMD_WORKSPACE_STATUSES}
        by_document_status = {status: 0 for status in EMD_DOCUMENT_STATUSES}
        by_coupon_status = {status: 0 for status in EMD_COUPON_STATUSES}
        by_type: dict[str, int] = {}
        by_a_or_s: dict[str, int] = {}
        by_validating_carrier: dict[str, int] = {}
        by_rfic: dict[str, int] = {}
        by_rfisc: dict[str, int] = {}
        by_service_category: dict[str, int] = {}
        agency_ids: set[str] = set()
        passenger_ids: set[str] = set()
        linked_counts = {
            "associated_ticket_coupon_count": 0,
            "associated_flight_workspace_count": 0,
            "ssr_count": 0,
            "osi_count": 0,
            "ancillary_service_count": 0,
            "emd_coupon_detail_count": 0,
            "tax_breakdown_count": 0,
            "exchange_reference_count": 0,
            "refund_reference_count": 0,
            "void_reference_count": 0,
            "linked_document_count": 0,
        }
        fare_amount_total = 0.0
        taxes_amount_total = 0.0
        total_amount_total = 0.0
        for item in items:
            status = item.get("emd_status") or EmdWorkspaceStatus.DRAFT.value
            by_status[status] = by_status.get(status, 0) + 1
            document_status = item.get("emd_document_status") or EmdWorkspaceDocumentStatus.DRAFT_METADATA.value
            by_document_status[document_status] = by_document_status.get(document_status, 0) + 1
            for coupon in item.get("emd_coupon_details") or []:
                if isinstance(coupon, dict):
                    coupon_status = coupon.get("coupon_status") or EmdWorkspaceCouponStatus.UNKNOWN.value
                    by_coupon_status[coupon_status] = by_coupon_status.get(coupon_status, 0) + 1
            self._count_value(by_type, item.get("emd_type"))
            self._count_value(by_a_or_s, item.get("emd_a_or_s"))
            self._count_value(by_validating_carrier, item.get("validating_carrier"))
            self._count_value(by_rfic, item.get("rfic"))
            self._count_value(by_rfisc, item.get("rfisc"))
            self._count_value(by_service_category, item.get("service_category"))
            self._add_if_present(agency_ids, item.get("agency_id"))
            self._add_if_present(passenger_ids, item.get("passenger_id"))
            linked_counts["associated_ticket_coupon_count"] += self._list_count(item.get("associated_ticket_coupon_numbers"))
            linked_counts["associated_flight_workspace_count"] += self._list_count(item.get("associated_flight_workspace_ids"))
            linked_counts["ssr_count"] += self._list_count(item.get("ssr_ids"))
            linked_counts["osi_count"] += self._list_count(item.get("osi_ids"))
            linked_counts["ancillary_service_count"] += self._list_count(item.get("ancillary_service_ids"))
            linked_counts["emd_coupon_detail_count"] += self._list_count(item.get("emd_coupon_details"))
            linked_counts["tax_breakdown_count"] += self._list_count(item.get("tax_breakdown"))
            linked_counts["exchange_reference_count"] += self._list_count(item.get("exchange_reference_ids"))
            linked_counts["refund_reference_count"] += self._list_count(item.get("refund_reference_ids"))
            linked_counts["void_reference_count"] += self._list_count(item.get("void_reference_ids"))
            linked_counts["linked_document_count"] += self._list_count(item.get("linked_document_ids"))
            fare_amount_total += self._amount(item.get("fare_amount"))
            taxes_amount_total += self._amount(item.get("taxes_amount"))
            total_amount_total += self._amount(item.get("total_amount"))
        return {
            "total_count": len(items),
            "by_status": by_status,
            "by_document_status": by_document_status,
            "by_coupon_status": by_coupon_status,
            "by_type": by_type,
            "by_a_or_s": by_a_or_s,
            "by_validating_carrier": by_validating_carrier,
            "by_rfic": by_rfic,
            "by_rfisc": by_rfisc,
            "by_service_category": by_service_category,
            "agency_count": len(agency_ids),
            "passenger_count": len(passenger_ids),
            "fare_amount_total": fare_amount_total,
            "taxes_amount_total": taxes_amount_total,
            "total_amount_total": total_amount_total,
            **linked_counts,
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "status": EMD_WORKSPACE_STATUSES,
            "emd_document_status": EMD_DOCUMENT_STATUSES,
            "emd_coupon_status": EMD_COUPON_STATUSES,
            "emd_type": "exact metadata match",
            "emd_a_or_s": "exact metadata match",
            "validating_carrier": "exact metadata match",
            "passenger": "passenger_id metadata match",
            "rfic": "exact metadata match",
            "rfisc": "exact metadata match",
            "service_category": "exact metadata match",
            "issue_date": "ISO date metadata match",
            "metadata_only": True,
        }

    async def _platform_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        projected["emd_display_name"] = self._emd_display_name(projected)
        agency = await self._agency_context(projected.get("agency_id"))
        projected["agency"] = agency
        projected["agency_name"] = agency.get("agency_name")
        projected["read_only"] = False
        projected.update(self.safety_flags())
        return projected

    def _agency_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        projected["read_only"] = True
        projected.update(self.safety_flags())
        return projected

    async def _require_emd(self, emd_workspace_id: str, *, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": emd_workspace_id}
        if agency_id:
            filters["agency_id"] = agency_id
        item = await self.db.collection(EMD_WORKSPACE_COLLECTION).find_one(filters)
        if not item:
            alt_filters = {"emd_reference": emd_workspace_id}
            if agency_id:
                alt_filters["agency_id"] = agency_id
            item = await self.db.collection(EMD_WORKSPACE_COLLECTION).find_one(alt_filters)
        if not item and not agency_id:
            item = await self.db.collection(EMD_WORKSPACE_COLLECTION).find_one({"emd_number": emd_workspace_id})
        if not item:
            raise EmdWorkspaceError("EMD workspace metadata was not found.")
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

    def _emd_display_name(self, item: dict[str, Any]) -> str:
        if item.get("emd_number"):
            return str(item["emd_number"])
        if item.get("emd_reference"):
            return str(item["emd_reference"])
        if item.get("service_description"):
            return f"EMD for {item['service_description']}"
        return item.get("id") or "EMD workspace"

    def _validate_status(self, value: str) -> None:
        if value not in EMD_WORKSPACE_STATUSES:
            raise EmdWorkspaceError("Unsupported EMD workspace status.")

    def _validate_document_status(self, value: str) -> None:
        if value not in EMD_DOCUMENT_STATUSES:
            raise EmdWorkspaceError("Unsupported EMD document status.")

    def _validate_coupon_details(self, value: Any) -> None:
        if not isinstance(value, list):
            raise EmdWorkspaceError("EMD coupon details must be a metadata-only list.")
        for coupon in value:
            if not isinstance(coupon, dict):
                raise EmdWorkspaceError("EMD coupon detail entries must be metadata-only objects.")
            coupon_status = coupon.get("coupon_status") or EmdWorkspaceCouponStatus.UNKNOWN.value
            if coupon_status not in EMD_COUPON_STATUSES:
                raise EmdWorkspaceError("Unsupported EMD coupon status.")

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

    def _emd_reference(self) -> str:
        return f"EMDW-{new_id()[:8].upper()}"

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
            "emd_workspace_metadata_only": True,
            "emd_issuance_disabled": True,
            "emd_exchange_disabled": True,
            "emd_refund_disabled": True,
            "emd_voiding_disabled": True,
            "live_gds_ndc_connectivity_disabled": True,
            "gds_connectivity_disabled": True,
            "ndc_connectivity_disabled": True,
            "airline_apis_disabled": True,
            "airline_api_calls_disabled": True,
            "payment_processing_disabled": True,
            "rfic_rfisc_validation_engine_disabled": True,
            "ssr_osi_transmission_disabled": True,
            "background_workers_disabled": True,
            "external_integrations_disabled": True,
            "external_api_calls_disabled": True,
            "parallel_duplicate_emd_architecture_disabled": True,
            "automation_disabled": True,
        }
