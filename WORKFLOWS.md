# Workflows

## Agency Setup

1. Platform admin creates or approves an `agency`.
2. Platform creates `agency_workspace`.
3. Agency owner is invited.
4. Agency owner completes branding, contact, legal, website, and portal settings.
5. Agency staff users and roles are created.
6. Agency selects website template and configures request intake.
7. Agency may customize document templates and default fees.

Outcome: agency can operate a branded workspace, public website, and client portal.

## Client Self-Registration

1. Visitor enters from agency website or portal link.
2. Visitor creates a client account.
3. System creates `client_profile` and `client_account` with `email_unverified` status.
4. Before email verification, the client can complete basic own profile fields and submit the registration, but cannot view existing agency records, accept offers, see bookings, access documents, pay, or create passenger relationships beyond a provisional self profile.
5. After email verification, status changes to `active` unless the agency requires staff review; if review is required, portal access remains restricted by record visibility and relationship permissions until staff approves.
6. Client may create passenger profiles only if agency self-service settings allow it.
7. System creates relationship records, usually `self` for the client and any additional relationships requested, with `proposed` relationship status until accepted by staff or policy.
8. Agency staff receives notification and can review, approve, restrict, suspend, or archive.

## Staff-Created Client Invitation

1. Staff creates `client_profile` without portal access.
2. Staff creates or links passenger profiles.
3. Staff creates `client_passenger_relationship` records with permissions.
4. Staff later sends portal invitation.
5. Client account status changes from `no_portal_access` to `invited`.
6. Client accepts invitation and sets credentials.
7. Client account status changes to `active`.

Staff can resend invitations, suspend portal access, archive accounts, and edit client/passenger associations.

## Client/Passenger Relationship Workflow

1. Staff or permitted client proposes a passenger link.
2. Relationship type and permissions are selected.
3. Consent status is recorded.
4. Validity dates are set if temporary.
5. Relationship controls portal visibility, editing, document upload, travel requests, payment, and notifications.
6. Relationship changes are audited in timeline events.

Examples:

- Company client pays for employee passenger.
- Parent manages child passenger.
- Assistant manages VIP passenger.
- Passenger later receives their own portal access.

## Request Workflow

1. Request is created from portal, website form, staff entry, email, phone, or WhatsApp summary.
2. Client and requesting contact are recorded.
3. Passengers are linked.
4. Intended route, dates, flexibility, services, pets/items, document needs, urgency, and notes are captured.
5. Staff adds internal notes and documents.
6. Optional airline intelligence hints identify policies, missing data, required documents, feasibility warnings, and contacts.
7. Request may become linked to one or more offers.
8. Request may be closed without offer.

Request validity does not depend on airline evaluation.

## Manual Offer Workflow

1. Staff starts offer from client, passenger, manual entry, airline research, or future imported GDS data.
2. Staff selects client and passengers.
3. Staff manually researches candidate options through GDS, airline portals, supplier checks, OTA affiliate fares, or direct contacts.
4. Staff creates up to 3 route alternatives.
5. Staff creates up to 3 fare bundles per route alternative.
6. Staff enters fare, tax, airline ancillary fees, agency service fees, service-specific fees, notes, and recommendation labels.
7. Airline intelligence may provide policy hints, EMD readiness, document requirements, contacts, and warnings.
8. Staff reviews client-visible wording and internal notes.
9. Offer is sent and a snapshot is created.

## Request-Linked Offer Workflow

1. Staff opens an existing request.
2. Staff creates offer from request context.
3. Request passengers, route intents, services, documents, and notes prefill offer draft.
4. Staff manually constructs route alternatives and fare bundles.
5. Staff resolves missing passenger or service information.
6. Offer is sent and linked to the request.
7. Request status updates to offered, pending response, accepted, rejected, expired, or closed.

## Client Offer Acceptance

1. Client opens branded offer in portal or via secure link.
2. Client compares route alternatives and fare bundles.
3. Client sees schedule, route, airlines, travel time, baggage, flexibility, special service support, ancillary charges, total price, and agent recommendation.
4. Client accepts, rejects, comments, or requests changes.
5. Acceptance records selected route alternative and fare bundle.
6. Acceptance snapshot is created.
7. Staff receives notification and may create booking.

## Booking / Ticket / EMD Workflow

1. Staff creates booking from accepted offer or manually.
2. Staff records passengers, segments, PNR, status, and chosen offer reference if applicable.
3. Staff tracks service confirmations.
4. Staff uploads or generates booking documents.
5. Ticket records are created per passenger.
6. Ticket numbers, validating airlines, fare/tax breakdowns, status, issue date, and receipt documents are recorded.
7. EMD records are created for ancillary or service documents.
8. EMD service code, number, RFIC, RFISC, amount, status, associated ticket/booking/service, and receipt are recorded.
9. Booking timeline updates throughout.

