# Canonical Operations Model

This document defines the target canonical operations model for AgencyOS. It translates the original Travel Agency Micro-ERP + CRM blueprint into the current FastAPI/Mongo/React architecture.

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
- Passenger link modes are `existing`, `new_inline`, or `unresolved`.
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
