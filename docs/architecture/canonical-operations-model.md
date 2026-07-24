# Canonical Operations Model

This document defines the target canonical operations model for AgencyOS. It translates the original Travel Agency Micro-ERP + CRM blueprint into the current FastAPI/Mongo/React architecture.

The enforceable per-domain ownership contract now lives in the
[Canonical Domain Ownership Map](canonical-domain-ownership-map.md), with
duplicate writers and future reconciliation tracked in the
[Canonical Domain Migration Register](canonical-domain-migration-register.md).
`agency_id` is the canonical tenant boundary; `workspace_id` is operational
context only. Until that register's exit criteria are met, selected targets are
architectural owners rather than a claim that compatibility writers have
already been migrated.

## Main Entities

- **Client**: payer/requester/account entity. A client may be an individual, household, or organization.
- **Passenger**: traveler/beneficiary registry entity. Passenger must not be conflated with payer/requester.
- **Request**: work intake/operational demand. A request may exist without a trip.
- **Trip**: operational dossier shell that groups accepted/commercialized work, itinerary, passengers, bookings, documents, tasks, and communications.
- **Offer**: proposal/comparison object. Offers may exist before trip creation.
- **Booking**: mirror/tracking record for booked itinerary state.
- **Ticket**: mirror/tracking record for ticket state.
- **EMD**: mirror/tracking record for ancillary document state.
- **Invoice**: commercial record for billing/payment tracking.
- **Document**: generated or stored output attached to request/trip/client/passenger context.
- **Task**: staff work item with owner, priority, due state, visibility, and operational context.
- **Communication**: message/note/email/portal communication with visibility boundaries.
- **Activity**: audit/timeline event recording state changes and staff/system actions.
- **Reference Data**: controlled catalogue and lookup data, including service catalogue.
- **Airline Policy Rule**: airline-specific decision support knowledge separate from reference data.

## Mandatory Rules

- Trip is the operational dossier shell.
- Never use `request_id` as `trip_id`.
- Requests may exist without trips.
- Offers may exist before trip creation.
- Accepted or commercialized offers should attach to a trip as early as possible.
- Imported GDS records must preserve raw source payloads.
- Reference data and airline policy rules are separate subsystems.
- Segment-first itinerary is authoritative.
- One-way/round-trip/multi-city are derived UI labels only, not operational truth.
- Services are passenger + segment scoped.
- Pets are segment-scoped through transport applicability records.
- Special items are segment-scoped through transport applicability records.
- Payer/requester and beneficiary must not be conflated.
- Public, portal, and admin request forms share one canonical intake model but have different UX.

## Request Alignment Rules

- `source_entry_path` identifies the UX/API entry route where the request began.
- `submission_channel` identifies whether data came from public site, agency website, portal, staff console, import, or API.
- `account_origin_at_submission` records whether the submitter was existing, new public contact, portal account, staff-created, imported, or unknown.
- Passenger link modes are `existing` or `unresolved`. The legacy `new_inline` input value is accepted only for compatibility and is normalized to an unresolved request passenger; it must not create a master profile.
- `PassengerProfile` is created or linked only after an explicit staff identity-confirmation action with complete identity data or a selected existing profile.
- Segment records are canonical for itinerary shape; summary fields are display conveniences.
- Requested services should use passenger and segment scoping rather than unstructured notes whenever possible.
- Mobility/medical/pet/special-item details use Phase 33 Reference Data and Phase 34 normalized child records while deeper airline policy checks are implemented separately.

## Phase 34 Request Normalization

Phase 34 implements the canonical request child model:

- `request_segments` remain the segment-first itinerary source for requests.
- `request_passengers` are request-context beneficiary rows and may remain unresolved until staff can link or create a master passenger profile.
- `request_passenger_segment_services` records bind one passenger, one segment, and one service catalogue/service-family context.
- `request_pets` stores request/passenger-linked animal details, while `request_pet_segment_transport` stores exact segment transport applicability.
- `request_special_items` stores request/passenger-linked item details, while `request_special_item_segments` stores exact segment transport applicability.
- `request_case_flags` summarize medical, document, pet, special-item, and scoped-service conditions but do not replace exact child records.

## Phase 35 Trip Dossier Foundation

Phase 35 implements the Trip Dossier as the agency operational shell:

- `trip_dossiers` have independent generated IDs and `TRP-YYYYMMDD-XXXX` references.
- `TravelRequest.trip_id` is an additive primary trip back-reference only; it is not the trip identity.
- `TripDossier.linked_request_ids` records the request scope for the operational shell.
- `trip_passengers`, `trip_segments`, and `trip_service_items` copy normalized request child records for operational use while preserving source request child IDs.
- Request-to-trip conversion does not delete, replace, or destructively mutate request records.
- `trip_timeline_events` and `audit_events` record trip creation, conversion, linking, unlinking, child copying, summary rebuilding, updating, and archiving.
- Pets and special items remain request-level child records in this phase and are summarized on the trip only.

