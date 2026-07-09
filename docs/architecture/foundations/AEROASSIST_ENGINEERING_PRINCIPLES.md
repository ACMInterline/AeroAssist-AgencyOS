# AeroAssist Engineering Principles

These principles guide future AeroAssist implementation. They are architectural constraints, not suggestions.

## Rules

- Never duplicate operational models.
- Prefer canonical taxonomy over free text.
- Passenger Need is always the root object.
- Capability is not Policy.
- Pricing is not Capability.
- The Capability Matrix records operational inventory; it does not evaluate passenger feasibility.
- Operational Evaluation Results determine what applies; they do not decide feasibility.
- Passenger Service Feasibility is non-Boolean advisory metadata; it is not recommendation.
- Airline Recommendation is advisory preference metadata; it is not booking, search, price generation, or final authority.
- Offer Intelligence Packages consume approved intelligence; they do not invent recommendations, feasibility, evidence, bookings, prices, or client messages.
- Operational Intelligence Cases consolidate the Chapter 50 pipeline; they do not add new intelligence, execute bookings, issue tickets or EMDs, call providers, generate AI output, or send client messages.
- Service Parameter Taxonomies define measurable reusable fields; they do not evaluate rules, calculate prices, execute recommendations, or merge Policy, Pricing, Capability, Constraints, and Procedures.
- Request Segment Service Scopes preserve segment-first passenger + segment + service intake metadata; they do not evaluate policy, calculate pricing, convert trips automatically, search, book, ticket, issue EMDs, call providers, generate AI output, or send client messages.
- Reference Data Domains provide governed values, aliases, normalization rules, and validation rules; they do not call providers, generate AI, evaluate live rules, calculate prices, run workers, or restore old `/admin` routes.
- Operational Rule Composer records define no-code compound rule metadata; they do not execute rules, evaluate live cases, calculate prices, call providers, run AI, launch workers, make automatic decisions, or replace human authority.
- Evidence is required for operational recommendations.
- Chapter 50 remains advisory, not executory.
- New services must fit the five-pillar knowledge model.
- Operational constraints should be represented generically where possible.
- Do not introduce `/admin/*` or `/agent/*` route roots.
- Do not introduce parallel RBAC or parallel trip/request/offer/booking/ticket/EMD models.
- Do not migrate architecture to Supabase, Next.js, or Horizons.

## Model Discipline

Future features must extend the existing operational chain instead of creating replacement objects. Passenger, request, trip, offer, booking, ticket, EMD, SSR / OSI, document, timeline, workflow, and AOIE records each have distinct responsibilities.

When a future phase needs new metadata, it should first ask:

- Which existing object owns the operational truth?
- Is this policy, pricing, capability, evidence, constraint, or procedure?
- Is the data advisory, operational, financial, or executable?
- Does this require a new model, or should it link to an existing model?
- Does it preserve `/platform/*` and `/agency/*` route boundaries?

## Advisory Boundary

AeroAssist can structure knowledge, display evidence, explain uncertainty, and prepare human-reviewed decision support. It must not silently cross into execution, enforcement, billing, provider integration, AI automation, scraping, scheduling, or route blocking unless a future phase explicitly authorizes that behavior.

## Request Segment Service Scopes

Phase 51.2 adds Request Segment Service Scopes as metadata-only intake precision records. They keep requests segment-first by joining passenger, segment, service, pet, special item, readiness, conversion, knowledge-link, and decision-trace metadata. Requests remain intake, trips remain operational dossiers, and human authority remains final.

## Reference Data Domains

Phase 52.1 adds Reference Data Domains as metadata-only operational vocabulary records for airline knowledge production. They prepare scenario testing and real airline data population while keeping human governance final.

Phase 52.2 adds Knowledge Import Templates as metadata-only schemas for airline knowledge population. They define columns, mappings, validation metadata, samples, accepted file types, review requirements, and governance links, but they must not parse files, scrape, run AI, call providers, launch workers, or automatically import/promote data.

Phase 52.4 adds Pricing Formula Builder as metadata-only no-code formula records for airline ancillary and service pricing. They define pricing units, route/flight/fare context, amount types, currencies, base amounts, formula components, multipliers, applicability, manual confirmation, client visibility, and refund/exchange condition references, but they must not calculate live prices, integrate payments, call providers, run AI, launch workers, or send automatically to clients.

Phase 52.5 adds Operational Rule Composer as metadata-only no-code compound rule records for airline passenger service restrictions and outcomes. They define applies-to scope, all/any condition groups, supported operators, result metadata, severity, messages, evidence, governance, parameter taxonomy links, effective dates, and lifecycle status, but they must not execute rules, evaluate live cases, calculate prices, call providers, run AI, launch workers, or make automatic decisions.
