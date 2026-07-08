from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.tenant_service import assert_agency_access, require_any_agency_role
from services.timeline_workspace_service import PHASE_LABEL, OperationalTimelineError, OperationalTimelineService


router = APIRouter(prefix="/api/agencies/{agency_id}/operational-timelines", tags=["agency-operational-timelines"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


@router.get("")
async def list_agency_operational_timelines(
    agency_id: str,
    passenger: str | None = Query(default=None),
    booking: str | None = Query(default=None),
    ticket: str | None = Query(default=None),
    emd: str | None = Query(default=None),
    ssr: str | None = Query(default=None),
    airline: str | None = Query(default=None),
    communication_type: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    status: str | None = Query(default=None),
    date: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await OperationalTimelineService(db).agency_response(
        agency_id,
        passenger=passenger,
        booking=booking,
        ticket=ticket,
        emd=emd,
        ssr=ssr,
        airline=airline,
        communication_type=communication_type,
        event_type=event_type,
        priority=priority,
        status=status,
        date=date,
    )


@router.get("/summary")
async def summarize_agency_operational_timelines(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await OperationalTimelineService(db).agency_summary(agency_id)


@router.get("/{timeline_id}")
async def get_agency_operational_timeline(
    agency_id: str,
    timeline_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = OperationalTimelineService(db)
    try:
        timeline_entry = await service.get_agency_entry(agency_id, timeline_id)
    except OperationalTimelineError:
        raise not_found("Operational timeline metadata not found.")
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "timeline_entry": timeline_entry,
        "read_only": True,
        "metadata_only": True,
        **service.safety_flags(),
    }
