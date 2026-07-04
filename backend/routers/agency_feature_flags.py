from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from auth import get_current_user
from database import Database, get_database
from services.agency_feature_flag_service import AgencyFeatureFlagService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/feature-flags", tags=["agency-feature-flags"])

AGENCY_READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_agency_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, AGENCY_READ_ROLES)


@router.get("/summary")
async def get_agency_feature_flags_summary(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return await AgencyFeatureFlagService(db).agency_summary(agency_id)


@router.get("/flags")
async def list_agency_feature_flags(
    agency_id: str,
    module_key: str | None = Query(default=None),
    state: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return {
        "items": await AgencyFeatureFlagService(db).list_flags(
            agency_id=agency_id,
            module_key=module_key,
            state=state,
            agency_view=True,
        ),
        "read_only": True,
        "payloads_hidden": True,
    }


@router.get("/reviews")
async def list_agency_feature_flag_reviews(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return {
        "items": await AgencyFeatureFlagService(db).list_reviews(agency_id=agency_id, agency_view=True),
        "read_only": True,
        "payloads_hidden": True,
    }
