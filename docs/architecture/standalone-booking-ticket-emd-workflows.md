# Standalone Booking, Ticket, And EMD Workflows

Phase 36.4.6 recognizes that the request-to-offer path is correct but not exclusive. A real agency also needs standalone manual records, imported confirmations, and existing-trip servicing.

## Valid Internal Workflows

| Workflow | Canonical path | Foundation |
|---|---|---|
| Planned new trip | Request/trip -> offer workspace -> accepted offer -> booking readiness -> booking workspace -> booking record -> ticket/EMD mirrors | Built across Phase 36.1-36.4 |
| Standalone manual | Client/passenger context -> manual booking workspace -> manual booking record -> manual ticket/EMD mirrors | Phase 36.4.6 |
| Imported confirmation | Raw GDS/confirmation text -> booking import draft -> parse preview -> reviewed import -> booking/ticket/EMD mirrors | Phase 36.4.6 |
| Existing trip change | Existing trip -> change operation -> revised booking mirror -> ticket/EMD exchange/reissue mirrors | Phase 36.4.6 |

## Source Context

Booking workspaces and booking records carry `source_context` values:

- `offer_readiness`
- `standalone_manual`
- `imported_gds`
- `imported_confirmation`
- `existing_trip_change`

Ticket and EMD mirrors carry compatible source contexts, including `exchange_reissue`.

## API Entry Points

- `POST /api/agencies/{agency_id}/booking-workspaces/manual`
- `POST /api/agencies/{agency_id}/tickets/manual`
- `POST /api/agencies/{agency_id}/emds/manual`
- `POST /api/agencies/{agency_id}/booking-workspaces/from-readiness`

## UI Entry Points

- `/agency/booking-workspaces`
- `/agency/booking-imports`
- `/agency/tickets-emds`
- `/agency/trips/{trip_id}`

Manual booking, ticket, and EMD creation use structured agent-facing sections as the primary UX. Agents enter passengers, flight segments, pricing, SSR/OSI, services, ticket coupons, and EMD coupon/service data through normal fields; the frontend derives the existing backend snapshot payloads from those fields.

Raw snapshot JSON remains available only as a collapsed advanced fallback for debugging, migration, or exceptional support cases. A raw override must parse as valid JSON before the form submits.

## Boundaries

All records are internal mirrors. No live booking, ticketing, EMD issuance, exchange, refund, void, payment, invoice, accounting, GDS, NDC, or supplier action is executed.
