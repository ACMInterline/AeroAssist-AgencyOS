from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user
from database import Database, get_database
from models import (
    AgencyDemoWorkspaceGenerateRequest,
    AgencyOnboardingEmailStatusUpdate,
    AgencyOnboardingPreferencesUpdate,
    AgencyOnboardingProfileUpdate,
)
from services.agency_onboarding_service import AgencyOnboardingError, AgencyOnboardingService
from services.tenant_service import require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/onboarding", tags=["agency-onboarding"])
READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin"]


async def authorize(db: Database, agency_id: str, user: dict, *, write: bool) -> None:
    platform_roles = {"platform_owner", "platform_admin"} if write else {"platform_owner", "platform_admin", "platform_support"}
    if user.get("global_role") in platform_roles:
        return
    await require_any_agency_role(db, agency_id, user, WRITE_ROLES if write else READ_ROLES)


def run_service_error(exc: AgencyOnboardingError) -> HTTPException:
    detail = str(exc)
    status_code = status.HTTP_404_NOT_FOUND if detail in {"Agency not found."} else status.HTTP_400_BAD_REQUEST
    return HTTPException(status_code=status_code, detail=detail)


@router.get("")
async def get_onboarding(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await authorize(db, agency_id, user, write=False)
    try:
        return await AgencyOnboardingService(db).get_state(agency_id)
    except AgencyOnboardingError as exc:
        raise run_service_error(exc) from exc


@router.put("/profile")
async def save_onboarding_profile(
    agency_id: str,
    payload: AgencyOnboardingProfileUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await authorize(db, agency_id, user, write=True)
    try:
        return await AgencyOnboardingService(db).save_profile(agency_id, payload, user["id"])
    except AgencyOnboardingError as exc:
        raise run_service_error(exc) from exc


@router.put("/email-status")
async def save_onboarding_email_status(
    agency_id: str,
    payload: AgencyOnboardingEmailStatusUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await authorize(db, agency_id, user, write=True)
    try:
        return await AgencyOnboardingService(db).save_email_status(agency_id, payload, user["id"])
    except AgencyOnboardingError as exc:
        raise run_service_error(exc) from exc


@router.put("/preferences")
async def save_onboarding_preferences(
    agency_id: str,
    payload: AgencyOnboardingPreferencesUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await authorize(db, agency_id, user, write=True)
    try:
        return await AgencyOnboardingService(db).save_preferences(agency_id, payload, user["id"])
    except AgencyOnboardingError as exc:
        raise run_service_error(exc) from exc


@router.post("/logo/confirm")
async def confirm_onboarding_logo(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await authorize(db, agency_id, user, write=True)
    try:
        return await AgencyOnboardingService(db).confirm_logo(agency_id, user["id"])
    except AgencyOnboardingError as exc:
        raise run_service_error(exc) from exc


@router.post("/logo/skip")
async def skip_onboarding_logo(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await authorize(db, agency_id, user, write=True)
    try:
        return await AgencyOnboardingService(db).skip_logo(agency_id, user["id"])
    except AgencyOnboardingError as exc:
        raise run_service_error(exc) from exc


@router.post("/seed-defaults")
async def seed_onboarding_defaults(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await authorize(db, agency_id, user, write=True)
    try:
        return await AgencyOnboardingService(db).seed_defaults(agency_id, user["id"])
    except AgencyOnboardingError as exc:
        raise run_service_error(exc) from exc


@router.post("/demo-workspace")
async def seed_onboarding_demo_workspace(
    agency_id: str,
    payload: AgencyDemoWorkspaceGenerateRequest | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await authorize(db, agency_id, user, write=True)
    try:
        return await AgencyOnboardingService(db).seed_demo_workspace(agency_id, user["id"], payload)
    except AgencyOnboardingError as exc:
        raise run_service_error(exc) from exc


@router.get("/demo-workspace/profiles")
async def list_onboarding_demo_workspace_profiles(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await authorize(db, agency_id, user, write=False)
    try:
        return await AgencyOnboardingService(db).demo_workspace_profiles(agency_id)
    except AgencyOnboardingError as exc:
        raise run_service_error(exc) from exc


@router.post("/complete")
async def complete_onboarding(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await authorize(db, agency_id, user, write=True)
    try:
        return await AgencyOnboardingService(db).complete(agency_id, user["id"])
    except AgencyOnboardingError as exc:
        raise run_service_error(exc) from exc
