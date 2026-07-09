from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import ReferenceDataDomainCreate, ReferenceDataDomainUpdate
from services.reference_data_engine_service import (
    PHASE_LABEL,
    ReferenceDataEngineError,
    ReferenceDataEngineService,
)
from services.tenant_service import require_any_platform_role


router = APIRouter(tags=["platform-reference-data-engine"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("/api/platform/reference-data-engine")
async def list_platform_reference_data_engine(
    agency_id: str | None = Query(default=None),
    domain_code: str | None = Query(default=None),
    governance_status: str | None = Query(default=None),
    review_status: str | None = Query(default=None),
    active: bool | None = Query(default=None),
    search: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await ReferenceDataEngineService(db).platform_response(
        agency_id=agency_id,
        domain_code=domain_code,
        governance_status=governance_status,
        review_status=review_status,
        active=active,
        search=search,
        include_archived=include_archived,
    )


@router.get("/api/platform/reference-data-engine/summary")
async def summarize_platform_reference_data_engine(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await ReferenceDataEngineService(db).platform_summary(agency_id)


@router.post("/api/platform/reference-data-engine", status_code=status.HTTP_201_CREATED)
async def create_platform_reference_data_domain(
    payload: ReferenceDataDomainCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await ReferenceDataEngineService(db).create_domain(payload, user)
    except ReferenceDataEngineError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/api/platform/reference-data-engine/{domain_id}")
async def get_platform_reference_data_domain(
    domain_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = ReferenceDataEngineService(db)
    try:
        domain = await service.get_domain(domain_id)
    except ReferenceDataEngineError as exc:
        raise bad_request(str(exc)) from exc
    return {"phase": PHASE_LABEL, "reference_data_domain": domain, "metadata_only": True, **service.safety_flags()}


@router.put("/api/platform/reference-data-engine/{domain_id}")
async def update_platform_reference_data_domain(
    domain_id: str,
    payload: ReferenceDataDomainUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await ReferenceDataEngineService(db).update_domain(domain_id, payload, user)
    except ReferenceDataEngineError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/api/platform/reference-data-engine/{domain_id}")
async def archive_platform_reference_data_domain(
    domain_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await ReferenceDataEngineService(db).archive_domain(domain_id, user)
    except ReferenceDataEngineError as exc:
        raise bad_request(str(exc)) from exc
