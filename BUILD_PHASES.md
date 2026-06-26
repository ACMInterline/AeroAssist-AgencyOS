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
- Phase 19: VPS reverse proxy, TLS, backup, and operations runbook.
- Phase 20: Hostinger VPS first deployment preparation.
- Phase 21: Production bootstrap and go-live hardening.
- Phase 22: Production onboarding and agency setup.
- Phase 23: Backup automation and lightweight monitoring readiness.
- Phase 24: Staff invitation acceptance and team access hardening.
- Phase 25: Document storage lifecycle and delivery provider readiness.
- Phase 26: Request intake to operational request stabilization.
- Phase 27: Operational request builder V1.
- Phase 27.1: Mobility assistance logic and request builder UX correction.
- Phase 27.2: Assistance assessment driven SSR recommendation.
- Phase 28: Agency branding, theme, and UI personalization settings.
- Phase 28.1: AgencyOS app shell, sidebar navigation, and visual polish stabilization.
- Phase 29: Agency website builder / CMS foundation.
- Phase 30: Public website publishing, intake forms, and CMS content blocks.
- Phase 30.1: Branding, logo asset management, and agency settings stabilization.
- Phase 31: CMS media library, website image assets, and public website visual polish.
- Phase 32: Blueprint alignment and canonical operations model.
- Phase 33: Reference data core and service catalogue.
- Phase 33.1: Global reference data governance, bulk import, and agency suggestion queue.
- Phase 34: Segment-scoped request services, pets, and special items.
- Phase 34.1: Global field library and agency form profiles.
- Phase 34.2: Platform reference data console and enriched countries.
- Phase 34.3: Reference data enrichment import packs and aviation normalization.
- Phase 35: Trip dossier foundation and request-to-trip operational shell.

Phase 35 navigation hotfix:

- Platform Owner navigation no longer includes a global Agency Workspace shortcut; agency workspace entry is contextual from platform agency management/detail pages.
- `/platform/agencies` and `/platform/airlines` render defensive management/foundation pages instead of blank routes.
- Agency reference data governance remains consume-and-suggest only.

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

Goal: Add safe server-side operational assets around the Docker Compose deployment without adding product functionality.

Implemented foundations:

- Host-level nginx reverse proxy template with TLS/certbot placeholders.
- Documentation for direct-container and host-nginx deployment modes.
- Safe deploy, restart, status, and log helper scripts.
- Timestamped MongoDB backup script using `mongodump`.
- Timestamped document export backup script using the backend mounted export volume.
- Manual restore guidance with explicit checksum verification and maintenance-window steps.
- Production smoke script for frontend, health, readiness, and login availability.
- Operations runbook covering update, rollback, incident checks, and known limitations.

Out of scope:

- Live DNS setup.
- Real certificate issuance or committed certificate files.
- Paid monitoring stack services.
- CI/CD deployment automation.
- Kubernetes.
- Object storage.
- Migrations framework.
- Background workers, provider webhooks, automatic sending, public links, uploads, or payment links.

### Phase 20: Hostinger VPS First Deployment Preparation

Goal: Make the first Hostinger VPS deployment executable without guessing by adding final pre-deployment checklists, preflight validation, troubleshooting, and post-deployment verification.

Implemented foundations:

- First deployment checklist with exact command sequence.
- `.env.production` creation and validation checklist.
- VPS directory layout and prerequisite checklist.
- Non-mutating preflight script that validates repo layout, env values, Docker/Compose availability, Compose config, and backup root writability.
- Deploy helper preflight integration before git update, build, or service start.
- Post-deployment security checklist.
- Troubleshooting guide for Docker, ports, frontend/backend proxy, CORS, Mongo, storage, PDF, SMTP refs, nginx, certbot, and document export downloads.
- First backup, rollback, deployed-commit recording, and post-deployment verification steps.

Out of scope:

- Actual server deployment.
- Real domains, secrets, or certificate issuance.
- Backup scheduler.
- Monitoring services.
- CI/CD.
- DNS automation.
- Background workers, provider webhooks, automatic sending, public links, uploads, or payment links.

### Phase 21: Production Bootstrap And Go-Live Hardening

Goal: Harden the successful Hostinger deployment with an official first-owner bootstrap path, production demo UI cleanup, real deployment notes, reboot verification, and temporary-to-final routing guidance.

