from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import PassengerServiceWorkflowCreate, PassengerServiceWorkflowUpdate
from services.passenger_service_workflow_service import PHASE_LABEL, PassengerServiceWorkflowError, PassengerServiceWorkflowService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/passenger-service-workflows", tags=["platform-passenger-service-workflows"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_platform_passenger_service_workflows(
    agency_id: str | None = Query(default=None),
    stage: str | None = Query(default=None),
    readiness: str | None = Query(default=None),
    passenger: str | None = Query(default=None),
    airline: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    assigned_agent: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await PassengerServiceWorkflowService(db).platform_response(
        agency_id=agency_id,
        stage=stage,
        readiness=readiness,
        passenger=passenger,
        airline=airline,
        priority=priority,
        assigned_agent=assigned_agent,
        include_archived=include_archived,
    )


@router.get("/summary")
async def summarize_platform_passenger_service_workflows(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await PassengerServiceWorkflowService(db).platform_summary()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_platform_passenger_service_workflow(
    payload: PassengerServiceWorkflowCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await PassengerServiceWorkflowService(db).create_workflow(payload, user)
    except PassengerServiceWorkflowError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{workflow_id}")
async def get_platform_passenger_service_workflow(
    workflow_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = PassengerServiceWorkflowService(db)
    try:
        passenger_service_workflow = await service.get_platform_workflow(workflow_id)
    except PassengerServiceWorkflowError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "passenger_service_workflow": passenger_service_workflow,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{workflow_id}")
async def update_platform_passenger_service_workflow(
    workflow_id: str,
    payload: PassengerServiceWorkflowUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await PassengerServiceWorkflowService(db).update_workflow(workflow_id, payload, user)
    except PassengerServiceWorkflowError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/{workflow_id}")
async def delete_platform_passenger_service_workflow(
    workflow_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await PassengerServiceWorkflowService(db).delete_workflow(workflow_id, user)
    except PassengerServiceWorkflowError as exc:
        raise bad_request(str(exc)) from exc
