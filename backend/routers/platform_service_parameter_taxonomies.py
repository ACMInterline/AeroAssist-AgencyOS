from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import ServiceParameterTaxonomyCreate, ServiceParameterTaxonomyUpdate
from services.service_parameter_taxonomy_service import (
    PHASE_LABEL,
    ServiceParameterTaxonomyError,
    ServiceParameterTaxonomyService,
)
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/service-parameter-taxonomies", tags=["platform-service-parameter-taxonomies"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_platform_service_parameter_taxonomies(
    agency_id: str | None = Query(default=None),
    taxonomy_status: str | None = Query(default=None),
    policy_family: str | None = Query(default=None),
    service_family: str | None = Query(default=None),
    service_code: str | None = Query(default=None),
    parameter_domain: str | None = Query(default=None),
    parameter_group: str | None = Query(default=None),
    parameter_scope: str | None = Query(default=None),
    review_status: str | None = Query(default=None),
    approval_status: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await ServiceParameterTaxonomyService(db).platform_response(
        agency_id=agency_id,
        taxonomy_status=taxonomy_status,
        policy_family=policy_family,
        service_family=service_family,
        service_code=service_code,
        parameter_domain=parameter_domain,
        parameter_group=parameter_group,
        parameter_scope=parameter_scope,
        review_status=review_status,
        approval_status=approval_status,
        include_archived=include_archived,
    )


@router.get("/summary")
async def summarize_platform_service_parameter_taxonomies(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await ServiceParameterTaxonomyService(db).platform_summary()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_platform_service_parameter_taxonomy(
    payload: ServiceParameterTaxonomyCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await ServiceParameterTaxonomyService(db).create_taxonomy(payload, user)
    except ServiceParameterTaxonomyError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{taxonomy_id}")
async def get_platform_service_parameter_taxonomy(
    taxonomy_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = ServiceParameterTaxonomyService(db)
    try:
        taxonomy = await service.get_platform_taxonomy(taxonomy_id)
    except ServiceParameterTaxonomyError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "service_parameter_taxonomy": taxonomy,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{taxonomy_id}")
async def update_platform_service_parameter_taxonomy(
    taxonomy_id: str,
    payload: ServiceParameterTaxonomyUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await ServiceParameterTaxonomyService(db).update_taxonomy(taxonomy_id, payload, user)
    except ServiceParameterTaxonomyError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/{taxonomy_id}")
async def archive_platform_service_parameter_taxonomy(
    taxonomy_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await ServiceParameterTaxonomyService(db).archive_taxonomy(taxonomy_id, user)
    except ServiceParameterTaxonomyError as exc:
        raise bad_request(str(exc)) from exc
