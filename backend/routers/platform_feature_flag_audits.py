from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from auth import get_current_user
from database import Database, get_database
from services.agency_feature_flag_audit_service import AgencyFeatureFlagAuditService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/feature-flags", tags=["platform-feature-flag-audits"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


@router.get("/audits")
async def list_platform_feature_flag_audits(
    agency_id: str | None = Query(default=None),
    feature_key: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AgencyFeatureFlagAuditService(db).platform_audits_response(agency_id=agency_id, feature_key=feature_key)


@router.get("/readiness")
async def list_platform_feature_flag_readiness(
    agency_id: str | None = Query(default=None),
    feature_key: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AgencyFeatureFlagAuditService(db).platform_readiness_response(agency_id=agency_id, feature_key=feature_key)


@router.get("/readiness/{feature_key}")
async def get_platform_feature_flag_readiness(
    feature_key: str,
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AgencyFeatureFlagAuditService(db).platform_readiness_response(agency_id=agency_id, feature_key=feature_key)
