# PROD-051 Safe Call-Control Runtime Update

## Summary

PROD-051 applies the PROD-050-proven `bridge-then-continue` softening to the live deterministic runtime for selected non-refusal cases only.

This checkpoint validates naturalness more deeply than artifact review. It freezes the PROD-050 cases, compares baseline versus live runtime on the same inputs, and scores every live response with a deterministic spoken-call naturalness rubric.

Exact spoken-response acceptance is now separated from this runtime gate. Use `PROD-052-language-lane-review-separation` for language-lane review state and `PROD-053E-english-runtime-wording-patch` for the currently promoted English wording. The PROD-051 validator may accept later explicitly reviewed response text while keeping call control, next action, protected boundaries, and naturalness gates strict.

## Local Commands

```powershell
python scripts\run_prod_051_safe_call_control_runtime_update.py
python scripts\validate_prod_051_safe_call_control_runtime_update.py
```

Recommended guard commands:

```powershell
python scripts\validate_prod_050_safe_call_control_softening_regression.py
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

## Runtime Scope

Live runtime softening is allowed only for these selected non-refusal groups:

- `price-first-direct`
- `written-info-request`
- `stakeholder-review`
- `partner-review`

The live next action for these groups is `answer-and-continue`; the live call control is `bridge-then-continue`.

## Naturalness Rubric

Each selected live response must pass:

- direct answer or acknowledgement
- optional low-pressure continuation
- no terminal closing phrase
- no internal jargon
- spoken sentence shape
- customer-move fit
- language-specific naturalness
- no pressure, payment, contract, or unsupported claim

The audit also compares each live response against the baseline PROD-050 current-runtime response on the same case and requires a positive naturalness score delta.

## Protected Boundaries

These paths must remain unchanged:

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
research\experiments\generated\PROD-051-safe-call-control-runtime-update\
```

Artifacts:

- `result.json`
- `report.md`
- `runtime_update_results.json`
- `naturalness_audit_results.json`
- `protected_boundary_results.json`
- `before_after_naturalness.json`
- `prod_051_review.html`

## Boundary Status

- Runtime behavior changed: `true`
- Call-control behavior changed: `true`
- Response text behavior changed: `true`
- Retrieval enabled: `false`
- Provider calls made: `false`
- LLM used: `false`
- Private data read: `false`
- Voice playback unblocked: `false`
- Public demo polish unblocked: `false`
- Payment collection allowed: `false`
- Contract signing allowed: `false`
- Production runtime promotion allowed: `false`
