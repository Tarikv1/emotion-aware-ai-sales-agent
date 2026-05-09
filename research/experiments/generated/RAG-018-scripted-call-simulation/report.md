# RAG-018 Scripted Call Simulation

This local run compares retrieval-disabled guarded responses against opt-in RAG-018 retrieval on fixed scripted turns with scored objection resolution and next-step quality.

No provider call, private customer data, vector database, embedding provider, or LLM reranker was used.

## Result

- Cases: `10`
- Quality-scored cases: `6`
- Safe cases: `10/10`
- Retrieval influenced responses: `4`
- Objection-resolution improvements: `4`
- Next-step quality improvements: `4`
- Protected contexts preserved: `4/4`
- Quality gap case IDs: `none`
- Max retrieval latency: `5 ms`
- Average retrieval latency: `3.3 ms`
- Decision: `keep_rag_018_opt_in_and_do_not_make_default`

Interpretation: keep RAG-018 opt-in and do not make retrieval default. The current narrow influence paths improve the German price-objection, send-me-info, authority, and trust turns while preserving protected contexts.

## Case Table

| Case | Difficulty | Retrieval | Used | Safe | Protected | Resolution Delta | Next-Step Delta |
| --- | --- | --- | --- | --- | --- | ---: | ---: |
| RAG-018-SIM-C01 | price-objection | influenced | True | True | False | 1 | 1 |
| RAG-018-SIM-C02 | price-objection | retrieved_not_used | False | True | False | 0 | 0 |
| RAG-018-SIM-C03 | unknown-runtime-signal | influenced | True | True | False | 1 | 1 |
| RAG-018-SIM-C04 | unknown-runtime-signal | influenced | True | True | False | 1 | 1 |
| RAG-018-SIM-C05 | unknown-runtime-signal | influenced | True | True | False | 1 | 1 |
| RAG-018-SIM-C06 | product-detail-lookup | retrieved_not_used | False | True | False | 0 | 0 |
| RAG-018-SIM-C07 | timing-delay | blocked | False | True | True | 0 | 0 |
| RAG-018-SIM-C08 | scheduling-confirmation | blocked | False | True | True | 0 | 0 |
| RAG-018-SIM-C09 | do-not-call | blocked | False | True | True | 0 | 0 |
| RAG-018-SIM-C10 | human-request | blocked | False | True | True | 0 | 0 |

## Next Gate

Do not make retrieval default from this scripted result alone. Run a broader multi-turn call simulation or add new cases before expanding retrieval beyond these four validated paths.
