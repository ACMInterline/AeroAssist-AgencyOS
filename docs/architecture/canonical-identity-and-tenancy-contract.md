# Canonical Identity and Tenancy Contract

## Purpose

This contract defines authentication, authorization, and tenant ownership for
the AeroAssist product kernel. It is a corrective security contract, not a new
roadmap phase. It does not change the active Phase 59.0 marker, create a second
RBAC system, migrate production records, or make `workspace_id` an
authorization boundary.

## Canonical Owners

| Concern | Canonical owner | Security role |
|---|---|---|
| Authentication principal | `AuthIdentity` | Credentials, identity type, active state |
| Session | `AuthSession` | Hashed bearer-token session linked only to identity |
| Platform staff profile | `PlatformUser` | Platform role and staff display profile |
| Agency authorization | `AgencyStaffMembership` | Active role edge between staff and one Agency |
| Portal authorization | `PortalAccessMapping` | Explicit active edge from identity to one Client or Passenger |
| Tenant | `Agency` | Root of all agency-owned records |
| CRM client | `ClientProfile` | Canonical client business record |
| Passenger | `PassengerProfile` | Canonical confirmed passenger business record |
| Client/passenger relation | `ClientPassengerRelationship` | Canonical agency-scoped relationship |

Authentication identity is not a Client or Passenger. A CRM email address is
contact data and is never sufficient authority for Portal access.

## Tenant Boundary

`agency_id` is the sole authorization tenant boundary for agency-owned data.

- Every `/api/agencies/{agency_id}/*` request requires an active
  `AgencyStaffMembership` for that exact Agency.
- Platform role alone does not grant Agency operational access.
- An Agency role does not grant Platform access.
- `workspace_id`, headers, request bodies, query parameters, and related-record
  IDs cannot grant or widen tenant scope.
- Canonical create paths set `agency_id` from the authorized route context.
  Tenant-owned IDs are immutable after creation.
- Cross-agency access is denied with HTTP 403; absent or invalid
  authentication is denied with HTTP 401.
- Portal identities cannot enter Platform or Agency staff routes.

The legacy immediate staff-creation endpoint remains as a compatibility
adapter, but it can only link an already active staff `AuthIdentity`; it cannot
create identity-free users or memberships. New staff identities use the
invitation and acceptance flow.

`backend/services/authorization_service.py` resolves these rules per request.
Existing tenant and persistence helpers remain in place; this contract does
not introduce a parallel framework.

## Role And Permission Contract

Permissions are centralized in `authorization_service.PERMISSIONS`. Backend
authorization is authoritative; frontend visibility is only a usability
projection.

| Role | Effective access |
|---|---|
| `platform_owner` | All Platform permissions |
| `platform_admin` | All Platform permissions |
| `platform_knowledge_editor` | View and edit airline knowledge only |
| `platform_support` | Airline-knowledge view and Platform agency support scope |
| `agency_owner` | Agency operational read/write, users, finance, supplier costs, margins, audit, settings |
| `agency_admin` | Agency operational read/write, users, finance, supplier costs, margins, audit, settings |
| `agency_agent` | Agency operational and invoice/payment read/write; no supplier costs, margins, user management, audit, or settings |
| `agency_accountant` | Client/passenger, booking, ticket/EMD, document and task context; finance read/write only |
| `agency_readonly` | Agency operational and finance read; no mutation |
| `client_portal` | Explicit linked Client projection only |
| `passenger_portal` | Explicit linked Passenger projection only |

The vocabulary covers Platform and Agency management, airline knowledge,
clients, passengers, requests, offers, trips, bookings, ticket/EMD records,
documents, tasks, finance, supplier costs, margins, audit, settings, and Portal
Client/Passenger visibility. Unknown Agency route families default to the
existing task/work permission rather than acquiring Platform authority.
Agency Offer Builder and offer-composition responses recursively remove
supplier-cost, commission, and margin fields when the active membership lacks
the corresponding permission, and protected commercial inputs are rejected
rather than accepted blind.

## Authentication And Current User

Bearer tokens remain opaque session tokens. `AuthSession` stores the identity
link, token hash, issued/expiry metadata, and bounded request metadata. Tokens
do not embed mutable Client or Passenger records.

`GET /api/auth/me` returns four clearly separated concerns:

- `identity`: safe `AuthIdentity` fields;
- `authorization.platform`: Platform role and permissions, when present;
- `authorization.agency_memberships`: active memberships and permissions;
- `authorization.portal`: explicit mapping and safe subject projection, when
  present.

Legacy `user`, `memberships`, and `portal` keys remain safe projections for
existing frontend compatibility. Identity status, membership status, and
Portal mapping status are checked server-side on each request, so revocation
takes effect without trusting stale client context.

The frontend has one `AuthorizationProvider`. It loads the current-user
contract, chooses only among memberships returned by the backend, and exposes
useful 401, 403, and unlinked-Portal states. Local storage may retain a selected
Agency ID and bearer token as transport/UI context; neither value grants
authorization. Moving browser token storage to secure cookies remains a
separate security-hardening decision.

## Portal Boundary

Portal authorization is defined in the
[Portal Identity Linkage Contract](portal-identity-linkage-contract.md).
Client and Passenger Portal principals resolve by `auth_identity_id`, never by
matching email. An unlinked Portal identity receives exactly:

> Your portal account is not linked to a profile yet.

## Compatibility And Migration

Pre-contract `PlatformUser` records may temporarily resolve by staff email when
their `identity_id` is absent. That compatibility lookup is limited to staff
resolution and cannot establish Portal access.

`ClientMasterRecord`, `PassengerMasterRecord`,
`ClientPassengerMasterLink`, and `ClientPortalAccessProfile` are deprecated
compatibility writers/projections. `ClientProfile`, `PassengerProfile`,
`ClientPassengerRelationship`, and `PortalAccessMapping` remain canonical.
Compatibility reads are preserved, including historical unlinked records.
Every new Client or Passenger Master record now requires an existing
same-Agency canonical profile, and every new Master relationship requires the
matching canonical relationship. Only one active compatibility projection is
accepted per source. Tenant and source IDs cannot be changed after linkage.
Historical unlinked records may be archived, statused, or annotated for
reconciliation, but cannot accept new identity-shaped data.

`ClientPortalAccessProfile` never authorizes access. New active or invited
legacy Portal metadata requires a same-Agency explicit `PortalAccessMapping`;
unlinked compatibility rows are limited to `no_portal_access` or `archived`.

`backend/scripts/analyze_identity_tenancy_migration.py` is dry-run only. It
reports candidate links, duplicate subjects, active memberships without an
active identity, and active legacy Portal profiles without a valid mapping,
without selecting a subject or writing records. Any future write tool must be
separately reviewed, one Agency at a time, explicitly confirmed, audited,
deterministic, idempotent, and paired with a rollback manifest.

## Known Limitations

- One active Portal mapping per identity and one per subject is currently
  supported. Multiple active contexts require a future explicit selector and
  are rejected for review.
- Historical email-only Portal mappings remain stored for reconciliation but
  confer no access.
- Legacy staff records without `identity_id` still use the bounded staff-only
  compatibility lookup.
- Compatibility Master APIs remain callable as source-bound projection
  adapters. Their duplicated payload fields are not canonical and are not
  written back into `ClientProfile` or `PassengerProfile`.
- Historical unlinked compatibility records still require reviewed,
  dry-run-led reconciliation before they can be retired.
