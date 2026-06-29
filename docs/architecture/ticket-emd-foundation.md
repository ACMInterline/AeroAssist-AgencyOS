# Ticket and EMD Foundation

Phase 36.4 adds internal ticket and EMD mirror records after booking readiness and manual PNR mirroring. The forward-only handoff is:

`Request/Trip -> Offer Workspace -> Accepted Offer -> Booking Readiness Package -> Booking Workspace -> Booking Record -> Ticket Records -> EMD Records`

## Implemented Records

- `TicketRecord` is extended as a booking-record-linked internal ticket mirror while retaining compatibility with legacy booking tracking.
- `TicketCoupon` stores passenger and segment coupon status for a ticket mirror.
- `EMDRecord` is extended as a booking-service-linked internal EMD mirror while retaining compatibility with legacy EMD tracking.
- `EmdCoupon` stores service, segment, and optional ticket-coupon linkage for an EMD mirror.
- `TicketEmdTimelineEvent` records draft creation and manual mirror updates for ticket and EMD records.

## Snapshot Rules

Ticket and EMD mirrors copy booking-record and booking-workspace context forward:

- booking workspace and booking record identifiers
- trip and request identifiers
- passenger snapshots
- segment summaries
- pricing snapshots
- provider payload and response placeholders
- fare and rule references
- service catalogue identifiers, service keys, categories, labels, RFIC/RFISC codes, and EMD applicability
- linked booking service snapshots
- warnings and readiness diagnostics

Booking readiness packages, accepted offer snapshots, original requests, and booking records are not mutated backward by ticket or EMD mirror actions.

## API Surface

Agency endpoints:

- `GET /api/agencies/{agency_id}/tickets`
- `POST /api/agencies/{agency_id}/tickets/from-booking-record`
- `GET /api/agencies/{agency_id}/tickets/{ticket_record_id}`
- `PUT /api/agencies/{agency_id}/tickets/{ticket_record_id}`
- `GET /api/agencies/{agency_id}/emds`
- `POST /api/agencies/{agency_id}/emds/from-booking-service`
- `GET /api/agencies/{agency_id}/emds/{emd_record_id}`
- `PUT /api/agencies/{agency_id}/emds/{emd_record_id}`
- `GET /api/agencies/{agency_id}/booking-records/{booking_record_id}/ticket-emd-readiness`

## UI Surface

- `/agency/tickets-emds` lists ticket and EMD mirrors with operational filters.
- `/agency/tickets/{ticket_record_id}` shows ticket mirror details, coupons, linked EMDs, warnings, and timeline.
- `/agency/emds/{emd_record_id}` shows EMD mirror details, service mapping, linked ticket, coupons, warnings, and timeline.
- Booking workspace and trip detail pages show ticket/EMD readiness, linked mirrors, and disabled issue actions.

## Boundaries

Phase 36.4 does not perform live ticket issuance, live EMD issuance, GDS/NDC/supplier calls, BSP/ARC settlement, payment capture, invoice/accounting posting, or provider import reconciliation.

Readiness exposes the non-blocking `ticket_emd_foundation` section. The foundation is optional for deployment readiness, and both `provider_ticketing_disabled` and `provider_emd_issuance_disabled` must remain true.
