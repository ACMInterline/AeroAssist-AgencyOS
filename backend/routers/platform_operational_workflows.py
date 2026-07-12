from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    OperationalWorkflowDefinitionCreate,
    OperationalWorkflowDefinitionUpdate,
    OperationalWorkflowGuardCreate,
    OperationalWorkflowGuardUpdate,
    OperationalWorkflowInstanceStartRequest,
    OperationalWorkflowTransitionRequest,
    OperationalWorkflowWarningAcknowledgementRequest,
)
from services.operational_workflow_orchestration_service import (
    PHASE_LABEL,
    OperationalWorkflowOrchestrationError,
    OperationalWorkflowOrchestrationService,
)
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/operational-workflows", tags=["platform-operational-workflows"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def platform_operational_workflows_dashboard(
    agency_id: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    workflow_status: str | None = Query(default=None),
    current_state: str | None = Query(default=None),
    workflow_definition_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await OperationalWorkflowOrchestrationService(db).platform_dashboard(
        agency_id=agency_id,
        entity_type=entity_type,
        status=status_filter,
        workflow_status=workflow_status,
        current_state=current_state,
        workflow_definition_id=workflow_definition_id,
    )


@router.get("/summary")
async def platform_operational_workflows_summary(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OperationalWorkflowOrchestrationService(db)
    return {"phase": PHASE_LABEL, "summary": await service.summary(agency_id=agency_id), "metadata_only": True, **service.safety_flags()}


@router.get("/diagnostics")
async def platform_operational_workflow_diagnostics(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await OperationalWorkflowOrchestrationService(db).diagnostics()


@router.get("/state-transition-maps")
async def platform_operational_workflow_state_transition_maps(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OperationalWorkflowOrchestrationService(db)
    return {"phase": PHASE_LABEL, "state_transition_maps": service.state_transition_maps(), "metadata_only": True, **service.safety_flags()}


@router.get("/definitions")
async def list_platform_operational_workflow_definitions(
    entity_type: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    include_defaults: bool = Query(default=True),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OperationalWorkflowOrchestrationService(db)
    return {
        "phase": PHASE_LABEL,
        "definitions": await service.list_definitions(entity_type=entity_type, status=status_filter, include_defaults=include_defaults),
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.post("/definitions", status_code=status.HTTP_201_CREATED)
async def create_platform_operational_workflow_definition(
    payload: OperationalWorkflowDefinitionCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalWorkflowOrchestrationService(db).create_definition(payload, user)
    except OperationalWorkflowOrchestrationError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/definitions/{definition_id}")
async def get_platform_operational_workflow_definition(
    definition_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OperationalWorkflowOrchestrationService(db)
    try:
        definition = await service.get_definition(definition_id)
    except OperationalWorkflowOrchestrationError as exc:
        raise bad_request(str(exc)) from exc
    return {"phase": PHASE_LABEL, "workflow_definition": definition, "metadata_only": True, **service.safety_flags()}


@router.put("/definitions/{definition_id}")
async def update_platform_operational_workflow_definition(
    definition_id: str,
    payload: OperationalWorkflowDefinitionUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalWorkflowOrchestrationService(db).update_definition(definition_id, payload, user)
    except OperationalWorkflowOrchestrationError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/definitions/{definition_id}/versions", status_code=status.HTTP_201_CREATED)
async def version_platform_operational_workflow_definition(
    definition_id: str,
    payload: OperationalWorkflowDefinitionUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalWorkflowOrchestrationService(db).create_definition_version(definition_id, payload, user)
    except OperationalWorkflowOrchestrationError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/guards")
async def list_platform_operational_workflow_guards(
    workflow_definition_id: str | None = Query(default=None),
    transition_code: str | None = Query(default=None),
    guard_type: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OperationalWorkflowOrchestrationService(db)
    return {
        "phase": PHASE_LABEL,
        "guards": await service.list_guards(workflow_definition_id=workflow_definition_id, transition_code=transition_code, guard_type=guard_type, is_active=is_active),
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.post("/guards", status_code=status.HTTP_201_CREATED)
async def create_platform_operational_workflow_guard(
    payload: OperationalWorkflowGuardCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalWorkflowOrchestrationService(db).create_guard(payload, user)
    except OperationalWorkflowOrchestrationError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/guards/{guard_id}")
async def get_platform_operational_workflow_guard(
    guard_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OperationalWorkflowOrchestrationService(db)
    try:
        guard = await service.get_guard(guard_id)
    except OperationalWorkflowOrchestrationError as exc:
        raise bad_request(str(exc)) from exc
    return {"phase": PHASE_LABEL, "workflow_guard": guard, "metadata_only": True, **service.safety_flags()}


@router.put("/guards/{guard_id}")
async def update_platform_operational_workflow_guard(
    guard_id: str,
    payload: OperationalWorkflowGuardUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalWorkflowOrchestrationService(db).update_guard(guard_id, payload, user)
    except OperationalWorkflowOrchestrationError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/instances")
async def list_platform_operational_workflow_instances(
    agency_id: str | None = Query(default=None),
    workflow_definition_id: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    entity_id: str | None = Query(default=None),
    workflow_status: str | None = Query(default=None),
    current_state: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OperationalWorkflowOrchestrationService(db)
    return {
        "phase": PHASE_LABEL,
        "instances": await service.list_instances(agency_id=agency_id, workflow_definition_id=workflow_definition_id, entity_type=entity_type, entity_id=entity_id, workflow_status=workflow_status, current_state=current_state),
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.post("/instances/start", status_code=status.HTTP_201_CREATED)
async def start_platform_operational_workflow_instance(
    payload: OperationalWorkflowInstanceStartRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalWorkflowOrchestrationService(db).start_instance(payload, user)
    except OperationalWorkflowOrchestrationError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/instances/{instance_id}")
async def get_platform_operational_workflow_instance(
    instance_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OperationalWorkflowOrchestrationService(db)
    try:
        instance = await service.get_instance(instance_id)
    except OperationalWorkflowOrchestrationError as exc:
        raise bad_request(str(exc)) from exc
    return {"phase": PHASE_LABEL, "workflow_instance": instance, "metadata_only": True, **service.safety_flags()}


@router.get("/instances/{instance_id}/available-transitions")
async def platform_operational_workflow_available_transitions(
    instance_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    try:
        return await OperationalWorkflowOrchestrationService(db).available_transitions(instance_id)
    except OperationalWorkflowOrchestrationError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/instances/{instance_id}/execute-transition")
async def execute_platform_operational_workflow_transition(
    instance_id: str,
    payload: OperationalWorkflowTransitionRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalWorkflowOrchestrationService(db).execute_transition(instance_id, payload, user)
    except OperationalWorkflowOrchestrationError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/instances/{instance_id}/acknowledge-warning")
async def acknowledge_platform_operational_workflow_warning(
    instance_id: str,
    payload: OperationalWorkflowWarningAcknowledgementRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalWorkflowOrchestrationService(db).acknowledge_warnings(instance_id, payload, user)
    except OperationalWorkflowOrchestrationError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/instances/{instance_id}/transitions")
async def list_platform_operational_workflow_transition_history(
    instance_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OperationalWorkflowOrchestrationService(db)
    try:
        transitions = await service.list_transitions(instance_id)
    except OperationalWorkflowOrchestrationError as exc:
        raise bad_request(str(exc)) from exc
    return {"phase": PHASE_LABEL, "transitions": transitions, "immutable_history": True, "metadata_only": True, **service.safety_flags()}


@router.get("/instances/{instance_id}/events")
async def list_platform_operational_workflow_events(
    instance_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OperationalWorkflowOrchestrationService(db)
    try:
        events = await service.list_events(instance_id)
    except OperationalWorkflowOrchestrationError as exc:
        raise bad_request(str(exc)) from exc
    return {"phase": PHASE_LABEL, "events": events, "immutable_history": True, "metadata_only": True, **service.safety_flags()}


@router.get("/entities/{entity_type}/{entity_id}/summary")
async def get_platform_operational_workflow_entity_summary(
    entity_type: str,
    entity_id: str,
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await OperationalWorkflowOrchestrationService(db).entity_summary(agency_id, entity_type, entity_id)
