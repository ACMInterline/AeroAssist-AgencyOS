# Canonical Domain Ownership Map

## Product-Kernel Summary

This document is the enforceable ownership contract for AeroAssist's current
product kernel. It classifies actual models, collections, services, routers,
frontends, snapshots, workspaces, projections, compatibility writers, seed
writers, and portal consumers found in the repository. It does not migrate
records, rename collections, rewrite routes, or change runtime behavior.

The machine-readable source is
`backend/canonical_domain_ownership.py`. Persistence tenancy and query
governance remain owned by `backend/database.py`,
`backend/persistence_query.py`, and `backend/persistence_repository.py`. The
domain registry links to those controls; it does not replace them.

The contract selects 36 ownership targets and leaves four domains explicitly
`decision_required`. Twenty-one domains require compatibility reconciliation
before their target can be considered exclusive. A valid registry therefore
reports `migration_required`; it does not claim the product kernel has already
been consolidated.

## Classification Contract

| Classification | Meaning |
|---|---|
| `canonical_write_owner` | Authoritative mutable business record or its governed writer. |
| `canonical_child_record` | Governed child of a canonical aggregate. |
| `immutable_snapshot` | Historical evidence that cannot become mutable source truth. |
| `read_projection` | Derived presentation with no independent truth. |
| `operational_workspace` | Human workflow state around a business record. |
| `compatibility_projection` | Legacy response or storage mirror that must be read-only. |
| `compatibility_writer` | Active duplicate writer requiring migration and removal. |
| `reference_record` | Governed shared vocabulary or catalogue data. |
| `audit_evidence` | Preserved security or mutation evidence. |
| `demo_or_test_only` | Bounded synthetic/test writer, never a production owner. |
| `deprecated` | Retained for historical compatibility with no new writes. |
| `decision_required` | The current repository cannot support a safe ownership choice. |

## Tenant-Boundary Decision

**agency_id is the canonical workspace boundary.**

- `Agency.id` is the tenant root; agency-owned records carry immutable
  `agency_id`.
- `workspace_id` is optional operational or presentation context. It is not an
  authorization boundary.
- Agency access requires an active membership for the same `agency_id`.
- Platform-global records use existing Platform authorization and have no
  synthetic tenant key.
- Portal access is derived from authenticated identity,
  `PortalAccessMapping`, canonical client/passenger links, and record ownership.
  Caller-supplied IDs are not authority.
- Created/updated actor fields remain inconsistent across older models. The
  registry records the required field names per target; normalization is a
  later migration concern.
- No `workspace_id` tenant migration is required.

## Frozen Lifecycle

The target lifecycle is:

`TravelRequest -> OfferWorkspace -> TripAcceptedOfferSnapshot -> TripDossier
-> BookingRecord -> TicketRecord / EMDRecord -> Invoice / PaymentRecord ->
DocumentWorkspace / OperationalWorkItem / OperationalTimeline -> authorized
portal projections`

The request remains the intake/audit origin. A normal confirmed Trip uses an
independent ID and is created from immutable accepted Offer evidence.
Request-to-Trip conversion is planning-only before acceptance. Booking
workspaces coordinate work but do not own PNR truth. Portal views are
authorized projections, not owners.

P1 Product Kernel Repair 6 makes OfferWorkspace the normal Agency UI write
target, requires exact Offer/Option versions for acceptance, creates one
hashed accepted snapshot and one linked Trip idempotently, requires governed
BookingRecord evidence before booked state, and enforces Booking lineage for
normal Ticket/EMD creation. Historical Offer, TripWorkspace, Booking,
TicketWorkspace, and EmdWorkspace records remain migration debt.

## Domain Map

### 1. Authentication Identity

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| `backend/auth.py`, auth router, authentication security service, demo seed | `AuthIdentity` / `auth_identities` | `backend/auth.py`; `/api/auth` | `AuthSession` is a canonical child | Global identity; not directly portal-visible | Security principal; selected |

### 2. Platform User

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Agency and auth routers, demo seed | `PlatformUser` / `platform_users` | `backend/routers/auth.py`; `/api/auth` | Agency role is not stored here | Global profile; not portal-visible | Staff profile; selected |

