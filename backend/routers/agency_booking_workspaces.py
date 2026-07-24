from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    BookingCreateFromReadinessRequest,
    BookingRecordUpdate,
    BookingWorkspaceStatusUpdate,
    ManualBookingWorkspaceCreate,
)
from services.authorization_service import (
    project_authorized_commercial_fields,
    require_permission,
)
from services.booking_workspace_service import PHASE_LABEL, BookingWorkspaceError, BookingWorkspaceService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}", tags=["agency-booking-workspaces"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin", "agency_agent"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    await require_any_agency_role(db, agency_id, user, READ_ROLES)
    require_permission(user, "view_bookings")


async def require_write(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    await require_any_agency_role(db, agency_id, user, WRITE_ROLES)
    require_permission(user, "edit_bookings")


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def bad_request(exc: BookingWorkspaceError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


def lifecycle_conflict(exc: BookingWorkspaceError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.get("/booking-workspaces")
async def list_booking_workspaces(
    agency_id: str,
    status_filter: str | None = Query(default=None, alias="status"),
    provider_target: str | None = None,
    trip_id: str | None = None,
    booking_owner: str | None = Query(default=None),
    airline: str | None = Query(default=None),
    supplier: str | None = Query(default=None),
    booking_date: date | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = BookingWorkspaceService(db)
    if provider_target or trip_id:
        return project_authorized_commercial_fields(
            await service.list_booking_workspaces(
                agency_id,
                status_filter=status_filter,
                provider_target=provider_target,
                trip_id=trip_id,
            ),
            user,
        )
    return project_authorized_commercial_fields(
        await service.agency_metadata_response(
            agency_id,
            booking_status=status_filter,
            booking_owner=booking_owner,
            airline=airline,
            supplier=supplier,
            booking_date=booking_date,
        ),
        user,
    )


@router.get("/booking-workspaces/summary")
async def summarize_booking_workspaces(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return project_authorized_commercial_fields(
        await BookingWorkspaceService(db).agency_metadata_summary(agency_id), user
    )


@router.get("/booking-readiness-packages")
async def list_booking_readiness_packages(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = BookingWorkspaceService(db)
    return project_authorized_commercial_fields(
        await service.list_eligible_booking_readiness_packages(agency_id), user
    )


@router.post("/booking-workspaces/from-readiness", status_code=status.HTTP_201_CREATED)
async def create_booking_workspace_from_readiness(
    agency_id: str,
    payload: BookingCreateFromReadinessRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    """Compatibility-only route; the primary agency flow uses OfferBookingHandoff."""
    await require_write(db, agency_id, user)
    service = BookingWorkspaceService(db)
    try:
        result = await service.create_booking_workspace_from_readiness(agency_id, payload, user)
    except BookingWorkspaceError as exc:
        raise bad_request(exc)
    if result is None:
        raise not_found("Booking readiness package not found.")
    return project_authorized_commercial_fields(
        {
            **result,
            "compatibility_only": True,
            "canonical_route": "/api/agencies/{agency_id}/booking-handoffs/{handoff_id}/create-booking-workspace",
        },
        user,
    )


@router.post("/booking-workspaces/manual", status_code=status.HTTP_201_CREATED)
async def create_manual_booking_workspace(
    agency_id: str,
    payload: ManualBookingWorkspaceCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = BookingWorkspaceService(db)
    try:
        return project_authorized_commercial_fields(
            await service.create_manual_booking_workspace(
                agency_id, payload, user
            ),
            user,
        )
    except BookingWorkspaceError as exc:
        raise bad_request(exc)


@router.get("/booking-workspaces/{booking_workspace_id}")
async def get_booking_workspace(
    agency_id: str,
    booking_workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = BookingWorkspaceService(db)
    workspace = await service.get_booking_workspace(agency_id, booking_workspace_id)
    if not workspace:
        raise not_found("Booking workspace not found.")
    return project_authorized_commercial_fields(
        {"phase": PHASE_LABEL, "agency_id": agency_id, **workspace},
        user,
    )


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
    try:
        result = await service.update_booking_workspace_status(
            agency_id,
            booking_workspace_id,
            payload.status,
            user,
            payload.internal_notes,
        )
    except BookingWorkspaceError as exc:
        raise lifecycle_conflict(exc) from exc
    if result is None:
        raise not_found("Booking workspace not found.")
    return project_authorized_commercial_fields(result, user)


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
    return project_authorized_commercial_fields(result, user)


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
    return project_authorized_commercial_fields(result, user)


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
    try:
        result = await service.update_booking_record(
            agency_id, booking_record_id, payload, user
        )
    except BookingWorkspaceError as exc:
        raise lifecycle_conflict(exc) from exc
    if result is None:
        raise not_found("Booking record not found.")
    return project_authorized_commercial_fields(result, user)
