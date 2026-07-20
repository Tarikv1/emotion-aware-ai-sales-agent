from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import re
import struct
import sys
import sysconfig
from collections.abc import Mapping, Sequence
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
CLASS_ORDER = ("A", "D", "F", "H", "N", "S")
MODEL_KEYS = ("class_prior", "sentence_id", "acoustic")
COVERAGE_TARGETS = (1.0, 0.8, 0.6)
MINIMUM_UNIQUE_ACTORS = 10
BOOTSTRAP_RESAMPLES = 2000
VALIDITY_KEYS = (
    "material_valid",
    "environment_valid",
    "split_valid",
    "leakage_free",
    "deterministic",
    "lockbox_valid",
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
    if not isinstance(value, Mapping) or tuple(value) != keys:
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
        ("schema_id", "partition_role", "class_order", "targets", "models"),
        "calibration result",
    )
    if payload["schema_id"] != "emotion-state-phase-b-calibration-v1":
        raise ValueError("calibration result schema does not match")
    validate_partition_role(payload["partition_role"], ("calibration",))
    validate_class_order(payload["class_order"])
    if tuple(payload["targets"]) != COVERAGE_TARGETS:
        raise ValueError("calibration targets do not match frozen contract")
    _exact_keys(payload["models"], MODEL_KEYS, "calibration model")
    for model in MODEL_KEYS:
        cells = _exact_keys(
            payload["models"][model],
            COVERAGE_TARGETS,
            "threshold",
        )
        previous_threshold = -1.0
        for target in COVERAGE_TARGETS:
            cell = _exact_keys(
                cells[target],
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
        actor_count = _count(metric["unique_actor_count"], "metric actor count")
        _count(metric["case_count"], "metric case count")
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
                _finite_float(value, f"metric {key}")
        if suppressed != (actor_count < MINIMUM_UNIQUE_ACTORS):
            raise ValueError("metric suppression does not match actor floor")
        class_cells = _exact_keys(
            metric["per_class_recall"],
            CLASS_ORDER,
            "per-class recall",
        )
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
            _count(cell["case_count"], "per-class recall case count")
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
        retained = _exact_keys(
            metric["retained"],
            COVERAGE_TARGETS,
            "retained metric",
        )
        for target in COVERAGE_TARGETS:
            cell = _exact_keys(
                retained[target],
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
            _count(cell["case_count"], "retained case count")
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
                _finite_float(
                    cell["retained_macro_f1"],
                    "retained macro-F1",
                )
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
        ),
        "evaluation result",
    )
    if payload["schema_id"] != "emotion-state-phase-b-evaluation-v1":
        raise ValueError("evaluation result schema does not match")
    role = validate_partition_role(
        payload["partition_role"],
        ("balanced_diagnostic", "final_lockbox"),
    )
    if expected_role is not None and role != expected_role:
        raise ValueError(f"evaluation result must have {expected_role} provenance")
    validate_class_order(payload["class_order"])
    if payload["final_decision_eligible"] is not (role == "final_lockbox"):
        raise ValueError("diagnostic evaluation cannot produce a final decision")
    _validate_metric_models(payload["models"])
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
        ),
        "bootstrap result",
    )
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
    _count(payload["unique_actor_count"], "bootstrap actor count")
    _count(payload["case_count"], "bootstrap case count")
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
        if not lower <= point <= upper:
            raise ValueError("bootstrap interval does not contain point estimate")
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
        ),
        "metric",
    )
    if metrics["schema_id"] != "emotion-state-phase-b-decision-evidence-v1":
        raise ValueError("metric schema does not match frozen contract")
    validate_partition_role(metrics["partition_role"], ("final_lockbox",))
    validate_class_order(metrics["class_order"])
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
        if not lower <= point <= upper:
            raise ValueError("paired lift interval does not contain point")
    for key in (
        "sentence_driven_apparent_lift",
        "eligible_slice_reversal",
        "eligible_slice_instability",
        "confidence_abstention_improves",
    ):
        if type(metrics[key]) is not bool:
            raise ValueError(f"metric {key} must be boolean")
    models = metrics["models"]
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
