# PROD-044 Core Sales Policy Update

## Summary

`PROD-044-core-sales-policy-update` is an offline review/design checkpoint. It reviews PROD-043 evidence, probes the current deterministic realtime turn entrypoint with PROD-043 synthetic generic single-turn cases, and identifies targeted core sales-policy updates that are justified.

This checkpoint does not apply runtime changes. Runtime behavior changed: `false`. Retrieval enabled: `false`.

## Local Commands

```powershell
python scripts\run_prod_044_core_sales_policy_update.py
python scripts\validate_prod_044_core_sales_policy_update.py
```

## Inputs

- `research/experiments/generated/PROD-043-sales-playbook-runtime-adapter/result.json`
- `research/experiments/generated/PROD-043-sales-playbook-runtime-adapter/report.md`
- `research/experiments/generated/PROD-043-sales-playbook-runtime-adapter/agent_response_evaluations.json`
- `research/experiments/generated/PROD-043-sales-playbook-runtime-adapter/runtime_adapter_review_data.json`
- Runtime architecture references:
  - `runtime/architecture/REALTIME_AGENT_ARCHITECTURE.md`
  - `docs/brain/BRAIN_002_RUNTIME_STATE_SCHEMA.md`
  - `scripts/run_realtime_turn_simulation.py`
  - `scripts/realtime_turn_cli.py`

## Outputs

- `research/experiments/generated/PROD-044-core-sales-policy-update/result.json`
- `research/experiments/generated/PROD-044-core-sales-policy-update/report.md`
- `research/experiments/generated/PROD-044-core-sales-policy-update/core_sales_policy_review_packet.json`
- `research/experiments/generated/PROD-044-core-sales-policy-update/prod_044_review_data.json`
- `research/experiments/generated/PROD-044-core-sales-policy-update/prod_044_review.html`

## Candidate Policy Updates

The generated packet lists candidate policy updates only when PROD-043 evidence plus current offline runtime probes justify them. Candidate updates are marked `candidate_not_applied` and include required campaign-fact guards and deterministic regression requirements.

The current packet identifies targeted candidates for price-first direct answers, written-info/email-only boundaries, identity repair, payment/scam safety, support/cancellation routing, specialist handoff boundaries, existing-provider gap isolation, and decision-maker review paths.

## Blocked Updates

PROD-044 blocks retrieval defaults, broad product claims, voice playback, public demo polish, payment or contract closes, full synthetic conversations, and runtime changes without regression coverage.

## Boundary

- Runtime behavior changed: `false`
- Retrieval enabled: `false`
- Runtime agent modified: `false`
- Provider calls made: `false`
- LLM used: `false`
- Private data read: `false`
- Dataset download performed: `false`
- Production runtime promotion allowed: `false`

## Next Checkpoint

Recommended next checkpoint: `PROD-045-core-sales-policy-regression-rerun`.

Purpose: apply only the justified policy changes behind deterministic regression tests, still without enabling retrieval by default or changing provider/private-data boundaries.
