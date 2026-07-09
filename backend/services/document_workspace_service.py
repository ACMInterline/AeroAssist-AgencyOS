from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import (
    DocumentWorkspace,
    DocumentWorkspaceCreate,
    DocumentWorkspaceStatus,
    DocumentWorkspaceType,
    DocumentWorkspaceUpdate,
    new_id,
)


PHASE_LABEL = "phase_52_1_reference_data_engine_foundation"
DOCUMENT_WORKSPACE_COLLECTION = "document_workspaces"

DOCUMENT_WORKSPACE_STATUSES = [item.value for item in DocumentWorkspaceStatus]
DOCUMENT_WORKSPACE_TYPES = [item.value for item in DocumentWorkspaceType]


class DocumentWorkspaceError(ValueError):
    pass


class DocumentWorkspaceService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_platform_workspaces(
        self,
        *,
        agency_id: str | None = None,
        document_type: str | None = None,
        document_status: str | None = None,
        passenger: str | None = None,
        booking_reference: str | None = None,
        related_service: str | None = None,
        required_for_travel: bool | None = None,
        verification_status: str | None = None,
        deadline: str | None = None,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if document_type:
            filters["document_type"] = document_type
        if document_status:
            filters["document_status"] = document_status
        if booking_reference:
            filters["booking_reference"] = booking_reference
        if required_for_travel is not None:
            filters["required_for_travel"] = required_for_travel
        if verification_status:
            filters["verification_status"] = verification_status
        if deadline:
            filters["requirement_deadline"] = deadline

        items = await self.db.collection(DOCUMENT_WORKSPACE_COLLECTION).find_many(filters or None)
        if not include_archived:
            items = [
                item
                for item in items
                if not item.get("deleted_at")
                and item.get("document_status", DocumentWorkspaceStatus.DRAFT_METADATA.value) != DocumentWorkspaceStatus.ARCHIVED.value
            ]
        if passenger:
            passenger_key = passenger.lower()
            items = [
                item
                for item in items
                if passenger_key
                in {
                    str(item.get("passenger_workspace_id") or "").lower(),
                    str(item.get("passenger_id") or "").lower(),
                    str(item.get("passenger_name") or "").lower(),
                }
            ]
        if related_service:
            related_key = related_service.lower()
            items = [
                item
                for item in items
                if related_key
                in {
                    str(item.get("related_service_requirement") or "").lower(),
                    str(item.get("related_ssr_code") or "").lower(),
                    str(item.get("ssr_osi_workspace_id") or "").lower(),
                }
            ]
        items.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._platform_projection(item) for item in items]

    async def list_agency_workspaces(
        self,
        agency_id: str,
        *,
        document_type: str | None = None,
        document_status: str | None = None,
        passenger: str | None = None,
        booking_reference: str | None = None,
        related_service: str | None = None,
        required_for_travel: bool | None = None,
        verification_status: str | None = None,
        deadline: str | None = None,
    ) -> list[dict[str, Any]]:
        items = await self.list_platform_workspaces(
            agency_id=agency_id,
            document_type=document_type,
            document_status=document_status,
            passenger=passenger,
            booking_reference=booking_reference,
            related_service=related_service,
            required_for_travel=required_for_travel,
            verification_status=verification_status,
            deadline=deadline,
        )
        return [self._agency_projection(item) for item in items if item.get("agency_id") == agency_id]

    async def platform_response(
        self,
        *,
        agency_id: str | None = None,
        document_type: str | None = None,
        document_status: str | None = None,
        passenger: str | None = None,
        booking_reference: str | None = None,
        related_service: str | None = None,
        required_for_travel: bool | None = None,
        verification_status: str | None = None,
        deadline: str | None = None,
        include_archived: bool = False,
    ) -> dict[str, Any]:
        items = await self.list_platform_workspaces(
            agency_id=agency_id,
            document_type=document_type,
            document_status=document_status,
            passenger=passenger,
            booking_reference=booking_reference,
            related_service=related_service,
            required_for_travel=required_for_travel,
            verification_status=verification_status,
            deadline=deadline,
            include_archived=include_archived,
        )
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "document_workspace_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Document Workspaces are metadata-only operational document records. They link passenger, request, trip, booking, ticket, EMD, SSR / OSI, and operational intelligence metadata without delivery, e-signature, public links, PDF generation, payment or invoice generation, external storage integrations, workers, or AI document generation.",
            **self.safety_flags(),
        }

    async def agency_response(
        self,
        agency_id: str,
        *,
        document_type: str | None = None,
        document_status: str | None = None,
        passenger: str | None = None,
        booking_reference: str | None = None,
        related_service: str | None = None,
        required_for_travel: bool | None = None,
        verification_status: str | None = None,
        deadline: str | None = None,
    ) -> dict[str, Any]:
        items = await self.list_agency_workspaces(
            agency_id,
            document_type=document_type,
            document_status=document_status,
            passenger=passenger,
            booking_reference=booking_reference,
            related_service=related_service,
            required_for_travel=required_for_travel,
            verification_status=verification_status,
            deadline=deadline,
        )
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "document_workspace_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            "notice": "Agency Documents show read-only operational document workspace metadata. No delivery, e-signature, public link, PDF generation, payment or invoice generation, storage integration, worker, or AI generation is available.",
            **self.safety_flags(),
        }

    async def platform_summary(self) -> dict[str, Any]:
        items = await self.list_platform_workspaces()
        return {
            "phase": PHASE_LABEL,
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_summary(self, agency_id: str) -> dict[str, Any]:
        items = await self.list_agency_workspaces(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def get_platform_workspace(self, workspace_id: str) -> dict[str, Any]:
        item = await self._require_workspace(workspace_id)
        return await self._platform_projection(item)

    async def get_agency_workspace(self, agency_id: str, workspace_id: str) -> dict[str, Any]:
        item = await self._require_workspace(workspace_id, agency_id=agency_id)
        return self._agency_projection(await self._platform_projection(item))

    async def create_workspace(self, payload: DocumentWorkspaceCreate, user: dict) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        self._validate_payload(data)
        data.setdefault("document_reference", self._document_reference())
        data["created_by"] = user.get("id")
        data["updated_by"] = user.get("id")
        data.update(self.safety_flags())
        workspace = DocumentWorkspace(**data)
        created = await self.db.collection(DOCUMENT_WORKSPACE_COLLECTION).insert_one(workspace.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "document_workspace": await self._platform_projection(created),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def update_workspace(self, workspace_id: str, payload: DocumentWorkspaceUpdate, user: dict) -> dict[str, Any]:
        existing = await self._require_workspace(workspace_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        self._validate_payload(updates, partial=True)
        updates["updated_by"] = user.get("id")
        updates.update(self.safety_flags())
        updated = await self.db.collection(DOCUMENT_WORKSPACE_COLLECTION).update_one({"id": existing["id"]}, updates)
        if not updated:
            raise DocumentWorkspaceError("Document workspace metadata could not be updated.")
        return {
            "phase": PHASE_LABEL,
            "document_workspace": await self._platform_projection(updated),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def delete_workspace(self, workspace_id: str, user: dict) -> dict[str, Any]:
        existing = await self._require_workspace(workspace_id)
        updated = await self.db.collection(DOCUMENT_WORKSPACE_COLLECTION).update_one(
            {"id": existing["id"]},
            {
                "document_status": DocumentWorkspaceStatus.ARCHIVED.value,
                "deleted_at": self._now(),
                "deleted_by": user.get("id"),
                "updated_by": user.get("id"),
                **self.safety_flags(),
            },
        )
        if not updated:
            raise DocumentWorkspaceError("Document workspace metadata could not be archived.")
        return {
            "phase": PHASE_LABEL,
            "document_workspace": await self._platform_projection(updated),
            "archived": True,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        by_document_status = {status: 0 for status in DOCUMENT_WORKSPACE_STATUSES}
        by_document_type = {document_type: 0 for document_type in DOCUMENT_WORKSPACE_TYPES}
        by_verification_status: dict[str, int] = {}
        agency_ids: set[str] = set()
        passenger_ids: set[str] = set()
        booking_references: set[str] = set()
        related_services: set[str] = set()
        linked_counts = {
            "required_for_travel_count": 0,
            "required_by_airline_count": 0,
            "required_by_airport_count": 0,
            "required_by_authority_count": 0,
            "customer_visible_count": 0,
            "airline_visible_count": 0,
            "internal_only_count": 0,
            "passenger_workspace_count": 0,
            "travel_request_workspace_count": 0,
            "trip_workspace_count": 0,
            "booking_workspace_count": 0,
            "ticket_workspace_count": 0,
            "emd_workspace_count": 0,
            "ssr_osi_workspace_count": 0,
            "operational_intelligence_record_count": 0,
            "document_package_count": 0,
            "render_job_count": 0,
            "share_record_count": 0,
        }
        for item in items:
            status = item.get("document_status") or DocumentWorkspaceStatus.DRAFT_METADATA.value
            document_type = item.get("document_type") or DocumentWorkspaceType.OTHER.value
            by_document_status[status] = by_document_status.get(status, 0) + 1
            by_document_type[document_type] = by_document_type.get(document_type, 0) + 1
            self._count_value(by_verification_status, item.get("verification_status"))
            self._add_if_present(agency_ids, item.get("agency_id"))
            self._add_if_present(passenger_ids, item.get("passenger_workspace_id") or item.get("passenger_id"))
            self._add_if_present(booking_references, item.get("booking_reference"))
            self._add_if_present(related_services, item.get("related_service_requirement") or item.get("related_ssr_code"))
            linked_counts["required_for_travel_count"] += 1 if item.get("required_for_travel") else 0
            linked_counts["required_by_airline_count"] += 1 if item.get("required_by_airline") else 0
            linked_counts["required_by_airport_count"] += 1 if item.get("required_by_airport") else 0
            linked_counts["required_by_authority_count"] += 1 if item.get("required_by_authority") else 0
            linked_counts["customer_visible_count"] += 1 if item.get("customer_visible") else 0
            linked_counts["airline_visible_count"] += 1 if item.get("airline_visible") else 0
            linked_counts["internal_only_count"] += 1 if item.get("internal_only") else 0
            linked_counts["passenger_workspace_count"] += 1 if item.get("passenger_workspace_id") else 0
            linked_counts["travel_request_workspace_count"] += 1 if item.get("travel_request_workspace_id") else 0
            linked_counts["trip_workspace_count"] += 1 if item.get("trip_workspace_id") else 0
            linked_counts["booking_workspace_count"] += 1 if item.get("booking_workspace_id") else 0
            linked_counts["ticket_workspace_count"] += 1 if item.get("ticket_workspace_id") else 0
            linked_counts["emd_workspace_count"] += 1 if item.get("emd_workspace_id") else 0
            linked_counts["ssr_osi_workspace_count"] += 1 if item.get("ssr_osi_workspace_id") else 0
            linked_counts["operational_intelligence_record_count"] += self._list_count(item.get("operational_intelligence_record_ids"))
            linked_counts["document_package_count"] += self._list_count(item.get("document_package_ids"))
            linked_counts["render_job_count"] += self._list_count(item.get("render_job_ids"))
            linked_counts["share_record_count"] += self._list_count(item.get("share_record_ids"))
        return {
            "total_count": len(items),
            "by_document_status": by_document_status,
            "by_document_type": by_document_type,
            "by_verification_status": by_verification_status,
            "agency_count": len(agency_ids),
            "passenger_count": len(passenger_ids),
            "booking_reference_count": len(booking_references),
            "related_service_count": len(related_services),
            **linked_counts,
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "document_type": DOCUMENT_WORKSPACE_TYPES,
            "document_status": DOCUMENT_WORKSPACE_STATUSES,
            "passenger": "passenger_workspace_id, passenger_id, or passenger_name metadata match",
            "booking_reference": "booking_reference exact metadata match",
            "related_service": "related_service_requirement, related_ssr_code, or ssr_osi_workspace_id metadata match",
            "required_for_travel": "boolean metadata filter",
            "verification_status": "verification_status exact metadata match",
            "deadline": "requirement_deadline exact date metadata match",
            "metadata_only": True,
        }

    async def _platform_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        projected["document_display_name"] = self._document_display_name(projected)
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

    async def _require_workspace(self, workspace_id: str, *, agency_id: str | None = None) -> dict[str, Any]:
        filters = {"id": workspace_id}
        if agency_id:
            filters["agency_id"] = agency_id
        item = await self.db.collection(DOCUMENT_WORKSPACE_COLLECTION).find_one(filters)
        if not item:
            alt_filters = {"document_reference": workspace_id}
            if agency_id:
                alt_filters["agency_id"] = agency_id
            item = await self.db.collection(DOCUMENT_WORKSPACE_COLLECTION).find_one(alt_filters)
        if not item:
            raise DocumentWorkspaceError("Document workspace metadata was not found.")
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

    def _validate_payload(self, data: dict[str, Any], *, partial: bool = False) -> None:
        self._validate_enum(data.get("document_status"), DOCUMENT_WORKSPACE_STATUSES, "document status")
        self._validate_enum(data.get("document_type"), DOCUMENT_WORKSPACE_TYPES, "document type")
        if not partial and not data.get("agency_id"):
            raise DocumentWorkspaceError("Agency id is required for document workspace metadata.")

    def _validate_enum(self, value: Any, allowed: list[str], label: str) -> None:
        if value and value not in allowed:
            raise DocumentWorkspaceError(f"Unsupported document workspace {label}.")

    def _document_display_name(self, item: dict[str, Any]) -> str:
        if item.get("document_title"):
            return str(item["document_title"])
        if item.get("document_reference"):
            return str(item["document_reference"])
        if item.get("file_name"):
            return str(item["file_name"])
        return item.get("id") or "Document workspace"

    def _document_reference(self) -> str:
        return f"DOCW-{new_id()[:8].upper()}"

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

    def _sort_text(self, value: Any) -> str:
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value or "")

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "document_workspace_metadata_only": True,
            "live_document_delivery_disabled": True,
            "e_signature_disabled": True,
            "public_share_links_disabled": True,
            "automatic_pdf_generation_disabled": True,
            "payment_invoice_generation_disabled": True,
            "external_storage_integrations_disabled": True,
            "background_workers_disabled": True,
            "ai_document_generation_disabled": True,
            "automation_disabled": True,
            "phase_36_5_document_foundation_not_duplicated": True,
        }
