# PROD-046A German Naturalized Policy Regression

## Summary

PROD-046A is a German de-DE regression checkpoint for the PROD-045 runtime-policy surface.

It does not translate the English PROD-045 cases literally. It creates synthetic, project-owned, intent-equivalent German customer utterances that preserve the same customer intent and `customer_move_id`, then runs them through the deterministic realtime turn policy.

## Local Commands

```powershell
python scripts\run_prod_046a_german_naturalized_policy_regression.py
python scripts\validate_prod_046a_german_naturalized_policy_regression.py
```

Recommended regression and guard commands:

```powershell
python scripts\run_prod_045_core_sales_policy_regression_rerun.py
python scripts\validate_prod_045_core_sales_policy_regression_rerun.py
python scripts\validate_realtime_turn_cli.py
python scripts\check_project_drift.py
python scripts\check_thesis_update_gate.py
python scripts\check_thesis_reference_registry.py
```

## Outputs

Generated output directory:

```text
research\experiments\generated\PROD-046A-german-naturalized-policy-regression\
```

Artifacts:

- `result.json`
- `report.md`
- `german_regression_cases.json`
- `german_regression_results.json`
- `german_false_positive_cases.json`
- `german_false_positive_results.json`
- `german_policy_review_data.json`
- `german_policy_review.html`

## Coverage

The checkpoint covers at least three natural German de-DE utterance variants for each PROD-045 policy move:

- price-first direct answer
- identity repair
- written-info request
- email-only boundary
- scam/card fear
- payment safety fear
- support route
- cancellation route
- technical specialist route
- security review route
- coverage boundary
- sensitive healthcare boundary
- existing-provider gap isolation
- manager approval
- spouse/partner review
- sale-ready interest
- not interested
- hostile rejection
- callback request
- claim-boundary proof request
- product-detail lookup
- scheduling confirmation

False-positive German cases also check negated cancellation, negated scam, price-over-support priority, negated security, payment-safety wording, and price-over-existing-provider priority.

## Boundary Status

- Runtime behavior changed: `true`
- German phrase triggers added: `true`
- German localized responses changed: `true`
- Retrieval enabled: `false`
- Provider calls made: `false`
- LLM used: `false`
- Private data read: `false`
- Payment collection allowed: `false`
- Contract signing allowed: `false`
- Production runtime promotion allowed: `false`
- Voice playback unblocked: `false`
- Public demo polish unblocked: `false`

## Review Note

The German cases are labeled as `synthetic_naturalized_de_regression_case` or `synthetic_naturalized_de_false_positive_case`. They are not CallCenterEN transcript text, not external German sales scripts, and not literal translations of English cases.

Next recommended checkpoint: `PROD-046-core-sales-policy-human-review`.
