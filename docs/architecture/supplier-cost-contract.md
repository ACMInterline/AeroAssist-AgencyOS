# Supplier Cost Contract

## Separation

`SupplierCost` is Agency-private cost evidence. It is separate from client
Invoice lines and is never exposed through client-facing projections.

A cost may reference the same Trip, Booking, Ticket, EMD, or Service as a
client charge without making the two records identical.

## Lifecycle

- `draft`: expected and actual lines may be reviewed;
- `confirmed`: the selected actual amount, or expected amount when actual is
  unavailable, is posted;
- `paid`: reserved for reviewed payment status;
- `cancelled`: retained without deleting its history.

Confirmed records are immutable. Additional corrections require new evidence,
not rewriting the confirmed source.

## Margin

Canonical reporting derives:

`gross margin = posted client revenue - posted supplier costs -
posted agency expenses`.

Supplier Cost lines tagged `agency_expense` post separately from ordinary
supplier cost. Draft values do not enter reporting.

## Visibility

Only Agency owners, admins, and accountants have supplier-cost and margin
visibility by default. Agents may prepare commercial work and see client-facing
finance status, but cannot mutate the ledger or view private supplier costs.
