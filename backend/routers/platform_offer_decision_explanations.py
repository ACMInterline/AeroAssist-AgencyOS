from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from auth import get_current_user
from database import Database, get_database
from services.offer_decision_explanation_service import OfferDecisionExplanationService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/offer-decision-explanations", tags=["platform-offer-decision-explanations"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor", "platform_support"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


@router.get("/summary")
async def get_platform_offer_decision_explanation_summary(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        **await OfferDecisionExplanationService(db).summary(),
        "platform_read_only_diagnostics": True,
        "operational_execution_disabled": True,
    }


@router.get("/explanations")
async def list_platform_offer_decision_explanations(
    decision_pack_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {"items": await OfferDecisionExplanationService(db).list_explanations(decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id), "read_only": True}


@router.get("/timeline")
async def list_platform_offer_decision_timeline(
    decision_pack_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {"items": await OfferDecisionExplanationService(db).list_timeline(decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id), "read_only": True}


@router.get("/evidence")
async def list_platform_offer_decision_evidence_references(
    decision_pack_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {"items": await OfferDecisionExplanationService(db).list_evidence_references(decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id), "read_only": True}


@router.get("/reasons")
async def list_platform_offer_decision_reasons(
    decision_pack_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {"items": await OfferDecisionExplanationService(db).list_reasons(decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id), "read_only": True}


@router.get("/acknowledgements")
async def list_platform_offer_decision_acknowledgements(
    decision_pack_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {"items": await OfferDecisionExplanationService(db).list_acknowledgements(decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id), "read_only": True}


@router.get("/snapshots")
async def list_platform_offer_decision_audit_snapshots(
    decision_pack_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {"items": await OfferDecisionExplanationService(db).list_snapshots(decision_pack_id=decision_pack_id, offer_workspace_id=offer_workspace_id), "read_only": True}
