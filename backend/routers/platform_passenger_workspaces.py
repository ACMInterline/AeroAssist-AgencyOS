from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import PassengerWorkspaceCreate, PassengerWorkspaceUpdate
from services.passenger_workspace_service import PHASE_LABEL, PassengerWorkspaceService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/passenger-workspaces", tags=["platform-passenger-workspaces"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_platform_passenger_workspaces(
    agency_id: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    nationality: str | None = Query(default=None),
    citizenship: str | None = Query(default=None),
    assistance_profile: str | None = Query(default=None),
    travel_date: date | None = Query(default=None),
    operational_workspace_id: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await PassengerWorkspaceService(db).platform_response(
        agency_id=agency_id,
        status=status_filter,
        nationality=nationality,
        citizenship=citizenship,
        assistance_profile=assistance_profile,
        travel_date=travel_date,
        operational_workspace_id=operational_workspace_id,
        include_archived=include_archived,
    )


@router.get("/summary")
async def summarize_platform_passenger_workspaces(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await PassengerWorkspaceService(db).platform_summary()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_platform_passenger_workspace(
    payload: PassengerWorkspaceCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await PassengerWorkspaceService(db).create_passenger(payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{passenger_workspace_id}")
async def get_platform_passenger_workspace(
    passenger_workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = PassengerWorkspaceService(db)
    try:
        passenger_workspace = await service.get_platform_passenger(passenger_workspace_id)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "passenger_workspace": passenger_workspace,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{passenger_workspace_id}")
async def update_platform_passenger_workspace(
    passenger_workspace_id: str,
    payload: PassengerWorkspaceUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await PassengerWorkspaceService(db).update_passenger(passenger_workspace_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/{passenger_workspace_id}")
async def delete_platform_passenger_workspace(
    passenger_workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await PassengerWorkspaceService(db).delete_passenger(passenger_workspace_id, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
