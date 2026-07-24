from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable

from fastapi import HTTPException
from pydantic import ValidationError

from database import Database
from models import (
    CreditNoteCreate,
    ExchangeLedgerEntryCreate,
    InvoiceCreate,
    InvoiceLineItemCreate,
    PaymentAllocationCreate,
    PaymentRecordCreate,
    RefundLedgerEntryCreate,
    SupplierCostCreate,
    SupplierCostLineCreate,
)
from persistence_query import CollectionOwnershipType, get_collection_ownership
from routers.finance import require_cost_read, require_read, require_write
from services.authorization_service import agency_permissions
from services.canonical_commercial_ledger_service import (
    CANONICAL_FINANCE_COLLECTIONS,
    COMMERCIAL_TRANSACTIONS_COLLECTION,
    CREDIT_NOTES_COLLECTION,
    EXCHANGE_LEDGER_ENTRIES_COLLECTION,
    FINANCE_WRITER_CLASSIFICATION,
    INVOICE_LIFECYCLE,
    PAYMENT_ALLOCATIONS_COLLECTION,
    REFUND_LEDGER_ENTRIES_COLLECTION,
    SUPPLIER_COSTS_COLLECTION,
    CanonicalCommercialLedgerService,
    CommercialLedgerError,
    commercial_ledger_readiness_metadata,
)


ROOT = Path(__file__).resolve().parents[2]
AGENCY_ID = "ledger-smoke-agency"
OTHER_AGENCY_ID = "ledger-smoke-other-agency"
CLIENT_ID = "ledger-smoke-client"
TRIP_ID = "ledger-smoke-trip"
BOOKING_ID = "ledger-smoke-booking"
WORKSPACE_ID = "ledger-smoke-booking-workspace"
SNAPSHOT_ID = "ledger-smoke-accepted-snapshot"
TICKET_ID = "ledger-smoke-ticket"
NEW_TICKET_ID = "ledger-smoke-new-ticket"
EMD_ID = "ledger-smoke-emd"
SERVICE_ID = "ledger-smoke-service"
OWNER_ID = "ledger-smoke-owner"
ACCOUNTANT_ID = "ledger-smoke-accountant"
AGENT_ID = "ledger-smoke-agent"
READONLY_ID = "ledger-smoke-readonly"
PLATFORM_ID = "ledger-smoke-platform"


@dataclass
class SmokeContext:
    db: Database
    service: CanonicalCommercialLedgerService
    upstream_before: dict[str, Any]
    checks: list[str]

    def check(self, name: str, condition: bool, message: str) -> None:
        if not condition:
            raise AssertionError(f"{name}: {message}")
        self.checks.append(name)


async def insert(db: Database, collection: str, record: dict[str, Any]) -> dict[str, Any]:
    return await db.collection(collection).insert_one(record)