Implemented foundations:

- Official `create_first_platform_owner.py` backend script for controlled production owner bootstrap.
- Interactive password handling without password echo or logging.
- Duplicate and existing-identity safety checks for bootstrap.
- Production frontend hides demo login labels, demo account cards, and demo credential defaults.
- Hostinger scripts default to `/opt/aeroassist-agencyos` while preserving `APP_DIR` overrides.
- Real deployment notes for temporary `:8080` state, deployed commit, old app coexistence, backups, persistence test, and pending reboot.
- Safe VPS reboot verification runbook.
- nginx/TLS migration plan from temporary IP port exposure to final HTTPS domain.

Out of scope:

- Creating real users in repository code.
- Touching the old `/opt/aeroassist` app.
- Running the VPS reboot from repo changes.
- Final domain/TLS cutover.
- Backup scheduler.
- Monitoring services.
- CI/CD.
- Background workers, provider webhooks, automatic sending, public links, uploads, or payment links.

### Phase 22: Production Onboarding And Agency Setup

Goal: Let the live production platform owner create and manage the first real agency/workspace from the UI without demo seed data or manual database scripts.

Implemented foundations:

- Platform agency list and create flow.
- Platform agency detail page for editing agency basics.
- Explicit first-workspace creation flow from agency detail.
- Workspace list/create API under `/api/agencies/{agency_id}/workspaces`.
- Agency list/detail workspace and staff counts.
- Safe platform-owner agency membership creation when the first workspace is created.
- Staff invitation preparation without automatic email sending or production token exposure.
- Production onboarding informational flags in platform summary.
- Production notes for `https://avio.my`, stopped/preserved old app, and no demo seed.

Out of scope:

- Demo seed or fake customer/operational data.
- Automatic staff invitation sending.
- Payment gateway integration.
- GDS/NDC/airline integrations.
- CMS/website publishing.
- Public sharing.
- Document upload.
- CI/CD or monitoring stack.

### Phase 23: Backup Automation And Lightweight Monitoring Readiness

Implemented scope:

- Combined MongoDB and document export backup script.
- Backup checksum verification and age checks with MongoDB freshness failure.
- Conservative dry-run-first backup pruning with explicit `--apply`.
- Root-owned systemd service/timer templates for daily backup and verification.
- Lightweight host healthcheck for Docker, nginx, certbot, Compose health, canonical domain routing, API health/readiness, local-only frontend binding, nginx-owned public ports, and old app stopped/preserved status.
- Full operational status script with git commit, app phase, containers, nginx, certbot timer, disk usage, latest backups, domain redirect summary, and old app state.
- Phase 23 production operations documentation.

Avoid adding:

- Provider webhooks, queue workers, public links, payment links, object storage, or CI/CD unless explicitly scoped.
- External monitoring SaaS, alerting service, automated restore, or old app deletion.

### Phase 24: Staff Invitation Acceptance And Team Access Hardening

Implemented scope:

- Staff invitation records with workspace scope, invited name, accepted/revoked metadata, and token-hash-only storage.
- One-time raw invitation token and acceptance URL returned only from create response.
- Staff invitation list and revoke endpoints without token exposure.
- Public token validation endpoint with minimal invitation metadata.
- Invitation-only staff account activation and membership creation.
- Role restrictions preventing platform owner or agency owner invitation through this flow.
- Audit events for invitation creation, revocation, acceptance, and membership creation without token material.
- Platform agency UI for invitation creation, one-time link copying, invitation listing, and revocation.
- Public `/invite/accept` page for invitation validation and password setup.
- Staff invitation smoke script.

Avoid adding:

- Public registration, automatic email sending, external email/SaaS dependencies, mass team management, membership removal, or platform owner invitation flow.

### Phase 25: Document Storage Lifecycle And Delivery Provider Readiness

Implemented scope:

- Storage lifecycle metadata records for generated document exports.
- Local filesystem storage backend health, summaries, and path-safe metadata listing.
- Storage archive and mark-missing actions without file deletion.
- Delivery provider readiness contract with manual provider enabled and all automatic/external providers disabled by default.
- Agency UI for storage health, lifecycle counts, provider readiness, and storage record actions.
- Hostinger storage check script for the backend document export volume.
- Smoke script for storage/provider readiness safety checks.

