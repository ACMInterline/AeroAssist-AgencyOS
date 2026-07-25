from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth import get_current_user
from database import Database, get_database
from models import (
    CreditNoteCreate,
    ExchangeLedgerEntryCreate,
    InvoiceCreate,
    InvoiceLineItemCreate,
    InvoiceLineItemUpdate,
    InvoiceUpdate,
    PaymentAllocationCreate,
    PaymentRecordCreate,
    PaymentRecordUpdate,
    RefundLedgerEntryCreate,
    SupplierCostCreate,
    SupplierCostLineCreate,
)
from persistence_query import PaginationRequest
from persistence_repository import PersistenceRepository
from services.authorization_service import agency_permissions
from services.canonical_commercial_ledger_service import (
    CREDIT_NOTES_COLLECTION,
    EXCHANGE_LEDGER_ENTRIES_COLLECTION,
    PAYMENT_ALLOCATIONS_COLLECTION,
    REFUND_LEDGER_ENTRIES_COLLECTION,
    SUPPLIER_COSTS_COLLECTION,
    SUPPLIER_COST_LINES_COLLECTION,
    CanonicalCommercialLedgerService,
    CommercialLedgerError,
)
from services.tenant_service import assert_agency_access, get_membership


router = APIRouter(prefix="/api/agencies/{agency_id}", tags=["finance"])


async def require_permission(
    db: Database,
    agency_id: str,
    user: dict[str, Any],
    permission: str,
) -> dict[str, Any]:
    await assert_agency_access(db, agency_id, user)
    membership = await get_membership(db, agency_id, user["id"])
    permissions = agency_permissions(membership.get("agency_role"))
    if permission not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission {permission} is required.",
        )
    return membership


async def require_read(
    db: Database, agency_id: str, user: dict[str, Any]
) -> None:
    await require_permission(db, agency_id, user, "view_finance")


async def require_write(
    db: Database, agency_id: str, user: dict[str, Any]
) -> None:
    await require_permission(db, agency_id, user, "edit_commercial_ledger")


async def require_cost_read(
    db: Database, agency_id: str, user: dict[str, Any]
) -> None:
    await require_permission(db, agency_id, user, "view_supplier_costs")


def clean_updates(payload: Any) -> dict[str, Any]:
    return payload.model_dump(exclude_unset=True, mode="json")


def translate_error(exc: CommercialLedgerError) -> HTTPException:
    not_found_codes = {
        "INVOICE_NOT_FOUND",
        "INVOICE_LINE_NOT_FOUND",
        "PAYMENT_NOT_FOUND",
        "PAYMENT_ALLOCATION_NOT_FOUND",
        "SUPPLIER_COST_NOT_FOUND",
        "CREDIT_NOTE_NOT_FOUND",
    }
    conflict_codes = {
        "IDEMPOTENCY_CONFLICT",
        "OVERALLOCATION",
        "CREDIT_EXCEEDS_INVOICE",
        "INVOICE_IMMUTABLE_AFTER_ISSUE",
        "SUPPLIER_COST_IMMUTABLE",
        "INVOICE_HAS_ALLOCATIONS",
    }
    code = (
        status.HTTP_404_NOT_FOUND
        if exc.code in not_found_codes
        else status.HTTP_409_CONFLICT
        if exc.code in conflict_codes
        else status.HTTP_400_BAD_REQUEST
    )
    return HTTPException(
        status_code=code,
        detail={"code": exc.code, "message": str(exc)},
    )


async def call(operation):
    try:
        return await operation
    except CommercialLedgerError as exc:
        raise translate_error(exc) from exc


