# Airline Intelligence Model

## Purpose

The Airline Intelligence layer is a core AeroAssist advantage. It gives small agencies searchable, reviewed, source-backed airline operating knowledge while preserving the role of the human travel agent.

The model must support stable structured domains and flexible new knowledge layers without schema redesign.

## Core Domains

### Airline Identity

- IATA code.
- ICAO code.
- Name.
- Country.
- Alliance.
- Active status.
- Logo/branding.

### Operational Profile

- GDS availability.
- NDC/agent portal availability.
- Website and agent portal links.
- Booking channels.
- Ticketing channel notes.
- Reissue/refund handling notes.
- Payment/settlement notes.

### Airline Contacts

- Medical desk.
- Special assistance.
- Groups.
- Baggage.
- Pet desk.
- Refund/exchange desk.
- Agency support.
- Sales/account manager.
- Escalation contacts.
- Hours, languages, URLs.

### GDS / SSR / OSI Formats

- Service code.
- GDS system.
- SSR format.
- OSI format.
- Free-text requirements.
- Examples.
- Passenger/segment scope.
- Validation notes.
- Airline-specific deviations.

### Special Service Policies

- UMNR / YP.
- PRM / WCHR / WCHS / WCHC / WCOB.
- Medical / MEDIF / oxygen / POC / stretcher.
- PETC / AVIH / SVAN / ESAN.
- EXST / CBBG.
- Sports equipment.
- Musical instruments.
- Weapons/firearms.
- Dangerous goods/batteries.
- Human remains.
- Documents/compliance.

### Products / Fare Families

- Branded fares.
- Cabin products.
- Fare bundle inclusions.
- Baggage.
- Seats.
- Flexibility.
- Refundability.
- Ancillaries.
- Booking class notes.
- Route/cabin applicability.

### Pricing / Ancillary Rules

- Airline service fees.
- Pricing basis.
- Currency.
- Unit.
- Route type.
- Flight type.
- Fare bundle.
- Formula.
- Manual quote flags.
- Client-visible flags.

### EMD / RFIC / RFISC Mapping

- Service code.
- RFIC.
- RFISC.
- Reason for issuance.
- EMD-S / EMD-A / manual.
- Source.
- Airline-specific override.
- Manual review requirements.

### Distribution / Manual Procedures

- GDS process.
- Portal process.
- Phone/email process.
- Documents required.
- Expected SLA.
- Escalation path.
- Credential requirement reference.

### Agreements

- Global or agency-specific agreement.
- PCC/OID/account reference.
- Commission, markup, private fare notes.
- Waiver rules.
- Validity.
- Confidentiality.
- Internal-only status.

## Flexible Knowledge Layer

`airline_knowledge_item` is the extensibility model for new policy, product, commercial, and operational domains.

Required fields:

- `airline_id`
- `knowledge_domain`
- `knowledge_layer`
- `topic`
- `service_code` optional
- `product_code` optional
- `applicability`
- `structured_data`
- `source`
- `version`
- `effective_from`
- `effective_to`
- `review_status`
- `agency_visibility`
- `agency_override_rules`

Examples supported without schema redesign:

- Airline starts offering a new onboard product.
- Airline changes PETC SSR text requirements.
- Airline changes PSS and now requires a reissue tax as EMD-S with RFISC 997.
- Airline creates a new medical desk portal.
- Airline changes branded fare baggage logic.

## Source, Review, And Version Model

Every knowledge record must include:

- Source type.
- Source URL, document, reference text, or internal evidence.
- Captured by.
- Reviewed by.
- Confidence.
- Effective date.
- Last reviewed date.
- Next review date.
- Review status.
- Version.
- Published-to-agencies status.

Suggested review statuses:

- `draft`
- `needs_review`
- `approved`
- `published`
- `deprecated`
- `superseded`
- `rejected`

Published knowledge is immutable by version. Corrections create a new version.

