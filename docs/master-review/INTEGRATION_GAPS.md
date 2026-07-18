# Golden Path Integration Gaps

## Current position

The audited Golden Path is **BROKEN**. This is not because every component is absent. It is broken because three required handoffs do not exist and several working handoffs do not advance one correlated operational record.

The most important distinction is between:

- a field that can hold another record's ID;
- a screen that can display related records; and
- a governed transition that validates, persists, audits, and advances work.

Only the third closes an integration gap.

## Critical transition gaps

| ID | Transition | Observed implementation | Operational consequence | Evidence required to close the gap |
| --- | --- | --- | --- | --- |
| GP-01 | Ticket -> Passenger Services | No ticket-driven API, UI, mapping, audit, queue, or workflow transition exists. Service requirements originate at request/trip/booking level. | The stated Golden Path order cannot be executed. An agent cannot use a recorded ticket to create or advance its service obligations. | A canonical operating sequence and a correlated service-fulfillment action showing how booking/ticket/EMD evidence advances an existing service case without recreating the requirement. |
| GP-02 | Documents -> Financial Tracking | No API or UI derives finance state from a document. The implemented direction is invoice/payment state first, optional invoice rendering second. | A document cannot become an authoritative charge, payment, or balance. Attempting this chain encourages duplicate or unsupported finance entry. | A corrected path definition and an explicit, audited relationship between finance records and their rendered documents. |
| GP-03 | Financial Tracking -> After Sales | After-sales financial impacts have no invoice, invoice-line, payment, refund, credit, or reconciliation reference. | Agents must retype estimates and cannot prove which financial obligation a refund/change/claim affects. | Source financial mappings, immutable before/after financial snapshots, approval trace, and reconciliation evidence tied to the case. |

## Material warnings on working transitions

| ID | Transition | Gap | Agent impact |
| --- | --- | --- | --- |
| GP-04 | Client -> Passenger | `client_passenger_relationships` overlaps `client_passenger_links`; there is no common timeline/workflow event. | Relationship state can be interpreted differently by CRM, portal, and master-record functions. |
| GP-05 | Passenger -> Request | Request Builder persists intake before workflow and triage queue synchronization. | A valid request can temporarily be invisible to the operational queue or have no workflow owner. |
| GP-06 | Trip -> Offer | Offer workspace creation writes audit but no trip/offer timeline or workflow transition; `offer_workspaces` overlaps `offer_workspaces_v2`. | Agents and reports cannot rely on one authoritative offer lifecycle. |
| GP-07 | Offer -> Booking | The UI retains a direct `booking-workspaces/from-readiness` action alongside the richer booking-handoff path. | A booking can be created without the canonical handoff checks, mappings, and instruction trace. |
| GP-08 | Booking -> Ticket | Ticket state is split across legacy and current booking/ticket families; recording a ticket does not atomically complete queue/workflow work. | A ticket can exist while booking workflow still appears incomplete, or vice versa. |
| GP-09 | Passenger Services -> Documents | Service-context rendering creates output but does not update `document_workspaces`, service readiness, queue work, or workflow stage. | The agency can produce a file while the system continues to report the document as missing or unresolved. |

## Cross-cutting integration gaps

### GP-10: No canonical record family through the chain

The transition path crosses overlapping representations:

- client/passenger relationships: `client_passenger_relationships` and `client_passenger_links`;
- offers: `offer_workspaces` and `offer_workspaces_v2`;
- bookings: `bookings`, `booking_workspaces`, and `booking_records`;
- tickets: `ticket_records` and `ticket_workspaces`;
- documents: `document_workspaces`, `document_render_jobs`, and `rendered_documents`.

These can serve different purposes, but the handoffs do not consistently declare which record is authoritative and how state synchronizes.

### GP-11: No end-to-end correlation ledger

Audit history is distributed across `audit_events`, request timelines, trip timelines, booking timelines, ticket/EMD timelines, render-job records, and operational timelines. Several transitions write only actor fields. There is no single correlation identifier that allows an operator or reviewer to reconstruct the complete case from client linkage through after-sales resolution.

### GP-12: Queue and workflow state are not transactionally aligned

Request triage is synchronized later. Trip-to-offer and booking-to-ticket do not atomically advance queue/workflow state. Document rendering does not close document work. The result can be valid domain data with stale operational work still shown as actionable.

### GP-13: Manual external-result recording lacks reconciliation

Booking and ticket operations correctly avoid pretending to execute providers, but the manual result path does not consistently require source evidence, provider reference validation, or a reconciliation state. This makes an operator-entered number sufficient to imply an issued ticket without proving the external result.

### GP-14: Passenger service fulfillment is not a continuous thread

Service requirements can be collected and evaluated, but ticket, EMD, documents, approvals, airport handling, and final readiness do not advance one clearly owned fulfillment record. Optional IDs across workspaces do not create lifecycle continuity.

### GP-15: Finance remains booking-centric and isolated from servicing

Invoices and payments have useful booking-level operations, but modern booking workspace records and after-sales cases do not share an authoritative financial impact chain. Refund, exchange, credit, and residual-value work therefore remains advisory/manual rather than reconciled.

### GP-16: The current end-to-end smoke is an assessment, not a transaction test

`smoke_end_to_end_operational_workflow_maturity_foundation.py` exercises isolated maturity templates. Its service reports that no production record was persisted. It therefore does not prove that one correlated case can traverse the actual APIs or that failures roll back safely.

## What the product can safely claim today

- A client can be associated with a passenger.
- A passenger can be captured in a request.
- A request can be converted into a trip with strong mappings and auditability.
- A trip can open an offer workspace.
- An accepted offer can be assessed and handed to a booking workspace.
- An externally completed booking/ticket result can be recorded manually.
- A document can be rendered from passenger-service request context.
- After-sales cases can organize tasks, workflow, timeline, decisions, communications, and estimated impacts.

It cannot safely claim that those actions form one complete, reconciled Golden Path through passenger-service fulfillment, documents, finance, and after sales.

## Acceptance evidence for a future re-audit

This audit should change to PASS only when a single isolated agency case can demonstrate all of the following through actual application APIs and UI actions:

1. One correlation trace spans every handoff.
2. Every state-changing action has an authoritative owner and agency boundary check.
3. Queue, workflow, timeline, and audit state agree after each action.
4. Passenger-service requirements persist from intake through confirmed fulfillment.
5. Generated and received documents reconcile to operational document requirements.
6. Invoice/payment state links to after-sales impacts and settlement without re-entry.
7. Idempotent retries do not duplicate trips, acceptances, bookings, tickets, documents, charges, or cases.
8. Failure at a handoff leaves an explicit recoverable state rather than partial silent progress.
9. Internal notes and client-visible content remain separated at every transition.
10. The test proves actual persisted transitions, not simulated maturity scores.
