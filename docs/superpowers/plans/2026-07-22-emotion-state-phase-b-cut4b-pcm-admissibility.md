# Phase B Cut 4B PCM Endpoint Admissibility Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Replace the false `PCM16 endpoint present => clipped WAV` rejection with an exact, threshold-free v2 admissibility contract, route all new Phase B production lineage into a fresh ignored root, and run one independently reviewed replacement non-lockbox attempt without touching the retired lineage or any prohibited surface.

**Architecture:** Keep the 17-feature extractor and all existing structural/feature-viability gates unchanged except for deleting the two-line endpoint-presence rejection. Bind that behavior through a new tracked v2 feature-schema authority and the existing cache/packet transitive digest fields. Keep the v1 schema byte-exact as historical authority. Route `RunnerPaths.production()` state, split, preflight, non-lockbox, control, and recovery surfaces to `.tmp/emotion-state-002-phase-b-cut4b`, while continuing to read the already verified dependency environment and wheelhouse under the retired root as immutable dependency inputs. Treat the retired split/preflight/non-lockbox lineage as opaque: only an aggregate metadata/byte fingerprint may be computed to prove immutability.

**Tech Stack:** Python 3.11, NumPy, SciPy, scikit-learn, `unittest`, strict JSON contracts, PowerShell, Git.

---

## Fixed authority and boundaries

- Approved design: `docs/superpowers/specs/2026-07-22-emotion-state-phase-b-cut4b-pcm-admissibility-design.md`.
- Design/plan base HEAD: `cb62a82d870b583bbe96c463458e5224e0f68eb4` (`Pin Cut 4B schema field order`).
- New production lineage root: `.tmp/emotion-state-002-phase-b-cut4b`.
- Retired lineage root: `.tmp/emotion-state-002-phase-b`.
- Immutable dependency environment: `.tmp/emotion-state-002-phase-b/venv`.
- Immutable dependency wheelhouse: `.tmp/emotion-state-002-phase-b/dependencies/wheelhouse`.
- Historical v1 static file SHA-256: `81B55B25F405A99ED7B29449631CFD39B2FE6E1D4F500ADA3BBCD8668790AB75`.
- Historical v1 semantic SHA-256: `70A5B1531D5127D37FD89B30F03EC14682B0B6C97850A5452DEEB59033618EF4`.
- Required v2 static file SHA-256: `C2A7DE308BAD32C3798016061777669881E7FDD3403979DCCC166DCE38F307C4`.
- Required v2 semantic SHA-256: `AEC550285DF6A92B3E86E16F66A2E5B554836BBE47C625106F517EB0CF1375DB`.
- Feature-cache schema v1 and packet schema v4 structures remain unchanged; their existing `feature_schema_sha256` and cache self-commitments bind v2 transitively.
- No endpoint rate threshold, run-length threshold, clipping classifier, feature, label, or exclusion is authorized.
- No parsing, reuse, deletion, recovery, cleanup, or mutation of retired split/preflight/non-lockbox lineage is authorized.
- No private data, provider access, calls, simulations, source adaptation, network, new download, dependency install/update, runtime activation, final-lockbox access, canonical staging/acceptance, push, merge, history rewrite, or Phase C work.
- The aggregate endpoint diagnostic is contextual evidence only and must not become a production input.
- Stop on the first unresolved blocker. No second production attempt is implicit.

## Task 1: Establish the strict RED contract

**Files:**

- Modify: `scripts/test_emotion_state_002_phase_b.py`
- Read only: `research/sources/emotion_state/emotion_state_phase_b_feature_v1.schema.json`
- Read only: `scripts/emotion_state_phase_b_features.py`
- Read only: `scripts/validate_emotion_state_002_phase_b.py`
- Read only: `scripts/run_emotion_state_002_phase_b.py`

Do not commit RED-only changes. They are part of the single Cut 4B behavior-changing commit after GREEN and independent review.

### Step 1: Split the schema test constants

At the top of `scripts/test_emotion_state_002_phase_b.py`, retain an explicit historical path and make the active path v2:

