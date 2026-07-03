from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    OfferDecisionExportDeliveryAttachmentCreateRequest,
    OfferDecisionExportDeliveryHandoffCreateRequest,
    OfferDecisionExportDeliveryHandoffStatusUpdateRequest,
    OfferDecisionExportDeliveryInstructionCompletionRequest,
    OfferDecisionExportDeliveryInstructionCreateRequest,
    OfferDecisionExportDeliveryRecipientCreateRequest,
    OfferDecisionExportDeliveryRecipientStatusUpdateRequest,
    OfferDecisionExportDeliverySnapshotCreateRequest,
)
from services.offer_decision_export_delivery_service import OfferDecisionExportDeliveryService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/offer-decision-export-deliveries", tags=["agency-offer-decision-export-deliveries"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin", "agency_agent"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


async def require_write(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin"}:
        await require_any_agency_role(db, agency_id, user, WRITE_ROLES)


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def bad_request(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


@router.get("/summary")
async def get_agency_offer_decision_export_delivery_summary(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {
        **await OfferDecisionExportDeliveryService(db).summary(agency_id=agency_id),
        "agency_operational_layer": True,
        "metadata_only": True,
    }


@router.get("/handoffs")
async def list_agency_offer_decision_export_delivery_handoffs(
    agency_id: str,
    export_id: str | None = Query(default=None),
    preview_id: str | None = Query(default=None),
    release_readiness_id: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportDeliveryService(db).list_handoffs(agency_id=agency_id, export_id=export_id, preview_id=preview_id, release_readiness_id=release_readiness_id, status=status_filter)}


@router.post("/handoffs", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_export_delivery_handoff(
    agency_id: str,
    payload: OfferDecisionExportDeliveryHandoffCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportDeliveryService(db).create_handoff(agency_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/handoffs/{handoff_id}")
async def get_agency_offer_decision_export_delivery_handoff(
    agency_id: str,
    handoff_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    detail = await OfferDecisionExportDeliveryService(db).get_handoff_detail(handoff_id, agency_id)
    if not detail:
        raise not_found("Delivery handoff metadata not found.")
    return detail


@router.patch("/handoffs/{handoff_id}/status")
async def update_agency_offer_decision_export_delivery_handoff_status(
    agency_id: str,
    handoff_id: str,
    payload: OfferDecisionExportDeliveryHandoffStatusUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportDeliveryService(db).update_handoff_status(agency_id, handoff_id, payload)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/handoffs/{handoff_id}/recipients")
async def list_agency_offer_decision_export_delivery_recipients(
    agency_id: str,
    handoff_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    if not await OfferDecisionExportDeliveryService(db).get_handoff(handoff_id, agency_id):
        raise not_found("Delivery handoff metadata not found.")
    return {"items": await OfferDecisionExportDeliveryService(db).list_recipients(agency_id=agency_id, handoff_id=handoff_id)}


@router.post("/handoffs/{handoff_id}/recipients", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_export_delivery_recipient(
    agency_id: str,
    handoff_id: str,
    payload: OfferDecisionExportDeliveryRecipientCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportDeliveryService(db).add_recipient(agency_id, handoff_id, payload)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.patch("/recipients/{recipient_id}/status")
async def update_agency_offer_decision_export_delivery_recipient_status(
    agency_id: str,
    recipient_id: str,
    payload: OfferDecisionExportDeliveryRecipientStatusUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportDeliveryService(db).update_recipient_status(agency_id, recipient_id, payload)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/handoffs/{handoff_id}/attachments")
async def list_agency_offer_decision_export_delivery_attachments(
    agency_id: str,
    handoff_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    if not await OfferDecisionExportDeliveryService(db).get_handoff(handoff_id, agency_id):
        raise not_found("Delivery handoff metadata not found.")
    return {"items": await OfferDecisionExportDeliveryService(db).list_attachments(agency_id=agency_id, handoff_id=handoff_id)}


@router.post("/handoffs/{handoff_id}/attachments", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_export_delivery_attachment(
    agency_id: str,
    handoff_id: str,
    payload: OfferDecisionExportDeliveryAttachmentCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportDeliveryService(db).add_attachment_metadata(agency_id, handoff_id, payload)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/handoffs/{handoff_id}/instructions")
async def list_agency_offer_decision_export_delivery_instructions(
    agency_id: str,
    handoff_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    if not await OfferDecisionExportDeliveryService(db).get_handoff(handoff_id, agency_id):
        raise not_found("Delivery handoff metadata not found.")
    return {"items": await OfferDecisionExportDeliveryService(db).list_instructions(agency_id=agency_id, handoff_id=handoff_id)}


@router.post("/handoffs/{handoff_id}/instructions", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_export_delivery_instruction(
    agency_id: str,
    handoff_id: str,
    payload: OfferDecisionExportDeliveryInstructionCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportDeliveryService(db).add_instruction(agency_id, handoff_id, payload)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.patch("/instructions/{instruction_id}/completion")
async def update_agency_offer_decision_export_delivery_instruction_completion(
    agency_id: str,
    instruction_id: str,
    payload: OfferDecisionExportDeliveryInstructionCompletionRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportDeliveryService(db).update_instruction_completion(agency_id, instruction_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/handoffs/{handoff_id}/snapshots")
async def list_agency_offer_decision_export_delivery_snapshots(
    agency_id: str,
    handoff_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    if not await OfferDecisionExportDeliveryService(db).get_handoff(handoff_id, agency_id):
        raise not_found("Delivery handoff metadata not found.")
    return {"items": await OfferDecisionExportDeliveryService(db).list_snapshots(agency_id=agency_id, handoff_id=handoff_id)}


@router.post("/handoffs/{handoff_id}/snapshots", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_export_delivery_snapshot(
    agency_id: str,
    handoff_id: str,
    payload: OfferDecisionExportDeliverySnapshotCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportDeliveryService(db).create_snapshot(agency_id, handoff_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
