from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import DocumentWorkspaceCreate, DocumentWorkspaceUpdate
from services.document_workspace_service import PHASE_LABEL, DocumentWorkspaceError, DocumentWorkspaceService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/document-workspaces", tags=["platform-document-workspaces"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_platform_document_workspaces(
    agency_id: str | None = Query(default=None),
    document_type: str | None = Query(default=None),
    document_status: str | None = Query(default=None),
    passenger: str | None = Query(default=None),
    booking_reference: str | None = Query(default=None),
    related_service: str | None = Query(default=None),
    required_for_travel: bool | None = Query(default=None),
    verification_status: str | None = Query(default=None),
    deadline: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await DocumentWorkspaceService(db).platform_response(
        agency_id=agency_id,
        document_type=document_type,
        document_status=document_status,
        passenger=passenger,
        booking_reference=booking_reference,
        related_service=related_service,
        required_for_travel=required_for_travel,
        verification_status=verification_status,
        deadline=deadline,
        include_archived=include_archived,
    )


@router.get("/summary")
async def summarize_platform_document_workspaces(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await DocumentWorkspaceService(db).platform_summary()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_platform_document_workspace(
    payload: DocumentWorkspaceCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await DocumentWorkspaceService(db).create_workspace(payload, user)
    except DocumentWorkspaceError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{workspace_id}")
async def get_platform_document_workspace(
    workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = DocumentWorkspaceService(db)
    try:
        document_workspace = await service.get_platform_workspace(workspace_id)
    except DocumentWorkspaceError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "document_workspace": document_workspace,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{workspace_id}")
async def update_platform_document_workspace(
    workspace_id: str,
    payload: DocumentWorkspaceUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await DocumentWorkspaceService(db).update_workspace(workspace_id, payload, user)
    except DocumentWorkspaceError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/{workspace_id}")
async def delete_platform_document_workspace(
    workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await DocumentWorkspaceService(db).delete_workspace(workspace_id, user)
    except DocumentWorkspaceError as exc:
        raise bad_request(str(exc)) from exc
