from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    OperationalQueueDefinitionCreate,
    OperationalQueueDefinitionUpdate,
    OperationalQueueViewCreate,
    OperationalQueueViewUpdate,
    OperationalWorkItemCreate,
    OperationalWorkItemGenerateRequest,
    OperationalWorkItemUpdate,
)
from services.agent_work_queue_service import PHASE_LABEL, AgentWorkQueueError, AgentWorkQueueService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/work-queues", tags=["platform-work-queues"])

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
async def platform_work_queue_dashboard(
    agency_id: str | None = Query(default=None),
    queue_code: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    priority: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    work_item_type: str | None = Query(default=None),
    source_entity_type: str | None = Query(default=None),
    assigned_user_id: str | None = Query(default=None),
    assigned_team_code: str | None = Query(default=None),
    blocker_status: str | None = Query(default=None),
    sla_status: str | None = Query(default=None),
    include_completed: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AgentWorkQueueService(db).platform_dashboard(
        agency_id=agency_id,
        queue_code=queue_code,
        status=status_filter,
        priority=priority,
        severity=severity,
        work_item_type=work_item_type,
        source_entity_type=source_entity_type,
        assigned_user_id=assigned_user_id,
        assigned_team_code=assigned_team_code,
        blocker_status=blocker_status,
        sla_status=sla_status,
        include_completed=include_completed,
    )


@router.get("/summary")
async def platform_work_queue_summary(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = AgentWorkQueueService(db)
    items = await service.list_work_items(agency_id=agency_id, include_completed=True)
    return {"phase": PHASE_LABEL, "summary": service.summarize_counts(items), "queue_summary": service.queue_summary(items), "metadata_only": True, **service.safety_flags()}


@router.get("/definitions")
async def list_platform_queue_definitions(
    agency_id: str | None = Query(default=None),
    include_defaults: bool = Query(default=True),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = AgentWorkQueueService(db)
    return {"phase": PHASE_LABEL, "queue_definitions": await service.list_queue_definitions(agency_id=agency_id, include_defaults=include_defaults), "metadata_only": True, **service.safety_flags()}


@router.post("/definitions", status_code=status.HTTP_201_CREATED)
async def create_platform_queue_definition(
    payload: OperationalQueueDefinitionCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AgentWorkQueueService(db).create_queue_definition(payload, user)
    except AgentWorkQueueError as exc:
        raise bad_request(str(exc)) from exc


@router.put("/definitions/{definition_id}")
async def update_platform_queue_definition(
    definition_id: str,
    payload: OperationalQueueDefinitionUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AgentWorkQueueService(db).update_queue_definition(definition_id, payload, user)
    except AgentWorkQueueError as exc:
        raise not_found(str(exc)) from exc


@router.get("/views")
async def list_platform_queue_views(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = AgentWorkQueueService(db)
    return {"phase": PHASE_LABEL, "queue_views": await service.list_queue_views(agency_id=agency_id), "metadata_only": True, **service.safety_flags()}


@router.post("/views", status_code=status.HTTP_201_CREATED)
async def create_platform_queue_view(
    payload: OperationalQueueViewCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AgentWorkQueueService(db).create_queue_view(payload, user)
    except AgentWorkQueueError as exc:
        raise bad_request(str(exc)) from exc


@router.put("/views/{view_id}")
async def update_platform_queue_view(
    view_id: str,
    payload: OperationalQueueViewUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AgentWorkQueueService(db).update_queue_view(view_id, payload, user)
    except AgentWorkQueueError as exc:
        raise not_found(str(exc)) from exc


@router.get("/work-items")
async def list_platform_work_items(
    agency_id: str | None = Query(default=None),
    queue_code: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    priority: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    work_item_type: str | None = Query(default=None),
    source_entity_type: str | None = Query(default=None),
    assigned_user_id: str | None = Query(default=None),
    assigned_team_code: str | None = Query(default=None),
    blocker_status: str | None = Query(default=None),
    sla_status: str | None = Query(default=None),
    include_completed: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = AgentWorkQueueService(db)
    items = await service.list_work_items(
        agency_id=agency_id,
        queue_code=queue_code,
        status=status_filter,
        priority=priority,
        severity=severity,
        work_item_type=work_item_type,
        source_entity_type=source_entity_type,
        assigned_user_id=assigned_user_id,
        assigned_team_code=assigned_team_code,
        blocker_status=blocker_status,
        sla_status=sla_status,
        include_completed=include_completed,
    )
    return {"phase": PHASE_LABEL, "items": items, "summary": service.summarize_counts(items), "metadata_only": True, **service.safety_flags()}


@router.post("/work-items", status_code=status.HTTP_201_CREATED)
async def create_platform_work_item(
    payload: OperationalWorkItemCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AgentWorkQueueService(db).create_work_item(payload, user)
    except AgentWorkQueueError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/work-items/generate", status_code=status.HTTP_201_CREATED)
async def generate_platform_work_item(
    payload: OperationalWorkItemGenerateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AgentWorkQueueService(db).generate_work_item(payload, user)
    except AgentWorkQueueError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/work-items/sync")
async def sync_platform_work_items(
    agency_id: str = Query(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await AgentWorkQueueService(db).sync_sources(agency_id, user)


@router.get("/work-items/{work_item_id}")
async def get_platform_work_item(
    work_item_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    try:
        work_item = await AgentWorkQueueService(db).get_work_item(work_item_id)
    except AgentWorkQueueError as exc:
        raise not_found(str(exc)) from exc
    return {"phase": PHASE_LABEL, "work_item": work_item, "metadata_only": True}


@router.put("/work-items/{work_item_id}")
async def update_platform_work_item(
    work_item_id: str,
    payload: OperationalWorkItemUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AgentWorkQueueService(db).update_work_item(work_item_id, payload, user)
    except AgentWorkQueueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/work-items/{work_item_id}/events")
async def list_platform_work_item_events(
    work_item_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = AgentWorkQueueService(db)
    return {"phase": PHASE_LABEL, "events": await service.list_assignment_events(work_item_id), "preserve_actor_history": True, "metadata_only": True, **service.safety_flags()}
