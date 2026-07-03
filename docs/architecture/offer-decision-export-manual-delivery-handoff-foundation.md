# Offer Decision Export Manual Delivery Handoff Foundation

Phase 37.8 adds a metadata-only manual delivery handoff workspace on top of Phase 37.7 export release readiness. It records what a human agent intends to do outside AgencyOS after approval, without sending anything from the system.

## Records

- `offer_decision_export_delivery_handoffs` stores handoff headers linked to offer decision exports, optional previews, approvals, release readiness records, manual method, manual status, counts, safety summary, and safety flags.
- `offer_decision_export_delivery_recipients` stores recipient metadata such as display name, optional email/phone metadata strings, manual method, manual status, and notes. These records are not sending targets.
- `offer_decision_export_delivery_attachments` stores attachment metadata such as source artifact/preview reference, filename, metadata file type, source type, size label, storage-reference metadata, `public_link_created=false`, and `real_file_delivered=false`.
- `offer_decision_export_delivery_instructions` stores internal manual handoff instructions and checklist metadata with completion state.
- `offer_decision_export_delivery_snapshots` stores immutable metadata snapshots of the handoff, recipients, attachments, instructions, and safety flags.

## Agency APIs

Agency endpoints live under `/api/agencies/{agency_id}/offer-decision-export-deliveries/*`.

- `GET /summary`
- `POST /handoffs`
- `GET /handoffs`
- `GET /handoffs/{handoff_id}`
- `PATCH /handoffs/{handoff_id}/status`
- `POST /handoffs/{handoff_id}/recipients`
- `GET /handoffs/{handoff_id}/recipients`
- `PATCH /recipients/{recipient_id}/status`
- `POST /handoffs/{handoff_id}/attachments`
- `GET /handoffs/{handoff_id}/attachments`
- `POST /handoffs/{handoff_id}/instructions`
- `GET /handoffs/{handoff_id}/instructions`
- `PATCH /instructions/{instruction_id}/completion`
- `POST /handoffs/{handoff_id}/snapshots`
- `GET /handoffs/{handoff_id}/snapshots`

Agency endpoints create and update manual handoff metadata only. Status changes record human state; they do not send, publish, upload, charge, book, issue, or execute anything.

## Platform APIs

Platform endpoints live under `/api/platform/offer-decision-export-deliveries/*`.

- `GET /summary`
- `GET /handoffs`
- `GET /handoffs/{handoff_id}`
- `GET /recipients`
- `GET /attachments`
- `GET /instructions`
- `GET /snapshots`

Platform endpoints are read-only diagnostics for governance visibility.

## Frontend

- `/agency/offer-decision-export-deliveries` shows handoff metrics, handoff creation from exports/release readiness, selected handoff detail, recipient metadata, attachment metadata, instructions, and immutable snapshots.
- `/platform/offer-decision-export-deliveries` shows read-only global diagnostics for handoffs, recipients, attachment metadata, instructions, snapshots, and safety flags.

## Readiness

Readiness exposes `offer_decision_export_manual_delivery_handoff_foundation` with flags and counts for handoffs, recipients, attachment metadata, instructions, immutable snapshots, agency UI, platform UI, manual-only handoff, automatic sending disabled, SMS sending disabled, public links disabled, real PDF delivery disabled, provider execution disabled, booking execution disabled, ticket/EMD issuance disabled, and payment/invoice/settlement disabled.

## Safety Boundaries

Phase 37.8 is review/audit metadata only. It does not send email or SMS, call SMTP/SMS/storage providers, create public links, deliver real PDFs, mutate offers or prices, auto-recommend airlines, auto-select winners, book, create or alter PNRs, ticket, issue EMDs, create invoices, charge payments, settle, scrape, call external AI, or execute providers. `/agency` and `/platform` remain canonical route roots; `/agent`, `/admin`, `/api/agent`, and `/api/admin` routes are not added.
