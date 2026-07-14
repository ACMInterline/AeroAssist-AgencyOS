from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import (
    SsrOsiApprovalStatus,
    SsrOsiNeedCategory,
    SsrOsiOperationalStatus,
    SsrOsiReadinessStatus,
    SsrOsiWorkspace,
    SsrOsiWorkspaceCreate,
    SsrOsiWorkspaceUpdate,
    new_id,
)


PHASE_LABEL = "phase_55_5_airline_distribution_pss_gds_ndc_capability_intelligence_foundation"
SSR_OSI_WORKSPACE_COLLECTION = "ssr_osi_workspaces"

SSR_OSI_OPERATIONAL_STATUSES = [item.value for item in SsrOsiOperationalStatus]
SSR_OSI_NEED_CATEGORIES = [item.value for item in SsrOsiNeedCategory]
SSR_OSI_READINESS_STATUSES = [item.value for item in SsrOsiReadinessStatus]
SSR_OSI_APPROVAL_STATUSES = [item.value for item in SsrOsiApprovalStatus]


class SsrOsiWorkspaceError(ValueError):
    pass


class SsrOsiWorkspaceService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_platform_workspaces(
        self,
        *,
        agency_id: str | None = None,
        need_category: str | None = None,
        airline: str | None = None,
        approval_status: str | None = None,
        readiness_status: str | None = None,
        passenger: str | None = None,
        priority: str | None = None,
        rfic: str | None = None,
        rfisc: str | None = None,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if need_category:
            filters["need_category"] = need_category
        if approval_status:
            filters["approval_status"] = approval_status
        if readiness_status:
            filters["readiness_status"] = readiness_status
        if passenger:
            filters["passenger_workspace_id"] = passenger
        if priority:
            filters["operational_priority"] = priority
        if rfic:
            filters["rfic"] = rfic
        if rfisc:
            filters["rfisc"] = rfisc

        items = await self.db.collection(SSR_OSI_WORKSPACE_COLLECTION).find_many(filters or None)
        if not include_archived:
            items = [
                item
                for item in items
                if not item.get("deleted_at")
                and item.get("operational_status", SsrOsiOperationalStatus.DRAFT.value) != SsrOsiOperationalStatus.ARCHIVED.value
            ]
        if airline:
            airline_key = airline.upper()
            items = [
                item
                for item in items
                if airline_key
                in {
                    str(item.get("airline_code") or "").upper(),
                    str(item.get("validating_carrier") or "").upper(),
                    str(item.get("operating_carrier") or "").upper(),
                }
            ]
        items.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._platform_projection(item) for item in items]

    async def list_agency_workspaces(
        self,
        agency_id: str,
        *,
        need_category: str | None = None,
        airline: str | None = None,
        approval_status: str | None = None,
        readiness_status: str | None = None,
        passenger: str | None = None,
        priority: str | None = None,
        rfic: str | None = None,
        rfisc: str | None = None,
    ) -> list[dict[str, Any]]:
        items = await self.list_platform_workspaces(
            agency_id=agency_id,
            need_category=need_category,
            airline=airline,
            approval_status=approval_status,
            readiness_status=readiness_status,
            passenger=passenger,
            priority=priority,
            rfic=rfic,
            rfisc=rfisc,
        )
        return [self._agency_projection(item) for item in items if item.get("agency_id") == agency_id]

    async def platform_response(
        self,
        *,
        agency_id: str | None = None,
        need_category: str | None = None,
        airline: str | None = None,
        approval_status: str | None = None,
        readiness_status: str | None = None,
        passenger: str | None = None,
        priority: str | None = None,
        rfic: str | None = None,
        rfisc: str | None = None,
        include_archived: bool = False,
    ) -> dict[str, Any]:
        items = await self.list_platform_workspaces(
            agency_id=agency_id,
            need_category=need_category,
            airline=airline,
            approval_status=approval_status,
            readiness_status=readiness_status,
            passenger=passenger,
            priority=priority,
            rfic=rfic,
            rfisc=rfisc,
            include_archived=include_archived,
        )
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "ssr_osi_workspace_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "SSR / OSI workspaces are metadata-only operational service records. They connect passenger needs to service requirements, airline handling, documents, EMD references, tasks, timelines, and communications without live SSR/OSI transmission, airline APIs, GDS/NDC connectivity, AI recommendations, approval automation, EMD issuance, workers, or provider integrations.",
            "aoie_input": "Passenger Need -> SSR / OSI Workspace -> Airline Knowledge -> Capability Matrix -> Operational Feasibility -> Offer Builder",
            **self.safety_flags(),
        }

    async def agency_response(
        self,
        agency_id: str,
        *,
        need_category: str | None = None,
        airline: str | None = None,
        approval_status: str | None = None,
        readiness_status: str | None = None,
        passenger: str | None = None,
        priority: str | None = None,
        rfic: str | None = None,
        rfisc: str | None = None,
    ) -> dict[str, Any]:
        items = await self.list_agency_workspaces(
            agency_id,
            need_category=need_category,
            airline=airline,
            approval_status=approval_status,
            readiness_status=readiness_status,
            passenger=passenger,
            priority=priority,
            rfic=rfic,
            rfisc=rfisc,
        )
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "ssr_osi_workspace_count": len(items),
            "summary": self.summarize_counts(items),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            "notice": "Agency Passenger Services are read-only SSR / OSI workspace metadata. No live SSR/OSI transmission, airline approval automation, EMD issuance, provider call, or background automation is available.",
            "aoie_input": "Passenger Need -> SSR / OSI Workspace -> Airline Knowledge -> Capability Matrix -> Operational Feasibility -> Offer Builder",
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

    async def create_workspace(self, payload: SsrOsiWorkspaceCreate, user: dict) -> dict[str, Any]:
        data = payload.model_dump(mode="json", exclude_none=True)
        self._validate_payload(data)
        data.setdefault("workspace_reference", self._workspace_reference())
        data["created_by"] = user.get("id")
        data["updated_by"] = user.get("id")
        data.update(self.safety_flags())
        workspace = SsrOsiWorkspace(**data)
        created = await self.db.collection(SSR_OSI_WORKSPACE_COLLECTION).insert_one(workspace.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "ssr_osi_workspace": await self._platform_projection(created),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def update_workspace(self, workspace_id: str, payload: SsrOsiWorkspaceUpdate, user: dict) -> dict[str, Any]:
        existing = await self._require_workspace(workspace_id)
        updates = payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        self._validate_payload(updates, partial=True)
        updates["updated_by"] = user.get("id")
        updates.update(self.safety_flags())
        updated = await self.db.collection(SSR_OSI_WORKSPACE_COLLECTION).update_one({"id": existing["id"]}, updates)
        if not updated:
            raise SsrOsiWorkspaceError("SSR / OSI workspace metadata could not be updated.")
        return {
            "phase": PHASE_LABEL,
            "ssr_osi_workspace": await self._platform_projection(updated),
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def delete_workspace(self, workspace_id: str, user: dict) -> dict[str, Any]:
        existing = await self._require_workspace(workspace_id)
        updated = await self.db.collection(SSR_OSI_WORKSPACE_COLLECTION).update_one(
            {"id": existing["id"]},
            {
                "operational_status": SsrOsiOperationalStatus.ARCHIVED.value,
                "deleted_at": self._now(),
                "deleted_by": user.get("id"),
                "updated_by": user.get("id"),
                **self.safety_flags(),
            },
        )
        if not updated:
            raise SsrOsiWorkspaceError("SSR / OSI workspace metadata could not be archived.")
        return {
            "phase": PHASE_LABEL,
            "ssr_osi_workspace": await self._platform_projection(updated),
            "archived": True,
            "read_only": False,
            "metadata_only": True,
            **self.safety_flags(),
        }

    def summarize_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        by_operational_status = {status: 0 for status in SSR_OSI_OPERATIONAL_STATUSES}
        by_readiness_status = {status: 0 for status in SSR_OSI_READINESS_STATUSES}
        by_approval_status = {status: 0 for status in SSR_OSI_APPROVAL_STATUSES}
        by_need_category = {category: 0 for category in SSR_OSI_NEED_CATEGORIES}
        by_airline: dict[str, int] = {}
        by_rfic: dict[str, int] = {}
        by_rfisc: dict[str, int] = {}
        agency_ids: set[str] = set()
        passenger_ids: set[str] = set()
        linked_counts = {
            "emd_workspace_link_count": 0,
            "document_requirement_count": 0,
            "missing_requirement_count": 0,
            "unresolved_item_count": 0,
            "task_count": 0,
            "timeline_count": 0,
            "communication_count": 0,
            "flight_workspace_count": 0,
            "linked_document_count": 0,
        }
        for item in items:
            by_operational_status[item.get("operational_status") or SsrOsiOperationalStatus.DRAFT.value] = by_operational_status.get(item.get("operational_status") or SsrOsiOperationalStatus.DRAFT.value, 0) + 1
            by_readiness_status[item.get("readiness_status") or SsrOsiReadinessStatus.PENDING.value] = by_readiness_status.get(item.get("readiness_status") or SsrOsiReadinessStatus.PENDING.value, 0) + 1
            by_approval_status[item.get("approval_status") or SsrOsiApprovalStatus.NOT_REQUIRED.value] = by_approval_status.get(item.get("approval_status") or SsrOsiApprovalStatus.NOT_REQUIRED.value, 0) + 1
            by_need_category[item.get("need_category") or SsrOsiNeedCategory.OTHER.value] = by_need_category.get(item.get("need_category") or SsrOsiNeedCategory.OTHER.value, 0) + 1
            self._count_value(by_airline, item.get("airline_code") or item.get("validating_carrier") or item.get("operating_carrier"))
            self._count_value(by_rfic, item.get("rfic"))
            self._count_value(by_rfisc, item.get("rfisc"))
            self._add_if_present(agency_ids, item.get("agency_id"))
            self._add_if_present(passenger_ids, item.get("passenger_workspace_id"))
            linked_counts["emd_workspace_link_count"] += self._list_count(item.get("emd_workspace_ids")) + (1 if item.get("emd_workspace_id") else 0)
            linked_counts["document_requirement_count"] += self._list_count(item.get("document_requirements"))
            linked_counts["missing_requirement_count"] += self._list_count(item.get("missing_requirements"))
            linked_counts["unresolved_item_count"] += self._list_count(item.get("unresolved_items"))
            linked_counts["task_count"] += self._list_count(item.get("task_ids"))
            linked_counts["timeline_count"] += self._list_count(item.get("timeline_ids"))
            linked_counts["communication_count"] += self._list_count(item.get("communication_ids"))
            linked_counts["flight_workspace_count"] += self._list_count(item.get("flight_workspace_ids"))
            linked_counts["linked_document_count"] += self._list_count(item.get("linked_document_ids"))
        return {
            "total_count": len(items),
            "by_operational_status": by_operational_status,
            "by_readiness_status": by_readiness_status,
            "by_approval_status": by_approval_status,
            "by_need_category": by_need_category,
            "by_airline": by_airline,
            "by_rfic": by_rfic,
            "by_rfisc": by_rfisc,
            "agency_count": len(agency_ids),
            "passenger_count": len(passenger_ids),
            **linked_counts,
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "need_category": SSR_OSI_NEED_CATEGORIES,
            "airline": "airline_code, validating_carrier, or operating_carrier exact metadata match",
            "approval_status": SSR_OSI_APPROVAL_STATUSES,
            "readiness_status": SSR_OSI_READINESS_STATUSES,
            "passenger": "passenger_workspace_id metadata match",
            "priority": "operational_priority exact metadata match",
            "rfic": "RFIC exact metadata match",
            "rfisc": "RFISC exact metadata match",
            "metadata_only": True,
        }

    async def _platform_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        projected["workspace_display_name"] = self._workspace_display_name(projected)
        agency = await self._agency_context(projected.get("agency_id"))
        projected["agency"] = agency
        projected["agency_name"] = agency.get("agency_name")
        projected["read_only"] = False
        projected["aoie_operational_input"] = True
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
        item = await self.db.collection(SSR_OSI_WORKSPACE_COLLECTION).find_one(filters)
        if not item:
            alt_filters = {"workspace_reference": workspace_id}
            if agency_id:
                alt_filters["agency_id"] = agency_id
            item = await self.db.collection(SSR_OSI_WORKSPACE_COLLECTION).find_one(alt_filters)
        if not item:
            raise SsrOsiWorkspaceError("SSR / OSI workspace metadata was not found.")
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
        self._validate_enum(data.get("operational_status"), SSR_OSI_OPERATIONAL_STATUSES, "operational status")
        self._validate_enum(data.get("need_category"), SSR_OSI_NEED_CATEGORIES, "need category")
        self._validate_enum(data.get("readiness_status"), SSR_OSI_READINESS_STATUSES, "readiness status")
        self._validate_enum(data.get("approval_status"), SSR_OSI_APPROVAL_STATUSES, "approval status")
        if not partial and not data.get("agency_id"):
            raise SsrOsiWorkspaceError("Agency id is required for SSR / OSI workspace metadata.")

    def _validate_enum(self, value: Any, allowed: list[str], label: str) -> None:
        if value and value not in allowed:
            raise SsrOsiWorkspaceError(f"Unsupported SSR / OSI {label}.")

    def _workspace_display_name(self, item: dict[str, Any]) -> str:
        if item.get("workspace_reference"):
            return str(item["workspace_reference"])
        if item.get("ssr_code"):
            return f"SSR {item['ssr_code']}"
        if item.get("need_description"):
            return str(item["need_description"])
        return item.get("id") or "SSR / OSI workspace"

    def _workspace_reference(self) -> str:
        return f"SSROSI-{new_id()[:8].upper()}"

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
            "ssr_osi_workspace_metadata_only": True,
            "live_ssr_transmission_disabled": True,
            "live_osi_transmission_disabled": True,
            "gds_connectivity_disabled": True,
            "ndc_connectivity_disabled": True,
            "airline_apis_disabled": True,
            "ai_recommendation_disabled": True,
            "automatic_airline_approval_disabled": True,
            "automatic_emd_issuance_disabled": True,
            "background_workers_disabled": True,
            "provider_integrations_disabled": True,
            "external_api_calls_disabled": True,
            "automation_disabled": True,
        }
