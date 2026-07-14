from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.airline_service_coverage_gap_service import (
    PHASE_LABEL,
    AirlineServiceCoverageGapError,
    AirlineServiceCoverageGapService,
)
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/airline-service-coverage", tags=["platform-airline-service-coverage"])

READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_read(user: dict) -> None:
    await require_any_platform_role(user, READ_ROLES)


async def require_write(user: dict) -> None:
    await require_any_platform_role(user, WRITE_ROLES)


def bad_request(exc: AirlineServiceCoverageGapError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("")
async def get_platform_airline_service_coverage(
    assessment_id: str | None = Query(default=None),
    agency_id: str | None = Query(default=None),
    airline_code: str | None = Query(default=None),
    service_family: str | None = Query(default=None),
    service_code: str | None = Query(default=None),
    coverage_status: str | None = Query(default=None),
    gap_type: str | None = Query(default=None),
    critical: bool | None = Query(default=None),
    operational_ready: bool | None = Query(default=None),
    route_type: str | None = Query(default=None),
    flight_type: str | None = Query(default=None),
    cabin: str | None = Query(default=None),
    fare_bundle: str | None = Query(default=None),
    operating_carrier: str | None = Query(default=None),
    marketing_carrier: str | None = Query(default=None),
    aircraft_family: str | None = Query(default=None),
    distribution_channel: str | None = Query(default=None),
    evidence_freshness: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    return await AirlineServiceCoverageGapService(db).platform_response(
        assessment_id=assessment_id,
        agency_id=agency_id,
        airline_code=airline_code,
        service_family=service_family,
        service_code=service_code,
        coverage_status=coverage_status,
        gap_type=gap_type,
        critical=critical,
        operational_ready=operational_ready,
        route_type=route_type,
        flight_type=flight_type,
        cabin=cabin,
        fare_bundle=fare_bundle,
        operating_carrier=operating_carrier,
        marketing_carrier=marketing_carrier,
        aircraft_family=aircraft_family,
        distribution_channel=distribution_channel,
        evidence_freshness=evidence_freshness,
    )


@router.get("/summary")
async def summarize_platform_airline_service_coverage(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    response = await AirlineServiceCoverageGapService(db).platform_response(agency_id=agency_id)
    return {"phase": PHASE_LABEL, "summary": response["summary"], "filters": response["filters"], **AirlineServiceCoverageGapService(db).safety_flags()}


@router.get("/targets")
async def list_platform_airline_coverage_targets(
    agency_id: str | None = Query(default=None),
    target_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = AirlineServiceCoverageGapService(db)
    items = await service.list_targets(agency_id, target_status)
    return {"phase": PHASE_LABEL, "items": items, "count": len(items), **service.safety_flags()}


@router.post("/targets", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_coverage_target(
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    try:
        return await AirlineServiceCoverageGapService(db).create_target(payload, user)
    except AirlineServiceCoverageGapError as exc:
        raise bad_request(exc) from exc


@router.put("/targets/{target_id}")
async def update_platform_airline_coverage_target(
    target_id: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    try:
        return await AirlineServiceCoverageGapService(db).update_target(target_id, payload, user)
    except AirlineServiceCoverageGapError as exc:
        raise bad_request(exc) from exc


@router.get("/assessments")
async def list_platform_airline_coverage_assessments(
    agency_id: str | None = Query(default=None),
    assessment_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = AirlineServiceCoverageGapService(db)
    items = await service.list_assessments(agency_id, assessment_status)
    return {"phase": PHASE_LABEL, "items": items, "count": len(items), **service.safety_flags()}


@router.post("/assessments", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_coverage_assessment(
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    try:
        return await AirlineServiceCoverageGapService(db).create_assessment(payload, user)
    except AirlineServiceCoverageGapError as exc:
        raise bad_request(exc) from exc


@router.get("/assessments/{assessment_id}")
async def get_platform_airline_coverage_assessment(
    assessment_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    try:
        return await AirlineServiceCoverageGapService(db).get_assessment(assessment_id)
    except AirlineServiceCoverageGapError as exc:
        raise bad_request(exc) from exc


@router.get("/gaps")
async def list_platform_airline_knowledge_gaps(
    assessment_id: str | None = Query(default=None),
    agency_id: str | None = Query(default=None),
    airline_code: str | None = Query(default=None),
    service_family: str | None = Query(default=None),
    service_code: str | None = Query(default=None),
    gap_type: str | None = Query(default=None),
    gap_status: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    critical: bool | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = AirlineServiceCoverageGapService(db)
    items = await service.list_gaps(
        assessment_id=assessment_id,
        agency_id=agency_id,
        airline_code=airline_code,
        service_family=service_family,
        service_code=service_code,
        gap_type=gap_type,
        gap_status=gap_status,
        severity=severity,
        critical=critical,
    )
    return {"phase": PHASE_LABEL, "items": items, "count": len(items), **service.safety_flags()}


@router.put("/gaps/{gap_id}")
async def update_platform_airline_knowledge_gap(
    gap_id: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    try:
        return await AirlineServiceCoverageGapService(db).update_gap(gap_id, payload, user)
    except AirlineServiceCoverageGapError as exc:
        raise bad_request(exc) from exc


@router.get("/remediation-plans")
async def list_platform_airline_coverage_remediation_plans(
    agency_id: str | None = Query(default=None),
    assessment_id: str | None = Query(default=None),
    plan_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = AirlineServiceCoverageGapService(db)
    items = await service.list_remediation_plans(agency_id, assessment_id, plan_status)
    return {"phase": PHASE_LABEL, "items": items, "count": len(items), **service.safety_flags()}


@router.post("/remediation-plans", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_coverage_remediation_plan(
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    try:
        return await AirlineServiceCoverageGapService(db).create_remediation_plan(payload, user)
    except AirlineServiceCoverageGapError as exc:
        raise bad_request(exc) from exc


@router.put("/remediation-plans/{plan_id}")
async def update_platform_airline_coverage_remediation_plan(
    plan_id: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    try:
        return await AirlineServiceCoverageGapService(db).update_remediation_plan(plan_id, payload, user)
    except AirlineServiceCoverageGapError as exc:
        raise bad_request(exc) from exc
