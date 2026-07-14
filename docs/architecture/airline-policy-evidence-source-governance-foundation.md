# Airline Policy Evidence And Source Governance Foundation

Phase 55.2 adds the canonical provenance and evidence-governance layer for airline policy, pricing, operational rules, capability, restrictions, procedures, distribution, contacts, and published knowledge.

## Ownership Boundary

Existing `airline_policy_sources`, `airline_knowledge_acquisitions`, and `airline_knowledge_sources` continue to own raw captured source truth. `AirlineEvidenceSource` can point to one of those records with `raw_source_collection` and `raw_source_record_id`; it does not copy, rewrite, or replace the original source.

Phase 55.2 owns governance metadata around that truth:

- `AirlineEvidenceSource` records source identity, authority, dates, status, access, supersession, and review metadata.
- `AirlineEvidenceArtifact` registers screenshot, PDF/manual, structured import, API response, and other artifact metadata without performing upload, extraction, or provider access.
- `AirlineEvidenceAssertion` stores a structured assertion separately from its source and artifact.
- `AirlineEvidenceLink` connects an assertion to a profile field, policy, pricing formula, operational rule, capability row, distribution/PSS/GDS fact, interline/codeshare rule, contact, knowledge item, or publication.
- `AirlineEvidenceReview` records human review decisions.
- `AirlineEvidenceConflict` preserves disagreeing source and assertion ids, values, channel/route context, status, accepted variants, and resolution metadata.
- `AirlineEvidenceFreshnessAssessment` records deterministic fresh, due-soon, overdue, stale, expired, superseded, or unknown status.
- `AirlineEvidenceAccessClassification` controls agency, client, attachment, and internal visibility.

## Source Types And Authority

The source registry supports airline websites, conditions of carriage, tariffs, agent manuals, GDS help and cryptic responses, operational bulletins, trade communications, airline emails and support-desk responses, airport handling responses, operational observations, historical cases, regulator/government sources, IATA/industry publications, supplier/consolidator instructions, screenshots, PDF/manuals, structured imports, and API responses.

Authority is assessed deterministically from source type or an explicitly reviewed authority level. Confidence combines authority with checksums, effective dates, review decisions, and supersession state. Unknown authority remains explicit and produces low confidence rather than a failure.

## Conflict Governance

Assertions with the same airline and assertion key but different structured values create conflict records. Conflict type distinguishes limit, support-status, effective-date, distribution-channel, route-specific, and general assertion differences.

Conflict statuses are `detected`, `under_review`, `accepted_variant`, `superseded`, `unresolved`, `resolved`, and `archived`. Resolution changes the conflict metadata and adds a review record. It never deletes either source or assertion. A newer source may supersede an older source, but both remain available in history.

## Visibility And Security

Platform governance APIs use `/api/platform/airline-evidence`. Platform knowledge roles can register and update source metadata, artifacts, assertions, links, access classifications, freshness assessments, supersession, and conflict decisions.

Agency APIs use `/api/agencies/{agency_id}/airline-evidence` and are read-only. A source is visible only when it is approved, published, or verified; belongs to the requesting agency or is global; and has agency-visible access. Agency responses remove source URLs, raw-source locations, storage references, checksums, internal notes, reviewer information, conflict values, and restricted attachments.

UI routes are `/platform/airline-evidence` and `/agency/airline-evidence`.

## Unsupported Knowledge And Evidence Traces

The service inspects canonical knowledge targets and reports records with no active Phase 55.2 evidence link as `unsupported` and `manual_review_required`. Evidence traces return source, assertion, link, conflict, and freshness metadata for a target. An incomplete trace or unresolved conflict remains a manual-review condition.

## Safety

- Raw and normalized records remain separate.
- Conflicting source truth is retained.
- Physical evidence deletion is disabled; archive and supersede are metadata transitions.
- No scraping, automatic extraction, AI, external API call, provider execution, background job, automatic publication, or production seed is introduced.
- Evidence supports advisory human decisions; it does not execute or enforce airline policy.
