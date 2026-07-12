from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import KnowledgePopulationToolkitCreate, KnowledgePopulationToolkitUpdate
from services.knowledge_population_toolkit_service import (
    PHASE_LABEL,
    KnowledgePopulationToolkitError,
    KnowledgePopulationToolkitService,
)
from services.tenant_service import require_any_platform_role


router = APIRouter(tags=["platform-knowledge-population-toolkit"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("/api/platform/knowledge-population-toolkit")
async def list_platform_knowledge_population_toolkits(
    agency_id: str | None = Query(default=None),
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
    await require_platform_read(user)
    return await KnowledgePopulationToolkitService(db).platform_response(
        agency_id=agency_id,
        airline_code=airline_code,
        population_status=population_status,
        QA_status=QA_status,
        publishing_status=publishing_status,
        scenario_test_status=scenario_test_status,
        owner=owner,
        search=search,
        include_archived=include_archived,
    )


@router.get("/api/platform/knowledge-population-toolkit/summary")
async def summarize_platform_knowledge_population_toolkits(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await KnowledgePopulationToolkitService(db).platform_summary(agency_id)


@router.post("/api/platform/knowledge-population-toolkit", status_code=status.HTTP_201_CREATED)
async def create_platform_knowledge_population_toolkit(
    payload: KnowledgePopulationToolkitCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await KnowledgePopulationToolkitService(db).create_toolkit(payload, user)
    except KnowledgePopulationToolkitError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/api/platform/knowledge-population-toolkit/{toolkit_id}")
async def get_platform_knowledge_population_toolkit(
    toolkit_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = KnowledgePopulationToolkitService(db)
    try:
        toolkit = await service.get_toolkit(toolkit_id)
    except KnowledgePopulationToolkitError as exc:
        raise bad_request(str(exc)) from exc
    return {"phase": PHASE_LABEL, "knowledge_population_toolkit": toolkit, "metadata_only": True, **service.safety_flags()}


@router.put("/api/platform/knowledge-population-toolkit/{toolkit_id}")
async def update_platform_knowledge_population_toolkit(
    toolkit_id: str,
    payload: KnowledgePopulationToolkitUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await KnowledgePopulationToolkitService(db).update_toolkit(toolkit_id, payload, user)
    except KnowledgePopulationToolkitError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/api/platform/knowledge-population-toolkit/{toolkit_id}")
async def archive_platform_knowledge_population_toolkit(
    toolkit_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await KnowledgePopulationToolkitService(db).archive_toolkit(toolkit_id, user)
    except KnowledgePopulationToolkitError as exc:
        raise bad_request(str(exc)) from exc
