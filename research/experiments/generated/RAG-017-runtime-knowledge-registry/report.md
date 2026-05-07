# RAG-017 Runtime Knowledge Registry

RAG-017 creates a local opt-in registry from already accepted project-owned RAG slices. Runtime retrieval is disabled by default.

## Summary

- Registry items: `59`
- Voice-delivery advisory items: `30`
- Runtime retrieval enabled by default: `False`
- Source-mapping blocker chunks excluded: `58`
- Source-mapping blocker groups excluded: `43`
- Latent quote follow-ups excluded: `21`

## Included Artifacts

- `RAG-007-reviewed-first-slice`
- `RAG-010-reviewed-expansion-slice`
- `RAG-012-accepted-cleanup`
- `RAG-014-source-mapped-quote-followup`
- `RAG-016A-quote-clearance-decision-slice`
- `RAG-016B-voice-delivery-quote-clearance-decision-slice`

## Runtime Boundary

- Registry lookup is deterministic keyword matching only.
- No external vector DB, embedding provider, provider call, NotebookLM API call, or private-data read is used.
- Runtime use requires explicit opt-in from the guarded response path.
- Retrieved items remain advisory-only and cannot alter protected text.

## Exclusions

- Unresolved source-mapping blockers stay out of the registry.
- Latent quote follow-ups stay out of the registry.
- Source excerpt text is not stored.
