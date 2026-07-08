from fastapi import APIRouter, Depends

from auth import get_current_user
from database import Database, get_database
from services.airline_operational_intelligence_service import PHASE_LABEL, AirlineOperationalIntelligenceService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/airline-operational-intelligence", tags=["agency-airline-operational-intelligence"])

AGENCY_READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_agency_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, AGENCY_READ_ROLES)


@router.get("")
async def get_agency_airline_operational_intelligence(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return await AirlineOperationalIntelligenceService(db).agency_response(agency_id)


@router.get("/summary")
async def summarize_agency_airline_operational_intelligence(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    return await AirlineOperationalIntelligenceService(db).summary()


@router.get("/architecture")
async def get_agency_airline_operational_intelligence_architecture(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_agency_read(db, agency_id, user)
    service = AirlineOperationalIntelligenceService(db)
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "architecture": await service.get_architecture(),
        "read_only": True,
        "metadata_only": True,
        "architecture_only": True,
        **service.safety_flags(),
    }
