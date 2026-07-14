from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.airline_distribution_capability_service import (
    PHASE_LABEL,
    AirlineDistributionCapabilityError,
    AirlineDistributionCapabilityService,
)
from services.tenant_service import require_any_platform_role


router = APIRouter(
    prefix="/api/platform/airline-distribution-capabilities",
    tags=["platform-airline-distribution-capabilities"],
)

READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_read(user: dict) -> None:
    await require_any_platform_role(user, READ_ROLES)


async def require_write(user: dict) -> None:
    await require_any_platform_role(user, WRITE_ROLES)


def bad_request(exc: AirlineDistributionCapabilityError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("")
async def get_platform_airline_distribution_capabilities(
    agency_id: str | None = Query(default=None),
    airline_code: str | None = Query(default=None),
    channel_code: str | None = Query(default=None),
    capability_area: str | None = Query(default=None),
    capability_code: str | None = Query(default=None),
    capability_status: str | None = Query(default=None),
    provider_stage: str | None = Query(default=None),
    publication_status: str | None = Query(default=None),
    freshness_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    return await AirlineDistributionCapabilityService(db).platform_dashboard(
        agency_id=agency_id,
        airline_code=airline_code,
        channel_code=channel_code,
        capability_area=capability_area,
        capability_code=capability_code,
        capability_status=capability_status,
        provider_stage=provider_stage,
        publication_status=publication_status,
        freshness_status=freshness_status,
    )


@router.get("/summary")
async def summarize_platform_airline_distribution_capabilities(
    agency_id: str | None = Query(default=None),
    airline_code: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = AirlineDistributionCapabilityService(db)
    response = await service.platform_dashboard(agency_id=agency_id, airline_code=airline_code)
    return {"phase": PHASE_LABEL, "summary": response["summary"], "legacy_context": response["legacy_context"], **service.safety_flags()}


@router.get("/filters")
async def get_platform_airline_distribution_capability_filters(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = AirlineDistributionCapabilityService(db)
    return {"phase": PHASE_LABEL, "filters": service.filter_metadata(), **service.safety_flags()}


@router.get("/{entity_type}")
async def list_platform_airline_distribution_records(
    entity_type: str,
    agency_id: str | None = Query(default=None),
    airline_code: str | None = Query(default=None),
    channel_code: str | None = Query(default=None),
    capability_area: str | None = Query(default=None),
    capability_code: str | None = Query(default=None),
    capability_status: str | None = Query(default=None),
    provider_stage: str | None = Query(default=None),
    publication_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = AirlineDistributionCapabilityService(db)
    try:
        items = await service.list_records(
            entity_type,
            agency_id=agency_id,
            airline_code=airline_code,
            channel_code=channel_code,
            capability_area=capability_area,
            capability_code=capability_code,
            capability_status=capability_status,
            provider_stage=provider_stage,
            publication_status=publication_status,
        )
    except AirlineDistributionCapabilityError as exc:
        raise bad_request(exc) from exc
    return {"phase": PHASE_LABEL, "entity_type": entity_type, "items": items, "count": len(items), **service.safety_flags()}


@router.post("/{entity_type}", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_distribution_record(
    entity_type: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    try:
        return await AirlineDistributionCapabilityService(db).create_record(entity_type, payload, user)
    except AirlineDistributionCapabilityError as exc:
        raise bad_request(exc) from exc


@router.get("/{entity_type}/{record_id}")
async def get_platform_airline_distribution_record(
    entity_type: str,
    record_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    try:
        return await AirlineDistributionCapabilityService(db).get_record(entity_type, record_id)
    except AirlineDistributionCapabilityError as exc:
        raise bad_request(exc) from exc


@router.put("/{entity_type}/{record_id}")
async def update_platform_airline_distribution_record(
    entity_type: str,
    record_id: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    try:
        return await AirlineDistributionCapabilityService(db).update_record(entity_type, record_id, payload, user)
    except AirlineDistributionCapabilityError as exc:
        raise bad_request(exc) from exc
