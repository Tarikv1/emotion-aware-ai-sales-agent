# RAG-018 Retrieval-vs-Core Call Simulation

This local run compares the older retrieval-disabled core response path against opt-in RAG-018 retrieval on fixed synthetic multi-turn calls.

No provider call, private customer data, vector database, embedding provider, or LLM reranker was used.

## Experiment

- Hypothesis: the retrieval version should improve objection handling and next-step quality on validated objection turns without losing any protected or already-adequate core turns.
- Baseline: older core response path with retrieval disabled.
- Variant: core response path plus opt-in RAG-018 retrieval.
- Fixed calls: `4`
- Fixed turns: `12`

## Result

- Retrieval version wins: `4`
- Core version wins: `0`
- Ties: `8`
- Core total score: `4`
- Retrieval total score: `12`
- Score delta: `+8`
- Safe turns: `12/12`
- Protected turns preserved: `6/6`
- Retrieval influenced responses: `4`
- Max retrieval latency: `5 ms`
- Average retrieval latency: `3.25 ms`
- Decision: `keep_retrieval_opt_in_for_validated_objection_turns`

Interpretation: retrieval version wins on the validated objection turns and the older core version wins zero turns. Keep retrieval opt-in for these paths; do not make retrieval default from this scripted result alone.

## Turn Table

| Turn | Difficulty | Winner | Core Score | Retrieval Score | Retrieval Used | Safe |
| --- | --- | --- | ---: | ---: | --- | --- |
| RAG-018-CALL-01-T01 | unknown-runtime-signal | retrieval | 0 | 2 | True | True |
| RAG-018-CALL-01-T02 | unknown-runtime-signal | retrieval | 0 | 2 | True | True |
| RAG-018-CALL-01-T03 | unknown-runtime-signal | retrieval | 0 | 2 | True | True |
| RAG-018-CALL-01-T04 | human-request | tie | 0 | 0 | False | True |
| RAG-018-CALL-02-T01 | price-objection | retrieval | 0 | 2 | True | True |
| RAG-018-CALL-02-T02 | product-detail-lookup | tie | 2 | 2 | False | True |
| RAG-018-CALL-02-T03 | scheduling-confirmation | tie | 0 | 0 | False | True |
| RAG-018-CALL-03-T01 | do-not-call | tie | 0 | 0 | False | True |
| RAG-018-CALL-03-T02 | repeated-silence | tie | 0 | 0 | False | True |
| RAG-018-CALL-03-T03 | voicemail | tie | 0 | 0 | False | True |
| RAG-018-CALL-04-T01 | price-objection | tie | 2 | 2 | False | True |
| RAG-018-CALL-04-T02 | claim-boundary | tie | 0 | 0 | False | True |

## Next Gate

Do not make retrieval default until a larger call-outcome simulation or human review confirms that the extra objection handling improves appointment-setting without adding pressure, unsupported claims, or protected-context drift.
