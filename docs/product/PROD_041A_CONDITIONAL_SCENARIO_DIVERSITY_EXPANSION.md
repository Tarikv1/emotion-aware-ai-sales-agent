# PROD-041A Conditional Scenario Diversity Expansion

PROD-041A keeps the same `40`-scenario checkpoint and repairs dialogue realism by adding concrete scenario frame mining before trace generation.

Generation flow is now:

`PROD-014 abstract scenario bank + PROD-013 abstract pattern IDs -> scenario_recipes.json -> concrete_scenario_frames.json -> spoken_trace_authoring -> scenario_diversity_traces.json -> review surface`

The recipe layer stores abstract reusable call-center structures only. Concrete frames are original fictional situations invented from those recipes. `spoken_trace_authoring` then uses those frames as semantic inputs only and selects scenario-specific authored spoken dialogue. It does not copy practical triggers, first objections, realistic next steps, spoken reasons, repeated concern phrases, source wording, or source sequences directly into speech.

## Local Commands

```powershell
python scripts\run_prod_041a_conditional_scenario_diversity_expansion.py
python scripts\validate_prod_041a_conditional_scenario_diversity_expansion.py
```

## Outputs

- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/result.json`
- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/report.md`
- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/scenario_recipes.json`
- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/concrete_scenario_frames.json`
- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/scenario_diversity_traces.json`
- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/scenario_diversity_review.html`
- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/scenario_diversity_review_data.json`

## Required Gates

- Call count: `40`
- B2B call count: `24`
- B2C call count: `16`
- Scenario labels: all `40` required curated labels appear exactly once.
- Scenario recipe count: `40`
- Each recipe describes only generalized structure, cites abstract pattern IDs, blocks transcript text, source sequences, dataset-specific phrasing, names, phone numbers, addresses, provider names, and close paraphrases of source examples.
- Concrete frame count: `40`
- Each trace references one `scenario_frame_id`, and each frame is used exactly once.
- Each trace references one `recipe_id`, and concrete frames reference their recipe source pattern IDs.
- Frames are original fictional contexts, not copied or paraphrased source situations.
- Spoken trace authoring is active, and visible dialogue is authored from scenario-specific natural-language scripts rather than frame-field interpolation.
- Each frame includes concrete context, customer role, practical trigger, first objection, realistic goal, realistic next step, safety boundaries, spoken guidance, and at least two source pattern IDs.
- Frame quality average score: `>= 6.5 / 7`, with no frame below `6 / 7`.
- Opening styles: all `7` allowed opening styles appear at least once.
- Terminal outcomes: at least `6` terminal outcome types appear, including support boundary, not qualified, handoff, callback, written information, and rejection.
- Strategy detection: deterministic rules only; no LLM judging.
- Emotion handling: deterministic rules only.
- Dialogue realism: each trace records `natural_customer_language`, `natural_agent_language`, `low_template_repetition`, `opening_grammar_ok`, `objection_progression_realistic`, `terminal_outcome_earned`, and `frame_context_used`.
- Dialogue realism average score: `>= 5.8 / 7`
- No trace below `5 / 7`
- Not every trace should be perfect.
- Non smooth trace rate: at least `0.2`, with customer interruptions, skeptical pushback, one-word refusals, confused follow-ups, early price asks, identity checks, email-only requests, and refusal-before-finish cases represented.
- Opening grammar issue count: `0`
- Banned template phrase hits: `0`
- Scenario label in spoken dialogue count: `0`
- Concern text repeat violations per conversation: `0`
- Agent bridge sentence repeat max: `<= 3`
- Customer bridge sentence repeat max: `<= 2`
- Traces with short customer response under 8 words: `>= 20`
- Traces with concrete frame detail used in speech: `>= 10`
- Traces with interruption/challenge/correction/refusal before final turn: `>= 10`
- Hard failure count: `0`
- Payment collection count: `0`
- Unsupported claim count: `0`
- Leakage findings: `0`

## Result

- Safe close rate: `0.775`
- Non sale correctness rate: `1.0`
- Hard failure rate: `0.0`
- Strategy match rate: `1.0`
- Emotion handling rate: `1.0`
- Dialogue realism average score: `6.85`
- Dialogue realism minimum score: `6`
- Dialogue realism pass count: `34`
- Non smooth trace rate: `0.45`
- Scenario recipe count: `40`
- Spoken trace authoring used: `true`
- Scenario frame quality average score: `7.0`
- Scenario frame quality minimum score: `7`
- Traces with short customer responses under 8 words: `40`
- Traces with frame detail used in dialogue: `40`
- Traces with interruption/challenge/correction/refusal before final turn: `18`
- Banned template phrase hits: `0`
- Opening grammar issue count: `0`
- Scenario label in spoken dialogue count: `0`
- Concern text repeat violations: `0`
- Agent bridge sentence repeat max: `1`
- Customer bridge sentence repeat max: `2`
- Hard failure count: `0`
- Payment collection count: `0`
- Unsupported claim count: `0`
- Leakage findings: `0`
- Failure taxonomy: all tracked flags remain at `0`

## Review Surface

The static HTML review surface supports filtering by B2B/B2C, domain, scenario label, emotion, strategy, objection, terminal outcome, and failure flag.

Each scenario shows:

- scenario frame id
- scenario recipe id
- customer role
- real world context
- practical trigger
- first customer objection
- hidden objection
- realistic agent goal
- realistic next step
- spoken language guidance
- scenario frame quality score
- selected opening plus unused opening variants
- exact customer text and exact agent answer per turn
- emotional state start and customer state shift
- required strategy, detected strategies used, and scenario strategy match
- terminal outcome and whether it counts toward safe close rate or non sale correctness rate
- dialogue realism score, non-smooth flag, recovery marker, variety tags, template hits, and opening grammar findings
- scenario-level scores
- failure taxonomy hits

## Decision

The next checkpoint remains `PROD-041-conditional-simulation-review` for human review.

PROD-041A remains offline, deterministic, and locked as the scenario diversity checkpoint.

## Boundary

PROD-041A does not call providers, call an LLM, read private data, download datasets, store raw transcripts, copy transcript text, export transcript-derived commercial runtime prompts, start a server, collect payment, enable retrieval by default, enable composer hooks by default, change runtime behavior, or allow production runtime promotion.
