# PROD-041A Conditional Scenario Diversity Expansion

PROD-041A expands the offline conditional simulator before the PROD-041 human review checkpoint.

It creates `40` deterministic mixed B2B/B2C calls with one curated label per scenario, richer terminal outcomes, opening-style diversity, rule-based strategy detection, deterministic emotion handling checks, scenario-level scores, hard-failure definitions, and failure taxonomy counts.

## Local Commands

```powershell
python scripts\run_prod_041a_conditional_scenario_diversity_expansion.py
python scripts\validate_prod_041a_conditional_scenario_diversity_expansion.py
```

## Outputs

- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/result.json`
- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/report.md`
- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/scenario_diversity_traces.json`
- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/scenario_diversity_review.html`
- `research/experiments/generated/PROD-041A-conditional-scenario-diversity-expansion/scenario_diversity_review_data.json`

## Required Gates

- Call count: `40`
- B2B call count: `24`
- B2C call count: `16`
- Scenario labels: all `40` required curated labels appear exactly once.
- Opening styles: all `7` allowed opening styles appear at least once.
- Terminal outcomes: at least `6` terminal outcome types appear, including support boundary, not qualified, handoff, callback, written information, and rejection.
- Strategy detection: deterministic rules only; no LLM judging.
- Emotion handling: deterministic rules only.
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
- Hard failure count: `0`
- Payment collection count: `0`
- Unsupported claim count: `0`
- Leakage findings: `0`
- Failure taxonomy: all tracked flags remain at `0`

## Review Surface

The static HTML review surface supports filtering by B2B/B2C, domain, scenario label, emotion, strategy, objection, terminal outcome, and failure flag.

Each scenario shows:

- selected opening plus unused opening variants
- exact customer text and exact agent answer per turn
- emotional state start and customer state shift
- required strategy, detected strategies used, and scenario strategy match
- terminal outcome and whether it counts toward safe close rate or non sale correctness rate
- scenario-level scores
- failure taxonomy hits

## Decision

The next checkpoint remains `PROD-041-conditional-simulation-review`.

PROD-041 should use the expanded traces to decide whether the conditional conversations are realistic enough to unblock voice playback, scenario branching, more seeds, or public demo polish.

## Boundary

PROD-041A does not call providers, call an LLM, read private data, download datasets, store raw transcripts, copy transcript text, export transcript-derived commercial runtime prompts, start a server, collect payment, enable retrieval by default, enable composer hooks by default, change runtime behavior, or allow production runtime promotion.
