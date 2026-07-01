# Airline Policy Ingestion Foundation

Phase 36.7 adds a governed foundation for airline-specific policy text. It is designed for pasted or uploaded policy material that platform owners or agencies can review before it becomes approved policy knowledge.

## Flow

Policy text is stored as an `AirlinePolicySource`, split into `AirlinePolicySection` records, processed by a deterministic `AirlinePolicyExtractionRun`, and normalized into candidate rows. Candidates are not authoritative until a human reviews them. Explicit platform promotion creates `AirlinePolicyApprovedKnowledgeRecord` rows.

## Source Records

`AirlinePolicySource` stores raw policy text, source title/type/date/url metadata, airline snapshots, service domain/family, hash, warnings, confidence, scope, and ingestion status. Sources can be platform-owned or agency-local.

## Section Detection

`AirlinePolicySection` stores detected sections such as applicability, pricing, how-to-book, SSR/OSI, EMD/payment, exceptions, documents, changes/refunds, and other text blocks. Detection is heuristic and conservative; unclear sectioning is flagged with warnings.

## Extraction Runs

`AirlinePolicyExtractionRun` records extractor version, status, confidence, warnings/errors, summary metadata, and counts for extracted rules, prices, communication candidates, EMD rules, exceptions, and distribution hints.

## Candidate Records

- `AirlinePolicyExtractedRule` stores applicability, age, deadline, route/connection, document, operational, change/refund, and other rule candidates.
- `AirlinePolicyExtractedPrice` stores currency/amount, mandatory/optional flags, price basis, route/direct-connecting hints, and EMD fee signals.
- `AirlinePolicyExtractedCommunicationRule` stores SSR/OSI/OTHS/GDS/NDC/manual-contact candidates with codes, provider family hints, templates, examples, and confirmation hints.
- `AirlinePolicyExtractedEmdRule` stores EMD required/fare-included hints, EMD-A/EMD-S, RFIC/RFISC, service subcode, ASVC, ICW ticket/coupon, lifecycle, channel, and GDS example signals.
- `AirlinePolicyExtractedException` stores embargoes, route/airport/connection blocks, train/bus/overnight restrictions, country/document triggers, partner-airline limitations, and manual-review triggers.

Every candidate stores a source excerpt, confidence, status, and optional correction payload.

## Review And Promotion

`AirlinePolicyReviewCorrection` records accept/correct/reject/promote/archive/add-missing actions with before/after payloads and reasons. Platform promotion is explicit through policy ingestion endpoints and creates `AirlinePolicyApprovedKnowledgeRecord` rows. Agency sources can be reviewed locally and submitted for platform review, but agency submission does not create global approved knowledge automatically.

## Rules And Services Relationship

Phase 36.7 does not replace `AirlineRulesCore`, `UnifiedExceptionRule`, service catalogue mappings, SSR/OSI generation, or the exception engine. Approved policy knowledge is a governed source-backed foundation that later phases can promote into canonical taxonomy, comparison, pricing, SSR/OSI, EMD, and exception structures.

## Document Integration

Document context supports `airline_policy_source`, `airline_policy_extraction_run`, and `airline_policy_approved_knowledge`. Default document templates `airline_policy_extraction_summary` and `airline_policy_review_summary` summarize source metadata, detected sections, candidate counts, warnings, corrections, and approved knowledge records.

## Boundaries

- No external AI policy extraction.
- No airline scraping.
- No live GDS/NDC/provider calls.
- No automatic global promotion.
- No full airline comparison matrix.
- No full SSR/OSI/EMD rules engine replacement.
- No payment, ticketing, EMD issuance, exchange, refund, void, BSP/ARC, accounting, or settlement execution.
- No `/agent` or `/admin` route roots.
