# PROD-046 Core Sales Policy Human Review

## Summary

PROD-046 is a review-only checkpoint over the deterministic runtime-policy surface produced by PROD-045 through PROD-046D.

It evaluates English and German response quality, call-control risk, campaign-field risk, and promotion readiness. It does not modify runtime behavior, enable retrieval, call providers, call LLMs, read private data, unblock voice playback, unblock public demo polish, allow payment collection, allow contract signing, or allow production promotion.

Tarik is not treated as the final German wording authority. German wording is accepted for synthetic regression evidence only until native-speaker/product review is completed.

## Local Commands

```powershell
python scripts\run_prod_046_core_sales_policy_human_review.py
python scripts\validate_prod_046_core_sales_policy_human_review.py
```

Recommended regression and guard commands:

```powershell
python scripts\validate_prod_045_core_sales_policy_regression_rerun.py
python scripts\validate_prod_046a_german_naturalized_policy_regression.py
python scripts\validate_prod_046b_german_response_wording_quality_pass.py
python scripts\validate_prod_046c_german_campaign_field_interpolation_guard.py
python scripts\validate_prod_046d_german_source_informed_wording_quality_guard.py
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
research\experiments\generated\PROD-046-core-sales-policy-human-review\
```

Artifacts:

- `result.json`
- `report.md`
- `human_review_packet.json`
- `english_response_quality_findings.json`
- `german_response_quality_findings.json`
- `call_control_findings.json`
- `campaign_field_findings.json`
- `recommended_next_actions.json`
- `prod_046_review.html`

## Review Result

The current policy surface is:

- accepted for offline regression evidence;
- accepted for internal product review;
- blocked from voice, public demo, and real customer use;
- ready for a campaign-profile contract validator next.

## Key Review Risks

- Some English responses still sound like internal policy output because they expose terms such as `approved`, `sales path`, or `sale-ready`.
- German responses pass deterministic source-informed wording guards, but still need native-speaker review.
- German support and cancellation responses still use `Verkaufsteil`, which is safer than the older wording but may still sound internal.
- Some safe end-call decisions may feel abrupt in spoken use.
- Campaign fields remain the main deterministic product bottleneck because field shape must be explicit before future campaigns.

## Boundary Status

- Runtime behavior changed: `false`
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

Recommended next checkpoint: `PROD-047-campaign-profile-contract-validator`.

Purpose: create deterministic validation for campaign/profile fields before adding future campaigns, voice playback, public demo use, or broader runtime promotion.