```python
FEATURE_SCHEMA_V1 = (
    ROOT
    / "research/sources/emotion_state/emotion_state_phase_b_feature_v1.schema.json"
)
FEATURE_SCHEMA = (
    ROOT
    / "research/sources/emotion_state/emotion_state_phase_b_feature_v2.schema.json"
)
```

Leave `WHEELHOUSE`, `EVALUATION_PYTHON`, and `ENVIRONMENT_TEST_TEMP` under `.tmp/emotion-state-002-phase-b`; those are fixed dependency inputs, not new lineage.

### Step 2: Add the exact v2/v1 authority test

Add `PhaseBContractTests.test_feature_schema_v2_endpoint_policy_and_v1_history_are_exact`.

It must assert:

```python
self.assertEqual(
    hashlib.sha256(FEATURE_SCHEMA_V1.read_bytes()).hexdigest().upper(),
    "81B55B25F405A99ED7B29449631CFD39B2FE6E1D4F500ADA3BBCD8668790AB75",
)
self.assertEqual(
    hashlib.sha256(FEATURE_SCHEMA.read_bytes()).hexdigest().upper(),
    "C2A7DE308BAD32C3798016061777669881E7FDD3403979DCCC166DCE38F307C4",
)
```

Load both schemas strictly. Treat v1 only as historical bytes and assert `validate_feature_schema(v1)` fails because production requires v2. Assert `canonical_payload_sha256(v2)` is `AEC550285DF6A92B3E86E16F66A2E5B554836BBE47C625106F517EB0CF1375DB`. Assert v2 validates and has exact root insertion order with `pcm_endpoint_admissibility` immediately after `channel_count`. Assert the nested key order and exact built-in JSON types/values:

```python
(
    "policy_id",
    "endpoint_values",
    "presence_interpretation",
    "reject_on_presence",
    "rate_threshold",
    "run_length_threshold",
    "clipping_classification_implemented",
)
```

Mutate each policy scalar, endpoint value/order, key set, root position, threshold, and boolean flag; every mutation must fail closed. Reuse the existing exhaustive exact-object mutation helper where possible.

### Step 3: Replace the false clipping test and add the endpoint-positive test

Rename `test_unsupported_wav_formats_malformed_riff_and_clipping_reject` to `test_unsupported_wav_formats_and_malformed_riff_reject` and remove only its two one-sample endpoint rejection cases. Preserve its stereo, sample-width, sample-rate, compression, and malformed-RIFF assertions.

Add `AcousticFeatureTests.test_pcm_endpoints_are_observations_not_clipping_rejections`. Build an otherwise viable deterministic 200 Hz mono PCM16/16 kHz waveform long enough to satisfy every frozen feature gate. Replace samples in copies so the cases collectively include:

- `32767`;
- `-32768`;
- both endpoint values; and
- at least one consecutive same-endpoint run of 10 samples.

For every case, call `extract_acoustic_features_bytes()`, assert the exact 17-name order, assert every output is a built-in finite `float`, and assert `f0_median_hz` remains near 200 Hz. Do not assert audio quality or clipping absence.

### Step 4: Freeze cache rejection of the v1 semantic identity

Extend `ProductionNonLockboxBuilderTests.test_feature_caches_are_exact_role_bound_deterministic_and_replayable` after its valid-cache assertions:

```python
legacy = deepcopy(first["training_discovery"])
legacy["feature_schema_sha256"] = (
    "70A5B1531D5127D37FD89B30F03EC14682B0B6C97850A5452DEEB59033618EF4"
)
legacy = reseal(legacy)
with self.assertRaises(ValueError):
    validate(legacy)
```

This proves cache schema v1 can stay structurally unchanged while v1 feature authority is rejected under the v2 run.

### Step 5: Freeze fresh production paths and old dependency paths

Add `Task10ProductionPipelineTests.test_cut4b_production_paths_use_fresh_lineage_and_fixed_dependencies`.

Assert:

