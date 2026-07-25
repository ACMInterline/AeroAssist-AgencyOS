# Commercial Reporting Contract

## Source

Revenue, supplier cost, agency expense, gross margin, outstanding receivables,
unallocated Payments, refund exposure, exchange exposure, Booking
profitability, and Trip profitability are projections over posted
`commercial_transactions`.

Operational records alone are never recomputed into accounting results.
Draft Invoices and unconfirmed Supplier Costs are excluded.

## Scope

Every query is Agency-scoped and may be narrowed to a Trip or Booking. Currency
ledgers remain separate; values in different currencies are not silently
combined.

## Visibility

Users with `view_finance` receive revenue, settlement, and exposure summaries.
Supplier costs, agency expenses, and margin are omitted unless the active
Agency membership grants the private-cost permissions. Portal projections
continue to expose only their existing client-safe Invoice and Payment views.

## Interpretation

Reports describe recorded evidence, not bank balances, statutory accounts,
tax filings, live supplier balances, or payment-provider state. Unknown or
missing historical postings remain migration warnings rather than inferred
truth.
