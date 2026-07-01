# Canonical Route Policy

AgencyOS keeps the current route model. The supplementary `/agent/*` and `/admin/*` route roots are intentionally not adopted.

## Canonical Routes

| Route root | Purpose |
|---|---|
| `/platform/*` | Platform owner and global governance/configuration UI |
| `/agency/*` | Agency operational workspace UI |
| `/api/platform/*` | Platform owner governance APIs |
| `/api/agencies/{agency_id}/*` | Agency operational APIs |
| `/api/reference/*` | Shared consume APIs |

## Rejected Roots

| Supplementary root | Decision | Reason |
|---|---|---|
| `/agent/*` | intentionally rejected | Duplicates `/agency/*` and would split agency workflow navigation. |
| `/admin/*` | intentionally rejected | Duplicates `/platform/*` and would blur platform governance boundaries. |

No redirects or aliases are added in Phase 36.4.5, Phase 36.4.6, Phase 36.5, Phase 36.6, or Phase 36.7. Documentation and API/UI mapping are preferred so future work remains explicit.

## Route Mapping

| Supplementary route | AgencyOS route |
|---|---|
| `/agent/clients` | `/agency/clients` |
| `/agent/trip-requests` | `/agency/requests` and `/agency/trips` |
| `/agent/parser` | `/agency/gds-parser` |
| `/agent/parser/imports` | `/agency/booking-imports` and `/agency/gds-parser` |
| `/admin/parser` | `/platform/gds-parser` |
| `/admin/exception-rules` | `/platform/rules-services` |
| `/admin/special-services` | `/platform/rules-services` |
| `/documents` | `/agency/documents` and `/platform/document-templates` |
| `/tickets` | `/agency/tickets-emds` |
| `/bookings` | `/agency/booking-workspaces` |
| `/changes` or `/exchanges` | `/agency/trips/{trip_id}` changes panel and `/agency/tickets-emds` exchange actions |

## Boundary

This policy does not redesign the app shell, introduce new route roots, or change existing tenant authorization. It records that `/platform` and `/agency` are the canonical user-facing roots for AeroAssist AgencyOS.
