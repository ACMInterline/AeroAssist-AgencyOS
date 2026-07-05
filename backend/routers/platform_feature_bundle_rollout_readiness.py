from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from auth import get_current_user
from database import Database, get_database
from services.feature_bundle_rollout_readiness_service import FeatureBundleRolloutReadinessService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/feature-bundle-rollout-readiness", tags=["platform-feature-bundle-rollout-readiness"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


@router.get("")
async def list_platform_feature_bundle_rollout_readiness(
    agency_id: str | None = Query(default=None),
    readiness_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await FeatureBundleRolloutReadinessService(db).platform_response(agency_id=agency_id, readiness_status=readiness_status)


@router.get("/summary")
async def summarize_platform_feature_bundle_rollout_readiness(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await FeatureBundleRolloutReadinessService(db).platform_summary(agency_id=agency_id)


@router.post("/defaults", status_code=status.HTTP_201_CREATED)
async def create_platform_feature_bundle_rollout_readiness_defaults(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await FeatureBundleRolloutReadinessService(db).create_default_readiness_records(agency_id=agency_id, user=user)
