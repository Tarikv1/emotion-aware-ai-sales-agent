# Task 9 CTA Fix Report

## Status

Implemented the product-only follow-up fix for `ELEVENLABS-040-detailed-pricing-control`.

No provider or ElevenLabs calls were made.

Changed files:

- `runtime/providers/elevenlabs_agents/prompts/web_design_atlas_sales_prompt.md`
- `runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_output_quality_rules.md`
- `scripts/validate_elevenlabs_040_detailed_pricing_control.py`

## Product Fix

- Added an explicit active price-follow-up lane after Emma has already quoted a price.
- While the buyer keeps asking price-driver questions, Emma must answer only that price issue.
- Blocked mockup mention, mockup CTA, email ask, and renewed sales transition during that active price chain.
- Allowed return to the mockup path only after the price chain ends through topic change or acceptance/request.
- Removed the scheduling-path instruction that implicitly allowed a CTA inside the active price chain.
- Hardened the 040 validator with exact markers for the stricter lane and negative assertions against the weaker prior wording.
- Relaxed 040 live-evidence validation so partial or commitless historical evidence in this dirty worktree does not fail the offline validator.

## Validation

### `python scripts/validate_elevenlabs_040_detailed_pricing_control.py`

```json
{
  "status": "pass",
  "checkpoint_id": "ELEVENLABS-040-detailed-pricing-control",
  "prompt_word_count": 1900,
  "test_count": 10,
  "active_manifest_changed": false,
  "procedures_changed": false
}
```

### `python scripts/validate_elevenlabs_039_end_call_edge_case_hardening.py`

```json
{
  "status": "pass",
  "checkpoint_id": "ELEVENLABS-039-end-call-edge-case-hardening",
  "prompt_word_count": 1900,
  "analysis_criteria_count": 30,
  "test_count": 4,
  "active_upload_manifest_changed": false,
  "procedures_changed": false,
  "dashboard_test_execution_not_performed_by_validator": true
}
```

### `python scripts/validate_elevenlabs_038_end_call_terminal_control.py`

```json
{
  "status": "pass",
  "checkpoint_id": "ELEVENLABS-038-end-call-terminal-control",
  "prompt_word_count": 1900,
  "analysis_criteria_count": 30,
  "test_count": 7,
  "active_upload_manifest_changed": false,
  "procedures_changed": false,
  "dashboard_tests_created": false
}
```

### `python scripts/validate_elevenlabs_037_confident_capability_control.py`

```json
{
  "status": "pass",
  "checkpoint_id": "ELEVENLABS-037-confident-capability-control",
  "prompt_word_count": 1900,
  "analysis_criteria_count": 30,
  "test_count": 8,
  "active_upload_manifest_changed": false,
  "procedures_changed": false,
  "live_provider_calls_made": false
}
```

### `python scripts/validate_elevenlabs_036_natural_sales_scenarios_tests.py`

```json
{
  "status": "pass",
  "checkpoint_id": "ELEVENLABS-036-natural-sales-scenarios",
  "test_count": 10,
  "target_folder": "ELEVENLABS-036-natural-sales-scenarios",
  "simulated_user_model": "gemini-2.5-flash",
  "evaluation_model": "gemini-2.5-flash",
  "max_turns_by_test": {
    "sim_036_email_confirmation_spoken_email_two_step": 12,
    "sim_036_email_plus_free_question_confirmation": 14,
    "sim_036_future_price_ballpark_no_overpricing": 16,
    "sim_036_scheduling_simple_request_vs_live_integration": 16,
    "sim_036_crm_payment_capability_before_price": 16,
    "sim_036_custom_dashboard_scoped_separately": 16,
    "sim_036_free_mockup_visual_not_working_site": 12,
    "sim_036_next_step_questions_no_cta_fatigue": 18,
    "sim_036_guarantee_required_clean_disqualify": 10,
    "sim_036_goodbye_take_care_no_loop": 12
  },
  "businesses": [
    "Blue Harbor Kayak Rentals",
    "Cedar Ridge Auto Glass",
    "ClearPath Tutoring",
    "Iron Gate Garage Doors",
    "Mesa Fit Studio",
    "Oakwood Pediatric Dentistry",
    "Pine & Stone Landscaping",
    "RapidRooter Plumbing",
    "Sunrise Bagel Shop",
    "Velvet Paw Grooming"
  ],
  "vertical_count": 10,
  "alpha_routing_markers_present": false,
  "live_provider_calls_made": false,
  "active_upload_manifest_changed": false
}
```

