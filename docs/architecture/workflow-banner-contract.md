# Workflow Banner Contract

## Purpose

The shared workflow banner tells an operator where a record sits, what is
complete, what needs attention, and where to continue. It is a read projection
with guarded links or callbacks; it does not own lifecycle state.

## Required Content

Where applicable, `WorkflowContinuityPanel` displays:

- breadcrumbs and current record
- current stage
- completed stages
- next action
- deadline
- validation state
- warnings
- blockers
- related records
- previous step
- next step
- timeline link

Missing optional values are stated plainly, for example "No deadline
recorded." A blocker disables or withholds an invalid action and explains why.
The component must not synthesize a successful status.

## Covered Operational Surfaces

The shared banner is used across Request, Client, Passenger, Trip, Offer,
Booking, Ticket, EMD, Passenger Service, Document, Invoice, conversion,
booking-handoff, and after-sales workspaces.

## Detail Page Order

Operational detail pages should use this reading order when the sections
apply:

1. Summary
2. Workflow and validation
3. Related records
4. Timeline
5. Communications
6. Documents
7. Financial information
8. Advanced details

Technical snapshots and raw state belong in collapsed Advanced details.

## Safety Rules

- Lifecycle state remains owned by the canonical backend model and service.
- Next actions call existing authorized routes or callbacks.
- A banner cannot bypass Agency membership, permissions, validation guards, or
  Portal mapping.
- Client-facing and internal messages remain separate.
- Accepted Offer and downstream historical snapshots remain immutable.
- No provider, booking, ticketing, payment, or external messaging execution is
  introduced by workflow guidance.
