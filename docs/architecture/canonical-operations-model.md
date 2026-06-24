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
- Mobility/medical/pet/special-item details can live in detail payload snapshots until full Reference Data and policy checks are implemented.

## Service Catalogue Target

The Phase 33 `service_catalogue` target should include:

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

Target service families:

- `wheelchair_mobility`
- `medical_support`
- `visual_support`
- `hearing_support`
- `cognitive_support`
- `escort_support`
- `stretcher_extra_seat`
- `passenger_of_size`
- `pet_transport`
- `service_animal`
- `umnr`
- `special_baggage`
- `sports_equipment`
- `musical_instruments`
- `fragile_valuable`
- `oxygen_poc`
