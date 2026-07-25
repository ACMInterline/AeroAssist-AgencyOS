# Approval Routing Contract

## Purpose

Internal approvals govern Class C recommendations. They do not execute the
underlying commercial, lifecycle, finance, Portal, supplier, or external
action.

Approvals cover Offer delivery, fee and low-margin exceptions, Trip
confirmation, Booking results, Ticket/EMD exceptions, Invoice issue, Credit
Notes, Refunds, Exchanges, Portal publication, and external communications.

## Record

The canonical approval is represented by approval-required
`OperationalWorkItem` evidence. It stores Agency, type, source entity and
timeline lineage, requester, required permission, optional assigned approver,
status, immutable decision evidence, source work item, and bounded snapshot.

Statuses are `requested`, `assigned`, `approved`, `rejected`, `cancelled`, and
`expired`.

## Guards

The approver must be an active same-Agency member with the required permission.
Where separation is required, requester and approver cannot be the same
identity. Decisions require a reason, are optimistic-versioned, and become
immutable timeline and audit evidence. Rejection performs no action. Approval
still requires an explicit call to the canonical Product Kernel business
service. Portal identities cannot access internal approvals.
