# PROD-041A Interactive Conditional Customer Simulation Expansion

PROD-041A now tests interactive conditional customer simulation, not fixed scripted dialogue.

The final HTML contains generated traces after running the local sales-agent turn harness against a deterministic customer simulator. Scenario profiles define persona, state, hidden objections, paths, terminal policy, safety boundaries, and seeds; they do not expose full scripts to the agent.

## Summary
- Scenario Profile Count: `40`
- Profile B2B Count: `24`
- Profile B2C Count: `16`
- Seed Count Per Scenario Min: `3`
- Generated Trace Count: `120`
- Reaction Rule Count: `20`
- Domain Count: `27`
- Terminal Outcome Type Count: `9`
- Actual Agent Logic Used: `True`
- Safe Close Rate: `0.8417`
- Non Sale Correctness Rate: `1.0`
- Hard Failure Count: `0`
- Payment Collection Count: `0`
- Unsupported Claim Count: `0`
- Leakage Finding Count: `0`
- Traces With 5 Plus Exchanges: `116`
- Traces With 8 Plus Exchanges: `76`
- Traces With 12 Plus Exchanges: `47`
- Traces With 18 Plus Exchanges: `11`
- Same Exchange Count Max Rate: `0.1167`
- Neutral State Two Exchange Trace Count: `81`
- Agent Caused State Change Trace Count: `120`
- Challenge Pushback Trace Count: `114`
- Recovery From Weak Answer Trace Count: `56`
- Boundary Handling Trace Count: `23`
- Repeated Full Agent Response Sequence Count: `0`
- Repeated Full Customer Response Sequence Count: `0`

## Outputs

- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/result.json`
- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/report.md`
- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/scenario_recipes.json`
- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/customer_reaction_policy_bank.json`
- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/interactive_scenario_profiles.json`
- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/interaction_traces.json`
- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/scenario_diversity_review.html`
- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/scenario_diversity_review_data.json`

## Review Trace Fields

Each generated interaction trace records `agent_action_tags`, selected `reaction_rule_ids`, customer state before/after each response, failure taxonomy hits, safety flags, loop guard status, and whether actual local agent logic was used.

## Boundary

PROD-041A remains offline and deterministic. No provider calls, no LLM calls, no private data reads, no dataset downloads, no transcript text copying, no runtime behavior changes, and no production promotion.

The next checkpoint remains `PROD-041-conditional-simulation-review` for human review.
