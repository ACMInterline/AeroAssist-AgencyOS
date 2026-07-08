from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import BookingWorkspaceMetadataCreate, BookingWorkspaceMetadataUpdate
from services.booking_workspace_service import PHASE_LABEL, BookingWorkspaceError, BookingWorkspaceService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/booking-workspaces", tags=["platform-booking-workspaces"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_platform_booking_workspaces(
    agency_id: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    booking_owner: str | None = Query(default=None),
    airline: str | None = Query(default=None),
    supplier: str | None = Query(default=None),
    booking_date: date | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await BookingWorkspaceService(db).platform_metadata_response(
        agency_id=agency_id,
        booking_status=status_filter,
        booking_owner=booking_owner,
        airline=airline,
        supplier=supplier,
        booking_date=booking_date,
        include_archived=include_archived,
    )


@router.get("/summary")
async def summarize_platform_booking_workspaces(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await BookingWorkspaceService(db).platform_metadata_summary()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_platform_booking_workspace(
    payload: BookingWorkspaceMetadataCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await BookingWorkspaceService(db).create_metadata_booking_workspace(payload, user)
    except BookingWorkspaceError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{booking_workspace_id}")
async def get_platform_booking_workspace(
    booking_workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = BookingWorkspaceService(db)
    try:
        booking_workspace = await service.get_platform_metadata_workspace(booking_workspace_id)
    except BookingWorkspaceError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "booking_workspace": booking_workspace,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{booking_workspace_id}")
async def update_platform_booking_workspace(
    booking_workspace_id: str,
    payload: BookingWorkspaceMetadataUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await BookingWorkspaceService(db).update_metadata_booking_workspace(booking_workspace_id, payload, user)
    except BookingWorkspaceError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/{booking_workspace_id}")
async def delete_platform_booking_workspace(
    booking_workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await BookingWorkspaceService(db).delete_metadata_booking_workspace(booking_workspace_id, user)
    except BookingWorkspaceError as exc:
        raise bad_request(str(exc)) from exc
