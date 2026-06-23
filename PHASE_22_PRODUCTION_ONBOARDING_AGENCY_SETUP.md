# Phase 22 Production Onboarding And Agency Setup

Phase 22 adds a production-safe path for the platform owner to create the first real agency, create its first workspace, enter that workspace, and prepare the first staff invitation without demo seed data or manual database scripts.

## Production State Recorded

- Production URL: `https://avio.my`.
- Canonical routing sends HTTP and `www` traffic to `https://avio.my`.
- Host nginx owns ports `80` and `443`.
- AgencyOS frontend is local-only behind nginx on `127.0.0.1:8080`.
- Backend and MongoDB remain internal Docker services.
- Old app is stopped and preserved under `/opt/aeroassist`.
- Demo auth, seed-on-startup, and seed endpoint remain disabled in production.

## Backend

Added or hardened:

- `GET /api/agencies` includes workspace and staff membership counts.
- `POST /api/agencies` creates an agency only, validates required production fields, blocks duplicate slugs and practical duplicate names, and writes an audit event.
- `GET /api/agencies/{agency_id}` includes workspace and staff counts.
- `PUT /api/agencies/{agency_id}` validates updates, blocks duplicate names/slugs, and writes an audit event.
- `GET /api/agencies/{agency_id}/workspaces` lists tenant-scoped workspaces.
- `POST /api/agencies/{agency_id}/workspaces` creates a tenant-scoped active workspace and creates a safe active agency owner membership for the platform owner if needed.
- `GET /api/agencies/{agency_id}/staff` remains tenant-scoped and platform-owner accessible through the existing platform override.
- `POST /api/agencies/{agency_id}/staff/invitations` prepares a pending staff invitation and writes an audit event.

Staff invitations do not send email automatically. Production responses do not expose raw invitation tokens or links; delivery remains manual/pending until a controlled delivery phase explicitly enables sending.

## Frontend

Added platform owner onboarding screens:

- `/platform/agencies` lists agencies, workspace counts, staff counts, and provides the create-agency form.
- `/platform/agencies/{agency_id}` shows agency detail, agency basics editing, first-workspace creation, staff memberships, and pending staff invitation preparation.
- The platform summary shows informational onboarding flags for owner, agency, workspace, and staff membership/invitation presence.
- The agency workspace reads `agency_id` from the URL and remembers the selected agency locally, so the platform owner can enter the workspace after creation.

Empty states use production-oriented copy:

> Create your first agency workspace to begin operating AeroAssist.

## First Agency And Workspace Flow

1. Sign in as the production platform owner at `https://avio.my/login`.
2. Open Platform > Agencies.
3. Create the real agency with name, legal name, slug, default currency, country, and timezone.
4. Open the agency detail page.
5. Create the first workspace with workspace name, brand label, default currency, and timezone.
6. Use Enter workspace to open `/agency?agency_id=...`.
7. Prepare a first staff invitation when ready.

No fake customers, operational records, demo accounts, payments, public links, uploads, GDS/NDC integrations, or automatic sending are created by this phase.

## Still Manual

- Delivering the invitation link/token remains manual unless an approved production delivery phase explicitly enables email sending.
- Broader migrations, automated backup retention, off-server backups, monitoring, alerting, and CI/CD are still outside this phase.
- Operational data entry remains manual through existing agency workflows.

## Next Recommended Phase

Phase 23 should focus on backup automation and lightweight monitoring readiness now that the live platform can be onboarded with a real agency and workspace.