async def seed() -> SmokeContext:
    db = Database()
    for agency_id, name in (
        (AGENCY_ID, "Ledger Smoke Agency"),
        (OTHER_AGENCY_ID, "Other Ledger Agency"),
    ):
        await insert(
            db,
            "agencies",
            {
                "id": agency_id,
                "name": name,
                "slug": agency_id,
                "status": "active",
            },
        )
    for user_id, role in (
        (OWNER_ID, "agency_owner"),
        (ACCOUNTANT_ID, "agency_accountant"),
        (AGENT_ID, "agency_agent"),
        (READONLY_ID, "agency_readonly"),
    ):
        await insert(
            db,
            "platform_users",
            {
                "id": user_id,
                "email": f"{user_id}@example.test",
                "status": "active",
            },
        )
        await insert(
            db,
            "agency_staff_memberships",
            {
                "id": f"membership-{user_id}",
                "agency_id": AGENCY_ID,
                "user_id": user_id,
                "agency_role": role,
                "status": "active",
            },
        )
    await insert(
        db,
        "platform_users",
        {
            "id": PLATFORM_ID,
            "email": "ledger-platform@example.test",
            "global_role": "platform_owner",
            "status": "active",
        },
    )
    await insert(
        db,
        "client_profiles",
        {
            "id": CLIENT_ID,
            "agency_id": AGENCY_ID,
            "display_name": "Ledger Test Client",
            "status": "active",
        },
    )
    await insert(
        db,
        "client_profiles",
        {
            "id": "other-client",
            "agency_id": OTHER_AGENCY_ID,
            "display_name": "Other Client",
            "status": "active",
        },
    )
    await insert(
        db,
        "trip_dossiers",
        {
            "id": TRIP_ID,
            "agency_id": AGENCY_ID,
            "client_id": CLIENT_ID,
            "trip_reference": "TRP-LEDGER-001",
            "trip_status": "confirmed",
        },
    )
    await insert(
        db,
        "trip_accepted_offer_snapshots",
        {
            "id": SNAPSHOT_ID,
            "agency_id": AGENCY_ID,
            "client_id": CLIENT_ID,
            "trip_id": TRIP_ID,
            "offer_workspace_id": "offer-ledger",
            "snapshot_hash": "accepted-ledger-evidence-hash",
            "confirmed_pricing_json": {
                "summary": {"currency": "EUR", "total_amount": 300}
            },
        },
    )
    await insert(
        db,
        "offer_workspaces",
        {
            "id": "offer-ledger",
            "agency_id": AGENCY_ID,
            "client_id": CLIENT_ID,
            "trip_id": TRIP_ID,
            "status": "accepted",
        },
    )
    await insert(
        db,
        "offer_workspaces",
        {
            "id": "other-offer",
            "agency_id": OTHER_AGENCY_ID,
            "client_id": "other-client",
            "trip_id": "other-trip",
            "status": "accepted",
        },
    )
    await insert(
        db,
        "booking_records",
        {
            "id": BOOKING_ID,
            "agency_id": AGENCY_ID,
            "client_id": CLIENT_ID,
            "trip_id": TRIP_ID,
            "booking_reference": "BOOK-LEDGER-001",
            "pnr_locator": "LEDGER",
            "booking_status": "confirmed",
        },
    )
    await insert(
        db,
        "booking_workspaces",
        {
            "id": WORKSPACE_ID,
            "agency_id": AGENCY_ID,
            "client_id": CLIENT_ID,
            "trip_id": TRIP_ID,
            "booking_record_id": BOOKING_ID,
            "accepted_offer_snapshot_id": SNAPSHOT_ID,
            "workspace_number": "BW-LEDGER-001",
            "status": "booked",
        },
    )
    for ticket_id, number in (
        (TICKET_ID, "1110000000001"),
        (NEW_TICKET_ID, "1110000000002"),
    ):
        await insert(
            db,
            "ticket_records",
            {
                "id": ticket_id,
                "agency_id": AGENCY_ID,
                "client_id": CLIENT_ID,
                "trip_id": TRIP_ID,
                "booking_record_id": BOOKING_ID,
                "ticket_number": number,
                "issue_status": "issued",
                "currency": "EUR",
            },
        )
    await insert(
        db,
        "emd_records",
        {
            "id": EMD_ID,
            "agency_id": AGENCY_ID,
            "client_id": CLIENT_ID,
            "trip_id": TRIP_ID,
            "booking_record_id": BOOKING_ID,
            "emd_number": "1119999999999",
            "issue_status": "issued",
            "currency": "EUR",
        },
    )
    await insert(
        db,
        "passenger_service_requests",
        {
            "id": SERVICE_ID,
            "agency_id": AGENCY_ID,
            "client_id": CLIENT_ID,
            "trip_id": TRIP_ID,
            "booking_id": BOOKING_ID,
            "service_code": "WCHC",
            "status": "confirmed",
        },
    )
    await insert(
        db,
        "passenger_service_requests",
        {
            "id": "other-service",
            "agency_id": OTHER_AGENCY_ID,
            "client_id": "other-client",
            "trip_id": "other-trip",
            "booking_id": "other-booking",
            "service_code": "PETC",
            "status": "confirmed",
        },
    )
    await insert(
        db,
        "ticket_exchange_operations",
        {
            "id": "accepted-change-001",
            "agency_id": AGENCY_ID,
            "trip_id": TRIP_ID,
            "booking_record_id": BOOKING_ID,
            "original_ticket_record_id": TICKET_ID,
            "new_ticket_record_id": NEW_TICKET_ID,
            "operation_type": "exchange",
            "status": "accepted",
        },
    )
    await insert(
        db,
        "ticket_exchange_operations",
        {
            "id": "draft-change-001",
            "agency_id": AGENCY_ID,
            "trip_id": TRIP_ID,
            "booking_record_id": BOOKING_ID,
            "original_ticket_record_id": TICKET_ID,
            "new_ticket_record_id": NEW_TICKET_ID,
            "operation_type": "exchange",
            "status": "draft",
        },
    )
    await insert(
        db,
        "ticket_exchange_operations",
        {
            "id": "other-accepted-change",
            "agency_id": OTHER_AGENCY_ID,
            "trip_id": "other-trip",
            "booking_record_id": "other-booking",
            "original_ticket_record_id": "other-ticket",
            "operation_type": "exchange",
            "status": "accepted",
        },
    )
    await insert(
        db,
        "ticket_records",
        {
            "id": "other-ticket",
            "agency_id": OTHER_AGENCY_ID,
            "client_id": "other-client",
            "trip_id": "other-trip",
            "booking_record_id": "other-booking",
            "ticket_number": "2220000000001",
            "issue_status": "issued",
        },
    )
    await insert(
        db,
        "payment_records",
        {
            "id": "other-payment",
            "agency_id": OTHER_AGENCY_ID,
            "client_id": "other-client",
            "status": "received",
            "amount": 100,
            "currency": "EUR",
        },
    )
    upstream_before = {
        name: deepcopy(await db.collection(name).find_many())
        for name in (
            "trip_accepted_offer_snapshots",
            "offer_workspaces",
            "trip_dossiers",
            "booking_records",
            "ticket_records",
            "emd_records",
            "passenger_service_requests",
            "ticket_exchange_operations",
        )
    }
    return SmokeContext(
        db=db,
        service=CanonicalCommercialLedgerService(db),
        upstream_before=upstream_before,
        checks=[],
    )


async def expect_ledger_error(
    awaitable: Awaitable[Any],
    code: str,
) -> CommercialLedgerError:
    try:
        await awaitable
    except CommercialLedgerError as exc:
        if exc.code != code:
            raise AssertionError(f"Expected {code}, received {exc.code}.") from exc
        return exc
    raise AssertionError(f"Expected CommercialLedgerError {code}.")


async def expect_http_forbidden(awaitable: Awaitable[Any]) -> None:
    try:
        await awaitable
    except HTTPException as exc:
        if exc.status_code != 403:
            raise AssertionError(f"Expected HTTP 403, received {exc.status_code}.")
        return
    raise AssertionError("Expected HTTP 403.")


async def create_invoice(
    ctx: SmokeContext,
    *,
    total: float,
    currency: str = "EUR",
    line_type: str = "ticket",
    ticket_id: str | None = TICKET_ID,
) -> tuple[dict[str, Any], dict[str, Any]]:
    invoice = await ctx.service.create_invoice(
        AGENCY_ID,
        InvoiceCreate(
            client_id=CLIENT_ID,
            trip_id=TRIP_ID,
            booking_id=BOOKING_ID,
            booking_record_id=BOOKING_ID,
            booking_workspace_id=WORKSPACE_ID,
            offer_id="offer-ledger",
            accepted_offer_snapshot_id=SNAPSHOT_ID,
            currency=currency,
        ),
        OWNER_ID,
    )
    line = await ctx.service.add_invoice_line(
        AGENCY_ID,
        invoice["id"],
        InvoiceLineItemCreate(
            trip_id=TRIP_ID,
            booking_id=BOOKING_ID,
            booking_record_id=BOOKING_ID,
            ticket_id=ticket_id,
            line_type=line_type,
            description=f"{line_type.replace('_', ' ').title()} charge",
            quantity=1,
            unit_amount=total,
            currency=currency,
        ),
        OWNER_ID,
    )
    invoice = await ctx.service.issue_invoice(AGENCY_ID, invoice["id"], OWNER_ID)
    return invoice, line


