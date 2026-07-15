# EMOTION-STATE-001 Open-Dataset Gate Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the bounded offline Phase A provenance, public-dataset manifest, dependency-split, and privacy-minimized cohort-release gate while keeping source adaptation, private data, providers, calls, dataset evaluation, and runtime influence disabled.

**Architecture:** Extend the existing deterministic Phase A checkpoint with three detached standard-library contract modules: public-dataset integrity, split-manifest v2, and cohort release. Build all logic and guards against synthetic temporary fixtures first. Stop at a hard authorization gate before downloading CREMA-D or AMI; after separate approval, inventory only the selected canonical artifacts, commit all input evidence, and publish the existing two-file checkpoint pair through the current crash-safe protocol.

**Tech Stack:** Python 3.11 standard library, `unittest`, JSON contracts and inventories, Markdown research/thesis records, Git and Git LFS for the separately authorized CREMA-D acquisition step, existing repository validators.

## Global Constraints

- Approved design: `docs/superpowers/specs/2026-07-15-emotion-state-phase-a-open-dataset-gate-completion-design.md`.
- Approved specification commit and fixed implementation baseline: `fb0513545fc0167bcf89dbc81283b7b2a2820b67`.
- Work only in the existing isolated worktree on `codex/emotion-state-phase-a-open-dataset-gate-design`.
- Do not push, merge, rewrite history, or modify another worktree.
- No private or customer data.
- No read from `data/private/` or `data/private-restricted/`.
- No ElevenLabs or other provider read or write.
- No outbound call or customer call.
- No provider-hosted simulation, call simulation, or synthetic sales-conversation simulation.
- No dataset download before the explicit hard gate in Task 8 receives separate user authorization.
- No source copying, translation, adaptation, or independent reimplementation from Creative Analysis Engine.
- No runtime wiring, prompt change, BRAIN-002 mutation, policy influence, or runtime activation.
- No dashboard test, Analysis criterion, hosted prompt or knowledge base, voice, LLM, phone setting, Procedure, or provider configuration change.
- Use Python standard-library functionality only. Do not add dependency metadata or a package.
- Selected dataset order is exactly `crema-d-v1.0-audio-wav`, then `ami-manual-annotations-v1.6.2`.
- CREMA-D is controlled acoustic-sensitivity evidence only. AMI is conversational-mechanics evidence only.
- Neither dataset maps to hesitation, frustration, confusion, interest, or disengagement.
- Public dedup key is exactly `(dataset_manifest_id, source_speaker_id)`.
- Candidate discovery is at least 5 unique speakers and 10 independently labelled turns with at most 2 qualifying turns per speaker.
- Aggregate release is at least 10 proven unique speakers with at most one eligible call or source session per speaker and at least 10 unique speakers in every emitted output cell.
- Confirmatory promotion is at least 30 unique speakers overall and at least 30 consensus-positive plus 30 consensus-negative turns for every promoted label; a later power analysis may raise these floors.
- `phase_a_complete=false` until both exact local dataset inventories are verified and every contract, privacy, dependency, provenance, publication, and repository gate passes.
- Even when `phase_a_complete=true`, `dataset_evaluation_started=false`, all runtime/provider/private/readiness flags remain false, and the scope is exactly `source_provenance_dataset_manifests_offline_contracts_and_cohort_release_gate_only`.
- The final canonical directory remains exactly `research/experiments/generated/EMOTION-STATE-001-phase-a-contracts/result.json` and `report.md`. No third canonical file is allowed.
- Every task uses a red/green test cycle and a focused commit. Preserve exact failures and stop on any timeout or failed gate.
- A missing/mismatched artifact, source label, dependency, hash, inventory, command, or guard leaves `phase_a_complete=false` and preserves the last valid canonical pair.
- A remote artifact change cannot overwrite a verified manifest version. It requires a new manifest version, new inventories, and review.
- Rollback affects offline manifests and generated checkpoint evidence only; there is no provider or runtime rollback because this plan changes neither.

## Authorization Split

Tasks 1-7 design and implement only offline contracts, synthetic fixtures, guards, and the material-pending checkpoint. They do not download or inspect dataset bytes. Task 8 is a mandatory stop. Tasks 9-11 may execute only after a new, explicit user authorization for public-dataset acquisition. Approval of this plan does not satisfy Task 8.

## File Map

**Create before the download gate:**

- `scripts/emotion_state_public_dataset_contracts.py`: frozen dataset profiles plus manifest, hash-inventory, WAV, AMI-path, label-boundary, and quality validation.
- `scripts/emotion_state_split_manifest_v2_contracts.py`: v2 dependency requirement/status, quarantine, covering-key, and cross-partition leakage validation; v1 remains readable.
- `scripts/emotion_state_cohort_release_contracts.py`: discovery, contribution cap, dedup, suppression, fixed-window, per-cell, replacement, and confirmatory-floor contracts.
- `scripts/emotion_state_phase_a_verification_evidence.py`: committed and uncommitted input inventories, dependency closure, command ledger, guard-policy digest, and deterministic verification input digest.
- `scripts/emotion_state_phase_a_guard_site/sitecustomize.py`: opt-in Python child-process network and private-path denial used only by the guarded Phase A runner.
- `scripts/build_emotion_state_public_dataset_manifests.py`: offline-only CLI that reads already acquired public paths and writes reviewed manifests/inventories; it contains no downloader.
- `scripts/test_emotion_state_001_open_dataset_gate.py`: focused standard-library tests and synthetic fixtures.
- `research/sources/emotion_state/split_manifest_v2.schema.json`: unpopulated seven-dimension split schema with requirement/status metadata and quarantine.
- `research/sources/emotion_state/cohort_release_evidence_v1.schema.json`: exact detached release-evidence field and suppression contract; it wraps but does not modify `OperationalAggregateV1`.
- `research/sources/emotion_state/phase_a_verification_guard_policy.json`: byte-bound provider-environment, private-path, network, import, subprocess, command, and publication policy.
- `research/experiments/cases/emotion-state-001-cohort-release-fixtures.json`: deterministic synthetic-only cohort scenarios; no customer or private records.

**Create only after Task 8 authorization and Task 9 local verification:**

- `research/sources/emotion_state/datasets/crema-d-v1.0-audio-wav.manifest.json`
- `research/sources/emotion_state/datasets/crema-d-v1.0-audio-wav.hashes.json`
- `research/sources/emotion_state/datasets/crema-d-v1.0-audio-wav.quality.json`
- `research/sources/emotion_state/datasets/ami-manual-annotations-v1.6.2.manifest.json`
- `research/sources/emotion_state/datasets/ami-manual-annotations-v1.6.2.hashes.json`
- `research/sources/emotion_state/datasets/ami-manual-annotations-v1.6.2.quality.json`

**Modify:**

- `research/sources/creative_analysis_engine/source_manifest.json`
- `research/sources/creative_analysis_engine/source_notes.md`
- `research/sources/emotion_state/dataset_manifest_contract.json`
- `research/experiments/cases/emotion-state-001-phase-a-contracts.json`
- `scripts/emotion_state_phase_a_contracts.py`
- `scripts/run_emotion_state_001_phase_a_contracts.py`
- `scripts/validate_emotion_state_001_phase_a_contracts.py`
- `scripts/test_emotion_state_001_closeout_hardening.py`
- `docs/product/EMOTION_STATE_001_PHASE_A_CONTRACTS.md`
- `research/experiments/EMOTION-STATE-001-phase-a.md`
- `docs/third-party-inspirations.md`
- `docs/product/COMMANDS.md`
- `docs/thesis/THESIS_REFERENCE_REGISTRY.md`
- `docs/thesis/DECISION_LOG.md`
- `docs/thesis/METHODOLOGY_LOG.md`
- `docs/thesis/ROADMAP.md`
- `scripts/check_setup.py`
- `scripts/validate_check_setup.py`
- `scripts/check_project_drift.py`
- `scripts/validate_project_drift_guard.py`
- final canonical `result.json` and `report.md` only after all inputs are committed.

**Must remain unchanged:**

- `runtime/entrypoints/`, `runtime/core/`, `runtime/action_selector/`, and `runtime/providers/`
- `runtime/contracts/brain_runtime_state_schema.py`
- `research/experiments/cases/brain-002-runtime-state-schema.json`
- provider, ElevenLabs, prompt, KB, Analysis, voice, LLM, phone, Procedure, call, simulation, dashboard, and private-data files
- every file in `D:\Codex\z\creative-analysis-engine-dev.zip`
- `runtime/contracts/emotion_state_contracts.py`, `runtime/contracts/emotion_pattern_contracts.py`, `runtime/contracts/emotion_state_brain_extension.py`, and `runtime/runtime_manifest.json`

---

### Task 0: Re-establish The Implementation Baseline

**Files:**

- Read only: approved spec, current branch, frozen baselines, existing canonical pair.

**Interfaces:**

- Consumes: commit `fb0513545fc0167bcf89dbc81283b7b2a2820b67` and the existing six frozen fingerprints.
- Produces: a clean, evidenced starting state; no files change.

- [ ] **Step 1: Verify branch, HEAD ancestry, worktree cleanliness, and fixed specification**

```powershell
git branch --show-current
git rev-parse HEAD
git merge-base --is-ancestor fb0513545fc0167bcf89dbc81283b7b2a2820b67 HEAD
git status --short --branch
git show --stat --oneline fb0513545fc0167bcf89dbc81283b7b2a2820b67
```

Expected: branch is `codex/emotion-state-phase-a-open-dataset-gate-design`, the ancestor check exits `0`, and status contains no changed path.

- [ ] **Step 2: Run the existing checkpoint before editing**

```powershell
python scripts\validate_exp_002_frozen_response_baseline.py
python scripts\validate_emotion_state_001_phase_a_contracts.py
python scripts\test_emotion_state_001_closeout_hardening.py
python scripts\validate_brain_002_runtime_state_schema.py
python scripts\validate_private_data_boundary.py
```

Expected: every command exits `0`. If any command times out or fails, preserve its exact output and stop before Task 1.

---

### Task 1: Pin Creative Analysis Engine Provenance Without Opening Adaptation

**Files:**

- Create: `scripts/test_emotion_state_001_open_dataset_gate.py`
- Modify: `research/sources/creative_analysis_engine/source_manifest.json`
- Modify: `research/sources/creative_analysis_engine/source_notes.md`
- Modify: `docs/third-party-inspirations.md`
- Modify: `scripts/emotion_state_phase_a_contracts.py`
- Modify: `scripts/validate_emotion_state_001_phase_a_contracts.py`

**Interfaces:**

- Consumes: already verified read-only repository evidence from the approved spec.
- Produces: `validate_source_manifest(manifest)` accepting the exact `dev` pin and seven-file byte-equivalence scope while keeping every reuse gate false.

- [ ] **Step 1: Write the failing provenance test**

Add this test class to the new test module:

```python
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SourceProvenanceTests(unittest.TestCase):
    def test_private_source_pin_is_exact_and_non_adapting(self) -> None:
        path = ROOT / "research/sources/creative_analysis_engine/source_manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(
            manifest["source_repository_url"],
            "https://github.com/WisdomBreathes/creative-analysis-engine",
        )
        self.assertEqual(manifest["source_repository_url_status"], "verified_read_only")
        self.assertEqual(manifest["source_branch"], "dev")
        self.assertEqual(
            manifest["source_revision"],
            "7cb99ea2da3016cd82d0b5f805c015a808ce4e0d",
        )
        self.assertEqual(manifest["source_revision_status"], "verified_read_only")
        self.assertEqual(manifest["observed_license_status"], "absent_in_reviewed_root")
        self.assertEqual(len(manifest["reviewed_files"]), 7)
        self.assertEqual(manifest["copied_material"], [])
        self.assertEqual(manifest["translated_material"], [])
        self.assertEqual(manifest["adapted_material"], [])
        self.assertEqual(manifest["independently_reimplemented_material"], [])
        self.assertFalse(manifest["adaptation_allowed"])
        self.assertFalse(manifest["phase_b_approval"]["approved"])
        self.assertFalse(manifest["runtime_dependency_added"])
```

- [ ] **Step 2: Run the test and verify the old unverified fields fail**

```powershell
python -m unittest scripts.test_emotion_state_001_open_dataset_gate.SourceProvenanceTests -v
```

Expected: failure because the existing manifest still records the URL and revision as unverified.

- [ ] **Step 3: Update the manifest with the exact seven reviewed paths and Git blob SHA-1 values**

Use this exact `reviewed_files` value and preserve the archive SHA-256 already present:

```json
[
  {"path":"README.md","git_blob_sha1":"f8a1afe3842b361432d8dcc061c5c5b6969cf363","equivalence_status":"byte_identical_to_dev_blob","reuse_status":"reference_only"},
  {"path":"docs/features/FEATURE_speech_call_readiness_analytics.md","git_blob_sha1":"b5e63a3dd9ba72f5eefc46688129aa98bf20a509","equivalence_status":"byte_identical_to_dev_blob","reuse_status":"reference_only"},
  {"path":"docs/features/FEATURE_speech_prosody.md","git_blob_sha1":"5d5cbd7e25dc7bce5fcf2c7fcb97448524c79f22","equivalence_status":"byte_identical_to_dev_blob","reuse_status":"reference_only"},
  {"path":"docs/features/FEATURE_speech_turn_dynamics.md","git_blob_sha1":"03f737ce52262fcac733016ec57f344d783a69b4","equivalence_status":"byte_identical_to_dev_blob","reuse_status":"reference_only"},
  {"path":"src/aggregation/speech_call_readiness.py","git_blob_sha1":"8387ae5d365d22c816e407e315701a066e745599","equivalence_status":"byte_identical_to_dev_blob","reuse_status":"excluded_from_emotion_labels"},
  {"path":"src/features/temporal/speech_prosody.py","git_blob_sha1":"dbadd19160affcd3aec864a9f4b77d3ed5e5a4d6","equivalence_status":"byte_identical_to_dev_blob","reuse_status":"reference_only"},
  {"path":"src/features/temporal/speech_turn_dynamics.py","git_blob_sha1":"4a46634ca9531e5181f72a554545083defcff59d","equivalence_status":"byte_identical_to_dev_blob","reuse_status":"reference_only"}
]
```

Set `source_repository_url_status` and `source_revision_status` to `verified_read_only`, `observed_license` to `null`, `observed_license_status` to `absent_in_reviewed_root`, and `adaptation_blockers` to:

```json
[
  "current_instruction_prohibits_source_adaptation",
  "observed_repository_license_absent",
  "phase_b_reuse_scope_not_defined",
  "phase_b_attribution_wording_pending",
  "phase_b_approval_not_granted"
]
```

