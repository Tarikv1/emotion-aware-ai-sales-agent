# PROD-061 English Product-Policy Gate Prioritization

## Summary

`PROD-061` records the English-only product-policy gate order after Tarik accepted the `PROD-060` path decision and confirmed that the project should move forward with the English version for now.

Decision: `prioritize_context_sensitive_autonomy_first`.

Selected first gate: `context_sensitive_autonomy_behavior`.

Selected first gate status: `selected_for_next_probe_still_blocked`.

This is prioritization only and not a runtime patch. It does not change runtime behavior, response text, classifier reachability, German behavior, retrieval, provider calls, LLM use, private-data handling, voice playback, payment handling, contract signing, public demo use, real customer use, legal readiness, or production runtime promotion.

## Source Evidence

- Source path checkpoint: `PROD-060-runtime-promotion-path-decision`
- Source selected path: `internal_guarded_english_baseline_only`
- Source allowed scope: `local_offline_synthetic_internal_regression_reference`
- Source review HTML: `research\experiments\generated\PROD-060-runtime-promotion-path-decision\prod_060_review.html`
- Source validator command: `python scripts\validate_prod_060_runtime_promotion_path_decision.py`

## Ranked Gates

1. `context_sensitive_autonomy_behavior`
   - Status: `selected_for_next_probe_still_blocked`
   - Rationale: best first English-only policy probe because it can be tested with synthetic multi-turn examples, does not require regulated product facts, and does not alter call-control or broad classifier reachability.
   - Risk: can still become manipulative or over-personalized if autonomy language adapts too aggressively.

2. `voicemail_action_only_behavior`
   - Status: `deferred_still_blocked`
   - Rationale: important for English call quality, but this is call-control/action behavior rather than phrase quality.

3. `coverage_knowledge_policy_behavior`
   - Status: `deferred_still_blocked`
   - Rationale: higher legal/product-knowledge risk because coverage answers can imply eligibility, coverage, or advice.

4. `customer_move_classification_outside_selected_non_refusal_groups`
   - Status: `deferred_still_blocked`
   - Rationale: highest blast radius because broader classifier reachability can route many customer turns into newly promoted behavior.

## Local Commands

```powershell
python scripts\run_prod_061_english_product_policy_gate_prioritization.py
python scripts\validate_prod_061_english_product_policy_gate_prioritization.py
```

## Result

- Human review acceptance recorded: `true`
- Prioritization only: `true`
- Product-policy gate count: `4`
- Selected first gate: `context_sensitive_autonomy_behavior`
- Selected first gate status: `selected_for_next_probe_still_blocked`
- Review HTML: not generated; no human review required for this prioritization checkpoint.
- Requires human review before next checkpoint: `false`
- Recommended next checkpoint: `PROD-062-english-context-sensitive-autonomy-policy-probe`
- Production runtime promotion allowed: `false`

## Outputs

Default output folder:

```text
research\experiments\generated\PROD-061-english-product-policy-gate-prioritization\
```

Generated files:

- `result.json`
- `report.md`
- `gate_priority.json`
- `gate_options.json`
- `evidence_summary.json`

Case file:

```text
research\experiments\cases\prod-061-english-product-policy-gate-prioritization.json
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

`PROD-062-english-context-sensitive-autonomy-policy-probe` should define allowed and forbidden English autonomy-preserving follow-up patterns with synthetic multi-turn examples only.

It should not be a runtime patch. It should not open production, public-demo, legal, provider, retrieval, voice, German, payment, contract, or real-customer paths.
