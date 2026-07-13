from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    OperationalBusinessCalendarCreate,
    OperationalBusinessCalendarUpdate,
    OperationalDeadlineActionRequest,
    OperationalDeadlineCreate,
    OperationalDeadlineUpdate,
    OperationalSlaPolicyCreate,
    OperationalSlaPolicyUpdate,
)
from services.operational_sla_deadline_service import PHASE_LABEL, OperationalSlaDeadlineError, OperationalSlaDeadlineService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/sla-policies", tags=["platform-sla-policies"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


def not_found(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.get("")
async def platform_sla_dashboard(
    agency_id: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    breach_state: str | None = Query(default=None),
    deadline_type: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    service_family: str | None = Query(default=None),
    source_entity_type: str | None = Query(default=None),
    source_entity_id: str | None = Query(default=None),
    workflow_instance_id: str | None = Query(default=None),
    work_item_id: str | None = Query(default=None),
    include_completed: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await OperationalSlaDeadlineService(db).platform_dashboard(
        agency_id=agency_id,
        status=status_filter,
        breach_state=breach_state,
        deadline_type=deadline_type,
        priority=priority,
        service_family=service_family,
        source_entity_type=source_entity_type,
        source_entity_id=source_entity_id,
        workflow_instance_id=workflow_instance_id,
        work_item_id=work_item_id,
        include_completed=include_completed,
    )


@router.get("/summary")
async def platform_sla_summary(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OperationalSlaDeadlineService(db)
    deadlines = await service.list_deadlines(agency_id=agency_id, include_completed=True)
    return {"phase": PHASE_LABEL, "summary": service.summarize_deadlines(deadlines), "metadata_only": True, **service.safety_flags()}


@router.get("/policies")
async def list_platform_sla_policies(
    agency_id: str | None = Query(default=None),
    deadline_type: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    include_defaults: bool = Query(default=True),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OperationalSlaDeadlineService(db)
    return {
        "phase": PHASE_LABEL,
        "policies": await service.list_policies(agency_id=agency_id, deadline_type=deadline_type, status=status_filter, include_defaults=include_defaults),
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.post("/policies", status_code=status.HTTP_201_CREATED)
async def create_platform_sla_policy(
    payload: OperationalSlaPolicyCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalSlaDeadlineService(db).create_policy(payload, user)
    except OperationalSlaDeadlineError as exc:
        raise bad_request(str(exc)) from exc


@router.put("/policies/{policy_id}")
async def update_platform_sla_policy(
    policy_id: str,
    payload: OperationalSlaPolicyUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalSlaDeadlineService(db).update_policy(policy_id, payload, user)
    except OperationalSlaDeadlineError as exc:
        raise not_found(str(exc)) from exc


@router.get("/business-calendars")
async def list_platform_business_calendars(
    agency_id: str | None = Query(default=None),
    include_defaults: bool = Query(default=True),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OperationalSlaDeadlineService(db)
    return {"phase": PHASE_LABEL, "business_calendars": await service.list_business_calendars(agency_id=agency_id, include_defaults=include_defaults), "metadata_only": True, **service.safety_flags()}


@router.post("/business-calendars", status_code=status.HTTP_201_CREATED)
async def create_platform_business_calendar(
    payload: OperationalBusinessCalendarCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalSlaDeadlineService(db).create_business_calendar(payload, user)
    except OperationalSlaDeadlineError as exc:
        raise bad_request(str(exc)) from exc


@router.put("/business-calendars/{calendar_id}")
async def update_platform_business_calendar(
    calendar_id: str,
    payload: OperationalBusinessCalendarUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalSlaDeadlineService(db).update_business_calendar(calendar_id, payload, user)
    except OperationalSlaDeadlineError as exc:
        raise not_found(str(exc)) from exc


@router.get("/deadlines")
async def list_platform_deadlines(
    agency_id: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    breach_state: str | None = Query(default=None),
    deadline_type: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    service_family: str | None = Query(default=None),
    source_entity_type: str | None = Query(default=None),
    source_entity_id: str | None = Query(default=None),
    workflow_instance_id: str | None = Query(default=None),
    work_item_id: str | None = Query(default=None),
    include_completed: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OperationalSlaDeadlineService(db)
    deadlines = await service.list_deadlines(
        agency_id=agency_id,
        status=status_filter,
        breach_state=breach_state,
        deadline_type=deadline_type,
        priority=priority,
        service_family=service_family,
        source_entity_type=source_entity_type,
        source_entity_id=source_entity_id,
        workflow_instance_id=workflow_instance_id,
        work_item_id=work_item_id,
        include_completed=include_completed,
    )
    return {"phase": PHASE_LABEL, "deadlines": deadlines, "summary": service.summarize_deadlines(deadlines), "metadata_only": True, **service.safety_flags()}


@router.post("/deadlines", status_code=status.HTTP_201_CREATED)
async def create_platform_deadline(
    payload: OperationalDeadlineCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalSlaDeadlineService(db).create_deadline(payload, user)
    except OperationalSlaDeadlineError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/deadlines/monitor")
async def monitor_platform_deadlines(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await OperationalSlaDeadlineService(db).monitor_deadlines(agency_id=agency_id, user=user)


@router.get("/deadlines/{deadline_id}")
async def get_platform_deadline(
    deadline_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    try:
        deadline = await OperationalSlaDeadlineService(db).get_deadline(deadline_id)
    except OperationalSlaDeadlineError as exc:
        raise not_found(str(exc)) from exc
    return {"phase": PHASE_LABEL, "deadline": deadline, "metadata_only": True}


@router.put("/deadlines/{deadline_id}")
async def update_platform_deadline(
    deadline_id: str,
    payload: OperationalDeadlineUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalSlaDeadlineService(db).update_deadline(deadline_id, payload, user)
    except OperationalSlaDeadlineError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/deadlines/{deadline_id}/events")
async def list_platform_deadline_events(
    deadline_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OperationalSlaDeadlineService(db)
    return {"phase": PHASE_LABEL, "events": await service.list_events(deadline_id), "metadata_only": True, **service.safety_flags()}


async def _apply_action(deadline_id: str, action: str, payload: OperationalDeadlineActionRequest, user: dict, db: Database) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalSlaDeadlineService(db).apply_action(deadline_id, action, payload, user)
    except OperationalSlaDeadlineError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/deadlines/{deadline_id}/pause")
async def pause_platform_deadline(deadline_id: str, payload: OperationalDeadlineActionRequest, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await _apply_action(deadline_id, "pause", payload, user, db)


@router.post("/deadlines/{deadline_id}/resume")
async def resume_platform_deadline(deadline_id: str, payload: OperationalDeadlineActionRequest, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await _apply_action(deadline_id, "resume", payload, user, db)


@router.post("/deadlines/{deadline_id}/extend")
async def extend_platform_deadline(deadline_id: str, payload: OperationalDeadlineActionRequest, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await _apply_action(deadline_id, "extend", payload, user, db)


@router.post("/deadlines/{deadline_id}/complete")
async def complete_platform_deadline(deadline_id: str, payload: OperationalDeadlineActionRequest, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await _apply_action(deadline_id, "complete", payload, user, db)


@router.post("/deadlines/{deadline_id}/waive")
async def waive_platform_deadline(deadline_id: str, payload: OperationalDeadlineActionRequest, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await _apply_action(deadline_id, "waive", payload, user, db)


@router.post("/deadlines/{deadline_id}/recalculate")
async def recalculate_platform_deadline(deadline_id: str, payload: OperationalDeadlineActionRequest, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await _apply_action(deadline_id, "recalculate", payload, user, db)
