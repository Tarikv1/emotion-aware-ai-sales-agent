# PROD-091 English Guided Option Synonym Coverage Runtime Patch

## Summary

`PROD-091` applies the smallest runtime trigger expansion for the two guided-option synonym gaps approved by `PROD-090`.

The patch is limited to English guided-option synonym coverage. It adds no retrieval, provider usage, private-data handling, voice playback, payment collection, contract signing, legal readiness, German wording, public demo use, real customer use, or production runtime promotion.

## Source Evidence

- Source checkpoint: `PROD-090-english-guided-option-synonym-coverage-narrow-probe`
- Source validator command: `python scripts\validate_prod_090_english_guided_option_synonym_coverage_narrow_probe.py`
- Source result: policy probe passed `true`, selected gap count `2`, current runtime gap count `2`

## Local Commands

```powershell
python scripts\run_prod_091_english_guided_option_synonym_coverage_runtime_patch.py
python scripts\validate_prod_091_english_guided_option_synonym_coverage_runtime_patch.py
```

## Result

- Runtime patch applied: `true`
- Selected gap fixed count: `2`
- Positive case failures: `0`
- Control case failures: `0`
- Review HTML created: `false`
- Recommended next checkpoint: `PROD-092-english-guided-option-synonym-coverage-post-patch-regression`

## Patch Scope

Runtime file:

```text
runtime\core\realtime_turns.py
```

Changes:

- adds `start small`, `fuller option`, and `side by side` as guided-option option signals
- adds `show`, `side by side`, `worth it`, and `worth` as guided-option action signals
- adds response branches for `worth it`, `side by side`, and `start small` / `fuller option`
- adds a current-provider guard so provider side-by-side phrasing does not route as guided-option selection

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

`PROD-092-english-guided-option-synonym-coverage-post-patch-regression` should verify the synonym patch after application before another customer-move slice is selected.