## Agency Override Model

Agencies may add private or agency-specific knowledge for:

- Contacts.
- Commercial agreements.
- PCC/OID/account references.
- Private fare, commission, markup, and waiver notes.
- Local operating procedures.
- Internal notes.
- Pricing or document handling rules.

Agency overrides must:

- Be scoped by `agency_id`.
- Never mutate global records.
- Declare whether they replace, augment, or annotate global knowledge.
- Carry their own source/review metadata where appropriate.
- Be excluded from other agencies.
- Be excluded from client-visible outputs unless explicitly allowed.

## Consumption By Requests

Requests may use airline intelligence to provide:

- Relevant airline search.
- Policy hints.
- Missing data prompts.
- Required document checklists.
- Feasibility warnings.
- Suggested contacts/procedures.

Requests remain valid without evaluation.

## Consumption By Offers

Offers may use airline intelligence to support:

- Special service feasibility summaries.
- Ancillary price guidance.
- EMD readiness hints.
- Fare bundle explanation.
- Baggage and flexibility notes.
- Warnings for manual review.
- Client-visible service support explanations.

When an offer is sent or accepted, relevant knowledge is snapshotted.

## Consumption By Bookings, Tickets, And EMDs

Bookings may use airline intelligence to support:

- SSR/OSI formatting.
- Service confirmation tracking.
- Contacts and escalation paths.
- Required document handling.
- EMD/RFIC/RFISC mapping.
- Refund/exchange procedures.

Ticket, EMD, invoice, refund, and exchange milestones must snapshot the knowledge used for audit and historical accuracy.

## Visibility Rules

- Global published knowledge is readable by subscribed agencies.
- Draft and review knowledge is platform-only.
- Agency overrides are visible only to that agency.
- Confidential agreements are internal-only by default.
- Client-visible wording must be explicitly marked or generated from approved fields.
- Internal warnings must not leak into portal or public documents.

## Review Hardening: Override Precedence

When global knowledge and agency-specific knowledge both exist, resolution must be deterministic:

1. Start with the latest published global version available to the agency.
2. Apply agency overrides that are active, in-date, and scoped to the same airline/domain/layer/topic/applicability.
3. Interpret override mode:
   - `replace`: agency value supersedes the matching global field or record for that agency only.
   - `augment`: agency value adds local context without hiding the global value.
   - `annotate`: agency value adds internal notes or warnings without changing operational guidance.
4. Exclude expired, draft, rejected, or unpublished agency overrides from operational recommendations.
5. Preserve both global version IDs and agency override version IDs in operational snapshots.

Conflict handling:

- New global versions must not overwrite agency overrides.
- If a new global version conflicts with an active agency override, create an agency review flag.
- If an agency override conflicts with a mandatory platform safety warning, the platform warning must remain visible to staff.
- Client-visible wording must be generated only from approved global fields or explicitly client-visible agency override fields.

## Review Hardening: Knowledge Ownership Guardrails

- Airline identity, reference data, service taxonomy, RFIC/RFISC base tables, and globally published policy/procedure knowledge belong to AeroAssist.
- Agency agreements, PCC/OID/account references, private contacts, commission notes, private fare notes, markups, waiver notes, and agency internal procedures belong to the agency.
- Agency-owned knowledge can reference global airline records but must not be embedded into global records.
- Platform editors may promote generalized learnings from agency-owned knowledge only through a new reviewed global source/version record.

## Review Hardening: Flexible Layer Governance

The flexible `airline_knowledge_item` model should not become unstructured free text. Before implementation, define controlled vocabularies for:

- `knowledge_domain`
- `knowledge_layer`
- `topic`
- `applicability`
- `agency_visibility`
- `review_status`
- override mode

`structured_data` must be validated by a schema selected from domain/layer metadata where possible. Truly new layers may begin with a generic schema, but platform review should decide whether a reusable schema is needed before broad publishing.