Do not read the private repository or ZIP again during implementation. Update source notes and third-party inspiration wording to say the seven files were verified byte-identical, the full ZIP was not proven equivalent, and no code was copied, translated, adapted, or independently reimplemented.

- [ ] **Step 4: Make builder and validator accept verified provenance but derive adaptation as false**

In `validate_source_manifest`, require these values and never derive `adaptation_allowed=true` from URL/revision verification:

```python
expected_values = {
    "archive_sha256": EXPECTED_ARCHIVE_SHA256,
    "source_repository_url": "https://github.com/WisdomBreathes/creative-analysis-engine",
    "source_repository_url_status": "verified_read_only",
    "source_branch": "dev",
    "source_revision": "7cb99ea2da3016cd82d0b5f805c015a808ce4e0d",
    "source_revision_status": "verified_read_only",
    "observed_license": None,
    "observed_license_status": "absent_in_reviewed_root",
}
if manifest["adaptation_allowed"] is not False:
    raise ValueError("source adaptation must remain blocked by the current instruction")
if manifest["phase_b_approval"]["approved"] is not False:
    raise ValueError("Phase B source reuse approval must remain false")
```

- [ ] **Step 5: Run focused validation and commit**

```powershell
python -m unittest scripts.test_emotion_state_001_open_dataset_gate.SourceProvenanceTests -v
python scripts\validate_emotion_state_001_phase_a_contracts.py --section source
git diff --check
git add research\sources\creative_analysis_engine\source_manifest.json research\sources\creative_analysis_engine\source_notes.md docs\third-party-inspirations.md scripts\emotion_state_phase_a_contracts.py scripts\validate_emotion_state_001_phase_a_contracts.py scripts\test_emotion_state_001_open_dataset_gate.py
git commit -m "Pin EMOTION-STATE source provenance"
```

Expected: tests and source validator pass; one focused commit is created.

---

### Task 2: Freeze The Two Public-Dataset Profiles And Manifest Contract

**Files:**

- Create: `scripts/emotion_state_public_dataset_contracts.py`
- Modify: `research/sources/emotion_state/dataset_manifest_contract.json`
- Modify: `scripts/test_emotion_state_001_open_dataset_gate.py`
- Modify: `scripts/validate_emotion_state_001_phase_a_contracts.py`

**Interfaces:**

- Consumes: exact dataset decisions in the approved spec.
- Produces: `dataset_profile(dataset_id)`, `validate_dataset_manifest(payload)`, `validate_hash_inventory(payload, dataset_root)`, and `public_dataset_contract_self_check()`.

- [ ] **Step 1: Add failing tests for order, identity, labels, and forbidden mappings**

```python
class PublicDatasetContractTests(unittest.TestCase):
    def test_selected_dataset_order_and_pins_are_exact(self) -> None:
        from scripts.emotion_state_public_dataset_contracts import (
            AMI_DATASET_ID,
            CREMA_DATASET_ID,
            SELECTED_PUBLIC_DATASETS,
            dataset_profile,
        )
        self.assertEqual(SELECTED_PUBLIC_DATASETS, (CREMA_DATASET_ID, AMI_DATASET_ID))
        crema = dataset_profile(CREMA_DATASET_ID)
        self.assertEqual(crema["release_or_version"], "v1.0")
        self.assertEqual(crema["source_revision"], "f3b8611a309886568dfa957141775b2e05add04a")
        self.assertEqual(crema["raw_source_label_map"], {
            "A": "anger", "D": "disgust", "F": "fear",
            "H": "happy", "N": "neutral", "S": "sad",
        })
        self.assertEqual(crema["project_label_mapping"], {})
        ami = dataset_profile(AMI_DATASET_ID)
        self.assertEqual(ami["release_or_version"], "AMI manual annotations v1.6.2")
        self.assertEqual(ami["project_label_mapping"], {})
        self.assertEqual(ami["selected_artifacts"][0], "official-manual-annotation-archive")

    def test_public_profiles_never_claim_operational_labels(self) -> None:
        from scripts.emotion_state_public_dataset_contracts import (
            OPERATIONAL_SIGNALS,
            SELECTED_PUBLIC_DATASETS,
            dataset_profile,
        )
        for dataset_id in SELECTED_PUBLIC_DATASETS:
            serialized = json.dumps(dataset_profile(dataset_id), sort_keys=True)
            for signal in OPERATIONAL_SIGNALS:
                self.assertNotIn(f'"{signal}":', serialized)
```

- [ ] **Step 2: Run the tests and verify the module is missing**

```powershell
python -m unittest scripts.test_emotion_state_001_open_dataset_gate.PublicDatasetContractTests -v
```

Expected: import failure for `scripts.emotion_state_public_dataset_contracts`.

- [ ] **Step 3: Implement frozen profiles and strict manifest validation**

Create these constants and exact public interfaces:

```python
CREMA_DATASET_ID = "crema-d-v1.0-audio-wav"
AMI_DATASET_ID = "ami-manual-annotations-v1.6.2"
SELECTED_PUBLIC_DATASETS = (CREMA_DATASET_ID, AMI_DATASET_ID)
OPERATIONAL_SIGNALS = frozenset({
    "hesitation", "frustration", "confusion", "interest", "disengagement",
})
REQUIRED_V1_FIELDS = frozenset({
    "dataset_id", "canonical_source_url", "release_or_version", "accessed_on",
    "terms_or_license", "access_restrictions", "local_file_hashes", "source_label",
    "source_labels", "project_label_mapping", "excluded_labels", "language", "domain",
    "domain_limitations", "permitted_research_lanes", "redistribution_status",
})
REQUIRED_V2_FIELDS = REQUIRED_V1_FIELDS | frozenset({
    "manifest_version", "selected_artifacts", "source_revision", "release_published_at",
    "dependency_keys", "quality_rules", "known_issues", "exclusion_inventory",
    "hash_inventory", "completion_status", "runtime_influence_allowed",
})
```

`dataset_profile` must return a deep copy of one frozen dictionary. `validate_dataset_manifest` must require the exact field set, `source_label == "public-only"`, `project_label_mapping == {}`, `runtime_influence_allowed is False`, project-relative inventory paths, and `completion_status` in `{"material_verification_pending", "verified"}`.

For a verified manifest, the three evidence-reference fields have these exact shapes:

```json
"local_file_hashes": {
  "algorithm": "SHA-256",
  "inventory_path": "research/sources/emotion_state/datasets/<dataset-id>.hashes.json",
  "inventory_sha256": "<64 uppercase hexadecimal characters>",
  "selected_file_count": 1,
  "selected_byte_count": 1
},
"hash_inventory": {
  "schema_id": "emotion-state-dataset-hash-inventory-v1",
  "schema_version": 1,
  "algorithm": "SHA-256",
  "inventory_path": "research/sources/emotion_state/datasets/<dataset-id>.hashes.json",
  "inventory_sha256": "<64 uppercase hexadecimal characters>",
  "selected_file_count": 1,
  "selected_byte_count": 1,
  "path_normalization": "project-relative-posix-nfc",
  "ordering": "ordinal-by-normalized-path"
},
"exclusion_inventory": {
  "schema_id": "emotion-state-dataset-quality-inventory-reference-v1",
  "schema_version": 1,
  "quality_inventory_path": "research/sources/emotion_state/datasets/<dataset-id>.quality.json",
  "quality_inventory_sha256": "<64 uppercase hexadecimal characters>",
  "included_file_count": 1,
  "excluded_file_count": 0
}
```

`local_file_hashes` is the v1-compatible projection of `hash_inventory`; the validator requires equality for their five shared keys. `dataset_quality_inventory_digests` and every quality-file integrity check use `exclusion_inventory.quality_inventory_sha256`. Counts are nonnegative integers, while verified manifests require positive selected-file and selected-byte counts and at least one included quality item. A pending manifest keeps the exact nested keys but sets digests and counts to `null`; it must not claim hashes or counts.

Use this label boundary for CREMA-D:

```python
CREMA_RAW_SOURCE_LABEL_MAP = {
    "A": "anger",
    "D": "disgust",
    "F": "fear",
    "H": "happy",
    "N": "neutral",
    "S": "sad",
}
CREMA_PROHIBITED_PROJECT_MAPPINGS = {
    "anger": "frustration",
    "happy": "interest",
    "sad": "disengagement",
    "fear": "hesitation",
    "neutral": "no_customer_concern",
}
```

The validator rejects every prohibited mapping and any nonempty AMI emotion/operational mapping.

Freeze the complete source identities and selection rules, not only their IDs:

```python
CREMA_PROFILE_IDENTITY = {
    "canonical_source_url": "https://github.com/CheyneyComputerScience/CREMA-D",
    "release_or_version": "v1.0",
    "source_revision": "f3b8611a309886568dfa957141775b2e05add04a",
    "release_published_at": "2025-03-18T09:54:26Z",
    "terms_or_license": ["ODbL-1.0", "DbCL-1.0"],
    "language": "English",
    "domain": "acted isolated utterances with controlled sentences",
    "selected_artifacts": [
        "AudioWAV/",
        "processedResults/summaryTable.csv",
        "finishedResponses.csv#audio-only-rows",
        "SentenceFilenames.csv",
        "README.md",
        "LICENSE.txt",
        "git-lfs-pointer-metadata",
    ],
}
AMI_PROFILE_IDENTITY = {
    "canonical_source_url": "https://groups.inf.ed.ac.uk/ami/download/",
    "release_or_version": "AMI manual annotations v1.6.2",
    "release_published_at": "2017-04-10",
    "terms_or_license": ["CC-BY-4.0"],
    "language": "English",
    "domain": "scenario-based and naturally occurring multi-party meetings",
    "selected_artifacts": [
        "official-manual-annotation-archive",
        "nxt-metadata",
        "speaker-aligned-orthographic-transcripts",
        "timing-links",
        "dialogue-acts",
        "official-partition-metadata",
        "official-release-license-page-provenance",
    ],
}
```

Record that CREMA-D requires its official access process and Git LFS media objects. Record that the AMI local archive SHA-256 is a local retrieval pin, not a publisher-signed checksum.

- [ ] **Step 4: Upgrade the tracked manifest contract without dropping v1 fields**

Set `schema_id` to `emotion-state-dataset-manifest-v2`, `schema_version` to `2`, keep `required_v1_fields` equal to the current sixteen fields, set `required_fields` to their union with the eleven v2 fields, and set:

```json
"selected_public_datasets": [
  "crema-d-v1.0-audio-wav",
  "ami-manual-annotations-v1.6.2"
],
"dataset_download_authorized": false,
"dataset_evaluation_started": false,
"runtime_influence_allowed": false
```

Do not create per-dataset manifest or hash files yet.

- [ ] **Step 5: Run focused validation and commit**

```powershell
python -m unittest scripts.test_emotion_state_001_open_dataset_gate.PublicDatasetContractTests -v
python scripts\validate_emotion_state_001_phase_a_contracts.py --section source
git diff --check
git add scripts\emotion_state_public_dataset_contracts.py research\sources\emotion_state\dataset_manifest_contract.json scripts\test_emotion_state_001_open_dataset_gate.py scripts\validate_emotion_state_001_phase_a_contracts.py
git commit -m "Define EMOTION-STATE public dataset contracts"
```

---

### Task 3: Add Split Manifest V2 Without Breaking V1

**Files:**

- Create: `research/sources/emotion_state/split_manifest_v2.schema.json`
- Create: `scripts/emotion_state_split_manifest_v2_contracts.py`
- Modify: `scripts/test_emotion_state_001_open_dataset_gate.py`
- Modify: `scripts/validate_emotion_state_001_phase_a_contracts.py`

**Interfaces:**

- Consumes: case dependency records shaped as `{case_id, dataset_manifest_id, dependency_value_by_key, dependency_status_by_key}`.
- Produces: `validate_split_manifest_v2(payload, case_records)` and `split_manifest_v2_self_check()`.

- [ ] **Step 1: Write failing tests for seven dimensions, quarantine, covering keys, and leakage**

```python
class SplitManifestV2Tests(unittest.TestCase):
    def test_v2_dependency_rules_fail_closed(self) -> None:
        from scripts.emotion_state_split_manifest_v2_contracts import (
            DEPENDENCY_KEYS_V2,
            fixture_split_manifest_v2,
            fixture_split_records_v2,
            validate_split_manifest_v2,
        )
        records = fixture_split_records_v2()
        manifest = fixture_split_manifest_v2(records)
        self.assertEqual(DEPENDENCY_KEYS_V2, (
            "speaker", "call_session", "dialogue_dyad", "source_corpus",
            "scripted_scenario", "meeting_series", "recording_site",
        ))
        validate_split_manifest_v2(manifest, records)
        leaked = json.loads(json.dumps(manifest))
        leaked["calibration"]["dependency_groups"]["speaker"] = ["speaker-training"]
        with self.assertRaisesRegex(ValueError, "speaker leakage"):
            validate_split_manifest_v2(leaked, records)

    def test_required_unknown_is_quarantined_and_covering_key_is_proven(self) -> None:
        from scripts.emotion_state_split_manifest_v2_contracts import (
            fixture_split_manifest_v2,
            fixture_split_records_v2,
            validate_split_manifest_v2,
        )
        records = fixture_split_records_v2(include_required_unknown=True)
        manifest = fixture_split_manifest_v2(records)
        validated = validate_split_manifest_v2(manifest, records)
        self.assertEqual(validated["dependency_unknown_quarantine"]["case_ids"], ["case-unknown"])
        self.assertFalse(validated["dependency_unknown_quarantine"]["claims_allowed"])
        broken = json.loads(json.dumps(manifest))
        broken["dependency_covering_key_by_key"]["call_session"] = "missing-key"
        with self.assertRaisesRegex(ValueError, "covering key"):
            validate_split_manifest_v2(broken, records)
```

- [ ] **Step 2: Verify the tests fail before the module exists**

```powershell
python -m unittest scripts.test_emotion_state_001_open_dataset_gate.SplitManifestV2Tests -v
```

Expected: import failure.

- [ ] **Step 3: Implement exact v2 enums and fail-closed validation**

Create these constants:

```python
DEPENDENCY_KEYS_V2 = (
    "speaker", "call_session", "dialogue_dyad", "source_corpus",
    "scripted_scenario", "meeting_series", "recording_site",
)
DEPENDENCY_REQUIREMENTS = frozenset({
    "required", "covered_by_higher_dependency", "advisory", "not_applicable",
})
DEPENDENCY_STATUSES = frozenset({"available", "not_available", "not_applicable"})
PARTITIONS = ("training_discovery", "calibration", "balanced_diagnostic", "final_lockbox")
```

`validate_split_manifest_v2` must enforce all of these rules in this order:

