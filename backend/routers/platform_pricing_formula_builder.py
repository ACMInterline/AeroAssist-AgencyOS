from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import PricingFormulaBuilderCreate, PricingFormulaBuilderUpdate
from services.pricing_formula_builder_service import (
    PHASE_LABEL,
    PricingFormulaBuilderError,
    PricingFormulaBuilderService,
)
from services.tenant_service import require_any_platform_role


router = APIRouter(tags=["platform-pricing-formula-builder"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("/api/platform/pricing-formula-builder")
async def list_platform_pricing_formula_builder_records(
    agency_id: str | None = Query(default=None),
    airline: str | None = Query(default=None),
    service_family: str | None = Query(default=None),
    service_code: str | None = Query(default=None),
    pricing_unit: str | None = Query(default=None),
    way: str | None = Query(default=None),
    route_type: str | None = Query(default=None),
    flight_type: str | None = Query(default=None),
    fare_bundle: str | None = Query(default=None),
    pricing_category: str | None = Query(default=None),
    amount_type: str | None = Query(default=None),
    currency: str | None = Query(default=None),
    formula_status: str | None = Query(default=None),
    manual_confirmation_required: bool | None = Query(default=None),
    client_visibility: str | None = Query(default=None),
    search: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await PricingFormulaBuilderService(db).platform_response(
        agency_id=agency_id,
        airline=airline,
        service_family=service_family,
        service_code=service_code,
        pricing_unit=pricing_unit,
        way=way,
        route_type=route_type,
        flight_type=flight_type,
        fare_bundle=fare_bundle,
        pricing_category=pricing_category,
        amount_type=amount_type,
        currency=currency,
        formula_status=formula_status,
        manual_confirmation_required=manual_confirmation_required,
        client_visibility=client_visibility,
        search=search,
        include_archived=include_archived,
    )


@router.get("/api/platform/pricing-formula-builder/summary")
async def summarize_platform_pricing_formula_builder_records(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await PricingFormulaBuilderService(db).platform_summary(agency_id)


@router.post("/api/platform/pricing-formula-builder", status_code=status.HTTP_201_CREATED)
async def create_platform_pricing_formula_builder_record(
    payload: PricingFormulaBuilderCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await PricingFormulaBuilderService(db).create_formula(payload, user)
    except PricingFormulaBuilderError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/api/platform/pricing-formula-builder/{formula_id}")
async def get_platform_pricing_formula_builder_record(
    formula_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = PricingFormulaBuilderService(db)
    try:
        formula = await service.get_formula(formula_id)
    except PricingFormulaBuilderError as exc:
        raise bad_request(str(exc)) from exc
    return {"phase": PHASE_LABEL, "pricing_formula_builder": formula, "metadata_only": True, **service.safety_flags()}


@router.put("/api/platform/pricing-formula-builder/{formula_id}")
async def update_platform_pricing_formula_builder_record(
    formula_id: str,
    payload: PricingFormulaBuilderUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await PricingFormulaBuilderService(db).update_formula(formula_id, payload, user)
    except PricingFormulaBuilderError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/api/platform/pricing-formula-builder/{formula_id}")
async def archive_platform_pricing_formula_builder_record(
    formula_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await PricingFormulaBuilderService(db).archive_formula(formula_id, user)
    except PricingFormulaBuilderError as exc:
        raise bad_request(str(exc)) from exc
