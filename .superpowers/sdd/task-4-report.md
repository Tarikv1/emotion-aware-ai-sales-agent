# Task 4 Report: Offline Cohort-Release Contract And Gate

## Status

Implementation, verification, and the focused commit are complete.

## Scope Implemented

- Added `CohortReleaseEvidenceV1` construction and strict validation for synthetic/public metadata only.
- Wrapped the unchanged `OperationalAggregateV1` validator as the aggregate input boundary; no speaker field was added to the runtime contract.
- Added deterministic one-record-per-dataset-namespaced-speaker selection ordered by dataset manifest ID, source speaker ID, source timestamp, and canonical record digest.
- Added suppression for an unproven speaker basis, missing deterministic selection evidence, fewer than ten proven speakers, and all mixed-dataset cohorts.
- Rejected call/session/turn identity bases, direct-identifier bases, biometric/embedding bases, model/provider identity predictions, probabilistic certainty claims, the reserved pseudonymous basis, and every non-null cross-corpus identity digest.
- Added the six-field metric allowlist and independent ten-speaker output-cell suppression.
- Added fixed, closed, non-overlapping window enforcement and whole-release-only replacement binding to the prior canonical release digest.
- Added the independent confirmatory floor of thirty overall speakers plus thirty consensus-positive and thirty consensus-negative turns for every promoted label.
- Added the Phase A wrapper that rejects CREMA-D and AMI as `PatternCandidateV1.discovery_dataset_version` values while leaving the detached legacy pattern contract unchanged.
- Added the tracked release schema and named parameter-only synthetic fixture scenarios.
- Registered `emotion_state_cohort_release_contracts` in the Phase A checkpoint builder and validator.

## TDD Evidence

1. Initial RED:
   - Command: `python -m unittest scripts.test_emotion_state_001_open_dataset_gate.CohortReleaseTests -v`
   - Result: exit 1; 16 tests errored with the expected `ModuleNotFoundError: No module named 'scripts.emotion_state_cohort_release_contracts'`.
2. Builder integration RED:
   - Command: `python -m unittest scripts.test_emotion_state_001_open_dataset_gate.CohortReleaseTests.test_phase_a_builder_registers_cohort_release_self_check -v`
   - Result: exit 1; expected missing `emotion_state_cohort_release_contracts` key.
3. First GREEN attempt:
   - Result: 16 passed, 1 errored because the test used the invalid runtime bucket `good`; the unchanged runtime validator correctly rejected it. The fixture was corrected to the allowed `usable` bucket without weakening the gate.
4. Self-review regression RED/GREEN:
   - A missing `eligible` field reproduced a `KeyError`; a focused regression test failed, the field-presence root cause was corrected, and the focused test passed.
   - Noncanonical and reversed release windows were accepted by standalone release validation; focused subtests failed, independent date validation was added, and the focused test passed.

## Final Verification Evidence

- `python -m unittest scripts.test_emotion_state_001_open_dataset_gate.CohortReleaseTests -v`
  - 18/18 passed after self-review additions.
- `python -m unittest scripts.test_emotion_state_001_open_dataset_gate -v`
  - 37/37 passed; exit 0.
- `python scripts\validate_emotion_state_001_phase_a_contracts.py --section contracts`
  - Passed; exit 0.
- `git diff --check`
  - Passed before staging.
- `git diff --cached --check`
  - Passed with exactly the six Task 4 source files staged.

## Boundary Review

- No dataset download, dataset material, annotation evidence, private/customer data, or private source reread occurred.
- No ElevenLabs or other provider access occurred.
- No outbound/customer call, simulation, source adaptation, or source reimplementation occurred.
- No runtime, prompt, BRAIN-002, policy, dependency, or package file changed.
- No push, merge, or other worktree change occurred.
- New release output contains no source speaker ID, speaker-token collection, per-speaker row, demographic slice, or state/signal label.
- All eight release boundary booleans are exact `false` constants.
- The contract describes itself exactly as a `suppression-based, privacy-minimized contribution gate`.

## Changed Source Files

- `scripts/emotion_state_cohort_release_contracts.py`
- `research/sources/emotion_state/cohort_release_evidence_v1.schema.json`
- `research/experiments/cases/emotion-state-001-cohort-release-fixtures.json`
- `scripts/test_emotion_state_001_open_dataset_gate.py`
- `scripts/emotion_state_phase_a_contracts.py`
- `scripts/validate_emotion_state_001_phase_a_contracts.py`

## Concerns

None within Task 4 scope. This remains an offline Phase A contract gate and does not authorize dataset material access, a live identity mechanism, customer-data processing, aggregate publication, confirmatory claims, provider activity, or runtime influence.

## Commit

- Subject: `Add EMOTION-STATE cohort release gate`
- SHA: `7cc288a8e69a8504cc8ce7728450698debbcdf32`

## 2026-07-16 Independent Review-Fix Resume

### Preserved Resume State

