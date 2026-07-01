from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    AirlineServiceAliasCreate,
    AirlineServiceAliasUpdate,
    CanonicalServiceDomainCreate,
    CanonicalServiceDomainUpdate,
    CanonicalServiceFamilyCreate,
    CanonicalServiceFamilyUpdate,
    CanonicalServiceVariantCreate,
    CanonicalServiceVariantUpdate,
    PolicyCandidateTaxonomyLinkCreate,
    PolicyCandidateTaxonomyLinkUpdate,
    ServiceTaxonomyMapCandidateRequest,
    ServiceTaxonomyMappingRuleCreate,
    ServiceTaxonomyMappingRuleUpdate,
    ServiceTaxonomyReviewCorrectionCreate,
)
from services.service_taxonomy_service import ServiceTaxonomyService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/service-taxonomy", tags=["platform-service-taxonomy"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def conflict_or_raise(exc: ValueError) -> None:
    if str(exc) in {"domain_exists", "family_exists", "variant_exists"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc).replace("_", " "))
    raise exc


@router.get("/summary")
async def get_platform_service_taxonomy_summary(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await ServiceTaxonomyService(db).summary()


@router.post("/seed-baseline", status_code=status.HTTP_201_CREATED)
async def seed_platform_service_taxonomy_baseline(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await ServiceTaxonomyService(db).seed_baseline(user)


@router.get("/domains")
async def list_platform_service_domains(
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {"items": await ServiceTaxonomyService(db).list_domains(include_archived=include_archived)}


@router.post("/domains", status_code=status.HTTP_201_CREATED)
async def create_platform_service_domain(
    payload: CanonicalServiceDomainCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        domain = await ServiceTaxonomyService(db).create_domain(payload, user)
    except ValueError as exc:
        conflict_or_raise(exc)
    return {"domain": domain}


@router.patch("/domains/{domain_id}")
async def update_platform_service_domain(
    domain_id: str,
    payload: CanonicalServiceDomainUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    domain = await ServiceTaxonomyService(db).update_domain(domain_id, payload, user)
    if not domain:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service domain not found.")
    return {"domain": domain}


@router.get("/families")
async def list_platform_service_families(
    domain_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {"items": await ServiceTaxonomyService(db).list_families(domain_code=domain_code, include_archived=include_archived)}


@router.post("/families", status_code=status.HTTP_201_CREATED)
async def create_platform_service_family(
    payload: CanonicalServiceFamilyCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        family = await ServiceTaxonomyService(db).create_family(payload)
    except ValueError as exc:
        conflict_or_raise(exc)
    return {"family": family}


@router.patch("/families/{family_id}")
async def update_platform_service_family(
    family_id: str,
    payload: CanonicalServiceFamilyUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    family = await ServiceTaxonomyService(db).update_family(family_id, payload)
    if not family:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service family not found.")
    return {"family": family}


@router.get("/variants")
async def list_platform_service_variants(
    domain_code: str | None = None,
    family_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {"items": await ServiceTaxonomyService(db).list_variants(domain_code=domain_code, family_code=family_code, include_archived=include_archived)}


@router.post("/variants", status_code=status.HTTP_201_CREATED)
async def create_platform_service_variant(
    payload: CanonicalServiceVariantCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        variant = await ServiceTaxonomyService(db).create_variant(payload)
    except ValueError as exc:
        conflict_or_raise(exc)
    return {"variant": variant}


@router.patch("/variants/{variant_id}")
async def update_platform_service_variant(
    variant_id: str,
    payload: CanonicalServiceVariantUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    variant = await ServiceTaxonomyService(db).update_variant(variant_id, payload)
    if not variant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service variant not found.")
    return {"variant": variant}


@router.get("/aliases")
async def list_platform_service_aliases(
    airline_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {"items": await ServiceTaxonomyService(db).list_aliases(airline_code=airline_code, include_archived=include_archived)}


@router.post("/aliases", status_code=status.HTTP_201_CREATED)
async def create_platform_service_alias(
    payload: AirlineServiceAliasCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return {"alias": await ServiceTaxonomyService(db).create_alias(payload)}


@router.patch("/aliases/{alias_id}")
async def update_platform_service_alias(
    alias_id: str,
    payload: AirlineServiceAliasUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    alias = await ServiceTaxonomyService(db).update_alias(alias_id, payload)
    if not alias:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service alias not found.")
    return {"alias": alias}


@router.get("/applicability-dimensions")
async def list_platform_applicability_dimensions(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {"items": await ServiceTaxonomyService(db).list_applicability_dimensions()}


@router.get("/outcome-types")
async def list_platform_outcome_types(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {"items": await ServiceTaxonomyService(db).list_outcome_types()}


@router.get("/mapping-rules")
async def list_platform_mapping_rules(
    airline_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {"items": await ServiceTaxonomyService(db).list_mapping_rules(airline_code=airline_code, include_archived=include_archived)}


@router.post("/mapping-rules", status_code=status.HTTP_201_CREATED)
async def create_platform_mapping_rule(
    payload: ServiceTaxonomyMappingRuleCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return {"mapping_rule": await ServiceTaxonomyService(db).create_mapping_rule(payload, user)}


@router.patch("/mapping-rules/{rule_id}")
async def update_platform_mapping_rule(
    rule_id: str,
    payload: ServiceTaxonomyMappingRuleUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    rule = await ServiceTaxonomyService(db).update_mapping_rule(rule_id, payload)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mapping rule not found.")
    return {"mapping_rule": rule}


@router.post("/map-candidate")
async def map_platform_service_candidate(
    payload: ServiceTaxonomyMapCandidateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await ServiceTaxonomyService(db).map_candidate_text(payload.text, airline_code=payload.airline_code)


@router.get("/candidate-links")
async def list_platform_candidate_links(
    candidate_type: str | None = None,
    candidate_id: str | None = None,
    policy_source_id: str | None = None,
    extraction_run_id: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await ServiceTaxonomyService(db).list_candidate_links(
            candidate_type=candidate_type,
            candidate_id=candidate_id,
            policy_source_id=policy_source_id,
            extraction_run_id=extraction_run_id,
        )
    }


@router.post("/candidate-links", status_code=status.HTTP_201_CREATED)
async def create_platform_candidate_link(
    payload: PolicyCandidateTaxonomyLinkCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await ServiceTaxonomyService(db).create_candidate_link(payload, user)


@router.patch("/candidate-links/{link_id}")
async def update_platform_candidate_link(
    link_id: str,
    payload: PolicyCandidateTaxonomyLinkUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    link = await ServiceTaxonomyService(db).update_candidate_link(link_id, payload)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate taxonomy link not found.")
    return {"link": link}


@router.get("/review-corrections")
async def list_platform_review_corrections(
    candidate_type: str | None = None,
    candidate_id: str | None = None,
    promotion_status: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await ServiceTaxonomyService(db).list_review_corrections(
            candidate_type=candidate_type,
            candidate_id=candidate_id,
            promotion_status=promotion_status,
        )
    }


@router.post("/review-corrections", status_code=status.HTTP_201_CREATED)
async def create_platform_review_correction(
    payload: ServiceTaxonomyReviewCorrectionCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await ServiceTaxonomyService(db).create_review_correction(payload, user)
