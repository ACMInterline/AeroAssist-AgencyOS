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
from services.tenant_service import require_any_platform_role


router = APIRouter(tags=["platform-knowledge-import-templates"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("/api/platform/knowledge-import-templates")
async def list_platform_knowledge_import_templates(
    agency_id: str | None = Query(default=None),
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
    await require_platform_read(user)
    return await KnowledgeImportTemplateService(db).platform_response(
        agency_id=agency_id,
        template_type=template_type,
        target_knowledge_domain=target_knowledge_domain,
        target_collection=target_collection,
        import_scope=import_scope,
        review_required=review_required,
        accepted_file_type=accepted_file_type,
        search=search,
        include_archived=include_archived,
    )


@router.get("/api/platform/knowledge-import-templates/summary")
async def summarize_platform_knowledge_import_templates(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await KnowledgeImportTemplateService(db).platform_summary(agency_id)


@router.post("/api/platform/knowledge-import-templates", status_code=status.HTTP_201_CREATED)
async def create_platform_knowledge_import_template(
    payload: KnowledgeImportTemplateCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await KnowledgeImportTemplateService(db).create_template(payload, user)
    except KnowledgeImportTemplateError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/api/platform/knowledge-import-templates/{template_id}")
async def get_platform_knowledge_import_template(
    template_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = KnowledgeImportTemplateService(db)
    try:
        template = await service.get_template(template_id)
    except KnowledgeImportTemplateError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "foundation_phase": FOUNDATION_PHASE_LABEL,
        "knowledge_import_template": template,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/api/platform/knowledge-import-templates/{template_id}")
async def update_platform_knowledge_import_template(
    template_id: str,
    payload: KnowledgeImportTemplateUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await KnowledgeImportTemplateService(db).update_template(template_id, payload, user)
    except KnowledgeImportTemplateError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/api/platform/knowledge-import-templates/{template_id}")
async def archive_platform_knowledge_import_template(
    template_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await KnowledgeImportTemplateService(db).archive_template(template_id, user)
    except KnowledgeImportTemplateError as exc:
        raise bad_request(str(exc)) from exc
