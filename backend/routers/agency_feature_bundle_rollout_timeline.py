from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.feature_bundle_rollout_timeline_service import PHASE_LABEL, FeatureBundleRolloutTimelineService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/feature-bundle-rollout-timeline", tags=["agency-feature-bundle-rollout-timeline"])

AGENCY_READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_agency_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, AGENCY_READ_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_agency_feature_bundle_rollout_timeline_entries(
    agency_id: str,
    rollout_plan_id: str | None = Query(default=None),
    bundle_id: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return await FeatureBundleRolloutTimelineService(db).agency_response(
        agency_id,
        rollout_plan_id=rollout_plan_id,
        bundle_id=bundle_id,
        event_type=event_type,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/summary")
async def summarize_agency_feature_bundle_rollout_timeline_entries(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return await FeatureBundleRolloutTimelineService(db).agency_summary(agency_id)


@router.get("/{timeline_entry_id}")
async def get_agency_feature_bundle_rollout_timeline_entry(
    agency_id: str,
    timeline_entry_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    service = FeatureBundleRolloutTimelineService(db)
    try:
        entry = await service.get_agency_entry(agency_id, timeline_entry_id)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "entry": entry,
        "read_only": True,
        "metadata_only": True,
        **service.safety_flags(),
    }
