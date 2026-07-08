from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import TripWorkspaceCreate, TripWorkspaceUpdate
from services.tenant_service import require_any_platform_role
from services.trip_workspace_service import PHASE_LABEL, TripWorkspaceService


router = APIRouter(prefix="/api/platform/trip-workspaces", tags=["platform-trip-workspaces"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_platform_trip_workspaces(
    agency_id: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    departure_country: str | None = Query(default=None),
    destination_country: str | None = Query(default=None),
    departure_date: date | None = Query(default=None),
    assigned_agent: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    operational_workspace_id: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await TripWorkspaceService(db).platform_response(
        agency_id=agency_id,
        status=status_filter,
        departure_country=departure_country,
        destination_country=destination_country,
        departure_date=departure_date,
        assigned_agent=assigned_agent,
        priority=priority,
        operational_workspace_id=operational_workspace_id,
        include_archived=include_archived,
    )


@router.get("/summary")
async def summarize_platform_trip_workspaces(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await TripWorkspaceService(db).platform_summary()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_platform_trip_workspace(
    payload: TripWorkspaceCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await TripWorkspaceService(db).create_trip(payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{trip_workspace_id}")
async def get_platform_trip_workspace(
    trip_workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = TripWorkspaceService(db)
    try:
        trip_workspace = await service.get_platform_trip(trip_workspace_id)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "trip_workspace": trip_workspace,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{trip_workspace_id}")
async def update_platform_trip_workspace(
    trip_workspace_id: str,
    payload: TripWorkspaceUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await TripWorkspaceService(db).update_trip(trip_workspace_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/{trip_workspace_id}")
async def delete_platform_trip_workspace(
    trip_workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await TripWorkspaceService(db).delete_trip(trip_workspace_id, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
