# PROD-011 Dialogue-Policy Hardening

Status: local experiment checkpoint. This document does not promote a live runtime.

PROD-011 dialogue-policy hardening turns the PROD-010 long-call BRAIN-002 packet evidence into a compact rule layer for choosing safe policy actions across multi-turn objections.

## Goal

Test whether the agent can keep a stable policy decision through longer objection stacks before any runtime promotion.

The hypothesis is:

```text
BRAIN-002 dialogue-policy hardening
  preserves safe close, non-sale correctness, policy action correctness,
  objection stack preservation, and blocked action avoidance
  across the PROD-010 long-call objection set
```

## Experiment Protocol

Fixed cases:

- seven PROD-010 long-call scenarios
- forty-nine turns
- one policy decision per turn
- PROD-010 packet references preserved per decision
- no new runtime response path
- retrieval disabled by default
- fixture candidate packets used: false

Generated surface:

- `dialogue_policy_rules`

This means PROD-011 tests policy routing over existing packet evidence. It does not claim model quality, provider quality, RAG quality, voice quality, or production readiness.

## Policy Actions

The first hardening pass keeps the action space small:

- `clarify-fit`
- `value-clarify`
- `fair-compare`
- `autonomy-check`
- `stakeholder-review`
- `procurement-review`
- `claim-boundary-escalation`
- `privacy-safe-escalation`
- `technical-escalation`
- `support-first-escalation`
- `trust-repair`
- `close-and-log-sale-ready`
- `end-call`

The policy is conservative: unresolved authority, procurement, privacy, claim, technical, support, anger, or refusal signals block a close even when interest is present.

## Metrics

- `safe_close_rate`: eligible calls ending with `sale_ready=true` and no hard failure.
- `hard_failure_rate`: calls with pressure, unsafe reassurance, support-to-sales drift, refusal pressure, retrieval, provider, or call-control failure.
- `non_sale_correctness`: non-sale calls where the agent correctly refuses to close.
- `policy action correctness`: every turn chooses the expected safe policy action.
- `blocked action avoidance`: every turn avoids the known bad motion for that objection state.
- `objection stack preservation`: every decision carries the call-level objection stack from PROD-010.
- `state_reference_completeness`: every policy decision references the source checkpoint, call, turn, and turn position.
- `call_control_correctness`: final call-control value matches the safe next action.
- `latency_readiness`: policy decision stays below the acceptable decision budget.

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

- `research/experiments/cases/prod-011-dialogue-policy-hardening.json`
- `scripts/dialogue_policy_hardening.py`
- `scripts/run_prod_011_dialogue_policy_hardening.py`
- `scripts/validate_prod_011_dialogue_policy_hardening.py`
- `research/experiments/generated/PROD-011-dialogue-policy-hardening/`

## Decision Rule

Keep dialogue-policy hardening for runtime design only if:

- hardened hard failure rate is `0.0`
- hardened non-sale correctness is `1.0`
- hardened safe close rate is `1.0`
- hardened policy action correctness is `1.0`
- hardened blocked action avoidance is `1.0`
- hardened objection stack preservation is `1.0`
- hardened state reference completeness is `1.0`
- hardened call-control correctness is `1.0`
- retrieval remains disabled by default

Passing PROD-011 does not make the runtime production-ready. It unlocks a later live-shaped transcript or simulation gate, still with retrieval default-off and no provider usage by default.
