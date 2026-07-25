# Canonical Commercial Ledger

## Decision

`CommercialLedger` is the sole accounting aggregate for Agency commercial
facts. It consumes immutable evidence from the canonical operational chain:

`TravelRequest -> OfferWorkspace -> OfferAcceptance ->
TripAcceptedOfferSnapshot -> TripDossier -> BookingRecord ->
TicketRecord / EMDRecord`.

Finance is downstream. A ledger posting may reference those records, but it
must never update them.

## Ownership

The canonical record chain is:

`CommercialLedger -> CommercialTransaction -> Invoice -> InvoiceLineItem ->
PaymentAllocation -> SupplierCost -> SupplierCostLine -> CreditNote ->
CreditNoteLine -> RefundLedgerEntry -> ExchangeLedgerEntry`.

Existing `invoices`, `invoice_line_items`, and `payment_records` collections
remain in place and are extended. The ledger does not create replacement
invoice or payment families.

| Concern | Canonical owner | Collection |
|---|---|---|
| Currency ledger | `CommercialLedger` | `commercial_ledgers` |
| Immutable posting | `CommercialTransaction` | `commercial_transactions` |
| Client charge document | `Invoice` | `invoices` |
| Client charge detail | `InvoiceLineItem` | `invoice_line_items` |
| Settlement application | `PaymentAllocation` | `payment_allocations` |
| Private supplier expense | `SupplierCost` | `supplier_costs` |
| Supplier expense detail | `SupplierCostLine` | `supplier_cost_lines` |
| Non-destructive credit | `CreditNote` | `credit_notes` |
| Credit detail | `CreditNoteLine` | `credit_note_lines` |
| Refund accounting evidence | `RefundLedgerEntry` | `refund_ledger_entries` |
| Exchange accounting evidence | `ExchangeLedgerEntry` | `exchange_ledger_entries` |

## Posting Contract

Every `CommercialTransaction` is Agency-scoped, currency-specific,
idempotent, append-only accounting evidence. It records:

- source event type and ID;
- posting time and actor;
- immutable source snapshot and hash;
- relevant Client, Trip, Booking, Ticket, EMD, accepted snapshot, Invoice,
  Payment, Supplier Cost, Credit, Refund, or Exchange references;
- reporting category, direction, and signed amount.

Posted entries are not edited to make later events appear simpler. Corrections
use another governed commercial record and another posting.

## Writer Classification

- **Canonical:** `canonical_commercial_ledger_service.py`.
- **Adapter:** Agency finance routes delegate writes to the canonical service.
- **Projection:** Finance, Invoice, Payment, Supplier Cost, Trip, and Booking
  screens read canonical results.
- **Compatibility:** historical refund/exchange and after-sales records remain
  operational evidence; they do not post accounting truth automatically.
- **Deprecated:** monetary summary fields on legacy Booking records remain
  readable but are not recalculated by canonical finance writes.
- **Demo:** pilot seed records are sample data, not production postings.

## Security

Every Agency route requires an active same-Agency staff membership. Owners,
admins, and accountants receive `edit_commercial_ledger` and may mutate
ledger-backed finance. Agents retain the older `edit_finance` permission needed
by non-ledger after-sales workflows, but do not receive
`edit_commercial_ledger`, supplier-cost, or margin access. Read-only users may
read client-safe commercial status. Platform roles do not bypass Agency
membership.

## Safety Boundary

The ledger records reviewed manual evidence only. It does not execute payment,
refund, exchange, booking, ticket, or EMD actions; call a provider; synchronize
external accounting software; infer missing commercial truth; or migrate
historical data automatically.
