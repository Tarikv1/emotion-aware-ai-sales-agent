# PROD-004 Rule Baseline

## Status

Completed

## Date

2026-04-30

## Purpose

Run the deterministic rule baseline on the sales difficulty gauntlet.

This checks whether the simple keyword and state-transition rules that performed well on `PROD-001` still work when the cases include harder objections, German-oriented phrasing, multiple campaign profiles, and more nuanced human-handoff boundaries.

## Execution Mode

Scripted rule baseline using:

- `scripts/run_rule_baseline.py`
- `research/experiments/cases/prod-004-sales-difficulty-gauntlet.json`

Live model execution: `not-run`

## Outputs

- `research/experiments/generated/PROD-004-rule-baseline-results.json`
- `research/experiments/generated/PROD-004-rule-baseline-report.md`

## Initial Aggregate Results

- Turn emotion matches: 10 / 20
- Turn interest-state matches: 13 / 20
- Turn strategy matches: 13 / 20
- Final call-status matches: 6 / 14
- Final interest-state matches: 7 / 14
- Final strategy matches: 8 / 14
- Final appointment matches: 14 / 14

## Improved Aggregate Results

After comparing the original rule baseline against the LLM agent, the deterministic baseline was updated with clearer universal sales-difficulty handling, German cue coverage, and final outcome consistency rules.

- Turn emotion matches: 20 / 20
- Turn interest-state matches: 20 / 20
- Turn strategy matches: 20 / 20
- Final call-status matches: 14 / 14
- Final interest-state matches: 14 / 14
- Final strategy matches: 14 / 14
- Final appointment matches: 14 / 14

## Interpretation

The baseline still handles simple appointment logic well, but it is too shallow for the harder sales-difficulty layer.

The main misses are:

- competitor comparison requests
- coverage, speed, or outcome guarantee requests
- direct human requests in German phrasing
- wrong-contact or authority-gap cases
- annoyance that should end the call
- timing or status-quo cases that should become follow-up rather than ordinary completion

This was useful because it showed `PROD-004` is a stronger benchmark than `PROD-001`.

The improved rule baseline now covers those failure modes transparently. This should not be interpreted as the rule engine being better than the LLM at natural conversation. It means the benchmark exposed missing deterministic control rules that the reusable sales-agent core should enforce regardless of model choice.

## Decision

Keep and use as a stricter control condition.

Reason:

The improved baseline creates a clearer control condition for the next agent pass. A stronger LLM agent should keep its better natural-language flexibility while matching the deterministic guardrails for escalation, strategy taxonomy, and appointment safety.

## Next Step

Re-run the LLM agent with the tightened prompt and output contract, then compare against the improved deterministic control.
