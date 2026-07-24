# Invoice Lifecycle Contract

## Purpose

An Invoice is a client-facing commercial document derived from reviewed
commercial evidence. It is not a mutable grand-total field on a Booking.

## States

`draft -> issued -> partially_paid -> paid`

Terminal or corrective states are `cancelled` and `credited`.

- A new Invoice always starts as `draft`.
- Only a draft Invoice accepts line changes.
- Issue requires at least one active line and a positive server-derived total.
- Allocations move an issued Invoice to `partially_paid` or `paid`.
- Issued corrections use a Credit Note.
- An unpaid draft or issued Invoice may be cancelled with a reason.
- A fully credited Invoice becomes `credited`.
- Historical `overdue`, `voided`, and `archived` values remain read-compatible
  but are not new canonical write states.

## Derived Values

The server derives:

- line total from quantity and unit amount;
- subtotal and tax total from active lines;
- credited amount from issued Credit Notes;
- payable amount from invoice total less credits;
- paid amount from posted Payment Allocations;
- due amount from payable amount less allocations;
- lifecycle status from those balances.

Clients cannot submit or update a grand total, paid amount, or due amount.

## Lineage

Lines may reference a canonical Ticket, EMD, Service, Agency fee, Supplier fee,
manual fee, tax, discount, or adjustment. References must resolve within the
same Agency and match the Invoice context. Accepted-offer and Booking evidence
captured at Invoice creation remains a source snapshot; finance does not edit
it.

## Audit And Compatibility

Creation, line changes, issue, cancellation, payment allocation, and credit
actions produce actor-scoped audit evidence. The legacy `/void` route is an
explicit compatibility adapter to reasoned cancellation, not a destructive
void mutation.
