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

## Aggregate Results

- Turn emotion matches: 10 / 20
- Turn interest-state matches: 13 / 20
- Turn strategy matches: 13 / 20
- Final call-status matches: 6 / 14
- Final interest-state matches: 7 / 14
- Final strategy matches: 8 / 14
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

This is useful because it shows `PROD-004` is a stronger benchmark than `PROD-001`.

## Decision

Keep.

Reason:

This creates a meaningful control condition for the next agent pass. A stronger rule engine or LLM agent should improve escalation, emotion, and strategy matching while preserving the appointment guardrail.

## Next Step

Evaluate whether an LLM-based agent improves over this baseline on the same `PROD-004` packet without weakening guardrails or over-scheduling.
