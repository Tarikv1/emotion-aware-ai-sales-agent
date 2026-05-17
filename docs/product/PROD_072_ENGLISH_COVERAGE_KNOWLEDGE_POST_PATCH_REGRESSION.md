# PROD-072 English Coverage Knowledge Post-Patch Regression

## Summary

`PROD-072` verifies the `PROD-071` English coverage boundary runtime patch after application.

This is regression evidence only. It is not a runtime patch, not a classifier expansion, not retrieval, and not coverage advice.

No human review required. This checkpoint creates no review HTML because it does not ask Tarik to approve product/legal wording, coverage facts, or a new persuasion tactic.

## Source Evidence

- Source checkpoint: `PROD-071-english-coverage-knowledge-runtime-patch`
- Stable English guard source: `PROD-056-english-post-patch-multi-turn-regression`
- Voicemail guard source: `PROD-068-english-voicemail-post-patch-regression`
- Source validator command: `python scripts\validate_prod_071_english_coverage_knowledge_runtime_patch.py`
- Stable guard command: `python scripts\validate_english_multi_turn_regression_guard.py`
- Voicemail guard command: `python scripts\validate_prod_068_english_voicemail_post_patch_regression.py`

## Local Commands

```powershell
python scripts\run_prod_072_english_coverage_knowledge_post_patch_regression.py
python scripts\validate_prod_072_english_coverage_knowledge_post_patch_regression.py
```

## Result

- Stable English guard passed: `true`
- Voicemail guard passed: `true`
- Coverage boundary regression cases: `5`
- Adjacent control cases: `6`
- Voicemail control cases: `2`
- Failed case count: `0`
- Runtime behavior changed: `false`
- Classifier behavior changed: `false`
- Response text behavior changed: `false`
- Call-control behavior changed: `false`
- Next-action behavior changed: `false`
- Coverage advice allowed: `false`
- Coverage fact claims allowed: `false`
- Eligibility claims allowed: `false`
- Reimbursement claims allowed: `false`
- Retrieval enabled: `false`
- Requires human review before next checkpoint: `false`
- Review HTML created: `false`
- Recommended next checkpoint: `PROD-073-english-customer-move-classification-gate-decision`
- Production runtime promotion allowed: `false`

## Future Persuasion-Tactics Checkpoint

`guided_option_selection` remains a future persuasion-tactics checkpoint candidate, not as `PROD-072` runtime behavior.

The tactic should stay blocked until a dedicated persuasion checkpoint defines fit/interest preconditions, fair option presentation, valid refusal choices, and pressure/urgency limits.

## Outputs

Default output folder:

```text
research\experiments\generated\PROD-072-english-coverage-knowledge-post-patch-regression\
```

Generated files:

- `result.json`
- `report.md`
- `coverage_boundary_regression_reviews.json`
- `adjacent_control_reviews.json`
- `voicemail_control_reviews.json`
- `post_patch_regression_decision.json`
- `evidence_summary.json`

Case file:

```text
research\experiments\cases\prod-072-english-coverage-knowledge-post-patch-regression.json
```

## Boundary Status

- Runtime behavior changed: `false`
- Response text behavior changed: `false`
- Classifier behavior changed: `false`
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

`PROD-073-english-customer-move-classification-gate-decision` should decide whether the remaining broad `customer_move_classification_outside_selected_non_refusal_groups` gate is ready for a narrow probe, still blocked behind more evidence, or should be split into smaller classifier slices.
