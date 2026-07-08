from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import EmdWorkspaceCreate, EmdWorkspaceUpdate
from services.emd_workspace_service import PHASE_LABEL, EmdWorkspaceError, EmdWorkspaceService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/emd-workspaces", tags=["platform-emd-workspaces"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_platform_emd_workspaces(
    agency_id: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    emd_type: str | None = Query(default=None),
    emd_a_or_s: str | None = Query(default=None),
    validating_carrier: str | None = Query(default=None),
    passenger: str | None = Query(default=None),
    rfic: str | None = Query(default=None),
    rfisc: str | None = Query(default=None),
    service_category: str | None = Query(default=None),
    issue_date: date | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await EmdWorkspaceService(db).platform_response(
        agency_id=agency_id,
        emd_status=status_filter,
        emd_type=emd_type,
        emd_a_or_s=emd_a_or_s,
        validating_carrier=validating_carrier,
        passenger=passenger,
        rfic=rfic,
        rfisc=rfisc,
        service_category=service_category,
        issue_date=issue_date,
        include_archived=include_archived,
    )


@router.get("/summary")
async def summarize_platform_emd_workspaces(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await EmdWorkspaceService(db).platform_summary()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_platform_emd_workspace(
    payload: EmdWorkspaceCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await EmdWorkspaceService(db).create_emd(payload, user)
    except EmdWorkspaceError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{emd_workspace_id}")
async def get_platform_emd_workspace(
    emd_workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = EmdWorkspaceService(db)
    try:
        emd_workspace = await service.get_platform_emd(emd_workspace_id)
    except EmdWorkspaceError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "emd_workspace": emd_workspace,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{emd_workspace_id}")
async def update_platform_emd_workspace(
    emd_workspace_id: str,
    payload: EmdWorkspaceUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await EmdWorkspaceService(db).update_emd(emd_workspace_id, payload, user)
    except EmdWorkspaceError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/{emd_workspace_id}")
async def delete_platform_emd_workspace(
    emd_workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await EmdWorkspaceService(db).delete_emd(emd_workspace_id, user)
    except EmdWorkspaceError as exc:
        raise bad_request(str(exc)) from exc
