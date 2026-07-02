from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    AirlinePolicyComparisonRequest,
    AirlinePolicyComparisonSavedViewCreate,
    AirlinePolicyComparisonSnapshotCreate,
    AirlineServiceAdvisorEvaluationRequest,
    AirlineServiceAdvisorScenarioCreate,
)
from services.policy_comparison_service import PolicyComparisonService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/policy-comparison", tags=["agency-policy-comparison"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin", "agency_agent"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


async def require_write(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin"}:
        await require_any_agency_role(db, agency_id, user, WRITE_ROLES)


@router.get("/summary")
async def get_agency_policy_comparison_summary(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    summary = await PolicyComparisonService(db).summary(agency_id=agency_id)
    return {
        **summary,
        "platform_profiles_read_only": True,
        "agency_global_mutation_blocked": True,
    }


@router.get("/profiles")
async def list_agency_policy_comparison_profiles(
    agency_id: str,
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {
        "items": await PolicyComparisonService(db).list_profiles(
            agency_id=agency_id,
            airline_code=airline_code,
            domain_code=domain_code,
            family_code=family_code,
            variant_code=variant_code,
            include_archived=include_archived,
        ),
        "read_only": True,
        "agency_global_mutation_blocked": True,
    }


@router.post("/compare", status_code=status.HTTP_201_CREATED)
async def compare_agency_policy(
    agency_id: str,
    payload: AirlinePolicyComparisonRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await PolicyComparisonService(db).compare(payload, user, agency_id=agency_id)


@router.get("/snapshots")
async def list_agency_policy_comparison_snapshots(
    agency_id: str,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {
        "items": await PolicyComparisonService(db).list_snapshots(
            agency_id=agency_id,
            domain_code=domain_code,
            family_code=family_code,
            variant_code=variant_code,
        )
    }


@router.post("/snapshots", status_code=status.HTTP_201_CREATED)
async def create_agency_policy_comparison_snapshot(
    agency_id: str,
    payload: AirlinePolicyComparisonSnapshotCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    return {"snapshot": await PolicyComparisonService(db).create_snapshot(payload, agency_id=agency_id)}


@router.get("/comparison-rows")
async def list_agency_policy_comparison_rows(
    agency_id: str,
    snapshot_id: str | None = None,
    airline_code: str | None = None,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {
        "items": await PolicyComparisonService(db).list_rows(
            agency_id=agency_id,
            snapshot_id=snapshot_id,
            airline_code=airline_code,
            domain_code=domain_code,
            family_code=family_code,
            variant_code=variant_code,
        )
    }


@router.get("/advisor-scenarios")
async def list_agency_service_advisor_scenarios(
    agency_id: str,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {
        "items": await PolicyComparisonService(db).list_advisor_scenarios(
            agency_id=agency_id,
            domain_code=domain_code,
            family_code=family_code,
            variant_code=variant_code,
        )
    }


@router.post("/advisor-scenarios", status_code=status.HTTP_201_CREATED)
async def create_agency_service_advisor_scenario(
    agency_id: str,
    payload: AirlineServiceAdvisorScenarioCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    return {"advisor_scenario": await PolicyComparisonService(db).create_advisor_scenario(payload, user, agency_id=agency_id)}


@router.post("/advisor-evaluate", status_code=status.HTTP_201_CREATED)
async def evaluate_agency_service_advisor(
    agency_id: str,
    payload: AirlineServiceAdvisorEvaluationRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await PolicyComparisonService(db).evaluate_advisor(payload, user, agency_id=agency_id)


@router.get("/advisor-results")
async def list_agency_service_advisor_results(
    agency_id: str,
    scenario_id: str | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {"items": await PolicyComparisonService(db).list_advisor_results(agency_id=agency_id, scenario_id=scenario_id)}


@router.get("/saved-views")
async def list_agency_policy_comparison_saved_views(
    agency_id: str,
    domain_code: str | None = None,
    family_code: str | None = None,
    variant_code: str | None = None,
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {
        "items": await PolicyComparisonService(db).list_saved_views(
            agency_id=agency_id,
            domain_code=domain_code,
            family_code=family_code,
            variant_code=variant_code,
            include_archived=include_archived,
        )
    }


@router.post("/saved-views", status_code=status.HTTP_201_CREATED)
async def create_agency_policy_comparison_saved_view(
    agency_id: str,
    payload: AirlinePolicyComparisonSavedViewCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    return {
        "saved_view": await PolicyComparisonService(db).create_saved_view(payload, agency_id=agency_id),
        "agency_global_mutation_blocked": True,
    }
