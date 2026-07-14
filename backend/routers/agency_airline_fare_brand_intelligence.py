from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.airline_fare_family_brand_intelligence_service import (
    PHASE_LABEL,
    AirlineFareFamilyBrandIntelligenceError,
    AirlineFareFamilyBrandIntelligenceService,
)
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(
    prefix="/api/agencies/{agency_id}/fare-brand-library",
    tags=["agency-fare-brand-library"],
)

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {
        "platform_owner",
        "platform_admin",
        "platform_support",
        "platform_knowledge_editor",
    }:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


def bad_request(exc: AirlineFareFamilyBrandIntelligenceError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("")
async def get_agency_fare_brand_library(
    agency_id: str,
    airline_code: str | None = Query(default=None),
    cabin: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await AirlineFareFamilyBrandIntelligenceService(db).agency_dashboard(
        agency_id,
        airline_code=airline_code,
        cabin=cabin,
    )


@router.get("/summary")
async def summarize_agency_fare_brand_library(
    agency_id: str,
    airline_code: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AirlineFareFamilyBrandIntelligenceService(db)
    response = await service.agency_dashboard(agency_id, airline_code=airline_code)
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "summary": response["summary"],
        "operational_caveats": response["operational_caveats"],
        "read_only": True,
        **service.safety_flags(),
    }


async def run_agency_advisory(
    action: str,
    agency_id: str,
    payload: dict,
    db: Database,
) -> dict:
    service = AirlineFareFamilyBrandIntelligenceService(db)
    if action == "compare":
        return await service.compare_brands(payload, agency_id=agency_id, agency_safe=True)
    if action == "resolve-rbd":
        return await service.resolve_rbd(payload, agency_id=agency_id, agency_safe=True)
    if action == "resolve-baggage":
        return await service.resolve_baggage(payload, agency_id=agency_id, agency_safe=True)
    return await service.offer_builder_attributes(payload, agency_id=agency_id, agency_safe=True)


@router.post("/compare")
async def compare_agency_fare_brands(
    agency_id: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    try:
        return await run_agency_advisory("compare", agency_id, payload, db)
    except AirlineFareFamilyBrandIntelligenceError as exc:
        raise bad_request(exc) from exc


@router.post("/resolve-rbd")
async def resolve_agency_booking_class(
    agency_id: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    try:
        return await run_agency_advisory("resolve-rbd", agency_id, payload, db)
    except AirlineFareFamilyBrandIntelligenceError as exc:
        raise bad_request(exc) from exc


@router.post("/resolve-baggage")
async def resolve_agency_baggage_allowance(
    agency_id: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    try:
        return await run_agency_advisory("resolve-baggage", agency_id, payload, db)
    except AirlineFareFamilyBrandIntelligenceError as exc:
        raise bad_request(exc) from exc


@router.post("/offer-builder-attributes")
async def project_agency_offer_builder_attributes(
    agency_id: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    try:
        return await run_agency_advisory("offer-builder-attributes", agency_id, payload, db)
    except AirlineFareFamilyBrandIntelligenceError as exc:
        raise bad_request(exc) from exc


@router.get("/{entity_type}")
async def list_agency_fare_brand_records(
    agency_id: str,
    entity_type: str,
    airline_code: str | None = Query(default=None),
    cabin: str | None = Query(default=None),
    rbd_code: str | None = Query(default=None),
    brand_code: str | None = Query(default=None),
    attribute_code: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AirlineFareFamilyBrandIntelligenceService(db)
    try:
        items = await service.list_agency_records(
            entity_type,
            agency_id,
            airline_code=airline_code,
            cabin=cabin,
            rbd_code=rbd_code,
            brand_code=brand_code,
            attribute_code=attribute_code,
        )
    except AirlineFareFamilyBrandIntelligenceError as exc:
        raise bad_request(exc) from exc
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "entity_type": entity_type,
        "items": items,
        "count": len(items),
        "read_only": True,
        **service.safety_flags(),
    }
