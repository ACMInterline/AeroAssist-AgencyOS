# Phase 33 — Reference Data Core and Service Catalogue

Phase 33 adds the first controlled Reference Data Core and Service Catalogue foundation for AeroAssist AgencyOS.

## Implemented

- Global reference domains for countries, cities, airports, airlines, currencies, timezones, languages, payments, clients, contacts, documents, cabins, passenger types, guardians, mobility, wheelchair devices, medical equipment, batteries, pets, breeds, and special-item categories.
- Idempotent manual bootstrap script at `backend/scripts/bootstrap_reference_data.py`.
- Authenticated reference APIs for domain discovery, domain listing/search, record create/update, activation/deactivation, and service catalogue listing/search/family grouping.
- Service catalogue records for wheelchair mobility, sensory assistance, medical assistance, extra seat, pet/service animal, unaccompanied minor, oxygen/POC, mobility device, sports equipment, musical instrument, and fragile/valuable item handling.
- Agency UI page at `/agency/reference` with domain counts, active/inactive filtering, search, record create/edit controls, and grouped service catalogue viewing.
- Readiness indicators under `/api/readiness` for reference data enablement, bootstrap availability, domain count, active reference count, and service catalogue count.

## Boundaries

- Reference Data is master lookup data only.
- Airline-specific policies remain in Airline Intelligence and agency overrides.
- Bootstrap is manual and idempotent; it does not run automatically on API startup.
- Management of global records requires platform owner/admin permissions.
- Agency-scoped overrides are model-ready but intentionally deferred until a dedicated agency override workflow.
- No pricing automation, policy scoring, airline execution, GDS/NDC integration, or external provider calls are introduced.

## Validation

- `backend/scripts/smoke_reference_data_core.py` verifies bootstrap idempotency, domain APIs, search, invalid-domain rejection, service catalogue families, activation/deactivation behavior, payload safety, and readiness fields.
