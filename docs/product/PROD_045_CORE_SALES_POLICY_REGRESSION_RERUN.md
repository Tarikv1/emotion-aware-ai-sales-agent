# PROD-045 Core Sales Policy Regression Rerun

## Summary

PROD-045 applies the targeted runtime-policy updates that PROD-044 justified, but only behind deterministic regression checks.

The checkpoint hardens the evaluator first: the old generic response, `Thanks. May I ask one quick clarifying question?`, must fail customer moves that require a direct answer, safety boundary, support route, specialist handoff, channel boundary, or guarded next step.

Runtime behavior changed only in the deterministic realtime turn policy surface. Retrieval remains disabled, providers and LLMs are not called, private data is not read, voice playback is not unblocked, and public demo polish is not unblocked.

## Local Commands

```powershell
python scripts\run_prod_045_core_sales_policy_regression_rerun.py
python scripts\validate_prod_045_core_sales_policy_regression_rerun.py
```

Recommended guard commands:

```powershell
python scripts\validate_realtime_turn_cli.py
python scripts\check_project_drift.py
python scripts\check_thesis_update_gate.py
python scripts\check_thesis_reference_registry.py
```

## Outputs

Generated output directory:

```text
research\experiments\generated\PROD-045-core-sales-policy-regression-rerun\
```

Artifacts:

- `result.json`
- `report.md`
- `regression_cases.json`
- `regression_results.json`
- `evaluator_hardening_results.json`
- `runtime_policy_change_summary.json`
- `prod_045_review_data.json`
- `prod_045_review.html`

## Applied Runtime Policy Updates

- `policy-price-first-direct-answer`
- `policy-written-info-and-email-boundary`
- `policy-identity-repair-before-discovery`
- `policy-payment-and-scam-safety-boundary`
- `policy-support-and-cancellation-routing`
- `policy-specialist-handoff-for-technical-security-healthcare`
- `policy-existing-provider-gap-isolation`
- `policy-decision-maker-review-path`
- `policy-sale-ready-interest-guarded-next-step`

## Campaign-Fact Guard Rule

The reusable core must not invent product facts. When approved campaign/profile fields exist, the runtime may use them. When required fields are missing, the runtime must return a safe boundary response or route to an approved human/specialist path.

Guarded areas include pricing facts, written summaries, caller identity, no-payment boundaries, verification paths, support and cancellation routes, technical scope, specialist handoff, coverage/healthcare boundaries, provider-gap wording, decision-maker review summaries, and sale-ready close criteria.

## Validation Gates

The validator checks that:

- generic clarification fails required-boundary moves;
- price-first does not pass without pricing facts or a pricing-boundary statement;
- send-info and email-only do not pass without written/channel boundary;
- scam/payment fears do not pass without no-payment/no-card and safe verification/written path;
- support and cancellation stop the sales path and route safely;
- technical, security, coverage, and healthcare turns use approved scope or specialist/qualified-reviewer routing;
- sale-ready interest uses guarded next-step behavior and never collects payment or implies contract signing;
- accepted behaviors for refusal, callback, claim boundary, product-detail lookup, scheduling, and sale-ready logging do not regress.

## Boundary Status

- Runtime behavior changed: `true`
- Retrieval enabled: `false`
- Provider calls made: `false`
- LLM used: `false`
- Private data read: `false`
- Dataset download performed: `false`
- Production runtime promotion allowed: `false`
- Voice playback unblocked: `false`
- Public demo polish unblocked: `false`
- Payment collection allowed: `false`
- Contract signing allowed: `false`

## Next Checkpoint

Recommended next checkpoint: `PROD-046-core-sales-policy-human-review`.

Purpose: review the regression-gated runtime policy changes against product expectations before any broader runtime promotion, demo claim, voice playback unlock, or retrieval default change.
