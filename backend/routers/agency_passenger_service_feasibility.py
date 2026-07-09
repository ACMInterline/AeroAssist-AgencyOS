from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.passenger_service_feasibility_service import (
    PHASE_LABEL,
    PassengerServiceFeasibilityError,
    PassengerServiceFeasibilityService,
)
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/passenger-service-feasibility", tags=["agency-passenger-service-feasibility"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


@router.get("")
async def list_agency_passenger_service_feasibilities(
    agency_id: str,
    feasibility_status: str | None = Query(default=None),
    feasibility_type: str | None = Query(default=None),
    airline: str | None = Query(default=None),
    feasibility_outcome: str | None = Query(default=None),
    confidence_level: str | None = Query(default=None),
    operational_risk: str | None = Query(default=None),
    passenger_need_category: str | None = Query(default=None),
    ssr_code: str | None = Query(default=None),
    travel_date: str | None = Query(default=None),
    cabin: str | None = Query(default=None),
    destination: str | None = Query(default=None),
    recommendation_ready: bool | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await PassengerServiceFeasibilityService(db).agency_response(
        agency_id,
        feasibility_status=feasibility_status,
        feasibility_type=feasibility_type,
        airline=airline,
        feasibility_outcome=feasibility_outcome,
        confidence_level=confidence_level,
        operational_risk=operational_risk,
        passenger_need_category=passenger_need_category,
        ssr_code=ssr_code,
        travel_date=travel_date,
        cabin=cabin,
        destination=destination,
        recommendation_ready=recommendation_ready,
    )


@router.get("/summary")
async def summarize_agency_passenger_service_feasibilities(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await PassengerServiceFeasibilityService(db).agency_summary(agency_id)


@router.get("/{feasibility_id}")
async def get_agency_passenger_service_feasibility(
    agency_id: str,
    feasibility_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = PassengerServiceFeasibilityService(db)
    try:
        feasibility = await service.get_agency_feasibility(agency_id, feasibility_id)
    except PassengerServiceFeasibilityError:
        raise not_found("Passenger service feasibility metadata not found.")
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "passenger_service_feasibility": feasibility,
        "read_only": True,
        "metadata_only": True,
        **service.safety_flags(),
    }
