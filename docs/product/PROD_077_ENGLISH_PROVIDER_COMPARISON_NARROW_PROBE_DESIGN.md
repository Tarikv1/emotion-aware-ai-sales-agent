# PROD-077 English Provider-Comparison Narrow Probe Design

## Summary

`PROD-077` designs the smallest deterministic English `provider-comparison` probe after `PROD-076` imported Tarik's constrained approval.

This checkpoint is design-only. It does not patch runtime behavior, response text, classifier reachability, retrieval, provider usage, private-data handling, voice playback, payment handling, contract signing, legal readiness, German wording, or production runtime promotion.

## Source Evidence

- Source checkpoint: `PROD-076-english-provider-comparison-review-import`
- Source validator command: `python scripts\validate_prod_076_english_provider_comparison_review_import.py`
- Review decision: approve for narrow probe with brevity constraint
- Not approved as exact wording: `true`
- Comparison target required: `true`

## Local Commands

```powershell
python scripts\run_prod_077_english_provider_comparison_narrow_probe_design.py
python scripts\validate_prod_077_english_provider_comparison_narrow_probe_design.py
```

## Result

- Probe design only: `true`
- Route: `provider-comparison`
- Required signal group: `compare_or_difference_signal`
- Required signal group: `known_comparison_target_signal`
- Comparison target required: `true`
- Generic provider or terms comparison allowed: `false`
- Candidate response: `Fair. We can compare fit against what you use now before you decide.`
- Insert before `existing-provider-gap` if a later runtime patch is opened
- Review HTML created: `false`
- Recommended next checkpoint: `PROD-078-english-provider-comparison-runtime-patch`
- Runtime behavior changed: `false`
- Response text behavior changed: `false`
- Classifier behavior changed: `false`
- Retrieval enabled: `false`
- Production runtime promotion allowed: `false`

## Probe Rule

The later runtime patch may route to `provider-comparison` only when both conditions are present:

- a compare/difference signal such as `compare`, `different`, `difference`, `versus`, or `vs`
- a known comparison target such as `current provider`, `current setup`, `what we already use`, `current terms`, or `existing provider`

Generic provider or terms comparison remains blocked. The route must not catch price-only questions, generic product questions, payment/card language, contract/sign-up language, or plain existing-provider objections with no comparison request.

## Outputs

Default output folder:

```text
research\experiments\generated\PROD-077-english-provider-comparison-narrow-probe-design\
```

Generated files:

- `result.json`
- `report.md`
- `narrow_probe_design.json`
- `candidate_response_design.json`
- `probe_case_matrix.json`
- `current_runtime_gap_analysis.json`
- `evidence_summary.json`

Case file:

```text
research\experiments\cases\prod-077-english-provider-comparison-narrow-probe-design.json
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

`PROD-078-english-provider-comparison-runtime-patch` may apply the candidate response and narrow classifier branch only if the patch preserves the `PROD-077` positive, negative, and protected controls.
