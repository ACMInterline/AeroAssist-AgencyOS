from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import AirlineRecommendationCreate, AirlineRecommendationUpdate
from services.airline_recommendation_engine_service import (
    AirlineRecommendationError,
    AirlineRecommendationService,
    PHASE_LABEL,
)
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/airline-recommendations", tags=["platform-airline-recommendations"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_platform_airline_recommendations(
    agency_id: str | None = Query(default=None),
    recommendation_status: str | None = Query(default=None),
    airline: str | None = Query(default=None),
    recommendation_level: str | None = Query(default=None),
    operational_score: float | None = Query(default=None),
    risk: float | None = Query(default=None),
    passenger_need_category: str | None = Query(default=None),
    cabin: str | None = Query(default=None),
    destination: str | None = Query(default=None),
    travel_date: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AirlineRecommendationService(db).platform_response(
        agency_id=agency_id,
        recommendation_status=recommendation_status,
        airline=airline,
        recommendation_level=recommendation_level,
        operational_score=operational_score,
        risk=risk,
        passenger_need_category=passenger_need_category,
        cabin=cabin,
        destination=destination,
        travel_date=travel_date,
        include_archived=include_archived,
    )


@router.get("/summary")
async def summarize_platform_airline_recommendations(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AirlineRecommendationService(db).platform_summary()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_recommendation(
    payload: AirlineRecommendationCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineRecommendationService(db).create_recommendation(payload, user)
    except AirlineRecommendationError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{recommendation_id}")
async def get_platform_airline_recommendation(
    recommendation_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = AirlineRecommendationService(db)
    try:
        recommendation = await service.get_platform_recommendation(recommendation_id)
    except AirlineRecommendationError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "airline_recommendation": recommendation,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{recommendation_id}")
async def update_platform_airline_recommendation(
    recommendation_id: str,
    payload: AirlineRecommendationUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineRecommendationService(db).update_recommendation(recommendation_id, payload, user)
    except AirlineRecommendationError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/{recommendation_id}")
async def archive_platform_airline_recommendation(
    recommendation_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineRecommendationService(db).archive_recommendation(recommendation_id, user)
    except AirlineRecommendationError as exc:
        raise bad_request(str(exc)) from exc
