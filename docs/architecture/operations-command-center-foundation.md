# Operations Command Center Foundation

Phase 54.8 adds the metadata-only Operations Command Center Foundation.

The command center is the primary agency operational visibility surface. It aggregates existing operational metadata rather than creating a duplicate operations model or a second workflow/task architecture.

## Scope

The command center summarizes:

- current operational workload
- unassigned work
- overdue and due-soon records
- critical blockers
- requests awaiting triage
- offers awaiting action
- accepted offers awaiting booking
- bookings awaiting ticketing
- service approvals and document requirements
- departures in the next 24, 48, and 72 hours
- disrupted trips
- after-sales cases
- unresolved knowledge and manual-review cases
- payment and invoice blockers
- pilot-readiness issues
- team and agent workload

## Source Metadata

The service reads from existing foundations, including work queue items, SLA deadlines, operational workflows, request intake, travel requests, offer workspaces, accepted-offer booking handoffs, booking workspaces, ticket and EMD workspaces, SSR / OSI workspaces, document workspaces, trip and flight workspaces, after-sales cases, operational intelligence cases, pilot-readiness issues, request tasks, invoices, and payments where present.

No `operations_command_center` collection is introduced in this phase. The command center is an aggregate read model over canonical records.

## Views

The agency page `/agency/operations-command-center` and platform governance page `/platform/operations-governance` expose:

- dashboard
- queue
- kanban
- calendar
- timeline
- exception list
- agent/team workload

Kanban lanes are derived from workflow state. The UI does not implement uncontrolled drag-and-drop. Any future move must call canonical workflow transitions and respect guard checks.

## APIs

Platform APIs:

- `GET /api/platform/operations-governance`
- `GET /api/platform/operations-governance/summary`
- `GET /api/platform/operations-governance/feed`
- `GET /api/platform/operations-governance/calendar`
- `GET /api/platform/operations-governance/kanban`
- `GET /api/platform/operations-governance/workload`

Agency APIs:

- `GET /api/agencies/{agency_id}/operations-command-center`
- `GET /api/agencies/{agency_id}/operations-command-center/summary`
- `GET /api/agencies/{agency_id}/operations-command-center/feed`
- `GET /api/agencies/{agency_id}/operations-command-center/calendar`
- `GET /api/agencies/{agency_id}/operations-command-center/kanban`
- `GET /api/agencies/{agency_id}/operations-command-center/workload`

Agency routes are scoped by existing agency access checks. Platform routes are read-only governance diagnostics and do not silently act as agency staff.

## Safety Boundaries

Phase 54.8 does not:

- execute providers
- call external APIs
- use AI
- schedule workers
- send messages
- book, ticket, issue EMDs, refund, exchange, or void
- mutate source entity status
- create duplicate task, workflow, or operations records
- weaken agency isolation
- bypass workflow guards

The command center provides safe action links into canonical pages where humans continue the work.
