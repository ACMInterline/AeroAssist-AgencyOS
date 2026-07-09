from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import OperationalIntelligenceCaseCreate, OperationalIntelligenceCaseUpdate
from services.operational_intelligence_case_service import (
    OperationalIntelligenceCaseError,
    OperationalIntelligenceCaseService,
    PHASE_LABEL,
)
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/operational-intelligence-cases", tags=["platform-operational-intelligence-cases"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_platform_operational_intelligence_cases(
    agency_id: str | None = Query(default=None),
    case_status: str | None = Query(default=None),
    overall_case_status: str | None = Query(default=None),
    airline: str | None = Query(default=None),
    passenger_need: str | None = Query(default=None),
    travel_request: str | None = Query(default=None),
    trip_workspace: str | None = Query(default=None),
    ready_for_agent_review: bool | None = Query(default=None),
    ready_for_offer_builder: bool | None = Query(default=None),
    ready_for_client_presentation: bool | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await OperationalIntelligenceCaseService(db).platform_response(
        agency_id=agency_id,
        case_status=case_status,
        overall_case_status=overall_case_status,
        airline=airline,
        passenger_need=passenger_need,
        travel_request=travel_request,
        trip_workspace=trip_workspace,
        ready_for_agent_review=ready_for_agent_review,
        ready_for_offer_builder=ready_for_offer_builder,
        ready_for_client_presentation=ready_for_client_presentation,
        include_archived=include_archived,
    )


@router.get("/summary")
async def summarize_platform_operational_intelligence_cases(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await OperationalIntelligenceCaseService(db).platform_summary()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_platform_operational_intelligence_case(
    payload: OperationalIntelligenceCaseCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalIntelligenceCaseService(db).create_case(payload, user)
    except OperationalIntelligenceCaseError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{case_id}")
async def get_platform_operational_intelligence_case(
    case_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OperationalIntelligenceCaseService(db)
    try:
        case = await service.get_platform_case(case_id)
    except OperationalIntelligenceCaseError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "operational_intelligence_case": case,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{case_id}")
async def update_platform_operational_intelligence_case(
    case_id: str,
    payload: OperationalIntelligenceCaseUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalIntelligenceCaseService(db).update_case(case_id, payload, user)
    except OperationalIntelligenceCaseError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/{case_id}")
async def archive_platform_operational_intelligence_case(
    case_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalIntelligenceCaseService(db).archive_case(case_id, user)
    except OperationalIntelligenceCaseError as exc:
        raise bad_request(str(exc)) from exc
