from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user
from database import Database, get_database
from models import AgencyFeatureBundleAssignmentCreate, AgencyFeatureBundleAssignmentUpdate
from services.agency_feature_bundle_assignment_service import AgencyFeatureBundleAssignmentService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform", tags=["platform-feature-bundle-assignments"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("/feature-bundle-assignments")
async def list_platform_feature_bundle_assignments(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AgencyFeatureBundleAssignmentService(db).platform_assignments_response()


@router.get("/agencies/{agency_id}/bundle-assignments")
async def list_platform_agency_feature_bundle_assignments(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AgencyFeatureBundleAssignmentService(db).platform_assignments_response(agency_id=agency_id)


@router.post("/agencies/{agency_id}/bundle-assignments", status_code=status.HTTP_201_CREATED)
async def create_platform_agency_feature_bundle_assignment(
    agency_id: str,
    payload: AgencyFeatureBundleAssignmentCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AgencyFeatureBundleAssignmentService(db).create_assignment(agency_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.put("/bundle-assignments/{assignment_id}")
async def update_platform_feature_bundle_assignment(
    assignment_id: str,
    payload: AgencyFeatureBundleAssignmentUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AgencyFeatureBundleAssignmentService(db).update_assignment(assignment_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/bundle-assignments/{assignment_id}")
async def inactive_platform_feature_bundle_assignment(
    assignment_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AgencyFeatureBundleAssignmentService(db).inactive_assignment(assignment_id, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