async def assert_upstream_unchanged(ctx: SmokeContext) -> None:
    after = {
        name: await ctx.db.collection(name).find_many()
        for name in ctx.upstream_before
    }
    ctx.check(
        "operational_evidence_immutable",
        after == ctx.upstream_before,
        "Commercial writes changed accepted, Trip, Booking, Ticket, or EMD evidence.",
    )


async def run_commercial_ledger() -> list[str]:
    ctx = await seed()
    invoice, _ = await create_invoice(ctx, total=300)
    cost = await ctx.service.create_supplier_cost(
        AGENCY_ID,
        SupplierCostCreate(
            supplier_reference="SUP-001",
            supplier_name="Test Airline",
            client_id=CLIENT_ID,
            trip_id=TRIP_ID,
            booking_id=BOOKING_ID,
            booking_workspace_id=WORKSPACE_ID,
            ticket_id=TICKET_ID,
            currency="EUR",
            description="Airline net cost",
            expected_cost_amount=120,
            actual_cost_amount=120,
        ),
        ACCOUNTANT_ID,
    )
    await ctx.service.confirm_supplier_cost(AGENCY_ID, cost["id"], ACCOUNTANT_ID)
    credit = await ctx.service.create_credit_note(
        AGENCY_ID,
        CreditNoteCreate(
            invoice_id=invoice["id"],
            reason="Reviewed client concession",
            amount=20,
        ),
        OWNER_ID,
    )
    await ctx.service.issue_credit_note(AGENCY_ID, credit["id"], OWNER_ID)
    transactions = await ctx.service.list_transactions(
        AGENCY_ID, include_costs=True
    )
    ctx.check(
        "ledger_postings_exist",
        {
            "invoice_created",
            "invoice_adjusted",
            "supplier_cost",
            "credit_note",
        }.issubset({item["entry_type"] for item in transactions}),
        "Expected canonical posting types were not recorded.",
    )
    ctx.check(
        "immutable_source_hashes",
        all(item.get("immutable_source_hash") for item in transactions),
        "A ledger posting is missing immutable source evidence.",
    )
    report = await ctx.service.reporting(AGENCY_ID, include_costs=True)
    summary = report["summaries"][0]
    ctx.check(
        "reporting_from_ledger",
        report["source"] == COMMERCIAL_TRANSACTIONS_COLLECTION
        and summary["revenue"] == 280
        and summary["supplier_costs"] == 120
        and summary["gross_margin"] == 160,
        "Ledger-derived revenue, cost, or margin is incorrect.",
    )
    safe_report = await ctx.service.reporting(AGENCY_ID, include_costs=False)
    safe_transactions = await ctx.service.list_transactions(
        AGENCY_ID, include_costs=False
    )
    ctx.check(
        "private_cost_projection",
        safe_report["summaries"][0]["supplier_costs"] is None
        and "supplier_costs" not in safe_report["profitability"][0],
        "Supplier cost leaked into the client-safe finance projection.",
    )
    ctx.check(
        "private_transaction_projection",
        all(
            item.get("reporting_category")
            not in {"supplier_cost", "agency_expense"}
            and "immutable_source_json" not in item
            for item in safe_transactions
        ),
        "Ledger timeline exposed private cost evidence or raw source snapshots.",
    )
    audits = await ctx.db.collection("audit_events").find_many(
        {"agency_id": AGENCY_ID}
    )
    ctx.check(
        "audit_evidence",
        len(audits) >= 8
        and all(
            event.get("metadata", {}).get("operational_record_mutated") is False
            for event in audits
        ),
        "Canonical finance mutations lack safe audit evidence.",
    )
    before = {
        name: await ctx.db.collection(name).count()
        for name in CANONICAL_FINANCE_COLLECTIONS
    }
    analysis = await ctx.service.migration_analysis()
    after = {
        name: await ctx.db.collection(name).count()
        for name in CANONICAL_FINANCE_COLLECTIONS
    }
    ctx.check(
        "migration_dry_run",
        analysis["dry_run"]
        and not analysis["write_mode_available"]
        and analysis["writes_performed"] == 0
        and before == after == analysis["before_counts"] == analysis["after_counts"],
        "Commercial migration analysis performed or exposed a write.",
    )
    readiness = commercial_ledger_readiness_metadata()
    ctx.check(
        "execution_boundaries",
        readiness["payment_gateway_execution_disabled"]
        and readiness["external_accounting_integration_disabled"]
        and readiness["operational_evidence_rewrite_disabled"],
        "A prohibited execution boundary is not registered.",
    )
    ctx.check(
        "writer_classification",
        set(FINANCE_WRITER_CLASSIFICATION)
        == {
            "canonical",
            "adapter",
            "projection",
            "compatibility",
            "deprecated",
            "demo",
        },
        "Finance writers are not fully classified.",
    )
    expected_ownership = {
        "commercial_transactions": CollectionOwnershipType.IMMUTABLE_SNAPSHOT,
        "payment_allocations": CollectionOwnershipType.IMMUTABLE_SNAPSHOT,
        "supplier_costs": CollectionOwnershipType.AGENCY_OWNED,
        "credit_notes": CollectionOwnershipType.AGENCY_OWNED,
        "refund_ledger_entries": CollectionOwnershipType.IMMUTABLE_SNAPSHOT,
        "exchange_ledger_entries": CollectionOwnershipType.IMMUTABLE_SNAPSHOT,
    }
    ctx.check(
        "persistence_ownership",
        all(
            get_collection_ownership(name).ownership == ownership
            for name, ownership in expected_ownership.items()
        ),
        "A canonical finance collection lacks the expected ownership registration.",
    )
    for relative in (
        "docs/architecture/canonical-commercial-ledger.md",
        "docs/architecture/invoice-lifecycle-contract.md",
        "docs/architecture/payment-allocation-contract.md",
        "docs/architecture/supplier-cost-contract.md",
        "docs/architecture/commercial-reporting-contract.md",
        "docs/architecture/refund-and-exchange-ledger.md",
        "frontend/src/pages/agency/FinanceDashboardPage.jsx",
        "frontend/src/pages/agency/SupplierCostsPage.jsx",
    ):
        ctx.check(
            f"source_{Path(relative).stem}",
            (ROOT / relative).is_file(),
            f"Required contract or UI source is missing: {relative}",
        )
    await assert_upstream_unchanged(ctx)
    return ctx.checks


