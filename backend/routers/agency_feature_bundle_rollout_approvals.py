from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.feature_bundle_rollout_approval_service import PHASE_LABEL, FeatureBundleRolloutApprovalService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/feature-bundle-rollout-approvals", tags=["agency-feature-bundle-rollout-approvals"])

AGENCY_READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_agency_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, AGENCY_READ_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_agency_feature_bundle_rollout_approvals(
    agency_id: str,
    approval_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return await FeatureBundleRolloutApprovalService(db).agency_response(agency_id, status=approval_status)


@router.get("/summary")
async def summarize_agency_feature_bundle_rollout_approvals(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return await FeatureBundleRolloutApprovalService(db).agency_summary(agency_id)


@router.get("/{approval_id}")
async def get_agency_feature_bundle_rollout_approval(
    agency_id: str,
    approval_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    service = FeatureBundleRolloutApprovalService(db)
    try:
        approval = await service.get_agency_approval(agency_id, approval_id)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "approval": approval,
        "read_only": True,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.get("/{approval_id}/notes")
async def list_agency_feature_bundle_rollout_approval_notes(
    agency_id: str,
    approval_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    try:
        return await FeatureBundleRolloutApprovalService(db).notes_response(approval_id, agency_id=agency_id)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{approval_id}/timeline")
async def list_agency_feature_bundle_rollout_approval_timeline(
    agency_id: str,
    approval_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    try:
        return await FeatureBundleRolloutApprovalService(db).timeline_response(approval_id, agency_id=agency_id)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
