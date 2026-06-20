# Open Questions

## Product Decisions

- Should agencies support multiple workspaces under one agency account in MVP, or exactly one workspace per agency?
- Should client self-registration create an active portal account immediately, or require staff approval first?
- Should passenger self-registration be supported in MVP, or only client-managed passenger profiles?
- Should the platform support organization/company clients in MVP, or start with person clients plus company fields?
- How much public website publishing is required at launch: hosted subdomain, custom domains, or both?
- Should portal payments be view-only in MVP, or should online payment collection be included?
- Should document generation begin with fixed templates only, or allow limited agency-editable content blocks in MVP?
- Which airline knowledge domains are required for launch coverage?

## Assumptions Made

- One agency has one primary workspace in MVP.
- Passenger profiles are scoped to an agency workspace, not globally shared across agencies.
- Client/passenger relationships are the primary access control mechanism for portal passenger data.
- Global airline knowledge is versioned and published by AeroAssist.
- Agency overrides layer over global knowledge and do not modify global records.
- Offers are manually constructed by staff from external research.
- Requests are useful but not mandatory for offers.
- Client portal starts as responsive web, not native app.
- The first website/CMS is controlled template configuration, not a freeform builder.

## Data Model Risks

- Passenger duplication across clients and agencies can become messy without merge/review tools.
- Relationship permissions can become hard to reason about if authorization, consent, and portal access are not clearly separated.
- Flexible airline knowledge items need governance or they may become inconsistent freeform data.
- Snapshot payloads can grow large if not carefully normalized and version-linked.
- Agency overrides may conflict with global updates and need review workflows.
- Financial tracking may drift toward accounting requirements if scope is not controlled.

## Implementation Risks

- Tenant isolation must be designed early and tested aggressively.
- Client-visible vs internal-only fields need explicit modeling to avoid data leaks.
- Offer builder complexity can expand quickly if fare search automation is allowed to creep into MVP.
- Document generation can become a full template product if MVP boundaries are loose.
- Website/CMS customization can absorb too much build time if not constrained.
- Airline intelligence review workflows need operational ownership, not only software support.
- Portal permissions should be tested with realistic family, company, assistant, VIP, and child scenarios.

## Validation Needed With Early Agencies

- Most common request types.
- Most common special services.
- Required launch document types.
- Typical invoice/payment practices.
- Preferred offer comparison format.
- Minimum acceptable airline intelligence coverage.
- Whether agency websites need custom domains for launch.
- Whether WhatsApp/email summaries should be first-class records in MVP.

## Must Resolve Before Database Implementation

- Final status enums for request, offer, offer client action, booking, booking segment, service confirmation, ticket, EMD, invoice, payment, refund/exchange case, generated document, message thread, task, and knowledge review.
- Whether `client_profile` represents both people and organizations in one table or separates person and organization profiles.
- Whether `client_account` can have a verification-pending state, or whether pending verification is represented by invitation/review fields while status remains one of the canonical values.
- Whether multiple client users can log in for one organization client in MVP.
- Whether passenger profiles can be merged inside an agency and what audit rules govern merges.
- Whether legal identity and document fields require approval after client portal edits.
- Whether portal self-registration can create passenger relationships without staff approval.
- Exact uniqueness rules for passenger documents, ticket numbers, EMD numbers, invoice numbers, and PNR references.
- Whether invoices can exist without bookings in MVP.
- Whether payments can be unapplied, partially applied, split across invoices, or multi-currency in MVP.
- Whether refund and exchange should be one combined case model or separate models with shared financial adjustment lines.
- Exact document storage policy, retention policy, and deletion/archive behavior for sensitive passenger documents.
- Exact override precedence rules for agency airline overrides across replace, augment, and annotate modes.
- Minimum launch schema for flexible airline `structured_data` by domain/layer.
- Tenant isolation enforcement strategy and test approach.
- Platform support access policy, including whether support can edit tenant records.
- Which first build phase is the committed MVP slice: full listed MVP or the narrower tenant plus CRM plus request plus offer plus fixed document vertical slice.
