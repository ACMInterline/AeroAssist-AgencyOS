# Canonical Domain Migration Register

## Purpose

This register converts the factual ownership map into a bounded future repair
queue. It does not authorize migrations, data rewrites, route removal, or
behavior changes. Every repair requires a separately reviewed migration plan,
reconciliation evidence, tenant-isolation tests, rollback handling, and
compatibility exit criteria.

`backend/canonical_domain_ownership.py` is the machine-readable contract.
`docs/architecture/canonical-domain-ownership-map.md` explains the selected
targets and unresolved decisions.

## Duplicate And Compatibility Writers

| Domain | Target | Duplicate or compatibility writer | Dependent routes | Dependent frontend | Required reconciliation | Exit criterion |
|---|---|---|---|---|---|---|
| Client portal identity | `PortalAccessMapping` | `ClientPortalAccessProfile`, `client_portal_access_profiles` | `/api/*/client-portal-access-profiles`, `/api/portal` | Portal dashboard; Client Master | Agency, client, email, status, auth identity | Legacy profile is non-authorizing; new active/invited rows require an explicit mapping; historical rows reconciled |
| Passenger portal identity | `AuthIdentity` + `PortalAccessMapping` + `PassengerProfile` | Historical client-relationship-derived visibility and email-only mappings | `/api/portal`, passenger invitation and mapping management routes | Passenger Portal dashboard/profile/self view | Explicit identity and passenger IDs within one Agency; no email auto-link | Every passenger principal has one reviewed active or revoked explicit mapping |
| CRM Client | `ClientProfile` | `ClientMasterRecord`, `client_master_records` | Agency/Platform Client Master CRUD | Clients, Client Detail, Client Master | Explicit agency-scoped ID map; no fuzzy auto-merge | New Master rows are one-per-source compatibility projections; historical rows remain for reconciliation |
| Passenger | `PassengerProfile` | `PassengerMasterRecord`, `PassengerWorkspace` | Passenger Master and Passenger Workspace CRUD | Passengers, Passenger Detail, Passenger Master/Workspace | Human-confirmed identity; quarantine synthetic DOB; preserve links/history | New Passenger Master rows require canonical source; remaining workspace overlap is separately reconciled; P0 integrity smoke remains green |
| Client-Passenger relationship | `ClientPassengerRelationship` | `ClientPassengerMasterLink` | Client Master link routes | Client/Passenger detail | Explicit client/passenger IDs within one agency | New Master links are one-per-source projections and must match the canonical relationship; historical links retained |
| Request | `TravelRequest` | `TravelRequestWorkspace` | Travel Request Workspace CRUD | Requests, Travel Requests | Request reference, source intake, client/passenger/segment links | Workspace becomes projection or is retired |
| Passenger Service | `PassengerServiceRequest` | `RequestedService` fulfillment overlap | Request service and Special Services routes | Request Detail, Special Services, Passenger Services | Request/trip/passenger/segment/service lineage | Fulfillment writes target PassengerServiceRequest only |
| Offer | `OfferWorkspace` | `Offer`, `OfferWorkspaceV2` | Legacy `/offers`; Offer Workspace V2 APIs | Offers, Offer Workspaces, Offer Builder | Request/trip/client/options/pricing/status/acceptance | One write API; compatibility families read-only |
| Offer Option | `OfferOption` | `OfferFareOption` and legacy route/fare children | Legacy offer fare-option routes | Offer Builder and legacy Offer views | Explicit option IDs and route/fare mapping | Acceptance references canonical option only |
| Offer Acceptance | `OfferAcceptance` | Persistence metadata treats collection as immutable | Acceptance routes | Offer detail; Portal offer detail | Separate mutable decision state from immutable accepted payload | Persistence classification reflects actual mutation contract |
| Trip | `TripDossier` | `TripWorkspace` | Trip Workspace CRUD | Trips and Trip Workspaces | Trip reference, request/client/passengers/segments/offers/bookings/docs | Every workspace links to dossier; no independent identity/status |
| Booking / PNR | `BookingRecord` | Legacy `Booking`; `BookingWorkspace` must remain context only | Legacy `/bookings`; Booking Workspace APIs | Bookings and Booking Workspaces | PNR/reference/trip/snapshot/passenger/segment/status | Legacy mutations adapt to BookingRecord; workspace points to record |
| Ticket | `TicketRecord` | `TicketWorkspace`; legacy Booking ticket writer | `/tickets`, `/ticket-workspaces`, booking ticket routes | Tickets/EMDs and Ticket Workspace | Number, booking, passenger, coupons, pricing, status, lifecycle refs | Ticket Workspace is projection/context; one ticket writer |
| EMD | `EMDRecord` | `EmdWorkspace`; legacy Booking EMD writer | `/emds`, `/emd-workspaces`, booking EMD routes | Tickets/EMDs and EMD Workspace | Number, booking/ticket/passenger, coupons, RFIC/RFISC, value/status | EMD Workspace is projection/context; one EMD writer |
| Refund / Exchange | `AfterSalesCase` | `RefundExchangeCase`, ticket/EMD exchange operations | `/refunds-exchanges`, `/after-sales` | Refunds/Exchanges and After Sales | Impact scope, coupon state, estimates, approvals, decisions, comms | Legacy cases are linked history or adapters |
| Task / Work Item | `OperationalWorkItem` | `RequestTask` | Request task routes; Work Queue | Request Detail, Tasks, Work Queue | Assignment, due date, status, blocker, source, timeline | All actionable work is queue-owned |
| Timeline | `OperationalTimeline` | Request, trip, booking, ticket/EMD, refund timelines | Entity timeline routes; operational timeline API | Timeline and entity details | Source event ID, actor, timestamp, visibility, entity links | New events use canonical timeline; old collections immutable |

