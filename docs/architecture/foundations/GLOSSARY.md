# Glossary

## Passenger Service Operations

The AeroAssist operating model for fulfilling passenger service requirements across requests, trips, offers, bookings, tickets, EMDs, documents, SSR / OSI records, timelines, workflows, and AOIE advisory knowledge.

## Passenger Service Requirement

A structured passenger need that has operational consequences for airline, airport, booking, ticket, document, approval, EMD, or travel-readiness handling.

## Airline Operational Knowledge Graph

The structured knowledge layer that links airline evidence, policy, pricing, capability, constraints, procedures, governance, and future decision-support metadata.

## Evidence

Reviewed source material or provenance that supports an operational knowledge claim.

## Policy

An airline, airport, authority, supplier, or internal rule that describes what is allowed, required, restricted, or prohibited.

## Pricing

Commercial charge, fee, fare, tax, EMD, refundability, exchangeability, or cost condition metadata. Pricing is not the same as capability.

## Capability

The ability of an airline, aircraft, cabin, airport, station, supplier, or operational process to support a passenger service requirement. Capability is not the same as policy.

## Capability Matrix

A metadata-only operational inventory of what airlines can deliver under stated airline, service, aircraft, cabin, airport, route, country, season, interline/codeshare, restriction, risk, confidence, evidence, and governance conditions. It does not evaluate passenger feasibility or recommend airlines.

## Operational Constraint

A structured condition that affects eligibility, handling, approval, documentation, timing, aircraft/cabin applicability, route applicability, pricing, or fulfilment.

## Operational Procedure

The required human or operational steps for fulfilling a service requirement, including review, approval, documentation, communication, EMD handling, airport handling, and readiness checks.

## Decision Pack

A future human-reviewed advisory package that explains evidence, applicability, constraints, risks, uncertainty, and rationale for passenger service feasibility or recommendation decisions.

## Feasibility

An advisory assessment of whether a passenger service profile can be fulfilled under known evidence, policy, pricing, capability, constraints, and procedures.

## Passenger Service Feasibility

A Phase 50.7 advisory, evidence-linked record that consumes Operational Evaluation Results and stores a non-Boolean outcome such as fully feasible, conditionally feasible, operational review required, operationally blocked, or unknown. It is not an airline recommendation, ranking, booking action, or final authority.

## Recommendation

An advisory output that suggests airline or itinerary options based on reviewed evidence, Passenger Service Feasibility, and structured operational knowledge. A recommendation is not an execution action, search action, booking action, price generation, or final authority.

## Offer Intelligence Package

A Phase 50.9 metadata package that prepares approved recommendations, feasibility records, operational evaluations, capability matrix records, knowledge versions, evidence references, required actions, explanations, decision pack metadata, and lifecycle state for human-reviewed offer presentation. It does not create bookings, tickets, EMDs, prices, provider searches, AI/LLM output, or automatic client messages.

## Operational Intelligence Case

A Phase 51.0 metadata case that consolidates the completed Chapter 50 pipeline from passenger requirement through offer-intelligence package. It preserves pipeline links, readiness, decision summaries, required actions, traces, and notes for scenario testing and real airline data population. It adds no new intelligence and does not execute bookings, issue tickets or EMDs, call providers, generate AI/LLM output, or send client messages.

## Reference Data Engine

A Phase 52.1 metadata-only foundation that stores governed reference domains for airline operational knowledge production. Domains contain records, aliases, normalization rules, validation rules, import-template references, governance status, review status, and active state. It prepares scenario testing and real airline data population without provider integrations, AI/LLM generation, live evaluation, pricing calculation, background workers, old `/admin` routes, or automation. Human authority remains final.

## Knowledge Import Templates

A Phase 52.2 metadata-only foundation that stores reusable schemas for airline knowledge population. Templates contain template type, version, target knowledge domain, target collections, required columns, optional columns, validation rules, mapping rules, sample rows, accepted file types, import scope, review requirements, and governance links. It does not parse files, scrape, use AI/LLM generation, call providers, run background workers, automatically import data, or replace human review.

## Visual Policy Editor

A Phase 52.3 metadata-only foundation that stores structured airline service policy cards. Cards contain airline, policy family, service family, service codes, status, effective dates, support status, limits, restrictions, required documents, approval requirements, warnings, client messages, internal notes, evidence links, knowledge governance links, and service parameter taxonomy links. It does not execute policies, evaluate rules, calculate pricing, use AI/LLM generation, call providers, run background workers, add old `/admin` routes, or replace human authority.

## Pricing Formula Builder

