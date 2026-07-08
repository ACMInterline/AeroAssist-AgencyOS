from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.airline_knowledge_acquisition_service import PHASE_LABEL, AirlineKnowledgeAcquisitionError, AirlineKnowledgeAcquisitionService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/airline-knowledge-acquisition", tags=["agency-airline-knowledge-acquisition"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


@router.get("")
async def list_agency_airline_knowledge_acquisitions(
    agency_id: str,
    airline: str | None = Query(default=None),
    service_domain: str | None = Query(default=None),
    service_family: str | None = Query(default=None),
    ssr_code: str | None = Query(default=None),
    rfic: str | None = Query(default=None),
    rfisc: str | None = Query(default=None),
    source_type: str | None = Query(default=None),
    review_status: str | None = Query(default=None),
    approval_status: str | None = Query(default=None),
    effective_date: str | None = Query(default=None),
    official_source_flag: bool | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await AirlineKnowledgeAcquisitionService(db).agency_response(
        agency_id,
        airline=airline,
        service_domain=service_domain,
        service_family=service_family,
        ssr_code=ssr_code,
        rfic=rfic,
        rfisc=rfisc,
        source_type=source_type,
        review_status=review_status,
        approval_status=approval_status,
        effective_date=effective_date,
        official_source_flag=official_source_flag,
    )


@router.get("/summary")
async def summarize_agency_airline_knowledge_acquisitions(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await AirlineKnowledgeAcquisitionService(db).agency_summary(agency_id)


@router.get("/{acquisition_id}")
async def get_agency_airline_knowledge_acquisition(
    agency_id: str,
    acquisition_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AirlineKnowledgeAcquisitionService(db)
    try:
        acquisition = await service.get_agency_acquisition(agency_id, acquisition_id)
    except AirlineKnowledgeAcquisitionError:
        raise not_found("Airline knowledge acquisition metadata not found.")
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "airline_knowledge_acquisition": acquisition,
        "read_only": True,
        "metadata_only": True,
        **service.safety_flags(),
    }
