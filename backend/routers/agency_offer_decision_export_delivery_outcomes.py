from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    OfferDecisionExportDeliveryIssueCreateRequest,
    OfferDecisionExportDeliveryIssueUpdateRequest,
    OfferDecisionExportDeliveryOutcomeCreateRequest,
    OfferDecisionExportDeliveryOutcomeEventCreateRequest,
    OfferDecisionExportDeliveryOutcomeSnapshotCreateRequest,
    OfferDecisionExportDeliveryOutcomeUpdateRequest,
    OfferDecisionExportDeliveryReceiptCreateRequest,
)
from services.offer_decision_export_delivery_outcome_service import OfferDecisionExportDeliveryOutcomeService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/offer-decision-export-delivery-outcomes", tags=["agency-offer-decision-export-delivery-outcomes"])

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
async def get_agency_offer_decision_export_delivery_outcome_summary(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {
        **await OfferDecisionExportDeliveryOutcomeService(db).summary(agency_id=agency_id),
        "agency_operational_layer": True,
        "metadata_only": True,
    }


@router.post("/outcomes", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_export_delivery_outcome(
    agency_id: str,
    payload: OfferDecisionExportDeliveryOutcomeCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportDeliveryOutcomeService(db).create_outcome(agency_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/outcomes")
async def list_agency_offer_decision_export_delivery_outcomes(
    agency_id: str,
    handoff_id: str | None = Query(default=None),
    export_id: str | None = Query(default=None),
    outcome_status: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportDeliveryOutcomeService(db).list_outcomes(agency_id=agency_id, handoff_id=handoff_id, export_id=export_id, outcome_status=outcome_status)}


@router.get("/outcomes/{outcome_id}")
async def get_agency_offer_decision_export_delivery_outcome(
    agency_id: str,
    outcome_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    detail = await OfferDecisionExportDeliveryOutcomeService(db).get_outcome_detail(outcome_id, agency_id)
    if not detail:
        raise not_found("Delivery outcome metadata not found.")
    return detail


@router.patch("/outcomes/{outcome_id}")
async def update_agency_offer_decision_export_delivery_outcome(
    agency_id: str,
    outcome_id: str,
    payload: OfferDecisionExportDeliveryOutcomeUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportDeliveryOutcomeService(db).update_outcome(agency_id, outcome_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/outcomes/{outcome_id}/events", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_export_delivery_outcome_event(
    agency_id: str,
    outcome_id: str,
    payload: OfferDecisionExportDeliveryOutcomeEventCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportDeliveryOutcomeService(db).add_event(agency_id, outcome_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/events")
async def list_agency_offer_decision_export_delivery_outcome_events(
    agency_id: str,
    outcome_id: str | None = Query(default=None),
    handoff_id: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportDeliveryOutcomeService(db).list_events(agency_id=agency_id, outcome_id=outcome_id, handoff_id=handoff_id, event_type=event_type)}


@router.post("/outcomes/{outcome_id}/receipts", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_export_delivery_receipt(
    agency_id: str,
    outcome_id: str,
    payload: OfferDecisionExportDeliveryReceiptCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportDeliveryOutcomeService(db).add_receipt(agency_id, outcome_id, payload)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/receipts")
async def list_agency_offer_decision_export_delivery_receipts(
    agency_id: str,
    outcome_id: str | None = Query(default=None),
    handoff_id: str | None = Query(default=None),
    receipt_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportDeliveryOutcomeService(db).list_receipts(agency_id=agency_id, outcome_id=outcome_id, handoff_id=handoff_id, receipt_type=receipt_type)}


@router.post("/outcomes/{outcome_id}/issues", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_export_delivery_issue(
    agency_id: str,
    outcome_id: str,
    payload: OfferDecisionExportDeliveryIssueCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportDeliveryOutcomeService(db).add_issue(agency_id, outcome_id, payload)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.patch("/issues/{issue_id}")
async def update_agency_offer_decision_export_delivery_issue(
    agency_id: str,
    issue_id: str,
    payload: OfferDecisionExportDeliveryIssueUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportDeliveryOutcomeService(db).update_issue(agency_id, issue_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/issues")
async def list_agency_offer_decision_export_delivery_issues(
    agency_id: str,
    outcome_id: str | None = Query(default=None),
    handoff_id: str | None = Query(default=None),
    issue_status: str | None = Query(default=None, alias="status"),
    issue_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportDeliveryOutcomeService(db).list_issues(agency_id=agency_id, outcome_id=outcome_id, handoff_id=handoff_id, issue_status=issue_status, issue_type=issue_type)}


@router.post("/outcomes/{outcome_id}/snapshots", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_export_delivery_outcome_snapshot(
    agency_id: str,
    outcome_id: str,
    payload: OfferDecisionExportDeliveryOutcomeSnapshotCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportDeliveryOutcomeService(db).create_snapshot(agency_id, outcome_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/snapshots")
async def list_agency_offer_decision_export_delivery_outcome_snapshots(
    agency_id: str,
    outcome_id: str | None = Query(default=None),
    handoff_id: str | None = Query(default=None),
    snapshot_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportDeliveryOutcomeService(db).list_snapshots(agency_id=agency_id, outcome_id=outcome_id, handoff_id=handoff_id, snapshot_type=snapshot_type)}
