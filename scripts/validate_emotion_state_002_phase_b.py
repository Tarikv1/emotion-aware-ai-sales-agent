from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.metadata
import json
import math
import os
import re
import struct
import sys
import sysconfig
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
CONFIG_PATH = ROOT / "research/experiments/cases/emotion-state-002-phase-b-config.json"
FEATURE_SCHEMA_PATH = (
    ROOT
    / "research/sources/emotion_state/emotion_state_phase_b_feature_v1.schema.json"
)
SPLIT_SCHEMA_PATH = (
    ROOT
    / "research/sources/emotion_state/emotion_state_evaluation_split_v1.schema.json"
)
ENVIRONMENT_LOCK_PATH = (
    ROOT / "research/environments/emotion-state-002/requirements.lock"
)
EVALUATION_PYTHON_PATH = (
    ROOT / ".tmp/emotion-state-002-phase-b/venv/Scripts/python.exe"
)
WHEELHOUSE_PATH = (
    ROOT / ".tmp/emotion-state-002-phase-b/dependencies/wheelhouse"
)
PHASE_A_RESULT_PATH = (
    ROOT
    / "research/experiments/generated/EMOTION-STATE-001-phase-a-contracts/result.json"
)
PHASE_A_REPORT_PATH = PHASE_A_RESULT_PATH.with_name("report.md")
SOURCE_MANIFEST_PATHS = {
    "crema_d": (
        ROOT
        / "research/sources/emotion_state/datasets/"
        "crema-d-v1.0-audio-wav.manifest.json"
    ),
    "ami": (
        ROOT
        / "research/sources/emotion_state/datasets/"
        "ami-manual-annotations-v1.6.2.manifest.json"
    ),
}

FEATURE_NAMES = (
    "duration_seconds", "silence_ratio", "voiced_fraction", "f0_median_hz",
    "f0_iqr_hz", "f0_range_hz", "rms_dbfs_mean", "rms_dbfs_std",
    "rms_dbfs_p90_minus_p10", "zero_crossing_rate_mean",
    "zero_crossing_rate_std", "spectral_centroid_hz_mean",
    "spectral_centroid_hz_std", "spectral_bandwidth_hz_mean",
    "spectral_bandwidth_hz_std", "spectral_rolloff_85_hz_mean",
    "spectral_rolloff_85_hz_std",
)
EXPECTED_FEATURE_NUMERICAL_SEMANTICS = {
    "f0_frame_input": "normalized_raw_frame",
    "f0_centering": "subtract_full_frame_mean",
    "f0_window": "none",
    "f0_zero_residual_energy": "unvoiced",
    "f0_autocorrelation_peak_tie_break": "lowest_lag_highest_f0",
    "zero_frame_rms_floor": "one_pcm16_lsb_over_full_frame_rms",
    "zero_frame_rms_floor_linear": 0.00000152587890625,
    "rms_summary_frame_scope": "all_complete_frames",
    "standard_deviation_ddof": 0,
    "f0_range_definition": "maximum_minus_minimum_voiced_f0",
    "voiced_fraction_denominator": "all_complete_frames",
    "zcr_spectral_frame_scope": "nonsilent_frames",
}
PARTITION_COUNTS = {
    "training_discovery": 35,
    "calibration": 13,
    "balanced_diagnostic": 13,
    "final_lockbox": 30,
}

EXPECTED_FEATURE_SCHEMA: dict[str, Any] = {
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
    "f0_frame_input": "normalized_raw_frame",
    "f0_centering": "subtract_full_frame_mean",
    "f0_window": "none",
    "f0_zero_residual_energy": "unvoiced",
    "voiced_autocorrelation_threshold": 0.3,
    "minimum_voiced_frames": 3,
    "f0_autocorrelation_peak_tie_break": "lowest_lag_highest_f0",
    "zero_frame_rms_floor": "one_pcm16_lsb_over_full_frame_rms",
    "zero_frame_rms_floor_linear": 0.00000152587890625,
    "rms_summary_frame_scope": "all_complete_frames",
    "standard_deviation_ddof": 0,
    "f0_range_definition": "maximum_minus_minimum_voiced_f0",
    "voiced_fraction_denominator": "all_complete_frames",
    "zcr_spectral_frame_scope": "nonsilent_frames",
    "spectral_rolloff_fraction": 0.85,
    "percentile_method": "linear",
    "ordered_features": list(FEATURE_NAMES),
    "imputation_allowed": False,
    "runtime_influence_allowed": False,
}

EXPECTED_SPLIT_SCHEMA: dict[str, Any] = {
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
        "dialogue_dyad": "not_applicable",
    },
    "covering_dependencies": {"call_session": "speaker"},
    "partition_order": [
        "training_discovery",
        "calibration",
        "balanced_diagnostic",
        "final_lockbox",
    ],
    "partition_actor_counts": PARTITION_COUNTS,
    "expected_actor_count": 91,
    "expected_sentence_count": 12,
    "unseen_sentence_claim_allowed": False,
    "recording_site_generalization_allowed": False,
    "runtime_influence_allowed": False,
}

EXPECTED_CONFIG: dict[str, Any] = {
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
            "unique_winner_disagreement": 23,
        },
        "expected_label_counts": {
            "A": 951,
            "D": 500,
            "F": 613,
            "H": 330,
            "N": 3834,
            "S": 342,
        },
    },
    "model": {
        "regularization": "l2",
        "C": 1.0,
        "class_weight": None,
        "maximum_iterations": 10000,
        "solver": "lbfgs",
        "hyperparameter_search_allowed": False,
    },
    "coverage_targets": [1.0, 0.8, 0.6],
    "ece_equal_width_bin_count": 10,
    "bootstrap_resamples": 2000,
    "minimum_unique_contributors_per_cell": 10,
    "ami_partitions": ["scenario_only", "full_corpus", "full_only"],
    "boundaries": {
        "private_data_allowed": False,
        "provider_operations_allowed": False,
        "network_during_evaluation_allowed": False,
        "source_adaptation_allowed": False,
        "runtime_influence_allowed": False,
        "customer_state_output_allowed": False,
    },
}

EXPECTED_ENVIRONMENT_LOCK: dict[str, Any] = {
    "schema_id": "emotion-state-002-research-environment-lock-v1",
    "python_version": "3.11",
    "platform": "win_amd64",
    "direct_requirements": [
        "numpy",
        "scipy",
        "scikit-learn",
    ],
    "distributions": [
        {
            "name": "joblib",
            "version": "1.5.3",
            "direct": False,
            "wheel_filename": "joblib-1.5.3-py3-none-any.whl",
            "sha256": "5FC3C5039FC5CA8C0276333A188BBD59D6B7AB37FE6632DAA76BC7F9EC18E713",
            "license": "BSD-3-Clause",
        },
        {
            "name": "numpy",
            "version": "2.4.6",
            "direct": True,
            "wheel_filename": "numpy-2.4.6-cp311-cp311-win_amd64.whl",
            "sha256": "1E254A00CDF42B1E4D5B3D68D33AF63268D41340D8885DF2AB6470F2E1500147",
            "license": "BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0",
        },
        {
            "name": "scikit-learn",
            "version": "1.8.0",
            "direct": True,
            "wheel_filename": "scikit_learn-1.8.0-cp311-cp311-win_amd64.whl",
            "sha256": "C57B1B610BD1F40BA43970E11CE62821C2E6569E4D74023DB19C6B26F246CB3B",
            "license": "BSD-3-Clause",
        },
        {
            "name": "scipy",
            "version": "1.17.1",
            "direct": True,
            "wheel_filename": "scipy-1.17.1-cp311-cp311-win_amd64.whl",
            "sha256": "D30E57C72013C2A4FE441C2FCB8E77B14E152AD48B5464858E07E2AD9FBFCEFF",
            "license": "BSD-3-Clause",
        },
        {
            "name": "threadpoolctl",
            "version": "3.6.0",
            "direct": False,
            "wheel_filename": "threadpoolctl-3.6.0-py3-none-any.whl",
            "sha256": "43A0B8FD5A2928500110039E43A5EED8480B918967083EA48DC3AB9F13C4A7FB",
            "license": "BSD-3-Clause",
        },
    ],
    "network_during_evaluation_allowed": False,
    "product_dependency_manifest_influence_allowed": False,
}

CREMA_SOURCE_BINDING_FIELDS = (
    "finished_responses_sha256",
    "summary_table_sha256",
    "raw_join_field",
    "raw_modality_field",
    "raw_audio_modality",
    "raw_label_field",
    "summary_join_field",
    "summary_label_field",
)
CLASS_ORDER = ("A", "D", "F", "H", "N", "S")
MODEL_KEYS = ("class_prior", "sentence_id", "acoustic")
COVERAGE_TARGETS = (1.0, 0.8, 0.6)
COVERAGE_TARGET_KEYS = tuple(str(value) for value in COVERAGE_TARGETS)
MINIMUM_UNIQUE_ACTORS = 10
AMI_PARTITION_CELLS = ("scenario_only", "full_corpus", "full_only")
AMI_BUCKET_KEYS = (
    "turn_duration_ms_median",
    "turn_duration_ms_p90",
    "inter_turn_gap_ms_median",
    "inter_turn_gap_ms_p90",
)
AMI_SCALAR_KEYS = (
    "overlap_ratio",
    "floor_changes_per_minute",
    "speaker_balance_normalized_entropy",
    "backchannels_per_100_turns",
)
AMI_V2_TIMING_SCALAR_KEYS = (
    "overlap_ratio",
    "speaker_balance_normalized_entropy",
)
AMI_DIALOGUE_ACT_VOCABULARY = (
    "ami_da_1",
    "ami_da_2",
    "ami_da_3",
    "ami_da_4",
    "ami_da_5",
    "ami_da_6",
    "ami_da_7",
    "ami_da_8",
    "ami_da_9",
    "ami_da_11",
    "ami_da_12",
    "ami_da_13",
    "ami_da_14",
    "ami_da_15",
    "ami_da_16",
)
BOOTSTRAP_RESAMPLES = 2000
VALIDITY_KEYS = (
    "material_valid",
    "environment_valid",
    "split_valid",
    "leakage_free",
    "deterministic",
    "lockbox_valid",
)
EXPECTED_PHASE_A_BINDING = {
    "commit": "f8ba503c3670fec6e9dee53f03f306798e7b807b",
    "result_sha256": "EED96BADBE916A38107A4289AD951F8953A5A96215E063890E07F054C7A90931",
    "report_sha256": "724C81C41C489B9BBAB0896009DE7CAB578F77082F230F78B90B65643586FE8A",
}
EXPECTED_DATASET_EVIDENCE = {
    "crema_d": {
        "dataset_id": "crema-d-v1.0-audio-wav",
        "source_revision": "f3b8611a309886568dfa957141775b2e05add04a",
        "manifest_sha256": "6E86F06358E4AD172C72BE1692CFF37291D9D5763DD7F6F5C7CE7405E7E01248",
        "hash_inventory_sha256": "AD58D8165C683847DF246F923FF466722C7F628FE8D81679F618FA5EB3031C87",
        "quality_inventory_sha256": "455D6A010855F209B4DC4C67F67E4222FAB81601861745B5B5E79E7942B92682",
    },
    "ami": {
        "dataset_id": "ami-manual-annotations-v1.6.2",
        "archive_sha256": "B56E5BABB2496B8795DEEEDA7E71178D7FBC9963F94276CF2A3F4B56EBBC9F9D",
        "manifest_sha256": "3904D4A3A9EDF53B06A65354E02FBE1BDD44361B5E196FC6DD4A3882C74911DE",
        "hash_inventory_sha256": "CE7F837A2A44DFEE44691C4BA8B5B0D7766E46D6616986CF565A6300056DEAEE",
        "quality_inventory_sha256": "A376A6C0D5F89770525936299717F1595B743489B593DC4E5CE88AB08ACB22C9",
    },
}
EXPECTED_RAW_CSV_SHA256 = {
    "finishedResponses.csv": "939D02D2DDDDDF575BBCCFFB80F14F1D110FDA88F092F2A68201994EB3BCB45B",
    "processedResults/summaryTable.csv": "1EA0E13D98853D920C7C51E69A72BA5BA42018F85A9B89B8B2CC1B53C1AA56A9",
}
EXPECTED_PUBLIC_RAW_SOURCE_SHA256 = {
    "finished_response_votes": EXPECTED_RAW_CSV_SHA256["finishedResponses.csv"],
    "summary_voice_votes": EXPECTED_RAW_CSV_SHA256[
        "processedResults/summaryTable.csv"
    ],
}
EXPECTED_METRIC_DEFINITIONS = {
    "primary": "paired_actor_cluster_macro_f1_lift",
    "secondary": [
        "balanced_accuracy",
        "per_class_recall",
        "multiclass_brier",
        "log_loss",
        "ece_10_equal_width_bins",
        "retained_macro_f1_at_1.0_0.8_0.6_coverage",
    ],
    "bootstrap_resamples": 2000,
    "bootstrap_unit": "actor_cluster",
    "minimum_unique_actors_per_published_cell": 10,
}
EXPECTED_SLICE_DEFINITIONS = {
    "balanced_diagnostic": {
        "source_label": list(CLASS_ORDER),
        "scripted_scenario_count": 12,
        "vote_agreement_bins": [
            "[0.00,0.50)",
            "[0.50,0.75)",
            "[0.75,1.00]",
        ],
        "silence_ratio_quartiles": 4,
    },
    "demographic_slices_allowed": False,
}
EXPECTED_VALIDITY = {key: True for key in VALIDITY_KEYS}
EXPECTED_STATIC_FILE_SHA256 = {
    "configuration_sha256": "BBB16BDB1205255B0D1C3F0F33891ECC75C4F074D0E6D7200D09A6B385CFE914",
    "environment_lock_sha256": "F78229E8C84B90DB0EB4487CA37949940D13D9AB30A95B5148081CC1B8F60DE3",
    "feature_schema_sha256": "81B55B25F405A99ED7B29449631CFD39B2FE6E1D4F500ADA3BBCD8668790AB75",
    "split_schema_sha256": "6086D63E0796AA5F3FED7F7130F307264DE0BD9B299D2203249FB6268BAD399A",
}
EXPECTED_EVIDENCE_IDENTITY_SHA256 = {
    "configuration_sha256": "24E2186A3ACB19817BF87689F09A2F069AC07B5C1D669364D5FC08BC9AD5FA8F",
    "environment_lock_sha256": "ECAE7C41E8310C52AA62846EDB7F966F5CD05DFF2FD3635C0070B71B8AB7673C",
    "feature_schema_sha256": "70A5B1531D5127D37FD89B30F03EC14682B0B6C97850A5452DEEB59033618EF4",
    "split_schema_sha256": "CA1551AC5664391406920D117E21CA1E413F71C96EF29FEC76FA22DCB8D37E9A",
}
PROVENANCE_KEYS = (
    "schema_id",
    "partition_role",
    "configuration_sha256",
    "environment_lock_sha256",
    "feature_schema_sha256",
    "split_schema_sha256",
    "split_manifest_sha256",
    "assignment_sha256",
    "row_commitment_sha256",
    "actor_commitment_sha256",
    "label_input_commitment_sha256",
    "sentence_commitment_sha256",
    "feature_input_commitment_sha256",
    "upstream_acoustic_source_commitment_sha256",
    "model_class_commitment_sha256",
    "case_count",
    "unique_actor_count",
    "self_sha256",
)
MODEL_METRIC_KEYS = (
    "suppressed",
    "unique_actor_count",
    "case_count",
    "macro_f1",
    "balanced_accuracy",
    "per_class_recall",
    "multiclass_brier",
    "log_loss",
    "ece_10_bin",
    "retained",
)


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


def _reject_non_finite(value: Any) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("non-finite JSON number")
    if isinstance(value, Mapping):
        for nested_value in value.values():
            _reject_non_finite(nested_value)
    if isinstance(value, (list, tuple)):
        for nested_value in value:
            _reject_non_finite(nested_value)


def _exact_keys(value: Any, keys: tuple[Any, ...], name: str) -> Mapping[Any, Any]:
    if not isinstance(value, Mapping) or set(value) != set(keys):
        raise ValueError(f"{name} keys do not match frozen contract")
    return value


def _finite_float(value: Any, name: str) -> float:
    if type(value) is not float or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite float")
    return value


def _count(value: Any, name: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _positive_count(value: Any, name: str) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def canonical_payload_sha256(payload: Mapping[str, Any]) -> str:
    if not isinstance(payload, Mapping):
        raise ValueError("self-hashed payload must be a mapping")
    unsigned = dict(payload)
    unsigned.pop("self_sha256", None)
    _reject_non_finite(unsigned)
    try:
        canonical = json.dumps(
            unsigned,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError) as error:
        raise ValueError("payload is not canonically serializable") from error
    return hashlib.sha256(canonical).hexdigest().upper()


def canonical_artifact_mint_sha256(payload: Mapping[str, Any]) -> str:
    """Hash the complete sealed artifact payload, including self_sha256."""
    if not isinstance(payload, Mapping):
        raise ValueError("minted artifact payload must be a mapping")
    _reject_non_finite(payload)
    try:
        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError) as error:
        raise ValueError(
            "minted artifact payload is not canonically serializable"
        ) from error
    return hashlib.sha256(canonical).hexdigest().upper()


