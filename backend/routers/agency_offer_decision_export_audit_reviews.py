from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    OfferDecisionExportAuditReviewChecklistItemCreateRequest,
    OfferDecisionExportAuditReviewChecklistItemUpdateRequest,
    OfferDecisionExportAuditReviewCreateRequest,
    OfferDecisionExportAuditReviewFindingCreateRequest,
    OfferDecisionExportAuditReviewFindingUpdateRequest,
    OfferDecisionExportAuditReviewSnapshotCreateRequest,
    OfferDecisionExportAuditReviewStatusUpdateRequest,
)
from services.offer_decision_export_audit_review_service import OfferDecisionExportAuditReviewService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/offer-decision-export-audit-reviews", tags=["agency-offer-decision-export-audit-reviews"])

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
async def get_agency_offer_decision_export_audit_review_summary(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {
        **await OfferDecisionExportAuditReviewService(db).summary(agency_id=agency_id),
        "agency_operational_layer": True,
        "metadata_only": True,
    }


@router.post("/reviews", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_export_audit_review(
    agency_id: str,
    payload: OfferDecisionExportAuditReviewCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportAuditReviewService(db).create_review(agency_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/reviews")
async def list_agency_offer_decision_export_audit_reviews(
    agency_id: str,
    export_id: str | None = Query(default=None),
    outcome_id: str | None = Query(default=None),
    review_status: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportAuditReviewService(db).list_reviews(agency_id=agency_id, export_id=export_id, outcome_id=outcome_id, review_status=review_status)}


@router.get("/reviews/{review_id}")
async def get_agency_offer_decision_export_audit_review(
    agency_id: str,
    review_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    detail = await OfferDecisionExportAuditReviewService(db).get_review_detail(review_id, agency_id)
    if not detail:
        raise not_found("Audit review not found.")
    return detail


@router.patch("/reviews/{review_id}/status")
async def update_agency_offer_decision_export_audit_review_status(
    agency_id: str,
    review_id: str,
    payload: OfferDecisionExportAuditReviewStatusUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportAuditReviewService(db).update_review_status(agency_id, review_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/reviews/{review_id}/findings", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_export_audit_review_finding(
    agency_id: str,
    review_id: str,
    payload: OfferDecisionExportAuditReviewFindingCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportAuditReviewService(db).add_finding(agency_id, review_id, payload)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.patch("/findings/{finding_id}")
async def update_agency_offer_decision_export_audit_review_finding(
    agency_id: str,
    finding_id: str,
    payload: OfferDecisionExportAuditReviewFindingUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportAuditReviewService(db).update_finding(agency_id, finding_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/findings")
async def list_agency_offer_decision_export_audit_review_findings(
    agency_id: str,
    review_id: str | None = Query(default=None),
    finding_status: str | None = Query(default=None, alias="status"),
    finding_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportAuditReviewService(db).list_findings(agency_id=agency_id, review_id=review_id, finding_status=finding_status, finding_type=finding_type)}


@router.post("/reviews/{review_id}/checklist-items", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_export_audit_review_checklist_item(
    agency_id: str,
    review_id: str,
    payload: OfferDecisionExportAuditReviewChecklistItemCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportAuditReviewService(db).add_checklist_item(agency_id, review_id, payload)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.patch("/checklist-items/{item_id}")
async def update_agency_offer_decision_export_audit_review_checklist_item(
    agency_id: str,
    item_id: str,
    payload: OfferDecisionExportAuditReviewChecklistItemUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportAuditReviewService(db).update_checklist_item(agency_id, item_id, payload)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/checklist-items")
async def list_agency_offer_decision_export_audit_review_checklist_items(
    agency_id: str,
    review_id: str | None = Query(default=None),
    item_status: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportAuditReviewService(db).list_checklist_items(agency_id=agency_id, review_id=review_id, item_status=item_status)}


@router.post("/reviews/{review_id}/snapshots", status_code=status.HTTP_201_CREATED)
async def create_agency_offer_decision_export_audit_review_snapshot(
    agency_id: str,
    review_id: str,
    payload: OfferDecisionExportAuditReviewSnapshotCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OfferDecisionExportAuditReviewService(db).create_snapshot(agency_id, review_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/snapshots")
async def list_agency_offer_decision_export_audit_review_snapshots(
    agency_id: str,
    review_id: str | None = Query(default=None),
    snapshot_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await OfferDecisionExportAuditReviewService(db).list_snapshots(agency_id=agency_id, review_id=review_id, snapshot_type=snapshot_type)}
