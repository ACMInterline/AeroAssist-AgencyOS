# AeroAssist AgencyOS

Multi-tenant SaaS foundation for micro and small travel agencies.

The current build marker is `phase_59_0_product_experience_recovery`. Phase 59.0 completes the product experience recovery for Platform and Agency navigation, practical home pages, full-width workspace layouts, plain-language labels, and optional diagnostic empty states. It preserves the Phase 58 Commercial Pilot behavior, the Phase 57 release gate, every canonical route, and all execution safety boundaries. See the [Platform Information Architecture](docs/product/platform-information-architecture.md), [Agency Information Architecture](docs/product/agency-information-architecture.md), and [Navigation and Layout Standards](docs/product/navigation-and-layout-standards.md).

An immediate corrective gate now protects audit visibility and passenger identity integrity. Intake and request creation retain unconfirmed travelers as request-level placeholders; only an explicit, tenant-scoped staff confirmation may create or link a canonical `PassengerProfile`. New feature foundations are frozen until the canonical product-kernel ownership map and simplified operator UI are approved. See [P0 Security, Identity Integrity, and Product Kernel Freeze](docs/architecture/p0-security-integrity-product-kernel-freeze.md).

P1 Product Kernel Repair 2 adds an enforceable, non-runtime [Canonical Domain Ownership Map](docs/architecture/canonical-domain-ownership-map.md) and [Canonical Domain Migration Register](docs/architecture/canonical-domain-migration-register.md). The registry selects one target owner for 35 of 40 core domains, leaves five ambiguous domains explicitly `decision_required`, confirms `agency_id` as the tenant boundary, and records every known compatibility writer without migrating data or changing application behavior.

This repository currently contains the Phase 0 architecture specifications through Phase 42.2 passenger service workflow engine foundation plus Chapter 50 AOIE foundations, Phase 52.1 reference data engine foundation, Phase 52.2 knowledge import templates foundation, Phase 52.3 visual policy editor foundation, Phase 52.4 pricing formula builder foundation, Phase 52.5 operational rule composer foundation, Phase 52.6 knowledge quality assurance foundation, Phase 52.7 airline knowledge publishing foundation, Phase 52.8 operational scenario testing foundation, Phase 52.9 knowledge population toolkit foundation, and Phase 53.0 end-to-end stabilization pilot readiness foundation, including CRM, requests, trips, reference/service catalogue governance, rules/services, offer builder, offer acceptance/booking readiness, booking/ticket/EMD mirrors, standalone/import/change/exchange workflows, document foundation, governed GDS parser foundation, governed airline policy source/extraction/review foundations, canonical special/ancillary service taxonomy mapping, separate SSR/OSI communication plus EMD/RFIC/RFISC payment mechanics mapping, policy-based ancillary pricing/exception metadata, metadata-only airline comparison/service advisory views, offer-linked policy advisor context, human-reviewed offer decision packs, decision explanation timelines, metadata-only review export snapshots, internal render preview metadata, manual release readiness, manual delivery handoff metadata, manual delivery outcome tracking, metadata-only export audit reviews, metadata-only export governance records, metadata-only compliance evidence records, governed airline intelligence data packs with staged items, validation issues, import runs, review notes, and coverage snapshots, metadata-only data pack review checklists, field mappings, conflict records, promotion-readiness records, review snapshots, governed airline intelligence knowledge versions with release-channel metadata, comparisons, rollback plans, and immutable version snapshots, agency consumption profiles, assignment views, usage readiness, notes, and snapshots for safe-use visibility, plain-language Platform Console and Agency Workspace navigation groups, metadata-only SaaS subscription plans, entitlements, assignments, readiness rows, review notes, immutable snapshots, read-only entitlement visibility badges for agency navigation and platform review, agency-specific feature visibility metadata independent of subscription plans, read-only feature flag audit/readiness metadata, reusable feature flag bundle metadata, metadata-only agency feature bundle assignment history, metadata-only capability catalog visibility, assigned-bundle rollout readiness checklists, metadata-only feature bundle rollout plan records, the read-only rollout dashboard, metadata-only rollout approval records, metadata-only rollout schedule records, metadata-only rollout timeline entries, metadata-only feature bundle dependency records, metadata-only feature bundle rollout risk register records, metadata-only feature bundle rollout issue log records, metadata-only feature bundle rollout decision register records, metadata-only feature bundle rollout change request records, metadata-only feature bundle rollout rollback plan records, and metadata-only feature bundle rollout summary evidence-pack records, plus metadata-only operational travel workspace, travel request workspace, passenger workspace, flight workspace, trip workspace, offer workspace, booking workspace, ticket workspace, EMD workspace, SSR / OSI operational workspace, document workspace records, operational timeline records, passenger service workflow records, architecture-only AOIE metadata, metadata-only airline operational knowledge graph records, metadata-only operational constraint language records, metadata-only airline operational knowledge normalisation records, metadata-only airline operational knowledge governance/version records, metadata-only airline operational capability matrix records, metadata-only operational knowledge evaluation records, metadata-only passenger service feasibility records, metadata-only airline recommendation records, metadata-only intelligent offer builder package records, metadata-only operational intelligence case records, metadata-only service parameter taxonomy records, metadata-only request segment service scope records, metadata-only client/passenger master workspace records, metadata-only reference data engine domain records, metadata-only knowledge import template records, metadata-only visual policy editor cards, metadata-only pricing formula builder records, metadata-only operational rule composer records, metadata-only knowledge QA review records, metadata-only airline knowledge publication records, metadata-only operational scenario test records, metadata-only knowledge population toolkit records, metadata-only pilot readiness profile, assessment, check, golden-path case/run, and issue records, metadata-only operational workflow orchestration records, metadata-only canonical agent work queue and assignment records, metadata-only SLA and operational deadline records, metadata-only task automation/dependency orchestration records, metadata-only request-to-trip operational conversion records, metadata-only offer-to-booking handoff readiness records, metadata-only servicing/after-sales workflow records, and metadata-only operations command center aggregate visibility records.

Phase 54.1 adds the metadata-only Operational Workflow Orchestration Foundation. It exposes canonical workflow-state, transition, guard, warning/blocker, immutable history, event, and entity-summary metadata around existing operational workspaces without replacing them, executing providers, automating workflows, sending messages, or mutating existing entity statuses without future explicit adapters.

Phase 54.2 adds the metadata-only Agent Work Queue and Assignment Foundation. It exposes the canonical agency staff queue for actionable work from requests, trips, offers, bookings, ticketing, EMDs, passenger services, documents, approvals, knowledge gaps, disruptions, service cases, workflow blockers, tasks, and timelines without creating a duplicate task system, executing providers, automating workflows, sending messages, or bypassing agency isolation.

Phase 54.3 adds the metadata-only SLA and Operational Deadline Engine Foundation. It exposes SLA policies, business calendars, calculated operational deadlines, due-soon/breach visibility, pause/resume/extension audit events, work-queue links, workflow links, and timeline history metadata without enforcing access, blocking routes, scheduling workers, calling providers, sending messages, or automating operational actions.

Phase 54.4 adds the metadata-only Task Automation and Dependency Orchestration Foundation. It exposes safe task templates, dependency metadata, automation rule metadata, idempotent automation run audit records, existing request-task creation, work-queue synchronization, and workflow-event metadata without arbitrary code execution, background workers, provider integrations, AI, messaging, operational execution, or duplicate task systems.

Phase 54.5 adds the metadata-only Request-to-Trip Operational Conversion Foundation. It exposes conversion preview, validation, run audit, entity mapping, issue, workflow/task/deadline/timeline integration, and safe retry metadata while preserving the request as the immutable intake origin and creating or explicitly attaching a downstream trip shell without booking, ticketing, provider calls, AI, workers, seeding, route blocking, or request-id-as-trip-id behavior.

Phase 54.6 adds the metadata-only Offer-to-Booking Handoff and Booking Readiness Foundation. It exposes accepted-offer handoff records, readiness checks, passenger/segment/service/document/approval/pricing mappings, booking instruction metadata, workflow/queue/SLA/task/timeline links, and controlled booking workspace creation from existing booking readiness packages while preserving frozen accepted offer snapshots as source truth and without live booking, ticketing, EMD issuance, payments, provider calls, AI, workers, or operational execution.

Phase 54.8 adds the metadata-only Operations Command Center Foundation. It exposes read-only agency and platform aggregate dashboards for workload, queues, deadlines, blockers, booking handoffs, service documents, departures, after-sales cases, knowledge/manual-review cases, payment blockers, pilot-readiness issues, calendar events, workflow-derived kanban lanes, timeline events, and team workload without duplicating operational records, mutating statuses, enabling uncontrolled drag-and-drop, executing providers, calling external APIs, using AI, sending messages, or scheduling workers.

Phase 54.9 completes Epic 54 with the End-to-End Operational Workflow Maturity Foundation. It reuses Phase 53 pilot-readiness patterns and canonical Epic 54 metadata to score workflow linkage, assignment, SLA, task dependency, conversion, booking handoff, servicing, command-center visibility, audit, message separation, agency isolation, and production safety. Platform and Agency pages show deterministic maturity, failing stages, blockers, remediation links, recent errors, coverage, and ten isolated golden-path diagnostics that are never persisted as production operational records.

Phase 58.4 (`phase_58_4_aeroassist_product_standards_ux_refinement`) established the shared travel-first product language, interaction, accessibility, and responsive patterns now reused by Commercial Pilot surfaces. See [AeroAssist Product Standards](docs/product/aeroassist-product-standards.md).

Phase 58.5 completes the Commercial Pilot readiness package for controlled use by micro and small agencies. Agency users receive contextual guidance across onboarding, Operations, Requests, Offers, Booking, Passengers, Documents, and Tasks, plus one tenant-scoped help and feedback surface. Platform roles receive governed feedback review and a deterministic Commercial Pilot assessment covering Phase 58 capabilities, documentation, health/readiness, smoke inventory, and disabled execution boundaries. The assessment supplements but never replaces Phase 57 production evidence and human sign-off.

Phase 59.0 reorganizes the technically complete product around operator purpose. Platform users receive eight permission-aware areas and a practical Overview; Agency users receive workflow-ordered navigation with the Phase 58.2 Operations Command Centre at `/agency`. The existing module catalogue remains the route source, specialist surfaces move into collapsed Advanced areas, workspace shells use explicit standard/wide/focused/reading layout primitives, and absent optional workflow diagnostics produce a useful empty state. This presentation phase adds no model, collection, index, router, provider action, payment, ticket issuance, messaging, deployment, or production-data change.

## Foundational Architecture Documents

Permanent AeroAssist architecture foundations live under `docs/architecture/foundations/`:

- [Passenger Service Operations Manifesto](docs/architecture/foundations/PASSENGER_SERVICE_OPERATIONS_MANIFESTO.md)
- [Airline Operational Knowledge Blueprint](docs/architecture/foundations/AIRLINE_OPERATIONAL_KNOWLEDGE_BLUEPRINT.md)
- [AeroAssist Engineering Principles](docs/architecture/foundations/AEROASSIST_ENGINEERING_PRINCIPLES.md)
- [Passenger Service Ontology](docs/architecture/foundations/PASSENGER_SERVICE_ONTOLOGY.md)
- [Airline Operational Knowledge Ontology](docs/architecture/foundations/AIRLINE_OPERATIONAL_KNOWLEDGE_ONTOLOGY.md)
- [Glossary](docs/architecture/foundations/GLOSSARY.md)

Product implementation and UX review should also follow [AeroAssist Product Standards](docs/product/aeroassist-product-standards.md).
Kernel lifecycle or persistence work must also follow the [Canonical Domain Ownership Map](docs/architecture/canonical-domain-ownership-map.md).

## Future Codex Guidance

Before implementing future phases, Codex should read and follow:

- `PASSENGER_SERVICE_OPERATIONS_MANIFESTO.md`
- `AIRLINE_OPERATIONAL_KNOWLEDGE_BLUEPRINT.md`
- `AEROASSIST_ENGINEERING_PRINCIPLES.md`
- `PASSENGER_SERVICE_ONTOLOGY.md`
- `AIRLINE_OPERATIONAL_KNOWLEDGE_ONTOLOGY.md`
- `GLOSSARY.md`
- `docs/product/aeroassist-product-standards.md`
- `docs/architecture/canonical-domain-ownership-map.md`
- `docs/architecture/canonical-domain-migration-register.md`

## Project Structure

- `backend/` FastAPI API, Pydantic models, tenant/auth helpers, seed service, persistence wrappers, smoke scripts, Dockerfile, and implemented Phase 1-30 foundations.
- `frontend/` Vite/React route shell for public, platform, agency, and portal layers.
- `docker-compose.production.yml` production Compose packaging for frontend, backend, MongoDB, and mounted document export storage.
- `deploy/hostinger/` nginx template, backup scripts, deployment helpers, smoke test, and operations runbook.
- `*.md` root specification documents.

## Phase 1 Includes

- Platform user/profile model.
- Agency model.
- Agency workspace/settings model.
- Agency staff membership model.
- Global reference record model.
- Audit event model.
- Demo/dev auth header mode.
- Platform role and agency role scaffolding.
- Tenant access helpers with `agency_id` isolation expectations.
- Core seed data for one platform owner, one demo agency, one agency owner membership, and foundation reference domains.
- Minimal frontend route shell for `/`, `/login`, `/platform`, `/agency`, and `/portal`.

## Phase 2 Includes

- Agency-owned client profiles.
- Agency-owned passenger profiles.
- Many-to-many client/passenger relationship records.
- Portal status fields on client profiles.
- Relationship permission flags for view, edit, document upload, travel requests, payment, and notifications.
- Non-destructive passenger merge audit.
- Agency-scoped CRM CRUD APIs.
- Agency CRM pages for clients, passengers, detail views, and relationship linking.
- Seed data for individual, organization, and family/guardian CRM scenarios.

## Phase 3 Includes

- Agency-scoped travel requests.
- Request passenger links with passenger profile snapshots.
- Intended itinerary segments.
- Requested services and service status tracking.
- Request messages.
- Request tasks.
- Request timeline events.
- Request audit events.
- Staff UI routes for request list, creation, and detail workflows.

## Phase 4 Includes

- Agency-scoped manual offers.
- Optional request-to-offer creation.
- Offer passengers with snapshots.
- Up to three route alternatives per offer.
- Up to three fare options per route alternative.
- Offer itinerary segments.
- Offer price lines.
- Manual service support checks.
- Internal client-preview page.
- Send action that snapshots the current offer content.
- Offer timeline and audit events.

## Phase 5 Includes

- Agency-scoped booking tracking records.
- Booking creation manually or from an offer.
- Booking snapshots copied from selected offer route, fare option, passengers, segments, price lines, and service checks.
- Booking passengers and booking segments.
- Ticket records issued externally.
- EMD records issued externally.
- Invoices with derived totals from line items.
- Manual payment records with received and reconciliation status.
- Booking timeline events for operational and finance changes.
- Staff UI routes for bookings, booking detail, invoices, invoice detail, and payments.

## Phase 6 Includes

- Platform-owned airline profiles.
- Platform-owned airline knowledge items with category, service code, review status, confidence, tags, and sources.
- Platform-owned airline procedures and contact/procedure instructions.
- Platform-owned EMD/RFIC/RFISC support notes.
- Platform-owned source/citation records.
- Agency-owned airline overrides and annotations.
- Agency knowledge usage events.
- Platform maintenance UI for airlines, knowledge, procedures, EMD notes, and sources.
- Agency search/detail UI for published airline intelligence.
- Lightweight search links from request, offer, and booking detail pages.
- Seeded fake/demo airline intelligence data.

## Phase 7 Includes

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

## Phase 8 Includes

- Demo portal access mapping records from portal email to agency client.
- Read-only client portal API under `/api/portal`.
- Portal-safe client, passenger, request, offer, booking, document, invoice, and payment responses.
- Client/passenger visibility enforcement through active `can_view` relationships.
- Client-scoped request, offer, booking, document, invoice, and payment visibility.
- Client-visible-only messages, tasks, timeline events, price lines, invoice lines, and rendered documents.
- Branded portal layout using agency workspace brand settings.
- Portal dashboard, profile, passengers, requests, offers, bookings, documents, invoices, and payments pages.
- Seeded demo portal accounts for the individual and organization sample clients.

## Phase 9 Includes

- MongoDB documented as the durable storage path.
- In-memory storage kept as a local dev/demo fallback only.
- Mongo startup index creation for core global and agency-owned collections.
- Immutable update-field protection for `id`, `_id`, `agency_id`, and `created_at`.
- Reusable tenant helpers for agency context, agency record assertions, agency filters, portal client context, portal passenger access, portal-owned record checks, and portal-safe projections.
- Portal response projection validation to catch internal field keys before response return.
- Lightweight backend and portal isolation smoke scripts.
- Phase 9 production-readiness warning and audit documentation.

## Phase 10 Includes

- `AuthIdentity`, `AuthSession`, and `Invitation` records.
- Local password authentication with PBKDF2 password hashes.
- Opaque bearer sessions stored as token hashes.
- Platform, agency staff, and client portal login through `POST /api/auth/login`.
- `GET /api/auth/me` role/context resolution for platform users, agency memberships, and portal mappings.
- Logout/session revocation through `POST /api/auth/logout`.
- Staff invitation creation under `/api/agencies/{agency_id}/staff/invitations`.
- Client portal invitation creation under `/api/agencies/{agency_id}/clients/{client_id}/portal-invitation`.
- Invitation acceptance through `/api/auth/invitations/accept`.
- Demo header fallback preserved only when `DEMO_AUTH_ENABLED=true`.

## Phase 11 Includes

- Portal request submission under the authenticated client context.
- Portal client message submission on existing client-owned requests.
- Portal offer accept/reject actions that create staff-review work but no bookings/tickets/payments.
- Portal document acknowledgement records.
- `PortalActionEvent` records for searchable client-originated actions.
- Staff review endpoints and `/agency/portal-actions` UI.
- Portal UI controls for new requests, messages, offer decisions, acknowledgements, and action history.

## Phase 12 Includes

- Refund/exchange case records linked to bookings, tickets, EMDs, invoices, payments, and client context.
- Manual estimate and final financial fields on case records.
- Manual financial lines for refundable fares, taxes, penalties, fees, differences, and offsets.
- Linked items with case-level statuses and notes.
- Case timeline and message history for auditability.
- Staff case status and lifecycle actions (`draft`, `review`, `completed`, `archived`, etc.).
- Optional case creation from booking with optional linked ticket/EMD/invoice/payment/passenger records.
- Portal-only read-only endpoints and pages for client-visible case summaries, visible items, lines, messages, and timeline.
- Seeded refund and exchange examples (tracking-only, no execution).

## Phase 13 Includes

- Document export records for already-rendered document snapshots.
- Printable HTML exports stored as inline base64 and downloadable by staff.
- Friendly PDF-unavailable behavior when no reliable PDF renderer is installed.
- Document delivery records for manual staff-controlled delivery attempts.
- Agency email settings with `disabled`, `dev_console`, and SMTP placeholder modes.
- Dev-console send behavior that records delivery without sending real email.
- Portal read-only export list/download for client-visible documents and exports.
- Staff document detail controls for exports, deliveries, and email settings.
- Seeded dev-console settings, printable export, and delivery example.

## Phase 14 Includes

- File-backed local storage abstraction for new document exports.
- Export checksums, safe storage keys, storage mode metadata, and cleanup-ready retention fields.
- Legacy inline-base64 export download fallback.
- Delivery attempt records for staff-controlled send/retry actions.
- Retry counters and max-attempt tracking on delivery records.
- Email settings validation with SMTP secret-reference requirements and no plaintext credential storage.
- Dev-console send attempts for local/demo delivery audit.
- Staff UI visibility for storage, retention, checksum, attempts, retry state, and email validation state.
- Portal read-only download behavior preserved without send/share controls.

## Phase 15 Includes

- ReportLab-based simplified PDF export generation from stored rendered HTML snapshots.
- `GET /api/agencies/{agency_id}/document-export-capabilities` for staff export capability diagnostics.
- File-backed PDF exports with `application/pdf`, checksum, file size, retention metadata, and safe storage keys.
- Portal read-only downloads for generated client-visible PDF and printable HTML exports.
- Stronger delivery attachment validation before staff-triggered send/retry.
- Safe dev-console delivery attempts preserved; SMTP remains guarded by secret-resolver limitations.
- Seeded PDF export only when the ReportLab renderer is available.

## Phase 16 Includes

- Environment-only SMTP password secret references using `env:VARIABLE_NAME`.
- Staff-controlled SMTP sending when agency email settings validate and the referenced environment secret resolves.
- Staff delivery diagnostics at `GET /api/agencies/{agency_id}/document-deliveries/{delivery_id}/diagnostics`.
- Retry governance so retries require `retry_available` and never run automatically.
- Production readiness script at `backend/scripts/check_production_readiness.py`.
- Staff UI visibility for delivery diagnostics, next allowed action, masked secret reference, and secret resolution status.

## Phase 17 Includes

- Centralized production configuration in `backend/config.py`.
- Strict production startup validation for MongoDB, demo auth, seed paths, CORS, auth secret, logging, and export storage.
- `GET /api/health` and `GET /api/readiness` with safe app, database, config, storage, PDF, and delivery summaries.
- Production-disabled startup seeding and seed endpoint defaults.
- Frontend API base URL handling that avoids localhost fallback in production builds.
- Hardened production readiness script and `.env.production.example`.

## Phase 18 Includes

- Backend Docker image for FastAPI/Uvicorn with ReportLab dependencies and health check.
- Frontend Docker image that builds Vite and serves it through nginx.
- nginx same-origin `/api` proxy from frontend container to backend container.
- `docker-compose.production.yml` with frontend, backend, MongoDB, health checks, and restart policies.
- Mounted named volumes for MongoDB data and document exports.
- Hostinger VPS deployment guide in `DEPLOYMENT_HOSTINGER_VPS.md`.

## Phase 19 Includes

- Host-level nginx reverse proxy template with TLS/certbot placeholders.
- Hostinger operations runbook in `deploy/hostinger/OPERATIONS_RUNBOOK.md`.
- Safe deploy, restart, status, and logs helper scripts.
- Timestamped MongoDB and document export backup scripts.
- Manual restore guidance for MongoDB and document exports.
- Production smoke-test script for frontend, health, readiness, and login availability.
- Rollback, update, log inspection, and incident checklist documentation.

## Phase 20 Includes

- First Hostinger deployment checklist in `deploy/hostinger/FIRST_DEPLOYMENT_CHECKLIST.md`.
- Post-deployment security checklist in `deploy/hostinger/POST_DEPLOYMENT_SECURITY_CHECKLIST.md`.
- Deployment troubleshooting guide in `deploy/hostinger/TROUBLESHOOTING.md`.
- Non-mutating preflight script at `deploy/hostinger/scripts/preflight.sh`.
- Deploy helper now runs preflight before git update, build, or service start.
- Phase 20 implementation note in `PHASE_20_FIRST_DEPLOYMENT_PREPARATION.md`.

## Phase 21 Includes

