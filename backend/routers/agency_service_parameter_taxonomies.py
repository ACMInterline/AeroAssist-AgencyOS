from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import ServiceParameterTaxonomyCreate, ServiceParameterTaxonomyUpdate
from services.service_parameter_taxonomy_service import (
    PHASE_LABEL,
    ServiceParameterTaxonomyError,
    ServiceParameterTaxonomyService,
)
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/service-parameter-taxonomies", tags=["agency-service-parameter-taxonomies"])

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


@router.get("")
async def list_agency_service_parameter_taxonomies(
    agency_id: str,
    taxonomy_status: str | None = Query(default=None),
    policy_family: str | None = Query(default=None),
    service_family: str | None = Query(default=None),
    service_code: str | None = Query(default=None),
    parameter_domain: str | None = Query(default=None),
    parameter_group: str | None = Query(default=None),
    parameter_scope: str | None = Query(default=None),
    review_status: str | None = Query(default=None),
    approval_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await ServiceParameterTaxonomyService(db).agency_response(
        agency_id,
        taxonomy_status=taxonomy_status,
        policy_family=policy_family,
        service_family=service_family,
        service_code=service_code,
        parameter_domain=parameter_domain,
        parameter_group=parameter_group,
        parameter_scope=parameter_scope,
        review_status=review_status,
        approval_status=approval_status,
    )


@router.get("/summary")
async def summarize_agency_service_parameter_taxonomies(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await ServiceParameterTaxonomyService(db).agency_summary(agency_id)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_agency_service_parameter_taxonomy(
    agency_id: str,
    payload: ServiceParameterTaxonomyCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await ServiceParameterTaxonomyService(db).create_taxonomy(payload, user, agency_id=agency_id)
    except ServiceParameterTaxonomyError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{taxonomy_id}")
async def get_agency_service_parameter_taxonomy(
    agency_id: str,
    taxonomy_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = ServiceParameterTaxonomyService(db)
    try:
        taxonomy = await service.get_agency_taxonomy(agency_id, taxonomy_id)
    except ServiceParameterTaxonomyError:
        raise not_found("Service parameter taxonomy metadata not found.")
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "service_parameter_taxonomy": taxonomy,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{taxonomy_id}")
async def update_agency_service_parameter_taxonomy(
    agency_id: str,
    taxonomy_id: str,
    payload: ServiceParameterTaxonomyUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await ServiceParameterTaxonomyService(db).update_taxonomy(taxonomy_id, payload, user, agency_id=agency_id)
    except ServiceParameterTaxonomyError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/{taxonomy_id}")
async def archive_agency_service_parameter_taxonomy(
    agency_id: str,
    taxonomy_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await ServiceParameterTaxonomyService(db).archive_taxonomy(taxonomy_id, user, agency_id=agency_id)
    except ServiceParameterTaxonomyError as exc:
        raise bad_request(str(exc)) from exc
