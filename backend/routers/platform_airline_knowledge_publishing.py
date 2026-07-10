from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import AirlineKnowledgePublicationCreate, AirlineKnowledgePublicationUpdate
from services.airline_knowledge_publishing_service import (
    PHASE_LABEL,
    AirlineKnowledgePublishingError,
    AirlineKnowledgePublishingService,
)
from services.tenant_service import require_any_platform_role


router = APIRouter(tags=["platform-airline-knowledge-publishing"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("/api/platform/airline-knowledge-publishing")
async def list_platform_airline_knowledge_publications(
    agency_id: str | None = Query(default=None),
    airline_code: str | None = Query(default=None),
    service_family: str | None = Query(default=None),
    publication_status: str | None = Query(default=None),
    release_channel: str | None = Query(default=None),
    agency_visibility: str | None = Query(default=None),
    AOIE_ready: bool | None = Query(default=None),
    search: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AirlineKnowledgePublishingService(db).platform_response(
        agency_id=agency_id,
        airline_code=airline_code,
        service_family=service_family,
        publication_status=publication_status,
        release_channel=release_channel,
        agency_visibility=agency_visibility,
        AOIE_ready=AOIE_ready,
        search=search,
        include_archived=include_archived,
    )


@router.get("/api/platform/airline-knowledge-publishing/summary")
async def summarize_platform_airline_knowledge_publications(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AirlineKnowledgePublishingService(db).platform_summary(agency_id)


@router.post("/api/platform/airline-knowledge-publishing", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_knowledge_publication(
    payload: AirlineKnowledgePublicationCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineKnowledgePublishingService(db).create_publication(payload, user)
    except AirlineKnowledgePublishingError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/api/platform/airline-knowledge-publishing/{publication_id}")
async def get_platform_airline_knowledge_publication(
    publication_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = AirlineKnowledgePublishingService(db)
    try:
        publication = await service.get_publication(publication_id)
    except AirlineKnowledgePublishingError as exc:
        raise bad_request(str(exc)) from exc
    return {"phase": PHASE_LABEL, "airline_knowledge_publication": publication, "metadata_only": True, **service.safety_flags()}


@router.put("/api/platform/airline-knowledge-publishing/{publication_id}")
async def update_platform_airline_knowledge_publication(
    publication_id: str,
    payload: AirlineKnowledgePublicationUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineKnowledgePublishingService(db).update_publication(publication_id, payload, user)
    except AirlineKnowledgePublishingError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/api/platform/airline-knowledge-publishing/{publication_id}")
async def archive_platform_airline_knowledge_publication(
    publication_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineKnowledgePublishingService(db).archive_publication(publication_id, user)
    except AirlineKnowledgePublishingError as exc:
        raise bad_request(str(exc)) from exc
