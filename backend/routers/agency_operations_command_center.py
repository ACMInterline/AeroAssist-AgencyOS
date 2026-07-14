from fastapi import APIRouter, Depends

from auth import get_current_user
from database import Database, get_database
from services.operations_command_center_service import PHASE_LABEL, OperationsCommandCenterService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/operations-command-center", tags=["agency-operations-command-center"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


@router.get("")
async def get_agency_operations_command_center(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await OperationsCommandCenterService(db).agency_command_center(agency_id)


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