1. exact top-level and partition fields;
2. exact ordered dependency key list;
3. `runtime_influence_allowed is False`;
4. every requirement/status map has all seven keys;
5. `not_applicable` has a nonempty applicability reason and no dependency value;
6. `required/not_available` appears only in `dependency_unknown_quarantine`, whose `claims_allowed` is false;
7. `covered_by_higher_dependency` names an available covering key and verifies functional many-to-one nesting in the supplied records: each covered dependency value maps to exactly one covering dependency value, one covering value may contain multiple covered values, and covering groups remain partition-disjoint;
8. `advisory/not_available` forces `confirmatory_claims_allowed=false`;
9. quarantine cases are absent from all four partitions and all metric/claim denominators;
10. case IDs and every available dependency group are disjoint across partitions;
11. partition dependency groups equal the groups derived from immutable case records.

- [ ] **Step 4: Create the unpopulated v2 schema and preserve v1 readability**

The v2 JSON must declare all seven dimensions, empty partitions, exact requirement/status/covering/applicability maps, an empty quarantine with `claims_allowed=false`, `confirmatory_claims_allowed=false`, and `runtime_influence_allowed=false`. Do not modify `split_manifest_v1.schema.json` or `validate_split_manifest` in `emotion_state_annotation_contracts.py`.

Freeze dataset mappings exactly:

```text
AMI participant -> speaker required
AMI meeting -> call_session required
AMI four-meeting series -> meeting_series required
AMI documented standalone meeting -> meeting_series not_applicable
AMI recording location -> recording_site required
AMI manifest ID -> source_corpus required
AMI scenario identity -> scripted_scenario required for scenario meetings
AMI documented natural meeting -> scripted_scenario not_applicable
AMI multi-party meeting -> dialogue_dyad not_applicable
CREMA ActorID -> speaker required
CREMA manifest ID -> source_corpus required
CREMA sentence code -> scripted_scenario required
CREMA call_session -> covered_by_higher_dependency speaker only after verified nesting
CREMA meeting_series -> not_applicable
CREMA dialogue_dyad -> not_applicable
CREMA recording_site -> advisory/not_available with confirmatory and site-generalization claims blocked
```

If CREMA session-to-speaker nesting cannot be verified, change `call_session` to `advisory/not_available`; never pretend the dimension is absent.

Extend the Phase A validator to read and validate both schemas and call both self-checks.

- [ ] **Step 5: Run tests and commit**

```powershell
python -m unittest scripts.test_emotion_state_001_open_dataset_gate.SplitManifestV2Tests -v
python scripts\validate_emotion_state_001_phase_a_contracts.py --section source
git diff --check
git add research\sources\emotion_state\split_manifest_v2.schema.json scripts\emotion_state_split_manifest_v2_contracts.py scripts\test_emotion_state_001_open_dataset_gate.py scripts\validate_emotion_state_001_phase_a_contracts.py
git commit -m "Add EMOTION-STATE split manifest v2"
```

---

### Task 4: Implement The Privacy-Minimized Cohort-Release Gate

**Files:**

- Create: `scripts/emotion_state_cohort_release_contracts.py`
- Create: `research/sources/emotion_state/cohort_release_evidence_v1.schema.json`
- Create: `research/experiments/cases/emotion-state-001-cohort-release-fixtures.json`
- Modify: `scripts/test_emotion_state_001_open_dataset_gate.py`
- Modify: `scripts/emotion_state_phase_a_contracts.py`
- Modify: `scripts/validate_emotion_state_001_phase_a_contracts.py`

**Interfaces:**

- Consumes: synthetic/public metadata records only.
- Produces: `build_cohort_release(records, request)`, `validate_cohort_release(payload)`, `validate_confirmatory_floor(evidence)`, and `cohort_release_contract_self_check()`.
- Wraps: the existing `runtime.contracts.emotion_state_contracts.validate_operational_aggregate` result without adding a speaker field to `OperationalAggregateV1`.

- [ ] **Step 1: Add the required synthetic release tests**

```python
class CohortReleaseTests(unittest.TestCase):
    def test_four_speakers_suppress_and_ten_speakers_pass(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            fixture_records,
            fixture_request,
        )
        suppressed = build_cohort_release(fixture_records(12, 4), fixture_request())
        self.assertEqual(suppressed["release_status"], "suppressed")
        self.assertIn("minimum_unique_speakers_not_met", suppressed["suppression_reason_codes"])
        released = build_cohort_release(fixture_records(10, 10), fixture_request())
        self.assertEqual(released["release_status"], "released")
        self.assertEqual(released["unique_speaker_count"], 10)
        self.assertNotIn("speaker_keys", released)
        self.assertFalse(released["contains_per_speaker_rows"])

    def test_cross_corpus_identity_cannot_be_pooled(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import (
            build_cohort_release,
            fixture_cross_corpus_records,
            fixture_request,
        )
        result = build_cohort_release(fixture_cross_corpus_records(), fixture_request())
        self.assertEqual(result["release_status"], "suppressed")
        self.assertIn("cross_corpus_identity_not_proven", result["suppression_reason_codes"])

    def test_confirmatory_floor_requires_thirty_by_class_for_every_promoted_label(self) -> None:
        from scripts.emotion_state_cohort_release_contracts import validate_confirmatory_floor
        passing = {
            "overall_unique_speaker_count": 30,
            "promoted_labels": ["frustration", "confusion"],
            "per_promoted_label": {
                "frustration": {
                    "consensus_positive_turn_count": 30,
                    "consensus_negative_turn_count": 30,
                },
                "confusion": {
                    "consensus_positive_turn_count": 30,
                    "consensus_negative_turn_count": 30,
                },
            },
            "power_precision_requirement_passed": True,
        }
        underpowered = json.loads(json.dumps(passing))
        underpowered["per_promoted_label"]["confusion"]["consensus_positive_turn_count"] = 29
        with self.assertRaisesRegex(ValueError, "consensus-positive"):
            validate_confirmatory_floor(underpowered)
        validate_confirmatory_floor(passing)
```

Add table-driven cases for all other required design scenarios: 20 turns from 5 speakers is discovery-only; duplicate actor IDs deduplicate; missing basis suppresses; call/session/turn IDs as speaker basis reject; phone/email/account/voiceprint/embedding basis reject; a syntactically valid non-null cross-corpus identity digest still rejects; contribution is deterministically capped; sub-10 cells omit; overlapping/nested/filtered/complementary windows reject; replacement binds the prior digest and preserves window/allowlist; output contains no speaker token or per-speaker row; all runtime flags remain false.

- [ ] **Step 2: Verify the tests fail before implementation**

```powershell
python -m unittest scripts.test_emotion_state_001_open_dataset_gate.CohortReleaseTests -v
```

Expected: import failure.

- [ ] **Step 3: Implement strict field sets and deterministic contribution selection**

Define:

```python
ALLOWED_SPEAKER_BASES = frozenset({
    "public_dataset_actor_id",
    "public_dataset_participant_id",
    "synthetic_fixture_speaker_id",
})
RESERVED_DISABLED_SPEAKER_BASE = "privacy_reviewed_pseudonymous_cohort_token"
METRIC_ALLOWLIST_V1 = (
    "eligible_call_count",
    "audio_analysis_availability_rate",
    "audio_quality_bucket_counts",
    "abstention_rate",
    "processing_latency_percentiles",
    "evidence_policy_version_counts",
)
MIN_DISCOVERY_SPEAKERS = 5
MIN_DISCOVERY_TURNS = 10
MAX_DISCOVERY_TURNS_PER_SPEAKER = 2
MIN_RELEASE_SPEAKERS = 10
MAX_RELEASE_CONTRIBUTIONS_PER_SPEAKER = 1
MIN_CONFIRMATORY_SPEAKERS = 30
MIN_CONFIRMATORY_POSITIVE_TURNS = 30
MIN_CONFIRMATORY_NEGATIVE_TURNS = 30
```

The reserved pseudonymous basis is rejected until a separate privacy/security review defines derivation, retention, rotation, deletion, access, and threat model. Reject names, phone numbers, email addresses, account/CRM IDs, undocumented identifier hashes, voiceprints, speaker embeddings, other biometric matching, provider/model identity predictions, and probabilistic dedup presented as certainty.

For each record, require a dataset-namespaced tuple. Sort eligible records by `(dataset_manifest_id, source_speaker_id, source_timestamp, canonical_record_digest)`, retain the earliest record per speaker, and suppress when timestamp/digest is missing rather than selecting nondeterministically. Phase A rejects grouping across different dataset IDs unconditionally and requires `cross_corpus_identity_evidence_digest` to be `null`; any non-null value is rejected even when it is syntactically valid SHA-256. A later reviewed contract may enable cross-corpus pooling only by binding an approved identity source, exact revision, permitted scope, evidence schema, and privacy/security review—not by accepting a bare digest.

`validate_confirmatory_floor` requires a nonempty ordered `promoted_labels` list whose unique values exactly equal the keys of `per_promoted_label`, `overall_unique_speaker_count >= 30`, and `power_precision_requirement_passed is True`. It independently requires at least 30 consensus-positive and 30 consensus-negative turns for every promoted label; pooled counts cannot satisfy a deficient label.

`build_cohort_release` must construct a new object containing the complete `CohortReleaseEvidenceV1` field set from the spec plus `aggregate_metrics` and `output_cell_unique_speaker_counts`. It must never copy the input speaker tuple, raw identity, per-speaker row, or disallowed slice into the output.

The exact release-evidence fields are:

```text
release_scope
source_label
aggregation_window
input_record_count
eligible_record_count
unique_speaker_count
unique_speaker_basis
dependency_keys
max_contribution_per_speaker
dedup_evidence_digest
minimum_unique_speakers
metric_allowlist_version
minimum_unique_speakers_per_output_cell
fixed_window_id
window_overlaps_previous_release
previous_release_digest
release_replaces_digest
direct_identifiers_present
voiceprint_used
speaker_tokens_persisted
contains_per_speaker_rows
contains_demographic_slices
contains_state_or_signal_labels
release_status
suppression_reason_codes
runtime_influence_allowed
aggregate_metrics
output_cell_unique_speaker_counts
```

Require all eight boolean boundary fields to be false, `max_contribution_per_speaker=1`, both unique-speaker minima to be `10`, and `release_status` to be exactly `released` or `suppressed`.

Require fixed, closed, non-overlapping windows and one release per window. Reject ad hoc filters, nested windows, demographic/campaign/state/signal slices, complementary queries, and differencing. Omit every scalar, bucket, percentile, or version cell supported by fewer than ten unique speakers; never emit a suppressed cell as zero. A replacement must preserve the exact window and metric allowlist, replace the entire prior release, and bind `release_replaces_digest` to the prior canonical release digest.

Documentation and serialized output must call this a suppression-based, privacy-minimized contribution gate. They must not call it anonymous, differential privacy, or proof against re-identification.

Neither public dataset may create a `PatternCandidateV1` for an operational signal. Add a test that a CREMA or AMI `dataset_manifest_id` passed as `discovery_dataset_version` is rejected by the Phase A public-dataset gate even though the detached legacy pattern contract remains unchanged.

The tracked schema must require the same fields and exact false constants. The tracked fixture file must contain named scenario parameters rather than expanded personal rows: `twelve_calls_four_speakers`, `ten_calls_ten_speakers`, `twenty_turns_five_speakers`, `duplicate_public_actor_ids`, `cross_corpus_same_bare_id`, `missing_speaker_basis`, `call_id_as_speaker`, `forbidden_identity_basis`, `over_contribution`, `sparse_output_cell`, `overlapping_release`, and `valid_replacement`. The test module expands those parameters into synthetic in-memory records.

- [ ] **Step 4: Add the self-check to the Phase A builder and validator**

Add `emotion_state_cohort_release_contracts` to the checkpoint `contract_checks`. The self-check uses only in-memory synthetic fixtures and returns exactly `"pass"`.

- [ ] **Step 5: Run tests and commit**

```powershell
python -m unittest scripts.test_emotion_state_001_open_dataset_gate.CohortReleaseTests -v
python scripts\validate_emotion_state_001_phase_a_contracts.py --section contracts
git diff --check
git add scripts\emotion_state_cohort_release_contracts.py research\sources\emotion_state\cohort_release_evidence_v1.schema.json research\experiments\cases\emotion-state-001-cohort-release-fixtures.json scripts\test_emotion_state_001_open_dataset_gate.py scripts\emotion_state_phase_a_contracts.py scripts\validate_emotion_state_001_phase_a_contracts.py
git commit -m "Add EMOTION-STATE cohort release gate"
```

---

### Task 5: Build The Offline Dataset Integrity And Quality Verifier

**Files:**

- Create: `scripts/build_emotion_state_public_dataset_manifests.py`
- Modify: `scripts/emotion_state_public_dataset_contracts.py`
- Modify: `scripts/test_emotion_state_001_open_dataset_gate.py`

**Interfaces:**

- Consumes: already-present local paths under ignored `data/public/emotion-state/` only.
- Produces: `build_hash_inventory`, `validate_crema_material`, `safe_extract_ami_archive`, `validate_ami_material`, `write_dataset_evidence`, and a CLI with no network capability.

- [ ] **Step 1: Add failing synthetic filesystem tests**

Add `io`, `struct`, `tempfile`, `wave`, and `zipfile` imports, then add:

```python
class DatasetMaterialValidationTests(unittest.TestCase):
    def test_crema_rejects_lfs_pointer_and_accepts_real_pcm_wav(self) -> None:
        from scripts.emotion_state_public_dataset_contracts import validate_wav_file
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pointer = root / "pointer.wav"
            pointer.write_text(
                "version https://" + "git-lfs.github.com/spec/v1\n"
                "oid sha256:" + "A" * 64 + "\nsize 44\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "Git LFS pointer"):
                validate_wav_file(pointer)
            valid = root / "valid.wav"
            with wave.open(str(valid), "wb") as output:
                output.setnchannels(1)
                output.setsampwidth(2)
                output.setframerate(16000)
                output.writeframes(struct.pack("<" + "h" * 160, *([100] * 160)))
            metadata = validate_wav_file(valid)
            self.assertEqual(metadata["frame_count"], 160)
            self.assertEqual(metadata["sample_rate_hz"], 16000)

    def test_ami_extraction_rejects_traversal_symlink_and_case_collision(self) -> None:
        from scripts.emotion_state_public_dataset_contracts import safe_extract_ami_archive
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "bad.zip"
            with zipfile.ZipFile(archive, "w") as output:
                output.writestr("../escape.xml", "blocked")
            with self.assertRaisesRegex(ValueError, "archive path escape"):
                safe_extract_ami_archive(archive, root / "extract")

    def test_hash_inventory_is_path_sorted_and_byte_bound(self) -> None:
        from scripts.emotion_state_public_dataset_contracts import build_hash_inventory
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "b.txt").write_bytes(b"b")
            (root / "a.txt").write_bytes(b"a")
            inventory = build_hash_inventory(
                dataset_id="synthetic-fixture",
                project_root=root,
                selected_paths=[root / "b.txt", root / "a.txt"],
            )
            self.assertEqual([item["path"] for item in inventory["files"]], ["a.txt", "b.txt"])
            self.assertEqual(inventory["selected_file_count"], 2)
            self.assertEqual(inventory["selected_byte_count"], 2)
```

