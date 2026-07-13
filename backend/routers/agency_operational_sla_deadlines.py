from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import OperationalDeadlineActionRequest, OperationalDeadlineCreate, OperationalDeadlineUpdate
from services.operational_sla_deadline_service import PHASE_LABEL, OperationalSlaDeadlineError, OperationalSlaDeadlineService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/deadlines", tags=["agency-deadlines"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin", "agency_agent"]
PLATFORM_ROLES = {"platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"}


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in PLATFORM_ROLES:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


async def require_write(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in PLATFORM_ROLES:
        await require_any_agency_role(db, agency_id, user, WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


def not_found(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.get("")
async def agency_deadline_dashboard(
    agency_id: str,
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
    await require_read(db, agency_id, user)
    return await OperationalSlaDeadlineService(db).agency_dashboard(
        agency_id,
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
async def agency_deadline_summary(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = OperationalSlaDeadlineService(db)
    deadlines = await service.list_deadlines(agency_id=agency_id, include_completed=True)
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "summary": service.summarize_deadlines(deadlines), "metadata_only": True, **service.safety_flags()}


@router.get("/policies")
async def list_agency_sla_policies(
    agency_id: str,
    deadline_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = OperationalSlaDeadlineService(db)
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "policies": await service.list_policies(agency_id=agency_id, deadline_type=deadline_type, include_defaults=True), "metadata_only": True, **service.safety_flags()}


@router.get("/business-calendars")
async def list_agency_business_calendars(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = OperationalSlaDeadlineService(db)
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "business_calendars": await service.list_business_calendars(agency_id=agency_id, include_defaults=True), "metadata_only": True, **service.safety_flags()}


@router.get("/items")
async def list_agency_deadlines(
    agency_id: str,
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
    await require_read(db, agency_id, user)
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
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "deadlines": deadlines, "summary": service.summarize_deadlines(deadlines), "metadata_only": True, **service.safety_flags()}


@router.post("/items", status_code=status.HTTP_201_CREATED)
async def create_agency_deadline(
    agency_id: str,
    payload: OperationalDeadlineCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OperationalSlaDeadlineService(db).create_deadline(payload, user, agency_id=agency_id)
    except OperationalSlaDeadlineError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/monitor")
async def monitor_agency_deadlines(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    return await OperationalSlaDeadlineService(db).monitor_deadlines(agency_id=agency_id, user=user)


@router.get("/{deadline_id}")
async def get_agency_deadline(
    agency_id: str,
    deadline_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    try:
        deadline = await OperationalSlaDeadlineService(db).get_deadline(deadline_id, agency_id=agency_id)
    except OperationalSlaDeadlineError as exc:
        raise not_found(str(exc)) from exc
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "deadline": deadline, "metadata_only": True}


@router.put("/{deadline_id}")
async def update_agency_deadline(
    agency_id: str,
    deadline_id: str,
    payload: OperationalDeadlineUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OperationalSlaDeadlineService(db).update_deadline(deadline_id, payload, user, agency_id=agency_id)
    except OperationalSlaDeadlineError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{deadline_id}/events")
async def list_agency_deadline_events(
    agency_id: str,
    deadline_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = OperationalSlaDeadlineService(db)
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "events": await service.list_events(deadline_id, agency_id=agency_id), "metadata_only": True, **service.safety_flags()}


async def _apply_action(agency_id: str, deadline_id: str, action: str, payload: OperationalDeadlineActionRequest, user: dict, db: Database) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OperationalSlaDeadlineService(db).apply_action(deadline_id, action, payload, user, agency_id=agency_id)
    except OperationalSlaDeadlineError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/{deadline_id}/pause")
async def pause_agency_deadline(agency_id: str, deadline_id: str, payload: OperationalDeadlineActionRequest, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await _apply_action(agency_id, deadline_id, "pause", payload, user, db)


@router.post("/{deadline_id}/resume")
async def resume_agency_deadline(agency_id: str, deadline_id: str, payload: OperationalDeadlineActionRequest, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await _apply_action(agency_id, deadline_id, "resume", payload, user, db)


@router.post("/{deadline_id}/extend")
async def extend_agency_deadline(agency_id: str, deadline_id: str, payload: OperationalDeadlineActionRequest, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await _apply_action(agency_id, deadline_id, "extend", payload, user, db)


@router.post("/{deadline_id}/complete")
async def complete_agency_deadline(agency_id: str, deadline_id: str, payload: OperationalDeadlineActionRequest, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await _apply_action(agency_id, deadline_id, "complete", payload, user, db)


@router.post("/{deadline_id}/waive")
async def waive_agency_deadline(agency_id: str, deadline_id: str, payload: OperationalDeadlineActionRequest, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await _apply_action(agency_id, deadline_id, "waive", payload, user, db)


@router.post("/{deadline_id}/recalculate")
async def recalculate_agency_deadline(agency_id: str, deadline_id: str, payload: OperationalDeadlineActionRequest, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await _apply_action(agency_id, deadline_id, "recalculate", payload, user, db)