Avoid adding:

- Automatic email sending, external object storage, public document links, external SaaS dependencies, provider webhooks, hard-delete API, or background workers.

### Phase 26: Request Intake Operational Request Stabilization

Implemented scope:

- Public and portal submissions are stored as request intakes before operational conversion.
- Additive request intake model with contact, travel, service, triage, raw/canonical payload, and conversion metadata.
- Public-safe intake endpoint with safe confirmation response and no privileged field acceptance.
- Staff intake queue/detail, triage, reject/archive/duplicate, and explicit convert actions.
- Conversion service creates canonical operational requests with source intake linkage and duplicate conversion guard.
- Platform/readiness summaries expose intake and open operational request counts.
- Smoke script for request intake conversion safety and idempotency.

Avoid adding:

- Airline integrations, pricing automation, payment gateways, automatic email sending, public document links, customer portal account creation, external SaaS dependencies, demo auth, or seed endpoint re-enablement.

### Phase 27: Operational Request Builder V1

Implemented scope:

- Structured internal request builder endpoint for client, passengers, itinerary, segments, services, and notes.
- Inline client creation and inline passenger creation from the request builder.
- Structured segment fields for trip type, route, dates, airline/flight placeholders, cabin/class, and notes.
- AeroAssist service categories with conditional detail payload storage.
- Requested service relationships to passengers and segments with all-scope defaults.
- Intake conversion aligned to the structured request model with passenger placeholders and service detail payloads.
- Agency request builder UI replacing the old generic ticket-style form.
- Smoke script for builder creation and intake conversion compatibility.

Avoid adding:

- GDS/NDC/airline integrations, automatic pricing, booking/PNR creation, payment gateways, automatic email, public document links, or external provider calls.

### Phase 27.1: Mobility Assistance Logic And Builder UX Correction

Implemented scope:

- Replaced incorrect mobility fields with `assistance_code` for WCHR/WCHS/WCHC/MAAS/unknown.
- Separated transfer and boarding clarifiers from the assistance code.
- Added conditional own mobility device details.
- Added battery fields only for electric wheelchair/powerchair and mobility scooter cases.
- Improved request builder service-card layout for mobility assistance.
- Updated request detail summaries and intake conversion defaults for mobility payloads.

Avoid adding:

- Airline-specific validation, pricing, airline integration, public links, external dependencies, or automated delivery.

### Phase 27.2: Assistance Assessment Driven SSR Recommendation

Implemented scope:

- Replaced code-first mobility assistance selection with assessment-first questions.
- Added passenger context tags and functional mobility assessment fields.
- Added frontend SSR/service recommendation for WCHR, WCHS, WCHC, MAAS, MEDA, BLND, DEAF, and manual review.
- Added staff confirmation and override reason requirement.
- Preserved own mobility device and conditional battery details as supplemental data.
- Updated intake conversion to create manual-review assessment payloads for mobility intakes without detail.

Avoid adding:

- Airline-specific validation, reference-data taxonomy, automated SSR transmission, pricing, airline integration, public links, or automated delivery.

### Phase 28: Agency Branding, Theme, And UI Personalization Settings

Implemented scope:

- Agency-scoped `agency_branding_settings` with optional workspace override, controlled design preset keys, audit metadata, and update actor metadata.
- Read/write branding APIs plus safe PNG/JPEG/WEBP logo upload and removal endpoints.
- Controlled typography choices, including Quicksand, without remote font loading.
- Ten controlled color palettes with light/dark values plus light/dark/system theme modes.
- Radius, density, field, button, date input, and card style presets without arbitrary CSS input.
- Agency settings UI at `/agency/settings` with brand identity, typography, theme, controls, logo, reset, and live preview.
- Shared agency theme layer that applies CSS variables to header, navigation, inputs, buttons, cards, badges, and native date inputs.
- Optional readiness/platform summaries and a branding smoke script.

Avoid adding:

- Arbitrary CSS/HTML injection, remote font loading, public logo filesystem paths, SVG logo execution, public document links, or marketing CMS publishing.

### Phase 28.1: AgencyOS App Shell, Sidebar Navigation, And Visual Polish Stabilization

Implemented scope:

