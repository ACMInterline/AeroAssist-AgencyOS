from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    AirlineKnowledgeReleaseCreate,
    AirlineKnowledgeReleaseUpdate,
    AirlineKnowledgeVersionCreate,
    AirlineKnowledgeVersionUpdate,
)
from services.airline_knowledge_governance_service import (
    PHASE_LABEL,
    AirlineKnowledgeGovernanceError,
    AirlineKnowledgeGovernanceService,
)
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/airline-knowledge-governance", tags=["platform-airline-knowledge-governance"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_platform_airline_knowledge_governance(
    agency_id: str | None = Query(default=None),
    lifecycle_status: str | None = Query(default=None),
    release_status: str | None = Query(default=None),
    review_status: str | None = Query(default=None),
    approval_status: str | None = Query(default=None),
    publication_channel: str | None = Query(default=None),
    publication_scope: str | None = Query(default=None),
    knowledge_scope: str | None = Query(default=None),
    change_type: str | None = Query(default=None),
    airline_code: str | None = Query(default=None),
    country: str | None = Query(default=None),
    service_domain: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AirlineKnowledgeGovernanceService(db).platform_response(
        agency_id=agency_id,
        lifecycle_status=lifecycle_status,
        release_status=release_status,
        review_status=review_status,
        approval_status=approval_status,
        publication_channel=publication_channel,
        publication_scope=publication_scope,
        knowledge_scope=knowledge_scope,
        change_type=change_type,
        airline_code=airline_code,
        country=country,
        service_domain=service_domain,
        include_archived=include_archived,
    )


@router.get("/summary")
async def summarize_platform_airline_knowledge_governance(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AirlineKnowledgeGovernanceService(db).platform_summary()


@router.get("/versions")
async def list_platform_airline_knowledge_versions(
    agency_id: str | None = Query(default=None),
    lifecycle_status: str | None = Query(default=None),
    review_status: str | None = Query(default=None),
    approval_status: str | None = Query(default=None),
    publication_channel: str | None = Query(default=None),
    publication_scope: str | None = Query(default=None),
    knowledge_scope: str | None = Query(default=None),
    change_type: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = AirlineKnowledgeGovernanceService(db)
    versions = await service.list_platform_versions(
        agency_id=agency_id,
        lifecycle_status=lifecycle_status,
        review_status=review_status,
        approval_status=approval_status,
        publication_channel=publication_channel,
        publication_scope=publication_scope,
        knowledge_scope=knowledge_scope,
        change_type=change_type,
        include_archived=include_archived,
    )
    return {
        "phase": PHASE_LABEL,
        "versions": versions,
        "airline_knowledge_version_count": len(versions),
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.post("/versions", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_knowledge_version(
    payload: AirlineKnowledgeVersionCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineKnowledgeGovernanceService(db).create_version(payload, user)
    except AirlineKnowledgeGovernanceError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/versions/{version_id}")
async def get_platform_airline_knowledge_version(
    version_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = AirlineKnowledgeGovernanceService(db)
    try:
        version = await service.get_platform_version(version_id)
    except AirlineKnowledgeGovernanceError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "airline_knowledge_version": version,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/versions/{version_id}")
async def update_platform_airline_knowledge_version(
    version_id: str,
    payload: AirlineKnowledgeVersionUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineKnowledgeGovernanceService(db).update_version(version_id, payload, user)
    except AirlineKnowledgeGovernanceError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/versions/{version_id}")
async def archive_platform_airline_knowledge_version(
    version_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineKnowledgeGovernanceService(db).archive_version(version_id, user)
    except AirlineKnowledgeGovernanceError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/releases")
async def list_platform_airline_knowledge_releases(
    agency_id: str | None = Query(default=None),
    release_status: str | None = Query(default=None),
    airline_code: str | None = Query(default=None),
    country: str | None = Query(default=None),
    service_domain: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = AirlineKnowledgeGovernanceService(db)
    releases = await service.list_platform_releases(
        agency_id=agency_id,
        release_status=release_status,
        airline_code=airline_code,
        country=country,
        service_domain=service_domain,
        include_archived=include_archived,
    )
    return {
        "phase": PHASE_LABEL,
        "releases": releases,
        "airline_knowledge_release_count": len(releases),
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.post("/releases", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_knowledge_release(
    payload: AirlineKnowledgeReleaseCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineKnowledgeGovernanceService(db).create_release(payload, user)
    except AirlineKnowledgeGovernanceError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/releases/{release_id}")
async def get_platform_airline_knowledge_release(
    release_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = AirlineKnowledgeGovernanceService(db)
    try:
        release = await service.get_platform_release(release_id)
    except AirlineKnowledgeGovernanceError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "airline_knowledge_release": release,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/releases/{release_id}")
async def update_platform_airline_knowledge_release(
    release_id: str,
    payload: AirlineKnowledgeReleaseUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineKnowledgeGovernanceService(db).update_release(release_id, payload, user)
    except AirlineKnowledgeGovernanceError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/releases/{release_id}")
async def archive_platform_airline_knowledge_release(
    release_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineKnowledgeGovernanceService(db).archive_release(release_id, user)
    except AirlineKnowledgeGovernanceError as exc:
        raise bad_request(str(exc)) from exc
