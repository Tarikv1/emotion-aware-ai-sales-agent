# Task 9 Care Plan Fix Report

## Status

Implemented the care-plan product fix and independent trace hardening for `ELEVENLABS-040-detailed-pricing-control`.

No provider, dashboard, simulation, or outbound API calls were made. Frozen dashboard test JSON, scenarios, success conditions, models, turns, dynamic variables, and Analysis were not edited. Existing generated live evidence remains dirty/untracked and uncommitted.

## Changes

- Updated the Atlas prompt to quote exactly one relevant care plan after ongoing-cost intent.
- Added the same care-plan selection rule to `atlas_price_scope_cost_drivers.md` and `atlas_output_quality_rules.md`.
- Default care behavior is now Essential Care at `$79/month` for hosting coordination, updates, backups, and monitoring when support need is unclear.
- `$149` is reserved for ordinary edits; `$249` is reserved for heavier edits or monthly reporting.
- The 040 patcher default active follow-up now plans exactly three writes: `atlas_price_scope_cost_drivers.md`, `atlas_output_quality_rules.md`, and the agent prompt.
- Hardened trace validation to canonicalize asynchronous run order by exact expected ID set, reject duplicate/missing IDs, normalize only known approved spoken-money phrases, classify missing required price triggers as `incomplete`, and support `--partial-test-id` for one known expected test.

## Trace Classification

Current `live_test_capture.json` now classifies as:

- 8 pass
- `sim_040_care_plan_only_when_asked`: product fail for quoting all three care plans
- `sim_040_multi_feature_no_price_stacking`: incomplete because the simulated buyer never supplied the required price trigger
- Overall exact-suite status: `fail`

## Validation

Passed:

- `python scripts\test_validate_elevenlabs_040_live_test_traces.py` - 12 tests
- `python scripts\validate_elevenlabs_040_live_test_traces.py --self-test`
- `python scripts\test_apply_elevenlabs_040_detailed_pricing_control.py` - 5 tests
- `python scripts\test_validate_elevenlabs_040_evidence.py` - 8 tests
- `python scripts\test_run_elevenlabs_040_tests.py` - 32 tests
- `python scripts\validate_elevenlabs_039_end_call_edge_case_hardening.py`
- `python scripts\validate_elevenlabs_038_end_call_terminal_control.py`
- `python scripts\validate_elevenlabs_037_confident_capability_control.py`
- `python scripts\validate_elevenlabs_037_custom_capability_scope_confidence.py`
- `python scripts\validate_elevenlabs_036_natural_sales_scenarios_tests.py`
- `python scripts\validate_elevenlabs_035_procedure_natural_sales_tests.py`
- `python scripts\validate_elevenlabs_034_human_phone_naturalness.py`
- `python scripts\validate_elevenlabs_033_email_confirmation_precision.py`
- `python scripts\validate_elevenlabs_032_final_runtime_polish.py`
- `python scripts\validate_elevenlabs_031_runtime_elite_hardening.py`
- `python scripts\validate_elevenlabs_030_live_transcript_failure_hardening.py`
- `python -m py_compile ...` for touched 040 scripts/tests
- `git diff --check` - passed with CRLF normalization warnings only

Expected current failure:

- `python scripts\validate_elevenlabs_040_detailed_pricing_control.py`
- Result: `error: update_kb_file::atlas_output_quality_rules.md source sha mismatch`
- Reason: current generated evidence is still source-bound to the pre-fix source state. Orchestrator must regenerate commit-bound plan-only evidence after this commit; this report does not weaken or bypass provenance.

## Concerns

- The prompt is at `1894` validator words. There is little spare budget.
- Existing generated 040 evidence is still dirty/untracked in the worktree and was intentionally left uncommitted.
- Any active live follow-up should target only the two KB docs plus the agent prompt, for three writes total, after commit-bound plan-only evidence is regenerated.