### 3. Agency Membership

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Agency and auth routers, demo seed | `AgencyStaffMembership` / `agency_staff_memberships` | `backend/routers/agencies.py`; `/api/agencies/{agency_id}/staff` | No parallel RBAC owner | Immutable `agency_id`; not portal-visible | Tenant authorization edge; selected |

### 4. Client Portal Identity

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Auth, clients, portal, explicit link service, seed; Client Master service | `PortalAccessMapping` / `portal_access_mappings` | `portal_identity_link_service.py`; Agency mapping management; `/api/portal` projections | `ClientPortalAccessProfile` / `client_portal_access_profiles` is a deprecated, non-authorizing compatibility projection | Agency scoped; explicit identity-to-client link only | Portal boundary selected; historical reconciliation required |

### 5. Passenger Portal Identity

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Auth invitation, Passenger invitation, explicit link service, Portal projections, seed | `AuthIdentity` + `PortalAccessMapping` + `PassengerProfile` / existing collections | `portal_identity_link_service.py`; `/api/agencies/{agency_id}/portal-access-mappings`; `/api/portal` | No duplicate `PassengerPortalUser`; historical relationship-derived visibility is reconciliation evidence only | Agency scoped; explicit identity-to-passenger self link only | Portal principal resolved; migration required |

### 6. Agency / Tenant / Workspace

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Agency router, onboarding, demo seed | `Agency` / `agencies` | `backend/routers/agencies.py`; `/api/agencies` | `AgencyWorkspace` is operating/presentation context | `Agency.id` is the root; no direct portal owner | Tenant root; selected, no workspace migration |

### 7. CRM Client

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Clients/auth/requests/intake writers and seed; source-bound Client Master adapter | `ClientProfile` / `client_profiles` | `backend/routers/clients.py`; `/api/agencies/{agency_id}/clients` | `ClientMasterRecord` / `client_master_records` accepts only one same-Agency canonical-source compatibility projection for new writes | Immutable `agency_id`; own client projection | Requester/payer selected; historical reconciliation required |

### 8. Passenger

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Passenger router, explicit request identity confirmation, seed; source-bound Passenger Master adapter and Passenger Workspace CRUD | `PassengerProfile` / `passenger_profiles` | `backend/routers/passengers.py`; `/api/agencies/{agency_id}/passengers` | `PassengerMasterRecord` accepts only one same-Agency canonical-source compatibility projection; `PassengerWorkspace` remains a compatibility writer | Immutable `agency_id`; explicit linked projection | Confirmed traveler selected; historical/workspace reconciliation required, P0 integrity applies |

### 9. Client-Passenger Relationship

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Client/passenger/request routers, identity confirmation, seed; source-bound Master Link adapter | `ClientPassengerRelationship` / `client_passenger_relationships` | Client relationship routes | `ClientPassengerMasterLink` / `client_passenger_links` accepts only a matching same-Agency canonical relationship source for new writes | Both endpoints must share immutable `agency_id` | Portal visibility edge selected; historical reconciliation required |

### 10. Request

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Request/offer routes, intake conversion, normalization, identity, trip link, seed | `TravelRequest` / `travel_requests` | `backend/routers/requests.py`; `/api/agencies/{agency_id}/requests` | `RequestIntake` is provenance/triage; `TravelRequestWorkspace` is a compatibility writer | Immutable `agency_id`; own request projection | Lifecycle origin; migration required |

### 11. Request Passenger

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Request router, intake conversion, identity service, seed | `RequestPassenger` / `request_passengers`, child of `TravelRequest` | Request passenger routes and explicit identity confirmation | Unresolved placeholders remain request-owned | Immutable `agency_id`; own request passenger view | Request child; selected |

### 12. Request Segment

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Request router, intake conversion, seed | `RequestSegment` / `request_segments`, child of `TravelRequest` | Request segment routes | Segment-first itinerary; summaries are projections | Immutable `agency_id`; own itinerary view | Request child; selected |

### 13. Passenger Service

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Special Services service; request service writers | `PassengerServiceRequest` / `passenger_service_requests` | `special_services_service.py`; `/api/agencies/{agency_id}/passenger-services` | `RequestPassengerSegmentService` is intake child; `RequestedService` is compatibility writer | Immutable `agency_id`; client-safe fulfillment status only | Operational service case; migration required |

