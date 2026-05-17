# PROD-090 English Guided Option Synonym Coverage Narrow Probe

## Summary

`PROD-090` tests whether the two near-synonym guided-option gaps selected by `PROD-089` can use the existing reviewed guardrails before any runtime trigger expansion.

This checkpoint is policy-probe-only. It does not patch runtime behavior, response text, classifier reachability, retrieval, provider usage, private-data handling, voice playback, payment handling, contract signing, legal readiness, German wording, or production runtime promotion.

## Source Evidence

- Source checkpoint: `PROD-089-english-customer-move-remaining-slice-selection-after-guided-option`
- Source validator command: `python scripts\validate_prod_089_english_customer_move_remaining_slice_selection_after_guided_option.py`
- Source result: selected next slice `guided_option_synonym_coverage`, selected gap count `2`, no review HTML

## Local Commands

```powershell
python scripts\run_prod_090_english_guided_option_synonym_coverage_narrow_probe.py
python scripts\validate_prod_090_english_guided_option_synonym_coverage_narrow_probe.py
```

## Result

- Policy probe only: `true`
- Policy probe passed: `true`
- Selected gap count: `2`
- Positive case count: `4`
- Control case count: `9`
- Failed policy case count: `0`
- Current runtime gap count: `2`
- Requires human review before next checkpoint: `false`
- Recommended next checkpoint requires human review: `false`
- Review HTML created: `false`
- Recommended next checkpoint: `PROD-091-english-guided-option-synonym-coverage-runtime-patch`

## Probe Scope

Selected runtime gaps:

- `Should I start small or go with the fuller option?`
- `Can you show me both options side by side?`

Still deferred:

- advice roleplay, such as `What would you do in my position?`
- process clarity after yes
- generic decision confusion
- payment, card, coverage, provider-comparison, autonomy, German, contract, and production boundaries

## Outputs

Default output folder:

```text
research\experiments\generated\PROD-090-english-guided-option-synonym-coverage-narrow-probe\
```

Generated files:

- `result.json`
- `report.md`
- `candidate_policy_constraints.json`
- `synonym_probe_case_matrix.json`
- `policy_probe_result.json`
- `current_runtime_gap_analysis.json`
- `evidence_summary.json`

Case file:

```text
research\experiments\cases\prod-090-english-guided-option-synonym-coverage-narrow-probe.json
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

`PROD-091-english-guided-option-synonym-coverage-runtime-patch` should apply the smallest trigger expansion for the two passing synonym gaps, then run post-patch regression.
