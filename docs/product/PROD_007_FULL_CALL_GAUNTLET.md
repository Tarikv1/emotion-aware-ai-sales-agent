# PROD-007 Full-Call Gauntlet

Status: local experiment checkpoint. This document does not promote a live runtime.

PROD-007 compares the older pre-full-sale core against a BRAIN-002/full-sale candidate on the same fixed calls.

## Goal

Test whether the new runtime state contract helps the agent make better full-call decisions, not just better single-turn wording.

The hypothesis is:

```text
BRAIN-002/full-sale candidate
  improves safe sale-ready decisions and non-sale correctness
  without increasing hard failures
```

## Experiment Protocol

Fixed cases:

- same calls
- same turn summaries
- same expected outcomes
- same scoring rules

Baseline:

- `old_core_pre_full_sale`
- appointment/qualification-oriented behavior before the explicit full-sale state packet

Candidate:

- `brain_002_full_sale_candidate`
- uses the BRAIN-002 packet shape with buyer state, strategy, safety, call control, retrieval status, voice profile, response, and evidence log

Editable surface:

- `runtime_state_decision_packet`

This means PROD-007 does not claim a better model, better provider, better RAG registry, or better voice. It tests whether the state contract makes the right decision easier to score.

## Metrics

- `safe_close_rate`: eligible calls ending with `sale_ready=true` and no hard failure.
- `hard_failure_rate`: calls with safety, pressure, claim, checkout, retrieval, provider, or call-control failure.
- `non_sale_correctness`: non-sale calls where the agent correctly refuses to close.
- `close_attempt_quality`: decision is clear, low-pressure, and grounded in confirmed fit.
- `call_control_correctness`: call-control value matches the safe next action.
- `retrieval_default_off`: retrieval remains disabled unless a later gate enables it.
- `latency_readiness`: fixture-level decision path stays under the acceptable decision budget.

## Fixed Call Types

The first gauntlet uses six PROD-006-style SD-card calls:

- sale eligible
- compatibility unclear
- support only
- complaint recovery
- human escalation
- unsafe for closing / stop request

This is intentionally small. It is a convergence checkpoint, not final product evidence.

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

- `research/experiments/cases/prod-007-full-call-gauntlet.json`
- `scripts/full_call_gauntlet.py`
- `scripts/run_prod_007_full_call_gauntlet.py`
- `scripts/validate_prod_007_full_call_gauntlet.py`
- `research/experiments/generated/PROD-007-full-call-gauntlet/`

## Decision Rule

Keep the BRAIN-002 candidate for the next gauntlet only if:

- candidate hard failure rate is `0.0`
- candidate non-sale correctness is `1.0`
- candidate safe close rate improves over baseline
- candidate call-control correctness improves over baseline
- retrieval remains disabled by default

Passing PROD-007 does not make the candidate production-ready. PROD-008 now covers the next step: generated full-call packets where local runtime-style logic produces BRAIN-002 state from each turn. The next gate is broader generated gauntlet coverage across more domains before any client-facing claim.
