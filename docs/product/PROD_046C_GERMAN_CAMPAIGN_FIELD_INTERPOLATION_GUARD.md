# PROD-046C German Campaign Field Interpolation Guard

## Summary

PROD-046C is a narrow German interpolation guard checkpoint after PROD-046B.

PROD-046B removed banned internal German route/policy terms, but generated runtime outputs still showed malformed campaign-field interpolation such as `bei beim` and `um ein kurzer Abgleich`. PROD-046C fixes those customer-facing string assembly problems without expanding runtime policy, retrieval, providers, voice, or demo scope.

## Local Commands

```powershell
python scripts\run_prod_046c_german_campaign_field_interpolation_guard.py
python scripts\validate_prod_046c_german_campaign_field_interpolation_guard.py
```

Recommended regression and guard commands:

```powershell
python scripts\run_prod_045_core_sales_policy_regression_rerun.py
python scripts\validate_prod_045_core_sales_policy_regression_rerun.py
python scripts\run_prod_046a_german_naturalized_policy_regression.py
python scripts\validate_prod_046a_german_naturalized_policy_regression.py
python scripts\run_prod_046b_german_response_wording_quality_pass.py
python scripts\validate_prod_046b_german_response_wording_quality_pass.py
python scripts\validate_realtime_turn_cli.py
python scripts\check_project_drift.py
python scripts\check_thesis_update_gate.py
python scripts\check_thesis_reference_registry.py
python scripts\check_setup.py
git diff --check
```

## Outputs

Generated output directory:

```text
research\experiments\generated\PROD-046C-german-campaign-field-interpolation-guard\
```

Artifacts:

- `result.json`
- `report.md`
- `german_interpolation_cases.json`
- `german_interpolation_results.json`
- `german_interpolation_before_after.json`
- `german_interpolation_review_data.json`
- `german_interpolation_review.html`

## Guard Scope

The checkpoint validates that German customer-facing runtime responses do not contain malformed interpolation or internal wording such as:

- `bei beim`
- `bei bei`
- `um ein kurzer`
- `um ein Abgleich`
- `um der Grund`
- `Support-Warteschlange`
- `Kündigungs-Warteschlange`
- `freigegebener Spezialistenweg`
- `freigegebenen Spezialistenweg`
- `sichere Passungsfrage`
- `Überlegenheitsaussage`
- `sale-ready`
- `freigegebene Übergabe`

It also separates positive required-boundary unknown/generic counts from false-positive unknown/generic counts, so intentional false-positive fallbacks do not hide required-boundary failures.

## Boundary Status

- Runtime behavior changed: `true`
- Retrieval enabled: `false`
- Provider calls made: `false`
- LLM used: `false`
- Private data read: `false`
- Voice playback unblocked: `false`
- Public demo polish unblocked: `false`
- Payment collection allowed: `false`
- Contract signing allowed: `false`
- Production runtime promotion allowed: `false`

## Next Checkpoint

Recommended next checkpoint: `PROD-046-core-sales-policy-human-review`.

Purpose: inspect English and German runtime-policy behavior, including German wording, before any broader runtime promotion, demo claim, voice playback unlock, or retrieval default change.
