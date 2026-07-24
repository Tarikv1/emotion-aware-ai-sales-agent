# EMOTION-STATE-002 Offline Phase B Public-Data Feasibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a fail-closed offline research checkpoint that tests a frozen
17-feature classical acoustic model against CREMA-D's concordant original
audio-perception labels and separately releases privacy-minimized AMI
conversational-mechanics aggregates.

**Architecture:** Two row-isolated research lanes share only a final aggregate
result/report transaction. CREMA-D uses pinned real-schema label evidence,
speaker-disjoint partitions, deterministic acoustic features, two baselines,
and one L2 multinomial logistic-regression model. AMI uses only selected manual
annotations to derive contribution-limited mechanics; neither lane can create
customer-state evidence or influence runtime.

**Tech Stack:** Python 3.11, standard-library `csv`, `json`, `wave`, and
`xml.etree.ElementTree`; reviewed and hash-locked NumPy, SciPy, and
scikit-learn distributions in an ignored research-only virtual environment;
standard-library `unittest`.

## Cut 4B Active Overlay (2026-07-22)

- `emotion_state_phase_b_feature_v2.schema.json` supersedes v1 for every new
  production execution; v1 remains unchanged historical authority only.
- The unchanged config field value
  `emotion-state-crema-interpretable-acoustic-v1` is a legacy seed-lineage
  compatibility token, not an active selector. The exact config identities,
  actor assignment, and model seed `618797162` remain frozen; the fixed v2 path
  and its static/semantic identities are the exclusive active authority. The
  review correction cross-binds that tuple at every composition and replay
  boundary.
- The corrected production lineage root is exactly
  `.tmp/emotion-state-002-phase-b-cut4b`. The retired
  `.tmp/emotion-state-002-phase-b` split, preflight, and non-lockbox lineage is
  opaque and must not be parsed, reused, recovered, deleted, or mutated.
- The old `.tmp/emotion-state-002-phase-b/venv` and
  `.tmp/emotion-state-002-phase-b/dependencies/wheelhouse` remain immutable
  dependency inputs. Command executables continue to use that venv.
- At most one fresh replacement preflight/non-lockbox attempt may be issued
  after Cut 4B implementation and independent review. No fallback, cleanup,
  retry, or migration is implicit.
- Task 10 review remains aggregate-only. Final-lockbox access, canonical
  staging or acceptance, runtime activation, push, merge, and Phase C remain
  blocked under their separate gates.

## Global Constraints

- Implementation base:
  `e5049cf5a169cbd6887e451a1e00348fe7d1b868`.
- Approved design:
  `docs/superpowers/specs/2026-07-19-emotion-state-phase-b-public-data-feasibility-design.md`.
- Checkpoint ID:
  `EMOTION-STATE-002-phase-b-public-data-feasibility`.
- Phase A result SHA-256:
  `EED96BADBE916A38107A4289AD951F8953A5A96215E063890E07F054C7A90931`.
- Phase A report SHA-256:
  `724C81C41C489B9BBAB0896009DE7CAB578F77082F230F78B90B65643586FE8A`.
- CREMA-D manifest, hash inventory, and quality inventory SHA-256 values remain
  `6E86F06358E4AD172C72BE1692CFF37291D9D5763DD7F6F5C7CE7405E7E01248`,
  `AD58D8165C683847DF246F923FF466722C7F628FE8D81679F618FA5EB3031C87`,
  and
  `455D6A010855F209B4DC4C67F67E4222FAB81601861745B5B5E79E7942B92682`.
- `finishedResponses.csv` and `processedResults/summaryTable.csv` must match
  SHA-256
  `939D02D2DDDDDF575BBCCFFB80F14F1D110FDA88F092F2A68201994EB3BCB45B`
  and
  `1EA0E13D98853D920C7C51E69A72BA5BA42018F85A9B89B8B2CC1B53C1AA56A9`.
- CREMA-D preflight must reproduce exactly `6570` eligible rows, `644`
  released `VoiceVote` ties, `204` additional raw audio-vote ties, and `23`
  unique-winner disagreements across all `91` actors and `12` sentences.
- Frozen eligible label counts are `A=951`, `D=500`, `F=613`, `H=330`,
  `N=3834`, and `S=342`.
- Filename emotion intent, actor prompt, path, clip stem, actor, sentence,
  votes, label, and any derived proxy are forbidden acoustic-model features.
- The ordered acoustic vector contains exactly the 17 features in the approved
  design; no MFCC, embedding, pretrained model, demographic field, transcript
  semantic, per-speaker normalization, or imputation is allowed.
- Actor allocation is exactly `35/13/13/30` for
  `training_discovery/calibration/balanced_diagnostic/final_lockbox`.
- The final lockbox opens once only after every configuration, environment,
  split, metric, slice, bootstrap, and renderer digest is frozen.
- AMI emits mechanics only and never an emotion, operational signal, customer
  state, or row-level join with CREMA-D.
- No task may create `PatternCandidateV1`, populate
  `PerceivedCustomerStateV1`, or produce persuasion/runtime input.
- Every published metric cell requires at least ten proven unique actors or
  participants; otherwise it is suppressed.
- Tracked output is exactly
  `research/experiments/generated/EMOTION-STATE-002-phase-b-public-data-feasibility/result.json`
  and `report.md`.
- No tracked artifact may contain rows, filenames, paths, identifiers,
  transcript text, audio, probabilities, fitted objects, timestamps,
  credentials, or operational-signal labels.
- No implementation task may read `data/private/` or
  `data/private-restricted/`, import `runtime/`, call a provider, place a call,
  run a simulation, perform source adaptation or adapt the friend source,
  change prompts/KB/voice/LLM/phone settings, push, merge, rewrite history, or
  claim production readiness.
- The current authorization covers this plan only. Execution must respect the
  boundary gates below.

## Boundary Gates

1. **Offline implementation gate:** Tasks 1, 2, 4, 5, 6, 7, 8, and 9 edit
   tracked research code/docs and run only synthetic or tracked-metadata tests.
   They require a later implementation authorization.
2. **Dependency gate:** Task 3 may access the package index and download wheels
   only through `.tmp/emotion-state-002-phase-b/resolver-venv/`, then install
   the reviewed wheels into the pip-free evaluation environment at
   `.tmp/emotion-state-002-phase-b/venv/`. Both environments remain ignored
   under the fixed Phase B root. This requires explicit
   network/download/install authority and a reviewed artifact lock.
3. **Public-material gate:** Task 10 may read the two public CREMA CSVs, CREMA
   WAVs, and selected AMI annotation files from their fixed ignored roots. It
   requires explicit public-material evaluation authority.
4. **Final-lockbox gate:** Task 11 completed exactly once under its explicit
   one-use authorization and is now closed. It must not be rerun for this
   experiment version.
5. **Publication gate:** Task 12 may stage, independently validate, explicitly
   accept, commit, and optionally push the exact canonical pair only under
   separately stated acceptance/push authority.

No gate implicitly grants the next gate.

## File Responsibility Map

### Tracked additions

- `research/environments/emotion-state-002/requirements.lock`
  records exact package names, versions, licenses, wheel filenames, and
  SHA-256 values.
- `research/experiments/EMOTION-STATE-002-phase-b-public-data-feasibility.md`
  records the experiment question, frozen protocol, execution state, and
  readiness boundary.
- `research/experiments/cases/emotion-state-002-phase-b-config.json`
  is the sole frozen experiment configuration.
- `research/sources/emotion_state/emotion_state_phase_b_feature_v1.schema.json`
  freezes acoustic preprocessing and ordered feature names.
- `research/sources/emotion_state/emotion_state_evaluation_split_v1.schema.json`
  freezes claim-scoped dependency roles and partition invariants.
- `scripts/emotion_state_phase_b_features.py`
  validates PCM input and extracts the exact 17 acoustic features.
- `scripts/emotion_state_phase_b_splits.py`
  creates and validates deterministic actor-disjoint assignments.
- `scripts/emotion_state_phase_b_evaluation.py`
  parses the real CREMA-D label schemas, trains the three frozen comparisons,
  calculates metrics/bootstrap intervals, and applies the decision contract.
- `scripts/emotion_state_phase_b_ami_mechanics.py`
  parses selected AMI manual annotations and calculates contribution-limited
  mechanics.
- `scripts/run_emotion_state_002_phase_b.py`
  owns phase transitions, ignored local state, lockbox accounting, rendering,
  and crash-safe staged publication.
- `scripts/validate_emotion_state_002_phase_b.py`
  validates source/config/environment/result/report bytes and boundary scans.
- `scripts/test_emotion_state_002_phase_b.py`
  contains all focused synthetic, mutation, transaction, and boundary tests.

### Tracked modifications

- `docs/product/COMMANDS.md` adds exact Phase B commands and gates.
- `docs/product/CHECKPOINT_INDEX.md` records the checkpoint and bounded claim.
- `docs/thesis/DECISION_LOG.md` records executed decisions only.
- `docs/thesis/METHODOLOGY_LOG.md` records tests, failures, corrections, and
  final evidence.
- `docs/thesis/ROADMAP.md` tracks the current gate.
- `research/experiments/EMOTION-STATE-001-phase-a.md` remains unchanged unless
  a verified Phase A statement becomes factually stale.

### Ignored local state

All row-level or fitted state lives under:

```text
.tmp/emotion-state-002-phase-b/
```

The runner must reject any local-state path outside that root.

---

### Task 1: Freeze configuration and schema contracts

**Files:**
- Create:
  `research/experiments/cases/emotion-state-002-phase-b-config.json`
- Create:
  `research/sources/emotion_state/emotion_state_phase_b_feature_v1.schema.json`
- Create:
  `research/sources/emotion_state/emotion_state_evaluation_split_v1.schema.json`
- Create:
  `research/experiments/EMOTION-STATE-002-phase-b-public-data-feasibility.md`
- Create: `scripts/validate_emotion_state_002_phase_b.py`
- Create: `scripts/test_emotion_state_002_phase_b.py`
- Modify:
  `docs/superpowers/plans/2026-07-19-emotion-state-phase-b-public-data-feasibility.md`
- Modify: `docs/thesis/METHODOLOGY_LOG.md`

