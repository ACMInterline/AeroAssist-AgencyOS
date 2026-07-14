from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.airline_intelligence_scale_readiness_service import (
    PHASE_LABEL,
    AirlineIntelligenceScaleReadinessError,
    AirlineIntelligenceScaleReadinessService,
)
from services.tenant_service import require_any_platform_role


router = APIRouter(
    prefix="/api/platform/airline-intelligence-readiness",
    tags=["platform-airline-intelligence-readiness"],
)

READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_read(user: dict) -> None:
    await require_any_platform_role(user, READ_ROLES)


async def require_write(user: dict) -> None:
    await require_any_platform_role(user, WRITE_ROLES)


def bad_request(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("")
async def get_platform_airline_intelligence_readiness(
    agency_id: str | None = Query(default=None),
    airline_code: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    issue_status: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    return await AirlineIntelligenceScaleReadinessService(db).platform_dashboard(
        agency_id=agency_id,
        airline_code=airline_code,
        status=status_filter,
        issue_status=issue_status,
        severity=severity,
    )


@router.get("/summary")
async def summarize_platform_airline_intelligence_readiness(
    agency_id: str | None = Query(default=None),
    airline_code: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = AirlineIntelligenceScaleReadinessService(db)
    response = await service.platform_dashboard(agency_id=agency_id, airline_code=airline_code)
    return {"phase": PHASE_LABEL, "summary": response["summary"], **service.safety_flags()}


@router.get("/filters")
async def get_platform_airline_intelligence_readiness_filters(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = AirlineIntelligenceScaleReadinessService(db)
    return {"phase": PHASE_LABEL, "filters": service.filter_metadata(), **service.safety_flags()}


@router.get("/assessment-templates")
async def get_platform_airline_intelligence_assessment_templates(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = AirlineIntelligenceScaleReadinessService(db)
    return {"phase": PHASE_LABEL, "items": service.assessment_templates(), "count": len(service.assessment_templates()), **service.safety_flags()}


@router.post("/profiles", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_intelligence_readiness_profile(
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    try:
        return await AirlineIntelligenceScaleReadinessService(db).create_profile(payload, user)
    except (AirlineIntelligenceScaleReadinessError, ValueError) as exc:
        raise bad_request(exc) from exc


@router.put("/profiles/{profile_id}")
async def update_platform_airline_intelligence_readiness_profile(
    profile_id: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    try:
        return await AirlineIntelligenceScaleReadinessService(db).update_profile(profile_id, payload, user)
    except (AirlineIntelligenceScaleReadinessError, ValueError) as exc:
        raise bad_request(exc) from exc


@router.get("/assessments")
async def list_platform_airline_intelligence_readiness_assessments(
    agency_id: str | None = Query(default=None),
    airline_code: str | None = Query(default=None),
    assessment_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = AirlineIntelligenceScaleReadinessService(db)
    items = await service.list_assessments(agency_id=agency_id, airline_code=airline_code, status=assessment_status)
    return {"phase": PHASE_LABEL, "items": items, "count": len(items), **service.safety_flags()}


@router.post("/assessments/run", status_code=status.HTTP_201_CREATED)
async def run_platform_airline_intelligence_readiness_assessment(
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    try:
        return await AirlineIntelligenceScaleReadinessService(db).run_assessment(payload, user)
    except (AirlineIntelligenceScaleReadinessError, ValueError) as exc:
        raise bad_request(exc) from exc


@router.get("/release-candidates")
async def list_platform_airline_intelligence_release_candidates(
    agency_id: str | None = Query(default=None),
    airline_code: str | None = Query(default=None),
    candidate_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = AirlineIntelligenceScaleReadinessService(db)
    items = await service.list_candidates(agency_id=agency_id, airline_code=airline_code, status=candidate_status)
    return {"phase": PHASE_LABEL, "items": items, "count": len(items), **service.safety_flags()}


@router.post("/release-candidates", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_intelligence_release_candidate(
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    try:
        return await AirlineIntelligenceScaleReadinessService(db).create_release_candidate(payload, user)
    except (AirlineIntelligenceScaleReadinessError, ValueError) as exc:
        raise bad_request(exc) from exc


@router.get("/release-candidates/{candidate_id}")
async def get_platform_airline_intelligence_release_candidate(
    candidate_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    try:
        return await AirlineIntelligenceScaleReadinessService(db).get_candidate(candidate_id)
    except AirlineIntelligenceScaleReadinessError as exc:
        raise bad_request(exc) from exc


@router.post("/release-candidates/{candidate_id}/evaluate-gates")
async def evaluate_platform_airline_intelligence_release_gates(
    candidate_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    try:
        return await AirlineIntelligenceScaleReadinessService(db).evaluate_release_gates(candidate_id, user)
    except AirlineIntelligenceScaleReadinessError as exc:
        raise bad_request(exc) from exc


@router.post("/release-candidates/{candidate_id}/decisions", status_code=status.HTTP_201_CREATED)
async def decide_platform_airline_intelligence_release(
    candidate_id: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    try:
        return await AirlineIntelligenceScaleReadinessService(db).decide_release(candidate_id, payload, user)
    except AirlineIntelligenceScaleReadinessError as exc:
        raise bad_request(exc) from exc


@router.get("/population-waves")
async def list_platform_airline_intelligence_population_waves(
    agency_id: str | None = Query(default=None),
    wave_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = AirlineIntelligenceScaleReadinessService(db)
    items = await service.list_waves(agency_id=agency_id, status=wave_status)
    return {"phase": PHASE_LABEL, "items": items, "count": len(items), **service.safety_flags()}


@router.post("/population-waves", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_intelligence_population_wave(
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    try:
        return await AirlineIntelligenceScaleReadinessService(db).create_population_wave(payload, user)
    except (AirlineIntelligenceScaleReadinessError, ValueError) as exc:
        raise bad_request(exc) from exc


@router.put("/population-waves/{wave_id}")
async def update_platform_airline_intelligence_population_wave(
    wave_id: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    try:
        return await AirlineIntelligenceScaleReadinessService(db).update_population_wave(wave_id, payload, user)
    except (AirlineIntelligenceScaleReadinessError, ValueError) as exc:
        raise bad_request(exc) from exc


@router.get("/issues")
async def list_platform_airline_intelligence_scale_issues(
    agency_id: str | None = Query(default=None),
    airline_code: str | None = Query(default=None),
    issue_status: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = AirlineIntelligenceScaleReadinessService(db)
    items = await service.list_issues(agency_id=agency_id, airline_code=airline_code, issue_status=issue_status, severity=severity)
    return {"phase": PHASE_LABEL, "items": items, "count": len(items), **service.safety_flags()}


@router.put("/issues/{issue_id}")
async def update_platform_airline_intelligence_scale_issue(
    issue_id: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    try:
        return await AirlineIntelligenceScaleReadinessService(db).update_issue(issue_id, payload, user)
    except AirlineIntelligenceScaleReadinessError as exc:
        raise bad_request(exc) from exc
