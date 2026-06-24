# Phase 24 Staff Invitation Acceptance And Team Access Hardening

Phase 24 completes a safe, auditable staff invitation acceptance path for AeroAssist AgencyOS without enabling public registration, demo auth, automatic email sending, external email services, role escalation, or public team signup.

Current production URL:

```text
https://avio.my
```

The API phase label is:

```text
phase_24_staff_invitation_acceptance_team_access_hardening
```

## Invitation Lifecycle

Staff invitations move through these states:

- `pending`: created by a platform owner/admin, agency owner, or permitted agency admin.
- `accepted`: token was accepted and an active staff membership was created or activated.
- `expired`: pending token passed its expiry window.
- `revoked`: pending invitation was revoked by an authorized operator.

Raw invitation tokens are generated with cryptographic randomness and stored only as `token_hash`. The raw token and acceptance URL are returned once in the create response so the operator can manually deliver the link. List, validate, revoke, accept, audit, and normal API responses do not expose `token_hash`.

## Who Can Invite

- Platform owners/admins can invite safe staff roles into an agency.
- Agency owners can invite safe staff roles into their agency.
- Agency admins can invite lower operational roles only.

The invitation flow cannot create `platform_owner` or `agency_owner` roles.

Allowed staff invitation roles are:

```text
agency_admin
agency_agent
agency_accountant
agency_readonly
```

Agency admins are limited to:

```text
agency_agent
agency_accountant
agency_readonly
```

## Token Validation And Acceptance

`GET /api/auth/invitations/validate?token=...` returns minimal invitation metadata for a valid pending token:

- agency name and slug
- workspace name when scoped
- invited email
- invited display name
- target role
- expiry and status

Invalid, expired, revoked, and accepted tokens do not reveal sensitive details.

`POST /api/auth/invitations/accept` accepts a valid pending token for the invited email only. For new invited staff, the request sets a password, creates an auth identity for the invited email, creates or activates exactly one agency staff membership, marks the invitation accepted, and creates a session.

If an active account already exists for the invited email, the user must be authenticated as that same email before accepting. The invitation flow does not silently reset an active account password.

## Membership Behavior

Membership creation is guarded by agency and user identity:

- only the invitation agency is used
- optional `workspace_id` must belong to the same agency
- membership is unique by agency and user
- accepted memberships are marked `active`
- the invitation role is applied
- `created_from_invitation_id`, `identity_id`, email, normalized email, and join timestamp are recorded
- accepting the same token twice fails because the invitation is no longer pending

## Audit Events

Phase 24 records audit events for:

- `invitation_created`
- `invitation_revoked`
- `invitation_accepted`
- `membership_created_from_invitation`

Audit metadata includes safe role/workspace/invitation identifiers only. Raw tokens and token hashes are never written to audit events.

## Frontend

The platform agency detail page now includes:

- staff invitations list
- invitation creation form with email, invited name, role, and workspace selection
- one-time acceptance link copy box
- pending invitation revoke action

The public acceptance page is:

```text
/invite/accept?token=...
```

It validates the token, shows minimal agency/workspace/email/role details, and activates the account with password setup when the token is accepted.

## Current Limits

- No automatic email sending.
- No public registration.
- No mass team management.
- No membership removal flow.
- No platform owner invitation flow.
- No external email/SaaS dependency.
