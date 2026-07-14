from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import AirlineEvidenceSourceCreate, AirlineEvidenceSourceUpdate
from services.airline_policy_evidence_governance_service import (
    PHASE_LABEL,
    AirlinePolicyEvidenceGovernanceError,
    AirlinePolicyEvidenceGovernanceService,
)
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/airline-evidence", tags=["platform-airline-evidence"])

READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_read(user: dict) -> None:
    await require_any_platform_role(user, READ_ROLES)


async def require_write(user: dict) -> None:
    await require_any_platform_role(user, WRITE_ROLES)


def bad_request(exc: AirlinePolicyEvidenceGovernanceError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("")
async def list_platform_airline_evidence(
    airline_id: str | None = Query(default=None),
    source_type: str | None = Query(default=None),
    evidence_status: str | None = Query(default=None),
    freshness_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    return await AirlinePolicyEvidenceGovernanceService(db).platform_response(
        airline_id=airline_id,
        source_type=source_type,
        evidence_status=evidence_status,
        freshness_status=freshness_status,
    )


@router.post("/sources", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_evidence_source(
    payload: AirlineEvidenceSourceCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    service = AirlinePolicyEvidenceGovernanceService(db)
    try:
        return {"phase": PHASE_LABEL, "source": await service.create_source(payload, user), **service.safety_flags()}
    except AirlinePolicyEvidenceGovernanceError as exc:
        raise bad_request(exc) from exc


@router.get("/sources/{source_id}")
async def get_platform_airline_evidence_source(
    source_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = AirlinePolicyEvidenceGovernanceService(db)
    try:
        return {"phase": PHASE_LABEL, "source": await service.get_source(source_id), **service.safety_flags()}
    except AirlinePolicyEvidenceGovernanceError as exc:
        raise bad_request(exc) from exc


@router.put("/sources/{source_id}")
async def update_platform_airline_evidence_source(
    source_id: str,
    payload: AirlineEvidenceSourceUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    service = AirlinePolicyEvidenceGovernanceService(db)
    try:
        return {"phase": PHASE_LABEL, "source": await service.update_source(source_id, payload, user), **service.safety_flags()}
    except AirlinePolicyEvidenceGovernanceError as exc:
        raise bad_request(exc) from exc


@router.delete("/sources/{source_id}")
async def archive_platform_airline_evidence_source(
    source_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    try:
        return {"phase": PHASE_LABEL, **await AirlinePolicyEvidenceGovernanceService(db).archive_source(source_id, user)}
    except AirlinePolicyEvidenceGovernanceError as exc:
        raise bad_request(exc) from exc


async def create_metadata(kind: str, payload: dict, user: dict, db: Database) -> dict:
    await require_write(user)
    service = AirlinePolicyEvidenceGovernanceService(db)
    methods = {
        "artifact": service.register_artifact,
        "assertion": service.register_assertion,
        "link": service.link_evidence,
        "access": service.create_access_classification,
    }
    try:
        return {"phase": PHASE_LABEL, "item": await methods[kind](payload, user), **service.safety_flags()}
    except AirlinePolicyEvidenceGovernanceError as exc:
        raise bad_request(exc) from exc


@router.post("/artifacts", status_code=status.HTTP_201_CREATED)
async def register_platform_airline_evidence_artifact(payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await create_metadata("artifact", payload, user, db)


@router.post("/assertions", status_code=status.HTTP_201_CREATED)
async def register_platform_airline_evidence_assertion(payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await create_metadata("assertion", payload, user, db)


@router.post("/links", status_code=status.HTTP_201_CREATED)
async def link_platform_airline_evidence(payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await create_metadata("link", payload, user, db)


@router.post("/access-classifications", status_code=status.HTTP_201_CREATED)
async def create_platform_airline_evidence_access_classification(payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await create_metadata("access", payload, user, db)


@router.put("/conflicts/{conflict_id}")
async def review_platform_airline_evidence_conflict(
    conflict_id: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    service = AirlinePolicyEvidenceGovernanceService(db)
    try:
        return {"phase": PHASE_LABEL, **await service.review_conflict(conflict_id, payload, user)}
    except AirlinePolicyEvidenceGovernanceError as exc:
        raise bad_request(exc) from exc


@router.post("/sources/{source_id}/supersede")
async def supersede_platform_airline_evidence_source(
    source_id: str,
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    service = AirlinePolicyEvidenceGovernanceService(db)
    try:
        return {
            "phase": PHASE_LABEL,
            **await service.supersede_source(source_id, str(payload.get("replacement_source_id") or ""), user, payload.get("reason")),
        }
    except AirlinePolicyEvidenceGovernanceError as exc:
        raise bad_request(exc) from exc


@router.post("/freshness-assessments", status_code=status.HTTP_201_CREATED)
async def assess_platform_airline_evidence_freshness(
    payload: dict = Body(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    service = AirlinePolicyEvidenceGovernanceService(db)
    try:
        assessment = await service.assess_freshness(
            source_id=payload.get("source_id"),
            assertion_id=payload.get("assertion_id"),
            actor_user_id=user.get("id"),
        )
        return {"phase": PHASE_LABEL, "assessment": assessment, **service.safety_flags()}
    except AirlinePolicyEvidenceGovernanceError as exc:
        raise bad_request(exc) from exc


@router.get("/unsupported-knowledge")
async def list_platform_unsupported_airline_knowledge(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = AirlinePolicyEvidenceGovernanceService(db)
    items = await service.unsupported_knowledge()
    return {"phase": PHASE_LABEL, "items": items, "count": len(items), **service.safety_flags()}


@router.get("/trace")
async def get_platform_airline_evidence_trace(
    target_type: str = Query(...),
    target_id: str = Query(...),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    return {"phase": PHASE_LABEL, **await AirlinePolicyEvidenceGovernanceService(db).evidence_trace(target_type, target_id)}
