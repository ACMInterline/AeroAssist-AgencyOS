from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import RequestSegmentServiceScopeCreate, RequestSegmentServiceScopeUpdate
from services.request_segment_service_precision_service import (
    PHASE_LABEL,
    RequestSegmentServicePrecisionError,
    RequestSegmentServicePrecisionService,
)
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/request-segment-services", tags=["platform-request-segment-services"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_platform_request_segment_services(
    agency_id: str | None = Query(default=None),
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
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await RequestSegmentServicePrecisionService(db).platform_response(
        agency_id=agency_id,
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
        include_archived=include_archived,
    )


@router.get("/summary")
async def summarize_platform_request_segment_services(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await RequestSegmentServicePrecisionService(db).platform_summary()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_platform_request_segment_service(
    payload: RequestSegmentServiceScopeCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await RequestSegmentServicePrecisionService(db).create_scope(payload, user)
    except RequestSegmentServicePrecisionError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{scope_id}")
async def get_platform_request_segment_service(
    scope_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = RequestSegmentServicePrecisionService(db)
    try:
        scope = await service.get_platform_scope(scope_id)
    except RequestSegmentServicePrecisionError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "request_segment_service_scope": scope,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{scope_id}")
async def update_platform_request_segment_service(
    scope_id: str,
    payload: RequestSegmentServiceScopeUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await RequestSegmentServicePrecisionService(db).update_scope(scope_id, payload, user)
    except RequestSegmentServicePrecisionError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/{scope_id}")
async def archive_platform_request_segment_service(
    scope_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await RequestSegmentServicePrecisionService(db).archive_scope(scope_id, user)
    except RequestSegmentServicePrecisionError as exc:
        raise bad_request(str(exc)) from exc
