# Operational Timeline Workspace Foundation

Phase 42.1 adds the metadata-only operational history layer for AeroAssist.

The `operational_timelines` collection stores timeline and communication-summary entries linked to the operational workspaces created in Chapter 41 and Chapter 42. It is a record of what staff know happened or needs attention; it does not send messages, summarize with AI, call providers, or run background work.

## Scope

Timeline entries can link to:

- passenger workspaces
- travel request workspaces
- trip workspaces
- booking workspaces
- ticket workspaces
- EMD workspaces
- SSR / OSI operational workspaces
- document workspaces

Each entry stores agency ownership, a timeline reference, event metadata, operational stage/result, airline/airport context, communication summary metadata, approval metadata, due/completed dates, visibility metadata, attachments, and operational notes.

## APIs

Platform routes:

- `GET /api/platform/operational-timelines`
- `GET /api/platform/operational-timelines/summary`
- `POST /api/platform/operational-timelines`
- `GET /api/platform/operational-timelines/{timeline_id}`
- `PUT /api/platform/operational-timelines/{timeline_id}`
- `DELETE /api/platform/operational-timelines/{timeline_id}`

Agency routes are read-only:

- `GET /api/agencies/{agency_id}/operational-timelines`
- `GET /api/agencies/{agency_id}/operational-timelines/summary`
- `GET /api/agencies/{agency_id}/operational-timelines/{timeline_id}`

Filters cover passenger, booking, ticket, EMD, SSR / OSI, airline, communication type, event type, priority, status, and date. Results are returned in chronological `created_at` order.

## UI

Platform Console:

- `/platform/operational-timelines`

Agency Workspace:

- `/agency/timeline`

Both pages show read-only chronological cards with linked workspaces, communication summaries, approval history, operational notes, attachments, and visibility metadata.

## Safety Boundary

Phase 42.1 is metadata-only. It does not implement email sending, SMS sending, WhatsApp, Teams, Slack, live airline messaging, live customer messaging, AI summarization, background workers, provider integrations, external API calls, or automation.
