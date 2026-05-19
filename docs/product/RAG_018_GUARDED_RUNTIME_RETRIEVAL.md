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

The accepted influence paths are intentionally narrow.

A safe German price-objection turn may use retrieved objection-diagnosis/autonomy hints to ask a clearer clarifying question before answering. The current RAG-guided wording is:

```text
Das verstehe ich. Damit ich nicht am Punkt vorbeirede: Geht es Ihnen eher um den Preis, die Bedingungen oder darum, ob sich der Aufwand lohnt?
```

A safe English send-me-info turn may use retrieved send-info/qualification hints to ask what information would be relevant before sending a generic follow-up. The current RAG-guided wording is:

```text
I can send information. To make it relevant, should I send details about fit, pricing, or how a specialist would review this with you?
```

A safe English authority/boss turn may use retrieved objection-diagnosis hints to offer a shareable summary or address one concern first. The current RAG-guided wording is:

```text
That makes sense. Should I send a short summary you can share with your boss, or is there one concern I should address first?
```

A safe English trust turn may use retrieved objection/proof hints to ask which proof-oriented information would help first. The current RAG-guided wording is:

```text
Fair. Trust matters on a cold call. To make this useful, should I send company context, security details, or a specialist review path first?
```

The matching no-retrieval core-playbook response remains the baseline, and all protected, blocked, or unsupported contexts must still report `retrieval_used_in_runtime=false`.

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

## Current Evidence

`scripts\run_resp_001_retrieval_ab_evaluation.py` compares policy response, core playbook, and opt-in live RAG on the 9 frozen `PROD-005` realtime cases.

- safe cases: `9/9`
- retrieval influenced responses: `1`
- retrieval blocked by guardrails: `7`
- retrieval no-match cases: `0`
- max retrieval latency: `3 ms`
- average retrieval latency: `1.33 ms`
- decision: `keep_hybrid_opt_in_and_run_larger_call_simulation`

`scripts\run_rag_018_scripted_call_simulation.py` then runs a larger fixed scripted-call simulation with scored objection resolution and next-step quality.

- cases: `10`
- quality-scored cases: `6`
- safe cases: `10/10`
- retrieval influenced responses: `4`
- objection-resolution improvements: `4`
- next-step quality improvements: `4`
- protected contexts preserved: `4/4`
- quality gap case IDs: `RAG-018-SIM-C05, RAG-018-SIM-C06`
- max retrieval latency: `3 ms`
- average retrieval latency: `1.5 ms`
- decision: `keep_rag_018_opt_in_and_do_not_make_default`

`scripts\run_rag_018_retrieval_vs_core_call_simulation.py` runs the RAG-018 retrieval-vs-core call simulation across fixed synthetic multi-turn calls to compare the older retrieval-disabled core path against opt-in retrieval.

- calls: `4`
- turns: `12`
- retrieval version wins: `4`
- core version wins: `0`
- score delta: `+8`
- protected turns preserved: `6/6`
- max retrieval latency: `3 ms`
- average retrieval latency: `1.58 ms`
- decision: `keep_retrieval_opt_in_for_validated_objection_turns`

These runs made no provider calls, used no private customer data, and used no vector database, embedding provider, or LLM reranker.

`scripts\run_prod_012_callcenteren_scenario_evaluation.py` extends this comparison to CallCenterEN-grounded synthetic scenarios while keeping the dataset pattern-grounding only.

- scenarios: `6`
- turns: `12`
- retrieval version wins: `5`
- old core wins: `0`
- retrieval score: `14`
- old core score: `5`
- hard failure rate: `0.0`
- non-sale correctness: `1.0`
- leakage failure rate: `0.0`
- protected turns preserved: `5/5`
- decision: `keep_retrieval_opt_in_for_callcenteren_grounded_scenarios`

This is stronger opt-in evidence, not default-retrieval evidence.

## Validate

```powershell
python scripts\validate_rag_018_guarded_runtime_retrieval.py
```

Validate the larger scripted-call simulation:

```powershell
python scripts\validate_rag_018_scripted_call_simulation.py
```

Validate the retrieval-vs-core call simulation:

```powershell
python scripts\validate_rag_018_retrieval_vs_core_call_simulation.py
```

Run the current policy/core-playbook/live-RAG comparison:

```powershell
python scripts\run_resp_001_retrieval_ab_evaluation.py
```

Run the scripted-call simulation directly:

```powershell
python scripts\run_rag_018_scripted_call_simulation.py
```

Run the retrieval-vs-core call simulation directly:

```powershell
python scripts\run_rag_018_retrieval_vs_core_call_simulation.py
```
