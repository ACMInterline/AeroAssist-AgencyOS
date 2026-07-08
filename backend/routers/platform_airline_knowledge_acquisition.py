from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import AirlineKnowledgeAcquisitionCreate, AirlineKnowledgeAcquisitionUpdate
from services.airline_knowledge_acquisition_service import PHASE_LABEL, AirlineKnowledgeAcquisitionError, AirlineKnowledgeAcquisitionService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/airline-knowledge-acquisition", tags=["platform-airline-knowledge-acquisition"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_platform_airline_knowledge_acquisitions(
    agency_id: str | None = Query(default=None),
    airline: str | None = Query(default=None),
    service_domain: str | None = Query(default=None),
    service_family: str | None = Query(default=None),
    ssr_code: str | None = Query(default=None),
    rfic: str | None = Query(default=None),
    rfisc: str | None = Query(default=None),
    source_type: str | None = Query(default=None),
    review_status: str | None = Query(default=None),
    approval_status: str | None = Query(default=None),
    effective_date: str | None = Query(default=None),
    official_source_flag: bool | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AirlineKnowledgeAcquisitionService(db).platform_response(
        agency_id=agency_id,
        airline=airline,
        service_domain=service_domain,
        service_family=service_family,
        ssr_code=ssr_code,
        rfic=rfic,
        rfisc=rfisc,
        source_type=source_type,
        review_status=review_status,
        approval_status=approval_status,
        effective_date=effective_date,
        official_source_flag=official_source_flag,
        include_archived=include_archived,
    )


@router.get("/summary")
async def summarize_platform_airline_knowledge_acquisitions(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await AirlineKnowledgeAcquisitionService(db).platform_summary()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_knowledge_acquisition(
    payload: AirlineKnowledgeAcquisitionCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineKnowledgeAcquisitionService(db).create_acquisition(payload, user)
    except AirlineKnowledgeAcquisitionError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{acquisition_id}")
async def get_platform_airline_knowledge_acquisition(
    acquisition_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = AirlineKnowledgeAcquisitionService(db)
    try:
        acquisition = await service.get_platform_acquisition(acquisition_id)
    except AirlineKnowledgeAcquisitionError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "airline_knowledge_acquisition": acquisition,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{acquisition_id}")
async def update_platform_airline_knowledge_acquisition(
    acquisition_id: str,
    payload: AirlineKnowledgeAcquisitionUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineKnowledgeAcquisitionService(db).update_acquisition(acquisition_id, payload, user)
    except AirlineKnowledgeAcquisitionError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/{acquisition_id}")
async def delete_platform_airline_knowledge_acquisition(
    acquisition_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await AirlineKnowledgeAcquisitionService(db).delete_acquisition(acquisition_id, user)
    except AirlineKnowledgeAcquisitionError as exc:
        raise bad_request(str(exc)) from exc
