from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from auth import get_current_user
from database import Database, get_database
from services.rollout_dashboard_service import RolloutDashboardService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/rollout-dashboard", tags=["agency-rollout-dashboard"])

AGENCY_READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_agency_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, AGENCY_READ_ROLES)


@router.get("")
async def get_agency_rollout_dashboard(
    agency_id: str,
    bundle_id: str | None = Query(default=None),
    feature_state: str | None = Query(default=None),
    readiness_status: str | None = Query(default=None),
    rollout_stage: str | None = Query(default=None),
    capability_category: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return await RolloutDashboardService(db).agency_dashboard(
        agency_id,
        {
            "bundle_id": bundle_id,
            "feature_state": feature_state,
            "readiness_status": readiness_status,
            "rollout_stage": rollout_stage,
            "capability_category": capability_category,
        },
    )


@router.get("/summary")
async def summarize_agency_rollout_dashboard(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return await RolloutDashboardService(db).agency_summary(agency_id)


@router.get("/snapshots")
async def list_agency_rollout_dashboard_snapshots(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return await RolloutDashboardService(db).agency_snapshots(agency_id)
