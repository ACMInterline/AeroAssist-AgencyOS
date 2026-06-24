# Reference Enrichment Import Packs

Phase 34.3 starter CSV templates for platform-owner reference enrichment imports.

These files are intentionally small examples, not a complete global dataset. Use `/platform/reference` → `Enrichment Packs` to dry-run and commit imports safely.

Default behavior is non-destructive: dry-run first, then commit with `insert_only` or `update_missing_only` unless a platform owner intentionally selects a broader update mode.
