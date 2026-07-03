# Offer Decision Export Release Readiness Foundation

Phase 37.7 adds a metadata-only human approval and manual release readiness layer on top of Phase 37.6 offer decision export render previews.

## Records

- `offer_decision_export_approvals` stores human approval requests linked to export previews, source exports, decision packs, assigned reviewers, approval status, checkpoint counts, readiness counts, and safety flags.
- `offer_decision_export_approval_checkpoints` stores ordered metadata checkpoints for preview review, artifact metadata review, recipient draft review, safety boundary review, internal approval, and manual release readiness.
- `offer_decision_export_release_readiness` stores manual release readiness records linked to previews and approvals, active/released hold counts, immutable snapshot counts, source counts, and readiness summaries.
- `offer_decision_export_release_holds` stores active or released manual holds with reason, severity, release notes, and metadata-only safety flags.
- `offer_decision_export_release_snapshots` stores immutable release readiness snapshots containing readiness, approval detail, holds, source counts, and safety flags.

## Agency APIs

Agency endpoints live under `/api/agencies/{agency_id}/offer-decision-export-releases/*`.

- `GET /summary`
- `GET /approvals`
- `POST /approvals`
- `GET /approvals/{approval_id}`
- `GET /approvals/{approval_id}/checkpoints`
- `POST /approvals/{approval_id}/checkpoints`
- `POST /approvals/{approval_id}/status`
- `GET /readiness`
- `POST /readiness`
- `GET /readiness/{readiness_id}`
- `GET /readiness/{readiness_id}/holds`
- `POST /readiness/{readiness_id}/holds`
- `POST /readiness/{readiness_id}/holds/{hold_id}/release`
- `GET /readiness/{readiness_id}/snapshots`
- `POST /readiness/{readiness_id}/snapshots`

Agency users can create and review approval/readiness metadata only. They cannot send exports, create public links, deliver real PDFs, execute providers, mutate offers or prices, recommend airlines automatically, book, ticket, issue EMDs, invoice, charge, or settle.

## Platform APIs

Platform endpoints live under `/api/platform/offer-decision-export-releases/*`.

- `GET /summary`
- `GET /approvals`
- `GET /readiness`
- `GET /holds`
- `GET /snapshots`

Platform endpoints are read-only diagnostics for governance visibility.

## Frontend

- `/agency/offer-decision-export-releases` shows release metrics, preview-linked approval creation, checkpoint recording, manual approval status, readiness creation, release holds, and immutable release snapshots.
- `/platform/offer-decision-export-releases` shows global read-only diagnostics for approvals, readiness, holds, snapshots, and safety flags.

## Readiness

Readiness exposes `offer_decision_export_release_readiness_foundation` with flags and counts for approvals, checkpoints, readiness records, holds, immutable snapshots, agency UI, platform UI, human approval required, automatic sending disabled, public links disabled, real PDF delivery disabled, offer price mutation disabled, provider execution disabled, booking execution disabled, ticket/EMD issuance disabled, and payment/invoice/settlement disabled.

## Safety Boundaries

Phase 37.7 is review/audit metadata only. It does not send emails or SMS, create public links, perform real PDF delivery, mutate offers or prices, auto-recommend airlines, book, create live PNRs, ticket, issue EMDs, invoice, charge, settle, scrape, call external AI, or execute providers. `/agency` and `/platform` remain canonical route roots; `/agent` and `/admin` aliases are not added.
