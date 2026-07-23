from fastapi import APIRouter, Depends, Query

from auth import get_current_user
from database import Database, get_database
from services.operations_command_center_service import PHASE_LABEL, OperationsCommandCenterService
from services.commercial_pilot_operations_command_centre_service import CommercialPilotOperationsCommandCentreService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/operations-command-center", tags=["agency-operations-command-center"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_read(db: Database, agency_id: str, user: dict) -> dict | None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        return await require_any_agency_role(db, agency_id, user, READ_ROLES)
    return None


@router.get("")
async def get_agency_operations_command_center(
    agency_id: str,
    assignment: str | None = Query(default=None),
    urgency: str | None = Query(default=None),
    work_type: str | None = Query(default=None),
    assignee_id: str | None = Query(default=None),
    due_period: str | None = Query(default=None),
    selected_date: str | None = Query(default=None, alias="date"),
    limit: int = Query(default=50, ge=1, le=50),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    membership = await require_read(db, agency_id, user)
    return await CommercialPilotOperationsCommandCentreService(db).agency_home(
        agency_id,
        user,
        membership,
        assignment=assignment,
        urgency=urgency,
        work_type=work_type,
        assignee_id=assignee_id,
        due_period=due_period,
        selected_date=selected_date,
        limit=limit,
    )


@router.get("/summary")
async def summarize_agency_operations_command_center(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = OperationsCommandCenterService(db)
    return {"phase": PHASE_LABEL, "summary": await service.summary(agency_id=agency_id), **service.safety_flags()}


@router.get("/feed")
async def list_agency_operations_feed(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = OperationsCommandCenterService(db)
    return {"phase": PHASE_LABEL, "items": await service.operational_feed(agency_id=agency_id), **service.safety_flags()}


@router.get("/calendar")
async def list_agency_operations_calendar(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = OperationsCommandCenterService(db)
    return {"phase": PHASE_LABEL, "events": await service.calendar_events(agency_id=agency_id), **service.safety_flags()}


@router.get("/kanban")
async def list_agency_operations_kanban(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = OperationsCommandCenterService(db)
    return {"phase": PHASE_LABEL, "lanes": await service.kanban_lanes(agency_id=agency_id), "guard_enforcement": True, **service.safety_flags()}


@router.get("/workload")
async def list_agency_operations_workload(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = OperationsCommandCenterService(db)
    return {"phase": PHASE_LABEL, "items": await service.team_workload(agency_id=agency_id), **service.safety_flags()}
