# Passenger Workspace Foundation

Phase 41.2 introduces metadata-only passenger workspaces for operational travel work. A passenger workspace is an agency-scoped record that captures personal identity metadata, travel document metadata, loyalty and known traveler metadata, emergency contacts, medical/mobility/dietary/assistance/baggage/seating/language profiles, contact information, linked operational records, and internal notes.

This phase does not execute bookings, issue tickets, connect to GDS or NDC, process payments, integrate suppliers, use AI, send email or SMS, run background workers, call external APIs, automatically match passenger profiles, automatically validate documents, communicate with airlines, or automate passenger operations.

## Model

`PassengerWorkspace` records live in `passenger_workspaces` and store:

- `id`
- `agency_id`
- `operational_workspace_id`
- `passenger_reference`
- `passenger_status`
- `title`
- `first_name`
- `middle_name`
- `last_name`
- `preferred_name`
- `gender`
- `date_of_birth`
- `nationality`
- `citizenship`
- `passport_number`
- `passport_expiry`
- `passport_country`
- `identity_document_type`
- `loyalty_programs`
- `frequent_flyer_numbers`
- `known_traveler_numbers`
- `emergency_contact`
- `mobility_profile`
- `medical_profile`
- `dietary_profile`
- `assistance_profile`
- `baggage_profile`
- `seating_preferences`
- `language_preferences`
- `contact_email`
- `contact_phone`
- `linked_request_ids`
- `linked_trip_ids`
- `linked_offer_ids`
- `linked_booking_ids`
- `linked_ticket_ids`
- `linked_document_ids`
- `internal_notes`
- `created_at`
- `updated_at`

The model carries explicit safety metadata such as `metadata_only`, `passenger_workspace_metadata_only`, `booking_execution_disabled`, `ticket_issuance_disabled`, `gds_connectivity_disabled`, `gds_live_connectivity_disabled`, `ndc_connectivity_disabled`, `payment_processing_disabled`, `supplier_integrations_disabled`, `ai_disabled`, `ai_automation_disabled`, `email_disabled`, `email_sending_disabled`, `sms_disabled`, `sms_sending_disabled`, `background_workers_disabled`, `external_api_calls_disabled`, `automatic_profile_matching_disabled`, `automatic_document_validation_disabled`, `document_validation_disabled`, `airline_communication_disabled`, and `automation_disabled`.

## Collection And Indexes

MongoDB collection registration is additive only. Phase 41.2 registers `passenger_workspaces` with indexes for:

- `id`
- `passenger_reference`
- `agency_id` plus status, nationality, and citizenship
- `operational_workspace_id`
- passenger status
- nationality and citizenship
- assistance profile metadata
- date of birth and passport expiry
- linked request, trip, offer, booking, ticket, and document references
- created timestamp

No destructive migration is included.

## APIs

Platform metadata APIs:

- `GET /api/platform/passenger-workspaces`
- `GET /api/platform/passenger-workspaces/summary`
- `POST /api/platform/passenger-workspaces`
- `GET /api/platform/passenger-workspaces/{passenger_workspace_id}`
- `PUT /api/platform/passenger-workspaces/{passenger_workspace_id}`
- `DELETE /api/platform/passenger-workspaces/{passenger_workspace_id}`

Agency read-only APIs:

- `GET /api/agencies/{agency_id}/passenger-workspaces`
- `GET /api/agencies/{agency_id}/passenger-workspaces/summary`
- `GET /api/agencies/{agency_id}/passenger-workspaces/{passenger_workspace_id}`

Filters support status, nationality, citizenship, assistance profile text, travel date through the assigned operational workspace, and assigned operational workspace.

## UI

Platform Console:

- `/platform/passenger-workspaces`
- Module catalog label: `Passenger Workspaces`

Agency Workspace:

- `/agency/passenger-workspaces`
- Module catalog label: `Passenger Workspaces`
- Page title: `Passengers`

The UI displays passenger lists, filters, counts, passenger references, personal information, travel documents, loyalty memberships, medical profiles, mobility profiles, assistance profiles, dietary profiles, seating preferences, emergency contacts, linked requests, linked trips, linked bookings, linked tickets, linked documents, and internal notes. It does not expose booking, ticketing, payment, provider, AI, sending, profile matching, document validation, airline communication, automation, or execution controls.

## Readiness

Readiness section:

- `passenger_workspace_foundation`

Active phase:

- `phase_41_2_passenger_workspace_foundation`

Readiness counters include passenger workspace count, counts by status, nationality count, and citizenship count. These counts are informational only and do not gate deployment or runtime behavior.
