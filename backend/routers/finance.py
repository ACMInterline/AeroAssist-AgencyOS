from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    AuditEvent,
    BookingTimelineEvent,
    Invoice,
    InvoiceCreate,
    InvoiceLineItem,
    InvoiceLineItemCreate,
    InvoiceLineItemUpdate,
    InvoiceUpdate,
    PaymentRecord,
    PaymentRecordCreate,
    PaymentRecordUpdate,
)
from services.tenant_service import assert_agency_access, require_any_agency_role

router = APIRouter(prefix="/api/agencies/{agency_id}", tags=["finance"])

READ_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant", "agency_readonly"]
WRITE_ROLES = ["agency_owner", "agency_admin", "agency_agent", "agency_accountant"]


def clean_updates(payload: Any) -> dict:
    return payload.model_dump(exclude_unset=True, mode="json")


async def require_read(db: Database, agency_id: str, user: dict) -> None:
    await assert_agency_access(db, agency_id, user)
    if user.get("global_role") not in {"platform_owner", "platform_admin", "platform_support"}:
        await require_any_agency_role(db, agency_id, user, READ_ROLES)


async def require_write(db: Database, agency_id: str, user: dict) -> None:
    if user.get("global_role") not in {"platform_owner", "platform_admin"}:
        await require_any_agency_role(db, agency_id, user, WRITE_ROLES)


async def write_audit(db: Database, agency_id: str, actor_user_id: str, event_type: str, entity_type: str, entity_id: str, summary: str, metadata: dict | None = None) -> None:
    event = AuditEvent(agency_id=agency_id, actor_user_id=actor_user_id, event_type=event_type, entity_type=entity_type, entity_id=entity_id, summary=summary, metadata=metadata or {})
    await db.collection("audit_events").insert_one(event.model_dump(mode="json"))


async def write_booking_timeline(db: Database, agency_id: str, booking_id: str | None, actor_user_id: str | None, event_type: str, title: str, summary: str | None = None, metadata: dict | None = None) -> None:
    if not booking_id:
        return
    event = BookingTimelineEvent(agency_id=agency_id, booking_id=booking_id, actor_user_id=actor_user_id, event_type=event_type, title=title, summary=summary, visibility="internal", metadata=metadata or {})
    await db.collection("booking_timeline_events").insert_one(event.model_dump(mode="json"))


async def next_invoice_number(db: Database, agency_id: str) -> str:
    count = await db.collection("invoices").count({"agency_id": agency_id})
    return f"INV-{count + 1:05d}"


async def get_client_or_404(db: Database, agency_id: str, client_id: str) -> dict:
    client = await db.collection("client_profiles").find_one({"agency_id": agency_id, "id": client_id})
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")
    return client