```python
paths = RunnerPaths.production()
new_root = ROOT / ".tmp" / "emotion-state-002-phase-b-cut4b"
old_root = ROOT / ".tmp" / "emotion-state-002-phase-b"
self.assertEqual(paths.state_root, new_root)
self.assertEqual(
    paths.feature_schema_path,
    ROOT / "research/sources/emotion_state/emotion_state_phase_b_feature_v2.schema.json",
)
```

For each of these exact state-derived paths, assert `relative_to(new_root)` succeeds and `relative_to(old_root)` raises `ValueError`:

```python
(
    paths.state_path,
    paths.material_pipeline_lock_path,
    paths.preflight_state_stage_path,
    paths.non_lockbox_state_stage_path,
    paths.non_lockbox_state_intent_path,
    paths.non_lockbox_state_prior_path,
    paths.split_manifest_path,
    paths.input_ledger_path,
    paths.non_lockbox_packet_path,
    paths.preflight_cache_root,
    paths.non_lockbox_root,
    paths.non_lockbox_cache_root,
    paths.recovery_root,
    paths.journal_path,
    paths.lockbox_root,
    paths.final_lockbox_cache_root,
    paths.lockbox_lock_path,
    paths.lockbox_reservation_path,
)
```

Separately assert `paths.lockbox_result_path is None`, and assert `EVALUATION_PYTHON` and `WHEELHOUSE` remain under `old_root` and outside `new_root`.

### Step 6: Replace the stale live-status contract

Rename `test_task_9_docs_hold_review_pending_status` to `test_cut4b_docs_hold_transaction_pending_status` and require this exact live sentence in both `docs/thesis/ROADMAP.md` and `research/experiments/EMOTION-STATE-002-phase-b-public-data-feasibility.md`:

```text
Cut 4B implementation and independent review are prerequisites to one fresh Task 10 replacement transaction under `.tmp/emotion-state-002-phase-b-cut4b`; until that transaction passes aggregate-only independent review, no non-lockbox checkpoint is accepted.
```

Also require both documents to state that the retired lineage is not reused or mutated and that final lockbox, canonical publication, push, merge, runtime activation, Phase C, providers, private data, calls, simulations, and source adaptation remain blocked.

### Step 7: Run RED and retain the evidence in the implementation report

Run with the verified immutable interpreter:

```powershell
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe -m unittest scripts.test_emotion_state_002_phase_b.PhaseBContractTests.test_feature_schema_v2_endpoint_policy_and_v1_history_are_exact -v
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe -m unittest scripts.test_emotion_state_002_phase_b.AcousticFeatureTests.test_pcm_endpoints_are_observations_not_clipping_rejections -v
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe -m unittest scripts.test_emotion_state_002_phase_b.ProductionNonLockboxBuilderTests.test_feature_caches_are_exact_role_bound_deterministic_and_replayable -v
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe -m unittest scripts.test_emotion_state_002_phase_b.Task10ProductionPipelineTests.test_cut4b_production_paths_use_fresh_lineage_and_fixed_dependencies -v
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe -m unittest scripts.test_emotion_state_002_phase_b.PhaseBContractTests.test_cut4b_docs_hold_transaction_pending_status -v
```

Expected RED:

- v2 schema path is absent or the validator remains v1-only;
- endpoint-bearing viable audio raises `WAV contains clipped samples`;
- a cache carrying the v1 semantic identity is still accepted because v1 is the current authority;
- production paths still resolve under `.tmp/emotion-state-002-phase-b`.
- the live thesis/experiment documents do not yet contain the Cut 4B transaction-pending status.

If a test passes before implementation, stop and explain why it does not prove the intended missing behavior. Do not weaken a test to manufacture RED.

## Task 2: Implement the endpoint-neutral v2 contract and fresh routing

**Files:**

- Create: `research/sources/emotion_state/emotion_state_phase_b_feature_v2.schema.json`
- Modify: `scripts/emotion_state_phase_b_features.py`
- Modify: `scripts/validate_emotion_state_002_phase_b.py`
- Modify: `scripts/run_emotion_state_002_phase_b.py`
- Modify: `scripts/test_emotion_state_002_phase_b.py`
- Modify: `docs/superpowers/plans/2026-07-19-emotion-state-phase-b-public-data-feasibility.md`
- Modify: `docs/product/COMMANDS.md`
- Modify: `docs/thesis/METHODOLOGY_LOG.md`
- Modify: `docs/thesis/ROADMAP.md`
- Modify: `research/experiments/EMOTION-STATE-002-phase-b-public-data-feasibility.md`

