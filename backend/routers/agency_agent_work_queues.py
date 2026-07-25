from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    OperationalAssignmentRouteRequest,
    OperationalBulkAssignmentRequest,
    OperationalQueueDefinitionCreate,
    OperationalQueueDefinitionUpdate,
    OperationalQueueViewCreate,
    OperationalQueueViewUpdate,
    OperationalWorkItemActionRequest,
    OperationalWorkItemCreate,
    OperationalWorkItemGenerateRequest,
    OperationalWorkItemUpdate,
)
from services.agent_work_queue_service import PHASE_LABEL, AgentWorkQueueError, AgentWorkQueueService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/work-queue", tags=["agency-work-queue"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin", "agency_agent"]
ADMIN_ROLES = ["agency_owner", "agency_admin"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    await require_any_agency_role(db, agency_id, user, READ_ROLES)


async def require_write(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    await require_any_agency_role(db, agency_id, user, WRITE_ROLES)


async def require_admin(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    await require_any_agency_role(db, agency_id, user, ADMIN_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


def not_found(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.get("")
async def agency_work_queue_dashboard(
    agency_id: str,
    queue_code: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    priority: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    work_item_type: str | None = Query(default=None),
    source_entity_type: str | None = Query(default=None),
    source_entity_id: str | None = Query(default=None),
    assigned_user_id: str | None = Query(default=None),
    assigned_team_code: str | None = Query(default=None),
    blocker_status: str | None = Query(default=None),
    sla_status: str | None = Query(default=None),
    include_completed: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await AgentWorkQueueService(db).agency_dashboard(
        agency_id,
        user,
        queue_code=queue_code,
        status=status_filter,
        priority=priority,
        severity=severity,
        work_item_type=work_item_type,
        source_entity_type=source_entity_type,
        source_entity_id=source_entity_id,
        assigned_user_id=assigned_user_id,
        assigned_team_code=assigned_team_code,
        blocker_status=blocker_status,
        sla_status=sla_status,
        include_completed=include_completed,
    )


@router.get("/summary")
async def agency_work_queue_summary(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AgentWorkQueueService(db)
    items = await service.list_work_items(agency_id=agency_id, include_completed=True, current_user_id=user.get("id"))
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "summary": service.summarize_counts(items), "queue_summary": service.queue_summary(items), "metadata_only": True, **service.safety_flags()}


@router.get("/queue-definitions")
async def list_agency_queue_definitions(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AgentWorkQueueService(db)
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "queue_definitions": await service.list_queue_definitions(agency_id=agency_id, include_defaults=True), "metadata_only": True, **service.safety_flags()}


@router.post("/queue-definitions", status_code=status.HTTP_201_CREATED)
async def create_agency_queue_definition(
    agency_id: str,
    payload: OperationalQueueDefinitionCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_admin(db, agency_id, user)
    try:
        return await AgentWorkQueueService(db).create_queue_definition(
            payload, user, agency_id=agency_id
        )
    except AgentWorkQueueError as exc:
        raise bad_request(str(exc)) from exc


@router.put("/queue-definitions/{definition_id}")
async def update_agency_queue_definition(
    agency_id: str,
    definition_id: str,
    payload: OperationalQueueDefinitionUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_admin(db, agency_id, user)
    try:
        return await AgentWorkQueueService(db).update_queue_definition(
            definition_id,
            payload,
            user,
            agency_id=agency_id,
        )
    except AgentWorkQueueError as exc:
        raise not_found(str(exc)) from exc


@router.get("/views")
async def list_agency_queue_views(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AgentWorkQueueService(db)
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "queue_views": await service.list_queue_views(agency_id=agency_id, owner_user_id=user.get("id")), "metadata_only": True, **service.safety_flags()}


@router.post("/views", status_code=status.HTTP_201_CREATED)
async def create_agency_queue_view(
    agency_id: str,
    payload: OperationalQueueViewCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await AgentWorkQueueService(db).create_queue_view(payload, user, agency_id=agency_id)
    except AgentWorkQueueError as exc:
        raise bad_request(str(exc)) from exc


@router.put("/views/{view_id}")
async def update_agency_queue_view(
    agency_id: str,
    view_id: str,
    payload: OperationalQueueViewUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await AgentWorkQueueService(db).update_queue_view(view_id, payload, user, agency_id=agency_id)
    except AgentWorkQueueError as exc:
        raise not_found(str(exc)) from exc


@router.post("/work-items", status_code=status.HTTP_201_CREATED)
async def create_agency_work_item(
    agency_id: str,
    payload: OperationalWorkItemCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await AgentWorkQueueService(db).create_work_item(payload, user, agency_id=agency_id)
    except AgentWorkQueueError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/work-items/generate", status_code=status.HTTP_201_CREATED)
async def generate_agency_work_item(
    agency_id: str,
    payload: OperationalWorkItemGenerateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await AgentWorkQueueService(db).generate_work_item(payload, user, agency_id=agency_id)
    except AgentWorkQueueError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/work-items/sync")
async def sync_agency_work_items(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    return await AgentWorkQueueService(db).sync_sources(agency_id, user)


@router.post("/work-items/bulk-assign")
async def bulk_assign_agency_work_items(
    agency_id: str,
    payload: OperationalBulkAssignmentRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await AgentWorkQueueService(db).bulk_assign(payload, user, agency_id)
    except AgentWorkQueueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/work-items/{work_item_id}")
async def get_agency_work_item(
    agency_id: str,
    work_item_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    try:
        work_item = await AgentWorkQueueService(db).get_work_item(work_item_id, agency_id=agency_id)
    except AgentWorkQueueError as exc:
        raise not_found(str(exc)) from exc
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "work_item": work_item, "metadata_only": True}


@router.put("/work-items/{work_item_id}")
async def update_agency_work_item(
    agency_id: str,
    work_item_id: str,
    payload: OperationalWorkItemUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await AgentWorkQueueService(db).update_work_item(work_item_id, payload, user, agency_id=agency_id)
    except AgentWorkQueueError as exc:
        if "version conflict" in str(exc).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(exc)
            ) from exc
        raise bad_request(str(exc)) from exc


@router.get("/work-items/{work_item_id}/events")
async def list_agency_work_item_events(
    agency_id: str,
    work_item_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AgentWorkQueueService(db)
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "events": await service.list_assignment_events(work_item_id, agency_id=agency_id), "preserve_actor_history": True, "metadata_only": True, **service.safety_flags()}


async def _apply_action(agency_id: str, work_item_id: str, action: str, payload: OperationalWorkItemActionRequest, user: dict, db: Database) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await AgentWorkQueueService(db).apply_action(work_item_id, action, payload, user, agency_id=agency_id)
    except AgentWorkQueueError as exc:
        if "version conflict" in str(exc).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(exc)
            ) from exc
        raise bad_request(str(exc)) from exc


@router.post("/work-items/{work_item_id}/assign-self")
async def assign_work_item_to_self(
    agency_id: str,
    work_item_id: str,
    payload: OperationalWorkItemActionRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    return await _apply_action(agency_id, work_item_id, "assign_self", payload, user, db)


@router.post("/work-items/{work_item_id}/assign")
async def assign_work_item(
    agency_id: str,
    work_item_id: str,
    payload: OperationalWorkItemActionRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    return await _apply_action(agency_id, work_item_id, "assign", payload, user, db)


@router.post("/work-items/{work_item_id}/route-assignment")
async def route_work_item_assignment(
    agency_id: str,
    work_item_id: str,
    payload: OperationalAssignmentRouteRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await AgentWorkQueueService(db).route_assignment(
            work_item_id,
            strategy=payload.strategy,
            fixed_user_id=payload.fixed_user_id,
            fixed_team_code=payload.fixed_team_code,
            parent_owner_user_id=payload.parent_owner_user_id,
            reason=payload.reason,
            expected_version=payload.expected_version,
            user=user,
            agency_id=agency_id,
        )
    except AgentWorkQueueError as exc:
        if "version conflict" in str(exc).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(exc)
            ) from exc
        raise bad_request(str(exc)) from exc


@router.post("/work-items/{work_item_id}/reassign")
async def reassign_work_item(
    agency_id: str,
    work_item_id: str,
    payload: OperationalWorkItemActionRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    return await _apply_action(agency_id, work_item_id, "reassign", payload, user, db)


@router.post("/work-items/{work_item_id}/unassign")
async def unassign_work_item(
    agency_id: str,
    work_item_id: str,
    payload: OperationalWorkItemActionRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    return await _apply_action(agency_id, work_item_id, "unassign", payload, user, db)


@router.post("/work-items/{work_item_id}/accept")
async def accept_work_item(
    agency_id: str,
    work_item_id: str,
    payload: OperationalWorkItemActionRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    return await _apply_action(agency_id, work_item_id, "accept", payload, user, db)


@router.post("/work-items/{work_item_id}/release")
async def release_work_item(
    agency_id: str,
    work_item_id: str,
    payload: OperationalWorkItemActionRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    return await _apply_action(agency_id, work_item_id, "release", payload, user, db)


@router.post("/work-items/{work_item_id}/in-progress")
async def mark_work_item_in_progress(
    agency_id: str,
    work_item_id: str,
    payload: OperationalWorkItemActionRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    return await _apply_action(agency_id, work_item_id, "in_progress", payload, user, db)


@router.post("/work-items/{work_item_id}/block")
async def block_work_item(
    agency_id: str,
    work_item_id: str,
    payload: OperationalWorkItemActionRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    return await _apply_action(agency_id, work_item_id, "block", payload, user, db)


@router.post("/work-items/{work_item_id}/complete")
async def complete_work_item(
    agency_id: str,
    work_item_id: str,
    payload: OperationalWorkItemActionRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    return await _apply_action(agency_id, work_item_id, "complete", payload, user, db)


@router.post("/work-items/{work_item_id}/reopen")
async def reopen_work_item(
    agency_id: str,
    work_item_id: str,
    payload: OperationalWorkItemActionRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    return await _apply_action(agency_id, work_item_id, "reopen", payload, user, db)


@router.post("/work-items/{work_item_id}/start")
async def start_work_item(
    agency_id: str,
    work_item_id: str,
    payload: OperationalWorkItemActionRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    return await _apply_action(agency_id, work_item_id, "start", payload, user, db)


@router.post("/work-items/{work_item_id}/wait")
async def wait_work_item(
    agency_id: str,
    work_item_id: str,
    payload: OperationalWorkItemActionRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    return await _apply_action(agency_id, work_item_id, "wait", payload, user, db)


@router.post("/work-items/{work_item_id}/resolve-blocker")
async def resolve_work_item_blocker(
    agency_id: str,
    work_item_id: str,
    payload: OperationalWorkItemActionRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    return await _apply_action(
        agency_id, work_item_id, "resolve_blocker", payload, user, db
    )


@router.post("/work-items/{work_item_id}/cancel")
async def cancel_work_item(
    agency_id: str,
    work_item_id: str,
    payload: OperationalWorkItemActionRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    return await _apply_action(agency_id, work_item_id, "cancel", payload, user, db)


@router.post("/work-items/{work_item_id}/escalate")
async def escalate_work_item(
    agency_id: str,
    work_item_id: str,
    payload: OperationalWorkItemActionRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    return await _apply_action(
        agency_id, work_item_id, "escalate", payload, user, db
    )


@router.post("/work-items/{work_item_id}/request-approval")
async def request_work_item_approval(
    agency_id: str,
    work_item_id: str,
    payload: OperationalWorkItemActionRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    return await _apply_action(
        agency_id, work_item_id, "request_approval", payload, user, db
    )
