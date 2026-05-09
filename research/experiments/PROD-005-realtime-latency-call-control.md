# PROD-005 Realtime Latency And Call-Control Simulation

## Status

Completed.

## Purpose

PROD-005 tests the real-time runtime behavior of the sales-agent core.

This is not another product-category expansion. It checks whether the agent can choose the right customer-facing response mode quickly while keeping specialist/background modules out of the live critical path.

## Scope

The case set covers:

- fast-path objection handling
- bridge response for product-detail lookup
- do-not-call hang-up
- voicemail handling
- human-request escalation
- schedule-and-end behavior
- vague callback follow-up
- claim-boundary escalation
- repeated-silence call closure

## Files

- Case file: `research/experiments/cases/prod-005-realtime-latency-call-control.json`
- Runner: `scripts/run_realtime_turn_simulation.py`
- Validator: `scripts/validate_prod_005_realtime_latency.py`
- Results JSON: `research/experiments/generated/PROD-005/PROD-005-realtime-results.json`
- Report: `research/experiments/generated/PROD-005/PROD-005-realtime-report.md`

## Aggregate Results

- Cases: 9
- Response-mode matches: 9 / 9
- First-response latency-bucket matches: 9 / 9
- Background-module matches: 9 / 9
- Emotion matches: 9 / 9
- Sales-difficulty matches: 9 / 9
- Interest-state matches: 9 / 9
- Strategy matches: 9 / 9
- Next-action matches: 9 / 9
- Call-control matches: 9 / 9
- Response-language matches: 9 / 9
- Live-path sub-agent violations: 0

## Interpretation

The benchmark confirms the intended runtime design:

- ordinary turns use the fast path
- lookup-heavy turns produce a bridge response before background work
- do-not-call, voicemail, repeated silence, and refusal cases end cleanly
- human requests and unsupported-claim boundaries transfer or escalate quickly
- exact scheduling can use `schedule-and-end`
- no case requires a live chain of sub-agents before the first response
- active German and English campaign profiles keep responses in the configured campaign language

## Next Step

Use PROD-005 as the control benchmark before building a live voice prototype.

The next technical step is to connect this deterministic runtime policy to a turn-level prototype that accepts live or simulated speech transcripts and measures actual elapsed time instead of latency buckets.
