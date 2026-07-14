# Request-to-Trip Operational Conversion Foundation

Phase 54.5 creates the metadata-only conversion layer from request intake into an operational trip dossier.

The request remains the immutable intake and audit origin. The trip becomes the downstream operational shell used for continuing passenger service operations. A request id must never be reused as a trip id.

## Scope

The foundation registers:

- `request_trip_conversion_plans`
- `request_trip_conversion_runs`
- `request_trip_entity_mappings`
- `request_trip_conversion_issues`

Agency routes live under `/api/agencies/{agency_id}/request-trip-conversion`. Platform diagnostics live under `/api/platform/request-trip-conversion`.

Frontend routes are:

- `/agency/request-trip-conversion`
- `/platform/request-trip-conversion`

## Conversion Behavior

The service supports preview, validation, execution, safe retry, and idempotency metadata. It can create a new trip shell or explicitly attach a request to an existing trip dossier.

Conversion records preserve source snapshots and store mappings for:

- request segment to trip segment
- request passenger to trip passenger
- request passenger to passenger profile
- request service to trip service item
- request scoped service to trip service item
- pet segment scope carry-forward
- special-item segment scope carry-forward
- linked offer carry-forward

Critical structural problems block execution. Incomplete but operationally recoverable data creates warnings or manual-review metadata so staff can proceed only with visibility.

## Integrations

Phase 54.5 records metadata links into:

- trip dossier creation/linking
- operational workflow instance and event metadata
- task automation run metadata
- SLA/deadline metadata
- request and trip timelines

These integrations are advisory and auditable. They do not execute booking, ticketing, provider actions, AI actions, sending, workers, or automation engines.

## Safety Boundaries

Phase 54.5 does not implement:

- booking execution
- ticket issuance
- provider, GDS, NDC, airline, or external API calls
- AI or automatic recommendations
- background workers or schedulers
- automatic production seeding
- destructive reset behavior
- permission model changes
- route blocking

Human authority remains final.
