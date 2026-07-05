from __future__ import annotations

from fastapi import APIRouter, Depends

from auth import get_current_user
from database import Database, get_database
from services.capability_catalog_service import CapabilityCatalogService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/capabilities", tags=["agency-capabilities"])

AGENCY_READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_agency_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, AGENCY_READ_ROLES)


@router.get("")
async def list_agency_capabilities(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return await CapabilityCatalogService(db).agency_capabilities_response(agency_id)


@router.get("/available")
async def list_agency_available_capabilities(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return await CapabilityCatalogService(db).agency_capabilities_response(agency_id, availability="available")


@router.get("/unavailable")
async def list_agency_unavailable_capabilities(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return await CapabilityCatalogService(db).agency_capabilities_response(agency_id, availability="unavailable")
