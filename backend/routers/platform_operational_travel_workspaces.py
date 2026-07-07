from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import OperationalTravelWorkspaceCreate, OperationalTravelWorkspaceUpdate
from services.operational_travel_workspace_service import PHASE_LABEL, OperationalTravelWorkspaceService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/operational-travel-workspaces", tags=["platform-operational-travel-workspaces"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_platform_operational_travel_workspaces(
    agency_id: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    workspace_type: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    assigned_agent: str | None = Query(default=None),
    travel_date: date | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await OperationalTravelWorkspaceService(db).platform_response(
        agency_id=agency_id,
        status=status_filter,
        workspace_type=workspace_type,
        priority=priority,
        assigned_agent=assigned_agent,
        travel_date=travel_date,
        include_archived=include_archived,
    )


@router.get("/summary")
async def summarize_platform_operational_travel_workspaces(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await OperationalTravelWorkspaceService(db).platform_summary()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_platform_operational_travel_workspace(
    payload: OperationalTravelWorkspaceCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalTravelWorkspaceService(db).create_workspace(payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{workspace_id}")
async def get_platform_operational_travel_workspace(
    workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OperationalTravelWorkspaceService(db)
    try:
        workspace = await service.get_platform_workspace(workspace_id)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "workspace": workspace,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{workspace_id}")
async def update_platform_operational_travel_workspace(
    workspace_id: str,
    payload: OperationalTravelWorkspaceUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalTravelWorkspaceService(db).update_workspace(workspace_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/{workspace_id}")
async def delete_platform_operational_travel_workspace(
    workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalTravelWorkspaceService(db).delete_workspace(workspace_id, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
