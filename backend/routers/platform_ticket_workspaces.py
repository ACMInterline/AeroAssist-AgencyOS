from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import TicketWorkspaceCreate, TicketWorkspaceUpdate
from services.tenant_service import require_any_platform_role
from services.ticket_workspace_service import PHASE_LABEL, TicketWorkspaceError, TicketWorkspaceService


router = APIRouter(prefix="/api/platform/ticket-workspaces", tags=["platform-ticket-workspaces"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_platform_ticket_workspaces(
    agency_id: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    document_status: str | None = Query(default=None),
    validating_carrier: str | None = Query(default=None),
    issue_date: date | None = Query(default=None),
    passenger: str | None = Query(default=None),
    booking_reference: str | None = Query(default=None),
    currency: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await TicketWorkspaceService(db).platform_response(
        agency_id=agency_id,
        ticket_status=status_filter,
        ticket_document_status=document_status,
        validating_carrier=validating_carrier,
        issue_date=issue_date,
        passenger=passenger,
        booking_reference=booking_reference,
        currency=currency,
        include_archived=include_archived,
    )


@router.get("/summary")
async def summarize_platform_ticket_workspaces(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await TicketWorkspaceService(db).platform_summary()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_platform_ticket_workspace(
    payload: TicketWorkspaceCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await TicketWorkspaceService(db).create_ticket(payload, user)
    except TicketWorkspaceError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{ticket_workspace_id}")
async def get_platform_ticket_workspace(
    ticket_workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = TicketWorkspaceService(db)
    try:
        ticket_workspace = await service.get_platform_ticket(ticket_workspace_id)
    except TicketWorkspaceError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "ticket_workspace": ticket_workspace,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{ticket_workspace_id}")
async def update_platform_ticket_workspace(
    ticket_workspace_id: str,
    payload: TicketWorkspaceUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await TicketWorkspaceService(db).update_ticket(ticket_workspace_id, payload, user)
    except TicketWorkspaceError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/{ticket_workspace_id}")
async def delete_platform_ticket_workspace(
    ticket_workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await TicketWorkspaceService(db).delete_ticket(ticket_workspace_id, user)
    except TicketWorkspaceError as exc:
        raise bad_request(str(exc)) from exc
