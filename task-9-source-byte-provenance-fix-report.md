# Task 9 Source Byte Provenance Fix Report

## Summary

Fixed the ELEVENLABS-040 source-byte provenance boundary so future KB evidence and uploads are bound to exact Git blob bytes at one pinned source commit, not mutable worktree bytes or later HEAD reads.

The patcher now captures `source_commit` once in `main()`, passes it through the source guard, evidence/request/plan/result builders, upload-byte loading, and provider write loop, and asserts current HEAD still equals that pinned commit before the provider write loop and immediately before every attempted write. Multipart KB uploads read the pinned Git blob bytes directly.

The validator now requires new Git-blob provenance fields for every non-allowlisted source evidence entry: `source_git_blob_sha256`, `source_git_blob_length`, `upload_sha256`, `upload_length`, `newline_mode`, plus `source_sha256` and `source_byte_length` aliases equal to the upload fields. Old-field-only evidence fails unless it matches the explicit completed-artifact allowlist.

The completed live ELEVENLABS-040 evidence is accepted only through the exact allowlist for source commit `1e8af8510b072d5fe08501af7229abac5208bdf8`, the expected KB source paths, and recorded upload digests/lengths. Both legacy allowlist paths require current HEAD Git blob bytes for the exact source path to equal the recorded source-commit blob before old evidence is accepted. `update_kb_file::atlas_output_quality_rules.md` reports visible `legacy_worktree_line_endings` mode after verifying HEAD blob equality, recorded worktree upload bytes, CRLF-to-LF normalization, no binary/NUL content, and unchanged plan/request evidence.

No provider/API calls were made.

## Files Changed

- `scripts/apply_elevenlabs_040_detailed_pricing_control.py`
- `scripts/validate_elevenlabs_040_detailed_pricing_control.py`
- `scripts/test_apply_elevenlabs_040_detailed_pricing_control.py`
- `scripts/test_validate_elevenlabs_040_evidence.py`

Follow-up reviewer fix changed only:

- `scripts/validate_elevenlabs_040_detailed_pricing_control.py`
- `scripts/test_validate_elevenlabs_040_evidence.py`
- `task-9-source-byte-provenance-fix-report.md`

## Review Findings Closed

- Mandatory new provenance fields now fail closed for non-allowlisted evidence, including old-field-only evidence whose hash matches the Git blob.
- Legacy line-ending acceptance is restricted to the exact completed artifact tuple for `atlas_output_quality_rules.md`; the companion old-field Git-blob evidence for `atlas_price_scope_cost_drivers.md` is separately allowlisted by exact tuple.
- `legacy_git_blob_old_fields` now requires current HEAD Git blob bytes for the exact source path to equal the recorded source-commit blob, matching the CRLF legacy path. Focused tests cover unchanged price KB acceptance and simulated current HEAD blob drift rejection.
- `source_commit` is captured once and retained in all artifacts; provider upload paths never reread HEAD for source bytes.
- HEAD drift before the first provider write or between writes aborts before any subsequent provider call.
- Direct multipart-body tests parse the generated boundary and assert the raw file part bytes equal the Git blob, including newline and NUL-sensitive byte sequences.
- Validator derives and enforces the exact expected `source_path` from the `update_kb_file::<doc>.md` request id.

## Verification

- `python -m py_compile scripts\apply_elevenlabs_040_detailed_pricing_control.py scripts\validate_elevenlabs_040_detailed_pricing_control.py scripts\test_apply_elevenlabs_040_detailed_pricing_control.py scripts\test_validate_elevenlabs_040_evidence.py` - pass
- `python scripts\test_apply_elevenlabs_040_detailed_pricing_control.py` - pass, 12 tests
- `python scripts\test_validate_elevenlabs_040_evidence.py` - pass, 21 tests
- `python scripts\test_run_elevenlabs_040_tests.py` - pass, 44 tests
- `python scripts\test_validate_elevenlabs_040_live_test_traces.py` - pass, 12 tests
- `python scripts\validate_elevenlabs_040_live_test_traces.py --self-test` - pass
- `python scripts\validate_elevenlabs_040_detailed_pricing_control.py` - pass; current live evidence reports `source_evidence_mode: legacy_worktree_line_endings`, `legacy_allowlisted_request_ids` for both KB updates, and `legacy_worktree_line_endings_request_ids` only for `update_kb_file::atlas_output_quality_rules.md`
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
- `git diff --check` - pass

## Concerns

- The older 036 trace fixture `live_test_invocation_unchanged_final_full_4_sanitized.json` still fails independently for pre-existing trace behavior (`timing_spoken_at_most_once` and repeated mockup CTA/email ask). I used the existing passing paired 036 capture listed above for the validator-chain check.
- Generated 040 live evidence files were already dirty/untracked before this fix. They were not edited or staged by this task.
