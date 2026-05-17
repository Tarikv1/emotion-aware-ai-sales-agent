# PROD-085 English Guided Option Selection Rewrite Review Import

## Summary

`PROD-085` imports Tarik's `PROD-084` rewrite review.

The decision is approve rewrite for policy probe with payment wording edit. Seven examples are approved as written. The payment-path example is approved after required payment wording edit.

This checkpoint is import-only. It does not patch runtime behavior, response text, classifier reachability, retrieval, provider usage, private-data handling, voice playback, payment handling, contract signing, legal readiness, German wording, spoken naturalness behavior, or production runtime promotion.

## Source Evidence

- Source checkpoint: `PROD-084-english-guided-option-selection-rewrite-design`
- Source validator command: `python scripts\validate_prod_084_english_guided_option_selection_rewrite_design.py`
- Source artifact preserved: `true`
- Source review HTML: `research/experiments/generated/PROD-084-english-guided-option-selection-rewrite-design/prod_084_review.html`
- Imported review: `research/experiments/imports/PROD-084-english-guided-option-selection-rewrite-design/prod_084_guided_option_selection_rewrite_review_from_chat.json`

## Local Commands

```powershell
python scripts\run_prod_085_english_guided_option_selection_rewrite_review_import.py
python scripts\validate_prod_085_english_guided_option_selection_rewrite_review_import.py
```

## Result

- Review import only: `true`
- Human review imported: `true`
- Review HTML created: `false`
- Imported decision: `approve_rewrite_for_policy_probe_with_payment_wording_edit`
- Narrow policy probe approved after required edit: `true`
- Narrow policy probe approved as written: `false`
- Approved as-written examples: `7`
- Required edit examples: `1`
- Runtime candidate promoted: `false`
- Recommended next checkpoint: `PROD-086-english-guided-option-selection-narrow-policy-probe`

## Payment Wording

Example seven was not accepted as written because the `companyname.com` placeholder was too specific and unnecessary for generic payment wording.

Final candidate:

```text
No payment on this call. I'll send you the link by email, and you can review the plan and register there.
```

This keeps no payment on this call as the default and removes the company-domain placeholder from the generic example.

## Outputs

Default output folder:

```text
research\experiments\generated\PROD-085-english-guided-option-selection-rewrite-review-import\
```

Generated files:

- `result.json`
- `report.md`
- `imported_review_summary.json`
- `payment_wording_edit.json`
- `approved_rewrite_candidate_packet.json`
- `narrow_policy_probe_readiness.json`
- `evidence_summary.json`

Case file:

```text
research\experiments\cases\prod-085-english-guided-option-selection-rewrite-review-import.json
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

`PROD-086-english-guided-option-selection-narrow-policy-probe` should design the smallest deterministic policy probe using the approved candidate packet, while keeping runtime promotion blocked.
