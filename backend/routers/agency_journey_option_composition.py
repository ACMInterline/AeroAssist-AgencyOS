import inspect
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.authorization_service import (
    project_authorized_commercial_fields,
    require_commercial_field_permissions,
    require_permission,
)
from services.journey_option_fare_brand_composition_service import (
    PHASE_LABEL,
    FinalizedCompositionSnapshotError,
    JourneyOptionCompositionError,
    JourneyOptionFareBrandCompositionService,
)
from services.tenant_service import assert_agency_access


router = APIRouter(prefix="/api/agencies/{agency_id}/journey-option-compositions", tags=["agency-journey-option-compositions"])

async def require_read(_db: Database, _agency_id: str, user: dict) -> None:
    await assert_agency_access(_db, _agency_id, user)
    require_permission(user, "view_offers")


async def require_write(_db: Database, _agency_id: str, user: dict) -> None:
    await assert_agency_access(_db, _agency_id, user)
    require_permission(user, "edit_offers")


class PermissionProjectedJourneyOptionService:
    def __init__(self, db: Database, principal: dict[str, Any]) -> None:
        self._service = JourneyOptionFareBrandCompositionService(db)
        self._principal = principal

    def __getattr__(self, name: str) -> Any:
        member = getattr(self._service, name)
        if not inspect.iscoroutinefunction(member):
            return member

        async def projected(*args: Any, **kwargs: Any) -> Any:
            result = await member(*args, **kwargs)
            return project_authorized_commercial_fields(result, self._principal)

        return projected


def permission_projected_service(
    db: Database,
    user: dict[str, Any],
) -> PermissionProjectedJourneyOptionService:
    return PermissionProjectedJourneyOptionService(db, user)


def request_error(exc: Exception) -> HTTPException:
    code = status.HTTP_409_CONFLICT if isinstance(exc, FinalizedCompositionSnapshotError) else status.HTTP_400_BAD_REQUEST
    return HTTPException(status_code=code, detail=str(exc))


