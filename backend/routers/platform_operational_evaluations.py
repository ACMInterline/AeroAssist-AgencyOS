from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import OperationalKnowledgeEvaluationCreate, OperationalKnowledgeEvaluationUpdate
from services.operational_knowledge_evaluation_service import (
    PHASE_LABEL,
    OperationalKnowledgeEvaluationError,
    OperationalKnowledgeEvaluationService,
)
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/operational-evaluations", tags=["platform-operational-evaluations"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_platform_operational_evaluations(
    agency_id: str | None = Query(default=None),
    evaluation_status: str | None = Query(default=None),
    evaluation_type: str | None = Query(default=None),
    airline: str | None = Query(default=None),
    passenger: str | None = Query(default=None),
    travel_request_id: str | None = Query(default=None),
    trip_workspace_id: str | None = Query(default=None),
    booking_workspace_id: str | None = Query(default=None),
    service_domain: str | None = Query(default=None),
    service_family: str | None = Query(default=None),
    ssr_code: str | None = Query(default=None),
    capability_result: str | None = Query(default=None),
    policy_result: str | None = Query(default=None),
    pricing_result: str | None = Query(default=None),
    constraint_result: str | None = Query(default=None),
    operational_result: str | None = Query(default=None),
    operational_risk: str | None = Query(default=None),
    confidence: str | None = Query(default=None),
    evaluation_completed: bool | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await OperationalKnowledgeEvaluationService(db).platform_response(
        agency_id=agency_id,
        evaluation_status=evaluation_status,
        evaluation_type=evaluation_type,
        airline=airline,
        passenger=passenger,
        travel_request_id=travel_request_id,
        trip_workspace_id=trip_workspace_id,
        booking_workspace_id=booking_workspace_id,
        service_domain=service_domain,
        service_family=service_family,
        ssr_code=ssr_code,
        capability_result=capability_result,
        policy_result=policy_result,
        pricing_result=pricing_result,
        constraint_result=constraint_result,
        operational_result=operational_result,
        operational_risk=operational_risk,
        confidence=confidence,
        evaluation_completed=evaluation_completed,
        include_archived=include_archived,
    )


@router.get("/summary")
async def summarize_platform_operational_evaluations(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await OperationalKnowledgeEvaluationService(db).platform_summary()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_platform_operational_evaluation(
    payload: OperationalKnowledgeEvaluationCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalKnowledgeEvaluationService(db).create_evaluation(payload, user)
    except OperationalKnowledgeEvaluationError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{evaluation_id}")
async def get_platform_operational_evaluation(
    evaluation_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OperationalKnowledgeEvaluationService(db)
    try:
        evaluation = await service.get_platform_evaluation(evaluation_id)
    except OperationalKnowledgeEvaluationError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "operational_knowledge_evaluation": evaluation,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{evaluation_id}")
async def update_platform_operational_evaluation(
    evaluation_id: str,
    payload: OperationalKnowledgeEvaluationUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalKnowledgeEvaluationService(db).update_evaluation(evaluation_id, payload, user)
    except OperationalKnowledgeEvaluationError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/{evaluation_id}")
async def archive_platform_operational_evaluation(
    evaluation_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalKnowledgeEvaluationService(db).archive_evaluation(evaluation_id, user)
    except OperationalKnowledgeEvaluationError as exc:
        raise bad_request(str(exc)) from exc
