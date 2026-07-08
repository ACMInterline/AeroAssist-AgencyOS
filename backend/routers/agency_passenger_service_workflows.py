from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.passenger_service_workflow_service import PHASE_LABEL, PassengerServiceWorkflowError, PassengerServiceWorkflowService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/passenger-service-workflows", tags=["agency-passenger-service-workflows"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


@router.get("")
async def list_agency_passenger_service_workflows(
    agency_id: str,
    stage: str | None = Query(default=None),
    readiness: str | None = Query(default=None),
    passenger: str | None = Query(default=None),
    airline: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    assigned_agent: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await PassengerServiceWorkflowService(db).agency_response(
        agency_id,
        stage=stage,
        readiness=readiness,
        passenger=passenger,
        airline=airline,
        priority=priority,
        assigned_agent=assigned_agent,
    )


@router.get("/summary")
async def summarize_agency_passenger_service_workflows(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await PassengerServiceWorkflowService(db).agency_summary(agency_id)


@router.get("/{workflow_id}")
async def get_agency_passenger_service_workflow(
    agency_id: str,
    workflow_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = PassengerServiceWorkflowService(db)
    try:
        passenger_service_workflow = await service.get_agency_workflow(agency_id, workflow_id)
    except PassengerServiceWorkflowError:
        raise not_found("Passenger service workflow metadata not found.")
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "passenger_service_workflow": passenger_service_workflow,
        "read_only": True,
        "metadata_only": True,
        **service.safety_flags(),
    }