**Interfaces:**
- Consumes: the corrected design and immutable hashes in Global Constraints.
- Produces:
  `load_json_strict(path: Path) -> dict[str, Any]`,
  `validate_config(payload: Any) -> dict[str, Any]`,
  `validate_feature_schema(payload: Any) -> dict[str, Any]`, and
  `validate_split_schema(payload: Any) -> dict[str, Any]`.

- [ ] **Step 1: Write failing contract tests**

Add the imports, path constants, and test class below to
`scripts/test_emotion_state_002_phase_b.py`:

```python
from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "research/experiments/cases/emotion-state-002-phase-b-config.json"
FEATURE_SCHEMA = (
    ROOT
    / "research/sources/emotion_state/emotion_state_phase_b_feature_v1.schema.json"
)
SPLIT_SCHEMA = (
    ROOT
    / "research/sources/emotion_state/emotion_state_evaluation_split_v1.schema.json"
)


class PhaseBContractTests(unittest.TestCase):
    def test_frozen_contracts_validate(self) -> None:
        from scripts.validate_emotion_state_002_phase_b import (
            load_json_strict,
            validate_config,
            validate_feature_schema,
            validate_split_schema,
        )

        config = validate_config(load_json_strict(CONFIG))
        feature = validate_feature_schema(load_json_strict(FEATURE_SCHEMA))
        split = validate_split_schema(load_json_strict(SPLIT_SCHEMA))
        self.assertEqual(config["checkpoint_id"], "EMOTION-STATE-002-phase-b-public-data-feasibility")
        self.assertEqual(len(feature["ordered_features"]), 17)
        self.assertEqual(split["partition_actor_counts"], {
            "training_discovery": 35,
            "calibration": 13,
            "balanced_diagnostic": 13,
            "final_lockbox": 30,
        })

    def test_contract_mutations_fail_closed(self) -> None:
        from scripts.validate_emotion_state_002_phase_b import (
            load_json_strict,
            validate_config,
            validate_feature_schema,
        )

        feature = load_json_strict(FEATURE_SCHEMA)
        mutated = deepcopy(feature)
        mutated["ordered_features"].append("filename")
        with self.assertRaisesRegex(ValueError, "ordered acoustic features"):
            validate_feature_schema(mutated)

        config = load_json_strict(CONFIG)
        mutated = deepcopy(config)
        mutated["boundaries"]["runtime_influence_allowed"] = True
        with self.assertRaisesRegex(ValueError, "runtime influence"):
            validate_config(mutated)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests and confirm RED**

Run:

```powershell
python -m unittest scripts.test_emotion_state_002_phase_b.PhaseBContractTests -v
```

Expected: import or missing-file errors for the Phase B validator/contracts.

- [ ] **Step 3: Create the exact feature schema**

Create
`research/sources/emotion_state/emotion_state_phase_b_feature_v1.schema.json`
with:

```json
{
  "schema_id": "emotion-state-crema-interpretable-acoustic-v1",
  "schema_version": 1,
  "sample_rate_hz": 16000,
  "sample_width_bytes": 2,
  "channel_count": 1,
  "window_ms": 25,
  "hop_ms": 10,
  "window": "hann_periodic",
  "silence_floor_dbfs": -50.0,
  "silence_relative_to_peak_db": -40.0,
  "f0_min_hz": 75.0,
  "f0_max_hz": 400.0,
  "voiced_autocorrelation_threshold": 0.3,
  "minimum_voiced_frames": 3,
  "spectral_rolloff_fraction": 0.85,
  "percentile_method": "linear",
  "ordered_features": [
    "duration_seconds",
    "silence_ratio",
    "voiced_fraction",
    "f0_median_hz",
    "f0_iqr_hz",
    "f0_range_hz",
    "rms_dbfs_mean",
    "rms_dbfs_std",
    "rms_dbfs_p90_minus_p10",
    "zero_crossing_rate_mean",
    "zero_crossing_rate_std",
    "spectral_centroid_hz_mean",
    "spectral_centroid_hz_std",
    "spectral_bandwidth_hz_mean",
    "spectral_bandwidth_hz_std",
    "spectral_rolloff_85_hz_mean",
    "spectral_rolloff_85_hz_std"
  ],
  "imputation_allowed": false,
  "runtime_influence_allowed": false
}
```

- [ ] **Step 4: Create the exact split schema**

Create
`research/sources/emotion_state/emotion_state_evaluation_split_v1.schema.json`
with:

```json
{
  "schema_id": "emotion-state-evaluation-split-v1",
  "schema_version": 1,
  "dataset_id": "crema-d-v1.0-audio-wav",
  "dependency_roles": {
    "speaker": "exclusion_group",
    "scripted_scenario": "stratification_factor",
    "source_corpus": "scope_constant",
    "call_session": "covered_by_higher_dependency",
    "recording_site": "advisory_unavailable",
    "meeting_series": "not_applicable",
    "dialogue_dyad": "not_applicable"
  },
  "covering_dependencies": {
    "call_session": "speaker"
  },
  "partition_order": [
    "training_discovery",
    "calibration",
    "balanced_diagnostic",
    "final_lockbox"
  ],
  "partition_actor_counts": {
    "training_discovery": 35,
    "calibration": 13,
    "balanced_diagnostic": 13,
    "final_lockbox": 30
  },
  "expected_actor_count": 91,
  "expected_sentence_count": 12,
  "unseen_sentence_claim_allowed": false,
  "recording_site_generalization_allowed": false,
  "runtime_influence_allowed": false
}
```

- [ ] **Step 5: Create the frozen experiment configuration**

Create
`research/experiments/cases/emotion-state-002-phase-b-config.json` with these
exact top-level fields and values:

```json
{
  "checkpoint_id": "EMOTION-STATE-002-phase-b-public-data-feasibility",
  "schema_version": 1,
  "implementation_base_commit": "e5049cf5a169cbd6887e451a1e00348fe7d1b868",
  "source_label": "public-only",
  "feature_schema_id": "emotion-state-crema-interpretable-acoustic-v1",
  "split_schema_id": "emotion-state-evaluation-split-v1",
  "crema_label_contract": {
    "finished_responses_sha256": "939D02D2DDDDDF575BBCCFFB80F14F1D110FDA88F092F2A68201994EB3BCB45B",
    "summary_table_sha256": "1EA0E13D98853D920C7C51E69A72BA5BA42018F85A9B89B8B2CC1B53C1AA56A9",
    "raw_join_field": "clipName",
    "raw_modality_field": "queryType",
    "raw_audio_modality": "1",
    "raw_label_field": "respEmo",
    "summary_join_field": "FileName",
    "summary_label_field": "VoiceVote",
    "expected_status_counts": {
      "eligible_concordant_unique_winner": 6570,
      "summary_voice_tie": 644,
      "raw_audio_vote_tie": 204,
      "unique_winner_disagreement": 23
    },
    "expected_label_counts": {
      "A": 951,
      "D": 500,
      "F": 613,
      "H": 330,
      "N": 3834,
      "S": 342
    }
  },
  "model": {
    "regularization": "l2",
    "C": 1.0,
    "class_weight": null,
    "maximum_iterations": 10000,
    "solver": "lbfgs",
    "hyperparameter_search_allowed": false
  },
  "coverage_targets": [1.0, 0.8, 0.6],
  "ece_equal_width_bin_count": 10,
  "bootstrap_resamples": 2000,
  "minimum_unique_contributors_per_cell": 10,
  "ami_partitions": [
    "scenario_only",
    "full_corpus",
    "full_only"
  ],
  "boundaries": {
    "private_data_allowed": false,
    "provider_operations_allowed": false,
    "network_during_evaluation_allowed": false,
    "source_adaptation_allowed": false,
    "runtime_influence_allowed": false,
    "customer_state_output_allowed": false
  }
}
```

- [ ] **Step 6: Implement strict contract validation**

Create `scripts/validate_emotion_state_002_phase_b.py` with strict duplicate-key
and non-finite JSON rejection. The first implementation must expose:

```python
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

FEATURE_NAMES = (
    "duration_seconds", "silence_ratio", "voiced_fraction", "f0_median_hz",
    "f0_iqr_hz", "f0_range_hz", "rms_dbfs_mean", "rms_dbfs_std",
    "rms_dbfs_p90_minus_p10", "zero_crossing_rate_mean",
    "zero_crossing_rate_std", "spectral_centroid_hz_mean",
    "spectral_centroid_hz_std", "spectral_bandwidth_hz_mean",
    "spectral_bandwidth_hz_std", "spectral_rolloff_85_hz_mean",
    "spectral_rolloff_85_hz_std",
)
PARTITION_COUNTS = {
    "training_discovery": 35,
    "calibration": 13,
    "balanced_diagnostic": 13,
    "final_lockbox": 30,
}


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


def load_json_strict(path: Path) -> dict[str, Any]:
    value = json.loads(
        Path(path).read_text(encoding="utf-8"),
        object_pairs_hook=_pairs,
        parse_constant=_constant,
    )
    if not isinstance(value, dict):
        raise ValueError("JSON root must be an object")
    return value


