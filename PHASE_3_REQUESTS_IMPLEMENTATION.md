# Phase 3 Requests Implementation

## Goal

Add the first operational workflow object: agency-scoped travel requests connected to clients, passengers, requested services, intended itinerary segments, messages, tasks, and timeline events.

## Models Added

- `TravelRequest`
- `RequestPassenger`
- `RequestSegment`
- `RequestedService`
- `RequestMessage`
- `RequestTask`
- `RequestTimelineEvent`

Requests are valid without airline evaluation and may later produce offers, but offer creation is not implemented in this phase.

## Endpoints Added

Requests:

- `GET /api/agencies/{agency_id}/requests`
- `POST /api/agencies/{agency_id}/requests`
- `GET /api/agencies/{agency_id}/requests/{request_id}`
- `PUT /api/agencies/{agency_id}/requests/{request_id}`
- `POST /api/agencies/{agency_id}/requests/{request_id}/archive`
- `POST /api/agencies/{agency_id}/requests/{request_id}/restore`
- `POST /api/agencies/{agency_id}/requests/{request_id}/status`

Request children:

- `GET/POST/PUT/POST archive /api/agencies/{agency_id}/requests/{request_id}/passengers`
- `GET/POST/PUT/POST archive /api/agencies/{agency_id}/requests/{request_id}/segments`
- `GET/POST/PUT/POST archive /api/agencies/{agency_id}/requests/{request_id}/services`
- `GET/POST /api/agencies/{agency_id}/requests/{request_id}/messages`
- `GET/POST/PUT/POST complete /api/agencies/{agency_id}/requests/{request_id}/tasks`
- `GET /api/agencies/{agency_id}/requests/{request_id}/timeline`

## Frontend Routes Added

- `/agency/requests`
- `/agency/requests/new`
- `/agency/requests/:requestId`

Agency navigation now shows implemented items only:

- Dashboard
- Clients
- Passengers
- Requests

## Seed Data Added

- One request for the individual demo client.
- One request for the organization demo client.
- Existing Phase 2 passengers linked to requests.
- Two intended itinerary segments per seeded request.
- Two requested services per seeded request.
- Two request messages per seeded request.
- Two request tasks per seeded request.
- Timeline events per seeded request.

No offers, bookings, tickets, EMDs, invoices, payments, airline intelligence, or document generation records are seeded.

## Data Rules Implemented

- Request records are scoped by `agency_id`.
- Request passengers must belong to the same agency.
- If a client/passenger relationship is provided, it must connect the request client and passenger.
- Request passenger rows snapshot passenger display name, date of birth, and PTC.
- Segment origin/destination supports free text.
- Requested services may be request-level or passenger-specific.
- Passenger and service counts update when records are added or archived/cancelled.
- Status changes write audit and timeline events.

## Limitations

- No client portal request submission yet.
- No offer creation from request.
- No airline policy evaluation or intelligence hints.
- No real document uploads.
- No bookings, tickets, EMDs, invoices, or payments.
- Messages are request-scoped records, not email/WhatsApp integrations.
- Tasks are request-scoped operational tasks, not automation.

## Next Recommended Phase

Implement the manual offer builder using requests as optional source context, including up to three route alternatives, up to three fare bundles per route, and offer snapshots.
