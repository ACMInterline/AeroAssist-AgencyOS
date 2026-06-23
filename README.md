# AeroAssist AgencyOS

Multi-tenant SaaS foundation for micro and small travel agencies.

This repository currently contains the Phase 0 architecture specifications, Phase 1 implementation foundation, Phase 2 CRM/client-passenger relationship foundation, Phase 3 request intake foundation, Phase 4 manual offer builder foundation, Phase 5 booking/finance tracking foundation, Phase 6 Airline Intelligence foundation, Phase 7 branded HTML document output foundation, Phase 8 read-only client portal visibility foundation, Phase 9 persistence/tenant hardening foundation, Phase 10 authentication/invitation foundation, Phase 11 controlled client portal actions, Phase 12 refund/exchange tracking, Phase 13 printable document export/email delivery foundation, Phase 14 document delivery hardening, Phase 15 production PDF rendering/delivery infrastructure, Phase 16 production delivery operations/secret resolution, Phase 17 production configuration hardening, Phase 18 Docker/Hostinger VPS packaging, Phase 19 VPS operations runbooks, and Phase 20 first deployment preparation.

## Project Structure

- `backend/` FastAPI API, Pydantic models, tenant/auth helpers, seed service, persistence wrappers, smoke scripts, Dockerfile, and implemented Phase 1-20 foundations.
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

## Intentionally Not Included Yet

- Production client portal authentication, invitations, sessions, or account security.
- Client request submission or editable portal workflows.
- Offer acceptance/rejection workflows.
- Pixel-perfect browser HTML-to-PDF rendering and legal/fiscal invoice compliance.
- Public share links.
- Refund/exchange execution outside manual tracking.
- Payment gateway processing.
- Full accounting or ledger reconciliation.
- Automated ticketing, GDS, NDC, OTA, or supplier integrations.
- Airline scraping, automated policy evaluation, and automated pricing.

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

Invitation endpoints store only token hashes. In local/demo mode the raw invitation token and `/login?invite=...` link are returned to support manual testing without email delivery. Production responses should not expose raw tokens unless an explicit development flag is enabled.

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
APP_BASE_URL=https://agencyos.example.com deploy/hostinger/scripts/smoke_production.sh
```

Use `deploy/hostinger/nginx/aeroassist.conf.example` as the host-level nginx/TLS template.

For the actual first VPS deployment, start here:

```text
deploy/hostinger/FIRST_DEPLOYMENT_CHECKLIST.md
```

Then run the non-mutating preflight before starting services:

```bash
APP_DIR=/opt/aeroassist/AeroAssist-AgencyOS deploy/hostinger/scripts/preflight.sh
```

## Smoke Scripts

With the backend running:

```bash
python3 backend/scripts/smoke_backend.py
python3 backend/scripts/check_portal_isolation.py
```

The backend smoke calls the seed endpoint twice and verifies counts remain stable, then exercises core module list/detail endpoints. The portal isolation smoke checks both seeded portal clients, verifies cross-client detail denial, and scans portal JSON for internal field names.

## Production Readiness Warning

Phase 20 adds first-deployment checklists, preflight, post-deployment security checks, and troubleshooting, but it is not a complete operations stack. Production use still requires migrations, automated backup retention/off-server backup policy, monitoring/alerting, broader automated tests, provider webhook/bounce handling decisions, and object-storage lifecycle policy.

## Useful Endpoints

- `GET /api/health`
- `GET /api/readiness`
- `GET /api/auth/me`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `POST /api/auth/invitations/accept`
- `POST /api/auth/change-password`
- `POST /api/auth/demo-login`
- `GET /api/platform/health`
- `GET /api/platform/summary`
- `GET /api/agencies`
- `POST /api/agencies`
- `GET /api/agencies/{agency_id}`
- `PUT /api/agencies/{agency_id}`
- `GET /api/agencies/{agency_id}/settings`
- `PUT /api/agencies/{agency_id}/settings`
- `GET /api/agencies/{agency_id}/staff`
- `POST /api/agencies/{agency_id}/staff`
- `POST /api/agencies/{agency_id}/staff/invitations`
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
- `GET /api/agencies/{agency_id}/requests/{request_id}`
- `PUT /api/agencies/{agency_id}/requests/{request_id}`
- `POST /api/agencies/{agency_id}/requests/{request_id}/archive`
- `POST /api/agencies/{agency_id}/requests/{request_id}/restore`
- `POST /api/agencies/{agency_id}/requests/{request_id}/status`
- `GET/POST /api/agencies/{agency_id}/requests/{request_id}/passengers`
- `GET/POST /api/agencies/{agency_id}/requests/{request_id}/segments`
- `GET/POST /api/agencies/{agency_id}/requests/{request_id}/services`
- `GET/POST /api/agencies/{agency_id}/requests/{request_id}/messages`
- `GET/POST /api/agencies/{agency_id}/requests/{request_id}/tasks`
- `GET /api/agencies/{agency_id}/requests/{request_id}/timeline`
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
- `POST /api/reference/seed`

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
- Portal messages are always `client_visible`; clients cannot create internal notes.
- Offer acceptance/rejection updates the offer and queues staff review. It does not create bookings, tickets, EMDs, invoices, or payments.
- Document acknowledgement applies only to visible rendered documents for the current client and is idempotent.

## Canonical Layers

- AeroAssist Global / Platform Owner.
- Agency Workspace.
- Airline Intelligence.
- Client / Passenger Portal.

Phase 1 implements the platform and agency workspace foundation. Phase 2 adds CRM client/passenger relationship foundations. Phase 3 adds request intake, messages, tasks, and timeline foundations. Phase 4 adds manual offer building and send snapshots. Phase 5 adds manual booking, ticket, EMD, invoice, and payment tracking. Phase 6 adds Airline Intelligence as source-backed decision support with agency overrides. Phase 7 adds branded HTML document previews from immutable render-time snapshots. Phase 8 adds read-only client portal visibility over already-created agency records. Phase 13 adds printable HTML exports and a manual email delivery foundation. Phase 14 hardens export storage, retention metadata, and delivery attempt tracking. Phase 15 adds simplified ReportLab PDF exports from stored snapshots. Phase 16 adds staff-controlled SMTP secret resolution and delivery diagnostics. Phase 17 hardens production configuration, readiness checks, and deployment env handling. Phase 18 adds Docker/Compose packaging for Hostinger VPS deployment. Phase 19 adds reverse proxy/TLS templates, backup scripts, restore guidance, and operations runbooks. Phase 20 adds first-deployment checklists, preflight, security checks, and troubleshooting. Pixel-perfect browser PDF rendering, gateway payments, automatic delivery, public links, production integrations, automated policy evaluation, automated pricing, and airline scraping are still intentionally outside the current implementation.
