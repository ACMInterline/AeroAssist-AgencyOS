from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.emd_workspace_service import PHASE_LABEL, EmdWorkspaceError, EmdWorkspaceService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/emd-workspaces", tags=["agency-emd-workspaces"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


@router.get("")
async def list_agency_emd_workspaces(
    agency_id: str,
    status_filter: str | None = Query(default=None, alias="status"),
    emd_type: str | None = Query(default=None),
    emd_a_or_s: str | None = Query(default=None),
    validating_carrier: str | None = Query(default=None),
    passenger: str | None = Query(default=None),
    rfic: str | None = Query(default=None),
    rfisc: str | None = Query(default=None),
    service_category: str | None = Query(default=None),
    issue_date: date | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await EmdWorkspaceService(db).agency_response(
        agency_id,
        emd_status=status_filter,
        emd_type=emd_type,
        emd_a_or_s=emd_a_or_s,
        validating_carrier=validating_carrier,
        passenger=passenger,
        rfic=rfic,
        rfisc=rfisc,
        service_category=service_category,
        issue_date=issue_date,
    )


@router.get("/summary")
async def summarize_agency_emd_workspaces(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await EmdWorkspaceService(db).agency_summary(agency_id)


@router.get("/{emd_workspace_id}")
async def get_agency_emd_workspace(
    agency_id: str,
    emd_workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = EmdWorkspaceService(db)
    try:
        emd_workspace = await service.get_agency_emd(agency_id, emd_workspace_id)
    except EmdWorkspaceError:
        raise not_found("EMD workspace metadata not found.")
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "emd_workspace": emd_workspace,
        "read_only": True,
        "metadata_only": True,
        **service.safety_flags(),
    }
