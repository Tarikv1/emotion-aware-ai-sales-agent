# RAG-018 Guarded Runtime Retrieval

## Purpose

RAG-018 connects the RAG-017 local registry to guarded response generation as an explicit opt-in path. It does not add a vector database, embedding provider, LLM reranker, private-data read, or default runtime retrieval.

RAG-017 may include the RAG-019 public sales communication source expansion after the RAG-019 validator passes. Those items remain advisory, source-traced, and blocked by the same runtime guardrails.

## Runtime Contract

`scripts\generate_guarded_response.py` supports:

```powershell
--retrieval-enabled
--retrieval-registry <path-to-rag-017-result.json>
--retrieval-max-results <n>
--retrieval-min-score <n>
--retrieval-target-latency-ms <n>
--retrieval-acceptable-latency-ms <n>
```

When retrieval is disabled, the output still includes retrieval metadata with `enabled=false` and `retrieval_used_in_runtime=false`.

When retrieval is enabled, advisory items may influence response metadata and hints only if the guarded response passes validation and the context is not blocked. `retrieval_used_in_runtime` is true only when the RAG-guided candidate differs from the no-retrieval core-playbook candidate; retrieved hints that do not change the response are reported as `retrieved_not_used`.

## Retrieval Timing And Gates

Live retrieval runs before candidate response composition only when `--retrieval-enabled` is set.

Latency budget:

- target: under 150 ms
- acceptable: under 300 ms
- fallback: skip retrieval and use the core playbook, or use a short stall-for-time bridge only when the call state allows it

Retrieved hints are used only when they pass the configured relevance threshold and campaign/source gate. Campaign facts, product facts, pricing, discounts, compliance text, allowed claims, forbidden claims, and client scripts override generic RAG advice.

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

Run the current policy/core-playbook/live-RAG comparison:

```powershell
python scripts\run_resp_001_retrieval_ab_evaluation.py
```