async def run_invoice() -> list[str]:
    ctx = await seed()
    invoice = await ctx.service.create_invoice(
        AGENCY_ID,
        InvoiceCreate(
            client_id=CLIENT_ID,
            trip_id=TRIP_ID,
            booking_id=BOOKING_ID,
            booking_record_id=BOOKING_ID,
            booking_workspace_id=WORKSPACE_ID,
            offer_id="offer-ledger",
            accepted_offer_snapshot_id=SNAPSHOT_ID,
            currency="EUR",
        ),
        OWNER_ID,
    )
    await expect_ledger_error(
        ctx.service.issue_invoice(AGENCY_ID, invoice["id"], OWNER_ID),
        "EMPTY_INVOICE",
    )
    await expect_ledger_error(
        ctx.service.add_invoice_line(
            AGENCY_ID,
            invoice["id"],
            InvoiceLineItemCreate(
                ticket_id=TICKET_ID,
                line_type="ticket",
                description="Derived ticket line",
                quantity=2,
                unit_amount=50,
                total_amount=99,
                currency="EUR",
            ),
            OWNER_ID,
        ),
        "DERIVED_TOTAL_MISMATCH",
    )
    ticket_line = await ctx.service.add_invoice_line(
        AGENCY_ID,
        invoice["id"],
        InvoiceLineItemCreate(
            ticket_id=TICKET_ID,
            line_type="ticket",
            description="Derived ticket line",
            quantity=2,
            unit_amount=50,
            total_amount=100,
            currency="EUR",
        ),
        OWNER_ID,
    )
    await ctx.service.add_invoice_line(
        AGENCY_ID,
        invoice["id"],
        InvoiceLineItemCreate(
            line_type="tax",
            description="Airport tax",
            quantity=1,
            unit_amount=20,
            currency="EUR",
        ),
        OWNER_ID,
    )
    await expect_ledger_error(
        ctx.service.update_invoice_line(
            AGENCY_ID,
            invoice["id"],
            ticket_line["id"],
            {"ticket_id": "other-ticket"},
            OWNER_ID,
        ),
        "INVALID_LINEAGE",
    )
    await expect_ledger_error(
        ctx.service.add_invoice_line(
            AGENCY_ID,
            invoice["id"],
            InvoiceLineItemCreate(
                service_id="other-service",
                line_type="service",
                description="Cross-Agency service",
                quantity=1,
                unit_amount=1,
                currency="EUR",
            ),
            OWNER_ID,
        ),
        "INVALID_LINEAGE",
    )
    preserved_line = await ctx.db.collection("invoice_line_items").find_one(
        {"agency_id": AGENCY_ID, "id": ticket_line["id"]}
    )
    ctx.check(
        "draft_line_tenant_lineage_guard",
        preserved_line["ticket_id"] == TICKET_ID,
        "Rejected draft line update changed its canonical Ticket lineage.",
    )
    recalculated = await ctx.service.recalculate_invoice(AGENCY_ID, invoice["id"])
    ctx.check(
        "server_derived_totals",
        recalculated["subtotal_amount"] == 120
        and recalculated["tax_amount"] == 20
        and recalculated["total_amount"] == 120
        and recalculated["due_amount"] == 120,
        "Invoice totals were not derived from active lines.",
    )
    issued = await ctx.service.issue_invoice(AGENCY_ID, invoice["id"], OWNER_ID)
    ctx.check(
        "invoice_issue_transition",
        issued["status"] == "issued" and issued["issued_at"] is not None,
        "Draft Invoice did not transition to issued.",
    )
    await expect_ledger_error(
        ctx.service.update_invoice_line(
            AGENCY_ID,
            invoice["id"],
            ticket_line["id"],
            {"unit_amount": 60},
            OWNER_ID,
        ),
        "INVOICE_IMMUTABLE_AFTER_ISSUE",
    )
    credit = await ctx.service.create_credit_note(
        AGENCY_ID,
        CreditNoteCreate(
            invoice_id=invoice["id"],
            reason="Service correction",
            amount=30,
            invoice_line_item_id=ticket_line["id"],
        ),
        ACCOUNTANT_ID,
    )
    await ctx.service.issue_credit_note(AGENCY_ID, credit["id"], ACCOUNTANT_ID)
    await expect_ledger_error(
        ctx.service.create_credit_note(
            AGENCY_ID,
            CreditNoteCreate(
                invoice_id=invoice["id"],
                reason="Excess credit",
                amount=91,
            ),
            ACCOUNTANT_ID,
        ),
        "CREDIT_EXCEEDS_INVOICE",
    )
    remaining_credit = await ctx.service.create_credit_note(
        AGENCY_ID,
        CreditNoteCreate(
            invoice_id=invoice["id"],
            reason="Final concession",
            amount=90,
        ),
        ACCOUNTANT_ID,
    )
    await ctx.service.issue_credit_note(
        AGENCY_ID, remaining_credit["id"], ACCOUNTANT_ID
    )
    credited = await ctx.service.recalculate_invoice(AGENCY_ID, invoice["id"])
    ctx.check(
        "credit_note_lifecycle",
        credited["status"] == "credited"
        and credited["credited_amount"] == 120
        and credited["due_amount"] == 0,
        "Credit Notes did not produce the canonical credited state.",
    )
    cancel_invoice, _ = await create_invoice(ctx, total=40, line_type="service", ticket_id=None)
    cancelled = await ctx.service.cancel_invoice(
        AGENCY_ID,
        cancel_invoice["id"],
        OWNER_ID,
        "Duplicate client document.",
    )
    ctx.check(
        "reasoned_cancellation",
        cancelled["status"] == "cancelled"
        and cancelled["cancelled_at"] is not None,
        "Unpaid issued Invoice was not cancelled non-destructively.",
    )
    await expect_ledger_error(
        ctx.service.create_invoice(
            AGENCY_ID,
            InvoiceCreate(client_id="other-client", currency="EUR"),
            OWNER_ID,
        ),
        "INVALID_LINEAGE",
    )
    await expect_ledger_error(
        ctx.service.create_invoice(
            AGENCY_ID,
            InvoiceCreate(
                client_id=CLIENT_ID,
                trip_id=TRIP_ID,
                offer_id="other-offer",
                currency="EUR",
            ),
            OWNER_ID,
        ),
        "INVALID_LINEAGE",
    )
    try:
        InvoiceCreate(client_id=CLIENT_ID, currency="EUR", total_amount=999)
    except ValidationError:
        ctx.check(
            "grand_total_input_forbidden",
            True,
            "InvoiceCreate unexpectedly accepted a grand total.",
        )
    else:
        raise AssertionError("InvoiceCreate accepted a client-supplied grand total.")
    ctx.check(
        "canonical_lifecycle_values",
        INVOICE_LIFECYCLE
        == (
            "draft",
            "issued",
            "partially_paid",
            "paid",
            "cancelled",
            "credited",
        ),
        "Invoice lifecycle differs from the canonical contract.",
    )
    await assert_upstream_unchanged(ctx)
    return ctx.checks


