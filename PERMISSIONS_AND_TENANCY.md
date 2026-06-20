# Permissions And Tenancy

## Tenancy Principles

- Each agency has isolated operational data.
- `agency_id` is mandatory on agency-owned operational records.
- Global reference and airline intelligence data is shared through controlled read access.
- Agency overrides are private to the owning agency.
- Client portal access is constrained by agency, client account, and client/passenger relationship permissions.
- Platform users may support or manage tenants according to platform roles and audit policy.

## Platform Roles

| Role | Can View | Can Edit |
| --- | --- | --- |
| `platform_owner` | All platform and tenant metadata | Platform configuration, subscription, global policies, emergency support access |
| `platform_admin` | Platform registry, agencies, global configuration | Agency provisioning, subscription/workspace state, feature flags |
| `platform_knowledge_editor` | Airline intelligence drafts and published records | Create/update knowledge drafts, attach sources, submit for review |
| `platform_support` | Limited support views with audit | Support fields and tenant troubleshooting according to access policy |

Platform access to agency operational data should be audited and minimized.

## Agency Roles

| Role | Primary Permissions |
| --- | --- |
| `agency_owner` | Full agency workspace, billing/subscription-facing settings, staff management, data export policy. |
| `agency_admin` | Workspace configuration, staff management except owner transfer, operational records. |
| `agency_agent` | Clients, passengers, requests, offers, bookings, tickets, EMDs, documents, messages, tasks. |
| `agency_accountant` | Invoices, payments, refunds/exchanges, financial exports, limited booking context. |
| `agency_readonly` | Read-only access to permitted agency records, excluding restricted commercial or internal fields if configured. |

## Client And Passenger Roles

| Role | Primary Permissions |
| --- | --- |
| `client_user` | Portal access to own client profile and permitted passenger/travel records. |
| `passenger_user` | Optional future role for passenger-owned portal access. |
| `authorized_contact` | Delegated access according to relationship or authorization record. |

## Client Account Statuses

- `no_portal_access`
- `invited`
- `active`
- `suspended`
- `archived`

Agency staff can create client profiles without login access, invite later, resend invitations, suspend access, and archive accounts.

## Client/Passenger Permission Fields

Relationship permissions control:

- `can_view`
- `can_edit`
- `can_upload_documents`
- `can_request_travel`
- `can_pay`
- `can_receive_notifications`

Access is also limited by:

- `consent_status`
- `valid_from`
- `valid_to`
- Agency-level portal settings.
- Record-specific document visibility.

## Tenant Boundaries

Agency-owned records must be isolated:

- Clients.
- Passengers.
- Relationships.
- Requests.
- Offers.
- Bookings.
- Tickets.
- EMDs.
- Invoices.
- Payments.
- Documents.
- Messages.
- Tasks.
- Notes.
- Website/CMS content.
- Agency-specific agreements and overrides.

Global shared records:

- Airlines.
- Airports.
- Countries.
- Aircraft types.
- Service taxonomy.
- RFIC/RFISC tables.
- Published airline knowledge.
- Global templates.

## Staff Permissions

Staff permissions must distinguish:

- View vs edit.
- Internal vs client-visible content.
- Financial records vs operational records.
- Template editing vs document generation.
- Agency settings vs daily work.
- Global knowledge read vs agency override edit.
- Passenger profile access vs relationship editing.

## Platform Owner Permissions

Platform owner layer controls:

- Agency provisioning.
- Subscription/workspace management.
- Global reference data.
- Global airline knowledge publishing.
- Global feature configuration.
- Global template libraries.
- Review workflows.

Platform users do not own agency client/passenger data and should not edit agency operational records except under explicit support workflows.

## Document Visibility

Every generated or uploaded document needs:

- Owner scope: global template, agency document, client upload, passenger document.
- Visibility: internal-only, staff-visible, client-visible, passenger-visible.
- Associated records: request, offer, booking, ticket, EMD, invoice, refund/exchange, passenger, client.
- Portal visibility flag.
- Download permission.
- Archive state.

Internal-only documents and notes must never appear in portal, public website, or client-facing generated documents.

## Internal vs Client-Visible Data

Internal-only:

- Staff notes.
- Agency commercial agreements.
- PCC/OID/account references.
- Commission and private fare notes.
- Unreviewed policy warnings.
- Support/admin audit details.

Client-visible:

- Approved offer wording.
- Branded documents.
- Itineraries.
- Tickets and EMD receipts.
- Invoices and payment status.
- Requested client tasks.
- Published status updates.

Mixed records should use explicit fields, not inferred visibility.

## Audit Requirements

Audit events should record:

- Actor type and ID.
- Agency ID where applicable.
- Action.
- Record type and ID.
- Timestamp.
- Before/after critical fields where appropriate.
- Support-access reason where platform user accessed tenant data.

## Review Hardening: Missing Permission Decisions

Before database implementation, the permission model must explicitly define:

- Which agency roles can create, edit, archive, merge, or export client and passenger profiles.
- Which agency roles can edit `client_passenger_relationship` permissions and consent status.
- Which agency roles can view, edit, or send client-visible offer wording.
- Which agency roles can view financial fields, private fare notes, markups, commissions, and PCC/OID/account references.
- Which agency roles can issue or mark tickets and EMDs as issued.
- Which agency roles can issue invoices, record payments, reconcile payments, or mark refunds paid.
- Which agency roles can create agency airline overrides and which can publish those overrides into operational use.
- Whether agency readonly users can see internal notes, commercial agreements, and support audit events.
- Whether clients can edit passenger legal identity fields after those fields are attached to active tickets, EMDs, or bookings.
- Whether clients can upload documents for passengers where `can_view` is true but `can_upload_documents` is false. The expected answer is no unless a separate task grants upload permission.
- Whether authorized contacts inherit permissions from a client/passenger relationship or require their own scoped authorization record.

## Review Hardening: Platform Support Access

Platform users do not own agency operational data. Support access must be:

- Time-bounded or case-bounded.
- Reason-coded.
- Audited.
- Read-only by default.
- Explicitly elevated for data correction only under a support policy.
- Excluded from routine platform knowledge editing workflows.

Platform support must not use agency-private commercial data to update global knowledge unless the agency explicitly grants permission and the data passes platform review.

## Review Hardening: Portal Access Rules

- A client account can exist only inside one agency tenant.
- A client profile may exist without portal access.
- Passenger portal access is future/optional and must not be assumed in MVP authorization checks.
- Portal visibility for a record requires all of: active client account, tenant match, relationship permission where passenger data is involved, record-specific visibility, and non-archived document or record status.
- Portal edits should create audit events and may require agency review for legal identity, travel documents, consent, and service-needs fields.
- Internal notes, internal warnings, unreviewed knowledge, commercial agreements, and private fare data are never client-visible.
