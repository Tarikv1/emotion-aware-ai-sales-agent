# PROD-047 Campaign Profile Contract Validator

## Summary

PROD-047 creates a reusable deterministic campaign-profile contract and validator.

This is a campaign contract checkpoint, not a runtime behavior checkpoint. It prevents future campaign/profile fields from being used in guarded runtime policies unless they declare language, customer-facing field shape, source boundary, review status, and hard safety defaults.

## Local Commands

```powershell
python scripts\run_prod_047_campaign_profile_contract_validator.py
python scripts\validate_prod_047_campaign_profile_contract_validator.py
```

Recommended regression and guard commands:

```powershell
python scripts\validate_prod_045_core_sales_policy_regression_rerun.py
python scripts\validate_prod_046a_german_naturalized_policy_regression.py
python scripts\validate_prod_046b_german_response_wording_quality_pass.py
python scripts\validate_prod_046c_german_campaign_field_interpolation_guard.py
python scripts\validate_prod_046d_german_source_informed_wording_quality_guard.py
python scripts\validate_prod_046_core_sales_policy_human_review.py
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
research\experiments\generated\PROD-047-campaign-profile-contract-validator\
```

Artifacts:

- `result.json`
- `report.md`
- `campaign_contract_schema.json`
- `campaign_guard_matrix.json`
- `validation_cases.json`
- `validation_results.json`
- `campaign_profile_review.html`

Example profiles:

- `campaigns/examples/campaign-prod-047-valid-en-internal-review.json`
- `campaigns/examples/campaign-prod-047-valid-de-source-informed.json`
- `campaigns/examples/campaign-prod-047-invalid-de-fragment-interpolation.json`
- `campaigns/examples/campaign-prod-047-invalid-en-internal-copy.json`
- `campaigns/examples/campaign-prod-047-invalid-payment-enabled.json`
- `campaigns/examples/campaign-prod-047-invalid-missing-regulated-boundary.json`
- `campaigns/examples/campaign-prod-047-invalid-missing-native-review-status.json`
- `campaigns/examples/campaign-prod-047-invalid-sale-ready-without-close-criteria.json`
- `campaigns/examples/campaign-prod-047-invalid-support-cancellation-route-label.json`
- `campaigns/examples/campaign-prod-047-incomplete-identity-reason.json`

## Contract Rules

Campaigns must declare:

- language: `en` or `de`;
- field shape for every customer-facing field;
- source boundary for every field;
- language-specific review statuses;
- hard safety defaults.

Customer-facing field shapes are:

- `full_sentence`
- `noun_phrase`
- `route_label`
- `written_info_object`
- `boundary_sentence`
- `pricing_sentence`
- `identity_reason_sentence`
- `verification_sentence`
- `next_step_label`

Source boundaries are:

- `synthetic_test_fixture`
- `company_approved`
- `public_source_informed`
- `human_reviewed`
- `legal_review_required`
- `blocked`

Review statuses are:

- `machine_validated`
- `source_informed`
- `native_speaker_review_required`
- `native_speaker_reviewed`
- `legal_review_required`
- `approved_for_internal_demo`
- `approved_for_voice`
- `approved_for_customer_use`

## Policy Group Coverage

The guard matrix covers:

- `price_first`
- `identity_repair`
- `written_info_and_email_boundary`
- `scam_and_payment_safety`
- `support_and_cancellation_routing`
- `technical_security_handoff`
- `coverage_healthcare_boundary`
- `existing_provider_gap`
- `decision_maker_review`
- `sale_ready_guarded_next_step`
- `callback_request`
- `do_not_call`

## Boundary Status

- Runtime behavior changed: `false`
- Default campaign readiness: `blocked_for_voice`, `blocked_for_public_demo`, and `blocked_for_customer_use`
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

Recommended next checkpoint: `PROD-048-native-german-wording-review`.

Purpose: review the now-contract-guarded German campaign wording with a native German reviewer before voice, public demo, or real customer use.
