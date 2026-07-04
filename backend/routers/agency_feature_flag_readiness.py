from __future__ import annotations

from fastapi import APIRouter, Depends

from auth import get_current_user
from database import Database, get_database
from services.agency_feature_flag_audit_service import AgencyFeatureFlagAuditService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/feature-readiness", tags=["agency-feature-flag-readiness"])

AGENCY_READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_agency_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, AGENCY_READ_ROLES)


@router.get("")
async def list_agency_feature_readiness(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return await AgencyFeatureFlagAuditService(db).agency_readiness_response(agency_id)


@router.get("/{feature_key}")
async def get_agency_feature_readiness(
    agency_id: str,
    feature_key: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return await AgencyFeatureFlagAuditService(db).agency_readiness_response(agency_id, feature_key=feature_key)
