from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    AfterSalesCaseCreate,
    AfterSalesCaseItemCreate,
    AfterSalesCaseUpdate,
    AfterSalesCommunicationRecordCreate,
    AfterSalesDecisionCreate,
    AfterSalesFinancialImpactCreate,
    AfterSalesResolutionCreate,
)
from services.after_sales_workflow_service import PHASE_LABEL, AfterSalesWorkflowError, AfterSalesWorkflowService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/after-sales", tags=["agency-after-sales-workflows"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin", "agency_agent"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


async def require_write(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin"}:
        await require_any_agency_role(db, agency_id, user, WRITE_ROLES)


def bad_request(exc: AfterSalesWorkflowError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


def not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="After-sales workflow metadata was not found.")


@router.get("")
async def list_agency_after_sales_cases(
    agency_id: str,
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
    await require_read(db, agency_id, user)
    return await AfterSalesWorkflowService(db).agency_dashboard(
        agency_id,
        case_status=status_filter,
        case_type=case_type,
        case_priority=case_priority,
        trip_workspace_id=trip_workspace_id,
        booking_workspace_id=booking_workspace_id,
        ticket_workspace_id=ticket_workspace_id,
        emd_workspace_id=emd_workspace_id,
        assigned_agent=assigned_agent,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_agency_after_sales_case(
    agency_id: str,
    payload: AfterSalesCaseCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await AfterSalesWorkflowService(db).create_case(payload, user, agency_id=agency_id)
    except AfterSalesWorkflowError as exc:
        raise bad_request(exc)


@router.get("/summary")
async def summarize_agency_after_sales_cases(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AfterSalesWorkflowService(db)
    return {"phase": PHASE_LABEL, "summary": await service.summary(agency_id=agency_id), **service.safety_flags()}


@router.get("/link-options")
async def list_agency_after_sales_link_options(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await AfterSalesWorkflowService(db).link_options(agency_id)


@router.get("/{case_id}")
async def get_agency_after_sales_case(
    agency_id: str,
    case_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    try:
        return {"phase": PHASE_LABEL, "case": await AfterSalesWorkflowService(db).get_case(case_id, agency_id=agency_id), "metadata_only": True}
    except AfterSalesWorkflowError:
        raise not_found()


@router.put("/{case_id}")
async def update_agency_after_sales_case(
    agency_id: str,
    case_id: str,
    payload: AfterSalesCaseUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await AfterSalesWorkflowService(db).update_case(case_id, payload, user, agency_id=agency_id)
    except AfterSalesWorkflowError as exc:
        raise bad_request(exc)


@router.get("/{case_id}/items")
async def list_agency_after_sales_items(
    agency_id: str,
    case_id: str,
    item_type: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AfterSalesWorkflowService(db)
    return {"phase": PHASE_LABEL, "items": await service.list_case_items(agency_id=agency_id, case_id=case_id, item_type=item_type), **service.safety_flags()}


@router.post("/{case_id}/items", status_code=status.HTTP_201_CREATED)
async def create_agency_after_sales_item(
    agency_id: str,
    case_id: str,
    payload: AfterSalesCaseItemCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await AfterSalesWorkflowService(db).create_case_item(case_id, payload, user, agency_id=agency_id)
    except AfterSalesWorkflowError as exc:
        raise bad_request(exc)


@router.get("/{case_id}/decisions")
async def list_agency_after_sales_decisions(
    agency_id: str,
    case_id: str,
    decision_status: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AfterSalesWorkflowService(db)
    return {"phase": PHASE_LABEL, "items": await service.list_decisions(agency_id=agency_id, case_id=case_id, decision_status=decision_status), **service.safety_flags()}


@router.post("/{case_id}/decisions", status_code=status.HTTP_201_CREATED)
async def create_agency_after_sales_decision(
    agency_id: str,
    case_id: str,
    payload: AfterSalesDecisionCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await AfterSalesWorkflowService(db).create_decision(case_id, payload, user, agency_id=agency_id)
    except AfterSalesWorkflowError as exc:
        raise bad_request(exc)


@router.get("/{case_id}/financial-impacts")
async def list_agency_after_sales_financial_impacts(
    agency_id: str,
    case_id: str,
    impact_type: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AfterSalesWorkflowService(db)
    return {"phase": PHASE_LABEL, "items": await service.list_financial_impacts(agency_id=agency_id, case_id=case_id, impact_type=impact_type), **service.safety_flags()}


@router.post("/{case_id}/financial-impacts", status_code=status.HTTP_201_CREATED)
async def create_agency_after_sales_financial_impact(
    agency_id: str,
    case_id: str,
    payload: AfterSalesFinancialImpactCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await AfterSalesWorkflowService(db).create_financial_impact(case_id, payload, user, agency_id=agency_id)
    except AfterSalesWorkflowError as exc:
        raise bad_request(exc)


@router.get("/{case_id}/resolutions")
async def list_agency_after_sales_resolutions(
    agency_id: str,
    case_id: str,
    resolution_status: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AfterSalesWorkflowService(db)
    return {"phase": PHASE_LABEL, "items": await service.list_resolutions(agency_id=agency_id, case_id=case_id, resolution_status=resolution_status), **service.safety_flags()}


@router.post("/{case_id}/resolutions", status_code=status.HTTP_201_CREATED)
async def create_agency_after_sales_resolution(
    agency_id: str,
    case_id: str,
    payload: AfterSalesResolutionCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await AfterSalesWorkflowService(db).create_resolution(case_id, payload, user, agency_id=agency_id)
    except AfterSalesWorkflowError as exc:
        raise bad_request(exc)


@router.get("/{case_id}/communications")
async def list_agency_after_sales_communications(
    agency_id: str,
    case_id: str,
    communication_type: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AfterSalesWorkflowService(db)
    return {"phase": PHASE_LABEL, "items": await service.list_communications(agency_id=agency_id, case_id=case_id, communication_type=communication_type), **service.safety_flags()}


@router.post("/{case_id}/communications", status_code=status.HTTP_201_CREATED)
async def create_agency_after_sales_communication(
    agency_id: str,
    case_id: str,
    payload: AfterSalesCommunicationRecordCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await AfterSalesWorkflowService(db).create_communication(case_id, payload, user, agency_id=agency_id)
    except AfterSalesWorkflowError as exc:
        raise bad_request(exc)
