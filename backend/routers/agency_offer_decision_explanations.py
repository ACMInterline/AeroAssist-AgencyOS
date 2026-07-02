from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    OfferDecisionAcknowledgementCreate,
    OfferDecisionAuditSnapshotCreate,
    OfferDecisionExplanationCreate,
    OfferDecisionExplanationUpdate,
    OfferDecisionReasonCreate,
    OfferDecisionReasonUpdate,
    OfferDecisionTimelineEventCreate,
)
from services.offer_decision_explanation_service import OfferDecisionExplanationService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/offer-decision-explanations", tags=["agency-offer-decision-explanations"])

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
async def get_agency_offer_decision_explanation_summary(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {
        **await OfferDecisionExplanationService(db).summary(agency_id=agency_id),
        "agency_operational_layer": True,
        "metadata_only": True,
    }


@router.get("/explanations")
async def list_agency_offer_decision_explanations(
    agency_id: str,
    decision_pack_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExplanationService(db).list_explanations(agency_id=agency_id, decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id)}


@router.post("/explanations", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_explanation(
    agency_id: str,
    payload: OfferDecisionExplanationCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExplanationService(db).create_explanation(agency_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.patch("/explanations/{explanation_id}")
async def update_agency_offer_decision_explanation(
    agency_id: str,
    explanation_id: str,
    payload: OfferDecisionExplanationUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        result = await OfferDecisionExplanationService(db).update_explanation(agency_id, explanation_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
    if not result:
        raise not_found("Offer decision explanation not found.")
    return result


@router.get("/timeline")
async def list_agency_offer_decision_timeline(
    agency_id: str,
    decision_pack_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExplanationService(db).list_timeline(agency_id=agency_id, decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id)}


@router.post("/timeline-events", status_code=status.HTTP_201_CREATED)
async def append_agency_offer_decision_timeline_event(
    agency_id: str,
    payload: OfferDecisionTimelineEventCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExplanationService(db).append_timeline_event(agency_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/evidence")
async def list_agency_offer_decision_evidence_references(
    agency_id: str,
    decision_pack_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExplanationService(db).list_evidence_references(agency_id=agency_id, decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id)}


@router.get("/reasons")
async def list_agency_offer_decision_reasons(
    agency_id: str,
    decision_pack_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExplanationService(db).list_reasons(agency_id=agency_id, decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id)}


@router.post("/reasons", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_reason(
    agency_id: str,
    payload: OfferDecisionReasonCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExplanationService(db).create_reason(agency_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.patch("/reasons/{reason_id}")
async def update_agency_offer_decision_reason(
    agency_id: str,
    reason_id: str,
    payload: OfferDecisionReasonUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        result = await OfferDecisionExplanationService(db).update_reason(agency_id, reason_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
    if not result:
        raise not_found("Offer decision reason not found.")
    return result


@router.get("/acknowledgements")
async def list_agency_offer_decision_acknowledgements(
    agency_id: str,
    decision_pack_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExplanationService(db).list_acknowledgements(agency_id=agency_id, decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id)}


@router.post("/acknowledgements", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_acknowledgement(
    agency_id: str,
    payload: OfferDecisionAcknowledgementCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExplanationService(db).create_acknowledgement(agency_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/snapshots")
async def list_agency_offer_decision_audit_snapshots(
    agency_id: str,
    decision_pack_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExplanationService(db).list_snapshots(agency_id=agency_id, decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id)}


@router.post("/snapshots", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_audit_snapshot(
    agency_id: str,
    payload: OfferDecisionAuditSnapshotCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExplanationService(db).create_snapshot(agency_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
