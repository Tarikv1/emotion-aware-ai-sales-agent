# PROD-021 Live-Shaped Dialogue-Policy Simulation

Status: completed local checkpoint.

PROD-021 tests whether the `PROD-020` opt-in runtime composer-hook gain survives live-shaped, multi-turn dialogue flow against the `PROD-011` hardened dialogue-policy expectations.

The checkpoint records exact customer turns, exact agent answers, retrieval status, hook decisions, policy traces, call-control traces, and state traces. It does not promote retrieval or composer hooks to default behavior.

## Boundary

- Local/offline only.
- Synthetic live-shaped customer turns only.
- No provider calls.
- No LLM calls.
- No private data reads.
- No dataset download.
- No raw CallCenterEN transcript text.
- No commercial runtime prompt contamination.
- Retrieval default enabled: `false`.
- Composer hook flag default enabled: `false`.

## Files

```text
research/experiments/cases/prod-021-live-shaped-dialogue-policy-simulation.json
scripts/prod_021_live_shaped_dialogue_policy_simulation.py
scripts/run_prod_021_live_shaped_dialogue_policy_simulation.py
scripts/validate_prod_021_live_shaped_dialogue_policy_simulation.py
research/experiments/generated/PROD-021-live-shaped-dialogue-policy-simulation/result.json
research/experiments/generated/PROD-021-live-shaped-dialogue-policy-simulation/report.md
```

## Current Result

- Calls: `7`
- Customer turns: `19`
- Protected turns: `9`
- Retrieval-only total score: `98`
- Opt-in total score: `112`
- Opt-in score delta vs retrieval-only: `14`
- Opt-in wins vs retrieval-only: `4`
- Retrieval-only wins vs opt-in: `0`
- Opt-in hooked answers: `4`
- Policy action correctness: `0.4737`
- Call-control correctness: `0.8421`
- Protected context preservation: `1.0`
- State reference completeness: `1.0`
- Non-sale correctness: `1.0`
- Safe-close correctness: `1.0`
- Hard failure rate: `0.0`
- Payment collection count: `0`
- Leakage finding count: `0`
- PROD-021 gate passed: `false`
- Decision: `revise_before_runtime_promotion_keep_hooks_opt_in`

## Interpretation

The opt-in hooks still improved specific live-shaped turns, and protected/non-sale boundaries stayed clean. That supports keeping the hooks as an opt-in candidate.

The gate does not pass because the current runtime policy layer does not fully match the hardened multi-turn dialogue policy. The biggest remaining gaps are policy-action coverage and call-control alignment, not hook safety.

This blocks runtime promotion. The next product step should review the exact PROD-021 turn traces and decide the narrowest runtime-policy or composer-state changes needed before any bounded demo integration.
