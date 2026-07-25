# Passenger Type Code Reference Contract

## Canonical Model

Passenger Type Codes (PTCs) are `GlobalReferenceRecord` rows in the stable
`passenger_types` domain. `passenger_type_codes` is an API/specification alias,
not another collection.

The canonical seed metadata contains:

| Code | Label | Category | Configured age | Review behavior |
|---|---|---|---|---|
| ADT | Adult | adult | 12-130 | DOB optional |
| CHD | Child | child | 2-11 | DOB required |
| INF | Infant | infant | 0-1 | DOB and guardian review |
| YTH | Youth | youth | 12-17 | DOB and policy review |
| SRC | Senior | senior | 65-130 | DOB and policy review |
| STU | Student | student | unspecified | documentation/policy review |
| SEA | Seaman | seaman | unspecified | documentation/policy review |
| MIL | Military | military | unspecified | documentation/policy review |
| GRP | Group Passenger | group | unspecified | airline/fare-rule review |

`UMNR` remains a passenger service. `INS` is not seeded as a canonical PTC.

The canonical `ADT`, `CHD`, and `INF` records retain `adult`, `child`, and
`infant` as read/resolve aliases. These aliases preserve legacy writers while
new selectors and snapshots use the canonical IATA code. If legacy and rich
canonical records coexist before a governed migration, resolution and option
projection prefer the rich canonical record without rewriting either record.

## Metadata

Each PTC supports `workspace_id` and `agency_id` compatibility scope plus:
`code`, `key`, `label`, `description`, `iata_ptc_code`,
`passenger_category`, configured minimum/maximum age,
`requires_date_of_birth`, `requires_guardian`, category flags, applicability
flags, sort order, active state, and additional governed metadata.

The validator rejects contradictory age ranges, invalid categories, out-of-range
ages, mismatched category flags, and lower-case canonical PTC codes. It does not
encode universal airline fare eligibility. Airline-specific pricing and
acceptance remain Policy Engine responsibilities.

## Operational Snapshots

`PassengerProfile` and `RequestPassenger` retain:

- `passenger_type_code_id`
- `passenger_type_code`
- `passenger_type_label`
- a reconciliation status

New writes resolve a same-domain, active, visible reference. Existing code-only
records remain readable and are marked for reconciliation. Inactive linked
records remain available to authenticated historical views. Updating a PTC
record does not relabel prior passengers or requests.

The legacy Operational Request Builder is the documented compatibility path:
old `unaccompanied_minor` input remains an unresolved `UMNR` snapshot and is
flagged for reconciliation while the corresponding operational requirement
continues through the UMNR service. The canonical Request V4 API does not accept
UMNR as a new PTC selection.

## Age Validation

Backend validation uses PTC metadata. Request V4 calculates age on the first
itinerary segment departure date. Passenger Profile validation uses its
effective profile validation date because a profile has no itinerary owner.
Missing DOB, configured age violations, contradictory metadata, guardian review,
and manual policy review are returned as explicit errors or warnings. PTC
validation classifies passenger data; it does not decide airline feasibility.

## Governance

Platform manual creation and import both normalize codes and reject active
code/key conflicts. Status changes use governed deactivate/reactivate actions.
Historical snapshots are immutable, and reconciliation analysis is dry-run
only.