- Persistent desktop sidebar for agency admins and agents.
- Responsive mobile drawer navigation and desktop sidebar collapse.
- Active-route highlighting and disabled coming-soon affordances; Website/CMS is enabled in Phase 29.
- Top bar with workspace context, primary create-request action, manual operations badge, and account/logout area.
- Theme-aware app background, cards, buttons, fields, status surfaces, focus states, and responsive table overflow.
- Dashboard, request list, request detail, intake queue, and request builder layout polish.

Avoid adding:

- CMS publishing, pricing automation, airline integrations, external UI libraries, arbitrary CSS injection, or automated delivery.

### Phase 29: Agency Website Builder / CMS Foundation

Implemented scope:

- Agency-owned website settings for site name, slug, tagline, status, SEO text, contact details, and request CTA visibility.
- Controlled website pages with draft, published, and archived lifecycle states.
- Controlled section blocks for hero, text, services, CTA, contact, and intake link content.
- Agency CMS UI at `/agency/website` with settings, page creation, section editing, publish/archive, and live preview.
- Public JSON endpoint and public frontend renderer at `/site/{slug}` for active websites only.
- Sidebar Website/CMS navigation enabled.
- Readiness/platform website counts.

Avoid adding:

- Custom CSS/JS/HTML embeds, domain routing changes, pricing automation, airline integrations, external UI libraries, or automatic delivery.

### Phase 30: Public Website Publishing, Intake Forms, And CMS Content Blocks

Implemented scope:

- Richer controlled CMS section blocks for hero, service cards, feature grids, process steps, FAQ, contact CTAs, request-form CTAs, testimonials, trust badges, image/text, contact details, and legal text.
- Type-aware section editing, delete, and move up/down controls in the agency website builder.
- Explicit publish/unpublish site endpoints.
- Published inner page rendering at `/site/{slug}/{pageSlug}`.
- Public website request form at `/site/{slug}/request` that creates `request_intakes` with website source metadata.
- Intake queue/detail source display for website CMS requests.
- Audit events for section updates, reorders, site publishing, site unpublishing, page publishing, and public website intake submission.

Avoid adding:

- Custom domain automation, raw HTML/CSS/JS, iframe embeds, advanced media library/public media delivery, pricing automation, airline integrations, or automatic email.

### Phase 30.1: Branding, Logo Asset Management, And Agency Settings Stabilization

Implemented scope:

- Dedicated logo asset records with original, square, compact, horizontal, and favicon variants.
- Server-side logo validation and preparation with PNG/JPEG/WEBP only, 2MB limit, decoded-image verification, SVG rejection, metadata stripping, and PNG derivative generation.
- Controlled logo fit, preferred usage, and public-usage settings in `/agency/settings`.
- Public website branding uses only public-safe generated derivatives.
- Agency shell uses compact/sidebar logo variants with stable object-fit rendering.
- Readiness/platform summaries expose branding/logo capability flags and configured counts.

Avoid adding:

- External image services, arbitrary CSS/JS, SVG execution, advanced media library, custom domain automation, background removal, pricing automation, airline integrations, or automatic delivery.

### Phase 31: CMS Media Library, Website Image Assets, And Public Website Visual Polish

Implemented scope:

- Agency-scoped CMS media library separate from logo assets.
- Safe PNG/JPEG/WEBP upload with 5MB limit, magic-byte checks, decoded-image verification, EXIF stripping, and generated thumbnail/card/hero/original-safe variants.
- Controlled media management UI at `/agency/website/media`.
- Section image picker for image-capable website sections.
- Public website responses include only referenced active public-safe media assets.
- Public website renderer and request form visual polish.

Avoid adding:

- Arbitrary HTML/CSS/JS, external CMS/media SaaS, external image editing APIs, custom domain automation, payments, pricing, airline integrations, or automatic delivery.

### Phase 32: Blueprint Alignment And Canonical Operations Model

Implemented scope:

- Formal blueprint alignment and gap map for the Travel Agency Micro-ERP + CRM blueprint.
- Canonical operations model documenting clients, passengers, requests, trips, offers, bookings, tickets, EMDs, invoices, documents, tasks, communications, activities, reference data, and airline policy rules.
- Current model inventory mapping FastAPI/Pydantic classes and Mongo-compatible collection names to blueprint entities.
- Additive trip dossier and segment-scoped request foundation models without destructive collection renames.
- Readiness/platform flags documenting blueprint alignment readiness.

