# Offer Decision Export Preview Foundation

Phase 37.6 adds a metadata-only render-preview layer on top of Phase 37.5 offer decision exports.

The foundation lets agency users generate internal preview records that describe how an offer decision export would be structured for human review. It does not render or deliver a live PDF file, create public links, send messages, or execute any operational provider or finance workflow.

## Models

- `offer_decision_export_previews` stores the preview header, source export, source decision pack/explanation references, render/template profile metadata, reviewer metadata, counts, and safety flags.
- `offer_decision_export_preview_sections` stores ordered preview sections such as executive summary, decision pack overview, option comparison, evidence, warnings, review notes, explanations, timeline, acknowledgements, artifact metadata, recipient drafts, and audit trail.
- `offer_decision_export_preview_blocks` stores typed preview blocks such as headings, paragraphs, key-value tables, warning lists, evidence lists, timeline lists, recipient draft blocks, artifact references, and safety disclaimers.
- `offer_decision_export_preview_validations` stores metadata-completeness checks for missing decision pack, explanation, timeline, acknowledgements, recipient draft, artifact metadata, internal reviewer, and safety boundary reminders.
- `offer_decision_export_preview_snapshots` stores immutable metadata snapshots of preview payloads, sections, blocks, validations, and safety flags.

## Agency Operations

Agency endpoints live under `/api/agencies/{agency_id}/offer-decision-export-previews/*`.

Agency users can generate a preview from an existing offer decision export, list/read previews, inspect sections and blocks, run metadata validation, and save immutable preview snapshots.

Generation reads existing export sections, artifact metadata, recipient drafts, export audit events, decision pack metadata, explanations, timeline events, reasons, acknowledgements, and audit snapshots. It writes preview metadata only.

## Platform Diagnostics

Platform endpoints live under `/api/platform/offer-decision-export-previews/*`.

Platform users receive read-only diagnostics: summary counts, preview lists/details, sections, blocks, validations, and snapshots. Platform routes do not create or mutate agency operational records.

## Safety Boundary

Offer decision export previews are internal review metadata only.

They do not:

- deliver or store real PDF files
- send emails or SMS
- create public links
- recommend or rank a winning airline automatically
- mutate offer prices
- mutate offer acceptance state
- create bookings or PNRs
- issue tickets or EMDs
- process payments
- generate invoices
- settle BSP/ARC/accounting records
- scrape airline sites
- call external AI
- execute GDS/NDC/provider actions

Preview validation is metadata completeness checking only. It does not approve, send, publish, book, issue, charge, invoice, or settle.

## Readiness

Readiness exposes `offer_decision_export_preview_foundation` with flags and counts for previews, sections, blocks, validations, immutable snapshots, agency UI, platform UI, metadata-only rendering, automatic sending disabled, public links disabled, real PDF delivery disabled, offer price mutation disabled, provider execution disabled, booking execution disabled, ticket/EMD issuance disabled, and payment/invoice/settlement disabled.
