from __future__ import annotations

from fastapi import APIRouter, Depends, Query, HTTPException, status

from auth import get_current_user
from database import Database, get_database
from models import (
    PolicyCandidateTaxonomyLinkCreate,
    PolicyCandidateTaxonomyLinkUpdate,
    ServiceTaxonomyMapCandidateRequest,
    ServiceTaxonomyReviewCorrectionCreate,
)
from services.service_taxonomy_service import ServiceTaxonomyService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/service-taxonomy", tags=["agency-service-taxonomy"])

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


@router.get("/summary")
async def get_agency_service_taxonomy_summary(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    summary = await ServiceTaxonomyService(db).summary(agency_id=agency_id)
    return {
        **summary,
        "platform_taxonomy_read_only": True,
        "agency_global_mutation_disabled": True,
    }


@router.get("/domains")
async def list_agency_service_domains(
    agency_id: str,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await ServiceTaxonomyService(db).list_domains(include_archived=include_archived), "read_only": True}


@router.get("/families")
async def list_agency_service_families(
    agency_id: str,
    domain_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {
        "items": await ServiceTaxonomyService(db).list_families(domain_code=domain_code, include_archived=include_archived),
        "read_only": True,
    }


@router.get("/variants")
async def list_agency_service_variants(
    agency_id: str,
    domain_code: str | None = None,
    family_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {
        "items": await ServiceTaxonomyService(db).list_variants(domain_code=domain_code, family_code=family_code, include_archived=include_archived),
        "read_only": True,
    }


@router.get("/aliases")
async def list_agency_service_aliases(
    agency_id: str,
    airline_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {
        "items": await ServiceTaxonomyService(db).list_aliases(airline_code=airline_code, agency_id=agency_id, include_archived=include_archived),
        "read_only": True,
    }


@router.get("/applicability-dimensions")
async def list_agency_applicability_dimensions(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await ServiceTaxonomyService(db).list_applicability_dimensions(), "read_only": True}


@router.get("/outcome-types")
async def list_agency_outcome_types(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await ServiceTaxonomyService(db).list_outcome_types(), "read_only": True}


@router.get("/mapping-rules")
async def list_agency_mapping_rules(
    agency_id: str,
    airline_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {
        "items": await ServiceTaxonomyService(db).list_mapping_rules(airline_code=airline_code, agency_id=agency_id, include_archived=include_archived),
        "read_only": True,
    }


@router.post("/map-candidate")
async def map_agency_service_candidate(
    agency_id: str,
    payload: ServiceTaxonomyMapCandidateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await ServiceTaxonomyService(db).map_candidate_text(payload.text, airline_code=payload.airline_code, agency_id=agency_id)


@router.get("/candidate-links")
async def list_agency_candidate_links(
    agency_id: str,
    candidate_type: str | None = None,
    candidate_id: str | None = None,
    policy_source_id: str | None = None,
    extraction_run_id: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {
        "items": await ServiceTaxonomyService(db).list_candidate_links(
            agency_id=agency_id,
            candidate_type=candidate_type,
            candidate_id=candidate_id,
            policy_source_id=policy_source_id,
            extraction_run_id=extraction_run_id,
        )
    }


@router.post("/candidate-links", status_code=status.HTTP_201_CREATED)
async def create_agency_candidate_link(
    agency_id: str,
    payload: PolicyCandidateTaxonomyLinkCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    return await ServiceTaxonomyService(db).create_candidate_link(payload, user, agency_id=agency_id)


@router.patch("/candidate-links/{link_id}")
async def update_agency_candidate_link(
    agency_id: str,
    link_id: str,
    payload: PolicyCandidateTaxonomyLinkUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    link = await ServiceTaxonomyService(db).update_candidate_link(link_id, payload, agency_id=agency_id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate taxonomy link not found.")
    return {"link": link}


@router.get("/review-corrections")
async def list_agency_review_corrections(
    agency_id: str,
    candidate_type: str | None = None,
    candidate_id: str | None = None,
    promotion_status: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {
        "items": await ServiceTaxonomyService(db).list_review_corrections(
            agency_id=agency_id,
            candidate_type=candidate_type,
            candidate_id=candidate_id,
            promotion_status=promotion_status,
        )
    }


@router.post("/review-corrections", status_code=status.HTTP_201_CREATED)
async def create_agency_review_correction(
    agency_id: str,
    payload: ServiceTaxonomyReviewCorrectionCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    return await ServiceTaxonomyService(db).create_review_correction(payload, user, agency_id=agency_id)
