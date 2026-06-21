# Phase 2 CRM Implementation

## Goal

Implement the travel-specific CRM foundation for agency-owned clients, passengers, and many-to-many client/passenger relationships.

## Models Added

- `ClientProfile`
- `PassengerProfile`
- `ClientPassengerRelationship`
- `PassengerMergeAudit`

Client records represent the agency account/contact relationship. Passenger records represent travelers. A client may manage many passengers, and a passenger may be associated with multiple clients through explicit relationship permissions.

## Endpoints Added

Clients:

- `GET /api/agencies/{agency_id}/clients`
- `POST /api/agencies/{agency_id}/clients`
- `GET /api/agencies/{agency_id}/clients/{client_id}`
- `PUT /api/agencies/{agency_id}/clients/{client_id}`
- `POST /api/agencies/{agency_id}/clients/{client_id}/archive`
- `POST /api/agencies/{agency_id}/clients/{client_id}/restore`

Passengers:

- `GET /api/agencies/{agency_id}/passengers`
- `POST /api/agencies/{agency_id}/passengers`
- `GET /api/agencies/{agency_id}/passengers/{passenger_id}`
- `PUT /api/agencies/{agency_id}/passengers/{passenger_id}`
- `POST /api/agencies/{agency_id}/passengers/{passenger_id}/archive`
- `POST /api/agencies/{agency_id}/passengers/{passenger_id}/restore`
- `POST /api/agencies/{agency_id}/passengers/{passenger_id}/merge`

Relationships:

- `GET /api/agencies/{agency_id}/client-passenger-relationships`
- `POST /api/agencies/{agency_id}/client-passenger-relationships`
- `PUT /api/agencies/{agency_id}/client-passenger-relationships/{relationship_id}`
- `POST /api/agencies/{agency_id}/client-passenger-relationships/{relationship_id}/archive`
- `GET /api/agencies/{agency_id}/clients/{client_id}/passengers`
- `GET /api/agencies/{agency_id}/passengers/{passenger_id}/clients`

## Frontend Routes Added

- `/agency/clients`
- `/agency/clients/:clientId`
- `/agency/passengers`
- `/agency/passengers/:passengerId`

Agency navigation now shows only implemented Phase 2 items:

- Dashboard
- Clients
- Passengers

## Seed Data Added

- Individual client with self passenger relationship.
- Organization client with employee passenger relationship.
- Family/household client with guardian relationship.
- Three passenger profiles.

No requests, offers, bookings, tickets, EMDs, invoices, payments, airline intelligence, or document workflows are seeded.

## Passenger Merge Behavior

- Same agency only.
- Requires `agency_owner` or `agency_admin`, except platform owner/admin support override.
- Source passenger status becomes `duplicate_merged`.
- Source passenger receives `merged_into_passenger_id`.
- Source relationships are copied to the target passenger if they do not duplicate an existing target relationship.
- Duplicate source relationships are archived.
- Merge creates `PassengerMergeAudit` and an audit event.
- No future booking/document records are merged because those modules do not exist yet.

## Limitations

- Production authentication and portal account mapping are not implemented.
- Client portal remains a safe placeholder.
- Relationship editing is foundation-level and does not yet drive request/offer visibility.
- No email invitation sending.
- No passenger document upload/storage.
- No travel requests, offers, bookings, tickets, EMDs, invoices, payments, airline intelligence, or document generation.

## Next Recommended Phase

Implement request intake, messages, tasks, and timelines after validating the CRM relationship model with realistic family, company, assistant, and self-traveler scenarios.
