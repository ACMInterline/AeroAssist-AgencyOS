from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import ReferenceDataDomainCreate, ReferenceDataDomainUpdate
from services.reference_data_engine_service import (
    PHASE_LABEL,
    ReferenceDataEngineError,
    ReferenceDataEngineService,
)
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(tags=["agency-reference-data-engine"])

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


@router.get("/api/agencies/{agency_id}/reference-data-engine")
async def list_agency_reference_data_engine(
    agency_id: str,
    domain_code: str | None = Query(default=None),
    governance_status: str | None = Query(default=None),
    review_status: str | None = Query(default=None),
    active: bool | None = Query(default=None),
    search: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await ReferenceDataEngineService(db).agency_response(
        agency_id,
        domain_code=domain_code,
        governance_status=governance_status,
        review_status=review_status,
        active=active,
        search=search,
        include_archived=include_archived,
    )


@router.get("/api/agencies/{agency_id}/reference-data-engine/summary")
async def summarize_agency_reference_data_engine(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await ReferenceDataEngineService(db).agency_summary(agency_id)


@router.post("/api/agencies/{agency_id}/reference-data-engine", status_code=status.HTTP_201_CREATED)
async def create_agency_reference_data_domain(
    agency_id: str,
    payload: ReferenceDataDomainCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await ReferenceDataEngineService(db).create_domain(payload, user, agency_id=agency_id)
    except ReferenceDataEngineError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/api/agencies/{agency_id}/reference-data-engine/{domain_id}")
async def get_agency_reference_data_domain(
    agency_id: str,
    domain_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = ReferenceDataEngineService(db)
    try:
        domain = await service.get_domain(domain_id, agency_id=agency_id)
    except ReferenceDataEngineError:
        raise not_found("Reference data domain metadata not found.")
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "reference_data_domain": domain, "metadata_only": True, **service.safety_flags()}


@router.put("/api/agencies/{agency_id}/reference-data-engine/{domain_id}")
async def update_agency_reference_data_domain(
    agency_id: str,
    domain_id: str,
    payload: ReferenceDataDomainUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await ReferenceDataEngineService(db).update_domain(domain_id, payload, user, agency_id=agency_id)
    except ReferenceDataEngineError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/api/agencies/{agency_id}/reference-data-engine/{domain_id}")
async def archive_agency_reference_data_domain(
    agency_id: str,
    domain_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await ReferenceDataEngineService(db).archive_domain(domain_id, user, agency_id=agency_id)
    except ReferenceDataEngineError as exc:
        raise bad_request(str(exc)) from exc
