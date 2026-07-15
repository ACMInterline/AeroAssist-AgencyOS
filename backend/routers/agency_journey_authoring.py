from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from services.journey_segment_authoring_service import (
    PHASE_LABEL,
    FinalizedJourneyMutationError,
    JourneyAuthoringError,
    JourneySegmentAuthoringService,
)
from services.tenant_service import assert_agency_access, require_any_agency_role


router = APIRouter(prefix="/api/agencies/{agency_id}/journey-authoring", tags=["agency-journey-authoring"])

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
    code = status.HTTP_409_CONFLICT if isinstance(exc, FinalizedJourneyMutationError) else status.HTTP_400_BAD_REQUEST
    return HTTPException(status_code=code, detail=str(exc))


async def write_call(method: str, agency_id: str, session_id: str, user: dict, db: Database, *args, **kwargs) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await getattr(JourneySegmentAuthoringService(db), method)(agency_id, session_id, *args, user=user, **kwargs)
    except (JourneyAuthoringError, ValueError) as exc:
        raise request_error(exc) from exc


@router.get("")
async def list_sessions(
    agency_id: str,
    status_filter: str | None = Query(default=None, alias="status"),
    source_type: str | None = Query(default=None),
    journey_id: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    service = JourneySegmentAuthoringService(db)
    items = await service.list_authoring_sessions(agency_id, status=status_filter, source_type=source_type, journey_id=journey_id, include_archived=include_archived)
    return {"phase": PHASE_LABEL, "items": items, "count": len(items), **service.safety_flags()}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_session(agency_id: str, payload: dict = Body(default={}), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await JourneySegmentAuthoringService(db).create_authoring_session(agency_id, payload, user)
    except (JourneyAuthoringError, ValueError) as exc:
        raise request_error(exc) from exc


@router.get("/summary")
async def summary(agency_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    service = JourneySegmentAuthoringService(db)
    return {"phase": PHASE_LABEL, "summary": await service.summarize_authoring_readiness(agency_id), **service.safety_flags()}


@router.get("/filters")
async def filters(agency_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    service = JourneySegmentAuthoringService(db)
    return {"phase": PHASE_LABEL, "filters": service.filters(), **service.safety_flags()}


@router.get("/templates")
async def list_templates(agency_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    service = JourneySegmentAuthoringService(db)
    items = await service.list_templates(agency_id)
    return {"phase": PHASE_LABEL, "items": items, "count": len(items), **service.safety_flags()}


@router.post("/templates", status_code=status.HTTP_201_CREATED)
async def create_template(agency_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await JourneySegmentAuthoringService(db).create_template(agency_id, payload, user)
    except (JourneyAuthoringError, ValueError) as exc:
        raise request_error(exc) from exc


@router.put("/templates/{template_id}")
async def update_template(agency_id: str, template_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await JourneySegmentAuthoringService(db).update_template(agency_id, template_id, payload)
    except (JourneyAuthoringError, ValueError) as exc:
        raise request_error(exc) from exc


@router.get("/{session_id}")
async def get_session(agency_id: str, session_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    try:
        return await JourneySegmentAuthoringService(db).get_authoring_session(agency_id, session_id)
    except JourneyAuthoringError as exc:
        raise request_error(exc) from exc


@router.put("/{session_id}")
async def update_session(agency_id: str, session_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await JourneySegmentAuthoringService(db).update_authoring_session(agency_id, session_id, payload, user)
    except (JourneyAuthoringError, ValueError) as exc:
        raise request_error(exc) from exc


@router.post("/{session_id}/archive")
async def archive_session(agency_id: str, session_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await write_call("archive_authoring_session", agency_id, session_id, user, db)


@router.post("/{session_id}/import-text")
async def import_text(agency_id: str, session_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await write_call("import_raw_text", agency_id, session_id, user, db, payload)


@router.post("/{session_id}/import-parser-run")
async def import_parser_run(agency_id: str, session_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    parser_run_id = str(payload.get("parser_run_id") or "")
    return await write_call("import_parser_run", agency_id, session_id, user, db, parser_run_id)


@router.post("/{session_id}/import-booking-draft")
async def import_booking_draft(agency_id: str, session_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    booking_import_draft_id = str(payload.get("booking_import_draft_id") or "")
    return await write_call("import_booking_import_draft", agency_id, session_id, user, db, booking_import_draft_id)


@router.post("/{session_id}/import-existing-journey")
async def import_existing_journey(agency_id: str, session_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    journey_id = str(payload.get("journey_id") or "")
    return await write_call("import_existing_journey", agency_id, session_id, user, db, journey_id)


@router.get("/{session_id}/sources")
async def sources(agency_id: str, session_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    service = JourneySegmentAuthoringService(db)
    try:
        items = [service._agency_safe_source(item) for item in await service.list_sources(agency_id, session_id)]
        return {"phase": PHASE_LABEL, "items": items, "count": len(items), **service.safety_flags()}
    except JourneyAuthoringError as exc:
        raise request_error(exc) from exc


@router.get("/{session_id}/segments")
async def segments(agency_id: str, session_id: str, include_archived: bool = Query(default=False), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    service = JourneySegmentAuthoringService(db)
    try:
        items = await service.list_segment_drafts(agency_id, session_id, include_archived=include_archived)
        return {"phase": PHASE_LABEL, "items": items, "count": len(items), **service.safety_flags()}
    except JourneyAuthoringError as exc:
        raise request_error(exc) from exc


@router.post("/{session_id}/segments", status_code=status.HTTP_201_CREATED)
async def create_segment(agency_id: str, session_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await write_call("create_manual_segment_draft", agency_id, session_id, user, db, payload)


@router.post("/{session_id}/segments/reorder")
async def reorder_segments(agency_id: str, session_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await write_call("reorder_segment_drafts", agency_id, session_id, user, db, list(payload.get("segment_ids") or []))


@router.post("/{session_id}/segments/bulk-update")
async def bulk_update_segments(agency_id: str, session_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await write_call("bulk_update_segment_drafts", agency_id, session_id, user, db, list(payload.get("segment_ids") or []), dict(payload.get("updates") or {}))


@router.post("/{session_id}/segments/assign")
async def assign_segments(agency_id: str, session_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await JourneySegmentAuthoringService(db).assign_segments(
            agency_id, session_id, list(payload.get("segment_ids") or []),
            option_group_key=payload.get("option_group_key"), leg_group_key=payload.get("leg_group_key"), user=user,
        )
    except (JourneyAuthoringError, ValueError) as exc:
        raise request_error(exc) from exc


@router.post("/{session_id}/segments/merge")
async def merge_segments(agency_id: str, session_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await write_call("merge_segment_drafts", agency_id, session_id, user, db, list(payload.get("segment_ids") or []), dict(payload.get("segment") or {}))


@router.put("/{session_id}/segments/{segment_id}")
async def update_segment(agency_id: str, session_id: str, segment_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await write_call("update_segment_draft", agency_id, session_id, user, db, segment_id, payload)


@router.post("/{session_id}/segments/{segment_id}/archive")
async def archive_segment(agency_id: str, session_id: str, segment_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await write_call("archive_segment_draft", agency_id, session_id, user, db, segment_id)


@router.post("/{session_id}/segments/{segment_id}/restore")
async def restore_segment(agency_id: str, session_id: str, segment_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await write_call("restore_segment_draft", agency_id, session_id, user, db, segment_id)


@router.post("/{session_id}/segments/{segment_id}/split")
async def split_segment(agency_id: str, session_id: str, segment_id: str, payload: dict = Body(...), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await write_call("split_segment_draft", agency_id, session_id, user, db, segment_id, list(payload.get("segments") or []))


@router.post("/{session_id}/normalize")
async def normalize(agency_id: str, session_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await JourneySegmentAuthoringService(db).normalize_session(agency_id, session_id)
    except (JourneyAuthoringError, ValueError) as exc:
        raise request_error(exc) from exc


@router.post("/{session_id}/enrich")
async def enrich(agency_id: str, session_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await write_call("enrich_session_from_internal_reference_data", agency_id, session_id, user, db)


@router.post("/{session_id}/recalculate")
async def recalculate(agency_id: str, session_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await JourneySegmentAuthoringService(db).recalculate_session(agency_id, session_id)
    except (JourneyAuthoringError, ValueError) as exc:
        raise request_error(exc) from exc


@router.post("/{session_id}/validate")
async def validate(agency_id: str, session_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await JourneySegmentAuthoringService(db).validate_session(agency_id, session_id)
    except (JourneyAuthoringError, ValueError) as exc:
        raise request_error(exc) from exc


@router.get("/{session_id}/validations")
async def validations(agency_id: str, session_id: str, active_only: bool = Query(default=False), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    service = JourneySegmentAuthoringService(db)
    try:
        items = await service.list_validations(agency_id, session_id, active_only=active_only)
        return {"phase": PHASE_LABEL, "items": items, "count": len(items), **service.safety_flags()}
    except JourneyAuthoringError as exc:
        raise request_error(exc) from exc


@router.post("/{session_id}/validations/{validation_id}/resolve")
async def resolve_validation(agency_id: str, session_id: str, validation_id: str, payload: dict = Body(default={}), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await JourneySegmentAuthoringService(db).resolve_validation(agency_id, session_id, validation_id, str(payload.get("resolution_note") or "Reviewed by agent"), user)
    except JourneyAuthoringError as exc:
        raise request_error(exc) from exc


@router.get("/{session_id}/provenance")
async def provenance(agency_id: str, session_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    service = JourneySegmentAuthoringService(db)
    items = await service.list_field_provenance(agency_id, session_id)
    return {"phase": PHASE_LABEL, "items": items, "count": len(items), **service.safety_flags()}


@router.get("/{session_id}/corrections")
async def corrections(agency_id: str, session_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    service = JourneySegmentAuthoringService(db)
    items = await service.list_corrections(agency_id, session_id)
    return {"phase": PHASE_LABEL, "items": items, "count": len(items), **service.safety_flags()}


@router.post("/{session_id}/preview-application")
async def preview_application(agency_id: str, session_id: str, payload: dict = Body(default={}), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    try:
        return await JourneySegmentAuthoringService(db).preview_application(agency_id, session_id, payload)
    except (JourneyAuthoringError, ValueError) as exc:
        raise request_error(exc) from exc


@router.post("/{session_id}/apply-to-journey")
async def apply_to_journey(agency_id: str, session_id: str, payload: dict = Body(default={}), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    return await write_call("apply_session_to_journey", agency_id, session_id, user, db, payload)
