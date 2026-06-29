# Trip Change, Ticket Exchange, And EMD Exchange Workflows

Phase 36.4.6 adds internal foundations for servicing existing trips without creating unrelated new trips.

## Foundation Records

| Record | Purpose |
|---|---|
| `TripChangeOperation` | Tracks itinerary, booking, ticket, EMD, cancellation, refund quote, or service-change work against an existing trip. |
| `TicketExchangeOperation` | Tracks internal ticket exchange, reissue, void, refund, name correction, or schedule-change reissue mirror work. |
| `EmdExchangeOperation` | Tracks internal EMD exchange, reissue, void, refund, or service-change mirror work. |

## Canonical Flow

1. Open an existing trip dossier.
2. Create a change operation.
3. Optionally create a revised booking workspace/record mirror linked to the same trip.
4. Create ticket or EMD exchange operation records from original mirrors.
5. Mirror revised ticket or EMD records with source context `exchange_reissue`.
6. Preserve links to original ticket/EMD records and operation records.

## Request And Offer Linkage

Phase 36.4.6 adds optional purpose/linkage fields to request and offer foundations:

- `existing_trip_id`
- `trip_change_operation_id`
- `request_purpose`
- `offer_purpose`

These fields prepare future change requests and exchange/refund quote offers without rebuilding offer builder in this phase.

## API Entry Points

- `GET /api/agencies/{agency_id}/trips/{trip_id}/change-operations`
- `POST /api/agencies/{agency_id}/trips/{trip_id}/change-operations`
- `POST /api/agencies/{agency_id}/trip-change-operations/{operation_id}/create-change-booking`
- `POST /api/agencies/{agency_id}/ticket-exchange-operations`
- `POST /api/agencies/{agency_id}/ticket-exchange-operations/{operation_id}/mirror-new-ticket`
- `POST /api/agencies/{agency_id}/emd-exchange-operations`
- `POST /api/agencies/{agency_id}/emd-exchange-operations/{operation_id}/mirror-new-emd`

## Boundaries

Exchange, reissue, refund, void, and cancellation records are internal mirrors only. No airline, GDS, NDC, supplier, BSP/ARC, payment, invoice, accounting, or live ticket/EMD action is executed.
