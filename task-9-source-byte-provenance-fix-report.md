# Task 9 Source Byte Provenance Fix Report

## Summary

Fixed the ELEVENLABS-040 source-byte provenance boundary so future KB evidence and uploads are bound to exact Git blob bytes, not worktree bytes. The patcher now verifies the worktree text normalizes to the Git blob before provider writes, rejects binary/non-UTF-8 source content, records Git blob/upload byte digests and newline mode, and uploads the exact blob byte buffer.

The validator now validates historical evidence against `git show <source_evidence_commit>:<path>` bytes and reports the existing completed live evidence through a visible `legacy_worktree_line_endings` mode only for `update_kb_file::atlas_output_quality_rules.md`.

No provider/API calls were made.

## Files Changed

- `scripts/apply_elevenlabs_040_detailed_pricing_control.py`
- `scripts/validate_elevenlabs_040_detailed_pricing_control.py`
- `scripts/test_apply_elevenlabs_040_detailed_pricing_control.py`
- `scripts/test_validate_elevenlabs_040_evidence.py`

## Verification

- `python scripts\test_apply_elevenlabs_040_detailed_pricing_control.py` - pass, 8 tests
- `python scripts\test_validate_elevenlabs_040_evidence.py` - pass, 15 tests
- `python scripts\test_run_elevenlabs_040_tests.py` - pass, 44 tests
- `python scripts\test_validate_elevenlabs_040_live_test_traces.py` - pass, 12 tests
- `python scripts\validate_elevenlabs_040_live_test_traces.py --self-test` - pass
- `python scripts\validate_elevenlabs_040_detailed_pricing_control.py` - pass; live evidence reports `legacy_worktree_line_endings` for `update_kb_file::atlas_output_quality_rules.md`
- `python scripts\validate_elevenlabs_039_end_call_edge_case_hardening.py` - pass
- `python scripts\validate_elevenlabs_039_live_test_traces.py --input research\experiments\generated\ELEVENLABS-039-end-call-edge-case-hardening\live_test_invocation_final_sanitized.json` - pass
- `python scripts\validate_elevenlabs_038_end_call_terminal_control.py` - pass
- `python scripts\validate_elevenlabs_037_custom_capability_scope_confidence.py` - pass, deprecated wrapper to current 037 validator
- `python scripts\validate_elevenlabs_037_confident_capability_control.py` - pass
- `python scripts\validate_elevenlabs_036_natural_sales_scenarios_tests.py` - pass
- `python scripts\validate_elevenlabs_036_live_test_traces.py --input research\experiments\generated\ELEVENLABS-036-natural-sales-scenarios\llm_gpt55_behavior4_full1_capture.json` - pass
- `python scripts\validate_elevenlabs_035_procedure_natural_sales_tests.py` - pass
- `python scripts\validate_elevenlabs_034_human_phone_naturalness.py` - pass
- `python scripts\validate_elevenlabs_033_email_confirmation_precision.py` - pass
- `python scripts\validate_elevenlabs_032_final_runtime_polish.py` - pass
- `python scripts\validate_elevenlabs_031_runtime_elite_hardening.py` - pass
- `python scripts\validate_elevenlabs_030_live_transcript_failure_hardening.py` - pass
- `python -m py_compile scripts\apply_elevenlabs_040_detailed_pricing_control.py scripts\validate_elevenlabs_040_detailed_pricing_control.py scripts\test_apply_elevenlabs_040_detailed_pricing_control.py scripts\test_validate_elevenlabs_040_evidence.py` - pass
- `git diff --check` - pass; Git emitted expected CRLF normalization warnings for edited Python files

## Concerns

- `python scripts\validate_elevenlabs_036_live_test_traces.py --input research\experiments\generated\ELEVENLABS-036-natural-sales-scenarios\live_test_invocation_unchanged_final_full_4_sanitized.json` still fails independently for pre-existing trace behavior (`timing_spoken_at_most_once` and repeated mockup CTA/email ask). I used the existing passing paired 036 capture listed above for the validator-chain check.
- Generated 040 live evidence files were already dirty before this fix. They were not edited or staged by this task.
