from fastapi import APIRouter, Depends

from auth import get_current_user
from services.blueprint_adoption_service import (
    get_blueprint_adoption_map,
    get_blueprint_gap_summary,
    get_blueprint_route_policy,
    get_next_phase_recommendations,
)
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/blueprint", tags=["platform-blueprint"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor", "platform_support"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


@router.get("/adoption-map")
async def blueprint_adoption_map(user: dict = Depends(get_current_user)) -> dict:
    await require_platform_read(user)
    return get_blueprint_adoption_map()


@router.get("/route-policy")
async def blueprint_route_policy(user: dict = Depends(get_current_user)) -> dict:
    await require_platform_read(user)
    return get_blueprint_route_policy()


@router.get("/gaps")
async def blueprint_gaps(user: dict = Depends(get_current_user)) -> dict:
    await require_platform_read(user)
    return get_blueprint_gap_summary()


@router.get("/next-phases")
async def blueprint_next_phases(user: dict = Depends(get_current_user)) -> dict:
    await require_platform_read(user)
    return get_next_phase_recommendations()
