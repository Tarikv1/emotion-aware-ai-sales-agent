# PROD-001 Rule Baseline

## Status

Completed

## Date

2026-04-30

## Purpose

Run a deterministic, transparent rule baseline on the 12 product qualification simulation cases.

This baseline is intentionally simple. It gives future LLM or learned-agent runs a minimum product behavior target for:

- interest-state classification
- strategy selection
- appointment decisions
- escalation decisions
- do-not-call suppression

## Execution Mode

Scripted rule baseline using:

- `scripts/run_rule_baseline.py`
- `research/experiments/cases/prod-001-qualification-simulation.json`

Live model execution: `not-run`

## Outputs

- `research/experiments/generated/PROD-001/PROD-001-rule-baseline-results.json`
- `research/experiments/generated/PROD-001/PROD-001-rule-baseline-report.md`

## Aggregate Results

- Turn emotion matches: 18 / 32
- Turn interest-state matches: 32 / 32
- Turn strategy matches: 32 / 32
- Final call-status matches: 12 / 12
- Final interest-state matches: 12 / 12
- Final strategy matches: 12 / 12
- Final appointment matches: 12 / 12

## Interpretation

The baseline proves that the current 12-case product workflow can be handled by a transparent rule system for state, strategy, scheduling, and escalation decisions.

This is useful, but it also exposes a limitation:

- the rule-based emotion detector is weak and only matched 18 of 32 turn labels

That means future model-based work should not only aim to match the final outcome. It should also improve emotional-state detection and produce more natural responses while preserving the same guardrails.

## Decision

Keep.

Reason:

The rule baseline is a strong control condition for the product MVP workflow. It is interpretable, cheap to run, and gives the next LLM-based run a clear behavioral floor.

## Next Step

Use the rule baseline as the comparison point for a live model or stronger agent implementation.

The next candidate agent should be evaluated on:

- whether it preserves 12 / 12 final outcome correctness
- whether it improves emotion-label matching
- whether generated responses are more natural than rule templates
- whether guardrails remain intact
