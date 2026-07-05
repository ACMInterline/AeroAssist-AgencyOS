from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    FeatureBundleRolloutApprovalCreate,
    FeatureBundleRolloutApprovalNoteCreate,
    FeatureBundleRolloutApprovalUpdate,
)
from services.feature_bundle_rollout_approval_service import PHASE_LABEL, FeatureBundleRolloutApprovalService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/feature-bundle-rollout-approvals", tags=["platform-feature-bundle-rollout-approvals"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_platform_feature_bundle_rollout_approvals(
    agency_id: str | None = Query(default=None),
    rollout_plan_id: str | None = Query(default=None),
    approval_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await FeatureBundleRolloutApprovalService(db).platform_response(
        agency_id=agency_id,
        rollout_plan_id=rollout_plan_id,
        status=approval_status,
    )


@router.get("/summary")
async def summarize_platform_feature_bundle_rollout_approvals(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await FeatureBundleRolloutApprovalService(db).platform_summary(agency_id=agency_id)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_platform_feature_bundle_rollout_approval(
    payload: FeatureBundleRolloutApprovalCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await FeatureBundleRolloutApprovalService(db).create_approval(payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{approval_id}")
async def get_platform_feature_bundle_rollout_approval(
    approval_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = FeatureBundleRolloutApprovalService(db)
    try:
        approval = await service.get_platform_approval(approval_id)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "approval": approval,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{approval_id}")
async def update_platform_feature_bundle_rollout_approval(
    approval_id: str,
    payload: FeatureBundleRolloutApprovalUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await FeatureBundleRolloutApprovalService(db).update_approval(approval_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{approval_id}/notes")
async def list_platform_feature_bundle_rollout_approval_notes(
    approval_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    try:
        return await FeatureBundleRolloutApprovalService(db).notes_response(approval_id)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/{approval_id}/notes", status_code=status.HTTP_201_CREATED)
async def create_platform_feature_bundle_rollout_approval_note(
    approval_id: str,
    payload: FeatureBundleRolloutApprovalNoteCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await FeatureBundleRolloutApprovalService(db).create_note(approval_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{approval_id}/timeline")
async def list_platform_feature_bundle_rollout_approval_timeline(
    approval_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    try:
        return await FeatureBundleRolloutApprovalService(db).timeline_response(approval_id)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
