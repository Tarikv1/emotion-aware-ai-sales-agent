# RAG-015 Source-Mapping Batches

RAG-015 organizes the remaining RAG source-mapping work after RAG-014. It reports `58 remaining source-mapping chunks` across `43 source-title groups`, grouped into review batches. It applies `0` source-mapping decisions.

Runtime retrieval remains disabled.

## Source Material Timing

Adding more source material later remains feasible. The project already has a repeatable path through RAG-001/RAG-002 intake and RAG-003+ refresh/review gates. New sources should still go through the same source accounting, chunk normalization, source mapping, quote clearance, and runtime-admission checks.

The practical rule is:

- Add a source now only if it is foundational enough to change the taxonomy or first principles.
- Add ordinary extra sales, voice, persuasion, objection-handling, or discovery material later through the intake pipeline.

## Command

Run from the repo root:

```powershell
python scripts\run_rag_015_source_mapping_batches.py
```

Default output folder:

```text
research\experiments\generated\RAG-015-source-mapping-batches\
```

Validate the checkpoint:

```powershell
python scripts\validate_rag_015_source_mapping_batches.py
```

## Inputs

- `research/experiments/generated/RAG-014-source-mapped-quote-followup/result.json`
- `research/experiments/generated/RAG-013-cleanup-strategy/result.json`
- `research/experiments/generated/RAG-006-chunk-review-packet/result.json`
- `research/experiments/generated/RAG-009-all-source-review-coverage/result.json`
- `research/experiments/cases/rag-015-source-mapping-batches.json`

## Official Counts

- Source-mapping groups: `43`
- Source-mapping chunks: `58`
- High-impact groups with `3+` chunks: `3`
- Medium groups with `2` chunks: `6`
- Singleton groups: `34`
- Candidate source suggestion groups: `6`
- Candidate source suggestions: `7`
- Latent quote follow-ups after source mapping: `21`
- Cleanup decisions applied now: `0`
- Source-mapping blockers resolved now: `0`
- Source-mapping blockers remaining: `58`
- Auto-promoted chunks: `0`
- Runtime retrieval enabled: `false`
- Chunk import enabled: `false`

## Priority Batches

| Batch | Groups | Chunks | Latent quote follow-ups |
| --- | ---: | ---: | ---: |
| `batch_1_high_impact_groups` | `3` | `12` | `3` |
| `batch_2_medium_groups` | `6` | `12` | `6` |
| `batch_3_suggested_singletons` | `6` | `6` | `3` |
| `batch_4_unsuggested_singletons` | `28` | `28` | `9` |

## Review Rules

- RAG-015 is a batch packet only.
- Human source review is still required before source mapping can be accepted.
- Candidate source suggestions are review hints only and are not auto-applied.
- Source mapping may create additional quote-clearance follow-up work.
- Runtime admission still requires a later gate after cleanup and re-audit.

## Boundaries

- Runtime retrieval remains disabled.
- Chunk import remains disabled.
- No chunks are auto-promoted.
- No source-mapping decisions are applied.
- No provider or NotebookLM API calls are made.
- No private customer data is used.
- No source excerpt text is stored.
- A later runtime integration gate is required before any runtime use.
