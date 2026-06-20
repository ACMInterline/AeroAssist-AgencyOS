# Phase 1 Implementation

## Goal

Create the clean application foundation, multi-tenant data model base, auth/role scaffolding, project structure, and validation-ready database layer for AeroAssist AgencyOS.

## Implemented Backend Models

- `PlatformUser`
- `Agency`
- `AgencyWorkspace`
- `AgencyStaffMembership`
- `GlobalReferenceRecord`
- `AuditEvent`

No client, passenger, request, offer, booking, ticket, EMD, invoice, payment, document-generation, or airline-intelligence operational models are implemented in Phase 1.

## Implemented Backend Endpoints

- `GET /api/health`
- `GET /api/auth/me`
- `POST /api/auth/demo-login`
- `GET /api/platform/health`
- `GET /api/platform/summary`
- `GET /api/platform/audit-events`
- `GET /api/audit-events`
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
- `POST /api/reference`
- `POST /api/reference/seed`

## Tenant Isolation

- Every agency-owned Phase 1 record includes `agency_id`.
- Agency workspace settings are scoped by `agency_id`.
- Staff membership is scoped by `agency_id`.
- Audit events may include nullable `agency_id` for platform-level events.
- Platform-owned reference records do not include `agency_id`.
- Role helpers centralize platform and agency access checks.

## Demo Auth

Phase 1 uses `X-Demo-User-Email` for local development. It is isolated to demo/dev usage and documented in `README.md`.

## Seed Data

Seed data creates:

- One platform owner demo user.
- One demo agency.
- One agency owner membership.
- Foundation reference data for countries, currencies, timezones, platform roles, agency roles, agency statuses, subscription statuses, website statuses, and portal statuses.

## Frontend Routes

- `/`
- `/login`
- `/platform`
- `/agency`
- `/portal`

The frontend exposes only Phase 1 route shells and dashboard summaries. Later modules are described as coming next but are not represented as working navigation or fake features.

## Known Limitations

- No production auth provider yet.
- In-memory storage is default for local validation.
- MongoDB mode is available but not required for Phase 1 checks.
- No CRM, requests, offers, airline intelligence UI, portal workflows, branded documents, or payment tracking yet.