### 14. Pet

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Request router, normalization, seed | `RequestPet` / `request_pets`, child of `TravelRequest` | Request pet routes | `RequestPetSegmentTransport` owns segment applicability | Immutable `agency_id`; own request-safe details | Request service subject; selected |

### 15. Special Item

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Request router, normalization, seed | `RequestSpecialItem` / `request_special_items`, child of `TravelRequest` | Request special-item routes | `RequestSpecialItemSegment` owns segment applicability | Immutable `agency_id`; own request-safe details | Request service subject; selected |

### 16. Offer

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Offer builder/acceptance/comparison; legacy Offer CRUD; Phase 41.5 Offer Workspace CRUD | `OfferWorkspace` / `offer_workspaces` | `offer_builder_service.py`; `/api/agencies/{agency_id}/offer-workspaces` | `Offer` / `offers` and `OfferWorkspaceV2` / `offer_workspaces_v2` are compatibility writers | Immutable `agency_id`; released snapshot only | Mutable proposal; migration required |

### 17. Offer Option

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Offer builder/acceptance/comparison and legacy fare options | `OfferOption` / `offer_options`, child of `OfferWorkspace` | Offer builder option routes | `OfferFareOption` / `offer_fare_options` is a compatibility writer | Immutable `agency_id`; released option snapshot only | Offer child; migration required |

### 18. Offer Acceptance

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Offer Acceptance service | `OfferAcceptance` / `offer_acceptances` | Offer Acceptance service/routes | Embedded accepted payloads are immutable; acceptance status is mutable governance | Immutable `agency_id`; own decision projection | Human decision; migration metadata correction required |

### 19. Accepted Offer Snapshot

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Offer Acceptance service, creation only | `TripAcceptedOfferSnapshot` / `trip_accepted_offer_snapshots` | Acceptance handoff | Entire record is immutable evidence | Immutable `agency_id`; client-safe frozen projection | Commercial handoff evidence; selected |

### 20. Trip

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Trip router/service; independent Trip Workspace CRUD | `TripDossier` / `trip_dossiers` | `trip_dossier_service.py`; `/api/agencies/{agency_id}/trips` | `TripWorkspace` / `trip_workspaces` is a compatibility writer | Immutable `agency_id`; explicit portal projection | Confirmed dossier; migration required |

### 21. Booking / PNR

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Booking Workspace service and legacy Booking routes | `BookingRecord` / `booking_records` | Booking Workspace service; `/api/agencies/{agency_id}/booking-workspaces` | `BookingWorkspace` is operational context; `Booking` / `bookings` is a compatibility writer | Immutable `agency_id`; client-safe booking view | External result mirror; migration required |

### 22. Booking Handoff

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Offer-to-Booking Handoff service | `OfferBookingHandoff` / `offer_booking_handoffs` | `/api/agencies/{agency_id}/booking-handoffs` | Checks, mappings, and instructions are governed children | Immutable `agency_id`; internal only | Readiness bridge; selected operational workspace |

### 23. Ticket

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Ticket/EMD service, legacy Booking ticket writer, seed; Ticket Workspace CRUD | `TicketRecord` / `ticket_records` | `/api/agencies/{agency_id}/tickets` | `TicketWorkspace` / `ticket_workspaces` is a compatibility writer | Immutable `agency_id`; client-safe ticket view | Ticket mirror; migration required |

### 24. Ticket Coupon

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Ticket/EMD service | `TicketCoupon` / `ticket_coupons`, child of `TicketRecord` | Ticket routes | Segment and usage status child | Immutable `agency_id`; safe status only | Ticket child; selected |

### 25. EMD

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Ticket/EMD service, legacy Booking EMD writer, seed; EMD Workspace CRUD | `EMDRecord` / `emd_records` | `/api/agencies/{agency_id}/emds` | `EmdWorkspace` / `emd_workspaces` is a compatibility writer | Immutable `agency_id`; client-safe EMD view | Ancillary document mirror; migration required |