Add tests for empty, zero-duration, unreadable, invalid-metadata, path-escape, missing selected file, extra selected file, LFS OID mismatch, CREMA filename parsing, `VideoDemographics.csv` rejection, intended-label/source-label separation, known `1076_MTI_SAD_XX.wav` handling, AMI audio/video/automatic/social-role/speculative-emotion exclusions, archive-before-extraction hashing, and deterministic repeat output.

- [ ] **Step 2: Run tests and verify the missing functions fail**

```powershell
python -m unittest scripts.test_emotion_state_001_open_dataset_gate.DatasetMaterialValidationTests -v
```

Expected: import or attribute failures.

- [ ] **Step 3: Implement canonical path and inventory primitives**

Use uppercase SHA-256 and project-relative forward-slash paths:

```python
def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def canonical_inventory_bytes(payload: dict[str, Any]) -> bytes:
    return (
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ) + "\n"
    ).encode("utf-8")


def normalized_relative_path(path: Path, project_root: Path) -> str:
    resolved = path.resolve(strict=True)
    root = project_root.resolve(strict=True)
    try:
        relative = resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError("selected dataset path escapes its approved root") from exc
    value = relative.as_posix()
    if not value or value.startswith("../"):
        raise ValueError("selected dataset path is not canonical")
    return value
```

`build_hash_inventory` must reject duplicate normalized paths and case-fold collisions, sort by ordinal normalized path, include `{path, size_bytes, sha256}` for every file, and return `inventory_version`, `dataset_id`, `algorithm`, path-normalization rule, ordering rule, counts, bytes, and `files`. For CREMA-D entries, add `git_lfs_oid_sha256` when a pinned pointer exposes it and require equality with the computed digest. The inventory never contains its own digest; the separate manifest stores the SHA-256 of the final inventory bytes.

- [ ] **Step 4: Implement CREMA-D selection and WAV checks**

Freeze the selected fixed paths:

```python
CREMA_SELECTED_FIXED_PATHS = (
    "processedResults/summaryTable.csv",
    "finishedResponses.csv",
    "SentenceFilenames.csv",
    "README.md",
    "LICENSE.txt",
)
CREMA_AUDIO_PREFIX = "AudioWAV/"
CREMA_KNOWN_NO_AUDIO_FILE = "AudioWAV/1076_MTI_SAD_XX.wav"
CREMA_EXCLUDED_PATHS = frozenset({"VideoDemographics.csv"})
```

`validate_wav_file` must reject the Git LFS pointer signature, files smaller than a valid RIFF/WAVE header, unsupported encodings, nonpositive channel/sample-width/sample-rate/frame counts, unreadable frames, and zero-duration content. Standard-library `wave` accepts PCM; unsupported floating-point WAV is rejected rather than treated as verified. Parse `ActorID`, sentence code, intended emotion code, and intensity from the filename, but retain the intended code as prompt metadata only. Read audio-only rows from `finishedResponses.csv`; preserve raw `A/D/F/H/N/S`, normalized source label, source column, vote distribution, agreement, and ambiguity. Never fill a missing perceived label from the filename.

Treat tied audio-only majority labels as ambiguous unless a preregistered vote-distribution rule resolves them without observing test outcomes. Use WAV, not MP3, when a valid corresponding WAV exists. Inspect every WAV counterpart named by the official mismatch list; filename agreement cannot waive an objective content/duration failure.

The quality inventory must record every inclusion/exclusion and reason, including the official known issue. It must not guess the advertised 7,442 count.

Record the cross-encoding limitation that raters heard audio-presentation encodings while feature verification uses corresponding WAV files. Filename agreement cannot override an official mismatch or objective duration/content failure.

- [ ] **Step 5: Implement safe AMI archive extraction and annotation-only selection**

`safe_extract_ami_archive` must hash the archive before opening it, reject absolute paths, `..`, drive-qualified paths, symlink entries, duplicate and case-colliding destinations, and any destination outside the exact extraction root. Extract only after the complete member list passes. Classify only manual NXT metadata, speaker-aligned orthographic transcript/timing links, dialogue acts, and official partition metadata. Any unclassified file that might be selected causes a hard failure. Audio, video, automatic annotations, DOME, social-role, and speculative-emotion paths are excluded and recorded; their content is not copied into tracked output.

`validate_ami_material` must retain participant, meeting, meeting-series, recording-site, scenario, source-corpus, and multi-party applicability metadata where the release supplies it. Missing required participant identity enters dependency quarantine. No transcript text is written to a tracked manifest or inventory beyond its relative path and hash.

The AMI manifest and quality evidence must record that some TNO participant metadata was not gathered, retain documented synchronization/dropout limitations even though media is unselected, and retain official scenario/full-corpus partition definitions as source metadata without assigning project cases.

- [ ] **Step 6: Implement the offline-only CLI**

The CLI accepts exactly:

```text
--crema-root
--ami-archive
--ami-extract-root
--accessed-on YYYY-MM-DD
--output-root research/sources/emotion_state/datasets
--mode list-ami | write-evidence
```

It rejects private paths, paths outside `data/public/emotion-state/`, an output root outside `research/sources/emotion_state/datasets/`, and any import or use of `socket`, `urllib`, `http.client`, third-party HTTP clients, GitHub clients, or provider clients. `list-ami` prints only normalized member paths and classification; `write-evidence` writes the six tracked manifest/hash/quality files atomically through temporary sibling files and `os.replace`.

If a verified output manifest already exists, `write-evidence` must compare canonical bytes and succeed only when the new bytes are identical. Different bytes under the same manifest version fail with `verified_manifest_version_is_immutable`; the operator must create a new reviewed version rather than overwrite it.

- [ ] **Step 7: Run synthetic tests and commit the verifier without dataset outputs**

```powershell
python -m unittest scripts.test_emotion_state_001_open_dataset_gate.DatasetMaterialValidationTests -v
rg -n "^(from|import) (socket|urllib|http|requests|httpx|aiohttp|github|elevenlabs)(\.| |$)" scripts\build_emotion_state_public_dataset_manifests.py scripts\emotion_state_public_dataset_contracts.py
git diff --check
git add scripts\build_emotion_state_public_dataset_manifests.py scripts\emotion_state_public_dataset_contracts.py scripts\test_emotion_state_001_open_dataset_gate.py
git commit -m "Add offline EMOTION-STATE dataset verifier"
```

Expected: tests pass; `rg` returns the expected no-match exit `1`; no file exists under the tracked dataset evidence directory yet.

---

### Task 6: Add Byte-Bound Verification Evidence And Child-Process Guards

**Files:**

- Create: `research/sources/emotion_state/phase_a_verification_guard_policy.json`
- Create: `scripts/emotion_state_phase_a_verification_evidence.py`
- Create: `scripts/emotion_state_phase_a_guard_site/sitecustomize.py`
- Modify: `scripts/test_emotion_state_001_open_dataset_gate.py`

**Interfaces:**

- Consumes: fixed baseline commit, current input HEAD, Git state, exact guard policy, changed executable roots, and allowed commands.
- Produces: `build_verification_evidence(root, baseline_commit, head_commit, mode)`, `build_guarded_child_environment(parent_environment, injected_environment)`, `run_guarded_command(command_id, root, substitutions)`, `derive_repository_gate_statuses(ledger)`, `--validate-json-inputs`, normalized command ledger entries, and deterministic component digests.

- [ ] **Step 1: Write failing guard and determinism tests**

```python
class VerificationEvidenceTests(unittest.TestCase):
    def test_policy_exclusions_are_exact_and_outputs_do_not_self_hash(self) -> None:
        from scripts.emotion_state_phase_a_verification_evidence import OUTPUT_EXCLUSIONS
        self.assertEqual(OUTPUT_EXCLUSIONS, (
            "research/experiments/generated/EMOTION-STATE-001-phase-a-contracts/result.json",
            "research/experiments/generated/EMOTION-STATE-001-phase-a-contracts/report.md",
            ".tmp/emotion-state-001-phase-a-publication/**",
        ))

    def test_child_environment_is_allowlisted_without_logging_values(self) -> None:
        from scripts.emotion_state_phase_a_verification_evidence import build_guarded_child_environment
        cleaned, removed_names = build_guarded_child_environment(
            parent_environment={
                "PATH": "safe",
                "SYSTEMROOT": r"C:\Windows",
                "DIALOGUE_REASONER_API_KEY": "fixture-only",
                "GH_TOKEN": "fixture-only",
                "GITHUB_TOKEN": "fixture-only",
                "HF_TOKEN": "fixture-only",
                "AWS_SECRET_ACCESS_KEY": "fixture-only",
                "TOOL_AUTH_TOKEN": "fixture-only",
                "UNLISTED_BENIGN": "fixture-only",
            },
            injected_environment={
                "EMOTION_STATE_PHASE_A_GUARD_POLICY": "fixture-policy",
            },
        )
        self.assertEqual(cleaned, {
            "EMOTION_STATE_PHASE_A_GUARD_POLICY": "fixture-policy",
            "PATH": "safe",
            "SYSTEMROOT": r"C:\Windows",
        })
        self.assertEqual(removed_names, [
            "AWS_SECRET_ACCESS_KEY",
            "DIALOGUE_REASONER_API_KEY",
            "GH_TOKEN",
            "GITHUB_TOKEN",
            "HF_TOKEN",
            "TOOL_AUTH_TOKEN",
            "UNLISTED_BENIGN",
        ])
        self.assertNotIn("fixture-only", json.dumps(removed_names))

    def test_ledger_is_relative_deterministic_and_timestamp_free(self) -> None:
        from scripts.emotion_state_phase_a_verification_evidence import canonical_command_entry
        entry = canonical_command_entry(
            sequence_number=1,
            command_id="focused-contract-tests",
            argv=["python", "-m", "unittest", "scripts.test_emotion_state_001_open_dataset_gate"],
            working_directory=".",
            exit_status=0,
        )
        self.assertEqual(entry["working_directory"], ".")
        self.assertNotIn("timestamp", entry)
        self.assertNotIn(str(ROOT), json.dumps(entry))
```

Add subprocess tests that opt into the guard site and prove all of these boundaries:

- `builtins.open`, `io.open`, `os.open`, `os.stat`, `os.lstat`, `os.listdir`, `os.scandir`, and `os.readlink` reject a synthetic path under each private root;
- the same read/stat/list operations succeed for a synthetic public fixture;
- `socket.getaddrinfo`, `gethostbyname`, `gethostbyname_ex`, `gethostbyaddr`, and `getnameinfo`, an `AF_INET`/`AF_INET6` socket constructor, and connection/send/bind/listen/accept operations raise `PermissionError` before DNS or I/O;
- every exact credential name and at least one otherwise-unlisted `_API_KEY`, `_ACCESS_TOKEN`, `_AUTH_TOKEN`, `_SECRET`, and `_PASSWORD` name is absent in the child;
- an unlisted `subprocess` command is rejected, and direct `os.system`, `os.popen`, `os.spawn*`, `os.exec*`, or `os.startfile` process-launch bypasses are rejected.

Use temporary files only; never read or enumerate an existing private path. Add deterministic inventory tests for a rename, a committed deletion, a path with different staged and unstaged bytes, and an untracked path. Add closure tests that reject an unresolved local import, a dynamic subprocess target, a path escape, and a direct `ctypes`, `_socket`, network-client, or provider import outside the guard implementation. Add a publication-race test that mutates an input after validation but before the locked re-read and requires an abort with the last valid result/report pair byte-identical.

- [ ] **Step 2: Verify the tests fail before implementation**

```powershell
python -m unittest scripts.test_emotion_state_001_open_dataset_gate.VerificationEvidenceTests -v
```

Expected: missing-module failure.

- [ ] **Step 3: Create the exact tracked guard policy**

