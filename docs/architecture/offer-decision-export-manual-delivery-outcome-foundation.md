# Offer Decision Export Manual Delivery Outcome Foundation

Phase 37.9 adds metadata-only outcome tracking after a human performs offer decision export delivery outside AgencyOS. It extends the Phase 37.8 manual delivery handoff layer without sending messages, delivering files, mutating offers, changing PNRs, or executing providers.

## Records

- `offer_decision_export_delivery_outcomes` stores outcome headers linked to an agency and manual delivery handoff, with copied export/preview/readiness references, human-recorded status, counts, and safety flags.
- `offer_decision_export_delivery_outcome_events` stores manual timeline-style events such as sent, failed, correction, resend, acknowledgement, issue, resolution, and close records.
- `offer_decision_export_delivery_receipts` stores receipt metadata such as client acknowledgement notes, internal confirmations, external reference labels, and manual notes. These are not public links or delivered files.
- `offer_decision_export_delivery_issues` stores human-recorded delivery issues and resolution metadata.
- `offer_decision_export_delivery_outcome_snapshots` stores immutable metadata snapshots of an outcome, events, receipts, issues, and safety flags.

## API And UI

- Agency APIs live under `/api/agencies/{agency_id}/offer-decision-export-delivery-outcomes`.
- Platform diagnostics live under `/api/platform/offer-decision-export-delivery-outcomes` and are read-only.
- Agency UI lives at `/agency/offer-decision-export-delivery-outcomes`.
- Platform UI lives at `/platform/offer-decision-export-delivery-outcomes`.

## Safety Boundaries

The foundation is manual tracking only. It does not send email or SMS, create public links, deliver real PDFs, mutate offers or prices, recommend airlines, book, create or alter PNRs, issue tickets or EMDs, create invoices, charge payments, settle, scrape, call external AI, or execute providers.

`/agency` and `/platform` remain the only canonical route roots for this layer. No `/agent`, `/admin`, `/api/agent`, or `/api/admin` routes are added.