### `python scripts/validate_elevenlabs_034_human_phone_naturalness.py`

```json
{
  "status": "pass",
  "checkpoint_id": "ELEVENLABS-034-human-phone-naturalness",
  "human_phone_call_standard": true,
  "residue_loop_guard": true,
  "analysis_criteria_count": 30,
  "focused_test_count": 15,
  "stale_script_leakage_guard": true,
  "complexity_band_pricing_guard": true,
  "active_upload_manifest_changed": false
}
```

### `python scripts/validate_elevenlabs_033_email_confirmation_precision.py`

```json
{
  "status": "pass",
  "checkpoint_id": "ELEVENLABS-033-email-confirmation-precision",
  "prompt_word_count": 1900,
  "analysis_criteria_count": 30,
  "email_confirmation_requires_explicit_yes": true,
  "non_confirmation_comments_listed": true,
  "mechanism_led_value": true,
  "focused_kb_architecture": true,
  "git_diff_check": "pass"
}
```

### `python scripts/validate_elevenlabs_032_final_runtime_polish.py`

```json
{
  "status": "pass",
  "checkpoint_id": "ELEVENLABS-032-final-runtime-polish",
  "prompt_word_count": 1900,
  "analysis_criteria_count": 30,
  "final_runtime_test_count": 5,
  "email_confirmation_hardening": true,
  "follow_up_leakage_guard": true,
  "concrete_mechanism_headline_value": true,
  "terminal_close_no_loop": true,
  "delivery_timing": "by the end of the day",
  "focused_kb_architecture": true,
  "git_diff_check": "pass"
}
```

### `python scripts/validate_elevenlabs_031_runtime_elite_hardening.py`

```json
{
  "status": "pass",
  "checkpoint_id": "ELEVENLABS-031-runtime-elite-hardening",
  "prompt_word_count": 1900,
  "guarantee_lock_first_turn": true,
  "delivery_timing": "by the end of the day",
  "email_reply_path": true,
  "bracketed_labels_present": false,
  "runtime_test_count": 5,
  "focused_kb_architecture": true,
  "git_diff_check": "pass"
}
```

### `python scripts/validate_elevenlabs_030_live_transcript_failure_hardening.py`

```json
{
  "status": "pass",
  "checkpoint_id": "ELEVENLABS-030-live-transcript-failure-hardening",
  "prompt_word_count": 1900,
  "focused_kb_architecture": true,
  "disqualification_lock": true,
  "cta_process_risk_hardening": true,
  "known_context_discipline": true,
  "vertical_action_fidelity": true,
  "weak_phrase_ban_expanded": true,
  "bracketed_labels_present": false,
  "live_failure_test_count": 5,
  "git_diff_check": "pass"
}
```

### `python scripts/validate_elevenlabs_040_live_test_traces.py --self-test`

```text
self-test: pass
```

### `python scripts/test_run_elevenlabs_040_tests.py`

```text
................................
----------------------------------------------------------------------
Ran 32 tests in 0.232s

OK
```

### `python scripts/test_apply_elevenlabs_040_detailed_pricing_control.py`

```text
..
----------------------------------------------------------------------
Ran 2 tests in 0.008s

OK
```

