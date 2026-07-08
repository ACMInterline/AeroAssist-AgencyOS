# SSR / OSI Operational Workspace Foundation

Phase 41.9 adds the metadata-only SSR / OSI Operational Workspace foundation.

This workspace is the operational heart of passenger service handling:

Passenger Need -> Operational Service Requirement -> Operational Fulfilment

It is not an SSR code repository. It is an agency-scoped operational record that links passenger needs to service classification, SSR/OSI metadata, airline handling, airport handling, EMD references, document requirements, MEDIF status, tasks, timeline references, communications, missing requirements, readiness, and operational notes.

## Collection

`ssr_osi_workspaces`

Records are agency-owned metadata and include additive indexes for workspace reference, agency, need category, airline, approval status, readiness status, passenger workspace, priority, RFIC, RFISC, operational status, related operational workspace, travel request, trip, booking, ticket, EMD, flights, and documents.

## Interfaces

- Platform API: `/api/platform/ssr-osi-workspaces`
- Agency API: `/api/agencies/{agency_id}/ssr-osi-workspaces`
- Platform UI: `/platform/ssr-osi-workspaces`
- Agency UI: `/agency/passenger-services`

Platform routes may create, update, archive, list, and read metadata records. Agency routes are read-only.

## Metadata Scope

The workspace stores:

- passenger need category, subcategory, description, and passenger statement
- service family/type plus ancillary, operational, medical, and mobility categories
- SSR code, description, status, and confirmation status
- OSI requirement, text, and status
- airline handling metadata, approval status/reference/deadline, and carrier references
- airport handling station and handling company metadata
- EMD requirement, EMD workspace references, RFIC, and RFISC
- document requirements, MEDIF metadata, certificates, veterinary, customs, and visa requirements
- task, timeline, and communication references
- readiness status, missing requirements, unresolved items, flights, documents, and notes

## AOIE Preparation

This workspace becomes the primary operational input for the Airline Operational Intelligence Engine:

Passenger Need -> SSR / OSI Workspace -> Airline Knowledge -> Capability Matrix -> Operational Feasibility -> Offer Builder

AOIE will later consume this metadata to reason about capability, feasibility, required documents, deadlines, risks, RFIC/RFISC mechanics, and offer-builder context. Phase 41.9 does not perform that reasoning.

## Explicit Non-Goals

Phase 41.9 does not implement live SSR transmission, live OSI transmission, GDS connectivity, NDC connectivity, airline APIs, AI recommendation, automatic airline approval, automatic EMD issuance, background workers, provider integrations, external API calls, or automation.