A Phase 52.4 metadata-only foundation that stores no-code airline ancillary and service pricing formula records. Records contain pricing unit, way, route type, flight type, fare bundle, pricing category, amount type, currency, base amount, formula components, multipliers, applicability, manual confirmation, client visibility, refund/exchange condition references, evidence links, governance links, service parameter taxonomy links, and visual policy editor links. It does not calculate live prices, integrate payments, call providers, use AI/LLM generation, run background workers, send automatically to clients, or replace human authority.

## Operational Rule Composer

A Phase 52.5 metadata-only foundation that stores no-code compound airline passenger service restriction and outcome records. Records contain rule family, service family, service codes, applies-to metadata, all/any condition groups, supported operators, result metadata, severity, client/internal messages, evidence links, governance links, service parameter taxonomy links, effective dates, and lifecycle status. It does not execute rules, evaluate live cases, calculate pricing, call providers, use AI/LLM generation, run background workers, make automatic decisions, or replace human authority.

## Knowledge Quality Assurance

A Phase 52.6 metadata-only foundation that stores airline knowledge QA review records. Records contain target metadata, airline/service scope, QA status, issues, severity, reviewer metadata, requested changes, approval recommendations, and governance links. It does not auto-approve, publish, execute rules, call providers, use AI/LLM generation, run background workers, make automatic decisions, or replace human authority.

## Airline Knowledge Publishing

A Phase 52.7 metadata-only foundation that stores controlled publication workflow records for approved airline operational knowledge. Records contain included knowledge versions, policy cards, pricing formulas, rules, QA review links, publication status, release channel, effective dates, supersession metadata, rollback plan, consumer readiness, AOIE readiness, and agency visibility. It does not publish automatically, execute recommendations, call providers, use AI/LLM generation, run background workers, make automatic decisions, or replace human authority.

## Operational Scenario Testing

A Phase 52.8 metadata-only foundation that stores passenger service scenario test cases for validating knowledge production examples. Records contain passenger, itinerary, airline, service requirement, pet, special item, document, expected policy, expected pricing, expected feasibility, expected recommendation, required-action, evidence, status, and review metadata. It does not run live providers, use AI/LLM generation, execute parsers, execute scenario automation, book, ticket, issue EMDs, run workers, or replace human authority.

## Knowledge Population Toolkit

A Phase 52.9 metadata-only foundation that stores airline knowledge population readiness and coverage records. Records contain onboarding checklist, reference readiness, import template readiness, policy editor readiness, pricing builder readiness, rule composer readiness, QA readiness, publishing readiness, scenario test readiness, evidence coverage, population progress, missing domains, blockers, warnings, next actions, owner, due dates, and notes. It does not scrape, auto-import, call providers, use AI/LLM generation, execute parser/import jobs, run workers, or replace human authority.

## Pilot Readiness

A Phase 53.0 metadata-only diagnostic foundation that records whether the end-to-end AeroAssist lifecycle is coherent enough for pilot review. It uses profiles, deterministic assessments, checks, issue records, module readiness summaries, golden-path cases, golden-path runs, and remediation links without auto-seeding production data, resetting records, executing providers, using AI, sending messages, booking, ticketing, or overriding human authority.

## Operational Workflow Maturity

The Phase 54.9 deterministic assessment of how completely the canonical operational chain is linked across workflow, assignment, SLA, task dependencies, request-to-trip conversion, accepted-offer booking handoff, servicing, command-center visibility, audit, client/internal message separation, agency isolation, and production safety. It reuses Phase 53 and Epic 54 metadata and runs only isolated, non-persisted diagnostics.

## Operational Workflow Orchestration

A Phase 54.1 metadata-only foundation that records shared workflow definitions, workflow instances, guarded transitions, warning acknowledgements, blockers, immutable transition history, workflow events, and explicit adapter metadata around existing operational workspaces. It coordinates lifecycle visibility without replacing request, trip, offer, booking, ticket, EMD, document, timeline, or passenger-service workflow services, and without provider execution, AI, background workers, message sending, automatic status mutation, booking, ticketing, EMD issuance, or automation.

## Agent Work Queue

A Phase 54.2 metadata-only foundation that records canonical agency staff work items, queue definitions, saved queue views, and assignment events. It consolidates existing tasks, timelines, workflow blockers, operational workspace metadata, pilot readiness issues, and agency users without creating a second task system, executing providers, sending messages, running workers, or automating actions.

## Operational SLA Policy

A Phase 54.3 metadata-only policy for advisory deadline calculation. It describes scope, entity/work type, priority, service family, route/flight context, duration, business-hour behavior, pause conditions, escalation thresholds, and effective dates without enforcing runtime access or automating work.

