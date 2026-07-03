from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    AgencyEntitlementReadinessCreateRequest,
    AgencySubscriptionAssignmentCreateRequest,
    AgencySubscriptionAssignmentUpdateRequest,
    AgencySubscriptionReviewNoteCreateRequest,
    AgencySubscriptionSnapshotCreateRequest,
    SaaSPlanEntitlementCreateRequest,
    SaaSSubscriptionPlanCreateRequest,
    SaaSSubscriptionPlanUpdateRequest,
)
from services.saas_subscription_service import SaaSSubscriptionService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/saas-subscriptions", tags=["platform-saas-subscriptions"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("/summary")
async def get_platform_saas_subscription_summary(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await SaaSSubscriptionService(db).platform_summary()


@router.get("/plans")
async def list_platform_saas_subscription_plans(
    status_filter: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {"items": await SaaSSubscriptionService(db).list_plans(status=status_filter), "metadata_only": True}


@router.post("/plans", status_code=status.HTTP_201_CREATED)
async def create_platform_saas_subscription_plan(
    payload: SaaSSubscriptionPlanCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await SaaSSubscriptionService(db).create_plan(payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.patch("/plans/{plan_id}")
async def update_platform_saas_subscription_plan(
    plan_id: str,
    payload: SaaSSubscriptionPlanUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await SaaSSubscriptionService(db).update_plan(plan_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/entitlements")
async def list_platform_saas_plan_entitlements(
    plan_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {"items": await SaaSSubscriptionService(db).list_entitlements(plan_id=plan_id), "metadata_only": True}


@router.post("/entitlements", status_code=status.HTTP_201_CREATED)
async def create_platform_saas_plan_entitlement(
    payload: SaaSPlanEntitlementCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await SaaSSubscriptionService(db).create_entitlement(payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/assignments")
async def list_platform_agency_subscription_assignments(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {"items": await SaaSSubscriptionService(db).list_assignments(agency_id=agency_id), "metadata_only": True}


@router.post("/assignments", status_code=status.HTTP_201_CREATED)
async def create_platform_agency_subscription_assignment(
    payload: AgencySubscriptionAssignmentCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await SaaSSubscriptionService(db).create_assignment(payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.patch("/assignments/{assignment_id}")
async def update_platform_agency_subscription_assignment(
    assignment_id: str,
    payload: AgencySubscriptionAssignmentUpdateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await SaaSSubscriptionService(db).update_assignment(assignment_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/readiness")
async def list_platform_agency_entitlement_readiness(
    agency_id: str | None = Query(default=None),
    assignment_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await SaaSSubscriptionService(db).list_readiness(agency_id=agency_id, assignment_id=assignment_id),
        "metadata_only": True,
    }


@router.post("/readiness", status_code=status.HTTP_201_CREATED)
async def create_platform_agency_entitlement_readiness(
    payload: AgencyEntitlementReadinessCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await SaaSSubscriptionService(db).create_readiness(payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/notes")
async def list_platform_agency_subscription_notes(
    agency_id: str | None = Query(default=None),
    assignment_id: str | None = Query(default=None),
    visible_to_agency: bool | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await SaaSSubscriptionService(db).list_notes(agency_id=agency_id, assignment_id=assignment_id, visible_to_agency=visible_to_agency),
        "metadata_only": True,
    }


@router.post("/notes", status_code=status.HTTP_201_CREATED)
async def create_platform_agency_subscription_note(
    payload: AgencySubscriptionReviewNoteCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await SaaSSubscriptionService(db).create_note(payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/snapshots")
async def list_platform_agency_subscription_snapshots(
    agency_id: str | None = Query(default=None),
    assignment_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await SaaSSubscriptionService(db).list_snapshots(agency_id=agency_id, assignment_id=assignment_id),
        "metadata_only": True,
    }


@router.post("/snapshots", status_code=status.HTTP_201_CREATED)
async def create_platform_agency_subscription_snapshot(
    payload: AgencySubscriptionSnapshotCreateRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await SaaSSubscriptionService(db).create_snapshot(payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
