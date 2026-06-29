from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from database import Database
from models import (
    BookingCreateFromReadinessRequest,
    BookingProviderTarget,
    BookingReadinessStatus,
    BookingRecord,
    BookingRecordStatus,
    BookingRecordUpdate,
    BookingRecordProviderStatus,
    BookingTimelineEvent,
    BookingWorkspace,
    BookingWorkspaceStatus,
)


PHASE_LABEL = "phase_36_3_booking_pnr_foundation"
ACTIVE_WORKSPACE_STATUSES = {
    BookingWorkspaceStatus.DRAFT.value,
    BookingWorkspaceStatus.READY_TO_BOOK.value,
    BookingWorkspaceStatus.BOOKING_IN_PROGRESS.value,
    BookingWorkspaceStatus.BOOKED.value,
    BookingWorkspaceStatus.BLOCKED.value,
}
REBUILDABLE_RECORD_STATUSES = {
    BookingRecordStatus.DRAFT.value,
    BookingRecordStatus.PENDING.value,
}


class BookingWorkspaceError(ValueError):
    pass


def _as_value(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _latest(items: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not items:
        return None
    return sorted(
        items,
        key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""),
        reverse=True,
    )[0]


def _summary_from_trip(trip: dict[str, Any] | None) -> dict[str, Any] | None:
    if not trip:
        return None
    return {
        "id": trip.get("id"),
        "trip_reference": trip.get("trip_reference"),
        "trip_title": trip.get("trip_title"),
        "route_summary": trip.get("route_summary"),
        "date_summary": trip.get("date_summary"),
        "status": trip.get("trip_status"),
    }


def _summary_from_acceptance(acceptance: dict[str, Any] | None) -> dict[str, Any] | None:
    if not acceptance:
        return None
    return {
        "id": acceptance.get("id"),
        "workspace_id": acceptance.get("workspace_id"),
        "option_id": acceptance.get("option_id"),
        "status": acceptance.get("status"),
        "accepted_at": acceptance.get("accepted_at"),
        "client_visible_summary_json": acceptance.get("client_visible_summary_json") or {},
    }


def _summary_from_readiness(readiness: dict[str, Any] | None) -> dict[str, Any] | None:
    if not readiness:
        return None
    return {
        "id": readiness.get("id"),
        "status": readiness.get("status"),
        "provider_target": readiness.get("provider_target"),
        "warnings": len(readiness.get("warnings_json") or []),
        "policy_violations": len(readiness.get("policy_violations_json") or []),
        "required_documents": len(readiness.get("required_documents_json") or []),
    }


class BookingWorkspaceService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def create_booking_workspace_from_readiness(
        self,
        agency_id: str,
        payload: BookingCreateFromReadinessRequest,
        user: dict,
    ) -> dict[str, Any] | None:
        readiness = await self.db.collection("booking_readiness_packages").find_one(
            {"agency_id": agency_id, "id": payload.booking_readiness_package_id}
        )
        if readiness is None:
            return None
        if readiness.get("status") not in {
            BookingReadinessStatus.DRAFT.value,
            BookingReadinessStatus.READY.value,
            BookingReadinessStatus.BLOCKED.value,
        }:
            raise BookingWorkspaceError("Booking readiness package is not eligible for workspace creation.")

        existing = await self._existing_active_workspace(agency_id, readiness["id"])
        if existing:
            detail = await self.get_booking_workspace(agency_id, existing["id"])
            detail["warnings"] = [
                *detail.get("warnings", []),
                {
                    "code": "existing_booking_workspace_reused",
                    "message": "An active booking workspace already exists for this readiness package.",
                    "severity": "info",
                },
            ]
            return detail

        trip = await self.db.collection("trip_dossiers").find_one(
            {"agency_id": agency_id, "id": readiness["trip_id"]}
        )
        acceptance = await self.db.collection("offer_acceptances").find_one(
            {"agency_id": agency_id, "id": readiness.get("acceptance_id")}
        )
        workspace_number = await self._next_workspace_number(agency_id)
        provider_target = _as_value(payload.provider_target or readiness.get("provider_target") or BookingProviderTarget.MANUAL.value)
        workspace_status = self._status_from_readiness(readiness)
        source_snapshot = await self._source_snapshot(agency_id, readiness, acceptance, trip)
        workspace = BookingWorkspace(
            agency_id=agency_id,
            trip_id=readiness["trip_id"],
            request_id=readiness.get("request_id"),
            offer_workspace_id=readiness.get("workspace_id"),
            offer_option_id=readiness.get("option_id"),
            offer_acceptance_id=readiness.get("acceptance_id"),
            booking_readiness_package_id=readiness["id"],
            workspace_number=workspace_number,
            title=self._workspace_title(workspace_number, trip, readiness),
            status=workspace_status,
            provider_target=provider_target,
            source_snapshot_json=source_snapshot,
            passengers_snapshot_json=readiness.get("passengers_snapshot_json") or [],
            segments_snapshot_json=readiness.get("segments_snapshot_json") or [],
            pricing_snapshot_json=readiness.get("pricing_snapshot_json") or {},
            services_snapshot_json=readiness.get("services_snapshot_json") or {},
            pets_snapshot_json=readiness.get("pets_snapshot_json") or {},
            special_items_snapshot_json=readiness.get("special_items_snapshot_json") or {},
            required_documents_json=readiness.get("required_documents_json") or [],
            warnings_json=readiness.get("warnings_json") or [],
            policy_violations_json=readiness.get("policy_violations_json") or [],
            ssr_json=readiness.get("ssr_json") or [],
            osi_json=readiness.get("osi_json") or [],
            internal_notes=payload.internal_notes,
            created_by_user_id=user.get("id"),
        )
        created_workspace = await self.db.collection("booking_workspaces").insert_one(
            workspace.model_dump(mode="json")
        )

        created_record = None
        if payload.create_draft_record:
            record = self._record_from_workspace_readiness(created_workspace, readiness, user)
            created_record = await self.db.collection("booking_records").insert_one(
                record.model_dump(mode="json")
            )
            created_workspace = await self.db.collection("booking_workspaces").update_one(
                {"agency_id": agency_id, "id": created_workspace["id"]},
                {"booking_record_id": created_record["id"]},
            ) or created_workspace

        await self._write_timeline(
            agency_id,
            created_workspace["id"],
            "booking_workspace.created_from_readiness",
            "Booking workspace created",
            user.get("id"),
            booking_record_id=(created_record or {}).get("id"),
            trip_id=readiness.get("trip_id"),
            description="Created from booking readiness package without provider execution.",
            payload_json={
                "booking_readiness_package_id": readiness["id"],
                "provider_execution_disabled": True,
                "workspace_status": created_workspace.get("status"),
            },
        )
        return await self.get_booking_workspace(agency_id, created_workspace["id"])

    async def list_booking_workspaces(
        self,
        agency_id: str,
        *,
        status_filter: str | None = None,
        provider_target: str | None = None,
        trip_id: str | None = None,
    ) -> dict[str, Any]:
        filters = {"agency_id": agency_id}
        if status_filter:
            filters["status"] = status_filter
        if provider_target:
            filters["provider_target"] = provider_target
        if trip_id:
            filters["trip_id"] = trip_id
        workspaces = await self.db.collection("booking_workspaces").find_many(filters)
        records = await self.db.collection("booking_records").find_many({"agency_id": agency_id})
        records_by_workspace = {item.get("booking_workspace_id"): item for item in records}
        trips = {
            item["id"]: item
            for item in await self.db.collection("trip_dossiers").find_many({"agency_id": agency_id})
        }
        items = []
        for workspace in workspaces:
            record = records_by_workspace.get(workspace["id"])
            items.append(
                {
                    **workspace,
                    "booking_record": record,
                    "trip_summary": _summary_from_trip(trips.get(workspace.get("trip_id"))),
                    "warning_count": len(workspace.get("warnings_json") or []),
                    "policy_violation_count": len(workspace.get("policy_violations_json") or []),
                }
            )
        items.sort(key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""), reverse=True)
        return {"items": items}

    async def get_booking_workspace(
        self,
        agency_id: str,
        booking_workspace_id: str,
    ) -> dict[str, Any]:
        workspace = await self.db.collection("booking_workspaces").find_one(
            {"agency_id": agency_id, "id": booking_workspace_id}
        )
        if workspace is None:
            return {}
        record = None
        if workspace.get("booking_record_id"):
            record = await self.db.collection("booking_records").find_one(
                {"agency_id": agency_id, "id": workspace["booking_record_id"]}
            )
        record = record or await self.db.collection("booking_records").find_one(
            {"agency_id": agency_id, "booking_workspace_id": workspace["id"]}
        )
        readiness = await self.db.collection("booking_readiness_packages").find_one(
            {"agency_id": agency_id, "id": workspace.get("booking_readiness_package_id")}
        )
        acceptance = await self.db.collection("offer_acceptances").find_one(
            {"agency_id": agency_id, "id": workspace.get("offer_acceptance_id")}
        )
        trip = await self.db.collection("trip_dossiers").find_one(
            {"agency_id": agency_id, "id": workspace.get("trip_id")}
        )
        timeline = await self.db.collection("booking_timeline_events").find_many(
            {"agency_id": agency_id, "booking_workspace_id": workspace["id"]}
        )
        timeline.sort(key=lambda item: str(item.get("created_at") or ""))
        return {
            "booking_workspace": workspace,
            "booking_record": record,
            "timeline": timeline,
            "warnings": [],
            "readiness_summary": _summary_from_readiness(readiness),
            "accepted_offer_summary": _summary_from_acceptance(acceptance),
            "trip_summary": _summary_from_trip(trip),
        }

    async def update_booking_workspace_status(
        self,
        agency_id: str,
        booking_workspace_id: str,
        status: str,
        user: dict,
        internal_notes: str | None = None,
    ) -> dict[str, Any] | None:
        workspace = await self.db.collection("booking_workspaces").find_one(
            {"agency_id": agency_id, "id": booking_workspace_id}
        )
        if workspace is None:
            return None
        updates: dict[str, Any] = {"status": status}
        if internal_notes is not None:
            updates["internal_notes"] = internal_notes
        updated = await self.db.collection("booking_workspaces").update_one(
            {"agency_id": agency_id, "id": booking_workspace_id},
            updates,
        )
        await self._write_timeline(
            agency_id,
            booking_workspace_id,
            "booking_workspace.status_updated",
            "Booking workspace status updated",
            user.get("id"),
            booking_record_id=workspace.get("booking_record_id"),
            trip_id=workspace.get("trip_id"),
            description=f"Status changed from {workspace.get('status')} to {status}.",
            payload_json={"previous_status": workspace.get("status"), "status": status},
        )
        return await self.get_booking_workspace(agency_id, updated["id"])

    async def update_booking_record(
        self,
        agency_id: str,
        booking_record_id: str,
        payload: BookingRecordUpdate,
        user: dict,
    ) -> dict[str, Any] | None:
        record = await self.db.collection("booking_records").find_one(
            {"agency_id": agency_id, "id": booking_record_id}
        )
        if record is None:
            return None
        updates = payload.model_dump(exclude_unset=True, mode="json")
        updated = await self.db.collection("booking_records").update_one(
            {"agency_id": agency_id, "id": booking_record_id},
            updates,
        )
        await self._write_timeline(
            agency_id,
            record["booking_workspace_id"],
            "booking_record.updated",
            "Booking record mirror updated",
            user.get("id"),
            booking_record_id=record["id"],
            trip_id=record.get("trip_id"),
            description="Manual PNR mirror fields were updated without provider execution.",
            payload_json={
                "updated_fields": sorted(updates.keys()),
                "provider_execution_disabled": True,
            },
        )
        return await self.get_booking_workspace(agency_id, record["booking_workspace_id"])

    async def rebuild_booking_record_from_readiness(
        self,
        agency_id: str,
        booking_workspace_id: str,
        user: dict,
    ) -> dict[str, Any] | None:
        workspace = await self.db.collection("booking_workspaces").find_one(
            {"agency_id": agency_id, "id": booking_workspace_id}
        )
        if workspace is None:
            return None
        readiness = await self.db.collection("booking_readiness_packages").find_one(
            {"agency_id": agency_id, "id": workspace.get("booking_readiness_package_id")}
        )
        if readiness is None:
            raise BookingWorkspaceError("Booking readiness package is missing.")
        record = await self.db.collection("booking_records").find_one(
            {"agency_id": agency_id, "booking_workspace_id": booking_workspace_id}
        )
        if record and (
            record.get("booking_status") not in REBUILDABLE_RECORD_STATUSES
            or record.get("provider_status") == BookingRecordProviderStatus.CONFIRMED.value
        ):
            raise BookingWorkspaceError("Booking record can only be rebuilt while draft or pending and before confirmed provider status.")

        if record is None:
            record_model = self._record_from_workspace_readiness(workspace, readiness, user)
            record = await self.db.collection("booking_records").insert_one(
                record_model.model_dump(mode="json")
            )
            await self.db.collection("booking_workspaces").update_one(
                {"agency_id": agency_id, "id": workspace["id"]},
                {"booking_record_id": record["id"]},
            )
        else:
            record = await self.db.collection("booking_records").update_one(
                {"agency_id": agency_id, "id": record["id"]},
                self._record_snapshot_updates(workspace, readiness),
            ) or record

        await self._write_timeline(
            agency_id,
            booking_workspace_id,
            "booking_record.rebuilt_from_readiness",
            "Booking record mirror rebuilt",
            user.get("id"),
            booking_record_id=record["id"],
            trip_id=workspace.get("trip_id"),
            description="Rebuilt internal PNR mirror snapshots from booking readiness without provider execution.",
            payload_json={
                "booking_readiness_package_id": readiness["id"],
                "provider_execution_disabled": True,
            },
        )
        return await self.get_booking_workspace(agency_id, booking_workspace_id)

    async def cancel_booking_workspace(
        self,
        agency_id: str,
        booking_workspace_id: str,
        user: dict,
    ) -> dict[str, Any] | None:
        workspace = await self.db.collection("booking_workspaces").find_one(
            {"agency_id": agency_id, "id": booking_workspace_id}
        )
        if workspace is None:
            return None
        updated_workspace = await self.db.collection("booking_workspaces").update_one(
            {"agency_id": agency_id, "id": booking_workspace_id},
            {"status": BookingWorkspaceStatus.CANCELLED.value},
        )
        record = await self.db.collection("booking_records").find_one(
            {"agency_id": agency_id, "booking_workspace_id": booking_workspace_id}
        )
        updated_record = record
        if record and record.get("booking_status") in REBUILDABLE_RECORD_STATUSES:
            updated_record = await self.db.collection("booking_records").update_one(
                {"agency_id": agency_id, "id": record["id"]},
                {
                    "booking_status": BookingRecordStatus.CANCELLED.value,
                    "provider_status": BookingRecordProviderStatus.CANCELLED.value,
                },
            )
        await self._write_timeline(
            agency_id,
            booking_workspace_id,
            "booking_workspace.cancelled",
            "Booking workspace cancelled",
            user.get("id"),
            booking_record_id=(updated_record or {}).get("id"),
            trip_id=workspace.get("trip_id"),
            description="Cancelled the booking workspace. No provider cancellation was executed.",
            payload_json={"provider_execution_disabled": True},
        )
        return await self.get_booking_workspace(agency_id, updated_workspace["id"])

    async def _existing_active_workspace(
        self,
        agency_id: str,
        booking_readiness_package_id: str,
    ) -> dict[str, Any] | None:
        items = await self.db.collection("booking_workspaces").find_many(
            {"agency_id": agency_id, "booking_readiness_package_id": booking_readiness_package_id}
        )
        return _latest([item for item in items if item.get("status") in ACTIVE_WORKSPACE_STATUSES])

    async def _next_workspace_number(self, agency_id: str) -> str:
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        prefix = f"BKG-{today}-"
        items = await self.db.collection("booking_workspaces").find_many({"agency_id": agency_id})
        sequence = len([item for item in items if str(item.get("workspace_number") or "").startswith(prefix)]) + 1
        return f"{prefix}{sequence:04d}"

    def _status_from_readiness(self, readiness: dict[str, Any]) -> str:
        status = readiness.get("status")
        if status == BookingReadinessStatus.READY.value:
            return BookingWorkspaceStatus.READY_TO_BOOK.value
        if status == BookingReadinessStatus.BLOCKED.value:
            return BookingWorkspaceStatus.BLOCKED.value
        return BookingWorkspaceStatus.DRAFT.value

    def _workspace_title(
        self,
        workspace_number: str,
        trip: dict[str, Any] | None,
        readiness: dict[str, Any],
    ) -> str:
        if trip and trip.get("trip_title"):
            return f"{workspace_number} · {trip['trip_title']}"
        if trip and trip.get("trip_reference"):
            return f"{workspace_number} · {trip['trip_reference']}"
        return f"{workspace_number} · Trip {readiness.get('trip_id')}"

    async def _source_snapshot(
        self,
        agency_id: str,
        readiness: dict[str, Any],
        acceptance: dict[str, Any] | None,
        trip: dict[str, Any] | None,
    ) -> dict[str, Any]:
        trip_snapshot = None
        if readiness.get("acceptance_id"):
            trip_snapshot = await self.db.collection("trip_accepted_offer_snapshots").find_one(
                {"agency_id": agency_id, "acceptance_id": readiness["acceptance_id"]}
            )
        return {
            "phase": PHASE_LABEL,
            "snapshotted_at": _now_iso(),
            "provider_execution_disabled": True,
            "booking_readiness_package": readiness,
            "accepted_offer": acceptance,
            "trip_accepted_offer_snapshot": trip_snapshot,
            "trip": _summary_from_trip(trip),
        }

    def _record_from_workspace_readiness(
        self,
        workspace: dict[str, Any],
        readiness: dict[str, Any],
        user: dict,
    ) -> BookingRecord:
        return BookingRecord(
            agency_id=workspace["agency_id"],
            booking_workspace_id=workspace["id"],
            trip_id=workspace["trip_id"],
            request_id=workspace.get("request_id"),
            booking_readiness_package_id=readiness["id"],
            offer_acceptance_id=readiness.get("acceptance_id"),
            provider=workspace.get("provider_target") or BookingProviderTarget.MANUAL.value,
            provider_status=BookingRecordProviderStatus.DRAFT,
            booking_status=BookingRecordStatus.DRAFT,
            passengers_json=readiness.get("passengers_snapshot_json") or [],
            segments_json=readiness.get("segments_snapshot_json") or [],
            pricing_json=readiness.get("pricing_snapshot_json") or {},
            services_json=readiness.get("services_snapshot_json") or {},
            pets_json=readiness.get("pets_snapshot_json") or {},
            special_items_json=readiness.get("special_items_snapshot_json") or {},
            ssr_json=readiness.get("ssr_json") or [],
            osi_json=readiness.get("osi_json") or [],
            internal_pnr_mirror_json=self._internal_pnr_mirror(workspace, readiness),
            warnings_json=readiness.get("warnings_json") or [],
            internal_notes=workspace.get("internal_notes"),
            created_by_user_id=user.get("id"),
        )

    def _record_snapshot_updates(
        self,
        workspace: dict[str, Any],
        readiness: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "passengers_json": readiness.get("passengers_snapshot_json") or [],
            "segments_json": readiness.get("segments_snapshot_json") or [],
            "pricing_json": readiness.get("pricing_snapshot_json") or {},
            "services_json": readiness.get("services_snapshot_json") or {},
            "pets_json": readiness.get("pets_snapshot_json") or {},
            "special_items_json": readiness.get("special_items_snapshot_json") or {},
            "ssr_json": readiness.get("ssr_json") or [],
            "osi_json": readiness.get("osi_json") or [],
            "internal_pnr_mirror_json": self._internal_pnr_mirror(workspace, readiness),
            "warnings_json": readiness.get("warnings_json") or [],
        }

    def _internal_pnr_mirror(self, workspace: dict[str, Any], readiness: dict[str, Any]) -> dict[str, Any]:
        return {
            "phase": PHASE_LABEL,
            "mirrored_at": _now_iso(),
            "provider_execution_disabled": True,
            "booking_workspace_id": workspace.get("id"),
            "booking_readiness_package_id": readiness.get("id"),
            "provider_target": workspace.get("provider_target"),
            "status": "draft",
            "passengers": readiness.get("passengers_snapshot_json") or [],
            "segments": readiness.get("segments_snapshot_json") or [],
            "pricing": readiness.get("pricing_snapshot_json") or {},
            "services": readiness.get("services_snapshot_json") or {},
            "pets": readiness.get("pets_snapshot_json") or {},
            "special_items": readiness.get("special_items_snapshot_json") or {},
            "ssr": readiness.get("ssr_json") or [],
            "osi": readiness.get("osi_json") or [],
            "required_documents": readiness.get("required_documents_json") or [],
            "warnings": readiness.get("warnings_json") or [],
        }

    async def _write_timeline(
        self,
        agency_id: str,
        booking_workspace_id: str,
        event_type: str,
        title: str,
        actor_user_id: str | None,
        *,
        booking_record_id: str | None = None,
        trip_id: str | None = None,
        description: str | None = None,
        payload_json: dict[str, Any] | None = None,
    ) -> None:
        event = BookingTimelineEvent(
            agency_id=agency_id,
            booking_workspace_id=booking_workspace_id,
            booking_record_id=booking_record_id,
            trip_id=trip_id,
            event_type=event_type,
            actor_user_id=actor_user_id,
            title=title,
            description=description,
            summary=description,
            payload_json=payload_json or {},
            metadata=payload_json or {},
        )
        await self.db.collection("booking_timeline_events").insert_one(event.model_dump(mode="json"))
