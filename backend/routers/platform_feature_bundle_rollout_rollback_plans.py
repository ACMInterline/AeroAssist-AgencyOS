from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import FeatureBundleRolloutRollbackPlanCreate, FeatureBundleRolloutRollbackPlanUpdate
from services.feature_bundle_rollout_rollback_plan_service import PHASE_LABEL, FeatureBundleRolloutRollbackPlanService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/feature-bundle-rollout-rollback-plans", tags=["platform-feature-bundle-rollout-rollback-plans"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_platform_feature_bundle_rollout_rollback_plans(
    rollout_plan_id: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    priority: str | None = Query(default=None),
    scope: str | None = Query(default=None),
    owner: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await FeatureBundleRolloutRollbackPlanService(db).platform_response(
        rollout_plan_id=rollout_plan_id,
        status=status_filter,
        priority=priority,
        scope=scope,
        owner=owner,
        include_archived=include_archived,
    )


@router.get("/summary")
async def summarize_platform_feature_bundle_rollout_rollback_plans(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await FeatureBundleRolloutRollbackPlanService(db).platform_summary()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_platform_feature_bundle_rollout_rollback_plan(
    payload: FeatureBundleRolloutRollbackPlanCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await FeatureBundleRolloutRollbackPlanService(db).create_rollback_plan(payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{rollback_plan_id}")
async def get_platform_feature_bundle_rollout_rollback_plan(
    rollback_plan_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = FeatureBundleRolloutRollbackPlanService(db)
    try:
        rollback_plan = await service.get_platform_rollback_plan(rollback_plan_id)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "rollback_plan": rollback_plan,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{rollback_plan_id}")
async def update_platform_feature_bundle_rollout_rollback_plan(
    rollback_plan_id: str,
    payload: FeatureBundleRolloutRollbackPlanUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await FeatureBundleRolloutRollbackPlanService(db).update_rollback_plan(rollback_plan_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/{rollback_plan_id}")
async def delete_platform_feature_bundle_rollout_rollback_plan(
    rollback_plan_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await FeatureBundleRolloutRollbackPlanService(db).delete_rollback_plan(rollback_plan_id, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