- Resumed the existing uncommitted review-fix patch at exact HEAD `7cc288a8e69a8504cc8ce7728450698debbcdf32` on `codex/emotion-state-phase-a-open-dataset-gate-design`.
- Initial status contained only the preserved unstaged changes in `scripts/emotion_state_cohort_release_contracts.py` and `scripts/test_emotion_state_001_open_dataset_gate.py`; no staged changes existed.
- No existing patch content was discarded, reverted, reset, stashed, or overwritten.

### Live RED Evidence

1. Command: `python -m unittest scripts.test_emotion_state_001_open_dataset_gate.CohortReleaseTests -v`
   - Exit: `1`.
   - Result before the resumed fixes: `Ran 27 tests`; `FAILED (failures=9, errors=7)`.
   - Exact remaining categories reproduced: an ineligible foreign-corpus record released instead of suppressing; four exact-integer lookalikes were accepted; `evaluate_discovery_gate` was missing; four suppression-reason contradictions were accepted; and six malformed request enum values leaked `TypeError`.
   - The authoritative-history/digest/replacement, membership-derived support, and strict sparse-shape review additions remained green in this RED run.
2. The required 28th method, `test_discovery_gate_requires_both_minimum_thresholds`, was added before production implementation.
   - Focused RED command: `python -m unittest scripts.test_emotion_state_001_open_dataset_gate.CohortReleaseTests.test_discovery_gate_requires_both_minimum_thresholds -v`.
   - Exit: `1`; expected `ImportError: cannot import name 'evaluate_discovery_gate'`.
3. A direct zero-support sparse-cell regression was added before its fix.
   - Focused RED command: `python -m unittest scripts.test_emotion_state_001_open_dataset_gate.CohortReleaseTests.test_sparse_output_cells_are_omitted_not_zeroed -v`.
   - Exit: `1`; exact failure was `KeyError: 'usable'` at `_filter_supported_cells` when no selected record claimed that aggregate cell.

### Review Fixes Applied

- Dataset IDs are validated and collected for every input record before eligibility filtering, so an ineligible foreign-corpus record still produces `cross_corpus_identity_not_proven`.
- Contribution-cap and both release-minimum constants now require exact `int` values; booleans and floating-point lookalikes fail closed.
- Added production `evaluate_discovery_gate(records)` with deterministic namespaced-speaker ordering, a two-turn cap per speaker, and exact five-speaker/ten-retained-turn eligibility thresholds.
- Added the frozen five-code suppression-reason set plus evidence-derived speaker-basis, minimum-speaker, and dedup consistency checks.
- Added string type guards before request/release enum membership checks so malformed unhashable values raise deterministic `ValueError`.
- Sparse dictionary cells with no derived speaker membership now receive zero support internally and are omitted rather than serialized or dereferenced with `KeyError`.
- Removed the caller-provided output-cell count boundary, retained membership-derived counts after deterministic contribution capping, retained strict sparse aggregate validation, and retained authoritative full-history/digest/replacement validation.

### GREEN And Verification Evidence

- `python -m unittest scripts.test_emotion_state_001_open_dataset_gate.CohortReleaseTests -v`
  - Exit `0`; `Ran 28 tests`; `OK`.
- `python -m unittest scripts.test_emotion_state_001_open_dataset_gate -v`
  - Exit `0`; `Ran 47 tests`; `OK`.
- `python scripts\validate_emotion_state_001_phase_a_contracts.py --section contracts`
  - Exit `0`; `EMOTION-STATE-001 Phase A validation passed: contracts`.
- `python -m py_compile scripts\emotion_state_cohort_release_contracts.py scripts\test_emotion_state_001_open_dataset_gate.py`
  - Exit `0`; no output.
- `python -m json.tool research\sources\emotion_state\cohort_release_evidence_v1.schema.json`
  - Exit `0`; valid JSON.
- `python -m json.tool research\experiments\cases\emotion-state-001-cohort-release-fixtures.json`
  - Exit `0`; valid JSON.
- `git diff --exit-code 7cc288a^ -- runtime\contracts\emotion_state_contracts.py runtime\contracts\emotion_pattern_contracts.py`
  - Exit `0`; no runtime contract diff across Task 4.
- `git diff --exit-code 7cc288a^ -- research\sources\emotion_state\split_manifest_v1.schema.json scripts\emotion_state_annotation_contracts.py`
  - Exit `0`; no frozen v1 split-contract diff across Task 4.
- `git diff --check`
  - Exit `0`; no whitespace errors. Git emitted only the existing LF-to-CRLF working-copy warnings for the two changed Python files.
- The complete staged verification set above was rerun immediately before the review-fix commit; every command exited `0`, including `git diff --cached --check`.

### Boundary And Remaining Concern

- This remained synthetic-fixture, local, offline contract/test work only.
- No ElevenLabs or other provider access, outbound/customer calls, simulations, dataset downloads, private-data inspection, source adaptation, runtime behavior activation, push, or merge occurred.
- This does not establish production readiness, anonymity, differential privacy, or proof against re-identification.
- The complete authoritative history and its digest still depend on an external append-only release registry. Phase A validates supplied evidence but does not implement or authenticate that registry.
- Task 5 was not started.
