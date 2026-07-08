from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.airline_knowledge_governance_service import (
    PHASE_LABEL,
    AirlineKnowledgeGovernanceError,
    AirlineKnowledgeGovernanceService,
)
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/airline-knowledge-governance", tags=["agency-airline-knowledge-governance"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


@router.get("")
async def list_agency_airline_knowledge_governance(
    agency_id: str,
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
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await AirlineKnowledgeGovernanceService(db).agency_response(
        agency_id,
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
    )


@router.get("/summary")
async def summarize_agency_airline_knowledge_governance(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await AirlineKnowledgeGovernanceService(db).agency_summary(agency_id)


@router.get("/versions")
async def list_agency_airline_knowledge_versions(
    agency_id: str,
    lifecycle_status: str | None = Query(default=None),
    review_status: str | None = Query(default=None),
    approval_status: str | None = Query(default=None),
    publication_channel: str | None = Query(default=None),
    publication_scope: str | None = Query(default=None),
    knowledge_scope: str | None = Query(default=None),
    change_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AirlineKnowledgeGovernanceService(db)
    versions = await service.list_agency_versions(
        agency_id,
        lifecycle_status=lifecycle_status,
        review_status=review_status,
        approval_status=approval_status,
        publication_channel=publication_channel,
        publication_scope=publication_scope,
        knowledge_scope=knowledge_scope,
        change_type=change_type,
    )
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "versions": versions,
        "airline_knowledge_version_count": len(versions),
        "read_only": True,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.get("/versions/{version_id}")
async def get_agency_airline_knowledge_version(
    agency_id: str,
    version_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AirlineKnowledgeGovernanceService(db)
    try:
        version = await service.get_agency_version(agency_id, version_id)
    except AirlineKnowledgeGovernanceError:
        raise not_found("Airline knowledge version metadata not found.")
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "airline_knowledge_version": version,
        "read_only": True,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.get("/releases")
async def list_agency_airline_knowledge_releases(
    agency_id: str,
    release_status: str | None = Query(default=None),
    airline_code: str | None = Query(default=None),
    country: str | None = Query(default=None),
    service_domain: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AirlineKnowledgeGovernanceService(db)
    releases = await service.list_agency_releases(
        agency_id,
        release_status=release_status,
        airline_code=airline_code,
        country=country,
        service_domain=service_domain,
    )
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "releases": releases,
        "airline_knowledge_release_count": len(releases),
        "read_only": True,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.get("/releases/{release_id}")
async def get_agency_airline_knowledge_release(
    agency_id: str,
    release_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AirlineKnowledgeGovernanceService(db)
    try:
        release = await service.get_agency_release(agency_id, release_id)
    except AirlineKnowledgeGovernanceError:
        raise not_found("Airline knowledge release metadata not found.")
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "airline_knowledge_release": release,
        "read_only": True,
        "metadata_only": True,
        **service.safety_flags(),
    }
