from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.airline_recommendation_engine_service import (
    AirlineRecommendationError,
    AirlineRecommendationService,
    PHASE_LABEL,
)
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/airline-recommendations", tags=["agency-airline-recommendations"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


@router.get("")
async def list_agency_airline_recommendations(
    agency_id: str,
    recommendation_status: str | None = Query(default=None),
    airline: str | None = Query(default=None),
    recommendation_level: str | None = Query(default=None),
    operational_score: float | None = Query(default=None),
    risk: float | None = Query(default=None),
    passenger_need_category: str | None = Query(default=None),
    cabin: str | None = Query(default=None),
    destination: str | None = Query(default=None),
    travel_date: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await AirlineRecommendationService(db).agency_response(
        agency_id,
        recommendation_status=recommendation_status,
        airline=airline,
        recommendation_level=recommendation_level,
        operational_score=operational_score,
        risk=risk,
        passenger_need_category=passenger_need_category,
        cabin=cabin,
        destination=destination,
        travel_date=travel_date,
    )


@router.get("/summary")
async def summarize_agency_airline_recommendations(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await AirlineRecommendationService(db).agency_summary(agency_id)


@router.get("/{recommendation_id}")
async def get_agency_airline_recommendation(
    agency_id: str,
    recommendation_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AirlineRecommendationService(db)
    try:
        recommendation = await service.get_agency_recommendation(agency_id, recommendation_id)
    except AirlineRecommendationError:
        raise not_found("Airline recommendation metadata not found.")
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "airline_recommendation": recommendation,
        "read_only": True,
        "metadata_only": True,
        **service.safety_flags(),
    }
