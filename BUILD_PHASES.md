# Build Phases

This file describes the AeroAssist AgencyOS roadmap numbering used by the repository documentation after the Phase 8 stabilization audit. Roadmap phase completion means the local foundation for that scope exists in code and documentation; it is not a claim of production readiness.

Production readiness still requires persistence hardening, migrations, tenant isolation tests, production authentication, invitation/session flows, formal permission enforcement, operational monitoring, and deployment/security review.

## Current Implementation State

The repository currently contains:

- Phase 0: Architecture contract and canonical planning documents.
- Phase 1: Foundation / tenancy / platform-agency shell.
- Phase 2: CRM / clients / passengers / relationships.
- Phase 3: Requests / messages / tasks / timeline.
- Phase 4: Manual offer builder.
- Phase 5: Booking / ticket / EMD / invoice / payment tracking.
- Phase 6: Airline Intelligence foundation.
- Phase 7: Branded HTML document previews.
- Phase 8: Read-only client portal visibility.
- Phase 8 stabilization audit: repository registration, routing, seed, visibility, and build consistency review.
- Phase 9: Production persistence and tenant hardening foundation.
- Phase 10: Production authentication and invitation flow.
- Phase 11: Client portal controlled actions.
- Phase 12: Refund and exchange tracking.
- Phase 13: Printable document export and email delivery foundation.
- Phase 14: Document delivery hardening.
- Phase 15: Production PDF rendering and delivery infrastructure.
- Phase 16: Production delivery operations and secret resolution.
- Phase 17: Production configuration hardening.
- Phase 18: Docker and Hostinger VPS packaging.

## Phase 0: Architecture Contract And Foundations

Goal: Establish canonical specifications before code.

Implemented artifacts:

- Product specification.
- Canonical data model.
- Workflow model.
- Permission and tenancy model.
- Navigation model.
- Review notes and open questions.

Out of scope:

- Application code.
- Database migrations.
- UI pages.
- External integrations.

## Phase 1: Foundation / Tenancy / Platform-Agency Shell

Goal: Create the application foundation, tenant-aware data model base, demo auth scaffolding, platform layer, agency workspace shell, seed flow, and frontend route shell.

Implemented foundations:

- Platform user/profile model.
- Agency model.
- Agency workspace/settings model.
- Agency staff membership model.
- Global reference records.
- Audit events.
- Demo/dev auth header mode.
- Platform role and agency role scaffolding.
- Tenant access helper expectations.
- Core seed data for one demo platform owner and agency workspace.
- Frontend route shell for public, login, platform, agency, and portal layers.

Out of scope:

- Production authentication.
- Production-grade authorization matrix.
- Persistent migrations and indexes.
- CRM, requests, offers, bookings, airline intelligence, documents, or portal workflows.

## Phase 2: CRM / Clients / Passengers / Relationships

Goal: Implement the travel-specific CRM foundation and keep client and passenger concepts separate.

Implemented foundations:

- Agency-owned client profiles.
- Agency-owned passenger profiles.
- Many-to-many client/passenger relationship records.
- Relationship permission flags for view, edit, document upload, travel requests, payment, and notifications.
- Portal status fields on client profiles.
- Non-destructive passenger merge audit.
- Agency-scoped CRM CRUD APIs.
- Staff pages for clients, passengers, detail views, and relationship linking.
- Seed data for individual, organization, and family/guardian scenarios.

Out of scope:

- Production portal invitations.
- Passenger document upload/storage.
- Client self-service editing.

## Phase 3: Requests / Messages / Tasks / Timeline

Goal: Add the first operational workflow object for agency-scoped travel requests.

Implemented foundations:

- Travel requests.
- Request passenger links with passenger snapshots.
- Intended itinerary segments.
- Requested services and service status tracking.
- Request messages.
- Request tasks.
- Request timeline events.
- Request audit events.
- Staff pages for request list, creation, and detail workflows.

Out of scope:

- Client portal request submission.
- Website request intake.
- Airline policy evaluation.
- Real document uploads.

## Phase 4: Manual Offer Builder

Goal: Let staff create and manage manually researched offers without fare-search or ticketing automation.

Implemented foundations:

