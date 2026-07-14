from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.airline_fare_family_brand_intelligence_service import (
    PHASE_LABEL,
    AirlineFareFamilyBrandIntelligenceError,
    AirlineFareFamilyBrandIntelligenceService,
)
from services.tenant_service import require_any_platform_role


router = APIRouter(
    prefix="/api/platform/fare-brand-intelligence",
    tags=["platform-fare-brand-intelligence"],
)

READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_read(user: dict) -> None:
    await require_any_platform_role(user, READ_ROLES)


async def require_write(user: dict) -> None:
    await require_any_platform_role(user, WRITE_ROLES)


def bad_request(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("")
async def get_platform_fare_brand_intelligence(
    agency_id: str | None = Query(default=None),
    airline_code: str | None = Query(default=None),
    cabin: str | None = Query(default=None),
    publication_status: str | None = Query(default=None),
    freshness_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    return await AirlineFareFamilyBrandIntelligenceService(db).platform_dashboard(
        agency_id=agency_id,
        airline_code=airline_code,
        cabin=cabin,
        publication_status=publication_status,
        freshness_status=freshness_status,
    )


@router.get("/summary")
async def summarize_platform_fare_brand_intelligence(
    agency_id: str | None = Query(default=None),
    airline_code: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = AirlineFareFamilyBrandIntelligenceService(db)
    response = await service.platform_dashboard(agency_id=agency_id, airline_code=airline_code)
    return {
        "phase": PHASE_LABEL,
        "summary": response["summary"],
        "stale_or_incomplete": response["stale_or_incomplete"],
        "legacy_context": response["legacy_context"],
        **service.safety_flags(),
    }


@router.get("/filters")
async def get_platform_fare_brand_filters(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = AirlineFareFamilyBrandIntelligenceService(db)
    return {"phase": PHASE_LABEL, "filters": service.filter_metadata(), **service.safety_flags()}


async def run_advisory(action: str, payload: dict, db: Database) -> dict:
    service = AirlineFareFamilyBrandIntelligenceService(db)
    if action == "compare":
        return await service.compare_brands(payload, agency_id=payload.get("agency_id"))
    if action == "resolve-rbd":
        return await service.resolve_rbd(payload, agency_id=payload.get("agency_id"))
    if action == "resolve-baggage":
        return await service.resolve_baggage(payload, agency_id=payload.get("agency_id"))
    return await service.offer_builder_attributes(payload, agency_id=payload.get("agency_id"), agency_safe=False)


@router.post("/compare")
async def compare_platform_fare_brands(
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    try:
        return await run_advisory("compare", payload, db)
    except AirlineFareFamilyBrandIntelligenceError as exc:
        raise bad_request(exc) from exc


@router.post("/resolve-rbd")
async def resolve_platform_booking_class(
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    try:
        return await run_advisory("resolve-rbd", payload, db)
    except AirlineFareFamilyBrandIntelligenceError as exc:
        raise bad_request(exc) from exc


@router.post("/resolve-baggage")
async def resolve_platform_baggage_allowance(
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    try:
        return await run_advisory("resolve-baggage", payload, db)
    except AirlineFareFamilyBrandIntelligenceError as exc:
        raise bad_request(exc) from exc


@router.post("/offer-builder-attributes")
async def project_platform_offer_builder_attributes(
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    try:
        return await run_advisory("offer-builder-attributes", payload, db)
    except AirlineFareFamilyBrandIntelligenceError as exc:
        raise bad_request(exc) from exc


@router.get("/{entity_type}")
async def list_platform_fare_brand_records(
    entity_type: str,
    agency_id: str | None = Query(default=None),
    airline_code: str | None = Query(default=None),
    cabin: str | None = Query(default=None),
    rbd_code: str | None = Query(default=None),
    brand_code: str | None = Query(default=None),
    attribute_code: str | None = Query(default=None),
    publication_status: str | None = Query(default=None),
    freshness_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = AirlineFareFamilyBrandIntelligenceService(db)
    try:
        items = await service.list_records(
            entity_type,
            agency_id=agency_id,
            airline_code=airline_code,
            cabin=cabin,
            rbd_code=rbd_code,
            brand_code=brand_code,
            attribute_code=attribute_code,
            publication_status=publication_status,
            freshness_status=freshness_status,
        )
    except AirlineFareFamilyBrandIntelligenceError as exc:
        raise bad_request(exc) from exc
    return {"phase": PHASE_LABEL, "entity_type": entity_type, "items": items, "count": len(items), **service.safety_flags()}


@router.post("/{entity_type}", status_code=status.HTTP_201_CREATED)
async def create_platform_fare_brand_record(
    entity_type: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    try:
        return await AirlineFareFamilyBrandIntelligenceService(db).create_record(entity_type, payload, user)
    except (AirlineFareFamilyBrandIntelligenceError, ValueError) as exc:
        raise bad_request(exc) from exc


@router.get("/{entity_type}/{record_id}")
async def get_platform_fare_brand_record(
    entity_type: str,
    record_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    try:
        return await AirlineFareFamilyBrandIntelligenceService(db).get_record(entity_type, record_id)
    except AirlineFareFamilyBrandIntelligenceError as exc:
        raise bad_request(exc) from exc


@router.put("/{entity_type}/{record_id}")
async def update_platform_fare_brand_record(
    entity_type: str,
    record_id: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    try:
        return await AirlineFareFamilyBrandIntelligenceService(db).update_record(entity_type, record_id, payload, user)
    except (AirlineFareFamilyBrandIntelligenceError, ValueError) as exc:
        raise bad_request(exc) from exc
