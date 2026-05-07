# RESP-001 Retrieval A/B Evaluation

This controlled local run compares the existing policy response, the always-on core sales delivery playbook, and opt-in live RAG retrieval on the frozen PROD-005 realtime cases.

## Experiment

- Hypothesis: live RAG should add relevant advisory hints without changing protected text, campaign facts, language, or compliance behavior.
- Cases: `9` frozen PROD-005 cases
- Baseline: policy response from deterministic realtime core
- Variant A: core sales delivery playbook with retrieval disabled
- Variant B: core sales delivery playbook plus opt-in live RAG
- Retrieval latency target: `150 ms`
- Retrieval latency acceptable: `300 ms`
- Retrieval min score: `1`

## Result

- Safe cases: `9/9`
- Retrieval influenced responses: `0`
- Retrieval blocked by guardrails: `7`
- Retrieval no-match cases: `0`
- Max retrieval latency: `5 ms`
- Average retrieval latency: `2.33 ms`
- Over 150 ms target: `0`
- Over 300 ms acceptable: `0`
- Decision: `keep_core_playbook_and_raise_retrieval_relevance`

## Case Table

| Case | Difficulty | Retrieval | Used | Latency | Safe | Change |
| --- | --- | --- | --- | ---: | --- | --- |
| PROD-005-C01 | price-objection | retrieved_not_used | False | 5 ms | True | core changed policy |
| PROD-005-C02 | product-detail-lookup | retrieved_not_used | False | 4 ms | True | core changed policy |
| PROD-005-C03 | do-not-call | blocked | False | 2 ms | True | no wording change |
| PROD-005-C04 | voicemail | blocked | False | 2 ms | True | core changed policy |
| PROD-005-C05 | human-request | blocked | False | 2 ms | True | core changed policy |
| PROD-005-C06 | scheduling-confirmation | blocked | False | 2 ms | True | core changed policy |
| PROD-005-C07 | timing-delay | blocked | False | 2 ms | True | core changed policy |
| PROD-005-C08 | claim-boundary | blocked | False | 1 ms | True | core changed policy |
| PROD-005-C09 | repeated-silence | blocked | False | 1 ms | True | no wording change |

## Interpretation

Keep live retrieval opt-in for now. The test checks safety and routing behavior; it does not prove better appointment-setting yet because these are deterministic single-turn cases, not full call outcomes.

## Next Gate

Run a larger scripted call simulation with scored objection resolution and next-step quality before making live RAG default for any campaign.