- Agency-scoped offers.
- Optional request-to-offer creation.
- Offer passengers with snapshots.
- Up to three route alternatives per offer.
- Up to three fare options per route alternative.
- Offer itinerary segments.
- Offer price lines.
- Manual service support checks.
- Offer send action with immutable sent snapshot.
- Offer timeline and audit events.
- Staff offer list, creation, and detail pages.

Out of scope:

- Client acceptance/rejection.
- Email sending or public links.
- Fare search, GDS, NDC, OTA, supplier, or airline integrations.
- Automated ticketing.

## Phase 5: Booking / Ticket / EMD / Invoice / Payment Tracking

Goal: Track the operational and financial lifecycle after offer work or manual booking.

Implemented foundations:

- Booking records.
- Booking creation manually or from an offer.
- Booking snapshots copied from selected offer context.
- Booking passengers and booking segments.
- Ticket records issued externally.
- EMD records issued externally.
- Invoices with line-item-derived totals.
- Manual payment records with received and reconciliation status.
- Booking timeline events.
- Staff routes for bookings, booking detail, invoices, invoice detail, and payments.

Out of scope:

- Reservation, ticket, or EMD execution.
- Payment gateway processing.
- Full accounting ledger.
- Refund/exchange tracking.

## Phase 6: Airline Intelligence Foundation

Goal: Add platform-owned, searchable, source-backed airline decision support with agency-specific overrides.

Implemented foundations:

- Platform-owned airline profiles.
- Platform-owned airline knowledge items.
- Platform-owned airline procedures.
- Platform-owned EMD/RFIC/RFISC support notes.
- Platform-owned source/citation records.
- Agency-owned airline overrides and annotations.
- Agency knowledge usage events.
- Platform maintenance UI for airlines, knowledge, procedures, EMD notes, and sources.
- Agency search/detail UI for published airline intelligence.
- Lightweight search links from request, offer, and booking detail pages.
- Seeded fake/demo airline intelligence data.

Out of scope:

- Automated rule engine.
- Pricing automation.
- Airline scraping.
- Broad version/import workflow.
- Client-facing airline intelligence.

## Phase 7: Branded HTML Document Previews

Goal: Add snapshot-based branded HTML document rendering for agency staff.

Implemented foundations:

- Agency/platform document template records.
- Agency-owned rendered document records.
- Document timeline events.
- Snapshot-based branded HTML rendering service.
- Agency workspace brand snapshots on rendered documents.
- Source snapshots on rendered documents.
- Staff document list/detail/template pages.
- Sandboxed HTML document preview.
- Render actions from offer, booking, ticket, EMD, and invoice detail workflows.
- Seeded default templates and rendered demo documents.

Out of scope:

- PDF export.
- Email delivery.
- Public/share links.
- File storage.
- Legal/fiscal invoice compliance output.
- Advanced template editor.

## Phase 8: Read-Only Client Portal Visibility

Goal: Add an agency-branded, read-only portal visibility layer over already-created agency records.

Implemented foundations:

- Demo portal access mapping records from portal email to agency client.
- Read-only client portal API under `/api/portal`.
- Portal-safe client, passenger, request, offer, booking, document, invoice, and payment responses.
- Client/passenger visibility enforcement through active `can_view` relationships.
- Client-scoped request, offer, booking, document, invoice, and payment visibility.
- Client-visible-only messages, tasks, timeline events, price lines, invoice lines, and rendered documents.
- Branded portal layout using agency workspace brand settings.
- Portal dashboard, profile, passengers, requests, offers, bookings, documents, invoices, and payments pages.
- Seeded demo portal accounts for individual and organization sample clients.

Out of scope:

- Production portal authentication.
- Portal invitations or sessions.
- Request submission.
- Offer acceptance/rejection.
- Document acknowledgement or upload.
- Online payment checkout.
- Client-facing airline intelligence.

## Phase 8 Stabilization Audit

Goal: Verify repository coherence after Phases 1 through 8 without adding product features.

Completed checks:

- Backend router registration and import consistency.
- Platform summary/health metadata consistency.
- Frontend route and navigation consistency.
- API helper usage.
- Seed data ordering and idempotency.
- Status/badge sanity checks.
- Document rendering smoke checks.
- Portal security/visibility smoke checks.
- Build, compile, and diff whitespace checks.

Recorded in:

- `PHASE_8_STABILIZATION_AUDIT.md`

## Phase 13: Printable Document Export And Email Delivery Foundation

Implemented foundations:

