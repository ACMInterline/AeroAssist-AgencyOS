# Canonical Automation and Orchestration Contract

## Purpose

AeroAssist converts canonical operational timeline events into controlled
internal work. It does not create a second business lifecycle:

`OperationalTimeline event -> governed rule evaluation -> OperationalWorkItem,
deadline, approval, or notification projection -> human action -> completion
evidence -> OperationalTimeline event`

The Product Kernel remains authoritative for requests, offers, acceptances,
trips, bookings, tickets, EMDs, commercial ledger records, documents,
communications, timeline, and Portal projections.

## Ownership

- `OperationalWorkItem` is the sole actionable task owner.
- `OperationalTimeline` is the chronological operational owner.
- `AuditEvent` is the security and mutation evidence owner.
- `CommunicationThread` and `CommunicationMessage` own communications.
- `NotificationProjection` is regenerable and is never business truth.
- Source entities retain their own lifecycle truth.

`request_tasks` is retained as immutable compatibility history. Supported
request-task mutations write `OperationalWorkItem`; queue synchronization may
project previously unmapped historical rows without modifying them.

## Execution Contract

Executions require an exact Agency-scoped source timeline entry. Only active,
published rules in effective date scope are evaluated. Ordering uses priority,
stable rule key, descending version, and record ID. A source event, rule
version, and action index produce stable deduplication lineage.

Every execution is deterministic, bounded, redacted, idempotent, replay-safe,
and linked to its source event. A reservation and recoverable lease are written
before actions. Stale leases enter `manual_review`; poison work is not retried
without an operator.

## Deployment Model

No persistent scheduler is enabled. Agency administrators may invoke guarded,
bounded timeline and reminder processing routes. Each batch has a hard limit,
startup never scans unbounded history, and external delivery remains disabled.

## Boundaries

The orchestrator cannot change Agency scope, permissions, tenant ownership, or
externally meaningful Product Kernel state. It cannot run arbitrary code or
perform airline, GDS, NDC, supplier, messaging, ticketing, EMD, payment,
refund, accounting, legal, medical, safety, pricing, or eligibility actions.
Human authority remains final.
