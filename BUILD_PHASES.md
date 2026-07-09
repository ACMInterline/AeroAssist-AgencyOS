# Build Phases

This file describes the AeroAssist AgencyOS roadmap numbering used by the repository documentation after the Phase 8 stabilization audit. Roadmap phase completion means the local foundation for that scope exists in code and documentation; it is not a claim of production readiness.

Production readiness still requires persistence hardening, migrations, tenant isolation tests, production authentication, invitation/session flows, formal permission enforcement, operational monitoring, and deployment/security review.

## Foundational Architecture Documents

Permanent AeroAssist architecture foundations live under `docs/architecture/foundations/`:

- `PASSENGER_SERVICE_OPERATIONS_MANIFESTO.md`
- `AIRLINE_OPERATIONAL_KNOWLEDGE_BLUEPRINT.md`
- `AEROASSIST_ENGINEERING_PRINCIPLES.md`
- `PASSENGER_SERVICE_ONTOLOGY.md`
- `AIRLINE_OPERATIONAL_KNOWLEDGE_ONTOLOGY.md`
- `GLOSSARY.md`

## Future Codex Guidance

Before implementing future phases, Codex should read and follow:

- `PASSENGER_SERVICE_OPERATIONS_MANIFESTO.md`
- `AIRLINE_OPERATIONAL_KNOWLEDGE_BLUEPRINT.md`
- `AEROASSIST_ENGINEERING_PRINCIPLES.md`
- `PASSENGER_SERVICE_ONTOLOGY.md`
- `AIRLINE_OPERATIONAL_KNOWLEDGE_ONTOLOGY.md`
- `GLOSSARY.md`

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
- Phase 36.0: Unified Airline Intelligence, Rules & Services foundation.
- Phase 36.1: Rule-aware offer builder and internal comparison matrix.
- Phase 36.2: Offer acceptance, trip accepted-offer snapshot, and booking readiness.
- Phase 36.2.5: Reference data consumer map and service catalogue governance.
- Phase 36.3: Booking workspace and manual PNR mirror foundation.
- Phase 36.4: Ticket and EMD mirror foundation.
- Phase 36.4.5: Supplementary blueprint adoption and unified workflow sync.
- Phase 36.4.6: Standalone booking, import draft, and existing-trip change/exchange foundation.
- Phase 36.5: Document foundation.
- Phase 36.6: GDS parser foundation and training samples.
- Phase 36.7: Airline policy ingestion foundation.
- Phase 36.8: Canonical special / ancillary services taxonomy.
- Phase 36.9: SSR / OSI / EMD / RFIC / RFISC service mechanics mapping foundation.
- Phase 37.0: Airline ancillary pricing schema and exception engine expansion.
- Phase 37.1: Airline policy comparison and service advisor foundation.
- Phase 37.2: Offer builder policy advisor integration foundation.
- Phase 37.3: Offer builder advisor consumption and decision pack foundation.
- Phase 37.4: Offer explanation and decision timeline foundation.
- Phase 37.5: Offer decision pack PDF and shareable review export foundation.
- Phase 37.6: Offer decision export render preview foundation.
- Phase 37.7: Offer decision export approval and manual release readiness foundation.
- Phase 37.8: Offer decision export manual delivery handoff foundation.
- Phase 37.9: Offer decision export manual delivery outcome tracking foundation.
- Phase 38.0: Offer decision export audit review foundation.
- Phase 38.1: Offer decision export governance foundation.
- Phase 38.2: Offer decision export compliance evidence foundation.
- Phase 39.0: Airline intelligence data pack foundation.
- Phase 39.1: Airline intelligence data pack review and promotion readiness foundation.
- Phase 39.2: Airline intelligence knowledge versioning and publication control foundation.
- Phase 39.3: Airline intelligence agency consumption bridge.
- Phase 39.4: Platform / agency UX consolidation and navigation clarity.
- Phase 39.5: SaaS subscription and entitlement foundation.
- Phase 39.6: Subscription entitlement UI guardrails and navigation visibility.
- Phase 39.7: Agency feature flags foundation.
- Phase 39.8: Agency feature flag readiness and audit foundation.
- Phase 39.9: Feature flag bundles foundation.
- Phase 40.0: Agency feature bundle assignment foundation.
- Phase 40.1: Capability catalog foundation.
- Phase 40.1: Feature bundle rollout readiness foundation.
- Phase 40.2: Feature bundle rollout plan foundation.
- Phase 40.3: Agency capability rollout dashboard foundation.
- Phase 40.4: Feature bundle rollout approval foundation.
- Phase 40.5: Feature bundle rollout schedule foundation.
- Phase 40.6: Feature bundle rollout timeline foundation.
- Phase 40.7: Feature bundle rollout dependency foundation.
- Phase 40.8: Feature bundle rollout risk register foundation.
- Phase 40.9: Feature bundle rollout issue log foundation.
- Phase 40.10: Feature bundle rollout decision register foundation.
- Phase 40.11: Feature bundle rollout change request foundation.
- Phase 40.12: Feature bundle rollout rollback plan foundation.
- Phase 40.13: Feature bundle rollout summary pack foundation.
- Phase 41.0: Operational travel workspace foundation.
- Phase 41.1: Travel request workspace foundation.
- Phase 41.2: Passenger workspace foundation.
- Phase 41.3: Flight workspace foundation.
- Phase 41.4: Trip workspace foundation.
- Phase 41.5: Offer workspace foundation.
- Phase 41.6: Booking workspace foundation.
- Phase 41.7: Ticket workspace foundation.
- Phase 41.8: EMD workspace foundation.
- Phase 41.9: SSR / OSI operational workspace foundation.
- Phase 42.0: Document workspace foundation.
- Phase 42.1: Operational timeline workspace foundation.
- Phase 42.2: Passenger service workflow engine foundation.
- Phase 50.0: Airline Operational Intelligence Engine architecture foundation.
- Phase 50.1: Airline knowledge acquisition workspace foundation.
- Phase 50.2: Operational constraint engine foundation.
- Phase 50.3: Airline operational knowledge normalisation foundation.
- Phase 50.4: Airline operational knowledge governance and version control foundation.
- Phase 50.5: Airline operational capability matrix foundation.
- Phase 50.6: Operational knowledge evaluation engine foundation.
- Phase 50.7: Passenger service feasibility engine foundation.
- Phase 50.8: Airline and itinerary recommendation engine foundation.
- Phase 50.9: Intelligent offer builder integration foundation.
- Phase 51.0: Operational intelligence pipeline consolidation foundation.
- Phase 51.1: Service parameter taxonomy integration foundation.

Phase 35 navigation hotfix:

- Platform Owner navigation no longer includes a global Agency Workspace shortcut; agency workspace entry is contextual from platform agency management/detail pages.
- `/platform/agencies` and `/platform/airlines` render defensive management/foundation pages instead of blank routes.
- Agency reference data governance remains consume-and-suggest only.

Phase 36.0 foundation note:

- Platform owns global airline intelligence, airline rules core records, and unified exception rules.
- Agencies consume and evaluate rules through request/trip special-services workspaces; they do not edit platform global rules.
- SSR/OSI generation is deterministic preview text for supported service codes and remains staff-reviewed.
- Full visual airline dashboards, AI reasoning engines, offer builder expansion, ticketing, document designer, and 100-airline datasets remain future phases.

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
- Seeded city reference records now use canonical IATA city codes (`SOF`, `NYC`, `LON`) with legacy slugs preserved as aliases and an idempotent migration/backfill for existing data.
- City advanced metadata now mirrors canonical fields (`record_type`, `iata_city_code`, `city_name`, `legacy_codes`, `country_code`) and backend validation rejects contradictory city metadata.

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

### Phase 36.0: Unified Airline Intelligence, Rules & Services Foundation

Implemented scope:

- Additive platform-owned airline intelligence foundation records beyond the earlier airline knowledge shell.
- `AirlineRulesCore` as the shared future source of truth for UMNR, PRM, medical, pets/service animals, baggage, seating, meals, cargo, VIP, POS, and general airline rules.
- `UnifiedExceptionRule` and a safe exception engine with exact matching and JSON/path comparisons only; no unsafe expression evaluation.
- `PassengerServiceRequest` as the agency-owned bridge for request, trip, booking, passenger, and segment special-service checks.
- Deterministic SSR/OSI preview generation for core UMNR, PRM, medical, pets, service animal, seating, meal, cargo, regulated item, VIP, and diplomatic service types.
- Platform APIs and `/platform/rules-services` console for airline rules, exception rules, and simulation.
- Agency APIs and request/trip special-services workspace routes for service creation, evaluation, and SSR/OSI preview.
- Idempotent seed script for LH, TK, and AF sample rules/services foundation data and a Phase 36 smoke script.
- Readiness flags and non-blocking counts under `rules_and_services`.

Avoid adding:

- Full offer builder bundles, visual maps, airline dashboards, AI reasoning/calls, ticketing, document designer, automatic booking, scraping, or large fake airline datasets.

### Phase 36.1: Rule-Aware Offer Builder And Internal Comparison Matrix

Implemented scope:

- Agency-owned offer workspaces linked to requests and/or trip dossiers.
- Rule-aware offer options with segments, fare bundles, pricing lines, rule summaries, service feasibility, warnings, and recommendation metadata.
- Internal comparison matrix generation and saved comparison snapshots.
- Request and trip entry points to create or open offer workspaces without replacing source records.
- Agency offer workspace list, detail, and builder UI routes.
- Readiness flags and non-blocking counts under `offer_builder`.

Avoid adding:

- Live fare search, supplier booking, payment capture, or client share links.

### Phase 36.2: Offer Acceptance, Trip Snapshot, And Booking Readiness

Implemented scope:

- `OfferAcceptance` records that snapshot accepted pricing, routing, fare bundle, services, pets, special items, rule feasibility, and client-visible summary.
- `TripAcceptedOfferSnapshot` records that anchor the accepted offer to the trip operational baseline.
- `BookingReadinessPackage` records with provider target, passengers, segments, pricing, service snapshots, SSR/OSI previews, warnings, required documents, policy violations, and readiness checks.
- Safe supersede/cancel lifecycle for accepted options without deleting prior snapshots.
- Agency acceptance/readiness APIs and UI panels on offer workspace, builder, and trip dossier pages.
- Readiness flags and non-blocking counts under `offer_builder`.

Avoid adding:

- Live GDS/NDC/supplier calls, PNR creation, ticketing, EMD issuance, invoices, payments, or document designer actions.

### Phase 36.2.5: Reference Data Consumer Map And Service Catalogue Governance

Implemented scope:

- Reference domain usage map covering ownership, agency behavior, consumers, routes, models, workflows, import support, enrichment support, health checks, operational impact, and missing-data risk.
- Reference Health & Action Required endpoints replacing unexplained Important Records with explicit missing metadata, active workflow usage, recent changes, review, pinned, and high-risk domain logic.
- Domain-aware import templates plus preview/apply import APIs for governed reference domains and service catalogue records.
- Reference Enrichment Pack model/API facade with default operational metadata packs for airports, airlines, service catalogue, documents, pets, and special items.
- Editable platform Service Catalogue APIs and UI with operational mappings for request UI, rules/services, SSR/OSI, offers, acceptance, booking readiness, documents, and future EMD readiness.
- Agency consume-only service catalogue view with correction suggestions remaining in the reference suggestion workflow.
- Compatibility-layer links from service catalogue records into requested services, passenger service requests, rules/services evaluation, offer builder snapshots, accepted offer snapshots, trip service items, and booking readiness packages.
- Readiness flags and non-blocking counts under `reference_data`.

Avoid adding:

- Live booking/PNR creation, ticketing, EMD issuance, supplier execution, invoices/accounting, payment processing, document designer actions, or agency mutation of platform-owned reference/service catalogue records.

### Phase 36.3: Booking / PNR Foundation From Booking Readiness

Implemented scope:

- `BookingWorkspace` records created from booking readiness packages with immutable copied passenger, segment, pricing, service catalogue, pet, special-item, SSR/OSI, warning, document, and policy snapshots.
- `BookingRecord` draft/manual PNR mirror records linked to booking workspaces, preserving provider target, manual locator/status fields, raw provider payload placeholders, and internal mirror JSON.
- Extended booking timeline events for booking workspace, booking record, trip, description, and payload data while preserving legacy booking timeline compatibility.
- Agency APIs for list, create-from-readiness, detail, status update, draft mirror rebuild, cancel, and manual booking record update.
- Agency UI routes `/agency/booking-workspaces` and `/agency/booking-workspaces/{booking_workspace_id}` plus trip/offer readiness entry points.
- Readiness flags and non-blocking counts under `booking_foundation`.

Avoid adding:

- Live GDS/NDC/supplier calls, provider booking execution, ticketing, EMD issuance, invoices, payments, document designer actions, or backward mutation of accepted offer/request snapshots.

### Phase 36.4: Tickets And EMD Foundation

Implemented scope:

- Extended compatible `TicketRecord` and `EMDRecord` mirror fields linked to `BookingRecord` and `BookingWorkspace`.
- `TicketCoupon` records for coupon-level passenger/segment ticket status.
- `EmdCoupon` records for service/segment/coupon-level EMD status.
- `TicketEmdTimelineEvent` records for ticket and EMD mirror lifecycle events.
- Agency APIs for ticket list/detail/update/create-from-booking, EMD list/detail/update/create-from-booking-service, and ticket/EMD readiness.
- Agency UI routes `/agency/tickets-emds`, `/agency/tickets/{ticket_record_id}`, and `/agency/emds/{emd_record_id}` plus booking workspace and trip summary panels.
- Service catalogue EMD mappings are preserved in EMD mirrors and readiness summaries.
- Readiness flags and non-blocking counts under `ticket_emd_foundation`.

Avoid adding:

- Live ticket issuance, live EMD issuance, GDS/NDC/supplier calls, BSP/ARC settlement, payment capture, invoices/accounting postings, or backward mutation of accepted offer/booking readiness snapshots.

### Phase 36.4.5: Supplementary Blueprint Adoption And Unified Workflow Sync

Implemented scope:

- Supplementary blueprint adoption map documenting existing equivalents, adopted foundations, deferred ideas, and rejected structures.
- Canonical route policy keeping `/platform/*` and `/agency/*` as the app roots while rejecting supplementary `/agent/*` and `/admin/*`.
- `AiTraceEvent`, `AdmRiskEvent`, `GdsParseSample`, and `AirlineBrandAsset` foundation records with Mongo indexes.
- Static `BlueprintAdoptionService` and platform governance APIs under `/api/platform/blueprint`.
- Platform UI route `/platform/blueprint` for adoption map, route policy, gaps, and next phase recommendations.
- `SpecialServicesUnifiedFacade` over the existing rules/services, exception, SSR/OSI, and service catalogue foundations.
- Readiness flags and non-blocking counts under `blueprint_sync`.
- Recognition that Phase 36.4 already built Tickets + EMD Foundation and that the booking workspace creation entry UX fix is canonical.

Avoid adding:

- `/agent` or `/admin` route roots, live provider execution, real ticketing/EMD issuance, supplier credentials, full document designer, full AI engines, visual airline dashboards, payments, invoices/accounting, or duplicate trip/request/offer/booking/ticket/EMD models.

### Phase 36.4.6: Standalone Booking, Import Draft, And Existing-Trip Change/Exchange Foundation

Implemented scope:

- Extended booking workspace, booking record, ticket record, and EMD record mirrors with source-context and standalone/import/change linkage fields.
- Added `BookingImportDraft`, `TripChangeOperation`, `TicketExchangeOperation`, and `EmdExchangeOperation` foundation records with Mongo indexes.
- Added internal-only APIs for manual booking workspaces, manual ticket/EMD mirrors, booking import drafts, conservative import parsing, trip change operations, and ticket/EMD exchange mirror operations.
- Added `/agency/booking-imports` plus booking workspace, ticket/EMD, and trip detail UI entry points for manual/import/change workflows.
- Added request/offer linkage fields for future change/exchange quotes without rebuilding offer builder.
- Readiness flags and non-blocking counts under `booking_foundation`, `ticket_emd_foundation`, `change_exchange_foundation`, and `blueprint_sync`.
- Recognition that agencies need four valid internal workflows: request/offer-driven, standalone manual, imported GDS/confirmation, and existing-trip change/exchange.

Avoid adding:

- Live GDS/NDC/supplier calls, live booking creation, real ticket/EMD issuance, real exchange/reissue/refund/void execution, payments, invoices/accounting, full document designer, `/agent` or `/admin` route roots, or duplicate trip/request/offer/booking/ticket/EMD models.

### Phase 36.5: Document Foundation / Offer-Trip-Booking-Ticket-EMD Documents

Implemented scope:

- Extended document types and templates for offer summaries/comparisons, trip confirmations, booking confirmations, PNR mirrors, ticket receipts, EMD receipts, service confirmations, medical/pet/special-item summaries, change/exchange/refund/import review summaries, and internal case summaries.
- Added `DocumentRenderJob`, `DocumentPackage`, and `DocumentShareRecord` foundation records with agency-owned indexes.
- Added `DocumentContextService` to normalize context from requests, offers, trips, booking workspaces/records, tickets, EMDs, booking imports, trip changes, ticket/EMD exchanges, service requests, and mixed context.
- Added `DocumentRenderService` for platform default template seeding, internal HTML/Markdown/JSON preview rendering, rerendering, packages, and manual/internal share records.
- Added agency document APIs under `/api/agencies/{agency_id}/documents/*` and platform default-template APIs under `/api/platform/documents/*`.
- Reworked `/agency/documents` into the unified document foundation console and added document entry points from trip detail, offer workspace/builder, booking workspace detail, Tickets & EMDs, and booking imports.
- Added `/platform/document-templates` for platform owners to inspect and seed default document templates.
- Added readiness flags and counts under `document_foundation` while keeping live delivery, e-signature, payments, invoice/accounting, settlement, provider execution, and required PDF export disabled.

Avoid adding:

- Full visual document designer, public document links, automatic delivery integrations, e-signature, payment or invoice/accounting workflows, settlement, live provider execution, or duplicate request/trip/offer/booking/ticket/EMD models.

### Phase 36.6: GDS Parser Foundation + Training Samples

Implemented scope:

- Added governed parser profiles, parser versions, parser runs, parsed entities, parse corrections, training samples, and parser evaluation records.
- Extended booking import drafts with latest parser run id, profile/version ids, overall confidence, entity counts, and normalized structured previews.
- Added deterministic `GdsParserService` rules for conservative PNR/itinerary/ticket/EMD/pricing/SSR/OSI extraction without external calls.
- Added agency APIs under `/api/agencies/{agency_id}/gds-parser/*` for profile listing, parse-text, import-draft parsing, run/entity review, corrections, and training sample creation.
- Added platform APIs under `/api/platform/gds-parser/*` for default profile/version seeding, version creation/activation, training sample review, and parser evaluations.
- Added `/agency/gds-parser` and `/platform/gds-parser` UI routes, plus booking-import and document-foundation entry points.
- Added `gds_parser_run` document context plus `gds_parse_review_summary` and `booking_import_review_summary` document types/templates.
- Added readiness flags and counts under `gds_parser_foundation`.

Avoid adding:

- Live GDS/NDC/provider connectivity, external AI parser calls, automatic mirror import, full host grammar coverage, provider reconciliation, live booking/ticket/EMD/exchange/refund/void execution, payments, invoices/accounting, settlement, `/agent` or `/admin` routes, or duplicate booking/ticket/EMD models.

### Phase 36.7: Airline Policy Ingestion Foundation

Implemented scope:

- Added governed airline policy source, section, extraction run, extracted rule/price/communication/EMD/exception candidate, review correction, and approved knowledge records.
- Added deterministic `AirlinePolicyIngestionService` extraction for obvious service identity, age/applicability, pricing, SSR/OSI/GDS/NDC communication, EMD/RFIC/RFISC, and exception text signals.
- Added platform governance APIs under `/api/platform/airline-policy/*` for source creation, section detection, extraction, candidate review, explicit promotion, and approved knowledge listing.
- Added agency APIs under `/api/agencies/{agency_id}/airline-policy/*` for read-only approved library access, local source creation/extraction/review, and submit-for-platform-review.
- Added `/platform/airline-policy-ingestion` and `/agency/airline-policy-library` UI routes.
- Added document source contexts for `airline_policy_source`, `airline_policy_extraction_run`, and `airline_policy_approved_knowledge`, plus policy extraction/review summary document templates.
- Added readiness flags and counts under `airline_policy_ingestion_foundation`.

Avoid adding:

- External AI extraction, airline scraping, live GDS/NDC/provider calls, automatic global promotion, full comparison matrix, full SSR/OSI/EMD engine replacement, ticketing/EMD/payment/refund/void/accounting/settlement execution, `/agent` or `/admin` routes, or duplicate rules/services/reference/document/GDS foundations.

### Phase 36.8: Canonical Special / Ancillary Services Taxonomy

Implemented scope:

- Added canonical service domain, family, and variant records for special/ancillary service normalization.
- Added airline service aliases, deterministic mapping rules, applicability dimensions, policy outcome types, candidate taxonomy links, and taxonomy review corrections.
- Added idempotent baseline taxonomy seeding for children, mobility, medical, pets/animals, baggage/special items, seating, meals, VIP/protocol, disruption, documents, claims, distribution/payment, and fallback domains.
- Added conservative deterministic mapping from airline terms, commercial labels, SSR/GDS codes, and Phase 36.7 policy candidates into canonical domain/family/variant results.
- Added platform APIs under `/api/platform/service-taxonomy/*` for global taxonomy governance, seeding, mapping tests, candidate links, and review corrections.
- Added agency APIs under `/api/agencies/{agency_id}/service-taxonomy/*` for read-only taxonomy lookup, deterministic mapping, agency-local candidate links, and agency-local corrections.
- Added `/platform/service-taxonomy` and `/agency/service-taxonomy` UI routes.
- Added readiness flags and counts under `service_taxonomy_foundation`.

Avoid adding:

- Full SSR/OSI instruction mapping, EMD/RFIC/RFISC payment mechanics, normalized ancillary pricing matrices, live GDS/NDC/provider connectivity, live booking/ticketing/EMD issuance, scraping, external AI mapping, agency auto-promotion, `/agent` or `/admin` routes, or replacement of the service catalogue and Rules & Services foundations.

### Phase 36.9: SSR / OSI / EMD / RFIC / RFISC Mapping Foundation

Implemented scope:

- Added separate communication mechanics records for airline service request channels, SSR/OSI/OTHS templates, request requirements, status recognition, and rejection/unable patterns.
- Added separate payment mechanics records for service payment rules, EMD issuance metadata, RFIC/RFISC mappings, interline restrictions, and EMD lifecycle rules.
- Added candidate mechanics links that connect Phase 36.7 policy candidates and Phase 36.8 taxonomy links to mechanics records without automatic global promotion.
- Added deterministic airline + canonical domain/family/variant lookup that returns `communication` and `payment` sections separately with warnings for no-match results.
- Added platform APIs under `/api/platform/service-mechanics/*` for global mechanics governance and agency APIs under `/api/agencies/{agency_id}/service-mechanics/*` for read-only lookup plus agency-local candidate links.
- Added `/platform/service-mechanics` and `/agency/service-mechanics` UI routes.
- Added readiness flags and counts under `service_mechanics_mapping_foundation`.

Avoid adding:

- Live SSR/OSI transmission, live GDS/NDC/provider execution, live booking/ticket/EMD issuance, payment capture, invoice/accounting posting, BSP/ARC settlement, automated refund/exchange/void execution, scraping, external AI mapping/extraction, agency auto-promotion, `/agent` or `/admin` routes, or destructive Mongo index migration.

### Phase 37: Provider Import And Issuance Provenance

Recommended scope:

- Provider import provenance, raw source payload preservation, parser-run-to-provider reconciliation, and deeper ticket/EMD reconciliation.
- Manual import/reconciliation workflow and provenance metadata.

Avoid adding:

- Direct GDS commands, NDC execution, automated ticketing, live EMD issuance, exchange/refund/void execution, or settlement without explicit authorization.

### Phase 37.0: Airline Ancillary Pricing Schema And Exception Engine Expansion

Implemented scope:

- Added normalized ancillary pricing rules, price components, applicability dimensions, pricing matrices, matrix rows, expanded service exception rules, quote scenarios/results, and policy candidate pricing links.
- Added deterministic quote evaluation that matches airline + canonical service pricing rules, applies conservative applicability filters, separates pricing from exceptions, sums fixed components, and flags range/percentage/unknown pricing for manual review.
- Added platform APIs and `/platform/ancillary-pricing` for global pricing/exception governance.
- Added agency APIs and `/agency/ancillary-pricing` for read-only pricing lookup, deterministic quote scenarios/results, and agency-local candidate pricing links.
- Added readiness flags and counts under `ancillary_pricing_exception_foundation`.

Avoid adding:

- Invoice/payment/accounting/ledger/BSP/ARC/settlement logic, EMD/ticket issuance, live GDS/NDC/provider execution, automatic policy/taxonomy/mechanics/pricing promotion, external AI, scraping, `/agent` or `/admin` routes, or destructive Mongo index migration.

### Phase 37.1: Airline Policy Comparison And Service Advisor Foundation

Implemented scope:

- Added airline policy comparison profiles, generated comparison snapshots, normalized comparison rows, service advisor scenarios/results, and saved comparison views.
- Added deterministic comparison/advisor service that consumes taxonomy, policy, mechanics, pricing, and exception metadata while returning safe empty summaries when records are missing.
- Added operational complexity scoring from deterministic metadata only; the score is not an automatic airline recommendation.
- Added platform APIs and `/platform/policy-comparison` for global comparison profile governance, comparison generation, advisor evaluation, and saved views.
- Added agency APIs, `/agency/policy-comparison`, and `/agency/airline-service-advisor` for read-only global profile consumption and agency-local snapshots, scenarios, results, and saved views.
- Added readiness flags and counts under `policy_comparison_service_advisor_foundation`.

Avoid adding:

- Live booking, live SSR/OSI transmission, provider action, ticketing, EMD issuance, payment/invoice/accounting/BSP/ARC/settlement logic, automatic airline recommendation, external AI, scraping, agency-to-global auto-promotion, `/agent` or `/admin` routes, or destructive Mongo index migration.

### Phase 37.2: Offer Builder Policy Advisor Integration Foundation

Implemented scope:

- Added offer policy advisor contexts, offer-linked airline rows, warnings, manual decision notes, and saved snapshots.
- Added deterministic offer advisor integration that builds metadata context from offer workspaces/options, compares airlines through the Phase 37.1 advisor layer, links ancillary quote results, stores service mechanics lookup metadata, and preserves taxonomy references.
- Added agency APIs and `/agency/offer-policy-advisor` for offer-linked context build/evaluate, artifact attach, manual notes, warnings, and saved snapshots.
- Added platform read-only diagnostics APIs and `/platform/offer-policy-advisor`.
- Added readiness flags and counts under `offer_policy_advisor_integration_foundation`.

Avoid adding:

- Live booking, live SSR/OSI transmission, provider action, ticketing, EMD issuance, payment/invoice/accounting/BSP/ARC/settlement logic, automatic airline recommendation, automatic offer price mutation, external AI, scraping, agency-to-global mutation, `/agent` or `/admin` routes, or destructive Mongo index migration.

### Phase 37.3: Offer Builder Advisor Consumption / Decision Pack Foundation

Implemented scope:

- Added offer decision packs, option-level evidence rows, warning summaries, review notes, and immutable decision pack snapshots.
- Added deterministic advisor evidence consumption from offer policy advisor contexts/saved snapshots, comparison rows, ancillary quote results, service mechanics metadata, taxonomy references, and offer workspace/option context.
- Added agency APIs and `/agency/offer-decision-packs` for pack build/rebuild, advisor evidence attach, review note create/update, evidence/warning listing, and immutable snapshots.
- Added platform read-only diagnostics APIs and `/platform/offer-decision-packs`.
- Added readiness flags and counts under `offer_builder_advisor_consumption_decision_pack_foundation`.

Avoid adding:

- Live booking, live SSR/OSI transmission, provider action, ticketing, EMD issuance, payment/invoice/accounting/BSP/ARC/settlement logic, automatic airline ranking/recommendation, automatic offer price mutation, external AI, scraping, agency-to-global mutation, `/agent` or `/admin` routes, or destructive Mongo index migration.

### Phase 37.4: Offer Explanation / Decision Timeline Foundation

Implemented scope:

- Added offer decision explanations, decision timeline events, evidence references, decision reasons, acknowledgements, and immutable audit snapshots.
- Added a deterministic explanation service that links explanation records to existing decision packs and derives evidence references from advisor evidence, comparison snapshots, ancillary quote results, service mechanics metadata, taxonomy references, warnings, and review notes.
- Added agency APIs and `/agency/offer-decision-explanations` for explanation create/update, timeline append/list, evidence/reason/acknowledgement listing, reason and acknowledgement creation, and immutable audit snapshots.
- Added platform read-only diagnostics APIs and `/platform/offer-decision-explanations`.
- Added readiness flags and counts under `offer_decision_explanation_foundation`.

Avoid adding:

- Live booking, live SSR/OSI transmission, provider action, ticketing, EMD issuance, payment/invoice/accounting/BSP/ARC/settlement logic, automatic airline ranking/recommendation, automatic offer price mutation, external AI, scraping, agency-to-global mutation, `/agent` or `/admin` routes, or destructive Mongo index migration.

### Phase 37.5: Offer Decision Pack PDF / Shareable Review Export Foundation

Implemented scope:

- Added offer decision export records, ordered export sections, metadata-only PDF/JSON artifact records, unsent recipient drafts, and export audit events.
- Added deterministic export generation from existing decision packs, option evidence, warnings, review notes, explanations, timeline events, reasons, acknowledgements, and audit snapshots.
- Added agency APIs and `/agency/offer-decision-exports` for export generation, listing, detail review, artifact metadata, recipient drafts, and audit events.
- Added platform read-only diagnostics APIs and `/platform/offer-decision-exports`.
- Added readiness flags and counts under `offer_decision_export_foundation`.

Avoid adding:

- Automatic email sending, public links, live PDF delivery/storage, live booking, live SSR/OSI transmission, provider action, ticketing, EMD issuance, payment/invoice/accounting/BSP/ARC/settlement logic, automatic airline ranking/recommendation, automatic offer price mutation, external AI, scraping, agency-to-global mutation, `/agent` or `/admin` routes, or destructive Mongo index migration.

### Phase 37.6: Offer Decision Export Render Preview Foundation

Implemented scope:

- Added offer decision export preview records, ordered preview sections, typed render-preview blocks, metadata completeness validation records, and immutable preview snapshots.
- Added deterministic preview generation from existing offer decision exports, export sections, artifacts, recipient drafts, audit events, decision pack metadata, explanations, timeline events, reasons, acknowledgements, and audit snapshots.
- Added agency APIs and `/agency/offer-decision-export-previews` for preview generation, metadata validation, preview detail review, and immutable preview snapshots.
- Added platform read-only diagnostics APIs and `/platform/offer-decision-export-previews`.
- Added readiness flags and counts under `offer_decision_export_preview_foundation`.

Avoid adding:

- Automatic email/SMS sending, public links, real PDF delivery/storage, live booking, live SSR/OSI transmission, provider action, ticketing, EMD issuance, payment/invoice/accounting/BSP/ARC/settlement logic, automatic airline ranking/recommendation, automatic offer price mutation, external AI, scraping, agency-to-global mutation, `/agent` or `/admin` routes, or destructive Mongo index migration.

### Phase 37.7: Offer Decision Export Approval / Manual Release Readiness Foundation

Implemented scope:

- Added offer decision export approval records, approval checkpoints, manual release readiness records, release holds, and immutable release readiness snapshots.
- Added deterministic metadata assembly from existing offer decision export previews, preview validations, preview snapshots, and source export metadata.
- Added agency APIs and `/agency/offer-decision-export-releases` for creating approval metadata, recording checkpoints, updating approval status, preparing manual release readiness, adding/releasing holds, and saving immutable release snapshots.
- Added platform read-only diagnostics APIs and `/platform/offer-decision-export-releases`.
- Added readiness flags and counts under `offer_decision_export_release_readiness_foundation`.

Avoid adding:

- Automatic email/SMS sending, public links, real PDF delivery/storage, live booking, live SSR/OSI transmission, provider action, ticketing, EMD issuance, payment/invoice/accounting/BSP/ARC/settlement logic, automatic airline ranking/recommendation, automatic offer price mutation, external AI, scraping, agency-to-global mutation, `/agent` or `/admin` routes, or destructive Mongo index migration.

### Phase 37.8: Offer Decision Export Manual Delivery Handoff Foundation

Implemented scope:

- Added offer decision export manual delivery handoff records, recipient metadata, attachment metadata, instruction/checklist metadata, and immutable handoff snapshots.
- Added deterministic metadata handoff creation from existing offer decision exports, previews, approvals, and release readiness records.
- Added agency APIs and `/agency/offer-decision-export-deliveries` for handoff metadata creation, manual status updates, recipient metadata, attachment metadata, instructions, instruction completion metadata, recipient status metadata, and immutable handoff snapshots.
- Added platform read-only diagnostics APIs and `/platform/offer-decision-export-deliveries`.
- Added readiness flags and counts under `offer_decision_export_manual_delivery_handoff_foundation`.

Avoid adding:

- Automatic email/SMS sending, SMTP/SMS/storage provider calls, public links, real PDF delivery/storage, live booking, live PNR mutation, live SSR/OSI transmission, provider action, ticketing, EMD issuance, payment/invoice/accounting/BSP/ARC/settlement logic, automatic airline ranking/recommendation, automatic offer price mutation, external AI, scraping, agency-to-global mutation, `/agent` or `/admin` routes, or destructive Mongo index migration.

### Phase 37.9: Offer Decision Export Manual Delivery Outcome Tracking Foundation

Implemented scope:

- Added offer decision export manual delivery outcome records, manual outcome events, receipt metadata, issue metadata, and immutable outcome snapshots.
- Added deterministic outcome creation from existing manual delivery handoff records without mutating handoff state.
- Added agency APIs and `/agency/offer-decision-export-delivery-outcomes` for creating/listing outcomes, recording manual events, adding receipt metadata, adding/resolving issue metadata, and saving immutable outcome snapshots.
- Added platform read-only diagnostics APIs and `/platform/offer-decision-export-delivery-outcomes`.
- Added readiness flags and counts under `offer_decision_export_manual_delivery_outcome_foundation`.

Avoid adding:

- Automatic email/SMS sending, public links, real PDF delivery/storage, live booking, live PNR mutation, live SSR/OSI transmission, provider action, ticketing, EMD issuance, payment/invoice/accounting/BSP/ARC/settlement logic, automatic airline ranking/recommendation, automatic offer price mutation, external AI, scraping, agency-to-global mutation, `/agent` or `/admin` routes, or destructive Mongo index migration.

### Phase 38.0: Offer Decision Export Audit Review Foundation

Implemented scope:

- Added offer decision export audit review records, findings, checklist items, and immutable review snapshots.
- Added deterministic lifecycle coverage review over decision pack, explanation, export, preview, release readiness, manual delivery handoff, and manual delivery outcome metadata.
- Added agency APIs and `/agency/offer-decision-export-audit-reviews` for creating/listing reviews, recording findings, checklist items, review status, and immutable snapshots.
- Added platform read-only diagnostics APIs and `/platform/offer-decision-export-audit-reviews`.
- Added readiness flags and counts under `offer_decision_export_audit_review_foundation`.
- Added `docs/architecture/offer-decision-export-audit-review-foundation.md`.

Avoid adding:

- Automatic email/SMS sending, public links, real PDF delivery/storage, live booking, live PNR mutation, live SSR/OSI transmission, provider action, ticketing, EMD issuance, payment/invoice/accounting/BSP/ARC/settlement logic, automatic airline ranking/recommendation, automatic offer price mutation, external AI, scraping, agency-to-global mutation, `/agent` or `/admin` routes, or destructive Mongo index migration.

### Phase 38.1: Offer Decision Export Governance Foundation

Implemented scope:

- Added offer decision export governance records, governance rules, retention policy metadata, legal basis metadata, archive status metadata, governance exceptions, and immutable governance snapshots.
- Added agency APIs and `/agency/offer-decision-export-governance` for creating/listing governance metadata linked to export audit review lifecycles.
- Added platform read-only diagnostics APIs and `/platform/offer-decision-export-governance`.
- Added readiness flags and counts under `offer_decision_export_governance_foundation`.
- Added `docs/architecture/offer-decision-export-governance-foundation.md`.

Avoid adding:

- Automatic email/SMS sending, public links, real PDF delivery/storage, live booking, live PNR mutation, live SSR/OSI transmission, provider action, ticketing, EMD issuance, payment/invoice/accounting/BSP/ARC/settlement logic, automatic airline ranking/recommendation, automatic offer price mutation, external AI, scraping, agency-to-global mutation, `/agent` or `/admin` routes, or destructive Mongo index migration.

### Phase 38.2: Offer Decision Export Compliance Evidence Foundation

Implemented scope:

- Added offer decision export compliance evidence records, requirements, checks, pass/fail result metadata, exceptions, and immutable compliance snapshots.
- Added agency APIs and `/agency/offer-decision-export-compliance` for creating/listing compliance metadata linked to export governance records.
- Added platform read-only diagnostics APIs and `/platform/offer-decision-export-compliance`.
- Added readiness flags and counts under `offer_decision_export_compliance_foundation`.
- Added `docs/architecture/offer-decision-export-compliance-foundation.md`.

Avoid adding:

- Automatic email/SMS/notification sending, public links, PDF/document delivery, live booking, live reservation creation, live PNR mutation, live GDS/provider action, ticketing, EMD issuance, payment/invoice/accounting/BSP/ARC/settlement logic, automatic airline ranking/recommendation, automatic offer or price mutation, external AI, scraping, agency-to-global mutation, `/agent` or `/admin` routes, or destructive Mongo index migration.

### Phase 39.0: Airline Intelligence Data Pack Foundation

Implemented scope:

- Added governed airline intelligence data packs, staged data pack items, validation issues, import runs, review notes, and coverage snapshots.
- Added deterministic local validation and inline JSON/CSV dry-run staging without scraping, external calls, external AI, or automatic promotion into operational airline tables.
- Added platform APIs and `/platform/airline-intelligence-data-packs` for guided data pack creation, review, validation, dry runs, and coverage snapshots.
- Added agency read-only APIs and `/agency/airline-intelligence-coverage` for plain-language coverage visibility without data-maintenance controls.
- Added CRM, agency website/CMS, client portal, and offer-builder alignment metadata flags for future safe consumption.
- Added readiness flags and counts under `airline_intelligence_data_pack_foundation`.
- Added `docs/architecture/airline-intelligence-data-pack-foundation.md`.

Avoid adding:

- Live scraping, external APIs, external AI, automatic promotion into operational airline tables, recommendation engines, provider/GDS execution, booking, reservation creation, PNR mutation, ticketing, EMD issuance, payment/invoice/accounting/settlement logic, public client portal links, CMS publishing, automatic document delivery, email/SMS/notification sending, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 39.1: Airline Intelligence Data Pack Review And Promotion Readiness Foundation

Implemented scope:

- Added airline intelligence data pack review records, review checklist items, field mappings, duplicate/conflict metadata, promotion-readiness records, and immutable review snapshots.
- Added metadata-only conflict detection for staged item duplicates, missing mappings, missing target references, and unsafe surface flags.
- Added platform APIs and `/platform/airline-intelligence-data-pack-reviews` for review, approval/rejection metadata, checklist updates, field mapping, conflict review, promotion-readiness marking, and snapshots.
- Added agency read-only APIs and `/agency/airline-intelligence-review-coverage` for plain-language safe-use coverage summaries.
- Added safe-consumption flags for internal CRM, agency display, CMS website display, client portal display, and offer builder on review/readiness metadata.
- Added readiness flags and counts under `airline_intelligence_data_pack_review_foundation`.
- Added `docs/architecture/airline-intelligence-data-pack-review-foundation.md`.

Avoid adding:

- Automatic promotion into operational airline tables, live scraping, external APIs, external AI, CMS publishing, client portal publishing, recommendations, provider/GDS execution, booking, reservation creation, PNR mutation, ticketing, EMD issuance, payment/invoice/accounting/settlement logic, email/SMS/notification sending, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 39.2: Airline Intelligence Knowledge Versioning And Publication Control Foundation

Implemented scope:

- Added airline intelligence knowledge versions, version items, release channels, release assignments, version comparisons, rollback plans, and immutable version snapshots.
- Added platform APIs and `/platform/airline-intelligence-knowledge-versions` for draft version creation, reviewed item inclusion, freeze/approve/published-metadata status, release-channel assignment, comparison, rollback planning, and snapshots.
- Added agency read-only APIs and `/agency/airline-intelligence-knowledge-versions` for current/preview version visibility and plain-language change summaries without raw staged payload exposure.
- Added readiness flags and counts under `airline_intelligence_knowledge_versioning_foundation`.
- Added `docs/architecture/airline-intelligence-knowledge-versioning-foundation.md`.

Avoid adding:

- Automatic promotion into operational airline tables, live scraping, external APIs, external AI, CMS publishing, client portal publishing, recommendations, provider/GDS execution, booking, reservation creation, PNR mutation, ticketing, EMD issuance, payment/invoice/accounting/settlement logic, email/SMS/notification sending, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 39.3: Airline Intelligence Agency Consumption Bridge

Implemented scope:

- Added airline intelligence agency consumption profiles, agency assignment views, usage readiness metadata, consumption notes, and immutable consumption snapshots.
- Added platform APIs and `/platform/airline-intelligence-agency-consumption` for safe-use profile governance, readiness calculation, notes, and snapshots.
- Added agency read-only APIs and `/agency/airline-intelligence-consumption` for CRM, agency website, client portal, and offer builder safe-use visibility without raw internal notes.
- Added readiness flags and counts under `airline_intelligence_agency_consumption_bridge`.
- Added `docs/architecture/airline-intelligence-agency-consumption-bridge.md`.

Avoid adding:

- Automatic publishing, CMS/client portal publication, recommendation engines, provider/GDS execution, booking, reservation creation, PNR mutation, ticketing, EMD issuance, payment/invoice/accounting/settlement logic, scraping, external APIs, external AI, email/SMS/notification sending, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 39.4: Platform / Agency UX Consolidation And Navigation Clarity

Implemented scope:

- Added shared frontend module catalog metadata for route descriptions, audiences, helper badges, safety status, and visible labels.
- Updated PlatformLayout and platform dashboard to use “Platform Console” and plain-language module groups for SaaS/agencies, airline intelligence governance, agency website/CMS governance, CRM/client portal governance, offer/document governance, and system readiness.
- Updated AgencyLayout and agency dashboard to use “Agency Workspace” and plain-language module groups for daily work, clients/passengers, requests/offers/trips, website/CMS, airline intelligence visibility, documents/delivery, and settings.
- Added readiness flags under `platform_agency_ux_consolidation`.
- Added `docs/architecture/platform-agency-ux-consolidation.md`.

Avoid adding:

- New route roots, route aliases, CMS/client portal publishing, recommendations, provider/GDS execution, booking, reservation creation, PNR mutation, ticketing, EMD issuance, payment/invoice/accounting/settlement logic, scraping, external APIs, external AI, email/SMS/notification sending, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 39.5: SaaS Subscription And Entitlement Foundation

Implemented scope:

- Added metadata-only SaaS subscription plans, plan entitlements, agency subscription assignments, entitlement readiness rows, review notes, and immutable subscription snapshots.
- Added platform APIs and `/platform/saas-subscriptions` for “Subscriptions & Entitlements” governance in the Platform Console.
- Added agency read-only APIs and `/agency/saas-subscription` for “My Subscription” visibility in the Agency Workspace.
- Added readiness flags and counts under `saas_subscription_entitlement_foundation`.
- Added `docs/architecture/saas-subscription-entitlement-foundation.md`.

Avoid adding:

- Billing, payment, invoice, settlement, automatic charging, Stripe, bank/card/tax/accounting logic, automatic access enforcement, CMS/client portal publishing, recommendations, provider/GDS execution, booking, reservation creation, PNR mutation, ticketing, EMD issuance, scraping, external APIs, external AI, email/SMS/notification sending, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 39.6: Subscription Entitlement UI Guardrails And Navigation Visibility

Implemented scope:

- Added read-only entitlement visibility summaries by agency/module using existing Phase 39.5 subscription collections.
- Added agency module visibility API under `/api/agencies/{agency_id}/saas-subscriptions/module-visibility`.
- Added platform review visibility API under `/api/platform/saas-subscriptions/entitlement-visibility`.
- Added Agency Workspace navigation and dashboard badges for Included, Limited, Review required, Not included, and Unknown.
- Added Platform Console subscription review visibility cards.
- Added readiness flags under `subscription_entitlement_ui_guardrails`.
- Added `docs/architecture/subscription-entitlement-ui-guardrails.md`.

Avoid adding:

- Billing, payment, invoice, settlement, automatic charging, Stripe, bank/card/tax/accounting logic, automatic access enforcement, destructive route blocking, CMS/client portal publishing, recommendations, provider/GDS execution, booking, reservation creation, PNR mutation, ticketing, EMD issuance, scraping, external APIs, external AI, email/SMS/notification sending, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 39.7: Agency Feature Flags Foundation

Implemented scope:

- Added metadata-only `AgencyFeatureFlag`, `AgencyFeatureFlagReview`, and `AgencyFeatureFlagSnapshot` records.
- Added platform APIs and `/platform/feature-flags` for owner review of agency-specific feature visibility metadata.
- Added agency read-only APIs and `/agency/feature-availability` for Feature Availability visibility.
- Added Enabled, Disabled, Hidden, Beta, and Pilot badges.
- Added readiness flags under `agency_feature_flags_foundation`.
- Added `docs/architecture/agency-feature-flags-foundation.md`.

Avoid adding:

- Billing, payments, Stripe, taxation, accounting, subscription charging, automatic entitlement enforcement, feature blocking, provider/GDS execution, booking, reservation creation, PNR mutation, ticketing, EMD issuance, CMS publishing, client portal publishing, scraping, external APIs, external AI, email/SMS/notification sending, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 39.8: Agency Feature Flag Readiness And Audit Foundation

Implemented scope:

- Added metadata-only `AgencyFeatureFlagAudit` and `AgencyFeatureFlagReadiness` records.
- Added platform read-only APIs and `/platform/feature-flag-audit` for feature audit history and readiness metadata.
- Added agency read-only APIs and `/agency/feature-readiness` for feature readiness checklist visibility.
- Added readiness flags under `feature_flag_audit_foundation`.
- Added `docs/architecture/agency-feature-flag-audit-foundation.md`.

Avoid adding:

- Feature enforcement, route blocking, permission changes, subscription changes, billing, payments, Stripe, taxation, accounting, subscription charging, provider/GDS execution, booking, reservation creation, PNR mutation, ticketing, EMD issuance, CMS publishing, client portal publishing, scraping, external APIs, external AI, email/SMS/notification sending, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 39.9: Feature Flag Bundles Foundation

Implemented scope:

- Added metadata-only `FeatureFlagBundle`, `FeatureFlagBundleSummary`, `FeatureFlagBundleReview`, `FeatureFlagBundleMember`, and `BundleReadiness` models.
- Added `agency_feature_flag_bundles` and `agency_feature_flag_bundle_reviews` collection/index registrations.
- Added read-only platform APIs and `/platform/feature-flag-bundles` for reusable bundle review metadata.
- Added read-only agency APIs and `/agency/feature-bundles` for available feature bundle visibility.
- Added readiness flags under `feature_flag_bundle_foundation`.
- Added `docs/architecture/agency-feature-flag-bundle-foundation.md`.

Avoid adding:

- Runtime feature enforcement, entitlement checks, billing, payments, Stripe, taxation, accounting, execution logic, module hiding, permission decisions, publishing, rollout, percentage deployments, provider integrations, AI, scraping, background workers, notifications, email/SMS sending, API integrations, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 40.0: Agency Feature Bundle Assignment Foundation

Implemented scope:

- Added metadata-only `AgencyFeatureBundleAssignment`, `AgencyFeatureBundleAssignmentCreate`, and `AgencyFeatureBundleAssignmentHistory` records.
- Added `agency_feature_bundle_assignments` and `agency_feature_bundle_assignment_history` collection/index registrations.
- Added platform metadata CRUD APIs and `/platform/feature-bundle-assignments` for agency bundle assignment review.
- Added agency read-only APIs and `/agency/assigned-bundles` for Assigned Bundles visibility.
- Added readiness flags under `feature_bundle_assignment_foundation`.
- Added `docs/architecture/feature-bundle-assignment-foundation.md`.

Avoid adding:

- Runtime feature enforcement, feature activation, entitlement evaluation, entitlement enforcement, billing, payments, Stripe, licensing, permission changes, provider/GDS execution, booking, reservation creation, PNR mutation, ticketing, EMD issuance, CMS publishing, client portal publishing, scraping, external APIs, external AI, background workers, cron jobs, email/SMS/notification sending, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 40.1: Capability Catalog Foundation

Implemented scope:

- Added metadata-only `CapabilityCatalogEntry` records.
- Added `capability_catalog` collection/index registration.
- Added read-only platform APIs and `/platform/capabilities` for capability catalog review.
- Added read-only agency APIs and `/agency/capabilities` for informational capability visibility.
- Added category/module listing metadata for catalog filters.
- Added readiness flags under `capability_catalog_foundation`.
- Added `docs/architecture/capability-catalog-foundation.md`.

Avoid adding:

- Runtime feature enforcement, entitlement checks or evaluation, billing, payments, subscriptions charging, feature activation, route blocking, permission decisions, provider/GDS execution, booking, reservation creation, PNR mutation, ticketing, EMD issuance, CMS publishing, client portal publishing, scraping, external APIs, external services, external AI, background workers, cron jobs, email/SMS/notification sending, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 40.1: Feature Bundle Rollout Readiness Foundation

Implemented scope:

- Added metadata-only `FeatureBundleRolloutReadiness` and `FeatureBundleRolloutChecklistItem` records.
- Added `agency_feature_bundle_rollout_readiness` collection/index registration.
- Added platform review APIs and `/platform/feature-bundle-rollout-readiness` for assigned-bundle readiness metadata.
- Added agency read-only APIs and `/agency/bundle-rollout-readiness` for Bundle Rollout Readiness summaries.
- Added default readiness views generated from Phase 40.0 assignment metadata.
- Added readiness flags under `feature_bundle_rollout_readiness_foundation`.
- Added `docs/architecture/feature-bundle-rollout-readiness-foundation.md`.

Avoid adding:

- Feature activation, feature deactivation, runtime access enforcement, route blocking, permission changes, entitlement evaluation/enforcement, billing, payments, Stripe, licensing, provider/GDS execution, booking, reservation creation, PNR mutation, ticketing, EMD issuance, CMS/client portal publishing, scraping, external APIs, external AI, background workers, cron jobs, email/SMS/notification sending, rollout execution, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 40.2: Feature Bundle Rollout Plan Foundation

Implemented scope:

- Added metadata-only `FeatureBundleRolloutPlan` records.
- Added `agency_feature_bundle_rollout_plans` collection/index registration.
- Added platform list/create/update/read APIs and `/platform/feature-bundle-rollout-plans` for rollout plan metadata.
- Added agency read-only list/read APIs and `/agency/rollout-plans` for rollout plan summaries.
- Added rollout stages `draft`, `readiness_review`, `scheduled`, `paused`, and `archived`.
- Added readiness snapshot references, assigned bundle references, target windows, owner metadata, notes, and checklist summaries.
- Added readiness flags under `feature_bundle_rollout_plan_foundation`.
- Added `docs/architecture/feature-bundle-rollout-plan-foundation.md`.

Avoid adding:

- Feature activation, feature deactivation, rollout execution, runtime access enforcement, route blocking, permission changes, entitlement evaluation/enforcement, billing, payments, Stripe, licensing, provider/GDS execution, booking, reservation creation, PNR mutation, ticketing, EMD issuance, CMS/client portal publishing, scraping, external APIs, external AI or AI execution, background workers, cron jobs, email/SMS/notification sending, publishing, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 40.3: Agency Capability Rollout Dashboard Foundation

Implemented scope:

- Added read-only `RolloutDashboardSummary`, `RolloutDashboardSection`, `RolloutDashboardCounts`, `RolloutDashboardSnapshot`, and `RolloutDashboardFilters` metadata models.
- Added `rollout_dashboard_views` and `rollout_dashboard_snapshots` collection/index registration.
- Added platform read-only APIs and `/platform/rollout-dashboard` for unified rollout metadata visibility.
- Added agency read-only APIs and `/agency/rollout-dashboard` scoped to the selected agency.
- Added dashboard cards for Capability Catalog, Feature Flags, Feature Bundles, Assigned Bundles, Rollout Readiness, and Rollout Plans.
- Added summary, filters, and snapshot response shapes.
- Added readiness flags under `rollout_dashboard_foundation`.
- Added `docs/architecture/rollout-dashboard-foundation.md`.

Avoid adding:

- Real entitlement enforcement, billing, payment processing, execution engines, provider execution, AI execution, publishing, rollout automation, background workers, schedulers, email/SMS sending, feature activation, permission enforcement, route blocking, webhook execution, scraping, external API calls, state transitions, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 40.4: Feature Bundle Rollout Approval Foundation

Implemented scope:

- Added metadata-only `FeatureBundleRolloutApproval`, `FeatureBundleRolloutApprovalSummary`, `FeatureBundleRolloutApprovalNote`, and `FeatureBundleRolloutApprovalTimelineEntry` models.
- Added `feature_bundle_rollout_approvals` and `feature_bundle_rollout_approval_notes` collection/index registration.
- Added platform list/create/update/read APIs and `/platform/feature-bundle-rollout-approvals` for rollout approval metadata.
- Added platform approval note and timeline metadata views.
- Added agency read-only APIs and `/agency/rollout-approval` scoped to the selected agency.
- Added approval statuses `draft`, `submitted`, `under_review`, `approved`, `rejected`, and `archived`.
- Added readiness flags under `feature_bundle_rollout_approval_foundation`.
- Added `docs/architecture/feature-bundle-rollout-approval-foundation.md`.

Avoid adding:

- Actual feature enablement, permission enforcement, runtime gating, billing, Stripe, payment providers, authentication changes, deployment automation, cron jobs, webhooks, background workers, email, SMS, notifications, AI, OpenAI, scraping, publishing, rollout execution, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 40.5: Feature Bundle Rollout Schedule Foundation

Implemented scope:

- Added metadata-only `FeatureBundleRolloutSchedule` model and create/update payload models.
- Added `feature_bundle_rollout_schedules` collection/index registration.
- Added platform list/create/update/read APIs and `/platform/feature-bundle-rollout-schedule` for intended rollout timing metadata.
- Added agency read-only APIs and `/agency/rollout-schedule` scoped to the selected agency.
- Added schedule statuses `Planned`, `Ready`, `AwaitingApproval`, `Approved`, `Deferred`, `Cancelled`, and `CompletedMetadata`.
- Added readiness flags under `feature_bundle_rollout_schedule_foundation`.
- Added `docs/architecture/feature-bundle-rollout-schedule-foundation.md`.

Avoid adding:

- Actual rollout execution, feature activation, entitlement behavior changes, permission changes, cron jobs, schedulers, workers, queues, timers, background execution, external API calls, AI functionality, billing logic, automatic publishing, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 40.6: Feature Bundle Rollout Timeline Foundation

Implemented scope:

- Added metadata-only `FeatureBundleRolloutTimelineEntry`, `FeatureBundleRolloutActor`, and `FeatureBundleRolloutEventType` models.
- Added `feature_bundle_rollout_timeline_entries` collection/index registration.
- Added platform create/list/read APIs and `/platform/feature-bundle-rollout-timeline` for historical rollout event metadata.
- Added agency read-only APIs and `/agency/rollout-timeline` scoped to the selected agency.
- Added filters by rollout plan, agency, bundle, event type, and date range with newest-first timeline ordering.
- Added readiness flags under `feature_bundle_rollout_timeline_foundation`.
- Added `docs/architecture/feature-bundle-rollout-timeline-foundation.md`.

Avoid adding:

- Feature bundle enablement, agency permission changes, rollout plan execution, background jobs, scheduled jobs, publishing, provider calls, email sending, notification sending, rollout state enforcement, subscription modification, automation, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 40.7: Feature Bundle Rollout Dependency Foundation

Implemented scope:

- Added metadata-only `FeatureBundleDependency`, `FeatureBundleDependencyReference`, and `FeatureBundleDependencyType` models.
- Added `feature_bundle_dependencies` collection/index registration.
- Added platform create/update/delete/read/list APIs and `/platform/feature-bundle-dependencies` for dependency metadata.
- Added agency read-only APIs and `/agency/bundle-dependencies` scoped to the selected agency.
- Added filters by bundle, rollout plan, agency, and dependency type.
- Added readiness flags under `feature_bundle_dependency_foundation`.
- Added `docs/architecture/feature-bundle-dependency-foundation.md`.

Avoid adding:

- Rollout plan execution, background jobs, dependency enforcement, rollout blocking, feature bundle activation, permission modification, notifications, publishing, provider calls, automation, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 40.8: Feature Bundle Rollout Risk Register Foundation

Implemented scope:

- Added metadata-only `FeatureBundleRolloutRisk`, `FeatureBundleRolloutRiskImpact`, `FeatureBundleRolloutRiskLikelihood`, and `FeatureBundleRolloutRiskStatus` models.
- Added `feature_bundle_rollout_risks` collection/index registration.
- Added platform create/update/delete/read/list APIs and `/platform/feature-bundle-rollout-risks` for risk register metadata.
- Added agency read-only APIs and `/agency/rollout-risks` scoped to the selected agency.
- Added filters by agency, bundle, rollout plan, status, impact, and likelihood.
- Added readiness flags under `feature_bundle_rollout_risk_register_foundation`.
- Added `docs/architecture/feature-bundle-rollout-risk-register-foundation.md`.

Avoid adding:

- Rollout execution, risk decision enforcement, rollout blocking, notifications, feature bundle activation, automation, external provider calls, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 40.9: Feature Bundle Rollout Issue Log Foundation

Implemented scope:

- Added metadata-only `FeatureBundleRolloutIssue`, `FeatureBundleRolloutIssueSeverity`, and `FeatureBundleRolloutIssueStatus` models.
- Added `feature_bundle_rollout_issues` collection/index registration.
- Added platform create/update/delete/read/list APIs and `/platform/feature-bundle-rollout-issues` for issue log metadata.
- Added agency read-only APIs and `/agency/rollout-issues` scoped to the selected agency.
- Added filters by agency, bundle, rollout plan, risk, dependency, approval, severity, and status.
- Added readiness flags under `feature_bundle_rollout_issue_log_foundation`.
- Added `docs/architecture/feature-bundle-rollout-issue-log-foundation.md`.

Avoid adding:

- Rollout execution, feature bundle activation, blocking enforcement, notifications, external provider calls, AI/provider execution, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 40.10: Feature Bundle Rollout Decision Register Foundation

Implemented scope:

- Added metadata-only `FeatureBundleRolloutDecision`, `FeatureBundleRolloutDecisionCategory`, and `FeatureBundleRolloutDecisionStatus` models.
- Added `feature_bundle_rollout_decisions` collection/index registration.
- Added platform create/update/delete/read/list APIs and `/platform/feature-bundle-rollout-decisions` for decision register metadata.
- Added agency read-only APIs and `/agency/rollout-decisions` scoped through rollout plan agency visibility.
- Added filters by rollout, category, owner, and status plus related bundle, dependency, risk, issue, and timeline references.
- Added readiness flags under `feature_bundle_rollout_decision_register_foundation`.
- Added `docs/architecture/feature-bundle-rollout-decision-register-foundation.md`.

Avoid adding:

- Rollout execution, deployment automation, feature activation, entitlement enforcement, billing, provider integrations, AI, external APIs, background workers, schedulers, notifications, email, webhooks, publishing, runtime switching, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 40.11: Feature Bundle Rollout Change Request Foundation

Implemented scope:

- Added metadata-only `FeatureBundleRolloutChangeRequest`, type, priority, impact, and status models.
- Added `feature_bundle_rollout_change_requests` collection/index registration.
- Added platform create/update/delete/read/list APIs and `/platform/feature-bundle-rollout-change-requests` for change request metadata.
- Added agency read-only APIs and `/agency/rollout-change-requests` scoped through rollout plan agency visibility.
- Added filters by rollout, status, priority, impact level, and change type plus affected bundle/feature flag and related decision/risk/issue/dependency references.
- Added readiness flags under `feature_bundle_rollout_change_request_foundation`.
- Added `docs/architecture/feature-bundle-rollout-change-request-foundation.md`.

Avoid adding:

- Rollout execution, deployment automation, feature activation, entitlement enforcement, billing, provider integrations, AI, external APIs, background workers, schedulers, notifications, email, webhooks, publishing, runtime switching, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 40.12: Feature Bundle Rollout Rollback Plan Foundation

Implemented scope:

- Added metadata-only `FeatureBundleRolloutRollbackPlan`, trigger, scope, status, and priority models.
- Added `feature_bundle_rollout_rollback_plans` collection/index registration.
- Added platform create/update/delete/read/list APIs and `/platform/feature-bundle-rollout-rollback-plans` for rollback plan metadata.
- Added agency read-only APIs and `/agency/rollout-rollback-plans` scoped through rollout plan agency visibility.
- Added filters by rollout, status, priority, scope, and owner plus affected bundle/feature flag and related change request/decision/risk/issue/dependency references.
- Added rollback steps and validation notes as metadata-only fields.
- Added readiness flags under `feature_bundle_rollout_rollback_plan_foundation`.
- Added `docs/architecture/feature-bundle-rollout-rollback-plan-foundation.md`.

Avoid adding:

- Actual rollback execution, deployment automation, feature activation/deactivation, entitlement enforcement, billing, provider integrations, AI, external APIs, background workers, schedulers, notifications, email, webhooks, publishing, runtime switching, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 40.13: Feature Bundle Rollout Summary Pack Foundation

Implemented scope:

- Added metadata-only `FeatureBundleRolloutSummaryPack`, status, and audience models.
- Added `feature_bundle_rollout_summary_packs` collection/index registration.
- Added platform create/update/delete/read/list APIs and `/platform/feature-bundle-rollout-summary-packs` for summary evidence-pack metadata.
- Added agency read-only APIs and `/agency/rollout-summary-packs` scoped through rollout plan agency visibility.
- Added filters by rollout, status, audience, and bundle plus covered bundle/readiness/approval/schedule/timeline/dependency/risk/issue/decision/change request/rollback plan references.
- Added evidence notes and compliance notes as metadata-only fields.
- Added readiness flags under `feature_bundle_rollout_summary_pack_foundation`.
- Added `docs/architecture/feature-bundle-rollout-summary-pack-foundation.md`.

Avoid adding:

- Rollout execution, deployment automation, feature activation/deactivation, entitlement enforcement, billing, provider integrations, AI, external APIs, background workers, schedulers, notifications, email, webhooks, publishing, runtime switching, PDF generation, file export, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 41.0: Operational Travel Workspace Foundation

Implemented scope:

- Added metadata-only `OperationalTravelWorkspace`, type, status, and priority models.
- Added `operational_travel_workspaces` collection/index registration.
- Added platform metadata create/update/archive/read/list APIs and `/platform/operational-travel-workspaces`.
- Added agency read-only APIs and `/agency/travel-workspaces`.
- Added filters by agency, status, type, priority, assigned agent, and travel date.
- Added client/passenger summaries, linked request/trip/offer/booking/ticket/document references, assigned team, assigned agent, travel dates, origin/destination summaries, service summary, and operational notes as metadata-only fields.
- Added readiness flags under `operational_travel_workspace_foundation`.
- Added `docs/architecture/operational-travel-workspace-foundation.md`.

Avoid adding:

- Booking execution, ticket issuance, live GDS or NDC connectivity, payment processing, email or SMS sending, AI automation, external APIs, supplier integrations, live airline calls, background workers, automation, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 41.1: Travel Request Workspace Foundation

Implemented scope:

- Added metadata-only `TravelRequestWorkspace`, type, status, and priority models.
- Added `travel_request_workspaces` collection/index registration.
- Added platform metadata create/update/archive/read/list APIs and `/platform/travel-request-workspaces`.
- Added agency read-only APIs and `/agency/travel-requests`.
- Added filters by agency, status, type, priority, assigned agent, departure date, and operational workspace.
- Added requester details, client/passenger summaries, requested route, requested dates, passenger summary, requested services, flexibility notes, special service notes, budget notes, deadline, linked trip/offer/document references, assigned agent, and internal notes as metadata-only fields.
- Added readiness flags under `travel_request_workspace_foundation`.
- Added `docs/architecture/travel-request-workspace-foundation.md`.

Avoid adding:

- Booking execution, ticket issuance, live GDS or NDC connectivity, payment processing, email or SMS sending, AI automation, external APIs, supplier integrations, live airline calls, background workers, automatic conversion to trips, automatic offer creation, automation, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 41.2: Passenger Workspace Foundation

Implemented scope:

- Added metadata-only `PassengerWorkspace` and status models.
- Added `passenger_workspaces` collection/index registration.
- Added platform metadata create/update/archive/read/list APIs and `/platform/passenger-workspaces`.
- Added agency read-only APIs and `/agency/passenger-workspaces`.
- Added filters by agency, status, nationality, citizenship, assistance profile, travel date, and assigned operational workspace.
- Added passenger reference, personal information, travel document, loyalty, known traveler, emergency contact, mobility, medical, dietary, assistance, baggage, seating, language, contact, linked request/trip/offer/booking/ticket/document, and internal note metadata fields.
- Added readiness flags under `passenger_workspace_foundation`.
- Added `docs/architecture/passenger-workspace-foundation.md`.

Avoid adding:

- Booking execution, ticket issuance, GDS connectivity, NDC connectivity, payment processing, supplier integrations, AI, email, SMS, background workers, external APIs, automatic profile matching, automatic document validation, airline communication, automation, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 41.3: Flight Workspace Foundation

Implemented scope:

- Added metadata-only `FlightWorkspace` and status models.
- Added `flight_workspaces` collection/index registration.
- Added platform metadata create/update/archive/read/list APIs and `/platform/flight-workspaces`.
- Added agency read-only APIs and `/agency/flight-workspaces`.
- Added filters by agency, status, airline, departure airport, arrival airport, departure date, cabin, booking class, and assigned operational workspace.
- Added flight reference, airline, marketing carrier, operating carrier, flight number, departure, arrival, terminal, schedule, aircraft, cabin, booking class, fare family, baggage, connection, stopover, elapsed travel time, operating day, passenger, linked request/trip/offer/booking/ticket/document, and operational note metadata fields.
- Added readiness flags under `flight_workspace_foundation`.
- Added `docs/architecture/flight-workspace-foundation.md`.

Avoid adding:

- Booking execution, live flight search, GDS connectivity, NDC connectivity, airline APIs, payment, ticket issuance, schedule synchronization, external APIs, AI, background workers, automatic route generation, flight validation, airline lookups, live schedule updates, automation, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 41.4: Trip Workspace Foundation

Implemented scope:

- Added metadata-only `TripWorkspace` and status models.
- Added `trip_workspaces` collection/index registration.
- Added platform metadata create/update/archive/read/list APIs and `/platform/trip-workspaces`.
- Added agency read-only APIs and `/agency/trip-workspaces`.
- Added filters by agency, status, departure country, destination country, departure date, assigned agent, priority, and assigned operational workspace.
- Added trip reference, journey type, service type, client, passenger summary, flight summary, linked request/offer/booking/ticket/EMD/document references, route, travel dates, itinerary summary, baggage summary, service summary, assigned agent/team, and operational note metadata fields.
- Added readiness flags under `trip_workspace_foundation`.
- Added `docs/architecture/trip-workspace-foundation.md`.

Avoid adding:

- Booking execution, ticket issuance, GDS connectivity, NDC connectivity, airline APIs, payment processing, invoicing, AI, background workers, automatic trip generation, automatic itinerary generation, external integrations, automation, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 41.5: Offer Workspace Foundation

Implemented scope:

- Added metadata-only `OfferWorkspaceV2` and status models.
- Added `offer_workspaces_v2` collection/index registration.
- Added platform metadata create/update/archive/read/list APIs and `/platform/offer-workspaces`.
- Added agency read-only APIs under `/api/agencies/{agency_id}/offer-workspaces-v2` and UI at `/agency/offer-workspaces`.
- Added filters by agency, status, validity, client, destination, price range, assigned agent, and assigned trip workspace.
- Added offer reference, status, type, client, passenger summary, flight summary, trip summary, pricing summary, taxes, fees, ancillary, baggage, seat, meal, hotel, transfer, insurance, validity, linked booking/ticket/document, agent note, customer note, and internal note metadata fields.
- Added readiness flags under `offer_workspace_foundation`.
- Added `docs/architecture/offer-workspace-foundation.md`.

Avoid adding:

- Booking execution, ticket issuance, payment processing, GDS connectivity, NDC connectivity, airline APIs, fare calculation engines, AI itinerary generation, supplier integrations, external APIs, automatic booking conversion, background workers, automation, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 41.6: Booking Workspace Foundation

Implemented scope:

- Extended the metadata-only `BookingWorkspace` model with booking reference, status, owner, airline PNR, GDS locator, supplier, linked passenger/flight/ticket/EMD/SSR/OSI/document/timeline/communication, payment summary, booking summary, and operational note fields.
- Extended `booking_workspaces` collection/index registration without destructively changing existing booking mirror data.
- Added platform metadata create/update/archive/read/list APIs and `/platform/booking-workspaces`.
- Added agency read-only metadata APIs at `/api/agencies/{agency_id}/booking-workspaces` and UI at `/agency/booking-workspaces`.
- Added filters by agency, booking status, booking owner, airline, supplier, and booking date.
- Added readiness flags under `booking_workspace_foundation`.
- Added `docs/architecture/booking-workspace-foundation.md`.

Avoid adding:

- Live booking creation, ticket issuance, GDS connectivity, NDC connectivity, airline APIs, payment processing, fare calculation, AI, background workers, automatic booking confirmation, automatic ticket generation, external integrations, automation, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 41.7: Ticket Workspace Foundation

Implemented scope:

- Added metadata-only `TicketWorkspace`, `TicketWorkspaceCreate`, `TicketWorkspaceUpdate`, `TicketWorkspaceStatus`, `TicketDocumentStatus`, `TicketWorkspaceCouponStatus`, `TicketWorkspaceCouponDetail`, `TicketWorkspacePricingUnit`, and `TicketWorkspaceFareComponent` models with ticket references, workspace status/type, whole-ticket document status, ticket number, validating carrier, issuing metadata, issue date, passenger, flight links, booking reference, airline PNR, GDS locator, fare basis summaries, fare calculation line/NUC/ROE metadata, equivalent fare paid metadata, form of payment, payment restrictions, commission summary, tax breakdown, pricing units, fare components, coupon status summary, coupon detail metadata with coupon-level fare basis, baggage, endorsement, restriction, exchange/refund/void reference ids, EMD/document links, lifecycle notes, and operational notes.
- Registered the additive `ticket_workspaces` collection and lookup indexes without destructive migrations.
- Added platform metadata create/update/archive/read/list APIs and `/platform/ticket-workspaces`.
- Added agency read-only metadata APIs at `/api/agencies/{agency_id}/ticket-workspaces` and UI at `/agency/ticket-workspaces`.
- Added filters by agency, ticket workspace status, ticket document status, validating carrier, issue date, passenger, booking reference, and currency.
- Added readiness flags under `ticket_workspace_foundation`.
- Added `docs/architecture/ticket-workspace-foundation.md`.

Avoid adding:

- Ticket issuance, ticket reissue, voiding, refunds, exchanges, payment processing, GDS connectivity, NDC connectivity, airline APIs, fare calculation, fare recalculation, automated ticket validation, coupon validation, background workers, external integrations, automation, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 41.8: EMD Workspace Foundation

Implemented scope:

- Added metadata-only `EmdWorkspace`, `EmdWorkspaceCreate`, `EmdWorkspaceUpdate`, `EmdWorkspaceStatus`, `EmdWorkspaceDocumentStatus`, `EmdWorkspaceCouponStatus`, and `EmdWorkspaceCouponDetail` models with EMD references, workspace status, whole-document status, EMD number, EMD-A/EMD-S metadata, validating carrier, issuing metadata, passenger, booking reference, airline PNR, GDS locator, associated ticket/coupon and flight links, SSR/OSI links, ancillary service links, RFIC/RFISC metadata, service metadata, coupon details, fare/tax/payment metadata, exchange/refund/void references, documents, lifecycle notes, and operational notes.
- Registered the additive `emd_workspaces` collection and lookup indexes without destructive migrations or duplicate EMD architecture.
- Added platform metadata create/update/archive/read/list APIs and `/platform/emd-workspaces`.
- Added agency read-only metadata APIs at `/api/agencies/{agency_id}/emd-workspaces` and UI at `/agency/emd-workspaces`.
- Added filters by agency, EMD status, EMD type, EMD-A/EMD-S, validating carrier, passenger, RFIC, RFISC, service category, and issue date.
- Added readiness flags under `emd_workspace_foundation`.
- Added `docs/architecture/emd-workspace-foundation.md`.

Avoid adding:

- EMD issuance, EMD exchange, EMD refund, EMD voiding, live GDS/NDC connectivity, airline APIs, payment processing, RFIC/RFISC validation engines, SSR/OSI transmission, background workers, external integrations, automation, parallel duplicate EMD architecture, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 41.9: SSR / OSI Operational Workspace Foundation

Implemented scope:

- Added metadata-only `SsrOsiWorkspace`, `SsrOsiWorkspaceCreate`, `SsrOsiWorkspaceUpdate`, `SsrOsiNeedCategory`, `SsrOsiReadinessStatus`, `SsrOsiApprovalStatus`, and `SsrOsiOperationalStatus` models with passenger need, service classification, SSR/OSI handling, airline handling, airport handling, approval metadata, EMD/RFIC/RFISC references, documents, MEDIF, tasks, timelines, communications, readiness, missing requirements, unresolved items, relationships, and notes.
- Registered the additive `ssr_osi_workspaces` collection and lookup indexes without destructive migrations.
- Added platform metadata create/update/archive/read/list APIs and `/platform/ssr-osi-workspaces`.
- Added agency read-only metadata APIs at `/api/agencies/{agency_id}/ssr-osi-workspaces` and UI at `/agency/passenger-services`.
- Added filters by need category, airline, approval status, readiness, passenger, priority, RFIC, and RFISC.
- Added readiness flags under `ssr_osi_operational_workspace_foundation`.
- Documented SSR / OSI workspaces as the operational input path for future AOIE: Passenger Need -> SSR / OSI Workspace -> Airline Knowledge -> Capability Matrix -> Operational Feasibility -> Offer Builder.
- Added `docs/architecture/ssr-osi-operational-workspace-foundation.md`.

Avoid adding:

- Live SSR transmission, live OSI transmission, GDS connectivity, NDC connectivity, airline APIs, AI recommendation, automatic airline approval, automatic EMD issuance, background workers, provider integrations, external API calls, automation, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 42.0: Document Workspace Foundation

Implemented scope:

- Added metadata-only `DocumentWorkspace`, `DocumentWorkspaceCreate`, `DocumentWorkspaceUpdate`, `DocumentWorkspaceStatus`, and `DocumentWorkspaceType` models with passenger/request/trip/booking/ticket/EMD/SSR-OSI links, operational intelligence references, document reference, status, type, category, title, description, passenger, booking, PNR, related service, ticket, EMD, SSR, travel/airline/airport/authority requirement flags, deadline, received and verification statuses, validity, issuing authority, file/storage metadata, package/render/share references, visibility flags, missing/rejection reasons, and operational notes.
- Registered the additive `document_workspaces` collection and lookup indexes without destructive migrations.
- Added platform metadata create/update/archive/read/list APIs and `/platform/document-workspaces`.
- Added agency read-only metadata APIs at `/api/agencies/{agency_id}/document-workspaces` and UI at `/agency/document-workspaces`.
- Added filters by document type, document status, passenger, booking reference, related service, required-for-travel, verification status, and deadline.
- Added readiness flags under `document_workspace_foundation`.
- Clarified that Phase 42.0 is the operational document workspace layer and does not duplicate the Phase 36.5 document render/package/share foundation.
- Added `docs/architecture/document-workspace-foundation.md`.

Avoid adding:

- Live document delivery, e-signature, public share links, automatic PDF generation, payment/invoice generation, external storage integrations, background workers, AI document generation, automation, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 42.1: Operational Timeline Workspace Foundation

Implemented scope:

- Added metadata-only `OperationalTimeline`, `OperationalTimelineCreate`, and `OperationalTimelineUpdate` models with agency ownership, timeline reference, creator metadata, passenger/request/trip/booking/ticket/EMD/SSR-OSI/document workspace links, event metadata, operational stage/result, airline/airport context, communication summary fields, approval metadata, due/completed dates, reminder metadata, visibility flags, attachment references, and operational notes.
- Registered the additive `operational_timelines` collection and lookup indexes without destructive migrations.
- Added platform metadata create/update/archive/read/list APIs under `/api/platform/operational-timelines` and UI at `/platform/operational-timelines`.
- Added agency read-only APIs under `/api/agencies/{agency_id}/operational-timelines` and UI at `/agency/timeline`.
- Added filters by passenger, booking, ticket, EMD, SSR / OSI, airline, communication type, event type, priority, status, and date.
- Added chronological ordering and readiness flags under `operational_timeline_workspace_foundation`.
- Added `docs/architecture/operational-timeline-workspace-foundation.md`.

Avoid adding:

- Email sending, SMS sending, WhatsApp, Teams, Slack, live airline messaging, live customer messaging, AI summarization, background workers, provider integrations, automation, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 42.2: Passenger Service Workflow Engine Foundation

Implemented scope:

- Added metadata-only `PassengerServiceWorkflow`, `PassengerServiceWorkflowCreate`, and `PassengerServiceWorkflowUpdate` models with agency ownership, workflow reference/status/type/version, passenger/request/trip/booking/ticket/EMD/SSR-OSI/document/timeline workspace links, current/previous/next stage metadata, readiness state, blocking and completed requirements, responsible team/agent, airline and priority filter metadata, timeline dates, future AOIE recommendation-pack reference, and operational notes.
- Registered the additive `passenger_service_workflows` collection and lookup indexes without destructive migrations.
- Added platform metadata create/update/archive/read/list APIs under `/api/platform/passenger-service-workflows` and UI at `/platform/passenger-service-workflows`.
- Added agency read-only APIs under `/api/agencies/{agency_id}/passenger-service-workflows` and UI at `/agency/workflow-engine`.
- Added filters by workflow stage, readiness, passenger, airline, priority, and assigned agent.
- Added workflow stage definitions, readiness states, linked-workspace counters, and readiness flags under `passenger_service_workflow_engine_foundation`.
- Documented the orchestration chain: Passenger -> Service Requirement -> Operational Workspaces -> Timeline -> Future AOIE -> Operational Execution.
- Added `docs/architecture/passenger-service-workflow-engine-foundation.md`.

Avoid adding:

- Automatic workflow execution, AI decision making, background workers, airline APIs, GDS connectivity, NDC connectivity, automatic approvals, automatic ticketing, automatic EMD issuance, automatic messaging, provider integrations, automation, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 50.0: Airline Operational Intelligence Engine Architecture Foundation

Implemented scope:

- Added architecture-only `AirlineOperationalIntelligenceArchitecture` metadata and the `airline_operational_intelligence_architecture` collection with additive index registration.
- Added `AirlineOperationalIntelligenceService` with a deterministic seed record for `phase_50_0_airline_operational_intelligence_engine_architecture_foundation`.
- Added read-only platform APIs under `/api/platform/airline-operational-intelligence` and agency APIs under `/api/agencies/{agency_id}/airline-operational-intelligence`.
- Added Platform Console `/platform/airline-operational-intelligence` and Agency Workspace `/agency/operational-intelligence` pages.
- Documented AOIE as the Chapter 50 intelligence track that feeds Chapter 41/42 operational workspaces without replacing them.
- Set next intelligence phase to Phase 50.6 Operational Knowledge Evaluation Engine Foundation after Phase 50.5 and next operational phase to Phase 42.2 Passenger Service Workflow Engine Foundation.

Avoid adding:

- AI generation, airline scraping, automatic web crawling, live airline APIs, provider integrations, pricing engine execution, itinerary search, booking execution, ticket issuance, EMD issuance, recommendation automation, background workers, automation, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 50.1: Airline Knowledge Acquisition Workspace Foundation

Implemented scope:

- Added metadata-only `AirlineKnowledgeAcquisition`, `AirlineKnowledgeAcquisitionCreate`, and `AirlineKnowledgeAcquisitionUpdate` models for manually entered trusted airline policy/source evidence.
- Refined those models into the Airline Operational Knowledge Graph foundation with independent Evidence, Policy, Pricing, Capability, and Operational Constraints & Procedures pillars.
- Added structured animal transport, extra-seat, and cabin capability metadata so capability, policy, pricing, and constraints stay separate.
- Registered the additive `airline_knowledge_acquisitions` collection and lookup indexes without destructive migrations.
- Added platform metadata create/update/archive/read/list APIs under `/api/platform/airline-knowledge-acquisition` and UI at `/platform/airline-knowledge-acquisition`.
- Added agency read-only APIs under `/api/agencies/{agency_id}/airline-knowledge-acquisition` and UI at `/agency/knowledge-acquisition`.
- Added filters by airline, service domain, service family, SSR code, RFIC, RFISC, source type, review status, approval status, effective date, and official source flag.
- Linked acquisition evidence and operational knowledge graph metadata to Phase 50.2 Operational Constraint Engine, Phase 50.3 Airline Operational Knowledge Normalisation, Phase 50.4 Airline Operational Knowledge Governance, Phase 50.5 Airline Operational Capability Matrix, Phase 50.6 Operational Knowledge Evaluation Engine, Phase 50.7 Passenger Service Feasibility Engine, and future AOIE phases: 50.8 Airline & Itinerary Recommendation Engine and 50.9 Offer Builder Intelligence Integration.
- Added readiness flags under `airline_knowledge_acquisition_workspace_foundation`.
- Added `docs/architecture/airline-knowledge-acquisition-workspace-foundation.md`.

Avoid adding:

- AI parsing, automatic extraction, web scraping, web crawling, airline website automation, provider integrations, live airline APIs, recommendation engines, feasibility engines, pricing calculation engines, background workers, parser execution, automation, `/agent` or `/admin` routes, Supabase/Next/Horizons/Base44/Fusion code, or destructive Mongo index migration.

### Phase 50.2: Operational Constraint Engine Foundation

Implemented scope:

- Added metadata-only `OperationalConstraint`, `OperationalConstraintCreate`, `OperationalConstraintUpdate`, `OperationalConstraintCondition`, and `OperationalConstraintConditionGroup` models for the formal AOIE constraint language.
- Registered the additive `operational_constraints` collection and lookup indexes without destructive migrations.
- Added platform metadata create/update/archive/read/list APIs under `/api/platform/operational-constraints` and UI at `/platform/operational-constraints`.
- Added agency read-only APIs under `/api/agencies/{agency_id}/operational-constraints` and UI at `/agency/operational-constraints`.
- Added metadata sections for Constraint Overview, Knowledge Link, Conditions, Outcomes, Applicability, Priority / Precedence, Governance, Future Evaluation, and Operational Links.
- Added readiness flags under `operational_constraint_engine_foundation`.
- Added `docs/architecture/operational-constraint-engine-foundation.md`.

Avoid adding:

- Live rule execution, AI reasoning, recommendation engines, feasibility scoring, pricing calculation, parser execution, scraping, background workers, provider integrations, evaluation endpoints, automation, `/agent` or `/admin` routes, or destructive Mongo index migration.

### Phase 50.3: Airline Operational Knowledge Normalisation Foundation

Implemented scope:

- Added metadata-only `AirlineKnowledgeNormalisation`, `AirlineKnowledgeNormalisationCreate`, and `AirlineKnowledgeNormalisationUpdate` models for canonical AOIE vocabulary.
- Registered the additive `airline_knowledge_normalisations` collection and lookup indexes without destructive migrations.
- Added platform metadata create/update/archive/read/list APIs under `/api/platform/airline-knowledge-normalisation` and UI at `/platform/airline-knowledge-normalisation`.
- Added agency read-only APIs under `/api/agencies/{agency_id}/airline-knowledge-normalisation` and UI at `/agency/knowledge-normalisation`.
- Added metadata sections for Canonical Record, Taxonomy Hierarchy, Aliases / Terms, Applicability, Animal Taxonomy, Aircraft / Cabin Taxonomy, Service Taxonomy, Units, Knowledge Links, and Governance.
- Added readiness flags under `airline_knowledge_normalisation_foundation`.
- Added `docs/architecture/airline-knowledge-normalisation-foundation.md`.

Avoid adding:

- Live evaluation, AI parsing, recommendation engines, feasibility scoring, pricing calculation, scraping, background workers, provider integrations, external API calls, automation, `/agent` or `/admin` routes, or destructive Mongo index migration.

### Phase 50.4: Airline Operational Knowledge Governance & Version Control Foundation

Implemented scope:

- Added metadata-only `AirlineKnowledgeVersion`, `AirlineKnowledgeVersionCreate`, and `AirlineKnowledgeVersionUpdate` models for independent Evidence, Policy, Pricing, Capability, Operational Constraint, and Operational Procedure version metadata.
- Added metadata-only `AirlineKnowledgeRelease`, `AirlineKnowledgeReleaseCreate`, and `AirlineKnowledgeReleaseUpdate` models for grouped knowledge release metadata.
- Registered additive `airline_knowledge_versions` and `airline_knowledge_releases` collections and lookup indexes without destructive migrations.
- Added platform metadata create/update/archive/read/list APIs under `/api/platform/airline-knowledge-governance` and UI routes at `/platform/airline-knowledge-governance` and `/platform/airline-knowledge-releases`.
- Added agency read-only APIs under `/api/agencies/{agency_id}/airline-knowledge-governance` and UI at `/agency/knowledge-governance`.
- Added lifecycle, review queue, approval queue, publication queue, historical version, version comparison, superseded knowledge, archived knowledge, rollback, and release metadata.
- Added readiness flags under `airline_operational_knowledge_governance_foundation`.
- Added `docs/architecture/airline-operational-knowledge-governance-foundation.md`.

Avoid adding:

- Live rule evaluation, AI reasoning, parser execution, recommendation engines, pricing calculation, provider integrations, background workers, automatic publication, automation, `/agent` or `/admin` routes, or destructive Mongo index migration.

### Phase 50.5: Airline Operational Capability Matrix Foundation

Implemented scope:

- Added metadata-only `AirlineCapabilityMatrixRecord`, `AirlineCapabilityMatrixCreate`, and `AirlineCapabilityMatrixUpdate` models for the Airline Operational Capability Matrix.
- Registered the additive `airline_capability_matrix` collection and lookup indexes without destructive migrations.
- Added platform metadata create/update/archive/read/list APIs under `/api/platform/airline-capability-matrix` and UI at `/platform/airline-capability-matrix`.
- Added agency read-only APIs under `/api/agencies/{agency_id}/airline-capability-matrix` and UI at `/agency/capability-matrix`.
- Added metadata sections for Capability Overview, Airline, Service, Knowledge Governance Links, Aircraft / Cabin Capability, Airport / Station Capability, Route / Country / Season Capability, Interline / Codeshare Capability, Animal Transport Capability, Extra Seat / EXST Capability, Medical / Accessibility Capability, Operational Requirements, Risk / Confidence, Lifecycle, and Notes.
- Added filters by airline, service domain/family, SSR, RFIC, RFISC, aircraft family, cabin, airport, route, country, season, capability status, operational risk, confidence level, and effective date.
- Added readiness flags under `airline_operational_capability_matrix_foundation`.
- Added `docs/architecture/airline-operational-capability-matrix-foundation.md`.

Avoid adding:

- Live rule evaluation, passenger feasibility scoring, airline recommendation ranking, AI reasoning, parser execution, pricing calculation, provider integrations, background workers, automatic publication, scraping, automation, `/agent` or `/admin` routes, or destructive Mongo index migration.

### Phase 50.6: Operational Knowledge Evaluation Engine Foundation

Implemented scope:

- Added metadata-only `OperationalKnowledgeEvaluation`, `OperationalKnowledgeEvaluationCreate`, and `OperationalKnowledgeEvaluationUpdate` models for deterministic, evidence-backed operational evaluation records.
- Registered the additive `operational_knowledge_evaluations` collection and lookup indexes without destructive migrations.
- Added platform metadata create/update/archive/read/list APIs under `/api/platform/operational-evaluations` and UI at `/platform/operational-evaluations`.
- Added agency read-only APIs under `/api/agencies/{agency_id}/operational-evaluations` and UI at `/agency/operational-evaluations`.
- Added metadata sections for Evaluation Overview, Passenger Context, Trip Context, Airline Context, Knowledge Sources, Evaluation Scope, Capability Evaluation, Policy Evaluation, Pricing Evaluation, Constraint Evaluation, Procedure Evaluation, Required Operational Actions, Evidence Trace, Operational Risk, Lifecycle, and Notes.
- Added filters by agency, evaluation status/type, airline, passenger, travel request, trip, booking, service domain/family, SSR, capability/policy/pricing/constraint/operational result, risk, confidence, and completion status.
- Added readiness flags under `operational_knowledge_evaluation_engine_foundation`.
- Added `docs/architecture/operational-knowledge-evaluation-engine-foundation.md`.
- Clarified that evaluation determines what operationally applies. Evaluation is not recommendation, does not determine passenger feasibility, and exists as the Phase 50.7 input.

Avoid adding:

- AI reasoning, LLM prompts, flight search, itinerary recommendation, passenger feasibility scoring, booking, ticketing, provider integrations, parser execution, pricing optimisation, background workers, automation, `/agent` or `/admin` routes, or destructive Mongo index migration.

### Phase 50.7: Passenger Service Feasibility Engine Foundation

Implemented scope:

- Added metadata-only `PassengerServiceFeasibility`, `PassengerServiceFeasibilityCreate`, and `PassengerServiceFeasibilityUpdate` models for advisory passenger service feasibility records.
- Registered the additive `passenger_service_feasibilities` collection and lookup indexes without destructive migrations.
- Added platform metadata create/update/archive/read/list APIs under `/api/platform/passenger-service-feasibility` and UI at `/platform/passenger-service-feasibility`.
- Added agency read-only APIs under `/api/agencies/{agency_id}/passenger-service-feasibility` and UI at `/agency/service-feasibility`.
- Added metadata sections for Feasibility Overview, Passenger Context, Trip / Itinerary Context, Airline Context, Evaluation Links, Feasibility Result, Satisfied / Conditional / Unsatisfied / Unknown Requirements, Required Actions, Operational Risk, Evidence Trace, Confidence, Lifecycle, and Notes.
- Added filters by airline, feasibility outcome, confidence level, operational risk, passenger need category, SSR code, travel date, cabin, destination, and recommendation readiness.
- Added readiness flags under `passenger_service_feasibility_engine_foundation`.
- Added `docs/architecture/passenger-service-feasibility-engine-foundation.md`.
- Clarified that feasibility is not Boolean, not recommendation, advisory, evidence-linked, and subject to final human authority. Recommendation remains separate Phase 50.8 metadata.

Avoid adding:

- Airline recommendation ranking, flight search, booking, ticketing, live provider integrations, AI/LLM reasoning, parser execution, pricing optimisation, background workers, automatic operational decisions, automation, `/agent` or `/admin` routes, or destructive Mongo index migration.

### Phase 50.8: Airline & Itinerary Recommendation Engine Foundation

Implemented scope:

- Added metadata-only `AirlineRecommendation`, `AirlineRecommendationCreate`, and `AirlineRecommendationUpdate` models for advisory airline and itinerary recommendation records.
- Registered the additive `airline_recommendations` collection and lookup indexes without destructive migrations.
- Added platform metadata create/update/archive/read/list APIs under `/api/platform/airline-recommendations` and UI at `/platform/airline-recommendations`.
- Added agency read-only APIs under `/api/agencies/{agency_id}/airline-recommendations` and UI at `/agency/recommendations`.
- Added metadata sections for Recommendation Dashboard, Comparison Matrix, Recommendation Cards, Operational Scores, Commercial Scores, Required Actions, Evidence, Recommendation Explanation, and Comparison Table.
- Added filters by airline, recommendation level, operational score, risk, passenger need, cabin, destination, and travel date.
- Added readiness flags under `airline_recommendation_engine_foundation`.
- Added `docs/architecture/airline-recommendation-engine-foundation.md`.
- Clarified that recommendation is not feasibility, not booking, not search, advisory, and subject to final human authority.

Avoid adding:

- Live GDS search, NDC search, flight booking, ticket issuance, EMD issuance, provider APIs, parser execution, AI/LLM generation, price generation, background workers, automation, `/agent` or `/admin` routes, or destructive Mongo index migration.

### Phase 50.9: Intelligent Offer Builder Integration Foundation

Implemented scope:

- Added metadata-only `IntelligentOfferBuilderPackage`, `IntelligentOfferBuilderPackageCreate`, and `IntelligentOfferBuilderPackageUpdate` models for offer-intelligence packages.
- Registered the additive `intelligent_offer_builder_packages` collection and lookup indexes without destructive migrations.
- Added platform metadata create/update/archive/read/list APIs under `/api/platform/intelligent-offer-builder` and UI at `/platform/intelligent-offer-builder`.
- Added agency-scoped metadata create/update/archive/read/list APIs under `/api/agencies/{agency_id}/offer-intelligence` and UI at `/agency/offer-intelligence`.
- Added metadata sections for Package Overview, Passenger Context, Trip / Request Context, Offer Context, Intelligence Inputs, Recommended Options, Operational Readiness, Required Actions, Pricing / Cost References, Client Explanation, Internal Explanation, Decision Pack, Lifecycle, and Notes.
- Added filters by package status, airline, recommendation level, readiness status, operational risk, passenger need, destination, travel date, offer workspace, and client visibility status.
- Added readiness flags under `intelligent_offer_builder_integration_foundation`.
- Added `docs/architecture/intelligent-offer-builder-integration-foundation.md`.
- Clarified that Offer Builder should not invent intelligence and that recommendation, feasibility, evidence, and final authority remain separate.

Avoid adding:

- Live GDS search, NDC search, booking, ticketing, EMD issuance, provider integrations, AI/LLM generation, parser execution, background workers, automatic client sending, automation, `/agent` or `/admin` routes, or destructive Mongo index migration.

### Phase 38: Invoices And Payments

Recommended scope:

- Invoice/payment workflow hardening around existing finance tracking models.
- Payment status, reconciliation metadata, and client-visible summaries.

Avoid adding:

- Payment gateway processing unless explicitly authorized.

### Phase 39: Document Template Builder And Delivery Hardening

Recommended scope:

- Broader document template builder, versioning, governed delivery, and request/trip/document snapshot hardening on top of the Phase 36.5 document foundation.

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

## Implemented Phase 51.2

Phase 51.2 adds the metadata-only Request Intake Segment-Service Precision Foundation. It registers `request_segment_service_scopes`, platform and agency request segment service routes, read-only UI pages, module catalog entries, architecture documentation, and smoke coverage for segment-first passenger + segment + service intake metadata. It does not evaluate policy, calculate pricing, search, book, ticket, issue EMDs, call providers, generate AI/LLM output, run workers, send automatically, or convert trips automatically.

## Implemented Phase 51.3

Phase 51.3 adds the metadata-only Client & Passenger Master Workspace Consolidation Foundation. It registers `client_master_records`, `passenger_master_records`, `client_passenger_links`, `passenger_service_history`, `passenger_operational_preferences`, `passenger_known_documents`, and `client_portal_access_profiles`, plus platform and agency master workspace routes, read-only UI pages, module catalog entries, architecture documentation, and smoke coverage. Client is the commercial owner; Passenger is the reusable operational identity. The phase does not add CRM sales pipeline behavior, marketing automation, provider integrations, AI/LLM generation, booking, ticketing, payment gateway processing, background workers, or automatic client sending.