### Step 1: Create the exact v2 schema

Copy the v1 object without changing the v1 file. In v2, change only:

```json
"schema_id": "emotion-state-crema-interpretable-acoustic-v2",
"schema_version": 2
```

Insert immediately after `"channel_count": 1`:

```json
"pcm_endpoint_admissibility": {
  "policy_id": "emotion-state-pcm16-endpoint-admissibility-v1",
  "endpoint_values": [
    -32768,
    32767
  ],
  "presence_interpretation": "numeric_saturation_observation_not_clipping_proof",
  "reject_on_presence": false,
  "rate_threshold": null,
  "run_length_threshold": null,
  "clipping_classification_implemented": false
},
```

Preserve the v1 decimal spelling `0.00000152587890625`, LF bytes, two-space indentation, terminal newline, all 17 feature names, and every remaining field/value/order.

Verify exact identities:

```powershell
Get-FileHash research/sources/emotion_state/emotion_state_phase_b_feature_v1.schema.json -Algorithm SHA256
Get-FileHash research/sources/emotion_state/emotion_state_phase_b_feature_v2.schema.json -Algorithm SHA256
```

Expected: v1 `81B55B...AB75`; v2 `C2A7DE...7C4`.

### Step 2: Bind the validator to v2

In `scripts/validate_emotion_state_002_phase_b.py`:

- point `FEATURE_SCHEMA_PATH` to `emotion_state_phase_b_feature_v2.schema.json`;
- change root id/version in `EXPECTED_FEATURE_SCHEMA` to v2/2;
- insert the exact `pcm_endpoint_admissibility` mapping after `channel_count` with the approved key order and built-in values;
- change `EXPECTED_STATIC_FILE_SHA256["feature_schema_sha256"]` to `C2A7DE308BAD32C3798016061777669881E7FDD3403979DCCC166DCE38F307C4`;
- change `EXPECTED_EVIDENCE_IDENTITY_SHA256["feature_schema_sha256"]` to `AEC550285DF6A92B3E86E16F66A2E5B554836BBE47C625106F517EB0CF1375DB`;
- make `validate_feature_schema()` require id `emotion-state-crema-interpretable-acoustic-v2`;
- retain `_validate_exact()` as the final exact graph/type/order check.

Do not change feature-cache or packet structural schemas.

### Step 3: Remove only the false endpoint rejection

In `_read_pcm16_mono_16khz_bytes()` in `scripts/emotion_state_phase_b_features.py`, delete exactly:

```python
if np.any((pcm == -32768) | (pcm == 32767)):
    raise FeatureExtractionError("WAV contains clipped samples")
```

Make no other reader, normalization, frame, silence, spectral, voicing, feature, or error-path change.

### Step 4: Route fresh lineage without moving dependencies

In `RunnerPaths.production()` in `scripts/run_emotion_state_002_phase_b.py`:

```python
state_root = root / ".tmp" / "emotion-state-002-phase-b-cut4b"
```

Point `feature_schema_path` to v2. Keep `_held_environment_wheel_inputs()` and all installed-environment checks bound to `.tmp/emotion-state-002-phase-b/dependencies/wheelhouse` and `.tmp/emotion-state-002-phase-b/venv` respectively.

Do not add a fallback, migration, cleanup, recovery, or old-lineage read path.

### Step 5: Correct the live plan, command map, experiment status, and thesis trace

Apply an explicit Cut 4B overlay near the top of `docs/superpowers/plans/2026-07-19-emotion-state-phase-b-public-data-feasibility.md` rather than rewriting historical v1/Cut 4 sections. The overlay must state:

- v2 supersedes v1 for new production execution;
- new state root is exact;
- the old root's lineage is retired and opaque;
- old venv/wheelhouse remain immutable dependencies;
- only one fresh replacement attempt is allowed;
- Task 10 is aggregate-only and final-lockbox/canonical/Phase C remain blocked.

Mechanically update active Task 10/11/future receipt state paths to `.tmp/emotion-state-002-phase-b-cut4b`, while keeping command executables under `.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe`. Make the same receipt-state correction in `docs/product/COMMANDS.md`.

Append a dated Cut 4B entry to `docs/thesis/METHODOLOGY_LOG.md`; do not rewrite historical entries. Record:

- final Cut 4A review passed;
- the first replacement attempt failed before linearization on `WAV contains clipped samples`;
- aggregate diagnostic scope/counts and its non-perceptual limitation;
- endpoint-neutral v2 decision and exact hashes;
- retired/new lineage roots and immutable dependency exception;
- RED/GREEN/full-suite evidence;
- the still-blocked boundaries.

Update `docs/thesis/ROADMAP.md` and the experiment brief with the exact live status sentence frozen in Task 1. Describe the implementation as pending independent review/one fresh replacement transaction; do not claim Task 10 completion.

### Step 6: Run focused GREEN tests

```powershell
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe -m unittest scripts.test_emotion_state_002_phase_b.PhaseBContractTests -v
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe -m unittest scripts.test_emotion_state_002_phase_b.AcousticFeatureTests -v
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe -m unittest scripts.test_emotion_state_002_phase_b.ProductionNonLockboxBuilderTests.test_feature_caches_are_exact_role_bound_deterministic_and_replayable -v
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe -m unittest scripts.test_emotion_state_002_phase_b.Task10ProductionPipelineTests -v
```

Expected: `14`, `19`, `1`, and `14` tests pass respectively, subject to the exact discovered baseline counts. Any count drift must be explained by named test additions/removals, not ignored.

### Step 7: Run the full correction ledger

```powershell
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe -m unittest scripts.test_emotion_state_002_phase_b -v
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe scripts/validate_emotion_state_002_phase_b.py source
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe scripts/validate_emotion_state_002_phase_b.py contracts
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe scripts/validate_emotion_state_002_phase_b.py environment
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe scripts/validate_emotion_state_002_phase_b.py synthetic
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe -m py_compile scripts/emotion_state_phase_b_features.py scripts/validate_emotion_state_002_phase_b.py scripts/run_emotion_state_002_phase_b.py scripts/test_emotion_state_002_phase_b.py
python scripts/check_thesis_update_gate.py
python scripts/check_thesis_reference_registry.py
python scripts/validate_project_drift_guard.py
python scripts/validate_context_reading_policy.py
python scripts/validate_check_setup.py
git diff --check
git status --short
```

Expected full test count: `348/348` if exactly three test methods are added and the old clipping method is renamed in place. All validator/gate commands must exit zero. The only changed paths must be the ten listed Task 2 paths plus this already-committed implementation plan; the ignored production roots must not be touched during code verification.

### Step 8: Independently review before commit

Provide a fresh reviewer:

- the approved design;
- this plan;
- the exact RED/GREEN/full-ledger report;
- `git diff --stat`;
- `git diff --check`;
- the complete uncommitted diff;
- v1/v2 raw and semantic hashes;
- proof that the new production root has not been created; and
- proof that no retired-lineage or dependency file changed.

Required verdict: `SPEC_PASS` and `QUALITY_PASS`, with zero open Critical or Important findings. Corrections require focused RED/GREEN evidence and re-review.

### Step 9: Commit the one behavior-changing correction

```powershell
git add research/sources/emotion_state/emotion_state_phase_b_feature_v2.schema.json scripts/emotion_state_phase_b_features.py scripts/validate_emotion_state_002_phase_b.py scripts/run_emotion_state_002_phase_b.py scripts/test_emotion_state_002_phase_b.py docs/superpowers/plans/2026-07-19-emotion-state-phase-b-public-data-feasibility.md docs/product/COMMANDS.md docs/thesis/METHODOLOGY_LOG.md docs/thesis/ROADMAP.md research/experiments/EMOTION-STATE-002-phase-b-public-data-feasibility.md
git diff --cached --check
git commit -m "Correct Phase B PCM endpoint admissibility"
```

