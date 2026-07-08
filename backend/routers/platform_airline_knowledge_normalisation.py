from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import AirlineKnowledgeNormalisationCreate, AirlineKnowledgeNormalisationUpdate
from services.airline_knowledge_normalisation_service import PHASE_LABEL, AirlineKnowledgeNormalisationError, AirlineKnowledgeNormalisationService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/airline-knowledge-normalisation", tags=["platform-airline-knowledge-normalisation"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_platform_airline_knowledge_normalisations(
    agency_id: str | None = Query(default=None),
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
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AirlineKnowledgeNormalisationService(db).platform_response(
        agency_id=agency_id,
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
        include_archived=include_archived,
    )


@router.get("/summary")
async def summarize_platform_airline_knowledge_normalisations(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AirlineKnowledgeNormalisationService(db).platform_summary()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_knowledge_normalisation(
    payload: AirlineKnowledgeNormalisationCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineKnowledgeNormalisationService(db).create_normalisation(payload, user)
    except AirlineKnowledgeNormalisationError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{normalisation_id}")
async def get_platform_airline_knowledge_normalisation(
    normalisation_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = AirlineKnowledgeNormalisationService(db)
    try:
        normalisation = await service.get_platform_normalisation(normalisation_id)
    except AirlineKnowledgeNormalisationError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "airline_knowledge_normalisation": normalisation,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{normalisation_id}")
async def update_platform_airline_knowledge_normalisation(
    normalisation_id: str,
    payload: AirlineKnowledgeNormalisationUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineKnowledgeNormalisationService(db).update_normalisation(normalisation_id, payload, user)
    except AirlineKnowledgeNormalisationError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/{normalisation_id}")
async def delete_platform_airline_knowledge_normalisation(
    normalisation_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineKnowledgeNormalisationService(db).delete_normalisation(normalisation_id, user)
    except AirlineKnowledgeNormalisationError as exc:
        raise bad_request(str(exc)) from exc
