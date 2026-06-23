from datetime import datetime, timedelta, timezone
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
    DocumentDeliveryAttempt,
    DocumentDeliveryCreate,
    DocumentDeliveryProvider,
    DocumentExport,
    DocumentExportCreate,
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
from services.file_storage_service import get_export_bytes, save_export_bytes
from services.pdf_rendering_service import pdf_capabilities, render_pdf_from_html
from services.secret_service import check_secret, mask_secret_ref, resolve_secret
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
        "storage_mode": export.get("storage_mode"),
        "storage_bucket": export.get("storage_bucket"),
        "retention_policy": export.get("retention_policy"),
        "retention_expires_at": export.get("retention_expires_at"),
        "checksum_sha256": export.get("checksum_sha256"),
        "file_size_bytes": export.get("file_size_bytes"),
        "generated_at": export.get("generated_at"),
        "generated_from_snapshot_at": export.get("generated_from_snapshot_at"),
        "archived_at": export.get("archived_at"),
        "archived_by_user_id": export.get("archived_by_user_id"),
        "client_visible": export.get("client_visible"),
        "error_message": export.get("error_message"),
        "created_at": export.get("created_at"),
        "updated_at": export.get("updated_at"),
    }


def public_portal_export(export: dict) -> dict:
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
        "created_at": export.get("created_at"),
        "updated_at": export.get("updated_at"),
    }


def public_email_settings(settings: dict) -> dict:
    secret_check = check_secret(settings.get("smtp_password_secret_ref")) if settings.get("smtp_password_secret_ref") else None
    return {
        "id": settings.get("id"),
        "agency_id": settings.get("agency_id"),
        "sender_name": settings.get("sender_name"),
        "sender_email": settings.get("sender_email"),
        "reply_to_email": settings.get("reply_to_email"),
        "smtp_host": settings.get("smtp_host"),
        "smtp_port": settings.get("smtp_port"),
        "smtp_username": settings.get("smtp_username"),
        "smtp_password_is_configured": bool(settings.get("smtp_password_is_configured") or settings.get("smtp_password_secret_ref")),
        "smtp_password_secret_ref_masked": mask_secret_ref(settings.get("smtp_password_secret_ref")),
        "smtp_password_secret_resolved": bool(secret_check and secret_check.ok),
        "smtp_use_tls": settings.get("smtp_use_tls", True),
        "mode": settings.get("mode"),
        "status": settings.get("status"),
        "verified_at": settings.get("verified_at"),
        "last_validation_error": settings.get("last_validation_error"),
        "created_at": settings.get("created_at"),
        "updated_at": settings.get("updated_at"),
    }


def retention_expires_at(policy: str, generated_at: datetime) -> datetime | None:
    if policy == "keep_30_days":
        return generated_at + timedelta(days=30)
    if policy == "keep_90_days":
        return generated_at + timedelta(days=90)
    if policy == "keep_1_year":
        return generated_at + timedelta(days=365)
    return None


def validate_export_metadata_for_download(export: dict) -> None:
    export_type = export.get("export_type")
    content_type = export.get("content_type") or ""
    if export_type == "print_html" and not content_type.startswith("text/html"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Export content type does not match printable HTML.")
    if export_type == "pdf" and content_type != "application/pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Export content type does not match PDF.")


def validate_email_settings(settings: dict) -> tuple[bool, str | None]:
    mode = settings.get("mode") or "disabled"
    if mode == "disabled":
        return True, None
    if not settings.get("sender_name") or not settings.get("sender_email"):
        return False, "Sender name and sender email are required."
    if mode == "dev_console":
        return True, None
    if mode == "smtp":
        if not settings.get("smtp_host") or not settings.get("smtp_port"):
            return False, "SMTP host and port are required."
        try:
            port = int(settings.get("smtp_port"))
        except (TypeError, ValueError):
            return False, "SMTP port must be a number."
        if port < 1 or port > 65535:
            return False, "SMTP port must be between 1 and 65535."
        if not settings.get("smtp_username"):
            return False, "SMTP username is required for authenticated SMTP sending."
        if not settings.get("smtp_password_secret_ref"):
            return False, "SMTP requires a password secret reference before sending."
        secret_check = check_secret(settings.get("smtp_password_secret_ref"))
        if not secret_check.ok:
            return False, secret_check.diagnostic or "SMTP password secret could not be resolved."
        return True, None
    return False, "Unsupported email mode."


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
    if export.get("status") != "generated":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Export file is not available.")
    validate_export_metadata_for_download(export)
    data = get_export_bytes(export)
    filename = safe_filename(export.get("filename") or "document", "")
    headers = {"Content-Disposition": f"attachment; filename=\"{filename}\""}
    return Response(content=data, media_type=export.get("content_type") or "application/octet-stream", headers=headers)


