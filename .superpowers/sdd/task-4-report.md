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

## 2026-07-16 Round 2 Cohort Release Review Closure

### Preserved Review State

- Resumed at exact HEAD `a40a46ece7cf0f6c7c01a2e3d60c9bf6ee3c9b8` on `codex/emotion-state-phase-a-open-dataset-gate-design`.
- Preserved the controller-appended Round 2 findings in `.superpowers/sdd/task-4-review-findings.md`; no finding or existing test assertion was removed or weakened.

### Round 2 RED Evidence

1. Count-map aggregate/support contradiction:
   - Focused command: `python -m unittest scripts.test_emotion_state_001_open_dataset_gate.CohortReleaseTests.test_count_map_values_must_match_membership_derived_support -v`.
   - Exit `1`; `Ran 1 test`; `FAILED (failures=4)`.
   - The five/five single-membership, five/five dual-membership, zero-count/nonzero-membership, and standalone released-count contradiction cases all failed because no `ValueError` was raised.
2. Mixed-corpus discovery:
   - Focused command: `python -m unittest scripts.test_emotion_state_001_open_dataset_gate.CohortReleaseTests.test_discovery_gate_rejects_mixed_dataset_input -v`.
   - Exit `1`; `Ran 1 test`; `FAILED (failures=1)` because the mixed-dataset cohort was accepted instead of failing closed.
3. Standalone and authoritative-history invariants:
   - Focused command: `python -m unittest scripts.test_emotion_state_001_open_dataset_gate.CohortReleaseTests.test_standalone_release_rejects_source_basis_and_basis_null_contradictions scripts.test_emotion_state_001_open_dataset_gate.CohortReleaseTests.test_authoritative_history_rejects_invalid_source_basis_and_basis_null_entries -v`.
   - Exit `1`; `Ran 2 tests`; `FAILED (failures=3)`.
   - Standalone validation accepted the synthetic-basis/public-source contradiction; authoritative history accepted both that contradiction and a basis-null entry with selected records. The standalone basis-null subcases were behind the first failing assertion in that RED run and were exercised after the shared fix.

### Round 2 Fixes

- Count-map metrics now require each aggregate cell value to equal membership-derived unique-speaker support after deterministic one-record-per-speaker selection. Zero aggregate cells with zero membership remain valid and sparse output omission remains unchanged; zero-count/nonzero-membership and every other mismatch fail closed.
- `evaluate_discovery_gate(records)` now collects every validated dataset ID before eligibility filtering and raises `ValueError` for mixed-dataset discovery input before threshold evaluation.
- Request construction, standalone release validation, and authoritative-history entry validation now share the exact public/synthetic source-to-speaker-basis invariant.
- Basis-null release evidence now requires zero selected records, zero unique speakers, and a null dedup evidence digest.

### Round 2 GREEN And Verification Evidence

- Exact adversarial regression command: `python -m unittest scripts.test_emotion_state_001_open_dataset_gate.CohortReleaseTests.test_count_map_values_must_match_membership_derived_support scripts.test_emotion_state_001_open_dataset_gate.CohortReleaseTests.test_discovery_gate_rejects_mixed_dataset_input scripts.test_emotion_state_001_open_dataset_gate.CohortReleaseTests.test_standalone_release_rejects_source_basis_and_basis_null_contradictions scripts.test_emotion_state_001_open_dataset_gate.CohortReleaseTests.test_authoritative_history_rejects_invalid_source_basis_and_basis_null_entries -v`.
  - Exit `0`; `Ran 4 tests`; `OK`.
  - Covered five/five single membership, five/five dual membership, zero-count/nonzero-membership, standalone count/support mismatch, mixed-corpus discovery, standalone source/basis mismatch, all three basis-null fields, and invalid authoritative-history entries.
- `python -m unittest scripts.test_emotion_state_001_open_dataset_gate.CohortReleaseTests -v`
  - Exit `0`; `Ran 32 tests`; `OK`.
- `python -m unittest scripts.test_emotion_state_001_open_dataset_gate -v`
  - Exit `0`; `Ran 51 tests`; `OK`.
- `python scripts\validate_emotion_state_001_phase_a_contracts.py --section contracts`
  - Exit `0`; `EMOTION-STATE-001 Phase A validation passed: contracts`.
- `python -m py_compile scripts\emotion_state_cohort_release_contracts.py scripts\test_emotion_state_001_open_dataset_gate.py`
  - Exit `0`; no output.
- `python -m json.tool research\sources\emotion_state\cohort_release_evidence_v1.schema.json`
  - Exit `0`; valid JSON.
- `python -m json.tool research\experiments\cases\emotion-state-001-cohort-release-fixtures.json`
  - Exit `0`; valid JSON.
- `git diff --exit-code 7cc288a^ -- runtime\contracts\emotion_state_contracts.py runtime\contracts\emotion_pattern_contracts.py`
  - Exit `0`; no Task 4 runtime-contract diff.