- Official first platform owner bootstrap script at `backend/scripts/create_first_platform_owner.py`.
- Production frontend hides demo login labels, demo account cards, and demo credential defaults.
- Hostinger scripts default to the real deployment path `/opt/aeroassist-agencyos` while preserving `APP_DIR` overrides.
- Real deployment notes in `deploy/hostinger/REAL_DEPLOYMENT_NOTES.md`.
- VPS reboot verification procedure in `deploy/hostinger/OPERATIONS_RUNBOOK.md`.
- Temporary `:8080` exposure and future nginx/TLS migration plan documented.

## Phase 22 Includes

- Platform owner agency management at `/platform/agencies`.
- Production-safe create-agency flow without automatic workspace or demo seed creation.
- Agency detail page for editing basics, creating the first workspace, viewing staff memberships, and preparing staff invitations.
- Workspace listing and creation endpoints under `/api/agencies/{agency_id}/workspaces`.
- Platform-owner safe agency membership creation when a workspace is created, preventing lockout from the agency workspace.
- Production onboarding summary flags in `/api/platform/summary`.
- Production deployment note for `https://avio.my` and old app preservation in `PHASE_22_PRODUCTION_ONBOARDING_AGENCY_SETUP.md`.

## Phase 23 Includes

- Combined backup script for MongoDB and document exports at `deploy/hostinger/scripts/backup_all.sh`.
- Backup verification script with checksum and age checks at `deploy/hostinger/scripts/verify_backups.sh`.
- Conservative dry-run-first retention pruning at `deploy/hostinger/scripts/prune_backups.sh`.
- Lightweight host healthcheck at `deploy/hostinger/scripts/healthcheck.sh`.
- Full safe operational status script at `deploy/hostinger/scripts/status_full.sh`.
- Root-owned systemd backup and verification timer templates under `deploy/hostinger/systemd/`.
- Phase 23 implementation note in `PHASE_23_BACKUP_AUTOMATION_MONITORING_READINESS.md`.

## Phase 24 Includes

- Staff invitation records hardened with workspace scope, invited name, accepted/revoked metadata, and token-hash-only storage.
- One-time raw staff invitation token and acceptance URL returned only when creating an invitation.
- Staff invitation list and revoke endpoints that never return token material.
- Public invitation validation endpoint with minimal agency/workspace/email/role metadata.
- Invitation-only staff account activation at `/invite/accept?token=...`.
- Role restrictions that prevent platform owner or agency owner invitation through the staff flow.
- Audit events for invitation creation, revocation, acceptance, and membership creation without token material.
- Staff invitation smoke script at `backend/scripts/smoke_staff_invitations.py`.

## Phase 25 Includes

- Document storage lifecycle metadata for generated document exports.
- Safe `/api/documents/storage/*` endpoints for summaries, health, listing, archive, and mark-missing actions.
- Delivery provider readiness endpoints where manual is enabled and automatic/external providers are disabled by default.
- Agency page at `/agency/document-storage` for storage health, lifecycle counts, provider readiness, and record actions.
- Hostinger storage check script at `deploy/hostinger/scripts/check_storage.sh`.
- Phase 25 implementation note in `PHASE_25_DOCUMENT_STORAGE_LIFECYCLE_DELIVERY_PROVIDER_READINESS.md`.

## Phase 26 Includes

- Public request intake endpoint at `POST /api/public/request-intakes` with safe confirmation responses.
- Staff request intake queue/detail, triage, reject/archive/duplicate, and conversion endpoints under `/api/request-intakes`.
- Conversion service that creates canonical operational requests with `source_intake_id`, payload snapshots, route/service summaries, and duplicate conversion guard.
- Portal request submission now creates request intakes first instead of direct operational requests.
- Public homepage intake form plus agency intake queue/detail UI.
- Phase 26 implementation note in `PHASE_26_REQUEST_INTAKE_OPERATIONAL_REQUEST_STABILIZATION.md`.

## Phase 27 Includes

- Structured operational request builder endpoint at `POST /api/agencies/{agency_id}/requests/builder`.
- Inline client and passenger creation from `/agency/requests/new`.
- Structured trip type, route, segment, service category, conditional service detail, and notes capture.
- Requested service detail payloads plus passenger/segment relationship fields.
- Intake conversion alignment with passenger placeholders and structured service records.
- Phase 27 implementation note in `PHASE_27_OPERATIONAL_REQUEST_BUILDER_V1.md`.

## Phase 27.1 Includes

- Corrected mobility assistance logic with `assistance_code` for WCHR/WCHS/WCHC/MAAS/unknown.
- Separate optional transfer/boarding details, own mobility device details, and battery fields only for electric mobility devices.
- Updated request builder UI cards and request detail summaries for mobility assistance.
- Phase 27.1 implementation note in `PHASE_27_1_MOBILITY_ASSISTANCE_LOGIC_FIX.md`.

## Phase 27.2 Includes

- Assessment-first mobility assistance workflow with passenger context tags and functional assessment fields.
- Frontend SSR/service recommendation for WCHR, WCHS, WCHC, MAAS, MEDA, BLND, DEAF, and manual review.
- Staff confirmation with override reason when confirmed code differs from the suggestion.
- Intake conversion manual-review payloads for mobility requests without assessment detail.
- Phase 27.2 implementation note in `PHASE_27_2_ASSISTANCE_ASSESSMENT_SSR_RECOMMENDATION.md`.

## Phase 28 Includes

- Agency branding settings model and APIs for controlled brand identity, typography, palettes, theme mode, radius, density, controls, date input, and card style presets.
- Safe logo upload/removal from `/agency/settings` with PNG/JPEG/WEBP only, 2MB limit, no SVG execution, no public filesystem path, and audit events.
- Central agency theme layer that converts settings into CSS variables for agency headers, navigation, buttons, inputs, cards, badges, and native date fields.
- Optional platform/readiness branding summary that does not fail readiness when no agency branding is configured.
- Phase 28 implementation note in `PHASE_28_AGENCY_BRANDING_THEME_PERSONALIZATION.md`.

## Phase 28.1 Includes

- Professional agency app shell with persistent desktop sidebar, responsive mobile drawer, active route highlighting, and desktop collapse.
- Top bar with workspace context, primary create-request action, manual-operations badge, and account/logout area.
- Theme-aware shared visual polish for backgrounds, cards, forms, buttons, focus states, status surfaces, and table overflow.
- Improved dashboard, requests, intakes, request detail, and request builder layout hierarchy.
- Disabled coming-soon sidebar entry for Offers/Pricing, later enabled by Phase 36.1.
- Phase 28.1 implementation note in `PHASE_28_1_APP_SHELL_SIDEBAR_VISUAL_POLISH.md`.

## Phase 29 Includes

- Agency website settings and controlled CMS pages/sections for safe public content.
- Agency UI at `/agency/website` for site settings, page creation, section editing, publishing, archiving, and live preview.
- Public website renderer at `/site/{slug}` backed by `GET /api/public/websites/{slug}` for active websites only.
- Website/CMS sidebar navigation enabled.
- CMS smoke script at `backend/scripts/smoke_agency_website_builder.py`.
- Phase 29 implementation note in `PHASE_29_AGENCY_WEBSITE_BUILDER_CMS_FOUNDATION.md`.

## Phase 30 Includes

- Rich controlled CMS blocks for hero, service cards, feature grid, process steps, FAQ, contact CTA, request-form CTA, testimonials, trust badges, image/text, contact details, and legal text.
- Type-aware website builder editing with add/edit/delete and move up/down section controls.
- Explicit publish/offline site actions and published inner-page rendering.
- Public request form at `/site/{slug}/request` that creates `request_intakes` with agency/site/page source metadata.
- Intake queue/detail display for website CMS requests.
- Phase 30 implementation note in `PHASE_30_PUBLIC_WEBSITE_PUBLISHING_INTAKE_FORMS_CMS_BLOCKS.md`.

## Phase 30.1 Includes

- Dedicated agency logo asset records with original, square, compact, horizontal, and favicon variants.
- Server-side logo upload validation, decoded-image verification, metadata stripping, and generated PNG derivatives.
- `/agency/settings` logo controls for preview, replace/remove, fit mode, preferred usage, public usage, and variant regeneration.
- Agency shell and public website rendering use safe prepared logo variants without exposing filesystem paths or private storage URLs.
- Phase 30.1 implementation note in `PHASE_30_1_BRANDING_LOGO_ASSET_SETTINGS_STABILIZATION.md`.

## Phase 31 Includes

- Agency CMS media library for public website images, separate from logo assets.
- Safe PNG/JPEG/WEBP upload with 5MB limit, magic-byte checks, decoded-image verification, metadata stripping, and generated thumbnail/card/hero/original-safe variants.
- Media management UI at `/agency/website/media` and controlled section image picker in the website builder.
- Public website renderer uses only active public-safe referenced media and has polished public layout/request form styling.
- Phase 31 implementation note in `PHASE_31_CMS_MEDIA_LIBRARY_PUBLIC_WEBSITE_VISUAL_POLISH.md`.

## Phase 32 Includes

- Blueprint alignment/gap map in `docs/architecture/agencyos-blueprint-alignment-gap-map.md`.
- Canonical operations model rules in `docs/architecture/canonical-operations-model.md`.
- Current FastAPI/Mongo model inventory in `docs/architecture/current-model-inventory.md`.
- Additive trip dossier, request case flag, passenger/segment service, pet transport, and special item foundation models.
- Phase 32 implementation note in `PHASE_32_BLUEPRINT_ALIGNMENT_CANONICAL_OPERATIONS_MODEL.md`.

## Phase 33 Includes

- Controlled reference domains and records for master operational lookup data.
- Service catalogue foundation with family, SSR, beneficiary, scoping, policy, document, pricing, and schema metadata.
- Manual idempotent bootstrap script in `backend/scripts/bootstrap_reference_data.py`.
- Authenticated reference APIs and agency UI at `/agency/reference`.
- Phase 33 implementation note in `PHASE_33_REFERENCE_DATA_CORE_SERVICE_CATALOGUE.md`.

## Phase 33.1 Includes

- Platform-owned global Reference Data governance and agency suggestion queue.
- Manual CSV bulk import batches with validation, file hash, audit records, and insert/update/skip reporting.
- Suggestion review actions for approve, reject, needs-more-information, and archive.
- Agency `/agency/reference` governance tabs for global data, service catalogue, suggestions, imports, and review queue.
- Future policy-governance notes for local overrides, evidence, and promotion to global policy rules.
- Phase 33.1 implementation note in `PHASE_33_1_GLOBAL_REFERENCE_GOVERNANCE_SUGGESTIONS.md`.

## Phase 34 Includes

- Request normalization into passenger + segment scoped service rows.
- Pet and special item capture with exact segment transport rows.
- Derived request case flags and root operational counters.
- Builder/detail UI for canonical services, pets, special items, and source snapshots.
- Phase 34 implementation note in `PHASE_34_SEGMENT_SCOPED_REQUEST_SERVICES_PETS_ITEMS.md`.

## Phase 34.1 Includes

- Platform-owned Global Field Library with canonical field definitions, safety flags, and override permissions.
- Agency Form Profiles and field settings for public, portal, admin, offer-client, and offer-PDF contexts.
- Effective profile resolver that enforces system-required locks and public/internal safety rules.
- Agency custom questions stored under `agency_custom_fields`.
- `/agency/settings/forms` field menu UI and foundational public/admin request form integration.
- Phase 34.1 implementation note in `PHASE_34_1_GLOBAL_FIELD_LIBRARY_AGENCY_FORM_PROFILES.md`.

## Phase 34.2 Includes

- Platform-only Reference Data Management Console at `/platform/reference`.
- Enriched country metadata on legacy-compatible `global_reference_records.metadata_json`.
- Platform-owned domain metadata, global record cards, suggestion review, dry-run/committed import, and CSV/JSON export.
- Agency reference data page remains consume-and-suggest only.
- Phase 34.2 implementation note in `PHASE_34_2_PLATFORM_REFERENCE_DATA_CONSOLE_ENRICHED_COUNTRIES.md`.

## Phase 34.3 Includes

- Reference enrichment import pack templates in `data/reference_packs/`.
- Platform-only enrichment APIs and `/platform/reference` import pack UI.
- Non-destructive dry-run and commit workflows with update modes and row-level reports.
- Country, airport, airline, currency, language, and region normalization.
- Cross-link warnings for missing country/airport/airline/currency/language references.
- Phase 34.3 implementation note in `PHASE_34_3_REFERENCE_DATA_ENRICHMENT_IMPORT_PACKS.md`.

## Phase 35 Includes

- Trip dossier operational shell with independent `TRP-YYYYMMDD-XXXX` references.
- Manual trip creation and idempotent request-to-trip conversion.
- Linked request management without replacing requests or reusing request IDs as trip IDs.
- Trip passenger, segment, and service item copies with source request child IDs preserved.
- Trip timeline/audit events, summary rebuild, archive action, and readiness counters.
- Agency UI routes `/agency/trips`, `/agency/trips/new`, `/agency/trips/{trip_id}` plus request detail/list linkage.
- Phase 35 implementation note in `PHASE_35_TRIP_DOSSIER_FOUNDATION.md`.

## Phase 36.0 Includes

- Unified platform-owned airline intelligence profile foundation records.
- `AirlineRulesCore` records for future UMNR, PRM, medical, pets/service animals, cargo, VIP, baggage, seating, meal, and general rules.
- `UnifiedExceptionRule` records and a safe exception engine with no unsafe expression evaluation.
- Agency-owned `PassengerServiceRequest` records bridging requests, trips, bookings, passengers, and segments.
- Deterministic SSR/OSI preview generation for core passenger service types.
- Platform `/platform/rules-services` console and APIs for airline rules, exception rules, and simulation.
- Agency request/trip special-services workspaces for service creation, evaluation, and SSR/OSI previews.
- Idempotent LH/TK/AF seed script and readiness flags under `rules_and_services`.
- Full airline dashboards, AI reasoning engines, ticketing, document designer, scraping, and large airline datasets remain future work.

## Phase 36.1 Includes

- Agency-owned offer workspaces linked to requests and/or trip dossiers.
- Rule-aware offer options with route segments, fare bundles, pricing lines, rule summaries, service feasibility, warnings, and recommendation metadata.
- Internal comparison matrix generation and saved comparison snapshots.
- Request and trip detail actions to create or open an offer workspace without replacing the source request/trip.
- Agency routes `/agency/offers`, `/agency/offers/{workspace_id}`, and `/agency/offers/{workspace_id}/builder`.
- Backend endpoints under `/api/agencies/{agency_id}/offer-workspaces` and `/api/agencies/{agency_id}/offer-options`.
- Readiness flags and counts under `offer_builder`.

## Phase 36.2 Includes

- Offer acceptance records with immutable snapshots of accepted pricing, routing, fare bundle, services, pets, special items, rules feasibility, and client-visible summary.
- Trip accepted-offer snapshots that attach the accepted option to the trip operational baseline.
- Booking readiness packages with manual provider target, passenger/segment/pricing/service snapshots, SSR/OSI previews, warnings, required documents, policy violations, and readiness checks.
- Supersede and cancel lifecycle for accepted options without deleting historical snapshots.
- Agency endpoints for accept, workspace acceptance lookup, trip accepted-offer lookup, booking readiness lookup, rebuild, and cancel.
- Offer workspace, offer builder, and trip detail UI panels for acceptance/readiness visibility.
- Readiness flags and counts under `offer_builder`.

## Phase 36.2.5 Includes

- Reference domain consumer map for platform-owned domains, including consumers, workflow usage, required metadata, import support, enrichment support, health checks, operational impact, and risk.
- Reference Health & Action Required endpoints and UI replacing unexplained Important Records with explicit reasons and recommended actions.
- Domain-aware import templates plus explicit preview/apply APIs for governed reference domains and service catalogue records.
- Reference Enrichment Pack definitions/API for controlled metadata updates.
- Editable platform Service Catalogue APIs and UI with operational mappings for request UI, rules/services, SSR/OSI, offers, acceptance, booking readiness, documents, and future EMD readiness.
- Agency consume-only service catalogue clarity with correction suggestions remaining in reference governance.
- Compatibility links from Service Catalogue into request services, special service requests, rules/services evaluation, offer builder, accepted snapshots, trip service items, and booking readiness.
- Readiness flags and counts under `reference_data`.

## Phase 36.3 Includes

- Booking workspaces created from booking readiness packages, preserving accepted passenger, segment, pricing, service catalogue, pet, special-item, SSR/OSI, document, warning, and policy snapshots.
- Draft booking record mirrors with manual PNR locator/status fields, provider payload/response placeholders, and internal PNR mirror JSON.
- Booking timeline events linked to booking workspaces and records while preserving legacy booking timeline compatibility.
- Agency APIs and UI for booking workspace list/detail, status updates, manual PNR mirror updates, draft rebuild, and cancel.
- Trip and accepted-offer readiness panels that create or open booking workspaces.
- Readiness flags and counts under `booking_foundation`; provider execution remains disabled.

## Phase 36.4 Includes

- Internal ticket and EMD mirror records linked to booking workspaces and booking records.
- Ticket coupon and EMD coupon records for passenger, segment, service, and coupon-level status tracking.
- Ticket/EMD timeline events for draft creation and manual mirror updates.
- Agency ticket list/detail/update/create-from-booking APIs and EMD list/detail/update/create-from-booking-service APIs.
- Ticket/EMD readiness summaries for booking records, preserving service catalogue EMD applicability mappings.
- Agency routes for `/agency/tickets-emds`, `/agency/tickets/{ticket_record_id}`, and `/agency/emds/{emd_record_id}`.
- Booking workspace and trip panels for linked ticket/EMD mirrors and readiness warnings.
- Readiness flags and counts under `ticket_emd_foundation`; provider ticketing and EMD issuance remain disabled.

## Phase 36.4.5 Includes

- Supplementary blueprint adoption map and canonical route policy documentation.
- `AiTraceEvent`, `AdmRiskEvent`, `GdsParseSample`, and `AirlineBrandAsset` foundation records.
- Platform blueprint APIs under `/api/platform/blueprint`.
- Platform route `/platform/blueprint` for adoption map, route policy, gaps, and next phase recommendations.
- `SpecialServicesUnifiedFacade` over existing rules/services, exception, SSR/OSI, and service catalogue foundations.
- Readiness flags and counts under `blueprint_sync`.
- Explicit rejection of supplementary `/agent` and `/admin` route roots.
- Recognition that Phase 36.4 already built Tickets + EMD Foundation and that booking workspace creation is available from accepted-offer readiness packages.

## Phase 36.4.6 Includes

- Manual booking workspace creation without requiring an accepted-offer readiness package.
- `BookingImportDraft` staging records for cryptic GDS or itinerary confirmation text, with conservative deterministic parse previews.
- `TripChangeOperation`, `TicketExchangeOperation`, and `EmdExchangeOperation` foundations for existing-trip servicing and internal exchange/reissue mirrors.
- Manual ticket and EMD mirror creation with optional booking record, booking workspace, trip, client, and passenger links.
- Structured manual booking, ticket, EMD, import preview, and trip-change UI sections; raw JSON snapshots remain collapsed advanced fallback inputs only.
- Agency UI entry points on `/agency/booking-workspaces`, `/agency/booking-imports`, `/agency/tickets-emds`, and trip detail.
- Readiness flags under `booking_foundation`, `ticket_emd_foundation`, `change_exchange_foundation`, and `blueprint_sync`.
- Request/offer linkage fields for future trip-change and exchange/refund quote flows.
- Provider execution, live booking, live ticketing, live EMD issuance, exchange, refund, void, payment, and accounting execution remain disabled.

## Phase 36.5 Includes

- Unified document context previews for requests, offers, trips, booking workspaces/records, tickets, EMDs, imports, change/exchange operations, service requests, and mixed contexts.
- Platform default document templates, agency render jobs, document packages, and internal/manual share records.
- Agency UI `/agency/documents` and platform UI `/platform/document-templates`.
- Live delivery, public links, e-signature, payments, invoice/accounting, settlement, provider execution, and required PDF export remain disabled.

## Phase 36.6 Includes

- Governed GDS parser profiles, parser versions, parser runs, parsed entities, human corrections, training samples, and evaluation records.
- Booking import drafts now reference the latest parser run, confidence, entity counts, warnings, and normalized structured preview.
- Agency UI `/agency/gds-parser` for parse review, structured entity tables, corrections, parser history, and training sample creation.
- Platform UI `/platform/gds-parser` for default profile/version seeding, version activation, training sample review, and evaluations.
- Parser-run document context plus GDS parse and booking import review summary document types.
- Live GDS/NDC/provider connectivity, external AI parser calls, automatic import, live booking/ticket/EMD issuance, exchanges/refunds/voids, payments, invoices/accounting, and settlement remain disabled.

## Phase 36.7 Includes

- Governed airline policy sources, detected sections, extraction runs, rule/price/SSR-OSI/EMD/exception candidates, review corrections, and approved knowledge records.
- Deterministic, conservative extraction from pasted policy text without external AI, scraping, GDS/NDC, or provider calls.
- Platform UI `/platform/airline-policy-ingestion` and APIs under `/api/platform/airline-policy/*` for source creation, extraction, candidate review, explicit promotion, and approved knowledge listing.
- Agency UI `/agency/airline-policy-library` and APIs under `/api/agencies/{agency_id}/airline-policy/*` for read-only approved library access, local source extraction/review, and submit-for-platform-review.
- Policy source/extraction/approved-knowledge document contexts plus airline policy extraction/review summary templates.
- Auto-promotion to global knowledge remains disabled; platform review is required for approved global policy knowledge.

## Phase 36.8 Includes

- Canonical service domains, families, and variants for special/ancillary service normalization.
- Airline service aliases, deterministic mapping rules, applicability dimensions, policy outcome types, candidate taxonomy links, and taxonomy review corrections.
- Idempotent baseline seed data for children, mobility, medical, pets/animals, special baggage/items, seating, meals, VIP/protocol, disruption, documents, claims, distribution/payment, and fallback service domains.
- Platform UI `/platform/service-taxonomy` and APIs under `/api/platform/service-taxonomy/*` for global taxonomy governance, baseline seeding, mapping tests, links, and corrections.
- Agency UI `/agency/service-taxonomy` and APIs under `/api/agencies/{agency_id}/service-taxonomy/*` for read-only taxonomy lookup, mapping tests, agency-local links, and corrections.
- Taxonomy remains separate from SSR/OSI communication instructions, EMD/RFIC/RFISC payment mechanics, pricing matrices, policy comparison matrices, live provider execution, scraping, and external AI mapping.

## Phase 36.9 Includes

- Airline-level service communication rules, SSR/OSI/OTHS templates, structured request requirements, host status recognition rules, and rejection/unable patterns.
- Separate payment and EMD mechanics records for service payment rules, EMD issuance metadata, RFIC/RFISC mappings, interline restrictions, and lifecycle behavior.
- Candidate mechanics links from policy candidates and taxonomy links without agency auto-promotion.
- Platform UI `/platform/service-mechanics` and APIs under `/api/platform/service-mechanics/*` for global mechanics governance and lookup.
- Agency UI `/agency/service-mechanics` and APIs under `/api/agencies/{agency_id}/service-mechanics/*` for read-only lookup plus agency-local candidate links.
- Deterministic lookup returns communication and payment mechanics separately and remains metadata-only.

## Phase 37.0 Includes

