# Offer Decision Export Governance Foundation

Phase 38.1 adds a metadata-only governance layer over the completed offer decision export lifecycle and the Phase 38.0 audit review foundation. It gives agency users a place to record governance records, rules, retention policy metadata, legal basis metadata, archive status metadata, governance exceptions, and immutable governance snapshots without executing delivery or operational actions.

## Scope

- `OfferDecisionExportGovernanceRecord` links governance metadata to export, audit review, decision pack, and manual outcome context.
- `OfferDecisionExportGovernanceRule` records human-reviewed rule metadata.
- `OfferDecisionExportRetentionPolicy` records retention period and review-action metadata only.
- `OfferDecisionExportLegalBasis` records legal basis labels and evidence references as metadata.
- `OfferDecisionExportArchiveStatus` records archive status metadata without performing real archive execution.
- `OfferDecisionExportGovernanceException` records governance exceptions and manual resolutions.
- `OfferDecisionExportGovernanceSnapshot` stores immutable governance snapshots for audit review.

## Agency Routes

- `/api/agencies/{agency_id}/offer-decision-export-governance/summary`
- `/api/agencies/{agency_id}/offer-decision-export-governance/governance-records`
- `/api/agencies/{agency_id}/offer-decision-export-governance/rules`
- `/api/agencies/{agency_id}/offer-decision-export-governance/retention-policies`
- `/api/agencies/{agency_id}/offer-decision-export-governance/legal-bases`
- `/api/agencies/{agency_id}/offer-decision-export-governance/archive-statuses`
- `/api/agencies/{agency_id}/offer-decision-export-governance/governance-exceptions`
- `/api/agencies/{agency_id}/offer-decision-export-governance/snapshots`

The agency UI is `/agency/offer-decision-export-governance`.

## Platform Routes

- `/api/platform/offer-decision-export-governance/summary`
- `/api/platform/offer-decision-export-governance/diagnostics`
- `/api/platform/offer-decision-export-governance/governance-records`
- `/api/platform/offer-decision-export-governance/rules`
- `/api/platform/offer-decision-export-governance/retention-policies`
- `/api/platform/offer-decision-export-governance/legal-bases`
- `/api/platform/offer-decision-export-governance/archive-statuses`
- `/api/platform/offer-decision-export-governance/governance-exceptions`
- `/api/platform/offer-decision-export-governance/snapshots`

The platform UI is `/platform/offer-decision-export-governance`. Platform endpoints are read-only diagnostics.

## Safety Boundaries

This foundation does not send email or SMS, create public links, deliver real PDFs, mutate offers or prices, recommend airlines, book, mutate PNRs, ticket, issue EMDs, charge, invoice, settle, scrape, call external AI, or execute providers. Retention, legal basis, and archive status records are governance metadata only; they do not delete, archive, transmit, or deliver records.
