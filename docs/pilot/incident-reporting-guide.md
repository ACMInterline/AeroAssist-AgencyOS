# Pilot Incident Reporting Guide

## Report Immediately

- Cross-agency data visibility or mutation.
- Authentication or permission bypass.
- Loss, unexplained mutation, or duplication of operational state.
- Health/readiness failure affecting work.
- Exposure of credentials, payment data, passenger identity documents, medical detail, or raw logs.
- External provider, payment, ticketing, messaging, or publishing behavior that should be disabled.
- Inability to distinguish synthetic from real operational records.

## Contain

Stop the affected workflow. Do not retry destructive actions, alter audit evidence, restart production, restore data, or deploy a change unless the authorized incident procedure directs it.

## Record

Capture only sanitized facts:

- UTC time, environment, agency, affected module, and operator.
- What the operator attempted and what the UI/API returned.
- Safe record references, request/correlation identifiers, and visible status.
- Operational impact and whether data may have crossed a boundary.
- Steps already taken and current containment state.

Do not paste secrets, full raw logs, payment data, passport data, or unnecessary medical details into pilot feedback.

Use Agency feedback for non-security pilot issues. Use the approved security/production incident channel for sensitive or critical incidents, then link only a sanitized reference in AeroAssist.
