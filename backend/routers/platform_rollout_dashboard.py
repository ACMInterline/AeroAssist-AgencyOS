from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from auth import get_current_user
from database import Database, get_database
from services.rollout_dashboard_service import RolloutDashboardService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/rollout-dashboard", tags=["platform-rollout-dashboard"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


@router.get("")
async def get_platform_rollout_dashboard(
    agency_id: str | None = Query(default=None),
    bundle_id: str | None = Query(default=None),
    feature_state: str | None = Query(default=None),
    readiness_status: str | None = Query(default=None),
    rollout_stage: str | None = Query(default=None),
    capability_category: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await RolloutDashboardService(db).platform_dashboard(
        {
            "agency_id": agency_id,
            "bundle_id": bundle_id,
            "feature_state": feature_state,
            "readiness_status": readiness_status,
            "rollout_stage": rollout_stage,
            "capability_category": capability_category,
        }
    )


@router.get("/summary")
async def summarize_platform_rollout_dashboard(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await RolloutDashboardService(db).platform_summary({"agency_id": agency_id})


@router.get("/snapshots")
async def list_platform_rollout_dashboard_snapshots(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await RolloutDashboardService(db).platform_snapshots(agency_id=agency_id)


@router.get("/filters")
async def list_platform_rollout_dashboard_filters(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await RolloutDashboardService(db).platform_filters()
