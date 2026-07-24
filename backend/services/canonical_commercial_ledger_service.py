from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from database import Database
from models import (
    AuditEvent,
    CommercialLedger,
    CommercialTransaction,
    CreditNote,
    CreditNoteCreate,
    CreditNoteLine,
    ExchangeLedgerEntry,
    ExchangeLedgerEntryCreate,
    Invoice,
    InvoiceCreate,
    InvoiceLineItem,
    InvoiceLineItemCreate,
    PaymentAllocation,
    PaymentAllocationCreate,
    PaymentRecord,
    PaymentRecordCreate,
    RefundLedgerEntry,
    RefundLedgerEntryCreate,
    SupplierCost,
    SupplierCostCreate,
    SupplierCostLine,
    SupplierCostLineCreate,
    new_id,
)
from persistence_query import PaginationRequest
from persistence_repository import PersistenceRepository


COMMERCIAL_LEDGERS_COLLECTION = "commercial_ledgers"
COMMERCIAL_TRANSACTIONS_COLLECTION = "commercial_transactions"
PAYMENT_ALLOCATIONS_COLLECTION = "payment_allocations"
SUPPLIER_COSTS_COLLECTION = "supplier_costs"
SUPPLIER_COST_LINES_COLLECTION = "supplier_cost_lines"
CREDIT_NOTES_COLLECTION = "credit_notes"
CREDIT_NOTE_LINES_COLLECTION = "credit_note_lines"
REFUND_LEDGER_ENTRIES_COLLECTION = "refund_ledger_entries"
EXCHANGE_LEDGER_ENTRIES_COLLECTION = "exchange_ledger_entries"

CANONICAL_FINANCE_COLLECTIONS = (
    COMMERCIAL_LEDGERS_COLLECTION,
    COMMERCIAL_TRANSACTIONS_COLLECTION,
    "invoices",
    "invoice_line_items",
    "payment_records",
    PAYMENT_ALLOCATIONS_COLLECTION,
    SUPPLIER_COSTS_COLLECTION,
    SUPPLIER_COST_LINES_COLLECTION,
    CREDIT_NOTES_COLLECTION,
    CREDIT_NOTE_LINES_COLLECTION,
    REFUND_LEDGER_ENTRIES_COLLECTION,
    EXCHANGE_LEDGER_ENTRIES_COLLECTION,
)

INVOICE_LIFECYCLE = (
    "draft",
    "issued",
    "partially_paid",
    "paid",
    "cancelled",
    "credited",
)
SUPPLIER_COST_STATUSES = ("draft", "confirmed", "paid", "cancelled")
REFUND_SOURCE_TYPES = ("ticket", "emd", "manual")

FINANCE_WRITER_CLASSIFICATION: dict[str, tuple[str, ...]] = {
    "canonical": ("backend/services/canonical_commercial_ledger_service.py",),
    "adapter": ("backend/routers/finance.py",),
    "projection": (
        "frontend/src/pages/agency/FinanceDashboardPage.jsx",
        "frontend/src/pages/agency/InvoicesPage.jsx",
        "frontend/src/pages/agency/PaymentsPage.jsx",
    ),
    "compatibility": (
        "backend/routers/refunds_exchanges.py",
        "backend/services/after_sales_workflow_service.py",
    ),
    "deprecated": ("backend/routers/bookings.py:financial summary fields",),
    "demo": ("backend/services/seed_service.py",),
}


class CommercialLedgerError(ValueError):
    def __init__(self, message: str, *, code: str = "COMMERCIAL_LEDGER_CONFLICT") -> None:
        self.code = code
        super().__init__(message)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def money(value: Any) -> float:
    try:
        return round(float(value or 0), 2)
    except (TypeError, ValueError) as exc:
        raise CommercialLedgerError(
            "Monetary value must be numeric.",
            code="INVALID_MONETARY_VALUE",
        ) from exc


def enum_value(value: Any) -> str:
    return str(getattr(value, "value", value))


def require_positive(value: Any, label: str) -> float:
    result = money(value)
    if result <= 0:
        raise CommercialLedgerError(
            f"{label} must be greater than zero.",
            code="INVALID_MONETARY_VALUE",
        )
    return result


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def reference(prefix: str) -> str:
    return f"{prefix}-{new_id().split('-')[0].upper()}"


