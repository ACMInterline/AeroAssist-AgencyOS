from __future__ import annotations

from datetime import date, datetime, timezone
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
    BookingSourceContext,
    BookingTimelineEvent,
    BookingWorkspace,
    BookingWorkspaceMetadataCreate,
    BookingWorkspaceMetadataUpdate,
    BookingWorkspaceStatus,
    ManualBookingWorkspaceCreate,
    TripTimelineEvent,
    new_id,
)


PHASE_LABEL = "phase_41_6_booking_workspace_foundation"
BOOKING_WORKSPACE_COLLECTION = "booking_workspaces"
BOOKING_WORKSPACE_STATUSES = [
    BookingWorkspaceStatus.DRAFT.value,
    BookingWorkspaceStatus.READY_TO_BOOK.value,
    BookingWorkspaceStatus.BOOKING_IN_PROGRESS.value,
    BookingWorkspaceStatus.BOOKED.value,
    BookingWorkspaceStatus.BLOCKED.value,
    BookingWorkspaceStatus.CANCELLED.value,
]
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


def _summary_from_offer_workspace(workspace: dict[str, Any] | None) -> dict[str, Any] | None:
    if not workspace:
        return None
    return {
        "id": workspace.get("id"),
        "title": workspace.get("title"),
        "status": workspace.get("status"),
        "currency": workspace.get("currency"),
        "request_id": workspace.get("request_id"),
        "trip_id": workspace.get("trip_id"),
    }


def _summary_from_booking_workspace(workspace: dict[str, Any] | None) -> dict[str, Any] | None:
    if not workspace:
        return None
    return {
        "id": workspace.get("id"),
        "workspace_number": workspace.get("workspace_number"),
        "title": workspace.get("title"),
        "status": workspace.get("status"),
        "provider_target": workspace.get("provider_target"),
        "booking_record_id": workspace.get("booking_record_id"),
    }


