from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import BaseModel, ConfigDict, Field

from database import Database, get_database
from routers.portal import portal_context, safe_response
from services.portal_projection_service import (
    PortalProjectionError,
    PortalProjectionService,
)


router = APIRouter(prefix="/api/portal", tags=["portal-product-kernel"])


class PortalEmergencyContact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, max_length=160)
    relationship: str | None = Field(default=None, max_length=80)
    phone: str | None = Field(default=None, max_length=80)
    email: str | None = Field(default=None, max_length=254)


class PortalProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(default=None, max_length=160)
    legal_name: str | None = Field(default=None, max_length=240)
    primary_phone: str | None = Field(default=None, max_length=80)
    country: str | None = Field(default=None, max_length=120)
    city: str | None = Field(default=None, max_length=120)
    address_line_1: str | None = Field(default=None, max_length=240)
    address_line_2: str | None = Field(default=None, max_length=240)
    postal_code: str | None = Field(default=None, max_length=40)
    preferred_language: str | None = Field(default=None, max_length=20)
    default_currency: str | None = Field(default=None, max_length=3)
    marketing_consent: bool | None = None
    data_processing_consent: bool | None = None
    middle_name: str | None = Field(default=None, max_length=80)
    gender: str | None = Field(default=None, max_length=40)
    nationality: str | None = Field(default=None, max_length=120)
    residence_country: str | None = Field(default=None, max_length=120)
    primary_language: str | None = Field(default=None, max_length=20)
    passport_country: str | None = Field(default=None, max_length=120)
    passport_expiry: date | None = None
    known_assistance_needs: str | None = Field(default=None, max_length=2000)
    meal_preferences: str | None = Field(default=None, max_length=1000)
    seating_preferences: str | None = Field(default=None, max_length=1000)
    baggage_preferences: str | None = Field(default=None, max_length=1000)
    emergency_contact: PortalEmergencyContact | None = None
    loyalty_numbers: list[dict[str, str]] | None = Field(default=None, max_length=50)


class PortalRequestDraftUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=180)
    client_notes: str | None = Field(default=None, max_length=4000)


class PortalRequestCancel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=3, max_length=1000)


class PortalDocumentUpload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_name: str = Field(min_length=1, max_length=240)
    content_type: str = Field(min_length=1, max_length=120)
    content_base64: str = Field(min_length=1, max_length=8_000_000)


def _service(db: Database) -> PortalProjectionService:
    return PortalProjectionService(db)


def _raise(exc: PortalProjectionError) -> None:
    from fastapi import HTTPException

    raise HTTPException(
        status_code=exc.status_code,
        detail={"code": exc.code, "message": str(exc)},
    ) from exc


async def _safe(call: Any) -> dict:
    try:
        return safe_response(await call)
    except PortalProjectionError as exc:
        _raise(exc)


@router.get("/workspace/dashboard")
async def workspace_dashboard(
    ctx: dict = Depends(portal_context),
    db: Database = Depends(get_database),
) -> dict:
    return await _safe(_service(db).dashboard(ctx))


@router.get("/trips")
async def trips(
    ctx: dict = Depends(portal_context),
    db: Database = Depends(get_database),
) -> dict:
    return await _safe(_list_payload(_service(db).list_trips(ctx)))


@router.get("/trips/{trip_id}")
async def trip_detail(
    trip_id: str,
    ctx: dict = Depends(portal_context),
    db: Database = Depends(get_database),
) -> dict:
    return await _safe(_service(db).trip_detail(ctx, trip_id))


@router.get("/booking-records")
async def booking_records(
    ctx: dict = Depends(portal_context),
    db: Database = Depends(get_database),
) -> dict:
    return await _safe(_list_payload(_service(db).list_bookings(ctx)))


@router.get("/booking-records/{booking_id}")
async def booking_record_detail(
    booking_id: str,
    ctx: dict = Depends(portal_context),
    db: Database = Depends(get_database),
) -> dict:
    return await _safe(_service(db).booking_detail(ctx, booking_id))


@router.get("/tickets")
async def tickets(
    ctx: dict = Depends(portal_context),
    db: Database = Depends(get_database),
) -> dict:
    return await _safe(_list_payload(_service(db).list_tickets(ctx)))


@router.get("/tickets/{ticket_id}")
async def ticket_detail(
    ticket_id: str,
    ctx: dict = Depends(portal_context),
    db: Database = Depends(get_database),
) -> dict:
    return await _safe(_service(db).ticket_detail(ctx, ticket_id))


