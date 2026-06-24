# Phase 27 — Operational Request Builder V1

Phase 27 replaces the internal generic request form with a structured Operational Request Builder for AeroAssist assistance cases.

## Implemented

- Structured builder endpoint: `POST /api/agencies/{agency_id}/requests/builder`.
- Inline client creation from the builder with name plus email or phone.
- Inline passenger creation and existing passenger selection.
- Structured itinerary storage with trip type, route summary, segment rows, airline/flight placeholders, cabin/class, dates, and notes.
- Structured service categories with conditional detail payloads.
- Corrected Phase 27.1 mobility assistance structure with separate assistance code, optional boarding/transfer clarifiers, own mobility device details, and conditional battery fields.
- Service relationships to all passengers/all segments by default, stored as `passenger_ids`, `segment_ids`, and all-scope flags.
- Request `builder_payload_snapshot` preservation for audit/debug continuity.
- Request detail display for trip type and service detail summaries.
- Intake conversion alignment so converted intakes create placeholder passenger records when only passenger count exists and store structured service payloads.
- Smoke script: `backend/scripts/smoke_operational_request_builder.py`.

## Backend Model/API Changes

- `TravelRequest` now stores `trip_type` and `builder_payload_snapshot`.
- `RequestSegment` now supports arrival date/time, marketing airline, and operating airline fields.
- `RequestedService` now stores `detail_payload`, `passenger_ids`, `segment_ids`, and all-passenger/all-segment flags.
- The builder endpoint creates:
  - client profile when needed,
  - passenger profiles and client-passenger relationships when needed,
  - request passenger snapshot rows,
  - route segment rows,
  - requested service rows,
  - audit and timeline events.

## Frontend Builder

- `/agency/requests/new` now presents sections for:
  - client selection or inline client creation,
  - passenger selection or inline passenger creation,
  - trip type and route/segment rows,
  - service category selection with conditional fields,
  - priority/source/status and notes.
- After save, the user is sent to the operational request detail page.

## Intake/Public Alignment

- Public intake remains lightweight and safe.
- Intake conversion now populates structured request fields where possible:
  - trip type,
  - passenger placeholders from passenger count,
  - request passenger links,
  - requested services with detail payloads,
  - source intake linkage.

## Not Included

- No GDS/NDC/airline integration.
- No automatic pricing.
- No booking/PNR creation.
- No payment gateway.
- No automatic email or document delivery.
- No external provider calls.

## Known Limits

- Passenger date of birth is still required by the existing passenger profile model; inline passengers without DOB use a placeholder date for now.
- Service relationships default to all passengers/all segments in the V1 UI.
- Inline client creation without email uses an internal placeholder email because existing client profiles require `primary_email`.
- Builder V1 does not yet provide rich edit-in-place flows for all structured sections after creation.
- Mobility assistance does not yet perform airline-specific validation or reference-data-driven taxonomy checks.

## Next Recommended Phase

Phase 28 should harden operational request editing after creation: section-level edit flows, passenger matching/reconciliation, richer relation UI, and request work queues before adding external automation.
