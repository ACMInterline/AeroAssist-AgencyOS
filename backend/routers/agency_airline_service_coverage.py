from fastapi import APIRouter, Depends, Query

from auth import get_current_user
from database import Database, get_database
from services.airline_service_coverage_gap_service import PHASE_LABEL, AirlineServiceCoverageGapService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/airline-service-coverage", tags=["agency-airline-service-coverage"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


@router.get("")
async def get_agency_airline_service_coverage(
    agency_id: str,
    airline_code: str | None = Query(default=None),
    service_family: str | None = Query(default=None),
    service_code: str | None = Query(default=None),
    coverage_status: str | None = Query(default=None),
    route_type: str | None = Query(default=None),
    flight_type: str | None = Query(default=None),
    cabin: str | None = Query(default=None),
    fare_bundle: str | None = Query(default=None),
    distribution_channel: str | None = Query(default=None),
    evidence_freshness: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await AirlineServiceCoverageGapService(db).agency_response(
        agency_id,
        airline_code=airline_code,
        service_family=service_family,
        service_code=service_code,
        coverage_status=coverage_status,
        route_type=route_type,
        flight_type=flight_type,
        cabin=cabin,
        fare_bundle=fare_bundle,
        distribution_channel=distribution_channel,
        evidence_freshness=evidence_freshness,
    )


@router.get("/summary")
async def summarize_agency_airline_service_coverage(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    response = await AirlineServiceCoverageGapService(db).agency_response(agency_id)
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "summary": response["summary"],
        "warnings": response["warnings"],
        "read_only": True,
        **AirlineServiceCoverageGapService(db).safety_flags(),
    }
