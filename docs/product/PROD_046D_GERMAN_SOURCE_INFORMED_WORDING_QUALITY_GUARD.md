# PROD-046D German Source-Informed Wording Quality Guard

## Summary

PROD-046D is a narrow German wording-quality checkpoint after PROD-046C.

It uses the GER-001 source audit as source-informed wording guidance only. This is not legal compliance, does not use German sales scripts, and does not broaden product, insurance, health, coverage, pricing, security, legal, or competitor claims.

The checkpoint reduces customer-facing internal wording such as `freigegeben`, `Vertriebsteil`, log-centric callback wording, and bureaucratic security phrasing while keeping the PROD-045 English regression, PROD-046A German regression, PROD-046B wording regression, and PROD-046C interpolation guard passing.

## Local Commands

```powershell
python scripts\run_prod_046d_german_source_informed_wording_quality_guard.py
python scripts\validate_prod_046d_german_source_informed_wording_quality_guard.py
```

Recommended regression and guard commands:

```powershell
python scripts\run_prod_045_core_sales_policy_regression_rerun.py
python scripts\validate_prod_045_core_sales_policy_regression_rerun.py
python scripts\run_prod_046a_german_naturalized_policy_regression.py
python scripts\validate_prod_046a_german_naturalized_policy_regression.py
python scripts\run_prod_046b_german_response_wording_quality_pass.py
python scripts\validate_prod_046b_german_response_wording_quality_pass.py
python scripts\run_prod_046c_german_campaign_field_interpolation_guard.py
python scripts\validate_prod_046c_german_campaign_field_interpolation_guard.py
python scripts\validate_realtime_turn_cli.py
python scripts\check_project_drift.py
python scripts\check_thesis_update_gate.py
python scripts\check_thesis_reference_registry.py
python scripts\check_setup.py
```

## Output Directory

```text
research\experiments\generated\PROD-046D-german-source-informed-wording-quality-guard\
```

Artifacts:

- `result.json`
- `report.md`
- `german_source_informed_before_after.json`
- `german_source_informed_results.json`
- `german_source_informed_review_data.json`
- `german_source_informed_review.html`
- `source_traceability_map.json`

## Source Boundary

PROD-046D uses source-informed wording guidance from accepted GER-001 sources:

- official regulator pages
- consumer-protection pages
- public-service safety pages
- public-service plain-language guidance

The checkpoint rejects sales guru blogs, cold-call scripts, aggressive closing scripts, affiliate SEO pages, copied competitor or insurer wording, random news articles when an official source exists, and legal/compliance pages unless handled in a separate compliance checkpoint.

No source wording is copied into runtime responses. The source map records URLs and paraphrased relevance only.

## Wording Guard Scope

PROD-046D validates that German customer-facing runtime responses:

- avoid overusing `freigegeben` in spoken customer output;
- avoid internal route or policy terms;
- use active customer-facing German;
- keep formal `Sie`;
- put safety boundaries before optional next steps;
- avoid pressure for a verbal yes;
- preserve no payment collection, no card-data collection, no contract signing, no unsupported claims, no medical/coverage advice, and no competitor superiority claims.

## Campaign Field Shape Rules

Future German campaign fields should identify their shape:

- full customer-facing sentence
- noun phrase
- route label
- written-info object
- boundary sentence

German templates should not insert an arbitrary fragment into a fixed sentence unless the field shape is known. Full customer-facing sentence fields are preferred for identity, pricing, and verification responses.

## Boundary Status

- Runtime behavior changed: `true`
- Retrieval enabled: `false`
- Provider calls made: `false`
- LLM used: `false`
- Private data read: `false`
- Voice playback unblocked: `false`
- Public demo polish unblocked: `false`
- Payment collection allowed: `false`
- Contract signing allowed: `false`
- Production runtime promotion allowed: `false`

## Next Checkpoint

Recommended next checkpoint: `PROD-046-core-sales-policy-human-review`.

Purpose: inspect English and German runtime-policy behavior, including source-informed German wording, before any broader runtime promotion, demo claim, voice playback unlock, or retrieval default change.
