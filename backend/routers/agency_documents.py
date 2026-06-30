from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    DocumentContextPreviewRequest,
    DocumentPackageCreate,
    DocumentRenderJobCreate,
    DocumentShareRecordCreate,
)
from services.document_context_service import DocumentContextService
from services.document_render_service import DocumentRenderService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/documents", tags=["agency-document-foundation"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


async def require_write(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin"}:
        await require_any_agency_role(db, agency_id, user, WRITE_ROLES)


def filters_from(**kwargs: Any) -> dict[str, Any]:
    return {key: value for key, value in kwargs.items() if value not in {None, ""}}


@router.get("/templates")
async def list_document_templates(
    agency_id: str,
    template_key: str | None = None,
    template_type: str | None = None,
    document_type: str | None = None,
    scope: str | None = None,
    active: bool | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = DocumentRenderService(db)
    await service.seed_default_templates()
    return await service.list_templates(
        agency_id,
        filters_from(template_key=template_key, template_type=template_type, document_type=document_type, scope=scope, active=active),
    )


@router.get("/templates/{template_id}")
async def get_document_template(
    agency_id: str,
    template_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    template = await DocumentRenderService(db).get_template(agency_id, template_id)
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document template not found.")
    return {"template": template}


@router.get("/render-jobs")
async def list_render_jobs(
    agency_id: str,
    document_type: str | None = None,
    source_context_type: str | None = None,
    source_context_id: str | None = None,
    render_status: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await DocumentRenderService(db).list_render_jobs(
        agency_id,
        filters_from(document_type=document_type, source_context_type=source_context_type, source_context_id=source_context_id, render_status=render_status),
    )


@router.post("/render-jobs", status_code=status.HTTP_201_CREATED)
async def create_render_job(
    agency_id: str,
    payload: DocumentRenderJobCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    service = DocumentRenderService(db)
    await service.seed_default_templates()
    return await service.render_document(agency_id, payload, user)


@router.get("/render-jobs/{render_job_id}")
async def get_render_job(
    agency_id: str,
    render_job_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    job = await DocumentRenderService(db).get_render_job(agency_id, render_job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document render job not found.")
    return {"render_job": job, "live_delivery_disabled": True, "pdf_export_required": False}


@router.post("/render-jobs/{render_job_id}/rerender")
async def rerender_job(
    agency_id: str,
    render_job_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    result = await DocumentRenderService(db).rerender_document(agency_id, render_job_id, user)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document render job not found.")
    return result


@router.get("/packages")
async def list_document_packages(
    agency_id: str,
    package_type: str | None = None,
    source_context_type: str | None = None,
    source_context_id: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await DocumentRenderService(db).list_document_packages(
        agency_id,
        filters_from(package_type=package_type, source_context_type=source_context_type, source_context_id=source_context_id, status=status_filter),
    )


@router.post("/packages", status_code=status.HTTP_201_CREATED)
async def create_document_package(
    agency_id: str,
    payload: DocumentPackageCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    return await DocumentRenderService(db).create_document_package(agency_id, payload, user)


@router.get("/packages/{package_id}")
async def get_document_package(
    agency_id: str,
    package_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    result = await DocumentRenderService(db).get_document_package(agency_id, package_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document package not found.")
    return result


@router.post("/share-records", status_code=status.HTTP_201_CREATED)
async def create_share_record(
    agency_id: str,
    payload: DocumentShareRecordCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    if not payload.document_render_job_id and not payload.document_package_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Render job or package is required.")
    return await DocumentRenderService(db).create_share_record(agency_id, payload, user)


@router.post("/context-preview")
async def context_preview(
    agency_id: str,
    payload: DocumentContextPreviewRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    context = await DocumentContextService(db).build_context_by_type(
        agency_id,
        payload.source_context_type,
        payload.source_context_id,
        payload.source_context_ids_json,
    )
    if context is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source context not found.")
    return {"context": context, "warnings": context.get("warnings_json") or []}