class BookingWorkspaceService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_platform_metadata_workspaces(
        self,
        *,
        agency_id: str | None = None,
        booking_status: str | None = None,
        booking_owner: str | None = None,
        airline: str | None = None,
        supplier: str | None = None,
        booking_date: date | str | None = None,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if agency_id:
            filters["agency_id"] = agency_id
        if booking_status:
            filters["booking_status"] = booking_status
        if booking_owner:
            filters["booking_owner"] = booking_owner
        if supplier:
            filters["supplier_reference"] = supplier
        workspaces = await self.db.collection(BOOKING_WORKSPACE_COLLECTION).find_many(filters or None)
        if booking_status:
            workspaces = [
                item
                for item in workspaces
                if (item.get("booking_status") or item.get("status") or BookingWorkspaceStatus.DRAFT.value) == booking_status
            ]
        if not include_archived:
            workspaces = [
                item
                for item in workspaces
                if not item.get("deleted_at")
                and (item.get("booking_status") or item.get("status")) != BookingWorkspaceStatus.CANCELLED.value
            ]
        if airline:
            workspaces = [item for item in workspaces if self._airline_matches(item, airline)]
        if booking_date:
            target = self._parse_date(booking_date)
            workspaces = [item for item in workspaces if self._date_matches(item.get("booking_created_date"), target)]
        workspaces.sort(key=lambda item: self._sort_text(item.get("updated_at") or item.get("created_at")), reverse=True)
        return [await self._platform_metadata_projection(item) for item in workspaces]

    async def list_agency_metadata_workspaces(
        self,
        agency_id: str,
        *,
        booking_status: str | None = None,
        booking_owner: str | None = None,
        airline: str | None = None,
        supplier: str | None = None,
        booking_date: date | str | None = None,
    ) -> list[dict[str, Any]]:
        items = await self.list_platform_metadata_workspaces(
            agency_id=agency_id,
            booking_status=booking_status,
            booking_owner=booking_owner,
            airline=airline,
            supplier=supplier,
            booking_date=booking_date,
        )
        return [self._agency_metadata_projection(item) for item in items if item.get("agency_id") == agency_id]

    async def platform_metadata_response(
        self,
        *,
        agency_id: str | None = None,
        booking_status: str | None = None,
        booking_owner: str | None = None,
        airline: str | None = None,
        supplier: str | None = None,
        booking_date: date | str | None = None,
        include_archived: bool = False,
    ) -> dict[str, Any]:
        items = await self.list_platform_metadata_workspaces(
            agency_id=agency_id,
            booking_status=booking_status,
            booking_owner=booking_owner,
            airline=airline,
            supplier=supplier,
            booking_date=booking_date,
            include_archived=include_archived,
        )
        return {
            "phase": PHASE_LABEL,
            "items": items,
            "booking_workspace_count": len(items),
            "summary": self.summarize_metadata_counts(items),
            "filters": self.filter_metadata(),
            "read_only": False,
            "metadata_only": True,
            "notice": "Booking workspaces are metadata only. They do not create live bookings, issue tickets, connect to GDS or NDC, call airline APIs, process payments, calculate fares, use AI, run workers, automatically confirm bookings, automatically generate tickets, or integrate external providers.",
            **self.safety_flags(),
        }

    async def agency_metadata_response(
        self,
        agency_id: str,
        *,
        booking_status: str | None = None,
        booking_owner: str | None = None,
        airline: str | None = None,
        supplier: str | None = None,
        booking_date: date | str | None = None,
    ) -> dict[str, Any]:
        items = await self.list_agency_metadata_workspaces(
            agency_id,
            booking_status=booking_status,
            booking_owner=booking_owner,
            airline=airline,
            supplier=supplier,
            booking_date=booking_date,
        )
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "items": items,
            "booking_workspace_count": len(items),
            "summary": self.summarize_metadata_counts(items),
            "filters": self.filter_metadata(),
            "read_only": True,
            "metadata_only": True,
            "notice": "Booking workspace metadata is read-only for this agency. It does not create live bookings, issue tickets, connect to GDS or NDC, call airline APIs, process payments, calculate fares, use AI, run workers, automatically confirm bookings, automatically generate tickets, or integrate external providers.",
            **self.safety_flags(),
        }

    async def platform_metadata_summary(self) -> dict[str, Any]:
        items = await self.list_platform_metadata_workspaces(include_archived=True)
        return {
            "phase": PHASE_LABEL,
            "summary": self.summarize_metadata_counts(items),
            "booking_workspace_count": len(items),
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def agency_metadata_summary(self, agency_id: str) -> dict[str, Any]:
        items = await self.list_agency_metadata_workspaces(agency_id)
        return {
            "phase": PHASE_LABEL,
            "agency_id": agency_id,
            "summary": self.summarize_metadata_counts(items),
            "booking_workspace_count": len(items),
            "read_only": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def get_platform_metadata_workspace(self, booking_workspace_id: str) -> dict[str, Any]:
        workspace = await self._require_metadata_workspace(booking_workspace_id)
        return await self._platform_metadata_projection(workspace)

    async def get_agency_metadata_workspace(self, agency_id: str, booking_workspace_id: str) -> dict[str, Any]:
        workspace = await self.get_platform_metadata_workspace(booking_workspace_id)
        if workspace.get("agency_id") != agency_id:
            raise BookingWorkspaceError("Booking workspace metadata was not found for this agency.")
        return self._agency_metadata_projection(workspace)

    async def create_metadata_booking_workspace(
        self,
        payload: BookingWorkspaceMetadataCreate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        data = self._payload_dict(payload)
        status = data.get("booking_status") or BookingWorkspaceStatus.DRAFT.value
        self._validate_metadata_status(status)
        reference = data.get("booking_reference") or self._booking_reference()
        workspace = BookingWorkspace(
            id=data.get("id") or new_id(),
            agency_id=data["agency_id"],
            operational_workspace_id=data.get("operational_workspace_id"),
            trip_workspace_id=data.get("trip_workspace_id"),
            offer_workspace_id=data.get("offer_workspace_id"),
            source_context=BookingSourceContext.STANDALONE_MANUAL,
            passenger_ids=data.get("passenger_ids") or [],
            flight_workspace_ids=data.get("flight_workspace_ids") or [],
            workspace_number=reference,
            booking_reference=reference,
            title=self._booking_display_name(data, reference),
            status=status,
            booking_status=status,
            booking_type=data.get("booking_type"),
            booking_source=data.get("booking_source"),
            booking_owner=data.get("booking_owner"),
            airline_pnr=data.get("airline_pnr"),
            gds_record_locator=data.get("gds_record_locator"),
            supplier_reference=data.get("supplier_reference"),
            booking_created_date=data.get("booking_created_date"),
            booking_deadline=data.get("booking_deadline"),
            provider_target=BookingProviderTarget.MANUAL,
            ticket_ids=data.get("ticket_ids") or [],
            emd_ids=data.get("emd_ids") or [],
            ssr_ids=data.get("ssr_ids") or [],
            osi_ids=data.get("osi_ids") or [],
            document_ids=data.get("document_ids") or [],
            timeline_ids=data.get("timeline_ids") or [],
            communication_ids=data.get("communication_ids") or [],
            payment_summary=data.get("payment_summary"),
            booking_summary=data.get("booking_summary"),
            operational_notes=data.get("operational_notes"),
            internal_notes=data.get("operational_notes"),
            created_by_user_id=(user or {}).get("id"),
            metadata=data.get("metadata") or {},
        )
        stored = await self.db.collection(BOOKING_WORKSPACE_COLLECTION).insert_one(workspace.model_dump(mode="json"))
        return {
            "phase": PHASE_LABEL,
            "booking_workspace": await self._platform_metadata_projection(stored),
            "metadata_only": True,
            "notice": "Booking workspace metadata was saved only. No live booking, ticketing, GDS/NDC, airline API, payment, fare calculation, AI, worker, automatic confirmation, automatic ticket generation, provider, or external integration action ran.",
            **self.safety_flags(),
        }

    async def update_metadata_booking_workspace(
        self,
        booking_workspace_id: str,
        payload: BookingWorkspaceMetadataUpdate | dict[str, Any],
        user: dict | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_metadata_workspace(booking_workspace_id)
        updates = {key: value for key, value in self._payload_dict(payload).items() if value is not None}
        if "booking_status" in updates:
            self._validate_metadata_status(updates["booking_status"])
            updates["status"] = updates["booking_status"]
        if "booking_reference" in updates:
            updates["workspace_number"] = updates["booking_reference"]
        if "operational_notes" in updates:
            updates["internal_notes"] = updates["operational_notes"]
        updates.update(
            {
                "updated_at": self._now(),
                "metadata_only": True,
                "booking_workspace_metadata_only": True,
                "updated_by_user_id": (user or {}).get("id"),
            }
        )
        updated = await self.db.collection(BOOKING_WORKSPACE_COLLECTION).update_one({"id": existing["id"]}, updates)
        stored = updated or {**existing, **updates}
        return {
            "phase": PHASE_LABEL,
            "booking_workspace": await self._platform_metadata_projection(stored),
            "metadata_only": True,
            "notice": "Booking workspace metadata was updated only. No live booking, ticketing, GDS/NDC, airline API, payment, fare calculation, AI, worker, automatic confirmation, automatic ticket generation, provider, or external integration action ran.",
            **self.safety_flags(),
        }

    async def delete_metadata_booking_workspace(
        self,
        booking_workspace_id: str,
        user: dict | None = None,
    ) -> dict[str, Any]:
        existing = await self._require_metadata_workspace(booking_workspace_id)
        updates = {
            "status": BookingWorkspaceStatus.CANCELLED.value,
            "booking_status": BookingWorkspaceStatus.CANCELLED.value,
            "deleted_at": self._now(),
            "updated_by_user_id": (user or {}).get("id"),
            "metadata_only": True,
            "booking_workspace_metadata_only": True,
            "booking_workspace_archived_metadata_only": True,
        }
        updated = await self.db.collection(BOOKING_WORKSPACE_COLLECTION).update_one({"id": existing["id"]}, updates)
        stored = updated or {**existing, **updates}
        return {
            "phase": PHASE_LABEL,
            "booking_workspace": await self._platform_metadata_projection(stored),
            "deleted": True,
            "metadata_only": True,
            "notice": "Booking workspace metadata was archived only. No live booking, ticketing, GDS/NDC, airline API, payment, fare calculation, AI, worker, automatic confirmation, automatic ticket generation, provider, or external integration action ran.",
            **self.safety_flags(),
        }

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
            source_context=BookingSourceContext.OFFER_READINESS,
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

    async def create_manual_booking_workspace(
        self,
        agency_id: str,
        payload: ManualBookingWorkspaceCreate,
        user: dict,
    ) -> dict[str, Any]:
        source_context = _as_value(payload.source_context or BookingSourceContext.STANDALONE_MANUAL.value)
        if source_context not in {
            BookingSourceContext.STANDALONE_MANUAL.value,
            BookingSourceContext.EXISTING_TRIP_CHANGE.value,
            BookingSourceContext.IMPORTED_GDS.value,
            BookingSourceContext.IMPORTED_CONFIRMATION.value,
        }:
            raise BookingWorkspaceError("Manual booking workspace source context is not supported.")
        trip = None
        if payload.trip_id:
            trip = await self.db.collection("trip_dossiers").find_one({"agency_id": agency_id, "id": payload.trip_id})
            if trip is None:
                trip = await self.db.collection("trip_dossiers").find_one({"agency_id": agency_id, "trip_reference": payload.trip_id})
            if trip is None:
                raise BookingWorkspaceError("Trip dossier not found for manual booking workspace.")
        trip_id = (trip or {}).get("id") or payload.trip_id

        workspace_number = await self._next_workspace_number(agency_id)
        title = payload.title or self._manual_workspace_title(workspace_number, trip, payload.pnr_locator)
        provider_target = _as_value(payload.provider_target or BookingProviderTarget.MANUAL.value)
        source_snapshot = {
            "phase": PHASE_LABEL,
            "source_context": source_context,
            "snapshotted_at": _now_iso(),
            "provider_execution_disabled": True,
            "manual_entry": True,
            "trip": _summary_from_trip(trip),
            "import_draft_id": payload.import_draft_id,
            "trip_change_operation_id": payload.trip_change_operation_id,
        }
        workspace = BookingWorkspace(
            agency_id=agency_id,
            source_context=source_context,
            client_id=payload.client_id,
            passenger_ids=payload.passenger_ids or [],
            trip_id=trip_id,
            booking_readiness_package_id=None,
            import_draft_id=payload.import_draft_id,
            trip_change_operation_id=payload.trip_change_operation_id,
            workspace_number=workspace_number,
            title=title,
            status=BookingWorkspaceStatus.DRAFT,
            provider_target=provider_target,
            source_snapshot_json=source_snapshot,
            passengers_snapshot_json=payload.passengers_json or [],
            segments_snapshot_json=payload.segments_json or [],
            pricing_snapshot_json=payload.pricing_json or {},
            services_snapshot_json=payload.services_json or {},
            pets_snapshot_json=payload.pets_json or {},
            special_items_snapshot_json=payload.special_items_json or {},
            warnings_json=[],
            ssr_json=payload.ssr_json or [],
            osi_json=payload.osi_json or [],
            internal_notes=payload.internal_notes,
            created_by_user_id=user.get("id"),
        )
        created_workspace = await self.db.collection("booking_workspaces").insert_one(workspace.model_dump(mode="json"))

        created_record = None
        if payload.create_draft_record:
            record = BookingRecord(
                agency_id=agency_id,
                booking_workspace_id=created_workspace["id"],
                source_context=source_context,
                client_id=payload.client_id,
                passenger_ids=payload.passenger_ids or [],
                trip_id=trip_id,
                import_draft_id=payload.import_draft_id,
                trip_change_operation_id=payload.trip_change_operation_id,
                original_booking_record_id=payload.original_booking_record_id,
                revision_reason=payload.revision_reason,
                pnr_locator=payload.pnr_locator,
                provider=provider_target,
                provider_status=BookingRecordProviderStatus.DRAFT,
                booking_status=BookingRecordStatus.DRAFT,
                passengers_json=payload.passengers_json or [],
                segments_json=payload.segments_json or [],
                pricing_json=payload.pricing_json or {},
                services_json=payload.services_json or {},
                pets_json=payload.pets_json or {},
                special_items_json=payload.special_items_json or {},
                ssr_json=payload.ssr_json or [],
                osi_json=payload.osi_json or [],
                internal_pnr_mirror_json=self._internal_manual_pnr_mirror(created_workspace, payload, provider_target, source_context),
                warnings_json=[],
                internal_notes=payload.internal_notes,
                created_by_user_id=user.get("id"),
            )
            created_record = await self.db.collection("booking_records").insert_one(record.model_dump(mode="json"))
            created_workspace = await self.db.collection("booking_workspaces").update_one(
                {"agency_id": agency_id, "id": created_workspace["id"]},
                {"booking_record_id": created_record["id"]},
            ) or created_workspace

        await self._write_timeline(
            agency_id,
            created_workspace["id"],
            "booking_workspace.created_manual",
            "Manual booking workspace created",
            user.get("id"),
            booking_record_id=(created_record or {}).get("id"),
            trip_id=trip_id,
            description="Created an internal booking workspace and PNR mirror without provider execution.",
            payload_json={
                "source_context": source_context,
                "provider_execution_disabled": True,
                "import_draft_id": payload.import_draft_id,
                "trip_change_operation_id": payload.trip_change_operation_id,
            },
        )
        if trip_id:
            await self._write_trip_timeline(
                agency_id,
                trip_id,
                user.get("id"),
                "trip.booking_workspace_created_manual",
                "Manual booking workspace created",
                f"{created_workspace.get('workspace_number')} linked to this trip.",
                {
                    "booking_workspace_id": created_workspace["id"],
                    "booking_record_id": (created_record or {}).get("id"),
                    "source_context": source_context,
                    "provider_execution_disabled": True,
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

    async def list_eligible_booking_readiness_packages(self, agency_id: str) -> dict[str, Any]:
        packages = await self.db.collection("booking_readiness_packages").find_many({"agency_id": agency_id})
        eligible_statuses = {
            BookingReadinessStatus.DRAFT.value,
            BookingReadinessStatus.READY.value,
            BookingReadinessStatus.BLOCKED.value,
        }
        packages = [item for item in packages if item.get("status") in eligible_statuses]

        trips = {
            item["id"]: item
            for item in await self.db.collection("trip_dossiers").find_many({"agency_id": agency_id})
        }
        acceptances = {
            item["id"]: item
            for item in await self.db.collection("offer_acceptances").find_many({"agency_id": agency_id})
        }
        offer_workspaces = {
            item["id"]: item
            for item in await self.db.collection("offer_workspaces").find_many({"agency_id": agency_id})
        }
        booking_workspaces = await self.db.collection("booking_workspaces").find_many({"agency_id": agency_id})

        active_by_package: dict[str, dict[str, Any]] = {}
        for workspace in booking_workspaces:
            package_id = workspace.get("booking_readiness_package_id")
            if not package_id or workspace.get("status") not in ACTIVE_WORKSPACE_STATUSES:
                continue
            current = active_by_package.get(package_id)
            active_by_package[package_id] = _latest([item for item in [current, workspace] if item]) or workspace

        items: list[dict[str, Any]] = []
        for package in packages:
            existing_workspace = active_by_package.get(package["id"])
            acceptance = acceptances.get(package.get("acceptance_id"))
            offer_workspace = offer_workspaces.get(package.get("workspace_id"))
            items.append(
                {
                    "id": package["id"],
                    "booking_readiness_package_id": package["id"],
                    "trip_id": package.get("trip_id"),
                    "request_id": package.get("request_id"),
                    "workspace_id": package.get("workspace_id"),
                    "option_id": package.get("option_id"),
                    "acceptance_id": package.get("acceptance_id"),
                    "status": package.get("status"),
                    "provider_target": package.get("provider_target"),
                    "warning_count": len(package.get("warnings_json") or []),
                    "policy_violation_count": len(package.get("policy_violations_json") or []),
                    "required_document_count": len(package.get("required_documents_json") or []),
                    "created_at": package.get("created_at"),
                    "updated_at": package.get("updated_at"),
                    "trip_summary": _summary_from_trip(trips.get(package.get("trip_id"))),
                    "accepted_offer_summary": _summary_from_acceptance(acceptance),
                    "offer_workspace_summary": _summary_from_offer_workspace(offer_workspace),
                    "workspace_summary": _summary_from_offer_workspace(offer_workspace),
                    "booking_workspace_already_exists": existing_workspace is not None,
                    "booking_workspace_id": (existing_workspace or {}).get("id"),
                    "booking_workspace_summary": _summary_from_booking_workspace(existing_workspace),
                    "can_create_booking_workspace": existing_workspace is None,
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

    def summarize_metadata_counts(self, items: list[dict[str, Any]]) -> dict[str, Any]:
        by_status = {status: 0 for status in BOOKING_WORKSPACE_STATUSES}
        by_type: dict[str, int] = {}
        by_source: dict[str, int] = {}
        by_supplier: dict[str, int] = {}
        agency_ids: set[str] = set()
        owners: set[str] = set()
        airlines: set[str] = set()
        operational_workspace_ids: set[str] = set()
        trip_workspace_ids: set[str] = set()
        offer_workspace_ids: set[str] = set()
        linked_counts = {
            "passenger_count": 0,
            "flight_workspace_count": 0,
            "ticket_count": 0,
            "emd_count": 0,
            "ssr_count": 0,
            "osi_count": 0,
            "document_count": 0,
            "timeline_count": 0,
            "communication_count": 0,
        }
        for item in items:
            status = item.get("booking_status") or item.get("status") or BookingWorkspaceStatus.DRAFT.value
            by_status[status] = by_status.get(status, 0) + 1
            self._count_value(by_type, item.get("booking_type"))
            self._count_value(by_source, item.get("booking_source"))
            self._count_value(by_supplier, item.get("supplier_reference"))
            if item.get("agency_id"):
                agency_ids.add(item["agency_id"])
            if item.get("booking_owner"):
                owners.add(item["booking_owner"])
            if item.get("airline_pnr"):
                airlines.add(item["airline_pnr"])
            if item.get("operational_workspace_id"):
                operational_workspace_ids.add(item["operational_workspace_id"])
            if item.get("trip_workspace_id") or item.get("trip_id"):
                trip_workspace_ids.add(item.get("trip_workspace_id") or item.get("trip_id"))
            if item.get("offer_workspace_id"):
                offer_workspace_ids.add(item["offer_workspace_id"])
            linked_counts["passenger_count"] += self._list_count(item.get("passenger_ids"))
            linked_counts["flight_workspace_count"] += self._list_count(item.get("flight_workspace_ids"))
            linked_counts["ticket_count"] += self._list_count(item.get("ticket_ids"))
            linked_counts["emd_count"] += self._list_count(item.get("emd_ids"))
            linked_counts["ssr_count"] += self._list_count(item.get("ssr_ids") or item.get("ssr_json"))
            linked_counts["osi_count"] += self._list_count(item.get("osi_ids") or item.get("osi_json"))
            linked_counts["document_count"] += self._list_count(item.get("document_ids") or item.get("required_documents_json"))
            linked_counts["timeline_count"] += self._list_count(item.get("timeline_ids"))
            linked_counts["communication_count"] += self._list_count(item.get("communication_ids"))
        return {
            "total_count": len(items),
            "by_status": by_status,
            "by_type": by_type,
            "by_source": by_source,
            "by_supplier": by_supplier,
            "agency_count": len(agency_ids),
            "booking_owner_count": len(owners),
            "airline_count": len(airlines),
            "operational_workspace_count": len(operational_workspace_ids),
            "trip_workspace_count": len(trip_workspace_ids),
            "offer_workspace_count": len(offer_workspace_ids),
            **linked_counts,
            "metadata_only": True,
            **self.safety_flags(),
        }

    def filter_metadata(self) -> dict[str, Any]:
        return {
            "statuses": BOOKING_WORKSPACE_STATUSES,
            "supports_booking_status_filter": True,
            "supports_booking_owner_filter": True,
            "supports_airline_filter": True,
            "supports_supplier_filter": True,
            "supports_booking_date_filter": True,
            "metadata_only": True,
            **self.safety_flags(),
        }

    async def _platform_metadata_projection(self, workspace: dict[str, Any]) -> dict[str, Any]:
        projected = dict(workspace)
        projected["booking_reference"] = projected.get("booking_reference") or projected.get("workspace_number") or projected.get("id")
        projected["booking_status"] = projected.get("booking_status") or projected.get("status") or BookingWorkspaceStatus.DRAFT.value
        projected["booking_display_name"] = self._booking_display_name(projected, projected["booking_reference"])
        projected["agency"] = await self._agency_context(projected.get("agency_id"))
        projected["agency_name"] = projected["agency"].get("agency_name")
        projected["operational_workspace"] = await self._operational_workspace_context(projected.get("operational_workspace_id"))
        projected["trip_workspace"] = await self._trip_workspace_context(
            projected.get("agency_id"),
            projected.get("trip_workspace_id") or projected.get("trip_id"),
        )
        projected["offer_workspace"] = await self._offer_workspace_context(projected.get("agency_id"), projected.get("offer_workspace_id"))
        projected["passengers"] = [
            await self._passenger_context(projected.get("agency_id"), passenger_id)
            for passenger_id in projected.get("passenger_ids") or []
        ]
        projected["flight_workspaces"] = [
            await self._flight_workspace_context(projected.get("agency_id"), flight_workspace_id)
            for flight_workspace_id in projected.get("flight_workspace_ids") or []
        ]
        projected["tickets"] = [
            await self._ticket_context(projected.get("agency_id"), ticket_id)
            for ticket_id in projected.get("ticket_ids") or []
        ]
        projected["emds"] = [
            await self._emd_context(projected.get("agency_id"), emd_id)
            for emd_id in projected.get("emd_ids") or []
        ]
        projected["ssrs"] = [
            await self._generic_reference_context("ssr_id", ssr_id)
            for ssr_id in projected.get("ssr_ids") or []
        ]
        projected["osis"] = [
            await self._generic_reference_context("osi_id", osi_id)
            for osi_id in projected.get("osi_ids") or []
        ]
        projected["documents"] = [
            await self._document_context(projected.get("agency_id"), document_id)
            for document_id in projected.get("document_ids") or []
        ]
        projected["timeline"] = await self._timeline_context(projected)
        projected["communications"] = [
            await self._generic_reference_context("communication_id", communication_id)
            for communication_id in projected.get("communication_ids") or []
        ]
        record = None
        if projected.get("booking_record_id"):
            record = await self.db.collection("booking_records").find_one(
                {"agency_id": projected.get("agency_id"), "id": projected.get("booking_record_id")}
            )
        record = record or await self.db.collection("booking_records").find_one(
            {"agency_id": projected.get("agency_id"), "booking_workspace_id": projected.get("id")}
        )
        projected["booking_record"] = record
        projected["trip_summary"] = projected["trip_workspace"]
        projected["warning_count"] = len(projected.get("warnings_json") or [])
        projected["policy_violation_count"] = len(projected.get("policy_violations_json") or [])
        projected["read_only"] = False
        projected["metadata_only"] = True
        projected["booking_workspace_metadata_only"] = True
        projected.update(self.safety_flags())
        return projected

    def _agency_metadata_projection(self, item: dict[str, Any]) -> dict[str, Any]:
        projected = dict(item)
        projected["read_only"] = True
        projected["metadata_only"] = True
        projected["booking_workspace_metadata_only"] = True
        projected.update(self.safety_flags())
        return projected

    async def _require_metadata_workspace(self, booking_workspace_id: str) -> dict[str, Any]:
        workspace = await self.db.collection(BOOKING_WORKSPACE_COLLECTION).find_one({"id": booking_workspace_id})
        if not workspace:
            workspace = await self.db.collection(BOOKING_WORKSPACE_COLLECTION).find_one({"booking_reference": booking_workspace_id})
        if not workspace:
            workspace = await self.db.collection(BOOKING_WORKSPACE_COLLECTION).find_one({"workspace_number": booking_workspace_id})
        if not workspace:
            raise BookingWorkspaceError("Booking workspace metadata was not found.")
        return workspace

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
        workspace = await self.db.collection("operational_travel_workspaces").find_one({"id": workspace_id})
        if not workspace:
            workspace = await self.db.collection("operational_travel_workspaces").find_one({"workspace_reference": workspace_id})
        if not workspace:
            return {"operational_workspace_id": workspace_id, "workspace_reference": workspace_id, "workspace_title": workspace_id, "metadata_only": True}
        return {
            "operational_workspace_id": workspace.get("id"),
            "workspace_reference": workspace.get("workspace_reference"),
            "workspace_title": workspace.get("workspace_title"),
            "workspace_type": workspace.get("workspace_type"),
            "workspace_status": workspace.get("workspace_status"),
            "metadata_only": True,
        }

    async def _trip_workspace_context(self, agency_id: str | None, trip_workspace_id: str | None) -> dict[str, Any]:
        item = await self._lookup_agency_record("trip_workspaces", agency_id, trip_workspace_id, ["trip_reference"])
        if not item:
            item = await self._lookup_agency_record("trip_dossiers", agency_id, trip_workspace_id, ["trip_reference"])
        return self._compact_context("trip_workspace_id", trip_workspace_id, item, ["trip_reference", "trip_status", "trip_title", "destination_city"], "trip_status")

    async def _offer_workspace_context(self, agency_id: str | None, offer_workspace_id: str | None) -> dict[str, Any]:
        item = await self._lookup_agency_record("offer_workspaces_v2", agency_id, offer_workspace_id, ["offer_reference"])
        if not item:
            item = await self._lookup_agency_record("offer_workspaces", agency_id, offer_workspace_id, ["workspace_reference", "offer_reference"])
        return self._compact_context("offer_workspace_id", offer_workspace_id, item, ["offer_reference", "offer_title", "title"], "offer_status")

    async def _passenger_context(self, agency_id: str | None, passenger_id: str | None) -> dict[str, Any]:
        item = await self._lookup_agency_record("passenger_workspaces", agency_id, passenger_id, ["passenger_reference"])
        if not item:
            item = await self._lookup_agency_record("passengers", agency_id, passenger_id, ["passenger_reference"])
        return self._compact_context("passenger_id", passenger_id, item, ["passenger_reference", "preferred_name", "first_name", "last_name"], "passenger_status")

    async def _flight_workspace_context(self, agency_id: str | None, flight_workspace_id: str | None) -> dict[str, Any]:
        item = await self._lookup_agency_record("flight_workspaces", agency_id, flight_workspace_id, ["flight_reference"])
        return self._compact_context("flight_workspace_id", flight_workspace_id, item, ["flight_reference", "flight_number", "airline_code"], "flight_status")

    async def _ticket_context(self, agency_id: str | None, ticket_id: str | None) -> dict[str, Any]:
        item = await self._lookup_agency_record("ticket_records", agency_id, ticket_id, ["ticket_number", "document_number"])
        if not item:
            item = await self._lookup_agency_record("tickets", agency_id, ticket_id, ["ticket_number", "document_number"])
        return self._compact_context("ticket_id", ticket_id, item, ["ticket_number", "document_number", "title"], "status")

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

    async def _timeline_context(self, workspace: dict[str, Any]) -> list[dict[str, Any]]:
        if workspace.get("timeline_ids"):
            return [
                await self._generic_reference_context("timeline_id", timeline_id)
                for timeline_id in workspace.get("timeline_ids") or []
            ]
        events = await self.db.collection("booking_timeline_events").find_many(
            {"agency_id": workspace.get("agency_id"), "booking_workspace_id": workspace.get("id")}
        )
        events.sort(key=lambda item: self._sort_text(item.get("created_at")), reverse=True)
        return [
            {
                "timeline_id": event.get("id"),
                "label": event.get("title") or event.get("event_type"),
                "status": event.get("event_type"),
                "created_at": event.get("created_at"),
                "metadata_only": True,
            }
            for event in events
        ]

    async def _generic_reference_context(self, id_key: str, reference_id: str | None) -> dict[str, Any]:
        return {id_key: reference_id, "label": reference_id, "status": None, "metadata_only": True}

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
            "status": item.get(status_key),
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

    def _booking_display_name(self, item: dict[str, Any], fallback_reference: str | None = None) -> str:
        if item.get("booking_summary"):
            return str(item["booking_summary"])
        if item.get("title"):
            return str(item["title"])
        return item.get("booking_reference") or fallback_reference or item.get("id") or "Booking workspace"

    def _airline_matches(self, item: dict[str, Any], airline: str) -> bool:
        needle = airline.strip().lower()
        haystack = " ".join(
            str(item.get(key) or "")
            for key in [
                "airline_pnr",
                "booking_summary",
                "supplier_reference",
                "source_snapshot_json",
                "segments_snapshot_json",
            ]
        ).lower()
        return needle in haystack

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
        raise ValueError("A booking date filter requires an ISO date.")

    def _count_value(self, target: dict[str, int], value: Any) -> None:
        if value:
            target[str(value)] = target.get(str(value), 0) + 1

    def _list_count(self, value: Any) -> int:
        if not value:
            return 0
        if isinstance(value, list):
            return len(value)
        return 1

    def _validate_metadata_status(self, value: str) -> None:
        if value not in BOOKING_WORKSPACE_STATUSES:
            raise BookingWorkspaceError("Unsupported booking workspace status.")

    def _booking_reference(self) -> str:
        return f"BKGW-{new_id()[:8].upper()}"

    def _payload_dict(self, payload: Any) -> dict[str, Any]:
        if hasattr(payload, "model_dump"):
            return payload.model_dump(mode="json", exclude_unset=True, exclude_none=True)
        return {key: value for key, value in dict(payload).items() if value is not None}

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _sort_text(self, value: Any) -> str:
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value or "")

    def safety_flags(self) -> dict[str, bool]:
        return {
            "metadata_only": True,
            "booking_workspace_metadata_only": True,
            "booking_execution_disabled": True,
            "live_booking_creation_disabled": True,
            "ticket_issuance_disabled": True,
            "gds_connectivity_disabled": True,
            "ndc_connectivity_disabled": True,
            "airline_apis_disabled": True,
            "airline_api_calls_disabled": True,
            "payment_processing_disabled": True,
            "fare_calculation_disabled": True,
            "ai_disabled": True,
            "background_workers_disabled": True,
            "automatic_booking_confirmation_disabled": True,
            "automatic_ticket_generation_disabled": True,
            "external_integrations_disabled": True,
            "external_api_calls_disabled": True,
            "automation_disabled": True,
        }

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

    def _manual_workspace_title(
        self,
        workspace_number: str,
        trip: dict[str, Any] | None,
        pnr_locator: str | None,
    ) -> str:
        if trip and trip.get("trip_title"):
            return f"{workspace_number} · {trip['trip_title']}"
        if trip and trip.get("trip_reference"):
            return f"{workspace_number} · {trip['trip_reference']}"
        if pnr_locator:
            return f"{workspace_number} · PNR {pnr_locator}"
        return f"{workspace_number} · Manual booking workspace"

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
            source_context=BookingSourceContext.OFFER_READINESS,
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

    def _internal_manual_pnr_mirror(
        self,
        workspace: dict[str, Any],
        payload: ManualBookingWorkspaceCreate,
        provider_target: str,
        source_context: str,
    ) -> dict[str, Any]:
        return {
            "phase": PHASE_LABEL,
            "mirrored_at": _now_iso(),
            "provider_execution_disabled": True,
            "manual_entry": True,
            "source_context": source_context,
            "booking_workspace_id": workspace.get("id"),
            "import_draft_id": payload.import_draft_id,
            "trip_change_operation_id": payload.trip_change_operation_id,
            "provider_target": provider_target,
            "pnr_locator": payload.pnr_locator,
            "status": "draft",
            "passengers": payload.passengers_json or [],
            "segments": payload.segments_json or [],
            "pricing": payload.pricing_json or {},
            "services": payload.services_json or {},
            "pets": payload.pets_json or {},
            "special_items": payload.special_items_json or {},
            "ssr": payload.ssr_json or [],
            "osi": payload.osi_json or [],
            "internal_notes": payload.internal_notes,
            "warnings": [],
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

    async def _write_trip_timeline(
        self,
        agency_id: str,
        trip_id: str,
        actor_user_id: str | None,
        event_type: str,
        title: str,
        summary: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        event = TripTimelineEvent(
            agency_id=agency_id,
            trip_id=trip_id,
            actor_user_id=actor_user_id,
            event_type=event_type,
            title=title,
            summary=summary,
            metadata=metadata or {},
        )
        await self.db.collection("trip_timeline_events").insert_one(event.model_dump(mode="json"))
