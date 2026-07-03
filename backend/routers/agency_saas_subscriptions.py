from __future__ import annotations

from fastapi import APIRouter, Depends

from auth import get_current_user
from database import Database, get_database
from services.saas_subscription_service import SaaSSubscriptionService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/saas-subscriptions", tags=["agency-saas-subscriptions"])

AGENCY_READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_agency_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, AGENCY_READ_ROLES)


@router.get("/summary")
async def get_agency_saas_subscription_summary(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return await SaaSSubscriptionService(db).agency_summary(agency_id)


@router.get("/assignments")
async def list_agency_saas_subscription_assignments(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return {
        "items": await SaaSSubscriptionService(db).list_assignments(agency_id=agency_id, agency_view=True),
        "read_only": True,
        "payloads_hidden": True,
    }


@router.get("/readiness")
async def list_agency_saas_entitlement_readiness(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return {
        "items": await SaaSSubscriptionService(db).list_readiness(agency_id=agency_id, agency_view=True),
        "read_only": True,
        "payloads_hidden": True,
    }


@router.get("/notes")
async def list_agency_saas_subscription_notes(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return {
        "items": await SaaSSubscriptionService(db).list_notes(agency_id=agency_id, visible_to_agency=True, agency_view=True),
        "read_only": True,
        "payloads_hidden": True,
    }


@router.get("/snapshots")
async def list_agency_saas_subscription_snapshots(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return {
        "items": await SaaSSubscriptionService(db).list_snapshots(agency_id=agency_id, agency_view=True),
        "read_only": True,
        "payloads_hidden": True,
    }
