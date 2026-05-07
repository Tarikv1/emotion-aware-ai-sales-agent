# RAG-007 Reviewed First Slice Design

## Goal

Create the first manually reviewed RAG knowledge slice for the project from RAG-006 candidates.

RAG-007 is a promotion gate for a small, safe, source-tracked slice. It does not enable runtime retrieval, does not import chunks into product memory, and does not make the sales agent use the promoted knowledge automatically.

The first slice should be vertical-agnostic. It should support the reusable sales-agent core across campaign profiles, not only insurance.

## Selected Slice

The first slice has two lanes.

Response wording:

- `rag005-chunk-017`: Yes-And objection framing
- `rag005-chunk-020`: short declarative statements
- `rag005-chunk-022`: empathy echo
- `rag005-chunk-024`: PREP structure
- `rag005-chunk-025`: 3-2-1 answer structure

Voice delivery:

- `rag005-chunk-091`: Yes-And delivery posture
- `rag005-chunk-098`: tone and pitch mismatch as an uncertainty signal
- `rag005-chunk-099`: trustworthiness over forced friendliness
- `rag005-chunk-101`: bounded vocal toolbox guidance

Excluded from the first slice:

- scarcity, loss aversion, decoy effects, sunk-cost reframing, reciprocity, authority, and other pressure tactics
- any tactic that depends on sensitive demographic inference
- any tactic that could override campaign guardrails, compliance text, customer refusal, or human escalation

## Review Policy

Every promoted item must be rewritten as project-owned paraphrased knowledge.

RAG-007 may carry source IDs, source titles, source metadata status, topic IDs, and reviewer notes. It must not copy raw source excerpts or quote text from RAG-005/RAG-006.

The `quote_review_required` flag from RAG-005/RAG-006 is resolved in RAG-007 by replacing quote-dependent content with a concise paraphrase and marking the item as manually reviewed for the first slice.

Source metadata can remain `needs_human_review` for later bibliography cleanup, but the RAG-007 report must show that runtime retrieval is still disabled and that source metadata is not final.

## Knowledge Rules

Each promoted item stores:

- `knowledge_id`
- `lane`
- `source_chunk_ids`
- `source_ids`
- `topic_ids`
- `review_verdict`
- `project_rule`
- `safe_application`
- `do_not_use_when`
- `guardrail_notes`
- `runtime_eligible_now: false`
- `retrieval_eligible_now: false`

Response-wording rules must stay conversational and bounded:

- acknowledge the customer's concern before moving to a useful next step
- use short statements when clarity matters
- structure longer answers only when the customer asked a broad or complex question
- echo emotion or key wording sparingly, not mechanically
- correct factual, legal, medical, pricing, or contract errors directly instead of using agreement language

Voice-delivery rules must stay weak and non-diagnostic:

- use tone guidance only to improve the agent's own delivery
- treat perceived customer tone mismatch as uncertainty, not truth
- ask a gentle clarification when words and tone appear misaligned
- preserve explicit consent, refusal, compliance boundaries, and campaign scripts
- avoid imitating a source speaker's identity, accent, or personal style

## Architecture

RAG-007 reads the existing RAG-006 review packet and RAG-004 source manifest.

It writes a reviewed first-slice artifact under:

```text
research\experiments\generated\RAG-007-reviewed-first-slice\
```

Expected files:

- `result.json`
- `report.md`

Product documentation should live at:

```text
docs\product\RAG_007_REVIEWED_FIRST_SLICE.md
```

The command map should add RAG-007 run and validation commands after RAG-006.

## Boundaries

Default behavior:

- no runtime retrieval
- no chunk import into product memory
- no auto-promotion
- no provider calls
- no NotebookLM API calls
- no private customer data
- no reads from `data/private`
- no raw source text or source excerpts stored
- no API keys or secrets required

RAG-007 is a reviewed artifact that prepares for a later guarded retrieval policy. A later checkpoint must separately decide how retrieval is queried, ranked, filtered, cited, and blocked by campaign guardrails.

## Validation

The RAG-007 validator must prove:

- all selected chunk IDs exist in RAG-006/RAG-005 inputs
- no unselected pressure-tactic chunks are promoted
- every promoted rule has `runtime_eligible_now: false`
- every promoted rule has `retrieval_eligible_now: false`
- no raw source excerpt text is present
- no source excerpt storage boundary is violated
- no provider or NotebookLM call is required
- no private data paths are read
- the tone-mismatch item is rewritten as uncertainty/clarification, not emotion certainty
- the output remains vertical-agnostic and campaign-guardrail-compatible

## Thesis Note

RAG-007 records the transition from extraction and review queues into a small manually reviewed knowledge slice. This is useful thesis evidence because it shows that the system does not treat extracted persuasion or voice advice as automatically safe. Human review, paraphrasing, source tracking, and guardrail compatibility remain required before retrieval or runtime use.
