from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import KnowledgeQualityAssuranceReviewCreate, KnowledgeQualityAssuranceReviewUpdate
from services.knowledge_quality_assurance_service import (
    PHASE_LABEL,
    KnowledgeQualityAssuranceError,
    KnowledgeQualityAssuranceService,
)
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(tags=["agency-knowledge-quality-assurance"])

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


@router.get("/api/agencies/{agency_id}/knowledge-quality-assurance")
async def list_agency_knowledge_quality_assurance_reviews(
    agency_id: str,
    target_type: str | None = Query(default=None),
    target_id: str | None = Query(default=None),
    airline_code: str | None = Query(default=None),
    service_family: str | None = Query(default=None),
    service_code: str | None = Query(default=None),
    qa_status: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    issue_check: str | None = Query(default=None),
    approval_recommendation: str | None = Query(default=None),
    search: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await KnowledgeQualityAssuranceService(db).agency_response(
        agency_id,
        target_type=target_type,
        target_id=target_id,
        airline_code=airline_code,
        service_family=service_family,
        service_code=service_code,
        qa_status=qa_status,
        severity=severity,
        issue_check=issue_check,
        approval_recommendation=approval_recommendation,
        search=search,
        include_archived=include_archived,
    )


@router.get("/api/agencies/{agency_id}/knowledge-quality-assurance/summary")
async def summarize_agency_knowledge_quality_assurance_reviews(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await KnowledgeQualityAssuranceService(db).agency_summary(agency_id)


@router.post("/api/agencies/{agency_id}/knowledge-quality-assurance", status_code=status.HTTP_201_CREATED)
async def create_agency_knowledge_quality_assurance_review(
    agency_id: str,
    payload: KnowledgeQualityAssuranceReviewCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await KnowledgeQualityAssuranceService(db).create_review(payload, user, agency_id=agency_id)
    except KnowledgeQualityAssuranceError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/api/agencies/{agency_id}/knowledge-quality-assurance/{review_id}")
async def get_agency_knowledge_quality_assurance_review(
    agency_id: str,
    review_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = KnowledgeQualityAssuranceService(db)
    try:
        review = await service.get_review(review_id, agency_id=agency_id)
    except KnowledgeQualityAssuranceError:
        raise not_found("Knowledge QA review metadata not found.")
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "knowledge_quality_assurance_review": review, "metadata_only": True, **service.safety_flags()}


@router.put("/api/agencies/{agency_id}/knowledge-quality-assurance/{review_id}")
async def update_agency_knowledge_quality_assurance_review(
    agency_id: str,
    review_id: str,
    payload: KnowledgeQualityAssuranceReviewUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await KnowledgeQualityAssuranceService(db).update_review(review_id, payload, user, agency_id=agency_id)
    except KnowledgeQualityAssuranceError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/api/agencies/{agency_id}/knowledge-quality-assurance/{review_id}")
async def archive_agency_knowledge_quality_assurance_review(
    agency_id: str,
    review_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await KnowledgeQualityAssuranceService(db).archive_review(review_id, user, agency_id=agency_id)
    except KnowledgeQualityAssuranceError as exc:
        raise bad_request(str(exc)) from exc