async def send_smtp_delivery(settings: dict, delivery: dict, export: dict | None) -> tuple[str, str | None]:
    ok, error = validate_email_settings(settings)
    if not ok:
        raise ValueError(error or "SMTP settings are incomplete.")
    password = resolve_secret(settings.get("smtp_password_secret_ref"))
    if not password:
        raise ValueError("SMTP password secret could not be resolved.")

    message = EmailMessage()
    message["From"] = f"{settings.get('sender_name') or 'Agency'} <{settings.get('sender_email')}>"
    message["To"] = delivery["recipient_email"]
    if settings.get("reply_to_email"):
        message["Reply-To"] = settings["reply_to_email"]
    message["Subject"] = delivery["subject"]
    message.set_content(delivery["message_text"])

    if export:
        data = get_export_bytes(export)
        content_type = (export.get("content_type") or "application/octet-stream").split(";", 1)[0]
        maintype, _, subtype = content_type.partition("/")
        message.add_attachment(data, maintype=maintype or "application", subtype=subtype or "octet-stream", filename=export.get("filename") or "document")

    if settings.get("smtp_use_tls", True):
        with smtplib.SMTP(settings["smtp_host"], int(settings["smtp_port"]), timeout=15) as smtp:
            smtp.starttls()
            smtp.login(settings["smtp_username"], password)
            response = smtp.send_message(message)
    else:
        with smtplib.SMTP(settings["smtp_host"], int(settings["smtp_port"]), timeout=15) as smtp:
            smtp.login(settings["smtp_username"], password)
            response = smtp.send_message(message)
    return "smtp", str(response) if response else None


def validate_delivery_attachment(export: dict | None, document: dict) -> None:
    if not export:
        return
    if export.get("rendered_document_id") != document["id"]:
        raise ValueError("Delivery export does not belong to the selected document.")
    if export.get("status") != "generated":
        raise ValueError("Delivery export file is not available.")
    validate_export_metadata_for_download(export)
    get_export_bytes(export)


def safe_attachment_diagnostic(export: dict | None, document: dict) -> dict:
    if not export:
        return {"attached": False, "valid": True, "message": "No export attachment selected."}
    try:
        validate_delivery_attachment(export, document)
        return {
            "attached": True,
            "valid": True,
            "export_id": export.get("id"),
            "export_type": export.get("export_type"),
            "content_type": export.get("content_type"),
            "file_size_bytes": export.get("file_size_bytes"),
            "message": "Attachment is valid for delivery.",
        }
    except Exception as exc:
        return {
            "attached": True,
            "valid": False,
            "export_id": export.get("id"),
            "export_type": export.get("export_type"),
            "content_type": export.get("content_type"),
            "message": str(exc),
        }


def next_delivery_action(delivery: dict, attachment_valid: bool, email_send_ready: bool) -> str:
    if delivery.get("status") == "sent":
        return "none_sent"
    if delivery.get("status") == "cancelled":
        return "none_cancelled"
    if delivery.get("status") == "archived":
        return "none_archived"
    if delivery.get("retry_status") == "max_retries_reached":
        return "none_max_attempts_reached"
    if not attachment_valid:
        return "fix_attachment"
    if not email_send_ready:
        return "fix_email_settings"
    if delivery.get("retry_status") == "retry_available":
        return "retry"
    if delivery.get("status") in {"draft", "queued"}:
        return "send"
    if delivery.get("status") == "sending":
        return "wait_for_manual_attempt"
    return "none"


def safe_delivery_error_message(exc: Exception, settings: dict | None = None) -> str:
    message = str(exc) or "Delivery failed."
    if settings and settings.get("smtp_password_secret_ref"):
        try:
            secret_value = resolve_secret(settings.get("smtp_password_secret_ref"))
        except Exception:
            secret_value = None
        if secret_value:
            message = message.replace(secret_value, "[secret]")
    return message[:500]


