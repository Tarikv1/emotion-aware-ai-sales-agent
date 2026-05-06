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
