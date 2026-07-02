from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from auth import get_current_user
from database import Database, get_database
from services.offer_policy_advisor_service import OfferPolicyAdvisorService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/offer-policy-advisor", tags=["platform-offer-policy-advisor"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor", "platform_support"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


@router.get("/summary")
async def get_platform_offer_policy_advisor_summary(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    summary = await OfferPolicyAdvisorService(db).summary()
    return {
        **summary,
        "platform_read_only_diagnostics": True,
        "operational_execution_disabled": True,
    }


@router.get("/contexts")
async def list_platform_offer_policy_advisor_contexts(
    offer_workspace_id: str | None = Query(default=None),
    offer_option_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await OfferPolicyAdvisorService(db).list_contexts(
            offer_workspace_id=offer_workspace_id,
            offer_option_id=offer_option_id,
        ),
        "read_only": True,
    }


@router.get("/contexts/{context_id}")
async def get_platform_offer_policy_advisor_context(
    context_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OfferPolicyAdvisorService(db)
    context = await service.get_context(context_id)
    return {
        "context": context,
        "airline_rows": await service.list_airline_rows(context_id=context_id),
        "warnings": await service.list_warnings(context_id=context_id),
        "decision_notes": await service.list_decision_notes(context_id=context_id),
        "saved_snapshots": await service.list_saved_snapshots(context_id=context_id),
        "read_only": True,
    }


@router.get("/airline-rows")
async def list_platform_offer_policy_advisor_airline_rows(
    context_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {"items": await OfferPolicyAdvisorService(db).list_airline_rows(context_id=context_id, offer_workspace_id=offer_workspace_id), "read_only": True}


@router.get("/warnings")
async def list_platform_offer_policy_advisor_warnings(
    context_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {"items": await OfferPolicyAdvisorService(db).list_warnings(context_id=context_id, offer_workspace_id=offer_workspace_id), "read_only": True}


@router.get("/decision-notes")
async def list_platform_offer_policy_advisor_decision_notes(
    context_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {"items": await OfferPolicyAdvisorService(db).list_decision_notes(context_id=context_id, offer_workspace_id=offer_workspace_id), "read_only": True}


@router.get("/saved-snapshots")
async def list_platform_offer_policy_advisor_saved_snapshots(
    context_id: str | None = Query(default=None),
    offer_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {"items": await OfferPolicyAdvisorService(db).list_saved_snapshots(context_id=context_id, offer_workspace_id=offer_workspace_id), "read_only": True}
