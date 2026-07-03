from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from auth import get_current_user
from database import Database, get_database
from services.offer_decision_export_release_service import OfferDecisionExportReleaseService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/offer-decision-export-releases", tags=["platform-offer-decision-export-releases"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor", "platform_support"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


@router.get("/summary")
async def get_platform_offer_decision_export_release_summary(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        **await OfferDecisionExportReleaseService(db).summary(),
        "platform_read_only_diagnostics": True,
        "operational_execution_disabled": True,
    }


@router.get("/approvals")
async def list_platform_offer_decision_export_approvals(
    preview_id: str | None = Query(default=None),
    export_id: str | None = Query(default=None),
    approval_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionExportReleaseService(db).list_approvals(preview_id=preview_id, export_id=export_id, approval_status=approval_status),
        "read_only": True,
    }


@router.get("/readiness")
async def list_platform_offer_decision_export_release_readiness(
    approval_id: str | None = Query(default=None),
    preview_id: str | None = Query(default=None),
    export_id: str | None = Query(default=None),
    readiness_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionExportReleaseService(db).list_readiness(approval_id=approval_id, preview_id=preview_id, export_id=export_id, readiness_status=readiness_status),
        "read_only": True,
    }


@router.get("/holds")
async def list_platform_offer_decision_export_release_holds(
    readiness_id: str | None = Query(default=None),
    approval_id: str | None = Query(default=None),
    preview_id: str | None = Query(default=None),
    export_id: str | None = Query(default=None),
    hold_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionExportReleaseService(db).list_holds(readiness_id=readiness_id, approval_id=approval_id, preview_id=preview_id, export_id=export_id, hold_status=hold_status),
        "read_only": True,
    }


@router.get("/snapshots")
async def list_platform_offer_decision_export_release_snapshots(
    readiness_id: str | None = Query(default=None),
    approval_id: str | None = Query(default=None),
    preview_id: str | None = Query(default=None),
    export_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionExportReleaseService(db).list_snapshots(readiness_id=readiness_id, approval_id=approval_id, preview_id=preview_id, export_id=export_id),
        "read_only": True,
    }
