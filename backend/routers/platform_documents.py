from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from auth import get_current_user
from database import Database, get_database
from services.document_render_service import DocumentRenderService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/documents", tags=["platform-document-foundation"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


@router.get("/templates")
async def list_platform_document_templates(
    template_type: str | None = None,
    active: bool | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = DocumentRenderService(db)
    await service.seed_default_templates()
    return await service.list_templates("platform", {"scope": "platform", "template_type": template_type, "active": active})


@router.post("/templates/seed-defaults", status_code=status.HTTP_201_CREATED)
async def seed_platform_document_templates(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    result = await DocumentRenderService(db).seed_default_templates()
    return {**result, "default_document_templates_enabled": True}
