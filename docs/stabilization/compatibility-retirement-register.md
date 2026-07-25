# Compatibility Retirement Register

**Status:** compatibility paths are retained and quarantined; no broad deletion
was authorized.

| Compatibility family | Purpose/current consumers | Allowed operations | Forbidden operations | Canonical owner | Removal evidence required |
|---|---|---|---|---|---|
| `TravelRequestWorkspace` | Historical workspace metadata and old deep links | deterministic reads; reviewed adapter behavior | independent Request truth | `TravelRequest` aggregate | complete record reconciliation and no route/UI consumer |
| legacy Request builder/intake | Historical intake and old clients | provenance, explicit conversion, bounded reads | direct V4 child mutation | `TravelRequest` | migrated callers and dry-run report with no unresolved records |
| `offers`, `offer_workspaces_v2` | Historical Offer rendering | reads and governed compatibility projection | overwrite linked canonical Offer | `OfferWorkspace` / `OfferOption` | all accepted/commercial lineage reconciled |
| `trip_workspaces` | Historical operational metadata | reads and explicit linkage | confirmed Trip truth without accepted evidence | `TripDossier` | lineage reconciliation and zero consumers |
| `bookings`, Booking Workspace metadata | Historical/import context and preparation | reads, preparation, evidenced adapter | false booked state or provider result without evidence | `BookingRecord` | historical PNR/result reconciliation |
| Ticket/EMD workspaces | Rich historical mirror metadata | reads and reviewed canonical mirror updates | issuance, refund, exchange, void execution | `TicketRecord` / `EMDRecord` | record/coupon/financial reconciliation |
| `request_tasks` and entity task stores | Historical task views | read/projection input | new parallel actionable work | `OperationalWorkItem` | every active task mapped and callers migrated |
| legacy communication/timelines | Historical rendering | read-only compatibility history | new conversation or history truth | `CommunicationThread`, `CommunicationMessage`, `OperationalTimeline` | visibility and ordering reconciliation |
| legacy Client/Passenger masters | Existing compatibility reads | source-bound projection | independent person truth | `ClientProfile` / `PassengerProfile` | reviewed identity migration |

## Quarantined Page Modules

Seven page modules remain intentionally unrouted/orphaned:
`AgencyDashboardPage`, `BookingCreatePage`, `ClientsPage`, `OfferDetailPage`,
`OffersPage`, `PassengersPage`, and `PortalOffersPage`.

They are excluded from primary navigation. Source removal requires proof that
there is no import, route, historical rendering requirement, smoke dependency,
or migration dependency.

## Governance

**Evidence:** canonical ownership, migration, route, Product Page Inventory,
Golden Path, and compatibility regressions. Product Recovery 11B changes no
canonical owner and deletes no collection or historical record.
