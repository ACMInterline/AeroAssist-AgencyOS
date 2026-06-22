import base64
import binascii
from datetime import datetime, timezone
from email.message import EmailMessage
import re
import smtplib
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from auth import get_current_user
from database import Database, get_database
from models import (
    AuditEvent,
    AgencyEmailSettings,
    AgencyEmailSettingsUpdate,
    BookingTimelineEvent,
    DocumentDelivery,
    DocumentDeliveryCreate,
    DocumentDeliveryProvider,
    DocumentDeliveryStatus,
    DocumentExport,
    DocumentExportCreate,
    DocumentExportStatus,
    DocumentExportStorageMode,
    DocumentExportType,
    DocumentTemplate,
    DocumentTemplateCreate,
    DocumentTemplateUpdate,
    DocumentTimelineEvent,
    OfferTimelineEvent,
    RenderDocumentRequest,
    RenderedDocument,
)
from routers.portal import portal_context
from services.document_rendering_service import render_document_payload
from services.tenant_service import assert_agency_access, assert_portal_projection_safe, require_any_agency_role

router = APIRouter(prefix="/api/agencies/{agency_id}", tags=["documents"])
portal_router = APIRouter(prefix="/api/portal", tags=["portal_document_exports"])

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
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin"}:
        await require_any_agency_role(db, agency_id, user, WRITE_ROLES)


