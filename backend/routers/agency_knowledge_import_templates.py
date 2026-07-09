from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import KnowledgeImportTemplateCreate, KnowledgeImportTemplateUpdate
from services.knowledge_import_template_service import (
    FOUNDATION_PHASE_LABEL,
    PHASE_LABEL,
    KnowledgeImportTemplateError,
    KnowledgeImportTemplateService,
)
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(tags=["agency-knowledge-import-templates"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin", "agency_agent"]
PLATFORM_ROLES = {"platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"}


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in PLATFORM_ROLES:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


async def require_write(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in PLATFORM_ROLES:
        await require_any_agency_role(db, agency_id, user, WRITE_ROLES)


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("/api/agencies/{agency_id}/knowledge-import-templates")
async def list_agency_knowledge_import_templates(
    agency_id: str,
    template_type: str | None = Query(default=None),
    target_knowledge_domain: str | None = Query(default=None),
    target_collection: str | None = Query(default=None),
    import_scope: str | None = Query(default=None),
    review_required: bool | None = Query(default=None),
    accepted_file_type: str | None = Query(default=None),
    search: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await KnowledgeImportTemplateService(db).agency_response(
        agency_id,
        template_type=template_type,
        target_knowledge_domain=target_knowledge_domain,
        target_collection=target_collection,
        import_scope=import_scope,
        review_required=review_required,
        accepted_file_type=accepted_file_type,
        search=search,
        include_archived=include_archived,
    )


@router.get("/api/agencies/{agency_id}/knowledge-import-templates/summary")
async def summarize_agency_knowledge_import_templates(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await KnowledgeImportTemplateService(db).agency_summary(agency_id)


@router.post("/api/agencies/{agency_id}/knowledge-import-templates", status_code=status.HTTP_201_CREATED)
async def create_agency_knowledge_import_template(
    agency_id: str,
    payload: KnowledgeImportTemplateCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await KnowledgeImportTemplateService(db).create_template(payload, user, agency_id=agency_id)
    except KnowledgeImportTemplateError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/api/agencies/{agency_id}/knowledge-import-templates/{template_id}")
async def get_agency_knowledge_import_template(
    agency_id: str,
    template_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = KnowledgeImportTemplateService(db)
    try:
        template = await service.get_template(template_id, agency_id=agency_id)
    except KnowledgeImportTemplateError:
        raise not_found("Knowledge import template metadata not found.")
    return {
        "phase": PHASE_LABEL,
        "foundation_phase": FOUNDATION_PHASE_LABEL,
        "agency_id": agency_id,
        "knowledge_import_template": template,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/api/agencies/{agency_id}/knowledge-import-templates/{template_id}")
async def update_agency_knowledge_import_template(
    agency_id: str,
    template_id: str,
    payload: KnowledgeImportTemplateUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await KnowledgeImportTemplateService(db).update_template(template_id, payload, user, agency_id=agency_id)
    except KnowledgeImportTemplateError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/api/agencies/{agency_id}/knowledge-import-templates/{template_id}")
async def archive_agency_knowledge_import_template(
    agency_id: str,
    template_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await KnowledgeImportTemplateService(db).archive_template(template_id, user, agency_id=agency_id)
    except KnowledgeImportTemplateError as exc:
        raise bad_request(str(exc)) from exc