```json
{
  "policy_id": "emotion-state-phase-a-verification-guard-v1",
  "schema_version": 1,
  "network_allowed": false,
  "private_path_prefixes": ["data/private", "data/private-restricted"],
  "parent_environment_allowlist": [
    "COMSPEC", "PATH", "PATHEXT", "SYSTEMDRIVE", "SYSTEMROOT", "WINDIR"
  ],
  "guard_generated_environment_names": [
    "EMOTION_STATE_PHASE_A_ALLOWED_SUBPROCESSES_JSON",
    "EMOTION_STATE_PHASE_A_GUARD_POLICY",
    "EMOTION_STATE_PHASE_A_PROJECT_ROOT",
    "GIT_CONFIG_GLOBAL",
    "GIT_CONFIG_NOSYSTEM",
    "GIT_TERMINAL_PROMPT",
    "HOME",
    "PYTHONDONTWRITEBYTECODE",
    "PYTHONIOENCODING",
    "PYTHONPATH",
    "PYTHONUTF8",
    "TEMP",
    "TMP",
    "USERPROFILE"
  ],
  "provider_environment_exact_names": [
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "CARTESIA_API_KEY",
    "DIALOGUE_REASONER_API_KEY",
    "ELEVENLABS_API_KEY",
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "GROQ_API_KEY",
    "HF_TOKEN",
    "HUGGING_FACE_HUB_TOKEN",
    "LOCAL_DIALOGUE_REASONER_API_KEY",
    "OPENAI_API_KEY",
    "OPENAI_SECRET",
    "OPENROUTER_API_KEY",
    "TOGETHER_API_KEY",
    "TOOL_AUTH_TOKEN",
    "ULTRAVOX_API_KEY"
  ],
  "provider_environment_prefixes": [
    "ASSEMBLYAI_", "AWS_", "CARTESIA_", "DEEPGRAM_", "DIALOGUE_REASONER_",
    "ELEVENLABS_", "GH_", "GITHUB_", "GROQ_", "HF_", "HUGGING_FACE_",
    "LOCAL_DIALOGUE_REASONER_", "OPENAI_", "OPENROUTER_", "TOGETHER_",
    "TWILIO_", "ULTRAVOX_"
  ],
  "credential_environment_name_pattern": "(^|_)(API_KEY|ACCESS_KEY|ACCESS_TOKEN|AUTH_TOKEN|BEARER_TOKEN|PRIVATE_KEY|SECRET|TOKEN|PASSWORD)$",
  "forbidden_import_prefixes": [
    "_socket", "aiohttp", "assemblyai", "cartesia", "ctypes", "deepgram",
    "elevenlabs", "ftplib", "github", "groq", "http", "httpx",
    "openai", "openrouter", "requests", "socket", "together", "twilio",
    "ultravox", "urllib"
  ],
  "output_exclusions": [
    "research/experiments/generated/EMOTION-STATE-001-phase-a-contracts/result.json",
    "research/experiments/generated/EMOTION-STATE-001-phase-a-contracts/report.md",
    ".tmp/emotion-state-001-phase-a-publication/**"
  ],
  "canonical_output_files": ["result.json", "report.md"],
  "allowed_commands": [
    {
      "command_id": "focused-open-dataset-tests",
      "argv_template": ["python", "-m", "unittest", "scripts.test_emotion_state_001_open_dataset_gate", "-v"]
    },
    {
      "command_id": "closeout-hardening-tests",
      "argv_template": ["python", "-m", "unittest", "scripts.test_emotion_state_001_closeout_hardening", "-v"]
    },
    {
      "command_id": "phase-a-prepublication-validator",
      "argv_template": ["python", "scripts/validate_emotion_state_001_phase_a_contracts.py", "--section", "prepublication", "--mode", "{mode}"]
    },
    {
      "command_id": "phase-a-materials-validator",
      "argv_template": ["python", "scripts/validate_emotion_state_001_phase_a_contracts.py", "--section", "materials"]
    },
    {
      "command_id": "frozen-exp-002-validator",
      "argv_template": ["python", "scripts/validate_exp_002_frozen_response_baseline.py"]
    },
    {
      "command_id": "brain-schema-validator",
      "argv_template": ["python", "scripts/validate_brain_002_runtime_state_schema.py"]
    },
    {
      "command_id": "private-boundary-validator",
      "argv_template": ["python", "scripts/validate_private_data_boundary.py"]
    },
    {
      "command_id": "runtime-manifest-validator",
      "argv_template": ["python", "scripts/validate_runtime_manifest.py"]
    },
    {
      "command_id": "setup-validator",
      "argv_template": ["python", "scripts/validate_check_setup.py"]
    },
    {
      "command_id": "drift-validator",
      "argv_template": ["python", "scripts/validate_project_drift_guard.py"]
    },
    {
      "command_id": "thesis-reference-validator",
      "argv_template": ["python", "scripts/check_thesis_reference_registry.py"]
    },
    {
      "command_id": "thesis-update-validator",
      "argv_template": ["python", "scripts/check_thesis_update_gate.py"]
    },
    {
      "command_id": "context-policy-validator",
      "argv_template": ["python", "scripts/validate_context_reading_policy.py"]
    },
    {
      "command_id": "json-validator",
      "argv_template": ["python", "scripts/emotion_state_phase_a_verification_evidence.py", "--validate-json-inputs"]
    },
    {
      "command_id": "git-diff-check",
      "argv_template": ["git", "diff", "--check", "{baseline_commit}..{head_commit}"]
    }
  ]
}
```

The SHA-256 of the exact policy bytes is `guard_policy_digest`. Command IDs and templates are unique and closed. The only substitutions are `mode` in `{"material-pending", "complete"}` and two already-captured lowercase 40-hex commits; all other argument bytes must match. The launcher resolves the normalized `python` token to `sys.executable` but records `python` in the canonical ledger.

Derive repository gates only from normalized ledger entries using this exact map:

```python
REPOSITORY_GATE_COMMAND_IDS = {
    "focused_tests": ("focused-open-dataset-tests",),
    "closeout_hardening": ("closeout-hardening-tests",),
    "phase_a_prepublication": ("phase-a-prepublication-validator",),
    "materials": ("phase-a-materials-validator",),
    "frozen_exp_002": ("frozen-exp-002-validator",),
    "brain_schema": ("brain-schema-validator",),
    "private_boundary": ("private-boundary-validator",),
    "runtime_manifest": ("runtime-manifest-validator",),
    "setup": ("setup-validator",),
    "drift": ("drift-validator",),
    "thesis_reference_registry": ("thesis-reference-validator",),
    "thesis_update": ("thesis-update-validator",),
    "context_policy": ("context-policy-validator",),
    "json": ("json-validator",),
    "diff_check": ("git-diff-check",),
}
```

Complete mode requires exactly one ordered entry for every allowed command and exit `0`; material-pending mode omits only `phase-a-materials-validator`. Missing, duplicate, reordered, template-mismatched, or nonzero entries fail. `repository_gate_statuses` and `guarded_command_results` are derived output projections only and are rejected as caller-supplied completion evidence. `--validate-json-inputs` parses every changed or closure-reachable JSON input with duplicate-key rejection and no arbitrary path argument.

- [ ] **Step 4: Implement child-process network and private-path denial**

The guard site activates only when `EMOTION_STATE_PHASE_A_GUARD_POLICY` is present. It loads the exact policy, resolves the project root from `EMOTION_STATE_PHASE_A_PROJECT_ROOT`, and denies every resolved path below either private prefix through wrappers for `builtins.open`, `io.open`, `os.open`, `os.stat`, `os.lstat`, `os.listdir`, `os.scandir`, and `os.readlink`. Guarded code has no approved `dir_fd` use, so any non-null `dir_fd` is rejected rather than resolved ambiguously. Children launch with inherited nonstandard file descriptors closed.

The guard denies `AF_INET` and `AF_INET6` construction and replaces `socket.create_connection`, `socket.create_server`, `socket.socketpair`, `socket.fromfd`, DNS resolvers (`getaddrinfo`, `gethostbyname`, `gethostbyname_ex`, `gethostbyaddr`, `getnameinfo`), and socket `connect`, `connect_ex`, `sendto`, `sendmsg`, `bind`, `listen`, and `accept` operations with functions that raise `PermissionError("EMOTION-STATE Phase A network access is blocked")`. Static closure validation rejects direct `_socket` and `ctypes` imports as bypasses. The guard implementation itself is the only reviewed file allowed to import `socket`, solely to install denials; every other changed or closure-reachable executable is subject to the forbidden-import list.

It wraps `subprocess.Popen` so nested commands must match the normalized allowlist passed in `EMOTION_STATE_PHASE_A_ALLOWED_SUBPROCESSES_JSON`. Direct `os.system`, `os.popen`, every available `os.spawn*`/`os.exec*`, and `os.startfile` are replaced with deterministic denial functions; reviewed child commands must go through `run_guarded_command`.

`build_guarded_child_environment` starts empty, copies only the six named parent variables, and injects only policy-listed guard/runtime variables. `HOME`, `USERPROFILE`, `TEMP`, and `TMP` point to a fresh transaction-local directory; `PYTHONPATH` is rebuilt from reviewed guard/repository paths; `GIT_CONFIG_GLOBAL=NUL`, `GIT_CONFIG_NOSYSTEM=1`, and `GIT_TERMINAL_PROMPT=0`. No other parent variable passes through. Exact-name, prefix, and generic credential checks are defense in depth and also reject credential-looking injected names. Matching uppercases names for case-insensitive comparison; evidence records sorted removed names only, never values.

Do not place `sitecustomize.py` at repository root. `run_guarded_command` prepends only `scripts/emotion_state_phase_a_guard_site` to `PYTHONPATH` for guarded Python children.

- [ ] **Step 5: Implement committed and uncommitted byte inventories without inventing a Git state**

Use two collections:

```text
committed_change_inventory entries: path, git_mode, sha256
uncommitted_change_inventory entries: path, git_state, git_mode, sha256
```

`git_state` is exactly one of `staged`, `unstaged`, or `untracked`. A path with both staged and unstaged bytes receives two entries. Committed paths come from `git diff --name-status --find-renames <baseline>..<head>` and are kept separately so the exact three-state enum is not falsified. Renames bind old and new paths. Deleted paths bind the baseline blob mode/digest and deletion state in the committed collection. Exclude only the two canonical outputs and exact ignored transaction directory.

Sort entries by `(path, git_state)` where state exists. Re-read every byte and Git mode under the publication lock immediately before payload generation; any mismatch aborts.

- [ ] **Step 6: Implement executable dependency closure and command evidence**

Parse changed Python files with `ast` and resolve project-local `import` and `from` targets without importing them. Resolve literal Python subprocess targets and maintain a reviewed root list containing the Phase A runner, builder, validator, new contract modules, both test modules, frozen baseline validator, and BRAIN validator. Each closure entry is `{path, git_mode, sha256}` and each edge is `{consumer, dependency, edge_type}`. Reject provider imports, runtime consumers importing new gate modules, dynamic subprocess targets, unresolved local imports, and path escapes.

Forbidden-action scans apply only to the exact changed executable inputs and this resolved dependency closure. Do not use or describe a global repository no-match scan as proof; the repository legitimately contains unrelated provider/call code and the documentation contains boundary terms.

`run_guarded_command` accepts a policy command ID, root, and only the reviewed substitutions required by that command. It constructs argv from the policy rather than accepting caller-provided argv, rejects absolute worktree paths in the canonical ledger, builds the allowlisted child environment, injects the guard site for Python, records `{sequence_number, command_id, argv, working_directory, exit_status}`, and stores stdout/stderr only in ephemeral diagnostic memory. Secret values and wall-clock times never enter result evidence.

`verification_input_tree_digest` hashes canonical JSON containing baseline commit, verified input HEAD, both change inventories, closure inventory and edges, manifest/hash-inventory digests, normalized ledger, and guard-policy digest. `verification_run_id` is `sha256("emotion-state-phase-a-validator-v1:" + verification_input_tree_digest)`.

- [ ] **Step 7: Run tests and commit**

```powershell
python -m unittest scripts.test_emotion_state_001_open_dataset_gate.VerificationEvidenceTests -v
git diff --check
git add research\sources\emotion_state\phase_a_verification_guard_policy.json scripts\emotion_state_phase_a_verification_evidence.py scripts\emotion_state_phase_a_guard_site\sitecustomize.py scripts\test_emotion_state_001_open_dataset_gate.py
git commit -m "Guard EMOTION-STATE Phase A verification"
```

---

### Task 7: Integrate A Material-Pending Checkpoint Without Downloading Data

**Files:**

- Modify: `research/experiments/cases/emotion-state-001-phase-a-contracts.json`
- Modify: `scripts/emotion_state_phase_a_contracts.py`
- Modify: `scripts/run_emotion_state_001_phase_a_contracts.py`
- Modify: `scripts/validate_emotion_state_001_phase_a_contracts.py`
- Modify: `scripts/test_emotion_state_001_closeout_hardening.py`
- Modify: `docs/product/EMOTION_STATE_001_PHASE_A_CONTRACTS.md`
- Modify: `research/experiments/EMOTION-STATE-001-phase-a.md`
- Modify: `docs/product/COMMANDS.md`
- Modify: `docs/thesis/THESIS_REFERENCE_REGISTRY.md`
- Modify: `docs/thesis/DECISION_LOG.md`
- Modify: `docs/thesis/METHODOLOGY_LOG.md`
- Modify: `docs/thesis/ROADMAP.md`
- Modify: `scripts/check_setup.py`
- Modify: `scripts/validate_check_setup.py`
- Modify: `scripts/check_project_drift.py`
- Modify: `scripts/validate_project_drift_guard.py`
- Modify by runner: canonical `result.json` and `report.md`.

**Interfaces:**

- Consumes: completed Tasks 1-6 with no local dataset bytes.
- Produces: a guarded, reproducible `material_pending` checkpoint with two selected dataset IDs and `phase_a_complete=false`.

- [ ] **Step 1: Add failing state-machine and non-recursion tests**

```python
class PhaseAStateMachineTests(unittest.TestCase):
    def test_selected_but_unverified_materials_keep_phase_incomplete(self) -> None:
        from scripts.emotion_state_phase_a_contracts import determine_phase_a_completion
        state = determine_phase_a_completion({
            "mode": "material_pending",
            "selected_dataset_ids": [
                "crema-d-v1.0-audio-wav",
                "ami-manual-annotations-v1.6.2",
            ],
            "dataset_download_authorized": False,
            "dataset_evidence": [],
            "contract_statuses": {
                "public_dataset_contract": "pass",
                "split_manifest_v2_contract": "pass",
                "cohort_release_contract": "pass",
            },
        })
        self.assertFalse(state["phase_a_complete"])
        self.assertEqual(state["blocking_reason_codes"], [
            "dataset_download_not_authorized",
            "selected_dataset_manifests_not_verified",
        ])

    def test_checkpoint_readback_does_not_invoke_runner(self) -> None:
        from unittest import mock
        from scripts import validate_emotion_state_001_phase_a_contracts as validator
        with mock.patch.object(validator.subprocess, "run") as run:
            validator.validate_checkpoint_readback()
        run.assert_not_called()
```

Update existing timeout tests rather than deleting them. Preserve the stable `EMOTION-STATE-001 Phase A validation failed:` prefix, empty stderr, no traceback, and the existing publication/recovery tests. Add tests proving: a staged candidate retains a durable journal and byte-exact previous-pair backups; candidate readback never invokes the runner; accept verifies the receipt/canonical digests before cleanup; reject force-restores the previous pair even when the candidate pair is internally valid; an `awaiting_acceptance` crash recovers to the previous pair rather than committing the candidate; and an interrupted accepted-state cleanup can finish the already-accepted candidate safely.

- [ ] **Step 2: Verify the new tests fail**

```powershell
python -m unittest scripts.test_emotion_state_001_open_dataset_gate.PhaseAStateMachineTests -v
```

Expected: missing function/readback section failures.

- [ ] **Step 3: Update the fixed case to selected-but-not-authorized state**

Use this exact control surface while retaining the six baseline fingerprints:

```json
{
  "checkpoint_id": "EMOTION-STATE-001-phase-a-contracts",
  "schema_version": 2,
  "source_label": "public-only",
  "campaign_profile_id": "emotion-state-phase-a-fixture",
  "campaign_profile_version": "fixture-v2",
  "selected_public_datasets": [
    "crema-d-v1.0-audio-wav",
    "ami-manual-annotations-v1.6.2"
  ],
  "dataset_download_authorized": false,
  "dataset_evaluation_started": false,
  "private_data_access_allowed": false,
  "provider_operations_allowed": false,
  "runtime_behavior_change_allowed": false,
  "runtime_activation_allowed": false,
  "baseline_fingerprints": {
    "packages/prompts/baseline-non-adaptive.txt": "BB1FD1EAC0D4DE858BFDCE4A880BBF2C59C14A216489A1A85EF149F3E88D7FCA",
    "packages/prompts/baseline-adaptive.txt": "EBD4106841987CA4A322C2B8B95A33ECFFC4238BB476DEC611A640D5B000EB42",
    "research/experiments/cases/exp-002-dataset-derived.json": "882B94C0A31C41A94540941A254AC7E8119CADE9AAD9B071089E854917BDC7D6",
    "research/experiments/EXP-002-dataset-derived-baseline.md": "D930C845AC912D44610B3CE263B55EA03BFFD7CAB8706C2BC95CB17045FF1316",
    "research/experiments/generated/EXP-002/EXP-002-prompt-packet.md": "14017F985D54D2B46A338EA2EFA796B24202E3E5A3D3EB8223346CEA96E5CD09",
    "docs/thesis/EVALUATION_RUBRIC.md": "39D3CF33E38A0C13ADEE178F3DB4174D4D8E3A42B1DE4C274BF96FFA36FFB416"
  }
}
```

