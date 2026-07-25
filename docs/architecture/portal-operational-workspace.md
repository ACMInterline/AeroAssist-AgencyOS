# Portal Operational Workspace

## Projection Architecture

`PortalProjectionService` composes bounded customer-safe views from canonical
records. It introduces no Portal-specific collection and performs no provider
operation.

```text
AuthIdentity
  -> active PortalAccessMapping
  -> ClientProfile or PassengerProfile
  -> tenant- and subject-scoped canonical IDs
  -> customer-safe projections and governed actions
```

Canonical sources are:

- Request V4 and its deterministic children;
- Offer Workspace, delivery version, acceptance, and accepted snapshot;
- Trip Dossier and Trip children;
- Booking Record, Ticket Record, EMD Record, and coupons;
- Document Workspace and immutable storage/export versions;
- Commercial Ledger records;
- Operational Collaboration, Timeline, and Notification projections.

## Routes

Canonical Portal workspace routes include:

- `/api/portal/workspace/dashboard`;
- `/api/portal/trips` and `/api/portal/trips/{id}`;
- `/api/portal/booking-records` and detail;
- `/api/portal/tickets` and detail;
- `/api/portal/emds` and detail;
- `/api/portal/document-center` and detail/download/requested upload;
- `/api/portal/communications` and detail/reply;
- `/api/portal/timeline`;
- `/api/portal/notifications`;
- `/api/portal/finance`;
- `/api/portal/approvals`;
- `/api/portal/profile`;
- governed Request V4 update/cancel routes.

The UI uses `/portal/travel-options`, `/portal/trips`, `/portal/bookings`,
`/portal/tickets`, `/portal/emds`, `/portal/documents`, `/portal/communications`,
`/portal/timeline`, `/portal/actions`, and subject-specific
profile/finance/assistance routes.

## Documents

Document download resolves a same-Agency immutable storage or generated export
record and verifies its checksum. Upload creates a new immutable
`DocumentStorageRecord`, updates only the Document Workspace receipt summary,
and records Audit and Timeline evidence. It never overwrites a prior file,
publishes a public link, or triggers delivery.

## Migration

`backend/scripts/analyze_portal_completion_migration.py` identifies legacy
email mappings, missing identity/subject links, duplicate active mappings, and
historical compatibility counts. It compares collection counts before and
after, reports zero writes, and permanently rejects `--write`.
