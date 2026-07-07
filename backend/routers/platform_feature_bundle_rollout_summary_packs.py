from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import FeatureBundleRolloutSummaryPackCreate, FeatureBundleRolloutSummaryPackUpdate
from services.feature_bundle_rollout_summary_pack_service import PHASE_LABEL, FeatureBundleRolloutSummaryPackService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/feature-bundle-rollout-summary-packs", tags=["platform-feature-bundle-rollout-summary-packs"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_platform_feature_bundle_rollout_summary_packs(
    rollout_plan_id: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    audience: str | None = Query(default=None),
    bundle_id: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await FeatureBundleRolloutSummaryPackService(db).platform_response(
        rollout_plan_id=rollout_plan_id,
        status=status_filter,
        audience=audience,
        bundle_id=bundle_id,
        include_archived=include_archived,
    )


@router.get("/summary")
async def summarize_platform_feature_bundle_rollout_summary_packs(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await FeatureBundleRolloutSummaryPackService(db).platform_summary()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_platform_feature_bundle_rollout_summary_pack(
    payload: FeatureBundleRolloutSummaryPackCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await FeatureBundleRolloutSummaryPackService(db).create_summary_pack(payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{pack_id}")
async def get_platform_feature_bundle_rollout_summary_pack(
    pack_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = FeatureBundleRolloutSummaryPackService(db)
    try:
        summary_pack = await service.get_platform_summary_pack(pack_id)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "summary_pack": summary_pack,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{pack_id}")
async def update_platform_feature_bundle_rollout_summary_pack(
    pack_id: str,
    payload: FeatureBundleRolloutSummaryPackUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await FeatureBundleRolloutSummaryPackService(db).update_summary_pack(pack_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/{pack_id}")
async def delete_platform_feature_bundle_rollout_summary_pack(
    pack_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await FeatureBundleRolloutSummaryPackService(db).delete_summary_pack(pack_id, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
