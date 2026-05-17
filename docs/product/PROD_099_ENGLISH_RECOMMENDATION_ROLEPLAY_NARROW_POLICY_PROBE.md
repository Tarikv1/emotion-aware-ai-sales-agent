# PROD-099 English Recommendation Roleplay Narrow Policy Probe

## Summary

`PROD-099` tests whether the approved `recommendation_roleplay_boundary` packet can be bounded before any runtime patch.

This checkpoint is policy-probe-only. It does not patch runtime behavior, response text, classifier reachability, retrieval, provider usage, private-data handling, voice playback, payment handling, contract signing, legal readiness, German wording, or production runtime promotion.

## Source Evidence

- Source checkpoint: `PROD-098-english-recommendation-roleplay-review-import`
- Source validator command: `python scripts\validate_prod_098_english_recommendation_roleplay_review_import.py`
- Imported decision: `approve_for_policy_probe_with_two_wording_edits`
- Narrow policy probe approved after required edits: `true`

## Local Commands

```powershell
python scripts\run_prod_099_english_recommendation_roleplay_narrow_policy_probe.py
python scripts\validate_prod_099_english_recommendation_roleplay_narrow_policy_probe.py
```

## Result

- Policy probe only: `true`
- Recommendation roleplay probe passed: `true`
- Selected source slice: `recommendation_roleplay_boundary`
- Positive case count: `7`
- Control case count: `10`
- Failed policy case count: `0`
- Current runtime gap count: `7`
- Requires customer facts for recommendation: `true`
- Requires agency preservation: `true`
- Review HTML created: `false`
- Recommended next checkpoint: `PROD-100-english-recommendation-roleplay-runtime-patch`

## Probe Boundaries

- Direct recommendation requires customer facts.
- The agent may guide, but must preserve customer agency.
- The agent must not decide for the customer.
- The agent must not guarantee value or outcome.
- Payment collection, contract signing, provider comparison, process clarity, generic confusion, and German exact-phrase handling stay outside this slice.

## Outputs

Default output folder:

```text
research\experiments\generated\PROD-099-english-recommendation-roleplay-narrow-policy-probe\
```

Generated files:

- `result.json`
- `report.md`
- `candidate_policy_constraints.json`
- `recommendation_roleplay_probe_case_matrix.json`
- `policy_probe_result.json`
- `current_runtime_gap_analysis.json`
- `evidence_summary.json`

Case file:

```text
research\experiments\cases\prod-099-english-recommendation-roleplay-narrow-policy-probe.json
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

`PROD-100-english-recommendation-roleplay-runtime-patch` can patch the English runtime only if it preserves the same controls and keeps recommendation roleplay grounded in customer facts.
