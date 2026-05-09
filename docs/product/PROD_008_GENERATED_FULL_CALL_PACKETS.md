# PROD-008 Generated Full-Call Packets

Status: local experiment checkpoint. This document does not promote a live runtime.

PROD-008 keeps the PROD-007 call set fixed, but removes the pre-scored BRAIN-002 packet shortcut from the case file. The runner now creates one BRAIN-002 state packet per turn from runtime-style turn signals, then scores the final call outcome.

## Goal

Test whether the BRAIN-002 state contract can be produced by local runtime logic, not just copied from fixture answers.

The hypothesis is:

```text
BRAIN-002 runtime turn generator
  preserves the PROD-007 safe close and non-sale correctness gains
  while generating complete state packets for every turn
```

## Experiment Protocol

Fixed cases:

- same six calls as the PROD-007 first gauntlet shape
- same expected outcomes
- same baseline behavior
- generated state packets for every turn
- no pre-scored fixture packet used for the generated side

Generated surface:

- `runtime_turn_packet_generation`

This means PROD-008 tests packet generation and call scoring. It does not claim a better model, better provider, better RAG registry, better voice, or production-ready sales behavior.

## Metrics

- `safe_close_rate`: eligible calls ending with `sale_ready=true` and no hard failure.
- `hard_failure_rate`: calls with safety, pressure, claim, checkout, retrieval, provider, or call-control failure.
- `non_sale_correctness`: non-sale calls where the agent correctly refuses to close.
- `close_attempt_quality`: decision is clear, low-pressure, and grounded in confirmed fit.
- `call_control_correctness`: call-control value matches the safe next action.
- `state_packet_completeness`: every turn has all required BRAIN-002 layers.
- `retrieval_default_off`: retrieval remains disabled unless a later gate enables it.
- `latency_readiness`: generated packet path stays under the acceptable decision budget.

## Boundaries

Default run:

- no provider calls
- no private data reads
- no customer audio
- no transcript body storage
- no dataset download
- no payment handling
- no checkout handling
- no runtime behavior change
- retrieval disabled by default

## Current Implementation

Files:

- `research/experiments/cases/prod-008-generated-full-call-packets.json`
- `scripts/generated_full_call_packets.py`
- `scripts/run_prod_008_generated_full_call_packets.py`
- `scripts/validate_prod_008_generated_full_call_packets.py`
- `research/experiments/generated/PROD-008-generated-full-call-packets/`

## Decision Rule

Keep generated packets for the next gauntlet only if:

- generated hard failure rate is `0.0`
- generated non-sale correctness is `1.0`
- generated safe close rate improves over baseline
- generated call-control correctness is `1.0`
- generated state packet completeness is `1.0`
- retrieval remains disabled by default

Passing PROD-008 does not make the runtime production-ready. PROD-009 now expands the generated full-call gauntlet beyond SD-card/storage scenarios while preserving the same safety and correctness gates. The next step is harder universal objections and longer calls.
