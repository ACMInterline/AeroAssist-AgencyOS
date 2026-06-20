# AeroAssist AgencyOS

Multi-tenant SaaS foundation for micro and small travel agencies.

This repository currently contains the Phase 0 architecture specifications and Phase 1 implementation foundation.

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

## Intentionally Not Included Yet

- CRM screens.
- Client/passenger models.
- Request workflow.
- Offer builder.
- Airline intelligence UI.
- Client portal workflows.
- Branded documents.
- Payment processing.
- Accounting.

## Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn server:app --reload
```

The backend starts on `http://localhost:8000`.

By default the API uses in-memory storage so Phase 1 can run without a database:

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
- `GET /api/reference`
- `GET /api/reference/{domain}`
- `POST /api/reference/seed`

## Canonical Layers

- AeroAssist Global / Platform Owner.
- Agency Workspace.
- Airline Intelligence.
- Client / Passenger Portal.

Phase 1 implements only the platform and agency workspace foundation needed before later layers can safely add CRM, requests, offers, airline intelligence, documents, and portal access.