- Document export records for existing rendered document snapshots.
- Printable HTML export generation and authenticated downloads.
- Friendly PDF-unavailable behavior when no reliable PDF renderer is installed.
- Manual document delivery records.
- Agency email settings with disabled, dev-console, and SMTP placeholder modes.
- Dev-console send behavior for local/demo delivery audit.
- Portal read-only export listing and download for client-visible documents/exports.
- Staff document detail UI for exports, deliveries, and email settings.

Out of scope:

- Real PDF rendering dependency selection.
- Public links.
- Bulk or marketing email.
- Automatic delivery on document render.
- Raw SMTP password storage.

## Phase 14: Document Delivery Hardening

Implemented foundations:

- File-backed local storage abstraction for new generated document exports.
- Export storage keys, storage bucket labels, checksums, and file size metadata.
- Cleanup-ready retention policy and retention expiry metadata.
- Archived export timestamps and actor tracking.
- Delivery attempt records for staff-controlled send/retry actions.
- Delivery attempt counters, retry state, and max-attempt tracking.
- Email settings validation endpoint.
- SMTP secret-reference requirement without storing raw credentials.
- Staff UI for export storage, retention, checksum, delivery attempts, retry state, and email validation.
- Portal read-only downloads preserved without public links or client-triggered sending.

Out of scope:

- Real PDF rendering, because no verified renderer dependency is installed in this environment.
- Public share links.
- Automatic or bulk email sending.
- Background worker infrastructure.
- Raw SMTP password storage.
- Payment links, electronic signatures, document upload, and fiscal invoice compliance.

## Phase 15: Production PDF Rendering And Delivery Infrastructure

Implemented foundations:

- ReportLab-based simplified PDF renderer for stored rendered HTML snapshots.
- Staff export capability endpoint with renderer diagnostics.
- PDF exports saved through the Phase 14 file storage abstraction.
- PDF export metadata with `application/pdf`, file size, checksum, retention policy, and safe storage keys.
- Portal read-only PDF and printable HTML downloads for generated client-visible exports.
- Delivery attachment validation before staff-triggered send/retry.
- Staff UI export capability status and PDF generation control.
- Seeded PDF export only when the ReportLab renderer is available.

Out of scope:

- Pixel-perfect browser HTML-to-PDF rendering.
- Legal/fiscal invoice compliance claims.
- Public share links.
- Automatic or client-triggered sending.
- Background workers and provider webhooks.
- Raw SMTP password storage or production secret resolver integration.

## Phase 16: Production Delivery Operations And Secret Resolution

Implemented foundations:

- Environment-only SMTP secret resolution for references in the form `env:VARIABLE_NAME`.
- Staff-controlled SMTP sending when agency email settings validate and the referenced password environment variable resolves.
- No SMTP secret values are returned by API responses, logs, diagnostics, or readiness checks.
- Staff delivery diagnostics endpoint with attachment validity, email mode, secret-resolution status, retry state, attempt counts, last safe error, and next allowed action.
- Retry governance that requires `retry_available`, respects `max_attempts`, and remains manual.
- Production readiness script for deployment checks around demo auth, MongoDB, export storage, ReportLab, CORS, and SMTP secret refs.
- Staff UI display for masked SMTP secret refs, secret resolution status, diagnostics, and next allowed delivery action.

Out of scope:

- Public share links.
- Automatic sending, background workers, cron, provider webhooks, or bounce handling.
- Client-triggered delivery.
- Mass/marketing email.
- Raw SMTP password storage.
- Payment links, uploads, signatures, airline/GDS/NDC integrations, refund/payment/ticketing execution, or fiscal invoice compliance.

## Next Recommended Phases

These are roadmap phases, not production-readiness claims. They should remain separate so each security, data, and external-side-effect boundary can be reviewed independently.

### Phase 17: Production Configuration Hardening

Goal: Prepare the app for safe VPS deployment by centralizing environment handling and exposing runtime readiness without adding business workflow features.

Implemented foundations:

- Central backend config service for app env, demo auth, seed gates, MongoDB, CORS, storage, logging, public URLs, token settings, and SMTP secret refs.
- Strict production startup checks for unsafe database mode, demo auth, seed behavior, wildcard/local CORS, placeholder auth secrets, and export storage writability.
- Lightweight `/api/health` and safe `/api/readiness` summaries for app env, config, database, storage, PDF capability, and SMTP secret reference diagnostics.
- Production-disabled startup seed and seed endpoint defaults.
- Frontend API base URL handling that avoids localhost fallback in production builds.
- Production readiness script aligned with runtime config checks.
- Production env example and Hostinger/VPS deployment checklist documentation.

