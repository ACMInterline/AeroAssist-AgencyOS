# Portal Visibility Matrix

| Capability | Client Portal | Passenger Portal | Canonical source | Guard |
|---|---|---|---|---|
| Dashboard | Client household and commercial view | exact Passenger view | Kernel projections | active mapping + Agency + subject |
| Requests | Own Client Requests; create, draft edit, early cancel | not Client-wide | `TravelRequest` | Client link and Request ownership |
| Released Offers | Compare and decide | exact-recipient read-only | Offer Delivery + `OfferAcceptance` | recipient identity and subject |
| Accepted snapshot | Client-safe immutable summary | Trip evidence reference only | `TripAcceptedOfferSnapshot` | scoped Offer/Trip |
| Trips | Client Requests/primary Client | exact `TripPassenger` membership | `TripDossier` | scoped IDs derived server-side |
| Bookings | linked Booking Records | linked record with subject-filtered children | `BookingRecord` | scoped Trip/Passenger |
| Tickets | related Client Passenger only | exact Passenger only | `TicketRecord` | canonical passenger link |
| EMDs | related Client Passenger only | exact Passenger only | `EMDRecord` | canonical passenger link |
| Documents | customer-visible, in scope | customer-visible, exact subject | `DocumentWorkspace` | no internal/conflicting Passenger link |
| Upload | requested Document only | requested, exact Passenger Document only | `DocumentStorageRecord` | allowlist, 5 MB, PDF/JPEG/PNG |
| Messages | explicit Client participant | explicit Passenger participant | Operational Collaboration | participant + entity + visibility |
| Timeline | Client-visible scoped events | Passenger-visible scoped events | `OperationalTimeline` | exact entity linkage |
| Notifications | Client projections | Passenger projections | notification projection | linked visible timeline event |
| Finance | read-only Client ledger | none | Commercial Ledger | Client ID; private-cost redaction |
| Profile | allowlisted Client fields | allowlisted travel-profile fields | canonical profile | subject-specific patch allowlist |
| Approvals | own acceptance and visible approval history | visible Passenger approval history only | Acceptance + Timeline | subject scope |

## Cross-Tenant And Cross-Subject Rules

1. `agency_id` comes only from the active `PortalAccessMapping`.
2. Client visibility requires the canonical Client ID and explicit active
   Client-Passenger relationships where Passenger data is involved.
3. Passenger visibility requires an exact Passenger ID match; a shared
   Request, Trip, or Booking never grants another Passenger's records.
4. Communication requires both visible entity scope and an explicit Portal
   participant.
5. A `customer_visible` flag cannot override conflicting ownership.
6. Internal visibility, raw provider data, supplier values, margins, secrets,
   and credentials are always excluded.

## Mutation Matrix

Only the following Portal writes are supported:

- Client Request create, Request V4 draft edit, and pre-processing cancel;
- Client decision against a released exact Offer version;
- requested Document upload;
- allowlisted canonical profile update;
- authorized Operational Collaboration reply;
- existing compatibility acknowledgements where the underlying record remains
  historical.

There is no booking manipulation, Ticket/EMD mutation, payment execution,
provider action, public share, external messaging, or operational Trip edit.
