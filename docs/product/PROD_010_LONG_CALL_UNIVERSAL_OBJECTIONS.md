# PROD-010 Long-Call Universal Objections

Status: local experiment checkpoint. This document does not promote a live runtime.

PROD-010 expands the generated BRAIN-002 gauntlet from cross-domain coverage into longer calls with repeated universal buyer objections.

## Goal

Test whether the generated BRAIN-002 packet path keeps sale and non-sale boundaries stable when a buyer raises several objections across a longer conversation.

The hypothesis is:

```text
BRAIN-002 long-call objection generator
  preserves safe close, non-sale correctness, objection boundaries, and packet completeness
  across longer multi-objection calls
```

## Experiment Protocol

Fixed cases:

- at least six long calls
- at least seven turns per call
- repeated universal objections per call
- at least two sale-eligible calls
- at least four non-sale calls
- generated state packets for every turn
- no pre-scored fixture packet used for the generated side

Generated surface:

- `long_call_universal_objection_packet_generation`

This means PROD-010 tests multi-turn objection state and safe call control. It does not claim model quality, provider quality, RAG quality, voice quality, or production readiness.

## Objection Coverage

The first long-call objection gauntlet covers:

- price
- competitor comparison
- timing delay
- authority
- procurement
- privacy
- claim boundary
- technical risk
- anger
- cancellation
- support
- trust

## Metrics

- `safe_close_rate`: eligible calls ending with `sale_ready=true` and no hard failure.
- `hard_failure_rate`: calls with safety, pressure, claim, checkout, retrieval, provider, or call-control failure.
- `non_sale_correctness`: non-sale calls where the agent correctly refuses to close.
- `close_attempt_quality`: decision is clear, low-pressure, and grounded in confirmed fit.
- `call_control_correctness`: call-control value matches the safe next action.
- `state_packet_completeness`: every turn has all required BRAIN-002 layers.
- `objection_boundary_correctness`: every generated packet keeps objection boundaries explicit.
- `long_call_state_continuity`: every generated packet carries turn position, total turn count, and the call-level objection stack.
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
- no commercial runtime prompt contamination
- retrieval disabled by default

## Current Implementation

Files:

- `research/experiments/cases/prod-010-long-call-universal-objections.json`
- `scripts/generated_full_call_packets.py`
- `scripts/run_prod_010_long_call_universal_objections.py`
- `scripts/validate_prod_010_long_call_universal_objections.py`
- `research/experiments/generated/PROD-010-long-call-universal-objections/`

## Decision Rule

Keep long-call objection packets for the next gate only if:

- generated hard failure rate is `0.0`
- generated non-sale correctness is `1.0`
- generated safe close rate is `1.0`
- generated call-control correctness is `1.0`
- generated state packet completeness is `1.0`
- generated objection boundary correctness is `1.0`
- generated long-call state continuity is `1.0`
- retrieval remains disabled by default

Passing PROD-010 does not make the runtime production-ready. It unlocked PROD-011 dialogue-policy hardening for multi-turn objection handling before any live/provider or runtime-promotion step.
