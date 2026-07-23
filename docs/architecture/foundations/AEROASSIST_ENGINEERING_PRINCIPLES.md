# AeroAssist Engineering Principles

These principles guide future AeroAssist implementation. They are architectural constraints, not suggestions.

## Rules

- Never duplicate operational models.
- Do not expand the feature or metadata surface while the P0 product-kernel freeze is active; first approve one canonical ownership map and simplify the operator workflow.
- Unconfirmed traveler claims belong to `RequestPassenger`; only explicit human identity confirmation may create or link a canonical `PassengerProfile`.
- Never invent identity fields, dates of birth, passenger types, relationships, or master records to satisfy downstream schemas.
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
- Knowledge Quality Assurance records define review findings and requested changes; they do not auto-approve, publish, execute rules, call providers, run AI, launch workers, make automatic decisions, or replace human authority.
- Evidence is required for operational recommendations.
- Canonical knowledge snapshots are immutable; detected changes create review and revalidation metadata rather than rewriting historical operational truth.
- Evidence governance must preserve raw sources, structured assertions, conflicts, effective dates, freshness, access classification, and human review separately. Conflict resolution must never erase source truth.
- Chapter 50 remains advisory, not executory.
- New services must fit the five-pillar knowledge model.
- Operational constraints should be represented generically where possible.
- Do not introduce `/admin/*` or `/agent/*` route roots.
- Do not introduce parallel RBAC or parallel trip/request/offer/booking/ticket/EMD models.
- End-to-end maturity diagnostics must reuse canonical workflow and Phase 53 readiness records; test scenarios must not silently become production operational records.
- Do not migrate architecture to Supabase, Next.js, or Horizons.

## Model Discipline

Future features must extend the existing operational chain instead of creating replacement objects. Passenger, request, trip, offer, booking, ticket, EMD, SSR / OSI, document, timeline, workflow, and AOIE records each have distinct responsibilities.

Until the product-kernel freeze exits, “future feature” work is limited to security, integrity, consolidation, pilot-blocking corrections, test coverage, documentation, and simplification. A new metadata collection or page is not an acceptable substitute for resolving ownership in the existing chain.

When a future phase needs new metadata, it should first ask:

- Which existing object owns the operational truth?
- Is this policy, pricing, capability, evidence, constraint, or procedure?
- Is the data advisory, operational, financial, or executable?
- Does this require a new model, or should it link to an existing model?
- Does it preserve `/platform/*` and `/agency/*` route boundaries?

## Advisory Boundary

AeroAssist can structure knowledge, display evidence, explain uncertainty, and prepare human-reviewed decision support. It must not silently cross into execution, enforcement, billing, provider integration, AI automation, scraping, scheduling, or route blocking unless a future phase explicitly authorizes that behavior.

## Operational Maturity Diagnostics

Phase 54.9 maturity scoring is a deterministic aggregate over canonical records. Diagnostic test cases are isolated response previews, are not persisted, and cannot create or mutate production requests, trips, offers, bookings, tickets, EMDs, after-sales cases, tasks, deadlines, or communications.

## Request Segment Service Scopes

Phase 51.2 adds Request Segment Service Scopes as metadata-only intake precision records. They keep requests segment-first by joining passenger, segment, service, pet, special item, readiness, conversion, knowledge-link, and decision-trace metadata. Requests remain intake, trips remain operational dossiers, and human authority remains final.

## Reference Data Domains

Phase 52.1 adds Reference Data Domains as metadata-only operational vocabulary records for airline knowledge production. They prepare scenario testing and real airline data population while keeping human governance final.

Phase 52.2 adds Knowledge Import Templates as metadata-only schemas for airline knowledge population. They define columns, mappings, validation metadata, samples, accepted file types, review requirements, and governance links, but they must not parse files, scrape, run AI, call providers, launch workers, or automatically import/promote data.

Phase 52.4 adds Pricing Formula Builder as metadata-only no-code formula records for airline ancillary and service pricing. They define pricing units, route/flight/fare context, amount types, currencies, base amounts, formula components, multipliers, applicability, manual confirmation, client visibility, and refund/exchange condition references, but they must not calculate live prices, integrate payments, call providers, run AI, launch workers, or send automatically to clients.

Phase 52.5 adds Operational Rule Composer as metadata-only no-code compound rule records for airline passenger service restrictions and outcomes. They define applies-to scope, all/any condition groups, supported operators, result metadata, severity, messages, evidence, governance, parameter taxonomy links, effective dates, and lifecycle status, but they must not execute rules, evaluate live cases, calculate prices, call providers, run AI, launch workers, or make automatic decisions.

