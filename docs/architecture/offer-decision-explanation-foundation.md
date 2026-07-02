# Offer Decision Explanation Foundation

Phase 37.4 adds a metadata-only explanation and decision timeline layer on top of Phase 37.3 offer decision packs.

## Models

- `offer_decision_explanations` stores human-authored explanations for an offer decision pack or option.
- `offer_decision_timeline_events` stores audit timeline events such as creation, advisor attachment, review start/completion, note creation, snapshot save, and manual override recording.
- `offer_decision_evidence_references` stores immutable references to advisor results, comparison snapshots, pricing quote metadata, service mechanics metadata, policy records, taxonomy references, warnings, review notes, and knowledge records.
- `offer_decision_reasons` stores human-authored reasons with category and importance.
- `offer_decision_acknowledgements` stores read/review/accept/reject/follow-up acknowledgements.
- `offer_decision_audit_snapshots` stores immutable snapshots of explanations, timeline, evidence references, reasons, and acknowledgements.

## Agency Operations

Agency users can record explanations, append timeline events, create reasons, create acknowledgements, list derived evidence references, and save immutable audit snapshots under `/api/agencies/{agency_id}/offer-decision-explanations/*`.

Finalized explanations are immutable except archive state. Audit snapshots are immutable records and are never edited in place.

## Platform Governance

Platform users can inspect summaries, explanations, timeline events, evidence references, reasons, acknowledgements, and snapshots under `/api/platform/offer-decision-explanations/*`.

Platform routes are read-only diagnostics. They do not expose mutation routes.

## Safety Boundary

The explanation layer does not rank airlines, select winners, alter offer pricing, create bookings, create PNRs, issue tickets, issue EMDs, process payments, create invoices, perform settlement, scrape websites, call external AI, or execute providers.

Complexity scores and advisor evidence remain operational indicators only. Decision explanations are human-authored audit metadata.

## Readiness

Readiness exposes `offer_decision_explanation_foundation` with flags and counts for explanations, timeline events, evidence references, reasons, acknowledgements, immutable snapshots, agency UI, platform UI, human review only, automatic recommendation disabled, provider execution disabled, booking disabled, ticketing disabled, EMD disabled, payment disabled, invoice disabled, and settlement disabled.