- [ ] **Step 4: Implement the completion state machine and bounded payload**

`determine_phase_a_completion(evidence)` accepts one evidence object in both modes and derives blockers from it; callers cannot pass `phase_a_complete`. In `material_pending` mode it must require `dataset_download_authorized=false`, zero dataset-evidence entries, passing public-dataset/cohort/split synthetic contract checks, and set:

```python
{
    "phase_a_contract_artifacts_built": True,
    "phase_a_complete": False,
    "phase_a_completion_scope": "source_provenance_dataset_selection_and_offline_contracts_only_material_verification_pending",
    "full_repository_gate_claimed_by_this_artifact": False,
    "live_aggregate_release_unblocked": False,
    "phase_b_unblocked": False,
    "public_dataset_evaluation_unblocked": False,
    "private_research_unblocked": False,
    "provider_feasibility_unblocked": False,
    "runtime_activation_unblocked": False,
}
```

The payload must include exact selected IDs, source pin, contract checks, blocker codes, and the normalized verification evidence. It must not invent local hashes or manifest counts.

- [ ] **Step 5: Split prepublication validation from checkpoint readback**

Refactor validator sections to:

```python
SECTIONS = {
    "source": validate_source,
    "contracts": validate_contracts,
    "split-v2": validate_split_v2,
    "cohort": validate_cohort,
    "materials": validate_materials,
    "patterns": validate_patterns,
    "brain": validate_brain_extension,
    "prepublication": validate_prepublication_inputs,
    "candidate": validate_candidate_readback,
    "checkpoint": validate_checkpoint_readback,
}
```

`validate_candidate_readback` requires an exact transaction receipt and a live `awaiting_acceptance` journal, then reads and validates the staged canonical pair without invoking the runner. `validate_checkpoint_readback` requires no live transaction and validates an accepted pair only; it never invokes the runner. `validate_prepublication_inputs` never reads or writes the canonical output pair and accepts `--mode` so pending and complete material requirements are explicit. This prevents runner-validator recursion. The runner invokes only allowed prepublication commands through the guarded command wrapper.

- [ ] **Step 6: Extend publication with an explicit acceptance transaction**

Add mutually exclusive CLI actions:

```text
--mode material-pending|complete --defer-acceptance --receipt <exact ignored transaction receipt>
--accept-receipt <same receipt>
--reject-receipt <same receipt>
```

Restrict receipts to `.tmp/emotion-state-001-phase-a-publication/`, encode only schema version, transaction ID, candidate result/report digests, previous-pair digests/presence, and mode, and omit timestamps and absolute paths. Under the existing OS lock, staging must:

1. recover any incomplete publication;
2. capture baseline and current input HEAD;
3. build the byte inventories and closure;
4. run the mode-specific guarded command set;
5. recompute every input byte, Git state, mode, edge, and digest;
6. build the deterministic payload;
7. stage and replace result first/report last with the existing fsync/backup/journal mechanics;
8. verify the candidate pair bytes but retain the journal/backups with durable `acceptance_status="awaiting_acceptance"`;
9. write the ignored receipt and return without claiming an accepted checkpoint.

`--accept-receipt` revalidates receipt, live journal, candidate digests, marker, canonical directory, and pure candidate-readback invariants under the lock, durably changes the journal to `acceptance_status="accepted"`, then removes backups/journal/receipt. If any acceptance check fails, it force-restores the byte-identical previous pair before returning nonzero. `--reject-receipt` always force-restores the previous pair (or removes the candidate when no previous pair existed), verifies the restoration, and cleans transaction state. Startup recovery treats `awaiting_acceptance` as rejected and restores the previous pair; only a durable `accepted` state may finish cleanup of a valid candidate.

Keep result-first/report-last replacement, file `fsync`, previous-pair backups, fixed destinations, and exact report marker. Extend the journal schema and tests rather than weakening existing recovery behavior. `material-pending` must refuse locally present dataset paths so an accidental early download cannot be silently ignored.

- [ ] **Step 7: Update documentation and register only files that already exist**

Register the new modules, schemas, policy, guard site, builder, tests, and synthetic fixture symmetrically in setup/drift. Do not register the six per-dataset evidence files before Task 9 creates them.

Register the primary CREMA-D, ODbL, DbCL, and AMI URLs from the approved spec in `THESIS_REFERENCE_REGISTRY.md`. Update product, experiment, decision, methodology, and roadmap records to state: two datasets selected; download and evaluation not started; source adaptation false; cohort/split design implemented against synthetic fixtures; `phase_a_complete=false`; no private/provider/call/simulation/runtime action; no production/customer/PSTN/ASR/latency claim.

Add commands:

```powershell
$receipt = '.tmp\emotion-state-001-phase-a-publication\material-pending-receipt.json'
python scripts\run_emotion_state_001_phase_a_contracts.py --mode material-pending --defer-acceptance --receipt $receipt
try {
    python scripts\validate_emotion_state_001_phase_a_contracts.py --section candidate --receipt $receipt
    if ($LASTEXITCODE -ne 0) { throw 'Pending candidate readback failed' }
    python -m unittest scripts.test_emotion_state_001_open_dataset_gate scripts.test_emotion_state_001_closeout_hardening -v
    if ($LASTEXITCODE -ne 0) { throw 'Pending candidate tests failed' }
    python scripts\run_emotion_state_001_phase_a_contracts.py --accept-receipt $receipt
    if ($LASTEXITCODE -ne 0) { throw 'Pending candidate acceptance failed' }
}
catch {
    if (Test-Path $receipt) {
        python scripts\run_emotion_state_001_phase_a_contracts.py --reject-receipt $receipt
        if ($LASTEXITCODE -ne 0) { throw 'Pending candidate rejection/restoration failed' }
    }
    throw
}
```

- [ ] **Step 8: Run focused and repository gates before publishing pending evidence**

```powershell
python -m unittest scripts.test_emotion_state_001_open_dataset_gate scripts.test_emotion_state_001_closeout_hardening -v
python scripts\validate_emotion_state_001_phase_a_contracts.py --section prepublication --mode material-pending
python scripts\validate_exp_002_frozen_response_baseline.py
python scripts\validate_brain_002_runtime_state_schema.py
python scripts\validate_private_data_boundary.py
python scripts\validate_runtime_manifest.py
python scripts\validate_check_setup.py
python scripts\validate_project_drift_guard.py
python scripts\check_thesis_reference_registry.py
python scripts\check_thesis_update_gate.py
python scripts\validate_context_reading_policy.py
python scripts\emotion_state_phase_a_verification_evidence.py --validate-json-inputs
git diff --check
```

Expected: all commands exit `0`. No dataset path is read or created.

- [ ] **Step 9: Commit inputs, publish pending evidence, validate, and commit only the pair**

```powershell
$task7Paths = @(
  'research/experiments/cases/emotion-state-001-phase-a-contracts.json',
  'research/sources/emotion_state/dataset_manifest_contract.json',
  'scripts/emotion_state_phase_a_contracts.py',
  'scripts/run_emotion_state_001_phase_a_contracts.py',
  'scripts/validate_emotion_state_001_phase_a_contracts.py',
  'scripts/test_emotion_state_001_open_dataset_gate.py',
  'scripts/test_emotion_state_001_closeout_hardening.py',
  'docs/product/EMOTION_STATE_001_PHASE_A_CONTRACTS.md',
  'research/experiments/EMOTION-STATE-001-phase-a.md',
  'docs/product/COMMANDS.md',
  'docs/thesis/THESIS_REFERENCE_REGISTRY.md',
  'docs/thesis/DECISION_LOG.md',
  'docs/thesis/METHODOLOGY_LOG.md',
  'docs/thesis/ROADMAP.md',
  'scripts/check_setup.py',
  'scripts/validate_check_setup.py',
  'scripts/check_project_drift.py',
  'scripts/validate_project_drift_guard.py'
)
git add -- $task7Paths
git commit -m "Integrate EMOTION-STATE open dataset gate contracts"
$receipt = '.tmp\emotion-state-001-phase-a-publication\material-pending-receipt.json'
python scripts\run_emotion_state_001_phase_a_contracts.py --mode material-pending --defer-acceptance --receipt $receipt
try {
    python scripts\validate_emotion_state_001_phase_a_contracts.py --section candidate --receipt $receipt
    if ($LASTEXITCODE -ne 0) { throw 'Pending candidate readback failed' }
    python scripts\run_emotion_state_001_phase_a_contracts.py --accept-receipt $receipt
    if ($LASTEXITCODE -ne 0) { throw 'Pending candidate acceptance failed' }
}
catch {
    if (Test-Path $receipt) {
        python scripts\run_emotion_state_001_phase_a_contracts.py --reject-receipt $receipt
        if ($LASTEXITCODE -ne 0) { throw 'Pending candidate rejection/restoration failed' }
    }
    throw
}
git diff --name-only
git add research\experiments\generated\EMOTION-STATE-001-phase-a-contracts\result.json research\experiments\generated\EMOTION-STATE-001-phase-a-contracts\report.md
git commit -m "Record EMOTION-STATE material pending checkpoint"
```

Expected: the pre-publication commit contains only planned inputs; candidate readback and acceptance say `phase_a_complete=false`, selected dataset count `2`, dataset download authorized `false`, and material verification pending; the second commit contains exactly the accepted result/report pair.

---

### Task 8: Hard Stop For Separate Public-Dataset Download Authorization

**Files:**

- No files change.

**Interfaces:**

- Consumes: clean, passing material-pending checkpoint from Task 7.
- Produces: either a new explicit user authorization or a bounded stop with `phase_a_complete=false`.

- [ ] **Step 1: Prove the branch is clean and the pending boundary is intact**

```powershell
git status --short --branch
python scripts\validate_emotion_state_001_phase_a_contracts.py --section checkpoint
```

Expected: clean status and a passing readback whose result contains `dataset_download_authorized=false`, `dataset_evaluation_started=false`, and `phase_a_complete=false`.

- [ ] **Step 2: Stop and request authorization using the exact scope**

Request explicit authorization for:

```text
Download only the pinned CREMA-D v1.0 Git/LFS artifacts and AMI manual annotations v1.6.2 archive into ignored data/public/emotion-state paths; perform local hash, safe-extraction, quality, dependency, and manifest verification only. No private data, provider access, calls, simulations, source adaptation, public-dataset model evaluation, or runtime activation.
```

Approval of the design, this implementation plan, or Tasks 1-7 does not authorize Task 9. If the user does not give the new authorization, stop execution here and report that contracts are implemented but material verification remains the exact blocker.

---

### Task 9: Acquire Only The Authorized Canonical Public Artifacts And Generate Inventories

**Files:**

- Create under ignored data paths: CREMA-D repository/LFS material and AMI archive/extraction.
- Create tracked: the six dataset manifest/hash/quality files listed in the file map.
- Modify: `research/experiments/cases/emotion-state-001-phase-a-contracts.json`
- Modify: `research/sources/emotion_state/dataset_manifest_contract.json`
- Modify if the canonical AMI archive exposes an unclassified selected path: `scripts/emotion_state_public_dataset_contracts.py` and its focused tests, followed by review before evidence generation.

**Interfaces:**

- Consumes: separate Task 8 authorization and canonical public sources only.
- Produces: locally verified, tracked metadata/inventories while raw bytes remain ignored.

- [ ] **Step 1: Record authorization state without opening evaluation**

Set `dataset_download_authorized` to `true` in the case and dataset contract. Keep `dataset_evaluation_started=false`, all runtime flags false, and `phase_a_complete` derived rather than stored in the case.

- [ ] **Step 2: Verify tools and exact ignored destinations**

```powershell
git lfs version
New-Item -ItemType Directory -Force data\public\emotion-state\crema-d-v1.0 | Out-Null
New-Item -ItemType Directory -Force data\public\emotion-state\ami-manual-annotations-v1.6.2 | Out-Null
git check-ignore -v data\public\emotion-state\crema-d-v1.0 data\public\emotion-state\ami-manual-annotations-v1.6.2
```

Expected: Git LFS is available and both destinations are ignored by `data/public/*`. Stop if either destination is not ignored.

- [ ] **Step 3: Acquire the exact CREMA-D revision with selected LFS media**

```powershell
$cremaRepository = Join-Path (Resolve-Path data\public\emotion-state\crema-d-v1.0) 'repository'
$previousLfsSkipSmudge = [Environment]::GetEnvironmentVariable('GIT_LFS_SKIP_SMUDGE', 'Process')
try {
    $env:GIT_LFS_SKIP_SMUDGE = '1'
    git clone --no-checkout https://github.com/CheyneyComputerScience/CREMA-D $cremaRepository
    if ($LASTEXITCODE -ne 0) { throw 'CREMA-D clone failed' }
    git -C $cremaRepository checkout --detach f3b8611a309886568dfa957141775b2e05add04a
    if ($LASTEXITCODE -ne 0) { throw 'CREMA-D detached checkout failed' }
}
finally {
    if ($null -eq $previousLfsSkipSmudge) {
        Remove-Item Env:\GIT_LFS_SKIP_SMUDGE -ErrorAction SilentlyContinue
    }
    else {
        $env:GIT_LFS_SKIP_SMUDGE = $previousLfsSkipSmudge
    }
}
git -C $cremaRepository lfs pull --include="AudioWAV/**" --exclude="VideoFlash/**,AudioMP3/**"
if ($LASTEXITCODE -ne 0) { throw 'Scoped CREMA-D AudioWAV LFS pull failed' }
$excludedMaterialized = git -C $cremaRepository lfs ls-files | Select-String '^[0-9a-f]+ \* (VideoFlash/|AudioMP3/)'
if ($excludedMaterialized) { throw 'Excluded CREMA-D LFS media materialized' }
$includedMaterialized = git -C $cremaRepository lfs ls-files | Select-String '^[0-9a-f]+ \* AudioWAV/'
if (-not $includedMaterialized) { throw 'Selected CREMA-D AudioWAV LFS media did not materialize' }
git -C $cremaRepository rev-parse HEAD
git -C $cremaRepository status --short
```

