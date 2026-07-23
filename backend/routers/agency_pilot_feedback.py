from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import CommercialPilotFeedbackCreate
from services.commercial_pilot_readiness_service import (
    CommercialPilotReadinessError,
    CommercialPilotReadinessService,
)
from services.tenant_service import require_any_agency_role


router = APIRouter(
    prefix="/api/agencies/{agency_id}/pilot-feedback",
    tags=["agency-commercial-pilot-feedback"],
)
READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant"]


async def authorize(db: Database, agency_id: str, user: dict, *, write: bool) -> dict:
    platform_roles = {"platform_owner", "platform_admin"} if write else {
        "platform_owner",
        "platform_admin",
        "platform_support",
    }
    if user.get("global_role") in platform_roles:
        return {"agency_role": "platform_override"}
    return await require_any_agency_role(
        db, agency_id, user, WRITE_ROLES if write else READ_ROLES
    )


def service_error(exc: CommercialPilotReadinessError) -> HTTPException:
    code = status.HTTP_404_NOT_FOUND if str(exc) == "Pilot feedback not found." else status.HTTP_400_BAD_REQUEST
    return HTTPException(status_code=code, detail=str(exc))


@router.get("")
async def list_agency_pilot_feedback(
    agency_id: str,
    feedback_status: str | None = Query(default=None, alias="status"),
    category: str | None = Query(default=None),
    affected_area: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    membership = await authorize(db, agency_id, user, write=False)
    try:
        response = await CommercialPilotReadinessService(db).list_agency_feedback(
            agency_id,
            status=feedback_status,
            category=category,
            affected_area=affected_area,
        )
        response["permissions"] = {
            "can_submit": membership.get("agency_role") in {*WRITE_ROLES, "platform_override"},
            "can_review": False,
        }
        return response
    except CommercialPilotReadinessError as exc:
        raise service_error(exc) from exc


@router.post("", status_code=status.HTTP_201_CREATED)
async def submit_agency_pilot_feedback(
    agency_id: str,
    payload: CommercialPilotFeedbackCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await authorize(db, agency_id, user, write=True)
    try:
        return await CommercialPilotReadinessService(db).submit_feedback(agency_id, payload, user)
    except CommercialPilotReadinessError as exc:
        raise service_error(exc) from exc


@router.get("/{feedback_id}")
async def get_agency_pilot_feedback(
    agency_id: str,
    feedback_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await authorize(db, agency_id, user, write=False)
    try:
        return await CommercialPilotReadinessService(db).get_agency_feedback(
            agency_id, feedback_id
        )
    except CommercialPilotReadinessError as exc:
        raise service_error(exc) from exc
