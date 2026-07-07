from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import TravelRequestWorkspaceCreate, TravelRequestWorkspaceUpdate
from services.tenant_service import require_any_platform_role
from services.travel_request_workspace_service import PHASE_LABEL, TravelRequestWorkspaceService


router = APIRouter(prefix="/api/platform/travel-request-workspaces", tags=["platform-travel-request-workspaces"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_platform_travel_request_workspaces(
    agency_id: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    request_type: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    assigned_agent: str | None = Query(default=None),
    departure_date: date | None = Query(default=None),
    operational_workspace_id: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await TravelRequestWorkspaceService(db).platform_response(
        agency_id=agency_id,
        status=status_filter,
        request_type=request_type,
        priority=priority,
        assigned_agent=assigned_agent,
        departure_date=departure_date,
        operational_workspace_id=operational_workspace_id,
        include_archived=include_archived,
    )


@router.get("/summary")
async def summarize_platform_travel_request_workspaces(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await TravelRequestWorkspaceService(db).platform_summary()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_platform_travel_request_workspace(
    payload: TravelRequestWorkspaceCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await TravelRequestWorkspaceService(db).create_request(payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{request_workspace_id}")
async def get_platform_travel_request_workspace(
    request_workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = TravelRequestWorkspaceService(db)
    try:
        request_workspace = await service.get_platform_request(request_workspace_id)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "request_workspace": request_workspace,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{request_workspace_id}")
async def update_platform_travel_request_workspace(
    request_workspace_id: str,
    payload: TravelRequestWorkspaceUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await TravelRequestWorkspaceService(db).update_request(request_workspace_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/{request_workspace_id}")
async def delete_platform_travel_request_workspace(
    request_workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await TravelRequestWorkspaceService(db).delete_request(request_workspace_id, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
