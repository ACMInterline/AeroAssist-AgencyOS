from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.feature_bundle_rollout_change_request_service import PHASE_LABEL, FeatureBundleRolloutChangeRequestService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/feature-bundle-rollout-change-requests", tags=["agency-feature-bundle-rollout-change-requests"])

AGENCY_READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_agency_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, AGENCY_READ_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_agency_feature_bundle_rollout_change_requests(
    agency_id: str,
    rollout_plan_id: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    priority: str | None = Query(default=None),
    impact_level: str | None = Query(default=None),
    change_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return await FeatureBundleRolloutChangeRequestService(db).agency_response(
        agency_id,
        rollout_plan_id=rollout_plan_id,
        status=status_filter,
        priority=priority,
        impact_level=impact_level,
        change_type=change_type,
    )


@router.get("/summary")
async def summarize_agency_feature_bundle_rollout_change_requests(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return await FeatureBundleRolloutChangeRequestService(db).agency_summary(agency_id)


@router.get("/{change_request_id}")
async def get_agency_feature_bundle_rollout_change_request(
    agency_id: str,
    change_request_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    service = FeatureBundleRolloutChangeRequestService(db)
    try:
        change_request = await service.get_agency_change_request(agency_id, change_request_id)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "change_request": change_request,
        "read_only": True,
        "metadata_only": True,
        **service.safety_flags(),
    }
