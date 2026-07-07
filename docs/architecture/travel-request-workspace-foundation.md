# Travel Request Workspace Foundation

Phase 41.1 introduces metadata-only travel request workspaces inside the operational travel workspace layer. A request workspace is an agency-scoped record that captures requester, client/passenger, requested route, requested dates, service categories, passenger summary, budget, deadline, assignment, notes, and linked trip/offer/document metadata.

This phase does not execute bookings, issue tickets, connect to live GDS or NDC, process payments, send email or SMS, run AI automation, call external APIs, integrate suppliers, call live airlines, run background workers, automatically convert requests to trips, automatically create offers, or automate travel operations.

## Model

`TravelRequestWorkspace` records live in `travel_request_workspaces` and store:

- `id`
- `agency_id`
- `operational_workspace_id`
- `request_reference`
- `request_title`
- `request_type`
- `request_status`
- `request_priority`
- `client_id`
- `primary_passenger_id`
- `requester_name`
- `requester_email`
- `requester_phone`
- `requested_service_categories`
- `requested_origin`
- `requested_destination`
- `requested_departure_date`
- `requested_return_date`
- `passenger_count`
- `passenger_type_summary`
- `flexibility_notes`
- `special_service_notes`
- `budget_notes`
- `deadline`
- `assigned_agent`
- `internal_notes`
- `linked_trip_ids`
- `linked_offer_ids`
- `linked_document_ids`
- `created_at`
- `updated_at`

The model carries explicit safety metadata such as `metadata_only`, `travel_request_workspace_metadata_only`, `booking_execution_disabled`, `ticket_issuance_disabled`, `gds_live_connectivity_disabled`, `ndc_connectivity_disabled`, `payment_processing_disabled`, `email_sending_disabled`, `sms_sending_disabled`, `ai_automation_disabled`, `external_api_calls_disabled`, `supplier_integrations_disabled`, `live_airline_calls_disabled`, `background_workers_disabled`, `automatic_trip_creation_disabled`, `automatic_offer_creation_disabled`, and `automation_disabled`.

## Collection And Indexes

MongoDB collection registration is additive only. Phase 41.1 registers `travel_request_workspaces` with indexes for:

- `id`
- `request_reference`
- `agency_id` plus status, type, and priority
- `operational_workspace_id`
- status plus priority
- type
- assigned agent
- requested departure date
- deadline
- client and primary passenger
- linked trip, offer, and document references
- created timestamp

No destructive migration is included.

## APIs

Platform metadata APIs:

- `GET /api/platform/travel-request-workspaces`
- `GET /api/platform/travel-request-workspaces/summary`
- `POST /api/platform/travel-request-workspaces`
- `GET /api/platform/travel-request-workspaces/{request_workspace_id}`
- `PUT /api/platform/travel-request-workspaces/{request_workspace_id}`
- `DELETE /api/platform/travel-request-workspaces/{request_workspace_id}`

Agency read-only APIs:

- `GET /api/agencies/{agency_id}/travel-request-workspaces`
- `GET /api/agencies/{agency_id}/travel-request-workspaces/summary`
- `GET /api/agencies/{agency_id}/travel-request-workspaces/{request_workspace_id}`

Filters support agency, status, type, priority, assigned agent, departure date, and operational workspace where applicable.

## UI

Platform Console:

- `/platform/travel-request-workspaces`
- Module catalog label: `Travel Request Workspaces`

Agency Workspace:

- `/agency/travel-requests`
- Module catalog label: `Travel Requests`

The UI displays request lists, filters, counts, request references, requester details, client/passenger summaries, requested routes, requested dates, passenger summaries, requested services, special service notes, budget notes, deadlines, linked trips, linked offers, linked documents, internal notes, assigned agents, and metadata-only safety notices. It does not expose booking, ticketing, payment, provider, sending, conversion, offer generation, automation, or execution controls.

## Readiness

Readiness section:

- `travel_request_workspace_foundation`

Active phase:

- `phase_41_1_travel_request_workspace_foundation`

Readiness counters include request workspace count and counts by status, type, and priority. These counts are informational only and do not gate deployment or runtime behavior.
