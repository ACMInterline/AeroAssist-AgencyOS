from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.ssr_osi_workspace_service import PHASE_LABEL, SsrOsiWorkspaceError, SsrOsiWorkspaceService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/ssr-osi-workspaces", tags=["agency-ssr-osi-workspaces"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


@router.get("")
async def list_agency_ssr_osi_workspaces(
    agency_id: str,
    need_category: str | None = Query(default=None),
    airline: str | None = Query(default=None),
    approval_status: str | None = Query(default=None),
    readiness_status: str | None = Query(default=None),
    passenger: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    rfic: str | None = Query(default=None),
    rfisc: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await SsrOsiWorkspaceService(db).agency_response(
        agency_id,
        need_category=need_category,
        airline=airline,
        approval_status=approval_status,
        readiness_status=readiness_status,
        passenger=passenger,
        priority=priority,
        rfic=rfic,
        rfisc=rfisc,
    )


@router.get("/summary")
async def summarize_agency_ssr_osi_workspaces(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await SsrOsiWorkspaceService(db).agency_summary(agency_id)


@router.get("/{workspace_id}")
async def get_agency_ssr_osi_workspace(
    agency_id: str,
    workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = SsrOsiWorkspaceService(db)
    try:
        ssr_osi_workspace = await service.get_agency_workspace(agency_id, workspace_id)
    except SsrOsiWorkspaceError:
        raise not_found("SSR / OSI workspace metadata not found.")
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "ssr_osi_workspace": ssr_osi_workspace,
        "read_only": True,
        "metadata_only": True,
        **service.safety_flags(),
    }