def validate_feature_schema(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("feature schema must be an object")
    if tuple(payload.get("ordered_features", ())) != FEATURE_NAMES:
        raise ValueError("ordered acoustic features do not match")
    if payload.get("schema_id") != "emotion-state-crema-interpretable-acoustic-v1":
        raise ValueError("feature schema identity does not match")
    if payload.get("imputation_allowed") is not False:
        raise ValueError("feature imputation must remain disabled")
    if payload.get("runtime_influence_allowed") is not False:
        raise ValueError("runtime influence must remain disabled")
    return payload


def validate_split_schema(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("split schema must be an object")
    if payload.get("partition_actor_counts") != PARTITION_COUNTS:
        raise ValueError("partition actor counts do not match")
    if sum(PARTITION_COUNTS.values()) != 91:
        raise ValueError("partition actor counts do not cover 91 actors")
    if payload.get("dependency_roles", {}).get("speaker") != "exclusion_group":
        raise ValueError("speaker must remain the exclusion group")
    if payload.get("dependency_roles", {}).get("source_corpus") != "scope_constant":
        raise ValueError("source corpus must remain a scope constant")
    if payload.get("runtime_influence_allowed") is not False:
        raise ValueError("runtime influence must remain disabled")
    return payload


def validate_config(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("config must be an object")
    if payload.get("checkpoint_id") != "EMOTION-STATE-002-phase-b-public-data-feasibility":
        raise ValueError("checkpoint identity does not match")
    boundaries = payload.get("boundaries")
    if not isinstance(boundaries, dict) or any(value is not False for value in boundaries.values()):
        raise ValueError("runtime influence and every external boundary must remain disabled")
    if payload.get("bootstrap_resamples") != 2000:
        raise ValueError("bootstrap resample count does not match")
    if payload.get("coverage_targets") != [1.0, 0.8, 0.6]:
        raise ValueError("coverage targets do not match")
    return payload
```

- [ ] **Step 7: Create the experiment protocol document**

Create
`research/experiments/EMOTION-STATE-002-phase-b-public-data-feasibility.md`
with status `offline implementation started; dependency/public-material/model
execution not started`,
the exact question/claim boundary from the design, the five Boundary Gates,
the corrected `6570/644/204/23` label ledger, and a statement that a valid
negative result completes the experiment.

- [ ] **Step 8: Run focused and repository contract checks**

Run:

```powershell
python -m unittest scripts.test_emotion_state_002_phase_b.PhaseBContractTests -v
python scripts/validate_emotion_state_002_phase_b.py
python scripts/check_thesis_update_gate.py
python scripts/validate_project_drift_guard.py
git diff --check
```

Expected: every command exits `0`; focused tests report `OK`; validators report
pass and no network calls.

- [ ] **Step 9: Commit Task 1**

```powershell
git add -- research/experiments/cases/emotion-state-002-phase-b-config.json research/sources/emotion_state/emotion_state_phase_b_feature_v1.schema.json research/sources/emotion_state/emotion_state_evaluation_split_v1.schema.json research/experiments/EMOTION-STATE-002-phase-b-public-data-feasibility.md scripts/validate_emotion_state_002_phase_b.py scripts/test_emotion_state_002_phase_b.py docs/superpowers/plans/2026-07-19-emotion-state-phase-b-public-data-feasibility.md docs/thesis/METHODOLOGY_LOG.md
git diff --cached --check
git commit -m "Add EMOTION-STATE Phase B frozen contracts"
```

### Task 2: Implement the real-schema CREMA-D reference-label ledger

**Files:**
- Create: `scripts/emotion_state_phase_b_evaluation.py`
- Modify: `scripts/test_emotion_state_002_phase_b.py`
- Modify: `scripts/validate_emotion_state_002_phase_b.py`

**Interfaces:**
- Consumes: exact CSV paths, included hash-inventory clip stems, and the
  `crema_label_contract` config.
- Produces:
  `load_crema_reference_labels(finished_path: Path, summary_path: Path,
  included_clip_stems: Collection[str]) -> tuple[tuple[CremaLabelRecord, ...],
  dict[str, Any]]`.
- `CremaLabelRecord` is an immutable local-only dataclass with
  `clip_stem`, `actor_id`, `sentence_id`, `label`, `abstention_reason`,
  `vote_distribution`, `vote_agreement`, and `vote_entropy`.

- [ ] **Step 1: Write failing real-schema and abstention tests**

Add synthetic fixtures with the exact real headers:

```python
class CremaReferenceLabelTests(unittest.TestCase):
    def _write_sources(self, root: Path) -> tuple[Path, Path]:
        finished = root / "finishedResponses.csv"
        summary = root / "summaryTable.csv"
        finished.write_text(
            ",localid,pos,ans,ttr,queryType,numTries,clipNum,questNum,"
            "subType,clipName,sessionNums,respEmo,respLevel,dispEmo,"
            "dispVal,dispLevel\n"
            "1,r1,1,A_80,1,1,0,1,1,4,1001_DFA_ANG_XX,s1,A,80,A,50,X\n"
            "2,r2,1,A_70,1,1,0,1,1,4,1001_DFA_ANG_XX,s2,A,70,A,50,X\n"
            "3,r3,1,N_60,1,1,0,1,1,4,1001_DFA_ANG_XX,s3,N,60,A,50,X\n"
            "4,r1,1,A_80,1,1,0,2,1,4,1002_IEO_HAP_HI,s1,A,80,H,80,H\n"
            "5,r2,1,H_80,1,1,0,2,1,4,1002_IEO_HAP_HI,s2,H,80,H,80,H\n"
            "6,r1,1,S_80,1,1,0,3,1,4,1003_TAI_FEA_XX,s1,S,80,F,50,X\n",
            encoding="utf-8",
        )
        summary.write_text(
            ",FileName,VoiceVote,VoiceLevel,FaceVote,FaceLevel,"
            "MultiModalVote,MultiModalLevel\n"
            "1,1001_DFA_ANG_XX,A,75,A,75,A,75\n"
            "2,1002_IEO_HAP_HI,H,80,H,80,H,80\n"
            "3,1003_TAI_FEA_XX,F,80,F,80,F,80\n",
            encoding="utf-8",
        )
        return finished, summary

    def test_concordant_unique_winner_is_eligible(self) -> None:
        from scripts.emotion_state_phase_b_evaluation import (
            load_crema_reference_labels,
        )

        with tempfile.TemporaryDirectory() as directory:
            finished, summary = self._write_sources(Path(directory))
            rows, ledger = load_crema_reference_labels(
                finished, summary,
                {"1001_DFA_ANG_XX", "1002_IEO_HAP_HI", "1003_TAI_FEA_XX"},
            )
        by_stem = {row.clip_stem: row for row in rows}
        self.assertEqual(by_stem["1001_DFA_ANG_XX"].label, "A")
        self.assertEqual(
            by_stem["1002_IEO_HAP_HI"].abstention_reason,
            "raw_audio_vote_tie",
        )
        self.assertEqual(
            by_stem["1003_TAI_FEA_XX"].abstention_reason,
            "unique_winner_disagreement",
        )
        self.assertEqual(ledger["eligible_concordant_unique_winner"], 1)

    def test_released_tie_and_filename_intent_abstain(self) -> None:
        from scripts.emotion_state_phase_b_evaluation import (
            load_crema_reference_labels,
        )

        with tempfile.TemporaryDirectory() as directory:
            finished, summary = self._write_sources(Path(directory))
            text = summary.read_text(encoding="utf-8").replace(
                "1001_DFA_ANG_XX,A,75", "1001_DFA_ANG_XX,A:N,75"
            )
            summary.write_text(text, encoding="utf-8")
            rows, _ = load_crema_reference_labels(
                finished, summary, {"1001_DFA_ANG_XX"}
            )
        self.assertIsNone(rows[0].label)
        self.assertEqual(rows[0].abstention_reason, "summary_voice_tie")
        self.assertNotEqual(rows[0].label, "ANG")
```

- [ ] **Step 2: Run the tests and confirm RED**

Run:

```powershell
python -m unittest scripts.test_emotion_state_002_phase_b.CremaReferenceLabelTests -v
```

Expected: FAIL because `emotion_state_phase_b_evaluation` is absent.

- [ ] **Step 3: Implement the strict label reader**

Create `scripts/emotion_state_phase_b_evaluation.py` with:

```python
from __future__ import annotations

import csv
import math
import re
from collections import Counter, defaultdict
from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path
from typing import Any

LABELS = frozenset({"A", "D", "F", "H", "N", "S"})
CLIP_PATTERN = re.compile(
    r"^(?P<actor>\d{4})_(?P<sentence>[A-Z0-9]{3})_"
    r"(?:ANG|DIS|FEA|HAP|NEU|SAD)_(?:HI|LO|MD|XX)$"
)


@dataclass(frozen=True)
class CremaLabelRecord:
    clip_stem: str
    actor_id: str
    sentence_id: str
    label: str | None
    abstention_reason: str | None
    vote_distribution: tuple[tuple[str, int], ...]
    vote_agreement: float | None
    vote_entropy: float | None


def _rows(path: Path, required: tuple[str, ...]) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or tuple(reader.fieldnames) != required:
            raise ValueError(f"unexpected CSV schema: {path.name}")
        return [
            {key: (value or "").strip() for key, value in row.items()}
            for row in reader
        ]


def _winners(distribution: Counter[str]) -> tuple[str, ...]:
    maximum = max(distribution.values(), default=0)
    return tuple(sorted(
        label for label, count in distribution.items()
        if count == maximum and maximum > 0
    ))


def _entropy(distribution: Counter[str]) -> float | None:
    total = sum(distribution.values())
    if total == 0:
        return None
    return -sum(
        (count / total) * math.log2(count / total)
        for count in distribution.values()
        if count
    )


def load_crema_reference_labels(
    finished_path: Path,
    summary_path: Path,
    included_clip_stems: Collection[str],
) -> tuple[tuple[CremaLabelRecord, ...], dict[str, Any]]:
    finished_header = (
        "", "localid", "pos", "ans", "ttr", "queryType", "numTries",
        "clipNum", "questNum", "subType", "clipName", "sessionNums",
        "respEmo", "respLevel", "dispEmo", "dispVal", "dispLevel",
    )
    summary_header = (
        "", "FileName", "VoiceVote", "VoiceLevel", "FaceVote", "FaceLevel",
        "MultiModalVote", "MultiModalLevel",
    )
    raw_groups: dict[str, Counter[str]] = defaultdict(Counter)
    for row in _rows(finished_path, finished_header):
        if row["queryType"] != "1":
            continue
        if row["respEmo"] not in LABELS:
            raise ValueError("invalid raw audio-perception label")
        raw_groups[row["clipName"]][row["respEmo"]] += 1

    released: dict[str, tuple[str, ...]] = {}
    for row in _rows(summary_path, summary_header):
        stem = row["FileName"]
        if stem in released:
            raise ValueError("duplicate summary clip")
        values = tuple(sorted(row["VoiceVote"].split(":")))
        if not values or len(values) != len(set(values)) or any(
            value not in LABELS for value in values
        ):
            raise ValueError("invalid released VoiceVote")
        released[stem] = values

    records: list[CremaLabelRecord] = []
    ledger: Counter[str] = Counter()
    label_counts: Counter[str] = Counter()
    for stem in sorted(set(included_clip_stems)):
        match = CLIP_PATTERN.fullmatch(stem)
        if match is None:
            raise ValueError("invalid included CREMA-D clip stem")
        if stem not in raw_groups or stem not in released:
            raise ValueError("missing CREMA-D reference-label join")
        distribution = raw_groups[stem]
        raw = _winners(distribution)
        summary = released[stem]
        if len(summary) != 1:
            reason, label = "summary_voice_tie", None
        elif len(raw) != 1:
            reason, label = "raw_audio_vote_tie", None
        elif raw != summary:
            reason, label = "unique_winner_disagreement", None
        else:
            reason, label = None, raw[0]
            ledger["eligible_concordant_unique_winner"] += 1
            label_counts[label] += 1
        if reason is not None:
            ledger[reason] += 1
        total = sum(distribution.values())
        records.append(CremaLabelRecord(
            clip_stem=stem,
            actor_id=match.group("actor"),
            sentence_id=match.group("sentence"),
            label=label,
            abstention_reason=reason,
            vote_distribution=tuple(sorted(distribution.items())),
            vote_agreement=max(distribution.values()) / total,
            vote_entropy=_entropy(distribution),
        ))
    result = dict(sorted(ledger.items()))
    result["label_counts"] = dict(sorted(label_counts.items()))
    eligible = tuple(record for record in records if record.label is not None)
    result["included_wav_count"] = len(records)
    result["eligible_actor_count"] = len({record.actor_id for record in eligible})
    result["eligible_sentence_count"] = len({
        record.sentence_id for record in eligible
    })
    return tuple(records), result
```

- [ ] **Step 4: Add frozen-ledger and hash-binding validation**

Extend the validator with
`validate_crema_label_ledger(ledger: Any, config: Mapping[str, Any]) -> None`.
It must compare exact status/label dictionaries, sum to `7441`, and require
`91` actors and `12` sentences from aggregate preflight metadata. Add mutation
tests for every count, field name, modality value, duplicate key, invalid
label, and missing join.

- [ ] **Step 5: Run focused tests**

```powershell
python -m unittest scripts.test_emotion_state_002_phase_b.CremaReferenceLabelTests -v
python -m unittest scripts.test_emotion_state_002_phase_b.PhaseBContractTests -v
git diff --check
```

Expected: all tests pass; no public-material path is used by the tests.

- [ ] **Step 6: Commit Task 2**

```powershell
git add -- scripts/emotion_state_phase_b_evaluation.py scripts/test_emotion_state_002_phase_b.py scripts/validate_emotion_state_002_phase_b.py
git diff --cached --check
git commit -m "Add Phase B CREMA-D reference-label ledger"
```

### Task 3: Review and lock the isolated research environment

**Files:**
- Create: `research/environments/emotion-state-002/requirements.lock`
- Modify: `scripts/test_emotion_state_002_phase_b.py`
- Modify: `scripts/validate_emotion_state_002_phase_b.py`

**Interfaces:**
- Consumes: a separately authorized package-index resolver report and wheelhouse
  under `.tmp/emotion-state-002-phase-b/dependencies/`.
- Produces:
  `validate_environment_lock(payload: Any) -> dict[str, Any]` and an exact
  JSON lock containing every direct and transitive distribution.

- [ ] **Step 1: Stop at the dependency authorization gate**

Do not run any command in the remaining Task 3 steps until network, wheel
download, and ignored-venv installation are explicitly authorized.

- [ ] **Step 2: Create isolated resolver and evaluation environments**

Run only after authorization:

```powershell
py -3.11 -m venv .tmp/emotion-state-002-phase-b/resolver-venv
.tmp/emotion-state-002-phase-b/resolver-venv/Scripts/python.exe -m pip --version
py -3.11 -m venv --without-pip .tmp/emotion-state-002-phase-b/venv
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe -c "import sys; print(sys.version); print(sys.executable)"
```

Expected: both interpreters report `3.11`; both paths remain under the ignored
Phase B root; only the resolver environment contains bootstrap tooling. The
fixed evaluation environment contains no `pip`, `setuptools`, or other
distribution before reviewed-wheel installation.

- [ ] **Step 3: Resolve binary distributions into an ignored wheelhouse**

Run with provider credentials removed from the child environment:

```powershell
.tmp/emotion-state-002-phase-b/resolver-venv/Scripts/python.exe -m pip download --only-binary=:all: --dest .tmp/emotion-state-002-phase-b/dependencies/wheelhouse "numpy>=2.4,<2.5" "scipy>=1.16,<1.18" "scikit-learn>=1.8,<1.9"
```

Expected: only NumPy, SciPy, scikit-learn, and resolver-required transitive
wheels appear. Abort on a source archive, prerelease, unexpected package, or
artifact outside the ignored wheelhouse.

- [ ] **Step 4: Review versions, licenses, filenames, and hashes**

For each wheel, run:

```powershell
Get-ChildItem -LiteralPath .tmp/emotion-state-002-phase-b/dependencies/wheelhouse -File | Sort-Object Name | Get-FileHash -Algorithm SHA256
```

Inspect each wheel's `METADATA` and license files without executing package
code. Reject any artifact whose license is incompatible with thesis research,
whose metadata name/version differs from its wheel filename, or whose
dependency graph is incomplete.

- [ ] **Step 5: Write the exact JSON environment lock**

Use `apply_patch` to create
`research/environments/emotion-state-002/requirements.lock` as a JSON object
with:

```json
{
  "schema_id": "emotion-state-002-research-environment-lock-v1",
  "python_version": "3.11",
  "platform": "win_amd64",
  "direct_requirements": [
    "numpy",
    "scipy",
    "scikit-learn"
  ],
  "distributions": [],
  "network_during_evaluation_allowed": false,
  "product_dependency_manifest_influence_allowed": false
}
```

Before committing, replace the empty `distributions` array with one
lexicographically sorted object per reviewed wheel. Each object must contain
exact `name`, `version`, `direct`, `wheel_filename`, uppercase `sha256`, and
SPDX-style `license` values derived from the reviewed artifacts. The validator
must reject an empty array, so the shown pre-review form can never pass or be
committed.

- [ ] **Step 6: Install only the reviewed wheel filenames without network**

```powershell
.tmp/emotion-state-002-phase-b/resolver-venv/Scripts/python.exe -m pip --python .tmp/emotion-state-002-phase-b/venv/Scripts/python.exe install --no-index --no-deps .tmp/emotion-state-002-phase-b/dependencies/wheelhouse/joblib-1.5.3-py3-none-any.whl .tmp/emotion-state-002-phase-b/dependencies/wheelhouse/numpy-2.4.6-cp311-cp311-win_amd64.whl .tmp/emotion-state-002-phase-b/dependencies/wheelhouse/scikit_learn-1.8.0-cp311-cp311-win_amd64.whl .tmp/emotion-state-002-phase-b/dependencies/wheelhouse/scipy-1.17.1-cp311-cp311-win_amd64.whl .tmp/emotion-state-002-phase-b/dependencies/wheelhouse/threadpoolctl-3.6.0-py3-none-any.whl
.tmp/emotion-state-002-phase-b/resolver-venv/Scripts/python.exe -m pip --python .tmp/emotion-state-002-phase-b/venv/Scripts/python.exe check
```

Expected: installation succeeds entirely from the wheelhouse, `pip check`
reports no broken requirements through the resolver tooling, and evaluation
runtime distribution identity equals the five reviewed lock entries exactly.

- [ ] **Step 7: Add lock and runtime-identity tests**

Tests must prove that:

- every installed distribution/version equals the reviewed lock;
- every wheel hash equals the lock;
- direct dependencies are exactly NumPy, SciPy, and scikit-learn;
- the lock never enters a product/runtime manifest;
- evaluation refuses system Python, a missing lock, an extra distribution, or
  a version/hash mismatch;
- actual interpreter platform/architecture must match locked `win_amd64`;
- a missing, extra, or hash-mismatched wheel fails closed.

Run:

```powershell
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe -m unittest scripts.test_emotion_state_002_phase_b -v
.tmp/emotion-state-002-phase-b/resolver-venv/Scripts/python.exe -m pip --python .tmp/emotion-state-002-phase-b/venv/Scripts/python.exe check
```

Expected: all tests pass, resolver-side `pip check` reports no broken
requirements, and the environment identity report matches the lock. The
pip-free evaluation interpreter must never run `-m pip`.

- [ ] **Step 8: Commit Task 3**

```powershell
git add -- research/environments/emotion-state-002/requirements.lock scripts/test_emotion_state_002_phase_b.py scripts/validate_emotion_state_002_phase_b.py
git diff --cached --check
git commit -m "Lock Phase B research dependencies"
```

### Task 4: Implement deterministic acoustic feature extraction

**Files:**
- Create: `scripts/emotion_state_phase_b_features.py`
- Modify: `scripts/test_emotion_state_002_phase_b.py`
- Modify:
  `research/sources/emotion_state/emotion_state_phase_b_feature_v1.schema.json`
- Modify: `scripts/validate_emotion_state_002_phase_b.py`
- Modify:
  `docs/superpowers/plans/2026-07-19-emotion-state-phase-b-public-data-feasibility.md`

**Interfaces:**
- Consumes: one exact mono 16-bit PCM 16 kHz WAV path and the feature schema.
- Produces:
  `extract_acoustic_features(path: Path) -> dict[str, float]` and
  `feature_vector(row: Mapping[str, Any]) -> tuple[float, ...]`.
- Internal helpers are
  `_read_pcm16_mono_16khz(path: Path) -> np.ndarray`,
  `_frames(samples: np.ndarray, frame_size: int, hop_size: int) ->
  np.ndarray`, and
  `_summarize(frames: np.ndarray, sample_count: int, sample_rate: int) ->
  dict[str, float]`.
- Raises `FeatureExtractionError` for unsupported, silent, insufficient-voiced,
  or non-finite input.

- [ ] **Step 1: Write failing synthetic signal tests**

Add tests that create WAVs only in `TemporaryDirectory` and assert:

- a 200 Hz sine produces finite F0 near 200 Hz;
- amplitude scaling preserves duration/F0 and changes RMS;
- duration scaling changes duration but not F0;
- digital silence, near-silence with no nonsilent frame, fewer than three
  voiced frames, stereo, 8-bit, 44.1 kHz, malformed RIFF, and clipping reject;
- nonzero DC, deterministic unvoiced noise, and both clipping endpoints reject;
- mixed voiced, unvoiced, and silent frames freeze the duration, silence,
  voiced-fraction, F0 median, IQR, and range populations;
- exact analytical fixtures freeze the PCM16-aware RMS floor, population
  standard deviation, linear percentiles, ZCR, periodic-Hann power centroid,
  bandwidth, and discrete 85% rolloff;
- output keys equal the exact 17-feature order;
- every value is finite and repeated extraction is byte-deterministic after
  canonical JSON encoding.

The tone helper must use:

```python
@staticmethod
def _write_tone(path: Path, *, hz: float, seconds: float, amplitude: float) -> None:
    import math
    import struct
    import wave

    sample_rate = 16000
    count = int(sample_rate * seconds)
    samples = [
        max(-32768, min(32767, round(
            amplitude * 32767 * math.sin(2 * math.pi * hz * index / sample_rate)
        )))
        for index in range(count)
    ]
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(struct.pack("<" + "h" * len(samples), *samples))
```

- [ ] **Step 2: Run tests and confirm RED**

```powershell
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe -m unittest scripts.test_emotion_state_002_phase_b.AcousticFeatureTests -v
```

Expected: import failure for the missing feature module.

- [ ] **Step 3: Implement the exact extractor**

Implement these frozen operations in
`scripts/emotion_state_phase_b_features.py`:

1. Read with `wave`; require `1` channel, `2` bytes, `16000` Hz, positive
   frames, and no compression. Reject a sample stream containing either
   full-scale endpoint `-32768` or `32767` as clipped.
2. Normalize signed little-endian PCM by `32768.0`.
3. Use full 400-sample frames, 160-sample hop, and SciPy's periodic Hann
   window; do not pad.
4. Exact-zero frame RMS uses the linear floor
   `1 / (32768 * sqrt(400))`. RMS summaries use all complete frames and
   population standard deviation (`ddof=0`). Set the nonsilent threshold to
   `max(-50, peak_frame_dbfs - 40)`.
5. Calculate duration and silence ratio over all frames.
6. ZCR and spectral summaries use nonsilent frames only. Calculate spectra
   with SciPy's periodic Hann window and power, not magnitude.
7. F0 input is the normalized raw frame with its full-frame mean subtracted;
   no window is applied to F0. A frame with zero centered residual energy is
   unvoiced. Calculate normalized autocorrelation over lags corresponding to
   `75-400 Hz`. Autocorrelation peak ties select the lowest allowed lag
   (highest F0). Retain frames whose peak is at least `0.30`; require three.
8. Calculate the exact linear percentiles and 85% cumulative-power rolloff.
9. `f0_range_hz` is maximum minus minimum voiced F0; `voiced_fraction` is
   voiced frames divided by all complete frames.
10. Reject every non-finite result and return an insertion-ordered dictionary
   matching `FEATURE_NAMES`.

Use this public surface:

```python
class FeatureExtractionError(ValueError):
    pass


def extract_acoustic_features(path: Path) -> dict[str, float]:
    samples = _read_pcm16_mono_16khz(Path(path))
    frames = _frames(samples, frame_size=400, hop_size=160)
    if frames.shape[0] == 0:
        raise FeatureExtractionError("WAV has no complete analysis frame")
    return _summarize(frames, sample_count=samples.size, sample_rate=16000)


def feature_vector(row: Mapping[str, Any]) -> tuple[float, ...]:
    if set(row) != set(FEATURE_NAMES):
        raise FeatureExtractionError("feature row fields do not match")
    values = tuple(float(row[name]) for name in FEATURE_NAMES)
    if any(not math.isfinite(value) for value in values):
        raise FeatureExtractionError("feature row contains a non-finite value")
    return values
```

- [ ] **Step 4: Run focused and mutation tests**

```powershell
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe -m unittest scripts.test_emotion_state_002_phase_b.AcousticFeatureTests -v
```

Expected: all acoustic tests pass; feature order mutation, imputation, and
schema drift tests reject.

- [ ] **Step 5: Commit Task 4**

```powershell
git add -- scripts/emotion_state_phase_b_features.py scripts/test_emotion_state_002_phase_b.py research/sources/emotion_state/emotion_state_phase_b_feature_v1.schema.json scripts/validate_emotion_state_002_phase_b.py docs/superpowers/plans/2026-07-19-emotion-state-phase-b-public-data-feasibility.md
git diff --cached --check
git commit -m "Add deterministic Phase B acoustic features"
```

### Task 5: Implement the claim-scoped actor split

**Files:**
- Create: `scripts/emotion_state_phase_b_splits.py`
- Modify: `scripts/test_emotion_state_002_phase_b.py`
- Modify: `scripts/validate_emotion_state_002_phase_b.py`

**Interfaces:**
- Consumes: eligible `CremaLabelRecord` objects and a configuration digest.
- Produces:
  `build_actor_split(records: Sequence[CremaLabelRecord], seed_digest: str)
  -> dict[str, str]`,
  `validate_actor_split(records, assignment) -> dict[str, Any]`, and
  `split_manifest_digest(records, assignment, seed_digest) -> str`.

- [ ] **Step 1: Write failing split tests**

Generate 91 synthetic actors, 12 sentences, and six labels without using
acoustics. Tests must assert exact `35/13/13/30` actor counts, zero overlap,
all sentences in each partition, stable output under row permutation, digest
mutation on a capacity-preserving cross-partition actor swap, digest mutation
when the authoritative lowercase SHA-256 configuration digest changes, and
failure on actor count `90` or `92`. Use a fixed expected assignment/digest
oracle with deliberately non-identical actor vectors. Add capacity-preserving
missing-label and missing-sentence mutations.

- [ ] **Step 2: Run tests and confirm RED**

```powershell
python -m unittest scripts.test_emotion_state_002_phase_b.ActorSplitTests -v
```

Expected: import failure for the missing split module.

- [ ] **Step 3: Implement deterministic stratified assignment**

Use one actor-level vector containing six label counts followed by twelve
sentence counts. Sort actors by descending vector L2 norm, then by
`sha256(f"{seed_digest}:{actor_id}")`. For each actor, evaluate every partition
with remaining capacity and select the partition minimizing:

```text
sum((candidate_partition_vector - global_vector * candidate_actor_count / 91)^2)
```

Break equal scores by the frozen partition order. After assignment, validate
all capacities, sentence presence, label presence, actor exclusivity, and
dependency roles. No acoustic feature or model output may be an input.

Digest creation must first call the same full
`validate_actor_split(records, assignment)` path. It must then commit to the
exact authoritative lowercase SHA-256 configuration digest, the validated
aggregate-only summary, and an inner canonical assignment commitment. Invalid
capacity, sentence-presence, label-presence, assignment, or dependency-role
input must never receive a digest.

The tracked digest payload may contain only schema/config identity, the
validated aggregate-only summary, and the opaque inner assignment commitment;
the ignored local manifest contains actor assignments. There is no public
standalone semantic validator for a fabricated aggregate summary. Only
records-plus-assignment validation may establish actor exclusivity or partition
presence.

- [ ] **Step 4: Run split and contract tests**

```powershell
python -m unittest scripts.test_emotion_state_002_phase_b.ActorSplitTests -v
python -m unittest scripts.test_emotion_state_002_phase_b.PhaseBContractTests -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit Task 5**

```powershell
git add -- scripts/emotion_state_phase_b_splits.py scripts/test_emotion_state_002_phase_b.py scripts/validate_emotion_state_002_phase_b.py
git diff --cached --check
git commit -m "Add Phase B actor-disjoint split contract"
```

### Task 6: Implement models, metrics, abstention, bootstrap, and decision rules

**Files:**
- Modify: `scripts/emotion_state_phase_b_evaluation.py`
- Modify: `scripts/test_emotion_state_002_phase_b.py`
- Modify: `scripts/validate_emotion_state_002_phase_b.py`

**Interfaces:**
- Consumes: eligible local rows, exact feature vectors, the deterministic
  actor assignment minted by the frozen split validator, and frozen
  config/environment identity.
- Produces:
  `mint_validated_split_assignment(records: Sequence[CremaLabelRecord],
  assignment: Mapping[str, str], seed_digest: str) ->
  ValidatedSplitAssignment`,
  `mint_partition_evidence(*, partition_role: str, row_ids: Sequence[str],
  actor_ids: Sequence[str], labels: np.ndarray, sentences: np.ndarray,
  features: np.ndarray, upstream_acoustic_source_commitment_sha256: str,
  split_assignment: ValidatedSplitAssignment, configuration: Mapping[str,
  Any], environment_lock: Mapping[str, Any], feature_schema: Mapping[str,
  Any], split_schema: Mapping[str, Any], model_identity: Mapping[str, Any])
  -> PartitionEvidence`,
  `fit_frozen_models(evidence: PartitionEvidence, seed: int) ->
  FittedModelEvidence`,
  `predict_probabilities(fitted_models: FittedModelEvidence,
  partition_evidence: PartitionEvidence) -> ProbabilityEvidence`,
  `calibrate_thresholds(probabilities: ProbabilityEvidence, targets:
  Sequence[float])
  -> CalibrationEvidence`,
  `evaluate_partition(probabilities: ProbabilityEvidence, thresholds:
  CalibrationEvidence) -> EvaluationEvidence`,
  `paired_actor_bootstrap(probabilities: ProbabilityEvidence, resamples:
  int, seed: int) -> BootstrapEvidence`,
  `mint_slice_analysis(probabilities: ProbabilityEvidence, evaluation:
  EvaluationEvidence, slices: Mapping[str, Sequence[str]]) ->
  SliceAnalysisEvidence`,
  `build_decision_evidence(evaluation: EvaluationEvidence, bootstrap:
  BootstrapEvidence, slice_analysis: SliceAnalysisEvidence) ->
  DecisionEvidence`, and
  `decide_experiment(metrics: DecisionEvidence, validity: Mapping[str, bool])
  -> str`.

`ValidatedSplitAssignment` has no public constructor. Its mint reruns the
frozen actor-split validator, requires the supplied assignment to equal the
deterministic split for the exact records/configuration digest, and binds the
existing split-manifest digest and privately retains the exact eligible record
set. `PartitionEvidence` also has no public constructor. Row IDs must be the
complete ordered eligible clip stems for the declared partition; actor,
label, and sentence arrays must match those records exactly. Its payload binds
the full split assignment/manifest, config/environment/feature/split schemas,
case order, authoritative rows/actors/labels/sentences, exact feature bytes,
the later-runner-owned upstream acoustic-source commitment, and model/class
identity without claiming that Task 6 validated source audio.

`FittedModelEvidence` privately retains the three fitted estimators and binds
the exact training partition, frozen estimator settings/classes, fitted
encoder/scaler/classifier state, and shared config/environment/split lineage.
`ProbabilityEvidence` can be minted only by revalidating that bundle,
executing those exact models on an authoritative partition, and recomputing
the fitted-state identity after prediction. Semantic calibration, evaluation,
and bootstrap interfaces accept only `ProbabilityEvidence`; pure underscored
array helpers remain available solely for hand-calculated numerical tests and
cannot mint semantic evidence.

Every bound object stores private canonical bytes plus a separately stored
mint digest. It exposes fresh decoded copies/read-only values, blocks normal
attribute mutation and public construction, and rechecks its mint digest and
private lineage before use. A caller-recomputed public `self_sha256` on a
detached mapping is never evidence authenticity.

Evaluation requires calibration and evaluated probability evidence to share
the exact fitted-model/training/config/environment/feature/split/assignment/
class lineage while permitting distinct partition rows and probability
commitments. Evaluation records the exact calibration mint and complete
calibration provenance; retained thresholds and achieved calibration coverage
must equal that artifact. Evaluation/bootstrap/slice artifacts must share the
same exact final probability mint before a decision; equal counts are
insufficient.

Fitting accepts only bound `training_discovery` evidence, calibration accepts
only bound `calibration` evidence, diagnostic evaluation names
`balanced_diagnostic` and cannot produce decision evidence, and paired
bootstrap/final decision evidence accepts only bound `final_lockbox`
evidence. The validator freezes exact input/result keys, model keys, class
order, thresholds, actor IDs, resample count, metric keys, validity keys,
mathematical domains, count relationships, and finite requirements.

Decision-critical facts are derived, never caller booleans:

- `sentence_driven_apparent_lift` is true exactly when sentence-ID macro-F1
  exceeds class-prior macro-F1 while acoustic lift over sentence ID is not
  positive;
- `confidence_abstention_improves` is true only when at least one unsuppressed
  acoustic `0.8`/`0.6` retained cell has actual coverage below one and strict
  macro-F1 improvement, with no eligible retained cell worse than full
  acoustic macro-F1;
- slice reversal/instability come from a private `SliceAnalysisEvidence`
  minted over authoritative contributor row IDs. Each slice requires at least
  ten actors; its metrics/lifts, contributor commitments, domains, and counts
  are validated. Reversal is any negative acoustic lift versus either
  baseline. Instability is any slice lift differing from the full-partition
  lift by more than the frozen absolute tolerance `0.10`.

- [ ] **Step 1: Write failing evaluation tests**

Use synthetic arrays with explicit actor clusters. Tests must prove:

- the class-prior baseline matches an exact imbalanced training-prevalence
  oracle;
- the sentence baseline contains only one-hot sentence IDs;
- the acoustic pipeline contains only `StandardScaler` and the frozen
  logistic regression;
- calibration thresholds use calibration probabilities only;
- 100/80/60% targets record achieved coverage under ties;
- macro-F1, balanced accuracy, per-class recall, multiclass Brier, log loss,
  and ten-bin ECE match hand-calculated fixtures;
- 2,000 paired actor-cluster bootstrap draws match hard-coded independent
  interval oracles over non-identical multi-row actors;
- cells below ten actors suppress;
- every `keep_for_research_only`, `revise`, and `discard` clause has a mutation
  test;
- diagnostic relabeling, cross-run equal-count artifact mixing, and any exact
  input/commitment mutation fail before a decision;
- cross-run calibration/model lineage mixing, nested mutation/reseal,
  non-authoritative row/label inputs, arbitrary probability mappings,
  bare-string row IDs, and caller-asserted decision flags fail closed;
- per-class actor/case totals, retained coverage/count identities, zero
  retained cells, and exact retained calibration cells are mutation tested;
- a valid skewed percentile interval may exclude the observed point estimate.

- [ ] **Step 2: Run tests and confirm RED**

```powershell
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe -m unittest scripts.test_emotion_state_002_phase_b.EvaluationTests -v
```

Expected: missing evaluation interfaces.

- [ ] **Step 3: Implement the three exact comparisons**

Construct:

```python
import numpy as np
from collections.abc import Mapping, Sequence
from typing import Any

from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def _classifier(seed: int) -> LogisticRegression:
    return LogisticRegression(
        C=1.0,
        class_weight=None,
        solver="lbfgs",
        max_iter=10000,
        random_state=seed,
        l1_ratio=0.0,
    )


def build_models(seed: int) -> dict[str, object]:
    return {
        "class_prior": DummyClassifier(strategy="prior"),
        "sentence_id": Pipeline([
            ("one_hot", OneHotEncoder(handle_unknown="ignore")),
            ("classifier", _classifier(seed)),
        ]),
        "acoustic": Pipeline([
            ("standardize", StandardScaler()),
            ("classifier", _classifier(seed)),
        ]),
    }
```

Before accepting the dependency lock, prove this warning-free scikit-learn
1.8 API produces multinomial six-class probabilities and bit-identical
coefficients/probabilities to the deprecated explicit `penalty="l2"` form.
Abort the lock rather than changing model semantics silently.

- [ ] **Step 4: Implement metrics and calibration**

Use fixed label order `A,D,F,H,N,S`. Multiclass Brier is the mean row-wise sum
of squared probability error. Equal-width ECE uses ten bins on maximum
probability with left-closed/right-open bins except the final closed bin.
Coverage thresholds are the highest deterministic threshold whose calibration
coverage is at least each target; ties retain all equal-confidence rows and
record achieved coverage. Validators enforce F1, balanced accuracy, recall,
ECE, coverage, and retained F1 in `[0,1]`; six-class Brier in `[0,2]`; log
loss at least zero; lift points/bounds in `[-1,1]` with `lower <= upper`; and
positive total actor/case counts with non-negative, internally consistent
class/retained counts. Percentile intervals do not have to contain the
observed point estimate.

- [ ] **Step 5: Implement paired actor-cluster bootstrap**

Derive the integer seed from the first 16 hex characters of the canonical
configuration SHA-256. For each of 2,000 draws, sample lockbox actors with
replacement and include every case for each sampled actor. Use identical draw
indexes for all three models and publish only aggregate percentile intervals.

- [ ] **Step 6: Implement the exact decision contract**

Return:

- `keep_for_research_only` only when both paired macro-F1 lift lower 95%
  bounds exceed zero, Brier improves over class prior, every class recall is
  positive, and no validity/slice reversal exists;
- `revise` for an interval crossing zero, worse calibration, zero recall,
  eligible slice instability, or ineffective confidence abstention;
- `discard` for failure to beat both baselines, sentence-driven apparent
  lift, leakage, nondeterminism, lockbox misuse, or invalid material/environment.

Never return a runtime recommendation.

- [ ] **Step 7: Run focused evaluation tests**

```powershell
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe -m unittest scripts.test_emotion_state_002_phase_b.EvaluationTests -v
```

Expected: all tests pass deterministically in repeated runs.

- [ ] **Step 8: Commit Task 6**

```powershell
git add -- scripts/emotion_state_phase_b_evaluation.py scripts/test_emotion_state_002_phase_b.py scripts/validate_emotion_state_002_phase_b.py docs/superpowers/plans/2026-07-19-emotion-state-phase-b-public-data-feasibility.md
git diff --cached --check
git commit -m "Add Phase B classical evaluation contract"
```

### Task 7: Implement the AMI conversational-mechanics lane

**Files:**
- Create: `scripts/emotion_state_phase_b_ami_mechanics.py`
- Modify: `scripts/test_emotion_state_002_phase_b.py`
- Modify: `scripts/validate_emotion_state_002_phase_b.py`

**Interfaces:**
- Consumes: selected, hash-verified AMI metadata, words/transcript boundaries,
  timing links, dialogue acts, participant dependencies, and official
  partition definitions.
- Produces:
  `MeetingMechanics`,
  `compute_meeting_mechanics(turns: Sequence[Turn]) -> MeetingMechanics`, and
  `contribution_limited_aggregates(meetings: Sequence[MeetingMechanics],
  partition_membership: Mapping[str, Sequence[str]], official_order:
  Sequence[str], minimum_contributors: int = 10) -> dict[str, Any]`.

- [ ] **Step 1: Write failing synthetic AMI tests**

Use tiny namespace-qualified XML strings in temporary files. Assert exact
turn-duration median/p90, inter-turn-gap median/p90, overlap ratio,
floor-changes/minute, normalized speaker entropy, backchannels/100 turns, and
dialogue-act distribution. Add failures for unresolved participants, malformed
time spans, unknown meetings, transcript-text leakage, repeated participant
contribution, and cells below ten participants.

- [ ] **Step 2: Run tests and confirm RED**

```powershell
python -m unittest scripts.test_emotion_state_002_phase_b.AmiMechanicsTests -v
```

Expected: import failure for the missing AMI module.

- [ ] **Step 3: Implement local-only turn records**

Use immutable records:

```python
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Turn:
    meeting_id: str
    participant_id: str
    start_ms: int
    end_ms: int
    dialogue_act: str


@dataclass(frozen=True)
class MeetingMechanics:
    meeting_id: str
    participants: tuple[str, ...]
    values: tuple[tuple[str, float], ...]
    dialogue_act_distribution: tuple[tuple[str, float], ...]
```

Normalize XML local names, follow only local NXT references, reject external
URIs, retain no transcript text, and require `0 <= start_ms < end_ms`.

- [ ] **Step 4: Implement exact mechanics**

Sort turns by `(start_ms, end_ms, participant_id)`. Define:

- turn duration as `end_ms - start_ms`;
- inter-turn gap as `next.start_ms - current.end_ms`, including negative
  overlap values only in overlap calculation and nonnegative values in gap
  summaries;
- overlap ratio as union duration of simultaneous multi-speaker intervals
  divided by meeting span;
- floor change when adjacent non-backchannel turns change participant;
- speaker balance as Shannon entropy divided by `log(participant_count)`;
- backchannel rate as backchannel acts divided by all turns times 100.

Use linear percentiles and fail on fewer than two proven participants.

- [ ] **Step 5: Implement contribution-limited aggregation**

For each official `scenario_only`, `full_corpus`, and `full_only` cell, sort
meetings by official order then canonical meeting digest. Include a meeting
only when none of its participants has contributed to that cell. Suppress any
scalar/bucket/dialogue-act cell with fewer than ten unique participants.
Return aggregates and suppression counts only.

- [ ] **Step 6: Run focused tests**

```powershell
python -m unittest scripts.test_emotion_state_002_phase_b.AmiMechanicsTests -v
```

Expected: all calculations and boundary tests pass.

- [ ] **Step 7: Commit Task 7**

```powershell
git add -- scripts/emotion_state_phase_b_ami_mechanics.py scripts/test_emotion_state_002_phase_b.py scripts/validate_emotion_state_002_phase_b.py
git diff --cached --check
git commit -m "Add Phase B AMI mechanics lane"
```

### Task 8: Implement the phase runner and one-use lockbox state machine

**Files:**
- Create: `scripts/run_emotion_state_002_phase_b.py`
- Modify: `scripts/test_emotion_state_002_phase_b.py`
- Modify: `scripts/validate_emotion_state_002_phase_b.py`

**Interfaces:**
- Consumes: frozen config/schemas/environment lock and ignored local state.
- Produces CLI phases `preflight`, `non-lockbox`, `lockbox`,
  `stage-candidate`, `accept-receipt`, and `reject-receipt`.

- [ ] **Step 1: Write failing state-machine tests**

Tests use injected temporary roots and synthetic data only. Cover invalid
phase order, config/environment mutation, second lockbox open, lockbox access
from non-lockbox mode, stale local state, path escape/reparse links, canonical
pair tampering, partial pair, crash recovery, accept, reject, and previous-pair
restoration.

- [ ] **Step 2: Run tests and confirm RED**

```powershell
python -m unittest scripts.test_emotion_state_002_phase_b.RunnerStateTests -v
```

Expected: missing runner module.

- [ ] **Step 3: Implement ignored state with explicit transitions**

Use a canonical JSON state file under
`.tmp/emotion-state-002-phase-b/state.json`:

```json
{
  "schema_version": 1,
  "phase": "initialized",
  "configuration_sha256": "",
  "environment_lock_sha256": "",
  "input_ledger_sha256": "",
  "split_manifest_sha256": "",
  "non_lockbox_packet_sha256": "",
  "lockbox_open_count": 0,
  "lockbox_result_sha256": "",
  "candidate_transaction_id": ""
}
```

The empty initial digest fields are allowed only in `initialized`; every later
phase requires uppercase 64-hex values. Allowed transitions are:

```text
initialized -> preflight_complete
preflight_complete -> non_lockbox_complete
non_lockbox_complete -> lockbox_complete
lockbox_complete -> awaiting_acceptance
awaiting_acceptance -> accepted | rejected
```

Any other transition fails without changing bytes.

- [ ] **Step 4: Implement guarded path and boundary checks**

Resolve every input against an exact allowed root. Reject symlinks/reparse
points, private path components, runtime imports, credential environment
variables, network modules/calls, and output destinations outside the exact
ignored/canonical roots. Tests must patch filesystem and socket entry points
to prove refusal.

- [ ] **Step 5: Build aggregate result and deterministic report rendering**

The result must bind:

- Phase A commit and pair hashes;
- dataset evidence and raw CSV hashes;
- environment/config/feature/split digests;
- label eligibility/abstention aggregates;
- model settings and metric definitions;
- non-lockbox review digest;
- lockbox open count `1`;
- aggregate CREMA metrics/intervals/suppression counts;
- aggregate AMI mechanics/suppression counts;
- keep/revise/discard decision;
- every closed boundary.

`render_report(result, result_sha256)` must be a pure function. JSON uses
sorted keys, UTF-8, LF, `allow_nan=False`, and one terminal newline.

- [ ] **Step 6: Implement the crash-safe acceptance transaction**

Mirror the reviewed Phase A transaction invariants inside the Phase B runner:

1. acquire an OS-backed publication lock;
2. recover or reject any prior journal;
3. render candidate result/report into transaction-specific ignored files;
4. hash and validate both;
5. preserve both previous canonical files or prove both absent;
6. durably write an `awaiting_acceptance` journal;
7. atomically replace both canonical files;
8. write a receipt containing transaction and pair hashes;
9. on accept, revalidate config, pair bytes, renderer equality, and journal
   identity before durable `accepted` cleanup;
10. on reject or pre-accept failure, restore the exact previous pair.

No direct canonical write path is allowed.

- [ ] **Step 7: Run all runner and publication tests**

```powershell
python -m unittest scripts.test_emotion_state_002_phase_b.RunnerStateTests -v
python -m unittest scripts.test_emotion_state_002_phase_b -v
```

Expected: all tests pass; transaction fault injection restores exact bytes.

- [ ] **Step 8: Commit Task 8**

```powershell
git add -- scripts/run_emotion_state_002_phase_b.py scripts/test_emotion_state_002_phase_b.py scripts/validate_emotion_state_002_phase_b.py
git diff --cached --check
git commit -m "Add Phase B guarded runner and publication transaction"
```

### Task 9: Complete validators, command docs, and the synthetic guarded ledger

**Files:**
- Modify: `scripts/validate_emotion_state_002_phase_b.py`
- Modify: `scripts/test_emotion_state_002_phase_b.py`
- Modify: `docs/product/COMMANDS.md`
- Modify: `docs/product/CHECKPOINT_INDEX.md`
- Modify: `docs/thesis/METHODOLOGY_LOG.md`
- Modify: `docs/thesis/ROADMAP.md`
- Modify:
  `research/experiments/EMOTION-STATE-002-phase-b-public-data-feasibility.md`

**Interfaces:**
- Consumes: all Tasks 1-8 code and synthetic fixtures.
- Produces validator sections `source`, `contracts`, `environment`,
  `synthetic`, `candidate --receipt`, and `checkpoint`.

- [ ] **Step 1: Add failing validator and output-leakage tests**

Mutation-test every result field, report sentence, hash, lockbox count,
decision, contributor floor, and boundary flag. Scan candidate output for
absolute paths, timestamps, filenames, stems, actor/speaker/participant IDs,
row arrays, transcripts, audio markers, model serialization, probabilities,
credentials, and the five operational signals.

- [ ] **Step 2: Implement the final validator CLI**

The CLI must require exactly one section:

```text
source
contracts
environment
synthetic
candidate --receipt .tmp/emotion-state-002-phase-b/publication/receipt.json
checkpoint
```

`candidate` requires a live `awaiting_acceptance` transaction; `checkpoint`
requires no live journal/receipt and exactly the accepted canonical pair.

- [ ] **Step 3: Add exact command documentation**

Document Windows commands using the ignored venv Python. Mark dependency,
public-material, lockbox, acceptance, push, and merge commands as explicit
gates. Do not document a provider, call, simulation, private-data, or runtime
command.

- [ ] **Step 4: Run the complete synthetic ledger**

Run:

```powershell
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe -m unittest scripts.test_emotion_state_002_phase_b -v
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe scripts/validate_emotion_state_002_phase_b.py source
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe scripts/validate_emotion_state_002_phase_b.py contracts
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe scripts/validate_emotion_state_002_phase_b.py environment
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe scripts/validate_emotion_state_002_phase_b.py synthetic
python scripts/check_thesis_update_gate.py
python scripts/check_thesis_reference_registry.py
python scripts/validate_project_drift_guard.py
python scripts/validate_context_reading_policy.py
python scripts/validate_check_setup.py
git diff --check
```

Expected: all commands exit `0`; no real public material, private path,
network, provider, call, simulation, or runtime action occurs.

- [ ] **Step 5: Commit Task 9**

```powershell
git add -- scripts/validate_emotion_state_002_phase_b.py scripts/test_emotion_state_002_phase_b.py docs/product/COMMANDS.md docs/product/CHECKPOINT_INDEX.md docs/thesis/METHODOLOGY_LOG.md docs/thesis/ROADMAP.md research/experiments/EMOTION-STATE-002-phase-b-public-data-feasibility.md
git diff --cached --check
git commit -m "Document and validate Phase B offline implementation"
```

### Task 10: Run the authorized public-material preflight and non-lockbox experiment

**Files:**
- Local ignored writes only under `.tmp/emotion-state-002-phase-b-cut4b/`
- Modify tracked docs only after reviewed aggregate evidence exists:
  `docs/thesis/METHODOLOGY_LOG.md`,
  `docs/thesis/ROADMAP.md`, and
  `research/experiments/EMOTION-STATE-002-phase-b-public-data-feasibility.md`

**Interfaces:**
- Consumes: fixed ignored CREMA-D/AMI roots and all frozen identities.
- Produces: ignored label/features/split/mechanics caches and one ignored
  non-lockbox review packet; no canonical pair.

- [ ] **Step 1: Stop at the public-material authorization gate**

Do not read either dataset or run a model until explicit public-material
evaluation authority is recorded.

- [ ] **Step 2: Run preflight before any audio feature extraction**

```powershell
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe scripts/run_emotion_state_002_phase_b.py preflight
```

Expected:

- every Phase A/dataset/config/environment hash matches;
- exact real CSV schemas match;
- label ledger is exactly `6570/644/204/23`;
- eligible labels are exactly `951/500/613/330/3834/342`;
- all 91 actors and 12 sentences remain;
- AMI selected classifications, dependencies, and official partitions match;
- no feature, model, or canonical output exists if any check fails.

- [ ] **Step 3: Extract local features and AMI mechanics**

```powershell
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe scripts/run_emotion_state_002_phase_b.py non-lockbox
```

The command may fit on `training_discovery`, calibrate on `calibration`, and
calculate balanced diagnostics. It must not read final-lockbox feature rows or
labels and must leave `lockbox_open_count=0`.

- [ ] **Step 4: Validate the non-lockbox packet independently**

Run the full Task 9 ledger plus direct aggregate inspection. Verify that no
identifier/row/path/probability is present, every diagnostic cell has at least
ten actors, and the frozen configuration cannot be changed without invalidating
the packet.

- [ ] **Step 5: Commit only reviewed non-lockbox documentation**

```powershell
git add -- docs/thesis/METHODOLOGY_LOG.md docs/thesis/ROADMAP.md research/experiments/EMOTION-STATE-002-phase-b-public-data-feasibility.md
git diff --cached --check
git commit -m "Record Phase B non-lockbox review"
```

Do not commit ignored caches or canonical result/report files.

### Task 11: Open the final lockbox once and review the aggregate result

**Files:**
- Local ignored writes only under `.tmp/emotion-state-002-phase-b-cut4b/`

**Interfaces:**
- Consumes: the independently accepted non-lockbox packet.
- Produces: one ignored lockbox result and candidate aggregate payload with
  `lockbox_open_count=1`.

- [x] **Step 1: Stop at the final-lockbox authorization gate**

Require explicit one-use authorization tied to the exact non-lockbox packet
SHA-256 and current HEAD. First write the fixed ignored source-silent admission
receipt bound to the reviewed clean HEAD, guarded-ledger SHA-256, accepted
predecessor-state SHA-256, and packet SHA-256. Admission and every production
recheck use exactly three local no-fetch Git reads (`show-toplevel`, `HEAD`, and
clean status including untracked files) with `GIT_LFS_SKIP_SMUDGE=1`. The runner must durably
write and read back the exact `reserved` record before minting its private
final-audio authority, hold that exact reservation file through final
evaluation and result persistence, and revalidate admission during completed
recovery. Completed reservation bytes remain held through recovery validation
and the state transition. A reserved failure is terminal.

The reviewed guarded ledger is the fixed ignored
`.tmp/emotion-state-002-phase-b-cut4b/task-11-guarded-ledger.json`. Render it as
canonical UTF-8 LF JSON with two-space indentation, sorted keys, and one terminal
LF. Bind `schema_version`, `task_id`, the exact committed implementation HEAD,
and the exact ordered guarded command vectors. Each command entry contains only
`argv`, `exit_code`, `stdout_sha256`, and `stderr_sha256`; do not persist raw
command output. The guarded-ledger digest is the uppercase SHA-256 of those exact
bytes. After `admit-lockbox`, independently hash the exact
`lockbox-admission.json` bytes and pass both reviewed digests to `lockbox`.
The passing ledger bound implementation HEAD
`c7a5e4037ad8134c96dcd7e8b9577f08fe92391b` and had exact SHA-256
`8515DA4A622A8AF8CE3BE07BE6CAFC8360EDE729F2845317E13C701DBA18299A`.
The admitted receipt SHA-256 was
`0F10FD618FD20819EB7D21981C29E77B6936977D80659A82A5CE1886C1191278`.

- [x] **Step 2: Run the one-use lockbox command**

Completed: exactly one production child exited `0` after `346.9s`; no retry
occurred. The state transitioned once from `non_lockbox_complete` to
`lockbox_complete` with `lockbox_open_count=1`. Exact state SHA-256 is
`69B6475BB32209DD50A6E24866F19D6B44FB51BFA458836BF3B1805140C2BC8C`;
exact result SHA-256 is
`E3EC0EB82E77C1979BF8F921D6EBF6321F510687A608C933473C4DB04AE02F35`.
The production lockbox completed exactly once and is closed. Do not run
`admit-lockbox` or `lockbox` again for this experiment version.

- [x] **Step 3: Review the aggregate decision evidence**

Completed: two independent aggregate-only reviews returned `C0/I0/M0`. The
decision is `revise`. Acoustic macro-F1 is `0.3635639146`, versus
`0.1260336470` for each baseline; paired lift is `0.2375302676` with 95%
interval `[0.2006732151, 0.2644157664]`. Eligible slice instability and
reversal are both `true`, and confidence abstention improvement is `false`.
The AMI persisted shape remains exactly aggregate plus authority SHA-256; its
timing and dialogue contributions remain unavailable.

- [x] **Step 4: Reject invalid execution before publication**

Completed: state/result/reservation/admission/ledger/split lineage validation
passed, the final-decision contract was eligible, and no canonical files were
staged. Task 12 remains separate and unchecked. This checkpoint is offline
acted-perception feasibility evidence, not customer internal emotion, AMI
contribution evidence, real-call performance, provider/PSTN/ASR/latency
feasibility, runtime readiness, commercial effectiveness, or production
readiness.

### Task 12: Stage, independently validate, accept, and commit the canonical pair

**Files:**
- Create only through the transaction:
  `research/experiments/generated/EMOTION-STATE-002-phase-b-public-data-feasibility/result.json`
- Create only through the transaction:
  `research/experiments/generated/EMOTION-STATE-002-phase-b-public-data-feasibility/report.md`
- Modify after acceptance:
  `docs/thesis/METHODOLOGY_LOG.md`,
  `docs/thesis/ROADMAP.md`,
  `docs/product/CHECKPOINT_INDEX.md`,
  `research/experiments/EMOTION-STATE-002-phase-b-public-data-feasibility.md`,
  `docs/superpowers/plans/2026-07-19-emotion-state-phase-b-public-data-feasibility.md`,
  and `scripts/test_emotion_state_002_phase_b.py`

**Interfaces:**
- Consumes: exact lockbox result and reviewed current HEAD.
- Produces: accepted exact pair, no residual transaction artifacts, and a
  pair-only commit followed by a separate documentation commit if authorized.

- [x] **Step 1: Stop at the publication authorization gate**

Require authority to stage the candidate. Acceptance and push remain separate
explicit actions.

- [x] **Step 2: Stage the candidate transaction**

```powershell
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe scripts/run_emotion_state_002_phase_b.py stage-candidate --receipt receipt.json
```

Expected: exact canonical pair is staged, previous pair is recoverable, journal
status is `awaiting_acceptance`, and no Git commit occurs.

- [x] **Step 3: Independently validate and inspect candidate content**

```powershell
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe scripts/validate_emotion_state_002_phase_b.py candidate --receipt .tmp/emotion-state-002-phase-b-cut4b/publication/receipt.json
git diff -- research/experiments/generated/EMOTION-STATE-002-phase-b-public-data-feasibility/result.json research/experiments/generated/EMOTION-STATE-002-phase-b-public-data-feasibility/report.md
```

Verify claims independently from any evaluator label. Confirm the exact pair,
digests, renderer equality, aggregate-only content, one lockbox opening,
decision contract, and every readiness limitation.

- [x] **Step 4: Accept or reject explicitly**

Accept only after review:

```powershell
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe scripts/run_emotion_state_002_phase_b.py accept-receipt --receipt receipt.json
```

Otherwise restore:

```powershell
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe scripts/run_emotion_state_002_phase_b.py reject-receipt --receipt receipt.json
```

- [x] **Step 5: Run final checkpoint and repository ledger**

```powershell
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe scripts/validate_emotion_state_002_phase_b.py checkpoint
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe -m unittest scripts.test_emotion_state_002_phase_b -v
python scripts/check_thesis_reference_registry.py
python scripts/validate_project_drift_guard.py
python scripts/validate_context_reading_policy.py
python scripts/validate_check_setup.py
git diff --check
```

Expected: all listed gates pass; no journal/receipt remains in the canonical
directory. The thesis-update gate is intentionally deferred to Step 7, after
the real closeout edits and before their separate commit, because running it
here conflicts with the exact pair-only invariant.

Completed: the monolithic test command hit its `1804s` shell wrapper limit
without a unittest verdict and was not counted as a pass. Its orphaned
worktree test tree was stopped. The unchanged `393` tests then passed in seven
attributable groups (`117/65/33/23/30/25/100`). Checkpoint, thesis-reference,
drift, context-policy, setup, and diff gates passed. The pre-pair
thesis-update failure was retained as expected sequencing evidence and was not
bypassed.

- [x] **Step 6: Commit the exact pair only**

```powershell
git add -- research/experiments/generated/EMOTION-STATE-002-phase-b-public-data-feasibility/result.json research/experiments/generated/EMOTION-STATE-002-phase-b-public-data-feasibility/report.md
git diff --cached --name-only
git diff --cached --check
git commit -m "Record EMOTION-STATE Phase B public-data feasibility"
```

The cached name list must contain exactly the two canonical paths.

Completed: exact pair-only commit
`f887989597f23f438e8e537ba5bfbd05823a3587`.

- [x] **Step 7: Record thesis closeout separately**

After the pair-only commit, update the closeout docs and their focused contract
test with the accepted transaction ID, result/report hashes, pair-only commit,
keep/revise/discard decision, limitations, and unchanged
runtime/provider/private boundaries. Correct the receipt command forms and
this thesis-gate sequence in the same documentation commit.

```powershell
.tmp/emotion-state-002-phase-b/venv/Scripts/python.exe -m unittest scripts.test_emotion_state_002_phase_b.PhaseBContractTests -v
python scripts/check_thesis_update_gate.py
python scripts/check_thesis_reference_registry.py
python scripts/validate_project_drift_guard.py
python scripts/validate_context_reading_policy.py
python scripts/validate_check_setup.py
git diff --check
```

The accepted transaction is `559ccc55b0b5412ba455ca7fe3e3a6b7`;
result SHA-256 is
`5829BF4A1FBE86BDD6B19B7CF8B07033BF79744B12F7AF1D493F8D3F10D0073C`;
report SHA-256 is
`56140D4ABDD0B2A6924749E719C66D3972483E0F4191F63201E9DDFCA0A23482`;
the prerequisite correction is commit
`256fa92ed94eda3f66fef21512d9f292b1d0de61`; and the decision is `revise`.
No fake changed-file input, checker exemption, or hook bypass is permitted.

Completed: the Phase B contract class passed `16/16`. The real no-argument
thesis-update gate passed with six changed files, three thesis-triggering
files, two thesis-tracking files, and zero failures. Checkpoint,
thesis-reference, drift, context-policy, setup, compilation, and diff gates
also passed.

- [x] **Step 8: Stop before push, merge, Phase C, runtime, or provider work**

Report the clean local branch and evidence. Push or merge only under explicit
authority. A completed result remains an offline public-data
research/prototype checkpoint, not production readiness or evidence of real
customer internal emotion.

## Plan Self-Review Checklist

- [x] Every approved design section maps to at least one task.
- [x] CREMA-D label parsing uses the real pinned schema and conservative
  `6570/644/204/23` concordance ledger.
- [x] The 17 feature names and `35/13/13/30` split are exact.
- [x] Training, calibration, diagnostic, and final-lockbox roles never blur.
- [x] AMI never produces an emotion/operational label or row join.
- [x] Dependency, public-material, lockbox, acceptance, and push authorities
  remain separate.
- [x] Every code task starts RED, reaches GREEN, runs focused checks, and
  commits an independently reviewable deliverable.
- [x] Canonical publication is staged, reviewed, explicitly accepted, and
  committed as an exact pair.
- [x] No placeholder text, undefined interface, runtime edit, private-data
  path, provider action, call, simulation, or production-readiness claim
  appears.
