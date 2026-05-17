# PROD-097 English Customer-Move Remaining Slice Selection After Process Clarity

## Summary

`PROD-097` selects the next remaining English customer-move subtype after process-clarity regression passed.

The selected subtype is `recommendation_roleplay_boundary`, represented by `prod-081-recommendation-02`: `What would you do in my position?`

This checkpoint creates a human review packet. It does not patch runtime behavior, response text, classifier reachability, retrieval, provider usage, private-data handling, voice playback, payment handling, contract signing, legal readiness, German wording, or production runtime promotion.

## Source Evidence

- Source checkpoint: `PROD-096-english-next-step-process-clarity-post-patch-regression`
- Source validator command: `python scripts\validate_prod_096_english_next_step_process_clarity_post_patch_regression.py`
- Process clarity positive failures: `0`
- Adjacent control failures: `0`
- Stable English guard passed: `true`

## Local Commands

```powershell
python scripts\run_prod_097_english_customer_move_remaining_slice_selection_after_process_clarity.py
python scripts\validate_prod_097_english_customer_move_remaining_slice_selection_after_process_clarity.py
```

## Result

- Selection only: `true`
- Selected next slice: `recommendation_roleplay_boundary`
- Selected remaining case: `prod-081-recommendation-02`
- Requires human review before next checkpoint: `true`
- Review HTML created: `true`
- Recommended next checkpoint: `PROD-098-english-recommendation-roleplay-review-import`

## Review Packet

Open:

```text
research\experiments\generated\PROD-097-english-customer-move-remaining-slice-selection-after-process-clarity\review.html
```

Review goal:

- decide whether the agent may answer recommendation-roleplay turns with a grounded recommendation
- edit any wording that feels too pushy, too scripted, too casual, or too much like the agent is deciding for the customer
- reject examples that should stay outside runtime behavior

## Outputs

Default output folder:

```text
research\experiments\generated\PROD-097-english-customer-move-remaining-slice-selection-after-process-clarity\
```

Generated files:

- `result.json`
- `report.md`
- `remaining_subtype_selection.json`
- `review_packet.json`
- `review_examples.json`
- `review_state_template.json`
- `review.html`
- `evidence_summary.json`

Case file:

```text
research\experiments\cases\prod-097-english-customer-move-remaining-slice-selection-after-process-clarity.json
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

`PROD-098-english-recommendation-roleplay-review-import` should import the human review export before any policy probe or runtime patch is opened.
