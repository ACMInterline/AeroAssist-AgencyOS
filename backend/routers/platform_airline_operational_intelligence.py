from fastapi import APIRouter, Depends

from auth import get_current_user
from database import Database, get_database
from services.airline_operational_intelligence_service import PHASE_LABEL, AirlineOperationalIntelligenceService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/airline-operational-intelligence", tags=["platform-airline-operational-intelligence"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor", "platform_support"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


@router.get("")
async def get_platform_airline_operational_intelligence(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AirlineOperationalIntelligenceService(db).platform_response()


@router.get("/summary")
async def summarize_platform_airline_operational_intelligence(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AirlineOperationalIntelligenceService(db).summary()


@router.get("/architecture")
async def get_platform_airline_operational_intelligence_architecture(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = AirlineOperationalIntelligenceService(db)
    return {
        "phase": PHASE_LABEL,
        "architecture": await service.get_architecture(),
        "read_only": True,
        "metadata_only": True,
        "architecture_only": True,
        **service.safety_flags(),
    }
