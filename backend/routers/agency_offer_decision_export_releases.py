from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    OfferDecisionExportApprovalCheckpointCreateRequest,
    OfferDecisionExportApprovalCreateRequest,
    OfferDecisionExportApprovalStatusUpdateRequest,
    OfferDecisionExportReleaseHoldCreateRequest,
    OfferDecisionExportReleaseHoldReleaseRequest,
    OfferDecisionExportReleaseReadinessCreateRequest,
    OfferDecisionExportReleaseSnapshotCreateRequest,
)
from services.offer_decision_export_release_service import OfferDecisionExportReleaseService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/offer-decision-export-releases", tags=["agency-offer-decision-export-releases"])

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
async def get_agency_offer_decision_export_release_summary(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {
        **await OfferDecisionExportReleaseService(db).summary(agency_id=agency_id),
        "agency_operational_layer": True,
        "metadata_only": True,
    }


@router.get("/approvals")
async def list_agency_offer_decision_export_approvals(
    agency_id: str,
    preview_id: str | None = Query(default=None),
    export_id: str | None = Query(default=None),
    approval_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportReleaseService(db).list_approvals(agency_id=agency_id, preview_id=preview_id, export_id=export_id, approval_status=approval_status)}


@router.post("/approvals", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_export_approval(
    agency_id: str,
    payload: OfferDecisionExportApprovalCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportReleaseService(db).create_approval(agency_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/approvals/{approval_id}")
async def get_agency_offer_decision_export_approval(
    agency_id: str,
    approval_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    detail = await OfferDecisionExportReleaseService(db).get_approval_detail(approval_id, agency_id)
    if not detail:
        raise not_found("Offer decision export approval not found.")
    return detail


@router.get("/approvals/{approval_id}/checkpoints")
async def list_agency_offer_decision_export_approval_checkpoints(
    agency_id: str,
    approval_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    if not await OfferDecisionExportReleaseService(db).get_approval(approval_id, agency_id):
        raise not_found("Offer decision export approval not found.")
    return {"items": await OfferDecisionExportReleaseService(db).list_checkpoints(agency_id=agency_id, approval_id=approval_id)}


@router.post("/approvals/{approval_id}/checkpoints", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_export_approval_checkpoint(
    agency_id: str,
    approval_id: str,
    payload: OfferDecisionExportApprovalCheckpointCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportReleaseService(db).add_checkpoint(agency_id, approval_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/approvals/{approval_id}/status")
async def update_agency_offer_decision_export_approval_status(
    agency_id: str,
    approval_id: str,
    payload: OfferDecisionExportApprovalStatusUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportReleaseService(db).update_approval_status(agency_id, approval_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/readiness")
async def list_agency_offer_decision_export_release_readiness(
    agency_id: str,
    approval_id: str | None = Query(default=None),
    preview_id: str | None = Query(default=None),
    export_id: str | None = Query(default=None),
    readiness_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportReleaseService(db).list_readiness(agency_id=agency_id, approval_id=approval_id, preview_id=preview_id, export_id=export_id, readiness_status=readiness_status)}


@router.post("/readiness", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_export_release_readiness(
    agency_id: str,
    payload: OfferDecisionExportReleaseReadinessCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportReleaseService(db).create_readiness(agency_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/readiness/{readiness_id}")
async def get_agency_offer_decision_export_release_readiness(
    agency_id: str,
    readiness_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    detail = await OfferDecisionExportReleaseService(db).get_readiness_detail(readiness_id, agency_id)
    if not detail:
        raise not_found("Release readiness record not found.")
    return detail


@router.get("/readiness/{readiness_id}/holds")
async def list_agency_offer_decision_export_release_holds(
    agency_id: str,
    readiness_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    if not await OfferDecisionExportReleaseService(db).get_readiness(readiness_id, agency_id):
        raise not_found("Release readiness record not found.")
    return {"items": await OfferDecisionExportReleaseService(db).list_holds(agency_id=agency_id, readiness_id=readiness_id)}


@router.post("/readiness/{readiness_id}/holds", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_export_release_hold(
    agency_id: str,
    readiness_id: str,
    payload: OfferDecisionExportReleaseHoldCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportReleaseService(db).add_hold(agency_id, readiness_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/readiness/{readiness_id}/holds/{hold_id}/release")
async def release_agency_offer_decision_export_release_hold(
    agency_id: str,
    readiness_id: str,
    hold_id: str,
    payload: OfferDecisionExportReleaseHoldReleaseRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportReleaseService(db).release_hold(agency_id, readiness_id, hold_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/readiness/{readiness_id}/snapshots")
async def list_agency_offer_decision_export_release_snapshots(
    agency_id: str,
    readiness_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    if not await OfferDecisionExportReleaseService(db).get_readiness(readiness_id, agency_id):
        raise not_found("Release readiness record not found.")
    return {"items": await OfferDecisionExportReleaseService(db).list_snapshots(agency_id=agency_id, readiness_id=readiness_id)}


@router.post("/readiness/{readiness_id}/snapshots", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_export_release_snapshot(
    agency_id: str,
    readiness_id: str,
    payload: OfferDecisionExportReleaseSnapshotCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportReleaseService(db).create_snapshot(agency_id, readiness_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
