from fastapi import APIRouter, Body, Depends, HTTPException, status

from auth import get_current_user
from database import Database, get_database
from services.operational_workflow_maturity_service import (
    PHASE_LABEL,
    OperationalWorkflowMaturityError,
    OperationalWorkflowMaturityService,
)
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/workflow-maturity", tags=["agency-operational-workflow-maturity"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


@router.get("")
async def get_agency_workflow_maturity(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await OperationalWorkflowMaturityService(db).agency_dashboard(agency_id)


@router.get("/assessment")
async def get_agency_workflow_maturity_assessment(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = OperationalWorkflowMaturityService(db)
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "assessment": await service.assessment(agency_id), **service.safety_flags()}


@router.get("/test-templates")
async def list_agency_workflow_maturity_test_templates(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = OperationalWorkflowMaturityService(db)
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "items": service.test_templates(), **service.safety_flags()}


@router.post("/test-runs")
async def run_agency_workflow_maturity_test(
    agency_id: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    try:
        return await OperationalWorkflowMaturityService(db).run_test_template(str(payload.get("template_code") or ""), agency_id)
    except OperationalWorkflowMaturityError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