async def get_invoice_or_404(db: Database, agency_id: str, invoice_id: str) -> dict:
    invoice = await db.collection("invoices").find_one({"agency_id": agency_id, "id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found.")
    return invoice


async def recalc_booking_from_invoices(db: Database, agency_id: str, booking_id: str | None) -> None:
    if not booking_id:
        return
    invoices = await db.collection("invoices").find_many({"agency_id": agency_id, "booking_id": booking_id})
    active = [invoice for invoice in invoices if invoice.get("status") not in {"voided", "cancelled", "archived"}]
    total = sum(float(invoice.get("total_amount") or 0) for invoice in active)
    paid = sum(float(invoice.get("paid_amount") or 0) for invoice in active)
    await db.collection("bookings").update_one({"agency_id": agency_id, "id": booking_id}, {"total_amount": total, "amount_paid": paid, "amount_due": max(total - paid, 0)})


async def recalc_invoice(db: Database, agency_id: str, invoice_id: str) -> dict:
    invoice = await get_invoice_or_404(db, agency_id, invoice_id)
    lines = await db.collection("invoice_line_items").find_many({"agency_id": agency_id, "invoice_id": invoice_id, "status": "active"})
    subtotal = sum(float(line.get("total_amount") or 0) for line in lines)
    tax_total = sum(float(line.get("total_amount") or 0) for line in lines if line.get("line_type") == "taxes")
    payments = await db.collection("payment_records").find_many({"agency_id": agency_id, "invoice_id": invoice_id, "status": "received"})
    paid = sum(float(payment.get("amount") or 0) for payment in payments)
    due = max(subtotal - paid, 0)
    status_value = invoice.get("status")
    paid_at = invoice.get("paid_at")
    if status_value not in {"draft", "voided", "cancelled", "archived"}:
        if paid >= subtotal and subtotal > 0:
            status_value = "paid"
            paid_at = paid_at or datetime.now(timezone.utc)
        elif paid > 0:
            status_value = "partially_paid"
        elif status_value == "paid":
            status_value = "issued"
            paid_at = None
    updated = await db.collection("invoices").update_one(
        {"agency_id": agency_id, "id": invoice_id},
        {
            "subtotal_amount": subtotal,
            "tax_amount": tax_total,
            "total_amount": subtotal,
            "paid_amount": paid,
            "due_amount": due,
            "status": status_value,
            "paid_at": paid_at,
        },
    )
    await recalc_booking_from_invoices(db, agency_id, invoice.get("booking_id"))
    return updated


async def invoice_detail(db: Database, agency_id: str, invoice_id: str) -> dict:
    invoice = await get_invoice_or_404(db, agency_id, invoice_id)
    return {
        "invoice": invoice,
        "client": await get_client_or_404(db, agency_id, invoice["client_id"]),
        "line_items": await db.collection("invoice_line_items").find_many({"agency_id": agency_id, "invoice_id": invoice_id}),
        "payments": await db.collection("payment_records").find_many({"agency_id": agency_id, "invoice_id": invoice_id}),
        "booking": await db.collection("bookings").find_one({"agency_id": agency_id, "id": invoice["booking_id"]}) if invoice.get("booking_id") else None,
    }


@router.get("/invoices")
async def list_invoices(agency_id: str, status_filter: Optional[str] = Query(default=None, alias="status"), client_id: Optional[str] = None, booking_id: Optional[str] = None, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    filters = {"agency_id": agency_id}
    if status_filter:
        filters["status"] = status_filter
    if client_id:
        filters["client_id"] = client_id
    if booking_id:
        filters["booking_id"] = booking_id
    items = await db.collection("invoices").find_many(filters)
    clients = {client["id"]: client for client in await db.collection("client_profiles").find_many({"agency_id": agency_id})}
    bookings = {booking["id"]: booking for booking in await db.collection("bookings").find_many({"agency_id": agency_id})}
    items.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    return {"items": [{**item, "client": clients.get(item["client_id"]), "booking": bookings.get(item.get("booking_id"))} for item in items]}


@router.post("/invoices", status_code=status.HTTP_201_CREATED)
async def create_invoice(agency_id: str, payload: InvoiceCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    await get_client_or_404(db, agency_id, payload.client_id)
    if payload.booking_id and not await db.collection("bookings").find_one({"agency_id": agency_id, "id": payload.booking_id, "client_id": payload.client_id}):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Booking must belong to the selected client.")
    if payload.offer_id and not await db.collection("offers").find_one({"agency_id": agency_id, "id": payload.offer_id, "client_id": payload.client_id}):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Offer must belong to the selected client.")
    invoice = Invoice(agency_id=agency_id, invoice_number=payload.invoice_number or await next_invoice_number(db, agency_id), **payload.model_dump(exclude={"invoice_number"}, mode="json"))
    created = await db.collection("invoices").insert_one(invoice.model_dump(mode="json"))
    await write_booking_timeline(db, agency_id, invoice.booking_id, user["id"], "finance.invoice_created", "Invoice created", invoice.invoice_number)
    await write_audit(db, agency_id, user["id"], "invoice.created", "invoice", invoice.id, f"Created invoice {invoice.invoice_number}.")
    return {"invoice": created}


@router.get("/invoices/{invoice_id}")
async def get_invoice(agency_id: str, invoice_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    return await invoice_detail(db, agency_id, invoice_id)


@router.put("/invoices/{invoice_id}")
async def update_invoice(agency_id: str, invoice_id: str, payload: InvoiceUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    invoice = await get_invoice_or_404(db, agency_id, invoice_id)
    updated = await db.collection("invoices").update_one({"agency_id": agency_id, "id": invoice_id}, clean_updates(payload))
    await recalc_booking_from_invoices(db, agency_id, invoice.get("booking_id"))
    return {"invoice": updated}


@router.post("/invoices/{invoice_id}/issue")
async def issue_invoice(agency_id: str, invoice_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    invoice = await get_invoice_or_404(db, agency_id, invoice_id)
    updated = await db.collection("invoices").update_one({"agency_id": agency_id, "id": invoice_id}, {"status": "issued", "issued_at": datetime.now(timezone.utc)})
    await write_booking_timeline(db, agency_id, invoice.get("booking_id"), user["id"], "finance.invoice_issued", "Invoice issued", invoice["invoice_number"])
    return {"invoice": updated}


@router.post("/invoices/{invoice_id}/void")
async def void_invoice(agency_id: str, invoice_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    invoice = await get_invoice_or_404(db, agency_id, invoice_id)
    updated = await db.collection("invoices").update_one({"agency_id": agency_id, "id": invoice_id}, {"status": "voided"})
    await recalc_booking_from_invoices(db, agency_id, invoice.get("booking_id"))
    await write_booking_timeline(db, agency_id, invoice.get("booking_id"), user["id"], "finance.invoice_voided", "Invoice voided", invoice["invoice_number"])
    return {"invoice": updated}


@router.get("/invoices/{invoice_id}/line-items")
async def list_line_items(agency_id: str, invoice_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    await get_invoice_or_404(db, agency_id, invoice_id)
    return {"items": await db.collection("invoice_line_items").find_many({"agency_id": agency_id, "invoice_id": invoice_id})}


@router.post("/invoices/{invoice_id}/line-items", status_code=status.HTTP_201_CREATED)
async def create_line_item(agency_id: str, invoice_id: str, payload: InvoiceLineItemCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    invoice = await get_invoice_or_404(db, agency_id, invoice_id)
    total = payload.total_amount if payload.total_amount is not None else payload.quantity * payload.unit_amount
    line = InvoiceLineItem(agency_id=agency_id, invoice_id=invoice_id, booking_id=payload.booking_id or invoice.get("booking_id"), total_amount=total, **payload.model_dump(exclude={"total_amount", "booking_id"}, mode="json"))
    created = await db.collection("invoice_line_items").insert_one(line.model_dump(mode="json"))
    await recalc_invoice(db, agency_id, invoice_id)
    await write_booking_timeline(db, agency_id, invoice.get("booking_id"), user["id"], "finance.invoice_line_added", "Invoice line added", line.description)
    return {"line_item": created}


@router.put("/invoices/{invoice_id}/line-items/{line_id}")
async def update_line_item(agency_id: str, invoice_id: str, line_id: str, payload: InvoiceLineItemUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    current = await db.collection("invoice_line_items").find_one({"agency_id": agency_id, "invoice_id": invoice_id, "id": line_id})
    if not current:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice line item not found.")
    updates = clean_updates(payload)
    if "total_amount" not in updates and ("quantity" in updates or "unit_amount" in updates):
        updates["total_amount"] = float(updates.get("quantity", current.get("quantity") or 0)) * float(updates.get("unit_amount", current.get("unit_amount") or 0))
    updated = await db.collection("invoice_line_items").update_one({"agency_id": agency_id, "invoice_id": invoice_id, "id": line_id}, updates)
    await recalc_invoice(db, agency_id, invoice_id)
    return {"line_item": updated}


@router.post("/invoices/{invoice_id}/line-items/{line_id}/archive")
async def archive_line_item(agency_id: str, invoice_id: str, line_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    updated = await db.collection("invoice_line_items").update_one({"agency_id": agency_id, "invoice_id": invoice_id, "id": line_id}, {"status": "archived"})
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice line item not found.")
    await recalc_invoice(db, agency_id, invoice_id)
    return {"line_item": updated}


@router.get("/payments")
async def list_payments(agency_id: str, status_filter: Optional[str] = Query(default=None, alias="status"), invoice_id: Optional[str] = None, client_id: Optional[str] = None, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    filters = {"agency_id": agency_id}
    if status_filter:
        filters["status"] = status_filter
    if invoice_id:
        filters["invoice_id"] = invoice_id
    if client_id:
        filters["client_id"] = client_id
    items = await db.collection("payment_records").find_many(filters)
    invoices = {invoice["id"]: invoice for invoice in await db.collection("invoices").find_many({"agency_id": agency_id})}
    clients = {client["id"]: client for client in await db.collection("client_profiles").find_many({"agency_id": agency_id})}
    items.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    return {"items": [{**item, "invoice": invoices.get(item["invoice_id"]), "client": clients.get(item["client_id"])} for item in items]}


@router.post("/payments", status_code=status.HTTP_201_CREATED)
async def create_payment(agency_id: str, payload: PaymentRecordCreate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    invoice = await get_invoice_or_404(db, agency_id, payload.invoice_id)
    if invoice["client_id"] != payload.client_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment client must match invoice client.")
    if payload.booking_id and payload.booking_id != invoice.get("booking_id"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment booking must match invoice booking.")
    payment = PaymentRecord(agency_id=agency_id, **payload.model_dump(mode="json"))
    created = await db.collection("payment_records").insert_one(payment.model_dump(mode="json"))
    await recalc_invoice(db, agency_id, payload.invoice_id)
    await write_booking_timeline(db, agency_id, invoice.get("booking_id"), user["id"], "finance.payment_created", "Payment tracking record created", f"{payment.amount} {payment.currency}")
    await write_audit(db, agency_id, user["id"], "payment.created", "payment", payment.id, "Created payment tracking record.")
    return {"payment": created}


@router.get("/payments/{payment_id}")
async def get_payment(agency_id: str, payment_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_read(db, agency_id, user)
    payment = await db.collection("payment_records").find_one({"agency_id": agency_id, "id": payment_id})
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found.")
    return {"payment": payment}


@router.put("/payments/{payment_id}")
async def update_payment(agency_id: str, payment_id: str, payload: PaymentRecordUpdate, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    payment = await db.collection("payment_records").find_one({"agency_id": agency_id, "id": payment_id})
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found.")
    updated = await db.collection("payment_records").update_one({"agency_id": agency_id, "id": payment_id}, clean_updates(payload))
    await recalc_invoice(db, agency_id, payment["invoice_id"])
    return {"payment": updated}


@router.post("/payments/{payment_id}/mark-received")
async def mark_payment_received(agency_id: str, payment_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    payment = await db.collection("payment_records").find_one({"agency_id": agency_id, "id": payment_id})
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found.")
    updated = await db.collection("payment_records").update_one({"agency_id": agency_id, "id": payment_id}, {"status": "received", "received_at": datetime.now(timezone.utc)})
    invoice = await recalc_invoice(db, agency_id, payment["invoice_id"])
    await write_booking_timeline(db, agency_id, invoice.get("booking_id"), user["id"], "finance.payment_received", "Payment received manually", f"{updated['amount']} {updated['currency']}")
    return {"payment": updated}


@router.post("/payments/{payment_id}/mark-reconciled")
async def mark_payment_reconciled(agency_id: str, payment_id: str, user: dict = Depends(get_current_user), db: Database = Depends(get_database)) -> dict:
    await require_write(db, agency_id, user)
    payment = await db.collection("payment_records").find_one({"agency_id": agency_id, "id": payment_id})
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found.")
    updated = await db.collection("payment_records").update_one({"agency_id": agency_id, "id": payment_id}, {"reconciliation_status": "reconciled"})
    invoice = await get_invoice_or_404(db, agency_id, payment["invoice_id"])
    await write_booking_timeline(db, agency_id, invoice.get("booking_id"), user["id"], "finance.payment_reconciled", "Payment reconciled", updated.get("external_reference"))
    return {"payment": updated}
