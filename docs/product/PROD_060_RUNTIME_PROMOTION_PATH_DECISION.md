# PROD-060 Runtime Promotion Path Decision

## Summary

`PROD-060` records the path decision after human acceptance of `PROD-059`.

Decision: `select_internal_guarded_english_baseline_only`.

Selected path: `internal_guarded_english_baseline_only`.

Allowed scope: `local_offline_synthetic_internal_regression_reference`.

Plain-language scope: local offline synthetic internal regression reference.

This is not production promotion. It does not change runtime behavior, response text, German behavior, retrieval, provider calls, LLM use, private-data handling, voice playback, payment handling, contract signing, public demo use, real customer use, legal readiness, or production runtime promotion.

## Source Evidence

- Source readiness checkpoint: `PROD-059-final-english-only-runtime-readiness-review`
- Source readiness status: `ready_with_exclusions`
- Source readiness decision: `english_only_runtime_ready_with_exclusions`
- Source review HTML: `research\experiments\generated\PROD-059-final-english-only-runtime-readiness-review\prod_059_review.html`
- Source stable guard command: `python scripts\validate_english_multi_turn_regression_guard.py`

## Selected Path

The bounded English deterministic runtime surface can be treated as an internal, local/offline, synthetic regression reference.

That means it can be used to anchor future local QA and checkpoint evidence, but not to claim public demo readiness, live customer readiness, provider readiness, legal readiness, payment readiness, contract readiness, German readiness, retrieval readiness, voice readiness, or production runtime readiness.

## Rejected Paths

The following paths remain blocked:

- `public_demo_path`
- `real_customer_path`
- `provider_or_private_data_path`
- `retrieval_default_path`
- `voice_playback_path`
- `german_language_path`
- `payment_or_contract_path`
- `production_runtime_path`

## Local Commands

```powershell
python scripts\run_prod_060_runtime_promotion_path_decision.py
python scripts\validate_prod_060_runtime_promotion_path_decision.py
```

## Result

- Human review acceptance recorded: `true`
- Path decision only: `true`
- Source readiness status: `ready_with_exclusions`
- Selected path: `internal_guarded_english_baseline_only`
- Allowed scope: `local_offline_synthetic_internal_regression_reference`
- Blocked paths: `8`
- Still-blocked blockers: `14`
- Review HTML with examples: `research\experiments\generated\PROD-060-runtime-promotion-path-decision\prod_060_review.html`
- Requires human review before next checkpoint: `true`
- Recommended next checkpoint: `PROD-061-english-product-policy-gate-prioritization`
- Production runtime promotion allowed: `false`

## Outputs

Default output folder:

```text
research\experiments\generated\PROD-060-runtime-promotion-path-decision\
```

Generated files:

- `result.json`
- `report.md`
- `path_decision.json`
- `path_options.json`
- `evidence_summary.json`
- `prod_060_review.html`

Case file:

```text
research\experiments\cases\prod-060-runtime-promotion-path-decision.json
```

## Still Blocked

- `customer_move_classification_outside_selected_non_refusal_groups`
- `voicemail_action_only_behavior`
- `coverage_knowledge_policy_behavior`
- `context_sensitive_autonomy_behavior`
- `native_german_review`
- `voice_playback_quality`
- `retrieval_default`
- `provider_or_private_data_use`
- `legal_compliance_review`
- `public_demo_use`
- `real_customer_use`
- `payment_collection`
- `contract_signing`
- `production_runtime_promotion`

## Boundary Status

- Runtime behavior changed: `false`
- Response text behavior changed: `false`
- Retrieval enabled: `false`
- LLM used: `false`
- LLM judging used: `false`
- Provider calls made: `false`
- Private data read: `false`
- Voice playback unblocked: `false`
- Public demo polish unblocked: `false`
- Real customer use unblocked: `false`
- Payment collection allowed: `false`
- Contract signing allowed: `false`
- Production runtime promotion allowed: `false`
- German exact-phrase promotion allowed: `false`
- German naturalness claimed: `false`
- Legal compliance claimed: `false`

## Next Decision

`PROD-061-english-product-policy-gate-prioritization` should prioritize the four product-policy gates that still block broader English runtime promotion:

- customer-move classification outside selected non-refusal groups
- voicemail action-only behavior
- coverage knowledge-policy behavior
- context-sensitive autonomy behavior

It should not open production, public-demo, legal, provider, retrieval, voice, German, payment, contract, or real-customer paths.