@router.get("/emds")
async def emds(
    ctx: dict = Depends(portal_context),
    db: Database = Depends(get_database),
) -> dict:
    return await _safe(_list_payload(_service(db).list_emds(ctx)))


@router.get("/emds/{emd_id}")
async def emd_detail(
    emd_id: str,
    ctx: dict = Depends(portal_context),
    db: Database = Depends(get_database),
) -> dict:
    return await _safe(_service(db).emd_detail(ctx, emd_id))


@router.get("/document-center")
async def document_center(
    ctx: dict = Depends(portal_context),
    db: Database = Depends(get_database),
) -> dict:
    return await _safe(_list_payload(_service(db).list_documents(ctx)))


@router.get("/document-center/{document_id}")
async def document_center_detail(
    document_id: str,
    ctx: dict = Depends(portal_context),
    db: Database = Depends(get_database),
) -> dict:
    return await _safe(_service(db).document_detail(ctx, document_id))


@router.post(
    "/document-center/{document_id}/upload",
    status_code=status.HTTP_201_CREATED,
)
async def document_upload(
    document_id: str,
    payload: PortalDocumentUpload,
    ctx: dict = Depends(portal_context),
    db: Database = Depends(get_database),
) -> dict:
    return await _safe(
        _service(db).upload_document(ctx, document_id, payload.model_dump(mode="json"))
    )


@router.get("/document-center/{document_id}/download")
async def document_download(
    document_id: str,
    version_id: str | None = Query(default=None),
    ctx: dict = Depends(portal_context),
    db: Database = Depends(get_database),
) -> Response:
    try:
        result = await _service(db).document_download(ctx, document_id, version_id)
    except PortalProjectionError as exc:
        _raise(exc)
    filename = str(result["file_name"]).replace('"', "").replace("\r", "").replace("\n", "")
    return Response(
        content=result["content"],
        media_type=result["content_type"],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/timeline")
async def timeline(
    entity_type: str | None = Query(default=None),
    entity_id: str | None = Query(default=None),
    ctx: dict = Depends(portal_context),
    db: Database = Depends(get_database),
) -> dict:
    return await _safe(
        _list_payload(
            _service(db).timeline(
                ctx,
                entity_type=entity_type,
                entity_id=entity_id,
            )
        )
    )


@router.get("/notifications")
async def notifications(
    ctx: dict = Depends(portal_context),
    db: Database = Depends(get_database),
) -> dict:
    return await _safe(_list_payload(_service(db).notifications(ctx)))


@router.get("/finance")
async def finance(
    ctx: dict = Depends(portal_context),
    db: Database = Depends(get_database),
) -> dict:
    return await _safe(_service(db).finance(ctx))


@router.get("/approvals")
async def approvals(
    ctx: dict = Depends(portal_context),
    db: Database = Depends(get_database),
) -> dict:
    return await _safe(_list_payload(_service(db).approvals(ctx)))


@router.patch("/profile")
async def update_profile(
    payload: PortalProfileUpdate,
    ctx: dict = Depends(portal_context),
    db: Database = Depends(get_database),
) -> dict:
    return await _safe(
        _profile_payload(
            _service(db).update_profile(
                ctx,
                payload.model_dump(mode="json", exclude_none=True),
            )
        )
    )


@router.patch("/requests/{request_id}")
async def update_request_draft(
    request_id: str,
    payload: PortalRequestDraftUpdate,
    ctx: dict = Depends(portal_context),
    db: Database = Depends(get_database),
) -> dict:
    return await _safe(
        _request_payload(
            _service(db).update_request_draft(
                ctx,
                request_id,
                payload.model_dump(mode="json", exclude_none=True),
            )
        )
    )


@router.post("/requests/{request_id}/cancel")
async def cancel_request(
    request_id: str,
    payload: PortalRequestCancel,
    ctx: dict = Depends(portal_context),
    db: Database = Depends(get_database),
) -> dict:
    return await _safe(
        _request_payload(
            _service(db).cancel_request(ctx, request_id, payload.reason)
        )
    )


async def _list_payload(call: Any) -> dict:
    items = await call
    return {"items": items, "count": len(items)}


async def _profile_payload(call: Any) -> dict:
    return {"profile": await call, "governed_kernel_update": True}


async def _request_payload(call: Any) -> dict:
    return {"request": await call, "governed_kernel_update": True}
