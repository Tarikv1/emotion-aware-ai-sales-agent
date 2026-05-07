# RAG-014 Source-Mapped Quote Follow-Up Design

## Purpose

RAG-014 clears the `5` quote-clearance follow-ups created by RAG-012 accepted source mappings. It converts safe candidates into project-owned paraphrased rules, rejects unsafe pressure/control guidance, and keeps runtime retrieval disabled.

## Design

RAG-014 reads:

- `RAG-013` cleanup strategy
- `RAG-009` all-source review coverage
- a small RAG-014 case/config file listing accepted and rejected follow-up chunk IDs

It emits one review artifact with:

- `4` accepted project-owned paraphrases
- `1` rejected pressure/control candidate
- `0` source-mapped quote follow-ups remaining after review
- a Markdown report documenting the accepted rules, rejected item, and boundaries

The accepted rules are vertical-agnostic sales-agent guidance:

- neutral pain reflection as a clarification question
- consent-based meeting/callback confirmation
- low-pressure cost-of-inaction check
- validation of prior customer investment before comparing future tradeoffs

The rejected candidate is fixed rep talk-time dominance because it optimizes control over listening and does not fit the reusable sales-agent core.

## Boundaries

- Runtime retrieval remains disabled.
- Chunk import remains disabled.
- No chunks are auto-promoted.
- No source excerpt text is stored.
- No provider or NotebookLM API calls are made.
- No private customer data is read.
- The artifact records review decisions only; runtime admission still requires a later gate.

## Success Criteria

- Official output reports `followup_candidate_count: 5`.
- Official output reports `accepted_followup_count: 4`.
- Official output reports `rejected_followup_count: 1`.
- Official output reports `source_mapped_quote_followups_remaining_after_review: 0`.
- Official output keeps runtime retrieval, chunk import, provider calls, private-data use, and auto-promotion disabled.
- Setup, command map, roadmap, and methodology docs include RAG-014.
