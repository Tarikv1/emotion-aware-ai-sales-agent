from __future__ import annotations

import csv
import copy
import hashlib
import io
import math
import re
from collections import Counter, defaultdict
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from scripts.validate_emotion_state_002_phase_b import (
    BOOTSTRAP_RESAMPLES,
    CLASS_ORDER,
    COVERAGE_TARGETS,
    MINIMUM_UNIQUE_ACTORS,
    MODEL_KEYS,
    validate_bootstrap_result,
    validate_calibration_result,
    validate_class_order,
    validate_decision_inputs,
    validate_evaluation_result,
    validate_fit_inputs,
    validate_labels_and_actors,
    validate_partition_role,
    validate_probability_inputs,
)

LABELS = frozenset({"A", "D", "F", "H", "N", "S"})
RAW_JOIN_FIELD = "clipName"
RAW_MODALITY_FIELD = "queryType"
RAW_AUDIO_MODALITY = "1"
RAW_LABEL_FIELD = "respEmo"
SUMMARY_JOIN_FIELD = "FileName"
SUMMARY_LABEL_FIELD = "VoiceVote"
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


def _rows(path: Path, required: tuple[str, ...]) -> tuple[list[dict[str, str]], str]:
    source_bytes = Path(path).read_bytes()
    try:
        with io.TextIOWrapper(
            io.BytesIO(source_bytes),
            encoding="utf-8-sig",
            newline="",
        ) as handle:
            reader = csv.DictReader(handle, strict=True)
            if reader.fieldnames is None or tuple(reader.fieldnames) != required:
                raise ValueError(f"unexpected CSV schema: {path.name}")
            rows: list[dict[str, str]] = []
            for row in reader:
                if (
                    tuple(row) != required
                    or any(not isinstance(row[key], str) for key in required)
                ):
                    raise ValueError(f"unexpected CSV row: {path.name}")
                rows.append({key: row[key].strip() for key in required})
    except csv.Error as error:
        raise ValueError(f"malformed CSV row: {path.name}") from error
    return rows, hashlib.sha256(source_bytes).hexdigest().upper()


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
    finished_rows, finished_responses_sha256 = _rows(finished_path, finished_header)
    raw_groups: dict[str, Counter[str]] = defaultdict(Counter)
    for row in finished_rows:
        if row[RAW_MODALITY_FIELD] != RAW_AUDIO_MODALITY:
            continue
        if row[RAW_LABEL_FIELD] not in LABELS:
            raise ValueError("invalid raw audio-perception label")
        raw_groups[row[RAW_JOIN_FIELD]][row[RAW_LABEL_FIELD]] += 1

    summary_rows, summary_table_sha256 = _rows(summary_path, summary_header)
    released: dict[str, tuple[str, ...]] = {}
    for row in summary_rows:
        stem = row[SUMMARY_JOIN_FIELD]
        if stem in released:
            raise ValueError("duplicate summary clip")
        values = tuple(sorted(row[SUMMARY_LABEL_FIELD].split(":")))
        if not values or len(values) != len(set(values)) or any(
            value not in LABELS for value in values
        ):
            raise ValueError("invalid released VoiceVote")
        released[stem] = values

    stems = tuple(included_clip_stems)
    if any(not isinstance(stem, str) for stem in stems):
        raise ValueError("invalid included CREMA-D clip stem")
    if len(stems) != len(set(stems)):
        raise ValueError("duplicate included CREMA-D clip stem")

    records: list[CremaLabelRecord] = []
    ledger: Counter[str] = Counter()
    label_counts: Counter[str] = Counter()
    for stem in sorted(stems):
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
    result["source_binding"] = {
        "finished_responses_sha256": finished_responses_sha256,
        "summary_table_sha256": summary_table_sha256,
        "raw_join_field": RAW_JOIN_FIELD,
        "raw_modality_field": RAW_MODALITY_FIELD,
        "raw_audio_modality": RAW_AUDIO_MODALITY,
        "raw_label_field": RAW_LABEL_FIELD,
        "summary_join_field": SUMMARY_JOIN_FIELD,
        "summary_label_field": SUMMARY_LABEL_FIELD,
    }
    return tuple(records), result


def _classifier(seed: int) -> LogisticRegression:
    return LogisticRegression(
        penalty="l2",
        C=1.0,
        class_weight=None,
        solver="lbfgs",
        max_iter=10000,
        random_state=seed,
    )