async def require_template_write(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin"}:
        await require_any_agency_role(db, agency_id, user, TEMPLATE_WRITE_ROLES)


async def write_audit(db: Database, agency_id: str, actor_user_id: str, event_type: str, entity_type: str, entity_id: str, summary: str, metadata: dict | None = None) -> None:
    await db.collection("audit_events").insert_one(AuditEvent(agency_id=agency_id, actor_user_id=actor_user_id, event_type=event_type, entity_type=entity_type, entity_id=entity_id, summary=summary, metadata=metadata or {}).model_dump(mode="json"))


async def write_document_timeline(db: Database, agency_id: str, document_id: str, actor_user_id: str | None, event_type: str, title: str, summary: str | None = None, metadata: dict | None = None) -> None:
    event = DocumentTimelineEvent(agency_id=agency_id, rendered_document_id=document_id, actor_user_id=actor_user_id, event_type=event_type, title=title, summary=summary, metadata=metadata or {})
    await db.collection("document_timeline_events").insert_one(event.model_dump(mode="json"))


def safe_filename(value: str, suffix: str) -> str:
    base = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._").lower() or "document"
    if not base.endswith(suffix):
        base = f"{base}{suffix}"
    return base


def public_export(export: dict) -> dict:
    return {
        "id": export["id"],
        "rendered_document_id": export.get("rendered_document_id"),
        "export_type": export.get("export_type"),
        "status": export.get("status"),
        "filename": export.get("filename"),
        "content_type": export.get("content_type"),
        "file_size_bytes": export.get("file_size_bytes"),
        "generated_at": export.get("generated_at"),
        "client_visible": export.get("client_visible"),
        "error_message": export.get("error_message"),
        "created_at": export.get("created_at"),
        "updated_at": export.get("updated_at"),
    }


async def get_document_or_404(db: Database, agency_id: str, document_id: str) -> dict:
    document = await db.collection("rendered_documents").find_one({"agency_id": agency_id, "id": document_id})
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rendered document not found.")
    return document


async def get_export_or_404(db: Database, agency_id: str, export_id: str) -> dict:
    export = await db.collection("document_exports").find_one({"agency_id": agency_id, "id": export_id})
    if not export:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document export not found.")
    return export


async def get_delivery_or_404(db: Database, agency_id: str, delivery_id: str) -> dict:
    delivery = await db.collection("document_deliveries").find_one({"agency_id": agency_id, "id": delivery_id})
    if not delivery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document delivery not found.")
    return delivery


async def get_email_settings_or_default(db: Database, agency_id: str) -> dict:
    settings = await db.collection("agency_email_settings").find_one({"agency_id": agency_id, "status": "active"})
    if settings:
        return settings
    agency = await db.collection("agencies").find_one({"id": agency_id}) or {}
    return AgencyEmailSettings(
        agency_id=agency_id,
        sender_name=agency.get("name") or "Agency",
        sender_email="no-reply@example.invalid",
        mode="disabled",
        status="active",
    ).model_dump(mode="json")


def export_download_response(export: dict) -> Response:
    if export.get("status") != "generated" or export.get("storage_mode") != "inline_base64" or not export.get("file_data_base64"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Export file is not available.")
    try:
        data = base64.b64decode(export["file_data_base64"].encode("ascii"), validate=True)
    except (binascii.Error, UnicodeEncodeError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Export file data is invalid.")
    filename = safe_filename(export.get("filename") or "document", "")
    headers = {"Content-Disposition": f"attachment; filename=\"{filename}\""}
    return Response(content=data, media_type=export.get("content_type") or "application/octet-stream", headers=headers)


async def send_smtp_delivery(settings: dict, delivery: dict, export: dict | None) -> tuple[str, str | None]:
    if not settings.get("smtp_host") or not settings.get("smtp_port"):
        raise ValueError("SMTP host and port are required before sending.")
    if settings.get("smtp_username") and settings.get("smtp_password_secret_ref"):
        raise ValueError("SMTP password secret resolution is not implemented in this foundation.")

    message = EmailMessage()
    message["From"] = f"{settings.get('sender_name') or 'Agency'} <{settings.get('sender_email')}>"
    message["To"] = delivery["recipient_email"]
    if settings.get("reply_to_email"):
        message["Reply-To"] = settings["reply_to_email"]
    message["Subject"] = delivery["subject"]
    message.set_content(delivery["message_text"])

    if export and export.get("storage_mode") == "inline_base64" and export.get("file_data_base64"):
        data = base64.b64decode(export["file_data_base64"].encode("ascii"))
        content_type = (export.get("content_type") or "application/octet-stream").split(";", 1)[0]
        maintype, _, subtype = content_type.partition("/")
        message.add_attachment(data, maintype=maintype or "application", subtype=subtype or "octet-stream", filename=export.get("filename") or "document")

    if settings.get("smtp_use_tls", True):
        with smtplib.SMTP(settings["smtp_host"], int(settings["smtp_port"]), timeout=15) as smtp:
            smtp.starttls()
            if settings.get("smtp_username"):
                raise ValueError("SMTP username is configured, but no password secret resolver is available.")
            response = smtp.send_message(message)
    else:
        with smtplib.SMTP(settings["smtp_host"], int(settings["smtp_port"]), timeout=15) as smtp:
            if settings.get("smtp_username"):
                raise ValueError("SMTP username is configured, but no password secret resolver is available.")
            response = smtp.send_message(message)
    return "smtp", str(response) if response else None


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


@router.post("/documents/{document_id}/exports", status_code=status.HTTP_201_CREATED)
async def create_document_export(agency_id: str, document_id: str, payload: DocumentExportCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    document = await get_document_or_404(db, agency_id, document_id)
    if payload.export_type == DocumentExportType.PDF:
        export = DocumentExport(
            agency_id=agency_id,
            rendered_document_id=document_id,
            export_type="pdf",
            status="failed",
            filename=safe_filename(document["title"], ".pdf"),
            content_type="application/pdf",
            storage_mode="not_generated",
            generated_by_user_id=user["id"],
            generated_at=datetime.now(timezone.utc),
            error_message="PDF generation is not available because no reliable PDF renderer is installed.",
            client_visible=False,
        )
        created = await db.collection("document_exports").insert_one(export.model_dump(mode="json"))
        await write_document_timeline(db, agency_id, document_id, user["id"], "document_export.failed", "PDF export unavailable", created["error_message"], {"export_id": created["id"]})
        await write_audit(db, agency_id, user["id"], "document_export.failed", "document_export", created["id"], "PDF export requested but unavailable.", {"rendered_document_id": document_id})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PDF generation is not available in this installation. Use print_html export.")

    html = document.get("rendered_html") or ""
    data = html.encode("utf-8")
    export = DocumentExport(
        agency_id=agency_id,
        rendered_document_id=document_id,
        export_type="print_html",
        status="generated",
        filename=safe_filename(document["title"], ".html"),
        content_type="text/html; charset=utf-8",
        storage_mode="inline_base64",
        file_data_base64=base64.b64encode(data).decode("ascii"),
        file_size_bytes=len(data),
        generated_by_user_id=user["id"],
        generated_at=datetime.now(timezone.utc),
        client_visible=payload.client_visible and bool(document.get("client_visible")),
    )
    created = await db.collection("document_exports").insert_one(export.model_dump(mode="json"))
    await write_document_timeline(db, agency_id, document_id, user["id"], "document_export.generated", "Printable export generated", created["filename"], {"export_id": created["id"], "export_type": created["export_type"]})
    await write_audit(db, agency_id, user["id"], "document_export.generated", "document_export", created["id"], "Generated printable document export.", {"rendered_document_id": document_id, "export_type": created["export_type"]})
    return {"export": public_export(created)}


@router.get("/documents/{document_id}/exports")
async def list_document_exports(agency_id: str, document_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    await get_document_or_404(db, agency_id, document_id)
    exports = await db.collection("document_exports").find_many({"agency_id": agency_id, "rendered_document_id": document_id})
    exports.sort(key=lambda item: str(item.get("created_at", "")), reverse=True)
    return {"items": [public_export(item) for item in exports]}


@router.get("/document-exports/{export_id}")
async def get_document_export(agency_id: str, export_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    export = await get_export_or_404(db, agency_id, export_id)
    await get_document_or_404(db, agency_id, export["rendered_document_id"])
    return {"export": public_export(export)}


@router.get("/document-exports/{export_id}/download")
async def download_document_export(agency_id: str, export_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> Response:
    await require_read(db, agency_id, user)
    export = await get_export_or_404(db, agency_id, export_id)
    await get_document_or_404(db, agency_id, export["rendered_document_id"])
    return export_download_response(export)


@router.post("/document-exports/{export_id}/archive")
async def archive_document_export(agency_id: str, export_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    export = await get_export_or_404(db, agency_id, export_id)
    updated = await db.collection("document_exports").update_one({"agency_id": agency_id, "id": export_id}, {"status": "archived"})
    await write_document_timeline(db, agency_id, export["rendered_document_id"], user["id"], "document_export.archived", "Document export archived", updated.get("filename"), {"export_id": export_id})
    await write_audit(db, agency_id, user["id"], "document_export.archived", "document_export", export_id, "Archived document export.", {"rendered_document_id": export["rendered_document_id"]})
    return {"export": public_export(updated)}


@router.post("/documents/{document_id}/deliveries", status_code=status.HTTP_201_CREATED)
async def create_document_delivery(agency_id: str, document_id: str, payload: DocumentDeliveryCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_document_or_404(db, agency_id, document_id)
    if payload.export_id:
        export = await get_export_or_404(db, agency_id, payload.export_id)
        if export.get("rendered_document_id") != document_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Export must belong to the selected document.")
    delivery = DocumentDelivery(agency_id=agency_id, rendered_document_id=document_id, **payload.model_dump(mode="json"))
    created = await db.collection("document_deliveries").insert_one(delivery.model_dump(mode="json"))
    await write_document_timeline(db, agency_id, document_id, user["id"], "document_delivery.created", "Delivery draft created", created["recipient_email"], {"delivery_id": created["id"]})
    await write_audit(db, agency_id, user["id"], "document_delivery.created", "document_delivery", created["id"], "Created document delivery draft.", {"rendered_document_id": document_id})
    return {"delivery": created}


@router.get("/documents/{document_id}/deliveries")
async def list_document_deliveries(agency_id: str, document_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    await get_document_or_404(db, agency_id, document_id)
    items = await db.collection("document_deliveries").find_many({"agency_id": agency_id, "rendered_document_id": document_id})
    items.sort(key=lambda item: str(item.get("created_at", "")), reverse=True)
    return {"items": items}


@router.get("/document-deliveries/{delivery_id}")
async def get_document_delivery(agency_id: str, delivery_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    delivery = await get_delivery_or_404(db, agency_id, delivery_id)
    await get_document_or_404(db, agency_id, delivery["rendered_document_id"])
    return {"delivery": delivery}


@router.post("/document-deliveries/{delivery_id}/send")
async def send_document_delivery(agency_id: str, delivery_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    delivery = await get_delivery_or_404(db, agency_id, delivery_id)
    if delivery.get("status") in {"sent", "cancelled", "archived"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Delivery cannot be sent from its current status.")
    if delivery.get("delivery_type") != "email":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only email deliveries can be sent.")

    document = await get_document_or_404(db, agency_id, delivery["rendered_document_id"])
    export = await get_export_or_404(db, agency_id, delivery["export_id"]) if delivery.get("export_id") else None
    if export and export.get("rendered_document_id") != document["id"]:
        updated = await db.collection("document_deliveries").update_one({"agency_id": agency_id, "id": delivery_id}, {"status": "failed", "provider": "none", "error_message": "Delivery export does not belong to the selected document."})
        await write_document_timeline(db, agency_id, document["id"], user["id"], "document_delivery.failed", "Delivery failed", updated["error_message"], {"delivery_id": delivery_id})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=updated["error_message"])
    if export and export.get("status") != "generated":
        updated = await db.collection("document_deliveries").update_one({"agency_id": agency_id, "id": delivery_id}, {"status": "failed", "provider": "none", "error_message": "Delivery export file is not available."})
        await write_document_timeline(db, agency_id, document["id"], user["id"], "document_delivery.failed", "Delivery failed", updated["error_message"], {"delivery_id": delivery_id})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=updated["error_message"])
    settings = await get_email_settings_or_default(db, agency_id)
    if settings.get("mode") == "disabled":
        updated = await db.collection("document_deliveries").update_one({"agency_id": agency_id, "id": delivery_id}, {"status": "failed", "provider": "none", "error_message": "Email sending is disabled for this agency."})
        await write_document_timeline(db, agency_id, document["id"], user["id"], "document_delivery.failed", "Delivery failed", updated["error_message"], {"delivery_id": delivery_id})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=updated["error_message"])

    now = datetime.now(timezone.utc)
    try:
        if settings.get("mode") == "dev_console":
            provider = DocumentDeliveryProvider.DEV_CONSOLE.value
            provider_message_id = f"dev-console:{delivery_id}"
        elif settings.get("mode") == "smtp":
            provider, provider_message_id = await send_smtp_delivery(settings, delivery, export)
        else:
            raise ValueError("Unsupported email mode.")
        updates = {"status": "sent", "provider": provider, "provider_message_id": provider_message_id, "sent_by_user_id": user["id"], "sent_at": now, "error_message": None}
        updated = await db.collection("document_deliveries").update_one({"agency_id": agency_id, "id": delivery_id}, updates)
        await write_document_timeline(db, agency_id, document["id"], user["id"], "document_delivery.sent", "Delivery sent", delivery["recipient_email"], {"delivery_id": delivery_id, "provider": provider})
        await write_audit(db, agency_id, user["id"], "document_delivery.sent", "document_delivery", delivery_id, "Document delivery sent.", {"rendered_document_id": document["id"], "provider": provider})
        return {"delivery": updated}
    except Exception as exc:
        updated = await db.collection("document_deliveries").update_one({"agency_id": agency_id, "id": delivery_id}, {"status": "failed", "provider": settings.get("mode") or "none", "error_message": str(exc)})
        await write_document_timeline(db, agency_id, document["id"], user["id"], "document_delivery.failed", "Delivery failed", str(exc), {"delivery_id": delivery_id})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/document-deliveries/{delivery_id}/cancel")
async def cancel_document_delivery(agency_id: str, delivery_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    delivery = await get_delivery_or_404(db, agency_id, delivery_id)
    if delivery.get("status") == "sent":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sent deliveries cannot be cancelled.")
    updated = await db.collection("document_deliveries").update_one({"agency_id": agency_id, "id": delivery_id}, {"status": "cancelled"})
    await write_document_timeline(db, agency_id, delivery["rendered_document_id"], user["id"], "document_delivery.cancelled", "Delivery cancelled", delivery["recipient_email"], {"delivery_id": delivery_id})
    await write_audit(db, agency_id, user["id"], "document_delivery.cancelled", "document_delivery", delivery_id, "Cancelled document delivery.", {"rendered_document_id": delivery["rendered_document_id"]})
    return {"delivery": updated}


@router.get("/email-settings")
async def get_email_settings(agency_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    return {"settings": await get_email_settings_or_default(db, agency_id)}


@router.put("/email-settings")
async def update_email_settings(agency_id: str, payload: AgencyEmailSettingsUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_template_write(db, agency_id, user)
    current = await db.collection("agency_email_settings").find_one({"agency_id": agency_id, "status": "active"})
    updates = clean_updates(payload)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided.")
    if current:
        updated = await db.collection("agency_email_settings").update_one({"agency_id": agency_id, "id": current["id"]}, updates)
    else:
        agency = await db.collection("agencies").find_one({"id": agency_id}) or {}
        model = AgencyEmailSettings(
            agency_id=agency_id,
            sender_name=updates.pop("sender_name", agency.get("name") or "Agency"),
            sender_email=updates.pop("sender_email", "no-reply@example.invalid"),
            **updates,
        )
        updated = await db.collection("agency_email_settings").insert_one(model.model_dump(mode="json"))
    await write_audit(db, agency_id, user["id"], "agency_email_settings.updated", "agency_email_settings", updated["id"], "Updated agency email settings.", {"mode": updated.get("mode")})
    return {"settings": updated}


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


async def get_portal_document_or_404(db: Database, ctx: dict, document_id: str) -> dict:
    document = await db.collection("rendered_documents").find_one(
        {
            "agency_id": ctx["account"]["agency_id"],
            "client_id": ctx["account"]["client_id"],
            "client_visible": True,
            "id": document_id,
        }
    )
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return document


@portal_router.get("/documents/{document_id}/exports")
async def list_portal_document_exports(document_id: str, ctx: dict = Depends(portal_context), db: Database = Depends(get_database)) -> dict:
    document = await get_portal_document_or_404(db, ctx, document_id)
    exports = await db.collection("document_exports").find_many(
        {
            "agency_id": ctx["account"]["agency_id"],
            "rendered_document_id": document["id"],
            "client_visible": True,
            "status": "generated",
        }
    )
    payload = {"items": [public_export(item) for item in exports]}
    assert_portal_projection_safe(payload)
    return payload


@portal_router.get("/document-exports/{export_id}/download")
async def download_portal_document_export(export_id: str, ctx: dict = Depends(portal_context), db: Database = Depends(get_database)) -> Response:
    export = await db.collection("document_exports").find_one(
        {
            "agency_id": ctx["account"]["agency_id"],
            "id": export_id,
            "client_visible": True,
            "status": "generated",
        }
    )
    if not export:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document export not found.")
    await get_portal_document_or_404(db, ctx, export["rendered_document_id"])
    return export_download_response(export)
