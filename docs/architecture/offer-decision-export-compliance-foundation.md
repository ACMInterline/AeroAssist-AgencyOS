# Offer Decision Export Compliance Evidence Foundation

Phase 38.2 adds a strict metadata-only compliance evidence layer over Phase 38.1 offer decision export governance. It records why a decision export satisfies governance requirements, without performing delivery, booking, pricing, provider, finance, or external decisioning actions.

## Scope

- Compliance evidence records linked to governance records, audit reviews, exports, decision packs, and manual delivery outcomes.
- Compliance requirements that describe the governance obligation being proven.
- Compliance checks that record performed human or deterministic metadata checks.
- Compliance results that capture pass/fail/warning/not-applicable evidence metadata.
- Compliance exceptions that track unresolved, accepted, waived, or resolved compliance gaps.
- Immutable compliance snapshots for review history and audit coverage.

## Agency Routes

- `/agency/offer-decision-export-compliance`
- `/api/agencies/{agency_id}/offer-decision-export-compliance/summary`
- `/api/agencies/{agency_id}/offer-decision-export-compliance/evidence`
- `/api/agencies/{agency_id}/offer-decision-export-compliance/requirements`
- `/api/agencies/{agency_id}/offer-decision-export-compliance/checks`
- `/api/agencies/{agency_id}/offer-decision-export-compliance/results`
- `/api/agencies/{agency_id}/offer-decision-export-compliance/exceptions`
- `/api/agencies/{agency_id}/offer-decision-export-compliance/snapshots`

Agency users can create and update compliance metadata inside their agency scope. They cannot mutate platform-owned source governance outside their tenant through this layer.

## Platform Routes

- `/platform/offer-decision-export-compliance`
- `/api/platform/offer-decision-export-compliance/summary`
- `/api/platform/offer-decision-export-compliance/diagnostics`
- `/api/platform/offer-decision-export-compliance/evidence`
- `/api/platform/offer-decision-export-compliance/requirements`
- `/api/platform/offer-decision-export-compliance/checks`
- `/api/platform/offer-decision-export-compliance/results`
- `/api/platform/offer-decision-export-compliance/exceptions`
- `/api/platform/offer-decision-export-compliance/snapshots`

Platform endpoints are read-only diagnostics and governance visibility. They do not create operational records.

## Safety Boundaries

This foundation does not send email, SMS, notifications, or documents. It does not create public links, deliver PDFs, mutate offers or prices, recommend airlines, book, create reservations, mutate PNRs, issue tickets or EMDs, charge payments, create invoices, settle funds, execute GDS/provider actions, scrape, or call external AI.

`/agency/*` and `/platform/*` remain canonical. No `/agent`, `/admin`, `/api/agent`, or `/api/admin` routes are introduced.
