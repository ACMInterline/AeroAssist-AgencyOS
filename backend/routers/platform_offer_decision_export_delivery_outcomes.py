from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from auth import get_current_user
from database import Database, get_database
from services.offer_decision_export_delivery_outcome_service import OfferDecisionExportDeliveryOutcomeService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/offer-decision-export-delivery-outcomes", tags=["platform-offer-decision-export-delivery-outcomes"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor", "platform_support"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


@router.get("/summary")
async def get_platform_offer_decision_export_delivery_outcome_summary(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        **await OfferDecisionExportDeliveryOutcomeService(db).summary(),
        "platform_read_only_diagnostics": True,
        "operational_execution_disabled": True,
    }


@router.get("/outcomes")
async def list_platform_offer_decision_export_delivery_outcomes(
    handoff_id: str | None = Query(default=None),
    export_id: str | None = Query(default=None),
    outcome_status: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionExportDeliveryOutcomeService(db).list_outcomes(handoff_id=handoff_id, export_id=export_id, outcome_status=outcome_status),
        "read_only": True,
    }


@router.get("/outcomes/{outcome_id}")
async def get_platform_offer_decision_export_delivery_outcome(
    outcome_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    detail = await OfferDecisionExportDeliveryOutcomeService(db).get_outcome_detail(outcome_id)
    return {
        **(detail or {"outcome": None, "events": [], "receipts": [], "issues": [], "snapshots": []}),
        "read_only": True,
    }


@router.get("/events")
async def list_platform_offer_decision_export_delivery_outcome_events(
    outcome_id: str | None = Query(default=None),
    handoff_id: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionExportDeliveryOutcomeService(db).list_events(outcome_id=outcome_id, handoff_id=handoff_id, event_type=event_type),
        "read_only": True,
    }


@router.get("/receipts")
async def list_platform_offer_decision_export_delivery_receipts(
    outcome_id: str | None = Query(default=None),
    handoff_id: str | None = Query(default=None),
    receipt_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionExportDeliveryOutcomeService(db).list_receipts(outcome_id=outcome_id, handoff_id=handoff_id, receipt_type=receipt_type),
        "read_only": True,
    }


@router.get("/issues")
async def list_platform_offer_decision_export_delivery_issues(
    outcome_id: str | None = Query(default=None),
    handoff_id: str | None = Query(default=None),
    issue_status: str | None = Query(default=None, alias="status"),
    issue_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionExportDeliveryOutcomeService(db).list_issues(outcome_id=outcome_id, handoff_id=handoff_id, issue_status=issue_status, issue_type=issue_type),
        "read_only": True,
    }


@router.get("/snapshots")
async def list_platform_offer_decision_export_delivery_outcome_snapshots(
    outcome_id: str | None = Query(default=None),
    handoff_id: str | None = Query(default=None),
    snapshot_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionExportDeliveryOutcomeService(db).list_snapshots(outcome_id=outcome_id, handoff_id=handoff_id, snapshot_type=snapshot_type),
        "read_only": True,
    }