- Normalized ancillary pricing rules, price components, applicability records, pricing matrices, matrix rows, expanded service exception rules, quote scenarios/results, and policy candidate pricing links.
- Platform UI `/platform/ancillary-pricing` and APIs under `/api/platform/ancillary-pricing/*` for pricing and exception governance.
- Agency UI `/agency/ancillary-pricing` and APIs under `/api/agencies/{agency_id}/ancillary-pricing/*` for read-only lookup, local quote scenarios/results, and agency-local candidate links.
- Deterministic quote evaluation that keeps pricing estimates separate from invoices, payments, accounting, BSP/ARC settlement, EMD issuance, ticketing, and provider execution.
- Pricing may reference EMD/payment mechanics records, but references never issue EMDs or execute SSR/OSI/GDS/NDC/provider actions.

## Phase 37.1 Includes

- Airline policy comparison profiles, generated comparison snapshots, normalized comparison rows, service advisor scenarios/results, and saved comparison views.
- Platform UI `/platform/policy-comparison` and APIs under `/api/platform/policy-comparison/*` for global comparison profile governance, comparison generation, advisor evaluation, and saved views.
- Agency UI `/agency/policy-comparison` for read-only global profile consumption, agency-local snapshots, comparison rows, and saved views.
- Agency UI `/agency/airline-service-advisor` for deterministic service advisory scenarios and stored results.
- Operational complexity scoring is metadata-only and is not an automatic airline recommendation.
- Provider execution, live SSR/OSI, ticketing, EMD issuance, payments, invoices, accounting, BSP/ARC settlement, scraping, external AI, and agency-to-global auto-promotion remain disabled.

## Phase 37.2 Includes

- Offer policy advisor contexts, offer-linked airline rows, warnings, manual decision notes, and saved snapshots.
- Agency UI `/agency/offer-policy-advisor` and APIs under `/api/agencies/{agency_id}/offer-policy-advisor/*` to build/evaluate offer workspace advisory context, attach metadata artifacts, record manual notes, and save snapshots.
- Platform UI `/platform/offer-policy-advisor` and APIs under `/api/platform/offer-policy-advisor/*` for read-only governance diagnostics.
- Links from offer workspaces/options to policy comparison snapshots, service advisor scenarios/results, ancillary pricing quote results, service mechanics lookup metadata, and taxonomy domain/family/variant references.
- Offer advisor output remains metadata-only and human-reviewed; it never auto-selects airlines or changes offer pricing.
- Provider execution, booking, ticketing, EMD issuance, payments, invoices, accounting, BSP/ARC settlement, scraping, external AI, and agency global mutation remain disabled.

## Phase 37.3 Includes

- Offer decision packs, option-level evidence rows, warning summaries, review notes, and immutable decision pack snapshots.
- Agency UI `/agency/offer-decision-packs` and APIs under `/api/agencies/{agency_id}/offer-decision-packs/*` to build/rebuild packs, consume saved advisor snapshots/context, attach evidence, record/update review notes, and save snapshots.
- Platform UI `/platform/offer-decision-packs` and APIs under `/api/platform/offer-decision-packs/*` for read-only governance diagnostics.
- Decision packs consume offer policy advisor contexts/snapshots, comparison rows, ancillary quote results, service mechanics metadata, taxonomy references, and offer option context.
- Decision packs are metadata-only and human-reviewed; they never rank a winner, recommend automatically, mutate offer prices, book, issue tickets/EMDs, charge, invoice, settle, or execute providers.

## Phase 37.4 Includes

- Offer decision explanations, decision timeline events, evidence references, human decision reasons, acknowledgements, and immutable audit snapshots.
- Agency UI `/agency/offer-decision-explanations` and APIs under `/api/agencies/{agency_id}/offer-decision-explanations/*` to record human explanations, append timeline events, record reasons and acknowledgements, list evidence references, and save audit snapshots.
- Platform UI `/platform/offer-decision-explanations` and APIs under `/api/platform/offer-decision-explanations/*` for read-only governance diagnostics.
- Explanation records derive evidence references from existing offer decision packs, advisor evidence, comparison snapshots, ancillary quotes, mechanics metadata, taxonomy references, warnings, and review notes.
- Explanations are metadata-only and human-reviewed; finalized explanations are immutable except archive state, and snapshots are immutable audit records. They never rank a winner, recommend automatically, mutate offer prices, book, issue tickets/EMDs, charge, invoice, settle, call providers, scrape, or call external AI.

## Phase 37.5 Includes

- Offer decision export records, ordered export sections, metadata-only PDF/JSON artifact records, unsent recipient drafts, and export audit events.
- Agency UI `/agency/offer-decision-exports` and APIs under `/api/agencies/{agency_id}/offer-decision-exports/*` to generate/list/read export snapshots from existing decision packs and explanations.
- Platform UI `/platform/offer-decision-exports` and APIs under `/api/platform/offer-decision-exports/*` for read-only governance diagnostics.
- Export sections include decision pack options, evidence, warnings, review notes, explanations, timeline events, reasons, acknowledgements, and audit snapshots.
- Export records are metadata-only review/audit snapshots. They do not send emails, create public links, generate live booking/ticket/EMD/payment/invoice/settlement actions, mutate offers or prices, recommend airlines automatically, or execute providers.

## Phase 37.6 Includes

- Offer decision export preview records, ordered preview sections, typed render-preview blocks, metadata completeness validations, and immutable preview snapshots.
- Agency UI `/agency/offer-decision-export-previews` and APIs under `/api/agencies/{agency_id}/offer-decision-export-previews/*` to generate render-preview metadata from existing offer decision exports, validate metadata completeness, and save immutable preview snapshots.
- Platform UI `/platform/offer-decision-export-previews` and APIs under `/api/platform/offer-decision-export-previews/*` for read-only governance diagnostics.
- Preview sections cover executive summary, selected decision pack overview, option comparison, advisor evidence, warnings, review notes, explanation narrative, decision timeline, acknowledgement status, artifact metadata, recipient draft metadata, and audit trail.
- Export previews are internal metadata-only render previews. They do not deliver PDFs, send emails/SMS, create public links, mutate offers or prices, recommend airlines automatically, book, ticket, issue EMDs, invoice, charge, settle, scrape, call external AI, or execute providers.

## Phase 37.7 Includes

- Offer decision export approval records, approval checkpoints, manual release readiness records, release holds, and immutable release snapshots.
- Agency UI `/agency/offer-decision-export-releases` and APIs under `/api/agencies/{agency_id}/offer-decision-export-releases/*` to create human approval metadata, record checkpoints, prepare manual release readiness, add/release holds, and save immutable release snapshots.
- Platform UI `/platform/offer-decision-export-releases` and APIs under `/api/platform/offer-decision-export-releases/*` for read-only governance diagnostics.
- Release readiness consumes Phase 37.6 export preview metadata and records human approval gates without sending, publishing, delivering real PDFs, mutating offers/prices, recommending airlines, booking, ticketing, EMD issuance, payment, invoice, settlement, scraping, external AI, or provider execution.

## Phase 37.8 Includes

- Offer decision export manual delivery handoff records, recipient metadata, attachment metadata, instructions, and immutable handoff snapshots.
- Agency UI `/agency/offer-decision-export-deliveries` and APIs under `/api/agencies/{agency_id}/offer-decision-export-deliveries/*` to prepare human-controlled handoff metadata after release readiness.
- Platform UI `/platform/offer-decision-export-deliveries` and APIs under `/api/platform/offer-decision-export-deliveries/*` for read-only governance diagnostics.
- Manual handoff records describe human intent only. They do not send email/SMS, call SMTP/SMS/storage providers, create public links, deliver real PDFs, mutate offers/prices, recommend airlines, book, create or alter PNRs, ticket, issue EMDs, invoice, charge, settle, scrape, call external AI, or execute providers.

## Phase 37.9 Includes

- Offer decision export manual delivery outcome records, manual outcome events, receipt metadata, issue metadata, and immutable outcome snapshots.
- Agency UI `/agency/offer-decision-export-delivery-outcomes` and APIs under `/api/agencies/{agency_id}/offer-decision-export-delivery-outcomes/*` to record human-controlled delivery outcomes after manual handoff.
- Platform UI `/platform/offer-decision-export-delivery-outcomes` and APIs under `/api/platform/offer-decision-export-delivery-outcomes/*` for read-only governance diagnostics.
- Outcome tracking records are metadata-only and human-recorded. They do not send email/SMS, create public links, deliver real PDFs, mutate offers/prices, recommend airlines, book, create or alter PNRs, ticket, issue EMDs, invoice, charge, settle, scrape, call external AI, or execute providers.

## Phase 38.0 Includes

- Offer decision export audit review records, findings, checklist items, and immutable review snapshots.
- Agency UI `/agency/offer-decision-export-audit-reviews` and APIs under `/api/agencies/{agency_id}/offer-decision-export-audit-reviews/*` to review lifecycle completeness, approval trail, handoff trail, outcome trail, unresolved issues, and snapshot coverage.
- Platform UI `/platform/offer-decision-export-audit-reviews` and APIs under `/api/platform/offer-decision-export-audit-reviews/*` for read-only governance diagnostics.
- Architecture note: `docs/architecture/offer-decision-export-audit-review-foundation.md`.
- Audit reviews are metadata-only. They do not send email/SMS, create public links, deliver real PDFs, mutate offers/prices, recommend airlines, book, create or alter PNRs, ticket, issue EMDs, invoice, charge, settle, scrape, call external AI, or execute providers.

## Phase 38.1 Includes

- Offer decision export governance records, rules, retention policy metadata, legal basis metadata, archive status metadata, governance exceptions, and immutable governance snapshots.
- Agency UI `/agency/offer-decision-export-governance` and APIs under `/api/agencies/{agency_id}/offer-decision-export-governance/*` to record human-reviewed governance metadata over export audit review lifecycles.
- Platform UI `/platform/offer-decision-export-governance` and APIs under `/api/platform/offer-decision-export-governance/*` for read-only governance diagnostics.
- Architecture note: `docs/architecture/offer-decision-export-governance-foundation.md`.
- Governance records are metadata-only. They do not send email/SMS, create public links, deliver real PDFs, mutate offers/prices, recommend airlines, book, create or alter PNRs, ticket, issue EMDs, invoice, charge, settle, scrape, call external AI, or execute providers.

## Phase 38.2 Includes

- Offer decision export compliance evidence records, compliance requirements, performed checks, pass/fail result metadata, compliance exceptions, and immutable compliance snapshots.
- Agency UI `/agency/offer-decision-export-compliance` and APIs under `/api/agencies/{agency_id}/offer-decision-export-compliance/*` to prove why an export satisfies governance requirements.
- Platform UI `/platform/offer-decision-export-compliance` and APIs under `/api/platform/offer-decision-export-compliance/*` for read-only compliance diagnostics.
- Architecture note: `docs/architecture/offer-decision-export-compliance-foundation.md`.
- Compliance evidence records are metadata-only. They do not send email/SMS/notifications, create public links, deliver PDFs/documents, mutate offers/prices, recommend airlines, book, create or alter PNRs, ticket, issue EMDs, invoice, charge, settle, execute GDS/provider actions, scrape, or call external AI.

## Phase 39.0 Includes

- Airline intelligence data packs, staged pack items, validation issues, import runs, review notes, and coverage snapshots for metadata-only airline data staging.
- Platform UI `/platform/airline-intelligence-data-packs` and APIs under `/api/platform/airline-intelligence-data-packs/*` for guided import, dry-run, validation, review note, and coverage snapshot workflows.
- Agency UI `/agency/airline-intelligence-coverage` and read-only APIs under `/api/agencies/{agency_id}/airline-intelligence-data-packs/*` for simple airline coverage/readiness visibility.
- Architecture note: `docs/architecture/airline-intelligence-data-pack-foundation.md`.
- Data packs prepare future CRM, offer builder, agency website/CMS, client portal, fare, fleet, route, and special-services workflows while remaining staged metadata. They do not scrape, call external APIs or external AI, auto-promote into operational airline tables, publish CMS/client portal content, recommend airlines, book, mutate PNRs, ticket, issue EMDs, charge, invoice, settle, send messages, or execute providers.

## Phase 39.1 Includes

- Airline intelligence data pack review records, checklist items, field mappings, duplicate/conflict metadata, promotion-readiness records, and immutable review snapshots.
- Platform UI `/platform/airline-intelligence-data-pack-reviews` and APIs under `/api/platform/airline-intelligence-data-pack-reviews/*` for human review, approval/rejection metadata, field mapping, conflict detection, and promotion-readiness marking.
- Agency UI `/agency/airline-intelligence-review-coverage` and read-only APIs under `/api/agencies/{agency_id}/airline-intelligence-data-pack-reviews/*` for plain-language safe-use coverage summaries.
- Architecture note: `docs/architecture/airline-intelligence-data-pack-review-foundation.md`.
- Promotion readiness is a metadata status only. Phase 39.1 does not promote staged data into operational airline tables, scrape, call external APIs or external AI, publish CMS/client portal content, recommend airlines, book, mutate PNRs, ticket, issue EMDs, charge, invoice, settle, or execute providers.

## Phase 39.2 Includes

- Airline intelligence knowledge versions, version items, release channels, release assignments, comparisons, rollback plans, and immutable version snapshots.
- Platform UI `/platform/airline-intelligence-knowledge-versions` and APIs under `/api/platform/airline-intelligence-knowledge-versions/*` for governed version creation, item inclusion, freeze/approve/published-metadata status, release-channel metadata, comparisons, rollback planning, and snapshots.
- Agency UI `/agency/airline-intelligence-knowledge-versions` and read-only APIs under `/api/agencies/{agency_id}/airline-intelligence-knowledge-versions/*` for current/preview version visibility and plain-language change summaries.
- Architecture note: `docs/architecture/airline-intelligence-knowledge-versioning-foundation.md`.
- Publication control is metadata only. Phase 39.2 does not promote staged data into operational airline tables, scrape, call external APIs or external AI, publish CMS/client portal content, recommend airlines, book, mutate PNRs, ticket, issue EMDs, charge, invoice, settle, send automatically, or execute providers.

## Phase 39.3 Includes

- Airline intelligence agency consumption profiles, agency assignment views, usage readiness records, consumption notes, and immutable consumption snapshots.
- Platform UI `/platform/airline-intelligence-agency-consumption` and APIs under `/api/platform/airline-intelligence-agency-consumption/*` for governance of agency safe-use metadata over knowledge versions.
- Agency UI `/agency/airline-intelligence-consumption` and read-only APIs under `/api/agencies/{agency_id}/airline-intelligence-consumption/*` for plain-language CRM, agency website, client portal, and offer builder safe-use visibility.
- Architecture note: `docs/architecture/airline-intelligence-agency-consumption-bridge.md`.
- Consumption bridge records are metadata only. Phase 39.3 does not publish CMS/client portal content, recommend airlines, book, mutate PNRs, ticket, issue EMDs, charge, invoice, settle, scrape, call external APIs or external AI, send automatically, or execute providers.

## Phase 39.4 Includes

- Plain-language Platform Console grouping for SaaS/agencies, airline intelligence governance, agency website/CMS governance, CRM/client portal governance, offer/document governance, and system readiness.
- Plain-language Agency Workspace grouping for daily work, clients/passengers, requests/offers/trips, website/CMS, airline intelligence visibility, documents/delivery, and settings.
- Shared frontend module catalog for route descriptions, audience labels, helper badges, and safety status used by the platform and agency shells.
- Architecture note: `docs/architecture/platform-agency-ux-consolidation.md`.
- UX consolidation is metadata only. Phase 39.4 does not add routes, publish CMS/client portal content, recommend airlines, book, mutate PNRs, ticket, issue EMDs, charge, invoice, settle, scrape, call external APIs or external AI, send automatically, or execute providers.

## Phase 39.5 Includes

- SaaS subscription plans, plan entitlements, agency subscription assignments, entitlement readiness rows, review notes, and immutable subscription snapshots.
- Platform UI `/platform/saas-subscriptions` and APIs under `/api/platform/saas-subscriptions/*` for plan and entitlement metadata governance.
- Agency UI `/agency/saas-subscription` and read-only APIs under `/api/agencies/{agency_id}/saas-subscriptions/*` for “My Subscription” visibility.
- Architecture note: `docs/architecture/saas-subscription-entitlement-foundation.md`.
- Subscription records are metadata only. Phase 39.5 does not add billing, payments, invoices, settlement, automatic charging, Stripe, bank/card/tax/accounting logic, automatic access enforcement, CMS/client portal publishing, recommendations, booking, PNR mutation, ticketing, EMD issuance, scraping, external APIs, external AI, automatic sending, or provider execution.

## Phase 39.6 Includes

- Read-only entitlement visibility summaries by agency/module derived from Phase 39.5 subscription metadata.
- Agency Workspace navigation and dashboard entitlement badges: Included, Limited, Review required, Not included, and Unknown.
- Platform Console subscription review visibility through `/api/platform/saas-subscriptions/entitlement-visibility`.
- Agency read-only module visibility through `/api/agencies/{agency_id}/saas-subscriptions/module-visibility`.
- Architecture note: `docs/architecture/subscription-entitlement-ui-guardrails.md`.
- Subscription visibility is informational only and does not automatically enforce access. Phase 39.6 does not add billing, payment, invoice, settlement, automatic charging, Stripe, bank/card/tax/accounting logic, automatic access enforcement, provider execution, booking, PNR mutation, ticketing, EMD issuance, scraping, external APIs, external AI, or automatic sending.

## Phase 39.7 Includes

- Agency feature flags, feature flag review notes, and immutable feature flag snapshots as metadata-only records.
- Platform UI `/platform/feature-flags` and APIs under `/api/platform/feature-flags/*` for owner review of agency feature visibility.
- Agency UI `/agency/feature-availability` and read-only APIs under `/api/agencies/{agency_id}/feature-flags/*` for Feature Availability visibility.
- Badges for Enabled, Disabled, Hidden, Beta, and Pilot feature states.
- Architecture note: `docs/architecture/agency-feature-flags-foundation.md`.
- Feature visibility is informational only. Phase 39.7 does not add billing, payments, Stripe, taxation, accounting, subscription charging, automatic entitlement enforcement, feature blocking, provider execution, booking, PNR mutation, ticketing, EMD issuance, CMS publishing, client portal publishing, external APIs, scraping, external AI, or automatic sending.

## Phase 39.8 Includes

- Agency feature flag audit history and readiness checklist metadata.
- Platform UI `/platform/feature-flag-audit` and read-only APIs under `/api/platform/feature-flags/audits` and `/api/platform/feature-flags/readiness`.
- Agency UI `/agency/feature-readiness` and read-only APIs under `/api/agencies/{agency_id}/feature-readiness`.
- Readiness checklist metadata for Documentation, Backend, API, UI, Testing, Deployment, and Rollout.
- Architecture note: `docs/architecture/agency-feature-flag-audit-foundation.md`.
- Feature flag readiness and audit metadata is informational only. Phase 39.8 does not enable feature enforcement, block routes, change permissions, affect subscriptions, execute providers, call external APIs, perform billing, publish changes, scrape, call external AI, or send automatically.

## Phase 39.9 Includes

- Reusable feature flag bundle metadata, bundle members, bundle summaries, bundle readiness, and owner-review notes.
- Platform UI `/platform/feature-flag-bundles` and read-only APIs under `/api/platform/feature-flag-bundles`.
- Agency UI `/agency/feature-bundles` and read-only APIs under `/api/agencies/{agency_id}/feature-flag-bundles`.
- Default metadata bundle definitions for Core Agency, CRM, Ticketing, Booking, Airline Intelligence, GDS, Finance, Premium Operations, Beta Features, and Internal Testing.
- Architecture note: `docs/architecture/agency-feature-flag-bundle-foundation.md`.
- Feature flag bundles are informational only. Phase 39.9 does not enable features, run entitlement checks, bill, enforce access, hide modules, decide permissions, publish, roll out changes, execute providers, call external APIs, scrape, call external AI, start background workers, send notifications, or send email.

## Phase 40.0 Includes

- Agency feature bundle assignment metadata and assignment history records.
- Platform UI `/platform/feature-bundle-assignments` and APIs under `/api/platform/feature-bundle-assignments`, `/api/platform/agencies/{agency_id}/bundle-assignments`, and `/api/platform/bundle-assignments/{assignment_id}` for metadata review.
- Agency UI `/agency/assigned-bundles` and read-only APIs under `/api/agencies/{agency_id}/feature-bundle-assignments` and `/api/agencies/{agency_id}/feature-bundle-assignment-history`.
- DELETE marks assignment metadata inactive and preserves history.
- Architecture note: `docs/architecture/feature-bundle-assignment-foundation.md`.
- Feature bundle assignments are informational only. Phase 40.0 does not activate features, evaluate entitlements, enforce permissions, change subscriptions, bill, license, execute feature flags, call providers, call external APIs, call external AI, run background workers, run cron jobs, or deploy anything.

## Phase 40.1 Includes

- Phase 40.1 Feature Bundle Rollout Readiness metadata for assigned bundle operational review.
- Platform UI `/platform/feature-bundle-rollout-readiness` and APIs under `/api/platform/feature-bundle-rollout-readiness`.
- Agency UI `/agency/bundle-rollout-readiness` and read-only APIs under `/api/agencies/{agency_id}/feature-bundle-rollout-readiness`.
- Checklist metadata with `pending`, `passed`, `warning`, and `blocked` item statuses plus readiness status summaries.
- Default readiness views derived from existing Phase 40.0 bundle assignment metadata.
- Architecture note: `docs/architecture/feature-bundle-rollout-readiness-foundation.md`.
- Feature bundle rollout readiness is informational only. Phase 40.1 does not activate or deactivate features, enforce access, block routes, change permissions, bill, publish, send email/SMS, execute providers, call external APIs, scrape, call external AI, run background workers, or run cron jobs.
- Capability catalog metadata as the canonical inventory of AgencyOS functional capabilities.
- Platform UI `/platform/capabilities` and read-only APIs under `/api/platform/capabilities`.
- Agency UI `/agency/capabilities` and read-only APIs under `/api/agencies/{agency_id}/capabilities`.
- Category and module listing metadata for Platform Console filters.
- Informational agency availability labels only. Phase 40.1 does not enforce features, evaluate entitlements, block routes, change permissions, bill, publish, execute providers, call external services, call external APIs, call external AI, run background workers, or run cron jobs.
- Architecture note: `docs/architecture/capability-catalog-foundation.md`.

## Phase 40.2 Includes

- Feature Bundle Rollout Plan metadata for post-readiness planning.
- Platform UI `/platform/feature-bundle-rollout-plans` and APIs under `/api/platform/feature-bundle-rollout-plans` for metadata list/create/update views.
- Agency UI `/agency/rollout-plans` and read-only APIs under `/api/agencies/{agency_id}/feature-bundle-rollout-plans`.
- Rollout stages `draft`, `readiness_review`, `scheduled`, `paused`, and `archived`.
- Optional readiness snapshot and assigned bundle references plus checklist summary counts.
- Architecture note: `docs/architecture/feature-bundle-rollout-plan-foundation.md`.
- Feature bundle rollout plans are informational only. Phase 40.2 does not activate features, enforce access, block routes, publish, send email/SMS/notifications, bill, charge, execute providers, call external APIs, use AI, scrape, run background workers, run cron jobs, or trigger rollout actions.

## Phase 40.3 Includes