async def run_payment() -> list[str]:
    ctx = await seed()
    invoice_a, line_a = await create_invoice(ctx, total=100)
    invoice_b, _ = await create_invoice(ctx, total=80, line_type="emd", ticket_id=None)
    payment_payload = PaymentRecordCreate(
        client_id=CLIENT_ID,
        status="received",
        method="bank_transfer",
        amount=150,
        currency="EUR",
        external_reference="BANK-LEDGER-001",
        idempotency_key="payment-ledger-001",
    )
    payment = await ctx.service.create_payment(
        AGENCY_ID, payment_payload, ACCOUNTANT_ID
    )
    allocation_a = await ctx.service.allocate_payment(
        AGENCY_ID,
        payment["id"],
        PaymentAllocationCreate(
            invoice_id=invoice_a["id"],
            amount=60,
            idempotency_key="allocation-ledger-a",
        ),
        ACCOUNTANT_ID,
    )
    retry = await ctx.service.allocate_payment(
        AGENCY_ID,
        payment["id"],
        PaymentAllocationCreate(
            invoice_id=invoice_a["id"],
            amount=60,
            idempotency_key="allocation-ledger-a",
        ),
        ACCOUNTANT_ID,
    )
    ctx.check(
        "allocation_idempotency",
        retry["id"] == allocation_a["id"],
        "Allocation retry created another record.",
    )
    await ctx.service.allocate_payment(
        AGENCY_ID,
        payment["id"],
        PaymentAllocationCreate(
            invoice_id=invoice_a["id"],
            invoice_line_item_id=line_a["id"],
            amount=40,
            idempotency_key="allocation-ledger-a-line",
        ),
        ACCOUNTANT_ID,
    )
    await ctx.service.allocate_payment(
        AGENCY_ID,
        payment["id"],
        PaymentAllocationCreate(
            invoice_id=invoice_b["id"],
            amount=50,
            idempotency_key="allocation-ledger-b",
        ),
        ACCOUNTANT_ID,
    )
    payment_after = await ctx.service.recalculate_payment(AGENCY_ID, payment["id"])
    invoice_a_after = await ctx.service.recalculate_invoice(
        AGENCY_ID, invoice_a["id"]
    )
    invoice_b_after = await ctx.service.recalculate_invoice(
        AGENCY_ID, invoice_b["id"]
    )
    ctx.check(
        "multi_invoice_partial_allocation",
        payment_after["allocated_amount"] == 150
        and payment_after["unallocated_amount"] == 0
        and invoice_a_after["status"] == "paid"
        and invoice_b_after["status"] == "partially_paid"
        and invoice_b_after["due_amount"] == 30,
        "Multi-Invoice or partial allocation balances are incorrect.",
    )
    payment_retry = await ctx.service.create_payment(
        AGENCY_ID, payment_payload, ACCOUNTANT_ID
    )
    ctx.check(
        "payment_idempotency_after_allocation",
        payment_retry["id"] == payment["id"],
        "Payment retry failed after its allocation changed balances.",
    )
    overflow = await ctx.service.create_payment(
        AGENCY_ID,
        PaymentRecordCreate(
            client_id=CLIENT_ID,
            status="received",
            amount=100,
            currency="EUR",
            idempotency_key="payment-overflow",
        ),
        ACCOUNTANT_ID,
    )
    await expect_ledger_error(
        ctx.service.allocate_payment(
            AGENCY_ID,
            overflow["id"],
            PaymentAllocationCreate(invoice_id=invoice_b["id"], amount=31),
            ACCOUNTANT_ID,
        ),
        "OVERALLOCATION",
    )
    await expect_ledger_error(
        ctx.service.allocate_payment(
            AGENCY_ID,
            overflow["id"],
            PaymentAllocationCreate(invoice_id=invoice_b["id"], amount=-1),
            ACCOUNTANT_ID,
        ),
        "INVALID_MONETARY_VALUE",
    )
    gbp_invoice, _ = await create_invoice(
        ctx, total=25, currency="GBP", line_type="service", ticket_id=None
    )
    await expect_ledger_error(
        ctx.service.allocate_payment(
            AGENCY_ID,
            overflow["id"],
            PaymentAllocationCreate(invoice_id=gbp_invoice["id"], amount=10),
            ACCOUNTANT_ID,
        ),
        "CURRENCY_MISMATCH",
    )
    cancelled_invoice, _ = await create_invoice(
        ctx, total=25, line_type="service", ticket_id=None
    )
    await ctx.service.cancel_invoice(
        AGENCY_ID,
        cancelled_invoice["id"],
        OWNER_ID,
        "No longer payable.",
    )
    await expect_ledger_error(
        ctx.service.allocate_payment(
            AGENCY_ID,
            overflow["id"],
            PaymentAllocationCreate(
                invoice_id=cancelled_invoice["id"], amount=10
            ),
            ACCOUNTANT_ID,
        ),
        "INVALID_INVOICE_LIFECYCLE",
    )
    await expect_ledger_error(
        ctx.service.allocate_payment(
            AGENCY_ID,
            overflow["id"],
            PaymentAllocationCreate(invoice_id="other-invoice", amount=10),
            ACCOUNTANT_ID,
        ),
        "INVOICE_NOT_FOUND",
    )
    draft_invoice = await ctx.service.create_invoice(
        AGENCY_ID,
        InvoiceCreate(
            client_id=CLIENT_ID,
            trip_id=TRIP_ID,
            booking_id=BOOKING_ID,
            currency="EUR",
        ),
        OWNER_ID,
    )
    await ctx.service.add_invoice_line(
        AGENCY_ID,
        draft_invoice["id"],
        InvoiceLineItemCreate(
            line_type="service",
            description="Draft-only service",
            quantity=1,
            unit_amount=10,
            currency="EUR",
        ),
        OWNER_ID,
    )
    pending_payment = await ctx.service.create_payment(
        AGENCY_ID,
        PaymentRecordCreate(
            invoice_id=draft_invoice["id"],
            client_id=CLIENT_ID,
            status="pending",
            amount=10,
            currency="EUR",
            idempotency_key="draft-invoice-pending-payment",
        ),
        ACCOUNTANT_ID,
    )
    await expect_ledger_error(
        ctx.service.mark_payment_received(
            AGENCY_ID, pending_payment["id"], ACCOUNTANT_ID
        ),
        "INVALID_INVOICE_LIFECYCLE",
    )
    pending_after = await ctx.db.collection("payment_records").find_one(
        {"agency_id": AGENCY_ID, "id": pending_payment["id"]}
    )
    received_posting = await ctx.db.collection(
        COMMERCIAL_TRANSACTIONS_COLLECTION
    ).find_one(
        {
            "agency_id": AGENCY_ID,
            "payment_record_id": pending_payment["id"],
            "entry_type": "payment_received",
        }
    )
    ctx.check(
        "received_transition_is_atomic_at_lifecycle_guard",
        pending_after["status"] == "pending" and received_posting is None,
        "Invalid payment receipt left partial ledger evidence.",
    )
    allocation_count = await ctx.db.collection(PAYMENT_ALLOCATIONS_COLLECTION).count(
        {"agency_id": AGENCY_ID, "payment_record_id": payment["id"]}
    )
    ctx.check(
        "allocation_count",
        allocation_count == 3,
        "Idempotent allocation created duplicate settlement evidence.",
    )
    await assert_upstream_unchanged(ctx)
    return ctx.checks


