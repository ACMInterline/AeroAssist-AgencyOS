from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    BookingCreateFromReadinessRequest,
    BookingRecordUpdate,
    BookingWorkspaceStatusUpdate,
)
from services.booking_workspace_service import BookingWorkspaceError, BookingWorkspaceService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}", tags=["agency-booking-workspaces"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin", "agency_agent"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


async def require_write(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin"}:
        await require_any_agency_role(db, agency_id, user, WRITE_ROLES)


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def bad_request(exc: BookingWorkspaceError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/booking-workspaces")
async def list_booking_workspaces(
    agency_id: str,
    status_filter: str | None = Query(default=None, alias="status"),
    provider_target: str | None = None,
    trip_id: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = BookingWorkspaceService(db)
    return await service.list_booking_workspaces(
        agency_id,
        status_filter=status_filter,
        provider_target=provider_target,
        trip_id=trip_id,
    )


@router.post("/booking-workspaces/from-readiness", status_code=status.HTTP_201_CREATED)
async def create_booking_workspace_from_readiness(
    agency_id: str,
    payload: BookingCreateFromReadinessRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = BookingWorkspaceService(db)
    try:
        result = await service.create_booking_workspace_from_readiness(agency_id, payload, user)
    except BookingWorkspaceError as exc:
        raise bad_request(exc)
    if result is None:
        raise not_found("Booking readiness package not found.")
    return result


@router.get("/booking-workspaces/{booking_workspace_id}")
async def get_booking_workspace(
    agency_id: str,
    booking_workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = BookingWorkspaceService(db)
    result = await service.get_booking_workspace(agency_id, booking_workspace_id)
    if not result:
        raise not_found("Booking workspace not found.")
    return result


@router.post("/booking-workspaces/{booking_workspace_id}/status")
async def update_booking_workspace_status(
    agency_id: str,
    booking_workspace_id: str,
    payload: BookingWorkspaceStatusUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = BookingWorkspaceService(db)
    result = await service.update_booking_workspace_status(
        agency_id,
        booking_workspace_id,
        payload.status,
        user,
        payload.internal_notes,
    )
    if result is None:
        raise not_found("Booking workspace not found.")
    return result


@router.post("/booking-workspaces/{booking_workspace_id}/rebuild-record")
async def rebuild_booking_record(
    agency_id: str,
    booking_workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = BookingWorkspaceService(db)
    try:
        result = await service.rebuild_booking_record_from_readiness(agency_id, booking_workspace_id, user)
    except BookingWorkspaceError as exc:
        raise bad_request(exc)
    if result is None:
        raise not_found("Booking workspace not found.")
    return result


@router.post("/booking-workspaces/{booking_workspace_id}/cancel")
async def cancel_booking_workspace(
    agency_id: str,
    booking_workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = BookingWorkspaceService(db)
    result = await service.cancel_booking_workspace(agency_id, booking_workspace_id, user)
    if result is None:
        raise not_found("Booking workspace not found.")
    return result


@router.put("/booking-records/{booking_record_id}")
async def update_booking_record(
    agency_id: str,
    booking_record_id: str,
    payload: BookingRecordUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = BookingWorkspaceService(db)
    result = await service.update_booking_record(agency_id, booking_record_id, payload, user)
    if result is None:
        raise not_found("Booking record not found.")
    return result
