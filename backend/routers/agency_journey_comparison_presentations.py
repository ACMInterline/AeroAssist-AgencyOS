from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.journey_comparison_client_presentation_service import (
    FinalizedJourneyPresentationSnapshotError,
    JourneyComparisonClientPresentationService,
    JourneyComparisonPresentationError,
    PHASE_LABEL,
)
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(
    prefix="/api/agencies/{agency_id}/journey-comparison-presentations",
    tags=["agency-journey-comparison-presentations"],
)

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


def request_error(exc: Exception) -> HTTPException:
    code = status.HTTP_409_CONFLICT if isinstance(exc, FinalizedJourneyPresentationSnapshotError) else status.HTTP_400_BAD_REQUEST
    return HTTPException(status_code=code, detail=str(exc))


@router.get("")
async def list_presentations(
    agency_id: str,
    presentation_status: str | None = Query(default=None, alias="status"),
    audience_type: str | None = Query(default=None),
    composition_id: str | None = Query(default=None),
    journey_id: str | None = Query(default=None),
    offer_id: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = JourneyComparisonClientPresentationService(db)
    items = await service.list_presentations(
        agency_id,
        status=presentation_status,
        audience_type=audience_type,
        composition_id=composition_id,
        journey_id=journey_id,
        offer_id=offer_id,
        include_archived=include_archived,
    )
    return {"phase": PHASE_LABEL, "items": items, "count": len(items), **service.safety_flags()}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_presentation(agency_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await JourneyComparisonClientPresentationService(db).create_presentation(agency_id, payload, user)
    except (JourneyComparisonPresentationError, ValueError) as exc:
        raise request_error(exc) from exc


@router.get("/summary")
async def summary(agency_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    service = JourneyComparisonClientPresentationService(db)
    return {"phase": PHASE_LABEL, "summary": await service.summarize_readiness(agency_id), **service.safety_flags()}


@router.get("/filters")
async def filters(agency_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    service = JourneyComparisonClientPresentationService(db)
    return {"phase": PHASE_LABEL, "filters": service.filters(), **service.safety_flags()}


@router.post("/from-composition/{composition_id}", status_code=status.HTTP_201_CREATED)
async def from_composition(agency_id: str, composition_id: str, payload: dict = Body(default={}), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await JourneyComparisonClientPresentationService(db).create_from_composition(agency_id, composition_id, payload, user)
    except (JourneyComparisonPresentationError, ValueError) as exc:
        raise request_error(exc) from exc


@router.post("/from-offer/{offer_id}", status_code=status.HTTP_201_CREATED)
async def from_offer(agency_id: str, offer_id: str, payload: dict = Body(default={}), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await JourneyComparisonClientPresentationService(db).create_from_offer(agency_id, offer_id, payload, user)
    except (JourneyComparisonPresentationError, ValueError) as exc:
        raise request_error(exc) from exc


@router.post("/from-journey/{journey_id}", status_code=status.HTTP_201_CREATED)
async def from_journey(agency_id: str, journey_id: str, payload: dict = Body(default={}), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await JourneyComparisonClientPresentationService(db).create_from_journey(agency_id, journey_id, payload, user)
    except (JourneyComparisonPresentationError, ValueError) as exc:
        raise request_error(exc) from exc


@router.get("/{presentation_id}")
async def get_presentation(agency_id: str, presentation_id: str, client_safe: bool = Query(default=False), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    try:
        return await JourneyComparisonClientPresentationService(db).get_presentation(agency_id, presentation_id, client_safe=client_safe)
    except JourneyComparisonPresentationError as exc:
        raise request_error(exc) from exc


@router.put("/{presentation_id}")
async def update_presentation(agency_id: str, presentation_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await JourneyComparisonClientPresentationService(db).update_presentation(agency_id, presentation_id, payload, user)
    except (JourneyComparisonPresentationError, ValueError) as exc:
        raise request_error(exc) from exc


@router.post("/{presentation_id}/archive")
async def archive_presentation(agency_id: str, presentation_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await JourneyComparisonClientPresentationService(db).archive_presentation(agency_id, presentation_id, user)
    except JourneyComparisonPresentationError as exc:
        raise request_error(exc) from exc


@router.post("/{presentation_id}/generate")
async def generate(agency_id: str, presentation_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await JourneyComparisonClientPresentationService(db).generate(agency_id, presentation_id, user)
    except JourneyComparisonPresentationError as exc:
        raise request_error(exc) from exc


@router.post("/{presentation_id}/recalculate")
async def recalculate(agency_id: str, presentation_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await JourneyComparisonClientPresentationService(db).recalculate(agency_id, presentation_id, user)
    except JourneyComparisonPresentationError as exc:
        raise request_error(exc) from exc


@router.post("/{presentation_id}/compare")
async def compare(agency_id: str, presentation_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await JourneyComparisonClientPresentationService(db).compare(agency_id, presentation_id)
    except JourneyComparisonPresentationError as exc:
        raise request_error(exc) from exc


async def projection_list(db: Database, agency_id: str, presentation_id: str, collection: str, user: dict) -> dict:
    await require_read(db, agency_id, user)
    await JourneyComparisonClientPresentationService(db)._require_presentation(agency_id, presentation_id)
    filters = {"agency_id": agency_id, "presentation_id": presentation_id}
    archive_field = "is_archived" if collection == "journey_comparison_option_projections" else "archived_at"
    filters[archive_field] = {"$ne": True} if archive_field == "is_archived" else None
    items = await db.collection(collection).find_many(filters)
    return {"phase": PHASE_LABEL, "items": items, "count": len(items), **JourneyComparisonClientPresentationService(db).safety_flags()}


@router.get("/{presentation_id}/options")
async def options(agency_id: str, presentation_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await projection_list(db, agency_id, presentation_id, "journey_comparison_option_projections", user)


@router.get("/{presentation_id}/segments")
async def segments(agency_id: str, presentation_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await projection_list(db, agency_id, presentation_id, "journey_comparison_segment_projections", user)


@router.get("/{presentation_id}/connections")
async def connections(agency_id: str, presentation_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await projection_list(db, agency_id, presentation_id, "journey_comparison_connection_projections", user)


@router.get("/{presentation_id}/fare-brands")
async def fare_brands(agency_id: str, presentation_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await projection_list(db, agency_id, presentation_id, "journey_comparison_fare_brand_projections", user)


@router.get("/{presentation_id}/service-suitability")
async def service_suitability(agency_id: str, presentation_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await projection_list(db, agency_id, presentation_id, "journey_comparison_service_suitability_projections", user)


@router.get("/{presentation_id}/comparison")
async def comparison(agency_id: str, presentation_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    await JourneyComparisonClientPresentationService(db)._require_presentation(agency_id, presentation_id)
    items = await db.collection("journey_comparison_results").find_many({"agency_id": agency_id, "presentation_id": presentation_id})
    return {"phase": PHASE_LABEL, "items": items, "count": len(items), **JourneyComparisonClientPresentationService(db).safety_flags()}


@router.put("/{presentation_id}/configuration")
async def configuration(agency_id: str, presentation_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await JourneyComparisonClientPresentationService(db).update_configuration(agency_id, presentation_id, payload, user)
    except (JourneyComparisonPresentationError, ValueError) as exc:
        raise request_error(exc) from exc


@router.put("/{presentation_id}/preferred-option")
async def preferred_option(agency_id: str, presentation_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await JourneyComparisonClientPresentationService(db).select_preferred_option(agency_id, presentation_id, payload, user)
    except JourneyComparisonPresentationError as exc:
        raise request_error(exc) from exc


@router.post("/{presentation_id}/content-blocks", status_code=status.HTTP_201_CREATED)
async def create_content_block(agency_id: str, presentation_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await JourneyComparisonClientPresentationService(db).create_content_block(agency_id, presentation_id, payload, user)
    except (JourneyComparisonPresentationError, ValueError) as exc:
        raise request_error(exc) from exc


@router.put("/{presentation_id}/content-blocks/{block_id}")
async def update_content_block(agency_id: str, presentation_id: str, block_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await JourneyComparisonClientPresentationService(db).update_content_block(agency_id, presentation_id, block_id, payload, user)
    except (JourneyComparisonPresentationError, ValueError) as exc:
        raise request_error(exc) from exc


@router.post("/{presentation_id}/content-blocks/{block_id}/archive")
async def archive_content_block(agency_id: str, presentation_id: str, block_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await JourneyComparisonClientPresentationService(db).archive_content_block(agency_id, presentation_id, block_id, user)
    except JourneyComparisonPresentationError as exc:
        raise request_error(exc) from exc


@router.get("/{presentation_id}/preview/client")
async def client_preview(agency_id: str, presentation_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    try:
        return await JourneyComparisonClientPresentationService(db).preview_client(agency_id, presentation_id)
    except JourneyComparisonPresentationError as exc:
        raise request_error(exc) from exc


@router.get("/{presentation_id}/preview/internal")
async def internal_preview(agency_id: str, presentation_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    try:
        return await JourneyComparisonClientPresentationService(db).preview_internal(agency_id, presentation_id)
    except JourneyComparisonPresentationError as exc:
        raise request_error(exc) from exc


@router.get("/{presentation_id}/snapshots")
async def snapshots(agency_id: str, presentation_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    service = JourneyComparisonClientPresentationService(db)
    await service._require_presentation(agency_id, presentation_id)
    items = await service.list_snapshots(agency_id, presentation_id)
    return {"phase": PHASE_LABEL, "items": items, "count": len(items), **service.safety_flags()}


@router.post("/{presentation_id}/snapshots", status_code=status.HTTP_201_CREATED)
async def create_snapshot(agency_id: str, presentation_id: str, payload: dict = Body(default={}), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await JourneyComparisonClientPresentationService(db).create_snapshot(agency_id, presentation_id, payload, user)
    except (JourneyComparisonPresentationError, ValueError) as exc:
        raise request_error(exc) from exc


@router.post("/{presentation_id}/snapshots/{snapshot_id}/finalize")
async def finalize_snapshot(agency_id: str, presentation_id: str, snapshot_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await JourneyComparisonClientPresentationService(db).finalize_snapshot(agency_id, presentation_id, snapshot_id, user)
    except JourneyComparisonPresentationError as exc:
        raise request_error(exc) from exc


@router.get("/{presentation_id}/reviews")
async def reviews(agency_id: str, presentation_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    service = JourneyComparisonClientPresentationService(db)
    await service._require_presentation(agency_id, presentation_id)
    items = await service.list_reviews(agency_id, presentation_id)
    return {"phase": PHASE_LABEL, "items": items, "count": len(items), **service.safety_flags()}


@router.post("/{presentation_id}/reviews", status_code=status.HTTP_201_CREATED)
async def create_review(agency_id: str, presentation_id: str, payload: dict = Body(default={}), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await JourneyComparisonClientPresentationService(db).create_review(agency_id, presentation_id, payload, user)
    except (JourneyComparisonPresentationError, ValueError) as exc:
        raise request_error(exc) from exc


@router.put("/{presentation_id}/reviews/{review_id}")
async def update_review(agency_id: str, presentation_id: str, review_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await JourneyComparisonClientPresentationService(db).update_review(agency_id, presentation_id, review_id, payload, user)
    except (JourneyComparisonPresentationError, ValueError) as exc:
        raise request_error(exc) from exc


@router.post("/{presentation_id}/handoff/preview")
async def handoff_preview(agency_id: str, presentation_id: str, payload: dict = Body(default={}), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await JourneyComparisonClientPresentationService(db).preview_handoff(agency_id, presentation_id, payload)
    except JourneyComparisonPresentationError as exc:
        raise request_error(exc) from exc


@router.post("/{presentation_id}/handoff/apply", status_code=status.HTTP_201_CREATED)
async def handoff_apply(agency_id: str, presentation_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await JourneyComparisonClientPresentationService(db).apply_handoff(agency_id, presentation_id, payload, user)
    except (JourneyComparisonPresentationError, ValueError) as exc:
        raise request_error(exc) from exc