@router.get("")
async def list_compositions(
    agency_id: str,
    journey_id: str | None = Query(default=None),
    composition_status: str | None = Query(default=None, alias="status"),
    offer_id: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    client_safe: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = permission_projected_service(db, user)
    items = await service.list_compositions(agency_id, journey_id=journey_id, status=composition_status, offer_id=offer_id, include_archived=include_archived)
    if client_safe:
        items = [service.sanitize_agency_output(item) for item in items]
    return {"phase": PHASE_LABEL, "items": items, "count": len(items), **service.safety_flags()}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_composition(agency_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await permission_projected_service(db, user).create_composition(agency_id, payload, user)
    except (JourneyOptionCompositionError, ValueError) as exc:
        raise request_error(exc) from exc


@router.get("/summary")
async def summary(agency_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    service = permission_projected_service(db, user)
    return {"phase": PHASE_LABEL, "summary": await service.summarize_readiness(agency_id), **service.safety_flags()}


@router.get("/filters")
async def filters(agency_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    service = permission_projected_service(db, user)
    return {"phase": PHASE_LABEL, "filters": service.filters(), **service.safety_flags()}


@router.post("/from-journey/{journey_id}", status_code=status.HTTP_201_CREATED)
async def from_journey(agency_id: str, journey_id: str, payload: dict = Body(default={}), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await permission_projected_service(db, user).create_from_journey(agency_id, journey_id, payload, user)
    except (JourneyOptionCompositionError, ValueError) as exc:
        raise request_error(exc) from exc


@router.post("/from-authoring-session/{session_id}", status_code=status.HTTP_201_CREATED)
async def from_authoring_session(agency_id: str, session_id: str, payload: dict = Body(default={}), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await permission_projected_service(db, user).create_from_authoring_session(agency_id, session_id, payload, user)
    except (JourneyOptionCompositionError, ValueError) as exc:
        raise request_error(exc) from exc


@router.post("/from-offer/{offer_id}", status_code=status.HTTP_201_CREATED)
async def from_offer(agency_id: str, offer_id: str, payload: dict = Body(default={}), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await permission_projected_service(db, user).create_from_offer(agency_id, offer_id, payload, user)
    except (JourneyOptionCompositionError, ValueError) as exc:
        raise request_error(exc) from exc


@router.get("/{composition_id}")
async def get_composition(agency_id: str, composition_id: str, client_safe: bool = Query(default=False), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    try:
        return await permission_projected_service(db, user).get_composition(agency_id, composition_id, client_safe=client_safe)
    except JourneyOptionCompositionError as exc:
        raise request_error(exc) from exc


@router.put("/{composition_id}")
async def update_composition(agency_id: str, composition_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await permission_projected_service(db, user).update_composition(agency_id, composition_id, payload, user)
    except (JourneyOptionCompositionError, ValueError) as exc:
        raise request_error(exc) from exc


@router.post("/{composition_id}/archive")
async def archive_composition(agency_id: str, composition_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await permission_projected_service(db, user).archive_composition(agency_id, composition_id, user)
    except JourneyOptionCompositionError as exc:
        raise request_error(exc) from exc


@router.post("/{composition_id}/options", status_code=status.HTTP_201_CREATED)
async def create_option(agency_id: str, composition_id: str, payload: dict = Body(default={}), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await permission_projected_service(db, user).create_option(agency_id, composition_id, payload, user)
    except (JourneyOptionCompositionError, ValueError) as exc:
        raise request_error(exc) from exc


@router.put("/{composition_id}/options/{option_id}")
async def update_option(agency_id: str, composition_id: str, option_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await permission_projected_service(db, user).update_option(agency_id, composition_id, option_id, payload, user)
    except (JourneyOptionCompositionError, ValueError) as exc:
        raise request_error(exc) from exc


@router.post("/{composition_id}/options/{option_id}/clone", status_code=status.HTTP_201_CREATED)
async def clone_option(agency_id: str, composition_id: str, option_id: str, payload: dict = Body(default={}), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await permission_projected_service(db, user).clone_option(agency_id, composition_id, option_id, payload, user)
    except (JourneyOptionCompositionError, ValueError) as exc:
        raise request_error(exc) from exc


@router.post("/{composition_id}/options/reorder")
async def reorder_options(agency_id: str, composition_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await permission_projected_service(db, user).reorder_options(agency_id, composition_id, list(payload.get("option_ids") or []), user)
    except (JourneyOptionCompositionError, ValueError) as exc:
        raise request_error(exc) from exc


@router.post("/{composition_id}/options/{option_id}/archive")
async def archive_option(agency_id: str, composition_id: str, option_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await permission_projected_service(db, user).archive_option(agency_id, composition_id, option_id, user)
    except JourneyOptionCompositionError as exc:
        raise request_error(exc) from exc


@router.post("/{composition_id}/options/{option_id}/restore")
async def restore_option(agency_id: str, composition_id: str, option_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await permission_projected_service(db, user).restore_option(agency_id, composition_id, option_id, user)
    except JourneyOptionCompositionError as exc:
        raise request_error(exc) from exc


@router.post("/{composition_id}/options/{option_id}/segments", status_code=status.HTTP_201_CREATED)
async def assign_segments(agency_id: str, composition_id: str, option_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await permission_projected_service(db, user).assign_segments(agency_id, composition_id, option_id, payload, user)
    except (JourneyOptionCompositionError, ValueError) as exc:
        raise request_error(exc) from exc


@router.put("/{composition_id}/options/{option_id}/segments")
async def replace_segments(agency_id: str, composition_id: str, option_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await permission_projected_service(db, user).replace_segment_assignments(agency_id, composition_id, option_id, payload, user)
    except (JourneyOptionCompositionError, ValueError) as exc:
        raise request_error(exc) from exc


@router.post("/{composition_id}/options/{option_id}/segments/{assignment_id}/archive")
async def archive_segment_assignment(agency_id: str, composition_id: str, option_id: str, assignment_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await permission_projected_service(db, user).remove_segment_assignment(agency_id, composition_id, option_id, assignment_id, user)
    except JourneyOptionCompositionError as exc:
        raise request_error(exc) from exc


@router.post("/{composition_id}/options/{option_id}/recalculate")
async def recalculate_option(agency_id: str, composition_id: str, option_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await permission_projected_service(db, user).calculate_option_metrics(agency_id, composition_id, option_id)
    except JourneyOptionCompositionError as exc:
        raise request_error(exc) from exc


@router.post("/{composition_id}/options/{option_id}/fare-brands", status_code=status.HTTP_201_CREATED)
async def create_fare_brand(agency_id: str, composition_id: str, option_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await permission_projected_service(db, user).create_manual_fare_brand(agency_id, composition_id, option_id, payload, user)
    except (JourneyOptionCompositionError, ValueError) as exc:
        raise request_error(exc) from exc


@router.post("/{composition_id}/options/{option_id}/fare-brands/import", status_code=status.HTTP_201_CREATED)
async def import_fare_brand(agency_id: str, composition_id: str, option_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await permission_projected_service(db, user).import_fare_brand(agency_id, composition_id, option_id, payload, user)
    except (JourneyOptionCompositionError, ValueError) as exc:
        raise request_error(exc) from exc


@router.put("/{composition_id}/options/{option_id}/fare-brands/{fare_choice_id}")
async def update_fare_brand(agency_id: str, composition_id: str, option_id: str, fare_choice_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await permission_projected_service(db, user).update_fare_brand(agency_id, composition_id, option_id, fare_choice_id, payload, user)
    except (JourneyOptionCompositionError, ValueError) as exc:
        raise request_error(exc) from exc


@router.post("/{composition_id}/options/{option_id}/fare-brands/{fare_choice_id}/clone", status_code=status.HTTP_201_CREATED)
async def duplicate_fare_brand(agency_id: str, composition_id: str, option_id: str, fare_choice_id: str, payload: dict = Body(default={}), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await permission_projected_service(db, user).duplicate_fare_brand(agency_id, composition_id, option_id, fare_choice_id, payload, user)
    except (JourneyOptionCompositionError, ValueError) as exc:
        raise request_error(exc) from exc


@router.post("/{composition_id}/options/{option_id}/fare-brands/reorder")
async def reorder_fare_brands(agency_id: str, composition_id: str, option_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await permission_projected_service(db, user).reorder_fare_brands(agency_id, composition_id, option_id, list(payload.get("fare_choice_ids") or []), user)
    except (JourneyOptionCompositionError, ValueError) as exc:
        raise request_error(exc) from exc


@router.post("/{composition_id}/options/{option_id}/fare-brands/{fare_choice_id}/archive")
async def archive_fare_brand(agency_id: str, composition_id: str, option_id: str, fare_choice_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await permission_projected_service(db, user).archive_fare_brand(agency_id, composition_id, option_id, fare_choice_id, user)
    except JourneyOptionCompositionError as exc:
        raise request_error(exc) from exc


@router.post("/{composition_id}/options/{option_id}/fare-brands/{fare_choice_id}/restore")
async def restore_fare_brand(agency_id: str, composition_id: str, option_id: str, fare_choice_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await permission_projected_service(db, user).restore_fare_brand(agency_id, composition_id, option_id, fare_choice_id, user)
    except JourneyOptionCompositionError as exc:
        raise request_error(exc) from exc


@router.put("/{composition_id}/options/{option_id}/fare-brands/{fare_choice_id}/pricing")
async def set_price(agency_id: str, composition_id: str, option_id: str, fare_choice_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    require_commercial_field_permissions(payload, user)
    try:
        return await permission_projected_service(db, user).set_price_breakdown(agency_id, composition_id, option_id, fare_choice_id, payload, user)
    except (JourneyOptionCompositionError, ValueError) as exc:
        raise request_error(exc) from exc


@router.post("/{composition_id}/assess-services")
async def assess_services(agency_id: str, composition_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await permission_projected_service(db, user).project_service_assessments(agency_id, composition_id, user)
    except JourneyOptionCompositionError as exc:
        raise request_error(exc) from exc


@router.post("/{composition_id}/compare")
async def compare(agency_id: str, composition_id: str, payload: dict = Body(default={}), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await permission_projected_service(db, user).generate_comparison(agency_id, composition_id, payload)
    except JourneyOptionCompositionError as exc:
        raise request_error(exc) from exc


@router.post("/{composition_id}/preferred-option")
async def preferred_option(agency_id: str, composition_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await permission_projected_service(db, user).select_preferred_option(agency_id, composition_id, payload, user)
    except JourneyOptionCompositionError as exc:
        raise request_error(exc) from exc


@router.get("/{composition_id}/snapshots")
async def list_snapshots(agency_id: str, composition_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    try:
        service = permission_projected_service(db, user)
        items = await service.list_snapshots(agency_id, composition_id)
        return {"phase": PHASE_LABEL, "items": items, "count": len(items), **service.safety_flags()}
    except JourneyOptionCompositionError as exc:
        raise request_error(exc) from exc


@router.post("/{composition_id}/snapshots", status_code=status.HTTP_201_CREATED)
async def create_snapshot(agency_id: str, composition_id: str, payload: dict = Body(default={}), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await permission_projected_service(db, user).create_snapshot(agency_id, composition_id, payload, user)
    except JourneyOptionCompositionError as exc:
        raise request_error(exc) from exc


@router.post("/{composition_id}/snapshots/{snapshot_id}/finalize")
async def finalize_snapshot(agency_id: str, composition_id: str, snapshot_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await permission_projected_service(db, user).finalize_snapshot(agency_id, composition_id, snapshot_id, user)
    except (JourneyOptionCompositionError, FinalizedCompositionSnapshotError) as exc:
        raise request_error(exc) from exc


@router.post("/{composition_id}/offer-handoff/preview")
async def handoff_preview(agency_id: str, composition_id: str, payload: dict = Body(default={}), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    try:
        return await permission_projected_service(db, user).preview_offer_handoff(agency_id, composition_id, payload)
    except JourneyOptionCompositionError as exc:
        raise request_error(exc) from exc


@router.post("/{composition_id}/offer-handoff/apply")
async def handoff_apply(agency_id: str, composition_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await permission_projected_service(db, user).apply_offer_handoff(agency_id, composition_id, payload, user)
    except JourneyOptionCompositionError as exc:
        raise request_error(exc) from exc
