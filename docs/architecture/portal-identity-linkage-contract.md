# Portal Identity Linkage Contract

## Decision

Client and Passenger Portal access use the same canonical identity pattern:

`AuthIdentity -> PortalAccessMapping -> ClientProfile | PassengerProfile`

`AuthIdentity` owns authentication, `PortalAccessMapping` owns authorization
linkage, and the linked Client or Passenger profile owns business truth. There
is no `PassengerPortalUser` model and no email-based authorization fallback.

## Mapping Shape

An explicit `PortalAccessMapping` records:

- `id`, `agency_id`, and `auth_identity_id`;
- `subject_type` (`client` or `passenger`);
- exactly one of `client_profile_id` or `passenger_profile_id`;
- active/revoked status;
- created and updated timestamps/actors;
- optional revocation and replacement metadata;
- additive active-identity and active-subject keys;
- a non-authoritative identity-email snapshot for operator review.

Historical `client_id`, `user_email`, and `portal_status` fields remain only
for storage/index/read compatibility. They do not authorize access.

## Invariants

1. The identity must exist, be active, and have the matching Portal identity
   type.
2. The Client or Passenger must exist and be active in the mapping Agency.
3. Exactly one subject is linked.
4. A subject cannot have two active mappings.
5. An identity cannot have two active mappings until a safe context selector
   is explicitly supported.
6. Subject, identity, and Agency links are immutable. A different link requires
   revoke then create.
7. Email equality is never an authorization decision.
8. Ambiguous or cross-agency candidates require operator review.

MongoDB registration adds partial string-only uniqueness for the active
identity key and the `(agency_id, active_subject_key)` pair, plus agency-first
identity, subject, and status lookup indexes. Historical missing or null
compatibility fields are excluded. Existing indexes are not dropped or mutated
automatically.

## Lifecycle

1. An authorized Agency Owner/Admin invites a known Client or Passenger.
2. Invitation acceptance creates or resolves the `AuthIdentity`.
3. Acceptance creates the explicit mapping after all tenant and subject checks.
4. Portal requests resolve the active mapping by `auth_identity_id`.
5. Revocation marks the mapping revoked, records actor/time/reason, writes an
   audit event, and releases active uniqueness keys through a tombstone.
6. A replacement can then be created through the same management API with
   `replaces_mapping_id`. The predecessor must be revoked, belong to the same
   Agency, have no prior replacement, and retain either the reviewed identity
   or subject. Its `replacement_mapping_id` then points to the new record.

There is no production auto-linking. Email may appear only in dry-run
suggestions or operator-assisted discovery.

One compatibility exception preserves already-issued Client Portal
invitations: when an authenticated identity accepts the exact pending
invitation for an exact Agency and Client, one matching legacy `invited`
mapping is upgraded in place. The invitation target and authenticated identity
authorize that transition; the email comparison only identifies the preserved
compatibility row. Multiple candidates fail closed for operator review.

## Access Rules

Client Portal:

- may read only the explicitly linked `ClientProfile` scope and its authorized
  related projections;
- may view linked passengers only through canonical same-Agency relationships;
- cannot access Agency staff or Platform routes.

Passenger Portal:

- may read its explicitly linked `PassengerProfile`, Portal dashboard, and
  profile projection;
- does not inherit the linked Client's wider records;
- cannot access Agency staff or Platform routes.

An inactive identity, revoked mapping, missing mapping, missing subject,
cross-tenant subject, or multiple active mappings denies access. The stable
unlinked message is:

> Your portal account is not linked to a profile yet.

## Management API

Agency Owner/Admin management uses:

- `GET /api/agencies/{agency_id}/portal-access-mappings`
- `POST /api/agencies/{agency_id}/portal-access-mappings`
- `GET /api/agencies/{agency_id}/portal-access-mappings/{mapping_id}`
- `POST /api/agencies/{agency_id}/portal-access-mappings/{mapping_id}/revoke`

All routes require an active membership for the route Agency plus
`manage_agency_users`. Safe responses omit credentials and internal identity
secrets.

## Frontend Contract

`AuthorizationProvider` consumes one current-user payload and never grants
access from a hidden or visible navigation item. Client and Passenger Portal
layouts cannot render Platform or Agency navigation. Passenger Portal exposes
only the Dashboard, Profile, and self Passenger surfaces currently supported.
Deep links continue to pass through the backend authorization boundary.

## Compatibility And Reconciliation

`ClientPortalAccessProfile` and email-only `PortalAccessMapping` records are
deprecated compatibility data. They remain readable for history but cannot
establish access. The dry-run identity migration analyzer reports:

- email-link suggestions without applying them;
- duplicate or ambiguous candidates;
- duplicate active subject mappings;
- cross-Agency email collisions;
- active links to missing or inactive identities;
- active staff memberships without an active linked identity;
- active legacy Portal profiles without a valid explicit mapping;
- Client/Passenger Master overlaps and relationship conflicts.

Future reconciliation must never silently choose a Client or Passenger,
delete conflicting evidence, or move records between Agencies.
