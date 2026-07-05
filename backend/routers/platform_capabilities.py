from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from auth import get_current_user
from database import Database, get_database
from services.capability_catalog_service import CapabilityCatalogService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/capabilities", tags=["platform-capabilities"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


@router.get("")
async def list_platform_capabilities(
    category: str | None = Query(default=None),
    module: str | None = Query(default=None),
    status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await CapabilityCatalogService(db).platform_capabilities_response(
        category=category,
        module=module,
        status=status,
    )


@router.get("/categories")
async def list_platform_capability_categories(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await CapabilityCatalogService(db).platform_categories_response()


@router.get("/modules")
async def list_platform_capability_modules(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await CapabilityCatalogService(db).platform_modules_response()


@router.get("/{code}")
async def get_platform_capability(
    code: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await CapabilityCatalogService(db).platform_capability_detail_response(code)
