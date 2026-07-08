from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.operational_knowledge_evaluation_service import (
    PHASE_LABEL,
    OperationalKnowledgeEvaluationError,
    OperationalKnowledgeEvaluationService,
)
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/operational-evaluations", tags=["agency-operational-evaluations"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


@router.get("")
async def list_agency_operational_evaluations(
    agency_id: str,
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
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await OperationalKnowledgeEvaluationService(db).agency_response(
        agency_id,
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
    )


@router.get("/summary")
async def summarize_agency_operational_evaluations(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await OperationalKnowledgeEvaluationService(db).agency_summary(agency_id)


@router.get("/{evaluation_id}")
async def get_agency_operational_evaluation(
    agency_id: str,
    evaluation_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = OperationalKnowledgeEvaluationService(db)
    try:
        evaluation = await service.get_agency_evaluation(agency_id, evaluation_id)
    except OperationalKnowledgeEvaluationError:
        raise not_found("Operational knowledge evaluation metadata not found.")
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "operational_knowledge_evaluation": evaluation,
        "read_only": True,
        "metadata_only": True,
        **service.safety_flags(),
    }