class CanonicalCommercialLedgerService:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def _agency_records(
        self,
        collection_name: str,
        agency_id: str,
        filters: dict[str, Any] | None = None,
        *,
        maximum_records: int = 5000,
    ) -> list[dict[str, Any]]:
        repository = PersistenceRepository(self.db)
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
        raise CommercialLedgerError(
            f"{collection_name} exceeds the bounded accounting query limit.",
            code="LEDGER_QUERY_LIMIT_EXCEEDED",
        )

    async def _audit(
        self,
        *,
        agency_id: str,
        actor_user_id: str | None,
        event_type: str,
        entity_type: str,
        entity_id: str,
        summary: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        event = AuditEvent(
            agency_id=agency_id,
            actor_user_id=actor_user_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            summary=summary,
            metadata={
                **(metadata or {}),
                "canonical_commercial_ledger": True,
                "payment_execution_performed": False,
                "operational_record_mutated": False,
            },
        )
        await self.db.collection("audit_events").insert_one(
            event.model_dump(mode="json")
        )

    async def _agency_record(
        self,
        collection_name: str,
        agency_id: str,
        record_id: str | None,
        label: str,
    ) -> dict[str, Any] | None:
        if not record_id:
            return None
        record = await self.db.collection(collection_name).find_one(
            {"agency_id": agency_id, "id": record_id}
        )
        if not record:
            raise CommercialLedgerError(
                f"{label} was not found in this Agency.",
                code="INVALID_LINEAGE",
            )
        return record

    async def _record_from_candidates(
        self,
        collection_names: tuple[str, ...],
        agency_id: str,
        record_id: str | None,
        label: str,
    ) -> dict[str, Any] | None:
        if not record_id:
            return None
        for collection_name in collection_names:
            record = await self.db.collection(collection_name).find_one(
                {"agency_id": agency_id, "id": record_id}
            )
            if record:
                return record
        raise CommercialLedgerError(
            f"{label} was not found in this Agency.",
            code="INVALID_LINEAGE",
        )

    @staticmethod
    def _assert_context(
        record: dict[str, Any] | None,
        *,
        client_id: str | None = None,
        trip_id: str | None = None,
        booking_id: str | None = None,
        label: str,
    ) -> None:
        if not record:
            return
        checks = (
            ("client_id", client_id),
            ("trip_id", trip_id),
            ("booking_id", booking_id),
            ("booking_record_id", booking_id),
        )
        for field, expected in checks:
            actual = record.get(field)
            if actual and expected and actual != expected:
                raise CommercialLedgerError(
                    f"{label} does not match the selected commercial context.",
                    code="CONTEXT_MISMATCH",
                )

    async def validate_lineage(
        self,
        *,
        agency_id: str,
        client_id: str | None = None,
        trip_id: str | None = None,
        booking_id: str | None = None,
        booking_workspace_id: str | None = None,
        ticket_id: str | None = None,
        emd_id: str | None = None,
        accepted_offer_snapshot_id: str | None = None,
        offer_id: str | None = None,
        service_id: str | None = None,
        supplier_cost_id: str | None = None,
    ) -> dict[str, Any]:
        client = await self._agency_record(
            "client_profiles", agency_id, client_id, "Client"
        )
        trip = await self._record_from_candidates(
            ("trip_dossiers", "trip_workspaces"),
            agency_id,
            trip_id,
            "Trip",
        )
        booking = await self._record_from_candidates(
            ("booking_records", "bookings"),
            agency_id,
            booking_id,
            "Booking",
        )
        workspace = await self._agency_record(
            "booking_workspaces",
            agency_id,
            booking_workspace_id,
            "Booking workspace",
        )
        ticket = await self._record_from_candidates(
            ("ticket_records", "ticket_workspaces"),
            agency_id,
            ticket_id,
            "Ticket",
        )
        emd = await self._record_from_candidates(
            ("emd_records", "emd_workspaces"),
            agency_id,
            emd_id,
            "EMD",
        )
        snapshot = await self._agency_record(
            "trip_accepted_offer_snapshots",
            agency_id,
            accepted_offer_snapshot_id,
            "Accepted offer snapshot",
        )
        offer = await self._record_from_candidates(
            ("offer_workspaces", "offers", "offer_workspaces_v2"),
            agency_id,
            offer_id,
            "Offer",
        )
        service = await self._record_from_candidates(
            (
                "passenger_service_requests",
                "ssr_osi_workspaces",
                "requested_services",
            ),
            agency_id,
            service_id,
            "Passenger service",
        )
        supplier_cost = await self._agency_record(
            SUPPLIER_COSTS_COLLECTION,
            agency_id,
            supplier_cost_id,
            "Supplier cost",
        )
        for label, record in (
            ("Trip", trip),
            ("Booking", booking),
            ("Booking workspace", workspace),
            ("Ticket", ticket),
            ("EMD", emd),
            ("Accepted offer snapshot", snapshot),
            ("Offer", offer),
            ("Passenger service", service),
            ("Supplier cost", supplier_cost),
        ):
            self._assert_context(
                record,
                client_id=client_id,
                trip_id=trip_id,
                booking_id=booking_id,
                label=label,
            )
        return {
            "client": client,
            "trip": trip,
            "booking": booking,
            "booking_workspace": workspace,
            "ticket": ticket,
            "emd": emd,
            "accepted_offer_snapshot": snapshot,
            "offer": offer,
            "passenger_service": service,
            "supplier_cost": supplier_cost,
        }

    async def validate_accepted_change(
        self,
        *,
        agency_id: str,
        accepted_change_id: str,
        client_id: str | None,
        trip_id: str,
        booking_id: str,
    ) -> dict[str, Any]:
        decision = await self.db.collection("after_sales_decisions").find_one(
            {"agency_id": agency_id, "id": accepted_change_id}
        )
        if decision:
            if decision.get("decision_status") != "approved":
                raise CommercialLedgerError(
                    "The referenced after-sales decision is not approved.",
                    code="CHANGE_NOT_ACCEPTED",
                )
            case = await self._agency_record(
                "after_sales_cases",
                agency_id,
                decision.get("case_id"),
                "After-sales case",
            )
            self._assert_context(
                case,
                client_id=client_id,
                trip_id=trip_id,
                booking_id=booking_id,
                label="Accepted after-sales decision",
            )
            return decision

        for collection_name in (
            "ticket_exchange_operations",
            "emd_exchange_operations",
        ):
            operation = await self.db.collection(collection_name).find_one(
                {"agency_id": agency_id, "id": accepted_change_id}
            )
            if not operation:
                continue
            if operation.get("status") not in {"accepted", "mirrored", "completed"}:
                raise CommercialLedgerError(
                    "The referenced exchange operation is not accepted.",
                    code="CHANGE_NOT_ACCEPTED",
                )
            self._assert_context(
                operation,
                client_id=client_id,
                trip_id=trip_id,
                booking_id=booking_id,
                label="Accepted exchange operation",
            )
            return operation

        raise CommercialLedgerError(
            "Accepted change evidence was not found in this Agency.",
            code="INVALID_LINEAGE",
        )

    async def ensure_ledger(
        self,
        agency_id: str,
        currency: str,
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        normalized = str(currency or "").strip().upper()
        if len(normalized) != 3:
            raise CommercialLedgerError(
                "Currency must be a three-letter code.",
                code="INVALID_CURRENCY",
            )
        existing = await self.db.collection(COMMERCIAL_LEDGERS_COLLECTION).find_one(
            {"agency_id": agency_id, "currency": normalized, "status": "active"}
        )
        if existing:
            return existing
        ledger = CommercialLedger(
            agency_id=agency_id,
            ledger_code=f"LEDGER-{normalized}",
            currency=normalized,
            created_by_user_id=actor_user_id,
        )
        created = await self.db.collection(COMMERCIAL_LEDGERS_COLLECTION).insert_one(
            ledger.model_dump(mode="json")
        )
        await self._audit(
            agency_id=agency_id,
            actor_user_id=actor_user_id,
            event_type="commercial_ledger.created",
            entity_type="commercial_ledger",
            entity_id=created["id"],
            summary=f"Created {normalized} commercial ledger.",
        )
        return created

    async def post_transaction(
        self,
        *,
        agency_id: str,
        currency: str,
        entry_type: str,
        reporting_category: str,
        direction: str,
        amount: float,
        source_event_type: str,
        source_event_id: str,
        idempotency_key: str,
        actor_user_id: str | None,
        immutable_source: dict[str, Any],
        references: dict[str, Any] | None = None,
        allow_zero: bool = False,
    ) -> dict[str, Any]:
        normalized_amount = money(amount)
        if normalized_amount < 0 or (normalized_amount == 0 and not allow_zero):
            raise CommercialLedgerError(
                "Ledger transaction amount must be positive.",
                code="INVALID_MONETARY_VALUE",
            )
        key = str(idempotency_key or "").strip()
        if not key:
            raise CommercialLedgerError(
                "Ledger transaction idempotency key is required.",
                code="IDEMPOTENCY_REQUIRED",
            )
        source_hash = canonical_hash(immutable_source)
        existing = await self.db.collection(
            COMMERCIAL_TRANSACTIONS_COLLECTION
        ).find_one({"agency_id": agency_id, "idempotency_key": key})
        if existing:
            if existing.get("immutable_source_hash") != source_hash:
                raise CommercialLedgerError(
                    "Idempotency key already refers to different source evidence.",
                    code="IDEMPOTENCY_CONFLICT",
                )
            return existing
        ledger = await self.ensure_ledger(agency_id, currency, actor_user_id)
        sign = -1 if direction in {"decrease", "outflow", "credit"} else 1
        transaction = CommercialTransaction(
            agency_id=agency_id,
            ledger_id=ledger["id"],
            entry_type=entry_type,
            reporting_category=reporting_category,
            direction=direction,
            amount=normalized_amount,
            signed_amount=money(sign * normalized_amount),
            currency=ledger["currency"],
            source_event_type=source_event_type,
            source_event_id=source_event_id,
            created_by_user_id=actor_user_id,
            idempotency_key=key,
            immutable_source_hash=source_hash,
            immutable_source_json=immutable_source,
            **(references or {}),
        )
        created = await self.db.collection(
            COMMERCIAL_TRANSACTIONS_COLLECTION
        ).insert_one(transaction.model_dump(mode="json"))
        await self._audit(
            agency_id=agency_id,
            actor_user_id=actor_user_id,
            event_type=f"commercial_transaction.{entry_type}",
            entity_type="commercial_transaction",
            entity_id=created["id"],
            summary=f"Posted {entry_type.replace('_', ' ')} transaction.",
            metadata={
                "source_event_type": source_event_type,
                "source_event_id": source_event_id,
                "immutable_source_hash": source_hash,
            },
        )
        return created

    async def create_invoice(
        self,
        agency_id: str,
        payload: InvoiceCreate,
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        if enum_value(payload.status) != "draft":
            raise CommercialLedgerError(
                "New invoices must start in draft.",
                code="INVALID_INVOICE_LIFECYCLE",
            )
        lineage = await self.validate_lineage(
            agency_id=agency_id,
            client_id=payload.client_id,
            trip_id=payload.trip_id,
            booking_id=payload.booking_record_id or payload.booking_id,
            booking_workspace_id=payload.booking_workspace_id,
            accepted_offer_snapshot_id=payload.accepted_offer_snapshot_id,
            offer_id=payload.offer_id,
        )
        ledger = await self.ensure_ledger(
            agency_id, payload.currency, actor_user_id
        )
        source_snapshot = {
            "client_id": payload.client_id,
            "trip_id": payload.trip_id,
            "booking_id": payload.booking_record_id or payload.booking_id,
            "booking_workspace_id": payload.booking_workspace_id,
            "offer_id": payload.offer_id,
            "accepted_offer_snapshot_id": payload.accepted_offer_snapshot_id,
            "lineage": {
                key: value.get("id") if value else None
                for key, value in lineage.items()
            },
        }
        invoice = Invoice(
            agency_id=agency_id,
            ledger_id=ledger["id"],
            invoice_number=payload.invoice_number or reference("INV"),
            created_by_user_id=actor_user_id,
            source_snapshot_hash=canonical_hash(source_snapshot),
            source_snapshot_json=source_snapshot,
            **payload.model_dump(exclude={"invoice_number"}, mode="json"),
        )
        created = await self.db.collection("invoices").insert_one(
            invoice.model_dump(mode="json")
        )
        await self.post_transaction(
            agency_id=agency_id,
            currency=invoice.currency,
            entry_type="invoice_created",
            reporting_category="invoice_draft",
            direction="increase",
            amount=0,
            source_event_type="invoice.created",
            source_event_id=created["id"],
            idempotency_key=f"invoice:{created['id']}:created",
            actor_user_id=actor_user_id,
            immutable_source=created,
            references={
                "client_id": invoice.client_id,
                "trip_id": invoice.trip_id,
                "booking_id": invoice.booking_record_id or invoice.booking_id,
                "booking_workspace_id": invoice.booking_workspace_id,
                "accepted_offer_snapshot_id": invoice.accepted_offer_snapshot_id,
                "invoice_id": created["id"],
            },
            allow_zero=True,
        )
        await self._audit(
            agency_id=agency_id,
            actor_user_id=actor_user_id,
            event_type="invoice.created",
            entity_type="invoice",
            entity_id=created["id"],
            summary=f"Created draft invoice {created['invoice_number']}.",
        )
        return created

    async def get_invoice(
        self, agency_id: str, invoice_id: str
    ) -> dict[str, Any]:
        invoice = await self.db.collection("invoices").find_one(
            {"agency_id": agency_id, "id": invoice_id}
        )
        if not invoice:
            raise CommercialLedgerError(
                "Invoice not found.",
                code="INVOICE_NOT_FOUND",
            )
        return invoice

    async def add_invoice_line(
        self,
        agency_id: str,
        invoice_id: str,
        payload: InvoiceLineItemCreate,
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        invoice = await self.get_invoice(agency_id, invoice_id)
        if invoice.get("status") != "draft":
            raise CommercialLedgerError(
                "Only draft invoices can be edited. Use a credit note after issue.",
                code="INVOICE_IMMUTABLE_AFTER_ISSUE",
            )
        if str(payload.currency).upper() != invoice["currency"]:
            raise CommercialLedgerError(
                "Invoice line currency must match the invoice.",
                code="CURRENCY_MISMATCH",
            )
        await self.validate_lineage(
            agency_id=agency_id,
            client_id=invoice["client_id"],
            trip_id=payload.trip_id or invoice.get("trip_id"),
            booking_id=payload.booking_record_id
            or payload.booking_id
            or invoice.get("booking_record_id")
            or invoice.get("booking_id"),
            ticket_id=payload.ticket_id,
            emd_id=payload.emd_id,
            service_id=payload.service_id,
            supplier_cost_id=payload.supplier_cost_id,
        )
        quantity = require_positive(payload.quantity, "Quantity")
        unit_amount = money(payload.unit_amount)
        line_type = enum_value(payload.line_type)
        if line_type not in {"discount", "adjustment"} and unit_amount < 0:
            raise CommercialLedgerError(
                "Negative amounts require a discount or adjustment line.",
                code="INVALID_INVOICE_LINE",
            )
        derived_total = money(quantity * unit_amount)
        if line_type == "discount":
            derived_total = -abs(derived_total)
        if (
            payload.total_amount is not None
            and money(payload.total_amount) != derived_total
        ):
            raise CommercialLedgerError(
                "Invoice line total is server-derived from quantity and unit amount.",
                code="DERIVED_TOTAL_MISMATCH",
            )
        line = InvoiceLineItem(
            agency_id=agency_id,
            invoice_id=invoice_id,
            trip_id=payload.trip_id or invoice.get("trip_id"),
            booking_id=payload.booking_id or invoice.get("booking_id"),
            booking_record_id=payload.booking_record_id
            or invoice.get("booking_record_id"),
            total_amount=derived_total,
            **payload.model_dump(
                exclude={
                    "trip_id",
                    "booking_id",
                    "booking_record_id",
                    "total_amount",
                },
                mode="json",
            ),
        )
        created = await self.db.collection("invoice_line_items").insert_one(
            line.model_dump(mode="json")
        )
        await self.recalculate_invoice(agency_id, invoice_id)
        await self._audit(
            agency_id=agency_id,
            actor_user_id=actor_user_id,
            event_type="invoice.line_added",
            entity_type="invoice_line_item",
            entity_id=created["id"],
            summary=f"Added invoice line to {invoice['invoice_number']}.",
            metadata={"invoice_id": invoice_id, "derived_total": derived_total},
        )
        return created

    async def update_invoice_line(
        self,
        agency_id: str,
        invoice_id: str,
        line_id: str,
        updates: dict[str, Any],
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        invoice = await self.get_invoice(agency_id, invoice_id)
        if invoice.get("status") != "draft":
            raise CommercialLedgerError(
                "Issued invoice lines are immutable.",
                code="INVOICE_IMMUTABLE_AFTER_ISSUE",
            )
        current = await self.db.collection("invoice_line_items").find_one(
            {"agency_id": agency_id, "invoice_id": invoice_id, "id": line_id}
        )
        if not current:
            raise CommercialLedgerError(
                "Invoice line not found.",
                code="INVOICE_LINE_NOT_FOUND",
            )
        proposed_trip_id = updates.get(
            "trip_id", current.get("trip_id") or invoice.get("trip_id")
        )
        proposed_booking_id = (
            updates.get("booking_record_id")
            or updates.get("booking_id")
            or current.get("booking_record_id")
            or current.get("booking_id")
            or invoice.get("booking_record_id")
            or invoice.get("booking_id")
        )
        await self.validate_lineage(
            agency_id=agency_id,
            client_id=invoice["client_id"],
            trip_id=proposed_trip_id,
            booking_id=proposed_booking_id,
            ticket_id=updates.get("ticket_id", current.get("ticket_id")),
            emd_id=updates.get("emd_id", current.get("emd_id")),
            service_id=updates.get("service_id", current.get("service_id")),
            supplier_cost_id=updates.get(
                "supplier_cost_id", current.get("supplier_cost_id")
            ),
        )
        updates.pop("total_amount", None)
        updates.pop("currency", None)
        quantity = require_positive(
            updates.get("quantity", current.get("quantity")), "Quantity"
        )
        unit_amount = money(updates.get("unit_amount", current.get("unit_amount")))
        line_type = enum_value(updates.get("line_type", current.get("line_type")))
        if line_type not in {"discount", "adjustment"} and unit_amount < 0:
            raise CommercialLedgerError(
                "Negative amounts require a discount or adjustment line.",
                code="INVALID_INVOICE_LINE",
            )
        total = money(quantity * unit_amount)
        if line_type == "discount":
            total = -abs(total)
        updates.update(
            {
                "quantity": quantity,
                "unit_amount": unit_amount,
                "total_amount": total,
            }
        )
        updated = await self.db.collection("invoice_line_items").update_one(
            {"agency_id": agency_id, "invoice_id": invoice_id, "id": line_id},
            updates,
        )
        await self.recalculate_invoice(agency_id, invoice_id)
        await self._audit(
            agency_id=agency_id,
            actor_user_id=actor_user_id,
            event_type="invoice.line_updated",
            entity_type="invoice_line_item",
            entity_id=line_id,
            summary=f"Updated draft invoice line on {invoice['invoice_number']}.",
            metadata={"derived_total": total},
        )
        return updated or current

    async def archive_invoice_line(
        self,
        agency_id: str,
        invoice_id: str,
        line_id: str,
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        invoice = await self.get_invoice(agency_id, invoice_id)
        if invoice.get("status") != "draft":
            raise CommercialLedgerError(
                "Issued invoice lines are immutable.",
                code="INVOICE_IMMUTABLE_AFTER_ISSUE",
            )
        updated = await self.db.collection("invoice_line_items").update_one(
            {
                "agency_id": agency_id,
                "invoice_id": invoice_id,
                "id": line_id,
                "status": "active",
            },
            {"status": "archived"},
        )
        if not updated:
            raise CommercialLedgerError(
                "Invoice line not found.",
                code="INVOICE_LINE_NOT_FOUND",
            )
        await self.recalculate_invoice(agency_id, invoice_id)
        await self._audit(
            agency_id=agency_id,
            actor_user_id=actor_user_id,
            event_type="invoice.line_archived",
            entity_type="invoice_line_item",
            entity_id=line_id,
            summary=f"Archived draft invoice line on {invoice['invoice_number']}.",
        )
        return updated

    async def recalculate_payment(
        self, agency_id: str, payment_id: str
    ) -> dict[str, Any]:
        payment = await self.db.collection("payment_records").find_one(
            {"agency_id": agency_id, "id": payment_id}
        )
        if not payment:
            raise CommercialLedgerError(
                "Payment record not found.",
                code="PAYMENT_NOT_FOUND",
            )
        allocations = await self._agency_records(
            PAYMENT_ALLOCATIONS_COLLECTION,
            agency_id,
            {"payment_record_id": payment_id, "status": "posted"},
        )
        allocated = money(sum(money(item.get("amount")) for item in allocations))
        updated = await self.db.collection("payment_records").update_one(
            {"agency_id": agency_id, "id": payment_id},
            {
                "allocated_amount": allocated,
                "unallocated_amount": money(payment.get("amount") - allocated),
            },
        )
        return updated or payment

    async def recalculate_invoice(
        self, agency_id: str, invoice_id: str
    ) -> dict[str, Any]:
        invoice = await self.get_invoice(agency_id, invoice_id)
        lines = await self._agency_records(
            "invoice_line_items",
            agency_id,
            {"invoice_id": invoice_id, "status": "active"},
        )
        allocations = await self._agency_records(
            PAYMENT_ALLOCATIONS_COLLECTION,
            agency_id,
            {"invoice_id": invoice_id, "status": "posted"},
        )
        credits = await self._agency_records(
            CREDIT_NOTES_COLLECTION,
            agency_id,
            {"invoice_id": invoice_id, "status": "issued"},
        )
        subtotal = money(sum(money(item.get("total_amount")) for item in lines))
        tax = money(
            sum(
                money(item.get("total_amount"))
                for item in lines
                if item.get("line_type") in {"tax", "taxes"}
            )
        )
        credited = money(sum(money(item.get("total_amount")) for item in credits))
        payable = max(money(subtotal - credited), 0)
        paid = money(sum(money(item.get("amount")) for item in allocations))
        due = max(money(payable - paid), 0)
        status_value = invoice.get("status") or "draft"
        paid_at = invoice.get("paid_at")
        credited_at = invoice.get("credited_at")
        if status_value not in {"draft", "cancelled"}:
            if subtotal > 0 and credited >= subtotal:
                status_value = "credited"
                credited_at = credited_at or now_utc()
                paid_at = None
            elif due <= 0 and payable > 0:
                status_value = "paid"
                paid_at = paid_at or now_utc()
            elif paid > 0:
                status_value = "partially_paid"
                paid_at = None
            else:
                status_value = "issued"
                paid_at = None
        updated = await self.db.collection("invoices").update_one(
            {"agency_id": agency_id, "id": invoice_id},
            {
                "subtotal_amount": subtotal,
                "tax_amount": tax,
                "total_amount": subtotal,
                "credited_amount": credited,
                "payable_amount": payable,
                "paid_amount": paid,
                "due_amount": due,
                "status": status_value,
                "paid_at": paid_at,
                "credited_at": credited_at,
            },
        )
        return updated or invoice

    async def update_invoice_metadata(
        self,
        agency_id: str,
        invoice_id: str,
        updates: dict[str, Any],
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        invoice = await self.get_invoice(agency_id, invoice_id)
        allowed = {
            "issue_date",
            "due_date",
            "client_visible_notes",
            "internal_notes",
        }
        if set(updates) - allowed:
            raise CommercialLedgerError(
                "Invoice financial state and totals are server-controlled.",
                code="PROTECTED_INVOICE_FIELDS",
            )
        updated = await self.db.collection("invoices").update_one(
            {"agency_id": agency_id, "id": invoice_id},
            {**updates, "updated_by_user_id": actor_user_id},
        )
        await self._audit(
            agency_id=agency_id,
            actor_user_id=actor_user_id,
            event_type="invoice.metadata_updated",
            entity_type="invoice",
            entity_id=invoice_id,
            summary=f"Updated invoice metadata for {invoice['invoice_number']}.",
        )
        return updated or invoice

    async def issue_invoice(
        self,
        agency_id: str,
        invoice_id: str,
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        invoice = await self.recalculate_invoice(agency_id, invoice_id)
        if invoice.get("status") != "draft":
            raise CommercialLedgerError(
                "Only a draft invoice can be issued.",
                code="INVALID_INVOICE_LIFECYCLE",
            )
        if money(invoice.get("total_amount")) <= 0:
            raise CommercialLedgerError(
                "Invoice requires a positive server-derived total before issue.",
                code="EMPTY_INVOICE",
            )
        issued_at = now_utc()
        updated = await self.db.collection("invoices").update_one(
            {"agency_id": agency_id, "id": invoice_id},
            {
                "status": "issued",
                "issued_at": issued_at,
                "issue_date": invoice.get("issue_date") or issued_at.date(),
                "updated_by_user_id": actor_user_id,
            },
        )
        await self.post_transaction(
            agency_id=agency_id,
            currency=invoice["currency"],
            entry_type="invoice_adjusted",
            reporting_category="client_revenue",
            direction="increase",
            amount=invoice["total_amount"],
            source_event_type="invoice.issued",
            source_event_id=invoice_id,
            idempotency_key=f"invoice:{invoice_id}:issued",
            actor_user_id=actor_user_id,
            immutable_source={
                "invoice": updated,
                "lines": await self._agency_records(
                    "invoice_line_items",
                    agency_id,
                    {"invoice_id": invoice_id, "status": "active"},
                ),
            },
            references={
                "client_id": invoice.get("client_id"),
                "trip_id": invoice.get("trip_id"),
                "booking_id": invoice.get("booking_record_id")
                or invoice.get("booking_id"),
                "booking_workspace_id": invoice.get("booking_workspace_id"),
                "accepted_offer_snapshot_id": invoice.get(
                    "accepted_offer_snapshot_id"
                ),
                "invoice_id": invoice_id,
            },
        )
        await self._audit(
            agency_id=agency_id,
            actor_user_id=actor_user_id,
            event_type="invoice.issued",
            entity_type="invoice",
            entity_id=invoice_id,
            summary=f"Issued invoice {invoice['invoice_number']}.",
        )
        return updated or invoice

    async def cancel_invoice(
        self,
        agency_id: str,
        invoice_id: str,
        actor_user_id: str | None,
        reason: str,
    ) -> dict[str, Any]:
        invoice = await self.recalculate_invoice(agency_id, invoice_id)
        if invoice.get("status") not in {"draft", "issued"}:
            raise CommercialLedgerError(
                "Only an unpaid draft or issued invoice can be cancelled.",
                code="INVALID_INVOICE_LIFECYCLE",
            )
        if money(invoice.get("paid_amount")) > 0:
            raise CommercialLedgerError(
                "An invoice with allocations requires a credit or refund record.",
                code="INVOICE_HAS_ALLOCATIONS",
            )
        cancelled_at = now_utc()
        updated = await self.db.collection("invoices").update_one(
            {"agency_id": agency_id, "id": invoice_id},
            {
                "status": "cancelled",
                "cancelled_at": cancelled_at,
                "updated_by_user_id": actor_user_id,
            },
        )
        if invoice.get("status") == "issued":
            await self.post_transaction(
                agency_id=agency_id,
                currency=invoice["currency"],
                entry_type="invoice_adjusted",
                reporting_category="client_revenue",
                direction="decrease",
                amount=invoice["total_amount"],
                source_event_type="invoice.cancelled",
                source_event_id=invoice_id,
                idempotency_key=f"invoice:{invoice_id}:cancelled",
                actor_user_id=actor_user_id,
                immutable_source={"invoice": invoice, "reason": reason},
                references={
                    "client_id": invoice.get("client_id"),
                    "trip_id": invoice.get("trip_id"),
                    "booking_id": invoice.get("booking_record_id")
                    or invoice.get("booking_id"),
                    "invoice_id": invoice_id,
                },
            )
        await self._audit(
            agency_id=agency_id,
            actor_user_id=actor_user_id,
            event_type="invoice.cancelled",
            entity_type="invoice",
            entity_id=invoice_id,
            summary=f"Cancelled invoice {invoice['invoice_number']}.",
            metadata={"reason": reason},
        )
        return updated or invoice

    async def create_payment(
        self,
        agency_id: str,
        payload: PaymentRecordCreate,
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        amount = require_positive(payload.amount, "Payment amount")
        source_snapshot = payload.model_dump(mode="json")
        source_hash = canonical_hash(source_snapshot)
        key = payload.idempotency_key or canonical_hash(
            {
                "agency_id": agency_id,
                "client_id": payload.client_id,
                "invoice_id": payload.invoice_id,
                "amount": amount,
                "currency": payload.currency.upper(),
                "external_reference": payload.external_reference,
            }
        )
        existing = await self.db.collection("payment_records").find_one(
            {"agency_id": agency_id, "idempotency_key": key}
        )
        if existing:
            if existing.get("source_snapshot_hash") != source_hash:
                raise CommercialLedgerError(
                    "Payment idempotency key already refers to different evidence.",
                    code="IDEMPOTENCY_CONFLICT",
                )
            return existing
        invoice = (
            await self.get_invoice(agency_id, payload.invoice_id)
            if payload.invoice_id
            else None
        )
        if invoice:
            if invoice["client_id"] != payload.client_id:
                raise CommercialLedgerError(
                    "Payment client must match the invoice.",
                    code="CONTEXT_MISMATCH",
                )
            if invoice["currency"] != payload.currency.upper():
                raise CommercialLedgerError(
                    "Payment currency must match the invoice.",
                    code="CURRENCY_MISMATCH",
                )
            if (
                enum_value(payload.status) == "received"
                and invoice.get("status") not in {"issued", "partially_paid"}
            ):
                raise CommercialLedgerError(
                    "Received payments can only be allocated to an issued invoice.",
                    code="INVALID_INVOICE_LIFECYCLE",
                )
            if (
                enum_value(payload.status) == "received"
                and amount > money(invoice.get("due_amount"))
            ):
                raise CommercialLedgerError(
                    "Linked payment exceeds the invoice balance.",
                    code="OVERALLOCATION",
                )
        await self.validate_lineage(
            agency_id=agency_id,
            client_id=payload.client_id,
            trip_id=payload.trip_id or (invoice or {}).get("trip_id"),
            booking_id=payload.booking_id
            or (invoice or {}).get("booking_record_id")
            or (invoice or {}).get("booking_id"),
        )
        ledger = await self.ensure_ledger(
            agency_id, payload.currency, actor_user_id
        )
        payment = PaymentRecord(
            agency_id=agency_id,
            ledger_id=ledger["id"],
            amount=amount,
            allocated_amount=0,
            unallocated_amount=amount,
            idempotency_key=key,
            received_by_user_id=actor_user_id
            if enum_value(payload.status) == "received"
            else None,
            source_snapshot_hash=source_hash,
            **payload.model_dump(
                exclude={"amount", "idempotency_key"}, mode="json"
            ),
        )
        created = await self.db.collection("payment_records").insert_one(
            payment.model_dump(mode="json")
        )
        if created.get("status") == "received":
            created = await self._post_payment_received(
                agency_id, created, actor_user_id
            )
            if invoice:
                await self.allocate_payment(
                    agency_id,
                    created["id"],
                    PaymentAllocationCreate(
                        invoice_id=invoice["id"],
                        amount=amount,
                        idempotency_key=f"payment:{created['id']}:invoice:{invoice['id']}",
                        reason="Compatibility auto-allocation from linked invoice.",
                    ),
                    actor_user_id,
                )
                created = await self.recalculate_payment(agency_id, created["id"])
        await self._audit(
            agency_id=agency_id,
            actor_user_id=actor_user_id,
            event_type="payment.created",
            entity_type="payment_record",
            entity_id=created["id"],
            summary="Recorded manual payment evidence.",
        )
        return created

    async def _post_payment_received(
        self,
        agency_id: str,
        payment: dict[str, Any],
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        received_at = payment.get("received_at") or now_utc()
        updated = await self.db.collection("payment_records").update_one(
            {"agency_id": agency_id, "id": payment["id"]},
            {
                "status": "received",
                "received_at": received_at,
                "received_by_user_id": actor_user_id,
            },
        )
        payment = updated or payment
        await self.post_transaction(
            agency_id=agency_id,
            currency=payment["currency"],
            entry_type="payment_received",
            reporting_category="payment_received",
            direction="increase",
            amount=payment["amount"],
            source_event_type="payment.received",
            source_event_id=payment["id"],
            idempotency_key=f"payment:{payment['id']}:received",
            actor_user_id=actor_user_id,
            immutable_source=payment,
            references={
                "client_id": payment.get("client_id"),
                "trip_id": payment.get("trip_id"),
                "booking_id": payment.get("booking_id"),
                "invoice_id": payment.get("invoice_id"),
                "payment_record_id": payment["id"],
            },
        )
        return payment

    async def mark_payment_received(
        self,
        agency_id: str,
        payment_id: str,
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        payment = await self.db.collection("payment_records").find_one(
            {"agency_id": agency_id, "id": payment_id}
        )
        if not payment:
            raise CommercialLedgerError(
                "Payment record not found.",
                code="PAYMENT_NOT_FOUND",
            )
        if payment.get("status") == "received":
            return payment
        if payment.get("status") not in {"pending", "failed"}:
            raise CommercialLedgerError(
                "Payment cannot move to received from its current state.",
                code="INVALID_PAYMENT_LIFECYCLE",
            )
        invoice = None
        if payment.get("invoice_id"):
            invoice = await self.recalculate_invoice(
                agency_id, payment["invoice_id"]
            )
            if invoice.get("status") not in {"issued", "partially_paid"}:
                raise CommercialLedgerError(
                    "Received payments can only be allocated to an issued invoice.",
                    code="INVALID_INVOICE_LIFECYCLE",
                )
            if money(payment["amount"]) > money(invoice["due_amount"]):
                raise CommercialLedgerError(
                    "Linked payment exceeds the invoice balance.",
                    code="OVERALLOCATION",
                )
        payment = await self._post_payment_received(
            agency_id, payment, actor_user_id
        )
        if invoice:
            await self.allocate_payment(
                agency_id,
                payment_id,
                PaymentAllocationCreate(
                    invoice_id=invoice["id"],
                    amount=payment["amount"],
                    idempotency_key=f"payment:{payment_id}:invoice:{invoice['id']}",
                    reason="Compatibility auto-allocation from linked invoice.",
                ),
                actor_user_id,
            )
        await self._audit(
            agency_id=agency_id,
            actor_user_id=actor_user_id,
            event_type="payment.received",
            entity_type="payment_record",
            entity_id=payment_id,
            summary="Marked manual payment evidence as received.",
        )
        return await self.recalculate_payment(agency_id, payment_id)

    async def update_payment_metadata(
        self,
        agency_id: str,
        payment_id: str,
        updates: dict[str, Any],
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        payment = await self.db.collection("payment_records").find_one(
            {"agency_id": agency_id, "id": payment_id}
        )
        if not payment:
            raise CommercialLedgerError(
                "Payment record not found.",
                code="PAYMENT_NOT_FOUND",
            )
        allowed = {
            "method",
            "external_reference",
            "reconciliation_status",
            "reconciliation_notes",
            "internal_notes",
        }
        if set(updates) - allowed:
            raise CommercialLedgerError(
                "Payment amount, currency, client, invoice, and received evidence are immutable.",
                code="PROTECTED_PAYMENT_FIELDS",
            )
        updated = await self.db.collection("payment_records").update_one(
            {"agency_id": agency_id, "id": payment_id},
            updates,
        )
        await self._audit(
            agency_id=agency_id,
            actor_user_id=actor_user_id,
            event_type="payment.metadata_updated",
            entity_type="payment_record",
            entity_id=payment_id,
            summary="Updated payment reconciliation metadata.",
        )
        return updated or payment

    async def mark_payment_reconciled(
        self,
        agency_id: str,
        payment_id: str,
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        return await self.update_payment_metadata(
            agency_id,
            payment_id,
            {"reconciliation_status": "reconciled"},
            actor_user_id,
        )

    async def allocate_payment(
        self,
        agency_id: str,
        payment_id: str,
        payload: PaymentAllocationCreate,
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        payment = await self.db.collection("payment_records").find_one(
            {"agency_id": agency_id, "id": payment_id}
        )
        if not payment:
            raise CommercialLedgerError(
                "Payment record not found.",
                code="PAYMENT_NOT_FOUND",
            )
        if payment.get("status") != "received":
            raise CommercialLedgerError(
                "Only received payments can be allocated.",
                code="PAYMENT_NOT_RECEIVED",
            )
        invoice = await self.recalculate_invoice(agency_id, payload.invoice_id)
        if invoice.get("status") not in {"issued", "partially_paid"}:
            raise CommercialLedgerError(
                "Payments can only be allocated to an issued invoice with a balance.",
                code="INVALID_INVOICE_LIFECYCLE",
            )
        if invoice.get("client_id") != payment.get("client_id"):
            raise CommercialLedgerError(
                "Payment and invoice must belong to the same client.",
                code="CONTEXT_MISMATCH",
            )
        if invoice.get("currency") != payment.get("currency"):
            raise CommercialLedgerError(
                "Payment and invoice currencies must match.",
                code="CURRENCY_MISMATCH",
            )
        amount = require_positive(payload.amount, "Allocation amount")
        key = payload.idempotency_key or canonical_hash(
            {
                "payment_id": payment_id,
                "invoice_id": payload.invoice_id,
                "invoice_line_item_id": payload.invoice_line_item_id,
                "amount": amount,
            }
        )
        existing = await self.db.collection(PAYMENT_ALLOCATIONS_COLLECTION).find_one(
            {"agency_id": agency_id, "idempotency_key": key}
        )
        if existing:
            if (
                existing.get("payment_record_id") != payment_id
                or existing.get("invoice_id") != payload.invoice_id
                or money(existing.get("amount")) != amount
            ):
                raise CommercialLedgerError(
                    "Allocation idempotency key already refers to a different allocation.",
                    code="IDEMPOTENCY_CONFLICT",
                )
            return existing
        payment = await self.recalculate_payment(agency_id, payment_id)
        if amount > money(payment.get("unallocated_amount")):
            raise CommercialLedgerError(
                "Allocation exceeds the unallocated payment balance.",
                code="OVERALLOCATION",
            )
        if amount > money(invoice.get("due_amount")):
            raise CommercialLedgerError(
                "Allocation exceeds the invoice balance.",
                code="OVERALLOCATION",
            )
        if payload.invoice_line_item_id:
            line = await self.db.collection("invoice_line_items").find_one(
                {
                    "agency_id": agency_id,
                    "invoice_id": invoice["id"],
                    "id": payload.invoice_line_item_id,
                    "status": "active",
                }
            )
            if not line:
                raise CommercialLedgerError(
                    "Invoice line does not belong to the selected invoice.",
                    code="CONTEXT_MISMATCH",
                )
            if money(line.get("total_amount")) <= 0:
                raise CommercialLedgerError(
                    "Payments cannot be allocated to a discount or non-positive line.",
                    code="INVALID_ALLOCATION_TARGET",
                )
            line_allocations = await self._agency_records(
                PAYMENT_ALLOCATIONS_COLLECTION,
                agency_id,
                {"invoice_line_item_id": line["id"], "status": "posted"},
            )
            line_remaining = money(
                abs(money(line.get("total_amount")))
                - sum(money(item.get("amount")) for item in line_allocations)
            )
            if amount > line_remaining:
                raise CommercialLedgerError(
                    "Allocation exceeds the invoice line balance.",
                    code="OVERALLOCATION",
                )
        allocation = PaymentAllocation(
            agency_id=agency_id,
            ledger_id=payment["ledger_id"],
            payment_record_id=payment_id,
            invoice_id=invoice["id"],
            invoice_line_item_id=payload.invoice_line_item_id,
            amount=amount,
            currency=payment["currency"],
            idempotency_key=key,
            allocated_by_user_id=actor_user_id,
            reason=payload.reason,
        )
        created = await self.db.collection(PAYMENT_ALLOCATIONS_COLLECTION).insert_one(
            allocation.model_dump(mode="json")
        )
        await self.post_transaction(
            agency_id=agency_id,
            currency=payment["currency"],
            entry_type="payment_allocated",
            reporting_category="receivable",
            direction="decrease",
            amount=amount,
            source_event_type="payment.allocated",
            source_event_id=created["id"],
            idempotency_key=f"allocation:{created['id']}:posted",
            actor_user_id=actor_user_id,
            immutable_source=created,
            references={
                "client_id": invoice.get("client_id"),
                "trip_id": invoice.get("trip_id"),
                "booking_id": invoice.get("booking_record_id")
                or invoice.get("booking_id"),
                "invoice_id": invoice["id"],
                "invoice_line_item_id": payload.invoice_line_item_id,
                "payment_record_id": payment_id,
                "payment_allocation_id": created["id"],
            },
        )
        await self.recalculate_payment(agency_id, payment_id)
        await self.recalculate_invoice(agency_id, invoice["id"])
        await self._audit(
            agency_id=agency_id,
            actor_user_id=actor_user_id,
            event_type="payment.allocated",
            entity_type="payment_allocation",
            entity_id=created["id"],
            summary="Allocated received payment to invoice.",
            metadata={
                "payment_record_id": payment_id,
                "invoice_id": invoice["id"],
            },
        )
        return created

    async def create_supplier_cost(
        self,
        agency_id: str,
        payload: SupplierCostCreate,
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        expected = money(payload.expected_cost_amount)
        actual = money(payload.actual_cost_amount)
        if expected < 0 or actual < 0:
            raise CommercialLedgerError(
                "Supplier costs cannot be negative.",
                code="INVALID_MONETARY_VALUE",
            )
        if expected == 0 and actual == 0:
            raise CommercialLedgerError(
                "Supplier cost requires an expected or actual amount.",
                code="INVALID_MONETARY_VALUE",
            )
        await self.validate_lineage(
            agency_id=agency_id,
            client_id=payload.client_id,
            trip_id=payload.trip_id,
            booking_id=payload.booking_id,
            booking_workspace_id=payload.booking_workspace_id,
            ticket_id=payload.ticket_id,
            emd_id=payload.emd_id,
            service_id=payload.service_id,
        )
        ledger = await self.ensure_ledger(
            agency_id, payload.currency, actor_user_id
        )
        record = SupplierCost(
            agency_id=agency_id,
            ledger_id=ledger["id"],
            supplier_cost_reference=reference("COST"),
            expected_cost_amount=expected,
            actual_cost_amount=actual,
            currency=ledger["currency"],
            created_by_user_id=actor_user_id,
            **payload.model_dump(
                exclude={
                    "description",
                    "expected_cost_amount",
                    "actual_cost_amount",
                    "expense_category",
                    "currency",
                },
                mode="json",
            ),
        )
        created = await self.db.collection(SUPPLIER_COSTS_COLLECTION).insert_one(
            record.model_dump(mode="json")
        )
        line = SupplierCostLine(
            agency_id=agency_id,
            supplier_cost_id=created["id"],
            description=payload.description,
            expected_amount=expected,
            actual_amount=actual,
            currency=ledger["currency"],
            expense_category=payload.expense_category,
            ticket_id=payload.ticket_id,
            emd_id=payload.emd_id,
            service_id=payload.service_id,
        )
        await self.db.collection(SUPPLIER_COST_LINES_COLLECTION).insert_one(
            line.model_dump(mode="json")
        )
        await self._audit(
            agency_id=agency_id,
            actor_user_id=actor_user_id,
            event_type="supplier_cost.created",
            entity_type="supplier_cost",
            entity_id=created["id"],
            summary=f"Created supplier cost {created['supplier_cost_reference']}.",
        )
        return created

    async def add_supplier_cost_line(
        self,
        agency_id: str,
        supplier_cost_id: str,
        payload: SupplierCostLineCreate,
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        cost = await self.db.collection(SUPPLIER_COSTS_COLLECTION).find_one(
            {"agency_id": agency_id, "id": supplier_cost_id}
        )
        if not cost:
            raise CommercialLedgerError(
                "Supplier cost not found.",
                code="SUPPLIER_COST_NOT_FOUND",
            )
        if cost.get("status") != "draft":
            raise CommercialLedgerError(
                "Confirmed supplier costs are immutable.",
                code="SUPPLIER_COST_IMMUTABLE",
            )
        await self.validate_lineage(
            agency_id=agency_id,
            client_id=cost.get("client_id"),
            trip_id=cost.get("trip_id"),
            booking_id=cost.get("booking_id"),
            booking_workspace_id=cost.get("booking_workspace_id"),
            ticket_id=payload.ticket_id or cost.get("ticket_id"),
            emd_id=payload.emd_id or cost.get("emd_id"),
            service_id=payload.service_id or cost.get("service_id"),
        )
        currency = (payload.currency or cost["currency"]).upper()
        if currency != cost["currency"]:
            raise CommercialLedgerError(
                "Supplier cost line currency must match its parent.",
                code="CURRENCY_MISMATCH",
            )
        expected = money(payload.expected_amount)
        actual = money(payload.actual_amount)
        if expected < 0 or actual < 0:
            raise CommercialLedgerError(
                "Supplier cost amounts cannot be negative.",
                code="INVALID_MONETARY_VALUE",
            )
        line = SupplierCostLine(
            agency_id=agency_id,
            supplier_cost_id=supplier_cost_id,
            currency=currency,
            expected_amount=expected,
            actual_amount=actual,
            **payload.model_dump(
                exclude={"currency", "expected_amount", "actual_amount"},
                mode="json",
            ),
        )
        created = await self.db.collection(SUPPLIER_COST_LINES_COLLECTION).insert_one(
            line.model_dump(mode="json")
        )
        await self.recalculate_supplier_cost(agency_id, supplier_cost_id)
        await self._audit(
            agency_id=agency_id,
            actor_user_id=actor_user_id,
            event_type="supplier_cost.line_added",
            entity_type="supplier_cost_line",
            entity_id=created["id"],
            summary="Added supplier cost line.",
            metadata={"supplier_cost_id": supplier_cost_id},
        )
        return created

    async def recalculate_supplier_cost(
        self, agency_id: str, supplier_cost_id: str
    ) -> dict[str, Any]:
        cost = await self.db.collection(SUPPLIER_COSTS_COLLECTION).find_one(
            {"agency_id": agency_id, "id": supplier_cost_id}
        )
        if not cost:
            raise CommercialLedgerError(
                "Supplier cost not found.",
                code="SUPPLIER_COST_NOT_FOUND",
            )
        lines = await self._agency_records(
            SUPPLIER_COST_LINES_COLLECTION,
            agency_id,
            {"supplier_cost_id": supplier_cost_id, "status": "active"},
        )
        expected = money(sum(money(item.get("expected_amount")) for item in lines))
        actual = money(sum(money(item.get("actual_amount")) for item in lines))
        updated = await self.db.collection(SUPPLIER_COSTS_COLLECTION).update_one(
            {"agency_id": agency_id, "id": supplier_cost_id},
            {
                "expected_cost_amount": expected,
                "actual_cost_amount": actual,
            },
        )
        return updated or cost

    async def confirm_supplier_cost(
        self,
        agency_id: str,
        supplier_cost_id: str,
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        cost = await self.recalculate_supplier_cost(agency_id, supplier_cost_id)
        if cost.get("status") == "confirmed":
            return cost
        if cost.get("status") != "draft":
            raise CommercialLedgerError(
                "Only draft supplier costs can be confirmed.",
                code="INVALID_SUPPLIER_COST_LIFECYCLE",
            )
        posted = money(
            cost.get("actual_cost_amount") or cost.get("expected_cost_amount")
        )
        if posted <= 0:
            raise CommercialLedgerError(
                "Supplier cost requires a positive amount before confirmation.",
                code="INVALID_MONETARY_VALUE",
            )
        confirmed_at = now_utc()
        lines = await self._agency_records(
            SUPPLIER_COST_LINES_COLLECTION,
            agency_id,
            {"supplier_cost_id": supplier_cost_id, "status": "active"},
        )
        updated = await self.db.collection(SUPPLIER_COSTS_COLLECTION).update_one(
            {"agency_id": agency_id, "id": supplier_cost_id},
            {
                "status": "confirmed",
                "posted_cost_amount": posted,
                "confirmed_by_user_id": actor_user_id,
                "confirmed_at": confirmed_at,
            },
        )
        category_totals: dict[str, float] = defaultdict(float)
        for line in lines:
            category = (
                "agency_expense"
                if line.get("expense_category") == "agency_expense"
                else "supplier_cost"
            )
            line_amount = money(
                line.get("actual_amount") or line.get("expected_amount")
            )
            category_totals[category] = money(
                category_totals[category] + line_amount
            )
        for category, category_amount in category_totals.items():
            if category_amount <= 0:
                continue
            category_lines = [
                line
                for line in lines
                if (
                    "agency_expense"
                    if line.get("expense_category") == "agency_expense"
                    else "supplier_cost"
                )
                == category
            ]
            await self.post_transaction(
                agency_id=agency_id,
                currency=cost["currency"],
                entry_type="supplier_cost",
                reporting_category=category,
                direction="increase",
                amount=category_amount,
                source_event_type="supplier_cost.confirmed",
                source_event_id=supplier_cost_id,
                idempotency_key=(
                    f"supplier-cost:{supplier_cost_id}:confirmed:{category}"
                ),
                actor_user_id=actor_user_id,
                immutable_source={
                    "supplier_cost": updated,
                    "lines": category_lines,
                },
                references={
                    "client_id": cost.get("client_id"),
                    "trip_id": cost.get("trip_id"),
                    "booking_id": cost.get("booking_id"),
                    "ticket_id": cost.get("ticket_id"),
                    "emd_id": cost.get("emd_id"),
                    "supplier_cost_id": supplier_cost_id,
                },
            )
        await self._audit(
            agency_id=agency_id,
            actor_user_id=actor_user_id,
            event_type="supplier_cost.confirmed",
            entity_type="supplier_cost",
            entity_id=supplier_cost_id,
            summary=f"Confirmed supplier cost {cost['supplier_cost_reference']}.",
        )
        return updated or cost

    async def create_credit_note(
        self,
        agency_id: str,
        payload: CreditNoteCreate,
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        invoice = await self.recalculate_invoice(agency_id, payload.invoice_id)
        if invoice.get("status") not in {"issued", "partially_paid", "paid"}:
            raise CommercialLedgerError(
                "Credit notes require an issued invoice.",
                code="INVALID_CREDIT_NOTE_LIFECYCLE",
            )
        amount = require_positive(payload.amount, "Credit note amount")
        issued_credits = await self._agency_records(
            CREDIT_NOTES_COLLECTION,
            agency_id,
            {"invoice_id": invoice["id"], "status": "issued"},
        )
        draft_credits = await self._agency_records(
            CREDIT_NOTES_COLLECTION,
            agency_id,
            {"invoice_id": invoice["id"], "status": "draft"},
        )
        reserved = money(
            sum(money(item.get("total_amount")) for item in issued_credits + draft_credits)
        )
        if money(reserved + amount) > money(invoice["total_amount"]):
            raise CommercialLedgerError(
                "Credit notes cannot exceed the invoiced amount.",
                code="CREDIT_EXCEEDS_INVOICE",
            )
        if payload.invoice_line_item_id:
            line = await self.db.collection("invoice_line_items").find_one(
                {
                    "agency_id": agency_id,
                    "invoice_id": invoice["id"],
                    "id": payload.invoice_line_item_id,
                }
            )
            if not line:
                raise CommercialLedgerError(
                    "Credit line does not belong to the invoice.",
                    code="CONTEXT_MISMATCH",
                )
        credit = CreditNote(
            agency_id=agency_id,
            ledger_id=invoice["ledger_id"],
            credit_note_number=reference("CN"),
            invoice_id=invoice["id"],
            client_id=invoice["client_id"],
            trip_id=invoice.get("trip_id"),
            booking_id=invoice.get("booking_record_id")
            or invoice.get("booking_id"),
            currency=invoice["currency"],
            reason=payload.reason,
            total_amount=amount,
            created_by_user_id=actor_user_id,
            notes=payload.notes,
        )
        created = await self.db.collection(CREDIT_NOTES_COLLECTION).insert_one(
            credit.model_dump(mode="json")
        )
        line = CreditNoteLine(
            agency_id=agency_id,
            credit_note_id=created["id"],
            invoice_line_item_id=payload.invoice_line_item_id,
            description=payload.description or payload.reason,
            amount=amount,
            currency=invoice["currency"],
        )
        await self.db.collection(CREDIT_NOTE_LINES_COLLECTION).insert_one(
            line.model_dump(mode="json")
        )
        await self._audit(
            agency_id=agency_id,
            actor_user_id=actor_user_id,
            event_type="credit_note.created",
            entity_type="credit_note",
            entity_id=created["id"],
            summary=f"Created credit note {created['credit_note_number']}.",
            metadata={"invoice_id": invoice["id"], "reason": payload.reason},
        )
        return created

    async def issue_credit_note(
        self,
        agency_id: str,
        credit_note_id: str,
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        credit = await self.db.collection(CREDIT_NOTES_COLLECTION).find_one(
            {"agency_id": agency_id, "id": credit_note_id}
        )
        if not credit:
            raise CommercialLedgerError(
                "Credit note not found.",
                code="CREDIT_NOTE_NOT_FOUND",
            )
        if credit.get("status") == "issued":
            return credit
        if credit.get("status") != "draft":
            raise CommercialLedgerError(
                "Only draft credit notes can be issued.",
                code="INVALID_CREDIT_NOTE_LIFECYCLE",
            )
        invoice = await self.recalculate_invoice(agency_id, credit["invoice_id"])
        issued_at = now_utc()
        updated = await self.db.collection(CREDIT_NOTES_COLLECTION).update_one(
            {"agency_id": agency_id, "id": credit_note_id},
            {
                "status": "issued",
                "issued_by_user_id": actor_user_id,
                "issued_at": issued_at,
            },
        )
        await self.post_transaction(
            agency_id=agency_id,
            currency=credit["currency"],
            entry_type="credit_note",
            reporting_category="client_revenue",
            direction="decrease",
            amount=credit["total_amount"],
            source_event_type="credit_note.issued",
            source_event_id=credit_note_id,
            idempotency_key=f"credit-note:{credit_note_id}:issued",
            actor_user_id=actor_user_id,
            immutable_source={
                "credit_note": updated,
                "lines": await self._agency_records(
                    CREDIT_NOTE_LINES_COLLECTION,
                    agency_id,
                    {"credit_note_id": credit_note_id, "status": "active"},
                ),
            },
            references={
                "client_id": credit.get("client_id"),
                "trip_id": credit.get("trip_id"),
                "booking_id": credit.get("booking_id"),
                "invoice_id": credit["invoice_id"],
                "credit_note_id": credit_note_id,
            },
        )
        await self.recalculate_invoice(agency_id, invoice["id"])
        await self._audit(
            agency_id=agency_id,
            actor_user_id=actor_user_id,
            event_type="credit_note.issued",
            entity_type="credit_note",
            entity_id=credit_note_id,
            summary=f"Issued credit note {credit['credit_note_number']}.",
            metadata={"invoice_id": invoice["id"], "reason": credit["reason"]},
        )
        return updated or credit

    async def create_refund_entry(
        self,
        agency_id: str,
        payload: RefundLedgerEntryCreate,
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        if payload.commercial_source_type not in REFUND_SOURCE_TYPES:
            raise CommercialLedgerError(
                "Refund source must be ticket, EMD, or manual.",
                code="INVALID_REFUND_SOURCE",
            )
        if not payload.payment_allocation_id:
            raise CommercialLedgerError(
                "Refund accounting requires original Payment Allocation lineage.",
                code="INCOMPLETE_REFUND_LINEAGE",
            )
        amount = require_positive(payload.amount, "Refund amount")
        source_id = payload.commercial_source_id
        ticket_id = payload.ticket_id
        emd_id = payload.emd_id
        if payload.commercial_source_type == "ticket":
            if source_id and ticket_id and source_id != ticket_id:
                raise CommercialLedgerError(
                    "Ticket refund source does not match the linked Ticket.",
                    code="CONTEXT_MISMATCH",
                )
            ticket_id = ticket_id or source_id
            source_id = source_id or ticket_id
            if not ticket_id:
                raise CommercialLedgerError(
                    "Ticket refunds require canonical Ticket lineage.",
                    code="INVALID_REFUND_SOURCE",
                )
        elif payload.commercial_source_type == "emd":
            if source_id and emd_id and source_id != emd_id:
                raise CommercialLedgerError(
                    "EMD refund source does not match the linked EMD.",
                    code="CONTEXT_MISMATCH",
                )
            emd_id = emd_id or source_id
            source_id = source_id or emd_id
            if not emd_id:
                raise CommercialLedgerError(
                    "EMD refunds require canonical EMD lineage.",
                    code="INVALID_REFUND_SOURCE",
                )
        key = payload.idempotency_key or canonical_hash(
            payload.model_dump(mode="json")
        )
        await self.validate_lineage(
            agency_id=agency_id,
            client_id=payload.client_id,
            trip_id=payload.trip_id,
            booking_id=payload.booking_id,
            ticket_id=ticket_id,
            emd_id=emd_id,
        )
        payment = await self._agency_record(
            "payment_records",
            agency_id,
            payload.payment_record_id,
            "Payment",
        )
        allocation = None
        if payload.payment_allocation_id:
            allocation = await self.db.collection(
                PAYMENT_ALLOCATIONS_COLLECTION
            ).find_one(
                {
                    "agency_id": agency_id,
                    "id": payload.payment_allocation_id,
                    "status": "posted",
                }
            )
            if not allocation:
                raise CommercialLedgerError(
                    "Payment allocation not found.",
                    code="PAYMENT_ALLOCATION_NOT_FOUND",
                )
            if (
                payment
                and allocation.get("payment_record_id") != payment.get("id")
            ):
                raise CommercialLedgerError(
                    "Refund Payment and allocation references do not match.",
                    code="CONTEXT_MISMATCH",
                )
            if not payment:
                payment = await self._agency_record(
                    "payment_records",
                    agency_id,
                    allocation.get("payment_record_id"),
                    "Allocated Payment",
                )
            if allocation.get("currency") != payload.currency.upper():
                raise CommercialLedgerError(
                    "Refund currency must match the payment allocation.",
                    code="CURRENCY_MISMATCH",
                )
        if payment:
            if payment.get("status") != "received":
                raise CommercialLedgerError(
                    "Refunds can only reference received Payment evidence.",
                    code="PAYMENT_NOT_RECEIVED",
                )
            if payment.get("currency") != payload.currency.upper():
                raise CommercialLedgerError(
                    "Refund currency must match the Payment.",
                    code="CURRENCY_MISMATCH",
                )
            self._assert_context(
                payment,
                client_id=payload.client_id,
                trip_id=payload.trip_id,
                booking_id=payload.booking_id,
                label="Payment",
            )
        existing = await self.db.collection(REFUND_LEDGER_ENTRIES_COLLECTION).find_one(
            {"agency_id": agency_id, "idempotency_key": key}
        )
        if existing:
            expected = {
                **payload.model_dump(
                    exclude={
                        "idempotency_key",
                        "amount",
                        "currency",
                        "ticket_id",
                        "emd_id",
                        "payment_record_id",
                        "commercial_source_id",
                    },
                    mode="json",
                ),
                "ticket_id": ticket_id,
                "emd_id": emd_id,
                "payment_record_id": (payment or {}).get("id"),
                "commercial_source_id": source_id,
                "amount": amount,
                "currency": payload.currency.upper(),
            }
            actual = {field: existing.get(field) for field in expected}
            if actual != expected:
                raise CommercialLedgerError(
                    "Refund idempotency key already refers to different evidence.",
                    code="IDEMPOTENCY_CONFLICT",
                )
            return existing
        if allocation:
            prior = await self._agency_records(
                REFUND_LEDGER_ENTRIES_COLLECTION,
                agency_id,
                {
                    "payment_allocation_id": allocation["id"],
                    "status": {"$ne": "cancelled"},
                },
            )
            remaining = money(
                allocation.get("amount")
                - sum(money(item.get("amount")) for item in prior)
            )
            if amount > remaining:
                raise CommercialLedgerError(
                    "Refund exceeds the linked payment allocation.",
                    code="REFUND_EXCEEDS_ALLOCATION",
                )
        if payment:
            prior_payment_refunds = await self._agency_records(
                REFUND_LEDGER_ENTRIES_COLLECTION,
                agency_id,
                {
                    "payment_record_id": payment["id"],
                    "status": {"$ne": "cancelled"},
                },
            )
            payment_remaining = money(
                payment.get("amount")
                - sum(money(item.get("amount")) for item in prior_payment_refunds)
            )
            if amount > payment_remaining:
                raise CommercialLedgerError(
                    "Refund exceeds the linked Payment evidence.",
                    code="REFUND_EXCEEDS_PAYMENT",
                )
        ledger = await self.ensure_ledger(
            agency_id, payload.currency, actor_user_id
        )
        entry = RefundLedgerEntry(
            agency_id=agency_id,
            ledger_id=ledger["id"],
            refund_reference=reference("REF"),
            amount=amount,
            currency=ledger["currency"],
            idempotency_key=key,
            recorded_by_user_id=actor_user_id,
            ticket_id=ticket_id,
            emd_id=emd_id,
            payment_record_id=(payment or {}).get("id"),
            commercial_source_id=source_id,
            **payload.model_dump(
                exclude={
                    "amount",
                    "currency",
                    "idempotency_key",
                    "ticket_id",
                    "emd_id",
                    "payment_record_id",
                    "commercial_source_id",
                },
                mode="json",
            ),
        )
        created = await self.db.collection(REFUND_LEDGER_ENTRIES_COLLECTION).insert_one(
            entry.model_dump(mode="json")
        )
        await self.post_transaction(
            agency_id=agency_id,
            currency=entry.currency,
            entry_type="refund",
            reporting_category="refund_exposure",
            direction="increase",
            amount=amount,
            source_event_type="refund.recorded",
            source_event_id=created["id"],
            idempotency_key=f"refund:{created['id']}:recorded",
            actor_user_id=actor_user_id,
            immutable_source=created,
            references={
                "client_id": entry.client_id,
                "trip_id": entry.trip_id,
                "booking_id": entry.booking_id,
                "ticket_id": entry.ticket_id,
                "emd_id": entry.emd_id,
                "payment_record_id": entry.payment_record_id,
                "payment_allocation_id": entry.payment_allocation_id,
                "refund_ledger_entry_id": created["id"],
            },
        )
        await self._audit(
            agency_id=agency_id,
            actor_user_id=actor_user_id,
            event_type="refund.recorded",
            entity_type="refund_ledger_entry",
            entity_id=created["id"],
            summary=f"Recorded refund {created['refund_reference']}.",
            metadata={"reason": payload.reason},
        )
        return created

    async def create_exchange_entry(
        self,
        agency_id: str,
        payload: ExchangeLedgerEntryCreate,
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        if not all(
            (
                payload.trip_id,
                payload.booking_id,
                payload.original_ticket_id,
                payload.new_ticket_id,
                payload.accepted_change_id,
            )
        ):
            raise CommercialLedgerError(
                "Exchange accounting requires Trip, Booking, original and new Tickets, and accepted change evidence.",
                code="INCOMPLETE_EXCHANGE_LINEAGE",
            )
        components = {
            "fare_difference_amount": money(payload.fare_difference_amount),
            "tax_difference_amount": money(payload.tax_difference_amount),
            "agency_fee_amount": money(payload.agency_fee_amount),
            "supplier_fee_amount": money(payload.supplier_fee_amount),
            "emd_difference_amount": money(payload.emd_difference_amount),
            "exchange_fee_amount": money(payload.exchange_fee_amount),
        }
        total = money(sum(components.values()))
        if total == 0:
            raise CommercialLedgerError(
                "Exchange accounting requires a non-zero financial difference.",
                code="INVALID_MONETARY_VALUE",
            )
        key = payload.idempotency_key or canonical_hash(
            payload.model_dump(mode="json")
        )
        existing = await self.db.collection(EXCHANGE_LEDGER_ENTRIES_COLLECTION).find_one(
            {"agency_id": agency_id, "idempotency_key": key}
        )
        if existing:
            expected = {
                **payload.model_dump(
                    exclude={
                        "currency",
                        "idempotency_key",
                        *components.keys(),
                    },
                    mode="json",
                ),
                **components,
                "currency": payload.currency.upper(),
                "total_difference_amount": total,
            }
            actual = {field: existing.get(field) for field in expected}
            if actual != expected:
                raise CommercialLedgerError(
                    "Exchange idempotency key already refers to different evidence.",
                    code="IDEMPOTENCY_CONFLICT",
                )
            return existing
        await self.validate_lineage(
            agency_id=agency_id,
            client_id=payload.client_id,
            trip_id=payload.trip_id,
            booking_id=payload.booking_id,
            ticket_id=payload.original_ticket_id,
            emd_id=payload.emd_id,
        )
        new_ticket = await self._record_from_candidates(
            ("ticket_records", "ticket_workspaces"),
            agency_id,
            payload.new_ticket_id,
            "New ticket",
        )
        self._assert_context(
            new_ticket,
            client_id=payload.client_id,
            trip_id=payload.trip_id,
            booking_id=payload.booking_id,
            label="New ticket",
        )
        await self.validate_accepted_change(
            agency_id=agency_id,
            accepted_change_id=payload.accepted_change_id,
            client_id=payload.client_id,
            trip_id=payload.trip_id,
            booking_id=payload.booking_id,
        )
        ledger = await self.ensure_ledger(
            agency_id, payload.currency, actor_user_id
        )
        entry = ExchangeLedgerEntry(
            agency_id=agency_id,
            ledger_id=ledger["id"],
            exchange_reference=reference("EXC"),
            total_difference_amount=total,
            currency=ledger["currency"],
            idempotency_key=key,
            recorded_by_user_id=actor_user_id,
            **payload.model_dump(
                exclude={
                    "currency",
                    "idempotency_key",
                    *components.keys(),
                },
                mode="json",
            ),
            **components,
        )
        created = await self.db.collection(
            EXCHANGE_LEDGER_ENTRIES_COLLECTION
        ).insert_one(entry.model_dump(mode="json"))
        await self.post_transaction(
            agency_id=agency_id,
            currency=entry.currency,
            entry_type="exchange",
            reporting_category="exchange_exposure",
            direction="increase" if total > 0 else "decrease",
            amount=abs(total),
            source_event_type="exchange.recorded",
            source_event_id=created["id"],
            idempotency_key=f"exchange:{created['id']}:recorded",
            actor_user_id=actor_user_id,
            immutable_source=created,
            references={
                "client_id": entry.client_id,
                "trip_id": entry.trip_id,
                "booking_id": entry.booking_id,
                "ticket_id": entry.original_ticket_id,
                "emd_id": entry.emd_id,
                "exchange_ledger_entry_id": created["id"],
            },
        )
        await self._audit(
            agency_id=agency_id,
            actor_user_id=actor_user_id,
            event_type="exchange.recorded",
            entity_type="exchange_ledger_entry",
            entity_id=created["id"],
            summary=f"Recorded exchange accounting {created['exchange_reference']}.",
            metadata={"reason": payload.reason},
        )
        return created

    async def invoice_detail(
        self, agency_id: str, invoice_id: str, *, include_costs: bool
    ) -> dict[str, Any]:
        invoice = await self.recalculate_invoice(agency_id, invoice_id)
        booking_record_id = invoice.get("booking_record_id") or invoice.get(
            "booking_id"
        )
        result = {
            "invoice": invoice,
            "client": await self._agency_record(
                "client_profiles",
                agency_id,
                invoice["client_id"],
                "Client",
            ),
            "line_items": await self._agency_records(
                "invoice_line_items",
                agency_id,
                {"invoice_id": invoice_id},
            ),
            "payments": [],
            "payment_allocations": await self._agency_records(
                PAYMENT_ALLOCATIONS_COLLECTION,
                agency_id,
                {"invoice_id": invoice_id},
            ),
            "credit_notes": await self._agency_records(
                CREDIT_NOTES_COLLECTION,
                agency_id,
                {"invoice_id": invoice_id},
            ),
            "booking": await self.db.collection("bookings").find_one(
                {"agency_id": agency_id, "id": invoice.get("booking_id")}
            )
            if invoice.get("booking_id")
            else None,
            "booking_workspace": await self.db.collection(
                "booking_workspaces"
            ).find_one(
                {
                    "agency_id": agency_id,
                    "id": invoice.get("booking_workspace_id"),
                }
            )
            if invoice.get("booking_workspace_id")
            else None,
            "booking_record": await self.db.collection("booking_records").find_one(
                {"agency_id": agency_id, "id": booking_record_id}
            )
            if booking_record_id
            else None,
        }
        payment_ids = {
            item["payment_record_id"]
            for item in result["payment_allocations"]
            if item.get("payment_record_id")
        }
        result["payments"] = [
            payment
            for payment_id in payment_ids
            if (
                payment := await self.db.collection("payment_records").find_one(
                    {"agency_id": agency_id, "id": payment_id}
                )
            )
        ]
        if include_costs:
            result["supplier_costs"] = await self._agency_records(
                SUPPLIER_COSTS_COLLECTION,
                agency_id,
                {"booking_id": booking_record_id},
            )
        return result

    async def list_transactions(
        self,
        agency_id: str,
        *,
        include_costs: bool = False,
        entry_type: str | None = None,
        trip_id: str | None = None,
        booking_id: str | None = None,
        invoice_id: str | None = None,
    ) -> list[dict[str, Any]]:
        filters: dict[str, Any] = {}
        if entry_type:
            filters["entry_type"] = entry_type
        if trip_id:
            filters["trip_id"] = trip_id
        if booking_id:
            filters["booking_id"] = booking_id
        if invoice_id:
            filters["invoice_id"] = invoice_id
        items = await self._agency_records(
            COMMERCIAL_TRANSACTIONS_COLLECTION,
            agency_id,
            filters,
        )
        if not include_costs:
            items = [
                item
                for item in items
                if item.get("reporting_category")
                not in {"supplier_cost", "agency_expense"}
            ]
        return [
            {
                key: value
                for key, value in item.items()
                if key != "immutable_source_json"
            }
            for item in items
        ]

    async def reporting(
        self,
        agency_id: str,
        *,
        include_costs: bool,
        trip_id: str | None = None,
        booking_id: str | None = None,
    ) -> dict[str, Any]:
        filters: dict[str, Any] = {"posting_status": "posted"}
        if trip_id:
            filters["trip_id"] = trip_id
        if booking_id:
            filters["booking_id"] = booking_id
        transactions = await self._agency_records(
            COMMERCIAL_TRANSACTIONS_COLLECTION,
            agency_id,
            filters,
        )
        if not include_costs:
            transactions = [
                item
                for item in transactions
                if item.get("reporting_category")
                not in {"supplier_cost", "agency_expense"}
            ]
        by_currency: dict[str, dict[str, float]] = defaultdict(
            lambda: defaultdict(float)
        )
        profitability: dict[tuple[str, str], dict[str, Any]] = {}
        for item in transactions:
            currency = item.get("currency") or "UNKNOWN"
            category = item.get("reporting_category") or "other"
            signed = money(item.get("signed_amount"))
            by_currency[currency][category] = money(
                by_currency[currency][category] + signed
            )
            context_type = "booking" if item.get("booking_id") else "trip"
            context_id = item.get("booking_id") or item.get("trip_id")
            if context_id:
                key = (context_type, context_id)
                row = profitability.setdefault(
                    key,
                    {
                        "context_type": context_type,
                        "context_id": context_id,
                        "currency": currency,
                        "revenue": 0,
                        "supplier_costs": 0,
                        "agency_expenses": 0,
                    },
                )
                if category == "client_revenue":
                    row["revenue"] = money(row["revenue"] + signed)
                elif category == "supplier_cost":
                    row["supplier_costs"] = money(
                        row["supplier_costs"] + abs(signed)
                    )
                elif category == "agency_expense":
                    row["agency_expenses"] = money(
                        row["agency_expenses"] + abs(signed)
                    )
        summaries: list[dict[str, Any]] = []
        for currency, values in sorted(by_currency.items()):
            revenue = money(values.get("client_revenue"))
            supplier_costs = money(values.get("supplier_cost")) if include_costs else None
            agency_expenses = money(values.get("agency_expense")) if include_costs else None
            margin = (
                money(revenue - (supplier_costs or 0) - (agency_expenses or 0))
                if include_costs
                else None
            )
            summaries.append(
                {
                    "currency": currency,
                    "revenue": revenue,
                    "supplier_costs": supplier_costs,
                    "agency_expenses": agency_expenses,
                    "gross_margin": margin,
                    "payments_received": money(values.get("payment_received")),
                    "payment_allocations": abs(money(values.get("receivable"))),
                    "refund_exposure": money(values.get("refund_exposure")),
                    "exchange_exposure": money(values.get("exchange_exposure")),
                }
            )
        receivable_by_invoice: dict[str, float] = defaultdict(float)
        for item in transactions:
            invoice_id = item.get("invoice_id")
            if not invoice_id:
                continue
            if item.get("reporting_category") == "client_revenue":
                receivable_by_invoice[invoice_id] = money(
                    receivable_by_invoice[invoice_id]
                    + money(item.get("signed_amount"))
                )
            if item.get("reporting_category") == "receivable":
                receivable_by_invoice[invoice_id] = money(
                    receivable_by_invoice[invoice_id]
                    + money(item.get("signed_amount"))
                )
        outstanding_invoices = [
            {"invoice_id": invoice_id, "amount": amount}
            for invoice_id, amount in receivable_by_invoice.items()
            if amount > 0
        ]
        payments = await self._agency_records(
            "payment_records",
            agency_id,
            {"status": "received"},
        )
        outstanding_payments = [
            {
                "payment_id": item["id"],
                "currency": item["currency"],
                "unallocated_amount": money(item.get("unallocated_amount")),
            }
            for item in payments
            if money(item.get("unallocated_amount")) > 0
        ]
        profitability_rows = []
        for row in profitability.values():
            if include_costs:
                row["gross_margin"] = money(
                    row["revenue"]
                    - row["supplier_costs"]
                    - row["agency_expenses"]
                )
            else:
                row.pop("supplier_costs", None)
                row.pop("agency_expenses", None)
            profitability_rows.append(row)
        return {
            "summaries": summaries,
            "outstanding_invoices": outstanding_invoices,
            "outstanding_payments": outstanding_payments,
            "profitability": profitability_rows,
            "transaction_count": len(transactions),
            "source": "commercial_transactions",
            "operational_records_recomputed": False,
            "supplier_costs_visible": include_costs,
        }

    async def migration_analysis(
        self, maximum_records_per_collection: int = 5000
    ) -> dict[str, Any]:
        if maximum_records_per_collection < 1:
            raise ValueError("maximum_records_per_collection must be positive")

        async def scan(collection_name: str) -> list[dict[str, Any]]:
            repository = PersistenceRepository(self.db)
            records: list[dict[str, Any]] = []
            offset = 0
            while len(records) < maximum_records_per_collection:
                page = await repository.find_platform_records(
                    collection_name=collection_name,
                    pagination=PaginationRequest.build(
                        limit=maximum_records_per_collection - len(records),
                        offset=offset,
                    ),
                )
                records.extend(page.items)
                if not page.pagination.has_more or not page.items:
                    break
                offset += len(page.items)
            return records

        before = {
            name: await self.db.collection(name).count()
            for name in CANONICAL_FINANCE_COLLECTIONS
        }
        invoices = await scan("invoices")
        payments = await scan("payment_records")
        legacy_refunds = await scan("refund_exchange_cases")
        supplier_costs = await scan(SUPPLIER_COSTS_COLLECTION)
        allocations = await scan(PAYMENT_ALLOCATIONS_COLLECTION)
        duplicate_invoices: dict[tuple[str, str], list[str]] = defaultdict(list)
        for item in invoices:
            context = item.get("booking_record_id") or item.get(
                "booking_workspace_id"
            ) or item.get("booking_id")
            if context:
                duplicate_invoices[(item.get("agency_id"), context)].append(
                    item["id"]
                )
        duplicate_allocations: dict[tuple[str, str, str, float], list[str]] = (
            defaultdict(list)
        )
        for item in allocations:
            key = (
                item.get("agency_id"),
                item.get("payment_record_id"),
                item.get("invoice_id"),
                money(item.get("amount")),
            )
            duplicate_allocations[key].append(item["id"])
        booking_cost_keys = {
            (item.get("agency_id"), item.get("booking_id"))
            for item in supplier_costs
            if item.get("booking_id")
        }
        missing_supplier_costs = [
            item["id"]
            for item in invoices
            if (item.get("agency_id"), item.get("booking_record_id") or item.get("booking_id"))
            not in booking_cost_keys
        ]
        missing_margin_ids: list[str] = []
        for item in invoices:
            posting = await self.db.collection(
                COMMERCIAL_TRANSACTIONS_COLLECTION
            ).find_one(
                {
                    "agency_id": item.get("agency_id"),
                    "invoice_id": item["id"],
                    "reporting_category": "client_revenue",
                }
            )
            if not posting:
                missing_margin_ids.append(item["id"])
        after = {
            name: await self.db.collection(name).count()
            for name in CANONICAL_FINANCE_COLLECTIONS
        }
        return {
            "dry_run": True,
            "write_mode_available": False,
            "writes_performed": 0,
            "before_counts": before,
            "after_counts": after,
            "legacy_invoices": len(invoices),
            "legacy_payments": len(payments),
            "legacy_refund_exchange_cases": len(legacy_refunds),
            "missing_supplier_cost_invoice_ids": sorted(missing_supplier_costs),
            "missing_margin_invoice_ids": sorted(missing_margin_ids),
            "duplicate_invoice_groups": [
                {"agency_id": key[0], "context_id": key[1], "invoice_ids": ids}
                for key, ids in duplicate_invoices.items()
                if len(ids) > 1
            ],
            "duplicate_allocation_groups": [
                {
                    "agency_id": key[0],
                    "payment_record_id": key[1],
                    "invoice_id": key[2],
                    "amount": key[3],
                    "allocation_ids": ids,
                }
                for key, ids in duplicate_allocations.items()
                if len(ids) > 1
            ],
            "manual_review_required": True,
            "operational_records_modified": False,
        }


def commercial_ledger_readiness_metadata() -> dict[str, Any]:
    return {
        "canonical_commercial_ledger_enabled": True,
        "invoice_totals_server_derived": True,
        "payment_allocation_enabled": True,
        "supplier_costs_separate_from_client_charges": True,
        "credit_notes_non_destructive": True,
        "refund_payment_history_immutable": True,
        "exchange_lineage_enabled": True,
        "ledger_reporting_enabled": True,
        "operational_evidence_rewrite_disabled": True,
        "payment_gateway_execution_disabled": True,
        "external_accounting_integration_disabled": True,
        "migration_analysis_dry_run_only": True,
        "readiness_required": False,
    }
