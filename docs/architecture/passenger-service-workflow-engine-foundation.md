# Passenger Service Workflow Engine Foundation

Phase 42.2 adds the metadata-only Passenger Service Workflow Engine. It coordinates a passenger service case across the operational workspace records already created in AeroAssist; it does not replace those records and it does not execute work.

## Purpose

The engine records where a passenger service case sits in the operational journey:

Passenger -> Service Requirement -> Operational Workspaces -> Timeline -> Future AOIE -> Operational Execution

The current phase stores only metadata needed for human visibility and future governance. It does not run automatic workflow execution, AI decision making, background workers, airline APIs, GDS connectivity, NDC connectivity, automatic approvals, ticketing, EMD issuance, or messaging.

## Collection

`passenger_service_workflows`

Each record stores agency scope, workflow reference/status/type/version, linked passenger/request/trip/booking/ticket/EMD/SSR-OSI/document/timeline workspace references, current/previous/next stages, readiness state, blocking and completed requirements, responsible team/agent, airline and priority metadata for filtering, future AOIE recommendation-pack reference, timeline dates, and operational notes.

## Stage Definitions

- `passenger_registered`
- `requirements_collected`
- `service_requirements_analysed`
- `airline_evaluation`
- `offer_preparation`
- `offer_accepted`
- `booking_ready`
- `booking_completed`
- `ticket_ready`
- `ticket_completed`
- `emd_required`
- `emd_completed`
- `documents_pending`
- `documents_complete`
- `travel_ready`
- `travel_completed`
- `case_closed`

## Readiness States

- `ready`
- `waiting_for_customer`
- `waiting_for_airline`
- `waiting_for_documents`
- `waiting_for_payment`
- `waiting_for_approval`
- `waiting_for_emd`
- `blocked`
- `completed`

## APIs

Platform metadata views and metadata CRUD:

- `GET /api/platform/passenger-service-workflows`
- `GET /api/platform/passenger-service-workflows/summary`
- `POST /api/platform/passenger-service-workflows`
- `GET /api/platform/passenger-service-workflows/{workflow_id}`
- `PUT /api/platform/passenger-service-workflows/{workflow_id}`
- `DELETE /api/platform/passenger-service-workflows/{workflow_id}`

Agency read-only views:

- `GET /api/agencies/{agency_id}/passenger-service-workflows`
- `GET /api/agencies/{agency_id}/passenger-service-workflows/summary`
- `GET /api/agencies/{agency_id}/passenger-service-workflows/{workflow_id}`

Filters include workflow stage, readiness, passenger workspace, airline, priority, and assigned agent. Agency responses are read-only and agency-scoped.

## UI

Platform Console:

- `/platform/passenger-service-workflows`

Agency Workspace:

- `/agency/workflow-engine`

Both pages show workflow lists and expandable metadata details for current/previous/next stage, readiness, blocking requirements, completed requirements, linked workspaces, future AOIE reference, and operational notes.

## Safety Boundary

This foundation is metadata-only. It does not automate workflow transitions, decide cases with AI, start workers, call airline/GDS/NDC/provider APIs, approve services, issue tickets, issue EMDs, send messages, or enforce operational behavior.
