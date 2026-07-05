from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import FeatureBundleRolloutDecisionCreate, FeatureBundleRolloutDecisionUpdate
from services.feature_bundle_rollout_decision_service import PHASE_LABEL, FeatureBundleRolloutDecisionService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/feature-bundle-rollout-decisions", tags=["platform-feature-bundle-rollout-decisions"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_platform_feature_bundle_rollout_decisions(
    rollout_plan_id: str | None = Query(default=None),
    category: str | None = Query(default=None),
    owner: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await FeatureBundleRolloutDecisionService(db).platform_response(
        rollout_plan_id=rollout_plan_id,
        category=category,
        owner=owner,
        status=status_filter,
        include_archived=include_archived,
    )


@router.get("/summary")
async def summarize_platform_feature_bundle_rollout_decisions(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await FeatureBundleRolloutDecisionService(db).platform_summary()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_platform_feature_bundle_rollout_decision(
    payload: FeatureBundleRolloutDecisionCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await FeatureBundleRolloutDecisionService(db).create_decision(payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{decision_id}")
async def get_platform_feature_bundle_rollout_decision(
    decision_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = FeatureBundleRolloutDecisionService(db)
    try:
        decision = await service.get_platform_decision(decision_id)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "decision": decision,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{decision_id}")
async def update_platform_feature_bundle_rollout_decision(
    decision_id: str,
    payload: FeatureBundleRolloutDecisionUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await FeatureBundleRolloutDecisionService(db).update_decision(decision_id, payload, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/{decision_id}")
async def delete_platform_feature_bundle_rollout_decision(
    decision_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await FeatureBundleRolloutDecisionService(db).delete_decision(decision_id, user)
    except ValueError as exc:
        raise bad_request(str(exc)) from exc