### 26. EMD Coupon

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Ticket/EMD service | `EmdCoupon` / `emd_coupons`, child of `EMDRecord` | EMD routes | Service/usage child | Immutable `agency_id`; safe status only | EMD child; selected |

### 27. SSR / OSI

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| SSR/OSI Workspace service | `SsrOsiWorkspace` / `ssr_osi_workspaces` | `/api/agencies/{agency_id}/ssr-osi-workspaces` | Current human-controlled record; no provider execution | Immutable `agency_id`; safe confirmation projection only | Service communication state; selected with workspace justification |

### 28. Invoice

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Canonical Commercial Ledger service; Finance router adapter; seed compatibility | `Invoice` / `invoices` | `/api/agencies/{agency_id}/invoices` | Lines are children; issued corrections use Credit Notes; totals are server-derived | Immutable `agency_id`; own invoice view | Commercial document; selected |

### 29. Invoice Line

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Canonical Commercial Ledger service; Finance router adapter; seed compatibility | `InvoiceLineItem` / `invoice_line_items`, child of `Invoice` | Invoice line routes | Draft-only edits; no independent Invoice ownership | Immutable `agency_id`; own invoice detail | Server-derived finance child; selected |

### 30. Payment

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Canonical Commercial Ledger service; Finance router adapter; seed compatibility | `PaymentRecord` / `payment_records` plus `PaymentAllocation` / `payment_allocations` | `/api/agencies/{agency_id}/payments` | Receipt evidence remains immutable; allocations settle one or more Invoices/lines | Immutable `agency_id`; own payment status; private reconciliation metadata | Payment evidence and settlement allocation; selected |

### 31. Refund / Exchange

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| After-Sales owns operations; Canonical Commercial Ledger owns accounting; legacy refund/exchange and ticket/EMD writers remain compatibility | `AfterSalesCase` for operational decisions; `RefundLedgerEntry` and `ExchangeLedgerEntry` for accounting evidence | `/api/agencies/{agency_id}/after-sales`, `/api/agencies/{agency_id}/finance/refunds`, `/api/agencies/{agency_id}/finance/exchanges` | Accounting entries reference, but never mutate, cases, Tickets, EMDs, Payments, or accepted changes | Immutable `agency_id`; client-safe case status only; ledger writes require finance permission | Operational case migration required; accounting owners selected |

### 32. Document

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Document Workspace and Special Services services | `DocumentWorkspace` / `document_workspaces` | `/api/agencies/{agency_id}/document-workspaces` | Render jobs/packages/shares are children; rendered outputs are immutable evidence | Immutable `agency_id`; only explicit customer-visible output | Requirement/verification record; selected with workspace justification |

### 33. Communication

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Request messages, portal messages, after-sales communication, supplier interactions, timeline fields | No safe single owner | Multiple request, portal, after-sales routes | Internal, supplier, and client content must remain separated | Immutable `agency_id`; client messages only | Cross-domain interaction; `decision_required` |

### 34. Task / Work Item

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Agent Work Queue service; Request Task and automation writers | `OperationalWorkItem` / `operational_work_items` | `/api/agencies/{agency_id}/work-queue` | Assignment/dependency/run records are children; `RequestTask` is compatibility | Immutable `agency_id`; internal only | Actionable work; migration required |

### 35. Timeline

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Timeline, SLA, and offer-delivery services plus entity-specific timelines | `OperationalTimeline` / `operational_timelines` | `/api/agencies/{agency_id}/operational-timelines` | Request/trip/booking/ticket-EMD/refund timelines are compatibility writers | Immutable `agency_id`; explicit visible events only | Cross-domain history; migration required |

### 36. Audit Event

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Shared audited routers/services listed in the machine registry | `AuditEvent` / `audit_events` | Protected Platform and agency audit routes | Immutable security/mutation evidence | Agency scope or Platform-global; never portal-visible | Audit evidence; selected, P0 access guard applies |

### 37. Reference Data

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Platform/reference routers, data/enrichment/import services, seed | `GlobalReferenceRecord` / `global_reference_records` | `/api/reference`, `/api/platform/reference` | Service catalogue, domain metadata, suggestions, imports are reference children | Platform global; approved safe values only | Shared vocabulary; selected |

