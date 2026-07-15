# Journey Segment Authoring And Intelligent Import Workspace Foundation

## Purpose

Phase 56.1 turns the Phase 56.0 canonical Journey representation into a practical agent authoring workflow. An agency user can preserve pasted or linked source material, translate existing GDS parser and Booking Import output into editable segment drafts, correct only uncertain fields, enrich known reference labels, validate chronology, and explicitly apply the result to canonical Journey options.

This is a governed preparation layer. It is not live schedule search, pricing, booking, ticketing, provider execution, AI parsing, or publication.

## Source-Of-Truth Boundary

Phase 56.1 does not create another Journey, itinerary option, leg, connection, or operational segment family. `JourneySegmentDraft` exists only before application. The application service delegates final records to `CanonicalJourneyItineraryService`, which writes the Phase 56.0 Journey collections and keeps source references.

Request, Trip, Offer, Booking, Ticket, EMD, Passenger, Flight Workspace, accepted offer snapshots, booking snapshots, ticket coupons, and imported provider/source records remain authoritative in their existing domains. Authoring application never mutates those records.

## Raw, Normalized, And Confirmed Data

The workspace separates three states:

1. `JourneyImportSource` retains original text or a linked-record snapshot, source label/type, parser and Booking Import references, importing actor, timestamp, and a deterministic SHA-256 hash. Raw content has no update or delete route.
2. `JourneySegmentDraft` retains editable normalized fields, explicit unknowns, confidence, schedule calculations, completeness, and review state.
3. `JourneyFieldProvenance` and `JourneyAuthoringCorrection` retain field-level imported, normalized, enriched, agent-confirmed, rejected, and overridden history.

Restricted source metadata is omitted from agency responses. Platform diagnostics omit raw source bodies and do not expose cross-agency editing.

## Session Lifecycle

`draft` -> `imported` -> `normalized` -> `requires_review` or `ready_to_apply` -> `applied`.

`partially_applied` remains available for future governed workflows. Archive operations are non-destructive. Draft segment archive and restore preserve correction history; source records are immutable.

## Parser And Booking Import Integration

Pasted text is first delegated to the existing `GdsParserService`. Parser-run and Booking Import Draft imports adapt their stored normalized previews and parsed entities rather than reimplementing those subsystems. A deliberately small deterministic recognizer covers common unresolved airline-segment lines, including compact carrier/flight/date/route/time forms. Unrecognized lines are retained in source metadata for manual review and are never silently discarded.

Parser runs store an input excerpt by design. Importing an existing parser run therefore labels that limitation explicitly. Booking Import Draft integration preserves the full raw draft text where available.

## Reference Enrichment

Enrichment reads governed internal airport and airline reference records only. It may fill blank airport names, city/country/timezone metadata, or carrier names where the reference record supplies them. It records the reference id and provenance for every changed field.

Precedence is agent-confirmed value, explicit structured import, governed internal reference enrichment, deterministic normalized pattern, then unknown. Enrichment never overwrites the latest agent-confirmed or agent-overridden field. It makes no internet, provider, scraper, or AI call.

## Deterministic Calculations

Local timestamps require either an explicit IANA timezone or an already timezone-aware value. The service never assumes that a naive local timestamp is UTC. Only resolvable timezone-aware pairs produce UTC values and scheduled duration.

The workspace calculates:

- segment duration and local calendar-day offset;
- overnight/date-change indicators;
- adjacent connection duration;
- option and leg grouping previews;
- codeshare indicators from explicit marketing/operating carrier differences;
- deterministic completeness from documented field weights.

No legal minimum connection time is asserted. Connection notices use neutral manual-review wording.

## Validation

Persistent validation records cover required flight fields, code formats, explicit timezone requirements, arrival-before-departure, segment overlap, negative/short/long connections, duplicate signatures, sequence gaps, overnight connections, terminal changes, origin/destination discontinuities, surface gaps, same-flight-number continuation, codeshare, and interline review.

Each validation has severity, category, field links, blocking state, resolution metadata, and supersession history. Running validation supersedes prior active findings but does not delete them. Completeness and a clean validation result are preparation signals, not operational approval.

## Applying To Canonical Journey

Application supports a new Journey, a new option, append/update of an editable option, and replacement of a draft option. Replacement is non-destructive: old option and segment projections become superseded. The service records an application hash, source draft ids, created/replaced canonical record ids, actor, warnings, and mode.

Any existing target with a finalized or immutable Journey snapshot is rejected. Applying never edits a snapshot and never creates or publishes a client snapshot automatically.

## Agency And Platform Interfaces

- Agency API: `/api/agencies/{agency_id}/journey-authoring`
- Platform diagnostics API: `/api/platform/journey-authoring`
- Agency workspace: `/agency/journey-authoring`
- Platform diagnostics: `/platform/journey-authoring`

Agency mutations use existing agency access and role checks. Platform routes are authenticated, governance-oriented, and read-only.

The agency workspace provides preserved source inspection, paste-and-parse, optimized manual flight entry, an editable schedule grid, bulk cabin updates, reordering, archive/restore, timeline and connection previews, grouped validation, provenance, correction history, and explicit preview/apply actions.

## Intentionally Disabled

Phase 56.1 does not perform live schedule or availability lookup, live pricing, provider/GDS/NDC execution, scraping, external API calls, AI inference, booking, ticketing, background work, automatic publication, or production seeding. It does not invent terminal, aircraft, operating-carrier, baggage, fare, service confirmation, or ticket status data.

## Known Limitations

- The fallback recognizer is intentionally narrow and leaves difficult text for manual review.
- Timezone enrichment depends on existing governed airport reference data.
- MCT legality and through-service guarantees remain unknown without a governed source.
- Parser-run imports can preserve only the excerpt retained by the existing parser unless a linked Booking Import Draft supplies full raw text.
- Application creates presentation projections; it does not change canonical operational source records.
