# Servicing and After-Sales Workflow Foundation

Phase 54.7 introduces a metadata-only after-sales workflow layer for servicing work that happens after a trip, offer, booking, ticket, EMD, document, or passenger service record already exists.

The foundation creates a unified case workspace for:

- voluntary change
- schedule change
- cancellation
- refund
- ticket exchange
- EMD exchange/refund
- claim
- service amendment
- passenger/document amendment
- disruption or irregular operation

## Metadata Model

Phase 54.7 registers these agency-owned collections:

- `after_sales_cases`
- `after_sales_case_items`
- `after_sales_decisions`
- `after_sales_financial_impacts`
- `after_sales_resolutions`
- `after_sales_communication_records`

The case model stores the case reference, type, status, priority, affected trip/booking/ticket/EMD/passenger/document/SSR-OSI/segment links, coupon-status snapshots, generated advice metadata, internal/client message metadata, document requirements, client-approval requirements, supplier-contact requirements, and integration links to workflow, work queue, SLA deadlines, task automation, and operational timelines.

## Safety Boundary

This phase does not execute servicing actions. It does not:

- mutate tickets or EMDs
- authorize or perform refunds, exchanges, voids, or financial commitments
- call airlines, GDS, NDC, suppliers, or external APIs
- send email, SMS, WhatsApp, or provider messages
- run AI
- run background workers or schedulers
- bypass agency isolation

Financial records are placeholders and estimates only. Resolution records explicitly reject metadata that attempts to mark ticket/EMD mutation or financial commitment as performed.

## Reuse Of Existing Foundations

Phase 54.7 does not replace older servicing records. It references and coordinates existing foundations:

- refund/exchange cases
- trip change operations
- ticket exchange operation metadata
- EMD exchange/refund metadata
- ticket workspaces and coupon metadata
- EMD workspaces
- document workspaces
- operational timelines
- workflow orchestration
- agent work queue
- SLA/deadline engine
- task automation/dependency orchestration

The after-sales case becomes the unified operational workspace for human review and audit, while execution remains outside this phase.

## API And UI

Platform diagnostics:

- `GET /api/platform/after-sales`
- `GET /api/platform/after-sales/summary`
- `GET /api/platform/after-sales/{case_id}`

Agency operations:

- `GET /api/agencies/{agency_id}/after-sales`
- `POST /api/agencies/{agency_id}/after-sales`
- `GET /api/agencies/{agency_id}/after-sales/{case_id}`
- `PUT /api/agencies/{agency_id}/after-sales/{case_id}`
- child metadata routes for items, decisions, financial impacts, resolutions, and communications

Frontend routes:

- `/platform/after-sales`
- `/agency/after-sales`

Both pages clearly identify the feature as metadata-only. Platform diagnostics are read-only. Agency operations can create and update metadata records only.
