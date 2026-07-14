from fastapi import APIRouter, Depends

from auth import get_current_user
from database import Database, get_database
from services.operations_command_center_service import PHASE_LABEL, OperationsCommandCenterService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/operations-governance", tags=["platform-operations-governance"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


@router.get("")
async def get_platform_operations_governance(
    agency_id: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await OperationsCommandCenterService(db).platform_dashboard(agency_id=agency_id)


@router.get("/summary")
async def summarize_platform_operations_governance(
    agency_id: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OperationsCommandCenterService(db)
    return {"phase": PHASE_LABEL, "summary": await service.summary(agency_id=agency_id), "platform_read_only_governance": True, **service.safety_flags()}


@router.get("/feed")
async def list_platform_operations_feed(
    agency_id: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OperationsCommandCenterService(db)
    return {"phase": PHASE_LABEL, "items": await service.operational_feed(agency_id=agency_id, platform=True), "platform_read_only_governance": True, **service.safety_flags()}


@router.get("/calendar")
async def list_platform_operations_calendar(
    agency_id: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OperationsCommandCenterService(db)
    return {"phase": PHASE_LABEL, "events": await service.calendar_events(agency_id=agency_id), "platform_read_only_governance": True, **service.safety_flags()}


@router.get("/kanban")
async def list_platform_operations_kanban(
    agency_id: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OperationsCommandCenterService(db)
    return {"phase": PHASE_LABEL, "lanes": await service.kanban_lanes(agency_id=agency_id, platform=True), "guard_enforcement": True, "platform_read_only_governance": True, **service.safety_flags()}


@router.get("/workload")
async def list_platform_operations_workload(
    agency_id: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OperationsCommandCenterService(db)
    return {"phase": PHASE_LABEL, "items": await service.team_workload(agency_id=agency_id), "platform_read_only_governance": True, **service.safety_flags()}
