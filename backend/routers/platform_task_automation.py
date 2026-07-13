from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    OperationalTaskAutomationRuleCreate,
    OperationalTaskAutomationRuleUpdate,
    OperationalTaskAutomationRunRequest,
    OperationalTaskDependencyActionRequest,
    OperationalTaskDependencyCreate,
    OperationalTaskDependencyUpdate,
    OperationalTaskTemplateCreate,
    OperationalTaskTemplateUpdate,
)
from services.task_automation_dependency_service import PHASE_LABEL, TaskAutomationDependencyError, TaskAutomationDependencyService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/task-automation", tags=["platform-task-automation"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def platform_task_automation_dashboard(
    agency_id: str | None = Query(default=None),
    trigger_event: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    source_entity_type: str | None = Query(default=None),
    source_entity_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await TaskAutomationDependencyService(db).platform_dashboard(
        agency_id=agency_id,
        trigger_event=trigger_event,
        status=status_filter,
        source_entity_type=source_entity_type,
        source_entity_id=source_entity_id,
    )


@router.get("/templates")
async def list_platform_task_templates(
    agency_id: str | None = Query(default=None),
    trigger_event: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    include_defaults: bool = Query(default=True),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = TaskAutomationDependencyService(db)
    return {
        "phase": PHASE_LABEL,
        "templates": await service.list_templates(agency_id=agency_id, trigger_event=trigger_event, status=status_filter, include_defaults=include_defaults),
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.post("/templates", status_code=status.HTTP_201_CREATED)
async def create_platform_task_template(
    payload: OperationalTaskTemplateCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await TaskAutomationDependencyService(db).create_template(payload, user)
    except TaskAutomationDependencyError as exc:
        raise bad_request(str(exc)) from exc


@router.put("/templates/{template_id}")
async def update_platform_task_template(
    template_id: str,
    payload: OperationalTaskTemplateUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await TaskAutomationDependencyService(db).update_template(template_id, payload, user)
    except TaskAutomationDependencyError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/rules")
async def list_platform_task_automation_rules(
    agency_id: str | None = Query(default=None),
    trigger_event: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    include_defaults: bool = Query(default=True),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = TaskAutomationDependencyService(db)
    return {
        "phase": PHASE_LABEL,
        "rules": await service.list_rules(agency_id=agency_id, trigger_event=trigger_event, status=status_filter, include_defaults=include_defaults),
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.post("/rules", status_code=status.HTTP_201_CREATED)
async def create_platform_task_automation_rule(
    payload: OperationalTaskAutomationRuleCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await TaskAutomationDependencyService(db).create_rule(payload, user)
    except TaskAutomationDependencyError as exc:
        raise bad_request(str(exc)) from exc


@router.put("/rules/{rule_id}")
async def update_platform_task_automation_rule(
    rule_id: str,
    payload: OperationalTaskAutomationRuleUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await TaskAutomationDependencyService(db).update_rule(rule_id, payload, user)
    except TaskAutomationDependencyError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/dependencies")
async def list_platform_task_dependencies(
    agency_id: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    source_entity_type: str | None = Query(default=None),
    source_entity_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = TaskAutomationDependencyService(db)
    dependencies = await service.list_dependencies(agency_id=agency_id, status=status_filter, source_entity_type=source_entity_type, source_entity_id=source_entity_id)
    return {"phase": PHASE_LABEL, "dependencies": dependencies, "metadata_only": True, **service.safety_flags()}


@router.post("/dependencies", status_code=status.HTTP_201_CREATED)
async def create_platform_task_dependency(
    payload: OperationalTaskDependencyCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await TaskAutomationDependencyService(db).create_dependency(payload, user)
    except TaskAutomationDependencyError as exc:
        raise bad_request(str(exc)) from exc


@router.put("/dependencies/{dependency_id}")
async def update_platform_task_dependency(
    dependency_id: str,
    payload: OperationalTaskDependencyUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await TaskAutomationDependencyService(db).update_dependency(dependency_id, payload, user)
    except TaskAutomationDependencyError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/dependencies/{dependency_id}/satisfy")
async def satisfy_platform_task_dependency(
    dependency_id: str,
    payload: OperationalTaskDependencyActionRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await TaskAutomationDependencyService(db).satisfy_dependency(dependency_id, payload, user)
    except TaskAutomationDependencyError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/dependencies/{dependency_id}/waive")
async def waive_platform_task_dependency(
    dependency_id: str,
    payload: OperationalTaskDependencyActionRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await TaskAutomationDependencyService(db).waive_dependency(dependency_id, payload, user)
    except TaskAutomationDependencyError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/dependencies/evaluate")
async def evaluate_platform_task_dependencies(
    agency_id: str,
    successor_task_id: str | None = Query(default=None),
    source_entity_type: str | None = Query(default=None),
    source_entity_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await TaskAutomationDependencyService(db).evaluate_dependencies(
        agency_id,
        user,
        successor_task_id=successor_task_id,
        source_entity_type=source_entity_type,
        source_entity_id=source_entity_id,
    )


@router.get("/runs")
async def list_platform_task_automation_runs(
    agency_id: str | None = Query(default=None),
    trigger_event: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    source_entity_type: str | None = Query(default=None),
    source_entity_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = TaskAutomationDependencyService(db)
    runs = await service.list_runs(agency_id=agency_id, trigger_event=trigger_event, status=status_filter, source_entity_type=source_entity_type, source_entity_id=source_entity_id)
    return {"phase": PHASE_LABEL, "runs": runs, "metadata_only": True, **service.safety_flags()}


@router.post("/runs", status_code=status.HTTP_201_CREATED)
async def run_platform_task_automation(
    payload: OperationalTaskAutomationRunRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await TaskAutomationDependencyService(db).run_automation(payload, user)
    except TaskAutomationDependencyError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/runs/{run_id}/retry")
async def retry_platform_task_automation_run(
    run_id: str,
    payload: OperationalTaskDependencyActionRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await TaskAutomationDependencyService(db).retry_run(run_id, payload, user)
    except TaskAutomationDependencyError as exc:
        raise bad_request(str(exc)) from exc
