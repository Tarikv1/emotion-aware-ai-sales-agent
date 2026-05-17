# PROD-087 English Guided Option Selection Runtime Patch

## Summary

`PROD-087` applies the narrow English `guided-option-selection` runtime route approved by `PROD-086`.

This checkpoint changes runtime behavior, response text behavior, and classifier behavior for the selected English guided option selection cases only. It does not enable retrieval, provider usage, private-data handling, voice playback, payment collection, contract signing, legal readiness, German wording, public demo use, real customer use, or production runtime promotion.

## Source Evidence

- Source checkpoint: `PROD-086-english-guided-option-selection-narrow-policy-probe`
- Source validator command: `python scripts\validate_prod_086_english_guided_option_selection_narrow_policy_probe.py`
- Source policy probe passed: `true`
- Runtime file: `runtime/core/realtime_turns.py`

## Local Commands

```powershell
python scripts\run_prod_087_english_guided_option_selection_runtime_patch.py
python scripts\validate_prod_087_english_guided_option_selection_runtime_patch.py
```

## Result

- Runtime patch applied: `true`
- New sales difficulty: `guided-option-selection`
- Requires plan feature matrix: `true`
- Requires customer facts for steering: `true`
- Review HTML created: `false`
- Recommended next checkpoint: `PROD-088-english-guided-option-selection-post-patch-regression`

## Payment Wording

The guided option payment path keeps no payment on this call and uses the shorter email-link wording:

```text
No payment on this call. I'll send you the link by email, and you can review the plan and register there.
```

Generic `companyname.com` payment wording remains blocked.

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

`PROD-088-english-guided-option-selection-post-patch-regression` must verify the new route against adjacent price, payment, contract, coverage, written-info, provider-comparison, autonomy, and unknown-signal behavior before this runtime patch is treated as stable.
