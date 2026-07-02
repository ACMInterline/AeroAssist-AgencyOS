from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    OfferDecisionExportPreviewGenerateRequest,
    OfferDecisionExportPreviewSnapshotCreate,
    OfferDecisionExportPreviewValidateRequest,
)
from services.offer_decision_export_preview_service import OfferDecisionExportPreviewService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/offer-decision-export-previews", tags=["agency-offer-decision-export-previews"])

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
async def get_agency_offer_decision_export_preview_summary(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {
        **await OfferDecisionExportPreviewService(db).summary(agency_id=agency_id),
        "agency_operational_layer": True,
        "metadata_only": True,
    }


@router.get("/previews")
async def list_agency_offer_decision_export_previews(
    agency_id: str,
    export_id: str | None = Query(default=None),
    decision_pack_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportPreviewService(db).list_previews(agency_id=agency_id, export_id=export_id, decision_pack_id=decision_pack_id)}


@router.get("/previews/{preview_id}")
async def get_agency_offer_decision_export_preview(
    agency_id: str,
    preview_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    detail = await OfferDecisionExportPreviewService(db).get_preview_detail(preview_id, agency_id)
    if not detail:
        raise not_found("Offer decision export preview not found.")
    return detail


@router.post("/generate", status_code=status.HTTP_201_CREATED)
async def generate_agency_offer_decision_export_preview(
    agency_id: str,
    payload: OfferDecisionExportPreviewGenerateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportPreviewService(db).generate_preview(agency_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/sections")
async def list_agency_offer_decision_export_preview_sections(
    agency_id: str,
    preview_id: str | None = Query(default=None),
    export_id: str | None = Query(default=None),
    decision_pack_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportPreviewService(db).list_sections(agency_id=agency_id, preview_id=preview_id, export_id=export_id, decision_pack_id=decision_pack_id)}


@router.get("/blocks")
async def list_agency_offer_decision_export_preview_blocks(
    agency_id: str,
    preview_id: str | None = Query(default=None),
    section_id: str | None = Query(default=None),
    export_id: str | None = Query(default=None),
    decision_pack_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportPreviewService(db).list_blocks(agency_id=agency_id, preview_id=preview_id, section_id=section_id, export_id=export_id, decision_pack_id=decision_pack_id)}


@router.get("/validations")
async def list_agency_offer_decision_export_preview_validations(
    agency_id: str,
    preview_id: str | None = Query(default=None),
    export_id: str | None = Query(default=None),
    decision_pack_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportPreviewService(db).list_validations(agency_id=agency_id, preview_id=preview_id, export_id=export_id, decision_pack_id=decision_pack_id)}


@router.post("/previews/{preview_id}/validate", status_code=status.HTTP_201_CREATED)
async def validate_agency_offer_decision_export_preview(
    agency_id: str,
    preview_id: str,
    payload: OfferDecisionExportPreviewValidateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportPreviewService(db).validate_preview(agency_id, preview_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/previews/{preview_id}/snapshots", status_code=status.HTTP_201_CREATED)
async def save_agency_offer_decision_export_preview_snapshot(
    agency_id: str,
    preview_id: str,
    payload: OfferDecisionExportPreviewSnapshotCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportPreviewService(db).save_snapshot(agency_id, preview_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/snapshots")
async def list_agency_offer_decision_export_preview_snapshots(
    agency_id: str,
    preview_id: str | None = Query(default=None),
    export_id: str | None = Query(default=None),
    decision_pack_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportPreviewService(db).list_snapshots(agency_id=agency_id, preview_id=preview_id, export_id=export_id, decision_pack_id=decision_pack_id)}
