# Canonical Request V4 Contract

## Decision

`TravelRequest` remains the sole Request owner in `travel_requests`. Request V4
adds a typed `canonical_payload` to that record and projects operational child
records into the existing canonical collections:

| Concern | Canonical model | Collection |
|---|---|---|
| Request | `TravelRequest` | `travel_requests` |
| Traveler claim | `RequestPassenger` | `request_passengers` |
| Intended flight | `RequestSegment` | `request_segments` |
| Passenger service | `PassengerServiceRequest` | `passenger_service_requests` |
| Animal | `RequestPet` | `request_pets` |
| Special item | `RequestSpecialItem` | `request_special_items` |

`RequestIntake` remains pre-request provenance and triage. It becomes an
operational Request only through explicit conversion. `TravelRequestWorkspace`
remains a compatibility family pending the existing migration register; it is
not a second Request owner.

## Aggregate

Every new canonical request has `request_version: 4` and a strict payload:

- `contact`: required first name, last name, and email; optional phone.
- `trip`: purpose, quote mode, cabin, budget and bounded preferences.
- `itinerary_segments`: at least one ordered, stable, dated segment.
- `passengers`: at least one stable request traveler, unresolved unless an
  active same-Agency `PassengerProfile` is explicitly supplied.
- `selected_services` and `service_details`: one typed detail block per
  passenger and service key.
- `pets`: structured animal, carrier, documentation, and segment scope.
- `special_items`: category-specific facts and segment scope.
- `admin_metadata`: source, operational status, priority, assignment, and
  internal notes.

Unknown fields are rejected. Server validation derives passenger age from the
first departure date and pet total weight from animal and container weights.
Aggregate errors name the relevant payload path.

## Referential Rules

- Local passenger, segment, pet, and item IDs are unique within one Request.
- Segment order begins at one and is contiguous.
- Passenger service, pet, and item references must resolve inside the same
  aggregate.
- A linked `PassengerProfile` must be active and belong to the exact Agency.
- `agency_id` and `request_id` are present on projections and remain immutable.
- Missing child rows on update are preserved. Removal requires an explicit
  local-ID removal list.
- No MongoDB transaction is assumed. The parent is marked `syncing` before
  projection and `reconciliation_required` with a bounded warning if projection
  fails. A safe normalization retry rebuilds projections.

## Service Detail Families

The contract validates:

- children traveling alone;
- wheelchair and mobility assistance;
- medical equipment and travel support;
- service animals;
- hearing and visual assistance;
- cognitive, invisible, or language support;
- extra-seat support;
- special items and equipment;
- documents and travel compliance.

All details have explicit all-segment or selected-segment scope. Client-safe
details are projected separately from internal operational detail. No schema
contains executable expressions and no service request executes airline or
provider activity.

## Routes

- `POST /api/public/requests` validates a V4 payload and stores a
  `RequestIntake`; it returns only a safe acknowledgement.
- `POST /api/agencies/{agency_id}/requests` creates a canonical Request V4.
- `GET /api/agencies/{agency_id}/requests/{request_id}` returns canonical and
  compatibility views.
- `PATCH /api/agencies/{agency_id}/requests/{request_id}` updates the aggregate
  and accepts explicit child-removal lists.
- `POST /api/agencies/{agency_id}/requests/{request_id}/normalize` rebuilds
  compatibility projections.

Existing intake, builder, and legacy request routes remain adapters. Structural
child routes reject independent writes for V4 records. Agency routes use the
existing identity, active membership, and centralized request permissions.

## Identity Boundary

Public intake and ordinary Request creation never create a
`PassengerProfile`. Unresolved traveler facts live only on `RequestPassenger`.
The existing explicit identity-confirmation action is the sole path that may
link an existing profile or create a confirmed master passenger. Confirmation
updates the canonical payload so the aggregate and child projection agree.

## Reference Dependencies

PTC, nationality, airport, airline, cabin, animal, breed, container, special
item, country, currency, and service values resolve through the canonical
reference-data contract where populated. Request V4 stores stable reference
IDs plus compatibility code/key and label snapshots. Unknown legacy values
remain readable and add a reconciliation message; they are never silently
replaced. Age validation is performed on the backend from PTC metadata and the
first segment departure date. See
[Canonical Reference Data Contract](canonical-reference-data-contract.md).

## Downstream Contract

Offer preparation and request-to-trip conversion continue to consume the
existing child collections. Request V4 generates those projections
deterministically and retains the canonical payload as source truth. Accepted
offer and later lifecycle snapshots remain immutable and are not rewritten by
Request edits.

## Safety

Request V4 does not migrate production records, create another Request
collection, activate providers, search or book flights, issue tickets or EMDs,
take payment, send messages, or alter downstream lifecycle ownership.
