from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.operational_scenario_testing_service import (
    PHASE_LABEL,
    OperationalScenarioTestingError,
    OperationalScenarioTestingService,
)
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(tags=["agency-operational-scenario-testing"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
PLATFORM_ROLES = {"platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"}


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in PLATFORM_ROLES:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


@router.get("/api/agencies/{agency_id}/operational-scenario-testing")
async def list_agency_operational_scenario_tests(
    agency_id: str,
    scenario_family: str | None = Query(default=None),
    test_status: str | None = Query(default=None),
    airline_code: str | None = Query(default=None),
    service_code: str | None = Query(default=None),
    expected_recommendation_level: str | None = Query(default=None),
    search: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await OperationalScenarioTestingService(db).agency_response(
        agency_id,
        scenario_family=scenario_family,
        test_status=test_status,
        airline_code=airline_code,
        service_code=service_code,
        expected_recommendation_level=expected_recommendation_level,
        search=search,
        include_archived=include_archived,
    )


@router.get("/api/agencies/{agency_id}/operational-scenario-testing/summary")
async def summarize_agency_operational_scenario_tests(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await OperationalScenarioTestingService(db).agency_summary(agency_id)


@router.get("/api/agencies/{agency_id}/operational-scenario-testing/{scenario_id}")
async def get_agency_operational_scenario_test(
    agency_id: str,
    scenario_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = OperationalScenarioTestingService(db)
    try:
        scenario = await service.get_scenario(scenario_id, agency_id=agency_id)
    except OperationalScenarioTestingError:
        raise not_found("Operational scenario test metadata not found.")
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "operational_scenario_test": scenario,
        "read_only": True,
        "metadata_only": True,
        **service.safety_flags(),
    }