async def list_delivery_attempts(db: Database, agency_id: str, delivery_id: str) -> list[dict]:
    attempts = await db.collection("document_delivery_attempts").find_many({"agency_id": agency_id, "delivery_id": delivery_id})
    attempts.sort(key=lambda item: int(item.get("attempt_number", 0)), reverse=True)
    return attempts


def retry_status_for_failure(attempt_number: int, max_attempts: int) -> str:
    return "max_retries_reached" if attempt_number >= max_attempts else "retry_available"


async def create_delivery_attempt(db: Database, agency_id: str, delivery: dict, provider: str = "none") -> dict:
    attempt_number = int(delivery.get("attempt_count") or 0) + 1
    attempt = DocumentDeliveryAttempt(
        agency_id=agency_id,
        delivery_id=delivery["id"],
        rendered_document_id=delivery["rendered_document_id"],
        export_id=delivery.get("export_id"),
        attempt_number=attempt_number,
        status="sending",
        provider=provider,
        started_at=datetime.now(timezone.utc),
    )
    return await db.collection("document_delivery_attempts").insert_one(attempt.model_dump(mode="json"))


async def fail_delivery_attempt(db: Database, agency_id: str, attempt: dict, delivery: dict, provider: str, error_message: str) -> dict:
    now = datetime.now(timezone.utc)
    updated_attempt = await db.collection("document_delivery_attempts").update_one(
        {"agency_id": agency_id, "id": attempt["id"]},
        {"status": "failed", "provider": provider, "error_message": error_message, "completed_at": now},
    )
    await db.collection("document_deliveries").update_one(
        {"agency_id": agency_id, "id": delivery["id"]},
        {
            "status": "failed",
            "provider": provider,
            "error_message": error_message,
            "last_error_message": error_message,
            "attempt_count": attempt["attempt_number"],
            "last_attempt_at": now,
            "retry_status": retry_status_for_failure(attempt["attempt_number"], int(delivery.get("max_attempts") or 3)),
            "locked_at": None,
            "locked_by": None,
            "processing_state": "failed",
        },
    )
    return updated_attempt


async def mark_delivery_attempt_sent(db: Database, agency_id: str, attempt: dict, delivery: dict, provider: str, provider_message_id: str | None, user_id: str) -> dict:
    now = datetime.now(timezone.utc)
    updated_attempt = await db.collection("document_delivery_attempts").update_one(
        {"agency_id": agency_id, "id": attempt["id"]},
        {"status": "sent", "provider": provider, "provider_message_id": provider_message_id, "completed_at": now},
    )
    await db.collection("document_deliveries").update_one(
        {"agency_id": agency_id, "id": delivery["id"]},
        {
            "status": "sent",
            "provider": provider,
            "provider_message_id": provider_message_id,
            "sent_by_user_id": user_id,
            "sent_at": now,
            "error_message": None,
            "last_error_message": None,
            "attempt_count": attempt["attempt_number"],
            "last_attempt_at": now,
            "retry_status": "none",
            "next_retry_at": None,
            "locked_at": None,
            "locked_by": None,
            "processing_state": "completed",
        },
    )
    return updated_attempt


