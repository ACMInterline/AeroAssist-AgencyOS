# AeroAssist AgencyOS

Multi-tenant SaaS foundation for micro and small travel agencies.

This repository currently contains the Phase 0 architecture specifications through Phase 36.7 airline policy ingestion foundation, including CRM, requests, trips, reference/service catalogue governance, rules/services, offer builder, offer acceptance/booking readiness, booking/ticket/EMD mirrors, standalone/import/change/exchange workflows, document foundation, governed GDS parser foundation, and governed airline policy source/extraction/review foundations.

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

## Intentionally Not Included Yet

- Public share links.
- Payment gateway processing.
- Full accounting or ledger reconciliation.
- Automated booking, PNR creation, ticketing, GDS, NDC, OTA, or supplier integrations.
- Airline scraping, external AI policy extraction, automated policy evaluation, automatic global policy promotion, and automated pricing.
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
```

The backend smoke calls the seed endpoint twice and verifies counts remain stable, then exercises core module list/detail endpoints. The portal isolation smoke checks both seeded portal clients, verifies cross-client detail denial, and scans portal JSON for internal field names. The reference service catalogue smoke validates the Phase 36.2.5 consumer map, health/action-required, domain-aware imports, enrichment packs, platform catalogue CRUD, agency consume behavior, and readiness flags. The offer builder smoke creates a request/trip-linked workspace, option, segment, fare bundle, pricing lines, rule evaluation, comparison snapshot, and recommendation. The offer acceptance smoke verifies acceptance snapshots, trip baseline snapshots, booking readiness packages, rebuild, supersede, and cancel. The booking PNR foundation smoke verifies booking workspace creation from readiness, draft manual PNR mirrors, timeline events, rebuild, cancellation, and disabled provider execution. The ticket/EMD foundation smoke verifies draft ticket and EMD mirrors, coupon records, service catalogue mapping preservation, timeline events, readiness summaries, and disabled provider issuance. The supplementary blueprint sync smoke verifies adoption-map APIs, canonical route policy, blueprint readiness flags, safe foundations, and the special-services facade. The standalone/change/exchange smoke verifies manual booking, booking import draft parsing/import, trip change booking mirrors, ticket exchange mirrors, and EMD exchange mirrors. The document foundation smoke verifies context preview, template seeding, render jobs, packages, and internal share records. The GDS parser smoke verifies parser profiles/versions/runs/entities, corrections, training samples, evaluations, booking-import integration, parser document context, and disabled live/external parser flags. The airline policy ingestion smoke verifies source creation, section detection, deterministic candidate extraction, review corrections, explicit promotion, agency-local submission boundaries, policy document context, and disabled external/auto-promotion safeguards.

## Production Readiness Warning

Phase 36.7 adds governed airline policy ingestion on top of parser, document, standalone booking/import/change, and ticket/EMD mirror foundations, but AgencyOS is not a complete operations stack. Production use still requires migrations, off-server backup policy, alerting decisions, broader automated tests, provider webhook/bounce handling decisions, real object-storage integration decisions, automatic invite delivery decisions, broader team management, visual regression automation, domain routing decisions, airline policy governance hardening, client offer sharing hardening, full visual form builder decisions, full GDS grammar/provider reconciliation, live GDS/NDC/provider execution, live ticket/EMD issuance, real exchange/refund/void execution, external data providers, automatic scraping, and deeper CMS publishing hardening.

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

Phase 1 implements the platform and agency workspace foundation. Phase 2 adds CRM client/passenger relationship foundations. Phase 3 adds request intake, messages, tasks, and timeline foundations. Phase 4 adds manual offer building and send snapshots. Phase 5 adds manual booking, ticket, EMD, invoice, and payment tracking. Phase 6 adds Airline Intelligence as source-backed decision support with agency overrides. Phase 7 adds branded HTML document previews from immutable render-time snapshots. Phase 8 adds read-only client portal visibility over already-created agency records. Phase 13 adds printable HTML exports and a manual email delivery foundation. Phase 14 hardens export storage, retention metadata, and delivery attempt tracking. Phase 15 adds simplified ReportLab PDF exports from stored snapshots. Phase 16 adds staff-controlled SMTP secret resolution and delivery diagnostics. Phase 17 hardens production configuration, readiness checks, and deployment env handling. Phase 18 adds Docker/Compose packaging for Hostinger VPS deployment. Phase 19 adds reverse proxy/TLS templates, backup scripts, restore guidance, and operations runbooks. Phase 20 adds first-deployment checklists, preflight, security checks, and troubleshooting. Phase 21 adds production owner bootstrap, go-live deployment notes, reboot verification, and nginx/TLS migration hardening. Phase 22 adds production agency onboarding, first-workspace setup, and staff invitation preparation. Phase 23 adds combined backup automation, checksum/age verification, conservative pruning, systemd timer templates, and lightweight host health/status scripts. Phase 24 adds staff invitation acceptance, one-time manual invite links, token-safe listing/validation/revocation, role restrictions, and invitation-only account activation. Phase 25 adds document storage lifecycle metadata, safe storage health/list/action APIs, delivery provider readiness placeholders, and a storage operations UI while keeping automatic delivery and public links disabled. Phase 26 adds public/portal request intake records, staff triage actions, explicit conversion into canonical operational requests, source intake linkage, and duplicate conversion guards. Phase 27 adds a structured operational request builder with inline client/passenger creation, route segments, service detail payloads, and intake conversion alignment. Phase 27.1 corrects mobility assistance device/code separation. Phase 27.2 makes WCHR/WCHS/WCHC/MAAS/MEDA/BLND/DEAF advisory recommendations derived from assessment answers with staff confirmation/override. Phase 28 adds controlled agency branding/theme settings, safe logo handling, and a shared CSS-variable personalization layer. Phase 28.1 adds a professional app shell, sidebar navigation, responsive drawer, and key agency page polish. Phase 29 adds controlled agency website settings, CMS pages/sections, public published-site JSON, and a simple public renderer. Phase 30 adds richer CMS blocks, explicit publishing/offline behavior, inner public pages, and website-origin intake forms. Phase 30.1 adds logo asset variants, server-side logo preparation, public-safe logo rendering, and stabilized agency settings. Phase 31 adds CMS media library assets, generated website image variants, section image picking, and public website visual polish. Phase 32 adds blueprint alignment docs, canonical operations rules, current model inventory, and additive trip/segment-scoping foundations. Phase 33 adds controlled reference domains, manual bootstrap, global reference maintenance APIs, and a service catalogue foundation. Phase 33.1 adds platform-owned reference governance, agency suggestion review, and manual CSV import batches. Phase 34 adds idempotent request normalization into passenger-segment services, pet segment transport, special item segment transport, and derived case flags. Phase 34.1 adds global field definitions, agency form profiles, effective profile resolution, and custom field namespacing. Phase 34.2 adds the platform reference console and enriched country management. Phase 34.3 adds reference enrichment import packs and aviation normalization. Phase 35 adds trip dossiers, request-to-trip conversion, linked request management, copied trip passengers/segments/services, and trip timeline readiness. Phase 36.0 adds unified airline rules, exception rules, passenger service requests, and deterministic SSR/OSI previews. Phase 36.1 adds request/trip-linked offer workspaces, rule-aware offer options, pricing recalculation, internal comparison matrices, snapshots, and recommendation flags. Phase 36.2 adds accepted-offer snapshots, trip operational baselines from accepted options, booking readiness packages, SSR/OSI booking previews, and acceptance lifecycle controls. Phase 36.2.5 adds reference domain consumer mapping, Reference Health & Action Required, domain-aware import preview/apply, enrichment pack governance, and editable operational service catalogue mappings. Phase 36.3 adds booking workspaces and draft manual PNR mirrors created from booking readiness packages. Phase 36.4 adds internal ticket and EMD mirrors, coupons, lifecycle events, service catalogue mapping preservation, and ticket/EMD readiness summaries from booking records. Phase 36.4.5 adds supplementary blueprint sync, canonical route policy, safe AI trace/ADM/GDS sample/airline brand foundations, platform blueprint governance UI, and special-services facade alignment. Phase 36.4.6 adds standalone manual booking/ticket/EMD mirrors, booking import drafts with conservative parse previews, and existing-trip change/exchange mirror foundations. Phase 36.5 adds unified document context, platform default templates, render jobs, packages, and internal/manual share records for offer/trip/booking/ticket/EMD/import/change/service documents. Phase 36.6 adds governed GDS parser profiles, versions, runs, parsed entities, corrections, training samples, evaluations, booking-import parser integration, and parser-run document context. Phase 36.7 adds governed airline policy source ingestion, section detection, deterministic candidate extraction, human review corrections, explicit promotion to approved knowledge, policy UIs, and policy document context. Pixel-perfect browser PDF rendering, gateway payments, automatic delivery, production domain routing, production integrations, automated policy evaluation, automated pricing, visual drag-and-drop document/form building, live GDS/NDC/provider execution, live ticket/EMD issuance, real exchange/refund/void execution, invoices/payments expansion, portal trip views, airline scraping, and external AI policy extraction are still intentionally outside the current implementation.
