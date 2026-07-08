# Booking Workspace Foundation

Phase 41.6 introduces metadata-only booking workspaces used throughout AeroAssist. This foundation extends the existing `booking_workspaces` collection so the older booking/PNR mirror foundation remains compatible while Platform and Agency users gain a safer operational booking metadata view.

This phase does not create live bookings, issue tickets, connect to GDS or NDC, call airline APIs, process payments, calculate fares, use AI, run background workers, automatically confirm bookings, automatically generate tickets, integrate external providers, call external APIs, or automate booking operations.

## Model

`BookingWorkspace` records in `booking_workspaces` now store booking workspace metadata such as:

- `id`
- `agency_id`
- `operational_workspace_id`
- `trip_workspace_id`
- `offer_workspace_id`
- `booking_reference`
- `booking_status`
- `booking_type`
- `booking_source`
- `booking_owner`
- `airline_pnr`
- `gds_record_locator`
- `supplier_reference`
- `booking_created_date`
- `booking_deadline`
- `passenger_ids`
- `flight_workspace_ids`
- `ticket_ids`
- `emd_ids`
- `ssr_ids`
- `osi_ids`
- `document_ids`
- `timeline_ids`
- `communication_ids`
- `payment_summary`
- `booking_summary`
- `operational_notes`
- `created_at`
- `updated_at`

The model carries explicit safety metadata such as `metadata_only`, `booking_workspace_metadata_only`, `booking_execution_disabled`, `live_booking_creation_disabled`, `ticket_issuance_disabled`, `gds_connectivity_disabled`, `ndc_connectivity_disabled`, `airline_apis_disabled`, `airline_api_calls_disabled`, `payment_processing_disabled`, `fare_calculation_disabled`, `ai_disabled`, `background_workers_disabled`, `automatic_booking_confirmation_disabled`, `automatic_ticket_generation_disabled`, `external_integrations_disabled`, `external_api_calls_disabled`, and `automation_disabled`.

## Collection And Indexes

MongoDB registration is additive only. Phase 41.6 extends `booking_workspaces` indexes for:

- operational workspace references
- trip workspace references
- offer workspace references
- booking references
- booking status
- booking owner
- airline PNR
- GDS record locator
- supplier reference
- booking created date
- booking deadline
- flight workspace references
- ticket references
- EMD references
- SSR references
- OSI references
- document references
- timeline references
- communication references

No destructive migration is included.

## APIs

Platform metadata APIs:

- `GET /api/platform/booking-workspaces`
- `GET /api/platform/booking-workspaces/summary`
- `POST /api/platform/booking-workspaces`
- `GET /api/platform/booking-workspaces/{booking_workspace_id}`
- `PUT /api/platform/booking-workspaces/{booking_workspace_id}`
- `DELETE /api/platform/booking-workspaces/{booking_workspace_id}`

Agency read-only metadata APIs:

- `GET /api/agencies/{agency_id}/booking-workspaces`
- `GET /api/agencies/{agency_id}/booking-workspaces/summary`
- `GET /api/agencies/{agency_id}/booking-workspaces/{booking_workspace_id}`

Filters support status, booking owner, airline, supplier, and booking date. Agency metadata views remain read-only. Existing explicit booking mirror action subroutes from the earlier booking foundation are not expanded by this phase.

## UI

Platform Console:

- `/platform/booking-workspaces`
- Module catalog label: `Booking Workspaces`

Agency Workspace:

- `/agency/booking-workspaces`
- Module catalog label: `Booking Workspaces`
- Page title: `Bookings`

The UI displays booking references, statuses, owners, airline PNRs, GDS locators, supplier references, passenger summaries, flight summaries, trip summaries, offer summaries, ticket links, EMD links, SSR links, OSI links, documents, timeline references, communications, payment summaries, booking summaries, and operational notes. It does not expose booking, ticketing, GDS/NDC, airline API, payment, fare calculation, AI, worker, automatic confirmation, automatic ticket generation, external provider, or automation controls.

## Readiness

Readiness section:

- `booking_workspace_foundation`

Active phase:

- `phase_41_6_booking_workspace_foundation`

Readiness counters include booking workspace count, counts by status, booking owner count, supplier count, airline count, operational workspace count, trip workspace count, and offer workspace count. These counts are informational only and do not gate deployment or runtime behavior.
