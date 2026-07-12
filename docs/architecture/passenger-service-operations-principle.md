# Passenger Service Operations Principle

AeroAssist is a Passenger Service Operations System.

The core operating chain is:

Passenger -> Need -> Service Requirement -> Airline Capability -> Operational Feasibility -> Pricing / Conditions -> Recommendation -> Fulfilment

This principle keeps the product centered on the passenger service case rather than on a supplier, booking engine, or generic CRM object.

## Foundational Architecture Documents

The permanent foundation documents under `docs/architecture/foundations/` define the passenger-service philosophy, Chapter 50 knowledge architecture, engineering rules, ontologies, and glossary that future phases must preserve.

## Future Codex Guidance

Before implementing future phases, Codex should read and follow:

- `PASSENGER_SERVICE_OPERATIONS_MANIFESTO.md`
- `AIRLINE_OPERATIONAL_KNOWLEDGE_BLUEPRINT.md`
- `AEROASSIST_ENGINEERING_PRINCIPLES.md`
- `PASSENGER_SERVICE_ONTOLOGY.md`
- `AIRLINE_OPERATIONAL_KNOWLEDGE_ONTOLOGY.md`
- `GLOSSARY.md`

## Operational Platform And AOIE

The Operational Platform answers what is happening:

- requests
- passengers
- trips
- offers
- bookings
- tickets
- EMDs
- documents
- timelines
- workflow engine records
- future SSR/OSI workspaces

The Airline Operational Intelligence Engine answers what is possible, allowed, priced, risky, and eventually recommended for the case. Phase 50.0 only documents this architecture. Phase 50.1 adds the Airline Knowledge Acquisition Workspace as manual official-source evidence intake and the Airline Operational Knowledge Graph foundation for future AOIE phases. Phase 50.2 adds the metadata-only Operational Constraint Engine language for condition groups, supported operators, outcomes, applicability, priority, governance, and future evaluation notes. Phase 50.3 adds metadata-only Airline Operational Knowledge Normalisation for canonical vocabulary and taxonomy. Phase 50.4 adds metadata-only Airline Operational Knowledge Governance & Version Control for independent Evidence, Policy, Pricing, Capability, Operational Constraint, Operational Procedure, release, comparison, rollback, superseded, archived, and historical lookup metadata. Phase 50.5 adds the metadata-only Airline Operational Capability Matrix for what airlines can operationally deliver under stated conditions. Phase 50.6 adds metadata-only Operational Evaluation Results for what operationally applies. Phase 50.7 adds advisory, evidence-linked, non-Boolean Passenger Service Feasibility records that consume those evaluation results. These foundations store source evidence, policy, pricing, capability, procedure, constraint, normalisation, governance, version, operational capability, operational evaluation, and feasibility metadata. Feasibility is not recommendation, and human authority remains final. They do not execute AI, parse with AI, scrape airline websites, search itineraries, call providers, book, ticket, issue EMDs, recommend or rank airlines, calculate pricing, publish automatically, or automate decisions.

Phase 41.9 adds the SSR / OSI Operational Workspace as the primary operational input between Passenger Need and Airline Capability:

Passenger Need -> SSR / OSI Workspace -> Airline Knowledge -> Capability Matrix -> Operational Feasibility -> Offer Builder

The workspace records passenger service requirements, SSR/OSI handling metadata, approvals, documents, EMD references, readiness, and fulfilment references. It remains metadata-only and does not transmit SSR/OSI messages, call airlines, automate approvals, issue EMDs, or run AOIE reasoning.

Phase 42.0 adds the Document Workspace as the operational document layer attached to passenger service operations:

Passenger Need -> SSR / OSI Workspace -> Document Workspace -> Airline Knowledge -> Operational Feasibility -> Fulfilment Evidence

The document workspace records required, requested, received, verified, rejected, waived, archived, and other document metadata linked to passenger, travel request, trip, booking, ticket, EMD, SSR / OSI, Phase 36.5 package/render/share, and operational intelligence records. It remains metadata-only and does not deliver documents, implement e-signature, create public links, generate PDFs automatically, generate payments or invoices, integrate external storage, run background workers, or generate documents with AI. It does not duplicate the older Phase 36.5 document render/package/share foundation.

Phase 42.1 adds the Operational Timeline Workspace as the chronological history layer attached to every operational object:

Passenger Need -> Operational Workspace -> Timeline Entry -> Review Evidence -> Fulfilment Evidence

Timeline entries record event metadata, communication summaries, approval history, reminders, attachments, visibility flags, and operational notes linked to passenger, request, trip, booking, ticket, EMD, SSR / OSI, and document workspaces. They remain metadata-only and do not send email, send SMS, use WhatsApp, Teams, or Slack, send live airline or customer messages, summarize with AI, run background workers, call providers, or automate actions.

Phase 42.2 adds the Passenger Service Workflow Engine as the coordination layer over the operational workspaces:

Passenger -> Service Requirement -> Operational Workspaces -> Timeline -> Future AOIE -> Operational Execution

Workflow records track current, previous, and next stage metadata, readiness state, blocking and completed requirements, responsible team and agent, linked passenger/request/trip/booking/ticket/EMD/SSR-OSI/document/timeline workspaces, and future AOIE recommendation-pack references. They remain metadata-only and do not execute workflows, make AI decisions, start background workers, call airline APIs, connect to GDS/NDC, approve services automatically, issue tickets, issue EMDs, send messages, or automate actions.

Phase 54.1 adds Operational Workflow Orchestration as the shared workflow-state layer around existing operational workspaces:

Request / Trip / Offer / Booking / Ticket / EMD / Service -> Workflow Definition -> Guarded Transition -> Immutable History -> Timeline Evidence

Operational workflow records store configurable definitions, agency instances, guard outcomes, warning acknowledgements, blockers, transition attempts, workflow events, and explicit adapter metadata. They do not replace request, trip, offer, booking, ticket, EMD, document, timeline, or passenger-service workflow services. Entity status synchronization remains disabled by default and requires future explicit adapters. The layer remains metadata-only and does not execute providers, run AI, send messages, schedule workers, book, ticket, issue EMDs, or automate actions.

Phase 51.2 adds segment-first intake precision:

Passenger -> Request -> Segment -> Service Requirement -> Operational Intelligence

Request Segment Service Scopes preserve passenger + segment + service metadata at intake time. Pets and special items are segment-scoped, not loose request notes. The request remains intake; the trip remains the operational dossier. This layer prepares clean operational intelligence inputs but does not evaluate policy, calculate pricing, search flights, book, ticket, issue EMDs, call providers, run AI/LLM generation, run background workers, send client messages, or convert trips automatically.

## Governance Boundary

Future AOIE phases should consume reviewed and versioned metadata from existing foundations. They should not create parallel ticket, EMD, booking, offer, service taxonomy, service mechanics, or pricing architectures.
