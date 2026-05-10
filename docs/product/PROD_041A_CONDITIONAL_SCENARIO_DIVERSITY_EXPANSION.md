# PROD-041A Interactive Conditional Customer Simulation Expansion

PROD-041A now tests interactive conditional customer simulation, not fixed scripted dialogue.

Generation flow is now:

`PROD-014 abstract scenario bank + PROD-013 abstract pattern IDs -> scenario_recipes.json -> customer_reaction_policy_bank.json -> interactive_scenario_profiles.json -> current local sales-agent turn harness -> customer simulator -> interaction_traces.json -> review surface`

The final HTML contains generated traces after running the agent against the customer simulator. Scenario profiles do not expose full scripts to the agent. They define persona, real-world context, hidden state, reaction paths, terminal policy, safety boundaries, and seed variation policy.

## Local Commands

```powershell
python scripts\run_prod_041a_conditional_scenario_diversity_expansion.py
python scripts\validate_prod_041a_conditional_scenario_diversity_expansion.py
```

## Outputs

- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/result.json`
- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/report.md`
- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/scenario_recipes.json`
- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/customer_reaction_policy_bank.json`
- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/concrete_scenario_frames.json`
- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/interactive_scenario_profiles.json`
- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/interaction_traces.json`
- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/scenario_diversity_traces.json`
- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/scenario_diversity_review.html`
- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/scenario_diversity_review_data.json`

`scenario_diversity_traces.json` is kept only as a compatibility alias for existing checkpoint conventions. The canonical trace artifact is `interaction_traces.json`.

## Required Gates

- Scenario profile count: `40`
- B2B profiles: `24`
- B2C profiles: `16`
- Seed count per scenario: at least `3`
- Generated trace count: at least `120`
- All `40` curated labels appear once at profile level.
- Customer reaction policy bank contains conditional rules with abstract `source_pattern_ids`, state deltas, utterance variants, possible paths, terminal risk, and safety notes.
- Interactive profiles contain no full agent answers and no fixed customer scripts.
- Every trace references `scenario_id`, `seed`, and selected `reaction_rule_ids`.
- Customer turns depend on immediately previous `agent_action_tags`.
- Customer state before and after every customer response is recorded.
- Actual local sales-agent logic use is recorded truthfully. The current local harness is called, but it is single-turn/stage-classified and does not consume full conversation history well enough for final contextual trace text, so PROD-041A records `actual_agent_logic_used: false` and uses the deterministic `prod_041a_reactive_agent_adapter` for final agent turns.
- Every agent turn records previous customer text, deterministic customer intent tags, agent reactivity tags, whether the latest customer intent was addressed, whether the answer repeated prior agent text, whether new information was added, whether the conversation progressed, and whether the agent ignored customer input.
- Conversations are variable length, not fixed three-turn scripts.
- At least `70` traces have `5+` exchanges.
- At least `40` traces have `8+` exchanges.
- At least `15` traces have `12+` exchanges.
- At least `4` traces have `18+` exchanges.
- No more than `25%` of traces share the same exchange count.
- No scenario uses the same exchange count across all seeds.
- Repeated full agent response sequence count: `0`
- Repeated full customer response sequence count: `0`
- Repeated agent answer count: `0`
- Ignored customer input count: `0`
- Looping question count: `0`
- False safe close count: `0`
- Hard failure count: `0`
- Payment collection count: `0`
- Unsupported claim count: `0`
- Leakage findings: `0`
- Provider calls made: `false`
- LLM used: `false`
- Exact transcript text used: `false`
- Source transcript sequence used: `false`
- Runtime behavior changed by this checkpoint: `false`
- Production runtime promotion allowed: `false`

## Result

- Generated traces: `120`
- Scenario profiles: `40`
- Seed count per scenario: `3`
- B2B/B2C profiles: `24 / 16`
- Reaction rules: `20`
- Actual agent logic called: `true`
- Actual agent logic used as final contextual text: `false`
- Agent addressed customer intent rate: `1.0`
- Agent reactivity average score: `1.0`
- Agent reactivity passed traces: `120`
- Traces with `5+` exchanges: `116`
- Traces with `8+` exchanges: `76`
- Traces with `12+` exchanges: `47`
- Traces with `18+` exchanges: `11`
- Same exchange count max rate: `0.1167`
- Neutral-state two-exchange traces: `98`
- Agent-caused state-change traces: `120`
- Customer challenge/pushback traces: `109`
- Recovery-from-weak-answer traces: `85`
- Boundary-handling traces: `23`
- Repeated full agent response sequence count: `0`
- Repeated full customer response sequence count: `0`
- Repeated agent answer count: `0`
- Ignored customer input count: `0`
- Looping question count: `0`
- False safe close count: `0`
- Hard failure count: `0`
- Payment collection count: `0`
- Unsupported claim count: `0`
- Leakage findings: `0`

## Review Surface

The static HTML review surface filters by scenario label, seed, path taken, terminal outcome, exchange count, B2B/B2C, domain, emotion, failure flag, and `actual_agent_logic_used`.

Each trace shows:

- scenario id
- seed
- path taken
- exchange count
- terminal outcome
- safe-close and non-sale correctness counters
- exact agent text per exchange
- `agent_action_tags` per agent turn
- previous customer intent tags and agent reactivity tags per exchange
- agent intent-addressing, repetition, new-information, progression, looping-question, and ignored-input booleans per exchange
- exact customer text per exchange
- selected `reaction_rule_ids`
- customer state before and after each customer response
- runtime decision metadata from the local agent harness
- failure taxonomy hits
- safety flags
- loop guard status
- scenario-level scores

## Decision

The next checkpoint remains `PROD-041-conditional-simulation-review` for human review.

PROD-041A remains offline, deterministic, and locked as the interactive customer simulation checkpoint.

## Boundary

PROD-041A does not call providers, call an LLM, read private data, download datasets, store raw transcripts, copy transcript text, export transcript-derived commercial runtime prompts, start a server, collect payment, enable retrieval by default, enable composer hooks by default, change runtime behavior, or allow production runtime promotion.