## Operational Deadline

A Phase 54.3 metadata-only due-date record linked to source operational entities, work items, workflow instances, request tasks, and timeline entries. It stores calculated and original due dates, status, breach state, paused duration, explanation, calculation snapshot, manual extension metadata, and escalation suggestions.

## Operational SLA Event

A Phase 54.3 metadata-only audit event for deadline lifecycle changes such as started, paused, resumed, warning, breached, extended, completed, waived, or recalculated.

## Operational Business Calendar

A Phase 54.3 metadata-only calendar defining timezone, working days, working hours, holidays, and exceptions for advisory deadline calculations.

## Operational Task Template

A Phase 54.4 metadata-only reusable task pattern that describes a title, description, trigger event, default priority, due offset, assignment strategy, required capability, dependency template codes, completion conditions, and effective dates for safe creation of existing request tasks.

## Operational Task Dependency

A Phase 54.4 metadata-only predecessor/successor relationship between existing request tasks. It can mark successors as waiting until dependency metadata is satisfied or waived, but it does not execute work, enforce routes, or call providers.

## Operational Task Automation Rule

A Phase 54.4 metadata-only rule that matches a trigger event and event snapshot to a generated task template with an idempotency/deduplication key. It does not execute arbitrary code.

## Operational Task Automation Run

A Phase 54.4 metadata-only audit record that stores the trigger event, event snapshot, matched rules, tasks created or skipped, dependency records created, warnings, errors, retry lineage, and idempotency key for safe task creation.

## Golden Path Case

A metadata-only passenger service scenario used to test whether the knowledge-production-to-offer-readiness lifecycle has enough structured evidence and operational coverage for pilot review. Sample templates are exposed but not auto-seeded.

## Golden Path Run

A persisted diagnostic run of a golden-path case. It records stage statuses, warnings, blockers, evidence references, client-facing messages, and internal trace metadata without creating requests, offers, bookings, tickets, EMDs, messages, or external provider actions.

## SSR

Special Service Request. A structured airline service request code or message used for passenger service handling.

## OSI

Other Service Information. Airline message information that communicates relevant service context without necessarily requesting a specific SSR-coded service.

## EMD

Electronic Miscellaneous Document. A document used for ancillary services, fees, or other non-ticket air travel charges.

## RFIC

Reason For Issuance Code. A high-level EMD category code.

## RFISC

Reason For Issuance Sub Code. A more specific EMD service sub-code.

## PETC

Pet in cabin. An SSR/service concept for an animal transported in the passenger cabin.

## AVIH

Animal in hold. An SSR/service concept for an animal transported in the aircraft hold.

## EXST

Extra seat. An SSR/service concept for an additional seat required for a passenger, comfort, medical, musical instrument, or other approved use.

## CBBG

Cabin baggage. An SSR/service concept for approved baggage occupying a cabin seat.

## MEDIF

Medical Information Form. A medical clearance document or process used by airlines for certain medical or assistance cases.

## AOIE

Airline Operational Intelligence Engine. The Chapter 50 advisory architecture that connects passenger service requirements to structured airline operational knowledge.

## Service Parameter Taxonomy

A metadata-only reusable vocabulary of measurable service fields, such as species, breed, weight, container dimensions, mobility level, wheelchair type, battery type, route type, aircraft type, cabin, pricing unit, amount type, and refund condition. It supports structured knowledge entry and future human-reviewed evaluation inputs without evaluating rules, calculating prices, calling providers, using AI/LLM logic, or automating decisions.

## Request Segment Service Scope

A Phase 51.2 metadata-only record that preserves segment-first intake precision by joining one passenger context, one request segment context, and one requested service context. It can include pet and special item metadata, operational flags, knowledge links, readiness, trip conversion metadata, request snapshots, decision traces, and operational notes. It does not evaluate policy, calculate pricing, search, book, ticket, issue EMDs, call providers, use AI/LLM logic, run workers, send automatically, or convert trips automatically.
# Phase 55.1 Terms

**Airline Master Profile**: The governed enrichment view composed around an existing canonical `airline_profiles.id`; it is not a separate airline catalogue.

**Canonical Airline ID**: The stable id of the existing `airline_profiles` record used by airline intelligence, evidence, capability, and operational profile links.

**Airline Identity Alias**: A governed former name, commercial name, code, or other identifier that resolves to one canonical airline identity.

**Profile Completeness**: A deterministic measure of known identity, network, operations, servicing, governance, evidence, and effective-date fields. Missing data remains explicit.

**Profile Confidence**: A deterministic advisory score based on governed confidence, completeness, verified evidence, and unresolved evidence conflicts.
