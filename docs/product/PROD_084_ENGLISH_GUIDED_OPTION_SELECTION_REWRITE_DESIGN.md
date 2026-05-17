# PROD-084 English Guided Option Selection Rewrite Design

## Summary

`PROD-084` creates rewritten guided option selection examples for human review after Tarik rejected the first `PROD-082` examples.

This checkpoint is review-only. It does not patch runtime behavior, response text, classifier reachability, retrieval, provider usage, private-data handling, voice playback, payment handling, contract signing, legal readiness, German wording, spoken naturalness behavior, or production runtime promotion.

## Source Evidence

- Source checkpoint: `PROD-083-english-guided-option-selection-review-import`
- Source validator command: `python scripts\validate_prod_083_english_guided_option_selection_review_import.py`
- Review import decision: needs rewrite before probe
- Rewrite rules: leave obvious facts out, do not repeat, use approved plan feature facts, steer only from customer facts, keep wording shorter and more human

## Local Commands

```powershell
python scripts\run_prod_084_english_guided_option_selection_rewrite_design.py
python scripts\validate_prod_084_english_guided_option_selection_rewrite_design.py
```

## Result

- Review packet only: `true`
- Selected review item: `guided_option_selection_rewritten_examples`
- Requires human review before next checkpoint: `true`
- Review HTML created: `true`
- Review HTML path: `research/experiments/generated/PROD-084-english-guided-option-selection-rewrite-design/prod_084_review.html`
- Recommended next checkpoint: `PROD-085-english-guided-option-selection-rewrite-review-import`
- Narrow policy probe approved: `false`
- Runtime candidate promoted: `false`
- Random fillers allowed: `false`
- Runtime behavior changed: `false`
- Response text behavior changed: `false`
- Classifier behavior changed: `false`
- Retrieval enabled: `false`
- Production runtime promotion allowed: `false`

## Review Target

The examples use a review-only plan feature matrix:

- `$29`: `[feature X]`, `[feature Y]`, `[feature Z]`
- `$59`: `$29` features plus `[feature A]`, `[feature B]`, `[feature C]`

These placeholders are not runtime facts. The runtime must not invent plan features.

The review packet also includes sparse discourse markers such as `I mean`, `like`, and `you know` so Tarik can judge whether they sound human or fake. Random fillers allowed: `false`.

## Outputs

Default output folder:

```text
research\experiments\generated\PROD-084-english-guided-option-selection-rewrite-design\
```

Generated files:

- `result.json`
- `report.md`
- `rewritten_guided_option_review_packet.json`
- `review_state_template.json`
- `review_only_plan_feature_fixture.json`
- `spoken_naturalness_audit.json`
- `evidence_summary.json`
- `prod_084_review.html`

Case file:

```text
research\experiments\cases\prod-084-english-guided-option-selection-rewrite-design.json
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

`PROD-085-english-guided-option-selection-rewrite-review-import` should import Tarik's review before any guided option selection policy probe.