Expected: skip-smudge remains active through clone and detached checkout; only `AudioWAV/**` objects are pulled; no `VideoFlash/**` or `AudioMP3/**` object is materialized; HEAD is exactly `f3b8611a309886568dfa957141775b2e05add04a`; and repository status is clean. Do not substitute an unofficial mirror or ordinary GitHub ZIP.

- [ ] **Step 4: Acquire the official AMI manual-annotation archive**

Using the canonical `https://groups.inf.ed.ac.uk/ami/download/` page, save only the official `AMI manual annotations v1.6.2` archive to:

```text
data/public/emotion-state/ami-manual-annotations-v1.6.2/ami_manual_1.6.2.zip
```

Do not download AMI audio, video, automatic annotations, DOME, social-role, or speculative-emotion material. Then run:

```powershell
Get-FileHash -Algorithm SHA256 data\public\emotion-state\ami-manual-annotations-v1.6.2\ami_manual_1.6.2.zip
python scripts\build_emotion_state_public_dataset_manifests.py --mode list-ami --crema-root data\public\emotion-state\crema-d-v1.0\repository --ami-archive data\public\emotion-state\ami-manual-annotations-v1.6.2\ami_manual_1.6.2.zip --ami-extract-root data\public\emotion-state\ami-manual-annotations-v1.6.2\extracted --accessed-on $((Get-Date).ToUniversalTime().ToString('yyyy-MM-dd')) --output-root research\sources\emotion_state\datasets
```

Expected: archive SHA-256 prints; every member is classified as selected, excluded, or metadata-only; no unclassified selected candidate, path escape, symlink, or case collision exists. The list command does not extract or write tracked evidence.

- [ ] **Step 5: Generate deterministic tracked evidence offline**

```powershell
$accessedOn = (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd')
python scripts\build_emotion_state_public_dataset_manifests.py --mode write-evidence --crema-root data\public\emotion-state\crema-d-v1.0\repository --ami-archive data\public\emotion-state\ami-manual-annotations-v1.6.2\ami_manual_1.6.2.zip --ami-extract-root data\public\emotion-state\ami-manual-annotations-v1.6.2\extracted --accessed-on $accessedOn --output-root research\sources\emotion_state\datasets
python scripts\validate_emotion_state_001_phase_a_contracts.py --section materials
```

Expected: exactly six tracked evidence files are created; every selected local file is hashed; CREMA WAV/LFS and quality checks pass; AMI archive and selected extracted files pass; no raw audio or transcript content enters tracked output.

- [ ] **Step 6: Independently inspect the generated evidence and Git boundary**

```powershell
Get-ChildItem research\sources\emotion_state\datasets -File | Sort-Object Name | Select-Object Name,Length
git status --short
git ls-files data\public
git check-ignore -v data\public\emotion-state\crema-d-v1.0\repository\AudioWAV data\public\emotion-state\ami-manual-annotations-v1.6.2\ami_manual_1.6.2.zip
python -m unittest scripts.test_emotion_state_001_open_dataset_gate.DatasetMaterialValidationTests -v
```

Expected: the evidence directory contains the six named JSON files; no raw public file is tracked; `git ls-files data/public` lists only the existing `.gitkeep`; synthetic material tests still pass.

- [ ] **Step 7: Do not commit yet**

Leave the six evidence files and authorization-state edits uncommitted for Task 10, where their exact counts/digests are propagated consistently into docs and registrations before the verified input HEAD is frozen.

---

### Task 10: Propagate Exact Evidence, Register Files, And Freeze The Verified Input HEAD

**Files:**

- Modify: Phase A builder, validator, case, dataset contract, product/experiment/thesis docs, setup/drift registration files.
- Add: six generated dataset evidence files.
- Do not modify: canonical result/report pair in this task.

**Interfaces:**

- Consumes: locally verified Task 9 evidence.
- Produces: a clean committed input HEAD from which the final deterministic pair can be generated without self-reference.

- [ ] **Step 1: Add complete-state tests before enabling completion**

```python
class PhaseACompleteStateTests(unittest.TestCase):
    def complete_gate_evidence(self) -> dict:
        from scripts.emotion_state_phase_a_verification_evidence import (
            REQUIRED_PHASE_A_COMMAND_IDS,
            expected_argv_for_command,
        )
        digest = "A" * 64
        baseline_commit = "b" * 40
        head_commit = "c" * 40
        return {
            "mode": "complete",
            "selected_dataset_ids": [
                "crema-d-v1.0-audio-wav",
                "ami-manual-annotations-v1.6.2",
            ],
            "dataset_download_authorized": True,
            "dataset_evidence": [
                {
                    "dataset_id": dataset_id,
                    "completion_status": "verified",
                    "manifest_sha256": digest,
                    "hash_inventory_sha256": digest,
                    "quality_inventory_sha256": digest,
                    "source_provenance_status": "pass",
                    "material_validation_status": "pass",
                }
                for dataset_id in (
                    "crema-d-v1.0-audio-wav",
                    "ami-manual-annotations-v1.6.2",
                )
            ],
            "contract_statuses": {
                "public_dataset_contract": "pass",
                "split_manifest_v2_contract": "pass",
                "cohort_release_contract": "pass",
            },
            "verification_evidence": {
                "implementation_baseline_commit": baseline_commit,
                "repository_head_commit": head_commit,
                "verification_run_id": digest,
                "verification_input_path_inventory_digest": digest,
                "executable_dependency_closure_digest": digest,
                "executed_command_ledger_digest": digest,
                "guard_policy_digest": digest,
                "verification_input_tree_digest": digest,
                "provider_environment_scrubbed": True,
                "private_path_guard_enabled": True,
                "network_guard_enabled": True,
                "prepublication_byte_lock_reread_status": "pass",
            },
            "executed_command_ledger": [
                {
                    "sequence_number": sequence_number,
                    "command_id": command_id,
                    "argv": expected_argv_for_command(
                        command_id,
                        mode="complete",
                        baseline_commit=baseline_commit,
                        head_commit=head_commit,
                    ),
                    "working_directory": ".",
                    "exit_status": 0,
                }
                for sequence_number, command_id in enumerate(
                    REQUIRED_PHASE_A_COMMAND_IDS, start=1
                )
            ],
            "publication_integrity_preconditions": {
                "crash_safe_pair_protocol_status": "pass",
                "explicit_acceptance_transaction_status": "pass",
                "last_valid_pair_preservation_status": "pass",
                "output_self_reference_absent": True,
            },
            "authorization_boundaries": {
                "live_aggregate_release_unblocked": False,
                "public_dataset_evaluation_unblocked": False,
                "phase_b_unblocked": False,
                "private_research_unblocked": False,
                "provider_feasibility_unblocked": False,
                "runtime_activation_unblocked": False,
            },
        }

    def test_completion_requires_both_verified_manifests_and_every_closed_gate(self) -> None:
        from scripts.emotion_state_phase_a_contracts import determine_phase_a_completion
        completed = determine_phase_a_completion(self.complete_gate_evidence())
        self.assertTrue(completed["phase_a_complete"])
        self.assertEqual(completed["blocking_reason_codes"], [])

    def test_missing_one_manifest_stays_incomplete(self) -> None:
        from scripts.emotion_state_phase_a_contracts import determine_phase_a_completion
        evidence = self.complete_gate_evidence()
        evidence["dataset_evidence"].pop()
        incomplete = determine_phase_a_completion(evidence)
        self.assertFalse(incomplete["phase_a_complete"])
        self.assertEqual(incomplete["blocking_reason_codes"], [
            "selected_dataset_manifests_not_verified",
        ])

    def test_each_closed_gate_can_independently_block_completion(self) -> None:
        from scripts.emotion_state_phase_a_contracts import determine_phase_a_completion
        mutations = (
            ("verification_evidence", "network_guard_enabled", False),
            ("publication_integrity_preconditions", "last_valid_pair_preservation_status", "fail"),
        )
        for section, key, value in mutations:
            with self.subTest(section=section, key=key):
                evidence = self.complete_gate_evidence()
                evidence[section][key] = value
                self.assertFalse(determine_phase_a_completion(evidence)["phase_a_complete"])

        evidence = self.complete_gate_evidence()
        drift = next(
            entry for entry in evidence["executed_command_ledger"]
            if entry["command_id"] == "drift-validator"
        )
        drift["exit_status"] = 1
        self.assertFalse(determine_phase_a_completion(evidence)["phase_a_complete"])

    def test_repository_gate_statuses_are_derived_only(self) -> None:
        from scripts.emotion_state_phase_a_contracts import determine_phase_a_completion
        evidence = self.complete_gate_evidence()
        evidence["repository_gate_statuses"] = {"drift": "pass"}
        with self.assertRaisesRegex(ValueError, "derived-only"):
            determine_phase_a_completion(evidence)
```

`REQUIRED_PHASE_A_COMMAND_IDS` is derived in order from the exact policy templates. Repository gates are the exact ordered keys of `REPOSITORY_GATE_COMMAND_IDS`; they are never accepted as input. Extend the table-driven negative test to cover every dataset digest/provenance/material field, every contract status, every verification digest/guard, every missing/duplicate/reordered/template-mismatched/nonzero ledger entry, every derived repository gate, every publication-integrity precondition, and every false authorization boundary. Run this class first and confirm it fails until the complete state is implemented.

- [ ] **Step 2: Bind manifests, inventories, quality evidence, and exact completion scope into the payload**

The complete payload must contain:

```text
selected_public_datasets
dataset_manifest_evidence
dataset_hash_inventory_digests
dataset_quality_inventory_digests
dataset_material_validation_status
source_provenance_status
public_dataset_contract_status
cohort_release_contract_status
split_manifest_v2_contract_status
implementation_baseline_commit
repository_head_commit
verification_run_id
verification_input_path_inventory_digest
executable_dependency_closure_digest
executed_command_ledger_digest
guard_policy_digest
verification_input_tree_digest
provider_environment_scrubbed = true
private_path_guard_enabled = true
network_guard_enabled = true
prepublication_byte_lock_reread_status = pass
executed_command_ledger
guarded_command_results (derived from executed_command_ledger)
repository_gate_statuses (derived from executed_command_ledger)
publication_integrity_preconditions
phase_a_completion_scope = source_provenance_dataset_manifests_offline_contracts_and_cohort_release_gate_only
```

`phase_a_complete=true` is derived only in `complete` mode and only when the exact complete-gate evidence object passes: locally recomputed manifest/inventory/quality bytes and exact two-dataset order; provenance, material, public-dataset, cohort, and split contracts; byte-bound verification evidence; all guarded commands with exit `0`; every repository gate; crash-safe publication and last-valid-pair preservation tests; and all false authorization boundaries. No caller may pass only IDs or advertised statuses.

The payload cannot contain the digest of the final pair without self-reference. Therefore `publication_integrity_preconditions` binds the tested publication protocol and locked input re-read, while Task 11 independently accepts the just-written pair only after canonical result parsing, exact report hash-marker verification, recovery-state inspection, and byte-identical last-valid-pair checks. A `phase_a_complete=true` payload is not an accepted checkpoint until that post-write validation passes. Keep `live_aggregate_release_unblocked=false`, `public_dataset_evaluation_unblocked=false`, `phase_b_unblocked=false`, `private_research_unblocked=false`, `provider_feasibility_unblocked=false`, and `runtime_activation_unblocked=false`.

- [ ] **Step 3: Update docs using exact generated values, not advertised counts**

Read the six evidence JSON files and record their actual selected file counts, selected byte counts, archive/inventory/quality SHA-256 values, CREMA inclusion/exclusion counts, AMI selected/excluded counts, and accessed dates. Do not use 7,442 as a verified included count unless the inventory independently produces that number.

Update:

- product contract and commands with pending versus complete modes and clean-clone readback behavior;
- experiment note with exact local verification evidence;
- methodology/decision/roadmap records with the open-only two-lane decision and bounded completion scope;
- reference registry with exact primary source roles;
- source notes with no-adaptation status.

State explicitly that `materials` validation requires ignored local bytes, while `checkpoint` validates the recorded tracked evidence and pair in a clean clone. A clean clone cannot re-prove raw-byte availability; it can only validate what the captured complete run recorded.

- [ ] **Step 4: Register all new tracked files symmetrically**

Add every new module, schema, policy, fixture, builder, test, and six evidence JSON paths to `check_setup.py` and the exact required-ID checks in `validate_check_setup.py`. Add the same paths to both drift required-file lists and `PHASE_A_REQUIRED_PATHS`. Keep lists unique and symmetric. Do not register ignored raw dataset paths.

- [ ] **Step 5: Run all prepublication gates with local material available**

```powershell
python -m unittest scripts.test_emotion_state_001_open_dataset_gate scripts.test_emotion_state_001_closeout_hardening -v
python scripts\validate_emotion_state_001_phase_a_contracts.py --section source
python scripts\validate_emotion_state_001_phase_a_contracts.py --section contracts
python scripts\validate_emotion_state_001_phase_a_contracts.py --section split-v2
python scripts\validate_emotion_state_001_phase_a_contracts.py --section cohort
python scripts\validate_emotion_state_001_phase_a_contracts.py --section materials
python scripts\validate_emotion_state_001_phase_a_contracts.py --section prepublication --mode complete
python scripts\validate_exp_002_frozen_response_baseline.py
python scripts\validate_brain_002_runtime_state_schema.py
python scripts\validate_private_data_boundary.py
python scripts\validate_runtime_manifest.py
python scripts\validate_check_setup.py
python scripts\validate_project_drift_guard.py
python scripts\check_thesis_reference_registry.py
python scripts\check_thesis_update_gate.py
python scripts\validate_context_reading_policy.py
python scripts\emotion_state_phase_a_verification_evidence.py --validate-json-inputs
git diff --check
```

Expected: all commands exit `0`; local materials pass; canonical result/report are still the prior material-pending pair.

- [ ] **Step 6: Inspect forbidden runtime/provider/dependency changes**

```powershell
rg -n "emotion_state_(public_dataset|split_manifest_v2|cohort_release|phase_a_verification)" runtime\entrypoints runtime\core runtime\action_selector runtime\providers
git diff fb0513545fc0167bcf89dbc81283b7b2a2820b67 --name-only | rg --pcre2 "(^|/)(requirements[^/]*\.txt|pyproject\.toml|setup\.py|setup\.cfg|Pipfile|poetry\.lock|uv\.lock|package(-lock)?\.json)$"
git status --short
```

Expected: both `rg` commands return no matches. Inspect status to ensure every path is named in this plan and no raw dataset, provider, runtime consumer, private, call, simulation, or friend-project source file is present.

