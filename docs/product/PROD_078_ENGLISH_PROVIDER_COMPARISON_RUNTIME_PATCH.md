# PROD-078 English Provider-Comparison Runtime Patch

## Summary

`PROD-078` applies the `PROD-077` narrow English `provider-comparison` runtime patch.

This is an English provider-comparison narrow runtime patch. It changes classifier reachability and English response text for `provider-comparison` only.

No human review required because `PROD-076` imported Tarik's constrained approval and `PROD-077` converted it into a deterministic design.

## Source Evidence

- Source checkpoint: `PROD-077-english-provider-comparison-narrow-probe-design`
- Source validator command: `python scripts\validate_prod_077_english_provider_comparison_narrow_probe_design.py`
- Candidate response: `Fair. We can compare fit against what you use now before you decide.`
- Inserted before `existing-provider-gap`: required by source design

## Local Commands

```powershell
python scripts\run_prod_078_english_provider_comparison_runtime_patch.py
python scripts\validate_prod_078_english_provider_comparison_runtime_patch.py
```

## Result

- Runtime behavior changed: `true`
- Response text behavior changed: `true`
- Classifier behavior changed: `true`
- English-only runtime patch: `true`
- Patched sales difficulty: `provider-comparison`
- Patched response: `Fair. We can compare fit against what you use now before you decide.`
- Inserted before `existing-provider-gap`
- Comparison target required: `true`
- Generic provider or terms comparison allowed: `false`
- Review HTML created: `false`
- Recommended next checkpoint: `PROD-079-english-provider-comparison-post-patch-regression`
- Retrieval enabled: `false`
- Production runtime promotion allowed: `false`

## Runtime Rule

The runtime can route to `provider-comparison` only when both signal groups are present:

- compare/difference signal
- known comparison target signal

Generic provider or terms comparison remains blocked. Existing-provider objections without a comparison request remain in `existing-provider-gap`. Payment, card, contract, sign-up, price-only, generic product, and German exact-phrase promotion remain outside this patch.

## Outputs

Default output folder:

```text
research\experiments\generated\PROD-078-english-provider-comparison-runtime-patch\
```

Generated files:

- `result.json`
- `report.md`
- `runtime_patch_reviews.json`
- `patch_decision.json`
- `evidence_summary.json`

Case file:

```text
research\experiments\cases\prod-078-english-provider-comparison-runtime-patch.json
```

## Boundary Status

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

`PROD-079-english-provider-comparison-post-patch-regression` should verify provider-comparison positives, existing-provider-gap controls, price/product/email/payment controls, and the stable English multi-turn guard.