def build_models(seed: int) -> dict[str, object]:
    if type(seed) is not int or not 0 <= seed <= 0xFFFFFFFF:
        raise ValueError("model seed must be a 32-bit non-negative integer")
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


def fit_frozen_models(
    training_features: np.ndarray,
    training_sentences: np.ndarray,
    training_labels: np.ndarray,
    seed: int,
    *,
    partition_role: str,
    class_order: Sequence[str],
) -> dict[str, object]:
    features, sentences, labels, validated_seed = validate_fit_inputs(
        training_features,
        training_sentences,
        training_labels,
        seed,
        partition_role=partition_role,
        class_order=class_order,
    )
    models = build_models(validated_seed)
    models["class_prior"].fit(features, labels)
    models["sentence_id"].fit(sentences.reshape(-1, 1), labels)
    models["acoustic"].fit(features, labels)
    for model in models.values():
        if tuple(model.classes_.tolist()) != CLASS_ORDER:
            raise ValueError("fitted model class order does not match A,D,F,H,N,S")
    probe_inputs = {
        "class_prior": features[:1],
        "sentence_id": sentences[:1].reshape(-1, 1),
        "acoustic": features[:1],
    }
    for key in MODEL_KEYS:
        probabilities = np.asarray(
            models[key].predict_proba(probe_inputs[key]),
            dtype=np.float64,
        )
        if (
            probabilities.shape != (1, len(CLASS_ORDER))
            or not np.isfinite(probabilities).all()
            or not np.allclose(
                probabilities.sum(axis=1),
                np.ones(1),
                rtol=0.0,
                atol=1e-12,
            )
        ):
            raise ValueError(
                "locked scikit-learn did not produce six-class probabilities"
            )
    return models


def calibrate_thresholds(
    probabilities: Mapping[str, np.ndarray],
    targets: Sequence[float],
    *,
    partition_role: str,
    class_order: Sequence[str],
) -> dict[str, Any]:
    validate_partition_role(partition_role, ("calibration",))
    validate_class_order(class_order)
    if tuple(targets) != COVERAGE_TARGETS:
        raise ValueError("calibration targets must be exactly 1.0, 0.8, 0.6")
    arrays, row_count = validate_probability_inputs(
        probabilities,
        class_order=class_order,
    )
    model_results: dict[str, dict[float, dict[str, float]]] = {}
    for model in MODEL_KEYS:
        confidence = np.max(arrays[model], axis=1)
        candidates = tuple(sorted(set(float(value) for value in confidence)))
        cells: dict[float, dict[str, float]] = {}
        for target in COVERAGE_TARGETS:
            eligible = [
                threshold
                for threshold in candidates
                if float(np.count_nonzero(confidence >= threshold)) / row_count
                >= target
            ]
            if not eligible:
                raise ValueError("calibration target has no valid threshold")
            threshold = max(eligible)
            achieved = (
                float(np.count_nonzero(confidence >= threshold)) / row_count
            )
            cells[target] = {
                "threshold": float(threshold),
                "achieved_coverage": float(achieved),
            }
        model_results[model] = cells
    result = {
        "schema_id": "emotion-state-phase-b-calibration-v1",
        "partition_role": "calibration",
        "class_order": list(CLASS_ORDER),
        "targets": list(COVERAGE_TARGETS),
        "models": model_results,
    }
    validate_calibration_result(result)
    return result


def _predicted_labels(probabilities: np.ndarray) -> np.ndarray:
    indexes = np.argmax(probabilities, axis=1)
    return np.asarray([CLASS_ORDER[index] for index in indexes], dtype="<U1")


def _macro_f1(labels: np.ndarray, predictions: np.ndarray) -> float:
    scores: list[float] = []
    for label in CLASS_ORDER:
        true_positive = int(np.count_nonzero(
            (labels == label) & (predictions == label)
        ))
        false_positive = int(np.count_nonzero(
            (labels != label) & (predictions == label)
        ))
        false_negative = int(np.count_nonzero(
            (labels == label) & (predictions != label)
        ))
        denominator = 2 * true_positive + false_positive + false_negative
        scores.append(
            0.0 if denominator == 0 else 2.0 * true_positive / denominator
        )
    return float(sum(scores) / len(CLASS_ORDER))