- `git diff --exit-code 7cc288a^ -- research\sources\emotion_state\split_manifest_v1.schema.json scripts\emotion_state_annotation_contracts.py`
  - Exit `0`; no frozen v1 split-contract diff.

### Round 2 Boundary And Remaining Concern

- This remained synthetic-fixture, local, offline contract/test work only.
- No ElevenLabs or other provider access, outbound/customer calls, simulations, dataset downloads, private-data inspection, source adaptation, runtime activation, push, or merge occurred.
- This does not establish production readiness, anonymity, differential privacy, or proof against re-identification.
- The external append-only authoritative release registry remains outside Phase A; this code validates supplied history evidence but does not authenticate its origin.
- Task 5 was not started.
- Intended commit subject: `Close EMOTION-STATE cohort release review gaps`.

## 2026-07-16 Round 3 Pass-4 Closure

### Preserved Resume State

- Resumed at exact HEAD `03af343f5ea4a2f3947a145627c604313e78b8b0` on `codex/emotion-state-phase-a-open-dataset-gate-design`.
- The initial dirty state contained only the controller-appended Round 3 section in `.superpowers/sdd/task-4-review-findings.md`. It was preserved unchanged and included with this closure; no reset, stash, revert, or overwrite occurred.
- All work remained inside the linked `emotion-state-layer-design` worktree.

### Pass-4 RED Evidence

1. Append-ordered authoritative history:
   - First focused command: `python -m unittest scripts.test_emotion_state_001_open_dataset_gate.CohortReleaseTests.test_authoritative_history_accepts_ordered_replacement_chain_and_later_release -v`.
   - Exit `1`; `Ran 1 test`; `FAILED (errors=1)` at the second replacement with exact error `ValueError: authoritative release history must use canonical window order`.
   - Expanded three-test history RED: exit `1`; `FAILED (failures=4, errors=1)`. The validator rejected a valid root-to-replacement-to-replacement chain, while accepting missing predecessors, arbitrary equal digests, and a changed-window successor. Reordered successors, stale forks, and distinct-chain overlap were also retained as negative regressions.
2. Count-map record cardinality:
   - Focused command: `python -m unittest scripts.test_emotion_state_001_open_dataset_gate.CohortReleaseTests.test_each_selected_record_has_exactly_one_cell_per_count_map_metric -v`.
   - Exit `1`; `Ran 1 test`; `FAILED (failures=2)` because the balanced 20-speaker dual-plus-empty construction was accepted for both `audio_quality_bucket_counts` and `evidence_policy_version_counts`.
3. Record provenance and canonical record evidence:
   - Initial release/discovery command over the two new provenance methods exited `1` with `FAILED (failures=11)`: private/arbitrary datasets, an email-shaped actor ID, both wrong public dataset-to-basis mappings, an uncontrolled synthetic namespace, wrong CREMA ID syntax in discovery, and forged canonical record digests were accepted.
   - After the official AMI participant/meeting distinction was confirmed, explicit AMI meeting-ID-as-participant cases were added before production work. The expanded RED exited `1` with `FAILED (failures=13)`.
4. Standalone and authoritative-history counts:
   - Focused direct/history command exited `1`; `Ran 2 tests`; `FAILED (failures=7)` because `eligible > unique`, `unique > input`, non-null dedup with unequal eligible/unique counts, and null dedup with selected records were accepted directly and in history entries.
5. Complete schema/fixture parity:
   - Focused command exited `1`; `Ran 1 test`; `FAILED (errors=1)` with the expected missing `cohort_release_fixture_descriptor` import before the complete descriptor implementation.
6. Self-review unhashable provenance regression:
   - The expanded malformed-value test exited `1` with four errors because list/dict `dataset_manifest_id` values leaked `TypeError: unhashable type` in both release and discovery paths.

### Pass-4 Fixes

