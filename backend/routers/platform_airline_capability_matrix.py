from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import AirlineCapabilityMatrixCreate, AirlineCapabilityMatrixUpdate
from services.airline_capability_matrix_service import (
    PHASE_LABEL,
    AirlineCapabilityMatrixError,
    AirlineCapabilityMatrixService,
)
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/airline-capability-matrix", tags=["platform-airline-capability-matrix"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_platform_airline_capability_matrix(
    agency_id: str | None = Query(default=None),
    airline: str | None = Query(default=None),
    service_domain: str | None = Query(default=None),
    service_family: str | None = Query(default=None),
    ssr_code: str | None = Query(default=None),
    rfic: str | None = Query(default=None),
    rfisc: str | None = Query(default=None),
    aircraft_family: str | None = Query(default=None),
    cabin: str | None = Query(default=None),
    airport: str | None = Query(default=None),
    route: str | None = Query(default=None),
    country: str | None = Query(default=None),
    season: str | None = Query(default=None),
    capability_status: str | None = Query(default=None),
    operational_risk: str | None = Query(default=None),
    confidence_level: str | None = Query(default=None),
    effective_date: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AirlineCapabilityMatrixService(db).platform_response(
        agency_id=agency_id,
        airline=airline,
        service_domain=service_domain,
        service_family=service_family,
        ssr_code=ssr_code,
        rfic=rfic,
        rfisc=rfisc,
        aircraft_family=aircraft_family,
        cabin=cabin,
        airport=airport,
        route=route,
        country=country,
        season=season,
        capability_status=capability_status,
        operational_risk=operational_risk,
        confidence_level=confidence_level,
        effective_date=effective_date,
        include_archived=include_archived,
    )


@router.get("/summary")
async def summarize_platform_airline_capability_matrix(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AirlineCapabilityMatrixService(db).platform_summary()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_capability_matrix_record(
    payload: AirlineCapabilityMatrixCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineCapabilityMatrixService(db).create_capability(payload, user)
    except AirlineCapabilityMatrixError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{capability_id}")
async def get_platform_airline_capability_matrix_record(
    capability_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = AirlineCapabilityMatrixService(db)
    try:
        capability = await service.get_platform_capability(capability_id)
    except AirlineCapabilityMatrixError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "airline_capability_matrix_record": capability,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{capability_id}")
async def update_platform_airline_capability_matrix_record(
    capability_id: str,
    payload: AirlineCapabilityMatrixUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineCapabilityMatrixService(db).update_capability(capability_id, payload, user)
    except AirlineCapabilityMatrixError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/{capability_id}")
async def archive_platform_airline_capability_matrix_record(
    capability_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineCapabilityMatrixService(db).archive_capability(capability_id, user)
    except AirlineCapabilityMatrixError as exc:
        raise bad_request(str(exc)) from exc
