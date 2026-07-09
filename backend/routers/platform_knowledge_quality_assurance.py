from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import KnowledgeQualityAssuranceReviewCreate, KnowledgeQualityAssuranceReviewUpdate
from services.knowledge_quality_assurance_service import (
    PHASE_LABEL,
    KnowledgeQualityAssuranceError,
    KnowledgeQualityAssuranceService,
)
from services.tenant_service import require_any_platform_role


router = APIRouter(tags=["platform-knowledge-quality-assurance"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("/api/platform/knowledge-quality-assurance")
async def list_platform_knowledge_quality_assurance_reviews(
    agency_id: str | None = Query(default=None),
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
    await require_platform_read(user)
    return await KnowledgeQualityAssuranceService(db).platform_response(
        agency_id=agency_id,
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


@router.get("/api/platform/knowledge-quality-assurance/summary")
async def summarize_platform_knowledge_quality_assurance_reviews(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await KnowledgeQualityAssuranceService(db).platform_summary(agency_id)


@router.post("/api/platform/knowledge-quality-assurance", status_code=status.HTTP_201_CREATED)
async def create_platform_knowledge_quality_assurance_review(
    payload: KnowledgeQualityAssuranceReviewCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await KnowledgeQualityAssuranceService(db).create_review(payload, user)
    except KnowledgeQualityAssuranceError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/api/platform/knowledge-quality-assurance/{review_id}")
async def get_platform_knowledge_quality_assurance_review(
    review_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = KnowledgeQualityAssuranceService(db)
    try:
        review = await service.get_review(review_id)
    except KnowledgeQualityAssuranceError as exc:
        raise bad_request(str(exc)) from exc
    return {"phase": PHASE_LABEL, "knowledge_quality_assurance_review": review, "metadata_only": True, **service.safety_flags()}


@router.put("/api/platform/knowledge-quality-assurance/{review_id}")
async def update_platform_knowledge_quality_assurance_review(
    review_id: str,
    payload: KnowledgeQualityAssuranceReviewUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await KnowledgeQualityAssuranceService(db).update_review(review_id, payload, user)
    except KnowledgeQualityAssuranceError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/api/platform/knowledge-quality-assurance/{review_id}")
async def archive_platform_knowledge_quality_assurance_review(
    review_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await KnowledgeQualityAssuranceService(db).archive_review(review_id, user)
    except KnowledgeQualityAssuranceError as exc:
        raise bad_request(str(exc)) from exc
