# Airline Operational Capability Matrix Foundation

Phase 50.5 creates the Airline Operational Capability Matrix foundation.

This phase is metadata-only. It records what airlines can operationally deliver under stated conditions. It does not evaluate passenger cases, score feasibility, rank airlines, reason with AI, execute parsers, calculate pricing, call providers, run background workers, scrape, publish automatically, or automate decisions.

## Purpose

The Capability Matrix answers:

`What can this airline operationally deliver?`

It does not answer:

`Is this passenger case feasible?`

Passenger feasibility belongs to Phase 50.7. Phase 50.5 only creates the operational inventory that Phase 50.6 evaluation and Phase 50.7 feasibility can consume.

## Capability Is Not Policy

Capability is different from Policy.

Policy says whether an airline may allow a service.

Capability records whether the airline can actually deliver the service under specific operational conditions, such as aircraft, cabin, airport, route, season, country, interline/codeshare context, handling restrictions, equipment, and confidence level.

Pricing is also separate from Capability. A service may be operationally deliverable while pricing remains unknown or manually quoted.

## Data Foundation

Phase 50.5 adds:

- `AirlineCapabilityMatrixRecord`
- `AirlineCapabilityMatrixCreate`
- `AirlineCapabilityMatrixUpdate`
- `airline_capability_matrix`
- `AirlineCapabilityMatrixService`
- `/api/platform/airline-capability-matrix`
- `/api/agencies/{agency_id}/airline-capability-matrix`
- `/platform/airline-capability-matrix`
- `/agency/capability-matrix`

Platform APIs may create, update, soft-archive, list, and read matrix metadata.

Agency APIs are read-only.

## Knowledge Inputs

The matrix consumes governed airline operational knowledge from:

- Phase 50.1 Airline Knowledge Acquisition
- Phase 50.2 Operational Constraint Engine
- Phase 50.3 Airline Operational Knowledge Normalisation
- Phase 50.4 Airline Operational Knowledge Governance & Version Control

Records keep references to knowledge versions, knowledge releases, acquisition records, normalisation records, operational constraints, and evidence references.

## Operational Dimensions

Matrix records can describe capability by:

- Airline, validating carrier, operating carrier, and marketing carrier
- Service domain, family, variant, passenger need category, SSR, OSI relevance, RFIC, RFISC, EMD relevance, and document relevance
- Aircraft family, subtype, configuration, cabin, seat properties, armrests, bulkhead/exit restrictions, under-seat space, accessible lavatory, and onboard wheelchair capability
- Airport, station, origin, destination, transit, ground handling, airport handling requirements, and station notification requirements
- Route, origin/destination/transit country, season, date range, event-based applicability, embargoes, and weather or temperature relevance
- Interline/codeshare context and carrier-control requirements
- Animal transport capability, including PETC, AVIH, species, breed, brachycephalic handling, carrier dimensions/weight, under-seat transport, and adjacent extra-seat handling
- Extra seat / EXST capability, including passenger of size, comfort extra seat, CBBG, musical instrument, medical extra seat, adjacent seat, cabin restrictions, and refund notes
- Medical and accessibility capability, including WCHR, WCHS, WCHC, MEDIF, oxygen, stretcher, medical equipment, and reduced mobility notes
- Operational requirements, including approvals, documents, EMD, SSR, OSI, MEDIF, advance notice, crew notification, procedures, and manual review
- Risk and confidence metadata
- Lifecycle metadata, supersession metadata, and archive metadata

## Future Consumers

Phase 50.6 consumes the matrix for metadata-only Operational Knowledge Evaluation records.

Phase 50.7 consumes Operational Evaluation Results for advisory, non-Boolean passenger service feasibility.

Neither future relationship changes Phase 50.5 into an execution engine. The matrix remains an operational inventory.

## Explicit Exclusions

Phase 50.5 does not implement live rule evaluation, passenger feasibility scoring, airline recommendation ranking, AI reasoning, parser execution, pricing calculation, provider integrations, background workers, automatic publication, scraping, external API calls, booking, ticketing, EMD issuance, payment, messaging, or automation.
