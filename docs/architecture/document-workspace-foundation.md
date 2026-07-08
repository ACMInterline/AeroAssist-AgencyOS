# Document Workspace Foundation

Phase 42.0 adds the metadata-only operational Document Workspace layer for passenger service operations.

This phase does not replace or duplicate the Phase 36.5 document render/package/share foundation. Phase 36.5 remains the foundation for templates, internal render jobs, document packages, and manual/internal share records. Phase 42.0 records the operational document workspace around those references so agents can see which documents are needed, received, verified, linked, visible, missing, rejected, or valid for a passenger service workflow.

## Collection

`document_workspaces`

The collection is additive and index-only. No destructive migration or production data rewrite is introduced.

## Metadata Scope

Each document workspace can link to:

- passenger workspaces
- travel request workspaces
- trip workspaces
- booking workspaces
- ticket workspaces
- EMD workspaces
- SSR / OSI operational workspaces
- operational intelligence records
- Phase 36.5 package, render job, and share record metadata

Tracked metadata includes document reference, type, category, status, passenger, booking, PNR, ticket, EMD, SSR/OSI, service requirement, travel/airline/airport/authority requirement flags, requirement deadline, received and verification status, validity dates, issuing authority, language, storage reference, package/render/share references, visibility flags, missing/rejection reasons, and operational notes.

## APIs

Platform metadata views:

- `GET /api/platform/document-workspaces`
- `GET /api/platform/document-workspaces/summary`
- `POST /api/platform/document-workspaces`
- `GET /api/platform/document-workspaces/{workspace_id}`
- `PUT /api/platform/document-workspaces/{workspace_id}`
- `DELETE /api/platform/document-workspaces/{workspace_id}`

Agency read-only views:

- `GET /api/agencies/{agency_id}/document-workspaces`
- `GET /api/agencies/{agency_id}/document-workspaces/summary`
- `GET /api/agencies/{agency_id}/document-workspaces/{workspace_id}`

Filters include document type, document status, passenger, booking reference, related service, required-for-travel, verification status, and deadline.

## UI

Platform Console:

- `/platform/document-workspaces`

Agency Workspace:

- `/agency/document-workspaces`

The Agency page is read-only and labeled Documents. It is separate from the existing `/agency/documents` rendered-document view.

## Safety Boundaries

Phase 42.0 does not implement live document delivery, e-signature, public share links, automatic PDF generation, payment or invoice generation, external storage integrations, background workers, AI document generation, provider execution, external API calls, or automation.

All records are metadata-only operational visibility records.
