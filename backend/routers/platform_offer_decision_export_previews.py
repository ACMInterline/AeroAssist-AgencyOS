from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from auth import get_current_user
from database import Database, get_database
from services.offer_decision_export_preview_service import OfferDecisionExportPreviewService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/offer-decision-export-previews", tags=["platform-offer-decision-export-previews"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor", "platform_support"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


@router.get("/summary")
async def get_platform_offer_decision_export_preview_summary(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        **await OfferDecisionExportPreviewService(db).summary(),
        "platform_read_only_diagnostics": True,
        "operational_execution_disabled": True,
    }


@router.get("/previews")
async def list_platform_offer_decision_export_previews(
    export_id: str | None = Query(default=None),
    decision_pack_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionExportPreviewService(db).list_previews(export_id=export_id, decision_pack_id=decision_pack_id),
        "read_only": True,
    }


@router.get("/previews/{preview_id}")
async def get_platform_offer_decision_export_preview(
    preview_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    detail = await OfferDecisionExportPreviewService(db).get_preview_detail(preview_id)
    return {
        **(detail or {"preview": None, "sections": [], "blocks": [], "validations": [], "snapshots": []}),
        "read_only": True,
    }


@router.get("/sections")
async def list_platform_offer_decision_export_preview_sections(
    preview_id: str | None = Query(default=None),
    export_id: str | None = Query(default=None),
    decision_pack_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {"items": await OfferDecisionExportPreviewService(db).list_sections(preview_id=preview_id, export_id=export_id, decision_pack_id=decision_pack_id), "read_only": True}


@router.get("/blocks")
async def list_platform_offer_decision_export_preview_blocks(
    preview_id: str | None = Query(default=None),
    section_id: str | None = Query(default=None),
    export_id: str | None = Query(default=None),
    decision_pack_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {"items": await OfferDecisionExportPreviewService(db).list_blocks(preview_id=preview_id, section_id=section_id, export_id=export_id, decision_pack_id=decision_pack_id), "read_only": True}


@router.get("/validations")
async def list_platform_offer_decision_export_preview_validations(
    preview_id: str | None = Query(default=None),
    export_id: str | None = Query(default=None),
    decision_pack_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {"items": await OfferDecisionExportPreviewService(db).list_validations(preview_id=preview_id, export_id=export_id, decision_pack_id=decision_pack_id), "read_only": True}


@router.get("/snapshots")
async def list_platform_offer_decision_export_preview_snapshots(
    preview_id: str | None = Query(default=None),
    export_id: str | None = Query(default=None),
    decision_pack_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {"items": await OfferDecisionExportPreviewService(db).list_snapshots(preview_id=preview_id, export_id=export_id, decision_pack_id=decision_pack_id), "read_only": True}
