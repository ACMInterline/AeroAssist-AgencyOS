from fastapi import APIRouter, Depends, Query

from auth import get_current_user
from database import Database, get_database
from services.request_to_trip_conversion_service import PHASE_LABEL, RequestToTripConversionService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/request-trip-conversion", tags=["platform-request-trip-conversion"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


@router.get("")
async def platform_request_trip_conversion_dashboard(
    agency_id: str | None = Query(default=None),
    request_id: str | None = Query(default=None),
    trip_id: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await RequestToTripConversionService(db).platform_dashboard(agency_id=agency_id, request_id=request_id, trip_id=trip_id, status=status_filter)


@router.get("/plans")
async def list_platform_request_trip_conversion_plans(
    agency_id: str | None = Query(default=None),
    request_id: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = RequestToTripConversionService(db)
    return {"phase": PHASE_LABEL, "plans": await service.list_plans(agency_id=agency_id, request_id=request_id, status=status_filter), "metadata_only": True, **service.safety_flags()}


@router.get("/runs")
async def list_platform_request_trip_conversion_runs(
    agency_id: str | None = Query(default=None),
    request_id: str | None = Query(default=None),
    trip_id: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = RequestToTripConversionService(db)
    return {"phase": PHASE_LABEL, "runs": await service.list_runs(agency_id=agency_id, request_id=request_id, trip_id=trip_id, status=status_filter), "metadata_only": True, **service.safety_flags()}


@router.get("/mappings")
async def list_platform_request_trip_conversion_mappings(
    agency_id: str | None = Query(default=None),
    run_id: str | None = Query(default=None),
    request_id: str | None = Query(default=None),
    trip_id: str | None = Query(default=None),
    mapping_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = RequestToTripConversionService(db)
    return {
        "phase": PHASE_LABEL,
        "mappings": await service.list_mappings(agency_id=agency_id, run_id=run_id, request_id=request_id, trip_id=trip_id, mapping_type=mapping_type),
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.get("/issues")
async def list_platform_request_trip_conversion_issues(
    agency_id: str | None = Query(default=None),
    run_id: str | None = Query(default=None),
    request_id: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = RequestToTripConversionService(db)
    return {
        "phase": PHASE_LABEL,
        "issues": await service.list_issues(agency_id=agency_id, run_id=run_id, request_id=request_id, severity=severity, status=status_filter),
        "metadata_only": True,
        **service.safety_flags(),
    }
