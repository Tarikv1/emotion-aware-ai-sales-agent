# RAG-014 Source-Mapped Quote Follow-Up

RAG-014 reviews the quote-clearance follow-ups created by RAG-012 accepted source mappings. It records `5 follow-up candidates`, `4 accepted project-owned paraphrases`, `1 rejected pressure/control candidate`, and `0` source-mapped quote follow-ups remaining after review.

Runtime retrieval remains disabled.

## Command

Run from the repo root:

```powershell
python scripts\run_rag_014_source_mapped_quote_followup.py
```

Default output folder:

```text
research\experiments\generated\RAG-014-source-mapped-quote-followup\
```

Validate the checkpoint:

```powershell
python scripts\validate_rag_014_source_mapped_quote_followup.py
```

## Inputs

- `research/experiments/generated/RAG-013-cleanup-strategy/result.json`
- `research/experiments/generated/RAG-009-all-source-review-coverage/result.json`
- `research/experiments/cases/rag-014-source-mapped-quote-followup.json`

## Accepted Rules

| Knowledge ID | Source chunk | Rule |
| --- | --- | --- |
| `rag014-response-neutral-pain-reflection` | `rag005-chunk-003` | When a customer names a problem, reflect one short neutral phrase back as a clarification question before moving deeper. |
| `rag014-response-consent-based-schedule-confirmation` | `rag005-chunk-006` | After a customer voluntarily agrees to a meeting or callback, confirm the date, time, channel, and expected next step in one concise check. |
| `rag014-response-cost-of-inaction-check` | `rag005-chunk-081` | When a customer has confirmed a problem and prefers to wait, ask neutrally whether keeping the current path has a cost worth considering. |
| `rag014-response-validate-prior-investment` | `rag005-chunk-084` | Validate the customer's prior effort before comparing future tradeoffs. |

These are review-only, vertical-agnostic response-wording rules. They are not imported into runtime retrieval.

## Rejected Candidate

`rag005-chunk-005` was rejected as `rejected_pressure_or_control_tactic`. Fixed rep talk-time dominance optimizes control over listening and does not fit a low-pressure, vertical-agnostic sales-agent core.

Replacement guidance: favor customer-led listening, concise answers, and campaign-stage-specific discovery instead of a fixed agent talk-time target.

## Official Counts

- Follow-up candidates reviewed: `5`
- Accepted project-owned paraphrases: `4`
- Rejected follow-up candidates: `1`
- Source-mapped quote follow-ups remaining: `0`
- Cleanup decisions applied now: `5`
- Auto-promoted chunks: `0`
- Runtime retrieval enabled: `false`
- Chunk import enabled: `false`
- Provider calls made: `false`
- NotebookLM API used: `false`
- Private customer data used: `false`

## Boundaries

- Runtime retrieval remains disabled.
- Chunk import remains disabled.
- No chunks are auto-promoted.
- No provider or NotebookLM API calls are made.
- No private customer data is used.
- No source excerpt text is stored.
- A later runtime integration gate is required before any runtime use.