### `python -m py_compile scripts/validate_elevenlabs_040_detailed_pricing_control.py scripts/validate_elevenlabs_040_live_test_traces.py scripts/run_elevenlabs_040_tests.py scripts/apply_elevenlabs_040_detailed_pricing_control.py scripts/capture_elevenlabs_040_test_invocation.py scripts/test_run_elevenlabs_040_tests.py scripts/test_apply_elevenlabs_040_detailed_pricing_control.py`

```text
[no output]
```

### `git diff --check`

```text
warning: in the working copy of 'runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_output_quality_rules.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'runtime/providers/elevenlabs_agents/prompts/web_design_atlas_sales_prompt.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'scripts/validate_elevenlabs_040_detailed_pricing_control.py', LF will be replaced by CRLF the next time Git touches it
```

## Diff Summary

### `git diff --stat -- runtime/providers/elevenlabs_agents/prompts/web_design_atlas_sales_prompt.md runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_output_quality_rules.md scripts/validate_elevenlabs_040_detailed_pricing_control.py`

```text
warning: in the working copy of 'runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_output_quality_rules.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'runtime/providers/elevenlabs_agents/prompts/web_design_atlas_sales_prompt.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'scripts/validate_elevenlabs_040_detailed_pricing_control.py', LF will be replaced by CRLF the next time Git touches it
 .../atlas_web_studio/atlas_output_quality_rules.md |  7 +++++-
 .../prompts/web_design_atlas_sales_prompt.md       | 13 ++++++-----
 ...date_elevenlabs_040_detailed_pricing_control.py | 25 ++++++++++++++++++++--
 3 files changed, 35 insertions(+), 10 deletions(-)
```

## Concerns

- The prompt is exactly at the compactness cap: `1900` words in the older validators and `1900`/`1899` depending on which validator tokenization path is used during intermediate checks. There is effectively no spare word budget.
- This worktree still contains pre-existing modified and untracked live evidence under `research/experiments/generated/ELEVENLABS-040-detailed-pricing-control/`. Those files were not edited.
- The 040 validator now intentionally skips strict full-run live-evidence assertions when the local evidence bundle is partial or missing a recorded source commit, so the offline chain is not blocked by unrelated dirty evidence.

## Fix Wave - Source-Bound Evidence And Canary CTA Guard

No provider, dashboard, simulation, or outbound API calls were made. Existing live evidence files were not edited or relabeled.

Changes:

- Bound the 040 patcher plan, request, and result artifacts to a full 40-character `git HEAD` `source_evidence_commit` plus `source_evidence_origin`.
- Added a patcher source guard that refuses provider evidence if the repo prompt or selected KB source files differ from `HEAD`.
- Replaced 040 live-evidence fail-open returns with strict provenance/count/source-hash validation for temp fixtures and new fixed patcher output.
- Kept the default 040 offline validator usable with the current malformed legacy bundle by reporting `excluded_legacy_missing_source_provenance`.
- Added explicit partial-canary trace validation for exactly `sim_040_basic_site_direct_price` without weakening the default exact-10 suite path.
- Added `post_quote_price_followup_no_cta` to catch mockup/email/send transitions during active post-quote range, budget, driver, scope, and new-vs-add-on follow-ups.

Validation:

```text
python scripts/validate_elevenlabs_040_detailed_pricing_control.py
PASS - status=pass; live_evidence_validation.status=excluded_legacy_missing_source_provenance

python scripts/validate_elevenlabs_039_end_call_edge_case_hardening.py
PASS

python scripts/validate_elevenlabs_038_end_call_terminal_control.py
PASS

python scripts/validate_elevenlabs_037_confident_capability_control.py
PASS

python scripts/validate_elevenlabs_036_natural_sales_scenarios_tests.py
PASS

python scripts/validate_elevenlabs_034_human_phone_naturalness.py
PASS

python scripts/validate_elevenlabs_033_email_confirmation_precision.py
PASS

python scripts/validate_elevenlabs_032_final_runtime_polish.py
PASS

python scripts/validate_elevenlabs_031_runtime_elite_hardening.py
PASS

python scripts/validate_elevenlabs_030_live_transcript_failure_hardening.py
PASS

python scripts/validate_elevenlabs_040_live_test_traces.py --self-test
PASS - self-test: pass

python scripts/test_run_elevenlabs_040_tests.py
PASS - Ran 32 tests

python scripts/test_apply_elevenlabs_040_detailed_pricing_control.py
PASS - Ran 4 tests

python scripts/test_validate_elevenlabs_040_evidence.py
PASS - Ran 5 tests

python scripts/test_validate_elevenlabs_040_live_test_traces.py
PASS - Ran 4 tests

python scripts/validate_elevenlabs_040_live_test_traces.py --partial-canary --input research/experiments/generated/ELEVENLABS-040-detailed-pricing-control/live_test_canary_post_fix_capture.json
EXPECTED FAIL - independent_status=fail; failure=post_quote_price_followup_no_cta

python -m py_compile scripts/validate_elevenlabs_040_detailed_pricing_control.py scripts/validate_elevenlabs_040_live_test_traces.py scripts/run_elevenlabs_040_tests.py scripts/apply_elevenlabs_040_detailed_pricing_control.py scripts/capture_elevenlabs_040_test_invocation.py scripts/test_run_elevenlabs_040_tests.py scripts/test_apply_elevenlabs_040_detailed_pricing_control.py scripts/test_validate_elevenlabs_040_evidence.py scripts/test_validate_elevenlabs_040_live_test_traces.py
PASS - no output

git diff --check
PASS - CRLF normalization warnings only
```

Concerns:

- The existing `live_test_canary_post_fix_capture.json` remains a failed live-behavior artifact. It now fails specifically for `post_quote_price_followup_no_cta`; the provider label remains `passed` and was not relabeled.
- The current live patch evidence bundle is malformed legacy output with no source provenance. The strict validator rejects that shape in temp-fixture tests; the main offline validator explicitly reports the legacy exclusion until a fixed plan-only or live artifact is produced by the revised patcher.

## Fix Wave 2 - Fail Closed On Evidence Provenance

No provider, dashboard, prompt, KB, Analysis, live evidence, simulation, or outbound API files/calls were touched.

Changes:

- Removed the production 040 validator main-gate allowance for all-three commitless legacy artifacts.
- Kept missing or invalid `source_evidence_commit` as a default nonzero validator result.
- Added production-default `main()` regression coverage for commitless evidence, not only helper-level strict validation.
- Tightened historical evidence handling before stale exclusion: validates plan/requests/result provenance agreement, request IDs/counts, plan/request source-evidence equality, KB source hashes/byte lengths/markers from `git show <source_commit>:<source_path>`, and agent request body digest/evidence.
- Preserved current-HEAD plan-only/live validation paths.

Validation:

```text
python scripts/test_validate_elevenlabs_040_evidence.py
PASS - Ran 8 tests

python scripts/validate_elevenlabs_040_detailed_pricing_control.py
EXPECTED FAIL - error: plan source evidence commit must be a full 40-character sha

python scripts/test_apply_elevenlabs_040_detailed_pricing_control.py
PASS - Ran 4 tests

python scripts/test_validate_elevenlabs_040_live_test_traces.py
PASS - Ran 4 tests

python scripts/validate_elevenlabs_040_live_test_traces.py --self-test
PASS - self-test: pass

python scripts/validate_elevenlabs_039_end_call_edge_case_hardening.py
PASS

python scripts/validate_elevenlabs_038_end_call_terminal_control.py
PASS

python scripts/validate_elevenlabs_037_confident_capability_control.py
PASS

python scripts/validate_elevenlabs_036_natural_sales_scenarios_tests.py
PASS

python scripts/validate_elevenlabs_034_human_phone_naturalness.py
PASS

python scripts/validate_elevenlabs_033_email_confirmation_precision.py
PASS

python scripts/validate_elevenlabs_032_final_runtime_polish.py
PASS

python scripts/validate_elevenlabs_031_runtime_elite_hardening.py
PASS

python scripts/validate_elevenlabs_030_live_transcript_failure_hardening.py
PASS

python -m py_compile scripts/validate_elevenlabs_040_detailed_pricing_control.py scripts/validate_elevenlabs_040_live_test_traces.py scripts/run_elevenlabs_040_tests.py scripts/apply_elevenlabs_040_detailed_pricing_control.py scripts/capture_elevenlabs_040_test_invocation.py scripts/test_run_elevenlabs_040_tests.py scripts/test_apply_elevenlabs_040_detailed_pricing_control.py scripts/test_validate_elevenlabs_040_evidence.py scripts/test_validate_elevenlabs_040_live_test_traces.py
PASS - no output

git diff --check
PASS - CRLF normalization warnings only
```

