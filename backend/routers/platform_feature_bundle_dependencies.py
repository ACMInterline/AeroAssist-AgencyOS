from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import FeatureBundleDependencyCreate, FeatureBundleDependencyUpdate
from services.feature_bundle_dependency_service import PHASE_LABEL, FeatureBundleDependencyService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/feature-bundle-dependencies", tags=["platform-feature-bundle-dependencies"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_platform_feature_bundle_dependencies(
    agency_id: str | None = Query(default=None),
    bundle_id: str | None = Query(default=None),
    rollout_plan_id: str | None = Query(default=None),
    dependency_type: str | None = Query(default=None),
    include_deleted: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await FeatureBundleDependencyService(db).platform_response(
        agency_id=agency_id,
        bundle_id=bundle_id,
        rollout_plan_id=rollout_plan_id,
        dependency_type=dependency_type,
        include_deleted=include_deleted,
    )


@router.get("/summary")
async def summarize_platform_feature_bundle_dependencies(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await FeatureBundleDependencyService(db).platform_summary(agency_id=agency_id)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_platform_feature_bundle_dependency(
    payload: FeatureBundleDependencyCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await FeatureBundleDependencyService(db).create_dependency(payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{dependency_id}")
async def get_platform_feature_bundle_dependency(
    dependency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = FeatureBundleDependencyService(db)
    try:
        dependency = await service.get_platform_dependency(dependency_id)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "dependency": dependency,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{dependency_id}")
async def update_platform_feature_bundle_dependency(
    dependency_id: str,
    payload: FeatureBundleDependencyUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await FeatureBundleDependencyService(db).update_dependency(dependency_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/{dependency_id}")
async def delete_platform_feature_bundle_dependency(
    dependency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await FeatureBundleDependencyService(db).delete_dependency(dependency_id, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
