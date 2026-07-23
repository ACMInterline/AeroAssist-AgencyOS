from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import CommercialPilotFeedbackReviewUpdate
from services.commercial_pilot_readiness_service import (
    CommercialPilotReadinessError,
    CommercialPilotReadinessService,
)
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/pilot-feedback", tags=["platform-commercial-pilot-feedback"])
READ_ROLES = ["platform_owner", "platform_admin", "platform_support"]
WRITE_ROLES = ["platform_owner", "platform_admin", "platform_support"]


def service_error(exc: CommercialPilotReadinessError) -> HTTPException:
    code = status.HTTP_404_NOT_FOUND if str(exc) == "Pilot feedback not found." else status.HTTP_400_BAD_REQUEST
    return HTTPException(status_code=code, detail=str(exc))


@router.get("")
async def list_platform_pilot_feedback(
    agency_id: str | None = Query(default=None),
    feedback_status: str | None = Query(default=None, alias="status"),
    category: str | None = Query(default=None),
    affected_area: str | None = Query(default=None),
    urgency: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_any_platform_role(user, READ_ROLES)
    return await CommercialPilotReadinessService(db).list_platform_feedback(
        agency_id=agency_id,
        status=feedback_status,
        category=category,
        affected_area=affected_area,
        urgency=urgency,
    )


@router.get("/{feedback_id}")
async def get_platform_pilot_feedback(
    feedback_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_any_platform_role(user, READ_ROLES)
    try:
        return await CommercialPilotReadinessService(db).get_platform_feedback(feedback_id)
    except CommercialPilotReadinessError as exc:
        raise service_error(exc) from exc


@router.patch("/{feedback_id}")
async def review_platform_pilot_feedback(
    feedback_id: str,
    payload: CommercialPilotFeedbackReviewUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_any_platform_role(user, WRITE_ROLES)
    try:
        return await CommercialPilotReadinessService(db).review_feedback(
            feedback_id, payload, user
        )
    except CommercialPilotReadinessError as exc:
        raise service_error(exc) from exc
