from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import AirlineKnowledgePublicationCreate, AirlineKnowledgePublicationUpdate
from services.airline_knowledge_publishing_service import (
    PHASE_LABEL,
    AirlineKnowledgePublishingError,
    AirlineKnowledgePublishingService,
)
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(tags=["agency-airline-knowledge-publishing"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin", "agency_agent"]
PLATFORM_ROLES = {"platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"}


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in PLATFORM_ROLES:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


async def require_write(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in PLATFORM_ROLES:
        await require_any_agency_role(db, agency_id, user, WRITE_ROLES)


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("/api/agencies/{agency_id}/published-knowledge")
async def list_agency_published_knowledge(
    agency_id: str,
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
    await require_read(db, agency_id, user)
    return await AirlineKnowledgePublishingService(db).agency_response(
        agency_id,
        airline_code=airline_code,
        service_family=service_family,
        publication_status=publication_status,
        release_channel=release_channel,
        agency_visibility=agency_visibility,
        AOIE_ready=AOIE_ready,
        search=search,
        include_archived=include_archived,
    )


@router.get("/api/agencies/{agency_id}/published-knowledge/summary")
async def summarize_agency_published_knowledge(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await AirlineKnowledgePublishingService(db).agency_summary(agency_id)


@router.post("/api/agencies/{agency_id}/published-knowledge", status_code=status.HTTP_201_CREATED)
async def create_agency_published_knowledge(
    agency_id: str,
    payload: AirlineKnowledgePublicationCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await AirlineKnowledgePublishingService(db).create_publication(payload, user, agency_id=agency_id)
    except AirlineKnowledgePublishingError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/api/agencies/{agency_id}/published-knowledge/{publication_id}")
async def get_agency_published_knowledge(
    agency_id: str,
    publication_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AirlineKnowledgePublishingService(db)
    try:
        publication = await service.get_publication(publication_id, agency_id=agency_id)
    except AirlineKnowledgePublishingError:
        raise not_found("Airline knowledge publication metadata not found.")
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "airline_knowledge_publication": publication, "metadata_only": True, **service.safety_flags()}


@router.put("/api/agencies/{agency_id}/published-knowledge/{publication_id}")
async def update_agency_published_knowledge(
    agency_id: str,
    publication_id: str,
    payload: AirlineKnowledgePublicationUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await AirlineKnowledgePublishingService(db).update_publication(publication_id, payload, user, agency_id=agency_id)
    except AirlineKnowledgePublishingError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/api/agencies/{agency_id}/published-knowledge/{publication_id}")
async def archive_agency_published_knowledge(
    agency_id: str,
    publication_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await AirlineKnowledgePublishingService(db).archive_publication(publication_id, user, agency_id=agency_id)
    except AirlineKnowledgePublishingError as exc:
        raise bad_request(str(exc)) from exc
