from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import PassengerServiceFeasibilityCreate, PassengerServiceFeasibilityUpdate
from services.passenger_service_feasibility_service import (
    PHASE_LABEL,
    PassengerServiceFeasibilityError,
    PassengerServiceFeasibilityService,
)
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/passenger-service-feasibility", tags=["platform-passenger-service-feasibility"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_platform_passenger_service_feasibilities(
    agency_id: str | None = Query(default=None),
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
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await PassengerServiceFeasibilityService(db).platform_response(
        agency_id=agency_id,
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
        include_archived=include_archived,
    )


@router.get("/summary")
async def summarize_platform_passenger_service_feasibilities(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await PassengerServiceFeasibilityService(db).platform_summary()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_platform_passenger_service_feasibility(
    payload: PassengerServiceFeasibilityCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await PassengerServiceFeasibilityService(db).create_feasibility(payload, user)
    except PassengerServiceFeasibilityError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{feasibility_id}")
async def get_platform_passenger_service_feasibility(
    feasibility_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = PassengerServiceFeasibilityService(db)
    try:
        feasibility = await service.get_platform_feasibility(feasibility_id)
    except PassengerServiceFeasibilityError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "passenger_service_feasibility": feasibility,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{feasibility_id}")
async def update_platform_passenger_service_feasibility(
    feasibility_id: str,
    payload: PassengerServiceFeasibilityUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await PassengerServiceFeasibilityService(db).update_feasibility(feasibility_id, payload, user)
    except PassengerServiceFeasibilityError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/{feasibility_id}")
async def archive_platform_passenger_service_feasibility(
    feasibility_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await PassengerServiceFeasibilityService(db).archive_feasibility(feasibility_id, user)
    except PassengerServiceFeasibilityError as exc:
        raise bad_request(str(exc)) from exc
