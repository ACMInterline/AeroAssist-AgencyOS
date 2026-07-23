# P0 Security, Identity Integrity, and Product Kernel Freeze

This is a corrective architecture gate, not a new product phase. It applies while the current Product Experience Recovery work is reviewed.

## Immediate Integrity Boundaries

### Audit access

- Platform-wide audit review belongs only to Platform Owner and Platform Admin.
- Agency audit review is tenant-scoped and belongs only to Agency Owner and Agency Admin.
- Portal users, anonymous callers, Platform Support, other Agency roles, and cross-agency callers cannot read those records.
- Audit responses are bounded and recursively redact protected metadata without mutating stored audit truth.

### Passenger identity

`PassengerProfile` is a canonical reusable identity. It must represent a real traveler whose identity has been explicitly confirmed.

`RequestPassenger` owns unconfirmed traveler information. Public intake and request creation may capture a proposed name, passenger type, birth date, and operational needs, but those values remain a request snapshot with:

- no `passenger_id`;
- `passenger_link_mode=unresolved`;
- `identity_status=unresolved`; and
- no invented birth date, name, relationship, or passenger profile.

An Agency Owner, Agency Admin, or Agency Agent must use the request passenger identity-confirmation action to select an existing active profile or create a fully identified profile. New-profile confirmation requires first name, last name, date of birth, and a human-entered reason. Offer creation from a request remains blocked while any active request passenger is unresolved.

The canonical confirmation route is:

`POST /api/agencies/{agency_id}/requests/{request_id}/passengers/{request_passenger_id}/confirm-identity`

The action is tenant-scoped, role-guarded, audited, recorded on the request timeline, duplicate-aware, and idempotent when retried against the already confirmed profile.

## Legacy Intake Placeholder Quarantine

Older intake conversion could create synthetic profiles named `Passenger N Details pending` with date of birth `1900-01-01`. The corrective utility uses a strict provenance signature: the exact generated name pattern, exact placeholder note, sentinel date, and a linked request carrying `source_intake_id`. A birth date alone is never enough to classify a profile.

The utility is read-only by default:

```bash
python3 backend/scripts/quarantine_legacy_intake_placeholder_passengers.py --agency-id AGENCY_ID
```

An operator must review the dry-run output before explicitly applying it:

```bash
python3 backend/scripts/quarantine_legacy_intake_placeholder_passengers.py \
  --agency-id AGENCY_ID \
  --apply \
  --confirmation QUARANTINE_LEGACY_INTAKE_PLACEHOLDERS \
  --actor-user-id OPERATOR_USER_ID
```

Apply mode never deletes a record. It:

- marks the synthetic profile `quarantined`;
- preserves its source and audit history;
- archives the synthetic client-passenger relationship;
- returns linked request passengers to unresolved state;
- removes the synthetic profile ID from request-level service applicability; and
- requires normal explicit identity confirmation before downstream offer work.

The utility does not run during application startup, deployment, or database initialization.

## Feature Expansion Freeze

New metadata foundations and new top-level product surfaces are frozen until all of the following are approved:

1. One canonical product-kernel ownership map identifies the single write owner for Client, Passenger, Request, Trip, Offer, Accepted Offer, Booking, Ticket, EMD, Passenger Service, Document, Finance, After Sales, Task, Workflow, Timeline, and Audit state.
2. Transitional and legacy-compatible models have explicit read, write, migration, and retirement rules.
3. The Agency UI presents the canonical golden path without requiring users to choose among overlapping foundations.
4. Platform and Agency navigation retain only actor-relevant primary workspaces, with diagnostics and specialist tools kept contextual or under Advanced.
5. Security, tenant isolation, immutable snapshots, audit evidence, and execution-disabled boundaries remain proven by regression coverage.

Allowed work during the freeze is limited to security fixes, data-integrity corrections, canonical consolidation, pilot-blocking defect repair, tests, documentation, and simplification of existing UI. This gate must not be treated as permission to create another workflow, master-record, readiness, dashboard, or metadata subsystem.