async def run_supplier_cost() -> list[str]:
    ctx = await seed()
    await create_invoice(ctx, total=300)
    cost = await ctx.service.create_supplier_cost(
        AGENCY_ID,
        SupplierCostCreate(
            supplier_reference="AIRLINE-NET-001",
            supplier_name="Example Airline",
            client_id=CLIENT_ID,
            trip_id=TRIP_ID,
            booking_id=BOOKING_ID,
            booking_workspace_id=WORKSPACE_ID,
            ticket_id=TICKET_ID,
            currency="EUR",
            description="Airline net fare",
            expected_cost_amount=100,
            actual_cost_amount=100,
        ),
        ACCOUNTANT_ID,
    )
    await expect_ledger_error(
        ctx.service.add_supplier_cost_line(
            AGENCY_ID,
            cost["id"],
            SupplierCostLineCreate(
                description="Cross-Agency Ticket cost",
                actual_amount=1,
                ticket_id="other-ticket",
            ),
            ACCOUNTANT_ID,
        ),
        "INVALID_LINEAGE",
    )
    await ctx.service.add_supplier_cost_line(
        AGENCY_ID,
        cost["id"],
        SupplierCostLineCreate(
            description="Agency handling expense",
            expected_amount=20,
            actual_amount=20,
            expense_category="agency_expense",
        ),
        ACCOUNTANT_ID,
    )
    ctx.check(
        "supplier_line_tenant_lineage_guard",
        await ctx.db.collection("supplier_cost_lines").count(
            {"agency_id": AGENCY_ID, "supplier_cost_id": cost["id"]}
        )
        == 2,
        "Rejected Supplier Cost line created cross-Agency accounting evidence.",
    )
    confirmed = await ctx.service.confirm_supplier_cost(
        AGENCY_ID, cost["id"], ACCOUNTANT_ID
    )
    confirmed_retry = await ctx.service.confirm_supplier_cost(
        AGENCY_ID, cost["id"], ACCOUNTANT_ID
    )
    ctx.check(
        "supplier_cost_confirmation_idempotent",
        confirmed_retry["id"] == confirmed["id"]
        and confirmed["posted_cost_amount"] == 120,
        "Confirmed Supplier Cost was duplicated or mis-totalled.",
    )
    await expect_ledger_error(
        ctx.service.add_supplier_cost_line(
            AGENCY_ID,
            cost["id"],
            SupplierCostLineCreate(
                description="Late destructive change",
                actual_amount=1,
            ),
            ACCOUNTANT_ID,
        ),
        "SUPPLIER_COST_IMMUTABLE",
    )
    report = await ctx.service.reporting(AGENCY_ID, include_costs=True)
    summary = report["summaries"][0]
    ctx.check(
        "cost_and_margin_reporting",
        summary["revenue"] == 300
        and summary["supplier_costs"] == 100
        and summary["agency_expenses"] == 20
        and summary["gross_margin"] == 180,
        "Supplier cost, agency expense, or margin is incorrect.",
    )
    await require_read(ctx.db, AGENCY_ID, {"id": AGENT_ID})
    await require_read(ctx.db, AGENCY_ID, {"id": READONLY_ID})
    await require_write(ctx.db, AGENCY_ID, {"id": OWNER_ID})
    await require_write(ctx.db, AGENCY_ID, {"id": ACCOUNTANT_ID})
    await require_cost_read(ctx.db, AGENCY_ID, {"id": OWNER_ID})
    await require_cost_read(ctx.db, AGENCY_ID, {"id": ACCOUNTANT_ID})
    await expect_http_forbidden(
        require_write(ctx.db, AGENCY_ID, {"id": AGENT_ID})
    )
    await expect_http_forbidden(
        require_write(ctx.db, AGENCY_ID, {"id": READONLY_ID})
    )
    await expect_http_forbidden(
        require_cost_read(ctx.db, AGENCY_ID, {"id": AGENT_ID})
    )
    await expect_http_forbidden(
        require_read(ctx.db, AGENCY_ID, {"id": PLATFORM_ID})
    )
    ctx.check(
        "centralized_finance_permissions",
        "edit_finance" in agency_permissions("agency_agent")
        and "edit_commercial_ledger"
        not in agency_permissions("agency_agent")
        and "view_supplier_costs" not in agency_permissions("agency_agent")
        and {
            "edit_finance",
            "edit_commercial_ledger",
            "view_supplier_costs",
            "view_margins",
        }.issubset(agency_permissions("agency_accountant")),
        "Finance permissions do not match the canonical role contract.",
    )
    safe_report = await ctx.service.reporting(AGENCY_ID, include_costs=False)
    ctx.check(
        "supplier_cost_privacy",
        safe_report["summaries"][0]["supplier_costs"] is None
        and "gross_margin" not in safe_report["profitability"][0],
        "Private cost or margin values leaked to a non-cost projection.",
    )
    ctx.check(
        "single_supplier_record",
        await ctx.db.collection(SUPPLIER_COSTS_COLLECTION).count(
            {"agency_id": AGENCY_ID}
        )
        == 1,
        "Supplier cost confirmation created a duplicate record.",
    )
    await assert_upstream_unchanged(ctx)
    return ctx.checks