After commit, rerun `git status --short`, inspect `git show --stat --oneline HEAD`, and repeat the full correction ledger against committed HEAD. Do not push.

## Task 3: Execute one fresh Cut 4B replacement transaction

**Writes:** ignored state only under `.tmp/emotion-state-002-phase-b-cut4b`.

**Reads:** fixed tracked public CREMA-D/AMI materials, tracked contracts, immutable old venv/wheelhouse, and aggregate-only retired-lineage fingerprinting. No final lockbox/canonical surfaces.

This task is controller-owned and begins only after Task 2's independent approval and post-commit ledger pass.

### Step 1: Fingerprint the retired lineage without exposing it

In memory, inventory and hash the retired root. Prune exactly these two subtrees and no broader parent:

```text
venv
dependencies/wheelhouse
```

The `dependencies` directory entry and any other entry below it remain in the fingerprint. Use this exact canonical algorithm for all three comparisons:

1. Treat the retired root itself as the trusted traversal root but do not emit a record for it.
2. Inspect entries without following links. Reject any symbolic link, junction/reparse point, or non-file/non-directory entry.
3. Normalize each selected relative path to NFC UTF-8 with `/` separators. Reject duplicate normalized names.
4. Sort records by the unsigned lexicographic order of those UTF-8 path bytes.
5. Encode a directory record as byte `0x44`, then a four-byte unsigned big-endian path-byte length, then the path bytes.
6. Encode a file record as byte `0x46`, then the same path encoding, then an eight-byte unsigned big-endian file length, then the raw 32-byte SHA-256 of the exact file bytes.
7. Compute the aggregate SHA-256 over the concatenated record bytes and render it as 64 uppercase hexadecimal characters.
8. Count every encoded file/directory record in `entry_count`, every file record in `file_count`, and sum exact file lengths in `total_file_bytes`.

Use no timestamps, ACLs, inode/file IDs, locale-dependent comparison, JSON, or newline framing. Print only:

```text
entry_count=<integer>
file_count=<integer>
total_file_bytes=<integer>
aggregate_sha256=<64 uppercase hex>
```

Do not print, persist, parse, or reuse individual paths, payloads, identities, rows, labels, audio, probabilities, features, or contents. Retain the four aggregate values only in controller memory for the two later comparisons.

### Step 2: Prove clean admission

```powershell
git status --short
Test-Path .tmp/emotion-state-002-phase-b-cut4b
```

Expected: tracked worktree clean and `False`. If the new root exists, stop; do not delete or recover it.

### Step 3: Run exactly one fresh preflight

Use a child process with the network closed and inherited environment sanitized to the runner's existing allowlist:

```powershell
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe scripts/run_emotion_state_002_phase_b.py preflight
```

Expected: one fresh `preflight_complete` state under the Cut 4B root, with newly minted split/input lineage bound to the v2 semantic identity. Do not copy the retired manifest or ledger.

### Step 4: Independently validate preflight and retired immutability

A fresh reviewer must read only the new preflight state/contracts and report aggregate verdicts. It must prove:

- production paths resolve under the new root;
- feature schema is exact v2, with static hash `C2A7DE...7C4` and semantic hash `AEC550...75DB`;
- new split/input commitments validate independently;
- phase is exactly `preflight_complete`;
- non-lockbox, lockbox, publication, and canonical outputs remain absent/unset;
- no forbidden output keys or private/runtime/provider/call capabilities appear.

Recompute the retired aggregate fingerprint exactly as Step 1. All four values must match. Any mismatch stops the transaction.

### Step 5: Run exactly one replacement non-lockbox attempt

After the independent preflight verdict passes, invoke once:

```powershell
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe scripts/run_emotion_state_002_phase_b.py non-lockbox
```

This is the only authorized Cut 4B replacement attempt. On failure, preserve the exact sanitized error, classify the blocker, re-fingerprint the retired lineage, and stop. Do not retry or loosen another rule.

