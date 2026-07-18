from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import require_platform_role
from database import Database, get_database
from models import (
    PilotAgencyInvitationCreate,
    PilotAgencyStatusChange,
    PilotHealthTimelineEventCreate,
    PilotOperationalEvidenceCreate,
    PilotReleaseProductionEvidence,
    PilotReleaseSignOff,
    PilotSyntheticDatasetCreate,
    PilotSyntheticDatasetRemoval,
)
from services.pilot_operations_release_readiness_service import (
    PHASE_LABEL,
    PilotOperationsError,
    PilotOperationsReleaseReadinessService,
)


router = APIRouter(
    prefix="/api/platform/pilot-operations",
    tags=["platform-pilot-operations-release-readiness"],
)

READ_ROLES = ["platform_owner", "platform_admin", "platform_support"]
EVIDENCE_ROLES = ["platform_owner", "platform_admin", "platform_support"]
SIGN_OFF_ROLES = ["platform_owner", "platform_admin"]
OWNER_ONLY = ["platform_owner"]


def bad_request(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("")
async def get_pilot_operations_dashboard(
    _user: dict = Depends(require_platform_role(READ_ROLES)),
    db: Database = Depends(get_database),
) -> dict:
    return await PilotOperationsReleaseReadinessService(db).dashboard()


@router.get("/evidence")
async def list_operational_evidence(
    evidence_type: str | None = Query(default=None),
    evidence_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=200),
    _user: dict = Depends(require_platform_role(READ_ROLES)),
    db: Database = Depends(get_database),
) -> dict:
    try:
        items = await PilotOperationsReleaseReadinessService(db).list_evidence(
            evidence_type=evidence_type, status=evidence_status, limit=limit
        )
    except PilotOperationsError as exc:
        raise bad_request(exc) from exc
    return {"phase": PHASE_LABEL, "items": items, "count": len(items)}


@router.post("/evidence", status_code=status.HTTP_201_CREATED)
async def create_operational_evidence(
    payload: PilotOperationalEvidenceCreate,
    user: dict = Depends(require_platform_role(EVIDENCE_ROLES)),
    db: Database = Depends(get_database),
) -> dict:
    try:
        item = await PilotOperationsReleaseReadinessService(db).create_evidence(payload, user)
    except PilotOperationsError as exc:
        raise bad_request(exc) from exc
    return {"phase": PHASE_LABEL, "evidence": item}


@router.post("/release-assessments", status_code=status.HTTP_201_CREATED)
async def assess_pilot_release(
    payload: PilotReleaseProductionEvidence,
    user: dict = Depends(require_platform_role(EVIDENCE_ROLES)),
    db: Database = Depends(get_database),
) -> dict:
    try:
        item = await PilotOperationsReleaseReadinessService(db).assess_release(payload, user)
    except PilotOperationsError as exc:
        raise bad_request(exc) from exc
    return {"phase": PHASE_LABEL, "assessment_evidence": item, "automatic_approval_disabled": True}


@router.post("/pilot-sign-offs", status_code=status.HTTP_201_CREATED)
async def record_pilot_sign_off(
    payload: PilotReleaseSignOff,
    user: dict = Depends(require_platform_role(SIGN_OFF_ROLES)),
    db: Database = Depends(get_database),
) -> dict:
    try:
        item = await PilotOperationsReleaseReadinessService(db).record_sign_off(payload, user)
    except PilotOperationsError as exc:
        raise bad_request(exc) from exc
    return {"phase": PHASE_LABEL, "sign_off": item, "automatic_approval_disabled": True}


@router.get("/pilot-agencies")
async def list_pilot_agencies(
    _user: dict = Depends(require_platform_role(READ_ROLES)),
    db: Database = Depends(get_database),
) -> dict:
    items = await PilotOperationsReleaseReadinessService(db).list_enrollments()
    return {"phase": PHASE_LABEL, "items": items, "count": len(items)}


@router.post("/pilot-agencies/invitations", status_code=status.HTTP_201_CREATED)
async def invite_pilot_agency(
    payload: PilotAgencyInvitationCreate,
    user: dict = Depends(require_platform_role(OWNER_ONLY)),
    db: Database = Depends(get_database),
) -> dict:
    try:
        item = await PilotOperationsReleaseReadinessService(db).invite_agency(payload, user)
    except PilotOperationsError as exc:
        raise bad_request(exc) from exc
    return {"phase": PHASE_LABEL, "pilot_agency": item, "invitation_email_sent": False}


