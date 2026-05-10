# PROD-041A Conditional Scenario Diversity Expansion

PROD-041A keeps the same 40-scenario checkpoint but repairs dialogue generation through a recipe-grounded frame layer and a spoken_trace_authoring layer.

## Summary
- Call Count: `40`
- B2B Call Count: `24`
- B2C Call Count: `16`
- Recipe Count: `40`
- Frame Count: `40`
- Scenario Label Count: `40`
- Domain Count: `27`
- Opening Style Count: `7`
- Terminal Outcome Type Count: `9`
- Safe Close Rate: `0.775`
- Non Sale Correctness Rate: `1.0`
- Hard Failure Rate: `0.0`
- Strategy Match Rate: `1.0`
- Emotion Handling Rate: `1.0`
- Dialogue Realism Average Score: `6.525`
- Dialogue Realism Min Score: `5`
- Non Smooth Trace Rate: `0.35`
- Scenario Frame Quality Average Score: `7.0`
- Scenario Frame Quality Min Score: `7`
- Spoken Trace Authoring Used: `True`
- Short Customer Response Trace Count: `40`
- Frame Detail Trace Count: `29`
- Challenge Before Final Trace Count: `20`
- Agent Bridge Sentence Max Repeat: `1`
- Customer Bridge Sentence Max Repeat: `2`
- Hard Failure Count: `0`
- Payment Collection Count: `0`
- Unsupported Claim Count: `0`
- Leakage Finding Count: `0`

## Outputs

- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/result.json`
- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/report.md`
- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/scenario_recipes.json`
- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/concrete_scenario_frames.json`
- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/scenario_diversity_traces.json`
- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/scenario_diversity_review.html`
- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/scenario_diversity_review_data.json`

## Scenario Frame Coverage

- Recipe count: `40`
- Frame count: `40`
- Source checkpoint IDs: `PROD-014-callcenteren-scenario-bank` and `PROD-013-callcenteren-pattern-extraction`
- Scenario recipes contain abstract call-center structures only; frames invent fictional contexts from those recipes.
- Spoken dialogue is authored from scenario-specific natural-language scripts through `spoken_trace_authoring`.
- Frame fields are semantic inputs only; dialogue does not copy practical triggers, first objections, next steps, or spoken reasons verbatim.

## Boundary

PROD-041A remains offline and deterministic. No provider calls, no LLM calls, no private data reads, no dataset downloads, no transcript text copying, no runtime behavior changes, and no production promotion.

The next checkpoint remains `PROD-041-conditional-simulation-review` for human review.
