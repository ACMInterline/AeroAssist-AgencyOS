from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from auth import get_current_user
from database import Database, get_database
from services.offer_decision_export_service import OfferDecisionExportService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/offer-decision-exports", tags=["platform-offer-decision-exports"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor", "platform_support"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


@router.get("/summary")
async def get_platform_offer_decision_export_summary(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        **await OfferDecisionExportService(db).summary(),
        "platform_read_only_diagnostics": True,
        "operational_execution_disabled": True,
    }


@router.get("/exports")
async def list_platform_offer_decision_exports(
    decision_pack_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionExportService(db).list_exports(decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id),
        "read_only": True,
    }


@router.get("/exports/{export_id}")
async def get_platform_offer_decision_export(
    export_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    detail = await OfferDecisionExportService(db).get_export_detail(export_id)
    return {
        **(detail or {"export": None, "sections": [], "artifacts": [], "recipient_drafts": [], "audit_events": []}),
        "read_only": True,
    }


@router.get("/artifacts")
async def list_platform_offer_decision_export_artifacts(
    export_id: str | None = Query(default=None),
    decision_pack_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {"items": await OfferDecisionExportService(db).list_artifacts(export_id=export_id, decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id), "read_only": True}


@router.get("/audit-events")
async def list_platform_offer_decision_export_audit_events(
    export_id: str | None = Query(default=None),
    decision_pack_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {"items": await OfferDecisionExportService(db).list_audit_events(export_id=export_id, decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id), "read_only": True}
