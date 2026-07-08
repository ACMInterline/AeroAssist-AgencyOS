from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.tenant_service import assert_agency_access, require_any_agency_role
from services.ticket_workspace_service import PHASE_LABEL, TicketWorkspaceError, TicketWorkspaceService


router = APIRouter(prefix="/api/agencies/{agency_id}/ticket-workspaces", tags=["agency-ticket-workspaces"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


@router.get("")
async def list_agency_ticket_workspaces(
    agency_id: str,
    status_filter: str | None = Query(default=None, alias="status"),
    document_status: str | None = Query(default=None),
    validating_carrier: str | None = Query(default=None),
    issue_date: date | None = Query(default=None),
    passenger: str | None = Query(default=None),
    booking_reference: str | None = Query(default=None),
    currency: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await TicketWorkspaceService(db).agency_response(
        agency_id,
        ticket_status=status_filter,
        ticket_document_status=document_status,
        validating_carrier=validating_carrier,
        issue_date=issue_date,
        passenger=passenger,
        booking_reference=booking_reference,
        currency=currency,
    )


@router.get("/summary")
async def summarize_agency_ticket_workspaces(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await TicketWorkspaceService(db).agency_summary(agency_id)


@router.get("/{ticket_workspace_id}")
async def get_agency_ticket_workspace(
    agency_id: str,
    ticket_workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = TicketWorkspaceService(db)
    try:
        ticket_workspace = await service.get_agency_ticket(agency_id, ticket_workspace_id)
    except TicketWorkspaceError:
        raise not_found("Ticket workspace metadata not found.")
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "ticket_workspace": ticket_workspace,
        "read_only": True,
        "metadata_only": True,
        **service.safety_flags(),
    }
