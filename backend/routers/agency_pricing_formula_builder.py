from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import PricingFormulaBuilderCreate, PricingFormulaBuilderUpdate
from services.pricing_formula_builder_service import (
    PHASE_LABEL,
    PricingFormulaBuilderError,
    PricingFormulaBuilderService,
)
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(tags=["agency-pricing-formula-builder"])

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


@router.get("/api/agencies/{agency_id}/pricing-formula-builder")
async def list_agency_pricing_formula_builder_records(
    agency_id: str,
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
    await require_read(db, agency_id, user)
    return await PricingFormulaBuilderService(db).agency_response(
        agency_id,
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


@router.get("/api/agencies/{agency_id}/pricing-formula-builder/summary")
async def summarize_agency_pricing_formula_builder_records(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await PricingFormulaBuilderService(db).agency_summary(agency_id)


@router.post("/api/agencies/{agency_id}/pricing-formula-builder", status_code=status.HTTP_201_CREATED)
async def create_agency_pricing_formula_builder_record(
    agency_id: str,
    payload: PricingFormulaBuilderCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await PricingFormulaBuilderService(db).create_formula(payload, user, agency_id=agency_id)
    except PricingFormulaBuilderError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/api/agencies/{agency_id}/pricing-formula-builder/{formula_id}")
async def get_agency_pricing_formula_builder_record(
    agency_id: str,
    formula_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = PricingFormulaBuilderService(db)
    try:
        formula = await service.get_formula(formula_id, agency_id=agency_id)
    except PricingFormulaBuilderError:
        raise not_found("Pricing formula builder metadata not found.")
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "pricing_formula_builder": formula, "metadata_only": True, **service.safety_flags()}


@router.put("/api/agencies/{agency_id}/pricing-formula-builder/{formula_id}")
async def update_agency_pricing_formula_builder_record(
    agency_id: str,
    formula_id: str,
    payload: PricingFormulaBuilderUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await PricingFormulaBuilderService(db).update_formula(formula_id, payload, user, agency_id=agency_id)
    except PricingFormulaBuilderError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/api/agencies/{agency_id}/pricing-formula-builder/{formula_id}")
async def archive_agency_pricing_formula_builder_record(
    agency_id: str,
    formula_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await PricingFormulaBuilderService(db).archive_formula(formula_id, user, agency_id=agency_id)
    except PricingFormulaBuilderError as exc:
        raise bad_request(str(exc)) from exc
