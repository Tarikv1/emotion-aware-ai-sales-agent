# PROD-086 English Guided Option Selection Narrow Policy Probe

## Summary

`PROD-086` tests the approved-with-edit guided option selection candidate packet from `PROD-085`.

This checkpoint is policy-probe-only. It does not patch runtime behavior, response text, classifier reachability, retrieval, provider usage, private-data handling, voice playback, payment handling, contract signing, legal readiness, German wording, spoken naturalness behavior, or production runtime promotion.

## Source Evidence

- Source checkpoint: `PROD-085-english-guided-option-selection-rewrite-review-import`
- Source validator command: `python scripts\validate_prod_085_english_guided_option_selection_rewrite_review_import.py`
- Approved candidate packet: `research/experiments/generated/PROD-085-english-guided-option-selection-rewrite-review-import/approved_rewrite_candidate_packet.json`
- Payment wording: `No payment on this call. I'll send you the link by email, and you can review the plan and register there.`

## Local Commands

```powershell
python scripts\run_prod_086_english_guided_option_selection_narrow_policy_probe.py
python scripts\validate_prod_086_english_guided_option_selection_narrow_policy_probe.py
```

## Result

- Policy probe passed: `true`
- Policy probe only: `true`
- Runtime patch allowed inside checkpoint: `false`
- Review HTML created: `false`
- Requires plan feature matrix: `true`
- Requires customer facts for steering: `true`
- Random fillers allowed: `false`
- Recommended next checkpoint: `PROD-087-english-guided-option-selection-runtime-patch`

## Constraints

The narrow policy probe requires:

- approved plan feature matrix before explaining `$29` and `$59` differences
- customer facts before fit-based steering
- no payment on this call by default
- email-link payment wording without a generic `companyname.com` placeholder
- no random filler words
- no discourse markers inside payment, contract, or other sensitive boundary statements

## Outputs

Default output folder:

```text
research\experiments\generated\PROD-086-english-guided-option-selection-narrow-policy-probe\
```

Generated files:

- `result.json`
- `report.md`
- `candidate_policy_constraints.json`
- `probe_case_matrix.json`
- `policy_probe_result.json`
- `current_runtime_gap_analysis.json`
- `evidence_summary.json`

Case file:

```text
research\experiments\cases\prod-086-english-guided-option-selection-narrow-policy-probe.json
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

`PROD-087-english-guided-option-selection-runtime-patch` may implement the smallest runtime route for the approved guided option selection behavior. Runtime promotion, real customer use, payment collection, and production use remain blocked.