## Ambiguous Ownership

| Domain | Current candidates | Why no target is safe | Decision evidence required |
|---|---|---|---|
| Communication | Request messages, portal messages, after-sales communication, supplier interactions, timeline communication fields | Different visibility and delivery semantics are mixed across aggregates | Define message aggregate, channel attempts, immutable content, internal/supplier/client partitions |
| Airline Knowledge | Legacy items, acquisition, normalized records, evidence assertions, versions, governance releases, publications, agency overlays | The five knowledge pillars and evidence lifecycle cannot be collapsed safely | Approve aggregate boundaries and the relation between normalized item, version, publication, and overlay |
| Policy | Approved extraction records, rules core, policy cards, composer rules, exceptions | Similar facts can be independently edited in multiple representations | Choose normalized policy aggregate and make editors/projections adapt to it |
| Pricing | Ancillary rules, formula builders, offer pricing lines, accepted snapshots | Rule definitions, quoted commercial values, and immutable accepted evidence are distinct | Choose governed rule owner and preserve quote/snapshot ownership separately |

## Unsafe Compatibility Patterns

1. Platform Client/Passenger Master routes allow independent cross-agency
   metadata creation instead of projecting canonical agency-owned records.
2. Phase 41 metadata workspaces for Request, Trip, Offer, Ticket, and EMD carry
   business identity and status fields without mandatory canonical IDs.
3. Legacy Offer and Booking routes remain active writers beside later
   workspaces/records.
4. Booking routes write directly to `ticket_records` and `emd_records`, bypassing
   the target Ticket/EMD service boundary.
5. `offer_acceptances` is updated for status transitions while query ownership
   currently labels the whole collection immutable.
6. Entity-specific task and timeline collections continue accepting new writes
   beside the canonical Work Queue and Operational Timeline.
7. Downstream handoff paths do not universally prove they read frozen accepted
   commercial evidence rather than a mutable offer.
8. Actor fields vary among `created_by`, `created_by_user_id`, `updated_by`, and
   `updated_by_user_id`, weakening uniform audit assertions.

## Lifecycle Gaps

| Transition | Current condition | Repair needed | Must preserve |
|---|---|---|---|
| Request -> Offer | Legacy and canonical offer creation paths coexist | Adapt all creation to `OfferWorkspace` with explicit request link | Request can exist without trip |
| Offer -> Acceptance | Acceptances target canonical options, while legacy portal/offer paths remain | Route compatibility acceptance through canonical service | Human decision and immutable accepted values |
| Acceptance -> Trip | Trip can exist before accepted evidence and `TripWorkspace` can exist independently | Require explicit dossier linkage and label pre-acceptance trips accurately | Never reuse request ID as trip ID |
| Accepted snapshot -> Booking | Booking handoff is correct in principle but legacy booking creation can read mutable offer state | Require snapshot ID on commercialized booking path | Accepted snapshot immutability |
| Booking Workspace -> Booking Record | Both carry PNR/status-shaped state | Make workspace workflow-only and record result-only | Imported raw provider truth and manual mode |
| Booking -> Ticket/EMD | Canonical service and legacy Booking route both write records | One service boundary with compatibility adapters | Coupon-level state and immutable historical snapshots |
| Booking -> Finance | Links accept several booking IDs/workspace IDs | Normalize explicit canonical booking linkage while retaining source IDs | Historical invoices/payments |
| Operations -> Portal | Portal uses projections but communication/document visibility rules vary | Centralize authorization and visibility mapping | Internal/client separation and tenant isolation |

