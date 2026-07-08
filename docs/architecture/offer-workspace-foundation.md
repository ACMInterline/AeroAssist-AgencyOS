# Offer Workspace Foundation

Phase 41.5 introduces metadata-only offer workspaces for preparing travel proposals. This foundation uses the additive `offer_workspaces_v2` collection so it does not replace the existing offer builder workflow stored in `offer_workspaces`.

This phase does not execute bookings, issue tickets, process payments, connect to GDS or NDC, call airline APIs, calculate fares, generate AI itineraries, integrate suppliers, call external APIs, automatically convert bookings, run background workers, or automate offer operations.

## Model

`OfferWorkspaceV2` records live in `offer_workspaces_v2` and store:

- `id`
- `agency_id`
- `operational_workspace_id`
- `trip_workspace_id`
- `offer_reference`
- `offer_status`
- `offer_type`
- `client_id`
- `passenger_ids`
- `flight_workspace_ids`
- `offer_title`
- `offer_summary`
- `destination_summary`
- `itinerary_summary`
- `pricing_summary`
- `currency`
- `total_price`
- `taxes_summary`
- `fees_summary`
- `ancillary_summary`
- `baggage_summary`
- `seat_summary`
- `meal_summary`
- `hotel_summary`
- `transfer_summary`
- `insurance_summary`
- `validity_date`
- `assigned_agent`
- `agent_notes`
- `customer_notes`
- `internal_notes`
- `linked_booking_ids`
- `linked_ticket_ids`
- `linked_document_ids`
- `created_at`
- `updated_at`

The model carries explicit safety metadata such as `metadata_only`, `offer_workspace_metadata_only`, `booking_execution_disabled`, `ticket_issuance_disabled`, `payment_processing_disabled`, `gds_connectivity_disabled`, `ndc_connectivity_disabled`, `airline_apis_disabled`, `airline_api_calls_disabled`, `fare_calculation_engines_disabled`, `fare_calculation_disabled`, `live_pricing_disabled`, `ai_itinerary_generation_disabled`, `supplier_integrations_disabled`, `external_api_calls_disabled`, `automatic_booking_conversion_disabled`, `background_workers_disabled`, and `automation_disabled`.

## Collection And Indexes

MongoDB collection registration is additive only. Phase 41.5 registers `offer_workspaces_v2` with indexes for:

- `id`
- `offer_reference`
- `agency_id` plus status, validity, client, destination, assigned agent, and price
- `operational_workspace_id`
- `trip_workspace_id`
- offer status and type
- client references
- passenger references
- flight workspace references
- currency and total price
- validity date
- linked booking, ticket, and document references
- created timestamp

No destructive migration is included.

## APIs

Platform metadata APIs:

- `GET /api/platform/offer-workspaces`
- `GET /api/platform/offer-workspaces/summary`
- `POST /api/platform/offer-workspaces`
- `GET /api/platform/offer-workspaces/{offer_workspace_id}`
- `PUT /api/platform/offer-workspaces/{offer_workspace_id}`
- `DELETE /api/platform/offer-workspaces/{offer_workspace_id}`

Agency read-only metadata APIs:

- `GET /api/agencies/{agency_id}/offer-workspaces-v2`
- `GET /api/agencies/{agency_id}/offer-workspaces-v2/summary`
- `GET /api/agencies/{agency_id}/offer-workspaces-v2/{offer_workspace_id}`

The v2 agency API path avoids colliding with the existing `/api/agencies/{agency_id}/offer-workspaces` offer builder workflow. Filters support status, validity date, client, destination, price range, assigned agent, and trip workspace.

## UI

Platform Console:

- `/platform/offer-workspaces`
- Module catalog label: `Offer Workspaces`

Agency Workspace:

- `/agency/offer-workspaces`
- Module catalog label: `Offer Workspaces`
- Page title: `Offers`

The UI displays offer lists, filters, counts, offer references, trip summary, passenger summary, flight summary, pricing summary, taxes, fees, ancillary services, baggage, seats, meals, hotels, transfers, insurance, validity, linked bookings, linked tickets, linked documents, agent notes, customer notes, and internal notes. It does not expose booking, ticketing, payment, provider, fare calculation, AI itinerary generation, supplier integration, external API, booking conversion, worker, automation, or execution controls.

## Readiness

Readiness section:

- `offer_workspace_foundation`

Active phase:

- `phase_41_5_offer_workspace_foundation`

Readiness counters include offer workspace count, counts by status, offer type count, currency count, destination count, and assigned agent count. These counts are informational only and do not gate deployment or runtime behavior.
