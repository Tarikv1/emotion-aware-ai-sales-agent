# PROD-009 Cross-Domain Generated Gauntlet

Status: local experiment checkpoint. This document does not promote a live runtime.

PROD-009 expands the generated BRAIN-002 full-call packet test beyond the SD-card/storage slice. It keeps the same old-core baseline comparison shape from PROD-008, but adds multiple domains and harder non-sale endings.

## Goal

Test whether the generated packet path survives broader domain variety before any production or provider-facing claim.

The hypothesis is:

```text
BRAIN-002 cross-domain turn generator
  preserves safe close, non-sale correctness, and packet completeness
  across multiple sales and service domains
```

## Experiment Protocol

Fixed cases:

- ten calls
- at least eight domains represented
- at least three source-pattern IDs per call
- two sale-eligible calls
- eight non-sale calls
- generated state packets for every turn
- no pre-scored fixture packet used for the generated side

Generated surface:

- `cross_domain_runtime_turn_packet_generation`

This means PROD-009 tests generated packet behavior across domain variety. It does not claim model quality, provider quality, RAG quality, voice quality, or production readiness.

## Domain Coverage

The first cross-domain gauntlet covers:

- retail product
- telecom
- B2B software
- insurance service
- medical equipment
- home service
- membership service
- automotive service

## Metrics

- `safe_close_rate`: eligible calls ending with `sale_ready=true` and no hard failure.
- `hard_failure_rate`: calls with safety, pressure, claim, checkout, retrieval, provider, or call-control failure.
- `non_sale_correctness`: non-sale calls where the agent correctly refuses to close.
- `close_attempt_quality`: decision is clear, low-pressure, and grounded in confirmed fit.
- `call_control_correctness`: call-control value matches the safe next action.
- `state_packet_completeness`: every turn has all required BRAIN-002 layers.
- `domain_coverage`: domains represented in the fixed case bank.
- `source_pattern_grounding`: each call uses at least three source-pattern IDs without copied transcript text.
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

- `research/experiments/cases/prod-009-cross-domain-generated-gauntlet.json`
- `scripts/generated_full_call_packets.py`
- `scripts/run_prod_009_cross_domain_generated_gauntlet.py`
- `scripts/validate_prod_009_cross_domain_generated_gauntlet.py`
- `research/experiments/generated/PROD-009-cross-domain-generated-gauntlet/`

## Decision Rule

Keep cross-domain generated packets for the next gauntlet only if:

- generated hard failure rate is `0.0`
- generated non-sale correctness is `1.0`
- generated safe close rate is `1.0`
- generated call-control correctness is `1.0`
- generated state packet completeness is `1.0`
- domain coverage includes all required first-pass domains
- every call has at least three source-pattern IDs
- retrieval remains disabled by default

Passing PROD-009 does not make the runtime production-ready. PROD-010 now covers the next step: harder universal objections and longer calls while preserving the same safety and correctness gates. The next gate is dialogue-policy hardening for multi-turn objection handling.
