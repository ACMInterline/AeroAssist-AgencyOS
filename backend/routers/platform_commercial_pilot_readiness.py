from fastapi import APIRouter, Depends, Query

from auth import get_current_user
from database import Database, get_database
from services.commercial_pilot_readiness_service import CommercialPilotReadinessService
from services.tenant_service import require_any_platform_role


router = APIRouter(
    prefix="/api/platform/commercial-pilot-readiness",
    tags=["platform-commercial-pilot-readiness"],
)
READ_ROLES = ["platform_owner", "platform_admin", "platform_support"]


@router.get("")
async def get_commercial_pilot_readiness(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_any_platform_role(user, READ_ROLES)
    return await CommercialPilotReadinessService(db).assess(agency_id=agency_id)
