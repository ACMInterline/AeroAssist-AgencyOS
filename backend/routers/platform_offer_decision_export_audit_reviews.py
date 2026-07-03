from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from auth import get_current_user
from database import Database, get_database
from services.offer_decision_export_audit_review_service import OfferDecisionExportAuditReviewService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/offer-decision-export-audit-reviews", tags=["platform-offer-decision-export-audit-reviews"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor", "platform_support"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


@router.get("/summary")
async def get_platform_offer_decision_export_audit_review_summary(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        **await OfferDecisionExportAuditReviewService(db).summary(),
        "platform_read_only_diagnostics": True,
        "operational_execution_disabled": True,
    }


@router.get("/diagnostics")
async def get_platform_offer_decision_export_audit_review_diagnostics(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        **await OfferDecisionExportAuditReviewService(db).summary(),
        "read_only": True,
    }


@router.get("/reviews")
async def list_platform_offer_decision_export_audit_reviews(
    export_id: str | None = Query(default=None),
    outcome_id: str | None = Query(default=None),
    review_status: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionExportAuditReviewService(db).list_reviews(export_id=export_id, outcome_id=outcome_id, review_status=review_status),
        "read_only": True,
    }


@router.get("/reviews/{review_id}")
async def get_platform_offer_decision_export_audit_review(
    review_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    detail = await OfferDecisionExportAuditReviewService(db).get_review_detail(review_id)
    return {
        **(detail or {"review": None, "findings": [], "checklist_items": [], "snapshots": [], "source_summary": {}}),
        "read_only": True,
    }


@router.get("/findings")
async def list_platform_offer_decision_export_audit_review_findings(
    review_id: str | None = Query(default=None),
    finding_status: str | None = Query(default=None, alias="status"),
    finding_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionExportAuditReviewService(db).list_findings(review_id=review_id, finding_status=finding_status, finding_type=finding_type),
        "read_only": True,
    }


@router.get("/checklist-items")
async def list_platform_offer_decision_export_audit_review_checklist_items(
    review_id: str | None = Query(default=None),
    item_status: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionExportAuditReviewService(db).list_checklist_items(review_id=review_id, item_status=item_status),
        "read_only": True,
    }


@router.get("/snapshots")
async def list_platform_offer_decision_export_audit_review_snapshots(
    review_id: str | None = Query(default=None),
    snapshot_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionExportAuditReviewService(db).list_snapshots(review_id=review_id, snapshot_type=snapshot_type),
        "read_only": True,
    }
