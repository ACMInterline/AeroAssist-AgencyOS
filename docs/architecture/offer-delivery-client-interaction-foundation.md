# Offer Delivery and Client Interaction Foundation

## Purpose

Phase 56.4 creates the controlled delivery layer between a reviewed Phase 56.3 Offer Comparison and the existing Offer Acceptance, Document, Timeline, Client Portal, Client, and Passenger foundations. Offer Workspace is the primary Agency owner. An agency user works under Delivery & Responses to prepare and explicitly release an immutable client-safe version to authorized portal recipients. A recipient can review alternatives, choose an itinerary and fare brand, acknowledge conditions, ask questions, and submit an explicit decision.

The active phase is `phase_56_4_offer_delivery_client_interaction_foundation`.

## Architectural Position

The internal operational path is:

`Journey and operational sources -> Phase 56.2 composition -> Phase 56.3 finalized comparison snapshot -> Phase 56.4 immutable delivery version -> explicit canonical Offer Acceptance handoff -> booking readiness`

Phase 56.4 is not a new journey, offer, acceptance, document, messaging, identity, passenger, or timeline engine. Its Agency UI is a reusable panel embedded in canonical Offer Workspace. The direct Agency route is contextual compatibility only and requires an Offer ID.

## Source Of Truth

- Canonical Journey and projections remain Phase 56.0 records.
- Segment authoring remains Phase 56.1.
- Option and fare-brand composition remains Phase 56.2.
- Client-safe comparison truth is a finalized Phase 56.3 `JourneyPresentationSnapshot`.
- Commercial Offer truth remains the existing Offer Workspace and Offer option records.
- Acceptance remains `OfferAcceptanceService` and its immutable accepted snapshots.
- Documents remain the existing render-job and package foundation.
- Client, passenger, portal identity, and relationship records remain canonical.
- Operational history remains the existing audit and timeline foundations.

## Delivery And Immutable Versions

`JourneyOfferDelivery` is the agency-owned preparation container. `JourneyOfferDeliveryVersion` copies only the sanitized client-safe projection of one finalized presentation snapshot and preserves both the source snapshot hash and a deterministic payload hash. A draft version can be reviewed and explicitly released. Release marks that version immutable. Pricing, itinerary, wording, conditions, or source changes require a new version; a released payload is never edited in place.

Supersession preserves both versions and links them. Expiry and revocation prevent new actions without deleting historical versions, decisions, interactions, acknowledgements, or audit records.

## Client And Internal Separation

Client payload construction recursively removes agency IDs, internal notes, internal reasoning, supplier costs, margins, markups, commissions, evidence details, governance metadata, restricted contacts, source provenance, source URLs, and unpublished knowledge references. A release validation fails if a restricted field is detected. Unknown, unassessed, conditional, and manual-review states remain explicit and are never converted into support or confirmation.

Internal previews require agency authorization. Platform diagnostics contain governed identifiers and counts only; they do not expose client payloads or provide recipient impersonation.

## Recipient Authorization

Client access uses the existing authenticated `/api/portal` route family and `portal_access_mappings`. Each request resolves the authenticated portal mapping, agency, client, delivery, and active `JourneyOfferDeliveryRecipient`. Passenger-scoped recipients must also resolve through an active canonical client-passenger relationship. Delivery IDs are not authorization credentials, no reusable public bearer token is stored, and no anonymous share route exists.

## Client Interaction

The portal presents practical option cards, local-time segment timelines, connection information, operating-carrier distinctions, fare-brand attributes, baggage, flexibility, pricing, and passenger-service suitability. Progressive disclosure keeps operational detail available without requiring clients to understand internal or GDS terminology.

`JourneyOfferClientInteraction` is append-only and records only purposeful product interactions such as opening a version, selecting an option, expanding relevant details, acknowledging a warning, asking a question, or recording a document download. It does not implement invasive analytics or profiling.

## Warnings And Acknowledgements

