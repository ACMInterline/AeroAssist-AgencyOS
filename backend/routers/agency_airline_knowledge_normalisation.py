from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.airline_knowledge_normalisation_service import PHASE_LABEL, AirlineKnowledgeNormalisationError, AirlineKnowledgeNormalisationService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/airline-knowledge-normalisation", tags=["agency-airline-knowledge-normalisation"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


@router.get("")
async def list_agency_airline_knowledge_normalisations(
    agency_id: str,
    normalisation_status: str | None = Query(default=None),
    normalisation_type: str | None = Query(default=None),
    canonical_code: str | None = Query(default=None),
    taxonomy_domain: str | None = Query(default=None),
    taxonomy_family: str | None = Query(default=None),
    taxonomy_variant: str | None = Query(default=None),
    airline: str | None = Query(default=None),
    ssr_code: str | None = Query(default=None),
    rfic: str | None = Query(default=None),
    rfisc: str | None = Query(default=None),
    review_status: str | None = Query(default=None),
    approval_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await AirlineKnowledgeNormalisationService(db).agency_response(
        agency_id,
        normalisation_status=normalisation_status,
        normalisation_type=normalisation_type,
        canonical_code=canonical_code,
        taxonomy_domain=taxonomy_domain,
        taxonomy_family=taxonomy_family,
        taxonomy_variant=taxonomy_variant,
        airline=airline,
        ssr_code=ssr_code,
        rfic=rfic,
        rfisc=rfisc,
        review_status=review_status,
        approval_status=approval_status,
    )


@router.get("/summary")
async def summarize_agency_airline_knowledge_normalisations(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await AirlineKnowledgeNormalisationService(db).agency_summary(agency_id)


@router.get("/{normalisation_id}")
async def get_agency_airline_knowledge_normalisation(
    agency_id: str,
    normalisation_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AirlineKnowledgeNormalisationService(db)
    try:
        normalisation = await service.get_agency_normalisation(agency_id, normalisation_id)
    except AirlineKnowledgeNormalisationError:
        raise not_found("Airline knowledge normalisation metadata not found.")
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "airline_knowledge_normalisation": normalisation,
        "read_only": True,
        "metadata_only": True,
        **service.safety_flags(),
    }
