from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.airline_policy_evidence_governance_service import (
    PHASE_LABEL,
    AirlinePolicyEvidenceGovernanceError,
    AirlinePolicyEvidenceGovernanceService,
)
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/airline-evidence", tags=["agency-airline-evidence"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


@router.get("")
async def list_agency_airline_evidence(
    agency_id: str,
    airline_id: str | None = Query(default=None),
    source_type: str | None = Query(default=None),
    evidence_status: str | None = Query(default=None),
    freshness_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return await AirlinePolicyEvidenceGovernanceService(db).agency_response(
        agency_id,
        airline_id=airline_id,
        source_type=source_type,
        evidence_status=evidence_status,
        freshness_status=freshness_status,
    )


@router.get("/sources/{source_id}")
async def get_agency_airline_evidence_source(
    agency_id: str,
    source_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = AirlinePolicyEvidenceGovernanceService(db)
    try:
        return {"phase": PHASE_LABEL, "agency_id": agency_id, "source": await service.get_source(source_id, agency_id=agency_id, agency_safe=True), "read_only": True, **service.safety_flags()}
    except AirlinePolicyEvidenceGovernanceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/trace")
async def get_agency_airline_evidence_trace(
    agency_id: str,
    target_type: str = Query(...),
    target_id: str = Query(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {
        "phase": PHASE_LABEL,
        "agency_id": agency_id,
        **await AirlinePolicyEvidenceGovernanceService(db).evidence_trace(target_type, target_id, agency_id=agency_id, agency_safe=True),
        "read_only": True,
    }
