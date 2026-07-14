from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.operational_workflow_maturity_service import (
    PHASE_LABEL,
    OperationalWorkflowMaturityError,
    OperationalWorkflowMaturityService,
)
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/workflow-maturity", tags=["platform-operational-workflow-maturity"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


@router.get("")
async def get_platform_workflow_maturity(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await OperationalWorkflowMaturityService(db).platform_dashboard(agency_id)


@router.get("/assessment")
async def get_platform_workflow_maturity_assessment(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OperationalWorkflowMaturityService(db)
    return {"phase": PHASE_LABEL, "assessment": await service.assessment(agency_id), **service.safety_flags()}


@router.get("/test-templates")
async def list_platform_workflow_maturity_test_templates(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OperationalWorkflowMaturityService(db)
    return {"phase": PHASE_LABEL, "items": service.test_templates(), **service.safety_flags()}


@router.post("/test-runs")
async def run_platform_workflow_maturity_test(
    payload: dict = Body(...),
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    try:
        return await OperationalWorkflowMaturityService(db).run_test_template(str(payload.get("template_code") or ""), agency_id)
    except OperationalWorkflowMaturityError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
