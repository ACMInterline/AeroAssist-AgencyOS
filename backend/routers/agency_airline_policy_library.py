from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import AirlinePolicyExtractionRequest, AirlinePolicyReviewCorrectionCreate, AirlinePolicySourceCreate
from services.airline_policy_ingestion_service import AirlinePolicyIngestionService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/airline-policy", tags=["agency-airline-policy-library"])

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


def filters_from(**kwargs: Any) -> dict[str, Any]:
    return {key: value for key, value in kwargs.items() if value not in {None, ""}}


async def _agency_source_or_404(db: Database, agency_id: str, policy_source_id: str) -> dict[str, Any]:
    source = await AirlinePolicyIngestionService(db).get_policy_source(policy_source_id)
    if not source or source.get("scope") != "agency" or source.get("agency_id") != agency_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy source not found.")
    return source


@router.get("/library")
async def get_agency_policy_library(
    agency_id: str,
    airline_id: str | None = None,
    service_domain: str | None = None,
    service_family: str | None = None,
    knowledge_type: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AirlinePolicyIngestionService(db)
    approved = await service.list_approved_knowledge(
        filters_from(
            airline_id=airline_id,
            service_domain=service_domain,
            service_family=service_family,
            knowledge_type=knowledge_type,
            status="approved",
        )
    )
    local_sources = await service.list_policy_sources({"scope": "agency", "agency_id": agency_id})
    return {
        "approved_knowledge": approved.get("items") or [],
        "local_sources": local_sources.get("items") or [],
        "platform_knowledge_read_only": True,
        "agency_global_promotion_disabled": True,
    }


@router.get("/sources")
async def list_agency_policy_sources(
    agency_id: str,
    airline_id: str | None = None,
    airline_iata_code: str | None = None,
    service_domain: str | None = None,
    service_family: str | None = None,
    ingestion_status: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await AirlinePolicyIngestionService(db).list_policy_sources(
        filters_from(
            scope="agency",
            agency_id=agency_id,
            airline_id=airline_id,
            airline_iata_code=airline_iata_code,
            service_domain=service_domain,
            service_family=service_family,
            ingestion_status=ingestion_status,
        )
    )


@router.post("/sources", status_code=status.HTTP_201_CREATED)
async def create_agency_policy_source(
    agency_id: str,
    payload: AirlinePolicySourceCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    return await AirlinePolicyIngestionService(db).create_policy_source(
        {**payload.model_dump(mode="json"), "scope": "agency", "agency_id": agency_id},
        user,
    )


@router.get("/sources/{policy_source_id}")
async def get_agency_policy_source(
    agency_id: str,
    policy_source_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    source = await _agency_source_or_404(db, agency_id, policy_source_id)
    service = AirlinePolicyIngestionService(db)
    sections = await db.collection("airline_policy_sections").find_many({"policy_source_id": policy_source_id})
    runs = await service.list_extraction_runs({"policy_source_id": policy_source_id})
    candidates = await service.list_extracted_candidates(policy_source_id)
    return {"policy_source": source, "sections": sections, "extraction_runs": runs.get("items") or [], "candidates": candidates}


@router.post("/sources/{policy_source_id}/detect-sections")
async def detect_agency_policy_sections(
    agency_id: str,
    policy_source_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    await _agency_source_or_404(db, agency_id, policy_source_id)
    result = await AirlinePolicyIngestionService(db).detect_sections(policy_source_id, user)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy source not found.")
    return result


@router.post("/sources/{policy_source_id}/extract", status_code=status.HTTP_201_CREATED)
async def extract_agency_policy_source(
    agency_id: str,
    policy_source_id: str,
    payload: AirlinePolicyExtractionRequest | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    await _agency_source_or_404(db, agency_id, policy_source_id)
    result = await AirlinePolicyIngestionService(db).run_extraction(policy_source_id, payload or {}, user)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy source not found.")
    return result


@router.get("/sources/{policy_source_id}/candidates")
async def list_agency_policy_candidates(
    agency_id: str,
    policy_source_id: str,
    extraction_run_id: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    await _agency_source_or_404(db, agency_id, policy_source_id)
    return await AirlinePolicyIngestionService(db).list_extracted_candidates(policy_source_id, extraction_run_id)


@router.post("/review-corrections", status_code=status.HTTP_201_CREATED)
async def apply_agency_policy_review_correction(
    agency_id: str,
    payload: AirlinePolicyReviewCorrectionCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    await _agency_source_or_404(db, agency_id, payload.policy_source_id)
    result = await AirlinePolicyIngestionService(db).apply_review_correction(payload, user)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review target not found.")
    return {**result, "agency_global_promotion_disabled": True}


@router.post("/sources/{policy_source_id}/submit-for-platform-review")
async def submit_agency_policy_source_for_platform_review(
    agency_id: str,
    policy_source_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    await _agency_source_or_404(db, agency_id, policy_source_id)
    result = await AirlinePolicyIngestionService(db).submit_for_platform_review(policy_source_id, user)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy source not found.")
    return result
