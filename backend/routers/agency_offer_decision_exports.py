from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import OfferDecisionExportGenerateRequest
from services.offer_decision_export_service import OfferDecisionExportService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/offer-decision-exports", tags=["agency-offer-decision-exports"])

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
async def get_agency_offer_decision_export_summary(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {
        **await OfferDecisionExportService(db).summary(agency_id=agency_id),
        "agency_operational_layer": True,
        "metadata_only": True,
    }


@router.get("/exports")
async def list_agency_offer_decision_exports(
    agency_id: str,
    decision_pack_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportService(db).list_exports(agency_id=agency_id, decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id)}


@router.get("/exports/{export_id}")
async def get_agency_offer_decision_export(
    agency_id: str,
    export_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    detail = await OfferDecisionExportService(db).get_export_detail(export_id, agency_id)
    if not detail:
        raise not_found("Offer decision export not found.")
    return detail


@router.post("/generate", status_code=status.HTTP_201_CREATED)
async def generate_agency_offer_decision_export(
    agency_id: str,
    payload: OfferDecisionExportGenerateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportService(db).generate_export(agency_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/artifacts")
async def list_agency_offer_decision_export_artifacts(
    agency_id: str,
    export_id: str | None = Query(default=None),
    decision_pack_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportService(db).list_artifacts(agency_id=agency_id, export_id=export_id, decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id)}


@router.get("/recipient-drafts")
async def list_agency_offer_decision_export_recipient_drafts(
    agency_id: str,
    export_id: str | None = Query(default=None),
    decision_pack_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportService(db).list_recipient_drafts(agency_id=agency_id, export_id=export_id, decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id)}


@router.get("/audit-events")
async def list_agency_offer_decision_export_audit_events(
    agency_id: str,
    export_id: str | None = Query(default=None),
    decision_pack_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportService(db).list_audit_events(agency_id=agency_id, export_id=export_id, decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id)}