- Read-only Rollout Dashboard metadata aggregation across capability catalog, feature flags, feature bundles, assigned bundles, rollout readiness, and rollout plans.
- Platform UI `/platform/rollout-dashboard` and APIs under `/api/platform/rollout-dashboard`.
- Agency UI `/agency/rollout-dashboard` and read-only APIs under `/api/agencies/{agency_id}/rollout-dashboard`.
- Metadata collections `rollout_dashboard_views` and `rollout_dashboard_snapshots` with index registration only.
- Dashboard cards show counts, statuses, and last-updated metadata only.
- Architecture note: `docs/architecture/rollout-dashboard-foundation.md`.
- Rollout Dashboard is informational only. Phase 40.3 does not enforce entitlements, bill, charge, process payments, execute providers, use AI, publish, automate rollouts, start workers, schedule jobs, send email/SMS, activate features, change permissions, block routes, execute webhooks, scrape, or call external APIs.

## Phase 40.4 Includes

- Feature Bundle Rollout Approval metadata for reviewing rollout plans after planning.
- Platform UI `/platform/feature-bundle-rollout-approvals` and APIs under `/api/platform/feature-bundle-rollout-approvals` for metadata list/create/update views, notes, and timeline.
- Agency UI `/agency/rollout-approval` and read-only APIs under `/api/agencies/{agency_id}/feature-bundle-rollout-approvals`.
- Approval statuses `draft`, `submitted`, `under_review`, `approved`, `rejected`, and `archived`.
- Metadata collections `feature_bundle_rollout_approvals` and `feature_bundle_rollout_approval_notes` with index registration only.
- Architecture note: `docs/architecture/feature-bundle-rollout-approval-foundation.md`.
- Rollout approvals are informational only. Phase 40.4 does not enable features, enforce permissions, gate runtime access, bill, use Stripe or payment providers, change authentication, deploy, run cron jobs, run webhooks, start background workers, send email/SMS/notifications, use AI/OpenAI, scrape, publish, or execute rollouts.

## Phase 40.5 Includes

- Feature Bundle Rollout Schedule metadata for intended rollout timing after approval review.
- Platform UI `/platform/feature-bundle-rollout-schedule` and APIs under `/api/platform/feature-bundle-rollout-schedule` for metadata list/create/update views.
- Agency UI `/agency/rollout-schedule` and read-only APIs under `/api/agencies/{agency_id}/feature-bundle-rollout-schedule`.
- Schedule statuses `Planned`, `Ready`, `AwaitingApproval`, `Approved`, `Deferred`, `Cancelled`, and `CompletedMetadata`.
- Metadata collection `feature_bundle_rollout_schedules` with index registration only.
- Architecture note: `docs/architecture/feature-bundle-rollout-schedule-foundation.md`.
- Rollout schedules are informational only. Phase 40.5 does not execute rollouts, activate features, change entitlement behavior, modify permissions, introduce cron jobs, schedulers, workers, queues, timers, background execution, call external APIs, use AI, bill, publish, or trigger rollout actions.

## Phase 40.6 Includes

- Feature Bundle Rollout Timeline metadata for historical rollout plan events.
- Platform UI `/platform/feature-bundle-rollout-timeline` and APIs under `/api/platform/feature-bundle-rollout-timeline` for metadata create/list/detail views.
- Agency UI `/agency/rollout-timeline` and read-only APIs under `/api/agencies/{agency_id}/feature-bundle-rollout-timeline`.
- Event types for plan, approval, schedule, future rollout, rollback, and note history.
- Metadata collection `feature_bundle_rollout_timeline_entries` with index registration only.
- Architecture note: `docs/architecture/feature-bundle-rollout-timeline-foundation.md`.
- Rollout timeline entries are informational only. Phase 40.6 does not enable feature bundles, change agency permissions, execute rollout plans, schedule background jobs, publish, call providers, send emails or notifications, enforce rollout state, modify subscriptions, or introduce automation.

## Phase 40.7 Includes

- Feature Bundle Dependency metadata for informational rollout dependencies.
- Platform UI `/platform/feature-bundle-dependencies` and APIs under `/api/platform/feature-bundle-dependencies` for metadata create/update/delete/list/detail views.
- Agency UI `/agency/bundle-dependencies` and read-only APIs under `/api/agencies/{agency_id}/feature-bundle-dependencies`.
- Dependency types for bundle, capability, approval, rollout plan, schedule, readiness checklist, and other metadata.
- Metadata collection `feature_bundle_dependencies` with index registration only.
- Architecture note: `docs/architecture/feature-bundle-dependency-foundation.md`.
- Feature bundle dependencies are informational only. Phase 40.7 does not execute rollout plans, schedule background jobs, enforce dependencies, block rollouts, activate feature bundles, modify permissions, send notifications, publish, call providers, or introduce automation.

## Phase 40.8 Includes

- Feature Bundle Rollout Risk metadata for tracking rollout concerns such as missing approval, dependency readiness, unclear agency impact, schedule conflicts, incomplete documentation, and operational concerns.
- Platform UI `/platform/feature-bundle-rollout-risks` and APIs under `/api/platform/feature-bundle-rollout-risks` for metadata create/update/delete/list/detail views.
- Agency UI `/agency/rollout-risks` and read-only APIs under `/api/agencies/{agency_id}/feature-bundle-rollout-risks`.
- Risk impact, likelihood, and status metadata with filters by agency, bundle, rollout plan, status, impact, and likelihood.
- Metadata collection `feature_bundle_rollout_risks` with index registration only.
- Architecture note: `docs/architecture/feature-bundle-rollout-risk-register-foundation.md`.
- Feature bundle rollout risks are informational only. Phase 40.8 does not execute rollouts, enforce risk decisions, block anything, send notifications, activate bundles, add automation, or call external providers.

## Phase 40.9 Includes

- Feature Bundle Rollout Issue metadata for tracking things that already went wrong or need attention.
- Platform UI `/platform/feature-bundle-rollout-issues` and APIs under `/api/platform/feature-bundle-rollout-issues` for metadata create/update/delete/list/detail views.
- Agency UI `/agency/rollout-issues` and read-only APIs under `/api/agencies/{agency_id}/feature-bundle-rollout-issues`.
- Issue severity and status metadata with filters by agency, bundle, rollout plan, risk, dependency, approval, severity, and status.
- Metadata collection `feature_bundle_rollout_issues` with index registration only.
- Architecture note: `docs/architecture/feature-bundle-rollout-issue-log-foundation.md`.
- Feature bundle rollout issues are informational only. Phase 40.9 does not execute rollouts, activate bundles, enforce blocking, send notifications, call external providers, or add AI/provider execution.

## Phase 40.10 Includes

- Feature Bundle Rollout Decision metadata for recording rollout plan decisions, reasons, owners, categories, statuses, and related rollout metadata references.
- Platform UI `/platform/feature-bundle-rollout-decisions` and APIs under `/api/platform/feature-bundle-rollout-decisions` for metadata create/update/delete/list/detail views.
- Agency UI `/agency/rollout-decisions` and read-only APIs under `/api/agencies/{agency_id}/feature-bundle-rollout-decisions`.
- Decision filters by rollout, category, owner, and status with related bundle, dependency, risk, issue, and timeline references for read-only visualization.
- Metadata collection `feature_bundle_rollout_decisions` with index registration only.
- Architecture note: `docs/architecture/feature-bundle-rollout-decision-register-foundation.md`.
- Feature bundle rollout decisions are informational only. Phase 40.10 does not execute rollouts, automate deployments, activate features, enforce entitlements, bill, call providers or external APIs, use AI, run workers or schedulers, notify users, send email, execute webhooks, publish, or switch runtime behavior.

## Phase 40.11 Includes

- Feature Bundle Rollout Change Request metadata for recording proposed rollout changes, reasons, requesters, priorities, impact levels, statuses, and related rollout metadata references.
- Platform UI `/platform/feature-bundle-rollout-change-requests` and APIs under `/api/platform/feature-bundle-rollout-change-requests` for metadata create/update/delete/list/detail views.
- Agency UI `/agency/rollout-change-requests` and read-only APIs under `/api/agencies/{agency_id}/feature-bundle-rollout-change-requests`.
- Change request filters by rollout, status, priority, impact level, and change type with affected bundle/feature flag and related decision, risk, issue, and dependency references for read-only visualization.
- Metadata collection `feature_bundle_rollout_change_requests` with index registration only.
- Architecture note: `docs/architecture/feature-bundle-rollout-change-request-foundation.md`.
- Feature bundle rollout change requests are informational only. Phase 40.11 does not execute rollouts, automate deployments, activate features, enforce entitlements, bill, call providers or external APIs, use AI, run workers or schedulers, notify users, send email, execute webhooks, publish, or switch runtime behavior.

## Phase 40.12 Includes

- Feature Bundle Rollout Rollback Plan metadata for recording rollback titles, reasons, triggers, scopes, statuses, priorities, owners, affected records, related rollout metadata references, rollback steps, and validation notes.
- Platform UI `/platform/feature-bundle-rollout-rollback-plans` and APIs under `/api/platform/feature-bundle-rollout-rollback-plans` for metadata create/update/delete/list/detail views.
- Agency UI `/agency/rollout-rollback-plans` and read-only APIs under `/api/agencies/{agency_id}/feature-bundle-rollout-rollback-plans`.
- Rollback plan filters by rollout, status, priority, scope, and owner with affected bundle/feature flag and related change request, decision, risk, issue, and dependency references for read-only visualization.
- Metadata collection `feature_bundle_rollout_rollback_plans` with index registration only.
- Architecture note: `docs/architecture/feature-bundle-rollout-rollback-plan-foundation.md`.
- Feature bundle rollout rollback plans are informational only. Phase 40.12 does not execute rollbacks, automate deployments, activate or deactivate features, enforce entitlements, bill, call providers or external APIs, use AI, run workers or schedulers, notify users, send email, execute webhooks, publish, or switch runtime behavior.

## Phase 40.13 Includes

- Feature Bundle Rollout Summary Pack metadata for read-only evidence-pack views over rollout plans, readiness, approvals, schedules, timelines, dependencies, risks, issues, decisions, change requests, and rollback plans.
- Platform UI `/platform/feature-bundle-rollout-summary-packs` and APIs under `/api/platform/feature-bundle-rollout-summary-packs` for metadata create/update/delete/list/detail views.
- Agency UI `/agency/rollout-summary-packs` and read-only APIs under `/api/agencies/{agency_id}/feature-bundle-rollout-summary-packs`.
- Summary pack filters by rollout, status, audience, and bundle with covered bundle references, evidence notes, and compliance notes.
- Metadata collection `feature_bundle_rollout_summary_packs` with index registration only.
- Architecture note: `docs/architecture/feature-bundle-rollout-summary-pack-foundation.md`.
- Feature bundle rollout summary packs are informational only. Phase 40.13 does not execute rollouts, automate deployments, activate or deactivate features, enforce entitlements, bill, call providers or external APIs, use AI, run workers or schedulers, notify users, send email, execute webhooks, publish, switch runtime behavior, generate PDFs, export files, or automate actions.

## Phase 41.0 Includes

- Operational Travel Workspace metadata for agency-scoped workspace references, client/passenger summaries, linked requests, trips, offers, bookings, tickets, documents, priorities, assignments, travel dates, route summaries, service summaries, and operational notes.
- Platform UI `/platform/operational-travel-workspaces` and APIs under `/api/platform/operational-travel-workspaces` for metadata create/update/archive/list/detail views.
- Agency UI `/agency/travel-workspaces` and read-only APIs under `/api/agencies/{agency_id}/operational-travel-workspaces`.
- Workspace filters by agency, status, type, priority, assigned agent, and travel date.
- Metadata collection `operational_travel_workspaces` with index registration only.
- Architecture note: `docs/architecture/operational-travel-workspace-foundation.md`.
- Operational travel workspaces are informational only. Phase 41.0 does not execute bookings, issue tickets, connect to live GDS or NDC, process payments, send email or SMS, run AI automation, call external APIs, integrate suppliers, call live airlines, run background workers, or automate travel operations.

## Phase 41.1 Includes

- Travel Request Workspace metadata for agency-scoped request references inside operational workspaces, requester details, client/passenger summaries, requested route and dates, passenger summaries, service categories, budget/deadline notes, assignments, linked trips, linked offers, linked documents, and internal notes.
- Platform UI `/platform/travel-request-workspaces` and APIs under `/api/platform/travel-request-workspaces` for metadata create/update/archive/list/detail views.
- Agency UI `/agency/travel-requests` and read-only APIs under `/api/agencies/{agency_id}/travel-request-workspaces`.
- Request filters by agency, status, type, priority, assigned agent, departure date, and operational workspace.
- Metadata collection `travel_request_workspaces` with index registration only.
- Architecture note: `docs/architecture/travel-request-workspace-foundation.md`.
- Travel request workspaces are informational only. Phase 41.1 does not execute bookings, issue tickets, connect to live GDS or NDC, process payments, send email or SMS, run AI automation, call external APIs, integrate suppliers, call live airlines, run background workers, automatically convert requests to trips, automatically create offers, or automate travel operations.

## Phase 41.2 Includes

- Passenger Workspace metadata for agency-scoped passenger references, assigned operational workspaces, passenger status, personal information, travel documents, loyalty memberships, known traveler numbers, emergency contact details, medical, mobility, assistance, dietary, baggage, seating, language, contact, linked operational records, and internal notes.
- Platform UI `/platform/passenger-workspaces` and APIs under `/api/platform/passenger-workspaces` for metadata create/update/archive/list/detail views.
- Agency UI `/agency/passenger-workspaces` and read-only APIs under `/api/agencies/{agency_id}/passenger-workspaces`.
- Passenger filters by status, nationality, citizenship, assistance profile, travel date, and assigned operational workspace.
- Metadata collection `passenger_workspaces` with index registration only.
- Architecture note: `docs/architecture/passenger-workspace-foundation.md`.
- Passenger workspaces are informational only. Phase 41.2 does not execute bookings, issue tickets, connect to GDS or NDC, process payments, integrate suppliers, use AI, send email or SMS, run background workers, call external APIs, automatically match profiles, automatically validate documents, communicate with airlines, or automate passenger operations.

## Phase 41.3 Includes

- Flight Workspace metadata for agency-scoped flight references, assigned operational workspaces, flight status/type/direction, airline and carrier details, flight numbers, departure/arrival airports and terminals, schedule metadata, aircraft, cabin, booking class, fare family, baggage, connection, stopover, elapsed time, operating days, passengers, linked operational records, and operational notes.
- Platform UI `/platform/flight-workspaces` and APIs under `/api/platform/flight-workspaces` for metadata create/update/archive/list/detail views.
- Agency UI `/agency/flight-workspaces` and read-only APIs under `/api/agencies/{agency_id}/flight-workspaces`.
- Flight filters by status, airline, departure airport, arrival airport, departure date, cabin, booking class, and assigned operational workspace.
- Metadata collection `flight_workspaces` with index registration only.
- Architecture note: `docs/architecture/flight-workspace-foundation.md`.
- Flight workspaces are informational only. Phase 41.3 does not execute bookings, search live flights, connect to GDS or NDC, call airline APIs, process payments, issue tickets, synchronize schedules, call external APIs, use AI, run background workers, automatically generate routes, validate flights, look up airlines, update live schedules, or automate flight operations.

## Phase 41.4 Includes

- Trip Workspace metadata for agency-scoped journey records, assigned operational workspaces, trip references, journey/service type, clients, passenger summaries, flight summaries, linked requests, offers, bookings, tickets, EMDs, documents, route metadata, travel dates, itinerary/baggage/service summaries, assignment, and operational notes.
- Platform UI `/platform/trip-workspaces` and APIs under `/api/platform/trip-workspaces` for metadata create/update/archive/list/detail views.
- Agency UI `/agency/trip-workspaces` and read-only APIs under `/api/agencies/{agency_id}/trip-workspaces`.
- Trip filters by status, departure country, destination country, departure date, assigned agent, priority, and assigned operational workspace.
- Metadata collection `trip_workspaces` with index registration only.
- Architecture note: `docs/architecture/trip-workspace-foundation.md`.
- Trip workspaces are informational only. Phase 41.4 does not execute bookings, issue tickets, connect to GDS or NDC, call airline APIs, process payments, create invoices, use AI, run background workers, automatically generate trips, automatically generate itineraries, call external integrations, or automate journey operations.

## Phase 41.5 Includes

- Offer Workspace metadata for agency-scoped proposal records, assigned operational/trip workspaces, offer references, status/type, clients, passenger summaries, flight summaries, trip summaries, itinerary and pricing summaries, taxes, fees, ancillary, baggage, seat, meal, hotel, transfer, insurance, validity, linked booking/ticket/document references, and agent/customer/internal notes.
- Platform UI `/platform/offer-workspaces` and APIs under `/api/platform/offer-workspaces` for metadata create/update/archive/list/detail views.
- Agency UI `/agency/offer-workspaces` and read-only APIs under `/api/agencies/{agency_id}/offer-workspaces-v2`.
- Offer filters by status, validity, client, destination, price range, assigned agent, and assigned trip workspace.
- Metadata collection `offer_workspaces_v2` with index registration only.
- Architecture note: `docs/architecture/offer-workspace-foundation.md`.
- Offer workspaces are informational only. Phase 41.5 does not execute bookings, issue tickets, process payments, connect to GDS or NDC, call airline APIs, calculate fares, generate AI itineraries, integrate suppliers, call external APIs, automatically convert bookings, run background workers, or automate proposal operations.

## Phase 41.6 Includes

- Booking Workspace metadata for agency-scoped booking records, assigned operational/trip/offer workspaces, booking references, statuses, owners, airline PNRs, GDS locators, supplier references, passenger summaries, flight summaries, ticket links, EMD links, SSR links, OSI links, documents, timeline references, communications, payment summaries, booking summaries, and operational notes.
- Platform UI `/platform/booking-workspaces` and APIs under `/api/platform/booking-workspaces` for metadata create/update/archive/list/detail views.
- Agency UI `/agency/booking-workspaces` and read-only APIs under `/api/agencies/{agency_id}/booking-workspaces`.
- Booking filters by status, booking owner, airline, supplier, and booking date.
- Metadata collection `booking_workspaces` is extended with additive index registration only.
- Architecture note: `docs/architecture/booking-workspace-foundation.md`.
- Booking workspaces are informational only. Phase 41.6 does not create live bookings, issue tickets, connect to GDS or NDC, call airline APIs, process payments, calculate fares, use AI, run background workers, automatically confirm bookings, automatically generate tickets, integrate external providers, call external APIs, or automate booking operations.

## Phase 41.7 Includes

- Ticket Workspace metadata for agency-scoped ticket records, assigned operational/trip/offer/booking workspaces, ticket references, workspace statuses, whole-ticket document statuses, ticket numbers, validating carriers, issuing metadata, passengers, booking references, airline PNRs, GDS locators, flight links, fare basis summaries, fare calculation line/NUC/ROE metadata, equivalent fare paid metadata, form of payment, tax breakdown, pricing units, fare components, coupon status summaries, per-coupon details with coupon-level fare basis, baggage, endorsements, restrictions, exchange/refund/void reference ids, linked EMDs, linked documents, lifecycle notes, and operational notes.
- Platform UI `/platform/ticket-workspaces` and APIs under `/api/platform/ticket-workspaces` for metadata create/update/archive/list/detail views.
- Agency UI `/agency/ticket-workspaces` and read-only APIs under `/api/agencies/{agency_id}/ticket-workspaces`.
- Ticket filters by workspace status, ticket document status, validating carrier, issue date, passenger, booking reference, and currency.
- Metadata collection `ticket_workspaces` with additive index registration only.
- Architecture note: `docs/architecture/ticket-workspace-foundation.md`.
- Ticket workspaces are informational only. Phase 41.7 does not issue tickets, reissue tickets, void tickets, process refunds, process exchanges, process payments, connect to GDS or NDC, call airline APIs, calculate or recalculate fares, validate tickets or coupons automatically, run background workers, integrate external providers, call external APIs, or automate ticket operations.

## Phase 41.8 Includes

- EMD Workspace metadata for agency-scoped EMD records, assigned operational/trip/offer/booking/ticket workspaces, EMD references, workspace statuses, whole-EMD document statuses, EMD numbers, EMD-A/EMD-S metadata, validating carriers, issuing metadata, passengers, booking references, airline PNRs, GDS locators, associated ticket/coupon and flight links, SSR/OSI links, ancillary service links, RFIC/RFISC service metadata, EMD coupon status summaries, EMD coupon details, fare/tax/payment metadata, exchange/refund/void reference ids, linked documents, lifecycle notes, and operational notes.
- Platform UI `/platform/emd-workspaces` and APIs under `/api/platform/emd-workspaces` for metadata create/update/archive/list/detail views.
- Agency UI `/agency/emd-workspaces` and read-only APIs under `/api/agencies/{agency_id}/emd-workspaces`.
- EMD filters by workspace status, EMD type, EMD-A/EMD-S, validating carrier, passenger, RFIC, RFISC, service category, and issue date.
- Metadata collection `emd_workspaces` with additive index registration only.
- Architecture note: `docs/architecture/emd-workspace-foundation.md`.
- EMD workspaces are informational only. Phase 41.8 does not issue EMDs, exchange EMDs, refund EMDs, void EMDs, validate RFIC/RFISC, transmit SSR/OSI, process payments, connect to GDS or NDC, call airline APIs, run background workers, integrate external providers, call external APIs, create duplicate EMD architecture, or automate EMD operations.

## Phase 41.9 Includes

- SSR / OSI Operational Workspace metadata for agency-scoped passenger service operations, including passenger need, service classification, SSR/OSI metadata, airline handling, airport handling, approval metadata, EMD/RFIC/RFISC references, document and MEDIF requirements, tasks, timelines, communications, readiness, missing requirements, unresolved items, flights, documents, and notes.
- Platform UI `/platform/ssr-osi-workspaces` and APIs under `/api/platform/ssr-osi-workspaces` for metadata create/update/archive/list/detail views.
- Agency UI `/agency/passenger-services` and read-only APIs under `/api/agencies/{agency_id}/ssr-osi-workspaces`.
- SSR / OSI filters by need category, airline, approval status, readiness, passenger, priority, RFIC, and RFISC.
- Metadata collection `ssr_osi_workspaces` with additive index registration only.
- AOIE input path documentation: Passenger Need -> SSR / OSI Workspace -> Airline Knowledge -> Capability Matrix -> Operational Feasibility -> Offer Builder.
- Architecture note: `docs/architecture/ssr-osi-operational-workspace-foundation.md`.
- SSR / OSI workspaces are informational only. Phase 41.9 does not transmit SSRs, transmit OSIs, connect to GDS or NDC, call airline APIs, recommend with AI, automatically approve airline services, issue EMDs, run background workers, integrate external providers, call external APIs, or automate passenger service operations.

## Phase 42.0 Includes

