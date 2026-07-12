# Operational Workflow Orchestration Foundation

Phase 54.1 introduces the canonical metadata layer for coordinating operational workflow state across AeroAssist. It gives Platform and Agency users a shared view of request, trip, offer, booking, ticket, EMD, document, timeline, and passenger-service workflow progression without replacing those existing workspaces.

Active phase marker:

`phase_54_1_operational_workflow_orchestration_foundation`

## Purpose

The orchestration foundation records workflow definitions, workflow instances, transition attempts, guard outcomes, warning acknowledgements, blockers, immutable transition history, and workflow events. It is designed to answer:

- Which lifecycle state is an operational object currently in?
- Which transitions are configured and available?
- Which guard checks pass, warn, block, require manual review, or remain unknown?
- What remediation guidance should staff review before moving forward?
- Which transition history and workflow events explain how the object reached its current state?

Unknown or incomplete data must create `unknown`, `warning`, or `manual_review` results. It must not crash the workflow layer.

## Collections

Phase 54.1 registers these Mongo collections:

- `operational_workflow_definitions`
- `operational_workflow_instances`
- `operational_workflow_transitions`
- `operational_workflow_guards`
- `operational_workflow_events`

The records are metadata-only and agency-scoped where operational instances, transitions, and events belong to an agency.

## Models

The foundation adds metadata models for:

- `OperationalWorkflowDefinition`
- `OperationalWorkflowInstance`
- `OperationalWorkflowTransition`
- `OperationalWorkflowGuard`
- `OperationalWorkflowEvent`

Definitions store configurable states and transitions. Instances store current state, previous state, snapshots, active warnings, and active blockers. Transitions store immutable attempt history, input snapshots, results, blockers, requested/approved metadata, and execution timestamp metadata. Guards store configured metadata checks and remediation guidance. Events store timeline-style workflow events.

## Default State Families

The service exposes safe default state maps for:

- Request lifecycle
- Trip lifecycle
- Booking readiness
- Service fulfillment

These defaults are reference metadata. They are not production seed records and do not overwrite existing entity statuses.

## Guard Outcomes

Guard evaluation returns one of:

- `passed`
- `warning`
- `blocked`
- `manual_review`
- `unknown`

Blocked transitions are rejected safely and recorded as transition metadata. Warnings require acknowledgement before a transition can be accepted with warning context. Unknown guard results lead to manual-review metadata, not crashes.

## Adapter Boundary

The service includes explicit adapters for existing request, trip, offer, booking, ticket, EMD, and passenger-service workflow modules. These adapters map existing entity status metadata into workflow-state summaries.

Entity status synchronization is disabled by default. No unrestricted dynamic mutation is allowed. Future phases must explicitly implement and review any adapter that writes back to an operational workspace.

## APIs

Platform APIs live under:

- `/api/platform/operational-workflows`

Agency APIs live under:

- `/api/agencies/{agency_id}/operational-workflows`

Platform routes expose metadata definition, guard, diagnostics, cross-agency summary, instance, transition, event, and entity-summary views. Agency routes expose agency-scoped instances, current state, available transitions, transition execution metadata, warnings, blockers, transition history, events, acknowledgements, and entity summaries.

## Frontend

Platform Console:

- `/platform/operational-workflows`

Agency Workspace:

- `/agency/operational-workflows`

Existing request, trip, offer, booking, passenger-service workflow, and timeline pages link to the orchestration summary layer without a broad UI rewrite.

## Safety Boundaries

Phase 54.1 does not:

- replace request, trip, offer, booking, ticket, EMD, document, timeline, task, or AOIE services
- execute bookings
- issue tickets or EMDs
- call GDS, NDC, airline, supplier, or external APIs
- run AI or provider execution
- send email, SMS, WhatsApp, Slack, Teams, or airline/customer messages
- schedule background work
- mutate operational entity statuses without a future explicit adapter
- bypass agency isolation
- introduce `/admin/*`, `/agent/*`, `/api/admin/*`, or `/api/agent/*` route roots

The orchestration layer is a shared workflow-state and guard metadata layer around existing operational workspaces. Human authority remains final.