def _recalls(labels: np.ndarray, predictions: np.ndarray) -> dict[str, float]:
    result: dict[str, float] = {}
    for label in CLASS_ORDER:
        mask = labels == label
        denominator = int(np.count_nonzero(mask))
        result[label] = (
            0.0
            if denominator == 0
            else float(np.count_nonzero(predictions[mask] == label) / denominator)
        )
    return result


def _ece(labels: np.ndarray, probabilities: np.ndarray) -> float:
    confidence = np.max(probabilities, axis=1)
    predictions = _predicted_labels(probabilities)
    correct = predictions == labels
    total = len(labels)
    ece = 0.0
    for index in range(10):
        lower = index / 10.0
        upper = (index + 1) / 10.0
        if index == 9:
            mask = (confidence >= lower) & (confidence <= upper)
        else:
            mask = (confidence >= lower) & (confidence < upper)
        count = int(np.count_nonzero(mask))
        if count:
            accuracy = float(np.mean(correct[mask], dtype=np.float64))
            mean_confidence = float(
                np.mean(confidence[mask], dtype=np.float64)
            )
            ece += (count / total) * abs(accuracy - mean_confidence)
    return float(ece)


def _metric_values(
    labels: np.ndarray,
    probabilities: np.ndarray,
) -> dict[str, Any]:
    predictions = _predicted_labels(probabilities)
    recalls = _recalls(labels, predictions)
    one_hot = np.zeros_like(probabilities, dtype=np.float64)
    for row, label in enumerate(labels.tolist()):
        one_hot[row, CLASS_ORDER.index(label)] = 1.0
    true_probabilities = probabilities[
        np.arange(len(labels)),
        np.asarray([CLASS_ORDER.index(label) for label in labels.tolist()]),
    ]
    clipped = np.clip(
        true_probabilities,
        np.finfo(np.float64).eps,
        1.0,
    )
    return {
        "macro_f1": _macro_f1(labels, predictions),
        "balanced_accuracy": float(
            sum(recalls.values()) / len(CLASS_ORDER)
        ),
        "recalls": recalls,
        "multiclass_brier": float(
            np.mean(
                np.sum((probabilities - one_hot) ** 2, axis=1),
                dtype=np.float64,
            )
        ),
        "log_loss": float(-np.mean(np.log(clipped), dtype=np.float64)),
        "ece_10_bin": _ece(labels, probabilities),
    }


def _actor_count(actor_ids: tuple[str, ...], mask: np.ndarray) -> int:
    return len({
        actor
        for actor, retained in zip(actor_ids, mask.tolist())
        if retained
    })


def evaluate_partition(
    labels: np.ndarray,
    probabilities: Mapping[str, np.ndarray],
    actor_ids: Sequence[str],
    thresholds: Mapping[str, Any],
    *,
    partition_role: str,
    class_order: Sequence[str],
) -> dict[str, Any]:
    role = validate_partition_role(
        partition_role,
        ("balanced_diagnostic", "final_lockbox"),
    )
    validate_class_order(class_order)
    arrays, row_count = validate_probability_inputs(
        probabilities,
        class_order=class_order,
    )
    validated_labels, actors = validate_labels_and_actors(
        labels,
        actor_ids,
        expected_rows=row_count,
    )
    validated_thresholds = validate_calibration_result(thresholds)
    model_results: dict[str, Any] = {}
    all_rows = np.ones(row_count, dtype=bool)
    unique_actor_count = _actor_count(actors, all_rows)
    for model in MODEL_KEYS:
        probability_array = arrays[model]
        confidence = np.max(probability_array, axis=1)
        suppressed = unique_actor_count < MINIMUM_UNIQUE_ACTORS
        values = None if suppressed else _metric_values(
            validated_labels,
            probability_array,
        )
        class_cells: dict[str, Any] = {}
        predictions = _predicted_labels(probability_array)
        recalls = _recalls(validated_labels, predictions)
        for label in CLASS_ORDER:
            mask = validated_labels == label
            actors_for_class = _actor_count(actors, mask)
            cases_for_class = int(np.count_nonzero(mask))
            class_suppressed = actors_for_class < MINIMUM_UNIQUE_ACTORS
            class_cells[label] = {
                "suppressed": class_suppressed,
                "unique_actor_count": actors_for_class,
                "case_count": cases_for_class,
                "recall": None if class_suppressed else float(recalls[label]),
            }
        retained_cells: dict[float, Any] = {}
        for target in COVERAGE_TARGETS:
            calibration_cell = validated_thresholds["models"][model][target]
            threshold = calibration_cell["threshold"]
            mask = confidence >= threshold
            retained_actors = _actor_count(actors, mask)
            retained_cases = int(np.count_nonzero(mask))
            retained_suppressed = (
                retained_actors < MINIMUM_UNIQUE_ACTORS
                or retained_cases == 0
            )
            retained_cells[target] = {
                "threshold": float(threshold),
                "calibration_achieved_coverage": float(
                    calibration_cell["achieved_coverage"]
                ),
                "coverage": float(retained_cases / row_count),
                "suppressed": retained_suppressed,
                "unique_actor_count": retained_actors,
                "case_count": retained_cases,
                "retained_macro_f1": (
                    None
                    if retained_suppressed
                    else _macro_f1(
                        validated_labels[mask],
                        predictions[mask],
                    )
                ),
            }
        model_results[model] = {
            "suppressed": suppressed,
            "unique_actor_count": unique_actor_count,
            "case_count": row_count,
            "macro_f1": None if suppressed else values["macro_f1"],
            "balanced_accuracy": (
                None if suppressed else values["balanced_accuracy"]
            ),
            "per_class_recall": class_cells,
            "multiclass_brier": (
                None if suppressed else values["multiclass_brier"]
            ),
            "log_loss": None if suppressed else values["log_loss"],
            "ece_10_bin": None if suppressed else values["ece_10_bin"],
            "retained": retained_cells,
        }
    result = {
        "schema_id": "emotion-state-phase-b-evaluation-v1",
        "partition_role": role,
        "class_order": list(CLASS_ORDER),
        "models": model_results,
        "final_decision_eligible": role == "final_lockbox",
    }
    validate_evaluation_result(result, expected_role=role)
    return result


