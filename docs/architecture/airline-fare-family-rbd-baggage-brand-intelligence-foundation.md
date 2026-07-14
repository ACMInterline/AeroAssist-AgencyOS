# Airline Fare Family, RBD, Baggage, and Brand Intelligence Foundation

## Purpose

Phase 55.7 creates governed commercial-product intelligence for offer preparation and operational comparison. It describes documented airline fare families, booking classes, baggage allowances, exceptions, and brand attributes. It does not calculate a live fare, infer availability, or execute provider, booking, ticketing, or servicing actions.

## Canonical Model

The existing `airline_fare_families` collection remains canonical and is extended with airline code, brand code, commercial name, hierarchy, channel/route/market scope, effective dates, freshness, publication, agency visibility, evidence links, and client-safe labels. Existing source fields remain intact.

The supporting metadata collections are:

- `airline_fare_brand_attributes`
- `airline_booking_class_mappings`
- `airline_baggage_allowance_rules`
- `airline_baggage_exceptions`
- `airline_commercial_bundles`
- `airline_fare_family_evidence_links`
- `airline_brand_comparison_profiles`

`AirlineFareBrandAttribute` covers seat selection, changeability, refundability, same-day change, priority, lounge, meals, fast track, mileage accrual, no-show conditions, and ancillary inclusion. `AirlineBookingClassMapping` records known, variable, unknown, and non-applicable RBD mappings, including cabin, brand, restrictions, and upgrade/downgrade relationships.

## Baggage Resolution

`AirlineBaggageAllowanceRule` supports piece, weight, hybrid, and unknown concepts; cabin and personal items; checked pieces or weight; infant and child rules; status-member exceptions; special-item inclusion/exclusion; distribution, route, and market scope; and effective dates.

`AirlineBaggageException` applies governed passenger, status, route, market, carrier, special-item, and channel overrides. A multi-carrier context is never treated as certain solely because a fare-brand record exists. Phase 55.6 baggage-responsibility intelligence is consulted and unresolved interline/codeshare cases return warnings and manual review.

## Evidence, Versions, and Offer Use

Fare-brand entities are registered as evidence-governance targets and structured knowledge-version objects. Conflicting or superseded source truth is preserved by those canonical services. Existing `airline_rbd_matrix_rows`, `airline_fare_rules`, and `airline_ancillaries` remain source context rather than being rewritten.

The Intelligent Offer Builder receives only published, agency-visible, client-safe fare-family labels and comparison attributes. Internal notes and restricted evidence references are excluded from agency projections. Missing intelligence remains unknown; the offer builder must not invent product claims.

## Routes and UI

- Platform API: `/api/platform/fare-brand-intelligence`
- Agency API: `/api/agencies/{agency_id}/fare-brand-library`
- Platform UI: `/platform/fare-brand-intelligence`
- Agency UI: `/agency/fare-brand-library`

Platform owners, administrators, and knowledge editors can create and update metadata. Agency views are read-only; comparison, RBD resolution, baggage resolution, and offer projection requests are transient advisory calculations and do not persist or execute an operational action.

## Safety Boundary

Phase 55.7 is intelligence and planning infrastructure. It stores no provider credentials, calls no live shopping source, makes no price commitment, asserts no live availability, and performs no booking, ticketing, EMD, payment, publishing, messaging, AI, or background-worker execution.
