# Reference Data Wiring and Migration

## Current Wiring

Priority operational writes now resolve canonical references for:

- Request V4 passenger type and nationality.
- Request V4 origin/destination airports, marketing/operating airlines, cabin,
  preferred/excluded airlines, and currency.
- Request V4 pet species, breed, container type, special-item category, and
  declared-value currency.
- Passenger Profile passenger type, nationality, residence country, passport
  country, primary language, and travel-document type.

The public Request V4, Agency Request V4, Passenger create/edit, Passenger
filters, and explicit Request passenger identity confirmation consume shared
reference selectors. Existing compatibility code fields remain populated.

## Legacy Rules

Legacy free text is never silently replaced. If an active unambiguous match
exists, dry-run analysis proposes its stable ID. Unknown values, ambiguous
aliases, missing IDs, wrong-domain links, cross-scope links, inactive links, and
PTC age/DOB contradictions are manual-review cases.

Historical code and label snapshots remain readable. No label update,
deactivation, import, or migration analysis rewrites an accepted offer, prior
request, passenger, booking, ticket, or other operational snapshot.

## Dry-Run Analysis

Run locally or against an explicitly selected environment:

```bash
python3 backend/scripts/analyze_reference_wiring_migration.py
```

The analyzer uses bounded deterministic reads of Passenger Profile, Request
passenger, Request parent, segment, pet, special-item, and global reference
collections. It reports:

- counts by agency and reference domain;
- deterministic candidate mappings;
- ambiguous mappings;
- manual-review cases;
- duplicate active codes/keys;
- global/agency scope conflicts;
- missing, wrong-domain, cross-scope, and inactive IDs;
- code-only countries, airports, airlines, cabins, species, breeds, container
  types, document types, languages, currencies, special-item categories, and
  PTCs;
- PTC age/DOB contradictions.

The command compares collection counts before and after analysis and reports
`writes_performed: 0` and `write_mode_available: false`. `--write` fails
closed.

## Future Write Migration Gate

No write migration exists. A future migration must require explicit
confirmation, exactly one agency and domain, before/after manifests, audit
evidence, a rollback plan, and human resolution of every ambiguous mapping.

## Remaining Wiring Debt

Client address, Offer, Booking, Invoice, and deeper pet/document/policy fields
still contain compatibility values in places. They should adopt the same
selector and snapshot contract only when their existing canonical forms are
touched. This repair does not redesign those workflows or create parallel
models.
