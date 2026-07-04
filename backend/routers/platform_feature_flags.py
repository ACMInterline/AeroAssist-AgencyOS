from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    AgencyFeatureFlagCreateRequest,
    AgencyFeatureFlagReviewCreateRequest,
    AgencyFeatureFlagSnapshotCreateRequest,
    AgencyFeatureFlagUpdateRequest,
)
from services.agency_feature_flag_service import AgencyFeatureFlagService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/feature-flags", tags=["platform-feature-flags"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("/summary")
async def get_platform_feature_flags_summary(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AgencyFeatureFlagService(db).platform_summary(agency_id=agency_id)


@router.get("/flags")
async def list_platform_feature_flags(
    agency_id: str | None = Query(default=None),
    module_key: str | None = Query(default=None),
    state: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await AgencyFeatureFlagService(db).list_flags(agency_id=agency_id, module_key=module_key, state=state),
        "metadata_only": True,
    }


@router.post("/flags", status_code=status.HTTP_201_CREATED)
async def create_platform_feature_flag(
    payload: AgencyFeatureFlagCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AgencyFeatureFlagService(db).create_flag(payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.patch("/flags/{flag_id}")
async def update_platform_feature_flag(
    flag_id: str,
    payload: AgencyFeatureFlagUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AgencyFeatureFlagService(db).update_flag(flag_id, payload)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/reviews")
async def list_platform_feature_flag_reviews(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await AgencyFeatureFlagService(db).list_reviews(agency_id=agency_id),
        "metadata_only": True,
    }


@router.post("/reviews", status_code=status.HTTP_201_CREATED)
async def create_platform_feature_flag_review(
    payload: AgencyFeatureFlagReviewCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await AgencyFeatureFlagService(db).create_review(payload, user)


@router.get("/snapshots")
async def list_platform_feature_flag_snapshots(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await AgencyFeatureFlagService(db).list_snapshots(agency_id=agency_id),
        "metadata_only": True,
    }


@router.post("/snapshots", status_code=status.HTTP_201_CREATED)
async def create_platform_feature_flag_snapshot(
    payload: AgencyFeatureFlagSnapshotCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await AgencyFeatureFlagService(db).create_snapshot(payload)