## Invoice / Payment Workflow

1. Staff creates invoice from offer, booking, or manual line items.
2. Invoice lines include fares, taxes, airline pass-through fees, agency service fees, service-specific fees, and adjustments.
3. Branded invoice document is generated.
4. Invoice is sent or made visible in portal.
5. Payment record is created with due date and method.
6. Payment status changes through due, pending, received, failed, refunded, or reconciled.
7. Reconciliation notes are stored.

## Refund / Exchange Workflow

1. Staff opens refund/exchange case from ticket, EMD, booking, or client request.
2. Original ticket/EMD is referenced.
3. Airline policy and EMD/RFIC/RFISC knowledge may be consulted and snapshotted.
4. Staff records fare difference, tax difference, airline penalty, agency fee, refund amount, and notes.
5. New ticket/EMD is linked if applicable.
6. Client-visible confirmation/refund documents are generated.
7. Invoice/payment adjustments are recorded.
8. Case is closed with final status and timeline.

## Airline Knowledge Update Workflow

1. Platform knowledge editor creates or updates airline knowledge.
2. Source evidence is attached.
3. Structured data, applicability, effective dates, and visibility are completed.
4. Record enters draft or review status.
5. Reviewer validates source, confidence, operational wording, and agency impact.
6. Version is approved and published to agencies.
7. Existing operational records do not change; future evaluations and lookups use new published version.

## Global Publishing To Agencies

1. Platform publishes global airline intelligence, templates, taxonomy, or reference data.
2. Agencies receive read access according to subscription and feature configuration.
3. Agency overrides remain intact.
4. If an override conflicts with a new global version, the system should flag review instead of overwriting agency data.
5. New operational snapshots record the currently used global version plus any agency override version.

## Review Hardening: Cross-Record Lifecycle Rules

- A request may exist without an offer, and an offer may exist without a request.
- A request can produce multiple offers over time; each offer should record whether it is active, superseded, rejected, expired, or accepted.
- An accepted offer does not automatically become a booking. Staff must intentionally create the booking because external GDS, portal, supplier, or direct-airline actions may still be required.
- A booking may be created from an accepted offer, manually from client/passenger context, or from an existing PNR. Manual bookings should still support later invoices, documents, messages, and timelines.
- Ticket and EMD records should be linked to the booking and passenger. EMD records should also link to the related ticket or service context when available.
- Invoices may be created from offer, booking, ticket, EMD, refund/exchange, or manual line items. The invoice must preserve line-item source references when derived from operational records.
- Payments apply to invoices in MVP. If unapplied payments are later supported, that requires a separate allocation model.
- Refund/exchange cases may originate from a client request, booking, ticket, EMD, invoice dispute, or staff-created servicing case.
- Generated documents must link to the record that produced them and to the message or portal publication event when sent.
- Messages and timeline events should be attachable across request, offer, booking, ticket, EMD, invoice, payment, refund/exchange, document, client, and passenger contexts.

## Review Hardening: Snapshot Timing By Workflow

- Request workflow: no snapshot is required merely to create a request, but evaluated policy hints should be logged with source versions if staff relies on them.
- Offer workflow: create an immutable snapshot when an offer is sent and again when a client accepts a specific route alternative and fare bundle.
- Booking workflow: create a booking snapshot when staff creates the booking, including selected offer context if applicable.
- Ticket workflow: create a ticket snapshot when each ticket is issued.
- EMD workflow: create an EMD snapshot when each EMD is issued, including RFIC/RFISC and service-code mapping provenance.
- Invoice workflow: create an invoice snapshot when the invoice is issued or made visible to the client.
- Payment workflow: payments do not need airline knowledge snapshots, but they do need immutable audit events and invoice balance history.
- Refund/exchange workflow: create a snapshot when the case decision is sent to the client and when the refund/exchange is processed.
- Document workflow: create or reference a snapshot when a client-facing document is generated, sent, downloaded, or archived.

## Architecture Decisions: Workflow Gap Resolutions

- Status enums are defined in `CANONICAL_DATA_MODEL.md`.
- Offer acceptance is allowed only for active verified client accounts with required relationship permissions. If required passenger documents or payment are incomplete, acceptance records the selected option but booking creation remains a staff action.
- Quote expiry, price changes, and unavailable fare bundles are represented with offer, route alternative, and fare bundle statuses: `expired`, `price_changed`, `unavailable`, `withdrawn`, or `superseded`.
- Client messages notify staff in MVP. Automatic task creation from messages is later scope unless staff manually creates a task.
- External communications from WhatsApp, email, and phone are captured as message records with channel metadata and timeline events. Uploaded transcripts or screenshots are optional document attachments.
