# Canonical Reference Data Contract

## Ownership

`GlobalReferenceRecord` in `global_reference_records` is the canonical owner of
shared operational vocabulary. It is extended by the existing reference-data
service, routers, import governance, Platform console, and audit stream. No
parallel reference collection or selector API is introduced.

`agency_id` remains the authorization tenant boundary. A global record is
Platform-owned. An agency-scoped record is visible only within its agency and
must not silently conflict with a global record or another active record in its
effective scope.

## Domain Inventory

| Specification domain | Stable domain | Classification |
|---|---|---|
| airlines | airlines | already canonical and complete |
| airports | airports | already canonical and complete |
| aircraft_types | aircraft_types | already canonical and complete |
| cabin_classes | cabin_classes | canonical but incomplete |
| fare_bundles | fare_bundles | canonical but incomplete |
| flight_types | flight_types | canonical but incomplete |
| route_types | route_types | canonical but incomplete |
| countries | countries | already canonical and complete |
| cities | cities | already canonical and complete |
| temperature_zones | temperature_zones | canonical but incomplete |
| languages | languages | already canonical and complete |
| currencies | currencies | already canonical and complete |
| client_types | client_types | already canonical and complete |
| contact_channels | contact_channels | already canonical and complete |
| guardian_relationships | guardian_relationships | already canonical and complete |
| passenger_type_codes | passenger_types | represented under a different stable key |
| document_types | document_types | already canonical and complete |
| vaccination_types | vaccination_types | canonical but incomplete |
| species | pet_species | represented under a different stable key |
| breeds | pet_breeds | represented under a different stable key |
| breed_risk_flags | breed_risk_flags | canonical but incomplete |
| container_types | container_types | canonical but incomplete |
| service_codes | service_catalogue | represented by the canonical service catalogue |
| assistance_types | assistance_types | canonical but incomplete |
| condition_types | condition_types | canonical but incomplete |
| special_item_categories | special_item_categories | already canonical and complete |
| policy_statuses | policy_statuses | canonical but incomplete |
| policy_result_statuses | policy_result_statuses | canonical but incomplete |
| seasonal_restriction_types | seasonal_restriction_types | canonical but incomplete |
| pricing_categories | pricing_categories | canonical but incomplete |
| pricing_units | pricing_units | canonical but incomplete |
| pricing_formula_components | formula_components | represented under a different stable key |
| payment_methods | payment_methods | already canonical and complete |
| tax_types | tax_types | already canonical and complete |
| task_types | task_types | canonical but incomplete |
| communication_channels | contact_channels | represented under a different stable key |
| priority_levels | priority_levels | canonical but incomplete |
| statuses | statuses | decision required because status vocabularies are lifecycle-specific |

This inventory is machine-readable as
`canonical_reference_service.REFERENCE_DOMAIN_INVENTORY`. Incomplete means the
domain is registered safely but needs governed population or further consumer
wiring; it does not authorize a duplicate domain.

## Normalized Option

All reusable selectors consume one response shape:

```json
{
  "id": "stable-record-id",
  "value": "stable-record-id",
  "label": "Human label",
  "code": "CODE",
  "key": "CODE",
  "raw": {
    "domain": "domain-key",
    "scope": "global",
    "is_active": true,
    "metadata": {}
  }
}
```

Results are sorted by `sort_order`, label, code, and ID. Active records are the
default. Authenticated historical reads may include inactive records.
Public options are limited to an explicit domain allowlist and allowlisted
metadata fields; persistence internals, reviewer notes, and secrets are never
returned.

## Lifecycle and History

- New selections require an active record in the correct domain and effective
  tenant scope.
- Operational records retain reference ID plus code/key and label snapshots.
- Editing a reference label never rewrites historical operational snapshots.
- Deactivation is soft. There is no destructive delete.
- Active operational usage blocks ordinary deactivation.
- A Platform Owner/Admin may use an explicit forced override only with a reason;
  usage, actor, reason, and counts are audited.
- Reactivation reruns active code/key conflict checks.
- Imports use the same code normalization, PTC metadata validation, duplicate
  checks, and governed lifecycle boundary as manual editing.

## Query and Execution Safety

Reference options cap requests at 200 rows and autocompletes use a bounded
50-row search. Usage scans use the repository maximum query limit and return
that limit in the result. The reference layer performs no provider calls,
policy evaluation, pricing, booking, ticketing, payment, messaging, automatic
migration, or production publication.