## Data-Reconciliation Requirements

- Reconciliation is agency-scoped. Cross-agency matching is forbidden.
- IDs are mapped explicitly; names, emails, references, and dates may produce
  review candidates but cannot silently merge records.
- Historical accepted offers, imported raw provider payloads, ticket/EMD
  coupons, invoice/payment history, rendered documents, audit events, and
  timeline evidence are never overwritten.
- Synthetic/demo records remain distinguishable and cannot establish production
  identity truth.
- Every duplicate must be classified as matched, unmatched, conflicting,
  superseded, or intentionally retained.
- Every compatibility adapter records source and target IDs plus actor, time,
  result, warnings, and idempotency key.
- Tenant keys are immutable. Reconciliation cannot move a record between
  agencies.
- Client-visible and internal fields are reconciled separately.

## Recommended Repair Order

1. **Identity and tenant edges:** reconcile explicit Portal links,
   Client/Passenger master adapters, relationships, and uniform actor fields.
2. **Request aggregate:** retain intake provenance, retire independent Travel
   Request Workspace truth, and finalize scoped services/pets/items.
3. **Offer aggregate:** adapt legacy Offer and OfferWorkspaceV2 writes to
   OfferWorkspace/OfferOption; correct acceptance persistence classification.
4. **Trip aggregate:** map TripWorkspace to TripDossier and prevent independent
   dossier identity.
5. **Booking handoff and result:** require immutable accepted evidence, keep
   BookingWorkspace operational, and adapt legacy Booking writes.
6. **Ticket and EMD:** route all writes through Ticket/EMD service and reconcile
   workspace/coupon state.
7. **Finance and after-sales:** normalize booking/ticket/EMD references and
   merge legacy service cases into AfterSalesCase.
8. **Operations support:** converge RequestTask and entity timelines into
   OperationalWorkItem and OperationalTimeline.
9. **Communication:** approve one aggregate without weakening internal,
   supplier, and client partitions.
10. **Knowledge, Policy, Pricing:** approve aggregate boundaries only after the
    operational chain no longer has competing writers.

## Exit Criteria

The product-kernel freeze can exit this ownership repair only when:

- every domain is `selected`; no `decision_required` entry remains;
- each primary domain has one active mutable owner;
- every compatibility writer is removed, read-only, or a tested adapter to the
  target;
- all canonical collections remain registered under existing persistence and
  tenant governance;
- every agency record has immutable `agency_id` and actor evidence;
- Request -> Offer -> accepted snapshot -> Trip -> Booking -> Ticket/EMD ->
  Finance continuity is proven with explicit IDs;
- downstream commercial reads use immutable accepted evidence;
- portal authorization and visibility are explicit and tenant-safe;
- reconciliation reports account for every duplicate record without destructive
  overwrite;
- migration rollback and idempotent replay are tested;
- P0 audit isolation and passenger identity integrity regressions pass;
- the canonical ownership validator and focused smoke pass without suppressing
  blockers.

## P1 Identity And Tenancy Dry Run

`backend/scripts/analyze_identity_tenancy_migration.py` analyzes historical
Portal links, Client/Passenger Master overlaps, duplicate relationships,
ambiguous/cross-Agency email candidates, and inactive or revoked identity
links. It also reports duplicate active Portal subjects, active staff
memberships without active identities, and active legacy Portal profiles
without valid mappings. The command is intentionally dry-run only and reports
`writes_performed: 0`; `--apply` is rejected. Suggestions are
non-authoritative and never create a Portal link.

Passenger Portal identity is no longer ambiguous: `AuthIdentity` authenticates,
`PortalAccessMapping` authorizes, and `PassengerProfile` owns passenger truth.
No separate Passenger Portal business model is introduced. Historical records
still require reviewed reconciliation, so the domain remains
`migration_required`, not migration complete.
