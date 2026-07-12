from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    PilotGoldenPathCaseCreate,
    PilotGoldenPathCaseUpdate,
    PilotGoldenPathRunCreateRequest,
    PilotReadinessAssessmentRunRequest,
    PilotReadinessIssueUpdate,
)
from services.pilot_readiness_service import PHASE_LABEL, PilotReadinessError, PilotReadinessService
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(tags=["agency-pilot-readiness"])

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


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


@router.get("/api/agencies/{agency_id}/pilot-readiness")
async def agency_pilot_readiness_dashboard(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await PilotReadinessService(db).agency_dashboard(agency_id)


@router.get("/api/agencies/{agency_id}/pilot-readiness/summary")
async def agency_pilot_readiness_summary(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = PilotReadinessService(db)
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "summary": await service.summary(agency_id), "metadata_only": True, **service.safety_flags()}


@router.get("/api/agencies/{agency_id}/pilot-readiness/module-readiness")
async def agency_pilot_readiness_modules(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = PilotReadinessService(db)
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "module_readiness": await service.module_readiness_summary(agency_id), "metadata_only": True, **service.safety_flags()}


@router.get("/api/agencies/{agency_id}/pilot-readiness/airline-service-coverage")
async def agency_pilot_readiness_airline_service_coverage(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = PilotReadinessService(db)
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "airline_service_coverage": await service.airline_service_coverage_summary(agency_id), "metadata_only": True, **service.safety_flags()}


@router.get("/api/agencies/{agency_id}/pilot-readiness/remediation-checklist")
async def agency_pilot_readiness_remediation_checklist(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = PilotReadinessService(db)
    issues = await service.list_issues(agency_id=agency_id)
    modules = await service.module_readiness_summary(agency_id)
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        "remediation_checklist": [
            {
                "item_key": issue.get("issue_reference"),
                "label": issue.get("title"),
                "severity": issue.get("severity"),
                "status": issue.get("issue_status"),
                "agency_route": issue.get("agency_remediation_route"),
                "platform_route": issue.get("remediation_route"),
            }
            for issue in issues
            if issue.get("issue_status") in {"open", "in_review", "reopened"}
        ],
        "module_readiness": modules,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.get("/api/agencies/{agency_id}/pilot-readiness/sample-cases")
async def agency_pilot_readiness_sample_cases(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = PilotReadinessService(db)
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "sample_cases": service.sample_case_templates(), "auto_seed_disabled": True, "metadata_only": True, **service.safety_flags()}


@router.get("/api/agencies/{agency_id}/pilot-readiness/profiles")
async def list_agency_pilot_readiness_profiles(
    agency_id: str,
    profile_status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = PilotReadinessService(db)
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "profiles": await service.list_profiles(agency_id=agency_id, profile_status=profile_status, search=search, include_archived=include_archived), "metadata_only": True, **service.safety_flags()}


@router.get("/api/agencies/{agency_id}/pilot-readiness/profiles/{profile_id}")
async def get_agency_pilot_readiness_profile(
    agency_id: str,
    profile_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = PilotReadinessService(db)
    try:
        profile = await service.get_profile(profile_id, agency_id=agency_id)
    except PilotReadinessError:
        raise not_found("Pilot readiness profile metadata not found.")
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "pilot_readiness_profile": profile, "metadata_only": True, **service.safety_flags()}


@router.get("/api/agencies/{agency_id}/pilot-readiness/assessments")
async def list_agency_pilot_readiness_assessments(
    agency_id: str,
    assessment_status: str | None = Query(default=None),
    profile_id: str | None = Query(default=None),
    airline_code: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = PilotReadinessService(db)
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "assessments": await service.list_assessments(agency_id=agency_id, assessment_status=assessment_status, profile_id=profile_id, airline_code=airline_code), "metadata_only": True, **service.safety_flags()}


@router.post("/api/agencies/{agency_id}/pilot-readiness/assessments/run", status_code=status.HTTP_201_CREATED)
async def run_agency_pilot_readiness_assessment(
    agency_id: str,
    payload: PilotReadinessAssessmentRunRequest,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await PilotReadinessService(db).run_assessment(payload, user, agency_id=agency_id)
    except PilotReadinessError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/api/agencies/{agency_id}/pilot-readiness/assessments/{assessment_id}")
async def get_agency_pilot_readiness_assessment(
    agency_id: str,
    assessment_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = PilotReadinessService(db)
    try:
        assessment = await service.get_assessment(assessment_id, agency_id=agency_id)
    except PilotReadinessError:
        raise not_found("Pilot readiness assessment metadata not found.")
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "pilot_readiness_assessment": assessment, "metadata_only": True, **service.safety_flags()}


@router.get("/api/agencies/{agency_id}/pilot-readiness/golden-path-cases")
async def list_agency_pilot_golden_path_cases(
    agency_id: str,
    case_family: str | None = Query(default=None),
    scenario_type: str | None = Query(default=None),
    case_status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = PilotReadinessService(db)
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "golden_path_cases": await service.list_cases(agency_id=agency_id, case_family=case_family, scenario_type=scenario_type, case_status=case_status, search=search, include_archived=include_archived), "metadata_only": True, **service.safety_flags()}


@router.post("/api/agencies/{agency_id}/pilot-readiness/golden-path-cases", status_code=status.HTTP_201_CREATED)
async def create_agency_pilot_golden_path_case(
    agency_id: str,
    payload: PilotGoldenPathCaseCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await PilotReadinessService(db).create_case(payload, user, agency_id=agency_id)
    except PilotReadinessError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/api/agencies/{agency_id}/pilot-readiness/golden-path-cases/{case_id}")
async def get_agency_pilot_golden_path_case(
    agency_id: str,
    case_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = PilotReadinessService(db)
    try:
        case = await service.get_case(case_id, agency_id=agency_id)
    except PilotReadinessError:
        raise not_found("Pilot golden-path case metadata not found.")
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "pilot_golden_path_case": case, "metadata_only": True, **service.safety_flags()}


@router.put("/api/agencies/{agency_id}/pilot-readiness/golden-path-cases/{case_id}")
async def update_agency_pilot_golden_path_case(
    agency_id: str,
    case_id: str,
    payload: PilotGoldenPathCaseUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await PilotReadinessService(db).update_case(case_id, payload, user, agency_id=agency_id)
    except PilotReadinessError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/api/agencies/{agency_id}/pilot-readiness/golden-path-cases/{case_id}/runs", status_code=status.HTTP_201_CREATED)
async def run_agency_pilot_golden_path_case(
    agency_id: str,
    case_id: str,
    payload: PilotGoldenPathRunCreateRequest | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await PilotReadinessService(db).run_golden_path_case(case_id, payload or PilotGoldenPathRunCreateRequest(), user, agency_id=agency_id)
    except PilotReadinessError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/api/agencies/{agency_id}/pilot-readiness/golden-path-runs")
async def list_agency_pilot_golden_path_runs(
    agency_id: str,
    case_id: str | None = Query(default=None),
    run_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = PilotReadinessService(db)
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "golden_path_runs": await service.list_runs(agency_id=agency_id, case_id=case_id, run_status=run_status), "metadata_only": True, **service.safety_flags()}


@router.get("/api/agencies/{agency_id}/pilot-readiness/issues")
async def list_agency_pilot_readiness_issues(
    agency_id: str,
    assessment_id: str | None = Query(default=None),
    golden_path_run_id: str | None = Query(default=None),
    issue_status: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = PilotReadinessService(db)
    return {"phase": PHASE_LABEL, "agency_id": agency_id, "issues": await service.list_issues(agency_id=agency_id, assessment_id=assessment_id, golden_path_run_id=golden_path_run_id, issue_status=issue_status, severity=severity), "metadata_only": True, **service.safety_flags()}


@router.put("/api/agencies/{agency_id}/pilot-readiness/issues/{issue_id}")
async def update_agency_pilot_readiness_issue(
    agency_id: str,
    issue_id: str,
    payload: PilotReadinessIssueUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await PilotReadinessService(db).update_issue(issue_id, payload, user, agency_id=agency_id)
    except PilotReadinessError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/api/agencies/{agency_id}/pilot-readiness/issues/{issue_id}/resolve")
async def resolve_agency_pilot_readiness_issue(
    agency_id: str,
    issue_id: str,
    payload: PilotReadinessIssueUpdate | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await PilotReadinessService(db).resolve_issue(issue_id, payload or PilotReadinessIssueUpdate(), user, agency_id=agency_id)
    except PilotReadinessError as exc:
        raise bad_request(str(exc)) from exc


@router.post("/api/agencies/{agency_id}/pilot-readiness/issues/{issue_id}/reopen")
async def reopen_agency_pilot_readiness_issue(
    agency_id: str,
    issue_id: str,
    payload: PilotReadinessIssueUpdate | None = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await PilotReadinessService(db).reopen_issue(issue_id, payload or PilotReadinessIssueUpdate(), user, agency_id=agency_id)
    except PilotReadinessError as exc:
        raise bad_request(str(exc)) from exc
