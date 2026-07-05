from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import FeatureBundleRolloutPlanCreate, FeatureBundleRolloutPlanUpdate
from services.feature_bundle_rollout_plan_service import PHASE_LABEL, FeatureBundleRolloutPlanService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/feature-bundle-rollout-plans", tags=["platform-feature-bundle-rollout-plans"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_platform_feature_bundle_rollout_plans(
    agency_id: str | None = Query(default=None),
    rollout_stage: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await FeatureBundleRolloutPlanService(db).platform_response(agency_id=agency_id, rollout_stage=rollout_stage)


@router.get("/summary")
async def summarize_platform_feature_bundle_rollout_plans(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await FeatureBundleRolloutPlanService(db).platform_summary(agency_id=agency_id)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_platform_feature_bundle_rollout_plan(
    payload: FeatureBundleRolloutPlanCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await FeatureBundleRolloutPlanService(db).create_plan(payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{rollout_plan_id}")
async def get_platform_feature_bundle_rollout_plan(
    rollout_plan_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = FeatureBundleRolloutPlanService(db)
    try:
        plan = await service.get_platform_plan(rollout_plan_id)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "plan": plan,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{rollout_plan_id}")
async def update_platform_feature_bundle_rollout_plan(
    rollout_plan_id: str,
    payload: FeatureBundleRolloutPlanUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await FeatureBundleRolloutPlanService(db).update_plan(rollout_plan_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
