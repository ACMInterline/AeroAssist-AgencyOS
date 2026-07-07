# Flight Workspace Foundation

Phase 41.3 introduces metadata-only flight workspaces for operational travel work. A flight workspace is an agency-scoped record that captures airline, flight number, carrier, airport, terminal, schedule, aircraft, cabin, booking class, fare family, baggage, connection, stopover, elapsed time, operating day, passenger, linked operational record, and notes metadata.

This phase does not execute bookings, search live flights, connect to GDS or NDC, call airline APIs, process payments, issue tickets, synchronize schedules, call external APIs, use AI, run background workers, automatically generate routes, validate flights, look up airlines, update live schedules, or automate flight operations.

## Model

`FlightWorkspace` records live in `flight_workspaces` and store:

- `id`
- `agency_id`
- `operational_workspace_id`
- `flight_reference`
- `flight_status`
- `flight_type`
- `travel_direction`
- `airline_code`
- `airline_name`
- `marketing_carrier`
- `operating_carrier`
- `flight_number`
- `operating_flight_number`
- `departure_airport`
- `arrival_airport`
- `departure_terminal`
- `arrival_terminal`
- `departure_datetime`
- `arrival_datetime`
- `aircraft_type`
- `cabin_class`
- `booking_class`
- `fare_family`
- `baggage_summary`
- `connection_summary`
- `stopover_summary`
- `elapsed_travel_time`
- `operating_days`
- `passenger_ids`
- `linked_request_ids`
- `linked_trip_ids`
- `linked_offer_ids`
- `linked_booking_ids`
- `linked_ticket_ids`
- `linked_document_ids`
- `operational_notes`
- `created_at`
- `updated_at`

The model carries explicit safety metadata such as `metadata_only`, `flight_workspace_metadata_only`, `booking_execution_disabled`, `live_flight_search_disabled`, `flight_search_disabled`, `gds_connectivity_disabled`, `ndc_connectivity_disabled`, `airline_apis_disabled`, `airline_api_calls_disabled`, `payment_disabled`, `payment_processing_disabled`, `ticket_issuance_disabled`, `schedule_synchronization_disabled`, `external_api_calls_disabled`, `ai_disabled`, `background_workers_disabled`, `automatic_route_generation_disabled`, `flight_validation_disabled`, `airline_lookups_disabled`, `live_schedule_updates_disabled`, and `automation_disabled`.

## Collection And Indexes

MongoDB collection registration is additive only. Phase 41.3 registers `flight_workspaces` with indexes for:

- `id`
- `flight_reference`
- `agency_id` plus status, airline, departure airport, and arrival airport
- `operational_workspace_id`
- flight status and type
- airline code
- departure and arrival airports
- departure and arrival datetimes
- cabin and booking class
- passenger references
- linked request, trip, offer, booking, ticket, and document references
- created timestamp

No destructive migration is included.

## APIs

Platform metadata APIs:

- `GET /api/platform/flight-workspaces`
- `GET /api/platform/flight-workspaces/summary`
- `POST /api/platform/flight-workspaces`
- `GET /api/platform/flight-workspaces/{flight_workspace_id}`
- `PUT /api/platform/flight-workspaces/{flight_workspace_id}`
- `DELETE /api/platform/flight-workspaces/{flight_workspace_id}`

Agency read-only APIs:

- `GET /api/agencies/{agency_id}/flight-workspaces`
- `GET /api/agencies/{agency_id}/flight-workspaces/summary`
- `GET /api/agencies/{agency_id}/flight-workspaces/{flight_workspace_id}`

Filters support status, airline, departure airport, arrival airport, departure date, cabin class, booking class, and assigned operational workspace.

## UI

Platform Console:

- `/platform/flight-workspaces`
- Module catalog label: `Flight Workspaces`

Agency Workspace:

- `/agency/flight-workspaces`
- Module catalog label: `Flight Workspaces`
- Page title: `Flights`

The UI displays flight lists, filters, counts, flight references, airline, flight number, marketing carrier, operating carrier, departure, arrival, terminals, schedule, cabin, booking class, fare family, aircraft, baggage summary, connection summary, stopover summary, passengers, linked requests, linked trips, linked offers, linked bookings, linked tickets, linked documents, and operational notes. It does not expose booking, ticketing, payment, provider, search, schedule sync, AI, route generation, validation, external API, airline lookup, live schedule update, automation, or execution controls.

## Readiness

Readiness section:

- `flight_workspace_foundation`

Active phase:

- `phase_41_3_flight_workspace_foundation`

Readiness counters include flight workspace count, counts by status, airline count, departure airport count, arrival airport count, and cabin count. These counts are informational only and do not gate deployment or runtime behavior.
