from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import OperationalIntelligenceCaseCreate, OperationalIntelligenceCaseUpdate
from services.operational_intelligence_case_service import (
    OperationalIntelligenceCaseError,
    OperationalIntelligenceCaseService,
    PHASE_LABEL,
)
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/intelligence-cases", tags=["agency-intelligence-cases"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin", "agency_agent"]
PLATFORM_ROLES = {"platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"}


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in PLATFORM_ROLES:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


async def require_write(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in PLATFORM_ROLES:
        await require_any_agency_role(db, agency_id, user, WRITE_ROLES)


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_agency_intelligence_cases(
    agency_id: str,
    case_status: str | None = Query(default=None),
    overall_case_status: str | None = Query(default=None),
    airline: str | None = Query(default=None),
    passenger_need: str | None = Query(default=None),
    travel_request: str | None = Query(default=None),
    trip_workspace: str | None = Query(default=None),
    ready_for_agent_review: bool | None = Query(default=None),
    ready_for_offer_builder: bool | None = Query(default=None),
    ready_for_client_presentation: bool | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await OperationalIntelligenceCaseService(db).agency_response(
        agency_id,
        case_status=case_status,
        overall_case_status=overall_case_status,
        airline=airline,
        passenger_need=passenger_need,
        travel_request=travel_request,
        trip_workspace=trip_workspace,
        ready_for_agent_review=ready_for_agent_review,
        ready_for_offer_builder=ready_for_offer_builder,
        ready_for_client_presentation=ready_for_client_presentation,
    )


@router.get("/summary")
async def summarize_agency_intelligence_cases(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await OperationalIntelligenceCaseService(db).agency_summary(agency_id)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_agency_intelligence_case(
    agency_id: str,
    payload: OperationalIntelligenceCaseCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OperationalIntelligenceCaseService(db).create_case(payload, user, agency_id=agency_id)
    except OperationalIntelligenceCaseError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{case_id}")
async def get_agency_intelligence_case(
    agency_id: str,
    case_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = OperationalIntelligenceCaseService(db)
    try:
        case = await service.get_agency_case(agency_id, case_id)
    except OperationalIntelligenceCaseError:
        raise not_found("Operational intelligence case metadata not found.")
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "operational_intelligence_case": case,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{case_id}")
async def update_agency_intelligence_case(
    agency_id: str,
    case_id: str,
    payload: OperationalIntelligenceCaseUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OperationalIntelligenceCaseService(db).update_case(case_id, payload, user, agency_id=agency_id)
    except OperationalIntelligenceCaseError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/{case_id}")
async def archive_agency_intelligence_case(
    agency_id: str,
    case_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await OperationalIntelligenceCaseService(db).archive_case(case_id, user, agency_id=agency_id)
    except OperationalIntelligenceCaseError as exc:
        raise bad_request(str(exc)) from exc
