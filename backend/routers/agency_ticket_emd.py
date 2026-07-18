from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    EmdCreateFromBookingServiceRequest,
    EmdRecordUpdate,
    ManualEmdCreate,
    ManualTicketCreate,
    TicketCreateFromBookingRequest,
    TicketRecordUpdate,
    TicketResultReconciliationRequest,
)
from services.tenant_service import assert_agency_access, require_any_agency_role
from services.ticket_emd_service import TicketEmdError, TicketEmdService


router = APIRouter(prefix="/api/agencies/{agency_id}", tags=["agency-ticket-emd"])

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


def bad_request(exc: TicketEmdError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/tickets")
async def list_tickets(
    agency_id: str,
    trip_id: str | None = None,
    booking_workspace_id: str | None = None,
    booking_record_id: str | None = None,
    passenger_id: str | None = None,
    issue_status: str | None = None,
    ticket_number: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = TicketEmdService(db)
    return await service.list_tickets(
        agency_id,
        {
            "trip_id": trip_id,
            "booking_workspace_id": booking_workspace_id,
            "booking_record_id": booking_record_id,
            "passenger_id": passenger_id,
            "issue_status": issue_status,
            "ticket_number": ticket_number,
        },
    )


@router.post("/tickets/from-booking-record", status_code=status.HTTP_201_CREATED)
async def create_ticket_from_booking_record(
    agency_id: str,
    payload: TicketCreateFromBookingRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = TicketEmdService(db)
    try:
        result = await service.create_ticket_from_booking_record(agency_id, payload, user)
    except TicketEmdError as exc:
        raise bad_request(exc)
    if result is None:
        raise not_found("Booking record not found.")
    return result


@router.post("/tickets/manual", status_code=status.HTTP_201_CREATED)
async def create_manual_ticket(
    agency_id: str,
    payload: ManualTicketCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = TicketEmdService(db)
    try:
        return await service.create_manual_ticket(agency_id, payload, user)
    except TicketEmdError as exc:
        raise bad_request(exc)


@router.get("/tickets/{ticket_record_id}")
async def get_ticket_detail(
    agency_id: str,
    ticket_record_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = TicketEmdService(db)
    result = await service.get_ticket_detail(agency_id, ticket_record_id)
    if not result:
        raise not_found("Ticket record not found.")
    return result


@router.put("/tickets/{ticket_record_id}")
async def update_ticket_record(
    agency_id: str,
    ticket_record_id: str,
    payload: TicketRecordUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = TicketEmdService(db)
    result = await service.update_ticket_record(agency_id, ticket_record_id, payload, user)
    if result is None:
        raise not_found("Ticket record not found.")
    return result


@router.post("/tickets/{ticket_record_id}/reconcile")
async def reconcile_external_ticket_result(
    agency_id: str,
    ticket_record_id: str,
    payload: TicketResultReconciliationRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        result = await TicketEmdService(db).reconcile_ticket_result(agency_id, ticket_record_id, payload, user)
    except TicketEmdError as exc:
        raise bad_request(exc)
    if result is None:
        raise not_found("Ticket record not found.")
    return result


@router.get("/emds")
async def list_emds(
    agency_id: str,
    trip_id: str | None = None,
    booking_workspace_id: str | None = None,
    booking_record_id: str | None = None,
    ticket_record_id: str | None = None,
    passenger_id: str | None = None,
    service_key: str | None = None,
    issue_status: str | None = None,
    emd_number: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = TicketEmdService(db)
    return await service.list_emds(
        agency_id,
        {
            "trip_id": trip_id,
            "booking_workspace_id": booking_workspace_id,
            "booking_record_id": booking_record_id,
            "ticket_record_id": ticket_record_id,
            "passenger_id": passenger_id,
            "service_key": service_key,
            "issue_status": issue_status,
            "emd_number": emd_number,
        },
    )


@router.post("/emds/from-booking-service", status_code=status.HTTP_201_CREATED)
async def create_emd_from_booking_service(
    agency_id: str,
    payload: EmdCreateFromBookingServiceRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = TicketEmdService(db)
    try:
        result = await service.create_emd_from_booking_service(agency_id, payload, user)
    except TicketEmdError as exc:
        raise bad_request(exc)
    if result is None:
        raise not_found("Booking record not found.")
    return result


@router.post("/emds/manual", status_code=status.HTTP_201_CREATED)
async def create_manual_emd(
    agency_id: str,
    payload: ManualEmdCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = TicketEmdService(db)
    try:
        return await service.create_manual_emd(agency_id, payload, user)
    except TicketEmdError as exc:
        raise bad_request(exc)


@router.get("/emds/{emd_record_id}")
async def get_emd_detail(
    agency_id: str,
    emd_record_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = TicketEmdService(db)
    result = await service.get_emd_detail(agency_id, emd_record_id)
    if not result:
        raise not_found("EMD record not found.")
    return result


@router.put("/emds/{emd_record_id}")
async def update_emd_record(
    agency_id: str,
    emd_record_id: str,
    payload: EmdRecordUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = TicketEmdService(db)
    result = await service.update_emd_record(agency_id, emd_record_id, payload, user)
    if result is None:
        raise not_found("EMD record not found.")
    return result


@router.get("/booking-records/{booking_record_id}/ticket-emd-readiness")
async def ticket_emd_readiness(
    agency_id: str,
    booking_record_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = TicketEmdService(db)
    result = await service.build_ticket_emd_readiness_summary(agency_id, booking_record_id)
    if result is None:
        raise not_found("Booking record not found.")
    return result
