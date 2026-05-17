# PROD-100 English Recommendation Roleplay Runtime Patch

## Summary

`PROD-100` applies the narrow English runtime branch approved by `PROD-099` for `recommendation_roleplay_boundary`.

This checkpoint patches English runtime behavior, response text behavior, and classifier reachability only for the reviewed recommendation-roleplay cases. It does not enable retrieval, provider calls, LLM use, LLM judging, private-data reads, voice playback, payment collection, contract signing, legal readiness, German exact-phrase promotion, public demo use, real customer use, or production runtime promotion.

## Source Evidence

- Source checkpoint: `PROD-099-english-recommendation-roleplay-narrow-policy-probe`
- Source validator command: `python scripts\validate_prod_099_english_recommendation_roleplay_narrow_policy_probe.py`
- Source selected slice: `recommendation_roleplay_boundary`
- Source runtime gap count: `7`
- Source recommendation roleplay probe passed: `true`

## Local Commands

```powershell
python scripts\run_prod_100_english_recommendation_roleplay_runtime_patch.py
python scripts\validate_prod_100_english_recommendation_roleplay_runtime_patch.py
```

## Result

- Runtime patch applied: `true`
- Selected gap fixed count: `7`
- Positive case failures: `0`
- Control case failures: `0`
- Current runtime gap count before patch: `7`
- Requires customer facts for recommendation: `true`
- Requires agency preservation: `true`
- No agent decides for customer: `true`
- No value guarantee: `true`
- Review HTML created: `false`
- Recommended next checkpoint: `PROD-101-english-recommendation-roleplay-post-patch-regression`

## Runtime Patch

- New sales difficulty: `recommendation-roleplay-boundary`
- Selected strategy: `guided-recommendation`
- Runtime file: `runtime/core/realtime_turns.py`
- The route is English-only.
- The route runs after stronger safety and claim boundaries and before product-detail and guided-option matching.
- The route requires plan-feature context and customer facts before direct recommendation wording.
- The route preserves the reviewed `if you need to` and `but I can show` edits from Tarik's review.

## Probe Boundaries Preserved

- Direct recommendation requires customer facts.
- The agent may guide, but must preserve customer agency.
- The agent must not decide for the customer.
- The agent must not guarantee value or outcome.
- Payment collection, contract signing, provider comparison, process clarity, generic confusion, and German exact-phrase handling stay outside this slice.

## Outputs

Default output folder:

```text
research\experiments\generated\PROD-100-english-recommendation-roleplay-runtime-patch\
```

Generated files:

- `result.json`
- `report.md`
- `runtime_patch_summary.json`
- `positive_runtime_cases.json`
- `control_runtime_cases.json`
- `evidence_summary.json`

Case file:

```text
research\experiments\cases\prod-100-english-recommendation-roleplay-runtime-patch.json
```

## Boundary Status

- Runtime behavior changed: `true`
- Response text behavior changed: `true`
- Classifier behavior changed: `true`
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

`PROD-101-english-recommendation-roleplay-post-patch-regression` should verify the patch against the approved positives, adjacent controls, and the stable English guard before selecting any further remaining customer-move slice.
