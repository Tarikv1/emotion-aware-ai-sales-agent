# RAG-007 Reviewed First Slice

## Purpose

RAG-007 creates the first manually reviewed RAG knowledge slice from RAG-006. It is a promotion gate for reviewed artifacts, not runtime retrieval.

## Selected Slice

Response wording:

- Yes-And objection framing.
- Short declarative statements.
- Empathy echo.
- PREP structure.
- 3-2-1 answer structure.

Voice delivery:

- Yes-And delivery posture.
- Tone mismatch as uncertainty and clarification.
- Trustworthiness over forced friendliness.
- Bounded vocal toolbox guidance.

## Commands

Run:

```powershell
python scripts\run_rag_007_reviewed_first_slice.py
```

Validate:

```powershell
python scripts\validate_rag_007_reviewed_first_slice.py
```

## Default Output

`research\experiments\generated\RAG-007-reviewed-first-slice\`

- `result.json`
- `report.md`

## Current Reviewed Slice Run

The 2026-05-06 run against the refreshed RAG-006 packet produced:

- `9` reviewed knowledge items
- `5` response-wording items
- `4` voice-delivery items
- `0` auto-promoted chunks
- source excerpt text stored: `false`
- runtime retrieval disabled
- chunk import disabled
- provider and NotebookLM calls made: `false`
- private customer data used: `false`

The slice is vertical-agnostic and campaign-guardrail-compatible. It prepares reviewed knowledge for a later retrieval-policy checkpoint but does not make the runtime sales agent use RAG.

## Product Boundary

Architecture block:

```text
RAG-004 source manifest
  + RAG-005 normalized chunks
  + RAG-006 review packet
  -> RAG-007 reviewed first slice artifacts
  -> human/product review
  -> guarded retrieval policy required before runtime use
```

Runtime retrieval and chunk import are disabled. RAG-007's default command uses no source excerpt text, private customer data, provider call, NotebookLM API call, API key, or data/private read. The runner also rejects private input/output paths.
