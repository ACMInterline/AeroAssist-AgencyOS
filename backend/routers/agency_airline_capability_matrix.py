from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.airline_capability_matrix_service import (
    PHASE_LABEL,
    AirlineCapabilityMatrixError,
    AirlineCapabilityMatrixService,
)
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/airline-capability-matrix", tags=["agency-airline-capability-matrix"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


@router.get("")
async def list_agency_airline_capability_matrix(
    agency_id: str,
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
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await AirlineCapabilityMatrixService(db).agency_response(
        agency_id,
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
    )


@router.get("/summary")
async def summarize_agency_airline_capability_matrix(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await AirlineCapabilityMatrixService(db).agency_summary(agency_id)


@router.get("/{capability_id}")
async def get_agency_airline_capability_matrix_record(
    agency_id: str,
    capability_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AirlineCapabilityMatrixService(db)
    try:
        capability = await service.get_agency_capability(agency_id, capability_id)
    except AirlineCapabilityMatrixError:
        raise not_found("Airline capability matrix metadata not found.")
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "airline_capability_matrix_record": capability,
        "read_only": True,
        "metadata_only": True,
        **service.safety_flags(),
    }