def validate_payload_self_hash(payload: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        raise ValueError(f"{name} must be a mapping")
    _reject_non_finite(payload)
    digest = payload.get("self_sha256")
    if (
        type(digest) is not str
        or re.fullmatch(r"[0-9A-F]{64}", digest) is None
        or digest != canonical_payload_sha256(payload)
    ):
        raise ValueError(f"{name} self hash does not match canonical payload")
    return payload


def validate_provenance_payload(
    payload: Any,
    *,
    expected_role: str | None = None,
) -> Mapping[str, Any]:
    _exact_keys(payload, PROVENANCE_KEYS, "provenance")
    validate_payload_self_hash(payload, "provenance")
    if payload["schema_id"] != "emotion-state-phase-b-partition-evidence-v1":
        raise ValueError("provenance schema does not match")
    role = validate_partition_role(
        payload["partition_role"],
        (
            "training_discovery",
            "calibration",
            "balanced_diagnostic",
            "final_lockbox",
        ),
    )
    if expected_role is not None and role != expected_role:
        raise ValueError(f"provenance must have {expected_role} partition role")
    for key in PROVENANCE_KEYS:
        if key.endswith("_sha256"):
            value = payload[key]
            if (
                type(value) is not str
                or re.fullmatch(r"[0-9A-F]{64}", value) is None
            ):
                raise ValueError(f"provenance {key} is invalid")
    cases = _positive_count(payload["case_count"], "provenance case count")
    actors = _positive_count(
        payload["unique_actor_count"],
        "provenance actor count",
    )
    if actors > cases:
        raise ValueError("provenance actors cannot exceed cases")
    return payload


def _uppercase_sha256(value: Any, name: str) -> str:
    if type(value) is not str or re.fullmatch(r"[0-9A-F]{64}", value) is None:
        raise ValueError(f"{name} must be uppercase SHA-256")
    return value


def validate_probability_evidence_payload(
    payload: Any,
    *,
    expected_role: str | None = None,
) -> Mapping[str, Any]:
    _exact_keys(
        payload,
        (
            "schema_id",
            "partition_role",
            "model_order",
            "class_order",
            "case_count",
            "probability_commitment_sha256",
            "partition_evidence_mint_sha256",
            "provenance",
            "fitted_model_evidence_mint_sha256",
            "training_evidence_mint_sha256",
            "training_provenance",
            "model_state_sha256",
            "self_sha256",
        ),
        "probability evidence",
    )
    validate_payload_self_hash(payload, "probability evidence")
    if payload["schema_id"] != "emotion-state-phase-b-probability-evidence-v1":
        raise ValueError("probability evidence schema does not match")
    role = validate_partition_role(
        payload["partition_role"],
        (
            "training_discovery",
            "calibration",
            "balanced_diagnostic",
            "final_lockbox",
        ),
    )
    if expected_role is not None and role != expected_role:
        raise ValueError(f"probability evidence must have {expected_role} role")
    if tuple(payload["model_order"]) != MODEL_KEYS:
        raise ValueError("probability evidence model order does not match")
    validate_class_order(payload["class_order"])
    case_count = _positive_count(
        payload["case_count"],
        "probability evidence case count",
    )
    for key in (
        "probability_commitment_sha256",
        "partition_evidence_mint_sha256",
        "fitted_model_evidence_mint_sha256",
        "training_evidence_mint_sha256",
        "model_state_sha256",
    ):
        _uppercase_sha256(payload[key], f"probability evidence {key}")
    provenance = validate_provenance_payload(
        payload["provenance"],
        expected_role=role,
    )
    training = validate_provenance_payload(
        payload["training_provenance"],
        expected_role="training_discovery",
    )
    if (
        payload["partition_evidence_mint_sha256"]
        != canonical_artifact_mint_sha256(provenance)
    ):
        raise ValueError(
            "probability partition evidence mint does not match provenance"
        )
    if (
        payload["training_evidence_mint_sha256"]
        != canonical_artifact_mint_sha256(training)
    ):
        raise ValueError(
            "probability training evidence mint does not match provenance"
        )
    if provenance["case_count"] != case_count:
        raise ValueError("probability evidence cases do not match provenance")
    for key in (
        "configuration_sha256",
        "environment_lock_sha256",
        "feature_schema_sha256",
        "split_schema_sha256",
        "split_manifest_sha256",
        "assignment_sha256",
        "model_class_commitment_sha256",
    ):
        if provenance[key] != training[key]:
            raise ValueError("probability evidence shared lineage does not match")
    return payload


def validate_class_order(class_order: Any) -> tuple[str, ...]:
    if tuple(class_order) != CLASS_ORDER:
        raise ValueError("class order does not match A,D,F,H,N,S")
    return CLASS_ORDER


def validate_partition_role(role: Any, allowed: tuple[str, ...]) -> str:
    if type(role) is not str or role not in allowed:
        raise ValueError(
            "partition role must be exactly " + " or ".join(allowed)
        )
    return role


def validate_fit_inputs(
    training_features: Any,
    training_sentences: Any,
    training_labels: Any,
    seed: Any,
    *,
    partition_role: Any,
    class_order: Any,
) -> tuple[Any, Any, Any, int]:
    import numpy as np

    validate_partition_role(partition_role, ("training_discovery",))
    validate_class_order(class_order)
    if (
        not isinstance(training_features, np.ndarray)
        or training_features.dtype != np.dtype(np.float64)
        or training_features.ndim != 2
        or training_features.shape[1] != len(FEATURE_NAMES)
        or training_features.shape[0] == 0
    ):
        raise ValueError("training feature array shape or dtype is invalid")
    if not np.isfinite(training_features).all():
        raise ValueError("training feature array must be finite")
    if (
        not isinstance(training_sentences, np.ndarray)
        or training_sentences.ndim != 1
        or training_sentences.dtype.kind != "U"
        or training_sentences.shape[0] != training_features.shape[0]
        or any(not str(value).strip() for value in training_sentences.tolist())
    ):
        raise ValueError("training sentence array shape or values are invalid")
    if (
        not isinstance(training_labels, np.ndarray)
        or training_labels.ndim != 1
        or training_labels.dtype.kind != "U"
        or training_labels.shape[0] != training_features.shape[0]
        or set(training_labels.tolist()) != set(CLASS_ORDER)
    ):
        raise ValueError("training label array must contain exactly A,D,F,H,N,S")
    if type(seed) is not int or not 0 <= seed <= 0xFFFFFFFF:
        raise ValueError("model seed must be a 32-bit non-negative integer")
    return training_features, training_sentences, training_labels, seed


def validate_probability_inputs(
    probabilities: Any,
    *,
    class_order: Any,
    expected_rows: int | None = None,
) -> tuple[dict[str, Any], int]:
    import numpy as np

    validate_class_order(class_order)
    _exact_keys(probabilities, MODEL_KEYS, "model")
    validated: dict[str, Any] = {}
    row_count = expected_rows
    for key in MODEL_KEYS:
        array = probabilities[key]
        if (
            not isinstance(array, np.ndarray)
            or array.dtype != np.dtype(np.float64)
            or array.ndim != 2
            or array.shape[1] != len(CLASS_ORDER)
            or array.shape[0] == 0
        ):
            raise ValueError("probability array shape or dtype is invalid")
        if row_count is None:
            row_count = int(array.shape[0])
        if array.shape[0] != row_count:
            raise ValueError("probability array shape does not match rows")
        if not np.isfinite(array).all():
            raise ValueError("probability arrays must be finite")
        if np.any(array < 0.0) or np.any(array > 1.0):
            raise ValueError("probability values must be within zero and one")
        if not np.allclose(
            array.sum(axis=1),
            np.ones(array.shape[0], dtype=np.float64),
            rtol=0.0,
            atol=1e-12,
        ):
            raise ValueError("probability row sum does not equal one")
        validated[key] = array
    assert row_count is not None
    return validated, row_count


def validate_labels_and_actors(
    labels: Any,
    actor_ids: Any,
    *,
    expected_rows: int,
) -> tuple[Any, tuple[str, ...]]:
    import numpy as np

    if (
        not isinstance(labels, np.ndarray)
        or labels.ndim != 1
        or labels.dtype.kind != "U"
        or labels.shape[0] != expected_rows
        or any(value not in CLASS_ORDER for value in labels.tolist())
    ):
        raise ValueError("label array shape, class order, or values are invalid")
    if isinstance(actor_ids, (str, bytes)) or not isinstance(actor_ids, Sequence):
        raise ValueError("actor IDs must be a sequence")
    actors = tuple(actor_ids)
    if (
        len(actors) != expected_rows
        or any(
            type(actor) is not str
            or not actor
            or actor.strip() != actor
            for actor in actors
        )
    ):
        raise ValueError("actor IDs do not match frozen row contract")
    return labels, actors


def validate_calibration_result(payload: Any) -> Mapping[str, Any]:
    _exact_keys(
        payload,
        (
            "schema_id",
            "partition_role",
            "class_order",
            "targets",
            "models",
            "probability_evidence_mint_sha256",
            "probability_evidence",
            "provenance",
            "self_sha256",
        ),
        "calibration result",
    )
    validate_payload_self_hash(payload, "calibration result")
    if payload["schema_id"] != "emotion-state-phase-b-calibration-v1":
        raise ValueError("calibration result schema does not match")
    validate_partition_role(payload["partition_role"], ("calibration",))
    provenance = validate_provenance_payload(
        payload["provenance"],
        expected_role="calibration",
    )
    probability = validate_probability_evidence_payload(
        payload["probability_evidence"],
        expected_role="calibration",
    )
    _uppercase_sha256(
        payload["probability_evidence_mint_sha256"],
        "calibration probability evidence mint",
    )
    if (
        payload["probability_evidence_mint_sha256"]
        != canonical_artifact_mint_sha256(probability)
    ):
        raise ValueError(
            "calibration probability evidence mint does not match payload"
        )
    if probability["provenance"] != provenance:
        raise ValueError("calibration probability provenance does not match")
    if payload["partition_role"] != provenance["partition_role"]:
        raise ValueError("calibration provenance partition role does not match")
    validate_class_order(payload["class_order"])
    if tuple(payload["targets"]) != COVERAGE_TARGETS:
        raise ValueError("calibration targets do not match frozen contract")
    _exact_keys(payload["models"], MODEL_KEYS, "calibration model")
    for model in MODEL_KEYS:
        cells = _exact_keys(
            payload["models"][model],
            COVERAGE_TARGET_KEYS,
            "threshold",
        )
        previous_threshold = -1.0
        for target, target_key in zip(COVERAGE_TARGETS, COVERAGE_TARGET_KEYS):
            cell = _exact_keys(
                cells[target_key],
                ("threshold", "achieved_coverage"),
                "threshold",
            )
            threshold = _finite_float(cell["threshold"], "threshold")
            coverage = _finite_float(
                cell["achieved_coverage"],
                "threshold achieved coverage",
            )
            if not 0.0 <= threshold <= 1.0:
                raise ValueError("threshold is outside zero and one")
            if not target <= coverage <= 1.0:
                raise ValueError("threshold achieved coverage is invalid")
            if threshold < previous_threshold:
                raise ValueError("threshold order is invalid")
            previous_threshold = threshold
    return payload


def _validate_metric_models(models: Any) -> Mapping[str, Any]:
    _exact_keys(models, MODEL_KEYS, "metric model")
    for model in MODEL_KEYS:
        metric = _exact_keys(models[model], MODEL_METRIC_KEYS, "metric")
        suppressed = metric["suppressed"]
        if type(suppressed) is not bool:
            raise ValueError("metric suppression flag is invalid")
        actor_count = _positive_count(
            metric["unique_actor_count"],
            "metric actor count",
        )
        case_count = _positive_count(metric["case_count"], "metric case count")
        if actor_count > case_count:
            raise ValueError("metric actors cannot exceed cases")
        for key in (
            "macro_f1",
            "balanced_accuracy",
            "multiclass_brier",
            "log_loss",
            "ece_10_bin",
        ):
            value = metric[key]
            if suppressed:
                if value is not None:
                    raise ValueError("suppressed metric must not emit a value")
            else:
                numeric = _finite_float(value, f"metric {key}")
                if key in (
                    "macro_f1",
                    "balanced_accuracy",
                    "ece_10_bin",
                ) and not 0.0 <= numeric <= 1.0:
                    raise ValueError(f"metric {key} must be within [0,1]")
                if key == "multiclass_brier" and not 0.0 <= numeric <= 2.0:
                    raise ValueError(
                        "metric multiclass_brier must be within [0,2]"
                    )
                if key == "log_loss" and numeric < 0.0:
                    raise ValueError("metric log_loss must be non-negative")
        if suppressed != (actor_count < MINIMUM_UNIQUE_ACTORS):
            raise ValueError("metric suppression does not match actor floor")
        class_cells = _exact_keys(
            metric["per_class_recall"],
            CLASS_ORDER,
            "per-class recall",
        )
        class_case_total = 0
        for label in CLASS_ORDER:
            cell = _exact_keys(
                class_cells[label],
                ("suppressed", "unique_actor_count", "case_count", "recall"),
                "per-class recall",
            )
            cell_actors = _count(
                cell["unique_actor_count"],
                "per-class recall actor count",
            )
            cell_cases = _count(
                cell["case_count"],
                "per-class recall case count",
            )
            class_case_total += cell_cases
            if cell_actors > actor_count:
                raise ValueError(
                    "per-class class actors cannot exceed model actors"
                )
            if cell_actors > cell_cases or cell_cases > case_count:
                raise ValueError(
                    "per-class recall actors/cases exceed model cases"
                )
            if type(cell["suppressed"]) is not bool:
                raise ValueError("per-class recall suppression flag is invalid")
            if cell["suppressed"] != (cell_actors < MINIMUM_UNIQUE_ACTORS):
                raise ValueError("per-class recall actor floor is invalid")
            if cell["suppressed"]:
                if cell["recall"] is not None:
                    raise ValueError("suppressed recall must not emit zero")
            else:
                recall = _finite_float(cell["recall"], "per-class recall")
                if not 0.0 <= recall <= 1.0:
                    raise ValueError("per-class recall is outside zero and one")
        if class_case_total != case_count:
            raise ValueError("six per-class class cases must sum to model cases")
        retained = _exact_keys(
            metric["retained"],
            COVERAGE_TARGET_KEYS,
            "retained metric",
        )
        for target_key in COVERAGE_TARGET_KEYS:
            cell = _exact_keys(
                retained[target_key],
                (
                    "threshold",
                    "calibration_achieved_coverage",
                    "coverage",
                    "suppressed",
                    "unique_actor_count",
                    "case_count",
                    "retained_macro_f1",
                ),
                "retained metric",
            )
            for key in (
                "threshold",
                "calibration_achieved_coverage",
                "coverage",
            ):
                value = _finite_float(cell[key], f"retained metric {key}")
                if not 0.0 <= value <= 1.0:
                    raise ValueError(f"retained metric {key} is invalid")
            retained_actors = _count(
                cell["unique_actor_count"],
                "retained actor count",
            )
            retained_cases = _count(
                cell["case_count"],
                "retained case count",
            )
            coverage = cell["coverage"]
            if not math.isclose(
                coverage,
                retained_cases / case_count,
                rel_tol=0.0,
                abs_tol=1e-15,
            ):
                raise ValueError(
                    "retained coverage must equal retained cases / model cases"
                )
            if retained_cases == 0 and not (
                retained_actors == 0
                and cell["suppressed"] is True
                and cell["retained_macro_f1"] is None
            ):
                raise ValueError(
                    "zero retained cases require zero retained actors, "
                    "suppression, and absent metric"
                )
            if (
                retained_actors > retained_cases
                or retained_actors > actor_count
                or retained_cases > case_count
            ):
                raise ValueError(
                    "retained actors/cases cannot exceed total model counts"
                )
            if type(cell["suppressed"]) is not bool:
                raise ValueError("retained suppression flag is invalid")
            if cell["suppressed"] != (
                retained_actors < MINIMUM_UNIQUE_ACTORS
            ):
                raise ValueError("retained actor floor is invalid")
            if cell["suppressed"]:
                if cell["retained_macro_f1"] is not None:
                    raise ValueError("suppressed retained metric must be absent")
            else:
                retained_f1 = _finite_float(
                    cell["retained_macro_f1"],
                    "retained macro-F1",
                )
                if not 0.0 <= retained_f1 <= 1.0:
                    raise ValueError(
                        "retained macro-F1 must be within [0,1]"
                    )
    count_pairs = {
        (
            models[model]["unique_actor_count"],
            models[model]["case_count"],
        )
        for model in MODEL_KEYS
    }
    if len(count_pairs) != 1:
        raise ValueError("cross-model actor/case counts do not match")
    return models


def validate_evaluation_result(
    payload: Any,
    *,
    expected_role: str | None = None,
) -> Mapping[str, Any]:
    _exact_keys(
        payload,
        (
            "schema_id",
            "partition_role",
            "class_order",
            "models",
            "final_decision_eligible",
            "probability_evidence_mint_sha256",
            "probability_evidence",
            "calibration_evidence_mint_sha256",
            "calibration_evidence",
            "provenance",
            "self_sha256",
        ),
        "evaluation result",
    )
    validate_payload_self_hash(payload, "evaluation result")
    if payload["schema_id"] != "emotion-state-phase-b-evaluation-v1":
        raise ValueError("evaluation result schema does not match")
    role = validate_partition_role(
        payload["partition_role"],
        ("balanced_diagnostic", "final_lockbox"),
    )
    if expected_role is not None and role != expected_role:
        raise ValueError(f"evaluation result must have {expected_role} provenance")
    provenance = validate_provenance_payload(
        payload["provenance"],
        expected_role=role,
    )
    probability = validate_probability_evidence_payload(
        payload["probability_evidence"],
        expected_role=role,
    )
    calibration = validate_calibration_result(
        payload["calibration_evidence"]
    )
    _uppercase_sha256(
        payload["probability_evidence_mint_sha256"],
        "evaluation probability evidence mint",
    )
    _uppercase_sha256(
        payload["calibration_evidence_mint_sha256"],
        "evaluation calibration evidence mint",
    )
    if (
        payload["probability_evidence_mint_sha256"]
        != canonical_artifact_mint_sha256(probability)
    ):
        raise ValueError(
            "evaluation probability evidence mint does not match payload"
        )
    if (
        payload["calibration_evidence_mint_sha256"]
        != canonical_artifact_mint_sha256(calibration)
    ):
        raise ValueError(
            "evaluation calibration evidence mint does not match payload"
        )
    if probability["provenance"] != provenance:
        raise ValueError("evaluation probability provenance does not match")
    for key in (
        "fitted_model_evidence_mint_sha256",
        "training_evidence_mint_sha256",
        "training_provenance",
        "model_state_sha256",
    ):
        if (
            probability[key]
            != calibration["probability_evidence"][key]
        ):
            raise ValueError("evaluation calibration shared lineage does not match")
    if provenance["partition_role"] != role:
        raise ValueError("evaluation provenance partition role does not match")
    validate_class_order(payload["class_order"])
    if payload["final_decision_eligible"] is not (role == "final_lockbox"):
        raise ValueError("diagnostic evaluation cannot produce a final decision")
    models = _validate_metric_models(payload["models"])
    expected_counts = (
        provenance["unique_actor_count"],
        provenance["case_count"],
    )
    if any(
        (
            models[model]["unique_actor_count"],
            models[model]["case_count"],
        ) != expected_counts
        for model in MODEL_KEYS
    ):
        raise ValueError("evaluation counts do not match provenance")
    for model in MODEL_KEYS:
        for target_key in COVERAGE_TARGET_KEYS:
            retained = models[model]["retained"][target_key]
            bound = calibration["models"][model][target_key]
            if (
                retained["threshold"] != bound["threshold"]
                or retained["calibration_achieved_coverage"]
                != bound["achieved_coverage"]
            ):
                raise ValueError(
                    "retained cell does not match exact bound calibration"
                )
    return payload


def validate_bootstrap_result(payload: Any) -> Mapping[str, Any]:
    _exact_keys(
        payload,
        (
            "schema_id",
            "partition_role",
            "class_order",
            "resamples",
            "seed",
            "configuration_sha256",
            "unique_actor_count",
            "case_count",
            "paired_macro_f1_lift",
            "probability_evidence_mint_sha256",
            "probability_evidence",
            "provenance",
            "self_sha256",
        ),
        "bootstrap result",
    )
    validate_payload_self_hash(payload, "bootstrap result")
    if payload["schema_id"] != "emotion-state-phase-b-bootstrap-v1":
        raise ValueError("bootstrap result schema does not match")
    validate_partition_role(payload["partition_role"], ("final_lockbox",))
    validate_class_order(payload["class_order"])
    if payload["resamples"] != BOOTSTRAP_RESAMPLES:
        raise ValueError("bootstrap requires exactly 2,000 resamples")
    if type(payload["seed"]) is not int or payload["seed"] < 0:
        raise ValueError("bootstrap seed is invalid")
    digest = payload["configuration_sha256"]
    if type(digest) is not str or re.fullmatch(r"[0-9A-F]{64}", digest) is None:
        raise ValueError("bootstrap configuration SHA-256 is invalid")
    if payload["seed"] != int(digest[:16], 16):
        raise ValueError("bootstrap seed does not match configuration SHA-256")
    actor_count = _positive_count(
        payload["unique_actor_count"],
        "bootstrap actor count",
    )
    case_count = _positive_count(payload["case_count"], "bootstrap case count")
    if actor_count > case_count:
        raise ValueError("bootstrap actors cannot exceed cases")
    provenance = validate_provenance_payload(
        payload["provenance"],
        expected_role="final_lockbox",
    )
    probability = validate_probability_evidence_payload(
        payload["probability_evidence"],
        expected_role="final_lockbox",
    )
    _uppercase_sha256(
        payload["probability_evidence_mint_sha256"],
        "bootstrap probability evidence mint",
    )
    if (
        payload["probability_evidence_mint_sha256"]
        != canonical_artifact_mint_sha256(probability)
    ):
        raise ValueError(
            "bootstrap probability evidence mint does not match payload"
        )
    if probability["provenance"] != provenance:
        raise ValueError("bootstrap probability provenance does not match")
    if (
        provenance["unique_actor_count"],
        provenance["case_count"],
    ) != (actor_count, case_count):
        raise ValueError("bootstrap counts do not match provenance")
    if provenance["configuration_sha256"] != digest:
        raise ValueError("bootstrap configuration does not match provenance")
    lifts = _exact_keys(
        payload["paired_macro_f1_lift"],
        ("class_prior", "sentence_id"),
        "bootstrap lift",
    )
    for baseline in lifts:
        cell = _exact_keys(
            lifts[baseline],
            ("point_estimate", "lower_95", "upper_95"),
            "bootstrap interval",
        )
        point = _finite_float(cell["point_estimate"], "bootstrap point estimate")
        lower = _finite_float(cell["lower_95"], "bootstrap lower interval")
        upper = _finite_float(cell["upper_95"], "bootstrap upper interval")
        if any(not -1.0 <= value <= 1.0 for value in (point, lower, upper)):
            raise ValueError("bootstrap lift values must be within [-1,1]")
        if lower > upper:
            raise ValueError("bootstrap lower interval exceeds upper interval")
    return payload


def validate_decision_inputs(
    metrics: Any,
    validity: Any,
) -> tuple[Mapping[str, Any], Mapping[str, bool]]:
    _exact_keys(
        metrics,
        (
            "schema_id",
            "partition_role",
            "class_order",
            "final_decision_eligible",
            "models",
            "paired_macro_f1_lift",
            "sentence_driven_apparent_lift",
            "eligible_slice_reversal",
            "eligible_slice_instability",
            "confidence_abstention_improves",
            "evaluation_evidence_mint_sha256",
            "bootstrap_evidence_mint_sha256",
            "slice_analysis_mint_sha256",
            "calibration_evidence_mint_sha256",
            "calibration_evidence",
            "provenance",
            "self_sha256",
        ),
        "metric",
    )
    validate_payload_self_hash(metrics, "decision evidence")
    if metrics["schema_id"] != "emotion-state-phase-b-decision-evidence-v1":
        raise ValueError("metric schema does not match frozen contract")
    validate_partition_role(metrics["partition_role"], ("final_lockbox",))
    validate_class_order(metrics["class_order"])
    provenance = validate_provenance_payload(
        metrics["provenance"],
        expected_role="final_lockbox",
    )
    for key in (
        "evaluation_evidence_mint_sha256",
        "bootstrap_evidence_mint_sha256",
        "slice_analysis_mint_sha256",
        "calibration_evidence_mint_sha256",
    ):
        _uppercase_sha256(metrics[key], f"decision {key}")
    calibration = validate_calibration_result(
        metrics["calibration_evidence"]
    )
    if (
        metrics["calibration_evidence_mint_sha256"]
        != canonical_artifact_mint_sha256(calibration)
    ):
        raise ValueError(
            "decision calibration evidence mint does not match payload"
        )
    if metrics["final_decision_eligible"] is not True:
        raise ValueError("final_lockbox evidence is not decision eligible")
    _validate_metric_models(metrics["models"])
    lifts = _exact_keys(
        metrics["paired_macro_f1_lift"],
        ("class_prior", "sentence_id"),
        "paired lift",
    )
    for baseline in lifts:
        cell = _exact_keys(
            lifts[baseline],
            ("point_estimate", "lower_95", "upper_95"),
            "paired lift",
        )
        point = _finite_float(cell["point_estimate"], "paired lift point")
        lower = _finite_float(cell["lower_95"], "paired lift lower")
        upper = _finite_float(cell["upper_95"], "paired lift upper")
        if any(not -1.0 <= value <= 1.0 for value in (point, lower, upper)):
            raise ValueError("paired lift values must be within [-1,1]")
        if lower > upper:
            raise ValueError("paired lift lower interval exceeds upper interval")
    for key in (
        "sentence_driven_apparent_lift",
        "eligible_slice_reversal",
        "eligible_slice_instability",
        "confidence_abstention_improves",
    ):
        if type(metrics[key]) is not bool:
            raise ValueError(f"metric {key} must be boolean")
    models = metrics["models"]
    expected_counts = (
        provenance["unique_actor_count"],
        provenance["case_count"],
    )
    if any(
        (
            models[model]["unique_actor_count"],
            models[model]["case_count"],
        ) != expected_counts
        for model in MODEL_KEYS
    ):
        raise ValueError(
            "decision cross-model counts do not match provenance"
        )
    if any(models[model]["suppressed"] for model in MODEL_KEYS):
        raise ValueError("decision metrics cannot use suppressed model cells")
    if any(
        models["acoustic"]["per_class_recall"][label]["suppressed"]
        for label in CLASS_ORDER
    ):
        raise ValueError("decision metrics cannot use suppressed recall cells")
    for baseline in ("class_prior", "sentence_id"):
        expected_point = (
            models["acoustic"]["macro_f1"] - models[baseline]["macro_f1"]
        )
        actual_point = lifts[baseline]["point_estimate"]
        if not math.isclose(
            actual_point,
            expected_point,
            rel_tol=0.0,
            abs_tol=1e-15,
        ):
            raise ValueError(
                "paired lift point estimate does not match final-lockbox metrics"
            )
    expected_sentence_driven = (
        models["sentence_id"]["macro_f1"]
        > models["class_prior"]["macro_f1"]
        and lifts["sentence_id"]["point_estimate"] <= 0.0
    )
    if (
        metrics["sentence_driven_apparent_lift"]
        is not expected_sentence_driven
    ):
        raise ValueError("sentence-driven lift flag is not derived")
    acoustic = models["acoustic"]
    abstention_candidates = [
        acoustic["retained"][target_key]
        for target_key in ("0.8", "0.6")
        if (
            not acoustic["retained"][target_key]["suppressed"]
            and acoustic["retained"][target_key]["coverage"] < 1.0
        )
    ]
    expected_confidence = (
        bool(abstention_candidates)
        and any(
            cell["retained_macro_f1"] > acoustic["macro_f1"]
            for cell in abstention_candidates
        )
        and all(
            cell["retained_macro_f1"] >= acoustic["macro_f1"]
            for cell in abstention_candidates
        )
    )
    if (
        metrics["confidence_abstention_improves"]
        is not expected_confidence
    ):
        raise ValueError("confidence abstention flag is not derived")
    for model in MODEL_KEYS:
        for target_key in COVERAGE_TARGET_KEYS:
            retained = models[model]["retained"][target_key]
            bound = calibration["models"][model][target_key]
            if (
                retained["threshold"] != bound["threshold"]
                or retained["calibration_achieved_coverage"]
                != bound["achieved_coverage"]
            ):
                raise ValueError(
                    "decision retained cell does not match bound calibration"
                )
    _exact_keys(validity, VALIDITY_KEYS, "validity")
    if any(type(validity[key]) is not bool for key in VALIDITY_KEYS):
        raise ValueError("validity values must be booleans")
    return metrics, validity


def _matches_expected(actual: Any, expected: Any) -> bool:
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        return (
            actual.keys() == expected.keys()
            and all(_matches_expected(actual[key], value) for key, value in expected.items())
        )
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(
            _matches_expected(item, expected_item)
            for item, expected_item in zip(actual, expected)
        )
    return actual == expected


def _validate_exact(payload: Any, expected: dict[str, Any], name: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError(f"{name} must be an object")
    if not _matches_expected(payload, expected):
        raise ValueError(f"{name} does not match frozen contract")
    return payload


def load_json_strict(path: Path) -> dict[str, Any]:
    value = json.loads(
        Path(path).read_text(encoding="utf-8"),
        object_pairs_hook=_pairs,
        parse_constant=_constant,
    )
    if not isinstance(value, dict):
        raise ValueError("JSON root must be an object")
    _reject_non_finite(value)
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
    for field, expected in EXPECTED_FEATURE_NUMERICAL_SEMANTICS.items():
        if payload.get(field) != expected:
            raise ValueError(
                f"feature numerical semantic {field} does not match"
            )
    return _validate_exact(payload, EXPECTED_FEATURE_SCHEMA, "feature schema")


def validate_split_schema(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("split schema must be an object")
    if payload.get("partition_actor_counts") != PARTITION_COUNTS:
        raise ValueError("partition actor counts do not match")
    if payload.get("dependency_roles", {}).get("speaker") != "exclusion_group":
        raise ValueError("speaker must remain the exclusion group")
    if payload.get("dependency_roles", {}).get("source_corpus") != "scope_constant":
        raise ValueError("source corpus must remain a scope constant")
    if payload.get("runtime_influence_allowed") is not False:
        raise ValueError("runtime influence must remain disabled")
    return _validate_exact(payload, EXPECTED_SPLIT_SCHEMA, "split schema")


def validate_config(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("config must be an object")
    if payload.get("checkpoint_id") != "EMOTION-STATE-002-phase-b-public-data-feasibility":
        raise ValueError("checkpoint identity does not match")
    boundaries = payload.get("boundaries")
    if not isinstance(boundaries, dict) or any(value is not False for value in boundaries.values()):
        raise ValueError("runtime influence and every external boundary must remain disabled")
    return _validate_exact(payload, EXPECTED_CONFIG, "config")


def validate_environment_lock(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("environment lock must be an object")
    distributions = payload.get("distributions")
    if not isinstance(distributions, list) or not distributions:
        raise ValueError("environment lock distributions must be non-empty")
    expected_distributions = EXPECTED_ENVIRONMENT_LOCK["distributions"]
    if len(distributions) != len(expected_distributions):
        raise ValueError("environment lock distribution set does not match")
    for actual, expected in zip(distributions, expected_distributions):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise ValueError("environment lock distribution fields do not match")
        if actual.get("name") != expected["name"]:
            raise ValueError("environment lock distribution name does not match")
        for field in ("version", "direct", "wheel_filename", "sha256", "license"):
            if actual.get(field) != expected[field]:
                raise ValueError(
                    f"environment lock distribution {field} does not match"
                )
    if payload.get("direct_requirements") != [
        "numpy",
        "scipy",
        "scikit-learn",
    ]:
        raise ValueError("environment lock direct requirements do not match")
    if payload.get("network_during_evaluation_allowed") is not False:
        raise ValueError("network during evaluation must remain disabled")
    if payload.get("product_dependency_manifest_influence_allowed") is not False:
        raise ValueError("product dependency manifest influence must remain disabled")
    return _validate_exact(
        payload,
        EXPECTED_ENVIRONMENT_LOCK,
        "environment lock",
    )


def _normalize_distribution_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _current_interpreter_platform() -> str:
    implementation_platform = (
        sysconfig.get_platform().lower().replace("-", "_").replace(".", "_")
    )
    pointer_bits = struct.calcsize("P") * 8
    if (
        sys.platform == "win32"
        and implementation_platform == "win_amd64"
        and pointer_bits == 64
    ):
        return "win_amd64"
    return f"{sys.platform}:{implementation_platform}:{pointer_bits}"


def _installed_distributions() -> dict[str, str]:
    installed: dict[str, str] = {}
    for distribution in importlib.metadata.distributions():
        raw_name = distribution.metadata["Name"]
        if type(raw_name) is not str or not raw_name:
            raise ValueError("installed distribution is missing a name")
        version = distribution.version
        if type(version) is not str or not version:
            raise ValueError("installed distribution is missing a version")
        name = _normalize_distribution_name(raw_name)
        if name in installed:
            raise ValueError("installed distributions contain duplicate names")
        installed[name] = version
    return installed


def _validate_installed_distributions(
    lock: Mapping[str, Any],
    installed_distributions: Mapping[str, str],
) -> dict[str, str]:
    expected_installed = {
        distribution["name"]: distribution["version"]
        for distribution in lock["distributions"]
    }
    normalized_installed: dict[str, str] = {}
    for raw_name, version in installed_distributions.items():
        if type(raw_name) is not str or type(version) is not str:
            raise ValueError(
                "installed distribution names and versions must be exact strings"
            )
        name = _normalize_distribution_name(raw_name)
        if name in normalized_installed:
            raise ValueError("installed distributions contain duplicate names")
        normalized_installed[name] = version
    if normalized_installed != expected_installed:
        raise ValueError("installed distributions do not match environment lock")
    return dict(sorted(normalized_installed.items()))


def _normalized_absolute_path(value: str | os.PathLike[str]) -> str:
    return os.path.normcase(os.path.abspath(os.path.normpath(os.fspath(value))))


def validate_installed_environment_identity() -> dict[str, Any]:
    """Validate only process-local interpreter and installed metadata."""
    expected_root = _normalized_absolute_path(ROOT)
    expected_python = _normalized_absolute_path(EVALUATION_PYTHON_PATH)
    actual_python = _normalized_absolute_path(sys.executable)
    try:
        expected_relative = os.path.relpath(expected_python, expected_root)
    except ValueError as error:
        raise ValueError(
            "fixed evaluation Python is outside the project root"
        ) from error
    if (
        expected_relative == os.pardir
        or expected_relative.startswith(os.pardir + os.sep)
    ):
        raise ValueError("fixed evaluation Python is outside the project root")
    if actual_python.casefold() != expected_python.casefold():
        raise ValueError("evaluation Python executable does not match fixed path")
    actual_python_version = (
        sys.version_info.major,
        sys.version_info.minor,
    )
    if actual_python_version != (3, 11):
        raise ValueError("evaluation Python version must be 3.11")
    actual_platform = _current_interpreter_platform()
    if actual_platform != EXPECTED_ENVIRONMENT_LOCK["platform"]:
        raise ValueError(
            "evaluation Python platform does not match environment lock: "
            f"{actual_platform}"
        )
    normalized_installed = _validate_installed_distributions(
        EXPECTED_ENVIRONMENT_LOCK,
        _installed_distributions(),
    )
    return {
        "python_executable": actual_python,
        "python_version": ".".join(
            str(value) for value in actual_python_version
        ),
        "platform": actual_platform,
        "installed_distributions": normalized_installed,
    }


def _load_json_object_bytes_strict(content: bytes, name: str) -> dict[str, Any]:
    if type(content) is not bytes:
        raise ValueError(f"{name} bytes must be exact bytes")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"{name} bytes must be valid UTF-8") from error
    try:
        value = json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_constant=_constant,
        )
    except (json.JSONDecodeError, ValueError) as error:
        raise ValueError(f"{name} bytes are not strict JSON: {error}") from error
    if type(value) is not dict:
        raise ValueError(f"{name} root must be an object")
    _reject_non_finite(value)
    return value


def validate_environment_identity_bytes(
    lock_bytes: bytes,
    wheel_bytes: Mapping[str, bytes],
) -> dict[str, Any]:
    """Validate held environment sources without performing path reads."""
    lock = validate_environment_lock(
        _load_json_object_bytes_strict(lock_bytes, "environment lock")
    )
    if (
        type(wheel_bytes) is not dict
        or any(type(name) is not str for name in wheel_bytes)
        or any(type(content) is not bytes for content in wheel_bytes.values())
    ):
        raise ValueError("wheel bytes must be an exact filename-to-bytes mapping")
    expected_filenames = {
        distribution["wheel_filename"]
        for distribution in EXPECTED_ENVIRONMENT_LOCK["distributions"]
    }
    if set(wheel_bytes) != expected_filenames:
        raise ValueError("wheel set does not match environment lock")
    wheel_hashes: dict[str, str] = {}
    for distribution in EXPECTED_ENVIRONMENT_LOCK["distributions"]:
        filename = distribution["wheel_filename"]
        digest = hashlib.sha256(wheel_bytes[filename]).hexdigest().upper()
        if digest != distribution["sha256"]:
            raise ValueError(
                f"wheel hash does not match environment lock: {filename}"
            )
        wheel_hashes[filename] = digest
    return {
        "environment_lock": copy.deepcopy(lock),
        "wheel_count": len(wheel_hashes),
        "wheel_hashes": wheel_hashes,
    }


def validate_environment_identity(
    *,
    lock_path: Path,
    wheelhouse_path: Path,
) -> dict[str, Any]:
    installed_report = validate_installed_environment_identity()
    lock_file = Path(lock_path)
    if not lock_file.is_file():
        raise ValueError("environment lock is missing")
    wheelhouse = Path(wheelhouse_path)
    wheels = {
        path.name: path
        for path in wheelhouse.iterdir()
        if path.is_file()
    } if wheelhouse.is_dir() else {}
    byte_report = validate_environment_identity_bytes(
        lock_file.read_bytes(),
        {name: path.read_bytes() for name, path in wheels.items()},
    )
    return {
        **installed_report,
        "wheel_count": byte_report["wheel_count"],
        "wheel_hashes": byte_report["wheel_hashes"],
    }


def validate_crema_source_binding(
    source_binding: Any,
    contract: Mapping[str, Any],
) -> None:
    if not isinstance(contract, Mapping):
        raise ValueError("CREMA-D source binding contract must be a mapping")
    try:
        expected_binding = {
            field: contract[field] for field in CREMA_SOURCE_BINDING_FIELDS
        }
    except KeyError as error:
        raise ValueError("CREMA-D source binding contract is incomplete") from error
    if not _matches_expected(source_binding, expected_binding):
        raise ValueError("CREMA-D source binding does not match frozen contract")


def _ami_canonical_identifier(value: Any, name: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} identifier must be a string")
    canonical = unicodedata.normalize("NFC", value.strip())
    if (
        not canonical
        or any(
            character.isspace()
            or unicodedata.category(character).startswith("C")
            for character in canonical
        )
    ):
        raise ValueError(f"{name} identifier is not canonical")
    return canonical


def _ami_canonical_identifiers(
    values: Sequence[str],
    name: str,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"{name} must be a sequence")
    canonical = tuple(
        _ami_canonical_identifier(value, name.rstrip("s"))
        for value in values
    )
    if not canonical or len(set(canonical)) != len(canonical):
        raise ValueError(f"{name} must contain unique canonical identifiers")
    return canonical


def _ami_canonical_dialogue_act(value: Any) -> str:
    if type(value) is not str:
        raise ValueError("AMI dialogue-act vocabulary label must be a string")
    canonical = unicodedata.normalize("NFC", value.strip().lower())
    if canonical not in AMI_DIALOGUE_ACT_VOCABULARY:
        raise ValueError("AMI dialogue-act vocabulary label is not allowed")
    return canonical


def _ami_validated_meetings(
    meetings: Sequence[Any],
) -> tuple[dict[str, Any], ...]:
    if isinstance(meetings, (str, bytes)) or not isinstance(meetings, Sequence):
        raise ValueError("authoritative AMI meetings must be a sequence")
    validated: list[dict[str, Any]] = []
    for meeting in meetings:
        try:
            meeting_id = _ami_canonical_identifier(
                meeting.meeting_id,
                "meeting",
            )
            participants = tuple(sorted(set(
                _ami_canonical_identifiers(
                    meeting.participants,
                    "participant identifiers",
                )
            )))
            raw_values = meeting.values
            raw_distribution = meeting.dialogue_act_distribution
        except AttributeError as error:
            raise ValueError(
                "authoritative AMI meeting record is incomplete"
            ) from error
        if len(participants) < 2:
            raise ValueError(
                "authoritative AMI meeting needs two canonical participants"
            )
        if (
            type(raw_values) is not tuple
            or any(
                type(pair) is not tuple or len(pair) != 2
                for pair in raw_values
            )
            or tuple(key for key, _ in raw_values)
            != AMI_BUCKET_KEYS + AMI_SCALAR_KEYS
            or any(
                type(value) is not float or not math.isfinite(value)
                for _, value in raw_values
            )
        ):
            raise ValueError("authoritative AMI metric values are invalid")
        values = dict(raw_values)
        if any(values[key] < 0.0 for key in AMI_BUCKET_KEYS):
            raise ValueError("authoritative AMI timing bucket is invalid")
        if not 0.0 <= values["overlap_ratio"] <= 1.0:
            raise ValueError("authoritative AMI overlap ratio is invalid")
        if values["floor_changes_per_minute"] < 0.0:
            raise ValueError("authoritative AMI floor-change rate is invalid")
        if not 0.0 <= values[
            "speaker_balance_normalized_entropy"
        ] <= 1.0:
            raise ValueError("authoritative AMI speaker balance is invalid")
        if not 0.0 <= values["backchannels_per_100_turns"] <= 100.0:
            raise ValueError("authoritative AMI backchannel rate is invalid")
        if (
            type(raw_distribution) is not tuple
            or not raw_distribution
            or any(
                type(pair) is not tuple or len(pair) != 2
                for pair in raw_distribution
            )
        ):
            raise ValueError(
                "authoritative AMI dialogue-act distribution is invalid"
            )
        distribution = tuple(sorted(
            (
                _ami_canonical_dialogue_act(label),
                value,
            )
            for label, value in raw_distribution
        ))
        if (
            len({label for label, _ in distribution}) != len(distribution)
            or any(
                type(value) is not float
                or not math.isfinite(value)
                or not 0.0 <= value <= 1.0
                for _, value in distribution
            )
            or not math.isclose(
                sum(value for _, value in distribution),
                1.0,
                rel_tol=0.0,
                abs_tol=1e-12,
            )
        ):
            raise ValueError(
                "authoritative AMI dialogue-act distribution is invalid"
            )
        validated.append({
            "meeting_id": meeting_id,
            "participants": participants,
            "values": tuple(raw_values),
            "dialogue_act_distribution": distribution,
        })
    identifiers = [meeting["meeting_id"] for meeting in validated]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("duplicate authoritative AMI meeting identifier")
    return tuple(validated)


def _ami_meeting_digest(meeting: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        {
            "meeting_id": meeting["meeting_id"],
            "participants": meeting["participants"],
            "values": meeting["values"],
            "dialogue_act_distribution": meeting[
                "dialogue_act_distribution"
            ],
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _ami_aggregate_cell(
    value: float,
    participant_count: int,
    minimum_contributors: int,
) -> dict[str, Any]:
    suppressed = participant_count < minimum_contributors
    return {
        "suppressed": suppressed,
        "unique_participant_count": participant_count,
        "value": None if suppressed else float(value),
    }


def _expected_ami_mechanics_aggregates(
    meetings: Sequence[Any],
    partition_membership: Mapping[str, Sequence[str]],
    official_order: Sequence[str],
    minimum_contributors: int,
) -> dict[str, Any]:
    if type(minimum_contributors) is not int or minimum_contributors < 10:
        raise ValueError("AMI minimum contributors must be at least 10")
    validated = _ami_validated_meetings(meetings)
    by_id = {meeting["meeting_id"]: meeting for meeting in validated}
    if not isinstance(partition_membership, Mapping) or set(
        partition_membership
    ) != set(AMI_PARTITION_CELLS):
        raise ValueError("authoritative AMI partition fields are invalid")
    order = _ami_canonical_identifiers(
        official_order,
        "official meeting order",
    )
    if set(order) != set(by_id):
        raise ValueError(
            "authoritative AMI official order does not match meetings"
        )
    order_index = {
        meeting_id: index
        for index, meeting_id in enumerate(order)
    }
    expected: dict[str, Any] = {}
    for partition_name in AMI_PARTITION_CELLS:
        member_ids = _ami_canonical_identifiers(
            partition_membership[partition_name],
            f"{partition_name} membership",
        )
        unknown = set(member_ids) - set(by_id)
        if unknown:
            raise ValueError(
                "authoritative AMI partition references unknown meeting: "
                f"{sorted(unknown)[0]}"
            )
        candidates = sorted(
            (by_id[meeting_id] for meeting_id in member_ids),
            key=lambda meeting: (
                order_index[meeting["meeting_id"]],
                _ami_meeting_digest(meeting),
            ),
        )
        selected: list[Mapping[str, Any]] = []
        participants: set[str] = set()
        repeated = 0
        for meeting in candidates:
            if participants.intersection(meeting["participants"]):
                repeated += 1
                continue
            selected.append(meeting)
            participants.update(meeting["participants"])
        participant_count = len(participants)
        value_maps = [
            dict(meeting["values"])
            for meeting in selected
        ]
        aggregate_values = {
            key: sum(values[key] for values in value_maps) / len(value_maps)
            for key in AMI_BUCKET_KEYS + AMI_SCALAR_KEYS
        }
        dialogue_acts = sorted({
            label
            for meeting in selected
            for label, _ in meeting["dialogue_act_distribution"]
        })
        distributions = [
            dict(meeting["dialogue_act_distribution"])
            for meeting in selected
        ]
        dialogue_values = {
            label: sum(
                distribution.get(label, 0.0)
                for distribution in distributions
            ) / len(distributions)
            for label in dialogue_acts
        }
        suppressed = participant_count < minimum_contributors
        expected[partition_name] = {
            "meeting_count": len(selected),
            "unique_participant_count": participant_count,
            "scalars": {
                key: _ami_aggregate_cell(
                    aggregate_values[key],
                    participant_count,
                    minimum_contributors,
                )
                for key in AMI_SCALAR_KEYS
            },
            "buckets": {
                key: _ami_aggregate_cell(
                    aggregate_values[key],
                    participant_count,
                    minimum_contributors,
                )
                for key in AMI_BUCKET_KEYS
            },
            "dialogue_acts": {
                key: _ami_aggregate_cell(
                    value,
                    participant_count,
                    minimum_contributors,
                )
                for key, value in dialogue_values.items()
            },
            "suppression_counts": {
                "repeated_participant_meetings": repeated,
                "scalar_cells": (
                    len(AMI_SCALAR_KEYS) if suppressed else 0
                ),
                "bucket_cells": (
                    len(AMI_BUCKET_KEYS) if suppressed else 0
                ),
                "dialogue_act_cells": (
                    len(dialogue_acts) if suppressed else 0
                ),
            },
        }
    return expected


def validate_ami_mechanics_aggregates(
    payload: Any,
    *,
    meetings: Sequence[Any],
    partition_membership: Mapping[str, Sequence[str]],
    official_order: Sequence[str],
    minimum_contributors: int = 10,
) -> Mapping[str, Any]:
    partitions = _exact_keys(
        payload,
        AMI_PARTITION_CELLS,
        "AMI aggregate fields",
    )
    for partition_name in AMI_PARTITION_CELLS:
        partition = _exact_keys(
            partitions[partition_name],
            (
                "meeting_count",
                "unique_participant_count",
                "scalars",
                "buckets",
                "dialogue_acts",
                "suppression_counts",
            ),
            "AMI partition fields",
        )
        _exact_keys(
            partition["scalars"],
            AMI_SCALAR_KEYS,
            "AMI scalar fields",
        )
        _exact_keys(
            partition["buckets"],
            AMI_BUCKET_KEYS,
            "AMI bucket fields",
        )
        dialogue_acts = partition["dialogue_acts"]
        if not isinstance(dialogue_acts, Mapping) or not dialogue_acts:
            raise ValueError("AMI dialogue-act fields are invalid")
        for label in dialogue_acts:
            if label != _ami_canonical_dialogue_act(label):
                raise ValueError(
                    "AMI dialogue-act vocabulary key is not canonical"
                )
        for group_name in ("scalars", "buckets", "dialogue_acts"):
            for cell in partition[group_name].values():
                _exact_keys(
                    cell,
                    ("suppressed", "unique_participant_count", "value"),
                    f"AMI {group_name} cell fields",
                )
        _exact_keys(
            partition["suppression_counts"],
            (
                "repeated_participant_meetings",
                "scalar_cells",
                "bucket_cells",
                "dialogue_act_cells",
            ),
            "AMI suppression-count fields",
        )
    expected = _expected_ami_mechanics_aggregates(
        meetings,
        partition_membership,
        official_order,
        minimum_contributors,
    )
    if not _matches_expected(partitions, expected):
        raise ValueError(
            "AMI aggregate does not match authoritative synthetic evidence"
        )
    return partitions


def _ami_v2_exact_mapping(
    value: Any,
    keys: tuple[str, ...],
    name: str,
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != set(keys):
        raise ValueError(f"{name} keys do not match the v2 contract")
    return value


def _ami_v2_matches_expected(actual: Any, expected: Any) -> bool:
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        return (
            actual.keys() == expected.keys()
            and all(
                _ami_v2_matches_expected(actual[key], value)
                for key, value in expected.items()
            )
        )
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(
            _ami_v2_matches_expected(item, expected_item)
            for item, expected_item in zip(actual, expected)
        )
    if isinstance(expected, float):
        return (
            math.isfinite(actual)
            and math.isfinite(expected)
            and actual == expected
            and (
                actual != 0.0
                or math.copysign(1.0, actual)
                == math.copysign(1.0, expected)
            )
        )
    return actual == expected


def _ami_v2_exact_identifier(value: Any, name: str) -> str:
    canonical = _ami_canonical_identifier(value, name)
    if value != canonical:
        raise ValueError(f"{name} identifier is not exactly canonical")
    return canonical


def _ami_v2_identifier_sequence(
    values: Any,
    name: str,
    *,
    require_list: bool = False,
) -> tuple[str, ...]:
    if (
        (require_list and type(values) is not list)
        or isinstance(values, (str, bytes))
        or not isinstance(values, Sequence)
    ):
        raise ValueError(f"{name} must be a sequence")
    identifiers = tuple(
        _ami_v2_exact_identifier(value, name.rstrip("s"))
        for value in values
    )
    if not identifiers or len(set(identifiers)) != len(identifiers):
        raise ValueError(f"{name} must contain unique canonical identifiers")
    return identifiers


def _ami_v2_serialized_turn(
    value: Any,
    *,
    meeting_id: str,
    participants: tuple[str, ...],
    dialogue: bool,
) -> dict[str, Any]:
    keys = (
        (
            "meeting_id",
            "participant_id",
            "start_ms",
            "end_ms",
            "dialogue_act",
        )
        if dialogue
        else (
            "meeting_id",
            "participant_id",
            "start_ms",
            "end_ms",
        )
    )
    turn = _ami_v2_exact_mapping(value, keys, "AMI v2 serialized turn")
    turn_meeting_id = _ami_v2_exact_identifier(
        turn["meeting_id"],
        "timed-turn meeting",
    )
    participant_id = _ami_v2_exact_identifier(
        turn["participant_id"],
        "timed-turn participant",
    )
    if turn_meeting_id != meeting_id:
        raise ValueError("AMI v2 serialized turn crosses meeting identity")
    if participant_id not in participants:
        raise ValueError(
            "AMI v2 serialized turn references an unknown participant"
        )
    start_ms = turn["start_ms"]
    end_ms = turn["end_ms"]
    if (
        type(start_ms) is not int
        or type(end_ms) is not int
        or not 0 <= start_ms < end_ms
    ):
        raise ValueError("AMI v2 serialized turn span is malformed")
    validated = {
        "meeting_id": turn_meeting_id,
        "participant_id": participant_id,
        "start_ms": start_ms,
        "end_ms": end_ms,
    }
    if dialogue:
        dialogue_act = _ami_canonical_dialogue_act(turn["dialogue_act"])
        if turn["dialogue_act"] != dialogue_act:
            raise ValueError(
                "AMI v2 serialized dialogue-act label is not canonical"
            )
        validated["dialogue_act"] = dialogue_act
    return validated


def _ami_v2_serialized_turns(
    value: Any,
    *,
    meeting_id: str,
    participants: tuple[str, ...],
    dialogue: bool,
) -> tuple[dict[str, Any], ...] | None:
    if value is None:
        return None
    if type(value) is not list or not value:
        raise ValueError(
            "AMI v2 serialized turns must be a non-empty list or null"
        )
    turns = tuple(
        _ami_v2_serialized_turn(
            turn,
            meeting_id=meeting_id,
            participants=participants,
            dialogue=dialogue,
        )
        for turn in value
    )
    order_keys = (
        ("start_ms", "end_ms", "participant_id", "dialogue_act")
        if dialogue
        else ("start_ms", "end_ms", "participant_id")
    )
    key = lambda turn: tuple(turn[field] for field in order_keys)
    if turns != tuple(sorted(turns, key=key)):
        raise ValueError("AMI v2 serialized turn order is ambiguous")
    if len({key(turn) for turn in turns}) != len(turns):
        raise ValueError("AMI v2 serialized turns contain an exact duplicate")
    if not dialogue and len({
        turn["participant_id"]
        for turn in turns
    }) < 2:
        raise ValueError(
            "AMI v2 usable timing requires two represented participants"
        )
    return turns


def _ami_v2_serialized_meetings(
    meetings: Sequence[Any],
) -> tuple[dict[str, Any], ...]:
    if isinstance(meetings, (str, bytes)) or not isinstance(
        meetings,
        Sequence,
    ):
        raise ValueError("AMI v2 serialized meetings must be a sequence")
    validated: list[dict[str, Any]] = []
    meeting_keys = (
        "meeting_id",
        "participants",
        "timing_file_present",
        "timed_turns",
        "dialogue_turns",
        "dialogue_act_file_count",
        "fully_labeled_dialogue_act_file_count",
        "unlabeled_dialogue_act_record_count",
        "unlabeled_dialogue_act_file_count",
    )
    for value in meetings:
        meeting = _ami_v2_exact_mapping(
            value,
            meeting_keys,
            "AMI v2 serialized meeting",
        )
        meeting_id = _ami_v2_exact_identifier(
            meeting["meeting_id"],
            "AMI v2 meeting",
        )
        participants = _ami_v2_identifier_sequence(
            meeting["participants"],
            "AMI v2 participants",
            require_list=True,
        )
        if (
            len(participants) < 2
            or participants != tuple(sorted(participants))
        ):
            raise ValueError(
                "AMI v2 participants must be unique, ordered, and plural"
            )
        timing_file_present = meeting["timing_file_present"]
        if type(timing_file_present) is not bool:
            raise ValueError(
                "AMI v2 timing-file presence must be a boolean"
            )
        timed_turns = _ami_v2_serialized_turns(
            meeting["timed_turns"],
            meeting_id=meeting_id,
            participants=participants,
            dialogue=False,
        )
        if timed_turns is not None and not timing_file_present:
            raise ValueError(
                "AMI v2 timed turns require a present timing source file"
            )
        dialogue_turns = _ami_v2_serialized_turns(
            meeting["dialogue_turns"],
            meeting_id=meeting_id,
            participants=participants,
            dialogue=True,
        )
        count_names = (
            "dialogue_act_file_count",
            "fully_labeled_dialogue_act_file_count",
            "unlabeled_dialogue_act_record_count",
            "unlabeled_dialogue_act_file_count",
        )
        counts: dict[str, int] = {}
        for name in count_names:
            count = meeting[name]
            if type(count) is not int or count < 0:
                raise ValueError(
                    f"AMI v2 {name} must be a non-negative integer"
                )
            counts[name] = count
        file_count = counts["dialogue_act_file_count"]
        fully_labeled_count = counts[
            "fully_labeled_dialogue_act_file_count"
        ]
        unlabeled_record_count = counts[
            "unlabeled_dialogue_act_record_count"
        ]
        unlabeled_file_count = counts[
            "unlabeled_dialogue_act_file_count"
        ]
        if fully_labeled_count > file_count:
            raise ValueError(
                "AMI v2 fully labeled dialogue files exceed total files"
            )
        if unlabeled_file_count > file_count:
            raise ValueError(
                "AMI v2 unlabeled dialogue files exceed total files"
            )
        if unlabeled_record_count < unlabeled_file_count:
            raise ValueError(
                "AMI v2 unlabeled records cannot be fewer than files"
            )
        incomplete_file_count = file_count - fully_labeled_count
        if unlabeled_file_count != incomplete_file_count:
            raise ValueError(
                "AMI v2 incomplete dialogue files require unlabeled records"
            )
        if incomplete_file_count == 0 and unlabeled_record_count != 0:
            raise ValueError(
                "AMI v2 unlabeled counts require an incomplete file"
            )
        if dialogue_turns is not None and (
            file_count == 0 or incomplete_file_count != 0
        ):
            raise ValueError(
                "AMI v2 complete dialogue turns require complete evidence"
            )
        validated.append({
            "meeting_id": meeting_id,
            "participants": participants,
            "timing_file_present": timing_file_present,
            "timed_turns": timed_turns,
            "dialogue_turns": dialogue_turns,
            **counts,
        })
    identifiers = [meeting["meeting_id"] for meeting in validated]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("duplicate AMI v2 serialized meeting identifier")
    return tuple(validated)


def _ami_v2_linear_percentile(
    values: Sequence[int | float],
    percentile: float,
) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * percentile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + fraction * (
        ordered[upper] - ordered[lower]
    )


def _ami_v2_overlap_duration(
    turns: Sequence[Mapping[str, Any]],
) -> int:
    events: dict[int, list[tuple[str, int]]] = defaultdict(list)
    for turn in turns:
        events[turn["start_ms"]].append((turn["participant_id"], 1))
        events[turn["end_ms"]].append((turn["participant_id"], -1))
    active: Counter[str] = Counter()
    previous: int | None = None
    overlap = 0
    for instant in sorted(events):
        if previous is not None and len(active) >= 2:
            overlap += instant - previous
        for participant, delta in events[instant]:
            active[participant] += delta
            if active[participant] == 0:
                del active[participant]
        previous = instant
    return overlap


def _ami_v2_timing_values(
    turns: tuple[dict[str, Any], ...],
) -> dict[str, float]:
    durations = [
        turn["end_ms"] - turn["start_ms"]
        for turn in turns
    ]
    nonnegative_gaps = [
        gap
        for current, following in zip(turns, turns[1:])
        if (
            gap := following["start_ms"] - current["end_ms"]
        ) >= 0
    ]
    meeting_span = (
        max(turn["end_ms"] for turn in turns)
        - min(turn["start_ms"] for turn in turns)
    )
    speaking_time: Counter[str] = Counter()
    for turn, duration in zip(turns, durations):
        speaking_time[turn["participant_id"]] += duration
    total_speaking_time = sum(speaking_time.values())
    entropy = -sum(
        (duration / total_speaking_time)
        * math.log(duration / total_speaking_time)
        for duration in speaking_time.values()
    )
    normalized_entropy = entropy / math.log(len(speaking_time))
    try:
        values = {
            "turn_duration_ms_median": _ami_v2_linear_percentile(
                durations,
                0.5,
            ),
            "turn_duration_ms_p90": _ami_v2_linear_percentile(
                durations,
                0.9,
            ),
            "inter_turn_gap_ms_median": _ami_v2_linear_percentile(
                nonnegative_gaps,
                0.5,
            ),
            "inter_turn_gap_ms_p90": _ami_v2_linear_percentile(
                nonnegative_gaps,
                0.9,
            ),
            "overlap_ratio": (
                _ami_v2_overlap_duration(turns) / meeting_span
            ),
            "speaker_balance_normalized_entropy": normalized_entropy,
        }
    except OverflowError as error:
        raise ValueError(
            "AMI v2 authority per-meeting timing values must be finite"
        ) from error
    if any(not math.isfinite(value) for value in values.values()):
        raise ValueError(
            "AMI v2 authority per-meeting timing values must be finite"
        )
    return values


def _ami_v2_aggregate_cell(
    value: float,
    participant_count: int,
    minimum_contributors: int,
) -> dict[str, Any]:
    suppressed = participant_count < minimum_contributors
    return {
        "suppressed": suppressed,
        "unique_participant_count": participant_count,
        "value": None if suppressed else float(value),
    }


def _ami_v2_timing_family(
    candidates: tuple[dict[str, Any], ...],
    minimum_contributors: int,
) -> dict[str, Any]:
    coverage = {
        "timing_file_meeting_count": sum(
            meeting["timing_file_present"]
            for meeting in candidates
        ),
        "usable_timing_meeting_count": sum(
            meeting["timed_turns"] is not None
            for meeting in candidates
        ),
    }
    if coverage["usable_timing_meeting_count"] != len(candidates):
        return {
            "status": "unavailable",
            "reason_codes": ["incomplete_usable_timing_coverage"],
            "coverage": coverage,
            "contribution": None,
            "buckets": None,
            "scalars": None,
        }
    selected: list[dict[str, Any]] = []
    contributed: set[str] = set()
    repeated = 0
    for meeting in candidates:
        if contributed.intersection(meeting["participants"]):
            repeated += 1
            continue
        selected.append(meeting)
        contributed.update(meeting["participants"])
    if len(selected) + repeated != len(candidates):
        raise ValueError("AMI v2 timing contribution accounting is invalid")
    participant_count = len(contributed)
    value_maps = [
        _ami_v2_timing_values(meeting["timed_turns"])
        for meeting in selected
        if meeting["timed_turns"] is not None
    ]
    aggregates = {
        key: sum(values[key] for values in value_maps) / len(value_maps)
        for key in AMI_BUCKET_KEYS + AMI_V2_TIMING_SCALAR_KEYS
    }
    if any(not math.isfinite(value) for value in aggregates.values()):
        raise ValueError(
            "AMI v2 authority aggregate timing values must be finite"
        )
    suppressed = participant_count < minimum_contributors
    return {
        "status": "available",
        "reason_codes": [],
        "coverage": coverage,
        "contribution": {
            "selected_meeting_count": len(selected),
            "unique_participant_count": participant_count,
            "repeated_participant_meeting_count": repeated,
            "suppressed": suppressed,
        },
        "buckets": {
            key: _ami_v2_aggregate_cell(
                aggregates[key],
                participant_count,
                minimum_contributors,
            )
            for key in AMI_BUCKET_KEYS
        },
        "scalars": {
            key: _ami_v2_aggregate_cell(
                aggregates[key],
                participant_count,
                minimum_contributors,
            )
            for key in AMI_V2_TIMING_SCALAR_KEYS
        },
    }


def _ami_v2_dialogue_family(
    candidates: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    coverage = {
        "dialogue_act_meeting_count": sum(
            meeting["dialogue_act_file_count"] > 0
            for meeting in candidates
        ),
        "dialogue_act_file_count": sum(
            meeting["dialogue_act_file_count"]
            for meeting in candidates
        ),
        "fully_labeled_dialogue_act_file_count": sum(
            meeting["fully_labeled_dialogue_act_file_count"]
            for meeting in candidates
        ),
    }
    reason_codes: list[str] = []
    if coverage["dialogue_act_meeting_count"] != len(candidates):
        reason_codes.append(
            "incomplete_dialogue_act_meeting_coverage"
        )
    if any(
        meeting["unlabeled_dialogue_act_record_count"] > 0
        or meeting["unlabeled_dialogue_act_file_count"] > 0
        or meeting["fully_labeled_dialogue_act_file_count"]
        != meeting["dialogue_act_file_count"]
        for meeting in candidates
    ):
        reason_codes.append("unlabeled_dialogue_act_records")
    if not reason_codes:
        raise ValueError(
            "AMI v2 available dialogue-act aggregation is not implemented"
        )
    return {
        "status": "unavailable",
        "reason_codes": reason_codes,
        "coverage": coverage,
        "contribution": None,
        "scalars": None,
        "dialogue_acts": None,
    }


def _expected_ami_mechanics_aggregates_v2(
    meetings: Sequence[Any],
    partition_membership: Mapping[str, Sequence[str]],
    official_order: Sequence[str],
    minimum_contributors: int,
) -> dict[str, Any]:
    if (
        type(minimum_contributors) is not int
        or minimum_contributors < 10
    ):
        raise ValueError("AMI v2 minimum contributors must be at least 10")
    validated = _ami_v2_serialized_meetings(meetings)
    by_id = {
        meeting["meeting_id"]: meeting
        for meeting in validated
    }
    if not isinstance(partition_membership, Mapping) or set(
        partition_membership
    ) != set(AMI_PARTITION_CELLS):
        raise ValueError("AMI v2 partition membership fields are invalid")
    membership = {
        partition: _ami_v2_identifier_sequence(
            partition_membership[partition],
            f"{partition} memberships",
        )
        for partition in AMI_PARTITION_CELLS
    }
    scenario = set(membership["scenario_only"])
    full_only = set(membership["full_only"])
    full_corpus = set(membership["full_corpus"])
    if not scenario.isdisjoint(full_only):
        raise ValueError(
            "AMI v2 scenario-only and full-only partitions overlap"
        )
    if scenario | full_only != full_corpus:
        raise ValueError(
            "AMI v2 partition union does not equal the full corpus"
        )
    order = _ami_v2_identifier_sequence(
        official_order,
        "official meeting orders",
    )
    if set(order) != full_corpus:
        raise ValueError(
            "AMI v2 official order does not equal the full corpus"
        )
    if set(by_id) != full_corpus:
        raise ValueError(
            "AMI v2 evidence does not equal the full corpus"
        )
    member_sets = {
        partition: set(meeting_ids)
        for partition, meeting_ids in membership.items()
    }
    partitions: dict[str, Any] = {}
    for partition in AMI_PARTITION_CELLS:
        candidates = tuple(
            by_id[meeting_id]
            for meeting_id in order
            if meeting_id in member_sets[partition]
        )
        partitions[partition] = {
            "population_meeting_count": len(candidates),
            "metric_families": {
                "timing": _ami_v2_timing_family(
                    candidates,
                    minimum_contributors,
                ),
                "dialogue_act": _ami_v2_dialogue_family(candidates),
            },
        }
    return {
        "schema_id": "emotion-state-ami-mechanics-aggregate-v2",
        "schema_version": 2,
        "source_quality": {
            "unlabeled_dialogue_act_record_count": sum(
                meeting["unlabeled_dialogue_act_record_count"]
                for meeting in validated
            ),
            "unlabeled_dialogue_act_file_count": sum(
                meeting["unlabeled_dialogue_act_file_count"]
                for meeting in validated
            ),
        },
        "partitions": partitions,
    }


def validate_ami_mechanics_aggregates_v2(
    payload: Any,
    *,
    meetings: Sequence[Any],
    partition_membership: Mapping[str, Sequence[str]],
    official_order: Sequence[str],
    minimum_contributors: int = 10,
) -> Mapping[str, Any]:
    expected = _expected_ami_mechanics_aggregates_v2(
        meetings,
        partition_membership,
        official_order,
        minimum_contributors,
    )
    if not _ami_v2_matches_expected(payload, expected):
        raise ValueError(
            "AMI v2 aggregate does not match serialized authority"
        )
    return expected


def _validate_published_ami_cell_v2(
    cell: Any,
    *,
    name: str,
    participant_count: int,
    suppressed: bool,
    unit_interval: bool,
) -> None:
    validated = _ami_v2_exact_mapping(
        cell,
        ("suppressed", "unique_participant_count", "value"),
        name,
    )
    if validated["suppressed"] is not suppressed:
        raise ValueError(f"{name} suppression does not match contribution")
    if (
        type(validated["unique_participant_count"]) is not int
        or validated["unique_participant_count"] != participant_count
    ):
        raise ValueError(f"{name} contributor count does not match")
    if suppressed:
        if validated["value"] is not None:
            raise ValueError(f"{name} suppressed value must be null")
        return
    value = validated["value"]
    if type(value) is not float or not math.isfinite(value):
        raise ValueError(f"{name} value must be a finite float")
    if value < 0.0:
        raise ValueError(f"{name} value must be non-negative")
    if unit_interval and not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} value must be within [0,1]")


def validate_published_ami_aggregate_v2(
    payload: Any,
) -> Mapping[str, Any]:
    aggregate = _ami_v2_exact_mapping(
        payload,
        ("schema_id", "schema_version", "source_quality", "partitions"),
        "published AMI v2 aggregate",
    )
    if aggregate["schema_id"] != "emotion-state-ami-mechanics-aggregate-v2":
        raise ValueError("published AMI v2 schema id is invalid")
    if type(aggregate["schema_version"]) is not int or (
        aggregate["schema_version"] != 2
    ):
        raise ValueError("published AMI v2 schema version must be integer 2")
    source_quality = _ami_v2_exact_mapping(
        aggregate["source_quality"],
        (
            "unlabeled_dialogue_act_record_count",
            "unlabeled_dialogue_act_file_count",
        ),
        "published AMI v2 source quality",
    )
    if not _matches_expected(
        source_quality,
        {
            "unlabeled_dialogue_act_record_count": 28,
            "unlabeled_dialogue_act_file_count": 26,
        },
    ):
        raise ValueError(
            "published AMI v2 source quality does not match release"
        )
    partitions = _ami_v2_exact_mapping(
        aggregate["partitions"],
        AMI_PARTITION_CELLS,
        "published AMI v2 partitions",
    )
    fixed = {
        "scenario_only": {
            "population": 138,
            "timing": (138, 138),
            "dialogue": (138, 552, 527),
            "timing_status": ("available", []),
            "dialogue_status": (
                "unavailable",
                ["unlabeled_dialogue_act_records"],
            ),
        },
        "full_corpus": {
            "population": 170,
            "timing": (170, 165),
            "dialogue": (139, 556, 530),
            "timing_status": (
                "unavailable",
                ["incomplete_usable_timing_coverage"],
            ),
            "dialogue_status": (
                "unavailable",
                [
                    "incomplete_dialogue_act_meeting_coverage",
                    "unlabeled_dialogue_act_records",
                ],
            ),
        },
        "full_only": {
            "population": 32,
            "timing": (32, 27),
            "dialogue": (1, 4, 3),
            "timing_status": (
                "unavailable",
                ["incomplete_usable_timing_coverage"],
            ),
            "dialogue_status": (
                "unavailable",
                [
                    "incomplete_dialogue_act_meeting_coverage",
                    "unlabeled_dialogue_act_records",
                ],
            ),
        },
    }
    for partition_name in AMI_PARTITION_CELLS:
        release = fixed[partition_name]
        partition = _ami_v2_exact_mapping(
            partitions[partition_name],
            ("population_meeting_count", "metric_families"),
            f"{partition_name} published AMI v2 partition",
        )
        if (
            type(partition["population_meeting_count"]) is not int
            or partition["population_meeting_count"]
            != release["population"]
        ):
            raise ValueError(
                f"{partition_name} AMI v2 population does not match release"
            )
        families = _ami_v2_exact_mapping(
            partition["metric_families"],
            ("timing", "dialogue_act"),
            f"{partition_name} AMI v2 metric families",
        )
        timing = _ami_v2_exact_mapping(
            families["timing"],
            (
                "status",
                "reason_codes",
                "coverage",
                "contribution",
                "buckets",
                "scalars",
            ),
            f"{partition_name} AMI v2 timing",
        )
        if (
            type(timing["status"]) is not str
            or type(timing["reason_codes"]) is not list
            or (
                timing["status"],
                timing["reason_codes"],
            ) != release["timing_status"]
        ):
            raise ValueError(
                f"{partition_name} AMI v2 timing state is invalid"
            )
        timing_coverage = _ami_v2_exact_mapping(
            timing["coverage"],
            (
                "timing_file_meeting_count",
                "usable_timing_meeting_count",
            ),
            f"{partition_name} AMI v2 timing coverage",
        )
        if not _matches_expected(
            timing_coverage,
            {
                "timing_file_meeting_count": release["timing"][0],
                "usable_timing_meeting_count": release["timing"][1],
            },
        ):
            raise ValueError(
                f"{partition_name} AMI v2 timing coverage is invalid"
            )
        if partition_name == "scenario_only":
            contribution = _ami_v2_exact_mapping(
                timing["contribution"],
                (
                    "selected_meeting_count",
                    "unique_participant_count",
                    "repeated_participant_meeting_count",
                    "suppressed",
                ),
                "scenario AMI v2 timing contribution",
            )
            selected = _positive_count(
                contribution["selected_meeting_count"],
                "scenario AMI v2 selected meeting count",
            )
            repeated = _count(
                contribution["repeated_participant_meeting_count"],
                "scenario AMI v2 repeated meeting count",
            )
            if selected + repeated != release["population"]:
                raise ValueError(
                    "scenario AMI v2 contribution accounting is invalid"
                )
            participant_count = _count(
                contribution["unique_participant_count"],
                "scenario AMI v2 contributor count",
            )
            if participant_count < 2 * selected:
                raise ValueError(
                    "scenario AMI v2 contributor count is impossible"
                )
            suppressed = contribution["suppressed"]
            if (
                type(suppressed) is not bool
                or suppressed is not (participant_count < 10)
            ):
                raise ValueError(
                    "scenario AMI v2 suppression is not derived"
                )
            buckets = _ami_v2_exact_mapping(
                timing["buckets"],
                AMI_BUCKET_KEYS,
                "scenario AMI v2 timing buckets",
            )
            scalars = _ami_v2_exact_mapping(
                timing["scalars"],
                AMI_V2_TIMING_SCALAR_KEYS,
                "scenario AMI v2 timing scalars",
            )
            for name, cell in buckets.items():
                _validate_published_ami_cell_v2(
                    cell,
                    name=f"scenario AMI v2 timing bucket {name}",
                    participant_count=participant_count,
                    suppressed=suppressed,
                    unit_interval=False,
                )
            for name, cell in scalars.items():
                _validate_published_ami_cell_v2(
                    cell,
                    name=f"scenario AMI v2 timing scalar {name}",
                    participant_count=participant_count,
                    suppressed=suppressed,
                    unit_interval=True,
                )
        elif any(
            timing[field] is not None
            for field in ("contribution", "buckets", "scalars")
        ):
            raise ValueError(
                f"{partition_name} unavailable AMI v2 timing must be null"
            )

        dialogue = _ami_v2_exact_mapping(
            families["dialogue_act"],
            (
                "status",
                "reason_codes",
                "coverage",
                "contribution",
                "scalars",
                "dialogue_acts",
            ),
            f"{partition_name} AMI v2 dialogue",
        )
        if (
            type(dialogue["status"]) is not str
            or type(dialogue["reason_codes"]) is not list
            or (
                dialogue["status"],
                dialogue["reason_codes"],
            ) != release["dialogue_status"]
        ):
            raise ValueError(
                f"{partition_name} AMI v2 dialogue state is invalid"
            )
        dialogue_coverage = _ami_v2_exact_mapping(
            dialogue["coverage"],
            (
                "dialogue_act_meeting_count",
                "dialogue_act_file_count",
                "fully_labeled_dialogue_act_file_count",
            ),
            f"{partition_name} AMI v2 dialogue coverage",
        )
        if not _matches_expected(
            dialogue_coverage,
            {
                "dialogue_act_meeting_count": release["dialogue"][0],
                "dialogue_act_file_count": release["dialogue"][1],
                "fully_labeled_dialogue_act_file_count": (
                    release["dialogue"][2]
                ),
            },
        ):
            raise ValueError(
                f"{partition_name} AMI v2 dialogue coverage is invalid"
            )
        if any(
            dialogue[field] is not None
            for field in ("contribution", "scalars", "dialogue_acts")
        ):
            raise ValueError(
                f"{partition_name} unavailable AMI v2 dialogue must be null"
            )
    try:
        return json.loads(json.dumps(
            aggregate,
            ensure_ascii=False,
            allow_nan=False,
        ))
    except (TypeError, ValueError) as error:
        raise ValueError(
            "published AMI v2 aggregate is not JSON serializable"
        ) from error


def validate_crema_label_ledger(ledger: Any, config: Mapping[str, Any]) -> None:
    validated_config = validate_config(config)
    expected_contract = validated_config["crema_label_contract"]
    expected_status_counts = expected_contract["expected_status_counts"]
    expected_label_counts = expected_contract["expected_label_counts"]
    expected_keys = set(expected_status_counts) | {
        "label_counts",
        "included_wav_count",
        "eligible_actor_count",
        "eligible_sentence_count",
        "source_binding",
    }
    if not isinstance(ledger, dict) or set(ledger) != expected_keys:
        raise ValueError("CREMA-D ledger fields do not match frozen contract")
    validate_crema_source_binding(ledger["source_binding"], expected_contract)
    status_counts = {key: ledger[key] for key in expected_status_counts}
    label_counts = ledger["label_counts"]
    aggregate_counts = (
        ledger["included_wav_count"],
        ledger["eligible_actor_count"],
        ledger["eligible_sentence_count"],
    )
    if (
        not all(type(value) is int for value in status_counts.values())
        or not isinstance(label_counts, dict)
        or not all(type(value) is int for value in label_counts.values())
        or not all(type(value) is int for value in aggregate_counts)
    ):
        raise ValueError("CREMA-D ledger counts must be integers")
    if status_counts != expected_status_counts:
        raise ValueError("CREMA-D ledger status counts do not match frozen contract")
    if label_counts != expected_label_counts:
        raise ValueError("CREMA-D ledger label counts do not match frozen contract")
    if sum(status_counts.values()) != 7441:
        raise ValueError("CREMA-D ledger status counts must sum to 7441")
    if ledger["included_wav_count"] != 7441:
        raise ValueError("CREMA-D included WAV count must be 7441")
    if sum(label_counts.values()) != status_counts[
        "eligible_concordant_unique_winner"
    ]:
        raise ValueError("CREMA-D eligible label count does not match status count")
    if ledger["eligible_actor_count"] != 91:
        raise ValueError("CREMA-D eligible actor count must be 91")
    if ledger["eligible_sentence_count"] != 12:
        raise ValueError("CREMA-D eligible sentence count must be 12")


def _require_exact(value: Any, expected: Any, name: str) -> Any:
    if not _matches_expected(value, expected):
        raise ValueError(f"{name} does not match the frozen contract")
    return value


def expected_crema_label_ledger() -> dict[str, Any]:
    contract = EXPECTED_CONFIG["crema_label_contract"]
    return {
        **dict(contract["expected_status_counts"]),
        "label_counts": dict(contract["expected_label_counts"]),
        "included_wav_count": 7441,
        "eligible_actor_count": 91,
        "eligible_sentence_count": 12,
        "source_binding": {
            key: contract[key] for key in CREMA_SOURCE_BINDING_FIELDS
        },
    }


def expected_phase_b_input_ledger() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "phase_a": dict(EXPECTED_PHASE_A_BINDING),
        "dataset_evidence": json.loads(json.dumps(EXPECTED_DATASET_EVIDENCE)),
        "raw_csv_sha256": dict(EXPECTED_RAW_CSV_SHA256),
        "crema_label_ledger": expected_crema_label_ledger(),
    }


def expected_non_lockbox_packet(review_sha256: str) -> dict[str, Any]:
    _uppercase_sha256(review_sha256, "non-lockbox review")
    return {
        "schema_version": 1,
        "review_sha256": review_sha256,
        "model_settings": dict(EXPECTED_CONFIG["model"]),
        "metric_definitions": json.loads(json.dumps(EXPECTED_METRIC_DEFINITIONS)),
        "slice_definitions": json.loads(json.dumps(EXPECTED_SLICE_DEFINITIONS)),
        "minimum_unique_contributors_per_cell": 10,
    }


_PHASE_B_NONFINAL_ROLES = (
    "training_discovery",
    "calibration",
    "balanced_diagnostic",
)
_PHASE_B_ROLE_ACTOR_COUNTS = {
    "training_discovery": 35,
    "calibration": 13,
    "balanced_diagnostic": 13,
}
_PHASE_B_CREMA_LABELS = frozenset({"A", "D", "F", "H", "N", "S"})
_PHASE_B_CREMA_CLIP_PATTERN = re.compile(
    r"^(?P<actor>\d{4})_(?P<sentence>[A-Z0-9]{3})_"
    r"(?:ANG|DIS|FEA|HAP|NEU|SAD)_(?:HI|LO|MD|XX)$"
)


def _phase_b_exact_dict(
    value: Any,
    keys: tuple[str, ...],
    name: str,
) -> dict[str, Any]:
    if (
        type(value) is not dict
        or any(type(key) is not str for key in value)
        or set(value) != set(keys)
    ):
        raise ValueError(f"{name} keys do not match frozen contract")
    return value


def _phase_b_require_exact_json_graph(
    value: Any,
    name: str,
    active_containers: set[int] | None = None,
    depth: int = 0,
) -> None:
    if depth > 128:
        raise ValueError(f"{name} JSON nesting exceeds the validation limit")
    active = set() if active_containers is None else active_containers
    if type(value) is dict:
        identity = id(value)
        if identity in active:
            raise ValueError(f"{name} contains a cyclic JSON container")
        active.add(identity)
        try:
            for key, nested in value.items():
                if type(key) is not str:
                    raise ValueError(
                        f"{name} keys must be exact built-in strings"
                    )
                _phase_b_require_exact_json_graph(
                    nested,
                    name,
                    active,
                    depth + 1,
                )
        finally:
            active.remove(identity)
        return
    if type(value) is list:
        identity = id(value)
        if identity in active:
            raise ValueError(f"{name} contains a cyclic JSON container")
        active.add(identity)
        try:
            for nested in value:
                _phase_b_require_exact_json_graph(
                    nested,
                    name,
                    active,
                    depth + 1,
                )
        finally:
            active.remove(identity)
        return
    if value is None or type(value) in (str, int, bool):
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError(f"{name} contains a non-finite float")
        return
    raise ValueError(f"{name} must contain only exact built-in JSON values")


def _phase_b_canonical_vote_metrics(
    cells: tuple[tuple[str, int], ...],
) -> tuple[float, float]:
    ordered = tuple(sorted(cells, key=lambda cell: cell[0]))
    total = sum(count for _label, count in ordered)
    agreement = max(count for _label, count in ordered) / total
    entropy_terms = (
        (count / total) * math.log2(count / total)
        for _label, count in ordered
        if count
    )
    entropy = -sum(entropy_terms)
    agreement = 0.0 if agreement == 0.0 else float(agreement)
    entropy = 0.0 if entropy == 0.0 else float(entropy)
    return agreement, entropy


def validate_phase_b_split_manifest(payload: Any) -> dict[str, Any]:
    _phase_b_require_exact_json_graph(payload, "validated split manifest")
    manifest = _phase_b_exact_dict(
        copy.deepcopy(payload),
        (
            "schema_id",
            "configuration_sha256",
            "eligible_actor_count",
            "eligible_record_count",
            "eligible_authority_commitment_sha256",
            "assignment_sha256",
            "split_manifest_sha256",
            "partition_authority_sha256",
            "final_lockbox_commitment",
            "self_sha256",
        ),
        "validated split manifest",
    )
    validate_payload_self_hash(manifest, "validated split manifest")
    if (
        type(manifest["schema_id"]) is not str
        or manifest["schema_id"]
        != "emotion-state-phase-b-validated-split-v2"
    ):
        raise ValueError("validated split manifest schema does not match")
    if (
        manifest["configuration_sha256"]
        != EXPECTED_EVIDENCE_IDENTITY_SHA256["configuration_sha256"]
    ):
        raise ValueError("validated split configuration identity does not match")
    if (
        type(manifest["eligible_actor_count"]) is not int
        or manifest["eligible_actor_count"] != 91
    ):
        raise ValueError("validated split actor count must be exactly 91")
    eligible_record_count = _positive_count(
        manifest["eligible_record_count"],
        "validated split record count",
    )
    for field in (
        "eligible_authority_commitment_sha256",
        "assignment_sha256",
        "split_manifest_sha256",
    ):
        _uppercase_sha256(manifest[field], f"validated split {field}")
    authority = _phase_b_exact_dict(
        manifest["partition_authority_sha256"],
        _PHASE_B_NONFINAL_ROLES,
        "non-lockbox partition authority commitments",
    )
    for role, digest in authority.items():
        _uppercase_sha256(digest, f"{role} partition authority")
    final_lockbox = _phase_b_exact_dict(
        manifest["final_lockbox_commitment"],
        (
            "eligible_record_count",
            "eligible_actor_count",
            "sealed_authority_commitment_sha256",
        ),
        "final-lockbox commitment",
    )
    final_record_count = _positive_count(
        final_lockbox["eligible_record_count"],
        "final-lockbox eligible record count",
    )
    if final_record_count >= eligible_record_count:
        raise ValueError(
            "final-lockbox eligible record count must be less than total"
        )
    if (
        type(final_lockbox["eligible_actor_count"]) is not int
        or final_lockbox["eligible_actor_count"] != 30
    ):
        raise ValueError("final-lockbox actor count must be exactly 30")
    _uppercase_sha256(
        final_lockbox["sealed_authority_commitment_sha256"],
        "final-lockbox sealed-authority commitment",
    )
    return copy.deepcopy(manifest)


def validate_phase_b_partition_authority_cache(
    payload: Any,
    split_manifest: Any,
    *,
    expected_role: str,
) -> dict[str, Any]:
    role = validate_partition_role(expected_role, _PHASE_B_NONFINAL_ROLES)
    manifest = validate_phase_b_split_manifest(split_manifest)
    _phase_b_require_exact_json_graph(payload, "partition authority cache")
    cache = _phase_b_exact_dict(
        copy.deepcopy(payload),
        (
            "schema_id",
            "schema_version",
            "partition_role",
            "configuration_sha256",
            "split_manifest_sha256",
            "assignment_sha256",
            "records",
            "self_sha256",
        ),
        "partition authority cache",
    )
    validate_payload_self_hash(cache, "partition authority cache")
    if (
        type(cache["schema_id"]) is not str
        or cache["schema_id"]
        != "emotion-state-phase-b-partition-authority-cache-v2"
    ):
        raise ValueError("partition authority cache schema does not match")
    if type(cache["schema_version"]) is not int or cache["schema_version"] != 2:
        raise ValueError("partition authority cache schema version must be 2")
    if type(cache["partition_role"]) is not str or cache["partition_role"] != role:
        raise ValueError("partition authority cache role does not match")
    for field in (
        "configuration_sha256",
        "split_manifest_sha256",
        "assignment_sha256",
    ):
        _uppercase_sha256(cache[field], f"partition authority cache {field}")
        if cache[field] != manifest[field]:
            raise ValueError(
                f"partition authority cache {field} does not match manifest"
            )
    if cache["self_sha256"] != manifest["partition_authority_sha256"][role]:
        raise ValueError(
            "partition authority cache commitment does not match manifest"
        )

    records = cache["records"]
    if type(records) is not list or not records:
        raise ValueError("partition authority cache records must be a non-empty list")
    previous_stem: str | None = None
    actors: set[str] = set()
    sentences: set[str] = set()
    labels: set[str] = set()
    for index, item in enumerate(records):
        record = _phase_b_exact_dict(
            item,
            (
                "clip_stem",
                "actor_id",
                "sentence_id",
                "label",
                "abstention_reason",
                "vote_distribution",
                "vote_agreement",
                "vote_entropy",
                "audio_sha256",
                "audio_size_bytes",
            ),
            f"partition authority cache record {index}",
        )
        clip_stem = record["clip_stem"]
        actor_id = record["actor_id"]
        sentence_id = record["sentence_id"]
        if (
            type(clip_stem) is not str
            or (match := _PHASE_B_CREMA_CLIP_PATTERN.fullmatch(clip_stem)) is None
            or type(actor_id) is not str
            or type(sentence_id) is not str
            or match.group("actor") != actor_id
            or match.group("sentence") != sentence_id
        ):
            raise ValueError(
                "partition authority cache clip identity does not match record"
            )
        if previous_stem is not None and clip_stem <= previous_stem:
            raise ValueError(
                "partition authority cache records must have unique ascending stems"
            )
        previous_stem = clip_stem
        label = record["label"]
        if (
            type(label) is not str
            or label not in _PHASE_B_CREMA_LABELS
            or record["abstention_reason"] is not None
        ):
            raise ValueError("partition authority cache label record is invalid")
        distribution = record["vote_distribution"]
        if (
            type(distribution) is not list
            or not distribution
            or any(
                type(cell) is not list
                or len(cell) != 2
                or type(cell[0]) is not str
                or cell[0] not in _PHASE_B_CREMA_LABELS
                or type(cell[1]) is not int
                or cell[1] <= 0
                for cell in distribution
            )
        ):
            raise ValueError(
                "partition authority cache vote distribution is invalid"
            )
        cells = tuple((cell[0], cell[1]) for cell in distribution)
        if (
            tuple(sorted(cells, key=lambda cell: cell[0])) != cells
            or len({cell[0] for cell in cells}) != len(cells)
        ):
            raise ValueError(
                "partition authority cache vote distribution is invalid"
            )
        maximum = max(count for _label, count in cells)
        winners = tuple(
            vote_label
            for vote_label, count in cells
            if count == maximum
        )
        if winners != (label,):
            raise ValueError(
                "partition authority cache label does not match unique vote winner"
            )
        agreement = record["vote_agreement"]
        entropy = record["vote_entropy"]
        for value, name in (
            (agreement, "agreement"),
            (entropy, "entropy"),
        ):
            if type(value) is not float or not math.isfinite(value):
                raise ValueError(
                    f"partition authority cache vote {name} is invalid"
                )
            if value == 0.0 and math.copysign(1.0, value) < 0.0:
                raise ValueError(
                    f"partition authority cache vote {name} is negative zero"
                )
        expected_agreement, expected_entropy = (
            _phase_b_canonical_vote_metrics(cells)
        )
        if (
            agreement.hex() != expected_agreement.hex()
            or entropy.hex() != expected_entropy.hex()
        ):
            raise ValueError("partition authority cache vote metrics are invalid")
        _uppercase_sha256(
            record["audio_sha256"],
            "partition authority cache audio SHA-256",
        )
        _positive_count(
            record["audio_size_bytes"],
            "partition authority cache audio size",
        )
        actors.add(actor_id)
        sentences.add(sentence_id)
        labels.add(label)
    if len(actors) != _PHASE_B_ROLE_ACTOR_COUNTS[role]:
        raise ValueError("partition authority cache actor count does not match")
    if len(sentences) != 12:
        raise ValueError("partition authority cache sentence count does not match")
    if labels != set(_PHASE_B_CREMA_LABELS):
        raise ValueError("partition authority cache label coverage does not match")
    return copy.deepcopy(cache)


def validate_phase_b_input_ledger(payload: Any) -> dict[str, Any]:
    ledger = _exact_keys(
        payload,
        (
            "schema_version",
            "phase_a",
            "dataset_evidence",
            "raw_csv_sha256",
            "crema_label_ledger",
        ),
        "Phase B input ledger",
    )
    if ledger["schema_version"] != 1 or type(ledger["schema_version"]) is not int:
        raise ValueError("Phase B input ledger schema version must be 1")
    _require_exact(ledger["phase_a"], EXPECTED_PHASE_A_BINDING, "Phase A binding")
    _require_exact(
        ledger["dataset_evidence"],
        EXPECTED_DATASET_EVIDENCE,
        "dataset evidence",
    )
    _require_exact(
        ledger["raw_csv_sha256"],
        EXPECTED_RAW_CSV_SHA256,
        "raw CSV hashes",
    )
    validate_crema_label_ledger(ledger["crema_label_ledger"], EXPECTED_CONFIG)
    return dict(ledger)


_NON_LOCKBOX_PACKET_V4_KEYS = (
    "schema_id",
    "schema_version",
    "configuration_sha256",
    "split_manifest_sha256",
    "model_settings",
    "metric_definitions",
    "slice_definitions",
    "minimum_unique_contributors_per_cell",
    "lockbox_access",
    "final_decision_eligible",
    "tracked_public_authority_commitment_sha256",
    "diagnostic_aggregate",
    "diagnostic_aggregate_sha256",
    "diagnostic_slice_analysis",
    "diagnostic_slice_analysis_sha256",
    "ami_aggregate",
    "ami_aggregate_sha256",
    "artifact_cache_commitments",
    "artifact_cache_commitments_sha256",
    "review_sha256",
)
_NON_LOCKBOX_SLICE_KEYS = (
    "schema_id",
    "partition_role",
    "class_order",
    "instability_tolerance",
    "slices",
    "eligible_slice_reversal",
    "eligible_slice_instability",
    "probability_evidence_mint_sha256",
    "evaluation_evidence_mint_sha256",
    "provenance",
    "self_sha256",
)
_NON_LOCKBOX_SLICE_CELL_KEYS = (
    "case_count",
    "unique_actor_count",
    "suppressed",
    "contributor_row_commitment_sha256",
    "contributor_actor_commitment_sha256",
    "model_macro_f1",
    "paired_macro_f1_lift",
)
_NON_LOCKBOX_CACHE_ROLES = (
    "training_discovery",
    "calibration",
    "balanced_diagnostic",
    "ami_evidence",
)
_NON_LOCKBOX_PRIVATE_KEYS = frozenset(
    {
        "row_id",
        "row_ids",
        "actor_id",
        "actor_ids",
        "participant_id",
        "participant_ids",
        "meeting_id",
        "meeting_ids",
        "clip_stem",
        "clip_stems",
        "filename",
        "filenames",
        "file_path",
        "file_paths",
        "source_path",
        "source_paths",
        "path",
        "paths",
        "probabilities",
        "labels",
        "sentences",
        "transcript",
        "transcripts",
        "utterance_text",
        "raw_text",
        "audio",
    }
)


def _non_lockbox_packet_digest(payload: Any) -> str:
    try:
        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError) as error:
        raise ValueError(
            "non-lockbox packet is not canonical JSON"
        ) from error
    return hashlib.sha256(canonical).hexdigest().upper()


def _validate_non_lockbox_aggregate_privacy(payload: Any) -> None:
    def visit(value: Any) -> None:
        if type(value) is dict:
            for raw_key, item in value.items():
                key = raw_key.casefold()
                if (
                    key in _NON_LOCKBOX_PRIVATE_KEYS
                    or key.endswith("_path")
                    or key.endswith("_filename")
                ):
                    raise ValueError(
                        "private identifier, row, text, or path field is blocked"
                    )
                visit(item)
            for count_key in (
                "unique_actor_count",
                "unique_participant_count",
            ):
                if count_key not in value:
                    continue
                count = value[count_key]
                if type(count) is not int or count < 0:
                    raise ValueError("published contributor count is invalid")
                suppressed = value.get("suppressed")
                has_published_value = (
                    "value" not in value or value.get("value") is not None
                )
                if (
                    count < MINIMUM_UNIQUE_ACTORS
                    and suppressed is not True
                    and has_published_value
                ):
                    raise ValueError(
                        "published aggregate cell has fewer than ten contributors"
                    )
            return
        if type(value) is list:
            for item in value:
                visit(item)
            return
        if type(value) is str and (
            "\\" in value
            or "/" in value
            or re.search(r"(?i)\.(?:wav|xml|csv)(?:$|[?#])", value)
            or re.match(r"^[A-Za-z]:", value)
        ):
            raise ValueError(
                "private identifier, row, text, or path value is blocked"
            )

    visit(payload)


def _validate_non_lockbox_slice_v2(
    payload: Any,
    *,
    diagnostic: Mapping[str, Any],
) -> dict[str, Any]:
    sliced = _phase_b_exact_dict(
        payload,
        _NON_LOCKBOX_SLICE_KEYS,
        "diagnostic slice analysis",
    )
    if (
        sliced["schema_id"] != "emotion-state-phase-b-slice-analysis-v2"
        or sliced["partition_role"] != "balanced_diagnostic"
        or type(sliced["class_order"]) is not list
        or any(type(label) is not str for label in sliced["class_order"])
        or tuple(sliced["class_order"]) != CLASS_ORDER
        or type(sliced["instability_tolerance"]) is not float
        or sliced["instability_tolerance"] != 0.10
        or type(sliced["eligible_slice_reversal"]) is not bool
        or type(sliced["eligible_slice_instability"]) is not bool
    ):
        raise ValueError("diagnostic slice analysis contract does not match")
    validate_provenance_payload(
        sliced["provenance"],
        expected_role="balanced_diagnostic",
    )
    if not _matches_expected(sliced["provenance"], diagnostic["provenance"]):
        raise ValueError(
            "diagnostic slice provenance does not match diagnostic"
        )
    for field in (
        "probability_evidence_mint_sha256",
        "evaluation_evidence_mint_sha256",
        "self_sha256",
    ):
        _uppercase_sha256(sliced[field], f"diagnostic slice {field}")
    if (
        sliced["probability_evidence_mint_sha256"]
        != diagnostic["probability_evidence_mint_sha256"]
        or sliced["evaluation_evidence_mint_sha256"]
        != _non_lockbox_packet_digest(diagnostic)
        or sliced["self_sha256"] != canonical_payload_sha256(sliced)
    ):
        raise ValueError("diagnostic slice lineage or self commitment changed")

    cells = sliced["slices"]
    if (
        type(cells) is not dict
        or any(type(name) is not str for name in cells)
        or tuple(cells) != tuple(sorted(cells))
    ):
        raise ValueError("diagnostic slice names must be an ordered mapping")
    names = tuple(cells)
    source_labels = tuple(
        name for name in names if name.startswith("source_label:")
    )
    scenarios = tuple(
        name for name in names if name.startswith("scripted_scenario:")
    )
    vote_names = tuple(
        name for name in names if name.startswith("vote_agreement:")
    )
    silence_names = tuple(
        name for name in names if name.startswith("silence_ratio:")
    )
    expected_source_labels = tuple(
        sorted(f"source_label:{label}" for label in CLASS_ORDER)
    )
    expected_vote_names = tuple(sorted((
        "vote_agreement:[0.00,0.50)",
        "vote_agreement:[0.50,0.75)",
        "vote_agreement:[0.75,1.00]",
    )))
    expected_silence_names = tuple(
        sorted(f"silence_ratio:Q{index}" for index in range(1, 5))
    )
    if (
        len(names) != 25
        or source_labels != expected_source_labels
        or len(scenarios) != 12
        or any(
            re.fullmatch(r"scripted_scenario:[A-Z0-9]{3}", name) is None
            for name in scenarios
        )
        or vote_names != expected_vote_names
        or silence_names != expected_silence_names
        or set(names) != set(
            (*source_labels, *scenarios, *vote_names, *silence_names)
        )
    ):
        raise ValueError(
            "diagnostic slice families do not match the frozen 25 cells"
        )

    diagnostic_cases = diagnostic["provenance"]["case_count"]
    diagnostic_actors = diagnostic["provenance"]["unique_actor_count"]
    full_lifts = {
        baseline: (
            diagnostic["models"]["acoustic"]["macro_f1"]
            - diagnostic["models"][baseline]["macro_f1"]
        )
        for baseline in ("class_prior", "sentence_id")
    }
    derived_reversal = False
    derived_instability = False
    for name, raw_cell in cells.items():
        cell = _phase_b_exact_dict(
            raw_cell,
            _NON_LOCKBOX_SLICE_CELL_KEYS,
            f"diagnostic slice cell {name}",
        )
        case_count = cell["case_count"]
        actor_count = cell["unique_actor_count"]
        suppressed = cell["suppressed"]
        if (
            type(case_count) is not int
            or not 0 <= case_count <= diagnostic_cases
            or type(actor_count) is not int
            or not 0 <= actor_count <= min(case_count, diagnostic_actors)
            or type(suppressed) is not bool
            or suppressed is not (actor_count < MINIMUM_UNIQUE_ACTORS)
        ):
            raise ValueError(
                f"diagnostic slice count or suppression contradicts: {name}"
            )
        for field in (
            "contributor_row_commitment_sha256",
            "contributor_actor_commitment_sha256",
        ):
            _uppercase_sha256(cell[field], f"diagnostic slice {name} {field}")
        if suppressed:
            if (
                cell["model_macro_f1"] is not None
                or cell["paired_macro_f1_lift"] is not None
            ):
                raise ValueError(
                    f"suppressed diagnostic slice metrics must be null: {name}"
                )
            continue
        scores = _phase_b_exact_dict(
            cell["model_macro_f1"],
            MODEL_KEYS,
            f"diagnostic slice model metrics {name}",
        )
        lifts = _phase_b_exact_dict(
            cell["paired_macro_f1_lift"],
            ("class_prior", "sentence_id"),
            f"diagnostic slice lift metrics {name}",
        )
        for model, value in scores.items():
            if (
                type(value) is not float
                or not math.isfinite(value)
                or not 0.0 <= value <= 1.0
            ):
                raise ValueError(
                    f"diagnostic slice model metric is invalid: {name}/{model}"
                )
        for baseline, value in lifts.items():
            expected = scores["acoustic"] - scores[baseline]
            if (
                type(value) is not float
                or not math.isfinite(value)
                or not -1.0 <= value <= 1.0
                or not math.isclose(
                    value,
                    expected,
                    rel_tol=0.0,
                    abs_tol=1e-15,
                )
            ):
                raise ValueError(
                    f"diagnostic slice lift is invalid: {name}/{baseline}"
                )
            derived_reversal = derived_reversal or value < 0.0
            derived_instability = derived_instability or (
                abs(value - full_lifts[baseline]) > 0.10
            )
    for family in (source_labels, scenarios, vote_names, silence_names):
        if sum(cells[name]["case_count"] for name in family) != diagnostic_cases:
            raise ValueError(
                "diagnostic slice family case counts do not cover the diagnostic set"
            )
    if (
        sliced["eligible_slice_reversal"] is not derived_reversal
        or sliced["eligible_slice_instability"] is not derived_instability
    ):
        raise ValueError(
            "diagnostic slice derived flags do not match unsuppressed cells"
        )
    _validate_non_lockbox_aggregate_privacy(sliced)
    return copy.deepcopy(sliced)


def validate_non_lockbox_packet(payload: Any) -> dict[str, Any]:
    _phase_b_require_exact_json_graph(payload, "non-lockbox packet")
    packet = copy.deepcopy(
        _phase_b_exact_dict(
            payload,
            _NON_LOCKBOX_PACKET_V4_KEYS,
            "non-lockbox packet",
        )
    )
    if (
        packet["schema_id"]
        != "emotion-state-phase-b-non-lockbox-review-v4"
        or type(packet["schema_version"]) is not int
        or packet["schema_version"] != 4
    ):
        raise ValueError("non-lockbox packet schema must be exact v4/4")
    digest_fields = (
        "configuration_sha256",
        "split_manifest_sha256",
        "tracked_public_authority_commitment_sha256",
        "diagnostic_aggregate_sha256",
        "diagnostic_slice_analysis_sha256",
        "ami_aggregate_sha256",
        "artifact_cache_commitments_sha256",
        "review_sha256",
    )
    for field in digest_fields:
        _uppercase_sha256(packet[field], f"non-lockbox packet {field}")
    if packet["configuration_sha256"] != EXPECTED_EVIDENCE_IDENTITY_SHA256[
        "configuration_sha256"
    ]:
        raise ValueError("configuration identity does not match")
    _require_exact(
        packet["model_settings"],
        EXPECTED_CONFIG["model"],
        "model settings",
    )
    _require_exact(
        packet["metric_definitions"],
        EXPECTED_METRIC_DEFINITIONS,
        "metric definitions",
    )
    _require_exact(
        packet["slice_definitions"],
        EXPECTED_SLICE_DEFINITIONS,
        "slice definitions",
    )
    if (
        type(packet["minimum_unique_contributors_per_cell"]) is not int
        or packet["minimum_unique_contributors_per_cell"]
        != MINIMUM_UNIQUE_ACTORS
    ):
        raise ValueError("contributor floor does not match the frozen contract")
    lockbox_access = _phase_b_exact_dict(
        packet["lockbox_access"],
        (
            "open_count",
            "label_reads",
            "feature_reads",
            "audio_reads",
            "cache_reads",
        ),
        "non-lockbox access counters",
    )
    if any(type(value) is not int or value != 0 for value in lockbox_access.values()):
        raise ValueError("non-lockbox packet must record integer-zero lockbox access")
    if packet["final_decision_eligible"] is not False:
        raise ValueError("non-lockbox packet cannot be decision eligible")

    diagnostic = packet["diagnostic_aggregate"]
    validate_evaluation_result(
        diagnostic,
        expected_role="balanced_diagnostic",
    )
    if diagnostic["final_decision_eligible"] is not False:
        raise ValueError("balanced diagnostic cannot be decision eligible")
    if (
        diagnostic["provenance"]["configuration_sha256"]
        != packet["configuration_sha256"]
        or diagnostic["provenance"]["split_manifest_sha256"]
        != packet["split_manifest_sha256"]
    ):
        raise ValueError("diagnostic identity bindings do not match packet")
    sliced = _validate_non_lockbox_slice_v2(
        packet["diagnostic_slice_analysis"],
        diagnostic=diagnostic,
    )
    if not _matches_expected(sliced, packet["diagnostic_slice_analysis"]):
        raise ValueError("diagnostic slice analysis changed during validation")
    ami = validate_published_ami_aggregate_v2(packet["ami_aggregate"])
    if not _matches_expected(ami, packet["ami_aggregate"]):
        raise ValueError("AMI aggregate changed during validation")

    cache_commitments = _phase_b_exact_dict(
        packet["artifact_cache_commitments"],
        _NON_LOCKBOX_CACHE_ROLES,
        "artifact cache commitments",
    )
    if tuple(cache_commitments) != _NON_LOCKBOX_CACHE_ROLES:
        raise ValueError("artifact cache commitment order does not match")
    for role, digest in cache_commitments.items():
        _uppercase_sha256(digest, f"artifact cache commitment {role}")
    _validate_non_lockbox_aggregate_privacy(diagnostic)
    _validate_non_lockbox_aggregate_privacy(sliced)
    _validate_non_lockbox_aggregate_privacy(packet["ami_aggregate"])

    if (
        _non_lockbox_packet_digest(diagnostic)
        != packet["diagnostic_aggregate_sha256"]
        or _non_lockbox_packet_digest(sliced)
        != packet["diagnostic_slice_analysis_sha256"]
        or _non_lockbox_packet_digest(packet["ami_aggregate"])
        != packet["ami_aggregate_sha256"]
        or _non_lockbox_packet_digest(cache_commitments)
        != packet["artifact_cache_commitments_sha256"]
    ):
        raise ValueError("non-lockbox aggregate commitment changed")
    unsigned = copy.deepcopy(packet)
    review_sha256 = unsigned.pop("review_sha256")
    if _non_lockbox_packet_digest(unsigned) != review_sha256:
        raise ValueError("non-lockbox review commitment changed")
    return copy.deepcopy(packet)


def derive_phase_b_decision(decision_evidence: Any) -> str:
    """Derive a structural readback, not provenance authority.

    The lockbox runner establishes authority by calling Task 6
    decide_experiment on a recursively verified private DecisionEvidence
    artifact before serializing and state-binding this mapping.
    """
    metrics, validity = validate_decision_inputs(
        decision_evidence,
        dict(EXPECTED_VALIDITY),
    )
    if not all(validity.values()):
        return "discard"
    if metrics["sentence_driven_apparent_lift"]:
        return "discard"
    lifts = metrics["paired_macro_f1_lift"]
    if any(lifts[baseline]["point_estimate"] <= 0.0 for baseline in lifts):
        return "discard"
    models = metrics["models"]
    acoustic = models["acoustic"]
    class_prior = models["class_prior"]
    if (
        all(lifts[baseline]["lower_95"] > 0.0 for baseline in lifts)
        and acoustic["multiclass_brier"] < class_prior["multiclass_brier"]
        and acoustic["ece_10_bin"] <= class_prior["ece_10_bin"]
        and all(
            acoustic["per_class_recall"][label]["recall"] is not None
            and acoustic["per_class_recall"][label]["recall"] > 0.0
            for label in CLASS_ORDER
        )
        and not metrics["eligible_slice_reversal"]
        and not metrics["eligible_slice_instability"]
        and metrics["confidence_abstention_improves"]
    ):
        return "keep_for_research_only"
    return "revise"


def _meeting_from_payload(payload: Any) -> Any:
    from scripts.emotion_state_phase_b_ami_mechanics import MeetingMechanics

    meeting = _exact_keys(
        payload,
        (
            "meeting_id",
            "participants",
            "values",
            "dialogue_act_distribution",
        ),
        "authoritative AMI meeting",
    )
    if not isinstance(meeting["participants"], list):
        raise ValueError("authoritative AMI participants must be a list")
    values = _exact_keys(meeting["values"], AMI_BUCKET_KEYS + AMI_SCALAR_KEYS, "AMI values")
    distribution = _exact_keys(
        meeting["dialogue_act_distribution"],
        AMI_DIALOGUE_ACT_VOCABULARY,
        "AMI dialogue-act distribution",
    )
    return MeetingMechanics(
        meeting_id=meeting["meeting_id"],
        participants=tuple(meeting["participants"]),
        values=tuple((key, values[key]) for key in AMI_BUCKET_KEYS + AMI_SCALAR_KEYS),
        dialogue_act_distribution=tuple(
            (key, distribution[key]) for key in AMI_DIALOGUE_ACT_VOCABULARY
        ),
    )


def _canonical_digest(payload: Any) -> str:
    content = (
        json.dumps(
            payload,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    return hashlib.sha256(content).hexdigest().upper()


def _validate_ami_authority(payload: Any) -> tuple[tuple[Any, ...], dict[str, list[str]], tuple[str, ...]]:
    authority = _exact_keys(
        payload,
        ("meetings", "partition_membership", "official_order"),
        "AMI authority",
    )
    if not isinstance(authority["meetings"], list) or not authority["meetings"]:
        raise ValueError("AMI authority meetings must be a non-empty list")
    meetings = tuple(_meeting_from_payload(item) for item in authority["meetings"])
    membership = _exact_keys(
        authority["partition_membership"],
        AMI_PARTITION_CELLS,
        "AMI partition membership",
    )
    if any(not isinstance(membership[key], list) for key in AMI_PARTITION_CELLS):
        raise ValueError("AMI partition memberships must be lists")
    if not isinstance(authority["official_order"], list):
        raise ValueError("AMI official order must be a list")
    return meetings, dict(membership), tuple(authority["official_order"])


def _validate_published_ami_cell(
    cell: Any,
    *,
    name: str,
    non_negative: bool,
    unit_interval: bool,
) -> None:
    validated = _exact_keys(
        cell,
        ("suppressed", "unique_participant_count", "value"),
        name,
    )
    count = _count(validated["unique_participant_count"], f"{name} contributor count")
    if type(validated["suppressed"]) is not bool:
        raise ValueError(f"{name} suppression flag must be boolean")
    if validated["suppressed"] is not (count < MINIMUM_UNIQUE_ACTORS):
        raise ValueError(f"{name} suppression is not derived from contributor count")
    if validated["suppressed"]:
        if validated["value"] is not None:
            raise ValueError(f"{name} suppressed value must be absent")
        return
    value = _finite_float(validated["value"], f"{name} value")
    if non_negative and value < 0.0:
        raise ValueError(f"{name} value must be non-negative")
    if unit_interval and not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} value must be within [0,1]")


def validate_published_ami_aggregate(payload: Any) -> Mapping[str, Any]:
    partitions = _exact_keys(payload, AMI_PARTITION_CELLS, "published AMI aggregate")
    for partition_name in AMI_PARTITION_CELLS:
        partition = _exact_keys(
            partitions[partition_name],
            (
                "meeting_count",
                "unique_participant_count",
                "scalars",
                "buckets",
                "dialogue_acts",
                "suppression_counts",
            ),
            f"{partition_name} AMI aggregate",
        )
        meeting_count = _count(partition["meeting_count"], "AMI meeting count")
        participant_count = _count(
            partition["unique_participant_count"],
            "AMI participant count",
        )
        if participant_count < 2 * int(meeting_count > 0):
            raise ValueError("AMI aggregate contributor count is impossible")
        scalars = _exact_keys(partition["scalars"], AMI_SCALAR_KEYS, "AMI scalar fields")
        buckets = _exact_keys(partition["buckets"], AMI_BUCKET_KEYS, "AMI bucket fields")
        dialogue = _exact_keys(
            partition["dialogue_acts"],
            AMI_DIALOGUE_ACT_VOCABULARY,
            "AMI dialogue-act fields",
        )
        for key, cell in scalars.items():
            _validate_published_ami_cell(
                cell,
                name=f"AMI scalar {key}",
                non_negative=True,
                unit_interval=key in {"overlap_ratio", "speaker_balance_normalized_entropy"},
            )
        for key, cell in buckets.items():
            _validate_published_ami_cell(
                cell,
                name=f"AMI bucket {key}",
                non_negative=True,
                unit_interval=False,
            )
        for key, cell in dialogue.items():
            _validate_published_ami_cell(
                cell,
                name=f"AMI dialogue act {key}",
                non_negative=True,
                unit_interval=True,
            )
        suppression = _exact_keys(
            partition["suppression_counts"],
            (
                "repeated_participant_meetings",
                "scalar_cells",
                "bucket_cells",
                "dialogue_act_cells",
            ),
            "AMI suppression counts",
        )
        if any(type(value) is not int or value < 0 for value in suppression.values()):
            raise ValueError("AMI suppression counts must be non-negative integers")
        if suppression["repeated_participant_meetings"] > meeting_count:
            raise ValueError("AMI repeated-meeting count exceeds meeting count")
        expected_suppressed = participant_count < MINIMUM_UNIQUE_ACTORS
        expected_counts = {
            "scalar_cells": len(AMI_SCALAR_KEYS) if expected_suppressed else 0,
            "bucket_cells": len(AMI_BUCKET_KEYS) if expected_suppressed else 0,
            "dialogue_act_cells": len(AMI_DIALOGUE_ACT_VOCABULARY)
            if expected_suppressed
            else 0,
        }
        if any(suppression[key] != value for key, value in expected_counts.items()):
            raise ValueError("AMI suppression counts are not derived")
    return partitions


def validate_lockbox_ami_input(payload: Any) -> dict[str, Any]:
    result = _exact_keys(
        payload,
        ("schema_version", "ami"),
        "lockbox AMI input",
    )
    if result["schema_version"] != 1 or type(result["schema_version"]) is not int:
        raise ValueError("lockbox AMI input schema version must be 1")
    ami = _exact_keys(
        result["ami"],
        ("aggregate", "authority", "authority_sha256"),
        "AMI lockbox evidence",
    )
    if _canonical_digest(ami["authority"]) != ami["authority_sha256"]:
        raise ValueError("AMI authority digest does not match")
    meetings, membership, order = _validate_ami_authority(ami["authority"])
    validate_ami_mechanics_aggregates(
        ami["aggregate"],
        meetings=meetings,
        partition_membership=membership,
        official_order=order,
        minimum_contributors=MINIMUM_UNIQUE_ACTORS,
    )
    validate_published_ami_aggregate(ami["aggregate"])
    return dict(result)


def serialized_decision_evidence_mint_sha256(payload: Any) -> str:
    """Return the serialized mint digest without asserting provenance authority."""
    validate_decision_inputs(payload, dict(EXPECTED_VALIDITY))
    content = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(content).hexdigest().upper()


def validate_lockbox_result(payload: Any) -> dict[str, Any]:
    """Structurally validate state-bound lockbox bytes.

    This function does not mint decision authority. Provenance is established
    only by recursively verifying a private DecisionEvidence lifecycle artifact
    before the runner serializes and binds these bytes.
    """
    result = _exact_keys(
        payload,
        ("schema_version", "decision_evidence", "ami"),
        "lockbox result",
    )
    if result["schema_version"] != 1 or type(result["schema_version"]) is not int:
        raise ValueError("lockbox result schema version must be 1")
    validate_decision_inputs(result["decision_evidence"], dict(EXPECTED_VALIDITY))
    validate_lockbox_ami_input(
        {
            "schema_version": result["schema_version"],
            "ami": result["ami"],
        }
    )
    return dict(result)


def validate_lockbox_lineage(
    payload: Any,
    split_manifest: Any,
) -> None:
    validated = validate_lockbox_result(payload)
    split = validate_phase_b_split_manifest(split_manifest)
    provenance = validated["decision_evidence"]["provenance"]
    if any(
        provenance[field] != digest
        for field, digest in EXPECTED_EVIDENCE_IDENTITY_SHA256.items()
    ):
        raise ValueError("lockbox evidence does not bind frozen identities")
    if (
        provenance["split_manifest_sha256"]
        != split["split_manifest_sha256"]
        or provenance["assignment_sha256"] != split["assignment_sha256"]
    ):
        raise ValueError("lockbox evidence does not bind validated split")


def validated_lockbox_summary(
    payload: Any,
    *,
    bound_decision_evidence_sha256: str,
    bound_decision_evidence_mint_sha256: str,
) -> dict[str, Any]:
    validated = validate_lockbox_result(payload)
    evidence = validated["decision_evidence"]
    if _canonical_digest(evidence) != bound_decision_evidence_sha256:
        raise ValueError("state-bound decision evidence digest does not match")
    if (
        serialized_decision_evidence_mint_sha256(evidence)
        != bound_decision_evidence_mint_sha256
    ):
        raise ValueError(
            "state-bound private decision evidence mint digest does not match"
        )
    authority = validated["ami"]["authority"]
    return {
        "crema": {
            "decision_evidence": evidence,
            "evidence_sha256": bound_decision_evidence_sha256,
            "evidence_mint_sha256": bound_decision_evidence_mint_sha256,
        },
        "ami": {
            "aggregate": validated["ami"]["aggregate"],
            "aggregate_sha256": _canonical_digest(
                validated["ami"]["aggregate"]
            ),
            "source_commitment_sha256": _canonical_digest(authority),
            "minimum_unique_contributors_per_cell": MINIMUM_UNIQUE_ACTORS,
        },
        "validity": dict(EXPECTED_VALIDITY),
        "decision": derive_phase_b_decision(evidence),
    }


def validate_phase_b_result(payload: Any) -> dict[str, Any]:
    result = _exact_keys(
        payload,
        (
            "schema_id",
            "schema_version",
            "checkpoint_id",
            "phase_a",
            "dataset_evidence",
            "raw_csv_sha256",
            "configuration_sha256",
            "environment_lock_sha256",
            "feature_schema_sha256",
            "split_schema_sha256",
            "split_manifest_sha256",
            "split_evidence",
            "crema_label_ledger",
            "model_settings",
            "metric_definitions",
            "slice_definitions",
            "non_lockbox_review_sha256",
            "lockbox",
            "validity",
            "decision",
            "closed_boundaries",
        ),
        "Phase B aggregate result",
    )
    if result["schema_id"] != "emotion-state-002-phase-b-result-v1":
        raise ValueError("Phase B aggregate schema id is invalid")
    if result["schema_version"] != 1 or type(result["schema_version"]) is not int:
        raise ValueError("Phase B aggregate schema version must be 1")
    if result["checkpoint_id"] != EXPECTED_CONFIG["checkpoint_id"]:
        raise ValueError("Phase B aggregate checkpoint id is invalid")
    _require_exact(result["phase_a"], EXPECTED_PHASE_A_BINDING, "Phase A binding")
    _require_exact(result["dataset_evidence"], EXPECTED_DATASET_EVIDENCE, "dataset evidence")
    _require_exact(
        result["raw_csv_sha256"],
        EXPECTED_PUBLIC_RAW_SOURCE_SHA256,
        "published raw-source hashes",
    )
    for field, digest in EXPECTED_STATIC_FILE_SHA256.items():
        if result[field] != digest:
            raise ValueError(f"{field} does not match the frozen tracked identity")
    _uppercase_sha256(result["split_manifest_sha256"], "split manifest file")
    split_evidence = validate_phase_b_split_manifest(result["split_evidence"])
    _uppercase_sha256(result["non_lockbox_review_sha256"], "non-lockbox review")
    validate_crema_label_ledger(result["crema_label_ledger"], EXPECTED_CONFIG)
    _require_exact(result["model_settings"], EXPECTED_CONFIG["model"], "model settings")
    _require_exact(
        result["metric_definitions"],
        EXPECTED_METRIC_DEFINITIONS,
        "metric definitions",
    )
    _require_exact(
        result["slice_definitions"],
        EXPECTED_SLICE_DEFINITIONS,
        "slice definitions",
    )
    lockbox = _exact_keys(
        result["lockbox"],
        (
            "open_count",
            "reservation_sha256",
            "result_sha256",
            "decision_evidence_sha256",
            "decision_evidence_mint_sha256",
            "crema",
            "ami",
        ),
        "aggregate lockbox",
    )
    if lockbox["open_count"] != 1 or type(lockbox["open_count"]) is not int:
        raise ValueError("aggregate lockbox open count must be exactly 1")
    _uppercase_sha256(lockbox["reservation_sha256"], "lockbox reservation")
    _uppercase_sha256(lockbox["result_sha256"], "lockbox result")
    _uppercase_sha256(
        lockbox["decision_evidence_sha256"],
        "lockbox decision evidence",
    )
    _uppercase_sha256(
        lockbox["decision_evidence_mint_sha256"],
        "lockbox private decision evidence mint",
    )
    crema = _exact_keys(
        lockbox["crema"],
        (
            "decision_evidence",
            "evidence_sha256",
            "evidence_mint_sha256",
        ),
        "published CREMA evidence",
    )
    if _canonical_digest(crema["decision_evidence"]) != crema["evidence_sha256"]:
        raise ValueError("published CREMA evidence digest does not match")
    if crema["evidence_sha256"] != lockbox["decision_evidence_sha256"]:
        raise ValueError("published CREMA evidence does not match lockbox binding")
    if (
        serialized_decision_evidence_mint_sha256(
            crema["decision_evidence"]
        )
        != crema["evidence_mint_sha256"]
        or crema["evidence_mint_sha256"]
        != lockbox["decision_evidence_mint_sha256"]
    ):
        raise ValueError(
            "published CREMA private mint digest does not match lockbox binding"
        )
    validate_decision_inputs(
        crema["decision_evidence"],
        dict(EXPECTED_VALIDITY),
    )
    provenance = crema["decision_evidence"]["provenance"]
    if any(
        provenance[field] != digest
        for field, digest in EXPECTED_EVIDENCE_IDENTITY_SHA256.items()
    ):
        raise ValueError("CREMA evidence does not bind frozen input identities")
    if (
        provenance["split_manifest_sha256"]
        != split_evidence["split_manifest_sha256"]
        or provenance["assignment_sha256"]
        != split_evidence["assignment_sha256"]
    ):
        raise ValueError("CREMA evidence does not bind validated split evidence")
    ami = _exact_keys(
        lockbox["ami"],
        (
            "aggregate",
            "aggregate_sha256",
            "source_commitment_sha256",
            "minimum_unique_contributors_per_cell",
        ),
        "published AMI evidence",
    )
    _uppercase_sha256(ami["source_commitment_sha256"], "AMI source commitment")
    if _canonical_digest(ami["aggregate"]) != ami["aggregate_sha256"]:
        raise ValueError("published AMI aggregate digest does not match")
    if ami["minimum_unique_contributors_per_cell"] != MINIMUM_UNIQUE_ACTORS:
        raise ValueError("AMI contributor floor does not match")
    validate_published_ami_aggregate(ami["aggregate"])
    _require_exact(result["validity"], EXPECTED_VALIDITY, "validity facts")
    derived = derive_phase_b_decision(crema["decision_evidence"])
    if result["decision"] != derived:
        raise ValueError("Phase B decision is not derived from validated evidence")
    _require_exact(
        result["closed_boundaries"],
        EXPECTED_CONFIG["boundaries"],
        "closed boundaries",
    )
    return dict(result)


def synthetic_phase_b_result_fixture() -> dict[str, Any]:
    raise ValueError(
        "synthetic Phase B aggregate fixtures require validated Task 6/7 evidence"
    )


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def validate_source_section() -> None:
    if _file_sha256(PHASE_A_RESULT_PATH) != EXPECTED_PHASE_A_BINDING["result_sha256"]:
        raise ValueError("Phase A result does not match the accepted source binding")
    if _file_sha256(PHASE_A_REPORT_PATH) != EXPECTED_PHASE_A_BINDING["report_sha256"]:
        raise ValueError("Phase A report does not match the accepted source binding")
    phase_a = load_json_strict(PHASE_A_RESULT_PATH)
    if (
        phase_a.get("checkpoint_id") != "EMOTION-STATE-001-phase-a-contracts"
        or phase_a.get("mode") != "complete"
        or phase_a.get("status") != "complete"
        or phase_a.get("dataset_evaluation_started") is not False
        or phase_a.get("selected_public_datasets")
        != ["crema-d-v1.0-audio-wav", "ami-manual-annotations-v1.6.2"]
    ):
        raise ValueError("accepted Phase A source checkpoint is invalid")
    evidence = phase_a.get("dataset_manifest_evidence")
    if not isinstance(evidence, list) or len(evidence) != 2:
        raise ValueError("Phase A dataset evidence set is invalid")
    evidence_by_dataset = {
        entry.get("dataset_id"): entry
        for entry in evidence
        if isinstance(entry, Mapping)
    }
    if set(evidence_by_dataset) != {
        "crema-d-v1.0-audio-wav",
        "ami-manual-annotations-v1.6.2",
    }:
        raise ValueError("Phase A dataset evidence identities are invalid")
    for key, manifest_path in SOURCE_MANIFEST_PATHS.items():
        expected = EXPECTED_DATASET_EVIDENCE[key]
        manifest = load_json_strict(manifest_path)
        dataset_id = expected["dataset_id"]
        manifest_evidence = evidence_by_dataset[dataset_id]
        if (
            manifest.get("dataset_id") != dataset_id
            or manifest.get("source_label") != "public-only"
            or manifest.get("completion_status") != "verified"
            or manifest.get("runtime_influence_allowed") is not False
            or manifest.get("project_label_mapping") != {}
            or tuple(manifest.get("excluded_labels", ()))
            != ("hesitation", "frustration", "confusion", "interest", "disengagement")
            or _file_sha256(manifest_path) != expected["manifest_sha256"]
            or any(
                manifest_evidence.get(field) != expected[field]
                for field in (
                    "manifest_sha256",
                    "hash_inventory_sha256",
                    "quality_inventory_sha256",
                )
            )
        ):
            raise ValueError(f"{dataset_id} tracked source evidence is invalid")
        if key == "crema_d" and manifest.get("source_revision") != expected[
            "source_revision"
        ]:
            raise ValueError("CREMA-D source revision is invalid")
    validate_phase_b_input_ledger(expected_phase_b_input_ledger())


def validate_contracts_section() -> None:
    validate_config(load_json_strict(CONFIG_PATH))
    validate_feature_schema(load_json_strict(FEATURE_SCHEMA_PATH))
    validate_split_schema(load_json_strict(SPLIT_SCHEMA_PATH))
    validate_environment_lock(load_json_strict(ENVIRONMENT_LOCK_PATH))
    for field, path in (
        ("configuration_sha256", CONFIG_PATH),
        ("environment_lock_sha256", ENVIRONMENT_LOCK_PATH),
        ("feature_schema_sha256", FEATURE_SCHEMA_PATH),
        ("split_schema_sha256", SPLIT_SCHEMA_PATH),
    ):
        if _file_sha256(path) != EXPECTED_STATIC_FILE_SHA256[field]:
            raise ValueError(f"{field} does not match the frozen tracked file")


def validate_environment_section() -> None:
    validate_environment_identity(
        lock_path=ENVIRONMENT_LOCK_PATH,
        wheelhouse_path=WHEELHOUSE_PATH,
    )


def validate_synthetic_section() -> None:
    def rejects_legacy_summary(payload: Any) -> bool:
        try:
            validate_non_lockbox_packet(payload)
        except (TypeError, ValueError):
            return True
        raise ValueError("legacy summary-only non-lockbox packet was accepted")

    fixture = {
        "input_ledger": expected_phase_b_input_ledger(),
        "non_lockbox_packet": expected_non_lockbox_packet("A" * 64),
    }
    first = {
        "input_ledger": validate_phase_b_input_ledger(
            fixture["input_ledger"]
        ),
        "legacy_summary_only_packet_rejected": rejects_legacy_summary(
            fixture["non_lockbox_packet"]
        ),
    }
    second = {
        "input_ledger": validate_phase_b_input_ledger(
            expected_phase_b_input_ledger()
        ),
        "legacy_summary_only_packet_rejected": rejects_legacy_summary(
            expected_non_lockbox_packet("A" * 64)
        ),
    }
    first_bytes = json.dumps(
        first,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    second_bytes = json.dumps(
        second,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    if first_bytes != second_bytes:
        raise ValueError("synthetic runner result is not deterministic")


def _normalized_output_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    normalized = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", normalized)
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", normalized)
    return normalized.strip("_").casefold()


def _scan_output_structure(value: Any) -> None:
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            if not isinstance(raw_key, str):
                raise ValueError("forbidden output: non-text structured key")
            key = _normalized_output_key(raw_key)
            tokens = tuple(part for part in key.split("_") if part)
            token_set = set(tokens)
            identity_subjects = {
                "actor",
                "actors",
                "speaker",
                "speakers",
                "participant",
                "participants",
                "meeting",
                "meetings",
                "row",
                "rows",
            }
            identity_markers = {
                "id",
                "ids",
                "identifier",
                "identifiers",
                "identity",
                "identities",
            }
            if (
                key in identity_subjects
                or (
                    token_set.intersection(identity_subjects)
                    and token_set.intersection(identity_markers)
                )
            ):
                raise ValueError("forbidden output: identity container")
            if (
                key in {"row", "rows", "record", "records", "row_records", "case_rows"}
                and isinstance(child, Sequence)
                and not isinstance(child, (str, bytes, bytearray))
            ):
                raise ValueError("forbidden output: row array")
            if (
                key == "transcript"
                or key.startswith("transcript_")
                or key
                in {
                    "utterance_text",
                    "raw_text",
                    "spoken_text",
                    "speech_text",
                    "dialogue_text",
                }
            ):
                raise ValueError("forbidden output: transcript content")
            audio_markers = {
                "audio",
                "audio_bytes",
                "audio_path",
                "audio_base64",
                "audio_data",
                "audio_payload",
                "encoded_audio",
                "waveform",
                "sample",
                "samples",
                "pcm",
                "pcm_samples",
            }
            if key in audio_markers or (
                key.startswith("audio_")
                and token_set.intersection(
                    {
                        "base64",
                        "blob",
                        "bytes",
                        "data",
                        "encoding",
                        "path",
                        "payload",
                        "sample",
                        "samples",
                        "waveform",
                    }
                )
            ):
                raise ValueError("forbidden output: audio encoding or marker")
            if not key.endswith("_sha256") and (
                key
                in {
                    "model_state",
                    "fitted_model",
                    "serialized_model",
                    "serialized_estimator",
                    "model_bytes",
                    "model_blob",
                    "model_pickle",
                    "coefficients",
                    "coefficient",
                    "intercepts",
                    "intercept",
                }
                or (
                    token_set.intersection({"model", "estimator"})
                    and token_set.intersection(
                        {"state", "serialized", "bytes", "blob", "pickle", "joblib"}
                    )
                )
            ):
                raise ValueError("forbidden output: model serialization")
            probability_metadata_keys = {
                "probability_evidence",
                "probability_evidence_mint_sha256",
                "probability_commitment_sha256",
            }
            if key in {"predict_proba", "probability_rows"} or (
                token_set.intersection({"probability", "probabilities"})
                and key not in probability_metadata_keys
                and not key.endswith("_sha256")
            ):
                raise ValueError("forbidden output: probability value")
            credential_keys = {
                "api_key",
                "access_key",
                "access_token",
                "auth_token",
                "authorization",
                "bearer",
                "client_secret",
                "credential",
                "credentials",
                "password",
                "passwd",
                "private_key",
                "refresh_token",
                "secret",
                "session_token",
            }
            if key in credential_keys or any(
                key.endswith(suffix)
                for suffix in (
                    "_api_key",
                    "_access_key",
                    "_access_token",
                    "_auth_token",
                    "_client_secret",
                    "_credential",
                    "_credentials",
                    "_password",
                    "_private_key",
                    "_refresh_token",
                    "_secret",
                    "_session_token",
                )
            ):
                raise ValueError("forbidden output: credential")
            _scan_output_structure(child)
    elif isinstance(value, str):
        validate_candidate_output_bytes(value.encode("utf-8"))
    elif isinstance(value, Sequence) and not isinstance(
        value,
        (bytes, bytearray),
    ):
        for item in value:
            _scan_output_structure(item)


def _decoded_output_payloads(text: str) -> list[Any]:
    decoder = json.JSONDecoder(
        object_pairs_hook=_pairs,
        parse_constant=_constant,
    )
    payloads: list[Any] = []
    start = len(text) - len(text.lstrip())
    try:
        payload, _end = decoder.raw_decode(text, start)
    except (ValueError, json.JSONDecodeError):
        pass
    else:
        payloads.append(payload)
    for match in re.finditer(
        r"```json[ \t]*\r?\n(?P<payload>.*?)\r?\n```",
        text,
        re.IGNORECASE | re.DOTALL,
    ):
        try:
            payloads.append(
                json.loads(
                    match.group("payload"),
                    object_pairs_hook=_pairs,
                    parse_constant=_constant,
                )
            )
        except (ValueError, json.JSONDecodeError) as error:
            raise ValueError(
                "forbidden output: invalid structured report content"
            ) from error
    return payloads


def validate_candidate_output_bytes(candidate_bytes: bytes) -> None:
    if not isinstance(candidate_bytes, bytes):
        raise TypeError("candidate output must be bytes")
    try:
        text = candidate_bytes.decode("utf-8")
    except UnicodeError as error:
        raise ValueError("forbidden output: candidate is not UTF-8") from error
    if "\x00" in text:
        raise ValueError("forbidden output: NUL byte")
    for payload in _decoded_output_payloads(text):
        _scan_output_structure(payload)
    lowered = unicodedata.normalize("NFKC", text).casefold()
    patterns = (
        (
            "absolute path",
            re.compile(
                r"(?<![a-z0-9_.-])[a-z]:[\\/]+[^\s\"'`]+|"
                r"\\\\+[a-z0-9._$-]+\\+[a-z0-9._$-]+"
                r"(?:\\+[^\s\"'`]+)*|"
                r"(?<![a-z0-9_.-])/(?:[a-z0-9._-]+/)*[a-z0-9._-]+",
                re.IGNORECASE,
            ),
        ),
        (
            "timestamp",
            re.compile(
                r"\b\d{4}-\d{2}-\d{2}t\d{2}:\d{2}:\d{2}"
                r"(?:\.\d+)?(?:z|[+-]\d{2}:\d{2})\b",
                re.IGNORECASE,
            ),
        ),
        (
            "filename",
            re.compile(
                r"(?<![a-z0-9_.-])[a-z_][a-z0-9_.-]{0,127}"
                r"\.[a-z][a-z0-9]{0,15}(?![a-z0-9_.-])",
                re.IGNORECASE,
            ),
        ),
        (
            "clip stem",
            re.compile(r"\b\d{4}_[a-z]{3}_[a-z]{3}_[a-z]{2}\b", re.IGNORECASE),
        ),
        (
            "identity container",
            re.compile(
                r'"(?:actor|speaker|participant|meeting|row)'
                r'(?:[_-]?(?:id|ids|identifier|identifiers))?"\s*:',
                re.IGNORECASE,
            ),
        ),
        (
            "row array",
            re.compile(
                r'"(?:rows?|row_records?|case_rows?|records?)"\s*:\s*\[',
                re.IGNORECASE,
            ),
        ),
        (
            "transcript content",
            re.compile(
                r'"(?:transcript(?:_[a-z0-9]+)*|utterance_text|raw_text|'
                r'spoken_text|speech_text|dialogue_text)"\s*:',
                re.IGNORECASE,
            ),
        ),
        (
            "audio encoding or marker",
            re.compile(
                r'"(?:audio(?:_(?:base64|blob|bytes|data|encoding|path|payload|'
                r'samples?|waveform))?|encoded_audio|waveform|pcm(?:_samples?)?|'
                r'samples?)"\s*:|\b(?:riff(?:-wave)?|uklgrg==|id3|flac|oggs)\b',
                re.IGNORECASE,
            ),
        ),
        (
            "model serialization",
            re.compile(
                r'"(?:model_(?:state|bytes|blob|pickle)|fitted_model|'
                r'serialized_(?:model|estimator)|coefficients?|intercepts?)"\s*:',
                re.IGNORECASE,
            ),
        ),
        (
            "probability value",
            re.compile(
                r'"(?:probability|probabilities|probability_rows|predict_proba|'
                r'(?:class|label|row)_(?:probability|probabilities))"\s*:',
                re.IGNORECASE,
            ),
        ),
        (
            "credential",
            re.compile(
                r'"(?:[a-z0-9]+_)*(?:api_key|access_key|access_token|auth_token|'
                r'authorization|bearer|client_secret|credentials?|password|'
                r'passwd|private_key|refresh_token|secret|session_token)"\s*:|'
                r"\bbearer\s+[a-z0-9._-]+",
                re.IGNORECASE,
            ),
        ),
        (
            "operational signal",
            re.compile(
                r"\b(?:hesitation|frustration|confusion|interest|disengagement)\b",
                re.IGNORECASE,
            ),
        ),
    )
    for label, pattern in patterns:
        if pattern.search(lowered):
            raise ValueError(f"forbidden output: {label}")


def canonical_publication_json_bytes(payload: Any) -> bytes:
    try:
        return (
            json.dumps(
                payload,
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ValueError("publication payload is not canonical JSON") from error


def render_phase_b_report(
    result: Mapping[str, Any],
    result_sha256: str,
) -> str:
    _uppercase_sha256(result_sha256, "result_sha256")
    validated = validate_phase_b_result(dict(result))
    canonical_bytes = canonical_publication_json_bytes(validated)
    canonical_sha256 = hashlib.sha256(canonical_bytes).hexdigest().upper()
    if canonical_sha256 != result_sha256:
        raise ValueError("report result digest does not match canonical JSON")
    canonical_payload = canonical_bytes.decode("utf-8").rstrip("\n")
    return (
        "# EMOTION-STATE-002 Phase B public-data feasibility\n\n"
        f"- Result SHA-256: `{result_sha256}`\n"
        f"- Decision: `{validated['decision']}`\n"
        "- Final lockbox open count: `1`\n"
        "- Boundary: aggregate public/synthetic evidence only; no private data, "
        "provider operations, network evaluation, source adaptation, runtime "
        "influence, or customer-state output.\n\n"
        "## Canonical aggregate\n\n"
        "```json\n"
        f"{canonical_payload}\n"
        "```\n"
    )


def validate_publication_pair_bytes(
    result_bytes: bytes,
    report_bytes: bytes,
) -> dict[str, Any]:
    if not isinstance(result_bytes, bytes) or not isinstance(report_bytes, bytes):
        raise TypeError("publication pair must be bytes")
    try:
        payload = json.loads(
            result_bytes.decode("utf-8"),
            object_pairs_hook=_pairs,
            parse_constant=_constant,
        )
        report_bytes.decode("utf-8")
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("publication pair is not valid UTF-8 JSON/text") from error
    _reject_non_finite(payload)
    validated = validate_phase_b_result(payload)
    canonical_result = canonical_publication_json_bytes(validated)
    if canonical_result != result_bytes:
        raise ValueError("publication result bytes are not deterministic")
    result_sha256 = hashlib.sha256(result_bytes).hexdigest().upper()
    expected_report = render_phase_b_report(
        validated,
        result_sha256,
    ).encode("utf-8")
    if report_bytes != expected_report:
        raise ValueError("publication report is not a deterministic readback")
    validate_candidate_output_bytes(result_bytes + b"\n" + report_bytes)
    return dict(validated)


def validate_candidate_readback(paths: Any, receipt_path: Path) -> dict[str, Any]:
    from scripts import run_emotion_state_002_phase_b as runner

    with runner.publication_lock(paths, read_only=True):
        state = runner.load_state(paths, recover=False)
        if state["phase"] != "awaiting_acceptance":
            raise ValueError(
                "candidate validation requires live awaiting_acceptance state"
            )
        transaction = runner._load_journal(paths, recover=False)
        if (
            transaction["status"] != "awaiting_acceptance"
            or transaction["transaction_id"]
            != state["candidate_transaction_id"]
            or transaction["configuration_sha256"]
            != state["configuration_sha256"]
        ):
            raise ValueError("candidate transaction does not match awaiting state")
        transaction, receipt = runner._load_matching_transaction_and_receipt(
            paths,
            Path(receipt_path),
            transaction=transaction,
        )
        runner._validate_canonical_pair_metadata(paths, require_entries=True)
        result_bytes = runner._read_file_nofollow(paths.result_path)
        report_bytes = runner._read_file_nofollow(paths.report_path)
        result_sha256 = hashlib.sha256(result_bytes).hexdigest().upper()
        report_sha256 = hashlib.sha256(report_bytes).hexdigest().upper()
        if (
            result_sha256 != transaction["candidate_pair"]["result_sha256"]
            or report_sha256 != transaction["candidate_pair"]["report_sha256"]
            or result_sha256 != receipt["result_sha256"]
            or report_sha256 != receipt["report_sha256"]
        ):
            raise ValueError(
                "candidate journal or receipt hashes do not match publication pair"
            )
        validated = validate_publication_pair_bytes(result_bytes, report_bytes)
        expected = runner.build_aggregate_result(paths, read_only=True)
        expected_result_bytes = canonical_publication_json_bytes(expected)
        if expected_result_bytes != result_bytes:
            raise ValueError(
                "candidate is not the exact state-bound aggregate result"
            )
        expected_report_bytes = render_phase_b_report(
            expected,
            hashlib.sha256(expected_result_bytes).hexdigest().upper(),
        ).encode("utf-8")
        if expected_report_bytes != report_bytes:
            raise ValueError(
                "candidate report does not match independent state-bound rendering"
            )

        final_state = runner.load_state(paths, recover=False)
        final_transaction = runner._load_journal(paths, recover=False)
        final_transaction, final_receipt = (
            runner._load_matching_transaction_and_receipt(
                paths,
                Path(receipt_path),
                transaction=final_transaction,
            )
        )
        runner._validate_canonical_pair_metadata(paths, require_entries=True)
        final_result_bytes = runner._read_file_nofollow(paths.result_path)
        final_report_bytes = runner._read_file_nofollow(paths.report_path)
        if (
            final_state != state
            or final_transaction != transaction
            or final_receipt != receipt
            or final_state["phase"] != "awaiting_acceptance"
            or final_transaction["status"] != "awaiting_acceptance"
            or final_result_bytes != result_bytes
            or final_report_bytes != report_bytes
        ):
            raise ValueError(
                "candidate lifecycle changed during read-only validation"
            )
        return validated


def validate_checkpoint_readback(paths: Any) -> dict[str, Any]:
    from scripts import run_emotion_state_002_phase_b as runner

    state = runner.load_state(paths)
    if state["phase"] != "accepted":
        raise ValueError("checkpoint validation requires accepted state")
    if os.path.lexists(paths.journal_path):
        raise ValueError("accepted checkpoint requires no live journal")
    residual = (
        sorted(
            entry.name
            for entry in paths.recovery_root.iterdir()
            if entry.name != runner.LOCK_NAME
        )
        if paths.recovery_root.is_dir()
        else []
    )
    if residual:
        raise ValueError(
            "accepted checkpoint requires no residual receipt or transaction artifacts"
        )
    runner._validate_canonical_pair_metadata(paths, require_entries=True)
    result_bytes = runner._read_file_nofollow(paths.result_path)
    report_bytes = runner._read_file_nofollow(paths.report_path)
    validated = validate_publication_pair_bytes(result_bytes, report_bytes)
    expected = runner.build_aggregate_result(paths)
    if runner.canonical_json_bytes(expected) != result_bytes:
        raise ValueError("accepted checkpoint is not the exact state-bound canonical pair")
    return validated


SECTIONS = (
    "source",
    "contracts",
    "environment",
    "synthetic",
    "candidate",
    "checkpoint",
)


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate EMOTION-STATE-002 Phase B offline evidence."
    )
    parser.add_argument(
        "section",
        choices=SECTIONS,
    )
    parser.add_argument("--receipt", action="append")
    parsed = parser.parse_args(argv)
    if parsed.section == "candidate":
        if parsed.receipt is None or len(parsed.receipt) != 1:
            parser.error("candidate validation requires exactly one --receipt")
        parsed.receipt = parsed.receipt[0]
    elif parsed.receipt is not None:
        parser.error("--receipt is valid only for candidate validation")
    return parsed


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parse_args(argv)
    try:
        if arguments.section == "source":
            validate_source_section()
        elif arguments.section == "contracts":
            validate_contracts_section()
        elif arguments.section == "environment":
            validate_environment_section()
        elif arguments.section == "synthetic":
            validate_synthetic_section()
        else:
            from scripts import run_emotion_state_002_phase_b as runner

            paths = runner.RunnerPaths.production()
            if arguments.section == "candidate":
                validate_candidate_readback(paths, Path(arguments.receipt))
            else:
                validate_checkpoint_readback(paths)
    except (KeyError, OSError, RuntimeError, TypeError, ValueError) as error:
        print(
            f"EMOTION-STATE-002 Phase B validation failed: "
            f"{arguments.section}: {error}",
            file=sys.stderr,
        )
        return 1
    print(f"EMOTION-STATE-002 Phase B validation passed: {arguments.section}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
