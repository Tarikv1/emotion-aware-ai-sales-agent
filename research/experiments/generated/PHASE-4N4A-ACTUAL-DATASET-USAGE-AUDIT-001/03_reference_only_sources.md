# Reference-Only Sources

| Source | Classification | Repo evidence | Correct use | Prohibited overclaim |
| --- | --- | --- | --- | --- |
| CallCenterEN / AIxBlock call-center scripts | reference_only_pattern_grounding | `docs/thesis/THESIS_REFERENCE_REGISTRY.md` | Pattern grounding for scenario-bank design, abstract pattern extraction, sales-policy review, and evaluator hardening. | Do not claim local downloaded training use unless a later artifact proves it. Do not copy transcript sentences, high-similarity paraphrases, or raw transcript bodies into tracked prompts, scenarios, reports, or runtime prompts. |
| Public OpenAI ChatGPT plan-fit fixture | product_source_bundle_claim_governance | `docs/thesis/THESIS_REFERENCE_REGISTRY.md`, `research/experiments/generated/PUBLIC-OPENAI-SOURCE-BUNDLE-001/result.json` | Source-grounded campaign/eval work, claim governance, plan-fit fixture construction, and product-boundary checks. | It is not a training dataset and is not proof of sales effectiveness. |

## Source Boundary

Reference-only sources can shape taxonomy, claim precision, and evaluation design. They should not be described as raw training data unless a specific generated dataset/result file says they were transformed into a permitted dataset under the repo privacy and license rules.
