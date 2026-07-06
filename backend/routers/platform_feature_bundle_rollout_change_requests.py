from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import FeatureBundleRolloutChangeRequestCreate, FeatureBundleRolloutChangeRequestUpdate
from services.feature_bundle_rollout_change_request_service import PHASE_LABEL, FeatureBundleRolloutChangeRequestService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/feature-bundle-rollout-change-requests", tags=["platform-feature-bundle-rollout-change-requests"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_platform_feature_bundle_rollout_change_requests(
    rollout_plan_id: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    priority: str | None = Query(default=None),
    impact_level: str | None = Query(default=None),
    change_type: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await FeatureBundleRolloutChangeRequestService(db).platform_response(
        rollout_plan_id=rollout_plan_id,
        status=status_filter,
        priority=priority,
        impact_level=impact_level,
        change_type=change_type,
        include_archived=include_archived,
    )


@router.get("/summary")
async def summarize_platform_feature_bundle_rollout_change_requests(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await FeatureBundleRolloutChangeRequestService(db).platform_summary()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_platform_feature_bundle_rollout_change_request(
    payload: FeatureBundleRolloutChangeRequestCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await FeatureBundleRolloutChangeRequestService(db).create_change_request(payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{change_request_id}")
async def get_platform_feature_bundle_rollout_change_request(
    change_request_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = FeatureBundleRolloutChangeRequestService(db)
    try:
        change_request = await service.get_platform_change_request(change_request_id)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "change_request": change_request,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{change_request_id}")
async def update_platform_feature_bundle_rollout_change_request(
    change_request_id: str,
    payload: FeatureBundleRolloutChangeRequestUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await FeatureBundleRolloutChangeRequestService(db).update_change_request(change_request_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/{change_request_id}")
async def delete_platform_feature_bundle_rollout_change_request(
    change_request_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await FeatureBundleRolloutChangeRequestService(db).delete_change_request(change_request_id, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