Phase 52.6 adds Knowledge Quality Assurance as metadata-only QA review records for airline knowledge production. They define checks, issues, severity, reviewer metadata, requested changes, approval recommendations, and governance links, but they must not auto-approve, publish, execute rules, call providers, run AI, launch workers, or make automatic decisions.

Phase 52.7 adds Airline Knowledge Publishing as metadata-only controlled publication workflow records for approved airline operational knowledge. They define included knowledge artifacts, QA review links, release channels, effective dates, supersession, rollback plans, consumer readiness, AOIE readiness, and agency visibility, but they must not publish automatically, execute recommendations, call providers, run AI, launch workers, or make automatic decisions.

Phase 52.8 adds Operational Scenario Testing as metadata-only passenger service scenario test records. They define passenger, itinerary, airline, service requirement, pet, special item, document, expected policy, expected pricing, expected feasibility, expected recommendation, required-action, evidence, and review metadata, but they must not run live providers, execute parsers, run AI, launch workers, book, ticket, issue EMDs, or make automatic decisions.

Phase 52.9 adds Knowledge Population Toolkit as metadata-only airline knowledge population readiness records. They define onboarding, reference, template, policy, pricing, rule, QA, publishing, scenario-test, evidence coverage, progress, missing-domain, blocker, warning, next-action, owner, due-date, and note metadata, but they must not scrape, auto-import, run AI, call providers, launch workers, execute parser/import jobs, or make automatic decisions.

Phase 55.4 coverage scores must be deterministic projections over canonical evidence, policy, pricing, capability, constraint/procedure, QA, publication, and scenario metadata. A critical knowledge gap must never be hidden by a numerical average or marked operationally ready. Agency coverage must contain only published, authorized knowledge and sanitized warnings.

Phase 55.5 distribution capability records must separate documented capability, configured provider, tested sandbox, and production-enabled provider stages. They must never store credentials or imply live connectivity, and they must extend the existing distribution/PSS/GDS context rather than replace it.

Phase 55.9 airline-intelligence release readiness must consolidate canonical Epic 55 sources. Critical gates must override aggregate scores, release decisions must be human and audited, population-wave completion must never auto-publish, and agency views must exclude drafts and restricted internal traces.

## Canonical Journey Representation

Journey and itinerary views are projections over canonical operational entities. They must retain source entity and source segment references, preserve accepted and issued historical snapshots, represent unknown data explicitly, and never become a parallel Trip, Offer, Booking, Ticket, EMD, Passenger, or flight-segment source of truth. Only supplied UTC timestamps may drive deterministic elapsed-time calculations. Finalized Journey snapshots are immutable and non-destructive.

Journey authoring records are pre-application metadata, not another canonical itinerary family. Preserve raw source input immutably, distinguish raw/normalized/enriched/agent-confirmed values, reuse existing parsers and imports, require explicit timezone context for calculations, retain corrections and application traces, and never overwrite agent-confirmed fields with enrichment. Apply through the canonical Journey service and never mutate finalized snapshots or auto-publish.

Journey option composition must reference canonical Journey segments rather than copy source truth. Keep governed fare intelligence distinct from manually entered commercial values, validate arithmetic without pretending to calculate a live fare, preserve unknown service and interline conditions, separate client-safe explanations from internal instructions, and require explicit human actions for preference selection, snapshot finalization, and Offer Workspace handoff. A composition or handoff must never imply availability, publication, acceptance, booking, ticketing, EMD issuance, or provider execution.
## Journey Comparison Presentation Rule

Client itinerary comparisons must project canonical Journey and governed composition truth. They must preserve unknowns, keep internal evidence and commercial construction out of client payloads, distinguish deterministic dimension leaders from an explicit human preferred option, and hand off only immutable reviewed snapshots. A presentation must never become a parallel Offer, Document, Booking, Ticket, or provider-execution model.

## Offer Delivery Rule

Client delivery must originate from an immutable, reviewed Journey comparison snapshot and must use authenticated portal identity plus explicit recipient authorization. Released payloads remain immutable, warning acknowledgement and client decisions remain auditable, and acceptance must pass through the canonical Offer Acceptance service as a separate guarded action. Delivery records must never become a parallel Offer, Document, messaging, payment, booking, ticketing, or provider-execution system.

## Product Surface Review Gate

One operational object has one primary workspace. Engines and services do not automatically justify top-level Agency pages; supporting capabilities should be embedded or linked contextually from their owning workspace. Separate surfaces require a different actor, Platform governance purpose, independent lifecycle, or materially different operational object. Every phase must apply [Product Surface and Workspace Governance](../product-surface-workspace-governance.md), use travel-agent vocabulary in ordinary UI, preserve passenger-needs-first design, and reject duplicate lifecycles or unnecessary navigation.