- Document Workspace metadata for agency-scoped operational documents, including passenger/request/trip/booking/ticket/EMD/SSR-OSI links, operational intelligence references, document type/status/category, travel/airline/airport/authority requirements, deadlines, received and verification statuses, validity, storage references, package/render/share references, visibility, missing/rejection reasons, and operational notes.
- Platform UI `/platform/document-workspaces` and APIs under `/api/platform/document-workspaces` for metadata create/update/archive/list/detail views.
- Agency UI `/agency/document-workspaces` and read-only APIs under `/api/agencies/{agency_id}/document-workspaces`.
- Document filters by type, status, passenger, booking reference, related service, required-for-travel, verification status, and deadline.
- Metadata collection `document_workspaces` with additive index registration only.
- Architecture note: `docs/architecture/document-workspace-foundation.md`.
- Document workspaces are informational only and do not duplicate the Phase 36.5 render/package/share foundation. Phase 42.0 does not deliver documents, implement e-signature, create public share links, generate PDFs automatically, generate payments or invoices, integrate external storage, run background workers, use AI document generation, or automate document operations.

## Phase 42.1 Includes

- Operational Timeline metadata for agency-scoped operational history, including passenger/request/trip/booking/ticket/EMD/SSR-OSI/document workspace links, event type/category/source/status/priority, operational stage/result, airline/airport context, communication summaries, approval references, due/completed dates, reminder flags, visibility, attachment references, and operational notes.
- Platform UI `/platform/operational-timelines` and APIs under `/api/platform/operational-timelines` for metadata create/update/archive/list/detail views.
- Agency UI `/agency/timeline` and read-only APIs under `/api/agencies/{agency_id}/operational-timelines`.
- Timeline filters by passenger, booking, ticket, EMD, SSR / OSI, airline, communication type, event type, priority, status, and date.
- Metadata collection `operational_timelines` with additive index registration only.
- Architecture note: `docs/architecture/operational-timeline-workspace-foundation.md`.
- Operational timeline entries are informational only. Phase 42.1 does not send email, send SMS, use WhatsApp, Teams, or Slack, send live airline or customer messages, summarize with AI, run background workers, integrate providers, call external APIs, or automate operational actions.

## Phase 42.2 Includes

- Passenger Service Workflow metadata for agency-scoped service case coordination, including passenger/request/trip/booking/ticket/EMD/SSR-OSI/document/timeline workspace links, current/previous/next stages, readiness state, blocking and completed requirements, responsible team/agent, airline and priority filter metadata, timeline dates, future AOIE recommendation-pack reference, and operational notes.
- Platform UI `/platform/passenger-service-workflows` and APIs under `/api/platform/passenger-service-workflows` for metadata create/update/archive/list/detail views.
- Agency UI `/agency/workflow-engine` and read-only APIs under `/api/agencies/{agency_id}/passenger-service-workflows`.
- Workflow filters by workflow stage, readiness, passenger, airline, priority, and assigned agent.
- Metadata collection `passenger_service_workflows` with additive index registration only.
- Architecture note: `docs/architecture/passenger-service-workflow-engine-foundation.md`.
- The engine coordinates Passenger -> Service Requirement -> Operational Workspaces -> Timeline -> Future AOIE -> Operational Execution as metadata only. Phase 42.2 does not execute workflows, make AI decisions, run background workers, call airline/GDS/NDC APIs, approve, ticket, issue EMDs, message, integrate providers, or automate actions.

## Phase 50.0 Includes

- Phase 50.0 Airline Operational Intelligence Engine architecture foundation remains architecture-only metadata.
- Airline Operational Intelligence Engine architecture metadata for the passenger service operations principle: Passenger -> Need -> Service Requirement -> Airline Capability -> Operational Feasibility -> Pricing / Conditions -> Recommendation -> Fulfilment.
- Deterministic architecture seed record in `airline_operational_intelligence_architecture`.
- Platform UI `/platform/airline-operational-intelligence` and read-only APIs under `/api/platform/airline-operational-intelligence`.
- Agency UI `/agency/operational-intelligence` and read-only APIs under `/api/agencies/{agency_id}/airline-operational-intelligence`.
- Chapter 50 AOIE roadmap through Phase 50.9, including operational evaluation, feasibility, recommendation, and intelligent offer builder integration metadata, with next operational hardening still tracked separately.
- Architecture notes: `docs/architecture/airline-operational-intelligence-engine-foundation.md` and `docs/architecture/passenger-service-operations-principle.md`.
- AOIE is architecture and governance only. Phase 50.0 does not run AI generation, scrape airlines, crawl the web, call live airline APIs, integrate providers, execute pricing engines, search itineraries, book, issue tickets, issue EMDs, automate recommendations, run background workers, call external APIs, or automate operational actions.

## Phase 50.1 Includes

- Airline Knowledge Acquisition metadata for manually entered trusted airline policy/source evidence, including acquisition status/type/version, airline metadata, source metadata, raw source text, excerpts, source notes, service classification, SSR/OSI relevance, RFIC/RFISC, review status, approval status, versioning links, future AOIE links, operational links, and internal notes.
- Airline Operational Knowledge Graph metadata with independent Evidence, Policy, Pricing, Capability, and Operational Constraints & Procedures pillars. Capability is separate from policy and pricing, and operational constraints are generic condition/operator/value/outcome records for future reasoning over combined conditions.
- Structured animal transport, extra-seat, and cabin capability metadata for future AOIE review without execution.
- Platform UI `/platform/airline-knowledge-acquisition` and APIs under `/api/platform/airline-knowledge-acquisition` for metadata create/update/archive/list/detail views.
- Agency UI `/agency/knowledge-acquisition` and read-only APIs under `/api/agencies/{agency_id}/airline-knowledge-acquisition`.
- Filters by airline, service domain, service family, SSR code, RFIC, RFISC, source type, review status, approval status, effective date, and official source flag.
- Metadata collection `airline_knowledge_acquisitions` with additive index registration only.
- Architecture note: `docs/architecture/airline-knowledge-acquisition-workspace-foundation.md`.
- Phase 50.1 feeds Phase 50.2 Operational Constraint Engine metadata, Phase 50.3 Airline Operational Knowledge Normalisation metadata, Phase 50.4 Airline Operational Knowledge Governance metadata, Phase 50.5 Airline Operational Capability Matrix metadata, Phase 50.6 Operational Knowledge Evaluation metadata, Phase 50.7 Passenger Service Feasibility metadata, and future 50.8 Airline & Itinerary Recommendation Engine and 50.9 Offer Builder Intelligence Integration metadata. It stores Airline Operational Knowledge and does not decide operational feasibility. Future AOIE should reason over the Operational Knowledge Graph, operational constraints, canonical vocabulary, governed versions/releases, capabilities, policies, pricing, evidence, evaluation results, and feasibility records, not raw text alone.
- Phase 50.1 does not run AI parsing, automatic extraction, web scraping, web crawling, airline website automation, provider integrations, live airline APIs, recommendation engines, feasibility engines, pricing calculation engines, background workers, parser execution, external API calls, or automation.

## Phase 50.2 Includes

- Metadata-only Operational Constraint Engine records for the formal AOIE constraint language, including condition groups, supported operators, outcomes, applicability, priority/preference, governance, future evaluation notes, and operational links.
- Platform UI `/platform/operational-constraints` and APIs under `/api/platform/operational-constraints` for metadata create/update/archive/list/detail views.
- Agency UI `/agency/operational-constraints` and read-only APIs under `/api/agencies/{agency_id}/operational-constraints`.
- Metadata collection `operational_constraints` with additive index registration only.
- Architecture note: `docs/architecture/operational-constraint-engine-foundation.md`.
- Phase 50.2 does not run live rule execution, AI reasoning, recommendations, feasibility scoring, pricing calculation, parser execution, scraping, background workers, provider integrations, external APIs, or evaluation endpoints.

## Phase 50.3 Includes

- Metadata-only Airline Knowledge Normalisation records for canonical operational vocabulary and taxonomy.
- Canonical record, taxonomy hierarchy, aliases/terms, applicability, animal taxonomy, aircraft/cabin taxonomy, service taxonomy, units, knowledge links, and governance metadata.
- Platform UI `/platform/airline-knowledge-normalisation` and APIs under `/api/platform/airline-knowledge-normalisation` for metadata create/update/archive/list/detail views.
- Agency UI `/agency/knowledge-normalisation` and read-only APIs under `/api/agencies/{agency_id}/airline-knowledge-normalisation`.
- Metadata collection `airline_knowledge_normalisations` with additive index registration only.
- Architecture note: `docs/architecture/airline-knowledge-normalisation-foundation.md`.
- Phase 50.3 does not run live evaluation, AI parsing, recommendations, feasibility scoring, pricing calculation, scraping, background workers, provider integrations, external APIs, or automation.

## Phase 50.4 Includes

- Metadata-only Airline Operational Knowledge Governance and Version Control records.
- Independent version metadata for Evidence, Policy, Pricing, Capability, Operational Constraints, and Operational Procedures.
- Grouped Knowledge Release metadata, release lifecycle metadata, future AOIE readiness flags, rollback references, superseded references, and historical lookup metadata.
- Version comparison metadata for added, modified, removed, changed effective dates, changed pricing, changed capability, changed operational constraints, and changed procedures.
- Platform UI `/platform/airline-knowledge-governance` and `/platform/airline-knowledge-releases` plus APIs under `/api/platform/airline-knowledge-governance` for metadata create/update/archive/list/detail views.
- Agency UI `/agency/knowledge-governance` and read-only APIs under `/api/agencies/{agency_id}/airline-knowledge-governance`.
- Metadata collections `airline_knowledge_versions` and `airline_knowledge_releases` with additive index registration only.
- Architecture note: `docs/architecture/airline-operational-knowledge-governance-foundation.md`.
- Phase 50.4 does not run live rule evaluation, AI reasoning, parser execution, recommendations, pricing calculation, provider integrations, background workers, automatic publication, external APIs, or automation.

## Phase 50.5 Includes

- Metadata-only Airline Operational Capability Matrix records for what airlines can operationally deliver.
- Capability metadata by airline, service, aircraft, cabin, airport, route, country, season, interline/codeshare context, operational restriction, confidence level, evidence references, and governance references.
- Capability remains different from policy: policy says whether a service may be allowed, capability records whether the airline can operationally deliver it under stated conditions.
- Platform UI `/platform/airline-capability-matrix` and APIs under `/api/platform/airline-capability-matrix` for metadata create/update/archive/list/detail views.
- Agency UI `/agency/capability-matrix` and read-only APIs under `/api/agencies/{agency_id}/airline-capability-matrix`.
- Filters by airline, service domain/family, SSR, RFIC, RFISC, aircraft family, cabin, airport, route, country, season, capability status, operational risk, confidence level, and effective date.
- Metadata collection `airline_capability_matrix` with additive index registration only.
- Architecture note: `docs/architecture/airline-operational-capability-matrix-foundation.md`.
- Phase 50.5 does not evaluate passenger cases, score feasibility, rank airlines, reason with AI, execute parsers, calculate pricing, call providers, run background workers, scrape, publish automatically, or automate decisions. Phase 50.6 consumes the matrix for operational knowledge evaluation metadata, and Phase 50.7 consumes evaluation outputs for passenger service feasibility.

## Phase 50.6 Includes

- Metadata-only Operational Knowledge Evaluation records for deterministic, explainable evaluation of airline operational knowledge against passenger operational requirements.
- Platform UI `/platform/operational-evaluations` and APIs under `/api/platform/operational-evaluations` for metadata create/update/archive/list/detail views.
- Agency UI `/agency/operational-evaluations` and read-only APIs under `/api/agencies/{agency_id}/operational-evaluations`.
- Evaluation metadata for passenger context, trip context, airline context, knowledge sources, evaluation scope, capability, policy, pricing, constraints, operational procedures, operational outcome, required operational actions, evidence trace, risk, lifecycle, and notes.
- Metadata collection `operational_knowledge_evaluations` with additive index registration only.
- Architecture note: `docs/architecture/operational-knowledge-evaluation-engine-foundation.md`.
- Evaluation is not recommendation. Evaluation determines what operationally applies from evidence-backed knowledge acquisition, normalisation, operational constraints, governance, and capability matrix metadata. Phase 50.6 does not determine passenger feasibility, rank airlines, generate itineraries, use AI or LLM prompts, search flights, book, ticket, execute parsers, optimise pricing, call providers, run background workers, or automate decisions.

## Phase 50.7 Includes

- Metadata-only Passenger Service Feasibility records that consume Operational Knowledge Evaluation Results from Phase 50.6.
- Platform UI `/platform/passenger-service-feasibility` and APIs under `/api/platform/passenger-service-feasibility` for metadata create/update/archive/list/detail views.
- Agency UI `/agency/service-feasibility` and read-only APIs under `/api/agencies/{agency_id}/passenger-service-feasibility`.
- Feasibility metadata for passenger context, trip / itinerary context, airline context, evaluation links, feasibility outcomes, satisfied/conditional/unsatisfied/unknown requirements, required actions, operational risk, evidence/evaluation/decision trace, confidence, lifecycle, and notes.
- Metadata collection `passenger_service_feasibilities` with additive index registration only.
- Architecture note: `docs/architecture/passenger-service-feasibility-engine-foundation.md`.
- Feasibility is not Boolean, not recommendation, advisory, evidence-linked, and subject to final human authority. Recommendation is separate Phase 50.8 metadata. Phase 50.7 does not rank airlines, search flights, book, ticket, call providers, use AI or LLM prompts, execute parsers, optimise pricing, run background workers, or automate decisions.

## Phase 50.8 Includes

- Metadata-only Airline Recommendation records that consume Passenger Service Feasibility from Phase 50.7.
- Platform UI `/platform/airline-recommendations` and APIs under `/api/platform/airline-recommendations` for metadata create/update/archive/list/detail views.
- Agency UI `/agency/recommendations` and read-only APIs under `/api/agencies/{agency_id}/airline-recommendations`.
- Recommendation metadata for passenger context, trip and itinerary context, airline context, feasibility/evaluation/capability/knowledge/evidence references, recommendation rank/status/summary, operational scores, commercial reference scores, recommendation level, explanation, required actions, comparison matrix, evidence, trace, lifecycle, and notes.
- Metadata collection `airline_recommendations` with additive index registration only.
- Architecture note: `docs/architecture/airline-recommendation-engine-foundation.md`.
- Recommendation is not feasibility, not booking, not search, advisory, and subject to final human authority. Phase 50.8 does not run live GDS or NDC search, book, issue tickets or EMDs, call providers, execute parsers, generate AI/LLM text, generate prices, run background workers, or automate decisions.

## Phase 50.9 Includes

- Metadata-only Intelligent Offer Builder packages that consume approved recommendations, feasibility, operational evaluations, capability matrix records, knowledge versions, and evidence references.
- Platform UI `/platform/intelligent-offer-builder` and APIs under `/api/platform/intelligent-offer-builder` for metadata create/update/archive/list/detail views.
- Agency UI `/agency/offer-intelligence` and APIs under `/api/agencies/{agency_id}/offer-intelligence` for agency-scoped metadata create/update/archive/list/detail views.
- Package metadata for overview, passenger context, trip / request context, offer context, intelligence inputs, recommended options, operational readiness, required actions, pricing / cost references, client explanation, internal explanation, decision pack, lifecycle, and notes.
- Metadata collection `intelligent_offer_builder_packages` with additive index registration only.
- Architecture note: `docs/architecture/intelligent-offer-builder-integration-foundation.md`.
- Offer Builder should not invent intelligence. Phase 50.9 does not run live GDS or NDC search, book, issue tickets or EMDs, call providers, execute parsers, generate AI/LLM text, generate prices, run background workers, send offers automatically, or automate decisions.

## Intentionally Not Included Yet

- Public share links.
- Payment gateway processing.
- Full accounting or ledger reconciliation.
- Automated booking, PNR creation, ticketing, GDS, NDC, OTA, or supplier integrations.
- Airline scraping, external AI policy extraction or taxonomy/mechanics/pricing/comparison mapping, automated policy evaluation, automatic global policy/taxonomy/mechanics/pricing/comparison promotion, SSR/OSI/EMD/payment execution, automatic airline recommendation execution, invoice/payment/settlement execution from estimates, live flight shopping, and automated live pricing.
- Automatic staff invitation sending unless explicitly enabled in a future production delivery phase.

## Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn server:app --reload
```

The backend starts on `http://localhost:8000`.

By default the API uses in-memory storage so the current foundation can run without a database. This is only a local demo/dev fallback; data is lost on restart:

```bash
AEROASSIST_DB_MODE=memory
```

To use MongoDB locally:

```bash
docker compose up -d mongo
AEROASSIST_DB_MODE=mongo uvicorn server:app --reload
```

MongoDB mode is the documented durable storage path for this phase. Startup creates recommended indexes for agency-owned collections, global records, portal mappings, airline intelligence, documents, and audit events. The environment variables are:

```bash
AEROASSIST_DB_MODE=mongo
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=aeroassist_agencyos
APP_ENV=development
DEMO_AUTH_ENABLED=true
SEED_ON_STARTUP=true
SEED_ENDPOINT_ENABLED=true
DOCUMENT_EXPORT_STORAGE_DIR=.local/document_exports
CORS_ALLOWED_ORIGINS=https://your-agencyos.example
LOG_LEVEL=INFO
AGENCY_SMTP_PASSWORD=
SMTP_SECRET_REFS=env:AGENCY_SMTP_PASSWORD
```

Do not commit real database credentials or production secrets.

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend starts on `http://localhost:5173`.

## Authentication And Seed Data

In development, seed data runs automatically on backend startup when `SEED_ON_STARTUP=true`. It can also be triggered through the seed endpoint when `SEED_ENDPOINT_ENABLED=true`:

```bash
curl -X POST http://localhost:8000/api/reference/seed \
  -H "X-Demo-User-Email: owner@aeroassist.dev"
```

Seeded demo logins use password `DemoPass123!`:

- Platform: `owner@aeroassist.dev`
- Agency owner: `agency.owner@aeroassist.dev`
- Agency agent: `agency.agent@aeroassist.dev`
- Portal client: `anna.client@example.com`
- Portal organization client: `travel@orbitex.example.com`

The login page at `/login` stores the returned bearer token in local storage and API requests send it as `Authorization: Bearer ...`.

Development/demo header fallback can be enabled with:

```bash
DEMO_AUTH_ENABLED=true
```

When enabled, legacy headers such as `X-Demo-User-Email` and `X-Demo-Client-Email` still work for local testing. Disable this for production-like runs:

```bash
DEMO_AUTH_ENABLED=false
AUTH_TOKEN_SECRET=replace-with-a-long-random-secret
SEED_ON_STARTUP=false
SEED_ENDPOINT_ENABLED=false
```

Invitation endpoints store only token hashes. Staff invitation creation returns a raw token and `/invite/accept?token=...` link once so an authorized operator can manually deliver it while automatic email sending remains disabled. Invitation lists, validation responses, audit events, logs, and normal API responses do not expose raw tokens or token hashes.

The seed endpoint is development/demo tooling and is disabled by default in production. First production platform owner creation should be handled by a controlled maintenance process or one-off administrative script, not by exposing demo seed data publicly.

## Production Configuration

Use `.env.production.example` as the Hostinger VPS checklist. Required production posture:

- `APP_ENV=production`
- `AEROASSIST_DB_MODE=mongo`
- `MONGODB_URL` and `MONGODB_DATABASE` configured
- `DEMO_AUTH_ENABLED=false`
- `SEED_ON_STARTUP=false`
- `SEED_ENDPOINT_ENABLED=false`
- non-placeholder `AUTH_TOKEN_SECRET`
- explicit writable `DOCUMENT_EXPORT_STORAGE_DIR`
- `CORS_ALLOWED_ORIGINS` set to the deployed frontend origin, never `*` or localhost
- SMTP passwords stored only in environment variables and referenced by agency settings as `env:VARIABLE_NAME`

Run:

```bash
python3 backend/scripts/check_production_readiness.py
```

`APP_ENV=production` makes critical readiness failures return a nonzero exit code. The script prints only masked secret references.

Frontend production builds should set `VITE_API_BASE_URL` when the API is on a different origin. If `VITE_API_BASE_URL` is omitted in a production build, the frontend uses same-origin `/api` calls rather than falling back to localhost.

## Docker Production Packaging

Phase 18 adds Docker packaging for a single VPS:

```bash
cp .env.production.example .env.production
docker compose --env-file .env.production -f docker-compose.production.yml build
docker compose --env-file .env.production -f docker-compose.production.yml up -d
```

The default Hostinger/TLS posture binds the frontend container to `127.0.0.1:8080` and lets host nginx own public ports `80` and `443`. The frontend nginx container serves the static app and proxies `/api` to the backend service. MongoDB data is stored in the `mongo_data` volume, and document exports are stored in the `document_exports` volume mounted at `/var/lib/aeroassist/document_exports` in the backend container.

See `DEPLOYMENT_HOSTINGER_VPS.md` for VPS prerequisites, env setup, readiness checks, logs, smoke checks, updates, and limitations.

Phase 19 operations helpers live under `deploy/hostinger/scripts`:

```bash
deploy/hostinger/scripts/deploy.sh
deploy/hostinger/scripts/backup_mongo.sh
deploy/hostinger/scripts/backup_exports.sh
deploy/hostinger/scripts/backup_all.sh
deploy/hostinger/scripts/verify_backups.sh
deploy/hostinger/scripts/prune_backups.sh
deploy/hostinger/scripts/healthcheck.sh
deploy/hostinger/scripts/status_full.sh
APP_BASE_URL=https://agencyos.example.com deploy/hostinger/scripts/smoke_production.sh
```

Use `deploy/hostinger/nginx/aeroassist.conf.example` as the host-level nginx/TLS template.

For the actual first VPS deployment, start here:

```text
deploy/hostinger/FIRST_DEPLOYMENT_CHECKLIST.md
```

Then run the non-mutating preflight before starting services:

```bash
APP_DIR=/opt/aeroassist-agencyos deploy/hostinger/scripts/preflight.sh
```

To bootstrap the first production platform owner when no auth identities exist:

```bash
cd /opt/aeroassist-agencyos
docker compose --env-file .env.production -f docker-compose.production.yml exec backend \
  python scripts/create_first_platform_owner.py
```

## Smoke Scripts

With the backend running:

```bash
python3 backend/scripts/smoke_backend.py
python3 backend/scripts/check_portal_isolation.py
python3 backend/scripts/smoke_reference_service_catalogue_governance.py
python3 backend/scripts/smoke_offer_builder_foundation.py
python3 backend/scripts/smoke_offer_acceptance_booking_readiness.py
python3 backend/scripts/smoke_booking_pnr_foundation.py
python3 backend/scripts/smoke_ticket_emd_foundation.py
python3 backend/scripts/smoke_supplementary_blueprint_sync.py
python3 backend/scripts/smoke_standalone_change_exchange_foundation.py
python3 backend/scripts/smoke_document_foundation.py
python3 backend/scripts/smoke_gds_parser_foundation.py
python3 backend/scripts/smoke_airline_policy_ingestion_foundation.py
python3 backend/scripts/smoke_service_taxonomy_foundation.py
python3 backend/scripts/smoke_service_mechanics_mapping_foundation.py
python3 backend/scripts/smoke_ancillary_pricing_exception_foundation.py
python3 backend/scripts/smoke_policy_comparison_service_advisor_foundation.py
python3 backend/scripts/smoke_offer_policy_advisor_integration_foundation.py
python3 backend/scripts/smoke_offer_decision_pack_foundation.py
python3 backend/scripts/smoke_offer_decision_explanation_foundation.py
python3 backend/scripts/smoke_offer_decision_export_foundation.py
python3 backend/scripts/smoke_offer_decision_export_preview_foundation.py
python3 backend/scripts/smoke_offer_decision_export_release_readiness_foundation.py
python3 backend/scripts/smoke_offer_decision_export_manual_delivery_handoff_foundation.py
python3 backend/scripts/smoke_offer_decision_export_manual_delivery_outcome_foundation.py
python3 backend/scripts/smoke_offer_decision_export_audit_review_foundation.py
python3 backend/scripts/smoke_offer_decision_export_governance_foundation.py
python3 backend/scripts/smoke_offer_decision_export_compliance_foundation.py
python3 backend/scripts/smoke_airline_intelligence_data_pack_foundation.py
python3 backend/scripts/smoke_airline_intelligence_data_pack_review_foundation.py
python3 backend/scripts/smoke_airline_intelligence_knowledge_versioning_foundation.py
python3 backend/scripts/smoke_airline_intelligence_agency_consumption_bridge.py
python3 backend/scripts/smoke_platform_agency_ux_consolidation.py
python3 backend/scripts/smoke_saas_subscription_entitlement_foundation.py
python3 backend/scripts/smoke_subscription_entitlement_ui_guardrails.py
python3 backend/scripts/smoke_agency_feature_flags_foundation.py
python3 backend/scripts/smoke_agency_feature_flag_audit_foundation.py
python3 backend/scripts/smoke_agency_feature_flag_bundle_foundation.py
python3 backend/scripts/smoke_feature_bundle_assignment_foundation.py
python3 backend/scripts/smoke_feature_bundle_rollout_readiness_foundation.py
python3 backend/scripts/smoke_feature_bundle_rollout_plan_foundation.py
python3 backend/scripts/smoke_feature_bundle_rollout_approval_foundation.py
python3 backend/scripts/smoke_feature_bundle_rollout_schedule_foundation.py
python3 backend/scripts/smoke_feature_bundle_rollout_timeline_foundation.py
python3 backend/scripts/smoke_feature_bundle_dependency_foundation.py
python3 backend/scripts/smoke_feature_bundle_rollout_risk_register_foundation.py
python3 backend/scripts/smoke_feature_bundle_rollout_issue_log_foundation.py
python3 backend/scripts/smoke_feature_bundle_rollout_decision_register_foundation.py
python3 backend/scripts/smoke_feature_bundle_rollout_change_request_foundation.py
python3 backend/scripts/smoke_feature_bundle_rollout_rollback_plan_foundation.py
python3 backend/scripts/smoke_feature_bundle_rollout_summary_pack_foundation.py
python3 backend/scripts/smoke_operational_travel_workspace_foundation.py
python3 backend/scripts/smoke_travel_request_workspace_foundation.py
python3 backend/scripts/smoke_passenger_workspace_foundation.py
python3 backend/scripts/smoke_flight_workspace_foundation.py
python3 backend/scripts/smoke_trip_workspace_foundation.py
python3 backend/scripts/smoke_offer_workspace_foundation.py
python3 backend/scripts/smoke_booking_workspace_foundation.py
python3 backend/scripts/smoke_ticket_workspace_foundation.py
python3 backend/scripts/smoke_rollout_dashboard_foundation.py
python3 backend/scripts/smoke_capability_catalog_foundation.py
```

The backend smoke calls the seed endpoint twice and verifies counts remain stable, then exercises core module list/detail endpoints. The portal isolation smoke checks both seeded portal clients, verifies cross-client detail denial, and scans portal JSON for internal field names. The reference service catalogue smoke validates the Phase 36.2.5 consumer map, health/action-required, domain-aware imports, enrichment packs, platform catalogue CRUD, agency consume behavior, and readiness flags. The offer builder smoke creates a request/trip-linked workspace, option, segment, fare bundle, pricing lines, rule evaluation, comparison snapshot, and recommendation. The offer acceptance smoke verifies acceptance snapshots, trip baseline snapshots, booking readiness packages, rebuild, supersede, and cancel. The booking PNR foundation smoke verifies booking workspace creation from readiness, draft manual PNR mirrors, timeline events, rebuild, cancellation, and disabled provider execution. The ticket/EMD foundation smoke verifies draft ticket and EMD mirrors, coupon records, service catalogue mapping preservation, timeline events, readiness summaries, and disabled provider issuance. The supplementary blueprint sync smoke verifies adoption-map APIs, canonical route policy, blueprint readiness flags, safe foundations, and the special-services facade. The platform/agency UX consolidation smoke verifies Phase 39.4 readiness flags, canonical route policy, absence of admin/agent route roots, Platform Console and Agency Workspace labels, plain-language module groups, helper badges, and frontend build success. The SaaS subscription entitlement smoke verifies Phase 39.5 readiness flags, platform plan/entitlement/assignment/readiness/note/snapshot metadata, agency read-only subscription visibility, disabled billing/payment/invoice/settlement/access-enforcement flags, canonical route boundaries, frontend labels, and docs. The subscription entitlement UI guardrails smoke verifies Phase 39.6 readiness flags, read-only visibility endpoints, agency navigation badge source, platform review visibility, preserved canonical routes, and no admin/agent route roots. The agency feature flags smoke verifies Phase 39.7 readiness flags, platform feature flag/review/snapshot metadata, agency read-only Feature Availability visibility, disabled enforcement/billing/provider boundaries, canonical routes, frontend labels, and docs. The agency feature flag audit smoke verifies Phase 39.8 readiness flags, read-only audit/readiness routers, feature audit history, agency-scoped readiness metadata, disabled enforcement/subscription/billing/provider boundaries, canonical routes, frontend labels, and docs. The agency feature flag bundle smoke verifies Phase 39.9 bundle models, collections, indexes, read-only platform/agency bundle routers, default bundle metadata, module catalog registration, docs, disabled enforcement/entitlement/billing/rollout/provider/background/notification boundaries, canonical routes, and absence of admin/agent route roots. The feature bundle assignment smoke verifies Phase 40.0 assignment models, collection/index registration, platform metadata CRUD, agency read-only assignment/history visibility, inactive-delete behavior, preserved history, docs, frontend route registration, module catalog registration, disabled activation/entitlement/billing/provider/AI/background boundaries, canonical routes, and absence of admin/agent route roots. The feature bundle rollout readiness smoke verifies Phase 40.1 rollout readiness models, collection/index registration, platform review and agency read-only endpoints, default readiness views, checklist response shape, summary counts, docs, frontend route registration, module catalog registration, disabled activation/enforcement/billing/provider/external API/sending boundaries, canonical routes, and previous bundle/assignment foundation compatibility. The feature bundle rollout plan smoke verifies Phase 40.2 rollout plan models, collection/index registration, platform metadata create/update/read endpoints, agency read-only plan endpoints, readiness/checklist summary response shape, docs, frontend route registration, module catalog registration, disabled execution/billing/provider/API/AI/sending/scraping boundaries, canonical routes, and previous readiness compatibility. The rollout dashboard smoke verifies Phase 40.3 read-only dashboard models, collection/index registration, platform and agency dashboard endpoints, summary/count/section/filter/snapshot shapes, frontend route registration, module catalog registration, docs, disabled automation/execution/billing/provider/API/AI/sending/scraping boundaries, canonical routes, and previous rollout plan compatibility. The feature bundle rollout approval smoke verifies Phase 40.4 approval models, collection/index registration, platform metadata create/update endpoints, agency read-only approval/note/timeline endpoints, docs, frontend route registration, module catalog registration, disabled enablement/gating/enforcement/billing/deployment/notification/API/AI/scraping/publishing/execution boundaries, canonical routes, and previous rollout dashboard compatibility. The feature bundle rollout schedule smoke verifies Phase 40.5 schedule models, collection/index registration, platform metadata create/update endpoints, agency read-only schedule endpoints, docs, frontend route registration, module catalog registration, disabled execution/activation/entitlement/permission/cron/scheduler/worker/queue/timer/API/AI/billing/publishing boundaries, canonical routes, and previous approval compatibility. The feature bundle rollout timeline smoke verifies Phase 40.6 timeline models, collection/index registration, platform metadata create/list/detail endpoints, agency read-only timeline endpoints, plan/agency/bundle/event/date filters, docs, frontend route registration, module catalog registration, disabled enablement/permission/execution/job/publishing/provider/email/notification/state/subscription/automation boundaries, canonical routes, and previous schedule compatibility. The feature bundle dependency smoke verifies Phase 40.7 dependency models, collection/index registration, platform metadata create/update/delete/read/list endpoints, agency read-only dependency endpoints, bundle/plan/agency/type filters, docs, frontend route registration, module catalog registration, disabled execution/job/enforcement/blocking/activation/permission/notification/publishing/provider/automation boundaries, canonical routes, and previous timeline compatibility. The capability catalog smoke verifies Phase 40.1 catalog models, collection/index registration, read-only platform/agency capability routers, category and module listings, frontend route registration, module catalog registration, docs, readiness flags, disabled enforcement/entitlement/billing/provider/external service boundaries, canonical routes, and absence of admin/agent route roots.

The feature bundle rollout risk register smoke verifies Phase 40.8 risk models, collection/index registration, platform metadata create/update/delete/read/list endpoints, agency read-only risk endpoints, agency/bundle/plan/status/impact/likelihood filters, docs, frontend route registration, module catalog registration, disabled execution/enforcement/blocking/notification/activation/automation/provider boundaries, canonical routes, and previous dependency compatibility.

The feature bundle rollout issue log smoke verifies Phase 40.9 issue models, collection/index registration, platform metadata create/update/delete/read/list endpoints, agency read-only issue endpoints, agency/bundle/plan/risk/dependency/approval/severity/status filters, docs, frontend route registration, module catalog registration, disabled execution/activation/blocking/notification/provider/AI boundaries, canonical routes, and previous risk register compatibility.

The feature bundle rollout decision register smoke verifies Phase 40.10 decision models, collection/index registration, platform metadata create/update/delete/read/list endpoints, agency read-only decision endpoints, rollout/category/owner/status filters, related bundle/risk/issue/dependency/timeline references, docs, frontend route registration, module catalog registration, disabled execution/deployment/activation/enforcement/billing/provider/API/AI/worker/scheduler/notification/email/webhook/publishing/runtime-switch boundaries, canonical routes, and previous issue log compatibility.

The feature bundle rollout change request smoke verifies Phase 40.11 change request models, collection/index registration, platform metadata create/update/delete/read/list endpoints, agency read-only change request endpoints, rollout/status/priority/impact/type filters, affected bundle/feature flag references, related decision/risk/issue/dependency references, docs, frontend route registration, module catalog registration, disabled execution/deployment/activation/enforcement/billing/provider/API/AI/worker/scheduler/notification/email/webhook/publishing/runtime-switch boundaries, canonical routes, and previous decision register compatibility.

The feature bundle rollout rollback plan smoke verifies Phase 40.12 rollback plan models, collection/index registration, platform metadata create/update/delete/read/list endpoints, agency read-only rollback plan endpoints, rollout/status/priority/scope/owner filters, affected bundle/feature flag references, related change request/decision/risk/issue/dependency references, rollback steps, docs, frontend route registration, module catalog registration, disabled rollback execution/deployment/activation/deactivation/enforcement/billing/provider/API/AI/worker/scheduler/notification/email/webhook/publishing/runtime-switch boundaries, canonical routes, and previous change request compatibility.

The feature bundle rollout summary pack smoke verifies Phase 40.13 summary pack models, collection/index registration, platform metadata create/update/delete/read/list endpoints, agency read-only summary pack endpoints, rollout/status/audience/bundle filters, covered bundle/readiness/approval/schedule/timeline/dependency/risk/issue/decision/change request/rollback plan references, evidence and compliance notes, docs, frontend route registration, module catalog registration, disabled execution/deployment/activation/deactivation/enforcement/billing/provider/API/AI/worker/scheduler/notification/email/webhook/publishing/runtime-switch/PDF/export boundaries, canonical routes, and previous rollback plan compatibility.

The operational travel workspace smoke verifies Phase 41.0 workspace models, collection/index registration, platform metadata create/update/archive/read/list endpoints, agency read-only workspace endpoints, agency/status/type/priority/assigned-agent/travel-date filters, client/passenger summaries, linked request/trip/offer/booking/ticket/document references, docs, frontend route registration, module catalog registration, disabled booking/ticketing/GDS/NDC/payment/email/SMS/AI/API/supplier/airline/worker/automation boundaries, canonical routes, and previous summary pack compatibility.

The travel request workspace smoke verifies Phase 41.1 request workspace models, collection/index registration, platform metadata create/update/archive/read/list endpoints, agency read-only request workspace endpoints, agency/status/type/priority/assigned-agent/departure-date/operational-workspace filters, requester details, client/passenger summaries, requested route/date/passenger/service/budget/deadline/internal-note metadata, linked trip/offer/document references, docs, frontend route registration, module catalog registration, disabled booking/ticketing/GDS/NDC/payment/email/SMS/AI/API/supplier/airline/worker/trip-conversion/offer-creation/automation boundaries, canonical routes, and previous operational workspace compatibility.

The passenger workspace smoke verifies Phase 41.2 passenger workspace models, collection/index registration, platform metadata create/update/archive/read/list endpoints, agency read-only passenger workspace endpoints, status/nationality/citizenship/assistance-profile/travel-date/assigned-workspace filters, personal information, travel documents, loyalty memberships, medical/mobility/assistance/dietary/seating/emergency-contact metadata, linked request/trip/offer/booking/ticket/document references, docs, frontend route registration, module catalog registration, disabled booking/ticketing/GDS/NDC/payment/supplier/AI/email/SMS/worker/API/profile-matching/document-validation/airline-communication/automation boundaries, canonical routes, and previous travel request workspace compatibility.

The flight workspace smoke verifies Phase 41.3 flight workspace models, collection/index registration, platform metadata create/update/archive/read/list endpoints, agency read-only flight workspace endpoints, status/airline/departure-airport/arrival-airport/departure-date/cabin/booking-class/assigned-workspace filters, airline, carrier, flight number, airport, terminal, schedule, aircraft, cabin, fare, baggage, connection, stopover, passenger, and linked request/trip/offer/booking/ticket/document metadata, docs, frontend route registration, module catalog registration, disabled booking/live-search/GDS/NDC/airline-API/payment/ticketing/schedule-sync/external-API/AI/worker/route-generation/validation/lookup/live-update/automation boundaries, canonical routes, and previous passenger workspace compatibility.

The trip workspace smoke verifies Phase 41.4 trip workspace models, collection/index registration, platform metadata create/update/archive/read/list endpoints, agency read-only trip workspace endpoints, status/departure-country/destination-country/departure-date/assigned-agent/priority/assigned-workspace filters, trip references, journey type, service type, client, passenger summary, flight summary, linked request/offer/booking/ticket/EMD/document metadata, route and travel date metadata, docs, frontend route registration, module catalog registration, disabled booking/ticketing/GDS/NDC/airline-API/payment/invoicing/AI/worker/trip-generation/itinerary-generation/external-integration/automation boundaries, canonical routes, and previous flight workspace compatibility.

The offer workspace smoke verifies Phase 41.5 offer workspace models, collection/index registration, platform metadata create/update/archive/read/list endpoints, agency read-only offer workspace endpoints, status/validity/client/destination/price-range/assigned-agent/trip-workspace filters, offer references, trip summary, passenger summary, flight summary, pricing summary, tax/fee/ancillary/baggage/seat/meal/hotel/transfer/insurance/validity metadata, linked booking/ticket/document references, docs, frontend route registration, module catalog registration, disabled booking/ticketing/payment/GDS/NDC/airline-API/fare-calculation/live-pricing/AI-itinerary/supplier/API/booking-conversion/worker/automation boundaries, canonical routes, and previous trip workspace compatibility.

The booking workspace smoke verifies Phase 41.6 booking workspace models, extended collection/index registration, platform metadata create/update/archive/read/list endpoints, agency read-only booking workspace endpoints, status/booking-owner/airline/supplier/booking-date filters, booking references, owner, airline PNR, GDS locator, supplier reference, passenger summary, flight summary, trip summary, offer summary, ticket, EMD, SSR, OSI, document, timeline, communication, payment, booking, and operational note metadata, docs, frontend route registration, module catalog registration, disabled live-booking/ticketing/GDS/NDC/airline-API/payment/fare-calculation/AI/worker/automatic-confirmation/automatic-ticket/external-integration/automation boundaries, canonical routes, and previous offer workspace compatibility.

The ticket workspace smoke verifies Phase 41.7 ticket workspace models, collection/index registration, platform metadata create/update/archive/read/list endpoints, agency read-only ticket workspace endpoints, workspace-status/ticket-document-status/validating-carrier/issue-date/passenger/booking-reference/currency filters, ticket references, ticket numbers, validating carrier, issue date, passenger, booking references, airline PNR, GDS locator, flight links, fare basis summaries, fare/tax/total amounts, fare calculation line/NUC/ROE metadata, equivalent fare paid metadata, form of payment, tax breakdown, pricing units, fare components, coupon status summary, coupon details with coupon-level fare basis, exchange/refund/void references, baggage, endorsement, restriction, EMD, document, lifecycle, and operational note metadata, docs, frontend route registration, module catalog registration, disabled issuance/reissue/void/refund/exchange/payment/GDS/NDC/airline-API/fare-calculation/recalculation/ticket-validation/coupon-validation/worker/external-integration/automation boundaries, canonical routes, and previous booking workspace compatibility.

The EMD workspace smoke verifies Phase 41.8 EMD workspace models, collection/index registration, platform metadata create/update/archive/read/list endpoints, agency read-only EMD workspace endpoints, agency/status/type/EMD-A-or-S/validating-carrier/passenger/RFIC/RFISC/service-category/issue-date filters, EMD references, document status, EMD-A/EMD-S metadata, associated ticket/coupon/flight links, SSR/OSI links, ancillary service links, RFIC/RFISC service metadata, coupon details, fare/tax/payment metadata, exchange/refund/void references, documents, lifecycle and operational notes, docs, frontend route registration, module catalog registration, disabled issuance/exchange/refund/void/payment/GDS/NDC/airline-API/RFIC-RFISC-validation/SSR-OSI-transmission/worker/external-integration/duplicate-architecture/automation boundaries, canonical routes, and previous ticket workspace compatibility.

The SSR / OSI operational workspace smoke verifies Phase 41.9 SSR / OSI workspace models, collection/index registration, platform metadata create/update/archive/read/list endpoints, agency read-only passenger service endpoints, need-category/airline/approval/readiness/passenger/priority/RFIC/RFISC filters, passenger need, service classification, SSR/OSI metadata, airline and airport handling, approval metadata, EMD/RFIC/RFISC references, documents, MEDIF, fulfilment references, readiness, missing requirements, unresolved items, AOIE input documentation, frontend route registration, module catalog registration, disabled SSR/OSI-transmission/GDS/NDC/airline-API/AI-recommendation/approval-automation/EMD-issuance/worker/provider/external-API/automation boundaries, canonical routes, and previous EMD workspace compatibility.

The document workspace smoke verifies Phase 42.0 document workspace models, collection/index registration, platform metadata create/update/archive/read/list endpoints, agency read-only document workspace endpoints, type/status/passenger/booking/service/required-for-travel/verification/deadline filters, passenger/request/trip/booking/ticket/EMD/SSR-OSI/AOIE links, requirement, received, verification, validity, storage, package, render job, share record, visibility, missing/rejection, and operational note metadata, docs, frontend route registration, module catalog registration, disabled delivery/e-signature/public-link/PDF-generation/payment-invoice/external-storage/worker/AI-generation/automation boundaries, canonical routes, and previous SSR / OSI, ticket, and EMD workspace compatibility.

The operational timeline smoke verifies Phase 42.1 operational timeline models, collection/index registration, platform metadata create/update/archive/read/list endpoints, agency read-only timeline endpoints, passenger/booking/ticket/EMD/SSR/airline/communication/event/priority/status/date filters, chronological ordering, passenger/request/trip/booking/ticket/EMD/SSR-OSI/document links, communication summary metadata, approval history metadata, attachment references, visibility flags, operational notes, docs, frontend route registration, module catalog registration, disabled email/SMS/WhatsApp/Teams/Slack/live-airline-message/live-customer-message/AI-summary/worker/provider/automation boundaries, canonical routes, and previous document, SSR / OSI, ticket, EMD, and booking workspace compatibility.

The passenger service workflow engine smoke verifies Phase 42.2 workflow models, collection/index registration, platform metadata create/update/archive/read/list endpoints, agency read-only workflow endpoints, stage/readiness/passenger/airline/priority/assigned-agent filters, workflow stage definitions, readiness states, passenger/request/trip/booking/ticket/EMD/SSR-OSI/document/timeline links, blocking and completed requirement metadata, future AOIE recommendation reference metadata, docs, frontend route registration, module catalog registration, disabled workflow-execution/AI-decision/worker/airline-API/GDS/NDC/approval/ticketing/EMD-issuance/messaging/provider/automation boundaries, canonical routes, and previous timeline, document, SSR / OSI, ticket, and EMD workspace compatibility.

The AOIE smoke verifies Phase 50.0 Airline Operational Intelligence Engine architecture models, collection/index registration, deterministic seed/read behavior, platform read-only routes, agency read-only routes, frontend route registration, module catalog registration, readiness flags, active phase marker, blueprint recommendation updates, Chapter 50 roadmap, retained Chapter 41 operational roadmap, and disabled AI generation/scraping/crawling/live-airline-API/provider/pricing-engine/itinerary-search/booking/ticketing/EMD/recommendation-automation/background-worker boundaries.

The airline knowledge acquisition workspace smoke verifies Phase 50.1 acquisition models, collection/index registration, platform metadata create/update/archive/read/list endpoints, agency read-only acquisition endpoints, airline/service-domain/service-family/SSR/RFIC/RFISC/source-type/review-status/approval-status/effective-date/official-source filters, raw official source text storage, operational knowledge graph pillars, policy/pricing/capability/constraint metadata, review/approval/version metadata, future AOIE links, operational links, docs, frontend route registration, module catalog registration, disabled AI-parsing/automatic-extraction/scraping/crawling/airline-website-automation/provider/live-airline-API/recommendation/feasibility/pricing/worker/parser-execution/automation boundaries, canonical routes, and AOIE linkage documentation.

## Production Readiness Warning

