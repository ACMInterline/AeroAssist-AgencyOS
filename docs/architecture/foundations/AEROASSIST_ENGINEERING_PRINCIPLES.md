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