async def run_refund() -> list[str]:
    ctx = await seed()
    invoice, _ = await create_invoice(ctx, total=100)
    payment = await ctx.service.create_payment(
        AGENCY_ID,
        PaymentRecordCreate(
            client_id=CLIENT_ID,
            status="received",
            amount=100,
            currency="EUR",
            idempotency_key="refund-source-payment",
        ),
        ACCOUNTANT_ID,
    )
    allocation = await ctx.service.allocate_payment(
        AGENCY_ID,
        payment["id"],
        PaymentAllocationCreate(
            invoice_id=invoice["id"],
            amount=100,
            idempotency_key="refund-source-allocation",
        ),
        ACCOUNTANT_ID,
    )
    original_payment = deepcopy(
        await ctx.db.collection("payment_records").find_one(
            {"agency_id": AGENCY_ID, "id": payment["id"]}
        )
    )
    payload = RefundLedgerEntryCreate(
        client_id=CLIENT_ID,
        trip_id=TRIP_ID,
        booking_id=BOOKING_ID,
        ticket_id=TICKET_ID,
        payment_record_id=payment["id"],
        payment_allocation_id=allocation["id"],
        commercial_source_type="ticket",
        commercial_source_id=TICKET_ID,
        amount=40,
        currency="EUR",
        reason="Reviewed ticket refund evidence.",
        idempotency_key="refund-ledger-001",
    )
    refund = await ctx.service.create_refund_entry(
        AGENCY_ID, payload, ACCOUNTANT_ID
    )
    retry = await ctx.service.create_refund_entry(
        AGENCY_ID, payload, ACCOUNTANT_ID
    )
    ctx.check(
        "refund_idempotency",
        retry["id"] == refund["id"],
        "Refund retry created another ledger entry.",
    )
    await expect_ledger_error(
        ctx.service.create_refund_entry(
            AGENCY_ID,
            RefundLedgerEntryCreate(
                **payload.model_dump(
                    exclude={"payment_allocation_id", "idempotency_key"}
                ),
                payment_allocation_id=None,
                idempotency_key="refund-missing-allocation",
            ),
            ACCOUNTANT_ID,
        ),
        "INCOMPLETE_REFUND_LINEAGE",
    )
    await expect_ledger_error(
        ctx.service.create_refund_entry(
            AGENCY_ID,
            RefundLedgerEntryCreate(
                **payload.model_dump(
                    exclude={
                        "payment_record_id",
                        "idempotency_key",
                    }
                ),
                payment_record_id="other-payment",
                idempotency_key="refund-other-tenant-payment",
            ),
            ACCOUNTANT_ID,
        ),
        "INVALID_LINEAGE",
    )
    await expect_ledger_error(
        ctx.service.create_refund_entry(
            AGENCY_ID,
            RefundLedgerEntryCreate(
                **payload.model_dump(
                    exclude={"commercial_source_id", "idempotency_key"}
                ),
                commercial_source_id="other-ticket",
                idempotency_key="refund-mismatched-source",
            ),
            ACCOUNTANT_ID,
        ),
        "CONTEXT_MISMATCH",
    )
    ctx.check(
        "refund_lineage_guard",
        await ctx.db.collection(REFUND_LEDGER_ENTRIES_COLLECTION).count(
            {"agency_id": AGENCY_ID}
        )
        == 1,
        "Rejected Refund references created accounting evidence.",
    )
    await expect_ledger_error(
        ctx.service.create_refund_entry(
            AGENCY_ID,
            RefundLedgerEntryCreate(
                **payload.model_dump(exclude={"amount", "idempotency_key"}),
                amount=41,
                idempotency_key="refund-ledger-001",
            ),
            ACCOUNTANT_ID,
        ),
        "IDEMPOTENCY_CONFLICT",
    )
    await expect_ledger_error(
        ctx.service.create_refund_entry(
            AGENCY_ID,
            RefundLedgerEntryCreate(
                **payload.model_dump(exclude={"amount", "idempotency_key"}),
                amount=61,
                idempotency_key="refund-ledger-overflow",
            ),
            ACCOUNTANT_ID,
        ),
        "REFUND_EXCEEDS_ALLOCATION",
    )
    current_payment = await ctx.db.collection("payment_records").find_one(
        {"agency_id": AGENCY_ID, "id": payment["id"]}
    )
    ctx.check(
        "original_payment_history_preserved",
        current_payment == original_payment,
        "Refund accounting altered original Payment evidence.",
    )
    ctx.check(
        "refund_posting_and_audit",
        await ctx.db.collection(REFUND_LEDGER_ENTRIES_COLLECTION).count(
            {"agency_id": AGENCY_ID}
        )
        == 1
        and bool(
            await ctx.db.collection(COMMERCIAL_TRANSACTIONS_COLLECTION).find_one(
                {
                    "agency_id": AGENCY_ID,
                    "refund_ledger_entry_id": refund["id"],
                }
            )
        )
        and bool(
            await ctx.db.collection("audit_events").find_one(
                {
                    "agency_id": AGENCY_ID,
                    "entity_type": "refund_ledger_entry",
                    "entity_id": refund["id"],
                }
            )
        ),
        "Refund lacks a canonical posting or audit record.",
    )
    await assert_upstream_unchanged(ctx)
    return ctx.checks


