# Pilot Feedback Guide

## Agency Submission

Open `/agency/pilot-feedback`. Select a category, affected area, urgency, clear title, and description. Optionally link a canonical record by type and ID. The API verifies that the record exists in the same agency before storing the link.

Categories are usability, workflow, data, documentation, defect, suggestion, and other. Agency users can read only their agency’s feedback. Read-only users cannot submit.

## Platform Review

Open `/platform/pilot-feedback`. Filter by agency, status, category, or urgency, inspect the sanitized context, and record a valid status transition with review notes.

Lifecycle:

`submitted` → `reviewing` → `planned` or `resolved` → `closed`

Governed alternatives allow closure, reopening to review, and resolution without deleting source feedback. The original agency, submission text, submitter context, and related-record reference remain immutable through review.

## Content Rules

Describe expected behavior, observed behavior, operational impact, and recovery. Do not include credentials, payment data, raw logs, passport data, unnecessary medical data, or private external attachments. Pilot feedback is an internal governed record, not a public anonymous form or external support integration.
