from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    AirlinePolicyExtractionRequest,
    AirlinePolicyPromoteCandidateRequest,
    AirlinePolicyReviewCorrectionCreate,
    AirlinePolicySourceCreate,
)
from services.airline_policy_ingestion_service import AirlinePolicyIngestionService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/airline-policy", tags=["platform-airline-policy-ingestion"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]
PLATFORM_PROMOTE_ROLES = ["platform_owner", "platform_admin"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


async def require_platform_promote(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_PROMOTE_ROLES)


def filters_from(**kwargs: Any) -> dict[str, Any]:
    return {key: value for key, value in kwargs.items() if value not in {None, ""}}


@router.get("/sources")
async def list_platform_policy_sources(
    airline_id: str | None = None,
    airline_iata_code: str | None = None,
    service_domain: str | None = None,
    service_family: str | None = None,
    ingestion_status: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AirlinePolicyIngestionService(db).list_policy_sources(
        filters_from(
            scope="platform",
            airline_id=airline_id,
            airline_iata_code=airline_iata_code,
            service_domain=service_domain,
            service_family=service_family,
            ingestion_status=ingestion_status,
        )
    )


@router.post("/sources", status_code=status.HTTP_201_CREATED)
async def create_platform_policy_source(
    payload: AirlinePolicySourceCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return await AirlinePolicyIngestionService(db).create_policy_source(
        {**payload.model_dump(mode="json"), "scope": "platform", "agency_id": None},
        user,
    )


@router.get("/sources/{policy_source_id}")
async def get_platform_policy_source(
    policy_source_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = AirlinePolicyIngestionService(db)
    source = await service.get_policy_source(policy_source_id)
    if not source or source.get("scope") != "platform":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy source not found.")
    sections = await db.collection("airline_policy_sections").find_many({"policy_source_id": policy_source_id})
    runs = await service.list_extraction_runs({"policy_source_id": policy_source_id})
    candidates = await service.list_extracted_candidates(policy_source_id)
    return {"policy_source": source, "sections": sections, "extraction_runs": runs.get("items") or [], "candidates": candidates}


@router.post("/sources/{policy_source_id}/detect-sections")
async def detect_platform_policy_sections(
    policy_source_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    result = await AirlinePolicyIngestionService(db).detect_sections(policy_source_id, user)
    if not result or (result.get("policy_source") or {}).get("scope") != "platform":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy source not found.")
    return result


@router.post("/sources/{policy_source_id}/extract", status_code=status.HTTP_201_CREATED)
async def extract_platform_policy_source(
    policy_source_id: str,
    payload: AirlinePolicyExtractionRequest | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    result = await AirlinePolicyIngestionService(db).run_extraction(policy_source_id, payload or {}, user)
    if not result or (result.get("policy_source") or {}).get("scope") != "platform":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy source not found.")
    return result


@router.get("/sources/{policy_source_id}/candidates")
async def list_platform_policy_candidates(
    policy_source_id: str,
    extraction_run_id: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    source = await AirlinePolicyIngestionService(db).get_policy_source(policy_source_id)
    if not source or source.get("scope") != "platform":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy source not found.")
    return await AirlinePolicyIngestionService(db).list_extracted_candidates(policy_source_id, extraction_run_id)


@router.get("/extraction-runs")
async def list_platform_policy_extraction_runs(
    policy_source_id: str | None = None,
    airline_id: str | None = None,
    extraction_status: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AirlinePolicyIngestionService(db).list_extraction_runs(
        filters_from(policy_source_id=policy_source_id, airline_id=airline_id, extraction_status=extraction_status)
    )


@router.get("/extraction-runs/{extraction_run_id}")
async def get_platform_policy_extraction_run(
    extraction_run_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = AirlinePolicyIngestionService(db)
    extraction_run = await service.get_extraction_run(extraction_run_id)
    if not extraction_run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Extraction run not found.")
    source = await service.get_policy_source(extraction_run["policy_source_id"])
    if not source or source.get("scope") != "platform":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Extraction run not found.")
    candidates = await service.list_extracted_candidates(extraction_run["policy_source_id"], extraction_run_id)
    return {"extraction_run": extraction_run, "policy_source": source, "candidates": candidates}


@router.post("/review-corrections", status_code=status.HTTP_201_CREATED)
async def apply_platform_policy_review_correction(
    payload: AirlinePolicyReviewCorrectionCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    result = await AirlinePolicyIngestionService(db).apply_review_correction(payload, user)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review target not found.")
    return result


@router.post("/promote-candidate", status_code=status.HTTP_201_CREATED)
async def promote_platform_policy_candidate(
    payload: AirlinePolicyPromoteCandidateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_promote(user)
    result = await AirlinePolicyIngestionService(db).promote_candidate(payload, user)
    if not result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Accepted or corrected candidate is required for promotion.")
    return result


@router.post("/sources/{policy_source_id}/promote-accepted", status_code=status.HTTP_201_CREATED)
async def promote_platform_policy_accepted_candidates(
    policy_source_id: str,
    payload: dict[str, Any] | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_promote(user)
    extraction_run_id = (payload or {}).get("extraction_run_id")
    if not extraction_run_id:
        runs = (await AirlinePolicyIngestionService(db).list_extraction_runs({"policy_source_id": policy_source_id})).get("items") or []
        extraction_run_id = runs[0]["id"] if runs else None
    if not extraction_run_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Extraction run is required.")
    return await AirlinePolicyIngestionService(db).promote_accepted_candidates(policy_source_id, extraction_run_id, user)


@router.get("/approved-knowledge")
async def list_platform_policy_approved_knowledge(
    airline_id: str | None = None,
    service_domain: str | None = None,
    service_family: str | None = None,
    knowledge_type: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AirlinePolicyIngestionService(db).list_approved_knowledge(
        filters_from(
            airline_id=airline_id,
            service_domain=service_domain,
            service_family=service_family,
            knowledge_type=knowledge_type,
            status=status_filter,
        )
    )
