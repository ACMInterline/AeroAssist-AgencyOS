from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import AirlineMasterProfileCreate, AirlineMasterProfileUpdate
from services.airline_master_profile_intelligence_service import (
    PHASE_LABEL,
    AirlineMasterProfileError,
    AirlineMasterProfileIntelligenceService,
)
from services.tenant_service import require_any_platform_role


router = APIRouter(prefix="/api/platform/airline-master-profiles", tags=["platform-airline-master-profiles"])

READ_ROLES = ["platform_owner", "platform_admin", "platform_support", "platform_knowledge_editor"]
WRITE_ROLES = ["platform_owner", "platform_admin", "platform_knowledge_editor"]


async def require_read(user: dict) -> None:
    await require_any_platform_role(user, READ_ROLES)


async def require_write(user: dict) -> None:
    await require_any_platform_role(user, WRITE_ROLES)


def bad_request(exc: AirlineMasterProfileError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("")
async def list_airline_master_profiles(
    search: str | None = Query(default=None),
    review_status: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    return await AirlineMasterProfileIntelligenceService(db).response(search=search, review_status=review_status)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_airline_master_profile(
    payload: AirlineMasterProfileCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    try:
        return {"phase": PHASE_LABEL, "item": await AirlineMasterProfileIntelligenceService(db).create_profile(payload, user)}
    except AirlineMasterProfileError as exc:
        raise bad_request(exc) from exc


@router.get("/coverage")
async def get_airline_master_profile_coverage(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = AirlineMasterProfileIntelligenceService(db)
    return {"phase": PHASE_LABEL, "coverage": await service.coverage(), **service.safety_flags()}


@router.get("/duplicate-candidates")
async def list_airline_master_profile_duplicate_candidates(
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    service = AirlineMasterProfileIntelligenceService(db)
    items = await service.duplicate_candidates()
    return {"phase": PHASE_LABEL, "items": items, "count": len(items), **service.safety_flags()}


@router.get("/{airline_id}")
async def get_airline_master_profile(
    airline_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    try:
        return {"phase": PHASE_LABEL, "item": await AirlineMasterProfileIntelligenceService(db).get_profile(airline_id)}
    except AirlineMasterProfileError as exc:
        raise bad_request(exc) from exc


@router.put("/{airline_id}")
async def update_airline_master_profile(
    airline_id: str,
    payload: AirlineMasterProfileUpdate,
    reason: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(user)
    try:
        return {"phase": PHASE_LABEL, "item": await AirlineMasterProfileIntelligenceService(db).update_profile(airline_id, payload, user, reason)}
    except AirlineMasterProfileError as exc:
        raise bad_request(exc) from exc


async def create_related(
    airline_id: str,
    payload: dict,
    kind: str,
    user: dict,
    db: Database,
) -> dict:
    await require_write(user)
    service = AirlineMasterProfileIntelligenceService(db)
    methods = {
        "alias": service.create_alias,
        "relationship": service.create_relationship,
        "hub": service.create_hub,
        "classification": service.create_classification,
        "distribution": service.create_distribution,
        "service-desk": service.create_service_desk,
        "evidence": service.create_evidence_link,
    }
    try:
        return {"phase": PHASE_LABEL, "item": await methods[kind](airline_id, payload, user), **service.safety_flags()}
    except AirlineMasterProfileError as exc:
        raise bad_request(exc) from exc


@router.post("/{airline_id}/aliases", status_code=status.HTTP_201_CREATED)
async def create_airline_alias(airline_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await create_related(airline_id, payload, "alias", user, db)


@router.post("/{airline_id}/relationships", status_code=status.HTTP_201_CREATED)
async def create_airline_relationship(airline_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await create_related(airline_id, payload, "relationship", user, db)


@router.post("/{airline_id}/hubs", status_code=status.HTTP_201_CREATED)
async def create_airline_hub(airline_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await create_related(airline_id, payload, "hub", user, db)


@router.post("/{airline_id}/classifications", status_code=status.HTTP_201_CREATED)
async def create_airline_classification(airline_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await create_related(airline_id, payload, "classification", user, db)


@router.post("/{airline_id}/distribution", status_code=status.HTTP_201_CREATED)
async def create_airline_distribution(airline_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await create_related(airline_id, payload, "distribution", user, db)


@router.post("/{airline_id}/service-desks", status_code=status.HTTP_201_CREATED)
async def create_airline_service_desk(airline_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await create_related(airline_id, payload, "service-desk", user, db)


@router.post("/{airline_id}/evidence", status_code=status.HTTP_201_CREATED)
async def create_airline_profile_evidence(airline_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await create_related(airline_id, payload, "evidence", user, db)


@router.get("/{airline_id}/revisions")
async def list_airline_profile_revisions(
    airline_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(user)
    try:
        item = await AirlineMasterProfileIntelligenceService(db).get_profile(airline_id)
    except AirlineMasterProfileError as exc:
        raise bad_request(exc) from exc
    return {"phase": PHASE_LABEL, "items": item["revision_history"], "count": len(item["revision_history"])}
