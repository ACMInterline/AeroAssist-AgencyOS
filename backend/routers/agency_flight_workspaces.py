from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.flight_workspace_service import PHASE_LABEL, FlightWorkspaceService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/flight-workspaces", tags=["agency-flight-workspaces"])

AGENCY_READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_agency_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, AGENCY_READ_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_agency_flight_workspaces(
    agency_id: str,
    status_filter: str | None = Query(default=None, alias="status"),
    airline: str | None = Query(default=None),
    departure_airport: str | None = Query(default=None),
    arrival_airport: str | None = Query(default=None),
    departure_date: date | None = Query(default=None),
    cabin: str | None = Query(default=None),
    booking_class: str | None = Query(default=None),
    operational_workspace_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return await FlightWorkspaceService(db).agency_response(
        agency_id,
        status=status_filter,
        airline=airline,
        departure_airport=departure_airport,
        arrival_airport=arrival_airport,
        departure_date=departure_date,
        cabin=cabin,
        booking_class=booking_class,
        operational_workspace_id=operational_workspace_id,
    )


@router.get("/summary")
async def summarize_agency_flight_workspaces(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return await FlightWorkspaceService(db).agency_summary(agency_id)


@router.get("/{flight_workspace_id}")
async def get_agency_flight_workspace(
    agency_id: str,
    flight_workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    service = FlightWorkspaceService(db)
    try:
        flight_workspace = await service.get_agency_flight(agency_id, flight_workspace_id)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "flight_workspace": flight_workspace,
        "read_only": True,
        "metadata_only": True,
        **service.safety_flags(),
    }
