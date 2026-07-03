from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from auth import get_current_user
from database import Database, get_database
from services.offer_decision_export_delivery_service import OfferDecisionExportDeliveryService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/offer-decision-export-deliveries", tags=["platform-offer-decision-export-deliveries"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor", "platform_support"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


@router.get("/summary")
async def get_platform_offer_decision_export_delivery_summary(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        **await OfferDecisionExportDeliveryService(db).summary(),
        "platform_read_only_diagnostics": True,
        "operational_execution_disabled": True,
    }


@router.get("/handoffs")
async def list_platform_offer_decision_export_delivery_handoffs(
    export_id: str | None = Query(default=None),
    preview_id: str | None = Query(default=None),
    release_readiness_id: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionExportDeliveryService(db).list_handoffs(export_id=export_id, preview_id=preview_id, release_readiness_id=release_readiness_id, status=status_filter),
        "read_only": True,
    }


@router.get("/handoffs/{handoff_id}")
async def get_platform_offer_decision_export_delivery_handoff(
    handoff_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    detail = await OfferDecisionExportDeliveryService(db).get_handoff_detail(handoff_id)
    return {
        **(detail or {"handoff": None, "recipients": [], "attachments": [], "instructions": [], "snapshots": []}),
        "read_only": True,
    }


@router.get("/recipients")
async def list_platform_offer_decision_export_delivery_recipients(
    handoff_id: str | None = Query(default=None),
    delivery_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionExportDeliveryService(db).list_recipients(handoff_id=handoff_id, delivery_status=delivery_status),
        "read_only": True,
    }


@router.get("/attachments")
async def list_platform_offer_decision_export_delivery_attachments(
    handoff_id: str | None = Query(default=None),
    artifact_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionExportDeliveryService(db).list_attachments(handoff_id=handoff_id, artifact_id=artifact_id),
        "read_only": True,
    }


@router.get("/instructions")
async def list_platform_offer_decision_export_delivery_instructions(
    handoff_id: str | None = Query(default=None),
    completed: bool | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionExportDeliveryService(db).list_instructions(handoff_id=handoff_id, completed=completed),
        "read_only": True,
    }


@router.get("/snapshots")
async def list_platform_offer_decision_export_delivery_snapshots(
    handoff_id: str | None = Query(default=None),
    snapshot_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionExportDeliveryService(db).list_snapshots(handoff_id=handoff_id, snapshot_type=snapshot_type),
        "read_only": True,
    }