async def list_agency_records(
    db: Database,
    agency_id: str,
    collection_name: str,
    filters: dict[str, Any] | None = None,
    *,
    maximum_records: int = 5000,
) -> list[dict[str, Any]]:
    repository = PersistenceRepository(db)
    records: list[dict[str, Any]] = []
    offset = 0
    while len(records) < maximum_records:
        page = await repository.find_agency_records(
            collection_name=collection_name,
            agency_id=agency_id,
            filters=filters,
            pagination=PaginationRequest.build(
                limit=maximum_records - len(records),
                offset=offset,
            ),
        )
        records.extend(page.items)
        if not page.pagination.has_more or not page.items:
            return records
        offset += len(page.items)
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="The finance result exceeds the bounded query limit.",
    )


@router.get("/invoices")
async def list_invoices(
    agency_id: str,
    status_filter: Optional[str] = Query(default=None, alias="status"),
    client_id: Optional[str] = None,
    booking_id: Optional[str] = None,
    booking_workspace_id: Optional[str] = None,
    trip_id: Optional[str] = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    filters: dict[str, Any] = {}
    if status_filter:
        filters["status"] = status_filter
    if client_id:
        filters["client_id"] = client_id
    if booking_id:
        filters["booking_id"] = booking_id
    if booking_workspace_id:
        filters["booking_workspace_id"] = booking_workspace_id
    if trip_id:
        filters["trip_id"] = trip_id
    items = await list_agency_records(db, agency_id, "invoices", filters)
    clients = {
        client["id"]: client
        for client in await list_agency_records(
            db, agency_id, "client_profiles"
        )
    }
    bookings = {
        booking["id"]: booking
        for booking in await list_agency_records(db, agency_id, "bookings")
    }
    workspaces: dict[str, dict[str, Any]] = {}
    for item in items:
        workspace_id = item.get("booking_workspace_id")
        if workspace_id and workspace_id not in workspaces:
            workspace = await db.collection("booking_workspaces").find_one(
                {"agency_id": agency_id, "id": workspace_id}
            )
            if workspace:
                workspaces[workspace_id] = workspace
    return {
        "items": [
            {
                **item,
                "client": clients.get(item["client_id"]),
                "booking": bookings.get(item.get("booking_id"))
                or workspaces.get(item.get("booking_workspace_id")),
            }
            for item in items
        ]
    }


@router.post("/invoices", status_code=status.HTTP_201_CREATED)
async def create_invoice(
    agency_id: str,
    payload: InvoiceCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    created = await call(
        CanonicalCommercialLedgerService(db).create_invoice(
            agency_id, payload, user["id"]
        )
    )
    return {"invoice": created}


@router.post(
    "/booking-workspaces/{booking_workspace_id}/invoice",
    status_code=status.HTTP_201_CREATED,
)
async def create_invoice_from_booking_workspace(
    agency_id: str,
    booking_workspace_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    workspace = await db.collection("booking_workspaces").find_one(
        {"agency_id": agency_id, "id": booking_workspace_id}
    )
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking workspace not found.",
        )
    booking_record = (
        await db.collection("booking_records").find_one(
            {
                "agency_id": agency_id,
                "id": workspace.get("booking_record_id"),
            }
        )
        if workspace.get("booking_record_id")
        else None
    )
    client_id = workspace.get("client_id") or (booking_record or {}).get(
        "client_id"
    )
    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking workspace requires a canonical client before finance can continue.",
        )
    existing = await db.collection("invoices").find_one(
        {
            "agency_id": agency_id,
            "booking_workspace_id": booking_workspace_id,
            "status": {"$ne": "cancelled"},
        }
    )
    if existing:
        return {"invoice": existing, "idempotent_reused": True}
    trip_id = workspace.get("trip_id") or (booking_record or {}).get("trip_id")
    trip = (
        await db.collection("trip_dossiers").find_one(
            {"agency_id": agency_id, "id": trip_id}
        )
        if trip_id
        else None
    )
    accepted_snapshot_id = (
        workspace.get("accepted_offer_snapshot_id")
        or workspace.get("offer_snapshot_id")
        or (trip or {}).get("accepted_offer_snapshot_id")
    )
    payload = InvoiceCreate(
        client_id=client_id,
        trip_id=trip_id,
        booking_id=(booking_record or {}).get("id"),
        booking_workspace_id=booking_workspace_id,
        booking_record_id=(booking_record or {}).get("id"),
        offer_id=workspace.get("offer_workspace_id"),
        accepted_offer_snapshot_id=accepted_snapshot_id,
        currency=(
            (workspace.get("pricing_snapshot_json") or {}).get("currency")
            or (booking_record or {}).get("currency")
            or "EUR"
        ),
    )
    created = await call(
        CanonicalCommercialLedgerService(db).create_invoice(
            agency_id, payload, user["id"]
        )
    )
    return {"invoice": created, "idempotent_reused": False}


@router.get("/invoices/{invoice_id}")
async def get_invoice(
    agency_id: str,
    invoice_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    membership = await get_membership(db, agency_id, user["id"])
    include_costs = "view_supplier_costs" in agency_permissions(
        membership.get("agency_role")
    )
    return await call(
        CanonicalCommercialLedgerService(db).invoice_detail(
            agency_id, invoice_id, include_costs=include_costs
        )
    )


@router.put("/invoices/{invoice_id}")
async def update_invoice(
    agency_id: str,
    invoice_id: str,
    payload: InvoiceUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    updated = await call(
        CanonicalCommercialLedgerService(db).update_invoice_metadata(
            agency_id, invoice_id, clean_updates(payload), user["id"]
        )
    )
    return {"invoice": updated}


@router.post("/invoices/{invoice_id}/issue")
async def issue_invoice(
    agency_id: str,
    invoice_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    updated = await call(
        CanonicalCommercialLedgerService(db).issue_invoice(
            agency_id, invoice_id, user["id"]
        )
    )
    return {"invoice": updated}


@router.post("/invoices/{invoice_id}/cancel")
async def cancel_invoice(
    agency_id: str,
    invoice_id: str,
    payload: dict[str, Any],
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    reason = str(payload.get("reason") or "").strip()
    if not reason:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cancellation reason is required.",
        )
    updated = await call(
        CanonicalCommercialLedgerService(db).cancel_invoice(
            agency_id, invoice_id, user["id"], reason
        )
    )
    return {"invoice": updated}


@router.post("/invoices/{invoice_id}/void")
async def void_invoice_compatibility_adapter(
    agency_id: str,
    invoice_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    """Compatibility adapter. Canonical invoices are cancelled, never void-mutated."""
    await require_write(db, agency_id, user)
    updated = await call(
        CanonicalCommercialLedgerService(db).cancel_invoice(
            agency_id,
            invoice_id,
            user["id"],
            "Legacy void action mapped to canonical cancellation.",
        )
    )
    return {"invoice": updated, "compatibility_adapter": True}


@router.get("/invoices/{invoice_id}/line-items")
async def list_line_items(
    agency_id: str,
    invoice_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    await call(CanonicalCommercialLedgerService(db).get_invoice(agency_id, invoice_id))
    return {
        "items": await list_agency_records(
            db,
            agency_id,
            "invoice_line_items",
            {"invoice_id": invoice_id},
        )
    }


@router.post(
    "/invoices/{invoice_id}/line-items",
    status_code=status.HTTP_201_CREATED,
)
async def create_line_item(
    agency_id: str,
    invoice_id: str,
    payload: InvoiceLineItemCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    created = await call(
        CanonicalCommercialLedgerService(db).add_invoice_line(
            agency_id, invoice_id, payload, user["id"]
        )
    )
    return {"line_item": created}


@router.put("/invoices/{invoice_id}/line-items/{line_id}")
async def update_line_item(
    agency_id: str,
    invoice_id: str,
    line_id: str,
    payload: InvoiceLineItemUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    updated = await call(
        CanonicalCommercialLedgerService(db).update_invoice_line(
            agency_id, invoice_id, line_id, clean_updates(payload), user["id"]
        )
    )
    return {"line_item": updated}


@router.post("/invoices/{invoice_id}/line-items/{line_id}/archive")
async def archive_line_item(
    agency_id: str,
    invoice_id: str,
    line_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    updated = await call(
        CanonicalCommercialLedgerService(db).archive_invoice_line(
            agency_id, invoice_id, line_id, user["id"]
        )
    )
    return {"line_item": updated}


@router.get("/payments")
async def list_payments(
    agency_id: str,
    status_filter: Optional[str] = Query(default=None, alias="status"),
    invoice_id: Optional[str] = None,
    client_id: Optional[str] = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    filters: dict[str, Any] = {}
    if status_filter:
        filters["status"] = status_filter
    if client_id:
        filters["client_id"] = client_id
    items = await list_agency_records(
        db, agency_id, "payment_records", filters
    )
    allocations = await list_agency_records(
        db, agency_id, PAYMENT_ALLOCATIONS_COLLECTION
    )
    by_payment: dict[str, list[dict[str, Any]]] = {}
    for allocation in allocations:
        by_payment.setdefault(allocation["payment_record_id"], []).append(allocation)
    if invoice_id:
        items = [
            item
            for item in items
            if item.get("invoice_id") == invoice_id
            or any(
                allocation.get("invoice_id") == invoice_id
                for allocation in by_payment.get(item["id"], [])
            )
        ]
    invoices = {
        invoice["id"]: invoice
        for invoice in await list_agency_records(db, agency_id, "invoices")
    }
    clients = {
        client["id"]: client
        for client in await list_agency_records(
            db, agency_id, "client_profiles"
        )
    }
    return {
        "items": [
            {
                **item,
                "allocations": by_payment.get(item["id"], []),
                "invoice": invoices.get(item.get("invoice_id"))
                or next(
                    (
                        invoices.get(allocation.get("invoice_id"))
                        for allocation in by_payment.get(item["id"], [])
                        if invoices.get(allocation.get("invoice_id"))
                    ),
                    None,
                ),
                "client": clients.get(item["client_id"]),
            }
            for item in items
        ]
    }


@router.post("/payments", status_code=status.HTTP_201_CREATED)
async def create_payment(
    agency_id: str,
    payload: PaymentRecordCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    created = await call(
        CanonicalCommercialLedgerService(db).create_payment(
            agency_id, payload, user["id"]
        )
    )
    return {"payment": created}


@router.get("/payments/{payment_id}")
async def get_payment(
    agency_id: str,
    payment_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    payment = await db.collection("payment_records").find_one(
        {"agency_id": agency_id, "id": payment_id}
    )
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found.",
        )
    allocations = await list_agency_records(
        db,
        agency_id,
        PAYMENT_ALLOCATIONS_COLLECTION,
        {"payment_record_id": payment_id},
    )
    return {"payment": payment, "allocations": allocations}


@router.put("/payments/{payment_id}")
async def update_payment(
    agency_id: str,
    payment_id: str,
    payload: PaymentRecordUpdate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    updates = clean_updates(payload)
    status_value = updates.pop("status", None)
    if status_value == "received":
        await call(
            CanonicalCommercialLedgerService(db).mark_payment_received(
                agency_id, payment_id, user["id"]
            )
        )
    elif status_value is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment lifecycle actions use explicit endpoints.",
        )
    updated = await call(
        CanonicalCommercialLedgerService(db).update_payment_metadata(
            agency_id, payment_id, updates, user["id"]
        )
    )
    return {"payment": updated}


@router.post("/payments/{payment_id}/mark-received")
async def mark_payment_received(
    agency_id: str,
    payment_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    updated = await call(
        CanonicalCommercialLedgerService(db).mark_payment_received(
            agency_id, payment_id, user["id"]
        )
    )
    return {"payment": updated}


@router.post("/payments/{payment_id}/mark-reconciled")
async def mark_payment_reconciled(
    agency_id: str,
    payment_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    updated = await call(
        CanonicalCommercialLedgerService(db).mark_payment_reconciled(
            agency_id, payment_id, user["id"]
        )
    )
    return {"payment": updated}


@router.get("/payments/{payment_id}/allocations")
async def list_payment_allocations(
    agency_id: str,
    payment_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    return {
        "items": await list_agency_records(
            db,
            agency_id,
            PAYMENT_ALLOCATIONS_COLLECTION,
            {"payment_record_id": payment_id},
        )
    }


@router.post(
    "/payments/{payment_id}/allocations",
    status_code=status.HTTP_201_CREATED,
)
async def create_payment_allocation(
    agency_id: str,
    payment_id: str,
    payload: PaymentAllocationCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    created = await call(
        CanonicalCommercialLedgerService(db).allocate_payment(
            agency_id, payment_id, payload, user["id"]
        )
    )
    return {"allocation": created}


@router.get("/finance/supplier-costs")
async def list_supplier_costs(
    agency_id: str,
    trip_id: Optional[str] = None,
    booking_id: Optional[str] = None,
    status_filter: Optional[str] = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_cost_read(db, agency_id, user)
    filters: dict[str, Any] = {}
    if trip_id:
        filters["trip_id"] = trip_id
    if booking_id:
        filters["booking_id"] = booking_id
    if status_filter:
        filters["status"] = status_filter
    return {
        "items": await list_agency_records(
            db, agency_id, SUPPLIER_COSTS_COLLECTION, filters
        )
    }


@router.post(
    "/finance/supplier-costs", status_code=status.HTTP_201_CREATED
)
async def create_supplier_cost(
    agency_id: str,
    payload: SupplierCostCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    await require_cost_read(db, agency_id, user)
    created = await call(
        CanonicalCommercialLedgerService(db).create_supplier_cost(
            agency_id, payload, user["id"]
        )
    )
    return {"supplier_cost": created}


@router.get("/finance/supplier-costs/{supplier_cost_id}")
async def get_supplier_cost(
    agency_id: str,
    supplier_cost_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_cost_read(db, agency_id, user)
    item = await db.collection(SUPPLIER_COSTS_COLLECTION).find_one(
        {"agency_id": agency_id, "id": supplier_cost_id}
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier cost not found.",
        )
    return {
        "supplier_cost": item,
        "lines": await list_agency_records(
            db,
            agency_id,
            SUPPLIER_COST_LINES_COLLECTION,
            {"supplier_cost_id": supplier_cost_id},
        ),
    }


@router.post(
    "/finance/supplier-costs/{supplier_cost_id}/lines",
    status_code=status.HTTP_201_CREATED,
)
async def create_supplier_cost_line(
    agency_id: str,
    supplier_cost_id: str,
    payload: SupplierCostLineCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    await require_cost_read(db, agency_id, user)
    created = await call(
        CanonicalCommercialLedgerService(db).add_supplier_cost_line(
            agency_id, supplier_cost_id, payload, user["id"]
        )
    )
    return {"supplier_cost_line": created}


@router.post("/finance/supplier-costs/{supplier_cost_id}/confirm")
async def confirm_supplier_cost(
    agency_id: str,
    supplier_cost_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    await require_cost_read(db, agency_id, user)
    updated = await call(
        CanonicalCommercialLedgerService(db).confirm_supplier_cost(
            agency_id, supplier_cost_id, user["id"]
        )
    )
    return {"supplier_cost": updated}


@router.get("/finance/credit-notes")
async def list_credit_notes(
    agency_id: str,
    invoice_id: Optional[str] = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    filters: dict[str, Any] = {}
    if invoice_id:
        filters["invoice_id"] = invoice_id
    return {
        "items": await list_agency_records(
            db, agency_id, CREDIT_NOTES_COLLECTION, filters
        )
    }


@router.post("/finance/credit-notes", status_code=status.HTTP_201_CREATED)
async def create_credit_note(
    agency_id: str,
    payload: CreditNoteCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    created = await call(
        CanonicalCommercialLedgerService(db).create_credit_note(
            agency_id, payload, user["id"]
        )
    )
    return {"credit_note": created}


@router.post("/finance/credit-notes/{credit_note_id}/issue")
async def issue_credit_note(
    agency_id: str,
    credit_note_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    updated = await call(
        CanonicalCommercialLedgerService(db).issue_credit_note(
            agency_id, credit_note_id, user["id"]
        )
    )
    return {"credit_note": updated}


@router.get("/finance/refunds")
async def list_refund_entries(
    agency_id: str,
    trip_id: Optional[str] = None,
    booking_id: Optional[str] = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    filters: dict[str, Any] = {}
    if trip_id:
        filters["trip_id"] = trip_id
    if booking_id:
        filters["booking_id"] = booking_id
    return {
        "items": await list_agency_records(
            db, agency_id, REFUND_LEDGER_ENTRIES_COLLECTION, filters
        )
    }


@router.post("/finance/refunds", status_code=status.HTTP_201_CREATED)
async def create_refund_entry(
    agency_id: str,
    payload: RefundLedgerEntryCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    created = await call(
        CanonicalCommercialLedgerService(db).create_refund_entry(
            agency_id, payload, user["id"]
        )
    )
    return {"refund": created}


@router.get("/finance/exchanges")
async def list_exchange_entries(
    agency_id: str,
    trip_id: Optional[str] = None,
    booking_id: Optional[str] = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    filters: dict[str, Any] = {}
    if trip_id:
        filters["trip_id"] = trip_id
    if booking_id:
        filters["booking_id"] = booking_id
    return {
        "items": await list_agency_records(
            db, agency_id, EXCHANGE_LEDGER_ENTRIES_COLLECTION, filters
        )
    }


@router.post("/finance/exchanges", status_code=status.HTTP_201_CREATED)
async def create_exchange_entry(
    agency_id: str,
    payload: ExchangeLedgerEntryCreate,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_write(db, agency_id, user)
    created = await call(
        CanonicalCommercialLedgerService(db).create_exchange_entry(
            agency_id, payload, user["id"]
        )
    )
    return {"exchange": created}


@router.get("/finance/ledger/transactions")
async def list_ledger_transactions(
    agency_id: str,
    entry_type: Optional[str] = None,
    trip_id: Optional[str] = None,
    booking_id: Optional[str] = None,
    invoice_id: Optional[str] = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    membership = await get_membership(db, agency_id, user["id"])
    include_costs = "view_supplier_costs" in agency_permissions(
        membership.get("agency_role")
    )
    items = await CanonicalCommercialLedgerService(db).list_transactions(
        agency_id,
        include_costs=include_costs,
        entry_type=entry_type,
        trip_id=trip_id,
        booking_id=booking_id,
        invoice_id=invoice_id,
    )
    return {"items": items}


@router.get("/finance/reporting")
async def get_finance_reporting(
    agency_id: str,
    trip_id: Optional[str] = None,
    booking_id: Optional[str] = None,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    await require_read(db, agency_id, user)
    membership = await get_membership(db, agency_id, user["id"])
    include_costs = "view_supplier_costs" in agency_permissions(
        membership.get("agency_role")
    )
    return await CanonicalCommercialLedgerService(db).reporting(
        agency_id,
        include_costs=include_costs,
        trip_id=trip_id,
        booking_id=booking_id,
    )


@router.get("/finance/dashboard")
async def get_finance_dashboard(
    agency_id: str,
    user: dict = Depends(get_current_user),
    db: Database = Depends(get_database),
) -> dict:
    return await get_finance_reporting(
        agency_id=agency_id,
        user=user,
        db=db,
    )