Phase 50.1 adds metadata-only airline operational knowledge graph records on top of Phase 50.0 AOIE architecture metadata and Phase 42.2 passenger service workflow records on top of Phase 42.1 operational timeline records, Phase 42.0 operational document workspace records, Phase 41.9 SSR / OSI operational workspace records, Phase 50.0 AOIE architecture metadata, Phase 41.8 EMD workspace records, Phase 41.7 ticket workspace records, Phase 41.6 booking workspace records, Phase 41.5 offer workspace records, Phase 41.4 trip workspace records, Phase 41.3 flight workspace records, Phase 41.2 passenger workspace records, Phase 41.1 travel request workspace records, Phase 41.0 operational travel workspace records, Phase 40.13 feature bundle rollout summary evidence-pack records, Phase 40.12 rollback plans, Phase 40.11 change requests, Phase 40.10 decision registers, Phase 40.9 issue logs, Phase 40.8 risk registers, Phase 40.7 dependencies, Phase 40.6 rollout timeline entries, Phase 40.5 rollout schedules, Phase 40.4 rollout approvals, Phase 40.3 rollout dashboard, Phase 40.2 feature bundle rollout plans, Phase 40.1 rollout readiness, Phase 40.0 feature bundle assignment history, and the capability catalog metadata layer on top of policy ingestion, taxonomy, mechanics, pricing, comparison, offer advisor, decision pack, explanation, export, preview, release readiness, manual handoff, manual outcome, audit review, governance, compliance, parser, document, standalone booking/import/change, ticket/EMD mirror, data-pack staging, data-pack review, knowledge-versioning, agency-consumption, UX consolidation, SaaS subscription, subscription guardrail, agency feature flag, feature flag audit, and feature flag bundle foundations, but AgencyOS is not a complete operations stack. Production use still requires migrations, off-server backup policy, alerting decisions, broader automated tests, provider webhook/bounce handling decisions, real object-storage integration decisions, automatic invite delivery decisions, broader team management, visual regression automation, domain routing decisions, airline policy/taxonomy/mechanics/pricing/comparison/offer-advisor/decision-pack/explanation/export/preview/release/handoff/outcome/audit/governance/compliance/data-pack/review/versioning/consumption hardening, AOIE acquisition/normalisation/review/capability/feasibility/recommendation/cost-comparison hardening only if explicitly authorized, real billing/payment/invoice/accounting/settlement design if ever authorized, real permission enforcement only if explicitly authorized, client offer sharing hardening, workflow execution only if explicitly authorized, fare calculation only if explicitly authorized, AI itinerary generation only if explicitly authorized, supplier integrations only if explicitly authorized, automatic booking conversion only if explicitly authorized, live booking creation only if explicitly authorized, automatic booking confirmation only if explicitly authorized, automatic ticket generation only if explicitly authorized, ticket issuance/reissue/void/refund/exchange/coupon validation only if explicitly authorized, EMD issuance/exchange/refund/void/RFIC-RFISC validation only if explicitly authorized, SSR/OSI transmission only if explicitly authorized, automatic airline service approval only if explicitly authorized, full visual form builder decisions, full GDS grammar/provider reconciliation, live SSR/OSI/GDS/NDC/provider execution, live ticket/EMD issuance, real exchange/refund/void execution, automatic passenger profile matching only if explicitly authorized, automatic passenger document validation only if explicitly authorized, automatic request-to-trip conversion only if explicitly authorized, automatic offer creation only if explicitly authorized, live flight search and schedule synchronization only if explicitly authorized, automatic route generation only if explicitly authorized, flight validation and airline lookup only if explicitly authorized, automatic trip generation only if explicitly authorized, automatic itinerary generation only if explicitly authorized, invoice/payment/accounting/settlement execution, external data providers, automatic scraping, real PDF/export/sending/publishing decisions, and deeper CMS publishing hardening.

## Useful Endpoints

