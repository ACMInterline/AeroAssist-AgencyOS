from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.document_workspace_service import PHASE_LABEL, DocumentWorkspaceError, DocumentWorkspaceService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/document-workspaces", tags=["agency-document-workspaces"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


@router.get("")
async def list_agency_document_workspaces(
    agency_id: str,
    document_type: str | None = Query(default=None),
    document_status: str | None = Query(default=None),
    passenger: str | None = Query(default=None),
    booking_reference: str | None = Query(default=None),
    related_service: str | None = Query(default=None),
    required_for_travel: bool | None = Query(default=None),
    verification_status: str | None = Query(default=None),
    deadline: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await DocumentWorkspaceService(db).agency_response(
        agency_id,
        document_type=document_type,
        document_status=document_status,
        passenger=passenger,
        booking_reference=booking_reference,
        related_service=related_service,
        required_for_travel=required_for_travel,
        verification_status=verification_status,
        deadline=deadline,
    )


@router.get("/summary")
async def summarize_agency_document_workspaces(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await DocumentWorkspaceService(db).agency_summary(agency_id)


@router.get("/{workspace_id}")
async def get_agency_document_workspace(
    agency_id: str,
    workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = DocumentWorkspaceService(db)
    try:
        document_workspace = await service.get_agency_workspace(agency_id, workspace_id)
    except DocumentWorkspaceError:
        raise not_found("Document workspace metadata not found.")
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "document_workspace": document_workspace,
        "read_only": True,
        "metadata_only": True,
        **service.safety_flags(),
    }