async def process_delivery_send(db: Database, agency_id: str, delivery_id: str, user: dict) -> dict:
    delivery = await get_delivery_or_404(db, agency_id, delivery_id)
    if delivery.get("status") in {"sent", "cancelled", "archived"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Delivery cannot be sent from its current status.")
    if delivery.get("delivery_type") != "email":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only email deliveries can be sent.")
    if int(delivery.get("attempt_count") or 0) >= int(delivery.get("max_attempts") or 3):
        await db.collection("document_deliveries").update_one({"agency_id": agency_id, "id": delivery_id}, {"retry_status": "max_retries_reached"})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum delivery attempts reached.")

    document = await get_document_or_404(db, agency_id, delivery["rendered_document_id"])
    export = await get_export_or_404(db, agency_id, delivery["export_id"]) if delivery.get("export_id") else None
    await db.collection("document_deliveries").update_one(
        {"agency_id": agency_id, "id": delivery_id},
        {
            "status": "sending",
            "locked_at": datetime.now(timezone.utc),
            "locked_by": user["id"],
            "processing_state": "processing",
            "last_error_message": None,
        },
    )
    attempt = await create_delivery_attempt(db, agency_id, delivery)

    def fail_detail(message: str, provider: str = "none") -> HTTPException:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    try:
        validate_delivery_attachment(export, document)

        settings = await get_email_settings_or_default(db, agency_id)
        if settings.get("mode") == "disabled":
            raise ValueError("Email sending is disabled for this agency.")

        if settings.get("mode") == "dev_console":
            provider = DocumentDeliveryProvider.DEV_CONSOLE.value
            provider_message_id = f"dev-console:{delivery_id}:{attempt['attempt_number']}"
        elif settings.get("mode") == "smtp":
            provider, provider_message_id = await send_smtp_delivery(settings, delivery, export)
        else:
            raise ValueError("Unsupported email mode.")

        await mark_delivery_attempt_sent(db, agency_id, attempt, delivery, provider, provider_message_id, user["id"])
        updated = await get_delivery_or_404(db, agency_id, delivery_id)
        await write_document_timeline(db, agency_id, document["id"], user["id"], "document_delivery.sent", "Delivery sent", delivery["recipient_email"], {"delivery_id": delivery_id, "provider": provider, "attempt_id": attempt["id"]})
        await write_audit(db, agency_id, user["id"], "document_delivery.sent", "document_delivery", delivery_id, "Document delivery sent.", {"rendered_document_id": document["id"], "provider": provider, "attempt_id": attempt["id"]})
        return {"delivery": updated, "attempt": await db.collection("document_delivery_attempts").find_one({"agency_id": agency_id, "id": attempt["id"]})}
    except Exception as exc:
        provider = (settings.get("mode") if "settings" in locals() else "none") or "none"
        error_message = safe_delivery_error_message(exc, settings if "settings" in locals() else None)
        await fail_delivery_attempt(db, agency_id, attempt, delivery, provider, error_message)
        await write_document_timeline(db, agency_id, document["id"], user["id"], "document_delivery.failed", "Delivery failed", error_message, {"delivery_id": delivery_id, "attempt_id": attempt["id"]})
        raise fail_detail(error_message, provider)


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


@router.get("/document-export-capabilities")
async def document_export_capabilities(agency_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    pdf = pdf_capabilities()
    return {
        "print_html": {"available": True, "engine": "stored_rendered_html", "diagnostic": "Printable HTML exports are generated from stored rendered document snapshots."},
        "pdf": pdf,
    }


@router.post("/documents/{document_id}/exports", status_code=status.HTTP_201_CREATED)
async def create_document_export(agency_id: str, document_id: str, payload: DocumentExportCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    document = await get_document_or_404(db, agency_id, document_id)
    if payload.export_type == DocumentExportType.PDF:
        pdf_result = render_pdf_from_html(document.get("rendered_html") or "", document.get("title") or "Document", agency_id, document_id)
        if pdf_result.ok and pdf_result.data:
            generated_at = datetime.now(timezone.utc)
            export = DocumentExport(
                agency_id=agency_id,
                rendered_document_id=document_id,
                export_type="pdf",
                status="generated",
                filename=safe_filename(document["title"], ".pdf"),
                content_type="application/pdf",
                storage_mode="file_path",
                retention_policy="keep_90_days",
                retention_expires_at=retention_expires_at("keep_90_days", generated_at),
                generated_by_user_id=user["id"],
                generated_at=generated_at,
                generated_from_snapshot_at=document.get("rendered_at"),
                client_visible=payload.client_visible and bool(document.get("client_visible")),
            )
            export_data = export.model_dump(mode="json")
            export_data.update(save_export_bytes(agency_id, export.id, export.filename, export.content_type, pdf_result.data))
            created = await db.collection("document_exports").insert_one(export_data)
            await write_document_timeline(db, agency_id, document_id, user["id"], "document_export.generated", "PDF export generated", created["filename"], {"export_id": created["id"], "export_type": created["export_type"], "renderer": pdf_result.engine_name})
            await write_audit(db, agency_id, user["id"], "document_export.generated", "document_export", created["id"], "Generated PDF document export.", {"rendered_document_id": document_id, "export_type": created["export_type"], "renderer": pdf_result.engine_name})
            return {"export": public_export(created)}

        export = DocumentExport(
            agency_id=agency_id,
            rendered_document_id=document_id,
            export_type="pdf",
            status="failed",
            filename=safe_filename(document["title"], ".pdf"),
            content_type="application/pdf",
            storage_mode="not_generated",
            generated_by_user_id=user["id"],
            generated_from_snapshot_at=document.get("rendered_at"),
            retention_policy="none",
            error_message=pdf_result.diagnostic or "PDF generation is not available in this installation.",
            client_visible=False,
        )
        created = await db.collection("document_exports").insert_one(export.model_dump(mode="json"))
        await write_document_timeline(db, agency_id, document_id, user["id"], "document_export.failed", "PDF export unavailable", created["error_message"], {"export_id": created["id"]})
        await write_audit(db, agency_id, user["id"], "document_export.failed", "document_export", created["id"], "PDF export requested but unavailable.", {"rendered_document_id": document_id})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=created["error_message"])

    html = document.get("rendered_html") or ""
    data = html.encode("utf-8")
    generated_at = datetime.now(timezone.utc)
    export = DocumentExport(
        agency_id=agency_id,
        rendered_document_id=document_id,
        export_type="print_html",
        status="generated",
        filename=safe_filename(document["title"], ".html"),
        content_type="text/html; charset=utf-8",
        storage_mode="file_path",
        retention_policy="keep_90_days",
        retention_expires_at=retention_expires_at("keep_90_days", generated_at),
        generated_by_user_id=user["id"],
        generated_at=generated_at,
        generated_from_snapshot_at=document.get("rendered_at"),
        client_visible=payload.client_visible and bool(document.get("client_visible")),
    )
    export_data = export.model_dump(mode="json")
    export_data.update(save_export_bytes(agency_id, export.id, export.filename, export.content_type, data))
    created = await db.collection("document_exports").insert_one(export_data)
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
    updated = await db.collection("document_exports").update_one({"agency_id": agency_id, "id": export_id}, {"status": "archived", "archived_at": datetime.now(timezone.utc), "archived_by_user_id": user["id"], "client_visible": False})
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
    for item in items:
        item["attempts"] = await list_delivery_attempts(db, agency_id, item["id"])
    items.sort(key=lambda item: str(item.get("created_at", "")), reverse=True)
    return {"items": items}


@router.get("/document-deliveries/{delivery_id}")
async def get_document_delivery(agency_id: str, delivery_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    delivery = await get_delivery_or_404(db, agency_id, delivery_id)
    await get_document_or_404(db, agency_id, delivery["rendered_document_id"])
    return {"delivery": delivery, "attempts": await list_delivery_attempts(db, agency_id, delivery_id)}


@router.get("/document-deliveries/{delivery_id}/diagnostics")
async def get_document_delivery_diagnostics(agency_id: str, delivery_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    delivery = await get_delivery_or_404(db, agency_id, delivery_id)
    document = await get_document_or_404(db, agency_id, delivery["rendered_document_id"])
    export = await get_export_or_404(db, agency_id, delivery["export_id"]) if delivery.get("export_id") else None
    attachment = safe_attachment_diagnostic(export, document)
    settings = await get_email_settings_or_default(db, agency_id)
    email_ok, email_error = validate_email_settings(settings)
    email_send_ready = email_ok and settings.get("mode") != "disabled"
    secret_check = check_secret(settings.get("smtp_password_secret_ref")) if settings.get("smtp_password_secret_ref") else None
    diagnostics = {
        "delivery_id": delivery["id"],
        "status": delivery.get("status"),
        "processing_state": delivery.get("processing_state"),
        "retry_status": delivery.get("retry_status"),
        "attempt_count": delivery.get("attempt_count") or 0,
        "max_attempts": delivery.get("max_attempts") or 3,
        "locked": bool(delivery.get("locked_at")),
        "last_error_message": delivery.get("last_error_message") or delivery.get("error_message"),
        "attachment": attachment,
        "email": {
            "mode": settings.get("mode") or "disabled",
            "valid": email_ok,
            "send_ready": email_send_ready,
            "validation_error": email_error,
            "smtp_secret_ref_masked": mask_secret_ref(settings.get("smtp_password_secret_ref")),
            "smtp_secret_configured": bool(settings.get("smtp_password_secret_ref")),
            "smtp_secret_resolved": bool(secret_check and secret_check.ok),
            "smtp_secret_diagnostic": secret_check.diagnostic if secret_check else "Secret reference is not configured.",
        },
    }
    diagnostics["next_allowed_action"] = next_delivery_action(delivery, attachment["valid"], email_send_ready)
    return {"diagnostics": diagnostics}


@router.post("/document-deliveries/{delivery_id}/send")
async def send_document_delivery(agency_id: str, delivery_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    return await process_delivery_send(db, agency_id, delivery_id, user)


@router.post("/document-deliveries/{delivery_id}/retry")
async def retry_document_delivery(agency_id: str, delivery_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    delivery = await get_delivery_or_404(db, agency_id, delivery_id)
    if delivery.get("retry_status") == "max_retries_reached":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum delivery attempts reached.")
    if delivery.get("retry_status") != "retry_available":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Delivery is not currently retryable.")
    return await process_delivery_send(db, agency_id, delivery_id, user)


@router.get("/document-deliveries/{delivery_id}/attempts")
async def get_document_delivery_attempts(agency_id: str, delivery_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    delivery = await get_delivery_or_404(db, agency_id, delivery_id)
    await get_document_or_404(db, agency_id, delivery["rendered_document_id"])
    return {"items": await list_delivery_attempts(db, agency_id, delivery_id)}


@router.post("/document-deliveries/{delivery_id}/cancel")
async def cancel_document_delivery(agency_id: str, delivery_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    delivery = await get_delivery_or_404(db, agency_id, delivery_id)
    if delivery.get("status") not in {"draft", "queued", "failed"} and delivery.get("retry_status") != "retry_available":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Delivery cannot be cancelled from its current status.")
    updated = await db.collection("document_deliveries").update_one(
        {"agency_id": agency_id, "id": delivery_id},
        {"status": "cancelled", "retry_status": "none", "next_retry_at": None, "locked_at": None, "locked_by": None, "processing_state": "manual_only"},
    )
    await write_document_timeline(db, agency_id, delivery["rendered_document_id"], user["id"], "document_delivery.cancelled", "Delivery cancelled", delivery["recipient_email"], {"delivery_id": delivery_id})
    await write_audit(db, agency_id, user["id"], "document_delivery.cancelled", "document_delivery", delivery_id, "Cancelled document delivery.", {"rendered_document_id": delivery["rendered_document_id"]})
    return {"delivery": updated}


@router.get("/email-settings")
async def get_email_settings(agency_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    return {"settings": public_email_settings(await get_email_settings_or_default(db, agency_id))}


@router.put("/email-settings")
async def update_email_settings(agency_id: str, payload: AgencyEmailSettingsUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_template_write(db, agency_id, user)
    current = await db.collection("agency_email_settings").find_one({"agency_id": agency_id, "status": "active"})
    updates = clean_updates(payload)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update fields provided.")
    if updates.get("smtp_password_secret_ref"):
        updates["smtp_password_is_configured"] = True
    candidate = {**(current or {}), **updates}
    ok, validation_error = validate_email_settings(candidate)
    updates["last_validation_error"] = validation_error
    updates["verified_at"] = datetime.now(timezone.utc) if ok and candidate.get("mode") != "disabled" else None
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
    return {"settings": public_email_settings(updated), "validation": {"ok": ok, "error": validation_error}}


@router.post("/email-settings/validate")
async def validate_agency_email_settings(agency_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_template_write(db, agency_id, user)
    settings = await get_email_settings_or_default(db, agency_id)
    ok, validation_error = validate_email_settings(settings)
    updated = await db.collection("agency_email_settings").update_one(
        {"agency_id": agency_id, "id": settings["id"]},
        {"last_validation_error": validation_error, "verified_at": datetime.now(timezone.utc) if ok and settings.get("mode") != "disabled" else None},
    ) if settings.get("id") else settings
    return {"settings": public_email_settings(updated), "validation": {"ok": ok, "error": validation_error}}


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
    payload = {"items": [public_portal_export(item) for item in exports]}
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