async def run_exchange() -> list[str]:
    ctx = await seed()
    payload = ExchangeLedgerEntryCreate(
        client_id=CLIENT_ID,
        trip_id=TRIP_ID,
        booking_id=BOOKING_ID,
        original_ticket_id=TICKET_ID,
        new_ticket_id=NEW_TICKET_ID,
        emd_id=EMD_ID,
        accepted_change_id="accepted-change-001",
        fare_difference_amount=25,
        tax_difference_amount=5,
        agency_fee_amount=10,
        supplier_fee_amount=3,
        emd_difference_amount=-2,
        exchange_fee_amount=4,
        currency="EUR",
        reason="Reviewed ticket exchange evidence.",
        idempotency_key="exchange-ledger-001",
    )
    exchange = await ctx.service.create_exchange_entry(
        AGENCY_ID, payload, ACCOUNTANT_ID
    )
    ctx.check(
        "server_derived_exchange_total",
        exchange["total_difference_amount"] == 45,
        "Exchange total was not derived from its accounting components.",
    )
    retry = await ctx.service.create_exchange_entry(
        AGENCY_ID, payload, ACCOUNTANT_ID
    )
    ctx.check(
        "exchange_idempotency",
        retry["id"] == exchange["id"],
        "Exchange retry created another ledger entry.",
    )
    await expect_ledger_error(
        ctx.service.create_exchange_entry(
            AGENCY_ID,
            ExchangeLedgerEntryCreate(
                **payload.model_dump(
                    exclude={"agency_fee_amount", "idempotency_key"}
                ),
                agency_fee_amount=11,
                idempotency_key="exchange-ledger-001",
            ),
            ACCOUNTANT_ID,
        ),
        "IDEMPOTENCY_CONFLICT",
    )
    await expect_ledger_error(
        ctx.service.create_exchange_entry(
            AGENCY_ID,
            ExchangeLedgerEntryCreate(
                **payload.model_dump(
                    exclude={"new_ticket_id", "idempotency_key"}
                ),
                new_ticket_id="other-ticket",
                idempotency_key="exchange-other-tenant",
            ),
            ACCOUNTANT_ID,
        ),
        "INVALID_LINEAGE",
    )
    await expect_ledger_error(
        ctx.service.create_exchange_entry(
            AGENCY_ID,
            ExchangeLedgerEntryCreate(
                **payload.model_dump(
                    exclude={"accepted_change_id", "idempotency_key"}
                ),
                accepted_change_id="other-accepted-change",
                idempotency_key="exchange-other-tenant-change",
            ),
            ACCOUNTANT_ID,
        ),
        "INVALID_LINEAGE",
    )
    await expect_ledger_error(
        ctx.service.create_exchange_entry(
            AGENCY_ID,
            ExchangeLedgerEntryCreate(
                **payload.model_dump(
                    exclude={"accepted_change_id", "idempotency_key"}
                ),
                accepted_change_id="draft-change-001",
                idempotency_key="exchange-unapproved-change",
            ),
            ACCOUNTANT_ID,
        ),
        "CHANGE_NOT_ACCEPTED",
    )
    ctx.check(
        "accepted_change_lineage_guard",
        await ctx.db.collection(EXCHANGE_LEDGER_ENTRIES_COLLECTION).count(
            {"agency_id": AGENCY_ID}
        )
        == 1,
        "Rejected accepted-change references created Exchange evidence.",
    )
    posting = await ctx.db.collection(COMMERCIAL_TRANSACTIONS_COLLECTION).find_one(
        {
            "agency_id": AGENCY_ID,
            "exchange_ledger_entry_id": exchange["id"],
        }
    )
    ctx.check(
        "exchange_posting",
        posting is not None
        and posting["amount"] == 45
        and posting["source_event_type"] == "exchange.recorded",
        "Exchange lacks its immutable commercial posting.",
    )
    ctx.check(
        "single_exchange_record",
        await ctx.db.collection(EXCHANGE_LEDGER_ENTRIES_COLLECTION).count(
            {"agency_id": AGENCY_ID}
        )
        == 1,
        "Idempotency did not preserve one Exchange record.",
    )
    await assert_upstream_unchanged(ctx)
    return ctx.checks


SUITES: dict[str, Callable[[], Awaitable[list[str]]]] = {
    "commercial-ledger": run_commercial_ledger,
    "invoice": run_invoice,
    "payment": run_payment,
    "supplier-cost": run_supplier_cost,
    "refund": run_refund,
    "exchange": run_exchange,
}


async def run_suite(name: str) -> list[str]:
    try:
        suite = SUITES[name]
    except KeyError as exc:
        raise ValueError(f"Unknown commercial ledger smoke suite: {name}") from exc
    checks = await suite()
    if not checks:
        raise AssertionError(f"{name} smoke executed no checks.")
    return checks
