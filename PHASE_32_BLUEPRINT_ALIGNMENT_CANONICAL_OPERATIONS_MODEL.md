# Phase 32 — Blueprint Alignment, Canonical Operations Model, and Gap Map

Phase 32 synchronizes AeroAssist AgencyOS with the original Travel Agency Micro-ERP + CRM blueprint while preserving the current FastAPI, Mongo-compatible repository, React, and Docker architecture. PocketBase-style blueprint language is treated as schema inspiration only, not as a migration target.

## Implemented

- Created formal blueprint alignment/gap map at `docs/architecture/agencyos-blueprint-alignment-gap-map.md`.
- Created canonical operations rules at `docs/architecture/canonical-operations-model.md`.
- Created current model inventory at `docs/architecture/current-model-inventory.md`.
- Added non-destructive model foundations for trip dossiers, trip passengers, trip segments, request case flags, passenger/segment service applicability, pets, pet segment transport, special items, and special-item segment applicability.
- Added optional request/intake alignment fields for `source_entry_path`, `submission_channel`, `account_origin_at_submission`, trip linkage, and canonical alignment notes.
- Updated readiness/platform phase labels and informational alignment flags.
- Updated roadmap sequence for Reference Data, segment-scoped services, trip dossiers, offers, GDS mirror records, invoices/payments, documents, communications/tasks, portal, reporting/automation, and airline policy knowledge.

## What Already Exceeds The Blueprint

- Production deployment and VPS packaging.
- Backup automation and readiness checks.
- Agency branding/theme personalization.
- Logo asset lifecycle and CMS media handling.
- CMS/public website publishing and public website request forms.
- App shell/sidebar polish.
- Request intake and operational request builder.
- Assistance assessment driven SSR recommendation.

## Non-Destructive Strategy

- Existing collection names remain unchanged.
- No production data is deleted or migrated.
- Existing request builder, request intake, CMS, branding, and media behavior remains backward compatible.
- New model classes are additive foundations only; they do not enable GDS imports, pricing, offer automation, portal expansion, or payments.

## Known Limits

- No Reference Data UI or service catalogue yet.
- No full trip dossier UI yet.
- No new offer builder/comparison matrix yet.
- No GDS import/mirror workflow yet.
- No invoice/payment expansion in this phase.
- No broader client portal foundation in this phase.