### 38. Airline Knowledge

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Legacy items, acquisition, normalization, governance/version, evidence, publication, agency overlays | No safe aggregate selected | Platform airline-knowledge families and agency published projections | Evidence and historical versions must remain distinct from mutable normalized knowledge | Mixed global/agency; published safe explanations only | AOIE knowledge; `decision_required` |

### 39. Policy

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Approved extraction records, `airline_rules_core`, visual cards, operational rule composer | No safe aggregate selected | Platform policy/rules and agency read projections | Evidence, policy, capability, and pricing remain separate | Mixed global/agency; approved safe explanation only | Airline policy; `decision_required` |

### 40. Pricing

| Current owners | Target / collection | Service / route | Children, snapshots, compatibility | Tenant / portal | Lifecycle / status |
|---|---|---|---|---|---|
| Ancillary pricing rules, formula builders, offer pricing lines, accepted price snapshots | No safe mutable rule owner selected | Pricing formula and ancillary pricing routes | Offer lines are children; accepted prices are immutable evidence | Mixed global/agency; released/accepted safe snapshot only | Commercial rules/evidence; `decision_required` |

## Enforcement

Run:

```bash
python3 backend/scripts/validate_canonical_domain_ownership.py
python3 backend/scripts/smoke_canonical_domain_ownership_map.py
```

The validator checks required domains, target uniqueness, classifications,
source files, persistence registration, tenant decisions, active writers,
frontend consumers, portal visibility, lifecycle continuity, canonical route
roots, deterministic ordering, secret/local-path exclusion, unchanged runtime
governance, and smoke inventory resolution. Migration blockers are reported
without turning an honest `migration_required` state into a validation failure.

## Canonical Request V4 Repair

`TravelRequest` remains the Request owner. `RequestPassenger`,
`RequestSegment`, `PassengerServiceRequest`, `RequestPet`, and
`RequestSpecialItem` are governed child records projected by
`request_v4_service.py`. `RequestIntake` remains pre-request provenance.
`TravelRequestWorkspace` remains a compatibility writer and an open migration
item; it is not promoted to canonical ownership. New V4 structural writes use
the aggregate route, while explicit passenger identity confirmation remains a
separate guarded action.

## P1 Product Kernel Repair 5 - Canonical Reference Data

`GlobalReferenceRecord` and `global_reference_records` remain the sole shared
reference-data owner. `passenger_type_codes`, `species`, `breeds`, pricing
formula components, communication channels, and service codes resolve to
existing stable domain keys rather than creating duplicate collections.
`PassengerProfile`, `TravelRequest`, and `RequestPassenger` retain operational
truth and store reference IDs with historical code/label snapshots. Agency
scope is a visibility constraint, never a replacement ownership boundary.

## P1 Product Kernel Repair 6 - Commercial Lifecycle

The enforced normal flow is `TravelRequest -> OfferWorkspace -> OfferOption ->
OfferAcceptance -> TripAcceptedOfferSnapshot -> TripDossier ->
OfferBookingHandoff -> BookingRecord -> TicketRecord / EMDRecord`.
OfferWorkspace and OfferOption own mutable commercial preparation; accepted
evidence is create-only. BookingWorkspace owns preparation only, while
BookingRecord owns an evidenced PNR/result. Legacy Offer and Booking routes
remain readable compatibility surfaces and cannot overwrite linked canonical
truth. Migration remains required for historical parallel records. See
[Canonical Commercial Lifecycle Contract](canonical-commercial-lifecycle-contract.md)
and [Commercial Lifecycle Compatibility And Migration](commercial-lifecycle-compatibility-and-migration.md).

## P1 Product Kernel Repair 7 - Commercial Ledger

`CommercialLedger` and append-only `CommercialTransaction` records own
accounting postings downstream of the canonical commercial lifecycle.
Existing Invoice, Invoice Line, and Payment collections remain canonical and
are extended; Payment Allocation, Supplier Cost, Credit Note, Refund Ledger,
and Exchange Ledger records complete the accounting chain. The Finance router
is an adapter to the canonical service. After Sales remains the operational
decision owner and the ledger records only reviewed commercial consequences.
See [Canonical Commercial Ledger](canonical-commercial-ledger.md).
