from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import OperationalScenarioTestCreate, OperationalScenarioTestUpdate
from services.operational_scenario_testing_service import (
    PHASE_LABEL,
    OperationalScenarioTestingError,
    OperationalScenarioTestingService,
)
from services.tenant_service import require_any_platform_role


router = APIRouter(tags=["platform-operational-scenario-testing"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("/api/platform/operational-scenario-testing")
async def list_platform_operational_scenario_tests(
    agency_id: str | None = Query(default=None),
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
    await require_platform_read(user)
    return await OperationalScenarioTestingService(db).platform_response(
        agency_id=agency_id,
        scenario_family=scenario_family,
        test_status=test_status,
        airline_code=airline_code,
        service_code=service_code,
        expected_recommendation_level=expected_recommendation_level,
        search=search,
        include_archived=include_archived,
    )


@router.get("/api/platform/operational-scenario-testing/summary")
async def summarize_platform_operational_scenario_tests(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await OperationalScenarioTestingService(db).platform_summary(agency_id)


@router.post("/api/platform/operational-scenario-testing", status_code=status.HTTP_201_CREATED)
async def create_platform_operational_scenario_test(
    payload: OperationalScenarioTestCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalScenarioTestingService(db).create_scenario(payload, user)
    except OperationalScenarioTestingError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/api/platform/operational-scenario-testing/{scenario_id}")
async def get_platform_operational_scenario_test(
    scenario_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OperationalScenarioTestingService(db)
    try:
        scenario = await service.get_scenario(scenario_id)
    except OperationalScenarioTestingError as exc:
        raise bad_request(str(exc)) from exc
    return {"phase": PHASE_LABEL, "operational_scenario_test": scenario, "metadata_only": True, **service.safety_flags()}


@router.put("/api/platform/operational-scenario-testing/{scenario_id}")
async def update_platform_operational_scenario_test(
    scenario_id: str,
    payload: OperationalScenarioTestUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalScenarioTestingService(db).update_scenario(scenario_id, payload, user)
    except OperationalScenarioTestingError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/api/platform/operational-scenario-testing/{scenario_id}")
async def archive_platform_operational_scenario_test(
    scenario_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalScenarioTestingService(db).archive_scenario(scenario_id, user)
    except OperationalScenarioTestingError as exc:
        raise bad_request(str(exc)) from exc
