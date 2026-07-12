from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    OperationalWorkflowInstanceStartRequest,
    OperationalWorkflowTransitionRequest,
    OperationalWorkflowWarningAcknowledgementRequest,
)
from services.operational_workflow_orchestration_service import (
    PHASE_LABEL,
    OperationalWorkflowOrchestrationError,
    OperationalWorkflowOrchestrationService,
)
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/operational-workflows", tags=["agency-operational-workflows"])

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
async def agency_operational_workflows_dashboard(
    agency_id: str,
    entity_type: str | None = Query(default=None),
    entity_id: str | None = Query(default=None),
    workflow_status: str | None = Query(default=None),
    current_state: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await OperationalWorkflowOrchestrationService(db).agency_dashboard(
        agency_id,
        entity_type=entity_type,
        entity_id=entity_id,
        workflow_status=workflow_status,
        current_state=current_state,
    )


@router.get("/summary")
async def agency_operational_workflows_summary(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = OperationalWorkflowOrchestrationService(db)
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "summary": await service.summary(agency_id=agency_id), "metadata_only": True, **service.safety_flags()}


@router.post("/instances/start", status_code=status.HTTP_201_CREATED)
async def start_agency_operational_workflow_instance(
    agency_id: str,
    payload: OperationalWorkflowInstanceStartRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OperationalWorkflowOrchestrationService(db).start_instance(payload, user, agency_id=agency_id)
    except OperationalWorkflowOrchestrationError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/instances/{instance_id}")
async def get_agency_operational_workflow_instance(
    agency_id: str,
    instance_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = OperationalWorkflowOrchestrationService(db)
    try:
        instance = await service.get_instance(instance_id, agency_id=agency_id)
    except OperationalWorkflowOrchestrationError:
        raise not_found("Operational workflow instance metadata not found.")
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "workflow_instance": instance, "metadata_only": True, **service.safety_flags()}


@router.get("/instances/{instance_id}/available-transitions")
async def agency_operational_workflow_available_transitions(
    agency_id: str,
    instance_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    try:
        return await OperationalWorkflowOrchestrationService(db).available_transitions(instance_id, agency_id=agency_id)
    except OperationalWorkflowOrchestrationError:
        raise not_found("Operational workflow instance metadata not found.")


@router.post("/instances/{instance_id}/execute-transition")
async def execute_agency_operational_workflow_transition(
    agency_id: str,
    instance_id: str,
    payload: OperationalWorkflowTransitionRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OperationalWorkflowOrchestrationService(db).execute_transition(instance_id, payload, user, agency_id=agency_id)
    except OperationalWorkflowOrchestrationError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/instances/{instance_id}/acknowledge-warning")
async def acknowledge_agency_operational_workflow_warning(
    agency_id: str,
    instance_id: str,
    payload: OperationalWorkflowWarningAcknowledgementRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OperationalWorkflowOrchestrationService(db).acknowledge_warnings(instance_id, payload, user, agency_id=agency_id)
    except OperationalWorkflowOrchestrationError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/instances/{instance_id}/transitions")
async def list_agency_operational_workflow_transition_history(
    agency_id: str,
    instance_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = OperationalWorkflowOrchestrationService(db)
    try:
        transitions = await service.list_transitions(instance_id, agency_id=agency_id)
    except OperationalWorkflowOrchestrationError:
        raise not_found("Operational workflow instance metadata not found.")
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "transitions": transitions, "immutable_history": True, "metadata_only": True, **service.safety_flags()}


@router.get("/instances/{instance_id}/events")
async def list_agency_operational_workflow_events(
    agency_id: str,
    instance_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = OperationalWorkflowOrchestrationService(db)
    try:
        events = await service.list_events(instance_id, agency_id=agency_id)
    except OperationalWorkflowOrchestrationError:
        raise not_found("Operational workflow instance metadata not found.")
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "events": events, "immutable_history": True, "metadata_only": True, **service.safety_flags()}


@router.get("/instances/{instance_id}/blockers")
async def list_agency_operational_workflow_blockers(
    agency_id: str,
    instance_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = OperationalWorkflowOrchestrationService(db)
    try:
        instance = await service.get_instance(instance_id, agency_id=agency_id)
    except OperationalWorkflowOrchestrationError:
        raise not_found("Operational workflow instance metadata not found.")
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "blockers": instance.get("active_blockers_json") or [], "metadata_only": True, **service.safety_flags()}


@router.get("/instances/{instance_id}/warnings")
async def list_agency_operational_workflow_warnings(
    agency_id: str,
    instance_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = OperationalWorkflowOrchestrationService(db)
    try:
        instance = await service.get_instance(instance_id, agency_id=agency_id)
    except OperationalWorkflowOrchestrationError:
        raise not_found("Operational workflow instance metadata not found.")
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "warnings": instance.get("active_warnings_json") or [], "metadata_only": True, **service.safety_flags()}


@router.get("/entities/{entity_type}/{entity_id}/summary")
async def get_agency_operational_workflow_entity_summary(
    agency_id: str,
    entity_type: str,
    entity_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await OperationalWorkflowOrchestrationService(db).entity_summary(agency_id, entity_type, entity_id)