- `GET /api/health`
- `GET /api/readiness`
- `GET /api/auth/me`
- `GET /api/platform/blueprint/adoption-map`
- `GET /api/platform/blueprint/route-policy`
- `GET /api/platform/blueprint/gaps`
- `GET /api/platform/blueprint/next-phases`
- `GET /api/agencies/{agency_id}/branding`
- `PUT /api/agencies/{agency_id}/branding`
- `POST /api/agencies/{agency_id}/branding/logo`
- `POST /api/agencies/{agency_id}/branding/logo/regenerate`
- `GET /api/agencies/{agency_id}/branding/public`
- `DELETE /api/agencies/{agency_id}/branding/logo`
- `GET /api/agencies/{agency_id}/website`
- `PUT /api/agencies/{agency_id}/website`
- `GET /api/agencies/{agency_id}/website/pages`
- `POST /api/agencies/{agency_id}/website/pages`
- `GET /api/agencies/{agency_id}/website/media`
- `POST /api/agencies/{agency_id}/website/media`
- `PUT /api/agencies/{agency_id}/website/media/{asset_id}`
- `DELETE /api/agencies/{agency_id}/website/media/{asset_id}`
- `GET /api/public/websites/{slug}`
- `GET /api/public/websites/{slug}/pages/{page_slug}`
- `POST /api/public/websites/{slug}/request`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/invitations/validate`
- `POST /api/auth/invitations/accept`
- `POST /api/auth/change-password`
- `POST /api/auth/demo-login`
- `GET /api/documents/storage/summary`
- `GET /api/documents/storage`
- `POST /api/documents/storage/{record_id}/archive`
- `POST /api/documents/storage/{record_id}/mark-missing`
- `GET /api/documents/storage/health`
- `GET /api/documents/delivery-providers`
- `GET /api/documents/delivery-providers/readiness`
- `GET /api/platform/health`
- `GET /api/platform/summary`
- `GET /api/agencies`
- `POST /api/agencies`
- `GET /api/agencies/{agency_id}`
- `PUT /api/agencies/{agency_id}`
- `GET /api/agencies/{agency_id}/workspaces`
- `POST /api/agencies/{agency_id}/workspaces`
- `GET /api/agencies/{agency_id}/settings`
- `PUT /api/agencies/{agency_id}/settings`
- `GET /api/agencies/{agency_id}/staff`
- `POST /api/agencies/{agency_id}/staff`
- `POST /api/agencies/{agency_id}/staff/invitations`
- `GET /api/agencies/{agency_id}/staff/invitations`
- `POST /api/agencies/{agency_id}/staff/invitations/{invitation_id}/revoke`
- `GET /api/agencies/{agency_id}/portal-actions`
- `POST /api/agencies/{agency_id}/portal-actions/{action_id}/process`
- `GET /api/agencies/{agency_id}/clients`
- `POST /api/agencies/{agency_id}/clients`
- `GET /api/agencies/{agency_id}/clients/{client_id}`
- `PUT /api/agencies/{agency_id}/clients/{client_id}`
- `POST /api/agencies/{agency_id}/clients/{client_id}/archive`
- `POST /api/agencies/{agency_id}/clients/{client_id}/restore`
- `POST /api/agencies/{agency_id}/clients/{client_id}/portal-invitation`
- `GET /api/agencies/{agency_id}/passengers`
- `POST /api/agencies/{agency_id}/passengers`
- `GET /api/agencies/{agency_id}/passengers/{passenger_id}`
- `PUT /api/agencies/{agency_id}/passengers/{passenger_id}`
- `POST /api/agencies/{agency_id}/passengers/{passenger_id}/archive`
- `POST /api/agencies/{agency_id}/passengers/{passenger_id}/restore`
- `POST /api/agencies/{agency_id}/passengers/{passenger_id}/merge`
- `GET /api/agencies/{agency_id}/client-passenger-relationships`
- `POST /api/agencies/{agency_id}/client-passenger-relationships`
- `PUT /api/agencies/{agency_id}/client-passenger-relationships/{relationship_id}`
- `POST /api/agencies/{agency_id}/client-passenger-relationships/{relationship_id}/archive`
- `GET /api/agencies/{agency_id}/clients/{client_id}/passengers`
- `GET /api/agencies/{agency_id}/passengers/{passenger_id}/clients`
- `GET /api/agencies/{agency_id}/requests`
- `POST /api/agencies/{agency_id}/requests`
- `POST /api/agencies/{agency_id}/requests/builder`
- `GET /api/agencies/{agency_id}/requests/{request_id}`
- `PUT /api/agencies/{agency_id}/requests/{request_id}`
- `POST /api/agencies/{agency_id}/requests/{request_id}/archive`
- `POST /api/agencies/{agency_id}/requests/{request_id}/restore`
- `POST /api/agencies/{agency_id}/requests/{request_id}/status`
- `POST /api/public/request-intakes`
- `GET /api/request-intakes`
- `POST /api/request-intakes`
- `GET /api/request-intakes/{intake_id}`
- `PATCH /api/request-intakes/{intake_id}/triage`
- `POST /api/request-intakes/{intake_id}/convert`
- `POST /api/request-intakes/{intake_id}/reject`
- `POST /api/request-intakes/{intake_id}/archive`
- `POST /api/request-intakes/{intake_id}/mark-duplicate`
- `GET/POST /api/agencies/{agency_id}/requests/{request_id}/passengers`
- `GET/POST /api/agencies/{agency_id}/requests/{request_id}/segments`
- `GET/POST /api/agencies/{agency_id}/requests/{request_id}/services`
- `GET/POST /api/agencies/{agency_id}/requests/{request_id}/messages`
- `GET/POST /api/agencies/{agency_id}/requests/{request_id}/tasks`
- `GET /api/agencies/{agency_id}/requests/{request_id}/timeline`
- `GET /api/agencies/{agency_id}/trips`
- `POST /api/agencies/{agency_id}/trips`
- `GET /api/agencies/{agency_id}/trips/{trip_id}`
- `PUT /api/agencies/{agency_id}/trips/{trip_id}`
- `POST /api/agencies/{agency_id}/trips/{trip_id}/archive`
- `POST /api/agencies/{agency_id}/trips/from-request/{request_id}`
- `POST /api/agencies/{agency_id}/trips/{trip_id}/link-request/{request_id}`
- `POST /api/agencies/{agency_id}/trips/{trip_id}/unlink-request/{request_id}`
- `POST /api/agencies/{agency_id}/trips/{trip_id}/rebuild-summary`
- `GET /api/agencies/{agency_id}/offer-workspaces`
- `POST /api/agencies/{agency_id}/offer-workspaces`
- `GET /api/agencies/{agency_id}/offer-workspaces/{workspace_id}`
- `POST /api/agencies/{agency_id}/requests/{request_id}/offer-workspace`
- `POST /api/agencies/{agency_id}/trips/{trip_id}/offer-workspace`
- `POST /api/agencies/{agency_id}/offer-workspaces/{workspace_id}/options`
- `PUT /api/agencies/{agency_id}/offer-options/{option_id}`
- `POST /api/agencies/{agency_id}/offer-options/{option_id}/evaluate-rules`
- `POST /api/agencies/{agency_id}/offer-options/{option_id}/recalculate-pricing`
- `GET /api/agencies/{agency_id}/offer-workspaces/{workspace_id}/comparison`
- `GET /api/agencies/{agency_id}/offers`
- `POST /api/agencies/{agency_id}/offers`
- `GET /api/agencies/{agency_id}/offers/{offer_id}`
- `PUT /api/agencies/{agency_id}/offers/{offer_id}`
- `POST /api/agencies/{agency_id}/offers/{offer_id}/archive`
- `POST /api/agencies/{agency_id}/offers/{offer_id}/restore`
- `POST /api/agencies/{agency_id}/offers/{offer_id}/send`
- `POST /api/agencies/{agency_id}/requests/{request_id}/create-offer`
- Offer passenger, route alternative, segment, fare option, price line, service check, and timeline endpoints under `/api/agencies/{agency_id}/offers/{offer_id}`
- `GET /api/agencies/{agency_id}/bookings`
- `POST /api/agencies/{agency_id}/bookings`
- `POST /api/agencies/{agency_id}/offers/{offer_id}/create-booking`
- `GET /api/agencies/{agency_id}/bookings/{booking_id}`
- `PUT /api/agencies/{agency_id}/bookings/{booking_id}`
- `POST /api/agencies/{agency_id}/bookings/{booking_id}/archive`
- `POST /api/agencies/{agency_id}/bookings/{booking_id}/cancel`
- Booking passenger, segment, ticket, EMD, and timeline endpoints under `/api/agencies/{agency_id}/bookings/{booking_id}`
- `GET /api/agencies/{agency_id}/tickets`
- `POST /api/agencies/{agency_id}/tickets/from-booking-record`
- `GET /api/agencies/{agency_id}/tickets/{ticket_record_id}`
- `PUT /api/agencies/{agency_id}/tickets/{ticket_record_id}`
- `GET /api/agencies/{agency_id}/emds`
- `POST /api/agencies/{agency_id}/emds/from-booking-service`
- `GET /api/agencies/{agency_id}/emds/{emd_record_id}`
- `PUT /api/agencies/{agency_id}/emds/{emd_record_id}`
- `GET /api/agencies/{agency_id}/booking-records/{booking_record_id}/ticket-emd-readiness`
- `GET /api/agencies/{agency_id}/invoices`
- `POST /api/agencies/{agency_id}/invoices`
- `GET /api/agencies/{agency_id}/invoices/{invoice_id}`
- `PUT /api/agencies/{agency_id}/invoices/{invoice_id}`
- `POST /api/agencies/{agency_id}/invoices/{invoice_id}/issue`
- `POST /api/agencies/{agency_id}/invoices/{invoice_id}/void`
- Invoice line item endpoints under `/api/agencies/{agency_id}/invoices/{invoice_id}`
- `GET /api/agencies/{agency_id}/payments`
- `POST /api/agencies/{agency_id}/payments`
- `GET /api/agencies/{agency_id}/payments/{payment_id}`
- `PUT /api/agencies/{agency_id}/payments/{payment_id}`
- `POST /api/agencies/{agency_id}/payments/{payment_id}/mark-received`
- `POST /api/agencies/{agency_id}/payments/{payment_id}/mark-reconciled`
- `GET /api/agencies/{agency_id}/refund-exchange-cases`
- `POST /api/agencies/{agency_id}/refund-exchange-cases`
- `GET /api/agencies/{agency_id}/refund-exchange-cases/{case_id}`
- `PUT /api/agencies/{agency_id}/refund-exchange-cases/{case_id}`
- `POST /api/agencies/{agency_id}/refund-exchange-cases/{case_id}/status`
- `POST /api/agencies/{agency_id}/refund-exchange-cases/{case_id}/archive`
- `POST /api/agencies/{agency_id}/bookings/{booking_id}/create-refund-exchange-case`
- `GET /api/agencies/{agency_id}/refund-exchange-cases/{case_id}/items`
- `POST /api/agencies/{agency_id}/refund-exchange-cases/{case_id}/items`
- `PUT /api/agencies/{agency_id}/refund-exchange-cases/{case_id}/items/{item_id}`
- `GET /api/agencies/{agency_id}/refund-exchange-cases/{case_id}/financial-lines`
- `POST /api/agencies/{agency_id}/refund-exchange-cases/{case_id}/financial-lines`
- `PUT /api/agencies/{agency_id}/refund-exchange-cases/{case_id}/financial-lines/{line_id}`
- `GET /api/agencies/{agency_id}/refund-exchange-cases/{case_id}/messages`
- `POST /api/agencies/{agency_id}/refund-exchange-cases/{case_id}/messages`
- `GET /api/agencies/{agency_id}/refund-exchange-cases/{case_id}/timeline`
- `GET /api/platform/airlines`
- `POST /api/platform/airlines`
- `GET /api/platform/airlines/{airline_id}`
- `PUT /api/platform/airlines/{airline_id}`
- Platform knowledge, procedure, EMD note, and source endpoints under `/api/platform/airlines`
- `GET /api/platform/airline-knowledge/{knowledge_id}`
- `PUT /api/platform/airline-knowledge/{knowledge_id}`
- `POST /api/platform/airline-knowledge/{knowledge_id}/publish`
- `POST /api/platform/airline-knowledge/{knowledge_id}/archive`
- `GET /api/agencies/{agency_id}/airline-intelligence/search`
- `GET /api/agencies/{agency_id}/airlines/{airline_id}/intelligence`
- `GET /api/agencies/{agency_id}/airline-knowledge/{knowledge_id}`
- Agency override and usage endpoints under `/api/agencies/{agency_id}/airlines/{airline_id}` and `/api/agencies/{agency_id}/airline-knowledge/{knowledge_id}`
- `GET /api/agencies/{agency_id}/document-templates`
- `POST /api/agencies/{agency_id}/document-templates`
- `GET /api/agencies/{agency_id}/document-templates/{template_id}`
- `PUT /api/agencies/{agency_id}/document-templates/{template_id}`
- `POST /api/agencies/{agency_id}/document-templates/{template_id}/archive`
- `GET /api/platform/documents/templates`
- `POST /api/platform/documents/templates/seed-defaults`
- `GET /api/agencies/{agency_id}/documents/templates`
- `GET /api/agencies/{agency_id}/documents/templates/{template_id}`
- `POST /api/agencies/{agency_id}/documents/context-preview`
- `GET /api/agencies/{agency_id}/documents/render-jobs`
- `POST /api/agencies/{agency_id}/documents/render-jobs`
- `GET /api/agencies/{agency_id}/documents/render-jobs/{render_job_id}`
- `POST /api/agencies/{agency_id}/documents/render-jobs/{render_job_id}/rerender`
- `GET /api/agencies/{agency_id}/documents/packages`
- `POST /api/agencies/{agency_id}/documents/packages`
- `GET /api/agencies/{agency_id}/documents/packages/{package_id}`
- `POST /api/agencies/{agency_id}/documents/share-records`
- Platform GDS parser endpoints under `/api/platform/gds-parser/*`
- Agency GDS parser endpoints under `/api/agencies/{agency_id}/gds-parser/*`
- Platform airline policy ingestion endpoints under `/api/platform/airline-policy/*`
- Agency airline policy library endpoints under `/api/agencies/{agency_id}/airline-policy/*`
- Platform service taxonomy endpoints under `/api/platform/service-taxonomy/*`
- Agency service taxonomy endpoints under `/api/agencies/{agency_id}/service-taxonomy/*`
- Platform service mechanics endpoints under `/api/platform/service-mechanics/*`
- Agency service mechanics endpoints under `/api/agencies/{agency_id}/service-mechanics/*`
- Platform ancillary pricing endpoints under `/api/platform/ancillary-pricing/*`
- Agency ancillary pricing endpoints under `/api/agencies/{agency_id}/ancillary-pricing/*`
- `GET /api/agencies/{agency_id}/documents`
- `GET /api/agencies/{agency_id}/documents/{document_id}`
- `POST /api/agencies/{agency_id}/documents/{document_id}/archive`
- `GET /api/agencies/{agency_id}/documents/{document_id}/timeline`
- `GET /api/agencies/{agency_id}/document-deliveries/{delivery_id}/diagnostics`
- Render document actions under offers, bookings, tickets, EMDs, and invoices.
- `GET /api/portal/me`
- `GET /api/portal/dashboard`
- `GET /api/portal/profile`
- `GET /api/portal/passengers`
- `GET /api/portal/passengers/{passenger_id}`
- `GET /api/portal/requests`
- `POST /api/portal/requests`
- `GET /api/portal/requests/{request_id}`
- `POST /api/portal/requests/{request_id}/messages`
- `GET /api/portal/offers`
- `GET /api/portal/offers/{offer_id}`
- `POST /api/portal/offers/{offer_id}/accept`
- `POST /api/portal/offers/{offer_id}/reject`
- `GET /api/portal/bookings`
- `GET /api/portal/bookings/{booking_id}`
- `GET /api/portal/documents`
- `GET /api/portal/documents/{document_id}`
- `POST /api/portal/documents/{document_id}/acknowledge`
- `GET /api/portal/actions`
- `GET /api/portal/invoices`
- `GET /api/portal/invoices/{invoice_id}`
- `GET /api/portal/payments`
- `GET /api/portal/refund-exchange-cases`
- `GET /api/portal/refund-exchange-cases/{case_id}`
- `GET /api/reference`
- `GET /api/reference/{domain}`
- `POST /api/reference/{domain}`
- `PUT /api/reference/{domain}/{record_id}`
- `PATCH /api/reference/{domain}/{record_id}/activate`
- `PATCH /api/reference/{domain}/{record_id}/deactivate`
- `POST /api/reference/suggestions`
- `GET /api/reference/suggestions`
- `PATCH /api/reference/suggestions/{suggestion_id}/approve`
- `PATCH /api/reference/suggestions/{suggestion_id}/reject`
- `POST /api/reference/import-batches`
- `GET /api/reference/import-batches`
- `POST /api/reference/bootstrap`
- `POST /api/reference/seed`
- `GET /api/form-profiles/field-definitions`
- `POST /api/form-profiles/field-definitions/bootstrap`
- `POST /api/form-profiles/field-definitions`
- `PUT /api/form-profiles/field-definitions/{field_id}`
- `GET /api/agencies/{agency_id}/form-profiles`
- `POST /api/agencies/{agency_id}/form-profiles`
- `GET /api/agencies/{agency_id}/form-profiles/{profile_id}/effective`
- `PUT /api/agencies/{agency_id}/form-profiles/{profile_id}/fields`
- `GET /api/public/form-profiles/effective`

## Portal Demo Access

Portal preview can still use development-only headers when `DEMO_AUTH_ENABLED=true`:

```bash
X-Demo-Role: portal_client
X-Demo-Client-Email: anna.client@example.com
```

Seeded portal emails are `anna.client@example.com` and `travel@orbitex.example.com`. Bearer-token login is now preferred. These headers are only for local/demo visibility testing.

## Portal Action Permission Rules

- Portal actions use the authenticated portal account's `agency_id` and `client_id`; payloads cannot choose another tenant or client.
- New portal requests may include only passengers with an active relationship that has `can_request_travel=true`, or an active `self` relationship.
- Public and portal request submissions are stored as request intakes first; staff must explicitly triage and convert them before an operational request exists.
- Portal messages are always `client_visible`; clients cannot create internal notes.
- Offer acceptance/rejection updates the offer and queues staff review. It does not create bookings, tickets, EMDs, invoices, or payments.
- Document acknowledgement applies only to visible rendered documents for the current client and is idempotent.

## Canonical Layers

- AeroAssist Global / Platform Owner.
- Agency Workspace.
- Airline Intelligence.
- Client / Passenger Portal.

Phase 1 implements the platform and agency workspace foundation. Phase 2 adds CRM client/passenger relationship foundations. Phase 3 adds request intake, messages, tasks, and timeline foundations. Phase 4 adds manual offer building and send snapshots. Phase 5 adds manual booking, ticket, EMD, invoice, and payment tracking. Phase 6 adds Airline Intelligence as source-backed decision support with agency overrides. Phase 7 adds branded HTML document previews from immutable render-time snapshots. Phase 8 adds read-only client portal visibility over already-created agency records. Phase 13 adds printable HTML exports and a manual email delivery foundation. Phase 14 hardens export storage, retention metadata, and delivery attempt tracking. Phase 15 adds simplified ReportLab PDF exports from stored snapshots. Phase 16 adds staff-controlled SMTP secret resolution and delivery diagnostics. Phase 17 hardens production configuration, readiness checks, and deployment env handling. Phase 18 adds Docker/Compose packaging for Hostinger VPS deployment. Phase 19 adds reverse proxy/TLS templates, backup scripts, restore guidance, and operations runbooks. Phase 20 adds first-deployment checklists, preflight, security checks, and troubleshooting. Phase 21 adds production owner bootstrap, go-live deployment notes, reboot verification, and nginx/TLS migration hardening. Phase 22 adds production agency onboarding, first-workspace setup, and staff invitation preparation. Phase 23 adds combined backup automation, checksum/age verification, conservative pruning, systemd timer templates, and lightweight host health/status scripts. Phase 24 adds staff invitation acceptance, one-time manual invite links, token-safe listing/validation/revocation, role restrictions, and invitation-only account activation. Phase 25 adds document storage lifecycle metadata, safe storage health/list/action APIs, delivery provider readiness placeholders, and a storage operations UI while keeping automatic delivery and public links disabled. Phase 26 adds public/portal request intake records, staff triage actions, explicit conversion into canonical operational requests, source intake linkage, and duplicate conversion guards. Phase 27 adds a structured operational request builder with inline client/passenger creation, route segments, service detail payloads, and intake conversion alignment. Phase 27.1 corrects mobility assistance device/code separation. Phase 27.2 makes WCHR/WCHS/WCHC/MAAS/MEDA/BLND/DEAF advisory recommendations derived from assessment answers with staff confirmation/override. Phase 28 adds controlled agency branding/theme settings, safe logo handling, and a shared CSS-variable personalization layer. Phase 28.1 adds a professional app shell, sidebar navigation, responsive drawer, and key agency page polish. Phase 29 adds controlled agency website settings, CMS pages/sections, public published-site JSON, and a simple public renderer. Phase 30 adds richer CMS blocks, explicit publishing/offline behavior, inner public pages, and website-origin intake forms. Phase 30.1 adds logo asset variants, server-side logo preparation, public-safe logo rendering, and stabilized agency settings. Phase 31 adds CMS media library assets, generated website image variants, section image picking, and public website visual polish. Phase 32 adds blueprint alignment docs, canonical operations rules, current model inventory, and additive trip/segment-scoping foundations. Phase 33 adds controlled reference domains, manual bootstrap, global reference maintenance APIs, and a service catalogue foundation. Phase 33.1 adds platform-owned reference governance, agency suggestion review, and manual CSV import batches. Phase 34 adds idempotent request normalization into passenger-segment services, pet segment transport, special item segment transport, and derived case flags. Phase 34.1 adds global field definitions, agency form profiles, effective profile resolution, and custom field namespacing. Phase 34.2 adds the platform reference console and enriched country management. Phase 34.3 adds reference enrichment import packs and aviation normalization. Phase 35 adds trip dossiers, request-to-trip conversion, linked request management, copied trip passengers/segments/services, and trip timeline readiness. Phase 36.0 adds unified airline rules, exception rules, passenger service requests, and deterministic SSR/OSI previews. Phase 36.1 adds request/trip-linked offer workspaces, rule-aware offer options, pricing recalculation, internal comparison matrices, snapshots, and recommendation flags. Phase 36.2 adds accepted-offer snapshots, trip operational baselines from accepted options, booking readiness packages, SSR/OSI booking previews, and acceptance lifecycle controls. Phase 36.2.5 adds reference domain consumer mapping, Reference Health & Action Required, domain-aware import preview/apply, enrichment pack governance, and editable operational service catalogue mappings. Phase 36.3 adds booking workspaces and draft manual PNR mirrors created from booking readiness packages. Phase 36.4 adds internal ticket and EMD mirrors, coupons, lifecycle events, service catalogue mapping preservation, and ticket/EMD readiness summaries from booking records. Phase 36.4.5 adds supplementary blueprint sync, canonical route policy, safe AI trace/ADM/GDS sample/airline brand foundations, platform blueprint governance UI, and special-services facade alignment. Phase 36.4.6 adds standalone manual booking/ticket/EMD mirrors, booking import drafts with conservative parse previews, and existing-trip change/exchange mirror foundations. Phase 36.5 adds unified document context, platform default templates, render jobs, packages, and internal/manual share records for offer/trip/booking/ticket/EMD/import/change/service documents. Phase 36.6 adds governed GDS parser profiles, versions, runs, parsed entities, corrections, training samples, evaluations, booking-import parser integration, and parser-run document context. Phase 36.7 adds governed airline policy source ingestion, section detection, deterministic candidate extraction, human review corrections, explicit promotion to approved knowledge, policy UIs, and policy document context. Phase 36.8 adds canonical special/ancillary service taxonomy domains, families, variants, aliases, mapping rules, applicability dimensions, outcome types, candidate taxonomy links, review corrections, and taxonomy UIs. Phase 36.9 adds separate SSR/OSI communication mechanics, EMD/RFIC/RFISC payment mechanics, deterministic mechanics lookup, candidate mechanics links, and mechanics UIs. Phase 37.0 adds ancillary pricing rules/components/applicability/matrices, exception rules, deterministic quote scenarios/results, candidate pricing links, and pricing UIs. Phase 37.1 adds policy comparison profiles/snapshots/rows, service advisor scenarios/results, saved views, policy comparison UI, and service advisor UI. Phase 37.2 adds offer policy advisor contexts, offer-linked airline rows, warnings, decision notes, saved snapshots, and platform/agency offer advisor UIs without automatic airline selection or offer price mutation. Phase 37.3 adds offer decision packs, option evidence, warning summaries, review notes, immutable snapshots, and platform/agency decision pack UIs without automatic ranking, offer price mutation, provider execution, booking, ticketing, EMD issuance, payment, invoice, or settlement. Phase 37.4 adds offer decision explanations, evidence references, decision reasons, acknowledgements, timeline events, immutable audit snapshots, and platform/agency decision explanation UIs without automatic recommendation, offer price mutation, provider execution, booking, ticketing, EMD issuance, payment, invoice, or settlement. Phase 37.5 adds metadata-only offer decision exports, ordered sections, PDF/JSON artifact records, recipient drafts, audit events, and platform/agency decision export UIs without automatic sending, public links, offer price mutation, provider execution, booking, ticketing, EMD issuance, payment, invoice, or settlement. Phase 37.6 adds metadata-only offer decision export previews, preview sections, typed blocks, validations, immutable preview snapshots, and platform/agency preview UIs without real PDF delivery, automatic sending, public links, offer price mutation, provider execution, booking, ticketing, EMD issuance, payment, invoice, or settlement. Phase 37.7 adds metadata-only export approvals, checkpoints, release readiness, holds, and release snapshots. Phase 37.8 adds metadata-only manual delivery handoffs, recipients, attachments, instructions, and handoff snapshots. Phase 37.9 adds metadata-only manual delivery outcomes, manual events, receipt metadata, issue metadata, and outcome snapshots. Phase 38.0 adds metadata-only export audit reviews, findings, checklist items, and review snapshots. Phase 38.1 adds metadata-only export governance records, rules, retention policy metadata, legal basis metadata, archive status metadata, exceptions, and immutable governance snapshots. Pixel-perfect browser PDF rendering, gateway payments, automatic delivery, production domain routing, production integrations, automated policy evaluation, live automated pricing, automatic airline recommendation, visual drag-and-drop document/form building, live SSR/OSI/GDS/NDC/provider execution, live ticket/EMD issuance, real exchange/refund/void execution, invoices/payments/accounting/settlement expansion, portal trip views, airline scraping, external AI policy extraction, and external AI taxonomy/mechanics/pricing/comparison/offer-advisor/decision-pack/explanation/export/preview/governance mapping are still intentionally outside the current implementation.
# Phase 55.1 Airline Master Profile Intelligence

Phase 55.1 enriches the existing canonical `airline_profiles` identity with governed airline aliases, relationships, hubs, operational classification, distribution, service desks, evidence, effective dates, confidence, completeness, and revision history. Platform governance is available at `/platform/airline-master-profiles`; agencies receive approved or published read-only profiles at `/agency/airline-profiles`, with internal notes and restricted source details removed. See [Airline Master Profile Intelligence Foundation](docs/architecture/airline-master-profile-intelligence-foundation.md).

## Phase 55.2 Airline Policy Evidence And Source Governance

Phase 55.2 provides canonical cross-domain evidence provenance, assertion links, authority and confidence assessment, freshness, unsupported-knowledge diagnostics, conflict preservation, review, and access governance. Existing acquisition and policy records remain raw source truth. Platform governance is available at `/platform/airline-evidence`; agencies receive approved read-only summaries at `/agency/airline-evidence`. See [Airline Policy Evidence And Source Governance Foundation](docs/architecture/airline-policy-evidence-source-governance-foundation.md).

## Phase 55.3 Airline Knowledge Versioning And Change Detection

Phase 55.3 reuses canonical airline knowledge governance and adds immutable object snapshots, structured field differences, source/release traceability, downstream impact review, and explicit re-QA or republish metadata. Platform users work at `/platform/knowledge-versions`; agencies see published operational updates at `/agency/knowledge-updates`. Historical operational snapshots are never rewritten. See [Airline Knowledge Versioning And Change Detection Foundation](docs/architecture/airline-knowledge-versioning-change-detection-foundation.md).

## Phase 55.4 Airline Service Coverage And Knowledge Gap Management

Phase 55.4 measures airline and service knowledge through deterministic completeness, confidence, freshness, scenario-test, publication-readiness, and operational-usability scores. It adds a dimensioned coverage matrix, critical-gap readiness guards, gap and remediation metadata, Knowledge Population Toolkit synchronization, Pilot Readiness counts, and agency-safe published coverage. Platform users work at `/platform/airline-service-coverage`; agencies consume read-only published coverage and warnings at `/agency/airline-service-coverage`. See [Airline Service Coverage And Knowledge Gap Management Foundation](docs/architecture/airline-service-coverage-gap-management-foundation.md).

## Phase 55.5 Airline Distribution PSS GDS NDC Capability Intelligence

Phase 55.5 records governed planning intelligence for airline distribution channels, PSS/host context, GDS participation, NDC capability, shopping, booking, fulfillment, servicing, restrictions, evidence, freshness, and manual fallbacks. It explicitly separates capability status from provider readiness and never treats a planning record as live connectivity. Platform users work at `/platform/airline-distribution-capabilities`; agencies consume published read-only planning guidance at `/agency/distribution-capabilities`. See [Airline Distribution PSS GDS NDC Capability Intelligence Foundation](docs/architecture/airline-distribution-pss-gds-ndc-capability-intelligence-foundation.md).

## Phase 55.6 Interline Codeshare and Operating Carrier Intelligence

Phase 55.6 records governed airline relationships and responsibility rules for marketing, operating, validating, ticketing, plating, and handling carriers. It covers codeshare, interline, SPA, alliance, wet lease, franchise, regional affiliates, through-check, baggage, special-service continuity, policy ownership, SSR confirmation, ancillary pricing, ticketing, EMD, airport fulfillment, exchanges, and disruption responsibility. Multi-segment evaluation is advisory and preserves explicit unknown/manual-review states. Platform users work at `/platform/interline-codeshare-intelligence`; agencies use the published advisor at `/agency/interline-codeshare-advisor`. See [Interline, Codeshare, and Operating Carrier Intelligence Foundation](docs/architecture/interline-codeshare-operating-carrier-intelligence-foundation.md).

## Phase 55.7 Fare Family, RBD, Baggage, and Brand Intelligence

Phase 55.7 extends the canonical fare-family model with governed hierarchy, RBD mappings, commercial attributes, baggage allowances and exceptions, comparison profiles, evidence, freshness, and publication scope. Platform users govern the library at `/platform/fare-brand-intelligence`; agency users compare published client-safe products at `/agency/fare-brand-library`. Unknown and interline contexts remain explicit manual-review results, and offer-intelligence packages consume only published projections. No live pricing, availability, provider connectivity, booking, or ticketing is introduced. See [Fare Family, RBD, Baggage, and Brand Intelligence Foundation](docs/architecture/airline-fare-family-rbd-baggage-brand-intelligence-foundation.md).

## Phase 55.8 Airline Contact and Communication Intelligence

Phase 55.8 extends canonical `airline_contacts` with governed desk scope, channels, operating hours, escalation paths, communication requirements, separated internal/supplier/client templates, verification, freshness, evidence, and manual interaction history. Platform users govern intelligence at `/platform/airline-contact-intelligence`; agency staff find published contacts and record interactions at `/agency/airline-contact-directory`. No credentials are stored, and no supplier/client message, provider action, automatic escalation, worker, or AI operation is executed. See [Airline Contact and Communication Intelligence Foundation](docs/architecture/airline-contact-communication-intelligence-foundation.md).

## Phase 55.9 Airline Intelligence Scale and Release Readiness

Phase 55.9 completes Epic 55 with deterministic airline-intelligence scale and release readiness. It reuses all preceding Epic 55 records, stores readiness profiles, assessments, checks, candidates, gates, decisions, population waves, and issues, and exposes platform governance at `/platform/airline-intelligence-readiness` plus assigned released agency coverage at `/agency/airline-intelligence-readiness`. A critical gate can never be averaged away; release decisions are audited human metadata and never automatically publish, seed production, call providers, use AI, run workers, or rewrite historical snapshots. See [Airline Intelligence Scale and Release Readiness Foundation](docs/architecture/airline-intelligence-scale-release-readiness-foundation.md).

## Phase 56.0 Canonical Journey And Itinerary Representation

Phase 56.0 adds the canonical Journey Engine presentation layer over existing Request, Trip, Offer, Booking, Ticket, EMD, Passenger, service, and segment records. Agency staff use `/agency/journeys` to project source-linked itinerary options, legs, segments, connections, fare brands, services, warnings, presentation settings, and immutable snapshots; Platform diagnostics use `/platform/journey-engine`. Operational entities remain source truth, finalized snapshots cannot be edited or physically deleted, and no live availability, pricing, provider connectivity, scraping, external call, AI, worker, or automatic publication is introduced. See [Canonical Journey and Itinerary Representation Foundation](docs/architecture/canonical-journey-itinerary-representation-foundation.md).

## Phase 56.1 Journey Segment Authoring And Intelligent Import

Phase 56.1 adds the governed agent workspace at `/agency/journey-authoring` and read-only Platform diagnostics at `/platform/journey-authoring`. It preserves raw text, adapts existing GDS Parser and Booking Import Draft output into editable segment drafts, records field provenance and correction history, enriches only from governed internal reference data, calculates schedule values only from explicit timezone-aware data, validates chronology and connections, and explicitly applies approved drafts through the canonical Phase 56.0 Journey service. It does not search live schedules, price, call providers, scrape, use AI, run workers, or publish snapshots. See [Journey Segment Authoring and Intelligent Import Workspace Foundation](docs/architecture/journey-segment-authoring-intelligent-import-workspace-foundation.md).

## Phase 56.2 Journey Option And Fare Brand Composition

Phase 56.2 adds the agency workspace at `/agency/journey-option-composition` and read-only Platform diagnostics at `/platform/journey-option-compositions`. It composes canonical Journey segment references into ordered itinerary alternatives, combines governed or explicitly manual fare-brand metadata with validated agency-entered commercial amounts, projects advisory passenger-service warnings, compares alternatives, and creates immutable snapshots plus explicit offer-handoff traces. It performs no live pricing or availability lookup, provider operation, publication, booking, ticketing, EMD issuance, payment, AI, scraping, or background work. See [Journey Option and Fare Brand Composition Workspace Foundation](docs/architecture/journey-option-fare-brand-composition-workspace-foundation.md).

## Phase 56.3 Journey Comparison And Client Presentation

Phase 56.3 adds the agency workspace at `/agency/journey-comparison-presentations` and read-only Platform diagnostics at `/platform/journey-comparison-presentations`. It projects Phase 56.2 options into deterministic itinerary, connection, fare-brand, price, baggage, flexibility, and passenger-service comparisons; preserves unknown and manual-review states; separates client-safe from internal content; requires explicit agent preference; and creates immutable snapshots, reviews, and metadata-only Offer or Document handoff traces. It performs no live fare or availability lookup, public sharing, publication, rendering, messaging, provider action, booking, ticketing, EMD issuance, AI, scraping, or background work. See [Journey Comparison and Client Presentation Foundation](docs/architecture/journey-comparison-client-presentation-foundation.md).

Phase 56.4 embeds Delivery & Responses in the canonical Offer Workspace at `/agency/offers/{offer_id}` and retains `/agency/offer-deliveries` only as a guarded contextual deep route. The distinct authenticated client experience remains at `/portal/travel-options`, and read-only Platform diagnostics remain at `/platform/offer-delivery-diagnostics`. It releases a sanitized copy of one finalized Phase 56.3 snapshot as an immutable, hashed version; authorizes recipients through existing Client Portal identity and client/passenger relationships; records option/fare selection, acknowledgements, questions, and explicit decisions; and provides guarded integration with canonical Offer Acceptance and Document packages. It performs no live pricing or availability lookup, anonymous sharing, provider operation, payment, booking, ticketing, EMD issuance, uncontrolled messaging, AI, scraping, background work, or automatic production seeding. See [Offer Delivery and Client Interaction Foundation](docs/architecture/offer-delivery-client-interaction-foundation.md) and [Product Surface and Workspace Governance](docs/architecture/product-surface-workspace-governance.md).

## Phase 56.5.1 Phase Marker And Regression Integrity

Phase 56.5.1 centralizes the current backend build marker as `phase_56_5_1_regression_integrity_foundation`, adds deterministic numeric phase comparison, and separates current application metadata from capability introduction and immutable historical provenance. Epic 55 and Phase 56 historical smokes now require the running application to be at or after their capability phase instead of requiring a stale exact build marker. No route, collection, product behavior, stored snapshot, or frontend surface changes. See [Phase Marker and Regression Integrity Foundation](docs/architecture/phase-marker-regression-integrity-foundation.md).

## Phase 56.5.2 Legacy Regression Suite Migration

Phase 56.5.2 advances the canonical marker to `phase_56_5_2_legacy_regression_suite_migration` and migrates the remaining historical smokes to evidence-backed minimum application phases while preserving capability assertions and immutable provenance. A complete checked-in inventory, deterministic validator, documented exact-current allowlist, narrow batch runner, and lightweight readiness counts make all smoke phase semantics explicit. No product route, schema, collection, stored record, tenant boundary, service behavior, production data, or frontend surface changes. See [Legacy Regression Suite Migration](docs/architecture/legacy-regression-suite-migration.md).

## Phase 56.5.3 GitHub Actions Continuous Integration

Phase 56.5.3 advances the canonical marker to `phase_56_5_3_github_actions_continuous_integration_foundation` and adds layered, least-privilege GitHub Actions validation. Pull requests and `main` pushes receive fast compile, inventory, import, frontend-build, production-Docker, and focused-smoke coverage; the complete inventory runs only on manual dispatch or a Monday/Wednesday/Friday schedule. Inventory-defined CI tiers and fresh-backend isolation keep selection explicit, while production image checks prevent tracked runtime files such as `backend/smoke_inventory.py` from being omitted again. CI uses only disposable local services and never deploys, publishes images, or requires production credentials. See [GitHub Actions Continuous Integration Foundation](docs/architecture/github-actions-continuous-integration-foundation.md).

## Phase 56.5.4 Authentication, Security, and HTTP Hardening

Phase 56.5.4 advances the canonical marker to `phase_56_5_4_authentication_security_http_hardening_foundation`. It preserves existing opaque bearer tokens and identity/session records while adding configurable exponential login backoff, temporary account locks, failure reset windows, bounded token clock skew, explicit token diagnostics, and metadata-only refresh policy. FastAPI now emits request correlation IDs, safe structured JSON errors, redacted security events, strict production CORS validation, and configurable CSP/HSTS/frame/MIME/referrer/permissions/cross-origin headers. Production `/api/readiness` is a lightweight public summary; detailed `/api/system/readiness` is explicitly enabled and key-protected in production. No OAuth, SSO, product workflow, provider operation, booking execution, AI, or commercial behavior is added. See [Authentication, Security, and HTTP Hardening Foundation](docs/architecture/authentication-security-http-hardening-foundation.md).

## Phase 56.5.5 MongoDB Security, Backup, and Disaster Recovery

Phase 56.5.5 advances the canonical marker to `phase_56_5_5_mongodb_security_backup_disaster_recovery_foundation`. Production configuration now supports fail-closed authenticated MongoDB, distinct administrative and least-privilege application identities, an empty-volume app-user initializer, and internal-only database networking. Existing Hostinger backup tooling now creates timestamped archives, SHA-256 checksums, non-sensitive manifests, MongoDB dry-run inspection, minimum-count retention guards, validation-only restore plans, and disposable count-verified restore rehearsals. Existing populated volumes require the documented manual maintenance-window migration; no production data, volume, deployment, scheduler, or restore is changed automatically. See [MongoDB Security, Backup, and Disaster Recovery Foundation](docs/architecture/mongodb-security-backup-disaster-recovery-foundation.md) and the [operational runbook](deploy/hostinger/MONGODB_DISASTER_RECOVERY_RUNBOOK.md).

## Phase 56.5.6 Persistence Scalability and Tenant Query Hardening

Phase 56.5.6 advances the canonical marker to `phase_56_5_6_persistence_scalability_tenant_query_hardening_foundation`. It adds configurable bounded pagination, stable allowlisted sorting, tenant-bound cursors, filter/operator safety, separate agency and platform/global repository helpers, an explicit collection ownership registry, additive index governance, redacted slow-query diagnostics, and timeout-bounded detailed readiness. High-risk operational and airline-readiness list services now use governed reads while preserving routes and response shapes; remaining legacy call sites are inventoried under a non-increasing static ceiling. No product page, destructive migration, index drop, production action, provider call, or external telemetry is introduced. See [Persistence Scalability and Tenant Query Hardening Foundation](docs/architecture/persistence-scalability-tenant-query-hardening-foundation.md).

## Phase 56.5.7 Observability, Diagnostics, and Performance Telemetry

Phase 56.5.7 advances the canonical marker to `phase_56_5_7_observability_diagnostics_performance_telemetry_foundation`. It adds one privacy-safe structured event envelope, production JSON and development human logging, separate request/correlation propagation, HTTP/error/security/query telemetry, configurable slow-operation thresholds, fixed-cardinality process counters, readiness timing, startup/shutdown events, centralized redaction, safe deployment identifiers, and protected Platform aggregate diagnostics. Public readiness and existing error response contracts remain compatible. Docker log rotation and nginx request-ID forwarding are documented and bounded; no external telemetry provider, product workflow, production access, deployment, or data migration is introduced. See [Observability, Diagnostics, and Performance Telemetry Foundation](docs/architecture/observability-diagnostics-performance-telemetry-foundation.md).

## Phase 56.5.8 Final Stabilization and Pilot Release Gate

Phase 56.5.8 advances the canonical marker to `phase_56_5_8_final_stabilization_pilot_release_gate`. It adds a deterministic environment-aware pilot release assessment, hard blockers, warnings, bounded operator attestations, immutable hashes, a read-only CLI, governed full-validation orchestration, protected Platform diagnostics, and a public-safe blocked-by-default readiness summary. Repository, CI, disposable, migration, and production evidence remain separate; no local or Docker result is promoted into production truth. Human sign-off remains mandatory, and no deployment, MongoDB migration, backup, restore, approval, provider action, or production access is automated. See [Final Stabilization and Pilot Release Gate](docs/architecture/final-stabilization-pilot-release-gate.md) and [Controlled Pilot Release Runbook](deploy/hostinger/PILOT_RELEASE_RUNBOOK.md).

## Phase 57.0 Pilot Operations and Release Readiness

Phase 57.0 advances the canonical marker to `phase_57_0_pilot_operations_release_readiness`. It adds a Platform-only operations console at `/platform/pilot-operations`, persists immutable deployment/smoke/backup/restore/production-validation/release-assessment/sign-off evidence, groups the existing deterministic release gate into eight operational assessment areas, records health history, and exposes protected bounded telemetry. Platform Owner controls existing-agency pilot enrollment and isolated prefixed synthetic metadata datasets with audited soft removal. Public health and readiness remain free of operational diagnostics and pilot data. No provider, GDS, payment, booking, ticketing, automatic release approval, migration, backup, restore, or production seed is executed. See [Pilot Operations and Release Readiness](docs/architecture/pilot-operations-release-readiness.md).