Client-safe warnings are copied into the immutable version. Required acknowledgements are stored in `JourneyOfferWarningAcknowledgement` against one recipient and one released version. An acknowledgement for an old version cannot satisfy a new version. Client-blocking warnings prevent acceptance until agency review resolves them in a new released version.

## Decisions And Acceptance Handoff

`JourneyOfferClientDecision` records accept, decline, request-changes, ask-question, or save-for-later metadata against one immutable version. Accept preview validates expiry, revocation, supersession, recipient status, option membership, fare-brand membership, required acknowledgements, terms confirmation, blocking warnings, and canonical Offer mapping.

Submitting an accept decision does not create an acceptance or booking. An authorized agency user must explicitly preview and apply `JourneyOfferAcceptanceHandoff`. Apply revalidates the released version and invokes the existing `OfferAcceptanceService` idempotently. The canonical acceptance ID is retained; booking creation, payment, ticketing, and EMD issuance remain outside this phase.

## Questions And Messages

Client questions and agency replies are stored as client-safe, conversation-linked metadata. Internal notes are not represented by this model. Recording a question or reply does not send email, SMS, or another external message. Existing timeline and audit records capture the interaction for operational follow-up.

## Document Handoff

`JourneyOfferDocumentPackageLink` bridges one immutable delivery version to the existing `document_packages` foundation. Package context includes the delivery/version IDs and source payload hash. The handoff does not create another renderer, mutate a released payload, publish a link, or send a file. Portal download actions record metadata only unless an existing authorized document package supplies a file through its own controls.

## Data Model

- `JourneyOfferDelivery`
- `JourneyOfferDeliveryVersion`
- `JourneyOfferDeliveryRecipient`
- `JourneyOfferClientInteraction`
- `JourneyOfferClientDecision`
- `JourneyOfferClientQuestion`
- `JourneyOfferWarningAcknowledgement`
- `JourneyOfferDocumentPackageLink`
- `JourneyOfferAcceptanceHandoff`
- `JourneyOfferDeliveryAuditEvent`

All records are agency-owned, additive, metadata-only, UTC-timestamped, and non-destructive.

## Product Surface And Routes

- Primary Agency workspace: `/agency/offers/{offer_id}` under Delivery & Responses
- Contextual Agency deep route: `/agency/offer-deliveries?offer_id={offer_id}`
- Agency API: `/api/agencies/{agency_id}/offer-deliveries`
- Authenticated client view: `/portal/travel-options`
- Authenticated client API: `/api/portal/offer-deliveries`
- Platform diagnostics: `/platform/offer-delivery-diagnostics`
- Platform API: `/api/platform/offer-delivery-diagnostics`

No `/admin/*`, `/agent/*`, anonymous public, or alternate client route root is introduced.

Itinerary Builder, Itinerary Options & Fare Brands, Offer Comparison, and Offer Delivery are contextual tools, not primary Agency modules. The Client Portal remains separate because it serves a different actor. Platform diagnostics remain separate because they serve read-only governance. This classification follows the [Product Surface and Workspace Governance](product-surface-workspace-governance.md) review gate.

## Security And Privacy

- Agency isolation is applied to every service query.
- Agency writes require existing agency roles.
- Client access requires an authenticated active portal mapping and recipient authorization.
- Object-level authorization is re-evaluated for every portal request.
- Rich text is not accepted; client questions and wording are plain text metadata.
- Internal costs, margins, evidence, restricted contacts, and governance records are excluded.
- Historical records are archived, expired, revoked, or superseded rather than deleted.
- Platform diagnostics are read-only and cannot impersonate clients.

## Explicit Limitations

Phase 56.4 does not retrieve live fares or availability, call GDS/NDC/airline/provider systems, publish anonymous links, process payment, create bookings, issue tickets or EMDs, send uncontrolled email/SMS, scrape, use AI, run background workers, or seed production records automatically.

## Future Phases

Future work may add explicitly configured notification delivery, richer document rendering/export, and booking-readiness continuation. Those capabilities must continue to use immutable released versions, canonical acceptance records, explicit authorization, and auditable user actions.
