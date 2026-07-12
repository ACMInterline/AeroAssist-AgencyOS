from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    PilotGoldenPathCaseCreate,
    PilotGoldenPathCaseUpdate,
    PilotGoldenPathRunCreateRequest,
    PilotReadinessAssessmentRunRequest,
    PilotReadinessIssueUpdate,
    PilotReadinessProfileCreate,
    PilotReadinessProfileUpdate,
)
from services.pilot_readiness_service import PHASE_LABEL, PilotReadinessError, PilotReadinessService
from services.tenant_service import require_any_platform_role


router = APIRouter(tags=["platform-pilot-readiness"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("/api/platform/pilot-readiness")
async def platform_pilot_readiness_dashboard(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await PilotReadinessService(db).platform_dashboard(agency_id=agency_id)


@router.get("/api/platform/pilot-readiness/summary")
async def platform_pilot_readiness_summary(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = PilotReadinessService(db)
    return {"phase": PHASE_LABEL, "summary": await service.summary(agency_id), "metadata_only": True, **service.safety_flags()}


@router.get("/api/platform/pilot-readiness/module-readiness")
async def platform_pilot_readiness_modules(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = PilotReadinessService(db)
    return {"phase": PHASE_LABEL, "module_readiness": await service.module_readiness_summary(agency_id), "metadata_only": True, **service.safety_flags()}


@router.get("/api/platform/pilot-readiness/airline-service-coverage")
async def platform_pilot_readiness_airline_service_coverage(
    agency_id: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = PilotReadinessService(db)
    return {"phase": PHASE_LABEL, "airline_service_coverage": await service.airline_service_coverage_summary(agency_id), "metadata_only": True, **service.safety_flags()}


@router.get("/api/platform/pilot-readiness/sample-cases")
async def platform_pilot_readiness_sample_cases(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = PilotReadinessService(db)
    return {"phase": PHASE_LABEL, "sample_cases": service.sample_case_templates(), "auto_seed_disabled": True, "metadata_only": True, **service.safety_flags()}


@router.get("/api/platform/pilot-readiness/profiles")
async def list_platform_pilot_readiness_profiles(
    agency_id: str | None = Query(default=None),
    profile_status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = PilotReadinessService(db)
    return {
        "phase": PHASE_LABEL,
        "profiles": await service.list_profiles(agency_id=agency_id, profile_status=profile_status, search=search, include_archived=include_archived),
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.post("/api/platform/pilot-readiness/profiles", status_code=status.HTTP_201_CREATED)
async def create_platform_pilot_readiness_profile(
    payload: PilotReadinessProfileCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await PilotReadinessService(db).create_profile(payload, user)
    except PilotReadinessError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/api/platform/pilot-readiness/profiles/{profile_id}")
async def get_platform_pilot_readiness_profile(
    profile_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    try:
        profile = await PilotReadinessService(db).get_profile(profile_id)
    except PilotReadinessError as exc:
        raise bad_request(str(exc)) from exc
    service = PilotReadinessService(db)
    return {"phase": PHASE_LABEL, "pilot_readiness_profile": profile, "metadata_only": True, **service.safety_flags()}


@router.put("/api/platform/pilot-readiness/profiles/{profile_id}")
async def update_platform_pilot_readiness_profile(
    profile_id: str,
    payload: PilotReadinessProfileUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await PilotReadinessService(db).update_profile(profile_id, payload, user)
    except PilotReadinessError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/api/platform/pilot-readiness/assessments")
async def list_platform_pilot_readiness_assessments(
    agency_id: str | None = Query(default=None),
    assessment_status: str | None = Query(default=None),
    profile_id: str | None = Query(default=None),
    airline_code: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = PilotReadinessService(db)
    return {
        "phase": PHASE_LABEL,
        "assessments": await service.list_assessments(agency_id=agency_id, assessment_status=assessment_status, profile_id=profile_id, airline_code=airline_code),
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.post("/api/platform/pilot-readiness/assessments/run", status_code=status.HTTP_201_CREATED)
async def run_platform_pilot_readiness_assessment(
    payload: PilotReadinessAssessmentRunRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await PilotReadinessService(db).run_assessment(payload, user)
    except PilotReadinessError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/api/platform/pilot-readiness/assessments/{assessment_id}")
async def get_platform_pilot_readiness_assessment(
    assessment_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    try:
        assessment = await PilotReadinessService(db).get_assessment(assessment_id)
    except PilotReadinessError as exc:
        raise bad_request(str(exc)) from exc
    service = PilotReadinessService(db)
    return {"phase": PHASE_LABEL, "pilot_readiness_assessment": assessment, "metadata_only": True, **service.safety_flags()}


@router.get("/api/platform/pilot-readiness/golden-path-cases")
async def list_platform_pilot_golden_path_cases(
    agency_id: str | None = Query(default=None),
    case_family: str | None = Query(default=None),
    scenario_type: str | None = Query(default=None),
    case_status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = PilotReadinessService(db)
    return {
        "phase": PHASE_LABEL,
        "golden_path_cases": await service.list_cases(agency_id=agency_id, case_family=case_family, scenario_type=scenario_type, case_status=case_status, search=search, include_archived=include_archived),
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.post("/api/platform/pilot-readiness/golden-path-cases", status_code=status.HTTP_201_CREATED)
async def create_platform_pilot_golden_path_case(
    payload: PilotGoldenPathCaseCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await PilotReadinessService(db).create_case(payload, user)
    except PilotReadinessError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/api/platform/pilot-readiness/golden-path-cases/{case_id}")
async def get_platform_pilot_golden_path_case(
    case_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    try:
        case = await PilotReadinessService(db).get_case(case_id)
    except PilotReadinessError as exc:
        raise bad_request(str(exc)) from exc
    service = PilotReadinessService(db)
    return {"phase": PHASE_LABEL, "pilot_golden_path_case": case, "metadata_only": True, **service.safety_flags()}


@router.put("/api/platform/pilot-readiness/golden-path-cases/{case_id}")
async def update_platform_pilot_golden_path_case(
    case_id: str,
    payload: PilotGoldenPathCaseUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await PilotReadinessService(db).update_case(case_id, payload, user)
    except PilotReadinessError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/api/platform/pilot-readiness/golden-path-cases/{case_id}/runs", status_code=status.HTTP_201_CREATED)
async def run_platform_pilot_golden_path_case(
    case_id: str,
    payload: PilotGoldenPathRunCreateRequest | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await PilotReadinessService(db).run_golden_path_case(case_id, payload or PilotGoldenPathRunCreateRequest(), user)
    except PilotReadinessError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/api/platform/pilot-readiness/golden-path-runs")
async def list_platform_pilot_golden_path_runs(
    agency_id: str | None = Query(default=None),
    case_id: str | None = Query(default=None),
    run_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = PilotReadinessService(db)
    return {"phase": PHASE_LABEL, "golden_path_runs": await service.list_runs(agency_id=agency_id, case_id=case_id, run_status=run_status), "metadata_only": True, **service.safety_flags()}


@router.get("/api/platform/pilot-readiness/issues")
async def list_platform_pilot_readiness_issues(
    agency_id: str | None = Query(default=None),
    assessment_id: str | None = Query(default=None),
    golden_path_run_id: str | None = Query(default=None),
    issue_status: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = PilotReadinessService(db)
    return {
        "phase": PHASE_LABEL,
        "issues": await service.list_issues(agency_id=agency_id, assessment_id=assessment_id, golden_path_run_id=golden_path_run_id, issue_status=issue_status, severity=severity),
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/api/platform/pilot-readiness/issues/{issue_id}")
async def update_platform_pilot_readiness_issue(
    issue_id: str,
    payload: PilotReadinessIssueUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await PilotReadinessService(db).update_issue(issue_id, payload, user)
    except PilotReadinessError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/api/platform/pilot-readiness/issues/{issue_id}/resolve")
async def resolve_platform_pilot_readiness_issue(
    issue_id: str,
    payload: PilotReadinessIssueUpdate | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await PilotReadinessService(db).resolve_issue(issue_id, payload or PilotReadinessIssueUpdate(), user)
    except PilotReadinessError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/api/platform/pilot-readiness/issues/{issue_id}/reopen")
async def reopen_platform_pilot_readiness_issue(
    issue_id: str,
    payload: PilotReadinessIssueUpdate | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await PilotReadinessService(db).reopen_issue(issue_id, payload or PilotReadinessIssueUpdate(), user)
    except PilotReadinessError as exc:
        raise bad_request(str(exc)) from exc
