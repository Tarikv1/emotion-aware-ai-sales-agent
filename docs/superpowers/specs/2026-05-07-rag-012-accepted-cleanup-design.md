# RAG-012 Accepted Cleanup Design

## Purpose

RAG-012 applies the human-accepted first cleanup slice from RAG-011 without enabling runtime retrieval. The checkpoint records accepted source mappings for the three high-confidence proposal groups and accepted project-owned paraphrases for the twelve quote-clearance cards.

## Design

RAG-012 reads the existing RAG-011 blocker cleanup packet and RAG-009 all-source coverage artifact. It creates a new review artifact rather than rewriting RAG-009, RAG-011, RAG-005, or runtime memory. The artifact has two reviewed sections:

- `accepted_source_mappings`: the five chunks from the three RAG-011 source-mapping proposal groups, with candidate source IDs accepted by human review.
- `accepted_quote_clearance_items`: twelve project-owned wording rules derived from the RAG-011 quote-clearance cards, each with a safe application, a do-not-use guardrail, and a `runtime_eligible_now: false` boundary.

The quote-clearance rewrites keep the project vertical-agnostic. Behavioral-economics and persuasion items are reframed as ethical, low-pressure sales guidance or guardrails. Voice/prosody items remain advisory-only and cannot infer hidden emotion, protected traits, consent, refusal, urgency, or buying intent.

## Boundaries

- Runtime retrieval remains disabled.
- Chunk import remains disabled.
- No chunks are auto-promoted.
- No source excerpt text is stored.
- No provider or NotebookLM API calls are made.
- No private customer data is read.
- Accepted cleanup reduces review blockers only inside the RAG-012 artifact.

## Success Criteria

- The official artifact reports `17` accepted cleanup decisions: `5` source-mapping chunks and `12` quote-clearance rewrites.
- It reports `source_mapping_blockers_remaining_after_acceptance: 58` and `quote_clearance_blockers_remaining_after_acceptance: 30` for the original RAG-011 quote-clearance queue.
- It reports that `5` accepted source-mapping chunks still need quote-clearance follow-up before any future promotion.
- It records `blockers_resolved_in_prior_artifacts: 0` so older artifacts are not presented as mutated.
- All runtime, provider, private-data, and source-excerpt flags remain false.
- The setup checker, command map, product doc, roadmap, and methodology log include RAG-012.
