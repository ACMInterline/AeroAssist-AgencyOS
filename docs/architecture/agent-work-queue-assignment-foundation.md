# Agent Work Queue and Assignment Foundation

Phase 54.2 introduces the canonical operational work queue for agency staff.

The foundation is metadata-first and consolidates actionable work from existing operational objects rather than creating a second task system. Work items can reference requests, trips, offers, bookings, ticketing, EMDs, passenger services, documents, approvals, policy gaps, knowledge issues, disruptions, service cases, workflow blockers, request tasks, workflow events, and timeline-compatible history.

## Scope

The phase adds four metadata models:

- `OperationalWorkItem`
- `OperationalQueueDefinition`
- `OperationalAssignmentEvent`
- `OperationalQueueView`

The Mongo collections are:

- `operational_work_items`
- `operational_queue_definitions`
- `operational_assignment_events`
- `operational_queue_views`

Platform APIs live under `/api/platform/work-queues`. Agency APIs live under `/api/agencies/{agency_id}/work-queue`. Frontend pages are `/platform/work-queues` and `/agency/work-queue`.

## Queue Behavior

The queue supports canonical views for unassigned work, my work, team queue, urgent/critical work, due soon, overdue, blocked, waiting client, waiting airline/supplier, waiting documents, waiting approval, waiting payment, disruption queue, service-case queue, knowledge-gap queue, and workflow blockers.

Ordering is deterministic:

1. Active records before completed/cancelled records.
2. Priority.
3. SLA status.
4. Due date.
5. Severity.
6. Creation time.

Unknown or incomplete source metadata is represented as warnings, manual review, unknown SLA state, or queue metadata. It must not crash queue rendering or synchronization.

## Assignment Metadata

Assignment actions record metadata and append immutable assignment events:

- assign to self
- assign to agent
- reassign
- unassign
- accept work
- release work
- mark in progress
- block
- complete
- reopen
- bulk assignment for safe eligible records

The assignment event stream preserves actor history with `from_user_id`, `to_user_id`, team metadata, reason, payload metadata, and timestamps.

## Source Synchronization

Work-item generation is idempotent. The service builds a stable source fingerprint from agency, work item type, source entity type, source id, workflow instance, workflow event, and request task metadata.

Phase 54.2 synchronizes from:

- operational workflow events and blockers
- request tasks
- travel request records and travel request workspaces
- offer workspaces
- booking workspaces
- document workspaces
- pilot readiness issues

This is synchronization of metadata only. It does not execute workflows, mutate operational records, send messages, call providers, schedule background jobs, or enforce access beyond existing tenant permissions.

## Security And Boundaries

Agency endpoints enforce agency isolation and staff roles. Platform endpoints provide governance and inspection over queue definitions and metadata; platform governance must not silently act as agency staff.

Internal context remains internal metadata. Client-facing route families must not receive hidden operational context.

This foundation reuses existing `RequestTask`, operational timeline, operational workflow, passenger service workflow, and workspace models through compatibility mappings. Future phases may add explicit adapters, but they must not duplicate task, workflow, trip, request, offer, booking, ticket, EMD, document, or passenger-service architectures.

## Non-Goals

Phase 54.2 does not add:

- provider execution
- AI execution
- email/SMS/notification sending
- background workers
- schedulers
- automatic workflow execution
- entitlement enforcement
- booking, ticketing, or EMD issuance
- external APIs
- route blocking
- duplicate task systems
- duplicate workflow architecture

Human authority remains final.
