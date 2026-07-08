# Trip Workspace Foundation

Phase 41.4 introduces metadata-only trip workspaces for operational travel work. A trip workspace is an agency-scoped journey record that links operational workspaces, clients, passengers, flights, travel requests, offers, bookings, tickets, EMDs, documents, route metadata, travel dates, summaries, assignments, and operational notes.

This phase does not execute bookings, issue tickets, connect to GDS or NDC, call airline APIs, process payments, create invoices, use AI, run background workers, automatically generate trips, automatically generate itineraries, call external integrations, or automate journey operations.

## Model

`TripWorkspace` records live in `trip_workspaces` and store:

- `id`
- `agency_id`
- `operational_workspace_id`
- `trip_reference`
- `trip_status`
- `journey_type`
- `service_type`
- `client_id`
- `passenger_ids`
- `flight_workspace_ids`
- `travel_request_ids`
- `offer_ids`
- `booking_ids`
- `ticket_ids`
- `emd_ids`
- `document_ids`
- `departure_country`
- `destination_country`
- `departure_city`
- `destination_city`
- `origin_airport`
- `destination_airport`
- `departure_date`
- `return_date`
- `travel_duration`
- `passenger_count`
- `itinerary_summary`
- `baggage_summary`
- `service_summary`
- `operational_priority`
- `assigned_agent`
- `assigned_team`
- `operational_notes`
- `created_at`
- `updated_at`

The model carries explicit safety metadata such as `metadata_only`, `trip_workspace_metadata_only`, `booking_execution_disabled`, `ticket_issuance_disabled`, `gds_connectivity_disabled`, `ndc_connectivity_disabled`, `airline_apis_disabled`, `airline_api_calls_disabled`, `payment_processing_disabled`, `invoicing_disabled`, `ai_disabled`, `background_workers_disabled`, `automatic_trip_generation_disabled`, `automatic_itinerary_generation_disabled`, `itinerary_generation_disabled`, `external_integrations_disabled`, `external_api_calls_disabled`, and `automation_disabled`.

## Collection And Indexes

MongoDB collection registration is additive only. Phase 41.4 registers `trip_workspaces` with indexes for:

- `id`
- `trip_reference`
- `agency_id` plus status, departure country, destination country, departure date, assigned agent, and priority
- `operational_workspace_id`
- trip status, journey type, and service type
- client references
- passenger references
- flight workspace references
- travel request references
- offer, booking, ticket, EMD, and document references
- departure and destination countries
- departure and return dates
- created timestamp

No destructive migration is included.

## APIs

Platform metadata APIs:

- `GET /api/platform/trip-workspaces`
- `GET /api/platform/trip-workspaces/summary`
- `POST /api/platform/trip-workspaces`
- `GET /api/platform/trip-workspaces/{trip_workspace_id}`
- `PUT /api/platform/trip-workspaces/{trip_workspace_id}`
- `DELETE /api/platform/trip-workspaces/{trip_workspace_id}`

Agency read-only APIs:

- `GET /api/agencies/{agency_id}/trip-workspaces`
- `GET /api/agencies/{agency_id}/trip-workspaces/summary`
- `GET /api/agencies/{agency_id}/trip-workspaces/{trip_workspace_id}`

Filters support status, departure country, destination country, departure date, assigned agent, priority, and assigned operational workspace.

## UI

Platform Console:

- `/platform/trip-workspaces`
- Module catalog label: `Trip Workspaces`

Agency Workspace:

- `/agency/trip-workspaces`
- Module catalog label: `Trip Workspaces`
- Page title: `Trips`

The UI displays trip lists, filters, counts, trip references, journey type, service type, travel dates, origin, destination, passenger summary, flight summary, linked requests, linked offers, linked bookings, linked tickets, linked EMDs, linked documents, assigned team, and operational notes. It does not expose booking, ticketing, payment, provider, invoicing, AI, worker, automatic trip generation, automatic itinerary generation, external integration, automation, or execution controls.

## Readiness

Readiness section:

- `trip_workspace_foundation`

Active phase:

- `phase_41_4_trip_workspace_foundation`

Readiness counters include trip workspace count, counts by status, departure country count, destination country count, and priority count. These counts are informational only and do not gate deployment or runtime behavior.
