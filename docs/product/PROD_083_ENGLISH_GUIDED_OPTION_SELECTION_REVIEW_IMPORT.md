# PROD-083 English Guided Option Selection Review Import

## Summary

`PROD-083` imports Tarik's `PROD-082` guided option selection review feedback.

The imported decision is: needs rewrite before probe.

This checkpoint is import-only. It does not patch runtime behavior, response text, classifier reachability, retrieval, provider usage, private-data handling, voice playback, payment handling, contract signing, legal readiness, German wording, spoken naturalness behavior, or production runtime promotion.

## Source Evidence

- Source checkpoint: `PROD-082-english-guided-option-selection-review`
- Source validator command: `python scripts\validate_prod_082_english_guided_option_selection_review.py`
- Review import: `research/experiments/imports/PROD-082-english-guided-option-selection-review/prod_082_guided_option_selection_review_from_chat.json`
- Review item: `guided_option_selection_candidate`

## Local Commands

```powershell
python scripts\run_prod_083_english_guided_option_selection_review_import.py
python scripts\validate_prod_083_english_guided_option_selection_review_import.py
```

## Result

- Review import only: `true`
- Human review imported: `true`
- Selected review item: `guided_option_selection_candidate`
- Decision: needs rewrite before probe
- Narrow policy probe approved: `false`
- Rewrite required: `true`
- Plan feature matrix required: `true`
- No payment on the call by default: `true`
- Campaign payment path can be explained when approved: `true`
- Sparse contextual discourse markers candidate: `true`
- Random fillers allowed: `false`
- Review HTML created: `false`
- Recommended next checkpoint: `PROD-084-english-guided-option-selection-rewrite-design`
- Runtime behavior changed: `false`
- Response text behavior changed: `false`
- Classifier behavior changed: `false`
- Retrieval enabled: `false`
- Production runtime promotion allowed: `false`

## Imported Review Interpretation

The `PROD-082` examples are not approved. They are too defensive and repeat obvious facts. The next rewrite must:

- leave obvious facts out
- do not repeat what the customer already said unless needed
- explain what each option includes
- use approved plan feature facts instead of invented differences
- steer toward the better option when customer facts support it
- keep wording shorter and more human
- preserve autonomy without repeatedly saying `neither` or `not now`
- use light persuasion when the customer is uncertain but still engaged
- separate option selection from payment handling

## Plan Feature Matrix

A guided option response cannot be realistic unless the campaign profile has approved plan facts.

Example placeholders:

- `$29`: `feature_x`, `feature_y`, `feature_z`
- `$59`: `$29` features plus `feature_a`, `feature_b`, `feature_c`

The runtime must not invent those features.

## Payment Workflow

Current rule: no payment on the call by default.

The agent may explain how the approved campaign payment path works if that path exists, such as a human callback, an approved company-domain email link, an approved registration link/form, or paperwork outside the call. Future agent-handled payment remains deferred.

## Spoken Naturalness

The review also adds a future spoken-naturalness candidate: sparse contextual discourse markers such as `I mean`, `like`, or `you know`.

This is not a random filler rule. Random fillers allowed: `false`.

Constraints:

- use sparingly
- use only where it improves spoken naturalness
- do not add fillers to payment, legal, coverage, healthcare, or safety-boundary statements
- do not repeat the same marker mechanically
- do not let markers lengthen already wordy answers

## Outputs

Default output folder:

```text
research\experiments\generated\PROD-083-english-guided-option-selection-review-import\
```

Generated files:

- `result.json`
- `report.md`
- `imported_review_summary.json`
- `rewrite_requirements.json`
- `plan_fact_requirements.json`
- `payment_workflow_requirements.json`
- `spoken_naturalness_constraints.json`
- `evidence_summary.json`

Case file:

```text
research\experiments\cases\prod-083-english-guided-option-selection-review-import.json
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

`PROD-084-english-guided-option-selection-rewrite-design` should design the rewrite contract before any policy probe or runtime patch.