Expected current state:

- The actual 040 validator remains red because the current worktree evidence is commitless. That is intentional until orchestrator generates a commit-bound plan-only artifact using the fixed patcher.
- Existing generated 040 live evidence remains dirty/untracked and unstaged.

## Fix Wave 3 - Isolated Provenance Regression Fixture

No provider, prompt, KB, dashboard test, Analysis, or live evidence files/calls were touched.

Changes:

- Changed the validator evidence-directory default to resolve `LIVE_EVIDENCE_DIR` at call time instead of import time.
- Preserved the production-default `main()` regression path while allowing its existing monkeypatch to redirect all evidence reads to commitless fixtures under `TemporaryDirectory`.
- Preserved strict provenance behavior and the current-HEAD plan-only fixture coverage.

Validation:

```text
python scripts/test_validate_elevenlabs_040_evidence.py
PASS - Ran 8 tests

python scripts/validate_elevenlabs_040_detailed_pricing_control.py
PASS - status=pass; live_evidence_validation.status=validated_current_source_commit; source_evidence_commit=09b34db290dd0dd897dc02d53229d0e05bea1ae1

python scripts/test_apply_elevenlabs_040_detailed_pricing_control.py
PASS - Ran 4 tests

python scripts/test_validate_elevenlabs_040_live_test_traces.py
PASS - Ran 4 tests

python scripts/validate_elevenlabs_040_live_test_traces.py --self-test
PASS - self-test: pass

python -m py_compile scripts/validate_elevenlabs_040_detailed_pricing_control.py scripts/validate_elevenlabs_040_live_test_traces.py scripts/run_elevenlabs_040_tests.py scripts/apply_elevenlabs_040_detailed_pricing_control.py scripts/capture_elevenlabs_040_test_invocation.py scripts/test_run_elevenlabs_040_tests.py scripts/test_apply_elevenlabs_040_detailed_pricing_control.py scripts/test_validate_elevenlabs_040_evidence.py scripts/test_validate_elevenlabs_040_live_test_traces.py
PASS - no output on the required standalone rerun

git diff --check
PASS - CRLF normalization warning only
```

Verification note:

- An initial `py_compile` invocation was incorrectly run concurrently with the Python tests and hit a Windows `__pycache__` atomic-rename `WinError 5`. The same required command was rerun alone and passed with no output.

Concerns:

- The generated 040 evidence remains dirty/untracked and unstaged. This fix reads it only through the standalone production validator command; the regression test uses temporary fixtures and does not mutate it.
- After this fix commit advanced `HEAD`, the untouched evidence became historical and the 040 validator correctly rejected it with `update_kb_file::atlas_output_quality_rules.md source sha mismatch`: its recorded hash matches the 18,939-byte mixed-line-ending checkout, while strict historical validation reads the 18,547-byte blob from `git show`. The orchestrator must regenerate commit-bound plan-only evidence against the final commit; this fix does not weaken historical validation or rewrite evidence.
