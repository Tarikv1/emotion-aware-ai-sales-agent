# RAG-013 Cleanup Strategy Design

## Purpose

RAG-013 chooses the cleanup strategy after RAG-012. It does not resolve additional blockers, promote chunks, import chunks, build embeddings, or enable runtime retrieval.

## Design

RAG-013 reads:

- `RAG-012` accepted cleanup
- `RAG-009` all-source review coverage
- `RAG-006` chunk review packet
- a small RAG-013 case/config file

It emits one strategy artifact with:

- the `5` quote-clearance follow-ups created by accepted source mappings
- the remaining `58` source-mapping chunks grouped into source-title review batches
- the remaining `30` original quote-clearance chunks grouped by review lane
- a recommended cleanup order before any runtime integration work

Recommended order:

1. `RAG-014`: clear or reject the `5` quote follow-ups from RAG-012 accepted source mappings.
2. `RAG-015`: batch the remaining source-mapping groups, starting with larger groups because one reviewed source decision can unlock multiple chunks.
3. `RAG-016`: batch the remaining quote-clearance rewrites by lane, keeping voice/prosody advisory-only and persuasion guidance low-pressure.
4. `RAG-017`: run a clean-candidate re-audit before any runtime-off retrieval harness.

## Boundaries

- Runtime retrieval remains disabled.
- Chunk import remains disabled.
- No chunks are auto-promoted.
- No blockers are resolved by RAG-013 itself.
- No source excerpt text is stored.
- No provider or NotebookLM API calls are made.
- No private customer data is read.

## Success Criteria

- Official output reports `remaining_source_mapping_chunk_count: 58`.
- Official output reports `remaining_original_quote_clearance_count: 30`.
- Official output reports `quote_follow_up_from_accepted_source_mappings: 5`.
- Official output reports `known_cleanup_work_count_before_runtime: 93`.
- Official output recommends `RAG-014-source-mapped-quote-followup` as the next checkpoint.
- Setup, command map, roadmap, and methodology docs include RAG-013.
