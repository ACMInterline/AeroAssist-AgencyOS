# Service Catalogue Operational Contract

Phase 36.2.5 promotes Service Catalogue from static reference output to the canonical service foundation for existing request, rules, offer, acceptance, booking readiness, document, and future EMD workflows.

## Ownership

- Platform owners create, edit, archive, and reorder service catalogue records through `/api/platform/service-catalogue`.
- Agencies consume active service records through `/api/reference/service-catalogue`.
- Agency corrections flow through reference suggestions; agencies do not mutate the global catalogue.

## Operational Fields

`ServiceCatalogueRecord` now supports:

- core fields: service key, label, description, category, subcategory, status, visibility, sort order, platform-managed flags
- applicability fields: passenger/trip/segment type scope, passenger scope, segment scope, and segment defaults
- request UI behavior: form enablement, required fields, validation rules, helper/warning text
- rules/services behavior: rules category, default service type, exception engine, policy checks
- SSR/OSI behavior: SSR code, SSR template, OSI template, staff review, booking preview
- offer/acceptance/readiness behavior: offer feasibility, offer pricing, acceptance snapshot, booking readiness, pricing category, EMD applicability, fee expectations
- documents behavior: required documents, client document summary, internal handling notes
- pet/special item linkage: pet taxonomy and special item taxonomy links
- audit fields: created/updated users and timestamps

## Compatibility Layer

Existing service codes continue to work. The compatibility helpers resolve service catalogue records by service key, old service code, default SSR code, SSR code, or default service type.

Current consumers preserve catalogue metadata where available:

- `RequestedService` and `RequestPassengerSegmentService` store catalogue id, key, and snapshot.
- `PassengerServiceRequest` stores catalogue id, key, label, category, and snapshot.
- `UnifiedExceptionRule` can narrow matching by service key and service catalogue category.
- SSR/OSI generation prefers catalogue SSR code and templates and merges catalogue required documents.
- Offer Builder passes catalogue context into rule evaluation and SSR/OSI preview rows.
- Offer Acceptance and Booking Readiness preserve service catalogue key, label, category, and snapshot in accepted service snapshots.
- Trip service items preserve catalogue references when copied from requests.

## Boundaries

This contract does not create bookings, PNRs, tickets, EMDs, invoices, payments, supplier actions, or document designer output. It prepares the operational metadata used by those later workflows while keeping staff review and platform governance explicit.
