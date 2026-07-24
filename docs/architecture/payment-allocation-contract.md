# Payment Allocation Contract

## Decision

`PaymentRecord` stores evidence that money was received or is pending.
`PaymentAllocation` stores how received value settles one or more Invoices or
positive Invoice lines. The original Payment remains intact.

## Rules

- amount must be positive;
- currency must be a three-letter code;
- only a `received` Payment may be allocated;
- Payment, Client, Invoice, and optional line must share Agency and context;
- Payment and Invoice currencies must match;
- an allocation cannot exceed the unallocated Payment balance;
- an allocation cannot exceed the Invoice due balance;
- a line allocation cannot exceed that positive line's remaining balance;
- discounts and non-positive lines cannot receive allocations;
- retries are idempotent and conflicting reuse of a key is rejected.

One Payment may have many allocations. One Invoice may be settled by many
Payments. Partial balances remain explicit.

## Reconciliation

`allocated_amount` and `unallocated_amount` are server-derived from posted
allocations. Invoice paid and due amounts are derived from the same records.
Reconciliation metadata may be updated, but the received amount, currency,
Client, and original evidence are immutable.

## Execution Boundary

Recording a Payment never charges a card, initiates a bank transfer, executes a
refund, or connects to a payment gateway. It is reviewed accounting evidence.
