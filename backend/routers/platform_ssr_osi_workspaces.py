from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import SsrOsiWorkspaceCreate, SsrOsiWorkspaceUpdate
from services.ssr_osi_workspace_service import PHASE_LABEL, SsrOsiWorkspaceError, SsrOsiWorkspaceService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/ssr-osi-workspaces", tags=["platform-ssr-osi-workspaces"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_platform_ssr_osi_workspaces(
    agency_id: str | None = Query(default=None),
    need_category: str | None = Query(default=None),
    airline: str | None = Query(default=None),
    approval_status: str | None = Query(default=None),
    readiness_status: str | None = Query(default=None),
    passenger: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    rfic: str | None = Query(default=None),
    rfisc: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await SsrOsiWorkspaceService(db).platform_response(
        agency_id=agency_id,
        need_category=need_category,
        airline=airline,
        approval_status=approval_status,
        readiness_status=readiness_status,
        passenger=passenger,
        priority=priority,
        rfic=rfic,
        rfisc=rfisc,
        include_archived=include_archived,
    )


@router.get("/summary")
async def summarize_platform_ssr_osi_workspaces(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await SsrOsiWorkspaceService(db).platform_summary()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_platform_ssr_osi_workspace(
    payload: SsrOsiWorkspaceCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await SsrOsiWorkspaceService(db).create_workspace(payload, user)
    except SsrOsiWorkspaceError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{workspace_id}")
async def get_platform_ssr_osi_workspace(
    workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = SsrOsiWorkspaceService(db)
    try:
        ssr_osi_workspace = await service.get_platform_workspace(workspace_id)
    except SsrOsiWorkspaceError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "ssr_osi_workspace": ssr_osi_workspace,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{workspace_id}")
async def update_platform_ssr_osi_workspace(
    workspace_id: str,
    payload: SsrOsiWorkspaceUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await SsrOsiWorkspaceService(db).update_workspace(workspace_id, payload, user)
    except SsrOsiWorkspaceError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/{workspace_id}")
async def delete_platform_ssr_osi_workspace(
    workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await SsrOsiWorkspaceService(db).delete_workspace(workspace_id, user)
    except SsrOsiWorkspaceError as exc:
        raise bad_request(str(exc)) from exc
