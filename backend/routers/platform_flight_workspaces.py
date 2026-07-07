from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import FlightWorkspaceCreate, FlightWorkspaceUpdate
from services.flight_workspace_service import PHASE_LABEL, FlightWorkspaceService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/flight-workspaces", tags=["platform-flight-workspaces"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_platform_flight_workspaces(
    agency_id: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    airline: str | None = Query(default=None),
    departure_airport: str | None = Query(default=None),
    arrival_airport: str | None = Query(default=None),
    departure_date: date | None = Query(default=None),
    cabin: str | None = Query(default=None),
    booking_class: str | None = Query(default=None),
    operational_workspace_id: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await FlightWorkspaceService(db).platform_response(
        agency_id=agency_id,
        status=status_filter,
        airline=airline,
        departure_airport=departure_airport,
        arrival_airport=arrival_airport,
        departure_date=departure_date,
        cabin=cabin,
        booking_class=booking_class,
        operational_workspace_id=operational_workspace_id,
        include_archived=include_archived,
    )


@router.get("/summary")
async def summarize_platform_flight_workspaces(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await FlightWorkspaceService(db).platform_summary()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_platform_flight_workspace(
    payload: FlightWorkspaceCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await FlightWorkspaceService(db).create_flight(payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{flight_workspace_id}")
async def get_platform_flight_workspace(
    flight_workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = FlightWorkspaceService(db)
    try:
        flight_workspace = await service.get_platform_flight(flight_workspace_id)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "flight_workspace": flight_workspace,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{flight_workspace_id}")
async def update_platform_flight_workspace(
    flight_workspace_id: str,
    payload: FlightWorkspaceUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await FlightWorkspaceService(db).update_flight(flight_workspace_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/{flight_workspace_id}")
async def delete_platform_flight_workspace(
    flight_workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await FlightWorkspaceService(db).delete_flight(flight_workspace_id, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
