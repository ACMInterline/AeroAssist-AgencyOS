from fastapi import APIRouter, Depends, Query

from auth import get_current_user
from database import Database, get_database
from services.after_sales_workflow_service import PHASE_LABEL, AfterSalesWorkflowService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/after-sales", tags=["platform-after-sales-workflows"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


@router.get("")
async def list_platform_after_sales_cases(
    agency_id: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    case_type: str | None = None,
    case_priority: str | None = None,
    trip_workspace_id: str | None = None,
    booking_workspace_id: str | None = None,
    ticket_workspace_id: str | None = None,
    emd_workspace_id: str | None = None,
    assigned_agent: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AfterSalesWorkflowService(db).platform_dashboard(
        agency_id=agency_id,
        case_status=status_filter,
        case_type=case_type,
        case_priority=case_priority,
        trip_workspace_id=trip_workspace_id,
        booking_workspace_id=booking_workspace_id,
        ticket_workspace_id=ticket_workspace_id,
        emd_workspace_id=emd_workspace_id,
        assigned_agent=assigned_agent,
    )


@router.get("/summary")
async def summarize_platform_after_sales_cases(
    agency_id: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = AfterSalesWorkflowService(db)
    return {"phase": PHASE_LABEL, "summary": await service.summary(agency_id=agency_id), "platform_read_only_diagnostics": True, **service.safety_flags()}


@router.get("/items")
async def list_platform_after_sales_items(
    agency_id: str | None = None,
    case_id: str | None = None,
    item_type: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = AfterSalesWorkflowService(db)
    return {"phase": PHASE_LABEL, "items": await service.list_case_items(agency_id=agency_id, case_id=case_id, item_type=item_type), "platform_read_only_diagnostics": True, **service.safety_flags()}


@router.get("/decisions")
async def list_platform_after_sales_decisions(
    agency_id: str | None = None,
    case_id: str | None = None,
    decision_status: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = AfterSalesWorkflowService(db)
    return {"phase": PHASE_LABEL, "items": await service.list_decisions(agency_id=agency_id, case_id=case_id, decision_status=decision_status), "platform_read_only_diagnostics": True, **service.safety_flags()}


@router.get("/financial-impacts")
async def list_platform_after_sales_financial_impacts(
    agency_id: str | None = None,
    case_id: str | None = None,
    impact_type: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = AfterSalesWorkflowService(db)
    return {"phase": PHASE_LABEL, "items": await service.list_financial_impacts(agency_id=agency_id, case_id=case_id, impact_type=impact_type), "platform_read_only_diagnostics": True, **service.safety_flags()}


@router.get("/resolutions")
async def list_platform_after_sales_resolutions(
    agency_id: str | None = None,
    case_id: str | None = None,
    resolution_status: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = AfterSalesWorkflowService(db)
    return {"phase": PHASE_LABEL, "items": await service.list_resolutions(agency_id=agency_id, case_id=case_id, resolution_status=resolution_status), "platform_read_only_diagnostics": True, **service.safety_flags()}


@router.get("/communications")
async def list_platform_after_sales_communications(
    agency_id: str | None = None,
    case_id: str | None = None,
    communication_type: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = AfterSalesWorkflowService(db)
    return {"phase": PHASE_LABEL, "items": await service.list_communications(agency_id=agency_id, case_id=case_id, communication_type=communication_type), "platform_read_only_diagnostics": True, **service.safety_flags()}


@router.get("/{case_id}")
async def get_platform_after_sales_case(
    case_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = AfterSalesWorkflowService(db)
    return {"phase": PHASE_LABEL, "case": await service.get_case(case_id), "platform_read_only_diagnostics": True, **service.safety_flags()}