- Authoritative history now uses caller-supplied list order as append/dependency order. A root has null replacement digests. A replacement must target the canonical digest of the unique earlier active head, preserve its exact window, fixed-window ID, and metric allowlist, and supersede that head. Dangling/forward/reordered references, stale-head forks, duplicate releases, and overlap across distinct window chains fail closed. Candidate replacements target only the active head named by their digest.
- Every deterministically selected record now has exactly one membership cell for each count-map metric. Exact aggregate-value-to-membership-support equality and sparse cell omission remain enforced.
- Release and discovery now share structural record-provenance validation. CREMA-D binds to exact dataset ID `crema-d-v1.0-audio-wav`, actor basis, and four-digit actor IDs. AMI binds to exact dataset ID `ami-manual-annotations-v1.6.2`, participant basis, and the conservative participant-ID grammar `^[MF][IET][EDO][0-9]{3}(?:PM|ID|ME|UID)?$`. `ES`/`IS`/`TS`/`EN` meeting IDs are rejected as participant identities. Synthetic records bind to the explicit controlled fixture dataset set and `fixture-speaker-NNN` IDs.
- Canonical record digests now bind one frozen domain-separated projection of every record evidence field except the digest itself, including eligibility and all metric-cell memberships. Fixture generation and mutated test setup recompute this digest explicitly.
- Standalone and history-entry evidence now enforces `0 <= eligible_record_count <= unique_speaker_count <= input_record_count`, non-null dedup implies eligible equals unique, and null dedup implies zero eligible records. Existing selection-failure reason/digest consistency remains active.
- The contracts validator and unit tests now compare the complete schema and fixture descriptors through type-sensitive canonical JSON, including contract name, source labels, release statuses, thresholds, false constants, provenance/history boundaries, and every named scenario expectation. A boolean-to-integer mutation is explicitly proven unequal.
- Malformed unhashable dataset IDs now raise deterministic `ValueError` before set membership in both release and discovery paths.

### Official AMI Identifier Boundary

- The official [AMI participant-ID documentation](https://groups.inf.ed.ac.uk/ami/corpus/participantids.shtml) distinguishes participant identifiers and their limited role suffixes.
- The official [AMI meeting-ID documentation](https://groups.inf.ed.ac.uk/ami/corpus/meetingids.shtml) confirms that identifiers beginning with `ES`, `IS`, `TS`, or `EN` are meeting identifiers, not participant keys.
- These sources informed structural validation facts only. No external source code, dataset material, annotation data, or source adaptation was used.

### Existing-Assertion Preservation

- No existing assertion was removed, weakened, or rewritten.
- Test setup changed only where the new provenance contract made the previous synthetic placeholders structurally invalid: `public-fixture-v1` became the exact CREMA-D dataset fixture; the ineligible foreign-corpus case now uses the second controlled synthetic fixture corpus; and membership/eligibility mutations explicitly refresh their canonical record digests.
- The existing `count-map.*support` assertion remains unchanged; the new cardinality error text was kept compatible with it.

### Final GREEN And Verification Evidence

- `python -m unittest scripts.test_emotion_state_001_open_dataset_gate.CohortReleaseTests -v`
  - Exit `0`; `Ran 41 tests`; `OK`.
- `python -m unittest scripts.test_emotion_state_001_open_dataset_gate -v`
  - Exit `0`; `Ran 60 tests`; `OK`.
- Pass-2 four-method adversarial slice from the Round 2 report
  - Exit `0`; `Ran 4 tests`; `OK`.
- Pass-3/pass-4 ten-method history, cardinality, provenance, count, parity, and malformed-value slice
  - Exit `0`; `Ran 10 tests`; `OK`.
- `python scripts\validate_emotion_state_001_phase_a_contracts.py --section contracts`
  - Exit `0`; `EMOTION-STATE-001 Phase A validation passed: contracts`.
- `python -m py_compile scripts\emotion_state_cohort_release_contracts.py scripts\test_emotion_state_001_open_dataset_gate.py scripts\validate_emotion_state_001_phase_a_contracts.py`
  - Exit `0`; no output.
- `python -m json.tool research\sources\emotion_state\cohort_release_evidence_v1.schema.json`
  - Exit `0`; valid JSON.
- `python -m json.tool research\experiments\cases\emotion-state-001-cohort-release-fixtures.json`
  - Exit `0`; valid JSON.
- `git diff --exit-code 7cc288a^ -- runtime\contracts\emotion_state_contracts.py runtime\contracts\emotion_pattern_contracts.py`
  - Exit `0`; no Task 4 runtime-contract diff.
- `git diff --exit-code 7cc288a^ -- research\sources\emotion_state\split_manifest_v1.schema.json scripts\emotion_state_annotation_contracts.py`
  - Exit `0`; no frozen v1 split-contract diff.
- `git diff --check`
  - Exit `0`; no whitespace errors. Git emitted only the existing LF-to-CRLF working-copy warnings.

### Corrected Trust And Readiness Boundaries

- Phase A validates dependency consistency inside the supplied authoritative history, but it cannot authenticate the relative append order or origin of unrelated root releases without a signed sequence from the external append-only registry. That registry remains outside this implementation.
- Dataset ID/basis/identifier syntax and canonical record digests are structural checks. They do not authenticate that external material is genuine, that a public identifier assignment is authoritative, or that the caller supplied the complete registry or dataset evidence.
- This remains a local, offline Phase A research/prototype contract gate only. It does not establish production readiness, anonymity, differential privacy, or proof against re-identification.
- No ElevenLabs or other provider access, outbound/customer calls, simulations, dataset downloads, private-data inspection, source adaptation, runtime activation, push, or merge occurred.
- Task 5 was not started.
- Intended commit subject: `Complete EMOTION-STATE cohort release chain validation`.
