# Refund And Exchange Ledger

## Refunds

`RefundLedgerEntry` records accounting evidence for a Ticket refund, EMD
refund, or reviewed manual refund. Every canonical Refund links the original
Payment Allocation; the Payment is derived and verified from that allocation.
Refunds cannot exceed the linked allocation or original Payment after prior
non-cancelled refunds and never edit or delete the original Payment history.

Each refund stores source lineage, amount, currency, reason, status, actor,
posting time, and an idempotency key.

## Exchanges

`ExchangeLedgerEntry` records:

- original and replacement Ticket references;
- accepted operational change evidence and an optional EMD reference;
- fare and tax differences;
- Agency, supplier, EMD, and exchange fees;
- Booking and Trip lineage;
- reason, status, actor, currency, and idempotency.

The server derives the total exchange difference from its components. A
positive or negative difference is recorded as evidence; no fare recalculation
or external exchange is executed. Trip, Booking, both Tickets, and accepted
change evidence are mandatory for new canonical Exchange entries.

## Operational Boundary

After-sales, Ticket, and EMD workflows remain owners of operational decisions
and provider outcomes. The ledger references their evidence and records the
commercial consequence. It does not mutate coupons, issue or exchange
documents, authorize a refund, commit funds, or contact a supplier.
