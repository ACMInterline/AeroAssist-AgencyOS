from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import RequestSegmentServiceScopeCreate, RequestSegmentServiceScopeUpdate
from services.request_segment_service_precision_service import (
    PHASE_LABEL,
    RequestSegmentServicePrecisionError,
    RequestSegmentServicePrecisionService,
)
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/request-segment-services", tags=["agency-request-segment-services"])

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
async def list_agency_request_segment_services(
    agency_id: str,
    request: str | None = Query(default=None),
    passenger: str | None = Query(default=None),
    segment: str | None = Query(default=None),
    service_family: str | None = Query(default=None),
    ssr_code: str | None = Query(default=None),
    pet_transport_mode: str | None = Query(default=None),
    item_category: str | None = Query(default=None),
    readiness_status: str | None = Query(default=None),
    requires_policy_review: bool | None = Query(default=None),
    requires_document_followup: bool | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await RequestSegmentServicePrecisionService(db).agency_response(
        agency_id,
        request=request,
        passenger=passenger,
        segment=segment,
        service_family=service_family,
        ssr_code=ssr_code,
        pet_transport_mode=pet_transport_mode,
        item_category=item_category,
        readiness_status=readiness_status,
        requires_policy_review=requires_policy_review,
        requires_document_followup=requires_document_followup,
    )


@router.get("/summary")
async def summarize_agency_request_segment_services(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await RequestSegmentServicePrecisionService(db).agency_summary(agency_id)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_agency_request_segment_service(
    agency_id: str,
    payload: RequestSegmentServiceScopeCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await RequestSegmentServicePrecisionService(db).create_scope(payload, user, agency_id=agency_id)
    except RequestSegmentServicePrecisionError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{scope_id}")
async def get_agency_request_segment_service(
    agency_id: str,
    scope_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = RequestSegmentServicePrecisionService(db)
    try:
        scope = await service.get_agency_scope(agency_id, scope_id)
    except RequestSegmentServicePrecisionError:
        raise not_found("Request segment service scope metadata not found.")
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "request_segment_service_scope": scope,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{scope_id}")
async def update_agency_request_segment_service(
    agency_id: str,
    scope_id: str,
    payload: RequestSegmentServiceScopeUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await RequestSegmentServicePrecisionService(db).update_scope(scope_id, payload, user, agency_id=agency_id)
    except RequestSegmentServicePrecisionError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/{scope_id}")
async def archive_agency_request_segment_service(
    agency_id: str,
    scope_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await RequestSegmentServicePrecisionService(db).archive_scope(scope_id, user, agency_id=agency_id)
    except RequestSegmentServicePrecisionError as exc:
        raise bad_request(str(exc)) from exc
