from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.airline_master_profile_intelligence_service import (
    PHASE_LABEL,
    AirlineMasterProfileError,
    AirlineMasterProfileIntelligenceService,
)
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/airline-master-profiles", tags=["agency-airline-master-profiles"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


@router.get("")
async def list_agency_airline_profiles(
    agency_id: str,
    search: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    response = await AirlineMasterProfileIntelligenceService(db).response(search=search, agency_safe=True)
    return {**response, "agency_id": agency_id}


@router.get("/{airline_id}")
async def get_agency_airline_profile(
    agency_id: str,
    airline_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AirlineMasterProfileIntelligenceService(db)
    try:
        item = await service.get_profile(airline_id, agency_safe=True)
    except AirlineMasterProfileError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "item": item, **service.safety_flags()}


@router.get("/{airline_id}/client-safe")
async def get_client_safe_airline_identity(
    agency_id: str,
    airline_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AirlineMasterProfileIntelligenceService(db)
    try:
        item = await service.get_profile(airline_id, agency_safe=True)
    except AirlineMasterProfileError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "identity": item["client_safe_identity"], **service.safety_flags()}
