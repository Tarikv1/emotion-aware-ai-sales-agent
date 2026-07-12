# Task 9 Runner Ownership Fix Report

## Scope

- Worktree: `D:\Codex\active\emotion-aware-ai-sales-agent\.worktrees\atlas-detailed-pricing-control`
- Head at start: `1e8af85`
- Edited:
  - `scripts/run_elevenlabs_040_tests.py`
  - `scripts/test_run_elevenlabs_040_tests.py`

## Root Cause

`mapping_payload()` rewrote reused 040 test records with `created_in_this_run=false`, but `validate_owned_mapping()` still treated `created_in_this_run=true` as the only ownership proof. After a full reuse run, later repair/canary validation failed even when the exact ten provider tests had already been created by the Task 9 runner and repaired through the guarded owned-context flow.

## Fix

- Added strict mapping identity parsing so folder/name/order/ID/boolean-flag invariants are checked before ownership resolution.
- Added strict repair-lineage validation for reused mappings using `live_test_context_repair_result.json`:
  - exact checkpoint/status/mode
  - exact folder ID
  - exactly ten repaired tests in expected source-ID order
  - exact provider names/IDs for reused entries
  - membership/repaired counts fixed at 10
  - operation ledger fixed at 10 attempts / 10 successes / 0 failures with exact request IDs, methods, endpoints, statuses, and `200` status codes
- Added durable ownership proof emission:
  - new mapping `ownership` section
  - normalized validated lineage payload
  - `lineage_sha256` bound to the normalized lineage
- Full reuse writes now preserve durable ownership proof when prior proof or strict repair lineage is available.
- Repair and canary validation now load sibling mapping lineage via `mapping_path`, so reused mappings validate fail-closed.

## Tests Added

- created mapping passes without lineage
- reused mapping plus exact repair lineage passes
- reused mapping without lineage fails
- tampering fails for folder/provider ID/provider name/order/status/count/ledger cases
- full reuse mapping write preserves durable ownership proof across repeated reuse runs
- canary validation succeeds after reuse mapping write

## Verification

### Runner / trace / patcher / evidence tests

- `python -m unittest test_run_elevenlabs_040_tests test_validate_elevenlabs_040_live_test_traces test_validate_elevenlabs_040_evidence test_apply_elevenlabs_040_detailed_pricing_control -v`
  - Result: `65 tests`, `OK`

### Trace validator self-test

- `python scripts/validate_elevenlabs_040_live_test_traces.py --self-test`
  - Result: `self-test: pass`

### 040 validator

- `python scripts/validate_elevenlabs_040_detailed_pricing_control.py`
  - Result: `pass`
  - Live evidence validation: `validated_current_source_commit`
  - Source evidence commit: `1e8af8510b072d5fe08501af7229abac5208bdf8`

### 039 / 036 live trace validators

- `python scripts/validate_elevenlabs_039_live_test_traces.py --input research/experiments/generated/ELEVENLABS-039-end-call-edge-case-hardening/live_test_invocation_final_sanitized.json --output research/experiments/generated/ELEVENLABS-039-end-call-edge-case-hardening/independent_trace_validation_final.json`
  - Result: `independent_status=pass`
- `python scripts/validate_elevenlabs_036_live_test_traces.py --input research/experiments/generated/ELEVENLABS-036-natural-sales-scenarios/llm_gpt55_behavior4_full1_capture.json --output research/experiments/generated/ELEVENLABS-036-natural-sales-scenarios/llm_gpt55_behavior4_full1_independent.json`
  - Result: `independent_status=pass`

### 039..030 validators

- `python scripts/validate_elevenlabs_039_end_call_edge_case_hardening.py` -> `pass`
- `python scripts/validate_elevenlabs_038_end_call_terminal_control.py` -> `pass`
- `python scripts/validate_elevenlabs_037_custom_capability_scope_confidence.py` -> `deprecated-wrapper`
- `python scripts/validate_elevenlabs_037_confident_capability_control.py` -> `pass`
- `python scripts/validate_elevenlabs_036_natural_sales_scenarios_tests.py` -> `pass`
- `python scripts/validate_elevenlabs_035_procedure_natural_sales_tests.py` -> `pass`
- `python scripts/validate_elevenlabs_034_human_phone_naturalness.py` -> `pass`
- `python scripts/validate_elevenlabs_033_email_confirmation_precision.py` -> `pass`
- `python scripts/validate_elevenlabs_032_final_runtime_polish.py` -> `pass`
- `python scripts/validate_elevenlabs_031_runtime_elite_hardening.py` -> `pass`
- `python scripts/validate_elevenlabs_030_live_transcript_failure_hardening.py` -> `pass`

### Compile / diff

- `python -m py_compile scripts/run_elevenlabs_040_tests.py scripts/test_run_elevenlabs_040_tests.py scripts/test_validate_elevenlabs_040_live_test_traces.py scripts/test_validate_elevenlabs_040_evidence.py scripts/test_apply_elevenlabs_040_detailed_pricing_control.py scripts/validate_elevenlabs_040_live_test_traces.py scripts/validate_elevenlabs_040_detailed_pricing_control.py scripts/validate_elevenlabs_039_live_test_traces.py scripts/validate_elevenlabs_036_live_test_traces.py`
  - Result: pass
- `git diff --check`
  - Result: pass

## Concerns

- `git diff --check` passed, but Git printed LF/CRLF normalization warnings for the two edited Python files. No whitespace errors were reported.
- The worktree still contains unrelated generated-evidence modifications and untracked files under `research/experiments/generated/ELEVENLABS-040-detailed-pricing-control/`. They were left untouched.