Avoid adding:

- PocketBase migration, destructive data migrations, GDS integrations, pricing, payment gateways, expanded portal workflows, or full trip/offer UI.

### Phase 33: Reference Data Core And Service Catalogue

Implemented scope:

- Controlled reference data domains for countries, cities, airports, airlines, currencies, timezones, languages, operational classifications, assistance classifications, pets, and special-item categories.
- `service_catalogue` records with service code, family, default SSR, beneficiary type, segment scoping, policy/document/manual-pricing flags, input schemas, active status, sort order, and metadata.
- Manual idempotent bootstrap workflow through `backend/scripts/bootstrap_reference_data.py` and platform-owned `/api/reference/bootstrap`.
- Authenticated reference APIs for domain discovery, listing, search, create/update, activation/deactivation, and service catalogue family/search views.
- Agency UI at `/agency/reference` for Reference Data and grouped service catalogue visibility.

Avoid adding:

- Automated pricing, airline policy scoring, GDS execution, external lookup providers, or automatic startup seeding.

### Phase 33.1: Global Reference Data Governance, Bulk Import, And Agency Suggestion Queue

Implemented scope:

- Platform-owned global Reference Data governance with agency suggestions separated from approved master records.
- `reference_data_suggestions` review queue with pending, needs-more-information, approved, rejected, merged, and archived states.
- `reference_import_batches` for manual CSV validation/import with file hashes, error reports, inserted/updated/skipped counts, and audit events.
- Owner endpoints for global record management, suggestion review, and import batch listing/detail.
- Agency reference UI tabs for global records, service catalogue, own suggestions, owner-only imports, and owner-only review queue.
- Future policy-governance documentation reserving local overrides, evidence, and promotion from agency policy suggestions to global rules.

Avoid adding:

- Airline policy engine execution, automated pricing, external data provider ingestion, scraping, GDS/NDC integration, or destructive seed/reset workflows.

### Phase 34: Segment-Scoped Request Services, Pets, And Special Items

Implemented scope:

- Request normalization service that creates passenger + segment scoped services, pet segment transport, special item segment transport, and derived case flags.
- Operational request builder UX for exact passenger and segment service assignment, plus structured pet and special item capture.
- Request detail view sections for canonical child records and source payload snapshots.
- Public intake conversion compatibility with pending-information placeholder normalization where simplified forms lack exact SSR details.
- Readiness and smoke coverage for normalized request child counts, idempotency, and invalid scoping validation.

Avoid adding:

- Airline booking execution, automated pricing, or policy automation.

### Phase 34.1: Global Field Library And Agency Form Profiles

Implemented scope:

- Platform-owned `global_field_definitions` for canonical field paths, families, types, safety flags, required levels, and agency override permissions.
- Agency-owned `agency_form_profiles` and `agency_form_field_settings` for public, portal, admin, offer-client, and offer-PDF field menus.
- Effective profile service that enforces system-required locks, internal/public safety, label override permissions, and required override permissions.
- Agency custom questions stored under the canonical `agency_custom_fields` payload namespace.
- `/agency/settings/forms` UI for profile lists, grouped field settings, safety badges, and custom questions.
- Foundational public website request form and admin request builder profile lookup with safe fallback to existing behavior.

Avoid adding:

- Full drag/drop builder, pricing formula editor, airline policy form generator, portal expansion, offer builder, GDS/NDC integrations, invoices, or payments.

### Phase 34.2: Platform Reference Data Console And Enriched Countries

Implemented scope:

- Platform-only Reference Data Management Console at `/platform/reference`.
- `reference_domain_metadata` for domain label, description, category, active status, sort order, and future schema metadata.
- Enriched country metadata on legacy-compatible `global_reference_records.metadata_json` including ISO, geography, aviation, currency, population, quality, source, and reviewer fields.
- Owner-only platform APIs under `/api/platform/reference/*` for domains, records, suggestion review, dry-run/committed import, CSV/JSON export, and important record cards.
- Agency reference UI remains consume-and-suggest only.
- Readiness counters for country record quality gaps and console/import/export/review flags.
- Platform reference global record save/update now shows visible saving/success/error status, reloads the selected domain after save, and prevents stale cross-domain rows from being edited or displayed.