The one-attempt restriction is a controller authorization invariant, not a new runner-state schema. The controller must issue exactly one `non-lockbox` child-process tool call and treat that recorded tool call as the attempt issuance. The current runner may technically remain callable after a pre-linearization build failure, but a second call is unauthorized. Do not add an attempt marker, state transition, allowlist entry, or recovery protocol: doing so would exceed the approved endpoint/schema/root correction and change transaction semantics. A restart or interruption does not renew authority.

### Step 6: Perform aggregate-only independent Task 10 readback

On success, a fresh independent reviewer may read exactly these source-silent authorities:

- the tracked configuration, environment lock, v2 feature schema, split schema, and tracked Phase A/dataset evidence already bound by the validator;
- the new Cut 4B `state.json`, input ledger, validated split manifest, and three preflight partition-authority caches;
- the new Cut 4B three acoustic feature caches, `ami-v2-evidence.json`, and non-lockbox packet.

It may not read raw CREMA-D/AMI material, the retired lineage, final-lockbox/canonical/publication surfaces, or any unlisted cache/state file. From the allowed authorities it must independently validate schema/order/types/digests and source-silent replay commitments, and report only aggregate facts:

- phase and packet schema/version;
- partition case counts and actor counts;
- abstention/tie counts;
- feature count and finite-value aggregate checks;
- model class/configuration identity;
- aggregate non-lockbox metrics and frozen decision thresholds;
- AMI aggregate mechanics;
- cache/packet commitment validity;
- all five lockbox access counters are exact built-in integer zero;
- final decision eligibility is false;
- final lockbox, canonical, publication, provider, private-data, call, runtime, and source-adaptation surfaces remain absent/unset.

It must not print or persist identifiers, paths, rows, labels, audio, transcripts, probabilities, feature vectors, per-case predictions, or model state.

Finally recompute the retired aggregate fingerprint. All four values must still match Step 1.

## Task 4: Record the accepted non-lockbox checkpoint and stop

Run this task only if Task 3 succeeded and independent Task 10 review returned both provider-independent validity and privacy/scope passes with no open Critical or Important finding.

**Files:**

- Modify: `docs/thesis/METHODOLOGY_LOG.md`
- Modify: `docs/thesis/ROADMAP.md`
- Modify: `research/experiments/EMOTION-STATE-002-phase-b-public-data-feasibility.md`

### Step 1: Update only aggregate claims

Record exact aggregate Task 10 evidence, independent verdict, new-root identity, v2 hashes, retired-lineage immutability proof, zero-lockbox counters, and test/validator results. State explicitly that this is only an offline public-dataset acted-perception feasibility checkpoint.

Do not claim internal emotion recognition, real-customer performance, production readiness, PSTN/ASR/latency validation, manipulation safety, runtime authority, or final-lockbox performance.

Set the live next-step status to: stop before Phase C. Phase C requires a new reviewed scope and explicit authorization.

### Step 2: Validate and independently review the documentation diff

```powershell
python scripts/check_thesis_update_gate.py
python scripts/check_thesis_reference_registry.py
python scripts/validate_project_drift_guard.py
python scripts/validate_context_reading_policy.py
python scripts/validate_check_setup.py
git diff --check
git diff -- docs/thesis/METHODOLOGY_LOG.md docs/thesis/ROADMAP.md research/experiments/EMOTION-STATE-002-phase-b-public-data-feasibility.md
```

Require a fresh independent documentation review with zero open Critical or Important findings.

### Step 3: Commit the aggregate-only checkpoint documentation

```powershell
git add docs/thesis/METHODOLOGY_LOG.md docs/thesis/ROADMAP.md research/experiments/EMOTION-STATE-002-phase-b-public-data-feasibility.md
git diff --cached --check
git commit -m "Record Phase B Cut 4B non-lockbox checkpoint"
```

Rerun the full correction ledger, verify a clean tracked worktree, and stop. Do not push, open final lockbox, stage canonical output, or begin Phase C.
