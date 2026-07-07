# Operational Travel Workspace Foundation

Phase 41.0 introduces metadata-only operational travel workspaces for agency travel operations. A workspace is an agency-scoped record that groups client, passenger, request, trip, offer, booking, ticket, document, priority, assignment, date, route, service, and notes metadata into one operational view.

This phase does not execute bookings, issue tickets, connect to live GDS or NDC, process payments, send email or SMS, run AI automation, call external APIs, integrate suppliers, call live airlines, run background workers, or automate travel operations.

## Model

`OperationalTravelWorkspace` records live in `operational_travel_workspaces` and store:

- `id`
- `agency_id`
- `workspace_reference`
- `workspace_title`
- `workspace_type`
- `workspace_status`
- `primary_client_id`
- `primary_passenger_id`
- `linked_request_ids`
- `linked_trip_ids`
- `linked_offer_ids`
- `linked_booking_ids`
- `linked_ticket_ids`
- `linked_document_ids`
- `priority`
- `assigned_team`
- `assigned_agent`
- `travel_start_date`
- `travel_end_date`
- `origin_summary`
- `destination_summary`
- `service_summary`
- `operational_notes`
- `created_at`
- `updated_at`

The model also carries explicit safety metadata such as `metadata_only`, `operational_workspace_metadata_only`, `booking_execution_disabled`, `ticket_issuance_disabled`, `gds_live_connectivity_disabled`, `ndc_connectivity_disabled`, `payment_processing_disabled`, `email_sending_disabled`, `sms_sending_disabled`, `ai_automation_disabled`, `external_api_calls_disabled`, `supplier_integrations_disabled`, `live_airline_calls_disabled`, `background_workers_disabled`, and `automation_disabled`.

## Collection And Indexes

MongoDB collection registration is additive only. Phase 41.0 registers `operational_travel_workspaces` with indexes for:

- `id`
- `workspace_reference`
- `agency_id` plus status, type, and priority
- status plus priority
- type
- assigned agent
- travel start/end dates
- primary client and passenger
- linked request, trip, offer, booking, ticket, and document references
- created timestamp

No destructive migration is included.

## APIs

Platform metadata APIs:

- `GET /api/platform/operational-travel-workspaces`
- `GET /api/platform/operational-travel-workspaces/summary`
- `POST /api/platform/operational-travel-workspaces`
- `GET /api/platform/operational-travel-workspaces/{workspace_id}`
- `PUT /api/platform/operational-travel-workspaces/{workspace_id}`
- `DELETE /api/platform/operational-travel-workspaces/{workspace_id}`

Agency read-only APIs:

- `GET /api/agencies/{agency_id}/operational-travel-workspaces`
- `GET /api/agencies/{agency_id}/operational-travel-workspaces/summary`
- `GET /api/agencies/{agency_id}/operational-travel-workspaces/{workspace_id}`

Filters support agency, status, type, priority, assigned agent, and travel date where applicable.

## UI

Platform Console:

- `/platform/operational-travel-workspaces`
- Module catalog label: `Operational Travel Workspaces`

Agency Workspace:

- `/agency/travel-workspaces`
- Module catalog label: `Travel Workspaces`

The UI displays workspace list cards/tables, filters, counts, workspace references, client/passenger summaries, linked requests, linked trips, linked offers, linked bookings, linked tickets, linked documents, operational notes, assigned team, assigned agent, travel dates, origin/destination summaries, and service summaries. It does not expose activation, booking, ticketing, payment, provider, sending, automation, or execution controls.

## Readiness

Readiness section:

- `operational_travel_workspace_foundation`

Active phase:

- `phase_41_0_operational_travel_workspace_foundation`

Readiness counters include workspace count and counts by status, type, and priority. These counts are informational only and do not gate deployment or runtime behavior.
