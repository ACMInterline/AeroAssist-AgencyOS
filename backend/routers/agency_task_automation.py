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
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/task-automation", tags=["agency-task-automation"])

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


@router.get("")
async def agency_task_automation_dashboard(
    agency_id: str,
    trigger_event: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    source_entity_type: str | None = Query(default=None),
    source_entity_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await TaskAutomationDependencyService(db).agency_dashboard(
        agency_id,
        trigger_event=trigger_event,
        status=status_filter,
        source_entity_type=source_entity_type,
        source_entity_id=source_entity_id,
    )


@router.get("/templates")
async def list_agency_task_templates(
    agency_id: str,
    trigger_event: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    include_defaults: bool = Query(default=True),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = TaskAutomationDependencyService(db)
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "templates": await service.list_templates(agency_id=agency_id, trigger_event=trigger_event, status=status_filter, include_defaults=include_defaults),
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.post("/templates", status_code=status.HTTP_201_CREATED)
async def create_agency_task_template(
    agency_id: str,
    payload: OperationalTaskTemplateCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await TaskAutomationDependencyService(db).create_template({**payload.model_dump(mode="json", exclude_none=True), "agency_id": agency_id}, user)
    except TaskAutomationDependencyError as exc:
        raise bad_request(str(exc)) from exc


@router.put("/templates/{template_id}")
async def update_agency_task_template(
    agency_id: str,
    template_id: str,
    payload: OperationalTaskTemplateUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await TaskAutomationDependencyService(db).update_template(template_id, payload, user, agency_id=agency_id)
    except TaskAutomationDependencyError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/rules")
async def list_agency_task_automation_rules(
    agency_id: str,
    trigger_event: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    include_defaults: bool = Query(default=True),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = TaskAutomationDependencyService(db)
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "rules": await service.list_rules(agency_id=agency_id, trigger_event=trigger_event, status=status_filter, include_defaults=include_defaults),
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.post("/rules", status_code=status.HTTP_201_CREATED)
async def create_agency_task_automation_rule(
    agency_id: str,
    payload: OperationalTaskAutomationRuleCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await TaskAutomationDependencyService(db).create_rule({**payload.model_dump(mode="json", exclude_none=True), "agency_id": agency_id}, user)
    except TaskAutomationDependencyError as exc:
        raise bad_request(str(exc)) from exc


@router.put("/rules/{rule_id}")
async def update_agency_task_automation_rule(
    agency_id: str,
    rule_id: str,
    payload: OperationalTaskAutomationRuleUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await TaskAutomationDependencyService(db).update_rule(rule_id, payload, user, agency_id=agency_id)
    except TaskAutomationDependencyError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/dependencies")
async def list_agency_task_dependencies(
    agency_id: str,
    status_filter: str | None = Query(default=None, alias="status"),
    source_entity_type: str | None = Query(default=None),
    source_entity_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = TaskAutomationDependencyService(db)
    dependencies = await service.list_dependencies(agency_id=agency_id, status=status_filter, source_entity_type=source_entity_type, source_entity_id=source_entity_id)
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "dependencies": dependencies, "metadata_only": True, **service.safety_flags()}


@router.post("/dependencies", status_code=status.HTTP_201_CREATED)
async def create_agency_task_dependency(
    agency_id: str,
    payload: OperationalTaskDependencyCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await TaskAutomationDependencyService(db).create_dependency(payload, user, agency_id=agency_id)
    except TaskAutomationDependencyError as exc:
        raise bad_request(str(exc)) from exc


@router.put("/dependencies/{dependency_id}")
async def update_agency_task_dependency(
    agency_id: str,
    dependency_id: str,
    payload: OperationalTaskDependencyUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await TaskAutomationDependencyService(db).update_dependency(dependency_id, payload, user, agency_id=agency_id)
    except TaskAutomationDependencyError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/dependencies/{dependency_id}/satisfy")
async def satisfy_agency_task_dependency(
    agency_id: str,
    dependency_id: str,
    payload: OperationalTaskDependencyActionRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await TaskAutomationDependencyService(db).satisfy_dependency(dependency_id, payload, user, agency_id=agency_id)
    except TaskAutomationDependencyError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/dependencies/{dependency_id}/waive")
async def waive_agency_task_dependency(
    agency_id: str,
    dependency_id: str,
    payload: OperationalTaskDependencyActionRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await TaskAutomationDependencyService(db).waive_dependency(dependency_id, payload, user, agency_id=agency_id)
    except TaskAutomationDependencyError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/dependencies/evaluate")
async def evaluate_agency_task_dependencies(
    agency_id: str,
    successor_task_id: str | None = Query(default=None),
    source_entity_type: str | None = Query(default=None),
    source_entity_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    return await TaskAutomationDependencyService(db).evaluate_dependencies(
        agency_id,
        user,
        successor_task_id=successor_task_id,
        source_entity_type=source_entity_type,
        source_entity_id=source_entity_id,
    )


@router.get("/runs")
async def list_agency_task_automation_runs(
    agency_id: str,
    trigger_event: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    source_entity_type: str | None = Query(default=None),
    source_entity_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = TaskAutomationDependencyService(db)
    runs = await service.list_runs(agency_id=agency_id, trigger_event=trigger_event, status=status_filter, source_entity_type=source_entity_type, source_entity_id=source_entity_id)
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "runs": runs, "metadata_only": True, **service.safety_flags()}


@router.post("/runs", status_code=status.HTTP_201_CREATED)
async def run_agency_task_automation(
    agency_id: str,
    payload: OperationalTaskAutomationRunRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await TaskAutomationDependencyService(db).run_automation(payload, user, agency_id=agency_id)
    except TaskAutomationDependencyError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/runs/{run_id}/retry")
async def retry_agency_task_automation_run(
    agency_id: str,
    run_id: str,
    payload: OperationalTaskDependencyActionRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await TaskAutomationDependencyService(db).retry_run(run_id, payload, user, agency_id=agency_id)
    except TaskAutomationDependencyError as exc:
        raise bad_request(str(exc)) from exc