- [ ] **Step 7: Commit all verified inputs and freeze the input HEAD**

```powershell
$verifiedInputPaths = @(
  'research/sources/emotion_state/dataset_manifest_contract.json',
  'research/sources/emotion_state/datasets/crema-d-v1.0-audio-wav.manifest.json',
  'research/sources/emotion_state/datasets/crema-d-v1.0-audio-wav.hashes.json',
  'research/sources/emotion_state/datasets/crema-d-v1.0-audio-wav.quality.json',
  'research/sources/emotion_state/datasets/ami-manual-annotations-v1.6.2.manifest.json',
  'research/sources/emotion_state/datasets/ami-manual-annotations-v1.6.2.hashes.json',
  'research/sources/emotion_state/datasets/ami-manual-annotations-v1.6.2.quality.json',
  'research/experiments/cases/emotion-state-001-phase-a-contracts.json',
  'scripts/emotion_state_public_dataset_contracts.py',
  'scripts/emotion_state_phase_a_contracts.py',
  'scripts/run_emotion_state_001_phase_a_contracts.py',
  'scripts/validate_emotion_state_001_phase_a_contracts.py',
  'scripts/test_emotion_state_001_open_dataset_gate.py',
  'scripts/test_emotion_state_001_closeout_hardening.py',
  'docs/product/EMOTION_STATE_001_PHASE_A_CONTRACTS.md',
  'docs/product/COMMANDS.md',
  'docs/thesis/THESIS_REFERENCE_REGISTRY.md',
  'docs/thesis/DECISION_LOG.md',
  'docs/thesis/METHODOLOGY_LOG.md',
  'docs/thesis/ROADMAP.md',
  'research/experiments/EMOTION-STATE-001-phase-a.md',
  'research/sources/creative_analysis_engine/source_notes.md',
  'scripts/check_setup.py',
  'scripts/validate_check_setup.py',
  'scripts/check_project_drift.py',
  'scripts/validate_project_drift_guard.py'
)
git add -- $verifiedInputPaths
git commit -m "Verify EMOTION-STATE public dataset gate inputs"
git status --short --branch
git rev-parse HEAD
```

Expected: the worktree is clean. Record the printed commit as the verified input HEAD. Do not generate or commit the final pair before this point.

---

### Task 11: Run Guarded Complete Publication, Independently Read Back, And Commit The Pair

**Files:**

- Modify by runner: canonical `result.json` and `report.md` only.
- Temporary ignored transaction state: receipt, journal, staged files, and backups under `.tmp/emotion-state-001-phase-a-publication/`; none may be tracked or survive acceptance/rejection cleanup.

**Interfaces:**

- Consumes: clean verified input HEAD from Task 10 and ignored local public bytes.
- Produces: a validated two-file complete checkpoint followed by one pair-only commit.

- [ ] **Step 1: Stage the complete candidate under the existing publication lock**

```powershell
$inputHead = (git rev-parse HEAD).Trim()
$receipt = '.tmp\emotion-state-001-phase-a-publication\complete-receipt.json'
python scripts\run_emotion_state_001_phase_a_contracts.py --mode complete --defer-acceptance --receipt $receipt
if ($LASTEXITCODE -ne 0) { throw 'Complete candidate staging failed' }
if (-not (Test-Path $receipt)) { throw 'Complete candidate receipt is missing' }
```

Expected: the runner exits `0`, the candidate pair is canonical on disk, and the durable transaction retains the prior material-pending pair until explicit acceptance. `phase_a_complete=true` inside the candidate is not yet an accepted checkpoint.

- [ ] **Step 2: Independently validate every gate while rollback remains available**

```powershell
$resultPath = 'research\experiments\generated\EMOTION-STATE-001-phase-a-contracts\result.json'
$reportPath = 'research\experiments\generated\EMOTION-STATE-001-phase-a-contracts\report.md'
$canonicalDirectory = Split-Path -Parent $resultPath
try {
    $checks = @(
        @{ Label = 'materials'; Exe = 'python'; Args = @('scripts/validate_emotion_state_001_phase_a_contracts.py', '--section', 'materials') },
        @{ Label = 'candidate readback'; Exe = 'python'; Args = @('scripts/validate_emotion_state_001_phase_a_contracts.py', '--section', 'candidate', '--receipt', $receipt) },
        @{ Label = 'focused tests'; Exe = 'python'; Args = @('-m', 'unittest', 'scripts.test_emotion_state_001_open_dataset_gate', '-v') },
        @{ Label = 'closeout hardening'; Exe = 'python'; Args = @('-m', 'unittest', 'scripts.test_emotion_state_001_closeout_hardening', '-v') },
        @{ Label = 'frozen EXP-002'; Exe = 'python'; Args = @('scripts/validate_exp_002_frozen_response_baseline.py') },
        @{ Label = 'BRAIN schema'; Exe = 'python'; Args = @('scripts/validate_brain_002_runtime_state_schema.py') },
        @{ Label = 'private boundary'; Exe = 'python'; Args = @('scripts/validate_private_data_boundary.py') },
        @{ Label = 'runtime manifest'; Exe = 'python'; Args = @('scripts/validate_runtime_manifest.py') },
        @{ Label = 'setup'; Exe = 'python'; Args = @('scripts/validate_check_setup.py') },
        @{ Label = 'drift'; Exe = 'python'; Args = @('scripts/validate_project_drift_guard.py') },
        @{ Label = 'thesis references'; Exe = 'python'; Args = @('scripts/check_thesis_reference_registry.py') },
        @{ Label = 'thesis update'; Exe = 'python'; Args = @('scripts/check_thesis_update_gate.py') },
        @{ Label = 'context policy'; Exe = 'python'; Args = @('scripts/validate_context_reading_policy.py') },
        @{ Label = 'JSON inputs'; Exe = 'python'; Args = @('scripts/emotion_state_phase_a_verification_evidence.py', '--validate-json-inputs') }
    )
    foreach ($check in $checks) {
        $executable = $check.Exe
        $arguments = $check.Args
        & $executable @arguments
        if ($LASTEXITCODE -ne 0) { throw "$($check.Label) failed" }
    }

    $result = Get-Content -Raw $resultPath | ConvertFrom-Json
    if ($result.repository_head_commit -ne $inputHead) { throw 'Result does not bind the verified input HEAD' }
    if ($result.implementation_baseline_commit -ne 'fb0513545fc0167bcf89dbc81283b7b2a2820b67') { throw 'Baseline commit mismatch' }
    if ($result.readiness_boundary.phase_a_complete -ne $true) { throw 'Phase A did not reach its bounded complete state' }

    $resultHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $resultPath).Hash
    $report = Get-Content -Raw $reportPath
    if ($report -notmatch [regex]::Escape("result.json sha256:$resultHash")) { throw 'Report marker mismatch' }
    if ($result.selected_public_datasets.Count -ne 2) { throw 'Dataset count mismatch' }
    if ($result.dataset_evaluation_started -ne $false) { throw 'Dataset evaluation boundary opened' }
    if ($result.summary.provider_operations_performed_by_runner -ne $false) { throw 'Provider boundary mismatch' }
    if ($result.summary.private_data_read_by_runner -ne $false) { throw 'Private-data boundary mismatch' }
    if ($result.summary.code_adaptation_started -ne $false) { throw 'Source-adaptation boundary mismatch' }
    if ($result.readiness_boundary.runtime_activation_unblocked -ne $false) { throw 'Runtime boundary mismatch' }
    if ($result.publication_integrity_preconditions.crash_safe_pair_protocol_status -ne 'pass') { throw 'Publication protocol evidence mismatch' }
    if ($result.publication_integrity_preconditions.explicit_acceptance_transaction_status -ne 'pass') { throw 'Publication acceptance evidence mismatch' }
    if ($result.publication_integrity_preconditions.last_valid_pair_preservation_status -ne 'pass') { throw 'Last-valid-pair evidence mismatch' }
    if (@($result.guarded_command_results.PSObject.Properties.Value | Where-Object { $_ -ne 0 }).Count -ne 0) { throw 'Guarded command failure recorded' }
    if (@($result.repository_gate_statuses.PSObject.Properties.Value | Where-Object { $_ -ne 'pass' }).Count -ne 0) { throw 'Derived repository gate failure recorded' }

    $canonicalNames = @(Get-ChildItem -Force $canonicalDirectory -File | Sort-Object Name | Select-Object -ExpandProperty Name)
    if (@(Compare-Object @('report.md', 'result.json') $canonicalNames).Count -ne 0) { throw 'Canonical directory contains a missing or third file' }
    $changedPaths = @(git diff --name-only)
    if ($LASTEXITCODE -ne 0) { throw 'Git changed-path inspection failed' }
    $expectedChangedPaths = @(
        'research/experiments/generated/EMOTION-STATE-001-phase-a-contracts/report.md',
        'research/experiments/generated/EMOTION-STATE-001-phase-a-contracts/result.json'
    )
    if (@(Compare-Object $expectedChangedPaths $changedPaths).Count -ne 0) { throw 'Candidate changed-path scope mismatch' }
    git diff --check
    if ($LASTEXITCODE -ne 0) { throw 'Candidate diff check failed' }
}
catch {
    $candidateFailure = $_
    if (Test-Path $receipt) {
        python scripts\run_emotion_state_001_phase_a_contracts.py --reject-receipt $receipt
        if ($LASTEXITCODE -ne 0) {
            throw "Candidate validation failed and previous-pair restoration also failed: $candidateFailure"
        }
    }
    throw $candidateFailure
}
```

Expected: every check exits `0`, the canonical directory contains exactly the candidate pair, Git shows only those two files, and the prior pair remains recoverable because the receipt is still awaiting acceptance.

- [ ] **Step 3: Inspect the evidence directly, then accept or reject**

Inspect normalized input inventories, dependency closure, command ledger, and the derived command/gate projections in the candidate rather than trusting summary labels. Confirm no secret value, absolute worktree path, timestamp, speaker token, per-speaker row, raw transcript, raw audio, provider payload, or third canonical artifact appears.

If any inspection fails, run the reject command and stop:

```powershell
python scripts\run_emotion_state_001_phase_a_contracts.py --reject-receipt $receipt
if ($LASTEXITCODE -ne 0) { throw 'Complete candidate rejection/restoration failed' }
throw 'Complete candidate rejected after independent inspection'
```

Only after the inspection passes, accept:

```powershell
python scripts\run_emotion_state_001_phase_a_contracts.py --accept-receipt $receipt
if ($LASTEXITCODE -ne 0) { throw 'Complete candidate acceptance failed; verify restoration state' }
if (Test-Path $receipt) { throw 'Accepted transaction receipt was not cleaned' }
```

Expected: acceptance revalidates the same candidate under lock and removes transaction state. A failed acceptance restores the exact prior pair before returning nonzero.

- [ ] **Step 4: Commit only the accepted canonical pair**

```powershell
git add research\experiments\generated\EMOTION-STATE-001-phase-a-contracts\result.json research\experiments\generated\EMOTION-STATE-001-phase-a-contracts\report.md
$stagedPaths = @(git diff --cached --name-only)
$expectedStagedPaths = @(
    'research/experiments/generated/EMOTION-STATE-001-phase-a-contracts/report.md',
    'research/experiments/generated/EMOTION-STATE-001-phase-a-contracts/result.json'
)
if (@(Compare-Object $expectedStagedPaths $stagedPaths).Count -ne 0) { throw 'Staged pair scope mismatch' }
git commit -m "Record EMOTION-STATE Phase A open dataset gate"
if ($LASTEXITCODE -ne 0) { throw 'Canonical pair commit failed' }
```

Expected: staged scope and commit contain exactly the accepted two-file pair.

- [ ] **Step 5: Verify the output-only successor relationship and clean status**

```powershell
$recordedInputHead = (Get-Content -Raw $resultPath | ConvertFrom-Json).repository_head_commit
git merge-base --is-ancestor $recordedInputHead HEAD
if ($LASTEXITCODE -ne 0) { throw 'Recorded input HEAD is not an ancestor' }
$successorPaths = @(git diff --name-only $recordedInputHead..HEAD)
$expectedSuccessorPaths = @(
    'research/experiments/generated/EMOTION-STATE-001-phase-a-contracts/report.md',
    'research/experiments/generated/EMOTION-STATE-001-phase-a-contracts/result.json'
)
if (@(Compare-Object $expectedSuccessorPaths $successorPaths).Count -ne 0) { throw 'Output-only successor scope mismatch' }
git diff HEAD^ HEAD --check
if ($LASTEXITCODE -ne 0) { throw 'Committed pair diff check failed' }
git status --short --branch
```

Expected: the recorded input HEAD is an ancestor; its only successor paths are `result.json` and `report.md`; final status is clean. All semantic/repository validation occurred against the same bytes before acceptance, while rollback was still available. Do not push or merge.

## Definition Of Done

This plan is complete only when:

- Creative Analysis Engine is pinned to the exact private `dev` revision and seven-file equivalence scope while source adaptation remains false;
- exactly two ordered public dataset manifests and their exact local SHA-256/quality inventories are tracked;
- raw public bytes remain ignored and no raw transcript/audio content is tracked;
- CREMA-D labels remain perceived acted-emotion source labels and AMI remains non-emotion conversational mechanics;
- split v1 remains readable and v2 represents all seven dependency dimensions, covering rules, advisory limits, and fail-closed quarantine;
- the synthetic cohort gate proves 5-speaker discovery, 10-speaker aggregate suppression/release, per-cell suppression, one-record contribution cap, and separate 30/30 confirmatory floors for every promoted label without adding identity fields to `OperationalAggregateV1`;
- exact changed bytes, dependency closure, command ledger, and guard policy are bound without output self-reference;
- child processes receive no provider credentials and deny network/private-path access during the captured verification window;
- the existing crash-safe, two-file publication/recovery protocol and exact report hash marker remain intact;
- all runtime/provider/private/call/simulation/adaptation flags remain false;
- `phase_a_complete=true` means only `source_provenance_dataset_manifests_offline_contracts_and_cohort_release_gate_only`;
- dataset evaluation, acoustic implementation, operational-signal accuracy, customer true emotion, live aggregate release, public-dataset performance, real calls, PSTN, ASR, streaming, latency, provider feasibility, production readiness, source adaptation, shadow use, and runtime activation remain unproven and unauthorized;
- final branch status is clean with no push or merge.

## Execution Handoff

Plan execution has two supported modes:

1. **Subagent-Driven (recommended):** dispatch a fresh worker for each task with spec-compliance and code-quality review between tasks. Stop at Task 8 for the separate dataset-download authorization.
2. **Inline Execution:** execute task-by-task in this session with explicit checkpoints. Stop at Task 8 for the same authorization.

Neither option itself authorizes implementation or public-dataset download.