Offer, booking, ticket, EMD, document, invoice, payment, claim, and communication workflows should attach through the trip dossier where relevant in future phases, but Phase 35 does not implement those expansions.

## Service Catalogue

Phase 33 implements `service_catalogue` as controlled master lookup data. It includes:

- `service_code`
- `service_label`
- `service_family_code`
- `default_ssr_code`
- `beneficiary_type`
- `requires_segment_scoping`
- `requires_policy_check`
- `requires_document_check`
- `requires_manual_pricing`
- `input_schema_json`
- `is_active`

Implemented service families:

- `wheelchair_mobility`
- `sensory_assistance`
- `medical_assistance`
- `seating_space`
- `pets_animals`
- `minor_assistance`
- `special_items`

Airline-specific rules, lead times, acceptance criteria, source documents, and exceptions remain in Airline Intelligence rather than Reference Data.
Sports equipment, musical instruments, fragile/valuable items, oxygen, POC, stretcher, extra seat, pet, and mobility-device handling are service catalogue records within those families.

## Phase 33.1 Reference Data Governance

Reference Data is global, platform-owned master data:

- Approved `global_reference_records` are available to all agencies and are the canonical lookup source.
- Agency users may submit `reference_data_suggestions`, but suggestions are not active globally until reviewed.
- Platform owners/admins review suggestions and may approve, reject, request more information, merge, or archive them.
- Manual `reference_import_batches` validate and import global records without destructive deletes or startup seeding.
- Agency-local overrides, when introduced, must be clearly local and must not be confused with global master records.
- Phase 34.2 adds the platform-only `/platform/reference` management console and keeps agency reference pages consume-and-suggest only.
- Enriched country metadata remains on `global_reference_records.metadata_json` for legacy compatibility while exposing structured platform editor fields.
- Phase 34.3 adds platform-owned import packs and normalization services for countries, airports, airlines, currencies, languages, and regions.
- Enrichment imports are dry-run first, non-destructive by default, and report missing cross-links without activating unreviewed external data.

The same governance shape is reserved for future airline policy learning:

- `agency_policy_overrides` remain agency-local.
- `policy_rule_suggestions` will allow agencies to submit evidence-backed improvements.
- `policy_evidence` preserves source material for reviewer decisions.
- Approved policy suggestions may become global policy rules; rejected suggestions remain local/rejected/archived.

## Phase 34.1 Field Library And Form Profiles

The Global Field Library is platform-owned schema governance:

- `global_field_definitions` define canonical field keys, canonical payload paths, field families/types, safety flags, required levels, validation metadata, and agency override permissions.
- Agencies configure `agency_form_profiles` and `agency_form_field_settings` to control display, labels, helper text, order, optional required overrides, and custom questions.
- Agencies cannot change canonical meaning, service logic, SSR interpretation, policy formulas, pricing formulas, or system-required compliance fields.
- `system_required` fields cannot be hidden.
- `internal_only` fields cannot be exposed in public contexts.
- Agency custom questions normalize under `agency_custom_fields` in canonical payloads.

Form profiles are a UI/presentation layer over canonical request payloads. They do not replace backend validation or the canonical request/intake models.

## Canonical Commercial Lifecycle

Commercial operations use one enforced lineage:

`TravelRequest -> OfferWorkspace -> OfferOption -> OfferAcceptance ->
TripAcceptedOfferSnapshot -> TripDossier -> OfferBookingHandoff ->
BookingRecord -> TicketRecord / EMDRecord`.

OfferWorkspace is the sole target mutable Offer aggregate and each option is a
same-Agency ordered child. Delivery freezes a version; material changes create
a governed superseding version. Acceptance targets exact Offer and Option
versions and creates one immutable hashed snapshot. Normal Trip confirmation
requires that snapshot. Request conversion before acceptance is planning-only.

BookingWorkspace holds readiness and operator workflow. It cannot establish
external booking truth. BookingRecord requires governed manual/import/source
evidence and owns the current PNR result. Normal Ticket/EMD records require a
same-Agency BookingRecord; explicit standalone imports retain mode, source,
reason, actor, and reconciliation evidence. See
[Canonical Commercial Lifecycle Contract](canonical-commercial-lifecycle-contract.md).

## Canonical Request V4 Aggregate

The Request lifecycle begins with either intake provenance or an Agency-created
`TravelRequest`. For new records, `TravelRequest.canonical_payload` is the
typed source of truth. Ordered segments, unresolved request passengers,
passenger-scoped services, animals, and special items are validated as one
aggregate and projected into their existing operational collections.

The aggregate may exist before a Trip. Explicit request-to-trip conversion
continues to map the Request into the downstream operational dossier. Offer and
Trip consumers read deterministic compatibility projections; they do not own
or mutate Request V4 truth. Accepted downstream snapshots remain immutable.
