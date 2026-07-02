from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    AirlineAncillaryPriceComponentCreate,
    AirlineAncillaryPriceComponentUpdate,
    AirlineAncillaryPricingApplicabilityCreate,
    AirlineAncillaryPricingApplicabilityUpdate,
    AirlineAncillaryPricingMatrixCreate,
    AirlineAncillaryPricingMatrixRowCreate,
    AirlineAncillaryPricingMatrixRowUpdate,
    AirlineAncillaryPricingMatrixUpdate,
    AirlineAncillaryPricingRuleCreate,
    AirlineAncillaryPricingRuleUpdate,
    AirlineServiceExceptionRuleCreate,
    AirlineServiceExceptionRuleUpdate,
    AirlineServicePriceQuoteEvaluationRequest,
    AirlineServicePriceQuoteScenarioCreate,
    AncillaryPricingLookupRequest,
    PolicyCandidatePricingLinkCreate,
    PolicyCandidatePricingLinkUpdate,
)
from services.ancillary_pricing_service import RESOURCE_SPECS, AncillaryPricingService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/ancillary-pricing", tags=["platform-ancillary-pricing"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def response_key(resource: str) -> str:
    return RESOURCE_SPECS[resource]["singular"]


async def list_resource(
    resource: str,
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
            airline_code=airline_code,
            domain_code=domain_code,
            family_code=family_code,
            variant_code=variant_code,
            pricing_rule_id=pricing_rule_id,
            matrix_id=matrix_id,
            scenario_id=scenario_id,
            include_archived=include_archived,
        )
    }


async def create_resource(resource: str, payload: Any, user: dict, db: Database) -> dict:
    record = await AncillaryPricingService(db).create_record(resource, payload, user)
    return {response_key(resource): record}


async def update_resource(resource: str, record_id: str, payload: Any, db: Database) -> dict:
    record = await AncillaryPricingService(db).update_record(resource, record_id, payload)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ancillary pricing record not found.")
    return {response_key(resource): record}


