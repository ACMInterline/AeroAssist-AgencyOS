# AeroAssist AgencyOS

Multi-tenant SaaS foundation for micro and small travel agencies.

This repository currently contains the Phase 0 architecture specifications, Phase 1 implementation foundation, Phase 2 CRM/client-passenger relationship foundation, Phase 3 request intake foundation, Phase 4 manual offer builder foundation, Phase 5 booking/finance tracking foundation, Phase 6 Airline Intelligence foundation, Phase 7 branded HTML document output foundation, and Phase 8 read-only client portal visibility foundation.

## Project Structure

- `backend/` FastAPI API, Pydantic models, tenant/auth helpers, seed service, and Phase 1 routers.
- `frontend/` Vite/React route shell for public, platform, agency, and portal layers.
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

## Intentionally Not Included Yet

- Production client portal authentication, invitations, sessions, or account security.
- Client request submission or editable portal workflows.
- Offer acceptance/rejection workflows.
- PDF document export.
- Email/share/public document links.
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

By default the API uses in-memory storage so the current foundation can run without a database:

```bash
AEROASSIST_DB_MODE=memory
```

To use MongoDB locally:

```bash
docker compose up -d mongo
AEROASSIST_DB_MODE=mongo uvicorn server:app --reload
```

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend starts on `http://localhost:5173`.

## Seed Data

Seed data runs automatically on backend startup. It can also be triggered through:

```bash
curl -X POST http://localhost:8000/api/reference/seed \
  -H "X-Demo-User-Email: owner@aeroassist.dev"
```

Seeded demo login:

- Email: `owner@aeroassist.dev`
- Role: `platform_owner`

Phase 1 demo auth uses the `X-Demo-User-Email` header. This is development-only and must be replaced before production authentication.

## Useful Endpoints

- `GET /api/health`
- `GET /api/auth/me`
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
- `GET /api/agencies/{agency_id}/clients`
- `POST /api/agencies/{agency_id}/clients`
- `GET /api/agencies/{agency_id}/clients/{client_id}`
- `PUT /api/agencies/{agency_id}/clients/{client_id}`
- `POST /api/agencies/{agency_id}/clients/{client_id}/archive`
- `POST /api/agencies/{agency_id}/clients/{client_id}/restore`
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
- Render document actions under offers, bookings, tickets, EMDs, and invoices.
- `GET /api/portal/me`
- `GET /api/portal/dashboard`
- `GET /api/portal/profile`
- `GET /api/portal/passengers`
- `GET /api/portal/passengers/{passenger_id}`
- `GET /api/portal/requests`
- `GET /api/portal/requests/{request_id}`
- `GET /api/portal/offers`
- `GET /api/portal/offers/{offer_id}`
- `GET /api/portal/bookings`
- `GET /api/portal/bookings/{booking_id}`
- `GET /api/portal/documents`
- `GET /api/portal/documents/{document_id}`
- `GET /api/portal/invoices`
- `GET /api/portal/invoices/{invoice_id}`
- `GET /api/portal/payments`
- `GET /api/reference`
- `GET /api/reference/{domain}`
- `POST /api/reference/seed`

## Portal Demo Access

Phase 8 portal preview uses development-only headers:

```bash
X-Demo-Role: portal_client
X-Demo-Client-Email: anna.client@example.com
```

Seeded portal emails are `anna.client@example.com` and `travel@orbitex.example.com`. These headers are only for local/demo visibility testing and must be replaced before production client authentication.

## Canonical Layers

- AeroAssist Global / Platform Owner.
- Agency Workspace.
- Airline Intelligence.
- Client / Passenger Portal.

Phase 1 implements the platform and agency workspace foundation. Phase 2 adds CRM client/passenger relationship foundations. Phase 3 adds request intake, messages, tasks, and timeline foundations. Phase 4 adds manual offer building and send snapshots. Phase 5 adds manual booking, ticket, EMD, invoice, and payment tracking. Phase 6 adds Airline Intelligence as source-backed decision support with agency overrides. Phase 7 adds branded HTML document previews from immutable render-time snapshots. Phase 8 adds read-only client portal visibility over already-created agency records. PDF export, gateway payments, production portal auth, production integrations, automated policy evaluation, automated pricing, and airline scraping are still intentionally outside the current implementation.
