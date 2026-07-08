from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import OperationalConstraintCreate, OperationalConstraintUpdate
from services.operational_constraint_engine_service import PHASE_LABEL, OperationalConstraintEngineError, OperationalConstraintEngineService
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/operational-constraints", tags=["platform-operational-constraints"])

PLATFORM_READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
PLATFORM_WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_platform_read(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_READ_ROLES)


async def require_platform_write(user: dict) -> None:
    await require_any_platform_role(user, PLATFORM_WRITE_ROLES)


def bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.get("")
async def list_platform_operational_constraints(
    agency_id: str | None = Query(default=None),
    acquisition_id: str | None = Query(default=None),
    airline: str | None = Query(default=None),
    service_domain: str | None = Query(default=None),
    service_family: str | None = Query(default=None),
    ssr_code: str | None = Query(default=None),
    rfic: str | None = Query(default=None),
    rfisc: str | None = Query(default=None),
    constraint_status: str | None = Query(default=None),
    outcome_type: str | None = Query(default=None),
    review_status: str | None = Query(default=None),
    approval_status: str | None = Query(default=None),
    evaluation_ready: bool | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await OperationalConstraintEngineService(db).platform_response(
        agency_id=agency_id,
        acquisition_id=acquisition_id,
        airline=airline,
        service_domain=service_domain,
        service_family=service_family,
        ssr_code=ssr_code,
        rfic=rfic,
        rfisc=rfisc,
        constraint_status=constraint_status,
        outcome_type=outcome_type,
        review_status=review_status,
        approval_status=approval_status,
        evaluation_ready=evaluation_ready,
        include_archived=include_archived,
    )


@router.get("/summary")
async def summarize_platform_operational_constraints(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    return await OperationalConstraintEngineService(db).platform_summary()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_platform_operational_constraint(
    payload: OperationalConstraintCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalConstraintEngineService(db).create_constraint(payload, user)
    except OperationalConstraintEngineError as exc:
        raise bad_request(str(exc)) from exc


@router.get("/{constraint_id}")
async def get_platform_operational_constraint(
    constraint_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_read(user)
    service = OperationalConstraintEngineService(db)
    try:
        constraint = await service.get_platform_constraint(constraint_id)
    except OperationalConstraintEngineError as exc:
        raise bad_request(str(exc)) from exc
    return {
        "phase": PHASE_LABEL,
        "operational_constraint": constraint,
        "read_only": False,
        "metadata_only": True,
        **service.safety_flags(),
    }


@router.put("/{constraint_id}")
async def update_platform_operational_constraint(
    constraint_id: str,
    payload: OperationalConstraintUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalConstraintEngineService(db).update_constraint(constraint_id, payload, user)
    except OperationalConstraintEngineError as exc:
        raise bad_request(str(exc)) from exc


@router.delete("/{constraint_id}")
async def delete_platform_operational_constraint(
    constraint_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_platform_write(user)
    try:
        return await OperationalConstraintEngineService(db).delete_constraint(constraint_id, user)
    except OperationalConstraintEngineError as exc:
        raise bad_request(str(exc)) from exc
