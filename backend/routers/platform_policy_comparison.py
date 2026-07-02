from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    AirlinePolicyComparisonBuildRequest,
    AirlinePolicyComparisonProfileCreate,
    AirlinePolicyComparisonProfileUpdate,
    AirlinePolicyComparisonRequest,
    AirlinePolicyComparisonSavedViewCreate,
    AirlinePolicyComparisonSavedViewUpdate,
    AirlinePolicyComparisonSnapshotCreate,
    AirlineServiceAdvisorEvaluationRequest,
    AirlineServiceAdvisorScenarioCreate,
)
from services.policy_comparison_service import PolicyComparisonService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/policy-comparison", tags=["platform-policy-comparison"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor", "platform_support"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


@router.get("/summary")
async def get_platform_policy_comparison_summary(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await PolicyComparisonService(db).summary()


@router.get("/profiles")
async def list_platform_policy_comparison_profiles(
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await PolicyComparisonService(db).list_profiles(
            airline_code=airline_code,
            domain_code=domain_code,
            family_code=family_code,
            variant_code=variant_code,
            include_archived=include_archived,
        )
    }


@router.post("/profiles", status_code=status.HTTP_201_CREATED)
async def create_platform_policy_comparison_profile(
    payload: AirlinePolicyComparisonProfileCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return {"comparison_profile": await PolicyComparisonService(db).create_profile(payload)}


@router.patch("/profiles/{profile_id}")
async def update_platform_policy_comparison_profile(
    profile_id: str,
    payload: AirlinePolicyComparisonProfileUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    profile = await PolicyComparisonService(db).update_profile(profile_id, payload)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comparison profile not found.")
    return {"comparison_profile": profile}


@router.post("/build-profile", status_code=status.HTTP_201_CREATED)
async def build_platform_policy_comparison_profile(
    payload: AirlinePolicyComparisonBuildRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return {"comparison_profile": await PolicyComparisonService(db).build_profile(payload, user)}


@router.post("/compare", status_code=status.HTTP_201_CREATED)
async def compare_platform_policy(
    payload: AirlinePolicyComparisonRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await PolicyComparisonService(db).compare(payload, user)


@router.get("/snapshots")
async def list_platform_policy_comparison_snapshots(
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await PolicyComparisonService(db).list_snapshots(
            domain_code=domain_code,
            family_code=family_code,
            variant_code=variant_code,
        )
    }


@router.post("/snapshots", status_code=status.HTTP_201_CREATED)
async def create_platform_policy_comparison_snapshot(
    payload: AirlinePolicyComparisonSnapshotCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return {"snapshot": await PolicyComparisonService(db).create_snapshot(payload)}


@router.get("/comparison-rows")
async def list_platform_policy_comparison_rows(
    snapshot_id: str | None = None,
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await PolicyComparisonService(db).list_rows(
            snapshot_id=snapshot_id,
            airline_code=airline_code,
            domain_code=domain_code,
            family_code=family_code,
            variant_code=variant_code,
        )
    }


@router.get("/advisor-scenarios")
async def list_platform_service_advisor_scenarios(
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await PolicyComparisonService(db).list_advisor_scenarios(
            domain_code=domain_code,
            family_code=family_code,
            variant_code=variant_code,
        )
    }


@router.post("/advisor-scenarios", status_code=status.HTTP_201_CREATED)
async def create_platform_service_advisor_scenario(
    payload: AirlineServiceAdvisorScenarioCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return {"advisor_scenario": await PolicyComparisonService(db).create_advisor_scenario(payload, user)}


@router.post("/advisor-evaluate", status_code=status.HTTP_201_CREATED)
async def evaluate_platform_service_advisor(
    payload: AirlineServiceAdvisorEvaluationRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await PolicyComparisonService(db).evaluate_advisor(payload, user)


@router.get("/advisor-results")
async def list_platform_service_advisor_results(
    scenario_id: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {"items": await PolicyComparisonService(db).list_advisor_results(scenario_id=scenario_id)}


@router.get("/saved-views")
async def list_platform_policy_comparison_saved_views(
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return {
        "items": await PolicyComparisonService(db).list_saved_views(
            domain_code=domain_code,
            family_code=family_code,
            variant_code=variant_code,
            include_archived=include_archived,
        )
    }


@router.post("/saved-views", status_code=status.HTTP_201_CREATED)
async def create_platform_policy_comparison_saved_view(
    payload: AirlinePolicyComparisonSavedViewCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    return {"saved_view": await PolicyComparisonService(db).create_saved_view(payload)}


@router.patch("/saved-views/{view_id}")
async def update_platform_policy_comparison_saved_view(
    view_id: str,
    payload: AirlinePolicyComparisonSavedViewUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    view = await PolicyComparisonService(db).update_saved_view(view_id, payload)
    if not view:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved view not found.")
    return {"saved_view": view}
