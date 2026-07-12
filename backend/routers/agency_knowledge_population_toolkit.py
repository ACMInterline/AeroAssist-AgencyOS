from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.knowledge_population_toolkit_service import (
    PHASE_LABEL,
    KnowledgePopulationToolkitError,
    KnowledgePopulationToolkitService,
)
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(tags=["agency-knowledge-population-toolkit"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
PLATFORM_ROLES = {"platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"}


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in PLATFORM_ROLES:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


@router.get("/api/agencies/{agency_id}/knowledge-population-toolkit")
async def list_agency_knowledge_population_toolkits(
    agency_id: str,
    airline_code: str | None = Query(default=None),
    population_status: str | None = Query(default=None),
    QA_status: str | None = Query(default=None),
    publishing_status: str | None = Query(default=None),
    scenario_test_status: str | None = Query(default=None),
    owner: str | None = Query(default=None),
    search: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await KnowledgePopulationToolkitService(db).agency_response(
        agency_id,
        airline_code=airline_code,
        population_status=population_status,
        QA_status=QA_status,
        publishing_status=publishing_status,
        scenario_test_status=scenario_test_status,
        owner=owner,
        search=search,
        include_archived=include_archived,
    )


@router.get("/api/agencies/{agency_id}/knowledge-population-toolkit/summary")
async def summarize_agency_knowledge_population_toolkits(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await KnowledgePopulationToolkitService(db).agency_summary(agency_id)


@router.get("/api/agencies/{agency_id}/knowledge-population-toolkit/{toolkit_id}")
async def get_agency_knowledge_population_toolkit(
    agency_id: str,
    toolkit_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = KnowledgePopulationToolkitService(db)
    try:
        toolkit = await service.get_toolkit(toolkit_id, agency_id=agency_id)
    except KnowledgePopulationToolkitError:
        raise not_found("Knowledge population toolkit metadata not found.")
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "knowledge_population_toolkit": toolkit,
        "read_only": True,
        "metadata_only": True,
        **service.safety_flags(),
    }