Avoid adding:

- External reference data providers, scraping, automated enrichment, airline execution, pricing, payment gateways, destructive import/reset workflows, or agency edits to global master records.

### Phase 34.3: Reference Data Enrichment Import Packs And Aviation Normalization

Implemented scope:

- Starter CSV templates under `data/reference_packs/` for enriched countries, airports, airlines, currencies, languages, and continents/regions.
- `reference_enrichment_service` for dry-run validation, commit imports, update modes, row-level reports, and missing cross-link warnings.
- Platform-only enrichment APIs and `/platform/reference` Enrichment Packs tab.
- Normalization for ISO country codes, airport IATA/ICAO, airline IATA/ICAO, currency ISO, language ISO, lat/lng, booleans, and max-3 arrays.
- Readiness quality counts for enriched airports, airlines, currencies, languages, country airport/carrier coverage, and missing country links.

Avoid adding:

- External scraping/API enrichment, full global datasets, airline policy engines, pricing engines, offer builders, GDS/NDC imports, invoices, payments, portal expansion, or destructive seed/reset behavior.

### Phase 35: Trip Dossier Foundation

Implemented scope:

- Additive `trip_dossiers`, `trip_passengers`, `trip_segments`, `trip_service_items`, and `trip_timeline_events` foundations.
- Manual trip dossier creation and request-to-trip conversion that never reuses `request_id` as `trip_id`.
- Request linking/unlinking with `TravelRequest.trip_id` as an additive primary back-reference and `TripDossier.linked_request_ids` for dossier scope.
- Idempotent copying of normalized request passengers, segments, and service scopes into trip-level child records with source IDs preserved.
- Trip summary rebuild, archive, audit/timeline events, and readiness counters.
- Agency trip APIs under `/api/agencies/{agency_id}/trips`.
- Agency UI routes `/agency/trips`, `/agency/trips/new`, and `/agency/trips/{trip_id}` plus request detail/list linked-trip integration.

Avoid adding:

- Offer builder expansion, GDS/NDC import, booking/ticket/EMD import, pricing, airline policy automation, invoices/payments, portal trip views, or automatic fulfillment.

### Phase 36: Offer Builder And Comparison Matrix

Recommended scope:

- Modern offer comparison matrix aligned to request segments, services, passengers, and trip attachment rules.
- Offer acceptance/commercialization workflow that attaches to trip early.

Avoid adding:

- Live fare search, supplier booking, or payment capture.

### Phase 37: Booking/Ticket/EMD Mirror Records

Recommended scope:

- Mirror records for booking, ticket, and EMD state with raw source payload preservation.
- Manual import/reconciliation workflow and provenance metadata.

Avoid adding:

- Direct GDS commands, NDC execution, or automated ticketing.

### Phase 38: Invoices And Payments

Recommended scope:

- Invoice/payment workflow hardening around existing finance tracking models.
- Payment status, reconciliation metadata, and client-visible summaries.

Avoid adding:

- Payment gateway processing unless explicitly authorized.

### Phase 39: Document Template Builder And Generation

Recommended scope:

- Broader document template builder, generation flows, and request/trip/document snapshot alignment.

Avoid adding:

- Public document links or automatic delivery beyond existing controlled foundations.

### Phase 40: Communications, Tasks, And Activity Timeline

Recommended scope:

- Unified communications/tasks/activity across request, trip, document, booking, and client contexts.
- Visibility and audit rules for internal/client-visible communication.

Avoid adding:

- Automatic external sending unless delivery governance is ready.

### Phase 41: Client Portal Foundation

Recommended scope:

- Broader authenticated portal foundation aligned to canonical request/trip/document visibility.
- Portal intake UX sharing canonical intake model.

Avoid adding:

- Client-side operational execution or automatic supplier actions.

### Phase 42: Reporting And Automation Suggestions

Recommended scope:

- Operational reports, dashboard KPIs, and staff-confirmed automation suggestions.

Avoid adding:

- Unreviewed automated decisions, pricing, or airline execution.

### Phase 43: Airline Policy Knowledge Base

Recommended scope:

- Versioned airline policy rule knowledge base, import/review workflow, source provenance, and usage snapshots.

Avoid adding:

- Automatic scraping or policy enforcement without human review.

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
