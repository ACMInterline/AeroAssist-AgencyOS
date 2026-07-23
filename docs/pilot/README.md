# AeroAssist Commercial Pilot Package

This directory is the controlled operating package for a micro or small travel agency evaluating AeroAssist. It supplements the in-product guidance and the Phase 57 production release gate; it does not approve a release, replace deployment runbooks, or enable provider execution.

## Package Contents

| Document | Use |
| --- | --- |
| [Pilot overview](pilot-overview.md) | Purpose, supported scope, known limitations, roles, and escalation boundaries |
| [Agency onboarding guide](agency-onboarding-guide.md) | Resumable setup and synthetic demo workspace |
| [Administrator guide](administrator-guide.md) | Agency configuration, staff governance, and daily oversight |
| [Travel consultant guide](travel-consultant-guide.md) | Core client-to-after-sales operating path |
| [First-day checklist](first-day-checklist.md) | Controlled first session |
| [Daily operations checklist](daily-operations-checklist.md) | Start-, during-, and end-of-day controls |
| [Demo workspace guide](demo-workspace-guide.md) | Safe use of synthetic scenarios |
| [Backup and recovery guide](backup-and-recovery-guide.md) | Operator boundaries and existing recovery controls |
| [Incident reporting guide](incident-reporting-guide.md) | Containment, evidence, and escalation |
| [Pilot feedback guide](pilot-feedback-guide.md) | Tenant-scoped feedback submission and review |
| [Pilot acceptance checklist](pilot-acceptance-checklist.md) | Human acceptance evidence |
| [Pilot exit checklist](pilot-exit-checklist.md) | Controlled close-out |

## Operating Rules

- Use only the canonical `/agency/*`, `/platform/*`, `/api/agencies/{agency_id}/*`, and `/api/platform/*` route families.
- Keep real credentials, payment data, raw logs, passport data, and unnecessary medical detail out of pilot feedback.
- Treat provider, payment, booking, ticketing, messaging, and publishing boundaries shown in the product as authoritative.
- Report unknown or inconsistent behavior for review. Do not work around tenant, permission, readiness, or workflow guards.
- Platform release approval remains a human Phase 57 decision supported by reviewed production evidence.

The package owner should record the repository commit and package review date used for each pilot.
