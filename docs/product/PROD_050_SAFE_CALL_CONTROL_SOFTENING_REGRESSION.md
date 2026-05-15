# PROD-050 Safe Call-Control Softening Regression

## Summary

PROD-050 runs a deterministic proposed-softening regression for the `PROD-049` non-refusal bridge-then-continue candidates.

This checkpoint does not edit the live runtime. It tests the proposed call-control and response-text change as evidence first so older validated checkpoints remain intact until a dedicated runtime-update checkpoint deliberately migrates expectations.

## Local Commands

```powershell
python scripts\run_prod_050_safe_call_control_softening_regression.py
python scripts\validate_prod_050_safe_call_control_softening_regression.py
```

Recommended guard commands:

```powershell
python scripts\validate_prod_049_safe_end_call_bridge_continue_review.py
python scripts\validate_prod_048c_german_wording_feedback_patch.py
python scripts\validate_prod_047_campaign_profile_contract_validator.py
python scripts\validate_prod_046_core_sales_policy_human_review.py
python scripts\validate_prod_045_core_sales_policy_regression_rerun.py
python scripts\validate_realtime_turn_cli.py
python scripts\check_project_drift.py
python scripts\check_thesis_update_gate.py
python scripts\check_thesis_reference_registry.py
python scripts\check_setup.py
git diff --check
```

## Regression Scope

Selected proposed `bridge-then-continue` groups:

- `price-first-direct`
- `written-info-request`
- `stakeholder-review`
- `partner-review`

The regression preserves the approved answer content, removes terminal safe-close phrasing from the proposed response, adds a low-pressure optional continuation, and tests the proposed call-control move from `end-call` to `bridge-then-continue`.

## Protected Boundaries

These boundaries must remain unchanged:

- support route
- cancellation route
- do-not-call or hard refusal
- human request
- email-only boundary
- payment safety fear
- scam or card fear
- sale-ready guarded close
- callback request

## Outputs

Generated output directory:

```text
research\experiments\generated\PROD-050-safe-call-control-softening-regression\
```

Artifacts:

- `result.json`
- `report.md`
- `softening_regression_cases.json`
- `softening_regression_results.json`
- `protected_boundary_results.json`
- `proposed_runtime_change_summary.json`
- `prod_050_review.html`

## Boundary Status

- Runtime behavior changed: `false`
- Call-control behavior changed: `false`
- Retrieval enabled: `false`
- Provider calls made: `false`
- LLM used: `false`
- Private data read: `false`
- Voice playback unblocked: `false`
- Public demo polish unblocked: `false`
- Payment collection allowed: `false`
- Contract signing allowed: `false`
- Production runtime promotion allowed: `false`
- Response text change recommended: `true`
- Call-control definition update required: `true`

## Next Checkpoint

Recommended next checkpoint: `PROD-051-safe-call-control-runtime-update`.

Purpose: apply the proven call-control and response-text softening to the live deterministic runtime and deliberately migrate affected historical expectations while keeping protected boundaries unchanged.
