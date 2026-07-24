# Canonical Operational Timeline

## Decision

`OperationalTimeline` in `operational_timelines` is the sole canonical
operational-history record. `OperationalCollaborationService` owns new
timeline writes. Entity-specific timeline collections remain immutable
compatibility history until a separately reviewed migration is approved.

This corrective kernel repair does not change the active Phase 59.0 marker and
does not migrate production data.

## Entry Contract

Each entry carries:

- immutable `id`, `agency_id`, `event_time`, `created_at`, and `ordering_key`;
- primary `entity_type` and `entity_id`;
- optional parent and Request, Offer, Trip, Booking, Ticket, EMD, Document, and
  finance links;
- canonical `event_type` plus optional source-specific `event_subtype`;
- actor type, identity reference, and display label;
- one explicit visibility;
- summary and structured details;
- optional Communication Thread, Communication Message, Attachment, and Audit
  links;
- source collection/record lineage and optional idempotency key.

The timeline records business evidence. It is not a task queue, notification
store, audit replacement, or communication body store.

## Append-Only Rules

1. The server assigns `event_time` and `created_at`.
2. An idempotency key produces one deterministic entry ID within an Agency.
3. Ordering is `event_time`, then `created_at`, then `id`.
4. Existing entries are never silently edited or deleted.
5. A correction appends `timeline_correction` and links
   `supersedes_entry_id`.
6. Archival appends `timeline_superseded`; it does not remove the original.
7. Audit evidence remains independent and is linked by ID where a mutation or
   human action needs security evidence.
8. Notification projections may be rebuilt without changing timeline rows.

## Tenant And Portal Boundary

Every Agency entry has immutable `agency_id`. Agency reads require active
same-Agency membership. Platform governance is protected by existing Platform
roles. Portal users receive only entries reached through an active
`PortalAccessMapping`, a permitted linked business entity, thread
participation, and matching `client` or `passenger` visibility.

`internal`, `agency`, `supplier`, `platform`, and `system` entries never appear
in a Portal response.

## Compatibility

The following collections are historical compatibility sources:

- `request_timeline_events`
- `offer_timeline_events`
- `trip_timeline_events`
- `booking_timeline_events`
- `ticket_emd_timeline_events`
- `document_timeline_events`
- `refund_exchange_timeline_events`

Compatibility APIs may project these records beside canonical entries. They
must retain source IDs and timestamps and must not manufacture ordering or
rewrite historical records.

The bounded analyzer
`backend/scripts/analyze_operational_collaboration_migration.py` is permanently
dry-run. It reports duplicate candidates, orphans, missing links, and legacy
note fields. It has no write mode.

## Safety Boundary

Appending history does not send email, SMS, chat, supplier, airline, or Portal
messages. It does not execute bookings, tickets, EMDs, payments, refunds,
exchanges, provider calls, background delivery, or notifications.
