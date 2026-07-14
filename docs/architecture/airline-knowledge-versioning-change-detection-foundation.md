# Airline Knowledge Versioning And Change Detection Foundation

Phase 55.3 adds deterministic, field-level versioning for canonical airline operational knowledge. It answers what changed, when, which evidence caused it, which published release contains it, what operational records may rely on it, and whether QA or publication review is required.

## Canonical Boundary

Phase 55.3 reuses the Phase 50.4 `airline_knowledge_versions` governance envelope. It does not create another version lifecycle. Phase 39.2 `airline_intelligence_knowledge_versions` remains the staging and release-channel history for reviewed data packs. Phase 55.2 evidence records remain the canonical source and assertion provenance.

The additional collections are:

- `airline_knowledge_version_items`: immutable snapshots of canonical knowledge objects.
- `airline_knowledge_change_sets`: deterministic comparisons between two canonical knowledge versions.
- `airline_knowledge_field_changes`: machine-readable and human-readable scalar, nested, list, rule, formula, effective-date, evidence, and severity differences.
- `airline_knowledge_impact_assessments`: potential downstream dependencies that require human review.
- `airline_knowledge_change_reviews`: human governance decisions about a detected change.
- `airline_knowledge_revalidation_requests`: explicit re-QA and republish obligations.

## Versioned Objects

The registry supports airline profiles, visual/structured policies, operational rules, pricing formulas, capability rows, evidence assertions, service instructions, SSR/OSI templates, EMD/RFIC/RFISC rules, distribution capabilities, contacts, service desks, and published knowledge packages. Each item is captured from its existing canonical collection. Arbitrary collection access and caller-supplied replacement snapshots are not supported.

Each version item stores a JSON snapshot and SHA-256 checksum. There is no item update or delete API. Later envelope reviews, release links, and change-set links cannot rewrite the historical object snapshot.

## Structured Change Detection

Comparison is recursive and deterministic:

- scalar values produce modified field changes;
- nested objects are compared by field path;
- lists record additions and removals, and object lists use stable references or codes where available;
- conditions, restrictions, formulas, messages, effective dates, evidence, contacts, and distribution fields receive semantic categories;
- numeric price and restriction changes receive directional categories;
- every difference includes before/after types, values, operation, category, severity, human explanation, and machine diff metadata.

Change categories are `added`, `modified`, `removed`, `superseded`, `effective_date_change`, `restriction_increased`, `restriction_reduced`, `pricing_increase`, `pricing_decrease`, `support_status_change`, `document_requirement_change`, `approval_requirement_change`, `distribution_change`, `contact_change`, and `evidence_only_change`.

## Impact And Revalidation

Potential impact is detected through exact version, evidence, release, and knowledge-object references plus airline, service, and route context. Targets include published releases, scenario tests, policy comparisons, recommendations, active offers, booking-readiness packages, passenger-service cases, agency knowledge assignments, future trips, and unresolved after-sales cases.

An impact assessment is advisory. It never updates a target record or mutable source. Historical accepted-offer, recommendation, booking, trip, and publication snapshots remain unchanged. Material changes create explicit re-QA requests. Changes affecting published or effective versions create explicit republish requests. Neither request runs automatically.

## Routes And Visibility

Platform APIs use `/api/platform/knowledge-versions`; the platform UI uses `/platform/knowledge-versions`. Platform knowledge roles can capture versions, compare them, review change sets, and update revalidation metadata.

Agency APIs use `/api/agencies/{agency_id}/knowledge-updates`; the agency UI uses `/agency/knowledge-updates`. Agency routes are read-only and return only published or effective updates for global or tenant-owned scope. They omit immutable snapshots, machine diffs, internal notes, reviewer metadata, and unpublished source details.

## Safety

Phase 55.3 does not mutate historical snapshots, automatically update operational records, rerun recommendations, alter accepted offers, publish, rollback, call providers, use AI, schedule workers, or execute airline rules. Unknown references remain review conditions rather than runtime failures.