def paired_actor_bootstrap(
    labels: np.ndarray,
    probabilities: Mapping[str, np.ndarray],
    actor_ids: Sequence[str],
    resamples: int,
    seed: int,
    *,
    partition_role: str,
    class_order: Sequence[str],
    configuration_sha256: str,
) -> dict[str, Any]:
    validate_partition_role(partition_role, ("final_lockbox",))
    validate_class_order(class_order)
    if type(resamples) is not int or resamples != BOOTSTRAP_RESAMPLES:
        raise ValueError("paired actor bootstrap requires exactly 2,000 resamples")
    if (
        type(configuration_sha256) is not str
        or re.fullmatch(r"[0-9A-F]{64}", configuration_sha256) is None
        or type(seed) is not int
        or seed != int(configuration_sha256[:16], 16)
    ):
        raise ValueError(
            "bootstrap seed must derive from the configuration SHA-256"
        )
    arrays, row_count = validate_probability_inputs(
        probabilities,
        class_order=class_order,
    )
    validated_labels, actors = validate_labels_and_actors(
        labels,
        actor_ids,
        expected_rows=row_count,
    )
    unique_actors = tuple(sorted(set(actors)))
    if len(unique_actors) < MINIMUM_UNIQUE_ACTORS:
        raise ValueError("final lockbox bootstrap requires at least ten actors")
    actor_rows = {
        actor: np.asarray(
            [index for index, value in enumerate(actors) if value == actor],
            dtype=np.int64,
        )
        for actor in unique_actors
    }
    full_scores = {
        model: _macro_f1(
            validated_labels,
            _predicted_labels(arrays[model]),
        )
        for model in MODEL_KEYS
    }
    lifts = {
        "class_prior": np.empty(resamples, dtype=np.float64),
        "sentence_id": np.empty(resamples, dtype=np.float64),
    }
    generator = np.random.default_rng(seed)
    for draw in range(resamples):
        actor_indexes = generator.integers(
            0,
            len(unique_actors),
            size=len(unique_actors),
        )
        row_indexes = np.concatenate([
            actor_rows[unique_actors[int(index)]]
            for index in actor_indexes.tolist()
        ])
        draw_labels = validated_labels[row_indexes]
        draw_scores = {
            model: _macro_f1(
                draw_labels,
                _predicted_labels(arrays[model][row_indexes]),
            )
            for model in MODEL_KEYS
        }
        for baseline in lifts:
            lifts[baseline][draw] = (
                draw_scores["acoustic"] - draw_scores[baseline]
            )
    intervals: dict[str, Any] = {}
    for baseline in ("class_prior", "sentence_id"):
        lower, upper = np.percentile(
            lifts[baseline],
            [2.5, 97.5],
            method="linear",
        )
        intervals[baseline] = {
            "point_estimate": float(
                full_scores["acoustic"] - full_scores[baseline]
            ),
            "lower_95": float(lower),
            "upper_95": float(upper),
        }
    result = {
        "schema_id": "emotion-state-phase-b-bootstrap-v1",
        "partition_role": "final_lockbox",
        "class_order": list(CLASS_ORDER),
        "resamples": resamples,
        "seed": seed,
        "configuration_sha256": configuration_sha256,
        "unique_actor_count": len(unique_actors),
        "case_count": row_count,
        "paired_macro_f1_lift": intervals,
    }
    validate_bootstrap_result(result)
    return result


