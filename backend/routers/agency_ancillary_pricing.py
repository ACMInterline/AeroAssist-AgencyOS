from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    AirlineServicePriceQuoteEvaluationRequest,
    AirlineServicePriceQuoteScenarioCreate,
    AncillaryPricingLookupRequest,
    PolicyCandidatePricingLinkCreate,
)
from services.ancillary_pricing_service import AncillaryPricingService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/ancillary-pricing", tags=["agency-ancillary-pricing"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin", "agency_agent"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


async def require_write(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin"}:
        await require_any_agency_role(db, agency_id, user, WRITE_ROLES)


async def list_resource(
    resource: str,
    agency_id: str,
    db: Database,
    *,
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    pricing_rule_id: str | None = None,
    matrix_id: str | None = None,
    scenario_id: str | None = None,
    include_archived: bool = False,
) -> dict:
    return {
        "items": await AncillaryPricingService(db).list_records(
            resource,
            agency_id=agency_id,
            airline_code=airline_code,
            domain_code=domain_code,
            family_code=family_code,
            variant_code=variant_code,
            pricing_rule_id=pricing_rule_id,
            matrix_id=matrix_id,
            scenario_id=scenario_id,
            include_archived=include_archived,
        ),
        "read_only": resource not in {"quote_scenarios", "candidate_pricing_links"},
        "agency_global_mutation_disabled": True,
    }


@router.get("/summary")
async def get_agency_ancillary_pricing_summary(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    summary = await AncillaryPricingService(db).summary(agency_id=agency_id)
    return {
        **summary,
        "platform_pricing_read_only": True,
        "agency_global_mutation_disabled": True,
    }


@router.post("/lookup")
async def lookup_agency_ancillary_pricing(
    agency_id: str,
    payload: AncillaryPricingLookupRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await AncillaryPricingService(db).lookup(**payload.model_dump(mode="json"), agency_id=agency_id)


@router.post("/evaluate")
async def evaluate_agency_ancillary_pricing(
    agency_id: str,
    payload: AirlineServicePriceQuoteEvaluationRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    return await AncillaryPricingService(db).evaluate(payload, user, agency_id=agency_id)


@router.get("/pricing-rules")
async def list_agency_pricing_rules(
    agency_id: str,
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await list_resource("pricing_rules", agency_id, db, airline_code=airline_code, domain_code=domain_code, family_code=family_code, variant_code=variant_code, include_archived=include_archived)


@router.get("/price-components")
async def list_agency_price_components(
    agency_id: str,
    pricing_rule_id: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await list_resource("price_components", agency_id, db, pricing_rule_id=pricing_rule_id, include_archived=include_archived)


@router.get("/applicability")
async def list_agency_applicability(
    agency_id: str,
    pricing_rule_id: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await list_resource("applicability", agency_id, db, pricing_rule_id=pricing_rule_id, include_archived=include_archived)


@router.get("/pricing-matrices")
async def list_agency_pricing_matrices(
    agency_id: str,
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await list_resource("pricing_matrices", agency_id, db, airline_code=airline_code, domain_code=domain_code, family_code=family_code, variant_code=variant_code, include_archived=include_archived)


@router.get("/pricing-matrix-rows")
async def list_agency_pricing_matrix_rows(
    agency_id: str,
    matrix_id: str | None = None,
    pricing_rule_id: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await list_resource("pricing_matrix_rows", agency_id, db, matrix_id=matrix_id, pricing_rule_id=pricing_rule_id, include_archived=include_archived)


@router.get("/exception-rules")
async def list_agency_exception_rules(
    agency_id: str,
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await list_resource("exception_rules", agency_id, db, airline_code=airline_code, domain_code=domain_code, family_code=family_code, variant_code=variant_code, include_archived=include_archived)


@router.get("/quote-scenarios")
async def list_agency_quote_scenarios(
    agency_id: str,
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await list_resource("quote_scenarios", agency_id, db, airline_code=airline_code, domain_code=domain_code, family_code=family_code, variant_code=variant_code)


@router.post("/quote-scenarios", status_code=status.HTTP_201_CREATED)
async def create_agency_quote_scenario(
    agency_id: str,
    payload: AirlineServicePriceQuoteScenarioCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    scenario = await AncillaryPricingService(db).create_record("quote_scenarios", payload, user, agency_id=agency_id)
    return {
        "quote_scenario": scenario,
        "invoice_payment_settlement_disabled": True,
        "emd_issuance_disabled": True,
        "provider_execution_disabled": True,
    }


@router.get("/quote-results")
async def list_agency_quote_results(
    agency_id: str,
    scenario_id: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await list_resource("quote_results", agency_id, db, scenario_id=scenario_id)


@router.get("/candidate-pricing-links")
async def list_agency_candidate_pricing_links(
    agency_id: str,
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await list_resource("candidate_pricing_links", agency_id, db, airline_code=airline_code, domain_code=domain_code, family_code=family_code, variant_code=variant_code, include_archived=include_archived)


@router.post("/candidate-pricing-links", status_code=status.HTTP_201_CREATED)
async def create_agency_candidate_pricing_link(
    agency_id: str,
    payload: PolicyCandidatePricingLinkCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    link = await AncillaryPricingService(db).create_record("candidate_pricing_links", payload, user, agency_id=agency_id)
    return {
        "link": link,
        "agency_auto_promotion_disabled": True,
        "agency_global_mutation_disabled": True,
    }
