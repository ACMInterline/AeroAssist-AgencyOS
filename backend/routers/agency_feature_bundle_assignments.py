from __future__ import annotations

from fastapi import APIRouter, Depends

from auth import get_current_user
from database import Database, get_database
from services.agency_feature_bundle_assignment_service import AgencyFeatureBundleAssignmentService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}", tags=["agency-feature-bundle-assignments"])

AGENCY_READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_agency_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, AGENCY_READ_ROLES)


@router.get("/feature-bundle-assignments")
async def list_agency_feature_bundle_assignments(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return await AgencyFeatureBundleAssignmentService(db).agency_assignments_response(agency_id)


@router.get("/feature-bundle-assignment-history")
async def list_agency_feature_bundle_assignment_history(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return await AgencyFeatureBundleAssignmentService(db).agency_history_response(agency_id)
