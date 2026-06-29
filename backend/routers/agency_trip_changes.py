from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user
from database import Database, get_database
from models import (
    EmdExchangeOperationCreate,
    ManualBookingWorkspaceCreate,
    ManualEmdCreate,
    ManualTicketCreate,
    TicketExchangeOperationCreate,
    TripChangeOperationCreate,
)
from services.tenant_service import assert_agency_access, require_any_agency_role
from services.trip_change_exchange_service import TripChangeExchangeError, TripChangeExchangeService


router = APIRouter(prefix="/api/agencies/{agency_id}", tags=["agency-trip-changes"])

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


def bad_request(exc: TripChangeExchangeError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/trips/{trip_id}/change-operations")
async def list_trip_change_operations(
    agency_id: str,
    trip_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = TripChangeExchangeService(db)
    return await service.list_trip_change_operations(agency_id, trip_id)


@router.post("/trips/{trip_id}/change-operations", status_code=status.HTTP_201_CREATED)
async def create_trip_change_operation(
    agency_id: str,
    trip_id: str,
    payload: TripChangeOperationCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = TripChangeExchangeService(db)
    result = await service.create_trip_change_operation(agency_id, trip_id, payload, user)
    if result is None:
        raise not_found("Trip dossier not found.")
    return result


@router.post("/trip-change-operations/{operation_id}/create-change-booking", status_code=status.HTTP_201_CREATED)
async def create_change_booking(
    agency_id: str,
    operation_id: str,
    payload: ManualBookingWorkspaceCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = TripChangeExchangeService(db)
    result = await service.create_change_booking_from_operation(agency_id, operation_id, payload, user)
    if result is None:
        raise not_found("Trip change operation not found.")
    return result


@router.post("/ticket-exchange-operations", status_code=status.HTTP_201_CREATED)
async def create_ticket_exchange_operation(
    agency_id: str,
    payload: TicketExchangeOperationCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = TripChangeExchangeService(db)
    result = await service.create_ticket_exchange_operation(agency_id, payload, user)
    if result is None:
        raise not_found("Original ticket record not found.")
    return result


@router.post("/ticket-exchange-operations/{operation_id}/mirror-new-ticket", status_code=status.HTTP_201_CREATED)
async def mirror_new_ticket_for_exchange(
    agency_id: str,
    operation_id: str,
    payload: ManualTicketCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = TripChangeExchangeService(db)
    result = await service.mirror_new_ticket_for_exchange(agency_id, operation_id, payload, user)
    if result is None:
        raise not_found("Ticket exchange operation not found.")
    return result


@router.post("/emd-exchange-operations", status_code=status.HTTP_201_CREATED)
async def create_emd_exchange_operation(
    agency_id: str,
    payload: EmdExchangeOperationCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = TripChangeExchangeService(db)
    result = await service.create_emd_exchange_operation(agency_id, payload, user)
    if result is None:
        raise not_found("Original EMD record not found.")
    return result


@router.post("/emd-exchange-operations/{operation_id}/mirror-new-emd", status_code=status.HTTP_201_CREATED)
async def mirror_new_emd_for_exchange(
    agency_id: str,
    operation_id: str,
    payload: ManualEmdCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = TripChangeExchangeService(db)
    result = await service.mirror_new_emd_for_exchange(agency_id, operation_id, payload, user)
    if result is None:
        raise not_found("EMD exchange operation not found.")
    return result