@router.get("/summary")
async def get_platform_ancillary_pricing_summary(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AncillaryPricingService(db).summary()


@router.post("/lookup")
async def lookup_platform_ancillary_pricing(
    payload: AncillaryPricingLookupRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AncillaryPricingService(db).lookup(**payload.model_dump(mode="json"))


@router.post("/evaluate")
async def evaluate_platform_ancillary_pricing(
    payload: AirlineServicePriceQuoteEvaluationRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AncillaryPricingService(db).evaluate(payload, user)


@router.get("/pricing-rules")
async def list_platform_pricing_rules(
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await list_resource("pricing_rules", db, airline_code=airline_code, domain_code=domain_code, family_code=family_code, variant_code=variant_code, include_archived=include_archived)


@router.post("/pricing-rules", status_code=status.HTTP_201_CREATED)
async def create_platform_pricing_rule(
    payload: AirlineAncillaryPricingRuleCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await create_resource("pricing_rules", payload, user, db)


@router.patch("/pricing-rules/{record_id}")
async def update_platform_pricing_rule(
    record_id: str,
    payload: AirlineAncillaryPricingRuleUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await update_resource("pricing_rules", record_id, payload, db)


@router.get("/price-components")
async def list_platform_price_components(
    pricing_rule_id: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await list_resource("price_components", db, pricing_rule_id=pricing_rule_id, include_archived=include_archived)


@router.post("/price-components", status_code=status.HTTP_201_CREATED)
async def create_platform_price_component(
    payload: AirlineAncillaryPriceComponentCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await create_resource("price_components", payload, user, db)


@router.patch("/price-components/{record_id}")
async def update_platform_price_component(
    record_id: str,
    payload: AirlineAncillaryPriceComponentUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await update_resource("price_components", record_id, payload, db)


@router.get("/applicability")
async def list_platform_applicability(
    pricing_rule_id: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await list_resource("applicability", db, pricing_rule_id=pricing_rule_id, include_archived=include_archived)


@router.post("/applicability", status_code=status.HTTP_201_CREATED)
async def create_platform_applicability(
    payload: AirlineAncillaryPricingApplicabilityCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await create_resource("applicability", payload, user, db)


@router.patch("/applicability/{record_id}")
async def update_platform_applicability(
    record_id: str,
    payload: AirlineAncillaryPricingApplicabilityUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await update_resource("applicability", record_id, payload, db)


@router.get("/pricing-matrices")
async def list_platform_pricing_matrices(
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await list_resource("pricing_matrices", db, airline_code=airline_code, domain_code=domain_code, family_code=family_code, variant_code=variant_code, include_archived=include_archived)


@router.post("/pricing-matrices", status_code=status.HTTP_201_CREATED)
async def create_platform_pricing_matrix(
    payload: AirlineAncillaryPricingMatrixCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await create_resource("pricing_matrices", payload, user, db)


@router.patch("/pricing-matrices/{record_id}")
async def update_platform_pricing_matrix(
    record_id: str,
    payload: AirlineAncillaryPricingMatrixUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await update_resource("pricing_matrices", record_id, payload, db)


@router.get("/pricing-matrix-rows")
async def list_platform_pricing_matrix_rows(
    matrix_id: str | None = None,
    pricing_rule_id: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await list_resource("pricing_matrix_rows", db, matrix_id=matrix_id, pricing_rule_id=pricing_rule_id, include_archived=include_archived)


@router.post("/pricing-matrix-rows", status_code=status.HTTP_201_CREATED)
async def create_platform_pricing_matrix_row(
    payload: AirlineAncillaryPricingMatrixRowCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await create_resource("pricing_matrix_rows", payload, user, db)


@router.patch("/pricing-matrix-rows/{record_id}")
async def update_platform_pricing_matrix_row(
    record_id: str,
    payload: AirlineAncillaryPricingMatrixRowUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await update_resource("pricing_matrix_rows", record_id, payload, db)


@router.get("/exception-rules")
async def list_platform_exception_rules(
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await list_resource("exception_rules", db, airline_code=airline_code, domain_code=domain_code, family_code=family_code, variant_code=variant_code, include_archived=include_archived)


@router.post("/exception-rules", status_code=status.HTTP_201_CREATED)
async def create_platform_exception_rule(
    payload: AirlineServiceExceptionRuleCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await create_resource("exception_rules", payload, user, db)


@router.patch("/exception-rules/{record_id}")
async def update_platform_exception_rule(
    record_id: str,
    payload: AirlineServiceExceptionRuleUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await update_resource("exception_rules", record_id, payload, db)


@router.get("/quote-scenarios")
async def list_platform_quote_scenarios(
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await list_resource("quote_scenarios", db, airline_code=airline_code, domain_code=domain_code, family_code=family_code, variant_code=variant_code)


@router.post("/quote-scenarios", status_code=status.HTTP_201_CREATED)
async def create_platform_quote_scenario(
    payload: AirlineServicePriceQuoteScenarioCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await create_resource("quote_scenarios", payload, user, db)


@router.get("/quote-results")
async def list_platform_quote_results(
    scenario_id: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await list_resource("quote_results", db, scenario_id=scenario_id)


@router.get("/candidate-pricing-links")
async def list_platform_candidate_pricing_links(
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await list_resource("candidate_pricing_links", db, airline_code=airline_code, domain_code=domain_code, family_code=family_code, variant_code=variant_code, include_archived=include_archived)


@router.post("/candidate-pricing-links", status_code=status.HTTP_201_CREATED)
async def create_platform_candidate_pricing_link(
    payload: PolicyCandidatePricingLinkCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await create_resource("candidate_pricing_links", payload, user, db)


@router.patch("/candidate-pricing-links/{record_id}")
async def update_platform_candidate_pricing_link(
    record_id: str,
    payload: PolicyCandidatePricingLinkUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await update_resource("candidate_pricing_links", record_id, payload, db)
