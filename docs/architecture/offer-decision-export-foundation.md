# Offer Decision Export Foundation

Phase 37.5 adds a metadata-only export layer on top of Phase 37.3 offer decision packs and Phase 37.4 offer decision explanations.

The foundation lets agency users generate internal review snapshots for offer decision evidence. Export records preserve what would be included in a human-review PDF or JSON package, but they do not create public links, send email, store live binary files, or perform any provider or finance execution.

## Models

- `offer_decision_exports` stores the export header, source decision pack, source explanation references, counts, and safety flags.
- `offer_decision_export_sections` stores ordered sections for decision pack options, evidence, warnings, review notes, explanations, timeline events, reasons, acknowledgements, and audit snapshots.
- `offer_decision_export_artifacts` stores metadata-only PDF and JSON artifact records with filenames, MIME types, checksums, and safety flags.
- `offer_decision_export_recipient_drafts` stores unsent recipient draft metadata for future reviewed delivery workflows.
- `offer_decision_export_audit_events` stores export creation, artifact metadata creation, recipient draft creation, and related audit events.

## Agency Operations

Agency endpoints live under `/api/agencies/{agency_id}/offer-decision-exports/*`.

Agency users can generate an export snapshot from an existing offer decision pack, list exports, read export details, inspect artifact metadata, inspect recipient drafts, and review audit events.

Generation reads existing decision pack options, evidence, warning summaries, review notes, explanations, timeline events, reasons, acknowledgements, and audit snapshots. It creates export metadata only and does not mutate offer options, prices, recommendations, bookings, tickets, EMDs, payments, invoices, settlements, or provider state.

## Platform Diagnostics

Platform endpoints live under `/api/platform/offer-decision-exports/*`.

Platform users receive read-only diagnostics: summary counts, export lists/details, artifact metadata, and audit events. Platform routes do not create or mutate agency operational records.

## Safety Boundary

Offer decision exports are review/audit metadata only.

They do not:

- send emails automatically
- create public links
- generate or store live binary PDF files
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

PDF export metadata is an artifact record describing an export snapshot. It is not a delivery channel, public URL, or provider execution hook.

## Readiness

Readiness exposes `offer_decision_export_foundation` with flags and counts for decision exports, export sections, artifact metadata, recipient drafts, audit events, PDF export metadata, automatic sending disabled, public links disabled, offer price mutation disabled, provider execution disabled, booking execution disabled, ticket/EMD issuance disabled, and payment/invoice/settlement disabled.
