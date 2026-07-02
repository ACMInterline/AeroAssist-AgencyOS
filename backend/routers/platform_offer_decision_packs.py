from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from auth import get_current_user
from database import Database, get_database
from services.offer_decision_pack_service import OfferDecisionPackService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/offer-decision-packs", tags=["platform-offer-decision-packs"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor", "platform_support"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


@router.get("/summary")
async def get_platform_offer_decision_pack_summary(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        **await OfferDecisionPackService(db).summary(),
        "platform_read_only_diagnostics": True,
        "operational_execution_disabled": True,
    }


@router.get("/packs")
async def list_platform_offer_decision_packs(
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferDecisionPackService(db).list_packs(offer_workspace_id=offer_workspace_id),
        "read_only": True,
    }


@router.get("/packs/{pack_id}")
async def get_platform_offer_decision_pack_detail(
    pack_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    detail = await OfferDecisionPackService(db).get_pack_detail(pack_id)
    return {
        **(detail or {"pack": None, "options": [], "evidence": [], "warnings": [], "review_notes": [], "snapshots": []}),
        "read_only": True,
    }


@router.get("/evidence")
async def list_platform_offer_decision_pack_evidence(
    decision_pack_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {"items": await OfferDecisionPackService(db).list_evidence(decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id), "read_only": True}


@router.get("/warnings")
async def list_platform_offer_decision_pack_warnings(
    decision_pack_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {"items": await OfferDecisionPackService(db).list_warnings(decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id), "read_only": True}


@router.get("/review-notes")
async def list_platform_offer_decision_pack_review_notes(
    decision_pack_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {"items": await OfferDecisionPackService(db).list_review_notes(decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id), "read_only": True}


@router.get("/snapshots")
async def list_platform_offer_decision_pack_snapshots(
    decision_pack_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {"items": await OfferDecisionPackService(db).list_snapshots(decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id), "read_only": True}