@router.post("/pilot-agencies/{enrollment_id}/enable")
async def enable_pilot_agency(
    enrollment_id: str,
    payload: PilotAgencyStatusChange,
    user: dict = Depends(require_platform_role(OWNER_ONLY)),
    db: Database = Depends(get_database),
) -> dict:
    return await change_pilot_status(enrollment_id, "enabled", payload.reason, user, db)


@router.post("/pilot-agencies/{enrollment_id}/activate")
async def activate_pilot_agency(
    enrollment_id: str,
    payload: PilotAgencyStatusChange,
    user: dict = Depends(require_platform_role(OWNER_ONLY)),
    db: Database = Depends(get_database),
) -> dict:
    return await change_pilot_status(enrollment_id, "activated", payload.reason, user, db)


@router.post("/pilot-agencies/{enrollment_id}/disable")
async def disable_pilot_agency(
    enrollment_id: str,
    payload: PilotAgencyStatusChange,
    user: dict = Depends(require_platform_role(OWNER_ONLY)),
    db: Database = Depends(get_database),
) -> dict:
    return await change_pilot_status(enrollment_id, "disabled", payload.reason, user, db)


async def change_pilot_status(
    enrollment_id: str,
    target_status: str,
    reason: str,
    user: dict,
    db: Database,
) -> dict:
    try:
        item = await PilotOperationsReleaseReadinessService(db).change_enrollment_status(
            enrollment_id, target_status, reason, user
        )
    except PilotOperationsError as exc:
        raise bad_request(exc) from exc
    return {"phase": PHASE_LABEL, "pilot_agency": item}


@router.get("/synthetic-datasets")
async def list_synthetic_datasets(
    include_removed: bool = Query(default=True),
    _user: dict = Depends(require_platform_role(READ_ROLES)),
    db: Database = Depends(get_database),
) -> dict:
    items = await PilotOperationsReleaseReadinessService(db).list_synthetic_datasets(include_removed=include_removed)
    return {"phase": PHASE_LABEL, "items": items, "count": len(items)}


@router.post("/synthetic-datasets", status_code=status.HTTP_201_CREATED)
async def create_synthetic_dataset(
    payload: PilotSyntheticDatasetCreate,
    user: dict = Depends(require_platform_role(OWNER_ONLY)),
    db: Database = Depends(get_database),
) -> dict:
    try:
        item = await PilotOperationsReleaseReadinessService(db).create_synthetic_dataset(payload, user)
    except PilotOperationsError as exc:
        raise bad_request(exc) from exc
    return {"phase": PHASE_LABEL, "synthetic_dataset": item}


@router.post("/synthetic-datasets/{dataset_id}/remove")
async def remove_synthetic_dataset(
    dataset_id: str,
    payload: PilotSyntheticDatasetRemoval,
    user: dict = Depends(require_platform_role(OWNER_ONLY)),
    db: Database = Depends(get_database),
) -> dict:
    try:
        item = await PilotOperationsReleaseReadinessService(db).remove_synthetic_dataset(dataset_id, payload.reason, user)
    except PilotOperationsError as exc:
        raise bad_request(exc) from exc
    return {"phase": PHASE_LABEL, "synthetic_dataset": item, "hard_delete_performed": False}


@router.get("/health-timeline")
async def list_health_timeline(
    event_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    _user: dict = Depends(require_platform_role(READ_ROLES)),
    db: Database = Depends(get_database),
) -> dict:
    try:
        items = await PilotOperationsReleaseReadinessService(db).list_health_timeline(event_type=event_type, limit=limit)
    except PilotOperationsError as exc:
        raise bad_request(exc) from exc
    return {"phase": PHASE_LABEL, "items": items, "count": len(items)}


@router.post("/health-timeline", status_code=status.HTTP_201_CREATED)
async def create_health_timeline_event(
    payload: PilotHealthTimelineEventCreate,
    user: dict = Depends(require_platform_role(EVIDENCE_ROLES)),
    db: Database = Depends(get_database),
) -> dict:
    try:
        item = await PilotOperationsReleaseReadinessService(db).create_health_event(payload, user)
    except PilotOperationsError as exc:
        raise bad_request(exc) from exc
    return {"phase": PHASE_LABEL, "timeline_event": item}


@router.get("/production-diagnostics")
async def get_production_diagnostics(
    _user: dict = Depends(require_platform_role(READ_ROLES)),
    db: Database = Depends(get_database),
) -> dict:
    return await PilotOperationsReleaseReadinessService(db).production_diagnostics()
