from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.airline_intelligence_scale_readiness_service import (
    PHASE_LABEL,
    AirlineIntelligenceScaleReadinessError,
    AirlineIntelligenceScaleReadinessService,
)
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(
    prefix="/api/agencies/{agency_id}/airline-intelligence-readiness",
    tags=["agency-airline-intelligence-readiness"],
)

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


def bad_request(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("")
async def get_agency_airline_intelligence_readiness(
    agency_id: str,
    airline_code: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await AirlineIntelligenceScaleReadinessService(db).agency_dashboard(agency_id, airline_code=airline_code)


@router.get("/summary")
async def summarize_agency_airline_intelligence_readiness(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AirlineIntelligenceScaleReadinessService(db)
    response = await service.agency_dashboard(agency_id)
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "summary": response["summary"], "read_only": True, **service.safety_flags()}


@router.get("/released")
async def list_agency_released_airline_intelligence(
    agency_id: str,
    airline_code: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AirlineIntelligenceScaleReadinessService(db)
    response = await service.agency_dashboard(agency_id, airline_code=airline_code)
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "items": response["released_coverage"], "count": len(response["released_coverage"]), "read_only": True, **service.safety_flags()}


@router.get("/released/{candidate_id}")
async def get_agency_released_airline_intelligence(
    agency_id: str,
    candidate_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    try:
        return await AirlineIntelligenceScaleReadinessService(db).get_candidate(candidate_id, agency_id=agency_id)
    except AirlineIntelligenceScaleReadinessError as exc:
        raise bad_request(exc) from exc