def build_decision_evidence(
    evaluation: Mapping[str, Any],
    bootstrap: Mapping[str, Any],
    *,
    sentence_driven_apparent_lift: bool,
    eligible_slice_reversal: bool,
    eligible_slice_instability: bool,
    confidence_abstention_improves: bool,
) -> dict[str, Any]:
    validated_evaluation = validate_evaluation_result(
        evaluation,
        expected_role="final_lockbox",
    )
    validated_bootstrap = validate_bootstrap_result(bootstrap)
    evaluation_counts = {
        (
            validated_evaluation["models"][model]["unique_actor_count"],
            validated_evaluation["models"][model]["case_count"],
        )
        for model in MODEL_KEYS
    }
    if evaluation_counts != {
        (
            validated_bootstrap["unique_actor_count"],
            validated_bootstrap["case_count"],
        )
    }:
        raise ValueError(
            "final-lockbox evaluation and bootstrap counts do not match"
        )
    flags = (
        sentence_driven_apparent_lift,
        eligible_slice_reversal,
        eligible_slice_instability,
        confidence_abstention_improves,
    )
    if any(type(flag) is not bool for flag in flags):
        raise ValueError("decision evidence flags must be booleans")
    result = {
        "schema_id": "emotion-state-phase-b-decision-evidence-v1",
        "partition_role": "final_lockbox",
        "class_order": list(CLASS_ORDER),
        "final_decision_eligible": True,
        "models": copy.deepcopy(validated_evaluation["models"]),
        "paired_macro_f1_lift": copy.deepcopy(
            validated_bootstrap["paired_macro_f1_lift"]
        ),
        "sentence_driven_apparent_lift": sentence_driven_apparent_lift,
        "eligible_slice_reversal": eligible_slice_reversal,
        "eligible_slice_instability": eligible_slice_instability,
        "confidence_abstention_improves": confidence_abstention_improves,
    }
    all_valid = {
        "material_valid": True,
        "environment_valid": True,
        "split_valid": True,
        "leakage_free": True,
        "deterministic": True,
        "lockbox_valid": True,
    }
    validate_decision_inputs(result, all_valid)
    return result


def decide_experiment(
    metrics: Mapping[str, Any],
    validity: Mapping[str, bool],
) -> str:
    validated_metrics, validated_validity = validate_decision_inputs(
        metrics,
        validity,
    )
    if not all(validated_validity.values()):
        return "discard"
    if validated_metrics["sentence_driven_apparent_lift"]:
        return "discard"
    lifts = validated_metrics["paired_macro_f1_lift"]
    if any(lifts[baseline]["point_estimate"] <= 0.0 for baseline in lifts):
        return "discard"

    models = validated_metrics["models"]
    acoustic = models["acoustic"]
    class_prior = models["class_prior"]
    recalls = acoustic["per_class_recall"]
    brier_improves = (
        acoustic["multiclass_brier"] < class_prior["multiclass_brier"]
    )
    calibration_not_worse = (
        acoustic["ece_10_bin"] <= class_prior["ece_10_bin"]
    )
    every_recall_positive = all(
        recalls[label]["recall"] is not None
        and recalls[label]["recall"] > 0.0
        for label in CLASS_ORDER
    )
    intervals_positive = all(
        lifts[baseline]["lower_95"] > 0.0
        for baseline in lifts
    )
    no_slice_failure = (
        not validated_metrics["eligible_slice_reversal"]
        and not validated_metrics["eligible_slice_instability"]
    )
    if (
        intervals_positive
        and brier_improves
        and calibration_not_worse
        and every_recall_positive
        and no_slice_failure
        and validated_metrics["confidence_abstention_improves"]
    ):
        return "keep_for_research_only"
    return "revise"
