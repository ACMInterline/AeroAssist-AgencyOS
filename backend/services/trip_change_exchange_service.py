from __future__ import annotations

from typing import Any

from database import Database
from models import (
    BookingSourceContext,
    EmdExchangeOperation,
    EmdExchangeOperationCreate,
    EmdSourceContext,
    ExchangeOperationStatus,
    ManualBookingWorkspaceCreate,
    ManualEmdCreate,
    ManualTicketCreate,
    TicketExchangeOperation,
    TicketExchangeOperationCreate,
    TicketSourceContext,
    TripChangeOperation,
    TripChangeOperationCreate,
    TripChangeOperationStatus,
    TripTimelineEvent,
)
from services.booking_workspace_service import BookingWorkspaceService
from services.operational_collaboration_service import OperationalCollaborationService
from services.ticket_emd_service import TicketEmdService


class TripChangeExchangeError(ValueError):
    pass


class TripChangeExchangeService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_trip_change_operations(self, agency_id: str, trip_id: str) -> dict[str, Any]:
        operations = await self.db.collection("trip_change_operations").find_many({"agency_id": agency_id, "trip_id": trip_id})
        operations.sort(key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""), reverse=True)
        ticket_exchanges = await self.db.collection("ticket_exchange_operations").find_many({"agency_id": agency_id, "trip_id": trip_id})
        emd_exchanges = await self.db.collection("emd_exchange_operations").find_many({"agency_id": agency_id, "trip_id": trip_id})
        return {
            "items": operations,
            "ticket_exchange_operations": ticket_exchanges,
            "emd_exchange_operations": emd_exchanges,
            "provider_execution_disabled": True,
        }

    async def create_trip_change_operation(
        self,
        agency_id: str,
        trip_id: str,
        payload: TripChangeOperationCreate,
        user: dict,
    ) -> dict[str, Any] | None:
        trip = await self.db.collection("trip_dossiers").find_one({"agency_id": agency_id, "id": trip_id})
        if not trip:
            return None
        operation = TripChangeOperation(
            agency_id=agency_id,
            trip_id=trip_id,
            request_id=payload.request_id,
            source_booking_workspace_id=payload.source_booking_workspace_id,
            source_booking_record_id=payload.source_booking_record_id,
            operation_type=payload.operation_type,
            status=TripChangeOperationStatus.DRAFT,
            reason=payload.reason,
            change_summary_json=payload.change_summary_json or {},
            original_snapshot_json=payload.original_snapshot_json or {},
            proposed_snapshot_json=payload.proposed_snapshot_json or {},
            created_by_user_id=user.get("id"),
        )
        created = await self.db.collection("trip_change_operations").insert_one(operation.model_dump(mode="json"))
        await self._write_trip_timeline(
            agency_id,
            trip_id,
            user.get("id"),
            "trip.change_operation_created",
            "Trip change operation created",
            payload.reason,
            {"trip_change_operation_id": created["id"], "operation_type": created.get("operation_type")},
        )
        return {"operation": created, "provider_execution_disabled": True}

    async def create_change_booking_from_operation(
        self,
        agency_id: str,
        operation_id: str,
        payload: ManualBookingWorkspaceCreate,
        user: dict,
    ) -> dict[str, Any] | None:
        operation = await self.db.collection("trip_change_operations").find_one({"agency_id": agency_id, "id": operation_id})
        if not operation:
            return None
        merged_payload = payload.model_copy(
            update={
                "trip_id": operation["trip_id"],
                "source_context": BookingSourceContext.EXISTING_TRIP_CHANGE,
                "trip_change_operation_id": operation_id,
                "original_booking_record_id": payload.original_booking_record_id or operation.get("source_booking_record_id"),
            }
        )
        booking = await BookingWorkspaceService(self.db).create_manual_booking_workspace(agency_id, merged_payload, user)
        workspace = booking.get("booking_workspace") or {}
        record = booking.get("booking_record") or {}
        updated = await self.db.collection("trip_change_operations").update_one(
            {"agency_id": agency_id, "id": operation_id},
            {
                "new_booking_workspace_id": workspace.get("id"),
                "new_booking_record_id": record.get("id"),
                "status": TripChangeOperationStatus.MIRRORED.value,
                "accepted_snapshot_json": {
                    "booking_workspace_id": workspace.get("id"),
                    "booking_record_id": record.get("id"),
                    "provider_execution_disabled": True,
                },
            },
        )
        await self._write_trip_timeline(
            agency_id,
            operation["trip_id"],
            user.get("id"),
            "trip.change_booking_mirrored",
            "Change booking mirror created",
            workspace.get("workspace_number"),
            {"trip_change_operation_id": operation_id, "booking_workspace_id": workspace.get("id"), "booking_record_id": record.get("id")},
        )
        return {"operation": updated, "booking_workspace": workspace, "booking_record": record, "provider_execution_disabled": True}

    async def create_ticket_exchange_operation(
        self,
        agency_id: str,
        payload: TicketExchangeOperationCreate,
        user: dict,
    ) -> dict[str, Any] | None:
        original = await self.db.collection("ticket_records").find_one({"agency_id": agency_id, "id": payload.original_ticket_record_id})
        if not original:
            return None
        operation = TicketExchangeOperation(
            agency_id=agency_id,
            trip_id=payload.trip_id or original.get("trip_id"),
            booking_record_id=payload.booking_record_id or original.get("booking_record_id"),
            original_ticket_record_id=payload.original_ticket_record_id,
            operation_type=payload.operation_type,
            reason=payload.reason,
            residual_value_amount=payload.residual_value_amount,
            additional_collection_amount=payload.additional_collection_amount,
            penalty_amount=payload.penalty_amount,
            tax_difference_amount=payload.tax_difference_amount,
            currency=payload.currency or original.get("currency"),
            fare_difference_json=payload.fare_difference_json or {},
            original_ticket_snapshot_json=original,
            warnings_json=[],
            created_by_user_id=user.get("id"),
        )
        created = await self.db.collection("ticket_exchange_operations").insert_one(operation.model_dump(mode="json"))
        if created.get("trip_id"):
            await self._write_trip_timeline(
                agency_id,
                created["trip_id"],
                user.get("id"),
                "trip.ticket_exchange_operation_created",
                "Ticket exchange operation created",
                created.get("reason"),
                {"ticket_exchange_operation_id": created["id"], "original_ticket_record_id": original["id"], "provider_exchange_execution_disabled": True},
            )
        return {"operation": created, "provider_exchange_execution_disabled": True, "provider_refund_execution_disabled": True, "provider_void_execution_disabled": True}

    async def mirror_new_ticket_for_exchange(
        self,
        agency_id: str,
        operation_id: str,
        payload: ManualTicketCreate,
        user: dict,
    ) -> dict[str, Any] | None:
        operation = await self.db.collection("ticket_exchange_operations").find_one({"agency_id": agency_id, "id": operation_id})
        if not operation:
            return None
        ticket = await TicketEmdService(self.db).create_manual_ticket(
            agency_id,
            payload.model_copy(
                update={
                    "trip_id": payload.trip_id or operation.get("trip_id"),
                    "booking_record_id": payload.booking_record_id or operation.get("booking_record_id"),
                    "source_context": TicketSourceContext.EXCHANGE_REISSUE,
                    "original_ticket_record_id": operation.get("original_ticket_record_id"),
                    "exchange_operation_id": operation_id,
                }
            ),
            user,
        )
        new_ticket = ticket.get("ticket") or {}
        updated = await self.db.collection("ticket_exchange_operations").update_one(
            {"agency_id": agency_id, "id": operation_id},
            {
                "new_ticket_record_id": new_ticket.get("id"),
                "status": ExchangeOperationStatus.MIRRORED.value,
                "new_ticket_snapshot_json": new_ticket,
            },
        )
        return {"operation": updated, "ticket": new_ticket, "provider_exchange_execution_disabled": True}

    async def create_emd_exchange_operation(
        self,
        agency_id: str,
        payload: EmdExchangeOperationCreate,
        user: dict,
    ) -> dict[str, Any] | None:
        original = await self.db.collection("emd_records").find_one({"agency_id": agency_id, "id": payload.original_emd_record_id})
        if not original:
            return None
        operation = EmdExchangeOperation(
            agency_id=agency_id,
            trip_id=payload.trip_id or original.get("trip_id"),
            booking_record_id=payload.booking_record_id or original.get("booking_record_id"),
            original_emd_record_id=payload.original_emd_record_id,
            operation_type=payload.operation_type,
            reason=payload.reason,
            residual_value_amount=payload.residual_value_amount,
            additional_collection_amount=payload.additional_collection_amount,
            penalty_amount=payload.penalty_amount,
            currency=payload.currency or original.get("currency"),
            original_emd_snapshot_json=original,
            warnings_json=[],
            created_by_user_id=user.get("id"),
        )
        created = await self.db.collection("emd_exchange_operations").insert_one(operation.model_dump(mode="json"))
        if created.get("trip_id"):
            await self._write_trip_timeline(
                agency_id,
                created["trip_id"],
                user.get("id"),
                "trip.emd_exchange_operation_created",
                "EMD exchange operation created",
                created.get("reason"),
                {"emd_exchange_operation_id": created["id"], "original_emd_record_id": original["id"], "provider_exchange_execution_disabled": True},
            )
        return {"operation": created, "provider_exchange_execution_disabled": True, "provider_refund_execution_disabled": True, "provider_void_execution_disabled": True}

    async def mirror_new_emd_for_exchange(
        self,
        agency_id: str,
        operation_id: str,
        payload: ManualEmdCreate,
        user: dict,
    ) -> dict[str, Any] | None:
        operation = await self.db.collection("emd_exchange_operations").find_one({"agency_id": agency_id, "id": operation_id})
        if not operation:
            return None
        emd = await TicketEmdService(self.db).create_manual_emd(
            agency_id,
            payload.model_copy(
                update={
                    "trip_id": payload.trip_id or operation.get("trip_id"),
                    "booking_record_id": payload.booking_record_id or operation.get("booking_record_id"),
                    "source_context": EmdSourceContext.EXCHANGE_REISSUE,
                    "original_emd_record_id": operation.get("original_emd_record_id"),
                    "exchange_operation_id": operation_id,
                }
            ),
            user,
        )
        new_emd = emd.get("emd") or {}
        updated = await self.db.collection("emd_exchange_operations").update_one(
            {"agency_id": agency_id, "id": operation_id},
            {
                "new_emd_record_id": new_emd.get("id"),
                "status": ExchangeOperationStatus.MIRRORED.value,
                "new_emd_snapshot_json": new_emd,
            },
        )
        return {"operation": updated, "emd": new_emd, "provider_exchange_execution_disabled": True}

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
        await OperationalCollaborationService(self.db).record_compatibility_event(
            agency_id=agency_id,
            entity_type="trip",
            entity_id=trip_id,
            source_event_type=event_type,
            summary=summary or title,
            actor_user_id=actor_user_id,
            visibility="internal",
            details={"title": title, **(metadata or {})},
            source_collection="trip_timeline_events",
        )
