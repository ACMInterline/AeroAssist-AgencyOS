from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import OperationalTimelineCreate, OperationalTimelineUpdate
from services.tenant_service import require_any_platform_role
from services.timeline_workspace_service import PHASE_LABEL, OperationalTimelineError, OperationalTimelineService


router = APIRouter(prefix="/api/platform/operational-timelines", tags=["platform-operational-timelines"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_platform_operational_timelines(
    agency_id: str | None = Query(default=None),
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
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await OperationalTimelineService(db).platform_response(
        agency_id=agency_id,
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
        include_archived=include_archived,
    )


@router.get("/summary")
async def summarize_platform_operational_timelines(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await OperationalTimelineService(db).platform_summary()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_platform_operational_timeline(
    payload: OperationalTimelineCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalTimelineService(db).create_entry(payload, user)
    except OperationalTimelineError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{timeline_id}")
async def get_platform_operational_timeline(
    timeline_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OperationalTimelineService(db)
    try:
        timeline_entry = await service.get_platform_entry(timeline_id)
    except OperationalTimelineError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "timeline_entry": timeline_entry,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{timeline_id}")
async def update_platform_operational_timeline(
    timeline_id: str,
    payload: OperationalTimelineUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalTimelineService(db).update_entry(timeline_id, payload, user)
    except OperationalTimelineError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/{timeline_id}")
async def delete_platform_operational_timeline(
    timeline_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalTimelineService(db).delete_entry(timeline_id, user)
    except OperationalTimelineError as exc:
        raise bad_request(str(exc)) from exc
