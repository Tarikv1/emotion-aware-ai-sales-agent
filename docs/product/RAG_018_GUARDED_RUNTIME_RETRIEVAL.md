# RAG-018 Guarded Runtime Retrieval

## Purpose

RAG-018 connects the RAG-017 local registry to guarded response generation as an explicit opt-in path. It does not add a vector database, embedding provider, LLM reranker, private-data read, or default runtime retrieval.

## Runtime Contract

`scripts\generate_guarded_response.py` supports:

```powershell
--retrieval-enabled
--retrieval-registry <path-to-rag-017-result.json>
--retrieval-max-results <n>
```

When retrieval is disabled, the output still includes retrieval metadata with `enabled=false` and `retrieval_used_in_runtime=false`.

When retrieval is enabled, advisory items may influence response metadata and hints only if the guarded response passes validation and the context is not blocked.

## Hard Blocks

Retrieval influence is blocked for:

- customer refusal
- do-not-call
- human escalation
- protected scripts
- required disclosure/protected-text contexts
- pressure-sensitive contexts
- private-data retrieval requests

## Voice/Prosody Limits

Voice/prosody rules are advisory-only. They may guide delivery hints, but they cannot claim hidden emotion, infer protected traits, escalate pressure, or change protected campaign/disclosure/refusal text.

## Validate

```powershell
python scripts\validate_rag_018_guarded_runtime_retrieval.py
```
