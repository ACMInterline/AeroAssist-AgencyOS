from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import RequestTripConversionExecuteRequest, RequestTripConversionPreviewRequest
from services.request_to_trip_conversion_service import PHASE_LABEL, RequestToTripConversionError, RequestToTripConversionService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/request-trip-conversion", tags=["agency-request-trip-conversion"])

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


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def agency_request_trip_conversion_dashboard(
    agency_id: str,
    request_id: str | None = Query(default=None),
    trip_id: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await RequestToTripConversionService(db).agency_dashboard(agency_id, request_id=request_id, trip_id=trip_id, status=status_filter)


@router.post("/preview")
async def preview_agency_request_trip_conversion(
    agency_id: str,
    payload: RequestTripConversionPreviewRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await RequestToTripConversionService(db).build_preview(payload, user, agency_id=agency_id)
    except RequestToTripConversionError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/validate")
async def validate_agency_request_trip_conversion(
    agency_id: str,
    payload: RequestTripConversionPreviewRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await RequestToTripConversionService(db).validate_conversion(payload, user, agency_id=agency_id)
    except RequestToTripConversionError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/execute")
async def execute_agency_request_trip_conversion(
    agency_id: str,
    payload: RequestTripConversionExecuteRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await RequestToTripConversionService(db).execute_conversion(payload, user, agency_id=agency_id)
    except RequestToTripConversionError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/plans")
async def list_agency_request_trip_conversion_plans(
    agency_id: str,
    request_id: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = RequestToTripConversionService(db)
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "plans": await service.list_plans(agency_id=agency_id, request_id=request_id, status=status_filter), "metadata_only": True, **service.safety_flags()}


@router.get("/runs")
async def list_agency_request_trip_conversion_runs(
    agency_id: str,
    request_id: str | None = Query(default=None),
    trip_id: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = RequestToTripConversionService(db)
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "runs": await service.list_runs(agency_id=agency_id, request_id=request_id, trip_id=trip_id, status=status_filter), "metadata_only": True, **service.safety_flags()}


@router.get("/mappings")
async def list_agency_request_trip_conversion_mappings(
    agency_id: str,
    run_id: str | None = Query(default=None),
    request_id: str | None = Query(default=None),
    trip_id: str | None = Query(default=None),
    mapping_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = RequestToTripConversionService(db)
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "mappings": await service.list_mappings(agency_id=agency_id, run_id=run_id, request_id=request_id, trip_id=trip_id, mapping_type=mapping_type),
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.get("/issues")
async def list_agency_request_trip_conversion_issues(
    agency_id: str,
    run_id: str | None = Query(default=None),
    request_id: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = RequestToTripConversionService(db)
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "issues": await service.list_issues(agency_id=agency_id, run_id=run_id, request_id=request_id, severity=severity, status=status_filter),
        "metadata_only": True,
        **service.safety_flags(),
    }
