from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import re
import struct
import sys
import sysconfig
from collections.abc import Mapping
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
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
    if isinstance(value, dict):
        for nested_value in value.values():
            _reject_non_finite(nested_value)
    if isinstance(value, list):
        for nested_value in value:
            _reject_non_finite(nested_value)


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
        if not isinstance(raw_name, str) or not raw_name:
            raise ValueError("installed distribution is missing a name")
        name = _normalize_distribution_name(raw_name)
        if name in installed:
            raise ValueError("installed distributions contain duplicate names")
        installed[name] = distribution.version
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
        name = _normalize_distribution_name(str(raw_name))
        if name in normalized_installed:
            raise ValueError("installed distributions contain duplicate names")
        normalized_installed[name] = str(version)
    if normalized_installed != expected_installed:
        raise ValueError("installed distributions do not match environment lock")
    return dict(sorted(normalized_installed.items()))


def validate_environment_identity(
    *,
    lock_path: Path,
    wheelhouse_path: Path,
) -> dict[str, Any]:
    expected_python = EVALUATION_PYTHON_PATH.resolve()
    actual_python = Path(sys.executable).resolve()
    if str(actual_python).casefold() != str(expected_python).casefold():
        raise ValueError("evaluation Python executable does not match fixed path")
    actual_python_version = (
        sys.version_info.major,
        sys.version_info.minor,
    )
    if actual_python_version != (3, 11):
        raise ValueError("evaluation Python version must be 3.11")
    lock_file = Path(lock_path)
    if not lock_file.is_file():
        raise ValueError("environment lock is missing")
    lock = validate_environment_lock(load_json_strict(lock_file))
    actual_platform = _current_interpreter_platform()
    if actual_platform != lock["platform"]:
        raise ValueError(
            "evaluation Python platform does not match environment lock: "
            f"{actual_platform}"
        )
    normalized_installed = _validate_installed_distributions(
        lock,
        _installed_distributions(),
    )

    wheelhouse = Path(wheelhouse_path)
    wheels = {
        path.name: path
        for path in wheelhouse.iterdir()
        if path.is_file()
    } if wheelhouse.is_dir() else {}
    expected_filenames = {
        distribution["wheel_filename"]
        for distribution in lock["distributions"]
    }
    if set(wheels) != expected_filenames:
        raise ValueError("wheel set does not match environment lock")
    wheel_hashes: dict[str, str] = {}
    for distribution in lock["distributions"]:
        wheel = wheels[distribution["wheel_filename"]]
        digest = hashlib.sha256(wheel.read_bytes()).hexdigest().upper()
        if digest != distribution["sha256"]:
            raise ValueError(
                f"wheel hash does not match environment lock: {wheel.name}"
            )
        wheel_hashes[wheel.name] = digest
    return {
        "python_executable": str(actual_python),
        "python_version": ".".join(str(value) for value in actual_python_version),
        "platform": actual_platform,
        "installed_distributions": normalized_installed,
        "wheel_count": len(wheels),
        "wheel_hashes": wheel_hashes,
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


def main() -> int:
    try:
        validate_config(load_json_strict(CONFIG_PATH))
        validate_feature_schema(load_json_strict(FEATURE_SCHEMA_PATH))
        validate_split_schema(load_json_strict(SPLIT_SCHEMA_PATH))
        validate_environment_lock(load_json_strict(ENVIRONMENT_LOCK_PATH))
        validate_environment_identity(
            lock_path=ENVIRONMENT_LOCK_PATH,
            wheelhouse_path=(
                ROOT / ".tmp/emotion-state-002-phase-b/dependencies/wheelhouse"
            ),
        )
    except (OSError, ValueError) as error:
        print(
            f"EMOTION-STATE-002 Phase B frozen contract validation failed: {error}",
            file=sys.stderr,
        )
        return 1
    print("EMOTION-STATE-002 Phase B frozen contract validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
