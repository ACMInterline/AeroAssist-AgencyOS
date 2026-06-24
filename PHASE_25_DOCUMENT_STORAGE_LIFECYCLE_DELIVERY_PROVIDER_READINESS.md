# Phase 25 Document Storage Lifecycle And Delivery Provider Readiness

Phase 25 adds a safe operational layer for document/export storage lifecycle and future delivery provider readiness. It does not add automatic email sending, public document links, object storage uploads, external SaaS dependencies, payment gateways, airline integrations, demo auth, or seed endpoint changes.

Current production URL:

```text
https://avio.my
```

The API phase label is:

```text
phase_25_document_storage_lifecycle_delivery_provider_readiness
```

## Storage Lifecycle Model

Document exports are registered into `document_storage_records` as lifecycle metadata. The local filesystem export backend remains the default:

```text
storage_backend=local_filesystem
```

Storage records track:

- agency and optional workspace scope
- related entity type and ID
- document type
- original filename and safe stored filename/key
- storage status: `active`, `archived`, `deleted`, `missing`, or `failed`
- content type, size, checksum, retention date
- creator metadata where known
- delivery and public access guard flags, both false by default

Normal API responses do not expose absolute local filesystem paths.

## Storage Service

`backend/services/document_storage_lifecycle_service.py` registers generated exports, verifies local file existence when practical, marks missing records, archives records without deleting files, and returns storage summaries/health without leaking host paths.

Hard deletion is not exposed by API in Phase 25.

## API Endpoints

Auth is required for all Phase 25 document storage and provider readiness endpoints:

```text
GET /api/documents/storage/summary
GET /api/documents/storage
POST /api/documents/storage/{record_id}/archive
POST /api/documents/storage/{record_id}/mark-missing
GET /api/documents/storage/health
GET /api/documents/delivery-providers
GET /api/documents/delivery-providers/readiness
```

Platform owner/admin/support users can view all storage metadata or filter by `agency_id`. Agency users are scoped to their agency and need agency access. Write actions require agency write permission.

## Delivery Provider Readiness

`backend/services/delivery_provider_service.py` exposes provider readiness without sending anything externally.

Phase 25 provider behavior:

- `manual` is enabled and ready by default.
- `email_smtp` may show configuration readiness but remains disabled for automatic sending.
- `email_api`, `portal`, `object_storage`, and `webhook` are disabled/not configured placeholders.
- No secrets are returned.
- No public links are enabled.
- No object storage upload is performed.

## Frontend

The agency workspace includes:

```text
/agency/document-storage
```

The page shows storage health, lifecycle counts, provider readiness, storage records, archive actions, and mark-missing actions. It states that automatic delivery is disabled, manual delivery is the only active provider, and no public links are enabled.

## Host Storage Check

The Hostinger script checks the backend document export volume:

```bash
deploy/hostinger/scripts/check_storage.sh
```

It verifies that the document export directory exists and is writable, then prints file count and total bytes. It does not print secrets.

## Audit Events

Phase 25 adds audit events for:

- `storage_record_registered`
- `storage_record_archived`
- `storage_record_marked_missing`

Audit metadata uses safe IDs and never includes absolute local paths or secrets.

## Current Limits

- No automatic email sending.
- No public unauthenticated document links.
- No external object storage.
- No hard-delete API.
- No external delivery provider integration.
- No provider webhooks or background workers.

## Next Recommended Phase

Phase 26 should focus on one bounded next operational layer, such as delivery provider operations with explicit admin controls, or Airline Intelligence source/version workflow if provider delivery remains out of scope.
