# RAG-015 Source-Mapping Batches Design

## Purpose

RAG-015 organizes the remaining source-mapping cleanup work after RAG-014. It does not accept source mappings, create new source records, promote chunks, import chunks, or enable runtime retrieval.

Adding more source material later remains feasible because the project already has a repeatable intake path through RAG-001/RAG-002 imports and RAG-003+ refresh/review gates. RAG-015 therefore proceeds with the current corpus instead of pausing for new resource gathering.

## Design

RAG-015 reads:

- `RAG-014` source-mapped quote follow-up review
- `RAG-013` cleanup strategy
- `RAG-006` chunk review packet
- `RAG-009` all-source review coverage
- a small RAG-015 case/config file

It emits one batch artifact with:

- all `58` remaining source-mapping chunks
- all `43` remaining source-title groups
- four priority batches:
  - high-impact groups with `3+` chunks
  - medium groups with `2` chunks
  - singleton groups with candidate source suggestions
  - singleton groups without candidate source suggestions
- latent quote-follow-up counts for chunks likely to need quote clearance after source mapping
- no source-mapping decisions applied

## Boundaries

- Runtime retrieval remains disabled.
- Chunk import remains disabled.
- No chunks are auto-promoted.
- No source mappings are accepted by RAG-015.
- No source excerpt text is stored.
- No provider or NotebookLM API calls are made.
- No private customer data is read.

## Success Criteria

- Official output reports `source_mapping_group_count: 43`.
- Official output reports `source_mapping_chunk_count: 58`.
- Official output reports `high_impact_group_count: 3`.
- Official output reports `medium_group_count: 6`.
- Official output reports `singleton_group_count: 34`.
- Official output reports `latent_quote_followup_after_source_mapping: 21`.
- Official output keeps runtime retrieval, chunk import, provider calls, private-data use, and auto-promotion disabled.
- Setup, command map, roadmap, and methodology docs include RAG-015.
