# Service Mechanics Mapping Foundation

Phase 36.9 connects canonical services from Phase 36.8 to airline/GDS communication and EMD payment metadata.

## Conceptual Split

| Layer | Purpose | Phase 36.9 behavior |
|---|---|---|
| Service taxonomy | Canonical meaning of the service | Reused from Phase 36.8 domain/family/variant codes |
| SSR/OSI communication | How the service is requested, confirmed, rejected, or manually handled | Stored in communication rules, templates, requirements, status recognition rules, and rejection patterns |
| EMD/RFIC/RFISC payment | How the service may be paid, represented, associated, or lifecycle-limited | Stored in payment rules, EMD issuance metadata, RFIC/RFISC mappings, interline rules, and lifecycle rules |

## Collections

- `airline_service_communication_rules`
- `ssr_osi_templates`
- `ssr_osi_requirements`
- `ssr_status_recognition_rules`
- `airline_rejection_patterns`
- `airline_service_payment_rules`
- `airline_emd_issuance_rules`
- `airline_rfic_rfisc_mappings`
- `airline_emd_interline_rules`
- `airline_emd_lifecycle_rules`
- `policy_candidate_mechanics_links`

## APIs And UI

- Platform governance APIs live under `/api/platform/service-mechanics/*`.
- Agency lookup APIs live under `/api/agencies/{agency_id}/service-mechanics/*`.
- Platform UI route: `/platform/service-mechanics`.
- Agency UI route: `/agency/service-mechanics`.

Agency routes can read global mechanics and create agency-scoped candidate mechanics links. They do not mutate global mechanics records.

## Lookup Contract

`POST /api/platform/service-mechanics/lookup` and `POST /api/agencies/{agency_id}/service-mechanics/lookup` accept airline code plus canonical domain/family/variant codes.

The response always separates:

- `communication`
- `payment`

No-match results return warnings rather than errors.

## Safety Boundaries

Phase 36.9 does not:

- transmit SSR, OSI, OTHS, remarks, or NDC service requests
- create live bookings or PNRs
- issue, refund, exchange, void, or reissue tickets or EMDs
- capture payments, post invoices/accounting, or perform settlement
- scrape airline websites or call external AI
- auto-promote agency-local links to global records
- add `/agent` or `/admin` routes
- perform destructive Mongo index migrations

All Mongo indexes added for Phase 36.9 use explicit stable names and the compatibility-aware index helper.