Out of scope:

- Docker packaging.
- VPS deployment scripts.
- nginx/TLS/domain setup.
- Backups.
- Monitoring stack.
- Public links.
- Automatic sending, provider webhooks, background workers, or object-storage lifecycle automation.

### Phase 18: Docker And Hostinger VPS Packaging

Goal: Package the already-built app for Hostinger managed VPS deployment using Docker Compose without adding product workflows.

Implemented foundations:

- Backend Dockerfile for FastAPI/Uvicorn and Python dependencies.
- Frontend Dockerfile for Vite build and nginx static serving.
- nginx `/api` proxy from frontend container to backend container.
- Production Docker Compose file with frontend, backend, and MongoDB services.
- Compose health checks for MongoDB, backend health, and frontend serving.
- Named volumes for MongoDB data and document export storage.
- Production env template alignment for Compose defaults.
- Hostinger VPS deployment runbook.

Out of scope:

- TLS certificate automation.
- Domain/DNS management.
- Backup automation.
- Monitoring stack.
- CI/CD pipeline.
- Kubernetes.
- Object storage.
- Public links.
- Worker queues, provider webhooks, or automatic sending.

### Phase 19: VPS Reverse Proxy, TLS, Backup, And Operations Runbook

Recommended scope:

- Host-level reverse proxy/TLS guidance.
- Domain and DNS checklist.
- Backup and restore procedures for MongoDB and document exports.
- Operational log review and incident checklist.
- Manual update and rollback runbooks.
- Basic VPS firewall hardening notes.

Avoid adding:

- Monitoring stack automation unless explicitly scoped.
- Provider webhooks, queue workers, public links, payment links, or object storage.

### Phase 20: Delivery Provider Operations And Object Storage Lifecycle

Recommended scope:

- Add email provider integration strategy beyond direct SMTP if needed.
- Add delivery queue worker design with explicit admin controls.
- Add provider webhook/bounce handling.
- Add external file storage/retention lifecycle if local disk is insufficient.
- Add visual PDF QA checks if browser-grade rendering is adopted later.
- Public/share link decision record if links are added later.
- Document visibility and expiry controls.

Avoid adding:

- Payment gateway links unless explicitly included in a later payment phase.

### Phase 21: Airline Intelligence Versioning/Import Workflow

Recommended scope:

- Immutable published knowledge versions.
- Import/review workflow for pasted or uploaded source material.
- Source provenance and reviewer gates.
- Agency override conflict review.
- Usage snapshots that reference specific knowledge versions.

Avoid adding:

- Automatic scraping without human review.
- Automated policy scoring or pricing decisions.

### Phase 22: Agency Website/CMS Publishing Foundation

Recommended scope:

- Controlled agency website settings.
- Basic hosted public pages.
- Template-driven content sections.
- Portal entry links and request-intake entry points.
- Brand/contact/legal page configuration.

Avoid adding:

- Complex drag/drop site building.
- Blog automation.
- Custom design tooling.

## Roadmap Guardrails

- Keep clients and passengers separate.
- Keep staff workflows manual unless a later phase explicitly adds automation.
- Keep Airline Intelligence as decision support until versioning, source review, and production authorization are hardened.
- Keep tickets, EMDs, payments, and documents as tracking/output layers until external integrations are intentionally designed.
- Keep portal visibility and portal actions aligned with scope boundaries: read-only visibility is complete for Phase 8, and controlled portal actions are implemented in Phase 11.
- Keep roadmap numbering distinct from production readiness.

## Scope Risks To Continue Watching

- Public website/CMS, client portal, CRM, requests, airline intelligence, offers, bookings, financial tracking, and documents are each substantial product areas.
- Airline intelligence requires operational content governance in addition to software features.
- Offer builder can drift into fare search if boundaries are not enforced.
- Document generation can drift into a full template-builder product.
- Payments can drift into accounting or payment processing if tracking boundaries are not explicit.
- Refunds and exchanges are operationally complex and should not be mixed into unrelated hardening work.
