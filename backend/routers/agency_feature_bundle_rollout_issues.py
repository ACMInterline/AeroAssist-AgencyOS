from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.feature_bundle_rollout_issue_service import PHASE_LABEL, FeatureBundleRolloutIssueService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/feature-bundle-rollout-issues", tags=["agency-feature-bundle-rollout-issues"])

AGENCY_READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_agency_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, AGENCY_READ_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_agency_feature_bundle_rollout_issues(
    agency_id: str,
    bundle_id: str | None = Query(default=None),
    rollout_plan_id: str | None = Query(default=None),
    risk_id: str | None = Query(default=None),
    dependency_id: str | None = Query(default=None),
    approval_id: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return await FeatureBundleRolloutIssueService(db).agency_response(
        agency_id,
        bundle_id=bundle_id,
        rollout_plan_id=rollout_plan_id,
        risk_id=risk_id,
        dependency_id=dependency_id,
        approval_id=approval_id,
        severity=severity,
        status=status_filter,
    )


@router.get("/summary")
async def summarize_agency_feature_bundle_rollout_issues(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return await FeatureBundleRolloutIssueService(db).agency_summary(agency_id)


@router.get("/{issue_id}")
async def get_agency_feature_bundle_rollout_issue(
    agency_id: str,
    issue_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    service = FeatureBundleRolloutIssueService(db)
    try:
        issue = await service.get_agency_issue(agency_id, issue_id)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "issue": issue,
        "read_only": True,
        "metadata_only": True,
        **service.safety_flags(),
    }
