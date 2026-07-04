from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from auth import get_current_user
from database import Database, get_database
from services.agency_feature_flag_bundle_service import AgencyFeatureFlagBundleService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/feature-flag-bundles", tags=["platform-feature-flag-bundles"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


@router.get("")
async def list_platform_feature_flag_bundles(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AgencyFeatureFlagBundleService(db).platform_bundles_response()


@router.get("/reviews")
async def list_platform_feature_flag_bundle_reviews(
    bundle_id: str | None = Query(default=None),
    bundle_key: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AgencyFeatureFlagBundleService(db).platform_reviews_response(bundle_id=bundle_id, bundle_key=bundle_key)


@router.get("/{bundle_id}")
async def get_platform_feature_flag_bundle(
    bundle_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AgencyFeatureFlagBundleService(db).platform_bundle_detail_response(bundle_id)


@router.get("/{bundle_id}/members")
async def list_platform_feature_flag_bundle_members(
    bundle_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AgencyFeatureFlagBundleService(db).platform_members_response(bundle_id)
