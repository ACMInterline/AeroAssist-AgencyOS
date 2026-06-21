from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    AuditEvent,
    BookingTimelineEvent,
    DocumentTemplate,
    DocumentTemplateCreate,
    DocumentTemplateUpdate,
    DocumentTimelineEvent,
    OfferTimelineEvent,
    RenderDocumentRequest,
    RenderedDocument,
)
from services.document_rendering_service import render_document_payload
from services.tenant_service import assert_agency_access, require_any_agency_role

router = APIRouter(prefix="/api/agencies/{agency_id}", tags=["documents"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant"]
TEMPLATE_WRITE_ROLES = ["agency_owner", "agency_admin"]


def clean_updates(payload: Any) -> dict:
    return payload.model_dump(exclude_unset=True, mode="json")


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


async def require_write(db: Database, agency_id: str, user: dict) -> None:
    if user.get("global_role") not in {"platform_owner", "platform_admin"}:
        await require_any_agency_role(db, agency_id, user, WRITE_ROLES)


async def require_template_write(db: Database, agency_id: str, user: dict) -> None:
    if user.get("global_role") not in {"platform_owner", "platform_admin"}:
        await require_any_agency_role(db, agency_id, user, TEMPLATE_WRITE_ROLES)


async def write_audit(db: Database, agency_id: str, actor_user_id: str, event_type: str, entity_type: str, entity_id: str, summary: str, metadata: dict | None = None) -> None:
    await db.collection("audit_events").insert_one(AuditEvent(agency_id=agency_id, actor_user_id=actor_user_id, event_type=event_type, entity_type=entity_type, entity_id=entity_id, summary=summary, metadata=metadata or {}).model_dump(mode="json"))


async def write_document_timeline(db: Database, agency_id: str, document_id: str, actor_user_id: str | None, event_type: str, title: str, summary: str | None = None, metadata: dict | None = None) -> None:
    event = DocumentTimelineEvent(agency_id=agency_id, rendered_document_id=document_id, actor_user_id=actor_user_id, event_type=event_type, title=title, summary=summary, metadata=metadata or {})
    await db.collection("document_timeline_events").insert_one(event.model_dump(mode="json"))


async def write_source_timeline(db: Database, agency_id: str, document: dict, actor_user_id: str | None) -> None:
    source_type = document.get("source_entity_type")
    source_id = document.get("source_entity_id")
    if source_type == "offer":
        event = OfferTimelineEvent(agency_id=agency_id, offer_id=source_id, actor_user_id=actor_user_id, event_type="document.rendered", title="Document rendered", summary=document["title"], metadata={"document_id": document["id"]})
        await db.collection("offer_timeline_events").insert_one(event.model_dump(mode="json"))
    elif source_type in {"booking", "ticket", "emd", "invoice"}:
        booking_id = None
        if source_type == "booking":
            booking_id = source_id
        elif source_type == "invoice":
            invoice = await db.collection("invoices").find_one({"agency_id": agency_id, "id": source_id})
            booking_id = invoice.get("booking_id") if invoice else None
        elif source_type == "ticket":
            ticket = await db.collection("ticket_records").find_one({"agency_id": agency_id, "id": source_id})
            booking_id = ticket.get("booking_id") if ticket else None
        elif source_type == "emd":
            emd = await db.collection("emd_records").find_one({"agency_id": agency_id, "id": source_id})
            booking_id = emd.get("booking_id") if emd else None
        if booking_id:
            event = BookingTimelineEvent(agency_id=agency_id, booking_id=booking_id, actor_user_id=actor_user_id, event_type="document.rendered", title="Document rendered", summary=document["title"], metadata={"document_id": document["id"], "source_entity_type": source_type, "source_entity_id": source_id})
            await db.collection("booking_timeline_events").insert_one(event.model_dump(mode="json"))


async def create_rendered_document(db: Database, agency_id: str, user: dict, source_type: str, source_id: str, payload: RenderDocumentRequest, default_type: str) -> dict:
    document_type = payload.document_type or default_type
    rendered = await render_document_payload(db, agency_id, source_type, source_id, document_type, payload.template_id, payload.language)
    model = RenderedDocument(
        agency_id=agency_id,
        rendered_by_user_id=user["id"],
        client_visible=payload.client_visible,
        internal_notes=payload.internal_notes,
        **rendered,
    )
    created = await db.collection("rendered_documents").insert_one(model.model_dump(mode="json"))
    await write_document_timeline(db, agency_id, created["id"], user["id"], "document.rendered", "Document rendered", created["title"])
    await write_source_timeline(db, agency_id, created, user["id"])
    await write_audit(db, agency_id, user["id"], "document.rendered", "rendered_document", created["id"], f"Rendered {created['document_type']} document.", {"source_entity_type": source_type, "source_entity_id": source_id})
    return {"document": created}


@router.get("/document-templates")
async def list_templates(agency_id: str, document_type: Optional[str] = None, status_filter: Optional[str] = Query(default=None, alias="status"), user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    all_templates = await db.collection("document_templates").find_many()
    items = [item for item in all_templates if item.get("agency_id") in {None, agency_id}]
    if document_type:
        items = [item for item in items if item.get("document_type") == document_type]
    if status_filter:
        items = [item for item in items if item.get("status") == status_filter]
    items.sort(key=lambda item: (item.get("document_type", ""), item.get("template_scope", ""), item.get("name", "")))
    return {"items": items}


@router.post("/document-templates", status_code=status.HTTP_201_CREATED)
async def create_template(agency_id: str, payload: DocumentTemplateCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_template_write(db, agency_id, user)
    scope = "agency_custom" if payload.template_scope != "platform_default" else "agency_custom"
    template = DocumentTemplate(agency_id=agency_id, template_scope=scope, created_by_user_id=user["id"], **payload.model_dump(exclude={"template_scope"}, mode="json"))
    created = await db.collection("document_templates").insert_one(template.model_dump(mode="json"))
    await write_audit(db, agency_id, user["id"], "document_template.created", "document_template", created["id"], f"Created document template {created['name']}.")
    return {"template": created}


@router.get("/document-templates/{template_id}")
async def get_template(agency_id: str, template_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    template = await db.collection("document_templates").find_one({"id": template_id})
    if not template or template.get("agency_id") not in {None, agency_id}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document template not found.")
    return {"template": template}


@router.put("/document-templates/{template_id}")
async def update_template(agency_id: str, template_id: str, payload: DocumentTemplateUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_template_write(db, agency_id, user)
    current = await db.collection("document_templates").find_one({"agency_id": agency_id, "id": template_id})
    if not current:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency document template not found.")
    updates = clean_updates(payload)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided.")
    updated = await db.collection("document_templates").update_one({"agency_id": agency_id, "id": template_id}, updates)
    return {"template": updated}


@router.post("/document-templates/{template_id}/archive")
async def archive_template(agency_id: str, template_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_template_write(db, agency_id, user)
    updated = await db.collection("document_templates").update_one({"agency_id": agency_id, "id": template_id}, {"status": "archived"})
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency document template not found.")
    return {"template": updated}


@router.get("/documents")
async def list_documents(agency_id: str, document_type: Optional[str] = None, source_entity_type: Optional[str] = None, status_filter: Optional[str] = Query(default=None, alias="status"), client_id: Optional[str] = None, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    filters = {"agency_id": agency_id}
    if document_type:
        filters["document_type"] = document_type
    if source_entity_type:
        filters["source_entity_type"] = source_entity_type
    if status_filter:
        filters["status"] = status_filter
    if client_id:
        filters["client_id"] = client_id
    items = await db.collection("rendered_documents").find_many(filters)
    clients = {client["id"]: client for client in await db.collection("client_profiles").find_many({"agency_id": agency_id})}
    items.sort(key=lambda item: item.get("rendered_at", ""), reverse=True)
    return {"items": [{**item, "client": clients.get(item.get("client_id"))} for item in items]}


@router.get("/documents/{document_id}")
async def get_document(agency_id: str, document_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    document = await db.collection("rendered_documents").find_one({"agency_id": agency_id, "id": document_id})
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rendered document not found.")
    return {"document": document, "timeline": await db.collection("document_timeline_events").find_many({"agency_id": agency_id, "rendered_document_id": document_id})}


@router.post("/documents/{document_id}/archive")
async def archive_document(agency_id: str, document_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    updated = await db.collection("rendered_documents").update_one({"agency_id": agency_id, "id": document_id}, {"status": "archived"})
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rendered document not found.")
    await write_document_timeline(db, agency_id, document_id, user["id"], "document.archived", "Document archived")
    return {"document": updated}


@router.get("/documents/{document_id}/timeline")
async def document_timeline(agency_id: str, document_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    if not await db.collection("rendered_documents").find_one({"agency_id": agency_id, "id": document_id}):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rendered document not found.")
    return {"items": await db.collection("document_timeline_events").find_many({"agency_id": agency_id, "rendered_document_id": document_id})}


@router.post("/offers/{offer_id}/render-document", status_code=status.HTTP_201_CREATED)
async def render_offer_document(agency_id: str, offer_id: str, payload: RenderDocumentRequest | None = None, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    return await create_rendered_document(db, agency_id, user, "offer", offer_id, payload or RenderDocumentRequest(document_type="offer_summary"), "offer_summary")


@router.post("/bookings/{booking_id}/render-document", status_code=status.HTTP_201_CREATED)
async def render_booking_document(agency_id: str, booking_id: str, payload: RenderDocumentRequest | None = None, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    request = payload or RenderDocumentRequest(document_type="booking_confirmation")
    return await create_rendered_document(db, agency_id, user, "booking", booking_id, request, "booking_confirmation")


@router.post("/tickets/{ticket_id}/render-document", status_code=status.HTTP_201_CREATED)
async def render_ticket_document(agency_id: str, ticket_id: str, payload: RenderDocumentRequest | None = None, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    return await create_rendered_document(db, agency_id, user, "ticket", ticket_id, payload or RenderDocumentRequest(document_type="ticket_receipt_summary"), "ticket_receipt_summary")


@router.post("/emds/{emd_id}/render-document", status_code=status.HTTP_201_CREATED)
async def render_emd_document(agency_id: str, emd_id: str, payload: RenderDocumentRequest | None = None, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    return await create_rendered_document(db, agency_id, user, "emd", emd_id, payload or RenderDocumentRequest(document_type="emd_receipt_summary"), "emd_receipt_summary")


@router.post("/invoices/{invoice_id}/render-document", status_code=status.HTTP_201_CREATED)
async def render_invoice_document(agency_id: str, invoice_id: str, payload: RenderDocumentRequest | None = None, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    return await create_rendered_document(db, agency_id, user, "invoice", invoice_id, payload or RenderDocumentRequest(document_type="invoice_summary"), "invoice_summary")
