# Phase 54.6: Offer-to-Booking Handoff and Booking Readiness Foundation

Phase 54.6 adds a controlled, metadata-only handoff from accepted offer to booking workspace.

The handoff consumes frozen `offer_acceptances`, `trip_accepted_offer_snapshots`, and existing `booking_readiness_packages`. It must not recreate accepted commercial data from mutable offer records.

## Purpose

The handoff answers one operational question:

Is this accepted offer ready to become a booking workspace mirror?

It evaluates passenger, segment, service, pricing, policy, document, approval, payment, supplier, booking-mode, ticket, and EMD readiness metadata before staff create or open a booking workspace.

## Metadata Collections

- `offer_booking_handoffs`
- `offer_booking_handoff_checks`
- `offer_booking_handoff_mappings`
- `booking_execution_instructions`

These records are audit and planning metadata only.

## Readiness States

Handoff status values:

- `draft`
- `assessing`
- `blocked`
- `conditional`
- `ready`
- `handed_off`
- `booking_created`
- `failed`
- `cancelled`

Checks may be `pending`, `passed`, `warning`, or `blocked`.

## Canonical Routes

Agency routes:

- `GET /api/agencies/{agency_id}/booking-handoffs`
- `POST /api/agencies/{agency_id}/booking-handoffs`
- `GET /api/agencies/{agency_id}/booking-handoffs/{handoff_id}`
- `POST /api/agencies/{agency_id}/booking-handoffs/{handoff_id}/assess`
- `POST /api/agencies/{agency_id}/booking-handoffs/{handoff_id}/create-booking-workspace`
- `GET /api/agencies/{agency_id}/booking-handoffs/checks`
- `GET /api/agencies/{agency_id}/booking-handoffs/mappings`
- `GET /api/agencies/{agency_id}/booking-handoffs/instructions`

Platform routes are read-only diagnostics under:

- `GET /api/platform/booking-handoffs`
- `GET /api/platform/booking-handoffs/summary`
- `GET /api/platform/booking-handoffs/checks`
- `GET /api/platform/booking-handoffs/mappings`
- `GET /api/platform/booking-handoffs/instructions`

UI routes:

- `/agency/booking-handoffs`
- `/platform/booking-handoffs`

## Safety Boundary

This phase does not book, ticket, issue EMDs, charge, invoice, call providers, call GDS/NDC, call airline APIs, send messages, use AI, run workers, or execute supplier logic.

Booking workspace creation uses the existing metadata-only `BookingWorkspaceService.create_booking_workspace_from_readiness` path. It creates or reuses internal booking workspace metadata only.

## Trace Separation

The handoff stores internal traces and client-facing traces separately:

- `internal_trace_json` contains checks, warnings, required documents, SSR/OSI previews, and operational notes.
- `client_trace_json` contains only client-facing accepted-offer summary metadata.

This preserves accepted offer snapshots and prevents mutable offer records from becoming the source of booking truth.
